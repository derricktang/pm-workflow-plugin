---
name: fb-design-query
description: fb 设计系统查询决策树 — PM 在写 PRD 章节前调用，按 8 维度走结构化路径定位精确组件 + token + 端规范 + 反 pattern。治 PM"凭直觉选 class / 漏读隐藏跨平台支持"根因；避免 v2 三 class 同型误叠加 + 隐藏陷阱漏读再次复现。
ssot_anchor_id: "ssot_anchors.md #52"
---

# fb-design-query — fb 设计系统查询决策树

## 一、何时调用 + 调用方式

### 调用时机

| PM Agent 阶段 | 强度 | 触发场景 |
|---|---|---|
| **子阶段五 Module PRD Agent**（写 prd_M[XX]_draft.html）| **`[Must]`** | 写每段 HTML 涉及 `class="fb-*"` 组件引用前，必走本 skill 决策树 |
| **子阶段三 Module Spec Agent**（写 spec_M[XX]_draft.md）| `[Should]` | 触点表 / 状态描述 / 业务规则涉及具体组件语义时调用 |

### 调用方式

按 `feedback-pm-self-reported-precheck-numbers` + `skill-design-principle` 纪律：

1. PM Read 本 SKILL.md 全文
2. 按 §二 8 维度决策树**逐题答**（不可跳题 / 不可凭直觉）
3. 落地到 §三 分支路径终点 → Read 指定真源段
4. 按 §四 输出 5 部分模板写答案到模块子进度文件「## fb-design-query 查询记录」段
5. PRD 章节内引用本次查询结果（HTML class / token 变量）

### 为什么必走（治 PM L2 推断错诊根因）

NB-pub-phone-bar 实证（参 `s4-28-v3-action-bar-unification`）：PM 漏读 `fb-fallback-manifest.md §3.2 移动端 Action Sheet 自动适配`（827 行 manifest 中第 41% 位置）→ 凭直觉推断"pub 缺 phone 底栏类" → 上报 L2 缺陷错诊 → 推 5 轮深度质疑驱动 v2→v3 重大重构。

根因 = **PM 无强制核查路径**。本 skill = 治本路径 = 强制 PM 按 8 维度查询，自动覆盖所有"深埋真源段"。

---

## 二、决策树主干（8 维度，按顺序逐题答）

### Q1: 业务需求类型？（6 大场景）

| 选项 | 含义 | 走分支 |
|---|---|---|
| A | 数据展示（卡片 / 标签 / 徽章 / 头像）| §三 分支 A（→ Read `pub_components_index.md §4.1`）|
| B | 数据输入（输入框 / 单选 / 多选 / 开关 / 上传）| §三 分支 B（→ Read `§4.2`）|
| C | 反馈 / 状态（空 / 加载 / 错误 / 浮层提示）| §三 分支 C（→ Read `§4.3`）|
| D | 操作 / 导航（按钮 / 弹框 / 分页 / Tab）| §三 分支 D（→ Read `§4.4`）|
| E | 容器 / 布局（卡片 / modal / drawer / 底栏 / 顶栏 / 列表 / 表格）| §三 分支 E（→ Read `§4.5`）⚠ 含底栏跨平台陷阱 |
| F | 多类组合（一个段同时涉及 2+ 类）| 拆分多个需求，分别走 Q1 |

### Q2: 容器上下文？

| 选项 | 含义 |
|---|---|
| 1 | 独立（直接在 page 内，非 modal/drawer/card 内）|
| 2 | `.fb-modal` 内（modal 弹框）|
| 3 | `.fb-drawer` 内（侧栏抽屉）|
| 4 | `.fb-card` 内（卡片）|
| 5 | `.{*}-frame` 直接子层（frame 末位 / 首位 sticky 位置）|
| 6 | 嵌套（如 phone-frame 内 modal 内）— 取**最近祖先**（CSS 变量就近继承）|

⚠ **关键陷阱**：phone-frame 内的 modal 自动变 Action Sheet 形态（由 `.phone-frame .fb-modal` 真源 CSS 触发，详 manifest §3.2）。**这是 NB-pub-phone-bar 错诊根源** — 漏看此段会误判"pub 缺 phone 类"。

### Q3: 适用端口？

