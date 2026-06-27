"""测试 gen_render_contract.py — R8 layer 1 契约导出（SSOT #77 WIP）。

覆盖根本原则「忠实转录 spec 权威列，禁推断」：
1. 触点 per-state 转录（.3 所在状态列；含通配「全部」；前缀过滤）
2. 字段 per-page 转录（.4 页面列；data-field 提取；隐式豁免）
3. 平台 per-state 转录（.2 平台列；仅具体平台入选；agnostic 不生项）
4. 人工对照区 NB 引用转录（不进机械区）
5. 确定性（同输入同输出）+ 含内嵌帧（iter_page_prd_ids）
6. provenance zero-item ⚠
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import gen_render_contract as G


# 合成 spec：含 .2 状态枚举 / .3 触点表 / .4 字段绑定（模拟真 spec 列序）
SPEC = """\
## S2.M01.1 页面概述
（略）

## S2.M01.2 状态枚举

| 页面 | 状态名 | 触发条件 | 是否互斥 | 平台 | 页面表现 | prd_id |
|------|--------|---------|---------|------|---------|--------|
| P01 | default | 进入 | 互斥 | agnostic | 卡片默认（NB-003） | `H-M01-P01-default` |
| P01 | mobile-only | 移动进入 | 互斥 | 手机 / 桌面Web | 卡片移动 | `H-M01-P01-mobile-only` |

## S2.M01.2A 元素交互细则
（略）

## S2.M01.3 触点表

| 触点 ID | 所在状态 | 元素 | 触发动作 | 系统响应 | 适用平台 |
|---------|---------|------|---------|---------|---------|
| M01-P01-T01 | default / mobile-only | 上传按钮 | 点击 | 弹 modal（NB-016） | all |
| M01-P01-T02 | default | 配置入口 | 点击 | 跳转 | all |
| M01-P01-T03 | 全部 | 帮助按钮 | 点击 | 提示 | all |
| M02-P01-T01 | other | 别的模块触点 | 点击 | x | all |

## S2.M01.4 数据字段绑定

