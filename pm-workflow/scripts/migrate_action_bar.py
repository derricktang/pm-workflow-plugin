#!/usr/bin/env python3
"""migrate_action_bar.py — S4-28 v2 → v3 自动迁移（旧 3 class + 双重叠加 → .fb-action-bar）。

用法:
  python3 migrate_action_bar.py <prd.html> [<prd2.html> ...]
  python3 migrate_action_bar.py --dry-run <prd.html>   # 仅 diff,不写入
  python3 migrate_action_bar.py --check <prd.html>    # 仅统计待迁移数,不修改

迁移规则（按优先级，先处理最严重的双重叠加）:
  1. 双重 class 叠加（v2 误用 16 处实证）:
     class="...fb-modal-footer...fb-frame-bottom-bar..." → class="...fb-action-bar..."
     class="...fb-frame-bottom-bar...fb-modal-footer..." → class="...fb-action-bar..."
     class="...fb-modal-footer...fb-drawer-footer..." → class="...fb-action-bar..."
     （任两个旧 class 同时出现 → 合并为单一 .fb-action-bar）

  2. 单用旧 class:
     class="...fb-frame-bottom-bar..." → class="...fb-action-bar..."
     class="...fb-modal-footer..." → class="...fb-action-bar..."
     class="...fb-drawer-footer..." → class="...fb-action-bar..."

设计:
  - 替换发生在 class 属性字符串内（不影响其他位置如注释 / docstring）
  - 保留原 class 列表中的其他类（不只删除旧 class，还保留其他类如 'is-visible' 等）
  - 输出 diff + 改动计数 + 提示「重跑 assemble」

零启发式: 仅扫 class 属性字面，无 DOM 语义分析（避免重蹈 S4-28 v1 启发式 5/5 FP 教训）。

详 rule_hard_constraints.md §S4-28 v3 + fb-fallback-manifest.md §3.11。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 旧 3 class（v2 deprecated 别名）
OLD_CLASSES = {
    "fb-frame-bottom-bar",
    "fb-modal-footer",
    "fb-drawer-footer",
}

# 新统一类（v3）
NEW_CLASS = "fb-action-bar"

# 匹配 class="..." 属性（容忍单引号 + 空白）
CLASS_ATTR_RE = re.compile(r'(class\s*=\s*)(["\'])([^"\']*)(\2)')


def migrate_class_list(class_str: str) -> tuple[str, list[str]]:
    """对单个 class="..." 内的 class 列表执行迁移。

    返回 (新 class 字符串, 命中的旧 class 列表)。
    若无旧 class 则原样返回 + 空列表。
    """
    classes = class_str.split()
    matched = [c for c in classes if c in OLD_CLASSES]
    if not matched:
        return class_str, []
    # 移除所有旧 class
    others = [c for c in classes if c not in OLD_CLASSES]
    # 加入新 class（若未已含）
    if NEW_CLASS not in others:
        others.append(NEW_CLASS)
    return " ".join(others), matched


def migrate_html(html: str) -> tuple[str, int, list[tuple[int, str, str]]]:
    """对整个 HTML 文档迁移。

    返回 (新 HTML, 改动数, [(line_num, old, new), ...])。
    """
    changes: list[tuple[int, str, str]] = []
    change_count = 0

    def _sub(m: re.Match) -> str:
        nonlocal change_count
        prefix, quote, class_str, _quote2 = m.group(1), m.group(2), m.group(3), m.group(4)
        new_str, matched = migrate_class_list(class_str)
        if not matched:
            return m.group(0)
        change_count += 1
        # 计算行号
        line_num = html[:m.start()].count("\n") + 1
        old_repr = "+".join(sorted(matched))
        changes.append((line_num, old_repr, NEW_CLASS))
        return f"{prefix}{quote}{new_str}{quote}"

    new_html = CLASS_ATTR_RE.sub(_sub, html)
    return new_html, change_count, changes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S4-28 v2 → v3 自动迁移（旧 3 class → .fb-action-bar）"
    )
    parser.add_argument("files", nargs="+", help="待迁移的 PRD HTML 文件")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅输出 diff（不写入文件）"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="仅统计待迁移数（不修改也不输出 diff）"
    )
    args = parser.parse_args()

    total_changes = 0
    files_modified = 0

    for file_path_str in args.files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"[ERROR] 文件不存在: {file_path}", file=sys.stderr)
            return 1

        html = file_path.read_text(encoding="utf-8")
        new_html, change_count, changes = migrate_html(html)

        if change_count == 0:
            print(f"[OK] {file_path}: 0 处待迁移（已是 v3 或无底栏）")
            continue

        total_changes += change_count
        files_modified += 1

        # 输出 diff 摘要
        print(f"\n[{file_path}] {change_count} 处迁移：")
        # 按 (old → new) 聚合统计
        agg: dict[str, int] = {}
        for ln, old, new in changes:
            agg[old] = agg.get(old, 0) + 1
        for old, n in sorted(agg.items(), key=lambda x: -x[1]):
            print(f"  {n:3d} 处: {old} → {new}")
        # 显示前 5 处具体行号
        print("  前 5 处行号：" + ", ".join(f"L{c[0]}" for c in changes[:5]))
        if len(changes) > 5:
            print(f"  （共 {len(changes)} 处，仅显示前 5 处行号）")

        if args.check:
            continue  # 仅统计，不修改

        if args.dry_run:
            print(f"  [DRY-RUN] 不写入文件")
            continue

        # 实际写入
        file_path.write_text(new_html, encoding="utf-8")
        print(f"  [WRITTEN] 文件已更新")

    # 总结
    print(f"\n═══ 迁移总结 ═══")
    print(f"  扫描文件数: {len(args.files)}")
    print(f"  含迁移文件: {files_modified}")
    print(f"  总迁移处数: {total_changes}")

    if total_changes > 0 and not args.check and not args.dry_run:
        print(f"\n[提示] 文件已更新。若涉及 outputs/prd_*.html，"
              f"建议下次 assemble 时不再覆盖（已落 v3）；"
              f"或在 PM Agent 派发流程中按需 re-assemble。")
        print(f"[提示] 验证：跑 precheck_stage4.py 看 S4-28 v3 deprecated WARN 是否清零。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
