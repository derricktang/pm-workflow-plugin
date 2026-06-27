#!/usr/bin/env python3
"""
precheck_common.py — 4 阶段 precheck 共享检查函数(G-01 / G-02 跨阶段通用规则)

模块定位:
    rule_hard_constraints.md G-01 / G-02 是 4 阶段通用硬规则,本模块把它们抽象为
    `check_archive_sync` / `check_version_changelog` 两个 helper,
    供 precheck_stage1/2/3/4.py 在 main() 中按各自阶段参数调用。

SSOT 真源:
    pm-workflow/rules/rule_hard_constraints.md
      - G-01 文件命名与归档(L36-41)
      - G-02 变更记录表格式(L43-48)

依赖:
    仅 stdlib(re, pathlib);与 precheck_stage*.Report 类通过鸭子类型对接
    (依赖 r.section/ok/fail/warn 四个方法)。
"""

import re
from pathlib import Path


# ── G-02:变更记录表 6 列固定 + 「审核人」预填校验 ────────────────────────────

EXPECTED_CHANGELOG_HEADER = ["版本", "变更内容", "变更原因", "变更人", "审核人", "日期"]


def _parse_table_row(line: str) -> list[str]:
    """解析 markdown 表格行为 cell 列表(去除首尾 | 和两端空白)。"""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_separator_row(line: str) -> bool:
    """识别 markdown 表格分隔行(如 `| --- | --- |`)。"""
    return bool(re.match(r"^\s*\|[\s\-:|]+\|\s*$", line))


def check_version_changelog(content: str, r, stage_label: str) -> None:
    """G-02:变更记录表 6 列固定 + 最后一行「审核人」为空校验。

    Args:
        content: 产物文件内容(markdown 文本)
        r: Report 实例(需有 section/ok/fail 方法)
        stage_label: 阶段名(用于错误信息,如「阶段1」/「阶段4 spec.md」)

    校验逻辑:
        1. 从文件末尾向上扫,找首个含「版本」「变更内容」「审核人」三关键列的表头
        2. 表头列必须恰为 6 列且与 EXPECTED_CHANGELOG_HEADER 字面一致
        3. 提取分隔行之后的所有数据行
        4. 最后一行(= PM 本次新增版本行)的「审核人」列(第 5 列)必须为空字符串
           — Supervisor 通过后才能填入 `Supervisor Agent`,PM 禁止预填
    """
    r.section(f"G-02 变更记录表 6 列 + 「审核人」预填校验({stage_label})")

    lines = content.splitlines()
    header_idx = None
    for i in range(len(lines) - 1, -1, -1):
        ln = lines[i]
        if "|" in ln and "版本" in ln and "变更内容" in ln and "审核人" in ln:
            header_idx = i
            break

    if header_idx is None:
        r.fail(
            "[G-02] 未找到变更记录表表头(应含 6 列:"
            "`| 版本 | 变更内容 | 变更原因 | 变更人 | 审核人 | 日期 |`);"
            "SSOT 真源:rule_hard_constraints.md G-02"
        )
        return

    header_cols = _parse_table_row(lines[header_idx])
    if header_cols != EXPECTED_CHANGELOG_HEADER:
        r.fail(
            f"[G-02] 变更记录表表头列名/列数错误:实际 {header_cols};"
            f"期望 6 列:`| 版本 | 变更内容 | 变更原因 | 变更人 | 审核人 | 日期 |`"
        )
        return
    r.ok("变更记录表表头 6 列字面一致")

    data_lines: list[str] = []
    seen_sep = False
    for ln in lines[header_idx + 1:]:
        if not ln.strip().startswith("|"):
            break
        if _is_separator_row(ln):
            seen_sep = True
            continue
        if seen_sep:
            data_lines.append(ln)

    if not data_lines:
        r.fail(
            "[G-02] 变更记录表无数据行(至少应有初始版本行——阶段 1-3 v1.0 / 阶段 4 v0.1 未交付态)"
        )
        return

    last_row_cols = _parse_table_row(data_lines[-1])
    if len(last_row_cols) != 6:
        r.fail(
            f"[G-02] 最后一行列数不等于 6:实际 {len(last_row_cols)} 列,"
            f"内容 {last_row_cols}"
        )
        return

    # G-02 接受两种合法状态（NB-RT-04 修复 / 2026-05-12 /retro 落地后发现）:
    #   ① 空字符串 — PM 提交前状态(原硬约束)
    #   ② `Supervisor Agent` — Supervisor 通过后回填状态(§4.0.4 通用终审收尾规定)
    # 其他任何字面(如 PM Agent / 待主管审核 / TBD)均视为 PM 预填违规
    reviewer = last_row_cols[4]
    if reviewer == "":
        r.ok(
            f"最后一行(最新版本 `{last_row_cols[0]}`)「审核人」列已留空,符合 G-02(PM 提交前态)"
        )
    elif reviewer == "Supervisor Agent":
        r.ok(
            f"最后一行(最新版本 `{last_row_cols[0]}`)「审核人」列已回填 `Supervisor Agent`,"
            f"符合 G-02(Supervisor 通过后态,§4.0.4 通用终审收尾)"
        )
    else:
        r.fail(
            f"[G-02] 最后一行(最新版本 `{last_row_cols[0]}`)「审核人」列字面非法:`{reviewer}`;"
            f"仅接受两种合法值:空字符串(PM 提交前)或 `Supervisor Agent`(通过后回填);"
            f"SSOT:rule_hard_constraints.md G-02 + §4.0.4 通用终审收尾"
        )


