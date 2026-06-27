# 设计文档：pm-workflow 封装为 Claude Code 插件（Phase 1）

- 文档日期：2026-06-28（rev.3.4，纳入两轮评审 + 文档核查 + scratch 实测 + 上游合并 + 上游「暂不瘦身」决策）
- 状态：通道级未知(A/B/C/D)+ M2 双根均已 scratch 验毕；**残留 = subagent 对数百处 transitive 引用套根的模型可靠性**（由通用规则+fallback+spot-check 管控，§13.5）。计划：`docs/superpowers/plans/2026-06-28-pm-workflow-claude-plugin.md`
- **上游决策（2026-06-28）**：暂不瘦身 CLAUDE.md → orchestrator.md = CLAUDE.md 逐字复制、不动 CLAUDE.md、取消 Phase 0a 锚区；前向兼容未来瘦身（§1.3 / §5.1）。
- **上游合并复核**：核心数字稳（17 脚本 / 335+98 引用 / 7 命令）；新增重点 = SSOT #81/#82 `doc_query.py`（§6.2 + plan E2/E3）。
- 范围：**Phase 1 = plugin + marketplace 打包**。**Phase 0a「CLAUDE.md 锚区划界」为插件必需前置**（低成本）；**Phase 0b「瘦身」可选、机会主义、非阻塞**（见 §1/§5）。均在**原项目**执行；本副本只读参考。

---

## 0. 决策记录

| # | 决策 | 选择 |
|---|------|------|
| D1 | 目标覆盖面 | Claude Code 单厂商旗舰，核心层厂商中立，结构预留跨厂商 |
| D2 | 编排大脑加载（插件不加载 CLAUDE.md）| 插件模式经 SessionStart hook 注入（**跨 /clear 重触发**，托住锚）；当前模式 CLAUDE.md 已自动常驻，禁引入第二注入源 |
| D3 | 旧 sync 机制 | 双模并存（过渡期），git-copy 标 deprecated |
| D4 | 发布仓布局 | 单仓：marketplace + plugin 同仓 |
| D5 | 编排大脑前置（**已更新，上游 2026-06-28「暂不瘦身、不动 CLAUDE.md」**）| **无 CLAUDE.md 前置改动**。`orchestrator.md` = CLAUDE.md 逐字复制（`gen_orchestrator.py` 无锚整文件复制）。原 Phase 0a 锚区划界取消。Phase 1 无 CLAUDE.md 依赖，可直接开工 |

---

## 1. 目标与非目标

### 目标
1. 把 pm-workflow（L2）封装为可 `/plugin install` 的 Claude Code 插件；单仓兼作 marketplace。
2. 核心层（rules / templates / agent-specs / scripts / design-system）保持**厂商中立**，Claude 专有部分收敛为薄适配壳，为 Codex / Gemini 预留。
3. **编排大脑：上游明确「暂不瘦身、不动 CLAUDE.md」（2026-06-28 决策）**。故 `orchestrator.md` = 仓根 CLAUDE.md 的**逐字复制**（加生成头 + 插件根声明）；插件模式注入**整份 CLAUDE.md**，常驻量 = 当前 git-copy 基线（~28K），**平价、无回归、无需改 CLAUDE.md**。原 Phase 0a 锚区划界 / Phase 0b 瘦身**全部取消/推迟**。**前向兼容**：未来若上游决定瘦身，给 CLAUDE.md 加 `<!-- ANCHOR -->` 标记，`gen_orchestrator.py` 自动改为只取锚区，本设计无需返工。

### 非目标
- ❌ 不在本副本执行 Phase 0。 ❌ 不把瘦身当独立项目。 ❌ 不实现 Codex/Gemini 适配层（仅预留结构）。 ❌ 不立即废弃 git-copy 通道。 ❌ 不改 L1 业务产物逻辑。

---

## 2. 现状与基准线

