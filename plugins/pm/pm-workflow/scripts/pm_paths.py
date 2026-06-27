"""双根定位（SSOT）。框架文件用 FRAMEWORK_ROOT（只读），产物用 PROJECT_ROOT（读写）。
插件模式：Claude Code 设 CLAUDE_PROJECT_DIR → PROJECT_ROOT=用户项目；FRAMEWORK_ROOT 在只读 cache。
git-copy / 测试模式：无 CLAUDE_PROJECT_DIR → PROJECT_ROOT 回退到 FRAMEWORK_ROOT（= 旧 REPO_ROOT 行为，零回归）。"""
import os
from pathlib import Path

# 本文件位于 <plugin_root>/pm-workflow/scripts/pm_paths.py → parents[2] = <plugin_root>（含 pm-workflow/ 的目录）
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
# 回退到 FRAMEWORK_ROOT（而非 cwd）：保证无 env 时与旧 REPO_ROOT=__file__ 行为一致，现有测试不破
PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or FRAMEWORK_ROOT).resolve()
