---
name: workflow-evolution
workflow_stage: meta
workflow_order: meta
output_target: "工作流框架自身的元规范 / 校验脚本 / 测试基础设施 / SSOT 双锚等(L2 工作流维护层)"
description: Lightweight workflow for L2 workflow framework evolution tasks. Use for meta-level work (rule revisions, script edits, SSOT updates, token additions) that the orchestrator handles directly without dispatching PM/Supervisor agents.
intent: >-
  Provide a disciplined skill the orchestrator follows when doing L2 workflow maintenance directly — preserving methodology rigor (atomic steps, mechanical self-check, SSOT sync) while saving 65-80% tokens vs dispatching PM Agent.
ssot_role: "true_source"
ssot_derived: "template.md（Step 3 / Step 7 / Step 8 进度文件 + SSOT 同步清单 + 完成报告三个核心模板）"
ssot_adjustment_direction: "先改 SKILL.md（流程定义）、再同步 template.md（执行模板）；禁止反向"
ssot_anchor_id: "ssot_anchors.md #33"
type: workflow
theme: meta-workflow
best_for:
  - "Single-rule revision in CLAUDE.md / agent_methodology.md / etc"
  - "Token additions to design system (--fb-*)"
  - "Single-line SSOT 双锚 entry add"
  - "Self-audit checklist updates (single section)"
  - "Script bug fixes (≤30 lines)"
scenarios:
  - "我要给 CLAUDE.md 工作流维护守则加一条 [Must] 规则"
  - "增加一个颜色 token --fb-warning-bg-light"
  - "把某个 SSOT 双锚从 B 组升到 A 组"
  - "修复 precheck_stage4.py 某个 check_* 函数的边界 bug"
estimated_time: "10-30 min"
---


## Purpose

Provide a lightweight, disciplined skill for the **orchestrator (Claude Code)** to handle L2 workflow maintenance tasks directly — without dispatching PM Agent + Supervisor Agent through the standard 2-round closure.

This is **not** a replacement for L1 product-document production (PRD/spec generation) — those still require PM/Supervisor agents. This skill applies only to L2 meta-work where the orchestrator has full context and dispatching agents adds cost without value.

## Key Concepts

### L1 vs L2 双层架构

| 层 | 工作性质 | 消费者 | 典型任务 | 处理方式 |
|---|---------|--------|---------|---------|
| **L1 产品业务层** | 产品文档生产 | 真实业务方（产品总监 / 设计 / 开发）| PRD / spec / 阶段产物 | 派 PM Agent + Supervisor Agent |
| **L2 工作流维护层** | 工作流框架自身演化 | 工作流维护者（项目维护者 + AI）| 元规范 / 校验脚本 / SSOT 双锚 / 测试 | **本 skill：编排器直做**（默认）/ 派 agent（复杂大型）|

### 路径判定（L1 vs L2 二元）

**核心判定标准**：任务**修改的文件归属哪一层**——L1 派 Agent / L2 走本 skill。**不再以文件数 / token / 是否新建脚本作为路径判定依据**（这些维度仅用于"分批执行"提示，见下方）。

| 文件归属 | 路径 |
|---------|------|
| **L2 文件**（修改任意以下路径）| **走本 skill 路径**（编排器直做）|
| - `pm-workflow/agents/*` | |
| - `pm-workflow/rules/*`（含 `bujue-design-system/`） | |
| - `pm-workflow/scripts/*`（含 `tests/`） | |
| - `pm-workflow/skills/*` | |
| - `CLAUDE.md` / `agent_methodology.md` / `agent_parameters.md` | |
| - `.claude/commands/*` | |
| **L1 文件** | **派 PM Agent**（保留 L1 业务流程严格性）|
| - `outputs/`（PRD / spec / 阶段产物） | |
| - `process_record/state.md` / `process_record/tasks/`（产品过程记录） | |
| **混合任务** | L2 部分走 skill / L1 部分派 Agent（拆分执行）|

