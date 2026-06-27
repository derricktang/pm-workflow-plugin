# 同步上游 L2 升级

你是 AI 产品工作流编排器。用户执行此命令，要求你**从上游 claude-code-pm-workflow 拉取最新 L2 升级**到当前下游产品仓（如 bujue-business-circle / bujue-payment-module / private-domain-homepage-module / bujue-quotation-tool 等）。

## 触发的自然语义变体

用户除了直接输入 `/syncUpstream`，也可能用以下自然语言变体触发同一动作 — **任一命中即按本命令执行**：

- 同步上游 / sync upstream / pull upstream
- 同步 L2 / sync L2 / 拉取 L2 / pull L2
- 拉取上游 / 更新工作流 / sync 工作流

## 上下游脚本归属（防错调）

**关键区分**：

| 角色 | 仓 | 脚本 / 函数 | 方向 |
|------|----|------------|------|
| **下游**（本命令适用）| bujue-business-circle / payment-module / private-domain-homepage-module / quotation-tool 等产品仓 | `bash pm-workflow/scripts/sync_from_upstream.sh` | **pull from upstream** |
| **上游** | claude-code-pm-workflow 工作流框架仓 | `sync_l2_all` / `sync_l2` shell function（`~/.bash_functions`） | **push to downstream** |

`[Must]` 当前是**下游仓**时本命令调用 `sync_from_upstream.sh`，**不要**调 `sync_l2` shell function（那是上游用的 push）。

判定方法：检查当前仓 git remote origin URL — 含 `claude-code-pm-workflow` 是上游，含其他产品名（business-circle / payment-module / private-domain-homepage-module / quotation-tool 等）是下游。

## 执行步骤

### 第一步：判定仓属性

跑 `git remote get-url origin 2>/dev/null` 看 URL 是否含 `claude-code-pm-workflow`。

- **是上游** → 提示用户「当前在上游仓，sync_from_upstream 无意义；上游用 `sync_l2_all` 推下游」并停止
- **是下游** → 进入第二步

### 第二步：调用 sync_from_upstream.sh 透传参数

跑：

```bash
bash pm-workflow/scripts/sync_from_upstream.sh $ARGUMENTS
```

`$ARGUMENTS` 是用户在命令后追加的选项（可能为空）。常用选项：

| 选项 | 作用 |
|------|------|
| `--dry-run` | 不实际改动，只展示将同步的文件清单 |
| `--no-commit` | rsync 后不自动 commit（用户手动审 diff 后再 commit） |
| `--no-push` | commit 后不自动 push（保留本地） |
| `--no-verify` | 跳过 pytest 验证（紧急修复 / 已知 pytest 故障时） |
| `--upstream-url URL` | 指定上游 git URL（默认从配置读取） |
| `--upstream-branch BRANCH` | 指定上游分支（默认 main） |

### 第三步：展示同步结果

脚本跑完后，把脚本的 stdout/stderr 完整贴给用户。重点 surface：

- ✅ / ❌ 各步是否成功（8 步：fetch → 备份 → rsync L2 → CLAUDE.md cp → .claude/commands cp → pytest 验证 → commit → push）
- 同步的 L2 文件数（`rsync --stats` 输出）
- L1 dirty 文件清单（如有 — WARN 不阻断）
- 任何 abort-guard 触发（L2 白名单越界 / dirty 状态过严等）

### 第四步：告知下一步

- 同步成功 → 提示用户「L2 已更新，可继续 PM 工作」
- 同步失败 → 复述失败步 + 给排查建议（grep memory `downstream_l2_sync_procedure` 7 Gotcha 对应症状）
- 处于 PM 阶段 4 等敏感工作 → 提示用户「同步可能影响进行中的 L1 任务，建议先 commit 当前 PM 进度再 sync」

## 注意事项

- **不要**在 sync 前后主动改 L1 文件（rsync 只动 L2 白名单，但编排器若擅自动 L1 会破坏对偶）
- **不要**对 sync 失败凭直觉 retry — 必先看脚本 stderr 找根因，对照 memory `downstream_l2_sync_procedure` 7 Gotcha
- 同步完成后**不自动**触发 PM Agent 重做 / 重 assemble，需用户显式指令
- 本命令仅做 L2 同步，**不**做 L1 重 assemble（assemble.py 是另一命令链路）

## 与上游同步约定对偶

上游 L2 commit 后**不再主动**跑 `sync_l2_all` 推下游 — 由下游用本命令 / 等价自然语义指令**主动拉**。这给下游 PM 接入时机的自主权（commit 间隙 / 议题闭环时一次性拉，不被上游强行中断）。
