"""L2 模板不变量：S4-04 帧类白名单 ↔ prd_template.html CSS 帧样式覆盖一致性。

治 NB-WE-MP-FRAME-CSS-NAME 根因（2026-06-09 私域上报）：S4-04 白名单曾含 `mp-frame`，
但 prd_template.html 整条帧样式错命名 `.miniprogram-frame` → 产品按 canonical `mp-frame`
写帧拿不到任何样式（帧塌缩 + 抽屉逃逸污染 sidebar），且过了 S4-04 白名单**无人发现**
（议题 #24 反复治标根因）。

本测试是缺失的机械兜底（SSOT #78）：**每个 S4-04 白名单帧类必须在 prd_template.html
有对应 CSS 规则**——白名单与样式真源任一漂移即 fail，把"白名单声明 ≠ 样式实现"在 L2
改动时（而非下游产品渲染时）拦下。
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import precheck_stage4  # noqa: E402

PRD_TEMPLATE = SCRIPTS_DIR.parent / "rules" / "prd_template.html"


def test_every_whitelist_frame_class_has_template_css():
    """S4-04 PLATFORM_FRAME_NAMES 每个帧类在 prd_template.html 有 `.{class}` CSS 引用。"""
    html = PRD_TEMPLATE.read_text(encoding="utf-8")
    missing = [c for c in precheck_stage4.PLATFORM_FRAME_NAMES if f".{c}" not in html]
    assert not missing, (
        f"S4-04 白名单帧类在 prd_template.html 无 CSS 样式：{missing}"
        f"（NB-WE-MP-FRAME-CSS-NAME 同型——白名单声明的帧类必须真有样式，"
        f"否则产品按 canonical 名写帧拿不到样式且过白名单无人发现）"
    )


def test_no_orphan_mp_frame_alias():
    """回归锁定：不得回退到 `mp-frame`（已统一 miniprogram-frame，方案 B）。"""
    html = PRD_TEMPLATE.read_text(encoding="utf-8")
    assert "mp-frame" not in html, "prd_template.html 不应含 mp-frame（已统一 miniprogram-frame）"
    assert "miniprogram-frame" in precheck_stage4.PLATFORM_FRAME_NAMES
    assert "mp-frame" not in precheck_stage4.PLATFORM_FRAME_NAMES
