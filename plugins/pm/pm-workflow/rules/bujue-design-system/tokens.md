<!--
  不觉设计系统 — 基础 Tokens
  本文件是 PM 工作流阶段4的必传设计规范，是颜色/字体/间距/圆角/阴影的唯一权威来源。
  原始完整文件：bujue-design-system/COMPONENTS.md（备查，不传入工作流）
-->

> ⚠️ **内建兜底 pub 库（单库,2026-05-16 定案）**：本文件属于「pub 库（正式组件库,不觉设计系统）」的**内建兜底库** `pm-workflow/rules/bujue-design-system/`——工作流自带、git 跟踪长期保留,当前**唯一 pub 源,可走 `workflow-evolution` skill 直改**（**非**"外部接管 / 只读不可改"）。正式 pub 库接入为后续:终态由独立仓 `pm-group/bujue-design-system` 经 skill/CLI 消费(纯 Python CLI + 显式 `--root`,非 Read plugin),届时本库降离线 fallback,缺陷按 SSOT #31 NB 上报。详 `workflow_architecture_map.md §六` 组件库二元边界 + memory `pub_library_distribution_decision`。

## 基础规范

### 总则（优先级）

- **本文件是最高优先级视觉规范**：当产品定义或产品总监要求"按不觉规范/规则"时，优先使用这里的 tokens 与约定。
- **产品总监新增/修订优先**：产品总监后续提供的新规则覆盖同名条目。
- **微观对齐容差**：在图标内部对齐或单行文字垂直居中时，若 4px 网格导致视觉重心偏移，允许使用 0.5px 的微调位移，以视觉审美为最终验收标准。

### 颜色使用原则（重要）

- **主视觉以黑白灰为主**：除非产品总监明确要求，否则不要引入彩色做"主色/强调色"。
- **红色 `token(白版/错误色 #E60023)` 仅用于错误/危险语义**：如报错提示、危险操作（删除/不可逆）确认、校验错误状态。
- 其他颜色（如紫菜星球/盘八斗主色）**默认不用于该软件主流程 UI**，只有在产品总监明确指定业务场景需要时才使用。

### 适用范围（平台 + 主题）

### 平台（端）

- **平板**：文字样式见"文字样式（平板）"。圆角常用 **4**。
- **手机**：文字样式见"文字样式（手机）"。圆角常用 **4**。
- **Web**：文字样式见"文字样式（Web）"。圆角常用 **8**。

### 主题（白版/黑版）

白版 = 亮色主题；黑版 = 暗色主题。两者共用同一套语义命名，但具体颜色值/透明度不同。

使用约定：
- 需要同时支持两套主题时：**同一语义 token 在白版/黑版各取对应值**。
- 若只做单主题：按用户指定主题（默认白版）。

### 圆角规则（跨平台）

- **平板**：常用 `4`
- **手机**：常用 `4`
- **Web**：常用 `8`

> 若组件明确为胶囊/圆形头像：使用 `大圆角100`（与平台无关）。

### 字体家族（跨平台）

- 字体：**Source Han Sans CN**（Regular / Medium / Normal）
- 默认：`letterSpacing = 0%`（除非用户另行规定）

### 颜色 Tokens（语义名 → 值）

### 白版

- `白版/文字 #333`: `#333333` + `#000000 @20%`
- `白版/文字 #666`: `#666666`
- `白版/文字 #999`: `#999999`
- `白版/错误色 #E60023`: `#e60023`（仅错误/危险语义）
- `白版/禁用色 #ccc`: `#cccccc`
- `白版/白色 #FFF`: `#ffffff`
- `白版/背景色1级`: `#fafafa`
- `白版/背景色2级 #F5F5F5`: `#f5f5f5`
- `白版/背景色3级`: `#f1f1f1`
- `白版/背景色4级 EDEDED`: `#ededed`
- `白版/背景色5级 #E2E2E2`: `#e2e2e2`
- `白版/线框色1级 #EBEBEB`: `#ebebeb`
- `白版/线框色2级 #DBDBDB`: `#dbdbdb`
- `白版/选中色浅 #FDE6E9`: `#fde6e9`
- `白版/APP导航栏底部透明度 #FFF 80%`: `#ffffff @80%`

### 黑版