**为什么 L1/L2 二元判定优于多维阈值**：
- 客观：文件路径判定无主观空间，避免"50K vs 80K 算不算超阈值"的争论
- 编排器主对话天然持有 L2 上下文，PM Agent 重 Read 同样规范是浪费
- 责任清晰：L2 工作流维护是编排器的固有职责（PM/Supervisor 仅参与 L1 业务），不应通过派 Agent 转移；L2 质量保障由本 skill §L2 三道质量门负责

### 大型 L2 任务的分批执行模式

L2 任务规模**大**（参考阈值：> 200K token / 涉及 > 5 文件 / 改既有脚本结构 ≥ 30%）时，仍走本 skill 路径，但编排器**分批执行**：

1. **拆分 atomic step 为多组**（如 5 文件改动 → 拆为 file-1/2 / file-3/4 / file-5 + 测试 三批）
2. **每批结束写进度文件 checkpoint**（含已完成步 + 待续步）
3. **批与批之间编排器自我评估上下文压力**（≥ 800K token / 1M 主对话 → 提示用户考虑 `/clear` 重启 + state.md 恢复）
4. **不一次性把所有文件 Read 进主对话**——按批次精读

**参考量化**：本会话所有历史 L2 任务（含 issue #1 用户旅程跨 6 文件 ~600K token / issue #6 建 4 个 precheck 脚本 ~450K token）均能在 Opus [1m] 单会话承载,但应主动用分批模式减轻 cache 失效（5 分钟 TTL）成本。

### SSOT 重大升级批次窗口模式（F.1 `[Recommended]`，SSOT #59）

**触发条件**（满足任一即进入批次窗口模式）：

1. 同一 SSOT 锚号下计划 **≥ 2 个**连续 L2 commit（如 SSOT #44 骨架屏 4 轮升级 #30→#31→#32→#33）
2. L2 改动涉及 `ssot_anchors.md / proto_*.md / scaffold schema / tmpl_*.md` 任一文件
3. 配套 L1 重 assemble 成本高（如 prd_template.html / proto_spec_md.md 涉及拼装链路）

**批次窗口纪律**：

1. **批次基线锁定**：相关 commit 在上游连续完成后，**先锁定批次基线 commit hash**（如 WE-A~WE-Z 一并落盘后获 `batch_hash`）
2. **批次窗口同步 L1**：避免 L2 单 commit 频繁触发 L1 落盘 — 同 SSOT 锚号 commit 序列**一并**落 L1（**节省 N-1 次 L1 重 assemble**）
3. **基线 commit 注明**：批次内 commit message 末尾注明 `批次 N/M`（如 `1/4` `2/4` `3/4` `4/4` 完整序列），便于下游 PM 识别批次边界

**反 pattern**（实证 SSOT #44 骨架屏 4 轮单 commit 升级）：

| ❌ 反 pattern | ✅ 批次窗口模式 |
|---|---|
| SSOT #44 骨架屏 #30→#31→#32→#33 4 轮单 commit → L1 重 assemble v1.3→v1.4→v1.5→v1.6 4 次 | #30~#33 批次窗口收尾后**一次性** L1 重 assemble v1.6（节省 3 次 L1 落盘 + 评审成本）|

**与「大型 L2 任务的分批执行模式」的边界**：

| 维度 | 大型 L2 任务分批 | SSOT 重大升级批次窗口 |
|---|---|---|
| **聚焦** | **单任务内**拆分多组 atomic step | **跨任务**同 SSOT 锚号 commit 序列 |
| **触发** | 任务规模 > 200K token / > 5 文件 | 同 SSOT 锚号 ≥ 2 commit |
| **目标** | 减轻 cache 失效成本 | **节省 L1 重 assemble 成本** |

**特例豁免**：
- SSOT 升级**仅含 1 个 commit**（无后续连续升级计划）→ 无需进入批次窗口模式，常规 commit + sync 即可
- SSOT 升级**仅改 L2** + 不触发 L1 重 assemble（如新增 ssot 锚记账无配套规则修改）→ 无需批次模式

