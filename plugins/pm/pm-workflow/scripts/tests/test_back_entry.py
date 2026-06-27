"""测试 S4-35 移动端次级页面返回入口完整性（SSOT 双锚 #45，item 2① 配套）。

零启发式结构校验，覆盖：
- 0 命中（无 .fb-navbar）→ OK（下游未迁移属正常）
- 合法 navbar（移动类 frame 直接子层 + 含 .fb-nav-back）→ OK
- navbar 放错层（父非移动类 frame）→ WARN
- navbar 缺 .fb-nav-back 返回入口 → WARN
- 既放错层又缺 back → 两条 WARN
- back 入口嵌套在更深子树仍能识别
- desktop-frame 内 navbar → WARN（桌面用 sidebar，不属移动类 PARENT_OK）
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from precheck_stage4 import Report, check_back_entry


def _run(html: str) -> Report:
    r = Report()
    check_back_entry(html, r)
    return r


# ── 0 命中 ────────────────────────────────────────────────────────────────────


def test_no_navbar_ok():
    """无 .fb-navbar → OK（下游未迁移，非 bug）。"""
    html = '<div class="phone-frame"><div class="content">内容</div></div>'
    r = _run(html)
    assert len(r.errors) == 0 and len(r.warnings) == 0 and r.passed == 1


# ── 合法 navbar ───────────────────────────────────────────────────────────────


def test_valid_navbar_ok():
    """移动类 frame 直接子层 + 含 .fb-nav-back → OK。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar">'
        '    <span class="fb-nav-back" data-tp="M01-P01-T01">←</span>'
        '    <span class="fb-nav-title">详情</span>'
        '    <span class="fb-nav-action"></span>'
        '  </div>'
        '  <div class="content">内容</div>'
        '</div>'
    )
    r = _run(html)
    assert len(r.errors) == 0 and len(r.warnings) == 0 and r.passed == 1


def test_valid_navbar_all_mobile_frames_ok():
    """h5 / miniprogram / tablet frame 均合法。"""
    for frame in ("h5-frame", "miniprogram-frame", "tablet-frame"):
        html = (
            f'<div class="{frame}">'
            '  <div class="fb-navbar">'
            '    <span class="fb-nav-back">←</span>'
            '    <span class="fb-nav-title">页</span>'
            '  </div>'
            '</div>'
        )
        r = _run(html)
        assert len(r.warnings) == 0, f"{frame} 应合法但报 WARN: {r.warnings}"
        assert r.passed == 1


def test_back_nested_deeper_still_detected():
    """.fb-nav-back 嵌在更深子树内仍识别为含返回入口。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar">'
        '    <div class="left"><a class="fb-nav-back">←</a></div>'
        '    <span class="fb-nav-title">页</span>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert len(r.warnings) == 0 and r.passed == 1


# ── 放错层 ────────────────────────────────────────────────────────────────────


def test_navbar_misplaced_parent_warn():
    """navbar 父非移动类 frame（嵌在内容容器内）→ WARN。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="content">'
        '    <div class="fb-navbar">'
        '      <span class="fb-nav-back">←</span>'
        '      <span class="fb-nav-title">页</span>'
        '    </div>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert len(r.errors) == 0
    assert any("不是 phone/h5/miniprogram/tablet-frame" in w for w in r.warnings)


def test_navbar_in_desktop_frame_warn():
    """desktop-frame 内 navbar → WARN（桌面用 sidebar，非移动类）。"""
    html = (
        '<div class="desktop-frame">'
        '  <div class="fb-navbar">'
        '    <span class="fb-nav-back">←</span>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert any("不是 phone/h5/miniprogram/tablet-frame" in w for w in r.warnings)


# ── 缺返回入口 ────────────────────────────────────────────────────────────────


def test_navbar_no_back_warn():
    """navbar 缺 .fb-nav-back → WARN（用户无路可返）。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar">'
        '    <span class="fb-nav-title">详情</span>'
        '    <span class="fb-nav-action">···</span>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert len(r.errors) == 0
    assert any("缺 .fb-nav-back 返回入口" in w for w in r.warnings)


def test_navbar_misplaced_and_no_back_two_warns():
    """既放错层又缺 back → 两条 WARN。"""
    html = (
        '<div class="phone-frame">'
        '  <section class="body">'
        '    <div class="fb-navbar">'
        '      <span class="fb-nav-title">页</span>'
        '    </div>'
        '  </section>'
        '</div>'
    )
    r = _run(html)
    assert len(r.errors) == 0
    assert any("不是 phone/h5/miniprogram/tablet-frame" in w for w in r.warnings)
    assert any("缺 .fb-nav-back 返回入口" in w for w in r.warnings)


def test_multiple_navbars_independent():
    """多个 navbar 各自独立评估。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar"><span class="fb-nav-back">←</span></div>'
        '</div>'
        '<div class="h5-frame">'
        '  <div class="fb-navbar"><span class="fb-nav-title">页</span></div>'
        '</div>'
    )
    r = _run(html)
    # 第二个 navbar 缺 back → 恰 1 条 WARN
    assert sum("缺 .fb-nav-back" in w for w in r.warnings) == 1


