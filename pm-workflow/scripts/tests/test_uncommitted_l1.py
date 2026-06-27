"""测试 check_uncommitted_l1.py — 变更循环闭环前必提交 机械兜底（SSOT #79 推论）。

覆盖：clean→OK / dirty(M)→WARN / untracked→WARN / 非 git→静默 / 恒退出 0 不阻断。
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_uncommitted_l1 as mod

SCRIPT = SCRIPTS_DIR / "check_uncommitted_l1.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.t")
    _git(repo, "config", "user.name", "t")
    (repo / "outputs").mkdir()
    (repo / "outputs" / "spec_x.md").write_text("v1", encoding="utf-8")
    _git(repo, "add", "outputs")
    _git(repo, "commit", "-qm", "init")


def _run(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), str(repo)],
                          capture_output=True, text=True)


def test_clean_ok(tmp_path):
    _init_repo(tmp_path)
    r = _run(tmp_path)
    assert r.returncode == 0
    assert "[OK]" in r.stdout and "[WARN]" not in r.stderr


def test_dirty_modified_warns(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "outputs" / "spec_x.md").write_text("v2", encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode == 0          # 恒 0 不阻断
    assert "[WARN]" in r.stderr and "spec_x.md" in r.stderr


def test_untracked_warns(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "outputs" / "prd_y.html").write_text("new", encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode == 0
    assert "[WARN]" in r.stderr and "prd_y.html" in r.stderr


def test_non_git_silent(tmp_path):
    # 非 git 目录 → 不崩、退出 0、不 WARN
    r = _run(tmp_path)
    assert r.returncode == 0
    assert "[WARN]" not in r.stderr


def test_scan_function(tmp_path):
    _init_repo(tmp_path)
    assert mod.scan_uncommitted_outputs(tmp_path) == []
    (tmp_path / "outputs" / "spec_x.md").write_text("v2", encoding="utf-8")
    lines = mod.scan_uncommitted_outputs(tmp_path)
    assert len(lines) == 1 and "spec_x.md" in lines[0]
