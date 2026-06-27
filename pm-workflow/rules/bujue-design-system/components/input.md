<!--
  不觉设计系统 — Input组件规范
  本文件在 PM 工作流阶段4按需传入（当产品定义包含此组件类型时）。
  原始完整文件：bujue-design-system/COMPONENTS.md（备查，不传入工作流）
-->

> ⚠️ **内建兜底 pub 库（单库,2026-05-16 定案）**：本文件属于「pub 库（正式组件库,不觉设计系统）」的**内建兜底库** `pm-workflow/rules/bujue-design-system/`——工作流自带、git 跟踪长期保留,当前**唯一 pub 源,可走 `workflow-evolution` skill 直改**（**非**"外部接管 / 只读不可改"）。正式 pub 库接入为后续:终态由独立仓 `pm-group/bujue-design-system` 经 skill/CLI 消费(纯 Python CLI + 显式 `--root`,非 Read plugin),届时本库降离线 fallback,缺陷按 SSOT #31 NB 上报。详 `workflow_architecture_map.md §六` 组件库二元边界 + memory `pub_library_distribution_decision`。

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
