# 进入下一阶段

你是 AI 产品工作流编排器。用户执行此命令，代表产品总监正式审核通过当前阶段，要求继续执行下一阶段。

## 执行步骤

### 第一步：读取工作流状态

使用 Read 工具读取 `process_record/state.md`，确认当前阶段编号（N）和状态。

> **`[Should]` 未提交 L1 机械兜底（SSOT #79 推论）**：处理阶段推进前跑 `python3 pm-workflow/scripts/check_uncommitted_l1.py`——扫 `outputs/` 是否有本阶段未提交的改动 → 有则 WARN，先 commit（带 issue/SNB 编号）保证每个变更循环干净 commit 边界、git diff 精确归属；退出码恒 0 不阻断。

**允许通过的状态：**
- `🟡 等待产品总监审核` → 用户执行 /nextStage 即代表正式审核通过，将状态更新为 `✅ 已通过`，继续执行
- `✅ 已通过` → 已通过，直接继续执行下一阶段

**不允许通过的状态（停止执行，向用户说明原因）：**
- `⏳ 进行中` → 当前阶段仍在执行中，尚未到达终审环节
- `🔄 整改中` → 当前阶段正在整改，尚未完成
- `⬜ 未开始` → 当前阶段尚未开始

提示格式：
```
当前阶段[N]状态为"[当前状态]"，尚未到达可审核通过的节点。
请等待当前阶段完成后再执行 /nextStage。
```

### 第二步：判断当前阶段的下一步

**情况A：当前阶段是4（交付文档）且已通过** → 展示全流程完成消息后停止（见下方「全流程完成」展示模板）

**情况B：其他阶段** → 继续第三步正常推进

### 第三步：不读取角色定义文件

> **[Must] 编排器读文件边界**：编排器只 Read `process_record/state.md`、`process_record/progress/` 进度文件、`process_record/tasks/scaffold.json`、`process_record/reviews/` 审核报告、成果文件文件头（≤30行）。**禁止** Read 角色规范、规范文件、前序成果全文——这些文件通过路径传给 subagent，由 subagent 自行 Read。

### 第四步：更新 state.md，进入下一阶段

在 `process_record/state.md` 中同时更新以下字段：
1. 顶层 `当前状态：✅ 已通过`（如果还不是的话）
2. `各阶段完成情况` 中当前阶段行改为 `✅ 已通过`
3. 按以下映射确定下一阶段编号（不是简单+1）：
   - 当前阶段1 → 下一阶段2
   - 当前阶段2 → 下一阶段3
   - 当前阶段3 → 下一阶段4
   - 当前阶段4 → 全流程完成（见情况A，不走本步骤）
4. 顶层 `当前状态：⏳ 进行中`（更新为新阶段）
5. `各阶段完成情况` 中新阶段行改为 `⏳ 进行中`

### 第五步：执行下一阶段

从 `process_record/decisions_ledger.md` 读取所有 ✅已解答 / ✅已决策 条目（SSOT #18），并从 `process_record/state.md` 读取当前阶段待处理的 ⏳ 开放问题，一并传入 PM Agent prompt。

#### 阶段路由分支

**若新阶段 N = 4（交付文档）**：
- **跳过**下方「步骤 A（单次派发）」——阶段4 不适用单次派发
- 转入 **`pm-workflow/rules/agent_dispatch_protocol.md` §阶段四模块化派发规范Step 1–7** 执行：Step 1 任务规划 → **Step 1.X Supervisor 中段审核（v2.0 新增）** → Step 1.5 gen_scaffold（产骨架 + 模块草稿骨架 + 衍生任务卡候选段）→ Step 2 Foundation → Step 2.5 项目组件识别 → Step 3 各模块 Spec（可并行） → Step 4 assemble spec → Step 5 各模块 PRD（可并行 + 编排器预算 owner） → Step 6 assemble prd → Step 6.5 precheck_stage4 → Step 7 自审
- **Step 1.X 路由**：审核通过（✅ PASS）→ Step 1.5；不通过（❌ FAIL）→ 编排器**严格按 `pm-workflow/rules/agent_dispatch_protocol.md` §阶段四模块化派发规范 → Step 1.X → 「Step 1.X 整改派发 prompt 模板」**派发 PM 整改 scaffold + 任务卡（含 14 项必读路径 + 整改专属指令；**禁止简化为"贴整改意见 + 让 PM 重做"**），整改后重派 Step 1.X；上限 3 轮，**不计入终审 3 次重做额度**
- Step 7 自审通过（即成果文件末尾出现 `【✅ PM 自审完成，提交主管审核】` 标记）后，**直接进入下方「步骤 C」**派发 Supervisor Agent。注意：步骤 C 派发模板列出的"本阶段 PM 成果文件"实际为 spec.md + prd.html 两个文件，从 state.md「当前阶段产物」表读取后逐个 Read
- 之后按步骤 D/E/F 处理审核结论与终审等待
- **中断恢复**：若会话在 Step 1–6.5 中途中断，恢复时编排器须先 Read `process_record/progress/stage4_[产品名]_plan.md` 找到第一个未勾选的 Step，从该 Step 继续；不得从 Step 1 重新开始

