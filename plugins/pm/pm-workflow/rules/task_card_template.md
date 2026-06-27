# 任务卡模板（阶段四模块 Agent 任务单）

> 本文件定义阶段四任务规划阶段生成的标准任务卡格式。  
> 每个最小功能模块对应一张任务卡，由编排器在「任务规划阶段」预先生成全部任务卡后，再依次/并行派发各模块 Agent。

---

## 任务卡格式

```markdown
# 任务卡 M[XX]：[模块名称]

## 基本信息

| 字段 | 内容 |
|------|------|
| 模块编号 | M[XX]（如 M01、M02） |
| 模块名称 | [业务含义名，如「商品列表」「购物车」] |
| 端口 | [APP / 桌面 Web / 小程序 / H5，多端逗号分隔] |
| 任务类型 | spec 章节 + prd 模块（首次生成）/ 仅 spec 章节 / 仅 prd 模块（修改场景） |
| 对应产品定义章节 | §7.X [章节名] + §8.X（如有状态流转图） |
| 父级系统容器层归属 | [本模块在父级系统中的位置 + 兄弟模块清单 + 上一级 navbar 返回目标语义；或「N/A 独立产品」]（详 `proto_spec_md.md §四.9 父级系统容器层规约`） |

---

## 依赖项

### 全局资源（编排器已就绪，直接读取）

| 资源 | 路径 |
|------|------|
| spec.md 文档骨架 | `outputs/spec_[产品名]_latest.md`（Foundation Agent 已写入 S0+S1） |
| prd.html 文档骨架 | `outputs/prd_[产品名]_latest.html`（任务规划阶段 fork 自 prd_template.html） |
| 任务卡目录 | `process_record/tasks/`（所有模块任务卡） |
| 原始需求 | `需求简述.md` |
| 产品定义 | `outputs/产品定义_[产品名]_latest.md` |

### 跨模块技术契约（预分配 Section ID 总表）

> 以下为全量 Section ID 预分配表，由任务规划阶段统一生成。  
> 本模块 Agent 生成页面内跳转时，**只能使用此表中的 ID，禁止自造**。

| Section ID | 模块 | 说明 |
|-----------|------|------|
| `#spec-M01-[页面名]` | M01 | [简述] |
| `#spec-M02-[页面名]` | M02 | [简述] |
| `#H-M01-P01-[状态名]` | M01 | prd.html 锚点 |
| `#H-M02-P01-[状态名]` | M02 | prd.html 锚点 |
| ...（完整列表） | | |

### 本模块依赖的其他模块成果

| 依赖模块 | 依赖原因 | 依赖内容 |
|---------|---------|---------|
| M[XX] [模块名] | [为何依赖，如「跳转目标状态帧」] | [具体依赖内容] |
| （无依赖时填「本模块无跨模块依赖」） | | |

---

## 本模块技术契约

### 本模块 Section ID 清单

> 以下 ID 由任务规划阶段预分配，本模块 Agent 必须严格使用，不得修改。

**spec.md 章节锚点**：

| 章节 | Section ID | 说明 |
|------|-----------|------|
| 状态枚举表 | `spec-M[XX]-states` | |
| 页面1功能规格 | `spec-M[XX]-p1-[页面名]` | |
| 页面2功能规格 | `spec-M[XX]-p2-[页面名]` | |

**prd.html section 锚点**：

| 状态帧 | Section ID | 说明 |
|--------|-----------|------|
| 默认态 | `H-M[XX]-P[XX]-default` | |
| 空态 | `H-M[XX]-P[XX]-empty` | |
| 加载态 | `H-M[XX]-P[XX]-loading` | |
| [其他状态] | `H-M[XX]-P[XX]-[状态名]` | |

### 本模块触点编号段

> **两段式分配机制**（详见 `proto_contract.md §三` 全局编号体系表）：
> - **本段是 Step 1 任务规划阶段的"命名空间范围预分配"**——锁定本模块的 M[XX]-P[XX]- 前缀范围，**不预分配具体 T[NN] / D[NN] 编号**。
> - **具体 T01 / T02 / D01 等编号由 Step 3 模块 Spec Agent 在编写 spec 时按页面内顺序填入**——页面内触点从 T01 起递增，弹窗/抽屉内触点用 D 替换 T。
> - 编号格式遵循 `proto_contract.md §四`。