| 选项 | 端口 | 关联规范 |
|---|---|---|
| 1 | desktop（桌面 Web）| `proto_platform_desktop.md` |
| 2 | tablet（PAD 横屏）| `proto_platform_app.md §PAD` |
| 3 | phone（移动 Web / APP）| `proto_platform_app.md §手机` + `proto_cross_platform.md §三 移动端操作布局` |
| 4 | h5（H5 端）| `proto_platform_h5.md` |
| 5 | miniprogram（小程序）| `proto_platform_miniprogram.md` |
| 6 | 跨端（多端覆盖）| `proto_cross_platform.md` 全文 |

⚠ **关键陷阱（移动端底栏）**：phone / h5 / miniprogram 端**禁 sticky 底栏**（违 proto_cross_platform §三 设计哲学）。应用 navbar 顶部 + 「···」菜单方案。`fb-action-bar` 在移动 frame 直接子层会触发 S4-28 v3 WARN。

### Q4: 特殊状态需求？

| 选项 | 状态 | 优先选用 |
|---|---|---|
| 1 | 无特殊状态（仅 default）| 跳过此维度 |
| 2 | 空（empty）| `fb-state-empty`（含 NoData svg）|
| 3 | 加载中（loading）| 长时 `fb-state-loading` / 短时按钮 `fb-btn.is-loading` |
| 4 | 错误（error）| `fb-state-error`（actions 必含重试）|
| 5 | 成功（success）| 短时 `fb-toast(success)` / 整页 `fb-state-success` |
| 6 | 禁用 / 无权限（disabled）| `fb-state-disabled`（整页级）|
| 7 | 字段级错误 | `fb-hint(error)` + `fb-input(is-error)` — **禁用 toast** |
| 8 | 表单 loading | 按钮 loading + 其他字段 readonly |

### Q5: 数据规模？

| 选项 | 规模 | 选型影响 |
|---|---|---|
| 1 | 单条 | 任意组件 |
| 2 | 少量（≤ 5）| `fb-list` + `fb-list-item` |
| 3 | 中量（5-20）| `fb-list` 或 `fb-table`（按端口）|
| 4 | 大量（> 20）| `fb-table`（同屏字段 ≥ 5 + 桌面优先）+ `fb-pagination`；手机端降级卡片（参 `proto_data_display_selection.md §一`）|
| 5 | 海量（需虚拟滚动 / 异步加载）| 派生 proj（pub 不覆盖虚拟滚动）|

### Q6: 设计 token 需求？

| 选项 | 需要 token | Read 资源 |
|---|---|---|
| 1 | 颜色（背景 / 文字 / 边框 / 状态色）| `bujue-design-system/tokens.md` 颜色表 |
| 2 | 间距（padding / margin / gap）| `tokens.md` 间距标准 + `INSTRUCTIONS.md` 间距规范 |
| 3 | 字号 / 行高 | `tokens.md` 字号表 |
| 4 | 圆角 / 阴影 | `tokens.md` 圆角 / 阴影规范 |
| 5 | z-index | `prd_expression_standard.md §零.1` 全局 z-index 数值表（仅合法集合 {300, 200, 150, 100, 60, 50, 41, 40, 10, 1}）|
| 6 | 交互态（hover / active / disabled）| `INSTRUCTIONS.md` 交互态规范 + 组件 detail md |

⚠ **关键陷阱（z-index 真源）**：PM 写自定义 z-index 数值 → 触发 `check_z_index_compliance` FAIL。必须从 §零.1 合法集合选。

### Q7: 端规范适配？

| 选项 | 适配维度 | Read 资源 |
|---|---|---|
| 1 | 触控目标尺寸（移动端 ≥ 44px） | `proto_platform_app.md §手机帧` + `proto_platform_miniprogram.md` |
| 2 | 帧规范（desktop / tablet / phone / h5 / miniprogram 帧）| 对应 `proto_platform_*.md` |
| 3 | 跨端差异（如 desktop 用 sidebar / 移动用 navbar）| `proto_cross_platform.md` 全文 |
| 4 | 移动端操作布局（导航栏 + 「···」菜单方案 vs sticky 底栏）| `proto_cross_platform.md §三` |
| 5 | 数据展示选型（列表 / 详情 / 异常态 / 海量）| `proto_data_display_selection.md` |
| 6 | 国际化 / 多语言 | `fb-fallback-manifest.md` data-zh / data-en 段 |