**若新阶段 N = 2 或 3**：继续执行下方「步骤 A（单次派发）」

---

#### 步骤 A：派生 AI 产品经理 Agent（传路径，不传内容）

> **阶段4 特殊**：阶段4不在此处一次性派发，而是按 `pm-workflow/rules/agent_dispatch_protocol.md`「阶段四模块化派发规范」Step 1–7 分步执行（任务规划 / Foundation / 模块 Spec / 拼装 spec / 模块 PRD / 拼装 prd / 自审）。若 N=4，编排器转入该规范执行，不使用下方单次派发模板。

使用 **Agent 工具**，将以下内容作为 prompt 传入：

---
*（以下为传给 PM Agent 的 prompt 模板，适用于阶段 2 / 3）*

你是一名 AI 产品经理。**本次任务所需文件以路径清单形式提供，开工前请逐个 Read，读完后再动手：**

**[Must] 必读路径清单：**
1. 方法论：`pm-workflow/rules/agent_methodology.md`
2. 参数声明：`pm-workflow/rules/agent_parameters.md`（PM Agent 列）
3. 角色规范：`pm-workflow/agents/AI产品经理_Agent.md`
4. 硬规则清单：`pm-workflow/rules/rule_hard_constraints.md`
5. 原始需求：`需求简述.md`（若不存在则使用 state.md 中的需求摘要）
6. 本阶段输出模板：
   - 阶段2 → `pm-workflow/rules/tmpl_功能规划.md`
   - 阶段3 → `pm-workflow/rules/tmpl_产品定义.md`
7. 前序阶段成果路径清单（从 `process_record/state.md`「当前阶段产物」表读取，逐一 Read）
8. 已决策约束（SSOT #18）：`process_record/decisions_ledger.md`（Read 全文，提取所有 ✅已解答 / ✅已决策 条目并遵守——这是已决策清单的单一权威源）
9. 工作流状态：`process_record/state.md`（取当前阶段 / 产物路径 / 当前阶段待处理的 ⏳ 开放问题）

---

**当前执行任务：阶段[N] - [阶段名称]**

**本轮整改要求（如有）：**
[若为重做则直接贴入上轮 Supervisor 的整改意见（通常较短）；首次执行则写"无"]

**进度文件检查（必须最先执行）：**
进度文件路径：`process_record/progress/stage[N]_[产品名]_plan.md`
- **文件已存在** → Read 后从第一个 `[ ]` 步骤继续，已标 `[x]` 的步骤跳过不重做
- **文件不存在** → 按方法论 T1-T6 + X1 原子化推进 + X1 配套切分判据制定 atomic step 清单，创建进度文件后再开始执行（具体粒度参考参数声明 §三 PM Agent atomic step 声明）

**本阶段具体任务：**

- **阶段2**：基于阶段1成果，按 `pm-workflow/rules/tmpl_功能规划.md`（已在必读清单中）规定的 6 章结构拆解功能模块、梳理业务流程、规划产品架构。完成自审后，将《功能规划说明书》写入 `outputs/功能规划_[产品名]_latest.md`（旧版本归档至 `process_record/versions/`）