| 触点类型 | 编号格式 | 示例 | 分配阶段 |
|---------|---------|------|---------|
| 页面触点 | `M[XX]-P[XX]-T[NN]` | `M01-P01-T01` | 前缀 Step 1 锁定 / NN Step 3 顺序填入 |
| 弹窗/抽屉触点 | `M[XX]-P[XX]-D[NN]` | `M01-P01-D01` | 前缀 Step 1 锁定 / NN Step 3 顺序填入 |

---

## 规格内容来源

> Agent 执行前必须读取以下章节，作为本模块 spec 和 prd 的唯一内容来源。

| 产品定义章节 | 内容摘要 | 对应生成内容 |
|-------------|---------|------------|
| §7.[X] [功能名] | [一句话描述该章节核心内容] | spec 功能规格 + prd 交互说明 |
| §8.[X] [状态流转] | [一句话描述] | spec 状态枚举表 + prd 状态帧 |
| §9.[X] [数据字段] | [一句话描述] | spec 数据字段表 + prd 数据回显说明 |
| §11.[X] [异常处理] | [一句话描述] | spec 异常路径 + prd 异常状态帧 |

---

## 候选组件清单（v2.0：由 gen_scaffold 自动衍生，PM 不手填）

> **【v2.0 重大变更】**：本段从"PM 子阶段一手填"改为"由 `gen_scaffold.py` 在 Step 1.5 从 `process_record/tasks/scaffold.json` `modules[].candidate_components` 自动衍生写入"。
>
> **数据真源**：scaffold.json 的 `modules[ id == 本模块 ].candidate_components`（pub 列表 + proj_gaps）和 `modules[].owner_assignments`。
>
> **PM 子阶段一职责**：在 scaffold.json 中按 D1-D5 评估**每个模块**、填好 `candidate_components` 与 `owner_assignments`；任务卡本段保留为占位（写注释 `<!-- 由 gen_scaffold 从 scaffold.candidate_components 自动衍生写入，PM 不手填 -->`）。
>
> **下游 Spec/PRD Agent 读取**：以 scaffold.json 为权威；任务卡本段仅作"已衍生数据视图"（人类审阅或调试用），**不**作为下游 Agent 的事实来源。

### A. 候选 pub 组件（衍生自 `scaffold.modules[本模块].candidate_components.pub`）

| 组件 id | 业务用途 |
|---------|---------|
| `fb-btn-primary` | 提交按钮（主操作） |
| `fb-textarea` | 反馈多行输入 |
| ...（gen_scaffold 自动写入，PM 勿改） | |

### B. 候选派生 proj 组件（衍生自 `scaffold.modules[本模块].candidate_components.proj_gaps`）

> **`[Must]` 表格 ID 字面规则**：本表「候选 proj 名」列裸写（不加反引号）；「inherits」列同样裸写。理由与适用范围见 `proj_component_protocol.md §二.1` 顶部「表格 ID 字面规则」段。

| 候选 proj 名 | 触发因素 | 派生原因 | inherits | 共用模块 |
|-------------|---------|---------|---------|---------|
| proj.L3.product-card | A 跨模块复用 + B D1 字段缺口 | fb-card 仅 4 slot 不足以表达本模块 5 字段 | pub.L2.card | M02 / M03 |
| ...（gen_scaffold 自动写入，PM 勿改） | | | | |

### C. owner 分配（衍生自 `scaffold.modules[].owner_assignments`）

| proj 组件 | 本模块是否 owner | owner 模块 |
|----------|----------------|----------|
| proj.L3.product-card | ✅ 是 | M02 |
| proj.L1.rich-textarea | ❌ 否（仅引用 class） | M01 |
| ...（gen_scaffold 自动写入） | | |

> **owner 含义**：owner 模块的 PRD Agent 负责写完整 PROJ-CSS（base + 全部 needed:yes 状态 modifier）；非 owner 模块仅引用 class、禁止重复声明。owner 数据**唯一权威源**为 `scaffold.modules[].owner_assignments`——由 PM 子阶段一按 modules[] 顺序最靠前的引用模块推算并写入；下游（含本表 C 段、PRD 草稿 OWNER-INFO、编排器 prompt 注入）一律从该字段读取，**禁止重算**。详见 `pm-workflow/rules/agent_dispatch_protocol.md`「owner 流转链路」。

