---
name: workflow-evolution-templates
provenance: "本模板配套 SKILL.md 的 Step 3 / Step 7 / Step 8 使用,提供进度文件 / SSOT 同步清单 / 完成报告三个核心模板"
ssot_role: "derived_view"
ssot_true_source: "SKILL.md（流程定义为权威源）"
ssot_adjustment_direction: "先改 SKILL.md、再同步本模板；禁止反向"
ssot_anchor_id: "ssot_anchors.md #33"
---

## Template 1｜进度文件模板（Step 3 用）

新建 `process_record/progress/workflow_evolution_YYYY-MM-DD_HHMM.md` 或在既有 `issue_*_plan.md` 末尾追加新段时使用。

```markdown
## [系列代号] [任务名] — 编排器 skill 路径

**触发来源**：[产品总监对话/retro 复盘/编排器自识别/PM-NB 上报 + 简短描述]
**路径确认**：L2 任务 → skill 路径（按 §路径判定 L2 一律走 skill）；规模 [N 文件 / ~XK token]，[启用 / 不启用] 分批执行模式
**开始时间**：YYYY-MM-DD HH:MM

**`[Recommended]` 产品总监原话 + 编排器理解**（SKILL.md Step 1.5 触发；自然语句反馈类必填，明确 file:line 类可省）：
- 原话原文：「[逐字复贴产品总监本次反馈，引号包裹]」
- 编排器理解：我理解为 [X 具体改动];可能误读点 [Y 备选解读 / 抽象词的多义]——审 diff 时请重点核对此处

**整改循环计数（SSOT #17 NB-WE-D3）**：
- `rework_round`：[N]（本任务整改第几轮,首次实施 = 0）
- `rework_type`：[初次实施 / 中段审核整改 / **终审 Supervisor 退回整改** / **终审产品总监意见整改**]（G-08 触发源区分见下）
- `terminal_rework_used`：[N/3]（**仅终审 Supervisor 退回整改**已用次数；**中段 + 终审产品总监意见整改不计入**——G-08 触发源限定：L3 信号意图捕获"PM 思路↔Supervisor 标准方向性冲突",产品总监主动改方向不属于该信号,混算会污染信号致升级 SOP 空触发）

### Atomic Steps

- [ ] [系列码]-1 [步骤描述]
- [ ] [系列码]-2 [步骤描述]
- [ ] [系列码]-3 [步骤描述]
- [ ] [系列码]-4 机械自检（[具体方式]，门 1）
- [ ] [系列码]-5 SSOT 同步检查
- [ ] [系列码]-6 编排器自审（门 2，按 SKILL.md Step 7.5 5 项清单）
- [ ] [系列码]-7 完成报告 + git diff 强制展示（门 3）

### NB 清单（编号 NB-WE-NN，挂账非阻塞性问题）

- [ ] NB-WE-01：...
- [ ] NB-WE-02：...

### 机械自检证据（门 1）

[grep / pytest / structure_check 等输出]

### 编排器自审记录（门 2，对照 SKILL.md Step 7.5 5 项清单）

- [ ] 1. 规则间语义冲突核查 — [结论]
- [ ] 2. SSOT 抽象层级核查 — [结论]
- [ ] 3. 论据强度核查 — [结论]
- [ ] 4. 边界场景核查 — [结论]
- [ ] 5. 双向引用核查 — [结论]

**自审结论**：✅ 全部通过 / ⚠ 已挂 NB / ❌ 须返工

### SSOT 同步结果

- 真源：[文件:行号]
- 派生：[文件:行号]（≥ 1 个）
- 调整方向：[已声明/已沿用]
- 双向引用：[已就位/部分就位/缺]
- 机械兜底：[已就位/挂 B 组架构债]

**完成时间**：YYYY-MM-DD HH:MM
**总耗时**：[N] 分钟
**总 token**：[~XK]（编排器对话增量估算）
```

---

## Template 2｜SSOT 同步检查清单（Step 7 用）

每次 L2 改动后,逐项核查:

