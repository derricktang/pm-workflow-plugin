# 设计文档：pm-workflow 封装为 Claude Code 插件（Phase 1）

- 文档日期：2026-06-28
- 状态：待 review
- 作者：编排器（Claude）+ 产品总监确认
- 范围：**Phase 1 = plugin + marketplace 打包**。Phase 0（CLAUDE.md 瘦身）为外部前置依赖，由产品总监在**原项目**中执行，本文档只给分区指引、不在本副本落地。
- **评审结论（2026-06-28）**：本文档已评审，逻辑错误清单 + 当前工作流优化方案见 `pm-workflow/workflow_backlog/2026-06-28_plugin-design-review_optimization-and-flaws.md`。**修订本文档前请先读该评审**——致命项 B-1（§6 Class C 433 处路径解析）/ B-2（D5 与 §12/§13 Phase 0 矛盾）。

---

## 0. 决策记录（brainstorming 已确认）

| # | 决策 | 选择 |
|---|------|------|
| D1 | 投入程度 / 目标覆盖面 | **Claude Code 单厂商旗舰，核心层厂商中立，结构预留跨厂商** |
| D2 | 编排大脑（CLAUDE.md 不被插件加载）处理 | **最小常驻锚**：精简核心经 SessionStart hook 注入，其余下沉 command/skill/rules 按需读 |
| D3 | 旧 sync 机制（pre-commit / install_hooks / syncUpstream）| **双模并存（过渡期）**：插件为主，git-copy 通道保留并标 deprecated |
| D4 | 发布仓布局 | **单仓**：marketplace + plugin 同仓 |
| D5 | Phase 0（CLAUDE.md 瘦身）执行归属 | **原项目，产品总监自做**；本副本只规划，不改工作流本体 |

---

## 1. 目标与非目标

### 目标
1. 把现有 pm-workflow 工作流框架（L2）封装为可发布、可 `/plugin install` 的 Claude Code 插件。
2. 单仓同时充当 marketplace，用户 `claude plugin marketplace add <repo>` 后即可安装。
3. 核心层（rules / templates / agent-specs / scripts / design-system）保持**厂商中立**，Claude 专有部分（commands / hooks / plugin.json）收敛为**薄适配壳**，为将来 Codex / Gemini 适配预留。
4. 把编排大脑常驻 footprint 从当前 ~49KB 降到 ~3–5KB 量级（token / rot / 注意力三项优于现状）。

### 非目标
- ❌ 不在本副本执行 CLAUDE.md 瘦身（Phase 0，归原项目）。
- ❌ 不做 Codex / Gemini 适配层的实际实现（仅预留结构）。
- ❌ 不立即废弃 git-copy 下游通道（双模过渡）。
- ❌ 不改动任何 L1 业务产物逻辑（outputs / process_record 的生成行为不变）。

---

## 2. 现状与基准线

- 当前分发模型：git-copy 整仓到工作区 + `install_hooks.sh` + `syncUpstream`。
- **基准事实**：`CLAUDE.md` = 27,901 字符（≈15–25K tokens），现状**每会话常驻**。瘦身是净减负，非新增开销。
- 路径耦合：`pm-workflow/...` 路径在 156 个文件中出现 **1468 次**。
- 已有 SessionStart hook：`pm-workflow/scripts/hooks/session_start_state_summary.py` 注入 state 摘要——**插件注入大脑复用同款机制**。
- 脚本含 pytest 测试目录 `pm-workflow/scripts/tests/`。

---

## 3. 架构：核心 + 适配壳（双根）

### 3.1 两个物理隔离的根

| 根 | 内容 | 读写 | 解析来源 |
|----|------|------|----------|
| **PLUGIN_ROOT**（框架）| rules / templates / scripts / agents / skills / design-system / core | **只读** | `${CLAUDE_PLUGIN_ROOT}` |
| **PROJECT_DIR**（产物）| `outputs/` `process_record/` | 读写 | 用户项目 cwd / `${CLAUDE_PROJECT_DIR}` |

设计的全部复杂度都来自这条线：**框架文件进只读 cache，业务产物留用户项目**。

### 3.2 仓 / 插件目录布局（单仓）