### Q8: 交互密度？

| 选项 | 密度 | 影响 |
|---|---|---|
| 1 | 单触点（仅 1 个操作）| 单按钮 / 单链接 |
| 2 | 操作组（2-3 个并列操作）| `fb-action-bar` / `fb-card-actions` / `fb-state-actions`（按容器选）|
| 3 | 主次操作（1 主 + N 次）| 主操作 `fb-btn-primary` 居右 + 次操作 `fb-btn-default`；同操作组只允许 1 个 primary |
| 4 | 危险操作 | `fb-btn-danger` + 二次确认 modal + 触点编号 `D[ZZ]` |
| 5 | 高频操作（列表项内 2+ 按钮）| `fb-list-item-extra` 内按钮组 / `fb-table-cell-actions` |
| 6 | 收纳菜单（≥ 3 个操作）| 移动端 navbar 「···」+ 底部抽屉（`proto_cross_platform.md §三`）|

### Q9: 页面状态（仅 phone-frame / h5-frame / miniprogram-frame 移动场景必答 — 决定 navbar variant）

按 7 场景分类决定 `.fb-navbar data-variant` 与底栏 `.fb-action-bar data-purpose`：

| 选项 | 页面状态 | navbar data-variant | navbar slot 填充 | 底栏 data-purpose |
|------|---------|---------------------|------------------|-------------------|
| 1 | 次级详情页（浏览态）| `detail`（默认）| `.fb-nav-back` + `.fb-nav-title` + `.fb-nav-action` ≤1 | `page-main`（≤4 并列主操作）|
| 2 | 列表多选态 | `multi-select` | `.fb-btn-text`（取消）+ `.fb-nav-title`（已选 N/M）+ `.fb-btn-text`（全选/反选）| `multi-select-batch`（≤3 批量操作）|
| 3 | 表单/浮层确认 | `confirm` | `.fb-btn-text`（取消）+ `.fb-nav-title` + `.fb-btn-primary`（确认）| 通常无底栏 |
| 4 | 编辑态密集 | `edit` | `.fb-btn-text`（完成）+ `.fb-nav-title` + `.fb-nav-action`（···）| 通常无底栏 |
| 5 | 列表入口页 | `list` | `.fb-nav-back`（可选）+ `.fb-nav-title` + `.fb-nav-action` × N（筛选/搜索/新增）| 通常无底栏 |
| 6 | 向导分步 | `workflow` | `.fb-nav-back`（上一步）+ `.fb-nav-title`（步骤 X/N）+ `.fb-nav-action`（跳过）| `workflow-nav` |
| 7 | 主页 / 一级 Tab | `home` | — + `.fb-nav-title`（logo）+ `.fb-nav-action` × N | `fb-tab-bar`（非 .fb-action-bar）|

**`[Must]` 规则**：
- PM 必须在 `<div class="fb-navbar">` 加 `data-variant="XXX"` 属性，缺省默认 `detail`（向后兼容现有用法）
- 移动 frame 直接子层 `.fb-action-bar` 必须加 `data-purpose="XXX"` 明示业务场景，否则触发 S4-28 v3 R2 WARN
- **禁止**用 inline `<div style="position:sticky;top:0">` 自由发挥实现顶部容器（`check_panel_class_evasion` 扩展拦截 + S4-35 v2 ⑤ 违规）；必须用 `.fb-navbar` + 适当 variant
- center slot 总用 `.fb-nav-title` 容器（即使内容是"已选 N/M" / "步骤 X/N" 等非标题文字）

**反 pattern**（v1 自由发挥旧坑）：
- ❌ 多选态用 inline `<div style="padding:8px 16px">已选 N/M [退出]</div>` → 应用 `.fb-navbar data-variant="multi-select"` 标准 slot 填充
- ❌ 详情页 4 并列按钮放底部 `.fb-action-bar`（无 data-purpose）→ 加 `data-purpose="page-main"` 明示合规
- ❌ 表单页底部放「保存」按钮无 navbar 确认 variant → 用 `.fb-navbar data-variant="confirm"` 右 slot `.fb-btn-primary`（确认）
- ❌ 自定义 `.toolbar` / `.top-bar` / `.action-strip` 等自由命名类 → 必须用 `.fb-navbar` + variant