**本会话实证**：G/A/B/C/D 5 方案均走 2-4 commit 切分 + **一次性 4 仓 sync**（C2/C3/C4 阶段统一同步 L1），是 F.1 批次窗口思想的自然实践 — F.1 把该实践规则化、显式化，供未来 SSOT 升级遵循。

### 与 L1 产品业务流程的关系

- **本 skill 不参与 L1 产品阶段流程**（不在 stage1/2/3/4 派发链路中）
- **触发**：产品总监在对话中提工作流改进建议 / `/retro` 复盘后规范优化 / 编排器自身识别工作流缺陷 / PM 或 Supervisor 在 L1 任务中走 NB 上报 SOP（`agent_dispatch_protocol.md` 第 6 条）后被编排器接收
- **完成后产物**：直接进 git，不经过 L1 stage 流程

### L2 三道质量门（取代"派 Supervisor 二审"）

`[Must]` L2 路径**没有 Supervisor**（L1/L2 边界明确：Supervisor 仅参与 L1 业务）。L2 修订的质量保障由以下**三道独立的门**串联组成，缺一不可：

| 质量门 | 时机 | 检测维度 | 落地形式 |
|-------|------|---------|---------|
| **门 1：机械检查** | Step 6 | 形式问题（语法、grep 一致性、字面对称、行数对称、frontmatter / class 登记齐全） | `pytest` / `structure_check.py` / `grep` / 跑改后脚本 |
| **门 2：编排器自审** | Step 7.5 | 语义合理性（规则间逻辑冲突 / SSOT 抽象层级 / 内部矛盾 / 论据强度 / 边界场景） | 编排器以"审核者视角"重审一遍 + 写审查记录到进度文件 |
| **门 3：人类审 diff** | Step 8 收尾 | 价值判断与方向是否符合产品总监意图（机械与 AI 都判断不了的事） | 编排器在完成报告中**强制 `git diff` 展示**，等待用户决策 |

**为什么需要三道门**：
- 机械检查擅长抓"形式问题",抓不到"规则间语义冲突"（如本次 SKILL.md Step 1 阈值残留与 §路径判定矛盾——pytest 无法检测）
- 编排器自审能补语义层,但有 anchoring bias（自己改自己作业）——必须有第三道门
- 人类审 diff 是最终质量门,价值判断不可委派

**禁止使用混淆性论据**（取自历史教训）：
- ❌ "机械检查捕错率高于 Supervisor" — Supervisor 在 L2 不存在,这种比较没有基准
- ❌ "本会话 N 次实战质量未降" — 样本量不足以支撑"长期可信"的断言
- ✅ 正确表述："L2 质量保障 = 三道门串联,各有独立维度,不互相替代"

## Application

### Step 1：任务理解 + 路径确认（T1）

`[Must]` 编排器收到 L2 任务后，先在对话中输出任务理解：

1. **本质**：这是 L2 任务还是 L1 任务？混合任务的拆分边界？
2. **范围**：影响哪些 L2 文件？预估改动行数？是否涉及代码逻辑 / schema 变更 / 多文件结构调整？
3. **路径确认**：按 §路径判定 — L2 任务**一律走本 skill 路径**（编排器直做，不派 PM/Supervisor）。文件数 / token 估算 / 是否新建脚本**仅用于决定是否启用「分批执行模式」**（参 §大型 L2 任务的分批执行模式），不作为切换派 Agent 的依据
4. **混合任务**：L2 部分走本 skill，L1 部分（如同时改了 `outputs/` 或 `process_record/state.md`）拆出来派 PM Agent — 但此时须警惕 git pre-commit hook 会拒绝 L1+L2 混合 commit，须分两次 commit
5. **`[Recommended]` 复读产品总监原话**：若任务源是产品总监**自然语句反馈**（非 file:line 具体改动指令），实施前在进度文件**顶部贴当次原话原文** + 显式答「我的理解是 X / 可能误读点是 Y」。**Why**：自然语句易被理解偏差（如"页面架构章节统一说明"= per-archetype 直觉被一度误读成 per-page → 数轮长链返工才回正）；形式化"原话 ↔ 理解"对照让产品总监审第一遍 diff 时一眼能纠（/retro 2026-05-21 主根因③防御）。**触发判定**：用户原话含"应当 / 似乎 / 最好 / 改成 / 需要"等抽象意图、且未明确 file:line ⇒ 触发；用户明示"prd_template.html L530 改 8 → 4" ⇒ 无须复读（已无歧义）。

