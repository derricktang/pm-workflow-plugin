# Spike 结果：插件路径/注入机制实测（2026-06-28）

验证 rev.3.1 设计文档 §13.5 的两个残留确认点。环境：Claude Code 2.1.195，Windows。

## 复现命令

```powershell
# 在普通终端（非 Claude Code 会话内；嵌套会 403）
claude --plugin-dir <docs/spike/pmtest 的绝对路径> -p "/pmtest:probe" --permission-mode bypassPermissions --output-format text
```

探针：`pmtest/`（plugin.json + commands/probe.md + hooks/hooks.json + hooks/inject.py）。

## 实测输出

```
TEST1A_INLINE=[C:/.../scratchpad/pmtest]
TEST1B_ENV=[]
TEST2_SUBAGENT_REPLY=SENTINEL=NONE
PROBE_DONE
```

## 结论

| 点 | 结论 | 证据 |
|---|---|---|
| **A** `${CLAUDE_PLUGIN_ROOT}` 在 command 正文 | **加载时替换为绝对路径**（TEST1A 有值）；**非运行时环境变量**（TEST1B 为空）；`rules/*.md` 等 plain 文件 Read 进来**不替换** | TEST1A/1B |
| **D** SessionStart 注入是否到达 subagent | **不到达**（哨兵在 subagent 不可见）| TEST2=SENTINEL=NONE |

## 对设计的锁定

- 路径解析归一：subagent 从 plain 文件（rules/agent-spec）读到的所有 `pm-workflow/...`（335+98 引用 + 37 行 bash）一律按**派发任务消息携带的绝对插件根**解析。
- `${CLAUDE_PLUGIN_ROOT}` 变量仅用于 command 正文 / skill / agent 组件内容（4 行 command-body bash）。
- B/C（自定义路径合法、relative 相对 marketplace 根）由官方文档关闭。
