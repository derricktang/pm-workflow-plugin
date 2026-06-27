"""测试 S4-34 触点 canonical 引用完整性（SSOT 双锚 #44，item 6 治本）。

覆盖：
- gen_scaffold.validate_v2_schema：touchpoints 可选（缺省不报错）/ id 格式 / 页面内唯一 / kind 枚举
- gen_scaffold.build_spec_module_draft：有 touchpoints 预填 canonical 行 / 无则旧静态占位
- precheck_stage4._build_touchpoint_canonical：构集
- precheck_stage4.check_touchpoint_canonical：无声明跳过(OK) / 全 ⊆ canonical(OK) /
  outside-canonical(WARN) / unreferenced(WARN)
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import gen_scaffold
import precheck_stage4
from precheck_stage4 import (
    Report,
    _build_touchpoint_canonical,
    check_touchpoint_canonical,
)


def _scaffold_with_tps(touchpoints):
    return {
        "schema_version": "v2.0",
        "modules": [
            {
                "id": "M01",
                "candidate_components": {"pub": [], "proj_gaps": []},
                "owner_assignments": {},
                "pages": [
                    {
                        "id": "P01",
                        "name": "列表页",
                        "route": "/x",
                        "states": [],
                        "touchpoints": touchpoints,
                    }
                ],
            }
        ],
    }


# ── validate_v2_schema touchpoints ───────────────────────────────────────────


def test_validate_touchpoints_optional():
    """无 touchpoints 字段不报错（向后兼容）。"""
    d = {
        "schema_version": "v2.0",
        "modules": [
            {
                "id": "M01",
                "candidate_components": {"pub": [], "proj_gaps": []},
                "owner_assignments": {},
                "pages": [{"id": "P01", "states": []}],
            }
        ],
    }
    errs = [e for e in gen_scaffold.validate_v2_schema(d) if "touchpoint" in e.lower()]
    assert errs == []


def test_validate_touchpoints_legal():
    d = _scaffold_with_tps(
        [{"id": "T01", "kind": "trigger", "element": "按钮", "action": "点击"},
         {"id": "D01", "kind": "data"}]
    )
    errs = [e for e in gen_scaffold.validate_v2_schema(d) if "touchpoint" in e.lower()]
    assert errs == []


def test_validate_touchpoints_bad_id_and_dup_and_kind():
    d = _scaffold_with_tps(
        [{"id": "T1"}, {"id": "T01"}, {"id": "T01"}, {"id": "X99", "kind": "bad"}]
    )
    errs = [e for e in gen_scaffold.validate_v2_schema(d) if "touchpoint" in e.lower()]
    joined = " ".join(errs)
    assert "T1" in joined  # 格式错
    assert "重复" in joined  # T01 dup
    assert "X99" in joined  # 格式错
    assert "kind" in joined  # bad kind


# ── build_spec_module_draft 触点表预生成 ─────────────────────────────────────


def test_spec_draft_prefills_canonical_rows():
    mod = {
        "id": "M01",
        "name": "项目管理",
        "pages": [
            {
                "id": "P01",
                "name": "列表页",
                "route": "/x",
                "states": [],
                "touchpoints": [
                    {"id": "T01", "kind": "trigger", "element": "新建按钮", "action": "点击"},
                    {"id": "D01", "kind": "data", "element": "名称回显"},
                ],
            }
        ],
    }
    draft = gen_scaffold.build_spec_module_draft(mod)
    assert "M01-P01-T01" in draft
    assert "M01-P01-D01" in draft
    assert "新建按钮" in draft
    assert "scaffold canonical 预生成" in draft
    assert "禁止增删" in draft


def test_spec_draft_fallback_no_touchpoints():
    """无 touchpoints → 旧静态占位 + 两段式提示（含治本路径建议）。"""
    mod = {
        "id": "M02",
        "name": "用户中心",
        "pages": [{"id": "P01", "name": "页", "route": "/y", "states": []}],
    }
    draft = gen_scaffold.build_spec_module_draft(mod)
    assert "M02-P01-T01" in draft  # 静态占位
    assert "治本路径" in draft


# ── _build_touchpoint_canonical ──────────────────────────────────────────────


def test_build_canonical_set():
    d = _scaffold_with_tps([{"id": "T01"}, {"id": "D01"}])
    canonical = _build_touchpoint_canonical(d)
    assert canonical == {"M01-P01-T01", "M01-P01-D01"}


def test_build_canonical_empty_when_no_touchpoints():
    d = {
        "schema_version": "v2.0",
        "modules": [{"id": "M01", "pages": [{"id": "P01", "states": []}]}],
    }
    assert _build_touchpoint_canonical(d) == set()


# ── check_touchpoint_canonical ───────────────────────────────────────────────


def test_check_skip_when_no_canonical():
    """scaffold 无 touchpoints → 跳过(OK)，不阻断旧产物。"""
    d = {"schema_version": "v2.0", "modules": [{"id": "M01", "pages": [{"id": "P01", "states": []}]}]}
    r = Report()
    check_touchpoint_canonical(d, "spec M01-P01-T01 引用", "<html>M01-P01-T01</html>", r)
    assert len(r.errors) == 0 and len(r.warnings) == 0 and r.passed == 1


def test_check_all_within_canonical():
    d = _scaffold_with_tps([{"id": "T01"}, {"id": "T02"}])
    spec = "触点 M01-P01-T01 与 M01-P01-T02"
    prd = '<pre>M01-P01-T01</pre><span data-tp="M01-P01-T02">x</span>'
    r = Report()
    check_touchpoint_canonical(d, spec, prd, r)
    assert len(r.errors) == 0 and len(r.warnings) == 0 and r.passed == 1


def test_check_outside_canonical_warns():
    """spec/prd 引用了 canonical 外的 ID（手写偏差）→ WARN。"""
    d = _scaffold_with_tps([{"id": "T01"}])
    spec = "M01-P01-T01 与手写错的 M01-P01-T09"
    prd = "<html>M01-P01-T01</html>"
    r = Report()
    check_touchpoint_canonical(d, spec, prd, r)
    assert len(r.errors) == 0
    assert any("不在 scaffold canonical" in w for w in r.warnings)
    assert any("M01-P01-T09" in w for w in r.warnings)


def test_check_unreferenced_canonical_warns():
    """scaffold 声明的 canonical 未被 spec/prd 引用 → WARN。"""
    d = _scaffold_with_tps([{"id": "T01"}, {"id": "T02"}])
    spec = "仅用 M01-P01-T01"
    prd = "<html>M01-P01-T01</html>"
    r = Report()
    check_touchpoint_canonical(d, spec, prd, r)
    assert len(r.errors) == 0
    assert any("未被引用" in w and "M01-P01-T02" in w for w in r.warnings)
