"""测试 assemble.py 派生层 SSOT #67/#68 — A-05 信息架构重组 + C-4 业务契约派生。

Commit 2 (~460 行) 覆盖：
- C2-1 extract_business_rules — spec §S2.MXX.4B 提取（NB-WE-01 锚字面 .4B）
- C2-2 extract_data_scale — spec §S2.MXX.5B 提取（NB-WE-01 锚字面 .5B）
- C2-3 extract_gherkin — spec §S2.MXX.7 Gherkin 提取（双状态锚格式适配）
- C2-4 inject_c4_into_interaction_card — C-3 后注入 C-4 子区块 + 幂等
- C2-5 build_function_overview_index / _with_jump — A-索引 4 列表派生
- C2-6 inject_function_overview_index — A-05 替换 / 占位 / 重入幂等
- C2-7 inject_c4_for_module + _build_module_page_to_main_lookup —
        多页 F 主/副分支（主页面全量 / 副页面缩略）
- C2-8 extract_main_page — F-xxx 节主页面字段提取
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import assemble


# ── 测试 fixture（所有 spec 字面均用 .4B/.5B，NB-WE-01）─────────────────────

SAMPLE_SPEC_4B = """
## S2.M01.4B 业务规则（SSOT #68 — C-4 业务契约派生真源）

#### P01 项目首页

- 单用户最多收藏 50 个项目
- 项目卡片标题截断超过 30 字符显示省略号

#### P02 项目详情

- 编辑权限仅限创建者本人

## S2.M01.5B 数据规模（SSOT #68 — C-4 业务契约派生真源）

#### P01 项目首页

- 单用户数据量：≤ 200 项
- 单次返回量：分页 20
- 操作频率：日均 5 次

#### P02 项目详情

- 单用户数据量：—（纯展示页）
- 单次返回量：—
- 操作频率：—

## S2.M01.7 状态清单与验收标准

**P01-default**

- 互斥说明：默认态独立
- 触发条件：用户访问 /projects
- 页面表现：【区域】顶部导航 + 主区项目卡片网格
- 验收标准：

```gherkin
Given 用户已登录
When 用户访问 /projects
Then 显示项目卡片网格
And  接口返回数据时长 ≤ 1s
```

**P02-default**

- 验收标准：

```gherkin
Given 用户点击项目卡片
When 跳转至详情
Then 显示项目详情主区
```

## S2.M02.4B 业务规则

#### P01 报价单首页

- 报价单字段长度 ≤ 500 字符
"""

SAMPLE_SPEC_F_SECTIONS = """
#### F-001：项目管理

**优先级**：P0　｜　**所属旅程**：旅程一　｜　**涉及页面**：P-01, P-02　｜　**主页面**：P-01

#### F-002：报价工具

**优先级**：P1　｜　**所属旅程**：旅程二　｜　**涉及页面**：P-01　｜　**主页面**：P-01

#### F-003：缺主页面字段

**优先级**：P2　｜　**所属旅程**：旅程三　｜　**涉及页面**：P-01
"""


SAMPLE_INTERACTION_CARD_FRAME = """\
<div class="interaction-card">
  <div class="card-title">交互说明 — default</div>
  <div class="data-sub-title">触点交互说明</div>
  <table><tr><td>01</td><td>登录按钮</td></tr></table>
</div>"""


# ── C2-1 extract_business_rules ────────────────────────────────────────────

class TestExtractBusinessRules:
    """NB-WE-01：段头字面 `.4B`（非 `.4`），与 SSOT #61 不撞号。"""

    def test_extract_4B_page_matches(self):
        out = assemble.extract_business_rules(SAMPLE_SPEC_4B, "M01", "P01")
        assert "单用户最多收藏 50 个项目" in out
        assert "项目卡片标题截断超过 30 字符" in out
        # 不应污染相邻页内容
        assert "编辑权限" not in out

    def test_extract_4B_second_page(self):
        out = assemble.extract_business_rules(SAMPLE_SPEC_4B, "M01", "P02")
        assert "编辑权限仅限创建者本人" in out
        assert "单用户最多收藏" not in out

    def test_extract_4B_module_isolation(self):
        """跨模块隔离：M01 的 .4B 与 M02 的 .4B 不串"""
        out_m01 = assemble.extract_business_rules(SAMPLE_SPEC_4B, "M01", "P01")
        out_m02 = assemble.extract_business_rules(SAMPLE_SPEC_4B, "M02", "P01")
        assert "单用户最多收藏" in out_m01
        assert "报价单字段长度" in out_m02
        assert "报价单字段长度" not in out_m01
        assert "单用户最多收藏" not in out_m02

    def test_extract_4B_missing_section_graceful(self):
        """spec 完全无 .4B 段 → 返回 "" 不抛"""
        out = assemble.extract_business_rules("# 无 4B 段", "M01", "P01")
        assert out == ""

    def test_extract_4B_missing_page_graceful(self):
        """段存在但页面不在分组 → 返回 ""（precheck S4-49 兜底）"""
        out = assemble.extract_business_rules(SAMPLE_SPEC_4B, "M01", "P99")
        assert out == ""


# ── C2-2 extract_data_scale ─────────────────────────────────────────────────

class TestExtractDataScale:
    """NB-WE-01：段头字面 `.5B`（非 `.5`）。"""

    def test_extract_5B_page_matches(self):
        out = assemble.extract_data_scale(SAMPLE_SPEC_4B, "M01", "P01")
        assert "单用户数据量：≤ 200 项" in out
        assert "单次返回量：分页 20" in out

    def test_extract_5B_display_only_page(self):
        """纯展示页：三维度 — 占位"""
        out = assemble.extract_data_scale(SAMPLE_SPEC_4B, "M01", "P02")
        assert "—" in out

    def test_extract_5B_missing_graceful(self):
        out = assemble.extract_data_scale("# 无 5B", "M01", "P01")
        assert out == ""


# ── C2-3 extract_gherkin ────────────────────────────────────────────────────

class TestExtractGherkin:
    """双状态锚格式适配（与 check_spec_gherkin_completeness 同源）。"""

    def test_extract_gherkin_old_format(self):
        """旧格式 **P01-default**：状态名 = "default" """
        out = assemble.extract_gherkin(SAMPLE_SPEC_4B, "M01", "P01", "default")
        assert "Given 用户已登录" in out
        assert "When 用户访问 /projects" in out
        assert "Then 显示项目卡片网格" in out
        assert "And  接口返回数据时长 ≤ 1s" in out

    def test_extract_gherkin_state_isolation(self):
        """不同 state 不串"""
        p01 = assemble.extract_gherkin(SAMPLE_SPEC_4B, "M01", "P01", "default")
        p02 = assemble.extract_gherkin(SAMPLE_SPEC_4B, "M01", "P02", "default")
        # P02 应不含 P01 的 Gherkin（"用户已登录" 仅 P01 有）
        assert "用户已登录" in p01
        assert "用户已登录" not in p02
        # P02 应含其专属内容
        assert "用户点击项目卡片" in p02

    def test_extract_gherkin_missing_section(self):
        out = assemble.extract_gherkin("# 无 7 段", "M01", "P01", "default")
        assert out == ""

    def test_extract_gherkin_missing_state(self):
        """状态名不存在 → ""（不抛错）"""
        out = assemble.extract_gherkin(
            SAMPLE_SPEC_4B, "M01", "P01", "nonexistent_state"
        )
        assert out == ""


# ── C2-8 extract_main_page ──────────────────────────────────────────────────

class TestExtractMainPage:
    def test_extract_main_page_full_fields(self):
        priority, main_page, fname = assemble.extract_main_page(
            SAMPLE_SPEC_F_SECTIONS, "F-001"
        )
        assert priority == "P0"
        assert main_page == "P-01"
        assert fname == "项目管理"

    def test_extract_main_page_missing_main_field(self):
        """F-xxx 节缺「主页面」字段 → main_page == ""（优雅降级）"""
        priority, main_page, fname = assemble.extract_main_page(
            SAMPLE_SPEC_F_SECTIONS, "F-003"
        )
        assert priority == "P2"
        assert main_page == ""  # 缺失
        assert fname == "缺主页面字段"

    def test_extract_main_page_missing_section(self):
        """F-xxx 节本身不存在 → 全 ""（不抛错）"""
        priority, main_page, fname = assemble.extract_main_page(
            SAMPLE_SPEC_F_SECTIONS, "F-999"
        )
        assert priority == "" and main_page == "" and fname == ""


# ── C2-4 inject_c4_into_interaction_card ────────────────────────────────────

class TestInjectC4IntoInteractionCard:
    def test_inject_c4_appends_after_c3(self):
        """C-4 注入位置：interaction-card 末尾（C-3 后）"""
        c4 = (
            '<div class="data-sub-title">业务契约</div>\n'
            '<ul class="c4-business-rules"><li>测试规则</li></ul>'
        )
        out = assemble.inject_c4_into_interaction_card(
            SAMPLE_INTERACTION_CARD_FRAME, c4, "H-M01-P01-default"
        )
        assert "[C4-START: H-M01-P01-default]" in out
        assert "测试规则" in out
        assert "[C4-END: H-M01-P01-default]" in out
        # C-3 表格内容未被破坏
        assert "登录按钮" in out

    def test_inject_c4_idempotent(self):
        """重入幂等：C4-START/END 已存在 → 替换中间内容"""
        c4_v1 = '<div class="data-sub-title">业务契约</div>\n<p>V1</p>'
        c4_v2 = '<div class="data-sub-title">业务契约</div>\n<p>V2</p>'
        once = assemble.inject_c4_into_interaction_card(
            SAMPLE_INTERACTION_CARD_FRAME, c4_v1, "H-M01-P01-default"
        )
        twice = assemble.inject_c4_into_interaction_card(
            once, c4_v2, "H-M01-P01-default"
        )
        assert "V2" in twice
        assert "V1" not in twice
        # 起始/结束包裹只出现一次
        assert twice.count("[C4-START: H-M01-P01-default]") == 1
        assert twice.count("[C4-END: H-M01-P01-default]") == 1

    def test_inject_c4_no_interaction_card_graceful(self):
        """无 interaction-card → 返回原 html 不抛"""
        out = assemble.inject_c4_into_interaction_card(
            "<div>无交互卡</div>", "<div>C4</div>", "X"
        )
        assert out == "<div>无交互卡</div>"

    def test_inject_c4_empty_content_skipped(self):
        """C-4 内容为空 → 跳过注入（不污染 frame）"""
        out = assemble.inject_c4_into_interaction_card(
            SAMPLE_INTERACTION_CARD_FRAME, "", "H-M01-P01-default"
        )
        assert "[C4-START" not in out
        assert out == SAMPLE_INTERACTION_CARD_FRAME


# ── C2-5 build_function_overview_index ──────────────────────────────────────

class TestBuildFunctionOverviewIndex:
    def test_build_index_basic(self):
        """4 列 schema + F-001/F-002/F-003 全部入表"""
        out = assemble.build_function_overview_index(SAMPLE_SPEC_F_SECTIONS)
        # 表头 4 列
        assert "<th>编号</th>" in out
        assert "<th>功能名</th>" in out
        assert "<th>优先级</th>" in out
        assert "<th>主页面</th>" in out
        # 3 行数据
        assert "F-001" in out
        assert "F-002" in out
        assert "F-003" in out
        assert "项目管理" in out

    def test_build_index_priority_tag(self):
        out = assemble.build_function_overview_index(SAMPLE_SPEC_F_SECTIONS)
        assert 'class="priority-tag"' in out
        assert ">P0<" in out
        assert ">P1<" in out

    def test_build_index_missing_main_page_em_dash(self):
        """F-003 缺主页面字段 → 主页面列填「—」"""
        out = assemble.build_function_overview_index(SAMPLE_SPEC_F_SECTIONS)
        # F-003 行应含 "—"（主页面列）
        assert "F-003" in out
        assert "—" in out

    def test_build_index_empty_spec(self):
        """spec 无 F-xxx 节 → 输出空表 + 占位说明"""
        out = assemble.build_function_overview_index("# 无 F-xxx")
        assert "无 F-xxx 节" in out or "F-xxx" in out
        assert "<thead>" in out  # 表头仍在


