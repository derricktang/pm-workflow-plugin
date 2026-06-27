"""测试提议1 页面层级架构（SSOT 双锚 #38 / S4-29）。

覆盖：
- assemble.build_hierarchy_mermaid：小产品（产品根→模块→页面）+ mermaid 转义
  + 页面节点 ID `M\\d+_P\\d+` 形态 + 大产品（>40 页）按模块拆 subgraph
- assemble.inject_spec_sitemap：marker 首次替换 + START..END 重入幂等 + 无 marker
  WARN+跳过
- assemble.inject_prd_sitemap：占位首次替换 + 重入幂等
- precheck_stage4.check_page_hierarchy_sitemap：合法（数对称无错）/ 违规（缺 §3.0
  / 缺 spec-sitemap）/ 边界（节点数不对称）
"""

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import assemble
import precheck_stage4


def _small_scaffold() -> dict:
    return {
        "product": "测试[产品]",
        "modules": [
            {
                "id": "M01",
                "name": '反馈"管理"',
                "pages": [
                    {"id": "P01", "name": "列表(页)", "route": "/feedback", "states": []},
                    {"id": "P02", "name": "详情", "route": "/f/:id", "states": []},
                ],
            },
            {
                "id": "M02",
                "name": "用户中心",
                "pages": [
                    {"id": "P01", "name": "个人主页", "route": "/profile", "states": []},
                ],
            },
        ],
    }


def _large_scaffold(n_modules: int = 5, pages_per: int = 9) -> dict:
    mods = []
    for mi in range(1, n_modules + 1):
        pages = [
            {"id": f"P{pi:02d}", "name": f"页面{pi}", "route": f"/m{mi}/p{pi}", "states": []}
            for pi in range(1, pages_per + 1)
        ]
        mods.append({"id": f"M{mi:02d}", "name": f"模块{mi}", "pages": pages})
    return {"product": "大产品", "modules": mods}


# ── build_hierarchy_mermaid ────────────────────────────────────────────────

def test_hierarchy_small_structure_and_escaping():
    """WE-LRTB（2026-05-25）：direction LR + 始终 subgraph 分组 + 模块内 TB
    竖排。原 graph TD 同级横排痛点（issue 2026-05-18 / 2026-05-25）治本。"""
    src = assemble.build_hierarchy_mermaid(_small_scaffold())
    # 布局方向：外层 LR（流向左→右、同级模块竖排）
    # 首行是 mermaid frontmatter（启 ELK 让 subgraph 内 direction TB 生效；
    # ELK 不支持 curve 配置——mermaid 10 架构限制，不加 dead config），
    # graph LR 在 frontmatter 后
    assert src.startswith("---\nconfig:")
    assert "defaultRenderer: elk" in src
    assert "curve:" not in src  # 守门：避免未来误加 curve 让维护者以为生效
    assert "\ngraph LR\n" in src
    # 产品根 + 模块 subgraph 分组 + 模块内 TB 竖排
    assert 'PRODUCT_ROOT[' in src
    assert "PRODUCT_ROOT --> M01" in src
    assert "PRODUCT_ROOT --> M02" in src
    assert "subgraph M01[" in src
    assert "subgraph M02[" in src
    assert "direction TB" in src  # subgraph 内显式 TB → 该模块的页面竖排
    # 页面节点 ID 固定 M\d+_P\d+ 形态，distinct 数 == 总页面数(3)
    page_nodes = set(re.findall(r"\bM\d+_P\d+\b", src))
    assert page_nodes == {"M01_P01", "M01_P02", "M02_P01"}
    # 子图分组下，页面节点声明在 subgraph 内（缩进 4 空格），不再有 `Mxx --> Mxx_Pxx` 边
    assert "M01 --> M01_P01" not in src
    assert "    M01_P01[" in src  # 4 空格缩进 = subgraph 内
    # mermaid 转义（非 HTML 转义域）：[ ] ( ) " 必须被实体化，原字符不得裸露在标签
    assert "&#91;" in src and "&#93;" in src  # 产品名 测试[产品]
    assert "&quot;" in src                      # 模块名 反馈"管理"
    assert "&#40;" in src and "&#41;" in src    # 页面名 列表(页)
    assert "[产品]" not in src                   # 裸方括号不得出现
    assert "/feedback" in src                    # route 以 · 分隔附加


