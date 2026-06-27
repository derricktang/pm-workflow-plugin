"""测试提议3 模块架构说明跨阶段（SSOT 双锚 #40 / S4-31）。

覆盖：
- assemble.build_module_arch_md/_html：有 modules → 模块表+依赖 mermaid；
  purpose 缺省 → 职责回退 "—"；无 modules → ""（优雅降级）
- gen_scaffold.validate_v2_schema：purpose 非 str → 报；缺省不报（D2）
- inject_spec/prd_sitemap：模块架构块追加 + 重入幂等
- precheck_stage4.check_module_architecture：合法/缺 spec 块/缺 prd 块/
  模块行数不对称/依赖边数不对称
- precheck_stage3.check_section_6_5：阶段3 §6.5 模块数 == 阶段2 §一（monkeypatch
  OUTPUT_DIR）；不对称 FAIL；无阶段2 文件 WARN
"""

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import assemble
import gen_scaffold
import precheck_stage3
import precheck_stage4


def _scaffold(purpose=True):
    m1 = {"id": "M01", "name": "反馈[管理]", "candidate_components": {"pub": [], "proj_gaps": []},
          "owner_assignments": {}, "depends_on": [{"module": "M02", "kind": "data_flow", "target": "x"}],
          "pages": [{"id": "P01", "name": "l", "route": "/l", "archetype": "list", "states": []}]}
    m2 = {"id": "M02", "name": '用户"中心"', "candidate_components": {"pub": [], "proj_gaps": []},
          "owner_assignments": {}, "depends_on": [],
          "pages": [{"id": "P01", "name": "p", "route": "/p", "archetype": "list", "states": []}]}
    if purpose:
        m1["purpose"] = "负责反馈收集"
    d = {"schema_version": "v2.0", "product": "P", "modules": [m1, m2],
         "page_archetypes": [{"id": "list", "name": "列表页", "regions": [{"slot": "a", "hosts": "b"}],
                              "invariants": [], "extension": []}]}
    return d


# ── assemble 派生 ──────────────────────────────────────────────────────────

def test_module_arch_md_table_and_mermaid():
    md = assemble.build_module_arch_md(_scaffold())
    assert "#### 模块架构说明" in md
    assert "| `M01` | 反馈[管理] | 负责反馈收集 | data_flow→M02 |" in md
    assert "| `M02` | 用户\"中心\" | — | — |" in md  # purpose 缺省回退 —
    assert "graph TB" in md and "M01 -->|data_flow| M02" in md  # Item 3 方向 LR→TB
    assert "&quot;" in md  # mermaid 标签转义（M02 名含引号）


def test_module_arch_graceful_and_purpose_fallback():
    assert assemble.build_module_arch_md({"modules": []}) == ""
    assert assemble.build_module_arch_html({}) == ""
    md = assemble.build_module_arch_md(_scaffold(purpose=False))
    assert "| `M01` | 反馈[管理] | — |" in md  # 无 purpose 回退
    html = assemble.build_module_arch_html(_scaffold())
    assert '<table class="spec-table' in html and '<pre class="mermaid"' in html


def test_validate_purpose_optional():
    g = gen_scaffold.validate_v2_schema(_scaffold())
    assert not any("purpose" in e for e in g)  # 有 purpose 合法
    g0 = gen_scaffold.validate_v2_schema(_scaffold(purpose=False))
    assert not any("purpose" in e for e in g0)  # 缺省不报（D2）
    bad = _scaffold()
    bad["modules"][0]["purpose"] = 123
    assert any("purpose" in e for e in gen_scaffold.validate_v2_schema(bad))


