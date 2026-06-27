"""测试 gen_scaffold.py 关键函数（专注 _resolve_proj_id 三优先级）。

覆盖场景（issue 2026-05-08：bujue-quotation-tool 反向回流 L1 inherits=null bug）：
- 优先级 1：global_owners 命中 → 用真源
- 优先级 2：inherits 解析（含 None / 空串容错）
- 优先级 3：全部失败 → proj.LX.{name}（未知层级）
"""

import sys
from pathlib import Path

# 确保 pm-workflow/scripts 在 import path 内
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import gen_scaffold


class TestResolveProjId:
    """覆盖 _resolve_proj_id 三优先级 + 容错。"""

    def test_priority_1_global_owners_hit(self) -> None:
        """优先级 1：global_owners 中存在 proj.LX.{name} → 直接返回该键。
        L1 组件常见场景（inherits=None）的核心修复点。"""
        gap = {"name": "lang-switcher", "inherits": None}
        global_owners = {
            "proj.L1.lang-switcher": "M01",
            "proj.L2.product-card": "M02",
        }
        assert gen_scaffold._resolve_proj_id(gap, global_owners) == "proj.L1.lang-switcher"

    def test_priority_1_global_owners_with_empty_inherits(self) -> None:
        """优先级 1：inherits 为空串时同样从 owner_assignments 命中。"""
        gap = {"name": "rich-textarea", "inherits": ""}
        global_owners = {"proj.L1.rich-textarea": "M03"}
        assert gen_scaffold._resolve_proj_id(gap, global_owners) == "proj.L1.rich-textarea"

    def test_priority_2_inherits_fallback(self) -> None:
        """优先级 2：global_owners 无该 name → 走 inherits 解析。"""
        gap = {"name": "product-card", "inherits": "pub.L2.card"}
        global_owners = {"proj.L1.lang-switcher": "M01"}  # 不含 product-card
        assert gen_scaffold._resolve_proj_id(gap, global_owners) == "proj.L2.product-card"

    def test_priority_2_inherits_no_global_owners(self) -> None:
        """优先级 2：global_owners=None 也能 fallback 解析 inherits。"""
        gap = {"name": "tag-badge", "inherits": "pub.L0.tag"}
        assert gen_scaffold._resolve_proj_id(gap) == "proj.L0.tag-badge"

    def test_priority_3_inherits_none_no_owner(self) -> None:
        """优先级 3：inherits=None 且 global_owners 无该 name → proj.LX.{name}。
        Bug 修复前的退化场景：原代码 `re.search(r"L(\\d+)", None)` 抛 TypeError。"""
        gap = {"name": "orphan-comp", "inherits": None}
        global_owners = {"proj.L1.other": "M01"}
        assert gen_scaffold._resolve_proj_id(gap, global_owners) == "proj.LX.orphan-comp"

    def test_priority_3_no_inherits_key_no_owner(self) -> None:
        """优先级 3：inherits 字段不存在(L1 PM 写 scaffold 时漏填) → 同上。"""
        gap = {"name": "no-key-comp"}
        assert gen_scaffold._resolve_proj_id(gap) == "proj.LX.no-key-comp"

    def test_no_typeerror_on_inherits_none(self) -> None:
        """回归测试：原 bug 是 inherits=None 时 re.search(re, None) → TypeError。
        修复后 None 容错通过 `gap.get("inherits") or ""`。"""
        gap = {"name": "test", "inherits": None}
        # 不应抛异常
        result = gen_scaffold._resolve_proj_id(gap)
        assert result == "proj.LX.test"

    def test_global_owners_partial_match_skipped(self) -> None:
        """边界：global_owners 中仅前缀匹配（同名不同层级不应误命中,实际上 name 应全局唯一）。"""
        gap = {"name": "card", "inherits": "pub.L2.card"}
        global_owners = {"proj.L3.product-card": "M01"}  # name 不同（product-card vs card）
        assert gen_scaffold._resolve_proj_id(gap, global_owners) == "proj.L2.card"