def test_hierarchy_large_subgraph_grouping():
    """WE-LRTB（2026-05-25）：原"大产品才 subgraph"分支已废除——所有规模统一
    subgraph 分组。large 用例（45 页）验证规模无关性。"""
    data = _large_scaffold(5, 9)  # 45 页
    src = assemble.build_hierarchy_mermaid(data)
    # 首行是 mermaid frontmatter（启 ELK 让 subgraph 内 direction TB 生效；
    # ELK 不支持 curve 配置——mermaid 10 架构限制，不加 dead config），
    # graph LR 在 frontmatter 后
    assert src.startswith("---\nconfig:")
    assert "defaultRenderer: elk" in src
    assert "curve:" not in src  # 守门：避免未来误加 curve 让维护者以为生效
    assert "\ngraph LR\n" in src
    assert "subgraph M01[" in src
    assert "subgraph M05[" in src
    assert 'PRODUCT_ROOT[' in src  # WE-LRTB：大产品也保留 ROOT（统一形态）
    assert "PRODUCT_ROOT --> M01" in src
    assert src.count("direction TB") == 5  # 每个模块 subgraph 各一条
    page_nodes = set(re.findall(r"\bM\d+_P\d+\b", src))
    assert len(page_nodes) == 45


# ── inject_spec_sitemap ────────────────────────────────────────────────────

def test_inject_spec_sitemap_marker_then_idempotent():
    data = _small_scaffold()
    spec0 = "## S0 背景\n\n## S1 页面流转总图\n\n<!-- [SITEMAP-3.0] -->\n\n### 3.1 全量页面清单\n"
    spec1, ok1 = assemble.inject_spec_sitemap(spec0, data)
    assert ok1 is True
    assert assemble.SITEMAP_SPEC_MARKER not in spec1
    assert "### 3.0 页面层级架构" in spec1
    assert assemble.SITEMAP_SPEC_START in spec1 and assemble.SITEMAP_SPEC_END in spec1
    assert "```mermaid" in spec1
    # 重入幂等：再跑一次，START..END 仅一组，内容稳定
    spec2, ok2 = assemble.inject_spec_sitemap(spec1, data)
    assert ok2 is True
    assert spec2.count(assemble.SITEMAP_SPEC_START) == 1
    assert spec2 == spec1  # 同 scaffold → 确定性，重跑结果稳定


def test_inject_spec_sitemap_missing_marker_skips():
    data = _small_scaffold()
    spec0 = "## S0 背景\n\n### 3.1 全量页面清单\n"  # Foundation 漏写 marker
    out, ok = assemble.inject_spec_sitemap(spec0, data)
    assert ok is False
    assert out == spec0  # 不破坏原文，precheck 兜底 FAIL


# ── inject_prd_sitemap ─────────────────────────────────────────────────────

def test_inject_prd_sitemap_placeholder_then_idempotent():
    data = _small_scaffold()
    html0 = '<section id="spec-sitemap"><div class="spec-body">\n<!-- [SITEMAP-PRD] -->\n</div></section>'
    html1, ok1 = assemble.inject_prd_sitemap(html0, data)
    assert ok1 is True
    assert assemble.SITEMAP_PRD_PLACEHOLDER not in html1
    assert '<pre class="mermaid">' in html1
    assert assemble.SITEMAP_PRD_START in html1
    html2, ok2 = assemble.inject_prd_sitemap(html1, data)
    assert ok2 is True
    assert html2.count(assemble.SITEMAP_PRD_START) == 1
    assert html2 == html1


# ── check_page_hierarchy_sitemap（S4-29）───────────────────────────────────

def _assembled_spec(data: dict) -> str:
    base = "## S0\n\n<!-- [SITEMAP-3.0] -->\n\n### 3.1 全量页面清单\n"
    out, _ = assemble.inject_spec_sitemap(base, data)
    return out


def _assembled_prd(data: dict) -> str:
    base = '<section id="spec-sitemap"><div class="spec-body"><!-- [SITEMAP-PRD] --></div></section>'
    out, _ = assemble.inject_prd_sitemap(base, data)
    return out


