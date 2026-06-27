"""测试 check_rule_coverage.py — SSOT #22 元 SSOT 覆盖矩阵。"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_rule_coverage


class TestExtractRules:
    def test_rule_id_pattern_matches(self) -> None:
        """RULE_ID_RE 应匹配 S1-01 / S4-22 / G-07 等正确格式。"""
        text = "见 S4-22 + G-01 + S1-05"
        ids = check_rule_coverage.RULE_ID_RE.findall(text)
        assert "S4-22" in ids
        assert "G-01" in ids
        assert "S1-05" in ids

    def test_rule_id_pattern_skips_invalid(self) -> None:
        """格式错误的不应匹配。"""
        # S5-01 / G-1 / S40-22 都不合法
        text = "见 S5-01 + G-1 + S40-22 + S40-22"
        ids = check_rule_coverage.RULE_ID_RE.findall(text)
        # S5-01 因为 [1-4]? 限定 1-4,不匹配
        assert "S5-01" not in ids
        # G-1 单数字不匹配（要求 \d{2}）
        assert "G-1" not in ids

    def test_extract_from_real_doc(self) -> None:
        """从真实 rule_hard_constraints.md 提取至少 30 条规则（项目实测 50）。"""
        rules = check_rule_coverage.extract_rules_from_doc()
        assert len(rules) >= 30, f"应至少 30 条,实际 {len(rules)}"
        # 必含核心 S4-XX 规则
        for must_have in ("S4-22", "S4-23", "S4-24"):
            assert must_have in rules, f"缺核心规则 {must_have}"

    def test_extract_from_real_code(self) -> None:
        """从真实 precheck/assemble 提取规则引用,至少 5 条（项目实测 8）。"""
        refs = check_rule_coverage.extract_rules_from_code()
        assert len(refs) >= 5, f"应至少 5 条引用,实际 {len(refs)}"
        # 至少 S4-22 / S4-23 在 precheck_stage4 中被引用
        assert "S4-22" in refs or "S4-23" in refs


class TestRealRepoSanity:
    """对真实仓库做基线断言（不强制 PASS,作健康检查）。"""

    def test_no_severe_drift(self) -> None:
        """code → doc 漂移：代码引用的规则编号不应大量出现在 doc 之外。
        允许少量边缘场景（如已废弃的旧编号注释残留）。"""
        doc_rules = check_rule_coverage.extract_rules_from_doc()
        code_refs = check_rule_coverage.extract_rules_from_code()
        drift = set(code_refs.keys()) - doc_rules
        # 允许 ≤ 3 条漂移作为容差
        assert len(drift) <= 3, (
            f"漂移规则数 {len(drift)} 超过容差 3：{sorted(drift)}"
        )
