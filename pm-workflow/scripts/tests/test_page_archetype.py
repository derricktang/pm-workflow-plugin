"""测试提议2 页面结构范式契约（SSOT 双锚 #39 / S4-30）。

覆盖：
- gen_scaffold.validate_v2_schema：缺 page_archetypes / 悬空 archetype /
  范式缺 regions / 合法 四态
- assemble.build_archetype_contract_md/_html：有 page_archetypes → 表；无 → ""
  （优雅降级，保 Commit1 行为）
- assemble.inject_spec/prd_sitemap：有 archetypes → 契约块附加 + 重入幂等
- precheck.check_page_archetype_contract：合法/缺 page_archetypes/悬空/缺契约表
- precheck.check_archetype_containment_record：无子进度文件→WARN skip /
  齐全→OK / 缺段→FAIL / 漏页→FAIL / 结论非 PASS|FAIL→FAIL（monkeypatch
  REPO_ROOT 到 tmp，不污染真实仓）
"""

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import assemble
import gen_scaffold
import precheck_stage4


def _arch():
    return [
        {
            "id": "list",
            "name": "列表页范式",
            "regions": [
                {"slot": "filter-bar", "hosts": "筛选"},
                {"slot": "data-area", "hosts": "表格"},
            ],
            "invariants": ["filter-bar 恒在 data-area 之上"],
            "extension": ["extra-toolbar"],
        }
    ]


def _scaffold(with_arch=True, archetype="list"):
    d = {
        "schema_version": "v2.0",
        "product": "P",
        "modules": [
            {
                "id": "M01",
                "name": "M",
                "candidate_components": {"pub": [], "proj_gaps": []},
                "owner_assignments": {},
                "depends_on": [],
                "pages": [
                    {"id": "P01", "name": "列表", "route": "/l",
                     "archetype": archetype, "states": []},
                ],
            }
        ],
    }
    if with_arch:
        d["page_archetypes"] = _arch()
    return d


# ── gen_scaffold.validate_v2_schema ────────────────────────────────────────

def test_validate_missing_page_archetypes_fails():
    d = _scaffold(with_arch=False)
    errs = gen_scaffold.validate_v2_schema(d)
    assert any("page_archetypes" in e for e in errs)


def test_validate_dangling_archetype_fails():
    d = _scaffold(archetype="ghost")
    errs = gen_scaffold.validate_v2_schema(d)
    assert any("悬空" in e for e in errs)


def test_validate_archetype_missing_regions_fails():
    d = _scaffold()
    d["page_archetypes"][0].pop("regions")
    errs = gen_scaffold.validate_v2_schema(d)
    assert any("regions" in e for e in errs)


def test_validate_legal_no_archetype_errors():
    d = _scaffold()
    errs = [e for e in gen_scaffold.validate_v2_schema(d)
            if "archetype" in e or "page_archetypes" in e]
    assert errs == [], errs


# ── assemble 契约派生 + 优雅降级 ───────────────────────────────────────────

def test_contract_md_html_present_and_graceful():
    d = _scaffold()
    md = assemble.build_archetype_contract_md(d)
    html = assemble.build_archetype_contract_html(d)
    assert "页面结构范式契约" in md and "`list`" in md and "M01-P01" in md
    assert '<table class="spec-table' in html and "list" in html
    # 无 page_archetypes → 空（保 Commit1 行为/向后兼容）
    d0 = _scaffold(with_arch=False)
    assert assemble.build_archetype_contract_md(d0) == ""
    assert assemble.build_archetype_contract_html(d0) == ""


def test_inject_appends_contract_and_idempotent():
    d = _scaffold()
    spec0 = "## S0\n\n<!-- [SITEMAP-3.0] -->\n\n### 3.1\n"
    s1, ok = assemble.inject_spec_sitemap(spec0, d)
    assert ok and "页面结构范式契约" in s1 and "```mermaid" in s1
    s2, _ = assemble.inject_spec_sitemap(s1, d)
    assert s2 == s1  # 确定性重入幂等
    # 无 archetypes：仅 hierarchy，无契约（Commit1 行为不回归）
    s_noarch, _ = assemble.inject_spec_sitemap(spec0, _scaffold(with_arch=False))
    assert "页面结构范式契约" not in s_noarch and "```mermaid" in s_noarch


