#!/usr/bin/env python3
"""migrate_frame_cell.py — outputs/prd_*.html 旧 frame-platforms-bar 兄弟 flex →
新 .frame-cell 嵌套结构迁移脚本。

旧 DOM：
    frame-card
    ├─ frame-platforms-bar
    │  └─ frame-platform-item × N (含 tag + 可选 note)
    └─ frame-wrapper
       └─ phone-frame / desktop-frame / ... × M (M 应 = N)

新 DOM：
    frame-card
    └─ frame-wrapper
       └─ frame-cell × N
          ├─ frame-platform-item (含 tag + 可选 note)
          └─ phone-frame / desktop-frame / ...

按 prd_template.html L554-577 + prd_expression_standard.md §四 区块 B DOM 嵌套规范，
.frame-cell 父子嵌套取代旧 bar/wrapper 兄弟 flex + JS sync 校正方案——CSS-only，
零 forced reflow。

用法：
    python3 migrate_frame_cell.py <prd.html>             # 原地迁移单文件
    python3 migrate_frame_cell.py <prd.html> --dry-run   # 预览不写
    python3 migrate_frame_cell.py <dir>                  # 递归处理目录下 *.html

退出码：
    0 — 全部处理完成（含 dry-run 与无改动）
    1 — 单个文件处理失败 / 数量不匹配（请人工核查）
    2 — 路径不存在 / 参数错误
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ── 正则与常量 ────────────────────────────────────────────────────────────────

DIV_OPEN_RE = re.compile(r"<div\b([^>]*)>", re.IGNORECASE)
DIV_CLOSE_RE = re.compile(r"</div\s*>", re.IGNORECASE)
CLASS_RE = re.compile(r'class\s*=\s*"([^"]*)"', re.IGNORECASE)

PLATFORM_FRAME_CLASSES = {
    "phone-frame", "tablet-frame", "desktop-frame", "miniprogram-frame", "h5-frame",
}


def _div_classes(tag_html: str) -> set[str]:
    """从 <div ...> 开标签字符串提取 class 集合。"""
    m = CLASS_RE.search(tag_html)
    return set(m.group(1).split()) if m else set()


def _find_balanced_div_end(html: str, open_start: int) -> int | None:
    """已知 <div ...> 开标签起始 offset，找匹配 </div> 结束 offset（含闭标签）。

    用 stack-based depth counter 处理嵌套 div。返回 None 表示不平衡。
    """
    m_open = DIV_OPEN_RE.match(html, open_start)
    if not m_open:
        return None
    pos = m_open.end()
    depth = 1
    while pos < len(html) and depth > 0:
        n_open = DIV_OPEN_RE.search(html, pos)
        n_close = DIV_CLOSE_RE.search(html, pos)
        if not n_close:
            return None
        if n_open and n_open.start() < n_close.start():
            depth += 1
            pos = n_open.end()
        else:
            depth -= 1
            pos = n_close.end()
    return pos if depth == 0 else None


def _find_direct_child_divs(inner_html: str) -> list[tuple[int, int, str]]:
    """找 inner_html 中所有直接子 <div> 元素的 (start, end, attrs_str) 列表。

    跳过嵌套 div（仅直接子级），用 stack-based 匹配。
    """
    children: list[tuple[int, int, str]] = []
    pos = 0
    while pos < len(inner_html):
        m_open = DIV_OPEN_RE.search(inner_html, pos)
        if not m_open:
            break
        # 找匹配闭标签
        depth = 1
        scan = m_open.end()
        end_pos: int | None = None
        while scan < len(inner_html) and depth > 0:
            n_open = DIV_OPEN_RE.search(inner_html, scan)
            n_close = DIV_CLOSE_RE.search(inner_html, scan)
            if not n_close:
                break
            if n_open and n_open.start() < n_close.start():
                depth += 1
                scan = n_open.end()
            else:
                depth -= 1
                scan = n_close.end()
                if depth == 0:
                    end_pos = scan
                    break
        if end_pos is None:
            break
        children.append((m_open.start(), end_pos, m_open.group(1)))
        pos = end_pos
    return children


# ── 单 frame-card 迁移 ────────────────────────────────────────────────────────


def migrate_frame_card(card_html: str) -> tuple[str, bool, str | None]:
    """迁移单个 frame-card 块（旧 bar+wrapper → 新 wrapper+cell）。

    Args:
        card_html: 完整 <div class="frame-card">...</div> 字符串

    Returns:
        (migrated_html, was_changed, skip_reason)
        was_changed = False 时:
          - skip_reason = None:    已是新 DOM 或单端无需迁移
          - skip_reason = "..."    数量不匹配 / 结构异常等待人工
    """
    m_card_open = DIV_OPEN_RE.match(card_html)
    if not m_card_open or "frame-card" not in _div_classes(m_card_open.group(0)):
        return card_html, False, None

    card_inner_start = m_card_open.end()
    if not card_html.rstrip().endswith("</div>"):
        return card_html, False, "frame-card 未正确闭合"
    card_inner_end = card_html.rfind("</div>")
    inner = card_html[card_inner_start:card_inner_end]

    children = _find_direct_child_divs(inner)
    # 找 bar + wrapper（位置不一定相邻 — 可能中间有空白节点，但都是直接子 div）
    bar_idx: int | None = None
    wrapper_idx: int | None = None
    for idx, (_s, _e, attrs) in enumerate(children):
        cls = _div_classes(f"<div {attrs}>")
        if "frame-platforms-bar" in cls:
            bar_idx = idx
        elif "frame-wrapper" in cls:
            wrapper_idx = idx

    # 已是新 DOM（无 bar，仅 wrapper）→ 不需迁移
    if bar_idx is None:
        return card_html, False, None

    if wrapper_idx is None:
        return card_html, False, "frame-card 有 bar 但无 wrapper"

    bar_s, bar_e, _ = children[bar_idx]
    wrap_s, wrap_e, _ = children[wrapper_idx]

    # 提取 bar 内 platform-items
    bar_full = inner[bar_s:bar_e]
    m_bar_open = DIV_OPEN_RE.match(bar_full)
    if not m_bar_open:
        return card_html, False, "bar 开标签解析失败"
    bar_inner = bar_full[m_bar_open.end():bar_full.rfind("</div>")]
    bar_children = _find_direct_child_divs(bar_inner)
    platform_items: list[str] = []
    for s, e, attrs in bar_children:
        if "frame-platform-item" in _div_classes(f"<div {attrs}>"):
            platform_items.append(bar_inner[s:e])

    # 提取 wrapper 内 frames
    wrap_full = inner[wrap_s:wrap_e]
    m_wrap_open = DIV_OPEN_RE.match(wrap_full)
    if not m_wrap_open:
        return card_html, False, "wrapper 开标签解析失败"
    wrap_inner = wrap_full[m_wrap_open.end():wrap_full.rfind("</div>")]
    wrap_children = _find_direct_child_divs(wrap_inner)
    frames: list[str] = []
    for s, e, attrs in wrap_children:
        if _div_classes(f"<div {attrs}>") & PLATFORM_FRAME_CLASSES:
            frames.append(wrap_inner[s:e])

    # 校验数量
    if len(platform_items) != len(frames):
        return card_html, False, (
            f"数量不匹配 — bar items {len(platform_items)} ≠ wrapper frames {len(frames)}"
        )
    if not frames:
        return card_html, False, None  # 空 wrapper，跳过

    # 重组：删除 bar，wrapper 内重写为 cells
    cells = [
        f'<div class="frame-cell">\n{item}\n{frame}\n</div>'
        for item, frame in zip(platform_items, frames)
    ]
    new_wrapper_inner = "\n" + "\n".join(cells) + "\n"
    new_wrapper = f'<div class="frame-wrapper">{new_wrapper_inner}</div>'
    new_card_inner = "\n" + new_wrapper + "\n"
    new_card = m_card_open.group(0) + new_card_inner + "</div>"
    return new_card, True, None


# ── 整文件迁移 ───────────────────────────────────────────────────────────────


def migrate_html(html: str) -> tuple[str, int, int, list[str]]:
    """扫描 HTML 字符串中所有 frame-card，逐个迁移。

    Returns:
        (migrated_html, total_cards, migrated_count, skip_reasons)
    """
    out: list[str] = []
    pos = 0
    total = 0
    migrated = 0
    skip_reasons: list[str] = []

    while pos < len(html):
        m = DIV_OPEN_RE.search(html, pos)
        if not m:
            out.append(html[pos:])
            break
        if "frame-card" not in _div_classes(m.group(0)):
            out.append(html[pos:m.end()])
            pos = m.end()
            continue

        end = _find_balanced_div_end(html, m.start())
        if end is None:
            out.append(html[pos:])
            break

        card_html = html[m.start():end]
        total += 1
        new_card, changed, reason = migrate_frame_card(card_html)
        if changed:
            migrated += 1
        elif reason:
            skip_reasons.append(reason)

        out.append(html[pos:m.start()])
        out.append(new_card)
        pos = end

    return "".join(out), total, migrated, skip_reasons


def process_file(path: Path, dry_run: bool = False) -> tuple[int, int, bool, list[str]]:
    """处理单个 .html 文件。Returns (total, migrated, was_modified, skip_reasons)。"""
    html = path.read_text(encoding="utf-8")
    new_html, total, migrated, reasons = migrate_html(html)
    modified = new_html != html
    if modified and not dry_run:
        path.write_text(new_html, encoding="utf-8")
    return total, migrated, modified, reasons


# ── CLI ──────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="迁移 outputs/prd_*.html: frame-platforms-bar 兄弟 flex → .frame-cell 嵌套",
    )
    ap.add_argument("path", help="待处理 *.html 文件 或 目录（递归处理 *.html）")
    ap.add_argument("--dry-run", action="store_true", help="预览不写文件")
    args = ap.parse_args(argv)

    p = Path(args.path)
    if not p.exists():
        print(f"❌ 路径不存在: {p}", file=sys.stderr)
        return 2

    files = [p] if p.is_file() else sorted(p.rglob("*.html"))
    if not files:
        print(f"⚠️  目录无 *.html: {p}", file=sys.stderr)
        return 0

    total_files = 0
    total_modified = 0
    total_cards = 0
    total_migrated = 0
    has_skip = False
    for f in files:
        cards, mig, modified, reasons = process_file(f, args.dry_run)
        total_files += 1
        total_cards += cards
        total_migrated += mig
        if modified:
            total_modified += 1
            tag = "[DRY-RUN]" if args.dry_run else "[MIGRATED]"
            print(f"{tag} {f}: frame-card {cards} 个 / 迁移 {mig} 个")
        if reasons:
            has_skip = True
            print(f"  ⚠️  {f}: 跳过 {len(reasons)} 个 frame-card，需人工核查：")
            for r in reasons[:5]:
                print(f"      - {r}")
            if len(reasons) > 5:
                print(f"      - ... 共 {len(reasons)} 处")

    print()
    print(
        f"汇总: {total_files} 文件 / frame-card 总 {total_cards} / 迁移 {total_migrated} / "
        f"修改 {total_modified} 文件"
    )
    if args.dry_run:
        print("(--dry-run 模式，未写盘)")
    return 1 if has_skip else 0


if __name__ == "__main__":
    sys.exit(main())
