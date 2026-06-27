# 交付契约 — 全局约束 v1.0

> **适用对象**：Claude PM Agent、Supervisor Agent
> **读取时机**：派发阶段4任务时**必须传入**，无论涉及哪个端口，均不可省略
> **文件定位**：本文件是所有交付文档规范的全局约束层，其他规范文件（`prd_expression_standard.md`、`proto_spec_md.md`、`proto_platform_*.md`）均在本文件约束之上叠加细节

---

## 规则强度说明

本规范各条规则按以下强度等级标注：

| 标签 | 含义 |
|------|------|
| `[Must]` | 必须遵守，无例外，直接影响原型质量或工具链一致性的底线规则 |
| `[Should]` | 原则上必须遵守，极端场景或特殊业务需求下可谨慎突破，须在 spec.md 中注明理由 |
| `[Recommended]` | 建议遵守，有明确理由时可灵活调整，属最佳实践 |
| `[Optional]` | 可选，根据产品特性决定是否采用 |

---

## 一、两份产出定义

PM Agent 接收阶段3《产品定义》后，必须输出**两份产出**，内容完全一致，表达方式不同：

| | 产出 A | 产出 B |
|--|--------|--------|
| **文件名** | `outputs/prd_[产品名]_latest.html` | `outputs/spec_[产品名]_latest.md` |
| **受众** | 人类 PM / UI / 开发 / 测试 | UI Agent / 开发 Agent / 测试 Agent |
| **表达方式** | 可点击的页面线框图 + 人类可读说明 | 严格 Markdown 结构，无 HTML，无装饰性内容 |
| **内容覆盖** | 完全相同 | 完全相同 |

---

## 二、`[Must]` 两份产出一致性约束

**任何违反以下约束的产出视为不合格，Supervisor 必须打回整改。**

> **约束适用范围**：以下一致性规则仅适用于 **Foundation Agent 和各模块 Agent 生成的内容**（产品概述区 A-01～A-08 + 各功能模块页面/状态/触点）。prd.html 中由 `gen_scaffold.py` 自动生成的文档脚手架页面（封面、使用说明、变更记录）属于文档元数据，面向人类读者，**不参与一致性校验**，也不需要在 spec.md 中体现对应章节。

> **`[Must]` 调整方向（SSOT 双锚 #12）**：spec.md 是**内容真源**(承载业务逻辑 / 状态枚举 / 触点定义),prd.html 是**派生展现**(可视化呈现);**先改 spec、再让 assemble.py 重生 prd**,**禁止反向**直接编辑 outputs/prd 业务内容。任何 PM 在 outputs/prd 上的手改会被下次 assemble fingerprint 校验拦截或覆盖（手改保护机制,详见 assemble.py 错误信息）。/issueReview 与 /changeRequest 涉及 PRD 改动时应改对应 `process_record/drafts/spec_M[XX]_draft.md`,由 assemble 重新拼装注入,不要直接改 outputs。

1. prd.html 功能模块区展示的任何页面、状态、逻辑，spec.md 中必须有对应的文字描述
2. spec.md 描述的任何规则，prd.html 功能模块区中必须有对应的视觉表现
3. **对称性硬性要求**：spec.md 每页状态枚举表行数 = prd.html 对应视觉帧数，误差为零
4. **触点对称**：spec.md 触点总表行数 = prd.html 触点卡片数，完全对应
5. 同一触点 ID 在两份产出中完全相同，不得各自编号

---

## 三、`[Must]` 全局编号体系

**核心原则：上层编号在模块拆分时一次性确定，不可事后重排；下层编号在对应 Agent 执行时按需分配。**

| 层级 | 格式 | 分配时机 | 分配主体 | 唯一性范围 |
|------|------|---------|---------|-----------|
| 模块 | `M[XX]`（M01, M02…） | 任务规划阶段，scaffold.json 生成时 | 任务规划 PM Agent | 全产品唯一 |
| 页面 | `P[XX]`（模块内，P01, P02…） | 任务规划阶段，scaffold.json 生成时 | 任务规划 PM Agent | 模块内唯一 |
| 状态 | 语义名（default / empty / loading…） | 任务规划阶段，scaffold.json 生成时 | 任务规划 PM Agent | 页面内唯一 |
| 功能需求 | `F-[XXX]`（F-001, F-002…） | 阶段三产品定义，全产品统一编号 | PM Agent | 全产品唯一 |
| 触点 | `M[XX]-P[XX]-T[NN]` | **`[Should]` canonical 单源（S4-34 治本，2026-05-22）**：全量触点于 Step 1 任务规划阶段在 `scaffold.pages[].touchpoints[]` 预声明（id `T01`/`D01` + kind + element + action），gen_scaffold 据此**预填 spec 触点表 canonical ID 行**，Spec Agent 仅补描述列、禁增删 / 改 ID。**旧两段式（向后兼容 fallback）**：scaffold 未声明 touchpoints 时回退——①前缀 Step 1 预分配 ②T[NN]/D[NN] Step 3 Spec Agent 手写（precheck S4-34 跳过校验，但反复出现 D4/D5 类手写偏差，故 [Should] 迁移到 canonical 单源）| ①任务规划 PM Agent 预声明 canonical（治本路径）/ fallback：①PM + ②Spec Agent | 页面内唯一 |