### D. 跳过说明（candidate_components.pub 与 proj_gaps 同时为空时由 gen_scaffold 写入）

- pub 索引版本：v1.x（gen_scaffold 注入实际版本号）
- 子阶段一已扫描维度：D1 字段 / D2 状态 / D3 交互 / D4 语义 / D5 约束 全部通过
- 结论：本模块未识别需要的 pub / proj 组件（裸文本/纯展示模块）

---

## 执行要求

### spec 章节生成要求（v2.0：占位填空模式）

- **草稿骨架已由 gen_scaffold 预生成**：`process_record/drafts/spec_M[XX]_draft.md`（含固定子章节 S2.M[XX] / .1~.6 + 预填部分表头/状态枚举/depends_on）
- **PM 工作**：在草稿骨架的每个 `[Spec Agent 填...]` 占位上替换为真实内容
- **章节标准**：见 `proto_spec_md.md §三.5`「单模块 spec 草稿章节标准」
- **禁止**：改章节顺序 / 标题 / 删除子章节 / 增加非标准章节 / 改 gen_scaffold 预填的状态枚举行结构 / 改预填的 depends_on 引用条目
- 本章节所有跳转必须使用「本模块技术契约」中预分配的 Section ID
- 禁止修改草稿文件以外的任何文件（spec.md 主文件由编排器通过 assemble.py 拼装）

### prd 模块生成要求（v2.0：占位填空模式）

- **草稿骨架已由 gen_scaffold 预生成**：`process_record/drafts/prd_M[XX]_draft.html`
  - 含 `<!-- [OWNER-INFO] ... -->` 注释（编排器从 scaffold.owner_assignments 读出的本模块 proj 归属）
  - 含 `<!-- [PROJ-CSS-START/END] -->` 占位（仅 owner 模块；non-owner 模块骨架中明确标"禁写 PROJ-CSS 块"）
  - 含全部 `<!-- [FRAME: prd_id] -->...<!-- [/FRAME: prd_id] -->` 占位（FRAME id 集合由 scaffold 锁定）
- **PM 工作**：在每个 FRAME 占位填帧内容；owner 模块在 PROJ-CSS 块写完整 CSS（base + needed:yes 状态 modifier）
- **owner 状态由编排器从 scaffold.owner_assignments 读出后写入 prompt**——PM 直接照办，不再自己读 components A 表判断、不重算
- **格式遵循**：`prd_expression_standard.md` + `prd_expression_standard.md §9.2 机器标记 audit trail`
- 使用的 CSS 变量只能来自 `bujue-design-system/tokens.md`
- **禁止**：
  - 改 FRAME id / 增删 FRAME（id 集合由 scaffold 锁定）
  - 改 OWNER-INFO 注释（编排器从 scaffold.owner_assignments 读出的事实，仅可读）
  - non-owner 模块写 PROJ-CSS 块（owner 模块独占写完整 CSS）
  - 写 `<html>/<head>/<body>`、`<section>...</section>` 外壳
  - 修改草稿文件以外的任何文件

**草稿格式（自上而下）：**

```html
<!-- 可选：本模块用到的 proj 组件 CSS（首个使用该 proj 的模块写完整定义，其他模块省略本块） -->
<!-- [PROJ-CSS-START] -->
.proj-{name} { /* base */ }
.proj-{name}.is-{state} { /* modifier */ }
<!-- [PROJ-CSS-END] -->

<!-- 必须：每个状态帧用 FRAME 标记包裹（FRAME id 对应 scaffold.json 本模块全部 prd_id） -->
<!-- frame-card 与 interaction-card 是 proto-section 的同级兄弟（FRAME 标记内顺序：frame-card 在前,interaction-card 在后） -->
<!-- [FRAME: H-M[XX]-P[XX]-default] -->
<div class="frame-card">
  <div class="frame-wrapper">
    ...视觉帧主体（phone-frame / desktop-frame / tablet-frame 等含组件、触点徽章）...
  </div>
</div>
<div class="interaction-card">
  ...触点说明、数据回显、边缘情况、业务规则文字...
</div>
<!-- [/FRAME: H-M[XX]-P[XX]-default] -->

<!-- [FRAME: H-M[XX]-P[XX]-empty] -->
<div class="frame-card frame-empty">
  <div class="frame-wrapper">
    ...空态视觉帧主体...
  </div>
</div>
<div class="interaction-card">
  ...空态对应的触点 / 数据回显说明...
</div>
<!-- [/FRAME: H-M[XX]-P[XX]-empty] -->
```

