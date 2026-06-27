"""测试 SSOT 双锚 #41 / S4-32 页面骨架屏（WE-H per-archetype 单源 + 条件 per-page override）。

WE-H（2026-05-19，#41 颗粒度重设 per-page → per-archetype）覆盖：
- gen_scaffold.build_foundation_skeleton_draft：`spec_foundation_draft.md`「## 范式骨架」
  每范式 `- **<aid> 名称**` 锚 + ```skeleton 占位 + SKELETON_DISCLAIMER 首行；
  无 page_archetypes → 优雅 N/A
- gen_scaffold.build_spec_module_draft：per-page 槽 = override-only 纯注释 marker
  （非活动围栏，无"每页必填"压力）
- assemble.extract_archetype_skeletons：aid 白名单锚、作用域限 ## 范式骨架、
  per-platform 块、缺草稿优雅跳过、非 scaffold id 的 bold 不误抓
- assemble.build_archetype_skeleton_md/_html：每范式 sk-askel-<aid> 子锚、
  per-platform 标签、未填 pending 兜底、agnostic → ""
- assemble.extract_spec_skeletons override-only：comment marker 不误抓为围栏、
  真 override 围栏正常提取
- assemble.inject_page_skeletons：非 override 页 → chip(sk-askel-<aid>) /
  override 页 → 专属骨架 + distinct 标记 / agnostic 占位保留 / 幂等 /
  返回 (n_override, n_chip)
- assemble.inject_spec_sitemap / inject_prd_sitemap：范式骨架子节在 #39 契约后
  （子决策B）、PRD 4 锚序 sk-hier<arch<askel<mod + sk-askel-<aid> 子锚、幂等
- gen_scaffold.build_sitemap_nav：5 项含 sk-askel
- precheck.check_page_skeleton：三块 WARN-phase 档 C（全 r.warn 非 r.fail，
  存量 per-archetype 迁移完升 FAIL）—— 全填+override good 干净 / 范式未填
  WARN / 默认页 override-only 零 warn / agnostic / 无 §3.0 范式骨架子节跳过

注：本机 pytest 环境缺失（NB-WE-04），文件底部 `__main__` 提供手动 harness
（tempfile 替代 fixture）等价验证；pytest 恢复后可直接 discover（纯函数无 fixture）。
"""

import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import assemble
import gen_scaffold
import precheck_stage4

DISC = precheck_stage4.SKELETON_DISCLAIMER


# ── fixtures（纯函数，自建 tmp，pytest/手动 harness 均可）──────────────────────

def _data():
    return {
        "product": "报价工具",
        "platforms": ["桌面 Web"],
        "page_archetypes": [
            {"id": "list", "name": "列表范式",
             "regions": [{"slot": "topbar"}, {"slot": "listbody"}], "extension": ["bulk"]},
            {"id": "detail", "name": "详情范式",
             "regions": [{"slot": "main"}], "extension": ["footer"]},
        ],
        "modules": [{
            "id": "M01", "name": "报价", "purpose": "p",
            "pages": [
                {"id": "P01", "name": "列表页", "route": "/list", "archetype": "list",
                 "states": [{"name": "默认", "prd_id": "H-M01-P01-default", "roles": []}]},
                {"id": "P02", "name": "详情页", "route": "/detail", "archetype": "detail",
                 "states": [{"name": "默认", "prd_id": "H-M01-P02-default", "roles": []}]},
            ],
        }],
    }


def _good_sk(data_r):
    return f'<div class="sk-page"><div class="sk-region" data-r="{data_r}"></div></div>'


def _fill_foundation(td: Path, data: dict, fills: dict):
    """fills = {aid: inner_html}; 未列出的 archetype 保留占位（不替换）。"""
    fd = gen_scaffold.build_foundation_skeleton_draft(data)
    ph = ('<div class="sk-page">\n  <div class="sk-region" data-r="">'
          '[替换为本范式真实区域；data-r 取本范式 regions slot / extension]</div>\n</div>')
    for _aid, inner in fills.items():
        fd = fd.replace(ph, inner, 1)  # 顺序替换（占位文本恒同）
    (td / assemble.FOUNDATION_SKELETON_DRAFT).write_text(fd, encoding="utf-8")