**硬性规则**：
- 模块（M）、页面（P）、状态三层编号写入 scaffold.json 后不得修改；需调整须走 `/changeRequest` 流程
- prd.html 中触点以**序号徽章**（01, 02…）展示，spec.md 中使用完整 `M[XX]-P[XX]-T[NN]` 格式
- 弹窗/抽屉内触点以 `-D[NN]` 后缀区分，如 `M01-P01-D01`
- 仅展示性元素（纯文本、图片）不分配触点编号
- **`[Should]` 触点 canonical 单源（S4-34，SSOT #44）**：触点编号优先在 `scaffold.pages[].touchpoints[]` 预声明，由 gen_scaffold 预生成 spec 触点表 ID 行——precheck `check_touchpoint_canonical` 校验 spec/prd 中任何 `M[XX]-P[YY]-[TD][NN]` 引用必 ⊆ canonical 集合（手写偏差 / 拼写错 / 跨页串号 → WARN）。增删触点须回 scaffold 重跑 gen_scaffold，禁止 spec/prd 手写 ID。详 `rule_hard_constraints.md §S4-34`。

---

## 四、`[Must]` 触点编号系统（触点格式细则）

触点 ID 命名规则：`M[XX]-P[XX]-[TDC][NN]`（v2 升级 2026-06-02 下游 D3 治本，扩 T/D/C 三系前缀）

- 示例：`M01-P01-T01`（Trigger）、`M01-P01-D02`（Data display 字段）、`M01-P01-C03`（Container 展示单元）
- `M[XX]`：模块编号，与 scaffold.json 一致
- `P[XX]`：模块内页面编号，与 scaffold.json 一致
- `[TDC][NN]`：前缀 + 两位序号；前缀 T/D/C 三系语义分类（详 §四.A），序号页面内从 01 起递增按前缀分别计数（T01/T02 / D01/D02 / C01/C02 各自独立计数）
- 弹窗/抽屉内触点独立编号，后缀改 `D`：`M[XX]-P[XX]-D[NN]`（注：此 D 是"对话框/抽屉"上下文标识，与 D-prefix 数据字段含义不同；上下文为弹窗时该位置的触点编号风格按上下文选定）—— **D3 落地后建议改用"对话框/抽屉视为独立 page"扩展 scaffold.pages 编号**避免歧义（NB-WE-06 待后续优化）
- **`[Should]` canonical 单源（S4-34）**：触点 ID 优先在 `scaffold.pages[].touchpoints[]` 预声明（id=`T01`/`D01`/`C01`），gen_scaffold 预生成 spec 触点表 ID 行，Spec Agent 仅补描述、禁改 ID——杜绝手写偏差（详 §三 触点行 + `rule_hard_constraints.md §S4-34`）

### 四.A、`[Must]` 触点前缀三系（T/D/C，SSOT #65，2026-06-02 下游 D3 治本）

`[Must]` 三系前缀语义分类（治"T/D 二系混用 - 把展示单元挤进 T"根因）：

| 前缀 | 全称 | 语义 | 示例 |
|------|-----|------|------|
| **T** | Trigger | 用户主动触发的**交互入口** | T01 新建按钮 / T03 chip 筛选 / T05 卡片点击 |
| **D** | Data display | **单字段被动回显** | D01 项目名称 / D02 业主联系 |
| **C** | Container | **多字段聚合的展示单元**（≥ 2 字段 + UI 块） | C01 项目卡片 / C02 业主信息卡 / C03 报价记录条 |