class TestValidateV2SchemaLogicOnly:
    """覆盖 validate_v2_schema logic-only 模块校验（SSOT #50，2026-05-28 落地）。

    场景：pages=[] 视为 logic-only 模块（业务逻辑层 / API 层无独立 UI），必须含 ui_carrier_modules
    非空数组 + 引用 ⊂ scaffold.modules[].id。详 agent_dispatch_protocol.md「logic-only 模块说明」。
    """

    def _make_scaffold(self, modules: list) -> dict:
        """构造 minimal v2.0 scaffold（含 page_archetypes 顶层 + 必填字段填充）。"""
        return {
            "schema_version": "v2.0",
            "product": "测试产品",
            "page_archetypes": [
                {"id": "list", "name": "列表", "frames": [], "invariants": [], "extension": []},
            ],
            "modules": modules,
        }

    def _ui_mod(self, mid: str) -> dict:
        """构造一个最小合法 UI 模块（pages 非空）。"""
        return {
            "id": mid,
            "name": f"UI 模块 {mid}",
            "candidate_components": {"pub": [], "proj_gaps": []},
            "owner_assignments": {},
            "depends_on": [],
            "pages": [{"id": "P01", "name": "页1", "archetype": "list",
                       "states": [{"name": "default", "roles": []}]}],
        }

    def _logic_only_mod(self, mid: str, ui_carriers) -> dict:
        """构造 logic-only 模块（pages=[] + ui_carrier_modules）。"""
        m = {
            "id": mid,
            "name": f"逻辑模块 {mid}",
            "candidate_components": {"pub": [], "proj_gaps": []},
            "owner_assignments": {},
            "depends_on": [],
            "pages": [],
        }
        if ui_carriers is not None:
            m["ui_carrier_modules"] = ui_carriers
        return m

    def test_logic_only_pass_with_valid_ui_carriers(self) -> None:
        """合法 logic-only：pages=[] + ui_carrier_modules 非空数组 + 引用合法 → 无错误。"""
        data = self._make_scaffold([
            self._ui_mod("M01"),
            self._logic_only_mod("M02", ["M01"]),
        ])
        errors = gen_scaffold.validate_v2_schema(data)
        # 仅关注 logic-only 相关错误（其他维度可能因 minimal scaffold 触发，过滤后应为 0）
        logic_errors = [e for e in errors if "M02" in e and ("ui_carrier" in e or "logic-only" in e)]
        assert logic_errors == [], f"合法 logic-only 不应触发任何 ui_carrier 校验错误：{logic_errors}"

    def test_logic_only_fail_missing_ui_carriers(self) -> None:
        """pages=[] 但缺 ui_carrier_modules 字段 → FAIL。"""
        data = self._make_scaffold([
            self._ui_mod("M01"),
            self._logic_only_mod("M02", None),
        ])
        errors = gen_scaffold.validate_v2_schema(data)
        assert any("M02" in e and "ui_carrier_modules" in e and "logic-only" in e for e in errors), \
            f"缺 ui_carrier_modules 必须报错；实际：{errors}"

    def test_logic_only_fail_empty_ui_carriers(self) -> None:
        """ui_carrier_modules=[] 空数组 → FAIL。"""
        data = self._make_scaffold([
            self._ui_mod("M01"),
            self._logic_only_mod("M02", []),
        ])
        errors = gen_scaffold.validate_v2_schema(data)
        assert any("M02" in e and "ui_carrier_modules" in e and "非空数组" in e for e in errors), \
            f"空 ui_carrier_modules 必须报错；实际：{errors}"

    def test_logic_only_fail_non_array_ui_carriers(self) -> None:
        """ui_carrier_modules 非数组（字符串） → FAIL。"""
        data = self._make_scaffold([
            self._ui_mod("M01"),
            self._logic_only_mod("M02", "M01"),  # 应为数组而非字符串
        ])
        errors = gen_scaffold.validate_v2_schema(data)
        assert any("M02" in e and "ui_carrier_modules" in e and "非空数组" in e for e in errors), \
            f"非数组 ui_carrier_modules 必须报错；实际：{errors}"

    def test_logic_only_fail_invalid_ref(self) -> None:
        """ui_carrier_modules 引用不存在的模块 id → FAIL（引用完整性）。"""
        data = self._make_scaffold([
            self._ui_mod("M01"),
            self._logic_only_mod("M02", ["M99"]),  # M99 不存在
        ])
        errors = gen_scaffold.validate_v2_schema(data)
        assert any("M02" in e and "ui_carrier_modules" in e and "M99" in e for e in errors), \
            f"非法引用必须报错；实际：{errors}"

    def test_normal_module_no_ui_carrier_check(self) -> None:
        """普通模块（pages 非空）不应触发 ui_carrier_modules 校验（即使该字段不存在）。"""
        data = self._make_scaffold([self._ui_mod("M01")])
        errors = gen_scaffold.validate_v2_schema(data)
        assert not any("ui_carrier" in e for e in errors), \
            f"普通模块不应触发 ui_carrier 校验；实际：{errors}"

    def test_logic_only_fail_self_reference(self) -> None:
        """ui_carrier_modules 自引（M02 → M02） → FAIL（自引非法）。"""
        data = self._make_scaffold([
            self._ui_mod("M01"),
            self._logic_only_mod("M02", ["M02"]),  # 自引
        ])
        errors = gen_scaffold.validate_v2_schema(data)
        assert any("M02" in e and "自引" in e for e in errors), \
            f"自引必须 FAIL；实际：{errors}"

    def test_logic_only_fail_pointing_to_logic_only(self) -> None:
        """ui_carrier_modules 指向其他 logic-only 模块（M02 → M03 也是 logic-only） → FAIL（禁链式/环引）。"""
        data = self._make_scaffold([
            self._ui_mod("M01"),
            self._logic_only_mod("M02", ["M03"]),  # 指向 M03
            self._logic_only_mod("M03", ["M01"]),  # M03 也是 logic-only
        ])
        errors = gen_scaffold.validate_v2_schema(data)
        assert any(
            "M02" in e and "logic-only" in e and "M03" in e for e in errors
        ), f"指向 logic-only 必须 FAIL；实际：{errors}"

    def test_pages_missing_field_fails(self) -> None:
        """模块完全缺 pages 字段（不是 [] 而是 key 不存在）→ FAIL。"""
        bad_mod = {
            "id": "M02",
            "name": "缺 pages 模块",
            "candidate_components": {"pub": [], "proj_gaps": []},
            "owner_assignments": {},
            "depends_on": [],
            # 没有 pages 字段
        }
        data = self._make_scaffold([self._ui_mod("M01"), bad_mod])
        errors = gen_scaffold.validate_v2_schema(data)
        assert any("M02" in e and "缺 pages 字段" in e for e in errors), \
            f"缺 pages 字段必须 FAIL；实际：{errors}"

    def test_pages_non_array_fails(self) -> None:
        """pages 非数组类型（如字符串）→ FAIL。"""
        bad_mod = {
            "id": "M02",
            "name": "pages 非数组",
            "candidate_components": {"pub": [], "proj_gaps": []},
            "owner_assignments": {},
            "depends_on": [],
            "pages": "not_an_array",
        }
        data = self._make_scaffold([self._ui_mod("M01"), bad_mod])
        errors = gen_scaffold.validate_v2_schema(data)
        assert any("M02" in e and "pages 必须为数组" in e for e in errors), \
            f"pages 非数组必须 FAIL；实际：{errors}"