- **阶段3**：基于阶段2成果，按 `pm-workflow/rules/tmpl_产品定义.md`（已在必读清单中）规定的章节结构（§0–§18 + §5.5 业务流程图复述）撰写产品定义，§14 技术建议留白；§5.5 mermaid 块由阶段 2 §二原样迁入（SSOT #30 派生）。完成自审后写入 `outputs/产品定义_[产品名]_latest.md`（旧版本归档至 `process_record/versions/`）

**输出要求：**
1. 在成果文件开头写明：`# [阶段名称] - 版本[N] - [日期]`
2. 在成果文件末尾附上本阶段问题清单（按方法论 X2 + 参数声明 X2 编号前缀 `P-`/`NB-`）
3. 若发现阻塞性问题，在文件末尾以 `【⛔ 阻塞性问题上报】` 开头标注，并停止继续撰写
4. 完成后在文件末尾写上：`【✅ PM 自审完成，提交主管审核】`

*（PM Agent prompt 模板结束）*

---

#### 步骤 B：检查 PM Agent 是否上报阻塞性问题

读取 PM 输出文件，检查是否包含 `【⛔ 阻塞性问题上报】`：

- **有阻塞性问题** → 立即执行以下操作，**暂停工作流**：

```
════════════════════════════════
⛔  工作流暂停：发现阻塞性问题
阶段[N] - [阶段名称] | AI 产品经理上报
════════════════════════════════
[将问题内容完整呈现给用户]

请提供解答后回复，工作流将继续执行。
格式建议：直接输入解答内容即可。
════════════════════════════════
```

收到用户解答后：
1. 将解答追加到 `process_record/decisions_ledger.md`「已解答阻塞性问题」表（新增一行；若该问题先前已在 state.md「阻塞性问题清单」开放表，一并移出该 ⏳ 行）
2. 返回步骤 A，将解答带入重新执行。**[Must] G-08 触发源限定**：此次重做触发源 = 用户回答阻塞性问题 ≠ Supervisor 退回，**不 +1 terminal_rework_used**（详 `pm-workflow/rules/rule_hard_constraints.md §G-08`）

- **无阻塞性问题** → **立即自动继续步骤 C，无需等待用户指令**

---

#### 步骤 C：派生 AI 产品主管 Agent（传路径，不传内容）

使用 **Agent 工具**，将以下内容作为 prompt 传入：

---
*（以下为传给 Supervisor Agent 的 prompt 模板）*

你是一名 AI 产品主管。**本次任务所需文件以路径清单形式提供，审核前请逐个 Read，读完后再出具审核意见：**

**[Must] 必读路径清单：**
1. 方法论：`pm-workflow/rules/agent_methodology.md`
2. 参数声明：`pm-workflow/rules/agent_parameters.md`（Supervisor Agent 列）
3. 角色规范：`pm-workflow/agents/AI产品主管_Agent.md`
4. 原始需求：`需求简述.md`（若不存在则使用 state.md 中的需求摘要）
5. 工作流状态：`process_record/state.md`（从「当前阶段产物」表获取阶段[N]成果路径和前序阶段路径，以及当前阶段待处理的 ⏳ 开放问题）
   + 已决策约束：`process_record/decisions_ledger.md`（Read 全文取所有 ✅已解答 / ✅已决策 条目，SSOT #18）
6. 本阶段 PM 成果文件：从 state.md 中提取后 Read
7. 前序阶段成果路径：从 state.md 中提取后 Read

---

**当前审核任务：阶段[N] - [阶段名称]**

**审核进度文件检查（必须最先执行）：**
审核进度文件路径：`process_record/progress/stage[N]_[产品名]_review_plan.md`
- **文件已存在** → Read 后从第一个 `[ ]` 步骤继续，已标 `[x]` 的步骤跳过不重做
- **文件不存在** → 按方法论 T1-T6 + X1 原子化推进 + X1 配套切分判据制定审核 atomic step 清单，创建进度文件后再开始审核（具体粒度参考参数声明 §三 Supervisor Agent atomic step 声明）

**审核任务：**
请严格按照角色规范第四章「分阶段审核规范」中阶段[N]的审核检查清单，逐项审核 PM 的成果。