**C ≠ Component 区分**（概念正交，可同时存在）：
- C 触点 = spec 触点表的**语义分类**（UI 聚合单元）
- 组件（Component）= spec/proj 组件库的**封装层级**
- 一个 C 触点**可能**对应组件（如 `proj.L1.project-card`），也**可能**仅页面布局（非组件）
- prd 表 C-2.A 索引层「C 展示单元清单表」含「是否封装为组件」列分别表达（详 `prd_expression_standard.md` 区块 C-2 v2）

**C 触点判定条件**（≥ 2 项满足）：
1. 聚合 ≥ 2 字段（含 D 触点）
2. 有独立的渲染时机 / 更新触发条件
3. 跨平台有展示差异需要规范
4. 已封装为 spec / proj 组件（或计划封装）

**双标机制**（同一 UI 元素既是 C 又是 T 时，行业惯例分层标注）：
- 项目卡片（聚合 4 字段 + 点击进入详情）：
  - C 表：`C05 项目卡片`，关联字段 D01-D04，含"关联 T 触点"列指向 T05
  - T 表：`T05 点击卡片进入详情`，含"所属 C 触点"列指向 C05
- 关键：交互行为（Trigger）与信息呈现（Display/Container）是**两个独立维度**，**不在同一字段合并**

**反 pattern 实证**（下游 quotation-tool 历史）：
- "项目行"（聚合 4 字段 UI 块）被标为 T05（Trigger）→ T 语义不纯
- 应改为 C05（展示单元）+ 关联 T05（点击进入详情）双标

**机械兜底**：
- precheck `check_touchpoint_canonical`（S4-34 v2）正则 `[TD][NN]` → `[TDC][NN]` 升级
- C 判定条件启发式（≥ 2 项满足）启发式空间复杂，当期不实装独立 precheck（NB-WE-06 挂账，待 ≥ 2 仓 dry-run 实证后设计）
- 触发方式必须从以下标准词中选取，**不得自造词汇**：

| 触发方式 | 适用端口 |
|---------|---------|
| 点击 | 所有端 |
| 长按 | 移动端 |
| 下拉刷新 | 移动端 |
| 上滑加载 | 移动端 |
| 输入 / 清空 | 所有端 |
| 鼠标悬浮 | 桌面端 |
| 键盘 Tab | 桌面端 |
| 键盘 Enter / Space | 桌面端 |

---

### `[Must]` 触点容器级唯一性纪律（SSOT #64，2026-06-02 下游 D2 治本）

`[Must]` "交互元素" = **逻辑交互单元**（用户视角的 1 个可识别交互），**不是 DOM 元素粒度**：

| 模式 | 单元数 | 标注位置 | 同 ID 重复 |
|------|------|---------|-----------|
| chip group / radio / tab / button-group | **1 个逻辑交互**（多选项共享 callback/state） | 容器级标 1 次（不在每个选项重复） | 违规 → WARN |
| list / table 同模板多实例 | **N 个交互实例**（每行独立 callback/跳转） | 每实例标 N 次 | **合规多次**（spec §.3 触点表 1 行说明即可） |

**反 pattern 实证**（下游 quotation-tool M01-P01 desktop）：
- chip group 3 个选项每个标 `data-tp="M01-P01-T03"` → 同 ID 在 1 frame 内出现 3 次 → 违反容器级唯一性
- spec §.3 表 1 行 T03 描述 vs PRD 中 3 次 data-tp → 信息不对齐
- 视觉徽章 `<span class="tp-marker">03</span>` 在每选项重复显示 → 视觉污染

**合规写法**：

```html
<!-- ✅ chip group 容器级标（1 次） -->
<div class="chip-group" data-tp="M01-P01-T03">
  <span class="tp-marker">03</span>
  <button class="chip">全部</button>
  <button class="chip">进行中</button>
  <button class="chip">已完成</button>
</div>

<!-- ✅ list 多实例标（N 次，合规） -->
<ul class="fb-list">
  <li class="project-row" data-tp="M01-P01-C05">项目 A</li>
  <li class="project-row" data-tp="M01-P01-C05">项目 B</li>
  <li class="project-row" data-tp="M01-P01-C05">项目 C</li>
</ul>
```

**判定依据**：子选项**共享一个 callback / state** → 1 个交互单元（容器级标）；每行**独立 callback / 跳转** → N 个交互实例（每实例标）。

**机械兜底**：`precheck_stage4.check_prd_data_tp_container_uniqueness` S4-43 v1（扫每 *-frame 内同 data-tp 重复出现 → WARN，dry-run 阶段；list/table 豁免判定由 PM/Sup 人审上下文）。详见 `rule_hard_constraints.md §S4-43`。