```markdown
### SSOT 同步检查清单

**1. 是否触发新建双锚关系？**
- [ ] 是 → 在 `pm-workflow/rules/ssot_anchors.md`加新行
- [ ] 否 → 跳过 1-3，直接看 4-6

**2. 新双锚 5 要素核查（如新建）**
- [ ] ① 权威源声明（明示哪个文件 + 字段路径是 SSOT）
- [ ] ② 派生视图标注（列出派生 / 复刻 / 反向引用的下游清单）
- [ ] ③ 调整方向（先改源、再同步派生，禁止反向）
- [ ] ④ 双向引用（源 → 派生 / 派生 → 源 必须有显式 link）
- [ ] ⑤ 机械兜底（precheck / gen_scaffold validate / assemble 校验等任一）

**3. 新双锚归组**
- [ ] 5 要素全齐 → A 组（5/5 完备）
- [ ] 缺机械兜底 → B 组架构债，标注 ❌ 缺...
- [ ] 缺多项 → C 组架构债

**4. 既有双锚是否需更新？**
- [ ] 真源改了 → 派生侧同步（按调整方向"先改源、再改派生"）
- [ ] 派生扩展了 → 在双锚行的「派生视图」列加新条目
- [ ] 机械兜底新增了 → 在双锚行的「机械兜底」列更新

**5. 双向引用核查**
- [ ] 真源文件中是否有指向派生的链接？
- [ ] 派生文件中是否有指向真源的链接？
- [ ] 双向都缺 → 至少补一向（标 ⚠ 单向，挂 NB 后续补）

**6. 标题数字 + 组数核查**
- [ ] 加新双锚后，`pm-workflow/rules/ssot_anchors.md`标题"N 对"是否同步 +1？
- [ ] A/B/C 组数量是否同步更新？

**7. Path 重命名 / 内容下沉时同步架构地图（NB-WE-30 落地）**
- [ ] 本次改动是否涉及 章节号重命名 / 内容跨文件下沉 / 文件路径变化？
- [ ] 是 → 跑 `pm-workflow/rules/workflow_architecture_map.md §七 Path 重命名 checklist` 4 步（grep 旧路径 + 核查 §三 文件分组表 + 核查 §五 影响速查表 + 核查 §四 TOP 5）+ broken link 自检命令
- [ ] 否 → 跳过本项

**8. 模板纯净度复检（防止整改原因注释污染 outputs）**
- [ ] 本次改动是否触及 5 个模板文件之一（`prd_template.html` / `tmpl_需求分析.md` / `tmpl_功能规划.md` / `tmpl_产品定义.md` / `task_card_template.md`）？
- [ ] 是 → 跑 `python3 pm-workflow/scripts/precheck_template_purity.py`，必须 [PASS]；若 FAIL → 删运维痕迹字面（日期 / issue / NB / retro / 复盘根因 / 建议 N 落地），参 `workflow_maintenance_protocol.md §模板纯净度红线` 三条红线
- [ ] 否 → 跳过本项（其他 L2 文件不受此约束）

**9. `[Must]` 真源升级 → 派生层联动核查（/retro 2026-05-13 共性根因 1 防御）**
- [ ] 本次改动是否升级了某 SSOT 真源（数值 / 枚举 / 字面字典 / schema / thead 字段名等）？
- [ ] 是 → 跑 `ssot_anchors.md` 查该双锚行的「派生视图」列，**逐项核查派生层是否已同步**（precheck 硬编码字典 / 规范文件描述 / 真源 css / 任务卡 / 模板等）；若有 N 个派生 → 修改清单中应有 N 处对应改动
- [ ] 是 → 跑 `pm-workflow/rules/workflow_architecture_map.md §五` 改动影响速查表，找「改 X → 同步 Y」对照行逐项核查覆盖
- [ ] 是 → 评估是否给精检函数加「反向真源解析」（参 `workflow_maintenance_protocol.md §机械兜底反向真源解析准则`），高 ROI 时补齐 `_parse_X_truth_source()` 防未来漂移
- [ ] 否（纯派生层改动，真源不动）→ 跳过本项

> **Why 这是 [Must]**：本会话 /retro 复盘共性根因 1 显示，至少 5 次「真源升级 → 派生层漂移」事故（z-index legal_set / frame position / sheet 规范 / S4-25 编号 / changelog thead），全部由"PM 人工记住要同步派生"失败导致 — 必须在 commit 前硬约束兜底。

**10. `[Must]` 新建 L2 文件 → 架构地图同步（2026-05-14 实战先例落地）**
- [ ] 本次改动是否在 `pm-workflow/agents/` / `pm-workflow/rules/`（含 `bujue-design-system/`）/ `pm-workflow/scripts/` / `pm-workflow/skills/` / `.claude/commands/` 下**新建文件**（非已有文件修改）？
- [ ] 是 → 在 `pm-workflow/rules/workflow_architecture_map.md §三 文件分组功能表`找对应段（顶层规则 / 角色规范 / 阶段 X 模板 / 阶段 4 交付规范 / 设计系统 / 脚本兜底 / Skill / 斜杠命令 / 过程记录 / 业务产物）补 1 行（路径 + 定位 + SSOT 归属）
- [ ] 是 + 该文件未来可能频繁改动 / 与其他文件存在派生关系 → 在 §五 改动影响速查表加 1 行（"改 X → 同步 Y"），明示触发联动条件
- [ ] 是 + 文件可能涉及 SSOT 真源 → 评估是否在 `ssot_anchors.md` 加双锚关系（参第 1-3 项）
- [ ] 是 + 文件需 PM / Supervisor 在阶段流程中触发 → 评估是否同步 `AI产品经理_Agent.md` / `AI产品主管_Agent.md` 自审清单（[Recommended] 温和触发或 [Must] 强制读，依文件性质判断）
- [ ] 否（仅修改既有文件）→ 跳过本项

> **Why 这是 [Must]**：第 1-9 项清单**只覆盖"既有文件改动"场景**，未显式覆盖"新建文件"。本会话 2026-05-14 实战先例：新建 `proto_data_display_selection.md` 走完 Step 7 9 项后仍漏更新架构地图，因新文件不属"真源升级"也不属"path 重命名"。架构地图是 L2 改动前必查的指针，新文件不入索引 = 后续维护者查不到 = SSOT 派生层漂移源头。本项专门兜底新建文件场景，与 1-9 项互补。

**11. `[Must]` 规则增量落盘 SOP（SSOT #60，治"编号撞号 + 基数失修"系统性盲区）**

详 `SKILL.md Step 7.4`；本节四项 grep 自检逐项打钩：

- [ ] **11.1 编号空间冲突自检**：新增 SSOT/S-XX/D-XX/G-XX/check_* 等编号时，跑 `grep -rn "<编号>" pm-workflow/ CLAUDE.md`；命中既有同号 → 改名递增至下一未占用编号；按编号家族判定（不按"全仓不撞"）
- [ ] **11.2 文档基数同步自检**：新增 check_/表行/维度 → grep `"N 项"` / `"N 对"` / `"N 个维度"` 字面全仓同步；基数动态计数（`grep -c "^def check_"` / `awk -F'|' '/^\| [0-9]+ /{c++}END{print c}'`）
- [ ] **11.3 对照表 / 维度表同步**：S4-XX → `rule_hard_constraints §六.X` 对照表加行；D-XX → `AI产品主管_Agent.md §4.5` 维度表 + SOP 数字；SSOT → ssot_anchors 5 要素
- [ ] **11.4 动态计数语义替代硬编码**：基数在 ≥ 3 处冗余 → 改"详见 X 文件头部（动态计数，截至 YYYY-MM-DD 为 N 对；脚本：`<grep 命令>`）"语义；2 处冗余 → 加交叉引用；1 处 → 不动

> **Why 这是 [Must]**：L2 矛盾审计实证 — G/A/B/C/D/F 6 方案密集落盘后未走此 SOP 导致 9 项高置信度矛盾沉淀（S3-06 一物二用 / 24 项 vs 49 项 / 50/36 对 vs 59 对 / Sup §4.5 D-07 vs D-09 等）；本项与 §10 互补——§10 治"新文件不入索引"，§11 治"新编号撞号 + 基数失修 + 对照表脱节"。
```