- `黑版/文字 #FFF 85%`: `#ffffff @85%`
- `黑版/文字 #FFF 65%`: `#ffffff @65%`
- `黑版/文字 #FFF 45%`: `#ffffff @45%`
- `黑版/禁用色  #FFF 25%`: `#ffffff @25%`
- `黑版/线框色 #FFF 15%`: `#ffffff @15%`
- `黑版/白色 #FFF 10%`: `#ffffff @10%`
- `黑版/白色 #FFF 8%`: `#ffffff @8%`
- `黑版/背景色1 #000`: `#000000`
- `黑版/背景色2 #151515`: `#151515`
- `黑版/图片底部图片预览色`: `#1f1f1f`
- `黑版/背景色3 #2A2A2A`: `#2a2a2a`
- `黑版/背景色4 #454545`: `#454545`
- `黑版/背景色5 #545454`: `#545454`
- `黑版/标签黑底#000 30%`: `#000000 @30%`
- `黑版/遮罩黑 #000 40%`: `#000000 @40%`
- `黑版/阴影黑 #000 8%`: `#000000 @8%`
- `黑版/阴影黑 #000 6%`: `#000000 @6%`
- `黑版/阴影黑 #000 4%`: `#000000 @4%`

### 其他品牌色（默认不使用）

- `紫菜星球`: `#8864de`
- `盘八斗主色`: `#3a7bff`

### 透明度写法（重要）

- `#RRGGBB @xx%` 表示 alpha。
- **代码输出规范**：所有的颜色 Token 必须转化为 `prd_template.html` 中已定义的 CSS 变量（`:root` 块），严禁直接输出 Hex 码。Token 语义名与 CSS 变量名对照：

| Token 语义名 | CSS 变量 | Hex 值 |
|---|---|---|
| `白版/文字 #333` | `var(--fb-text-primary)` | `#333333` |
| `白版/文字 #666` | `var(--fb-text-secondary)` | `#666666` |
| `白版/文字 #999` | `var(--fb-text-hint)` | `#999999` |
| `白版/禁用色 #ccc` | `var(--fb-text-disabled)` | `#cccccc` |
| `白版/错误色 #E60023` | `var(--fb-error)` | `#E60023` |
| `白版/错误浅色背景 #FEEDEF` | `var(--fb-error-bg-light)` | `#FEEDEF` |
| `白版/选中色浅 #FDE6E9` | `var(--fb-selected-light)` | `#FDE6E9` |
| `白版/白色 #FFF` | `var(--fb-white)` | `#ffffff` |
| `白版/背景色1级` | `var(--fb-bg-1)` | `#fafafa` |
| `白版/背景色2级 #F5F5F5` | `var(--fb-bg-2)` | `#f5f5f5` |
| `白版/背景色3级` | `var(--fb-bg-3)` | `#f1f1f1` |
| `白版/背景色4级 EDEDED` | `var(--fb-bg-4)` | `#ededed` |
| `白版/背景色5级 #E2E2E2` | `var(--fb-bg-5)` | `#e2e2e2` |
| `白版/线框色1级 #EBEBEB` | `var(--fb-border-1)` | `#ebebeb` |
| `白版/线框色2级 #DBDBDB` | `var(--fb-border-2)` | `#dbdbdb` |
| `白版/APP导航栏底部透明度 #FFF 80%` | `var(--fb-nav-bg)` | `rgba(255,255,255,0.8)` |

- 生成代码时：
  - **CSS**：优先用 `rgba(r,g,b,a)` 或 `#RRGGBBAA`
  - **Figma**：用颜色 + opacity/alpha

### 效果样式/阴影/模糊

- `白底阴影`: DROP_SHADOW `x=0 y=0 blur=12` `token(黑版/阴影黑 #000 6%)`
- `灰底阴影`: DROP_SHADOW `x=0 y=0 blur=12` `token(黑版/阴影黑 #000 4%)`
- `悬浮框阴影`: DROP_SHADOW `x=0 y=0 blur=12` `token(黑版/阴影黑 #000 8%)`
- `APP模糊+悬浮窗`: DROP_SHADOW `token(黑版/阴影黑 #000 8%)` + BACKGROUND_BLUR `80px`
- `APP导航栏模糊`: BACKGROUND_BLUR `80px`

### 文字样式（通用说明）