def test_inject_appends_module_arch_idempotent():
    d = _scaffold()
    spec0 = "## S0\n\n<!-- [SITEMAP-3.0] -->\n\n### 3.1\n"
    s1, ok = assemble.inject_spec_sitemap(spec0, d)
    assert ok and "模块架构说明" in s1 and "页面层级架构" in s1
    s2, _ = assemble.inject_spec_sitemap(s1, d)
    assert s2 == s1  # 确定性重入幂等
    prd0 = '<section id="spec-sitemap"><div class="spec-body"><!-- [SITEMAP-PRD] --></div></section>'
    p1, ok2 = assemble.inject_prd_sitemap(prd0, d)
    assert ok2 and "模块架构说明" in p1
    p2, _ = assemble.inject_prd_sitemap(p1, d)
    assert p2 == p1


# ── precheck_stage4.check_module_architecture（S4-31）──────────────────────

def _spec(d):
    out, _ = assemble.inject_spec_sitemap("## S0\n<!-- [SITEMAP-3.0] -->\n### 3.1\n", d)
    return out


def _prd(d):
    out, _ = assemble.inject_prd_sitemap(
        '<section id="spec-sitemap"><div class="spec-body"><!-- [SITEMAP-PRD] --></div></section>', d)
    return out


def test_check_module_arch_legal():
    d = _scaffold()
    r = precheck_stage4.Report()
    precheck_stage4.check_module_architecture(d, _spec(d), _prd(d), r)
    assert r.errors == [], r.errors


def test_check_module_arch_missing_spec_block():
    d = _scaffold()
    r = precheck_stage4.Report()
    precheck_stage4.check_module_architecture(d, "## S0 无模块架构", _prd(d), r)
    assert any("spec §3.0 缺" in e for e in r.errors)


def test_check_module_arch_row_count_mismatch():
    d = _scaffold()
    spec_ok, prd_ok = _spec(d), _prd(d)
    d2 = _scaffold()
    d2["modules"].append({"id": "M03", "name": "x", "candidate_components": {"pub": [], "proj_gaps": []},
                          "owner_assignments": {}, "depends_on": [],
                          "pages": [{"id": "P01", "name": "x", "route": "/x", "archetype": "list", "states": []}]})
    r = precheck_stage4.Report()
    precheck_stage4.check_module_architecture(d2, spec_ok, prd_ok, r)
    assert any("行数" in e for e in r.errors)


# ── precheck_stage3.check_section_6_5 ──────────────────────────────────────

_S65 = """## 6.5 产品架构（来源：阶段 2 §三）

> SSOT 派生约束。

| 模块 | 名称 | 职责（一句话） | 依赖于（模块 + 原因）|
|------|------|---------------|---------------------|
| M1 | 反馈管理 | 负责反馈 | 无 |
| M2 | 用户中心 | 负责用户 | M1：读反馈数 |

## 7. 功能需求
"""


def _stage2(tmp, n):
    f = tmp / "功能规划_测试_latest.md"
    body = "## 一、功能模块清单\n\n### 模块总览\n\n"
    for i in range(1, n + 1):
        body += f"### M{i}：模块{i}\n\n内容\n\n"
    body += "## 二、业务流程图\n"
    f.write_text(body, encoding="utf-8")


def test_section_6_5_parity_ok(monkeypatch, tmp_path):
    _stage2(tmp_path, 2)
    monkeypatch.setattr(precheck_stage3, "OUTPUT_DIR", tmp_path)
    r = precheck_stage3.Report()
    precheck_stage3.check_section_6_5(_S65, r)
    assert r.errors == [], r.errors


def test_section_6_5_parity_mismatch(monkeypatch, tmp_path):
    _stage2(tmp_path, 3)  # 阶段2 三个模块 vs §6.5 两行
    monkeypatch.setattr(precheck_stage3, "OUTPUT_DIR", tmp_path)
    r = precheck_stage3.Report()
    precheck_stage3.check_section_6_5(_S65, r)
    assert any("不对称" in e for e in r.errors)


def test_section_6_5_no_stage2_warns(monkeypatch, tmp_path):
    monkeypatch.setattr(precheck_stage3, "OUTPUT_DIR", tmp_path)  # 空目录无阶段2
    r = precheck_stage3.Report()
    precheck_stage3.check_section_6_5(_S65, r)
    assert r.errors == [] and any("未找到" in w for w in r.warnings)