### Step 2：必读路径 Read（T2）

`[Must]` 编排器自己 Read 必读文件——但**比派 Agent 路径精简**（编排器已在主对话中持有部分上下文，避免重复 Read）：

- **必读**（每次 L2 任务都 Read）：
  - 待修订的具体文件（不超过 5 个）
  - 直接相关的真源 / 派生（按 SSOT 双锚清单查）
- **可省**（编排器主对话已含）：
  - `agent_methodology.md` / `agent_parameters.md` 等通用方法论（除非任务直接修订这些文件）
  - `AI产品经理_Agent.md` / `AI产品主管_Agent.md`（这是 L1 角色规范，L2 任务不读）
  - `rule_hard_constraints.md` 全文（按需 grep 相关 S4-XX）

`[Must]` **规范完整性自检前置 Read**（/retro 2026-05-13 落地，根因 A 防御）：L2 改动涉及 `.frame-*` / `.phone-frame` / sidebar 渲染 / `.proto-section` / `.proj-component-showcase` 等**模板核心 CSS 类**，或 `gen_scaffold.build_proto_nav` / `assemble.py inject_*` 等**模板渲染算法**时，必读以下规范文档相关章节：
- `pm-workflow/rules/prd_expression_standard.md`（§零 元规范、§四 状态帧三区块、§七.7.1 项目组件展示区、§十一 组件变更清单等对应章节）
- `pm-workflow/rules/proto_contract.md`（§零.1 全局 z-index、§十二 通用组件视觉规范、§十五 视觉自检清单）
- 涉及帧规范的端类文件（如 `proto_platform_app.md` / `proto_platform_h5.md`）