**`[Should]` 特例：装饰背景 navbar（modal-bg 场景）**：phone-frame.is-modal-bg / h5-frame.is-modal-bg 内 navbar 仅作背景层视觉表达（modal 遮罩覆盖后不可交互），不选 detail（会触发 S4-35 强制 nav-back 污染触点表）；推荐 `data-variant="list"` 兜底（不强制 nav-back）+ `style="opacity:0.5"` 视觉降权 + 仅 `.fb-nav-title` + 注释豁免 `<!-- modal-bg 装饰: list variant 兜底（背景层无返回语义）-->`（同 SSOT #58 注释豁免同型）。详 `fb-fallback-manifest.md §3.12 v2 装饰背景 navbar 选择指引` 段。

详 `fb-fallback-manifest.md §3.12 v2` + `proto_cross_platform.md §三 v2` + `rule_hard_constraints.md §S4-35 v2` + `§S4-28 v3 R2`（SSOT #53）。

### 二.X 决策树执行完毕后的显式声明（[Must]，治"PM 查了 pub 仍自由发挥"根因）

`[Must]` PM 走完 Q1-Q8 决策树后，必须在 PRD 写作前 / spec 写作前**显式声明 pub 库查询结论 + 后续动作**（写入进度文件 / PM 自审报告 / 或 PRD 文档注释，三选一）。三选一格式：

**①pub 已含变体场景（严格沿用）**：
```
[fb-design-query 查询结论] 本次写作涉及 pub 组件 [fb-XXX / archetype-YYY]，
已查 Q1-Q8 决策树拿到对应变体 [variant-key]；严格沿用 pub 规范，
未自由发挥视觉细节（色彩 / 字号 / 间距 / 动效 / 状态变体）。
真源：pub_components_index.md §X.Y / fb-fallback-manifest.md §3.Z。
```

**②pub 无变体场景（上报 NB）**：
```
[fb-design-query 查询结论] 本次写作涉及视觉需求 [描述]，
已查 Q1-Q8 决策树 + pub 库无对应变体；走 SSOT #31 NB 上报路径
（NB-pub-补 [描述]），等上游补 pub 规范后再写作此部分；
本次 PRD/spec 仅以业务语义描述（不自定义视觉细节）。
```

**③装饰/特殊场景（注释豁免）**：
```
[fb-design-query 查询结论] 本次写作涉及 [装饰背景 / modal-bg / 其他特殊]
场景，按 §二 Q9 注释豁免机制 + 装饰背景 navbar 选择指引处理；
显式注释豁免理由：<!-- 装饰: list variant 兜底（无返回语义）-->
（同 SSOT #58 D 方案注释豁免同型）。
```

**禁止行为**：
- ❌ PM 走完 Q1-Q8 但**不声明** → Supervisor §4.4 抽查时 WARN
- ❌ PM 声明"已查 pub"但 PRD/spec 视觉细节与 pub 规范不符 → P0 一票否决退回整改
- ❌ PM 声明"pub 无变体"但 NB-pub-补 [...] 未实际上报 → P0 一票否决退回

**违反信号**：private-domain-homepage-module issue 2026-06-01_1222 ~ 13 条视觉问题（仪式感 / 卡片样式 / 间距 / 色彩饱和度 / 视觉权重等）— PM 已应用 SSOT #52 走 Q1-Q8 但仍凭直觉构造视觉细节；根因 = 查了 pub 但**未显式承诺严格沿用**就开写。本 [Must] 强制显式声明环节，让"查了 pub 仍自由发挥"反 pattern 在 §4.4 抽查 + Sup 终审两道门拦截。

**与 SSOT #58 D 方案的协同**：
- D 方案 §十二 [Should] 注释豁免机制 = 业务多样性兜底
- 本声明 [Must] = pub 真源严守
- 二者协同：先 [Must] 严守 pub → pub 无 / 特殊场景走 [Should] 注释豁免

---

## 三、分支路径（Q1 → 8 个场景对应 Read 段）

每分支终点都需要 Read 对应真源段（不在本 SKILL.md 内重复）。

### 分支 A — 数据展示