class TestSpecItemsSidebarLabel:
    """SSOT #67 — SPEC_ITEMS sidebar 字面与 prd_expression_standard §三 A-05 真源对齐。

    锁定 spec-feature 节的 sidebar 标签字面为「功能索引」，
    防止 gen_scaffold 字面回退到旧字「功能需求规格」造成 sidebar 与 PRD 主体
    A-05 标题双源漂移（治本 NB-HF-01 — assemble.py inject_function_overview_index
    Bug 1 仅替换 spec-feature section 内 spec-header 字面，不影响 sidebar，
    故 sidebar 必须由 SPEC_ITEMS 源头正确）。
    """

    def test_spec_feature_label_is_function_index(self) -> None:
        """SPEC_ITEMS 中 spec-feature 节标签必须为「功能索引」（SSOT #67 真源）。"""
        labels = dict(gen_scaffold.SPEC_ITEMS)
        assert labels.get("spec-feature") == "功能索引", \
            f"spec-feature 标签必须为「功能索引」（SSOT #67 A-05 重组）；实际：{labels.get('spec-feature')!r}"

    def test_build_spec_nav_emits_function_index_label(self) -> None:
        """build_spec_nav 输出含「功能索引」字面 + 不含旧字「功能需求规格」。"""
        nav = gen_scaffold.build_spec_nav()
        assert "功能索引" in nav, "build_spec_nav 应含「功能索引」字面"
        assert "功能需求规格" not in nav, "build_spec_nav 不应残留旧字「功能需求规格」"