```
pm-workflow-plugin/                          # 发布仓根（= marketplace）
├── .claude-plugin/
│   └── marketplace.json                     # 市场清单，relative source 指向 ↓
├── plugins/
│   └── pm-workflow-plugin/                  # ★ 插件本体（= 安装后的 PLUGIN_ROOT）
│       ├── .claude-plugin/
│       │   └── plugin.json                  # 清单
│       ├── commands/                        # ◇ Claude 适配壳：斜杠命令
│       │   ├── newRequirement.md  nextStage.md  projectStatus.md
│       │   ├── changeRequest.md   retro.md   syncUpstream.md
│       ├── hooks/
│       │   └── hooks.json                   # ◇ Claude 适配壳：SessionStart 注入
│       └── pm-workflow/                     # ★ 厂商中立核心（目录名不变）
│           ├── core/
│           │   └── orchestrator.md          # 新增：最小常驻锚（Phase 0 瘦身产物的 port）
│           ├── agents/                      # PM / Supervisor 角色规范
│           ├── rules/                       # tmpl_ / rule_ / proto_ 全套
│           ├── scripts/                     # precheck / assemble / gen_scaffold / hooks/ ...
│           ├── skills/                      # 分析类 skills（JTBD / OST / story ...）
│           └── design-system/               # 不觉设计系统资源
├── README.md                               # 安装 + 双模迁移指引
├── CHANGELOG.md                            # 由 CHANGELOG_L2.md 升级而来
└── docs/                                   # 本设计文档等
```

**关键设计点**：`pm-workflow/` 目录名**原样保留**。所有 `pm-workflow/...` 引用因此无需逐条改写——只要建立"`pm-workflow/` 相对 PLUGIN_ROOT 解析"的约定（见 §5）。`commands/` + `hooks/` + `plugin.json` 是**纯 Claude 适配壳**；将来加 Codex 只需在核心旁加 `AGENTS.md` + Codex skill 注册，复用同一 `pm-workflow/` 核心（见 §9）。

---

## 4. 清单文件

### 4.1 plugin.json

```json
{
  "name": "pm-workflow-plugin",
  "description": "结构化 AI 产品经理工作流：需求分析→功能规划→产品定义→交付文档，多层审核、可控变更。",
  "version": "1.0.0",
  "author": { "name": "<待填>" },
  "homepage": "<待填仓库 URL>",
  "repository": "<待填仓库 URL>",
  "license": "<待定>",
  "skills": "./pm-workflow/skills/",
  "agents": ["./pm-workflow/agents/AI产品经理_Agent.md",
             "./pm-workflow/agents/AI产品主管_Agent.md"],
  "commands": "./commands/",
  "hooks": "./hooks/hooks.json"
}
```

> 说明：`skills` / `agents` 用自定义路径指向核心 `pm-workflow/`，使核心目录结构不被打散。命名空间统一为 `pm-workflow-plugin:`（如 `/pm-workflow-plugin:newRequirement`）。

### 4.2 marketplace.json（仓根）

```json
{
  "name": "pm-workflow-market",
  "displayName": "PM Workflow Marketplace",
  "description": "AI 产品经理工作流插件市场",
  "version": "1.0.0",
  "author": { "name": "<待填>" },
  "plugins": [
    {
      "name": "pm-workflow-plugin",
      "displayName": "PM Workflow",
      "description": "结构化 AI 产品经理工作流",
      "source": { "source": "relative", "path": "./plugins/pm-workflow-plugin" }
    }
  ]
}
```

用户安装路径：
```bash
claude plugin marketplace add <github-user>/<repo>
# 然后
/plugin install pm-workflow-plugin@pm-workflow-market
```

---

## 5. 编排大脑：最小常驻锚（D2）

### 5.1 三分法（CLAUDE.md → 三个去处）

| 内容类型 | 去处 | 加载 |
|---|---|---|
| **必须常驻**（无命令触发 / 编排器永远要）：调整意见自动记录规则、L1-L2 二元判定 + 编排器读文件边界、文件命名速查、派发速查、changeRequest-vs-调整意见 3 步判定、**插件根声明** | `pm-workflow/core/orchestrator.md`（≈3–5KB）| **SessionStart hook 注入** |
| **可下沉**（有命令/派发触发）：四阶段详细执行循环、changeRequest 对照表全文、版本号 SemVer 全文、调整意见第零~四步 SOP 全文、会话管理建议、工作流维护守则 | 留 `commands/*.md` + `rules/*.md` | subagent 按需 Read（不变）|
| **外迁**（机构记忆，不该常驻）：26 行内联历史引用（议题# / 矛盾审计# / 实证…）| `nb_log.md` / `CHANGELOG.md` | 不注入，正文留必要指针 |