**Why（治"跨产品 PM 各自发挥"根因）**：
- S4-24 强制"每交互元素标 data-tp" — 没说清"什么算交互元素"
- PM 无据可依 → 各自发挥 → chip group / radio / tab 自由发挥重复标
- 本纪律明确"交互元素 = 逻辑交互单元"，与 S4-24 协同（非冲突）

---

## 五、`[Must]` 页面内状态枚举规则（全局规则）

> **术语限定**：本节「状态」专指**页面内 UI 状态**（empty / loading / error / success / disabled / default 等显示态）;与 `process_record/state.md` 中「阶段流程状态」（⏳进行中 / 🟡待审 / ✅已通过 等阶段推进态）属不同概念,不要混淆（SSOT 双锚 #23）。

每个页面的页面内状态必须在状态枚举表中穷举，格式：

```
[S01] 默认态（有数据）— 触发前提：接口返回非空数据，与 S02/S03 互斥
[S02] 空态            — 触发前提：接口返回空数据，与 S01/S03 互斥
[S03] 加载失败态      — 触发前提：接口超时或网络错误，与 S01/S02 互斥
```

**强制规则**：
- 每个状态 ID 对应一个且仅一个视觉帧，不得跳过、不得多出
- 「是否互斥」必须明确标注；互斥状态不得在同一帧中共存
- **叠加态**（弹窗/抽屉/Toast 覆盖在主页面上）不单独占状态表一行，在触发它的主状态行备注说明
- **瞬态**（骨架屏、短暂 Toast）可在注释中说明，不强制单独成帧
- 禁用态须在对应状态帧中明确展示，不得仅靠文字描述
- 同一页面多个状态帧须展示**完全一致的字段集合**，不得因状态不同而省略字段

---

## 六、`[Must]` 必须覆盖的状态清单

PM Agent 对产品定义中每个功能，必须生成以下状态（功能无关则跳过）：

| 状态类型 | 必须生成 | 说明 |
|---------|---------|------|
| 默认 / 初始态 | ✅ | 用户进入页面时的初始状态 |
| 空状态 | ✅ | 列表无数据、搜索无结果 |
| 加载态（骨架屏） | ✅ | 接口 > 300ms 未返回 |
| 填写中 / 交互中 | ✅ | 表单有内容，按钮激活 |
| 成功态 | ✅ | 操作成功反馈 |
| 字段错误态 | ✅ | 校验失败，红色提示 |
| 网络错误态 | ✅ | 接口失败，重试入口 |
| 禁用态 | ✅ | 无权限或条件不满足 |
| 越权提示态 | ✅（有权限矩阵时） | 403 场景 |
| 确认弹窗态 | ✅（有不可逆操作时） | 删除、放弃编辑等 |
| 角色差异态 | ✅（有多角色时） | 不同角色看到不同操作项 |

---

## 七、文件命名规范

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 产出 A（人类版） | `prd_[产品名]_latest.html` | `prd_报价工具_latest.html` |
| 产出 B（AI 版） | `spec_[产品名]_latest.md` | `spec_报价工具_latest.md` |

两份文件统一输出到 `outputs/` 目录，无子目录。

**多端产品**：产品涉及多个端口时，两份文档均在同一文件中覆盖所有端口，通过平台标签区分帧（如 `P-03 报价列表 [手机] / P-03 报价列表 [桌面]`）。

**跨平台页面编号规则**：
- 页面编号在产品定义页面路由表中统一定义，各端共用同一套编号体系
- 同一页面在不同端均有帧时，使用相同编号，在页面标题行后用平台标签区分
- 仅存在于某一端的页面，照常分配编号，在页面清单「访问权限」列注明端口限制

---

## 八、变更与版本管理

- 交付文档版本号与产品定义版本号对应，产品定义更新时交付文档须同步更新
- 每次更新在 spec.md 文档头部记录变更内容（变更页面、变更原因、变更人）
- 历史版本归档至：
  ```
  process_record/versions/deliverable_v[版本]_[日期]/
    ├── prd.html
    └── spec.md
  ```

---

## 九、`[Should]` 触控尺寸规范（移动端）

依据 Apple HIG、Google Material Design 及 WCAG 2.5.8 标准。

