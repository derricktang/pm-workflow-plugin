---
name: workflow-evolution-examples
provenance: "本会话(2026-05-06)累计 11 次 PM/Supervisor 闭环中,5 个适合走 skill 路径的 L2 任务案例 — 用作判断阈值 + 流程参考"
---

# Workflow Evolution Skill 应用案例

## 案例 1｜Token 添加（issue #7 BL 系列，最简）

**背景**：产品总监要求新增 `--fb-error-bg-light` 错误浅色背景 token。

**阈值判定**：
- 文件数：2 个（prd_template.html + tokens.md）
- 预估 token：~30K
- 无新建脚本
- ✅ 走 skill 路径

**Atomic Steps**（4 步,共 ~10 分钟）：

1. `[ ] BL-1 prd_template.html :root 亮色块加 --fb-error-bg-light: #FEEDEF`
2. `[ ] BL-2 prd_template.html :root 暗色块加 --fb-error-bg-light: #3D1520`
3. `[ ] BL-3 tokens.md 颜色表登记 + 用途说明`
4. `[ ] BL-4 grep 验证（3 处含 + fb-fallback.css 未变）`

**机械自检**：
```
$ grep -n "fb-error-bg-light" pm-workflow/rules/prd_template.html pm-workflow/rules/bujue-design-system/tokens.md
prd_template.html:31:      --fb-error-bg-light: #FEEDEF;
prd_template.html:58:      --fb-error-bg-light: #3D1520;
tokens.md:108: ... fb-error-bg-light ...
$ grep "fb-error-bg-light" pm-workflow/rules/bujue-design-system/fb-fallback.css  # 应为空
```

**SSOT 同步**：沿用既有 SSOT #4（prd_template ↔ tokens.md），无需新建双锚。

**NB**：3 条（NB-BL-01/02/03）

**实测 token**：~50K（实际 PM Agent 路径 235K，节约 ~78%）

**关键经验**：
- ✅ 单 token 添加是 skill 路径最佳示例
- ✅ 真源（template）→ 派生（tokens.md）顺序严格遵守
- ✅ 不动 fb-fallback.css 既有组件,符合"最小变更"原则

---

## 案例 2｜单条 SSOT 双锚加（IC-8 系列，中等）

**背景**：issue #4 DOM 重构（interaction-card 移出 frame-card）+ IC-7 加 precheck `check_section_nesting` 后，需在 SSOT 双锚清单加 #25。

**阈值判定**：
- 文件数：1 个（CLAUDE.md）
- 预估 token：~25K
- 无新建脚本
- ✅ 走 skill 路径

**Atomic Steps**（3 步,共 ~8 分钟）：

1. `[ ] IC-8-1 `pm-workflow/rules/ssot_anchors.md`标题 24 → 25`
2. `[ ] IC-8-2 A 组数量 7 → 8`
3. `[ ] IC-8-3 加 #25 行(主源 + 三规则机械兜底说明)`

**机械自检**：
```
$ grep -c "^| [0-9]" CLAUDE.md  # 数清单行
$ grep "25 对" CLAUDE.md  # 标题数字一致
```

**SSOT 5 要素核查**：
- ✅ 主源：prd_template.html DOM + prd_expression_standard §四
- ✅ 派生：task_card_template.md / gen_scaffold.py / precheck_stage4.py
- ✅ 调整方向：明示「先改 template、再同步派生」
- ✅ 双向引用：CLAUDE.md → precheck 函数名 + precheck 注释 → 真源
- ✅ 机械兜底：precheck check_section_nesting（R1/R2/R3 三规则）

**NB**：0

**关键经验**：
- ✅ 加 SSOT 双锚行是 skill 路径标准动作
- ✅ 5 要素必须齐全才进 A 组,否则进 B 组架构债

---

## 案例 3｜元规范修订（TS 系列，中等）

**背景**：`/retro` 复盘后产品总监确认建议 1-4，加 4 条规则到 CLAUDE.md / agent_methodology.md。

**阈值判定**：
- 文件数：2 个
- 预估 token：~40K
- 无新建脚本
- ✅ 走 skill 路径

**Atomic Steps**（5 步,共 ~25 分钟）：

1. `[ ] TS-1 `pm-workflow/rules/workflow_maintenance_protocol.md`加「模板/规范描述粒度原则」[Must]`
2. `[ ] TS-2 `pm-workflow/rules/ssot_anchors.md`标题下加机械兜底 [Must] 条款`
3. `[ ] TS-3 CLAUDE.md「调整意见自动记录规则」第二步加「预防性排查模式」[Should]`
4. `[ ] TS-4 agent_methodology.md 加 §七「新规则建立的边界思考清单」[Should]，原 §七 重编为 §八`
5. `[ ] TS-5 跨文件 grep 验证（4 条新条款 + 强度标签 + 引用关系）`

