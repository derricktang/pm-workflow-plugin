# 会话交接 — 2026-04-26

> ⚠️ **2026-05-15 前提作废声明**：本文件「问题 5：原型生成路线—— fb-fallback CSS vs React + TDesign」及相关 React / TDesign 迁移讨论**前提已作废**。最终结论：PRD 原生 HTML 无法引入框架组件库（React/TDesign/Ant Design 需构建工具，与 PRD 自包含静态 HTML 不兼容）；pub 库定为**原生 CSS（fb-fallback 体系）单库内建兜底**，正式库接入为后续 skill/CLI（详 `workflow_architecture_map.md §六`）。下方 TDesign / PoC 历史内容**保留备查，不作为现行方向**。详 memory `component_library_architecture` / `pub_library_distribution_decision` + `workflow_architecture_map.md §六`。

> ⚠️ **2026-05-31 过期项数作废声明（L2 矛盾审计 #9 修复）**：本文件提及的 `precheck_stage4.py` 项数（如 "扩展 8 项 proj 检查 / precheck_stage4 14 项全过"，L144/L151/L282）**与现状严重不符** — 截至 2026-05-31 该脚本含 **49 个 check_ 函数**（脚本动态计数 `grep -c "^def check_"`），由 S4-30~S4-39 累计新增。本文件作为会话历史档案保留备查不持续维护（参 `pm-workflow/nb_log.md:5` 定位），新维护者请以脚本实际计数为准，**勿信此文中任何 precheck 数字**。

> **重启后恢复指令**：
> 「请先 Read `HANDOFF.md` 同步上次会话进展，再 Read `process_record/state.md` 同步反馈页测试用例的工作流状态，然后告诉我下一步。」

---

## ⚠️ 待评估的开放问题

> 用户主动提出，**先记录、待重要事项处理完再回头评估**。

### 问题 1：工作流是否设计为"整产品迭代管理"还是仅"单功能模块"？

**用户原话：** "我的设计初衷是把一个产品放在这个 AI 工作流中管理迭代，不只是某个功能模块，需要评估一下现有工作流是否满足。"

**衍生场景：**
- 产品演进多个版本（v1.0 → v2.0 → v3.0），跨多个迭代周期
- 不同迭代可能新增/修改/弃用模块（M01 v1.0 中存在，v2.0 删除，v2.5 新加 M05）
- 旧 PRD 由人工控制是否升级到新 fallback / 新组件库
- 多人协作：不同 PM 可能同时开发不同模块

**当前工作流的潜在缺口（待评估时核查）：**
- ❌ scaffold.json 是单次性的，不支持版本演进（v1 与 v2 怎么区分？）
- ❌ state.md 仅记录单产品当前版本状态，不记录历史迭代
- ❌ /changeRequest 是否能处理"模块新增/弃用"层级的变更（不仅字段级）
- ❌ outputs/ 路径仅 `*_latest`，不区分版本（产品定义_v1 vs v2）
- ❌ 阶段 4 自审 / 主管审核没有"对比上一版本"维度
- ❌ proj 组件 `inherits: pub.X.v1` vs `pub.X.v2` 的版本钉绑机制
- ❌ HANDOFF.md / 整产品演进路线图 是否需要长期维护

**评估时可参考的设计方向：**
- 引入 product_version 概念：state.md 顶层加 `当前版本 v2.0`
- outputs/ 加版本子目录或文件后缀（`prd_反馈页_v2_latest.html`）
- /productRelease 命令：把 latest 标记为 v[N].0 + 创建归档
- 版本间 diff 视图：阶段 4 主管审核增加"vs 上版"对比
- 产品演进路线图：`pm-workflow/_product_evolution/[产品名].md` 长期文件

**评估优先级：** 🟡 重要但不阻塞当前工作；待批次 2-5 + 跨模块/能力审核机制等关键工作落地后回头评估。

### 问题 2：proj 反馈池机制（升级 proj→pub 的反馈通道）

虽然已通过 S4-22 组件变更清单部分实现（PM 在每次 PRD 中标记"建议升级 proj→pub"），**但仍缺**：
- 跨产品 / 跨项目的 proj 升级建议汇总（同一 proj 在多产品出现就该升级）
- 谁定期 review 这些建议？
- 升级 fallback 批次的触发条件 / 流程

**评估时机：** 当跑过 ≥ 3 个真实项目后，看实际累积的"建议升级"条目数量与跨项目重复模式，再决定是否设独立 review 流程。

