"""test_precheck_stage4.py — precheck_stage4.py pytest 用例集。

历史来源：
- IC-EXT 5 测试用例烟测（NB-IC-EXT-03 挂账等待 pytest 引入后转 fixture）
- HC-4 状态覆盖增强烟测（NB-HC-05 挂账）

覆盖函数：
- check_section_nesting（issue #3/#4 嵌套约束）
- check_state_coverage（S4-05 状态枚举三类覆盖）

[Must] 测试隔离纪律：每个用例独立产出 Report 对象 + 独立 HTML/scaffold 输入；
不共享全局状态、不读真实 outputs/ 目录。
"""

from __future__ import annotations

import copy

import pytest

# precheck_stage4 由 conftest.py sys.path 注入；直接 import 即可
from precheck_stage4 import (  # type: ignore
    REQUIRED_PROJ_FIELDS,
    Report,
    check_frame_platform_tag,
    check_page_platform_coverage,
    check_scaffold_roles_format,
    check_section_nesting,
    check_spec_state_table_count,
    check_state_coverage,
    check_state_naming_convention,
    parse_proj_components,
)
import precheck_stage4 as _stage4_mod  # type: ignore


# ── check_section_nesting 用例（issue #3/#4 嵌套约束）─────────────────────────


class TestSectionNesting:
    """覆盖 precheck_stage4.check_section_nesting — IC-EXT 5 测试用例 pytest 沉淀。"""

    def test_check_section_nesting_pass(self, sample_prd_html_minimal: str) -> None:
        """合法结构（frame-card 仅含 frame-wrapper + interaction-card 同级）→ 应 pass。"""
        r = Report()
        check_section_nesting(sample_prd_html_minimal, r)
        assert r.errors == [], f"合法结构应 PASS,但有错误：{r.errors}"
        assert r.passed >= 1, "至少应有 1 项 OK 通过"

    def test_check_section_nesting_fail_section_header_in_frame_card(
        self, make_prd_with_violation
    ) -> None:
        """frame-card 内含 section-header → 应 fail R1（issue #3 违反）。"""
        r = Report()
        prd_html = make_prd_with_violation("section_header_in_frame_card")
        check_section_nesting(prd_html, r)
        assert len(r.errors) >= 1, "frame-card 内嵌 section-header 必须报 fail"
        assert any("R1" in e for e in r.errors), \
            f"错误信息应含 R1 标记,实际：{r.errors}"
        assert any("section-header" in e for e in r.errors), \
            f"错误信息应明示 section-header,实际：{r.errors}"

    def test_check_section_nesting_fail_interaction_card_in_frame_card(
        self, make_prd_with_violation
    ) -> None:
        """frame-card 内嵌 interaction-card → 应 fail R2（issue #4 违反）。"""
        r = Report()
        prd_html = make_prd_with_violation("interaction_card_in_frame_card")
        check_section_nesting(prd_html, r)
        assert len(r.errors) >= 1, "frame-card 内嵌 interaction-card 必须报 fail"
        assert any("R2" in e for e in r.errors), \
            f"错误信息应含 R2 标记,实际：{r.errors}"
        assert any("interaction-card" in e for e in r.errors), \
            f"错误信息应明示 interaction-card,实际：{r.errors}"

    def test_check_section_nesting_fail_interaction_card_deep_nesting(
        self, make_prd_with_violation
    ) -> None:
        """interaction-card 深层嵌套于 frame-card 子元素 → 应 fail R2。

        逆否覆盖：interaction-card 不应是 frame-card 的任何级别后代,
        必须是 proto-section 直接子元素。
        """
        r = Report()
        prd_html = make_prd_with_violation("interaction_card_deep_nested")
        check_section_nesting(prd_html, r)
        assert len(r.errors) >= 1, "深层嵌套 interaction-card 必须报 fail"
        assert any("R2" in e for e in r.errors), \
            f"错误信息应含 R2 标记,实际：{r.errors}"

    def test_check_section_nesting_pass_no_proto_section(
        self, make_prd_with_violation
    ) -> None:
        """非 proto-section 内的嵌套（如 cover-page）→ 静默 PASS。

        check_section_nesting 仅校验 proto-section 内嵌套,
        其他 section 不受 issue #3/#4 约束。
        """
        r = Report()
        prd_html = make_prd_with_violation("no_proto_section")
        check_section_nesting(prd_html, r)
        assert r.errors == [], \
            f"非 proto-section 嵌套不应触发,实际错误：{r.errors}"


# ── check_state_coverage 用例（S4-05 状态清单覆盖）──────────────────────────


class TestStateCoverage:
    """覆盖 precheck_stage4.check_state_coverage — S4-05 三类状态覆盖。"""

    def test_check_state_coverage_pass(self, fake_scaffold_v2: dict) -> None:
        """状态枚举包含 default + loading + error → 应 pass。"""
        r = Report()
        check_state_coverage(fake_scaffold_v2, r)
        assert r.errors == [], \
            f"完整三类状态应 PASS,实际错误：{r.errors}"
        assert r.passed >= 1, "至少应有 1 项 OK 通过"

    def test_check_state_coverage_fail_lazy_default_only(
        self, fake_scaffold_v2: dict
    ) -> None:
        """仅含 default 态（缺时序态 + 约束态）→ 应 fail。"""
        s = copy.deepcopy(fake_scaffold_v2)
        # 删 loading + error,只剩 default
        s["modules"][0]["pages"][0]["states"] = [
            {
                "name": "default",
                "prd_id": "H-M01-P01-default",
                "roles": ["普通用户"],
            }
        ]
        r = Report()
        check_state_coverage(s, r)
        assert len(r.errors) >= 1, "仅 default 态必须报 fail"
        assert any("S4-05" in e for e in r.errors), \
            f"错误应含 S4-05 标记,实际：{r.errors}"

    def test_check_state_coverage_fail_missing_constraint_state(
        self, fake_scaffold_v2: dict
    ) -> None:
        """缺约束态（无 error / disabled）→ 应 fail。"""
        s = copy.deepcopy(fake_scaffold_v2)
        # 留 default + loading,删 error
        s["modules"][0]["pages"][0]["states"] = [
            {"name": "default", "prd_id": "H-M01-P01-default", "roles": ["x"]},
            {"name": "loading", "prd_id": "H-M01-P01-loading", "roles": ["x"]},
        ]
        r = Report()
        check_state_coverage(s, r)
        assert len(r.errors) >= 1, "缺约束态必须报 fail"
        assert any(
            "error" in e or "disabled" in e or "约束" in e for e in r.errors
        ), f"错误应明示缺约束态类别,实际：{r.errors}"

    def test_check_state_coverage_pass_chinese_state_names(
        self, fake_scaffold_v2: dict
    ) -> None:
        """中文状态名（默认 + 加载 + 错误）→ 应 pass（关键字含中文同义词）。"""
        s = copy.deepcopy(fake_scaffold_v2)
        s["modules"][0]["pages"][0]["states"] = [
            {"name": "默认", "prd_id": "H-M01-P01-默认", "roles": ["x"]},
            {"name": "加载中", "prd_id": "H-M01-P01-加载中", "roles": ["x"]},
            {"name": "错误", "prd_id": "H-M01-P01-错误", "roles": ["x"]},
        ]
        r = Report()
        check_state_coverage(s, r)
        assert r.errors == [], \
            f"中文状态名三类齐全应 PASS,实际错误：{r.errors}"

    def test_check_state_coverage_fail_no_default(
        self, fake_scaffold_v2: dict
    ) -> None:
        """无 default 态（仅 loading + error）→ 应 fail。"""
        s = copy.deepcopy(fake_scaffold_v2)
        s["modules"][0]["pages"][0]["states"] = [
            {"name": "loading", "prd_id": "H-M01-P01-loading", "roles": ["x"]},
            {"name": "error", "prd_id": "H-M01-P01-error", "roles": ["x"]},
        ]
        r = Report()
        check_state_coverage(s, r)
        assert len(r.errors) >= 1, "缺 default 态必须报 fail"
        assert any("default" in e or "默认" in e for e in r.errors), \
            f"错误应明示缺 default 态类别,实际：{r.errors}"


# ── 边界 / 鲁棒性用例 ─────────────────────────────────────────────────────────


class TestRobustness:
    """边界与鲁棒性场景核查（确保 precheck 行为稳定）。"""

    def test_check_section_nesting_handles_empty_html(self) -> None:
        """空 HTML 输入 → 不应崩溃,无错误（无 proto-section 即跳过）。"""
        r = Report()
        check_section_nesting("", r)
        assert r.errors == [], "空 HTML 不应触发任何错误"

    def test_check_state_coverage_handles_missing_modules_field(self) -> None:
        """scaffold 无 modules 字段 → 不应崩溃（已在 check_scaffold 报错）。"""
        r = Report()
        # 不传 modules,直接传空字典
        check_state_coverage({}, r)
        # 仅验证不抛异常即可（错误由上游 check_scaffold 统一报告）

    def test_check_state_coverage_with_multiple_pages(
        self, fake_scaffold_v2: dict
    ) -> None:
        """多页面场景：1 页面合规 + 1 页面缺约束态 → 仅缺约束态页面报 fail。"""
        s = copy.deepcopy(fake_scaffold_v2)
        # 添加第二个页面（仅 default + loading,缺约束态）
        s["modules"][0]["pages"].append({
            "id": "P02",
            "name": "页面2",
            "spec_id": "spec-M01-P02",
            "route": "/p2",
            "states": [
                {"name": "default", "prd_id": "H-M01-P02-default", "roles": ["x"]},
                {"name": "loading", "prd_id": "H-M01-P02-loading", "roles": ["x"]},
            ],
        })
        r = Report()
        check_state_coverage(s, r)
        # 至少 1 个错误（M01-P02），但 M01-P01 仍应贡献 1 个 OK
        assert len(r.errors) >= 1, "至少 P02 缺约束态应报 fail"
        assert any("P02" in e for e in r.errors), \
            f"错误应定位到 P02,实际：{r.errors}"


# ── REQUIRED_PROJ_FIELDS 业务语义三段（issue 2026-05-07_1117 PC 系列）──────────


class TestProjComponentMetaThreeSections:
    """覆盖 issue 2026-05-07_1117 PC 系列:proj 组件三段（boundary/usage/interaction）必填。

    验证 REQUIRED_PROJ_FIELDS 列表含三段,以及 parse_proj_components 解析后
    既有 check_proj_components L1001 字段存在性循环能正确识别缺失。
    """

    def test_required_proj_fields_includes_meta_three(self) -> None:
        """REQUIRED_PROJ_FIELDS 须含 boundary / usage / interaction 三段。"""
        assert "boundary" in REQUIRED_PROJ_FIELDS, \
            f"REQUIRED_PROJ_FIELDS 缺 boundary,实际:{REQUIRED_PROJ_FIELDS}"
        assert "usage" in REQUIRED_PROJ_FIELDS, \
            f"REQUIRED_PROJ_FIELDS 缺 usage,实际:{REQUIRED_PROJ_FIELDS}"
        assert "interaction" in REQUIRED_PROJ_FIELDS, \
            f"REQUIRED_PROJ_FIELDS 缺 interaction,实际:{REQUIRED_PROJ_FIELDS}"

    def test_parse_proj_components_with_full_meta(self) -> None:
        """合法 proj 组件含三段时,parse_proj_components 提取的 text 应保留三段字段名(供 check_proj_components L1001 字段存在性检查)。"""
        md = """## 二.2 详情段

```yaml
- id: proj.L2.product-card
  inherits: pub.L2.card
  modules: [M01]
  purpose: 商品卡片
  boundary:
    applicable_when: ["列表页"]
    not_applicable_when: ["纯文本"]
    differs_from: { pub.L2.card: "5 vs 4 slot" }
  usage:
    business_scenarios: ["电商列表", "搜索结果"]
    modules: { M01: "主列表" }
    pain_point: "需价格槽"
  interaction:
    user_flow: "滑动 → 点击进详情"
    collaborates_with: [fb-btn-primary]
  slots:
    - title: { type: text }
  states:
    required: [default]
  state_transitions:
    - default ↔ hover
  field_schema:
    - title: { type: string }
```
"""
        components = parse_proj_components(md)
        assert len(components) == 1, f"应解析 1 个 proj 组件,实际 {len(components)} 个"
        text = components[0]["text"]
        # 确认三段字段名都在 text 中(check_proj_components L1001 用 regex 检查字段存在性)
        for field in ("boundary", "usage", "interaction"):
            assert field in text, f"解析后 text 缺 {field},无法触发字段存在性检查"

    def test_parse_proj_components_missing_boundary(self) -> None:
        """缺 boundary 段的 proj 组件,parse 后 text 不含 boundary 字段名 → 既有 check 循环会 FAIL。"""
        md = """## 二.2 详情段

```yaml
- id: proj.L2.no-boundary
  inherits: pub.L2.card
  modules: [M01]
  usage:
    business_scenarios: ["x"]
    modules: { M01: "主" }
    pain_point: "y"
  interaction:
    user_flow: "z"
    collaborates_with: []
  slots:
    - title: { type: text }
  states:
    required: [default]
  state_transitions:
    - default ↔ hover
  field_schema:
    - title: { type: string }
```
"""
        components = parse_proj_components(md)
        assert len(components) == 1, "应解析 1 个组件"
        text = components[0]["text"]
        # 缺 boundary 段时,text 不含 "boundary:" 字段名
        # 既有 check_proj_components L1001 的 regex 检查会触发 FAIL
        import re as _re
        boundary_match = _re.search(r"^\s*boundary\s*:", text, _re.MULTILINE)
        assert boundary_match is None, \
            f"应缺 boundary,实际:text 含 boundary 字段名"


# ── check_frame_platform_tag 用例（.frame-cell 嵌套 DOM）─────────────────────


class TestFramePlatformTag:
    """覆盖 precheck_stage4.check_frame_platform_tag — .frame-cell 嵌套 DOM。

    新 DOM:
      frame-card
      └─ frame-wrapper                  ← 唯一 flex 容器（横向铺多端 cell）
         ├─ frame-cell                  ← 每端一个 cell（纵向 flex）
         │  ├─ frame-platform-item      ← cell 顶
         │  │  ├─ .frame-platform-tag   （span, 必填）
         │  │  └─ .frame-platform-note  （p, 可选）
         │  └─ phone-frame / desktop-frame / ...   ← 视觉帧（cell 底）

    规则：1 个 frame-card 内并列 ≥ 2 端口帧实例（含 ≥ 2 种类型）时:
      ①每个端口帧必须包在 .frame-cell 内（不能直接挂 .frame-wrapper 下）
      ②每个 .frame-cell 必须含 .frame-platform-item
      ③每个 .frame-platform-item 必须含 .frame-platform-tag
    单端 / 单帧 frame-card 跳过（cell 可省略）。
    """

    @staticmethod
    def _wrap(body: str) -> str:
        """最小 PRD 包装,提供 proto-section 上下文。"""
        return f"""<!DOCTYPE html><html><body>
<section id="H-M01-P01-default" class="proto-section">
{body}
</section>
</body></html>"""

    def test_single_platform_pass(self) -> None:
        """frame-card 内仅 1 个端口帧 → 规则不适用，应 PASS。"""
        prd_html = self._wrap("""
<div class="frame-card">
  <div class="frame-wrapper">
    <div class="phone-frame"></div>
  </div>
</div>
""")
        r = Report()
        check_frame_platform_tag(prd_html, r)
        assert r.errors == [], f"单端应 PASS,实际错误：{r.errors}"
        assert r.passed >= 1

    def test_multi_platform_with_cell_pass(self) -> None:
        """新 DOM 合规：每端帧包在 .frame-cell 内 + 每 cell 含 platform-item + tag。"""
        prd_html = self._wrap("""
<div class="frame-card">
  <div class="frame-wrapper">
    <div class="frame-cell">
      <div class="frame-platform-item">
        <span class="frame-platform-tag">手机</span>
      </div>
      <div class="phone-frame"></div>
    </div>
    <div class="frame-cell">
      <div class="frame-platform-item">
        <span class="frame-platform-tag">桌面</span>
        <p class="frame-platform-note">布局同手机帧，空态居中显示</p>
      </div>
      <div class="desktop-frame"></div>
    </div>
  </div>
</div>
""")
        r = Report()
        check_frame_platform_tag(prd_html, r)
        assert r.errors == [], f"新 DOM 合规应 PASS,实际错误：{r.errors}"
        assert r.passed >= 1

    def test_multi_platform_missing_cell_fail(self) -> None:
        """frame-card 含多端帧但端口帧直接挂 wrapper 下（无 .frame-cell 包裹）→ FAIL。"""
        prd_html = self._wrap("""
<div class="frame-card">
  <div class="frame-wrapper">
    <div class="phone-frame"></div>
    <div class="desktop-frame"></div>
  </div>
</div>
""")
        r = Report()
        check_frame_platform_tag(prd_html, r)
        assert len(r.errors) >= 1, "端口帧未在 .frame-cell 内应 FAIL"
        assert any("frame-cell" in e for e in r.errors), \
            f"错误应明示 .frame-cell,实际：{r.errors}"

    def test_multi_platform_cell_missing_item_fail(self) -> None:
        """.frame-cell 内缺 .frame-platform-item → FAIL。"""
        prd_html = self._wrap("""
<div class="frame-card">
  <div class="frame-wrapper">
    <div class="frame-cell">
      <div class="frame-platform-item">
        <span class="frame-platform-tag">手机</span>
      </div>
      <div class="phone-frame"></div>
    </div>
    <div class="frame-cell">
      <!-- 缺 .frame-platform-item -->
      <div class="desktop-frame"></div>
    </div>
  </div>
</div>
""")
        r = Report()
        check_frame_platform_tag(prd_html, r)
        assert len(r.errors) >= 1, "cell 缺 platform-item 应 FAIL"
        assert any("frame-platform-item" in e for e in r.errors), \
            f"错误应明示 frame-platform-item 缺失,实际：{r.errors}"

    def test_multi_platform_cell_missing_tag_fail(self) -> None:
        """.frame-platform-item 存在但缺 .frame-platform-tag span → FAIL。"""
        prd_html = self._wrap("""
<div class="frame-card">
  <div class="frame-wrapper">
    <div class="frame-cell">
      <div class="frame-platform-item">
        <span class="frame-platform-tag">手机</span>
      </div>
      <div class="phone-frame"></div>
    </div>
    <div class="frame-cell">
      <div class="frame-platform-item">
        <!-- 缺 tag span -->
        <p class="frame-platform-note">布局同手机帧</p>
      </div>
      <div class="desktop-frame"></div>
    </div>
  </div>
</div>
""")
        r = Report()
        check_frame_platform_tag(prd_html, r)
        assert len(r.errors) >= 1, "cell 内 item 缺 tag 应 FAIL"
        assert any("frame-platform-tag" in e for e in r.errors), \
            f"错误应明示 frame-platform-tag 缺失,实际：{r.errors}"

    def test_no_frame_card_pass(self) -> None:
        """PRD 无 frame-card → 规则不适用，应 PASS。"""
        prd_html = self._wrap("<div class=\"some-other-card\">不是 frame-card</div>")
        r = Report()
        check_frame_platform_tag(prd_html, r)
        assert r.errors == [], f"无 frame-card 应 PASS,实际错误：{r.errors}"

    def test_same_type_multi_instance_skip(self) -> None:
        """frame-card 内 2 个 phone-frame（同类型 ≥ 2 实例但仅 1 种类型）→ 规则不适用，应 PASS。"""
        prd_html = self._wrap("""
<div class="frame-card">
  <div class="frame-wrapper">
    <div class="phone-frame"></div>
    <div class="phone-frame"></div>
  </div>
</div>
""")
        r = Report()
        check_frame_platform_tag(prd_html, r)
        assert r.errors == [], f"同类型多实例应 PASS,实际错误：{r.errors}"


# ── check_page_platform_coverage 用例（SNB-005 修复 WARN-phase 页面级精度）──

class TestPagePlatformCoverage:
    """覆盖 precheck_stage4.check_page_platform_coverage — 单帧 + 多 platform-item 漂移。

    与 TestFramePlatformTag 互补：前者校验 ≥ 2 帧的对齐，本类抓单帧 + 多 platform-item
    的不一致（设计盲区 SNB-005，issue#27/#28 根因）。
    """

    @staticmethod
    def _wrap(body: str) -> str:
        return f"<html><body>{body}</body></html>"

    def test_single_frame_with_multi_cells_warn(self) -> None:
        """单帧 + 声明 ≥ 2 个 .frame-cell → WARN（漂移命中）。"""
        prd_html = self._wrap("""
<section id="H-M01-P03-audit-pass">
  <div class="frame-card">
    <div class="frame-wrapper">
      <div class="frame-cell">
        <div class="frame-platform-item"><span class="frame-platform-tag">桌面</span></div>
        <div class="desktop-frame"></div>
      </div>
      <div class="frame-cell">
        <div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>
      </div>
      <div class="frame-cell">
        <div class="frame-platform-item"><span class="frame-platform-tag">平板</span></div>
      </div>
    </div>
  </div>
</section>
""")
        r = Report()
        check_page_platform_coverage(prd_html, r)
        assert any("端口覆盖漂移" in w for w in r.warnings), \
            f"单帧+多 cell 应 WARN,实际 warn：{r.warnings} / err：{r.errors}"
        assert r.errors == [], f"WARN-phase 不应 FAIL,实际错误：{r.errors}"

    def test_single_frame_with_exempt_comment_pass(self) -> None:
        """单帧 + 多 .frame-cell 但有 skeleton-single-frame 豁免注释 → 不 WARN。"""
        prd_html = self._wrap("""
<section id="H-M01-P03-audit-pass">
  <!-- skeleton-single-frame: Pad 同手机帧、引用说明 -->
  <div class="frame-card">
    <div class="frame-wrapper">
      <div class="frame-cell">
        <div class="frame-platform-item"><span class="frame-platform-tag">桌面</span></div>
        <div class="desktop-frame"></div>
      </div>
      <div class="frame-cell">
        <div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>
      </div>
      <div class="frame-cell">
        <div class="frame-platform-item"><span class="frame-platform-tag">平板</span></div>
      </div>
    </div>
  </div>
</section>
""")
        r = Report()
        check_page_platform_coverage(prd_html, r)
        drift_warns = [w for w in r.warnings if "端口覆盖漂移" in w]
        assert not drift_warns, \
            f"有豁免注释应不 WARN,实际 warn：{drift_warns}"

    def test_single_frame_no_cell_skip(self) -> None:
        """单帧 + 无 .frame-cell（wrapper 直接含帧）→ 不属于漂移（无声明）→ 不 WARN。"""
        prd_html = self._wrap("""
<section id="H-M02-P01-default">
  <div class="frame-card">
    <div class="frame-wrapper">
      <div class="desktop-frame"></div>
    </div>
  </div>
</section>
""")
        r = Report()
        check_page_platform_coverage(prd_html, r)
        drift_warns = [w for w in r.warnings if "端口覆盖漂移" in w]
        assert not drift_warns, \
            f"无 .frame-cell 应不 WARN,实际 warn：{drift_warns}"

    def test_multi_frame_not_in_scope(self) -> None:
        """≥ 2 帧（属于 check_frame_platform_tag 管辖）→ 本 check 不应 WARN。"""
        prd_html = self._wrap("""
<section id="H-M01-P01-default">
  <div class="frame-card">
    <div class="frame-wrapper">
      <div class="frame-cell">
        <div class="frame-platform-item"><span class="frame-platform-tag">桌面</span></div>
        <div class="desktop-frame"></div>
      </div>
      <div class="frame-cell">
        <div class="frame-platform-item"><span class="frame-platform-tag">手机</span></div>
        <div class="phone-frame"></div>
      </div>
    </div>
  </div>
</section>
""")
        r = Report()
        check_page_platform_coverage(prd_html, r)
        drift_warns = [w for w in r.warnings if "端口覆盖漂移" in w]
        assert not drift_warns, \
            f"≥2 帧不归本 check 管,实际 warn：{drift_warns}"

    def test_single_frame_single_cell_pass(self) -> None:
        """单帧 + 仅 1 个 .frame-cell → 声明与实绘一致 → 不 WARN。"""
        prd_html = self._wrap("""
<section id="H-M01-P02-default">
  <div class="frame-card">
    <div class="frame-wrapper">
      <div class="frame-cell">
        <div class="frame-platform-item"><span class="frame-platform-tag">桌面</span></div>
        <div class="desktop-frame"></div>
      </div>
    </div>
  </div>
</section>
""")
        r = Report()
        check_page_platform_coverage(prd_html, r)
        drift_warns = [w for w in r.warnings if "端口覆盖漂移" in w]
        assert not drift_warns, \
            f"单帧+单 item 应不 WARN,实际 warn：{drift_warns}"