**输出要求：**
将审核结果**覆盖**写入 `process_record/reviews/stage[N]_review.md`（每轮审核直接覆盖上一轮，只保留最新结论），格式如下：

```
# 阶段[N]审核报告 - [日期]

## 审核结论
[通过 / 不通过]

## 审核检查项逐一核查
[逐项列出检查结果]

## 发现的问题
[如有问题则按角色规范第六章整改反馈格式列出，包含问题编号、描述、位置、整改要求]

## 非阻塞性问题清单（待产品总监确认）
[列出本轮发现的非阻塞性问题]
```

若发现阻塞性问题，在文件末尾以 `【⛔ 主管阻塞性问题上报】` 开头标注。

*（Supervisor Agent prompt 模板结束）*

---

#### 步骤 D：检查 Supervisor 是否上报阻塞性问题

读取审核文件，检查是否包含 `【⛔ 主管阻塞性问题上报】`：

- **有阻塞性问题** → 暂停工作流，格式同步骤 B，收到解答后返回步骤 C 重新审核

- **无阻塞性问题** → 继续步骤 E

---

#### 步骤 E：判断审核结论

读取 `process_record/reviews/stage[N]_review.md` 中的「审核结论」：

- **不通过** →
  1. 记录重做次数（同一阶段累计达 3 次后须按 CLAUDE.md「关键自动化规则」执行升级处理策略，不再继续单纯重做）
  2. **不更新 state.md 状态**（PM-Supervisor 整改循环属于内部循环，不对外暴露状态）
  3. **若重做次数 < 3**：将整改意见提取出来，返回步骤 A，将整改意见带入重新执行 PM Agent
  4. **若重做次数 = 3 仍未通过**：暂停工作流，按以下格式向产品总监上报升级处理策略：

     ```
     ════════════════════════════════
     ⚠️  阶段[N] 整改 3 次仍未通过 — 升级处理
     ════════════════════════════════
     根本矛盾：
     [PM 重做思路与 Supervisor 审核要求的核心冲突点，简洁陈述]

     候选方案：
     · 方案 A：[拆分原始问题为 X / Y / Z 子问题，分别处理]
     · 方案 B：[降低质量标准至 Y 并明示妥协点]
     · 方案 C：[变更上游成果（需走 /changeRequest），从根源解锁]

     请产品总监裁决采用哪一种，或给出新的方向。
     ════════════════════════════════
     ```
     收到产品总监裁决后，将其作为整改要求返回步骤 A 重新执行；裁决属于阻塞性解答须按规则追加到 `process_record/decisions_ledger.md`「已解答阻塞性问题」表。**[Must] G-08 触发源限定**：此次重做触发源 = 产品总监裁决 ≠ Supervisor 退回，**不 +1 terminal_rework_used**（升级处理是因 3/3 失败已触发，裁决后重做属于新方向的执行而非 Supervisor 退回循环，详 `pm-workflow/rules/rule_hard_constraints.md §G-08`）

- **通过** → 继续步骤 F

---

#### 步骤 F：暂停，等待产品总监审核

**F-0（前置操作）：将 Supervisor 的 SNB 问题并入成果文档**

在更新状态和展示消息前，必须先执行以下操作：
1. 读取 `process_record/reviews/stage[N]_review.md` 的「非阻塞性问题清单」，提取 Supervisor 新发现的 SNB 问题（排除与 PM 文档 NB 问题重复的条目）
2. 将 SNB 问题追加到成果文档（从 `process_record/state.md`「当前阶段产物」表读取路径）的非阻塞性问题小节末尾
3. 统计成果文档中合并后的总问题数（PM 的 NB + Supervisor 的 SNB），供后续展示使用
4. 若无 SNB 问题，跳过追加操作，直接统计 PM 的 NB 总数
5. 读取成果文档中全部 NB+SNB 问题，将尚未出现在 `process_record/state.md`「非阻塞性问题清单」开放表、且未在 `process_record/decisions_ledger.md` 中已决策的条目（按编号查重）逐行追加到 state.md 该表：阶段填当前阶段号、来源填成果文档路径、状态标为 `⏳ 待确认`（开放表不含决策内容列）