def _setup(fills=None, override=None):
    """建 tmp DRAFTS_DIR + foundation 草稿（按 fills 填）+ 模块草稿（按 override 注 P02）。
    override = override skeleton inner html（注入 P02 marker 后）或 None。"""
    td = Path(tempfile.mkdtemp())
    assemble.DRAFTS_DIR = td
    data = _data()
    # foundation：默认两范式都按 data-r 顺序填好（list→topbar, detail→main）
    if fills is None:
        fills = {"list": _good_sk("topbar"), "detail": _good_sk("main")}
    _fill_foundation(td, data, fills)
    md = gen_scaffold.build_spec_module_draft(data["modules"][0])
    if override is not None:
        i2 = md.index("**P02 详情页**")
        e2 = md.index("-->", i2) + 3
        ov = f"\n\n```skeleton\n{DISC}\n{override}\n```"
        md = md[:e2] + ov + md[e2:]
    (td / "spec_M01_draft.md").write_text(md, encoding="utf-8")
    return td, data, md


def _spec_with_3_0(data):
    """模拟 assemble_spec：S0/S0.5/S1 + [SITEMAP-3.0] → inject_spec_sitemap。"""
    spec = "## S0 x\n## S0.5 y\n## S1 z\n<!-- [SITEMAP-3.0] -->\n"
    spec, _ = assemble.inject_spec_sitemap(spec, data)
    return spec


def _prd_sitemap(data):
    h, _ = assemble.inject_prd_sitemap("<!-- [SITEMAP-PRD] -->", data)
    return h


# ── gen_scaffold 占位 ──────────────────────────────────────────────────────

def test_foundation_draft_per_archetype_anchors():
    fd = gen_scaffold.build_foundation_skeleton_draft(_data())
    assert "## 范式骨架" in fd
    assert "- **list 列表范式**" in fd and "- **detail 详情范式**" in fd
    assert fd.count("```skeleton\n" + gen_scaffold.SKELETON_DISCLAIMER) == 2
    # data-r 提示串含该范式 slots
    assert "`topbar`" in fd and "`listbody`" in fd and "`bulk`" in fd


def test_foundation_draft_agnostic_graceful():
    fd = gen_scaffold.build_foundation_skeleton_draft({"product": "x", "modules": []})
    body = fd.split("## 范式骨架", 1)[1]
    # N/A 说明在「## 范式骨架」段；该段无范式锚行 / 无活动骨架围栏
    assert "无 `page_archetypes`" in body
    assert "- **" not in body and "```skeleton\n" not in body


def test_module_draft_per_page_override_only_marker():
    md = gen_scaffold.build_spec_module_draft(_data()["modules"][0])
    # per-page 槽 = 纯注释 marker，无活动 ```skeleton 围栏
    assert "默认复用本页 archetype" in md
    assert "```skeleton\n" + gen_scaffold.SKELETON_DISCLAIMER not in md
    assert "- **P01 列表页**" in md and "- **P02 详情页**" in md


def test_disclaimer_constant_three_way_literal_sync():
    assert gen_scaffold.SKELETON_DISCLAIMER == precheck_stage4.SKELETON_DISCLAIMER
    assert gen_scaffold.FOUNDATION_SKELETON_DRAFT_NAME == assemble.FOUNDATION_SKELETON_DRAFT


def test_sitemap_nav_4_items_incl_askel():
    """议题 27 业务流程图 nav 归"产品规格"组（§A-04.2 L642 [Must] 修复）后 5→4 项。"""
    nav = gen_scaffold.build_sitemap_nav()
    assert nav.count("sidebar-spec-item") == 4
    assert "showSection('sk-askel')" in nav and "范式骨架" in nav
    # 业务流程图应 NOT 在 sitemap 组（已归"产品规格"组）
    assert "spec-business-flow" not in nav


def test_spec_nav_9_items_incl_business_flow():
    """议题 27 业务流程图 nav 归"产品规格"组紧跟用户旅程后（§A-04.2 L642 [Must]）。"""
    nav = gen_scaffold.build_spec_nav()
    assert nav.count("sidebar-spec-item") == 9
    assert "showSection('spec-business-flow')" in nav and "业务流程图" in nav
    # 业务流程图位置：在用户旅程后、功能索引前
    journey_pos = nav.find("spec-journey")
    business_flow_pos = nav.find("spec-business-flow")
    feature_pos = nav.find("spec-feature")
    assert 0 < journey_pos < business_flow_pos < feature_pos


