# CLAUDE.md

> 本文件由 [pm-workflow plugin](https://github.com/derricktang/pm-workflow-plugin) 初始化。请勿删除或大幅修改下列工作流规则，否则编排器行为将偏离预期。自定义规则可追加到文件底部。

## 项目性质

这是一个由 **pm-workflow plugin** 驱动的 AI 产品工作流项目，所有产出均为 Markdown/HTML 文档。Claude Code 扮演编排器，协调两个 AI Agent（产品经理、产品主管）完成产品文档的全流程生产与审核。

---

## 斜杠命令

| 命令 | 说明 |
|------|------|
| `/newRequirement <需求文件或文字>` | 启动新需求工作流，从需求分析开始执行全四阶段 |
| `/nextStage` | 产品总监正式通过当前阶段，推进至下一阶段 |
| `/projectStatus` | 查看当前工作流进度简报 |
| `/changeRequest` | 启动需求变更工作流 |
| `/issueReview` | 分析最新未分析的调整意见文件，产出分析报告并标记为已分析 |

命令由 pm-workflow plugin 提供，插件同时封装了 PM/Supervisor Agent 规范与各阶段模板，无需在本仓库维护。

---

## 目录结构

```
outputs/                  # 各阶段最新成果（*_latest.md / *_latest.html）

process_record/           # 工作流执行过程中间记录，不建议删除
  state.md                # 当前工作流状态（必读，包含当前阶段、已解答问题、产物路径）
  versions/               # 历史归档版本
  progress/               # 各阶段分步进度文件（stage[N]_[产品名]_plan.md / _review_plan.md）
  reviews/                # 主管审核报告（stage[N]_review.md）
  issues/                 # 产品总监调整意见记录（按日期时间命名，状态：未分析/已分析）
  changes/                # 需求变更记录（每次 /changeRequest 生成）

需求简述.md                # 当前项目的原始需求输入（由用户提供）
```

> 工作流框架资源（PM/Supervisor Agent 规范、阶段模板）由 plugin 安装目录提供，位于 `${CLAUDE_PLUGIN_ROOT}/shared/agent-specs/` 与 `${CLAUDE_PLUGIN_ROOT}/shared/rules/`，由各斜杠命令自动引用，无须在本仓库维护。

---

## 工作流架构

### 四阶段流程

```
阶段1 需求分析 → 阶段2 功能规划 → 阶段3 产品定义 → 阶段4 交付文档
```

每个阶段的执行循环：
1. **编排器**读取 plugin 提供的 PM Agent 规范，以 Agent 工具派发 PM 执行
2. PM 完成后，**编排器立即**（无需用户确认）派发 Supervisor 审核
3. 审核不通过 → **编排器立即**派发 PM 整改 → 再次自动派发审核，循环直至通过（最多3次）
4. 审核通过后展示终审提交信息给产品总监，**等待** `/nextStage`

### 关键自动化规则（硬性要求）

- PM 完成任何阶段后（首次、重做、临时任务），**立即自动**派发 Supervisor 审核，不得询问用户
- Supervisor 审核不通过后，**立即自动**派发 PM 整改，不得询问用户
- 向产品总监提交终审时，**必须按重要程度列举前三个问题**重点关注
- 若同一问题经过3次整改仍未通过，PM 不得继续重复相同思路，须升级处理策略（如拆分问题、提出多套候选方案、列明根本矛盾请产品总监裁决）后继续推进，而非直接暂停等待

### 调整意见自动记录规则（硬性要求）

产品总监（用户）在任何对话中提出对已交付成果的调整意见时，**必须按以下顺序执行，不得跳过任何步骤**：

#### 第一步：记录意见

1. **检查未分析文件**：Glob `process_record/issues/*.md`，文件名**不含** `_analyzed` 后缀的为未分析文件
   - 存在未分析文件 → 将新意见追加到该文件的调整意见表末尾
   - 不存在未分析文件（目录为空或所有文件均含 `_analyzed`）→ 用 Bash 执行 `date +"%Y-%m-%d_%H%M"` 获取当前系统时间，创建新文件 `YYYY-MM-DD_HHMM.md`，写入表头和新条目
2. **拆分规则**：若用户一次性描述了多个独立问题，**每个问题单独一行**，禁止合并为一条记录
3. **记录格式**：每条意见一行，列：`# | 完整描述 | 影响成果文件 | 业务 | 功能逻辑`

#### 第二步：梳理调整范围

记录完成后，在对话中明确列出本次调整涉及的：
- 影响文件（具体文件路径）
- 影响位置（页面/章节/函数/行号等）
- 影响程度（仅局部修改 / 涉及多处联动 / 需同步更新其他文件）

#### 第三步：制定调整计划

在对话中输出具体的执行步骤列表（每步说明操作内容），**经用户确认或无异议后**再开始执行。

#### 第四步：派发 PM Agent 执行调整

**编排器本身不直接修改任何成果文件。** 调整计划确认后，必须：
1. 读取 plugin 提供的 PM Agent 规范，以 Agent 工具派发 PM 执行调整
2. PM 完成后，**立即自动**派发 Supervisor Agent 审核调整结果（同阶段正式流程规则一致）
3. 审核不通过 → 立即派发 PM 整改 → 再次审核，循环至通过
4. 审核通过后，向产品总监汇报完成情况

> **注意**：临时调整同样适用"PM完成→立即审核→循环整改"的全自动闭环规则，不因为是小改动而跳过审核。

**文件命名规范**：
- 未分析：`YYYY-MM-DD_HHMM.md`（时间必须来自系统 `date` 命令，禁止估算）
- 已分析：`YYYY-MM-DD_HHMM_analyzed.md`（由 `/issueReview` 命令执行重命名）

### 分步执行规范（硬性要求）

PM 和 Supervisor 在执行时必须维护进度文件（`process_record/progress/`），**每完成一个步骤立即将 `[ ]` 改为 `[x]`，严禁批量完成后统一更新**。进度文件用于支持中断后恢复。

---

## 当前项目状态

运行 `/projectStatus` 或直接读取 `process_record/state.md` 获取最新状态。

恢复工作时**必须先读取** `process_record/state.md`，从中获取：
- 当前阶段和状态
- 各阶段产物的实际文件路径和版本号
- 所有已解答的阻塞性/非阻塞性问题（**执行时不得忽略已确认的解答**）

---

## Agent 调用规范

派发 PM Agent 时，prompt 必须包含：
1. `${CLAUDE_PLUGIN_ROOT}/shared/agent-specs/AI产品经理_Agent.md` 完整内容（由 plugin 提供）
2. 原始需求（`需求简述.md` 内容）
3. 前序阶段成果文件路径
4. `process_record/state.md` 中所有已解答问题
5. 本轮整改要求（若为重做）
6. 进度文件检查指引（文件存在则继续，不存在则创建）
7. **受影响阶段的规范文件**（根据本次调整所涉及的阶段显式传入，并在 prompt 中明确要求 PM 动手前先读取）：
   - 调整涉及阶段1成果 → 传入 `${CLAUDE_PLUGIN_ROOT}/shared/rules/需求分析模板.md` 内容
   - 调整涉及阶段2成果 → 传入 `${CLAUDE_PLUGIN_ROOT}/shared/rules/功能规划模板.md` 内容
   - 调整涉及阶段3成果 → 传入 `${CLAUDE_PLUGIN_ROOT}/shared/rules/PRD_Template.md` 内容
   - 调整涉及阶段4成果 → 传入 `${CLAUDE_PLUGIN_ROOT}/shared/rules/Prototype_Design_Spec.md` 内容
   - 调整同时涉及多个阶段 → 逐一传入所有受影响阶段的规范文件

派发 Supervisor Agent 时，prompt 必须包含：
1. `${CLAUDE_PLUGIN_ROOT}/shared/agent-specs/AI产品主管_Agent.md` 完整内容（由 plugin 提供）
2. 原始需求
3. 待审核的成果文件路径（从 `process_record/state.md` 读取）
4. 前序成果路径
5. 审核进度文件检查指引

> **变更场景额外要求**：在 `/changeRequest` 流程中派发 Supervisor 审核时，prompt 还需额外传入「变更编号」和「本次仅审核受变更影响的内容，不重审全文」的说明。

---

## 文件命名规范

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 阶段1-2成果 | `[阶段名]_[产品名]_latest.md` | `功能规划_报价工具_latest.md` |
| 阶段3产物 | `产品定义_[产品名]_latest.md` | `产品定义_报价工具_latest.md` |
| 阶段4人类交付 | `prd_[产品名]_latest.html` | `prd_报价工具_latest.html` |
| 阶段4AI交付 | `spec_[产品名]_latest.md` | `spec_报价工具_latest.md` |
| 归档版本 | `[阶段名]_[产品名]_v[主版本].[次版本]_[YYYYMMDD].md` | `功能规划_报价工具_v1.4_20260413.md` |
| 执行进度 | `stage[N]_[产品名]_plan.md` | `stage2_报价工具_plan.md` |
| 审核进度 | `stage[N]_[产品名]_review_plan.md` | `stage2_报价工具_review_plan.md` |
| 审核报告 | `stage[N]_review.md` | `stage2_review.md` |

版本号规则：每次修改 +0.1（如 v1.0→v1.1）；变更请求（/changeRequest）触发时主版本+1（如 v1.x→v2.0）。