**拼装行为（PM 仅作认知背景，不必在草稿体现）：**
- `assemble.py prd` 提取 FRAME 内容 → 替换 prd 骨架占位（包裹形态变为 `[FRAME-START/END]` 用于重跑可重入）
- `assemble.py prd` 提取所有模块的 PROJ-CSS 块 → 合并 → 注入到 prd `<style>` 顶部 `[PROJ-CSS-START/END]` 占位
- `assemble.py prd` 自动注入 `fb-fallback.css` 到 prd `<style>` 块顶部（包裹于 FB FALLBACK START/END 之间，幂等）

### 分步执行要求

1. 开工前读取进度文件 `process_record/progress/stage4_[产品名]_plan.md`，确认本模块步骤状态
2. 先完成 spec 草稿，再生成 prd 草稿（顺序不可颠倒）
3. 每完成一个步骤立即更新进度文件（将 `[ ]` 改为 `[x]`）
4. 每完成一个 prd 状态帧立即执行规则7分步自审（Section ID 唯一、frame-card 数 = spec 状态表行数、触点 ID 集合一致）

---

## 验收标准

### spec 草稿验收

- [ ] 输出文件 `process_record/drafts/spec_M[XX]_draft.md` 已创建
- [ ] 本章节所有功能点均有对应规格描述，无遗漏
- [ ] 状态枚举表行数与产品定义异常处理章节覆盖的状态一致
- [ ] 所有跨模块跳转目标均使用预分配 Section ID，无自造 ID
- [ ] 触点编号在本模块分配段内，无超出范围

### prd 草稿验收

- [ ] 输出文件 `process_record/drafts/prd_M[XX]_draft.html` 已创建
- [ ] 状态帧数 = spec 状态枚举表行数（零误差）
- [ ] 触点卡片数 = spec 触点表行数（零误差）
- [ ] 触点 ID 集合与 spec 完全一致
- [ ] 所有 Section ID 使用预分配值（用 Grep 核查无自造 ID）
- [ ] 色彩 100% 使用 `--fb-*` 变量
- [ ] 可点击元素均有 `cursor:pointer`
- [ ] 无 `<html>/<head>/<body>` 标签，草稿为纯 section 片段

### 通用元素覆盖清单（每页逐项勾选）

> **跨模块反复遗漏的通用元素**，PM 阶段 4 **每生产一页 prd 状态帧时**逐项过一遍（"不适用 / 豁免"也须显式标注，避免漏判而非漏勾）。本清单是 **L2 生产自检层**——与 ① 模板内置（`prd_template.html` 自带槽位，结构上漏不掉）+ ② precheck 机械门禁（`precheck_stage4.py`，漏了拦得回）**三层互补**，目的是在产出当下主动确认，避免依赖 precheck 整改往返。
>
> **判定标准前置**：返回按钮"加 / 豁免"判定、弹框遮罩、toast 端类定位、底栏对齐的完整判定路径见 `proto_cross_platform.md`（移动端操作布局 / 弹框规范 / 返回入口判定）；勾选时如拿不准"该不该加"，回查该规范，不靠直觉。

逐页核对（每页重复以下 5 项）：

- [ ] **返回按钮**：业务流子页（次级页面）含返回入口——移动端用 `.fb-navbar` 含 `.fb-nav-back`（S4-35 机械兜底）；**主导航直达页 / 浏览器原生返回域** → 标"豁免"（判定见 `proto_cross_platform.md`）
- [ ] **弹框遮罩**：modal / 移动端 sheet 帧含 `.fb-modal-overlay + .fb-modal` 标准结构（S4-25 机械兜底）；本页无弹框 → 标"不适用"
- [ ] **toast 端类定位**：`.fb-toast` 元素**置于所属 frame 内**（端类定位由 fb-fallback.css `:where()` 自动处理：桌面顶部 / 移动端底部，无需手写定位 class）；本页无 toast → 标"不适用"
- [ ] **标题栏**：页面含标题栏（移动端 `.fb-navbar` 含 `.fb-nav-title` / 桌面端 header）；全屏沉浸页 / 封面页 → 标"豁免"
- [ ] **底栏对齐**：桌面 / Pad 端含末位固定操作栏时 sticky bottom 对齐（S4-28 机械兜底）；本页无固定底栏 → 标"不适用"