| 组件类型 | 最小尺寸 | 说明 |
|---------|---------|------|
| 主/次/危险按钮 | 44×44px | 点击区域（视觉可小于此值） |
| 列表行 | 高度 ≥ 52px | 整行可点击 |
| 图标按钮 | 44×44px | 外层透明点击区达标即可 |
| 步进器按钮（±） | 36×36px（最低） | 步进器整体宽度 ≥ 120px |
| Tab 标签项 | 高度 ≥ 44px | 宽度不限 |
| 底部操作栏 | 高度 ≥ 52px | 含底部安全区 padding |
| 表单字段行 | 高度 ≥ 48px | 含 label + input |
| 表单输入框 | 44px | 独立输入框高度 |
| 导航栏 | 44px（含 Dynamic Island 区域 59px，总计 103px；iPhone 17 Pro Max 基准） | — |

`[Should]` **相邻元素间距**：相邻可点击元素 ≥ 8px；同行多个操作按钮 ≥ 8px；列表行内右侧操作区与主内容 ≥ 16px

`[Should]` **密度控制**：单屏可见主要操作入口不超过 3 个（不含导航栏）；次要操作收入「···」菜单或底部抽屉

---

## 十、`[Must]` 导航组件槽位契约

导航组件使用**三槽位模型**，三个槽位在 HTML 中**必须始终存在**。

### NavBar（顶部导航栏）

```
┌──────────────────────────────────────────────┐
│  [左槽位]      [中槽位·标题]      [右槽位]     │
│  min-width     flex:1            min-width    │
└──────────────────────────────────────────────┘
```

| 槽位 | 内容规则 | 占位规则 |
|------|---------|---------|
| 左槽位 | 有返回时：`‹ 返回` 按钮；有关闭时：`✕` 按钮 | **无内容时必须放置等宽空白占位块** |
| 中槽位 | 当前页面名称，居中显示 | 始终存在 |
| 右槽位 | 操作按钮；多个操作时横向排列；多语言产品须在右槽位最右侧放置语言切换器 | **无内容时必须放置等宽空白占位块** |

`[Should]` 槽位对称原则：左右槽位保留宽度必须相等（同为 60px 或按实际按钮宽度对齐）。

`[Should]` 操作入口唯一性原则：同一操作在同一页面内只有一个入口，避免重复。

### BottomBar（底部操作栏）

- `[Should]` 主操作按钮统一放置于 BottomBar，不得放置于内容区标题行内
- 同一页面的不同状态帧，BottomBar 内的按钮集合须保持一致
- 若某状态下 BottomBar 整体不可操作，以 `opacity: 0.4 + pointer-events: none` 表示禁用

---

## 十一、`[Should]` 交互完整性标准

### 按钮导航覆盖率

原则上所有可交互元素均须绑定 onclick 跳转逻辑。以下情形可例外：① 明确处于禁用态；② 标注为「待后续迭代实现」的占位功能入口。

**高优先级必覆盖清单**：

| 元素类型 | 跳转要求 |
|---------|---------|
| ··· 更多按钮 | → 对应更多菜单叠加态 |
| 导出按钮 | → 导出确认/成功态 |
| 列表项（卡片/行） | → 对应详情页默认态 |
| 底部操作栏全部按钮 | → 对应目标帧 |

### `[Must]` 页面跳转实现规范

所有触点卡片「跳转」字段不为空的交互元素，**必须**在 HTML 中绑定 onclick 调用 `showSection()`：

```html
<button onclick="showSection('H-M01-P02-default')">下一步</button>
<div class="list-item" onclick="showSection('H-M01-P03-default')">列表项</div>
```

- 禁止跳转字段有值但 onclick 为空、写 `javascript:void(0)` 或不写
- 导航侧栏每个条目同样须调用 `showSection()`
- 跳转目标 ID 格式：`H-M[XX]-P[XX]-[状态名]`（与 `gen_scaffold.py` 输出的 `prd_id` 一致），必须与实际 `<section id="...">` 保持一致

### `[Should]` 光标样式

所有 phone-frame 内可点击元素须添加 `cursor: pointer`。推荐在全局 CSS 中使用通配选择器统一覆盖（已内置于 `prd_template.html`）。

### `[Must]` prd.html 中 Mermaid 局部豁免规则