# ── C2-5b build_function_overview_index_with_jump（接 scaffold modules）─────

class TestBuildFunctionOverviewIndexWithJump:
    def test_jump_resolves_main_page_prd_id(self):
        """主页面 P-XX → prd_id 解析成 onclick"""
        modules = [
            {
                "id": "M01",
                "pages": [
                    {
                        "id": "P01",
                        "name": "项目首页",
                        "states": [{"prd_id": "H-M01-P01-default", "name": "default"}],
                    },
                    {
                        "id": "P02",
                        "name": "项目详情",
                        "states": [{"prd_id": "H-M01-P02-default", "name": "default"}],
                    },
                ],
            }
        ]
        out = assemble.build_function_overview_index_with_jump(
            SAMPLE_SPEC_F_SECTIONS, modules
        )
        # 主页面 P-01 应解析为 H-M01-P01-default onclick
        assert "showSection('H-M01-P01-default')" in out
        # 应含页面名 label
        assert "项目首页" in out

    def test_jump_unresolvable_falls_back_to_literal(self):
        """主页面 ID 在 modules 中无匹配 → 填字面（无 onclick）"""
        modules = []  # 空 modules
        out = assemble.build_function_overview_index_with_jump(
            SAMPLE_SPEC_F_SECTIONS, modules
        )
        # 应不含 onclick（因解析失败）
        assert "showSection(" not in out
        # 应仍显示主页面字面 "P-01"
        assert "P-01" in out

    def test_jump_3digit_padded_form(self):
        """议题 1 治本（SSOT #67）：spec.md 用 3 位前导零 P-002 / scaffold 用 P02 也能匹配"""
        modules = [
            {
                "id": "M01",
                "pages": [
                    {
                        "id": "P02",
                        "name": "项目详情",
                        "states": [{"prd_id": "H-M01-P02-default", "name": "default"}],
                    }
                ],
            }
        ]
        # spec 用 P-002（3 位前导零）
        spec_with_3digit = """
#### F-001：测试功能
- **优先级**：P0　｜　**所属旅程**：旅程一
- **主页面**：P-002
- **简述**：3 位前导零主页面写法测试
"""
        out = assemble.build_function_overview_index_with_jump(
            spec_with_3digit, modules
        )
        # 议题 1 治本验证：P-002 应解析到 H-M01-P02-default 跳转
        assert "showSection('H-M01-P02-default')" in out

    def test_jump_involved_pages_fallback_when_main_missing(self):
        """议题 1 治本（fallback）：主页面字段缺失 → 用涉及页面首项作 prd_id 解析源"""
        modules = [
            {
                "id": "M01",
                "pages": [
                    {
                        "id": "P02",
                        "name": "项目详情",
                        "states": [{"prd_id": "H-M01-P02-default", "name": "default"}],
                    }
                ],
            }
        ]
        # spec F-xxx 缺主页面字段，但有涉及页面
        spec_no_main = """
#### F-001：测试功能
- **优先级**：P0　｜　**所属旅程**：旅程一
- **涉及页面**：P-02 项目详情页
- **简述**：测试 main 字段缺失 fallback
"""
        out = assemble.build_function_overview_index_with_jump(
            spec_no_main, modules
        )
        # 议题 1 治本：涉及页面首项 P-02 作 fallback 解析 → 输出 <a>
        assert "showSection('H-M01-P02-default')" in out


class TestPidFormsHelper:
    """议题 1 / SSOT #67 _pid_forms 多形态归一化辅助函数。"""

    def test_basic_two_digit_form(self):
        """P02 → 6 形态（覆盖 P2/P-2/P02/P-02/P002/P-002）"""
        forms = assemble._pid_forms("P02")
        assert "P02" in forms
        assert "P-02" in forms
        assert "P2" in forms
        assert "P-2" in forms
        assert "P002" in forms
        assert "P-002" in forms

    def test_3digit_form_equivalent_to_2digit(self):
        """P-002 / P02 等价 — 形态集合相同"""
        assert assemble._pid_forms("P-002") == assemble._pid_forms("P02")
        assert assemble._pid_forms("P-2") == assemble._pid_forms("P-002")

    def test_empty_returns_empty(self):
        """空字符串 → 空集合"""
        assert assemble._pid_forms("") == set()

    def test_non_numeric_returns_literal(self):
        """非数字后缀 → 返回原字面集合（不展开）"""
        assert assemble._pid_forms("PXX") == {"PXX"}


# ── C2-6 inject_function_overview_index ─────────────────────────────────────

class TestInjectFunctionOverviewIndex:
    def test_inject_into_placeholder(self):
        """首次注入：替换 [FUNCTION-INDEX] 占位"""
        html = (
            '<section id="spec-feature">'
            '<div class="spec-section">'
            '<div class="spec-header">功能索引</div>'
            '<div class="spec-body"><!-- [FUNCTION-INDEX] --></div>'
            "</div></section>"
        )
        table = '<table><thead><tr><th>编号</th></tr></thead><tbody></tbody></table>'
        out, ok = assemble.inject_function_overview_index(html, table)
        assert ok is True
        assert "[FUNCTION-INDEX-START]" in out
        assert "[FUNCTION-INDEX-END]" in out
        assert "<th>编号</th>" in out

    def test_inject_reentry_idempotent(self):
        """重入幂等：[FUNCTION-INDEX-START/END] 包裹 → 替换中间"""
        html = (
            '<section id="spec-feature">'
            '<div class="spec-body">'
            '<!-- [FUNCTION-INDEX-START] auto-injected by assemble.py -->\n'
            "OLD_TABLE"
            "\n<!-- [FUNCTION-INDEX-END] -->"
            "</div></section>"
        )
        table = "NEW_TABLE_CONTENT"
        out, ok = assemble.inject_function_overview_index(html, table)
        assert ok is True
        assert "NEW_TABLE_CONTENT" in out
        assert "OLD_TABLE" not in out
        # START/END 标记仍各 1 次
        assert out.count("[FUNCTION-INDEX-START]") == 1
        assert out.count("[FUNCTION-INDEX-END]") == 1

    def test_inject_no_spec_feature_section_graceful(self):
        """无 spec-feature section → 返回 (原, False) 不抛"""
        html = "<html><body>无 spec-feature</body></html>"
        out, ok = assemble.inject_function_overview_index(html, "TABLE")
        assert ok is False
        assert out == html

    def test_inject_legacy_article_form_replaced(self):
        """兼容旧 PRD：spec-feature 内含旧 F-xxx article 形态 → 整段替换"""
        html = (
            '<section id="spec-feature">'
            '<div class="spec-section">'
            '<div class="spec-header">功能需求规格</div>'
            '<div class="spec-body">'
            '<article><h4>F-001</h4><p>旧 article 详情</p></article>'
            "</div></div></section>"
        )
        table = '<table>NEW</table>'
        out, ok = assemble.inject_function_overview_index(html, table)
        assert ok is True
        # 新表格应取代旧 article 内容
        assert "[FUNCTION-INDEX-START]" in out
        assert "NEW" in out
        assert "旧 article 详情" not in out

    # ── 2026-06-04 P0 hot fix 4 联 bug 修复 ────────────────────────────────────

    def test_bug1_header_label_force_replaced(self):
        """Bug 1：spec-header 字面「功能需求规格」强制替换为「功能索引」。"""
        html = (
            '<section id="spec-feature">'
            '<div class="spec-section">'
            '<div class="spec-header">功能需求规格</div>'  # 旧字面
            '<div class="spec-body">'
            '<!-- [FUNCTION-INDEX-START] auto-injected by assemble.py -->\n'
            "OLD\n"
            "<!-- [FUNCTION-INDEX-END] -->"
            "</div></div></section>"
        )
        out, ok = assemble.inject_function_overview_index(html, "<table>NEW</table>")
        assert ok is True
        # Bug 1：旧字面被替换为新字面
        assert '<div class="spec-header">功能索引</div>' in out
        assert '<div class="spec-header">功能需求规格</div>' not in out

    def test_bug1_header_label_not_touched_outside_section(self):
        """Bug 1 边界：spec-feature section 外的同名 header 不应被改。"""
        html = (
            '<section id="spec-other">'
            '<div class="spec-header">功能需求规格</div>'  # 不在 spec-feature 内
            "</section>"
            '<section id="spec-feature">'
            '<div class="spec-section">'
            '<div class="spec-header">功能索引</div>'  # 已是新字面
            '<div class="spec-body"><!-- [FUNCTION-INDEX] --></div>'
            "</div></section>"
        )
        out, ok = assemble.inject_function_overview_index(html, "<table>T</table>")
        assert ok is True
        # spec-other 内的旧字面 header 应保留（非本函数职责范围）
        assert '<section id="spec-other"><div class="spec-header">功能需求规格</div></section>' in out

    def test_bug2_placeholder_upgraded_with_ssot_marker(self):
        """Bug 2：tbody 空时（spec.md 无 F-xxx）占位字面升级为 SSOT #67/#68 醒目提示。"""
        # 复用 build_function_overview_index 空表（无 F-xxx）的输出
        empty_table = assemble.build_function_overview_index("## §三 无 F-xxx 节\n")
        html = (
            '<section id="spec-feature">'
            '<div class="spec-section">'
            '<div class="spec-header">功能索引</div>'
            '<div class="spec-body"><!-- [FUNCTION-INDEX] --></div>'
            "</div></section>"
        )
        out, ok = assemble.inject_function_overview_index(html, empty_table)
        assert ok is True
        # Bug 2：升级后的字面应含 SSOT 锚号 + ⚠️ 警示
        assert "SSOT #67/#68" in out
        assert "⚠️" in out
        # 旧字面 placeholder 不再裸出现（已替换）
        assert "（spec.md 无 F-xxx 节；详 proto_spec_md.md §三.3 功能需求规格 规范）" not in out

    def test_bug3_sub_article_removed(self):
        """Bug 3：spec-feature 内 sub-article `<article id="spec-F0X">` 强制清除。"""
        html = (
            '<section id="spec-feature">'
            '<div class="spec-section">'
            '<div class="spec-header">功能需求规格</div>'
            '<div class="spec-body">'
            '<!-- [FUNCTION-INDEX-START] auto-injected by assemble.py -->\n'
            "TABLE\n"
            "<!-- [FUNCTION-INDEX-END] -->"
            "</div>"
            # Foundation 残留的 sub-article 块（私域 6/quotation-tool 2 实证形态）
            '<article id="spec-F002" class="feature-block">'
            '<div class="feature-title">F-002</div>'
            '<p>残留 1</p>'
            "</article>"
            '<article id="spec-F003" class="feature-block">'
            '<p>残留 2</p>'
            "</article>"
            "</div></section>"
        )
        out, ok = assemble.inject_function_overview_index(html, "<table>NEW</table>")
        assert ok is True
        # Bug 3：sub-article 已清除
        assert 'spec-F002' not in out
        assert 'spec-F003' not in out
        assert '残留 1' not in out
        assert '残留 2' not in out
        # Bug 1 联动：header 字面也被改了
        assert '<div class="spec-header">功能索引</div>' in out

    def test_bug3_sub_article_not_touched_outside_section(self):
        """Bug 3 边界：spec-feature section 外的顶层 article（含 A-XX）不应被误删。"""
        html = (
            '<article id="A-05">外层 article 保留</article>'
            '<section id="spec-feature">'
            '<article id="spec-F001">section 内 sub-article 应清</article>'
            '<div class="spec-section">'
            '<div class="spec-header">功能索引</div>'
            '<div class="spec-body"><!-- [FUNCTION-INDEX] --></div>'
            "</div></section>"
            '<article id="A-06">另一外层 article 保留</article>'
        )
        out, ok = assemble.inject_function_overview_index(html, "<table>T</table>")
        assert ok is True
        # 顶层 article id="A-XX" 不被误删
        assert '<article id="A-05">外层 article 保留</article>' in out
        assert '<article id="A-06">另一外层 article 保留</article>' in out
        # section 内的 sub-article 被清
        assert 'section 内 sub-article 应清' not in out

    def test_bug5_v1_buggy_legacy_orphan_residue_cleaned(self):
        """Bug 5（2026-06-04 P0 hot fix）：v1 老版 inject 残留的孤立尾巴 + div 不平衡修正。

        实证现场：commit 3848b88 时 inject_function_overview_index 用
        `(<div class="spec-body">)(.*?)(</div>)` 非贪婪命中首个 spec-block 的 `</div>` →
        吃掉 F-001 的 `<article>` open 但留下：①F-001 内部 2 个 `<div class="spec-block">`
        ②孤立 `</article>` ③额外的 `</div>` （致 spec-feature body div 收支 -1）。
        后果：layout 提前闭合，所有 frame 跑到 layout 外（私域主页用户报「section 与 layout 平级」）。
        """
        # 模拟 af5cadd commit 时 prd 残留状态：F-001 的 open 已被吃，但内部 spec-block + </article> 残留
        # + 由 v1 buggy 注入吃掉 open 致 div 收支 -1（多 1 个 </div>）
        html = (
            '<section id="spec-feature">'
            '<div class="spec-section">'
            '<div class="spec-header">功能需求规格</div>'
            '<div class="spec-body">'
            '<!-- [FUNCTION-INDEX-START] auto-injected by assemble.py -->\n'
            "OLD_TABLE\n"
            "<!-- [FUNCTION-INDEX-END] -->"
            "</div>"
            # v1 buggy 残留：F-001 内部 spec-block（无 article open）
            '<div class="spec-block"><h4>业务规则</h4><ul><li>R-01 上传 zip</li></ul></div>'
            '<div class="spec-block"><h4>验收标准</h4><pre>Given X</pre></div>'
            # 孤立 </article>（无 open）
            '</article>'
            # 额外的 </div>（致 div 收支 -1）
            '</div>'
            "</div></section>"
        )
        out, ok = assemble.inject_function_overview_index(html, "<table>NEW</table>")
        assert ok is True
        # Bug 5a：孤立 spec-block 清除
        assert '<div class="spec-block">' not in out
        assert '业务规则' not in out
        assert '验收标准' not in out
        # Bug 5b：孤立 </article> 清除
        assert '</article>' not in out
        # Bug 5c：div 平衡（spec-feature section 内 open == close）
        import re as _re
        section_m = _re.search(
            r'<section id="spec-feature">(.*?)</section>', out, _re.DOTALL
        )
        assert section_m is not None
        body = section_m.group(1)
        div_opens = len(_re.findall(r'<div[\s>]', body))
        div_closes = len(_re.findall(r'</div>', body))
        assert div_opens == div_closes, (
            f"spec-feature body div imbalance: opens={div_opens} closes={div_closes}"
        )
        # 新 INDEX 表正常注入
        assert "<table>NEW</table>" in out

    def test_bug5_no_false_positive_on_clean_input(self):
        """Bug 5 反 false positive：干净 prd（无残留）跑 Bug 5 不应误删合法 div / article。"""
        html = (
            '<section id="spec-feature">'
            '<div class="spec-section">'
            '<div class="spec-header">功能索引</div>'
            '<div class="spec-body"><!-- [FUNCTION-INDEX] --></div>'
            "</div></section>"
        )
        out, ok = assemble.inject_function_overview_index(html, "<table>CLEAN</table>")
        assert ok is True
        # spec-section + spec-body 结构完整
        assert '<div class="spec-section">' in out
        assert '<div class="spec-body">' in out
        # 平衡校验
        import re as _re
        section_m = _re.search(
            r'<section id="spec-feature">(.*?)</section>', out, _re.DOTALL
        )
        body = section_m.group(1)
        div_opens = len(_re.findall(r'<div[\s>]', body))
        div_closes = len(_re.findall(r'</div>', body))
        assert div_opens == div_closes

    def test_idempotent_reentry_after_4_bug_fix(self):
        """4 bug fix 后重入幂等：再跑一次不应产生新差异。"""
        html_v1 = (
            '<section id="spec-feature">'
            '<div class="spec-section">'
            '<div class="spec-header">功能需求规格</div>'
            '<div class="spec-body"><!-- [FUNCTION-INDEX] --></div>'
            "</div>"
            '<article id="spec-F001">残留</article>'
            "</section>"
        )
        out1, _ = assemble.inject_function_overview_index(html_v1, "<table>T</table>")
        out2, _ = assemble.inject_function_overview_index(out1, "<table>T</table>")
        # 重入后内容稳定（仅 START/END 包裹块内容刷新，结构不变）
        assert out1 == out2
        # 4 bug 修复痕迹保持
        assert '功能索引' in out2
        assert 'spec-F001' not in out2


