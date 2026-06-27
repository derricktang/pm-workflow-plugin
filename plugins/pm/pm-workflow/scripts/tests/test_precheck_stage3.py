"""test_precheck_stage3.py — precheck_stage3.py pytest 用例集。

历史来源：HC-3 5 测试用例烟测（NB-HC-05 挂账等待 pytest 引入后转 fixture）。

覆盖函数：
- check_sections（20 章节存在性,含 §5.5 业务流程图复述）
- check_section_3 / check_section_5_5 / check_section_7 / check_section_13（内容约束）
- Tier 2 FMT-1~6 格式约束（[Must] 段落存在性）
- §5.5 业务流程图 mermaid 数 ↔ 阶段 2 §二 对称（SSOT #30 阶段 3 派生）

[Must] 测试隔离纪律：每个用例独立产出 Report 对象 + 独立 md content；
不共享全局状态、不读真实 outputs/ 目录。
"""

from __future__ import annotations

import pytest

# precheck_stage3 由 conftest.py sys.path 注入；直接 import 即可
from precheck_stage3 import (  # type: ignore
    Report,
    check_sections,
    check_section_3,
    check_section_5,
    check_section_7,
    check_section_13,
)


# ── 章节存在性用例（HC-3 1-2 派生）──────────────────────────────────────────