1. Read `pub_components_index.md §4.1` 反查表 → 定位候选组件
2. Read `fb-fallback-manifest.md §3.x` 对应组件段（HTML 模板 + 反 pattern）
3. 若涉及 D1-D5 维度查询（字段数 / 状态数 / 交互模式 / 业务语义 / 端约束）→ Read `pub_components_index.md §五`
4. 若涉及 token → Q6 + Read `tokens.md`

### 分支 B — 数据输入

1. Read `pub_components_index.md §4.2` 反查表
2. Read `fb-fallback-manifest.md §1.x（Input/Textarea/Select/Radio/Checkbox/Switch/Search/FormRow）` 对应段
3. 表单组合 → Read `fb-fallback-manifest.md §1.5 FormRow` 段（label + 控件 + 错误提示）
4. 输入校验状态 → Q4 字段级错误（`fb-hint(error)` + `fb-input(is-error)`，禁 toast）

### 分支 C — 反馈 / 状态

1. Read `pub_components_index.md §4.3` 反查表
2. Read `fb-fallback-manifest.md §3.3 Toast` + §5 State 段
3. **决策路径**：
   - 整页状态（空 / 加载 / 错误 / 成功 / 禁用）→ `fb-state-*`
   - 浮层短提示（自动消失）→ `fb-toast(*)`
   - 字段级错误 → `fb-hint(error)` + `fb-input(is-error)`
   - 长时反馈（不消失）→ Q2 容器决定（在 modal 内或独立）

### 分支 D — 操作 / 导航

1. Read `pub_components_index.md §4.4` 反查表
2. Read `fb-fallback-manifest.md §1.1 Button` + §3.2 Modal 段
3. **触点编号决策**：危险/不可逆操作 → `D[ZZ]` 编号 + 必有二次确认 modal；普通触点 → `T[ZZ]`
4. **操作组排列**：主操作居右 + 次操作居中 + 取消居左（详 §4.4 反查 + INSTRUCTIONS.md）

### 分支 E — 容器 / 布局 ⚠ 重点（含底栏跨平台陷阱）

1. Read `pub_components_index.md §4.5` 反查表
2. Read `fb-fallback-manifest.md` 对应段：
   - 卡片 → §3.1 Card
   - modal → **§3.2 Modal（必读「移动端 Action Sheet 自动适配」段 — NB-pub-phone-bar 错诊根源！）**
   - drawer → §3.4 Drawer
   - 列表 → §4.1 List
   - 表格 → §4.2 Table
   - 底栏 → **§3.11 Action Bar v3（CSS 变量就近继承机制，单类覆盖 frame/modal/drawer）**
   - 顶栏 → §3.12 Navbar
3. **底栏决策（v3 重点）**：
   - 任意容器内底栏 → `.fb-action-bar`（v3 单类，CSS 变量就近继承自动切换行为）
   - 移动 frame 直接子层禁用 → 应走 `fb-navbar` 顶部 + 「···」菜单方案（proto_cross_platform §三）
   - phone-frame 内 modal → 自动 Sheet 形态（manifest §3.2 跨平台 — 不需要 PM 写 .fb-action-sheet 等自定义类！）
   - 禁 inline `position:fixed/sticky` / `bottom:0`（S4-28 v3 第 3 条）

### 分支 F — 多类组合

将组合拆分为多个独立查询，分别走 Q1。如「modal 弹框 + 内含表单 + 底部操作栏」拆为：
- 子查询 1: 容器 → modal（分支 E）
- 子查询 2: 表单 → FormRow + Input/Radio/Select（分支 B）
- 子查询 3: 底栏 → `.fb-action-bar`（分支 E）

每个子查询独立填表（§四 输出 5 部分）。

---

## 四、输出 5 部分模板（PM 填表写入模块子进度文件）

每次查询完，PM **必须**在 `process_record/progress/stage4_[产品名]_M[XX]_plan.md` 内「## fb-design-query 查询记录」段追加一条记录：