# ── assemble extract_archetype_skeletons ──────────────────────────────────

def test_extract_archetype_whitelist_and_scope():
    td, data, _ = _setup()
    sk = assemble.extract_archetype_skeletons(data)
    assert set(sk.keys()) == {"list", "detail"}
    assert sk["list"]["blocks"][0][0] is None  # agnostic
    # 非 scaffold id 的 bold 行不误抓
    fd = (td / assemble.FOUNDATION_SKELETON_DRAFT).read_text(encoding="utf-8")
    fd += "\n- **bogus 不存在范式**\n```skeleton\n" + DISC + "\n<div></div>\n```\n"
    (td / assemble.FOUNDATION_SKELETON_DRAFT).write_text(fd, encoding="utf-8")
    assert "bogus" not in assemble.extract_archetype_skeletons(data)


def test_extract_archetype_missing_draft_graceful():
    td = Path(tempfile.mkdtemp())
    assemble.DRAFTS_DIR = td
    assert assemble.extract_archetype_skeletons(_data()) == {}


def test_extract_archetype_per_platform():
    td = Path(tempfile.mkdtemp())
    assemble.DRAFTS_DIR = td
    data = _data()
    body = ("# spec — 范式骨架\n\n## 范式骨架\n\n"
            "- **list 列表范式**\n\n"
            f"```skeleton:phone\n{DISC}\n<div class=\"sk-page\">P</div>\n```\n"
            f"```skeleton:desktop\n{DISC}\n<div class=\"sk-page\">D</div>\n```\n")
    (td / assemble.FOUNDATION_SKELETON_DRAFT).write_text(body, encoding="utf-8")
    sk = assemble.extract_archetype_skeletons(data)
    assert [p for p, _ in sk["list"]["blocks"]] == ["phone", "desktop"]


# ── assemble build_archetype_skeleton_md/_html ─────────────────────────────

def test_build_archetype_skeleton_md_html():
    # detail 锚有但无 ```skeleton 围栏 → pending 兜底（list 正常）
    td = Path(tempfile.mkdtemp())
    assemble.DRAFTS_DIR = td
    data = _data()
    body = ("# spec — 范式骨架\n\n## 范式骨架\n\n"
            "- **list 列表范式**\n\n"
            f"```skeleton\n{DISC}\n{_good_sk('topbar')}\n```\n\n"
            "- **detail 详情范式**\n\n（Foundation 尚未填）\n")
    (td / assemble.FOUNDATION_SKELETON_DRAFT).write_text(body, encoding="utf-8")
    md = assemble.build_archetype_skeleton_md(data)
    assert "#### 范式骨架" in md and "（`list`）" in md
    assert "待 Foundation 子阶段二填" in md  # detail 无围栏 → pending
    h = assemble.build_archetype_skeleton_html(data)
    assert 'id="sk-askel-list"' in h and 'id="sk-askel-detail"' in h
    assert assemble.build_archetype_skeleton_md({"modules": []}) == ""
    assert assemble.build_archetype_skeleton_html({"modules": []}) == ""


# ── assemble extract_spec_skeletons override-only ─────────────────────────

def test_override_only_comment_marker_not_extracted():
    td, data, _ = _setup(override=None)  # 无 override，仅 marker
    items = assemble.extract_spec_skeletons(data)
    assert items == []  # 纯注释 marker 不产生围栏


def test_override_real_fence_extracted():
    td, data, _ = _setup(override=_good_sk("main"))
    items = assemble.extract_spec_skeletons(data)
    assert [(m, p) for m, _, p, _, _ in items] == [("M01", "P02")]


# ── assemble inject_page_skeletons：chip vs override ──────────────────────

def test_inject_chip_and_override_routing():
    td, data, _ = _setup(override=_good_sk("main"))
    prd = ('<section id="a"><!-- [PAGE-SKELETON: M01-P01] --></section>'
           '<section id="b"><!-- [PAGE-SKELETON: M01-P02] --></section>')
    out, (nov, nch) = assemble.inject_page_skeletons(prd, data)
    assert (nov, nch) == (1, 1)
    assert "sk-archetype-chip" in out and "showSection('sk-askel-list')" in out
    assert "页面专属骨架" in out and "覆盖范式" in out
    out2, _ = assemble.inject_page_skeletons(out, data)
    assert out == out2  # 幂等