---

## Template 3｜完成报告模板（Step 8 用）

实施完成后在对话中输出:

```markdown
## [系列代号] 完成 — 等用户决策

### 改动摘要

| 项 | 文件 | 改动 |
|---|------|------|
| WE-1 | [文件路径:行号] | [简短描述] |
| WE-2 | [文件路径:行号] | [简短描述] |
| ... | ... | ... |

### 机械自检证据（门 1）

- **grep 验证**：[输出关键行数 / 命中位置]
- **pytest 烟测**（如适用）：`X passed in Y.YYs` / 0 warning / 0 skip
- **structure_check**（如适用）：✅ PASS
- **实际跑改后脚本**（如适用）：[退出码 / 输出摘要]

### 编排器自审记录（门 2）

[从进度文件 Step 7.5 段复制 5 项清单 + 结论]

### SSOT 同步结果

[按 Template 2 清单逐项打钩]

### NB 清单（NB-WE-NN）

- **NB-WE-01**：[问题描述] —— [挂账理由,何时消化]
- **NB-WE-02**：...

### `[Should]` 视觉验证清单（触发条件参 SKILL.md Step 8；改 PRD/spec 视觉呈现类必填）

机械三门抓不到视觉问题——下游请打开浏览器逐项验证（**触发条件**：模板 CSS 几何 / 模板 DOM 结构 / DSL 多元素布局 / nav 信息架构 / 帧渲染等 ⇒ 必填；纯 docstring / 注释 / 测试代码 ⇒ 可省「本批无视觉改动」一行说明）：

- [ ] [打开哪个 outputs/prd_*.html / 看哪个 section] — 关注 [视觉点 1，如：间距是否符合预期 / 几何尺寸 / 元素对齐 / 渲染时序]
- [ ] [...] — 关注 [视觉点 2]
- [ ] ...

### git diff 实际输出（门 3，强制展示）

```
[git diff --stat 输出]
```

```diff
[git diff 完整输出 — 让产品总监审完整改动后再决策]
```

### Token 消耗实测

- 编排器对话增量：~[XK] token
- vs Agent 路径（PM ~150K + Supervisor ~140K）：节约 ~[XX]%

### 等用户决策

- 改动是否 commit？
- 是否 push？
- 是否有遗漏需补？

回 "1（commit + push）/ 2（commit 不 push）/ 3（结束不 commit）"；或继续提调整。
```