- **字重默认 Normal**：界面里**大多数文字**使用 **Normal** 作为默认字重；只有**少数需要区分层级或强调**的场景才用 **Regular / Medium** 等（例如样式表已命名的「标题 Medium」「TAB 选中 Medium」、弹窗标题变体等）。实现新界面或自选字重时，除非有明确设计意图，否则优先 Normal，避免随意混用字重。
- **多语言适配**：当渲染越南语（VN）时，若 lineHeight 导致字母上下溢出，允许在语义范围内微调 lineHeight 增加 2px 缓冲区。
- **默认正文跨端基线（新增）**：
  - Web 默认正文：`token(typo.body.web.default)`（`14/21`）
  - App（手机 + Pad）默认正文：`token(typo.body.app.default)`（`12/19`）
  - 仅当组件有明确独立文字规范（如输入态 `token(typo.body.input.app)`、大标题、备注 `token(typo.caption.default)` 等）时，才覆盖该基线。

> 单一来源：所有端（Pad/Web/手机）的详细文字样式与命名对齐，统一以「文字样式 Token 映射」为准，避免在多处重复维护。

### 文字样式 Token 映射（新增）

> 目的：将现有设计样式名与工程 token 命名一一对齐，便于 Figma / 代码双向映射。

### 平板（Pad）映射

- `标题/超大标题Medium` -> `token(typo.pad.title.xxxl.medium)` = `32/48`
- `标题/大标题Regular` -> `token(typo.pad.title.xl.medium)` = `20/30`
- `标题/中标题Regular` -> `token(typo.pad.title.l.medium)` = `18/27`
- `标题/小标题Medium` -> `token(typo.pad.title.m.medium)` = `14/21`
- `标题/小标题Regular` -> `token(typo.pad.title.m.regular)` = `14/21`
- `正文/正文大/常态Normal` -> `token(typo.pad.body.l.normal)` = `14/21`
- `正文/正文大/输入Normal` -> `token(typo.pad.body.l.input)` = `14/24`
- `正文/正文中/常态Normal` -> `token(typo.pad.body.m.normal)` = `12/19`
- `正文/正文中/多行Normal` -> `token(typo.pad.body.m.multiline)` = `12/21`
- `正文/正文中/输入Normal` -> `token(typo.pad.body.m.input)` = `12/24`
- `正文/正文小/常态Normal` -> `token(typo.pad.body.s.normal)` = `10/15`

### Web 映射

- `超大标题` -> `token(typo.web.title.xxxl.medium)` = `40/60`
- `大标题` -> `token(typo.web.title.xl.medium)` = `20/30`
- `大标题两行` -> `token(typo.web.title.xl.multiline)` = `20/36`
- `弹窗标题 Medium` -> `token(typo.web.modal.title.medium)` = `16/24`
- `弹窗标题 Regular` -> `token(typo.web.modal.title.regular)` = `16/24`
- `弹窗标题 Normal` -> `token(typo.web.modal.title.normal)` = `16/24`
- `正文常规14 Medium` -> `token(typo.web.body.l.medium)` = `14/21`
- `正文常规14 Regular` -> `token(typo.web.body.l.regular)` = `14/21`
- `正文常规14 Normal` -> `token(typo.web.body.l.normal)` = `14/21`
- `正文常规12 Normal` -> `token(typo.web.body.m.normal)` = `12/19`
- `正文常规12 Medium` -> `token(typo.web.body.m.medium)` = `12/19`
- `辅助信息 Normal` -> `token(typo.web.caption.normal)` = `10/15`
- `辅助信息 Regular` -> `token(typo.web.caption.regular)` = `10/15`
- `特殊` -> `token(typo.web.micro.regular)` = `8/12`

### 手机（Mobile）映射