> orchestrator.md 是 **Phase 0 瘦身产物的直接 port**。Phase 0 在原项目把 CLAUDE.md 瘦成"最小常驻锚 + 下沉"后，本文件 ≈ 复制该锚 + 加一段插件根声明。

### 5.2 SessionStart hook 注入要点
1. **静态/动态分块**：orchestrator.md（静态）与 state 摘要（动态）**分两块注入，静态在前**，避免动态内容击穿 prompt cache。
2. **插件根声明**：注入内容含一句——"框架文件位于 `${CLAUDE_PLUGIN_ROOT}`；所有 `pm-workflow/...` 路径相对此根解析；用户产物 `outputs/`、`process_record/` 相对项目 cwd。"
3. **fail-safe**：hook 失败必须可见报错且不阻断会话；因 command/skill 会按需重读 rules，最坏退化为"降级不瘫痪"。

---

## 6. 路径解析策略（化解 1468 处引用）

三类引用，工作量分级：

| 类 | 例 | 处理 | 强度 |
|---|---|---|---|
| **A. Bash 脚本调用** | `python3 pm-workflow/scripts/precheck_stage1.py` | **硬改** `python3 "${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/..."` | 必须（否则 cwd 找不到）|
| **B. Python 脚本内部路径** | assemble 读模板 / 写 drafts | 框架文件用 `__file__` 自定位；项目产物用 cwd / `CLAUDE_PROJECT_DIR`；必要时加 `--framework-root` / `--project-root` | 必须，逐脚本审计 |
| **C. 散文 Read 引用** | "详 `pm-workflow/rules/x.md`" | 编排器派发时按 dispatch 协议**前缀 PLUGIN_ROOT** 传给 subagent；orchestrator.md 写明约定 | 约定即可，**无需逐条改写** |

### 6.1 Python 脚本双根审计清单（Phase 1 必做）
对每个脚本判定其读/写各属哪个根：

| 脚本 | 读框架（PLUGIN_ROOT）| 读写产物（PROJECT_DIR）|
|---|---|---|
| `precheck_stage1~4.py` | 对照模板 tmpl_*.md | 读 outputs/ |
| `assemble.py` | 读模板/规范 | 读 drafts/ 写 outputs/ |
| `gen_scaffold.py` | 读 schema/范式 | 读 scaffold.json 写 drafts/ |
| `check_*.py` / `structure_check.py` | 规则 | 扫 outputs/ process_record/ |
| `hooks/session_start_state_summary.py` | — | 读 state.md（PROJECT_DIR）|
| `strip_inline_change_markers.py` 等 | — | 扫产物 |

判定原则：**脚本可用 `__file__` 自定位框架文件**（模板就在脚本旁），产物一律以 cwd 为基（用户在自己项目里运行）。审计输出落入实施计划。

---

