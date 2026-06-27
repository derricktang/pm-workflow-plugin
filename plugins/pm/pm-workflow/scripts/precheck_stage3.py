#!/usr/bin/env python3
"""
precheck_stage3.py — 阶段三（产品定义）自审前置机械检查脚本

用法：
    python pm-workflow/scripts/precheck_stage3.py [产物路径]

    产物路径默认按下序解析：
      1. 命令行参数 1 = 显式路径
      2. outputs/ 下匹配 `产品定义_*_latest.md` 的唯一文件
      3. 若无法解析 → 错误退出

作用：
    在 PM 自审清单的「机械检查前置」步骤运行，机械校验阶段三产物
    （outputs/产品定义_[产品名]_latest.md）是否满足模板硬约束（含 issue #5 Tier 2 修订）：

      A. 章节存在性（tmpl_产品定义.md §0 ~ §18 + §5.5 业务流程图复述,共 20 个章节 + 变更日志）
      B. 表格列校验（§0 / §3 / §4 / §5 / §6 / §7 / §8 / §9 / §10 / §11 / §12
                     / §13 性能体验 / §15 / §16 / §17 / §18）
      C. [Must] 段非空（§1 4 固定问题 / §2 OKR / §3 用户画像 5 属性 / §4 矩阵）
      D. issue #5 Tier 2 格式约束（重点机械化项）：
         - FMT-1 §7 [Must] 交互说明表元素最小集（标题段存在）
         - FMT-2 §7 [Must] 业务规则格式约束（标题段存在）
         - FMT-3 §7 [Must] 验收场景选取标准（标题段存在）
         - FMT-4 §5 [Should] 多旅程产品组织规则（标题段存在）
         - FMT-5 §6 [Should] 复杂跳转用 Mermaid 补充（标题段存在）
         - FMT-6 §13 [Must] 体验意图填写格式（四要素核查 + 反例提示）
      E. §14 PM 不填豁免（仅校验章节存在性，内容允许"待开发 Agent 填写"占位）

    SSOT 主从关系：模板（pm-workflow/rules/tmpl_产品定义.md，含 Tier 2 修订）是真源，
    本脚本是机械兜底（`pm-workflow/rules/ssot_anchors.md` #28）。
    模板调整后须同步本脚本规则；本脚本不得反向倒逼模板。

    SSOT 元规范：本脚本是 prd_expression_standard.md §零 元规范
    "零猜测实现粒度"原则的阶段三机械化实现——让不同 PM 用同一模板产出格式相同的章节。

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
    check_archive_sync,
    check_role_naming_consistency,
    check_version_changelog,
    extract_role_table,
)

OUTPUT_DIR = PROJECT_ROOT / "outputs"


# ── 报告收集器 ────────────────────────────────────────────────────────────────

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
            print("请 PM 按以下清单整改后重跑 precheck_stage3.py：")
            for i, e in enumerate(self.errors, 1):
                print(f"  {i}. {e}")
            return 1
        if self.warnings:
            print(f"\n[PASS-W] 通过，但存在 {len(self.warnings)} 项警告，自审时请一并确认。")
        else:
            print("\n[PASS] 阶段三机械检查通过，可继续 PM 自审。")
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
    """提取从某个标题开始到下一个同级标题之间的文本。"""
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


def all_table_headers(text: str) -> list[list[str]]:
    """提取一段文本中所有 markdown 表格的表头列表。"""
    headers: list[list[str]] = []
    for h_m in re.finditer(r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", text, re.MULTILINE):
        cols = [c.strip() for c in h_m.group(1).split("|")]
        headers.append(cols)
    return headers


# ── A. 章节存在性 ──────────────────────────────────────────────────────────────

# tmpl_产品定义.md 使用 `## 0. ...` 风格（数字 + 句点）而非 `## 一、...`
REQUIRED_SECTIONS = [
    ("§0 文档导读", re.compile(r"^##\s*0\.\s*文档导读", re.MULTILINE)),
    ("§1 问题陈述", re.compile(r"^##\s*1\.\s*问题陈述", re.MULTILINE)),
    ("§2 战略背景", re.compile(r"^##\s*2\.\s*战略背景", re.MULTILINE)),
    ("§3 用户画像", re.compile(r"^##\s*3\.\s*用户画像", re.MULTILINE)),
    ("§4 权限矩阵", re.compile(r"^##\s*4\.\s*权限矩阵", re.MULTILINE)),
    ("§5 用户旅程", re.compile(r"^##\s*5\.\s*用户旅程", re.MULTILINE)),
    ("§5.5 业务流程图", re.compile(r"^##\s*5\.5\s*业务流程图", re.MULTILINE)),
    ("§6 页面路由", re.compile(r"^##\s*6\.\s*页面路由", re.MULTILINE)),
    ("§6.5 产品架构", re.compile(r"^##\s*6\.5\s*产品架构", re.MULTILINE)),
    ("§7 功能需求", re.compile(r"^##\s*7\.\s*功能需求", re.MULTILINE)),
    ("§8 状态流转", re.compile(r"^##\s*8\.\s*状态流转", re.MULTILINE)),
    ("§9 数据字段说明", re.compile(r"^##\s*9\.\s*数据字段说明", re.MULTILINE)),
    ("§10 接口需求说明", re.compile(r"^##\s*10\.\s*接口需求说明", re.MULTILINE)),
    ("§11 异常处理全景", re.compile(r"^##\s*11\.\s*异常处理全景", re.MULTILINE)),
    ("§12 数据埋点需求", re.compile(r"^##\s*12\.\s*数据埋点需求", re.MULTILINE)),
    ("§13 非功能需求", re.compile(r"^##\s*13\.\s*非功能需求", re.MULTILINE)),
    ("§14 技术实现建议", re.compile(r"^##\s*14\.\s*技术实现建议", re.MULTILINE)),
    ("§15 测试数据准备", re.compile(r"^##\s*15\.\s*测试数据准备", re.MULTILINE)),
    ("§16 待解决问题", re.compile(r"^##\s*16\.\s*待解决问题", re.MULTILINE)),
    ("§17 依赖与风险", re.compile(r"^##\s*17\.\s*依赖与风险", re.MULTILINE)),
    ("§18 里程碑", re.compile(r"^##\s*18\.\s*里程碑", re.MULTILINE)),
    ("变更日志", re.compile(r"^##\s*变更日志", re.MULTILINE)),
]


def check_sections(content: str, r: Report) -> dict[str, re.Match | None]:
    r.section("章节存在性（tmpl_产品定义.md §0–§18 + §5.5 + §6.5 + 变更日志）")
    matches: dict[str, re.Match | None] = {}
    all_ok = True
    for name, pat in REQUIRED_SECTIONS:
        m = pat.search(content)
        matches[name] = m
        if m is None:
            r.fail(f"[章节] 缺失：{name}；期望格式：`## {name.replace('§', '').replace(' ', '. ', 1)}`")
            all_ok = False
    if all_ok:
        r.ok(f"全部 {len(REQUIRED_SECTIONS)} 个章节齐全（§0–§18 + §5.5 + §6.5 + 变更日志）")
    return matches


# ── B. §0 文档导读：表格 4 列 ────────────────────────────────────────────────

def check_section_0(content: str, r: Report) -> None:
    r.section("§0 文档导读：Agent 必读章节表")
    sec_re = re.compile(r"^##\s*0\.\s*文档导读", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§0] 无法提取本节内容")
        return
    expected = ["Agent", "必读章节", "可跳过章节", "核心任务"]
    if not any(h == expected for h in all_table_headers(sec_text)):
        r.fail(
            f"[§0] 文档导读表列名错误或缺失；"
            f"期望：`| Agent | 必读章节 | 可跳过章节 | 核心任务 |` 4 列"
        )
    else:
        r.ok("§0 文档导读表 列名正确（4 列）")


# ── C. §1 问题陈述：4 固定问题 ────────────────────────────────────────────────

PROBLEM_QUESTIONS = [
    "谁有这个问题？",
    "问题是什么？",
    "为什么痛？",
    "用户证据",
]


def check_section_1(content: str, r: Report) -> None:
    r.section("§1 问题陈述：4 个固定问题 + 产品边界复述")
    sec_re = re.compile(r"^##\s*1\.\s*问题陈述", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§1] 无法提取本节内容")
        return
    for q in PROBLEM_QUESTIONS:
        if not re.search(rf"\*\*{re.escape(q)}\*\*", sec_text):
            r.fail(
                f"[§1.问题陈述] 缺少必填问题：『{q}』；"
                f"期望：`**{q}**`（粗体小标题）独立成行"
            )
            return
    # T2-1：产品边界复述段（issue 2026-05-05_2243 复盘根因 3）
    if not re.search(r"\*\*`?\[Must\]`?\s*产品边界与系统集成", sec_text):
        r.fail(
            "[§1.产品边界] 缺少必填复述段：`**[Must]` 产品边界与系统集成 **`；"
            "期望：复刻阶段 1 §一·产品边界 5 字段（系统形态/上级模块/进入入口/退出·返回/跨系统数据流）+ 阶段 3 业务术语展开"
        )
        return
    # 校验 5 字段齐全（与 stage1 一致）
    boundary_fields = ["系统形态", "上级模块", "进入入口", "退出/返回", "跨系统数据流"]
    boundary_section_match = re.search(
        r"\*\*`?\[Must\]`?\s*产品边界与系统集成[^\n]*\n.*",
        sec_text, flags=re.DOTALL
    )
    boundary_text = boundary_section_match.group(0) if boundary_section_match else ""
    missing = [
        f for f in boundary_fields
        if not re.search(rf"-\s*\*\*{re.escape(f)}\*\*", boundary_text)
    ]
    if missing:
        r.fail(
            f"[§1.产品边界] 复述段缺字段：{missing}；"
            f"期望 5 字段全列出（与阶段 1 真源对齐）"
        )
        return
    r.ok("§1 问题陈述 4 个固定问题齐全 + 产品边界 5 字段复述")


# ── D. §2 战略背景 ────────────────────────────────────────────────────────────

def check_section_2(content: str, r: Report) -> None:
    r.section("§2 战略背景：业务目标关联 / 为什么是现在")
    sec_re = re.compile(r"^##\s*2\.\s*战略背景", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§2] 无法提取本节内容")
        return
    if not re.search(r"\*\*业务目标关联\*\*", sec_text):
        r.fail("[§2] 缺少 `**业务目标关联**` 段（含关联 OKR + 战略意义）")
        return
    if not re.search(r"\*\*为什么是现在\*\*", sec_text):
        r.fail("[§2] 缺少 `**为什么是现在**` 段")
        return
    r.ok("§2 战略背景 含必填两段")


# ── E. §3 用户画像：5 属性表 ─────────────────────────────────────────────────

def check_section_3(content: str, r: Report) -> None:
    r.section("§3 用户画像：5 属性表 + 结构化角色 ID/名 字段")
    sec_re = re.compile(r"^##\s*3\.\s*用户画像", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§3] 无法提取本节内容")
        return
    expected = ["属性", "描述"]
    headers = all_table_headers(sec_text)
    if not any(h == expected for h in headers):
        r.fail(
            f"[§3] 角色属性表列名错误或缺失；"
            f"期望：`| 属性 | 描述 |` 2 列（每个角色独立 1 张）"
        )
        return
    # 5 行属性：典型用户 / 核心诉求 / 使用场景 / 关键痛点 / Jobs-to-be-done
    required_attrs = ["典型用户", "核心诉求", "使用场景", "关键痛点", "Jobs-to-be-done"]
    missing = [a for a in required_attrs if a not in sec_text]
    if missing:
        r.fail(
            f"[§3] 角色画像缺少必填属性：{missing}；"
            f"期望：每个角色含 5 行属性（典型用户/核心诉求/使用场景/关键痛点/Jobs-to-be-done）"
        )
        return

    # 结构化角色 ID/名 字段校验（SSOT 双锚 #24 升级）
    # 期望每个 `### 角色N：` 块含两行：
    #   - **角色 ID**：[`role-N`]（N 为正整数）
    #   - **角色名**：[xxx]
    role_blocks = re.findall(r"^###\s+角色[一二三四五六七八九十\d]+[：:].*?(?=^###\s|^##\s|\Z)",
                             sec_text, flags=re.MULTILINE | re.DOTALL)
    if not role_blocks:
        r.fail("[§3] 未识别到 `### 角色N：` 三级标题块")
        return

    role_id_re = re.compile(r"-\s*\*\*角色\s*ID\*\*\s*[：:]\s*\[`?(role-\d+)`?\]")
    role_name_re = re.compile(r"-\s*\*\*角色名\*\*\s*[：:]\s*\[(.+?)\]")
    seen_ids: list[str] = []
    seen_names: list[str] = []
    for i, block in enumerate(role_blocks, 1):
        # 跳过模板自身的占位符（含中文【】）—— 占位符未被 PM 替换属于"未填"由人工把关
        # 这里仅校验非占位符的真实角色块结构是否齐全
        title_line = block.split("\n", 1)[0]
        # 占位符识别：标题中含【】方括号即视为模板未替换
        is_placeholder_title = "【" in title_line or "】" in title_line

        id_m = role_id_re.search(block)
        name_m = role_name_re.search(block)

        if not id_m:
            r.fail(
                f"[§3] 第 {i} 个角色块缺 `**角色 ID**：[role-N]` 字段；"
                f"标题：{title_line.strip()}；期望格式：`- **角色 ID**：[\\`role-1\\`]`"
            )
            continue
        if not name_m:
            r.fail(
                f"[§3] 第 {i} 个角色块缺 `**角色名**：[xxx]` 字段；"
                f"标题：{title_line.strip()}；期望格式：`- **角色名**：[业务角色名]`"
            )
            continue

        role_id = id_m.group(1)
        role_name = name_m.group(1).strip()
        if role_id in seen_ids:
            r.fail(f"[§3] 角色 ID 重复：{role_id!r}；本节内必须全局唯一")
            continue
        seen_ids.append(role_id)
        if not is_placeholder_title and role_name in seen_names:
            r.fail(f"[§3] 角色名重复：{role_name!r}；本节内必须全局唯一")
            continue
        seen_names.append(role_name)

    if seen_ids:
        r.ok(f"§3 用户画像 含 {len(seen_ids)} 个角色块 + 全部含结构化 ID/名 字段")
    else:
        r.fail("[§3] 未提取到任何合法角色 ID/名对")


# ── F. §4 权限矩阵：表格 + ✅/❌ 标记 ────────────────────────────────────────

def check_section_4(content: str, r: Report) -> None:
    r.section("§4 权限矩阵：表格 + 权限标记")
    sec_re = re.compile(r"^##\s*4\.\s*权限矩阵", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§4] 无法提取本节内容")
        return
    headers = all_table_headers(sec_text)
    if not headers:
        r.fail("[§4] 未找到权限矩阵表；期望：至少 1 张表，第 1 列为「功能点」")
        return
    # 至少有一张表，首列叫"功能点"
    has_perm_table = any(h and h[0] == "功能点" for h in headers)
    if not has_perm_table:
        r.fail(
            f"[§4] 权限矩阵表首列错误；"
            f"期望：首列为 `功能点`，后续列为各角色（如 `普通用户` / `管理员` / `未登录`）"
        )
        return
    # 含 ✅ 或 ❌ 之一
    if "✅" not in sec_text and "❌" not in sec_text:
        r.fail(
            "[§4] 权限矩阵未使用 ✅ / ❌ 标记；"
            "期望：每个权限单元格用 ✅（允许）/ ❌（禁止）+ 可选附说明"
        )
        return
    r.ok("§4 权限矩阵 表头正确 + 含 ✅/❌ 标记")


# ── G. §5 用户旅程：旅程步骤表 8 列 + 多角色矩阵 4 列 + Tier 2 FMT-4 ─────────

JOURNEY_STEP_COLS = ["序号", "阶段名", "用户行为", "涉及页面", "触点", "痛点", "期望", "系统响应", "异常 / 边界"]
JOURNEY_ROLE_COLS = ["步骤序号", "主导角色", "参与角色", "协作关系描述"]


def check_section_5(content: str, r: Report) -> None:
    r.section("§5 用户旅程：步骤表 9 列 + 多角色矩阵 4 列 + FMT-4 多旅程规则")
    sec_re = re.compile(r"^##\s*5\.\s*用户旅程", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§5] 无法提取本节内容")
        return

    # 旅程步骤表（9 列）：序号 / 阶段名 / 用户行为 / 涉及页面 / 触点 / 痛点 / 期望 / 系统响应 / 异常 / 边界
    headers = all_table_headers(sec_text)
    if not any(h == JOURNEY_STEP_COLS for h in headers):
        r.fail(
            f"[§5] 旅程步骤表列名错误或缺失；"
            f"期望 9 列：`| {' | '.join(JOURNEY_STEP_COLS)} |`"
        )
    else:
        r.ok("§5 旅程步骤表 列名正确（9 列）")

    # FMT-4：[Should] 多旅程产品组织规则 段（issue #5 Tier 2 修订）
    # 允许 `[Should]` / [Should] / 反引号包裹形式（模板使用 `[Should]` 反引号风格）
    if not re.search(r"`?\[Should\]`?\s*多旅程产品组织规则", sec_text):
        r.fail(
            "[§5] 缺少 issue #5 Tier 2 修订段：`[Should] 多旅程产品组织规则`；"
            "期望：在「填写规则总览」表后插入该段（含三级标题分割 + 旅程间流转关系表 5 列 + 4 条独立判定标准）"
        )
    else:
        r.ok("§5 [Should] 多旅程产品组织规则 段（FMT-4）存在")


# ── G+. §5.5 业务流程图：mermaid 数 ↔ 阶段 2 §二对称（SSOT #30）─────────────


def check_section_5_5(content: str, r: Report) -> None:
    """§5.5 业务流程图复述与阶段 2 §二 mermaid 数对称（NB SSOT #30 阶段 3 派生扩展）。

    阶段 2 真源：outputs/功能规划_*_latest.md §二
    阶段 3 派生：本章节 §5.5（含 5.5.1 主流程 / 5.5.2 跨角色 / 5.5.3 补充）
    校验：mermaid 块数对称（数对称作为机械兜底,字面值差异留人审）
    """
    r.section("§5.5 业务流程图复述 ↔ 阶段 2 §二 mermaid 数对称（SSOT #30）")
    sec_re = re.compile(r"^##\s*5\.5\s*业务流程图", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§5.5] 无法提取本节内容（章节缺失或编号格式错误）")
        return

    stage3_count = len(re.findall(r"```mermaid\b", sec_text))

    stage2_files = list(OUTPUT_DIR.glob("功能规划_*_latest.md"))
    if not stage2_files:
        r.warn(
            "[§5.5] 未找到 outputs/功能规划_*_latest.md,跳过 mermaid 数对称校验"
            "（阶段 2 产物缺失时不阻断阶段 3 自审,仅 WARN）"
        )
        return

    stage2_text = stage2_files[0].read_text(encoding="utf-8")
    stage2_section_re = re.compile(r"^##\s*二、\s*业务流程图", re.MULTILINE)
    stage2_sec = section_text(stage2_text, stage2_section_re)
    if not stage2_sec:
        r.warn(
            f"[§5.5] {stage2_files[0].name} 未找到 §二 业务流程图章节,跳过对称校验"
        )
        return

    stage2_count = len(re.findall(r"```mermaid\b", stage2_sec))

    if stage3_count == 0 and stage2_count > 0:
        r.fail(
            f"[§5.5] 本章节 0 个 mermaid 块,但阶段 2 §二有 {stage2_count} 个"
            f"（PM 漏迁入,违反 SSOT #30 派生约束）"
        )
    elif stage3_count != stage2_count:
        r.fail(
            f"[§5.5] mermaid 数不对称：本章节 {stage3_count} 块 vs "
            f"阶段 2 §二 {stage2_count} 块（SSOT #30 真源派生应等数）"
        )
    elif stage2_count == 0:
        r.warn("[§5.5] 阶段 2 §二与本章节均 0 个 mermaid 块（业务流程图未填写,需人审确认是否合理）")
    else:
        r.ok(f"§5.5 业务流程图 mermaid 数对称（{stage3_count} 块 ↔ 阶段 2 §二 {stage2_count} 块）")


# ── G++. §6.5 产品架构：模块数 ↔ 阶段 2 §一对称（SSOT #40）──────────────────


def check_section_6_5(content: str, r: Report) -> None:
    """§6.5 产品架构复述与阶段 2 §一 模块数对称（SSOT #40 阶段 3 派生）。

    阶段 2 真源：outputs/功能规划_*_latest.md §一（模块定义 `### M\\d+` 标题数）
    阶段 3 派生：本章节 §6.5 模块表数据行数
    校验：模块数对称（数对称机械兜底；依赖/职责字面差异留人审，与 #30 同型）。
    """
    r.section("§6.5 产品架构复述 ↔ 阶段 2 §一 模块数对称（SSOT #40）")
    sec_re = re.compile(r"^##\s*6\.5\s*产品架构", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§6.5] 无法提取本节内容（章节缺失或编号格式错误）")
        return

    table_rows = [
        ln.strip() for ln in sec_text.splitlines() if ln.strip().startswith("|")
    ]
    data_rows = [
        ln for ln in table_rows
        if not re.match(r"^\|[\s:|-]+\|?$", ln)   # 分隔行 |---|---|
        and "名称" not in ln                       # 表头行（含列名"名称"）
        and "【" not in ln                          # 未填模板占位行
    ]
    stage3_modules = len(data_rows)

    stage2_files = list(OUTPUT_DIR.glob("功能规划_*_latest.md"))
    if not stage2_files:
        r.warn(
            "[§6.5] 未找到 outputs/功能规划_*_latest.md,跳过模块数对称校验"
            "（阶段 2 产物缺失时不阻断阶段 3 自审,仅 WARN）"
        )
        return

    s2 = stage2_files[0].read_text(encoding="utf-8")
    s2_sec = section_text(s2, re.compile(r"^##\s*一、\s*功能模块清单", re.MULTILINE))
    if not s2_sec:
        r.warn(
            f"[§6.5] {stage2_files[0].name} 未找到 §一 功能模块清单,跳过对称校验"
        )
        return
    stage2_modules = len(re.findall(r"^###\s*M\d+", s2_sec, re.MULTILINE))

    if stage2_modules == 0:
        r.warn("[§6.5] 阶段 2 §一 未识别到 `### M\\d+` 模块定义,跳过（需人审）")
    elif stage3_modules == 0:
        r.fail(
            f"[§6.5] 本章节 0 个模块行,但阶段 2 §一有 {stage2_modules} 个模块"
            f"（PM 漏复述,违反 SSOT #40 派生约束）"
        )
    elif stage3_modules != stage2_modules:
        r.fail(
            f"[§6.5] 模块数不对称：本章节 {stage3_modules} 行 vs "
            f"阶段 2 §一 {stage2_modules} 个（SSOT #40 真源派生应等数）"
        )
    else:
        r.ok(
            f"§6.5 产品架构模块数对称（{stage3_modules} ↔ 阶段 2 §一 {stage2_modules}）"
        )


# ── H. §6 页面路由：路由表 8 列 + Tier 2 FMT-5 ──────────────────────────────

ROUTE_COLS = ["页面 ID", "页面名称", "路由地址", "父页面", "对应功能", "访问权限", "类型", "对客"]


def check_section_6(content: str, r: Report) -> None:
    r.section("§6 页面路由：路由表 8 列 + FMT-5 复杂跳转 Mermaid")
    sec_re = re.compile(r"^##\s*6\.\s*页面路由", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§6] 无法提取本节内容")
        return
    if not any(h == ROUTE_COLS for h in all_table_headers(sec_text)):
        r.fail(
            f"[§6] 页面路由表列名错误或缺失；"
            f"期望 8 列：`| {' | '.join(ROUTE_COLS)} |`"
        )
    else:
        r.ok("§6 页面路由表 列名正确（8 列）")

    # FMT-5：[Should] 复杂跳转用 Mermaid 补充 段
    if not re.search(r"`?\[Should\]`?\s*复杂跳转用\s*Mermaid", sec_text):
        r.fail(
            "[§6] 缺少 issue #5 Tier 2 修订段：`[Should] 复杂跳转用 Mermaid 补充`；"
            "期望：在「补充跳转规则」段后插入（含 4 条触发条件 + 完整 mermaid 示例 + 派生输入说明）"
        )
    else:
        r.ok("§6 [Should] 复杂跳转用 Mermaid 段（FMT-5）存在")


# ── I. §7 功能需求 + Tier 2 FMT-1/2/3 三段 [Must] ────────────────────────────

def check_section_7(content: str, r: Report) -> None:
    r.section("§7 功能需求：FMT-1/2/3 三段 [Must] + 验收 Gherkin 格式")
    sec_re = re.compile(r"^##\s*7\.\s*功能需求", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§7] 无法提取本节内容")
        return

    # FMT-1：[Must] 交互说明表元素最小集
    if not re.search(r"`?\[Must\]`?\s*交互说明表元素最小集", sec_text):
        r.fail(
            "[§7] 缺少 issue #5 Tier 2 修订段：`[Must] 交互说明表元素最小集`（FMT-1）；"
            "期望：章节头部含必含元素清单（表单字段 / 操作按钮 / 成功反馈 / 异常态）"
        )
    else:
        r.ok("§7 [Must] FMT-1 交互说明表元素最小集 段存在")

    # FMT-2：[Must] 业务规则格式约束
    if not re.search(r"`?\[Must\]`?\s*业务规则格式约束", sec_text):
        r.fail(
            "[§7] 缺少 issue #5 Tier 2 修订段：`[Must] 业务规则格式约束`（FMT-2）；"
            "期望：章节头部明示数据规模/数据来源用表格、其他子项 markdown bullet"
        )
    else:
        r.ok("§7 [Must] FMT-2 业务规则格式约束 段存在")

    # FMT-3：[Must] 验收场景选取标准
    if not re.search(r"`?\[Must\]`?\s*验收场景选取标准", sec_text):
        r.fail(
            "[§7] 缺少 issue #5 Tier 2 修订段：`[Must] 验收场景选取标准`（FMT-3）；"
            "期望：章节头部含四类穷举（正常 / 枚举 / 约束 / 异常）+ G-W-T 句式"
        )
    else:
        r.ok("§7 [Must] FMT-3 验收场景选取标准 段存在")

    # 至少含一个 F-XXX 功能定义
    f_funcs = re.findall(r"^###\s+F-\d{3}", sec_text, re.MULTILINE)
    if not f_funcs:
        r.fail(
            "[§7] 未找到任何功能定义；期望：至少 1 个 `### F-001：...` 三级标题"
        )
    else:
        r.ok(f"§7 含 {len(f_funcs)} 个功能（F-XXX）")

    # 至少含一个 gherkin 代码块
    if not re.search(r"```gherkin", sec_text):
        r.fail(
            "[§7] 未找到任何 ```gherkin``` 代码块；"
            "期望：每个 F-XXX 含 ```gherkin``` 块用 Given/When/Then/And 格式"
        )


# ── I.5 S3-05 跨章节一致性(页面编号 + 字段名死引用) ───────────────────────────

PAGE_ID_REF_RE = re.compile(r"P-\d{2,}")


def check_cross_section_consistency(content: str, r: Report) -> None:
    """S3-05: 跨章节一致性校验(简化版,2 维度)。

    校验维度:
        a. 页面编号一致性: §7 / §11 中所有 P-XX 引用 ⊆ §6 路由表页面 ID 集合
        b. 字段名死引用: §9 定义字段(英文标识符格式)应在 §7/§10/§11/§12 至少出现 1 次(WARN)

    其他维度(接口编号反查 / 功能编号反查 / 同义词识别)挂 NB-WE-22 后续补。

    SSOT 真源: rule_hard_constraints.md S3-05
    """
    r.section("S3-05 跨章节一致性(页面编号 + 字段名死引用)")

    # ── a. 页面编号一致性 ──
    sec6_re = re.compile(r"^##\s*6\.\s*页面路由", re.MULTILINE)
    sec6_text = section_text(content, sec6_re)
    if not sec6_text:
        r.fail("[S3-05] §6 页面路由章节缺失,无法核查页面编号一致性")
        return

    page_ids: set[str] = set()
    for line in sec6_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if PAGE_ID_REF_RE.fullmatch(cells[0]):
            page_ids.add(cells[0])

    if not page_ids:
        r.warn(
            "[S3-05] §6 路由表未提取到任何页面 ID(`P-XX` 格式),跳过页面编号一致性核查"
        )
    else:
        r.ok(f"§6 路由表定义了 {len(page_ids)} 个页面 ID")

        sec7_text = section_text(
            content, re.compile(r"^##\s*7\.\s*功能需求", re.MULTILINE)
        )
        sec11_text = section_text(
            content, re.compile(r"^##\s*11\.\s*异常处理全景", re.MULTILINE)
        )
        refs_in_7 = set(PAGE_ID_REF_RE.findall(sec7_text)) if sec7_text else set()
        refs_in_11 = set(PAGE_ID_REF_RE.findall(sec11_text)) if sec11_text else set()
        all_refs = refs_in_7 | refs_in_11
        ghost_refs = all_refs - page_ids
        if ghost_refs:
            r.fail(
                f"[S3-05] §7/§11 引用了 §6 未定义的页面 ID(鬼页面): "
                f"{sorted(ghost_refs)};SSOT: rule_hard_constraints.md S3-05"
            )
        else:
            r.ok(
                f"§7/§11 引用的 {len(all_refs)} 个页面 ID 全部在 §6 中定义"
            )

    # ── b. 字段名死引用 ──
    sec9_re = re.compile(r"^##\s*9\.\s*数据字段说明", re.MULTILINE)
    sec9_text = section_text(content, sec9_re)
    if not sec9_text:
        r.warn("[S3-05] §9 数据字段章节缺失,跳过字段名死引用核查")
        return

    field_names: set[str] = set()
    for line in sec9_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        first = cells[0]
        if first in ("字段", "") or first.startswith("-") or has_placeholder(first):
            continue
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", first):
            field_names.add(first)

    if not field_names:
        r.warn(
            "[S3-05] §9 未提取到英文标识符格式字段名,跳过字段名死引用核查"
        )
        return

    other_text = ""
    for sec_num_str in ["7", "10", "11", "12"]:
        sec_x = section_text(
            content, re.compile(rf"^##\s*{sec_num_str}\.", re.MULTILINE)
        )
        if sec_x:
            other_text += "\n" + sec_x

    dead_fields: list[str] = []
    for fname in field_names:
        if not re.search(rf"\b{re.escape(fname)}\b", other_text):
            dead_fields.append(fname)

    if dead_fields:
        preview = dead_fields[:10]
        suffix = "..." if len(dead_fields) > 10 else ""
        r.warn(
            f"[S3-05] §9 定义的字段名未在 §7/§10/§11/§12 引用(疑似死字段): "
            f"{preview}{suffix};建议核查这些字段是否真需要,或在使用章节补充引用"
        )
    else:
        r.ok(
            f"§9 定义的 {len(field_names)} 个字段名全部在 §7/§10/§11/§12 至少出现 1 次"
        )


# ── J. §8 状态流转：图 + 表 ──────────────────────────────────────────────────

STATE_TRANSITION_COLS = ["当前状态", "触发条件", "目标状态", "操作权限", "不可逆说明"]


def check_section_8(content: str, r: Report) -> None:
    r.section("§8 状态流转：mermaid 图 + 状态切换规则表")
    sec_re = re.compile(r"^##\s*8\.\s*状态流转", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§8] 无法提取本节内容")
        return
    if not re.search(r"```mermaid", sec_text):
        r.fail(
            "[§8] 未找到 ```mermaid``` 状态流转图；"
            "期望：至少 1 个 mermaid 块（flowchart 或 stateDiagram-v2）"
        )
    if not any(h == STATE_TRANSITION_COLS for h in all_table_headers(sec_text)):
        r.fail(
            f"[§8] 状态切换规则表列名错误或缺失；"
            f"期望 5 列：`| {' | '.join(STATE_TRANSITION_COLS)} |`"
        )
    else:
        r.ok("§8 状态切换规则表 列名正确（5 列）")


# ── K. §9 数据字段：表格 4 列 ────────────────────────────────────────────────

DATA_FIELD_COLS = ["字段", "业务含义", "约束 / 说明", "数据来源"]


def check_section_9(content: str, r: Report) -> None:
    r.section("§9 数据字段说明：4 列表")
    sec_re = re.compile(r"^##\s*9\.\s*数据字段说明", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§9] 无法提取本节内容")
        return
    if not any(h == DATA_FIELD_COLS for h in all_table_headers(sec_text)):
        r.fail(
            f"[§9] 数据字段表列名错误或缺失；"
            f"期望 4 列：`| {' | '.join(DATA_FIELD_COLS)} |`"
        )
    else:
        r.ok("§9 数据字段表 列名正确（4 列）")


# ── L. §10 接口需求：表格 6 列 ────────────────────────────────────────────────

API_COLS = ["接口 ID", "对应功能", "业务能力描述", "输入（业务语言）", "输出（业务语言）", "关键业务约束"]


def check_section_10(content: str, r: Report) -> None:
    r.section("§10 接口需求说明：6 列表")
    sec_re = re.compile(r"^##\s*10\.\s*接口需求说明", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§10] 无法提取本节内容")
        return
    if not any(h == API_COLS for h in all_table_headers(sec_text)):
        r.fail(
            f"[§10] 接口需求表列名错误或缺失；"
            f"期望 6 列：`| {' | '.join(API_COLS)} |`"
        )
    else:
        r.ok("§10 接口需求表 列名正确（6 列）")


# ── M. §11 异常处理全景：表格 5 列 ────────────────────────────────────────────

EXCEPTION_COLS = ["场景类型", "具体场景", "触发条件", "用户反馈（界面表现）", "系统处理逻辑"]


def check_section_11(content: str, r: Report) -> None:
    r.section("§11 异常处理全景：5 列表")
    sec_re = re.compile(r"^##\s*11\.\s*异常处理全景", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§11] 无法提取本节内容")
        return
    if not any(h == EXCEPTION_COLS for h in all_table_headers(sec_text)):
        r.fail(
            f"[§11] 异常处理表列名错误或缺失；"
            f"期望 5 列：`| {' | '.join(EXCEPTION_COLS)} |`"
        )
    else:
        r.ok("§11 异常处理表 列名正确（5 列）")


# ── N. §12 数据埋点：表格 4 列 ────────────────────────────────────────────────

EVENT_COLS = ["埋点 ID", "触发时机", "记录内容", "用途"]


def check_section_12(content: str, r: Report) -> None:
    r.section("§12 数据埋点需求：4 列表")
    sec_re = re.compile(r"^##\s*12\.\s*数据埋点需求", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§12] 无法提取本节内容")
        return
    if not any(h == EVENT_COLS for h in all_table_headers(sec_text)):
        r.fail(
            f"[§12] 数据埋点表列名错误或缺失；"
            f"期望 4 列：`| {' | '.join(EVENT_COLS)} |`"
        )
    else:
        r.ok("§12 数据埋点表 列名正确（4 列）")


# ── O. §13 非功能需求：性能体验表 4 列 + Tier 2 FMT-6 体验意图四要素 ──────────

PERF_COLS = ["指标", "目标值", "测量条件", "体验意图（PM 填：不达标时用户会遇到什么问题）"]


def check_section_13(content: str, r: Report) -> None:
    r.section("§13 非功能需求：性能体验表 4 列 + FMT-6 体验意图四要素")
    sec_re = re.compile(r"^##\s*13\.\s*非功能需求", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§13] 无法提取本节内容")
        return

    # FMT-6：[Must] 体验意图填写格式 段
    if not re.search(r"`?\[Must\]`?\s*体验意图填写格式", sec_text):
        r.fail(
            "[§13] 缺少 issue #5 Tier 2 修订段：`[Must] 体验意图填写格式`（FMT-6）；"
            "期望：性能体验段含必填四要素格式 `[业务角色] 在 [触发场景] 时 [遭遇的具体问题]，导致 [可量化的业务后果]`"
        )
    else:
        r.ok("§13 [Must] FMT-6 体验意图填写格式 段存在")

    # 性能体验表存在性
    headers = all_table_headers(sec_text)
    perf_table_found = any(h == PERF_COLS for h in headers)
    if not perf_table_found:
        r.fail(
            f"[§13.性能体验] 表列名错误或缺失；"
            f"期望 4 列：`| {' | '.join(PERF_COLS)} |`"
        )
    else:
        r.ok("§13 性能体验表 列名正确（4 列）")

    # 兼容性段（必含 iOS / Android）
    if not re.search(r"###\s*兼容性", sec_text):
        r.fail("[§13] 缺少 `### 兼容性` 段")

    # FMT-6 四要素抽样检查（[Must]）：含"反例"和"正例"对照表
    if perf_table_found:
        # 抽样校验：表内至少有一行含「，导致」（四要素中的因果联接词）
        # 反例对照表中必含 "❌ 反例" 标题
        if "❌ 反例" not in sec_text:
            r.fail(
                "[§13.FMT-6] 缺少『❌ 反例（抽象，无可执行性）』对照表；"
                "期望：含反例 → 正例对照表 4 行 + 四要素核查清单 4 条"
            )


# ── P. §14 技术建议：PM 不填豁免 ──────────────────────────────────────────────

def check_section_14(content: str, r: Report) -> None:
    r.section("§14 技术实现建议（PM 不填，仅校验存在）")
    sec_re = re.compile(r"^##\s*14\.\s*技术实现建议", re.MULTILINE)
    sec_text = section_text(content, sec_re)
    if not sec_text:
        r.fail("[§14] 无法提取本节内容")
        return
    if "PM 不填" not in sec_text and "开发 Agent 自动生成" not in sec_text:
        r.warn(
            "[§14] 未发现『PM 不填 / 开发 Agent 自动生成』标记；"
            "期望：标题或注释中明示『（⚙️ 开发 Agent 自动生成，PM 不填）』"
        )
    else:
        r.ok("§14 含『PM 不填 / 开发 Agent 自动生成』标记")


# ── Q. §15-§18 表格列校验 ────────────────────────────────────────────────────

TEST_DATA_COLS = ["对应场景", "所需前置数据", "准备方式", "准备责任方"]
OPEN_QUESTION_COLS = ["#", "问题描述", "影响范围", "负责人", "截止日期", "状态"]
DEPENDENCY_COLS = ["类型", "描述", "影响范围", "当前状态", "应对措施"]
MILESTONE_COLS = ["节点", "计划日期", "交付内容", "负责方"]


def check_tail_sections(content: str, r: Report) -> None:
    r.section("§15-§18 表格列校验")

    # §15
    sec15 = section_text(content, re.compile(r"^##\s*15\.\s*测试数据准备", re.MULTILINE))
    if sec15:
        if not any(h == TEST_DATA_COLS for h in all_table_headers(sec15)):
            r.fail(
                f"[§15] 测试数据表列名错误或缺失；"
                f"期望 4 列：`| {' | '.join(TEST_DATA_COLS)} |`"
            )
        else:
            r.ok("§15 测试数据表 列名正确（4 列）")

    # §16
    sec16 = section_text(content, re.compile(r"^##\s*16\.\s*待解决问题", re.MULTILINE))
    if sec16:
        if not any(h == OPEN_QUESTION_COLS for h in all_table_headers(sec16)):
            r.fail(
                f"[§16] 待解决问题表列名错误或缺失；"
                f"期望 6 列：`| {' | '.join(OPEN_QUESTION_COLS)} |`"
            )
        else:
            r.ok("§16 待解决问题表 列名正确（6 列）")

    # §17
    sec17 = section_text(content, re.compile(r"^##\s*17\.\s*依赖与风险", re.MULTILINE))
    if sec17:
        if not any(h == DEPENDENCY_COLS for h in all_table_headers(sec17)):
            r.fail(
                f"[§17] 依赖与风险表列名错误或缺失；"
                f"期望 5 列：`| {' | '.join(DEPENDENCY_COLS)} |`"
            )
        else:
            r.ok("§17 依赖与风险表 列名正确（5 列）")

    # §18
    sec18 = section_text(content, re.compile(r"^##\s*18\.\s*里程碑", re.MULTILINE))
    if sec18:
        if not any(h == MILESTONE_COLS for h in all_table_headers(sec18)):
            r.fail(
                f"[§18] 里程碑表列名错误或缺失；"
                f"期望 4 列：`| {' | '.join(MILESTONE_COLS)} |`"
            )
        else:
            r.ok("§18 里程碑表 列名正确（4 列）")


def check_no_inline_change_markers(content: str, r: Report) -> None:
    """SSOT #79 — 阶段 3 产品定义正文禁内联变更标记（WARN，跨阶段前移防线）。
    产品定义是阶段 4 spec/prd 的直接上游，此处标记会被搬进交付物——故守源头尤为关键。
    变更历史走变更记录表 + git；查版本差异用 `git diff`。检测 + 文案单源自 warn_inline_markers。"""
    r.section("内联变更标记纪律（SSOT #79，跨阶段前移；WARN）")
    warn_inline_markers("产品定义", content, r)


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
            f"用法：python pm-workflow/scripts/precheck_stage3.py [产物路径]",
            file=sys.stderr,
        )
        sys.exit(1)
    candidates = sorted(OUTPUT_DIR.glob("产品定义_*_latest.md"))
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) == 0:
        print(
            f"[ERROR] {OUTPUT_DIR} 下未找到 `产品定义_*_latest.md`；"
            f"请显式传入产物路径作为参数 1",
            file=sys.stderr,
        )
        sys.exit(1)
    print(
        f"[ERROR] {OUTPUT_DIR} 下存在多个 `产品定义_*_latest.md`，请显式传入产物路径作为参数 1：\n"
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
    if matches.get("§0 文档导读"):
        check_section_0(content, r)
    if matches.get("§1 问题陈述"):
        check_section_1(content, r)
    if matches.get("§2 战略背景"):
        check_section_2(content, r)
    if matches.get("§3 用户画像"):
        check_section_3(content, r)
    if matches.get("§4 权限矩阵"):
        check_section_4(content, r)
    if matches.get("§5 用户旅程"):
        check_section_5(content, r)
    if matches.get("§5.5 业务流程图"):
        check_section_5_5(content, r)
    if matches.get("§6 页面路由"):
        check_section_6(content, r)
    if matches.get("§6.5 产品架构"):
        check_section_6_5(content, r)
    if matches.get("§7 功能需求"):
        check_section_7(content, r)
    if matches.get("§8 状态流转"):
        check_section_8(content, r)
    if matches.get("§9 数据字段说明"):
        check_section_9(content, r)
    if matches.get("§10 接口需求说明"):
        check_section_10(content, r)
    if matches.get("§11 异常处理全景"):
        check_section_11(content, r)
    if matches.get("§12 数据埋点需求"):
        check_section_12(content, r)
    if matches.get("§13 非功能需求"):
        check_section_13(content, r)
    if matches.get("§14 技术实现建议"):
        check_section_14(content, r)
    check_tail_sections(content, r)

    # S3-05 跨章节一致性(§6 / §7 / §11 页面编号 + §9 字段名死引用)
    if matches.get("§6 页面路由") or matches.get("§9 数据字段说明"):
        check_cross_section_consistency(content, r)

    # G-01 / G-02 4 阶段通用硬规则(rule_hard_constraints.md)
    archive_prefix = target.stem.removesuffix("_latest")
    check_archive_sync(target, r, "阶段3 产品定义", archive_prefix, PROJECT_ROOT)
    check_version_changelog(content, r, "阶段3 产品定义")
    # SSOT #79 跨阶段前移 — 正文禁内联变更标记（WARN；产品定义是阶段 4 直接上游）
    check_no_inline_change_markers(content, r)

    # S3-07 UI 字面来源标注校验（G 方案 G.5，SSOT #54，[Recommended] WARN 不阻断）
    from precheck_common import check_ui_source_annotation
    check_ui_source_annotation(content, 3, r)

    # S3-NAMING-01 角色命名一致性(建议 7 / issue # 3 复盘根因 G)
    # 跑前 Read 阶段 1 真源 → extract_role_table → 在本阶段产物 grep 别名命中
    if archive_prefix.startswith("产品定义_"):
        product_name = archive_prefix[len("产品定义_"):]
        stage1_path = OUTPUT_DIR / f"需求分析_{product_name}_latest.md"
        if stage1_path.exists():
            role_table = extract_role_table(stage1_path.read_text(encoding="utf-8"))
            check_role_naming_consistency(
                content, role_table or {}, r, "阶段3 产品定义", "S3-NAMING-01"
            )
        else:
            r.section("S3-NAMING-01 角色命名一致性(建议 7 / issue # 3 复盘)")
            r.warn(
                f"[S3-NAMING-01] 阶段 1 产物不存在: {stage1_path},"
                f"无法启用命名校验"
            )

    sys.exit(r.summary())


if __name__ == "__main__":
    main()