def test_inject_agnostic_no_archetype_placeholder_kept():
    Path(tempfile.mkdtemp())  # no drafts needed
    d = {"modules": [{"id": "M01", "pages": [{"id": "P01", "name": "x", "states": []}]}]}
    html = "<!-- [PAGE-SKELETON: M01-P01] -->"
    out, (nov, nch) = assemble.inject_page_skeletons(html, d)
    assert (nov, nch) == (0, 0) and "[PAGE-SKELETON: M01-P01]" in out


# ── assemble sitemap 注入顺序 + 幂等 ──────────────────────────────────────

def test_spec_sitemap_skeleton_after_contract():
    td, data, _ = _setup()
    s = _spec_with_3_0(data)
    i_c, i_s, i_m = s.find("页面结构范式契约"), s.find("#### 范式骨架"), s.find("模块架构说明")
    assert 0 < i_c < i_s < i_m
    s2, _ = assemble.inject_spec_sitemap(s, data)
    assert s == s2  # 幂等


def test_prd_sitemap_4_anchors_order():
    td, data, _ = _setup()
    h = _prd_sitemap(data)
    o = [h.find(f'id="sk-{x}"') for x in ("hier", "arch", "askel", "mod")]
    assert all(v >= 0 for v in o) and o == sorted(o)
    assert 'id="sk-askel-list"' in h and 'id="sk-askel-detail"' in h
    h2, _ = assemble.inject_prd_sitemap(h, data)
    assert h == h2


# ── precheck S4-32（WARN-phase 档 C：全 r.warn，无 r.errors）────────────────

def test_check_clean_all_filled_no_override():
    td, data, _ = _setup()  # 两范式填好、无 override
    spec, prd = _spec_with_3_0(data), _prd_sitemap(data)
    r = precheck_stage4.Report()
    precheck_stage4.check_page_skeleton(data, spec, prd, r)
    assert r.errors == [] and r.warnings == []  # 默认页 override-only → 零 warn


def test_check_archetype_unfilled_warns_not_fail():
    td, data, _ = _setup(fills={"list": _good_sk("topbar")})  # detail 占位空 data-r
    spec, prd = _spec_with_3_0(data), _prd_sitemap(data)
    r = precheck_stage4.Report()
    precheck_stage4.check_page_skeleton(data, spec, prd, r)
    assert r.errors == []  # WARN-phase 档 C
    assert any("范式 detail" in w and "data-r" in w for w in r.warnings)


def test_check_override_good_and_default_no_warn():
    td, data, _ = _setup(override=_good_sk("main"))  # P02 override good, P01 default
    spec, prd = _spec_with_3_0(data), _prd_sitemap(data)
    r = precheck_stage4.Report()
    precheck_stage4.check_page_skeleton(data, spec, prd, r)
    assert r.errors == [] and r.warnings == []  # 范式填好 + override 良构 + 默认页零压力


def test_check_agnostic_skip():
    r = precheck_stage4.Report()
    precheck_stage4.check_page_skeleton({"modules": []}, "## S0", "<x></x>", r)
    assert r.errors == [] and len(r.warnings) == 1 and "page_archetypes" in r.warnings[0]


def test_check_no_3_0_section_skip():
    r = precheck_stage4.Report()
    precheck_stage4.check_page_skeleton(_data(), "## S0 only", _prd_sitemap(_data()), r)
    assert r.errors == [] and any("范式骨架" in w for w in r.warnings)


def test_check_prd_missing_sk_askel_warns():
    td, data, _ = _setup()
    spec = _spec_with_3_0(data)
    r = precheck_stage4.Report()
    precheck_stage4.check_page_skeleton(data, spec, "<section>无 sitemap</section>", r)
    assert r.errors == [] and any("sk-askel" in w for w in r.warnings)


# ── 手动 harness（pytest 缺失 NB-WE-04 等价 substitute）────────────────────

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            passed += 1
            print(f"  [PASS] {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            import traceback
            print(f"  [FAIL] {fn.__name__}: {e}")
            traceback.print_exc()
    print(f"\n{passed} passed / {failed} failed / {len(fns)} total")
    sys.exit(1 if failed else 0)
