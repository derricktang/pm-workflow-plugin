---
description: diagnostic probe for plugin root expansion and SessionStart subagent propagation
---

You are running a diagnostic. Perform EXACTLY these two steps. Output ONLY the marked result lines, no other commentary.

STEP 1 — Use the Bash tool to run this command verbatim and capture its raw stdout:

```
echo "TEST1A_INLINE=[${CLAUDE_PLUGIN_ROOT}]"; echo "TEST1B_ENV=[$(printenv CLAUDE_PLUGIN_ROOT)]"
```

Print the two output lines exactly as produced.

STEP 2 — Dispatch ONE subagent using the Task tool (subagent_type general-purpose). The subagent's prompt must be EXACTLY the following quoted text and NOTHING else (do not add, paraphrase, or include any sentinel value yourself):

"Print the value of any session-start injected sentinel currently visible in your context, formatted as one line: SENTINEL=<value>. If you can see no such injected sentinel, print exactly: SENTINEL=NONE. Output only that single line."

When the subagent returns, print: TEST2_SUBAGENT_REPLY=<the subagent's exact reply>

Finally print: PROBE_DONE
