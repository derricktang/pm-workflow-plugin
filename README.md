# Claude PM Workflow

> 基于 Claude Code 的结构化产品经理工作流 —— 从需求到交付文档，AI 全程辅助，多层审核，可控变更。

---

## 插件安装（推荐）

### 安装

```bash
claude plugin marketplace add derricktang/pm-workflow-plugin
/plugin install pm@pm-workflow-market
```

> 仓库：https://github.com/derricktang/pm-workflow-plugin

### 更新

```bash
/plugin update
```

`/plugin update` 升级后，若模板/脚本有变，手动重生产物：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/assemble.py" spec --force-overwrite
python3 "${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/assemble.py" prd --force-overwrite
```

### 命令（均以 `/pm:` 命名空间为前缀）

| 命令 | 作用 |
|------|------|
| `/pm:newRequirement {简述}` | 启动新需求，从需求分析开始执行全四阶段 |
| `/pm:nextStage` | 产品总监正式通过当前阶段，推进至下一阶段 |
| `/pm:projectStatus` | 查看当前工作流进度简报 |
| `/pm:changeRequest` | 启动需求变更工作流 |
| `/pm:retro` | 复盘最新未分析的调整意见，输出根因分析 + 机制改进建议 |
| `/pm:investigate` | 临时排查专项（调研类子任务） |

---

## L2 演化策略

- **插件用户 = 纯消费者**：L2 框架文件（规范/模板/脚本/角色定义）由 maintainer 维护，插件目录只读，用户不直接修改。
- **改进反馈渠道**：通过源仓 **Issue 或 PR** 提交改进意见，maintainer 评审后硬化进下一版本，经 `/plugin update` 下发所有用户。
- **贡献者 / 本地 L2 修改**：`git clone` 源仓，本地修改后提 PR 回源；maintainer 审核合并后经 `/plugin update` 下发。
- **参考**：详细 L2 演进历史见 [`CHANGELOG_L2.md`](CHANGELOG_L2.md)。

---

## 工作流详细说明

> 以下为原工作流文档内容，适用于两种模式。

### 简介

`Claude PM Workflow` 是一套运行在 **Claude Code** 之上的产品经理工作流。你只需要用 `/pm:newRequirement + 需求简述` 下达指令，AI 便会自动依次执行 **需求分析 → 功能规划 → 产品定义 → 交付文档** 四个核心阶段。

每个阶段内部包含：
- **AI 自审** – 检查输出质量与完整性
- **AI 产品主管审核** – 模拟主管视角，提出修改意见
- **人类产品总监审核** – 最终确认，通过后解锁下一阶段

整个流程支持**状态查看**、**阶段跳转等待**、**需求变更影响分析**，并采用**规范的文件输出结构**，便于版本管理与多人协作。

---

### 快速开始

#### 插件模式（推荐）

安装插件后（见上方「插件安装」），在 Claude Code 对话中直接输入：

```
/pm:newRequirement 用户希望用手机号一键登录，支持验证码倒计时
```

AI 会自动开始 **阶段1：需求分析**，完成后等待你的审核，输入 `/pm:nextStage` 继续进入下一阶段。

---

### 特性

- **四阶段标准流程** – 需求分析 → 功能规划 → 产品定义 → 交付文档（prd.html + spec.md）
- **技能驱动分析** – 阶段1/2 内置结构化技能框架（proto-persona / JTBD / Problem Statement / OST / Epic Breakdown / Story Mapping / User Story），确保分析有据可循
- **多层审核机制** – AI 自审 + AI 主管 + 人类 PM，确保产出质量
- **状态持久化与恢复** – 随时 `/pm:projectStatus` 查看进度，AI 引导继续
- **智能需求变更** – `/pm:changeRequest` 自动分析影响范围，同步更新所有相关文档
- **显式阶段推进** – 必须使用 `/pm:nextStage` 进入下一步，避免 AI 过度自动
- **调整意见闭环** – `/pm:retro` 对已记录的调整意见进行根因分析与工作流优化
- **规范化输出** – 产出物、归档、变更记录、审核记录分目录存储，清晰可追溯

---

### 工作流程详解

```mermaid
graph TD
    A[/pm:newRequirement] --> B[阶段1: 需求分析]
    B --> C{AI自审+AI主管审核}
    C -- 通过 --> D{人类PM审核}
    D -- 通过 --> E[/pm:nextStage]
    E --> F[阶段2: 功能规划]
    F --> G{AI自审+AI主管审核}
    G -- 通过 --> H{人类PM审核}
    H -- 通过 --> I[/pm:nextStage]
    I --> J[阶段3: 产品定义]
    J --> K{AI自审+AI主管审核}
    K -- 通过 --> L{人类PM审核}
    L -- 通过 --> M[/pm:nextStage]
    M --> N[阶段4: 交付文档]
    N --> O{AI自审+AI主管审核}
    O -- 通过 --> P{人类PM审核}
    P -- 通过 --> Q[完成]
    Q --> R[prd_xxx_latest.html]
    Q --> S[spec_xxx_latest.md]

    style A fill:#90EE90,stroke:#006400
    style E fill:#FFD700,stroke:#8B8000
    style I fill:#FFD700,stroke:#8B8000
    style M fill:#FFD700,stroke:#8B8000
    style Q fill:#87CEEB,stroke:#000080