prd.html 中**默认禁止出现 Mermaid 代码块**（` ```mermaid ` / `<pre class="mermaid">` / `<div class="mermaid">`）。理由：浏览器无法原生渲染 Mermaid，过往让 PM 用 mermaid 替代真正的页面线框图（prototype）会破坏文档的"可点击高保真原型"定位。

**`[Must]` 豁免场景（白名单，仅以下三类 section 允许 mermaid）**：

| 豁免类别 | section id 必须含的关键字（不区分大小写）| 用途 | SSOT 来源 |
|---------|--------------------------------|------|----------|
| 用户旅程可视化 | `journey` / `user-journey` | A-04 用户旅程的「流程图视图」（多角色泳道 / 单角色横向流程） | 阶段 3 产品定义 §5（旅程步骤表 + 多角色参与矩阵）|
| 业务流程图 | `flow` | 规格区附属的业务流程图 / 状态流转图（如 `spec-business-flow`、`spec-state-flow`）| **阶段 2 功能规划 §二**（详见 `tmpl_功能规划.md §二`）；spec.md §3.4 + **PRD A-04.2** 双侧渲染（双视图 + 多角色 subgraph 泳道,工程视角,与 A-04 用户旅程互补）|
| 页面架构总览 | `sitemap` | `spec-sitemap`「页面架构总览」colocate 的两类 mermaid：①页面层级架构图（产品根→模块→页面，提议1，**布局 `graph LR` + 模块 subgraph 内 `direction TB`**——2026-05-25 WE-LRTB 治本同级横排痛点）②模块依赖图 `graph TB`（提议3，Item 3 方向 LR→TB，2026-05-18 3dd28b8）| **`scaffold.json modules[]`/`pages[]`**（SSOT 双锚 **#38** 页面层级 / **#40** 模块架构）；`assemble.build_hierarchy_mermaid` / `build_module_arch_*` 现场派生注入 spec §3.0 + PRD spec-sitemap。**同族对称硬约束**：`rule_hard_constraints.md S4-29`/`S4-31` **强制该 section 必含 mermaid**，故本白名单**必须**含 `sitemap`（强制含 ⇔ check_prd 局部豁免必豁免；缺则两检查互斥死锁，agent_methodology §七.2）|

**豁免范围内 mermaid 用法仍受以下约束**：

1. **`[Must]` SSOT 派生约束**：
   - 用户旅程可视化的 mermaid 源码必须由阶段 3 产品定义的结构化数据派生（旅程步骤表 + 多角色参与矩阵），**禁止 PM 在阶段 4 凭空写 mermaid 源码**。详见 `prd_expression_standard.md §A-04 用户旅程 / 用户旅程可视化` 小节。
   - 业务流程图的 mermaid 源码必须由阶段 2 §二 直接迁入（含 2.1 主流程 / 2.2 跨角色交互 / 2.3 补充流程全部子节），调整方向为"先改阶段 2 §二 → 再重拼装"，禁止反向。详见 `pm-workflow/rules/proto_spec_md.md §3.4` + `pm-workflow/rules/tmpl_功能规划.md §二`。
   - 页面架构总览的 mermaid 源码必须由 `assemble.build_hierarchy_mermaid` / `build_module_arch_*` 从 `scaffold.json` 现场派生（提议1/3，SSOT #38/#40），**禁止 Foundation / PM 凭空写或反向手改 outputs**；调整方向"先改 scaffold → 重跑 `assemble.py spec`+`prd`"，禁止反向。详见 `pm-workflow/rules/proto_spec_md.md §3.0` + `rule_hard_constraints.md S4-29/S4-31`。
2. **`[Must]` 与表格视图共存**（仅适用「用户旅程可视化」「业务流程图」两类）：该两类豁免须同时提供「表格视图」与「流程图视图」，通过 toggle 切换；不允许只给 mermaid 无表格回退（断网时表格仍可读）。**「页面架构总览」不适用本条**——其结构化伴随是同 section 内 colocate 注入的「页面结构范式契约」表（SSOT #39）与「模块架构说明」表（SSOT #40），与层级/依赖 mermaid 互补共存而非 toggle；sitemap 为静态结构概览，无断网交互回退需求。
3. **`[Must]` CDN 引入**：mermaid 渲染依赖 `https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js`，主模板已含此 script 标签 + initialize 调用，模块 PRD Agent 不重复引入。
4. **`[Must]` mermaid 块所属 section 校验**：精确机械检查由 `precheck_stage4.py` 兜底——出现在豁免关键字以外 section 中的 mermaid 块均报 FAIL。
5. **`[Must]` 检测域 = 仅 DOM，剥 `<script>`/注释域（同族对称硬化）**：本校验仅针对**真实 mermaid DOM 节点**。`check_prd` 扫描前经 `_blank_mermaid_scan_noise` 等长留白 `<script>...</script>` 与 `<!-- ... -->`——mermaid 渲染 JS（`renderStaticMermaid` / `switchJourneyView` 等）的**注释或选择器**合法地含字面 ` ```mermaid ` / `<pre class="mermaid">`，且经 `assemble._overwrite_scripts_from_template`（SSOT #2 派生5）进 `outputs/prd` 的 `<script>`；此类字面**不是**违规（真 mermaid DOM 结构上永不在 JS 文本域 / 注释域内，留白零假阴性）。下游 Supervisor NB-L2-SITEMAP-RENDER-FP 教训：触发源（渲染 JS 含字面）加了、检测器须同族对称剥噪声域（agent_methodology §七.2，与 9e1a405 同型）。

