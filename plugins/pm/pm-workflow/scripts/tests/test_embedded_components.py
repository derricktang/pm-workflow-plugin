"""测试 embedded_components 内嵌子组件构造（SSOT #76 R3）。

治实验报告问题 4 根因：scaffold 缺"内嵌带状态构造" → PM 逼出页膨胀。
内嵌子组件隶属某 page、含自己的 states（各带 prd_id），复用 prd_id→section→
FRAME→nav 全套机器，但不占独立 page/route。

覆盖维度：
1. iter_page_prd_ids helper（直挂 + 内嵌；向后兼容；robustness）
2. validate_v2_schema 内嵌结构校验（合法 / 缺 id / 撞 id / 空 states / 越界 prefix / 撞号）
3. 渲染派生（build_proto_nav 第 4 层 / build_module_sections section+FRAME / build_prd_module_draft draft FRAME）
4. precheck 集成（check_scaffold 内嵌 prd_id 校验 / #72 frame 一致性含内嵌 / check_prd 含内嵌）
5. 向后兼容（无 embedded_components → 行为零变化）
"""

import copy
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import gen_scaffold
import precheck_stage4
from precheck_stage4 import Report


def _emb() -> dict:
    """一个最小合法内嵌子组件（强制下架卡片，对应实验报告决定性案例）。"""
    return {
        "id": "offshelf",
        "name": "强制下架卡片",
        "archetype": "modal-confirm",
        "states": [
            {"name": "default", "prd_id": "H-M01-P01-offshelf-default", "roles": ["管理员"]},
            {"name": "error", "prd_id": "H-M01-P01-offshelf-error", "roles": ["管理员"]},
        ],
    }


def _page_with_emb() -> dict:
    """带 1 个内嵌子组件（2 态）的页面。"""
    return {
        "id": "P01",
        "name": "主页设置",
        "route": "/admin/home",
        "archetype": "readonly-status",
        "states": [
            {"name": "default", "prd_id": "H-M01-P01-default", "roles": ["管理员"]},
        ],
        "embedded_components": [_emb()],
    }


def _scaffold_with_emb() -> dict:
    """完整 v2.0 scaffold（含 page_archetypes + 1 内嵌页）。"""
    return {
        "schema_version": "v2.0",
        "product": "测试产品",
        "platforms": ["桌面Web"],
        "page_archetypes": [
            {"id": "readonly-status", "name": "只读状态", "semantic_category": "readonly-status",
             "regions": [{"slot": "main", "hosts": "x"}], "invariants": [], "extension": []},
            {"id": "modal-confirm", "name": "弹窗确认", "semantic_category": "modal-confirm",
             "regions": [{"slot": "main", "hosts": "x"}], "invariants": [], "extension": []},
        ],
        "modules": [
            {
                "id": "M01",
                "name": "主页设置模块",
                "task_card": "process_record/tasks/task_M01.md",
                "depends_on": [],
                "candidate_components": {"pub": [], "proj_gaps": []},
                "owner_assignments": {},
                "pages": [_page_with_emb()],
            }
        ],
    }


# ── 1. iter_page_prd_ids helper ───────────────────────────────────────────────


class TestIterPagePrdIds:
    def test_direct_plus_embedded(self) -> None:
        ids = list(gen_scaffold.iter_page_prd_ids(_page_with_emb()))
        assert ids == [
            "H-M01-P01-default",
            "H-M01-P01-offshelf-default",
            "H-M01-P01-offshelf-error",
        ], f"应先 yield 直挂 states 再 yield 内嵌 states，实际：{ids}"

    def test_backward_compat_no_embedded(self) -> None:
        """无 embedded_components → 仅 yield 直挂 states（向后兼容，行为零变化）。"""
        page = {"id": "P01", "states": [{"name": "d", "prd_id": "H-M01-P01-d"}]}
        assert list(gen_scaffold.iter_page_prd_ids(page)) == ["H-M01-P01-d"]

    def test_robustness_non_dict(self) -> None:
        assert list(gen_scaffold.iter_page_prd_ids(None)) == []
        assert list(gen_scaffold.iter_page_prd_ids({"states": [None, "x"]})) == []

    def test_empty_embedded_array(self) -> None:
        page = {"states": [{"prd_id": "H-M01-P01-d"}], "embedded_components": []}
        assert list(gen_scaffold.iter_page_prd_ids(page)) == ["H-M01-P01-d"]