# ── G-01:latest ↔ versions 归档同步校验 ────────────────────────────────────

def check_archive_sync(
    target_path: Path,
    r,
    stage_label: str,
    archive_prefix: str,
    repo_root: Path,
) -> None:
    """G-01:latest 路径存在 + versions/ 下有匹配快照校验。

    Args:
        target_path: 当前 latest 产物路径(阶段 1-3 是 .md,阶段 4 spec.md / prd.html)
        r: Report 实例
        stage_label: 阶段名(用于错误信息)
        archive_prefix: versions 归档命名前缀
            - 阶段 1-3:`[阶段名]_[产品名]` 形式(如 `需求分析_报价工具`)
            - 阶段 4:`deliverable`(因为归档为子目录形式)
        repo_root: 仓库根路径(用于定位 process_record/versions/)

    校验逻辑:
        1. latest 路径存在(resolve_target_path 已保证,本处兜底)
        2. versions/ 目录存在
        3. versions/ 下至少有一份匹配前缀的快照(文件或目录)
           — G-01 要求:初次创建时必须同步复制 v1.0 快照至 versions/
    """
    r.section(f"G-01 latest ↔ versions 归档同步({stage_label})")

    if not target_path.exists():
        r.fail(f"[G-01] latest 文件不存在:{target_path}")
        return
    try:
        rel = target_path.relative_to(repo_root)
    except ValueError:
        rel = target_path
    r.ok(f"latest 路径存在:{rel}")

    versions_dir = repo_root / "process_record" / "versions"
    if not versions_dir.exists():
        r.fail(
            f"[G-01] versions 归档目录不存在:{versions_dir};"
            f"应在产物初次创建时同步创建 v1.0 快照(rule_hard_constraints.md G-01)"
        )
        return

    if archive_prefix == "deliverable":
        candidates = [
            c for c in versions_dir.glob("deliverable_v*_*") if c.is_dir()
        ]
        match_type = "归档目录"
    else:
        candidates = sorted(versions_dir.glob(f"{archive_prefix}_v*_*.md"))
        match_type = "归档文件"

    if not candidates:
        r.fail(
            f"[G-01] versions/ 下无任何 `{archive_prefix}_v*_*` {match_type};"
            f"G-01 要求:初次创建时必须同步复制 v1.0 快照,每次修订前先归档当前 latest;"
            f"SSOT 真源:rule_hard_constraints.md G-01"
        )
        return

    r.ok(f"versions/ 下找到 {len(candidates)} 份 `{archive_prefix}_v*_*` {match_type}")


