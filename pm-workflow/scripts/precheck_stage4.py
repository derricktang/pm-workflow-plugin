#!/usr/bin/env python3
"""
precheck_stage4.py — 阶段四自审前置机械检查脚本

用法：
    python pm-workflow/scripts/precheck_stage4.py [scaffold.json 路径]

    scaffold.json 默认路径：process_record/tasks/scaffold.json

作用：
    在 Step 7 PM 自审之前运行，机械校验阶段四产出物是否满足以下硬约束：
      1. scaffold.json 格式与编号体系（M/P/prd_id 格式、全局唯一性、层级一致）
      2. prd.html 占位注释已被全部替换（gen_scaffold.py 与 assemble.py prd 均已执行完毕）
      3. prd.html ↔ scaffold.json 结构一致（每个 prd_id 都有对应 section；产品规格区 9 节齐全,含 A-04.2 业务流程图）
      4. prd.html 导航完整性（所有 showSection 目标都能解析到 section id）
      5. prd.html Mermaid 局部豁免（proto_contract.md §十一）：默认禁用，仅 id 含
         journey / user-journey / flow 关键字的 <section> 内豁免
      6. prd.html 基本 HTML 结构完整
      7. spec.md 包含全部模块、尾部含变更记录与非阻塞问题清单、内容非空骨架
      8. proj 组件协议（S4-17/18/19）：schema 完整性、状态枚举完整性、可视化与 CSS 抽象纪律
      9. pub 组件索引一致性：components/*.md 必有索引项 / 子类编号唯一 / 业务场景反查 id 已声明 / 分类总览组件数与总表行数一致
     10. proj 索引段一致性：A/B 表与详情段一一对应 / B 表替代组件在 A 表 / D 表模块清单与 scaffold.json 一致 / D 表引用的 proj 组件在 A 表
     11. PRD 中所有 fb-* class 必须已在 pub 索引登记（S4-23）
     12. frame-card 端口标签 + .frame-cell 嵌套规则：
         1 个 frame-card 并列 ≥ 2 端口帧实例（含 ≥ 2 类型）时，每个端口帧必须包在
         .frame-cell 内（不能直接挂 .frame-wrapper 下），每个 .frame-cell 必须含
         .frame-platform-item + .frame-platform-tag span（.frame-platform-note 可选）
     13. 侧栏「组件变更」分组完整性（来源 issue 2026-05-07_1613）：sidebar 含
         「组件变更」section-title + [COMPONENT-CHANGELOG-NAV-START/END] 注入块 +
         注入项与主体 §十一 component-changelog 三类（new/update/deprecated）双向一致
         （集合 + 状态 tag 类型一一对应；promote 不进 sidebar）
     14. 派生模块引用 owner proj 组件内部 slot class 完整性（S4-27,SSOT #37 / NB-WE-32/33 实装,
         issue # 8 复盘）：派生模块 draft 中 `class="...proj-XXX..."` 容器内部应含 owner 已定义
         的 slot class(.{prefix}-{name});v2 双分支判定:
           - 分支 v1(fb-tag 平铺):slot=0 + fb-tag>=2 → WARN
           - 分支 v2(单行字面退化):slot=0 + fb-tag=0 + 可视文本长度>=20 → WARN(NB-WE-33)
     15. [v2 档 C｜WARN 阶段] S4-28 desktop/tablet-frame 末位固定操作栏
         .fb-frame-bottom-bar 结构完整性 — 零启发式真源 class 匹配:扫
         .fb-frame-bottom-bar,校验其为 .desktop-frame / .tablet-frame 直接子元素,
         否则 WARN(放错层 → sticky 贴底失效)。sticky 由真源 class 自带,PM 禁
         inline sticky。0 命中 = 下游未迁移(正常,非 bug);下游迁移完成后升 FAIL。
         v1 flex+button 启发式 2026-05-15 同日下线(5/5 false positive),v2 从根
         消除该失败模式。详 rule_hard_constraints.md §S4-28 + fb-fallback-manifest.md §3.11。
     16. [S4-33｜WARN 阶段] mermaid 块语法校验(mmdc 实际 parse,SSOT #43): 提取 PRD
         <pre class="mermaid">(html.unescape) / spec ```mermaid 块 → 拼临时 markdown →
         mmdc 单次渲染 parse(chrome 启一次,~1-2s/十余块);语法错(括号未引号/edge label/
         时序图等)WARN。一次性消除 #23/#26/#34/#35 类反复。mmdc 缺失/超时/异常 → WARN
         跳过不阻断(下游无 mmdc 静默降级);puppeteer 需 --no-sandbox(临时 config 注入)。
         与 check_prd「游离 mermaid」位置校验正交(本规则校语法能否 parse)。WARN 阶段,
         3 仓 dry-run + FP<30% 后升 FAIL。详 rule_hard_constraints.md §S4-33。
     17. [S4-34｜WARN 阶段] 触点 canonical 引用完整性(SSOT #44,item 6 治本): 触点编号从
         scaffold.pages[].touchpoints[] canonical 单源生成(gen_scaffold 预填 spec 触点表
         ID 行),precheck 校 spec/prd 中任何 M[XX]-P[YY]-[TDC][NN] 引用 ⊆ canonical 集合;
         不在集合内(手写偏差/拼写错/跨页串号) → WARN,治本 D4/D5 类。向后兼容:scaffold 无
         touchpoints[] 声明 → 跳过(不阻断旧两段式产物迁移)。WARN 阶段,3 仓 dry-run +
         FP<30% 后升 FAIL。详 rule_hard_constraints.md §S4-34。
     18. [S4-35｜WARN 阶段] 移动端次级页面返回入口完整性(SSOT #45,item 2① 配套): 扫所有
         class 含 fb-navbar 的元素,零启发式结构校验——① 须为移动类 *-frame(phone/h5/
         miniprogram/tablet-frame)直接子元素,否则 WARN(放错层 → sticky 贴顶失效);② 须
         含 fb-nav-back 后代(返回入口),否则 WARN(导航栏无返回 → 用户无路可返)。keys off
         fb-navbar 组件存在性(非页面类型启发式) → FP≈0(对齐 S4-28 v2 真源匹配教训,放弃
         scaffold 无字段支撑的"次级页面"推断)。0 命中 = 下游未迁移(正常,非 bug)。WARN
         阶段,下游迁移完升 FAIL。详 rule_hard_constraints.md §S4-35 + manifest §3.12。

退出码：
    0  — 全部通过，可进入 Step 7 PM 自审
    1  — 存在错误，禁止进入自审，PM 须先整改
"""

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_scaffold import iter_page_prd_ids  # SSOT #76 R3 内嵌子组件统一 prd_id 收集
from strip_inline_change_markers import (  # SSOT #79 / S4-68 正文内联变更标记检测（复用，单源）
    warn_inline_markers,
)
from gen_render_contract import (  # SSOT #77 R8 渲染契约转录器（复用，不重复实现）
    extract_touchpoints_for_state,
    extract_fields_for_page,
)
from precheck_common import (
    EXPECTED_CHANGELOG_HEADER,
    check_archive_sync,
    check_role_naming_consistency,
    check_version_changelog,
    extract_role_table,
)

# ── 路径约定 ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SCAFFOLD = REPO_ROOT / "process_record" / "tasks" / "scaffold.json"
OUTPUT_DIR = REPO_ROOT / "outputs"


# ── 报告收集器 ────────────────────────────────────────────────────────────────

class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passed = 0

    def ok(self, msg: str) -> None:
        self.passed += 1
        print(f"  [OK]   {msg}")

    def fail(self, msg: str) -> None:
        self.errors.append(msg)
        print(f"  [FAIL] {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"  [WARN] {msg}")

    def section(self, name: str) -> None:
        print(f"\n▌ {name}")

    def summary(self) -> int:
        total = self.passed + len(self.errors) + len(self.warnings)
        print()
        print("─" * 60)
        print(
            f"共 {total} 项检查：通过 {self.passed} | "
            f"错误 {len(self.errors)} | 警告 {len(self.warnings)}"
        )
        if self.errors:
            print(f"\n[BLOCK] 存在 {len(self.errors)} 项错误，禁止进入 Step 7 自审。")
            print("请 PM 按以下清单整改后重跑 precheck_stage4.py：")
            for i, e in enumerate(self.errors, 1):
                print(f"  {i}. {e}")
            return 1
        if self.warnings:
            print(f"\n[PASS-W] 通过，但存在 {len(self.warnings)} 项警告，自审时请一并确认。")
        else:
            print("\n[PASS] 机械检查通过，可进入 Step 7 PM 自审。")
        return 0


# ── §3 角色清单 SSOT 加载（消化 SSOT 双锚 #24，issue 2026-05-08_0024）────────
# 真源：产品定义 §3 用户画像「**角色 ID**：[role-N]」+「**角色名**：[xxx]」结构化字段
# 派生：scaffold roles / depends_on permission target / spec / PRD 的角色字面值
# 抽取规范：tmpl_产品定义.md §5「角色名抽取算法」段

ROLE_ID_FIELD_RE = re.compile(r"-\s*\*\*角色\s*ID\*\*\s*[：:]\s*\[`?(role-\d+)`?\]")
ROLE_NAME_FIELD_RE = re.compile(r"-\s*\*\*角色名\*\*\s*[：:]\s*\[(.+?)\]")


def _load_role_lists_from_product_def(product: str) -> tuple[set[str], set[str]]:
    """从产品定义 §3 提取（角色 ID 集合,角色名集合）。
    若产品定义文件不存在或 §3 缺结构化字段，返回（空集,空集）—— 调用方降级 WARN。
    占位符（含【】方括号）的角色名跳过收集，避免模板未替换文本污染清单。"""
    pdef_path = OUTPUT_DIR / f"产品定义_{product}_latest.md"
    if not pdef_path.exists():
        return set(), set()
    try:
        text = pdef_path.read_text(encoding="utf-8")
    except OSError:
        return set(), set()
    # 仅扫 §3 段（避免误抓后续章节的同名字段）
    sec_match = re.search(
        r"^##\s*3\.\s*用户画像.*?(?=^##\s*\d+\.\s|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    if not sec_match:
        return set(), set()
    sec_text = sec_match.group(0)
    role_ids = set(ROLE_ID_FIELD_RE.findall(sec_text))
    raw_names = ROLE_NAME_FIELD_RE.findall(sec_text)
    # 过滤占位符（含【】视为模板未替换）+ 空白
    role_names = {n.strip() for n in raw_names if n.strip() and "【" not in n and "】" not in n}
    return role_ids, role_names


# ── 校验 1｜scaffold.json 格式 ────────────────────────────────────────────────

MODULE_ID_RE = re.compile(r"^M\d{2}$")
PAGE_ID_RE = re.compile(r"^P\d{2}$")
PRD_ID_RE = re.compile(r"^H-(M\d{2})-(P\d{2})-[\w-]+$")


def check_scaffold(data: dict, r: Report) -> None:
    r.section("scaffold.json 格式与编号")

    for key in ("product", "platforms", "modules"):
        if key not in data:
            r.fail(f"scaffold.json 缺少必填字段：{key}")
            return

    if not isinstance(data["modules"], list) or len(data["modules"]) == 0:
        r.fail("scaffold.json modules 必须为非空数组（至少 1 个模块）")
        return

    seen_mods: set[str] = set()
    seen_prd_ids: dict[str, str] = {}

    mod_ok = page_ok = state_ok = prd_ok = nonempty_ok = True

    # 模块 id 集合（供 logic-only 模块的 ui_carrier_modules 引用完整性校验）
    all_mod_ids = {m.get("id") for m in data["modules"] if m.get("id")}

    for mod in data["modules"]:
        # pages 字段类型校验
        if not isinstance(mod.get("pages"), list):
            r.fail(f"[{mod.get('id', '?')}] pages 必须为数组类型")
            nonempty_ok = False
            continue
        # 边界条件：pages 数组非空 / logic-only 模块特例
        if len(mod.get("pages", [])) == 0:
            # logic-only 模块（业务逻辑层 / API 层 / 无 UI 承载）：pages=[] 合法
            # 但必须满足：①含 ui_carrier_modules 数组字段 ②数组非空 ③引用 scaffold.modules 内的 id
            # SSOT：agent_dispatch_protocol.md §scaffold v2.0 schema「logic-only 模块」段
            ui_carriers = mod.get("ui_carrier_modules")
            if ui_carriers is None:
                r.fail(
                    f"[{mod.get('id', '?')}] pages=[] 为 logic-only 模块语义，"
                    f"必须含 ui_carrier_modules 字段指向承载 UI 的模块 id 列表"
                    f"（详 agent_dispatch_protocol.md §scaffold v2.0 schema logic-only 段）"
                )
                nonempty_ok = False
                continue
            if not isinstance(ui_carriers, list) or len(ui_carriers) == 0:
                r.fail(
                    f"[{mod.get('id', '?')}] ui_carrier_modules 必须为非空数组"
                )
                nonempty_ok = False
                continue
            # 自引检查（SSOT #50 D-自引防御）：本模块不可承载自己的 UI
            cur_mid = mod.get("id", "?")
            if cur_mid in ui_carriers:
                r.fail(
                    f"[{cur_mid}] ui_carrier_modules 含本模块自身（自引非法，"
                    f"logic-only 模块的 UI 必须由其他承载模块承担）"
                )
                nonempty_ok = False
                continue
            invalid_refs = [ref for ref in ui_carriers if ref not in all_mod_ids]
            if invalid_refs:
                r.fail(
                    f"[{cur_mid}] ui_carrier_modules 引用不存在的模块 id：{invalid_refs}"
                    f"（必须 ⊂ scaffold.modules[].id）"
                )
                nonempty_ok = False
                continue
            # 禁指向其他 logic-only 模块（SSOT #50 D-链式/环引防御）：承载者必须是 pages 非空的真实 UI 模块
            logic_only_ids = {
                m.get("id") for m in data["modules"]
                if m.get("id") and isinstance(m.get("pages"), list) and len(m.get("pages", [])) == 0
            }
            logic_only_refs = [
                ref for ref in ui_carriers
                if ref != cur_mid and ref in all_mod_ids and ref in logic_only_ids
            ]
            if logic_only_refs:
                r.fail(
                    f"[{cur_mid}] ui_carrier_modules 指向其他 logic-only 模块：{logic_only_refs}"
                    f"（承载者必须是 pages 非空的真实 UI 模块；禁链式 / 禁环引）"
                )
                nonempty_ok = False
                continue
            # logic-only 模块校验通过，跳过 pages[].states 校验
            continue
        for p in mod["pages"]:
            if not isinstance(p.get("states"), list) or len(p.get("states", [])) == 0:
                r.fail(f"[{mod.get('id', '?')}-{p.get('id', '?')}] states 必须为非空数组（至少 1 个状态）")
                nonempty_ok = False

    for mod in data["modules"]:
        mid = mod.get("id", "")
        if not MODULE_ID_RE.match(mid):
            r.fail(f"模块编号格式错误：{mid!r}（应为 M 后跟两位数字）")
            mod_ok = False
            continue
        if mid in seen_mods:
            r.fail(f"模块编号重复：{mid}")
            mod_ok = False
            continue
        seen_mods.add(mid)

        if "pages" not in mod or not isinstance(mod["pages"], list):
            r.fail(f"[{mid}] 缺少 pages 列表")
            continue

        seen_pages: set[str] = set()
        for page in mod["pages"]:
            pid = page.get("id", "")
            if not PAGE_ID_RE.match(pid):
                r.fail(f"[{mid}] 页面编号格式错误：{pid!r}（应为 P 后跟两位数字）")
                page_ok = False
                continue
            if pid in seen_pages:
                r.fail(f"[{mid}] 页面编号重复：{pid}")
                page_ok = False
                continue
            seen_pages.add(pid)

            if "states" not in page or not isinstance(page["states"], list):
                r.fail(f"[{mid}-{pid}] 缺少 states 列表")
                continue

            seen_states: set[str] = set()
            for state in page["states"]:
                sname = state.get("name", "")
                prd_id = state.get("prd_id", "")
                if not sname:
                    r.fail(f"[{mid}-{pid}] 存在未命名的状态")
                    state_ok = False
                elif sname in seen_states:
                    r.fail(f"[{mid}-{pid}] 状态名重复：{sname}")
                    state_ok = False
                else:
                    seen_states.add(sname)

                m = PRD_ID_RE.match(prd_id)
                if not m:
                    r.fail(f"[{mid}-{pid}] prd_id 格式错误：{prd_id!r}")
                    prd_ok = False
                    continue
                if m.group(1) != mid or m.group(2) != pid:
                    r.fail(
                        f"prd_id 内部编号与所属层级不一致：{prd_id}"
                        f"（应含 {mid}-{pid}）"
                    )
                    prd_ok = False
                if prd_id in seen_prd_ids:
                    r.fail(
                        f"prd_id 重复：{prd_id}"
                        f"（已在 {seen_prd_ids[prd_id]} 出现）"
                    )
                    prd_ok = False
                else:
                    seen_prd_ids[prd_id] = f"{mid}-{pid}-{sname}"

            # 内嵌子组件 prd_id 校验（SSOT #76 R3）：emb id 页内唯一 + 各内嵌状态
            # prd_id 格式 / 父页作用域 / 全局唯一（与直挂 states 同 seen_prd_ids 池查撞号）。
            # 可选字段——无 embedded_components → 跳过（向后兼容，零变化）。
            embs = page.get("embedded_components")
            if isinstance(embs, list):
                seen_emb_ids: set[str] = set()
                for emb in embs:
                    if not isinstance(emb, dict):
                        r.fail(f"[{mid}-{pid}] embedded_components 项非对象")
                        prd_ok = False
                        continue
                    eid = emb.get("id", "")
                    if not eid:
                        r.fail(f"[{mid}-{pid}] embedded_components 项缺 id")
                        prd_ok = False
                    elif eid in seen_emb_ids:
                        r.fail(f"[{mid}-{pid}] embedded_components id 页内重复：{eid}")
                        prd_ok = False
                    else:
                        seen_emb_ids.add(eid)
                    for st in emb.get("states", []) or []:
                        if not isinstance(st, dict):
                            continue
                        e_prd = st.get("prd_id", "")
                        em = PRD_ID_RE.match(e_prd)
                        if not em:
                            r.fail(f"[{mid}-{pid}] 内嵌 prd_id 格式错误：{e_prd!r}（emb={eid}）")
                            prd_ok = False
                            continue
                        if em.group(1) != mid or em.group(2) != pid:
                            r.fail(
                                f"内嵌 prd_id 内部编号与父页层级不一致：{e_prd}"
                                f"（应含 {mid}-{pid}）"
                            )
                            prd_ok = False
                        if e_prd in seen_prd_ids:
                            r.fail(
                                f"内嵌 prd_id 重复：{e_prd}"
                                f"（已在 {seen_prd_ids[e_prd]} 出现）"
                            )
                            prd_ok = False
                        else:
                            seen_prd_ids[e_prd] = f"{mid}-{pid}-{eid}-{st.get('name', '')}"

    if mod_ok:
        r.ok(f"模块编号格式与唯一性（{len(seen_mods)} 个）")
    if page_ok:
        total_pages = sum(len(m["pages"]) for m in data["modules"] if "pages" in m)
        r.ok(f"页面编号格式与模块内唯一性（共 {total_pages} 页）")
    if state_ok:
        r.ok("状态名在页面内唯一")
    if prd_ok:
        r.ok(f"prd_id 格式与全局唯一性（{len(seen_prd_ids)} 个）")

    # depends_on 引用合法性（v2.0 对象数组：{module, kind, target}）
    # `pm-workflow/rules/agent_dispatch_protocol.md` v2.0 schema 字段说明承诺：target 必须能在被依赖模块中解析到（precheck 校验）
    # 4 类 kind 解析：
    #   section_jump → target ∈ 被依赖模块的 prd_id 集合
    #   shared_component → target ∈ owner_assignments 全局 proj 并集 + pub 索引（fb-* / pub.L*.*）+ fb-fallback class
    #   data_flow → 字段名格式校验（产品定义 §9 markdown 自由文本，降级 WARN）
    #   permission → 角色名格式校验（产品定义 §3 markdown 自由文本，降级 WARN）
    deps_ok = True
    target_warn_count = 0

    # 预计算：每个模块的 prd_id 集合
    prd_ids_by_module: dict[str, set[str]] = {}
    for m in data["modules"]:
        mid_p = m.get("id", "")
        ids: set[str] = set()
        for page in m.get("pages", []):
            # SSOT #76 R3：含内嵌子组件状态帧（section_jump target 可指向内嵌帧）
            ids.update(iter_page_prd_ids(page))
        prd_ids_by_module[mid_p] = ids

    # 预计算：全局 owner_assignments 中的 proj id 集合
    # 兜底校验：同一 proj_id 不得被多个模块同时声明为 owner（gen_scaffold
    # validate_v2_schema 应已拦下；此处兜 changeRequest 未加 --force-rescaffold
    # 或人工编辑 scaffold.json 后只跑 precheck 的边缘场景）
    all_proj_ids: set[str] = set()
    proj_claimers: dict[str, list[str]] = {}
    for m in data["modules"]:
        mid = m.get("id", "?")
        for proj_id in m.get("owner_assignments", {}).keys():
            all_proj_ids.add(proj_id)
            proj_claimers.setdefault(proj_id, []).append(mid)
    for proj_id, claimers in proj_claimers.items():
        if len(claimers) > 1:
            r.fail(
                f"scaffold.json owner_assignments 冲突：proj_id {proj_id!r} 被多个模块"
                f"同时声明为 owner: {claimers}（应仅顺序最靠前者声明；通常说明 PM "
                f"修改了 scaffold.json 但未重跑 gen_scaffold.py 校验）"
            )

    # 预计算：pub 索引 + fb-fallback.css 登记的 fb-* / pub.L*.*
    registered_fb_pub: set[str] = set()
    if PUB_INDEX_PATH.exists():
        pub_md = PUB_INDEX_PATH.read_text(encoding="utf-8")
        registered_fb_pub.update(re.findall(r"\bbj-[a-z][\w-]*", pub_md))
        registered_fb_pub.update(re.findall(r"\bpub\.L\d+\.[\w-]+", pub_md))
    if FB_FALLBACK_CSS_PATH.exists():
        css_text = FB_FALLBACK_CSS_PATH.read_text(encoding="utf-8")
        registered_fb_pub.update(
            t.lstrip(".") for t in re.findall(r"\.fb-[a-z][\w-]*", css_text)
        )

    shared_component_pool = all_proj_ids | registered_fb_pub

    # 字段名 / 角色名格式校验（中英文 + 常见分隔符）
    data_flow_target_re = re.compile(r"^[\w一-鿿][\w一-鿿\s\-\./]*$")
    permission_target_re = re.compile(r"^[\w一-鿿][\w一-鿿\s\-/]*$")

    # 加载产品定义 §3 角色清单 SSOT（消化双锚 #24）
    product = data.get("product", "").strip()
    role_ids_set, role_names_set = _load_role_lists_from_product_def(product)
    role_ssot_loaded = bool(role_ids_set or role_names_set)

    for mod in data["modules"]:
        mid = mod.get("id", "")
        deps = mod.get("depends_on", [])
        if not isinstance(deps, list):
            r.fail(f"[{mid}] depends_on 必须为数组,实际：{type(deps).__name__}")
            deps_ok = False
            continue
        for i, dep in enumerate(deps):
            if not isinstance(dep, dict):
                r.fail(
                    f"[{mid}] depends_on[{i}] 必须为对象 "
                    f"{{module, kind, target}}（v2.0 schema），实际：{type(dep).__name__}"
                )
                deps_ok = False
                continue
            target_mod = dep.get("module")
            if not target_mod:
                r.fail(f"[{mid}] depends_on[{i}] 缺 module 字段")
                deps_ok = False
                continue
            if target_mod not in seen_mods:
                r.fail(
                    f"[{mid}] depends_on[{i}].module 引用不存在的模块：{target_mod!r}"
                    f"（已声明模块：{sorted(seen_mods)}）"
                )
                deps_ok = False
                continue  # module 错则不再校 target,避免级联错误
            if target_mod == mid:
                r.fail(f"[{mid}] depends_on[{i}] 不可包含自身（module={target_mod}）")
                deps_ok = False
                continue

            # —— target 解析（`pm-workflow/rules/agent_dispatch_protocol.md` v2.0 schema 字段说明承诺履行）——
            kind = dep.get("kind", "")
            target = dep.get("target", "")
            if not target:
                r.fail(f"[{mid}] depends_on[{i}] 缺 target 字段")
                deps_ok = False
                continue

            if kind == "section_jump":
                valid_prd_ids = prd_ids_by_module.get(target_mod, set())
                if target not in valid_prd_ids:
                    # SSOT #50 B-section_jump 防御：target_mod 是 logic-only（pages=[]）→ 给明确指引
                    target_mod_obj = next(
                        (m for m in data["modules"] if m.get("id") == target_mod), None
                    )
                    is_logic_only = (
                        target_mod_obj is not None
                        and isinstance(target_mod_obj.get("pages"), list)
                        and len(target_mod_obj.get("pages", [])) == 0
                    )
                    if is_logic_only:
                        ui_carriers = target_mod_obj.get("ui_carrier_modules", [])
                        r.fail(
                            f"[{mid}] depends_on[{i}] kind=section_jump → target={target!r} "
                            f"指向 logic-only 模块 {target_mod}（pages=[]，无 prd_id）；"
                            f"section_jump 仅允许指向有独立 UI 页面的模块，请改为 "
                            f"kind=data_flow / shared_component / permission，"
                            f"或将 target 指向承载模块 {ui_carriers} 之一的 prd_id"
                        )
                    else:
                        r.fail(
                            f"[{mid}] depends_on[{i}] kind=section_jump → target={target!r} "
                            f"不在被依赖模块 {target_mod} 的 prd_id 集合中"
                            f"（合法值：{sorted(valid_prd_ids)}）"
                        )
                    deps_ok = False
            elif kind == "shared_component":
                if target not in shared_component_pool:
                    proj_hint = sorted(all_proj_ids) if all_proj_ids else "（本期 owner_assignments 为空）"
                    r.fail(
                        f"[{mid}] depends_on[{i}] kind=shared_component → target={target!r} "
                        f"不在合法集合中："
                        f"owner_assignments 全局 proj={proj_hint} / "
                        f"pub 索引 fb-* / pub.L*.* + fb-fallback class（共 {len(registered_fb_pub)} 项已登记）"
                    )
                    deps_ok = False
            elif kind == "data_flow":
                if not data_flow_target_re.match(target):
                    r.fail(
                        f"[{mid}] depends_on[{i}] kind=data_flow → target={target!r} "
                        f"格式非法（应为字段名：中英文 + 数字 + 常见分隔符 _-./）"
                    )
                    deps_ok = False
                else:
                    r.warn(
                        f"[{mid}] depends_on[{i}] kind=data_flow → target={target!r} "
                        f"无 SSOT 解析点（产品定义 §9 是 markdown 自由文本），仅做格式校验；"
                        f"主管 D-05 维度需手工核对该字段是否存在于产品定义 §9"
                    )
                    target_warn_count += 1
            elif kind == "permission":
                if not permission_target_re.match(target):
                    r.fail(
                        f"[{mid}] depends_on[{i}] kind=permission → target={target!r} "
                        f"格式非法（应为角色名：中英文 + 常见分隔符 _-/）"
                    )
                    deps_ok = False
                elif role_ssot_loaded:
                    # SSOT 双锚 #24 升级：基于 §3 真源校验,WARN 升 FAIL
                    if target not in role_ids_set and target not in role_names_set:
                        r.fail(
                            f"[{mid}] depends_on[{i}] kind=permission → target={target!r} "
                            f"不在产品定义 §3 角色清单中"
                            f"（合法 ID={sorted(role_ids_set)} / 名={sorted(role_names_set)}）；"
                            f"调整方向：先改 §3 真源,再同步 scaffold"
                        )
                        deps_ok = False
                else:
                    # 产品定义 §3 真源未加载（文件不存在或缺结构化字段）→ 降级 WARN
                    r.warn(
                        f"[{mid}] depends_on[{i}] kind=permission → target={target!r} "
                        f"无法加载产品定义 §3 角色 SSOT（文件未生成 / 缺 `**角色 ID**` 结构化字段）；"
                        f"仅做格式校验；待 §3 真源就绪后本项升级为 FAIL"
                    )
                    target_warn_count += 1
            else:
                # 非法 kind 兜底（防御深度第二层）：
                # gen_scaffold.py:465-468 在生成时已拦截；但自然语言调整路径派发 PM 修改
                # scaffold.json 非编号字段（depends_on 等）后不重跑 gen_scaffold 时
                # precheck 单独跑仍需兜底（changeRequest 流程会强制 --force-rescaffold，
                # 不在本兜底覆盖范围；中断恢复 / 测试场景同理）
                r.fail(
                    f"[{mid}] depends_on[{i}].kind={kind!r} 不在合法枚举内"
                    f"（合法值：section_jump / shared_component / data_flow / permission）"
                )
                deps_ok = False

    # 传递闭环检测（`pm-workflow/rules/agent_dispatch_protocol.md` Step 3/Step 5 派发按 depends_on 拓扑等待，
    # 环路会导致编排器无限等待；line 268 仅拦截 1 步自环，此处补 ≥2 步传递闭环）
    # 图只采纳 module 字段合法的边（其他边已在上方报 fail，跳过避免误报级联）
    #
    # **仅对 shared_component（CSS owner 强依赖）构图**——其他 kind 是非派发依赖,会引入误报循环:
    #   - section_jump（页面跳转）天然双向（A→B 看详情、B→A 返回列表）,是真实业务路径而非派发依赖
    #   - data_flow / permission 是松约束,不影响 Step 3/Step 5 派发顺序
    # **proj 自引用 owner 跳过**：mid 即 target proj 的 owner 时,本质为嵌入引用而非依赖
    # 来源：PM 业务任务期间识别（commit 616bd71 "修复流程逻辑问题"实际未走规范路径）,
    #       本次走 workflow-evolution skill 路径正式合并（issue 2026-05-07_1400 条 2 排查）
    proj_id_to_owner: dict[str, str] = {}
    for proj_id, claimers in proj_claimers.items():
        if claimers:
            proj_id_to_owner[proj_id] = claimers[0]
    graph: dict[str, list[str]] = {mid: [] for mid in seen_mods}
    for mod in data["modules"]:
        mid = mod.get("id", "")
        if mid not in seen_mods:
            continue
        for dep in mod.get("depends_on", []):
            if not isinstance(dep, dict):
                continue
            if dep.get("kind") != "shared_component":
                continue  # section_jump / data_flow / permission 非派发依赖
            target = dep.get("target", "")
            # 自引用 owner 跳过（mid 即 target proj 的 owner,本质为嵌入引用而非依赖）
            if target.startswith("proj.") and proj_id_to_owner.get(target) == mid:
                continue
            tgt = dep.get("module")
            if tgt and tgt in seen_mods and tgt != mid:
                graph[mid].append(tgt)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}
    parent: dict[str, str] = {}
    cycle_path: list[str] | None = None

    def dfs(u: str) -> list[str] | None:
        color[u] = GRAY
        for v in graph[u]:
            if color[v] == GRAY:
                # 回溯 parent 链构造环路：v → ... → u → v
                path = [v]
                cur = u
                while cur != v:
                    path.append(cur)
                    cur = parent[cur]
                path.append(v)
                path.reverse()
                return path
            if color[v] == WHITE:
                parent[v] = u
                cyc = dfs(v)
                if cyc:
                    return cyc
        color[u] = BLACK
        return None

    for node in graph:
        if color[node] == WHITE:
            cyc = dfs(node)
            if cyc:
                cycle_path = cyc
                break

    if cycle_path:
        r.fail(
            f"depends_on 存在循环依赖：{' → '.join(cycle_path)}"
            f"（Step 3/Step 5 按拓扑派发会陷入无限等待，必须打断环路；"
            f"通常做法：把其中一条 kind=section_jump/shared_component 改为单向引用，"
            f"或将共享逻辑抽到独立模块作为公共依赖）"
        )
        deps_ok = False

    if deps_ok:
        suffix = f"；{target_warn_count} 条 data_flow/permission 弱校验通过" if target_warn_count else ""
        r.ok(
            f"depends_on 引用合法（全部依赖模块均已声明且无自依赖；"
            f"target 按 kind 解析：section_jump/shared_component 严格校验，"
            f"data_flow/permission 格式校验{suffix}）"
        )


# ── 校验 1.4｜scaffold roles 字段格式 + §3 SSOT 一致性（消化双锚 #24）─────────

def check_scaffold_roles_format(data: dict, r: Report) -> None:
    """校验 scaffold.json 全部 modules[].pages[].states[].roles 数组：
    1. 必为数组（list of strings）
    2. 元素必须 ⊂ §3 角色 ID 集合 OR ⊂ §3 角色名集合
    3. 同一 scaffold 文件内必须统一使用 ID 或名（不混用）

    抽取规范：tmpl_产品定义.md §5「角色名抽取算法」段
    SSOT 双锚 #24（A 组 5/5 完备）"""
    r.section("scaffold roles 字段 ↔ 产品定义 §3 角色清单 SSOT 一致性")

    if "modules" not in data or not isinstance(data["modules"], list):
        return  # check_scaffold 已报错

    product = data.get("product", "").strip()
    role_ids_set, role_names_set = _load_role_lists_from_product_def(product)
    if not role_ids_set and not role_names_set:
        r.warn(
            f"产品定义 §3 角色 SSOT 未加载（文件 outputs/产品定义_{product}_latest.md 不存在 "
            f"/ §3 缺 `**角色 ID**：[role-N]` 与 `**角色名**：[xxx]` 结构化字段）；"
            f"scaffold roles 字段降级为格式校验。建议补全 §3 后重跑。"
        )

    # 收集本 scaffold 全部 roles 元素 + 位置（mid/pid/sname）
    all_roles_with_loc: list[tuple[str, str, str, str]] = []  # (mid, pid, sname, role_value)
    fmt_ok = True
    for mod in data["modules"]:
        mid = mod.get("id", "?")
        for page in mod.get("pages", []):
            pid = page.get("id", "?")
            for state in page.get("states", []):
                sname = state.get("name", "?")
                roles = state.get("roles", None)
                if roles is None:
                    # 缺字段 → 默认空数组（公开访问），不报错
                    continue
                if not isinstance(roles, list):
                    r.fail(
                        f"[{mid}-{pid}-{sname}] roles 必须是数组,实际：{type(roles).__name__}"
                    )
                    fmt_ok = False
                    continue
                for el in roles:
                    if not isinstance(el, str):
                        r.fail(
                            f"[{mid}-{pid}-{sname}] roles 元素必须是字符串,实际：{type(el).__name__}（值={el!r}）"
                        )
                        fmt_ok = False
                        continue
                    el_stripped = el.strip()
                    if el != el_stripped:
                        r.fail(
                            f"[{mid}-{pid}-{sname}] roles 元素 {el!r} 含首尾空格,须 trim"
                        )
                        fmt_ok = False
                        continue
                    if not el_stripped:
                        r.fail(f"[{mid}-{pid}-{sname}] roles 含空字符串元素")
                        fmt_ok = False
                        continue
                    all_roles_with_loc.append((mid, pid, sname, el_stripped))

    if not fmt_ok:
        return  # 格式都不对,无须做 SSOT 一致性校验

    if not all_roles_with_loc:
        r.ok("scaffold roles 字段格式：本 scaffold 无角色限制（全部 roles 为空数组）")
        return

    # 推断本 scaffold 用的格式：全部 ⊂ ID 集合 OR 全部 ⊂ 名集合
    if not (role_ids_set or role_names_set):
        # SSOT 未加载,仅汇报
        r.warn(
            f"scaffold roles 共 {len(all_roles_with_loc)} 处填值,但 §3 真源未加载,"
            f"无法做 SSOT 一致性校验"
        )
        return

    all_values = [v for (_, _, _, v) in all_roles_with_loc]
    matches_id = [v for v in all_values if v in role_ids_set]
    matches_name = [v for v in all_values if v in role_names_set]
    matches_either = set(matches_id) | set(matches_name)
    unknown = [v for v in all_values if v not in matches_either]

    if unknown:
        # 去重并示例位置
        unknown_set = sorted(set(unknown))
        sample_loc = next(
            (loc for loc in all_roles_with_loc if loc[3] in unknown_set), None
        )
        loc_hint = f"（首处出现：{sample_loc[0]}-{sample_loc[1]}-{sample_loc[2]}）" if sample_loc else ""
        r.fail(
            f"scaffold roles 含 {len(unknown_set)} 个未在 §3 登记的字面值：{unknown_set}{loc_hint}；"
            f"§3 合法 ID={sorted(role_ids_set)} / 名={sorted(role_names_set)}；"
            f"调整方向：先改 §3 真源,再同步 scaffold"
        )
        return

    # 全部已知 → 检查是否统一使用 ID 或名（不混用）
    use_id = bool(set(matches_id))
    use_name = bool(set(matches_name) - set(matches_id))  # 减 ID 防 ID 也恰好等于名的边界
    if use_id and use_name:
        # 真混用：明确分类哪些是 ID,哪些是名
        id_only = [v for v in set(all_values) if v in role_ids_set and v not in role_names_set]
        name_only = [v for v in set(all_values) if v in role_names_set and v not in role_ids_set]
        if id_only and name_only:
            r.fail(
                f"scaffold roles 混用了角色 ID 和角色名（同一文件内必须统一）："
                f"用 ID 的元素={sorted(id_only)} / 用名的元素={sorted(name_only)}；"
                f"调整方向：选定 ID 或名后,全部 roles 元素改为同一种"
            )
            return

    fmt_label = "ID" if use_id else "名"
    r.ok(
        f"scaffold roles 字段：{len(all_roles_with_loc)} 处填值,全部 ⊂ §3 角色 {fmt_label} 清单"
    )


# ── 校验 1.45｜SSOT #14 状态命名一致性 NB-WE-13 ──────────────────────────────
#
# 双锚 #14（状态枚举表 ↔ 视觉帧映射）的"语义命名一致性"漏洞 NB-WE-13。
# 旧 precheck 仅检数对称（spec 中 H- 锚点 ⊃ scaffold prd_id 集合,见 check_prd 第 4 步）；
# 不查 scaffold.states[].name 字面规范 + name ↔ prd_id 后缀字面对称。
# 历史教训（bujue-quotation-tool）：曾出现 PM 在 scaffold 写 name="提交中" / "Loading" / "submit_ing"
# 三种乱写,导致 UI Agent 拿到 scaffold token 后无法在 spec 自由文本中定位对应状态。
#
# 三维兜底：
# 1. NAME_RE：`[a-z][a-z0-9-]*`——拒绝中文 / 大写 / 下划线 / 空格 / 数字开头
# 2. prd_id 后缀字面 = name（即 prd_id 必须 endswith "-" + name,防止人工手改 scaffold 后漂移）
# 3. spec 中每页「状态枚举表」行数 = scaffold 同页 states 数组长度（数对称补全）
#
# 5% 中文术语漂移（spec 写"暂无数据态" / scaffold 写 empty）属业务语义层,留给人审。
STATE_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def check_state_naming_convention(data: dict, r: Report) -> None:
    """SSOT #14 NB-WE-13 — scaffold 状态命名规范 + name ↔ prd_id 后缀字面对称。"""
    r.section("SSOT #14 状态命名一致性（name 字面规范 + prd_id 后缀对称）")

    name_violations: list[str] = []
    suffix_violations: list[str] = []
    total_states = 0

    for mod in data.get("modules", []):
        mid = mod.get("id", "?")
        for page in mod.get("pages", []):
            pid = page.get("id", "?")
            for state in page.get("states", []):
                total_states += 1
                sname = state.get("name", "")
                prd_id = state.get("prd_id", "")

                if not STATE_NAME_RE.match(sname):
                    name_violations.append(f"[{mid}-{pid}] name={sname!r}")

                expected_suffix = f"-{sname}"
                if sname and not prd_id.endswith(expected_suffix):
                    suffix_violations.append(
                        f"[{mid}-{pid}] name={sname!r} ↔ prd_id={prd_id!r}"
                    )

    if name_violations:
        r.fail(
            f"scaffold 状态 name 字面违反 `[a-z][a-z0-9-]*` 命名规范"
            f"（共 {len(name_violations)} 处）："
            f"{name_violations[:5]}{'...' if len(name_violations) > 5 else ''}"
            f" — 拒绝中文 / 首字母大写 / 下划线 / 空格 / 数字开头,统一英文 lowercase token"
        )
    else:
        r.ok(f"scaffold 状态 name 字面规范（{total_states} 个状态全合规）")

    if suffix_violations:
        r.fail(
            f"scaffold prd_id 后缀与 name 字面不对称（共 {len(suffix_violations)} 处）："
            f"{suffix_violations[:5]}{'...' if len(suffix_violations) > 5 else ''}"
            f" — prd_id 必须 endswith '-' + name(防人工手改 scaffold 后漂移)"
        )
    else:
        r.ok(f"scaffold prd_id 后缀与 name 字面对称（{total_states} 个状态全对齐）")


def check_spec_state_table_count(data: dict, spec_md: str, r: Report) -> None:
    """SSOT #14 NB-WE-13 — spec 状态枚举表行数 ↔ scaffold states 数组长度对称。

    对每个 page,扫 spec.md 中 spec_id 段内的「状态枚举表」（表头含「状态 ID」+「对应帧」），
    统计 `| S\\d+ |` 行数,与 scaffold 同 page 的 states 数组长度比对。
    """
    r.section("SSOT #14 spec 状态枚举表 ↔ scaffold states 数对称")

    state_id_re = re.compile(r"^\|\s*S\d+\s*\|", re.MULTILINE)
    mismatches: list[str] = []
    checked_pages = 0
    skipped_pages = 0

    for mod in data.get("modules", []):
        mid = mod.get("id", "?")
        for page in mod.get("pages", []):
            pid = page.get("id", "?")
            spec_id = page.get("spec_id", "")
            scaffold_count = len(page.get("states", []))

            if not spec_id:
                skipped_pages += 1
                continue

            anchor = f'<a id="{spec_id}"></a>'
            anchor_md = f"<{spec_id}>"
            spec_id_pos = -1
            for marker in (anchor, anchor_md, f"{spec_id}"):
                pos = spec_md.find(marker)
                if pos >= 0:
                    spec_id_pos = pos
                    break
            if spec_id_pos < 0:
                skipped_pages += 1
                continue

            next_section_re = re.compile(r"\n###?\s+P-", re.MULTILINE)
            m = next_section_re.search(spec_md, spec_id_pos + 1)
            section_end = m.start() if m else len(spec_md)
            section_text = spec_md[spec_id_pos:section_end]

            spec_count = len(state_id_re.findall(section_text))

            if spec_count == 0:
                continue

            checked_pages += 1
            if spec_count != scaffold_count:
                mismatches.append(
                    f"[{mid}-{pid}] spec 状态枚举表 {spec_count} 行 ≠ "
                    f"scaffold states {scaffold_count} 项"
                )

    if mismatches:
        r.fail(
            f"spec 状态枚举表行数与 scaffold states 数不对称（共 {len(mismatches)} 处）："
            f"{mismatches[:5]}{'...' if len(mismatches) > 5 else ''}"
        )
    elif checked_pages == 0:
        r.warn("spec 中未找到状态枚举表（如已用其他格式描述状态请确认）")
    else:
        r.ok(f"spec 状态枚举表行数 ↔ scaffold states 数对称（{checked_pages} 个页面）")


# ── 校验 1.5｜S4-05 状态清单覆盖 ──────────────────────────────────────────────
#
# rule_hard_constraints.md S4-05 要求每页状态枚举至少含「默认 + 加载/空 + 错误/禁用」
# 的语义覆盖（条件附加状态——越权提示 / 确认弹窗 / 角色差异——由 Agent 人工审核兜底）。
# 旧 precheck 仅校验 states 数组非空，对"PM 偷懒只写 default"无防御；本节按关键字
# 分类做兜底——单状态名可同时归多类（如「加载错误」同时归 timing + constraint）。

# 关键字扩展来源：PM 业务任务期间识别（合并自 Downloads PM 副本，issue 2026-05-07_1400 条 2 排查）
# - DEFAULT 加 management/管理（业务后台管理面板默认态）；不加 PM 版本的 "main"——
#   "main" 子串匹配会误伤业务命名（main-flow / main-page 等），如未来确需可改边界匹配
# - TIMING 加 skeleton/骨架（外部依赖加载占位）
# - CONSTRAINT 加 skeleton/骨架（双归类:外部依赖未就绪占位）+ expired/失效/revoke/撤销 +
#   not-found/缺失 + no-permission/越权/无权限（覆盖真实业务约束态）
DEFAULT_STATE_KEYWORDS = ("default", "默认", "正常", "标准", "management", "管理")
TIMING_STATE_KEYWORDS = (
    "loading", "loaded", "empty", "加载", "空",
    "skeleton", "骨架",
)
CONSTRAINT_STATE_KEYWORDS = (
    "error", "disabled", "错误", "禁用", "异常", "失败",
    "skeleton", "骨架",  # external-skeleton / preview-app-skeleton 等"外部依赖未就绪"占位
    "expired", "失效", "revoked", "revoke", "撤销",
    "not-found", "not_found", "缺失",
    "no-permission", "no_permission", "no-perm", "越权", "无权限",
)


def _classify_state_name(name: str) -> set[str]:
    """根据状态名关键字返回它命中的覆盖类别集合。空集 = 不命中任何 S4-05 关键字。"""
    n = name.strip().lower()
    cats: set[str] = set()
    for kw in DEFAULT_STATE_KEYWORDS:
        if kw.lower() in n:
            cats.add("default")
            break
    for kw in TIMING_STATE_KEYWORDS:
        if kw.lower() in n:
            cats.add("timing")
            break
    for kw in CONSTRAINT_STATE_KEYWORDS:
        if kw.lower() in n:
            cats.add("constraint")
            break
    return cats


def check_state_coverage(data: dict, r: Report) -> None:
    """S4-05：每页状态枚举至少覆盖 default + (loading|empty) + (error|disabled) 三类。"""
    r.section("S4-05 状态清单覆盖（默认 + 时序态 + 约束态）")

    if not isinstance(data.get("modules"), list):
        return  # 已在 check_scaffold 报错

    fail_count = 0
    pass_count = 0
    skip_count = 0
    for mod in data["modules"]:
        mid = mod.get("id", "?")
        for page in mod.get("pages", []):
            pid = page.get("id", "?")
            states = page.get("states", [])
            if not isinstance(states, list) or len(states) == 0:
                skip_count += 1  # 已在 check_scaffold 报「states 必须非空」,本节不重复
                continue

            covered: set[str] = set()
            for s in states:
                covered |= _classify_state_name(s.get("name", ""))

            missing: list[str] = []
            if "default" not in covered:
                missing.append("default 态（关键字：default / 默认 / 正常 / 标准）")
            if "timing" not in covered:
                missing.append("loading/empty 态二选一（关键字：loading / empty / 加载 / 空）")
            if "constraint" not in covered:
                missing.append("error/disabled 态二选一（关键字：error / disabled / 错误 / 禁用 / 异常 / 失败）")

            if missing:
                state_names = [s.get("name", "?") for s in states]
                r.fail(
                    f"[{mid}-{pid}] S4-05 状态清单不达标：缺 {len(missing)}/3 必备类别 → "
                    f"{' | '.join(missing)}；现有状态：{state_names}"
                )
                fail_count += 1
            else:
                pass_count += 1

    if fail_count == 0 and pass_count > 0:
        suffix = f"（{skip_count} 个页面已在 check_scaffold 报 states 空）" if skip_count else ""
        r.ok(f"S4-05 状态清单覆盖：{pass_count} 个页面均覆盖 default + 时序态 + 约束态{suffix}")


# ── 校验 2｜prd.html ──────────────────────────────────────────────────────────

PLACEHOLDER_MARKERS: list[tuple[str, str]] = [
    ("<!-- [FRAME:",        "未替换的 [FRAME:...] 占位（assemble.py prd 未执行或草稿缺失对应帧）"),
    ("<!-- [SPEC-NAV]",     "未替换的 [SPEC-NAV] 占位（gen_scaffold.py 未执行）"),
    ("<!-- [SITEMAP-NAV]",  "未替换的 [SITEMAP-NAV] 占位（gen_scaffold.py 未执行；Item 2 页面架构总览组）"),
    ("<!-- [PROTO-NAV]",    "未替换的 [PROTO-NAV] 占位"),
    ("<!-- [COVER-PAGE]",   "未替换的 [COVER-PAGE] 占位"),
    ("<!-- [GUIDE-PAGE]",   "未替换的 [GUIDE-PAGE] 占位"),
    ("<!-- [CHANGELOG-PAGE]", "未替换的 [CHANGELOG-PAGE] 占位"),
    ("<!-- [MODULE SPEC]",  "未替换的 [MODULE SPEC] 占位"),
]

SPEC_SECTION_IDS = [
    "spec-background", "spec-persona", "spec-permission", "spec-journey",
    "spec-business-flow",  # A-04.2 业务流程图（工程视角,与 A-04 用户旅程互补）
    "spec-feature",    "spec-data",    "spec-exception",  "spec-nonfunc",
]

# ── Mermaid 局部豁免清单 ──────────────────────────────────────────────────────
# 来源：proto_contract.md §十一「prd.html 中 Mermaid 局部豁免规则」
# 仅当 mermaid 块所属 <section id="..."> 的 id 含以下任一关键字（不区分大小写）时豁免；
# 其他场景的 mermaid 用法均报 FAIL。
# 未来扩展（如新增「时序图」类豁免 section）只需追加本清单即可，校验代码无需改。
MERMAID_ALLOWED_SECTION_KEYWORDS: tuple[str, ...] = (
    "journey",       # A-04 用户旅程可视化（spec-journey / spec-user-journey）
    "user-journey",  # 显式别名
    "flow",          # 业务流程图 / 状态流转图（spec-business-flow 等）
    "sitemap",       # 页面架构总览（spec-sitemap）：提议1 页面层级图(#38) +
                     # 提议3 模块依赖图(#40) colocate；S4-29/S4-31 强制该
                     # section 必含 mermaid → 同族对称必须豁免（agent_methodology
                     # §七.2；缺则与 S4-29/31 互斥死锁，下游 NB 上报修复）
)


def _blank_mermaid_scan_noise(html: str) -> str:
    """把 `<script>...</script>` 与 `<!-- ... -->` 整段等长留白（空格填充，
    字符偏移完全保持）后返回，供 check_prd §5 mermaid 检测扫描。

    Why（同族对称硬化，下游 Supervisor NB-L2-SITEMAP-RENDER-FP）：mermaid 渲染
    JS（如 `renderStaticMermaid` / `switchJourneyView` 的注释与选择器）合法地
    含字面 ` ```mermaid ` / `<pre class="mermaid">`，经 assemble
    `_overwrite_scripts_from_template`（SSOT #2 派生5）进 outputs/prd 的
    `<script>`；旧实现扫整个 html → 误判为「游离 mermaid 块」FAIL。真实
    mermaid **DOM 节点结构上永不在 `<script>`（JS 文本域）或 `<!-- -->`
    （注释域，浏览器不渲染）内** → 留白这两域零假阴性，仅消除该类假阳性。
    与 9e1a405「触发源加了、检测器未同族对称硬化」同型（agent_methodology §七.2）。

    等长留白而非删除：check_prd §5 用字符 offset 反向定位 `<section>` 包裹关系，
    删除会移位、破坏归属判定；`<section>`/`</section>`/真 `<pre class="mermaid">`
    永不在 script/注释域内，留白不触及它们。
    """
    def _blank(m: "re.Match[str]") -> str:
        return " " * (m.end() - m.start())

    html = re.sub(
        r"<script\b[^>]*>.*?</script>", _blank, html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(r"<!--.*?-->", _blank, html, flags=re.DOTALL)
    return html


def check_prd(data: dict, html: str, r: Report) -> None:
    r.section("prd.html 结构与一致性")

    # 1. 占位注释残留
    residual = []
    for marker, msg in PLACEHOLDER_MARKERS:
        count = html.count(marker)
        if count > 0:
            r.fail(f"{msg} — 残留 {count} 处")
            residual.append(marker)
    if re.search(r"<!--\s*\[MODULE M-?\d+\]:\s*待拼装\s*-->", html):
        r.fail("模板示例占位 <!-- [MODULE M-XX]: 待拼装 --> 未被 gen_scaffold.py 清理")
        residual.append("MODULE M-XX")
    if not residual:
        r.ok("占位注释全部已替换")

    # 2. 每个 prd_id 必须对应 <section id="...">（含内嵌子组件帧，SSOT #76 R3——
    #    内嵌帧同样由 gen_scaffold build_module_sections 派生 <section> + FRAME 占位）
    all_prd_ids = [
        prd_id
        for mod in data.get("modules", [])
        for p in mod.get("pages", [])
        for prd_id in iter_page_prd_ids(p)
    ]
    section_ids = set(re.findall(r'<section[^>]*id="([^"]+)"', html))
    missing = [pid for pid in all_prd_ids if pid not in section_ids]
    if missing:
        shown = missing[:5]
        more = f"... 等 {len(missing)} 个" if len(missing) > 5 else ""
        r.fail(f"prd.html 缺少状态帧 section：{shown}{more}")
    else:
        r.ok(f"全部 {len(all_prd_ids)} 个状态帧 section 就位")

    # 3. 产品规格区 9 节齐全（含 A-04.2 业务流程图 spec-business-flow）
    missing_spec = [s for s in SPEC_SECTION_IDS if s not in section_ids]
    if missing_spec:
        r.fail(f"prd.html 缺少产品规格 section：{missing_spec}")
    else:
        r.ok(f"产品规格区 {len(SPEC_SECTION_IDS)} 个 section 齐全")

    # 4. showSection 目标可解析
    #    WE-F（2026-05-19，下游 R1 修）：showSection JS 用 getElementById 对**任意
    #    元素 id** 生效（非仅 <section>）。WE-B「页面架构总览」nav 的
    #    showSection('sk-hier/arch/mod') 指向 spec-sitemap 内 `<div id="sk-*">`
    #    锚（合法滚动目标），旧 `targets - section_ids` 仅认 <section id> → 误判
    #    orphan（下游 e6f87e4 显形 3 error）。**精确豁免** sk-* 锚命名空间
    #    （gen_scaffold.SITEMAP_NAV_ANCHORS 受控集；不泛接所有 div id，保 section
    #    typo 检出力）。锚 id 真源 = assemble.inject_prd_sitemap `<div id="sk-*">`。
    targets = set(re.findall(r"showSection\(\s*['\"]([^'\"]+)['\"]\s*\)", html))
    sk_div_anchors = set(re.findall(r'<div\s+id\s*=\s*"(sk-[\w-]+)"', html))
    orphan = sorted(targets - section_ids - sk_div_anchors)
    if orphan:
        shown = orphan[:5]
        more = f"... 等 {len(orphan)} 个" if len(orphan) > 5 else ""
        r.fail(f"showSection 指向不存在的 section：{shown}{more}")
    else:
        r.ok(
            f"showSection 跳转目标全部可解析（{len(targets)} 个；"
            f"含 {len(sk_div_anchors)} 个 sk-* div 锚 WE-B/WE-F）"
        )

    # 5. Mermaid 局部豁免检查（proto_contract.md §十一）
    #    规则：
    #      - 默认禁用 mermaid 代码块
    #      - 若 mermaid 块所属 <section id="..."> 的 id 含 MERMAID_ALLOWED_SECTION_KEYWORDS
    #        中任一关键字（不区分大小写），则豁免（PASS）
    #      - 否则报 FAIL，并明示违反 proto_contract §十一 + 所在 section id
    #    实现：①找出所有 mermaid 触发位置（pos 偏移量）②反向定位最近的 <section id="..."> 包裹
    # 同族对称硬化：剥 <script>/注释域后再扫（offset 保持），避免 mermaid 渲染
    # JS 注释/选择器里字面的 ```mermaid / <pre class="mermaid"> 被误判为游离块
    # （NB-L2-SITEMAP-RENDER-FP；真 mermaid DOM 永不在 script/注释域，零假阴性）
    scan = _blank_mermaid_scan_noise(html)
    mermaid_hits: list[tuple[int, str]] = []
    for m in re.finditer(r"```mermaid", scan):
        mermaid_hits.append((m.start(), "```mermaid"))
    for m in re.finditer(
        r'<(?:pre|div)[^>]*\bclass\s*=\s*"[^"]*\bmermaid\b[^"]*"', scan
    ):
        mermaid_hits.append((m.start(), m.group(0)[:60] + "..."))

    if not mermaid_hits:
        r.ok("未检测到 Mermaid 代码")
    else:
        # 预先收集每个 <section id="..."> 的 (start, end, id)，方便反向定位包裹关系
        section_ranges: list[tuple[int, int, str]] = []
        # 用栈匹配 <section> ... </section>（容忍嵌套）
        section_open_re = re.compile(r'<section\b[^>]*\bid\s*=\s*"([^"]+)"', re.IGNORECASE)
        # 简化：扫所有 <section ... id=".."> 与对应 </section>，按嵌套深度配对
        # 因 prd.html 不会让 section 嵌套出现两次相同 id，我们仅记录每个开 tag 的位置 + id
        opens = [(m.start(), m.group(1), m.end()) for m in section_open_re.finditer(scan)]
        closes = [m.start() for m in re.finditer(r'</section\s*>', scan, re.IGNORECASE)]
        # 按位置对开/闭做栈匹配
        events: list[tuple[int, str, str | None]] = []
        for pos, sid, _end in opens:
            events.append((pos, "open", sid))
        for pos in closes:
            events.append((pos, "close", None))
        events.sort(key=lambda x: x[0])
        stack: list[tuple[int, str]] = []  # (open_pos, sid)
        for pos, kind, sid in events:
            if kind == "open" and sid is not None:
                stack.append((pos, sid))
            elif kind == "close" and stack:
                open_pos, popped_sid = stack.pop()
                section_ranges.append((open_pos, pos, popped_sid))

        def find_owning_section(pos: int) -> str | None:
            """返回 pos 所在的最内层 <section id="...">；若不在任何 section 内则返回 None。"""
            best: tuple[int, str] | None = None  # (start, sid) 取 start 最大者（最内）
            for s, e, sid in section_ranges:
                if s < pos < e:
                    if best is None or s > best[0]:
                        best = (s, sid)
            return best[1] if best else None

        violations: list[str] = []
        exempted: list[str] = []
        for pos, snippet in mermaid_hits:
            owner_id = find_owning_section(pos)
            if owner_id is None:
                violations.append(f"游离 mermaid 块（不在任何 <section> 内）@ offset {pos}")
                continue
            owner_lower = owner_id.lower()
            if any(kw in owner_lower for kw in MERMAID_ALLOWED_SECTION_KEYWORDS):
                exempted.append(f"<section id=\"{owner_id}\">")
            else:
                violations.append(
                    f'<section id="{owner_id}"> 内出现 mermaid（仅 id 含 '
                    f'{list(MERMAID_ALLOWED_SECTION_KEYWORDS)} 任一关键字的 section 才豁免）'
                )

        if violations:
            shown = violations[:3]
            more = f"... 等 {len(violations)} 处" if len(violations) > 3 else ""
            r.fail(
                "prd.html 中出现非豁免 section 的 Mermaid 代码块（违反 proto_contract.md §十一 "
                f"prd.html 中 Mermaid 局部豁免规则）：{shown}{more}"
            )
        if exempted:
            r.ok(
                f"Mermaid 块全部位于豁免 section 内（共 {len(exempted)} 处，"
                f"涉及 {len(set(exempted))} 个 section）"
            )

    # 6. HTML 基本结构
    basic_ok = True
    for tag in ("<html", "</html>", "<body", "</body>"):
        if tag not in html:
            r.fail(f"prd.html 缺少 {tag} 标签")
            basic_ok = False
    if basic_ok:
        r.ok("HTML 基本结构完整（html/body 闭合）")

    # 7. Foundation 占位残留（非阻塞，仅警告）
    foundation_placeholder = html.count("<!-- Foundation Agent 填充 -->")
    if foundation_placeholder > 0:
        r.warn(
            f"产品规格区仍有 {foundation_placeholder} 处 "
            f"<!-- Foundation Agent 填充 --> 占位未填写"
        )

    # 8. <img src="..."> 相对路径存在性（绝对/远程/data URI 跳过）
    img_srcs = re.findall(r'<img[^>]+\bsrc=["\']([^"\']+)["\']', html)
    missing_imgs: list[str] = []
    for src in img_srcs:
        if src.startswith(("http://", "https://", "//", "data:", "#")):
            continue
        if src.startswith("/"):
            target = REPO_ROOT / src.lstrip("/")
        else:
            target = OUTPUT_DIR / src
        if not target.exists():
            missing_imgs.append(src)
    if missing_imgs:
        # 去重，最多展示前 5 条
        unique = sorted(set(missing_imgs))
        r.fail(
            f"prd.html 引用的本地 img/SVG 路径不存在（共 {len(unique)} 个 unique）："
            f"{unique[:5]}{'...' if len(unique) > 5 else ''}"
        )
    elif img_srcs:
        r.ok(f"prd.html 引用的本地 img/SVG 路径全部存在（{len(img_srcs)} 个引用）")


# ── 校验 3｜spec.md ───────────────────────────────────────────────────────────

REQUIRED_FOOTER_SECTIONS = ["## 变更记录", "## 非阻塞性问题清单"]

# proto_spec_md.md §三「页面流转总图」要求 spec 文档主干含以下章节
REQUIRED_SPEC_BACKBONE_SECTIONS: list[tuple[str, re.Pattern]] = [
    # 顶层 §三 页面流转总图（含全量页面清单 + 核心流程 mermaid + 跳转关系总表）
    # 标题允许带「S1.x 」前缀（spec.md S1 章节常用 S1.1/S1.3 编号），保持向后兼容
    # 来源：PM 业务任务期间识别（合并自 Downloads PM 副本，issue 2026-05-07_1400 条 2 排查）
    ("全量页面清单", re.compile(r"^###?\s*(?:S1\.\d+\s+)?全量页面清单", re.MULTILINE)),
    ("跳转关系总表", re.compile(r"^###?\s*(?:S1\.\d+\s+)?跳转关系总表", re.MULTILINE)),
]


def check_spec(data: dict, md: str, r: Report) -> None:
    r.section("spec.md 结构与一致性")

    # 1. 所有模块在 spec 中出现
    missing_mods = [m["id"] for m in data.get("modules", []) if m.get("id") and m["id"] not in md]
    if missing_mods:
        r.fail(f"spec.md 未提及以下模块：{missing_mods}")
    else:
        r.ok(f"全部 {len(data.get('modules', []))} 个模块 id 在 spec.md 中出现")

    # 2. 文档尾部必备章节
    missing_footer = [s for s in REQUIRED_FOOTER_SECTIONS if s not in md]
    if missing_footer:
        r.fail(f"spec.md 缺少尾部章节：{missing_footer}")
    else:
        r.ok("尾部变更记录 + 非阻塞问题清单齐全")

    # 2.5. 主干结构章节（proto_spec_md.md §三 页面流转总图骨架）
    missing_backbone = [name for name, pat in REQUIRED_SPEC_BACKBONE_SECTIONS if not pat.search(md)]
    if missing_backbone:
        r.fail(
            f"spec.md 缺少主干结构章节：{missing_backbone}（"
            f"参 proto_spec_md.md §三「页面流转总图」骨架——Foundation Agent 在 S1 步骤须写入）"
        )
    else:
        r.ok("spec.md 主干结构章节齐全（全量页面清单 + 跳转关系总表）")

    # 3. 内容非空骨架（100 以下视为未拼装，100-2000 提示可疑，2000+ 放行）
    non_comment = re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL).strip()
    length = len(non_comment)
    if length < 100:
        r.fail(f"spec.md 实际内容仅 {length} 字符，疑为未拼装空骨架")
    elif length < 2000:
        r.warn(f"spec.md 实际内容仅 {length} 字符，相对单薄，请确认 Foundation 与各模块内容均已写入")
    else:
        r.ok(f"spec.md 实际内容长度 {length} 字符")

    # 4. spec 中的 H- 锚点应覆盖 scaffold 全部 prd_id（漏写状态拦截）
    spec_h_ids = set(re.findall(r"H-M\d+-P\d+-[\w-]+", md))
    expected_prd_ids = {
        s["prd_id"]
        for mod in data.get("modules", [])
        for p in mod.get("pages", [])
        for s in p.get("states", [])
        if "prd_id" in s
    }
    missing_in_spec = sorted(expected_prd_ids - spec_h_ids)
    if missing_in_spec:
        r.fail(
            f"spec.md 未出现以下 prd_id（scaffold 已声明但 spec 漏写状态枚举）："
            f"{missing_in_spec[:5]}{'...' if len(missing_in_spec) > 5 else ''}"
            f"（共 {len(missing_in_spec)} 个）"
        )
    else:
        r.ok(f"spec.md 已覆盖 scaffold 全部 prd_id（{len(expected_prd_ids)} 个状态）")

    # 5. spec 中 mermaid 检查（与 prd 一致，避免双交付不对称）
    if "```mermaid" in md or re.search(r'class\s*=\s*"[^"]*\bmermaid\b', md):
        r.warn("spec.md 中检测到 Mermaid 代码块——若 proto_contract.md §十一硬禁 spec mermaid 请整改；否则确认无意外格式漂移")
    else:
        r.ok("spec.md 未检测到 Mermaid 代码")

    # 6. spec 中触点 ID 格式合法性（拦截 M01-P01-T1 这种少位数错误）
    # 宽松正则抓所有疑似触点 token；严格格式要求 M\d{2}-P\d{2}-[TDC]\d{2,3}
    loose_tokens = set(re.findall(r"\bM\d+-P\d+-[TDC]\d+\b", md))
    strict_re = re.compile(r"^M\d{2}-P\d{2}-[TDC]\d{2,3}$")
    illegal_tokens = sorted(t for t in loose_tokens if not strict_re.match(t))
    if illegal_tokens:
        r.fail(
            f"spec.md 中以下触点 ID 格式不合法（应为 M[XX]-P[XX]-[T|D][NN]，"
            f"模块/页面 2 位数字 + 触点 2-3 位数字）：{illegal_tokens[:5]}"
        )
    elif loose_tokens:
        r.ok(f"spec.md 触点 ID 格式合法（{len(loose_tokens)} 个）")


# ── 校验 3.4｜spec §3.4 业务流程图 ↔ 阶段 2 §二 SSOT 同步 ─────────────────────


def check_business_flow_in_spec(data: dict, spec_md: str, r: Report) -> None:
    """业务流程图 SSOT 同步性校验

    阶段 2 功能规划 §二 是 spec.md §3.4 业务流程图的 SSOT 主源
    （参 tmpl_功能规划.md §二 头注释 + proto_spec_md.md §3.4）。
    本检查比较两侧 mermaid 块数量：阶段 2 §二 有 N 张图,spec §3.4 应至少有 N 张
    （阶段 4 拼装时按原标题层级 2.1/2.2/2.3 全量迁入）。
    """
    r.section("业务流程图 SSOT 同步性（spec §3.4 ↔ 阶段 2 §二）")

    product = data.get("product", "").strip()
    stage2_path = OUTPUT_DIR / f"功能规划_{product}_latest.md"

    if not stage2_path.exists():
        r.ok(f"阶段 2 功能规划文件不存在（{stage2_path.name}），跳过本项")
        return

    stage2_md = stage2_path.read_text(encoding="utf-8")

    # 阶段 2 §二 范围：从 "## 二、业务流程图" 到下一个 "## " 或文档末尾
    stage2_match = re.search(
        r"^## 二、业务流程图(.*?)(?=^## [^二]|\Z)",
        stage2_md,
        re.MULTILINE | re.DOTALL,
    )
    if not stage2_match:
        r.warn(f"阶段 2 文件存在但未找到 §二 章节,跳过同步性校验")
        return

    stage2_section = stage2_match.group(1)
    stage2_mermaid_count = len(re.findall(r"```mermaid\b", stage2_section))

    if stage2_mermaid_count == 0:
        r.ok("阶段 2 §二 无 mermaid 流程图,spec §3.4 可省略")
        return

    # spec §3.4 范围：从 "### 3.4 业务流程图" 到下一个 "## " 或 "### 3.5" 或文档末尾
    spec_match = re.search(
        r"^### 3\.4 业务流程图(.*?)(?=^## |^### 3\.5|\Z)",
        spec_md,
        re.MULTILINE | re.DOTALL,
    )
    if not spec_match:
        r.fail(
            f"阶段 2 §二 含 {stage2_mermaid_count} 张 mermaid 流程图,"
            f"但 spec.md 缺少 `### 3.4 业务流程图` 章节——"
            f"参 proto_spec_md.md §3.4 + tmpl_功能规划.md §二,"
            f"阶段 4 拼装时须全量迁入（含 2.1/2.2/2.3 全部子节）"
        )
        return

    spec_section = spec_match.group(1)
    spec_mermaid_count = len(re.findall(r"```mermaid\b", spec_section))

    if spec_mermaid_count < stage2_mermaid_count:
        r.fail(
            f"业务流程图迁入不完整：阶段 2 §二 含 {stage2_mermaid_count} 张 mermaid,"
            f"spec §3.4 仅含 {spec_mermaid_count} 张——参 tmpl_功能规划.md §二（SSOT 主源）"
            f"+ proto_spec_md.md §3.4,须按原标题层级（2.1/2.2/2.3）全量迁入"
        )
    else:
        r.ok(
            f"spec §3.4 业务流程图与阶段 2 §二 同步"
            f"（阶段 2: {stage2_mermaid_count} 张, spec §3.4: {spec_mermaid_count} 张）"
        )


def check_business_flow_in_prd(data: dict, prd_html: str, r: Report) -> None:
    """业务流程图 PRD 侧 SSOT 同步性校验（A-04.2 业务流程图）

    阶段 2 功能规划 §二 是 PRD A-04.2 业务流程图的 SSOT 主源
    （参 prd_expression_standard.md §A-04.2 + proto_spec_md.md §3.4）。
    PRD A-04.2 与 spec §3.4 同源（都是阶段 2 §二的派生视图）,
    本检查校验 PRD 含 `<section id="spec-business-flow">` + mermaid 块数 ≥ 阶段 2 §二。
    """
    r.section("业务流程图 SSOT 同步性（PRD A-04.2 ↔ 阶段 2 §二）")

    product = data.get("product", "").strip()
    stage2_path = OUTPUT_DIR / f"功能规划_{product}_latest.md"

    if not stage2_path.exists():
        r.ok(f"阶段 2 功能规划文件不存在（{stage2_path.name}），跳过本项")
        return

    stage2_md = stage2_path.read_text(encoding="utf-8")
    stage2_match = re.search(
        r"^## 二、业务流程图(.*?)(?=^## [^二]|\Z)",
        stage2_md,
        re.MULTILINE | re.DOTALL,
    )
    if not stage2_match:
        r.warn("阶段 2 文件存在但未找到 §二 章节,跳过本校验")
        return
    stage2_mermaid_count = len(re.findall(r"```mermaid\b", stage2_match.group(1)))

    if stage2_mermaid_count == 0:
        r.ok("阶段 2 §二 无 mermaid 流程图,PRD A-04.2 可省略")
        return

    # PRD spec-business-flow section 范围
    prd_match = re.search(
        r'<section\s+id\s*=\s*"spec-business-flow"[^>]*>(.*?)</section>',
        prd_html,
        re.DOTALL | re.IGNORECASE,
    )
    if not prd_match:
        r.fail(
            f"阶段 2 §二 含 {stage2_mermaid_count} 张 mermaid 流程图,"
            f'但 PRD 缺少 `<section id="spec-business-flow">` —— '
            f"按 prd_expression_standard.md §A-04.2 由 Foundation Agent 写入,"
            f"工程视角章节,与 A-04 用户旅程互补不可省略"
        )
        return

    prd_section = prd_match.group(1)
    # PRD 的 mermaid 写在 <pre class="mermaid"> 内,不用 ```mermaid 包裹
    prd_mermaid_count = len(re.findall(r'<pre[^>]*class\s*=\s*"[^"]*\bmermaid\b[^"]*"', prd_section, re.IGNORECASE))

    if prd_mermaid_count < stage2_mermaid_count:
        r.fail(
            f"业务流程图 PRD 侧迁入不完整：阶段 2 §二 含 {stage2_mermaid_count} 张 mermaid,"
            f'PRD A-04.2 (`spec-business-flow`) 仅含 {prd_mermaid_count} 张 `<pre class="mermaid">` 块——'
            f"参 prd_expression_standard.md §A-04.2,须三类子 spec-block "
            f"(主流程总览 / 跨角色交互 / 补充流程) 全量迁入"
        )
    else:
        r.ok(
            f"PRD A-04.2 业务流程图与阶段 2 §二 同步"
            f"（阶段 2: {stage2_mermaid_count} 张, PRD: {prd_mermaid_count} 张）"
        )


def check_page_hierarchy_sitemap(
    data: dict, spec_md: str, prd_html: str, r: Report
) -> None:
    """S4-29：页面层级架构（§3.0 / PRD spec-sitemap）SSOT 同步性校验

    真源 = scaffold.json modules[].pages[]（SSOT 双锚 #38）。assemble.py
    `build_hierarchy_mermaid` 从 scaffold 现场派生「产品根→模块→页面」两层
    mermaid，注入 spec.md §3.0 + PRD `spec-sitemap` section（提议1）。本检查
    校验两侧均存在，且 mermaid 中页面节点（ID 固定 `M\\d+_P\\d+` 形态，由
    build_hierarchy_mermaid 保证 → 可靠计数，不受标签内容干扰）distinct 数
    == scaffold 全量 pages 数。缺失 = 漏注入 / Foundation 漏写 marker；
    数不对称 = 派生漂移（改 scaffold 后未重跑 assemble）。
    """
    r.section("页面层级架构 SSOT 同步性（§3.0 / PRD spec-sitemap ↔ scaffold，S4-29）")

    modules = data.get("modules", []) or []
    expected_pages = sum(len(m.get("pages", []) or []) for m in modules)
    if expected_pages == 0:
        r.warn("scaffold 无页面，跳过页面层级架构校验")
        return

    page_node_re = re.compile(r"\bM\d+_P\d+\b")

    # ── spec.md §3.0 ──
    spec_m = re.search(
        r"^###\s*3\.0\s*页面层级架构(.*?)(?=^#{2,3}\s|\Z)",
        spec_md, re.MULTILINE | re.DOTALL,
    )
    if not spec_m:
        r.fail(
            "spec.md 缺少 `### 3.0 页面层级架构` 章节——应由 assemble.py 从 "
            "scaffold 现场派生注入（SSOT #38）；常见原因：Foundation 漏在区块1 "
            "顶写 `<!-- [SITEMAP-3.0] -->` marker（参 proto_spec_md.md §3.0 / "
            "agent_dispatch_protocol.md Step2），或未重跑 assemble.py spec"
        )
    else:
        spec_pages = len(set(page_node_re.findall(spec_m.group(1))))
        if spec_pages != expected_pages:
            r.fail(
                f"spec §3.0 页面层级图页面节点数不对称：scaffold {expected_pages} "
                f"页，§3.0 mermaid 含 {spec_pages} 个页面节点（M\\d+_P\\d+）——"
                f"派生漂移，改 scaffold 后须重跑 assemble.py spec 刷新"
            )
        else:
            r.ok(f"spec §3.0 页面层级架构与 scaffold 同步（{expected_pages} 页）")

    # ── PRD spec-sitemap ──
    prd_m = re.search(
        r'<section\s+id\s*=\s*"spec-sitemap"[^>]*>(.*?)</section>',
        prd_html, re.DOTALL | re.IGNORECASE,
    )
    if not prd_m:
        r.fail(
            'prd.html 缺少 `<section id="spec-sitemap">`「页面架构总览」——'
            "gen_scaffold.DERIVED_SPEC_ITEMS 出空壳 + assemble.py 现场派生注入"
            "（SSOT #38）；常见原因：骨架由旧版 gen_scaffold 生成"
        )
        return
    prd_section = prd_m.group(1)
    if not re.search(
        r'<pre[^>]*class\s*=\s*"[^"]*\bmermaid\b[^"]*"', prd_section, re.IGNORECASE
    ):
        r.fail(
            'PRD spec-sitemap section 内缺少 `<pre class="mermaid">` 层级图——'
            "assemble.inject_prd_sitemap 未注入；常见原因：gen_scaffold 空壳缺 "
            "`<!-- [SITEMAP-PRD] -->` 占位，或未重跑 assemble.py prd"
        )
        return
    prd_pages = len(set(page_node_re.findall(prd_section)))
    if prd_pages != expected_pages:
        r.fail(
            f"PRD spec-sitemap 页面节点数不对称：scaffold {expected_pages} 页，"
            f"sitemap mermaid 含 {prd_pages} 个页面节点——派生漂移，"
            f"改 scaffold 后须重跑 assemble.py prd 刷新"
        )
    else:
        r.ok(f"PRD spec-sitemap 页面架构与 scaffold 同步（{expected_pages} 页）")


# ── S4-32 页面骨架屏（SSOT 双锚 #41，WE-H per-archetype）──────────────────────
# WE-H（2026-05-19，#41 颗粒度重设 per-page→per-archetype + 条件 per-page
# override）：#41 = #39 的视觉化身。单源 = Foundation 草稿 spec_foundation_draft.md
# 「## 范式骨架」段每 archetype 一 ```skeleton → assemble 派生 spec.md §3.0
# 「#### 范式骨架」子节（本 check 据此校验「每 archetype 有良构骨架」，取代旧
# 「每页有骨架」）+ per-page override（S2.M[XX].1 override-only：默认页复用范式
# 骨架、无围栏 → 不校验不 WARN，无"每页必填"压力/无 SNB-006 redux）。
# SKELETON_DISCLAIMER 真源 = proto_spec_md.md §四「页面结构（骨架屏）」首行免责
# 注释；本常量 / gen_scaffold.SKELETON_DISCLAIMER / prd_expression_standard §A-09
# 须与之字面一致（调整方向：先改 proto_spec_md.md §四，再同步三处，禁反向）。
SKELETON_DISCLAIMER = (
    "<!-- 平面布局示意，非组件层级/非实现 DOM 依据；容纳权威归 page_archetypes(#39) -->"
)
# per-page override 锚（S2.M[XX].1 内 `- **P[XX] 页面名**`，与 assemble
# extract_spec_skeletons / gen_scaffold 同型；override-only）
_SK_ANCHOR_RE = re.compile(r"^[ \t]*-[ \t]*\*\*(P\d+)[ \t]+(.+?)\*\*", re.MULTILINE)
# WE-H：§3.0「范式骨架」子节内每范式锚 `**名称**（`<aid>`）`（assemble
# build_archetype_skeleton_md 派生对侧；aid 白名单交叉校验杜绝误抓）
_SK_ARCH_ANCHOR_RE = re.compile(r"\*\*(.+?)\*\*（`([\w-]+)`）")
# WE-G 条件 per-platform：可选 :platform 标签（围栏 info-string）
_SK_FENCE_RE = re.compile(r"```skeleton(?::(\w+))?[ \t]*\n(.*?)\n```", re.DOTALL)
_SK_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_SK_TAG_RE = re.compile(r"<\s*/?\s*([a-zA-Z][\w-]*)")
_SK_ALLOWED_CLASSES = {"sk-page", "sk-row", "sk-col", "sk-region"}
# WE-G：合法 per-platform frame token（对齐帧 class 根；scaffold.platforms↔frame
# 反向映射故意不在此交叉校验——keys 是中文端名、映射有 FP 风险，known-token
# 校验是高值低 FP 部分；1-vs-N/发散与否属 PM 判断层，不机械强制，详 §四 + S4-32）
_SK_PLATFORM_TOKENS = {"phone", "desktop", "tablet", "h5", "mp"}


def _validate_skeleton_blocks(
    blocks: list, allowed: set, ctx: str, r: "Report"
) -> bool:
    """逐块校验一组 ```skeleton(:plat)? 块（②~④ + 平台 token + 嵌套）。
    archetype 范式骨架 与 per-page override 共用（同一白名单/字面/容纳纪律）。
    WE-G：1-vs-N/发散与否是 PM/Foundation 判断层、**不机械强制**（同 #39 B 组、
    dry-run FP 纪律），本处仅逐块校形 + 平台 token 合法。全块通过 → True。
    全部结构项 r.warn（WARN-phase 档 C，迁移完升 FAIL，详 S4-32 状态块）。"""
    ok = True
    for plat, inner in blocks:
        btag = ctx if plat is None else f"{ctx}:{plat}"
        if plat is not None and plat not in _SK_PLATFORM_TOKENS:
            r.warn(
                f"[{btag}] ```skeleton:{plat} 平台 token 非法"
                f"（合法 {sorted(_SK_PLATFORM_TOKENS)}；WARN 档 C）"
            )
            ok = False
            continue
        lines = [ln for ln in inner.splitlines() if ln.strip()]
        if not lines or lines[0].strip() != SKELETON_DISCLAIMER:
            r.warn(
                f"[{btag}] ```skeleton 首行非固定免责注释（S4-32 字面校验）；"
                f"应为：{SKELETON_DISCLAIMER}"
            )
            ok = False
            continue
        body = _SK_COMMENT_RE.sub("", inner)
        bad_tags = sorted({
            t.lower() for t in _SK_TAG_RE.findall(body) if t.lower() != "div"
        })
        if bad_tags:
            r.warn(
                f"[{btag}] ```skeleton 含非白名单标签 {bad_tags}"
                f"（仅允许 <div>；详 proto_spec_md.md §四白名单）"
            )
            ok = False
            continue
        if re.search(r"\bstyle\s*=", body):
            r.warn(f"[{btag}] ```skeleton 含 inline style=（白名单禁止；data-w/data-h 由模板落地）")
            ok = False
            continue
        cls_bad = sorted({
            c for c in re.findall(r'class\s*=\s*"([^"]*)"', body)
            if c not in _SK_ALLOWED_CLASSES
        })
        if cls_bad:
            r.warn(
                f"[{btag}] ```skeleton class 越白名单 {cls_bad}"
                f"（仅 {sorted(_SK_ALLOWED_CLASSES)}）"
            )
            ok = False
            continue
        data_r = re.findall(r'data-r\s*=\s*"([^"]*)"', body)
        bad_r = sorted({v for v in data_r if v not in allowed})
        if bad_r:
            r.warn(
                f"[{btag}] ```skeleton data-r {bad_r} 不在该 archetype "
                f"regions slot/extension {sorted(allowed)}"
                f"（#39 容纳权威；空值=未填占位）"
            )
            ok = False
            continue
        depth = mx = 0
        for tok in re.findall(r"<\s*(/?)\s*div", body):
            depth += -1 if tok else 1
            mx = max(mx, depth)
        if mx > 3:
            r.warn(f"[{btag}] ```skeleton div 嵌套深度 {mx} > 3（§四建议 ≤ 3，请自审）")
    return ok


def check_page_skeleton(
    data: dict, spec_md: str, prd_html: str, r: Report
) -> None:
    """S4-32：页面骨架屏（SSOT #41，WE-H per-archetype）结构兜底。

    **WE-H（2026-05-19，#41 颗粒度重设 per-page→per-archetype + 条件 per-page
    override）**：#41 = #39 的视觉化身。本 check 三块（全 WARN-phase 档 C）：

      ① **per-archetype 范式骨架**（spec.md §3.0「#### 范式骨架」子节，assemble
         build_archetype_skeleton_md 派生）：**每个 scaffold archetype 有 ≥1
         良构 ```skeleton 块**（取代旧「每页有骨架」）+ 块②~④（免责首行字面 /
         仅 sk-* div 白名单 / data-r ⊆ **该 archetype** regions∪extension）+
         :plat token 合法 + 嵌套。缺范式骨架 / 不良构 → WARN（迁移完升 FAIL）。
      ② **per-page override**（S2.M[XX].1，override-only）：默认页复用范式骨架
         （无 ```skeleton 围栏 → 不校验、不 WARN，无"每页必填"压力/无 SNB-006
         redux）；仅 override 页有围栏 → 同②~④校验 + data-r ⊆ **本页 archetype**。
      ③ **PRD 侧**：spec-sitemap 含 `<div id="sk-askel">` + 每范式子锚
         `sk-askel-<aid>`（非 override 页帧旁 chip showSection 深链对侧，不死链）。

    WE-G 条件 per-platform 在 archetype/override 级均适用（_validate_skeleton_
    blocks 复用）；1-vs-N/发散与否是 Foundation/PM 判断层、**不机械强制**
    （同 #39 B 组、dry-run FP 纪律）。

    **WARN-phase（档 C，2026-05-18 产品总监裁决，对齐 S4-25/S4-28 先例）**：
    新结构规则即便 exact 判定，凡追溯性作用于存量产物者必先 WARN-phase
    （S4-32 Why / SNB-006 教训）。**下游全 archetype 范式骨架良构 + override
    良构后升 r.fail**（rule_hard_constraints S4-32 状态块 + WE-D readiness
    gate 重基线——逆向当前 WE-H 后代码，非 WE-D2/WE-G 旧基线）。

    无 page_archetypes（agnostic / 向后兼容）→ WARN 跳过 per-archetype（同
    build_archetype_skeleton_* 优雅降级）。Foundation 未写 [SITEMAP-3.0]
    marker / 未重跑 assemble → §3.0 无「#### 范式骨架」子节 → WARN 跳过
    （文件/阶段存在性守恒，不阻断框架仓 dry-run）。
    """
    r.section("页面骨架屏 结构兜底（S4-32 / SSOT #41 per-archetype；WARN-phase 档 C）")

    archs = {a.get("id"): a for a in (data.get("page_archetypes") or []) if isinstance(a, dict)}
    if not archs:
        r.warn(
            "scaffold 无 page_archetypes（agnostic / 向后兼容场景）—— "
            "S4-32 per-archetype 范式骨架校验跳过（assemble 同步优雅降级）"
        )
        return

    def _allowed_slots(arch_id: str) -> set[str]:
        a = archs.get(arch_id) or {}
        slots = {r0.get("slot") for r0 in (a.get("regions") or []) if r0.get("slot")}
        slots |= {e for e in (a.get("extension") or []) if e}
        return slots

    # ── ① per-archetype 范式骨架（spec.md §3.0「#### 范式骨架」子节）──────────
    skel_sec = re.search(
        r"####[ \t]*范式骨架\b.*?"
        r"(?=\n####[ \t]|\n###[ \t]|\n##[ \t]|<!--[ \t]*\[SITEMAP-3\.0-END\]|\Z)",
        spec_md, re.DOTALL,
    )
    if not skel_sec:
        r.warn(
            "spec.md §3.0 无『#### 范式骨架』子节——未重跑 assemble.py spec / "
            "Foundation 未写 [SITEMAP-3.0] marker / spec_foundation_draft.md 缺失；"
            "per-archetype 校验跳过（WARN 档 C，不阻断框架仓 dry-run）"
        )
    else:
        scope = skel_sec.group(0)
        ach_anchors = list(_SK_ARCH_ANCHOR_RE.finditer(scope))
        arch_blocks: dict[str, list[tuple[str | None, str]]] = {}
        for i, m in enumerate(ach_anchors):
            aid = m.group(2)
            if aid not in archs:
                continue  # 非 scaffold 范式 id 的 bold（白名单纪律，杜绝误抓）
            seg = scope[m.end(): ach_anchors[i + 1].start() if i + 1 < len(ach_anchors) else len(scope)]
            blocks = [(f.group(1), f.group(2)) for f in _SK_FENCE_RE.finditer(seg)]
            if blocks:
                arch_blocks[aid] = blocks
        n_arch_ok = 0
        for aid in archs:
            blocks = arch_blocks.get(aid)
            if not blocks:
                r.warn(
                    f"[范式 {aid}] §3.0「范式骨架」缺该 archetype ```skeleton 块"
                    f"（Foundation 子阶段二未填 / 存量待迁移；SSOT #41 [Must] 每"
                    f" archetype 一骨架；WARN 档 C，迁移完升 FAIL）"
                )
                continue
            if _validate_skeleton_blocks(blocks, _allowed_slots(aid), f"范式 {aid}", r):
                n_arch_ok += 1
        if n_arch_ok == len(archs):
            r.ok(
                f"全部 {len(archs)} 个 archetype 范式骨架良构 + data-r ⊆ 该范式 "
                f"regions∪extension（SSOT #41 per-archetype）"
            )

    # ── ② per-page override（S2.M[XX].1，override-only；默认页无 → 不校验不 WARN）──
    if "## S2." in spec_md:
        n_override = n_override_ok = 0
        for mod in data.get("modules", []) or []:
            mid = mod.get("id", "M??")
            sec = re.search(
                rf"##[ \t]*S2\.{re.escape(mid)}\.1[ \t].*?(?=\n##[ \t]|\Z)",
                spec_md, re.DOTALL,
            )
            scope = sec.group(0) if sec else ""
            anchors = list(_SK_ANCHOR_RE.finditer(scope))
            page_arch = {p.get("id", "P??"): p.get("archetype", "") for p in (mod.get("pages") or [])}
            for i, m in enumerate(anchors):
                pid = m.group(1)
                seg = scope[m.end(): anchors[i + 1].start() if i + 1 < len(anchors) else len(scope)]
                blocks = [(f.group(1), f.group(2)) for f in _SK_FENCE_RE.finditer(seg)]
                if not blocks:
                    continue  # override-only：默认页无围栏 = 复用范式 = 正常
                n_override += 1
                if _validate_skeleton_blocks(
                    blocks, _allowed_slots(page_arch.get(pid, "")),
                    f"{mid}-{pid} override", r,
                ):
                    n_override_ok += 1
        if n_override:
            if n_override_ok == n_override:
                r.ok(
                    f"{n_override} 个 per-page override 骨架良构（覆盖范式，"
                    f"data-r ⊆ 本页 archetype；SSOT #41 条件 override）"
                )
        else:
            r.ok("无 per-page override（默认全页复用范式骨架，符合 WE-H 预期）")

    # ── ③ PRD 侧子检查：spec-sitemap 含 sk-askel 范式骨架画廊 + 每范式子锚 ──
    # （WE-H：非 override 页帧旁 chip `showSection('sk-askel-<aid>')` 深链对侧，
    # sk-* div 锚 WE-F R1 已让 check_prd 解析合法；WARN 档 C，不阻断）
    if 'id="sk-askel"' not in prd_html:
        r.warn(
            "PRD spec-sitemap 缺 <div id=\"sk-askel\"> 范式骨架画廊"
            "（未重跑 assemble.py prd / 模板缺 [SITEMAP-PRD] 占位）；WARN 档 C"
        )
    else:
        missing = sorted(aid for aid in archs if f'id="sk-askel-{aid}"' not in prd_html)
        if missing:
            r.warn(
                f"PRD sk-askel 缺范式子锚 {missing}（非 override 页帧旁 chip "
                f"showSection 深链将无目标——assemble 优雅占位时正常，"
                f"迁移完应齐全；WARN 档 C）"
            )
        else:
            r.ok(
                f"PRD 范式骨架画廊 sk-askel + {len(archs)} 个范式子锚齐全"
                f"（chip 深链不死链，SSOT #41 / WE-H）"
            )


def check_page_archetype_contract(
    data: dict, spec_md: str, prd_html: str, r: Report
) -> None:
    """S4-30：页面结构范式契约（提议2，SSOT #39）结构层兜底

    真源 = scaffold.json page_archetypes + pages[].archetype。
    gen_scaffold.validate_v2_schema 是 Step1.5 首次闸，但 post-Foundation 不再
    重跑 gen_scaffold（H1=(c) 现场消费），故本 check 在 Step6.5 恒跑承接结构
    兜底：① page_archetypes 顶层非空 + 每条 id/name/regions ② 每页 archetype
    必填且引用合法（悬空 FAIL）③ spec §3.0 + PRD spec-sitemap 含 assemble
    现场派生的「页面结构范式契约」表（注入存在性）。
    """
    r.section("页面结构范式契约 结构兜底（提议2，S4-30 / SSOT #39）")
    archs = data.get("page_archetypes")
    if not isinstance(archs, list) or not archs:
        r.fail(
            "scaffold 缺 page_archetypes 顶层非空数组（提议2 必填——页面结构范式"
            "定义本体；详见 agent_dispatch_protocol.md §scaffold v2.0 schema + "
            "proto_spec_md.md「页面结构范式契约」段）"
        )
        return
    ids: set[str] = set()
    for i, a in enumerate(archs):
        if not isinstance(a, dict):
            r.fail(f"page_archetypes[{i}] 必须是对象")
            continue
        aid = a.get("id")
        if not aid:
            r.fail(f"page_archetypes[{i}] 缺 id")
        else:
            ids.add(aid)
        if not a.get("name"):
            r.fail(f"page_archetypes[{aid or i}] 缺 name")
        if not isinstance(a.get("regions"), list) or not a.get("regions"):
            r.fail(f"page_archetypes[{aid or i}] regions 必须非空数组")

    missing, dangling = [], []
    for mod in data.get("modules", []) or []:
        mid = mod.get("id", "?")
        for p in mod.get("pages", []) or []:
            pid = p.get("id", "?")
            pa = p.get("archetype")
            if not pa:
                missing.append(f"{mid}-{pid}")
            elif pa not in ids:
                dangling.append(f"{mid}-{pid}→{pa}")
    if missing:
        shown = ", ".join(missing[:10]) + ("..." if len(missing) > 10 else "")
        r.fail(f"以下页面缺 archetype 字段：{shown}")
    if dangling:
        shown = ", ".join(dangling[:10]) + ("..." if len(dangling) > 10 else "")
        r.fail(f"以下页面 archetype 悬空（不在 page_archetypes ids {sorted(ids)}）：{shown}")
    if not missing and not dangling:
        r.ok(f"全部页面 archetype 引用合法（{len(ids)} 个范式）")

    if "页面结构范式契约" not in spec_md:
        r.fail(
            "spec §3.0 缺「页面结构范式契约」派生表——"
            "assemble.build_archetype_contract_md 未注入；常见原因：未重跑 "
            "assemble.py spec（改 scaffold 后须重跑刷新）"
        )
    else:
        r.ok("spec §3.0 含页面结构范式契约表")
    prd_m = re.search(
        r'<section\s+id\s*=\s*"spec-sitemap"[^>]*>(.*?)</section>',
        prd_html, re.DOTALL | re.IGNORECASE,
    )
    if not prd_m or "页面结构范式契约" not in prd_m.group(1):
        r.fail(
            'PRD spec-sitemap 缺「页面结构范式契约」派生表——'
            "assemble.build_archetype_contract_html 未注入；常见原因：未重跑 "
            "assemble.py prd"
        )
    else:
        r.ok("PRD spec-sitemap 含页面结构范式契约表")


def check_archetype_containment_record(data: dict, r: Report) -> None:
    """S4-30（过程层）：页面结构容纳性二值校验记录齐全+覆盖（提议2，SSOT #39）

    A+C 债处理之「C」——把"二值校验做没做"从 B 组拉回 A 组机械兜底（同
    SSOT #35 手法：校验记录*存在+覆盖*，不校验每条判断*对不对*——后者是
    B 组判断层，靠 Step1.X + 终审 + subagent 二值闸三道非脚本门）。

    Step3/5 模块 subagent 填/绘每页前须做容纳性二值校验并写定长记录入模块
    子进度文件 `## 页面结构容纳性校验记录` 段。无模块子进度文件（尚未进
    Step3 / 框架仓 dry-run）→ WARN 跳过（与其它 check 文件存在性守恒一致）。
    """
    r.section("页面结构容纳性校验记录 过程兜底（提议2，S4-30 过程层 / SSOT #39）")
    product = data.get("product", "").strip()
    prog_dir = REPO_ROOT / "process_record" / "progress"
    any_found = False
    for mod in data.get("modules", []) or []:
        mid = mod.get("id", "?")
        sub = prog_dir / f"stage4_{product}_{mid}_plan.md"
        if not sub.exists():
            continue
        any_found = True
        text = sub.read_text(encoding="utf-8")
        m = re.search(
            r"##\s*页面结构容纳性校验记录(.*?)(?=^##\s|\Z)",
            text, re.MULTILINE | re.DOTALL,
        )
        if not m:
            r.fail(
                f"[{mid}] 子进度文件缺 `## 页面结构容纳性校验记录` 段"
                f"（Step3/5 subagent 未写——提议2 [Must]，参 proto_spec_md.md）"
            )
            continue
        seg = m.group(1)
        page_ids = [p.get("id", "?") for p in mod.get("pages", []) or []]
        miss = [
            pid for pid in page_ids
            if not re.search(rf"\b{re.escape(mid)}-{re.escape(pid)}\b", seg)
        ]
        if miss:
            r.fail(f"[{mid}] 容纳性校验记录未覆盖页面：{miss}")
        for pid in page_ids:
            row = re.search(
                rf"^.*\b{re.escape(mid)}-{re.escape(pid)}\b.*$", seg, re.MULTILINE
            )
            if row and "PASS" not in row.group(0) and "FAIL" not in row.group(0):
                r.fail(f"[{mid}-{pid}] 容纳性记录行结论列非 PASS/FAIL")
        if not miss:
            r.ok(f"[{mid}] 容纳性校验记录齐全（{len(page_ids)} 页）")
    if not any_found:
        r.warn(
            "无模块子进度文件（尚未进 Step3/5 或框架仓 dry-run）——容纳性记录"
            "校验跳过；真实运行须由 Step3/5 subagent 按 proto_spec_md.md 定长格式写入"
        )


def check_module_architecture(
    data: dict, spec_md: str, prd_html: str, r: Report
) -> None:
    """S4-31：模块架构说明（提议3，SSOT #40）结构兜底

    真源 = scaffold.json modules[]{name, 可选 purpose, depends_on}。assemble.py
    `build_module_arch_*` 从 scaffold 现场派生「模块架构说明」(模块表 + 模块
    依赖 graph TB，2026-05-18 commit 3dd28b8 改自 LR)，与 §3.0 页面层级图
    （graph LR + subgraph 分组，2026-05-25 WE-LRTB 改自 TD）/ 提议2 契约
    colocate 注入 §3.0 / spec-sitemap。post-Foundation 不重跑 gen_scaffold（H1=(c)），本 check
    Step6.5 恒跑承接结构兜底：spec §3.0 + PRD spec-sitemap 含「模块架构说明」
    + 模块表行数 == scaffold.modules 数 + 依赖边数 == 全 depends_on 条目数。
    全数对称、无判断层 → SSOT #40 干净 A 组。
    """
    r.section("模块架构说明 结构兜底（提议3，S4-31 / SSOT #40）")
    modules = data.get("modules", []) or []
    if not modules:
        r.warn("scaffold 无 modules，跳过模块架构校验")
        return
    exp_mods = len(modules)
    exp_edges = sum(len(m.get("depends_on", []) or []) for m in modules)

    # spec §3.0 区块内「模块架构说明」（assemble 注入顺序：层级图→契约→模块架构，
    # 故 "模块架构说明" 之后到 SITEMAP-3.0-END / 下一 ### 即本块范围）
    if "模块架构说明" not in spec_md:
        r.fail(
            "spec §3.0 缺「模块架构说明」派生块——assemble.build_module_arch_md "
            "未注入；常见原因：未重跑 assemble.py spec（改 scaffold 后须重跑）"
        )
    else:
        seg = spec_md.split("模块架构说明", 1)[1]
        seg = re.split(r"<!--\s*\[SITEMAP-3\.0-END\]|\n#{3}\s", seg, 1)[0]
        rows = len(re.findall(r"^\|\s*`M\d", seg, re.MULTILINE))
        edges = len(re.findall(r"-->\|", seg))
        if rows != exp_mods:
            r.fail(
                f"spec §3.0 模块架构表行数 {rows} ≠ scaffold.modules {exp_mods}"
                f"（派生漂移，改 scaffold 后须重跑 assemble.py spec）"
            )
        elif edges != exp_edges:
            r.fail(
                f"spec §3.0 模块依赖边数 {edges} ≠ scaffold depends_on 总数 "
                f"{exp_edges}（派生漂移，重跑 assemble.py spec）"
            )
        else:
            r.ok(
                f"spec §3.0 模块架构与 scaffold 同步"
                f"（{exp_mods} 模块 / {exp_edges} 依赖边）"
            )

    prd_m = re.search(
        r'<section\s+id\s*=\s*"spec-sitemap"[^>]*>(.*?)</section>',
        prd_html, re.DOTALL | re.IGNORECASE,
    )
    if not prd_m or "模块架构说明" not in prd_m.group(1):
        r.fail(
            'PRD spec-sitemap 缺「模块架构说明」派生块——'
            "assemble.build_module_arch_html 未注入；常见原因：未重跑 assemble.py prd"
        )
        return
    prd_seg = prd_m.group(1)
    prd_rows = len(re.findall(r"<tr><td><code>M\d", prd_seg))
    prd_edges = len(re.findall(r"-->\|", prd_seg))
    if prd_rows != exp_mods:
        r.fail(
            f"PRD spec-sitemap 模块架构表行数 {prd_rows} ≠ scaffold.modules "
            f"{exp_mods}（重跑 assemble.py prd）"
        )
    elif prd_edges != exp_edges:
        r.fail(
            f"PRD spec-sitemap 模块依赖边数 {prd_edges} ≠ depends_on 总数 "
            f"{exp_edges}（重跑 assemble.py prd）"
        )
    else:
        r.ok(
            f"PRD spec-sitemap 模块架构与 scaffold 同步"
            f"（{exp_mods} 模块 / {exp_edges} 依赖边）"
        )


# ── 校验 3.5｜spec ↔ prd 触点 ID 集合一致性 ──────────────────────────────────

TOUCHPOINT_RE = re.compile(r"\b(M\d{2}-P\d{2}-[TDC]\d{2,3})\b")


def check_touchpoint_consistency(spec_md: str, prd_html: str, r: Report) -> None:
    """spec.md 与 prd.html 的触点 ID 集合应完全一致。"""
    r.section("触点 ID 集合一致性（spec ↔ prd）")

    spec_ids = set(TOUCHPOINT_RE.findall(spec_md))
    prd_ids = set(TOUCHPOINT_RE.findall(prd_html))

    only_in_spec = sorted(spec_ids - prd_ids)
    only_in_prd = sorted(prd_ids - spec_ids)

    if not spec_ids and not prd_ids:
        r.warn("spec.md 与 prd.html 均未检测到触点 ID（M[XX]-P[XX]-[T|D][NN]）；若产品确无交互触点请忽略，否则请检查触点编号")
        return

    if only_in_spec:
        r.fail(f"以下触点仅出现在 spec.md，prd.html 缺失：{only_in_spec[:10]}{'...' if len(only_in_spec) > 10 else ''}（共 {len(only_in_spec)} 个）")
    if only_in_prd:
        r.fail(f"以下触点仅出现在 prd.html，spec.md 缺失：{only_in_prd[:10]}{'...' if len(only_in_prd) > 10 else ''}（共 {len(only_in_prd)} 个）")
    if not only_in_spec and not only_in_prd:
        r.ok(f"触点 ID 集合在 spec.md 与 prd.html 完全一致（{len(spec_ids)} 个）")


# ── 校验 3.5a｜S4-34 触点 canonical 引用完整性 ────────────────────────────────

# 来源：下游 /retro 共性根因 D — 触点 ID 手写偏差（D4/D5 类：补少位 / 拼写 / 跨页串号）。
#   治本：触点编号从 scaffold.pages[].touchpoints[] canonical 清单生成（gen_scaffold 预填
#   spec 触点表行），precheck 校验 spec/prd 中任何 M[XX]-P[YY]-[TDC][NN] 引用必 ⊆ canonical。
#   比"补少位正则"更根本——杜绝一切手写偏差（不在 canonical 集合即 WARN）。
# SSOT 真源：rule_hard_constraints.md S4-34 + ssot_anchors.md #44
# 向后兼容：scaffold 无 touchpoints[] 声明（旧两段式产物）→ 跳过（WARN 阶段不阻断迁移）。


def _build_touchpoint_canonical(data: dict) -> set[str]:
    """从 scaffold.pages[].touchpoints[] 构建 canonical 全量触点 ID 集合。

    canonical 全 ID = f"{mid}-{pid}-{tp.id}"（如 M01-P01-T01）；无 touchpoints 声明返回空集。
    """
    canonical: set[str] = set()
    for mod in data.get("modules", []):
        mid = mod.get("id", "")
        for p in mod.get("pages", []) or []:
            pid = p.get("id", "")
            for tp in p.get("touchpoints", []) or []:
                tid = tp.get("id")
                if mid and pid and tid:
                    canonical.add(f"{mid}-{pid}-{tid}")
    return canonical


def check_touchpoint_canonical(
    data: dict, spec_md: str, prd_html: str, r: Report
) -> None:
    """S4-34（WARN 阶段）：spec/prd 中所有触点引用必 ⊆ scaffold canonical 集合。

    治本 D4/D5 类手写偏差：触点 ID 从 scaffold.pages[].touchpoints[] canonical 生成，
    任何 spec/prd 中的 M[XX]-P[YY]-[TDC][NN] 引用不在 canonical 内 → WARN（PM 手写 /
    拼写错 / 跨页串号）。向后兼容：scaffold 无 touchpoints[] → 跳过（不阻断旧产物迁移）。
    """
    r.section("S4-34 触点 canonical 引用完整性（WARN 阶段）")
    canonical = _build_touchpoint_canonical(data)
    if not canonical:
        r.ok(
            "scaffold 未声明 pages[].touchpoints[] canonical（旧两段式产物，跳过）；"
            "治本路径：在 scaffold 预声明触点 canonical → gen_scaffold 预填 spec 触点表（SSOT #44）"
        )
        return

    refs = set(TOUCHPOINT_RE.findall(spec_md)) | set(TOUCHPOINT_RE.findall(prd_html))
    outside = sorted(refs - canonical)
    unreferenced = sorted(canonical - refs)

    if outside:
        r.warn(
            f"S4-34: {len(outside)} 个触点引用不在 scaffold canonical 集合内"
            f"（PM 手写偏差 / 拼写错 / 跨页串号）：{outside[:10]}{'...' if len(outside) > 10 else ''}；"
            f"canonical 共 {len(canonical)} 个——增删触点须回 scaffold.touchpoints[] 重跑 gen_scaffold，"
            f"禁止 spec/prd 手写 ID。WARN 阶段，3 仓 dry-run + FP<30% 后升 FAIL"
        )
    if unreferenced:
        r.warn(
            f"S4-34: {len(unreferenced)} 个 canonical 触点在 spec/prd 中未被引用"
            f"（scaffold 声明了但页面未用）：{unreferenced[:10]}{'...' if len(unreferenced) > 10 else ''}；"
            f"核对是否漏渲染或 scaffold 多声明"
        )
    if not outside and not unreferenced:
        r.ok(f"全部触点引用 ⊆ scaffold canonical 且无未引用项（canonical {len(canonical)} 个）")


# ── 校验 3.5b｜S4-33 mermaid 语法校验（mmdc 实际 parse）─────────────────────────

# 来源：下游 /retro 共性根因 B — mermaid 语法错（括号未引号 / edge label / 时序图等）
#   反复在 #23/#26/#34/#35 类问题出现。机械门禁：每个 mermaid 块经 mmdc 实际 parse，
#   语法错则 WARN（dry-run 纪律：新追溯型 check 先 WARN，3 仓 dry-run + FP<30% 后升 FAIL）。
# SSOT 真源：rule_hard_constraints.md S4-33 + ssot_anchors.md #43
# 设计要点：
#   - 多块拼一个临时 markdown 文件，mmdc 单次渲染（chrome 仅启一次，~1-2s/十余块），避免逐块 launch
#   - mmdc 缺失（未 npm install -g）→ WARN 跳过（提示安装），不阻断；下游无 mmdc 时静默降级
#   - puppeteer 需 --no-sandbox（Ubuntu 23.10+ unprivileged userns 限制），由临时 config 注入
#   - prd <pre class="mermaid"> 是人类交付超集 → 优先校；prd 无块时回退校 spec ```mermaid

_MERMAID_PRE_RE = re.compile(r'<pre\s+class="mermaid"\s*>(.*?)</pre>', re.DOTALL)
_MERMAID_FENCE_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)


def _find_mmdc() -> str | None:
    """探测 mmdc 可执行路径：PATH → npm prefix/bin → 常见全局位置。

    mmdc 常装在 npm 全局 prefix（本机 ~/.hermes/node/bin）不在 PATH，故 shutil.which
    可能 miss，须 npm prefix + 常见位置兜底。
    """
    found = shutil.which("mmdc")
    if found:
        return found
    candidates: list[str] = []
    try:
        prefix = subprocess.run(
            ["npm", "config", "get", "prefix"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        if prefix:
            candidates.append(os.path.join(prefix, "bin", "mmdc"))
    except Exception:
        pass
    candidates += [
        os.path.expanduser("~/.hermes/node/bin/mmdc"),
        os.path.expanduser("~/.local/bin/mmdc"),
        "/usr/local/bin/mmdc",
        os.path.expanduser("~/node_modules/.bin/mmdc"),
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def _extract_mermaid_blocks(spec_md: str, prd_html: str) -> list[tuple[str, str]]:
    """提取 mermaid 块：prd <pre class="mermaid"> 优先（人类交付超集），无则回退 spec。

    prd 块内容经 html.unescape——浏览器 mermaid.js 读 textContent 时会解 HTML 实体，
    故须与运行时一致（如 `&gt;` → `>`，`&amp;` → `&`）；raw `<br/>` 标签不受影响。
    """
    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(_MERMAID_PRE_RE.finditer(prd_html)):
        blocks.append((f"prd#{i + 1}", html.unescape(m.group(1).strip())))
    if not blocks:
        for i, m in enumerate(_MERMAID_FENCE_RE.finditer(spec_md)):
            blocks.append((f"spec#{i + 1}", m.group(1).strip()))
    return blocks


def check_mermaid_syntax(spec_md: str, prd_html: str, r: Report) -> None:
    """S4-33（WARN 阶段）：所有 mermaid 块经 mmdc 实际 parse，语法错则 WARN。

    一次性消除 #23/#26/#34/#35 类 mermaid 语法反复（括号未引号 / edge label / 时序图等）。
    mmdc 未安装 → WARN 跳过（提示安装），不阻断。WARN 阶段（dry-run 纪律）：
    3 仓 dry-run + FP<30% 后升 FAIL（带语法错的图进不了产物）。
    """
    r.section("S4-33 mermaid 语法校验（mmdc parse，WARN 阶段）")
    mmdc = _find_mmdc()
    if not mmdc:
        r.warn(
            "mmdc 未安装（npm install -g @mermaid-js/mermaid-cli），跳过 mermaid 语法校验；"
            "建议安装后重跑以捕获括号未引号 / edge label 等语法错（不阻断）"
        )
        return

    blocks = _extract_mermaid_blocks(spec_md, prd_html)
    if not blocks:
        r.ok("未检测到 mermaid 块（产品无流程图 / 架构图，跳过）")
        return

    with tempfile.TemporaryDirectory() as td:
        md_path = os.path.join(td, "all.md")
        cfg_path = os.path.join(td, "pp.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}, f)
        with open(md_path, "w", encoding="utf-8") as f:
            for _label, content in blocks:
                f.write(f"```mermaid\n{content}\n```\n\n")
        try:
            proc = subprocess.run(
                [mmdc, "-p", cfg_path, "-i", md_path, "-o", os.path.join(td, "out.svg")],
                capture_output=True, text=True, timeout=180,
            )
        except subprocess.TimeoutExpired:
            r.warn(f"mmdc 渲染超时（{len(blocks)} 块 > 180s），跳过 mermaid 语法校验（不阻断）")
            return
        except Exception as e:  # noqa: BLE001 — 任何调用异常都降级为 WARN 跳过，不阻断
            r.warn(f"mmdc 调用异常（{type(e).__name__}: {e}），跳过 mermaid 语法校验（不阻断）")
            return

    if proc.returncode == 0:
        r.ok(f"全部 {len(blocks)} 个 mermaid 块语法校验通过（mmdc parse）")
        return

    err = (proc.stderr or proc.stdout or "").strip()
    parse_line = ""
    for ln in err.splitlines():
        low = ln.lower()
        if "parse error" in low or ("error" in low and "at " not in low):
            parse_line = ln.strip()
            break
    r.warn(
        f"mermaid 块存在语法错误（mmdc parse 失败 exit={proc.returncode}）：{parse_line[:200] or err[:200]}；"
        f"共 {len(blocks)} 块，mmdc 在首个错误块停止——修复后重跑捕获后续；"
        f"WARN 阶段不阻断，3 仓 dry-run 通过后升 FAIL"
    )


# ── 校验 3.6｜issue #3/#4 嵌套约束（frame-card / interaction-card / section-header）──

# 来源：
#   - issue #3：frame-card 内不嵌套 section-header（section-header 已在 proto-section 一级层级）
#   - issue #4：interaction-card 不嵌套在 frame-card 内（须为 proto-section 直接子元素，与 frame-card 同级兄弟）
# SSOT 真源：prd_template.html `<style>` L268-366 + prd_expression_standard.md §四 区块 A 规则段（L677-678）
# 派生扩展：task_card_template.md 草稿示例（L189-208）/ gen_scaffold.py build_prd_module_draft frame_blocks
# 本函数为机械兜底：若派生层（草稿 / template / 任一拼装产物）违反结构，强制 FAIL 阻断 Step 7 自审

class _SectionNestingChecker(HTMLParser):
    """追踪 prd.html 中 <div> 嵌套深度,识别违反 issue #3/#4 嵌套约束的位置。

    规则：
      R1 frame-card 内不应含 section-header
      R2 frame-card 内不应含 interaction-card
      R3 interaction-card 须是 proto-section 直接子元素（不嵌入 frame-card 等子容器）
         —— 由 R2 的逆否命题机械等价覆盖；本实现统一用"在 frame-card 内出现 interaction-card"信号触发。
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        # div 栈：每项为 dict(classes: set[str], section_id: str | None)
        # 注意：仅追踪 div / section 这两个标签即可覆盖本次校验所需嵌套
        self._stack: list[dict] = []
        # 命中违反清单：每项 (rule_id, section_id, detail)
        self.violations: list[tuple[str, str, str]] = []

    @staticmethod
    def _extract_classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        for k, v in attrs:
            if k == "class" and v:
                return set(v.split())
        return set()

    @staticmethod
    def _extract_id(attrs: list[tuple[str, str | None]]) -> str | None:
        for k, v in attrs:
            if k == "id":
                return v
        return None

    def _current_section_id(self) -> str:
        for frame in reversed(self._stack):
            if frame.get("tag") == "section" and frame.get("section_id"):
                return frame["section_id"]
        return "(no-section)"

    def _is_inside_frame_card(self) -> bool:
        # 仅查询当前栈中是否有任意 div 含 frame-card class
        return any(
            frame.get("tag") == "div" and "frame-card" in frame.get("classes", set())
            for frame in self._stack
        )

    def _is_inside_proto_section(self) -> bool:
        return any(
            frame.get("tag") == "section" and "proto-section" in frame.get("classes", set())
            for frame in self._stack
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in ("div", "section"):
            return
        classes = self._extract_classes(attrs)
        sid = self._extract_id(attrs) if tag == "section" else None
        frame = {"tag": tag, "classes": classes, "section_id": sid}

        # 仅当处于 proto-section 内时启用嵌套校验（避免误报 cover-page 等其他 section）
        if tag == "div" and self._is_inside_proto_section():
            owning_section = self._current_section_id()
            inside_frame_card = self._is_inside_frame_card()

            # R1：frame-card 内出现 section-header
            if inside_frame_card and "section-header" in classes:
                self.violations.append((
                    "R1",
                    owning_section,
                    "frame-card 内嵌套 section-header（issue #3 违反）",
                ))
            # R2 + R3：frame-card 内出现 interaction-card
            if inside_frame_card and "interaction-card" in classes:
                self.violations.append((
                    "R2",
                    owning_section,
                    "interaction-card 嵌套在 frame-card 内（issue #4 违反；应作为 proto-section 直接子元素与 frame-card 同级兄弟）",
                ))

        self._stack.append(frame)

    def handle_endtag(self, tag: str) -> None:
        if tag not in ("div", "section"):
            return
        # 反向匹配最近的同标签开 tag（容错残缺 HTML）
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].get("tag") == tag:
                del self._stack[i:]
                return


def check_section_nesting(prd_html: str, r: Report) -> None:
    r.section("issue #3/#4 嵌套约束（frame-card 内不嵌套 section-header / interaction-card；interaction-card 必须是 proto-section 直接子元素）")

    parser = _SectionNestingChecker()
    try:
        parser.feed(prd_html)
        parser.close()
    except Exception as e:
        # HTMLParser 一般容错性较好；任何意外异常作为 WARN 不阻断（避免误伤）
        r.warn(f"嵌套校验解析异常（不阻断流程）：{e}")
        return

    if not parser.violations:
        r.ok("frame-card / interaction-card / section-header 嵌套结构合规（issue #3/#4 规则全部通过）")
        return

    # 按 rule + section 分组聚合后逐条 fail
    grouped: dict[tuple[str, str], list[str]] = {}
    for rule_id, sid, detail in parser.violations:
        grouped.setdefault((rule_id, sid), []).append(detail)

    for (rule_id, sid), details in grouped.items():
        r.fail(
            f"[{rule_id}] <section id=\"{sid}\"> {details[0]}"
            + (f"（共 {len(details)} 处）" if len(details) > 1 else "")
        )


# ── 校验 3.7｜frame-card 端口标签 + .frame-cell 嵌套规则（多端并列必出现）──

# SSOT 真源：prd_template.html .frame-cell / .frame-platform-item / .frame-platform-tag
#            / .frame-platform-note CSS 定义
# SSOT 派生：prd_expression_standard.md §四 区块 B「端口标签 + 视觉帧 DOM 嵌套」+
#            「端口差异说明」[Must] 规则段 / proto_cross_platform.md §六 6.1 + 6.2
# 规则：1 个 frame-card 内并列 ≥ 2 个端口帧实例（含 ≥ 2 种类型）时:
#   ①每个端口帧必须包在 .frame-cell 内（不能直接挂在 .frame-wrapper 下）
#   ②每个 .frame-cell 必须含 .frame-platform-item（cell 顶，frame 之上）
#   ③每个 .frame-platform-item 必须含 .frame-platform-tag span
#   ④.frame-platform-note 为可选（端口差异说明跟随标签时使用）
# 单端 frame-card（仅 1 种端口或仅 1 帧）可省略 .frame-cell + .frame-platform-item，
#   .frame-wrapper 内直接放视觉帧。

PLATFORM_FRAME_NAMES = {
    "phone-frame", "tablet-frame", "desktop-frame", "miniprogram-frame", "h5-frame",
}


class _FramePlatformTagChecker(HTMLParser):
    """扫描 frame-card 的 DOM 结构,校验 .frame-cell 嵌套规则。

    每个 frame-card 维护一个 ctx,关闭时结算:
      - cells: list[{frame_type, has_platform_item, has_tag}] cell 内 frame + 标签结构
      - direct_frames: list[str] 直接挂在 frame-wrapper 下的端口帧类型（无 cell 包裹）
      - frame_types: list[str] 全部端口帧实例类型（cell 内 + 直挂，DOM 顺序）
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        # 栈项：dict(tag, classes, section_id, frame_card_ctx?, in_frame_cell?, cell_record?)
        self._stack: list[dict] = []
        # 每个多端并列 frame-card 的检查结果（≥ 2 帧 + ≥ 2 类型，供 check_frame_platform_tag 用）
        self.frame_card_results: list[dict] = []
        # 所有 frame-card 全量记录（供 check_page_platform_coverage 用）
        self.all_frame_cards: list[dict] = []

    @staticmethod
    def _extract_classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        for k, v in attrs:
            if k == "class" and v:
                return set(v.split())
        return set()

    @staticmethod
    def _extract_id(attrs: list[tuple[str, str | None]]) -> str | None:
        for k, v in attrs:
            if k == "id":
                return v
        return None

    def _current_section_id(self) -> str:
        for f in reversed(self._stack):
            if f.get("tag") == "section" and f.get("section_id"):
                return f["section_id"]
        return "(no-section)"

    def _current_frame_card_ctx(self) -> dict | None:
        for f in reversed(self._stack):
            if f.get("frame_card_ctx") is not None:
                return f["frame_card_ctx"]
        return None

    def _current_cell_record(self) -> dict | None:
        for f in reversed(self._stack):
            if f.get("cell_record") is not None:
                return f["cell_record"]
        return None

    def _is_inside_frame_cell(self) -> bool:
        return any(
            f.get("in_frame_cell") is True
            for f in self._stack
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in ("div", "section", "span", "p"):
            return
        classes = self._extract_classes(attrs)
        sid = self._extract_id(attrs) if tag == "section" else None
        frame_entry: dict = {"tag": tag, "classes": classes, "section_id": sid}

        if tag == "div":
            # 检测 frame-card：开启新 ctx
            if "frame-card" in classes:
                frame_entry["frame_card_ctx"] = {
                    "section_id": self._current_section_id(),
                    "cells": [],             # list[{frame_type, has_platform_item, has_tag}]
                    "direct_frames": [],     # list[str] 直接挂 wrapper 下的帧类型（无 cell）
                    "frame_types": [],       # list[str] 全部帧类型（DOM 顺序）
                }

            ctx = self._current_frame_card_ctx()
            if ctx is not None:
                # 检测 .frame-cell：开启新 cell record
                if "frame-cell" in classes:
                    cell_rec = {
                        "frame_type": None,
                        "has_platform_item": False,
                        "has_tag": False,
                    }
                    ctx["cells"].append(cell_rec)
                    frame_entry["in_frame_cell"] = True
                    frame_entry["cell_record"] = cell_rec

                # 检测 .frame-platform-item（必须在 frame-cell 内才计入）
                if "frame-platform-item" in classes and self._is_inside_frame_cell():
                    cell = self._current_cell_record()
                    if cell is not None:
                        cell["has_platform_item"] = True

                # 检测端口帧实例
                hits = classes & PLATFORM_FRAME_NAMES
                if hits:
                    frame_type = next(iter(hits))
                    ctx["frame_types"].append(frame_type)
                    cell = self._current_cell_record()
                    if cell is not None and self._is_inside_frame_cell():
                        # cell 内的端口帧
                        cell["frame_type"] = frame_type
                    else:
                        # 直接挂 wrapper 下的端口帧（多端时违规，单端时合规）
                        ctx["direct_frames"].append(frame_type)

        elif tag == "span":
            # 检测 .frame-platform-tag：标记当前最近的 cell record
            if "frame-platform-tag" in classes:
                cell = self._current_cell_record()
                if cell is not None:
                    cell["has_tag"] = True

        self._stack.append(frame_entry)

    def handle_endtag(self, tag: str) -> None:
        if tag not in ("div", "section", "span", "p"):
            return
        # 反向匹配最近的同 tag 开标签
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].get("tag") == tag:
                closed = self._stack[i]
                # 关闭 frame-card 时结算
                if "frame_card_ctx" in closed:
                    ctx = closed["frame_card_ctx"]
                    types_set = set(ctx["frame_types"])
                    frame_count = len(ctx["frame_types"])
                    card_data = {
                        "section_id": ctx["section_id"],
                        "types": sorted(types_set),
                        "frame_count": frame_count,
                        "cells": ctx["cells"],
                        "cells_count": len(ctx["cells"]),
                        "direct_frames": ctx["direct_frames"],
                        "direct_frames_count": len(ctx["direct_frames"]),
                        # cell 内缺 platform-item 的 cell 索引
                        "cells_missing_item": [
                            idx for idx, c in enumerate(ctx["cells"])
                            if not c["has_platform_item"]
                        ],
                        # cell 内 platform-item 缺 tag 的 cell 索引
                        "cells_missing_tag": [
                            idx for idx, c in enumerate(ctx["cells"])
                            if c["has_platform_item"] and not c["has_tag"]
                        ],
                    }
                    # 全量记录所有 frame-card
                    self.all_frame_cards.append(card_data)
                    # 触发条件：≥ 2 帧实例 且 ≥ 2 种类型
                    if frame_count >= 2 and len(types_set) >= 2:
                        self.frame_card_results.append(card_data)
                del self._stack[i:]
                return


def check_frame_platform_tag(prd_html: str, r: Report) -> None:
    """frame-card 端口标签 + .frame-cell 嵌套规则机械兜底。

    新 DOM 结构：
      frame-card
      └─ frame-wrapper                  ← 唯一 flex 容器（横向铺多端 cell）
         ├─ frame-cell                  ← 每端一个 cell（纵向 flex）
         │  ├─ frame-platform-item      ← cell 顶，含 .frame-platform-tag（必填）
         │  │  ├─ .frame-platform-tag   （span,必填）
         │  │  └─ .frame-platform-note  （p,可选）
         │  └─ phone-frame / desktop-frame / ...   ← 视觉帧（cell 底）
         └─ ...

    校验：1 个 frame-card 内并列 ≥ 2 端口帧实例（含 ≥ 2 种类型）时:
      ①每个端口帧必须包在 .frame-cell 内（不能直接挂在 .frame-wrapper 下）
      ②每个 .frame-cell 必须含 .frame-platform-item
      ③每个 .frame-platform-item 必须含 .frame-platform-tag span
    单端 / 单帧 frame-card 跳过（规则不适用，cell 可省略）。
    """
    r.section("frame-card 端口标签 + .frame-cell 嵌套规则（多端并列必出现）")

    parser = _FramePlatformTagChecker()
    try:
        parser.feed(prd_html)
        parser.close()
    except Exception as e:
        r.warn(f"端口标签校验解析异常（不阻断流程）：{e}")
        return

    if not parser.frame_card_results:
        r.ok("无多端并列 frame-card（无 ≥ 2 端口帧实例 + ≥ 2 类型场景，规则不适用）")
        return

    has_fail = False
    for item in parser.frame_card_results:
        sec = f'<section id="{item["section_id"]}">'

        # ① 端口帧直接挂在 wrapper 下（未包在 cell 内）
        if item["direct_frames"]:
            r.fail(
                f"端口帧未包在 .frame-cell 内 {sec} frame-card 并列 {item['types']}"
                f"（{item['frame_count']} 帧实例）但 {item['direct_frames_count']} 个端口帧"
                f" {item['direct_frames']} 直接挂在 .frame-wrapper 下"
                f"（多端必须用 .frame-cell 包裹「标签 + 帧」）"
            )
            has_fail = True
            continue

        # ② cell 缺 .frame-platform-item
        if item["cells_missing_item"]:
            missing_idx = item["cells_missing_item"]
            r.fail(
                f"cell 缺标签 item {sec} frame-card 内第 {missing_idx} 个 .frame-cell"
                f"未含 .frame-platform-item（共 {len(missing_idx)}/{item['cells_count']} 缺失）"
            )
            has_fail = True
            continue

        # ③ .frame-platform-item 缺 .frame-platform-tag
        if item["cells_missing_tag"]:
            missing_idx = item["cells_missing_tag"]
            r.fail(
                f"端口标签缺失 {sec} frame-card 内第 {missing_idx} 个 .frame-cell"
                f"的 .frame-platform-item 未含 .frame-platform-tag span"
                f"（共 {len(missing_idx)}/{item['cells_count']} 缺失）"
            )
            has_fail = True

    if not has_fail:
        ok_count = len(parser.frame_card_results)
        r.ok(f"frame-card 端口标签 + .frame-cell 嵌套全部合规（{ok_count} 个多端并列 frame-card 全部满足 DOM 约束）")


# ── 校验 3.8｜页面级端口覆盖漂移防御（SNB-005 修复，WARN-phase）──────────────
#
# 漏洞场景：单页面 frame-card 内 frame-wrapper 实绘 1 帧，但声明 ≥ 2 个 .frame-cell
# → 声明多端但实绘只覆盖 1 端。
#
# 与既有 S4-04 (SNB-005, line 4374-) 模块级覆盖核查的关系：
#   - 模块级：M01 整体所有声明端口须各有 ≥ 1 帧（粗粒度，模块间互补可掩盖）
#   - 页面级（本 check）：单页面 frame-card 内 .frame-cell 声明 vs frame-wrapper 实绘对齐
#   - 例：M01 含 10 页，9 页画了全端、第 10 页只画 desktop（仍声明 ≥ 2 cell）→
#     模块级 PASS（M01 整体有多端帧），但第 10 页实际多端缺失逃过。本 check 抓这种漂移。
#
# 豁免：紧邻 frame-card 之前出现 <!-- skeleton-single-frame: <reason> --> 注释
# 可显式豁免（如 Pad 同手机帧、引用说明卡、跨端共用一帧的合理场景；reason 必填）。
#
# WARN-phase：dry-run 纪律——新追溯规则先 WARN-phase 一轮 stabilize 再升 FAIL，
# 避免追溯硬阻断已交付存量（同 S4-04 SNB-005 模块级 + S4-28 v2 档 C + S4-32 经验）。

_SINGLE_FRAME_EXEMPT_RE = re.compile(
    r"<!--\s*skeleton-single-frame:\s*(\S[^>]*?)\s*-->", re.IGNORECASE
)
_PRECHECK_SECTION_OPEN_RE = re.compile(r'<section\s+id\s*=\s*"([^"]+)"', re.IGNORECASE)


def _collect_single_frame_exempt_sections(prd_html: str) -> set[str]:
    """收集所有 <!-- skeleton-single-frame: <reason> --> 豁免注释覆盖的 section id。

    豁免范围：注释之前出现的最近一个 <section id="..."> 视为该豁免作用域。
    """
    exempt: set[str] = set()
    for m in _SINGLE_FRAME_EXEMPT_RE.finditer(prd_html):
        prev = prd_html[: m.start()]
        sections = _PRECHECK_SECTION_OPEN_RE.findall(prev)
        if sections:
            exempt.add(sections[-1])
    return exempt


def check_page_platform_coverage(prd_html: str, r: Report) -> None:
    """页面级端口覆盖漂移检测（SNB-005 修复补页面级精度，WARN-phase）。

    扫描所有 frame-card，命中以下漂移则 WARN：
      - frame-wrapper 实绘单帧（frame_count == 1）
      - 声明 ≥ 2 个 .frame-cell
      - 该 section 不在 skeleton-single-frame 豁免清单内

    与 check_frame_platform_tag 互补：前者校验 ≥ 2 帧场景的对齐（设计意图，
    单帧跳过），本 check 抓单帧 + 多 cell 的不一致（设计盲区）。
    """
    r.section(
        "页面级端口覆盖（单帧+多 .frame-cell 漂移防御，SNB-005 修复 WARN-phase）"
    )

    parser = _FramePlatformTagChecker()
    try:
        parser.feed(prd_html)
        parser.close()
    except Exception as e:
        r.warn(f"页面级端口覆盖解析异常（不阻断流程）：{e}")
        return

    exempt_sections = _collect_single_frame_exempt_sections(prd_html)

    drift_count = 0
    exempt_used = 0
    for card in parser.all_frame_cards:
        if card["frame_count"] != 1:
            continue
        if card["cells_count"] < 2:
            continue
        # 命中漂移
        if card["section_id"] in exempt_sections:
            exempt_used += 1
            continue
        drift_count += 1
        r.warn(
            f"端口覆盖漂移 <section id=\"{card['section_id']}\"> "
            f"frame-card 实绘单帧 {card['types']} 但声明 "
            f"{card['cells_count']} 个 .frame-cell → 声明 vs 实绘不一致；"
            f"补齐所有声明端的帧，或在 frame-card 之前加 "
            f"<!-- skeleton-single-frame: <reason> --> 注释显式豁免（reason 必填，"
            f"如「Pad 同手机帧」「引用说明卡」）"
        )

    if drift_count == 0:
        msg = "无单帧+多 .frame-cell 端口覆盖漂移"
        if exempt_used > 0:
            msg += f"（{exempt_used} 个 frame-card 经 skeleton-single-frame 注释显式豁免）"
        r.ok(msg)


# ── 校验 4｜proj 组件协议（S4-17/18/19）─────────────────────────────────────

REQUIRED_PROJ_FIELDS = [
    "inherits", "modules", "slots", "states", "state_transitions", "field_schema",
    # 业务语义三段（issue 2026-05-07_1117 落地,见 proj_component_protocol.md §二.2 [Must]）:
    # 缺一段后续开发构建组件时无业务依据,会反复回查产品定义 §7
    "boundary",       # 功能边界（applicable_when / not_applicable_when / differs_from）
    "usage",          # 用途说明（business_scenarios / modules / pain_point）
    "interaction",    # 交互说明（user_flow / collaborates_with）
]
REQUIRED_STATE_KEYS = ["hover", "active", "disabled", "loading", "error", "empty", "selected", "focused"]

# 提取 markdown 中的 yaml 代码块
YAML_BLOCK_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)
# 匹配 yaml 块内顶层 `- id: proj.LX.name`（标识一个 proj 组件的起点）
PROJ_COMPONENT_HEAD_RE = re.compile(r"^- id:\s*(proj\.L\d+\.[\w-]+)\s*$", re.MULTILINE)


def parse_proj_components(md: str) -> list[dict]:
    """从 components_[产品名]_latest.md 中解析所有 proj 组件，
    返回 [{id, text}] 列表；text 为该组件 yaml 片段（含末尾的状态 / 字段定义）。"""
    components: list[dict] = []
    for block_match in YAML_BLOCK_RE.finditer(md):
        block = block_match.group(1)
        positions = [(m.start(), m.group(1)) for m in PROJ_COMPONENT_HEAD_RE.finditer(block)]
        for i, (pos, comp_id) in enumerate(positions):
            end = positions[i + 1][0] if i + 1 < len(positions) else len(block)
            components.append({"id": comp_id, "text": block[pos:end]})
    return components


def check_proj_components(data: dict, prd_html: str, r: Report) -> None:
    """S4-17/18/19 — proj 组件协议核查。"""
    r.section("proj 组件协议（S4-17/18/19）")

    product = data.get("product", "").strip()
    components_path = OUTPUT_DIR / f"components_{product}_latest.md"

    if not components_path.exists():
        r.ok("无 proj 组件需核查（components 文件不存在，Step 2.5 判定本期无新建组件）")
        return

    md = components_path.read_text(encoding="utf-8")
    components = parse_proj_components(md)

    if not components:
        r.ok("无 proj 组件需核查（components 文件存在但未声明任何 proj.* 组件）")
        return

    # 收集 PRD 中所有 <style> 块内容（用于 CSS 检查）
    style_blocks = re.findall(r"<style[^>]*>(.*?)</style>", prd_html, re.DOTALL)
    all_styles = "\n".join(style_blocks)

    declared_ids = {c["id"] for c in components}

    schema_ok = state_ok = showcase_ok = rows_ok = True
    inline_ok = css_def_ok = state_mod_ok = new_ok = True

    for comp in components:
        cid = comp["id"]
        text = comp["text"]
        name_match = re.match(r"proj\.L\d+\.([\w-]+)", cid)
        if not name_match:
            r.fail(f"proj 组件 id 格式错误：{cid!r}")
            schema_ok = False
            continue
        name = name_match.group(1)
        base_class = f".proj-{name}"

        # —— 1. schema 必填字段 ——
        for field in REQUIRED_PROJ_FIELDS:
            if not re.search(rf"^\s*{field}\s*:", text, re.MULTILINE):
                r.fail(f"[{cid}] 缺少必填字段：{field}")
                schema_ok = False

        # —— 2. 状态枚举完整性（8 项 needed + reason） ——
        applicable_match = re.search(
            r"applicable\s*:\s*\n((?:\s+- \w+\s*:.*\n?)+)", text
        )
        applicable_block = applicable_match.group(1) if applicable_match else ""
        needed_yes_states: list[str] = []

        for skey in REQUIRED_STATE_KEYS:
            line_match = re.search(
                rf"^\s*-\s*{skey}\s*:\s*\{{(.+?)\}}\s*$", applicable_block, re.MULTILINE
            )
            if not line_match:
                r.fail(f"[{cid}] states.applicable 缺少 {skey} 项")
                state_ok = False
                continue
            line_content = line_match.group(1)
            needed_match = re.search(r"needed\s*:\s*(yes|no)", line_content)
            if not needed_match:
                r.fail(f"[{cid}] {skey} 缺少 needed 字段或值非 yes/no")
                state_ok = False
                continue
            if not re.search(r"reason\s*:", line_content):
                r.fail(f"[{cid}] {skey} 缺少 reason 字段")
                state_ok = False
                continue
            if needed_match.group(1) == "yes":
                needed_yes_states.append(skey)

        # —— 3. 独立状态展示区存在性 ——
        showcase_id = f"proj-component-{name}"
        showcase_match = re.search(
            rf'<section[^>]*id="{re.escape(showcase_id)}"[^>]*>(.*?)</section>',
            prd_html, re.DOTALL,
        )
        if not showcase_match:
            r.fail(f'[{cid}] PRD 缺少独立状态展示区 id="{showcase_id}"')
            showcase_ok = False
        else:
            showcase_html = showcase_match.group(1)
            row_count = len(re.findall(r'class="showcase-row"', showcase_html))
            expected = len(needed_yes_states) + 1  # default + needed:yes 状态
            if row_count != expected:
                r.fail(
                    f"[{cid}] 状态展示区 .showcase-row 数={row_count}，"
                    f"应为 {expected}（needed:yes={len(needed_yes_states)} + default=1）"
                )
                rows_ok = False

        # —— 4. CSS base 类定义存在 ——
        if base_class not in all_styles:
            r.fail(f"[{cid}] CSS base 类 {base_class} 在 <style> 块中无定义")
            css_def_ok = False

        # —— 5. 状态 modifier 选择器完备 ——
        for sname in needed_yes_states:
            modifier = f"{base_class}.is-{sname}"
            if modifier not in all_styles:
                r.fail(f"[{cid}] 缺少状态 modifier 选择器 {modifier}")
                state_mod_ok = False

        # —— 6. 禁 inline style（CSS 变量与数据属性除外）——
        proj_tag_re = rf'<\w+[^>]*\bclass="[^"]*\bproj-{re.escape(name)}\b[^"]*"[^>]*>'
        for tag_match in re.finditer(proj_tag_re, prd_html):
            full_tag = tag_match.group(0)
            style_attr = re.search(r'\sstyle="([^"]*)"', full_tag)
            if not style_attr:
                continue
            style_content = style_attr.group(1).strip()
            allowed = True
            for decl in style_content.rstrip(";").split(";"):
                decl = decl.strip()
                if not decl:
                    continue
                # 仅允许 CSS 自定义属性（--xxx: ...）
                if not re.match(r"^--[\w-]+\s*:", decl):
                    allowed = False
                    break
            if not allowed:
                r.fail(
                    f"[{cid}] 使用处含禁用的 inline style："
                    f'style="{style_content[:80]}"'
                )
                inline_ok = False
                break  # 一个组件只报一次，避免刷屏

        # —— 7. NEW 标记完整性 ——
        for tag_match in re.finditer(proj_tag_re, prd_html):
            full_tag = tag_match.group(0)
            if 'data-component-status="NEW"' not in full_tag:
                r.fail(f'[{cid}] proj 组件实例缺少 data-component-status="NEW" 标记')
                new_ok = False
                break
            if f'data-component-id="{cid}"' not in full_tag:
                r.fail(f'[{cid}] proj 组件实例缺少 data-component-id="{cid}" 标记')
                new_ok = False
                break

    # —— 8. NEW 组件可追溯（PRD 中 data-component-id 必须能在 components 文件找到）——
    used_ids = set(re.findall(r'data-component-id="([^"]+)"', prd_html))
    untraceable = used_ids - declared_ids
    traceability_ok = True
    if untraceable:
        r.fail(
            f"PRD 中 data-component-id 在 components 文件中无对应声明："
            f"{sorted(untraceable)}"
        )
        traceability_ok = False

    # 汇总通过项
    if schema_ok:
        r.ok(f"proj 组件 schema 完整性（{len(components)} 个组件含必填字段）")
    if state_ok:
        r.ok(f"proj 组件状态枚举完整性（每组件 {len(REQUIRED_STATE_KEYS)} 项 needed+reason 全满足）")
    if showcase_ok:
        r.ok("proj 组件状态展示区全部存在")
    if rows_ok:
        r.ok("proj 组件状态展示行数与 schema 一致")
    if css_def_ok:
        r.ok("proj 组件 CSS base 类全部已定义")
    if state_mod_ok:
        r.ok("proj 组件 .is-{state} modifier 选择器全部已定义")
    if inline_ok:
        r.ok("proj 组件 CSS 抽象纪律：无禁用 inline style")
    if new_ok:
        r.ok("proj 组件 NEW 标记完整性")
    if traceability_ok:
        r.ok("proj 组件 data-component-id 全部可追溯")


# ── 校验 5｜组件索引一致性 ────────────────────────────────────────────────────

PUB_INDEX_PATH = REPO_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "pub_components_index.md"
PUB_COMPONENTS_DIR = REPO_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "components"


def check_pub_index(r: Report) -> None:
    """pub_components_index.md 一致性。"""
    r.section("pub 组件索引一致性")

    if not PUB_INDEX_PATH.exists():
        r.fail(f"pub_components_index.md 不存在：{PUB_INDEX_PATH}")
        return

    md = PUB_INDEX_PATH.read_text(encoding="utf-8")

    # —— 1. components/*.md 必有索引项 ——
    if PUB_COMPONENTS_DIR.exists():
        md_files = [
            f for f in PUB_COMPONENTS_DIR.glob("*.md")
            if not f.name.startswith("_")
        ]
        missing = [f.name for f in md_files if f"components/{f.name}" not in md]
        if missing:
            r.fail(f"以下 components/*.md 在 pub 索引中无引用：{missing}")
        else:
            r.ok(f"components/*.md 全部在 pub 索引中有引用（{len(md_files)} 个）")

    # —— 2. 子类编号唯一 ——
    sub_headings = re.findall(r"^####\s+(\d+\.\d+\.\d+)\b", md, re.MULTILINE)
    if len(sub_headings) != len(set(sub_headings)):
        dupes = sorted({h for h in sub_headings if sub_headings.count(h) > 1})
        r.fail(f"pub 索引子类编号重复：{dupes}")
    else:
        r.ok(f"pub 索引子类编号唯一（{len(sub_headings)} 个子类）")

    # —— 3. 业务场景反查表中引用的 id 必须存在于组件总表 ——
    section3_match = re.search(
        r"## 三、组件总表(.*?)(?=^## 四、)", md, re.DOTALL | re.MULTILINE
    )
    section3 = section3_match.group(1) if section3_match else ""
    declared_ids = set(re.findall(r"\bbj-[\w-]+\b", section3))

    section4_match = re.search(
        r"## 四、按业务场景反查(.*?)(?=^## 五、)", md, re.DOTALL | re.MULTILINE
    )
    section4 = section4_match.group(1) if section4_match else ""
    referenced_ids = set(re.findall(r"\bbj-[\w-]+\b", section4))

    unknown = referenced_ids - declared_ids
    if unknown:
        r.fail(f"业务场景反查表引用了未声明的组件 id：{sorted(unknown)}")
    elif referenced_ids:
        r.ok(f"业务场景反查表引用 id 全部在组件总表已声明（{len(referenced_ids)} 个）")
    else:
        r.warn("业务场景反查表（§四）未提取到任何 fb-* 引用，请人工核查")

    # —— 4. 分类总览组件数与组件总表行数一致 ——
    overview_match = re.search(
        r"## 二、分类总览\s*\n(.*?)(?=^## 三、)", md, re.DOTALL | re.MULTILINE
    )
    overview = overview_match.group(1) if overview_match else ""
    # 解析"子类(N)"模式
    overview_counts: dict[str, int] = {}
    for line_match in re.finditer(r"^\|\s*([^\s|][^|]*?)\s*\|\s*([^|]+?)\s*\|", overview, re.MULTILINE):
        cat_name = line_match.group(1).strip()
        sub_field = line_match.group(2)
        if cat_name in {"类别", "---"} or "—" in cat_name:
            continue
        nums = [int(n) for n in re.findall(r"\((\d+)\)", sub_field)]
        if nums:
            overview_counts[cat_name] = sum(nums)

    # 统计组件总表中各一级类下的组件数（按 ### 3.x 分块，数其下的表行）
    actual_counts: dict[str, int] = {}
    section3_blocks = re.split(r"^### (\d+\.\d+)\s+([^\n]+)", section3, flags=re.MULTILINE)
    # split 结果：[before, num1, name1, content1, num2, name2, content2, ...]
    for i in range(1, len(section3_blocks), 3):
        cat_label = section3_blocks[i + 1].strip()  # "原子 atom" 等
        cat_content = section3_blocks[i + 2]
        # 数表格数据行（排除表头与分隔行）
        rows = re.findall(r"^\|[^|]+\|[^|]+\|[^|]+\|", cat_content, re.MULTILINE)
        # 每个表都有 1 行表头 + 1 行分隔；若无 #### 子类至少有 1 个表
        sub_table_count = max(
            1,
            len(re.findall(r"^####\s+\d+\.\d+\.\d+", cat_content, re.MULTILINE)),
        )
        data_rows = max(0, len(rows) - 2 * sub_table_count)
        actual_counts[cat_label] = data_rows

    overview_ok = True
    for cat_label, actual in actual_counts.items():
        # cat_label 形如 "原子 atom"，分类总览第一列形如 "原子 atom"
        if cat_label not in overview_counts:
            r.fail(f"分类总览缺少类别 {cat_label!r}")
            overview_ok = False
            continue
        if overview_counts[cat_label] != actual:
            r.fail(
                f"分类总览组件数 {overview_counts[cat_label]} ≠ 组件总表实际行数 {actual}"
                f"（类别：{cat_label}）"
            )
            overview_ok = False
    if overview_ok and actual_counts:
        r.ok(f"分类总览组件数与组件总表行数一致（{sum(actual_counts.values())} 个组件）")


FB_FALLBACK_CSS_PATH = REPO_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "fb-fallback.css"


def check_prd_fb_registration(data: dict, prd_html: str, r: Report) -> None:
    """S4-23 — PRD 中所有 fb-* class 必须已在 pub 索引或 fallback.css 登记。

    权威集合：
      - pub_components_index.md 中提到的全部 fb-* token（组件 id）
      - fb-fallback.css 中实际定义的全部 .fb-* 选择器（子元素 / modifier 完整名）
    两者并集即合法 class 清单。
    """
    r.section("PRD fb-* class 已登记（S4-23）")

    registered: set[str] = set()

    if PUB_INDEX_PATH.exists():
        pub_md = PUB_INDEX_PATH.read_text(encoding="utf-8")
        registered.update(re.findall(r"\bbj-[a-z][\w-]*", pub_md))

    if FB_FALLBACK_CSS_PATH.exists():
        css_text = FB_FALLBACK_CSS_PATH.read_text(encoding="utf-8")
        # 抓 .fb-xxx 选择器（去掉前导点）
        registered.update(re.findall(r"\.fb-[a-z][\w-]*", css_text))
        registered = {t.lstrip(".") for t in registered}

    if not registered:
        r.warn("pub 索引和 fb-fallback.css 都不存在，无法核查 S4-23")
        return

    # PRD class 属性中提取 fb-* token
    used: set[str] = set()
    for cls_match in re.finditer(r'class="([^"]*)"', prd_html):
        for token in cls_match.group(1).split():
            if token.startswith("fb-"):
                used.add(token)

    if not used:
        r.ok("PRD 中未使用任何 fb-* class（无需登记核查）")
        return

    unregistered = sorted(used - registered)
    if unregistered:
        r.fail(
            f"PRD 中以下 fb-* class 未在 pub 索引 / fallback.css 登记（违反 S4-23）："
            f"{unregistered}"
        )
    else:
        r.ok(f"PRD 中全部 fb-* class 已登记（{len(used)} 个 unique class）")


# ── S4-23 扩展：扫 prd_template.html 真源（issue 2026-05-08 NB-WE-08）─────────
# 历史教训：fb-table 在 §11.4 真源沉淀已久但未被抓到——S4-23 仅扫 outputs/prd 派生,
# 真源中漏登记 class 直到下游跑实际产物才暴露。本 check 把扫描延伸到 template 真源,
# template 含未登记 fb-* 即 FAIL,防止派生侧再撞同一坑。

PRD_TEMPLATE_PATH = REPO_ROOT / "pm-workflow" / "rules" / "prd_template.html"


def check_prd_template_fb_registration(r: Report) -> None:
    """S4-23 扩展 — prd_template.html 真源中 fb-* class 必须已在 pub 索引或 fallback.css 登记。

    与 check_prd_fb_registration 的区别：
      - check_prd_fb_registration 扫 outputs/prd_*.html 产物
      - 本 check 扫 prd_template.html 真源
    两层防御：真源不漂移 + 派生不漂移。
    """
    r.section("prd_template.html fb-* class 已登记（S4-23 扩展,扫真源）")

    if not PRD_TEMPLATE_PATH.exists():
        r.warn(f"prd_template.html 不存在：{PRD_TEMPLATE_PATH}")
        return

    registered: set[str] = set()
    if PUB_INDEX_PATH.exists():
        pub_md = PUB_INDEX_PATH.read_text(encoding="utf-8")
        registered.update(re.findall(r"\bbj-[a-z][\w-]*", pub_md))
    if FB_FALLBACK_CSS_PATH.exists():
        css_text = FB_FALLBACK_CSS_PATH.read_text(encoding="utf-8")
        registered.update(re.findall(r"\.fb-[a-z][\w-]*", css_text))
        registered = {t.lstrip(".") for t in registered}

    if not registered:
        r.warn("pub 索引和 fb-fallback.css 都不存在，无法核查 S4-23 扩展")
        return

    template_html = PRD_TEMPLATE_PATH.read_text(encoding="utf-8")

    # template class 属性中提取 fb-* token（仅 HTML class 属性,不扫 CSS 选择器或注释）
    used: set[str] = set()
    for cls_match in re.finditer(r'class="([^"]*)"', template_html):
        for token in cls_match.group(1).split():
            if token.startswith("fb-"):
                used.add(token)

    if not used:
        r.ok("prd_template.html 中未使用任何 fb-* class（无需登记核查）")
        return

    unregistered = sorted(used - registered)
    if unregistered:
        r.fail(
            f"prd_template.html 真源中以下 fb-* class 未登记（违反 S4-23 扩展）："
            f"{unregistered}；调整方向：在 pub_components_index.md 登记 + fb-fallback.css "
            f"加 selector,或重命名为非 fb-* class（如 proto-* 内部命名空间）"
        )
    else:
        r.ok(f"prd_template.html 真源 fb-* class 全部已登记（{len(used)} 个 unique class）")


PRD_EXPRESSION_STANDARD_PATH = REPO_ROOT / "pm-workflow" / "rules" / "prd_expression_standard.md"


def _parse_z_index_truth_source() -> set[int] | None:
    """解析 prd_expression_standard.md §零.1 表得到真源合法数值集合。

    返回 None 表示真源文件不存在或解析失败（豁免对账,不阻断主流程）。

    抓取规则：§零.1 表格行 `^\\| Z-(\\d+) \\|`（Z-300/200/150/100/60/50/41/40/10/1）
    10 行 1:1 对应 legal_set 10 值（NB-WE-18:§零.1 自洽不依赖 §零.2 兜底；
    Item 3 2026-05-18 加 Z-300 mermaid 全屏预览行，10 行）。
    """
    if not PRD_EXPRESSION_STANDARD_PATH.exists():
        return None
    try:
        text = PRD_EXPRESSION_STANDARD_PATH.read_text(encoding="utf-8")
    except OSError:
        return None
    truth = {int(m) for m in re.findall(r"^\| Z-(\d+) \|", text, flags=re.MULTILINE)}
    return truth or None


def _check_z_index_legal_set_drift(legal_set: set[int], r: Report) -> None:
    """运行时双向对账 legal_set ↔ §零.1 真源（防硬编码漂移,NB-WE-06 第 5 要素）。

    解析失败（真源文件不存在等）→ 静默豁免,不阻断主流程。
    集合不一致 → r.warn 漂移信号（不 fail,避免下游 PM 看到双 FAIL；漂移在 L2 维护层修）。
    """
    truth = _parse_z_index_truth_source()
    if truth is None:
        return
    only_legal = legal_set - truth
    only_truth = truth - legal_set
    if only_legal or only_truth:
        r.warn(
            f"L2 派生漂移信号：precheck legal_set 与 §零.1 真源不一致 — "
            f"legal_set 多出 {sorted(only_legal) or '∅'} / 真源多出 {sorted(only_truth) or '∅'}；"
            f"调整方向：先确认真源（prd_expression_standard.md §零.1 表 + §零.2 协议）正确,再同步 precheck_stage4.py:legal_set"
        )


FRAME_CONTAINER_CLASSES = [
    ".phone-frame",
    ".desktop-frame",
    ".h5-frame",
    ".tablet-frame",
    ".miniprogram-frame",
]


def check_frame_card_isolation(prd_html: str, r: Report) -> None:
    """§零.2 rule-3 实装（NB-WE-20,issue 2026-05-12 下游 # 14）—
    `.frame-card` 规则必须含 `isolation: isolate` 创建独立 stacking context。

    SSOT 真源：`prd_template.html` L343 `.frame-card { ...isolation: isolate; }`
    + `prd_expression_standard.md §零.2 rule-3`「frame-card stacking context 隔离」

    历史漂移：assemble.py 旧版从不重读 template `<style>` 段,导致 template
    新增 isolation 后 outputs/prd 派生层 `.frame-card` 规则缺 isolation,
    frame 内弹框 z-index 溢出到 sticky section-header / sidebar。

    本 check 是机械兜底层（assemble.py 已加 `_overwrite_first_style_from_template`
    做主动派生同步,本 check 防回归）。

    无对应规则 → 静默豁免（PRD 未用该 frame,无需校验）。

    NB-WE-25 扩展（2026-05-12 issue # 4）:5 个 frame 容器类亦须 `position: relative`,
    为内部 modal/popover 等 absolute 元素提供 positioning context;无此则 modal
    冒泡至 viewport 形成全屏漂移（M07-P10 客户端访客侧 modal 全局常驻显示就是
    此根因)。
    """
    r.section(
        "frame-card isolation + frame 容器 position: relative"
        "（§零.2 rule-3 支柱 1 + 支柱 1.b,NB-WE-20/25）"
    )

    # ── 第 1 道:.frame-card isolation:isolate（NB-WE-20）──
    m = re.search(r"\.frame-card\s*\{([^}]+)\}", prd_html)
    if not m:
        r.ok("PRD 中无 .frame-card 规则,跳过 isolation 校验（豁免）")
    else:
        rule_body = m.group(1)
        if "isolation" in rule_body and "isolate" in rule_body:
            r.ok(".frame-card 规则含 isolation: isolate（§零.2 rule-3 / 支柱 1 PASS）")
        else:
            r.fail(
                ".frame-card 规则缺少 `isolation: isolate`（违反 §零.2 rule-3 / 支柱 1）；"
                "派生层与 template 真源漂移 — 跑 assemble.py 重新拼装即可由 "
                "_overwrite_first_style_from_template 自动同步,或手动在 outputs/prd "
                ".frame-card 规则内补 `isolation: isolate;`"
            )

    # ── 第 2 道:5 个 frame 容器类 position: relative（NB-WE-25)──
    for frame_cls in FRAME_CONTAINER_CLASSES:
        pat = re.escape(frame_cls) + r"\s*\{([^}]+)\}"
        m_frame = re.search(pat, prd_html)
        if not m_frame:
            r.ok(
                f"PRD 中无 {frame_cls} 规则,跳过 position 校验"
                "（产品未涉及该端口,豁免）"
            )
            continue
        body = m_frame.group(1)
        if re.search(r"position\s*:\s*relative", body):
            r.ok(f"{frame_cls} 规则含 position: relative（§零.2 支柱 1.b PASS）")
        else:
            r.fail(
                f"{frame_cls} 规则缺少 `position: relative`（违反 §零.2 支柱 1.b）；"
                "无此则内部 absolute 元素（如 .fb-modal-overlay）冒泡到 viewport "
                "形成全屏漂移；在 prd_template.html 真源 / outputs/prd 派生层 "
                f"{frame_cls} 规则内补 `position: relative;`"
            )


# 自定义 sheet 规避模式关键字（rule-5,/retro 2026-05-13 # 5 落地）
# 命中条件:phone-frame / miniprogram-frame 内 class 含以下字面但 class 不是
# fb-* 真源（即 PM 自由发挥写了非标准 sheet 类）→ B 主因典型规避路径
SHEET_EVASION_KEYWORDS = (
    "sheet",          # .sheet / .bottom-sheet / .action-sheet
    "popup",          # .popup
    "modal-mask",     # .modal-mask（半自定义遮罩）
    "dialog",         # .dialog（非 fb- 前缀的对话框）
)


def check_panel_class_evasion(prd_html: str, r: Report) -> None:
    """S4-25：移动端 sheet 形态须用标准 .fb-modal-overlay + .fb-modal 结构。

    rule-5（/retro 2026-05-13 # 5 落地）— phone-frame / miniprogram-frame 内
    禁止 PM 用自定义 class 规避 `.fb-modal-overlay + .fb-modal` 标准结构。

    SSOT 真源：`fb-fallback.css` L509-510 `.phone-frame .fb-modal,
    .miniprogram-frame .fb-modal { ...align-self: flex-end; width: 100% }` 已实现
    sheet 形态自动适配；规范声明在 `prd_expression_standard.md §零.2 反例禁令`
    + `fb-fallback-manifest.md §3.2 Modal "移动端 Action Sheet 自动适配"`。

    历史背景：rule-1 仅扫含 `.fb-modal-overlay` 节点的 inline style 越界；当 PM
    完全不用 `.fb-modal-overlay`、自己写 `<div class="sheet">` + position:relative
    + flex:1 撑底时,rule-1 没有节点可扫 → 抓不到 → B 主因长期存在。

    本 check 的扫描机理：
    1. 在 PRD HTML 中找所有 `.phone-frame` / `.miniprogram-frame` 容器块
    2. 提取每个容器块内的所有 class 字面值
    3. class 同时满足：① 含 SHEET_EVASION_KEYWORDS 任一字面 ② 不以 `fb-` 开头
       → 命中规避模式 → r.warn（v1 不阻断 FAIL,允许下迭代升级）

    无 phone-frame / miniprogram-frame 容器 → 静默豁免（产品未涉及移动端,无需校验）。
    """
    r.section(
        "phone-frame / miniprogram-frame 内禁止自定义 sheet class "
        "规避标准 modal 结构（§零.2 rule-5,/retro 2026-05-13 # 5）"
    )

    # 找所有 phone-frame / miniprogram-frame 块（含容器自闭合标签到对应 </div> 的完整片段）
    mobile_frame_classes = (".phone-frame", ".miniprogram-frame")
    # 简化版：用 regex 找 <div class="...phone-frame..." > 起到下一个 phone-frame 或文档末（保守作为字符级窗口扫描）
    # 不做严格 DOM 树解析,只关心"phone-frame 容器附近大块文本"含规避 class 即标记
    pat_container_open = re.compile(
        r'<div\s+class\s*=\s*"([^"]*(?:phone-frame|miniprogram-frame)[^"]*)"',
        re.IGNORECASE,
    )
    container_starts = [
        (m.start(), m.group(1)) for m in pat_container_open.finditer(prd_html)
    ]
    if not container_starts:
        r.ok(
            "PRD 中无 .phone-frame / .miniprogram-frame 容器,跳过 "
            "sheet 规避扫描（产品未涉及移动端,豁免）"
        )
        return

    pat_class_attr = re.compile(r'class\s*=\s*"([^"]+)"')
    hits = []  # (frame_cls_text, evasive_class, surrounding_excerpt)
    # 限定扫描窗口：每个 mobile frame 起点向后 ~6000 字符（覆盖典型单 frame 渲染量）
    SCAN_WINDOW = 6000
    for start, frame_cls_text in container_starts:
        window = prd_html[start : start + SCAN_WINDOW]
        for m_cls in pat_class_attr.finditer(window):
            class_value = m_cls.group(1)
            # 拆 class 字面值（空格分隔）逐个判定
            for cls_token in class_value.split():
                cls_lower = cls_token.lower()
                if cls_lower.startswith("fb-"):
                    continue  # 真源 class,豁免
                if cls_lower in ("phone-frame", "miniprogram-frame"):
                    continue  # 容器自身,豁免
                # 命中关键字判定
                for kw in SHEET_EVASION_KEYWORDS:
                    if kw in cls_lower:
                        # 排除已登记的 proj.* 派生组件（class 含 `.` 视为 proj 命名,不属于自定义 sheet 范畴）
                        if "." in cls_token:
                            break
                        snippet_start = max(0, m_cls.start() - 60)
                        snippet = window[snippet_start : m_cls.end() + 60]
                        snippet = re.sub(r"\s+", " ", snippet)[:200]
                        hits.append((frame_cls_text, cls_token, snippet))
                        break

    if not hits:
        r.ok(
            "phone-frame / miniprogram-frame 内未发现自定义 sheet class 规避模式"
            "（rule-5 PASS）"
        )
        # 不 return —— 继续执行 v2 inline sticky 顶部容器扩展扫描

    # 去重（同 class 多次命中只报一次代表样例）
    seen = set()
    unique_hits = []
    for h in hits:
        key = (h[0], h[1])
        if key not in seen:
            seen.add(key)
            unique_hits.append(h)

    msg_lines = [
        f"phone-frame / miniprogram-frame 内发现 {len(unique_hits)} 个自定义 sheet "
        f"class 规避模式（违反 §零.2 反例禁令 rule-5）："
    ]
    for frame_cls_text, evasive_class, snippet in unique_hits[:10]:  # 最多展示 10 条
        msg_lines.append(
            f"  • frame=`{frame_cls_text[:50]}` 自定义 class=`{evasive_class}` "
            f"附近: {snippet}"
        )
    if len(unique_hits) > 10:
        msg_lines.append(f"  ...（其余 {len(unique_hits) - 10} 条省略）")
    if hits:
        msg_lines.append(
            "修复方向：用标准结构 `<div class=\"fb-modal-overlay is-visible\">"
            "<div class=\"fb-modal\">…</div></div>` — sheet 形态由真源 fb-fallback.css "
            "L509-510 全自动适配,无需自行实现遮罩 + 贴底。详见 "
            "prd_expression_standard.md §零.2 状态帧表达约束第 5 条 + "
            "fb-fallback-manifest.md §3.2 Modal「移动端 Action Sheet 自动适配」。"
        )
        r.warn("\n".join(msg_lines))

    # ── S4-35 v2 扩展（2026-05-30 落地）：移动 frame 直接子层 inline sticky 顶部容器自由发挥拦截 ──
    # multi-select 实证：PM 在 phone-frame 用 inline `<div style="padding...">已选 N/M [退出]</div>` 实现
    # 多选态顶部工具栏（绕过 .fb-navbar 标准 7 variant）。
    # 治本：拦截移动 frame 直接子层 inline `position:sticky;top:0` 或非 fb-/proj- class 的"顶部容器"。
    # 详 rule_hard_constraints.md §S4-35 v2 ⑤自由发挥禁令 + manifest §3.12 v2。
    pat_inline_sticky_top = re.compile(
        r'<div\s+[^>]*style\s*=\s*"[^"]*position\s*:\s*sticky[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    pat_inline_top_zero = re.compile(
        r'<div\s+[^>]*style\s*=\s*"[^"]*\btop\s*:\s*0[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    inline_sticky_hits: list[tuple[int, str]] = []  # (lineno, snippet)
    for start, frame_cls_text in container_starts:
        # 限定扫描窗口：每个 mobile frame 起点向后 ~1500 字符（仅取"顶部"段，排除底部
        # action-bar 等场景；inline sticky 顶部容器若存在通常紧贴 phone-frame 开头）
        TOP_SCAN_WINDOW = 1500
        window = prd_html[start : start + TOP_SCAN_WINDOW]
        for pat in (pat_inline_sticky_top, pat_inline_top_zero):
            for m_div in pat.finditer(window):
                div_open = m_div.group(0)
                # 排除 .fb-navbar / .fb-action-bar / .fb-* / .proj-* 标准类
                cls_match = re.search(r'class\s*=\s*"([^"]*)"', div_open)
                if cls_match:
                    classes = cls_match.group(1).split()
                    if any(
                        c.startswith("fb-") or c.startswith("proj-")
                        for c in classes
                    ):
                        continue
                # 排除已被 .fb-* 包裹的内层 div（仅扫 phone-frame 直接子层）
                abs_pos = start + m_div.start()
                lineno = prd_html[:abs_pos].count("\n") + 1
                snippet = re.sub(r"\s+", " ", div_open)[:140]
                inline_sticky_hits.append((lineno, snippet))

    if inline_sticky_hits:
        # 去重（同行多次命中取一次）
        seen_lines = set()
        unique_inline = []
        for ln, sn in inline_sticky_hits:
            if ln not in seen_lines:
                seen_lines.add(ln)
                unique_inline.append((ln, sn))
        evasion_msg = [
            f"phone-frame / h5-frame / miniprogram-frame 内发现 {len(unique_inline)} 处 "
            f"inline sticky 顶部容器自由发挥（S4-35 v2 ⑤ 违规 — PM 应用 .fb-navbar + "
            f"data-variant 标准 variant，禁手写 inline 顶部 sticky 容器）："
        ]
        for ln, sn in unique_inline[:10]:
            evasion_msg.append(f"  • L{ln}: {sn}")
        if len(unique_inline) > 10:
            evasion_msg.append(f"  ...（其余 {len(unique_inline) - 10} 条省略）")
        evasion_msg.append(
            "修复方向：按业务场景选 .fb-navbar variant —— ① 多选态: "
            "<div class=\"fb-navbar\" data-variant=\"multi-select\"> + [取消][已选 N/M][全选] "
            "② 确认态: data-variant=\"confirm\" + [取消][title][确认] ③ 编辑态: "
            "data-variant=\"edit\" + [完成][title][···]。详 manifest §3.12 v2 + "
            "rule_hard_constraints.md §S4-35 v2 + proto_cross_platform.md §三 v2。"
        )
        r.warn("\n".join(evasion_msg))


# 组件变更清单 4 sub-section 期望 thead 字面（CHANGELOG_EXPECTED_HEADERS）
# SSOT 真源：`prd_expression_standard.md §11.1` + `proto_spec_md.md §八`
# 设计要点：
#   - 「新增」段：删了原「类型」列（与组件 ID 前缀 + sub-section 信息冗余）;
#     「触发原因」→「派生原因」（仅本段使用,语义更精确——SSOT #8 双触发条件)
#   - 「spec / prd 锚点」→「组件说明锚点」（命名更直观,锚点本来就指向 §7.1 集中容器)
CHANGELOG_EXPECTED_HEADERS = {
    "changelog-new": ["组件 ID", "派生原因", "使用页面", "组件说明锚点"],
    "changelog-update": ["组件 ID", "修改类型", "修改描述", "上一版本", "本版本", "影响页面"],
    "changelog-deprecated": ["组件 ID", "弃用版本", "弃用原因", "替代组件"],
    "changelog-promote": ["组件 ID", "建议原因", "当前使用项目数", "复用价值评估"],
}

# 禁用字面（旧表头名,应已升级)
CHANGELOG_FORBIDDEN_HEADERS = {
    "类型": "已删除冗余列(与组件 ID 前缀 + sub-section 信息重叠)",
    "触发原因": "已重命名为「派生原因」(语义更精确,仅新增段使用)",
    "spec / prd 锚点": "已重命名为「组件说明锚点」(锚点指向 §7.1 集中容器)",
    "使用模块": "已升级为「使用页面」(细粒度 M{XX}-P{YY},可点击跳转)",
    "影响模块": "已升级为「影响页面」(细粒度 M{XX}-P{YY},可点击跳转)",
}


def check_changelog_thead(prd_html: str, r: Report) -> None:
    """S4-26：组件变更清单 4 个 sub-section thead 字面规范化校验。

    SSOT 真源：`prd_expression_standard.md §11.1 Section 结构` +
              `proto_spec_md.md §八 格式 4 张子表表头定义`

    历史背景：组件变更清单字段优化前后存在不同版本表头:
        旧版:组件 ID | 类型 | 触发原因 | 使用模块 | spec / prd 锚点
        新版:组件 ID | 派生原因 | 使用页面 | 组件说明锚点
    本 check 强制 thead 字面与最新规范一致,防 Agent 沿用旧版表头漂移。

    校验对象:outputs/prd_*.html 中 <section id="component-changelog"> 内每个
    changelog-group(changelog-new / -update / -deprecated / -promote)的
    <thead><tr><th>...</th></tr></thead> 字面。

    无对应 group 静默豁免(本期某类无变更时 PRD 可能整段不渲染该 group)。

    机械化档:可机械化(thead 字面字符串严格 == 比对)。
    """
    r.section("组件变更清单 thead 字面规范化(§11.1 / §八,S4-26)")

    # 提取 component-changelog section
    m = re.search(
        r'<section[^>]*id\s*=\s*"component-changelog"[^>]*>(.*?)</section>',
        prd_html, re.DOTALL,
    )
    if not m:
        r.ok("PRD 中无 component-changelog section,跳过 thead 校验(豁免)")
        return

    section_body = m.group(1)

    # 提取每个 changelog-group 块 + 内部第一个 thead 的字面
    group_re = re.compile(
        r'<div\s+class\s*=\s*"changelog-group\s+(changelog-(?:new|update|deprecated|promote))[^"]*"'
        r'[^>]*>(.*?)(?=<div\s+class\s*=\s*"changelog-group|</section>|\Z)',
        re.DOTALL | re.IGNORECASE,
    )
    thead_re = re.compile(
        r'<thead[^>]*>.*?<tr[^>]*>(.*?)</tr>.*?</thead>', re.DOTALL
    )
    th_text_re = re.compile(r'<th[^>]*>(.*?)</th>', re.DOTALL)

    found_groups = []
    violations = []
    forbidden_hits = []

    for grp_m in group_re.finditer(section_body):
        grp_name = grp_m.group(1)
        grp_body = grp_m.group(2)
        thead_m = thead_re.search(grp_body)
        if not thead_m:
            continue  # 该 group 无 thead(可能写了占位"本期无 X 变更"),豁免
        th_cells = th_text_re.findall(thead_m.group(1))
        actual = [re.sub(r"<[^>]+>", "", th).strip() for th in th_cells]
        found_groups.append(grp_name)

        # 1. 检查禁用字面
        for forbidden, hint in CHANGELOG_FORBIDDEN_HEADERS.items():
            if forbidden in actual:
                forbidden_hits.append((grp_name, forbidden, hint))

        # 2. 检查与期望表头一致
        expected = CHANGELOG_EXPECTED_HEADERS.get(grp_name)
        if expected and actual != expected:
            violations.append((grp_name, actual, expected))

    if not found_groups:
        r.ok("PRD changelog section 内无含 thead 的 group(均为占位文本),豁免")
        return

    if not violations and not forbidden_hits:
        r.ok(
            f"changelog thead 全部合规({len(found_groups)} 个 group 命中)：" +
            ", ".join(found_groups)
        )
        return

    # 输出违规清单
    msgs = []
    if forbidden_hits:
        msgs.append(f"检测到 {len(forbidden_hits)} 处禁用旧表头字面（违反 §11.1 SSOT）：")
        for grp_name, forbidden, hint in forbidden_hits:
            msgs.append(f"  • {grp_name} 内 `{forbidden}` 列: {hint}")

    if violations:
        msgs.append(f"\n检测到 {len(violations)} 个 group thead 与规范不一致：")
        for grp_name, actual, expected in violations:
            msgs.append(f"  • {grp_name}:")
            msgs.append(f"    实际: {actual}")
            msgs.append(f"    期望: {expected}")

    msgs.append(
        "\n修复方向：按 `prd_expression_standard.md §11.1 Section 结构` 4 个 thead 字面统一,"
        "并跑 `assemble.py prd` 重生派生层(L2 真源升级后未重跑会保留旧表头)。"
    )
    r.fail("\n".join(msgs))


def check_z_index_compliance(prd_html: str, r: Report) -> None:
    """NB-WE-06 视觉一致性机械化(z-index 集合校验) — issue 2026-05-08。

    SSOT 真源：prd_expression_standard.md §零.1 全局 z-index 数值规范表
    合法数值集合：{300, 200, 150, 100, 60, 50, 41, 40, 10, 1}（300=Item 3 mermaid 全屏预览遮罩 Z-300；其余如 auto / 0 / inherit / initial 视为豁免）

    防漂移（NB-WE-06 第 5 要素,issue 2026-05-11_1925 加固）：
    每次跑本 check 时,_check_z_index_legal_set_drift 会反向解析 §零.1 真源表 + §零.2 协议得集合
    并与本地 legal_set 双向对账,不一致 → 显式 warn 漂移信号；根除"真源升级派生忘改"假阳性面。

    校验对象：outputs/prd HTML 中所有 `z-index: \\d+` 出现（inline style + <style> 块）
    历史教训：bujue-quotation-tool 历史出现 PM 给弹框写 z-index: 999/1000 盖住 sticky
    section-header（z-index: 200）→ 视觉漂移。本 check 强制数值在合法集合,防魔术数。
    """
    r.section("z-index 数值合规（NB-WE-06,SSOT §零.1）")

    # 提取所有 z-index: 数值 出现（带行号便于定位）
    # 真源：prd_expression_standard.md §零.1 表 10 行（Z-300/200/150/100/60/50/41/40/10/1；
    # Z-300=Item 3 2026-05-18 mermaid 全屏预览遮罩 .mmd-fs-overlay，高于 section-header）
    # 防漂移：本 legal_set 与真源运行时双向对账见 _check_z_index_legal_set_drift（NB-WE-06 第 5 要素 + NB-WE-18 自洽化）
    legal_set = {300, 200, 150, 100, 60, 50, 41, 40, 10, 1}
    _check_z_index_legal_set_drift(legal_set, r)
    illegal_occurrences: list[tuple[int, int, str]] = []  # (line_num, value, context)
    for m in re.finditer(r"z-index\s*:\s*(\d+)", prd_html):
        value = int(m.group(1))
        if value in legal_set:
            continue
        # 计算行号 + 提取上下文(本行)
        line_num = prd_html[:m.start()].count("\n") + 1
        line_start = prd_html.rfind("\n", 0, m.start()) + 1
        line_end = prd_html.find("\n", m.end())
        if line_end == -1:
            line_end = len(prd_html)
        context = prd_html[line_start:line_end].strip()
        if len(context) > 100:
            context = context[:100] + "..."
        illegal_occurrences.append((line_num, value, context))

    # 运行时格式化合法集合字面（避免硬编码字面与 legal_set 双源漂移）
    legal_repr = "{" + ", ".join(str(v) for v in sorted(legal_set)) + "}"
    legal_z_labels = " / ".join(f"Z-{v}" for v in sorted(legal_set, reverse=True))

    if not illegal_occurrences:
        # 统计合法值出现次数（确保有数据,不只是空文档）
        legal_count = sum(1 for m in re.finditer(r"z-index\s*:\s*\d+", prd_html))
        if legal_count == 0:
            r.ok("PRD 中未出现任何 z-index 数值（无需核查）")
        else:
            r.ok(f"PRD 中全部 z-index 数值 ⊂ §零.1 合法集合 {legal_repr}（{legal_count} 处）")
        return

    r.fail(
        f"PRD 中 {len(illegal_occurrences)} 处 z-index 数值不在 §零.1 合法集合 "
        f"{legal_repr}：" +
        "\n  ".join(
            f"line {ln}: z-index: {v} | 上下文: {ctx}"
            for ln, v, ctx in illegal_occurrences[:10]
        ) + (f"\n  （共 {len(illegal_occurrences)} 处,仅显示前 10 条）" if len(illegal_occurrences) > 10 else "")
        + f"\n修复方向：从 prd_expression_standard.md §零.1 全局 z-index 数值表选取合法值（{legal_z_labels}）；新需求的数值需通过 /retro 修订真源表"
    )


# ── 校验 4.2｜视觉一致性机械化剩余 2 维度 NB-WE-10 ──────────────────────────
#
# NB-WE-06 z-index 已机械化（commit f164cc5）,本节补 NB-WE-10 剩余 2 维度。
#
# 维度 A — 同状态名跨帧元数据字面一致（prd.html）：
#   同 page 的多个 state frame 间, page 元数据字面必须一致。
#   prd.html 中每个 `<section id="H-M{NN}-P{NN}-{state}">` 内含 4 个 page 元数据 span:
#     - <span class="page-id">M{NN} / P{NN}</span>
#     - <span class="page-name">{页面名称}</span>
#     - <span class="role-tag">视角：{角色}</span>
#     - <span class="func-tag">路由：{路由}</span>
#   PM 历史踩坑：在 default frame 写"项目列表"另 frame 写"项目列表（销售）"漂移。
#
# 维度 B — 同字段格式跨页字面 normalize（spec.md）：
#   spec.md 各页 §数据字段绑定表中,同 field_id 在多页出现时,
#   「数据类型」+「约束」列字面应一致（PM 在 P01 写 `string | required, max=500`,
#   在 P03 写 `string | optional, max=600` 是 SSOT 漂移）。

PAGE_META_TAGS = ("page-id", "page-name", "role-tag", "func-tag")


def check_frame_page_metadata_consistency(prd_html: str, r: Report) -> None:
    """NB-WE-10 维度 A — 同 page 多 frame 间 page 元数据字面一致性校验。"""
    r.section("视觉一致性 — 同 page 跨 frame 元数据字面一致性（NB-WE-10 维度 A）")

    section_re = re.compile(
        r'<section\s+id="(H-M\d+-P\d+-[\w-]+)"[^>]*>(.*?)</section>',
        re.DOTALL,
    )

    # page_key (M01-P01) → state_name → {tag: text}
    page_frames: dict[str, dict[str, dict[str, str]]] = {}

    page_id_re = re.compile(r'^H-(M\d+-P\d+)-(.+)$')

    for m in section_re.finditer(prd_html):
        prd_id = m.group(1)
        body = m.group(2)
        pm = page_id_re.match(prd_id)
        if not pm:
            continue
        page_key = pm.group(1)
        state_name = pm.group(2)

        meta: dict[str, str] = {}
        for tag in PAGE_META_TAGS:
            tag_re = re.compile(
                rf'<span\s+class="{re.escape(tag)}"[^>]*>(.*?)</span>',
                re.DOTALL,
            )
            tag_m = tag_re.search(body)
            if tag_m:
                meta[tag] = re.sub(r"\s+", " ", tag_m.group(1)).strip()

        page_frames.setdefault(page_key, {})[state_name] = meta

    drift_reports: list[str] = []
    pages_checked = 0
    for page_key, frames in page_frames.items():
        if len(frames) < 2:
            continue
        pages_checked += 1
        for tag in PAGE_META_TAGS:
            seen: dict[str, list[str]] = {}
            for state, meta in frames.items():
                if tag not in meta:
                    continue
                seen.setdefault(meta[tag], []).append(state)
            if len(seen) > 1:
                detail = " | ".join(
                    f"{val!r}@{','.join(states)}"
                    for val, states in seen.items()
                )
                drift_reports.append(f"[{page_key}] {tag} 跨 frame 漂移: {detail}")

    if drift_reports:
        # WARN（非 FAIL）— 部分场景业务合理（如 no-permission frame 仅 role-1 可见，
        # 与其他 frame 的"role-1 / role-2"字面不同但合理）。机械检查无法区分,留 PM/Supervisor 人审兜底。
        r.warn(
            f"prd.html 同 page 跨 frame 元数据字面漂移（共 {len(drift_reports)} 处，需人工核查是否业务合理）：\n  "
            + "\n  ".join(drift_reports[:10])
            + (f"\n  （共 {len(drift_reports)} 处,仅显示前 10 条）" if len(drift_reports) > 10 else "")
        )
    elif pages_checked == 0:
        r.warn("未发现同 page 多 frame 场景（每 page 仅 1 个 state frame 时跳过）")
    else:
        r.ok(f"同 page 跨 frame 元数据字面一致（{pages_checked} 个多帧 page 检查通过）")


FIELD_BIND_ROW_RE = re.compile(
    r"^\|\s*([a-zA-Z_][\w]*)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
)


def _normalize_format_cell(s: str) -> str:
    """字段格式 normalize: 去多余空白 + 内部 token 排序（容忍 `required, max=500` vs `max=500, required`）。"""
    s = s.strip()
    tokens = [t.strip() for t in re.split(r",\s*", s) if t.strip()]
    return ", ".join(sorted(tokens))


def check_field_format_consistency_across_pages(spec_md: str, r: Report) -> None:
    """NB-WE-10 维度 B — spec 各页字段绑定表同 field_id 的「数据类型 + 约束」字面一致。"""
    r.section("视觉一致性 — spec 同字段跨页格式 normalize 一致性（NB-WE-10 维度 B）")

    page_section_re = re.compile(r"\n###?\s+P-", re.MULTILINE)
    starts = [m.start() + 1 for m in page_section_re.finditer(spec_md)]
    if not starts:
        starts = [0]

    sections: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(spec_md)
        sections.append(spec_md[start:end])

    field_records: dict[str, list[tuple[str, str, str, int]]] = {}

    for idx, section_text in enumerate(sections, start=1):
        for row in FIELD_BIND_ROW_RE.finditer(section_text):
            field_id = row.group(1)
            if field_id.lower() in ("field", "id", "字段"):
                continue
            data_type = row.group(3).strip()
            constraint = row.group(4).strip()
            normalized_constraint = _normalize_format_cell(constraint)
            field_records.setdefault(field_id, []).append(
                (data_type, normalized_constraint, constraint, idx)
            )

    drift_reports: list[str] = []
    fields_with_multi_pages = 0
    for field_id, records in field_records.items():
        if len(records) < 2:
            continue
        fields_with_multi_pages += 1
        type_set = {r_[0] for r_ in records}
        constraint_set = {r_[1] for r_ in records}
        if len(type_set) > 1:
            drift_reports.append(
                f"[{field_id}] 数据类型跨页漂移: " + " | ".join(
                    f"{r_[0]!r}@page{r_[3]}" for r_ in records
                )
            )
        if len(constraint_set) > 1:
            drift_reports.append(
                f"[{field_id}] 约束跨页漂移: " + " | ".join(
                    f"{r_[2]!r}@page{r_[3]}" for r_ in records
                )
            )

    if drift_reports:
        # WARN（非 FAIL）— 部分场景合理（同字段在不同业务上下文下约束变化、
        # 「来源 §9」引用 F-XXX 编号在不同页指向不同功能业务点）。
        # 机械检查抓"同字段疑似漂移",但合理性留 PM/Supervisor 人审。
        r.warn(
            f"spec 同 field_id 跨页格式疑似漂移（共 {len(drift_reports)} 处，需人工核查是否合理）：\n  "
            + "\n  ".join(drift_reports[:10])
            + (f"\n  （共 {len(drift_reports)} 处,仅显示前 10 条）" if len(drift_reports) > 10 else "")
        )
    elif fields_with_multi_pages == 0:
        r.warn("未发现跨页字段（每字段仅在单页绑定时跳过）")
    else:
        r.ok(
            f"spec 同字段跨页格式一致（{fields_with_multi_pages} 个跨页字段 normalize 后字面对齐）"
        )


def check_proj_index(data: dict, r: Report) -> None:
    """components_[产品]_latest.md 索引段一致性。"""
    r.section("proj 组件索引段一致性")

    product = data.get("product", "").strip()
    components_path = OUTPUT_DIR / f"components_{product}_latest.md"

    if not components_path.exists():
        r.ok("无 proj 索引段需核查（components 文件不存在）")
        return

    md = components_path.read_text(encoding="utf-8")

    # —— 空白文件强警告（防 Step 2.5 漏跑被旧规范分支静默吞掉）——
    proj_decls = re.findall(r"\bproj\.L\d+\.[\w-]+", md)
    if len(md.strip()) < 200 and not proj_decls and not re.search(r"^### [ABCD]\.", md, re.MULTILINE):
        r.fail(
            f"components_{product}_latest.md 内容长度仅 {len(md.strip())} 字符 + 无任何 proj.* 声明 + 无索引段表头——"
            "可能 Step 2.5「项目组件识别 Agent」未实际执行或产出为空骨架。"
            "若本期确无 proj 组件，须按 proj_component_protocol.md §二.1 写入 A/B/C/D 4 张表（含'本期无 proj 组件'兜底说明）"
        )
        return

    # —— 检测是否为新规范（v1.1+，含 §二.1 索引段）——
    # 标志：含至少一个 "### A.", "### B.", "### C.", "### D." 子标题之一
    has_new_format = bool(re.search(r"^### [ABCD]\.", md, re.MULTILINE))
    if not has_new_format:
        # 旧规范文件（无索引段），降级为警告并跳过
        r.warn(
            f"components_{product}_latest.md 为旧规范格式（缺索引段 §二.1）。"
            "建议升级到 v1.1：在文件顶部补加 A/B/C/D 4 张表"
            "（详见 proj_component_protocol.md §二.1）"
        )
        return

    # —— 提取 4 张表段落 ——
    def extract_section(label: str) -> str:
        # 支持以下一个 ### 或 ## 作为终止
        pattern = rf"### {re.escape(label)}\..*?(?=^### [A-Z]\.|^## )"
        match = re.search(pattern, md, re.DOTALL | re.MULTILINE)
        return match.group(0) if match else ""

    a_section = extract_section("A")
    b_section = extract_section("B")
    c_section = extract_section("C")
    d_section = extract_section("D")

    if not a_section:
        r.fail("索引段缺少 A. active 表（§二.1）")
        return

    # —— 表格 ID 字面规范 fail loud（参 proj_component_protocol.md §二.1 顶部规则）——
    # 表格首列 / 替代组件列 / 模块列内禁反引号包裹 ID,避免行首锚定 regex 静默漏检
    backtick_in_table_re = re.compile(r"^\|[^|\n]*`proj\.L\d+\.[\w-]+`", re.MULTILINE)
    bt_offenders: list[str] = []
    for label, sec in (("A", a_section), ("B", b_section), ("C", c_section), ("D", d_section)):
        if sec and backtick_in_table_re.search(sec):
            bt_offenders.append(label)
    if bt_offenders:
        r.fail(
            f"§二.1 索引段 {'/'.join(bt_offenders)} 表内出现反引号包裹的 proj id（如 `proj.L1.x`）。"
            "按 proj_component_protocol.md §二.1 表格 ID 字面规则,表格首列/替代组件列/模块列须裸写,"
            "否则行首锚定 regex 静默漏检。请去掉反引号(narrative inline 引用不受此约束)"
        )
        return

    # 仅取表格行首列（防止"替代组件"列重复算入）
    row_id_re = re.compile(r"^\|\s*(proj\.L\d+\.[\w-]+)\s*\|", re.MULTILINE)
    a_ids = set(row_id_re.findall(a_section))
    b_ids = set(row_id_re.findall(b_section)) if b_section else set()

    # 详情段（YAML 块）中声明的 proj id
    detail_ids = {c["id"] for c in parse_proj_components(md)}

    # —— 1. A 表 id 与详情段一一对应（B 表的也要在详情段保留）——
    expected_detail = a_ids | b_ids
    missing_in_detail = expected_detail - detail_ids
    extra_in_detail = detail_ids - expected_detail
    if missing_in_detail:
        r.fail(f"索引 A/B 表列入但详情段未声明：{sorted(missing_in_detail)}")
    if extra_in_detail:
        r.fail(f"详情段声明但索引 A/B 表未列入：{sorted(extra_in_detail)}")
    if not missing_in_detail and not extra_in_detail and (a_ids or b_ids):
        r.ok(f"索引 A/B 表与详情段一一对应（A {len(a_ids)} + B {len(b_ids)}）")
    elif not (a_ids or b_ids) and not detail_ids:
        r.ok("索引段与详情段一致：本期无 proj 组件")

    # —— 2. B 表 deprecated 替代组件必须在 A 表 ——
    # 行格式：| <id> | <reason> | <replacement> | <date> |
    if b_section:
        b_rows = re.findall(
            r"^\|\s*(proj\.L\d+\.[\w-]+)\s*\|[^|]*\|\s*(proj\.L\d+\.[\w-]+)\s*\|",
            b_section, re.MULTILINE,
        )
        bad_replacements = [
            (dep, repl) for dep, repl in b_rows if repl not in a_ids
        ]
        if bad_replacements:
            r.fail(
                f"B 表 deprecated 条目的替代组件不在 A 表："
                f"{[(d, r_) for d, r_ in bad_replacements]}"
            )
        elif b_rows:
            r.ok(f"B 表 deprecated 替代组件全部在 A 表（{len(b_rows)} 条）")

    # —— 3. D 表模块列与 scaffold.json 一致（id + name 双向校验）——
    scaffold_modules = [
        (m.get("id", ""), m.get("name", "").strip())
        for m in data.get("modules", []) if isinstance(m, dict)
    ]
    scaffold_module_ids = {mid for mid, _ in scaffold_modules}
    scaffold_name_by_id = {mid: name for mid, name in scaffold_modules}

    if d_section:
        # 抓 D 表行：| M02 商品列表 | proj.L3.product-card |
        d_row_re = re.compile(r"^\|\s*(M\d{2})(?:\s+([^|]+?))?\s*\|", re.MULTILINE)
        d_rows: list[tuple[str, str]] = [
            (m.group(1), (m.group(2) or "").strip())
            for m in d_row_re.finditer(d_section)
        ]
        d_module_ids = {mid for mid, _ in d_rows}

        missing_in_d = scaffold_module_ids - d_module_ids
        extra_in_d = d_module_ids - scaffold_module_ids
        if missing_in_d:
            r.fail(f"D 表缺少 scaffold.json 中的模块：{sorted(missing_in_d)}")
        if extra_in_d:
            r.fail(f"D 表含 scaffold.json 中不存在的模块：{sorted(extra_in_d)}")
        if not missing_in_d and not extra_in_d and scaffold_module_ids:
            r.ok(f"D 表模块清单与 scaffold.json 一致（{len(scaffold_module_ids)} 个模块）")

        # A4: 模块名同步校验
        name_mismatches: list[str] = []
        for mid, dname in d_rows:
            if mid not in scaffold_name_by_id:
                continue
            scaffold_name = scaffold_name_by_id[mid]
            if not scaffold_name:
                continue
            if dname and dname != scaffold_name:
                name_mismatches.append(f"{mid}: D 表名'{dname}' ≠ scaffold 名'{scaffold_name}'")
        if name_mismatches:
            r.fail(
                "D 表模块名与 scaffold.json modules[].name 不一致："
                + "; ".join(name_mismatches[:5])
                + ("..." if len(name_mismatches) > 5 else "")
            )
        elif d_rows:
            r.ok("D 表模块名与 scaffold.json modules[].name 一致")
    else:
        r.fail("索引段缺少 D 表（按模块反查）")

    # —— 4. D 表引用的 proj 组件必须存在于 A 表 ——
    if d_section:
        d_referenced_ids = set(re.findall(r"\bproj\.L\d+\.[\w-]+", d_section))
        bad_d_refs = d_referenced_ids - a_ids
        if bad_d_refs:
            r.fail(f"D 表引用了 A 表不存在的 proj 组件：{sorted(bad_d_refs)}")
        elif d_referenced_ids:
            r.ok(f"D 表引用 proj 组件全部在 A 表（{len(d_referenced_ids)} 个）")

    # —— 5. A 表 owner 列校验 + 草稿 PROJ-CSS 归属唯一 ——
    check_proj_owner(data, a_section, a_ids, r)


# ── 校验 5.1｜A 表 owner 列与草稿 PROJ-CSS 归属 ──────────────────────────────

A_TABLE_ROW_RE = re.compile(
    r"^\|\s*(proj\.L\d+\.[\w-]+)\s*\|"      # id
    r"\s*([^|]+?)\s*\|"                       # 模块列
    r"\s*([^|]+?)\s*\|",                      # owner 列
    re.MULTILINE,
)
DRAFTS_DIR = REPO_ROOT / "process_record" / "drafts"
PROJ_CSS_BLOCK_RE = re.compile(
    r"<!--\s*\[PROJ-CSS-START\]\s*-->(.*?)<!--\s*\[PROJ-CSS-END\]\s*-->",
    re.DOTALL,
)


def parse_a_table_owners(a_section: str) -> dict[str, dict[str, str]]:
    """解析 A 表行，返回 {proj_id: {modules_raw, owner}}。
    跳过表头/分隔行（owner 列含「---」或「owner」字样的行）。"""
    rows: dict[str, dict[str, str]] = {}
    for m in A_TABLE_ROW_RE.finditer(a_section):
        proj_id, modules_raw, owner_raw = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if owner_raw.lower() in {"owner", "---"} or set(owner_raw) <= {"-"}:
            continue
        rows[proj_id] = {"modules_raw": modules_raw, "owner": owner_raw}
    return rows


def check_proj_owner(
    data: dict, a_section: str, a_ids: set[str], r: Report
) -> None:
    """A 表 owner 列校验 + 草稿 PROJ-CSS 块归属唯一。"""
    if not a_ids:
        return  # 本期无 proj 组件，无 owner 可验

    # 头部表头容易被解析为一行（id 列匹配 proj.L 失败而被跳过），所以正则不会误捕表头
    rows = parse_a_table_owners(a_section)
    scaffold_module_ids_ordered = [
        m.get("id", "") for m in data.get("modules", []) if isinstance(m, dict)
    ]
    scaffold_id_set = set(scaffold_module_ids_ordered)

    owner_field_ok = owner_in_modules_ok = owner_first_ok = True
    expected_owner_by_id: dict[str, str] = {}

    for proj_id in sorted(a_ids):
        row = rows.get(proj_id)
        if row is None or not row["owner"]:
            r.fail(f"A 表 [{proj_id}] 缺少 owner 列或值为空")
            owner_field_ok = False
            continue

        owner = row["owner"]
        # 解析"模块"列（支持 / , 、 空格 多种分隔）
        ref_modules_raw = re.split(r"[/,、\s]+", row["modules_raw"])
        ref_modules = [m for m in ref_modules_raw if MODULE_ID_RE.match(m)]

        if owner not in ref_modules:
            r.fail(
                f"A 表 [{proj_id}] owner={owner!r} 不在同行「模块」列声明的模块集合 {ref_modules} 中"
            )
            owner_in_modules_ok = False
            continue

        # 校验 owner 必须是 scaffold.json modules 顺序最靠前的引用者
        first_ref = next((mid for mid in scaffold_module_ids_ordered if mid in ref_modules), None)
        if first_ref is None:
            r.fail(
                f"A 表 [{proj_id}] 模块列 {ref_modules} 与 scaffold.json modules 无交集"
            )
            owner_first_ok = False
            continue
        if owner != first_ref:
            r.fail(
                f"A 表 [{proj_id}] owner={owner!r} 不是 scaffold.json modules 中"
                f"顺序最靠前的引用模块（应为 {first_ref!r}）"
            )
            owner_first_ok = False
            continue

        # 顺便校验 ref_modules 全部在 scaffold
        unknown_refs = [m for m in ref_modules if m not in scaffold_id_set]
        if unknown_refs:
            r.fail(f"A 表 [{proj_id}] 模块列含 scaffold.json 未声明的模块：{unknown_refs}")
            owner_first_ok = False
            continue

        expected_owner_by_id[proj_id] = owner

    if owner_field_ok and a_ids:
        r.ok(f"A 表 owner 列存在性（{len(a_ids)} 个组件）")
    if owner_in_modules_ok and a_ids:
        r.ok("A 表 owner ∈ 模块列")
    if owner_first_ok and a_ids:
        r.ok("A 表 owner = scaffold.json modules 顺序最靠前的引用者")

    # SSOT #16 NB-WE-D2：A 表 owner ↔ scaffold.owner_assignments 双向同步校验
    # 防 PM 子阶段二.5 在 A 表重算 owner 与 scaffold.owner_assignments 字面值漂移
    scaffold_owner_by_proj: dict[str, str] = {}
    for mod in data.get("modules", []):
        if not isinstance(mod, dict):
            continue
        for proj_id, _owner_module_id in mod.get("owner_assignments", {}).items():
            scaffold_owner_by_proj[proj_id] = mod.get("id", "?")
    sync_ok = True
    for proj_id, a_table_owner in expected_owner_by_id.items():
        scaffold_owner = scaffold_owner_by_proj.get(proj_id)
        if scaffold_owner is None:
            r.fail(
                f"A 表 [{proj_id}] 含 owner={a_table_owner!r}, 但 scaffold.json 中"
                f"无任何模块在 owner_assignments 声明该 proj_id（违反 SSOT #16 双向同步）"
            )
            sync_ok = False
        elif scaffold_owner != a_table_owner:
            r.fail(
                f"A 表 [{proj_id}] owner={a_table_owner!r} 与 scaffold.json 中声明的"
                f"owner 模块={scaffold_owner!r} 不一致（违反 SSOT #16 双向同步;"
                f"调整方向：scaffold.json 是真源,改 A 表为 {scaffold_owner!r}）"
            )
            sync_ok = False
    if sync_ok and expected_owner_by_id:
        r.ok(f"A 表 owner ↔ scaffold.owner_assignments 双向同步（{len(expected_owner_by_id)} proj）")

    # —— 草稿 PROJ-CSS 块归属唯一 ——
    if not DRAFTS_DIR.exists() or not expected_owner_by_id:
        return

    css_owner_ok = True
    # 收集每个 proj 的 .proj-{name} selector → 出现在哪些模块草稿
    selectors_by_proj: dict[str, str] = {}  # proj_id -> base CSS selector
    for proj_id, owner in expected_owner_by_id.items():
        name_match = re.match(r"proj\.L\d+\.([\w-]+)", proj_id)
        if name_match:
            selectors_by_proj[proj_id] = f".proj-{name_match.group(1)}"

    for draft_path in sorted(DRAFTS_DIR.glob("prd_M*_draft.html")):
        # 提取模块 id（M01, M02 ...）
        mod_match = re.match(r"prd_(M\d{2})_draft\.html", draft_path.name)
        if not mod_match:
            continue
        draft_module = mod_match.group(1)
        text = draft_path.read_text(encoding="utf-8")
        # 提取 PROJ-CSS 块
        css_blocks = PROJ_CSS_BLOCK_RE.findall(text)
        if not css_blocks:
            continue
        joined_css = "\n".join(css_blocks)

        for proj_id, base_selector in selectors_by_proj.items():
            owner = expected_owner_by_id[proj_id]
            if base_selector not in joined_css:
                continue
            if draft_module != owner:
                r.fail(
                    f"草稿 [{draft_path.name}] 含 [{proj_id}] 的 PROJ-CSS（selector {base_selector}），"
                    f"但 owner 为 {owner}（非本模块）。非 owner 模块禁止写本组件 CSS。"
                )
                css_owner_ok = False

    if css_owner_ok:
        r.ok("草稿 PROJ-CSS 块归属与 A 表 owner 一致")

    # —— A3: 拼装后 prd.html PROJ-CSS 注入区 selector 唯一性 ——
    check_proj_css_selector_unique(data, r)


PROJ_CSS_INJECT_RE = re.compile(
    r"/\*\s*===\s*\[PROJ-CSS-START\][^*]*\*/(.*?)/\*\s*===\s*\[PROJ-CSS-END\]\s*===\s*\*/",
    re.DOTALL,
)
PROJ_SELECTOR_RE = re.compile(r"^\s*(\.proj-[\w-]+(?:\.is-[\w-]+)?)\s*\{", re.MULTILINE)


# ── 校验 5.2｜S4-27 派生模块引用 owner proj 组件内部 slot class 完整性 ──────
# SSOT 双锚 #37 机械兜底（NB-WE-32 实装，issue # 8 复盘）
# 算法：owner draft 的 PROJ-CSS 中若为 .proj-XXX 定义了 slot class（.proj-XXX .{prefix}-{name}），
#       则派生模块（非 owner）在引用该 proj 容器时,内部应至少含 1 个 slot class;
#       若派生容器内 0 个 slot class + ≥ 2 个 fb-tag → WARN(疑似 fb-tag 平铺替代 slot)


def check_proj_slot_class_completeness(data: dict, r: Report) -> None:
    """S4-27：派生模块引用 owner proj 组件时,内部 slot class 完整性。

    SSOT 双锚 #37 机械兜底(NB-WE-32 实装,issue # 8 复盘根因防御)。

    算法:
    1. 从 scaffold.owner_assignments 推算 {proj_id: owner_module}
    2. 对每个 proj,Read owner draft 的 PROJ-CSS 块,
       grep `.proj-{suffix}(?:.is-XXX)? .{prefix}-{name}` 提取 slot class 名集合
    3. 对每个派生模块(非 owner)的 draft,grep `class="...proj-{suffix}..."` 找容器位置,
       30 行滑动窗口内扫 slot class 数 vs fb-tag 数 + 提取可视文本长度
    4. 判定(v2 双分支,NB-WE-33 增强):
       - 分支 v1:slot=0 且 fb-tag>=2 → WARN(疑似 fb-tag 平铺替代 slot)
       - 分支 v2:slot=0 且 fb-tag=0 且 可视文本长度>=K(K=20) → WARN(疑似完全退化为单行字面)
    """
    r.section("派生模块引用 owner proj 组件内部 slot class 完整性(SSOT 双锚 #37, S4-27)")

    # 1. owner 推算（从 scaffold.owner_assignments）
    owner_by_proj: dict[str, str] = {}
    for mod in data.get("modules", []):
        if not isinstance(mod, dict):
            continue
        for proj_id in mod.get("owner_assignments", {}):
            owner_by_proj[proj_id] = mod.get("id", "?")

    if not owner_by_proj:
        r.warn("scaffold.owner_assignments 为空,跳过 slot class 完整性检查")
        return

    if not DRAFTS_DIR.exists():
        r.warn(f"drafts 目录不存在({DRAFTS_DIR}),跳过 slot class 完整性检查")
        return

    # 2. 提取每个 proj 的 owner-defined slot class 集合
    proj_slot_classes: dict[str, set[str]] = {}
    proj_base_class: dict[str, str] = {}
    owners_with_slots: int = 0

    for proj_id, owner_mid in owner_by_proj.items():
        name_match = re.match(r"proj\.L\d+\.([\w-]+)", proj_id)
        if not name_match:
            continue
        base_suffix = name_match.group(1)
        proj_base_class[proj_id] = f"proj-{base_suffix}"

        owner_draft = DRAFTS_DIR / f"prd_{owner_mid}_draft.html"
        if not owner_draft.exists():
            continue
        owner_text = owner_draft.read_text(encoding="utf-8")
        css_blocks = PROJ_CSS_BLOCK_RE.findall(owner_text)
        if not css_blocks:
            continue
        joined_css = "\n".join(css_blocks)

        # 匹配 .proj-{base_suffix}(.is-XXX)? .{prefix}-{name}
        slot_re = re.compile(
            rf"\.proj-{re.escape(base_suffix)}(?:\.is-[\w-]+)?\s+\.([a-z]+-[\w-]+)",
        )
        slots: set[str] = set()
        for m in slot_re.finditer(joined_css):
            slot_name = m.group(1)
            # 排除 is-* state modifier(误判) / proj-* 嵌套(罕见) / fb-* 通用引用
            if slot_name.startswith("is-") or slot_name.startswith("proj-") or slot_name.startswith("fb-"):
                continue
            slots.add(slot_name)
        if slots:
            owners_with_slots += 1
        proj_slot_classes[proj_id] = slots

    # 3. 扫派生 draft
    WINDOW_LINES = 30
    LITERAL_TEXT_K = 20  # v2 增强(NB-WE-33):可视文本长度阈值
    violations: list[str] = []

    for draft_path in sorted(DRAFTS_DIR.glob("prd_M*_draft.html")):
        mod_match = re.match(r"prd_(M\d{2})_draft\.html", draft_path.name)
        if not mod_match:
            continue
        draft_module = mod_match.group(1)
        text = draft_path.read_text(encoding="utf-8")
        lines = text.split("\n")

        for proj_id, owner_mid in owner_by_proj.items():
            if draft_module == owner_mid:
                continue  # owner 自身不审(它就是真源)
            slots = proj_slot_classes.get(proj_id, set())
            if not slots:
                continue  # owner 未定义 slot class,无法判定该 proj
            base_cls = proj_base_class[proj_id]

            container_re = re.compile(rf'class="[^"]*\b{re.escape(base_cls)}\b[^"]*"')
            for idx, line in enumerate(lines):
                if not container_re.search(line):
                    continue
                window = "\n".join(lines[idx:idx + WINDOW_LINES])
                slot_count = 0
                for slot_name in slots:
                    slot_count += len(
                        re.findall(rf'class="[^"]*\b{re.escape(slot_name)}\b[^"]*"', window)
                    )
                fb_tag_count = len(re.findall(r'class="[^"]*\bbj-tag\b[^"]*"', window))

                if slot_count == 0 and fb_tag_count >= 2:
                    # 分支 v1:fb-tag 平铺替代 slot
                    violations.append(
                        f"  - [{draft_path.name}:{idx + 1}] proj 容器 .{base_cls} 内部 0 个 "
                        f"owner({owner_mid}) 定义的 slot class，但含 {fb_tag_count} 个 fb-tag"
                        f"(疑似平铺替代 slot;详 proj_component_protocol.md §5.1 派生模块引用 owner 组件的内部结构规则)"
                    )
                elif slot_count == 0 and fb_tag_count == 0:
                    # 分支 v2(NB-WE-33):容器内可能完全退化为单行字面文本
                    # 取容器开标签行 + 后续 5 行作为容器近似边界
                    container_window = "\n".join(lines[idx:idx + 6])
                    # 去除从容器开标签到首个 > 之间的属性(避免 data-component-id 等长属性误判)
                    container_close = lines[idx].find(">")
                    if container_close >= 0:
                        tail = lines[idx][container_close + 1:]
                        rest = "\n".join(lines[idx + 1:idx + 6])
                        approx_inner = tail + "\n" + rest
                    else:
                        approx_inner = container_window
                    # 去剩余 HTML tag,保留可视文本
                    visible_text = re.sub(r"<[^>]+>", "", approx_inner)
                    visible_text = re.sub(r"\s+", " ", visible_text).strip()
                    if len(visible_text) >= LITERAL_TEXT_K:
                        preview = visible_text[:60] + ("..." if len(visible_text) > 60 else "")
                        violations.append(
                            f"  - [{draft_path.name}:{idx + 1}] proj 容器 .{base_cls} 内部 0 slot + 0 fb-tag,"
                            f"但含 {len(visible_text)} 字符可视文本(疑似完全退化为单行字面替代 slot 结构):"
                            f'「{preview}」;详 proj_component_protocol.md §5.1'
                        )

    if violations:
        r.warn(
            f"派生模块用 fb-tag 平铺替代 owner 专用 slot class — {len(violations)} 处疑似违规"
            f"(详 proj_component_protocol.md §5.1):"
        )
        for v in violations[:20]:
            r.warn(v)
        if len(violations) > 20:
            r.warn(f"  ...(还有 {len(violations) - 20} 处未显示)")
    else:
        r.ok(
            f"派生模块 slot class 完整性合规({len(owner_by_proj)} proj 组件;"
            f"{owners_with_slots} 个 owner 含 slot class 定义参与本次扫描)"
        )


def check_proj_css_selector_unique(data: dict, r: Report) -> None:
    """A3：prd.html 的 PROJ-CSS 注入区内任一 selector 不得重复声明。"""
    product = data.get("product", "").strip()
    prd_path = OUTPUT_DIR / f"prd_{product}_latest.html"
    if not prd_path.exists():
        return
    html = prd_path.read_text(encoding="utf-8")
    block_match = PROJ_CSS_INJECT_RE.search(html)
    if not block_match:
        # 模板缺占位 = 模板退化（assemble.py prd 应已拦截，此处兜底）
        # 与 assemble.py inject_proj_css 的 ERROR 路径配对，避免 prd.html 被手改后静默放过
        r.fail(
            "prd.html 缺 PROJ-CSS 注入区占位（/* === [PROJ-CSS-START] === */ ... "
            "/* === [PROJ-CSS-END] === */）；owner 模块草稿的 PROJ-CSS 可能被 assemble 静默丢弃，"
            "或 prd.html 被手改。请恢复 prd_template.html 占位并重跑 assemble.py prd"
        )
        return
    block = block_match.group(1)
    counts: dict[str, int] = {}
    for sel in PROJ_SELECTOR_RE.findall(block):
        counts[sel] = counts.get(sel, 0) + 1
    dupes = sorted(s for s, n in counts.items() if n > 1)
    if dupes:
        r.fail(
            f"prd.html PROJ-CSS 注入区检测到重复 selector：{dupes}（违反 proj_component_protocol §五.1：owner 写完整 CSS，非 owner 只引用 class）"
        )
    elif counts:
        r.ok(f"PROJ-CSS 注入区 selector 唯一（{len(counts)} 个）")


# ── 校验 6.5｜S4-22 组件变更清单一致性（spec §八 ↔ prd #component-changelog）──

CHANGELOG_CATEGORIES = ["新增", "修改", "弃用", "建议升级"]
CATEGORY_TO_PRD_CLASS = {
    "新增": "new",
    "修改": "update",
    "弃用": "deprecated",
    "建议升级": "promote",
}
PRD_CLASS_TO_CATEGORY = {v: k for k, v in CATEGORY_TO_PRD_CLASS.items()}

CHANGELOG_SPEC_HEAD_RE = re.compile(r"^## 组件变更清单\s*$", re.MULTILINE)
CHANGELOG_SPEC_NEXT_H2_RE = re.compile(r"^## ", re.MULTILINE)
CHANGELOG_SPEC_SUB_RE = re.compile(r"^### (新增|修改|弃用|建议升级)[^\n]*", re.MULTILINE)
CHANGELOG_SPEC_TABLE_PROJ_RE = re.compile(r"\b(proj\.L\d+\.[\w-]+)")
CHANGELOG_SPEC_PLACEHOLDER_RE = re.compile(r"本期无 proj 组件变更")

CHANGELOG_PRD_SECTION_RE = re.compile(
    r'<section\s+id="component-changelog"[^>]*>(.*?)</section>',
    re.DOTALL,
)
CHANGELOG_PRD_GROUP_ANCHOR_RE = re.compile(r'changelog-(new|update|deprecated|promote)')
CHANGELOG_PRD_PROJ_RE = re.compile(r'<code>(proj\.L\d+\.[\w-]+)</code>')


def parse_spec_changelog(spec_md: str) -> dict | None:
    """解析 spec.md §八 组件变更清单。
    返回 {"placeholder": bool, "categories": {cat: {"present": bool, "ids": [...], "rows": [...]}}}；
    若 §八 章节不存在返回 None。"""
    head_match = CHANGELOG_SPEC_HEAD_RE.search(spec_md)
    if not head_match:
        return None
    section_text = spec_md[head_match.end():]
    next_h2 = CHANGELOG_SPEC_NEXT_H2_RE.search(section_text)
    if next_h2:
        section_text = section_text[: next_h2.start()]

    cats: dict = {c: {"present": False, "ids": [], "rows": []} for c in CHANGELOG_CATEGORIES}
    sub_matches = list(CHANGELOG_SPEC_SUB_RE.finditer(section_text))
    placeholder = bool(CHANGELOG_SPEC_PLACEHOLDER_RE.search(section_text)) and not sub_matches

    for i, m in enumerate(sub_matches):
        cat = m.group(1)
        start = m.end()
        end = sub_matches[i + 1].start() if i + 1 < len(sub_matches) else len(section_text)
        sub_text = section_text[start:end]
        cats[cat]["present"] = True
        for line in sub_text.split("\n"):
            line = line.strip()
            if not line.startswith("|") or line.startswith("|--") or line.startswith("|-"):
                continue
            if re.search(r"组件\s*ID", line, re.IGNORECASE):
                continue  # 表头
            ids = CHANGELOG_SPEC_TABLE_PROJ_RE.findall(line)
            if ids:
                cats[cat]["ids"].extend(ids)
                cats[cat]["rows"].append({"raw": line, "ids": ids})
    return {"placeholder": placeholder, "categories": cats}


def parse_prd_changelog(prd_html: str) -> dict | None:
    """解析 prd.html <section id="component-changelog">。
    返回 {"categories": {cat: {"present": bool, "ids": [...]}}}；section 不存在返回 None。"""
    section_match = CHANGELOG_PRD_SECTION_RE.search(prd_html)
    if not section_match:
        return None
    section_text = section_match.group(1)

    cats: dict = {c: {"present": False, "ids": []} for c in CHANGELOG_CATEGORIES}
    anchors = list(CHANGELOG_PRD_GROUP_ANCHOR_RE.finditer(section_text))
    for i, m in enumerate(anchors):
        cat = PRD_CLASS_TO_CATEGORY[m.group(1)]
        start = m.end()
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(section_text)
        chunk = section_text[start:end]
        cats[cat]["present"] = True
        cats[cat]["ids"].extend(CHANGELOG_PRD_PROJ_RE.findall(chunk))
    return {"categories": cats}


def check_component_changelog_consistency(data: dict, r: Report) -> None:
    """S4-22：spec §八 与 prd #component-changelog 一致性校验。

    校验维度：
      1. 章节存在性（spec §八 + prd #component-changelog）
      2. prd 4 sub-section 占位齐全（强制；spec 占位场景允许只写一句话）
      3. 按类对齐：spec ↔ prd 组件 id 集合按 4 类逐一比对
      4. 弃用条目"替代组件"必须存在于（本清单"新增" ∪ components 文件已声明 proj）
    """
    product = data.get("product", "").strip()
    spec_path = OUTPUT_DIR / f"spec_{product}_latest.md"
    prd_path = OUTPUT_DIR / f"prd_{product}_latest.html"

    if not spec_path.exists() or not prd_path.exists():
        return  # 上层已报错

    spec_data = parse_spec_changelog(spec_path.read_text(encoding="utf-8"))
    prd_data = parse_prd_changelog(prd_path.read_text(encoding="utf-8"))

    # 1. 章节存在性
    if spec_data is None:
        r.fail("S4-22: spec.md 缺少 §八 组件变更清单章节（应为 `## 组件变更清单`）")
        return
    if prd_data is None:
        r.fail('S4-22: prd.html 缺少 <section id="component-changelog"> 章节')
        return

    spec_cats = spec_data["categories"]
    prd_cats = prd_data["categories"]

    # 2. prd 4 sub-section 占位齐全（强制）
    missing_prd_subs = [c for c in CHANGELOG_CATEGORIES if not prd_cats[c]["present"]]
    if missing_prd_subs:
        r.fail(
            f"S4-22: prd #component-changelog 缺 sub-section: {missing_prd_subs}"
            f"（prd_expression_standard.md §11.2 强制要求 4 类 sub-section 全部保留，无内容时保留占位）"
        )
        return

    # 占位场景：spec 写"本期无 proj 组件变更"一句话；prd 4 sub-section 都为空
    if spec_data["placeholder"]:
        prd_total = sum(len(prd_cats[c]["ids"]) for c in CHANGELOG_CATEGORIES)
        if prd_total > 0:
            r.fail(
                f'S4-22: spec 写"本期无 proj 组件变更"占位但 prd '
                f"#component-changelog 含 {prd_total} 条 proj 组件 id（不一致）"
            )
            return
        r.ok("S4-22 组件变更清单一致性（spec ↔ prd 双方均为占位状态，0 条变更）")
        return

    # 3. 按类对齐（条目数 + 组件 id 集合）
    diff_found = False
    for cat in CHANGELOG_CATEGORIES:
        spec_ids = sorted(set(spec_cats[cat]["ids"]))
        prd_ids = sorted(set(prd_cats[cat]["ids"]))
        if spec_ids != prd_ids:
            only_spec = sorted(set(spec_ids) - set(prd_ids))
            only_prd = sorted(set(prd_ids) - set(spec_ids))
            details = []
            if only_spec:
                details.append(f"spec 独有={only_spec}")
            if only_prd:
                details.append(f"prd 独有={only_prd}")
            r.fail(
                f"S4-22: 「{cat}」段 spec ↔ prd 组件 id 集合不一致："
                f"spec={spec_ids} / prd={prd_ids}（{' | '.join(details)}）"
            )
            diff_found = True

    # 4. 弃用条目"替代组件"必须存在于（本清单"新增" ∪ components 文件已声明 proj）
    deprecated_rows = spec_cats["弃用"]["rows"]
    new_ids = set(spec_cats["新增"]["ids"])

    components_path = OUTPUT_DIR / f"components_{product}_latest.md"
    existing_proj_ids: set[str] = set()
    if components_path.exists():
        comps = parse_proj_components(components_path.read_text(encoding="utf-8"))
        existing_proj_ids = {c["id"] for c in comps}

    valid_replacement_pool = new_ids | existing_proj_ids
    for row in deprecated_rows:
        ids = row["ids"]
        if len(ids) < 2:
            continue  # 单 id 行（无替代组件）
        deprecated_id = ids[0]
        for repl in ids[1:]:
            if repl == deprecated_id:
                continue
            if repl not in valid_replacement_pool:
                r.fail(
                    f"S4-22: 弃用条目 [{deprecated_id}] 的替代组件 [{repl}] 不存在于"
                    f'本清单"新增"段或 components 文件已声明 proj'
                    f"（新增={sorted(new_ids)} / components 已声明={sorted(existing_proj_ids)}）"
                )
                diff_found = True

    if not diff_found:
        total = sum(len(spec_cats[c]["ids"]) for c in CHANGELOG_CATEGORIES)
        r.ok(f"S4-22 组件变更清单一致性（spec ↔ prd ↔ components 三方对齐，共 {total} 条变更）")


# ── 校验 6.6｜侧栏「组件变更」分组（issue 2026-05-07_1613）──────────────────

# SSOT 真源：PRD §十一 <section id="component-changelog"> 三个 group(new/update/deprecated)
# SSOT 派生：PRD sidebar <nav class="sidebar"> 内「组件变更」分组（assemble.py 自动注入）
# 校验维度：
#   ①sidebar 含「组件变更」section-title
#   ②[COMPONENT-CHANGELOG-NAV-START/END] 注入块存在
#   ③注入块内组件 id 集合 = 主体 component-changelog 三类（new/update/deprecated）id 全集
#   ④每个 nav 项状态 tag class 与组件来源 changelog group 类型一致

# 匹配 sidebar「组件变更」分组的标题锚点 — 用 data-changelog-title 这个稳定锚点
# (真源 prd_template.html L833 由 <div class="sidebar-section-title sidebar-group-toggle"
#  ...><span data-changelog-title>组件变更</span>...</div> 渲染,含多 class + span 子元素;
# 旧 regex 期望"单 class + 文字直接在 div"已不再匹配真源结构)
SIDEBAR_CHANGELOG_TITLE_RE = re.compile(
    r'<span[^>]*data-changelog-title[^>]*>\s*组件变更\s*</span>'
)
SIDEBAR_CHANGELOG_BLOCK_RE = re.compile(
    r"<!--\s*\[COMPONENT-CHANGELOG-NAV-START\][^>]*-->"
    r"(?P<body>.*?)"
    r"<!--\s*\[COMPONENT-CHANGELOG-NAV-END\]\s*-->",
    re.DOTALL,
)
# 兼容 sidebar-spec-item(一级) + sidebar-spec-subitem(二级嵌套) — sidebar 结构升级为分级
# 嵌套后,assemble.py inject_component_changelog_nav 实际注入 proj 组件条目用 subitem(L871),
# 占位文字用 item(L824/L881)。本 regex 兼容两者以提取带状态 tag 的 proj 组件条目。
SIDEBAR_CHANGELOG_ITEM_RE = re.compile(
    r'<div\s+class\s*=\s*"sidebar-spec-(?:item|subitem)"[^>]*>'
    r'\s*<span\s+class\s*=\s*"sidebar-component-status\s+sidebar-status-(?P<status>new|update|deprecated)"[^>]*>'
    r'(?P<label>新增|更新|弃用)</span>\s*'
    r'(?P<proj_id>proj\.L\d+\.[a-z][\w-]*)\s*</div>',
    re.IGNORECASE,
)

# 主体 changelog 类型（中文）→ sidebar 注入 status class 映射
CHANGELOG_CAT_TO_SIDEBAR_STATUS = {
    "新增": "new",
    "修改": "update",
    "弃用": "deprecated",
    # 建议升级 不进 sidebar
}


def check_sidebar_component_changelog(prd_html: str, r: Report) -> None:
    """侧栏「组件变更」分组完整性（issue 2026-05-07_1613，Q2=A 完整校验）。

    校验:
      ①sidebar 含「组件变更」section-title
      ②[COMPONENT-CHANGELOG-NAV-START/END] 注入块存在
      ③注入块组件 id 集合 = 主体 component-changelog 三类（new/update/deprecated）全集
      ④每个 nav 项状态 tag 与组件来源 changelog group 类型一致
    """
    r.section("侧栏「组件变更」分组完整性（v1.0,issue 2026-05-07_1613）")

    # ① sidebar 含分组标题
    if not SIDEBAR_CHANGELOG_TITLE_RE.search(prd_html):
        r.fail(
            "sidebar 缺「组件变更」section-title 分组（应紧跟「交互原型」分组之后）；"
            "请确认 prd_template.html 含 <span data-changelog-title>组件变更</span> 锚点"
        )
        return  # 后续校验依赖此分组,提前 return

    # ② 注入块存在
    block_match = SIDEBAR_CHANGELOG_BLOCK_RE.search(prd_html)
    if not block_match:
        # 占位注释还没被替换（assemble.py 未跑或跑失败）
        if "[COMPONENT-CHANGELOG-NAV]" in prd_html:
            r.fail(
                "sidebar 含 [COMPONENT-CHANGELOG-NAV] 占位但未被 assemble.py 替换；"
                "请运行 python pm-workflow/scripts/assemble.py prd"
            )
        else:
            r.fail(
                "sidebar 缺 [COMPONENT-CHANGELOG-NAV-START/END] 注入块；"
                "请确认 prd_template.html 含占位 + 已运行 assemble.py prd"
            )
        return

    body = block_match.group("body")

    # 解析注入块内的 nav 项（id + status）
    sidebar_items: dict[str, str] = {}  # proj_id → status (new/update/deprecated)
    for it in SIDEBAR_CHANGELOG_ITEM_RE.finditer(body):
        sidebar_items[it.group("proj_id")] = it.group("status").lower()

    # ③ 与主体 component-changelog 对齐
    body_changelog = parse_prd_changelog(prd_html)
    if not body_changelog:
        # 主体无 component-changelog → sidebar 注入应为空提示
        if sidebar_items:
            r.fail(
                f"PRD 主体无 <section id=\"component-changelog\"> 但 sidebar 注入了 "
                f"{len(sidebar_items)} 个组件项；应注入「（本期无组件变更）」占位"
            )
        else:
            r.ok("主体无 component-changelog,sidebar 注入空占位（合规）")
        return

    # 主体期望集合（仅 new/update/deprecated 三类,promote 不进 sidebar）
    expected: dict[str, str] = {}  # proj_id → expected_status
    for cat, info in body_changelog["categories"].items():
        if cat not in CHANGELOG_CAT_TO_SIDEBAR_STATUS:
            continue
        target_status = CHANGELOG_CAT_TO_SIDEBAR_STATUS[cat]
        for proj_id in info["ids"]:
            expected[proj_id] = target_status

    actual_ids = set(sidebar_items.keys())
    expected_ids = set(expected.keys())

    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids
    fails = 0

    if missing:
        r.fail(
            f"sidebar 缺组件项（主体 component-changelog 含但 sidebar 未注入）: "
            f"{sorted(missing)}；请重跑 assemble.py prd"
        )
        fails += 1
    if extra:
        r.fail(
            f"sidebar 多余组件项（主体未声明）: {sorted(extra)}；"
            f"sidebar 应为派生视图,禁止手写"
        )
        fails += 1

    # ④ 状态 tag 与来源 group 一致
    mismatched: list[str] = []
    for proj_id in actual_ids & expected_ids:
        if sidebar_items[proj_id] != expected[proj_id]:
            mismatched.append(
                f"{proj_id}（sidebar={sidebar_items[proj_id]} / 主体期望={expected[proj_id]}）"
            )
    if mismatched:
        r.fail(
            f"sidebar 状态 tag 与主体 changelog group 类型不一致: {mismatched}；"
            f"请重跑 assemble.py prd"
        )
        fails += 1

    if fails == 0:
        r.ok(
            f"sidebar「组件变更」分组完整（{len(actual_ids)} 个组件项,状态 tag 与主体一致）"
        )


# ── 校验 7｜S4-04 平台覆盖（scaffold.platforms ↔ prd frame 双向对照）──────────

PLATFORM_FRAME_MAP = {
    # 每个端口对应 1 至 N 个候选 frame；命中任一即视为覆盖
    "APP": {"phone-frame", "tablet-frame"},          # APP 含手机 + PAD，至少其一
    "桌面Web": {"desktop-frame"},
    "桌面": {"desktop-frame"},
    "小程序": {"miniprogram-frame"},
    "微信小程序": {"miniprogram-frame"},
    "H5": {"h5-frame"},
    "PAD": {"tablet-frame"},
}
PLATFORM_FRAME_RE = re.compile(
    r'class="[^"]*\b(phone-frame|tablet-frame|desktop-frame|miniprogram-frame|h5-frame)\b'
)


def check_platform_coverage(data: dict, prd_html: str, r: Report) -> None:
    """S4-04：scaffold.platforms 声明的端口必须与 prd.html 实际 frame 类型双向一致。

    - 每个声明端口至少需要候选集中某一个 frame 在 prd.html 出现（如 APP 至少含 phone 或 tablet）
    - prd.html 中出现的 frame 必须在所有声明端口的候选集并集内（防超出声明）
    """
    r.section("S4-04 平台覆盖")
    platforms = data.get("platforms", [])
    if not platforms:
        r.warn("S4-04: scaffold.platforms 为空，跳过平台覆盖核查")
        return

    actual = set(PLATFORM_FRAME_RE.findall(prd_html))
    legal_frames: set[str] = set()
    uncovered: list[tuple[str, list[str]]] = []
    unknown_platforms: list[str] = []

    for p in platforms:
        cands = set(PLATFORM_FRAME_MAP.get(p, set()))
        if not cands:
            unknown_platforms.append(p)
            continue
        legal_frames.update(cands)
        if not (cands & actual):
            uncovered.append((p, sorted(cands)))

    extra = actual - legal_frames

    has_fail = False
    if unknown_platforms:
        r.warn(
            f"S4-04: scaffold.platforms 含未知端口标识 {unknown_platforms}"
            f"（已知: {sorted(PLATFORM_FRAME_MAP.keys())}）"
        )
    if uncovered:
        for p, cands in uncovered:
            r.fail(
                f"S4-04: 声明端口 '{p}' 在 prd.html 中无对应 frame（需任一: {cands}）"
            )
        has_fail = True
    if extra:
        r.fail(
            f"S4-04: prd.html 含 scaffold.platforms 未声明的端口 frame: {sorted(extra)}"
            f"（声明端口候选并集: {sorted(legal_frames)}）"
        )
        has_fail = True

    if not has_fail and not unknown_platforms:
        r.ok(
            f"S4-04 平台覆盖（声明端口 {sorted(platforms)} ↔ 实际 frame {sorted(actual)}）"
        )

    # ── SNB-005 修复：per-module 声明端口覆盖（WARN-phase，2026-05-18）──
    # 根因：上方仅全文档级（声明端口在整 PRD 任一处出现即过）→ 某模块全无某
    # 声明端口帧（如 M01 全无 APP 帧）会被其他模块的同端口帧掩盖而逃过 + 前序
    # 终审；叠加 check_frame_platform_tag 单帧静默跳过 → 整模块缺端口无人拦。
    # 修复 = 模块级覆盖核查，但**WARN 阶段不 FAIL**（吸取 S4-32 教训：新结构
    # 规则即便有价值也先 WARN——某些模块合法地单端口，per-module 硬 FAIL 会
    # FP；WARN 给人审裁定"该模块是否确应缺此端口"）。升 FAIL 条件同 S4-28 档 C。
    known = [p for p in platforms if PLATFORM_FRAME_MAP.get(p)]
    if len(known) >= 2:  # 单声明端口无"模块缺某端口"概念，跳过
        sec_re = re.compile(
            r'<section\s+id\s*=\s*"H-(M\d{2})-[^"]*"[^>]*>(.*?)</section>',
            re.DOTALL | re.IGNORECASE,
        )
        mod_frames: dict[str, set[str]] = {}
        for mm in sec_re.finditer(prd_html):
            mid = mm.group(1)
            mod_frames.setdefault(mid, set()).update(
                PLATFORM_FRAME_RE.findall(mm.group(2))
            )
        for mid in sorted(mod_frames):
            fr = mod_frames[mid]
            if not fr:
                continue  # 该模块无任何端口帧（其它 check 兜底），不在此判
            missing = [
                p for p in known
                if not (set(PLATFORM_FRAME_MAP[p]) & fr)
            ]
            if missing:
                r.warn(
                    f"S4-04(SNB-005,WARN 阶段): 模块 {mid} 全无声明端口 "
                    f"{missing} 的任何 frame（本模块实际 frame: {sorted(fr)}；"
                    f"声明端口 {sorted(known)}）——若该模块确应缺此端口请人审确认，"
                    f"否则补帧；档 C，下游迁移稳定后升 FAIL"
                )


# ── 校验 8｜S4-08 cursor:pointer 全覆盖 ───────────────────────────────────────

CURSOR_POINTER_RE = re.compile(r"cursor\s*:\s*pointer", re.IGNORECASE)
CSS_RULE_RE = re.compile(
    r"((?:[^{}]+))\s*\{([^}]*)\}",
    re.DOTALL,
)
ONCLICK_ELEM_RE = re.compile(
    r'<(?P<tag>\w+)(?P<attrs>(?:\s+[^>]*?)?\s+onclick\s*=\s*"[^"]+"(?:[^>]*)?)>',
    re.IGNORECASE,
)


def _collect_cursor_classes(prd_html: str) -> set[str]:
    """收集"自带 cursor:pointer"的 class 集合（fallback.css + prd <style>）。"""
    cursor_classes: set[str] = set()

    css_sources: list[str] = []
    if FB_FALLBACK_CSS_PATH.exists():
        css_sources.append(FB_FALLBACK_CSS_PATH.read_text(encoding="utf-8"))
    for m in re.finditer(r"<style[^>]*>(.*?)</style>", prd_html, re.DOTALL):
        css_sources.append(m.group(1))

    for css in css_sources:
        for rule_match in CSS_RULE_RE.finditer(css):
            selector_block = rule_match.group(1)
            body = rule_match.group(2)
            if not CURSOR_POINTER_RE.search(body):
                continue
            for sel in selector_block.split(","):
                # 提取所有 .class-name token（处理 .a.b / .a:hover / .a > .b 等）
                for cls in re.findall(r"\.([a-zA-Z][\w-]*)", sel):
                    cursor_classes.add(cls)
    return cursor_classes


def check_cursor_pointer_coverage(prd_html: str, r: Report) -> None:
    """S4-08：所有 onclick 元素必须有 cursor:pointer（inline 或登记 class）。"""
    r.section("S4-08 cursor:pointer 全覆盖")
    cursor_classes = _collect_cursor_classes(prd_html)

    missing: list[str] = []
    total_onclick = 0
    for m in ONCLICK_ELEM_RE.finditer(prd_html):
        tag = m.group("tag").lower()
        attrs = m.group("attrs")
        total_onclick += 1
        if tag in ("button", "a"):
            continue  # 浏览器原生 pointer，免检
        # inline style cursor:pointer
        if CURSOR_POINTER_RE.search(attrs):
            continue
        # class 命中登记 cursor 的 class
        cls_match = re.search(r'\bclass\s*=\s*"([^"]*)"', attrs)
        if cls_match:
            class_tokens = set(cls_match.group(1).split())
            if class_tokens & cursor_classes:
                continue
        snippet = m.group(0)[:120].replace("\n", " ")
        missing.append(snippet)

    if missing:
        r.fail(
            f"S4-08: {len(missing)}/{total_onclick} 个非 button/a 的 onclick 元素缺 cursor:pointer"
            f"（既无 inline style 也无登记 cursor 的 class）"
        )
        for s in missing[:5]:
            r.fail(f"  - {s}")
        if len(missing) > 5:
            r.fail(f"  ... 还有 {len(missing) - 5} 个未列出")
    else:
        r.ok(
            f"S4-08 onclick 元素全部含 cursor:pointer"
            f"（{total_onclick} 个 onclick / {len(cursor_classes)} 个登记 cursor class）"
        )


# ── 校验 9｜S4-21 spec ↔ prd 字段绑定一致性 ──────────────────────────────────

SPEC_FIELD_SECTION_RE = re.compile(
    r"S2\.M\d+\.4\s*数据字段绑定.*?(?=S2\.M\d+\.5|\n##\s|\Z)",
    re.DOTALL,
)
SPEC_FIELD_ROW_RE = re.compile(
    # spec §S2.M[XX].4 数据字段绑定表实际表头：
    # | 页面 | 字段名 | 类型 | 来源 | 必填 | prd 渲染元素 | prd 属性 |
    # 字段名在第 2 列；可能带 `[]` 后缀（多选字段如 status[]），解析时去尾部 [] 与 prd name 对齐
    # 来源：PM 业务任务期间识别（原正则字段名当第 1 列，对实际表头静默失效，
    #       导致 S4-21 字段绑定一致性校验完全无效；issue 2026-05-07_1400 条 2 排查 — bug 修复）
    r"^\|\s*[^|]+\|\s*`?([a-zA-Z][\w]*)(?:\[\])?`?\s*\|(.+)$",
    re.MULTILINE,
)
PRD_FORM_FIELD_RE = re.compile(
    r'<(?:input|select|textarea)\b[^>]*?\b(?:name|data-field)\s*=\s*"([^"]+)"',
    re.IGNORECASE,
)


def _parse_spec_fields(spec_md: str) -> tuple[set[str], set[str]]:
    """从 spec.md 各模块 S2.M[XX].4 数据字段绑定段提取字段名 + required 标记。
    返回 (all_fields, required_fields)。"""
    all_fields: set[str] = set()
    required_fields: set[str] = set()

    for sec_match in SPEC_FIELD_SECTION_RE.finditer(spec_md):
        section = sec_match.group(0)
        for row_match in SPEC_FIELD_ROW_RE.finditer(section):
            field_id = row_match.group(1).strip()
            row_rest = row_match.group(2)
            # 跳过表头候选
            if field_id.lower() in ("field", "id") or "字段" in row_match.group(0)[:20]:
                continue
            # 跳过分隔行
            if "-" in field_id and len(set(field_id)) == 1:
                continue
            all_fields.add(field_id)
            if "required" in row_rest.lower() or "必填" in row_rest:
                required_fields.add(field_id)
    return all_fields, required_fields


def check_field_binding_consistency(spec_md: str, prd_html: str, r: Report) -> None:
    """S4-21：spec.md §9 字段名 ↔ prd 表单 name/data-field 严格一致。"""
    r.section("S4-21 spec ↔ prd 字段绑定一致性")
    spec_fields, required_fields = _parse_spec_fields(spec_md)
    if not spec_fields:
        r.warn(
            "S4-21: spec.md 未发现 S2.M*.4 数据字段绑定段（或解析失败），"
            "跳过 S4-21 核查；如本期含表单请人工核对"
        )
        return

    prd_fields = set(PRD_FORM_FIELD_RE.findall(prd_html))
    missing_required = required_fields - prd_fields
    prd_only = prd_fields - spec_fields
    spec_only_optional = spec_fields - prd_fields - required_fields

    has_fail = False
    if missing_required:
        r.fail(
            f"S4-21: spec §9 必填字段未在 prd 表单绑定: {sorted(missing_required)}"
            f"（spec 必填总数 {len(required_fields)}，缺 {len(missing_required)} 项）"
        )
        has_fail = True
    if prd_only:
        r.fail(
            f"S4-21: prd 表单字段不在 spec §9 中（PM 凭空生造或命名风格漂移）: "
            f"{sorted(prd_only)}（如 productName vs product_name 应统一为 spec 写法）"
        )
        has_fail = True
    if spec_only_optional:
        r.warn(
            f"S4-21: spec §9 可选字段未在 prd 表单绑定（可能是纯展示元素或漏渲染）: "
            f"{sorted(spec_only_optional)}"
        )

    if not has_fail:
        r.ok(
            f"S4-21 字段绑定一致（spec {len(spec_fields)} 字段 / 必填 {len(required_fields)}"
            f" / prd 表单 {len(prd_fields)}）"
        )


# ── 校验 10｜S4-24 交互元素 data-tp 绑定 ─────────────────────────────────────

DATA_TP_RE = re.compile(r'\bdata-tp\s*=\s*"(M\d{2}-P\d{2}-[TDC]\d{2,3})"')
INTERACTIVE_FB_CLASSES = {
    "fb-btn-primary", "fb-btn-default", "fb-btn-ghost", "fb-btn-text", "fb-btn-danger",
    "fb-input", "fb-textarea", "fb-search", "fb-select",
    "fb-checkbox", "fb-radio", "fb-switch",
    "fb-link", "fb-list-item", "fb-pagination",
    "fb-chip",
}
# PRD 工具/演示态导航元素 class 黑名单（免 data-tp，不属于产品业务触点）
# 包括：侧栏导航、状态 chip 切换、主模板顶部多语言/主题/搜索/缩放/标注等。
# 来源：PM 业务任务期间识别（无黑名单时 S4-24 对 PRD 工具元素全量误报，PM 在 commit
#       616bd71 等业务 commit 中夹带了这些黑名单；本次走 workflow-evolution skill 路径
#       正式合并；issue 2026-05-07_1400 条 2 排查 — 关键误报修复）
NON_BUSINESS_NAV_CLASSES = {
    "sidebar-page", "sidebar-state", "sidebar-section", "sidebar-spec-item",
    "sidebar-state-chip", "sidebar-toggle",
    "sidebar-group-toggle",  # sidebar 5 分组折叠/展开按钮(doc/spec/sitemap/changelog/proto；sitemap=Item 2 页面架构总览)
    "sidebar-recursive-toggle",  # sidebar ⇊ 按钮(折叠/展开所有下层)
    "sidebar-subgroup-icon",  # sidebar non-leaf 节点 icon
    "state-chip",  # state-chips segmented control
    "lang-btn", "theme-btn",
    "back-to-top", "scroll-to-top",
    "changelog-anchor",
    "icon-toggle", "zoom-btn", "tab-trigger",
    "journey-view-btn",  # A-04 用户旅程 toggle 切换（PRD 工具）
    "mmd-fs-btn",  # WE-C mermaid 全屏预览触发按钮（JS 注入，doc-viewer chrome
                   # 非业务触点；WE-F 防御——若未来静态化亦免 S4-24，主豁免
                   # 走 NON_BUSINESS_ONCLICK_PATTERNS 的 openMermaidFs 等）
}
NON_BUSINESS_ONCLICK_PATTERNS = (
    "showSection(", "searchSidebar(", "setLang(", "setTheme(",
    "scrollToTop(", "toggleSidebar(",
    "toggleSidebarGroup(",  # sidebar 4 分组折叠
    "toggleSidebarSubgroup(",  # sidebar non-leaf 子节点折叠
    "toggleAllSubgroupsInGroup(",  # sidebar ⇊ 批量折叠
    "handleSubgroupClick(",  # sidebar non-leaf 分流(icon 折叠/文字跳转)
    "toggleTheme(", "toggleAnnotations(", "setZoom(",
    "toggleSection(", "switchTab(",
    "switchJourneyView(",  # A-04 用户旅程 toggle 切换
    # WE-C mermaid 全屏预览 doc-viewer chrome（同 switchJourneyView 类，
    # 非产品业务触点；WE-F 2026-05-19 下游 R2 修：模态工具按钮
    # prd_template.html:1097-1098 onclick=resetMermaidFsView/closeMermaidFs
    # 静态无 class，被 S4-24 误收 → 缺 data-tp + 连带 tp-marker 序号错）
    "openMermaidFs(", "closeMermaidFs(", "resetMermaidFsView(",
    "event.stopPropagation()", "event.preventDefault()",
)
TP_WRAP_BLOCK_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\btp-wrap\b[^"]*"[^>]*>(.*?)</div>',
    re.DOTALL,
)
TP_MARKER_NUM_RE = re.compile(r'<span\s+class\s*=\s*"[^"]*\btp-marker\b[^"]*"[^>]*>([^<]+)</span>')


def _remove_sections_by_id_prefix(html: str, id_prefix: str) -> str:
    """剔除所有 id 以 PREFIX 开头的 <section> 块,平衡标签深度计数器算法。

    替代非贪婪 regex `<section...>.*?</section>` 的不安全实现——后者在嵌套 section
    场景下会停在第一个 `</section>`,误把内层关闭当外层关闭,导致剔除不完整 + 撕碎
    HTML 结构（外层按钮 / 文本残留进入下游交互元素扫描）。

    触发场景（下游 PM 修复线索）：proj-component-{name} 状态展示区内,PM 写状态展示
    时偶尔用 <section> 嵌套替代 <article>,旧实现漏剔。
    """
    result: list[str] = []
    i = 0
    target_re = re.compile(
        r'<section\b[^>]*\bid\s*=\s*"' + re.escape(id_prefix) + r'[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    open_re = re.compile(r'<section\b', re.IGNORECASE)
    close_re = re.compile(r'</section\s*>', re.IGNORECASE)
    while i < len(html):
        m = target_re.search(html, i)
        if not m:
            result.append(html[i:])
            break
        result.append(html[i : m.start()])
        depth = 1
        pos = m.end()
        while pos < len(html) and depth > 0:
            om = open_re.search(html, pos)
            cm = close_re.search(html, pos)
            if cm and (not om or cm.start() < om.start()):
                depth -= 1
                pos = cm.end()
            elif om:
                depth += 1
                pos = om.end()
            else:
                break
        i = pos
    return "".join(result)


def _extract_interactive_elements(prd_html: str) -> list[tuple[str, str]]:
    """提取 PRD 中所有"应该有 data-tp"的交互元素的 (开始标签片段, data-tp 值或 None)。
    覆盖：onclick 元素 / button / a[href!='#'] / input / select / textarea / 含 INTERACTIVE_FB_CLASSES 的元素。
    例外（不计入）：tp-marker 自身、status section 内的元素、proj-component-{name} section 内的元素（属规格展示）。"""
    # 先剔除 #proj-component-{name} section 内容（规格展示，免）；用平衡标签算法正确处理嵌套 section
    cleaned = _remove_sections_by_id_prefix(prd_html, "proj-component-")
    # 同时剔除 #spec-* section（产品规格区，免）
    cleaned = _remove_sections_by_id_prefix(cleaned, "spec-")

    results: list[tuple[str, str]] = []
    # 任意标签开头：含 onclick 或属于 INTERACTIVE_FB_CLASSES 类型
    elem_re = re.compile(r'<(?P<tag>\w+)(?P<attrs>(?:\s+[^>]*?)?)>', re.IGNORECASE)
    for m in elem_re.finditer(cleaned):
        tag = m.group("tag").lower()
        attrs = m.group("attrs") or ""

        # 跳过 tp-marker 自身
        if "tp-marker" in attrs:
            continue
        # 跳过状态展示区相关 class（保险）
        if "proj-component" in attrs or "spec-" in attrs:
            continue

        # 跳过 PRD 工具/导航元素（class 黑名单：sidebar / state-chip / lang-btn / journey-view-btn 等）
        cls_attr_match = re.search(r'\bclass\s*=\s*"([^"]*)"', attrs)
        if cls_attr_match:
            cls_tokens = set(cls_attr_match.group(1).split())
            if cls_tokens & NON_BUSINESS_NAV_CLASSES:
                continue
        # 跳过 onclick 中调用 PRD 工具函数的元素（showSection / setLang / switchJourneyView 等）
        onclick_match = re.search(r'\bonclick\s*=\s*"([^"]*)"', attrs)
        if onclick_match:
            onclick_val = onclick_match.group(1)
            if any(pat in onclick_val for pat in NON_BUSINESS_ONCLICK_PATTERNS):
                continue
        oninput_match = re.search(r'\boninput\s*=\s*"([^"]*)"', attrs)
        if oninput_match:
            oninput_val = oninput_match.group(1)
            if any(pat in oninput_val for pat in NON_BUSINESS_ONCLICK_PATTERNS):
                continue

        is_interactive = False
        # 信号 1：onclick 属性
        if re.search(r'\bonclick\s*=', attrs):
            is_interactive = True
        # 信号 2：button / 表单 / a 标签
        elif tag in ("button", "input", "select", "textarea"):
            # input type=hidden 免（无独立触点）
            if tag == "input" and re.search(r'\btype\s*=\s*"hidden"', attrs):
                continue
            is_interactive = True
        elif tag == "a":
            # a[href] 算交互；a[href^='#'] 一律视为页内锚点导航免（侧栏导航、目录跳转、触点徽章关联等常见无害模式）
            href_m = re.search(r'\bhref\s*=\s*"([^"]*)"', attrs)
            if href_m and href_m.group(1) and not href_m.group(1).startswith("#"):
                is_interactive = True
        # 信号 3：含 INTERACTIVE_FB_CLASSES 任一
        else:
            cls_m = re.search(r'\bclass\s*=\s*"([^"]*)"', attrs)
            if cls_m:
                tokens = set(cls_m.group(1).split())
                if tokens & INTERACTIVE_FB_CLASSES:
                    is_interactive = True

        if not is_interactive:
            continue

        # 提取 data-tp 值
        tp_m = re.search(r'\bdata-tp\s*=\s*"([^"]*)"', attrs)
        tp_val = tp_m.group(1) if tp_m else ""
        snippet = m.group(0)[:120]
        results.append((snippet, tp_val))

    return results


def check_interactive_data_tp(spec_md: str, prd_html: str, r: Report) -> None:
    """S4-24：每个交互元素须含 data-tp 属性，值与 spec 触点表 ID 一致。"""
    r.section("S4-24 交互元素 data-tp 绑定")

    # 1. 提取交互元素及其 data-tp
    elements = _extract_interactive_elements(prd_html)
    if not elements:
        r.warn("S4-24: 未在 PRD 中检测到交互元素（onclick / button / 表单 / 链接 / fb-* 交互类）")
        return

    # 2. 缺失 data-tp 的交互元素
    missing = [s for s, tp in elements if not tp]
    if missing:
        r.fail(
            f"S4-24: {len(missing)}/{len(elements)} 个交互元素缺 data-tp 属性"
            f"（违反 prd_expression_standard.md §6.1）"
        )
        for s in missing[:5]:
            r.fail(f"  - {s}")
        if len(missing) > 5:
            r.fail(f"  ... 还有 {len(missing) - 5} 个未列出")

    # 3. data-tp 值与 spec 触点表一致
    prd_tp_set = {tp for _, tp in elements if tp}
    spec_tp_set = set(TOUCHPOINT_RE.findall(spec_md))
    only_prd = sorted(prd_tp_set - spec_tp_set)
    only_spec = sorted(spec_tp_set - prd_tp_set)

    if only_prd:
        r.fail(
            f"S4-24: prd data-tp 值不在 spec 触点表中（PM 凭空生造或拼写错）: {only_prd}"
        )
    if only_spec:
        r.warn(
            f"S4-24: spec 触点表中有 ID 在 prd data-tp 中未绑定: {only_spec}"
            f"（如对应触点是规格描述未渲染元素请忽略）"
        )

    # 4. tp-wrap 内 tp-marker 数字 ↔ 兄弟元素 data-tp 末段一致性
    inconsistent_wraps: list[str] = []
    for wrap_m in TP_WRAP_BLOCK_RE.finditer(prd_html):
        block = wrap_m.group(1)
        marker_m = TP_MARKER_NUM_RE.search(block)
        sibling_tp_m = re.search(r'\bdata-tp\s*=\s*"M\d{2}-P\d{2}-[TDC](\d{2,3})"', block)
        if not marker_m or not sibling_tp_m:
            continue
        marker_num = marker_m.group(1).strip()
        tp_suffix = sibling_tp_m.group(1)
        # 末段允许 01 / 1 / 001 等格式，去前导零比对
        if marker_num.lstrip("0") != tp_suffix.lstrip("0"):
            inconsistent_wraps.append(
                f"tp-marker={marker_num} vs data-tp 末段={tp_suffix}"
            )

    if inconsistent_wraps:
        r.fail(
            f"S4-24: {len(inconsistent_wraps)} 个 tp-wrap 内的 tp-marker 数字与兄弟元素 data-tp 末段不一致"
        )
        for s in inconsistent_wraps[:5]:
            r.fail(f"  - {s}")

    if not missing and not only_prd and not inconsistent_wraps:
        r.ok(
            f"S4-24 交互元素 data-tp 绑定一致"
            f"（{len(elements)} 个交互元素 / {len(prd_tp_set)} 个唯一 data-tp / 与 spec 触点表对齐）"
        )


# ── 校验 11｜fb-fallback.css ↔ fb-fallback-manifest.md sync ──────────────────

FB_FALLBACK_MANIFEST_PATH = (
    REPO_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "fb-fallback-manifest.md"
)
FB_FALLBACK_CSS_SELECTOR_RE = re.compile(r"^\s*\.(fb-[a-z][a-z0-9-]*)", re.MULTILINE)
# Manifest 端宽松 regex（覆盖 HTML class 属性 + CSS 声明 + 散文描述三种形式）：
# - HTML：`class="fb-modal-body"`（无 `.` 前缀，是 manifest 主流形式）
# - CSS：`.fb-modal-body { ... }`（带 `.` 前缀）
# - 散文：`fb-modal-body` 引用（无 `.` 前缀）
# 避免 FP 不靠 regex 严格化（方案 3 曾试过导致 44 FAIL），改靠下方 FB_NON_COMPONENT_REFS
# 多层豁免集合（skill 名 + 文件名 + 注释占位词），治 fb-design-query / fb-tab-bar 类 FP
FB_FALLBACK_MANIFEST_TOKEN_RE = re.compile(r"\bbj-[a-z][a-z0-9-]*\b")
# CSS variable 名(以 `--fb-X` 形式出现,非 class)— 提取后从 manifest_tokens 扣除,
# 避免 manifest 中提及 var 名(如 fb-overlay)被误判为"在 css 中未实现"的 class
FB_FALLBACK_CSS_VAR_RE = re.compile(r"--fb-[a-z][a-z0-9-]*")


def _collect_fb_non_component_refs() -> set[str]:
    """收集 manifest 中合法的非组件 `fb-*` 字面（用于排除 FP）。

    三类来源（2026-05-31 治"宽松 regex 误判 skill 名 + 文件名为组件 FAIL"）：
    1. 文件名自引：fb-fallback / fb-fallback-manifest（manifest 提及自身或对方文件名）
    2. Skill 目录名：自动扫 `pm-workflow/skills/fb-*` 目录列表（治 fb-design-query 类，
       未来加 fb-* skill 自动豁免，无需手工维护清单）
    3. 由调用方按需扩充（如有新的合法非组件字面发现）

    设计原则：自动同步优先（skill 目录扫描），不维护静态清单避免遗漏。
    """
    refs = {"fb-fallback", "fb-fallback-manifest"}  # 文件名自引

    # 自动扫 pm-workflow/skills/fb-* 目录名（避免硬编码 skill 名清单）
    skills_dir = REPO_ROOT / "pm-workflow" / "skills"
    if skills_dir.exists():
        for p in skills_dir.glob("fb-*"):
            if p.is_dir():
                refs.add(p.name)

    return refs


def check_fb_fallback_sync(r: Report) -> None:
    """fb-fallback.css 与 fb-fallback-manifest.md 双向 sync 校验。

    - css 是技术真源（实际渲染依据,assemble.py 注入 PRD <style>）
    - manifest 是派生视图（HTML 模板调用文档,PM 阶段 4 PRD 必读）
    - 双方 fb-* class 集合应一致（排除合法非组件字面：文件名自引 + skill 名 + CSS var）

    历史教训（2026-05-31）：原仅排除 `{fb-fallback, fb-fallback-manifest}` 致
    `fb-design-query`（SSOT #52 skill 目录名）+ `fb-tab-bar`（manifest 待加占位）
    误判 FAIL。治本：①自动扫 skills/fb-* 目录纳入豁免（治 skill 名 FP）
    ②manifest 注释占位字面改 hyphen 化避免 `\\bbj-...\\b` 捕获（治待加占位 FP）。
    """
    r.section("fb-fallback.css ↔ fb-fallback-manifest.md sync")

    if not FB_FALLBACK_CSS_PATH.exists():
        r.warn(f"fb-fallback.css 不存在: {FB_FALLBACK_CSS_PATH}, 跳过 sync 校验")
        return
    if not FB_FALLBACK_MANIFEST_PATH.exists():
        r.warn(
            f"fb-fallback-manifest.md 不存在: {FB_FALLBACK_MANIFEST_PATH}, 跳过 sync 校验"
        )
        return

    css_text = FB_FALLBACK_CSS_PATH.read_text(encoding="utf-8")
    manifest_text = FB_FALLBACK_MANIFEST_PATH.read_text(encoding="utf-8")

    # CSS selector 集合（去 . 前缀）
    css_selectors = set(FB_FALLBACK_CSS_SELECTOR_RE.findall(css_text))

    # CSS variable 集合(去 -- 前缀,如 --fb-overlay → fb-overlay)
    # 这些是 var 名而非 class,manifest 中提及它们时不应算"未实现 class"
    css_vars = {v[2:] for v in FB_FALLBACK_CSS_VAR_RE.findall(css_text)}

    # 合法非组件字面豁免集合（自动同步 skill 目录 + 文件名自引）
    non_component_refs = _collect_fb_non_component_refs()

    # Manifest token 集合（扣除合法非组件字面 + CSS variable 名）
    manifest_tokens = set(FB_FALLBACK_MANIFEST_TOKEN_RE.findall(manifest_text))
    manifest_tokens -= non_component_refs
    manifest_tokens -= css_vars

    only_css = sorted(css_selectors - manifest_tokens)
    only_manifest = sorted(manifest_tokens - css_selectors)

    has_fail = False
    if only_css:
        r.fail(
            f"fb-fallback.css 中有 {len(only_css)} 个 selector 在 manifest 中未文档化"
            f"（PM 不知存在,可能重复派生 proj 或漏引用）: {only_css}"
        )
        has_fail = True
    if only_manifest:
        r.fail(
            f"fb-fallback-manifest.md 中有 {len(only_manifest)} 个 fb-* token 在 css 中未实现"
            f"（PM 引用后浏览器渲染会塌陷到 fallback CSS）: {only_manifest}"
        )
        has_fail = True

    if not has_fail:
        r.ok(
            f"fb-fallback css ↔ manifest 双向一致"
            f"（css 共 {len(css_selectors)} 个 selector / manifest 共 {len(manifest_tokens)} 个 token,"
            f"排除非组件字面 {sorted(non_component_refs)}）"
        )


# ── 校验 12｜prd.html doc-changelog 6 列校验（G-02 NB-WE-21 完整摘账，2026-06-01）─

# 复用 spec 端 EXPECTED_CHANGELOG_HEADER 常量，prd/spec 6 列字面 1:1 对齐
# 与 spec 端 `check_version_changelog` markdown 解析路径正交（HTML regex 直扫）
DOC_CHANGELOG_SECTION_RE = re.compile(
    r'<section\s+id="doc-changelog">(.*?)</section>', re.DOTALL
)
DOC_CHANGELOG_THEAD_RE = re.compile(
    r'<thead><tr>(.*?)</tr></thead>', re.DOTALL
)
DOC_CHANGELOG_TH_RE = re.compile(r'<th[^>]*>(.*?)</th>')
DOC_CHANGELOG_EMPTY_COLSPAN_RE = re.compile(
    r'<td\s+colspan="(\d+)"[^>]*>暂无变更记录</td>'
)


def check_prd_doc_changelog_columns(prd_path: Path, r: Report) -> None:
    """G-02 [MUST] 校验 prd.html doc-changelog 6 列对齐 spec/G-02。

    - 真源：`rule_hard_constraints.md G-02`（6 列固定字面）
    - 派生：`gen_scaffold.build_changelog_page` 注入 prd.html
    - spec 端 markdown 校验由 `check_version_changelog` 负责（precheck_common）
    - 本函数专扫 prd.html HTML 端 `<section id="doc-changelog">` 的 thead + colspan

    校验逻辑：
        1. 找 `<section id="doc-changelog">` 段
        2. 提取 thead 列名 → 必须等于 EXPECTED_CHANGELOG_HEADER（6 列 1:1）
        3. 空 changelog 占位 colspan 必须 = 6（与 thead 列数对齐）
    """
    r.section("G-02 prd.html doc-changelog 6 列校验（NB-WE-21 摘账）")

    if not prd_path.exists():
        r.warn(f"[G-02-prd] prd 文件不存在: {prd_path}, 跳过校验")
        return

    content = prd_path.read_text(encoding="utf-8")

    section_match = DOC_CHANGELOG_SECTION_RE.search(content)
    if not section_match:
        r.fail(
            "[G-02-prd] 未找到 <section id=\"doc-changelog\"> "
            "（gen_scaffold.build_changelog_page 应注入此 section）"
        )
        return
    section_html = section_match.group(1)

    thead_match = DOC_CHANGELOG_THEAD_RE.search(section_html)
    if not thead_match:
        r.fail(
            "[G-02-prd] doc-changelog section 内未找到 <thead><tr>...</tr></thead>"
        )
        return
    th_cols = [c.strip() for c in DOC_CHANGELOG_TH_RE.findall(thead_match.group(1))]

    if th_cols != EXPECTED_CHANGELOG_HEADER:
        r.fail(
            f"[G-02-prd] doc-changelog thead 列名/列数错误: 实际 {th_cols}; "
            f"期望 {EXPECTED_CHANGELOG_HEADER}（对齐 spec/G-02 字面）"
        )
        return
    r.ok("prd doc-changelog thead 6 列字面与 spec/G-02 一致")

    # 空 changelog 占位的 colspan 校验（与 thead 列数对齐）
    empty_match = DOC_CHANGELOG_EMPTY_COLSPAN_RE.search(section_html)
    if empty_match:
        colspan = int(empty_match.group(1))
        if colspan != 6:
            r.fail(
                f"[G-02-prd] 空 changelog 占位 colspan={colspan}, "
                f"期望 6 (与 thead 列数一致)"
            )
            return
        r.ok("空 changelog 占位 colspan=6 与 thead 6 列对齐")


# ── 校验 13｜spec/prd v0.1 行 6 cell 字面一致校验（G-02 SSOT 同源治本，2026-06-02）─

# 治"SPEC_FOOTER 硬编码（today + 空 reviewer）vs build_changelog_page 消费 scaffold.json"
# 二模板源不一致导致 spec v0.1 行 ≠ prd v0.1 行；本 check 校验同源后 v0.1 行 6 cell 字面对齐
SPEC_V01_ROW_RE = re.compile(r"^\|\s*v0\.1\s*\|(.*?)\|", re.MULTILINE)
PRD_V01_ROW_RE = re.compile(
    r'<tr>\s*<td>v0\.1</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*'
    r'<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>',
    re.DOTALL,
)


def _parse_spec_v01_cells(content: str) -> list[str] | None:
    """从 spec.md ## 变更记录段提取 v0.1 行的 6 个 cell（去首尾空格）。"""
    # 找 spec markdown 表行：| v0.1 | ... |
    pattern = re.compile(r"^\|\s*v0\.1\s*\|(.+?)\|\s*$", re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return None
    # 拆分剩余 5 cell（去掉首尾 |）+ "v0.1" 共 6 cell
    inner = match.group(1)
    cells = [c.strip() for c in inner.split("|")]
    if len(cells) != 5:  # 期望 5 cell（v0.1 已单独提取）
        return None
    return ["v0.1"] + cells


def _parse_prd_v01_cells(content: str) -> list[str] | None:
    """从 prd.html doc-changelog section 提取 v0.1 行的 6 个 cell（去 HTML 标签）。"""
    match = PRD_V01_ROW_RE.search(content)
    if not match:
        return None
    cells = ["v0.1"] + [g.strip() for g in match.groups()]
    return cells


def check_spec_prd_v01_row_parity(spec_path: Path, prd_path: Path, r: Report) -> None:
    """G-02 [MUST] 校验 spec.md v0.1 行 6 cell 字面 与 prd.html v0.1 行字面对齐。

    治"二模板源（SPEC_FOOTER 硬编码 vs build_changelog_page JSON 消费）不一致"根因；
    SSOT #61 设计盲区揭示后落地（2026-06-02 NB-CHANGELOG-SCAFFOLD-DERIVATION-MISMATCH
    治本，配套 assemble.py _build_spec_changelog_rows 同源 scaffold.json["changelog"]）。

    校验：spec/prd v0.1 行 6 cell 字面一一对应（含变更内容 / 变更原因 / 变更人 / 审核人 / 日期）。
    """
    r.section("G-02 spec/prd v0.1 行 6 cell 字面一致校验（NB-CHANGELOG-SCAFFOLD 摘账）")

    if not spec_path.exists() or not prd_path.exists():
        r.warn("[G-02-parity] spec 或 prd 文件不存在，跳过校验")
        return

    spec_content = spec_path.read_text(encoding="utf-8")
    prd_content = prd_path.read_text(encoding="utf-8")

    spec_cells = _parse_spec_v01_cells(spec_content)
    prd_cells = _parse_prd_v01_cells(prd_content)

    if spec_cells is None:
        r.fail("[G-02-parity] spec.md ## 变更记录段未找到 v0.1 行（应有 | v0.1 | ... | 6 cell）")
        return
    if prd_cells is None:
        r.fail("[G-02-parity] prd.html doc-changelog 未找到 v0.1 行（应有 <tr><td>v0.1</td>... 6 cell）")
        return

    if spec_cells != prd_cells:
        diffs = []
        col_names = ["版本", "变更内容", "变更原因", "变更人", "审核人", "日期"]
        for i, (s, p) in enumerate(zip(spec_cells, prd_cells)):
            if s != p:
                diffs.append(f"  - 列{i+1}「{col_names[i]}」: spec=`{s}` ≠ prd=`{p}`")
        r.fail(
            "[G-02-parity] spec/prd v0.1 行字面不一致（违反 G-02 [MUST] SSOT 同源）:\n"
            + "\n".join(diffs)
            + "\n  根因：assemble.py SPEC_FOOTER 应消费 scaffold.json[\"changelog\"]"
            + "（同 build_changelog_page），不应硬编码 today + 空 reviewer。"
        )
        return
    r.ok(
        f"spec/prd v0.1 行 6 cell 字面一致（SSOT 同源 scaffold.json[\"changelog\"]）: "
        f"{spec_cells}"
    )


# ── 校验 14｜scaffold.json["changelog"] SSOT #48 合规校验（2026-06-02 治本）─

# 治"quotation-tool 等历史仓 scaffold.json changelog 含 v1.x 开发态散文违反 SSOT #48"根因
# SSOT #48 阶段 4 SemVer：v0.1 启动 / v0.1→v1.0 首次终审 / v1.0 后 vX.0 主版本 三种触发
SSOT48_VERSION_RE = re.compile(r"^v(0\.1|1\.0|[2-9]\.0|[1-9][0-9]+\.0)$")


def check_scaffold_changelog_ssot48_compliance(scaffold_path: Path, r: Report) -> None:
    """SSOT #48 [MUST] 校验 scaffold.json["changelog"] 版本号合规性。

    历史遗留场景：v0.1 期间 PM 在 scaffold.json["changelog"] 填 v1.1/v1.2 等
    开发态内部迭代分版本（违反 SSOT #48 v0.1 期间不升版本号规则）→ 重 assemble
    会让 spec 末尾被这些散文行污染（assemble.py _build_spec_changelog_rows
    SSOT #48 防御会 fallback，但 precheck 在此点拦截让 PM 显式清理）。

    校验：每条 changelog version ∈ {v0.1, v1.0, vN.0 N≥2}；违规 FAIL + 列清单。
    """
    r.section("SSOT #48 scaffold.json changelog 版本号合规校验")

    if not scaffold_path.exists():
        r.warn(f"[SSOT-48] scaffold.json 不存在: {scaffold_path}, 跳过校验")
        return

    try:
        data = json.loads(scaffold_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        r.fail(f"[SSOT-48] scaffold.json 解析失败: {e}")
        return

    changelog = data.get("changelog", [])
    if not changelog:
        r.ok("scaffold.json 无 changelog（assemble 会用 fallback v0.1 行）")
        return

    violations = []
    for i, e in enumerate(changelog):
        version = e.get("version", "")
        if not SSOT48_VERSION_RE.match(version):
            violations.append(f"[{i}] version={version!r}")

    if violations:
        r.fail(
            f"[SSOT-48] scaffold.json[\"changelog\"] 含 {len(violations)} 条违反 SSOT #48"
            f" SemVer 版本号（仅允许 v0.1/v1.0/vN.0 N≥2）:\n  "
            + "\n  ".join(violations)
            + "\n  治本：清理 scaffold.json[\"changelog\"] 仅保留 v0.1/v1.0/vX.0；"
            + "历史 v1.x 开发态散文属 v0.1 期间内部循环（按 SSOT #48）不应入 changelog。"
        )
        return
    r.ok(
        f"scaffold.json changelog {len(changelog)} 条版本号全合规 SSOT #48"
        f"（v0.1/v1.0/vN.0）"
    )


def check_scaffold_version_changelog_consistency(scaffold_path: Path, r: Report) -> None:
    """S4-65 v1（议题 20 / NB-WE-2A-R8-03 P1）— scaffold.json `version` 与 `changelog`
    末行 `version` 一致性校验（WARN）。

    背景：私域主页 R8-03 实证 scaffold.json["version"] = "v4.0"（PM 历史遗留粗粒度填法）
    vs changelog 末行 version = "v0.1"（SSOT #48 合规填法）→ 重 assemble 时 prd 封面
    cover-version 取错源致下游误判产品 release 状态。

    治本三层：
    1. 派生层：assemble.py `_overwrite_cover_version_from_scaffold_changelog` 强制对齐
       封面字面到 changelog 末行真源（议题 20 派生兜底）
    2. 校验层（本规则 S4-65 WARN）：检测 scaffold 内部不一致 → 提示 PM 在 changelog
       追加变更记录（治根因，让 scaffold["version"] 跟随真实 release 节奏前进）
    3. 教育层（议题 21）：派发 prompt 显式禁占位字面 + PM 自审清单

    判定：
    - scaffold["version"] == changelog[-1]["version"] → PASS
    - 不一致 → WARN（不阻断；rollout 阶段 [Recommended]）

    rollout：WARN 阶段对齐 dry-run 纪律；3 仓实测 + FP < 30% 后再考虑升 FAIL。
    详 rule_hard_constraints.md §S4-65 + assemble.py
    `_overwrite_cover_version_from_scaffold_changelog`。
    """
    r.section("S4-65 v1 scaffold.json version ↔ changelog 末行 version 一致性（议题 20，WARN 阶段）")

    if not scaffold_path.exists():
        r.warn(f"[S4-65] scaffold.json 不存在：{scaffold_path}，跳过校验")
        return

    try:
        data = json.loads(scaffold_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        r.warn(f"[S4-65] scaffold.json 解析失败：{e}，跳过校验")
        return

    scaffold_version = (data.get("version") or "").strip()
    changelog = data.get("changelog", [])

    if not scaffold_version:
        r.warn("[S4-65] scaffold.json 无 `version` 字段，跳过一致性校验")
        return
    if not changelog:
        r.warn("[S4-65] scaffold.json[\"changelog\"] 为空，跳过一致性校验")
        return

    last_entry = changelog[-1]
    if not isinstance(last_entry, dict):
        r.warn("[S4-65] scaffold.json[\"changelog\"] 末行格式非 dict，跳过一致性校验")
        return

    changelog_last_version = (last_entry.get("version") or "").strip()
    if not changelog_last_version:
        r.warn("[S4-65] scaffold.json[\"changelog\"] 末行无 `version` 字段，跳过一致性校验")
        return

    if scaffold_version == changelog_last_version:
        r.ok(
            f"scaffold.json `version` 与 `changelog` 末行 `version` 一致："
            f"{scaffold_version}（S4-65 PASS）"
        )
        return

    r.warn(
        f"[S4-65] scaffold.json `version`={scaffold_version!r} 与 `changelog` 末行 "
        f"`version`={changelog_last_version!r} 不一致；"
        f"治本：①若 changelog 末行落后 → 在 changelog 追加当前 release 行（SSOT #48 仅允许 "
        f"v0.1 / v1.0 / vN.0 三类触发点）；②若 scaffold[\"version\"] 落后 → "
        f"按真实 release 节奏推进；assemble.py 派生层（议题 20）会强制对齐封面字面到 "
        f"changelog 末行真源。"
        f"（WARN 阶段，3 仓 dry-run + FP < 30% 后升 FAIL）"
    )


# ── S4-66｜§A-04.2 业务流程图双视图三件套（议题 25，SSOT #30 派生方完整化）──
# 治"Foundation Agent 漏实现 §A-04.2 双视图规范"漏洞：报价工具 outputs/prd L3820-3900 实证可做对
# / 私域 outputs/prd 完全缺三件套（仅裸 <pre class="mermaid">，缺 toggle/table/flow-view 包装）。
# 规范 prd_expression_standard.md §A-04.2 [Must]：spec-business-flow section 内每个含 mermaid 的
# spec-block 必同构复刻 A-04.1 用户旅程三件套（journey-toggle + journey-table-view + journey-flow-view）。
# WARN 阶段对齐 dry-run 纪律（SSOT #60）；3 仓 dry-run + FP<30% 后升 FAIL。
# 详 rule_hard_constraints.md §S4-66 + prd_expression_standard.md §A-04.2 + ssot_anchors.md #30。
def check_spec_business_flow_double_view(prd_html: str, r: Report) -> None:
    """S4-66 v1 — §A-04.2 业务流程图 spec-block 双视图三件套校验（WARN，议题 25）。

    校验 PRD `<section id="spec-business-flow">` 内每个含 `<pre class="mermaid">` 的
    spec-block 必同时含三件套字面：journey-toggle / journey-table-view / journey-flow-view。

    与 SSOT #30 既有 check 互补：
    - `check_business_flow_in_spec`：阶段 2 §二 ↔ spec §3.4 mermaid 数对称（已实现）
    - `check_business_flow_in_prd`：阶段 2 §二 ↔ prd `<pre class="mermaid">` 块数对称（已实现）
    - `check_spec_business_flow_double_view`：prd 三件套齐全（本规则新增，补 §A-04.2 双视图维度）

    豁免：spec-business-flow section 不存在（无业务流程图需求）/ section 内无 mermaid 块。
    """
    r.section("S4-66 v1 §A-04.2 业务流程图双视图三件套（WARN 阶段，议题 25）")

    section_match = re.search(
        r'<section\s+id\s*=\s*"spec-business-flow"[^>]*>(.*?)</section>',
        prd_html,
        re.DOTALL | re.IGNORECASE,
    )
    if not section_match:
        r.ok(
            "[S4-66] PRD 无 `<section id=\"spec-business-flow\">`，"
            "跳过本校验（由 check_business_flow_in_prd 处理 SSOT #30 同步）"
        )
        return

    section_html = section_match.group(1)
    spec_blocks = re.split(r'<div\s+class="spec-block"', section_html)[1:]

    if not spec_blocks:
        r.warn(
            "[S4-66] `<section id=\"spec-business-flow\">` 内无 `<div class=\"spec-block\">`，"
            "跳过校验（建议 Foundation 按 §A-04.2 补三类子 spec-block）"
        )
        return

    violations = []  # [(block_label, missing_list)]
    total_with_mermaid = 0

    for i, block_html in enumerate(spec_blocks, 1):
        if not re.search(r'<pre\s+class="mermaid"', block_html, re.IGNORECASE):
            continue

        total_with_mermaid += 1

        h3_match = re.search(r'<h3[^>]*>(.*?)</h3>', block_html, re.DOTALL | re.IGNORECASE)
        block_label = (
            re.sub(r'\s+', ' ', h3_match.group(1)).strip()[:50]
            if h3_match
            else f"第 {i} 个 spec-block"
        )

        missing = []
        if not re.search(r'class="journey-toggle"', block_html, re.IGNORECASE):
            missing.append("journey-toggle")
        if not re.search(r'class="journey-table-view"', block_html, re.IGNORECASE):
            missing.append("journey-table-view")
        if not re.search(r'class="journey-flow-view"', block_html, re.IGNORECASE):
            missing.append("journey-flow-view")

        if missing:
            violations.append((block_label, missing))

    if total_with_mermaid == 0:
        r.ok(
            "[S4-66] `<section id=\"spec-business-flow\">` 内无含 mermaid 的 spec-block，"
            "跳过本校验"
        )
        return

    if not violations:
        r.ok(
            f"[S4-66] PRD A-04.2 业务流程图 {total_with_mermaid} 个 spec-block "
            f"双视图三件套齐全（WARN 阶段 PASS）"
        )
    else:
        for block_label, missing in violations:
            r.warn(
                f"[S4-66] PRD A-04.2 业务流程图「{block_label}」spec-block 含 mermaid 但缺三件套："
                f"{' / '.join(missing)} —— 按 prd_expression_standard.md §A-04.2 [Must] "
                f"同构复刻 A-04.1 用户旅程三件套（journey-toggle + journey-table-view + journey-flow-view），"
                f"Foundation Agent 漏实现，需补完（参 bujue-quotation-tool outputs/prd L3820-3900 实证）"
            )


# ── S4-68｜spec/prd 正文禁内联变更标记（SSOT #79）──────────────────────────────────
# 真源 = rule_hard_constraints.md §S4-68 + proto_spec_md.md / prd_expression_standard.md。
# WARN-only（既有下游普遍含历史标记，渐进清理；≥2 仓反馈 + FP<30% 再议升 FAIL）。
# pattern 单源自 strip_inline_change_markers.py（清理侧工具 + 校验侧复用同一 pattern）。
def check_no_inline_change_markers(spec_text: str, prd_html: str, r: Report) -> None:
    """S4-68 v1 — spec/prd 正文内联变更 / 过程标记检测（WARN，SSOT #79）。

    变更历史只应进「变更记录表 + git」，正文禁内联标记（如 【v4.0 新增】/
    【历史留痕 …】/（CR-20260609-01 新增）/（议题 #2 …）/（SSOT #61 …）），
    这些把内部追溯泄漏进下游可读正文。schema 标记（【触发态】【组件】【区域】
    【字段回显】【业务定位】…）+ 派生溯源标注（（来源：…））+ workflow 信号
    （【✅ PM 自审完成…】）不在此列（pattern 已排除）。定位用 strip_inline_change_markers.py
    （只读报告，删除 PM 手动做——机械删除会损伤语义）。查版本差异用 git diff。
    """
    r.section("S4-68 spec/prd 正文禁内联变更标记（WARN 阶段，SSOT #79）")
    # 检测 + 文案单源自 strip_inline_change_markers.warn_inline_markers（stage1/2/3/4 共用）
    warn_inline_markers("spec.md", spec_text, r)
    warn_inline_markers("prd.html", prd_html, r)


# ── i18n 最小化校验（NB-阶段4-D 闭环, B+ 档位） ──────────────────────────────
# 真源：`pm-workflow/rules/prd_expression_standard.md §十`（多语言触发条件 + 用法）
# 派生：本检查在「产品定义含多语言需求」条件下兜底「prd.html data-zh 数 = 0」的 BLOCK
# 工具配套：`pm-workflow/scripts/add_i18n.py` (extract / inject 双模式)
# ── S4-28 v3｜统一底栏 .fb-action-bar 结构 + deprecation + 移动端 frame 禁令 ──
# v3 升级（CSS 变量继承机制）：扫 .fb-action-bar + 3 deprecated 别名（fb-frame-bottom-bar /
# fb-modal-footer / fb-drawer-footer），按父链路（含祖先）判定行为合规性：
#   ① 移动端 frame（phone/h5/miniprogram）直接子层 → WARN（违 proto_cross_platform §三）
#   ② deprecated 别名命中 → WARN 提示迁移到 .fb-action-bar
# v2 结构层"父元素必须是 desktop/tablet-frame"约束 v3 放宽（CSS 变量继承支持任意嵌套深度 + modal/drawer 内底栏）。
# WARN 阶段对齐 dry-run 纪律；下游迁移完成后升 FAIL。
# 详 rule_hard_constraints.md §S4-28 v3 + fb-fallback-manifest.md §3.11。
def check_desktop_sticky_completeness(prd_html: str, r: Report) -> None:
    """S4-28 v3 — .fb-action-bar 结构合规 + deprecated 别名迁移 + 移动端 frame 禁令(零启发式,WARN)。

    规则（v3 三层）:
      ① 扫 .fb-action-bar 及 3 deprecated 别名（fb-frame-bottom-bar /
         fb-modal-footer / fb-drawer-footer），统计每个命中元素的祖先链
      ② 移动端 frame（phone/h5/miniprogram）直接子层禁用底栏 → WARN
         （违 proto_cross_platform §三 设计哲学；例外：嵌套在 modal/drawer 内可用）
      ③ deprecated 别名命中 → WARN 提示迁移到 .fb-action-bar

    判定优先级:祖先链先找 .fb-modal / .fb-drawer → 静态行为（不报移动端 WARN）;
    否则找 .{phone|h5|miniprogram}-frame → 报移动端 WARN;
    否则视为合法 frame（desktop/tablet）内底栏 OK。

    rollout: WARN 阶段（下游迁移缓冲）;0 命中 = 下游未使用底栏,正常非 bug。
    下游迁移完成后升 FAIL（同步 rule_hard_constraints §S4-28 + dry-run 纪律）。

    v1 启发式 2026-05-15 同日下线（5/5 false positive）;
    v2 真源 class 匹配（.fb-frame-bottom-bar 仅 desktop/tablet）;
    v3 升级 CSS 变量继承（.fb-action-bar 单类覆盖 frame/modal/drawer）。
    详 rule_hard_constraints.md §S4-28 v3。
    """
    from html.parser import HTMLParser

    # v3 类集合：新统一类 + 3 deprecated 别名
    BAR_CLASSES = {
        "fb-action-bar",
        "fb-frame-bottom-bar",
        "fb-modal-footer",
        "fb-drawer-footer",
    }
    DEPRECATED_ALIASES = {
        "fb-frame-bottom-bar",
        "fb-modal-footer",
        "fb-drawer-footer",
    }
    # 命名覆盖容器（祖先链含此 → 静态行为，无移动端 WARN）
    OVERRIDE_CONTAINERS = {"fb-modal", "fb-drawer"}
    # 移动端 frame 直接子层禁令（祖先链含此 + 无 modal/drawer 覆盖 → WARN）
    MOBILE_FRAMES = {"phone-frame", "h5-frame", "miniprogram-frame"}
    # v3 R2 升级（2026-05-30）：移动 frame 内 .fb-action-bar 合规白名单（按 PM 自报 data-purpose 判定）
    # page-main: 详情页主操作（≤ 4 并列，配合 navbar data-variant=detail/edit）
    # multi-select-batch: 多选态批量操作（≤ 3 并列，配合 navbar data-variant=multi-select）
    # workflow-nav: 向导上一步/下一步（配合 navbar data-variant=workflow）
    # 详 rule_hard_constraints.md §S4-28 v3 R2 + proto_cross_platform.md §三 v2
    PURPOSE_WHITELIST = {"page-main", "multi-select-batch", "workflow-nav"}

    class _Parser(HTMLParser):
        _SELF_CLOSING = {"br", "img", "input", "meta", "link", "hr", "source"}

        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.stack: list[dict] = []
            self.bar_count = 0
            self.mobile_violations: list[tuple[int, str, str]] = []  # (lineno, used_class, data_purpose)
            self.deprecated_uses: list[tuple[int, str]] = []  # (lineno, deprecated_class)

        def handle_starttag(self, tag, attrs):
            attrs_d = {k: (v or "") for k, v in attrs}
            classes = set((attrs_d.get("class") or "").split())
            # 命中 BAR_CLASSES 任一 → 进入校验
            hit = classes & BAR_CLASSES
            if hit:
                self.bar_count += 1
                used = sorted(hit)[0]  # 命中类（多个时取字典序首位用于报告）
                lineno = self.getpos()[0]
                # ③ deprecation 检查
                dep_hit = hit & DEPRECATED_ALIASES
                if dep_hit:
                    self.deprecated_uses.append((lineno, sorted(dep_hit)[0]))
                # ② v3 R2 升级：移动端 frame 直接子层按 data-purpose 白名单判定
                # 白名单 ∈ {page-main, multi-select-batch, workflow-nav} → 合规
                # 其他场景 → WARN（提示加 data-purpose 或改 navbar variant）
                ancestor_classes: set[str] = set()
                for anc in self.stack:
                    ancestor_classes |= anc["classes"]
                in_override = bool(ancestor_classes & OVERRIDE_CONTAINERS)
                in_mobile_frame = bool(ancestor_classes & MOBILE_FRAMES)
                if in_mobile_frame and not in_override:
                    # v3 R2: 读 data-purpose 属性判定（缺省 → 不在白名单 → WARN）
                    data_purpose = (attrs_d.get("data-purpose") or "").strip()
                    if data_purpose not in PURPOSE_WHITELIST:
                        self.mobile_violations.append((lineno, used, data_purpose))
            if tag in self._SELF_CLOSING:
                return
            self.stack.append({"tag": tag, "classes": classes})

        def handle_endtag(self, tag):
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i]["tag"] == tag:
                    self.stack = self.stack[:i]
                    return

    p = _Parser()
    try:
        p.feed(prd_html)
    except Exception as e:  # noqa: BLE001
        r.warn(f"[S4-28 v3] HTML 解析异常,跳过 .fb-action-bar 结构校验:{e}")
        return

    r.section(
        "S4-28 v3 .fb-action-bar 结构合规 + deprecated 迁移(零启发式,WARN 阶段)"
    )
    if p.bar_count == 0:
        r.ok(
            "未发现 .fb-action-bar 或 3 deprecated 别名(下游未使用底栏属正常,非 bug;"
            "使用后本检查校验①移动端 frame 直接子层禁令 ②deprecated 别名迁移)"
        )
        return

    # ② 移动端 frame 直接子层 WARN（v3 R2 升级：按 data-purpose 白名单判定）
    for lineno, used, data_purpose in p.mobile_violations:
        purpose_hint = f"（当前 data-purpose=\"{data_purpose}\"）" if data_purpose else "（无 data-purpose）"
        r.warn(
            f"[S4-28 v3 R2] .{used} L{lineno} 在移动端 frame 内（phone/h5/miniprogram）"
            f"直接子层使用{purpose_hint}— 不在合规白名单 "
            f"{{page-main, multi-select-batch, workflow-nav}}；"
            f"修复路径：① 详情页主操作 → 加 data-purpose=\"page-main\" + navbar "
            f"data-variant=\"detail\"/\"edit\"；② 多选态批量 → 加 "
            f"data-purpose=\"multi-select-batch\" + navbar data-variant=\"multi-select\"；"
            f"③ 向导上/下一步 → 加 data-purpose=\"workflow-nav\" + navbar "
            f"data-variant=\"workflow\"；其他场景 → 改走 navbar variant + 「···」菜单"
            f"或嵌套 modal/drawer 内。详 rule_hard_constraints.md §S4-28 v3 R2 + "
            f"proto_cross_platform.md §三 v2（WARN 阶段，下游迁移完升 FAIL）"
        )

    # ③ deprecated 别名迁移 WARN
    for lineno, dep in p.deprecated_uses:
        r.warn(
            f"[S4-28 v3] .{dep} L{lineno} 已 deprecated（v3 别名仍生效，无视觉差异）；"
            f"请改用 .fb-action-bar（单类覆盖 frame/modal/drawer 三场景，"
            f"CSS 变量就近继承自动切换行为）。可用 pm-workflow/scripts/migrate_action_bar.py 自动迁移。"
            f"详 fb-fallback-manifest.md §3.11"
        )

    # 整体合规态
    if not p.mobile_violations and not p.deprecated_uses:
        r.ok(
            f".fb-action-bar × {p.bar_count} 全部合规（无移动端 frame 直接子层违规 + 无 deprecated 别名使用）"
            f" — v3 CSS 变量继承机制按 DOM 最近祖先自动切换行为"
        )


# ── S4-28 v2 档 C 第 3 条补充｜inline position:fixed/sticky 字面扫描 ────────────
# zero-heuristic 字面扫描（mirror check_z_index_compliance 模式）：扫 style="..." 中
# position:fixed / position:sticky 字面 → WARN。不判定"哪些 div 是底栏"（对齐 S4-28 v1
# 启发式 5/5 false-positive 同日下线教训）；治反向规避路径——PM 完全不用 .fb-frame-bottom-bar
# 转手写 inline `style="position:fixed"` 实现底栏即完全规避 check_desktop_sticky_completeness
# 的盲区（quotation-tool L8705 实证）。WARN 阶段对齐 S4-28 自身 dry-run 纪律。
# 详 rule_hard_constraints.md §S4-28 第 3 条 + fb-fallback-manifest.md §3.11。
def check_inline_position_compliance(prd_html: str, r: Report) -> None:
    """S4-28 v2 档 C 第 3 条补充 — inline `style="position:fixed/sticky"` 字面扫描（零启发式，WARN）。

    SSOT 真源：rule_hard_constraints.md §S4-28 第 3 条
    禁令：禁止 PM 在元素 `style="..."` 中写 `position:fixed` / `position:sticky`——
    sticky 贴底由 `.fb-frame-bottom-bar` pub 组件真源 CSS 自带；inline 写法
    ①等价于绕过组件协议 ②复现 v1 inline 污染（outputs L18812/L19350 等 5 处教训）。

    零启发式（对齐 S4-28 v2 教训）：不判定"哪些 div 应是底栏"（v1 启发式 5/5 FP 教训）；
    仅扫 style 属性字面值 → WARN，让 PM/Supervisor 看具体行号 + 上下文人审定夺
    （合法底栏走 .fb-frame-bottom-bar class，自动豁免；inline position 写法在 PRD 静态
    原型中正常无合法场景）。

    WARN 阶段：对齐 S4-28 v2 档 C dry-run 纪律（≥ 2 下游实测 + FP < 30% 后升 FAIL）；
    与 check_desktop_sticky_completeness 共同覆盖 S4-28 双层（结构 + inline style）。
    """
    r.section("inline position 字面扫描（S4-28 v3 第 3 条，WARN）")

    illegal_occurrences: list[tuple[int, str, str]] = []  # (line_num, prop, context)
    # 扫 style="..." 中 position:fixed / position:sticky（容忍空白 + 大小写不敏感）
    style_attr_re = re.compile(r'style\s*=\s*"([^"]*)"')
    pos_re = re.compile(r'position\s*:\s*(fixed|sticky)\b', re.IGNORECASE)

    for m in style_attr_re.finditer(prd_html):
        style_content = m.group(1)
        for pm in pos_re.finditer(style_content):
            prop = f"position:{pm.group(1).lower()}"
            # 计算行号 + 上下文（本行）
            line_num = prd_html[:m.start()].count("\n") + 1
            line_start = prd_html.rfind("\n", 0, m.start()) + 1
            line_end = prd_html.find("\n", m.end())
            if line_end == -1:
                line_end = len(prd_html)
            context = prd_html[line_start:line_end].strip()
            if len(context) > 120:
                context = context[:120] + "..."
            illegal_occurrences.append((line_num, prop, context))

    if not illegal_occurrences:
        r.ok("PRD 中无 inline `style=\"position:fixed/sticky\"` 字面违规（S4-28 第 3 条 PASS）")
        return

    r.warn(
        f"PRD 中 {len(illegal_occurrences)} 处 inline `style=\"...position:fixed/sticky...\"` "
        f"（S4-28 v3 第 3 条违规，WARN 阶段）：\n  "
        + "\n  ".join(
            f"line {ln}: {prop} | 上下文: {ctx}"
            for ln, prop, ctx in illegal_occurrences[:10]
        )
        + (f"\n  （共 {len(illegal_occurrences)} 处，仅显示前 10 条）"
           if len(illegal_occurrences) > 10 else "")
        + f"\n修复方向：底栏须用 pub 组件 `.fb-action-bar`（v3 统一类，真源 CSS 变量 "
        f"就近继承自动切换 frame/modal/drawer 行为），PRD 中 inline `style=\"position:fixed\"` "
        f"等价于绕过组件协议；详 rule_hard_constraints.md §S4-28 v3 + fb-fallback-manifest.md §3.11"
    )


# ── S4-35｜移动端次级页面顶部导航栏 .fb-navbar 返回入口完整性 ──────────────────
# 零启发式结构校验(mirror S4-28 v2):keys off .fb-navbar 组件存在性,不做"次级页面"
# 页面类型推断(scaffold 无 level/parent 字段支撑,page_archetypes 自由命名 → 高 FP,
# 对齐 S4-28 v1 启发式 5/5 false-positive 同日下线教训)。扫 .fb-navbar:① 须为移动类
# *-frame 直接子元素(否则 sticky 贴顶失效);② 须含 .fb-nav-back 后代(否则用户无路可返)。
# WARN 阶段(下游迁移缓冲):0 命中 = 下游未迁移,正常非 bug;迁移完升 FAIL。
# 详 rule_hard_constraints.md §S4-35 + fb-fallback-manifest.md §3.12。
def check_back_entry(prd_html: str, r: Report) -> None:
    """S4-35 v2 — .fb-navbar 7 variant + 返回入口完整性(按 data-variant 字面判定,
    零启发式,WARN 阶段)。

    v2 升级（2026-05-30 落地）：
      ① 结构约束(不变):.fb-navbar 必须是移动类 *-frame(phone/h5/miniprogram/
         tablet-frame)的直接子元素。
      ② 7 variant + .fb-nav-back 强制范围:
         - detail（默认）/ workflow → 强制含 .fb-nav-back（缺 → WARN）
         - multi-select / confirm / edit / list / home → 不强制
           （用 [取消]/[完成] 等替代）
      ③ data-variant 显式声明: PM 写 .fb-navbar 时应加 data-variant="XXX"
         属性;缺省 → 默认 detail（向后兼容现有 21 处用法）。

    设计：零启发式 + 严格按 data-variant 字面判定（避免 v1 启发式 5/5 FP 教训）。
    向后兼容：缺省 data-variant 等同 detail（强制 .fb-nav-back）。

    rollout：WARN 阶段（下游迁移缓冲）；0 命中 = 下游未迁移正常非 bug。
    下游迁移完成后升 FAIL。详 rule_hard_constraints.md §S4-35 v2 + manifest §3.12 v2。
    """
    from html.parser import HTMLParser

    NAVBAR_CLASS = "fb-navbar"
    BACK_CLASS = "fb-nav-back"
    PARENT_OK = {"phone-frame", "h5-frame", "miniprogram-frame", "tablet-frame"}
    # v2: 强制 .fb-nav-back 的 variant（其他 variant 用 [取消]/[完成] 等替代）
    BACK_REQUIRED_VARIANTS = {"detail", "workflow"}
    # v2 合法 variant 全集（用于警示拼写错误）
    VALID_VARIANTS = {
        "detail", "multi-select", "confirm", "edit", "list", "workflow", "home"
    }

    class _Parser(HTMLParser):
        _SELF_CLOSING = {"br", "img", "input", "meta", "link", "hr", "source"}

        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.stack: list[dict] = []
            self.navbar_count = 0
            self.misplaced: list[tuple[int, str]] = []
            self.no_back: list[tuple[int, str]] = []  # v2: (lineno, variant)
            self.invalid_variants: list[tuple[int, str]] = []  # v2: 拼写错误警示

        def handle_starttag(self, tag, attrs):
            attrs_d = {k: (v or "") for k, v in attrs}
            classes = set((attrs_d.get("class") or "").split())
            # 返回入口:标记最近的祖先 navbar 为已含 back
            if BACK_CLASS in classes:
                for e in reversed(self.stack):
                    if e["is_navbar"]:
                        e["has_back"] = True
                        break
            is_navbar = NAVBAR_CLASS in classes
            parent = self.stack[-1] if self.stack else None
            parent_classes = parent["classes"] if parent else set()
            # v2: 读取 data-variant 属性（缺省 detail，向后兼容）
            variant = attrs_d.get("data-variant", "detail").strip() if is_navbar else None
            if is_navbar:
                self.navbar_count += 1
                # v2: 检查 variant 是否合法（拼写错误警示）
                if variant not in VALID_VARIANTS:
                    self.invalid_variants.append((self.getpos()[0], variant))
            if tag in self._SELF_CLOSING:
                return
            self.stack.append({
                "tag": tag,
                "classes": classes,
                "is_navbar": is_navbar,
                "has_back": False,
                "lineno": self.getpos()[0],
                "parent_classes": parent_classes,
                "variant": variant,  # v2 新增
            })

        def _evaluate(self, entry: dict) -> None:
            if not (entry["parent_classes"] & PARENT_OK):
                pc = " ".join(sorted(entry["parent_classes"])) or "—"
                where = (
                    "(无父元素,直接位于文档根)"
                    if not entry["parent_classes"]
                    else f'父元素 class="{pc}"'
                )
                self.misplaced.append((entry["lineno"], where))
            # v2: 按 variant 判定 .fb-nav-back 强制范围
            variant = entry.get("variant", "detail")
            if variant in BACK_REQUIRED_VARIANTS and not entry["has_back"]:
                self.no_back.append((entry["lineno"], variant))

        def handle_endtag(self, tag):
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i]["tag"] == tag:
                    for e in self.stack[i:]:
                        if e["is_navbar"]:
                            self._evaluate(e)
                    self.stack = self.stack[:i]
                    return

    p = _Parser()
    try:
        p.feed(prd_html)
    except Exception as e:  # noqa: BLE001
        r.warn(f"[S4-35 v2] HTML 解析异常,跳过 .fb-navbar 返回入口校验:{e}")
        return
    # 文档结束仍未闭合的 navbar（容错）也评估
    for e in p.stack:
        if e["is_navbar"]:
            p._evaluate(e)

    r.section("S4-35 v2 .fb-navbar 7 variant + 返回入口完整性(零启发式,WARN 阶段)")
    if p.navbar_count == 0:
        r.ok(
            "未发现 .fb-navbar(下游未迁移属正常,非 bug;迁移后本检查按 data-variant "
            "判定 detail/workflow 必含 .fb-nav-back,其他 variant 用 [取消]/[完成] 替代)"
        )
        return
    if not p.misplaced and not p.no_back and not p.invalid_variants:
        r.ok(
            f".fb-navbar × {p.navbar_count} 均为移动类 frame 直接子元素 + "
            f"data-variant 合法 + 按 variant 强制范围含 .fb-nav-back — "
            f"v2 7 variant 合规"
        )
        return
    for lineno, where in p.misplaced:
        r.warn(
            f"[S4-35 v2] .fb-navbar L{lineno} 不是 phone/h5/miniprogram/tablet-frame "
            f"的直接子元素({where})— sticky 贴顶将失效;须置于移动类 frame 直接子层"
            f"首位。详 fb-fallback-manifest.md §3.12 v2(WARN 阶段,下游迁移完升 FAIL)"
        )
    for lineno, variant in p.no_back:
        r.warn(
            f"[S4-35 v2] .fb-navbar L{lineno}[data-variant=\"{variant}\"] 缺 "
            f".fb-nav-back 返回入口 — v2 规定 detail/workflow variant 强制含 "
            f".fb-nav-back;须加 <span class=\"fb-nav-back\" data-tp=\"...\">←</span>。"
            f"详 manifest §3.12 v2(WARN 阶段,下游迁移完升 FAIL)"
        )
    for lineno, variant in p.invalid_variants:
        r.warn(
            f"[S4-35 v2] .fb-navbar L{lineno} data-variant=\"{variant}\" 不在合法集合 "
            f"{sorted(VALID_VARIANTS)} 内 — 拼写错误?默认按 detail 判定。"
            f"详 manifest §3.12 v2 7 variant 矩阵"
        )


# ── S4-36 v1 ┤ data-tp ↔ tp-marker 配对完整性（A 方案 A.1，retro issue #56 235 处实证）──
# 每个 data-tp 元素必有同级或父级 <span class="tp-marker">NN</span>，且 NN = data-tp T/D 编号
# 豁免白名单：showcase-only / is-unchecked / nav-inactive
# WARN 阶段（dry-run 期不阻断），≥ 2 仓 + FP<30% 后升 FAIL
# 详 rule_hard_constraints.md §S4-36 + SSOT #55
def check_tp_marker_pairing(prd_html: str, r: Report) -> None:
    """S4-36 v1 — data-tp ↔ tp-marker 配对完整性校验（A 方案 A.1，WARN 阶段）。

    规则：每个 data-tp="M[XX]-P[YY]-T[ZZ]" 元素必有同级或父级
        <span class="tp-marker">NN</span>，且 NN = data-tp 的 T/D 编号（NN 取 ZZ）。

    豁免白名单（class 含任一关键字即跳过）:
      - showcase-only: showcase 区元素（仅展示，无触点交互）
      - is-unchecked: 未选中 fb-radio（待选触点）
      - nav-inactive: 未选中 nav（待选状态）

    设计:零启发式（按 class + data-tp 字面 + 父链路 marker 查找）。
    rollout:WARN 阶段（dry-run 缓冲），下游迁移完升 FAIL（dry-run ≥ 2 仓 + FP<30%）。
    详 rule_hard_constraints.md §S4-36 + retro 优化方案 A.1（issue #56 235 处实证）。
    """
    from html.parser import HTMLParser

    EXEMPT_PATTERNS = {"showcase-only", "is-unchecked", "nav-inactive"}
    TP_RE = re.compile(r'^M\d+-P\d+-([TDC])(\d+)$')

    class _Parser(HTMLParser):
        _SELF_CLOSING = {"br", "img", "input", "meta", "link", "hr", "source"}

        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.stack: list[dict] = []
            self.tp_elements: list[dict] = []
            # tracking 当前栈每层的 tp-marker（值：NN 字符串）
            self.markers_in_stack: list[list[str]] = []  # 各层 marker 字面 NN

        def handle_starttag(self, tag, attrs):
            attrs_d = {k: (v or "") for k, v in attrs}
            classes = set((attrs_d.get("class") or "").split())
            data_tp = attrs_d.get("data-tp", "").strip()
            lineno = self.getpos()[0]
            # 父链路豁免检查（任一祖先含豁免 class → 跳过）
            ancestor_exempt = False
            for anc in self.stack:
                if anc["classes"] & EXEMPT_PATTERNS:
                    ancestor_exempt = True
                    break
            # 命中 data-tp → 记录待校验
            if data_tp and not (classes & EXEMPT_PATTERNS) and not ancestor_exempt:
                m = TP_RE.match(data_tp)
                if m:
                    tp_kind, tp_num = m.group(1), m.group(2)
                    # 当前元素自身的 marker（同级 marker 在父节点入栈时收集，需要在父级查）
                    self.tp_elements.append({
                        "lineno": lineno,
                        "data_tp": data_tp,
                        "tp_num": tp_num,
                        "tp_kind": tp_kind,
                        "stack_depth": len(self.stack),
                        # parent_markers 在 endtag 时回填（父级闭合前其所有子级 marker 已收集）
                    })
            # 命中 tp-marker → 提取 NN 注册到祖先收集
            if "tp-marker" in classes:
                # 注：tp-marker 文本内容在 handle_data 时获取，但 HTML 简单实现下用 data-mark 属性或文本节点
                # 为简化：先记录占位，文本在 handle_data 收集
                pass
            if tag in self._SELF_CLOSING:
                return
            self.stack.append({
                "tag": tag,
                "classes": classes,
                "data_tp": data_tp,
                "lineno": lineno,
                "child_markers": [],  # 子树中所有 tp-marker 数字
            })

        def handle_data(self, data):
            # 当前栈顶若是 tp-marker 元素，文本即 marker 数字
            if self.stack and "tp-marker" in self.stack[-1]["classes"]:
                num = data.strip()
                # 注册到所有祖先（用于父级匹配）
                for anc in self.stack[:-1]:
                    anc["child_markers"].append(num)
                # 自身也算（用于同级匹配）
                if len(self.stack) >= 2:
                    self.stack[-2]["child_markers"].append(num)

        def handle_endtag(self, tag):
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i]["tag"] == tag:
                    self.stack = self.stack[:i]
                    return

    p = _Parser()
    try:
        p.feed(prd_html)
    except Exception as e:  # noqa: BLE001
        r.warn(f"[S4-36] HTML 解析异常,跳过 tp-marker 配对校验:{e}")
        return

    # 第二轮扫描：用 regex 简化 marker 查找（兼容更多写法 + 替代复杂 HTMLParser 状态）
    # 实际策略：扫每个 data-tp 元素，向其父链路（含同级）找 tp-marker 数字
    # 用简化字符串扫描：以 data-tp= 为锚点，向前 / 向后 ~500 字符内找 tp-marker NN
    tp_pattern = re.compile(
        r'data-tp\s*=\s*"(M\d+-P\d+-[TDC]\d+)"', re.IGNORECASE
    )
    marker_pattern = re.compile(
        r'<span\s+class\s*=\s*"[^"]*\btp-marker\b[^"]*"[^>]*>\s*(\d+)\s*</span>',
        re.IGNORECASE,
    )
    SCAN_RADIUS = 500  # 同级/父级 ±500 字符内查找

    r.section(
        "S4-36 v1 data-tp ↔ tp-marker 配对完整性（A 方案 A.1，零启发式，WARN 阶段）"
    )

    violations: list[tuple[int, str, str]] = []  # (lineno, data_tp, reason)
    tp_count = 0
    for m in tp_pattern.finditer(prd_html):
        full_tp = m.group(1)
        m_re = TP_RE.match(full_tp)
        if not m_re:
            continue
        tp_num = m_re.group(2)
        # 计算行号
        lineno = prd_html[:m.start()].count('\n') + 1
        # 豁免：扫该 data-tp 字符前 ±100 字符内 class 含豁免 pattern
        ctx_before = prd_html[max(0, m.start() - 200):m.start()]
        ctx_after = prd_html[m.end():m.end() + 100]
        full_ctx = ctx_before + ctx_after
        if any(p in full_ctx for p in EXEMPT_PATTERNS):
            continue
        tp_count += 1
        # 在 ±SCAN_RADIUS 字符内找 tp-marker NN
        search_start = max(0, m.start() - SCAN_RADIUS)
        search_end = min(len(prd_html), m.end() + SCAN_RADIUS)
        search_window = prd_html[search_start:search_end]
        found_match = False
        for mm in marker_pattern.finditer(search_window):
            if mm.group(1) == tp_num:
                found_match = True
                break
        if not found_match:
            violations.append((lineno, full_tp, f"在 ±{SCAN_RADIUS} 字符内未找 marker={tp_num}"))

    if tp_count == 0:
        r.ok("PRD 中无 data-tp 元素，跳过 S4-36 校验")
        return
    if not violations:
        r.ok(f"data-tp × {tp_count} 均含配对 tp-marker（S4-36 PASS）")
        return

    for lineno, data_tp, reason in violations[:10]:
        r.warn(
            f"[S4-36] L{lineno} data-tp=\"{data_tp}\" 缺配对 tp-marker — {reason}；"
            f"修复：在同级或父级加 <span class=\"tp-marker\">{data_tp.split('-')[-1][1:]}</span>。"
            f"详 rule_hard_constraints.md §S4-36 + manifest §6 tp-marker（WARN 阶段，下游迁移完升 FAIL）"
        )
    if len(violations) > 10:
        r.warn(f"[S4-36] 共 {len(violations)} 处违规，仅显示前 10 条")


# ── S4-37 v1 ┤ tp-marker tp-wrap 包裹结构（A 方案 A.2，retro issue #53 103 处实证）──
# 所有 <span class="tp-marker"> 必有父级 .tp-wrap（确保 position:relative 定位基准）
# 豁免：tp-marker 父含已 position:relative 容器（显式标 data-tp-no-wrap）
# WARN 阶段，下游迁移完升 FAIL
# 详 rule_hard_constraints.md §S4-37 + SSOT #55
def check_tp_marker_wrap(prd_html: str, r: Report) -> None:
    """S4-37 v1 — tp-marker tp-wrap 包裹结构校验（A 方案 A.2，WARN 阶段）。

    规则：所有 <span class="tp-marker"> 必有父级或祖先（≤2 层）含 .tp-wrap class，
        确保 position:relative 定位基准；否则 marker 飞到 frame 角（issue #53 103 处实证）。

    豁免：tp-marker 自身或父祖先（≤2 层）显式标 data-tp-no-wrap 属性（PM 已确认
        在已 position:relative 容器内）。

    设计:零启发式（按 .tp-wrap class + data-tp-no-wrap 属性双白名单）。
    rollout:WARN 阶段，下游迁移完升 FAIL。
    详 rule_hard_constraints.md §S4-37 + retro 优化方案 A.2（issue #53 103 处实证）。
    """
    r.section(
        "S4-37 v1 tp-marker tp-wrap 包裹结构（A 方案 A.2，零启发式，WARN 阶段）"
    )

    # 扫所有 tp-marker 元素 → 向前 ~300 字符找 tp-wrap 或 data-tp-no-wrap
    marker_full_pattern = re.compile(
        r'<span\s+class\s*=\s*"[^"]*\btp-marker\b[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    # 父级 wrap 检测：向前 200 字符内若有 <... class="...tp-wrap..."> 视为合规
    wrap_pattern = re.compile(
        r'<\w+\s+[^>]*class\s*=\s*"[^"]*\btp-wrap\b[^"]*"',
        re.IGNORECASE,
    )
    no_wrap_attr = "data-tp-no-wrap"
    SCAN_BEFORE = 300  # 父链路向前扫 ~300 字符

    marker_count = 0
    violations: list[int] = []  # lineno
    for m in marker_full_pattern.finditer(prd_html):
        marker_count += 1
        lineno = prd_html[:m.start()].count('\n') + 1
        # 父链路扫：向前 SCAN_BEFORE 字符内找 .tp-wrap 或 data-tp-no-wrap
        search_window = prd_html[max(0, m.start() - SCAN_BEFORE):m.start() + 100]
        if wrap_pattern.search(search_window) or no_wrap_attr in search_window:
            continue
        violations.append(lineno)

    if marker_count == 0:
        r.ok("PRD 中无 .tp-marker 元素，跳过 S4-37 校验")
        return
    if not violations:
        r.ok(
            f".tp-marker × {marker_count} 均含父级 .tp-wrap 或 data-tp-no-wrap "
            f"豁免（S4-37 PASS）"
        )
        return

    for lineno in violations[:10]:
        r.warn(
            f"[S4-37] L{lineno} .tp-marker 缺父级 .tp-wrap 包裹 — marker 将飞到 "
            f"frame 角（position:relative 定位基准缺失）；修复：在父级加 "
            f"<span class=\"tp-wrap\">…</span> 或显式标 data-tp-no-wrap 属性。"
            f"详 rule_hard_constraints.md §S4-37 + manifest §6 tp-marker（WARN 阶段，下游迁移完升 FAIL）"
        )
    if len(violations) > 10:
        r.warn(f"[S4-37] 共 {len(violations)} 处违规，仅显示前 10 条")


# ── S4-38 v1 ┤ PRD section 最小内容粒度（A 方案 A.3，retro issue #57 实证）──
# 每个 <section id="..."> inner 字符数 ≥ 500B（非空壳），避免占位 section（如
# spec-background / spec-data 仅壳）
# 豁免：显式标 <!-- section-shell-by-design: <reason> --> 注释
# WARN 档（[Should]），不阻断
# 详 rule_hard_constraints.md §S4-38 + SSOT #55
def check_section_min_content(prd_html: str, r: Report) -> None:
    """S4-38 v1 — PRD section 最小内容粒度校验（A 方案 A.3，[Should] WARN）。

    规则：每个 <section id="..."> inner 字节数 ≥ 500B；< 阈值且无显式豁免标 → WARN。

    豁免：section 内含 `<!-- section-shell-by-design: <reason> -->` 注释。

    设计:零启发式（字节数 + 注释豁免）；阈值 500B 来源 retro A.3 草案，
    issue #57 spec-background / spec-data 实测仅几十字节空壳触发该 WARN。

    rollout:[Should] WARN 永远不阻断 EXIT=0（不像 A.1/A.2 升 FAIL）。
    详 rule_hard_constraints.md §S4-38 + retro 优化方案 A.3。
    """
    r.section("S4-38 v1 PRD section 最小内容粒度（A 方案 A.3，[Should] WARN）")

    MIN_CONTENT_BYTES = 500
    EXEMPT_MARKER = "section-shell-by-design"

    # 简化解析：用非贪婪正则配对 <section id="..."> ... </section>
    # 不支持嵌套 section（PRD 中 section 通常平铺，不嵌套）
    section_pattern = re.compile(
        r'<section\s+[^>]*id\s*=\s*"([^"]+)"[^>]*>(.*?)</section>',
        re.IGNORECASE | re.DOTALL,
    )

    violations: list[tuple[int, str, int]] = []  # (lineno, section_id, byte_size)
    section_count = 0

    for m in section_pattern.finditer(prd_html):
        section_count += 1
        section_id = m.group(1)
        inner = m.group(2)
        # 显式豁免标 → 跳过
        if EXEMPT_MARKER in inner:
            continue
        # 字节数（UTF-8）— 去掉前后空白后计长
        inner_stripped = inner.strip()
        byte_size = len(inner_stripped.encode('utf-8'))
        if byte_size < MIN_CONTENT_BYTES:
            lineno = prd_html[:m.start()].count('\n') + 1
            violations.append((lineno, section_id, byte_size))

    if section_count == 0:
        r.ok("PRD 中无 <section> 元素，跳过 S4-38 校验")
        return
    if not violations:
        r.ok(
            f"PRD 中 {section_count} 个 <section> 均含 ≥ {MIN_CONTENT_BYTES}B 内容或显式豁免标"
            f"（S4-38 PASS）"
        )
        return

    for lineno, section_id, byte_size in violations[:10]:
        r.warn(
            f"[S4-38] L{lineno} <section id=\"{section_id}\"> inner 内容仅 {byte_size}B "
            f"< 阈值 {MIN_CONTENT_BYTES}B（疑似空壳）；修复：① 补全 section 内容 ② 或加显式"
            f"豁免标 <!-- section-shell-by-design: <reason> --> 注释。"
            f"详 rule_hard_constraints.md §S4-38（[Should] WARN，不阻断 EXIT=0）"
        )
    if len(violations) > 10:
        r.warn(f"[S4-38] 共 {len(violations)} 处违规，仅显示前 10 条")


# ── S4-39 v1 ┤ Mermaid label 字符安全（A 方案 A.4，retro issue #57 EmptyState parse 错实证）──
# 扫所有 mermaid block 节点 label 内：
#  - 双引号未转义（含 mermaid `"..."` 嵌套不安全场景）
#  - 中文标点（，。；："" ''）混入（可能触发 mermaid parse 错或视觉异常）
# WARN 档（[Should]），含修复建议字面
# 详 rule_hard_constraints.md §S4-39 + SSOT #55
def check_mermaid_label_chars(spec_md: str, prd_html: str, r: Report) -> None:
    """S4-39 v1 — Mermaid label 字符安全校验（A 方案 A.4，[Should] WARN）。

    规则：扫所有 mermaid block 节点 label 内：
      - 双引号 `"` 未转义为 `&quot;` / `#quot;` → WARN（mermaid label 内裸 " 可能
        引发括号嵌套 parse 错，如 issue #57 EmptyState label 含 `"..."`）
      - 中文标点（，。；："" '' 等）混入 → WARN（可能触发 parse 错或视觉异常）

    设计:扫各类节点 label 写法（A[label]/A(label)/A{label}/A((label))/A>label]/etc）；
    label 内查 " ' 中文标点字面；忽略 mermaid 关键字（如 ```、graph、subgraph）。

    rollout:[Should] WARN 永远不阻断 EXIT=0；含修复建议（`"..." → '...'` 或
    转义为 `&quot;`）。详 rule_hard_constraints.md §S4-39 + retro 优化方案 A.4。
    """
    r.section("S4-39 v1 Mermaid label 字符安全（A 方案 A.4，[Should] WARN）")

    blocks = _extract_mermaid_blocks(spec_md, prd_html)
    if not blocks:
        r.ok("未检测到 mermaid 块（跳过 S4-39 校验）")
        return

    # 节点 label 模式：A[文字] / A(文字) / A{文字} / A((文字)) / A>文字]
    # 简化：捕所有方/圆/花/双圆/不规则括号内的内容
    # 注：避免捕到边定义如 A -->|label| B（这个 label 在 |...| 中）
    # 主要节点 label 模式
    label_patterns = [
        re.compile(r'\[([^\[\]]+)\]'),  # 方括号 [...]
        re.compile(r'\(([^()]+)\)'),     # 圆括号 (...)
        re.compile(r'\{([^{}]+)\}'),     # 花括号 {...}
        re.compile(r'\|([^|]+)\|'),      # edge label |...|
    ]

    # 中文标点字符（混入 mermaid label 可能触发 parse 错或视觉异常）
    # 注：ASCII 双引号 `"` 在 mermaid 是合法 string literal 包裹符（A["text"]），
    # 不报；仅检测 label 内"嵌套未转义"双引号（出现次数 ≥ 3 或非外围包裹时奇数次）
    CHINESE_PUNCT = {
        '“': "中文左双引号 “",
        '”': "中文右双引号 ”",
        '‘': "中文左单引号 ‘",
        '’': "中文右单引号 ’",
        '，': "中文逗号 ，",
        '。': "中文句号 。",
        '；': "中文分号 ；",
        '：': "中文冒号 ：",
    }

    violations: list[tuple[str, str, str]] = []  # (source, label, reason)

    def _check_nested_quotes(label: str) -> str | None:
        """检测 label 是否含嵌套未转义双引号（issue #57 EmptyState `"..."` parse 错根因）

        v1 严格 → v2 放宽：仅报"奇数个 / ≥ 4 个"未转义双引号，
        因 mermaid subroutine shape `[["..."]]` 内 label 含双引号是合法常见写法。

        非法写法（必触发 parse 错或视觉异常）：
          - 奇数个 " → 必未闭合
          - ≥ 4 个 " → 必嵌套（外围 2 + 内部 ≥ 2）

        其他场景（0 / 2 个）→ 放过，由 S4-33 mermaid mmdc parse 兜底；
        避免 FP（quotation-tool 实测 mermaid subroutine `[["text"]]` 不应 WARN）。
        """
        # 去转义实体后计 " 出现次数
        clean = label.replace('&quot;', '').replace('&#34;', '').replace('&#x22;', '')
        count = clean.count('"')
        if count == 0:
            return None
        if count == 2:
            return None  # mermaid 合法 string literal 或 subroutine 内 label
        if count % 2 != 0:
            return f"label 含 {count} 个未转义双引号（奇数 → 必未闭合）"
        if count >= 4:
            return f"label 含 {count} 个未转义双引号（≥ 4 个 → 嵌套未转义）"
        return None

    for source, block in blocks:
        # 跳过 mermaid 关键字行（避免 parse 关键字字符串）
        for line in block.split('\n'):
            line_strip = line.strip()
            # 跳过 frontmatter / graph 声明 / 注释 / subgraph 等
            if not line_strip:
                continue
            if line_strip.startswith(('graph', 'flowchart', 'sequenceDiagram',
                                       'classDiagram', 'stateDiagram', 'subgraph',
                                       'end', '%%', '---', 'config:')):
                continue
            for pattern in label_patterns:
                for m in pattern.finditer(line_strip):
                    label = m.group(1)
                    # 嵌套双引号检测
                    quote_issue = _check_nested_quotes(label)
                    if quote_issue:
                        violations.append((source, label[:80], quote_issue))
                        continue  # 一个 label 报一次即可
                    # 中文标点检测
                    for ch, desc in CHINESE_PUNCT.items():
                        if ch in label:
                            violations.append((source, label[:80], f"含 {desc}"))
                            break

    if not violations:
        r.ok(f"Mermaid block × {len(blocks)} 均 label 字符安全（S4-39 PASS）")
        return

    # 去重（同 source 同 label 多次命中只报一次）
    seen = set()
    unique_violations = []
    for v in violations:
        key = (v[0], v[1])
        if key not in seen:
            seen.add(key)
            unique_violations.append(v)

    msg_lines = [
        f"Mermaid label 字符安全违规 {len(unique_violations)} 处（S4-39，可能触发 parse 错或视觉异常）："
    ]
    for source, label, reason in unique_violations[:10]:
        msg_lines.append(
            f"  [{source}] label='{label}' — {reason}"
        )
    if len(unique_violations) > 10:
        msg_lines.append(f"  ...（共 {len(unique_violations)} 处，仅显示前 10 条）")
    msg_lines.append(
        "修复方向：\n"
        "  ① 双引号 `\"...\"` → 改用单引号 `'...'` 或转义为 `&quot;...&quot;`\n"
        "  ② 中文标点 → 替换为对应英文标点（， → , / 。 → . / ； → ; / ： → :）\n"
        "  ③ 中文引号 → 用 ASCII 单引号 ' 替代\n"
        "详 rule_hard_constraints.md §S4-39 + S4-33 mermaid 语法校验（mmdc parse 兜底）"
    )
    r.warn('\n'.join(msg_lines))


# ── SSOT #70 业务流程图选型规范配套机械兜底（WARN 档，[Should]）──────────────────


def check_business_flow_diagrams(spec_md: str, prd_html: str, r: Report) -> None:
    """SSOT #70 业务流程图选型规范配套机械兜底（[Should] WARN 阶段）。

    校验 3 项可机械化项：
      ① 图类型头部识别 — mermaid 块首行须含合法图类型关键字（flowchart / sequenceDiagram /
         stateDiagram-v2 / journey / gantt / classDiagram / erDiagram / gitGraph / mindmap /
         timeline）
      ② flowchart 终态节点完整 — 按 tmpl_功能规划 §二 通用规则 1「每条路径末端有终态节点
         `([文字])`」每个 flowchart 块须含 ≥ 1 个 `Name([...])` stadium-shape 终态形态
      ③ flowchart 判断节点全覆盖 — 按通用规则 2「每个 `{}` 节点的所有分支都有出口条件
         标注」每个 `Name{...}` 决策节点须含 ≥ 2 条 labeled outgoing edges `Name -->|label|`

    豁免：
      - sequenceDiagram / stateDiagram-v2 / journey 等非 flowchart 块不应用 R2/R3（语义
        不同，sequenceDiagram 用 participant + 时间轴，stateDiagram 用 [*] 入终态）
      - 空 mermaid 块跳过
      - mermaid 块无任何 `{}` 决策节点 → R3 自动 PASS（不强制必有决策节点）

    选型决策本身（流程图类型该选哪个）因业务语境敏感无法机械化校验，PM 自觉对照
    `proto_business_flow_selection.md` 决策路径 + Supervisor 审核兜底。本函数仅承载
    "已选定图类型后的形式合规性"，与 `check_mermaid_syntax`（mmdc parse）/
    `check_mermaid_label_chars`（label 字符安全）正交，三者协同覆盖 mermaid 块质量
    全维度。

    强度：WARN 阶段（dry-run 纪律）：≥ 2 仓真实下游 dry-run + FP < 30% 后升 FAIL；
    FP ≥ 30% 挂 NB 不上线（同 `a_precheck_pairing_completeness` v1→v2 FP 收敛纪律）。
    """
    r.section("SSOT #70 业务流程图选型规范机械兜底（[Should] WARN）")

    blocks = _extract_mermaid_blocks(spec_md, prd_html)
    if not blocks:
        r.ok("未检测到 mermaid 块（产品无流程图，跳过 SSOT #70 校验）")
        return

    # 合法 mermaid 图类型头部关键字（含主流类型 + mermaid v10+ 新增）
    valid_diagram_types = (
        "flowchart", "graph",                # flowchart（含旧 graph 别名）
        "sequenceDiagram",                    # 时序图 / 跨角色泳道
        "stateDiagram-v2", "stateDiagram",    # 状态机
        "journey",                            # 用户旅程
        "classDiagram",                       # 类图
        "erDiagram",                          # 实体关系
        "gantt",                              # 甘特图
        "gitGraph",                           # git 图
        "mindmap",                            # 思维导图
        "timeline",                           # 时间轴
    )

    # mermaid v10+ frontmatter 块识别（`---\nconfig:...\n---\n<diagram>`）
    # v1→v2 FP 收敛：private-domain prd#7 命中根因（首行 "---" 被误判 R1）
    frontmatter_re = re.compile(r'^\s*---\s*\n(?:.*?\n)*?---\s*\n', re.MULTILINE)

    def _strip_frontmatter(content: str) -> str:
        """剥除 mermaid v10+ frontmatter，返回真正的图类型起始内容"""
        m = frontmatter_re.match(content)
        return content[m.end():] if m else content

    # R2 终态节点：Name([...]) stadium-shape（圆角矩形含方括号内嵌内容）
    terminal_node_re = re.compile(r'\w+\s*\(\s*\[[^\]]+\]\s*\)')

    # R3 决策节点：Name{...} 菱形（排除 Name{{...}} 六边形）；node name + label 双捕获
    decision_node_re = re.compile(r'(\w+)\s*\{(?!\{)([^{}]+)\}(?!\})')

    def _labeled_edges_from(block: str, node: str) -> int:
        """统计从指定节点出发的 outgoing edges 数（含 labeled / unlabeled）。

        匹配 `NodeName -->`、`NodeName --> Next`、`NodeName -->|label| Next` 三型；
        R3 关注分支完整性（≥ 2 即合规），不强制 label 必填（label 缺失另由 Supervisor 审）。
        """
        pattern = re.compile(rf'\b{re.escape(node)}\b\s*-{{2,3}}>(?:\|[^|]+\|)?\s*\w+')
        return len(pattern.findall(block))

    type_violations: list[str] = []
    terminal_violations: list[str] = []
    decision_violations: list[str] = []

    for source, content in blocks:
        # v2 FP 收敛：先剥 mermaid v10+ frontmatter（`---\nconfig:...\n---`）
        body = _strip_frontmatter(content)
        # 取首行非空非 mermaid 注释（%%）
        lines = [l.strip() for l in body.split("\n")
                 if l.strip() and not l.lstrip().startswith("%%")]
        if not lines:
            continue  # 空块（仅注释 / 仅 frontmatter）跳过
        header = lines[0]
        first_word = header.split()[0] if header.split() else ""

        # R1: 图类型头部识别
        if first_word not in valid_diagram_types:
            type_violations.append(
                f"[{source}] 首行 '{header[:60]}' 不含合法 mermaid 图类型关键字"
            )
            continue  # 类型不识别 → 跳过 R2/R3（无法判定）

        # R2 + R3 仅对 flowchart / graph 应用
        if first_word not in ("flowchart", "graph"):
            continue

        # v2 FP 收敛：含 subgraph 的 graph/flowchart 块视为"架构图 / 模块依赖图"，
        # 不应用 R2 终态节点校验（架构图 / 模块图本身无业务路径起终态语义；
        # private-domain prd#7/#8 命中根因）。R3 仍适用——架构图也可能含决策节点。
        has_subgraph = bool(re.search(r'\bsubgraph\b', body))
        # v3 FP 收敛：节点名 ≥ 3 个匹配系统编号（M\d+ / P\d+ / S\d+ 等单字母+数字）
        # 视为模块依赖图 / 页面路由图（private-domain prd#8 graph TB M01-M08 命中根因）。
        # 节点名提取：[ / ( / { 前的标识符
        sys_id_nodes = re.findall(r'(?:^|\n|\s)([A-Z]\d{1,3})\s*[\[\(\{]', body)
        looks_like_architecture = has_subgraph or len(set(sys_id_nodes)) >= 3
        # v3 FP 收敛：边 label 含技术词（data_flow / section_jump / api_call 等下划线
        # 蛇形命名）视为 DFD / 模块依赖图豁免 R2（private-domain prd#8 命中根因）
        tech_edge_labels = re.findall(r'-->\|([a-z_]+)\|', body)
        looks_like_dfd = sum(1 for lbl in tech_edge_labels if '_' in lbl) >= 2
        is_architecture_diagram = looks_like_architecture or looks_like_dfd

        # R2: 终态节点完整（架构图豁免）
        if not is_architecture_diagram and not terminal_node_re.search(body):
            terminal_violations.append(
                f"[{source}] flowchart 块无 `Name([...])` 终态节点（按 tmpl_功能规划 §二 通用规则 1）"
            )

        # R3: 判断节点分支全覆盖（label 完整性）
        for node_name, _ in decision_node_re.findall(body):
            edge_count = _labeled_edges_from(body, node_name)
            if edge_count < 2:
                decision_violations.append(
                    f"[{source}] 决策节点 `{node_name}{{...}}` 仅 {edge_count} 条出口（按通用规则 2 须 ≥ 2 分支）"
                )

    total_violations = len(type_violations) + len(terminal_violations) + len(decision_violations)

    if total_violations == 0:
        r.ok(f"业务流程图选型规范校验通过（{len(blocks)} 个 mermaid 块全部合规）")
        return

    msg_lines = [
        f"SSOT #70 业务流程图选型规范校验发现 {total_violations} 项问题（{len(blocks)} 个 mermaid 块）："
    ]
    if type_violations:
        msg_lines.append(f"  R1 图类型头部不识别 ({len(type_violations)} 处)：")
        for v in type_violations[:5]:
            msg_lines.append(f"    {v}")
        if len(type_violations) > 5:
            msg_lines.append(f"    ...（共 {len(type_violations)} 处，仅显示前 5）")
    if terminal_violations:
        msg_lines.append(f"  R2 flowchart 终态节点缺失 ({len(terminal_violations)} 处)：")
        for v in terminal_violations[:5]:
            msg_lines.append(f"    {v}")
        if len(terminal_violations) > 5:
            msg_lines.append(f"    ...（共 {len(terminal_violations)} 处，仅显示前 5）")
    if decision_violations:
        msg_lines.append(f"  R3 flowchart 判断节点分支不全 ({len(decision_violations)} 处)：")
        for v in decision_violations[:5]:
            msg_lines.append(f"    {v}")
        if len(decision_violations) > 5:
            msg_lines.append(f"    ...（共 {len(decision_violations)} 处，仅显示前 5）")
    msg_lines.append(
        "修复方向：详 `pm-workflow/rules/proto_business_flow_selection.md` 决策路径 + "
        "tmpl_功能规划 §二 通用格式规则；选型决策本身（图类型该选哪个）业务语境敏感，"
        "无法机械化校验，PM 自觉对照 + Supervisor 审核兜底"
    )
    r.warn("\n".join(msg_lines))


def check_html_div_balance(prd_html: str, r: Report) -> None:
    """SSOT #71 outputs/prd 真 DOM div 平衡兜底（议题 10 NB-WE-PROTO-NAV-OVERWRITE 第 3
    层防御，[Should] WARN 阶段）。

    用 stdlib html.parser 真 DOM 解析 outputs/prd，跟踪 `<div>` 嵌套深度，最终 depth ≠ 0
    → WARN 报警（治"PM 直 Edit outputs 违规 / inject 链路漂移 / drafts 拼装 div 孤儿"
    等系统性 DOM 平衡缺陷）。

    与 assemble.py `_ensure_layout_closing_before_body`（机械兜底层）协同形成 div 平衡
    防御链：assemble 兜底自动补足 depth > 0 缺失 → precheck 兜底捕获兜底失败 / depth < 0
    多 close 异常分布（assemble 兜底不删多余 close，只补缺失）。

    算法（与机械 grep 算法对偶 — 治 PM 历史用 `grep -c` 错算 div 数的同型踩坑）：
    - 用 html.parser 跟踪 `<div>` 开闭深度（跳过 `<script>` / `<style>` 内容字面）
    - 最终 depth > 0 → 缺 `</div>` close（PM 直 Edit or inject bug）
    - 最终 depth < 0 → 多 `</div>` 孤儿（drafts 拼装 + 错配）
    - 最终 depth == 0 → 平衡 PASS

    豁免：
    - 空 prd_html → skip
    - html.parser 异常 → WARN（不阻塞 precheck，PM 自查）

    强度：WARN 阶段（NB-LIT-25-B dry-run 纪律）：≥ 2 仓 dry-run + FP < 30% 后升 FAIL。
    议题 #10 实证：私域 outputs/prd depth +1（缺 1 个 close），与下游 PM 自报 -9/-10/-11
    等数字差异巨大——PM 自报用 `grep -c` 数行而非 `grep -o` 数字面引起的算法偏差。
    """
    r.section("SSOT #71 outputs/prd 真 DOM div 平衡兜底（[Should] WARN）")

    if not prd_html.strip():
        r.ok("空 prd_html，跳过 SSOT #71 校验")
        return

    from html.parser import HTMLParser as _HP

    class _DivDepth(_HP):
        def __init__(self) -> None:
            super().__init__()
            self.depth = 0
            self.in_skip = False
            self.opens = 0
            self.closes = 0

        def handle_starttag(self, tag: str, attrs: list) -> None:
            if tag in ("script", "style"):
                self.in_skip = True
                return
            if self.in_skip:
                return
            if tag == "div":
                self.depth += 1
                self.opens += 1

        def handle_endtag(self, tag: str) -> None:
            if tag in ("script", "style"):
                self.in_skip = False
                return
            if self.in_skip:
                return
            if tag == "div":
                self.depth -= 1
                self.closes += 1

    try:
        p = _DivDepth()
        p.feed(prd_html)
    except Exception as e:
        r.warn(f"html.parser 异常，跳过 div 平衡校验：{e}")
        return

    if p.depth == 0:
        r.ok(f"outputs/prd 真 DOM div 平衡（开 {p.opens} / 闭 {p.closes} / depth 0）")
        return

    if p.depth > 0:
        r.warn(
            f"outputs/prd 真 DOM 缺 {p.depth} 个 `</div>` 闭合"
            f"（开 {p.opens} / 闭 {p.closes} / depth +{p.depth}）— "
            f"修复方向：跑 assemble.py prd --force-overwrite 让 "
            f"`_ensure_layout_closing_before_body` 兜底补足；若兜底后仍 WARN，"
            f"排查 inject 链路 / PM 是否直 Edit outputs/prd 违规（详 CLAUDE.md "
            f"§调整意见自动记录规则 §阶段 4 outputs 派生链路硬约束）"
        )
    else:
        r.warn(
            f"outputs/prd 真 DOM 多 {abs(p.depth)} 个 `</div>` 孤儿"
            f"（开 {p.opens} / 闭 {p.closes} / depth {p.depth}）— "
            f"修复方向：排查 process_record/drafts/prd_M*_draft.html 是否含孤儿 "
            f"`</div>` 或 inject 链路 bug；机械兜底层 `_ensure_layout_closing_before_body` "
            f"不删多余 close（避免误删合法 DOM），需 PM 手动定位"
        )


def check_scaffold_outputs_frame_consistency(data: dict, prd_html: str, r: Report) -> None:
    """SSOT #72 scaffold ↔ outputs/prd FRAME 一致性兜底（议题 11/12 NB-WE-12，[Should] WARN）。

    比对 `scaffold.json modules[*].pages[*].states[*].prd_id` 全集 vs outputs/prd 含
    FRAME 全集（已生成 `id="H-XXX"` + 未填 `[FRAME: H-XXX]` placeholder + 可重入
    `[FRAME-START: H-XXX]` 块三类来源），输出漂移详情供 PM 参考整改。

    漂移分二类：
    - 漂移 A（scaffold 有 / outputs 无）：PM 加 scaffold 新 state 未重 gen_scaffold；
      assemble.py 议题 12 治本后会 WARN + skip 不再 ERROR sys.exit(1)，但漂移仍需 PM 整改
    - 漂移 B（outputs 有 / scaffold 无）：PM 删 scaffold 但 outputs 残留孤儿 frame；
      assemble.py 不主动清（避免误删 PM 写在 drafts 同步的内容）

    议题 11 私域 outputs/prd 实证：漂移 A = 4 帧（H-M01-P01-offshelf-{appeal-submitted,
    default, error, loading}）+ 漂移 B = 24 帧（M01-P06 4 + M03-P03 14 + M07-P07 5 +
    M01-P01-offshelf 1）+ 一致项 = 119。

    与 SSOT #71 `check_html_div_balance` 协同形成 outputs/prd 质量防御链：#71 治真 DOM
    平衡 / #72 治 frame 集合一致性，二者正交覆盖不同维度漂移。与议题 12 治本
    `assemble.py` ERROR → WARN + skip 协同 — assemble 不阻塞 reassembly，precheck 兜底
    暴露漂移让 PM 选 gen_scaffold rescaffold 或手动整改。

    强度：WARN 阶段（NB-LIT-25-B dry-run 纪律）：≥ 2 仓真实 PM 反馈 + FP < 30% 后升 FAIL。

    修复方向（PM 二选一）：
    - ✅ 推荐：重跑 `python3 pm-workflow/scripts/gen_scaffold.py --force-rescaffold` 重生骨架
      （A 自动补 placeholder + B 重生时孤儿自动清）
    - 手动：手补 missing placeholder + 定位删孤儿 frame（A 维护成本高，B 易误删）
    """
    r.section("SSOT #72 scaffold ↔ outputs/prd FRAME 一致性兜底（[Should] WARN）")

    # Scaffold prd_id 全集（三层嵌套：modules > pages > states）
    scaffold_ids: set[str] = set()
    for mod in data.get("modules", []):
        for page in mod.get("pages", []):
            # SSOT #76 R3：含内嵌子组件帧——内嵌 prd_id 同样在 outputs/prd 有 FRAME
            # 占位（gen_scaffold build_module_sections 派生），漏收会误判内嵌帧为漂移 B 孤儿。
            scaffold_ids.update(iter_page_prd_ids(page))

    if not scaffold_ids:
        r.ok("scaffold.json 无 prd_id，跳过 SSOT #72 校验")
        return

    if not prd_html.strip():
        r.ok("空 prd_html，跳过 SSOT #72 校验")
        return

    # outputs/prd 含 FRAME 全集（三类来源）
    outputs_ids: set[str] = set()
    # 已生成 frame：id="H-..." 字面
    for m in re.finditer(r'\bid="(H-[A-Za-z0-9_-]+)"', prd_html):
        outputs_ids.add(m.group(1))
    # 未填 placeholder：[FRAME: H-...]
    for m in re.finditer(r'<!--\s*\[FRAME:\s*(H-[A-Za-z0-9_-]+)\s*\]\s*-->', prd_html):
        outputs_ids.add(m.group(1))
    # 可重入块：[FRAME-START: H-...]
    for m in re.finditer(r'<!--\s*\[FRAME-START:\s*(H-[A-Za-z0-9_-]+)', prd_html):
        outputs_ids.add(m.group(1))

    if not outputs_ids:
        r.warn(
            f"outputs/prd 无 FRAME 标记（scaffold 含 {len(scaffold_ids)} 个 prd_id 全漂移 A）"
            f" — 修复方向：重跑 gen_scaffold.py --force-rescaffold 重生骨架"
        )
        return

    drift_a = sorted(scaffold_ids - outputs_ids)  # scaffold 有 outputs 无
    drift_b = sorted(outputs_ids - scaffold_ids)  # outputs 有 scaffold 无（孤儿）
    consistent_count = len(scaffold_ids & outputs_ids)

    if not drift_a and not drift_b:
        r.ok(
            f"scaffold ↔ outputs FRAME 一致性 PASS（一致 {consistent_count} / scaffold "
            f"{len(scaffold_ids)} / outputs {len(outputs_ids)}）"
        )
        return

    msg_lines = [
        f"scaffold ↔ outputs FRAME 漂移：一致 {consistent_count} / scaffold "
        f"{len(scaffold_ids)} / outputs {len(outputs_ids)}"
    ]
    if drift_a:
        msg_lines.append(
            f"  漂移 A（scaffold 有 / outputs 无）{len(drift_a)} 帧 — PM 加 scaffold "
            f"未重 gen_scaffold；assemble 议题 12 治本后 WARN + skip 不再 ERROR："
        )
        for pid in drift_a[:10]:
            msg_lines.append(f"    - {pid}")
        if len(drift_a) > 10:
            msg_lines.append(f"    ...（共 {len(drift_a)} 帧，仅显示前 10）")
    if drift_b:
        msg_lines.append(
            f"  漂移 B（outputs 有 / scaffold 无，孤儿 frame）{len(drift_b)} 帧 — "
            f"PM 删 scaffold 但 outputs 残留（assemble 不主动清避免误删 drafts 同步内容）："
        )
        for pid in drift_b[:10]:
            msg_lines.append(f"    - {pid}")
        if len(drift_b) > 10:
            msg_lines.append(f"    ...（共 {len(drift_b)} 帧，仅显示前 10）")
    msg_lines.append(
        "修复方向（PM 二选一）：① 推荐：`python3 pm-workflow/scripts/gen_scaffold.py"
        " --force-rescaffold` 重生骨架（A 自动补 placeholder + B 重生时孤儿清除）"
        "② 手动：补 missing placeholder + 定位删孤儿 frame（A 高维护成本，B 易误删）"
    )
    r.warn("\n".join(msg_lines))


def check_outputs_prd_no_assemble_timestamp(prd_html: str, r: Report) -> None:
    """SSOT #73 outputs/prd assemble 输出确定性兜底（议题 13 NB-WE-ASSEMBLE-DETERMINISM，
    [Should] WARN）。

    扫 outputs/prd 含的"已知非确定性 marker"——目前是 `assembled=<UTC ISO timestamp>`
    字面（议题 13 治本前 assemble.py L4243 FRAME-START 含 `| assembled={assembled_at}`
    wall-clock timestamp，导致每次 assemble outputs sha 必差与 CLAUDE.md 三方对账机制
    冲突），命中即 WARN（治本后 assemble 不再注入，应 0 命中）。

    与 SSOT #71 `check_html_div_balance`（真 DOM 平衡）+ SSOT #72
    `check_scaffold_outputs_frame_consistency`（frame 集合一致性）协同形成 outputs/prd
    质量防御三正交维度：真 DOM 结构 / frame 集合 / 字节级确定性。

    议题 13 实证：私域 outputs/prd（commit bbd0cb3 议题 #14 后基线）含 139 处
    `assembled=YYYY-MM-DDTHH:MM:SSZ` 字面 → assemble.py 治本 + reassembly 后应 0 命中。

    未来若新增 assemble 非确定性源（rand / pid / hostname / 其他 wall-clock 字段）→
    扩展本函数扫描清单 + 升级到 [Must] FAIL。

    强度：WARN 阶段（NB-LIT-25-B dry-run 纪律）：≥ 2 仓 FP < 30% 后升 FAIL。

    完整 assemble 确定性验证（跑两次 assemble 对比 sha）作为 PM 手动验证步骤（不入 precheck，
    避免 subprocess 复杂度 + 性能成本）：详 CLAUDE.md「PM 自报 sha 一致性审计」段。
    """
    r.section("SSOT #73 outputs/prd assemble 输出确定性兜底（[Should] WARN）")

    if not prd_html.strip():
        r.ok("空 prd_html，跳过 SSOT #73 校验")
        return

    # 扫已知非确定性 marker：`assembled=<UTC ISO timestamp>` 字面
    # 议题 13 治本前 assemble.py L4243 注入字面格式：`assembled=2026-06-07T12:21:48Z`
    timestamp_pattern = re.compile(r'assembled=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')
    matches = timestamp_pattern.findall(prd_html)

    if not matches:
        r.ok("outputs/prd 无非确定性 marker（`assembled=<ISO timestamp>` 0 命中）")
        return

    r.warn(
        f"outputs/prd 含 {len(matches)} 处 `assembled=<ISO timestamp>` 字面"
        f"（NB-WE-ASSEMBLE-DETERMINISM 治本前残留 / 旧 assemble.py 产出）— "
        f"修复方向：①确认上游 assemble.py 已应用议题 13 治本（L4243 去 `| assembled={{...}}` 字段）"
        f" ②重跑 `python3 pm-workflow/scripts/assemble.py prd --force-overwrite` 让 outputs/prd "
        f"重生（清除 timestamp 字面）③后续 sha 字节级确定性恢复 → CLAUDE.md 三方对账机制对 "
        f"outputs/prd 生效"
    )


def check_page_source_provenance(data: dict, r: Report) -> None:
    """SSOT #74 页面集守恒——scaffold 每页 page_source 溯源标注兜底（R1 阶段 2 页面集 SSOT，
    [Should] WARN）。

    阶段 2 §3.1/§3.3 页面集是产品总监审核过的 SSOT 基线（`tmpl_功能规划.md` 双锚 #74）。
    后续阶段页面集必须 ⊆ 基线，PM 不得擅自增页。本兜底校验 scaffold 每页是否标注
    `page_source` 溯源——机械层只校「溯源声明存在 + 格式合法」（语义层「声明的来源是否
    真实可追溯阶段 2」由 Supervisor 中段审核反查，详 AI产品主管_Agent.md；报告 3.5 实证
    该越界 AI 拆 + AI 自审双双漏掉，人类拿阶段 2 明文反查才抓出——机械层抓不到语义）。

    page_source 合法值：
    - 'stage2'：追溯阶段 2 §3.3 基线页面（正常路径）
    - 'director_approved:<YYYY-MM-DD>'：缺页无法闭环 → escalation 产品总监拍板新增
      （详 agent_dispatch_protocol.md 第 8 条 SOP）

    校验项：
    - 每页缺 page_source → WARN（迁移期提醒；治"PM 擅自增页无溯源标注"）
    - page_source 格式非法（gen_scaffold 已校格式，本处兜底再扫）→ WARN

    豁免：
    - logic-only 模块（pages=[]）跳过（无页可标）
    - scaffold 无 modules → skip

    强度：WARN 阶段（NB-LIT-25-B dry-run 纪律）：≥ 2 仓 FP < 30% 后升 FAIL。迁移期既有
    下游 scaffold 普遍无 page_source → WARN 不阻塞，PM 逐页补标 stage2 / escalation。

    与 SSOT #38 正交：#38 管页面层级渲染派生（scaffold 仍是阶段 4 真源），#74 管页面集
    成员守恒（不得擅自扩张）。
    """
    r.section("SSOT #74 页面集守恒 page_source 溯源兜底（[Should] WARN）")

    modules = data.get("modules", [])
    if not modules:
        r.ok("scaffold 无 modules，跳过 SSOT #74 校验")
        return

    _valid_re = re.compile(r"^(stage2|director_approved:\d{4}-\d{2}-\d{2})$")
    missing: list[str] = []
    malformed: list[str] = []
    approved: list[str] = []
    total_pages = 0

    for mod in modules:
        if not isinstance(mod, dict):
            continue
        mid = mod.get("id", "?")
        pages = mod.get("pages", [])
        if not isinstance(pages, list) or len(pages) == 0:
            continue  # logic-only 模块无页可标
        for page in pages:
            if not isinstance(page, dict):
                continue
            total_pages += 1
            pid = page.get("id", "?")
            ps = page.get("page_source")
            if ps is None:
                missing.append(f"{mid}/{pid}")
            elif not _valid_re.match(str(ps)):
                malformed.append(f"{mid}/{pid}={ps!r}")
            elif str(ps).startswith("director_approved:"):
                approved.append(f"{mid}/{pid}={ps}")

    if not missing and not malformed:
        note = f"（{len(approved)} 页 escalation 批准）" if approved else ""
        r.ok(f"页面集守恒 page_source 溯源完整（{total_pages} 页全标注）{note}")
        return

    msg_lines = [
        f"SSOT #74 页面集守恒：{total_pages} 页中 page_source 溯源问题 "
        f"{len(missing) + len(malformed)} 处"
    ]
    if missing:
        msg_lines.append(
            f"  缺 page_source 溯源标注 {len(missing)} 页（PM 须标 'stage2' 追溯阶段 2 "
            f"§3.3 基线 / escalation 批准页标 'director_approved:<YYYY-MM-DD>'）："
        )
        for x in missing[:10]:
            msg_lines.append(f"    - {x}")
        if len(missing) > 10:
            msg_lines.append(f"    ...（共 {len(missing)} 页，仅显示前 10）")
    if malformed:
        msg_lines.append(f"  page_source 格式非法 {len(malformed)} 页：")
        for x in malformed[:10]:
            msg_lines.append(f"    - {x}")
    msg_lines.append(
        "修复方向：① 追溯阶段 2 §3.3 基线的页标 `page_source: stage2` ② 擅自增页（阶段 2 "
        "未定义）→ 禁；按 agent_dispatch_protocol 第 8 条 escalation 上报产品总监拍板 → "
        "批准后标 `director_approved:<日期>` + 回写阶段 2 基线 ③ 本该内嵌的子卡片/弹窗 → "
        "改为承载页子状态/子区域（禁外化独立 page）。详 tmpl_功能规划 §3.1/§3.3 双锚 #74"
    )
    r.warn("\n".join(msg_lines))


def check_depends_on_cycle(data: dict, r: Report) -> None:
    """SSOT #75-R7 depends_on 运行时依赖图环检测（R7，[Should] WARN）。

    治问题 8「依赖方向建模错——把『卡片跳转入口』建成反向依赖伪环」：depends_on 的 kind
    分两类语义——
    - **运行时依赖**（runtime_dep，消费者→生产者，禁反向 + 禁环）：`data_flow`（A 读 B 的
      数据）/ `permission`（A 的权限受 B 控制）。这两类构成运行时依赖图，**必须无环**
      （A 依赖 B 依赖 A = 循环运行时依赖 = 架构缺陷）。
    - **非运行时边**（不计入运行时依赖图，**排除环检测**）：`section_jump`（页面跳转入口，
      仅导航关系非数据依赖——问题 8 伪环根因：把跳转入口当反向依赖）/ `shared_component`
      （组件复用，复用关系非运行时依赖）。

    算法：
    - 仅从 `data_flow` + `permission` 边构建有向图（module → target，"本模块依赖 target"）
    - DFS 三色标记检测环；发现环 → WARN 列出环路径
    - section_jump / shared_component 边**不参与**环检测（治伪环）

    豁免：无 modules / 无 runtime 边 → skip。强度 WARN（NB-LIT-25-B ≥ 2 仓 FP < 30% 升 FAIL）。

    与 D-05（Supervisor depends_on 结构化完整性）协同：D-05 校字段完整 + kind 枚举，本检
    校运行时子图无环（方向建模正确性）。
    """
    r.section("SSOT #75-R7 depends_on 运行时依赖图环检测（[Should] WARN）")

    modules = data.get("modules", [])
    if not modules:
        r.ok("scaffold 无 modules，跳过 R7 校验")
        return

    RUNTIME_KINDS = {"data_flow", "permission"}
    graph: dict[str, set] = {}
    valid_ids = {m.get("id") for m in modules if isinstance(m, dict) and m.get("id")}
    for m in modules:
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        if not mid:
            continue
        graph.setdefault(mid, set())
        for dep in m.get("depends_on", []):
            if not isinstance(dep, dict):
                continue
            if dep.get("kind") in RUNTIME_KINDS:
                tgt = dep.get("module")
                if tgt and tgt in valid_ids and tgt != mid:
                    graph[mid].add(tgt)

    runtime_edges = sum(len(v) for v in graph.values())
    if runtime_edges == 0:
        r.ok("无运行时依赖边（data_flow / permission），跳过环检测")
        return

    # DFS 三色：0=未访问 1=在栈中 2=完成
    color: dict[str, int] = {n: 0 for n in graph}
    cycles: list[list] = []

    def _dfs(node: str, path: list) -> None:
        color[node] = 1
        path.append(node)
        for nxt in sorted(graph.get(node, ())):
            if color.get(nxt, 0) == 1:
                # 找到环：截取 path 中 nxt 到当前的子段
                idx = path.index(nxt)
                cycles.append(path[idx:] + [nxt])
            elif color.get(nxt, 0) == 0:
                _dfs(nxt, path)
        path.pop()
        color[node] = 2

    for n in sorted(graph):
        if color[n] == 0:
            _dfs(n, [])

    if not cycles:
        r.ok(
            f"运行时依赖图无环（{runtime_edges} 条 data_flow/permission 边；"
            f"section_jump/shared_component 跳转/复用边已排除）"
        )
        return

    # 去重（同一环不同起点）
    uniq = []
    seen = set()
    for cyc in cycles:
        key = frozenset(cyc)
        if key not in seen:
            seen.add(key)
            uniq.append(cyc)

    msg_lines = [
        f"depends_on 运行时依赖图发现 {len(uniq)} 个环（data_flow/permission 子图）："
    ]
    for cyc in uniq[:5]:
        msg_lines.append(f"  {' → '.join(cyc)}")
    msg_lines.append(
        "修复方向：①核查是否把『页面跳转入口』误建成 data_flow 反向依赖（问题 8 伪环根因）"
        "——跳转入口应 kind=section_jump（不计入运行时依赖图）②真循环运行时依赖（A 读 B "
        "数据 + B 读 A 数据）需重新建模数据流向，拆出单向 producer/consumer ③组件复用关系"
        "应 kind=shared_component（不计入运行时依赖）"
    )
    r.warn("\n".join(msg_lines))


def check_archetype_semantics(data: dict, r: Report) -> None:
    """SSOT #75-R5 archetype 语义匹配校验（R5，[Should] WARN）。

    治问题 3「只读页误套表单范式」（反复犯——实验报告 B′/Arm S/Arm H-AI 三处同犯：强制
    下架卡片是只读状态展示，却套 admin-form-flow 表单范式）。

    机械层（启发式，FP 保守）：
    - 识别「表单类」archetype：id/name 含 form / 表单 / 录入 / 编辑 / wizard / 填写 关键字
    - 识别「纯状态展示页」：该页所有 state 名都是状态展示词（default/loading/error/empty/
      offshelf/appeal/warn/exception/fail/timeout/success/pending/active/completed/
      disabled/readonly/审查/驳回 等）且无输入类词（edit/input/form/fill/录入/编辑/填写/提交）
    - 表单类 archetype 被分配给纯状态展示页 → WARN（疑似只读页误套表单范式）

    可选 schema 字段 `page_archetypes[].semantic_category`（form/readonly-status/list/
    detail/modal-confirm/wizard/dialog-flow）由 gen_scaffold 校格式；存在时优先用其判定
    （比关键字启发式准）。语义层「该页确属只读 vs 表单」终判由 Supervisor §4.5 反查。

    豁免：无 page_archetypes / 无 modules → skip。强度 WARN（NB-LIT-25-B ≥ 2 仓 FP < 30% 升 FAIL）。
    """
    r.section("SSOT #75-R5 archetype 语义匹配校验（[Should] WARN）")

    archetypes = data.get("page_archetypes")
    modules = data.get("modules", [])
    if not isinstance(archetypes, list) or not archetypes or not modules:
        r.ok("无 page_archetypes / modules，跳过 R5 校验")
        return

    _FORM_KW = ("form", "表单", "录入", "编辑", "wizard", "填写", "edit")
    _STATUS_KW = (
        "default", "loading", "error", "empty", "offshelf", "appeal", "warn",
        "exception", "fail", "timeout", "success", "pending", "active",
        "completed", "disabled", "readonly", "审查", "驳回", "下架", "submitted",
        "overridden", "audit",
    )
    _INPUT_KW = ("edit", "input", "form", "fill", "录入", "编辑", "填写", "提交", "submit-form")

    # archetype id → (是否表单类, semantic_category)
    arche_form: dict[str, bool] = {}
    for a in archetypes:
        if not isinstance(a, dict):
            continue
        aid = a.get("id", "")
        sem = a.get("semantic_category")
        if sem == "form" or sem == "wizard":
            arche_form[aid] = True
        elif sem is not None:
            arche_form[aid] = False  # 显式声明非表单类
        else:
            blob = f"{aid} {a.get('name','')}".lower()
            arche_form[aid] = any(kw in blob for kw in _FORM_KW)

    violations: list[str] = []
    for m in modules:
        if not isinstance(m, dict):
            continue
        mid = m.get("id", "?")
        for page in m.get("pages", []):
            if not isinstance(page, dict):
                continue
            pid = page.get("id", "?")
            aid = page.get("archetype")
            if not aid or not arche_form.get(aid):
                continue  # 非表单类 archetype 或无 archetype，跳过
            # 页名含表单/维护语境词 → 豁免（FP 收敛：M08「系统预设提示词维护页」是真表单
            # 页，状态名恰为状态类会误命中；页名「维护/配置/编辑/录入/设置/管理/新建」等强
            # 暗示表单交互 → 不应判为只读误套）
            page_name = str(page.get("name", "")).lower()
            _PAGE_FORM_CTX = (
                "维护", "配置", "编辑", "录入", "设置", "管理", "新建", "创建", "填写",
                "表单", "form", "edit", "config", "setting", "manage", "create",
            )
            if any(kw in page_name for kw in _PAGE_FORM_CTX):
                continue
            states = page.get("states", [])
            if not isinstance(states, list) or not states:
                continue
            state_names = [str(s.get("name", "")).lower() for s in states if isinstance(s, dict)]
            blob = " ".join(state_names)
            has_input = any(kw in blob for kw in _INPUT_KW)
            all_status = all(
                any(kw in sn for kw in _STATUS_KW) for sn in state_names if sn
            )
            if all_status and not has_input:
                violations.append(
                    f"{mid}/{pid}（archetype={aid}，states=[{', '.join(state_names[:5])}]）"
                )

    if not violations:
        r.ok("archetype 语义匹配校验通过（无『纯状态展示页套表单范式』疑似）")
        return

    msg_lines = [
        f"疑似只读页误套表单范式 {len(violations)} 处（表单类 archetype 分配给纯状态展示页）："
    ]
    for v in violations[:10]:
        msg_lines.append(f"  - {v}")
    if len(violations) > 10:
        msg_lines.append(f"  ...（共 {len(violations)} 处，仅显示前 10）")
    msg_lines.append(
        "修复方向：①只读状态展示页应套只读/状态类 archetype（非 form/wizard 表单范式）"
        "②若确为表单页（含录入/编辑/提交交互）→ 在 page_archetypes[].semantic_category 显式"
        "标 'form' 豁免本启发式 ③语义终判由 Supervisor §4.5 D-08 范式合理性 + 拿阶段 2 反查。"
        "治实验报告决定性案例：强制下架卡片（只读状态）误套 admin-form-flow 表单范式"
    )
    r.warn("\n".join(msg_lines))


# §11 异常覆盖：错误类 state 名关键字
_EXCEPTION_STATE_KW = (
    "error", "exception", "fail", "warn", "timeout", "异常", "失败", "超时",
    "错误", "网络", "冲突", "拒绝", "denied", "conflict",
)


def check_exception_coverage(data: dict, r: Report) -> None:
    """SSOT #75-R6 §11 异常覆盖粗对照（R6，[Should] WARN）。

    治「覆盖漏检」（实验报告 P8：各臂分别漏 §11 异常态）。产品定义 §11「异常处理全景」是
    异常场景全集真源，scaffold 状态帧应覆盖其异常态。

    机械层（粗启发式，§11 自由文本无精确 ID 映射 → 粗覆盖信号 + 人工对照）：
    - 读 `产品定义_{product}_latest.md` §11「异常处理全景」段，数异常条目（表行 / 列表项）
    - 数 scaffold 中错误类 state（名含 error/exception/fail/warn/timeout/异常/失败… 关键字）
    - §11 异常条目数 >> scaffold 错误类 state 数（差距明显）→ WARN 提示可能漏检 + 列 scaffold
      现有错误类 state 覆盖供 PM 人工对照 §11 全集

    **重要 caveat**：本检是**粗覆盖信号非精确比对**（§11 markdown 自由文本，逐条 ID 映射
    不可行）；WARN 仅提示「数量上 scaffold 错误态可能不足以覆盖 §11 异常全集」，需 PM /
    Supervisor 人工对照确认。FP 容忍（WARN 阶段）。

    豁免：产品定义不存在 / 无 §11 段 / scaffold 无 modules → skip。
    """
    r.section("SSOT #75-R6 §11 异常覆盖粗对照（[Should] WARN）")

    modules = data.get("modules", [])
    product = data.get("product", "").strip()
    if not modules or not product:
        r.ok("无 modules / product，跳过 R6 校验")
        return

    pdef_path = OUTPUT_DIR / f"产品定义_{product}_latest.md"
    if not pdef_path.exists():
        r.ok(f"产品定义文件不存在（{pdef_path.name}），跳过 R6 异常覆盖校验")
        return

    text = pdef_path.read_text(encoding="utf-8")
    # 定位 §11「异常处理全景」段（## 11 / §11 / ## 十一 等）至下一个 ## 标题
    m = re.search(
        r'(^#{1,3}\s*(?:11|十一)[\.、\s].*?异常.*?$)([\s\S]*?)(?=^#{1,3}\s|\Z)',
        text, re.MULTILINE,
    )
    if not m:
        r.ok("产品定义无 §11 异常处理全景段（或标题格式不匹配），跳过 R6")
        return
    sec = m.group(2)
    # 数异常条目：表格数据行（| ... | 且非分隔行 | --- |）+ 列表项（- / * 开头）
    table_rows = [
        ln for ln in sec.splitlines()
        if ln.strip().startswith("|") and "---" not in ln
        and ln.strip().strip("|").strip()
    ]
    # 去表头（首个数据行常为表头）——粗略减 1（每张表）；保守：用 max(0, n-1)
    list_items = [ln for ln in sec.splitlines() if re.match(r'^\s*[-*]\s+\S', ln)]
    exc_entries = max(0, len(table_rows) - 1) + len(list_items)

    # 数 scaffold 错误类 state
    err_states = []
    for mod in modules:
        if not isinstance(mod, dict):
            continue
        mid = mod.get("id", "?")
        for page in mod.get("pages", []):
            if not isinstance(page, dict):
                continue
            pid = page.get("id", "?")
            for s in page.get("states", []):
                if not isinstance(s, dict):
                    continue
                sn = str(s.get("name", "")).lower()
                if any(kw in sn for kw in _EXCEPTION_STATE_KW):
                    err_states.append(f"{mid}/{pid}/{s.get('name')}")
            # 内嵌子组件错误态计入覆盖（SSOT #76 R3）：内嵌 modal/卡片可自带 error 态，
            # 同样承载 §11 异常——漏计会低估 scaffold 异常覆盖致误 WARN。
            for emb in page.get("embedded_components", []) or []:
                if not isinstance(emb, dict):
                    continue
                for s in emb.get("states", []) or []:
                    if not isinstance(s, dict):
                        continue
                    sn = str(s.get("name", "")).lower()
                    if any(kw in sn for kw in _EXCEPTION_STATE_KW):
                        err_states.append(f"{mid}/{pid}/{emb.get('id', '?')}/{s.get('name')}")

    if exc_entries == 0:
        r.ok("§11 异常段无可解析条目（表格/列表），跳过 R6 覆盖对照")
        return

    # 粗阈值：scaffold 错误态 < §11 异常条目数 * 0.5 → 提示可能漏检
    if len(err_states) >= exc_entries * 0.5:
        r.ok(
            f"§11 异常覆盖粗对照通过（§11 约 {exc_entries} 异常条目 / scaffold "
            f"{len(err_states)} 错误类 state，比例充分）"
        )
        return

    msg_lines = [
        f"§11 异常覆盖粗对照提示可能漏检：产品定义 §11 约 {exc_entries} 个异常条目，"
        f"但 scaffold 仅 {len(err_states)} 个错误类 state（< 50%）",
        "  scaffold 现有错误类 state 覆盖（供 PM 人工对照 §11 全集）：",
    ]
    for x in err_states[:15]:
        msg_lines.append(f"    - {x}")
    if len(err_states) > 15:
        msg_lines.append(f"    ...（共 {len(err_states)} 个）")
    msg_lines.append(
        "**caveat**：本检为粗覆盖信号（§11 自由文本无精确 ID 映射），WARN 仅提示数量可能"
        "不足；需 PM / Supervisor 逐条对照 §11 异常全集确认哪些异常态在 scaffold 缺承载（"
        "顺锚定方向漏检根因——参实验报告 P8）"
    )
    r.warn("\n".join(msg_lines))


# 范围：B+ 档位仅最低底线校验 (触发但 0 属性 → BLOCK)；
#      档位 C 完整叶子节点对账（每个候选 leaf 都已注入）暂不实现,后续踩坑再升级。
I18N_KEYWORDS = ("多语言", "中英", "i18n", "双语")


def check_i18n_minimum(prd_html: str, pdef_text: str, r: Report) -> None:
    """最小化 i18n 校验:仅兜底「触发 i18n 但 data-zh = 0」的 BLOCK 情况。

    触发条件: 产品定义 (outputs/产品定义_{产品}_latest.md) 含 I18N_KEYWORDS 任一关键字。
    无关键字 → 跳过整段校验（不阻断）。
    """
    r.section("i18n 最小化校验（多语言条件触发, NB-阶段4-D）")

    requires_i18n = any(kw in pdef_text for kw in I18N_KEYWORDS)
    if not requires_i18n:
        r.ok("产品定义未含多语言关键字（多语言/中英/双语/i18n）,跳过 i18n 校验")
        return

    data_zh_count = prd_html.count('data-zh="')
    if data_zh_count == 0:
        r.fail(
            "产品定义含多语言需求但 prd.html 中 data-zh 属性 = 0; "
            "请跑 `python pm-workflow/scripts/add_i18n.py --extract`+ 维护字典 + `--inject`,"
            "再重跑 `assemble.py prd` (详见 prd_expression_standard.md §十)"
        )
    else:
        r.ok(f"prd.html 含 {data_zh_count} 个 data-zh 属性,通过最小化 i18n 校验")


# ── S4-40｜.interaction-card 内禁 inline 字号覆盖（SSOT #62 E.3 第 1 条，WARN）─

class _InteractionCardInlineFontChecker(HTMLParser):
    """扫描 prd.html 中所有 .interaction-card 块内是否含 inline font-size 覆盖。

    解析策略：追踪 div 嵌套栈；进入 <div class="interaction-card"> 时 _in_card_depth +1
    （嵌套安全）；flag 打开期间，对所有元素的 style 属性检查 font-size 字面；退出对应
    .interaction-card div 时 -1。

    WARN 阶段：对齐 S4-28 dry-run 纪律（≥ 2 仓 + FP < 30% 后升 FAIL）。
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[dict] = []
        self._in_card_depth: int = 0
        self.violations: list[tuple[int, str, str]] = []  # (line, tag, style)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes: set[str] = set()
        style = ""
        for k, v in attrs:
            if k == "class" and v:
                classes = set(v.split())
            elif k == "style" and v:
                style = v

        is_card = (tag == "div" and "interaction-card" in classes)
        if is_card:
            self._in_card_depth += 1

        if self._in_card_depth > 0 and style:
            if re.search(r"font-size\s*:", style, re.IGNORECASE):
                line, _col = self.getpos()
                self.violations.append((line, tag, style))

        if tag == "div":
            self._stack.append({"tag": tag, "is_card": is_card})

    def handle_endtag(self, tag: str) -> None:
        if tag != "div":
            return
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i]["tag"] == "div":
                if self._stack[i]["is_card"]:
                    self._in_card_depth -= 1
                del self._stack[i:]
                return


def check_interaction_card_no_inline_font(prd_html: str, r: Report) -> None:
    """S4-40 / SSOT #62 E.3 第 1 条 — .interaction-card 内禁 inline 字号覆盖（WARN）。

    SSOT 真源：prd_expression_standard.md 区块 C E.3 第 1 条
    禁令：.interaction-card 内任何元素 style 属性禁含 font-size:...
    WARN 阶段：对齐 S4-28 dry-run 纪律（≥ 2 仓 + FP < 30% 后升 FAIL）。
    """
    r.section(".interaction-card 内 inline font-size 覆盖扫描（S4-40 / SSOT #62 E.3 第 1 条，WARN）")

    parser = _InteractionCardInlineFontChecker()
    try:
        parser.feed(prd_html)
        parser.close()
    except Exception as e:
        r.warn(f"S4-40 解析异常（不阻断）：{e}")
        return

    if not parser.violations:
        r.ok(".interaction-card 内无 inline `style=\"font-size:...\"` 覆盖（S4-40 PASS）")
        return

    r.warn(
        f"S4-40：.interaction-card 内 {len(parser.violations)} 处 inline `style=\"...font-size...\"`"
        f"（违规 WARN 阶段）：\n  "
        + "\n  ".join(
            f"line {line}: <{tag}> style=\"{style[:80]}{'...' if len(style) > 80 else ''}\""
            for line, tag, style in parser.violations[:10]
        )
        + (f"\n  （共 {len(parser.violations)} 处，仅显示前 10 条）"
           if len(parser.violations) > 10 else "")
        + f"\n修复方向：删除 inline font-size；模板已硬编码字号体系于 `prd_template.html`"
          f" `.interaction-card` 段（含 .card-title / .state-diff-note / .data-sub-title / table 各字号）"
    )


# ── S4-41｜典型交互说明字面必须在 .interaction-card 内（SSOT #62 E.3 第 2 条，WARN）─

class _InteractionCardClassComplianceChecker(HTMLParser):
    """检测典型交互说明字面是否在 .interaction-card 容器内。

    解析策略：追踪 div + pre + code 嵌套栈；进入 .interaction-card 时 _in_card_depth +1
    （嵌套安全）；进入 pre/code 时 _in_code_depth +1（豁免代码块/示例引用）；
    handle_data 检查当前文本：若 _in_card_depth==0 且 _in_code_depth==0 且含信号字面
    → WARN（说明 PM 用自造结构替代 .interaction-card 标准容器）。

    SIGNAL_PHRASES 来自 prd_expression_standard.md 区块 C 模板的固定字面，PRD 中这些
    字面应**仅**出现在 .interaction-card 内；出现在外 = 自造结构嫌疑（零启发式 FP≈0）。
    """

    SIGNAL_PHRASES: tuple[str, ...] = (
        "交互说明 —",     # card-title 字面（含 em-dash 区分 changelog "修改交互说明"）
        "状态差异说明",   # E.1 C-0 sub-title
        "列表回显说明",   # C-1 sub-title
        "数据展示说明",   # C-2 sub-title（SSOT #62 v2：原"卡片字段说明" → "数据展示说明"，含 C-2.A 索引 + C-2.B 详情）
        "触点交互说明",   # C-3 sub-title
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[dict] = []
        self._in_card_depth: int = 0
        self._in_code_depth: int = 0
        self.violations: list[tuple[int, str, str]] = []  # (line, phrase, context)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes: set[str] = set()
        for k, v in attrs:
            if k == "class" and v:
                classes = set(v.split())

        if tag == "div":
            is_card = "interaction-card" in classes
            if is_card:
                self._in_card_depth += 1
            self._stack.append({"tag": tag, "is_card": is_card, "is_code": False})
        elif tag in ("pre", "code"):
            self._in_code_depth += 1
            self._stack.append({"tag": tag, "is_card": False, "is_code": True})

    def handle_endtag(self, tag: str) -> None:
        if tag not in ("div", "pre", "code"):
            return
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i]["tag"] == tag:
                if self._stack[i]["is_card"]:
                    self._in_card_depth -= 1
                if self._stack[i]["is_code"]:
                    self._in_code_depth -= 1
                del self._stack[i:]
                return

    def handle_data(self, data: str) -> None:
        if self._in_card_depth > 0 or self._in_code_depth > 0:
            return
        for phrase in self.SIGNAL_PHRASES:
            if phrase in data:
                line, _col = self.getpos()
                idx = data.find(phrase)
                ctx_start = max(0, idx - 20)
                ctx_end = min(len(data), idx + 40)
                ctx = data[ctx_start:ctx_end].strip().replace("\n", " ")
                self.violations.append((line, phrase, ctx))


def check_interaction_card_class_compliance(prd_html: str, r: Report) -> None:
    """S4-41 / SSOT #62 E.3 第 2 条 — 典型交互说明字面必须在 .interaction-card 内（WARN）。

    SSOT 真源：prd_expression_standard.md 区块 C E.3 第 2 条
    禁令：含「交互说明 —」/「状态差异说明」/「列表回显说明」/「数据展示说明」/
    「触点交互说明」字面的文本，其元素父链路必须含 .interaction-card 容器
    （防 PM 自造 div / section / <h3> 等替代标准结构）。
    豁免：pre/code 块内字面（spec/示例代码引用）；changelog 表「修改交互说明」
    （不含 em-dash，自然不命中）。
    WARN 阶段：对齐 S4-28 dry-run 纪律（≥ 2 仓 + FP < 30% 后升 FAIL）。
    """
    r.section("交互说明字面 vs .interaction-card 父链路（S4-41 / SSOT #62 E.3 第 2 条，WARN）")

    parser = _InteractionCardClassComplianceChecker()
    try:
        parser.feed(prd_html)
        parser.close()
    except Exception as e:
        r.warn(f"S4-41 解析异常（不阻断）：{e}")
        return

    if not parser.violations:
        r.ok(".interaction-card 外无典型交互说明字面残留（S4-41 PASS）")
        return

    r.warn(
        f"S4-41：.interaction-card 外 {len(parser.violations)} 处典型交互说明字面"
        f"（违规 WARN 阶段，可能用自造结构替代 .interaction-card 标准容器）：\n  "
        + "\n  ".join(
            f"line {line}: 命中字面「{phrase}」上下文「{ctx}」"
            for line, phrase, ctx in parser.violations[:10]
        )
        + (f"\n  （共 {len(parser.violations)} 处，仅显示前 10 条）"
           if len(parser.violations) > 10 else "")
        + f"\n修复方向：自造结构替换为 `.interaction-card > (.card-title + .state-diff-note + .data-sub-title + <table>)`"
          f" 标准结构；详见 `prd_expression_standard.md` 区块 C E.3 第 2 条"
    )


# ── S4-42｜.fb-state-loading 内禁 inline padding 覆盖（SSOT #63 Skeleton tokens，WARN）─

class _SkeletonInlinePaddingChecker(HTMLParser):
    """扫 prd.html 中 .fb-state-loading 元素是否含 inline padding 覆盖。

    SSOT 真源：bujue-design-system/tokens.md skeleton tokens 段 + prd_template.html :root + 平台 selector
    禁令：.fb-state-loading 元素 style 属性禁含 padding 字面（模板 :root 已声明 --skel-*-padding tokens
    + 平台 selector 自动应用，PM 在 drafts 中默认继承，无需 inline 覆盖）
    WARN 阶段：dry-run ≥ 2 仓 + FP < 30% 后升 FAIL（同 S4-28 v3 纪律）
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.violations: list[tuple[int, str]] = []  # (line, style)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes: set[str] = set()
        style = ""
        for k, v in attrs:
            if k == "class" and v:
                classes = set(v.split())
            elif k == "style" and v:
                style = v

        if "fb-state-loading" in classes and style:
            if re.search(r"padding\s*:", style, re.IGNORECASE):
                line, _col = self.getpos()
                self.violations.append((line, style))


def check_skeleton_inline_padding(prd_html: str, r: Report) -> None:
    """S4-42 / SSOT #63 — .fb-state-loading 内禁 inline padding 覆盖（WARN）。

    SSOT 真源：bujue-design-system/tokens.md skeleton tokens 段
    禁令：.fb-state-loading 元素 style 属性禁含 padding 字面
    WARN 阶段：对齐 S4-28 dry-run 纪律
    """
    r.section(".fb-state-loading inline padding 覆盖扫描（S4-42 / SSOT #63，WARN）")

    parser = _SkeletonInlinePaddingChecker()
    try:
        parser.feed(prd_html)
        parser.close()
    except Exception as e:
        r.warn(f"S4-42 解析异常（不阻断）：{e}")
        return

    if not parser.violations:
        r.ok(".fb-state-loading 元素无 inline padding 覆盖（S4-42 PASS）")
        return

    r.warn(
        f"S4-42：.fb-state-loading 元素 {len(parser.violations)} 处 inline padding 覆盖"
        f"（违规 WARN 阶段）：\n  "
        + "\n  ".join(
            f"line {line}: style=\"{style[:80]}{'...' if len(style) > 80 else ''}\""
            for line, style in parser.violations[:10]
        )
        + (f"\n  （共 {len(parser.violations)} 处，仅显示前 10 条）"
           if len(parser.violations) > 10 else "")
        + "\n修复方向：删除 inline padding；模板 :root 已声明 --skel-*-padding tokens"
          " 由平台 selector 自动应用；详见 `bujue-design-system/tokens.md` skeleton 段"
    )


# ── S4-43｜data-tp 容器级唯一性纪律（SSOT #64，WARN dry-run）─────────────────

class _DataTpContainerUniquenessChecker(HTMLParser):
    """扫 prd.html 中每 *-frame 内 data-tp 出现统计。

    SSOT 真源：proto_contract.md §四 触点容器级唯一性纪律
    禁令：同一 data-tp 在同一 *-frame 内出现 > 1 次（chip group/radio/tab 反 pattern）
    豁免：list/table 多实例（PM/Sup 看 WARN 上下文人审，dry-run 阶段不机械化判定）

    解析策略：追踪 div 嵌套栈，标识哪些 div 是 *-frame；data-tp 出现时记录到最近
    *-frame 的 tp_map；frame 关闭时统计同 ID > 1 次 → WARN。
    """

    FRAME_CLASSES = {"phone-frame", "desktop-frame", "tablet-frame", "h5-frame", "miniprogram-frame"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._div_stack: list[dict] = []
        self.violations: list[tuple[str, str, list[int]]] = []  # (frame_class, tp_id, lines)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes: set[str] = set()
        data_tp = ""
        for k, v in attrs:
            if k == "class" and v:
                classes = set(v.split())
            elif k == "data-tp" and v:
                data_tp = v

        # 仅 div 入嵌套栈（追踪 frame 深度）
        if tag == "div":
            frame_class = next((c for c in classes if c in self.FRAME_CLASSES), None)
            entry = {"is_frame": frame_class is not None, "frame_class": frame_class, "tp_map": {} if frame_class else None}
            self._div_stack.append(entry)

        # 所有 tag 都检查 data-tp（button/a/li/td 等都可能含 data-tp）
        if data_tp:
            for frame_div in reversed(self._div_stack):
                if frame_div["is_frame"]:
                    line, _ = self.getpos()
                    frame_div["tp_map"].setdefault(data_tp, []).append(line)
                    break

    def handle_endtag(self, tag: str) -> None:
        if tag != "div" or not self._div_stack:
            return
        entry = self._div_stack.pop()
        if entry["is_frame"]:
            for tp_id, lines in entry["tp_map"].items():
                if len(lines) > 1:
                    self.violations.append((entry["frame_class"], tp_id, lines))


def check_prd_data_tp_container_uniqueness(prd_html: str, r: Report) -> None:
    """S4-43 / SSOT #64 — data-tp 容器级唯一性扫描（WARN dry-run 阶段）。

    SSOT 真源：proto_contract.md §四 触点容器级唯一性纪律
    禁令：同一 data-tp 在同一 *-frame 内出现 > 1 次
    豁免：list/table 多实例（PM/Sup 看 WARN 上下文人审）
    dry-run 阶段：仅 WARN 收集数据，list/table 豁免启发式待样本充分后设计
    """
    r.section("data-tp 容器级唯一性扫描（S4-43 / SSOT #64，WARN dry-run）")

    parser = _DataTpContainerUniquenessChecker()
    try:
        parser.feed(prd_html)
        parser.close()
    except Exception as e:
        r.warn(f"S4-43 解析异常（不阻断）：{e}")
        return

    if not parser.violations:
        r.ok("所有 *-frame 内 data-tp 容器级唯一（S4-43 PASS）")
        return

    r.warn(
        f"S4-43：检测到 {len(parser.violations)} 个 data-tp 在同一 *-frame 内重复出现"
        f"（WARN dry-run；list/table 多实例豁免由 PM/Sup 人审上下文）：\n  "
        + "\n  ".join(
            f".{frame_class} 内 data-tp=\"{tp_id}\" 出现 {len(lines)} 次（行 {lines[:5]}{'...' if len(lines) > 5 else ''}）"
            for frame_class, tp_id, lines in parser.violations[:10]
        )
        + (f"\n  （共 {len(parser.violations)} 个违规 ID，仅显示前 10 条）"
           if len(parser.violations) > 10 else "")
        + "\n修复方向：chip group/radio/tab 容器级标 data-tp 1 次（移除子选项重复标）；"
          "list/table 同模板多实例合规（spec §.3 表 1 行说明即可，PM/Sup 看上下文人审判定）；"
          "详见 `proto_contract.md §四 触点容器级唯一性纪律`"
    )


# ── 主入口 ────────────────────────────────────────────────────────────────────

def _check_pre_commit_hook_installed() -> str | None:
    """检测 .git/hooks/pre-commit 是否已安装（指向仓库 hook 源）。
    返回 None = 已装/检查不适用；返回 str = WARN 信息。
    SSOT 真源：`pm-workflow/rules/agent_dispatch_protocol.md`「PM / Supervisor Agent 文件改动权限边界」第 5 条 / SSOT 双锚 #31。"""
    git_hook = REPO_ROOT / ".git" / "hooks" / "pre-commit"
    expected = REPO_ROOT / "pm-workflow" / "scripts" / "hooks" / "pre-commit"
    if not expected.exists():
        return None
    if not git_hook.exists():
        return (
            "git pre-commit hook 未安装,L1+L2 混合提交防御失效（SSOT 双锚 #31 机械兜底层退化）。"
            "请执行: bash pm-workflow/scripts/install_hooks.sh"
        )
    if git_hook.is_symlink():
        try:
            if git_hook.resolve() == expected.resolve():
                return None
        except OSError:
            pass
    try:
        if git_hook.read_text(encoding="utf-8") == expected.read_text(encoding="utf-8"):
            return None
    except (OSError, UnicodeDecodeError):
        pass
    return (
        "git pre-commit hook 与 pm-workflow/scripts/hooks/pre-commit 内容/指向不一致,"
        "可能是手工创建或已过期。请重跑: bash pm-workflow/scripts/install_hooks.sh"
    )


# ── SSOT #66 spec.md SSOT 输入 schema 严格化（2026-06-03 落地）──────────────
#
# 治本路径：兑现 SSOT #61 "后续 ROI 评估补 precheck_stage4 章节完整度校验" 的 B 组待补承诺。
# #61 文档级三层（规范 + PM 自审 + Foundation 落地）+ #66 精确机械化兜底（5 新 check_*）。
#
# 5 维度（均 WARN 阶段，按 S4-28 v3 纪律待 ≥ 2 仓 dry-run FP < 30% 后升 FAIL）：
# - S4-44 模块子块完整度（7 必填 .1/.2/.2A/.3/.3A/.4/.5/.7）
# - S4-45 Gherkin 完整度（S2.MXX.7 每状态 4 子项 + ```gherkin 围栏 Given/When/Then）
# - S4-46 API ID 闭环（spec API-XXX ⊆ 产品定义 §10）
# - S4-47 NB ID 闭环（spec NB-XXX ⊆ ledger ∪ scaffold.notes ∪ §S0.5）
# - S4-48 模块编号连续性 + 子段层级父子约束（.2A→.2 / .3A→.3）
#
# 启发式豁免：spec.md 顶层无 `^## S2\.M\d+` → 旧版 spec（SSOT #61 升级前），全部跳过

# SSOT #61 升级后 §三.5 必填子块（7 个）
SPEC_REQUIRED_SUBSECTIONS = [".1", ".2", ".2A", ".3", ".3A", ".4", ".5", ".7"]
SPEC_OPTIONAL_SUBSECTIONS = [".6", ".8"]  # .6 API 摘要（[Should]）/ .8 本页新增组件（[Should]）
SPEC_MODULE_RE = re.compile(r"^## S2\.(M\d+) 模块概述", re.MULTILINE)


def check_spec_module_subsections_completeness(
    data: dict, spec_md: str, r: Report
) -> None:
    """SSOT #66 / S4-44 — spec.md 模块子块完整度（WARN）。

    每个 S2.MXX 模块校验 7 必填子块覆盖率（.1/.2/.2A/.3/.3A/.4/.5/.7）。
    启发式豁免：spec 顶层无 `^## S2\\.M\\d+` 段头 → 旧版 spec（SSOT #61 升级前），跳过。
    """
    r.section("SSOT #66 / S4-44 spec 模块子块完整度（WARN）")

    modules_in_spec = SPEC_MODULE_RE.findall(spec_md)
    if not modules_in_spec:
        r.ok("spec.md 无 S2.MXX 模块段头（旧版 spec / 跳过）")
        return

    missing_per_module: list[tuple[str, list[str]]] = []
    for mid in modules_in_spec:
        missing = []
        for sub in SPEC_REQUIRED_SUBSECTIONS:
            pattern = re.compile(rf"^## S2\.{mid}\{sub}\s", re.MULTILINE)
            if not pattern.search(spec_md):
                missing.append(sub)
        if missing:
            missing_per_module.append((mid, missing))

    if missing_per_module:
        examples = "; ".join(
            f"{mid} 缺 {','.join(subs)}" for mid, subs in missing_per_module[:5]
        )
        suffix = " ..." if len(missing_per_module) > 5 else ""
        r.warn(
            f"spec.md {len(missing_per_module)}/{len(modules_in_spec)} 个模块缺必填子块"
            f"（SSOT #61 升级后 7 必填 .1/.2/.2A/.3/.3A/.4/.5/.7）："
            f"{examples}{suffix} — 详 proto_spec_md.md §三.5"
        )
    else:
        r.ok(
            f"spec.md {len(modules_in_spec)} 个模块 7 必填子块全覆盖（"
            f"{','.join(SPEC_REQUIRED_SUBSECTIONS)}）"
        )


def check_spec_gherkin_completeness(
    data: dict, spec_md: str, r: Report
) -> None:
    """SSOT #66 / S4-45 — spec.md S2.MXX.7 Gherkin 完整度（WARN）。

    S2.MXX.7 段内每状态条目（`^\\*\\*P\\d+-` 锚行）必含 4 子项「互斥说明 / 触发条件 /
    页面表现 / 验收标准」+ 验收标准下必有 ```gherkin 围栏 + 围栏内含 Given/When/Then 三段。
    启发式豁免：spec 无 .7 段 → 旧版 spec，跳过。
    """
    r.section("SSOT #66 / S4-45 spec S2.MXX.7 Gherkin 完整度（WARN）")

    s7_section_re = re.compile(r"^## S2\.M\d+\.7[^\n]*$", re.MULTILINE)
    s7_section_marks = list(s7_section_re.finditer(spec_md))
    if not s7_section_marks:
        r.ok("spec.md 无 S2.MXX.7 段头（旧版 spec / 跳过）")
        return

    # 状态锚双格式适配（SSOT #61 升级前后）：
    # 旧格式（报价工具）：**P01-default**（页-状态横杠拼接）
    # 新格式（私域，SSOT #61 NB-SSOT61-01 后）：**S01：default(...)**（### P01 段下 S 系列）
    state_anchor_re = re.compile(
        r"^\*\*(P\d+-[\w-]+|S\d+[：:][^\*\n]{1,100})\*\*", re.MULTILINE
    )
    next_section_re = re.compile(
        r"^## S2\.M\d+\.[89]|^## S2\.M\d+ 模块|^## [^S]", re.MULTILINE
    )
    SUB_ITEMS = ["互斥说明", "触发条件", "页面表现", "验收标准"]
    GHERKIN_FENCE_RE = re.compile(r"```gherkin\b")
    GIVEN_RE = re.compile(r"^\s*Given\s", re.MULTILINE)
    WHEN_RE = re.compile(r"^\s*When\s", re.MULTILINE)
    THEN_RE = re.compile(r"^\s*Then\s", re.MULTILINE)

    total_states = 0
    violations: list[str] = []

    for mark in s7_section_marks:
        sec_start = mark.start()
        next_match = next_section_re.search(spec_md, mark.end())
        sec_end = next_match.start() if next_match else len(spec_md)
        sec_text = spec_md[sec_start:sec_end]

        mid_match = re.match(r"^## S2\.(M\d+)\.7", sec_text)
        mid = mid_match.group(1) if mid_match else "?"

        state_anchors = list(state_anchor_re.finditer(sec_text))
        for j, sa in enumerate(state_anchors):
            total_states += 1
            state_id = sa.group(1)
            sub_start = sa.end()
            sub_end = (
                state_anchors[j + 1].start()
                if j + 1 < len(state_anchors)
                else len(sec_text)
            )
            sub_text = sec_text[sub_start:sub_end]

            missing_items: list[str] = []
            for item in SUB_ITEMS:
                if item not in sub_text:
                    missing_items.append(item)

            # Gherkin 围栏（仅当含「验收标准」时校验，避免与"缺验收标准"双报）
            if "验收标准" in sub_text:
                fence_match = GHERKIN_FENCE_RE.search(sub_text)
                if not fence_match:
                    missing_items.append("Gherkin围栏")
                else:
                    # 围栏内 Given/When/Then 三段
                    gh_start = fence_match.end()
                    gh_close = sub_text.find("```", gh_start)
                    gh_text = (
                        sub_text[gh_start:gh_close] if gh_close > 0 else sub_text[gh_start:]
                    )
                    if not GIVEN_RE.search(gh_text):
                        missing_items.append("Given")
                    if not WHEN_RE.search(gh_text):
                        missing_items.append("When")
                    if not THEN_RE.search(gh_text):
                        missing_items.append("Then")

            if missing_items:
                violations.append(f"{mid}-{state_id} 缺[{','.join(missing_items)}]")

    if violations:
        examples = "; ".join(violations[:5])
        suffix = " ..." if len(violations) > 5 else ""
        r.warn(
            f"spec.md {len(violations)}/{total_states} 个 .7 状态条目缺 Gherkin 完整度要素："
            f"{examples}{suffix} — 详 proto_spec_md.md §三.5 §S2.M[XX].7"
        )
    else:
        r.ok(f"spec.md {total_states} 个 .7 状态条目 Gherkin 完整度全覆盖")


def check_spec_api_id_closure(data: dict, spec_md: str, r: Report) -> None:
    """SSOT #66 / S4-46 — spec.md API ID 引用闭环（WARN）。

    spec.md 所有 API-XXX 引用 ⊆ 产品定义 §10 API-XXX 定义集合。
    启发式豁免：产品定义文件不存在（阶段 4 前置）→ WARN 跳过。
    """
    r.section("SSOT #66 / S4-46 spec API ID 引用闭环（WARN）")

    product = data.get("product", "").strip()
    if not product:
        r.warn("scaffold 无 product 字段，无法定位产品定义文件 → 跳过 API ID 闭环校验")
        return

    prod_def_path = OUTPUT_DIR / f"产品定义_{product}_latest.md"
    if not prod_def_path.exists():
        r.warn(
            f"产品定义文件 {prod_def_path.name} 不存在 → 跳过 API ID 闭环校验（启发式豁免）"
        )
        return

    try:
        prod_def_text = prod_def_path.read_text(encoding="utf-8")
    except OSError as e:
        r.warn(f"产品定义文件读取失败 → 跳过 API ID 闭环校验：{e}")
        return

    api_re = re.compile(r"\bAPI-[A-Za-z0-9-]+\b")
    spec_apis = set(api_re.findall(spec_md))
    def_apis = set(api_re.findall(prod_def_text))

    if not spec_apis:
        r.ok("spec.md 未引用 API-XXX（业务无 API 涉及）")
        return

    not_in_def = sorted(spec_apis - def_apis)
    if not_in_def:
        examples = ", ".join(not_in_def[:5])
        suffix = " ..." if len(not_in_def) > 5 else ""
        r.warn(
            f"spec.md {len(not_in_def)}/{len(spec_apis)} 个 API 引用未在产品定义 §10 定义："
            f"{examples}{suffix} — 详 tmpl_产品定义.md §10 / proto_spec_md.md §三.5 §S2.M[XX].6"
        )
    else:
        r.ok(f"spec.md {len(spec_apis)} 个 API 引用全部在产品定义 §10 闭环")


def check_spec_nb_id_closure(data: dict, spec_md: str, r: Report) -> None:
    """SSOT #66 / S4-47 — spec.md NB ID 引用闭环（WARN）。

    spec.md 所有 NB-XXX 业务引用 ⊆ decisions_ledger.md ∪ scaffold.notes ∪ §S0.5 NB 清单。
    启发式豁免：NB-WE-* / NB-LIT-* / NB-SSOT* / NB-SNB* 等 L2 工作流 NB → 跳过。
    """
    r.section("SSOT #66 / S4-47 spec NB ID 引用闭环（WARN）")

    nb_re = re.compile(r"\bNB-[A-Za-z0-9-]+\b")
    spec_nbs = set(nb_re.findall(spec_md))
    if not spec_nbs:
        r.ok("spec.md 未引用 NB-XXX")
        return

    product = data.get("product", "").strip()
    # 启发式豁免：L2 工作流 NB 前缀（非产品业务 NB）
    L2_NB_PREFIXES = ("NB-WE-", "NB-LIT-", "NB-SSOT", "NB-SNB")
    business_nbs = {nb for nb in spec_nbs if not nb.startswith(L2_NB_PREFIXES)}
    if not business_nbs:
        r.ok(
            f"spec.md {len(spec_nbs)} 个 NB 全部为 L2 工作流 NB（启发式豁免，"
            f"前缀 {L2_NB_PREFIXES}）"
        )
        return

    defined_nbs: set[str] = set()

    # 1. decisions_ledger.md
    ledger_path = OUTPUT_DIR.parent / "process_record" / "decisions_ledger.md"
    if ledger_path.exists():
        try:
            defined_nbs |= set(nb_re.findall(ledger_path.read_text(encoding="utf-8")))
        except OSError:
            pass

    # 2. scaffold.notes
    for note in data.get("notes", []):
        if isinstance(note, dict):
            nb_id = note.get("id", "")
            if isinstance(nb_id, str) and nb_re.match(nb_id):
                defined_nbs.add(nb_id)
        elif isinstance(note, str):
            defined_nbs |= set(nb_re.findall(note))

    # 3. spec.md §S0.5 NB 清单
    s05_match = re.search(
        r"^## S0\.5[^\n]*$.*?(?=^## S1\b|\Z)", spec_md, re.MULTILINE | re.DOTALL
    )
    if s05_match:
        defined_nbs |= set(nb_re.findall(s05_match.group(0)))

    # 4. 产品定义文件 NB（部分 NB 在产品定义 §13 / §11 等段定义）
    prod_def_path = OUTPUT_DIR / f"产品定义_{product}_latest.md"
    if product and prod_def_path.exists():
        try:
            defined_nbs |= set(nb_re.findall(prod_def_path.read_text(encoding="utf-8")))
        except OSError:
            pass

    not_defined = sorted(business_nbs - defined_nbs)
    if not_defined:
        examples = ", ".join(not_defined[:5])
        suffix = " ..." if len(not_defined) > 5 else ""
        r.warn(
            f"spec.md {len(not_defined)}/{len(business_nbs)} 个业务 NB 未在 "
            f"ledger / scaffold.notes / §S0.5 定义："
            f"{examples}{suffix} — 详 decisions_ledger.md / scaffold.json notes"
        )
    else:
        r.ok(
            f"spec.md {len(business_nbs)} 个业务 NB 全部在定义源闭环（"
            f"ledger / scaffold / §S0.5）"
        )


def check_spec_section_numbering_consistency(
    data: dict, spec_md: str, r: Report
) -> None:
    """SSOT #66 / S4-48 — spec.md 模块编号连续性 + 子段层级父子约束（WARN）。

    S2.MXX 模块编号连续（M01 ~ MNN 无跳号）+ .2A 必有父 .2 + .3A 必有父 .3。
    启发式豁免：spec 顶层无 `^## S2\\.M\\d+` 段头 → 旧版 spec，跳过。
    """
    r.section("SSOT #66 / S4-48 spec 模块编号连续性 + 子段父子约束（WARN）")

    modules_in_spec = SPEC_MODULE_RE.findall(spec_md)
    if not modules_in_spec:
        r.ok("spec.md 无 S2.MXX 模块段头（旧版 spec / 跳过）")
        return

    # 1. 模块编号连续性
    mod_nums = sorted({int(m[1:]) for m in modules_in_spec})
    expected_nums = list(range(1, max(mod_nums) + 1))
    missing_nums = sorted(set(expected_nums) - set(mod_nums))

    if missing_nums:
        missing_mids = [f"M{n:02d}" for n in missing_nums]
        r.warn(
            f"spec.md 模块编号不连续：缺 {missing_mids} "
            f"（实际 {[f'M{n:02d}' for n in mod_nums]}）"
        )
    else:
        r.ok(f"spec.md 模块编号连续（M01-M{max(mod_nums):02d}）")

    # 2. .2A 必有父 .2 + .3A 必有父 .3
    parent_violations: list[str] = []
    for mid in modules_in_spec:
        has_2a = re.search(rf"^## S2\.{mid}\.2A\s", spec_md, re.MULTILINE)
        has_2 = re.search(rf"^## S2\.{mid}\.2\s", spec_md, re.MULTILINE)
        if has_2a and not has_2:
            parent_violations.append(f"{mid}.2A 无父 .2")
        has_3a = re.search(rf"^## S2\.{mid}\.3A\s", spec_md, re.MULTILINE)
        has_3 = re.search(rf"^## S2\.{mid}\.3\s", spec_md, re.MULTILINE)
        if has_3a and not has_3:
            parent_violations.append(f"{mid}.3A 无父 .3")

    if parent_violations:
        examples = ", ".join(parent_violations[:5])
        suffix = " ..." if len(parent_violations) > 5 else ""
        r.warn(
            f"spec.md {len(parent_violations)} 处子段层级缺父：{examples}{suffix}"
        )
    else:
        r.ok(
            f"spec.md {len(modules_in_spec)} 个模块子段层级父子约束齐全"
            f"（.2A→.2 / .3A→.3）"
        )


# ── SSOT #67/#68/#69 spec/prd 派生层 + interaction-card schema 机械化（2026-06-04）──
#
# 治本路径：兑现 SSOT #67/#68/#69 三锚配套 precheck 强约束承诺。
# Commit 1 落 L2 真源（spec/prd 规范层）+ Commit 2 落 assemble.py 派生函数 +
# Commit 3 落 precheck 12 个 check_* 函数（本段）。
#
# 12 维度（均 [Should · WARN] 阶段，按 S4-28 v3 / SSOT #66 同型纪律待 ≥ 2 仓真实
# PM 反馈 + FP < 30% 后升 [Must] FAIL）：
#
# SSOT #68 spec/prd 派生层（7 函数）：
#  - S4-49 §S2.MXX.4B 业务规则段头存在 + 非空
#  - S4-50 §S2.MXX.5B 数据规模段头存在 + 非空
#  - S4-51 F-xxx 主页面字段存在 + ∈ 涉及页面
#  - S4-52 F-xxx 4 必填字段齐全（优先级 / 所属旅程 / 涉及页面 / 主页面）
#  - S4-53 prd interaction-card C-4 派生闭环
#  - S4-54 prd A-05 章节已重组（原 article 形态已清除）
#  - S4-55 prd A-索引 4 列完整 + spec F-xxx 数对齐
#
# SSOT #69 interaction-card C-0~C-3 schema 机械化（5 函数）：
#  - S4-56 C-0 状态差异说明子区块
#  - S4-57 C-1 列表回显 4 行表
#  - S4-58 C-2.A C 单元清单 6 列表
#  - S4-59 C-2.B D 字段子表 5 列含 D 触点 ID
#  - S4-60 C-3 触点行 6 列含跳转/边缘
#
# 启发式豁免：5 spec 校验对旧版 spec（无 ^## S2\.M\d+）一律跳过；
# 5 prd schema 校验对无 .interaction-card 的 PRD 跳过；
# C-4 派生闭环对 spec 缺失场景 / outputs 派生未跑场景跳过。

# F-xxx 节锚：详 proto_spec_md.md §三.5 F-xxx 4 必填字段
_F_SECTION_RE = re.compile(r"^####\s+F-(\d+)[：:]\s*(.+?)$", re.MULTILINE)
_F_NEXT_RE = re.compile(r"^####\s+F-\d+[：:]|^###\s|^##\s", re.MULTILINE)
# 4 必填字段（顺序固定）
_F_REQUIRED_FIELDS = ["优先级", "所属旅程", "涉及页面", "主页面"]
# 单字段抽取
_F_FIELD_PATTERNS = {
    "优先级": re.compile(r"\*\*优先级\*\*[：:]\s*([^\s|｜│]+)"),
    "所属旅程": re.compile(r"\*\*所属旅程\*\*[：:]\s*([^|｜│]+?)(?:　?[|｜│]|$)"),
    "涉及页面": re.compile(r"\*\*涉及页面\*\*[：:]\s*([^|｜│]+?)(?:　?[|｜│]|$)"),
    "主页面": re.compile(r"\*\*主页面\*\*[：:]\s*(P-?\d+)"),
}


def _iter_f_sections(spec_md: str):
    """生成 (fid, name, body) 三元组（fid 含前缀 F-，如 F-001）。"""
    matches = list(_F_SECTION_RE.finditer(spec_md))
    for i, m in enumerate(matches):
        fid = f"F-{m.group(1)}"
        name = m.group(2).strip()
        start = m.end()
        # 下一个 #### F-xxx 或 ### / ## 为止
        nxt = _F_NEXT_RE.search(spec_md, start)
        end = nxt.start() if nxt else len(spec_md)
        # 排除本节匹配自身（首节匹配即从 m.end 开始，不会重复）
        body = spec_md[start:end]
        yield fid, name, body


def check_spec_section_4B_business_rules(
    data: dict, spec_md: str, r: Report
) -> None:
    """SSOT #68 / S4-49 — spec.md §S2.MXX.4B 业务规则段头存在 + 非空（WARN）。

    每个 S2.MXX 模块校验 .4B 业务规则段头存在 + 段内非空。
    启发式豁免：spec 顶层无 `^## S2\\.M\\d+` 段头 → 旧版 spec，跳过。
    """
    r.section("SSOT #68 / S4-49 spec §S2.MXX.4B 业务规则段头（WARN）")

    modules_in_spec = SPEC_MODULE_RE.findall(spec_md)
    if not modules_in_spec:
        r.ok("spec.md 无 S2.MXX 模块段头（旧版 spec / 跳过）")
        return

    missing: list[str] = []
    empty: list[str] = []
    for mid in modules_in_spec:
        # 段头存在性
        header_re = re.compile(rf"^## S2\.{mid}\.4B\s", re.MULTILINE)
        m = header_re.search(spec_md)
        if not m:
            missing.append(mid)
            continue
        # 段内非空（到下一个 ## 为止；剔除起始空白后字符数 ≥ 5）
        next_re = re.compile(r"^## S2\.M\d+|^## [^S]", re.MULTILINE)
        nxt = next_re.search(spec_md, m.end())
        seg_end = nxt.start() if nxt else len(spec_md)
        body = spec_md[m.end():seg_end].strip()
        if len(body) < 5:
            empty.append(mid)

    if missing:
        ex = ", ".join(missing[:5])
        suffix = " ..." if len(missing) > 5 else ""
        r.warn(
            f"spec.md {len(missing)}/{len(modules_in_spec)} 个模块缺 .4B 业务规则段头："
            f"{ex}{suffix} — 详 proto_spec_md.md §三.5 §S2.M[XX].4B"
        )
    if empty:
        ex = ", ".join(empty[:5])
        suffix = " ..." if len(empty) > 5 else ""
        r.warn(
            f"spec.md {len(empty)}/{len(modules_in_spec)} 个模块 .4B 段头存在但内容为空："
            f"{ex}{suffix}"
        )
    if not missing and not empty:
        r.ok(f"spec.md {len(modules_in_spec)} 个模块 .4B 业务规则段头齐全 + 非空")


def check_spec_section_5B_data_scale(
    data: dict, spec_md: str, r: Report
) -> None:
    """SSOT #68 / S4-50 — spec.md §S2.MXX.5B 数据规模段头存在 + 非空（WARN）。

    每个 S2.MXX 模块校验 .5B 数据规模段头存在 + 段内非空。
    启发式豁免：spec 顶层无 `^## S2\\.M\\d+` 段头 → 旧版 spec，跳过。
    """
    r.section("SSOT #68 / S4-50 spec §S2.MXX.5B 数据规模段头（WARN）")

    modules_in_spec = SPEC_MODULE_RE.findall(spec_md)
    if not modules_in_spec:
        r.ok("spec.md 无 S2.MXX 模块段头（旧版 spec / 跳过）")
        return

    missing: list[str] = []
    empty: list[str] = []
    for mid in modules_in_spec:
        header_re = re.compile(rf"^## S2\.{mid}\.5B\s", re.MULTILINE)
        m = header_re.search(spec_md)
        if not m:
            missing.append(mid)
            continue
        next_re = re.compile(r"^## S2\.M\d+|^## [^S]", re.MULTILINE)
        nxt = next_re.search(spec_md, m.end())
        seg_end = nxt.start() if nxt else len(spec_md)
        body = spec_md[m.end():seg_end].strip()
        if len(body) < 5:
            empty.append(mid)

    if missing:
        ex = ", ".join(missing[:5])
        suffix = " ..." if len(missing) > 5 else ""
        r.warn(
            f"spec.md {len(missing)}/{len(modules_in_spec)} 个模块缺 .5B 数据规模段头："
            f"{ex}{suffix} — 详 proto_spec_md.md §三.5 §S2.M[XX].5B"
        )
    if empty:
        ex = ", ".join(empty[:5])
        suffix = " ..." if len(empty) > 5 else ""
        r.warn(
            f"spec.md {len(empty)}/{len(modules_in_spec)} 个模块 .5B 段头存在但内容为空："
            f"{ex}{suffix}"
        )
    if not missing and not empty:
        r.ok(f"spec.md {len(modules_in_spec)} 个模块 .5B 数据规模段头齐全 + 非空")


def check_spec_function_main_page_field(
    data: dict, spec_md: str, r: Report
) -> None:
    """SSOT #68 / S4-51 — spec.md F-xxx 主页面字段存在 + ∈ 涉及页面（WARN）。

    每个 F-xxx 节校验「主页面：P-XX」字段存在 + 值 ∈「涉及页面」集合。
    启发式豁免：spec 无 F-xxx 节 → 旧版 spec / 未拆 F-xxx 单元，跳过。
    """
    r.section("SSOT #68 / S4-51 spec F-xxx 主页面字段（WARN）")

    f_sections = list(_iter_f_sections(spec_md))
    if not f_sections:
        r.ok("spec.md 无 F-xxx 节（旧版 spec / 跳过）")
        return

    missing_main: list[str] = []
    not_in_involved: list[str] = []

    for fid, name, body in f_sections:
        main_m = _F_FIELD_PATTERNS["主页面"].search(body)
        involve_m = _F_FIELD_PATTERNS["涉及页面"].search(body)
        if not main_m:
            missing_main.append(fid)
            continue
        # 校验主页面 ∈ 涉及页面集合（标准化：去 "-" 比较数字）
        if involve_m:
            involved_text = involve_m.group(1).strip()
            involved_ids = set(re.findall(r"P-?(\d+)", involved_text))
            main_num = re.match(r"P-?(\d+)", main_m.group(1)).group(1)
            if involved_ids and main_num not in involved_ids:
                not_in_involved.append(
                    f"{fid} 主页面 {main_m.group(1)} ∉ 涉及页面 [{involved_text}]"
                )

    if missing_main:
        ex = ", ".join(missing_main[:5])
        suffix = " ..." if len(missing_main) > 5 else ""
        r.warn(
            f"spec.md {len(missing_main)}/{len(f_sections)} 个 F-xxx 节缺「主页面」字段："
            f"{ex}{suffix} — 详 proto_spec_md.md §三.5 F-xxx 4 必填字段"
        )
    if not_in_involved:
        ex = "; ".join(not_in_involved[:5])
        suffix = " ..." if len(not_in_involved) > 5 else ""
        r.warn(
            f"spec.md {len(not_in_involved)}/{len(f_sections)} 个 F-xxx 节主页面字段值"
            f"不在涉及页面集合内：{ex}{suffix}"
        )
    if not missing_main and not not_in_involved:
        r.ok(f"spec.md {len(f_sections)} 个 F-xxx 节主页面字段齐全 + ∈ 涉及页面")


def check_spec_function_xxx_required(
    data: dict, spec_md: str, r: Report
) -> None:
    """SSOT #68 / S4-52 — spec.md F-xxx 4 必填字段齐全（WARN）。

    每个 F-xxx 节校验 4 必填字段：优先级 / 所属旅程 / 涉及页面 / 主页面。
    启发式豁免：spec 无 F-xxx 节 → 旧版 spec / 未拆 F-xxx 单元，跳过。
    """
    r.section("SSOT #68 / S4-52 spec F-xxx 4 必填字段（WARN）")

    f_sections = list(_iter_f_sections(spec_md))
    if not f_sections:
        r.ok("spec.md 无 F-xxx 节（旧版 spec / 跳过）")
        return

    violations: list[str] = []
    for fid, name, body in f_sections:
        missing = []
        for field in _F_REQUIRED_FIELDS:
            if not _F_FIELD_PATTERNS[field].search(body):
                missing.append(field)
        if missing:
            violations.append(f"{fid} 缺 [{','.join(missing)}]")

    if violations:
        ex = "; ".join(violations[:5])
        suffix = " ..." if len(violations) > 5 else ""
        r.warn(
            f"spec.md {len(violations)}/{len(f_sections)} 个 F-xxx 节缺必填字段："
            f"{ex}{suffix} — 详 proto_spec_md.md §三.5 F-xxx 4 必填字段"
        )
    else:
        r.ok(f"spec.md {len(f_sections)} 个 F-xxx 节 4 必填字段全覆盖")


# C-4 派生痕迹锚（assemble.inject_c4_into_interaction_card 注入边界）
# NB-1 修复（2026-06-04）：兼容两种形式
#   旧（向后兼容）：`<!-- [C4-START] -->...<!-- [C4-END] -->`
#   新（当前注入）：`<!-- [C4-START: prd_id] auto-injected... -->...<!-- [C4-END: prd_id] -->`
# 关键点：`[C4-START` 后允许可选 `: prd_id`，再允许任意注释内容直到 `-->`
_C4_PRD_MARKER_RE = re.compile(
    r"<!--\s*\[C4-START(?:\s*:\s*[^\]]+)?\]\s*[^>]*-->"
    r".*?"
    r"<!--\s*\[C4-END(?:\s*:\s*[^\]]+)?\]\s*-->",
    re.DOTALL,
)
_C4_CROSS_PAGE_RE = re.compile(r"class=\"c4-cross-page-note\"")


def check_prd_c4_derivation_closure(
    data: dict, prd_html: str, spec_md: str, r: Report
) -> None:
    """SSOT #68 / S4-53 — prd interaction-card C-4 派生闭环（WARN）。

    扫 prd.html 中 interaction-card 个数 vs C-4 注入痕迹个数（[C4-START/END]
    包裹块 ∪ c4-cross-page-note 跳转占位）；命中率 < 50% → WARN。
    启发式豁免：prd 无 .interaction-card / spec 无 F-xxx → 跳过（派生未触发）。
    """
    r.section("SSOT #68 / S4-53 prd interaction-card C-4 派生闭环（WARN）")

    ic_count = prd_html.count("class=\"interaction-card\"")
    if ic_count == 0:
        r.ok("prd.html 无 .interaction-card → 跳过 C-4 派生闭环校验")
        return

    if not list(_iter_f_sections(spec_md)):
        r.ok("spec.md 无 F-xxx 节 → 跳过 C-4 派生闭环校验（启发式豁免）")
        return

    c4_full = len(_C4_PRD_MARKER_RE.findall(prd_html))
    c4_cross = len(_C4_CROSS_PAGE_RE.findall(prd_html))
    c4_total = c4_full + c4_cross
    coverage = c4_total / ic_count if ic_count > 0 else 0

    if c4_total == 0:
        r.warn(
            f"prd.html {ic_count} 个 .interaction-card 全部无 C-4 派生痕迹"
            f"（[C4-START/END] 或 c4-cross-page-note 一个都没有）— "
            f"请确认 assemble.py 已跑 assemble_prd 派生（SSOT #68 链路）"
        )
    elif coverage < 0.5:
        r.warn(
            f"prd.html C-4 派生覆盖率 {c4_total}/{ic_count} ({coverage:.0%}) 偏低 "
            f"(< 50%) — 主页面全量 {c4_full} + 副页面缩略 {c4_cross}；"
            f"请核查 spec.md F-xxx 「主页面」字段是否齐全"
        )
    else:
        r.ok(
            f"prd.html C-4 派生覆盖率 {c4_total}/{ic_count} ({coverage:.0%})"
            f"（主页面 {c4_full} + 副页面缩略 {c4_cross}）"
        )


_FRAME_BLOCK_RE = re.compile(
    r'<!--\s*\[FRAME-START:\s*(H-[\w-]+?)(?:\s*\|[^\]]*)?\]\s*-->(.*?)<!--\s*\[FRAME-END:\s*\1\s*\]\s*-->',
    re.DOTALL,
)


def check_render_contract(data: dict, prd_html: str, spec_md: str, r: Report) -> None:
    """SSOT #77 / S4-67 — R8 渲染契约标记完整性（WARN）。

    把「PRD agent 渲染了 spec 声明的某项没有」从事后语义猜测（FP 不可控）转为
    **显式标记 presence 核对**（机械零 FP）。逐帧/逐页核对契约期望项的可追溯标记：
    - 触点 per-frame：spec `.3` 转录的本帧期望触点 ID ⊆ 帧内 `data-tp` 标记集
    - 字段 per-page：spec `.4` 转录的本页期望字段 ⊆ 本页帧 `data-field` 标记集

    缺标记 → WARN（治实验报告 §8 批量摊薄漏搬运；**勾是自报、标记是物证 → 验标记不验勾**）。
    转录器复用 `gen_render_contract`（忠实转录 spec 权威列禁推断；契约天花板有归属）。
    豁免：无 modules / prd 无 FRAME 块 / spec 无 .3/.4 可转录项 → skip。
    **WARN 阶段**（NB-LIT-25-B：≥2 仓真实 PM 反馈 + FP<30% 后升 FAIL；data-field 为新约定，
    既有下游 prd 普遍未标 → WARN 不阻塞，暴露搬运漏损待逐帧补标）。
    """
    r.section("SSOT #77 / S4-67 渲染契约标记完整性（R8，WARN）")
    modules = data.get("modules", [])
    if not modules:
        r.ok("无 modules，跳过渲染契约校验")
        return
    frames = {m.group(1): m.group(2) for m in _FRAME_BLOCK_RE.finditer(prd_html)}
    if not frames:
        r.ok("prd.html 无 FRAME-START/END 块，跳过渲染契约校验")
        return

    missing_tp: list[str] = []
    missing_field: list[str] = []
    total_tp = total_field = 0
    for mod in modules:
        mid = mod.get("id", "")
        if not mod.get("pages"):
            continue
        for page in mod.get("pages", []):
            pid = page.get("id", "")
            # 字段 per-page：本页所有帧合并查 data-field
            exp_fields = {df for df, _ in extract_fields_for_page(spec_md, mid, pid)}
            page_html = "".join(
                fh for fid, fh in frames.items() if fid.startswith(f"H-{mid}-{pid}-")
            )
            present_field = set(re.findall(r'data-field="([^"]+)"', page_html))
            for f in sorted(exp_fields):
                total_field += 1
                if f not in present_field:
                    missing_field.append(f"{mid}-{pid}/{f}")
            # 触点 per-frame：本帧查 data-tp（含内嵌帧 iter_page_prd_ids）
            for prd_id in iter_page_prd_ids(page):
                prefix = f"H-{mid}-{pid}-"
                if not prd_id.startswith(prefix):
                    continue
                state = prd_id[len(prefix):]
                fh = frames.get(prd_id)
                if fh is None:
                    continue  # 帧缺失由 #72 frame 一致性兜
                exp_tp = {t for t, _ in extract_touchpoints_for_state(spec_md, mid, pid, state)}
                present_tp = set(re.findall(r'data-tp="([^"]+)"', fh))
                for t in sorted(exp_tp):
                    total_tp += 1
                    if t not in present_tp:
                        missing_tp.append(f"{prd_id}/{t}")

    if total_tp == 0 and total_field == 0:
        r.ok("spec 无 .3/.4 可转录契约项，跳过渲染契约校验")
        return
    if not missing_tp and not missing_field:
        r.ok(
            f"渲染契约标记完整（触点 {total_tp} 全有 data-tp + 字段 {total_field} 全有 data-field）"
        )
        return

    msg = [
        f"渲染契约标记缺失（治 §8 批量摊薄漏搬运；勾是自报、标记是物证 → 验标记）："
        f"触点缺 {len(missing_tp)}/{total_tp} + 字段缺 {len(missing_field)}/{total_field}"
    ]
    if missing_tp:
        msg.append(f"  触点缺 data-tp（前 10）：{missing_tp[:10]}")
    if missing_field:
        msg.append(f"  字段缺 data-field（前 10）：{missing_field[:10]}")
    msg.append(
        "  修复：PRD agent 逐条照任务卡渲染契约 checklist 渲染缺项 + 打 data-tp/data-field 标记"
        "（详 prd_expression_standard §6.2）；modal-internal 未编入 .3 属 v1 边界归人工对照区"
    )
    r.warn("\n".join(msg))


# A-05 原 article 形态识别锚（在 spec-feature section 内含 feature-block / feature-title 即旧形态）
_A05_LEGACY_RE = re.compile(
    r'<section[^>]*id="spec-feature"[^>]*>.*?<div\s+class="feature-block"',
    re.DOTALL,
)
# 2026-06-04 P0 hot fix Bug 4：S4-54 覆盖度升级 — 3 维度合并检测
# 1) feature-block 旧形态（原有）
# 2) sub-article `<article id="spec-F[0-9]+">` 残留（私域 6 / quotation-tool 2 实证）
# 3) spec-header 字面旧字（`功能需求规格` 应改为 `功能索引`，3 仓 100% 命中）
_A05_SECTION_INNER_RE = re.compile(
    r'<section[^>]*id="spec-feature"[^>]*>(.*?)</section>',
    re.DOTALL,
)
_A05_SUBARTICLE_RE = re.compile(
    r'<article\s+id\s*=\s*"spec-F[0-9]+"', re.IGNORECASE
)
_A05_OLD_HEADER_RE = re.compile(
    r'<div\s+class\s*=\s*"spec-header"\s*>\s*功能需求规格\s*</div>',
)
# 议题 7 / S4-54 维度 4（2026-06-04）：sidebar nav 字面 — `<div class="sidebar-spec-item"
# data-target="spec-feature">功能需求规格</div>` 旧字面（assemble._overwrite_spec_nav_label_from_template
# 治本，gen_scaffold.SPEC_ITEMS spec-feature → 功能索引）
_A05_OLD_SIDEBAR_NAV_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bsidebar-spec-item\b[^"]*"[^>]*\bdata-target\s*=\s*"spec-feature"[^>]*>'
    r'\s*功能需求规格\s*</div>',
    re.IGNORECASE,
)


def check_prd_a05_removed(data: dict, prd_html: str, r: Report) -> None:
    """SSOT #67 / S4-54 — prd A-05 章节已重组为「功能索引」（WARN）。

    扫 prd.html `<section id="spec-feature">` 内 3 维度 + sidebar 1 维度
    （2026-06-04 P0 hot fix Bug 4 升级覆盖度 3 维度 + 议题 7 NB-WE-2A-R2-02
    扩 sidebar 维度，3 仓 widespread bug 实证）：

    1. feature-block / feature-title 旧 article 形态（原 S4-54 行为）
    2. `<article id="spec-F[0-9]+">` sub-article 残留（Foundation 历史产物未清；
       私域主页 6 处 / quotation-tool 2 处实证）
    3. spec-header 字面仍为「功能需求规格」（应改为「功能索引」；3 仓 100% 命中
       上线后 P0 现象 — 真源 prd_expression_standard.md §三 A-05 L656）
    4. **sidebar nav `<div class="sidebar-spec-item" data-target="spec-feature">功能需求规格</div>`
       旧字面**（议题 7 / NB-WE-2A-R2-02 P1 — sidebar 在 spec-feature section 外，
       3 仓上线后 100% 命中；assemble._overwrite_spec_nav_label_from_template 治本）

    任一维度违规 → WARN（不升 FAIL，保持 SSOT #59 F.1 v1 上线策略）。
    启发式豁免：prd 无 spec-feature section AND 无 sidebar 旧字面 → 跳过。
    """
    r.section("SSOT #67 / S4-54 prd A-05 旧 article 形态清除 + sidebar nav 字面（WARN）")

    sec_m = _A05_SECTION_INNER_RE.search(prd_html)
    # 维度 4：sidebar nav 旧字面（在 spec-feature section 外的 sidebar 内，独立判定）
    sidebar_old_label_hit = bool(_A05_OLD_SIDEBAR_NAV_RE.search(prd_html))
    if not sec_m and not sidebar_old_label_hit:
        r.ok("prd.html 无 spec-feature section + sidebar 无旧字面 → 跳过 A-05 校验")
        return

    violations: list[str] = []
    sec_inner = sec_m.group(1) if sec_m else ""

    # 维度 1：feature-block 旧形态
    if sec_m and _A05_LEGACY_RE.search(prd_html):
        violations.append(
            "feature-block 旧 article 形态（A-05 应重组为 4 列轻量索引）"
        )

    # 维度 2：sub-article spec-F[0-9]+ 残留
    if sec_m:
        sub_articles = _A05_SUBARTICLE_RE.findall(sec_inner)
        if sub_articles:
            violations.append(
                f"sub-article 残留 {len(sub_articles)} 处（<article id=\"spec-F0X\">；"
                "Foundation 历史产物未清，assemble.py 应自动清除）"
            )

    # 维度 3：spec-header 字面旧字
    if sec_m and _A05_OLD_HEADER_RE.search(sec_inner):
        violations.append(
            "spec-header 字面仍为「功能需求规格」（真源 prd_expression_standard.md "
            "§三 A-05 已改为「功能索引」；assemble.py 应自动替换）"
        )

    # 维度 4：sidebar nav 旧字面（议题 7 / NB-WE-2A-R2-02 P1）
    if sidebar_old_label_hit:
        violations.append(
            "sidebar nav `data-target=\"spec-feature\"` 字面仍为「功能需求规格」"
            "（真源 gen_scaffold.SPEC_ITEMS 已改为「功能索引」；assemble.py "
            "_overwrite_spec_nav_label_from_template 应自动替换 — 议题 7 / "
            "NB-WE-2A-R2-02 P1）"
        )

    if violations:
        r.warn(
            "prd.html spec-feature section A-05 未完成 SSOT #67 重组 — "
            + "；".join(violations)
            + "；建议重跑 `python pm-workflow/scripts/assemble.py prd --force-overwrite` "
            + "应用最新 inject_function_overview_index 4 联 fix"
        )
    else:
        r.ok("prd.html A-05 已完成 SSOT #67 重组（feature-block / sub-article / header 字面 3 维度 PASS）")


# A-索引 4 列识别：spec-feature section 内 4 列 thead 字面
_A_INDEX_THEAD_RE = re.compile(
    r'<section[^>]*id="spec-feature"[^>]*>.*?<thead>.*?'
    r'编号.*?功能名.*?优先级.*?主页面.*?</thead>',
    re.DOTALL,
)
# spec-feature section 内 tbody 行计数
_A_INDEX_SECTION_RE = re.compile(
    r'<section[^>]*id="spec-feature"[^>]*>(.*?)</section>', re.DOTALL
)
_TBODY_TR_RE = re.compile(r"<tr>.*?</tr>", re.DOTALL)


def check_prd_a_index_complete(
    data: dict, prd_html: str, spec_md: str, r: Report
) -> None:
    """SSOT #67 / S4-55 — prd A-索引 4 列完整 + spec F-xxx 数对齐（WARN）。

    扫 prd.html spec-feature section 内 4 列表头（编号/功能名/优先级/主页面）+
    tbody 行数 == spec.md F-xxx 节数。
    启发式豁免：prd 无 spec-feature section → 跳过；spec 无 F-xxx → 跳过。
    """
    r.section("SSOT #67 / S4-55 prd A-索引 4 列 + spec F-xxx 数对齐（WARN）")

    if 'id="spec-feature"' not in prd_html:
        r.ok("prd.html 无 spec-feature section → 跳过 A-索引校验")
        return

    f_sections = list(_iter_f_sections(spec_md))
    if not f_sections:
        r.ok("spec.md 无 F-xxx 节 → 跳过 A-索引校验（启发式豁免）")
        return

    # 1. 4 列表头存在
    if not _A_INDEX_THEAD_RE.search(prd_html):
        r.warn(
            "prd.html spec-feature section 缺 4 列表头"
            "（编号 / 功能名 / 优先级 / 主页面）"
            " — 详 prd_expression_standard.md §三 A-05"
        )
        return

    # 2. tbody 行数 == F-xxx 节数（剔除 thead 内的 tr）
    sec_m = _A_INDEX_SECTION_RE.search(prd_html)
    if not sec_m:
        r.ok("prd.html spec-feature section 解析失败 → 跳过行数对齐")
        return
    sec_inner = sec_m.group(1)
    # 简化：剔除 <thead>...</thead> 段，统计余下 <tr>
    no_thead = re.sub(r"<thead>.*?</thead>", "", sec_inner, flags=re.DOTALL)
    tr_count = len(_TBODY_TR_RE.findall(no_thead))

    if tr_count != len(f_sections):
        r.warn(
            f"prd.html A-索引行数 {tr_count} ≠ spec.md F-xxx 节数 {len(f_sections)}"
            f" — 可能 assemble 派生不完整 / spec F-xxx 节添加后未重 assemble"
        )
    else:
        r.ok(
            f"prd.html A-索引 4 列齐全 + 行数 {tr_count} == spec.md F-xxx 节数"
        )


# ── SSOT #69 interaction-card C-0~C-3 schema 机械化（5 函数，S4-56~60）──

_INTERACTION_CARD_RE = re.compile(
    r'<div\s+class="interaction-card"[^>]*>(.*?)</div>\s*(?=<div\s+class="interaction-card"|</section|<section)',
    re.DOTALL,
)


def _iter_interaction_cards(prd_html: str):
    """生成 prd.html 中所有 interaction-card 的内部 HTML 片段。

    粗粒度匹配（嵌套 div 不严格平衡，足够 5 schema 校验用）。
    """
    # 简化：用前向锚 + 下一个 interaction-card 或 section 边界
    start = 0
    while True:
        m = re.search(r'<div\s+class="interaction-card"[^>]*>', prd_html[start:])
        if not m:
            return
        actual_start = start + m.end()
        # 找下一个 interaction-card 或 </section>
        nxt = re.search(
            r'<div\s+class="interaction-card"[^>]*>|</section>',
            prd_html[actual_start:],
        )
        end = actual_start + nxt.start() if nxt else len(prd_html)
        yield prd_html[actual_start:end]
        start = end


# 议题 23（2026-06-05，PM 反审治本）：narrative-only 一级判定精化辅助
#
# 旧版用裸 regex `数据展示说明 / 字段说明 / 触点交互说明` 字面 grep 判定
# "卡内有 sub-title 字面但未容器化"，被业务规则结构 cell（td/th/label）+
# HTML attribute（data-zh / data-en / title / aria-label / alt）内的字面
# 误命中（bujue-quotation-tool card #111-#118 实证 8/8 FP）。
#
# 真 narrative-only 场景：`<p>字段说明 — XXX</p>` 顶层散文段（PM 写源未按
# §四 C-2.B 容器化 schema 渲染）。识别策略：先剥除业务结构 cell 与 HTML
# attribute 内容（置空），再在剩余"卡内顶层散文"上 grep —— 命中即真违规。
#
# 同型扩展 S4-58「数据展示说明」/ S4-60「触点交互说明」。
_TD_INNER_RE = re.compile(r"<td\b[^>]*>.*?</td>", re.DOTALL | re.IGNORECASE)
_TH_INNER_RE = re.compile(r"<th\b[^>]*>.*?</th>", re.DOTALL | re.IGNORECASE)
_LABEL_INNER_RE = re.compile(r"<label\b[^>]*>.*?</label>", re.DOTALL | re.IGNORECASE)
# 属性值（data-*/title/aria-label/alt/placeholder）整段连同等号 / 引号置空
_TAG_ATTR_RE = re.compile(r'<[a-zA-Z][^>]*>', re.DOTALL)
_ATTR_VALUE_RE = re.compile(r'\s([a-zA-Z_:][\w:-]*)\s*=\s*"([^"]*)"')


def _strip_narrative_noise(card_html: str) -> str:
    """剥除 narrative-only 一级判定的噪声源,返回"卡内真 narrative 段"。

    剥除范围（依次置空,保留外壳避免破坏结构）：
    1. `<td>...</td>` / `<th>...</th>` / `<label>...</label>` 内文本
       （业务规则 cell / 表头 / form label 内字面 ≠ narrative-only sub-title）
    2. HTML 标签所有属性值（data-zh / data-en / title / aria-label / alt /
       placeholder 等内字面 ≠ narrative-only sub-title）

    剩余文本 = 卡内真 narrative 散文（`<p>...</p>` 顶层段 / `<div>...</div>` 直接
    文本节点 / 标签外文本等）。在此结果上 grep `字段说明 / 数据展示说明 / 触点交互说明`
    可精确识别"PM 未容器化的散文 sub-title"违规。

    注意：此函数不修复 HTML 结构,只用于 grep 字面判定;不应用于其他用途。
    """
    s = _TD_INNER_RE.sub("<td></td>", card_html)
    s = _TH_INNER_RE.sub("<th></th>", s)
    s = _LABEL_INNER_RE.sub("<label></label>", s)
    # 剥除所有标签的属性值（保留属性名 + 等号 + 空引号防破坏结构判定）
    def _scrub_attrs(m: re.Match) -> str:
        return _ATTR_VALUE_RE.sub(r' \1=""', m.group(0))
    s = _TAG_ATTR_RE.sub(_scrub_attrs, s)
    return s


_C0_STATE_DIFF_RE = re.compile(r'class="state-diff-note"')


def check_interaction_c0_state_diff_note(prd_html: str, r: Report) -> None:
    """SSOT #69 / S4-56 — interaction-card C-0 状态差异说明子区块（WARN）。

    每个 interaction-card 应含 `<div class="state-diff-note">` 子区块。
    启发式豁免：prd 无 interaction-card → 跳过。
    """
    r.section("SSOT #69 / S4-56 interaction-card C-0 状态差异说明（WARN）")

    cards = list(_iter_interaction_cards(prd_html))
    if not cards:
        r.ok("prd.html 无 .interaction-card → 跳过 C-0 校验")
        return

    missing = sum(1 for c in cards if not _C0_STATE_DIFF_RE.search(c))
    if missing > 0:
        r.warn(
            f"prd.html {missing}/{len(cards)} 个 interaction-card 缺 C-0 "
            f".state-diff-note 子区块 — 详 prd_expression_standard.md §四 区块 C C-0"
        )
    else:
        r.ok(f"prd.html {len(cards)} 个 interaction-card C-0 .state-diff-note 全覆盖")


# C-1 列表回显说明：data-sub-title「列表回显说明」+ 4 行固定行目
_C1_TITLE_RE = re.compile(r'列表回显说明')
_C1_ROW_KEYS = ["排序规则", "加载方式", "总数回显", "空列表判断"]


def check_interaction_c1_list_table(prd_html: str, r: Report) -> None:
    """SSOT #69 / S4-57 — interaction-card C-1 列表回显 4 行表（WARN）。

    含「列表回显说明」标题的 interaction-card，其后表格须含 4 固定行目：
    排序规则 / 加载方式 / 总数回显 / 空列表判断。
    启发式豁免：①prd 无 interaction-card 跳过；②不含「列表回显说明」标题的卡跳过
    （无列表场景），扫含此标题的卡。
    """
    r.section("SSOT #69 / S4-57 interaction-card C-1 列表回显 4 行表（WARN）")

    cards = list(_iter_interaction_cards(prd_html))
    if not cards:
        r.ok("prd.html 无 .interaction-card → 跳过 C-1 校验")
        return

    cards_with_c1 = [c for c in cards if _C1_TITLE_RE.search(c)]
    if not cards_with_c1:
        r.ok(f"prd.html {len(cards)} 个 interaction-card 均无「列表回显说明」段（跳过 C-1 列表表格校验）")
        return

    violations: list[str] = []
    for i, c in enumerate(cards_with_c1):
        # 在「列表回显说明」标题后 1500 字符内找 4 行 key
        idx = _C1_TITLE_RE.search(c).end()
        region = c[idx:idx + 1500]
        missing = [k for k in _C1_ROW_KEYS if k not in region]
        # 排除「本帧无列表」等显式注明（C-1 规范允许无列表注明）
        if "本帧无列表" in region:
            continue
        if missing:
            violations.append(f"#{i + 1} 缺[{','.join(missing)}]")

    if violations:
        ex = "; ".join(violations[:5])
        suffix = " ..." if len(violations) > 5 else ""
        r.warn(
            f"prd.html {len(violations)}/{len(cards_with_c1)} 个 C-1 列表表格"
            f"缺固定行目：{ex}{suffix} — 详 prd_expression_standard.md §四 区块 C C-1"
        )
    else:
        r.ok(
            f"prd.html {len(cards_with_c1)} 个 C-1 列表表格 4 行目全覆盖"
        )


# C-2.A C 单元清单 6 列识别（thead 字面）
_C2A_THEAD_COLS = ["C 触点 ID", "单元名称", "是否封装为组件", "渲染时机", "跨平台差异", "关联 T 触点"]
# 议题 17 容器锁定升级（一级判定）：sub-title 必须在 `<div class="data-sub-title">…</div>`
# 容器内（与 assemble._C2_SUBTITLE_PRESENT_RE 同源），治"narrative 字面命中 FP"
_C2A_TITLE_CONTAINER_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>[^<]*数据展示说明[^<]*</div>',
    re.IGNORECASE,
)
# 兼容旧版：narrative 字面检测（用于"未容器化 sub-title"二级判定提示）
_C2A_TITLE_RE = re.compile(r'数据展示说明')


def check_interaction_c2a_unit_index(prd_html: str, r: Report) -> None:
    """SSOT #69 / S4-58 — interaction-card C-2.A C 单元清单 6 列表（WARN，议题 17 二级判定升级）。

    含「数据展示说明」`<div class="data-sub-title">` 容器锁定 sub-title 头的
    interaction-card，其后第一张 table 应是 C-2.A 索引层，含 6 列：C 触点 ID /
    单元名称 / 是否封装为组件 / 渲染时机 / 跨平台差异 / 关联 T 触点。

    议题 17 二级判定升级（治"sub-title 不存在但表存在 / sub-title 存在但表列缺"漏检）：
    - 一级（sub-title 头存在性）：容器锁定 `<div class="data-sub-title">数据展示说明</div>`
      （治旧版裸字面 regex 命中 narrative 字面 FP）；裸字面命中 + 容器缺 → WARN 提示
      "sub-title 未容器化"
    - 二级（列完整）：在容器锁定命中后 + 表 6 列齐全
    任一级失败 → WARN 分级提示哪一级缺。

    启发式豁免：①prd 无 interaction-card 跳过；②含「本帧无数据展示」豁免（议题 15
    assemble 派生兜底已覆盖；PM 写源含豁免文案亦合规）。
    """
    r.section("SSOT #69 / S4-58 interaction-card C-2.A 6 列单元清单（WARN，议题 17 二级判定）")

    cards = list(_iter_interaction_cards(prd_html))
    if not cards:
        r.ok("prd.html 无 .interaction-card → 跳过 C-2.A 校验")
        return

    # 一级判定：sub-title 头容器存在性（含豁免文案的卡视作 sub-title 头满足）
    # 议题 23（2026-06-05）：narrative-only 判定先剥除 td/th/label + HTML attribute
    # 内字面（业务规则 cell / form label / data-zh 等属性内字面 ≠ narrative-only），
    # 在剩余"卡内真 narrative 散文"上 grep —— 仅 `<p>数据展示说明...</p>` 类顶层
    # 散文段才视作真违规。
    cards_with_c2_container = [c for c in cards if _C2A_TITLE_CONTAINER_RE.search(c)]
    cards_with_c2_narrative_only = [
        c for c in cards
        if _C2A_TITLE_RE.search(_strip_narrative_noise(c))
        and not _C2A_TITLE_CONTAINER_RE.search(c)
    ]
    if not cards_with_c2_container and not cards_with_c2_narrative_only:
        r.ok(f"prd.html {len(cards)} 个 interaction-card 均无「数据展示说明」段（跳过 C-2.A 校验）")
        return

    # 一级失败：sub-title 字面存在但未容器化（PM 写散文 `**数据展示说明**` 等）
    if cards_with_c2_narrative_only:
        r.warn(
            f"[一级判定] prd.html {len(cards_with_c2_narrative_only)} 个 interaction-card 含"
            f"「数据展示说明」字面但未容器化 `<div class=\"data-sub-title\">…</div>` —"
            f" 详 prd_expression_standard.md §四 C-2"
        )

    if not cards_with_c2_container:
        return

    # 二级判定：列完整性
    violations: list[str] = []
    for i, c in enumerate(cards_with_c2_container):
        if "本帧无数据展示" in c:
            continue
        idx = _C2A_TITLE_CONTAINER_RE.search(c).end()
        # sub-title 容器后第一张 thead
        thead_m = re.search(r"<thead>.*?</thead>", c[idx:idx + 2000], re.DOTALL)
        if not thead_m:
            violations.append(f"#{i + 1} 无 thead")
            continue
        thead_text = thead_m.group(0)
        missing = [k for k in _C2A_THEAD_COLS if k not in thead_text]
        if missing:
            violations.append(f"#{i + 1} 缺列[{','.join(missing)}]")

    if violations:
        ex = "; ".join(violations[:5])
        suffix = " ..." if len(violations) > 5 else ""
        r.warn(
            f"[二级判定] prd.html {len(violations)}/{len(cards_with_c2_container)} 个 C-2.A 索引"
            f"表缺列：{ex}{suffix} — 详 prd_expression_standard.md §四 区块 C C-2.A"
        )
    else:
        r.ok(
            f"prd.html {len(cards_with_c2_container)} 个 C-2.A 索引表 6 列齐全（一级+二级 PASS）"
        )


# C-2.B D 字段子表 5 列（thead 字面）
_C2B_THEAD_COLS = ["D 触点 ID", "字段名", "接口字段", "显示格式", "空值处理"]
# 议题 10 容器锁定（2026-06-04，PM 反审 trust-but-verify 实证 8 FP / 77 触发 = 10.4% FP）：
# 旧版 `r'字段说明'` 命中 ①spec-header「数据字段说明」② td/data-zh 属性内字面
# ③ narrative `**字段说明**` 等 FP；新版只锁定真容器 `<div class="data-sub-title"...>...字段说明...</div>`
# （与 assemble._build_c4_content_html / inject_c2b 同源容器，PM 写源也按 prd_expression_standard.md
# §四 C-2.B schema 渲染同容器）。dry-run 实测：bujue-quotation-tool 旧 77 触发 → 新 69 触发
# （-8 FP），违规数 8 → 0（FP 全清，真实通过率 100%）。私域主页 0 触发不变。
_C2B_SUB_TITLE_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>[^<]*字段说明[^<]*</div>',
    re.IGNORECASE,
)
# 议题 17 一级判定：裸字面 narrative `字段说明` 检测（用于"未容器化 sub-title"提示）
_C2B_NARRATIVE_RE = re.compile(r'字段说明')


def check_interaction_c2b_field_table(prd_html: str, r: Report) -> None:
    """SSOT #69 / S4-59 — interaction-card C-2.B 字段子表 5 列含 D 触点 ID（WARN，议题 17 二级判定升级）。

    含「字段说明」子标题（容器锁定：`<div class="data-sub-title">...字段说明...</div>`，
    议题 10 容器锁定 2026-06-04）的 interaction-card，其后 table 应是 C-2.B 字段
    子表，含 5 列：D 触点 ID / 字段名 / 接口字段 / 显示格式 / 空值处理。

    议题 17 二级判定升级（治"sub-title 不存在但表存在 / sub-title 存在但表列缺"漏检）：
    - 一级（sub-title 头容器存在性）：议题 10 容器锁定（避免 narrative 字面 FP）
    - 二级（列完整）：容器命中后表 5 列齐全
    任一级失败 → WARN 分级提示哪一级缺。

    启发式豁免：prd 无 interaction-card 跳过。
    """
    r.section("SSOT #69 / S4-59 interaction-card C-2.B 5 列字段子表（WARN，议题 17 二级判定）")

    cards = list(_iter_interaction_cards(prd_html))
    if not cards:
        r.ok("prd.html 无 .interaction-card → 跳过 C-2.B 校验")
        return

    # 议题 23（2026-06-05，PM 反审治本）：narrative-only 判定先剥除 td/th/label +
    # HTML attribute 内字面再 grep，治 bujue-quotation-tool card #111-#118 8/8 FP
    # （业务规则 cell `<td>**字段说明**：≤200 字符...</td>` / form label / data-zh
    # 属性内字面误判为 narrative-only）。
    cards_with_c2b = [c for c in cards if _C2B_SUB_TITLE_RE.search(c)]
    cards_narrative_only = [
        c for c in cards
        if _C2B_NARRATIVE_RE.search(_strip_narrative_noise(c))
        and not _C2B_SUB_TITLE_RE.search(c)
    ]

    # 一级失败：sub-title 字面存在但未容器化
    if cards_narrative_only:
        r.warn(
            f"[一级判定] prd.html {len(cards_narrative_only)} 个 interaction-card 含"
            f"「字段说明」字面但未容器化 `<div class=\"data-sub-title\">…</div>` —"
            f" 详 prd_expression_standard.md §四 C-2.B"
        )

    if not cards_with_c2b:
        if not cards_narrative_only:
            r.ok(f"prd.html {len(cards)} 个 interaction-card 均无「字段说明」子段（跳过 C-2.B 校验）")
        return

    # 二级判定：列完整性
    violations: list[str] = []
    for i, c in enumerate(cards_with_c2b):
        # 「字段说明」后第一张 thead
        idx = _C2B_SUB_TITLE_RE.search(c).end()
        thead_m = re.search(r"<thead>.*?</thead>", c[idx:idx + 2000], re.DOTALL)
        if not thead_m:
            violations.append(f"#{i + 1} 无 thead")
            continue
        thead_text = thead_m.group(0)
        missing = [k for k in _C2B_THEAD_COLS if k not in thead_text]
        if missing:
            violations.append(f"#{i + 1} 缺列[{','.join(missing)}]")

    if violations:
        ex = "; ".join(violations[:5])
        suffix = " ..." if len(violations) > 5 else ""
        r.warn(
            f"[二级判定] prd.html {len(violations)}/{len(cards_with_c2b)} 个 C-2.B 字段"
            f"子表缺列：{ex}{suffix} — 详 prd_expression_standard.md §四 区块 C C-2.B"
        )
    else:
        r.ok(
            f"prd.html {len(cards_with_c2b)} 个 C-2.B 字段子表 5 列齐全（一级+二级 PASS）"
        )


# C-3 触点表 6 列（thead 字面）
_C3_THEAD_COLS = ["序号", "触点说明", "触发", "行为", "跳转", "边缘"]
# 议题 17 一级判定：容器锁定 sub-title 头（治"narrative 字面命中 FP"）
_C3_TITLE_CONTAINER_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>[^<]*触点交互说明[^<]*</div>',
    re.IGNORECASE,
)
_C3_TITLE_RE = re.compile(r'触点交互说明')


def check_interaction_c3_touchpoint_table(prd_html: str, r: Report) -> None:
    """SSOT #69 / S4-60 — interaction-card C-3 触点表 6 列含行为/边缘（WARN，议题 17 二级判定升级）。

    含「触点交互说明」`<div class="data-sub-title">` 容器锁定 sub-title 头的
    interaction-card，其后 table 应是 C-3 触点表，含 6 列：序号 / 触点说明 / 触发 /
    行为 / 跳转 / 边缘。

    议题 17 二级判定升级：
    - 一级（sub-title 头容器存在性）：容器锁定（避免 narrative 字面 FP）
    - 二级（列完整）：容器命中后表 6 列齐全
    任一级失败 → WARN 分级提示哪一级缺。

    启发式豁免：①prd 无 interaction-card 跳过；②含「本帧无交互触点」豁免（议题 15
    assemble 派生兜底已覆盖）。
    """
    r.section("SSOT #69 / S4-60 interaction-card C-3 触点表 6 列（WARN，议题 17 二级判定）")

    cards = list(_iter_interaction_cards(prd_html))
    if not cards:
        r.ok("prd.html 无 .interaction-card → 跳过 C-3 校验")
        return

    # 议题 23 同型扩展（2026-06-05）：narrative-only 判定先剥除业务结构 cell +
    # HTML attribute 内字面再 grep，避免业务表格 / data-zh 属性内"触点交互说明"
    # 字面误判为 narrative-only。
    cards_with_c3_container = [c for c in cards if _C3_TITLE_CONTAINER_RE.search(c)]
    cards_narrative_only = [
        c for c in cards
        if _C3_TITLE_RE.search(_strip_narrative_noise(c))
        and not _C3_TITLE_CONTAINER_RE.search(c)
    ]

    # 一级失败：sub-title 字面存在但未容器化
    if cards_narrative_only:
        r.warn(
            f"[一级判定] prd.html {len(cards_narrative_only)} 个 interaction-card 含"
            f"「触点交互说明」字面但未容器化 `<div class=\"data-sub-title\">…</div>` —"
            f" 详 prd_expression_standard.md §四 C-3"
        )

    if not cards_with_c3_container:
        if not cards_narrative_only:
            r.ok(f"prd.html {len(cards)} 个 interaction-card 均无「触点交互说明」段（跳过 C-3 校验）")
        return

    # 二级判定：列完整性
    violations: list[str] = []
    for i, c in enumerate(cards_with_c3_container):
        if "本帧无交互触点" in c:
            continue
        idx = _C3_TITLE_CONTAINER_RE.search(c).end()
        thead_m = re.search(r"<thead>.*?</thead>", c[idx:idx + 2000], re.DOTALL)
        if not thead_m:
            violations.append(f"#{i + 1} 无 thead")
            continue
        thead_text = thead_m.group(0)
        missing = [k for k in _C3_THEAD_COLS if k not in thead_text]
        if missing:
            violations.append(f"#{i + 1} 缺列[{','.join(missing)}]")

    if violations:
        ex = "; ".join(violations[:5])
        suffix = " ..." if len(violations) > 5 else ""
        r.warn(
            f"[二级判定] prd.html {len(violations)}/{len(cards_with_c3_container)} 个 C-3 触点表"
            f"缺列：{ex}{suffix} — 详 prd_expression_standard.md §四 区块 C C-3"
        )
    else:
        r.ok(
            f"prd.html {len(cards_with_c3_container)} 个 C-3 触点表 6 列齐全（一级+二级 PASS）"
        )


# ── S4-61 ┤ interaction-card 同名子区块重复检测（议题 2B，SSOT #69 延伸，WARN）──
# PM 手写 `<p><strong>业务规则</strong>...</p>` + C-4 派生 `<div class="c4-sub-title">业务规则</div>`
# 双段并存（私域主页 49/143 实证）。同名子标题段在同一 interaction-card 内出现 ≥ 2 次 → WARN。
# 检测对象：业务规则 / 数据回显 / 验收标准 三类（C-4.A/.B/.C 同源名）。
# 详 prd_expression_standard.md §四 区块 C C-4 schema + SSOT #69
_DOUBLE_SUBSECTION_KEYS = ("业务规则", "数据回显", "验收标准")


def check_interaction_card_double_subsection(prd_html: str, r: Report) -> None:
    """S4-61 v1（议题 2B）— interaction-card 同名子区块重复检测（WARN）。

    规则：每个 .interaction-card 内同名子标题字面（业务规则 / 数据回显 / 验收标准）
    出现 ≥ 2 次 → WARN（治"PM 手写 `<p><strong>业务规则</strong></p>` 与 C-4 派生
    `<div class="c4-sub-title">业务规则</div>` 双段并存"反 pattern，私域主页 49 处实证）。

    豁免：①prd 无 .interaction-card 跳过；②同名字面在 c4-business-rules / c4-data-scale
    / pre.gherkin 子元素文本内（如业务规则列表条目里"按业务规则"等内容性重复，非子标题）不计。

    设计：扫每个 interaction-card 内 3 个同名 key，分别匹配
    ①PM 手写形态 `<p><strong>KEY</strong>` ②C-4 派生 `<div class="c4-sub-title">KEY</div>`
    （也覆盖 `<div class="data-sub-title">业务契约</div>` 异名同源情况）；任一 key
    在同一卡片内总计 ≥ 2 次 → WARN（不区分手写 vs 派生形态，捕获所有重复源）。

    rollout：WARN 阶段，3 仓 dry-run + FP < 30% 后升 FAIL。
    详 rule_hard_constraints.md §S4-61 + prd_expression_standard.md §四 C-4 + SSOT #69。
    """
    r.section(
        "S4-61 v1 interaction-card 同名子区块重复检测（议题 2B，WARN 阶段）"
    )

    cards = list(_iter_interaction_cards(prd_html))
    if not cards:
        r.ok("prd.html 无 .interaction-card → 跳过 S4-61 校验")
        return

    # 子标题字面三类形态（PM 手写 + C-4 派生，互不重叠）
    # 形态 A：PM 手写段头 `<p><strong>KEY</strong>` / `<p><b>KEY</b>`
    # 形态 B：C-4 派生 `<div class="c4-sub-title">KEY</div>` / `<div class="data-sub-title">KEY</div>`
    # 形态 C：`<h4>KEY</h4>` / `<h5>KEY</h5>` 等子标题（兼容更宽松的 schema 实践）
    # 注：不单独匹配裸 `<strong>KEY</strong>`（会与形态 A 重叠双计；且裸 strong 也可能
    #     出现在列表项 / 段落内容中作内容性强调，非子标题）。
    def _build_patterns(key: str) -> list[re.Pattern]:
        kesc = re.escape(key)
        return [
            re.compile(rf'<p[^>]*>\s*<(?:strong|b)>\s*{kesc}\s*</(?:strong|b)>'),
            re.compile(rf'<div\s+class\s*=\s*"[^"]*\b(?:c4-sub-title|data-sub-title)\b[^"]*"\s*>\s*{kesc}\s*</div>'),
            re.compile(rf'<h[1-6][^>]*>\s*{kesc}\s*</h[1-6]>'),
        ]

    key_patterns = {k: _build_patterns(k) for k in _DOUBLE_SUBSECTION_KEYS}

    violations: list[str] = []
    total_double_cards = 0
    per_key_count: dict[str, int] = {k: 0 for k in _DOUBLE_SUBSECTION_KEYS}

    for i, card in enumerate(cards):
        card_doubles: list[str] = []
        for key, patterns in key_patterns.items():
            count = 0
            for p in patterns:
                count += len(p.findall(card))
            if count >= 2:
                card_doubles.append(f"{key}×{count}")
                per_key_count[key] += 1
        if card_doubles:
            total_double_cards += 1
            if len(violations) < 5:
                # 取卡片首 80 字符做定位 hint
                title_m = re.search(
                    r'<div\s+class\s*=\s*"card-title"\s*>([^<]+)</div>',
                    card[:300],
                )
                title = (title_m.group(1).strip()[:60] + "…") if title_m else "(无 title)"
                violations.append(
                    f"#{i + 1} {title} — 重复段：[{', '.join(card_doubles)}]"
                )

    if total_double_cards == 0:
        r.ok(
            f"prd.html {len(cards)} 个 .interaction-card 无同名子区块重复"
            f"（S4-61 PASS）"
        )
        return

    summary = ", ".join(
        f"{k}×{per_key_count[k]} 卡"
        for k in _DOUBLE_SUBSECTION_KEYS
        if per_key_count[k]
    )
    r.warn(
        f"[S4-61] prd.html {total_double_cards}/{len(cards)} 个 .interaction-card "
        f"存在同名子区块重复（PM 手写 + C-4 派生双段并存）；按 key 统计：{summary}；"
        f"前 5 示例：{' | '.join(violations)}；治本：删 PM 手写形态（`<p><strong>业务规则</strong>` "
        f"等），让 C-4 派生层（`c4-sub-title` 子区块）作唯一来源。"
        f"详 prd_expression_standard.md §四 C-4 + SSOT #69。"
        f"（WARN 阶段，3 仓 dry-run + FP < 30% 后升 FAIL）"
    )


# ── S4-62 ┤ tp-marker 反向配对：marker → data-tp（议题 3，SSOT #65 延伸，WARN）──
# S4-36 正向校验（每个 data-tp 必有 tp-marker）；S4-62 反向校验（每个 tp-marker
# 必有 data-tp 邻近配对）—— 治"PM 删 data-tp 后忘删悬空 marker"（bujue-quotation-tool
# L5733 实证：`<span class="tp-marker">01</span>` 悬空 in H-M01-P01-default）。
# 详 rule_hard_constraints.md §S4-62 + SSOT #65 触点 marker 配对纪律
def check_tp_marker_reverse_pairing(prd_html: str, r: Report) -> None:
    """S4-62 v1（议题 3）— tp-marker 反向配对检测：marker → data-tp（WARN）。

    规则：每个 `<span class="tp-marker">NN</span>` 必有同级或邻近 ≤ 500 字符内
    的 `data-tp="M[XX]-P[YY]-[TDC]NN"` 元素（NN 数字段一致）配对；否则视为悬空 marker
    （PM 删 data-tp 后忘删 marker / 重复粘贴未清理）。

    与 S4-36 的对偶：
    - S4-36（正向）：data-tp → tp-marker（缺 marker 渲染时无序号气泡）
    - S4-62（反向）：tp-marker → data-tp（marker 悬空显示无对应触点）

    豁免：①prd 无 .tp-marker 跳过；②父链路含 showcase-only / is-unchecked / nav-inactive
    豁免 class（同 S4-36 豁免列表）；③父链路含 `data-tp-no-wrap` 属性视为展示性 marker。

    rollout：WARN 阶段，3 仓 dry-run + FP < 30% 后升 FAIL。
    详 rule_hard_constraints.md §S4-62 + SSOT #65。
    """
    r.section(
        "S4-62 v1 tp-marker 反向配对（议题 3，零启发式，WARN 阶段）"
    )

    EXEMPT_PATTERNS = ("showcase-only", "is-unchecked", "nav-inactive")
    SCAN_RADIUS = 500  # 同 S4-36

    marker_pattern = re.compile(
        r'<span\s+class\s*=\s*"[^"]*\btp-marker\b[^"]*"[^>]*>\s*(\d+)\s*</span>',
        re.IGNORECASE,
    )
    data_tp_pattern = re.compile(
        r'\bdata-tp\s*=\s*"M\d+-P\d+-[TDC](\d+)"', re.IGNORECASE
    )

    marker_count = 0
    violations: list[tuple[int, str]] = []

    for m in marker_pattern.finditer(prd_html):
        marker_count += 1
        marker_num = m.group(1)
        # 豁免父链路扫（向前 200 字符内含豁免 pattern）
        ctx_before = prd_html[max(0, m.start() - 200):m.start()]
        if any(p in ctx_before for p in EXEMPT_PATTERNS):
            continue
        # 反向查找：±SCAN_RADIUS 字符内找 data-tp 末段数字 == marker_num
        search_start = max(0, m.start() - SCAN_RADIUS)
        search_end = min(len(prd_html), m.end() + SCAN_RADIUS)
        search_window = prd_html[search_start:search_end]
        found = False
        for dm in data_tp_pattern.finditer(search_window):
            if dm.group(1) == marker_num:
                found = True
                break
        if not found:
            lineno = prd_html[:m.start()].count("\n") + 1
            violations.append((lineno, marker_num))

    if marker_count == 0:
        r.ok("prd.html 无 .tp-marker → 跳过 S4-62 校验")
        return
    if not violations:
        r.ok(f"tp-marker × {marker_count} 均有邻近配对 data-tp（S4-62 PASS）")
        return

    for lineno, num in violations[:10]:
        r.warn(
            f"[S4-62] L{lineno} `<span class=\"tp-marker\">{num}</span>` 悬空"
            f" — 在 ±{SCAN_RADIUS} 字符内未找邻近 data-tp 末段数字={num} 的配对元素；"
            f"治本：①删除该悬空 marker（PM 重复粘贴 / 删 data-tp 时遗留）"
            f" ②或补回原 data-tp 元素恢复配对。"
            f"详 rule_hard_constraints.md §S4-62 + SSOT #65（WARN 阶段，3 仓 dry-run + FP<30% 后升 FAIL）"
        )
    if len(violations) > 10:
        r.warn(f"[S4-62] 共 {len(violations)} 处悬空 marker，仅显示前 10 条")


# ── S4-63 ┤ interaction-card C-4 表达形式校验（议题 2A，SSOT #69 延伸，WARN）──
# C-4.A 业务规则 → 必为 <table class="c4-business-rules">（议题 2A：从 <ul> 改表格表达）
# C-4.B 数据规模 → 必为 <table class="c4-data-scale">（议题 2A：从 <p> 单段改表格表达）
# C-4.C 验收标准 → 必为 <pre class="gherkin">（Gherkin 三段语义代码格式，保留 pre）
# 详 rule_hard_constraints.md §S4-63 + prd_expression_standard.md §四 C-4 + SSOT #69
_C4_BUSINESS_RULES_TABLE_RE = re.compile(r'<table\s+class\s*=\s*"[^"]*\bc4-business-rules\b')
_C4_DATA_SCALE_TABLE_RE = re.compile(r'<table\s+class\s*=\s*"[^"]*\bc4-data-scale\b')
_C4_GHERKIN_PRE_RE = re.compile(r'<pre\s+class\s*=\s*"[^"]*\bgherkin\b')
_C4_BLOCK_MARKER_RE = re.compile(r'\[C4-START:')


def check_interaction_card_c4_format(prd_html: str, r: Report) -> None:
    """S4-63 v1（议题 2A）— interaction-card C-4 表达形式校验（WARN）。

    规则：每个含 C-4 派生注入（`<!-- [C4-START: ...] -->` 标记）的 .interaction-card 必须
    满足三子区块表达形式：
    - C-4.A 业务规则 → `<table class="c4-business-rules">`（表格表达）
    - C-4.B 数据规模 → `<table class="c4-data-scale">`（表格表达）
    - C-4.C 验收标准 → `<pre class="gherkin">`（Gherkin 三段语义代码）

    议题 2A 治"PM 手写 / 历史 assemble 派生用 <ul> / <p> 表达 C-4.A/.B"反 pattern；
    Gherkin 保留 <pre>（代码语义）。

    豁免：
    - prd 无 .interaction-card → 跳过
    - .interaction-card 无 C-4 派生（不含 [C4-START: 标记）→ 跳过（非主页面副页面跳转形态合规）

    rollout：WARN 阶段，3 仓 dry-run + FP < 30% 后升 FAIL（同 S4-49~62 同型纪律）。
    详 rule_hard_constraints.md §S4-63 + prd_expression_standard.md §四 C-4 + SSOT #69。
    """
    r.section("S4-63 v1 interaction-card C-4 表达形式校验（议题 2A，WARN 阶段）")

    cards = list(_iter_interaction_cards(prd_html))
    if not cards:
        r.ok("prd.html 无 .interaction-card → 跳过 S4-63 校验")
        return

    cards_with_c4 = [c for c in cards if _C4_BLOCK_MARKER_RE.search(c)]
    if not cards_with_c4:
        r.ok(
            f"prd.html {len(cards)} 个 .interaction-card 均无 C-4 派生注入"
            "（无主页面 C-4 或全副页面跳转形态）→ 跳过 S4-63 校验"
        )
        return

    violations: list[str] = []
    per_key_count = {"C-4.A 业务规则": 0, "C-4.B 数据规模": 0, "C-4.C 验收标准": 0}

    for i, c in enumerate(cards_with_c4):
        missing: list[str] = []
        if not _C4_BUSINESS_RULES_TABLE_RE.search(c):
            missing.append("C-4.A 业务规则需 <table class='c4-business-rules'>")
            per_key_count["C-4.A 业务规则"] += 1
        if not _C4_DATA_SCALE_TABLE_RE.search(c):
            missing.append("C-4.B 数据规模需 <table class='c4-data-scale'>")
            per_key_count["C-4.B 数据规模"] += 1
        if not _C4_GHERKIN_PRE_RE.search(c):
            missing.append("C-4.C 验收标准需 <pre class='gherkin'>")
            per_key_count["C-4.C 验收标准"] += 1
        if missing:
            title_m = re.search(
                r'<div\s+class\s*=\s*"card-title"\s*>([^<]+)</div>', c[:300]
            )
            title = (title_m.group(1).strip()[:60] + "…") if title_m else f"(card #{i + 1})"
            if len(violations) < 5:
                violations.append(f"`{title}` 缺[{'; '.join(missing)}]")

    if not violations:
        r.ok(
            f"prd.html {len(cards_with_c4)} 个含 C-4 派生的 interaction-card "
            f"C-4.A/.B 表格 + C-4.C Gherkin pre 全合规（S4-63 PASS）"
        )
        return

    summary = ", ".join(
        f"{k}×{v} 卡" for k, v in per_key_count.items() if v
    )
    total_violation_cards = max(per_key_count.values()) if per_key_count else 0
    r.warn(
        f"[S4-63] prd.html {total_violation_cards}/{len(cards_with_c4)} 个含 C-4 派生 "
        f"interaction-card 表达形式不合规；按 key 统计：{summary}；"
        f"前 5 示例：{' | '.join(violations)}；"
        f"治本：重跑 `assemble.py prd --force-overwrite` 让 C-4.A/.B 派生为 <table>，"
        f"C-4.C 保持 <pre class='gherkin'>（议题 2A 表达规范化）。"
        f"详 rule_hard_constraints.md §S4-63 + prd_expression_standard.md §四 C-4 + SSOT #69。"
        f"（WARN 阶段，3 仓 dry-run + FP < 30% 后升 FAIL）"
    )


# ── S4-64 ┤ interaction-card sub-title 顺序 + 完整性校验（议题 16，SSOT #69 延伸，WARN）──
# 议题 16 / NB-R3-02：interaction-card 5 子区块（C-0/C-1/C-2/C-3/C-4）须按规范固定顺序
# 出现 + 缺失 sub-title 头 → WARN。assemble 派生层（议题 15 / NB-R3-01）已注入 C-1/C-2/C-3
# 占位作为防御兜底；本 S4-64 校验"派生兜底是否生效 + sub-title 顺序是否合规"。
# 详 rule_hard_constraints.md §S4-64 + prd_expression_standard.md §四 区块 C + SSOT #69
_SUBTITLE_ORDER = [
    ("C-1", "列表回显说明"),
    ("C-2", "数据展示说明"),
    ("C-3", "触点交互说明"),
    ("C-4", "业务契约"),
]
_DATA_SUB_TITLE_GENERIC_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>([^<]+)</div>',
    re.IGNORECASE,
)


def check_interaction_card_subtitle_order(prd_html: str, r: Report) -> None:
    """S4-64 v1（议题 16 / NB-R3-02）— interaction-card sub-title 顺序 + 完整性校验（WARN）。

    规则：每个 .interaction-card 内 4 个标准 sub-title 头（C-1 列表回显说明 / C-2 数据展示
    说明 / C-3 触点交互说明 / C-4 业务契约）须按规范固定顺序出现；缺失任一 sub-title 头
    → WARN（含「真无内容」豁免：sub-title 头存在 + 紧跟「本帧无 XXX」豁免文案合规）。

    议题 16 / NB-R3-02 治理路径：
    - assemble 派生层（议题 15）：缺 C-1/C-2/C-3 → 自动注入豁免占位
    - 规范教育层（prd_expression_standard.md §四 必填 + 豁免明示）
    - precheck 校验层（S4-64）：检测 assemble 派生 + PM 写源后顺序 / 完整性

    豁免：
    - prd 无 .interaction-card → 跳过
    - sub-title 头存在 + 紧跟「本帧无 XXX」豁免文案 → 合规（不计违规）

    rollout：WARN 阶段，3 仓 dry-run + FP < 30% 后升 FAIL（同 S4-49~63 同型纪律）。
    详 rule_hard_constraints.md §S4-64 + prd_expression_standard.md §四 区块 C + SSOT #69。
    """
    r.section("S4-64 v1 interaction-card sub-title 顺序 + 完整性校验（议题 16，WARN 阶段）")

    cards = list(_iter_interaction_cards(prd_html))
    if not cards:
        r.ok("prd.html 无 .interaction-card → 跳过 S4-64 校验")
        return

    missing_violations: list[str] = []
    order_violations: list[str] = []
    per_key_missing = {label: 0 for _, label in _SUBTITLE_ORDER}

    for i, c in enumerate(cards):
        title_m = re.search(
            r'<div\s+class\s*=\s*"card-title"\s*>([^<]+)</div>', c[:300]
        )
        title = (title_m.group(1).strip()[:50] + "…") if title_m else f"(card #{i + 1})"

        # 提取本 card 内所有 data-sub-title 字面 + 出现位置
        positions: dict[str, int] = {}
        for sm in _DATA_SUB_TITLE_GENERIC_RE.finditer(c):
            sub_text = sm.group(1).strip()
            for code, label in _SUBTITLE_ORDER:
                if label in sub_text and code not in positions:
                    positions[code] = sm.start()
                    break

        # 完整性：缺哪个 sub-title 头
        for code, label in _SUBTITLE_ORDER:
            if code not in positions:
                per_key_missing[label] += 1
                if len(missing_violations) < 5:
                    missing_violations.append(f"`{title}` 缺 {code}「{label}」")

        # 顺序：positions 中已出现的子集必须按规范顺序排列
        present_codes = [code for code, _ in _SUBTITLE_ORDER if code in positions]
        sorted_by_pos = sorted(present_codes, key=lambda x: positions[x])
        if present_codes != sorted_by_pos:
            actual = " < ".join(sorted_by_pos)
            expected = " < ".join(present_codes)
            if len(order_violations) < 5:
                order_violations.append(
                    f"`{title}` 顺序乱：实际 [{actual}] vs 规范 [{expected}]"
                )

    if not missing_violations and not order_violations:
        r.ok(
            f"prd.html {len(cards)} 个 .interaction-card sub-title 4 子区块（C-1/C-2/C-3/C-4）"
            f"齐全 + 顺序合规（S4-64 PASS）"
        )
        return

    if missing_violations:
        summary = ", ".join(
            f"{label}×{v} 卡" for label, v in per_key_missing.items() if v
        )
        r.warn(
            f"[S4-64 完整性] prd.html {len(cards)} 个 .interaction-card 中缺 sub-title 头："
            f"{summary}；前 5 示例：{' | '.join(missing_violations)}；"
            f"治本：重跑 `assemble.py prd --force-overwrite` 让议题 15 派生层兜底注入豁免占位。"
        )
    if order_violations:
        r.warn(
            f"[S4-64 顺序] prd.html {len(order_violations)} 个 .interaction-card 子区块顺序违反"
            f"规范（C-1 < C-2 < C-3 < C-4）；前 5 示例：{' | '.join(order_violations)}；"
            f"详 prd_expression_standard.md §四 区块 C。"
            f"（WARN 阶段，3 仓 dry-run + FP < 30% 后升 FAIL）"
        )


def main() -> None:
    hook_warn = _check_pre_commit_hook_installed()
    if hook_warn:
        print(f"[WARN] {hook_warn}\n", file=sys.stderr)

    scaffold_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SCAFFOLD

    if not scaffold_path.exists():
        print(f"[ERROR] scaffold.json 不存在：{scaffold_path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(scaffold_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[ERROR] scaffold.json 解析失败：{e}", file=sys.stderr)
        sys.exit(1)

    product = data.get("product", "").strip()
    if not product:
        print("[ERROR] scaffold.json 未指定 product 字段", file=sys.stderr)
        sys.exit(1)

    prd_path = OUTPUT_DIR / f"prd_{product}_latest.html"
    spec_path = OUTPUT_DIR / f"spec_{product}_latest.md"

    print(f"产品：{product}")
    print(f"PRD ：{prd_path}")
    print(f"SPEC：{spec_path}")

    r = Report()
    check_scaffold(data, r)
    check_scaffold_roles_format(data, r)
    check_state_naming_convention(data, r)
    check_state_coverage(data, r)
    # SSOT #74 v1 — 页面集守恒 page_source 溯源兜底（R1 阶段 2 页面集 SSOT，[Should] WARN）
    check_page_source_provenance(data, r)
    # SSOT #75 v1 — 阶段 4 蓝图质量三校验（R5 archetype 语义 / R6 §11 异常覆盖 / R7 depends_on 环，[Should] WARN）
    check_archetype_semantics(data, r)
    check_exception_coverage(data, r)
    check_depends_on_cycle(data, r)

    if not prd_path.exists():
        r.section("prd.html 结构与一致性")
        r.fail(f"prd.html 不存在：{prd_path}（请先执行 assemble.py prd）")
    else:
        check_prd(data, prd_path.read_text(encoding="utf-8"), r)

    if not spec_path.exists():
        r.section("spec.md 结构与一致性")
        r.fail(f"spec.md 不存在：{spec_path}（请先执行 assemble.py spec）")
    else:
        spec_text = spec_path.read_text(encoding="utf-8")
        check_spec(data, spec_text, r)
        check_business_flow_in_spec(data, spec_text, r)
        check_spec_state_table_count(data, spec_text, r)
        # SSOT #66 spec.md SSOT 输入 schema 严格化（WARN 阶段，5 维度）
        check_spec_module_subsections_completeness(data, spec_text, r)
        check_spec_gherkin_completeness(data, spec_text, r)
        check_spec_api_id_closure(data, spec_text, r)
        check_spec_nb_id_closure(data, spec_text, r)
        check_spec_section_numbering_consistency(data, spec_text, r)
        # SSOT #68 spec 派生层（4 函数，WARN 阶段）
        check_spec_section_4B_business_rules(data, spec_text, r)
        check_spec_section_5B_data_scale(data, spec_text, r)
        check_spec_function_main_page_field(data, spec_text, r)
        check_spec_function_xxx_required(data, spec_text, r)

    # 业务流程图 PRD 侧 SSOT 同步（A-04.2）
    if prd_path.exists():
        prd_html_for_business_flow = prd_path.read_text(encoding="utf-8")
        check_business_flow_in_prd(data, prd_html_for_business_flow, r)
        # S4-66：§A-04.2 业务流程图双视图三件套（议题 25，SSOT #30 派生方完整化）
        check_spec_business_flow_double_view(prd_html_for_business_flow, r)

    # 触点 ID 集合一致性（仅当 spec.md 与 prd.html 都存在时）
    if spec_path.exists() and prd_path.exists():
        check_touchpoint_consistency(
            spec_path.read_text(encoding="utf-8"),
            prd_path.read_text(encoding="utf-8"),
            r,
        )

    # S4-33 mermaid 语法校验（mmdc parse，WARN 阶段；SSOT #43）
    if spec_path.exists() and prd_path.exists():
        check_mermaid_syntax(
            spec_path.read_text(encoding="utf-8"),
            prd_path.read_text(encoding="utf-8"),
            r,
        )

    # S4-34 触点 canonical 引用完整性（WARN 阶段；SSOT #44）
    if spec_path.exists() and prd_path.exists():
        check_touchpoint_canonical(
            data,
            spec_path.read_text(encoding="utf-8"),
            prd_path.read_text(encoding="utf-8"),
            r,
        )

    # S4-29 页面层级架构 SSOT 同步（§3.0 / PRD spec-sitemap ↔ scaffold，SSOT #38）
    if spec_path.exists() and prd_path.exists():
        check_page_hierarchy_sitemap(
            data,
            spec_path.read_text(encoding="utf-8"),
            prd_path.read_text(encoding="utf-8"),
            r,
        )

    # S4-30 页面结构范式契约 结构兜底（提议2，SSOT #39）
    if spec_path.exists() and prd_path.exists():
        check_page_archetype_contract(
            data,
            spec_path.read_text(encoding="utf-8"),
            prd_path.read_text(encoding="utf-8"),
            r,
        )
    # S4-30 过程层：容纳性校验记录齐全+覆盖（无模块子进度文件 → WARN 跳过）
    check_archetype_containment_record(data, r)

    # S4-31 模块架构说明 结构兜底（提议3，SSOT #40）
    if spec_path.exists() and prd_path.exists():
        check_module_architecture(
            data,
            spec_path.read_text(encoding="utf-8"),
            prd_path.read_text(encoding="utf-8"),
            r,
        )

    # S4-32 页面骨架屏 结构兜底（SSOT #41；spec.md per-page ```skeleton + PRD 画廊）
    if spec_path.exists() and prd_path.exists():
        check_page_skeleton(
            data,
            spec_path.read_text(encoding="utf-8"),
            prd_path.read_text(encoding="utf-8"),
            r,
        )

    # issue #3/#4 嵌套约束（frame-card / interaction-card / section-header）
    if prd_path.exists():
        check_section_nesting(prd_path.read_text(encoding="utf-8"), r)

    # frame-wrapper 端口标签规则（多端并列必出现）— 来源 issue 2026-05-06_2319
    if prd_path.exists():
        check_frame_platform_tag(prd_path.read_text(encoding="utf-8"), r)

    # 页面级端口覆盖漂移防御（SNB-005 修复补 S4-04 模块级精度，WARN-phase）
    if prd_path.exists():
        check_page_platform_coverage(prd_path.read_text(encoding="utf-8"), r)

    # proj 组件协议检查（仅当 prd.html 存在时执行；不存在已在前面报错）
    if prd_path.exists():
        check_proj_components(data, prd_path.read_text(encoding="utf-8"), r)

    # 组件索引一致性（pub 索引始终核查，proj 索引按需）
    check_pub_index(r)
    check_proj_index(data, r)

    # S4-27 派生模块引用 owner proj 组件内部 slot class 完整性（NB-WE-32 实装,SSOT #37 兜底）
    check_proj_slot_class_completeness(data, r)

    # S4-23 PRD fb-* class 登记核查（仅当 prd.html 存在时执行）
    if prd_path.exists():
        check_prd_fb_registration(data, prd_path.read_text(encoding="utf-8"), r)

    # S4-23 扩展 — prd_template.html 真源 fb-* 登记核查（无条件,扫元规范层）
    # 历史 fb-table 漂移在 §11.4 真源沉淀但 S4-23 仅扫 outputs 派生未抓到（NB-WE-08）
    check_prd_template_fb_registration(r)

    # NB-WE-06 视觉一致性机械化（z-index 集合校验,SSOT §零.1）— 仅当 prd.html 存在
    # NB-WE-20 §零.2 rule-3 实装（frame-card isolation）— 同样仅当 prd.html 存在
    # rule-5 实装（phone/miniprogram-frame 内 sheet 规避扫描）
    # S4-26 组件变更清单 thead 字面规范化
    if prd_path.exists():
        prd_html_text = prd_path.read_text(encoding="utf-8")
        check_z_index_compliance(prd_html_text, r)
        check_frame_card_isolation(prd_html_text, r)
        check_panel_class_evasion(prd_html_text, r)
        check_changelog_thead(prd_html_text, r)
        # S4-28 v2 档 C — .fb-frame-bottom-bar 结构完整性(零启发式,WARN 阶段)
        check_desktop_sticky_completeness(prd_html_text, r)
        # S4-28 v2 档 C 第 3 条补充 — inline position:fixed/sticky 字面扫描(零启发式,WARN)
        check_inline_position_compliance(prd_html_text, r)
        check_back_entry(prd_html_text, r)
        # S4-36 v1 — data-tp ↔ tp-marker 配对完整性（A 方案 A.1，WARN 阶段）
        check_tp_marker_pairing(prd_html_text, r)
        # S4-37 v1 — tp-marker tp-wrap 包裹结构（A 方案 A.2，WARN 阶段）
        check_tp_marker_wrap(prd_html_text, r)
        # S4-38 v1 — PRD section 最小内容粒度（A 方案 A.3，[Should] WARN）
        check_section_min_content(prd_html_text, r)
        # S4-39 v1 — Mermaid label 字符安全（A 方案 A.4，[Should] WARN）
        check_mermaid_label_chars(spec_path.read_text(encoding="utf-8") if spec_path.exists() else "", prd_html_text, r)
        # SSOT #70 v1 — 业务流程图选型规范配套机械兜底（[Should] WARN，dry-run 阶段）
        check_business_flow_diagrams(spec_path.read_text(encoding="utf-8") if spec_path.exists() else "", prd_html_text, r)
        # SSOT #71 v1 — outputs/prd 真 DOM div 平衡兜底（议题 10 NB-WE-PROTO-NAV-OVERWRITE，[Should] WARN）
        check_html_div_balance(prd_html_text, r)
        # SSOT #72 v1 — scaffold ↔ outputs/prd FRAME 一致性兜底（议题 12 NB-WE-12，[Should] WARN）
        check_scaffold_outputs_frame_consistency(data, prd_html_text, r)
        # SSOT #73 v1 — outputs/prd assemble 输出确定性兜底（议题 13 NB-WE-ASSEMBLE-DETERMINISM，[Should] WARN）
        check_outputs_prd_no_assemble_timestamp(prd_html_text, r)
        # SSOT #79 v1 / S4-68 — spec/prd 正文禁内联变更标记（议题 24，[Should] WARN，下游可读性）
        check_no_inline_change_markers(
            spec_path.read_text(encoding="utf-8") if spec_path.exists() else "",
            prd_html_text, r)
        # S4-40 v1 — .interaction-card 内禁 inline 字号覆盖（SSOT #62 E.3 第 1 条，WARN）
        check_interaction_card_no_inline_font(prd_html_text, r)
        # S4-41 v1 — 典型交互说明字面必须在 .interaction-card 内（SSOT #62 E.3 第 2 条，WARN）
        check_interaction_card_class_compliance(prd_html_text, r)
        # S4-42 v1 — .fb-state-loading 内禁 inline padding 覆盖（SSOT #63 Skeleton tokens，WARN）
        check_skeleton_inline_padding(prd_html_text, r)
        # S4-43 v1 — data-tp 容器级唯一性（SSOT #64 触点容器级唯一性纪律，WARN dry-run）
        check_prd_data_tp_container_uniqueness(prd_html_text, r)
        # SSOT #67 / #69 prd 派生层 + interaction-card C-0~C-3 schema（WARN 阶段，6 维度）
        check_prd_a05_removed(data, prd_html_text, r)
        check_interaction_c0_state_diff_note(prd_html_text, r)
        check_interaction_c1_list_table(prd_html_text, r)
        check_interaction_c2a_unit_index(prd_html_text, r)
        check_interaction_c2b_field_table(prd_html_text, r)
        check_interaction_c3_touchpoint_table(prd_html_text, r)
        # S4-61 v1 — interaction-card 同名子区块重复检测（议题 2B，SSOT #69 延伸，WARN）
        check_interaction_card_double_subsection(prd_html_text, r)
        # S4-62 v1 — tp-marker 反向配对（议题 3，SSOT #65 延伸，WARN）
        check_tp_marker_reverse_pairing(prd_html_text, r)
        # S4-63 v1 — interaction-card C-4 表达形式校验（议题 2A，SSOT #69 延伸，WARN）
        check_interaction_card_c4_format(prd_html_text, r)
        # S4-64 v1 — interaction-card sub-title 顺序 + 完整性校验（议题 16 / NB-R3-02，SSOT #69 延伸，WARN）
        check_interaction_card_subtitle_order(prd_html_text, r)

    # SSOT #67 / #68 spec+prd 联合派生闭环（A-索引行数对齐 + C-4 派生闭环）
    if spec_path.exists() and prd_path.exists():
        spec_text_for_derive = spec_path.read_text(encoding="utf-8")
        prd_text_for_derive = prd_path.read_text(encoding="utf-8")
        check_prd_a_index_complete(data, prd_text_for_derive, spec_text_for_derive, r)
        check_prd_c4_derivation_closure(data, prd_text_for_derive, spec_text_for_derive, r)
        # SSOT #77 / S4-67 — R8 渲染契约标记完整性（验 data-tp/data-field 标记，WARN）
        check_render_contract(data, prd_text_for_derive, spec_text_for_derive, r)

    # NB-WE-10 视觉一致性机械化剩余 2 维度
    # 维度 A — 同 page 跨 frame 元数据字面一致（prd.html）
    if prd_path.exists():
        check_frame_page_metadata_consistency(prd_path.read_text(encoding="utf-8"), r)
    # 维度 B — 同字段跨页格式 normalize（spec.md）
    if spec_path.exists():
        check_field_format_consistency_across_pages(
            spec_path.read_text(encoding="utf-8"), r
        )

    # S4-22 组件变更清单一致性（仅当 spec.md + prd.html 都存在时执行）
    if spec_path.exists() and prd_path.exists():
        r.section("S4-22 组件变更清单一致性")
        check_component_changelog_consistency(data, r)

    # 侧栏「组件变更」分组完整性（issue 2026-05-07_1613）
    if prd_path.exists():
        check_sidebar_component_changelog(prd_path.read_text(encoding="utf-8"), r)

    # S4-04 平台覆盖（scaffold.platforms ↔ prd frame 双向对照）
    if prd_path.exists():
        check_platform_coverage(data, prd_path.read_text(encoding="utf-8"), r)

    # S4-08 cursor:pointer 全覆盖（onclick 元素必须有 cursor:pointer）
    if prd_path.exists():
        check_cursor_pointer_coverage(prd_path.read_text(encoding="utf-8"), r)

    # S4-21 spec ↔ prd 字段绑定一致性
    if spec_path.exists() and prd_path.exists():
        check_field_binding_consistency(
            spec_path.read_text(encoding="utf-8"),
            prd_path.read_text(encoding="utf-8"),
            r,
        )

    # S4-24 交互元素 data-tp 绑定（与 spec 触点表一致 + tp-marker 一致性）
    if spec_path.exists() and prd_path.exists():
        check_interactive_data_tp(
            spec_path.read_text(encoding="utf-8"),
            prd_path.read_text(encoding="utf-8"),
            r,
        )

    # fb-fallback.css ↔ fb-fallback-manifest.md sync（每次 precheck 都跑,与产物无关）
    check_fb_fallback_sync(r)

    # NB-阶段4-D B+ 档位 i18n 最小化校验
    # 触发: 产品定义含多语言关键字; 兜底: prd.html data-zh 数 = 0 → BLOCK
    pdef_path = OUTPUT_DIR / f"产品定义_{product}_latest.md"
    if prd_path.exists() and pdef_path.exists():
        check_i18n_minimum(
            prd_path.read_text(encoding="utf-8"),
            pdef_path.read_text(encoding="utf-8"),
            r,
        )

    # G-01 / G-02 4 阶段通用硬规则(rule_hard_constraints.md)
    # G-01:阶段 4 归档为子目录 `process_record/versions/deliverable_v*_*/`(含 prd.html + spec.md)
    # G-02:校验 spec.md 末尾变更记录表 + prd.html doc-changelog section(NB-WE-21 完整摘账,2026-06-01)
    # 用 spec_path 作 G-01 校验入口(prd_path 同步存在);archive_prefix="deliverable" 触发子目录扫描
    if spec_path.exists():
        check_archive_sync(spec_path, r, "阶段4 交付文档", "deliverable", REPO_ROOT)
        check_version_changelog(
            spec_path.read_text(encoding="utf-8"), r, "阶段4 spec.md"
        )
    if prd_path.exists():
        check_prd_doc_changelog_columns(prd_path, r)
    if spec_path.exists() and prd_path.exists():
        check_spec_prd_v01_row_parity(spec_path, prd_path, r)
    # SSOT #48 scaffold.json changelog 合规校验（2026-06-02 治本）
    check_scaffold_changelog_ssot48_compliance(scaffold_path, r)
    # S4-65 v1 — scaffold.json version ↔ changelog 末行 version 一致性（议题 20，WARN 阶段）
    check_scaffold_version_changelog_consistency(scaffold_path, r)

    # S4-NAMING-01 角色命名一致性(建议 7 / issue # 3 复盘根因 G)— 同时校验 prd.html 与 spec.md
    stage1_naming_path = OUTPUT_DIR / f"需求分析_{product}_latest.md"
    if stage1_naming_path.exists():
        role_table = extract_role_table(stage1_naming_path.read_text(encoding="utf-8"))
        if prd_path.exists():
            check_role_naming_consistency(
                prd_path.read_text(encoding="utf-8"),
                role_table or {}, r, "阶段4 prd.html", "S4-NAMING-01",
            )
        if spec_path.exists():
            check_role_naming_consistency(
                spec_path.read_text(encoding="utf-8"),
                role_table or {}, r, "阶段4 spec.md", "S4-NAMING-01-spec",
            )
    else:
        r.section("S4-NAMING-01 角色命名一致性(建议 7 / issue # 3 复盘)")
        r.warn(
            f"[S4-NAMING-01] 阶段 1 产物不存在: {stage1_naming_path},无法启用命名校验"
        )

    # S4-PERF-01~05 性能反模式扫描(建议 9-L2 / issue # 15 复盘根因 E 预防层)
    # 扫描 prd.html 找已知性能反模式,触发 WARN 提示 PM 是否在文档场景下被 PRD 静态化兜底 CSS(prd_template.html)关停
    if prd_path.exists():
        _check_perf_antipatterns(prd_path.read_text(encoding="utf-8"), r)

    # S4-FRAME-01 frame class 禁止 inline 尺寸 override(/retro 2026-05-12_1521 # 4 复盘根因 B)
    # 扫 drafts 真源 + outputs 派生,frame class 含 inline width/height/min-height/max-height 即 FAIL
    _check_frame_inline_size_override(REPO_ROOT, r)

    sys.exit(r.summary())


# ── S4-PERF-01~05 性能反模式扫描(建议 9-L2 / issue # 15 四轮整改复盘根因 E)──────
#
# 触发 WARN(非 FAIL),因为:
#   - 这些反模式在真实业务页面可能合理(业务需要 loading 动画 / 多层 gradient 等)
#   - PRD 文档场景下由 prd_template.html 顶部 PRD 静态化兜底 CSS 关停
#   - 本扫描提示 PM/Supervisor 视觉/性能复测时关注这些点

def _check_perf_antipatterns(prd_content: str, r) -> None:
    """扫 prd.html 性能反模式,触发 WARN 提示。

    S4-PERF-01 越界 stripe keyframes(translateX 含 -N% 或 >100% 字面)
    S4-PERF-02 background-blend-mode: multiply/overlay/soft-light 高代价 blend
    S4-PERF-03 inline style="animation:...infinite" 大数量
    S4-PERF-04 @keyframes 命名是否符合一键关停清单
    S4-PERF-05 absolute 子元素的父容器 overflow:auto 组合
    """
    r.section("S4-PERF-01~05 性能反模式扫描(建议 9-L2 / issue # 15 复盘)")

    # S4-PERF-01 越界 stripe keyframes
    out_of_bound = re.findall(
        r"@keyframes\s+([A-Za-z0-9_-]+)\s*\{[^}]*translateX\(\s*(-\d+%|\d{3,}%)",
        prd_content, re.DOTALL,
    )
    if out_of_bound:
        names = sorted(set(m[0] for m in out_of_bound))
        r.warn(
            f"[S4-PERF-01] 检测到越界 stripe keyframes {len(names)} 个:{names} — "
            f"translateX(<0% 或 >100%)在父级 overflow:auto 下会触发滚动条闪烁循环;"
            f"PRD 文档场景已由 prd_template.html PRD 静态化兜底 CSS 关停,"
            f"业务页面引用时须同步排查父容器 overflow(参 proj_component_protocol.md §5.4 父容器契约)"
        )
    else:
        r.ok("S4-PERF-01 无越界 stripe keyframes")

    # S4-PERF-02 multiply / overlay / soft-light blend
    blends = re.findall(
        r"background-blend-mode:\s*(multiply|overlay|soft-light|hard-light|color-dodge)",
        prd_content,
    )
    if blends:
        from collections import Counter
        c = Counter(blends)
        r.warn(
            f"[S4-PERF-02] 检测到高代价 background-blend-mode {sum(c.values())} 处: "
            f"{dict(c)} — 与多层 gradient 叠加 paint 成本高;"
            f"PRD 文档场景已由 PRD 静态化兜底关停 qd-canvas 一处,"
            f"如有其他实例需在 proj_component_protocol.md §5.4 父容器契约扫描中确认 paint 影响"
        )
    else:
        r.ok("S4-PERF-02 无高代价 background-blend-mode")

    # S4-PERF-03 inline style infinite 动画大数量
    inline_infinite = re.findall(
        r'style="[^"]*animation:[^"]*infinite', prd_content
    )
    if len(inline_infinite) > 10:
        r.warn(
            f"[S4-PERF-03] inline style 含 infinite 动画 {len(inline_infinite)} 处 "
            f"(>10 阈值)— 已由 PRD 静态化兜底 `[style*=\"animation:\"][style*=\"infinite\"] "
            f"{{ animation: none !important }}` 关停,但数量大说明 drafts 内骨架/spinner "
            f"未抽象为 fb-* 组件,建议长远抽象到 fb-fallback CSS"
        )
    elif inline_infinite:
        r.ok(f"S4-PERF-03 inline infinite 动画 {len(inline_infinite)} 处 (≤10 阈值)")
    else:
        r.ok("S4-PERF-03 无 inline infinite 动画")

    # S4-PERF-04 @keyframes 命名是否符合一键关停清单
    kf_names = re.findall(r"@keyframes\s+([A-Za-z0-9_-]+)", prd_content)
    known_patterns = ("loading-stripe", "skeleton", "spin", "pulse", "shake")
    nonconforming = [
        k for k in kf_names
        if not any(p in k for p in known_patterns)
    ]
    if nonconforming:
        r.warn(
            f"[S4-PERF-04] @keyframes 命名不在一键关停清单 {nonconforming} — "
            f"建议改为含 'loading-stripe' / 'skeleton' / 'spin' / 'pulse' 关键字的命名,"
            f"以便 PRD 静态化兜底 CSS 通过 [class*=\"-loading-stripe\"] 等通配选择器统一关停"
        )
    elif kf_names:
        r.ok(f"S4-PERF-04 全部 {len(kf_names)} 个 keyframes 命名符合一键关停清单")
    else:
        r.ok("S4-PERF-04 无 @keyframes 定义")

    # S4-PERF-05 absolute 子元素 + 父级 overflow:auto 组合(简化版,基于行邻近度启发)
    # 完整实现需要 CSS AST parse;本版仅做"提示性扫描":
    # 找形如 `.X { ... overflow-x: auto ... position: relative ... }` 之后 `.X::before { position: absolute }`
    # 命中即提示 PM 在 proj_component_protocol.md §5.4 父容器契约中确认这种组合的安全性
    paired = re.findall(
        r"(\.[\w-]+)\s*\{[^}]*overflow-x:\s*auto[^}]*position:\s*relative",
        prd_content,
    )
    if paired:
        r.warn(
            f"[S4-PERF-05] {len(paired)} 个选择器同时含 overflow-x:auto + position:relative "
            f"(典型 absolute 伪元素父容器场景): {paired[:5]}{'...' if len(paired) > 5 else ''} — "
            f"若有 absolute 伪元素含越界 transform 会触发滚动条闪烁;请按 proj_component_protocol.md §5.4 父容器契约确认"
        )
    else:
        r.ok("S4-PERF-05 无 overflow-x:auto + position:relative 组合(0 滚动条闪烁风险点)")


# ── S4-FRAME-01 frame class 禁止 inline 尺寸 override(/retro 2026-05-12_1521 # 4 复盘根因 B)─────
#
# 设计规则:
#   - 5 frame 类(.phone-frame / .desktop-frame / .h5-frame / .tablet-frame / .miniprogram-frame)
#     标准尺寸由 prd_template.html 真源定义,不应被 inline `style="min-height:..."` 等覆盖
#   - 若 PM 在 modal 状态帧需要"紧凑背景帧"视觉,应用 `.is-modal-bg` modifier
#     (`<div class="phone-frame is-modal-bg">`),不要 inline 自由发挥
#   - 配套规范:prd_expression_standard.md §零.2 状态帧表达约束第 4 条
#
# 触发即 ERROR,提示 PM 改用 .is-modal-bg modifier(若是 modal 背景帧场景)或删除 inline override

FRAME_INLINE_SIZE_RE = re.compile(
    r'<div[^>]*\bclass="(?:[^"]*\s)?(phone|desktop|h5|tablet|miniprogram)-frame(?:\s[^"]*)?"[^>]*'
    r'\bstyle="[^"]*\b(width|height|min-height|max-height)\s*:\s*\d',
    re.IGNORECASE,
)


def _check_frame_inline_size_override(repo_root: Path, r) -> None:
    """扫 drafts 真源 + outputs 派生,frame class 含 inline 尺寸 override 即 FAIL。

    误判豁免:已含 .is-modal-bg modifier 的 frame 不计(规范允许 modal 背景帧用紧凑尺寸)。
    """
    r.section("S4-FRAME-01 frame class 禁止 inline 尺寸 override(/retro 2026-05-12_1521 # 4 复盘)")

    drafts_dir = repo_root / "process_record" / "drafts"
    outputs_dir = repo_root / "outputs"
    targets: list[Path] = []
    if drafts_dir.exists():
        targets.extend(sorted(drafts_dir.glob("prd_M*_draft.html")))
    if outputs_dir.exists():
        targets.extend(sorted(outputs_dir.glob("prd_*_latest.html")))

    total_violations: list[tuple[str, int, str]] = []  # (file, line_no, snippet)
    for path in targets:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if FRAME_INLINE_SIZE_RE.search(line):
                # 豁免:已用 .is-modal-bg modifier 的 frame(规范允许)
                if "is-modal-bg" in line:
                    continue
                rel = path.relative_to(repo_root) if path.is_absolute() else path
                total_violations.append((str(rel), i, line.strip()[:120]))

    if total_violations:
        msg = (
            f"[S4-FRAME-01] frame class inline 尺寸 override 共 {len(total_violations)} 处违反:\n"
        )
        for f, ln, snip in total_violations[:10]:
            msg += f"  - {f}:{ln}: {snip}\n"
        if len(total_violations) > 10:
            msg += f"  - ...(共 {len(total_violations)} 处,仅列前 10)\n"
        msg += (
            "frame class 标准尺寸由 prd_template.html 真源定义,违反 SSOT #30 派生层禁修真源精神。\n"
            "若是 modal 背景帧场景,改用 `<div class=\"phone-frame is-modal-bg\">` modifier\n"
            "(参 prd_expression_standard.md §零.2 状态帧表达约束第 4 条)。"
        )
        r.fail(msg)
    else:
        r.ok(
            f"S4-FRAME-01 {len(targets)} 个 drafts/outputs 文件 0 处 frame class inline 尺寸 override"
        )


if __name__ == "__main__":
    main()