# ── check_scaffold_roles_format 用例（NB-WE-04 + SSOT 双锚 #24）─────────────


class TestScaffoldRolesFormat:
    """覆盖 check_scaffold_roles_format 三个核心场景：
    1) roles 全部用 ID 且 ⊂ §3 ID 集合 → PASS
    2) roles 全部用名 且 ⊂ §3 名集合 → PASS
    3) roles 含未在 §3 登记的字面值 → FAIL
    4) roles 混用 ID 和名 → FAIL
    5) §3 真源未加载（产品定义文件不存在）→ WARN（降级）
    """

    @staticmethod
    def _make_product_def_md(role_pairs: list[tuple[str, str]]) -> str:
        """生成最小 §3 用户画像 md 文本（每对 (id, name) 一个角色块）。"""
        blocks = []
        for idx, (rid, rname) in enumerate(role_pairs, 1):
            cn_num = ["一", "二", "三", "四"][idx - 1] if idx <= 4 else str(idx)
            blocks.append(
                f"### 角色{cn_num}：{rname}\n\n"
                f"- **角色 ID**：[`{rid}`]\n"
                f"- **角色名**：[{rname}]\n"
            )
        return "## 3. 用户画像\n\n" + "\n".join(blocks) + "\n## 4. 权限矩阵\n"

    def _setup_pdef(self, monkeypatch, tmp_path, product: str, role_pairs: list[tuple[str, str]]) -> None:
        """临时把 OUTPUT_DIR 改成 tmp_path 并写入产品定义 md。"""
        pdef = tmp_path / f"产品定义_{product}_latest.md"
        pdef.write_text(self._make_product_def_md(role_pairs), encoding="utf-8")
        monkeypatch.setattr(_stage4_mod, "OUTPUT_DIR", tmp_path)

    def _scaffold_with_roles(self, base: dict, roles: list[str]) -> dict:
        s = copy.deepcopy(base)
        # 替换所有 states.roles 为给定值
        for mod in s["modules"]:
            for page in mod.get("pages", []):
                for state in page.get("states", []):
                    state["roles"] = list(roles)
        return s

    def test_all_ids_subset_of_section3_passes(self, fake_scaffold_v2, monkeypatch, tmp_path) -> None:
        """全部 roles 用 ID 且 ⊂ §3 ID 集合 → PASS。"""
        self._setup_pdef(
            monkeypatch, tmp_path, "测试产品",
            [("role-1", "销售"), ("role-2", "经理")],
        )
        scaffold = self._scaffold_with_roles(fake_scaffold_v2, ["role-1", "role-2"])
        r = Report()
        check_scaffold_roles_format(scaffold, r)
        assert r.errors == [], f"全 ID 合规应 PASS,实际错误：{r.errors}"

    def test_all_names_subset_of_section3_passes(self, fake_scaffold_v2, monkeypatch, tmp_path) -> None:
        """全部 roles 用名 且 ⊂ §3 名集合 → PASS。"""
        self._setup_pdef(
            monkeypatch, tmp_path, "测试产品",
            [("role-1", "销售"), ("role-2", "经理")],
        )
        scaffold = self._scaffold_with_roles(fake_scaffold_v2, ["销售", "经理"])
        r = Report()
        check_scaffold_roles_format(scaffold, r)
        assert r.errors == [], f"全名合规应 PASS,实际错误：{r.errors}"

    def test_unregistered_value_fails(self, fake_scaffold_v2, monkeypatch, tmp_path) -> None:
        """roles 含未在 §3 登记的字面值（如 "客户"）→ FAIL。"""
        self._setup_pdef(
            monkeypatch, tmp_path, "测试产品",
            [("role-1", "销售"), ("role-2", "经理")],
        )
        scaffold = self._scaffold_with_roles(fake_scaffold_v2, ["销售", "客户"])
        r = Report()
        check_scaffold_roles_format(scaffold, r)
        assert any("未在 §3 登记" in e or "客户" in e for e in r.errors), (
            f"未登记字面值应 FAIL,实际错误：{r.errors}"
        )

    def test_mixed_id_and_name_fails(self, fake_scaffold_v2, monkeypatch, tmp_path) -> None:
        """roles 混用 ID（role-1）和名（经理）→ FAIL。"""
        self._setup_pdef(
            monkeypatch, tmp_path, "测试产品",
            [("role-1", "销售"), ("role-2", "经理")],
        )
        scaffold = self._scaffold_with_roles(fake_scaffold_v2, ["role-1", "经理"])
        r = Report()
        check_scaffold_roles_format(scaffold, r)
        assert any("混用" in e for e in r.errors), (
            f"ID 名混用应 FAIL,实际错误：{r.errors}"
        )

    def test_pdef_missing_warns_not_fails(self, fake_scaffold_v2, monkeypatch, tmp_path) -> None:
        """§3 真源未加载（产品定义文件不存在）→ WARN 降级,不阻断。"""
        # 不调用 _setup_pdef,但仍把 OUTPUT_DIR 指向空 tmp_path
        monkeypatch.setattr(_stage4_mod, "OUTPUT_DIR", tmp_path)
        scaffold = self._scaffold_with_roles(fake_scaffold_v2, ["销售"])
        r = Report()
        check_scaffold_roles_format(scaffold, r)
        # 应仅 warn,不 fail
        assert len(r.warnings) >= 1, "§3 未加载应至少 1 个 WARN"
        # 允许有少量 fail（如格式非法）但不应因"未在 §3 登记"fail
        for e in r.errors:
            assert "未在 §3 登记" not in e, f"§3 未加载时不应报登记 FAIL: {e}"


# ── check_z_index_compliance 用例（NB-WE-06 视觉一致性机械化）──────────────


class TestZIndexCompliance:
    """覆盖 check_z_index_compliance — SSOT §零.1 全局 z-index 数值合规。"""

    def test_legal_set_passes(self) -> None:
        """全部 z-index 数值在 {200, 150, 100, 60, 50, 41, 40, 10, 1} 集合 → PASS。

        issue 2026-05-11_1925 派生漂移修复后,合法集合扩到 9 值（追赶 §零.2 三大类规范）。
        """
        from precheck_stage4 import check_z_index_compliance  # type: ignore
        prd = """<!DOCTYPE html>
<html><head><style>
.section-header { z-index: 200; }
.fb-toast { z-index: 150; }
.fb-dropdown { z-index: 100; }
.fb-tooltip { z-index: 60; }
.fb-modal-overlay { z-index: 50; }
.fb-drawer { z-index: 41; }
.fb-drawer-overlay { z-index: 40; }
.tp-marker { z-index: 10; }
</style></head><body></body></html>"""
        r = Report()
        check_z_index_compliance(prd, r)
        assert r.errors == [], f"全合法应 PASS,实际错误：{r.errors}"
        assert r.passed >= 1

    def test_toast_z_150_passes(self) -> None:
        """fb-toast z-index: 150 — §零.2 反馈型预设,不应被 NB-WE-06 误判。

        issue 2026-05-11_1925 下游反馈核心场景之一（精确回归）。
        """
        from precheck_stage4 import check_z_index_compliance  # type: ignore
        prd = '<style>.fb-toast { z-index: 150; }</style>'
        r = Report()
        check_z_index_compliance(prd, r)
        assert r.errors == [], f"z-index: 150 应 PASS（§零.2 toast 预设）,实际错误：{r.errors}"

    def test_drawer_content_z_41_passes(self) -> None:
        """fb-drawer 内容 z-index: 41 — §零.2 容器型预设（高于 drawer-overlay 40 一档）。

        issue 2026-05-11_1925 下游反馈核心场景之二（精确回归）。
        """
        from precheck_stage4 import check_z_index_compliance  # type: ignore
        prd = '<style>.fb-drawer { z-index: 41; }</style>'
        r = Report()
        check_z_index_compliance(prd, r)
        assert r.errors == [], f"z-index: 41 应 PASS（§零.2 drawer 内容预设）,实际错误：{r.errors}"

    def test_truth_source_drift_warned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """防漂移机械兜底（NB-WE-06 第 5 要素）— 真源临时缺值 → r.warn 漂移信号。

        模拟场景：真源 §零.1 表临时只剩 7 值（漏 150/41）,但 legal_set 仍是 9 值,
        应能在 check 启动时主动检测出漂移（issue 2026-05-11_1925 防漂移加固）。
        """
        from precheck_stage4 import check_z_index_compliance  # type: ignore
        monkeypatch.setattr(
            _stage4_mod,
            "_parse_z_index_truth_source",
            lambda: {200, 100, 60, 50, 40, 10, 1},  # 漏 150/41
        )
        prd = '<style>.foo { z-index: 200; }</style>'
        r = Report()
        check_z_index_compliance(prd, r)
        assert any("派生漂移" in w and "150" in w and "41" in w for w in r.warnings), \
            f"应触发漂移 warn 含 150/41,实际 warnings：{r.warnings}"

    def test_truth_source_missing_silently_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """真源文件不存在 / 解析失败 → 静默豁免,不阻断主流程。"""
        from precheck_stage4 import check_z_index_compliance  # type: ignore
        monkeypatch.setattr(_stage4_mod, "_parse_z_index_truth_source", lambda: None)
        prd = '<style>.foo { z-index: 200; }</style>'
        r = Report()
        check_z_index_compliance(prd, r)
        assert all("派生漂移" not in w for w in r.warnings), \
            f"真源缺失应静默,实际 warnings：{r.warnings}"

    def test_no_z_index_passes(self) -> None:
        """PRD 无任何 z-index → PASS（无需核查）。"""
        from precheck_stage4 import check_z_index_compliance  # type: ignore
        prd = "<html><head><style>.foo { color: red; }</style></head></html>"
        r = Report()
        check_z_index_compliance(prd, r)
        assert r.errors == []

    def test_magic_number_999_fails(self) -> None:
        """z-index: 999（魔术数,历史 PM 常见错误）→ FAIL。"""
        from precheck_stage4 import check_z_index_compliance  # type: ignore
        prd = """<style>
.modal { z-index: 999; }
.section-header { z-index: 200; }
</style>"""
        r = Report()
        check_z_index_compliance(prd, r)
        assert len(r.errors) >= 1
        assert any("999" in e for e in r.errors), f"错误应明示 999,实际：{r.errors}"

    def test_inline_style_z_index_caught(self) -> None:
        """inline style 中 z-index 也应被扫到（不止 <style> 块）。"""
        from precheck_stage4 import check_z_index_compliance  # type: ignore
        prd = '<div style="position: fixed; z-index: 1000;">弹框</div>'
        r = Report()
        check_z_index_compliance(prd, r)
        assert len(r.errors) >= 1
        assert any("1000" in e for e in r.errors)

    def test_multiple_violations_reported(self) -> None:
        """多处违反 → 全部报告(前 10 条)。"""
        from precheck_stage4 import check_z_index_compliance  # type: ignore
        prd = """<style>
.a { z-index: 999; }
.b { z-index: 555; }
.c { z-index: 88; }
.d { z-index: 200; }
</style>"""
        r = Report()
        check_z_index_compliance(prd, r)
        assert len(r.errors) >= 1
        # 报告中应含三个非法值
        full_err = " ".join(r.errors)
        for v in ("999", "555", "88"):
            assert v in full_err, f"错误应含 {v},实际：{full_err}"


# ── check_frame_card_isolation 用例（NB-WE-20 §零.2 rule-3 实装）─────────────


class TestFrameCardIsolation:
    """覆盖 check_frame_card_isolation — §零.2 rule-3「frame-card stacking context 隔离」。

    issue 2026-05-12 下游 # 14：assemble.py 旧版从不重读 template `<style>`,
    template L343 加 isolation: isolate 后 outputs/prd 派生层 .frame-card
    规则缺 isolation。本 check 是机械兜底层。
    """

    def test_isolation_present_passes(self) -> None:
        """.frame-card 规则含 isolation: isolate → PASS。"""
        from precheck_stage4 import check_frame_card_isolation  # type: ignore
        prd = """<style>
.frame-card {
  padding: 20px 24px;
  margin-bottom: 24px;
  box-sizing: border-box;
  isolation: isolate;
}
</style>"""
        r = Report()
        check_frame_card_isolation(prd, r)
        assert r.errors == [], f"含 isolation 应 PASS,实际错误：{r.errors}"

    def test_isolation_missing_fails(self) -> None:
        """.frame-card 规则缺 isolation → FAIL（指向 assemble.py 派生同步）。"""
        from precheck_stage4 import check_frame_card_isolation  # type: ignore
        prd = """<style>
.frame-card {
  padding: 20px 24px;
  margin-bottom: 24px;
  box-sizing: border-box;
}
</style>"""
        r = Report()
        check_frame_card_isolation(prd, r)
        assert any(
            "isolation" in e and "isolate" in e and "rule-3" in e for e in r.errors
        ), f"应触发 rule-3 FAIL 含 isolation/isolate 关键字,实际：{r.errors}"

    def test_no_frame_card_silently_passes(self) -> None:
        """PRD 无 .frame-card 规则 → 静默豁免（PASS）。"""
        from precheck_stage4 import check_frame_card_isolation  # type: ignore
        prd = "<style>.foo { color: red; }</style>"
        r = Report()
        check_frame_card_isolation(prd, r)
        assert r.errors == [], f"无 .frame-card 应豁免,实际：{r.errors}"


# ── check_state_naming_convention 用例（NB-WE-13 SSOT #14 状态命名规范）──────


class TestStateNamingConvention:
    """覆盖 precheck_stage4.check_state_naming_convention —
    SSOT #14 NB-WE-13 状态命名规范 + name ↔ prd_id 后缀对称。
    """

    def _scaffold(self, states: list[dict]) -> dict:
        return {
            "modules": [
                {"id": "M01", "pages": [{"id": "P01", "states": states}]}
            ]
        }

    def test_pass_lowercase_kebab(self) -> None:
        data = self._scaffold([
            {"name": "default", "prd_id": "H-M01-P01-default"},
            {"name": "loading", "prd_id": "H-M01-P01-loading"},
            {"name": "filter-no-result", "prd_id": "H-M01-P01-filter-no-result"},
        ])
        r = Report()
        check_state_naming_convention(data, r)
        assert r.errors == [], f"合规命名应 PASS,实际：{r.errors}"

    def test_fail_chinese_name(self) -> None:
        data = self._scaffold([
            {"name": "提交中", "prd_id": "H-M01-P01-提交中"}
        ])
        r = Report()
        check_state_naming_convention(data, r)
        assert any("提交中" in e and "命名规范" in e for e in r.errors), \
            f"应拦截中文 name,实际：{r.errors}"

    def test_fail_uppercase_name(self) -> None:
        data = self._scaffold([
            {"name": "Loading", "prd_id": "H-M01-P01-Loading"}
        ])
        r = Report()
        check_state_naming_convention(data, r)
        assert any("Loading" in e and "命名规范" in e for e in r.errors)

    def test_fail_underscore_name(self) -> None:
        data = self._scaffold([
            {"name": "no_data", "prd_id": "H-M01-P01-no_data"}
        ])
        r = Report()
        check_state_naming_convention(data, r)
        assert any("no_data" in e and "命名规范" in e for e in r.errors)

    def test_fail_prd_id_suffix_mismatch(self) -> None:
        """name=loading 但 prd_id 后缀写成 -load —— 人工手改 scaffold 后漂移场景。"""
        data = self._scaffold([
            {"name": "loading", "prd_id": "H-M01-P01-load"}
        ])
        r = Report()
        check_state_naming_convention(data, r)
        assert any("后缀" in e and "loading" in e for e in r.errors)

    def test_fail_combo_name_violation_and_suffix_drift(self) -> None:
        """同时违反 name 规范 + 后缀漂移 → 应报两类错误。"""
        data = self._scaffold([
            {"name": "Loading_中", "prd_id": "H-M01-P01-loading"}
        ])
        r = Report()
        check_state_naming_convention(data, r)
        assert any("命名规范" in e for e in r.errors)
        assert any("后缀" in e for e in r.errors)


# ── check_spec_state_table_count 用例（NB-WE-13 spec ↔ scaffold 数对称）─────


class TestSpecStateTableCount:
    """覆盖 precheck_stage4.check_spec_state_table_count —
    spec 状态枚举表行数 ↔ scaffold states 数组长度对称。
    """

    def _scaffold(self, states_count: int) -> dict:
        states = [
            {"name": f"s{i}", "prd_id": f"H-M01-P01-s{i}"}
            for i in range(states_count)
        ]
        return {
            "modules": [
                {
                    "id": "M01",
                    "pages": [
                        {"id": "P01", "spec_id": "spec-M01-P01", "states": states}
                    ],
                }
            ]
        }

    def test_pass_count_match(self) -> None:
        data = self._scaffold(3)
        spec = """
spec-M01-P01

#### 状态枚举表

| 状态 ID | 状态名称 | 触发前提 | 是否互斥 | 对应帧 |
|--------|---------|---------|---------|-------|
| S01 | 默认态 | x | y | 帧1 |
| S02 | 空态 | x | y | 帧2 |
| S03 | 错误态 | x | y | 帧3 |
"""
        r = Report()
        check_spec_state_table_count(data, spec, r)
        assert r.errors == [], f"数对称应 PASS,实际：{r.errors}"

    def test_fail_spec_more_than_scaffold(self) -> None:
        data = self._scaffold(2)
        spec = """spec-M01-P01

| S01 | a | b | c | 帧1 |
| S02 | a | b | c | 帧2 |
| S03 | a | b | c | 帧3 |
"""
        r = Report()
        check_spec_state_table_count(data, spec, r)
        assert any("3 行" in e and "2 项" in e for e in r.errors)

    def test_fail_spec_less_than_scaffold(self) -> None:
        data = self._scaffold(4)
        spec = """spec-M01-P01

| S01 | a | b | c | 帧1 |
| S02 | a | b | c | 帧2 |
"""
        r = Report()
        check_spec_state_table_count(data, spec, r)
        assert any("2 行" in e and "4 项" in e for e in r.errors)

    def test_warn_when_no_spec_table_found(self) -> None:
        """spec 中完全没找到状态枚举表 → WARN 而非 FAIL。"""
        data = self._scaffold(3)
        spec = "无 spec_id 锚点的内容"
        r = Report()
        check_spec_state_table_count(data, spec, r)
        assert r.errors == [], "无表应 WARN,不该 FAIL"


# ── check_frame_page_metadata_consistency 用例（NB-WE-10 维度 A）──────────────


class TestFramePageMetadataConsistency:
    """覆盖 precheck_stage4.check_frame_page_metadata_consistency —
    NB-WE-10 维度 A: 同 page 跨 frame 元数据字面一致。
    """

    def _frame(self, prd_id: str, page_id: str, page_name: str,
               role: str, route: str) -> str:
        return f'''<section id="{prd_id}" class="proto-section">
  <span class="page-id">{page_id}</span>
  <span class="page-name">{page_name}</span>
  <span class="role-tag">视角：{role}</span>
  <span class="func-tag">路由：{route}</span>
</section>'''

    def test_pass_consistent_metadata(self) -> None:
        """同 page 多 frame 元数据全一致 → PASS。"""
        from precheck_stage4 import check_frame_page_metadata_consistency  # type: ignore
        prd = "\n".join([
            self._frame("H-M01-P01-default", "M01 / P01", "项目列表", "role-1", "/projects"),
            self._frame("H-M01-P01-loading", "M01 / P01", "项目列表", "role-1", "/projects"),
            self._frame("H-M01-P01-error", "M01 / P01", "项目列表", "role-1", "/projects"),
        ])
        r = Report()
        check_frame_page_metadata_consistency(prd, r)
        assert r.errors == [] and len(r.warnings) == 0, \
            f"全一致应 PASS,实际：errors={r.errors} warnings={r.warnings}"

    def test_warn_drift_page_name(self) -> None:
        """同 page 不同 frame 的 page-name 字面不一致 → WARN。"""
        from precheck_stage4 import check_frame_page_metadata_consistency  # type: ignore
        prd = "\n".join([
            self._frame("H-M01-P01-default", "M01 / P01", "项目列表", "role-1", "/projects"),
            self._frame("H-M01-P01-empty", "M01 / P01", "项目列表（销售）", "role-1", "/projects"),
        ])
        r = Report()
        check_frame_page_metadata_consistency(prd, r)
        assert r.errors == [], "降级 WARN 不应 FAIL"
        assert any("page-name" in w and "漂移" in w for w in r.warnings)

    def test_no_warn_single_frame_page(self) -> None:
        """page 只 1 个 frame → 不报漂移（无跨 frame 比较）。"""
        from precheck_stage4 import check_frame_page_metadata_consistency  # type: ignore
        prd = self._frame("H-M01-P01-default", "M01 / P01", "项目列表", "role-1", "/projects")
        r = Report()
        check_frame_page_metadata_consistency(prd, r)
        assert not any("漂移" in w for w in r.warnings)

    def test_warn_role_tag_drift(self) -> None:
        """role-tag 漂移（业务可能合理）→ WARN。"""
        from precheck_stage4 import check_frame_page_metadata_consistency  # type: ignore
        prd = "\n".join([
            self._frame("H-M05-P01-default", "M05 / P01", "页面 X", "role-1 / role-2", "/x"),
            self._frame("H-M05-P01-no-permission", "M05 / P01", "页面 X", "role-1", "/x"),
        ])
        r = Report()
        check_frame_page_metadata_consistency(prd, r)
        assert r.errors == [], "应 WARN 不 FAIL"
        assert any("role-tag" in w and "漂移" in w for w in r.warnings)


# ── check_field_format_consistency_across_pages 用例（NB-WE-10 维度 B）────


class TestFieldFormatConsistency:
    """覆盖 precheck_stage4.check_field_format_consistency_across_pages —
    NB-WE-10 维度 B: 同字段跨页字面一致。
    """

    def test_pass_same_format_across_pages(self) -> None:
        """同字段在多页字面一致 → PASS。"""
        from precheck_stage4 import check_field_format_consistency_across_pages  # type: ignore
        spec = """
### P-M01-P01：列表页
字段绑定表
| feedback_text | 反馈正文 | string | required, max=500 | §9.f1 | textarea | name="feedback_text" |
| name | 名称 | string | required | §9.f2 | input | name="name" |

### P-M01-P02：详情页
字段绑定表
| feedback_text | 反馈正文 | string | required, max=500 | §9.f1 | input | name="feedback_text" |
| name | 名称 | string | required | §9.f2 | span | data-field="name" |
"""
        r = Report()
        check_field_format_consistency_across_pages(spec, r)
        assert r.errors == [] and not any("漂移" in w for w in r.warnings), \
            f"全一致应 PASS,实际：{r.warnings}"

    def test_warn_drift_data_type(self) -> None:
        """同字段在多页数据类型不同 → WARN。"""
        from precheck_stage4 import check_field_format_consistency_across_pages  # type: ignore
        spec = """
### P-M01-P01：列表页
| count | 计数 | int | min=0 | §9.f1 | span |

### P-M01-P02：详情页
| count | 计数 | string | min=0 | §9.f1 | span |
"""
        r = Report()
        check_field_format_consistency_across_pages(spec, r)
        assert r.errors == []
        assert any("count" in w and "数据类型" in w and "漂移" in w for w in r.warnings)

    def test_pass_token_order_normalize(self) -> None:
        """约束列 token 顺序不同但内容相同 → normalize 后 PASS。"""
        from precheck_stage4 import check_field_format_consistency_across_pages  # type: ignore
        spec = """
### P-M01-P01：列表页
| feedback | 反馈 | string | required, max=500 | §9 | input |

### P-M01-P02：详情页
| feedback | 反馈 | string | max=500, required | §9 | input |
"""
        r = Report()
        check_field_format_consistency_across_pages(spec, r)
        assert not any("漂移" in w for w in r.warnings), \
            f"normalize 后应 PASS,实际：{r.warnings}"

    def test_no_check_single_page_field(self) -> None:
        """字段仅在单页出现 → 不进入跨页比较。"""
        from precheck_stage4 import check_field_format_consistency_across_pages  # type: ignore
        spec = """
### P-M01-P01：列表页
| only_here | 只此页 | string | required | §9 | input |
"""
        r = Report()
        check_field_format_consistency_across_pages(spec, r)
        assert not any("only_here" in w for w in r.warnings)


# ── _remove_sections_by_id_prefix 用例（NB-WE-16 嵌套 section 算法）──────────


