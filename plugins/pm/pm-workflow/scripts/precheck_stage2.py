#!/usr/bin/env python3
"""
precheck_stage2.py — 阶段二（功能规划）自审前置机械检查脚本

用法：
    python pm-workflow/scripts/precheck_stage2.py [产物路径]

    产物路径默认按下序解析：
      1. 命令行参数 1 = 显式路径
      2. outputs/ 下匹配 `功能规划_*_latest.md` 的唯一文件
      3. 若无法解析 → 错误退出

作用：
    在 PM 自审清单的「机械检查前置」步骤运行，机械校验阶段二产物
    （outputs/功能规划_[产品名]_latest.md）是否满足模板硬约束：

      A. 章节存在性（tmpl_功能规划.md §一 ~ §五 + 变更记录）
      B. 表格列校验（§一 模块总览 4 列 / §一 子功能表 4 列 / §3.2 模块依赖 3 列
                     / §3.3 核心页面 5 列 / §四.4.1 5 列 / §四.4.2 5 列）
      C. [Must] 段非空（模块总览至少 1 行 / §二 至少 1 个 mermaid 块 / 子功能编号格式 MN-XX）
      D. 格式约束（模块编号 `M` + 数字 / 子功能编号 `MN-XX` / mermaid 类型 flowchart/sequence/state）

    SSOT 主从关系：模板（pm-workflow/rules/tmpl_功能规划.md）是真源，
    本脚本是机械兜底（`pm-workflow/rules/ssot_anchors.md` #27）。
    模板调整后须同步本脚本规则；本脚本不得反向倒逼模板。

    SSOT 元规范：本脚本是 prd_expression_standard.md §零 元规范
    "零猜测实现粒度"原则的阶段二机械化实现——让不同 PM 用同一模板产出格式相同的章节。

退出码：
    0  — 全部通过（可能含 WARN），可进入 PM 自审后续清单项
    1  — 存在 FAIL，禁止继续自审，PM 须按错误清单整改
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pm_paths import FRAMEWORK_ROOT, PROJECT_ROOT
from strip_inline_change_markers import warn_inline_markers  # SSOT #79 跨阶段内联标记检测（单源）
from precheck_common import (
    check_role_naming_consistency,
    extract_role_table,
    check_archive_sync,
    check_version_changelog,
    extract_already_have_modules,
)

OUTPUT_DIR = PROJECT_ROOT / "outputs"


# ── 报告收集器（同 precheck_stage4.py 风格）────────────────────────────────────

class Report:
    def __init__(self) -> None:
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
            print(f"\n[BLOCK] 存在 {len(self.errors)} 项错误，禁止继续 PM 自审。")
            print("请 PM 按以下清单整改后重跑 precheck_stage2.py：")
            for i, e in enumerate(self.errors, 1):
                print(f"  {i}. {e}")
            return 1
        if self.warnings:
            print(f"\n[PASS-W] 通过，但存在 {len(self.warnings)} 项警告，自审时请一并确认。")
        else:
            print("\n[PASS] 阶段二机械检查通过，可继续 PM 自审。")
        return 0


# ── 占位字面值识别 ─────────────────────────────────────────────────────────────

PLACEHOLDER_PATTERNS = [
    re.compile(r"<!--\s*待补充\s*-->"),
    re.compile(r"\[例[:：]"),
    re.compile(r"待定"),
]


def has_placeholder(text: str) -> bool:
    if not text or not text.strip():
        return True
    for pat in PLACEHOLDER_PATTERNS:
        if pat.search(text):
            return True
    stripped = text.strip()
    if stripped.startswith("【") and stripped.endswith("】") and stripped.count("【") <= 2:
        return True
    return False


def section_text(content: str, header_re: re.Pattern, end_re: re.Pattern | None = None) -> str:
    m = header_re.search(content)
    if not m:
        return ""
    start = m.end()
    if end_re is not None:
        end_m = end_re.search(content, start)
        end = end_m.start() if end_m else len(content)
    else:
        end_m = re.compile(r"^##\s", re.MULTILINE).search(content, start)
        end = end_m.start() if end_m else len(content)
    return content[start:end]


# ── A. 章节存在性 ──────────────────────────────────────────────────────────────

REQUIRED_SECTIONS = [
    ("§一 功能模块清单", re.compile(r"^##\s*一[、\.]\s*功能模块清单", re.MULTILINE)),
    ("§二 业务流程图", re.compile(r"^##\s*二[、\.]\s*业务流程图", re.MULTILINE)),
    ("§三 产品架构", re.compile(r"^##\s*三[、\.]\s*产品架构", re.MULTILINE)),
    ("§四 问题清单", re.compile(r"^##\s*四[、\.]\s*问题清单", re.MULTILINE)),
    ("§五 自审检查清单", re.compile(r"^##\s*五[、\.]\s*自审检查清单", re.MULTILINE)),
    ("§六 变更记录", re.compile(r"^##\s*六[、\.]\s*变更记录", re.MULTILINE)),
]


def check_sections(content: str, r: Report) -> dict[str, re.Match | None]:
    r.section("章节存在性（tmpl_功能规划.md 二级标题）")
    matches: dict[str, re.Match | None] = {}
    all_ok = True
    for name, pat in REQUIRED_SECTIONS:
        m = pat.search(content)
        matches[name] = m
        if m is None:
            label = name.lstrip("§").strip()
            num_part, _, rest = label.partition(" ")
            expected = f"## {num_part}、{rest}".strip()
            r.fail(f"[章节] 缺失：{name}；期望格式：`{expected}`")
            all_ok = False
    if all_ok:
        r.ok(f"全部 {len(REQUIRED_SECTIONS)} 个二级章节齐全")
    return matches


# ── B. §一 功能模块清单 ────────────────────────────────────────────────────────

MODULE_ID_RE = re.compile(r"^M\d+$")
SUBFUNC_ID_RE = re.compile(r"^M\d+-\d+$")


def check_module_list(content: str, r: Report) -> None:
    r.section("§一 功能模块清单：模块总览 + 子功能表")
    sec_re = re.compile(r"^##\s*一[、\.]\s*功能模块清单", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§一] 无法提取本节内容")
        return

    # 模块总览表（4 列：模块编号 / 模块名称 / 优先级 / 说明）
    expected_overview = ["模块编号", "模块名称", "优先级", "说明"]
    table_headers = list(re.finditer(r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", sec_text, re.MULTILINE))
    overview_found = False
    overview_rows: list[list[str]] = []
    for h_m in table_headers:
        cols = [c.strip() for c in h_m.group(1).split("|")]
        if cols == expected_overview:
            overview_found = True
            # 提取该表行
            # h_m.end() 含表头行 + 分隔符行 + 数据首行的第一个 `|`，
            # 直接按行解析从 header 起的数据行更稳妥
            # 先回退到 header 行起点（h_m.start()），按行切，跳过前两行（header + separator）
            tail_lines = sec_text[h_m.start():].splitlines()
            body_lines = []
            for line in tail_lines[2:]:  # 跳 header + separator
                if line.strip().startswith("|"):
                    body_lines.append(line)
                else:
                    break
            tbl_body = "\n".join(body_lines)
            for line in tbl_body.splitlines():
                if line.strip().startswith("|"):
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    if len(cells) == 4 and cells[0] and not cells[0].startswith("-"):
                        overview_rows.append(cells)
            break

    if not overview_found:
        r.fail(
            f"[§一.模块总览] 表头错误或缺失；"
            f"期望：`| 模块编号 | 模块名称 | 优先级 | 说明 |` 4 列"
        )
        return

    # 检查模块编号格式
    real_modules = [row for row in overview_rows if not all(has_placeholder(c) for c in row)]
    if not real_modules:
        r.fail("[§一.模块总览] 表中所有行均为占位（如『M1』『M2』），期望：至少 1 行实际模块")
        return
    bad_ids = [row[0] for row in real_modules if not MODULE_ID_RE.match(row[0])]
    if bad_ids:
        r.fail(
            f"[§一.模块总览] 模块编号格式错误：{bad_ids}；期望：`M` + 数字（如 `M1` / `M01`）"
        )
        return
    # 优先级列须为 P0/P1/P2
    bad_prio = [row[2] for row in real_modules if row[2] not in ("P0", "P1", "P2")]
    if bad_prio:
        r.fail(
            f"[§一.模块总览] 优先级列值非法：{bad_prio}；期望：仅 `P0` / `P1` / `P2`"
        )
        return
    r.ok(f"§一.模块总览 表头正确（4 列）+ 编号格式合法（{len(real_modules)} 个模块）")

    # 子功能表：每个模块应有一张 4 列表（子功能编号 / 子功能名称 / 优先级 / 功能描述）
    expected_sub = ["子功能编号", "子功能名称", "优先级", "功能描述"]
    sub_tables_found = 0
    sub_func_ids: set[str] = set()
    duplicate_sub_ids: list[str] = []
    for h_m in table_headers:
        cols = [c.strip() for c in h_m.group(1).split("|")]
        if cols == expected_sub:
            sub_tables_found += 1
            # h_m.end() 含表头行 + 分隔符行 + 数据首行的第一个 `|`，
            # 直接按行解析从 header 起的数据行更稳妥
            # 先回退到 header 行起点（h_m.start()），按行切，跳过前两行（header + separator）
            tail_lines = sec_text[h_m.start():].splitlines()
            body_lines = []
            for line in tail_lines[2:]:  # 跳 header + separator
                if line.strip().startswith("|"):
                    body_lines.append(line)
                else:
                    break
            tbl_body = "\n".join(body_lines)
            for line in tbl_body.splitlines():
                if line.strip().startswith("|"):
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    if len(cells) >= 4 and cells[0] and not cells[0].startswith("-"):
                        if has_placeholder(cells[0]):
                            continue
                        if not SUBFUNC_ID_RE.match(cells[0]):
                            r.fail(
                                f"[§一.子功能表] 子功能编号格式错误：{cells[0]!r}；"
                                f"期望：`MN-XX`（如 `M1-01`）"
                            )
                            continue
                        if cells[0] in sub_func_ids:
                            duplicate_sub_ids.append(cells[0])
                        sub_func_ids.add(cells[0])

    if sub_tables_found == 0:
        r.fail(
            f"[§一.子功能表] 未找到任何符合 4 列格式的子功能表；"
            f"期望：每个模块下一张 `| 子功能编号 | 子功能名称 | 优先级 | 功能描述 |` 4 列表"
        )
    elif sub_tables_found < len(real_modules):
        r.warn(
            f"[§一.子功能表] 子功能表数量 {sub_tables_found} 少于模块数 {len(real_modules)}；"
            f"期望：每个模块独立 1 张表（简单模块也应保留表头）"
        )
    else:
        r.ok(
            f"§一.子功能表 表头正确（4 列），共 {sub_tables_found} 张，"
            f"含 {len(sub_func_ids)} 个子功能"
        )

    if duplicate_sub_ids:
        r.fail(
            f"[§一.子功能表] 子功能编号重复：{duplicate_sub_ids}；"
            f"期望：所有子功能编号全局唯一"
        )


# ── B.5 S2-06 现网已有模块承继约束(§一 不得规划已有模块) ─────────────────────

def check_no_overlap_with_already_have(
    content: str, r: Report, stage1_path: Path
) -> None:
    """S2-06: 阶段 2 §一 模块清单不得包含阶段 1 §四.2 标注的现网已有模块。

    校验逻辑:
        1. Read 阶段 1 产物,提取已有模块名集合
        2. 提取阶段 2 §一 模块总览表的模块名集合(第 2 列「模块名称」)
        3. 校验:两集合无重叠(精确相等 OR 任一方向子串)

    SSOT 真源: rule_hard_constraints.md S2-06
    """
    r.section("S2-06 现网已有模块承继约束(§一 不得规划已有模块)")

    if not stage1_path.exists():
        r.warn(
            f"[S2-06] 阶段 1 产物不存在: {stage1_path},无法核查承继约束;"
            f"请先完成阶段 1"
        )
        return

    stage1_content = stage1_path.read_text(encoding="utf-8")
    already_modules = extract_already_have_modules(stage1_content)

    if not already_modules:
        r.ok("阶段 1 §四.2 未标注「已有模块」,跳过承继约束校验")
        return

    r.ok(
        f"阶段 1 标注了 {len(already_modules)} 个已有模块: {', '.join(already_modules)}"
    )

    sec_re = re.compile(r"^##\s*一[、\.]\s*功能模块清单", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[S2-06] §一 功能模块清单章节缺失,无法核查")
        return

    expected_overview = ["模块编号", "模块名称", "优先级", "说明"]
    stage2_modules: list[str] = []
    table_headers = list(
        re.finditer(r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", sec_text, re.MULTILINE)
    )
    for h_m in table_headers:
        cols = [c.strip() for c in h_m.group(1).split("|")]
        if cols == expected_overview:
            tail_lines = sec_text[h_m.start():].splitlines()
            for line in tail_lines[2:]:
                if not line.strip().startswith("|"):
                    break
                cells = [
                    c.strip() for c in line.strip().strip("|").split("|")
                ]
                if (
                    len(cells) == 4
                    and cells[1]
                    and not has_placeholder(cells[1])
                ):
                    stage2_modules.append(cells[1])
            break

    overlaps: list[tuple[str, str]] = []
    for m2 in stage2_modules:
        for m1 in already_modules:
            if m1 in m2 or m2 in m1:
                overlaps.append((m2, m1))
                break

    if overlaps:
        details = "; ".join(f"`{m2}` ↔ 阶段1 `{m1}`" for m2, m1 in overlaps)
        r.fail(
            f"[S2-06] 阶段 2 §一 模块清单出现已有模块(违反承继约束): {details};"
            f"SSOT: rule_hard_constraints.md S2-06"
        )
    else:
        r.ok(
            f"阶段 2 §一 模块清单({len(stage2_modules)} 个模块)"
            f"与阶段 1 已有模块({len(already_modules)} 个)无重叠"
        )


# ── C. §二 业务流程图：mermaid 块 ─────────────────────────────────────────────

MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
MERMAID_TYPE_RE = re.compile(
    r"^\s*(flowchart|graph|sequenceDiagram|stateDiagram(?:-v2)?)\b",
    re.MULTILINE,
)


def check_flowcharts(content: str, r: Report) -> None:
    r.section("§二 业务流程图：Mermaid 块")
    sec_re = re.compile(r"^##\s*二[、\.]\s*业务流程图", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§二] 无法提取本节内容")
        return

    blocks = MERMAID_BLOCK_RE.findall(sec_text)
    if not blocks:
        r.fail(
            "[§二.业务流程图] 未找到任何 ```mermaid``` 代码块；"
            "期望：§2.1 主流程总览必须存在 1 个 mermaid 块（最少要求）"
        )
        return

    # 校验图类型
    valid_types_count = 0
    type_summary: dict[str, int] = {}
    for blk in blocks:
        m = MERMAID_TYPE_RE.search(blk)
        if not m:
            r.fail(
                f"[§二.业务流程图] 一个 mermaid 块未声明合法图类型；"
                f"期望首行：`flowchart TD/LR` / `sequenceDiagram` / `stateDiagram-v2`"
            )
            continue
        valid_types_count += 1
        t = m.group(1)
        type_summary[t] = type_summary.get(t, 0) + 1

    # §2.1 主流程总览必须存在
    if not re.search(r"^###\s*2\.1\s+主流程总览", sec_text, re.MULTILINE):
        r.fail("[§二.2.1] 缺失三级标题；期望：`### 2.1 主流程总览（必选）`")

    if valid_types_count > 0:
        r.ok(
            f"§二.业务流程图 含 {len(blocks)} 个 mermaid 块（类型分布：{type_summary}）"
        )


# ── D. §三 产品架构：3.1 / 3.2 / 3.3 ─────────────────────────────────────────

def check_architecture(content: str, r: Report) -> None:
    r.section("§三 产品架构：3.1 页面架构 / 3.2 模块依赖 / 3.3 核心页面")
    sec_re = re.compile(r"^##\s*三[、\.]\s*产品架构", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§三] 无法提取本节内容")
        return

    if not re.search(r"^###\s*3\.1\s+页面架构", sec_text, re.MULTILINE):
        r.fail("[§三.3.1] 缺失三级标题；期望：`### 3.1 页面架构`")
    else:
        # 至少含一段代码块（ASCII 树）
        if not re.search(r"```[\s\S]+?```", sec_text):
            r.warn(
                "[§三.3.1] 未发现 ASCII 树形结构代码块（``` ... ```）；"
                "期望：用代码块包裹页面层级树"
            )
        else:
            r.ok("§三.3.1 页面架构 存在")

    if not re.search(r"^###\s*3\.2\s+模块依赖关系", sec_text, re.MULTILINE):
        r.fail("[§三.3.2] 缺失三级标题；期望：`### 3.2 模块依赖关系`")
    else:
        # 表头：模块 / 依赖于 / 说明
        expected_dep = ["模块", "依赖于", "说明"]
        table_headers = re.findall(r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", sec_text, re.MULTILINE)
        if not any([c.strip() for c in raw.split("|")] == expected_dep for raw in table_headers):
            r.fail(
                f"[§三.3.2] 模块依赖表列名错误或缺失；"
                f"期望：`| 模块 | 依赖于 | 说明 |` 3 列"
            )
        else:
            r.ok("§三.3.2 模块依赖关系表 列名正确（3 列）")

    if not re.search(r"^###\s*3\.3\s+核心页面说明", sec_text, re.MULTILINE):
        r.fail("[§三.3.3] 缺失三级标题；期望：`### 3.3 核心页面说明`")
    else:
        # 表头：页面名称 / 访问者 / 关键交互 / 端 / 对客
        expected_page = ["页面名称", "访问者", "关键交互", "端", "对客"]
        table_headers = re.findall(r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", sec_text, re.MULTILINE)
        if not any([c.strip() for c in raw.split("|")] == expected_page for raw in table_headers):
            r.fail(
                f"[§三.3.3] 核心页面说明表列名错误或缺失；"
                f"期望：`| 页面名称 | 访问者 | 关键交互 | 端 | 对客 |` 5 列"
            )
        else:
            r.ok("§三.3.3 核心页面说明表 列名正确（5 列）")


# ── E. §四 问题清单：4.1 / 4.2 ─────────────────────────────────────────────────

def check_issue_lists(content: str, r: Report) -> None:
    r.section("§四 问题清单：4.1 阻塞 / 4.2 非阻塞")
    sec_re = re.compile(r"^##\s*四[、\.]\s*问题清单", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§四] 无法提取本节内容")
        return

    if not re.search(r"^###\s*4\.1\s+阻塞性问题", sec_text, re.MULTILINE):
        r.fail("[§四.4.1] 缺失子节标题；期望：`### 4.1 阻塞性问题`")
    if not re.search(r"^###\s*4\.2\s+非阻塞性问题", sec_text, re.MULTILINE):
        r.fail("[§四.4.2] 缺失子节标题；期望：`### 4.2 非阻塞性问题`")

    expected_41 = ["编号", "问题描述", "影响范围", "待确认内容", "状态"]
    # 列名为中性词「处理方式」——兼容 ⏳ 暂定态（PM 提交前）与 ✅ 已决策态（产品总监终审后）两态语义
    expected_42 = ["编号", "问题描述", "处理方式", "待确认内容", "状态"]
    table_headers = re.findall(r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", sec_text, re.MULTILINE)
    found_41 = found_42 = False
    for raw_h in table_headers:
        cols = [c.strip() for c in raw_h.split("|")]
        if cols == expected_41:
            found_41 = True
        elif cols == expected_42:
            found_42 = True
    if not found_41:
        r.fail(
            f"[§四.4.1] 阻塞性问题表列名错误或缺失；"
            f"期望 5 列：`| 编号 | 问题描述 | 影响范围 | 待确认内容 | 状态 |`"
        )
    else:
        r.ok("§四.4.1 阻塞性问题表 列名正确（5 列）")
    if not found_42:
        r.fail(
            f"[§四.4.2] 非阻塞性问题表列名错误或缺失；"
            f"期望 5 列：`| 编号 | 问题描述 | 处理方式 | 待确认内容 | 状态 |`"
        )
    else:
        r.ok("§四.4.2 非阻塞性问题表 列名正确（5 列）")


# ── F. PM 自审完成提交标记 ────────────────────────────────────────────────────

def check_submit_marker(content: str, r: Report) -> None:
    r.section("PM 自审完成提交标记")
    if "【✅ PM 自审完成，提交主管审核】" in content:
        r.ok("已含 PM 自审完成提交标记")
    else:
        r.warn(
            "[标记] 未发现 `【✅ PM 自审完成，提交主管审核】`；"
            "期望：自审通过后于文末（§五 自审清单与 §六 变更记录之间）写入此标记"
        )


def check_no_inline_change_markers(content: str, r: Report) -> None:
    """SSOT #79 — 阶段 2 功能规划正文禁内联变更标记（WARN，跨阶段前移防线）。
    变更历史走变更记录表 + git；查版本差异用 `git diff`。检测 + 文案单源自 warn_inline_markers。"""
    r.section("内联变更标记纪律（SSOT #79，跨阶段前移；WARN）")
    warn_inline_markers("功能规划", content, r)


# ── 主入口 ────────────────────────────────────────────────────────────────────

def resolve_target_path(argv: list[str]) -> Path:
    if len(argv) > 1:
        p = Path(argv[1])
        if not p.is_absolute():
            p = (PROJECT_ROOT / p).resolve()
        return p
    if not OUTPUT_DIR.exists():
        print(
            f"[ERROR] 默认目录不存在：{OUTPUT_DIR}\n"
            f"用法：python pm-workflow/scripts/precheck_stage2.py [产物路径]",
            file=sys.stderr,
        )
        sys.exit(1)
    candidates = sorted(OUTPUT_DIR.glob("功能规划_*_latest.md"))
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) == 0:
        print(
            f"[ERROR] {OUTPUT_DIR} 下未找到 `功能规划_*_latest.md`；"
            f"请显式传入产物路径作为参数 1",
            file=sys.stderr,
        )
        sys.exit(1)
    print(
        f"[ERROR] {OUTPUT_DIR} 下存在多个 `功能规划_*_latest.md`，请显式传入产物路径作为参数 1：\n"
        + "\n".join(f"  - {c}" for c in candidates),
        file=sys.stderr,
    )
    sys.exit(1)


def _check_pre_commit_hook_installed() -> str | None:
    """检测 .git/hooks/pre-commit 是否已安装（指向仓库 hook 源）。
    返回 None = 已装/检查不适用；返回 str = WARN 信息。
    SSOT 真源：`pm-workflow/rules/agent_dispatch_protocol.md`「PM / Supervisor Agent 文件改动权限边界」第 5 条 / SSOT 双锚 #31。"""
    git_hook = PROJECT_ROOT / ".git" / "hooks" / "pre-commit"
    expected = FRAMEWORK_ROOT / "pm-workflow" / "scripts" / "hooks" / "pre-commit"
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