def test_check_legal_passes():
    data = _small_scaffold()
    r = precheck_stage4.Report()
    precheck_stage4.check_page_hierarchy_sitemap(
        data, _assembled_spec(data), _assembled_prd(data), r
    )
    assert r.errors == [], r.errors


def test_check_missing_spec_section_fails():
    data = _small_scaffold()
    r = precheck_stage4.Report()
    precheck_stage4.check_page_hierarchy_sitemap(
        data, "## S0\n（无 §3.0）\n", _assembled_prd(data), r
    )
    assert any("3.0" in e for e in r.errors)


def test_check_node_count_mismatch_fails():
    data = _small_scaffold()
    spec_ok = _assembled_spec(data)
    prd_ok = _assembled_prd(data)
    # scaffold 比派生时多一页 → 数不对称
    data2 = _small_scaffold()
    data2["modules"][0]["pages"].append(
        {"id": "P03", "name": "新增页", "route": "/x", "states": []}
    )
    r = precheck_stage4.Report()
    precheck_stage4.check_page_hierarchy_sitemap(data2, spec_ok, prd_ok, r)
    assert any("不对称" in e for e in r.errors)


# ── WE-D 回归：spec-sitemap mermaid 局部豁免（下游 NB 上报缺陷修复）──────────
# 缺陷：S4-29/S4-31 强制 spec-sitemap 必含 mermaid，但 §十一 豁免白名单缺
# `sitemap` → check_prd 局部豁免判该 mermaid FAIL，与 S4-29 互斥死锁。


def test_spec_sitemap_in_mermaid_exempt_whitelist():
    """`sitemap` 必须在 mermaid 豁免白名单（强制含 ⇔ 必豁免，同族对称）。"""
    assert "sitemap" in precheck_stage4.MERMAID_ALLOWED_SECTION_KEYWORDS


def test_mermaid_exempt_membership_matches_spec_sitemap_only():
    """复刻 check_prd 局部豁免判定逻辑：spec-sitemap 豁免；非豁免 section 不被
    误豁免（防过度豁免回归）。"""
    kws = precheck_stage4.MERMAID_ALLOWED_SECTION_KEYWORDS

    def exempt(section_id: str) -> bool:
        owner_lower = section_id.lower()
        return any(kw in owner_lower for kw in kws)

    # 提议1 层级图 + 提议3 模块依赖图 同在 spec-sitemap → 必豁免
    assert exempt("spec-sitemap") is True
    # 既有豁免不回归
    assert exempt("spec-business-flow") is True
    assert exempt("spec-journey") is True
    # 非豁免 section 不得被误豁免（防 "sitemap" 过宽）
    assert exempt("spec-feature") is False
    assert exempt("spec-data") is False
    assert exempt("spec-background") is False


def test_assemble_sitemap_section_is_exempt_end_to_end():
    """assemble 实产的 spec-sitemap section（含层级图 mermaid）按 check_prd 同款
    判定应被豁免——闭环验证死锁已解。"""
    data = _small_scaffold()
    prd = _assembled_prd(data)
    m = re.search(
        r'<section\s+id\s*=\s*"(spec-sitemap)"', prd, re.IGNORECASE
    )
    assert m, "assemble 应产出 <section id=\"spec-sitemap\">"
    assert '<pre class="mermaid">' in prd  # 确有 mermaid（S4-29 要求）
    owner_lower = m.group(1).lower()
    assert any(
        kw in owner_lower
        for kw in precheck_stage4.MERMAID_ALLOWED_SECTION_KEYWORDS
    ), "spec-sitemap 内 mermaid 必须被 check_prd 局部豁免（否则与 S4-29 死锁）"


# ── WE-FP 回归：check_prd mermaid 检测器剥 <script>/注释域（同族对称硬化）──────
# 缺陷（下游 Supervisor NB-L2-SITEMAP-RENDER-FP）：renderStaticMermaid() 等
# mermaid 渲染 JS 的注释/选择器合法含字面 `<pre class="mermaid">` / ```mermaid，
# 经 assemble._overwrite_scripts_from_template 进 outputs/prd <script>；旧
# check_prd 扫整个 html → 误判为「游离 mermaid 块」FAIL。修复：扫描前等长留白
# <script>/<!-- -->（真 mermaid DOM 永不在该两域，零假阴性）。