- 当前分发：git-copy 整仓 + `install_hooks.sh` + `syncUpstream`。
- `CLAUDE.md` ≈ 28K token，由 harness 作 project instructions、**跨 /clear 自动重注入**——它已是那个「最小常驻锚」，只是不小。
- **路径耦合（P1-4 修正，按 tracked source 重算）**：原 rev.2「1468 处 / 156 文件」**虚高**——误把 `.claude/worktrees/` 副本树（87 文件）算进来了。真实 tracked 范围 ≈ **880 处引用 / ~86 文件 / 全仓 174 文件**。其中 `rules/` **335** 处（30 文件，单文件最高 **143** = `agent_dispatch_protocol.md`）+ `agents/` **98** 处 = **433 处裸交叉引用**（subagent 从只读 cache Read 进来的正文里遇到，见 §6 P0-2）。Class A 硬改目标 = commands+rules 内 **41** 行 bash 调用。
- 已有 SessionStart hook：`scripts/hooks/session_start_state_summary.py`。
- 测试目录：`scripts/tests/`（pytest）。

---

## 3. 架构：核心 + 适配壳（双根）

### 3.1 双根（物理隔离）

| 根 | 内容 | 读写 | 解析 |
|----|------|------|------|
| **PLUGIN_ROOT** | rules / templates / scripts / agents / skills / design-system / core | 只读 | `${CLAUDE_PLUGIN_ROOT}` |
| **PROJECT_DIR** | `outputs/` `process_record/` | 读写 | cwd / `${CLAUDE_PROJECT_DIR}` |

### 3.2 仓 / 插件布局（单仓）

```
pm-workflow-plugin/                          # 发布仓根（= marketplace）
├── .claude-plugin/marketplace.json
├── CLAUDE.md                                # ★ 仅留仓根：git-copy 模式用 + orchestrator.md 生成源；不进插件 payload（§8/B-6）
├── plugins/
│   └── pm/                                  # ★ 插件本体（短名，规避命名空间 UX 回退，见 §15）
│       ├── .claude-plugin/plugin.json
│       ├── commands/                        # ◇Claude 适配壳：斜杠命令（注入解析后的绝对根，见 §6）
│       ├── hooks/hooks.json                 # ◇Claude 适配壳：SessionStart 注入
│       └── pm-workflow/                     # ★ 厂商中立核心（目录名不变）
│           ├── core/orchestrator.md         # 由仓根 CLAUDE.md 锚区【生成】（非手维护，§5）
│           ├── agents/ rules/ scripts/ skills/ design-system/
├── README.md  docs/
```

`pm-workflow/` 目录名保留；`commands/`+`hooks/`+`plugin.json` 为纯 Claude 适配壳。
> **✅ 卖点已确认（待核-B 关闭）**：plugins-reference.md 明确 `"skills"` 自定义路径**叠加**默认 `skills/`；`commands`/`agents` 自定义路径**替换**默认。故 `"skills": "./pm-workflow/skills/"` 合法，「目录名原样保留」成立。

---

## 4. 清单文件

### 4.1 plugin.json（已删 `agents` 字段——B-3 修正）

```json
{
  "name": "pm",
  "description": "结构化 AI 产品经理工作流：需求分析→功能规划→产品定义→交付文档，多层审核、可控变更。",
  "version": "1.0.0",
  "author": { "name": "<待填>" },
  "homepage": "<待填>",
  "repository": "<待填>",
  "license": "<待定>",
  "skills": "./pm-workflow/skills/",
  "commands": "./commands/",
  "hooks": "./hooks/hooks.json"
}
```

> **B-3 修正**：原 `"agents": [...]` 删除。实测 `AI产品经理_Agent.md` / `AI产品主管_Agent.md` 无 line-1 YAML frontmatter（开头是 `# … Agent`），不符合插件 `agents` 字段期望的「带 frontmatter 的 subagent 类型定义」。且本工作流**从不注册 agent 类型**——它派通用 subagent 再 Read 角色规范路径。故角色文件作为普通文件随 `pm-workflow/agents/` 发布即可。

### 4.2 marketplace.json（仓根）

```json
{
  "name": "pm-workflow-market",
  "displayName": "PM Workflow Marketplace",
  "description": "AI 产品经理工作流插件市场",
  "version": "1.0.0",
  "author": { "name": "<待填>" },
  "plugins": [
    { "name": "pm", "displayName": "PM Workflow",
      "description": "结构化 AI 产品经理工作流",
      "source": { "source": "relative", "path": "./plugins/pm" } }
  ]
}
```