- `标题超大 Regular` -> `token(typo.mobile.title.xl.regular)` = `20/30`
- `标题大 Regular` -> `token(typo.mobile.title.l.regular)` = `16/24`
- `标题 Regular` -> `token(typo.mobile.title.m.regular)` = `14/21`
- `标题 Normal` -> `token(typo.mobile.title.m.normal)` = `14/21`
- `标题小 Normal` -> `token(typo.mobile.title.s.normal)` = `12/19`
- `标题备注 Normal` -> `token(typo.mobile.caption.normal)` = `10/15`
- `TAB 选中` -> `token(typo.mobile.tab.selected.medium)` = `14/21`
- `TAB 未选中` -> `token(typo.mobile.tab.default.normal)` = `14/21`
- `正文大 常态` -> `token(typo.mobile.body.l.normal)` = `14/21`
- `正文大 输入` -> `token(typo.mobile.body.l.input)` = `14/24`
- `正文中 常态 Medium` -> `token(typo.mobile.body.m.medium)` = `12/19`
- `正文中 常态 Normal` -> `token(typo.mobile.body.m.normal)` = `12/19`
- `正文中 多行 Normal` -> `token(typo.mobile.body.m.multiline)` = `12/21`
- `正文中 输入` -> `token(typo.mobile.body.m.input)` = `12/24`
- `正文小 常态10` -> `token(typo.mobile.body.s.normal)` = `10/15`
- `正文小 分类卡片` -> `token(typo.mobile.body.s.cardRegular)` = `10/13`
- `正文小 常态8` -> `token(typo.mobile.micro.normal)` = `8/12`

### 变量集合（Figma Variables）

- Collection：模式包含 `4一级圆角`、`2二级圆角`、`大圆角100`（变量数=4）

### 全局尺寸/排版/间距 Tokens（新增）

> 规则：组件规范中出现尺寸、字号、行高、间距、圆角时，优先引用本节 token 名；原始数值仅作为对照值。

### 圆角

- `token(radius.level.2) = 4`
- `token(radius.level.4) = 8`
- `token(radius.pill) = 100`

### 边距规则（页面横向 padding / gutter，新增）

> 口径：这里的"边距"指页面内容区的左右内边距（gutter）。若业务页面有独立栅格/容器规范，则以页面规范为准。

- App（手机）通用横向边距：`token(layout.space.inline.mobile) = 16`
- App（Pad）通用横向边距：`token(layout.space.inline.pad) = 20`
- Web 通用横向边距：`token(layout.space.inline.web) = 32`
- 带图卡片横向边距：
  - App（手机/Pad）：`token(layout.space.card.media.inline.app) = 8`
  - Web：默认同 `token(layout.space.inline.web)`；紧凑布局可降级为 `8`

### 间距规则（节奏，新增）

- 项间距（普通条目之间）：
  - App：`token(layout.space.item.app) = 28`
  - Web：`token(layout.space.item.web) = 32`
- 卡片间距（纵向）：
  - App：文本类卡片 `token(layout.space.card.vertical.text.mobile) = 12`；图片类卡片 `token(layout.space.card.vertical.media.mobile) = 8`
  - Web：小卡片 `token(layout.space.card.vertical.web.small) = 12`；大卡片 `token(layout.space.card.vertical.web.large) = 20`

### 卡片大小定义（Web，仅用于区分纵向间距，新增）

- 小卡片：宽度 ≤ 200px（或宫格型/缩略图为主：资材宫格卡、文件卡等）
- 大卡片：宽度 > 200px（或通栏/图文组合/图片独占：媒体组合卡、全屏图片卡等）

### 结构层间距

- `token(layout.space.inline.app) = 20`
- `token(layout.space.inline.web) = 32`
- `token(layout.space.card.vertical.text.mobile) = 12`
- `token(layout.space.card.vertical.media.mobile) = 8`

### Navigation Bar（结构规范）

### 尺寸与间距
- App（手机 + Pad）导航栏高度：token(nav.height.app)
- 导航栏左右内边距：App token(layout.space.inline.app) / Web token(layout.space.inline.web)
- 底部分隔线：按任务要求决定（默认可去线）

### 导航栏与内容区间距规范（强制）

- **App（手机/Pad）**：导航栏底部到页面内容区顶部间距固定 `20px`。
- **Web**：导航栏底部到页面内容区顶部间距固定 `32px`。
- **执行说明**：
  - 该间距为全局统一值，所有页面必须遵循，不得自定义修改。
  - 若页面存在固定顶部导航栏，内容区必须预留此间距，避免内容被导航栏遮挡。
  - 特殊全屏页面（无导航栏）不受此规则限制，但必须在页面规范/PRD 中单独说明。

### 标题与返回
- 标题：token(typo.body.web.default)
- 标题左对齐（不使用绝对居中）
- 返回：仅 icon，不显示返回文字
- 返回 icon：token(nav.icon.size.app)

