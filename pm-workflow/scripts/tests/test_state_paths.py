"""测试 check_state_paths.py — SSOT #21 state.md 路径校验。"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_state_paths


class TestExtractPaths:
    def test_extract_simple_md_path(self) -> None:
        text = "| 阶段 1 | `outputs/需求分析_报价_latest.md` |\n"
        paths = check_state_paths.extract_paths_from_state(text)
        assert paths == [(1, "outputs/需求分析_报价_latest.md")]

    def test_extract_multiple_paths(self) -> None:
        text = """## 当前阶段产物
| 阶段 | 路径 |
| 1 | `outputs/需求分析_x_latest.md` |
| 4 | `outputs/prd_x_latest.html` |
"""
        paths = check_state_paths.extract_paths_from_state(text)
        assert len(paths) == 2

    def test_extract_versioned_path(self) -> None:
        text = "归档版本：`outputs/spec_x_v1.2_20260413.md`\n"
        paths = check_state_paths.extract_paths_from_state(text)
        assert paths[0][1] == "outputs/spec_x_v1.2_20260413.md"

    def test_skip_non_outputs_paths(self) -> None:
        text = "见 process_record/issues/ + outputs/x.md\n"
        paths = check_state_paths.extract_paths_from_state(text)
        assert len(paths) == 1
        assert paths[0][1] == "outputs/x.md"


class TestValidateVersionDate:
    def test_valid_date(self) -> None:
        assert check_state_paths.validate_version_date("20260413") is True

    def test_year_out_of_range(self) -> None:
        assert check_state_paths.validate_version_date("19990413") is False
        assert check_state_paths.validate_version_date("21000413") is False

    def test_month_out_of_range(self) -> None:
        assert check_state_paths.validate_version_date("20261313") is False
        assert check_state_paths.validate_version_date("20260013") is False

    def test_day_out_of_range(self) -> None:
        assert check_state_paths.validate_version_date("20260432") is False
        assert check_state_paths.validate_version_date("20260400") is False

    def test_non_numeric(self) -> None:
        assert check_state_paths.validate_version_date("2026abcd") is False

    def test_wrong_length(self) -> None:
        assert check_state_paths.validate_version_date("2026041") is False
        assert check_state_paths.validate_version_date("202604130") is False
