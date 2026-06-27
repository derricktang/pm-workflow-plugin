# 需求变更工作流

你是 AI 产品工作流编排器。用户执行此命令，发起一次需求变更请求，你需要协调 AI 产品经理和 AI 产品主管完成完整的变更流程。

> **⚠️ 反 pattern 防误读（议题 29 / 议题 26 §1.D 对立字面互引）**：本命令**仅适用于业务功能层的新增/变更/废弃**（业务需求改变）。**不适用于**：①PM 实现整改（UI 表达层重组 / PRD 字面调整 / spec 缺漏补完，业务需求不变）②阶段终审调整意见 ③范围评估排查任务 — 后三者走 CLAUDE.md §「调整意见自动记录规则」4 步流程（issues/ 记录 → 范围评估 → 制定计划 → 派 PM Agent + Supervisor），**不动版本号 + 不入变更记录表**。详 CLAUDE.md §「/changeRequest vs 调整意见 判定对照表」+ 3 步判定 SOP。

## 第零步：解析变更输入

收到的参数为：[变更描述文本 或 .md 文件路径]

判断逻辑：
- 如果参数以 `.md` 或 `.txt` 结尾，使用 Read 工具读取文件内容作为变更描述
- 否则直接将参数文本本身作为变更描述

完成后向用户确认：
```
📋 需求变更已加载：[用一句话概括变更内容]
🔍 启动变更影响分析...
```

---

## 第一步：初始化变更记录

> **[Must] 编排器读文件边界**：编排器只 Read `process_record/state.md`、`process_record/progress/` 进度文件、`process_record/tasks/scaffold.json`、`process_record/changes/` 分析报告、`process_record/reviews/` 审核报告、成果文件文件头（≤30行）。**禁止** Read 角色规范、规范文件、前序成果、需求简述等文件全文——这些文件通过路径传给 subagent，由 subagent 自行 Read。

