import importlib, sys
from pathlib import Path
SCRIPTS = Path(__file__).resolve().parent / "pm-workflow" / "scripts"
sys.path.insert(0, str(SCRIPTS))

def _reload():
    import pm_paths, asm_repro
    importlib.reload(pm_paths); importlib.reload(asm_repro)
    return asm_repro

def test_plugin_mode_bug_then_fix(monkeypatch, tmp_path):
    # 插件模式：项目根 ≠ 框架根
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    a = _reload()
    fw = a.FRAMEWORK_ROOT
    # BUG 实证：现状写法把产物挂到框架根（= 插件只读 cache）
    assert str(a.BUGGY_OUTPUT_DIR).startswith(str(fw)), "应复现 bug：产物落框架根"
    assert str(a.BUGGY_DRAFTS_DIR).startswith(str(fw))
    # FIX 实证：产物落项目根，且绝不在框架根下
    assert str(a.FIXED_OUTPUT_DIR).startswith(str(tmp_path))
    assert str(a.FIXED_DRAFTS_DIR).startswith(str(tmp_path))
    assert not str(a.FIXED_OUTPUT_DIR).startswith(str(fw / "pm-workflow"))
    # FIX 实证：框架文件仍在框架根
    assert str(a.FIXED_TEMPLATE).startswith(str(fw))

def test_gitcopy_backward_compatible(monkeypatch):
    a = _reload()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(a.FRAMEWORK_ROOT))
    a = _reload()
    # git-copy：项目根==框架根 → 修复后产物位置与现状一致（零回归）
    assert a.FIXED_OUTPUT_DIR == a.BUGGY_OUTPUT_DIR
    assert a.FIXED_DRAFTS_DIR == a.BUGGY_DRAFTS_DIR