### 问题 3：反馈页历史 PRD 触点漏渲染（2026-04-28 由 N4 检查发现）

precheck_stage4 N4 触点 ID 集合一致性核查发现反馈页 PRD 真实瑕疵：

```
spec.md 触点：M01-P01-T01 / T02 / T03 / T04 / T05  （5 个）
prd.html 触点：M01-P01-T01                          （1 个）
缺失：T02 / T03 / T04 / T05 的 interaction-card
```

**当前状态：** precheck 报 1 项 FAIL，但反馈页是历史项目，本期不修复也不阻塞主线。

**待评估时机：** 决定下次跑反馈页相关变更（/changeRequest）或新需求时一并补齐 — 修复路径：重派 M01 PRD Agent 补齐 T02-T05 的 interaction-card → 重跑 assemble.py prd（用 N3 重入逻辑）→ precheck 通过。

**意义：** N4 机械检查在加入第一天就发现了上线已久的真实瑕疵——证明这层机械化的价值。

### 问题 4：components_反馈页_latest.md 旧规范（2026-04-27 新增）

components_反馈页_latest.md 是旧规范（v1.0）格式，无 §二.1 索引段（A/B/C/D 4 张表）。precheck 降级为 WARN 兼容，但建议升级到 v1.1。

**修复路径：** 在文件顶部按 `proj_component_protocol.md §二.1` 添加 4 张表（本期无 proj 组件，4 张表均填"本期无新建 proj 组件"即可）。约 5 分钟工作量。

### 问题 5：原型生成路线—— fb-fallback CSS vs React + TDesign（2026-04-27 新增）

**核心问题：** 用户提出"不要重复造轮子"，希望改用 React + 真实组件库（TDesign / Ant Design）+ mock data 的形态产出 PRD 原型。当前 fb-fallback CSS 路线虽已全量适配但只是"伪装成 utility CSS 让静态 HTML 可渲染"的中间层，开发对接时仍需翻译。

**已做：** PoC 已实证（vite + react-ts + tdesign-react 跑通），技术风险已清零；用户已浏览验证。**PoC 目录已于 2026-04-28 清理**（占用 334MB），如需重做按 `PROTOTYPE_STRATEGY_DECISION.md` 步骤可快速重建。

**待决：**
- 是否走 React + TDesign 路线？（5-6 周改造 vs 1 周省事）
- 多端如何处理？（每端独立项目 / Taro 一套代码 / Web+H5 同项目 + 小程序截图占位 / Web 响应式模拟）

**完整决策记录：** [`PROTOTYPE_STRATEGY_DECISION.md`](./PROTOTYPE_STRATEGY_DECISION.md) — 含全部 4 方案对比、多端 4 子方案对比、Phase 0-3 时间消耗（25.5-32 人天 + 缓冲 ≈ 5-6 周）、推荐目录架构、决策建议矩阵、恢复时的步骤指引。

**评估优先级：** 🔴 重大架构决策——改造成本大但长期收益更大；优先级取决于未来 3-6 个月内预期跑多少个产品（≥ 3 个则强烈推荐迁移）。

---

## 会话主线

本次会话不是跑产品需求，而是**对 PM 工作流自身做检查 + 修复 + 增强**。主线脉络：

1. 跑了一次"账号密码登录"测试（旧测试，已清理）
2. 发现 skill 工具引用问题 → 修复（改为 Read SKILL.md 机制）
3. 建立 skills 版本管理（.sources.json + sync_skills.py）
4. 全面检查工作流逻辑 → 发现 14 个问题（4 红 / 6 黄 / 4 绿）
5. 修复全部 4 红 + 6 黄
6. 跑"反馈页"测试验证修复（已跑到阶段 4 PM 自审通过，未派发主管审核）
7. 设计并落地 proj 组件协议（含 3 条新硬规则 S4-17/18/19）
8. 开始设计兜底组件库 → **断在批次 1 实施前**

---

## 已完成（全部持久化在文件系统）

### 1. skill 应用机制修复

- 全工作流的"调用 skill 工具"措辞改为"Read `pm-workflow/skills/<框架名>/SKILL.md` + `template.md`，按 schema 产出"
- 改动文件：`agent_methodology.md` / `agent_parameters.md` / `AI产品经理_Agent.md` / `AI产品主管_Agent.md` / `rule_hard_constraints.md`
- 设计原则：项目自包含，不依赖 Claude Code 平台 Skill 工具