def main() -> None:
    hook_warn = _check_pre_commit_hook_installed()
    if hook_warn:
        print(f"[WARN] {hook_warn}\n", file=sys.stderr)

    target = resolve_target_path(sys.argv)
    if not target.exists():
        print(f"[ERROR] 产物文件不存在：{target}", file=sys.stderr)
        sys.exit(1)

    print(f"产物：{target}")
    content = target.read_text(encoding="utf-8")

    r = Report()
    matches = check_sections(content, r)
    if matches.get("§一 功能模块清单"):
        check_module_list(content, r)
    if matches.get("§二 业务流程图"):
        check_flowcharts(content, r)
    if matches.get("§三 产品架构"):
        check_architecture(content, r)
    if matches.get("§四 问题清单"):
        check_issue_lists(content, r)
    check_submit_marker(content, r)
    # SSOT #79 跨阶段前移 — 正文禁内联变更标记（WARN）
    check_no_inline_change_markers(content, r)

    # S2-06 现网已有模块承继约束(读阶段 1 产物核查)
    # 推导 product 名:`功能规划_[产品名]_latest` → `[产品名]`
    archive_prefix = target.stem.removesuffix("_latest")
    if matches.get("§一 功能模块清单") and archive_prefix.startswith("功能规划_"):
        product_name = archive_prefix[len("功能规划_"):]
        stage1_path = OUTPUT_DIR / f"需求分析_{product_name}_latest.md"
        check_no_overlap_with_already_have(content, r, stage1_path)

    # G-01 / G-02 4 阶段通用硬规则(rule_hard_constraints.md)
    check_archive_sync(target, r, "阶段2 功能规划", archive_prefix, PROJECT_ROOT)
    check_version_changelog(content, r, "阶段2 功能规划")

    # S2-07 UI 字面来源标注校验（G 方案 G.5，SSOT #54，[Recommended] WARN 不阻断）
    from precheck_common import check_ui_source_annotation
    check_ui_source_annotation(content, 2, r)

    # S2-NAMING-01 角色命名一致性(建议 7 / issue # 3 复盘根因 G)
    if archive_prefix.startswith("功能规划_"):
        product_name_for_naming = archive_prefix[len("功能规划_"):]
        stage1_naming_path = OUTPUT_DIR / f"需求分析_{product_name_for_naming}_latest.md"
        if stage1_naming_path.exists():
            role_table = extract_role_table(
                stage1_naming_path.read_text(encoding="utf-8")
            )
            check_role_naming_consistency(
                content, role_table or {}, r, "阶段2 功能规划", "S2-NAMING-01"
            )
        else:
            r.section("S2-NAMING-01 角色命名一致性(建议 7 / issue # 3 复盘)")
            r.warn(
                f"[S2-NAMING-01] 阶段 1 产物不存在: {stage1_naming_path},"
                f"无法启用命名校验"
            )

    sys.exit(r.summary())


if __name__ == "__main__":
    main()