class TestRemoveSectionsByIdPrefix:
    """覆盖 _remove_sections_by_id_prefix —— 平衡标签深度计数器替代非贪婪 regex。

    核心场景：proj-component-{name} 状态展示区内 PM 偶尔用 <section> 嵌套替代
    <article>,旧 regex `<section...>.*?</section>` 会停在第一个 </section> 漏剔
    外层。本组用例覆盖：嵌套 / 多个同前缀实例 / 无目标。
    """

    def test_nested_section_fully_removed(self) -> None:
        """proj-component- 外层含嵌套 section → 应整体剔除,不残留外层按钮。"""
        from precheck_stage4 import _remove_sections_by_id_prefix  # type: ignore
        html = (
            '<body>'
            '<section id="proj-component-foo">'
            '  <h2>foo</h2>'
            '  <section id="proj-foo-state-hover">'
            '    <p>hover state</p>'
            '  </section>'
            '  <button onclick="doX()">应被剔除</button>'
            '</section>'
            '<section id="other">'
            '  <button onclick="doY()">应保留</button>'
            '</section>'
            '</body>'
        )
        cleaned = _remove_sections_by_id_prefix(html, "proj-component-")
        assert "doX" not in cleaned, f"嵌套场景应整体剔除外层按钮 doX,实际：{cleaned}"
        assert "doY" in cleaned, f"非目标 section 应保留按钮 doY,实际：{cleaned}"
        assert "proj-component-foo" not in cleaned

    def test_multiple_same_prefix_sections_all_removed(self) -> None:
        """多个同前缀 section 并列 → 应全部剔除（不只剔除第一个）。"""
        from precheck_stage4 import _remove_sections_by_id_prefix  # type: ignore
        html = (
            '<section id="proj-component-foo"><button onclick="a()">A</button></section>'
            '<section id="kept"><button onclick="b()">B</button></section>'
            '<section id="proj-component-bar"><button onclick="c()">C</button></section>'
        )
        cleaned = _remove_sections_by_id_prefix(html, "proj-component-")
        assert "a()" not in cleaned and "c()" not in cleaned, \
            f"两个同前缀 section 应都剔除,实际：{cleaned}"
        assert "b()" in cleaned, f"中间非目标 section 应保留,实际：{cleaned}"

    def test_no_target_section_returns_input_unchanged(self) -> None:
        """无目标 section → 原样返回,不产生空字符串 / None / 异常。"""
        from precheck_stage4 import _remove_sections_by_id_prefix  # type: ignore
        html = '<section id="other"><button onclick="ok()">OK</button></section>'
        cleaned = _remove_sections_by_id_prefix(html, "proj-component-")
        assert cleaned == html, f"无目标场景应原样返回,实际：{cleaned!r}"


class TestI18nMinimum:
    """check_i18n_minimum — NB-阶段4-D B+ 档位最小化兜底。

    验收标准 #4: 模拟「触发 i18n 但 0 属性」场景能正确 BLOCK
    验收标准 #5: 模拟「无多语言需求」场景跳过 i18n 校验不阻断
    """

    def test_no_i18n_keyword_skips_check(self) -> None:
        """产品定义不含多语言关键字 → check 函数 ok,不阻断。"""
        from precheck_stage4 import check_i18n_minimum, Report  # type: ignore
        prd_html = '<div class="phone-frame"><span>首页</span></div>'
        pdef_text = "## 1. 问题陈述\n本产品仅面向单语用户。\n## 13. 非功能需求\n响应 < 2s。"
        r = Report()
        check_i18n_minimum(prd_html, pdef_text, r)
        assert len(r.errors) == 0, f"无多语言需求场景不应 FAIL,实际:{r.errors}"

    def test_i18n_triggered_but_zero_data_zh_blocks(self) -> None:
        """产品定义含多语言关键字但 prd.html data-zh = 0 → check 函数 FAIL。"""
        from precheck_stage4 import check_i18n_minimum, Report  # type: ignore
        prd_html = '<div class="phone-frame"><span>首页</span></div>'  # 0 data-zh
        pdef_text = "## 13. 非功能需求\n本产品要求支持中英双语切换。"
        r = Report()
        check_i18n_minimum(prd_html, pdef_text, r)
        assert len(r.errors) == 1, f"应 FAIL 1 项,实际 {len(r.errors)} 项:{r.errors}"
        assert "add_i18n.py" in r.errors[0], "FAIL 文案应引导到 add_i18n.py 工具"

    def test_i18n_triggered_with_data_zh_passes(self) -> None:
        """产品定义含多语言关键字且 prd.html 含 data-zh → check 函数 PASS。"""
        from precheck_stage4 import check_i18n_minimum, Report  # type: ignore
        prd_html = (
            '<div class="phone-frame">'
            '<span data-zh="首页" data-en="Home">首页</span>'
            '<span data-zh="新建" data-en="Create">新建</span>'
            "</div>"
        )
        pdef_text = "本产品支持多语言 (中英) 切换。"
        r = Report()
        check_i18n_minimum(prd_html, pdef_text, r)
        assert len(r.errors) == 0, f"应 PASS,实际 FAIL:{r.errors}"

    def test_i18n_keyword_variants_all_trigger(self) -> None:
        """4 个关键字（多语言/中英/双语/i18n）任一触发即视为需求。"""
        from precheck_stage4 import check_i18n_minimum, Report  # type: ignore
        for kw in ("多语言", "中英", "双语", "i18n"):
            r = Report()
            check_i18n_minimum(
                '<div class="phone-frame"><span>首页</span></div>',  # 0 data-zh
                f"产品支持 {kw} 切换",
                r,
            )
            assert len(r.errors) == 1, f"关键字 '{kw}' 应触发 BLOCK,实际通过"


class TestS428ActionBar:
    """覆盖 check_desktop_sticky_completeness v3 — S4-28 统一底栏 .fb-action-bar 合规校验。

    v3 升级（CSS 变量继承机制）：扫 .fb-action-bar + 3 deprecated 别名
    （fb-frame-bottom-bar / fb-modal-footer / fb-drawer-footer），三层校验：
      ① v2 结构层"frame 直接子层必填"约束 v3 放宽（CSS 变量继承支持任意嵌套深度）
      ② 移动端 frame（phone/h5/miniprogram）直接子层 → WARN（违 proto_cross_platform §三）
         例外：嵌套在 modal/drawer 内可用（变量继承自动取静态行为）
      ③ deprecated 别名命中 → WARN 提示迁移到 .fb-action-bar

    WARN 阶段（下游迁移缓冲）；0 命中 = 下游未使用底栏属正常。
    """

    def test_zero_bars_ok(self) -> None:
        """0 个底栏 class → OK，无 error/warning。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="desktop-frame"><div class="main">x</div></div>', r
        )
        assert r.errors == [] and r.warnings == [], (
            f"0 命中应静默 OK,实际 errors={r.errors} warnings={r.warnings}"
        )

    def test_action_bar_in_desktop_frame_ok(self) -> None:
        """.fb-action-bar 在 .desktop-frame 内（v3 合规）→ OK。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="desktop-frame"><div class="sidebar"></div>'
            '<div class="fb-action-bar"><button>保存</button></div></div>',
            r,
        )
        assert r.errors == [] and r.warnings == [], (
            f"v3 合规应 OK,实际 errors={r.errors} warnings={r.warnings}"
        )

    def test_action_bar_in_tablet_frame_ok(self) -> None:
        """.fb-action-bar 在 .tablet-frame 内 → OK。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="tablet-frame"><div class="fb-action-bar"></div></div>',
            r,
        )
        assert r.errors == [] and r.warnings == []

    def test_action_bar_in_modal_ok(self) -> None:
        """.fb-action-bar 在 modal 内（嵌套深度任意）→ OK（变量继承自动取静态行为）。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="fb-modal-overlay is-visible"><div class="fb-modal">'
            '<div class="fb-modal-header">x</div>'
            '<div class="fb-modal-body">y</div>'
            '<div class="fb-action-bar"><button>确认</button></div>'
            '</div></div>',
            r,
        )
        assert r.errors == [] and r.warnings == [], (
            f"modal 内 .fb-action-bar 应 OK,实际 warnings={r.warnings}"
        )

    def test_action_bar_in_drawer_ok(self) -> None:
        """.fb-action-bar 在 drawer 内 → OK。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<aside class="fb-drawer fb-drawer-right is-visible">'
            '<div class="fb-drawer-body">x</div>'
            '<div class="fb-action-bar"><button>关闭</button></div>'
            '</aside>',
            r,
        )
        assert r.errors == [] and r.warnings == [], (
            f"drawer 内 .fb-action-bar 应 OK,实际 warnings={r.warnings}"
        )

    def test_action_bar_in_phone_frame_direct_warns(self) -> None:
        """.fb-action-bar 在 phone-frame 直接子层 → 移动端 WARN（违 proto_cross_platform §三）。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="phone-frame"><div class="fb-action-bar"><button>提交</button></div></div>',
            r,
        )
        assert r.errors == [], f"WARN 阶段不应 FAIL,实际 errors={r.errors}"
        assert any(
            "S4-28 v3" in w and "移动端" in w for w in r.warnings
        ), f"应触发移动端 frame WARN,实际 warnings={r.warnings}"

    def test_action_bar_in_phone_frame_nested_modal_ok(self) -> None:
        """phone-frame 内嵌套 modal 内 .fb-action-bar → OK（例外，变量继承自动取静态行为）。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="phone-frame">'
            '<div class="fb-modal-overlay is-visible"><div class="fb-modal">'
            '<div class="fb-modal-body">x</div>'
            '<div class="fb-action-bar"><button>确认</button></div>'
            '</div></div></div>',
            r,
        )
        # 此处不应触发移动端 WARN（祖先含 .fb-modal → 例外）
        mobile_warns = [w for w in r.warnings if "移动端" in w]
        assert mobile_warns == [], (
            f"phone-frame 嵌套 modal 内应例外（OK），不应触发移动端 WARN,"
            f"实际 mobile_warns={mobile_warns}"
        )

    def test_deprecated_frame_bottom_bar_warns(self) -> None:
        """旧 .fb-frame-bottom-bar 命中 → deprecated WARN（仍生效但提示迁移）。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="desktop-frame"><div class="fb-frame-bottom-bar"></div></div>',
            r,
        )
        assert r.errors == [], f"WARN 阶段不应 FAIL,实际 errors={r.errors}"
        deps = [w for w in r.warnings if "deprecated" in w and "fb-frame-bottom-bar" in w]
        assert len(deps) == 1, (
            f"应触发 1 个 deprecated WARN,实际 deps={deps}"
        )

    def test_deprecated_modal_footer_warns(self) -> None:
        """旧 .fb-modal-footer 命中 → deprecated WARN。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="fb-modal"><div class="fb-modal-footer"></div></div>',
            r,
        )
        deps = [w for w in r.warnings if "deprecated" in w and "fb-modal-footer" in w]
        assert len(deps) == 1, f"应触发 1 个 deprecated WARN,实际 deps={deps}"

    def test_deprecated_drawer_footer_warns(self) -> None:
        """旧 .fb-drawer-footer 命中 → deprecated WARN。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<aside class="fb-drawer"><div class="fb-drawer-footer"></div></aside>',
            r,
        )
        deps = [w for w in r.warnings if "deprecated" in w and "fb-drawer-footer" in w]
        assert len(deps) == 1, f"应触发 1 个 deprecated WARN,实际 deps={deps}"

    def test_double_class_overlap_double_deprecated(self) -> None:
        """v2 双重叠加 class="fb-modal-footer fb-frame-bottom-bar" → 触发 deprecated WARN
        （单元素命中多个旧 class，按字典序首位报告即可，关键是迁移路径明确）。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="fb-modal"><div class="fb-modal-footer fb-frame-bottom-bar"></div></div>',
            r,
        )
        deps = [w for w in r.warnings if "deprecated" in w]
        # 命中至少 1 个 deprecated WARN（字典序取首位报告）
        assert len(deps) >= 1, f"双重叠加应至少触发 1 deprecated WARN,实际 deps={deps}"
        # 报告含 fb-frame-bottom-bar（字典序 < fb-modal-footer）
        assert any("fb-frame-bottom-bar" in w for w in deps), (
            f"应报告 fb-frame-bottom-bar（字典序首位）,实际 deps={deps}"
        )

    def test_misplaced_in_wrapper_no_longer_warns(self) -> None:
        """v3 放宽：嵌套在 wrapper 内不再触发 misplace WARN（CSS 变量继承支持任意嵌套）。

        v2 期望: .fb-frame-bottom-bar 嵌在 wrapper 内 → misplace WARN
        v3 现状: 嵌套深度不敏感（变量继承生效），不报 misplace；但若是 deprecated 别名仍报 deprecated。
        """
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="desktop-frame"><div class="wrap">'
            '<div class="fb-action-bar"><button>x</button></div></div></div>',
            r,
        )
        # v3 放宽：不应有 misplace WARN（嵌套深度不敏感）
        misplace_warns = [w for w in r.warnings if "misplace" in w.lower() or "不是" in w]
        assert misplace_warns == [], (
            f"v3 嵌套深度不敏感，wrapper 内不应触发 misplace WARN,"
            f"实际 misplace_warns={misplace_warns}"
        )


# ── check_inline_position_compliance 用例（S4-28 v2 档 C 第 3 条补充，2026-05-29）──


class TestInlinePositionCompliance:
    """覆盖 precheck_stage4.check_inline_position_compliance — S4-28 inline 反规避（WARN）。

    场景：PM 完全规避 .fb-frame-bottom-bar pub 组件，手写 inline `style="position:fixed"`
    实现底栏（quotation-tool L8705 实证）。零启发式字面扫，检测 position:fixed/sticky。
    """

    def test_clean_html_passes(self) -> None:
        """无 inline position 字面 → OK（不报 WARN）。"""
        from precheck_stage4 import check_inline_position_compliance  # type: ignore
        r = Report()
        check_inline_position_compliance(
            '<div class="desktop-frame"><div class="fb-frame-bottom-bar">'
            '<button>保存</button></div></div>',
            r,
        )
        assert r.errors == [] and r.warnings == [], (
            f"无违规应 OK,实际 errors={r.errors} warnings={r.warnings}"
        )

    def test_inline_position_fixed_warns(self) -> None:
        """inline `style="position:fixed"` 手写底栏 → WARN（quotation-tool L8705 同型）。"""
        from precheck_stage4 import check_inline_position_compliance  # type: ignore
        r = Report()
        check_inline_position_compliance(
            '<div class="phone-frame">'
            '<div style="position:fixed; bottom:0; left:0; right:0; display:flex; gap:8px;">'
            '<button>提交</button></div></div>',
            r,
        )
        assert r.errors == [], f"WARN 阶段不应 FAIL,实际 errors={r.errors}"
        assert any(
            "position:fixed" in w and "S4-28" in w for w in r.warnings
        ), f"应触发 S4-28 inline position:fixed WARN,实际 warnings={r.warnings}"

    def test_inline_position_sticky_warns(self) -> None:
        """inline `style="position:sticky"` 也属违规 → WARN（v1 污染 5 处教训同型）。"""
        from precheck_stage4 import check_inline_position_compliance  # type: ignore
        r = Report()
        check_inline_position_compliance(
            '<div style="position: sticky; bottom: 0;">操作栏</div>',
            r,
        )
        assert r.errors == []
        assert any(
            "position:sticky" in w and "S4-28" in w for w in r.warnings
        ), f"应触发 S4-28 inline position:sticky WARN,实际 warnings={r.warnings}"

    def test_multiple_violations_listed(self) -> None:
        """多处违规 → 一个 WARN 列出所有命中行号。"""
        from precheck_stage4 import check_inline_position_compliance  # type: ignore
        r = Report()
        html = (
            '<div style="position:fixed; bottom:0;">A</div>\n'
            '<div style="display:flex;">B</div>\n'
            '<div style="position:sticky; top:0;">C</div>'
        )
        check_inline_position_compliance(html, r)
        assert r.errors == []
        warns = [w for w in r.warnings if "S4-28" in w]
        assert len(warns) >= 1
        # 检查 WARN 字符串中确含 2 处违规计数
        assert any("2 处" in w for w in warns), f"应汇报 2 处违规,实际 warnings={r.warnings}"

    def test_case_insensitive_and_whitespace_tolerant(self) -> None:
        """容忍大小写 + 空白（`Position : Fixed` 等变体也应捕获）。"""
        from precheck_stage4 import check_inline_position_compliance  # type: ignore
        r = Report()
        check_inline_position_compliance(
            '<div style="Position : Fixed; bottom : 0;">x</div>',
            r,
        )
        assert any("position:fixed" in w.lower() for w in r.warnings), (
            f"大小写 + 空白变体应捕获,实际 warnings={r.warnings}"
        )

    def test_position_relative_absolute_not_flagged(self) -> None:
        """position:relative / position:absolute 不在禁令范围 → 不报 WARN（S4-28 仅禁 fixed/sticky）。"""
        from precheck_stage4 import check_inline_position_compliance  # type: ignore
        r = Report()
        check_inline_position_compliance(
            '<div style="position:relative; z-index:1;">A</div>'
            '<div style="position:absolute; top:0;">B</div>',
            r,
        )
        assert r.errors == [] and r.warnings == [], (
            f"position:relative/absolute 不应报 WARN,实际 errors={r.errors} warnings={r.warnings}"
        )


# ── check_scaffold logic-only 模块用例（SSOT #50，2026-05-28 落地）──────────────


class TestScaffoldLogicOnlyModule:
    """覆盖 check_scaffold 对 logic-only 模块（pages=[]）的 ui_carrier_modules 校验。

    场景：业务逻辑层 / API 层模块 UI 100% 内嵌于其他承载模块 → pages=[] 合法，但必须
    显式声明 ui_carrier_modules 数组指向承载 UI 的模块 id（引用 ⊂ scaffold.modules[].id）。
    详 agent_dispatch_protocol.md §scaffold v2.0 schema「logic-only 模块说明」。
    """

    def _build_scaffold(self, modules: list) -> dict:
        """构造 minimal scaffold（含 product/platforms/modules 三项必填顶层字段）。"""
        return {
            "product": "测试产品",
            "platforms": ["desktop"],
            "modules": modules,
        }

    def _ui_mod(self, mid: str) -> dict:
        """构造一个最小合法 UI 模块（pages 非空 + 至少 1 state）。"""
        return {
            "id": mid,
            "name": f"UI 模块 {mid}",
            "pages": [
                {"id": "P01", "name": "页1",
                 "states": [{"name": "default", "roles": []}]}
            ],
        }

    def test_logic_only_pass_with_valid_carriers(self) -> None:
        """合法 logic-only：pages=[] + ui_carrier_modules 引用存在的模块 → 不触发 FAIL。"""
        data = self._build_scaffold([
            self._ui_mod("M01"),
            {"id": "M02", "name": "数据契约模块",
             "pages": [], "ui_carrier_modules": ["M01"]},
        ])
        r = Report()
        _stage4_mod.check_scaffold(data, r)
        # 仅断言 logic-only 相关错误为 0（其他维度的报错过滤掉）
        logic_errs = [
            e for e in r.errors
            if "M02" in e and ("ui_carrier" in e or "logic-only" in e or "pages=[]" in e)
        ]
        assert logic_errs == [], f"合法 logic-only 不应触发 ui_carrier 校验 FAIL：{logic_errs}"

    def test_logic_only_fail_missing_ui_carriers(self) -> None:
        """pages=[] 但缺 ui_carrier_modules 字段 → FAIL（含 logic-only / ui_carrier_modules 提示）。"""
        data = self._build_scaffold([
            self._ui_mod("M01"),
            {"id": "M02", "name": "无 UI 模块", "pages": []},
        ])
        r = Report()
        _stage4_mod.check_scaffold(data, r)
        assert any(
            "M02" in e and "ui_carrier_modules" in e and "logic-only" in e
            for e in r.errors
        ), f"缺 ui_carrier_modules 必须 FAIL；实际 errors={r.errors}"

    def test_logic_only_fail_empty_ui_carriers(self) -> None:
        """pages=[] 且 ui_carrier_modules=[] → FAIL（非空数组要求）。"""
        data = self._build_scaffold([
            self._ui_mod("M01"),
            {"id": "M02", "name": "无 UI 模块",
             "pages": [], "ui_carrier_modules": []},
        ])
        r = Report()
        _stage4_mod.check_scaffold(data, r)
        assert any(
            "M02" in e and "ui_carrier_modules" in e and "非空" in e
            for e in r.errors
        ), f"空 ui_carrier_modules 必须 FAIL；实际 errors={r.errors}"

    def test_logic_only_fail_invalid_ref(self) -> None:
        """ui_carrier_modules 引用不存在的模块 id → FAIL（引用完整性）。"""
        data = self._build_scaffold([
            self._ui_mod("M01"),
            {"id": "M02", "name": "无 UI 模块",
             "pages": [], "ui_carrier_modules": ["M99"]},  # M99 不存在
        ])
        r = Report()
        _stage4_mod.check_scaffold(data, r)
        assert any(
            "M02" in e and "ui_carrier_modules" in e and "M99" in e
            for e in r.errors
        ), f"非法引用必须 FAIL；实际 errors={r.errors}"

    def test_logic_only_fail_non_array_ui_carriers(self) -> None:
        """ui_carrier_modules 字段非数组（字符串） → FAIL（类型检查）。"""
        data = self._build_scaffold([
            self._ui_mod("M01"),
            {"id": "M02", "name": "无 UI 模块",
             "pages": [], "ui_carrier_modules": "M01"},  # 应为数组
        ])
        r = Report()
        _stage4_mod.check_scaffold(data, r)
        assert any(
            "M02" in e and "ui_carrier_modules" in e and "非空" in e
            for e in r.errors
        ), f"非数组 ui_carrier_modules 必须 FAIL；实际 errors={r.errors}"

    def test_logic_only_fail_self_reference(self) -> None:
        """ui_carrier_modules 自引（M02 → M02） → FAIL（SSOT #50 D-自引防御）。"""
        data = self._build_scaffold([
            self._ui_mod("M01"),
            {"id": "M02", "name": "自引模块",
             "pages": [], "ui_carrier_modules": ["M02"]},  # 自引
        ])
        r = Report()
        _stage4_mod.check_scaffold(data, r)
        assert any(
            "M02" in e and "自引" in e for e in r.errors
        ), f"自引必须 FAIL；实际 errors={r.errors}"

    def test_logic_only_fail_pointing_to_logic_only(self) -> None:
        """ui_carrier_modules 指向其他 logic-only 模块 → FAIL（SSOT #50 D-链式/环引防御）。"""
        data = self._build_scaffold([
            self._ui_mod("M01"),
            {"id": "M02", "name": "logic 模块 1",
             "pages": [], "ui_carrier_modules": ["M03"]},  # 指向 M03
            {"id": "M03", "name": "logic 模块 2",
             "pages": [], "ui_carrier_modules": ["M01"]},  # M03 也是 logic-only
        ])
        r = Report()
        _stage4_mod.check_scaffold(data, r)
        assert any(
            "M02" in e and "logic-only" in e and "M03" in e for e in r.errors
        ), f"指向 logic-only 必须 FAIL；实际 errors={r.errors}"


# ── S4-28 v3 R2 升级用例（data-purpose 白名单，2026-05-30）──


