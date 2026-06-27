"""复刻 assemble.py:33-40 的真实路径写法，对比 BUGGY（现状）与 FIXED（双根）。"""
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_paths import FRAMEWORK_ROOT, PROJECT_ROOT

# ---- BUGGY：assemble.py 现状（产物+框架同挂 __file__ 根）----
_BUGGY_ROOT = Path(__file__).resolve().parent.parent.parent
BUGGY_OUTPUT_DIR = _BUGGY_ROOT / "outputs"
BUGGY_DRAFTS_DIR = _BUGGY_ROOT / "process_record" / "drafts"
BUGGY_TEMPLATE   = _BUGGY_ROOT / "pm-workflow" / "rules" / "prd_template.html"

# ---- FIXED：双根（产物→PROJECT_ROOT，框架→FRAMEWORK_ROOT）----
FIXED_OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIXED_DRAFTS_DIR = PROJECT_ROOT / "process_record" / "drafts"
FIXED_TEMPLATE   = FRAMEWORK_ROOT / "pm-workflow" / "rules" / "prd_template.html"
