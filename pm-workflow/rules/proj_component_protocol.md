# proj_component_protocol.md — PM 创建项目级组件的协议

> **本文件定位**：当 PM Agent 在阶段 4 识别到「跨模块复用、字段 schema 锁定」的项目内组件时，按本协议创建 `proj.*` 组件。本协议覆盖 schema 声明、状态枚举强制清单、PRD 可视化要求（中保真）、CSS 抽象纪律、HTML 标记规范，以及配套硬规则与 precheck 验证规则。
>
> **PM 边界澄清**：
> - **pub 组件库**（`pub.L0–L4`）由设计/前端团队外部维护，PM 工作流**只读消费**
> - **proj 组件**由 PM 在阶段 4 设计，**不实现为生产代码**（无 React 组件、无 Vue SFC），但**必须在 PRD 中以中保真方式可视化**呈现各状态
> - 下游开发团队接收 PRD 中的视觉合同 + spec 中的结构化字段定义，自行落地为正式可复用组件

---

## 一、何时新建 proj 组件

PM Agent 在阶段 4 Step 2.5（项目组件识别）扫描产品定义 + 各模块任务卡，按以下**双触发因素**判定。**任一成立**即触发新建 proj 组件。

> **判定前置**：开工本判定前**必须先**读 `pm-workflow/rules/bujue-design-system/pub_components_index.md`（pub 组件索引）—— A 触发的"pub slot 化模板不能覆盖" / B 触发的"能力缺口"都需以 pub 索引为参照系。绕开 pub 索引直接派生 proj 视为违反硬规则 S4-19。

### 触发因素 A — 跨模块复用

同时满足以下三条：

1. **跨模块出现**：同类组件在 ≥ 2 个模块（不是同一模块内多次）出现
2. **字段一致**：字段集合在多处出现时保持一致（包括字段名 / 类型 / 业务语义）
3. **pub slot 化模板不能直接覆盖**：必须有项目特有的字段或语义

**典型场景：** 产品卡片在「商品列表页 / 商品详情页推荐区 / 购物车关联推荐」3 处复用，字段一致（产品图 / 名称 / 价格 / 库存 / 加购按钮），但 pub.L2.card 的通用 slot 不足以承载"价格 + 库存标签 + 加购按钮"复合信息——派生 `proj.L2.product-card`。

### 触发因素 B — 能力缺口（即使单模块也可触发）

pub 库已有同类基础组件，但其能力不足以覆盖本次业务需求。**用以下 5 维清单逐项判定**，任一不通过即视为能力缺口：

| 维度 | 判定标准（必须**全部满足**才算覆盖） | 不通过即触发 B 派生 |
|------|------------------------------------|-------------------|
| **D1 字段 / 槽** | 业务需要的每个数据字段都能在组件 slot 中放下，slot 数量与槽语义匹配 | fb-card 仅 4 个 slot，业务需要 5 个独立可视字段 |
| **D2 状态** | 业务定义的所有状态都能由组件 modifier 表达 | 业务有"售罄"全卡灰色 + 遮罩 + 售罄文字徽章，fb-card 无对应 modifier |
| **D3 交互** | 业务定义的所有用户动作都被组件支持 | 业务需要"长按拖动重排"，fb-list-item 不提供 drag handle |
| **D4 语义** | 组件命名与业务语义一致（即使视觉对得上） | 业务是"删除"，PM 用 `.fb-btn-primary` 视觉对得上但语义错——必须 `.fb-btn-danger` |
| **D5 约束** | 字段约束（必填/长度/格式/范围/枚举）能在组件层显式表达 | 必填字段 PM 用 `.fb-label`（应用 `.fb-label-required`）；错误态未加 `.is-error` modifier |

**Supervisor 与 PM 共用同一把尺子**：本清单同时是 Supervisor §4.4 阶段4 审核「组件能力覆盖业务需求」P0 项的判定 SOP。

**典型场景：**

| 场景 | 不通过的维度 | 派生方向 |
|------|-------------|---------|
| pub 提供 `.fb-textarea`，业务需要"富文本编辑 + 表情 + @提及" | D3 交互缺口 | proj.L1.rich-textarea |
| pub 提供 `.fb-card`，业务需要"含倒计时 + 抢购状态 + 售罄遮罩"的促销卡片 | D2 状态缺口 + D1 字段缺口 | proj.L2.flash-sale-card |
| pub 提供 `.fb-list-item`，业务需要"含拖拽 + 多选" | D3 交互缺口 | proj.L2.editable-list-item |
| 业务"产品卡片"含 5 个固定字段（图/名/价格/库存标签/加购按钮）| D1 字段缺口（slot 不够） | proj.L2.product-card |

### 优先级与互斥

- 若**同时满足 A+B**：按 A 处理（跨模块复用价值更高，命名沿用 A 触发的语义）
- 若**仅 A 不满足 B**（pub 能完全覆盖但仅跨模块共享）：**不需要新建 proj**，直接在多个模块用同一 `fb-*` class，由 fallback CSS 提供视觉
- 若**仅 B 不满足 A**（单模块能力缺口）：**仍需新建 proj**——能力缺口必须显式声明给下游开发团队
- **A、B 都不满足** → 不新建 proj，使用 pub 组件 + slot 填充

### 判定结果三种情况

| 判定结论 | 处理方式 |
|---------|---------|
| 触发 A 或 B 任一 | 按本协议 §二 起声明 schema、§三 枚举状态、§四 在 PRD 可视化 |
| 都不触发 | `outputs/components_[产品名]_latest.md` 仍须保留 §二.1 索引段 4 张表（A/B/C/D）的表头 + 表内写"本期无 proj 组件"，不得省略段落框架 |
| 不确定 | 按 NB 上报产品总监决策，不擅自硬造 |

---

## 二、文件结构（写入 `outputs/components_[产品名]_latest.md`）

`components_[产品名]_latest.md` 由两部分构成，**顺序不可颠倒**：

```
1. 顶部索引段（必填，§二.1）— 全部 proj 组件的快速检索表
2. 详情段（每组件一段，§二.2）— 每个 proj 组件的完整 schema 声明
```

PM 在阶段 4 派发各模块 PRD Agent / Spec Agent 时，subagent 收到本文件路径后**先**读索引段定位本模块用到的 proj 组件 id，**再**精读对应详情段，避免每次都全文扫描。

---

### 二.1 索引段（必填，置于文件顶部）

索引段含 4 张表（A / B / C / D），即使本期无 proj 组件也必须保留段落框架（仅写"本期无新建 proj 组件"作为兜底说明）。

#### `[Must]` 表格 ID 字面规则（A/B/C/D 4 张表 + 详情段 changelog 共用）