# ── 建议 7(/retro issue # 3 复盘根因 G)角色命名 SSOT helpers ──────────────────
#
# 阶段 1 §二 用户角色与权限表升级为 6 列(角色编号 / 规范字面 / 别名/禁用字面 /
# 角色描述 / 核心诉求 / 权限范围),本节 helper 抽取该表作为后续阶段命名 SSOT,
# precheck_stage2/3/4 跑前 Read stage 1 → extract_role_table → 在本阶段产物上
# check_role_naming_consistency 检测别名命中。
#
# 兼容性:
#   - 旧产物表头 4 列(角色 / 角色描述 / 核心诉求 / 权限范围)→ extract 返回 None
#     → SX-NAMING-01 仅 WARN("阶段 1 模板未升级,无法启用命名校验"),不阻断
#   - 新产物 6 列且字段合规 → extract 返回 {canonical: [aliases]} dict
#     → SX-NAMING-01 grep 产物命中别名触发 ERROR

EXPECTED_ROLE_TABLE_HEADER = [
    "角色编号", "规范字面（canonical）", "别名/禁用字面",
    "角色描述", "核心诉求", "权限范围",
]


def extract_role_table(stage1_content: str) -> dict | None:
    """从阶段 1 §二 用户角色与权限抽取 6 列角色表,返回 {canonical: [aliases]} dict。

    Args:
        stage1_content: 阶段 1 产物(`需求分析_[产品名]_latest.md`)的完整内容

    Returns:
        dict {规范字面 str: [别名 str, ...]}:成功识别 6 列表
        None:未找到 §二 / 表头非 6 列 / 表头列名不符 / 无数据行 → SX-NAMING-01 仅 WARN
    """
    # 定位 §二 用户角色与权限 section
    sec2_match = re.search(
        r"^##\s*二[、\.]\s*用户角色与权限", stage1_content, re.MULTILINE
    )
    if not sec2_match:
        return None
    sec2_start = sec2_match.end()
    next_h2 = re.search(r"^##\s+", stage1_content[sec2_start:], re.MULTILINE)
    sec2_end = sec2_start + next_h2.start() if next_h2 else len(stage1_content)
    sec2_text = stage1_content[sec2_start:sec2_end]

    # 找首个 markdown 表格(头行 + 分隔行 + 数据行)
    lines = sec2_text.splitlines()
    header_idx = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("|") and "角色" in ln and "规范字面" in ln:
            header_idx = i
            break
    if header_idx is None:
        return None

    header_cols = _parse_table_row(lines[header_idx])
    # 表头需含 6 个核心字段,允许"规范字面（canonical）"的括号变体
    if len(header_cols) != 6:
        return None
    # 关键字段存在校验(放松字面 match,但必含核心字)
    required_keywords = ["角色编号", "规范字面", "别名", "角色描述", "核心诉求", "权限范围"]
    for kw, col in zip(required_keywords, header_cols):
        if kw not in col:
            return None

    # 解析数据行
    role_table: dict[str, list[str]] = {}
    seen_sep = False
    for ln in lines[header_idx + 1:]:
        if not ln.strip().startswith("|"):
            break
        if _is_separator_row(ln):
            seen_sep = True
            continue
        if not seen_sep:
            continue
        cols = _parse_table_row(ln)
        if len(cols) != 6:
            continue
        canonical = cols[1].strip()
        # 跳过占位符行(如「【唯一规范字面】」)
        if not canonical or canonical.startswith("【"):
            continue
        aliases_raw = cols[2].strip()
        aliases: list[str] = []
        if aliases_raw and aliases_raw != "—" and not aliases_raw.startswith("【"):
            # 别名以 / 或 ， / , 分隔
            for token in re.split(r"[/，,、]", aliases_raw):
                t = token.strip()
                if t and t != "—":
                    aliases.append(t)
        role_table[canonical] = aliases

    return role_table if role_table else None


