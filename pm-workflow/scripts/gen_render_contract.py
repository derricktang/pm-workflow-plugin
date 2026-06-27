#!/usr/bin/env python3
"""
gen_render_contract.py — R8 layer 1：PRD 帧级渲染契约导出（SSOT #77，WIP）

用法：
    python pm-workflow/scripts/gen_render_contract.py [scaffold.json] [flags]
    flags:
      --module M01      仅导出指定模块（pilot / 调试用）
      --dry-run         仅打印契约到 stdout，不写入任何文件（默认行为，layer 1 当前阶段）
      --provenance      额外打印 per-frame 导出溯源（防静默漏导）

根本原则（layer 1 命门）：**忠实转录 spec 权威列，禁推断**。契约完整性 = spec
权威列完整性；spec 列漏 = spec bug（S4-21 字段 / S4-34 触点 / Supervisor 另兜），
非契约导出 bug → 天花板有明确归属。

三类机械可核项（逐源转录，不推断）：
  - 触点 per-state：`## S2.{mid}.3 触点表`「所在状态」列含本帧 state（或全部/所有/通用/all）
                    且 触点 ID 前缀 == 本帧 M-P → marker `data-tp="<canonical>"`（复用 prd_expression §6.1 既有约定）
  - 字段 per-page：`## S2.{mid}.4 字段绑定`「页面」==pid 且「prd 属性」含 data-field
                    且无「隐式/不显式/不展示/隐藏」→ marker `data-field="<name>"`
  - 平台 per-state：`## S2.{mid}.2 状态枚举` 本帧「平台」列**仅当列出具体平台**
                    （非 agnostic/all/通用）→ marker 帧类 `phone-frame` 等

不导出 C-4 三件（.4B 业务规则 / .5B 数据规模 / .7 Gherkin 已 SSOT #68 派生，避双源）。

显式边界（§8.6 天花板上台面）：导出分两段——「机械可核」（三类，进 check_render_contract）
+ 「人工对照」（§11 异常态 / ledger NB 等不可枚举模糊项，只列供 Supervisor 抽样，绝不进机械 check）。

含内嵌帧（走 gen_scaffold.iter_page_prd_ids，R3 SSOT #76）。确定性输出（排序、无时间戳，对齐 #73）。
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_scaffold import iter_page_prd_ids  # noqa: E402  (R3 SSOT #76 统一收集)

DEFAULT_SCAFFOLD = REPO_ROOT / "process_record" / "tasks" / "scaffold.json"
OUTPUT_DIR = REPO_ROOT / "outputs"

# 平台「不生契约项」豁免词（跨端单帧，无 per-platform 期望）
_AGNOSTIC_PLATFORM_TOKENS = {"agnostic", "all", "全部", "所有", "通用", "跨端", "—", "-", ""}
# 触点「所在状态」通配词（适用全部状态）
_TOUCHPOINT_WILDCARD = ("全部", "所有", "通用", "all")
# 字段「不渲染」豁免词（隐式承载，不显式展示）
_FIELD_IMPLICIT_RE = re.compile(r"隐式|不显式|不展示|隐藏")
_PRD_ID_RE = re.compile(r"^H-(M\d{2})-(P\d{2})-(.+)$")
_TP_ID_RE = re.compile(r"^M\d{2}-P\d{2}-[TD]\d{2}$")
_DATA_FIELD_RE = re.compile(r'data-field="([^"]+)"')
_NB_REF_RE = re.compile(r"\bNB-\d+[A-Za-z]*\b")


def spec_section(spec: str, mid: str, suffix: str) -> str:
    """提取 `## S2.{mid}.{suffix} ...` 段（到下一 `## ` 或文末）。suffix 如 '2'/'3'/'4'。"""
    m = re.search(
        rf"^## S2\.{re.escape(mid)}\.{re.escape(suffix)}\b.*?(?=\n## |\Z)",
        spec, re.DOTALL | re.MULTILINE,
    )
    return m.group(0) if m else ""


def _table_rows(section: str) -> list[list[str]]:
    """解析 markdown 表格数据行为 cell 列表（跳表头 + 分隔行）。"""
    rows = []
    for ln in section.splitlines():
        s = ln.strip()
        if not s.startswith("|") or "---" in s:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        rows.append(cells)
    return rows


def extract_touchpoints_for_state(spec: str, mid: str, pid: str, state: str):
    """转录 .3 触点表：返回本帧期望触点 [(canonical_id, 描述)]（per-state）。"""
    sec = spec_section(spec, mid, "3")
    out = []
    for cells in _table_rows(sec):
        if len(cells) < 2 or not _TP_ID_RE.match(cells[0]):
            continue
        tpid, states_cell = cells[0], cells[1]
        if not tpid.startswith(f"{mid}-{pid}-"):
            continue
        st_list = [s.strip() for s in re.split(r"[/／]", states_cell)]
        applies = (state in st_list) or any(w in states_cell for w in _TOUCHPOINT_WILDCARD)
        if applies:
            desc = cells[2] if len(cells) > 2 else ""
            out.append((tpid, desc))
    return out


def extract_fields_for_page(spec: str, mid: str, pid: str):
    """转录 .4 字段绑定：返回本页期望字段 [(data_field, 字段名)]（per-page）。
    仅含「prd 属性」声明 data-field 且非「隐式/不显式/不展示/隐藏」的字段。"""
    sec = spec_section(spec, mid, "4")
    out, seen = [], set()
    for cells in _table_rows(sec):
        if len(cells) < 2 or cells[0] != pid:
            continue
        row = " | ".join(cells)
        dfm = _DATA_FIELD_RE.search(row)
        if not dfm or _FIELD_IMPLICIT_RE.search(row):
            continue
        df = dfm.group(1)
        if df in seen:
            continue
        seen.add(df)
        fname = cells[1] if len(cells) > 1 else df
        out.append((df, fname))
    return out


def extract_platforms_for_frame(spec: str, mid: str, prd_id: str, state: str):
    """转录 .2 状态枚举「平台」列：返回本帧具体平台 token 列表（agnostic→空）。
    优先用 prd_id 列精确匹配本帧行，回退状态名匹配。"""
    sec = spec_section(spec, mid, "2")
    chosen = None
    for cells in _table_rows(sec):
        if len(cells) < 7:
            continue
        # .2 列序：页面 | 状态名 | 触发条件 | 是否互斥 | 平台 | 页面表现 | prd_id
        row_prd = cells[-1].strip("`")
        if row_prd == prd_id:
            chosen = cells[4]
            break
        if cells[1] == state and chosen is None:
            chosen = cells[4]
    if not chosen:
        return []
    toks = [t.strip() for t in re.split(r"[/／,，、]", chosen) if t.strip()]
    return [t for t in toks if t.lower() not in _AGNOSTIC_PLATFORM_TOKENS
            and t not in _AGNOSTIC_PLATFORM_TOKENS]


def extract_human_review_refs(spec: str, mid: str, pid: str, state: str):
    """人工对照区：转录本帧相关 spec 段（.2 本帧行「页面表现」+ .3 本帧触点系统响应）
    中的 NB-xxx 引用（不可枚举模糊项指针，供 Supervisor 抽样；绝不进机械 check）。"""
    refs = set()
    # .2 本帧「页面表现」cell
    sec2 = spec_section(spec, mid, "2")
    for cells in _table_rows(sec2):
        if len(cells) >= 7 and cells[1] == state and cells[0] == pid:
            refs.update(_NB_REF_RE.findall(cells[5]))
    # .3 本帧触点「系统响应」
    sec3 = spec_section(spec, mid, "3")
    for cells in _table_rows(sec3):
        if len(cells) >= 5 and _TP_ID_RE.match(cells[0]) and cells[0].startswith(f"{mid}-{pid}-"):
            st_list = [s.strip() for s in re.split(r"[/／]", cells[1])]
            if state in st_list or any(w in cells[1] for w in _TOUCHPOINT_WILDCARD):
                refs.update(_NB_REF_RE.findall(cells[4]))
    return sorted(refs)


def build_module_contract(mod: dict, spec: str) -> dict:
    """构造单模块契约：per-page 字段 + per-frame 触点/平台/人工对照 + provenance。"""
    mid = mod["id"]
    pages = mod.get("pages", []) or []
    contract = {"mid": mid, "name": mod.get("name", ""), "pages": [], "provenance": []}
    for page in pages:
        pid = page["id"]
        fields = extract_fields_for_page(spec, mid, pid)
        page_entry = {"pid": pid, "name": page.get("name", ""), "fields": fields, "frames": []}
        # 本页所有帧（含内嵌，R3 SSOT #76）
        for prd_id in iter_page_prd_ids(page):
            m = _PRD_ID_RE.match(prd_id)
            if not m:
                continue
            state = m.group(3)
            tps = extract_touchpoints_for_state(spec, mid, pid, state)
            plats = extract_platforms_for_frame(spec, mid, prd_id, state)
            human = extract_human_review_refs(spec, mid, pid, state)
            page_entry["frames"].append({
                "prd_id": prd_id, "state": state,
                "touchpoints": tps, "platforms": plats, "human": human,
            })
            contract["provenance"].append(
                f"{prd_id}: 触点 .3→{len(tps)}{' ⚠' if not tps else ''} | "
                f"平台 .2→{plats or 'agnostic(0)'} | 人工 NB→{len(human)}"
            )
        contract["provenance"].append(
            f"{mid}-{pid}: 字段(页) .4→{len(fields)}{' ⚠' if not fields else ''}"
        )
        contract["pages"].append(page_entry)
    return contract


def render_contract_md(contract: dict) -> str:
    """渲染契约为 task-card checklist markdown（机械可核段 + 人工对照段）。"""
    mid = contract["mid"]
    L = [f"## 渲染契约 checklist（机械可核）— {mid} {contract['name']}", ""]
    human_lines = [f"## 渲染契约 — 人工对照（Supervisor 抽样，非机械核）— {mid}", ""]
    has_human = False
    for pg in contract["pages"]:
        pid = pg["pid"]
        L.append(f"### 页面 {pid} {pg['name']}（字段 per-page）")
        if pg["fields"]:
            for df, fname in pg["fields"]:
                L.append(f'- [ ] field:{df} — 字段「{fname}」渲染（marker: `data-field="{df}"`）')
        else:
            L.append("- （本页 .4 无显式 data-field 字段）")
        L.append("")
        for fr in pg["frames"]:
            L.append(f"#### 帧 {fr['prd_id']}")
            if fr["touchpoints"]:
                for tpid, desc in fr["touchpoints"]:
                    short = (desc[:36] + "…") if len(desc) > 37 else desc
                    L.append(f'- [ ] tp:{tpid} — 触点「{short}」（marker: `data-tp="{tpid}"`）')
            for plat in fr["platforms"]:
                L.append(f"- [ ] plat:{plat} — 平台「{plat}」帧（marker: 对应帧类）")
            if not fr["touchpoints"] and not fr["platforms"]:
                L.append("- （本帧无机械可核触点/平台项）")
            L.append("")
            if fr["human"]:
                has_human = True
                human_lines.append(f"#### 帧 {fr['prd_id']}")
                human_lines.append(
                    f"- NB 边缘语义抽样：{', '.join(fr['human'])}（见 decisions_ledger / §11 异常态）"
                )
                human_lines.append("")
    out = "\n".join(L)
    if has_human:
        out += "\n" + "\n".join(human_lines)
    return out


# ── layer 2a：契约 checklist 落 task card ──────────────────────────────────────
RC_START = "<!-- [RENDER-CONTRACT-START] -->"
RC_END = "<!-- [RENDER-CONTRACT-END] -->"


def update_task_card_render_contract(task_card_path: Path, contract_md: str) -> bool:
    """把渲染契约 checklist 落进任务卡（RENDER-CONTRACT 定界块，幂等替换/缺则追加）。
    返回是否实际写入。**编排器在 Step 4 后、Step 5 派发前跑一次**（落全 `[ ]` 新契约）；
    PRD agent 在 Step 5 逐条勾 `[ ]→[x]`；**编排器之后不再重跑**（重跑会重置勾态——
    属新契约语义，scaffold/spec 变更才重跑）。"""
    if not task_card_path.exists():
        return False
    text = task_card_path.read_text(encoding="utf-8")
    block = f"{RC_START}\n{contract_md.rstrip()}\n{RC_END}"
    if RC_START in text and RC_END in text:
        new_text = re.sub(
            re.escape(RC_START) + r".*?" + re.escape(RC_END),
            lambda m: block, text, count=1, flags=re.DOTALL,
        )
    else:
        new_text = text.rstrip() + "\n\n" + block + "\n"
    task_card_path.write_text(new_text, encoding="utf-8")
    return True


def main():
    args = sys.argv[1:]
    only_mod = None
    if "--module" in args:
        i = args.index("--module")
        only_mod = args[i + 1] if i + 1 < len(args) else None
        args = [a for j, a in enumerate(args) if j not in (i, i + 1)]
    show_prov = "--provenance" in args
    write_mode = "--write" in args  # 落进任务卡（否则仅 dry-run 打印）
    args = [a for a in args if a not in ("--dry-run", "--provenance", "--write")]
    scaffold_path = Path(args[0]) if args else DEFAULT_SCAFFOLD

    if not scaffold_path.exists():
        print(f"[ERROR] scaffold 不存在：{scaffold_path}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(scaffold_path.read_text(encoding="utf-8"))
    product = data["product"]
    # outputs 目录从 scaffold 所在仓推导（scaffold 在 <repo>/process_record/tasks/）——
    # 兼容 in-repo 运行与跨仓 dry-run（指向下游 scaffold 时 spec 在下游 outputs/）。
    scaffold_repo = scaffold_path.resolve().parent.parent.parent
    out_dir = scaffold_repo / "outputs"
    if not out_dir.exists():
        out_dir = OUTPUT_DIR
    spec_path = out_dir / f"spec_{product}_latest.md"
    if not spec_path.exists():
        print(f"[ERROR] spec 不存在：{spec_path}", file=sys.stderr)
        sys.exit(1)
    spec = spec_path.read_text(encoding="utf-8")

    mods = [m for m in data["modules"] if (only_mod is None or m["id"] == only_mod)]
    if not mods:
        print(f"[ERROR] 未找到模块 {only_mod}", file=sys.stderr)
        sys.exit(1)

    all_prov = []
    for mod in mods:
        if not mod.get("pages"):
            continue  # logic-only 模块无帧
        contract = build_module_contract(mod, spec)
        contract_md = render_contract_md(contract)
        if write_mode:
            tc_rel = mod.get("task_card", "")
            tc_path = scaffold_repo / tc_rel if tc_rel else None
            if tc_path and update_task_card_render_contract(tc_path, contract_md):
                print(f"[✎] {tc_path.name} 渲染契约 checklist 已落地")
            else:
                print(f"[WARN] {mod['id']} 任务卡缺失或未配置 task_card，跳过落地：{tc_rel!r}",
                      file=sys.stderr)
        else:
            print(contract_md)
            print()
        all_prov.extend(contract["provenance"])

    if show_prov:
        print("\n## 导出溯源（provenance — 防静默漏导）\n")
        for line in all_prov:
            print(line)


if __name__ == "__main__":
    main()
