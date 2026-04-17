# pm-workflow plugin

一个 AI 驱动的产品经理工作流插件：从一句话需求出发，经过 **需求分析 → 功能规划 → 产品定义 → 交付文档（PRD + 交互原型）** 四个阶段，由两个 AI Agent（产品经理 + 产品主管）协作闭环产出可交付文档。

## 特性

- 5 个斜杠命令驱动四阶段流程（`/newRequirement`、`/nextStage`、`/projectStatus`、`/changeRequest`、`/issueReview`）
- 2 个 Agent 规范分别约束 PM 产出与 Supervisor 审核
- 4 份模板保证各阶段产物章节结构一致（需求分析 / 功能规划 / PRD / 原型设计规范）
- 7 个产品管理 skill 覆盖 JTBD、Story Mapping、OST 等常用方法
- PM 完成 → 自动派发 Supervisor 审核 → 不通过自动重做的全闭环
- 产品总监（用户）的调整意见会被自动记录到 `process_record/issues/`，可通过 `/issueReview` 复盘
- 当前适配 Claude ，后续将扩展至更多 AI Agent

## 安装

### 方式一：本地开发安装

```bash
claude --plugin-dir /path/to/pm-workflow-plugin
```

### 方式二：从 marketplace 安装（待后续发布）

```bash
/plugin install pm-workflow@derricktang/pm-workflow-plugin
```

## 依赖

本插件内置的 7 个产品管理 skill 已随 plugin 一并安装，无需额外配置。但阶段 4（交付文档）依赖以下**外部插件**，请在使用 `/newRequirement` 走到阶段 4 之前完成安装，否则 prd.html 生成会失败：

| 依赖 | 类型 | 用途 | 安装方式 |
|------|------|------|---------|
| `frontend-design` plugin（含 `frontend-design:frontend-design` skill） | Claude Code plugin | 阶段 4 生成/重做 prd.html 之前由 PM Agent 强制调用，负责高品质前端设计输出 | `/plugin install frontend-design@anthropic`（或官方 marketplace 检索） |

> 未来若新增外部依赖会在此表补充。本插件自身（commands / agent-specs / rules / skills）不需要任何运行时依赖。

## 使用

1. 在你的新项目目录创建 `需求简述.md`，写入初始需求描述
2. 运行 `/newRequirement 需求简述.md`
   - 首次运行会自动在当前目录生成 `CLAUDE.md`（包含工作流规则与目录约定）
   - 自动创建 `outputs/`、`process_record/` 等目录
3. 按阶段推进：每阶段完成后编排器会展示终审总结，你输入 `/nextStage` 进入下一阶段
4. 随时用 `/projectStatus` 查看进度；需求有变用 `/changeRequest`；对已交付成果有意见直接在对话里说，自动记录

## 目录结构

```
pm-workflow-plugin/
├── .claude-plugin/
│   └── plugin.json                   # 插件清单
├── shared/                           # 跨工具共享的核心资产
│   ├── agent-specs/                  # 两个 AI Agent 行为规范
│   │   ├── AI产品经理_Agent.md
│   │   └── AI产品主管_Agent.md
│   ├── rules/                        # 四阶段输出模板
│   │   ├── 需求分析模板.md
│   │   ├── 功能规划模板.md
│   │   ├── PRD_Template.md
│   │   └── Prototype_Design_Spec.md
│   ├── skills/                       # 7 个产品管理技能
│   │   ├── epic-breakdown-advisor/
│   │   ├── jobs-to-be-done/
│   │   ├── opportunity-solution-tree/
│   │   ├── problem-statement/
│   │   ├── proto-persona/
│   │   ├── user-story/
│   │   └── user-story-mapping/
│   └── templates/
│       └── project-claude-md.md      # 供 /newRequirement 写入用户项目根的 CLAUDE.md
└── claude-code/
    └── commands/                     # Claude Code 斜杠命令
        ├── newRequirement.md
        ├── nextStage.md
        ├── projectStatus.md
        ├── changeRequest.md
        └── issueReview.md
```

## 路线图

- **v1.x**：Claude Code 全功能支持
- **v2.0**：新增 `codex/` 子目录，提供 OpenAI Codex CLI 适配层（Agent 规范与模板保持共享，仅重写命令触发方式）
- **v2.x**：Gemini CLI / Copilot CLI 适配

## 致谢

本插件 `shared/skills/` 下的 7 个产品管理 skill 基于以下开源项目改编与扩展，感谢作者 [@deanpeters](https://github.com/deanpeters) 的系统化梳理：

- **[deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills)** — 产品经理日常方法论（JTBD / 问题陈述 / User Story / Story Mapping / Proto-Persona / Opportunity Solution Tree 等）的 skill 化沉淀

部分 skill 的提示词模板同时引用自 [`deanpeters/product-manager-prompts`](https://github.com/deanpeters/product-manager-prompts)，已在各 `SKILL.md` 文件末尾注明来源。

另外致谢：
- Richard Lawrence & Peter Green 的 **Humanizing Work 拆分用户故事方法论**（`epic-breakdown-advisor` skill 基于该方法实现）

## 作者

derricktang

## 许可

MIT
