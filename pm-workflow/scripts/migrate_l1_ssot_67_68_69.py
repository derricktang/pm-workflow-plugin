#!/usr/bin/env python3
"""migrate_l1_ssot_67_68_69.py — L1 整改 migrate 脚本（SSOT #67/#68/#69 配套）

用途
====

SSOT #67/#68/#69 完成 L2 落地后，下游 spec.md 需做配套 L1 整改：
  - B2-1 spec.md 段头骨架插入：为每个 S2.M[XX] 模块补 .4B 业务规则 + .5B 数据规模
        段头骨架（待 PM 补全）
  - B2-2 单页 F 主页面字段自动派生：扫每个 F-xxx 节，若仅 1 个涉及页面则自动
        填入「主页面」字段；多页或无涉及页面则插入占位
  - B2-3 PM 整改提示书生成：聚合 precheck_stage4 各 check_* 输出，输出
        process_record/issues/PM_整改_<产品名>_SSOT_67_68_69_<时间戳>.md

用法
====

  python3 migrate_l1_ssot_67_68_69.py --root /path/to/downstream/repo
                                       [--dry-run]   # 预览不写入
                                       [--task b2-1,b2-2,b2-3]  # 默认全做

强约束
======

- idempotent：重跑必须不破坏 PM 已填的内容；B2-1/B2-2 各自有检测逻辑
- 真源字面：spec.md 段头必须用 .4B/.5B（与 SSOT #61 .4/.5 不撞号；详
  ssot_anchors.md SSOT #68 entry）
- 派生函数命名与 assemble.py extract_business_rules / extract_data_scale 字面
  对齐，便于 PM 一次整改后下次 assemble 派生即生效

出口码
======

  0 — 成功（含 dry-run 全成功）
  1 — 失败（仓不存在 / spec 文件不存在 / IO 异常等）
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


# ── 配置 ──────────────────────────────────────────────────────────────────────

ALL_TASKS = ("b2-1", "b2-2", "b2-3")

# 段头匹配（与 precheck_stage4 + assemble 同源字面）
MODULE_OVERVIEW_RE = re.compile(r"^## S2\.(M\d+) 模块概述", re.MULTILINE)

# 子段头通用匹配 ## S2.MXX.<num><suffix?> <title>
SUBSECTION_RE_TMPL = r"^## S2\.{mid}\.{num}{suffix}\b"


# F-xxx 段头识别（与 precheck_stage4._F_SECTION_RE 同源）
F_SECTION_RE = re.compile(r"^####\s+F-(\d+)[：:]\s*(.+?)$", re.MULTILINE)
F_NEXT_RE = re.compile(r"^####\s+F-\d+[：:]|^###\s|^##\s", re.MULTILINE)

# 字段抽取（与 precheck_stage4._F_FIELD_PATTERNS 同源）
F_FIELD_INVOLVED_RE = re.compile(
    r"\*\*涉及页面\*\*[：:]\s*([^|｜│]+?)(?:　?[|｜│]|$)", re.MULTILINE
)
# 主页面字段：值可为 P-XX 或占位（如 `[待 PM 选...]` / `[待 PM 补...]`）
# 检测「主页面」字段是否存在（不区分值类型），用于 idempotent 跳过
F_FIELD_MAIN_RE = re.compile(r"\*\*主页面\*\*[：:]\s*(\S+)")
# 仅匹配已填实际 P-XX ID 的主页面字段（用于 assemble 派生消费）
F_FIELD_MAIN_PID_RE = re.compile(r"\*\*主页面\*\*[：:]\s*(P-?\d+)")
F_FIELD_PRIORITY_RE = re.compile(r"\*\*优先级\*\*[：:]\s*([^\s|｜│]+)")
F_FIELD_JOURNEY_RE = re.compile(
    r"\*\*所属旅程\*\*[：:]\s*([^|｜│]+?)(?:　?[|｜│]|$)", re.MULTILINE
)

# 涉及页面值内的 P-xxx 提取
P_ID_RE = re.compile(r"P-?\d+")


# ── 数据类 ────────────────────────────────────────────────────────────────────


class TaskResult:
    """单项子任务执行结果。"""

    def __init__(self, name: str) -> None:
        self.name = name
        self.success = True
        self.summary: str = ""
        self.details: list[str] = []

    def add(self, msg: str) -> None:
        self.details.append(msg)

    def fail(self, msg: str) -> None:
        self.success = False
        self.add(f"[ERROR] {msg}")


# ── 工具 ──────────────────────────────────────────────────────────────────────


def find_spec_md(root: Path) -> Optional[Path]:
    """定位 outputs/spec_*_latest.md（约定唯一）。"""
    out_dir = root / "outputs"
    if not out_dir.exists():
        return None
    candidates = sorted(out_dir.glob("spec_*_latest.md"))
    if not candidates:
        return None
    return candidates[0]


def find_product_name(spec_path: Path) -> str:
    """从 spec 文件名提取产品名（spec_<name>_latest.md）。"""
    stem = spec_path.stem  # spec_报价工具_latest
    m = re.match(r"spec_(.+)_latest$", stem)
    if m:
        return m.group(1)
    return "unknown"


def iter_f_sections(spec_md: str):
    """生成 (fid, name, body_start, body_end) 四元组。

    body 范围是 #### F-xxx 行的下一字符到下一个 ####/###/## 之前的位置。
    """
    matches = list(F_SECTION_RE.finditer(spec_md))
    for i, m in enumerate(matches):
        fid = f"F-{m.group(1)}"
        name = m.group(2).strip()
        start = m.end()
        nxt = F_NEXT_RE.search(spec_md, start)
        end = nxt.start() if nxt else len(spec_md)
        yield fid, name, start, end


# ── B2-1：spec.md 段头骨架插入 ───────────────────────────────────────────────


def _next_subsection_index(
    spec_md: str, mid: str, after_num: int
) -> Optional[int]:
    """找到 `## S2.{mid}.{after_num}` 段头位置，返回该行起始 index。

    若该号段头不存在，递增 after_num 至 9 寻找次最近后继；都不存在返回 None。
    """
    for num in range(after_num, 10):
        pattern = re.compile(rf"^## S2\.{mid}\.{num}\b", re.MULTILINE)
        m = pattern.search(spec_md)
        if m:
            return m.start()
    # 找下一个模块概述 / 文档尾部段（## 但不属本模块）
    pattern = re.compile(rf"^## (?!S2\.{mid}\.)", re.MULTILINE)
    # 跳过本模块的 ## S2.{mid} 模块概述自身
    start = 0
    overview = re.search(rf"^## S2\.{mid} 模块概述", spec_md, re.MULTILINE)
    if overview:
        start = overview.end()
    m = pattern.search(spec_md, start)
    return m.start() if m else None


def _has_subsection(spec_md: str, mid: str, num_with_suffix: str) -> bool:
    """检测 `## S2.{mid}.{num_with_suffix}` 段头是否已存在。"""
    pattern = re.compile(
        rf"^## S2\.{mid}\.{num_with_suffix}\b", re.MULTILINE
    )
    return pattern.search(spec_md) is not None


def _build_skeleton_block(mid: str, suffix: str, title: str) -> str:
    """构造段头骨架文本（结尾含两个换行）。"""
    return f"## S2.{mid}.{suffix} {title}\n\n[待 PM 补全]\n\n"


def task_b2_1(spec_md: str, result: TaskResult) -> str:
    """B2-1 — 在 .5 前插入 .4B；在 .6 前（或下一段头前）插入 .5B。

    idempotent：已存在的 .4B/.5B 段头跳过（不重复插入）。
    """
    modules = MODULE_OVERVIEW_RE.findall(spec_md)
    if not modules:
        result.summary = "spec.md 无 S2.MXX 模块段头（旧版 spec / 跳过）"
        return spec_md

    inserted_4b = 0
    inserted_5b = 0
    skipped_4b: list[str] = []
    skipped_5b: list[str] = []

    # 由于插入会改变索引，需从后向前处理
    for mid in reversed(modules):
        # .5B 插入：参考点 = .6 段头；若无则用下一段后继
        if _has_subsection(spec_md, mid, "5B"):
            skipped_5b.append(mid)
        else:
            anchor = _next_subsection_index(spec_md, mid, 6)
            if anchor is None:
                result.add(f"[WARN] {mid}: .5B 锚点未找到（无 .6 后继段）→ 跳过")
            else:
                block = _build_skeleton_block(mid, "5B", "数据规模")
                spec_md = spec_md[:anchor] + block + spec_md[anchor:]
                inserted_5b += 1

        # .4B 插入：参考点 = .5 段头；若无则 .6 / 下一段
        if _has_subsection(spec_md, mid, "4B"):
            skipped_4b.append(mid)
        else:
            anchor = _next_subsection_index(spec_md, mid, 5)
            if anchor is None:
                result.add(f"[WARN] {mid}: .4B 锚点未找到（无 .5 后继段）→ 跳过")
            else:
                block = _build_skeleton_block(mid, "4B", "业务规则")
                spec_md = spec_md[:anchor] + block + spec_md[anchor:]
                inserted_4b += 1

    result.summary = (
        f"模块数 {len(modules)}；插入 .4B {inserted_4b} 个 / .5B {inserted_5b} 个；"
        f"已存在 .4B {len(skipped_4b)} 个 / .5B {len(skipped_5b)} 个（跳过）"
    )
    if skipped_4b:
        result.add(f"已存在 .4B（跳过）: {', '.join(skipped_4b[:10])}"
                   + (" ..." if len(skipped_4b) > 10 else ""))
    if skipped_5b:
        result.add(f"已存在 .5B（跳过）: {', '.join(skipped_5b[:10])}"
                   + (" ..." if len(skipped_5b) > 10 else ""))
    return spec_md


# ── B2-2：单页 F 主页面字段自动派生 ─────────────────────────────────────────


def _extract_pages_from_involved(text: str) -> list[str]:
    """从「涉及页面」字段值中提取所有 P-XX ID（保留原顺序，去重保留首次出现）。"""
    pages = []
    seen = set()
    for m in P_ID_RE.finditer(text):
        pid = m.group(0)
        # 规范化为 P-XX（保留原写法的「-」或无「-」），但去重以原字面为准
        if pid not in seen:
            seen.add(pid)
            pages.append(pid)
    return pages


def _build_main_page_bullet(value: str) -> str:
    """构造主页面 bullet 行（前接换行，便于直接 splice 进 body）。"""
    return f"- **主页面**：{value}\n"


def task_b2_2(spec_md: str, result: TaskResult) -> str:
    """B2-2 — F-xxx 节自动派生「主页面」字段。

    规则：
      - 已含「主页面」字段 → 跳过（idempotent）
      - 仅 1 个 P-XX → 自动填该值
      - ≥ 2 个 P-XX → 占位 [待 PM 选，候选: ...]
      - 完全无「涉及页面」字段 → 占位 [待 PM 补涉及页面后选]
    """
    sections = list(iter_f_sections(spec_md))
    if not sections:
        result.summary = "spec.md 无 F-xxx 节（旧版 spec / 跳过）"
        return spec_md

    auto_single = 0
    placeholder_multi = 0
    placeholder_no_involved = 0
    skipped_existing = 0

    # 从后向前插入避免索引偏移
    for fid, fname, body_start, body_end in reversed(sections):
        body = spec_md[body_start:body_end]
        if F_FIELD_MAIN_RE.search(body):
            skipped_existing += 1
            continue

        invol_m = F_FIELD_INVOLVED_RE.search(body)
        if not invol_m:
            value = "[待 PM 补涉及页面后选]"
            placeholder_no_involved += 1
        else:
            invol_text = invol_m.group(1).strip()
            pages = _extract_pages_from_involved(invol_text)
            if len(pages) == 0:
                value = "[待 PM 补涉及页面后选]"
                placeholder_no_involved += 1
            elif len(pages) == 1:
                value = pages[0]
                auto_single += 1
            else:
                value = f"[待 PM 选，候选: {', '.join(pages)}]"
                placeholder_multi += 1

        # 插入位置：body 起始处第一个非空行的下一行起点
        # 优先放在 body 第一行（紧贴 #### F-xxx 标题之后），与现有 F-xxx 字段
        # bullet 同列。新行单独成段，置于 body 顶部。
        new_bullet = _build_main_page_bullet(value)

        # 找 body 内第一个换行（即 #### F-xxx 行结束）后立即插入
        # body_start 指向 #### F-xxx 标题之后的字符，通常是 "\n"
        # 直接将 bullet 插在 body 顶部
        spec_md = (
            spec_md[:body_start]
            + "\n"
            + new_bullet.rstrip("\n")
            + spec_md[body_start:]
        )

    result.summary = (
        f"F-xxx 节数 {len(sections)}；自动派生单页主页面 {auto_single} 个；"
        f"多页占位 {placeholder_multi} 个；无涉及页面占位 {placeholder_no_involved} 个；"
        f"已存在跳过 {skipped_existing} 个"
    )
    return spec_md


# ── B2-3：PM 整改提示书生成 ───────────────────────────────────────────────


def _run_precheck(root: Path) -> tuple[str, int]:
    """跑 precheck_stage4.py 取得 WARN/FAIL 文本输出 + 退出码。

    `precheck_stage4.py` 通过 `REPO_ROOT = __file__.parent.parent.parent` 解析仓根，
    因此必须使用**下游仓自带的**副本（`<root>/pm-workflow/scripts/precheck_stage4.py`），
    而非上游 pm-workflow 仓的脚本。若下游未同步 L2（无副本），降级用上游脚本（仅
    能扫上游仓内文件，对下游产物为 FAIL "文件不存在"）。
    """
    downstream_script = root / "pm-workflow" / "scripts" / "precheck_stage4.py"
    if downstream_script.exists():
        script = downstream_script
    else:
        script = Path(__file__).resolve().parent / "precheck_stage4.py"

    scaffold = root / "process_record" / "tasks" / "scaffold.json"
    cmd = ["python3", str(script)]
    if scaffold.exists():
        cmd.append(str(scaffold))
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(root),
        )
        return proc.stdout + "\n" + proc.stderr, proc.returncode
    except Exception as exc:
        return f"[precheck 调用异常] {exc}", -1


# 12 个新规则节标题字面（与 precheck_stage4.py r.section() 字面同源）
SSOT_676869_SECTIONS = [
    ("S4-49", "SSOT #68 / S4-49 spec §S2.MXX.4B 业务规则段头（WARN）"),
    ("S4-50", "SSOT #68 / S4-50 spec §S2.MXX.5B 数据规模段头（WARN）"),
    ("S4-51", "SSOT #68 / S4-51 spec F-xxx 主页面字段（WARN）"),
    ("S4-52", "SSOT #68 / S4-52 spec F-xxx 4 必填字段（WARN）"),
    ("S4-53", "SSOT #68 / S4-53 prd interaction-card C-4 派生闭环（WARN）"),
    ("S4-54", "SSOT #67 / S4-54 prd A-05 旧 article 形态清除（WARN）"),
    ("S4-55", "SSOT #67 / S4-55 prd A-索引 4 列 + spec F-xxx 数对齐（WARN）"),
    ("S4-56", "SSOT #69 / S4-56 interaction-card C-0 状态差异说明（WARN）"),
    ("S4-57", "SSOT #69 / S4-57 interaction-card C-1 列表回显 4 行表（WARN）"),
    ("S4-58", "SSOT #69 / S4-58 interaction-card C-2.A 6 列单元清单（WARN）"),
    ("S4-59", "SSOT #69 / S4-59 interaction-card C-2.B 5 列字段子表（WARN）"),
    ("S4-60", "SSOT #69 / S4-60 interaction-card C-3 触点表 6 列（WARN）"),
]


def _parse_precheck_sections(output: str) -> dict[str, dict]:
    """从 precheck stdout 提取 12 个 SSOT #67/68/69 节及其 WARN/OK 行。

    返回 {rule_id: {"section_title": str, "lines": [str], "warn_count": int}}
    """
    result: dict[str, dict] = {}
    # 把 output 按行扫
    lines = output.splitlines()
    current_id: Optional[str] = None
    current_buf: list[str] = []

    # 节标题前缀 → rule_id 反查表
    title_to_id = {title: rid for rid, title in SSOT_676869_SECTIONS}

    def flush():
        if current_id is not None:
            warn_n = sum(1 for ln in current_buf if "[WARN]" in ln)
            result[current_id] = {
                "section_title": current_section_title,
                "lines": current_buf[:],
                "warn_count": warn_n,
            }

    current_section_title = ""
    for ln in lines:
        # 节标题识别：以 "==" 或 SSOT 字面开头（precheck 用 r.section 输出）
        # precheck Report.section 输出形如：
        #   "\n── SSOT #68 / S4-49 ...（WARN）──"
        # 或类似带 box 字符的 header。简化：找包含已知 title 字面的行
        stripped = ln.strip("─ \t")
        matched = False
        for title, rid in title_to_id.items():
            if title in ln:
                # 切换 section
                flush()
                current_id = rid
                current_section_title = title
                current_buf = []
                matched = True
                break
        if matched:
            continue
        if current_id is not None:
            current_buf.append(ln)
    flush()
    return result


def task_b2_3(
    root: Path, product_name: str, result: TaskResult
) -> Optional[Path]:
    """B2-3 — 生成 PM 整改提示书。

    返回提示书路径（dry-run 模式下也返回预期路径，但不写盘；调用方据
    args.dry_run 判断是否实际写入）。
    """
    output, returncode = _run_precheck(root)
    parsed = _parse_precheck_sections(output)

    total_warn = sum(v["warn_count"] for v in parsed.values())
    matched_rules = sum(1 for v in parsed.values() if v["warn_count"] > 0)
    result.summary = (
        f"precheck 退出码 {returncode}；命中 SSOT #67/#68/#69 规则 "
        f"{matched_rules}/12；总 WARN 行数 {total_warn}"
    )

    # 构造提示书 markdown
    timestamp = time.strftime("%Y-%m-%d_%H%M")
    issues_dir = root / "process_record" / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    out_path = issues_dir / (
        f"PM_整改_{product_name}_SSOT_67_68_69_{timestamp}.md"
    )

    sections_md: list[str] = []
    sections_md.append(f"# PM 整改提示书 — SSOT #67/#68/#69 配套 L1 整改\n")
    sections_md.append(f"生成时间：{timestamp}")
    sections_md.append(f"产品：{product_name}")
    sections_md.append(f"工作目录：{root}\n")
    sections_md.append("## 1. 总览\n")
    sections_md.append(
        f"- 命中规则数：{matched_rules}/12（SSOT #67/#68/#69 共 12 项）"
    )
    sections_md.append(f"- 总 WARN 行数：{total_warn}")
    sections_md.append(f"- precheck_stage4 退出码：{returncode}\n")

    sections_md.append("## 2. 建议整改顺序\n")
    sections_md.append(
        "推荐按下方顺序执行（先治源头，再派生层，最后机械验证）：\n"
    )
    sections_md.append(
        "1. **spec.md 源头**（B2-1 已自动补 .4B/.5B 骨架；B2-2 已派生主页面字段）"
    )
    sections_md.append(
        "   - 在 .4B 段头下按页面分组补业务规则（详 proto_spec_md.md §三.5 §S2.M[XX].4B）"
    )
    sections_md.append(
        "   - 在 .5B 段头下按页面分组补数据规模三维度（详 §三.5 §S2.M[XX].5B）"
    )
    sections_md.append(
        "   - 检查 F-xxx「主页面」字段中的 `[待 PM 选...]` / `[待 PM 补...]` 占位"
    )
    sections_md.append(
        "2. **drafts/ 模块草稿层**（若 outputs/spec 是 assemble 派生而非主写）"
    )
    sections_md.append(
        "   - 改 `process_record/drafts/spec_M[XX]_draft.md` 对应模块"
    )
    sections_md.append(
        "3. **重跑 assemble.py**"
    )
    sections_md.append(
        "   - `python3 pm-workflow/scripts/assemble.py spec --force-overwrite`"
    )
    sections_md.append(
        "   - `python3 pm-workflow/scripts/assemble.py prd --force-overwrite`"
    )
    sections_md.append(
        "4. **重跑 precheck_stage4.py** 验证 12 项规则 WARN 数收敛\n"
    )

    sections_md.append("## 3. 详细 WARN 清单（按规则分组）\n")
    for rid, title in SSOT_676869_SECTIONS:
        block = parsed.get(rid)
        if not block or block["warn_count"] == 0:
            sections_md.append(f"### {rid}: {title.split(' ', 2)[-1]}\n")
            sections_md.append("- PASS / 无 WARN\n")
            continue
        sections_md.append(f"### {rid}: {title.split(' ', 2)[-1]}\n")
        sections_md.append(f"WARN 行数：{block['warn_count']}\n")
        sections_md.append("```")
        for ln in block["lines"]:
            if "[WARN]" in ln or "[OK]" in ln:
                sections_md.append(ln.rstrip())
        sections_md.append("```\n")
        # 整改示例
        sections_md.append(_remediation_example(rid))

    sections_md.append("## 4. 附：precheck_stage4 完整输出（调试用）\n")
    sections_md.append("```")
    sections_md.append(output.rstrip())
    sections_md.append("```\n")

    content = "\n".join(sections_md)
    return out_path, content


def _remediation_example(rule_id: str) -> str:
    """按规则 ID 返回整改示例文本（含一两句操作指引）。"""
    examples = {
        "S4-49": (
            "**整改示例**：在 spec.md 找到 `## S2.M[XX].4B 业务规则` 段头，"
            "按页面分组撰写：\n\n"
            "```markdown\n#### P[XX] 页面名\n\n- 规则一（含边界值）\n"
            "- 规则二\n```\n"
        ),
        "S4-50": (
            "**整改示例**：在 spec.md 找到 `## S2.M[XX].5B 数据规模` 段头，"
            "按页面分组撰写三维度：\n\n"
            "```markdown\n#### P[XX] 页面名\n\n- 单用户数据量：N\n"
            "- 单次返回量：N\n- 操作频率：N\n```\n"
        ),
        "S4-51": (
            "**整改示例**：在每个 F-xxx 节加 `**主页面**：P-XX` 字段（必须 ∈"
            "「涉及页面」集合）。B2-2 已自动派生单页 F；多页 F 需 PM 从候选中选定。\n"
        ),
        "S4-52": (
            "**整改示例**：补齐 4 必填字段：优先级 / 所属旅程 / 涉及页面 / 主页面。"
            "格式参考 proto_spec_md.md §三.5 F-xxx 示例。\n"
        ),
        "S4-53": (
            "**整改示例**：spec 补完 .4B/.5B + F-xxx 主页面后，重跑 "
            "`assemble.py prd --force-overwrite` 让 C-4 派生闭环。\n"
        ),
        "S4-54": (
            "**整改示例**：A-05 已重组为 4 列轻量索引；重跑 "
            "`assemble.py prd --force-overwrite` 让 build_function_overview_index 派生。\n"
        ),
        "S4-55": (
            "**整改示例**：spec F-xxx 数与 A-索引行数不对齐，多半是 spec 改后"
            "未重 assemble。跑 `assemble.py prd --force-overwrite`。\n"
        ),
        "S4-56": (
            "**整改示例**：每个 interaction-card 应含 "
            "`<div class=\"state-diff-note\">` 子区块（C-0 状态差异说明）。\n"
        ),
        "S4-57": (
            "**整改示例**：C-1 列表回显 4 行：排序规则 / 加载方式 / 总数回显 / "
            "空列表判断。无列表场景注明「本帧无列表」豁免。\n"
        ),
        "S4-58": (
            "**整改示例**：C-2.A 6 列：C 触点 ID / 单元名称 / 是否封装为组件 / "
            "渲染时机 / 跨平台差异 / 关联 T 触点。无数据展示场景注明「本帧无数据展示」。\n"
        ),
        "S4-59": (
            "**整改示例**：C-2.B 5 列：D 触点 ID / 字段名 / 接口字段 / "
            "显示格式 / 空值处理。\n"
        ),
        "S4-60": (
            "**整改示例**：C-3 6 列：序号 / 触点说明 / 触发 / 行为 / 跳转 / 边缘。"
            "无交互场景注明「本帧无交互触点」。\n"
        ),
    }
    return examples.get(rule_id, "")


# ── 主流程 ────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="L1 整改 migrate 脚本（SSOT #67/#68/#69 配套）"
    )
    parser.add_argument(
        "--root", required=True, type=Path,
        help="下游产品仓根路径（含 outputs/ + process_record/）"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="预览不写入"
    )
    parser.add_argument(
        "--task", default=",".join(ALL_TASKS),
        help=f"指定子任务（逗号分隔，默认全做）：{','.join(ALL_TASKS)}"
    )
    args = parser.parse_args()

    if not args.root.exists():
        print(f"[ERROR] 仓根路径不存在：{args.root}", file=sys.stderr)
        return 1

    spec_path = find_spec_md(args.root)
    if spec_path is None:
        print(f"[ERROR] 未找到 outputs/spec_*_latest.md（仓未生成或路径错）",
              file=sys.stderr)
        return 1

    product_name = find_product_name(spec_path)
    print(f"[INFO] 产品仓：{args.root}")
    print(f"[INFO] spec 文件：{spec_path}")
    print(f"[INFO] 产品名：{product_name}")
    print(f"[INFO] dry-run：{args.dry_run}")
    print(f"[INFO] 任务：{args.task}\n")

    tasks_to_run = {t.strip() for t in args.task.split(",") if t.strip()}
    invalid = tasks_to_run - set(ALL_TASKS)
    if invalid:
        print(f"[ERROR] 未知任务：{invalid}（合法：{ALL_TASKS}）", file=sys.stderr)
        return 1

    spec_md = spec_path.read_text(encoding="utf-8")
    original_spec = spec_md
    results: list[TaskResult] = []

    # B2-1
    if "b2-1" in tasks_to_run:
        r = TaskResult("B2-1 spec.md 段头骨架插入")
        spec_md = task_b2_1(spec_md, r)
        results.append(r)

    # B2-2
    if "b2-2" in tasks_to_run:
        r = TaskResult("B2-2 F-xxx 主页面字段自动派生")
        spec_md = task_b2_2(spec_md, r)
        results.append(r)

    # B2-3
    b3_payload: Optional[tuple[Path, str]] = None
    if "b2-3" in tasks_to_run:
        r = TaskResult("B2-3 PM 整改提示书生成")
        b3_payload = task_b2_3(args.root, product_name, r)
        results.append(r)

    # 打印执行报告
    print("══════════════ 执行报告 ══════════════")
    for r in results:
        status = "OK" if r.success else "FAIL"
        print(f"\n[{status}] {r.name}")
        print(f"  {r.summary}")
        for d in r.details:
            print(f"  - {d}")

    # 写入
    if args.dry_run:
        print(f"\n[DRY-RUN] 不写入文件")
        if spec_md != original_spec:
            diff_lines_added = spec_md.count("\n") - original_spec.count("\n")
            print(f"  spec.md 将新增约 {diff_lines_added} 行")
        if b3_payload is not None:
            out_path, content = b3_payload
            print(f"  将生成提示书：{out_path}")
            print(f"  提示书行数：{content.count(chr(10)) + 1}")
        return 0

    # 实际写入
    if spec_md != original_spec:
        spec_path.write_text(spec_md, encoding="utf-8")
        print(f"\n[WRITTEN] spec.md 已更新：{spec_path}")
    else:
        print(f"\n[NO-CHANGE] spec.md 内容未改变")

    if b3_payload is not None:
        out_path, content = b3_payload
        out_path.write_text(content, encoding="utf-8")
        print(f"[WRITTEN] PM 整改提示书：{out_path}")
        print(f"  行数：{content.count(chr(10)) + 1}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