### 右侧操作区
- 支持文字按钮或 icon-only
- icon-only 按钮：24x24（App），图标尺寸 token(nav.icon.size.app)
- icon-only 默认无边框无描边（border: none）
- 文案按钮基线：token(typo.body.app.default)

### 字体排版（全局基线）

- `token(typo.body.web.default) = 14/21 Normal`
- `token(typo.body.app.default) = 12/19 Normal`
- `token(typo.body.input.app) = 12/24 Normal`
- `token(typo.body.input.web) = 14/21 Normal`
- `token(typo.caption.default) = 10/15 Normal`
- `token(typo.micro.default) = 8/12 Normal`

### Button 尺寸与图标（Web）

- `token(btn.size.height.xs/s/m/l/xl/xxl) = 20/28/32/40/48/56`
- `token(btn.size.paddingX.xs/s/m/l/xl/xxl) = 4/8/8/12/12/16`
- `token(btn.size.radius.default) = token(radius.level.4)`
- `token(btn.size.radius.pill) = token(radius.pill)`
- `token(btn.size.gap.iconText) = 4`
- `token(btn.icon.size.xs/s/m/l/xl/xxl) = 12/24/24/24/24/24`
- `token(btn.icon.gap.xs/s/m/l/xl/xxl) = 8/8/12/12/16/20`
- `token(btn.iconOnly.width.sm/md/lg/xl) = 28/40/48/60`
- `token(btn.mobile.dual.height) = 40`

### Card / Overlay
- `token(input.size.height.app) = 36`
- `token(input.size.height.web) = 40`
- `token(input.space.paddingX) = 12`
- `token(card.radius.web) = token(radius.level.4)`
- `token(card.radius.app) = token(radius.level.2)`
- `token(card.shadow.whiteBase) = 0 0 12 token(黑版/阴影黑 #000 6%)`
- `token(card.shadow.grayBase) = 0 0 12 token(黑版/阴影黑 #000 4%)`
- `token(card.mediaCombo.padding.app/web) = 4/8`
- `token(card.mediaCombo.gap.imageText) = 8`
- `token(card.mediaCombo.gap.text) = 12`
- `token(card.mediaCombo.gap.icon) = 8`
- `token(card.mediaCombo.size.selector) = 20`
- `token(card.assetTile.textAreaHeight) = 48`
- `token(card.assetTile.icon.empty/add) = 40/24`
- `token(card.toolbar.size.button/icon) = 24/24`
- `token(card.toolbar.gap.button) = 12`
- `token(card.badge.offset.edge) = 12`
- `token(card.badge.size.single) = 28x28`
- `token(card.badge.size.multiHeight) = 28`
- `token(card.badge.blur) = 10`
- `token(card.badge.iconCanvas) = 24`
- `token(card.badge.gap.icon) = 4`
- `token(card.badge.paddingX) = 12`
- `token(layout.space.card.media.inline.app) = 8`
- `token(overlay.blur.strong) = 20`
- `token(overlay.blur.app.nav) = 80`

---

## 设计迭代压缩：常用间距/留白速查 + 交互态标准（下游批 4 项 8）

> **诚实边界**：纯主观审美迭代（配色微调、留白手感、视觉权重）**无法事前完全归零**——这类来回是设计的固有成本。但**常用间距 / 留白**和**交互态视觉**有客观标准，把它们明确下来可把"反复来回"压缩到"一次到位"。本节是 PM 阶段 4 取值的**默认标准**：除非业务有特殊理由，**先用本节默认值，不要逐页重新拍脑袋**。

### 常用间距 / 留白速查（默认取值，详值见上方各「间距规则 / 边距规则 / 结构层间距」节，本表为使用导向汇总，勿改值）

| 场景 | App（手机）| App（Pad）| Web | token 名 |
|------|-----------|-----------|-----|---------|
| 页面横向边距（gutter）| `16` | `20` | `32` | `layout.space.inline.{mobile/pad/web}` |
| 普通条目项间距 | `28` | `28` | `32` | `layout.space.item.{app/web}` |
| 文本类卡片纵向间距 | `12` | `12` | `12`（小）/ `20`（大）| `layout.space.card.vertical.text.mobile` / `.web.{small/large}` |
| 图片类卡片纵向间距 | `8` | `8` | `8` | `layout.space.card.vertical.media.mobile` |
| 导航栏底→内容区顶 | `20` | `20` | `32` | （强制全局值，见「导航栏与内容区间距规范」）|
| 圆角 | `4`（App 卡片）| `4` | `8`（Web 卡片）| `radius.level.{2/4}` / `radius.pill=100` |

