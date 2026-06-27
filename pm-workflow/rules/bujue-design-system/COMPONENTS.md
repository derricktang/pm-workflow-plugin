<!--
  ⚠️ 此文件不是 PM 工作流的直接传入资源。
  PM 工作流中请使用拆分后的文件：
    - 基础规范/Tokens → bujue-design-system/tokens.md
    - 组件规范（按需） → bujue-design-system/components/*.md
  本文件保留作为完整设计系统备查文档。
-->

> ⚠️ **内建兜底 pub 库（单库,2026-05-16 定案）**：本文件属于「pub 库（正式组件库,不觉设计系统）」的**内建兜底库** `pm-workflow/rules/bujue-design-system/`——工作流自带、git 跟踪长期保留,当前**唯一 pub 源,可走 `workflow-evolution` skill 直改**（**非**"外部接管 / 只读不可改"）。正式 pub 库接入为后续:终态由独立仓 `pm-group/bujue-design-system` 经 skill/CLI 消费(纯 Python CLI + 显式 `--root`,非 Read plugin),届时本库降离线 fallback,缺陷按 SSOT #31 NB 上报。详 `workflow_architecture_map.md §六` 组件库二元边界 + memory `pub_library_distribution_decision`。

# 不觉设计系统：组件规范

> 本文件包含「基础规范 + 组件规范」。页面结构规范见 `SKILL.md`。

## 基础规范

### 总则（优先级）

- **本技能是最高优先级视觉规范**：当用户要求“按不觉规范/规则”时，优先使用这里的 tokens 与约定。
- **用户新增/修订优先**：用户后续提供的新规则覆盖同名条目。
- **微观对齐容差**：在图标内部对齐或单行文字垂直居中时，若 4px 网格导致视觉重心偏移，允许使用 0.5px 的微调位移，以视觉审美为最终验收标准。

### 颜色使用原则（重要）

- **主视觉以黑白灰为主**：除非用户明确要求，否则不要引入彩色做“主色/强调色”。
- **红色 `token(白版/错误色 #E60023)` 仅用于错误/危险语义**：如报错提示、危险操作（删除/不可逆）确认、校验错误状态。
- 其他颜色（如紫菜星球/盘八斗主色）**默认不用于该软件主流程 UI**，只有在用户明确指定业务场景需要时才使用。

### 适用范围（平台 + 主题）

### 平台（端）

- **平板**：文字样式见“文字样式（平板）”。圆角常用 **4**。
- **手机**：文字样式见“文字样式（手机）”。圆角常用 **4**。
- **Web**：文字样式见“文字样式（Web）”。圆角常用 **8**。

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
- **代码输出规范**：所有的颜色 Token 必须转化为项目中的 CSS 变量（如 `var(--fb-text-333)`），严禁直接输出 Hex 码。
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

> 口径：这里的“边距”指页面内容区的左右内边距（gutter）。若业务页面有独立栅格/容器规范，则以页面规范为准。

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

## 所有组件

### 命名约定（组件/变体）

- 组件：`业务前缀-组件名`（例：`创意版-素材卡`）
- 变体属性：中文业务语义（例：`状态`、`尺寸`、`类型`）
- 变体值：中文（例：`默认`、`添加`、`禁用`、`选中`）

### Button（通用规则）

#### 角色模型（Role Model）
- `Primary`：同一操作组仅允许 `1` 个主操作。
- `Secondary`：同级次操作；按背景对比选择浅底/描边/文字等样式承载。
- `Text`/`Ghost`：弱化操作（按端实现选其一或同时存在，保持命名一致）。
- `Icon-only`：仅图标操作，需保证热区与可点击性。

#### 状态（States）
- 必备：`default / disabled`
- Web 追加：`hover / active`
- 预留扩展口：`focus / loading`

#### Loading（强制）

- **统一加载动画**：使用 `https://uiverse.io/dovatgabriel/kind-cougar-54` 的加载动画（工程实现时按项目方式内联/组件化，但视觉与节奏必须一致）。
- **按钮加载态规则**：
  - 按钮触发接口请求/提交等待时，按钮必须进入 `loading` 状态。
  - 加载动画放在按钮内容区域正中（水平/垂直居中），通常以加载动画替换按钮文字，避免按钮宽高抖动与布局偏移。
  - 禁止使用自定义 GIF、文字加载、原生浏览器加载动画代替。

#### 约束
- 同一页面同一类按钮：尺寸/圆角/状态策略必须一致。
- 禁用态只表达“不可点”，不改变信息架构（文案不换语义）。

### Button（Pad 基线 + 手机补充）

#### Pad 样式库（default / disabled）
- `Style-1 TextOnly`：`bg none / text token(白版/文字 #333) / border none`；disabled=`bg token(白版/禁用色 #ccc) / text token(白版/白色 #FFF) / border none`
- `Style-2 SolidDark`：`bg token(白版/文字 #333) / text token(白版/白色 #FFF) / border none`；disabled=`bg token(白版/禁用色 #ccc) / text token(白版/白色 #FFF) / border none`
- `Style-3 Outline`：`bg none / text token(白版/文字 #333) / border 1px token(白版/线框色1级 #EBEBEB)`；disabled=`bg token(白版/禁用色 #ccc) / text token(白版/白色 #FFF) / border none`
- `Style-4 SolidLight`：`bg token(白版/白色 #FFF) / text token(白版/文字 #333) / border none`；disabled=`bg token(白版/禁用色 #ccc) / text token(白版/白色 #FFF) / border none`
- `Style-5 SolidSoft`：`bg token(白版/背景色2级 #F5F5F5) / text token(白版/文字 #333) / border none`；disabled=`bg token(白版/禁用色 #ccc) / text token(白版/白色 #FFF) / border none`
- `Style-6 OutlineStrong`：`bg none / text token(白版/文字 #333) / border 1px token(白版/线框色2级 #DBDBDB)`；disabled=`bg token(白版/禁用色 #ccc) / text token(白版/白色 #FFF) / border none`

#### 映射与选择规则
- `Primary = Style-2`
- `Secondary = Style-4/5/3/1/6` 动态选择
- 白底优先：`Style-3/1/6`
- 灰底/深底优先：`Style-4`
- 强调操作优先：`Style-2`

#### Pad 尺寸与字体
- 尺寸：`S/M/L/XL`
- 高度：`24 / 28 / 36 / 40`（建议沉淀为 `token(btn.pad.size.height.s/m/l/xl)`）
- 左右 padding：`8 / 8 / 8 / 24`（建议沉淀为 `token(btn.pad.size.paddingX.s/m/l/xl)`）
- 圆角：`S/M/L=token(radius.level.2)`，`XL=token(radius.pill)`
- Icon-only 容器：`24 / 28 / 36 / 40`
- Icon-only icon：`14 / 16 / 20 / 20`
- 按钮文案：`token(typo.body.app.default)`

#### Mobile 专属按钮（双触发按钮）
- 组件：`DualActionButton`（仅手机）
- 总高度：`40`（`token(btn.mobile.dual.height)`），左右双分区，外形胶囊（大圆角 `token(radius.pill)`）
- 左区（分享）：`bg = token(白版/背景色5级 #E2E2E2)`，padding=`8`，文案区宽=`86`，文案色=`token(白版/文字 #333)`
- 右区（采购）：`bg = token(白版/文字 #333)`，padding=`8`，宽=`102`，文案色=`token(白版/白色 #FFF)`
- 两行文案：
  - 主文案：`token(typo.body.app.default)`
  - 副文案：`token(typo.micro.default)`
- disabled：左右统一 `bg = token(白版/禁用色 #ccc)`，主副文案统一 `token(白版/白色 #FFF)`

#### 状态
- 状态口径见 `Button（通用规则）`。

### Button（Web版）

#### 命名规则（Token-first）
- 本章节所有颜色/边框/文字色一律使用 token 名，不直写 Hex。
- 推荐代码映射：`token(语义名)` -> `var(--fb-*)`（命名由项目实现层落地）。
- 允许在评审文档中保留“语义名 + 原值”用于对照，但工程实现只写变量。

#### Web Button Token 别名（Alias）
- `btn.color.text.default` -> `token(白版/文字 #333)`
- `btn.color.text.inverse` -> `token(白版/白色 #FFF)`
- `btn.color.text.disabled` -> `token(白版/白色 #FFF)`
- `btn.color.bg.primary` -> `token(白版/文字 #333)`
- `btn.color.bg.primaryHover` -> `token(黑版/背景色1 #000)`
- `btn.color.bg.disabled` -> `token(白版/禁用色 #ccc)`
- `btn.color.bg.soft` -> `token(白版/背景色2级 #F5F5F5)`
- `btn.color.bg.softHover` -> `token(白版/背景色5级 #E2E2E2)`
- `btn.color.bg.white` -> `token(白版/白色 #FFF)`
- `btn.color.bg.darkL3` -> `token(黑版/背景色3 #2A2A2A)`
- `btn.color.bg.darkL4` -> `token(黑版/背景色4 #454545)`
- `btn.color.bg.darkL4Hover` -> `token(黑版/背景色5 #545454)`
- `btn.color.bg.error` -> `token(白版/错误色 #E60023)`
- `btn.color.bg.overlayBlack30` -> `token(黑版/标签黑底#000 30%)`
- `btn.color.bg.overlayWhite08` -> `token(黑版/白色 #FFF 8%)`
- `btn.color.bg.overlayWhite10` -> `token(黑版/白色 #FFF 10%)`
- `btn.color.border.l1` -> `token(白版/线框色1级 #EBEBEB)`
- `btn.color.border.l2` -> `token(白版/线框色2级 #DBDBDB)`

#### A. 角色模型（Role Model）
- 角色模型见 `Button（通用规则）`。

#### B. 表现样式库（Appearance Styles）
- `Style-1 (TextOnly)`：
  - default: `bg none / text btn.color.text.default / border none`
  - disabled: `bg btn.color.bg.disabled / text btn.color.text.disabled / border none`
  - hover: `bg btn.color.bg.soft`
- `Style-2 (Black)`：
  - default: `bg btn.color.bg.primary / text btn.color.text.inverse / border none`
  - disabled: `bg btn.color.bg.disabled / text btn.color.text.disabled / border none`
  - hover: `bg btn.color.bg.primaryHover`
- `Style-3 (Outline 1)`：
  - default: `bg none / text btn.color.text.default / border 1px solid btn.color.border.l1`
  - disabled: `bg btn.color.bg.disabled / text btn.color.text.disabled / border none`
  - hover: `bg btn.color.bg.soft / text btn.color.text.default / border none`
- `Style-4 (Outline 2)`：
  - default: `bg none / text|icon btn.color.text.default / border 1px solid btn.color.border.l2`
  - disabled: `bg btn.color.bg.disabled / text btn.color.text.disabled / border none`
  - hover: `bg btn.color.bg.soft / text|icon btn.color.text.default / border none`
- `Style-5 (White)`：
  - default: `bg btn.color.bg.white / text btn.color.text.default / border none`
  - disabled: `bg btn.color.bg.disabled / text btn.color.text.disabled / border none`
  - hover: `bg btn.color.bg.soft / text btn.color.text.default / border none`
- `Style-6 (Black 30%)`：
  - default: `bg btn.color.bg.overlayBlack30 / icon-color btn.color.text.inverse / border none / bg blur 20`
  - disabled: `bg btn.color.bg.disabled / icon-color btn.color.text.inverse / border none / bg blur 20`
  - hover: `bg btn.color.bg.overlayWhite08 + btn.color.bg.overlayBlack30`
- `Style-7 (Dark background level 3)`：
  - default: `bg btn.color.bg.darkL3 / icon-color btn.color.text.inverse / border none`
  - disabled: `bg btn.color.bg.disabled / icon-color btn.color.text.inverse / border none`
  - hover: `bg btn.color.bg.darkL4`
- `Style-8 (Dark background level 4)`：
  - default: `bg btn.color.bg.darkL4 / icon-color btn.color.text.inverse / border none`
  - disabled: `bg btn.color.bg.disabled / icon-color btn.color.text.inverse / border none`
  - hover: `bg btn.color.bg.darkL4Hover`
- `Style-9 (F5)`：
  - default: `bg btn.color.bg.soft / text|icon btn.color.text.default / border none`
  - disabled: `bg btn.color.bg.disabled / icon-color btn.color.text.inverse / border none`
  - hover: `bg btn.color.bg.softHover`
- `Style-10 (Red)`：
  - default: `bg btn.color.bg.error / text btn.color.text.inverse / border none`
  - disabled: `bg btn.color.bg.disabled / icon-color btn.color.text.inverse / border none`
  - hover: `bg btn.color.bg.overlayWhite10 + btn.color.bg.error`

#### C. 角色到样式映射（Role -> Style）
- `Primary = Style-2 (Black)`
- `Secondary =` 动态（`Style-3 / Style-4 / Style-5 / Style-6 / Style-7 / Style-8 / Style-9`）
- `Text =` 动态（按页面底色和对比度选择）
- `Icon-color =` 动态（每个样式均可使用，按页面对比选择）
- `Icon-only =` 动态（每个样式均可使用，按页面对比选择）

#### D. 对比选择规则（Contrast Rules）
- 白底场景：优先 `Style-2 (Black)`；辅助 `Style-1/2/3/4/5`
- 灰底场景：优先 `Style-2 (Black)`；辅助 `Style-1/2/3/4/5`
- 暗底场景：优先 `Style-10 (Red)`；辅助 `Style-1/7/8`
- 强调操作：亮底使用 `Style-2 (Black)`，暗底使用 `Style-10 (Red)`
- 禁止项：同一操作组中出现多个主强调按钮。

#### E. 尺寸（Sizes）
- 尺寸档位：`XS / S / M / L / XL / XXL`
- 高度：`token(btn.size.height.xs/s/m/l/xl/xxl)`
- 左右 padding：`token(btn.size.paddingX.xs/s/m/l/xl/xxl)`
- 图标 + 文字时：icon 侧减 padding `token(btn.size.gap.iconText)`
- 圆角：`XS` 支持 `token(btn.size.radius.pill)`；其他型号统一 `token(btn.size.radius.default)`；如使用 `token(btn.size.radius.pill)`，左右 padding 额外 `+4`
- icon 与文案间距：`token(btn.size.gap.iconText)`
- 边框：有边框样式统一 `1px solid`

#### F. 图标规则（Icon Rules）
- `XS20`：左/右图标 `token(btn.icon.size.xs)`，gap=`token(btn.icon.gap.xs)`
- `S28`：左/右图标 `token(btn.icon.size.s)`，gap=`token(btn.icon.gap.s)`
- `M32`：左/右图标 `token(btn.icon.size.m)`，gap=`token(btn.icon.gap.m)`
- `L40`：左/右图标 `token(btn.icon.size.l)`，gap=`token(btn.icon.gap.l)`
- `XL48`：左/右图标 `token(btn.icon.size.xl)`，gap=`token(btn.icon.gap.xl)`
- `XXL56`：左/右图标 `token(btn.icon.size.xxl)`，gap=`token(btn.icon.gap.xxl)`
- `Icon-only` 宽度：`token(btn.iconOnly.width.sm/md/lg/xl)`
- `Icon-only` 无文案：是（仅图标）

#### G. 字体（Typography）
- `XS`：文案 `token(typo.caption.default)`，字重 `Normal`，字间距 `0%`
- `S`：文案 `token(typo.body.app.default)`，字重 `Normal`，字间距 `0%`
- `M / L / XL / XXL`：文案 `token(typo.body.web.default)`，字重 `Normal`，字间距 `0%`

#### H. 状态（States）
- 状态口径见 `Button（通用规则）`。

#### I. 推荐实现变量（Web）
- 尺寸：
  - `--fb-btn-height-xs/s/m/l/xl/xxl: token(btn.size.height.xs/s/m/l/xl/xxl)`
  - `--fb-btn-padding-x-xs/s/m/l/xl/xxl: token(btn.size.paddingX.xs/s/m/l/xl/xxl)`
  - `--fb-btn-radius-default: token(btn.size.radius.default)`
  - `--fb-btn-radius-pill: token(btn.size.radius.pill)`
  - `--fb-btn-gap-icon-text: token(btn.size.gap.iconText)`
- 字体：
  - `--fb-btn-font-size-xs / line-height-xs: token(typo.caption.default)`
  - `--fb-btn-font-size-s / line-height-s: token(typo.body.app.default)`
  - `--fb-btn-font-size-m-l-xl-xxl / line-height-m-l-xl-xxl: token(typo.body.web.default)`
  - `--fb-btn-font-weight: 400`
- 图标：
  - `--fb-btn-icon-xs: token(btn.icon.size.xs)`
  - `--fb-btn-icon-s/m/l/xl/xxl: token(btn.icon.size.s/m/l/xl/xxl)`
  - `--fb-btn-icon-gap-xs/s/m/l/xl/xxl: token(btn.icon.gap.xs/s/m/l/xl/xxl)`
  - `--fb-btn-icon-only-width-sm/md/lg/xl: token(btn.iconOnly.width.sm/md/lg/xl)`

### Input（补全）

#### 语义色
- default/focus text：`token(白版/文字 #333)`
- disabled text：`token(白版/禁用色 #ccc)`
- error text：`token(白版/错误色 #E60023)`
- placeholder：`token(白版/文字 #999)`

#### 背景与边框
- 背景：`none / token(白版/白色 #FFF) / token(白版/背景色2级 #F5F5F5)`（按父背景对比选择）
- default border：`token(白版/线框色1级 #EBEBEB)` 或 `token(白版/线框色2级 #DBDBDB)`
- focus border：`token(白版/文字 #333)`
- error border：`token(白版/错误色 #E60023)`
- disabled border：`none`

#### 尺寸与字体
- Pad/手机：`h=36`（`token(input.size.height.app)`），`radius=token(radius.level.2)`，`padding-x=12`（`token(input.space.paddingX)`）
- Web：`h=40`（`token(input.size.height.web)`），`radius=token(radius.level.4)`，`padding-x=12`（`token(input.space.paddingX)`）
- Pad/手机输入文案：`token(typo.body.input.app)`
- Web 输入文案：`token(typo.body.input.web)`

#### Readonly
- 背景：`token(白版/白色 #FFF)` 或 `token(白版/背景色2级 #F5F5F5)`
- 文字：`token(白版/文字 #333)`
- 边框：`token(白版/线框色1级 #EBEBEB)`
- 可聚焦：是（仅显示光标，不改变样式）

#### 错误提示文案
- 字体：与输入正文一致
- 颜色：`token(白版/错误色 #E60023)`
- 与输入框间距：下 `4`
- 不预留固定占位高度

#### 前后缀/清除图标
- icon 尺寸：Web=`24`，App=`20`
- icon 颜色：default=`token(白版/文字 #333)`，disabled=`token(白版/禁用色 #ccc)`，error=`token(白版/错误色 #E60023)`
- icon 与文本间距：`4`
- 有 icon 时左右内边距在基础值上减 `4`
- 清除按钮显示：按场景（可常显或 focus 显示）

### Tag / Tab（Pad / 手机）

> 来源：`tag-tab规范(1).txt` **v1.1（文案优化版）**。统一用于**移动端组件库**（Pad + 手机）。存在多种实现时采用 **推荐值 + 可选值 + 使用条件**。  
> **语义**：**Tag** 用于筛选/标记；**Tab** 用于同级内容切换。

#### Tag 组件

**类型（Type）**  
- `Normal`（普通） / `Selected`（选中） / `Disabled`（禁用） / `Closable`（可关闭）  
- `Closable` 为 Normal/Selected 的扩展态，右侧增加关闭图标（x）。

**字体**  
- 字号 `12px`，行高 `19px`，字重 Normal（对齐 `token(typo.body.app.default)` 字号/行高时可映射）。

**文字颜色**

| 容器背景 | Default | Selected | Disabled |
|----------|---------|----------|----------|
| 白底 `#FFFFFF` | `#666666` | `#333333` | `#CCCCCC` |
| 灰底 `#F5F5F5` | `#666666` | `#333333`（白底选中块）/ `#FFFFFF`（深色底选中块） | `#CCCCCC` |

**背景与边框**

| 容器 | Default | Selected | Disabled |
|------|---------|----------|----------|
| 白底 | 背景 `#FFFFFF`，边框 `#EBEBEB` | 背景 `#F1F1F1`，无边框 | 背景 `#FFFFFF`，边框 `#EBEBEB` |
| 灰底 | 背景/边框均为 none | 背景 `#FFFFFF`（白底）或 `#333333`（深色底），无边框 | 背景/边框均为 none |

**圆角**  
- 常规：`4px`（对齐 `token(radius.level.2)`）  
- 胶囊：`100px`（对齐大圆角/胶囊）

**尺寸与间距（Pad / 手机）**  
- 高度：`24` / `36` / `40`  
- 标签间距：`12px`（推荐）/ `16px`（宽松布局）

**图标（图标 + 文字）**  
- 图标尺寸：`20px`  
- 图标侧内边距在纯文案基础上 **减少 4px**

**内边距细则**

- **图标在右（如 Closable）**  
  - 高 24：字-图间距 `4`；`pl 8` / `pr 4`  
  - 高 36 / 40：字-图间距 `4`；`pl 12` / `pr 8`  
- **图标在左**  
  - 高 24：字-图间距 `0`；`pl 4` / `pr 8`  
  - 高 36 / 40：字-图间距 `0`；`pl 8` / `pr 12`  
- **纯文字**  
  - 高 24：左右 `8`；高 36 / 40：左右 `12`

#### Tab 组件

**通用状态**  
- `Default`（未选中） / `Selected`（选中） / `Disabled`（禁用）

##### 下划线型 Tab（顶部导航栏）

**字体**  
- 字号 `14px`，行高 `21px`  
- 字重：未选中 Normal / 选中 Medium

**文字颜色**

| 容器 | Default | Selected | Disabled |
|------|---------|----------|----------|
| 白底 `#FFFFFF` | `#666666` | `#333333` | `#CCCCCC` |
| 灰底 `#F5F5F5` | `#666666` | `#333333` | `#CCCCCC` |
| 黑底 `#000000` | `#FFFFFF` @65% | `#FFFFFF` | `#FFFFFF` @25% |

**背景**：各状态均为 none。

**尺寸与布局（Pad / 手机）**  
- 两个 Tab：`40px` 文字间距；超过两个：`24px`。

##### 胶囊型 Tab（分段切换等）

**字体**  
- 字号 `12px`，行高 `19px`，字重 Normal（未选/选中/禁用一致）。

**文字颜色（节选）**  
- 白底：Default `#666666`（白选中底）或 `#333333`（深色选中底）；Selected 对应互换；Disabled `#CCCCCC`。  
- 灰底：同上逻辑。  
- 黑底：Default `#FFFFFF` @85%；Selected `#FFFFFF`；Disabled `#FFFFFF` @25%。

**背景与底板**  
- 白底：未选中/禁用背景 none；选中背景 `#333333` 或 `#FFFFFF`；胶囊底板 `#F5F5F5`。  
- 灰底：选中背景 `#333333` 或 `#FFFFFF`；胶囊底板 `#EDEDED`。  
- 黑底：选中背景 `#FFFFFF` @25%；胶囊底板 `#FFFFFF` @15%。

**圆角**  
- 常规 `4px`；胶囊 `100px`。

**尺寸与布局（Pad / 手机）**  
- 高度：`28` / `32` / `36`  
- 容器内边距：`2px`  
- 按钮间距：`0`

**图标（图标 + 文字）**  
- 图标 `20px`；图标侧内边距在纯文案基础上 **减 4px**

**内边距细则（胶囊）**

- **图标在右**：高 28/32 → `pl 12` `pr 8`；高 36 → `pl 16` `pr 12`（字-图间距均为 4）。  
- **图标在左**：高 28/32 → `pl 8` `pr 12`；高 36 → `pl 12` `pr 16`（字-图间距 0）。  
- **纯文字**：高 28/32 → 左右 `12`，最小宽 `48`；高 36 → 左右 `16`，最小宽 `56`；超长宽度自适应。

**等宽规则（多按钮）**  
- 同组 Tab 等宽，宽度取组内**最长文案按钮**。

### Card（结构分类）

#### 分类
- `Image-only Card`
- `Media Combo Card`
- `File Card`
- `Asset Tile Card`

#### 通用规则
- 图片比例：`1:1 / 16:9 / 3:2`
- 背景：`none / token(白版/白色 #FFF) / token(白版/背景色2级 #F5F5F5)`（按对比）
- 当背景为 `none` 时，至少通过 `边框/阴影/遮罩/留白` 之一保证边界可识别。
- 选择控件统一：`20x20`
- 文案最多 `2` 行，超出省略号
- 圆角：Web=`8`，App=`4`
- 阴影：
  - 底 `token(白版/白色 #FFF)`：`0 0 12 token(黑版/阴影黑 #000 6%)`
  - 底 `token(白版/背景色2级 #F5F5F5)`：`0 0 12 token(黑版/阴影黑 #000 4%)`

#### 卡片内间距规则（强制）

- 文本与文本之间（段落/多行）：上下间距 `4px`。
- 文本与其他元素（图片/按钮/分隔线）之间：上下间距 `8px`。

#### Media Combo 间距（已定）
- Pad/手机：padding=`4`（`token(card.mediaCombo.padding.app)`），图文间距=`8`（`token(card.mediaCombo.gap.imageText)`）
- Web：padding=`8`（`token(card.mediaCombo.padding.web)`），图文间距=`8`（`token(card.mediaCombo.gap.imageText)`）
- 右侧元素间距：文字=`12`（`token(card.mediaCombo.gap.text)`），icon=`8`（`token(card.mediaCombo.gap.icon)`），选择=`20`（`token(card.mediaCombo.size.selector)`）

#### Asset Tile Card（资材宫格卡）
- 图片比例：`1:1`
- 标题最多 `2` 行
- 价格样式：Web=`14/21 token(白版/文字 #666)`；App=`12/19 token(白版/文字 #666)`
- 品牌卡文案区高度：`48`（`token(card.assetTile.textAreaHeight)`）
- 无产品态图标：`40`（`token(card.assetTile.icon.empty)`）
- 添加态图标：`24`（`token(card.assetTile.icon.add)`）

#### 悬停工具条（Web）
- 仅 hover 出现
- 遮罩：`token(黑版/遮罩黑 #000 40%)` + blur=`token(overlay.blur.strong)`
- 按钮容器：`24`（`token(card.toolbar.size.button)`），icon=`24`（`token(card.toolbar.size.icon)`），按钮间距=`12`（`token(card.toolbar.gap.button)`）
- icon 颜色：`token(白版/白色 #FFF)`

#### 作品/资材状态角标系统
- 左上功能角标距边：`12`（`token(card.badge.offset.edge)`）
- 右上标签角标：贴边；小标签可切角
- 单图标角标：`28x28`（`token(card.badge.size.single)`），圆角 `token(radius.level.4)`
- 多图标角标：高 `28`（`token(card.badge.size.multiHeight)`），宽自适应（如 `56/83`）
- 角标背景：`token(黑版/标签黑底#000 30%)` + blur=`10`（`token(card.badge.blur)`）
- 图标画布：`24`（`token(card.badge.iconCanvas)`），组合间距：`4`（`token(card.badge.gap.icon)`）
- 文案角标（新增/封面）：`token(typo.body.app.default) token(白版/白色 #FFF)`，高=`28`（`token(card.badge.size.multiHeight)`），padding=`12`（`token(card.badge.paddingX)`）
- 状态策略：常态为默认优先；其余状态按业务逻辑文件决定；允许 3 状态组合。

#### 卡片外边距（并入 Card 章节）
- 普通信息卡（文本类）：跟随页面结构层横向间距（App `token(layout.space.inline.app)` / Web `token(layout.space.inline.web)`）
- 图片铺满类卡片（作品/资材/文件预览/宫格 Tile）：
  - App（手机/Pad）：`8`（`token(layout.space.card.media.inline.app)`）
  - Web：默认 `32`（`token(layout.space.inline.web)`，可按业务页面覆盖）

#### 卡片纵向间距（手机端）
- 普通信息卡之间：`token(layout.space.card.vertical.text.mobile)`
- 图片类卡片之间：`token(layout.space.card.vertical.media.mobile)`
- 同页混用时按卡片类型分别应用，不强制统一为同一数值。

### Modal / Dialog（规范待补）

- 目标：统一弹窗/对话框的层级、间距、按钮布局与状态策略（Pad/手机/Web）。
- 需补：尺寸（宽高/边距/圆角/阴影）、标题区/内容区/按钮区排版、遮罩、动效、状态（default/disabled/loading）。

### Drawer（规范待补）

- 目标：统一侧滑抽屉的宽度档位、遮罩、滚动策略、Header/Body/Footer 布局。
- 需补：Pad/Web 宽度档位、手机全屏/半屏策略、关闭按钮与返回策略、手势（若有）。

### Bottom Sheet（规范待补）

- 目标：统一底部浮层的高度档位（半屏/全屏）、圆角、拖拽把手、遮罩与滚动联动。
- 需补：安全区、Header（标题/关闭）、CTA 区、展开/收起动效与阈值（若有）。

### Toast / Snackbar（规范待补）

- 目标：统一提示条的出现位置、持续时间、层级、可关闭与动作按钮样式。
- 需补：成功/错误/警告/信息语义色 token 映射、图标、最大行数与换行策略。

### List Cell（规范待补）

- 目标：统一列表项高度档位、左右结构间距、分割线策略、右侧附加元素（箭头/开关/说明/状态）。
- 需补：一行/两行/三行文本、缩略图/头像、禁用态与点击反馈。

### Switch（规范待补）

- 目标：统一开关尺寸、轨道/圆点、开/关/禁用状态与点击热区。
- 需补：颜色 token（开/关/禁用）、动效时长与曲线。

### Checkbox（规范待补）

- 目标：统一复选框尺寸、勾选样式、半选态、与文案间距。
- 需补：错误态/禁用态、组间距（列表/表单场景）。

### Radio（规范待补）

- 目标：统一单选尺寸、选中点、与文案间距。
- 需补：禁用态、横排/竖排组间距、说明文案样式。

### Select / Dropdown（规范待补）

- 目标：统一选择器触发器高度、左右 padding、下拉层样式与选中态。
- 需补：多选/单选、搜索型下拉、空态、长列表滚动与分组。

### Search（规范待补）

- 目标：统一搜索框（icon、placeholder、清除按钮）与搜索页结构（建议/历史/结果）。
- 需补：输入态/聚焦态/禁用态、取消按钮（移动端）样式与间距。

### Empty / Loading / Error（规范待补）

- 目标：统一空态/加载/异常三类状态页的版式、图标、文案层级与操作按钮。
- 需补：插画/图标尺寸、标题/说明/CTA、不同端的垂直节奏与留白。

#### 资源规范（强制）

所有空状态、加载态 SVG 资源统一存放在项目路径下：
`Panzi/.cursor/skills/bujue-design-system/`

**1. 空状态（暂无数据 / No Data）**

- **存放目录**：`bujue-design-system/No Data/`
- **亮版（Light Mode）**：`No Data_Light Mode.svg`
- **暗版（Dark Mode）**：`No Data_Dark Mode.svg`
- **使用规则**：
  - 页面出现「暂无数据/暂无项目/暂无报价/暂无图片」等空状态时，必须使用对应主题色的统一 SVG。
  - 禁止使用占位符图片、字符图标或自定义插画代替空状态资源。
  - 必须支持系统主题自动切换亮/暗版，禁止固定单一版本。

**2. 加载状态（Loading）**

- **统一加载动画 CDN**：`https://uiverse.io/dovatgabriel/kind-cougar-54`
- **使用规则**：
  - 所有接口请求、列表加载、图片懒加载、提交等待场景，必须使用该统一加载动画。
  - 加载动画需居中显示，不遮挡关键操作按钮。
  - 禁止使用自定义 GIF、文字加载、原生浏览器加载动画。
