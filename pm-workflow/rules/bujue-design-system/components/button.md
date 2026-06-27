<!--
  不觉设计系统 — Button组件规范
  本文件在 PM 工作流阶段4按需传入（当产品定义包含此组件类型时）。
  原始完整文件：bujue-design-system/COMPONENTS.md（备查，不传入工作流）
-->

> ⚠️ **内建兜底 pub 库（单库,2026-05-16 定案）**：本文件属于「pub 库（正式组件库,不觉设计系统）」的**内建兜底库** `pm-workflow/rules/bujue-design-system/`——工作流自带、git 跟踪长期保留,当前**唯一 pub 源,可走 `workflow-evolution` skill 直改**（**非**"外部接管 / 只读不可改"）。正式 pub 库接入为后续:终态由独立仓 `pm-group/bujue-design-system` 经 skill/CLI 消费(纯 Python CLI + 显式 `--root`,非 Read plugin),届时本库降离线 fallback,缺陷按 SSOT #31 NB 上报。详 `workflow_architecture_map.md §六` 组件库二元边界 + memory `pub_library_distribution_decision`。

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
- 禁用态只表达"不可点"，不改变信息架构（文案不换语义）。

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
- 允许在评审文档中保留"语义名 + 原值"用于对照，但工程实现只写变量。

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