```markdown
### 查询 #N — [简短业务描述]

**Q1-Q8 答**: A2(modal 内) + 端 1(desktop) + 状态 1(default) + 规模 1(单条) + token 6(无)
+ 端规范 0(无) + 密度 3(主次操作)

**【推荐组件】** `.fb-action-bar`

**【用法示例】**（从 manifest §3.11 引用）：
```html
<div class="fb-modal-overlay is-visible">
  <div class="fb-modal">
    <div class="fb-modal-header">...</div>
    <div class="fb-modal-body">...</div>
    <div class="fb-action-bar">
      <button class="fb-btn fb-btn-default" data-tp="M[XX]-P[YY]-T[ZZ]">取消</button>
      <button class="fb-btn fb-btn-primary" data-tp="M[XX]-P[YY]-T[ZZ]">确认</button>
    </div>
  </div>
</div>
```

**【设计 token】**:
- padding: `12px 20px`（由 .fb-modal 容器覆盖 `--bar-padding` 自动取值）
- border-top: `1px solid var(--fb-border-1)`
- 按钮 token: `fb-btn-primary` / `fb-btn-default`

**【反 pattern】**:
- ❌ 不要写 `style="position:fixed; bottom:0"`（S4-28 v3 第 3 条 + check_inline_position_compliance）
- ❌ 不要叠加 `class="fb-modal-footer fb-action-bar"`（v2 deprecated 别名已自动继承）
- ❌ phone-frame 直接子层禁用 `.fb-action-bar`（违 proto_cross_platform §三）

**【关联场景】**:
- ⚠ phone-frame 内 modal 自动变 Action Sheet（manifest §3.2，跨平台无需特殊处理）
- ⚠ 主操作 `fb-btn-primary` 居右（INSTRUCTIONS.md 操作组排列规范）

**【D1-D5 约束】**:
- D1 字段: 按钮组（slot，1+ 个按钮）
- D2 状态: default
- D3 交互: 主次操作并列
- D4 语义: action-bar（底栏操作组）
- D5 约束: CSS 变量就近继承自动切换 frame/modal/drawer 行为；禁 inline position
```

**进度文件位置**: `process_record/progress/stage4_[产品名]_M[XX]_plan.md` 末尾段

**precheck 校验** (未来可选)：若加 check_fb_design_query_records，会扫该段 → 每个 PRD 章节是否有对应查询记录。

---

## 五、反 pattern 库（已知陷阱清单 — 必读避坑）

按 v2/v3 历史 NB / SNB 教训汇总：

### 跨平台陷阱

| 陷阱 | 真相 | 来源 |
|---|---|---|
| phone-frame 缺底栏类 | fb-modal 自动 Sheet（manifest §3.2）；phone-frame 直接子层应用 navbar + 「···」菜单 | NB-pub-phone-bar |
| modal 内底栏须用 fb-modal-footer | v3 deprecated；统一用 `.fb-action-bar`（自动适配 modal/drawer 静态行为）| S4-28 v3 |
| desktop / tablet 用 fb-frame-bottom-bar 单独 class | 同上，统一 `.fb-action-bar` | S4-28 v3 |
| 自定义 sheet / popup / modal-mask 类 | 禁用！必走 `.fb-modal-overlay + .fb-modal` 标准结构（precheck `check_panel_class_evasion`）| /retro 2026-05-13 #5 |

### inline 禁令

| 陷阱 | 真相 | 来源 |
|---|---|---|
| inline `position:fixed/sticky` 实现底栏 | 禁！由 `.fb-action-bar` CSS 变量管控 | S4-28 v3 第 3 条 |
| inline `z-index: 999` 等魔术数 | 禁！必从 `prd_expression_standard.md §零.1` 合法集合选（10/40/41/50/60/100/150/200/300）| `check_z_index_compliance` |
| inline `display:none/flex` 强制隐藏 / 显示 modal | 禁！默认隐藏（`.fb-modal-overlay` 真源），弹出态加 `.is-visible` 修饰类 | manifest §3.2 |
| inline `background:...` / `padding:...` 覆盖 token | 禁！必用真源 CSS 变量 / class | INSTRUCTIONS.md |

### 误叠加陷阱

| 陷阱 | 真相 | 来源 |
|---|---|---|
| `class="fb-modal-footer fb-frame-bottom-bar"` | 2 个 deprecated 别名叠加；统一 `.fb-action-bar` | S4-28 v3（quotation-tool 16 处实证）|
| `class="fb-modal fb-card"` | 不能混用（modal 是浮层，card 是容器，z-index 不同）| manifest §3.1/§3.2 |
| `class="fb-tag fb-chip"` | 不能混用（不同语义：tag 是标签，chip 是可关闭筹码）| pub_components_index §三 |