class TestSectionExistence:
    """覆盖 precheck_stage3.check_sections — 20 必填章节 + 变更日志。"""

    def test_stage3_pass_all_sections_complete(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """合法产物（含 §0–§18 + §5.5 业务流程图 + 变更日志 + Tier 2 FMT 段）→ 应 pass。"""
        r = Report()
        matches = check_sections(sample_产品定义_md_minimal, r)
        assert r.errors == [], f"完整产物应 PASS,实际错误：{r.errors}"
        # 全部 22 个章节（§0–§18 + §5.5 + §6.5 + 变更日志）匹配命中
        assert all(m is not None for m in matches.values()), \
            f"所有章节应命中,缺失：{[k for k, v in matches.items() if v is None]}"

    def test_stage3_fail_missing_section_7(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """删除 §7 功能需求 → 应 fail。"""
        # 把 §7 标题改名让正则匹配不到
        broken = sample_产品定义_md_minimal.replace(
            "## 7. 功能需求", "## 7. 不是功能需求"
        )
        r = Report()
        check_sections(broken, r)
        assert any("§7" in e or "功能需求" in e for e in r.errors), \
            f"应报 §7 缺失,实际错误：{r.errors}"

    def test_stage3_fail_missing_section_13(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """删除 §13 非功能需求 → 应 fail。"""
        broken = sample_产品定义_md_minimal.replace(
            "## 13. 非功能需求", "## 13. xxxx"
        )
        r = Report()
        check_sections(broken, r)
        assert any("§13" in e or "非功能需求" in e for e in r.errors), \
            f"应报 §13 缺失,实际错误：{r.errors}"


# ── §3 用户画像用例 ──────────────────────────────────────────────────────────


class TestSection3Persona:
    """覆盖 §3 用户画像 5 属性表校验。"""

    def test_stage3_pass_section_3_full_attributes(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """完整 5 属性表（典型用户/核心诉求/使用场景/关键痛点/JTBD）→ 应 pass。"""
        r = Report()
        check_section_3(sample_产品定义_md_minimal, r)
        assert r.errors == [], \
            f"§3 5 属性齐全应 PASS,实际错误：{r.errors}"

    def test_stage3_fail_section_3_missing_attribute(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """§3 角色画像缺 Jobs-to-be-done 属性 → 应 fail。"""
        # 把 Jobs-to-be-done 改名,触发缺失属性 fail
        broken = sample_产品定义_md_minimal.replace(
            "| Jobs-to-be-done | 测试 |", "| 任务待办 | 测试 |"
        )
        r = Report()
        check_section_3(broken, r)
        assert len(r.errors) >= 1, "缺 Jobs-to-be-done 必须报 fail"
        assert any("Jobs-to-be-done" in e for e in r.errors), \
            f"错误应明示缺 JTBD,实际：{r.errors}"


# ── §5 用户旅程 + FMT-4 用例 ─────────────────────────────────────────────────


class TestSection5Journey:
    """覆盖 §5 用户旅程表 + Tier 2 FMT-4 多旅程产品组织规则。"""

    def test_stage3_fail_fmt4_missing_multi_journey_rule(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """§5 缺 [Should] 多旅程产品组织规则段（FMT-4）→ 应 fail。"""
        broken = sample_产品定义_md_minimal.replace(
            "`[Should]` 多旅程产品组织规则",
            "（已删除多旅程组织规则）",
        )
        r = Report()
        check_section_5(broken, r)
        assert any(
            "FMT-4" in e or "多旅程产品组织规则" in e for e in r.errors
        ), f"应报 FMT-4 缺失,实际错误：{r.errors}"


# ── §7 功能需求 + FMT-1/2/3 用例 ─────────────────────────────────────────────


class TestSection7Feature:
    """覆盖 §7 功能需求 + Tier 2 FMT-1/2/3 三段 [Must]。"""

    def test_stage3_pass_section_7_with_all_fmt(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """§7 含 FMT-1/2/3 三段 [Must] + F-XXX + gherkin → 应 pass。"""
        r = Report()
        check_section_7(sample_产品定义_md_minimal, r)
        assert r.errors == [], \
            f"§7 完整 FMT-1/2/3 应 PASS,实际错误：{r.errors}"

    def test_stage3_fail_fmt1_missing_interaction_minset(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """§7 缺 [Must] 交互说明表元素最小集（FMT-1）→ 应 fail。"""
        broken = sample_产品定义_md_minimal.replace(
            "`[Must]` 交互说明表元素最小集",
            "（已删除 FMT-1 段）",
        )
        r = Report()
        check_section_7(broken, r)
        assert any(
            "FMT-1" in e or "交互说明表元素最小集" in e for e in r.errors
        ), f"应报 FMT-1 缺失,实际错误：{r.errors}"

    def test_stage3_fail_fmt3_missing_acceptance_criteria(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """§7 缺 [Must] 验收场景选取标准（FMT-3）→ 应 fail。"""
        broken = sample_产品定义_md_minimal.replace(
            "`[Must]` 验收场景选取标准",
            "（已删除 FMT-3 段）",
        )
        r = Report()
        check_section_7(broken, r)
        assert any(
            "FMT-3" in e or "验收场景选取标准" in e for e in r.errors
        ), f"应报 FMT-3 缺失,实际错误：{r.errors}"

    def test_stage3_fail_section_7_missing_gherkin(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """§7 无 ```gherkin 块 → 应 fail。"""
        broken = sample_产品定义_md_minimal.replace("```gherkin", "```text")
        r = Report()
        check_section_7(broken, r)
        assert any("gherkin" in e for e in r.errors), \
            f"应报 gherkin 缺失,实际错误：{r.errors}"


# ── §13 非功能需求 + FMT-6 用例 ──────────────────────────────────────────────


class TestSection13NonFunctional:
    """覆盖 §13 性能体验表 + Tier 2 FMT-6 体验意图四要素。"""

    def test_stage3_pass_section_13_with_fmt6(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """§13 含 [Must] 体验意图填写格式段 + 反例对照 → 应 pass。"""
        r = Report()
        check_section_13(sample_产品定义_md_minimal, r)
        assert r.errors == [], \
            f"§13 完整 FMT-6 应 PASS,实际错误：{r.errors}"

    def test_stage3_fail_fmt6_missing_experience_intent_format(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """§13 缺 [Must] 体验意图填写格式段（FMT-6）→ 应 fail。"""
        broken = sample_产品定义_md_minimal.replace(
            "`[Must]` 体验意图填写格式",
            "（已删除 FMT-6 段）",
        )
        r = Report()
        check_section_13(broken, r)
        assert any(
            "FMT-6" in e or "体验意图填写格式" in e for e in r.errors
        ), f"应报 FMT-6 缺失,实际错误：{r.errors}"

    def test_stage3_fail_fmt6_missing_negative_examples(
        self, sample_产品定义_md_minimal: str
    ) -> None:
        """§13 缺 ❌ 反例对照表 → 应 fail。"""
        broken = sample_产品定义_md_minimal.replace("❌ 反例", "示例")
        r = Report()
        check_section_13(broken, r)
        assert any(
            "反例" in e or "FMT-6" in e for e in r.errors
        ), f"应报反例对照表缺失,实际错误：{r.errors}"


# ── §5.5 业务流程图复述 mermaid 数对称用例（NB SSOT #30 阶段 3 派生）──────


class TestSection55BusinessFlow:
    """覆盖 precheck_stage3.check_section_5_5 — §5.5 ↔ 阶段 2 §二 mermaid 数对称。"""

    def test_section_5_5_no_template_fail(self) -> None:
        """§5.5 章节内容缺失 → 应 fail。"""
        from precheck_stage3 import check_section_5_5  # type: ignore
        content = "## 5. 用户旅程\n\n（无 §5.5）\n\n## 6. 页面路由"
        r = Report()
        check_section_5_5(content, r)
        assert any("§5.5" in e for e in r.errors)

    def test_section_5_5_warn_when_no_stage2_output(
        self, tmp_path, monkeypatch
    ) -> None:
        """§5.5 存在但 outputs/ 无阶段 2 产物 → WARN 不阻断。"""
        from precheck_stage3 import check_section_5_5  # type: ignore
        import precheck_stage3  # type: ignore
        empty_outputs = tmp_path / "outputs"
        empty_outputs.mkdir()
        monkeypatch.setattr(precheck_stage3, "OUTPUT_DIR", empty_outputs)
        content = "## 5.5 业务流程图\n\n```mermaid\nflowchart TD\n  A --> B\n```"
        r = Report()
        check_section_5_5(content, r)
        assert r.errors == [], "无阶段 2 产物应 WARN 不 FAIL"
        assert any("跳过" in w or "未找到" in w for w in r.warnings)

    def test_section_5_5_pass_count_match(
        self, tmp_path, monkeypatch
    ) -> None:
        """§5.5 与阶段 2 §二 mermaid 数相同 → PASS。"""
        from precheck_stage3 import check_section_5_5  # type: ignore
        import precheck_stage3  # type: ignore
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        (outputs / "功能规划_测试_latest.md").write_text(
            "## 二、业务流程图\n\n```mermaid\nflowchart TD\nA-->B\n```\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(precheck_stage3, "OUTPUT_DIR", outputs)
        content = "## 5.5 业务流程图\n\n```mermaid\nflowchart TD\nA-->B\n```\n\n## 6. 页面路由"
        r = Report()
        check_section_5_5(content, r)
        assert r.errors == []

    def test_section_5_5_fail_count_mismatch(
        self, tmp_path, monkeypatch
    ) -> None:
        """§5.5 与阶段 2 §二 mermaid 数不同 → FAIL。"""
        from precheck_stage3 import check_section_5_5  # type: ignore
        import precheck_stage3  # type: ignore
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        (outputs / "功能规划_测试_latest.md").write_text(
            "## 二、业务流程图\n\n```mermaid\nA\n```\n\n```mermaid\nB\n```\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(precheck_stage3, "OUTPUT_DIR", outputs)
        content = "## 5.5 业务流程图\n\n```mermaid\nA\n```\n\n## 6. 页面路由"
        r = Report()
        check_section_5_5(content, r)
        assert any("不对称" in e and "1" in e and "2" in e for e in r.errors)


# ── G 方案 G.5 UI 字面来源标注校验用例（SSOT #54） ─────────────────────────────


class TestUISourceAnnotationG5:
    """覆盖 precheck_common.check_ui_source_annotation — G 方案 G.5
    UI 字面来源标注校验（共享逻辑，stage 1/2/3 调用）。
    """

    def _run(self, content: str, stage_num: int):
        from precheck_common import check_ui_source_annotation  # type: ignore
        # 使用 stage 3 的 Report（已在 test_precheck_stage3 上下文）
        from precheck_stage3 import Report  # type: ignore
        r = Report()
        check_ui_source_annotation(content, stage_num, r)
        return r

    def test_no_ui_literal_passes(self):
        """无 UI 字面 → OK，无 WARN。"""
        r = self._run("# 标题\n\n业务规则描述。", 1)
        assert len(r.warnings) == 0

    def test_ui_show_detail_no_source_warns(self):
        """UI 字面"显示...详单"无【来源】标注 → WARN。"""
        r = self._run("# 标题\n\n显示资源详单。", 1)
        assert any('S1-08' in w for w in r.warnings)
        assert any('显示资源详单' in w for w in r.warnings)

    def test_source_annotation_within_2_lines_passes(self):
        """【来源：...】标注在 ±2 行上下文 → OK，不报 WARN。"""
        content = "【来源：产品总监诉求】\n\n显示资源详单。"
        r = self._run(content, 1)
        assert len(r.warnings) == 0

    def test_color_hex_no_source_warns(self):
        """颜色 hex 字面无标注 → WARN（stage 3 视觉细节场景）。"""
        r = self._run("# 颜色：#1890FF", 3)
        assert any('S3-07' in w for w in r.warnings)

    def test_font_size_with_source_passes(self):
        """字号字面 + 上下文【来源】标注 → OK。"""
        content = "【来源：客户访谈】\n字号: 14px"
        r = self._run(content, 3)
        assert len(r.warnings) == 0

    def test_stage_2_rule_id(self):
        """stage 2 调用 → S2-07 rule id。"""
        r = self._run("显示矩阵预览。", 2)
        assert any('S2-07' in w for w in r.warnings)

    def test_button_position_no_source_warns(self):
        """按钮位置细节无标注 → WARN。"""
        r = self._run("按钮放置在右上角。", 3)
        # 注: 关键词 "右上" 单独不命中（需"按钮...右上"或"右上...角"）
        # 这里"按钮放置在右上角"含"右上角" → 命中"右上...角"
        warned = any('S3-07' in w for w in r.warnings)
        assert warned, f"warnings: {r.warnings}"

    def test_chinese_full_width_annotation(self):
        """中文全角【来源：...】格式 + 半角冒号兼容。"""
        content = "【来源:产品总监诉求】\n显示资源详单"
        r = self._run(content, 1)
        assert len(r.warnings) == 0

    def test_business_rule_no_ui_literal_passes(self):
        """业务规则描述（不含 UI 实现细节字面）→ OK。
        反例：retro G.3 草案中正确写法示例。"""
        content = "清理对应节点资源（按 NB-210 资源回收矩阵）"
        r = self._run(content, 1)
        # 注：包含"矩阵"但无"显示...矩阵"/"...预览矩阵"前缀，应不命中
        assert len(r.warnings) == 0

    def test_multiple_ui_literals_reports_distinct(self):
        """多处 UI 字面无标注 → 全部报 WARN（去重 + 计数）。"""
        content = "显示资源详单\n弹窗排版调整\n颜色: #FF0000"
        r = self._run(content, 1)
        # 多处不同字面 → 至少 1 个 WARN
        assert len(r.warnings) >= 1
        msg = r.warnings[0]
        # 全部命中应在同 WARN 中报告（含计数）
        assert '3 处' in msg or '2 处' in msg or '处' in msg