def check_role_naming_consistency(
    content: str,
    role_table: dict[str, list[str]],
    r,
    stage_label: str,
    item_id: str,
) -> None:
    """检测产物全文是否命中 role_table 中的「别名/禁用字面」。

    Args:
        content: 本阶段产物完整内容
        role_table: extract_role_table 返回的 {canonical: [aliases]} dict
        r: Report 实例
        stage_label: 阶段名(用于错误信息)
        item_id: 检查项编号(如 "S2-NAMING-01")

    校验逻辑:
        1. 遍历 role_table 所有 aliases
        2. 对每个 alias 全文 grep(逐行扫描记录行号)
        3. 若命中 → ERROR,提示替换为对应 canonical
        4. 排除 §二 角色定义表本身(allowing 别名出现在「别名/禁用字面」列内)

    豁免:
        - 别名出现在 §二 用户角色与权限 section 内(本就是 SSOT 表自身,
          抽取期间无法解析的占位行除外)
        - 别名出现在 §变更日志 / §变更记录 / §修订历史 / Changelog 章节内
          (历史字面引用不可避免,NB-RT-01 修复 — 2026-05-12 /retro 后发现)
    """
    r.section(f"{item_id} 角色命名一致性({stage_label},建议 7 / issue # 3 复盘)")

    if not role_table:
        r.warn(
            f"[{item_id}] 阶段 1 §二 未检测到 6 列角色定义表 — "
            f"NAMING 系列检查待阶段 1 模板升级后启用(建议 7-L1 模板侧)"
        )
        return

    # 定位 §二 范围(供豁免判断)
    sec2_match = re.search(r"^##\s*二[、\.]", content, re.MULTILINE)
    if sec2_match:
        next_h2 = re.search(r"^##\s+", content[sec2_match.end():], re.MULTILINE)
        sec2_end_line = (
            content[:sec2_match.end() + next_h2.start()].count("\n")
            if next_h2 else content.count("\n")
        )
        sec2_start_line = content[:sec2_match.start()].count("\n")
    else:
        sec2_start_line = sec2_end_line = -1

    # NB-RT-01 修复(2026-05-12 /retro 落地后发现):
    # 定位变更日志 / 修订历史 / Changelog 章节范围,供豁免判断
    # 因为这些章节会引用历史字面(如 SNB-04 整改记录中描述"客户访客 → 客户端访客"字面统一),
    # 是不可避免的历史引用,改成规范字面反而让历史记录失真。
    changelog_ranges: list[tuple[int, int]] = []
    for cl_match in re.finditer(
        r"^#{1,4}\s*(?:[\d.]+\s*)?(?:变更日志|变更记录|修订历史|Changelog|Change Log|更新日志)",
        content, re.MULTILINE | re.IGNORECASE,
    ):
        next_h = re.search(r"^#{1,4}\s+", content[cl_match.end():], re.MULTILINE)
        cl_start_line = content[:cl_match.start()].count("\n")
        cl_end_line = (
            content[:cl_match.end() + next_h.start()].count("\n")
            if next_h else content.count("\n")
        )
        changelog_ranges.append((cl_start_line, cl_end_line))

    def _in_changelog(line_idx: int) -> bool:
        """判断给定行号(1-based 转 0-based)是否在任一变更日志范围内。"""
        zero_based = line_idx - 1
        for s, e in changelog_ranges:
            if s < zero_based < e + 1:
                return True
        return False

    lines = content.splitlines()
    violations: list[tuple[int, str, str]] = []  # (line_no, alias, canonical)
    for canonical, aliases in role_table.items():
        for alias in aliases:
            if not alias:
                continue
            for i, ln in enumerate(lines, start=1):
                # 豁免 §二 角色定义表本身
                if sec2_start_line < i - 1 < sec2_end_line + 1:
                    continue
                # 豁免 变更日志 / 修订历史(历史字面引用,NB-RT-01)
                if _in_changelog(i):
                    continue
                if alias in ln:
                    # 二次过滤:确保不是规范字面的子串(如 "客户访客" ∈ "客户端访客")
                    # 简单策略:把规范字面替换为空再检查
                    ln_normalized = ln
                    for c in role_table.keys():
                        ln_normalized = ln_normalized.replace(c, "")
                    if alias in ln_normalized:
                        violations.append((i, alias, canonical))

    if violations:
        # 报告前 10 处,余略
        sample = violations[:10]
        msg = (
            f"[{item_id}] 命中 {len(violations)} 处禁用别名,"
            f"应替换为对应规范字面(§角色定义表 SSOT):"
        )
        for line_no, alias, canonical in sample:
            msg += f"\n  - line {line_no}:「{alias}」→ 应改为「{canonical}」"
        if len(violations) > 10:
            msg += f"\n  - ...(共 {len(violations)} 处,仅列前 10)"
        r.fail(msg)
    else:
        total_aliases = sum(len(v) for v in role_table.values())
        r.ok(
            f"{len(role_table)} 个角色 / {total_aliases} 个别名全文 0 命中,"
            f"角色命名一致性合规"
        )


