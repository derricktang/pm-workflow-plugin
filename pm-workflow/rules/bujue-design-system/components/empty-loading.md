<!--
  不觉设计系统 — Empty/Loading/Error组件规范
  本文件在 PM 工作流阶段4按需传入（当产品定义包含此组件类型时）。
  原始完整文件：bujue-design-system/COMPONENTS.md（备查，不传入工作流）
-->

> ⚠️ **内建兜底 pub 库（单库,2026-05-16 定案）**：本文件属于「pub 库（正式组件库,不觉设计系统）」的**内建兜底库** `pm-workflow/rules/bujue-design-system/`——工作流自带、git 跟踪长期保留,当前**唯一 pub 源,可走 `workflow-evolution` skill 直改**（**非**"外部接管 / 只读不可改"）。正式 pub 库接入为后续:终态由独立仓 `pm-group/bujue-design-system` 经 skill/CLI 消费(纯 Python CLI + 显式 `--root`,非 Read plugin),届时本库降离线 fallback,缺陷按 SSOT #31 NB 上报。详 `workflow_architecture_map.md §六` 组件库二元边界 + memory `pub_library_distribution_decision`。

### Empty / Loading / Error（规范待补）

- 目标：统一空态/加载/异常三类状态页的版式、图标、文案层级与操作按钮。
- 需补：插画/图标尺寸、标题/说明/CTA、不同端的垂直节奏与留白。

#### 资源规范（强制）

所有空状态、加载态 SVG 资源统一存放在项目路径下：
`pm-workflow/rules/bujue-design-system/`

**1. 空状态（暂无数据 / No Data）**

- **存放目录**：`pm-workflow/rules/bujue-design-system/icon/`
- **亮版（Light Mode）**：`NoData_LightMode.svg`
- **暗版（Dark Mode）**：`NoData_DarkMode.svg`
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
