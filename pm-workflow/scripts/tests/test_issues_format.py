"""测试 check_issues_format.py — SSOT #19 issues 格式校验。"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_issues_format


_VALID_CONTENT = """# 调整意见 — 2026-05-08 01:23

状态：未分析

| # | 完整描述 | 影响成果文件 | 业务 | 功能逻辑 |
|---|---------|-------------|------|---------|
| 1 | 测试调整 | `outputs/x.md` | 业务 | 功能 |
"""


class TestValidateOne:
    def test_valid_未分析_passes(self, tmp_path) -> None:
        f = tmp_path / "2026-05-08_0123.md"
        f.write_text(_VALID_CONTENT, encoding="utf-8")
        assert check_issues_format.validate_one(f) == []

    def test_valid_已分析_with_analyzed_suffix(self, tmp_path) -> None:
        f = tmp_path / "2026-05-08_0123_analyzed.md"
        content = _VALID_CONTENT.replace("状态：未分析", "状态：已分析")
        f.write_text(content, encoding="utf-8")
        assert check_issues_format.validate_one(f) == []

    def test_bad_filename_fails(self, tmp_path) -> None:
        f = tmp_path / "issue_2026.md"  # 非法文件名
        f.write_text(_VALID_CONTENT, encoding="utf-8")
        errors = check_issues_format.validate_one(f)
        assert any("文件名格式非法" in e for e in errors)

    def test_missing_header_fails(self, tmp_path) -> None:
        f = tmp_path / "2026-05-08_0123.md"
        f.write_text(
            "状态：未分析\n\n| # | 完整描述 | 影响成果文件 |\n|---|---|---|\n| 1 | x | y |\n",
            encoding="utf-8",
        )
        errors = check_issues_format.validate_one(f)
        assert any("缺文件头" in e for e in errors)

    def test_missing_status_fails(self, tmp_path) -> None:
        f = tmp_path / "2026-05-08_0123.md"
        f.write_text(
            "# 调整意见 — 2026-05-08 01:23\n\n| # | 完整描述 | 影响成果文件 |\n|---|---|---|\n| 1 | x | y |\n",
            encoding="utf-8",
        )
        errors = check_issues_format.validate_one(f)
        assert any("缺 `状态" in e for e in errors)

    def test_status_filename_mismatch_fails(self, tmp_path) -> None:
        """文件名含 _analyzed 但状态字段为「未分析」→ FAIL。"""
        f = tmp_path / "2026-05-08_0123_analyzed.md"
        f.write_text(_VALID_CONTENT, encoding="utf-8")  # 状态:未分析
        errors = check_issues_format.validate_one(f)
        assert any("应为 `已分析`" in e for e in errors)

    def test_table_header_missing_required_col_fails(self, tmp_path) -> None:
        f = tmp_path / "2026-05-08_0123.md"
        f.write_text(
            "# 调整意见 — 2026-05-08 01:23\n\n状态：未分析\n\n| 列1 | 列2 |\n|---|---|\n| a | b |\n",
            encoding="utf-8",
        )
        errors = check_issues_format.validate_one(f)
        assert any("缺必备列" in e for e in errors)

    def test_no_data_row_fails(self, tmp_path) -> None:
        f = tmp_path / "2026-05-08_0123.md"
        f.write_text(
            "# 调整意见 — 2026-05-08 01:23\n\n状态：未分析\n\n| # | 完整描述 | 影响成果文件 |\n|---|---|---|\n",
            encoding="utf-8",
        )
        errors = check_issues_format.validate_one(f)
        assert any("无任何数据行" in e for e in errors)