**非豁免场景（默认禁用）的替代方案**：

| 原 Mermaid 图类型 | HTML/CSS 替代方式 |
|-----------------|----------------|
| 流程图（flowchart）| 用 `<div>` + flexbox/grid 绘制方框与箭头 |
| 时序图（sequenceDiagram）| 用有序列表或表格按步骤列出 |
| 状态图（stateDiagram）| 用表格列出状态与转移条件 |

> Mermaid 在 `spec.md` 中始终允许（spec 面向 AI 消费方，无渲染问题）。
> 非豁免 section 中出现 mermaid → 视为违反本条 `[Must]`，precheck 报 FAIL，Supervisor 必须打回整改。

---

## 十二、`[Should]` 通用组件视觉规范

### Toast 提示

位置：**移动端在屏幕底部居中**，距底部操作栏上方 12px；**桌面端在屏幕左下角**，距左 24px、距底 24px

```
成功：  ╔══════════════════════╗  左边线 var(--fb-text-secondary)，白底，持续 2 秒
        ║ ✓  操作成功提示文字  ║
        ╚══════════════════════╝

警告：  ╔══════════════════════╗  左边线 var(--fb-text-secondary)，持续 3 秒
        ║ ⚠  警告提示文字      ║
        ╚══════════════════════╝

错误：  ╔══════════════════════╗  左边线 var(--fb-error)，持续 3 秒
        ║ ✕  操作失败提示文字  ║
        ╚══════════════════════╝

含操作：╔════════════════════════════╗  左边线 var(--fb-text-primary)，持续 4 秒
        ║ ℹ  提示文字       [撤销]  ║
        ╚════════════════════════════╝
```

多条 Toast 叠加时：新 Toast 替换旧 Toast，不堆叠显示。

### 弹窗（Modal）

```
        ┌──────────────────────────────┐  圆角 8px，悬浮框阴影
        │ 弹窗标题（16px Medium）       │
        │──────────────────────────────│
        │ 内容描述文字（14px，var(--fb-text-secondary)） │  背景遮罩 var(--fb-overlay)
        │                              │
        │   [取消（次按钮）]  [确认]   │  按钮区域左右 padding 16px
        └──────────────────────────────┘
```

不可逆操作弹窗：点击背景遮罩无响应，必须通过按钮操作关闭。

### `[Must]` 语言切换器（多语言产品必须实现）

**触发条件**：产品定义中标注支持多语言时，原型必须包含可工作的语言切换器。

**视觉规格**

```
移动端（NavBar 右槽位）：
  [ 中 | EN ]    胶囊形，当前语言高亮（深色底白字），另一语言灰色底；高度 28px，圆角 100px；字号 12px

桌面端（顶部右侧固定区）：
  [ 中文  ▾ ]    下拉触发器，宽 72px，高 32px，圆角 8px，边框 var(--fb-border-2)；展开后每项高 36px，当前语言前加 ✓
```

**JS 实现规范**（使用 `data-lang` 属性驱动，无需引入 i18n 库）：

```html
<body data-lang="zh">
<span data-zh="项目名称" data-en="Project Name"></span>

<script>
function switchLang(lang) {
  document.body.setAttribute('data-lang', lang);
  document.querySelectorAll('[data-zh]').forEach(el => {
    el.textContent = lang === 'zh' ? el.dataset.zh : el.dataset.en;
  });
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.target === lang);
  });
}
</script>
```

**覆盖要求**：所有对外展示的文字节点均须添加 `data-zh` / `data-en` 属性；纯内部系统管理页面可豁免多语言。

### 列表与分页

