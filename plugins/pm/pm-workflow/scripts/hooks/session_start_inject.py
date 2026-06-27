"""SessionStart：注入 orchestrator.md（静态）+ 绝对插件根声明。stdout 必须只有 JSON。"""
import json, os
from pathlib import Path

root = os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).resolve().parents[3])
orch = Path(root) / "pm-workflow" / "core" / "orchestrator.md"
body = orch.read_text(encoding="utf-8") if orch.exists() else "(orchestrator.md 缺失)"
decl = (f"\n\n[插件根] 框架文件绝对根 = {root}。"
        f"派发任何 subagent 时，prompt 必须声明：所有 `pm-workflow/...` 路径相对 {root} 解析；"
        f"产物 outputs/、process_record/ 相对项目 cwd。")
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": body + decl}}))