> **强约束理由**：本批 /retro 复盘 3/4 问题(# 1 单页模块剪枝 / # 2 showcase 无 padding / # 3 phone-frame 无 flex column)都是 **L2 规范声明 vs 算法/CSS 实现脱节** — 规范文档已说明设计意图,但模板代码没遵守。Step 6 机械自检必须能识别这类脱节。

### Step 3：进度文件创建（T3）

`[Must]` 在 `process_record/progress/` 创建或追加进度文件：

- **新建场景**：`workflow_evolution_YYYY-MM-DD_HHMM.md`（按时间戳）
- **追加既有 issue 修订场景**：在 `issue_*_plan.md` 末尾追加新段
- 进度文件结构遵循本 skill 的 `template.md` 模板

### Step 4：Atomic Step 切分（T4）

`[Must]` 把任务拆为 atomic steps（**每步独立可验证**），每步前缀用任务系列码（如 `WE-1` / `WE-2` ...）：

- 步骤粒度：每步 ≤ 5 分钟可完成
- 每步完成立即在进度文件标 `[x]`，**禁止批量勾选**
- 步骤总数：典型 3-7 步

### Step 5：实施 + 即时勾选（T5）

`[Must]` 按 atomic step 顺序实施：

- 用 Edit / Write / Bash 工具修订
- 每步完成 → 立即 grep 验证或 Read 确认 → TaskUpdate 标 `[x]` + 进度文件标 `[x]`
- 遇不确定 → **产出 NB（非阻塞性问题）继续推进，不暂停等待**
- NB 写入进度文件 NB 段（编号 `NB-WE-NN`）

`[Recommended]` **L2 修复优先用"兼容既有 L1 写法"的 CSS 技巧**(/retro 2026-05-13 最佳实践):L2 改 CSS / 渲染规则修复 L1 已积累的 inline 越界写法时，优先采用以下 CSS 技巧让既有 drafts **无需改 HTML** 即可受益:
- `:where()` 选择器(特异性 0，不与 inline 打架):`:where(.phone-frame, .desktop-frame, .h5-frame, .tablet-frame, .miniprogram-frame) { display: flex; flex-direction: column; }`
- 属性选择器命中既有 inline:`[style*="position:sticky"][style*="bottom:0"] { margin-top: auto; }` 自动覆盖 17+ 处 PM 写的 inline sticky panel
- `margin-top: auto` 在 flex column 容器自动撑开剩余空间,替代显式 `position:absolute; bottom:0`
- 反例:避免要求 PM 批量改 N 处 drafts 这种重 L1 改造方案(token 成本高 + 易遗漏)

> **示范案例(L2 commit `dc8f582`)**:5 frame 类启用 flex column + 子选择器 `margin-top: auto` 一次性修复 17 处 PM 写的 inline sticky panel,CSS-only 无需改 HTML,极简 + 完美兼容既有 drafts。

### Step 6：机械自检（T6）

`[Must]` 完成后执行机械检查（**至少一项**适用即必跑）：

| 改动类型 | 必跑机械检查 |
|---------|------------|
| 改 precheck_stage*.py | `cd pm-workflow/scripts && pytest`（PT 系列覆盖部分）+ 实际跑改后脚本 |
| **新增 / 大改 `check_*` 函数**（NB-LIT-25-B B.2 v1 失败教训）| `[Must]` 走 `workflow_maintenance_protocol.md §新增 precheck 规则上线前 dry-run 纪律`：① 在 ≥ 2 个真实下游产物 dry-run，命中数据附 commit message；② 人工核查 ≥ 1 个命中样本（命中 ≤ 5 全核查，> 5 抽 3 个）；③ false positive 率 ≥ 30% 禁止上线；④ 启发式特征空间穷举评估，无法穷举改真源匹配 |
| 改 prd_template.html / tokens.md | `grep` 验证 token / class 在双锚两侧字面一致 |
| 改 SSOT 双锚清单 | `grep "^| #"` 数清单行数 + 标题数字一致 |
| 改 skill 三件套 | `python pm-workflow/scripts/structure_check.py` |
| 改 CLAUDE.md / agent_methodology.md | `grep "[Must]"` / `grep "[Should]"` 标签数量 |
| **改模板核心 CSS 类 / 渲染算法**（/retro 2026-05-13 新增,根因 A 防御）| **规范完整性对照**:grep `prd_expression_standard.md` / `proto_contract.md` 相关章节的每条 `[Must]` / `[Should]` 设计声明,逐条验证模板代码(CSS / algorithm)落地;发现"规范声明了但实现没遵守"的漏洞,优先在本次 commit 内补齐（避免下个 PM/L2 改动时再次踩同坑) |

### Step 7：SSOT 同步检查（T6 延伸）

`[Must]` 对照 `pm-workflow/rules/ssot_anchors.md`核查本次改动是否触发 SSOT 关系新建 / 调整：

- **新建双锚关系** → 在清单加新行（A 组要求 5 要素齐全）
- **改既有双锚** → 同步真源 + 派生 + 调整方向 + 双向引用
- **机械兜底缺失** → 评估是否当期补；不补则挂 B 组架构债
- **`[Must]` 新建 L2 文件** → 同步 `pm-workflow/rules/workflow_architecture_map.md §三` 文件分组功能表 + §五 改动影响速查表（详 `template.md` Template 2 第 10 项）。**Why**：架构地图是 L2 改动前必查指针；新文件不入索引 = 后续维护者查不到 = SSOT 派生层漂移源头（2026-05-14 实战先例：`proto_data_display_selection.md` 新建后漏同步架构地图）

### Step 7.4：规则增量落盘 SOP（SSOT #60，治"编号撞号 + 基数失修"系统性盲区）

`[Must]` 本次改动涉及**新增编号**（SSOT #NN / S{stage}-XX / D-XX / G-XX / check_* 函数 / 规则对照表行 / 维度表行 / 维度集合数变化）时，按下方 4 项 grep 自检逐项打钩；任一 FAIL 回 Step 5 修复后重跑：

**1. `[Must]` 编号空间冲突自检**（防"S3-06 一物二用"等撞号）

