"""测试 assemble._overwrite_scripts_from_template — WE-ASM <script> 派生漂移兜底。

缺陷背景（下游报告 2026-05-16）：assemble_prd 旧实现只重读 template `<style>`
覆盖派生层（NB-WE-20），不覆盖 `<script>` → prd_template.html 的 mermaid 时序
竞态修复（ensureMermaidReady / head CDN onerror）不注入 outputs/prd，
outputs/prd 仍是 ~20:1 失败旧实现。本测试守护该 drift 类不再复发。

覆盖：
- 旧脆弱 outputs/prd → 覆盖后含真源 ensureMermaidReady + CDN onerror
- 仅覆盖 <script>，不破坏 body / <style> / 注入内容
- 幂等（重复覆盖结果稳定）
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import assemble


def _stale_outputs_prd() -> str:
    """模拟漂移的 outputs/prd：旧 CDN 标签(无 onerror) + 旧脆弱内联 mermaid 逻辑。"""
    return (
        "<!DOCTYPE html><html><head>\n"
        '<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js" defer></script>\n'
        "<style>.frame-card{isolation:isolate}</style>\n"
        "</head><body>\n"
        '<section id="proj-component-x" class="proj-component-showcase">SHOWCASE_KEEP</section>\n'
        "<!-- BODY_SENTINEL_KEEP -->\n"
        "<script>\n"
        "  window.addEventListener('DOMContentLoaded', () => {\n"
        "    if (typeof window.mermaid === 'undefined') { applyMermaidFailureFallback(); return; }\n"
        "  });\n"
        "</script>\n"
        "</body></html>\n"
    )


class TestScriptOverwrite:
    def test_stale_prd_gets_template_mermaid_fix(self):
        out, changed = assemble._overwrite_scripts_from_template(_stale_outputs_prd())
        assert changed is True
        # 内联块来自真源：含新实现特征，且旧脆弱特征已被替换掉
        assert "ensureMermaidReady" in out
        assert "renderMermaidWithRetry" in out
        assert "defer 加载的 CDN 脚本在 DOMContentLoaded 之前会就绪" not in out
        # head CDN 标签来自真源：含 onerror 标记
        assert 'onerror="window.__mermaidLoadFailed' in out

    def test_only_scripts_replaced_body_and_style_preserved(self):
        out, _ = assemble._overwrite_scripts_from_template(_stale_outputs_prd())
        assert "BODY_SENTINEL_KEEP" in out
        assert "SHOWCASE_KEEP" in out
        assert ".frame-card{isolation:isolate}" in out  # <style> 未被本 helper 触碰

    def test_idempotent(self):
        once, c1 = assemble._overwrite_scripts_from_template(_stale_outputs_prd())
        twice, c2 = assemble._overwrite_scripts_from_template(once)
        assert c1 is True and c2 is True  # 仍执行替换（真源→派生），但结果稳定
        assert once == twice
        assert "ensureMermaidReady" in twice

    def test_missing_blocks_skip_gracefully(self):
        out, changed = assemble._overwrite_scripts_from_template(
            "<html><body>no scripts here</body></html>"
        )
        assert changed is False
        assert out == "<html><body>no scripts here</body></html>"


class TestSidebarNavStructureOverwrite:
    """议题 28 NB-WE-NAV-OVERWRITE: assemble.py 补 sidebar 结构重读测试用例。

    治"议题 27 修改 sidebar 结构但 outputs/prd 不会自动重生 sidebar"哑修复根因。
    与 NB-WE-20 (<style>) / WE-ASM (<script>) 同模式，但目标是 sidebar SPEC/SITEMAP
    两组 group-body 结构层。
    """

    def _old_outputs_prd(self) -> str:
        """议题 27 前的旧 outputs/prd sidebar 结构（spec 8 项 + sitemap 5 项含业务流程图）。"""
        return (
            "<html><body>"
            '<div class="sidebar-group-body" data-group-body="spec">'
            '<div class="sidebar-spec-item" data-target="spec-background">需求背景</div>'
            '<div class="sidebar-spec-item" data-target="spec-persona">用户画像</div>'
            '<div class="sidebar-spec-item" data-target="spec-permission">权限矩阵</div>'
            '<div class="sidebar-spec-item" data-target="spec-journey">用户旅程</div>'
            '<div class="sidebar-spec-item" data-target="spec-feature">功能索引</div>'
            '<div class="sidebar-spec-item" data-target="spec-data">数据字段</div>'
            '<div class="sidebar-spec-item" data-target="spec-exception">异常处理全景</div>'
            '<div class="sidebar-spec-item" data-target="spec-nonfunc">非功能需求</div>'
            '</div>'
            '<div class="sidebar-section-title sidebar-group-toggle" data-group="sitemap">页面架构总览</div>'
            '<div class="sidebar-group-body" data-group-body="sitemap">'
            '<div class="sidebar-spec-item" data-target="sk-hier">页面层级图</div>'
            '<div class="sidebar-spec-item" data-target="sk-arch">页面结构契约</div>'
            '<div class="sidebar-spec-item" data-target="sk-askel">范式骨架</div>'
            '<div class="sidebar-spec-item" data-target="sk-mod">模块架构</div>'
            '<div class="sidebar-spec-item" data-target="spec-business-flow">业务流程图</div>'
            '</div>'
            '<div class="sidebar-section-title sidebar-group-toggle" data-group="changelog">组件变更</div>'
            "</body></html>"
        )

    def test_old_structure_overwritten_to_issue27(self):
        """旧结构 8+5 → 议题 27 新结构 9+4，业务流程图从 sitemap 移到 spec。"""
        out, replaced = assemble._overwrite_sidebar_nav_structure_from_template(
            self._old_outputs_prd()
        )
        assert replaced == 2  # spec + sitemap 都改

        import re
        spec_inner = re.search(r'data-group-body="spec">([\s\S]*?)</div>\s*<div\s+class="sidebar-section-title', out).group(1)
        sitemap_inner = re.search(r'data-group-body="sitemap">([\s\S]*?)</div>\s*<div\s+class="sidebar-section-title', out).group(1)

        # spec 组：9 项含业务流程图
        assert spec_inner.count("sidebar-spec-item") == 9
        assert "spec-business-flow" in spec_inner
        # sitemap 组：4 项无业务流程图
        assert sitemap_inner.count("sidebar-spec-item") == 4
        assert "spec-business-flow" not in sitemap_inner

    def test_idempotent_when_already_new_structure(self):
        """已是议题 27 新结构 → 替换段数 0（幂等）。"""
        once, c1 = assemble._overwrite_sidebar_nav_structure_from_template(self._old_outputs_prd())
        twice, c2 = assemble._overwrite_sidebar_nav_structure_from_template(once)
        assert c1 == 2  # 首次改 2 段
        assert c2 == 0  # 再次跑 idempotent
        assert once == twice

    def test_missing_group_body_skip_gracefully(self):
        """outputs/prd 无 group-body 段 → 跳过不报错。"""
        out, replaced = assemble._overwrite_sidebar_nav_structure_from_template(
            "<html><body>no sidebar group-body here</body></html>"
        )
        assert replaced == 0
        assert "no sidebar group-body here" in out

    def test_business_flow_position_after_journey(self):
        """议题 27 期望位置：业务流程图紧跟用户旅程（在 spec 组内位置 5）。"""
        out, _ = assemble._overwrite_sidebar_nav_structure_from_template(self._old_outputs_prd())
        journey_pos = out.find("spec-journey")
        business_flow_pos = out.find("spec-business-flow")
        feature_pos = out.find("spec-feature")
        # 业务流程图必在用户旅程之后、功能索引之前
        assert 0 < journey_pos < business_flow_pos < feature_pos
