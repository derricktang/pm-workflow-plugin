#!/usr/bin/env python3
"""
structure_check.py — 新对象入库结构齐全性检查

按 `pm-workflow/rules/workflow_maintenance_protocol.md`「新对象入库对照清单」核查 skill / pub 组件
是否符合"必备文件清单"。proj 组件索引段已由 precheck_stage4.py 的
check_proj_index / check_proj_owner 覆盖,本脚本不重复。agent 类型为低频
新增,不机械化。

用法:
    python pm-workflow/scripts/structure_check.py

退出码:
    0 — 全部齐全 (允许 WARN)
    1 — 存在 ERROR (必备文件缺失或登记不一致)

检查项:
    1. skill 三件套:
       - 每个 pm-workflow/skills/<name>/ 必含 SKILL.md + template.md + examples/sample.md
    2. pub 组件登记双向:
       - components/<name>.md (排除 _pending.md / _开头) 在 pub_components_index.md §三 总表中应被引用
       - pub_components_index.md §三 总表中提及的 components/<name>.md 应实际存在
"""

import re
import sys
from pathlib import Path

import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_paths import FRAMEWORK_ROOT, PROJECT_ROOT
SKILLS_DIR = FRAMEWORK_ROOT / "pm-workflow" / "skills"
COMPONENTS_DIR = FRAMEWORK_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "components"
PUB_INDEX = FRAMEWORK_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "pub_components_index.md"


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
        print()
        print("─" * 60)
        print(
            f"通过 {self.passed} | 错误 {len(self.errors)} | 警告 {len(self.warnings)}"
        )
        if self.errors:
            print(f"\n[BLOCK] {len(self.errors)} 项错误:")
            for i, e in enumerate(self.errors, 1):
                print(f"  {i}. {e}")
            return 1
        if self.warnings:
            print(f"\n[PASS-W] 通过,但有 {len(self.warnings)} 项警告。")
        else:
            print("\n[PASS] 新对象入库结构齐全。")
        return 0


# ── 检查 1｜skill 三件套 ──────────────────────────────────────────────────────

REQUIRED_SKILL_FILES = [
    ("SKILL.md", "skill 主入口"),
    ("template.md", "产出模板(供 PM 填写)"),
    ("examples/sample.md", "完整填写示例"),
]


def check_skills(r: Report) -> None:
    r.section("skill 三件套(SKILL.md + template.md + examples/sample.md)")

    if not SKILLS_DIR.exists():
        r.warn(f"skills 目录不存在: {SKILLS_DIR}")
        return

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith("_"))
    if not skill_dirs:
        r.warn("skills 目录为空")
        return

    incomplete = 0
    for sk in skill_dirs:
        missing = []
        for fname, desc in REQUIRED_SKILL_FILES:
            if not (sk / fname).exists():
                missing.append(f"{fname}({desc})")
        if missing:
            r.fail(f"skill [{sk.name}] 缺: {', '.join(missing)}")
            incomplete += 1

    if incomplete == 0:
        r.ok(f"{len(skill_dirs)} 个 skill 全部三件套齐全")

    # SSOT #3 NB-WE-D4：每个 SKILL.md frontmatter 必含 workflow_stage 字段（合法值 meta / stage1-4 / 裸数字 1-4）
    LEGAL_STAGES = {"meta", "stage1", "stage2", "stage3", "stage4", "1", "2", "3", "4"}
    stage_ok = True
    for sk in skill_dirs:
        skill_md = sk / "SKILL.md"
        if not skill_md.exists():
            continue  # 上方已 fail
        text = skill_md.read_text(encoding="utf-8")
        m = re.search(r"^workflow_stage:\s*(\S+)\s*$", text, re.MULTILINE)
        if not m:
            r.fail(f"skill [{sk.name}] SKILL.md frontmatter 缺 workflow_stage 字段（合法值 {sorted(LEGAL_STAGES)}）")
            stage_ok = False
            continue
        stage = m.group(1).strip().strip('"\'')
        if stage not in LEGAL_STAGES:
            r.fail(f"skill [{sk.name}] workflow_stage={stage!r} 非法（合法值 {sorted(LEGAL_STAGES)}）")
            stage_ok = False
    if stage_ok:
        r.ok(f"{len(skill_dirs)} 个 skill 全部 workflow_stage 字段合法（SSOT #3）")

    # SSOT #5 NB-WE-D5：SKILL.md / template.md 中提及的 W 步前缀格式（W?-N）大小写规范
    # 检测项：模板 / 示例中出现的 atomic step 前缀,验证形如 `[X]-N` 大写字母 + 数字
    prefix_ok = True
    bad_prefixes: list[tuple[str, str]] = []  # (file, bad_token)
    PREFIX_RE = re.compile(r"\[?\s*\b([a-zA-Z]{1,4})-(\d+)\b\s*\]?")  # 宽松匹配
    for sk in skill_dirs:
        for fname, _desc in REQUIRED_SKILL_FILES:
            f = sk / fname
            if not f.exists():
                continue
            text = f.read_text(encoding="utf-8")
            for m in PREFIX_RE.finditer(text):
                prefix = m.group(1)
                # 排除常见非 W 步前缀（HTTP-、E-、L1-、A-D1 等已在其他枚举）
                if prefix.lower() in {"http", "v", "p", "h", "m", "n", "e", "l", "s", "g"}:
                    continue
                if prefix in ("WE", "TS", "BL", "IC", "SR", "HC", "T", "X"):  # 已知合法前缀
                    continue
                # 排除示例文字（file-N / step-N / task-N / item-N 等通用名）
                if prefix.lower() in {"file", "step", "task", "item", "row", "col", "case", "test", "stage", "type", "id", "no"}:
                    continue
                # 仅当含小写字母时报警（W 步前缀应全大写）
                if not prefix.isupper():
                    bad_prefixes.append((str(f.relative_to(FRAMEWORK_ROOT)), m.group(0)))
                    prefix_ok = False
    if bad_prefixes:
        r.fail(f"SKILL/template 中含非规范 W 步前缀（应全大写,如 WE-1）: {bad_prefixes[:5]}")
    elif prefix_ok:
        r.ok(f"{len(skill_dirs)} 个 skill 三件套 W 步前缀格式合规（SSOT #5）")


