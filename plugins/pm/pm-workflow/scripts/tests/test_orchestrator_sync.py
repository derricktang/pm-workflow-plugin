"""Test that orchestrator.md is in sync with CLAUDE.md (--check returns 0)."""
import subprocess, sys, pathlib

SCRIPTS = pathlib.Path(__file__).resolve().parents[1]


def test_orchestrator_regenerates_identically():
    gen = SCRIPTS / "gen_orchestrator.py"
    r = subprocess.run([sys.executable, str(gen), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, (
        f"orchestrator.md 与 CLAUDE.md 锚区不同步:\n{r.stdout}\n{r.stderr}"
    )