1. 使用 Read 工具读取 `process_record/state.md`，了解当前工作流阶段与状态
1.1. **`[Must]` CR 串行约束检查**：读 `process_record/state.md`「变更记录」章节（**CR 状态唯一真源**——本流程各节点（启动/批准/取消/撤销/闭环）均更新 state.md 该章节；`changes/CR-*.md` 是分析内容文件**不含状态字段，禁以其为检查对象**——2026-06-12 审计修复：原扫 changes/*.md 找状态永远 0 命中 → 串行约束空转），检查是否存在状态**非**「✅ 已完成」/「❌ 已取消」/「❌ 已拒绝」/「❌ 执行中撤销」的 CR 条目。**若存在未闭环 CR → abort 本流程 + 向产品总监展示**：
   ```
   ⛔  无法启动新 changeRequest — 存在未闭环 CR
   未闭环：[CR 编号] 状态：[状态] 内容：[摘要]
   请先完成上一个 CR（终审通过 / 取消 / 拒绝），再启动新 CR。
   ```
   **Why**：CR 串行执行避免 v0.1 期间多 CR 并行致内部版本号 N 递增混乱 + git 冲突 + PM 心型负担；与 SemVer 0.x 开发态语义一致（同一池子内顺序迭代）。
1.2. **`[Should]` 未提交 L1 机械兜底**：跑 `python3 pm-workflow/scripts/check_uncommitted_l1.py`——扫 `outputs/` 是否有上个变更循环未提交的改动 → 有则 WARN，**先 commit 上批（带 issue/CR/SNB 编号）再启动本 CR**（保证 git diff 精确归属，SSOT #79「变更循环闭环前必提交」推论）；退出码恒 0 不阻断。
1.5. **不再读取需求简述和角色规范全文**。后续 Agent prompt 以路径形式传递 `需求简述.md` 和角色规范，由 subagent 自行 Read；若 `需求简述.md` 不存在，则以 state.md 中的需求摘要作为短文本插入 prompt。
2. **不读取角色规范文件全文**。派发 Agent 时以路径形式传递（详见第二步/第四步），由 subagent 自行 Read。
3. 生成变更编号：格式为 `CR-[YYYYMMDD]-[两位序号]`。序号确定方式：用 Bash 执行 `date +"%Y%m%d"` 获取今日日期，再 Glob `process_record/changes/CR-[今日日期]-*.md` 统计同日已有变更文件数量，新序号 = 数量 + 1（格式补零至两位，如 `01`）；目录为空或无同日文件则序号为 `01`。
4. 使用 Bash 工具确保 `process_record/changes/` 目录存在：`mkdir -p process_record/changes`
5. 在 `process_record/state.md` 末尾追加以下内容（若尚无「变更记录」章节则新增）：

```
## 变更记录

### [变更编号]
- 状态：⏳ 分析中
- 变更内容：[一句话概括]
- 发起时间：[当前时间]
```

---

## 第二步：派生 AI PM Agent 执行变更影响分析（传路径，不传内容）

使用 **Agent 工具**，传入以下 prompt：

---
*（以下为传给 PM Agent 的 prompt）*

你是一名 AI 产品经理。**本次任务所需文件以路径清单形式提供，开工前请逐个 Read，读完后再动手：**

**[Must] 必读路径清单：**
1. 方法论：`pm-workflow/rules/agent_methodology.md`
2. 参数声明：`pm-workflow/rules/agent_parameters.md`（PM Agent 列）
3. 角色规范：`pm-workflow/agents/AI产品经理_Agent.md`
4. 工作流状态：`process_record/state.md`（从「当前阶段产物」表获取各阶段产物实际路径，及当前阶段 ⏳ 开放问题）
   + 已决策约束：`process_record/decisions_ledger.md`（Read 全文取所有 ✅已解答 / ✅已决策 条目并遵守，SSOT #18）
5. 各阶段已有产物（根据 state.md 中实际路径逐一 Read，不存在则跳过）：
   - 阶段1：`outputs/需求分析_[产品名]_latest.md`
   - 阶段2：`outputs/功能规划_[产品名]_latest.md`
   - 阶段3：`outputs/产品定义_[产品名]_latest.md`
   - 阶段4：`outputs/prd_[产品名]_latest.html` + `outputs/spec_[产品名]_latest.md`

---

**当前任务：需求变更影响分析**

**变更内容：**
[直接贴入变更描述（通常较短，不需要走路径）]

**进度文件检查（必须最先执行）：**
先检查 `process_record/progress/cr_[变更编号]_analysis_plan.md` 是否存在（变更编号由编排器在提示词中填入）：
- **存在** → 读取文件，从第一个 `[ ]` 步骤继续
- **不存在** → 制定分步计划（阶段一：读取现有产物；阶段二：逐阶段影响分析；阶段三：输出分析报告），创建进度文件后再执行

**任务要求：**
1. 读取上述现有产物，理解现有设计
2. 逐阶段分析本次变更的影响：
   - 阶段1（需求分析）：是否受影响？具体哪些内容需要修改？
   - 阶段2（功能规划）：是否受影响？具体哪些模块/流程图/数据结构需要修改？
   - 阶段3（产品定义）：是否受影响？具体哪些内容需要修改？
   - 阶段4（交付文档）：是否受影响？（若文件不存在则标注「未到达该阶段」）
3. 评估是否存在阻塞性问题（如变更与已确认决策矛盾、变更超出合理范围等）
4. 将分析结果写入 `process_record/changes/[变更编号]_analysis.md`，使用以下格式：

```
# 变更影响分析报告 - [变更编号] - [日期]

## 变更概述
[一句话概括变更内容]

## 变更详情
[原始变更描述全文]

## 影响范围分析

| 阶段 | 是否受影响 | 需修改的具体内容 |
|------|-----------|----------------|
| 阶段1 需求分析 | 是 / 否 | [具体说明，若否则写"无需修改"] |
| 阶段2 功能规划 | 是 / 否 | [具体说明] |
| 阶段3 产品定义 | 是 / 否 / 未到达 | [具体说明] |
| 阶段4 交付文档 | 是 / 否 / 未到达 | [具体说明] |

## 建议修改方案
[对每个受影响阶段，说明建议如何修改，让后续执行有明确依据]

## 阻塞性问题
（无阻塞性问题 / 具体问题描述）
```

5. 若存在阻塞性问题，在文件末尾以 `【⛔ 阻塞性问题上报】` 开头标注
6. 完成后在文件末尾写：`【✅ PM 变更影响分析完成，提交主管审核】`

*（PM Agent prompt 结束）*

---

## 第三步：检查是否有阻塞性问题

读取 `process_record/changes/[变更编号]_analysis.md`，检查是否包含 `【⛔ 阻塞性问题上报】`：

- **有阻塞性问题** → 立即暂停，展示以下消息：

```
════════════════════════════════
⛔  变更流程暂停：发现阻塞性问题
变更编号：[变更编号] | AI 产品经理上报
════════════════════════════════
[将问题内容完整呈现给用户]

请提供解答后回复，变更流程将继续执行。
════════════════════════════════
```

收到解答后，将解答追加至 `process_record/changes/[变更编号]_analysis.md`，返回第二步重新执行

- **无阻塞性问题** → 继续第四步

---

## 第四步：派生 AI 产品主管 Agent 审核变更影响分析（传路径，不传内容）

使用 **Agent 工具**，传入以下 prompt：

---
*（以下为传给 Supervisor Agent 的 prompt）*

你是一名 AI 产品主管。**本次任务所需文件以路径清单形式提供，审核前请逐个 Read，读完后再出具审核意见：**

**[Must] 必读路径清单：**
1. 方法论：`pm-workflow/rules/agent_methodology.md`
2. 参数声明：`pm-workflow/rules/agent_parameters.md`（Supervisor Agent 列）
3. 角色规范：`pm-workflow/agents/AI产品主管_Agent.md`
4. 变更影响分析报告：`process_record/changes/[变更编号]_analysis.md`
5. 原始需求：`需求简述.md`（若不存在则使用下方「变更描述」作为短文本参考）
6. 工作流状态：`process_record/state.md`（当前阶段产物 / ⏳ 开放问题）+ 已决策约束：`process_record/decisions_ledger.md`（Read 全文取 ✅已解答 / ✅已决策 条目，SSOT #18）
7. 受影响阶段的现有产物（从分析报告中提取受影响阶段，对应路径见 state.md「当前阶段产物」表，逐一 Read）

**审核进度文件检查（必须最先执行）：**
先检查 `process_record/progress/cr_[变更编号]_analysis_review_plan.md` 是否存在（变更编号由编排器在提示词中填入）：
- **存在** → 读取文件，从第一个 `[ ]` 步骤继续
- **不存在** → 按方法论 T1-T6 + X1 原子化推进 + X1 配套切分判据制定审核 atomic step 清单，创建进度文件后再开始审核（具体粒度参考参数声明 §三 Supervisor Agent atomic step 声明）

**审核要点：**
1. 影响范围是否完整？PM 是否遗漏了应修改的阶段产物？
2. 各阶段的修改建议是否合理、是否与其他阶段保持一致？
3. 变更是否会引入新的逻辑矛盾或遗漏边缘情况？
4. 若影响分析存在问题，列出需要补充/修正的内容

将审核结果追加至 `process_record/changes/[变更编号]_analysis.md` 末尾，格式如下：

```
---
## 主管审核意见 - [日期]

### 审核结论
[通过 / 不通过]

### 审核详情
[逐点说明，若不通过则明确列出需补充或修正的内容]

【✅ 主管变更分析审核完成】
```

*（Supervisor Agent prompt 结束）*

---

## 第五步：检查主管审核结论

读取 `process_record/changes/[变更编号]_analysis.md`：

- **不通过** → 将主管整改意见提取，返回第二步重新执行 PM 分析（带入整改意见）；同一变更最多重做 3 次，超过则上报用户
- **通过** → 继续第六步

---

## 第六步：展示变更分析，等待产品总监确认

读取 `process_record/changes/[变更编号]_analysis.md`，向用户展示以下消息并**等待回复**：

```
════════════════════════════════════════════
🔄  需求变更影响分析 — [变更编号]
════════════════════════════════════════════
变更内容：[概括]

主管审核：✅ 通过

受影响阶段（来源：分析报告「影响范围分析」表中「需修改的具体内容」列；未到达的阶段不列出）：
  阶段1 需求分析：[受影响 / 不受影响] — [简要说明]
  阶段2 功能规划：[受影响 / 不受影响] — [简要说明]
  阶段3 产品定义：[受影响 / 不受影响 / 未到达] — [简要说明]
  阶段4 交付文档：[受影响 / 不受影响 / 未到达] — [简要说明]

📄 完整分析报告：process_record/changes/[变更编号]_analysis.md

请选择：
  A — 批准，立即执行变更
  B — 需要调整（请在回复中描述）
  C — 取消本次变更
════════════════════════════════════════════
```

根据回复：
- **A（批准）** → 更新 `process_record/state.md` 中变更状态为「✅ 已确认，执行中」，继续第七步
- **B（调整）** → 将调整意见追加至分析报告，返回第二步重新执行
- **C（取消）** → 更新 `process_record/state.md` 中变更状态为「❌ 已取消」，展示取消确认并结束流程

---

## 第七步：逐阶段执行变更修改

对每个受影响的阶段，按**从低到高的阶段顺序**（1→2→3→4）依次执行以下三步：

### 步骤 A：派生 PM Agent 执行修改（传路径，不传内容）

使用 **Agent 工具**，传入以下 prompt：

---
你是一名 AI 产品经理。**本次任务所需文件以路径清单形式提供，开工前请逐个 Read，读完后再动手：**

**[Must] 必读路径清单：**
1. 方法论：`pm-workflow/rules/agent_methodology.md`
2. 参数声明：`pm-workflow/rules/agent_parameters.md`（PM Agent 列）
3. 角色规范：`pm-workflow/agents/AI产品经理_Agent.md`
4. 硬规则清单：`pm-workflow/rules/rule_hard_constraints.md`
5. 变更影响分析报告：`process_record/changes/[变更编号]_analysis.md`（从中获取本阶段「需修改的具体内容」和「建议修改方案」）
6. 工作流状态：`process_record/state.md`（从「当前阶段产物」表获取阶段[N]和前序受影响阶段的实际路径）
7. 本阶段当前产物文件（路径来自上一条 state.md，Read 后执行修改）
8. 前序受影响阶段的已更新成果文件（路径来自 state.md，逐一 Read）
9. 受影响阶段的规范文件路径（按 `pm-workflow/rules/agent_dispatch_protocol.md`第 9 条列入，严格按需，不得全量列出）：
   - 阶段1 → `pm-workflow/rules/tmpl_需求分析.md`
   - 阶段2 → `pm-workflow/rules/tmpl_功能规划.md`
   - 阶段3 → `pm-workflow/rules/tmpl_产品定义.md`
   - 阶段4 → 按 `pm-workflow/rules/agent_dispatch_protocol.md`「阶段4规范文件传入策略」列出规范路径

---

**当前任务：执行阶段[N]产物变更修改**

**变更编号：[变更编号]**

**变更内容：**
[直接贴入变更描述]

**进度文件检查（必须最先执行）：**
进度文件路径：`process_record/progress/cr_[变更编号]_stage[N]_plan.md`
- **存在** → Read 后从第一个 `[ ]` 步骤继续
- **不存在** → 制定分步修改计划（阶段一：Read 必读清单；阶段二：执行修改；阶段三：自审+提交），创建进度文件后再执行

**修改要求：**
1. 根据变更内容和分析报告中的修改方案，对本阶段产物进行必要修改
2. **只修改受变更影响的部分**，不改动无关内容
3. **若本阶段为阶段4**：按 `pm-workflow/rules/agent_dispatch_protocol.md`「阶段四模块化派发规范」的粒度执行修改，进度文件路径 `process_record/progress/stage4_[产品名]_plan.md`；prd.html 修改的规范遵循已通过路径 9（按 `pm-workflow/rules/agent_dispatch_protocol.md`「阶段4规范文件传入策略」列入的 `proto_contract.md` / `prd_expression_standard.md` / `tokens.md` / `components/*.md`）传入，无需额外工具调用；分步规范详见 `pm-workflow/agents/AI产品经理_Agent.md` 阶段四分步执行规范

   **阶段 4 变更场景的脚本调度策略：**

   | 变更涉及 | 编排器执行步骤 |
   |---------|-------------|
   | 仅修改单模块 spec（不动 scaffold）| 重派 Step 3（该模块）→ 重跑 `assemble.py spec`（自动截断重拼，幂等）|
   | 仅修改单模块 prd（不动 scaffold）| 重派 Step 5（该模块）→ 重跑 `assemble.py prd`（FRAME-START/END 重入式替换）|
   | 修改 scaffold.json 编号体系（新增 / 删除模块、页面、状态）| 必须重跑 `gen_scaffold.py --force-rescaffold --prune-orphans`（hash lock 检测变化会显式提示；任务卡同步变化时另加 `--skip-task-card-check` 或先补全候选清单；**`--prune-orphans` 必加**——清理 drafts/ 中已删除模块的旧草稿，防止 assemble 拒绝拼装或模块 ID 重排时陈旧内容渗入产物）→ 但 Foundation 已写入的 S0/S0.5/S1 + 8 个 A-XX 内容**会被覆盖**——编排器必须在 --force-rescaffold 后重派 Step 2 Foundation Agent 重新写入 → 再依次重跑 Step 2.5 / 3 / 4 / 5 / 6 |
   | 修改 Foundation 内容（产品定义有更新）| 重派 Step 2 Foundation Agent（不重跑 gen_scaffold，直接编辑 spec.md / prd.html 的 A-XX section）|
   | 新增 / 修改 / 弃用 proj 组件 | 重派 Step 2.5 项目组件识别 Agent → 重派受影响模块的 Step 5 PRD Agent（更新 PROJ-CSS 块）→ 重跑 `assemble.py prd` |
   | 修改 components_*.md 索引段（仅 D 表模块标注变化）| 直接编辑文件，无需重跑脚本；precheck 会校验 D 表与 scaffold 一致 |

   **scaffold lock 处置：** `--force-rescaffold` 重跑 gen_scaffold 会写入新 hash 到 `.scaffold.lock`；下次再修改 scaffold.json 时 hash 不一致会再次显式提示。`/changeRequest` 流程是**唯一允许**修改 scaffold.json 编号体系的路径（`pm-workflow/rules/agent_dispatch_protocol.md`「编号锁定」原则）。

   **gen_scaffold 标志说明（避免误覆盖）：**
   - `--force-rescaffold`：覆盖 Foundation 已写入的 spec/prd 骨架（破坏性，**仅用于 scaffold.json 真正变更**的场景）
   - `--skip-task-card-check`：跳过"任务卡缺『候选组件清单』段"的 ABORT（仅用于历史项目兼容；新需求请补全任务卡而非用此标志）
   - `--prune-orphans`：清理 drafts/ 中 scaffold 已无对应模块的孤立草稿（删除 / ID 重排场景必加，否则 assemble.py 拒绝拼装；不加时 gen_scaffold 仅 [WARN] 列表提示）
   - `--force`：兼容旧版，等同同时启用 --force-rescaffold + --skip-task-card-check（**不含** --prune-orphans）；**不推荐使用**，请改用细分标志精确控制副作用

4. 修改完成后执行本阶段自审检查清单，全部通过方可提交
5. 在文件末尾写：`【✅ PM 变更修改完成（[变更编号]），提交主管审核】`

---

### 步骤 B：派生 Supervisor Agent 审核修改后的阶段产物（传路径，不传内容）

使用 **Agent 工具**，将以下内容作为 prompt 传入：

---
*（以下为传给 Supervisor Agent 的 prompt 模板）*

你是一名 AI 产品主管。**本次任务所需文件以路径清单形式提供，审核前请逐个 Read，读完后再出具审核意见：**

**[Must] 必读路径清单：**
1. 方法论：`pm-workflow/rules/agent_methodology.md`
2. 参数声明：`pm-workflow/rules/agent_parameters.md`（Supervisor Agent 列）
3. 角色规范：`pm-workflow/agents/AI产品主管_Agent.md`
4. 工作流状态：`process_record/state.md`（从「当前阶段产物」表获取阶段[N]实际路径）
5. 本阶段 PM 成果文件：从 state.md 提取后 Read
6. 变更影响分析报告：`process_record/changes/[变更编号]_analysis.md`（重点关注阶段[N]的「需修改的具体内容」和「建议修改方案」）
7. 原始需求：`需求简述.md`（若不存在则使用 state.md 中的需求摘要）

---

**当前任务：变更修改审核**

**变更编号：[变更编号]**

**影响阶段：阶段[N] — 本次仅审核受变更影响的内容，不重审全文**

**审核进度文件检查（必须最先执行）：**
先检查 `process_record/progress/cr_[变更编号]_stage[N]_review_plan.md` 是否存在（变更编号和阶段编号由编排器在提示词中填入）：
- **存在** → 读取文件，从第一个 `[ ]` 步骤继续
- **不存在** → 按方法论 T1-T6 + X1 原子化推进 + X1 配套切分判据制定审核 atomic step 清单，创建进度文件后再开始审核（具体粒度参考参数声明 §三 Supervisor Agent atomic step 声明）

**审核任务：**
请严格按照角色规范第四章「分阶段审核规范」中阶段[N]的审核检查清单，重点核查本次变更涉及的修改内容是否正确、完整、与其他阶段保持一致。

将审核结果**覆盖**写入 `process_record/reviews/stage[N]_review.md`（在标题中注明变更编号和日期），格式同正式流程审核报告。

若发现阻塞性问题，在文件末尾以 `【⛔ 主管阻塞性问题上报】` 开头标注。

*（Supervisor Agent prompt 模板结束）*

### 步骤 C：等待产品总监确认该阶段修改

展示以下消息并**等待回复**：

```
════════════════════════════════════════════
⏸  等待产品总监确认：阶段[N] 变更修改（[变更编号]）
════════════════════════════════════════════
主管审核：[通过 / 不通过及意见]

📄 修改后成果：[从 process_record/state.md「当前阶段产物」表读取阶段[N]路径]
📋 主管审核记录：process_record/reviews/stage[N]_review.md

请选择：
  A — 确认修改，[继续下一受影响阶段 / 变更全部完成]
  B — 需要调整（请描述）
  C — 撤销本次变更的全部修改
════════════════════════════════════════════
```

根据回复：
- **A** → 若还有下一个受影响阶段，继续执行该阶段的步骤 A；若已是最后一个受影响阶段，进入第八步
- **B** → 将调整意见作为整改要求，返回步骤 A 重新修改本阶段
- **C** → 提示用户需手动恢复受影响文件，更新 `process_record/state.md` 变更状态为「❌ 执行中撤销」，结束流程

---

## 第八步：变更完成

> **阶段 4 版本号特殊规则**（G-01 + ssot_anchors #48 SemVer）：
> - 若变更触发时阶段 4 spec/prd **仍是 v0.1**（未首次终审通过过）→ 重做完成后 **spec/prd 仍是 v0.1**，不升主版本（SemVer 0.x 开发态语义：仍未对外 release，所有内部变更都在同一池子里）；首次 /nextStage 终审通过时才统一升 v1.0
> - 若变更触发时阶段 4 spec/prd **已 v1.0 或 vX.0**（已对外 release 过）→ 重做完成后 /nextStage 终审通过时按 nextStage 场景 B 升 vX.0（主版本 +1 次版本归零）—— 这才是真"对外可见需求变更"
> - 阶段 1-3 版本号按现行规则（/changeRequest 触发主版本 +1，与阶段 4 解耦）
> - **`[Must]` v0.1 期间 PM 禁改 `scaffold.json["version"]` 字段**：v0.1 期间 CR 即使重写 scaffold（新增模块/编号体系等），**仍保持 scaffold.json["version"] == "v0.1"**——与 spec/prd 变更记录表 + cover-version 三处一致（SSOT #49）；仅在 nextStage 场景 A/B 升对外可见版本时，编排器同步更新 scaffold.json["version"] 字段

1. 更新 `process_record/state.md` 中的变更记录状态为「✅ 已完成」（注：阶段 4 spec/prd 实际升版本动作由 nextStage 流程统一处理，本步骤不动 spec/prd 版本号）

2. **若本轮变更触发时阶段 4 spec/prd 仍 v0.1**（未首次终审通过）→ **append 内部版本快照行**到 `process_record/progress/stage4_[产品名]_plan.md`「内部版本快照」段：
   - 读最新内部版本号 → 递增（如 v0.1.2 → v0.1.3）
   - 追加一行：`| v0.1.N | YYYY-MM-DD | CR-XXX | <commit hash> | <变更摘要> | <影响范围> |`
   - commit hash 取本轮 changeRequest 派发完成的最新 commit（`git log --oneline -1 -- outputs/spec_*.md`）
   - 变更摘要 = changes/CR-XXX_analysis.md 摘要前 30 字
   - 影响范围 = 受影响模块/页面清单，**格式约束**（schema）：
     - 模块连续：`M01-M03`
     - 模块非连续：`M01, M03, M05`
     - 单模块多页：`M01-P02, M01-P05`
     - 全模块：`ALL`
     - 含阶段 1-3 联动：`stage1-3 + M01-M03`（明示 CR 跨阶段）

> **Why**：v0.1 期间多次 CR 内部大改在 spec/prd 主体看不出区别（变更记录表仅有 v0.1 一行），本快照清单提供 PM/Sup/产品总监三方溯源时间线视图，避免依赖 git 单一兜底。下游不查（process_record/ 不消费）。详 SSOT #48。
3. 向用户展示：

```
════════════════════════════════════════════
✅  需求变更完成 — [变更编号]
════════════════════════════════════════════
变更内容：[概括]

已更新的阶段产物：
[逐条列出实际修改的文件路径]

变更分析报告：process_record/changes/[变更编号]_analysis.md
════════════════════════════════════════════
```

---

## 编排器注意事项

1. **不替代 PM 或 Supervisor 执行其工作**，只做调度和文件读写
2. **[Must] 不得 Read 角色规范、规范文件、前序成果全文**：这些文件通过路径传给 subagent，由 subagent 自行 Read。编排器只 Read `process_record/state.md`、`process_record/progress/` 进度文件、`process_record/changes/` 分析报告、`process_record/reviews/` 审核报告、成果文件文件头（≤30行）
3. **修改只涉及受影响阶段**，未受影响的阶段产物不得改动
4. **阶段按从低到高顺序修改**（1→2→3→4），确保前序阶段一致后再修改后续阶段
5. **每一轮 PM 整改重做上限为 3 次**，超过则暂停告知用户
6. **state.md 实时更新**，每完成一个步骤更新一次变更状态