# ── S1-07 / S2-06 / S3-06 共用 helper:从阶段 1 产物提取「已有模块」名单 ────────

def extract_already_have_modules(stage1_content: str) -> list[str]:
    """从阶段 1 产物 §四.2 排除功能表中提取「后续安排」列含「已有模块」字面值的行。

    返回每行「排除项」列的内容(已识别为现网已有模块的模块名)。

    Args:
        stage1_content: 阶段 1 产物(`需求分析_[产品名]_latest.md`)的完整内容

    Returns:
        已有模块名列表(可能为空,表示本项目未识别任何上位系统已有模块)
    """
    # 先定位 §四 功能边界 section
    sec4_match = re.search(
        r"^##\s*四[、\.]\s*功能边界", stage1_content, re.MULTILINE
    )
    if not sec4_match:
        return []
    sec4_start = sec4_match.end()
    # §四 截至下一个 ## 二级标题
    next_h2 = re.search(r"^##\s+", stage1_content[sec4_start:], re.MULTILINE)
    sec4_end = sec4_start + next_h2.start() if next_h2 else len(stage1_content)
    sec4_text = stage1_content[sec4_start:sec4_end]

    # 找 §4.2 子节
    sub42_match = re.search(
        r"^###\s*4\.2\s+明确排除的功能", sec4_text, re.MULTILINE
    )
    if not sub42_match:
        return []
    sub42_start = sub42_match.end()
    next_h3 = re.search(r"^###\s+", sec4_text[sub42_start:], re.MULTILINE)
    sub42_end = sub42_start + next_h3.start() if next_h3 else len(sec4_text)
    sub42_text = sec4_text[sub42_start:sub42_end]

    modules: list[str] = []
    for ln in sub42_text.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        if _is_separator_row(ln):
            continue
        cols = _parse_table_row(ln)
        if len(cols) != 3:
            continue
        # 跳过表头
        if cols[0] == "排除项":
            continue
        # 看「后续安排」列(第 3 列,index 2)
        if "已有模块" in cols[2]:
            modules.append(cols[0])
    return modules


# ── G 方案 G.5 UI 字面来源标注校验（共享逻辑）SSOT #54 ─────────────────────────
# 阶段 1/2/3 产物 UI 字面【来源：...】标注 WARN 兜底（[Recommended]，不阻断 EXIT=0）
# 关键词扫描 + ±2 行上下文【来源：...】标注核查；无标注 → WARN
# 配合 tmpl_需求分析/功能规划/产品定义.md「阶段分层粒度纪律」段
# 详 CLAUDE.md §调整意见自动记录规则第二步 G.1 + AI产品经理_Agent.md §三.5 G.2

import re as _re_ui

# UI 字面关键词候选清单（按 retro G.5 草案，可扩展）
# 设计纪律：避免高 FP 启发式（对齐 S4-28 v1 启发式 5/5 FP 教训）—
# 关键词仅捕"明显 UI 实现细节"字面，正常业务规则描述不命中
_UI_LITERAL_PATTERNS = [
    # UI 元素呈现细节（包含动词 + UI 对象组合）
    (r'(?:显示|展示)\S{0,12}(?:详单|预览|矩阵)', 'UI 展示细节'),
    (r'弹窗\S{0,12}(?:排版|布局|尺寸)', '弹窗排版细节'),
    (r'(?:文案|按钮文字)\S{0,12}(?:字号|大小|加粗)', '文案视觉细节'),
    (r'颜色\s*[:：]\s*#?[\dA-Fa-f]{3,6}', '颜色 hex 字面'),
    (r'(?:按钮|图标)\S{0,12}(?:右上|左下|顶部|底部)\s*角?', '按钮位置细节'),
    (r'(?:右上|左下|左上|右下)\S{0,12}(?:角|位置)', '位置坐标细节'),
    (r'(?:字号|font-size)\s*[:：]\s*\d+\s*(?:px|em)', '字号字面'),
    (r'(?:padding|margin)\s*[:：]\s*\d+\s*(?:px|em)', 'CSS 间距字面'),
    (r'toast\S{0,12}(?:显示|弹出)', 'toast 实现字面'),
]