- **本节及详情段所有表格的 `proj.L*.*` ID 一律裸写**（不加反引号包裹）
- **narrative 段落内的 inline 引用** 仍按 markdown 习惯用反引号（如 "PM 派生 \`proj.L2.product-card\`"），**仅**表格首列 / 替代组件列 / 模块列 / changelog 表内禁用反引号
- **理由**：
  1. 表格 ID 与 YAML `- id:` / scaffold.json `"id"` / HTML `data-component-id="..."` 共享同一字面源，全栈裸 → 跨载体对账（precheck `extra_in_detail` / `missing_in_detail` set 比对）零成本
  2. precheck 行首锚定 regex `^\|\s*<id>\s*\|` 用 pipe 边界消歧,反引号会导致**静默漏检**（regex 不匹配反引号包裹形式 → 表内一半行被跳过却不报错）
  3. 混用→fail loud：表格内一旦出现反引号包裹形式,precheck 会显式 fail 而非沉默剔除（参 `precheck_stage4.check_components_index_consistency` 反引号 fail loud check）
- **何时适用**：A / B / C / D 4 张表的所有列；详情段中的 changelog 表（如各 proj 组件的版本变更记录）；spec.md §八 组件变更清单 4 张子表（新增 / 修改 / 弃用 / 升级建议）

#### A. active 组件（可直接引用）