### 移动端布局陷阱

| 陷阱 | 真相 | 来源 |
|---|---|---|
| 移动端 frame 直接子层用 sticky 底栏 | 禁！应用 navbar 顶部 + 「···」菜单方案 | proto_cross_platform §三 |
| 移动端 ≥ 3 个操作并排展示 | 禁！收纳到 navbar 「···」菜单 | proto_cross_platform §三 |
| 触控目标 < 44px | 禁！移动端最小触控目标 44x44 | proto_platform_app.md §手机帧 |

### 数据展示陷阱

| 陷阱 | 真相 | 来源 |
|---|---|---|
| 数字输入用 fb-input(number) + 自定义加减按钮 | 禁！pub 无 stepper → 派生 proj | pub_components_index §4.2 |
| 多标签点选用 fb-tag + 自定义 click | 禁！pub 无 tag-multi-select → 派生 proj | pub_components_index §4.2 |
| 字段级错误用 toast | 禁！必用 `fb-hint(error)` + `fb-input(is-error)` | pub_components_index §4.3 |

---

## 六、典型场景路径示例

### 场景 1：modal 内底栏（最常见 + v2 16 处误叠加场景）

```
Q1: 容器/布局（E）
Q2: .fb-modal 内（2）
Q3: 跨端（6） — modal 自动适配（phone-frame 内变 Sheet）
Q4: 无特殊状态（1）
Q5: 单条（1）
Q6: 无 token 需求（已由真源管控）
Q7: 无端规范单独适配（modal 跨平台 by design）
Q8: 主次操作（3） — 1 primary + 1 default

→ 分支 E + Read manifest §3.11 Action Bar v3
→ 推荐组件: .fb-action-bar
→ 反 pattern 关键: 不叠加旧 .fb-modal-footer; 不写 inline position:fixed
→ 关联: phone-frame 内 modal 自动 Sheet（§3.2）— 无需特殊处理
```

### 场景 2：移动端列表项右侧操作

```
Q1: 操作/导航（D）
Q2: fb-list-item 内（无独立选项，按需 Read §4.4）
Q3: phone（3）
Q4: 无特殊状态（1）
Q5: 中量 5-20（3） — 列表
Q6: 无（用真源）
Q7: 移动端操作布局（4） → Read proto_cross_platform §三
Q8: 高频操作（5）

→ 分支 D + Read pub_components_index §4.4 + proto_cross_platform §三
→ 推荐组件: fb-list-item-extra 内含 fb-btn 系列
→ 反 pattern: 不要并排 ≥3 个按钮（应收纳「···」抽屉菜单）
→ 关联: 触控目标 ≥ 44px（proto_platform_app.md）
```

### 场景 3：数据加载中状态

```
Q1: 反馈/状态（C）
Q2: 独立 page（1）
Q3: 跨端（6）
Q4: 加载中（3） — 长时（整页骨架屏 / loading 容器）
Q5: 中量（3）
Q6: 无
Q7: 无
Q8: 无（仅加载视觉）

→ 分支 C + Read pub_components_index §4.3 + manifest §5 State
→ 推荐组件: .fb-state-loading
→ 反 pattern: 短时按钮加载用 fb-btn.is-loading（不用 fb-state-loading 整页级）
→ 关联: 骨架屏由 §零.4 / Foundation 子阶段二范式骨架自动渲染
```

---

## 七、与现有体系的边界（不重复维护知识）

本 skill 仅是**查询过程的结构化引导**。所有组件 / token / 端规范知识 SSOT 仍在原文件：

| 知识 SSOT | 文件 | skill 关系 |
|---|---|---|
| 组件 id 清单 + D1-D5 | `pub_components_index.md §三` | 终点 Read 引用 |
| 组件 HTML 模板 + 反 pattern | `fb-fallback-manifest.md §三` | 终点 Read 引用 |
| 场景反查 | `pub_components_index.md §四` | 分支 A-F 终点 Read 引用 |
| 能力维度反查 | `pub_components_index.md §五` | Q4-Q8 终点 Read 引用 |
| 设计 token | `bujue-design-system/tokens.md` + `INSTRUCTIONS.md` | Q6 终点 Read 引用 |
| 端规范 | `proto_platform_*.md` + `proto_cross_platform.md` | Q3/Q7 终点 Read 引用 |
| z-index / 面板/浮层 | `prd_expression_standard.md §零.1/§零.2.x` | Q6 终点 Read 引用 |

