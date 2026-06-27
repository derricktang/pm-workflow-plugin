"""test_migrate_frame_cell.py — 迁移脚本单元测试

覆盖：
- 基本多端转换（手机+桌面，含/不含 note）
- 单端 / 无 bar 不变（已是新 DOM 或单端帧）
- 数量不匹配 → 跳过 + skip_reason
- 嵌套 div（在 frame 内）不被误判为 frame-card 子元素
- 整文件多 frame-card 实例
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保能 import scripts/migrate_frame_cell（pytest 在 pm-workflow/scripts/tests/ 内运行）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import migrate_frame_cell as mfc


# ── 基础转换 ──────────────────────────────────────────────────────────────


def test_basic_two_platform_no_note():
    """两端（手机+桌面）无差异说明 → 转换为 2 个 frame-cell。"""
    old = (
        '<div class="frame-card">\n'
        '  <div class="frame-platforms-bar">\n'
        '    <div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>\n'
        '    <div class="frame-platform-item"><span class="frame-platform-tag">桌面</span></div>\n'
        '  </div>\n'
        '  <div class="frame-wrapper">\n'
        '    <div class="phone-frame">PHONE</div>\n'
        '    <div class="desktop-frame">DESKTOP</div>\n'
        '  </div>\n'
        '</div>'
    )
    new, changed, reason = mfc.migrate_frame_card(old)
    assert changed is True
    assert reason is None
    assert new.count('class="frame-cell"') == 2
    assert 'frame-platforms-bar' not in new
    # cell 内顺序：第 1 个 cell 含手机 item + phone-frame
    assert new.index('手机') < new.index('PHONE')
    assert new.index('PHONE') < new.index('桌面')
    assert new.index('桌面') < new.index('DESKTOP')


def test_three_platform_with_note():
    """三端含 note → 3 个 cell，note 跟随 item 进入 cell。"""
    old = (
        '<div class="frame-card">'
        '<div class="frame-platforms-bar">'
        '<div class="frame-platform-item"><span class="frame-platform-tag">桌面 Web</span></div>'
        '<div class="frame-platform-item"><span class="frame-platform-tag">APP 手机</span></div>'
        '<div class="frame-platform-item"><span class="frame-platform-tag">APP Pad</span>'
        '<p class="frame-platform-note">布局同桌面，尺寸适配 1376×1032</p></div>'
        '</div>'
        '<div class="frame-wrapper">'
        '<div class="desktop-frame">D</div>'
        '<div class="phone-frame">P</div>'
        '<div class="tablet-frame">T</div>'
        '</div>'
        '</div>'
    )
    new, changed, reason = mfc.migrate_frame_card(old)
    assert changed is True
    assert reason is None
    assert new.count('class="frame-cell"') == 3
    assert 'frame-platforms-bar' not in new
    # note 跟着 APP Pad item 进入第 3 个 cell（同 cell 内 tablet-frame 之前）
    note_pos = new.index('1376×1032')
    pad_pos = new.index('APP Pad')
    tablet_pos = new.index('>T<')
    assert pad_pos < note_pos < tablet_pos


# ── 跳过场景 ──────────────────────────────────────────────────────────────


def test_single_platform_no_bar_unchanged():
    """单端帧（无 bar，wrapper 直接含 frame）→ 不变。"""
    old = (
        '<div class="frame-card">'
        '<div class="frame-wrapper">'
        '<div class="phone-frame">single</div>'
        '</div>'
        '</div>'
    )
    new, changed, reason = mfc.migrate_frame_card(old)
    assert changed is False
    assert reason is None
    assert new == old


def test_already_new_dom_unchanged():
    """已是新 DOM（含 frame-cell 嵌套）→ 不变。"""
    old = (
        '<div class="frame-card">'
        '<div class="frame-wrapper">'
        '<div class="frame-cell">'
        '<div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>'
        '<div class="phone-frame">P</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    new, changed, reason = mfc.migrate_frame_card(old)
    assert changed is False
    assert reason is None
    assert new == old


def test_count_mismatch_skipped_with_reason():
    """bar items 数 ≠ wrapper frames 数 → 跳过 + reason。"""
    old = (
        '<div class="frame-card">'
        '<div class="frame-platforms-bar">'
        '<div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>'
        '<div class="frame-platform-item"><span class="frame-platform-tag">桌面</span></div>'
        '<div class="frame-platform-item"><span class="frame-platform-tag">平板</span></div>'
        '</div>'
        '<div class="frame-wrapper">'
        '<div class="phone-frame">P</div>'
        '<div class="desktop-frame">D</div>'
        '</div>'
        '</div>'
    )
    new, changed, reason = mfc.migrate_frame_card(old)
    assert changed is False
    assert reason is not None
    assert "3" in reason and "2" in reason
    assert new == old


# ── 边界 / 嵌套场景 ──────────────────────────────────────────────────────


def test_nested_div_in_frame_not_confused():
    """frame 内部含嵌套 div（按钮、卡片等）不被误判为 frame-card 直接子。"""
    old = (
        '<div class="frame-card">'
        '<div class="frame-platforms-bar">'
        '<div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>'
        '</div>'
        '<div class="frame-wrapper">'
        '<div class="phone-frame">'
        '<div class="fb-card"><div class="fb-card-body">'
        '<div class="fb-tag">嵌套深</div>'
        '</div></div>'
        '</div>'
        '</div>'
        '</div>'
    )
    new, changed, reason = mfc.migrate_frame_card(old)
    # 单 platform-item / 单 frame，仍触发迁移（数量匹配）
    assert changed is True
    assert reason is None
    assert new.count('class="frame-cell"') == 1
    # 嵌套结构完整保留
    assert 'fb-card-body' in new
    assert '嵌套深' in new


def test_migrate_html_multi_cards():
    """整文档含 ≥ 2 个 frame-card → 全部独立处理。"""
    html = (
        '<html><body>'
        '<section id="A">'
        '<div class="frame-card">'
        '<div class="frame-platforms-bar">'
        '<div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>'
        '<div class="frame-platform-item"><span class="frame-platform-tag">桌面</span></div>'
        '</div>'
        '<div class="frame-wrapper">'
        '<div class="phone-frame">A_P</div>'
        '<div class="desktop-frame">A_D</div>'
        '</div>'
        '</div>'
        '</section>'
        '<section id="B">'
        '<div class="frame-card">'
        '<div class="frame-wrapper">'
        '<div class="phone-frame">B_single</div>'
        '</div>'
        '</div>'
        '</section>'
        '</body></html>'
    )
    new_html, total, migrated, reasons = mfc.migrate_html(html)
    assert total == 2
    assert migrated == 1
    assert reasons == []
    assert 'frame-platforms-bar' not in new_html
    assert new_html.count('class="frame-cell"') == 2  # 仅 A 段的 2 cell
    # B 段单端不变
    assert 'B_single' in new_html


def test_dry_run_does_not_write(tmp_path):
    """--dry-run 不写文件，但报告迁移数。"""
    f = tmp_path / "prd_test.html"
    original = (
        '<div class="frame-card">'
        '<div class="frame-platforms-bar">'
        '<div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>'
        '<div class="frame-platform-item"><span class="frame-platform-tag">桌面</span></div>'
        '</div>'
        '<div class="frame-wrapper">'
        '<div class="phone-frame">P</div>'
        '<div class="desktop-frame">D</div>'
        '</div>'
        '</div>'
    )
    f.write_text(original, encoding="utf-8")

    total, migrated, modified, reasons = mfc.process_file(f, dry_run=True)
    assert total == 1
    assert migrated == 1
    assert modified is True
    assert reasons == []
    # 文件内容未变（dry-run）
    assert f.read_text(encoding="utf-8") == original


def test_in_place_writes(tmp_path):
    """非 dry-run 写入新内容。"""
    f = tmp_path / "prd_test.html"
    f.write_text(
        '<div class="frame-card">'
        '<div class="frame-platforms-bar">'
        '<div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>'
        '</div>'
        '<div class="frame-wrapper">'
        '<div class="phone-frame">P</div>'
        '</div>'
        '</div>',
        encoding="utf-8",
    )
    total, migrated, modified, reasons = mfc.process_file(f, dry_run=False)
    assert migrated == 1
    assert modified is True
    new = f.read_text(encoding="utf-8")
    assert 'frame-platforms-bar' not in new
    assert 'class="frame-cell"' in new