class TestS428ActionBarR2DataPurpose:
    """覆盖 check_desktop_sticky_completeness R2 升级 — 移动端 frame 直接子层
    .fb-action-bar 按 data-purpose 白名单判定（page-main / multi-select-batch /
    workflow-nav 合规，其他 WARN）。
    """

    def test_data_purpose_page_main_ok(self) -> None:
        """phone-frame 直接子 .fb-action-bar data-purpose="page-main" → 合规。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="phone-frame">'
            '  <div class="fb-action-bar" data-purpose="page-main">'
            '    <button class="fb-btn fb-btn-primary">导出</button>'
            '  </div>'
            '</div>',
            r,
        )
        mobile_warns = [w for w in r.warnings if 'S4-28 v3 R2' in w]
        assert mobile_warns == [], f"page-main 合规不应 WARN，实际 {mobile_warns}"

    def test_data_purpose_multi_select_batch_ok(self) -> None:
        """multi-select-batch 合规。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="phone-frame">'
            '  <div class="fb-action-bar" data-purpose="multi-select-batch">'
            '    <button class="fb-btn fb-btn-danger">批量删除</button>'
            '  </div>'
            '</div>',
            r,
        )
        mobile_warns = [w for w in r.warnings if 'S4-28 v3 R2' in w]
        assert mobile_warns == []

    def test_data_purpose_workflow_nav_ok(self) -> None:
        """workflow-nav 合规。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="phone-frame">'
            '  <div class="fb-action-bar" data-purpose="workflow-nav">'
            '    <button class="fb-btn">上一步</button>'
            '    <button class="fb-btn fb-btn-primary">下一步</button>'
            '  </div>'
            '</div>',
            r,
        )
        mobile_warns = [w for w in r.warnings if 'S4-28 v3 R2' in w]
        assert mobile_warns == []

    def test_no_data_purpose_warns(self) -> None:
        """无 data-purpose → WARN（提示加显式 data-purpose 或改 navbar variant）。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="phone-frame">'
            '  <div class="fb-action-bar">'
            '    <button class="fb-btn">x</button>'
            '  </div>'
            '</div>',
            r,
        )
        mobile_warns = [w for w in r.warnings if 'S4-28 v3 R2' in w and '无 data-purpose' in w]
        assert len(mobile_warns) == 1

    def test_invalid_data_purpose_warns(self) -> None:
        """data-purpose 不在白名单 → WARN。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="phone-frame">'
            '  <div class="fb-action-bar" data-purpose="some-other-purpose">'
            '    <button class="fb-btn">x</button>'
            '  </div>'
            '</div>',
            r,
        )
        mobile_warns = [w for w in r.warnings if 'S4-28 v3 R2' in w and 'some-other-purpose' in w]
        assert len(mobile_warns) == 1

    def test_data_purpose_in_modal_irrelevant(self) -> None:
        """data-purpose 在 modal 嵌套时无关（CSS 变量继承自动处理） → 不报 WARN。"""
        from precheck_stage4 import check_desktop_sticky_completeness  # type: ignore
        r = Report()
        check_desktop_sticky_completeness(
            '<div class="phone-frame">'
            '  <div class="fb-modal-overlay is-visible"><div class="fb-modal">'
            '    <div class="fb-action-bar">'  # 无 data-purpose，modal 嵌套自动合规
            '      <button class="fb-btn">确定</button>'
            '    </div>'
            '  </div></div>'
            '</div>',
            r,
        )
        mobile_warns = [w for w in r.warnings if 'S4-28 v3 R2' in w]
        assert mobile_warns == [], (
            f"modal 嵌套不应触发 R2 WARN（变量继承例外），实际 {mobile_warns}"
        )


class TestPanelClassEvasionExtension:
    """覆盖 check_panel_class_evasion 扩展 — S4-35 v2 移动 frame 直接子层
    inline sticky 顶部容器自由发挥拦截（2026-05-30 落地）。
    """

    def test_inline_sticky_top_div_warns(self) -> None:
        """phone-frame 直接子 inline `style="position:sticky;top:0"` div → WARN。"""
        from precheck_stage4 import check_panel_class_evasion  # type: ignore
        r = Report()
        check_panel_class_evasion(
            '<div class="phone-frame">'
            '  <div style="position:sticky; top:0; padding:8px 16px">'
            '    自定义顶栏'
            '  </div>'
            '</div>',
            r,
        )
        evasion_warns = [w for w in r.warnings if 'sticky 顶部容器' in w]
        assert len(evasion_warns) == 1, (
            f"inline sticky 顶部容器应 WARN，实际 {r.warnings}"
        )

    def test_fb_navbar_with_inline_sticky_excluded(self) -> None:
        """.fb-navbar 标准类即使有 inline sticky 也豁免（合规 navbar）→ 不报 WARN。"""
        from precheck_stage4 import check_panel_class_evasion  # type: ignore
        r = Report()
        check_panel_class_evasion(
            '<div class="phone-frame">'
            '  <div class="fb-navbar" data-variant="detail" style="position:sticky;top:0">'
            '    <span class="fb-nav-title">页</span>'
            '  </div>'
            '</div>',
            r,
        )
        evasion_warns = [w for w in r.warnings if 'sticky 顶部容器' in w]
        assert evasion_warns == [], (
            f".fb-navbar 类应豁免，实际 {evasion_warns}"
        )

    def test_proj_component_excluded(self) -> None:
        """.proj-* 项目组件类豁免 → 不报 WARN。"""
        from precheck_stage4 import check_panel_class_evasion  # type: ignore
        r = Report()
        check_panel_class_evasion(
            '<div class="phone-frame">'
            '  <div class="proj-custom-header" style="position:sticky;top:0">'
            '    proj 顶栏'
            '  </div>'
            '</div>',
            r,
        )
        evasion_warns = [w for w in r.warnings if 'sticky 顶部容器' in w]
        assert evasion_warns == []

    def test_no_phone_frame_no_check(self) -> None:
        """无 phone/h5/miniprogram-frame → 跳过扫描。"""
        from precheck_stage4 import check_panel_class_evasion  # type: ignore
        r = Report()
        check_panel_class_evasion(
            '<div class="desktop-frame">'
            '  <div style="position:sticky;top:0">x</div>'
            '</div>',
            r,
        )
        evasion_warns = [w for w in r.warnings if 'sticky 顶部容器' in w]
        assert evasion_warns == []


# ── S4-36 / S4-37 用例（A 方案 A.1 + A.2，2026-05-30）──


class TestS436TpMarkerPairing:
    """覆盖 check_tp_marker_pairing — S4-36 v1 data-tp ↔ tp-marker 配对完整性（A.1）。"""

    def test_paired_ok(self) -> None:
        """data-tp + 同级配对 marker → OK。"""
        from precheck_stage4 import check_tp_marker_pairing  # type: ignore
        r = Report()
        check_tp_marker_pairing(
            '<button data-tp="M01-P01-T05">x</button>'
            '<span class="tp-marker">05</span>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-36' in w]
        assert warns == [], f"配对应 OK，实际 {warns}"

    def test_no_pairing_warns(self) -> None:
        """data-tp 无配对 marker → WARN。"""
        from precheck_stage4 import check_tp_marker_pairing  # type: ignore
        r = Report()
        check_tp_marker_pairing(
            '<button data-tp="M01-P01-T05">x</button>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-36' in w]
        assert len(warns) >= 1
        assert 'M01-P01-T05' in warns[0]

    def test_wrong_number_warns(self) -> None:
        """配对 marker 编号不匹配 → WARN。"""
        from precheck_stage4 import check_tp_marker_pairing  # type: ignore
        r = Report()
        check_tp_marker_pairing(
            '<button data-tp="M01-P01-T05">x</button>'
            '<span class="tp-marker">99</span>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-36' in w]
        assert len(warns) >= 1

    def test_showcase_only_exempt(self) -> None:
        """showcase-only 父祖先豁免 → OK。"""
        from precheck_stage4 import check_tp_marker_pairing  # type: ignore
        r = Report()
        check_tp_marker_pairing(
            '<div class="showcase-only">'
            '<button data-tp="M01-P01-T05">x</button>'
            '</div>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-36' in w]
        assert warns == []

    def test_is_unchecked_exempt(self) -> None:
        """is-unchecked 豁免 → OK。"""
        from precheck_stage4 import check_tp_marker_pairing  # type: ignore
        r = Report()
        check_tp_marker_pairing(
            '<input class="fb-radio is-unchecked" data-tp="M01-P01-T05" />',
            r,
        )
        warns = [w for w in r.warnings if 'S4-36' in w]
        assert warns == []

    def test_d_type_pairing(self) -> None:
        """D 类触点（危险操作）同 T 类规则。"""
        from precheck_stage4 import check_tp_marker_pairing  # type: ignore
        r = Report()
        check_tp_marker_pairing(
            '<button data-tp="M01-P01-D03">x</button>'
            '<span class="tp-marker">03</span>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-36' in w]
        assert warns == []


class TestS437TpMarkerWrap:
    """覆盖 check_tp_marker_wrap — S4-37 v1 tp-marker tp-wrap 包裹结构（A.2）。"""

    def test_tp_wrap_ok(self) -> None:
        """tp-marker 在 .tp-wrap 父内 → OK。"""
        from precheck_stage4 import check_tp_marker_wrap  # type: ignore
        r = Report()
        check_tp_marker_wrap(
            '<span class="tp-wrap">'
            '<button>x</button>'
            '<span class="tp-marker">01</span>'
            '</span>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-37' in w]
        assert warns == []

    def test_no_wrap_warns(self) -> None:
        """tp-marker 无 .tp-wrap 父 → WARN。"""
        from precheck_stage4 import check_tp_marker_wrap  # type: ignore
        r = Report()
        check_tp_marker_wrap(
            '<div><span class="tp-marker">01</span></div>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-37' in w]
        assert len(warns) >= 1

    def test_data_tp_no_wrap_exempt(self) -> None:
        """data-tp-no-wrap 属性豁免 → OK。"""
        from precheck_stage4 import check_tp_marker_wrap  # type: ignore
        r = Report()
        check_tp_marker_wrap(
            '<div data-tp-no-wrap>'
            '<span class="tp-marker">01</span>'
            '</div>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-37' in w]
        assert warns == []

    def test_no_marker_ok(self) -> None:
        """无 tp-marker → 跳过校验，0 WARN。"""
        from precheck_stage4 import check_tp_marker_wrap  # type: ignore
        r = Report()
        check_tp_marker_wrap(
            '<div><button>x</button></div>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-37' in w]
        assert warns == []

    def test_multiple_violations_reports(self) -> None:
        """多处违规 → 报多 WARN（最多前 10 条 + 计数）。"""
        from precheck_stage4 import check_tp_marker_wrap  # type: ignore
        r = Report()
        html = '<div>' + '<span class="tp-marker">01</span>' * 12 + '</div>'
        check_tp_marker_wrap(html, r)
        warns = [w for w in r.warnings if 'S4-37' in w]
        assert len(warns) >= 10  # 至少前 10 个 WARN


# ── S4-38 / S4-39 用例（A 方案 A.3 + A.4，2026-05-30）──


class TestS438SectionMinContent:
    """覆盖 check_section_min_content — S4-38 v1 PRD section 最小内容粒度（A.3）。"""

    def test_long_content_ok(self) -> None:
        """section 内容 ≥ 500B → OK。"""
        from precheck_stage4 import check_section_min_content  # type: ignore
        r = Report()
        filler = "x" * 600
        check_section_min_content(f'<section id="s1">{filler}</section>', r)
        assert [w for w in r.warnings if 'S4-38' in w] == []

    def test_empty_shell_warns(self) -> None:
        """section 内容 < 500B → WARN。"""
        from precheck_stage4 import check_section_min_content  # type: ignore
        r = Report()
        check_section_min_content('<section id="s1">短壳</section>', r)
        warns = [w for w in r.warnings if 'S4-38' in w]
        assert len(warns) == 1
        assert 's1' in warns[0]

    def test_explicit_exempt_ok(self) -> None:
        """显式豁免标 → OK。"""
        from precheck_stage4 import check_section_min_content  # type: ignore
        r = Report()
        check_section_min_content(
            '<section id="s1">短壳<!-- section-shell-by-design: 占位 --></section>',
            r,
        )
        assert [w for w in r.warnings if 'S4-38' in w] == []

    def test_no_section_skipped(self) -> None:
        """无 section → 跳过校验。"""
        from precheck_stage4 import check_section_min_content  # type: ignore
        r = Report()
        check_section_min_content('<div>x</div>', r)
        assert [w for w in r.warnings if 'S4-38' in w] == []


class TestS439MermaidLabelChars:
    """覆盖 check_mermaid_label_chars — S4-39 v1 Mermaid label 字符安全（A.4）。"""

    def test_safe_string_literal_ok(self) -> None:
        """A["normal text"] mermaid 合法 string literal → OK。"""
        from precheck_stage4 import check_mermaid_label_chars  # type: ignore
        r = Report()
        check_mermaid_label_chars(
            "",
            '<pre class="mermaid">graph TD\nA["normal text"] --> B</pre>',
            r,
        )
        assert [w for w in r.warnings if 'S4-39' in w] == []

    def test_subroutine_shape_ok(self) -> None:
        """A[["text"]] mermaid subroutine shape → OK（v2 不报）。"""
        from precheck_stage4 import check_mermaid_label_chars  # type: ignore
        r = Report()
        check_mermaid_label_chars(
            "",
            '<pre class="mermaid">graph TD\nA[["text"]] --> B</pre>',
            r,
        )
        assert [w for w in r.warnings if 'S4-39' in w] == []

    def test_escaped_quot_ok(self) -> None:
        """A[text &quot;esc&quot;] 已转义 → OK。"""
        from precheck_stage4 import check_mermaid_label_chars  # type: ignore
        r = Report()
        check_mermaid_label_chars(
            "",
            '<pre class="mermaid">graph TD\nA[text &quot;esc&quot;] --> B</pre>',
            r,
        )
        assert [w for w in r.warnings if 'S4-39' in w] == []

    def test_nested_4_quotes_warns(self) -> None:
        """A["text "inner" abc"] 4 个未转义 → WARN（必嵌套）。"""
        from precheck_stage4 import check_mermaid_label_chars  # type: ignore
        r = Report()
        check_mermaid_label_chars(
            "",
            '<pre class="mermaid">graph TD\nA["text "inner" abc"] --> B</pre>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-39' in w]
        assert len(warns) == 1

    def test_odd_quotes_warns(self) -> None:
        """A[text" abc] 奇数 1 个 → WARN（必未闭合）。"""
        from precheck_stage4 import check_mermaid_label_chars  # type: ignore
        r = Report()
        check_mermaid_label_chars(
            "",
            '<pre class="mermaid">graph TD\nA[text" abc] --> B</pre>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-39' in w]
        assert len(warns) == 1

    def test_chinese_comma_warns(self) -> None:
        """A[标题，副标题] 中文逗号 → WARN。"""
        from precheck_stage4 import check_mermaid_label_chars  # type: ignore
        r = Report()
        check_mermaid_label_chars(
            "",
            '<pre class="mermaid">graph TD\nA[标题，副标题] --> B</pre>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-39' in w]
        assert len(warns) == 1

    def test_chinese_quotes_warns(self) -> None:
        """中文左/右双引号 → WARN。"""
        from precheck_stage4 import check_mermaid_label_chars  # type: ignore
        r = Report()
        check_mermaid_label_chars(
            "",
            '<pre class="mermaid">graph TD\nA[label “quotes”] --> B</pre>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-39' in w]
        assert len(warns) == 1

    def test_no_mermaid_skipped(self) -> None:
        """无 mermaid 块 → 跳过。"""
        from precheck_stage4 import check_mermaid_label_chars  # type: ignore
        r = Report()
        check_mermaid_label_chars("", "<div>无 mermaid</div>", r)
        assert [w for w in r.warnings if 'S4-39' in w] == []


class TestS440InteractionCardNoInlineFont:
    """覆盖 check_interaction_card_no_inline_font — S4-40 / SSOT #62 E.3 第 1 条
    .interaction-card 内禁 inline 字号覆盖（WARN）。"""

    def test_no_inline_font_ok(self) -> None:
        """.interaction-card 内无 inline font-size → OK。"""
        from precheck_stage4 import check_interaction_card_no_inline_font  # type: ignore
        r = Report()
        check_interaction_card_no_inline_font(
            '<div class="interaction-card"><div class="card-title">A</div><table><tr><td>x</td></tr></table></div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-40' in w] == []

    def test_inline_font_on_card_title_warns(self) -> None:
        """.card-title style="font-size:..." → WARN。"""
        from precheck_stage4 import check_interaction_card_no_inline_font  # type: ignore
        r = Report()
        check_interaction_card_no_inline_font(
            '<div class="interaction-card"><div class="card-title" style="font-size:16px">A</div></div>',
            r,
        )
        assert len([w for w in r.warnings if 'S4-40' in w]) == 1

    def test_inline_font_on_table_warns(self) -> None:
        """.interaction-card 内 <table style="font-size:..."> → WARN。"""
        from precheck_stage4 import check_interaction_card_no_inline_font  # type: ignore
        r = Report()
        check_interaction_card_no_inline_font(
            '<div class="interaction-card"><table style="font-size: 14px"><tr><td>x</td></tr></table></div>',
            r,
        )
        assert len([w for w in r.warnings if 'S4-40' in w]) == 1

    def test_inline_font_on_th_td_warns(self) -> None:
        """.interaction-card 内 <th> / <td> style font-size → WARN（多处聚合）。"""
        from precheck_stage4 import check_interaction_card_no_inline_font  # type: ignore
        r = Report()
        check_interaction_card_no_inline_font(
            '<div class="interaction-card"><table>'
            '<tr><th style="font-size:11px">h</th></tr>'
            '<tr><td style="font-size: 10px">v</td></tr>'
            '</table></div>',
            r,
        )
        # 单条 WARN 内聚合多个违规
        warns = [w for w in r.warnings if 'S4-40' in w]
        assert len(warns) == 1
        assert '2 处' in warns[0]

    def test_inline_font_outside_card_ok(self) -> None:
        """.interaction-card 外的 inline font-size → 不命中（如 cover-page / changelog）。"""
        from precheck_stage4 import check_interaction_card_no_inline_font  # type: ignore
        r = Report()
        check_interaction_card_no_inline_font(
            '<p style="font-size:12px">cover description</p>'
            '<div class="changelog"><table><tr><td style="font-size:13px">x</td></tr></table></div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-40' in w] == []

    def test_no_interaction_card_skipped(self) -> None:
        """全文无 .interaction-card → OK。"""
        from precheck_stage4 import check_interaction_card_no_inline_font  # type: ignore
        r = Report()
        check_interaction_card_no_inline_font(
            '<div><p style="font-size:14px">irrelevant</p></div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-40' in w] == []

    def test_uppercase_font_size_warns(self) -> None:
        """大写 FONT-SIZE 也命中（case-insensitive）。"""
        from precheck_stage4 import check_interaction_card_no_inline_font  # type: ignore
        r = Report()
        check_interaction_card_no_inline_font(
            '<div class="interaction-card"><div style="FONT-SIZE: 14px">x</div></div>',
            r,
        )
        assert len([w for w in r.warnings if 'S4-40' in w]) == 1

    def test_nested_interaction_cards_ok(self) -> None:
        """嵌套 .interaction-card（罕见但允许）— 进出深度计数正确。"""
        from precheck_stage4 import check_interaction_card_no_inline_font  # type: ignore
        r = Report()
        check_interaction_card_no_inline_font(
            '<div class="interaction-card">'
            '  <div class="interaction-card"><div style="font-size:9px">inner</div></div>'
            '  <div>outer end</div>'
            '</div>',
            r,
        )
        # 内层 inline font 应被捕获
        assert len([w for w in r.warnings if 'S4-40' in w]) == 1


class TestS441InteractionCardClassCompliance:
    """覆盖 check_interaction_card_class_compliance — S4-41 / SSOT #62 E.3 第 2 条
    典型交互说明字面必须在 .interaction-card 内（防自造结构 WARN）。"""

    def test_signal_phrase_inside_card_ok(self) -> None:
        """.interaction-card 内含信号字面「交互说明 —」/「触点交互说明」→ OK。"""
        from precheck_stage4 import check_interaction_card_class_compliance  # type: ignore
        r = Report()
        check_interaction_card_class_compliance(
            '<div class="interaction-card">'
            '<div class="card-title">交互说明 — 默认态</div>'
            '<div class="data-sub-title">触点交互说明</div>'
            '<table><tr><td>x</td></tr></table>'
            '</div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-41' in w] == []

    def test_self_made_h3_title_warns(self) -> None:
        """直接 <h3>交互说明 — A</h3> 不在 .interaction-card 内 → WARN。"""
        from precheck_stage4 import check_interaction_card_class_compliance  # type: ignore
        r = Report()
        check_interaction_card_class_compliance(
            '<h3>交互说明 — 默认态</h3><p>some text</p>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-41' in w]
        assert len(warns) == 1

    def test_self_made_div_warns_multiple(self) -> None:
        """<div class="my-custom"> 含多个信号字面 → 多处 WARN（单条聚合）。"""
        from precheck_stage4 import check_interaction_card_class_compliance  # type: ignore
        r = Report()
        check_interaction_card_class_compliance(
            '<div class="my-custom">'
            '<h4>交互说明 — 默认态</h4>'
            '<p>状态差异说明：本帧为初始态</p>'
            '<p>列表回显说明：5 列</p>'
            '<p>触点交互说明：3 个触点</p>'
            '</div>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-41' in w]
        assert len(warns) == 1
        assert '4 处' in warns[0]

    def test_signal_in_pre_block_ok(self) -> None:
        """pre 块内含信号字面 → OK（豁免代码块/示例引用）。"""
        from precheck_stage4 import check_interaction_card_class_compliance  # type: ignore
        r = Report()
        check_interaction_card_class_compliance(
            '<pre>示例：&lt;div class="card-title"&gt;交互说明 — 默认态&lt;/div&gt;</pre>',
            r,
        )
        assert [w for w in r.warnings if 'S4-41' in w] == []

    def test_signal_in_code_block_ok(self) -> None:
        """code 块内含信号字面 → OK。"""
        from precheck_stage4 import check_interaction_card_class_compliance  # type: ignore
        r = Report()
        check_interaction_card_class_compliance(
            '<p>使用 <code>触点交互说明</code> 作为 sub-title</p>',
            r,
        )
        assert [w for w in r.warnings if 'S4-41' in w] == []

    def test_changelog_modify_safe_ok(self) -> None:
        """changelog 表「修改交互说明」（无 em-dash）→ OK，字面不命中。"""
        from precheck_stage4 import check_interaction_card_class_compliance  # type: ignore
        r = Report()
        check_interaction_card_class_compliance(
            '<table class="proto-changelog-table">'
            '<tr><td>M01-P01</td><td>修改交互说明文案</td></tr>'
            '</table>',
            r,
        )
        assert [w for w in r.warnings if 'S4-41' in w] == []

    def test_no_signal_skipped(self) -> None:
        """全文无信号字面 → OK。"""
        from precheck_stage4 import check_interaction_card_class_compliance  # type: ignore
        r = Report()
        check_interaction_card_class_compliance(
            '<div>普通业务文本</div><p>无关说明</p>',
            r,
        )
        assert [w for w in r.warnings if 'S4-41' in w] == []

    def test_nested_div_outside_card_warns(self) -> None:
        """多层 div 嵌套但都不是 .interaction-card → WARN。"""
        from precheck_stage4 import check_interaction_card_class_compliance  # type: ignore
        r = Report()
        check_interaction_card_class_compliance(
            '<div><div><div class="not-card">触点交互说明：3 个触点</div></div></div>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-41' in w]
        assert len(warns) == 1


class TestS442SkeletonInlinePadding:
    """覆盖 check_skeleton_inline_padding — S4-42 / SSOT #63 Skeleton tokens
    .fb-state-loading 内禁 inline padding 覆盖（WARN）。"""

    def test_no_inline_padding_ok(self) -> None:
        """.fb-state-loading 元素无 inline padding → OK（由模板 :root + 平台 selector 自动应用）。"""
        from precheck_stage4 import check_skeleton_inline_padding  # type: ignore
        r = Report()
        check_skeleton_inline_padding(
            '<div class="fb-state fb-state-loading"><div class="skel-row"></div></div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-42' in w] == []

    def test_inline_padding_warns(self) -> None:
        """.fb-state-loading 含 inline padding → WARN。"""
        from precheck_stage4 import check_skeleton_inline_padding  # type: ignore
        r = Report()
        check_skeleton_inline_padding(
            '<div class="fb-state-loading" style="padding:24px 0">...</div>',
            r,
        )
        assert len([w for w in r.warnings if 'S4-42' in w]) == 1

    def test_multi_class_inline_padding_warns(self) -> None:
        """多 class 写法 class="fb-state fb-state-loading" 含 inline padding → WARN。"""
        from precheck_stage4 import check_skeleton_inline_padding  # type: ignore
        r = Report()
        check_skeleton_inline_padding(
            '<div class="fb-state fb-state-loading" style="padding: 8px 0; text-align:center;">...</div>',
            r,
        )
        assert len([w for w in r.warnings if 'S4-42' in w]) == 1

    def test_multiple_violations_aggregated(self) -> None:
        """多处 inline padding 违规 → 单条 WARN 聚合（含'共 N 处'字面）。"""
        from precheck_stage4 import check_skeleton_inline_padding  # type: ignore
        r = Report()
        check_skeleton_inline_padding(
            '<div class="fb-state-loading" style="padding:24px 0">a</div>'
            '<div class="fb-state-loading" style="padding:60px 20px">b</div>'
            '<div class="fb-state-loading" style="padding:96px 32px">c</div>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-42' in w]
        assert len(warns) == 1
        assert '3 处' in warns[0]

    def test_other_inline_style_ok(self) -> None:
        """.fb-state-loading 含其他 inline style（非 padding）→ OK（不命中）。"""
        from precheck_stage4 import check_skeleton_inline_padding  # type: ignore
        r = Report()
        check_skeleton_inline_padding(
            '<div class="fb-state-loading" style="text-align:center; background:#f5f5f5">...</div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-42' in w] == []

    def test_non_skeleton_inline_padding_ok(self) -> None:
        """非 .fb-state-loading 元素的 inline padding → OK（不命中 S4-42 域）。"""
        from precheck_stage4 import check_skeleton_inline_padding  # type: ignore
        r = Report()
        check_skeleton_inline_padding(
            '<div class="cover-page" style="padding:80px 40px">cover</div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-42' in w] == []


class TestS443DataTpContainerUniqueness:
    """覆盖 check_prd_data_tp_container_uniqueness — S4-43 / SSOT #64
    data-tp 容器级唯一性纪律（WARN dry-run）。"""

    def test_unique_data_tp_ok(self) -> None:
        """同 frame 内 data-tp 各唯一 → OK。"""
        from precheck_stage4 import check_prd_data_tp_container_uniqueness  # type: ignore
        r = Report()
        check_prd_data_tp_container_uniqueness(
            '<div class="desktop-frame">'
            '<div data-tp="M01-P01-T01">a</div>'
            '<div data-tp="M01-P01-T02">b</div>'
            '</div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-43' in w] == []

    def test_chip_group_duplicate_warns(self) -> None:
        """chip group 3 选项标同 data-tp 3 次 → WARN（反 pattern 治本）。"""
        from precheck_stage4 import check_prd_data_tp_container_uniqueness  # type: ignore
        r = Report()
        check_prd_data_tp_container_uniqueness(
            '<div class="desktop-frame">'
            '<div class="chip-group">'
            '<button class="chip" data-tp="M01-P01-T03">全部</button>'
            '<button class="chip" data-tp="M01-P01-T03">进行中</button>'
            '<button class="chip" data-tp="M01-P01-T03">已完成</button>'
            '</div>'
            '</div>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-43' in w]
        assert len(warns) == 1
        assert 'M01-P01-T03' in warns[0]
        assert '3 次' in warns[0]

    def test_list_multi_instance_warns_for_human_review(self) -> None:
        """list 3 行同 data-tp（合规多实例）也 WARN，由 PM/Sup 看上下文人审豁免（dry-run）。"""
        from precheck_stage4 import check_prd_data_tp_container_uniqueness  # type: ignore
        r = Report()
        check_prd_data_tp_container_uniqueness(
            '<div class="desktop-frame">'
            '<ul class="fb-list">'
            '<li class="project-row" data-tp="M01-P01-C05">项目 A</li>'
            '<li class="project-row" data-tp="M01-P01-C05">项目 B</li>'
            '<li class="project-row" data-tp="M01-P01-C05">项目 C</li>'
            '</ul>'
            '</div>',
            r,
        )
        # dry-run 阶段：list 多实例也 WARN，让 PM/Sup 看上下文人审
        warns = [w for w in r.warnings if 'S4-43' in w]
        assert len(warns) == 1

    def test_cross_frame_same_id_ok(self) -> None:
        """同 data-tp 跨不同 frame 各出现 1 次 → OK（容器级唯一性是 per-frame 范围）。"""
        from precheck_stage4 import check_prd_data_tp_container_uniqueness  # type: ignore
        r = Report()
        check_prd_data_tp_container_uniqueness(
            '<div class="desktop-frame"><div data-tp="M01-P01-T01">a</div></div>'
            '<div class="phone-frame"><div data-tp="M01-P01-T01">a</div></div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-43' in w] == []

    def test_no_frame_skipped(self) -> None:
        """无 *-frame → OK（无范围统计）。"""
        from precheck_stage4 import check_prd_data_tp_container_uniqueness  # type: ignore
        r = Report()
        check_prd_data_tp_container_uniqueness(
            '<div><div data-tp="M01-P01-T01">a</div><div data-tp="M01-P01-T01">b</div></div>',
            r,
        )
        assert [w for w in r.warnings if 'S4-43' in w] == []

    def test_multiple_violations_aggregated(self) -> None:
        """多个 data-tp ID 重复 → 多条 WARN 聚合（含 ID + 次数 + 行号）。"""
        from precheck_stage4 import check_prd_data_tp_container_uniqueness  # type: ignore
        r = Report()
        check_prd_data_tp_container_uniqueness(
            '<div class="desktop-frame">'
            '<button data-tp="M01-P01-T03">a</button>'
            '<button data-tp="M01-P01-T03">b</button>'
            '<button data-tp="M01-P01-T04">c</button>'
            '<button data-tp="M01-P01-T04">d</button>'
            '</div>',
            r,
        )
        warns = [w for w in r.warnings if 'S4-43' in w]
        assert len(warns) == 1
        # 单条 WARN 内聚合 2 个违规 ID（T03 + T04）
        assert 'M01-P01-T03' in warns[0]
        assert 'M01-P01-T04' in warns[0]


# ── SSOT #66 spec.md SSOT 输入 schema 严格化测试 ──────────────────────────────
# 5 个 check_* 函数（S4-44 ~ S4-48）的 pytest 用例


def _spec_with_full_module(mid: str = "M01", num_pages: int = 1) -> str:
    """构造 SSOT #61 v2.0 完整模块的 spec.md 片段（7 必填 .1~.7 + 可选 .6/.8）。"""
    return f"""## S2.{mid} 模块概述
[业务定位 / 关键路由]

## S2.{mid}.1 页面概述
[逐页]

## S2.{mid}.2 状态枚举
| 页面 | 状态名 | 触发条件 |
|------|--------|----------|
| P01 | default | 用户进入 |

## S2.{mid}.2A 元素交互细则
| 元素 | 组件类型 | 默认态 |
|------|----------|--------|

## S2.{mid}.3 触点表
| 触点 ID | 所在状态 | 元素 |
|---------|----------|------|

## S2.{mid}.3A 本模块页面跳转表
| 触发操作 | 跳转目标 |
|----------|----------|

## S2.{mid}.4 数据字段绑定
| 字段名 | 类型 |
|--------|------|

## S2.{mid}.5 跨模块跳转引用
- 依赖 M02

## S2.{mid}.6 API 摘要（详 产品定义 §10）
| API 编号 | 端点摘要 |
|----------|----------|

## S2.{mid}.7 状态清单与验收标准（Gherkin）
**P01-default**
- 互斥说明：与 loading 互斥
- 触发条件：进入
- 页面表现：详 .2
- 验收标准：
  ```gherkin
  Given 已登录
  When  进入页面
  Then  渲染 default
  ```

## S2.{mid}.8 本页新增组件
| 组件 ID | 组件名 |
|---------|--------|
"""


class TestS444SpecModuleSubsectionsCompleteness:
    """SSOT #66 / S4-44 — spec 模块子块完整度（WARN）。"""

    def _data(self) -> dict:
        return {"modules": [{"id": "M01"}]}

    def test_pass_full_required_subsections(self) -> None:
        from precheck_stage4 import check_spec_module_subsections_completeness  # type: ignore
        spec = _spec_with_full_module("M01")
        r = Report()
        check_spec_module_subsections_completeness(self._data(), spec, r)
        assert r.warnings == []
        assert r.passed >= 1

    def test_warn_missing_required(self) -> None:
        from precheck_stage4 import check_spec_module_subsections_completeness  # type: ignore
        # 缺 .2A + .3A 两个必填子块
        spec = """## S2.M01 模块概述
## S2.M01.1 页面概述
## S2.M01.2 状态枚举
## S2.M01.3 触点表
## S2.M01.4 数据字段绑定
## S2.M01.5 跨模块跳转引用
## S2.M01.7 状态清单
"""
        r = Report()
        check_spec_module_subsections_completeness(self._data(), spec, r)
        warns = [w for w in r.warnings if '.2A' in w or '.3A' in w]
        assert len(warns) == 1, f"应单条 WARN 聚合, got {r.warnings}"
        assert 'M01' in warns[0]

    def test_skip_legacy_spec_no_modules(self) -> None:
        """启发式豁免：spec 顶层无 S2.MXX 段头（旧版 spec）→ skip。"""
        from precheck_stage4 import check_spec_module_subsections_completeness  # type: ignore
        spec = "## §三 页面流转总图\n## §四 文档尾部\n"
        r = Report()
        check_spec_module_subsections_completeness(self._data(), spec, r)
        assert r.warnings == []
        assert any('旧版' in m for m in [str(s) for s in [r.passed]] + r.warnings) or r.passed >= 1

    def test_multiple_modules_partial_missing(self) -> None:
        from precheck_stage4 import check_spec_module_subsections_completeness  # type: ignore
        spec = _spec_with_full_module("M01") + _spec_with_full_module("M02").replace(
            "## S2.M02.7 状态清单与验收标准（Gherkin）", "## S2.M02.7-XXX 异写"
        )
        r = Report()
        check_spec_module_subsections_completeness({"modules": [{"id": "M01"}, {"id": "M02"}]}, spec, r)
        warns = [w for w in r.warnings if 'M02' in w]
        assert len(warns) == 1


class TestS445SpecGherkinCompleteness:
    """SSOT #66 / S4-45 — Gherkin 完整度（WARN）。"""

    def _data(self) -> dict:
        return {"modules": [{"id": "M01"}]}

    def test_pass_full_gherkin(self) -> None:
        from precheck_stage4 import check_spec_gherkin_completeness  # type: ignore
        spec = _spec_with_full_module("M01")
        r = Report()
        check_spec_gherkin_completeness(self._data(), spec, r)
        assert r.warnings == []

    def test_warn_missing_sub_items(self) -> None:
        from precheck_stage4 import check_spec_gherkin_completeness  # type: ignore
        # 4 子项缺 2（缺互斥说明 + 触发条件）
        spec = """## S2.M01.7 状态清单
**P01-default**
- 页面表现：详 .2
- 验收标准：
  ```gherkin
  Given 已登录
  When  进入
  Then  渲染
  ```
"""
        r = Report()
        check_spec_gherkin_completeness(self._data(), spec, r)
        assert len(r.warnings) == 1
        assert '互斥说明' in r.warnings[0]
        assert '触发条件' in r.warnings[0]

    def test_warn_missing_gherkin_keywords(self) -> None:
        from precheck_stage4 import check_spec_gherkin_completeness  # type: ignore
        # Gherkin 围栏内缺 When + Then
        spec = """## S2.M01.7 状态清单
**P01-default**
- 互斥说明：x
- 触发条件：x
- 页面表现：x
- 验收标准：
  ```gherkin
  Given 已登录
  ```
"""
        r = Report()
        check_spec_gherkin_completeness(self._data(), spec, r)
        assert len(r.warnings) == 1
        assert 'When' in r.warnings[0] and 'Then' in r.warnings[0]

    def test_new_format_S_colon_anchor(self) -> None:
        """私域格式 **S01：default(xx)** 应被正常匹配（SSOT #61 升级后）。"""
        from precheck_stage4 import check_spec_gherkin_completeness  # type: ignore
        spec = """## S2.M01.7 状态清单

### P01 主页设置首页

**S01：default（has_active_package=true）**
- 互斥说明：x
- 触发条件：x
- 页面表现：x
- 验收标准：
  ```gherkin
  Given x
  When  y
  Then  z
  ```
"""
        r = Report()
        check_spec_gherkin_completeness(self._data(), spec, r)
        assert r.warnings == []

    def test_skip_no_s7_section(self) -> None:
        from precheck_stage4 import check_spec_gherkin_completeness  # type: ignore
        spec = "## §三 页面流转总图\n"
        r = Report()
        check_spec_gherkin_completeness(self._data(), spec, r)
        assert r.warnings == []


class TestS446SpecApiIdClosure:
    """SSOT #66 / S4-46 — API ID 引用闭环（WARN）。"""

    def test_skip_no_product_def(self, monkeypatch, tmp_path) -> None:
        """产品定义文件不存在 → WARN 启发式跳过。"""
        from precheck_stage4 import check_spec_api_id_closure  # type: ignore
        monkeypatch.setattr(_stage4_mod, 'OUTPUT_DIR', tmp_path)
        spec = "本段引用 API-001 / API-002"
        r = Report()
        check_spec_api_id_closure({"product": "测试产品"}, spec, r)
        # 产品定义不存在 → WARN 跳过
        assert any('启发式豁免' in w or '跳过' in w for w in r.warnings)

    def test_pass_closure(self, monkeypatch, tmp_path) -> None:
        from precheck_stage4 import check_spec_api_id_closure  # type: ignore
        monkeypatch.setattr(_stage4_mod, 'OUTPUT_DIR', tmp_path)
        (tmp_path / "产品定义_X_latest.md").write_text(
            "API-001 / API-002\n## §10 API 列表\nAPI-001 / API-002\n"
        )
        spec = "引 API-001 + API-002"
        r = Report()
        check_spec_api_id_closure({"product": "X"}, spec, r)
        assert [w for w in r.warnings if 'API' in w] == []

    def test_warn_unclosed(self, monkeypatch, tmp_path) -> None:
        from precheck_stage4 import check_spec_api_id_closure  # type: ignore
        monkeypatch.setattr(_stage4_mod, 'OUTPUT_DIR', tmp_path)
        (tmp_path / "产品定义_X_latest.md").write_text("API-001\n")
        spec = "引 API-001 + API-002 + API-003"
        r = Report()
        check_spec_api_id_closure({"product": "X"}, spec, r)
        assert len(r.warnings) == 1
        assert 'API-002' in r.warnings[0]
        assert 'API-003' in r.warnings[0]


class TestS447SpecNbIdClosure:
    """SSOT #66 / S4-47 — NB ID 引用闭环（WARN）。"""

    def test_pass_no_nb(self, monkeypatch, tmp_path) -> None:
        from precheck_stage4 import check_spec_nb_id_closure  # type: ignore
        monkeypatch.setattr(_stage4_mod, 'OUTPUT_DIR', tmp_path)
        r = Report()
        check_spec_nb_id_closure({"product": "X"}, "无 NB 引用", r)
        assert r.warnings == []

    def test_l2_nb_prefixes_exempt(self, monkeypatch, tmp_path) -> None:
        from precheck_stage4 import check_spec_nb_id_closure  # type: ignore
        monkeypatch.setattr(_stage4_mod, 'OUTPUT_DIR', tmp_path)
        r = Report()
        spec = "引 NB-WE-13, NB-LIT-25-B, NB-SSOT61-01, NB-SNB-009"
        check_spec_nb_id_closure({"product": "X"}, spec, r)
        # 全部 L2 NB 启发式豁免
        assert [w for w in r.warnings if '未在' in w] == []

    def test_pass_in_scaffold_notes(self, monkeypatch, tmp_path) -> None:
        from precheck_stage4 import check_spec_nb_id_closure  # type: ignore
        monkeypatch.setattr(_stage4_mod, 'OUTPUT_DIR', tmp_path)
        r = Report()
        data = {
            "product": "X",
            "notes": [{"id": "NB-001"}, "NB-002 决策细节"],
        }
        check_spec_nb_id_closure(data, "引 NB-001 + NB-002", r)
        assert [w for w in r.warnings if '未在' in w] == []

    def test_warn_unclosed(self, monkeypatch, tmp_path) -> None:
        from precheck_stage4 import check_spec_nb_id_closure  # type: ignore
        monkeypatch.setattr(_stage4_mod, 'OUTPUT_DIR', tmp_path)
        r = Report()
        check_spec_nb_id_closure({"product": "X"}, "引 NB-999 + NB-888", r)
        assert len(r.warnings) == 1
        assert 'NB-999' in r.warnings[0] or 'NB-888' in r.warnings[0]


class TestS448SpecSectionNumberingConsistency:
    """SSOT #66 / S4-48 — 模块编号连续性 + 子段层级父子约束（WARN）。"""

    def _data(self) -> dict:
        return {"modules": [{"id": "M01"}]}

    def test_skip_no_modules(self) -> None:
        from precheck_stage4 import check_spec_section_numbering_consistency  # type: ignore
        r = Report()
        check_spec_section_numbering_consistency(self._data(), "## §三 旧版\n", r)
        assert r.warnings == []

    def test_pass_continuous(self) -> None:
        from precheck_stage4 import check_spec_section_numbering_consistency  # type: ignore
        spec = """## S2.M01 模块概述
## S2.M01.2 状态枚举
## S2.M01.2A 元素交互细则
## S2.M02 模块概述
## S2.M02.3 触点表
## S2.M02.3A 跳转表
## S2.M03 模块概述
"""
        r = Report()
        check_spec_section_numbering_consistency(self._data(), spec, r)
        assert r.warnings == []

    def test_warn_skip_module(self) -> None:
        from precheck_stage4 import check_spec_section_numbering_consistency  # type: ignore
        spec = """## S2.M01 模块概述
## S2.M03 模块概述
## S2.M05 模块概述
"""
        r = Report()
        check_spec_section_numbering_consistency(self._data(), spec, r)
        warns = [w for w in r.warnings if '不连续' in w]
        assert len(warns) == 1
        assert 'M02' in warns[0] and 'M04' in warns[0]

    def test_warn_orphan_2A(self) -> None:
        from precheck_stage4 import check_spec_section_numbering_consistency  # type: ignore
        # 有 .2A 但无父 .2
        spec = """## S2.M01 模块概述
## S2.M01.1 页面概述
## S2.M01.2A 元素交互细则
"""
        r = Report()
        check_spec_section_numbering_consistency(self._data(), spec, r)
        warns = [w for w in r.warnings if '无父' in w]
        assert len(warns) == 1
        assert 'M01.2A' in warns[0]


# ── SSOT #67/#68/#69 spec/prd 派生层 + interaction-card schema 12 用例（S4-49~60）────


def _spec_with_4B_5B(mid: str = "M01") -> str:
    """构造 SSOT #68 .4B/.5B 段头齐全的 spec 片段。"""
    return f"""## S2.{mid} 模块概述
[业务定位]

## S2.{mid}.4B 业务规则（SSOT #68）
#### P01 列表页
- 单用户最多保存 50 条
- 列表分页每页 ≤ 20 条

## S2.{mid}.5B 数据规模（SSOT #68）
#### P01 列表页
- 单用户数据量：50
- 单次返回量：20
- 操作频率：日均 5 次
"""


def _spec_with_f_section(
    fid: str = "F-001", name: str = "示例功能",
    priority: str = "P0", journey: str = "旅程一",
    involved: str = "P-01, P-02", main: str = "P-01"
) -> str:
    """构造 F-xxx 节标准格式（4 必填字段）。"""
    parts = []
    if priority:
        parts.append(f"**优先级**：{priority}")
    if journey:
        parts.append(f"**所属旅程**：{journey}")
    if involved:
        parts.append(f"**涉及页面**：{involved}")
    if main:
        parts.append(f"**主页面**：{main}")
    meta = "　｜　".join(parts)
    return f"""#### {fid}：{name}

{meta}

**交互说明**

| 元素 | 默认态 |
|------|--------|
"""


class TestS449SpecSection4BBusinessRules:
    """SSOT #68 / S4-49 — .4B 业务规则段头存在 + 非空（WARN）。"""

    def _data(self) -> dict:
        return {"modules": [{"id": "M01"}]}

    def test_skip_legacy_no_modules(self) -> None:
        from precheck_stage4 import check_spec_section_4B_business_rules  # type: ignore
        r = Report()
        check_spec_section_4B_business_rules(self._data(), "## §三 旧版\n", r)
        assert r.warnings == []

    def test_pass_with_4B(self) -> None:
        from precheck_stage4 import check_spec_section_4B_business_rules  # type: ignore
        r = Report()
        check_spec_section_4B_business_rules(self._data(), _spec_with_4B_5B("M01"), r)
        assert r.warnings == []
        assert r.passed >= 1

    def test_warn_missing_4B(self) -> None:
        from precheck_stage4 import check_spec_section_4B_business_rules  # type: ignore
        spec = "## S2.M01 模块概述\n[业务定位]\n## S2.M01.1 页面概述\n"
        r = Report()
        check_spec_section_4B_business_rules(self._data(), spec, r)
        assert len(r.warnings) == 1
        assert "M01" in r.warnings[0]


class TestS450SpecSection5BDataScale:
    """SSOT #68 / S4-50 — .5B 数据规模段头存在 + 非空（WARN）。"""

    def _data(self) -> dict:
        return {"modules": [{"id": "M01"}]}

    def test_skip_legacy(self) -> None:
        from precheck_stage4 import check_spec_section_5B_data_scale  # type: ignore
        r = Report()
        check_spec_section_5B_data_scale(self._data(), "## §三 旧版\n", r)
        assert r.warnings == []

    def test_pass_with_5B(self) -> None:
        from precheck_stage4 import check_spec_section_5B_data_scale  # type: ignore
        r = Report()
        check_spec_section_5B_data_scale(self._data(), _spec_with_4B_5B("M01"), r)
        assert r.warnings == []

    def test_warn_missing_5B(self) -> None:
        from precheck_stage4 import check_spec_section_5B_data_scale  # type: ignore
        spec = "## S2.M01 模块概述\n## S2.M01.4B 业务规则\n- x\n"
        r = Report()
        check_spec_section_5B_data_scale(self._data(), spec, r)
        assert len(r.warnings) == 1


class TestS451SpecFunctionMainPageField:
    """SSOT #68 / S4-51 — F-xxx 主页面字段存在 + ∈ 涉及页面（WARN）。"""

    def test_skip_no_f_sections(self) -> None:
        from precheck_stage4 import check_spec_function_main_page_field  # type: ignore
        r = Report()
        check_spec_function_main_page_field({}, "## §三 无 F\n", r)
        assert r.warnings == []

    def test_pass_main_in_involved(self) -> None:
        from precheck_stage4 import check_spec_function_main_page_field  # type: ignore
        r = Report()
        check_spec_function_main_page_field({}, _spec_with_f_section(
            involved="P-01, P-02", main="P-01"
        ), r)
        assert r.warnings == []

    def test_warn_missing_main(self) -> None:
        from precheck_stage4 import check_spec_function_main_page_field  # type: ignore
        r = Report()
        check_spec_function_main_page_field({}, _spec_with_f_section(main=""), r)
        # 缺主页面字段 → 1 条 WARN
        assert any("缺「主页面」" in w for w in r.warnings)

    def test_warn_main_not_in_involved(self) -> None:
        from precheck_stage4 import check_spec_function_main_page_field  # type: ignore
        r = Report()
        check_spec_function_main_page_field({}, _spec_with_f_section(
            involved="P-01, P-02", main="P-05"
        ), r)
        assert any("不在涉及页面集合" in w for w in r.warnings)


class TestS452SpecFunctionXxxRequired:
    """SSOT #68 / S4-52 — F-xxx 4 必填字段齐全（WARN）。"""

    def test_skip_no_f_sections(self) -> None:
        from precheck_stage4 import check_spec_function_xxx_required  # type: ignore
        r = Report()
        check_spec_function_xxx_required({}, "## §三 无 F\n", r)
        assert r.warnings == []

    def test_pass_4_fields(self) -> None:
        from precheck_stage4 import check_spec_function_xxx_required  # type: ignore
        r = Report()
        check_spec_function_xxx_required({}, _spec_with_f_section(), r)
        assert r.warnings == []

    def test_warn_missing_fields(self) -> None:
        from precheck_stage4 import check_spec_function_xxx_required  # type: ignore
        r = Report()
        check_spec_function_xxx_required({}, _spec_with_f_section(
            priority="P0", journey="", involved="", main=""
        ), r)
        assert len(r.warnings) == 1
        assert "所属旅程" in r.warnings[0]
        assert "涉及页面" in r.warnings[0]
        assert "主页面" in r.warnings[0]


class TestS453PrdC4DerivationClosure:
    """SSOT #68 / S4-53 — prd interaction-card C-4 派生闭环（WARN）。"""

    def test_skip_no_card(self) -> None:
        from precheck_stage4 import check_prd_c4_derivation_closure  # type: ignore
        r = Report()
        check_prd_c4_derivation_closure({}, "<html><body>无 card</body></html>",
                                         _spec_with_f_section(), r)
        assert r.warnings == []

    def test_skip_no_f_sections(self) -> None:
        from precheck_stage4 import check_prd_c4_derivation_closure  # type: ignore
        prd = '<div class="interaction-card"></div>'
        r = Report()
        check_prd_c4_derivation_closure({}, prd, "## §三 无 F\n", r)
        assert r.warnings == []

    def test_warn_zero_c4(self) -> None:
        from precheck_stage4 import check_prd_c4_derivation_closure  # type: ignore
        prd = '<div class="interaction-card"></div><div class="interaction-card"></div>'
        r = Report()
        check_prd_c4_derivation_closure({}, prd, _spec_with_f_section(), r)
        assert any("全部无 C-4" in w for w in r.warnings)

    def test_pass_full_c4(self) -> None:
        from precheck_stage4 import check_prd_c4_derivation_closure  # type: ignore
        prd = (
            '<div class="interaction-card">'
            '<!-- [C4-START] -->C-4 内容<!-- [C4-END] -->'
            '</div>'
            '<div class="interaction-card">'
            '<p class="c4-cross-page-note">跳转</p>'
            '</div>'
        )
        r = Report()
        check_prd_c4_derivation_closure({}, prd, _spec_with_f_section(), r)
        # 2 card / 2 C-4 痕迹 → 100% coverage 无 WARN
        assert r.warnings == []

    # NB-1 修复（2026-06-04）：兼容 assemble.py 当前注入的含参数形式
    # `<!-- [C4-START: prd_id] auto-injected by assemble.py -->...<!-- [C4-END: prd_id] -->`
    def test_pass_full_c4_new_param_form(self) -> None:
        """新形式（含参数 + auto-injected 备注）— assemble.py 当前实际注入。"""
        from precheck_stage4 import check_prd_c4_derivation_closure  # type: ignore
        prd = (
            '<div class="interaction-card">'
            '<!-- [C4-START: H-M01-P01-default] auto-injected by assemble.py -->'
            'C-4 内容'
            '<!-- [C4-END: H-M01-P01-default] -->'
            '</div>'
            '<div class="interaction-card">'
            '<!-- [C4-START: H-M02-P03-admin] auto-injected by assemble.py -->'
            'C-4 内容'
            '<!-- [C4-END: H-M02-P03-admin] -->'
            '</div>'
        )
        r = Report()
        check_prd_c4_derivation_closure({}, prd, _spec_with_f_section(), r)
        # 2 card / 2 C-4 (新形式) → 100% coverage 无 WARN
        assert r.warnings == []

    def test_pass_mixed_old_new_and_cross_page(self) -> None:
        """三种 C-4 形态混合：旧无参数 + 新含参数 + 副页面 cross-page-note。"""
        from precheck_stage4 import check_prd_c4_derivation_closure  # type: ignore
        prd = (
            # 主页面全量 — 新形式（含参数）
            '<div class="interaction-card">'
            '<!-- [C4-START: H-M01-P01-default] auto-injected by assemble.py -->'
            'C-4 主页面'
            '<!-- [C4-END: H-M01-P01-default] -->'
            '</div>'
            # 主页面全量 — 旧形式（向后兼容）
            '<div class="interaction-card">'
            '<!-- [C4-START] -->C-4 旧形式<!-- [C4-END] -->'
            '</div>'
            # 副页面缩略
            '<div class="interaction-card">'
            '<p class="c4-cross-page-note">跳转主页面</p>'
            '</div>'
        )
        r = Report()
        check_prd_c4_derivation_closure({}, prd, _spec_with_f_section(), r)
        # 3 card / 3 C-4 痕迹 → 100% coverage 无 WARN
        assert r.warnings == []


class TestS454PrdA05Removed:
    """SSOT #67 / S4-54 — A-05 章节已重组（WARN）。"""

    def test_skip_no_section(self) -> None:
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        r = Report()
        check_prd_a05_removed({}, "<html>无 section</html>", r)
        assert r.warnings == []

    def test_pass_index_form(self) -> None:
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        prd = (
            '<section id="spec-feature"><table>'
            '<thead><tr><th>编号</th><th>功能名</th>'
            '<th>优先级</th><th>主页面</th></tr></thead>'
            '</table></section>'
        )
        r = Report()
        check_prd_a05_removed({}, prd, r)
        assert r.warnings == []

    def test_warn_legacy_article(self) -> None:
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        prd = (
            '<section id="spec-feature">'
            '<div class="feature-block">'
            '<div class="feature-title">F-001 功能名</div>'
            '</div></section>'
        )
        r = Report()
        check_prd_a05_removed({}, prd, r)
        assert any("feature-block" in w for w in r.warnings)

    # 2026-06-04 P0 hot fix Bug 4：S4-54 覆盖度升级 — 2 维度新增测试
    def test_warn_sub_article_residual(self) -> None:
        """Bug 4 维度 2：spec-feature 内残留 `<article id="spec-F[0-9]+">` → WARN。"""
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        prd = (
            '<section id="spec-feature">'
            '<article id="spec-F002">残留 F-002</article>'
            '<article id="spec-F003">残留 F-003</article>'
            '</section>'
        )
        r = Report()
        check_prd_a05_removed({}, prd, r)
        assert any("sub-article 残留" in w for w in r.warnings)
        assert any("2 处" in w for w in r.warnings)

    def test_warn_old_header_label(self) -> None:
        """Bug 4 维度 3：spec-header 字面仍为「功能需求规格」（应为「功能索引」）→ WARN。"""
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        prd = (
            '<section id="spec-feature">'
            '<div class="spec-header">功能需求规格</div>'
            '</section>'
        )
        r = Report()
        check_prd_a05_removed({}, prd, r)
        assert any("功能需求规格" in w for w in r.warnings)

    def test_warn_3_dimensions_combined(self) -> None:
        """Bug 4 联动：3 维度同时违规 → 单 WARN 含全部 3 项分号串接。"""
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        prd = (
            '<section id="spec-feature">'
            '<div class="spec-header">功能需求规格</div>'
            '<div class="feature-block"><p>old</p></div>'
            '<article id="spec-F001">res</article>'
            '</section>'
        )
        r = Report()
        check_prd_a05_removed({}, prd, r)
        # 1 个 WARN，含 3 个分号串接（3 维度）
        assert len(r.warnings) == 1
        warn = r.warnings[0]
        assert "feature-block" in warn
        assert "sub-article" in warn
        assert "功能需求规格" in warn

    def test_pass_index_form_new_header(self) -> None:
        """重组完成形态：新 header「功能索引」+ 4 列表头 + 无 sub-article → PASS。"""
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        prd = (
            '<section id="spec-feature">'
            '<div class="spec-header">功能索引</div>'
            '<table>'
            '<thead><tr><th>编号</th><th>功能名</th>'
            '<th>优先级</th><th>主页面</th></tr></thead>'
            '</table></section>'
        )
        r = Report()
        check_prd_a05_removed({}, prd, r)
        assert r.warnings == []
        assert r.passed >= 1

    # 议题 7 / NB-WE-2A-R2-02 P1：维度 4 sidebar nav 旧字面（2026-06-04）
    def test_warn_sidebar_old_label(self) -> None:
        """维度 4：sidebar nav `data-target="spec-feature"` 含旧字面「功能需求规格」→ WARN。"""
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        prd = (
            '<section id="spec-feature">'
            '<div class="spec-header">功能索引</div>'  # section 内已治本
            '</section>'
            '<nav class="sidebar">'
            '<div class="sidebar-spec-item" data-target="spec-feature" '
            'onclick="showSection(\'spec-feature\')">功能需求规格</div>'
            '</nav>'
        )
        r = Report()
        check_prd_a05_removed({}, prd, r)
        assert any("sidebar" in w and "功能需求规格" in w for w in r.warnings)

    def test_pass_sidebar_new_label(self) -> None:
        """维度 4：sidebar nav 已是「功能索引」→ PASS。"""
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        prd = (
            '<section id="spec-feature">'
            '<div class="spec-header">功能索引</div>'
            '<table>'
            '<thead><tr><th>编号</th><th>功能名</th>'
            '<th>优先级</th><th>主页面</th></tr></thead>'
            '</table></section>'
            '<nav class="sidebar">'
            '<div class="sidebar-spec-item" data-target="spec-feature">功能索引</div>'
            '</nav>'
        )
        r = Report()
        check_prd_a05_removed({}, prd, r)
        assert r.warnings == []

    def test_sidebar_only_no_section(self) -> None:
        """边界：prd 无 spec-feature section 但 sidebar 仍含旧字面 → 仍 WARN（维度 4 独立判定）"""
        from precheck_stage4 import check_prd_a05_removed  # type: ignore
        prd = (
            '<nav class="sidebar">'
            '<div class="sidebar-spec-item" data-target="spec-feature">功能需求规格</div>'
            '</nav>'
        )
        r = Report()
        check_prd_a05_removed({}, prd, r)
        assert any("sidebar" in w for w in r.warnings)


class TestS455PrdAIndexComplete:
    """SSOT #67 / S4-55 — A-索引 4 列 + 行数对齐（WARN）。"""

    def test_skip_no_section(self) -> None:
        from precheck_stage4 import check_prd_a_index_complete  # type: ignore
        r = Report()
        check_prd_a_index_complete({}, "<html></html>", _spec_with_f_section(), r)
        assert r.warnings == []

    def test_skip_no_f(self) -> None:
        from precheck_stage4 import check_prd_a_index_complete  # type: ignore
        prd = '<section id="spec-feature"></section>'
        r = Report()
        check_prd_a_index_complete({}, prd, "## §三 无 F\n", r)
        assert r.warnings == []

    def test_warn_missing_4col_thead(self) -> None:
        from precheck_stage4 import check_prd_a_index_complete  # type: ignore
        prd = (
            '<section id="spec-feature"><table>'
            '<thead><tr><th>编号</th><th>功能名</th></tr></thead>'
            '<tbody><tr><td>F-001</td><td>x</td></tr></tbody>'
            '</table></section>'
        )
        r = Report()
        check_prd_a_index_complete({}, prd, _spec_with_f_section(), r)
        assert any("4 列" in w or "缺 4 列" in w for w in r.warnings)

    def test_pass_4col_and_aligned(self) -> None:
        from precheck_stage4 import check_prd_a_index_complete  # type: ignore
        prd = (
            '<section id="spec-feature"><table>'
            '<thead><tr><th>编号</th><th>功能名</th>'
            '<th>优先级</th><th>主页面</th></tr></thead>'
            '<tbody><tr><td>F-001</td><td>x</td><td>P0</td><td>P-01</td></tr></tbody>'
            '</table></section>'
        )
        spec_one_f = _spec_with_f_section()
        r = Report()
        check_prd_a_index_complete({}, prd, spec_one_f, r)
        assert r.warnings == []

    def test_warn_row_count_mismatch(self) -> None:
        from precheck_stage4 import check_prd_a_index_complete  # type: ignore
        prd = (
            '<section id="spec-feature"><table>'
            '<thead><tr><th>编号</th><th>功能名</th>'
            '<th>优先级</th><th>主页面</th></tr></thead>'
            '<tbody><tr><td>F-001</td><td>x</td><td>P0</td><td>P-01</td></tr></tbody>'
            '</table></section>'
        )
        # spec 含 2 F-xxx,prd 仅 1 行 → mismatch
        spec_two_f = (
            _spec_with_f_section(fid="F-001") +
            _spec_with_f_section(fid="F-002", main="P-02")
        )
        r = Report()
        check_prd_a_index_complete({}, prd, spec_two_f, r)
        assert any("行数" in w and ("≠" in w or "不" in w) for w in r.warnings)


# ── SSOT #69 interaction-card C-0~C-3 schema 校验（S4-56~60）────


def _ic_card(content: str = "") -> str:
    """构造一个 interaction-card 容器。需要后面包 </section> 边界让迭代器停。"""
    return f'<div class="interaction-card">{content}</div></section>'


class TestS456InteractionC0:
    """SSOT #69 / S4-56 — C-0 .state-diff-note 子区块（WARN）。"""

    def test_skip_no_card(self) -> None:
        from precheck_stage4 import check_interaction_c0_state_diff_note  # type: ignore
        r = Report()
        check_interaction_c0_state_diff_note("<html></html>", r)
        assert r.warnings == []

    def test_pass_with_state_diff(self) -> None:
        from precheck_stage4 import check_interaction_c0_state_diff_note  # type: ignore
        prd = _ic_card('<div class="state-diff-note">本帧初始</div>')
        r = Report()
        check_interaction_c0_state_diff_note(prd, r)
        assert r.warnings == []

    def test_warn_missing_state_diff(self) -> None:
        from precheck_stage4 import check_interaction_c0_state_diff_note  # type: ignore
        prd = _ic_card('<p>无 state-diff-note</p>')
        r = Report()
        check_interaction_c0_state_diff_note(prd, r)
        assert len(r.warnings) == 1


class TestS457InteractionC1ListTable:
    """SSOT #69 / S4-57 — C-1 列表回显 4 行表（WARN）。"""

    def test_skip_no_card(self) -> None:
        from precheck_stage4 import check_interaction_c1_list_table  # type: ignore
        r = Report()
        check_interaction_c1_list_table("<html></html>", r)
        assert r.warnings == []

    def test_skip_no_c1_title(self) -> None:
        from precheck_stage4 import check_interaction_c1_list_table  # type: ignore
        prd = _ic_card('<div class="state-diff-note">x</div>')
        r = Report()
        check_interaction_c1_list_table(prd, r)
        # 无 C-1 标题 → 跳过校验
        assert all("缺固定行目" not in w for w in r.warnings)

    def test_pass_4_rows(self) -> None:
        from precheck_stage4 import check_interaction_c1_list_table  # type: ignore
        prd = _ic_card(
            '<div>列表回显说明</div>'
            '<table><tr><td>排序规则</td><td>x</td></tr>'
            '<tr><td>加载方式</td><td>x</td></tr>'
            '<tr><td>总数回显</td><td>x</td></tr>'
            '<tr><td>空列表判断</td><td>x</td></tr></table>'
        )
        r = Report()
        check_interaction_c1_list_table(prd, r)
        assert r.warnings == []

    def test_warn_missing_rows(self) -> None:
        from precheck_stage4 import check_interaction_c1_list_table  # type: ignore
        prd = _ic_card(
            '<div>列表回显说明</div>'
            '<table><tr><td>排序规则</td><td>x</td></tr></table>'
        )
        r = Report()
        check_interaction_c1_list_table(prd, r)
        assert any("缺固定行目" in w for w in r.warnings)

    def test_exempt_no_list(self) -> None:
        from precheck_stage4 import check_interaction_c1_list_table  # type: ignore
        prd = _ic_card('<div>列表回显说明</div><p>本帧无列表</p>')
        r = Report()
        check_interaction_c1_list_table(prd, r)
        assert all("缺固定行目" not in w for w in r.warnings)


class TestS458InteractionC2AUnitIndex:
    """SSOT #69 / S4-58 — C-2.A C 单元清单 6 列（WARN）。"""

    def test_skip_no_card(self) -> None:
        from precheck_stage4 import check_interaction_c2a_unit_index  # type: ignore
        r = Report()
        check_interaction_c2a_unit_index("<html></html>", r)
        assert r.warnings == []

    def test_pass_6_cols(self) -> None:
        # 议题 17 二级判定升级：sub-title 必须容器锁定（`<div class="data-sub-title">`）
        from precheck_stage4 import check_interaction_c2a_unit_index  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">数据展示说明</div>'
            '<table><thead><tr>'
            '<th>C 触点 ID</th><th>单元名称</th>'
            '<th>是否封装为组件</th><th>渲染时机</th>'
            '<th>跨平台差异</th><th>关联 T 触点</th>'
            '</tr></thead></table>'
        )
        r = Report()
        check_interaction_c2a_unit_index(prd, r)
        assert r.warnings == []

    def test_warn_missing_cols(self) -> None:
        from precheck_stage4 import check_interaction_c2a_unit_index  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">数据展示说明</div>'
            '<table><thead><tr>'
            '<th>C 触点 ID</th><th>单元名称</th>'
            '</tr></thead></table>'
        )
        r = Report()
        check_interaction_c2a_unit_index(prd, r)
        assert any("缺列" in w for w in r.warnings)

    def test_exempt_no_data(self) -> None:
        from precheck_stage4 import check_interaction_c2a_unit_index  # type: ignore
        prd = _ic_card('<div class="data-sub-title">数据展示说明</div><p>本帧无数据展示</p>')
        r = Report()
        check_interaction_c2a_unit_index(prd, r)
        assert all("缺列" not in w for w in r.warnings)

    # 议题 17 二级判定升级：一级判定（容器锁定）新增 narrative-only 检测
    def test_narrative_only_one_level_warn(self) -> None:
        """sub-title 字面存在但未容器化（裸 `<div>数据展示说明</div>`）→ 一级判定 WARN"""
        from precheck_stage4 import check_interaction_c2a_unit_index  # type: ignore
        prd = _ic_card(
            '<div>数据展示说明</div>'  # 无 class="data-sub-title"
            '<table><thead><tr>'
            '<th>C 触点 ID</th><th>单元名称</th>'
            '<th>是否封装为组件</th><th>渲染时机</th>'
            '<th>跨平台差异</th><th>关联 T 触点</th>'
            '</tr></thead></table>'
        )
        r = Report()
        check_interaction_c2a_unit_index(prd, r)
        assert any("一级判定" in w and "未容器化" in w for w in r.warnings)


