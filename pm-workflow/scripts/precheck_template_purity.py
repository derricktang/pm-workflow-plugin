#!/usr/bin/env python3
"""precheck_template_purity.py — 模板纯净度机械兜底

模块定位：
    L2 维护层防御工具。扫 5 个「模板类」文件中是否含"整改原因注释"污染
    （日期 / issue / NB / retro / 复盘根因 / 建议 N 落地 等运维痕迹字面）。
    这些注释应归档于 git log / process_record/issues/*_analyzed.md,
    不应污染模板，否则 PM 阶段 4 fork prd_template.html 时连带把维护历史
    复制进 outputs/prd_*.html,污染产品交付物。

SSOT 真源：
    pm-workflow/rules/workflow_maintenance_protocol.md「模板纯净度红线」节
    （列出 5 个模板文件 + 3 条红线 + 白名单原则）

集成点：
    - pm-workflow/scripts/hooks/pre-commit 调用本脚本(commit 时硬拦截)
    - workflow-evolution skill template.md Step 7 SSOT 同步清单第 8 项
      "模板纯净度复检"运行时人工核查
    - 直接命令行运行:`python3 precheck_template_purity.py`,非 0 退出码表 FAIL

退出码：
    0 — PASS（无污染）
    1 — FAIL（命中污染，输出行号 + 字面）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]

# 代码类 L2 文件清单（与 workflow_maintenance_protocol.md「模板纯净度红线」+
# 「通用 L2 注释纯净度准则」§代码类 [Must] 对齐）
# 分类:
# - 5 个模板类:PM 复制到 outputs 的 fork 起点
# - 1 个 CSS 真源类(fb-fallback.css):assemble.py 注入到 outputs/prd.html <style> 顶部,
#   PM 不直接读但 CSS 渲染影响产物。同属代码类,运维痕迹会污染产物 / 跨文件 commit hash
#   引用易腐败。
TEMPLATE_FILES = [
    "pm-workflow/rules/prd_template.html",
    "pm-workflow/rules/tmpl_需求分析.md",
    "pm-workflow/rules/tmpl_功能规划.md",
    "pm-workflow/rules/tmpl_产品定义.md",
    "pm-workflow/rules/task_card_template.md",
    "pm-workflow/rules/bujue-design-system/fb-fallback.css",
]

# 污染模式（命中即 FAIL）
POLLUTION_PATTERNS = [
    # 日期字面（YYYY-MM-DD 或 YYYY-MM-DD_HHMM）— 避开模板占位 [YYYY-MM-DD]
    (r"(?<!\[)20\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])", "日期字面"),
    # issue 引用
    (r"issue\s*#\s*\d+", "issue # N 引用"),
    (r"issue\s+20\d{2}-\d{2}-\d{2}", "issue 日期引用"),
    # NB 编号
    (r"NB-WE-\d+", "NB-WE-NN 编号"),
    (r"NB-阶段[0-9]+-[A-Z]?\d*", "NB-阶段 编号"),
    # retro 引用
    (r"/retro\s+20\d{2}", "/retro 引用"),
    # 复盘语义
    (r"复盘根因", "复盘根因"),
    # 建议编号
    (r"建议\s*\d+\s*(落地|配套|预防侧)", "建议 N 落地"),
]

# 白名单豁免（这些字面允许出现）
WHITELIST_PATTERNS = [
    # 模板占位 [YYYY-MM-DD]（PM 填日期处）
    r"\[YYYY-MM-DD\]",
    # 变更记录表头 / schema 版本号示意
    r"v\d+\.\d+",
    # 文件名中的日期字面（如 2026-05-11_1925.md 出现在路径引用）— 仅当行含 .md 路径
    # 这种豁免在 line 级处理:若该行同时含 .md 路径,则忽略日期命中
]

# ── 报告 ─────────────────────────────────────────────────────────────────────


class Report:
    def __init__(self) -> None:
        self.violations: list[tuple[str, int, str, str]] = []  # (file, line_no, pattern_name, snippet)
        self.files_scanned: int = 0
        self.files_clean: int = 0

    def violation(self, file: str, line_no: int, pattern_name: str, snippet: str) -> None:
        self.violations.append((file, line_no, pattern_name, snippet))

    def file_clean(self) -> None:
        self.files_clean += 1

    def file_scanned(self) -> None:
        self.files_scanned += 1

    @property
    def exit_code(self) -> int:
        return 1 if self.violations else 0


def is_whitelisted_line(line: str) -> bool:
    """整行豁免判断（仅当行同时含路径引用时,日期字面被视为引用而非污染）。"""
    # 行含 .md / .html / .py 路径引用时,行内日期视为合规引用
    if re.search(r"\.(md|html|py|css|json|sh)\b", line):
        # 但仍需排除"修复 / 加固 / 升级"等动词 — 这些是真污染
        if not re.search(r"修复|加固|升级|落地|补强|调整|复盘", line):
            return True
    # 模板占位 / 版本号
    for pat in WHITELIST_PATTERNS:
        if re.search(pat, line):
            return True
    return False


def scan_file(file_path: Path, r: Report) -> None:
    r.file_scanned()
    if not file_path.exists():
        print(f"[WARN] 模板文件不存在,跳过: {file_path}", file=sys.stderr)
        return
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rel = str(file_path.relative_to(REPO_ROOT))
    hits = 0
    for line_no, line in enumerate(lines, 1):
        if is_whitelisted_line(line):
            continue
        for pat, name in POLLUTION_PATTERNS:
            if re.search(pat, line):
                snippet = line.strip()[:120]
                r.violation(rel, line_no, name, snippet)
                hits += 1
    if hits == 0:
        r.file_clean()


# ── 主入口 ──────────────────────────────────────────────────────────────────


def main() -> int:
    r = Report()

    print("precheck_template_purity.py — 模板纯净度机械兜底")
    print(f"  扫描根目录: {REPO_ROOT}")
    print(f"  目标模板:   {len(TEMPLATE_FILES)} 个")
    print()

    for rel in TEMPLATE_FILES:
        scan_file(REPO_ROOT / rel, r)

    if not r.violations:
        print(f"[PASS] 所有 {r.files_scanned} 个模板文件纯净（无整改原因注释污染）")
        return 0

    # 按文件分组输出
    from collections import defaultdict
    by_file: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for file, line_no, name, snippet in r.violations:
        by_file[file].append((line_no, name, snippet))

    print(f"[FAIL] 检测到 {len(r.violations)} 处模板污染（违反 workflow_maintenance_protocol.md 模板纯净度红线）：")
    print()
    for file, items in by_file.items():
        print(f"  📄 {file} ({len(items)} 处)")
        for line_no, name, snippet in items[:8]:  # 每文件最多展示 8 条
            print(f"    L{line_no} [{name}]: {snippet}")
        if len(items) > 8:
            print(f"    ...（其余 {len(items) - 8} 处省略,见完整扫描）")
        print()

    print("修复方向：")
    print("  - 删时间戳 / issue 号 / NB 号 / retro 引用 / 复盘根因 / 建议 N 落地 等运维痕迹字面")
    print("  - 保留对'规则是什么 / 为什么这样写'的纯语义说明")
    print("  - 详见 workflow_maintenance_protocol.md「模板纯净度红线」节")
    return 1


if __name__ == "__main__":
    sys.exit(main())