# ── 检查 2｜pub 组件登记双向一致性 ─────────────────────────────────────────────

def _collect_component_files() -> set[str]:
    """返回 components/ 目录下所有 <name>.md 的 name 集合(排除 _pending / _ 开头)。"""
    if not COMPONENTS_DIR.exists():
        return set()
    return {
        p.stem for p in COMPONENTS_DIR.glob("*.md")
        if not p.stem.startswith("_")
    }


def _collect_index_references() -> tuple[set[str], dict[str, list[str]]]:
    """从 pub_components_index.md 解析:
    - 总表"详情"列引用的 components/<name>.md 集合
    - 每个 components/<name>.md 在哪些位置被提及(行号清单)
    """
    if not PUB_INDEX.exists():
        return set(), {}

    text = PUB_INDEX.read_text(encoding="utf-8")
    refs: set[str] = set()
    locations: dict[str, list[str]] = {}

    # 匹配 "components/<name>.md" 形式的引用
    for m in re.finditer(r"\bcomponents/([\w-]+)\.md\b", text):
        name = m.group(1)
        refs.add(name)
        # 反推所在行号
        line_no = text.count("\n", 0, m.start()) + 1
        locations.setdefault(name, []).append(f"L{line_no}")

    return refs, locations


def check_pub_components(r: Report) -> None:
    r.section("pub 组件登记双向(components/*.md ↔ pub_components_index §三)")

    if not COMPONENTS_DIR.exists():
        r.warn(f"components 目录不存在: {COMPONENTS_DIR}")
        return
    if not PUB_INDEX.exists():
        r.fail(f"pub_components_index.md 不存在: {PUB_INDEX}")
        return

    component_files = _collect_component_files()
    index_refs, locations = _collect_index_references()

    # 方向 1: components/<name>.md → pub_components_index 应有引用
    only_files = component_files - index_refs
    if only_files:
        for name in sorted(only_files):
            r.fail(
                f"components/{name}.md 存在但 pub_components_index.md 中未引用——"
                f"PM 检索时找不到该组件的详情位置"
            )

    # 方向 2: pub_components_index 引用 → components/<name>.md 应存在
    only_index = index_refs - component_files
    if only_index:
        for name in sorted(only_index):
            locs = ", ".join(locations.get(name, []))
            r.fail(
                f"pub_components_index.md 在 {locs} 引用 components/{name}.md "
                f"但文件不存在——PM 按引用打开会 404"
            )

    if not only_files and not only_index and component_files:
        r.ok(
            f"pub 组件登记双向一致 — {len(component_files)} 个 components/*.md 全部"
            f"在索引登记 + 无悬空引用"
        )

    # 警告:components 目录虽然有文件但 _ 开头(如 _pending.md)被跳过
    pending_count = sum(1 for p in COMPONENTS_DIR.glob("*.md") if p.stem.startswith("_"))
    if pending_count:
        r.warn(
            f"{pending_count} 个 _ 前缀文件(如 _pending.md)已跳过本核查——"
            f"它们是占位/暂存文件,不参与 pub 索引登记;若已升级为正式组件,请重命名"
        )