```bash
# 模板：新增 SSOT #NN
grep -rn "SSOT #NN\b" pm-workflow/ CLAUDE.md .claude/

# 模板：新增 S{N}-XX 规则
grep -rn "\bS{N}-XX\b" pm-workflow/ CLAUDE.md .claude/

# 模板：新增 D-XX scaffold 维度
grep -rn "\bD-XX\b" pm-workflow/ CLAUDE.md .claude/
```

- 命中既有同号 → 改名递增至下一未占用编号
- **编号空间分系列**：编号家族独立计数（如「现网模块承继 S1-07/S2-06/S3-06」与「G.5 UI 字面 S1-08/S2-07/S3-07」是两个不同家族，撞号判定按家族 + 编号双键，不按"全仓不撞"）

**2. `[Must]` 文档基数同步自检**（防"24 项 / 36 对"类失修）

- 新增 `check_*` 函数 → `grep -rn "\bN 项\b\|\bN 个\b" pm-workflow/agents/ CLAUDE.md` 同步所有文档侧基数描述（基数 = 脚本动态计数 `grep -c "^def check_" <脚本>`）
- 新增 SSOT 表行 → `grep -rn "\bN 对\b\|A 组 N\b" pm-workflow/` 同步顶部声明 + 架构地图引用
- 新增 D-XX 维度 → 维度表行数 vs SOP 数字字面对齐（如 §4.5 "9 个维度" + "D-01~D-09"）
- 新增 S4-XX 硬规则 → `rule_hard_constraints §六.X` 对照表 + PM/Sup 自审清单同步加行

**3. `[Should]` 对照表 / 维度表同步**

- 涉及 S4-XX → 同步 `rule_hard_constraints §六.X S4 规则与检查点对照表` 加行（PM 自审 §5.4 / Supervisor §4.4 / precheck 函数三列）
- 涉及 D-XX → 同步 `AI产品主管_Agent.md §4.5` 维度表 + SOP "D-01~D-XX 共 N 个维度" 数字
- 涉及 SSOT 双锚 → 走 `ssot_anchors.md` 5 要素 + A/B/C 组归类（详 `template.md` Template 2 第 1-3 项）

**4. `[Should]` 动态计数语义替代硬编码**

- 若同一数字基数在 ≥ 3 个文档侧重复（如 "59 对 SSOT" 在 ssot_anchors + architecture_map + CLAUDE.md 三处）→ 改为"动态计数（grep 命令）"语义 + 引用唯一权威源
- **标准措辞模板**："详见 X 文件头部（动态计数，截至 YYYY-MM-DD 为 N 对；脚本：`<grep / awk 命令>`）"
- **触发阈值**：≥ 3 处冗余 → [Should] 改动态语义；2 处冗余 → 保留硬编码 + 加交叉引用脚注；1 处 → 不动

**Why（治本路径）**：L2 矛盾审计实证 — 编号撞号 + 基数失修 + 对照表脱节 + 数字基数多文档冗余四类系统性盲区在批次落盘场景高发（同一锚号 ≥ 2 commit 时风险倍增）。**机制核心**：把"新对象入库对照清单"（`workflow_maintenance_protocol §新对象入库`）从"加文件齐全度"扩展到"加编号空间不撞 + 加基数同步 + 加对照表 + 加动态计数语义"四维度——前者是结构性入库，后者是数量性入库，二者协同形成 L2 演化的完整入库纪律。

**自检产出**：
- ✅ 全部通过 → 进入 Step 7.5 编排器自审
- ⚠ 个别项可挂 NB（如动态计数语义改造工作量大）→ 在进度文件 NB 段挂账，进入 Step 7.5
- ❌ 编号撞号 / 基数失修硬错误 → 回 Step 5 修复，重跑 Step 6 + Step 7 + Step 7.4

### Step 7.5：编排器自审（门 2）

`[Must]` SSOT 同步检查后、完成报告前，编排器以"审核者视角"重审本次改动 — 这是机械检查抓不到的语义层质量门：

**自审清单（逐项打钩，写入进度文件「编排器自审记录」段）**：

