# tests/test_dual_root.py
import os, importlib
from pathlib import Path

def test_framework_root_is_repo_root(monkeypatch):
    import pm_paths; importlib.reload(pm_paths)
    # pm_paths.py 在 <root>/pm-workflow/scripts/ → FRAMEWORK_ROOT 末两级为 pm-workflow/.. 的父
    assert (pm_paths.FRAMEWORK_ROOT / "pm-workflow" / "scripts" / "pm_paths.py").exists()

def test_project_root_uses_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    import pm_paths; importlib.reload(pm_paths)
    assert pm_paths.PROJECT_ROOT == tmp_path.resolve()

def test_project_root_falls_back_to_framework_root(monkeypatch, tmp_path):
    # 无 env 时回退到 FRAMEWORK_ROOT（而非 cwd）——保证 git-copy/测试零回归
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)  # 故意换 cwd，证明不依赖 cwd
    import pm_paths; importlib.reload(pm_paths)
    assert pm_paths.PROJECT_ROOT == pm_paths.FRAMEWORK_ROOT