**机械自检**：
```
$ grep -n "[Must]\|[Should]" CLAUDE.md | head -20  # 标签计数
$ grep "§七\|§八" pm-workflow/rules/agent_methodology.md  # 重编号验证
```

**SSOT 同步**：
- TS-1 引用 prd_expression_standard.md §零（单向引用，挂 NB-TS-01 后续补双向）
- TS-4 与 agent_methodology §六 SSOT 主从原则对齐

**NB**：3 条（NB-TS-01/02/03）

**关键经验**：
- ✅ 元规范修订是 skill 路径"中等任务"代表
- ✅ 4 条规则跨 2 文件，仍在阈值内（< 5 文件）
- ✅ 强度标签必须正确（[Must] 底线 / [Should] 重要约束有例外）

---

## 案例 4｜SSOT 派生漂移修补（SR-01，最小）

**背景**：上轮 R-01/R-02 修补后，Supervisor 审核发现 `prd_expression_standard §A-04.1.4` 与 `prd_template.html` 真源在 `switchJourneyView` 函数体存在轻度漂移。

**阈值判定**：
- 文件数：1 个（仅改 prd_expression_standard.md）
- 预估 token：~15K
- 无新建脚本
- ✅✅ 走 skill 路径（最小级）

**Atomic Steps**（4 步,共 ~5 分钟）：

1. `[ ] SR-01-1 Read template 真源 + 提取 switchJourneyView 完整代码`
2. `[ ] SR-01-2 Read standard 派生 + 定位 switchJourneyView`
3. `[ ] SR-01-3 standard 逐字替换为真源`
4. `[ ] SR-01-4 grep 验证字面一致`

**机械自检**：
```
$ diff <(grep -A 25 "function switchJourneyView" prd_template.html) \
       <(grep -A 25 "function switchJourneyView" prd_expression_standard.md)
# 应为空
```

**SSOT 同步**：沿用 SSOT #4（template ↔ expression_standard），仅修复派生漂移，不改双锚结构。

**NB**：0

**关键经验**：
- ✅ 最简 skill 路径案例（< 30 行改动）
- ✅ 真源 → 派生 单向同步,严格守"先改 template、再改 standard"
- ✅ diff / grep 字面对齐验证是机械自检黄金标准

---

## 案例 5｜小幅自审清单升级（HC-5 单段）

**背景**：issue #6 完成后,需在 AI产品经理_Agent.md §五.1/2/3 自审清单顶部统一加「机械检查前置（必须,自检第一步）」段。

**阈值判定**：
- 文件数：1 个（AI产品经理_Agent.md）
- 预估 token：~30K（要 Read 既有 §五 全段）
- 无新建脚本
- ✅ 走 skill 路径

**Atomic Steps**（4 步,共 ~12 分钟）：

1. `[ ] HC-5-1 Read §五.1 / §五.2 / §五.3 / §五.4 现有结构`
2. `[ ] HC-5-2 §五.1 / §五.2 / §五.3 顶部加新段（措辞与 §五.4 对齐）`
3. `[ ] HC-5-3 §五.4 既有段措辞校对一致`
4. `[ ] HC-5-4 grep 验证 4 处「机械检查前置（必须,自检第一步）」字面一致`

**机械自检**：
```
$ grep -c "机械检查前置（必须,自检第一步）" pm-workflow/agents/AI产品经理_Agent.md
4
```

**SSOT 同步**：沿用 SSOT #26-#29（4 个新建的阶段产物 ↔ 校对脚本双锚），自审清单是其派生应用。

**NB**：0

**关键经验**：
- ✅ 4 处文档同步用 grep 字面计数验证最直接
- ✅ "措辞与 §五.4 对齐"是 skill 路径常见 SSOT 同步模式

---

## 案例 6｜CLAUDE.md 大瘦身：物理拆分到 L2 子文件（最大型,2026-05-08）

**背景**：CLAUDE.md 91KB / 1005 行，超 system prompt 友好上限,Claude Code 报"Large CLAUDE.md will impact performance"。每次主对话固定加载,token 浪费且模型注意力被稀释。

**路径**：L2 任务 → skill 路径(启用分批执行模式)；规模 27 文件 / ~700 行迁移 / 4 批