class TestS459InteractionC2BFieldTable:
    """SSOT #69 / S4-59 — C-2.B 字段子表 5 列含 D 触点 ID（WARN）。"""

    def test_skip_no_card(self) -> None:
        from precheck_stage4 import check_interaction_c2b_field_table  # type: ignore
        r = Report()
        check_interaction_c2b_field_table("<html></html>", r)
        assert r.warnings == []

    def test_pass_5_cols(self) -> None:
        # 议题 17 二级判定升级：sub-title 必须容器锁定
        from precheck_stage4 import check_interaction_c2b_field_table  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">字段说明 — C01</div>'
            '<table><thead><tr>'
            '<th>D 触点 ID</th><th>字段名</th>'
            '<th>接口字段</th><th>显示格式</th><th>空值处理</th>'
            '</tr></thead></table>'
        )
        r = Report()
        check_interaction_c2b_field_table(prd, r)
        assert r.warnings == []

    def test_warn_missing_d_id_col(self) -> None:
        from precheck_stage4 import check_interaction_c2b_field_table  # type: ignore
        # 缺 D 触点 ID 列；test 用 strict 容器 data-sub-title 触发
        prd = _ic_card(
            '<div class="data-sub-title">字段说明 — C01</div>'
            '<table><thead><tr>'
            '<th>字段名</th><th>接口字段</th>'
            '<th>显示格式</th><th>空值处理</th>'
            '</tr></thead></table>'
        )
        r = Report()
        check_interaction_c2b_field_table(prd, r)
        assert any("D 触点 ID" in w for w in r.warnings)

    # 议题 10 / PM 反审 trust-but-verify 实证（2026-06-04）：容器锁定 — narrative
    # 字面 `字段说明` 不再误命中二级判定。
    # 议题 23（2026-06-05，PM 反审治本）：一级判定 narrative-only 检测精化 —
    # 业务规则 cell（td / th / label）+ HTML 属性（data-zh / title 等）内字面
    # 不再误判为 narrative-only；仅 `<p>字段说明...</p>` 等顶层散文段才触发。
    def test_loose_field_label_in_td_no_false_positive(self) -> None:
        """narrative td 内含「字段说明」字面（如 D03 元素表行 / 业务规则 cell）— 不应误命中。
        议题 23：业务结构 cell 内字面剥除后不再触发一级判定 WARN（治 bujue-quotation-tool 8/8 FP）。
        """
        from precheck_stage4 import check_interaction_c2b_field_table  # type: ignore
        prd = _ic_card(
            # 元素表行内 td 含「字段说明」字面（quotation-tool card #111-#118 实证 FP）
            '<table><tr><td>D03</td><td>字段说明</td><td>CustomFieldDefinition</td></tr></table>'
            # 业务规则 cell 内字面（同源 FP，新版需识别）
            '<table><tr><td><strong>字段说明</strong>：≤200 字符，选填</td></tr></table>'
            # 无 data-sub-title 子标题 → 不触发 C-2.B 二级判定列校验
        )
        r = Report()
        check_interaction_c2b_field_table(prd, r)
        # 二级判定（列缺）应不触发
        assert all("缺列" not in w for w in r.warnings)
        # 议题 23：一级判定（narrative-only）应**不**触发 — td 内字面剥除后无残余
        assert all("一级判定" not in w for w in r.warnings)

    def test_loose_field_label_in_data_zh_attribute_no_false_positive(self) -> None:
        """data-zh 属性值含「字段说明」字面 — 议题 23 精化：属性值剥除后不触发一级判定 WARN。"""
        from precheck_stage4 import check_interaction_c2b_field_table  # type: ignore
        prd = _ic_card(
            '<label data-zh="字段说明" data-en="Field Description">字段说明</label>'
        )
        r = Report()
        check_interaction_c2b_field_table(prd, r)
        # 二级判定（列缺）不触发
        assert all("缺列" not in w for w in r.warnings)
        # 议题 23：一级判定 narrative-only 不触发 — label / 属性内字面剥除
        assert all("一级判定" not in w for w in r.warnings)

    # 议题 23 真 narrative-only 场景仍报：`<p>字段说明 — XXX</p>` 顶层散文段
    def test_real_narrative_p_tag_triggers_warn(self) -> None:
        """真 narrative-only 场景（`<p>字段说明 — XXX</p>` 顶层散文段）— 应触发一级判定 WARN。

        议题 23 精化只剥除业务结构 cell + 属性内字面，顶层 `<p>` 散文段保留 → 真违规被识别。
        """
        from precheck_stage4 import check_interaction_c2b_field_table  # type: ignore
        prd = _ic_card(
            '<p>字段说明 — name 必填、≤50 字符；description 选填</p>'
        )
        r = Report()
        check_interaction_c2b_field_table(prd, r)
        # 一级判定应触发（PM 未容器化）
        assert any("一级判定" in w and "未容器化" in w for w in r.warnings)

    def test_strict_container_match_still_triggers(self) -> None:
        """真容器 `<div class="data-sub-title">字段说明 ...</div>` 仍正常触发校验"""
        from precheck_stage4 import check_interaction_c2b_field_table  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">字段说明 — C01 项目卡片</div>'
            '<table><thead><tr>'
            '<th>D 触点 ID</th><th>字段名</th><th>接口字段</th>'
            '<th>显示格式</th><th>空值处理</th>'
            '</tr></thead></table>'
        )
        r = Report()
        check_interaction_c2b_field_table(prd, r)
        # 5 列齐全 → PASS
        assert r.warnings == []

    def test_spec_header_data_field_label_no_false_positive(self) -> None:
        """spec-header「数据字段说明」字面（quotation-tool L4605 实证 FP #1）— 二级判定不命中。
        议题 17 二级判定升级：字面含「字段说明」会触发一级判定 narrative-only WARN，
        但二级判定（列缺）应保持不命中（这是议题 10 容器锁定的核心目的）。
        """
        from precheck_stage4 import check_interaction_c2b_field_table  # type: ignore
        prd = _ic_card(
            '<div class="spec-header">数据字段说明</div>'  # spec-header 非 data-sub-title
            '<p>无 C-2.B</p>'
        )
        r = Report()
        check_interaction_c2b_field_table(prd, r)
        # 二级判定（列缺）不命中（议题 10 容器锁定核心目的保留）
        assert all("缺列" not in w for w in r.warnings)