# ── precheck.check_page_archetype_contract ─────────────────────────────────

def _spec_with_contract(d):
    base = "## S0\n\n<!-- [SITEMAP-3.0] -->\n\n### 3.1\n"
    out, _ = assemble.inject_spec_sitemap(base, d)
    return out


def _prd_with_contract(d):
    base = '<section id="spec-sitemap"><div class="spec-body"><!-- [SITEMAP-PRD] --></div></section>'
    out, _ = assemble.inject_prd_sitemap(base, d)
    return out


def test_check_contract_legal_passes():
    d = _scaffold()
    r = precheck_stage4.Report()
    precheck_stage4.check_page_archetype_contract(
        d, _spec_with_contract(d), _prd_with_contract(d), r)
    assert r.errors == [], r.errors


def test_check_contract_missing_archetypes_fails():
    d = _scaffold(with_arch=False)
    r = precheck_stage4.Report()
    precheck_stage4.check_page_archetype_contract(d, "x", "y", r)
    assert any("page_archetypes" in e for e in r.errors)


def test_check_contract_dangling_fails():
    d = _scaffold(archetype="ghost")
    r = precheck_stage4.Report()
    precheck_stage4.check_page_archetype_contract(
        d, _spec_with_contract(d), _prd_with_contract(d), r)
    assert any("悬空" in e for e in r.errors)


def test_check_contract_missing_table_fails():
    d = _scaffold()
    r = precheck_stage4.Report()
    # spec/prd 无契约表（模拟未重跑 assemble）
    precheck_stage4.check_page_archetype_contract(
        d, "## S0 无契约", "<section id=\"spec-sitemap\"></section>", r)
    assert any("页面结构范式契约" in e for e in r.errors)


# ── precheck.check_archetype_containment_record ────────────────────────────

def test_record_no_subprogress_warns_not_fail():
    d = _scaffold()
    r = precheck_stage4.Report()
    precheck_stage4.check_archetype_containment_record(d, r)
    assert r.errors == []  # 无子进度文件 → WARN skip，非 FAIL
    assert any("跳过" in w for w in r.warnings)


def _setup_repo(monkeypatch, tmp_path, record_body: str | None):
    prog = tmp_path / "process_record" / "progress"
    prog.mkdir(parents=True)
    if record_body is not None:
        (prog / "stage4_P_M01_plan.md").write_text(record_body, encoding="utf-8")
    monkeypatch.setattr(precheck_stage4, "REPO_ROOT", tmp_path)


def test_record_complete_ok(monkeypatch, tmp_path):
    _setup_repo(monkeypatch, tmp_path,
                "## 页面结构容纳性校验记录\n\n"
                "| 页面 | archetype | 结论 | 说明 |\n|--|--|--|--|\n"
                "| M01-P01 | list | PASS | — |\n")
    r = precheck_stage4.Report()
    precheck_stage4.check_archetype_containment_record(_scaffold(), r)
    assert r.errors == [], r.errors


def test_record_missing_section_fails(monkeypatch, tmp_path):
    _setup_repo(monkeypatch, tmp_path, "## 别的段\n无记录\n")
    r = precheck_stage4.Report()
    precheck_stage4.check_archetype_containment_record(_scaffold(), r)
    assert any("页面结构容纳性校验记录" in e for e in r.errors)


def test_record_uncovered_page_fails(monkeypatch, tmp_path):
    d = _scaffold()
    d["modules"][0]["pages"].append(
        {"id": "P02", "name": "详情", "route": "/d", "archetype": "list", "states": []})
    _setup_repo(monkeypatch, tmp_path,
                "## 页面结构容纳性校验记录\n\n| M01-P01 | list | PASS | — |\n")
    r = precheck_stage4.Report()
    precheck_stage4.check_archetype_containment_record(d, r)
    assert any("未覆盖" in e for e in r.errors)


def test_record_bad_conclusion_fails(monkeypatch, tmp_path):
    _setup_repo(monkeypatch, tmp_path,
                "## 页面结构容纳性校验记录\n\n| M01-P01 | list | 待定 | — |\n")
    r = precheck_stage4.Report()
    precheck_stage4.check_archetype_containment_record(_scaffold(), r)
    assert any("PASS/FAIL" in e for e in r.errors)