1. **规则间语义冲突**：本次新增 / 修订的规则与既有规则有无矛盾？特别核查同一文件不同段落是否描述同一逻辑但表述不一致（如本次修订前的 Step 1 阈值判定 vs §路径判定）
2. **SSOT 抽象层级**：本次新增的概念 / 字段 / 段落是否处在合适的抽象层级？是否应该上升到 CLAUDE.md / agent_methodology.md 等更高层文件？是否应该下沉到具体文件？
3. **论据强度**：本次写入的"为什么"段落是否依赖样本量小的实证 / 单视角推论 / 与既有边界（如 L1/L2）混淆的比较？
4. **边界场景**：本次改动在异常路径（如混合任务、超大规模、git hook 拦截）下是否仍自洽？
5. **与既有规范双向引用**：本次改动是否被关联文件以双向引用方式登记？（参 SSOT 5 要素第 4 项）

**自审产出**：
- ✅ 全部通过 → 进入 Step 8
- ⚠ 发现问题但可挂 NB → 在进度文件 NB 段挂账（NB-WE-NN），简短说明，进入 Step 8
- ❌ 发现问题且必须立即修 → 回到 Step 5 修复，重新走 Step 6 → Step 7 → Step 7.5

**禁止行为**：
- ❌ 跳过 Step 7.5 直接进 Step 8（"我都改完了应该没问题"是 anchoring bias）
- ❌ 把"机械检查通过"作为跳过自审的理由——机械检查与自审是不同维度

### Step 8：完成报告 + 强制 git diff 展示（门 3，T6 收尾）

`[Must]` 在对话中输出结构化完成报告（用 `template.md` 完成报告模板）：

- 改动摘要表（按文件分组）
- 机械验证证据（grep / pytest 输出 / 实际跑测）
- 编排器自审记录（从进度文件复制 Step 7.5 清单 + 结论）
- NB-WE 清单（如有）
- **`[Should]` 视觉验证清单**：L2 改动涉及 **PRD / spec 视觉呈现**（模板 CSS 几何 / 模板 DOM 结构 / DSL 多元素布局 / nav 信息架构 / 帧渲染等）时，完成报告必须显式列出 「建议产品总监 / 下游打开浏览器验证 X / Y / Z」 清单——具体到"打开哪个 outputs/prd_*.html / 看哪个 section / 关注什么视觉点"。**Why**：机械三门（py_compile / pytest / css_sync / purity）只校结构同步与字面对称，**抓不到视觉问题**（间距 / 几何尺寸 / 多元素布局 / 渲染时序），下游产品总监打开 PRD 才能看出。显式 surface 视觉验证项 = 让产品总监审 diff 时知道"该开浏览器看什么"，避免"机械绿灯但视觉爆炸"（/retro 2026-05-21 主根因① + S4 视觉 issue 半数都是用户使用时才发现）。**触发判定**：改 `prd_template.html` `<style>` / `gen_scaffold.build_*_nav` / `assemble.inject_*` / `.sk-*`/`.frame-*` 类 / `proto_platform_*.md` 帧规范 ⇒ 触发；纯 docstring / 注释 / 测试代码 ⇒ 不触发。
- **`[Should]` CHANGELOG_L2 下游升级日志追加**：本次 L2 改动**影响下游产物 / 行为**（precheck 新增 check / assemble 改动 / gen_scaffold schema / prd_template / 规范硬约束 / scaffold 字段）时，在仓根 `CHANGELOG_L2.md` **顶部追加一条**，含：日期 + commit_short + 类型 + 一句话 + 下游影响 + **「sync 后须知」actionable 整改步骤**（跑什么命令 / 预期结果 / 出 WARN 怎么改）。**Why**：下游 PM sync 上游 L2 后需快速知道"这次升级要我做什么"，逐条读 commit / ssot_anchors 成本高；CHANGELOG_L2 是 commit 的**下游向消费者视图**（curated 整改指引），由 `sync_from_upstream.sh` 同步进下游仓 + 完成时提示下游查看。**触发判定**：改 `precheck_stage*.py` 新增 check / `assemble.py` / `gen_scaffold.py` schema / `prd_template.html` / `rule_hard_constraints.md` 硬约束 / scaffold schema ⇒ 追加；纯 docstring / 注释 / 内部记账 / 文档措辞 ⇒ 可省（标 [FYI] 或不记）。**强度对齐**：每条「sync 后须知」标 [Must]（不做破坏产物）/ [Should]（WARN 阶段渐进整改）/ [FYI]（无须动作）。
- **`git diff` 实际输出**（强制门 3，禁止省略）：编排器在完成报告中执行 `git diff --stat` + `git diff` 并把输出贴入对话，让产品总监审完整改动后再决策 commit
- 等用户决策（commit / push / 继续）