# 【来源：...】标注正则（兼容全/半角 + 中英冒号 + 空格）
_SOURCE_ANNOTATION_RE = _re_ui.compile(r'【\s*来源\s*[:：]\s*[^】]+】')


def check_ui_source_annotation(content: str, stage_num: int, r) -> None:
    """G 方案 G.5 UI 字面来源标注校验（共享，阶段 1/2/3 调用）

    扫描产物中疑似 UI 实现细节字面（关键词清单），上下文 ±2 行无【来源：...】
    标注 → WARN [Recommended]，不阻断 EXIT=0。

    设计：零启发式 + 关键词清单严格控制 FP（避免 v1 启发式 5/5 FP 教训）。
    向后兼容：现有产物缺标注 → WARN 不阻断（产品总监已决策）。
    详 CLAUDE.md §调整意见自动记录规则第二步 + tmpl_*.md 阶段分层粒度纪律段。

    Args:
        content: 阶段产物 markdown 文本
        stage_num: 阶段编号（1/2/3）— 决定 S{N}-XX rule id
        r: Report 实例
    """
    rule_id_map = {1: 'S1-08', 2: 'S2-07', 3: 'S3-07'}
    rule_id = rule_id_map.get(stage_num, f'S{stage_num}-XX')
    r.section(f"{rule_id} UI 字面来源标注校验（G.5，SSOT #54，[Recommended] WARN）")

    lines = content.split('\n')
    hits: list[tuple[int, str, str, str]] = []  # (line_no, matched_literal, category, line_text)

    for i, line in enumerate(lines):
        line_no = i + 1
        for pattern, category in _UI_LITERAL_PATTERNS:
            for m in _re_ui.finditer(pattern, line):
                # 上下文 ±2 行扫描【来源：...】标注
                ctx_start = max(0, i - 2)
                ctx_end = min(len(lines), i + 3)
                ctx = '\n'.join(lines[ctx_start:ctx_end])
                if _SOURCE_ANNOTATION_RE.search(ctx):
                    continue  # 已有【来源】标注 → 合法承载，跳过
                # 无标注 → WARN
                literal = m.group(0)
                hits.append((line_no, literal, category, line.strip()[:120]))

    if not hits:
        r.ok(f"未发现 UI 字面无【来源】标注（{rule_id} PASS）")
        return

    # 去重（同行同字面多次命中只报一次）
    seen = set()
    unique_hits = []
    for h in hits:
        key = (h[0], h[1])
        if key not in seen:
            seen.add(key)
            unique_hits.append(h)

    msg_lines = [
        f"发现 {len(unique_hits)} 处 UI 字面无【来源：...】标注（{rule_id}）："
    ]
    for line_no, literal, category, ctx in unique_hits[:10]:
        msg_lines.append(
            f"  L{line_no} [{category}]: '{literal}' | 行: {ctx}"
        )
    if len(unique_hits) > 10:
        msg_lines.append(f"  ...（共 {len(unique_hits)} 处，仅显示前 10 条）")
    msg_lines.append(
        "修复方向（G 方案 G.2 三分类）：\n"
        "  ① 客户原始诉求 UI（合法承载）→ 加【来源：产品总监诉求/客户访谈/issue #N】标注\n"
        "  ② PM 推导粒度污染（违规承载）→ 清回业务粒度，删 UI 细节，留业务语义\n"
        "  ③ 未标注/模糊 → 评估归类后按 ①/② 处理 + 补全来源标注\n"
        "详 tmpl_需求分析/功能规划/产品定义.md「阶段分层粒度纪律」+ CLAUDE.md §调整意见自动记录规则第二步 G.1"
    )
    r.warn('\n'.join(msg_lines))