**禁止**: skill 内重复组件清单 / HTML 模板 / token 数值 / 端约束等。任何知识更新只改原 SSOT，skill 自动跟随（因 Read 引用）。

**SSOT 双锚 #52**: fb-design-query skill ↔ pub 库 4 层资源（组件 / token / 端规范 / PRD 表达）三锚关系（详 `ssot_anchors.md #52`）。

---

## 八、PM Agent 调用约定（强制路径）

### 子阶段五 Module PRD Agent — `[Must]` 调用

PM Agent 派发 prompt 中包含本 skill 路径 `pm-workflow/skills/fb-design-query/SKILL.md`，PM **必须**:

1. 开工前 Read 本 skill 全文 + 现有 reverse-lookup 资源（§四 / §五）
2. 写每段 PRD HTML 前，对每个组件需求按 Q1-Q8 走决策树
3. 每次查询记录到模块子进度文件「## fb-design-query 查询记录」段（按 §四 输出 5 部分模板）
4. PRD 章节内组件引用必须与本次查询记录的「推荐组件」一致
5. 若 PM 推断"pub 缺某能力" → 必须先按 Q3 端口维度 + Q7 端规范维度 Read 对应 proto_*.md 全文核查 → 若仍无 → 上报 NB-WE（按 SSOT #31 NB 上报 SOP）；**禁止**凭直觉推断（v3 NB-pub-phone-bar 错诊教训）

### 子阶段三 Module Spec Agent — `[Should]` 调用

PM Agent 派发 prompt 中**强建议**Read 本 skill 全文，写触点表 / 状态描述 / 业务规则涉及具体组件语义时按 Q1-Q8 走决策树。可不填查询记录（仅 [Should]）。

### Supervisor 审核项（§4.5）

- 抽样审查 PRD 章节是否与模块子进度文件「fb-design-query 查询记录」一致
- 检查记录段是否每个组件需求都有对应查询条目
- 若 PRD 内引用了未查询的组件 → 警示 PM 补查询（避免回到"凭直觉选 class"）

---

## 九、常见困惑（FAQ）

**Q: 我已熟悉 pub 库，每次都走 Q1-Q8 是否冗余？**
A: 即使熟悉，仍 [Must] 走决策树（PRD Agent 子阶段五）。v3 重构教训：v2 三 class 误叠加 16 处都是"PM 凭直觉"导致。决策树 = 强制核查路径 = 治本。

**Q: 决策树 Q6/Q7 维度太细，每次都答吗？**
A: Q6 token / Q7 端规范在"无需求"时可标"无"，仅当业务实际涉及才详查。Q1-Q5 + Q8 是骨架，必须答。

**Q: 推荐组件结果与 PM 经验冲突怎么办？**
A: 优先决策树结果（强制走真源 SSOT），若坚持认为错应**先派 Explore 调研真源**（核查 manifest / proto_*.md 实际定义）→ 若真矛盾则按 SSOT #31 NB 上报 SOP 写 NB-WE。**禁止**绕过决策树。

**Q: skill 内未覆盖的边缘场景怎么办？**
A: 走分支 F 多类组合 + 手动 Read manifest / index 全文。若仍找不到 → 必有"pub 无该能力 → 派生 proj"（参 `proj_component_protocol.md`）；prefer 派生 proj 而非自由发挥写 HTML。

**Q: 决策树本身错了 / 漏维度怎么办？**
A: 写 NB-WE 上报到 L2（走 workflow-evolution skill 修订本 SKILL.md），不擅自绕过 / 改 PRD。

---

**相关**: 
- [[s4-28-v3-action-bar-unification]] — v3 重构教训（NB-pub-phone-bar 错诊根源）
- [[feedback-pm-l2-root-cause-inference-unreliable]] — PM L2 推断 67% 错诊率根因
- [[skill-design-principle]] — skill 通过 Read SKILL.md 应用，不依赖 Skill 工具
- [[component-library-architecture]] — pub/proj 两层架构