def _MERMAID_ERR(r) -> list:
    """筛出 check_prd §5 mermaid 局部豁免规则产生的 error。"""
    return [e for e in r.errors if "§十一" in e or "游离" in e]


def test_blank_noise_preserves_offsets_and_strips_only_script_comment():
    """_blank_mermaid_scan_noise：长度逐字保持；script/注释域内字面被留白；
    域外真 <pre class="mermaid"> 完整保留。"""
    src = (
        '<body>\n'
        '<section id="spec-sitemap"><pre class="mermaid">graph TD\nA-->B</pre>'
        '</section>\n'
        '<!-- 文档注释里写了 <pre class="mermaid"> 仅作说明 -->\n'
        '<script>\n/* 选择器 .x pre.mermaid；字面 <pre class="mermaid"> 与 '
        '```mermaid 仅注释 */\nfunction f(){}\n</script>\n</body>'
    )
    out = precheck_stage4._blank_mermaid_scan_noise(src)
    assert len(out) == len(src)  # offset 逐字保持
    # 域外真 mermaid DOM 完整保留
    assert '<section id="spec-sitemap"><pre class="mermaid">graph TD' in out
    # script 段整体被留白（函数体也没了）
    assert "function f()" not in out
    # 注释/script 内的 mermaid 字面在 scan 上不可被检测正则命中
    assert len(re.findall(r"```mermaid", out)) == 0
    pre_div = re.findall(
        r'<(?:pre|div)[^>]*\bclass\s*=\s*"[^"]*\bmermaid\b[^"]*"', out
    )
    assert pre_div == ['<pre class="mermaid"']  # 仅域外那一处真节点


def test_check_prd_no_fp_on_script_comment_mermaid_literal():
    """触发源复现：<script> 注释含 `<pre class="mermaid">`/```mermaid 字面 +
    合法 spec-sitemap 真 mermaid → check_prd 不得产生任何 mermaid 违规。"""
    html = (
        "<html><body>\n"
        '<section id="spec-sitemap">\n'
        '  <pre class="mermaid">\ngraph TD\n  ROOT["产品"] --> M01\n</pre>\n'
        "</section>\n"
        "<script>\n"
        "  /* renderStaticMermaid: 渲染 #spec-sitemap pre.mermaid；提议1/3 两块\n"
        '     `<pre class="mermaid">` 由 assemble 注入；switchJourneyView 只渲\n'
        "     .journey-flow-view pre.mermaid；源码块 ```mermaid 亦仅注释 */\n"
        "  function renderStaticMermaid(){ "
        "document.querySelectorAll('#spec-sitemap pre.mermaid'); }\n"
        "</script>\n</body></html>"
    )
    r = precheck_stage4.Report()
    precheck_stage4.check_prd({"modules": []}, html, r)
    assert _MERMAID_ERR(r) == [], _MERMAID_ERR(r)  # 零假阳性


def test_check_prd_still_flags_real_freefloating_mermaid():
    """假阴性守卫：真实游离 mermaid（在 <body> 内、不在任何 section、不在
    script/注释域）仍须 FAIL —— 硬化不得放过真违规。"""
    html = (
        "<html><body>\n"
        '<pre class="mermaid">\ngraph LR\n  A --> B\n</pre>\n'
        "</body></html>"
    )
    r = precheck_stage4.Report()
    precheck_stage4.check_prd({"modules": []}, html, r)
    errs = _MERMAID_ERR(r)
    assert errs, "真实游离 mermaid 必须仍被 check_prd 判 FAIL（防假阴性回归）"
    assert any("游离" in e for e in errs), errs


def test_check_prd_still_flags_mermaid_in_nonexempt_section():
    """假阴性守卫：非豁免 section 内真 mermaid 仍 FAIL（硬化只剥噪声域，
    不放宽白名单）。"""
    html = (
        "<html><body>\n"
        '<section id="spec-feature">\n'
        '  <pre class="mermaid">\ngraph TD\n  X --> Y\n</pre>\n'
        "</section>\n</body></html>"
    )
    r = precheck_stage4.Report()
    precheck_stage4.check_prd({"modules": []}, html, r)
    errs = _MERMAID_ERR(r)
    assert errs, "spec-feature 内 mermaid 必须仍 FAIL（白名单未放宽）"
    assert any("spec-feature" in e for e in errs), errs