**Atomic Steps**（11 步分 4 批）：
- 批 1：创建 3 新 L2 文件（agent_dispatch_protocol.md 594 行 / ssot_anchors.md 86 行 / workflow_maintenance_protocol.md 106 行）
- 批 2：CLAUDE.md 删已迁出段 + 替换指针段（1005 → 281 行 ↓72%）
- 批 3：4 轮 sed 跨 24 文件批量更新 ~30 处引用（agents / rules / scripts / commands / skills）
- 收尾：自检 + 27 文件统一 commit

**机械自检**：pytest 36/36 + 7 模块 import + grep 残留引用全部为合法语境（CLAUDE.md 保留段 / L2 路径字面值 / 历史档案）

**SSOT 同步**：3 个新派生关系（CLAUDE.md ↔ 3 拆出文件）声明为基础设施性质,不入 31 对清单；SSOT #1/#9/#31 真源路径迁移到 agent_dispatch_protocol.md（同步更新 ssot_anchors.md 中相关行）

**实测 token**：~250K（编排器对话增量,含 580 行规范段 Read + 多轮 sed + diff 展示）vs 派 Agent 路径估算 ~750K = **节约 67%**

**关键经验**：
- ✅ 主对话 system prompt 减负 ~16K token / 72%（最大单次 ROI）
- ✅ 物理拆分时,被拆出内容 100% 字面一致（不可随手简化）
- ✅ "21 维度"系统排查发现 4 处死引用补漏（pre-commit hook 不在 sed `--include=*.sh` 范围）
- ✅ 跨文件引用更新用 4 轮 sed 而非逐 Edit,~10 倍效率

**反例对照**：本任务在派 Agent 路径下需要先派 Architect Agent 出拆分方案,再派 Refactor Agent 执行,再派 Audit Agent 验证 — 至少 3 轮 PM/Supervisor 闭环 + 大量重复 Read,token 消耗倍增。

---

## 案例 7｜反向回流下游修复（fb-table 命名空间漂移,2026-05-08）