| 模式 | 适用端口 | 触发条件 | 视觉反馈 |
|------|---------|---------|---------|
| 下拉刷新 | 移动端 | 列表处于顶部，继续下拉 ≥ 64px | 顶部指示区（高 44px），图标旋转；完成后淡出 |
| 上滑加载更多 | 移动端 | 滚动至底部距离 ≤ 200px 时预加载 | 底部「加载中」行；无更多数据时显示「已显示全部 X 条」 |
| 分页控件 | 桌面端 | — | 分页控件置于列表底部右侧，含上/下页、页码、每页条数选择器 |

---

## 十三、`[Optional]` 深色模式声明

默认：本规范产出**仅覆盖浅色模式**。

例外：若产品定义明确写明「需支持深色模式」，在浅色模式全部完成并通过审核后追加深色帧。深色模式使用不觉黑板主题 Token，在 `:root` 中覆盖对应 CSS 变量：

```css
[data-theme="dark"] {
  --fb-text-primary:   rgba(255, 255, 255, 0.85);
  --fb-text-secondary: rgba(255, 255, 255, 0.65);
  --fb-text-hint:      rgba(255, 255, 255, 0.45);
  --fb-text-disabled:  rgba(255, 255, 255, 0.25);
  --fb-border-1:       rgba(255, 255, 255, 0.15);
  --fb-border-2:       rgba(255, 255, 255, 0.15);
  --fb-white:          #151515;
  --fb-bg-1:           #000000;
  --fb-bg-2:           #151515;
  --fb-bg-3:           #2a2a2a;
  --fb-bg-4:           #454545;
  --fb-nav-bg:         rgba(0, 0, 0, 0.3);
}
```

深色帧紧跟对应页面浅色帧之后，标题标注「[深色模式]」；交互逻辑与浅色模式完全一致，不单独建立状态枚举表。

---

## 十四、`[Must]` UX 守则

生成每个页面帧前逐条检查：

**1 — 语义优先**：时间/日期范围属"筛选条件"，必须作为独立筛选入口，不得与状态胶囊同形同权；下拉图标仅用于展开更多选项。

**2 — 操作入口统一**：列表行内禁止放主操作按钮；主操作统一在底部固定操作栏，对当前选中项生效；有"选择"逻辑时明确单选/多选。

**3 — 极简线条**：同一区域仅允许一种分隔方式（卡片间距 或 分割线），禁止叠加；优先"留白+轻阴影"。

**4 — 作用域隔离**：所有样式限定在页面作用域容器，禁止全局覆盖。

---

## 十五、`[Must]` 视觉自检清单（全部 H 步骤完成后逐项执行）

**布局**
- [ ] 信息层级与业务语义一致；组件基线对齐无偏移
- [ ] 模块内留白 ≥ 8px，模块间 ≥ 16px
- [ ] 主操作已从列表行内移除，统一到底部固定操作栏

**色彩与对比**
- [ ] 100% 使用 `--fb-*` CSS 变量，无散值 Hex 硬编码
- [ ] 文本对比度 ≥ 4.5:1；核心操作视觉突出

**资源与图标**
- [ ] 无字符占位图标（`●▼✕←›` 等已替换为 iconfont/SVG）
- [ ] 无双 icon（伪元素注入 + 自定义图标叠加）
- [ ] 空态使用 `pm-workflow/rules/bujue-design-system/icon/NoData_LightMode.svg`
- [ ] 加载动画符合 uiverse 规范

**交互语义**
- [ ] 时间筛选为独立筛选入口，非普通胶囊
- [ ] 无多余分割线/描边叠加

**组件父容器几何契约（建议 10 / issue # 11/# 15/# 16 复盘根因 I）**
- [ ] `[Must]` 凡组件 CSS 含 `position: absolute / sticky / fixed` 子元素 / 伪元素的，已按 `prd_expression_standard.md §零.3 组件父容器几何契约` 在 CSS 块顶部注释声明父容器约束（position / overflow / width/height 三项）
- [ ] `[Must]` 父容器为 `overflow: auto / scroll` + 子元素含越界 transform（如 `translateX(-30%→130%)`）的组合**禁止**出现（触发滚动条闪烁循环，参 issue # 15 根因 A/B）— 改用 `overflow: hidden` 或改 transform 为 in-bounds 写法
- [ ] `[Must]` `.fb-modal-overlay` / `.fb-drawer-overlay` / `.fb-toast` 等 `position: absolute; inset: 0` 元素的父容器（h5-frame / phone-frame / desktop-frame / tablet-frame / miniprogram-frame / 任何自定义 frame）必须含 `position: relative`（参 §零.2 三大支柱 1.b 与 §零.3 反例 vs 正例表）