# ── C2-7 _build_module_page_to_main_lookup（多页 F 主/副分支）────────────────

class TestBuildModulePageToMainLookup:
    def _modules(self):
        return [
            {
                "id": "M01",
                "pages": [
                    {
                        "id": "P01",
                        "name": "项目首页",
                        "states": [{"prd_id": "H-M01-P01-default", "name": "default"}],
                    },
                    {
                        "id": "P02",
                        "name": "项目详情",
                        "states": [{"prd_id": "H-M01-P02-default", "name": "default"}],
                    },
                ],
            }
        ]

    def test_main_page_not_in_lookup(self):
        """主页面（F-001 主 = P-01）不在 secondary_lookup（避免自反副页面缩略）"""
        lookup = assemble._build_module_page_to_main_lookup(
            SAMPLE_SPEC_F_SECTIONS, self._modules()
        )
        # M01-P01 是 F-001 主页面 → 不应在 lookup（自反过滤）
        assert ("M01", "P01") not in lookup

    def test_secondary_page_in_lookup(self):
        """副页面（F-001 涉及 P-02，主 = P-01）→ 在 lookup，跳转目标 = 主页 prd_id"""
        lookup = assemble._build_module_page_to_main_lookup(
            SAMPLE_SPEC_F_SECTIONS, self._modules()
        )
        # F-001 涉及 P-01, P-02；主页 = P-01 → P02 应在 lookup 指向 P01
        assert ("M01", "P02") in lookup
        main_prd_id, main_label, main_name = lookup[("M01", "P02")]
        assert main_prd_id == "H-M01-P01-default"
        assert "P-01" in main_label and "项目首页" in main_label


# ── C2-7 inject_c4_for_module（主/副双分支总入口）────────────────────────────

class TestInjectC4ForModule:
    def _modules(self):
        return [
            {
                "id": "M01",
                "pages": [
                    {
                        "id": "P01",
                        "name": "项目首页",
                        "states": [{"prd_id": "H-M01-P01-default", "name": "default"}],
                    },
                    {
                        "id": "P02",
                        "name": "项目详情",
                        "states": [{"prd_id": "H-M01-P02-default", "name": "default"}],
                    },
                ],
            }
        ]

    def test_main_page_full_c4(self):
        """主页面（P-01 是 F-001 主页）→ 注入全量 C-4（业务规则 / 数据规模 / Gherkin）"""
        lookup = assemble._build_module_page_to_main_lookup(
            SAMPLE_SPEC_F_SECTIONS, self._modules()
        )
        out = assemble.inject_c4_for_module(
            SAMPLE_INTERACTION_CARD_FRAME,
            SAMPLE_SPEC_4B,
            "M01",
            "P01",
            "default",
            "H-M01-P01-default",
            lookup,
        )
        # 全量内容（业务规则 + 数据规模 + Gherkin）
        # 议题 2A：C-4.A 改 <table>（业务规则文本仍可 grep）
        assert "单用户最多收藏 50 个项目" in out
        # 议题 2A：C-4.B 改 <table>，维度 + 值分列，原 "维度：值" 字面拆为 <td>维度</td><td>值</td>
        assert "<td>单用户数据量</td>" in out
        assert "≤ 200 项" in out
        assert "Given 用户已登录" in out
        # 议题 2A：C-4.A/.B 必为表格 + C-4.C 必为 pre.gherkin
        assert '<table class="c4-business-rules">' in out
        assert '<table class="c4-data-scale">' in out
        assert '<pre class="gherkin">' in out
        # C-4 start/end 标记
        assert "[C4-START: H-M01-P01-default]" in out
        # 应有 4 子标题
        assert "业务契约" in out
        assert "业务规则" in out
        assert "数据规模" in out
        assert "验收标准" in out

    def test_secondary_page_cross_page_note(self):
        """副页面（P-02 涉及 F-001，主 = P-01）→ 注入缩略跳转链接，不复制全量"""
        lookup = assemble._build_module_page_to_main_lookup(
            SAMPLE_SPEC_F_SECTIONS, self._modules()
        )
        out = assemble.inject_c4_for_module(
            SAMPLE_INTERACTION_CARD_FRAME,
            SAMPLE_SPEC_4B,
            "M01",
            "P02",
            "default",
            "H-M01-P02-default",
            lookup,
        )
        # 应含 cross-page-note 跳转 + 主页面 prd_id
        assert "c4-cross-page-note" in out
        assert "showSection('H-M01-P01-default')" in out
        # 不应含全量业务规则（副页面不复制）
        assert "单用户最多收藏 50 个项目" not in out

    def test_main_page_with_missing_spec_segments_uses_placeholder(self):
        """spec 缺 .4B/.5B/.7 段 → C-4 注入占位说明（不抛错）"""
        lookup = {}
        out = assemble.inject_c4_for_module(
            SAMPLE_INTERACTION_CARD_FRAME,
            "# 无任何 .4B/.5B/.7 段",
            "M99",
            "P99",
            "default",
            "H-M99-P99-default",
            lookup,
        )
        # 注入成功 + 占位说明出现
        assert "[C4-START: H-M99-P99-default]" in out
        # 三段都应有占位
        assert "本帧无业务规则" in out
        assert "本帧无数据规模" in out
        assert "本帧无验收标准" in out


# ── NB-2A-01 选项 C: _strip_inline_font_size_in_interaction_cards ───────────

