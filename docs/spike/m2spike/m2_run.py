import os, sys, importlib, tempfile
from pathlib import Path
BASE = Path(__file__).resolve().parent / "m2spike"
SCRIPTS = BASE / "pm-workflow" / "scripts"
sys.path.insert(0, str(SCRIPTS))

def reload():
    import pm_paths, asm_repro
    importlib.reload(pm_paths); importlib.reload(asm_repro)
    return asm_repro

fails = []
proj = Path(tempfile.mkdtemp())
os.environ["CLAUDE_PROJECT_DIR"] = str(proj)
a = reload(); fw = a.FRAMEWORK_ROOT
checks = [
    ("BUG  现状写法：产物落框架根(=只读cache)", str(a.BUGGY_OUTPUT_DIR).startswith(str(fw))),
    ("FIX  修复后：产物落项目根", str(a.FIXED_OUTPUT_DIR).startswith(str(proj))),
    ("FIX  修复后：产物绝不在框架/pm-workflow下", not str(a.FIXED_OUTPUT_DIR).startswith(str(fw / "pm-workflow"))),
    ("FIX  修复后：模板仍在框架根", str(a.FIXED_TEMPLATE).startswith(str(fw))),
]
os.environ["CLAUDE_PROJECT_DIR"] = str(fw)
a = reload()
checks.append(("GITCOPY 项目==框架时 fixed==buggy(零回归)", a.FIXED_OUTPUT_DIR == a.BUGGY_OUTPUT_DIR))
for name, ok in checks:
    print(("PASS " if ok else "FAIL ") + name)
    if not ok: fails.append(name)
print("\nRESULT:", "ALL PASS" if not fails else f"{len(fails)} FAILED")
os.environ["CLAUDE_PROJECT_DIR"] = str(proj); a = reload()
print("\n-- evidence (plugin mode, FRAMEWORK != PROJECT) --")
print("BUGGY_OUTPUT_DIR =", a.BUGGY_OUTPUT_DIR)
print("FIXED_OUTPUT_DIR =", a.FIXED_OUTPUT_DIR)
print("FIXED_TEMPLATE   =", a.FIXED_TEMPLATE)