# ── 2. validate_v2_schema 内嵌校验 ────────────────────────────────────────────


class TestValidateEmbedded:
    def _emb_errors(self, data: dict) -> list[str]:
        return [
            e for e in gen_scaffold.validate_v2_schema(data)
            if "内嵌" in e or "embedded_components" in e
        ]

    def test_valid_embedded_no_errors(self) -> None:
        assert self._emb_errors(_scaffold_with_emb()) == []

    def test_missing_id(self) -> None:
        s = _scaffold_with_emb()
        del s["modules"][0]["pages"][0]["embedded_components"][0]["id"]
        assert any("缺合法 id" in e for e in self._emb_errors(s))

    def test_duplicate_id(self) -> None:
        s = _scaffold_with_emb()
        embs = s["modules"][0]["pages"][0]["embedded_components"]
        dup = copy.deepcopy(embs[0])
        dup["states"] = [{"name": "x", "prd_id": "H-M01-P01-offshelf2-x"}]
        embs.append(dup)  # 同 id 'offshelf'
        assert any("id 页内重复" in e for e in self._emb_errors(s))

    def test_empty_states(self) -> None:
        s = _scaffold_with_emb()
        s["modules"][0]["pages"][0]["embedded_components"][0]["states"] = []
        assert any("states 必须为非空数组" in e for e in self._emb_errors(s))

    def test_prd_id_wrong_scope(self) -> None:
        """内嵌 prd_id 不以父页 H-M01-P01- 前缀开头 → FAIL。"""
        s = _scaffold_with_emb()
        s["modules"][0]["pages"][0]["embedded_components"][0]["states"][0]["prd_id"] = "H-M02-P09-x"
        assert any("须以" in e and "开头" in e for e in self._emb_errors(s))

    def test_prd_id_collision_with_page_state(self) -> None:
        """内嵌 prd_id 与直挂 state prd_id 撞号 → FAIL。"""
        s = _scaffold_with_emb()
        s["modules"][0]["pages"][0]["embedded_components"][0]["states"][0]["prd_id"] = "H-M01-P01-default"
        assert any("撞号" in e for e in self._emb_errors(s))

    def test_non_array_embedded(self) -> None:
        s = _scaffold_with_emb()
        s["modules"][0]["pages"][0]["embedded_components"] = "nope"
        assert any("非数组" in e for e in self._emb_errors(s))


# ── 3. 渲染派生 ───────────────────────────────────────────────────────────────


class TestEmbeddedRendering:
    def test_proto_nav_emits_4th_level(self) -> None:
        nav = gen_scaffold.build_proto_nav([_scaffold_with_emb()["modules"][0]])
        assert 'data-subgroup="embed-M01-P01-offshelf"' in nav, "应有内嵌子组 toggle"
        assert "⤷ 强制下架卡片" in nav, "应有内嵌子组名（⤷ 前缀）"
        assert "showSection('H-M01-P01-offshelf-default')" in nav, "应有内嵌状态跳转"
        assert "padding-left:60px" in nav, "内嵌状态应缩进 60px（第 4 层）"

    def test_module_sections_emit_embedded_section_and_frame(self) -> None:
        html = gen_scaffold.build_module_sections([_scaffold_with_emb()["modules"][0]])
        assert '<section id="H-M01-P01-offshelf-default" class="proto-section">' in html
        assert "<!-- [FRAME: H-M01-P01-offshelf-default] -->" in html
        assert "<!-- [FRAME: H-M01-P01-offshelf-error] -->" in html
        assert "内嵌于 P01（无独立路由）" in html, "应标注内嵌无独立路由"

    def test_module_sections_no_embedded_skeleton(self) -> None:
        """内嵌帧不 emit PAGE-SKELETON（骨架 per-page，仅随首个直挂帧）。"""
        html = gen_scaffold.build_module_sections([_scaffold_with_emb()["modules"][0]])
        assert html.count("[PAGE-SKELETON: M01-P01]") == 1, "PAGE-SKELETON 每页仅 1 次"

    def test_prd_draft_emits_embedded_frame_blocks(self) -> None:
        mod = _scaffold_with_emb()["modules"][0]
        draft = gen_scaffold.build_prd_module_draft(mod, [mod])
        assert "<!-- [FRAME: H-M01-P01-offshelf-default] -->" in draft
        assert "<!-- [/FRAME: H-M01-P01-offshelf-error] -->" in draft
        assert draft.count("class=\"interaction-card\"") == 3, "1 直挂 + 2 内嵌 = 3 interaction-card"

    def test_spec_draft_state_table_excludes_embedded(self) -> None:
        """spec 状态表 per-page 只含直挂 states（与 check_spec_state_table_count 一致）。"""
        mod = _scaffold_with_emb()["modules"][0]
        spec = gen_scaffold.build_spec_module_draft(mod)
        assert "H-M01-P01-default" in spec
        assert "H-M01-P01-offshelf-default" not in spec, "内嵌不进 spec 状态表（NB-WE-R3-02）"