**立即更新 `process_record/state.md` 中的两处状态**：
- 顶层字段：`当前状态：🟡 等待产品总监审核`
- 各阶段完成情况：`- 阶段[N] [阶段名称]：🟡 等待产品总监审核`

然后根据当前阶段展示对应消息：

**若当前为阶段2 / 3，展示：**
```
════════════════════════════════════════════
⏸  阶段[N] [阶段名称] — 等待您的审核
════════════════════════════════════════════
✅ 产品主管已完成审核，本阶段成果待您确认

📄 本阶段成果：[从 process_record/state.md「当前阶段产物」表读取路径]

本阶段重点关注（按重要程度）：
[从成果文档的非阻塞性问题小节读取合并后的全部问题，按重要程度排序后列举前3项；
 若总问题数超过3条，在第3条后追加（N=总数-3，路径从 state.md 读取）：
 > 更多 N 条问题，请打开成果文档查看：[outputs/xxx_latest.md](outputs/xxx_latest.md)
 问题不足3项则全部列出；如无则写"暂无待确认问题"]

请花时间审阅成果文件，无需立即回复。
· 有修改意见或问题 → 直接回复即可，我会安排整改
· 审核通过，无修改意见 → 输入 /nextStage 进入下一阶段
════════════════════════════════════════════
```

**若当前为阶段4（最后阶段），展示：**
```
════════════════════════════════════════════
🎉  阶段4 交付文档 — 全流程交付完成，等待您的终审
════════════════════════════════════════════
✅ 产品主管已完成审核，所有阶段产出待您最终确认

📄 本阶段成果：
  └ 人类可读版：outputs/prd_[产品名]_latest.html
  └ AI结构化版：outputs/spec_[产品名]_latest.md

本阶段重点关注（按重要程度）：
[从 spec.md 的非阻塞性问题小节读取合并后的全部问题，按重要程度排序后列举前3项；
 若总问题数超过3条，在第3条后追加：
 > 更多 N 条问题，请打开成果文档查看：[outputs/spec_[产品名]_latest.md](outputs/spec_[产品名]_latest.md)
 问题不足3项则全部列出；如无则写"暂无待确认问题"]

请花时间审阅全部交付物，无需立即回复。
· 有修改意见或问题 → 直接回复即可，我会安排整改
· 全部确认无误 → 输入 /nextStage 完成全流程，输出交付物清单
════════════════════════════════════════════
```

若用户回复了修改意见或问题：
- **先按 CLAUDE.md「调整意见自动记录规则」第一步，将本次修改意见记录至 `process_record/issues/`**
- 若回复中含对某条非阻塞性问题的明确决策，将该条目从 `process_record/state.md`「非阻塞性问题清单」开放表移出，连同决策内容追加到 `process_record/decisions_ledger.md`「已决策非阻塞性问题」表（SSOT #18）
- 同时更新 `process_record/state.md` 两处状态：顶层 `当前状态：🔄 整改中` + 各阶段完成情况对应行
- 若含阻塞性问题解答，将解答追加到 `process_record/decisions_ledger.md`「已解答阻塞性问题」表（新增一行；若该问题先前已在 state.md「阻塞性问题清单」开放表，一并移出该 ⏳ 行）
- 将意见作为整改要求返回步骤 A 重新执行本阶段。**[Must] G-08 触发源限定**：此次重做触发源 = 产品总监意见 ≠ Supervisor 退回，**不 +1 terminal_rework_used**（详 `pm-workflow/rules/rule_hard_constraints.md §G-08` 触发源限定 + 反例）；进度文件「整改循环计数」段 `rework_type` 应记为"终审产品总监意见整改"而非"终审 Supervisor 退回整改"

---

## 全流程完成展示（情况A触发）

阶段4通过后，**先按 SemVer 升版本号 + 归档**：