**禁止行为**：
- ❌ 完成报告中只口头描述改动而不展示 diff（产品总监无法审"我看不见的代码"）
- ❌ 在用户给出明确 commit 指令前自行 commit / push
- ❌ **触发视觉验证清单条件但完成报告不列**（机械检查抓不到视觉，省略 = 把产品总监置于"事后才发现"的位置；/retro 2026-05-21 主根因①防御）

## Anti-Patterns（什么时候 **不** 用本 skill）

- ❌ **L1 产品文档生产**（修改 `outputs/` PRD / spec / 阶段产物）→ 用 PM Agent + Supervisor Agent 双轮闭环
- ❌ **L1 产品过程记录修订**（如 `process_record/state.md` 含产品工作流状态变更）→ 派 PM Agent
- ❌ **PM Agent 自审清单升级 / L1 角色规范修订涉及业务方法论核心改动** → 派 PM Agent 自己改（让 PM 用方法论修方法论,自指闭环）
- ❌ **自由发挥不维护进度文件 / 跳过机械自检 / 不写 NB**（即使 skill 路径，纪律不能破）

**注意**：L2 任务**不论规模**都走本 skill,大型任务用分批执行模式（参 §路径判定）。**不再以"文件数/token/新建脚本"作为派 Agent 理由**。

## Why This Skill Works

- **匹配编排器天然能力**：L2 工作需要的是「对框架的整体理解」+「文件修订 + 多门质量保障」——编排器都具备，且主对话天然持有 L2 上下文
- **token 节约 65-80%**：免去派 Agent 路径中 PM + Supervisor 重复 Read 必读路径的成本（实测本会话历次 L2 任务节约 65-80%）
- **保留方法论纪律**：T1-T6 的不变式仍在（任务理解 / 必读 / 切分 / 即时勾选 / 自检 / 收尾），只是执行者从 PM 变编排器
- **三道质量门串联**：L2 路径没有 Supervisor 角色（L1/L2 边界），改由「机械检查 + 编排器自审 + 人类审 diff」三道独立维度的门保证质量（参 §L2 三道质量门）。三道门各管不同维度，不互相替代

## When to Escalate（升级路径）

L2 任务**不切换派 PM/Supervisor**（L1/L2 边界明确）。以下情况升级到产品总监裁决：

- **机械自检（门 1）失败 3 次仍不通过** → 暂停 + 提交产品总监裁决（拆分问题 / 列多套候选方案）
- **编排器自审（门 2）发现的语义冲突无法在 skill 内解决**（如涉及 L1/L2 边界本身的重新定义）→ 暂停 + 提交产品总监
- **实施中发现规模真的过大**（如改 200K+ token、需新建多个测试套件）→ 暂停 + 拆分为多个独立 skill 任务，每个任务独立走完 8 步
- **涉及边界条件**（如同族对称性问题——参 agent_methodology.md §七）→ 暂停思考清单，再决定 skill 内修复或提交产品总监

---

参见：
- `template.md` — 进度文件 / SSOT 同步清单 / 完成报告 三个核心模板
- `examples/sample.md` — 本会话历史成功 L2 案例汇总（5 个 case）
- `pm-workflow/rules/agent_methodology.md` — T1-T6 方法论原文（编排器版本是其实例化）
- `pm-workflow/rules/ssot_anchors.md` 双锚清单 — 每次 L2 修订须对照同步
