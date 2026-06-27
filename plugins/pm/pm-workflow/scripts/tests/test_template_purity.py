"""测试 precheck_template_purity.py — 模板纯净度机械兜底（2026-06-12 审计补）。

该脚本被 pre-commit hook 调用（commit 时硬拦截），此前无任何测试 → 判定边界
漂移会让 hook 行为不稳。本文件守三件事：①真仓模板当前 PASS（退出码 0 基线）
②污染样本必 FAIL ③白名单不误伤。
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import precheck_template_purity as ptp


def test_real_repo_templates_currently_pass():
    """真仓 6 个代码类文件当前必须 PASS（main 退出码 0 基线锁定）。"""
    assert ptp.main() == 0


def test_polluted_file_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(ptp, "REPO_ROOT", tmp_path)  # scan_file 要求文件在 REPO_ROOT 下
    p = tmp_path / "fake_template.md"
    p.write_text(
        "<!-- 2026-06-12 issue # 12 整改：NB-WE-99 落地 -->\n正文内容\n",
        encoding="utf-8",
    )
    r = ptp.Report()
    ptp.scan_file(p, r)
    assert r.violations, "污染样本（日期 + issue + NB 引用）应命中违规"


def test_clean_file_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(ptp, "REPO_ROOT", tmp_path)
    p = tmp_path / "clean_template.md"
    p.write_text("# 模板标题\n\n占位 [YYYY-MM-DD] 与正文，无运维痕迹。\n", encoding="utf-8")
    r = ptp.Report()
    ptp.scan_file(p, r)
    assert not r.violations
