#!/usr/bin/env python3
"""
precheck_stage1.py — 阶段一（需求分析）自审前置机械检查脚本

用法：
    python pm-workflow/scripts/precheck_stage1.py [产物路径]

    产物路径默认按下序解析：
      1. 命令行参数 1 = 显式路径
      2. outputs/ 下匹配 `需求分析_*_latest.md` 的唯一文件
      3. 若无法解析 → 错误退出

作用：
    在 PM 自审清单的「机械检查前置」步骤运行，机械校验阶段一产物
    （outputs/需求分析_[产品名]_latest.md）是否满足模板硬约束：

      A. 章节存在性（tmpl_需求分析.md §一 ~ §六 + 自审清单 + 变更记录全部存在）
      B. 表格列校验（§三 边缘情况表 3 列 / §四.1 + §四.2 各 3 列 / §六.1 + §六.2 各 5 列）
         注:§二 角色定义表(6 列)由 S1-NAMING-01 校验,职责独立,不在 B 段
      C. [Must] 段非空（三固定问题——背景/目标/成功标志；五约束节；6.1/6.2 子节）
      D. 格式约束（§一 三个固定问题标题、§五 三个固定子节标题、占位字面值未保留）

    SSOT 主从关系：模板（pm-workflow/rules/tmpl_需求分析.md）是真源，
    本脚本是机械兜底（`pm-workflow/rules/ssot_anchors.md` #26）。
    模板调整后须同步本脚本规则；本脚本不得反向倒逼模板。

    SSOT 元规范：本脚本是 prd_expression_standard.md §零 元规范
    "零猜测实现粒度"原则的阶段一机械化实现——让不同 PM 用同一模板产出格式相同的章节。

退出码：
    0  — 全部通过（可能含 WARN），可进入 PM 自审后续清单项
    1  — 存在 FAIL，禁止继续自审，PM 须按错误清单整改
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from strip_inline_change_markers import warn_inline_markers  # SSOT #79 跨阶段内联标记检测（单源）
from precheck_common import (
    check_archive_sync,
    check_role_naming_consistency,
    check_version_changelog,
    extract_role_table,
    extract_already_have_modules,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "outputs"


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
            print("请 PM 按以下清单整改后重跑 precheck_stage1.py：")
            for i, e in enumerate(self.errors, 1):
                print(f"  {i}. {e}")
            return 1
        if self.warnings:
            print(f"\n[PASS-W] 通过，但存在 {len(self.warnings)} 项警告，自审时请一并确认。")
        else:
            print("\n[PASS] 阶段一机械检查通过，可继续 PM 自审。")
        return 0


# ── 占位字面值识别（模板未填的标记）───────────────────────────────────────────

PLACEHOLDER_PATTERNS = [
    re.compile(r"<!--\s*待补充\s*-->"),
    re.compile(r"<!--\s*待填\s*-->"),
    re.compile(r"\[例[:：]"),
    re.compile(r"【填写[^】]*】"),
    re.compile(r"【.*?示例[:：][^】]*】"),
    re.compile(r"待定"),
]


def has_placeholder(text: str) -> bool:
    """判定一段文本是否仍为模板占位（未被 PM 实际填写）。"""
    if not text or not text.strip():
        return True
    for pat in PLACEHOLDER_PATTERNS:
        if pat.search(text):
            return True
    # 纯 【XXX】 内容（如「【目标一：示例：xxx】」）— 整段被 【】 包裹
    stripped = text.strip()
    if stripped.startswith("【") and stripped.endswith("】") and stripped.count("【") <= 2:
        return True
    return False


def section_text(content: str, header_re: re.Pattern, end_re: re.Pattern | None = None) -> str:
    """提取从某个二级/三级标题开始到下一个同级或更高级标题之间的文本。"""
    m = header_re.search(content)
    if not m:
        return ""
    start = m.end()
    if end_re is not None:
        end_m = end_re.search(content, start)
        end = end_m.start() if end_m else len(content)
    else:
        # 默认到下一个二级标题
        end_m = re.compile(r"^##\s", re.MULTILINE).search(content, start)
        end = end_m.start() if end_m else len(content)
    return content[start:end]


# ── A. 章节存在性 ──────────────────────────────────────────────────────────────

REQUIRED_SECTIONS = [
    ("§一 需求概述", re.compile(r"^##\s*一[、\.]\s*需求概述", re.MULTILINE)),
    ("§二 用户角色与权限", re.compile(r"^##\s*二[、\.]\s*用户角色与权限", re.MULTILINE)),
    ("§三 核心业务场景", re.compile(r"^##\s*三[、\.]\s*核心业务场景", re.MULTILINE)),
    ("§四 功能边界", re.compile(r"^##\s*四[、\.]\s*功能边界", re.MULTILINE)),
    ("§五 约束条件", re.compile(r"^##\s*五[、\.]\s*约束条件", re.MULTILINE)),
    ("§六 问题清单", re.compile(r"^##\s*六[、\.]\s*问题清单", re.MULTILINE)),
    ("§七 自审检查清单", re.compile(r"^##\s*七[、\.]\s*自审检查清单", re.MULTILINE)),
    ("§八 变更记录", re.compile(r"^##\s*八[、\.]\s*变更记录", re.MULTILINE)),
]


def check_sections(content: str, r: Report) -> dict[str, re.Match | None]:
    r.section("章节存在性（tmpl_需求分析.md 二级标题）")
    matches: dict[str, re.Match | None] = {}
    all_ok = True
    for name, pat in REQUIRED_SECTIONS:
        m = pat.search(content)
        matches[name] = m
        if m is None:
            # 把 "§一 需求概述" 转换为期望的二级标题文本 "一、需求概述"
            label = name.lstrip("§").strip()
            num_part, _, rest = label.partition(" ")
            expected = f"## {num_part}、{rest}".strip()
            r.fail(f"[章节] 缺失：{name}；期望格式：`{expected}`")
            all_ok = False
    if all_ok:
        r.ok(f"全部 {len(REQUIRED_SECTIONS)} 个二级章节齐全")
    return matches


# ── B. §一 需求概述：三个固定问题 ─────────────────────────────────────────────

OVERVIEW_QUESTIONS = [
    ("需求背景", re.compile(r"\*\*需求背景\*\*", re.MULTILINE)),
    ("业务目标", re.compile(r"\*\*业务目标\*\*", re.MULTILINE)),
    ("成功标志", re.compile(r"\*\*成功标志\*\*", re.MULTILINE)),
]

# T2-1（issue 2026-05-05_2243 复盘根因 3）：产品边界与系统集成 5 字段
PRODUCT_BOUNDARY_FIELDS = [
    ("系统形态", re.compile(r"-\s*\*\*系统形态\*\*", re.MULTILINE)),
    ("上级模块", re.compile(r"-\s*\*\*上级模块\*\*", re.MULTILINE)),
    ("进入入口", re.compile(r"-\s*\*\*进入入口\*\*", re.MULTILINE)),
    ("退出/返回", re.compile(r"-\s*\*\*退出/返回\*\*", re.MULTILINE)),
    ("跨系统数据流", re.compile(r"-\s*\*\*跨系统数据流\*\*", re.MULTILINE)),
]


def check_overview(content: str, r: Report) -> None:
    r.section("§一 需求概述：三个固定问题")
    sec_re = re.compile(r"^##\s*一[、\.]\s*需求概述", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§一.需求概述] 无法提取本节内容（章节缺失）")
        return

    for name, pat in OVERVIEW_QUESTIONS:
        if not pat.search(sec_text):
            r.fail(
                f"[§一.需求概述] 缺少必填子项：『{name}』；"
                f"期望格式：`**{name}**`（粗体小标题，独立成行）"
            )
            continue
        # 提取该子项内容（到下一个粗体小标题或本节结尾）
        sub_pat = re.compile(
            rf"\*\*{re.escape(name)}\*\*\s*\n+(.*?)(?=\n\*\*\S|\Z)",
            re.DOTALL,
        )
        sub_m = sub_pat.search(sec_text)
        body = sub_m.group(1).strip() if sub_m else ""
        # 业务目标允许列表项格式
        if name == "业务目标":
            # 至少应有 1 个数字列表项
            if not re.search(r"^\s*\d+\.\s+\S", body, re.MULTILINE):
                r.fail(
                    f"[§一.需求概述.业务目标] 内容为空或缺少编号列表；"
                    f"期望格式：`1. 【动词开头的业务目标】` 至少 1 行"
                )
                continue
            # 提取每行检查占位
            placeholder_lines = [
                line for line in re.findall(r"^\s*\d+\.\s+(.*)$", body, re.MULTILINE)
                if has_placeholder(line)
            ]
            if placeholder_lines:
                r.fail(
                    f"[§一.需求概述.业务目标] 含 {len(placeholder_lines)} 行占位文本未填实"
                    f"（如『【目标一：示例：xxx】』）；期望：每行替换为实际业务目标"
                )
                continue
        else:
            if has_placeholder(body):
                r.fail(
                    f"[§一.需求概述.{name}] 内容为占位或空；"
                    f"期望：移除 `【...】` / `[例：...]` / `<!-- 待... -->` 占位，填入实际内容"
                )
                continue
        r.ok(f"§一.{name} 已填写")

    # T2-1：产品边界与系统集成 5 字段（issue 2026-05-05_2243 复盘根因 3）
    boundary_section_re = re.compile(
        r"\*\*`?\[Must\]`?\s*产品边界与系统集成\*\*", re.MULTILINE
    )
    if not boundary_section_re.search(sec_text):
        r.fail(
            "[§一.产品边界] 缺少必填段：`**[Must]` 产品边界与系统集成 **`；"
            "期望：在「成功标志」段后追加,含 5 个字段（系统形态/上级模块/进入入口/退出·返回/跨系统数据流）"
        )
        return
    boundary_match = boundary_section_re.search(sec_text)
    boundary_text = sec_text[boundary_match.end():] if boundary_match else ""
    for fname, fpat in PRODUCT_BOUNDARY_FIELDS:
        if not fpat.search(boundary_text):
            r.fail(
                f"[§一.产品边界.{fname}] 缺少必填字段；"
                f"期望格式：`- **{fname}**：[填写内容]`"
            )
            continue
        # 字段值占位识别（独立行 + 简易抓取）
        field_line_re = re.compile(
            rf"-\s*\*\*{re.escape(fname)}\*\*[^\n]*", re.MULTILINE
        )
        line_m = field_line_re.search(boundary_text)
        line_body = line_m.group(0) if line_m else ""
        # "上级模块"允许填"无"（独立系统场景）；"跨系统数据流"为条件必填,允许填"无"
        if fname in ("上级模块", "跨系统数据流") and re.search(r"[填无]\s*$|无$", line_body):
            r.ok(f"§一.产品边界.{fname} 已填写（豁免值「无」）")
            continue
        if has_placeholder(line_body.split("：", 1)[1] if "：" in line_body else line_body):
            r.fail(
                f"[§一.产品边界.{fname}] 内容为占位或空；"
                f"期望：移除 `【例：...】` 占位填入实际内容（独立系统时'上级模块'可填'无'）"
            )
            continue
        r.ok(f"§一.产品边界.{fname} 已填写")


# ── C. §二 用户角色与权限：表结构校验已由 S1-NAMING-01 接管 ───────────────────
# (移除原 check_role_table + extract_first_table 冗余 4 列校验,与建议 7 落地的
#  6 列 §二 角色定义表结构冲突;S1-NAMING-01 在 main() 中独立调用,职责清晰)


# ── D. §三 核心业务场景：每个场景的边缘情况表 3 列 ────────────────────────────

def check_scenarios(content: str, r: Report) -> None:
    r.section("§三 核心业务场景：场景结构 + 边缘情况表 3 列")
    sec_re = re.compile(r"^##\s*三[、\.]\s*核心业务场景", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§三.核心业务场景] 无法提取本节内容")
        return

    # 至少含一个场景（### 场景X）
    scenario_re = re.compile(r"^###\s*场景[一二三四五六七八九十\d]+", re.MULTILINE)
    scenarios = scenario_re.findall(sec_text)
    if not scenarios:
        r.fail(
            "[§三.场景] 未找到任何场景；期望：至少 1 个三级标题 `### 场景一：...`"
        )
        return
    r.ok(f"§三.场景 含 {len(scenarios)} 个场景")

    # 每个场景应含「触发条件」「主流程」「边缘情况」3 个粗体小标题
    must_subsections = ["触发条件", "主流程", "边缘情况"]
    missing_count = 0
    for sub in must_subsections:
        sub_pat = re.compile(rf"\*\*{re.escape(sub)}\*\*", re.MULTILINE)
        sub_count = len(sub_pat.findall(sec_text))
        if sub_count < len(scenarios):
            r.fail(
                f"[§三.场景] 子项『{sub}』出现 {sub_count} 次，少于场景数 {len(scenarios)}；"
                f"期望：每个场景独立含 `**{sub}**` 段"
            )
            missing_count += 1
    if missing_count == 0:
        r.ok(f"§三.场景 三个必填子项（触发条件/主流程/边缘情况）数量与场景数匹配")

    # 边缘情况表 3 列校验：扫描所有 markdown 表格，找列名为「边缘情况|触发条件|系统处理方式」者
    expected_edge_cols = ["边缘情况", "触发条件", "系统处理方式"]
    edge_table_count = 0
    table_headers = re.findall(r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", sec_text, re.MULTILINE)
    for raw_h in table_headers:
        cols = [c.strip() for c in raw_h.split("|")]
        if cols == expected_edge_cols:
            edge_table_count += 1
    if edge_table_count < len(scenarios):
        r.fail(
            f"[§三.边缘情况表] 仅找到 {edge_table_count} 张符合 3 列格式的表，少于场景数 {len(scenarios)}；"
            f"期望：每个场景独立 1 张表，列名严格为 `| 边缘情况 | 触发条件 | 系统处理方式 |`"
        )
    else:
        r.ok(f"§三.边缘情况表 列名正确（3 列），共 {edge_table_count} 张")


# ── E. §四 功能边界：4.1 / 4.2 两表 ─────────────────────────────────────────────

def check_boundaries(content: str, r: Report) -> None:
    r.section("§四 功能边界：4.1 包含 / 4.2 排除")
    sec_re = re.compile(r"^##\s*四[、\.]\s*功能边界", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§四.功能边界] 无法提取本节内容")
        return

    # 子节 4.1
    if not re.search(r"^###\s*4\.1\s+本次包含的功能", sec_text, re.MULTILINE):
        r.fail("[§四.4.1] 缺失三级标题；期望：`### 4.1 本次包含的功能`")
    # 子节 4.2
    if not re.search(r"^###\s*4\.2\s+明确排除的功能", sec_text, re.MULTILINE):
        r.fail("[§四.4.2] 缺失三级标题；期望：`### 4.2 明确排除的功能`")

    # 4.1 表头：功能模块 / 功能描述 / 备注
    table_headers = re.findall(r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", sec_text, re.MULTILINE)
    expected_41 = ["功能模块", "功能描述", "备注"]
    expected_42 = ["排除项", "排除原因", "后续安排"]
    found_41 = found_42 = False
    for raw_h in table_headers:
        cols = [c.strip() for c in raw_h.split("|")]
        if cols == expected_41:
            found_41 = True
        elif cols == expected_42:
            found_42 = True
    if not found_41:
        r.fail(
            f"[§四.4.1] 包含功能表列名错误或缺失；期望：`| 功能模块 | 功能描述 | 备注 |`"
        )
    else:
        r.ok("§四.4.1 包含功能表列名正确（3 列）")
    if not found_42:
        r.fail(
            f"[§四.4.2] 排除功能表列名错误或缺失；期望：`| 排除项 | 排除原因 | 后续安排 |`"
        )
    else:
        r.ok("§四.4.2 排除功能表列名正确（3 列）")


# ── F. §五 约束条件：三个固定子节 + 5.4 条件 ──────────────────────────────────

CONSTRAINT_SUBSECTIONS = [
    ("5.1 技术约束", re.compile(r"^###\s*5\.1\s+技术约束", re.MULTILINE)),
    ("5.2 平台约束", re.compile(r"^###\s*5\.2\s+平台约束", re.MULTILINE)),
    ("5.3 范围约束", re.compile(r"^###\s*5\.3\s+范围约束", re.MULTILINE)),
]


def check_constraints(content: str, r: Report) -> None:
    r.section("§五 约束条件：5.1/5.2/5.3 三个固定子节")
    sec_re = re.compile(r"^##\s*五[、\.]\s*约束条件", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§五.约束条件] 无法提取本节内容")
        return
    for name, pat in CONSTRAINT_SUBSECTIONS:
        if not pat.search(sec_text):
            r.fail(
                f"[§五] 缺失三级子节：{name}；期望：`### {name}`"
            )
            continue
        # 提取该子节文本，确认非空
        sub_text = section_text(sec_text, pat, end_re=re.compile(r"^###\s", re.MULTILINE))
        # 移除 HTML 注释后非空
        cleaned = re.sub(r"<!--.*?-->", "", sub_text, flags=re.DOTALL).strip()
        if not cleaned or has_placeholder(cleaned):
            r.fail(
                f"[§五.{name}] 内容为空或全部为占位；期望：至少 1 条 markdown bullet 描述具体约束"
            )
            continue
        # 至少 1 个 bullet
        if not re.search(r"^\s*-\s+\S", sub_text, re.MULTILINE):
            r.fail(
                f"[§五.{name}] 未找到 bullet；期望：至少 1 行 `- 描述具体约束`"
            )
            continue
        r.ok(f"§五.{name} 已填写")


# ── F.5 S1-07 现网已有模块双重登记(§四.2 标注 ↔ §五.3 锚点) ─────────────────

S1_07_ANCHOR_WORDS = ["现网已有", "已登录态", "登录态", "未登录场景", "现网"]


def check_already_registered_modules(content: str, r: Report) -> None:
    """S1-07: 现网已有模块在 §四.2 排除功能 + §五.3 范围约束 双重登记校验。

    校验逻辑:
        1. 提取 §四.2 标注「已有模块」的行(排除项列内容)
        2. 若无标注 → 视为本项目无上位系统,跳过(OK)
        3. 若有标注 → §五.3 范围约束子节必须含锚点字之一(确认 PM 写了范围声明)

    SSOT 真源: rule_hard_constraints.md S1-07
    """
    r.section("S1-07 现网已有模块双重登记(§四.2 标注 ↔ §五.3 锚点)")

    already_modules = extract_already_have_modules(content)
    if not already_modules:
        r.ok("§四.2 未标注「已有模块」(适用于无上位系统项目);跳过 §五.3 锚点校验")
        return

    r.ok(
        f"§四.2 标注了 {len(already_modules)} 个「已有模块」: {', '.join(already_modules)}"
    )

    # §五.3 范围约束子节文本
    sec5_re = re.compile(r"^##\s*五[、\.]\s*约束条件", re.MULTILINE)
    sec5_text = section_text(content, sec5_re)
    if not sec5_text:
        r.fail(
            "[S1-07] §四.2 标注了已有模块,但 §五 约束条件章节缺失,无法核查双重登记;"
            "SSOT: rule_hard_constraints.md S1-07"
        )
        return

    sub53_re = re.compile(r"^###\s*5\.3\s+范围约束", re.MULTILINE)
    sub53_text = section_text(
        sec5_text, sub53_re, end_re=re.compile(r"^###\s", re.MULTILINE)
    )
    if not sub53_text:
        r.fail(
            "[S1-07] §四.2 标注了已有模块,但 §五.3 范围约束子节缺失"
        )
        return

    found_anchors = [w for w in S1_07_ANCHOR_WORDS if w in sub53_text]
    if not found_anchors:
        r.fail(
            f"[S1-07] §四.2 标注了 {len(already_modules)} 个已有模块,"
            f"但 §五.3 范围约束未含锚点字之一: {S1_07_ANCHOR_WORDS};"
            f"违反双重登记约束(SSOT: rule_hard_constraints.md S1-07)"
        )
    else:
        r.ok(f"§五.3 范围约束含锚点字: {found_anchors}")


# ── G. §六 问题清单：6.1 / 6.2 各 5 列 ────────────────────────────────────────

def check_issue_lists(content: str, r: Report) -> None:
    r.section("§六 问题清单：6.1 阻塞 / 6.2 非阻塞")
    sec_re = re.compile(r"^##\s*六[、\.]\s*问题清单", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§六.问题清单] 无法提取本节内容")
        return

    if not re.search(r"^###\s*6\.1\s+阻塞性问题", sec_text, re.MULTILINE):
        r.fail("[§六.6.1] 缺失子节标题；期望：`### 6.1 阻塞性问题`")
    if not re.search(r"^###\s*6\.2\s+非阻塞性问题", sec_text, re.MULTILINE):
        r.fail("[§六.6.2] 缺失子节标题；期望：`### 6.2 非阻塞性问题`")

    # 6.1 表头：编号 / 问题描述 / 影响范围 / 待确认内容 / 状态
    expected_61 = ["编号", "问题描述", "影响范围", "待确认内容", "状态"]
    # 6.2 表头：编号 / 问题描述 / 处理方式 / 待确认内容 / 状态
    # 列名为中性词「处理方式」——兼容 ⏳ 暂定态（PM 提交前）与 ✅ 已决策态（产品总监终审后）两态语义
    expected_62 = ["编号", "问题描述", "处理方式", "待确认内容", "状态"]
    table_headers = re.findall(r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", sec_text, re.MULTILINE)
    found_61 = found_62 = False
    for raw_h in table_headers:
        cols = [c.strip() for c in raw_h.split("|")]
        if cols == expected_61:
            found_61 = True
        elif cols == expected_62:
            found_62 = True
    if not found_61:
        r.fail(
            f"[§六.6.1] 阻塞性问题表列名错误或缺失；"
            f"期望 5 列：`| 编号 | 问题描述 | 影响范围 | 待确认内容 | 状态 |`"
        )
    else:
        r.ok("§六.6.1 阻塞性问题表列名正确（5 列）")
    if not found_62:
        r.fail(
            f"[§六.6.2] 非阻塞性问题表列名错误或缺失；"
            f"期望 5 列：`| 编号 | 问题描述 | 处理方式 | 待确认内容 | 状态 |`"
        )
    else:
        r.ok("§六.6.2 非阻塞性问题表列名正确（5 列）")


# ── H. 文件末尾交接标记 ─────────────────────────────────────────────────────────

def check_submit_marker(content: str, r: Report) -> None:
    r.section("PM 自审完成提交标记")
    if "【✅ PM 自审完成，提交主管审核】" in content:
        r.ok("已含 PM 自审完成提交标记")
    else:
        r.warn(
            "[标记] 未发现 `【✅ PM 自审完成，提交主管审核】`；"
            "期望：自审通过后于文末（§七 自审清单与 §八 变更记录之间）写入此标记"
        )


def check_no_inline_change_markers(content: str, r: Report) -> None:
    """SSOT #79 — 阶段 1 需求分析正文禁内联变更标记（WARN，跨阶段前移防线）。
    变更历史走变更记录表 + git；查版本差异用 `git diff`，正文勿留内联标记
    （否则顺前序阶段搬进交付 spec/prd）。检测 + 文案单源自 warn_inline_markers。"""
    r.section("内联变更标记纪律（SSOT #79，跨阶段前移；WARN）")
    warn_inline_markers("需求分析", content, r)


# ── 主入口 ────────────────────────────────────────────────────────────────────

def resolve_target_path(argv: list[str]) -> Path:
    if len(argv) > 1:
        p = Path(argv[1])
        if not p.is_absolute():
            p = (REPO_ROOT / p).resolve()
        return p
    if not OUTPUT_DIR.exists():
        print(
            f"[ERROR] 默认目录不存在：{OUTPUT_DIR}\n"
            f"用法：python pm-workflow/scripts/precheck_stage1.py [产物路径]",
            file=sys.stderr,
        )
        sys.exit(1)
    candidates = sorted(OUTPUT_DIR.glob("需求分析_*_latest.md"))
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) == 0:
        print(
            f"[ERROR] {OUTPUT_DIR} 下未找到 `需求分析_*_latest.md`；"
            f"请显式传入产物路径作为参数 1",
            file=sys.stderr,
        )
        sys.exit(1)
    print(
        f"[ERROR] {OUTPUT_DIR} 下存在多个 `需求分析_*_latest.md`，请显式传入产物路径作为参数 1：\n"
        + "\n".join(f"  - {c}" for c in candidates),
        file=sys.stderr,
    )
    sys.exit(1)


def _check_pre_commit_hook_installed() -> str | None:
    """检测 .git/hooks/pre-commit 是否已安装（指向仓库 hook 源）。
    返回 None = 已装/检查不适用；返回 str = WARN 信息。
    SSOT 真源：`pm-workflow/rules/agent_dispatch_protocol.md`「PM / Supervisor Agent 文件改动权限边界」第 5 条 / SSOT 双锚 #31。"""
    git_hook = REPO_ROOT / ".git" / "hooks" / "pre-commit"
    expected = REPO_ROOT / "pm-workflow" / "scripts" / "hooks" / "pre-commit"
    if not expected.exists():
        return None  # 仓库未含 hook 源,跳过
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
    if matches.get("§一 需求概述"):
        check_overview(content, r)
    # §二 用户角色与权限的表结构校验由 S1-NAMING-01 接管(下方 NAMING 段)
    if matches.get("§三 核心业务场景"):
        check_scenarios(content, r)
    if matches.get("§四 功能边界"):
        check_boundaries(content, r)
    if matches.get("§五 约束条件"):
        check_constraints(content, r)
    if matches.get("§六 问题清单"):
        check_issue_lists(content, r)
    check_submit_marker(content, r)
    # SSOT #79 跨阶段前移 — 正文禁内联变更标记（WARN）
    check_no_inline_change_markers(content, r)

    # S1-07 现网已有模块双重登记(§四.2 ↔ §五.3)
    if matches.get("§四 功能边界") and matches.get("§五 约束条件"):
        check_already_registered_modules(content, r)

    # G-01 / G-02 4 阶段通用硬规则(rule_hard_constraints.md)
    # archive_prefix 从 latest 文件名推导: 需求分析_[产品名]_latest.md → 需求分析_[产品名]
    archive_prefix = target.stem.removesuffix("_latest")
    check_archive_sync(target, r, "阶段1 需求分析", archive_prefix, REPO_ROOT)
    check_version_changelog(content, r, "阶段1 需求分析")

    # S1-08 UI 字面来源标注校验（G 方案 G.5，SSOT #54，[Recommended] WARN 不阻断）
    from precheck_common import check_ui_source_annotation
    check_ui_source_annotation(content, 1, r)

    # S1-NAMING-01 §二 角色定义表结构校验(建议 7-L1 / issue # 3 复盘根因 G)
    # 校验角色表是 6 列结构(角色编号/规范字面/别名/角色描述/核心诉求/权限范围),
    # 是阶段 2/3/4 SX-NAMING-01 别名命中校验的 SSOT 数据源
    r.section("S1-NAMING-01 §二 角色定义表结构校验(建议 7 / issue # 3 复盘)")
    role_table = extract_role_table(content)
    if role_table is None:
        r.warn(
            "[S1-NAMING-01] 未检测到 §二 用户角色与权限 6 列结构(角色编号/规范字面/别名"
            "/禁用字面/角色描述/核心诉求/权限范围),NAMING 系列校验待模板升级后启用;"
            "SSOT 真源:tmpl_需求分析.md §二"
        )
    else:
        canonicals = list(role_table.keys())
        if len(canonicals) != len(set(canonicals)):
            dups = [c for c in canonicals if canonicals.count(c) > 1]
            r.fail(
                f"[S1-NAMING-01] §二 角色定义表「规范字面」列出现重复:"
                f"{list(set(dups))} — 必须字面唯一(角色命名 SSOT 不可歧义)"
            )
        else:
            total_aliases = sum(len(v) for v in role_table.values())
            r.ok(
                f"§二 角色定义表合规:{len(role_table)} 个角色,"
                f"{total_aliases} 个别名登记,规范字面字面唯一"
            )

    sys.exit(r.summary())


if __name__ == "__main__":
    main()