# ── 4. precheck 集成 ──────────────────────────────────────────────────────────


class TestPrecheckEmbedded:
    def test_check_scaffold_valid_embedded_passes(self) -> None:
        r = Report()
        precheck_stage4.check_scaffold(_scaffold_with_emb(), r)
        assert r.errors == [], f"合法内嵌 scaffold 不应 FAIL：{r.errors}"

    def test_check_scaffold_embedded_collision_fails(self) -> None:
        s = _scaffold_with_emb()
        s["modules"][0]["pages"][0]["embedded_components"][0]["states"][0]["prd_id"] = "H-M01-P01-default"
        r = Report()
        precheck_stage4.check_scaffold(s, r)
        assert any("内嵌 prd_id 重复" in e for e in r.errors), f"撞号应 FAIL：{r.errors}"

    def test_check_scaffold_embedded_bad_format_fails(self) -> None:
        s = _scaffold_with_emb()
        s["modules"][0]["pages"][0]["embedded_components"][0]["states"][0]["prd_id"] = "BAD-ID"
        r = Report()
        precheck_stage4.check_scaffold(s, r)
        assert any("内嵌 prd_id 格式错误" in e for e in r.errors), f"坏格式应 FAIL：{r.errors}"

    def test_frame_consistency_includes_embedded(self) -> None:
        """#72：scaffold 含内嵌 prd_id，outputs/prd 缺内嵌 FRAME → 漂移 A 含内嵌。"""
        s = _scaffold_with_emb()
        # outputs 仅含直挂帧（缺内嵌）
        prd_html = '<section id="H-M01-P01-default"></section>'
        r = Report()
        precheck_stage4.check_scaffold_outputs_frame_consistency(s, prd_html, r)
        combined = " ".join(r.errors + r.warnings)
        assert "offshelf" in combined, f"内嵌帧应被识别为漂移而非忽略：errors={r.errors} warns={r.warnings}"

    def test_frame_consistency_full_match_with_embedded(self) -> None:
        """#72：outputs 含全部直挂 + 内嵌 FRAME 占位 → 一致 PASS。"""
        s = _scaffold_with_emb()
        prd_html = (
            "<!-- [FRAME: H-M01-P01-default] -->"
            "<!-- [FRAME: H-M01-P01-offshelf-default] -->"
            "<!-- [FRAME: H-M01-P01-offshelf-error] -->"
        )
        r = Report()
        precheck_stage4.check_scaffold_outputs_frame_consistency(s, prd_html, r)
        assert r.errors == [], f"全匹配不应 FAIL：{r.errors}"


# ── 5. 向后兼容（无 embedded_components 行为零变化）────────────────────────────


class TestBackwardCompat:
    def _plain(self) -> dict:
        s = _scaffold_with_emb()
        del s["modules"][0]["pages"][0]["embedded_components"]
        return s

    def test_nav_unchanged_without_embedded(self) -> None:
        nav = gen_scaffold.build_proto_nav([self._plain()["modules"][0]])
        assert "embed-" not in nav, "无内嵌字段时 nav 不应出现内嵌子组"

    def test_sections_unchanged_without_embedded(self) -> None:
        html = gen_scaffold.build_module_sections([self._plain()["modules"][0]])
        assert "offshelf" not in html
        assert html.count("[FRAME:") == 1, "仅 1 直挂帧"

    def test_validate_no_embedded_no_errors(self) -> None:
        errs = [e for e in gen_scaffold.validate_v2_schema(self._plain()) if "内嵌" in e]
        assert errs == []