安装：`claude plugin marketplace add <repo>` → `/plugin install pm@pm-workflow-market`，命令形如 `/pm:newRequirement`。

---

## 5. 编排大脑：单一真源 + 双模一致（B-2 + B-4 根治）

### 5.1 真源与生成（消灭 split-brain，上游「不动 CLAUDE.md」版）

- **单一真源 = 仓根 `CLAUDE.md`**（**不加锚、不瘦身、不改**）。
- `orchestrator.md` **由 `gen_orchestrator.py` 从 CLAUDE.md 生成**：**无 `<!-- ANCHOR -->` 标记时整文件逐字复制**（当前路径）；有锚时只取锚区（未来瘦身时自动启用）。**不手维护**。
- git-copy 模式读 `CLAUDE.md`；插件模式 hook 注入生成的 `orchestrator.md`（当前 = 整份 CLAUDE.md）。
- **一致性测试**：`gen_orchestrator.py --check` 重生成与已提交 orchestrator.md diff 为空，漂移即 FAIL（防 CLAUDE.md 改了忘重生成）。
- **无 CLAUDE.md 前置**：Phase 1 不依赖任何 CLAUDE.md 改动，可直接开工。

### 5.2 常驻锚三分法（⏸ 已推迟——上游暂不瘦身；保留作未来瘦身参考）

> **当前不执行**：上游 2026-06-28 决定不瘦身、不动 CLAUDE.md，故 orchestrator.md = 整份 CLAUDE.md，无需分桶。下表为将来若瘦身时的分区指引，**本期仅存档**。

判定线唯一：**「无命令触发时，这条规则会不会自己 fire？」**

| 桶 | 内容 | 处理 |
|---|---|---|
| **⛔ 必须常驻**（无触发 / 一给反馈即 fire）| 编排器读文件边界、派发 prompt 自检 3 项、调整意见第零步（接收下游反馈先 AskUserQuestion）、L1/L2 二元判定速查、文件命名速查、**changeRequest vs 调整意见 判定对照表** | 留锚区（→ 生成进 orchestrator.md）|
| **⬇ 可下沉**（议题①复核大幅收窄）| **仅** SemVer 全文 → nextStage/changeRequest；会话管理建议（面向人类）→ README/projectStatus。**注意：四阶段循环、调整意见 SOP 不可下沉**——它们跨 /clear 仍需常驻，command 不重读 → 搬走即 /clear 后丢失 | 仅这两块移入命令文件/README；锚区留一句话指针 |
| **🗄 外迁**（机构记忆，零操作价值）| 44 处括注（议题#/SSOT#/审计#/NB-/日期/实证/commit/回滚）| → `nb_log.md`（**仅此处**，不进 CHANGELOG，见 §8/B-6）|

> **A-3 修正（关键）**：`changeRequest 对照表` **必须常驻**——它守的是「调用 /changeRequest **之前**」的误判方向（用户对话中描述变更、编排器须判定该走 CR 还是调整意见，**无命令触发**）。下沉到 changeRequest.md = 等你决定调用时才加载，误判已发生。原文把它划入「可下沉」错误。
>
> **A-1 修正**：外迁机构记忆是 **Tier 1 零回归先行项**——CLAUDE.md 自身通篇违反 SSOT #79（禁内联变更标记），是「定义 #79 的文件违反 #79」。手段：把 `strip_inline_change_markers.py` 扫描目标扩到 CLAUDE.md → 生成逐条清单 → 按 #79 既有分工人工定夺（机械删伤语义）。**此项归 Phase 0（原项目）。**

### 5.3 SessionStart 注入（仅插件模式）
1. 静态（orchestrator.md）/ 动态（state 摘要）**分块注入，静态在前**，护 prompt cache。
2. 注入插件根声明（仅达主会话——**注意：不达 subagent**，见 §6）。
3. hook fail-safe + 可见报错；不阻断会话。
4. **A-4 提醒**：当前（git-copy）模式 CLAUDE.md 已自动常驻，**禁**再用 hook 注入 orchestrator.md，否则两份常驻真源。hook 注入仅用于插件模式。
5. **/clear 存活（议题①洞察）**：SessionStart hook **跨 /clear 重触发**（评审确认主链路成立），故插件模式 orchestrator.md 在每次 /clear 后重注入——**与 CLAUDE.md 跨 /clear 自动重注入对等**。这使插件模式具备当前模式所缺的能力：理论上可把更多内容放进 hook 注入块而不怕 /clear 丢失（但本期保守，锚区只放「必须常驻」集）。**前提：待核-D 确认注入确实送达后续派发链路。**