### 2. skills 版本管理

- `pm-workflow/skills/.sources.json`（顶层数组，支持多源扩展）
- `pm-workflow/scripts/sync_skills.py`（list / status / update / diff 子命令）
- 上游：https://github.com/deanpeters/Product-Manager-Skills，钉版 commit `4aa4196c14873b84f5af7316e7f66328cb6dee4c`
- selected 7 个：proto-persona / jobs-to-be-done / problem-statement / opportunity-solution-tree / epic-breakdown-advisor / user-story / user-story-mapping

### 3. 工作流 10 个问题修复

**🔴 4 个阻断性：**
1. `changeRequest.md` 删除 `frontend-design:frontend-design` skill 调用
2. `tasks/index.md` → `scaffold.json`（task_card_template.md + AI产品经理_Agent.md）
3. 触点编号统一为 `M[XX]-P[XX]-T[NN]` / `H-M[XX]-P[XX]-状态`（涉及 7 处文件）
4. PM 自审 §十四 视觉自检 → §十五（实际章节位置）

**🟡 6 个重要不一致：**
5. nextStage.md 阶段 4 → 步骤 C 入口语义澄清 + 中断恢复说明
6. CLAUDE.md Step 1/2/3/5/7 路径清单**显式列入**方法论 + 参数声明
7. PM 自审清单加"未自行修改 state.md NB 表"防双写（4 处自审）
8. G-07 引用从不存在的"已确认调整决策章节"改为现有 NB/P 清单的 ✅ 状态条目
9. 重做 3 次升级处理策略落地（newRequirement.md + nextStage.md 加候选方案 A/B/C 模板）
10. issues 文件创建格式硬性规定（含 `状态：未分析` 字段）

🟢 4 个优化建议**未做**：见下方"待办"

### 4. proj 组件协议（完整机制）

- `pm-workflow/rules/proj_component_protocol.md`（391 行完整协议）
- 三条新硬规则：S4-17 状态枚举完整性 / S4-18 可视化完整性 / S4-19 CSS 抽象纪律
- CLAUDE.md 阶段 4 增加 **Step 2.5 项目组件识别**（含路径清单、触发判定、跳过条件）
- Step 3/5 路径清单加入 `outputs/components_[产品名]_latest.md` + `proj_component_protocol.md`
- nextStage.md 阶段 4 路由链含 Step 2.5
- `precheck_stage4.py` 扩展 8 项 proj 检查（schema / 状态枚举 / 展示区 / 行数 / 禁 inline style / CSS 类定义 / 状态 modifier / NEW 标记）
- `prd_expression_standard.md` §7.1「项目组件状态展示区」规范

### 5. 反馈页测试用例（验证 1-9 项修复）

- 阶段 1-3 全部主管审核通过
- 阶段 4 Step 1-7 全部完成；PM 自审通过；spec.md + prd.html 已生成
- precheck_stage4 14 项全过
- **未做：** 阶段 4 主管审核（断在派发前；用户主动选择 B "测试已足够"结束）
- 状态文件：`process_record/state.md`（阶段 4 ⏳ 进行中，实际是等待派发主管审核）
- 产物：`outputs/反馈页_*` 各阶段成果齐全

### 6. Memory（已存）

- `~/.claude/projects/-home-tangjun-Documents-claude-code-pm-workflow/memory/`
- workflow_performance_baseline.md（性能基线）
- stage4_agent_load_bottleneck.md（阶段 4 单 agent 负荷瓶颈）
- skill_design_principle.md（skill 应用机制设计原则）

---

## 进行中 / 待办

### 批次 1：兜底组件库（已确定方案，待开工）

**关键决策（用户已确认）：**
- ✅ 参考来源：**TDesign**（不是 Ant Design）—— 因为它官方覆盖 Web / Mobile / Miniprogram 三端，API 一致
- ✅ 命名前缀：`fb-`（与 bujue 设计规范一致）
- ✅ 视觉风格：基于 bujue tokens（黑白灰主调），借鉴 TDesign API 形态
- ✅ 接入 PRD 方式：方案 C —— `assemble.py prd` 自动把 fallback CSS 注入到 PRD `<style>` 顶部
- ✅ 文件位置：`pm-workflow/rules/bujue-design-system/fb-fallback.css`
- ✅ 分批做，先做批次 1

**批次 1 待交付物：**