# ── v2 7 variant 用例（2026-05-30 落地）─────────────────────────────────────────


def test_v2_multi_select_variant_no_back_ok():
    """multi-select variant 不强制 .fb-nav-back（用 [取消] 替代）→ OK。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar" data-variant="multi-select">'
        '    <button class="fb-btn fb-btn-text">取消</button>'
        '    <span class="fb-nav-title">已选 2/8</span>'
        '    <button class="fb-btn fb-btn-text">全选</button>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert sum("缺 .fb-nav-back" in w for w in r.warnings) == 0, (
        f"multi-select 不应强制 back，实际 warnings={r.warnings}"
    )


def test_v2_confirm_variant_no_back_ok():
    """confirm variant 不强制 .fb-nav-back（用 [取消] 替代）→ OK。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar" data-variant="confirm">'
        '    <button class="fb-btn fb-btn-text">取消</button>'
        '    <span class="fb-nav-title">编辑信息</span>'
        '    <button class="fb-btn fb-btn-primary">确认</button>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert sum("缺 .fb-nav-back" in w for w in r.warnings) == 0


def test_v2_edit_variant_no_back_ok():
    """edit variant 不强制 .fb-nav-back（用 [完成] 替代）→ OK。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar" data-variant="edit">'
        '    <button class="fb-btn fb-btn-text">完成</button>'
        '    <span class="fb-nav-title">草稿编辑</span>'
        '    <span class="fb-nav-action"><button class="fb-btn">···</button></span>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert sum("缺 .fb-nav-back" in w for w in r.warnings) == 0


def test_v2_home_variant_no_back_ok():
    """home variant 不强制 .fb-nav-back（主页无返回入口）→ OK。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar" data-variant="home">'
        '    <span class="fb-nav-title">App 名称</span>'
        '    <span class="fb-nav-action"><button class="fb-btn">搜索</button></span>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert sum("缺 .fb-nav-back" in w for w in r.warnings) == 0


def test_v2_workflow_variant_requires_back():
    """workflow variant 强制 .fb-nav-back（上一步）；缺 back → WARN。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar" data-variant="workflow">'
        '    <span class="fb-nav-title">步骤 2/4</span>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert sum("缺 .fb-nav-back" in w and 'workflow' in w for w in r.warnings) == 1


def test_v2_detail_variant_requires_back():
    """detail variant（缺省）强制 .fb-nav-back；缺 back → WARN。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar" data-variant="detail">'
        '    <span class="fb-nav-title">详情页</span>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert sum("缺 .fb-nav-back" in w and 'detail' in w for w in r.warnings) == 1


def test_v2_default_variant_backward_compat():
    """缺省 data-variant 等同 detail（向后兼容现有 21 处用法）→ 强制 back。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar">'
        '    <span class="fb-nav-title">页</span>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert sum("缺 .fb-nav-back" in w for w in r.warnings) == 1


def test_v2_invalid_variant_warns():
    """data-variant 不在合法集合 → WARN（拼写错误警示）。"""
    html = (
        '<div class="phone-frame">'
        '  <div class="fb-navbar" data-variant="multiselect">'  # 拼写错误：缺连字符
        '    <span class="fb-nav-title">x</span>'
        '  </div>'
        '</div>'
    )
    r = _run(html)
    assert any('multiselect' in w and '不在合法集合' in w for w in r.warnings)