# ── 检查 3｜fb-fallback-manifest.md anchor 完整性 ─────────────────────────────


MANIFEST_PATH = FRAMEWORK_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "fb-fallback-manifest.md"


def check_manifest_anchors(r: Report) -> None:
    """SSOT #2 延伸 — fb-fallback-manifest.md anchor 系统三向一致性。

    校验：
    1. 实际 FB-MODEL anchor 集合（line 中 `<!-- [FB-MODEL: xxx] -->` 注释）
    2. 顶部「完整 anchor 清单」表中的 id 集合
    3. 派发说明 agent_dispatch_protocol.md 中声明的 21 个 anchor 数量
    三方应一致；任一漂移即 FAIL,防止 PM 检索 SOP 与实际 anchor 错位。
    """
    r.section("fb-fallback-manifest.md anchor 完整性（SSOT #2 延伸）")

    if not MANIFEST_PATH.exists():
        r.warn(f"manifest 不存在: {MANIFEST_PATH}")
        return

    text = MANIFEST_PATH.read_text(encoding="utf-8")

    # 1. 实际 anchor（排除 SOP 段说明性引用——通过位置过滤：仅扫 `## 1.` 以下章节内的 anchor）
    sop_end_pat = re.compile(r"^## 1\. 原子组件", re.MULTILINE)
    sop_end = sop_end_pat.search(text)
    actual_text = text[sop_end.start():] if sop_end else text
    actual_anchors = re.findall(r"<!--\s*\[FB-MODEL:\s*([\w-]+)\s*\]\s*-->", actual_text)
    actual_set = set(actual_anchors)

    # 2. 顶部清单（| 章节 | `id` | 用例 | 表格中的 ` 包裹 id）
    list_block_pat = re.compile(r"### 完整 anchor 清单.*?(?=^>|\Z)", re.MULTILINE | re.DOTALL)
    list_block = list_block_pat.search(text)
    if not list_block:
        r.fail("manifest 缺「完整 anchor 清单」段")
        return
    list_ids: set[str] = set()
    for m in re.finditer(r"\|\s*[^|]+\|\s*`([\w-]+)`(?:\s*/\s*`([\w-]+)`)?(?:\s*/\s*`([\w-]+)`)?\s*\|", list_block.group(0)):
        for g in m.groups():
            if g:
                list_ids.add(g)

    # 3. 派发说明 agent_dispatch_protocol 中声明数（仅校验 21 这个数字字面）
    DISPATCH_PATH = FRAMEWORK_ROOT / "pm-workflow" / "rules" / "agent_dispatch_protocol.md"
    expected_count = 21
    if DISPATCH_PATH.exists():
        dispatch_text = DISPATCH_PATH.read_text(encoding="utf-8")
        # 形如 "21 个 anchor"
        m_n = re.search(r"(\d+)\s*个\s*anchor", dispatch_text)
        if m_n:
            expected_count = int(m_n.group(1))

    # 对比
    actual_unique = len(actual_set)
    list_count = len(list_ids)

    only_actual = actual_set - list_ids
    only_list = list_ids - actual_set

    if only_actual or only_list:
        if only_actual:
            r.fail(
                f"manifest 实际 anchor 中含清单未列：{sorted(only_actual)}"
            )
        if only_list:
            r.fail(
                f"manifest 顶部清单声明的 id 在实际 anchor 中未出现：{sorted(only_list)}"
            )
        return

    if actual_unique != expected_count:
        r.fail(
            f"manifest 实际 anchor 数 {actual_unique} ≠ agent_dispatch_protocol 声明 {expected_count}"
            f"（清单段也是 {list_count} 个 id,但实际 anchor 集合不匹配 expected）"
        )
        return

    r.ok(
        f"manifest anchor 三向一致：实际 {actual_unique} 个 = 清单段 {list_count} 个 = "
        f"派发说明 {expected_count} 个"
    )


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main() -> int:
    print("structure_check.py — 新对象入库结构齐全性检查")
    print(f"仓库: {FRAMEWORK_ROOT}")

    r = Report()
    check_skills(r)
    check_pub_components(r)
    check_manifest_anchors(r)

    print(f"\n备注: proj 组件索引段(A/B/C/D 4 表)的齐全性由 precheck_stage4.py 的")
    print(f"      check_proj_index + check_proj_owner 在阶段 4 Step 6.5 自动核查,本脚本不重复。")
    print(f"      agent 类型新增为低频操作,未机械化;参 `pm-workflow/rules/workflow_maintenance_protocol.md`「新对象入库对照清单」人工核对。")

    return r.summary()


if __name__ == "__main__":
    sys.exit(main())