class TestS460InteractionC3TouchpointTable:
    """SSOT #69 / S4-60 — C-3 触点表 6 列含跳转/边缘（WARN）。"""

    def test_skip_no_card(self) -> None:
        from precheck_stage4 import check_interaction_c3_touchpoint_table  # type: ignore
        r = Report()
        check_interaction_c3_touchpoint_table("<html></html>", r)
        assert r.warnings == []

    def test_pass_6_cols(self) -> None:
        # 议题 17 二级判定升级：sub-title 必须容器锁定
        from precheck_stage4 import check_interaction_c3_touchpoint_table  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">触点交互说明</div>'
            '<table><thead><tr>'
            '<th>序号</th><th>触点说明</th>'
            '<th>触发</th><th>行为</th>'
            '<th>跳转</th><th>边缘</th>'
            '</tr></thead></table>'
        )
        r = Report()
        check_interaction_c3_touchpoint_table(prd, r)
        assert r.warnings == []

    def test_warn_missing_jump_edge(self) -> None:
        from precheck_stage4 import check_interaction_c3_touchpoint_table  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">触点交互说明</div>'
            '<table><thead><tr>'
            '<th>序号</th><th>触点说明</th>'
            '<th>触发</th><th>行为</th>'
            '</tr></thead></table>'
        )
        r = Report()
        check_interaction_c3_touchpoint_table(prd, r)
        assert any("跳转" in w or "边缘" in w for w in r.warnings)

    def test_exempt_no_touchpoint(self) -> None:
        from precheck_stage4 import check_interaction_c3_touchpoint_table  # type: ignore
        prd = _ic_card('<div class="data-sub-title">触点交互说明</div><p>本帧无交互触点</p>')
        r = Report()
        check_interaction_c3_touchpoint_table(prd, r)
        assert all("缺列" not in w for w in r.warnings)

    # 议题 17 二级判定升级：一级判定（容器锁定）新增 narrative-only 检测
    def test_narrative_only_one_level_warn(self) -> None:
        """sub-title 字面存在但未容器化（裸 `<div>触点交互说明</div>`）→ 一级判定 WARN"""
        from precheck_stage4 import check_interaction_c3_touchpoint_table  # type: ignore
        prd = _ic_card(
            '<div>触点交互说明</div>'
            '<table><thead><tr>'
            '<th>序号</th><th>触点说明</th><th>触发</th>'
            '<th>行为</th><th>跳转</th><th>边缘</th>'
            '</tr></thead></table>'
        )
        r = Report()
        check_interaction_c3_touchpoint_table(prd, r)
        assert any("一级判定" in w and "未容器化" in w for w in r.warnings)


