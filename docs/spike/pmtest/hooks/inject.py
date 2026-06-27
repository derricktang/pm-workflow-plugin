import json
# Inject a unique sentinel via SessionStart additionalContext.
# If this string shows up in a SUBAGENT's context, SessionStart propagates to subagents.
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "PMTEST_SENTINEL=ZQ7K9X2W4M (this line was injected by the pmtest SessionStart hook at session start)"
    }
}))