class TestStripInlineFontSizeInInteractionCards:
    """治"PM 写源 inline font-size 优先级 > CSS 致字号不统一"。

    范围：仅 .interaction-card div 内的 style 属性；其他位置 PM 故意写的 inline 字号
    （如 frame-wrapper PRD 元数据）应保留。
    """

    def test_strip_solo_font_size_in_card(self):
        """单 font-size 声明（没其他 inline 属性）→ 整个 style 属性删除"""
        html = (
            '<div class="interaction-card">'
            '<p style="font-size:12px;">内容</p>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 1
        assert "font-size" not in out
        # style 属性整个被删（空 style 无意义）
        assert 'style="' not in out
        assert "<p>内容</p>" in out

    def test_strip_font_size_preserves_other_inline_props(self):
        """font-size 在中间 → 删除该声明，保留其他声明（color / padding 等）"""
        html = (
            '<div class="interaction-card">'
            '<p style="color:red; font-size:11px; padding:8px">内容</p>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 1
        assert "font-size" not in out
        assert "color:red" in out
        assert "padding:8px" in out

    def test_strip_font_size_at_start(self):
        """font-size 在 style 开头 → 删除该声明，保留后续"""
        html = (
            '<div class="interaction-card">'
            '<span style="font-size:11px; color:#999;">A</span>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 1
        assert "font-size" not in out
        assert "color:#999" in out

    def test_strip_font_size_at_end(self):
        """font-size 在 style 末尾 → 删除该声明，保留前置"""
        html = (
            '<div class="interaction-card">'
            '<span style="color:#999; font-size:11px">A</span>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 1
        assert "font-size" not in out
        assert "color:#999" in out

    def test_strip_font_size_with_spaces(self):
        """`font-size : 12 px` 带空格变体也匹配"""
        html = (
            '<div class="interaction-card">'
            '<span style="font-size : 12px ; color:red">A</span>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 1
        assert "font-size" not in out
        assert "color:red" in out

    def test_strip_outside_card_preserved(self):
        """interaction-card 外部 inline font-size 应保留（PM 故意写）"""
        html = (
            '<div class="frame-wrapper">'
            '<span style="font-size:11px;">外部元数据</span>'
            "</div>"
            '<div class="interaction-card">'
            '<p style="font-size:12px;">卡内</p>'
            "</div>"
            '<div class="other">'
            '<span style="font-size:13px;">外部</span>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 1  # 只剥离 card 内 1 处
        # 外部 font-size 仍在
        assert "font-size:11px" in out
        assert "font-size:13px" in out
        # 卡内 font-size 已删
        assert "font-size:12px" not in out

    def test_strip_nested_div_in_card(self):
        """nesting-aware：card 内嵌套 div / table / 多层 → 全范围扫"""
        html = (
            '<div class="interaction-card">'
            '<div class="data-sub-title">业务契约</div>'
            '<table class="c4-business-rules">'
            '<tr><td style="font-size:11px;">R-01 规则</td></tr>'
            "</table>"
            '<div class="inner-block">'
            '<span style="font-size:12px;color:#666;">嵌套深</span>'
            "</div>"
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 2
        assert "font-size" not in out
        assert "color:#666" in out  # 保留其他声明

    def test_idempotent_repeat_strip(self):
        """重入幂等：再跑一次无新作用（已无 font-size → regex 不匹配）"""
        html = (
            '<div class="interaction-card">'
            '<p style="font-size:12px; color:red">A</p>'
            "</div>"
        )
        once, n1 = assemble._strip_inline_font_size_in_interaction_cards(html)
        twice, n2 = assemble._strip_inline_font_size_in_interaction_cards(once)
        assert n1 == 1
        assert n2 == 0
        assert once == twice

    def test_strip_multiple_font_size_same_style(self):
        """同一 style 内多个 font-size（罕见但需鲁棒）→ 全清"""
        html = (
            '<div class="interaction-card">'
            '<p style="font-size:11px; color:red; font-size:13px">A</p>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 2
        assert "font-size" not in out
        assert "color:red" in out

    def test_strip_multiple_cards(self):
        """多个 interaction-card 块 → 各自独立剥离"""
        html = (
            '<div class="interaction-card">'
            '<p style="font-size:11px;">A</p>'
            "</div>"
            '<div class="interaction-card">'
            '<p style="font-size:12px;">B</p>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 2
        assert "font-size" not in out

    def test_strip_card_with_extra_modifier_class(self):
        """class 含其他 modifier 也应识别（如 `interaction-card large` / `card-1 interaction-card`）"""
        html = (
            '<div class="card-1 interaction-card extra">'
            '<p style="font-size:12px;">A</p>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 1
        assert "font-size" not in out

    def test_no_change_when_no_card(self):
        """无 interaction-card → 不动任何 font-size"""
        html = (
            '<div class="frame-wrapper">'
            '<p style="font-size:11px;">仅 frame 内</p>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 0
        assert out == html

    def test_no_change_when_no_inline_font_size(self):
        """card 内无 inline font-size（已统一走 CSS） → 不动"""
        html = (
            '<div class="interaction-card">'
            '<p style="color:red">A</p>'
            '<table class="c4-business-rules"><tr><td>R-01</td></tr></table>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 0
        assert out == html

    def test_strip_realistic_c4_sample(self):
        """议题 2A C-4 表格化后形态：c4-data-scale td 内 inline font-size（假残留）"""
        html = (
            '<div class="interaction-card">'
            '<div class="data-sub-title">业务契约</div>'
            '<table class="c4-business-rules">'
            '<tbody><tr><td style="font-size:11px;color:var(--fb-text-hint);">'
            "单用户最多收藏 50 个项目"
            "</td></tr></tbody>"
            "</table>"
            '<table class="c4-data-scale">'
            '<tbody><tr><td style="font-size:12px;">单用户数据量</td>'
            '<td style="font-size:12px;">≤ 200 项</td></tr></tbody>'
            "</table>"
            '<pre class="gherkin" style="font-size:13px;">'
            "Given 用户已登录"
            "</pre>"
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 4
        assert "font-size" not in out
        # 业务内容仍在
        assert "单用户最多收藏 50 个项目" in out
        assert "≤ 200 项" in out
        assert "Given 用户已登录" in out
        # 保留 color 声明
        assert "color:var(--fb-text-hint)" in out

    def test_strip_em_rem_var_values(self):
        """font-size 值含 em / rem / var() 等也清"""
        html = (
            '<div class="interaction-card">'
            '<p style="font-size: 1.2em; color:red">A</p>'
            '<p style="font-size: var(--text-md); padding:4px">B</p>'
            "</div>"
        )
        out, n = assemble._strip_inline_font_size_in_interaction_cards(html)
        assert n == 2
        assert "font-size" not in out
        assert "color:red" in out
        assert "padding:4px" in out


# ── 议题 4：C-4.A thead 列名「规则描述」（避免与子标题字面重复）──────────────

class TestC4ARulesHeadDescription:
    """议题 4：thead 列名「规则描述」（非「业务规则」）— 避免与外层 .c4-sub-title「业务规则」
    字面重复（同字面出现 2 次视觉冗余）。
    """

    def test_thead_uses_rule_description(self):
        """C-4.A 表格 thead 列 2 字面为「规则描述」（非「业务规则」）"""
        out = assemble._build_c4_content_html(
            business_rules_md="#### P01 页面\n\n- 单用户最多 50 项",
            data_scale_md="",
            gherkin_text="",
        )
        # 子标题保留「业务规则」字面
        assert '<div class="c4-sub-title">业务规则</div>' in out
        # thead 列 2 改名「规则描述」
        assert "<th>规则描述</th>" in out
        # thead 不再含「业务规则」字面（已迁移到子标题）
        assert "<th>业务规则</th>" not in out

    def test_thead_rule_description_with_empty_rules(self):
        """业务规则为空时占位回退也用「规则描述」列名"""
        out = assemble._build_c4_content_html(
            business_rules_md="",
            data_scale_md="",
            gherkin_text="",
        )
        assert "<th>规则描述</th>" in out
        assert "<th>业务规则</th>" not in out

    def test_thead_rule_description_with_unparseable_lines(self):
        """业务规则有内容但无可解析 bullet → 占位回退也用「规则描述」"""
        out = assemble._build_c4_content_html(
            business_rules_md="散文段无 bullet",
            data_scale_md="",
            gherkin_text="",
        )
        assert "<th>规则描述</th>" in out
        assert "<th>业务规则</th>" not in out

    def test_data_scale_head_unchanged(self):
        """C-4.B 数据规模 thead「维度|值」字面不与子标题「数据规模」重复 → 不动"""
        out = assemble._build_c4_content_html(
            business_rules_md="",
            data_scale_md="#### P01 页面\n\n- 单用户数据量：≤ 200 项",
            gherkin_text="",
        )
        # 子标题
        assert '<div class="c4-sub-title">数据规模</div>' in out
        # thead 仍是「维度」+「值」字面（与「数据规模」不重复）
        assert "<th>维度</th>" in out
        assert "<th>值</th>" in out


# ── 议题 8：_split_data_scale 启发式升级（NB-WE-2A-R2-01 P1） ─────────────────


class TestSplitDataScaleHeuristicUpgrade:
    """议题 8（2026-06-04 PM 反审 trust-but-verify 实证）：
    单 dim 一行 bullet 内的 ` / ` 应视为值内业务列举（不再当多 dim 分隔）
    → c4-data-scale 渲染为「维度+值」双列而非 fallback「说明」单列。
    """

    def _render(self, data_scale_md: str) -> str:
        return assemble._build_c4_content_html(
            business_rules_md="",
            data_scale_md=data_scale_md,
            gherkin_text="",
        )

    def test_single_dim_with_slash_in_value_keeps_dual_column(self):
        """议题 8 真因：bullet `- 操作频率：销售典型 3-10 次/天/项目（A / B / C）`
        旧版按 ` / ` 拆 4 段 → 3 段无 dim → fallback 单列；新版整 bullet 视为
        单 dim/val pair（值内 ` / ` 保留）→ 双列 + dim「操作频率」+ val 完整。
        """
        md = (
            "#### P01 页面\n\n"
            "- 单用户数据量：1 项对应 5 字段 + 关联记录（典型 1-10 条 / P95 ≤ 50 条）\n"
            "- 单次返回量：API-X 单次返回完整 payload ≤ 50KB\n"
            "- 操作频率：销售典型 3-10 次/天/项目（创建后回看 / 编辑信息 / 跳转 H5）\n"
        )
        out = self._render(md)
        # 双列（非 fallback 单列）
        assert "<th>维度</th>" in out
        assert "<th>值</th>" in out
        assert "<th>说明</th>" not in out, "应渲染双列，而非 fallback 单列「说明」"
        # 3 个维度都正确提取
        assert "<td>单用户数据量</td>" in out
        assert "<td>单次返回量</td>" in out
        assert "<td>操作频率</td>" in out
        # 值内 ` / ` 保留（不再被拆维度）
        assert "（创建后回看 / 编辑信息 / 跳转 H5）" in out
        assert "（典型 1-10 条 / P95 ≤ 50 条）" in out

    def test_legacy_single_line_multi_dim_now_treated_as_single_dim(self):
        """议题 9 [Should] 反 pattern：单行多 dim 用 `dim1：v1 / dim2：v2 / dim3：v3`
        在新启发式下按主路径解析为「整 bullet = 单 dim/val pair」（首冒号前 dim，
        其后含 ` / ` 的值整段为 val）。这是有意行为 — 议题 9 已在 proto_spec_md.md
        §三.5 .5B 加 [Should] 反 pattern 引导 PM 改用「每 dim 独立 bullet 行」，
        与 [Must] 禁单 dim 值内 ` / ` 一脉相承。
        """
        md = (
            "#### P01 页面\n\n"
            "- 单用户数据量：≤ 200 项 / 单次返回量：50 条/页 / 操作频率：10 次/天\n"
        )
        out = self._render(md)
        # 双列（主路径解析成功）
        assert "<th>维度</th>" in out
        assert "<th>值</th>" in out
        # 首 dim 命中
        assert "<td>单用户数据量</td>" in out
        # 剩余内容作 val 整段保留（含其他 dim 字面）
        assert "≤ 200 项 / 单次返回量：50 条/页 / 操作频率：10 次/天" in out

    def test_prose_no_colon_falls_back(self):
        """完全无冒号散文 bullet → fallback 单列「说明」（precheck S4-XX WARN 兜底）"""
        md = "#### P01 页面\n\n- 数据量较大\n- 操作频繁\n"
        out = self._render(md)
        # 无 dim → fallback 单列
        assert "<th>说明</th>" in out

    def test_split_data_scale_unit_single_dim_keeps_slash(self):
        """`_split_data_scale` 单元：单 dim bullet 内 ` / ` 不再拆维度"""
        result = assemble._build_c4_content_html.__globals__  # access nested fn via the module
        # 直接调用 _build_c4_content_html 内的逻辑路径（已通过上面集成测验证）
        # 此处只补一个最小契约：dim/val 切分后整 bullet 是一对
        md = "#### P01\n\n- 单用户数据量：值含 ` / ` 也保留\n"
        out = self._render(md)
        assert "<td>单用户数据量</td>" in out
        assert "值含 ` / ` 也保留" in out

    def test_empty_dim_falls_back_to_multi_dim_split(self):
        """dim 候选为空（冒号在 bullet 开头）→ 回退多 dim 启发式"""
        md = "#### P01\n\n- ：缺 dim 命名直接给值\n"
        out = self._render(md)
        # 无有效 dim → fallback 单列
        assert "<th>说明</th>" in out or "<td>—</td>" in out


# ── 议题 6：tp-marker 视觉前缀属性注入（SNB-MARKER-VISUAL-PREFIX-T-D-C）──────

class TestInjectTpMarkerSystemAttr:
    """议题 6：扫所有 `<span class="tp-marker">NN</span>` 注入 `data-tp-system="T"/"D"/"C"`
    属性，覆盖 4 种 PM 写源嵌套场景（自身 / 父 / 前兄弟 / 父之前兄弟）。
    """

    def test_classify_tp_system_t(self):
        assert assemble._classify_tp_system("M01-P01-T01") == "T"

    def test_classify_tp_system_d(self):
        assert assemble._classify_tp_system("M01-P01-D02") == "D"

    def test_classify_tp_system_c(self):
        assert assemble._classify_tp_system("M01-P01-C03") == "C"

    def test_classify_tp_system_empty_no_suffix(self):
        """末段不含 T/D/C → 返回空（如 `M01-P01` 容器级 data-tp）"""
        assert assemble._classify_tp_system("M01-P01") == ""

    def test_classify_tp_system_empty_value(self):
        assert assemble._classify_tp_system("") == ""

    def test_scene_a_self_data_tp(self):
        """场景 A：tp-marker 自身带 data-tp → 自取末段"""
        html = '<span class="tp-marker" data-tp="M01-P01-T01">01</span>'
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 1
        assert 'data-tp-system="T"' in out

    def test_scene_b_parent_data_tp_direct(self):
        """场景 B：直接父元素带 data-tp → 用父 data-tp"""
        html = (
            '<button data-tp="M01-P01-T01">+ 新建</button>'
            '<span class="tp-marker">01</span>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 1
        assert 'data-tp-system="T"' in out

    def test_scene_c_sibling_data_tp_with_tp_wrap(self):
        """场景 C：紧邻前兄弟带 data-tp，含 tp-wrap 包裹（最常见 PM 写法）"""
        html = (
            '<span data-tp="M01-P01-D03">A</span>'
            '<span class="tp-wrap"><span class="tp-marker">03</span></span>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 1
        assert 'data-tp-system="D"' in out

    def test_scene_d_chip_data_tp_inside_chip(self):
        """场景 D：chip 内嵌套 — chip 含 data-tp → 内嵌 tp-marker 取 chip data-tp"""
        html = (
            '<span class="fb-chip">进行中 '
            '<span class="fb-chip-close" data-tp="M01-P01-C02">×</span>'
            '<span class="tp-wrap"><span class="tp-marker">02</span></span>'
            '</span>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 1
        assert 'data-tp-system="C"' in out

    def test_no_data_tp_skip_dangling_marker(self):
        """悬空 marker（无邻近 data-tp）→ 不注入"""
        html = '<div>裸文字 <span class="tp-marker">99</span></div>'
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 0
        assert "data-tp-system" not in out

    def test_no_classify_when_data_tp_has_no_t_d_c_suffix(self):
        """data-tp 末段无 T/D/C（如容器级 `M01-P01`）→ 不注入"""
        html = (
            '<div data-tp="M01-P01">容器</div>'
            '<span class="tp-marker">01</span>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 0
        assert "data-tp-system" not in out

    def test_idempotent_already_has_attr(self):
        """已有 data-tp-system → 跳过（幂等）"""
        html = (
            '<span class="tp-marker" data-tp-system="T">01</span>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 0
        # 原属性保留
        assert 'data-tp-system="T"' in out

    def test_idempotent_repeat_call(self):
        """重入幂等：同源 html 跑两次结果不变 + 第二次 n=0"""
        html = (
            '<button data-tp="M01-P01-T01">A</button>'
            '<span class="tp-marker">01</span>'
        )
        once, n1 = assemble._inject_tp_marker_system_attr(html)
        twice, n2 = assemble._inject_tp_marker_system_attr(once)
        assert n1 == 1
        assert n2 == 0
        assert once == twice

    def test_multiple_markers_mixed_systems(self):
        """多个 marker 各自取自己邻近 data-tp 末段（T/D/C 混合）"""
        html = (
            '<button data-tp="M01-P01-T01">A</button>'
            '<span class="tp-marker">01</span>'
            '<span data-tp="M01-P01-D02">B</span>'
            '<span class="tp-wrap"><span class="tp-marker">02</span></span>'
            '<div data-tp="M01-P01-C03">'
            '<span class="tp-marker">03</span>'
            '</div>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 3
        # 三种系都注入
        assert 'data-tp-system="T"' in out
        assert 'data-tp-system="D"' in out
        assert 'data-tp-system="C"' in out

    def test_frame_boundary_no_cross_frame_leakage(self):
        """不跨 frame 边界：前 frame data-tp 不应被后 frame marker 取用"""
        html = (
            '<button data-tp="M01-P01-T01">A</button>'
            '<!-- [/FRAME M01-P01-default] -->'
            '<!-- [FRAME M01-P02-default] -->'
            '<span class="tp-marker">99</span>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        # 后 frame marker 跨边界回溯被截断 → 不注入
        assert n == 0
        assert "data-tp-system" not in out

    def test_class_with_modifier_still_matched(self):
        """class 含其他 modifier 也应识别（如 `tp-marker extra-style`）"""
        html = (
            '<button data-tp="M01-P01-T01">A</button>'
            '<span class="tp-marker extra-class">01</span>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 1
        assert 'data-tp-system="T"' in out

    def test_not_match_tp_marker_substring(self):
        """非 tp-marker 完整 class（如 `.tp-marker-active`）不应误注入"""
        html = (
            '<button data-tp="M01-P01-T01">A</button>'
            '<span class="tp-marker-active">不算 marker</span>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 0
        assert "data-tp-system" not in out

    def test_realistic_sample_from_quotation_tool(self):
        """实证样本（来自 bujue-quotation-tool prd.html L5737-5745 形态）"""
        html = (
            '<div class="fb-list-item" data-tp="M01-P01-C01">'
            '<span class="tp-wrap"><span class="tp-marker">01</span></span>'
            '<div class="fb-list-item-title" data-tp="M01-P01-D01">永和小区</div>'
            '<span class="tp-wrap"><span class="tp-marker">01</span></span>'
            '<div class="fb-list-item-desc" data-tp="M01-P01-D02">张总</div>'
            '<span class="tp-wrap"><span class="tp-marker">02</span></span>'
            '<span class="fb-tag fb-tag-pill" data-tp="M01-P01-T06">进行中</span>'
            '<span class="tp-marker">06</span>'
            '</div>'
        )
        out, n = assemble._inject_tp_marker_system_attr(html)
        # 4 个 tp-marker 全部注入（C/D/D/T 系混合）
        assert n == 4
        # 4 个 data-tp-system 注入字面
        assert out.count('data-tp-system="') == 4
        # 三系都覆盖
        assert 'data-tp-system="T"' in out
        assert 'data-tp-system="D"' in out
        assert 'data-tp-system="C"' in out

    def test_no_markers_in_html(self):
        """无 tp-marker → 返回原 html，n=0"""
        html = '<div>无 marker</div>'
        out, n = assemble._inject_tp_marker_system_attr(html)
        assert n == 0
        assert out == html


# ── 议题 7：sidebar nav 字面 SSOT 重置（NB-WE-2A-R2-02 P1） ─────────────────


class TestOverwriteSpecNavLabelFromTemplate:
    """议题 7（2026-06-04）：assemble 后处理把 sidebar `<div class="sidebar-spec-item"
    data-target="{sid}">` 内 label 强制对齐 SPEC_ITEMS 真源，治"既有 PRD 上线后
    sidebar 仍含旧字面（功能需求规格）"3 仓共性根因。
    """

    def test_replaces_legacy_label(self):
        """旧字面「功能需求规格」→ 新字面「功能索引」"""
        html = (
            '<nav class="sidebar">'
            '<div class="sidebar-spec-item" data-target="spec-feature" '
            'onclick="showSection(\'spec-feature\')">功能需求规格</div>'
            '</nav>'
        )
        out, n = assemble._overwrite_spec_nav_label_from_template(html)
        assert n == 1
        assert "功能需求规格" not in out
        assert ">功能索引<" in out

    def test_idempotent_when_label_already_canonical(self):
        """已是新字面 → 不动 + 计数 0（幂等）"""
        html = (
            '<div class="sidebar-spec-item" data-target="spec-feature" '
            'onclick="showSection(\'spec-feature\')">功能索引</div>'
        )
        out, n = assemble._overwrite_spec_nav_label_from_template(html)
        assert n == 0
        assert out == html

    def test_other_sidebar_items_also_canonicalized(self):
        """其他 sid（spec-background / spec-data 等）同模式幂等校准"""
        html = (
            '<div class="sidebar-spec-item" data-target="spec-data">旧字段名</div>'
            '<div class="sidebar-spec-item" data-target="spec-nonfunc">非功能性需求</div>'
        )
        out, n = assemble._overwrite_spec_nav_label_from_template(html)
        assert n == 2
        assert ">数据字段<" in out
        assert ">非功能需求<" in out

    def test_unknown_sid_unchanged(self):
        """未在 SPEC_NAV_LABEL_OVERRIDE 中的 sid（如 sk-hier）不动"""
        html = (
            '<div class="sidebar-spec-item" data-target="sk-hier">页面层级图</div>'
        )
        out, n = assemble._overwrite_spec_nav_label_from_template(html)
        assert n == 0
        assert out == html

    def test_does_not_touch_spec_header_label(self):
        """spec-feature section 内的 spec-header 字面不受本函数影响
        （由 inject_function_overview_index 单独处理）"""
        html = (
            '<section id="spec-feature">'
            '<div class="spec-header">功能需求规格</div>'
            '</section>'
            '<div class="sidebar-spec-item" data-target="spec-feature">功能需求规格</div>'
        )
        out, n = assemble._overwrite_spec_nav_label_from_template(html)
        # 仅替换 sidebar 内 1 处，section 内 spec-header 字面保留（让 inject_func 处理）
        assert n == 1
        assert '<div class="spec-header">功能需求规格</div>' in out
        assert '>功能索引</div>' in out

    def test_no_sidebar_in_html(self):
        """html 无 sidebar-spec-item → 返回原 html + n=0"""
        html = '<div>无 sidebar</div>'
        out, n = assemble._overwrite_spec_nav_label_from_template(html)
        assert n == 0
        assert out == html


# ── 议题 12 P3 / SSOT #69 C-2.B 无 C 触点绑定场景派生（方案 c）─────────────────


def _make_section_with_card(
    section_id: str,
    page_name: str,
    card_title_state: str,
    card_inner: str,
    has_c_tp: bool = False,
) -> str:
    """构造一个完整 proto-section，含 frame body + interaction-card；用于测试派生"""
    c_tp_button = (
        '<button data-tp="M01-P01-C01">卡片</button>' if has_c_tp else ''
    )
    return (
        f'<section id="{section_id}" class="proto-section">'
        f'<div class="section-header">'
        f'<div class="section-meta">'
        f'<div class="section-title-row">'
        f'<span class="page-id">M10 / P13</span>'
        f'<span class="page-name">{page_name}</span>'
        f'</div></div></div>'
        f'<div class="frame-card"><div class="frame-wrapper">{c_tp_button}</div></div>'
        f'<div class="interaction-card">'
        f'<div class="card-title">交互说明 — {card_title_state}</div>'
        f'{card_inner}'
        f'</div>'
        f'</section>'
    )


# C-2.B 字段子表 5 列（与 _C2B_THEAD_COLS 同源）
_C2B_FIELD_TABLE = (
    '<table>'
    '<thead><tr>'
    '<th>D 触点 ID</th><th>字段名</th><th>接口字段</th><th>显示格式</th><th>空值处理</th>'
    '</tr></thead>'
    '<tbody>'
    '<tr><td>D01</td><td>名称</td><td>name</td><td>文本</td><td>—</td></tr>'
    '</tbody>'
    '</table>'
)


class TestInjectC2BSubtitleForNoCBinding:
    """议题 12 P3 / SSOT #69 — 无 C 触点绑定场景派生 C-2.B 字段说明 sub-title

    背景：M10 admin-default 等纯字段表场景（页面无 `data-tp="...-C\\d+"` 元素绑定）
    PM 不知 sub-title 该写什么；本函数检测「无 C 触点绑定 + C-2.B 字段表前缺 sub-title」
    自动派生「字段说明 — {派生名}」。
    """

    def test_inject_with_page_name(self):
        """优先级 B：从 page-name 派生「字段说明 — {页面名}」"""
        html = _make_section_with_card(
            section_id="H-M10-P13-admin-default",
            page_name="自定义字段管理页",
            card_title_state="admin-default 管理员默认列表态",
            card_inner=_C2B_FIELD_TABLE,
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        assert n == 1
        assert '<div class="data-sub-title">字段说明 — 自定义字段管理页</div>' in out
        # 派生 sub-title 应在 <table> 前
        assert out.index('字段说明 — 自定义字段管理页') < out.index('<table>')

    def test_inject_falls_back_to_card_title_state_when_no_page_name(self):
        """优先级 B 兜底：page-name 缺失 → 用 card-title 状态名派生"""
        # 不用 helper，直接构造无 page-name 但有 card-title 的 section
        html = (
            '<section id="H-M10-P13-loading" class="proto-section">'
            '<div class="section-header"></div>'  # 无 page-name
            '<div class="frame-card">空</div>'
            '<div class="interaction-card">'
            '<div class="card-title">交互说明 — loading 加载态</div>'
            + _C2B_FIELD_TABLE +
            '</div>'
            '</section>'
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        assert n == 1
        assert '<div class="data-sub-title">字段说明 — loading 加载态</div>' in out

    def test_inject_falls_back_to_section_id_when_no_page_name_no_card_title(self):
        """优先级 A：无 page-name + 无 card-title → 用 MXX-PYY 派生"""
        html = (
            '<section id="H-M10-P13-default" class="proto-section">'
            '<div class="section-header"></div>'
            '<div class="frame-card">空</div>'
            '<div class="interaction-card">'
            # 无 card-title
            + _C2B_FIELD_TABLE +
            '</div>'
            '</section>'
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        assert n == 1
        assert '<div class="data-sub-title">字段说明 — M10-P13</div>' in out

    def test_skip_when_c_tp_binding_present(self):
        """有 C 触点绑定 → 跳过（规范原 schema 适用，不派生）"""
        html = _make_section_with_card(
            section_id="H-M01-P01-default",
            page_name="项目首页",
            card_title_state="default 默认态",
            card_inner=_C2B_FIELD_TABLE,
            has_c_tp=True,  # frame 内含 data-tp="M01-P01-C01"
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        assert n == 0
        assert '字段说明 —' not in out

    def test_idempotent_when_subtitle_already_present(self):
        """idempotent：已含「字段说明」sub-title 不动 + 计数 0"""
        existing_subtitle = '<div class="data-sub-title">字段说明 — C01 项目卡片</div>'
        html = _make_section_with_card(
            section_id="H-M10-P13-admin-default",
            page_name="自定义字段管理页",
            card_title_state="admin-default",
            card_inner=existing_subtitle + _C2B_FIELD_TABLE,
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        assert n == 0
        # PM 写源保留
        assert '字段说明 — C01 项目卡片' in out
        # 不重复派生「字段说明 — 自定义字段管理页」
        assert '字段说明 — 自定义字段管理页' not in out

    def test_idempotent_repeat_call(self):
        """重入幂等：连续两次跑结果一致"""
        html = _make_section_with_card(
            section_id="H-M10-P13-admin-default",
            page_name="自定义字段管理页",
            card_title_state="admin-default",
            card_inner=_C2B_FIELD_TABLE,
            has_c_tp=False,
        )
        once, n1 = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        twice, n2 = assemble._inject_c2b_subtitle_for_no_c_binding(once)
        assert n1 == 1
        assert n2 == 0  # 第二跑已 idempotent 跳过
        assert once == twice

    def test_no_interaction_card_graceful(self):
        """proto-section 内无 interaction-card → 跳过"""
        html = (
            '<section id="H-M10-P13-empty" class="proto-section">'
            '<div class="section-header"></div>'
            '</section>'
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        assert n == 0
        assert out == html

    def test_no_c2b_field_table_skipped(self):
        """interaction-card 无 C-2.B 字段子表（如只含 C-1 列表回显说明）→ 跳过"""
        # 模拟 C-1 thead（属性/说明），不是 C-2.B 的「D 触点 ID」+「字段名」
        c1_table = (
            '<table>'
            '<thead><tr><th>属性</th><th>说明</th></tr></thead>'
            '<tbody><tr><td>排序</td><td>desc</td></tr></tbody>'
            '</table>'
        )
        html = _make_section_with_card(
            section_id="H-M10-P13-admin-default",
            page_name="自定义字段管理页",
            card_title_state="admin-default",
            card_inner=c1_table,
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        assert n == 0
        assert '字段说明 —' not in out

    def test_no_proto_section_graceful(self):
        """html 无 proto-section 边界 → 返回原 html + n=0"""
        html = '<div>裸 div 无 section</div>'
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        assert n == 0
        assert out == html

    def test_compatible_with_s4_59_regex(self):
        """派生 sub-title 容器格式与 precheck S4-59 _C2B_SUB_TITLE_RE 兼容
        （precheck S4-59 会捕获派生形态作为合法 C-2.B sub-title）"""
        import re
        html = _make_section_with_card(
            section_id="H-M10-P13-admin-default",
            page_name="自定义字段管理页",
            card_title_state="admin-default",
            card_inner=_C2B_FIELD_TABLE,
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(html)
        assert n == 1
        # 与 precheck_stage4._C2B_SUB_TITLE_RE 同源 regex
        s4_59_regex = re.compile(
            r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>[^<]*字段说明[^<]*</div>',
            re.IGNORECASE,
        )
        assert s4_59_regex.search(out) is not None


# ── 议题 13：C-3 / C-4.A 序号样式统一（tp-num 包裹 + CSS 去装饰） ───────────────


class TestC4ARulesTpNumWrapping:
    """议题 13：C-4.A 业务规则序号字面与 C-3 触点交互序号字面统一表达
    （`<span class="tp-num">N</span>` 包裹 + CSS 去徽章装饰，普通文字 + mono 字体）。
    """

    def test_c4a_rules_serial_wrapped_with_tp_num_span(self):
        """C-4.A 业务规则表 tbody 序号包 `<span class="tp-num">N</span>`"""
        out = assemble._build_c4_content_html(
            business_rules_md="#### P01 页面\n\n- 规则 A\n- 规则 B\n- 规则 C",
            data_scale_md="",
            gherkin_text="",
        )
        # 序号字面包 tp-num
        assert '<td><span class="tp-num">1</span></td>' in out
        assert '<td><span class="tp-num">2</span></td>' in out
        assert '<td><span class="tp-num">3</span></td>' in out
        # 旧字面 <td>1</td> 不再出现
        assert "<td>1</td>" not in out
        assert "<td>2</td>" not in out

    def test_c4a_empty_placeholder_uses_em_dash_not_tp_num(self):
        """业务规则为空时占位 `—` 不需 tp-num 包裹（非真序号）"""
        out = assemble._build_c4_content_html(
            business_rules_md="",
            data_scale_md="",
            gherkin_text="",
        )
        # 占位用 `<td>—</td>`，无 tp-num
        assert "<td>—</td>" in out


class TestPrdTemplateTpNumCssNoBadgeDecoration:
    """议题 13：prd_template.html `.tp-num` CSS 已去除徽章装饰
    （background / padding / 圆角徽章规则不再用于 .tp-num — 仅保留 mono + bold + tabular-nums）。
    """

    def _read_template(self) -> str:
        from pathlib import Path
        repo = Path(__file__).resolve().parents[3]
        return (repo / "pm-workflow" / "rules" / "prd_template.html").read_text(
            encoding="utf-8"
        )

    def test_tp_num_css_has_no_background(self):
        """.tp-num CSS 块不含 background 声明（徽章蓝底已去）"""
        import re
        text = self._read_template()
        # 匹配 `.tp-num {` 后到 `}` 之间的 CSS 块（非贪婪 + DOTALL）
        m = re.search(r"\n\s*\.tp-num\s*\{([^}]*)\}", text)
        assert m is not None, ".tp-num CSS 块必须存在"
        block = m.group(1)
        assert "background" not in block, "tp-num 不应再有 background（徽章装饰已去）"
        assert "border-radius" not in block, "tp-num 不应再有 border-radius（徽章圆角已去）"
        assert "padding" not in block, "tp-num 不应再有 padding（徽章内边距已去）"

    def test_tp_num_css_uses_mono_font(self):
        """.tp-num CSS 块使用 mono 字体（与 C-3/C-4.A 序号字面统一表达）"""
        import re
        text = self._read_template()
        m = re.search(r"\n\s*\.tp-num\s*\{([^}]*)\}", text)
        assert m is not None
        block = m.group(1)
        assert "monospace" in block, "tp-num 应使用 monospace 字体栈"
        # 保留 tabular-nums（数字等宽对齐）
        assert "tabular-nums" in block

    def test_dark_theme_tp_num_no_background_override(self):
        """暗色主题不再为 .tp-num 单独覆盖 background（徽章装饰已去 → 无需覆盖）"""
        text = self._read_template()
        # 暗色主题规则中不再含 `.tp-num { background:` 形式
        assert 'html[data-theme="dark"] .tp-num { background' not in text
        assert 'html[data-theme="dark"] .tp-num{background' not in text


class TestPrdExpressionStandardC4ASchemaSyncTpNum:
    """议题 13：prd_expression_standard.md §四 C-4.A schema 示例同步包 `tp-num` 字面"""

    def _read_standard(self) -> str:
        from pathlib import Path
        repo = Path(__file__).resolve().parents[3]
        return (repo / "pm-workflow" / "rules" / "prd_expression_standard.md").read_text(
            encoding="utf-8"
        )

    def test_c4a_example_tbody_uses_tp_num_span(self):
        """§四 C-4.A 示例 tbody 序号字面已包 `<span class="tp-num">N</span>`"""
        text = self._read_standard()
        # 议题 13 落地后 C-4.A 示例序号包 tp-num span
        assert '<td><span class="tp-num">1</span></td>' in text
        assert '<td><span class="tp-num">2</span></td>' in text


# ── 议题 15 / NB-R3-01 C-1/C-2/C-3 真无内容占位派生 ────────────────────────────


def _wrap_in_card(inner: str) -> str:
    """构造一个最小 interaction-card（不含 section / frame）用于占位派生测试"""
    return (
        '<div class="interaction-card">'
        '<div class="card-title">交互说明 — default</div>'
        f'{inner}'
        '</div>'
    )


class TestInjectC1PlaceholderWhenMissing:
    """议题 15 / NB-R3-01 — interaction-card 缺 C-1「列表回显说明」占位注入"""

    def test_inject_when_missing(self):
        html = _wrap_in_card('<div class="data-sub-title">数据展示说明</div>')
        out, n = assemble._inject_c1_placeholder_when_missing(html)
        assert n == 1
        assert '<div class="data-sub-title">列表回显说明</div>' in out
        assert '本帧无列表' in out

    def test_skip_when_present(self):
        html = _wrap_in_card(
            '<div class="data-sub-title">列表回显说明</div>'
            '<table><tbody><tr><td>排序规则</td><td>desc</td></tr></tbody></table>'
        )
        out, n = assemble._inject_c1_placeholder_when_missing(html)
        assert n == 0
        # PM 写源保留
        assert '排序规则' in out

    def test_idempotent_repeat(self):
        html = _wrap_in_card('<div class="data-sub-title">数据展示说明</div>')
        once, n1 = assemble._inject_c1_placeholder_when_missing(html)
        twice, n2 = assemble._inject_c1_placeholder_when_missing(once)
        assert n1 == 1
        assert n2 == 0
        assert once == twice

    def test_no_card_graceful(self):
        out, n = assemble._inject_c1_placeholder_when_missing('<div>no cards</div>')
        assert n == 0


class TestInjectC2PlaceholderWhenMissing:
    """议题 15 / NB-R3-01 — interaction-card 缺 C-2「数据展示说明」占位注入"""

    def test_inject_when_missing(self):
        html = _wrap_in_card('<div class="data-sub-title">列表回显说明</div>')
        out, n = assemble._inject_c2_placeholder_when_missing(html)
        assert n == 1
        assert '<div class="data-sub-title">数据展示说明</div>' in out
        assert '本帧无数据展示' in out

    def test_skip_when_present(self):
        html = _wrap_in_card('<div class="data-sub-title">数据展示说明</div>')
        out, n = assemble._inject_c2_placeholder_when_missing(html)
        assert n == 0

    def test_skip_when_card_field_description_present(self):
        """PM 自造 `卡片字段说明` sub-title → 让议题 18 C-2.A 派生兜底，避免双段"""
        html = _wrap_in_card('<div class="data-sub-title">卡片字段说明</div>')
        out, n = assemble._inject_c2_placeholder_when_missing(html)
        assert n == 0
        # 不应注入"数据展示说明"占位
        assert '数据展示说明' not in out


class TestInjectC3PlaceholderWhenMissing:
    """议题 15 / NB-R3-01 — interaction-card 缺 C-3「触点交互说明」占位注入"""

    def test_inject_when_missing(self):
        html = _wrap_in_card('<div class="data-sub-title">数据展示说明</div>')
        out, n = assemble._inject_c3_placeholder_when_missing(html)
        assert n == 1
        assert '<div class="data-sub-title">触点交互说明</div>' in out
        assert '本帧无交互触点' in out

    def test_skip_when_present(self):
        html = _wrap_in_card(
            '<div class="data-sub-title">触点交互说明</div>'
            '<table><thead><tr><th>序号</th></tr></thead></table>'
        )
        out, n = assemble._inject_c3_placeholder_when_missing(html)
        assert n == 0

    def test_inserted_before_c4_marker(self):
        """C-4 派生注入标记 `<!-- [C4-START: ...] -->` 存在时占位插在标记前"""
        html = _wrap_in_card(
            '<div class="data-sub-title">数据展示说明</div>'
            '<!-- [C4-START: H-M01-P01-default] auto-injected by assemble.py -->'
            '<div class="data-sub-title">业务契约</div>'
        )
        out, n = assemble._inject_c3_placeholder_when_missing(html)
        assert n == 1
        # 触点交互说明须在 C4-START 之前
        c3_idx = out.index('触点交互说明')
        c4_idx = out.index('[C4-START:')
        assert c3_idx < c4_idx


# ── 议题 19 / NB-WE-2A-R5-01 — _compute_card_insert_anchor 串联升级 ───────────
# 治"3 函数都拿同一 anchor（C-4 marker）后注入堆到前面致 C-3<C-1<C-2 顺序乱"根因
#
# 治本策略：串联查找优先级链
# - C-1 → 找 C-2 / C-3 sub-title / C-4 marker → 取最早 anchor
# - C-2 → 找 C-3 sub-title / C-4 marker → 取最早 anchor
# - C-3 → 找 C-4 marker（同议题 15 现态）
#
# 3 baseline 场景（治本目标 — 注入后顺序必须 C-1 < C-2 < C-3 < C-4）：
#   场景 1（仅 C-3）   → 应注入 C-1 < C-2 < [C-3] < (C-4)
#   场景 2（仅 C-2）   → 应注入 C-1 < [C-2] < C-3 < (C-4)
#   场景 3（全无）     → 应注入 C-1 < C-2 < C-3 < (C-4)


def _ordered_subtitle_indices(html: str) -> dict:
    """辅助：返回 C-1/C-2/C-3/C-4 在 html 中的字符 idx（不存在 → -1）"""
    def _idx(sub: str) -> int:
        i = html.find(sub)
        return i if i >= 0 else -1
    return {
        "C-1": _idx("列表回显说明"),
        "C-2": _idx("数据展示说明"),
        "C-3": _idx("触点交互说明"),
        "C-4": _idx("[C4-START:"),
    }


def _run_full_injection_pipeline(html: str) -> str:
    """辅助：复现 assemble.py L4115-4127 的 c1 → c2 → c3 调用顺序"""
    html, _ = assemble._inject_c1_placeholder_when_missing(html)
    html, _ = assemble._inject_c2_placeholder_when_missing(html)
    html, _ = assemble._inject_c3_placeholder_when_missing(html)
    return html


class TestIssue19SerialAnchorBaselineScenarios:
    """议题 19 / NB-WE-2A-R5-01 — 3 baseline 顺序合规场景"""

    def test_baseline_1_only_c3_present(self):
        """场景 1：PM 仅有 C-3 → 注入后顺序 C-1 < C-2 < C-3"""
        html = _wrap_in_card(
            '<div class="data-sub-title">触点交互说明</div>'
            '<table><tr><td>01</td></tr></table>'
        )
        out = _run_full_injection_pipeline(html)
        idx = _ordered_subtitle_indices(out)
        assert idx["C-1"] >= 0, "C-1 应被注入"
        assert idx["C-2"] >= 0, "C-2 应被注入"
        assert idx["C-3"] >= 0, "C-3 应保留"
        # 顺序严格：C-1 < C-2 < C-3
        assert idx["C-1"] < idx["C-2"] < idx["C-3"], (
            f"顺序乱: C-1={idx['C-1']} C-2={idx['C-2']} C-3={idx['C-3']}"
        )

    def test_baseline_2_only_c2_present(self):
        """场景 2：PM 仅有 C-2 → 注入后顺序 C-1 < C-2 < C-3"""
        html = _wrap_in_card(
            '<div class="data-sub-title">数据展示说明</div>'
            '<table><tr><td>field</td></tr></table>'
        )
        out = _run_full_injection_pipeline(html)
        idx = _ordered_subtitle_indices(out)
        assert idx["C-1"] >= 0, "C-1 应被注入"
        assert idx["C-2"] >= 0, "C-2 应保留"
        assert idx["C-3"] >= 0, "C-3 应被注入"
        assert idx["C-1"] < idx["C-2"] < idx["C-3"], (
            f"顺序乱: C-1={idx['C-1']} C-2={idx['C-2']} C-3={idx['C-3']}"
        )

    def test_baseline_3_all_missing(self):
        """场景 3：PM 全无 → 注入后顺序 C-1 < C-2 < C-3"""
        html = _wrap_in_card('')
        out = _run_full_injection_pipeline(html)
        idx = _ordered_subtitle_indices(out)
        assert idx["C-1"] >= 0
        assert idx["C-2"] >= 0
        assert idx["C-3"] >= 0
        assert idx["C-1"] < idx["C-2"] < idx["C-3"], (
            f"顺序乱: C-1={idx['C-1']} C-2={idx['C-2']} C-3={idx['C-3']}"
        )

    def test_baseline_3_with_c4_marker(self):
        """场景 3 加强：全无 + 已派生 C-4 marker → C-1 < C-2 < C-3 < C-4"""
        html = _wrap_in_card(
            '<!-- [C4-START: H-M01-P01-default] auto-injected by assemble.py -->'
            '<div class="data-sub-title">业务契约</div>'
            '<table><tr><td>规则</td></tr></table>'
            '<!-- [C4-END: H-M01-P01-default] -->'
        )
        out = _run_full_injection_pipeline(html)
        idx = _ordered_subtitle_indices(out)
        assert idx["C-1"] < idx["C-2"] < idx["C-3"] < idx["C-4"], (
            f"顺序乱: C-1={idx['C-1']} C-2={idx['C-2']} C-3={idx['C-3']} C-4={idx['C-4']}"
        )

    def test_baseline_1_with_c4_marker(self):
        """场景 1 加强：PM 仅 C-3 + 已派生 C-4 marker → C-1 < C-2 < C-3 < C-4"""
        html = _wrap_in_card(
            '<div class="data-sub-title">触点交互说明</div>'
            '<table><tr><td>01</td></tr></table>'
            '<!-- [C4-START: H-M01-P01-default] auto-injected by assemble.py -->'
            '<div class="data-sub-title">业务契约</div>'
            '<!-- [C4-END: H-M01-P01-default] -->'
        )
        out = _run_full_injection_pipeline(html)
        idx = _ordered_subtitle_indices(out)
        assert idx["C-1"] < idx["C-2"] < idx["C-3"] < idx["C-4"], (
            f"顺序乱: C-1={idx['C-1']} C-2={idx['C-2']} C-3={idx['C-3']} C-4={idx['C-4']}"
        )


class TestIssue19ComputeCardInsertAnchor:
    """议题 19 — _compute_card_insert_anchor 串联查找单元测试（覆盖 subtitle_type 各分支）"""

    def test_none_fallback_with_c4_marker(self):
        """subtitle_type=None → 旧行为：C-4 marker 优先 → body 末尾兜底"""
        card = (
            '<div class="data-sub-title">触点交互说明</div>'
            '<!-- [C4-START: X] auto -->'
        )
        anchor = assemble._compute_card_insert_anchor(card)
        # 旧 fallback：C-4 marker 之前
        assert anchor == card.index('<!--')

    def test_none_fallback_no_anchor(self):
        """subtitle_type=None + 无 C-4 marker → body 末尾"""
        card = '<div class="data-sub-title">触点交互说明</div>'
        anchor = assemble._compute_card_insert_anchor(card)
        assert anchor == len(card)

    def test_c1_finds_c2_anchor(self):
        """C-1 注入：找到 C-2 sub-title → anchor 是 C-2 起点"""
        card = '<div class="data-sub-title">数据展示说明</div>'
        anchor = assemble._compute_card_insert_anchor(card, "C-1")
        assert anchor == 0  # C-2 sub-title 从位置 0 开始

    def test_c1_finds_c3_when_c2_missing(self):
        """C-1 注入：无 C-2 → 找到 C-3 sub-title → anchor 是 C-3 起点"""
        card = '<div class="data-sub-title">触点交互说明</div>'
        anchor = assemble._compute_card_insert_anchor(card, "C-1")
        assert anchor == 0

    def test_c1_takes_earliest_when_c2_c3_both_present(self):
        """C-1 注入：C-2 和 C-3 都在 → 取最早 anchor（C-2 在前 → C-2 起点）"""
        card = (
            '<div class="data-sub-title">数据展示说明</div>'
            'A'
            '<div class="data-sub-title">触点交互说明</div>'
        )
        anchor = assemble._compute_card_insert_anchor(card, "C-1")
        assert anchor == 0  # C-2 在前

    def test_c1_with_card_field_description_treated_as_c2(self):
        """C-1 注入：PM 自造「卡片字段说明」也视作 C-2 段 → anchor 找到它"""
        card = (
            '前置内容'
            '<div class="data-sub-title">卡片字段说明</div>'
        )
        anchor = assemble._compute_card_insert_anchor(card, "C-1")
        assert anchor == card.index('<div class="data-sub-title">卡片字段说明</div>')

    def test_c2_finds_c3_anchor(self):
        """C-2 注入：找到 C-3 sub-title → anchor 是 C-3 起点"""
        card = '<div class="data-sub-title">触点交互说明</div>'
        anchor = assemble._compute_card_insert_anchor(card, "C-2")
        assert anchor == 0

    def test_c2_ignores_c1_subtitle(self):
        """C-2 注入：不应被已有 C-1 sub-title 影响（C-1 应在 C-2 之前）"""
        card = (
            '<div class="data-sub-title">列表回显说明</div>'
            '<p>本帧无列表。</p>'
            '<div class="data-sub-title">触点交互说明</div>'
        )
        anchor = assemble._compute_card_insert_anchor(card, "C-2")
        # C-2 找 C-3 anchor（不应找到 C-1 而插到 C-1 之前）
        c3_idx = card.index('<div class="data-sub-title">触点交互说明</div>')
        assert anchor == c3_idx

    def test_c3_finds_c4_marker(self):
        """C-3 注入：找到 C-4 marker → anchor 是 marker 起点（同议题 15 现态）"""
        card = '<!-- [C4-START: X] -->'
        anchor = assemble._compute_card_insert_anchor(card, "C-3")
        assert anchor == 0

    def test_c3_ignores_c1_c2_subtitles(self):
        """C-3 注入：不应被已有 C-1/C-2 sub-title 影响（C-3 应在 C-1/C-2 之后）"""
        card = (
            '<div class="data-sub-title">列表回显说明</div>'
            '<div class="data-sub-title">数据展示说明</div>'
        )
        anchor = assemble._compute_card_insert_anchor(card, "C-3")
        # C-3 链路不含 C-1/C-2 查找 → 只查 C-4 marker → 无 → body 末尾
        assert anchor == len(card)


# ── 议题 18 / NB-R4-01 C-2.A 索引层派生（「卡片字段说明」缺索引层）─────────────


class TestInjectC2AIndexForCardFieldDescription:
    """议题 18 / NB-R4-01 — 为「卡片字段说明」+ C-2.A 索引层缺失的卡注入 6 列占位表"""

    def test_inject_when_card_field_description_no_index(self):
        html = _wrap_in_card(
            '<div class="data-sub-title">卡片字段说明</div>'
            '<table><thead><tr>'
            '<th>字段名</th><th>接口字段</th><th>显示格式</th><th>空值处理</th>'
            '</tr></thead><tbody><tr><td>name</td><td>n</td><td>—</td><td>—</td></tr></tbody></table>'
        )
        out, n = assemble._inject_c2a_index_for_card_field_description(html)
        assert n == 1
        # 注入了「数据展示说明」sub-title + 6 列占位 thead
        assert '<div class="data-sub-title">数据展示说明</div>' in out
        assert 'C 触点 ID' in out
        assert '单元名称' in out
        assert '是否封装为组件' in out
        assert '渲染时机' in out
        assert '跨平台差异' in out
        assert '关联 T 触点' in out
        assert '（PM 待补完整 schema）' in out
        # 「卡片字段说明」原写源保留
        assert '卡片字段说明' in out
        # 注入顺序：「数据展示说明」在「卡片字段说明」之前
        assert out.index('数据展示说明') < out.index('卡片字段说明')

    def test_skip_when_c2a_index_already_present(self):
        """已含 C-2.A 索引层 thead 强信号（C 触点 ID + 单元名称）→ 跳过"""
        html = _wrap_in_card(
            '<table><thead><tr>'
            '<th>C 触点 ID</th><th>单元名称</th>'
            '<th>是否封装为组件</th><th>渲染时机</th>'
            '<th>跨平台差异</th><th>关联 T 触点</th>'
            '</tr></thead></table>'
            '<div class="data-sub-title">卡片字段说明</div>'
        )
        out, n = assemble._inject_c2a_index_for_card_field_description(html)
        assert n == 0

    def test_skip_when_standard_c2_subtitle_present(self):
        """已含「数据展示说明」标准 sub-title → 跳过避免双段并存"""
        html = _wrap_in_card(
            '<div class="data-sub-title">数据展示说明</div>'
            '<div class="data-sub-title">卡片字段说明</div>'
        )
        out, n = assemble._inject_c2a_index_for_card_field_description(html)
        assert n == 0

    def test_skip_when_card_field_description_absent(self):
        """卡内无「卡片字段说明」字面 → 跳过（非本议题触发场景）"""
        html = _wrap_in_card('<div class="data-sub-title">数据展示说明</div>')
        out, n = assemble._inject_c2a_index_for_card_field_description(html)
        assert n == 0

    def test_idempotent_repeat(self):
        """重入幂等"""
        html = _wrap_in_card(
            '<div class="data-sub-title">卡片字段说明</div>'
            '<table><thead><tr><th>字段名</th></tr></thead></table>'
        )
        once, n1 = assemble._inject_c2a_index_for_card_field_description(html)
        twice, n2 = assemble._inject_c2a_index_for_card_field_description(once)
        assert n1 == 1
        assert n2 == 0
        assert once == twice


# ── 议题 20 / NB-WE-2A-R8-03 P1 cover-version override ────────────────────────


class TestOverwriteCoverVersionFromScaffoldChangelog:
    """议题 20 / NB-WE-2A-R8-03 P1 — assemble 后处理把 prd 封面 cover-version
    强制对齐 scaffold.json["changelog"] 末行 version 真源。

    实证样本：私域主页 scaffold["version"]="v4.0" vs changelog[-1]["version"]="v0.1"
    → 重 assemble 必须取后者覆盖封面字面。
    """

    def _write_scaffold(self, tmp_path, version, changelog_versions):
        import json as _json

        scaffold = {
            "schema_version": "v2.0",
            "product": "测试产品",
            "platforms": ["桌面Web"],
            "version": version,
            "changelog": [
                {
                    "version": v,
                    "desc": f"changelog {v}",
                    "reason": "test",
                    "author": "PM Agent",
                    "reviewer": "Supervisor Agent",
                    "date": "2026-06-05",
                }
                for v in changelog_versions
            ],
        }
        sc_path = tmp_path / "scaffold.json"
        sc_path.write_text(_json.dumps(scaffold, ensure_ascii=False), encoding="utf-8")
        return sc_path

    def test_replaces_legacy_cover_version(self, monkeypatch, tmp_path):
        """scaffold.version=v4.0 vs changelog 末行=v0.1 → 封面被对齐到 v0.1"""
        sc_path = self._write_scaffold(tmp_path, "v4.0", ["v0.1"])
        monkeypatch.setattr(assemble, "SCAFFOLD", sc_path)
        html = (
            '<div class="cover-badge-row">'
            '<span class="cover-version">v4.0</span>'
            '<span class="cover-date">2026-06-05</span>'
            '</div>'
        )
        out, n = assemble._overwrite_cover_version_from_scaffold_changelog(html)
        assert n == 1
        assert '>v4.0<' not in out
        assert '>v0.1<' in out

    def test_idempotent_when_already_canonical(self, monkeypatch, tmp_path):
        """封面已是 changelog 末行真源 → 不动 + 计数 0（幂等）"""
        sc_path = self._write_scaffold(tmp_path, "v0.1", ["v0.1"])
        monkeypatch.setattr(assemble, "SCAFFOLD", sc_path)
        html = '<span class="cover-version">v0.1</span>'
        out, n = assemble._overwrite_cover_version_from_scaffold_changelog(html)
        assert n == 0
        assert out == html

    def test_takes_last_changelog_entry(self, monkeypatch, tmp_path):
        """changelog 有多条 → 取末行 version 作真源（v0.1 → v1.0 → v2.0 取 v2.0）"""
        sc_path = self._write_scaffold(tmp_path, "v0.1", ["v0.1", "v1.0", "v2.0"])
        monkeypatch.setattr(assemble, "SCAFFOLD", sc_path)
        html = '<span class="cover-version">v0.1</span>'
        out, n = assemble._overwrite_cover_version_from_scaffold_changelog(html)
        assert n == 1
        assert '>v2.0<' in out

    def test_scaffold_missing_returns_unchanged(self, monkeypatch, tmp_path):
        """scaffold.json 不存在 → 优雅降级 + WARN + html 不变"""
        sc_path = tmp_path / "missing_scaffold.json"
        monkeypatch.setattr(assemble, "SCAFFOLD", sc_path)
        html = '<span class="cover-version">v0.1</span>'
        out, n = assemble._overwrite_cover_version_from_scaffold_changelog(html)
        assert n == 0
        assert out == html

    def test_changelog_empty_returns_unchanged(self, monkeypatch, tmp_path):
        """changelog 为空 → 优雅降级 + WARN + html 不变"""
        sc_path = self._write_scaffold(tmp_path, "v0.1", [])
        monkeypatch.setattr(assemble, "SCAFFOLD", sc_path)
        html = '<span class="cover-version">v0.1</span>'
        out, n = assemble._overwrite_cover_version_from_scaffold_changelog(html)
        assert n == 0
        assert out == html

    def test_html_without_cover_version_returns_zero(self, monkeypatch, tmp_path):
        """html 无 cover-version span → 计数 0（旧版 prd 无封面块场景）"""
        sc_path = self._write_scaffold(tmp_path, "v0.1", ["v0.1"])
        monkeypatch.setattr(assemble, "SCAFFOLD", sc_path)
        html = '<div>无 cover</div>'
        out, n = assemble._overwrite_cover_version_from_scaffold_changelog(html)
        assert n == 0
        assert out == html


# ── 议题 22 / NB-WE-2A-R7-01 P3 _inject_c2b 精度防御（紧贴 C-2.B `<table>`）─────


class TestInjectC2BSubtitlePrecisionGuard:
    """议题 22 / NB-WE-2A-R7-01 P3 — `_inject_c2b_subtitle_for_no_c_binding` 精度防御：
    派生的 sub-title 必须紧贴 C-2.B 字段表 `<table>` open，不能夹在 C-2.A 占位表 /
    正文段（`</p>` / `</ul>` / `</ol>` / `</pre>` / 其他 `</table>`）之前；
    不紧贴时按 fallback 仍插入 `<table>` 前（保持派生有效），stderr WARN 提示。
    """

    def test_standard_adjacent_injection(self):
        """标准场景：C-2.B 表紧贴 card open → 正常注入 + 无 WARN"""
        section = _make_section_with_card(
            "H-M10-P13-admin-default",
            page_name="自定义字段管理",
            card_title_state="admin-default",
            card_inner=_C2B_FIELD_TABLE,
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(section)
        assert n == 1
        # 派生 sub-title 紧贴 `<table>` 前（中间仅 newline）
        idx_sub = out.index('<div class="data-sub-title">字段说明')
        idx_tbl = out.index('<table>', idx_sub)
        between = out[idx_sub + len('<div class="data-sub-title">字段说明 — 自定义字段管理</div>\n'):idx_tbl]
        # 中间只剩 whitespace
        assert between.strip() == ''

    def test_non_adjacent_with_preceding_table_still_injects_with_warn(self, capsys):
        """异常场景：C-2.B 表前夹有其他 `</table>`（如 C-2.A 占位表）→ fallback 仍注入 + WARN"""
        c2a_placeholder_table = (
            '<table><thead><tr>'
            '<th>C 触点 ID</th><th>单元名称</th><th>是否封装为组件</th>'
            '<th>渲染时机</th><th>跨平台差异</th><th>关联 T 触点</th>'
            '</tr></thead><tbody><tr>'
            '<td>（PM 待补完整 schema）</td><td>（PM 待补完整 schema）</td>'
            '<td>（PM 待补完整 schema）</td><td>（PM 待补完整 schema）</td>'
            '<td>（PM 待补完整 schema）</td><td>（PM 待补完整 schema）</td>'
            '</tr></tbody></table>'
        )
        section = _make_section_with_card(
            "H-M10-P13-admin-default",
            page_name="自定义字段管理",
            card_title_state="admin-default",
            # C-2.A 占位表先（议题 18 派生形态）+ C-2.B 字段表后
            card_inner=c2a_placeholder_table + _C2B_FIELD_TABLE,
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(section)
        # 仍注入（fallback 保持派生有效）
        assert n == 1
        assert '<div class="data-sub-title">字段说明' in out
        # 注入点在 C-2.B 字段表前（确认 C-2.A 占位表 thead 在派生 sub-title 之前）
        idx_c2a = out.index('C 触点 ID')
        idx_sub = out.index('<div class="data-sub-title">字段说明')
        idx_c2b = out.index('D 触点 ID')
        assert idx_c2a < idx_sub < idx_c2b
        # 触发 stderr WARN
        captured = capsys.readouterr()
        assert "精度防御" in captured.err
        assert "未能紧贴 C-2.B 字段表" in captured.err

    def test_non_adjacent_with_preceding_paragraph_warns(self, capsys):
        """异常场景：C-2.B 表前夹有 `</p>` 段（PM 写的说明段）→ fallback + WARN"""
        section = _make_section_with_card(
            "H-M10-P13-admin-default",
            page_name="自定义字段管理",
            card_title_state="admin-default",
            card_inner='<p>说明性文字</p>' + _C2B_FIELD_TABLE,
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(section)
        assert n == 1
        captured = capsys.readouterr()
        assert "精度防御" in captured.err

    def test_card_title_close_adjacent_no_warn(self, capsys):
        """允许紧贴 `<div class="card-title">…</div>` close 后（卡片标题紧贴 OK）→ 无 WARN"""
        section = _make_section_with_card(
            "H-M10-P13-admin-default",
            page_name="自定义字段管理",
            card_title_state="admin-default",
            card_inner=_C2B_FIELD_TABLE,  # card_title close 紧贴 _C2B_FIELD_TABLE
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(section)
        assert n == 1
        captured = capsys.readouterr()
        # `</div>` close 不触发 adjacency violation
        assert "精度防御" not in captured.err

    def test_idempotent_with_existing_subtitle(self):
        """已含「字段说明」sub-title → 跳过（幂等）"""
        section = _make_section_with_card(
            "H-M10-P13-admin-default",
            page_name="自定义字段管理",
            card_title_state="admin-default",
            card_inner=(
                '<div class="data-sub-title">字段说明 — 自定义字段管理</div>'
                + _C2B_FIELD_TABLE
            ),
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(section)
        assert n == 0
        assert out == section

    def test_no_c2b_table_returns_zero(self):
        """card 内无 C-2.B 字段表强信号 → 跳过 + 计数 0"""
        section = _make_section_with_card(
            "H-M10-P13-admin-default",
            page_name="自定义字段管理",
            card_title_state="admin-default",
            card_inner='<p>无字段表</p>',
            has_c_tp=False,
        )
        out, n = assemble._inject_c2b_subtitle_for_no_c_binding(section)
        assert n == 0
        assert out == section