# ── 议题 2B / S4-61 interaction-card 同名子区块重复检测（WARN）────


class TestS461InteractionCardDoubleSubsection:
    """议题 2B / S4-61 — interaction-card 同名子区块重复检测（WARN）。"""

    def test_skip_no_card(self) -> None:
        from precheck_stage4 import check_interaction_card_double_subsection  # type: ignore
        r = Report()
        check_interaction_card_double_subsection("<html></html>", r)
        assert r.warnings == []

    def test_pass_single_form(self) -> None:
        """单一形态 — 只有 C-4 派生 → PASS。"""
        from precheck_stage4 import check_interaction_card_double_subsection  # type: ignore
        prd = _ic_card(
            '<div class="c4-sub-title">业务规则</div>'
            '<ul><li>规则 1</li></ul>'
        )
        r = Report()
        check_interaction_card_double_subsection(prd, r)
        assert r.warnings == []

    def test_warn_pm_handwritten_plus_c4(self) -> None:
        """PM 手写 + C-4 派生双段 → WARN（议题 2B 主治本场景）。"""
        from precheck_stage4 import check_interaction_card_double_subsection  # type: ignore
        prd = _ic_card(
            '<p><strong>业务规则</strong>：旧手写段</p>'
            '<div class="c4-sub-title">业务规则</div>'
            '<ul><li>派生段</li></ul>'
        )
        r = Report()
        check_interaction_card_double_subsection(prd, r)
        assert any("业务规则" in w for w in r.warnings)

    def test_warn_double_div_form(self) -> None:
        """data-sub-title + c4-sub-title 双 div 形态 → WARN。"""
        from precheck_stage4 import check_interaction_card_double_subsection  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">业务规则</div>'
            '<div class="c4-sub-title">业务规则</div>'
        )
        r = Report()
        check_interaction_card_double_subsection(prd, r)
        assert any("业务规则" in w for w in r.warnings)

    def test_multi_card_only_dup_flagged(self) -> None:
        """多卡场景，仅重复卡被统计。"""
        from precheck_stage4 import check_interaction_card_double_subsection  # type: ignore
        # 卡 1 干净；卡 2 双段
        prd = (
            '<div class="interaction-card">'
            '<div class="c4-sub-title">业务规则</div></div>'
            '<div class="interaction-card">'
            '<p><strong>业务规则</strong>:重复</p>'
            '<div class="c4-sub-title">业务规则</div></div></section>'
        )
        r = Report()
        check_interaction_card_double_subsection(prd, r)
        assert any("1/2" in w or "业务规则" in w for w in r.warnings)


# ── 议题 3 / S4-62 tp-marker 反向配对（WARN）────


class TestS462TpMarkerReversePairing:
    """议题 3 / S4-62 — tp-marker 反向配对：marker → data-tp（WARN）。"""

    def test_skip_no_marker(self) -> None:
        from precheck_stage4 import check_tp_marker_reverse_pairing  # type: ignore
        r = Report()
        check_tp_marker_reverse_pairing("<html></html>", r)
        assert all("悬空" not in w for w in r.warnings)

    def test_pass_paired(self) -> None:
        """data-tp + 邻近 marker 配对 → PASS。"""
        from precheck_stage4 import check_tp_marker_reverse_pairing  # type: ignore
        prd = (
            '<div data-tp="M01-P01-T01">elem</div>'
            '<span class="tp-wrap"><span class="tp-marker">01</span></span>'
        )
        r = Report()
        check_tp_marker_reverse_pairing(prd, r)
        assert all("悬空" not in w for w in r.warnings)

    def test_warn_orphan_marker(self) -> None:
        """悬空 marker（无邻近 data-tp 末段配对）→ WARN。"""
        from precheck_stage4 import check_tp_marker_reverse_pairing  # type: ignore
        # marker 99 但所有 data-tp 末段都不是 99
        prd = (
            '<div data-tp="M01-P01-T01">elem</div>'
            '<span class="tp-marker">99</span>'
        )
        r = Report()
        check_tp_marker_reverse_pairing(prd, r)
        assert any("悬空" in w and "99" in w for w in r.warnings)

    def test_exempt_showcase_only(self) -> None:
        """showcase-only 父链路 → 豁免。"""
        from precheck_stage4 import check_tp_marker_reverse_pairing  # type: ignore
        prd = (
            '<div class="showcase-only">'
            '<span class="tp-marker">99</span></div>'
        )
        r = Report()
        check_tp_marker_reverse_pairing(prd, r)
        # showcase-only 父链路在 ±200 字符内 → 不计入悬空
        assert all("99" not in w for w in r.warnings)


# ── 议题 2A / S4-63 interaction-card C-4 表达形式校验（WARN）────


class TestS463InteractionCardC4Format:
    """议题 2A / S4-63 — interaction-card C-4 表达形式校验（WARN）。

    C-4.A 业务规则 → <table class="c4-business-rules">
    C-4.B 数据规模 → <table class="c4-data-scale">
    C-4.C 验收标准 → <pre class="gherkin">
    """

    def test_skip_no_card(self) -> None:
        from precheck_stage4 import check_interaction_card_c4_format  # type: ignore
        r = Report()
        check_interaction_card_c4_format("<html></html>", r)
        assert r.warnings == []

    def test_skip_card_without_c4_marker(self) -> None:
        """无 [C4-START: 注入标记 → 跳过（副页面跳转形态合规）。"""
        from precheck_stage4 import check_interaction_card_c4_format  # type: ignore
        prd = _ic_card('<div class="state-diff-note">x</div>')
        r = Report()
        check_interaction_card_c4_format(prd, r)
        assert r.warnings == []

    def test_pass_all_three_formats(self) -> None:
        """C-4.A 表格 + C-4.B 表格 + C-4.C pre.gherkin 全合规 → PASS。"""
        from precheck_stage4 import check_interaction_card_c4_format  # type: ignore
        prd = _ic_card(
            '<!-- [C4-START: H-M01-P01-default] -->\n'
            '<table class="c4-business-rules"><thead><tr><th>#</th><th>业务规则</th></tr></thead>'
            '<tbody><tr><td>1</td><td>规则一</td></tr></tbody></table>\n'
            '<table class="c4-data-scale"><thead><tr><th>维度</th><th>值</th></tr></thead>'
            '<tbody><tr><td>单用户数据量</td><td>N</td></tr></tbody></table>\n'
            '<pre class="gherkin">Given x When y Then z</pre>\n'
            '<!-- [C4-END: H-M01-P01-default] -->'
        )
        r = Report()
        check_interaction_card_c4_format(prd, r)
        assert all("S4-63" not in w for w in r.warnings)

    def test_warn_c4a_ul_not_table(self) -> None:
        """C-4.A 仍为 <ul class="c4-business-rules"> → WARN（议题 2A 治本场景）。"""
        from precheck_stage4 import check_interaction_card_c4_format  # type: ignore
        prd = _ic_card(
            '<!-- [C4-START: x] -->\n'
            '<ul class="c4-business-rules"><li>旧表达</li></ul>\n'
            '<table class="c4-data-scale"><thead><tr><th>维度</th><th>值</th></tr></thead>'
            '<tbody><tr><td>x</td><td>y</td></tr></tbody></table>\n'
            '<pre class="gherkin">G x W y T z</pre>\n'
            '<!-- [C4-END: x] -->'
        )
        r = Report()
        check_interaction_card_c4_format(prd, r)
        assert any("S4-63" in w and "C-4.A" in w for w in r.warnings)

    def test_warn_c4b_p_not_table(self) -> None:
        """C-4.B 仍为 <p class="c4-data-scale"> 单段 → WARN（议题 2A 治本场景）。"""
        from precheck_stage4 import check_interaction_card_c4_format  # type: ignore
        prd = _ic_card(
            '<!-- [C4-START: x] -->\n'
            '<table class="c4-business-rules"><thead><tr><th>#</th><th>业务规则</th></tr></thead>'
            '<tbody><tr><td>1</td><td>r</td></tr></tbody></table>\n'
            '<p class="c4-data-scale">单用户数据量：N / 单次返回量：N</p>\n'
            '<pre class="gherkin">G W T</pre>\n'
            '<!-- [C4-END: x] -->'
        )
        r = Report()
        check_interaction_card_c4_format(prd, r)
        assert any("S4-63" in w and "C-4.B" in w for w in r.warnings)

    def test_warn_c4c_missing_gherkin(self) -> None:
        """C-4.C 缺 <pre class="gherkin"> → WARN。"""
        from precheck_stage4 import check_interaction_card_c4_format  # type: ignore
        prd = _ic_card(
            '<!-- [C4-START: x] -->\n'
            '<table class="c4-business-rules"><thead><tr><th>#</th><th>业务规则</th></tr></thead>'
            '<tbody><tr><td>1</td><td>r</td></tr></tbody></table>\n'
            '<table class="c4-data-scale"><thead><tr><th>维度</th><th>值</th></tr></thead>'
            '<tbody><tr><td>x</td><td>y</td></tr></tbody></table>\n'
            '<p>无 Gherkin pre</p>\n'
            '<!-- [C4-END: x] -->'
        )
        r = Report()
        check_interaction_card_c4_format(prd, r)
        assert any("S4-63" in w and "C-4.C" in w for w in r.warnings)


# ── 议题 16 / NB-R3-02 / S4-64 interaction-card sub-title 顺序 + 完整性校验 ────


class TestS464InteractionCardSubtitleOrder:
    """议题 16 / NB-R3-02 — interaction-card sub-title 顺序 + 完整性校验（WARN）"""

    def _all_present_card(self) -> str:
        return _ic_card(
            '<div class="data-sub-title">列表回显说明</div><p>本帧无列表</p>'
            '<div class="data-sub-title">数据展示说明</div><p>本帧无数据展示</p>'
            '<div class="data-sub-title">触点交互说明</div><p>本帧无交互触点</p>'
            '<div class="data-sub-title">业务契约</div><p>本帧无业务契约</p>'
        )

    def test_skip_no_card(self) -> None:
        from precheck_stage4 import check_interaction_card_subtitle_order  # type: ignore
        r = Report()
        check_interaction_card_subtitle_order("<html></html>", r)
        assert r.warnings == []

    def test_pass_all_4_subtitles_in_order(self) -> None:
        from precheck_stage4 import check_interaction_card_subtitle_order  # type: ignore
        r = Report()
        check_interaction_card_subtitle_order(self._all_present_card(), r)
        # 4 子区块齐全 + 顺序合规 → 0 WARN
        assert all("S4-64" not in w or "PASS" in w for w in r.warnings)
        assert not any("完整性" in w or "顺序" in w for w in r.warnings)

    def test_warn_missing_c1(self) -> None:
        from precheck_stage4 import check_interaction_card_subtitle_order  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">数据展示说明</div>'
            '<div class="data-sub-title">触点交互说明</div>'
            '<div class="data-sub-title">业务契约</div>'
        )
        r = Report()
        check_interaction_card_subtitle_order(prd, r)
        assert any("完整性" in w and "列表回显说明" in w for w in r.warnings)

    def test_warn_missing_c4(self) -> None:
        from precheck_stage4 import check_interaction_card_subtitle_order  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">列表回显说明</div>'
            '<div class="data-sub-title">数据展示说明</div>'
            '<div class="data-sub-title">触点交互说明</div>'
        )
        r = Report()
        check_interaction_card_subtitle_order(prd, r)
        assert any("完整性" in w and "业务契约" in w for w in r.warnings)

    def test_warn_order_violation(self) -> None:
        """sub-title 4 全在但顺序乱（C-3 在 C-1 之前）→ 顺序 WARN"""
        from precheck_stage4 import check_interaction_card_subtitle_order  # type: ignore
        prd = _ic_card(
            '<div class="data-sub-title">触点交互说明</div>'  # C-3 在前
            '<div class="data-sub-title">列表回显说明</div>'  # C-1 在后
            '<div class="data-sub-title">数据展示说明</div>'
            '<div class="data-sub-title">业务契约</div>'
        )
        r = Report()
        check_interaction_card_subtitle_order(prd, r)
        assert any("顺序" in w for w in r.warnings)


# ── 议题 20 / S4-65 — scaffold version ↔ changelog 末行 version 一致性 ─────────


class TestScaffoldVersionChangelogConsistency:
    """S4-65 v1（议题 20 / NB-WE-2A-R8-03 P1）— scaffold.json `version` 与 `changelog`
    末行 `version` 一致性 WARN。
    """

    def _write_scaffold(self, tmp_path, version, changelog_versions):
        import json as _json

        scaffold = {
            "schema_version": "v2.0",
            "product": "测试产品",
            "version": version,
            "changelog": [
                {"version": v, "desc": f"changelog {v}", "date": "2026-06-05"}
                for v in changelog_versions
            ],
        }
        sc_path = tmp_path / "scaffold.json"
        sc_path.write_text(_json.dumps(scaffold, ensure_ascii=False), encoding="utf-8")
        return sc_path

    def test_consistent_pass(self, tmp_path) -> None:
        """scaffold.version 与 changelog 末行一致 → PASS"""
        from precheck_stage4 import check_scaffold_version_changelog_consistency  # type: ignore
        sc_path = self._write_scaffold(tmp_path, "v0.1", ["v0.1"])
        r = Report()
        check_scaffold_version_changelog_consistency(sc_path, r)
        assert r.passed >= 1
        assert not r.errors
        assert not r.warnings

    def test_inconsistent_warn(self, tmp_path) -> None:
        """scaffold.version=v4.0 vs changelog 末行=v0.1 → WARN"""
        from precheck_stage4 import check_scaffold_version_changelog_consistency  # type: ignore
        sc_path = self._write_scaffold(tmp_path, "v4.0", ["v0.1"])
        r = Report()
        check_scaffold_version_changelog_consistency(sc_path, r)
        assert any("S4-65" in w and "v4.0" in w and "v0.1" in w for w in r.warnings)

    def test_multi_entry_takes_last(self, tmp_path) -> None:
        """changelog 多条 → 取末行；与 scaffold.version 比较"""
        from precheck_stage4 import check_scaffold_version_changelog_consistency  # type: ignore
        sc_path = self._write_scaffold(tmp_path, "v1.0", ["v0.1", "v1.0"])
        r = Report()
        check_scaffold_version_changelog_consistency(sc_path, r)
        assert r.passed >= 1
        assert not r.warnings

    def test_scaffold_missing_warn(self, tmp_path) -> None:
        """scaffold.json 不存在 → 优雅降级 WARN（不阻断）"""
        from precheck_stage4 import check_scaffold_version_changelog_consistency  # type: ignore
        sc_path = tmp_path / "missing_scaffold.json"
        r = Report()
        check_scaffold_version_changelog_consistency(sc_path, r)
        assert any("S4-65" in w and "不存在" in w for w in r.warnings)

    def test_empty_changelog_warn(self, tmp_path) -> None:
        """changelog 为空 → 优雅降级 WARN"""
        from precheck_stage4 import check_scaffold_version_changelog_consistency  # type: ignore
        sc_path = self._write_scaffold(tmp_path, "v0.1", [])
        r = Report()
        check_scaffold_version_changelog_consistency(sc_path, r)
        assert any("S4-65" in w and "为空" in w for w in r.warnings)


# ── SSOT #70 业务流程图选型规范配套机械兜底 ─────────────────────────────────


class TestBusinessFlowDiagrams:
    """SSOT #70 业务流程图选型规范配套机械兜底（[Should] WARN 阶段）。

    覆盖 3 项可机械化项：
      R1 图类型头部识别 — flowchart / sequenceDiagram / stateDiagram-v2 / journey 等
      R2 flowchart 终态节点完整 — Name([...]) stadium-shape ≥ 1
      R3 flowchart 判断节点全覆盖 — Name{...} 每节点出口 ≥ 2
    """

    def _spec_with_mermaid(self, content: str) -> str:
        """构造含单个 mermaid fence block 的 spec.md 内容"""
        return f"# Spec\n\n## §3.4 业务流程图\n\n```mermaid\n{content}\n```\n"

    def _prd_with_mermaid(self, content: str) -> str:
        """构造含单个 <pre class=\"mermaid\"> 块的 prd.html 内容"""
        return f'<html><body><pre class="mermaid">{content}</pre></body></html>'

    def test_no_blocks_skipped(self) -> None:
        """无 mermaid 块 → r.ok 跳过，0 WARN"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        r = Report()
        check_business_flow_diagrams("# Spec only", "<html></html>", r)
        assert r.passed >= 1
        assert not r.warnings

    def test_valid_flowchart_pass(self) -> None:
        """合规 flowchart 含终态 + 决策节点双分支 → PASS"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        spec = self._spec_with_mermaid(
            "flowchart TD\n"
            "    Start([开始]) --> A{是否登录?}\n"
            "    A -->|是| B[进入首页]\n"
            "    A -->|否| C[跳登录页]\n"
            "    B --> End([结束])\n"
            "    C --> End"
        )
        r = Report()
        check_business_flow_diagrams(spec, "", r)
        assert r.passed >= 1
        assert not r.warnings, f"应 PASS 但有 WARN: {r.warnings}"

    def test_valid_sequence_pass(self) -> None:
        """合规 sequenceDiagram → R2/R3 自动跳过 → PASS"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        spec = self._spec_with_mermaid(
            "sequenceDiagram\n"
            "    participant A as 用户\n"
            "    participant B as 系统\n"
            "    A->>B: 请求数据\n"
            "    B-->>A: 返回结果"
        )
        r = Report()
        check_business_flow_diagrams(spec, "", r)
        assert r.passed >= 1
        assert not r.warnings

    def test_r1_invalid_header_warn(self) -> None:
        """图类型头部不识别 → R1 WARN"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        spec = self._spec_with_mermaid(
            "myDiagram TD\n"
            "    A --> B"
        )
        r = Report()
        check_business_flow_diagrams(spec, "", r)
        assert any("R1" in w and "图类型头部不识别" in w for w in r.warnings)

    def test_r2_no_terminal_warn(self) -> None:
        """flowchart 无终态节点 → R2 WARN"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        spec = self._spec_with_mermaid(
            "flowchart TD\n"
            "    A[开始] --> B[处理]\n"
            "    B --> C[结束]"
        )
        r = Report()
        check_business_flow_diagrams(spec, "", r)
        assert any("R2" in w and "终态节点缺失" in w for w in r.warnings)

    def test_r3_decision_missing_branch_warn(self) -> None:
        """决策节点仅 1 条出口 → R3 WARN"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        spec = self._spec_with_mermaid(
            "flowchart TD\n"
            "    Start([开始]) --> A{条件?}\n"
            "    A -->|是| B[处理]\n"
            "    B --> End([结束])"
        )
        r = Report()
        check_business_flow_diagrams(spec, "", r)
        assert any("R3" in w and "分支不全" in w for w in r.warnings)

    def test_prd_pre_mermaid_priority(self) -> None:
        """PRD <pre class=\"mermaid\"> 优先于 spec ```mermaid（人类交付超集）"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        # spec 含违规块，prd 含合规块 → 应只校 prd
        spec = self._spec_with_mermaid("invalidHeader\n    A --> B")
        prd = self._prd_with_mermaid(
            "flowchart TD\n"
            "    Start([开始]) --> A{条件?}\n"
            "    A -->|是| B([结束A])\n"
            "    A -->|否| C([结束B])"
        )
        r = Report()
        check_business_flow_diagrams(spec, prd, r)
        # prd 合规 → 0 WARN（spec 因 prd 存在被跳过）
        assert not any("R1" in w for w in r.warnings), f"prd 优先，spec 不应触发 R1: {r.warnings}"

    def test_state_diagram_pass(self) -> None:
        """stateDiagram-v2 不应用 R2/R3（状态机语义不同）→ PASS"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        spec = self._spec_with_mermaid(
            "stateDiagram-v2\n"
            "    [*] --> Active\n"
            "    Active --> Archived\n"
            "    Archived --> Deleted\n"
            "    Deleted --> [*]"
        )
        r = Report()
        check_business_flow_diagrams(spec, "", r)
        # stateDiagram 不应用 R2/R3 → 0 WARN
        assert not r.warnings, f"stateDiagram 应跳过 R2/R3: {r.warnings}"

    def test_multi_decision_nodes_partial_warn(self) -> None:
        """多决策节点，1 个完整 + 1 个缺分支 → 1 条 R3 WARN"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        spec = self._spec_with_mermaid(
            "flowchart TD\n"
            "    Start([开始]) --> A{完整?}\n"
            "    A -->|是| B[正常]\n"
            "    A -->|否| C{缺分支?}\n"
            "    C -->|是| D[终态]\n"
            "    B --> End([结束])\n"
            "    D --> End"
        )
        r = Report()
        check_business_flow_diagrams(spec, "", r)
        # 仅 C 节点违规（仅 1 条 |是| 分支）
        assert any("R3" in w and "C" in w for w in r.warnings)

    def test_empty_block_skipped(self) -> None:
        """空 mermaid 块（仅 %% 注释）→ 跳过 → PASS"""
        from precheck_stage4 import check_business_flow_diagrams  # type: ignore
        spec = self._spec_with_mermaid("%% only comment\n%% another comment")
        r = Report()
        check_business_flow_diagrams(spec, "", r)
        # 仅注释 → 视为空块 → 不触发 R1
        assert r.passed >= 1 or not r.warnings


class TestHtmlDivBalance:
    """SSOT #71 — outputs/prd 真 DOM div 平衡兜底（议题 10 NB-WE-PROTO-NAV-OVERWRITE）。

    用 html.parser 跟踪 div 深度，最终 depth ≠ 0 → WARN。与 assemble.py
    `_ensure_layout_closing_before_body` 兜底层协同。
    """

    def test_balanced_pass(self) -> None:
        """完全平衡 div → PASS"""
        from precheck_stage4 import check_html_div_balance  # type: ignore
        html = '<html><body><div class="a"><div class="b"></div></div></body></html>'
        r = Report()
        check_html_div_balance(html, r)
        assert r.passed >= 1
        assert not r.warnings, f"应 PASS 但有 WARN: {r.warnings}"

    def test_missing_close_warns(self) -> None:
        """缺 1 个 </div> → WARN (depth +1)"""
        from precheck_stage4 import check_html_div_balance  # type: ignore
        html = '<html><body><div class="layout"><div class="x"></div></body></html>'
        r = Report()
        check_html_div_balance(html, r)
        assert r.warnings, "缺 close 应 WARN"
        assert "depth +1" in "\n".join(r.warnings) or "缺 1" in "\n".join(r.warnings)

    def test_extra_close_warns(self) -> None:
        """多 1 个 </div> 孤儿 → WARN (depth -1)"""
        from precheck_stage4 import check_html_div_balance  # type: ignore
        html = '<html><body><div></div></div></body></html>'
        r = Report()
        check_html_div_balance(html, r)
        assert r.warnings, "多 close 应 WARN"
        assert "depth -1" in "\n".join(r.warnings) or "多 1" in "\n".join(r.warnings)

    def test_script_div_literal_ignored(self) -> None:
        """script 内 `<div>` 字面 → 不计入（浏览器不解析） → PASS"""
        from precheck_stage4 import check_html_div_balance  # type: ignore
        html = '<html><body><div></div><script>var s = "<div>x</div>";</script></body></html>'
        r = Report()
        check_html_div_balance(html, r)
        assert r.passed >= 1
        assert not r.warnings

    def test_style_div_literal_ignored(self) -> None:
        """style 内 `<div>` 字面（注释或属性选择器）→ 不计入 → PASS"""
        from precheck_stage4 import check_html_div_balance  # type: ignore
        html = '<html><body><div></div><style>/* <div></div> */</style></body></html>'
        r = Report()
        check_html_div_balance(html, r)
        assert r.passed >= 1
        assert not r.warnings

    def test_empty_html_skipped(self) -> None:
        """空 prd_html → skip"""
        from precheck_stage4 import check_html_div_balance  # type: ignore
        r = Report()
        check_html_div_balance("", r)
        assert r.passed >= 1
        assert not r.warnings


class TestScaffoldOutputsFrameConsistency:
    """SSOT #72 — scaffold ↔ outputs/prd FRAME 一致性兜底（议题 11/12 NB-WE-12）。

    比对 scaffold prd_id 全集 vs outputs/prd 含 FRAME 全集，输出漂移 A/B 详情。
    """

    def _scaffold(self, prd_ids: list) -> dict:
        """构造 scaffold 含 prd_ids"""
        return {
            "modules": [
                {
                    "id": "M01",
                    "pages": [
                        {
                            "id": "P01",
                            "states": [{"prd_id": pid, "name": pid} for pid in prd_ids],
                        }
                    ],
                }
            ]
        }

    def test_consistent_pass(self) -> None:
        """scaffold ∩ outputs 全一致 → PASS"""
        from precheck_stage4 import check_scaffold_outputs_frame_consistency  # type: ignore
        scaffold = self._scaffold(["H-M01-P01-default", "H-M01-P01-error"])
        prd = '<div id="H-M01-P01-default"></div><div id="H-M01-P01-error"></div>'
        r = Report()
        check_scaffold_outputs_frame_consistency(scaffold, prd, r)
        assert r.passed >= 1
        assert not r.warnings, f"应 PASS 但有 WARN: {r.warnings}"

    def test_drift_a_warns(self) -> None:
        """scaffold 有 / outputs 无 → 漂移 A WARN（议题 #10 ERROR 触发场景）"""
        from precheck_stage4 import check_scaffold_outputs_frame_consistency  # type: ignore
        scaffold = self._scaffold(["H-M01-P01-default", "H-M01-P01-offshelf-default"])
        prd = '<div id="H-M01-P01-default"></div>'  # 缺 offshelf
        r = Report()
        check_scaffold_outputs_frame_consistency(scaffold, prd, r)
        assert r.warnings, "漂移 A 应 WARN"
        msg = "\n".join(r.warnings)
        assert "漂移 A" in msg and "H-M01-P01-offshelf-default" in msg

    def test_drift_b_warns(self) -> None:
        """outputs 有 / scaffold 无 → 漂移 B 孤儿 WARN（议题 #11 私域实证场景）"""
        from precheck_stage4 import check_scaffold_outputs_frame_consistency  # type: ignore
        scaffold = self._scaffold(["H-M01-P01-default"])
        prd = '<div id="H-M01-P01-default"></div><div id="H-M07-P07-loading"></div>'  # 孤儿
        r = Report()
        check_scaffold_outputs_frame_consistency(scaffold, prd, r)
        assert r.warnings, "漂移 B 应 WARN"
        msg = "\n".join(r.warnings)
        assert "漂移 B" in msg and "H-M07-P07-loading" in msg

    def test_drift_a_and_b_both_warn(self) -> None:
        """漂移 A + B 同时存在 → 单 WARN 含双段"""
        from precheck_stage4 import check_scaffold_outputs_frame_consistency  # type: ignore
        scaffold = self._scaffold(["H-A", "H-B"])
        prd = '<div id="H-A"></div><div id="H-X"></div>'  # B 缺，X 孤
        r = Report()
        check_scaffold_outputs_frame_consistency(scaffold, prd, r)
        assert r.warnings
        msg = "\n".join(r.warnings)
        assert "漂移 A" in msg and "H-B" in msg
        assert "漂移 B" in msg and "H-X" in msg

    def test_placeholder_form_recognized(self) -> None:
        """`<!-- [FRAME: H-X] -->` placeholder 形式也被识别为 outputs 含"""
        from precheck_stage4 import check_scaffold_outputs_frame_consistency  # type: ignore
        scaffold = self._scaffold(["H-A"])
        prd = '<!-- [FRAME: H-A] -->'
        r = Report()
        check_scaffold_outputs_frame_consistency(scaffold, prd, r)
        assert r.passed >= 1
        assert not r.warnings

    def test_frame_start_form_recognized(self) -> None:
        """`<!-- [FRAME-START: H-X ...] -->` 可重入块形式也被识别"""
        from precheck_stage4 import check_scaffold_outputs_frame_consistency  # type: ignore
        scaffold = self._scaffold(["H-A"])
        prd = '<!-- [FRAME-START: H-A | assembled=2026-06-07] --><div></div><!-- [FRAME-END: H-A] -->'
        r = Report()
        check_scaffold_outputs_frame_consistency(scaffold, prd, r)
        assert r.passed >= 1
        assert not r.warnings

    def test_empty_scaffold_skipped(self) -> None:
        """空 scaffold → skip"""
        from precheck_stage4 import check_scaffold_outputs_frame_consistency  # type: ignore
        r = Report()
        check_scaffold_outputs_frame_consistency({"modules": []}, "<div></div>", r)
        assert r.passed >= 1
        assert not r.warnings

    def test_empty_prd_skipped(self) -> None:
        """空 prd_html → skip"""
        from precheck_stage4 import check_scaffold_outputs_frame_consistency  # type: ignore
        scaffold = self._scaffold(["H-A"])
        r = Report()
        check_scaffold_outputs_frame_consistency(scaffold, "", r)
        assert r.passed >= 1
        assert not r.warnings