---

## 使用流程速查

```
T1 任务理解
  └─ Step 1：在对话输出本质 + 范围 + 阈值核查

T2 必读路径
  └─ Step 2：编排器自己 Read（精简版）

T3 进度记录
  └─ Step 3：用 Template 1 创建/追加进度文件

T4 切分
  └─ Step 4：atomic step 切分（粒度 ≤ 5 分钟/步）

T5 实施
  └─ Step 5：每步完成立即 [x]，遇不确定 → NB 挂账继续

T6 自检
  ├─ Step 6：机械自检（按改动类型选必跑项）
  ├─ Step 7：用 Template 2 核查 SSOT 同步
  └─ Step 8：用 Template 3 输出完成报告
```

---

## 与既有方法论的对应关系

本模板是 `pm-workflow/rules/agent_methodology.md` 的 T1-T6 + X1-X4 在「编排器执行 L2 任务」场景下的实例化：

| agent_methodology 通用 | 本 skill 实例化 |
|----------------------|--------------|
| T1 任务理解 | Step 1（编排器在对话输出，不写到独立文档）|
| T2 必读路径 | Step 2（精简版，编排器主对话已含部分上下文）|
| T3 atomic step 切分 | Step 3 + Step 4（写进度文件 + 切分）|
| T4 实施 | Step 5（编排器直接用 Edit / Write / Bash）|
| T5 自检 | Step 6 + Step 7 + Step 7.5（机械检查 + SSOT 同步 + 编排器自审 = L2 三道质量门的前两道）|
| T6 收尾 | Step 8（完成报告 + git diff 强制展示 = 门 3 + 等用户决策）|
| X1 中断恢复 | 编排器主对话天然恢复（重读进度文件）|
| X2 atomic step 不变式 | 同 PM Agent（每步独立可验证 / 即时勾选）|
| X3 NB 处置 | 同 PM Agent（即时挂账，编号 NB-WE-NN）|
| X4 外部反馈 | 用户在对话中提反馈 → 编排器即时调整 |