> **取值纪律**：上表是默认；如某页确需偏离，须有业务理由（如紧凑列表降级为 `8`），不得为"看起来更好看"随手改——审美偏好走终审反馈，不在生产期反复试。

### 交互态标准（hover / focus / selected / active / disabled，真源 `fb-fallback.css`）

> 以下是 `fb-fallback.css` 已落地的交互态约定，PM 写 proj 组件 / inline 交互态时**沿用同一套视觉语言**，不要为同类交互发明新配色（这是"反复来回"的高发区）。色值一律用 `--fb-*` 变量，禁魔术色。

| 交互态 | 视觉标准 | 适用 |
|--------|---------|------|
| **hover**（悬停反馈）| 背景 `var(--fb-bg-2)`；幽灵按钮 `var(--fb-bg-3)`；主按钮 / 危险按钮加深各自主色 | 可点击项（列表项 / 选项 / 行 / 次级按钮 / 链接）|
| **focus**（输入聚焦）| 去默认 outline + 边框 `var(--fb-text-primary)`；错误态边框 `var(--fb-error)` | input / textarea / select |
| **selected**（选中态）| 背景 `var(--fb-bg-3)` + 文字 `var(--fb-text-primary)` + `font-weight: 500` | 多选 / 单选列表项、下拉选项、表格行 |
| **active**（激活 / 当前态）| 背景 `var(--fb-text-primary)` + 文字 `var(--fb-white)`（反白强调）| 分页当前页、Tab 当前项等"当前位置"强调 |
| **disabled**（禁用）| 背景 `var(--fb-bg-2)` + 文字 `var(--fb-text-disabled)` + `cursor: not-allowed` | 任何禁用控件 |

> **selected vs active 区分**：`selected` = 用户**勾选 / 多选**的结果（弱强调，浅灰底）；`active` = 系统**当前所处位置**（强强调，反白）。二者视觉不可混用——混用是跨帧状态命名不一致（PRD §5.4 视觉一致性自审项）的常见诱因。

### Skeleton 尺寸 Tokens（骨架屏 padding / circle / row，跨平台默认值）

> **取值依据**：下游产品 PRD 中 skeleton padding inline 散乱实证（同平台 padding 差异率 ≥ 50%），按"频次中位数法"收敛跨平台默认值——phone 32px 高频 / desktop 48px 32px 中位 / h5 40px 24px 实例 / modal 24px 16px 收敛极端。**取值纪律**：除业务有特殊理由，**先用本节默认值**，不要逐页 inline 覆盖（与 `fb-fallback.css` 字号体系 + `prd_template.html` `.interaction-card` 段同模式 — 模板硬编码 + token 化集中管理 vs PM 在 drafts inline 散乱）。

| Token | 默认值 | 适用 |
|-------|--------|------|
| `--skel-phone-padding` | `32px` | 手机端 skeleton 容器 padding |
| `--skel-phone-circle` | `80px` | 手机端 skeleton 圆头像直径 |
| `--skel-phone-row` | `24px` | 手机端 skeleton 文本行高 |
| `--skel-desktop-padding` | `48px 32px` | 桌面端 skeleton 容器 padding（垂直/水平） |
| `--skel-desktop-circle` | `120px` | 桌面端 skeleton 圆头像直径 |
| `--skel-desktop-row` | `28px` | 桌面端 skeleton 文本行高 |
| `--skel-h5-padding` | `40px 24px` | H5 端 skeleton 容器 padding |
| `--skel-h5-row` | `24px` | H5 端 skeleton 文本行高 |
| `--skel-modal-padding` | `24px 16px` | modal 内 skeleton 容器 padding（收敛极端值） |
| `--skel-modal-row` | `20px` | modal 内 skeleton 文本行高 |

**Why**：跨产品 PRD 中 skeleton padding inline 散乱（下游产品实证），token 化集中管理后下游重 assemble 时自然受益（不强制旧 PRD 重生）。配套 `prd_template.html` :root 加变量声明 + 平台 selector CSS 自动应用，PM 在 drafts 中默认继承（与 SSOT #62 E.3 inline 字号防御同治理思路）。