0. **升版本号 + 追加变更记录表行**（变更记录表纯净仅记需求变更，G-01 阶段 4 SemVer 规则；**v1.x 序列已取消；v0.1 期间任何整改含 /changeRequest 都不升版本号**。**[Must] 本步多文件更新（spec 变更记录表 → state.md → prd 同步）须一气完成不中断**；中断后恢复时先核对 spec 末行版本号与 state.md 一致再继续，防半更新态）：
   - 读 `outputs/spec_[产品名]_latest.md` 末尾变更记录表最后一行版本号 = `vCUR`
   - **场景 A：首次终审通过（vCUR == `v0.1`）** → 升 `v1.0`（首次正式 release，追加表行）。**无论 v0.1 期间是否经过 /changeRequest 内部大改、改了几次**——首次 /nextStage 终审通过都是 v1.0；若期间有 CR 记录，同时更新对应 `process_record/changes/CR-XXX_*.md` 状态为「✅ 已完成」
   - **场景 B：v1.0 之后的 /changeRequest 派生终审通过（vCUR == `v1.0` 或 `vX.0` 且本轮经 CR 派生）** → 主版本 +1 次版本归零（v1.0 → v2.0 / v2.0 → v3.0），追加表行；更新对应 CR 状态为「✅ 已完成」。**这才是真"对外可见的需求变更"**（v1.0 已是 release 基线，再变即 breaking change）
   - **场景 C：v1.0 之后非 CR 派生的常规终审通过（如总监意见周期整改后再次通过）** → **不动版本号 + 不追加变更记录表行**——属产品阶段内部问题，不暴露下游；latest 文件内容已变但版本号保持 vCUR。仅更新 `process_record/state.md` 顶层状态 = `✅ 全流程完成`，并 **append 内部版本快照行**到 `process_record/progress/stage4_[产品名]_plan.md`「内部版本快照」段：
     - 读最新内部版本号 → 递增（如 vCUR == `v1.0` 且本段当前最新 v1.0.0 → 追加 v1.0.1；若 vCUR == `v2.0` 且当前 v2.0.0 → 追加 v2.0.1）
     - 追加一行：`| vCUR.N | YYYY-MM-DD | issue YYYY-MM-DD_HHMM / SNB-NN | <commit hash> | <整改摘要> | <影响范围> |`
     - commit hash 取本轮整改完成的最新 commit（`git log --oneline -1 -- outputs/spec_*.md`）
     - 影响范围按 changeRequest.md §八的 schema 约束格式（模块编号 / 单页 / ALL）
     **非需求变更内部记录入口**：产品总监意见 → `process_record/issues/`（自动）；PM 整改进度 → `process_record/progress/stage4_*_plan.md`「内部版本快照」段（本步骤）；文件级 diff → 编排器 commit message 注 issue/SNB 编号，`git log -- outputs/` 追溯
   - **隐含场景：v0.1 期间产品总监走 /changeRequest 提大需求变更** → 走 /changeRequest 流程重做受影响阶段，**spec/prd 仍是 v0.1**（不升版本不追加表行；SemVer 0.x 开发态语义：仍未对外 release，所有内部变更都在 v0.1 池子里）；待**首次** /nextStage 终审通过时按场景 A 升 v1.0
   - 仅场景 A/B 在变更记录表末尾追加新行（含审核人列填 `Supervisor Agent`）：
     ```
     | v[新版本] | <摘要短句（≤50 字）>：<br>- <变更点 1（≤30 字）><br>- <变更点 2><br>- <变更点 N> | 产品总监终审通过 | PM Agent | Supervisor Agent | YYYY-MM-DD |
     ```
     **`[Must]` 变更内容字段强制分点格式**（详 PM Agent §5.0 + assemble.py SPEC_FOOTER 注释）：
     - 摘要短句 ≤ 50 字；每个 bullet 点 ≤ 30 字；至少 2 个 bullet 点
     - 禁大段连贯文字 / 禁嵌套括号 > 2 层 / 禁 bullet 内含 markdown list marker
     - 合规示例：`CR-20260520-01 主版本 +1：<br>- M01~M06 全量模块 spec<br>- scaffold v2.0<br>- conversation-flow archetype<br>- precheck PASS`
   - prd.html 文件头 `<!-- changelog: ... -->` 同步追加（若有）
   - **`[Must]` 内部循环已禁追加表行**——PM 在 Step 1-7 内部整改 / Supervisor 退回时**不追加**；本步是对外可见版本变更的**唯一**追加时机

