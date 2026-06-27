<!--
  不觉设计系统 — Card组件规范
  本文件在 PM 工作流阶段4按需传入（当产品定义包含此组件类型时）。
  原始完整文件：bujue-design-system/COMPONENTS.md（备查，不传入工作流）
-->

> ⚠️ **内建兜底 pub 库（单库,2026-05-16 定案）**：本文件属于「pub 库（正式组件库,不觉设计系统）」的**内建兜底库** `pm-workflow/rules/bujue-design-system/`——工作流自带、git 跟踪长期保留,当前**唯一 pub 源,可走 `workflow-evolution` skill 直改**（**非**"外部接管 / 只读不可改"）。正式 pub 库接入为后续:终态由独立仓 `pm-group/bujue-design-system` 经 skill/CLI 消费(纯 Python CLI + 显式 `--root`,非 Read plugin),届时本库降离线 fallback,缺陷按 SSOT #31 NB 上报。详 `workflow_architecture_map.md §六` 组件库二元边界 + memory `pub_library_distribution_decision`。

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