```

### 各阶段产出物与存储位置

| 阶段 | 产出物 | 存储路径 |
|------|--------|----------|
| 需求分析 | 用户画像、JTBD、问题陈述、业务场景、功能边界 | `./outputs/需求分析_[产品名]_latest.md` |
| 功能规划 | 功能模块清单、业务流程图、用户故事地图、产品架构 | `./outputs/功能规划_[产品名]_latest.md` |
| 产品定义 | 完整功能规格（用例、数据字典、验收标准，不含交互细节） | `./outputs/产品定义_[产品名]_latest.md` |
| 交付文档 | AI结构化规格（spec.md）+ 人类可读PRD（prd.html） | `./outputs/prd_[产品名]_latest.html` + `./outputs/spec_[产品名]_latest.md` |

> `prd.html` 以 `spec.md` 为唯一来源生成，两份文档内容保持严格对齐。

---

### 技能驱动分析

阶段1和阶段2引入结构化技能框架，确保需求分析和功能规划有方法论支撑：

**阶段1 需求分析（4步技能法）**

| 步骤 | 技能 | 目的 |
|------|------|------|
| 1 | proto-persona | 识别核心用户画像，锁定"为谁做" |
| 2 | jobs-to-be-done | 挖掘功能/社交/情感三维动机，找真实需求 |
| 3 | problem-statement | 将 JTBD 转化为可观测的问题陈述，不夹带解法 |
| 4 | opportunity-solution-tree | 发散机会、收敛解法方向，确定本次迭代范围 |

**阶段2 功能规划（3步技能法）**

| 步骤 | 技能 | 目的 |
|------|------|------|
| 1 | epic-breakdown-advisor | 将解法方向拆解为垂直可交付的 Story 切片 |
| 2 | user-story-mapping | 按用户旅程排布 Stories，形成主流程与迭代切片 |
| 3 | user-story | 将每条 Story 写成 Mike Cohn 格式 + Gherkin 验收条件 |

技能定义文件位于 `pm-workflow/skills/`（7个技能目录），通过 Claude Code Superpowers 插件加载。各技能的产出物为**中间分析产物**，PM 提炼关键结论后写入对应说明书章节。

---

### 完整目录结构（插件模式）

```
/
  ├── 需求简述.md                     # 当前需求的核心简述（由 /pm:newRequirement 写入）
  ├── README.md                       # 项目说明文档
  ├── CLAUDE.md                       # Claude Code 工作流总规范
  ├── pm-workflow/                    # 工作流框架资源（AI 角色规范 + 输出模板）
  │   ├── agents/
  │   │   ├── AI产品经理_Agent.md     # PM Agent：角色定义、4阶段执行规范、自审清单
  │   │   └── AI产品主管_Agent.md     # Supervisor Agent：审核规范、整改反馈格式
  │   └── rules/
  │       ├── tmpl_需求分析.md              # 阶段1输出模板
  │       ├── tmpl_功能规划.md              # 阶段2输出模板
  │       ├── tmpl_产品定义.md              # 阶段3产品定义模板
  │       ├── rule_hard_constraints.md      # 全程硬约束规则
  │       ├── proto_contract.md             # 阶段4全局约束（必传）
  │       ├── prd_expression_standard.md    # PRD文档表达规范（结构/布局/标准区块）
  │       ├── prd_template.html             # PRD主模板（规划阶段直接fork）
  │       ├── proto_spec_md.md              # spec.md 生成规范
  │       ├── proto_platform_app.md         # APP 端帧规范（手机/PAD）
  │       ├── proto_platform_desktop.md     # 桌面 Web 端帧规范
  │       ├── proto_platform_miniprogram.md # 微信小程序帧规范
  │       ├── proto_platform_h5.md          # 手机 H5 帧规范
  │       ├── proto_cross_platform.md       # 跨端规范（2个及以上端口时传入）
  │       ├── proto_spec_legacy.md          # 已拆分原始规范，保留备查
  │       ├── task_card_template.md         # 阶段四模块任务卡标准格式（模块 Agent 任务单）
  │       └── bujue-design-system/          # 不觉设计系统规范（阶段4必传）
  │   ├── scripts/                        # 阶段四自动化脚本
  │   │   ├── gen_scaffold.py             # 骨架生成：scaffold.json → spec/prd 骨架文件
  │   │   └── assemble.py                 # 拼装：spec草稿/prd草稿 → 最终交付文件
  │   └── skills/                         # 结构化分析技能（Superpowers 插件加载）
  │       ├── proto-persona/
  │       ├── jobs-to-be-done/
  │       ├── problem-statement/
  │       ├── opportunity-solution-tree/
  │       ├── epic-breakdown-advisor/
  │       ├── user-story-mapping/
  │       └── user-story/
  ├── .claude/commands/
  │   ├── newRequirement.md
  │   ├── nextStage.md
  │   ├── changeRequest.md
  │   ├── projectStatus.md
  │   ├── retro.md
  │   └── investigate.md
  ├── outputs/                        # 各阶段最新交付物（运行时生成，不入 git）
  └── process_record/                 # 工作流执行过程记录（运行时生成，不入 git）
      ├── state.md
      ├── decisions_ledger.md
      ├── reviews/
      ├── progress/
      ├── issues/
      ├── changes/
      ├── versions/
      ├── tasks/
      └── drafts/