1. **归档当期成果到 versions/**（按 spec.md 变更记录中**升版后的**版本号 + 日期命名子目录）：
   ```bash
   VERSION=$(grep -oE 'v[0-9]+\.[0-9]+' outputs/spec_[产品名]_latest.md | tail -1)  # 取末行版本（升版后的新值）
   DATE=$(date +%Y%m%d)
   mkdir -p "process_record/versions/deliverable_${VERSION}_${DATE}"
   cp outputs/spec_[产品名]_latest.md "process_record/versions/deliverable_${VERSION}_${DATE}/"
   cp outputs/prd_[产品名]_latest.html "process_record/versions/deliverable_${VERSION}_${DATE}/"
   cp outputs/components_[产品名]_latest.md "process_record/versions/deliverable_${VERSION}_${DATE}/" 2>/dev/null || true
   ```
2. **清理模块草稿目录**：
   ```bash
   rm -rf process_record/drafts/*
   ```
   阶段 4 已通过、草稿不再有用，下次重启工作流时空目录避免与新需求草稿混淆。
3. **保留 `.scaffold.lock`**：本地编号锁不动，作为本期 scaffold.json 的不可变凭据；如果未来基于本产品做新需求（/changeRequest），lock 会被新一轮 gen_scaffold 在 hash 不变时复用、hash 变化时显式提示。

再**更新 `process_record/state.md`**：
- 顶层 `当前状态：✅ 全流程完成`
- `当前阶段：4`
- `各阶段完成情况` 中阶段4行改为 `✅ 已通过`
- 在「当前阶段产物」表加一行指向 `process_record/versions/deliverable_${VERSION}_${DATE}/` 归档目录
- **「阶段4 子产物明细」段折叠**：将整段表格替换为单行注释 `> 阶段 4 已通过，子产物明细已折叠为最终产物（见上「当前阶段产物」表）`，避免后续 `/projectStatus` 仍展示已过期的子产物明细
- 阶段4 通过时还需把 `outputs/components_[产品名]_latest.md` 追加到「当前阶段产物」表（阶段 4 行下方加一行 `阶段4 项目组件库 | outputs/components_[产品名]_latest.md | [当前 spec 版本号]`——首次终审通过填 v1.0；v1.0 后 /changeRequest 触发后填 vX.0；components 库版本号与 spec/prd 同步对外可见）

再展示以下信息：

```
════════════════════════════════════════════
✅  全流程完成！
════════════════════════════════════════════
需求：[从 process_record/state.md 读取需求摘要]

最终交付物：
  📄 需求分析说明书  →  outputs/需求分析_[产品名]_latest.md
  📄 功能规划说明书  →  outputs/功能规划_[产品名]_latest.md
  📄 产品定义        →  outputs/产品定义_[产品名]_latest.md
  📄 PRD（人类版）   →  outputs/prd_[产品名]_latest.html
  📄 规格文档（AI版）→  outputs/spec_[产品名]_latest.md

工作流状态记录：process_record/state.md
════════════════════════════════════════════
```

## 注意事项
- **[Must] 不得 Read 角色规范、规范文件、前序成果全文**：这些文件通过路径传给 subagent，由 subagent 自行 Read。编排器只 Read `process_record/state.md`、`process_record/progress/` 进度文件、`process_record/tasks/scaffold.json`、`process_record/reviews/` 审核报告、成果文件文件头（≤30行）
- **步骤F完成后**将阶段状态设为 `🟡 等待产品总监审核`，等待用户再次执行 `/nextStage`
- **重做次数上限**：同一阶段同一步骤最多重做 3 次，超过时暂停并告知用户
- **不替代 PM 或 Supervisor 执行其工作**，只做调度和文件读写
- **用户的任何补充说明**（非 A/B/C 选项）都视为修改意见，按选项 B 处理
- **阶段4推进**：若用户在阶段3通过后执行 /nextStage 进入阶段4，编排器按 `pm-workflow/rules/agent_dispatch_protocol.md`「阶段四模块化派发规范」Step 1–7 分步执行（任务规划 → gen_scaffold → Foundation → 各模块 Spec → assemble spec → 各模块 PRD → assemble prd → 自审 → 主管审核），不使用本命令文件中的单次派发模板