| 产物 | 路径 | 预估大小 |
|------|------|---------|
| 兜底 CSS | `pm-workflow/rules/bujue-design-system/fb-fallback.css` | ~350 行 |
| 调用清单 | `pm-workflow/rules/bujue-design-system/fb-fallback-manifest.md` | ~200 行 |
| assemble.py 注入逻辑 | `pm-workflow/scripts/assemble.py` | +20 行 Python |
| prd_expression_standard 引用 | 加一节"兜底 CSS 自动注入说明" | +30 行 |
| 待补组件 spec 部分填充 | `bujue-design-system/components/_pending.md` 中 Modal/Toast/Switch/Checkbox/Radio/Select/Search 移到独立文件 | 按需 |

**批次 1 覆盖范围（~26 个 class 系列）：**

| 类别 | 组件 | 数量 |
|------|------|------|
| 原子 | Button / Input / Textarea / Icon / Label / Hint / Link | 7 |
| 表单 | FormRow / Select（基础下拉）/ Checkbox / Radio / Switch / Search | 6 |
| 容器 | Card / Modal / Toast / Tag / Chip / Badge | 6 |
| 列表 | ListItem / Pagination | 2 |
| 状态帧 L4 | empty / loading / error / success / disabled-page | 5 |

**端口适配方式：**
- 单一 CSS 文件 + 双层组织
- 通用层：所有端共用，class 写在 frame 容器内会自动按所在 frame 适配尺寸
  - `.fb-btn` 基础 + `.phone-frame .fb-btn` / `.desktop-frame .fb-btn` / `.tablet-frame .fb-btn` / `.miniprogram-frame .fb-btn` 端口 modifier
- 端口专属层：仅在特定 frame 内生效（批次 2-4 增补）

**预估工作量：** 批次 1 总 ~2 小时

### 后续批次（未启动）

- 批次 2: 移动端专属（ActionSheet / Tabbar / Picker / PullRefresh）—— ~150 行
- 批次 3: 桌面端专属（Tooltip / Popover / Dropdown）—— ~120 行
- 批次 4: 小程序独有差异 —— ~80 行
- 批次 5: 触控/无障碍/键盘细节 —— ~50 行

### 更早遗留的待办（优先级低）

🟢 4 个优化建议未做：
- #11 agent_parameters.md §三 草稿状态自标改为定稿
- #12 /retro 复盘结论回写 state.md
- #13 CLAUDE.md 路径 A 第 2-4 步在 nextStage.md 步骤 F 显式实现
- #14 precheck_stage4.py 增加状态枚举完整性校验（部分已通过 S4-17 实现，可关闭）

### 未触发未验证的 3 个修复

- 🔴 #1 changeRequest 删除 frontend-design 引用（已修，未实测——需要走一次 /changeRequest 验证）
- 🟡 #9 重做 3 次升级处理（已加模板，未实测——需要构造 3 次审核不通过场景）
- 🟡 #10 issues 文件状态字段（已加规定，未实测——需要走一次 /retro）

---

## 当前文件系统状态（关键路径）