| 页面 | 字段名 | 类型 | 来源 | 必填 | prd 渲染元素 | prd 属性 |
|------|-------|------|------|------|-------------|---------|
| P01 | package_id | string | §9 | 否 | `<span>` | `data-field="package_id"` |
| P01 | secret_id | string | §9 | ✓ | `<span>` 隐式承载（不显式展示） | `data-field="secret_id"` |
| P01 | created_at | string | §9 | 否 | `<span>` | `data-field="created_at"` |
| P02 | other_field | string | §9 | 否 | `<span>` | `data-field="other_field"` |
"""


def _page():
    return {
        "id": "P01", "name": "首页",
        "states": [
            {"name": "default", "prd_id": "H-M01-P01-default", "roles": []},
            {"name": "mobile-only", "prd_id": "H-M01-P01-mobile-only", "roles": []},
        ],
        "embedded_components": [
            {"id": "card", "name": "子卡片", "states": [
                {"name": "default", "prd_id": "H-M01-P01-card-default", "roles": []},
            ]},
        ],
    }


class TestTouchpointExtraction:
    def test_per_state_filter(self):
        tps = dict(G.extract_touchpoints_for_state(SPEC, "M01", "P01", "default"))
        # default 命中 T01（default/mobile-only）+ T02（default）+ T03（全部通配）
        assert set(tps) == {"M01-P01-T01", "M01-P01-T02", "M01-P01-T03"}

    def test_state_excludes_nonmatching(self):
        tps = dict(G.extract_touchpoints_for_state(SPEC, "M01", "P01", "mobile-only"))
        # mobile-only 命中 T01（含 mobile-only）+ T03（全部），不含 T02（仅 default）
        assert set(tps) == {"M01-P01-T01", "M01-P01-T03"}

    def test_prefix_filter_excludes_other_page(self):
        # M02-P01-T01 前缀不匹配 M01-P01，不应混入
        tps = dict(G.extract_touchpoints_for_state(SPEC, "M01", "P01", "default"))
        assert "M02-P01-T01" not in tps

    def test_wildcard_全部(self):
        # 任意状态都应含 T03（所在状态=全部）
        for st in ("default", "mobile-only"):
            tps = dict(G.extract_touchpoints_for_state(SPEC, "M01", "P01", st))
            assert "M01-P01-T03" in tps


class TestFieldExtraction:
    def test_per_page_data_field(self):
        fields = dict(G.extract_fields_for_page(SPEC, "M01", "P01"))
        # package_id + created_at（secret_id 隐式豁免；other_field 属 P02）
        assert set(fields) == {"package_id", "created_at"}

    def test_implicit_field_excluded(self):
        fields = dict(G.extract_fields_for_page(SPEC, "M01", "P01"))
        assert "secret_id" not in fields, "隐式承载字段应豁免"

    def test_other_page_excluded(self):
        fields = dict(G.extract_fields_for_page(SPEC, "M01", "P01"))
        assert "other_field" not in fields, "P02 字段不应混入 P01"


class TestPlatformExtraction:
    def test_agnostic_yields_nothing(self):
        plats = G.extract_platforms_for_frame(SPEC, "M01", "H-M01-P01-default", "default")
        assert plats == [], "agnostic 不生平台契约项"

    def test_specific_platforms_extracted(self):
        plats = G.extract_platforms_for_frame(SPEC, "M01", "H-M01-P01-mobile-only", "mobile-only")
        assert set(plats) == {"手机", "桌面Web"}, f"具体平台应入选，实际 {plats}"


class TestHumanReviewBoundary:
    def test_nb_refs_collected_not_in_machine(self):
        # default 帧的 NB 引用（.2 页面表现 NB-003 + .3 T01 系统响应 NB-016）
        refs = G.extract_human_review_refs(SPEC, "M01", "P01", "default")
        assert "NB-003" in refs and "NB-016" in refs
        # 触点机械区不含 NB（NB 只在人工对照区）
        tps = dict(G.extract_touchpoints_for_state(SPEC, "M01", "P01", "default"))
        assert all("NB-" not in k for k in tps)


class TestContractBuildAndDeterminism:
    def _mod(self):
        return {"id": "M01", "name": "模块", "pages": [_page()]}

    def test_embedded_frame_included(self):
        c = G.build_module_contract(self._mod(), SPEC)
        all_frames = [fr["prd_id"] for pg in c["pages"] for fr in pg["frames"]]
        assert "H-M01-P01-card-default" in all_frames, "内嵌帧应纳入契约（iter_page_prd_ids）"

    def test_deterministic(self):
        m = self._mod()
        a = G.render_contract_md(G.build_module_contract(m, SPEC))
        b = G.render_contract_md(G.build_module_contract(m, SPEC))
        assert a == b, "同输入须同输出（确定性，对齐 #73）"

    def test_md_has_two_sections_with_markers(self):
        md = G.render_contract_md(G.build_module_contract(self._mod(), SPEC))
        assert "渲染契约 checklist（机械可核）" in md
        assert "人工对照（Supervisor 抽样" in md
        assert 'data-field="package_id"' in md
        assert 'data-tp="M01-P01-T01"' in md

    def test_landing_append_then_idempotent_replace(self, tmp_path):
        tc = tmp_path / "task_M01.md"
        tc.write_text("# 任务卡 M01\n\n## 候选组件清单\n（略）\n", encoding="utf-8")
        md1 = G.render_contract_md(G.build_module_contract(self._mod(), SPEC))
        assert G.update_task_card_render_contract(tc, md1) is True
        t = tc.read_text(encoding="utf-8")
        assert G.RC_START in t and G.RC_END in t
        assert "## 候选组件清单" in t, "落地不应破坏既有段"
        assert 'data-tp="M01-P01-T01"' in t
        # 幂等替换：再落一次，块仍只 1 个
        G.update_task_card_render_contract(tc, md1)
        t2 = tc.read_text(encoding="utf-8")
        assert t2.count(G.RC_START) == 1 and t2.count(G.RC_END) == 1

    def test_landing_missing_task_card(self, tmp_path):
        assert G.update_task_card_render_contract(tmp_path / "nope.md", "x") is False

    def test_provenance_flags_zero(self):
        # 构造一个无触点的帧 → provenance 应含 ⚠
        mod = {"id": "M09", "name": "x", "pages": [{
            "id": "P01", "name": "p", "states": [
                {"name": "blank", "prd_id": "H-M09-P01-blank", "roles": []}]}]}
        c = G.build_module_contract(mod, SPEC)  # SPEC 无 M09 段 → 全 0
        assert any("⚠" in line for line in c["provenance"])


# ── layer 4：check_render_contract（验标记 presence，零 FP-by-design）────────────
import precheck_stage4 as P  # noqa: E402
from precheck_stage4 import Report  # noqa: E402


def _frame(prd_id: str, body: str) -> str:
    return f"<!-- [FRAME-START: {prd_id} | from=x | sha256:abc] -->\n{body}\n<!-- [FRAME-END: {prd_id}] -->"


class TestCheckRenderContract:
    def _mod(self):
        return {"id": "M01", "name": "模块", "pages": [{
            "id": "P01", "name": "首页", "states": [
                {"name": "default", "prd_id": "H-M01-P01-default", "roles": []}]}]}

    def test_all_markers_present_pass(self):
        data = {"modules": [self._mod()]}
        # default 帧期望触点 T01/T02/T03 + 页字段 package_id/created_at
        prd = _frame("H-M01-P01-default",
                     '<button data-tp="M01-P01-T01"></button>'
                     '<button data-tp="M01-P01-T02"></button>'
                     '<a data-tp="M01-P01-T03"></a>'
                     '<span data-field="package_id"></span>'
                     '<span data-field="created_at"></span>')
        r = Report()
        P.check_render_contract(data, prd, SPEC, r)
        assert r.warnings == [], f"全标记应 PASS：{r.warnings}"
        assert r.passed >= 1

    def test_missing_touchpoint_marker_warns(self):
        data = {"modules": [self._mod()]}
        prd = _frame("H-M01-P01-default",
                     '<button data-tp="M01-P01-T01"></button>'  # 缺 T02/T03
                     '<span data-field="package_id"></span>'
                     '<span data-field="created_at"></span>')
        r = Report()
        P.check_render_contract(data, prd, SPEC, r)
        assert len(r.warnings) == 1
        assert "M01-P01-T02" in r.warnings[0] and "M01-P01-T03" in r.warnings[0]

    def test_missing_field_marker_warns(self):
        data = {"modules": [self._mod()]}
        prd = _frame("H-M01-P01-default",
                     '<button data-tp="M01-P01-T01"></button>'
                     '<button data-tp="M01-P01-T02"></button>'
                     '<a data-tp="M01-P01-T03"></a>')  # 缺 data-field
        r = Report()
        P.check_render_contract(data, prd, SPEC, r)
        assert len(r.warnings) == 1
        assert "package_id" in r.warnings[0] and "created_at" in r.warnings[0]

    def test_no_frames_skips(self):
        r = Report()
        P.check_render_contract({"modules": [self._mod()]}, "<html></html>", SPEC, r)
        assert r.warnings == [] and r.passed >= 1

    def test_no_spec_sections_skips(self):
        data = {"modules": [self._mod()]}
        prd = _frame("H-M01-P01-default", "<div></div>")
        r = Report()
        P.check_render_contract(data, prd, "（空 spec 无 .3/.4）", r)
        assert r.warnings == [] and r.passed >= 1, "无可转录契约项应 skip"
