"""Test E3: doc_query.py resolves bare pm-workflow/ file args via FRAMEWORK_ROOT fallback.

When the caller's cwd is NOT the framework root, a bare path like
`pm-workflow/rules/agent_dispatch_protocol.md` should still resolve correctly
because doc_query falls back to FRAMEWORK_ROOT / args.file.
"""

import subprocess
import sys
import pathlib

SCRIPTS = pathlib.Path(__file__).resolve().parents[1]


def test_resolves_framework_relative_path(tmp_path, monkeypatch):
    """From a non-framework cwd, bare pm-workflow/... path resolves via FRAMEWORK_ROOT."""
    monkeypatch.chdir(tmp_path)
    target = "pm-workflow/rules/agent_dispatch_protocol.md"
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "doc_query.py"), "outline", target],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"未能按 FRAMEWORK_ROOT 解析裸路径:\n{r.stderr}"