---

## 6. 路径解析（P0-1 + P0-2，重大修正）

| 类 | 例 | 处理 | 强度 |
|---|---|---|---|
| **A1. command-body bash（4 行）** | commands/*.md 内 `python3 pm-workflow/scripts/...` | 改 `python3 "${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/..."`——**加载时替换，已验可行** | P1，机械改 |
| **A2. rules/agent-body bash（37 行：21+16）** | rules/agent-spec 内 bash 调用 | **不能用变量**（plain 文件不替换）→ 走 C 的派发绝对根机制（subagent 用任务消息里的根拼绝对路径执行）| P0，随 C |
| **B. Python 脚本根（P0-1）** | assemble/add_i18n 等 17 脚本 | 拆 `REPO_ROOT` → `FRAMEWORK_ROOT(__file__)` + `PROJECT_ROOT(CLAUDE_PROJECT_DIR/cwd)` | **P0 重写（非审计）** |
| **C. 散文交叉引用 + A2（P0-2）** | rules 335 + agents 98 + 37 bash | **派发任务消息携带绝对插件根**，subagent 据此解析所有 `pm-workflow/...`（已验：注入不下传、任务消息下传）| **P0，方案已锁定** |

### 6.1 P0-1（最严重，我 rev.2 写反了，已实测纠正）
- **实测真相**：`assemble.py:33` `REPO_ROOT = Path(__file__).resolve().parent.parent.parent`，产物（`OUTPUT_DIR`/`DRAFTS_DIR`/`SCAFFOLD`/backups）**与**框架（`FALLBACK_CSS_PATH`/`PRD_TEMPLATE_PATH`）**同挂这一个 `__file__` 根**。全仓 **17** 个脚本如此，**0** 个用 `CLAUDE_PROJECT_DIR`。`add_i18n.py:42` 同样 `REPO_ROOT=__file__/../../..` → rev.2「DICT_PATH 已正确指 PROJECT_DIR」**错误**（它指的是 `__file__` 根下的 process_record，插件模式即 cache）。
- **后果**：插件模式 `__file__` 在只读 cache → assemble 把 `outputs/`、`drafts/` 写进 cache → 失败或污染框架。
- **修正（P0 重写）**：17 脚本统一引入双根——框架文件用 `FRAMEWORK_ROOT = Path(__file__)...`；产物用 `PROJECT_ROOT = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())`。配**红线集成测试**：断言产物落 PROJECT_ROOT、绝不写 cache。

### 6.2 P0-2（433 处跨文件引用，「约定即可」覆盖不到）
- **错因**：subagent cwd=用户项目，插件模式 `pm-workflow/` 在只读 cache、不在项目里 → 裸相对路径 Read 失败。§5.3 根声明经 SessionStart 进**主会话**，**subagent 全新上下文收不到**（待核-D 确认断裂点）。编排器前缀注入只能管它自己写进 dispatch 的几条，**管不了 subagent 读进来的数百条**。
- **方案已定（D 文档核查后）= (b)**：因 SessionStart 注入不下传 subagent（§13.5 D），且 rules/ 普通文件不展开 `${CLAUDE_PLUGIN_ROOT}`（§13.5 A），故**唯一可行**是「**派发任务消息携带解析后的绝对插件根 + 声明所有 `pm-workflow/...` 相对此根**」——任务消息确认进 subagent。**(a) 正文统一改写对 rules/ 不可行，作废。**
  - **改造点**：dispatch 协议（`agent_dispatch_protocol.md`）+ 所有 command 的派发段，统一加「绝对根 + 解析约定」一句。
  - **doc_query 专项（SSOT #81/#82，2026-06-28 上游合并后新增重点）**：分节读取已成派发核心，`doc_query.py` 被调用 16 处，每条命令含**两处** `pm-workflow/...`（脚本路径 + 文件参数）。编排器**从 SECTION-MAP 复制命令进派发 prompt 时必须把两处都改写为绝对框架根**。加固：给 `doc_query.py` 加「文件参数相对 FRAMEWORK_ROOT 回退」（plan Task E3），使裸路径参数也能定位。`doc_query.py` 取 `file` 为位置参数、不自 root，故**不在 17 脚本双根迁移内**。
  - **可靠性加固（可选）**：把"插件根 + 路径约定"做成**预加载 skill**（subagent 启动会加载预加载 skill，§13.5 D 文档），作为任务消息之外的第二保险；高密度文件（`agent_dispatch_protocol.md` 143 处）可优先抽查。
- **集成测试**：跑通四阶段，断言被 follow 的 `pm-workflow/` 引用全部解析到 cache 真实文件。

**附（次要）**：只读 cache 下 `import precheck_common` 写 `.pyc` 被静默跳过（不致命）；审计确认无脚本依赖框架目录可写。

---

## 7. hooks.json
```json
{ "hooks": { "SessionStart": [ { "matcher": "*", "hooks": [
  { "type": "command",
    "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/hooks/session_start_inject.py\"" }
] } ] } }
```
- 新建 `session_start_inject.py`：输出 ① orchestrator.md（静态）② state 摘要（动态）③ 插件根声明（仅主会话）。
- **去掉** pre-commit 安装类 hook（插件模式 L2 不在用户仓）。

---

## 8. 包含/排除清单（B-6 修正）

| 进插件 payload（`plugins/pm/`）| 不进 payload |
|---|---|
| `commands/` `hooks/` `plugin.json` | **`CLAUDE.md`**（留仓根：git-copy 用 + 生成源；进 payload 会与 orchestrator.md 双重加载）|
| `pm-workflow/{agents,rules,scripts,skills,design-system,core/orchestrator.md}` | `process_record/` `outputs/` `nb_log.md` `HANDOFF.md` `workflow_backlog/` `PROTOTYPE_STRATEGY_DECISION.md` 根 `Python/_cache` `.claude/settings.local.json` |

- **CHANGELOG 单职（B-6）**：`CHANGELOG.md` **仅作面向下游的 release notes**；**机构记忆只进 `nb_log.md`**。原 rev.1「CHANGELOG 兼承接外迁记忆」会混淆下游受众 + 内部记忆两类，正是框架一直防的「下游被内部循环污染」，作废。

---

## 9. 跨厂商预留（D1，仅结构）

| 厂商 | 适配壳 | 复用核心 |
|---|---|---|
| Claude Code（本期）| commands/ + hooks/ + plugin.json | pm-workflow/ |
| Codex/Cursor（将来）| AGENTS.md | 同一 pm-workflow/ |
| Gemini（将来）| GEMINI.md + skill 注册 | 同一 pm-workflow/ |

**硬约束（坦白）**：核心价值依赖「编排器派发 PM/Supervisor subagent 隔离执行」；别家 subagent 弱 → 退化单上下文。跨厂商体验随各家支持度降级，非平价移植。

---

## 10. 双模并存 / 过渡（D3）

`sync_from_upstream.sh`/`install_hooks.sh`/`pre-commit`/`syncUpstream.md` 保留核心、标 deprecated。
| 模式 | 更新 | L1/L2 git 拦截 | 编排大脑源 |
|---|---|---|---|
| 插件（主推）| `/plugin update` | **不命中**：插件用户仓无 `pm-workflow/`，pre-commit 永不触发 = 空 hook | 生成的 orchestrator.md |
| git-copy（过渡）| install_hooks + syncUpstream | 生效 | CLAUDE.md |
> **次要修正**：原表「插件模式拦截仍生效」误导——插件用户仓里没有 L2 文件，pre-commit/install_hooks 是 no-op。README 给「两模式对照 + 迁移指引」。

---

## 11. L2 自我演化闭环（B-5 新增 · 战略）

**问题**：只读插件切断框架核心闭环——`/retro → SSOT #N → L2 硬化 + 下游 NB 上报`（SSOT #31 上报 SOP、upstream_feedback、sync_from_upstream 均假设 L2 本地可编辑）。插件把 L2 变只读 → 插件模式用户失去参与 L2 演化的路径。**rev.1 用 D3 git-copy 当逃生口，但从未正面承认此取舍。**

**方案（P1-6 收口，明确定性）**：**插件用户 = 纯消费者（只读，不演化）**。
1. 用户本地跑 `/retro` 仍可运行（只读 `pm-workflow/` + 读写自己 L1）→ 产出**改进提议**。
2. 演化**只在源仓发生**：提议作为 **GitHub issue / PR 回源仓**（替代 upstream_feedback 文件落盘 + sync_* 镜像）。
3. maintainer 在源仓硬化 L2 + 同步 `ssot_anchors.md` 5 要素 + pytest 全绿。
4. `/plugin update` 下发给所有插件用户。
5. **contributor 模式**：需本地改 L2 者 `git clone` 源仓直接编辑（= git-copy 通道复用）。

**取舍正面承认**：插件把「人人本地可改 L2 + workflow-evolution 直改 + 下游 NB 上报」降级为「本地提议 → 源仓统一硬化 → /plugin update 下发」，换取分发一致性与防漂移。`workflow-evolution` skill / `sync_from_upstream.sh` / SSOT #31 上报 SOP 仅在源仓（contributor 模式）有效，对纯消费用户悬空——文档不再用 git-copy 当隐性逃生口，而是显式声明此降级。

---

## 12. 测试与验证
1. **单元**：`scripts/tests/` pytest 双根改造后全绿。
2. **大脑一致性**：`gen_orchestrator.py` 重生成与发布副本 diff 为空（B-4）。
3. **路径集成（P0-2 核心）**：本地装插件跑通四阶段，断言被 follow 的 `pm-workflow/` 引用全部解析到 cache 真实文件。
4. **双根红线（P0-1 核心）**：断言所有产物（`outputs/`/`process_record/`）落 **PROJECT_ROOT**、**绝不写入只读 cache**；框架文件从 PLUGIN_ROOT 读；precheck 能定位模板。
5. **回归**：四阶段 + /changeRequest + /retro 行为与 git-copy 一致。

---

## 13. 风险与缓解（修订）

| 风险 | 缓解 |
|---|---|
| **P0-1：17 脚本产物写进只读 cache** | 双根重写 `FRAMEWORK_ROOT`+`PROJECT_ROOT` + 红线集成测试（§6.1）|
| **P0-2：433 处裸引用在 subagent 解析失败** | 正文统一改写 或 根声明进每 subagent prompt + 改 dispatch（§6.2，待核-A/D 定方案）|
| **待核 A/B/C/D 纸面定不了** | 实施前强制 scratch 插件 spike（§13.5）|
| split-brain（两份大脑真源）| orchestrator.md 由 CLAUDE.md 锚区生成（单源）+ 一致性 diff 测试 |
| SessionStart hook 故障点 | fail-safe + 可见报错；command/skill 按需重读兜底 |
| 静态+动态拼接击穿 cache | 分块注入，静态在前 |
| **L2 演化闭环切断** | §11 纯消费者定性 + 提议→源仓 PR→/plugin update + contributor git-copy |
| **transitive 套根模型可靠性（残留①，spike 未覆盖）** | 通用规则（非枚举）+ doc_query fallback（E3）+ 集成 spot-check（plan G1 Step4）；失败则退预加载 skill 加固。**承认非零** |
| 编排大脑前置 | 已取消（上游不动 CLAUDE.md，orchestrator.md 整文件复制）|
| 命名空间 UX 回退 | 短插件名 `pm` → `/pm:newRequirement` |

---

## 13.5 待核与验证（文档核查 + scratch 实测 2026-06-28）

> 通道级未知 A/B/C/D + M2 双根**已验毕**；**transitive 套根可靠性为承认的残留**（见末尾「诚实边界」），非"全部关闭"。

| 待核 | 结论 | 依据 |
|---|---|---|
| **A** | ✅ 已验：`${CLAUDE_PLUGIN_ROOT}` 在 **command 正文 / skill / agent 组件内容**里**加载时替换**为绝对路径；**但不是运行时环境变量**（`printenv` 为空）；`rules/*.md` 等**普通文件 Read 进来不替换** | 文档 plugins-reference.md + scratch 实测：`TEST1A_INLINE=[<绝对插件根>]`、`TEST1B_ENV=[]` |
| **B** | ✅ 自定义路径合法：`skills` 叠加默认、`commands`/`agents` 替换默认 | plugins-reference.md |
| **C** | ✅ relative 路径相对 marketplace 根（含 `.claude-plugin/` 的目录）| plugin-marketplaces.md |
| **D** | ✅ 已验：SessionStart 注入 **不到达 subagent** | sub-agents.md 加载清单无 additionalContext + scratch 实测 `TEST2_SUBAGENT_REPLY=SENTINEL=NONE` |

**实测命令**：`claude --plugin-dir <pmtest> -p "/pmtest:probe" --permission-mode bypassPermissions`（探针见 scratchpad/pmtest）。

**对设计的决定性影响（已锁定）**：
- **路径解析归一为一个机制**：subagent 读/执行**任何来自 plain 文件（rules/ + agent-spec）的 `pm-workflow/...`** 都按「**派发任务消息携带的绝对插件根**」解析（任务消息确认进 subagent；SessionStart 不到 subagent，故注入法对 subagent 无效）。
- `${CLAUDE_PLUGIN_ROOT}` 变量**只在 command 正文 / skill / agent 组件内容**可用（加载时替换，非 env）：覆盖 **4** 行 command-body bash；**不覆盖** rules/agent 正文里的 **37** 行 bash（21 rules + 16 agents）与 335+98 路径引用——这些全部走上面的「派发绝对根」机制。
- **B/C → §3.2 布局与卖点成立**，无需改布局。
- **可选加固**：把"插件根 + 路径约定"做成**预加载 skill**（subagent 启动会加载预加载 skill），作为派发消息之外第二保险。

**M2 双根（脚本写只读 cache）—— 已 scratch 实测（2026-06-28）**：复刻 assemble.py:33-40 写法，模拟插件模式（FRAMEWORK≠PROJECT）证明：①现状写法产物落框架根（bug 复现）②双根修复后产物落 PROJECT_ROOT、绝不在框架下、模板仍在框架根 ③git-copy（项目==框架）零回归。5 项断言全 PASS。证据：`docs/spike/m2spike/`。

**诚实边界（治"无未知"过度表述）**：spike 关闭的是 **A/B/C/D 通道级未知 + M2 双根机制**。**残留 ≠ 0** —— 一项**模型可靠性**风险未被 spike 覆盖：subagent 读 plain 文件时，能否对其中**数百处 transitive `pm-workflow/` 裸引用**可靠套上派发的绝对根。Read 工具取字面路径、无机械 fallback，故这条只能靠：① 派发约定写成**通用规则**（"凡 `pm-workflow/...` 一律相对根解析"，非逐条枚举）② 脚本/参数类走 fallback（doc_query FRAMEWORK_ROOT 回退，plan E3）③ 集成测试 **spot-check** 高密度文件（如 `agent_dispatch_protocol.md` 143 处）抽样验证可达。**这是承认的残留风险，非"零未知"。**

---

## 14. 实施阶段（交 writing-plans 细化）
0. **前置门**：~~Phase 0a 锚区划界~~ 已取消（上游不动 CLAUDE.md）；§13.5 scratch spike A/B/C/D 已验毕。**无前置阻塞，可直接开工。**
1. 建仓骨架：marketplace.json + plugins/pm/plugin.json + 目录搬迁（CLAUDE.md 留仓根）。
2. `gen_orchestrator.py`：从 CLAUDE.md 锚区生成 orchestrator.md + 一致性测试。
3. hooks.json + `session_start_inject.py`。
4. **P0-1**：17 脚本双根重写 + 红线测试。
5. **P0-2**：按 spike 结论改 433 处引用（正文改写 或 dispatch+prompt 注入）。
6. 路径 A 类（41 行 bash 调用，按 spike-A 结论）。
7. commands 适配（短命名空间 + 路径）。
8. 包含/排除清理；CHANGELOG（单职 release notes）；nb_log 承接外迁记忆；README 双模迁移。
9. 测试（单元 + 一致性 + 路径集成 + 双根红线 + 回归）。

---

## 15. 待确认 / Open Questions
- **B-6 短插件名**：用 `pm` 还是 `pmflow` / 其他（决定 `/pm:` 前缀长度）。
- plugin.json 的 `author` / `homepage` / `repository` / `license` + 发布仓最终 GitHub 地址（可实施时填）。
- §11 演化路径已按 P1-6 定为「纯消费者 + 源仓 PR + contributor git-copy」，待你点头确认。
- ~~§13.5 待核 A/B/C/D~~ —— ✅ 已全部验毕关闭（rev.3.2）。

---

## 16. 评审修订记录

### rev.3.1 → rev.3.2（scratch 插件实测，spike 关闭）
| 待核 | 实测结论 | 文档处理 |
|---|---|---|
| A | ✅ 验毕：command 正文里 `${CLAUDE_PLUGIN_ROOT}` **加载时替换为绝对路径**（`TEST1A=[<根>]`）、**非运行时 env**（`TEST1B=[]`）；rules plain 文件不替换 | §13.5 关闭 + §6 拆 A1(4 行可用变量)/A2(37 行走派发根)|
| B/C | ✅ 文档关闭（同 rev.3.1）| §3.2 |
| D | ✅ 验毕：`TEST2=SENTINEL=NONE` → SessionStart **不到达 subagent** | §6 C 方案锁定「派发任务消息携带绝对根」|
| 净效果 | **spike 门关闭**，路径方案无未知，可进 writing-plans | §13.5 |

### rev.3 → rev.3.1（官方文档核查 4 待核）
| 待核 | 结论 | 文档处理 |
|---|---|---|
| A | 部分确定（后 rev.3.2 实测）| §13.5 |
| B | ✅ 自定义路径合法（skills 叠加）| §3.2 |
| C | ✅ 相对 marketplace 根 | §3.2 |
| D | 强证据"不到达"（后 rev.3.2 实测证实）| §6 |

### rev.2 → rev.3（第二轮评审：议题①复核 + P0/P1/待核）
| 项 | 评审点 | 处理 |
|---|---|---|
| **P0-1** | §6.1 脚本根写反——17 脚本产物挂 `__file__` 根、0 用 CLAUDE_PROJECT_DIR（实测确认；rev.2 add_i18n 判断错）| §6.1 改 P0 双根重写 + 红线测试；§13/§14 |
| **P0-2** | §6 Class C「约定即可」覆盖不到 subagent 读进的 433 处 | §6.2 二选一方案（待 spike）+ 集成测试 |
| **P0-3** | plugin.json `agents` 无 frontmatter；skills/agents 自定义路径待核 | §4.1 已删 agents；§3.2 加待核-B 警示 |
| **P1-4** | 数字虚高：1468/156 含 worktree 副本 | §2 改 tracked 真值 880/~86/174 |
| **P1-5** | Phase 0 归属歧义 + fallback 双源 | §0 D5 澄清 + 删手工抽锚（§5.1）|
| **P1-6** | 只读插件 vs L2 演化冲突未正面处理 | §11 改「纯消费者」定性 + 降级正面承认 |
| **议题① /clear** | CLAUDE.md 跨 /clear 重注入、command 不重读 → 可下沉集仅 SemVer+会话管理，降幅 −15~25% | §1 goal3 + §5.2 收窄 + §5.3.5 /clear 存活；瘦身不单独立项，Phase 拆 0a/0b |
| **待核 A/B/C/D** | 纸面定不了 | 新增 §13.5 强制 spike 门 |
| 次要 | §10 拦截误导 / __pycache__ / §12 产物落点断言 | §10 修正 + §6.2 附 + §12.4 红线 |

### rev.1 → rev.2（首轮评审 Part A/B）
| 项 | 处理 |
|---|---|
| B-1 433 处 | 必做改造（后 rev.3 升级为 P0-2）|
| B-2 split-brain | orchestrator.md 生成式 + 严格前置 |
| B-3 agents 字段 | 删除 |
| B-4 双源漂移 | 一致性 diff 测试 |
| B-5 演化闭环 | §11（后 rev.3 用 P1-6 收口）|
| B-6 归属/CHANGELOG/命名 | §8 + 短名 |
| A-1~A-4 | 瘦身分桶（后 rev.3 按 /clear 洞察收窄）|
