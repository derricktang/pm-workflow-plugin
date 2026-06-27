import os
from pathlib import Path
# 本文件位于 <root>/pm-workflow/scripts/pm_paths.py
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