**背景**：下游 bujue-quotation-tool 跑 PRD 实际拼装时触发 S4-23 FAIL — `fb-table` 在 prd_expression_standard.md §11.4 + prd_template.html 中使用,但**从未在 pub_components_index / fb-fallback.css / components/*.md 登记**。下游精确诊断后修为 `proto-changelog-table`,**未回流真源**(派生侧改源未同步,违反 SSOT 调整方向)。

**路径**：L2 任务 → skill 路径；2 文件 ~33 行,小型不分批

**Atomic Steps**（3 步）：
1. prd_expression_standard.md §11.1 模板 + §11.4 配套 CSS：fb-table → proto-changelog-table（1 处 class + 3 条 CSS selector）
2. prd_template.html `<style>` 块加 .proto-changelog-table CSS（与 §11.4 字面一致）+ 4 处 class 替换
3. 机械自检 + commit

**机械自检**：fb-table 全仓 0 残留 / proto-changelog-table 跨 2 文件 11 处一致 / pytest 44/44

**SSOT 同步**：强化 SSOT #4 PRD template ↔ prd_expression_standard 双侧 §11.4 CSS 字面一致

**关键经验**：
- ✅ **命名空间纪律**：fb-* 前缀必须在 pub 索引/fallback.css 登记;新加内部 class 用 proto- 前缀避免占用
- ✅ **反向回流警觉性**：下游修源不同步是隐性 SSOT 违规,任何下游修复必须确认是否需回流真源
- ✅ **commit message 标"反向回流"**：让维护者一眼识别此类修订的特殊性质
- ⚠ **机械兜底盲点**：S4-23 仅扫 outputs/prd 派生,真源中 fb-table 漂移直到下游撞才暴露 → 后续 NB-WE-08 加 S4-23 扫 template 真源补盲点

**实测 token**：~40K（小型反向回流）vs 派 Agent 路径估算 ~150K = **节约 73%**

---

## 案例 8｜机械兜底从无到有：SSOT #4 升 4/5 → 5/5（架构债清理,2026-05-08）

**背景**：SSOT #4「PRD template CSS ↔ prd_expression_standard」在 B 组 4/5 完备已久,缺最后 1 项「无 CSS sync 脚本」机械兜底。本次加 check_css_sync.py 投产即检出 9 条历史漂移。

**路径**：L2 任务 → skill 路径；3 文件 ~150 行（1 新脚本 + 1 新测试 + 1 SSOT 更新）

**Atomic Steps**（4 步）：
1. `pm-workflow/scripts/check_css_sync.py`：从 standard 提取所有 ```css 块（10 个）→ selector → body 字典；同方式提取 template `<style>`；normalize（去注释 + 空白合并 + 末尾分号）+ 集合对比（漏同步 / 不一致 / template 独有豁免）
2. `tests/test_css_sync.py`：15 用例覆盖 normalize / extract / compare 三类逻辑 + TestRealRepo 实际仓库 §11.4 9 个 changelog selector 字面一致断言
3. 跑实际数据 → **检出 9 条历史漂移**（4 漏同步 .proj-component-showcase 系列 + 5 不一致 .section-meta / .page-id / .page-name / .tp-marker / .sidebar-component-status）
4. ssot_anchors.md SSOT #4 行 4/5 → 5/5 移入 A 组（A 16→17 / B 11→10 / 总 31 不变）

**机械自检**：pytest 44 → 59 全过 / check_css_sync.py 投产即可见效

**关键经验**：
- ✅ **机械兜底投产即检出真实漂移**：本次 9 条漂移在 commit 7d5c326 后早就存在,但人工审核未抓到 — 投产即可见效是兜底价值的最佳证明
- ✅ **修脚本 vs 修漂移分批**：本次 commit 仅交付机械兜底（脚本 + 测试 + SSOT 升级）,不含漂移修复 — 漂移挂 NB-WE-09 下迭代清理(职责分离)
- ✅ **示意性 CSS 块识别**：§9.1 fallback 注入示例含 `... 占位字面量 ...`,正则误识别为跨块 selector → 加 `\.\.\..*\.\.\.` 跳过示意块的容错

**实测 token**：~100K（脚本 ~150 行 + 测试 ~120 行 + 实际数据验证）vs 派 Agent 路径估算 ~280K = **节约 64%**

---

## 案例 9｜历史漂移机械检出后修复（NB-WE-09,2026-05-08）

**背景**：案例 8 的 check_css_sync.py 投产后立即检出 9 条 SSOT #4 历史漂移。本次按调整方向"先改 template、再同步 standard"逐条清理。

**路径**：L2 任务 → skill 路径；2 文件 ~17 行

**Atomic Steps**（10 行 sed + Edit）：
- 5 条不一致：standard 同步 template 字面值（template 真源）— sed 替换单行 / Edit 替换多行块
- 4 条漏同步（.proj-component-showcase 系列）：standard §七 7.1 已声明,补到 template `<style>` 块
- 跑 check_css_sync.py 验证 [PASS]

**机械自检**：check_css_sync.py 0 漂移 / pytest 59 全过

**关键经验**：
- ✅ **逐条修复 + 重跑兜底验证 PASS**：每改一条立即重跑脚本，避免最后一次性发现多重错误
- ✅ **真源选择影响修复方向**：SSOT #4 调整方向是"template 真源"（实际渲染依据 template）,所以 5 条不一致以 template 为准修 standard,不是反过来
- ✅ **机械兜底从"投产"到"清债"是分两次 commit**：避免一次 commit 既建工具又改大量数据,审计粒度模糊

---

## 9 个案例的 token 消耗对比表

| 案例 | Skill 路径实测 | Agent 路径估算 | 节约 |
|------|--------------|--------------|------|
| 1. Token 添加（BL）| ~50K | ~235K | **78%** |
| 2. SSOT 双锚加（IC-8）| ~40K | ~290K | **86%** |
| 3. 元规范修订（TS）| ~80K | ~244K | **67%** |
| 4. 派生漂移修补（SR-01）| ~30K | ~213K | **86%** |
| 5. 自审清单升级（HC-5）| ~50K | ~290K | **83%** |
| 6. CLAUDE.md 大瘦身（27 文件物理拆）| ~250K | ~750K | **67%** |
| 7. 反向回流 fb-table（命名空间纪律）| ~40K | ~150K | **73%** |
| 8. 机械兜底建设（SSOT #4 升 5/5）| ~100K | ~280K | **64%** |
| 9. 历史漂移清理（9 条 CSS）| ~30K | ~120K | **75%** |
| **平均** | **~75K** | **~285K** | **~75%** |

→ skill 路径平均节约 75% token（含大型物理拆分场景）,**且方法论纪律完整保留**（atomic step / 即时勾选 / 机械自检 / SSOT 同步 / NB 挂账）。

---

## 大型 L2 任务的分批执行示例（取代旧"超阈值派 Agent"反例）

按新阈值规则（L1/L2 二元判定），以下历史"曾派 PM Agent 的大型 L2 任务"**回顾应走 skill 分批模式**：

### 示例 A｜issue #1 用户旅程可视化升级（跨 6 文件 / ~600K）

**当时实际路径**：派 PM Agent + Supervisor Agent（PM 328K + Supervisor 272K = 600K）。

**按新规则应走 skill 分批模式**：

```
批 1 (atomic step W1-W4)：
  - 修订 proto_contract.md §十一（mermaid 局部豁免）
  - 修订 precheck_stage4.py mermaid 检查规则
  - 写 checkpoint 进度文件

批 2 (atomic step W5-W8)：
  - 扩展 tmpl_产品定义.md §5 用户旅程为结构化产出
  - 修订 prd_expression_standard.md 加 §A-04.1
  - 写 checkpoint

批 3 (atomic step W9-W11)：
  - 修订 prd_template.html 加 mermaid CDN + JS + CSS
  - 修订 `pm-workflow/rules/ssot_anchors.md`加 #24
  - 完成报告 + NB 挂账
```

**预估 token 节约**：~200K（vs 派 Agent 的 600K，节约 ~67%——大型任务节约率略低于小型，但仍显著）。

### 示例 B｜issue #6 阶段 1-4 校对脚本（建 4 脚本 / ~450K）

**当时实际路径**：派 PM Agent（PM 256K + Supervisor 197K = 453K）。

**按新规则应走 skill 分批模式**：

```
批 1：precheck_stage1.py 新建（基于 tmpl_需求分析.md）+ 5 测试用例
批 2：precheck_stage2.py 新建 + 5 测试用例
批 3：precheck_stage3.py 新建（含 Tier 2 FMT 校验）+ 5 测试用例
批 4：precheck_stage4.py 增强 REQUIRED_SPEC_BACKBONE_SECTIONS
批 5：AI产品经理_Agent.md §五.1/2/3 自审清单加机械检查前置 + CLAUDE.md SSOT 双锚 #26-29
```

**关键点**：每批结束写 checkpoint 进度文件,中间 800K context 可主动 `/clear` 重启 + state.md 恢复。

**预估 token 节约**：~180K（vs 派 Agent 的 453K，节约 ~60%）。

### 反 - 反例｜issue #1 中的 R-01/R-02 修补（~270K）

**当时**实际派 Agent（PM 150K + Supervisor 121K）。

**按新规则**：仍走 skill 路径。R-01/R-02 是改 prd_template.html + prd_expression_standard.md（纯 L2 文件），跨 2 文件 4 段,**约 100K 编排器对话增量**——单线连续即可,不必分批。

→ **本会话选派 Agent 路径是历史决策（旧规则下"稳妥"）,新规则下应直接走 skill。**

---

## 路径决策速查表（L1/L2 二元规则）

| 任务类型 | 修改文件归属 | 路径 | 备注 |
|---------|------------|------|------|
| 加 1 个 token | L2（prd_template.html + tokens.md） | **skill** ⭐ | 最简场景 |
| 加 1 条 SSOT 双锚行 | L2（CLAUDE.md） | **skill** ⭐ | 标准动作 |
| 改 1 个规则的措辞 | L2（CLAUDE.md / agent_methodology.md） | **skill** ⭐ | 直接编辑 |
| 加 1 段 [Must] 条款 | L2 | **skill** ⭐ | 标准动作 |
| 修 1 个脚本的 bug | L2（pm-workflow/scripts/） | **skill** ⭐ | 配 pytest 自检 |
| 跨 2-3 文件元规范修订 | L2 | **skill** ⭐ | 单线连续 |
| 跨 2-3 文件 + 改既有脚本 | L2 | **skill** ⭐ | 单线连续 |
| 新建脚本 / 测试套件 | L2 | **skill ⭐ 分批模式** | 大型,分多批写进度 checkpoint |
| 跨 5+ 文件大重构 | L2 | **skill ⭐ 分批模式** | 大型,分批 + 必要时 `/clear` 重启 |
| `/retro` 5a 步规范修订 | L2 | **skill** ⭐ | 编排器全程一气呵成 |
| L1 角色规范业务方法论核心改动 | L1 角色 | **派 PM Agent** | 让 PM 自指闭环 |
| `outputs/` PRD/spec 生成 / 修改 | L1 | **派 PM Agent** | L1 业务,与 skill 无关 |
| `process_record/state.md` 产品工作流状态 | L1 | **派 PM Agent** | L1 过程记录 |