| id | 模块 | owner | 业务语义 | 派生原因 | 详情段锚点 |
|----|------|-------|---------|---------|----------|
| proj.L{tier}.{name} | M01/M02 | M01 | 一句话语义 | A 跨模块复用 / B 能力缺口（具体说明缺什么）/ A+B | [#proj-{name}](#proj-{name}) |

**字段约束：**
- `派生原因` 必填，必须以 `A` / `B` / `A+B` 开头（对应 §一 双触发因素）；后接简短说明
- `详情段锚点` 必须指向本文件下方实际存在的 `## proj.L{tier}.{name}` 详情段
- 同一 id 不得在 A 和 B/C 表中同时出现
- **`owner` 必填**，标识"首批使用模块"——所有跨模块共用本组件时，由该模块负责写完整 PROJ-CSS 与独立状态展示区，其他模块仅引用 class
  - **唯一权威源**：`scaffold.modules[].owner_assignments`（PM 子阶段一推算并写入；详见 `pm-workflow/rules/agent_dispatch_protocol.md`「owner 流转链路」）
  - **数据来源**：本表 owner 列由 PM 子阶段二.5 **直接从 scaffold.owner_assignments 读取**抄入，**禁止重算**（v2.0 [Must] 不重做评估约束）
  - **算法定义**（仅 **PM 子阶段一计算阶段** 适用，其他角色一律从 owner_assignments 读）：owner = `scaffold.json` `modules[]` 数组中**顺序最靠前**的引用本组件的模块 id（即"模块"列中按 scaffold 顺序的第一个）
  - 与派发顺序、依赖图（depends_on）无关；即使 owner 模块在 Step 3/5 是后派发的，仍由它负责写 CSS
  - precheck 强制校验（兜底防漂移）：A 表 `owner` ∈ A 表「模块」列；A 表 `owner` 必须等于按 scaffold modules 顺序计算的最靠前者（即与 owner_assignments 一致）；草稿 PROJ-CSS 块归属与 owner 一致

#### B. deprecated 组件（保留不删，禁止新引用）

| id | 弃用原因 | 替代组件 | 弃用日期 |
|----|---------|---------|---------|
| proj.L{tier}.old-name-v1 | 字段不足以表达多规格 | proj.L{tier}.new-name | YYYY-MM-DD |

**字段约束：**
- `替代组件` 必填，且其 id 必须存在于 A 表（active 状态），否则 precheck 报错
- 弃用条目的详情段**必须保留**（不删），但段落开头加 `> ⚠ 已弃用，改用 [proj.L{tier}.new-name](#proj-new-name)` 引导线

#### C. proposed-promote 组件（建议升级为 pub）

| id | 推荐理由 | 提议日期 |
|----|---------|---------|
| proj.L{tier}.{name} | 已在 N 个产品复用 / 通用度高 | YYYY-MM-DD |

**说明：** C 表是 proj→pub 反馈池，由 PM 在判断"本组件在 ≥3 个产品复现 + 字段稳定"时填入；工作流维护者定期审视、决定是否真正升 pub。

#### D. 按模块反查（哪些 proj 组件被哪些模块使用）

| 模块 | 引用的 proj 组件 |
|------|----------------|
| M01 [模块名] | proj.L{tier}.{name1} |
| M02 [模块名] | proj.L{tier}.{name2} / proj.L{tier}.{name1} |

**字段约束：**
- `模块` 列必须与 `process_record/tasks/scaffold.json` 中的模块清单完全一致（编号 + 名称）
- `引用的 proj 组件` 必须存在于 A 表（active），不允许引用 deprecated 或不存在的 id
- 用途：PM 做某个模块的 spec/prd 时，**先**看本表确认本模块复用了哪些 proj，避免重复派生

#### 索引段示例

```markdown
## 索引段

### A. active 组件
| id | 模块 | owner | 业务语义 | 派生原因 | 详情段锚点 |
| proj.L3.product-card | M02/M03 | M02 | 商品卡片 | A 跨模块复用 + B 通用 fb-card 字段不足以表达规格 / 库存 | [#proj-product-card](#proj-product-card) |
| proj.L3.spec-selector | M02 | M02 | 规格多选 | B pub 无 tag-multi-select 组件 | [#proj-spec-selector](#proj-spec-selector) |

### B. deprecated 组件
（本期无）

### C. proposed-promote 组件
| id | 推荐理由 | 提议日期 |
| proj.L3.spec-selector | 选规格场景通用，建议升 pub.L3.tag-multi-select | 2026-04-27 |

### D. 按模块反查
| 模块 | 引用的 proj 组件 |
| M02 商品列表 | proj.L3.product-card / proj.L3.spec-selector |
| M03 商品详情 | proj.L3.product-card |
```

---

### 二.2 详情段 Schema 声明（每个 proj 组件按此声明）

每个 proj 组件按以下 YAML 结构声明：

```yaml
- id: proj.L{tier}.{name}              # 必填，命名见 §六.1
  inherits: pub.L{tier}.{name}         # 必填，基于哪个 pub 组件派生
  modules: [M01, M02, ...]             # 必填，使用本组件的模块列表
  purpose: 一句话用途                     # 必填

  # —— [Must] 业务语义三段 — 后续开发构建组件时的需求依据 ——
  boundary:                            # 必填，功能边界
    applicable_when:                   # 必填,≥ 2 个适用场景
      - "用户列表展示商品时（含主图 + 标题 + 价格 + 操作按钮）"
      - "搜索结果页商品卡片"
    not_applicable_when:               # 必填,≥ 1 个不适用场景
      - "纯文本展示（应用 pub.L0.text-only-card）"
    differs_from:                      # 必填,与同类组件的区分边界
      pub.L2.card: "本组件 5 slot,pub.L2.card 仅 4 slot,无价格槽"

  usage:                               # 必填，用途说明
    business_scenarios:                # 必填,≥ 2 个业务场景示例
      - "电商列表页 - 用户浏览决策"
      - "商家后台商品管理列表"
    modules:                           # 必填,描述哪些模块用本组件 + 各自用途
      M02 商品列表页: "主列表展示"
      M03 搜索结果页: "搜索结果展示"
    pain_point: "本产品需在列表中同时展示价格 + 库存 + 收藏数,pub.L2.card 4 slot 不够"  # 必填,解决的具体痛点

  interaction:                         # 必填，交互说明
    user_flow: "用户滑动浏览 → 点击卡片进详情 / 点击右上角心形收藏 / 点击购物车图标加购"  # 必填,用户操作流程
    collaborates_with:                 # 必填,与本组件协作的其他组件清单
      - fb-btn-primary                 # 卡片底部主操作按钮
      - proj.L1.price-tag              # 价格槽内嵌组件
      - fb-toast-success               # 收藏成功反馈

  # —— 视觉规范层（既有字段保留）——
  slots:                               # 必填，槽定义
    - {slot_name}: 
        required: true/false
        type: image / text / list / ...
        source: spec §X.{字段名}        # 数据来源指向 spec
        max?: <最大长度/数量>
        min?: <最小长度/数量>

  states:                              # 必填，按 §三 9 项清单逐条判定
    required: [default]
    applicable:
      - hover:    {needed: yes/no, reason}
      - active:   {needed: yes/no, reason}
      - disabled: {needed: yes/no, reason}
      - loading:  {needed: yes/no, reason}
      - error:    {needed: yes/no, reason}
      - empty:    {needed: yes/no, reason}
      - selected: {needed: yes/no, reason}
      - focused:  {needed: yes/no, reason}

  state_transitions:                   # 必填，状态间转移规则
    - default → loading → default
    - loading → error
    - default ↔ hover

  field_schema:                        # 必填，每字段含类型 + 约束
    - {field_name}: 
        type: string / integer / enum / url / ...
        max?: ...
        enum?: [...]
        source: spec §X.{字段名}
```

**`[Must]` 业务语义三段填写要求**：

`boundary / usage / interaction` 是后续开发构建组件时的需求依据,缺一段会让开发猜业务意图、反复回查产品定义 §7。与既有视觉规范层（slots / states / state_transitions / field_schema）正交互补——前者解决"为什么 / 在哪用 / 怎么用"业务语义,后者解决"长什么样 / 有什么状态 / 数据怎么进"工程实现。

填写纪律：
- **boundary** 强调"边界"——明示**不适用场景**比明示适用场景更重要,避免组件被滥用
- **usage 与既有 modules 字段不重复**——modules 是"哪些模块引用本组件"的扁平清单,usage.modules 是"在每个模块内承担什么具体角色"的语义层
- **interaction 与 state_transitions 不重复**——state_transitions 是状态机（系统视角）,interaction.user_flow 是用户操作流程（人类视角）;collaborates_with 列出本组件与其他组件的协作关系（如本卡片底部用 fb-btn-primary,价格槽内嵌 proj.L1.price-tag）
- 缺任一段 → `precheck_stage4.py check_proj_components` 自动 FAIL（机械兜底）

---

## 三、状态枚举强制清单

新增 proj 组件时，`states.applicable` **必须**对以下 8 项**逐条**判定（`default` 强制存在不需判定，共 8 项需声明）：

| 状态 | 含义 | 适用场景 |
|------|------|---------|
| `hover` | 鼠标悬停反馈 | 桌面端可交互组件 |
| `active` | 点击瞬态 | 桌面端可点击组件 |
| `disabled` | 禁用态 | 任何可交互组件可能禁用时 |
| `loading` | 加载中 | 含异步数据 / 图片 |
| `error` | 加载失败 / 错误态 | 含异步数据 / 图片 |
| `empty` | 内部内容为空 | 含列表 / 集合容器 |
| `selected` | 选中态 | 含选择 / 多选交互 |
| `focused` | 键盘聚焦 | 含表单 / 键盘导航 |

**判定格式硬约束（违反即 precheck fail）：**

```yaml
- hover: {needed: yes, reason: 桌面端鼠标悬停反馈}     # ✅ 含理由
- active: {needed: no, reason: 卡片整体不可点击}       # ✅ 不需要也要写理由
- disabled: yes                                       # ❌ 缺 reason
- loading: {needed: yes}                              # ❌ 缺 reason
```

每条必须含 `needed` + `reason`，禁止简写或遗漏。

---

## 四、PRD 可视化要求（中保真）

### 4.1 中保真定义

PRD 中 proj 组件的可视化目的：**让人类阅读理解需求、走通流程**。不是发布级视觉、不是生产代码参考、也不是占位图。

**做到：**
- 组件之间**视觉可辨**：按钮看起来是按钮、价格看起来是价格、卡片看起来是卡片
- 状态之间**差异可辨**：default / hover / loading / error 肉眼能区分
- 真实文案 + 真实数据：写"无线降噪耳机 / ¥299 / 有货"，不写"产品名 / 价格 / 库存"
- 布局结构反映真实信息层级：卡片有图、有标题、有元信息、有操作按钮，各就各位

**不做：**
- 像素级精雕：阴影层次、动画过渡、字间距微调
- 完整设计系统：12 级灰度、8 级字号、复杂语义色板
- 浏览器兼容性优化、ARIA 完整标注、响应式全断点

可参考保真度区间：**Balsamiq 的结构清晰度 + 真实数据填充 + 状态差异可视**。

### 4.2 必须包含的两类可视化区域

#### A. 独立状态展示区（每个 proj 组件**必须**有一个）

```html
<section id="proj-component-{组件名}" class="proj-component-showcase">
  <h2>proj.L{tier}.{name} · 状态全集</h2>

  <div class="showcase-row">
    <span class="showcase-label">default 默认态</span>
    <article class="proj-{组件名}" data-component-status="NEW" data-component-id="proj.L{tier}.{name}">
      [完整渲染样例]
    </article>
  </div>

  <div class="showcase-row">
    <span class="showcase-label">hover 悬停态</span>
    <article class="proj-{组件名} is-hover" data-component-status="NEW" data-component-id="proj.L{tier}.{name}">
      [完整渲染样例]
    </article>
  </div>

  <!-- ...所有 needed: yes 的状态各一行 + default 一行 -->
</section>
```

**展示行数 = schema 中所有 `needed: yes` 的状态数 + 1（default）**。少一行即 precheck fail。

**[Must] 独立状态展示区的物理位置与归属**：

| 项 | 约定 |
|----|------|
| 物理位置 | 写在 **owner 模块** 的 PRD 草稿中（`process_record/drafts/prd_M[XX]_draft.html`），位于第一个 FRAME 之前（PROJ-CSS 块之后） |
| 归属规则 | 多模块共用同一 proj 组件时，独立状态展示区**只在 owner 模块的草稿中写一次**（与 PROJ-CSS 块的归属规则一致），非 owner 模块草稿**禁止**重复写 |
| owner 取值 | owner = §二.1 A 表中本组件的 `owner` 列值（机械可判定：`scaffold.json` `modules[]` 数组中顺序最靠前的引用本组件的模块 id） |
| 拼装行为 | `assemble.py prd` 不对独立状态展示区做特殊处理——它会随 FRAME 之外的草稿原文内容**保留在草稿中**；最终 PRD 中独立状态展示区会作为 `<section id="proj-component-{name}">` 出现在拼装产物中 |
| precheck 校验 | `precheck_stage4.py` 检测每个 proj 组件在 PRD 中是否含对应 `<section id="proj-component-{name}">`，缺失即 fail（S4-18）|

> **注意**（`assemble.py prd` 当前行为细分）：
> - ✅ **PROJ-CSS 块**：通过 `extract_proj_css` + `inject_proj_css`（`assemble.py` L445 / L879）**已自动注入**到 PRD `<style>` 顶部 `[PROJ-CSS-START/END]` 占位之间（详见 §五.1 表格「拼装动作」列）
> - ⚠️ **独立状态展示区**（FRAME 外的 `<section id="proj-component-{name}">`）：当前**不会**被自动拼到 PRD 主体；这是协议层的下一步增强项，已记录为后续优化（如需立即生效，可改造 `assemble_prd` 增加"提取独立状态展示区 section 注入到 PRD 模块 section 之前"的逻辑）
> - 普通 FRAME 内容：通过 `[FRAME: id]` 包裹标记提取并替换 PRD 骨架占位（既有逻辑）

#### B. 模块帧内引用（在使用本组件的模块帧中）

```html
<section id="H-M02-P01-default">
  <div class="product-grid">
    <article class="proj-{组件名}" data-component-status="NEW" data-component-id="proj.L{tier}.{name}">
      [实例 1：真实数据]
    </article>
    <article class="proj-{组件名}" data-component-status="NEW" data-component-id="proj.L{tier}.{name}">
      [实例 2：真实数据]
    </article>
  </div>
</section>
```

模块帧中的使用**不替代**独立状态展示区——两者必须并存。

---

## 五、CSS 抽象纪律（关键）

### 5.1 一次定义多处引用

每个 proj 组件**必须**在 PRD 顶部 `<style>` 块中定义一份 CSS class（base + 状态 modifier），**所有使用处只能引用 class 名**，禁止在使用处用 `style="..."` 实现该组件的视觉细节。

```html
<style>
/* === Project components — single source of truth === */
.proj-product-card { /* base */ }
.proj-product-card .pc-img { ... }
.proj-product-card .pc-title { ... }
.proj-product-card.is-hover { ... }
.proj-product-card.is-loading { ... }
.proj-product-card.is-error { ... }
.proj-product-card.is-focused { ... }
</style>

<!-- 使用处仅引用 class 名 -->
<article class="proj-product-card">...</article>
<article class="proj-product-card is-hover">...</article>
```

#### PRD 中 proj CSS 的物理位置（PM 实操路径）

> **关键**：proj 组件 CSS 不是 PM 直接写在 PRD 顶部 `<style>` 块。PM 在**模块 PRD 草稿**中按下方约定写入 `[PROJ-CSS]` 块，由 `assemble.py prd` 自动合并注入。

| 组件出现位置 | 物理写入位置 | 写入者 | 拼装动作 |
|------------|------------|-------|---------|
| 多模块草稿头部 | `process_record/drafts/prd_M[XX]_draft.html` 第一个 FRAME 之前 `<!-- [PROJ-CSS-START] -->...<!-- [PROJ-CSS-END] -->` 块 | 模块 PRD Agent（Step 5）| `assemble.py prd` 提取所有模块草稿中的 PROJ-CSS 块、合并 |
| PRD 模板预留占位 | `pm-workflow/rules/prd_template.html` 第一个 `<style>` 块顶部 `/* === [PROJ-CSS-START] auto-injected by assemble.py === */ ... /* === [PROJ-CSS-END] === */` | 模板（已就位）| `assemble.py prd` 把合并后的 CSS 注入到此占位 |
| 最终 PRD 产物 | `outputs/prd_[产品名]_latest.html` 顶部 `<style>` 块内 PROJ-CSS 占位中 | 脚本（注入）| 拼装产物，PM 不动 |

**约定：**
- **owner 模块**（即 §二.1 A 表 `owner` 列指定的模块）负责写完整 CSS（base + 全部状态 modifier）
- **非 owner 模块**仅引用 class，**禁止**写本组件的 PROJ-CSS 块（assemble 不去重；重复声明 → precheck FAIL）
- owner 判定无歧义：owner = `scaffold.json` `modules[]` 数组顺序最靠前的引用本组件的模块 id（与派发顺序、依赖图无关）
- 子阶段二.5（项目组件识别 Agent）**不写** CSS，仅在 components A 表写 owner；CSS 是 owner 模块 PRD Agent 的产出

**草稿示例（模块 PRD Agent 视角）：**

```html
<!-- [PROJ-CSS-START] -->
.proj-product-card { display: flex; padding: 12px; border: 1px solid var(--fb-border-1); }
.proj-product-card .pc-img { width: 60px; height: 60px; }
.proj-product-card.is-hover { box-shadow: 0 0 12px rgba(0,0,0,0.06); }
.proj-product-card.is-soldout { opacity: 0.5; filter: grayscale(1); }
<!-- [PROJ-CSS-END] -->

<!-- [FRAME: H-M02-P01-default] -->
<div class="frame-card">
  <article class="proj-product-card" data-component-status="NEW" data-component-id="proj.L2.product-card">
    ...真实数据...
  </article>
</div>
<!-- [/FRAME: H-M02-P01-default] -->
```

#### `[Must]` 派生模块引用 owner 组件的内部结构规则

> **来源历史**：issue # 8 复盘根因 = M02 PM 误读 §5.1「非 owner 仅引用 class」,理解为「只用容器 class（如 `.proj-scope-filter-bar`）即可,内部子元素可随便用通用 class（如 `fb-tag`）平铺替代」。**但 PROJ-CSS 真源中 owner 已为内部 slot 定义专用 class（如 `.pf-status-chip` / `.pf-owner-select` / `.pf-sort-toggle` / `.pf-range-trigger`)**,M02 内部用 fb-tag 时这些专用样式不作用,8 处帧视觉退化为通用 tag。

**规则**:派生模块（非 owner）引用 owner 的 proj 组件时,**HTML 内部结构必须完整使用 owner 在 PROJ-CSS 中定义的全套 slot class（容器 class + 所有内部子元素 class）**;**禁止**用通用 `fb-*` class（如 `fb-tag` / `fb-chip` / 裸 `fb-search`）或自定义 class 平铺替代这些专用 slot class。

| 维度 | owner 模块（如 M01） | 派生模块（如 M02） |
|------|---------------------|--------------------|
| PROJ-CSS 块 | **写完整**:base class + 所有内部子元素 class + 所有状态 modifier | **不写**（重复声明会触发 precheck FAIL）|
| HTML 引用 | 容器 class + **owner 定义的全套内部 slot class** | 容器 class + **同 owner 全套内部 slot class**（不可降级为通用 fb-* 平铺）|
| 数据值/业务规则 | owner 自身视角 | 派生模块自身视角（如管理员视角 3 status 全选 vs 销售视角 2 status 默认）|
| 状态 modifier | owner + 派生均可用 | 派生按本模块业务态选择 modifier 组合 |

**判定标准**：派生模块的 HTML 写法应与 owner 同组件 default 帧的 DOM **结构对偶**——容器 class 一致 + 内部子元素 class 集合一致 + class 名层级一致;**仅数据值 + 状态 modifier + 业务规则相关字面允许差异**。

**反例**(M02 修复前实际写法,issue # 8 修复 1-3 整改前):

```html
<!-- ❌ 派生模块用 fb-tag 平铺替代专用 slot,导致 owner PROJ-CSS 中 .pf-* 选择器全部失效 -->
<div class="proj-scope-filter-bar">
  <div class="fb-search"><input class="fb-search-input" /></div>
  <span class="fb-tag fb-tag-selected">进行中</span>
  <span class="fb-tag fb-tag-selected">已成交</span>
  <span class="fb-tag">负责人：王小明 / 张三 ▾</span>
  <span class="fb-tag">↕ 更新时间倒序</span>
</div>
```

**正例**(M02 修复后,与 owner M01 default 帧 DOM 结构对偶):

```html
<!-- ✅ 派生模块完整使用 owner 定义的 .pf-* slot class,PROJ-CSS 选择器正常生效 -->
<article class="proj-scope-filter-bar">
  <div class="pf-row">
    <div class="pf-sort-toggle">
      <span class="pf-sort-item">创建时间</span>
      <span class="pf-sort-item is-active">↕ 更新时间倒序</span>
      ...
    </div>
    <div class="pf-status-chips">
      <span class="pf-status-chip is-selected">进行中</span>
      <span class="pf-status-chip is-selected">已成交</span>
      <span class="pf-status-chip is-selected">已放弃</span>
    </div>
    <span class="pf-owner-select">负责人：王小明 / 张三 ▾</span>
    <span class="pf-range-trigger">创建：2026-01-01 ~ 今 ▾</span>
    <div class="pf-search"><input ... /></div>
  </div>
</article>
```

**根因展开**:`§5.1` 规定 PROJ-CSS **真源唯一**（owner 单源写、派生不重复声明）。SSOT 的完整外延是:**owner 定义的全套 class 名空间**（容器 class + 内部 slot class + 状态 modifier）**整体构成 SSOT,派生引用时不可只取容器 class 而省略内部 slot class**。否则 owner 已为内部 slot 写好的样式（如 `.pf-status-chip { padding:4px 12px; border-radius:14px; background:var(--fb-primary-bg-light); }`）就因派生层 HTML 不写 `.pf-status-chip` 而无法作用,视觉退化为浏览器默认 `<span>` + 浏览器默认 background。

**PM 实操对照清单**(PM 写派生模块 PRD 草稿引用 owner proj 组件时必做):

1. **第 1 步**:Read owner 模块草稿的 `[PROJ-CSS-START]...[PROJ-CSS-END]` 块,列出所有 owner 定义的 class 名（容器 + 内部 slot + modifier）
2. **第 2 步**:Read owner default 帧的 DOM,记录容器 + 内部 slot 的 class 层级结构
3. **第 3 步**:在派生模块草稿中**仿照 owner default 帧 DOM 结构**写,容器 class + 内部 slot class 名集合完全一致;仅替换数据值 + 按本模块业务态调整状态 modifier
4. **第 4 步**:**禁止**用 `fb-tag` / `fb-chip` / `fb-search` 等通用 class 平铺替代 owner 定义的专用 slot class（除非 owner 自身的 default 帧就使用了这些通用 class——则派生跟随 owner）
5. **第 5 步**:自审:grep 派生草稿,验证容器 class 数 + 各内部 slot class 数 ≈ owner default 帧的对应数量（允许业务态 modifier 差异但 slot 集合应对齐）

### 5.2 禁止模式

```html
<!-- ❌ inline style 散落，无法统一修改 -->
<article style="display:flex; padding:12px; border:1px solid #eee;">...</article>

<!-- ❌ 不同实例不同 inline style，破坏抽象 -->
<article class="proj-product-card" style="padding:16px;">...</article>

<!-- ❌ 未在 <style> 中定义的 class 直接使用 -->
<article class="proj-product-card-large">...</article>   <!-- 缺定义 -->

<!-- ❌ 派生模块引用 owner 组件时用通用 fb-* 平铺替代 owner 专用 slot class（issue # 8 复盘）-->
<!-- owner M01 PROJ-CSS 已定义 .pf-status-chip / .pf-owner-select / .pf-sort-toggle / .pf-range-trigger -->
<!-- 派生 M02 引用时若写 fb-tag 平铺,PROJ-CSS 的 .pf-* 选择器不作用 → 视觉退化 -->
<div class="proj-scope-filter-bar">
  <span class="fb-tag">进行中</span>           <!-- 应为 <span class="pf-status-chip is-selected">进行中</span> -->
  <span class="fb-tag">负责人：王 ▾</span>    <!-- 应为 <span class="pf-owner-select">负责人：王 ▾</span> -->
  <span class="fb-tag">↕ 时间倒序</span>      <!-- 应为完整 .pf-sort-toggle 容器 + 多个 .pf-sort-item -->
</div>
<!-- 详见本节 §5.1「派生模块引用 owner 组件的内部结构规则」-->
```

### 5.3 允许的例外

仅以下两种情况允许 inline style：

- **数据驱动的 layout 变量**：如 `style="--col-count: 3;"` 用于 CSS Grid 列数，需在组件 class CSS 中通过 `var()` 引用
- **slot 内容真实数据属性**：`<img src="...">` 的 src、`<a href="...">` 的 href、`<button onclick="...">` 的 onclick 等

**视觉细节**（颜色、字体、padding、border、shadow、border-radius 等）一律通过 class + modifier 实现。

### 5.4 `[Must]` 父容器几何契约（absolute 子元素 / 越界 transform 容器约束）

> **本节定位**：本节是组件 CSS 作者（proj 组件 / fb-fallback 组件 / PROJ-CSS 内临时样式）的强约束 — 任何含 `position: absolute / sticky / fixed` 子元素 / 伪元素 / 越界 transform 动画的组件 CSS,都必须显式声明对父容器的契约要求。`prd_expression_standard.md §零.3` 指向本节（2026-05-13 下沉,原位置仅留指针）。
>
> **来源历史**：issue # 15 滚动条闪烁根因 = 伪元素 `position: absolute; left:0; right:0` + `transform: translateX(-30%→130%)` 越界，**父级 `overflow-x: auto` 检测溢出 → 滚动条出现 → 抢宽度 → reflow → 收回 → 反复闪烁**。组件 CSS 作者只考虑了组件自身视觉(扫光动画)，没把"父容器若是 overflow: auto/scroll 会怎样"作为约束纳入设计。

#### `[Must]` 父容器契约清单

任何**含 `position: absolute / sticky / fixed` 子元素 / 伪元素**的组件 CSS（无论是 proj.\* 派生组件、fb-fallback 内置组件、还是 PROJ-CSS 内的临时样式），**必须**在组件 CSS 块顶部以注释形式声明父容器契约：

```css
/* 组件父容器契约（proj_component_protocol.md §5.4 SSOT）：
   1. position: 必须为 relative / absolute / fixed / sticky 之一（非 static），
      否则 absolute 子元素冒泡到 viewport 形成全屏漂移（参 issue # 11/# 16 复盘）
   2. overflow: 必须为 visible 或 hidden（**禁止** auto / scroll），
      因为本组件子元素含越界 transform / 越界几何，auto 会触发滚动条闪烁
      （参 issue # 15 stripe 越界 transform + overflow:auto 复盘根因 A/B）
   3. width/height: 须明确（不能 max-content / fit-content 自适应），
      否则子元素 inset: 0 / left+right: 0 计算异常 */
.my-component { /* ... 业务 CSS ... */ }
.my-component::before { position: absolute; /* ... 越界写法 ... */ }
```

#### `[Must]` 反例 vs 正例

| 类型 | 反例 ❌ | 正例 ✅ |
|------|--------|--------|
| 越界 stripe + 父级 overflow:auto | `.parent { overflow-x: auto } .parent::before { position: absolute; left:0; right:0; transform: translateX(-30%→130%) }` → 滚动条闪烁 | `.parent { overflow: hidden } .parent::before { ... translateX(-30%→130%) }` ✓ overflow:hidden 阻断溢出冒泡<br/>或：stripe 改为 `width: 30% + translateX(0→333%)`,在 `left:0; right:0` 撑满 vs `width:30%` 局部移动两种思路里选后者 |
| absolute 子元素 + 父级缺 position:relative | `.h5-frame { width: 390px; min-height: 844px } .fb-modal-overlay { position: absolute; inset: 0 }` → modal 冒泡到 viewport 看似全屏 | `.h5-frame { width: 390px; min-height: 844px; position: relative } .fb-modal-overlay { position: absolute; inset: 0 }` ✓ frame 是 positioned 祖先 |
| 自适应宽 + inset:0 | `.parent { width: max-content } .child { position: absolute; inset: 0 }` → inset 计算依赖父级具体尺寸,max-content 可能塌缩 | `.parent { width: 100% } .child { position: absolute; inset: 0 }` ✓ |

#### 与 prd_expression_standard.md §零.2 的关系

| 范围 | 规范出处 |
|------|---------|
| 面板/浮层组件（modal / toast / drawer / dropdown / popover / tooltip）— 7 种 | `prd_expression_standard.md §零.2` + `fb-fallback.css`（专门规范 7 类面板/浮层组件 + 嵌入帧 + 预设 z-index）|
| 其他所有 absolute 子元素 / 伪元素 / 越界 transform 写法 — proj.\* 派生 + 流程演示帧 inline + fb-fallback 非面板组件（如 `.fb-spinner` / `.fb-btn.is-loading::after`） | **本节 §5.4**（更广义的通用约束）|

`prd_expression_standard.md §零.2` 是本节的具体应用实例（面板/浮层是 absolute 元素的一种特殊场景）；本节 §5.4 是更高抽象层的通用父容器契约。

#### 机械兜底（precheck_stage4 S4-PERF-05）

`precheck_stage4` S4-PERF-05 检查项：
- 扫所有 `position: absolute` 的 CSS 规则（含 `::before / ::after` 伪元素）
- 顺藤摸 selector 到父容器对应 CSS 规则,检查父容器是否含 `position: relative/absolute/fixed/sticky` 和 `overflow: visible/hidden`
- 父容器为 `overflow: auto / scroll` + 子元素含越界 keyframes（`translateX` 出现 `<0%` 或 `>100%` 字面）→ WARN
- 父容器无 positioned 设置 → WARN（提示 inset/left/right/bottom/top 可能冒泡到 viewport）

详 `pm-workflow/scripts/precheck_stage4.py` 内 S4-PERF-05 实现。

---

## 六、HTML 标记规范

### 6.1 命名约定

```
proj.L{tier}.{kebab-case-name}              # schema id
proj-{kebab-case-name}                       # CSS 类名（去除层级前缀）
proj-component-{kebab-case-name}            # 状态展示区 section id
```

示例：

| schema id | CSS class | showcase section id |
|-----------|-----------|---------------------|
| proj.L2.product-card | .proj-product-card | proj-component-product-card |
| proj.L2.work-card | .proj-work-card | proj-component-work-card |
| proj.L3.product-list-section | .proj-product-list-section | proj-component-product-list-section |

### 6.2 必填属性

每个 proj 组件实例（包括状态展示区和模块帧内的所有使用处）**必须**含两个 data 属性：

```html
<article 
  class="proj-product-card" 
  data-component-status="NEW" 
  data-component-id="proj.L2.product-card">
  ...
</article>
```

- `data-component-status="NEW"` — 标识"此组件由 PM 在本项目中新建，下游需实现为正式可复用组件"
- `data-component-id="..."` — 与 schema 声明的 id 完全一致，便于 grep 与追溯

pub 组件**不需要**这两个标记。

### 6.3 触点 ID

如组件含可交互元素，按 `proto_contract.md §四` 触点编号规范分配 `data-touchpoint`：

```html
<article class="proj-product-card" data-component-status="NEW" data-component-id="proj.L2.product-card">
  ...
  <button class="fb-btn-primary" data-touchpoint="M02-P01-T01">加入购物车</button>
</article>
```

---

## 七、配套硬规则（应加入 `rule_hard_constraints.md` §七 阶段4 硬规则节）

### S4-17 `[MUST]` proj 组件状态枚举完整性

新增 proj 组件时，`states.applicable` 必须按本协议 §三 的 8 项清单**逐条**判定（`default` 不需判定）；每条必须提供 `needed: yes/no` + `reason: <一句话理由>`，不允许简写或遗漏。

precheck 验证：扫 `outputs/components_[产品名]_latest.md` 中每个 proj 组件，`states.applicable` 须含全部 8 项 key 且每项含 `needed` + `reason` 字段。

### S4-18 `[MUST]` proj 组件可视化完整性

每个 proj 组件必须在 PRD 中提供**独立状态展示区**（`<section id="proj-component-{name}">`）；区内按 schema 中所有 `needed: yes` 的状态各渲染一行可见样例 + default 一行。模块帧内的使用**不替代**独立状态展示区——两者必须并存。

precheck 验证：对每个 proj 组件 id，PRD 中必须存在对应 `id="proj-component-{name}"` 的 section；section 内 `.showcase-row` 数量 = schema `needed: yes` 计数 + 1。

### S4-19 `[MUST]` proj 组件 CSS 抽象纪律

每个 proj 组件**必须**在 PRD 顶部 `<style>` 块定义一份 CSS class（base + 全部 `needed: yes` 状态对应的 modifier 选择器）；所有使用处**只能引用 class 名**，禁止在使用处用 `style=""` 实现组件视觉细节。仅 §五.3 列出的两种例外（CSS 变量、数据属性）允许 inline style。

precheck 验证：
- 每个 `class="proj-XXX"` 元素不得含 `style="..."` 属性（数据属性与 CSS 变量除外）
- 每个出现在 HTML 中的 `.proj-XXX` 类必须在 `<style>` 块中有 selector 定义
- 每个 `needed: yes` 的状态对应 `.proj-XXX.is-{state}` 选择器必须存在

---

## 八、precheck 验证规则（应纳入 `precheck_stage4.py`）

| 检查项 | 失败条件 | 关联硬规则 |
|--------|---------|-----------|
| **schema 完整性** | `outputs/components_[产品名]_latest.md` 中任一 proj 组件缺少 `inherits` / `modules` / `slots` / `states` / `state_transitions` / `field_schema` 任一字段 | — |
| **状态枚举完整性** | `states.applicable` 缺失 8 项中任一；或某项无 `needed` 或 `reason` 字段 | S4-17 |
| **状态展示区存在性** | 每个 proj 组件 id 在 PRD 中找不到对应 `id="proj-component-{name}"` 的 section | S4-18 |
| **状态展示行数一致** | 状态展示区中 `.showcase-row` 数量 ≠ schema `needed: yes` 数 + 1 | S4-18 |
| **CSS 抽象纪律：禁 inline style** | 任何 `class="proj-XXX"` 元素带 `style="..."` 属性（数据 attribute 与 CSS 变量除外） | S4-19 |
| **CSS 类定义存在性** | HTML 中出现的 `.proj-XXX` 类在 `<style>` 块中无 selector 定义 | S4-19 |
| **状态 modifier 完备性** | 某 `needed: yes` 状态对应的 `.proj-XXX.is-{state}` 选择器在 `<style>` 中缺失 | S4-19 |
| **NEW 标记完整性** | proj 组件实例缺少 `data-component-status="NEW"` 或 `data-component-id` 标记 | — |
| **NEW 组件可追溯** | `data-component-id` 在 `components_[产品名]_latest.md` 中找不到对应 schema 声明 | — |
| **owner 字段存在性** | A 表行缺 `owner` 列或值为空 | — |
| **owner ∈ 模块列** | A 表 `owner` 不在同行「模块」列声明的模块集合中 | — |
| **owner 顺序最靠前** | A 表 `owner` 不等于 `scaffold.json` `modules[]` 中顺序最靠前的引用本组件的模块 id | — |
| **草稿 PROJ-CSS 归属唯一** | 扫 `process_record/drafts/prd_M[XX]_draft.html` 的 `[PROJ-CSS-START/END]` 块；某 proj 组件的 `.proj-{name}` 选择器只允许在 owner 模块草稿中出现，非 owner 草稿出现即 FAIL | — |

---

## 九、完整示例：`proj.L2.product-card`

### 9.1 schema 声明

```yaml
- id: proj.L2.product-card
  inherits: pub.L2.card
  modules: [M02, M03, M07]
  purpose: 在产品列表 / 详情推荐 / 购物车关联推荐三个场景中复用展示产品基础信息

  slots:
    - media:    {required: true,  type: image, source: spec §9.cover_url}
    - title:    {required: true,  type: text,  source: spec §9.product_name, max: 50}
    - meta:     {required: true,  type: list,  source: [价格, 库存标签]}
    - actions:  {required: true,  type: list,  source: [加购按钮]}

  states:
    required: [default]
    applicable:
      - hover:    {needed: yes, reason: 桌面端鼠标悬停反馈}
      - active:   {needed: yes, reason: 桌面端点击瞬态}
      - disabled: {needed: no,  reason: 卡片整体不可禁用，按钮独立处理}
      - loading:  {needed: yes, reason: 产品图异步加载}
      - error:    {needed: yes, reason: 产品图加载失败显示占位}
      - empty:    {needed: no,  reason: 库存为零通过 meta 标签处理}
      - selected: {needed: no,  reason: 本期不支持多选}
      - focused:  {needed: yes, reason: 键盘 Tab 导航无障碍要求}

  state_transitions:
    - default → loading → default       # 图片异步加载流程
    - loading → error                   # 加载失败
    - default ↔ hover                   # 桌面悬停切换
    - default → focused                 # Tab 聚焦

  field_schema:
    - product_id:   {type: string,  source: spec §9.product_id}
    - product_name: {type: string,  max: 50, source: spec §9.product_name}
    - price_cents:  {type: integer, min: 0,  source: spec §9.price_cents}
    - stock_label:  {type: enum,    enum: [有货, 缺货, 预售], source: spec §9.stock_label}
    - cover_url:    {type: url,     source: spec §9.cover_url}
```

### 9.2 PRD CSS 定义（中保真）

```html
<style>
/* === Project component: product-card === */
.proj-product-card {
  display: flex; gap: 12px; padding: 12px;
  border: 1px solid var(--fb-border-1); border-radius: 8px;
  background: var(--fb-bg-1);
}
.proj-product-card .pc-img {
  width: 80px; height: 80px;
  background: var(--fb-bg-2); border-radius: 4px;
  flex-shrink: 0; object-fit: cover;
}
.proj-product-card .pc-body { flex: 1; min-width: 0; }
.proj-product-card .pc-title {
  font-weight: 600; margin-bottom: 4px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.proj-product-card .pc-meta { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.proj-product-card .pc-price { color: var(--fb-text-price); font-weight: 700; }
.proj-product-card .pc-stock { font-size: 12px; color: var(--fb-text-secondary); }

/* state modifiers */
.proj-product-card.is-hover {
  background: var(--fb-bg-2); border-color: var(--fb-text-primary);
}
.proj-product-card.is-active { transform: scale(0.98); }
.proj-product-card.is-loading .pc-img {
  background: linear-gradient(90deg, var(--fb-bg-2) 0%, var(--fb-border-1) 50%, var(--fb-bg-2) 100%);
}
.proj-product-card.is-error .pc-img {
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: var(--fb-text-hint);
}
.proj-product-card.is-error .pc-img::after { content: "图片加载失败"; }
.proj-product-card.is-focused {
  outline: 2px solid var(--fb-text-primary); outline-offset: 2px;
}
</style>
```

### 9.3 状态展示区

```html
<section id="proj-component-product-card" class="proj-component-showcase">
  <h2>proj.L2.product-card · 状态全集</h2>

  <div class="showcase-row">
    <span class="showcase-label">default 默认态</span>
    <article class="proj-product-card" data-component-status="NEW" data-component-id="proj.L2.product-card">
      <img class="pc-img" src="..." alt="">
      <div class="pc-body">
        <div class="pc-title">无线降噪耳机</div>
        <div class="pc-meta">
          <span class="pc-price">¥299</span>
          <span class="pc-stock">有货</span>
        </div>
        <button class="fb-btn-primary" data-touchpoint="M02-P01-T01">加入购物车</button>
      </div>
    </article>
  </div>

  <div class="showcase-row">
    <span class="showcase-label">hover 悬停态</span>
    <article class="proj-product-card is-hover" data-component-status="NEW" data-component-id="proj.L2.product-card">
      <!-- 同 default 内容，is-hover modifier 触发悬停视觉 -->
    </article>
  </div>

  <!-- active / loading / error / focused 各一行 -->
</section>
```

### 9.4 模块帧内引用

```html
<section id="H-M02-P01-default">
  <h3>产品列表 · 默认态</h3>
  <div class="product-grid" style="--col-count: 3;">
    <article class="proj-product-card" data-component-status="NEW" data-component-id="proj.L2.product-card">
      [产品 A：真实数据]
    </article>
    <article class="proj-product-card" data-component-status="NEW" data-component-id="proj.L2.product-card">
      [产品 B：真实数据]
    </article>
    <article class="proj-product-card" data-component-status="NEW" data-component-id="proj.L2.product-card">
      [产品 C：真实数据]
    </article>
  </div>
</section>
```

注意 9.4 中 `style="--col-count: 3;"` 是允许的例外（数据驱动 CSS 变量），`.product-grid` 自身的 grid layout 在 `<style>` 块中通过 `grid-template-columns: repeat(var(--col-count, 1), 1fr);` 定义。

---

## 十、相关文件引用

| 文件 | 关联点 |
|------|-------|
| `bujue-design-system/pub_components_index.md` | **pub 组件索引**——本协议 §一 双触发判定的参照系，PM 派生 proj 前**必读** |
| `proto_contract.md` | 阶段 4 触点编号规范、状态帧规范、视觉自检清单 |
| `prd_expression_standard.md` | PRD 文档结构、状态切换实现（`showSection`） |
| `proto_spec_md.md` | spec.md 中模块/页面/组件描述格式 |
| `task_card_template.md` | 阶段 4 任务规划阶段，可在任务卡中预声明候选 proj 组件清单 |
| `rule_hard_constraints.md` | 本协议 §七 三条硬规则（S4-17 / S4-18 / S4-19）的最终落地位置 |
| `gen_scaffold.py` / `assemble.py` / `precheck_stage4.py` | 阶段 4 脚本，需配合本协议扩展（参见 §八） |

---

## 十一、消费者清单（schema 字段覆盖核查参照）

> **本段为 `pm-workflow/rules/workflow_maintenance_protocol.md`「模板/规范描述粒度原则·消费者视角对偶」`[Must]` 原则的最小落地示范。** 协议演进时（增删字段 / 新增消费者）须反向核查本表是否仍完备——任一缺口须补字段或显式豁免理由。

| 消费者 | 消费场景 | 期望从 components_*.md 提取的信息 | 当前覆盖位置 |
|-------|---------|-------------------------------|-------------|
| 下游开发（构建组件） | 理解为什么派生 + 在哪用 + 怎么用 + 怎么实现 | 业务边界 / 业务场景 / 用户操作流 / 状态枚举 / 字段约束 / CSS 抽象 | §二.2 三段（boundary / usage / interaction）+ slots / states / field_schema |
| 模块 PRD Agent（Step 5） | 在 PRD 中正确渲染状态展示区与模块帧实例 | 状态枚举 + 状态 modifier + slot 视觉规则 + HTML 标记 | §二.2 视觉规范层 + §四 PRD 可视化要求 + §六 HTML 标记 |
| 模块 Spec Agent（Step 3） | 在 spec 中按 id 引用 + 字段绑定 | id / inherits / slots / field_schema source 指向 | §二.1 索引段 D 表 + §二.2 字段层 |
| Supervisor 阶段 4 审核 | 审核组件能力是否覆盖业务需求 | 派生触发因素（A/B + D1-D5） + boundary.differs_from + 状态完备性 | §一 D1-D5 + §二.2 boundary + §三 状态清单 |
| precheck_stage4.py | 机械校验 schema 完整性 / CSS 抽象 / NEW 标记 | 必填字段 / 状态字段格式 / class 命名约定 | §二.2 三段 [Must] + §六 命名约定 + §八 验证规则 |

---

## 十二、阶段 4 流程衔接

本协议在阶段 4 模块化派发流程中的位置：

```
Step 1   任务规划 PM Agent（生成 scaffold.json）
Step 1.5 gen_scaffold.py（编排器执行）
Step 2   Foundation Agent（写 spec S0/S0.5/S1 + prd 产品规格区）
Step 2.5 ★ 项目组件识别 Agent（按本协议产出 components_[产品名]_latest.md）  ← 本协议主要触发点
Step 3   各模块 Spec Agent（引用 pub.* + proj.*）
Step 4   assemble.py spec
Step 5   各模块 PRD Agent（引用 pub.* + proj.*；按本协议在 PRD 中渲染 proj 组件）  ← 本协议主要执行点
Step 6   assemble.py prd
Step 6.5 precheck_stage4.py（含本协议 §八 验证规则）
Step 7   PM 自审（含本协议 §七 三条硬规则核查）
```

---

## 十三、变更记录

| 版本 | 变更内容 | 日期 |
|------|---------|------|
| v1.0 | 初版：PM 边界澄清、双交付定义、schema 协议、8 状态枚举强制清单、中保真可视化要求、CSS 抽象纪律、HTML 标记规范、3 条配套硬规则（S4-17/18/19）、precheck 验证清单、完整示例（proj.L2.product-card） | 2026-04-26 |
| v1.1 | 引入 pub_components_index.md 作为派生判定前置；§二 改为"文件结构（索引段 + 详情段）"两层；§二.1 索引段 4 张表（A active / B deprecated / C proposed-promote / D 按模块反查）；§十 加入 pub 索引引用 | 2026-04-27 |
| v1.2 | §二.2 schema YAML 加业务语义三段（boundary / usage / interaction），后续开发构建组件时有明确需求依据；新增 §十一·消费者清单（`pm-workflow/rules/workflow_maintenance_protocol.md`「消费者视角对偶」原则的最小落地示范）；原 §十一 / §十二 重编号为 §十二 / §十三 | 2026-05-07 |