## 7. hooks.json

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          { "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/hooks/session_start_inject.py\"" }
        ]
      }
    ]
  }
}
```

- 新建 `session_start_inject.py`：输出 ① orchestrator.md 全文（静态块）② 现有 state 摘要（动态块，沿用 `session_start_state_summary.py` 逻辑）③ 插件根声明。
- **去掉** pre-commit 安装类 hook（插件模式 L2 不在用户仓，无需 git 拦截）。

---

## 8. 包含 / 排除清单

| 进插件 | 不进插件（项目运行态 / 内部）|
|---|---|
| `commands/` `hooks/` `plugin.json` | `process_record/`  `outputs/` |
| `pm-workflow/{agents,rules,scripts,skills,design-system,core}` | `nb_log.md`（外迁后留指针）`HANDOFF.md` |
| `README.md` `CHANGELOG.md` | `workflow_backlog/`  `PROTOTYPE_STRATEGY_DECISION.md` |
| | 根 `Python/_cache`  `.claude/settings.local.json`  `.gitignore` 调整 |

`CHANGELOG_L2.md` → 升级为发布仓 `CHANGELOG.md`（同时承接 §5 外迁的历史引用）。

---

## 9. 跨厂商预留（D1，仅结构不实现）

核心 `pm-workflow/` 全部为 Markdown + Python，**无厂商假设**。将来增厂商 = 在核心旁加薄适配层：

| 厂商 | 适配层（薄壳）| 复用核心 |
|---|---|---|
| Claude Code（本期）| `commands/` + `hooks/` + `plugin.json` | `pm-workflow/` |
| Codex / Cursor（将来）| `AGENTS.md`（指向核心 rules + skills）| 同一 `pm-workflow/` |
| Gemini（将来）| `GEMINI.md` + skill 注册 | 同一 `pm-workflow/` |

**已知硬约束（写入风险）**：工作流核心价值依赖"编排器派发 PM/Supervisor subagent 隔离执行"。该能力在 Claude Code 最成熟；别家 subagent 支持弱时，工作流退化为单上下文（违背抗 rot 初衷）。故跨厂商体验**随各家 subagent/skill/命令/hook 支持度降级**，非平价移植。

---

## 10. 双模并存 / 过渡（D3）

`sync_from_upstream.sh` / `install_hooks.sh` / `pre-commit` / `syncUpstream.md` **保留在核心**，README 标 **deprecated（过渡通道）**：

| 模式 | 更新方式 | L1/L2 git 拦截 |
|---|---|---|
| 插件模式（主推）| `/plugin update` | 无关（L2 不在用户仓）|
| git-copy 模式（老下游过渡）| `install_hooks.sh` + `syncUpstream` | 仍生效 |

README 提供「两模式对照 + 迁移指引」。

---

## 11. 测试与验证

1. **单元**：保留 `pm-workflow/scripts/tests/` pytest，双根改造后须全绿。
2. **本地集成**：
   - `claude plugin marketplace add ./`（relative）装本地插件。
   - 在 scratch 空项目运行 `/pm-workflow-plugin:newRequirement`。
   - 验证：subagent 从 cache（PLUGIN_ROOT）读框架；产物落在 scratch 项目 cwd（PROJECT_DIR）；precheck 脚本能定位模板。
3. **大脑注入**：确认 SessionStart 注入 orchestrator.md + state 摘要分块、缓存友好、hook 失败可见。
4. **回归**：跑一遍四阶段 + 一次 /changeRequest + 一次 /retro，确认行为与 git-copy 模式一致。

---

## 12. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| SessionStart hook 故障点（新增）| 大脑静默不注入 | fail-safe + 可见报错；command/skill 按需重读 rules 降级兜底 |
| split-brain 漂移（orchestrator.md vs rules）| 规则不一致 | 锚只放速查+指针，真源留 rules（SSOT 纪律）|
| 静态+动态拼接击穿 cache | token 成本上升 | 分块注入，静态在前 |
| Bash 调用漏改 PLUGIN_ROOT | 脚本在用户 cwd 报错 | 实施计划逐处枚举 + 集成测试覆盖 |
| Python 脚本根混淆（读框架/写产物搞反）| 产物写错位置或读不到模板 | §6.1 双根审计逐脚本验证 |
| Phase 0 未完成即打包 | orchestrator.md 无源可 port | Phase 0 为前置依赖；未完成时本期可临时从现 CLAUDE.md 手工抽锚 |

---

## 13. 前置依赖与假设

- **前置（Phase 0，原项目）**：CLAUDE.md 瘦身为"最小常驻锚 + 下沉 + 外迁"。本期 orchestrator.md 直接 port 该锚。若 Phase 0 尚未完成，本期可临时按 §5.1 三分法从现 CLAUDE.md 手工抽取锚内容。
- **假设**：用户运行环境有 `python3`；Claude Code 版本支持 `${CLAUDE_PLUGIN_ROOT}` 与 SessionStart hook additionalContext。

---

## 14. 实施阶段建议（交由 writing-plans 细化）

1. 建仓骨架：`.claude-plugin/marketplace.json` + `plugins/pm-workflow-plugin/.claude-plugin/plugin.json` + 目录搬迁。
2. orchestrator.md 落位（port 自 Phase 0 锚）。
3. hooks.json + `session_start_inject.py`。
4. 路径改写 A 类（Bash 调用枚举硬改）。
5. 路径审计 B 类（Python 双根，逐脚本）。
6. commands 适配（命名空间 + 路径）。
7. 包含/排除清理 + CHANGELOG 升级 + README（含双模迁移）。
8. 测试（单元 + 本地集成 + 回归）。

---

## 15. 待确认 / Open Questions

- plugin.json 的 `author` / `homepage` / `repository` / `license` 具体值。
- marketplace / plugin 命名是否就用 `pm-workflow-market` / `pm-workflow-plugin`。
- 发布仓的最终 GitHub 地址（决定 marketplace add 命令）。