```

---

### 需求变更示例

当你输入：
```
/pm:changeRequest 增加"一键登录前需要用户同意隐私协议"的勾选框
```

AI 会：
1. 分析变更涉及哪些阶段（需求分析、功能规划、产品定义、交付文档）
2. 梳理影响范围并列出调整计划，**等待产品总监确认后**再执行
3. 派发 PM Agent 更新受影响的文档，Supervisor 自动审核，不通过则循环整改
4. 将旧版本归档到 `process_record/versions/`
5. 在 `process_record/changes/` 中生成变更记录（含时间、描述、影响范围）
6. 输出变更摘要，提示你重新审核相关阶段

---

### 审核记录说明

- **AI 产品主管审核**：每次审核完成后，在 `process_record/reviews/` 生成审核报告（`stage[N]_review.md`），含通过/驳回理由及整改要求。
- **人类 PM 审核**：通过对话直接反馈，状态记录在 `process_record/state.md`。
- **调整意见记录**：产品总监在任何对话中提出的调整意见，自动记录至 `process_record/issues/`，可通过 `/pm:retro` 进行复盘分析。

---

### 常见问题

**Q: 人类审核时如何反馈？**
A: 直接回复"通过"或"审核通过"，AI 会记录并提示使用 `/pm:nextStage`。若不通过，请描述修改意见，AI 会重新修正当前阶段产出。

**Q: 可以跳过某个阶段吗？**
A: 不建议。工作流设计为顺序执行，若确有紧急情况，可使用 `/pm:changeRequest` 调整范围，或手动修改状态文件（高级操作）。

**Q: 中途关闭 Claude Code 后如何恢复？**
A: 重新打开后输入 `/pm:projectStatus`，AI 会自动读取 `process_record/state.md` 并恢复进度。

**Q: 为什么第四阶段要输出 `spec.md` 和 `prd.html` 两个文件？**
A: `spec.md` 是 AI 结构化规格文档，作为权威来源先生成；`prd.html` 是面向人类（PM、设计师、业务）的可视化文档，以 `spec.md` 为唯一来源派生生成。你审阅 `prd.html`，反馈的修改会先更新 `spec.md`，再同步到 `prd.html`，确保两份文档永远对齐。

**Q: 如何开始一个新的产品需求？**
A: 直接输入 `/pm:newRequirement 你的需求简述`。AI 会重置工作区，创建新的 `需求简述.md`，并从阶段1开始执行。

**Q: 技能（skills）是什么，需要单独安装吗？**
A: 技能是结构化分析框架，定义文件位于 `pm-workflow/skills/`，通过 Claude Code Superpowers 插件加载，无需额外安装步骤。AI 在执行阶段1和阶段2时会自动调用。

---

### 贡献指南

欢迎通过 Issue 或 PR 改进工作流规则、审核模板或分析技能。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-idea`)
3. 提交改动 (`git commit -m 'Add some amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-idea`)
5. 打开 Pull Request

---

### 许可证

MIT License © 2025