class TestNoAssembleTimestamp:
    """SSOT #73 — outputs/prd assemble 输出确定性兜底（议题 13 NB-WE-ASSEMBLE-DETERMINISM）。

    扫 outputs/prd 含 `assembled=<UTC ISO timestamp>` 字面（治本前残留 / 旧 assemble.py 产出）。
    """

    def test_no_timestamp_pass(self) -> None:
        """治本后 0 命中 → PASS"""
        from precheck_stage4 import check_outputs_prd_no_assemble_timestamp  # type: ignore
        html = '<!-- [FRAME-START: H-A | from=draft.html | sha256:abc123] -->'
        r = Report()
        check_outputs_prd_no_assemble_timestamp(html, r)
        assert r.passed >= 1
        assert not r.warnings, f"应 PASS 但有 WARN: {r.warnings}"

    def test_timestamp_warns(self) -> None:
        """含 timestamp 字面 → WARN（治本前残留）"""
        from precheck_stage4 import check_outputs_prd_no_assemble_timestamp  # type: ignore
        html = '<!-- [FRAME-START: H-A | assembled=2026-06-07T12:21:48Z | from=draft.html | sha256:abc123] -->'
        r = Report()
        check_outputs_prd_no_assemble_timestamp(html, r)
        assert r.warnings, "含 timestamp 应 WARN"
        assert "1 处" in "\n".join(r.warnings) or "assembled" in "\n".join(r.warnings)

    def test_multiple_timestamp_count(self) -> None:
        """多处 timestamp → WARN 含正确计数"""
        from precheck_stage4 import check_outputs_prd_no_assemble_timestamp  # type: ignore
        html = (
            '<!-- [FRAME-START: H-A | assembled=2026-06-07T12:21:48Z | from=d.html | sha256:a] -->'
            '<!-- [FRAME-START: H-B | assembled=2026-06-07T12:21:49Z | from=d.html | sha256:b] -->'
            '<!-- [FRAME-START: H-C | assembled=2026-06-07T12:21:50Z | from=d.html | sha256:c] -->'
        )
        r = Report()
        check_outputs_prd_no_assemble_timestamp(html, r)
        assert r.warnings
        assert "3 处" in "\n".join(r.warnings)

    def test_empty_html_skipped(self) -> None:
        """空 prd_html → skip"""
        from precheck_stage4 import check_outputs_prd_no_assemble_timestamp  # type: ignore
        r = Report()
        check_outputs_prd_no_assemble_timestamp("", r)
        assert r.passed >= 1
        assert not r.warnings

    def test_only_non_iso_timestamp_format_not_matched(self) -> None:
        """非 ISO 格式 timestamp（如 epoch / 不带 Z 后缀）不命中（避免 FP）"""
        from precheck_stage4 import check_outputs_prd_no_assemble_timestamp  # type: ignore
        # 非 ISO 格式：纯数字 / 不带 Z / 不带 T 等
        html = (
            '<!-- assembled=1717729308 --><!-- assembled=2026-06-07 -->'
            '<!-- assembled=12:21:48 -->'
        )
        r = Report()
        check_outputs_prd_no_assemble_timestamp(html, r)
        assert r.passed >= 1
        assert not r.warnings


class TestPageSourceProvenance:
    """SSOT #74 — 页面集守恒 page_source 溯源兜底（R1 阶段 2 页面集 SSOT）。

    每页须标 page_source（stage2 / director_approved:<日期>），缺失 / 格式非法 → WARN。
    """

    def _scaffold(self, pages: list) -> dict:
        """构造单模块 scaffold 含给定 pages"""
        return {"modules": [{"id": "M01", "name": "M01", "pages": pages}]}

    def test_all_stage2_pass(self) -> None:
        """全页标 stage2 → PASS"""
        from precheck_stage4 import check_page_source_provenance  # type: ignore
        sc = self._scaffold([
            {"id": "P01", "page_source": "stage2"},
            {"id": "P02", "page_source": "stage2"},
        ])
        r = Report()
        check_page_source_provenance(sc, r)
        assert r.passed >= 1
        assert not r.warnings, f"应 PASS 但有 WARN: {r.warnings}"

    def test_director_approved_pass(self) -> None:
        """escalation 批准页标 director_approved:<日期> → PASS"""
        from precheck_stage4 import check_page_source_provenance  # type: ignore
        sc = self._scaffold([
            {"id": "P01", "page_source": "stage2"},
            {"id": "P09", "page_source": "director_approved:2026-06-09"},
        ])
        r = Report()
        check_page_source_provenance(sc, r)
        assert r.passed >= 1
        assert not r.warnings

    def test_missing_warns(self) -> None:
        """缺 page_source → WARN（治擅自增页无溯源）"""
        from precheck_stage4 import check_page_source_provenance  # type: ignore
        sc = self._scaffold([
            {"id": "P01", "page_source": "stage2"},
            {"id": "P08"},  # 缺溯源
        ])
        r = Report()
        check_page_source_provenance(sc, r)
        assert r.warnings, "缺 page_source 应 WARN"
        assert "M01/P08" in "\n".join(r.warnings)

    def test_malformed_warns(self) -> None:
        """page_source 格式非法 → WARN"""
        from precheck_stage4 import check_page_source_provenance  # type: ignore
        sc = self._scaffold([
            {"id": "P01", "page_source": "stage2"},
            {"id": "P02", "page_source": "director_approved:2026/06/09"},  # 错格式
        ])
        r = Report()
        check_page_source_provenance(sc, r)
        assert r.warnings
        assert "格式非法" in "\n".join(r.warnings) or "M01/P02" in "\n".join(r.warnings)

    def test_logic_only_module_skipped(self) -> None:
        """logic-only 模块（pages=[]）跳过，不误报缺 page_source"""
        from precheck_stage4 import check_page_source_provenance  # type: ignore
        sc = {"modules": [
            {"id": "M01", "pages": [{"id": "P01", "page_source": "stage2"}]},
            {"id": "M09", "pages": []},  # logic-only
        ]}
        r = Report()
        check_page_source_provenance(sc, r)
        assert r.passed >= 1
        assert not r.warnings

    def test_empty_modules_skipped(self) -> None:
        """无 modules → skip"""
        from precheck_stage4 import check_page_source_provenance  # type: ignore
        r = Report()
        check_page_source_provenance({"modules": []}, r)
        assert r.passed >= 1
        assert not r.warnings


class TestDependsOnCycle:
    """SSOT #75-R7 — depends_on 运行时依赖图环检测。"""

    def _sc(self, mods: list) -> dict:
        return {"product": "X", "modules": mods}

    def test_no_cycle_pass(self) -> None:
        from precheck_stage4 import check_depends_on_cycle  # type: ignore
        sc = self._sc([
            {"id": "M01", "depends_on": [{"module": "M02", "kind": "data_flow", "target": "x"}]},
            {"id": "M02", "depends_on": []},
        ])
        r = Report()
        check_depends_on_cycle(sc, r)
        assert r.passed >= 1
        assert not r.warnings, f"应 PASS: {r.warnings}"

    def test_runtime_cycle_warns(self) -> None:
        """data_flow A→B→A 环 → WARN"""
        from precheck_stage4 import check_depends_on_cycle  # type: ignore
        sc = self._sc([
            {"id": "M01", "depends_on": [{"module": "M02", "kind": "data_flow", "target": "x"}]},
            {"id": "M02", "depends_on": [{"module": "M01", "kind": "data_flow", "target": "y"}]},
        ])
        r = Report()
        check_depends_on_cycle(sc, r)
        assert r.warnings, "运行时环应 WARN"
        assert "环" in "\n".join(r.warnings)

    def test_section_jump_cycle_excluded(self) -> None:
        """section_jump A→B→A 跳转伪环 → 不报（治问题 8）"""
        from precheck_stage4 import check_depends_on_cycle  # type: ignore
        sc = self._sc([
            {"id": "M01", "depends_on": [{"module": "M02", "kind": "section_jump", "target": "x"}]},
            {"id": "M02", "depends_on": [{"module": "M01", "kind": "section_jump", "target": "y"}]},
        ])
        r = Report()
        check_depends_on_cycle(sc, r)
        assert not r.warnings, "section_jump 伪环不应报"

    def test_shared_component_cycle_excluded(self) -> None:
        """shared_component 复用环 → 不报"""
        from precheck_stage4 import check_depends_on_cycle  # type: ignore
        sc = self._sc([
            {"id": "M01", "depends_on": [{"module": "M02", "kind": "shared_component", "target": "x"}]},
            {"id": "M02", "depends_on": [{"module": "M01", "kind": "shared_component", "target": "y"}]},
        ])
        r = Report()
        check_depends_on_cycle(sc, r)
        assert not r.warnings

    def test_no_runtime_edges_skipped(self) -> None:
        from precheck_stage4 import check_depends_on_cycle  # type: ignore
        sc = self._sc([{"id": "M01", "depends_on": []}])
        r = Report()
        check_depends_on_cycle(sc, r)
        assert r.passed >= 1
        assert not r.warnings


class TestArchetypeSemantics:
    """SSOT #75-R5 — archetype 语义匹配（只读页禁表单范式）。"""

    def _sc(self, archetypes: list, pages: list) -> dict:
        return {"product": "X", "page_archetypes": archetypes,
                "modules": [{"id": "M01", "pages": pages}]}

    def test_form_archetype_on_status_page_warns(self) -> None:
        """form 关键字 archetype 套纯状态页 → WARN（决定性案例）"""
        from precheck_stage4 import check_archetype_semantics  # type: ignore
        sc = self._sc(
            [{"id": "admin-form-flow", "name": "管理表单流"}],
            [{"id": "P01", "archetype": "admin-form-flow",
              "states": [{"name": "default"}, {"name": "loading"}, {"name": "error"},
                         {"name": "offshelf"}]}],
        )
        r = Report()
        check_archetype_semantics(sc, r)
        assert r.warnings, "只读页套表单范式应 WARN"
        assert "M01/P01" in "\n".join(r.warnings)

    def test_form_archetype_with_input_states_pass(self) -> None:
        """真表单页（含 edit/input 态）不报"""
        from precheck_stage4 import check_archetype_semantics  # type: ignore
        sc = self._sc(
            [{"id": "admin-form-flow", "name": "表单"}],
            [{"id": "P01", "archetype": "admin-form-flow",
              "states": [{"name": "default"}, {"name": "editing"}, {"name": "submit-error"}]}],
        )
        r = Report()
        check_archetype_semantics(sc, r)
        assert not r.warnings, "含输入态的表单页不应报"

    def test_explicit_semantic_form_exemption(self) -> None:
        """semantic_category=form 显式声明 → 仍按表单判定（但此处无纯状态页不报）"""
        from precheck_stage4 import check_archetype_semantics  # type: ignore
        sc = self._sc(
            [{"id": "ax", "name": "x", "semantic_category": "readonly-status"}],
            [{"id": "P01", "archetype": "ax",
              "states": [{"name": "default"}, {"name": "error"}]}],
        )
        r = Report()
        check_archetype_semantics(sc, r)
        # 显式标 readonly-status → 非表单类 → 不报
        assert not r.warnings

    def test_non_form_archetype_pass(self) -> None:
        from precheck_stage4 import check_archetype_semantics  # type: ignore
        sc = self._sc(
            [{"id": "list-detail", "name": "列表详情"}],
            [{"id": "P01", "archetype": "list-detail",
              "states": [{"name": "default"}, {"name": "error"}]}],
        )
        r = Report()
        check_archetype_semantics(sc, r)
        assert not r.warnings

    def test_maintenance_page_name_exempted(self) -> None:
        """FP 收敛：页名含『维护』的真表单页（form archetype + 状态态）不报"""
        from precheck_stage4 import check_archetype_semantics  # type: ignore
        sc = self._sc(
            [{"id": "admin-form-flow", "name": "表单流"}],
            [{"id": "P01", "name": "系统预设提示词维护页", "archetype": "admin-form-flow",
              "states": [{"name": "default"}, {"name": "empty"}, {"name": "error"}]}],
        )
        r = Report()
        check_archetype_semantics(sc, r)
        assert not r.warnings, "维护页应豁免（FP 收敛）"

    def test_decisive_case_still_caught(self) -> None:
        """决定性案例：强制下架卡片（页名无表单词 + 纯状态态 + form archetype）仍命中"""
        from precheck_stage4 import check_archetype_semantics  # type: ignore
        sc = self._sc(
            [{"id": "admin-form-flow", "name": "表单流"}],
            [{"id": "P09", "name": "强制下架状态卡片", "archetype": "admin-form-flow",
              "states": [{"name": "default"}, {"name": "loading"}, {"name": "error"},
                         {"name": "appeal-submitted"}]}],
        )
        r = Report()
        check_archetype_semantics(sc, r)
        assert r.warnings, "决定性案例应仍命中"
        assert "M01/P09" in "\n".join(r.warnings)

    def test_no_archetypes_skipped(self) -> None:
        from precheck_stage4 import check_archetype_semantics  # type: ignore
        r = Report()
        check_archetype_semantics({"product": "X", "modules": []}, r)
        assert r.passed >= 1
        assert not r.warnings


class TestExceptionCoverage:
    """SSOT #75-R6 — §11 异常覆盖粗对照（产品定义不存在则 skip）。"""

    def test_no_pdef_skipped(self) -> None:
        """产品定义不存在 → skip（测试环境无产品定义文件）"""
        from precheck_stage4 import check_exception_coverage  # type: ignore
        sc = {"product": "不存在的产品XYZ", "modules": [{"id": "M01", "pages": []}]}
        r = Report()
        check_exception_coverage(sc, r)
        assert r.passed >= 1
        assert not r.warnings

    def test_no_modules_skipped(self) -> None:
        from precheck_stage4 import check_exception_coverage  # type: ignore
        r = Report()
        check_exception_coverage({"product": "X", "modules": []}, r)
        assert r.passed >= 1
        assert not r.warnings


class TestSpecBusinessFlowDoubleView:
    """S4-66 议题 25 — §A-04.2 业务流程图双视图三件套校验（WARN）。

    治"Foundation Agent 漏实现 §A-04.2 双视图规范"漏洞。规范要求：
    `<section id="spec-business-flow">` 内每个含 mermaid 的 spec-block 必同时含
    journey-toggle + journey-table-view + journey-flow-view 三件套字面（同构复刻 A-04.1）。
    """

    def _prd_with_section(self, section_inner: str) -> str:
        return (
            "<html><body>\n"
            '<section id="spec-business-flow">\n'
            f"{section_inner}\n"
            "</section>\n"
            "</body></html>"
        )

    def _block_complete(self, label: str = "主流程总览") -> str:
        return (
            '<div class="spec-block">\n'
            f"<h3>{label}</h3>\n"
            '<div class="journey-toggle"><button>表格</button><button>流程图</button></div>\n'
            '<div class="journey-table-view"><table><tr><th>步骤</th></tr></table></div>\n'
            '<div class="journey-flow-view"><pre class="mermaid">flowchart TD\nA-->B</pre></div>\n'
            "</div>"
        )

    def _block_missing_all(self, label: str = "主流程总览") -> str:
        return (
            '<div class="spec-block">\n'
            f"<h3>{label}</h3>\n"
            '<pre class="mermaid">flowchart TD\nA-->B</pre>\n'
            "</div>"
        )

    def _block_missing_toggle_only(self, label: str = "主流程总览") -> str:
        return (
            '<div class="spec-block">\n'
            f"<h3>{label}</h3>\n"
            '<div class="journey-table-view"><table></table></div>\n'
            '<div class="journey-flow-view"><pre class="mermaid">flowchart TD</pre></div>\n'
            "</div>"
        )

    def test_complete_triplet_passes(self) -> None:
        """单 spec-block 三件套齐全 → 1 PASS / 0 WARN"""
        from precheck_stage4 import check_spec_business_flow_double_view  # type: ignore
        prd = self._prd_with_section(self._block_complete())
        r = Report()
        check_spec_business_flow_double_view(prd, r)
        assert r.passed >= 1 and not r.warnings

    def test_missing_all_triplet_warns(self) -> None:
        """单 spec-block 含 mermaid 但全缺三件套 → 1 WARN，缺失字面含 3 件套"""
        from precheck_stage4 import check_spec_business_flow_double_view  # type: ignore
        prd = self._prd_with_section(self._block_missing_all())
        r = Report()
        check_spec_business_flow_double_view(prd, r)
        assert len(r.warnings) == 1
        import re
        m = re.search(r"缺三件套：([^—]+)——", r.warnings[0])
        assert m, f"WARN 应含 '缺三件套：' 字面：{r.warnings[0]}"
        missing_set = {x.strip() for x in m.group(1).split("/")}
        assert missing_set == {"journey-toggle", "journey-table-view", "journey-flow-view"}

    def test_partial_missing_toggle_warns(self) -> None:
        """单 spec-block 仅缺 journey-toggle → 1 WARN，缺失列表仅含 toggle"""
        from precheck_stage4 import check_spec_business_flow_double_view  # type: ignore
        prd = self._prd_with_section(self._block_missing_toggle_only())
        r = Report()
        check_spec_business_flow_double_view(prd, r)
        assert len(r.warnings) == 1
        import re
        m = re.search(r"缺三件套：([^—]+)——", r.warnings[0])
        assert m, f"WARN 应含 '缺三件套：' 字面：{r.warnings[0]}"
        missing_set = {x.strip() for x in m.group(1).split("/")}
        assert missing_set == {"journey-toggle"}

    def test_no_section_skipped(self) -> None:
        """无 spec-business-flow section → 跳过 → PASS（豁免）"""
        from precheck_stage4 import check_spec_business_flow_double_view  # type: ignore
        prd = "<html><body><p>no section here</p></body></html>"
        r = Report()
        check_spec_business_flow_double_view(prd, r)
        assert r.passed >= 1 and not r.warnings

    def test_no_mermaid_in_section_skipped(self) -> None:
        """section 存在但 spec-block 无 mermaid → 跳过 → PASS（豁免）"""
        from precheck_stage4 import check_spec_business_flow_double_view  # type: ignore
        prd = self._prd_with_section(
            '<div class="spec-block"><h3>占位</h3><p>无 mermaid 块</p></div>'
        )
        r = Report()
        check_spec_business_flow_double_view(prd, r)
        assert r.passed >= 1 and not r.warnings

    def test_multi_block_mixed_passes_and_warns(self) -> None:
        """多 spec-block 混合：1 完整 + 1 全缺 → 1 WARN（仅违规块）"""
        from precheck_stage4 import check_spec_business_flow_double_view  # type: ignore
        prd = self._prd_with_section(
            self._block_complete("主流程总览") + "\n" + self._block_missing_all("跨角色交互")
        )
        r = Report()
        check_spec_business_flow_double_view(prd, r)
        assert len(r.warnings) == 1
        assert "跨角色交互" in r.warnings[0]
