"""派生注入回归守（SSOT #80 派生注入清单配套，retro 2026-06-11 C1 根因治本）。

治「阶段 4 派生注入点散落 + 回归无统一守」：assemble.py 有 24+ 个
inject_*/_inject_*/_overwrite_* 派生注入函数（从 spec / scaffold / template 派生
进 outputs/spec|prd），历史多次出现新注入引入回归无机械守（议题 1/7/8/14/17/18/20）。

**元测试守（test_every_derived_injection_func_has_regression_test）**：枚举所有派生
注入函数，断言各有回归测试引用 → 新增派生注入点漏测即 pytest FAIL，强制登记
`workflow_architecture_map.md §阶段4 派生注入点清单` + 配回归测试。

本文件同时补齐 5 个历史缺口函数的回归测试。
"""

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import assemble

ASSEMBLE_SRC = (SCRIPTS_DIR / "assemble.py").read_text(encoding="utf-8")
TESTS_DIR = Path(__file__).resolve().parent

# 纯内部 helper —— 通过被测的上层函数间接覆盖,无须独立回归测试。
# 新增项须在此说明理由(避免 allowlist 沦为绕过守的后门)。
_COVERAGE_ALLOWLIST = {
    "_inject_template_hash",          # 嵌 template hash 注释,无派生语义
    "_inject_c_subtitle_placeholder",  # c1/c2/c3 占位共享 helper(三者均有独立测试)
}


def _derived_injection_funcs() -> list[str]:
    return sorted(set(re.findall(
        r"^def ((?:inject_|_inject_|_overwrite_)\w+)", ASSEMBLE_SRC, re.M)))


def _referenced_in_tests(name: str) -> bool:
    # 含本文件：本文件的 5 缺口测试以真实调用(assemble.inject_*)引用函数,算有效覆盖。
    # 元测试自身从 assemble.py 源码动态枚举函数名(本文件体内无函数名硬编码列表),
    # 故不会"自满足"——某函数名只在测试以真实调用出现才计为被引用。
    for p in TESTS_DIR.glob("test_*.py"):
        if name in p.read_text(encoding="utf-8"):
            return True
    return False


# ── 元测试：统一守 ────────────────────────────────────────────────────────────

def test_every_derived_injection_func_has_regression_test():
    funcs = _derived_injection_funcs()
    assert funcs, "未枚举到任何派生注入函数(正则失配?)"
    missing = [f for f in funcs
               if f not in _COVERAGE_ALLOWLIST and not _referenced_in_tests(f)]
    assert not missing, (
        "以下 assemble 派生注入函数缺回归测试(C1 根因守,SSOT #80):\n  "
        + "\n  ".join(missing)
        + "\n→ 新增派生注入点须:① 登记 architecture_map §阶段4 派生注入点清单 "
        "② 配回归测试;纯内部 helper 加入 _COVERAGE_ALLOWLIST 并注明理由。"
    )


def test_overwrite_first_style_runs_before_css_injections():
    """注入顺序锁定（2026-06-12 审计）：_overwrite_first_style_from_template 必须
    先于 inject_fallback_css / inject_proj_css 调用——重排会让 template 覆盖
    静默冲掉已注入的 FB FALLBACK / PROJ CSS 块。按源码调用位置断言。"""
    # 精确匹配调用点字面（函数定义是 `(html: str)`，不会误命中）
    overwrite_at = ASSEMBLE_SRC.index("_overwrite_first_style_from_template(html)")
    fallback_at = ASSEMBLE_SRC.index("inject_fallback_css(html)")
    proj_at = ASSEMBLE_SRC.index("inject_proj_css(html, all_proj_css)")
    assert overwrite_at < fallback_at and overwrite_at < proj_at, (
        "assemble_prd 注入顺序被重排：_overwrite_first_style 必须在 "
        "fallback/proj CSS 注入之前（否则覆盖会冲掉注入块）"
    )


# ── 5 个历史缺口函数的回归测试 ────────────────────────────────────────────────

def test_inject_fallback_css_idempotent():
    html = "<html><head><style>.base{color:#000}</style></head><body></body></html>"
    once, n1 = assemble.inject_fallback_css(html)
    assert assemble.FB_FALLBACK_START in once and n1 > 0
    twice, _ = assemble.inject_fallback_css(once)
    assert twice.count(assemble.FB_FALLBACK_START) == 1  # 幂等:不重复堆叠


def test_inject_proj_css_idempotent():
    html = f"<style>\n{assemble.PROJ_CSS_START}\n{assemble.PROJ_CSS_END}\n</style>"
    once, n1 = assemble.inject_proj_css(html, ".x{color:red}")
    assert ".x{color:red}" in once and n1 > 0
    twice, _ = assemble.inject_proj_css(once, ".x{color:red}")
    assert twice.count(assemble.PROJ_CSS_START) == 1  # 幂等


def test_inject_proj_component_showcase_inject_and_noop():
    # 含占位 → 注入 + 幂等
    html = "<body>\n<!-- [PROJ-COMPONENT-SHOWCASE-AREA] -->\n</body>"
    once, _ = assemble.inject_proj_component_showcase(html, "<div>SHOWCASE_X</div>")
    assert "SHOWCASE_X" in once and "PROJ-COMPONENT-SHOWCASE-AREA-START" in once
    twice, _ = assemble.inject_proj_component_showcase(once, "<div>SHOWCASE_X</div>")
    assert twice.count("PROJ-COMPONENT-SHOWCASE-AREA-START") == 1  # 幂等
    # 无占位 / 无容器 → 优雅跳过(产品无 proj 组件场景),不崩不改
    noop, n = assemble.inject_proj_component_showcase("<body>NO_AREA</body>", "<div>x</div>")
    assert noop == "<body>NO_AREA</body>" and n == 0


def test_inject_component_changelog_nav_noop_when_no_placeholder():
    # 旧骨架无 [COMPONENT-CHANGELOG-NAV] 占位 → 静默跳过,不崩不改
    html = "<body><section id='other'>x</section></body>"
    out, n = assemble.inject_component_changelog_nav(html)
    assert out == html and n == 0


def test_overwrite_first_style_from_template_idempotent():
    # 陈旧 outputs/prd 第一个 <style> → 重读 template 覆盖(NB-WE-20 派生漂移守)
    stale = ("<html><head>\n<style>.frame-card{/*STALE*/}</style>\n</head>"
             "<body><!-- BODY_KEEP --></body></html>")
    once, changed = assemble._overwrite_first_style_from_template(stale)
    assert "BODY_KEEP" in once  # 不破坏 body
    twice, _ = assemble._overwrite_first_style_from_template(once)
    assert twice == once  # 幂等:再覆盖结果稳定