```
项目根/
├── HANDOFF.md                          ← 本文件
├── CLAUDE.md                           ← 已修复（含 Step 2.5、显式方法论必列、issues 格式等）
├── outputs/
│   ├── 需求分析_反馈页_latest.md         ← 反馈页测试 v1.0
│   ├── 功能规划_反馈页_latest.md         ← 反馈页测试 v1.0
│   ├── 产品定义_反馈页_latest.md         ← 反馈页测试 v1.0
│   ├── spec_反馈页_latest.md            ← 反馈页测试 v1.0（自审通过）
│   └── prd_反馈页_latest.html           ← 反馈页测试 v1.0（自审通过）
├── process_record/
│   ├── state.md                        ← 反馈页阶段 4 ⏳ 进行中
│   ├── tasks/scaffold.json             ← 反馈页 M01 单模块 4 状态帧
│   ├── tasks/task_M01_反馈页.md         ← 任务卡
│   ├── drafts/spec_M01_draft.md        ← 已拼装
│   ├── drafts/prd_M01_draft.html       ← 已拼装
│   ├── progress/stage*_反馈页_*.md      ← 全部已完成
│   ├── reviews/stage1_review.md ~ stage3_review.md  ← 主管审核通过
│   └── versions/                       ← 各阶段 v1.0 归档快照
├── pm-workflow/
│   ├── agents/
│   │   ├── AI产品经理_Agent.md          ← 已修复（skill 机制 + 自审防双写 + §十五 引用）
│   │   └── AI产品主管_Agent.md          ← 已修复（分析框架应用判定标准）
│   ├── rules/
│   │   ├── agent_methodology.md         ← 已修复（T3 探索框架措辞）
│   │   ├── agent_parameters.md          ← 已修复（T3 + atomic step 验收点）
│   │   ├── rule_hard_constraints.md     ← S4-01~S4-19（新增 S4-17/18/19）
│   │   ├── proj_component_protocol.md   ← 新建（391 行完整协议）
│   │   ├── proto_contract.md            ← 已修复（触点示例）
│   │   ├── prd_expression_standard.md   ← 已修复（触点示例 + §7.1 项目组件状态展示区）
│   │   ├── proto_spec_md.md             ← 已修复（触点示例）
│   │   ├── prd_template.html            ← 已修复（侧栏导航示例）
│   │   ├── proto_prd_html.md            ← 已修复（§十四→§十五 映射）
│   │   ├── task_card_template.md        ← 已修复（index.md → scaffold.json）
│   │   ├── tmpl_*.md                    ← 未动
│   │   ├── proto_platform_*.md          ← 未动
│   │   ├── proto_cross_platform.md      ← 未动
│   │   └── bujue-design-system/
│   │       ├── tokens.md                ← 既有
│   │       ├── COMPONENTS.md            ← 既有
│   │       ├── INSTRUCTIONS.md          ← 既有
│   │       ├── components/button.md     ← 既有
│   │       ├── components/card.md       ← 既有
│   │       ├── components/input.md      ← 既有
│   │       ├── components/tag-tab.md    ← 既有
│   │       ├── components/empty-loading.md  ← 既有
│   │       ├── components/_pending.md   ← 待补 10 个组件清单
│   │       ├── fb-fallback.css          ← ❌ 待建（批次 1）
│   │       └── fb-fallback-manifest.md  ← ❌ 待建（批次 1）
│   ├── scripts/
│   │   ├── gen_scaffold.py              ← 既有，未动
│   │   ├── assemble.py                  ← 待加注入逻辑（批次 1 一部分）
│   │   ├── precheck_stage4.py           ← 已扩展（含 8 项 proj 检查）
│   │   └── sync_skills.py               ← 新建
│   └── skills/
│       ├── .sources.json                ← 新建
│       └── (7 个 skill 框架文件)         ← fork 自上游
└── .claude/commands/
    ├── newRequirement.md                ← 已修复（升级处理策略）
    ├── nextStage.md                     ← 已修复（阶段 4 路由 + 升级策略 + Step 2.5 引用）
    ├── changeRequest.md                 ← 已修复（删 frontend-design）
    ├── retro.md                         ← 未动（早期叫 issueReview.md，2026-05-12 改名）
    └── projectStatus.md                 ← 未动
```

---

## 重启后建议第一步

1. Read `HANDOFF.md`（本文件）
2. Read `process_record/state.md`（反馈页测试上下文）
3. 决定下一步：
   - **A. 开工批次 1**（兜底 CSS + manifest + assemble.py 注入）—— 推荐
   - **B. 先清理反馈页测试**（`rm -rf process_record outputs`，state 重置）
   - **C. 处理遗留 🟢 优化建议**
   - **D. 验证未实测的 3 个修复**（构造场景跑一次）

---

## 关键决策快速回顾

| 决策点 | 结论 |
|--------|------|
| skill 应用机制 | Read SKILL.md（不依赖 Claude Code 平台 Skill 工具）|
| skills 上游 | github.com/deanpeters/Product-Manager-Skills，钉版 commit |
| 触点编号格式 | `M[XX]-P[XX]-T[NN]` / `H-M[XX]-P[XX]-状态` |
| 视觉自检清单引用 | proto_contract §十五（不是 §十四）|
| 兜底组件库参考 | **TDesign**（覆盖 Web/Mobile/Miniprogram 三端）|
| 兜底 CSS 命名前缀 | `fb-`（与 bujue 一致）|
| 兜底 CSS 接入方式 | 方案 C（assemble.py 自动注入到 PRD）|
| 中保真定义 | Balsamiq 结构 + 真实数据 + 状态可辨；不像素精雕 |
| proj 组件 PRD 输出 | 必须独立状态展示区 + 模块帧引用，两者并存 |
| PM 边界 | 设计 + 可视化 proj 组件，不实现生产代码 |