### 完成后通知编排器

```
【M[XX] [模块名] 任务完成】
spec 草稿：process_record/drafts/spec_M[XX]_draft.md ✅
prd 草稿：process_record/drafts/prd_M[XX]_draft.html ✅
状态帧数：[N] 帧，与 spec 一致
触点数量：P [N] 个 / D [N] 个，与 spec 一致
跨模块跳转：使用预分配 ID [列举] ✅
异常/边缘：[简述已覆盖的异常状态]
```
```

---

## 任务卡生成说明（供编排器参考）

任务规划阶段，编排器（或 PM Agent）需为每个最小功能模块生成一张任务卡，步骤如下：

1. **模块拆分**：读取产品定义 §7 功能需求，按最小独立业务模块拆分，每个模块编号 M01、M02...
2. **Section ID 预分配**：为所有模块的所有页面/状态，统一预分配 `spec-M[XX]-*` 和 `H-M[XX]-P[XX]-*` ID，写入所有任务卡的「跨模块技术契约」表
3. **依赖分析**：分析模块间的跳转依赖关系，写入各任务卡的「依赖项」节
4. **任务卡文件命名**：`process_record/tasks/task_M[XX]_[模块名].md`
5. **任务卡索引**：所有模块结构、Section ID 预分配、依赖关系统一写入 `process_record/tasks/scaffold.json`（scaffold.json 即模块结构真理来源，不再单独维护 index.md）

任务卡全部生成后，编排器方可派发 Foundation Agent 和各模块 Agent。

---

## scaffold.json 字段填写要求

> 完整字段定义见 `pm-workflow/agents/AI产品经理_Agent.md` 子阶段一「scaffold.json 格式规范」。本节仅列出 PM 任务规划阶段应**优先填写**的字段，避免下游脚本 / 骨架使用默认值导致信息单薄。

| 字段 | 必填 | 用途 | PM 来源 |
|------|------|------|---------|
| `product` | ✅ | 产品名（影响所有产物文件命名） | 产品定义封面页 |
| `platforms` | ✅ | 端口数组（影响阶段 4 规范文件传入策略） | 产品定义 §1 / §3 |
| `modules` | ✅ | 模块清单（含 pages / states / prd_id / depends_on） | 产品定义 §7 拆分 |
| `version` | 推荐 | 版本号（写入 prd 封面徽章），缺省 `v1.0` | 与 spec.md 变更记录表对齐 |
| `description` | 推荐 | 产品一句话简述（写入封面副标题），缺省空 | 产品定义 §1 |
| `status` | 推荐 | 文档状态（封面状态徽章），建议值 `草稿` / `评审中` / `已批准` | 与 state.md 当前阶段状态对齐 |
| `changelog` | 推荐 | 变更记录数组（封面变更记录页），每项 `{version, date, author, desc}` | 与 spec.md 变更记录表逐条对齐 |
| `modules[].depends_on` | ✅ | 模块依赖（precheck 校验，影响 Step 3/5 并行调度顺序） | 任务规划阶段跨模块跳转分析 |
| `modules[].name` | ✅ | 模块业务名（写入侧栏导航 + state-chip 标签） | 产品定义 §7 |
| `modules[].pages[].route` | ✅ | 页面路由（写入 prd section-header 路由标签） | 产品定义 §6 / §7 |
| `modules[].pages[].states[].roles` | ✅ | 角色数组（写入 section-header 视角标注） | 产品定义 §3 / §4 |

**约束**：
- `depends_on[].module` 中的 ID 必须存在于 `modules[].id` 集合（precheck 强制校验，自依赖禁止；v2.0 schema 下 `depends_on[i]` 是对象 `{module, kind, target}`，不是 ID 字符串）
- `prd_id` 格式严格为 `H-M\d{2}-P\d{2}-[\w-]+`，且内部编号与所属模块 / 页面一致（precheck 强制校验）
- 任务规划阶段写入后**不可修改**编号体系；如需变更须走 `/changeRequest` 流程，禁止直接编辑 scaffold.json + 重跑 gen_scaffold
