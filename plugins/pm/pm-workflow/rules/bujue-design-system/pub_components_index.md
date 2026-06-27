# pub 组件索引（不觉设计系统）

> ⚠️ **内建兜底 pub 库（单库,2026-05-16 定案）**：本文件属于「pub 库（正式组件库,不觉设计系统）」的**内建兜底库** `pm-workflow/rules/bujue-design-system/`——工作流自带、git 跟踪长期保留,当前**唯一 pub 源,可走 `workflow-evolution` skill 直改**（**非**"外部接管 / 只读不可改"）。正式 pub 库接入为后续:终态由独立仓 `pm-group/bujue-design-system` 经 skill/CLI 消费(纯 Python CLI + 显式 `--root`,非 Read plugin),届时本库降离线 fallback,缺陷按 SSOT #31 NB 上报。详 `workflow_architecture_map.md §六` 组件库二元边界 + memory `pub_library_distribution_decision`。

> **本文件定位**：阶段 4 PM Agent 进入任何子任务（任务规划 / 项目组件识别 / spec / PRD）之前的**第一份必读文件**。先在此找候选 → 再用 D1-D5 验能力 → 最后才精读具体组件 .md。
>
> **[Must] 查询入口（SSOT #52）**：PM 在写 PRD 章节前 / 涉及组件 / token / 端规范选型时，**必须先 Read `pm-workflow/skills/fb-design-query/SKILL.md`** 走 Q1-Q8 决策树（PRD Agent `[Must]` / Spec Agent `[Should]`），决策树 §三 分支终点 Read 本文件 §四 / §五 反查行。本文件 + `fb-fallback-manifest.md §三` 是查询路径的真源知识库（skill 仅引用不重复维护）。
>
> **真源**：`fb-fallback.css`（视觉实现）+ `fb-fallback-manifest.md`（调用模板）+ `components/*.md`（详细规范，部分组件有）。本索引是这三者的统一检索入口，不重复声明 CSS / 模板。
>
> **维护**：新增 / 修改 / 弃用 pub 组件时**同步**更新本文件 + 真源文件；`precheck_stage4.py` 校验本索引与真源 / `components/*.md` 一一对应。

---

## 一、查询路径

```
PM 收到模块任务 → 阶段 4 检索顺序（先粗后精）：

1. 扫 §二 分类总览，按业务直觉锁一级类
2. 在该类的子类下找候选 id（≤3 个）
3. 对每个候选用 §五 D1-D5 反查表验能力覆盖
4. 业务术语模糊时改走 §四 业务场景反查（自然语言入口）
5. 全部命中 → 直接引用；部分命中 → 走 proj 派生（见 proj_component_protocol.md §一.B）
```

⚠ 凡反查表中标 `⚠ pub 无` 的能力，PM 必须按 `proj_component_protocol.md` 派生 proj 组件，不得用现有 pub 组件硬凑。

---

## 二、分类总览

| 类别 | 子类（组件数） | 锚点 | 真源章节 |
|------|---------------|------|---------|
| 原子 atom | 操作类(2) / 输入类(2) / 装饰类(3) | [#atom](#31-原子-atom) | manifest §1 |
| 表单 form | 容器类(1) / 选择类(4) / 输入类(1) | [#form](#32-表单-form) | manifest §2 |
| 容器 container | 卡片类(1) / 弹层类(1) / 反馈类(1) / 标记类(3) / 布局类(2) | [#container](#33-容器-container) | manifest §3 |
| 列表 list | 列表类(1) / 表格类(1) / 分页(1) | [#list](#34-列表-list) | manifest §4 |
| 状态帧 state | 整页状态(5)：empty / loading / error / success / disabled | [#state](#35-状态帧-state) | manifest §5 |

**总计**：29 个组件 / 5 大类 / 13 个子类
**端口覆盖**：所有 pub 组件默认全端（Web / 手机 / PAD / 小程序 / H5），由 `.phone-frame` / `.tablet-frame` / `.miniprogram-frame` 容器自动适配触控目标和字号

---

## 三、组件总表

### 3.1 原子 atom

#### 3.1.1 操作类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-btn | 按钮 | text/icon | default/disabled/loading + Web(hover/active/focus) | click | primary/default/ghost/text/danger | - | components/button.md + manifest §1.1 |
| fb-link | 文字链接 | text | default/hover | click | link | - | manifest §1.5 |

#### 3.1.2 输入类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-input | 单行输入 | value/placeholder | default/focus/error/disabled/readonly | input/blur/focus | text | required(用 fb-label-required)/maxlength/pattern | components/input.md + manifest §1.2 |
| fb-textarea | 多行输入 | value/placeholder/rows | default/focus/error/disabled | input/blur | text | required/maxlength | manifest §1.3 |

#### 3.1.3 装饰类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-icon | 图标容器 | svg/字符 | - | - | - | 尺寸 sm/md/lg | manifest §1.4 |
| fb-label | 表单标签 | text | default + required modifier | - | form-label | - | manifest §1.5 |
| fb-hint | 辅助说明文字 | text | default/error | - | helper-text | - | manifest §1.5 |

---

### 3.2 表单 form

#### 3.2.1 容器类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-form-row | 表单行（label + 控件 + 错误提示）| label slot/control slot/error slot | default/error | - | form-row 纵向/横向 | - | manifest §2.1 |

#### 3.2.2 选择类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-select | 下拉选择 | options/value/placeholder | default/open/disabled/error | select/blur | dropdown 单选 | required | manifest §2.2 |
| fb-checkbox | 复选框 | label/checked | default/checked/disabled | toggle | 多选项 | - | manifest §2.3 |
| fb-radio | 单选框 | label/value/group | default/selected/disabled | select | 单选项 | - | manifest §2.4 |
| fb-switch | 开关 | checked/label | default/checked/disabled | toggle | 二态开关 | - | manifest §2.5 |

#### 3.2.3 输入类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-search | 搜索框 | value/placeholder | default/focus/disabled | input/submit | search | maxlength | manifest §2.6 |

---

### 3.3 容器 container

#### 3.3.1 卡片类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-card | 卡片 | title/body/media/meta/actions | default/hover | click(可选) | image-only / media-combo / file / asset-tile | 文案 ≤2 行 | components/card.md + manifest §3.1 |

#### 3.3.2 弹层类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-modal | 模态对话框 | title/body/footer | open/close | confirm/cancel/close | dialog | - | manifest §3.2 |

#### 3.3.3 反馈类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-toast | 浮层提示（短时） | text/icon | visible/hidden（自动消失）| 自动消失/手动关闭 | success/error/info/warning | 单行 | manifest §3.3 |

#### 3.3.4 标记类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-tag | 标签（筛选 / 标记） | text | default/selected/disabled | click(可选)/close(可选) | filter-tag / status-tag | - | components/tag-tab.md + manifest §3.4 |
| fb-chip | 芯片（已选条件，可关闭） | text/close-icon | default | close | selected-condition | - | manifest §3.5 |
| fb-badge | 徽章（数量 / 红点） | count / dot | visible/hidden | - | counter / unread-mark | 数字 ≤99（>99 显示 99+）| manifest §3.6 |

#### 3.3.5 布局类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-action-bar | 统一底栏操作组（frame/modal/drawer 通用）| 按钮组（slot）| default | - | action-bar | CSS 变量就近继承自动切换：frame 内 sticky 贴底 / modal·drawer 内静态居底；移动端 frame 直接子层 WARN（应用 navbar 菜单方案）；禁 inline position（S4-28 v3）。**deprecated 别名**：fb-frame-bottom-bar / fb-modal-footer / fb-drawer-footer | manifest §3.11 |
| fb-navbar | 移动类端口顶部 sticky 容器（v2 支持 7 variant）| left/center/right slot（按 data-variant 填充不同组件）| 7 variant：detail（默认）/ multi-select / confirm / edit / list / workflow / home | back / cancel / done / btn... | sticky-top-nav 灵活布局 | 仅 phone/h5/miniprogram/tablet-frame 直接子层置首位；data-variant=detail/workflow 强制 .fb-nav-back（S4-35）；其他 variant 用 [取消]/[完成] 替代；center slot 总用 .fb-nav-title 容器（即使内容是计数/步骤等）；PM 禁写 inline sticky | manifest §3.12 v2 |

---

### 3.4 列表 list

#### 3.4.1 列表类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-list + fb-list-item | 通用列表 | item.title/item.desc/item.extra slots | default/hover/selected | click | list-row | - | manifest §4.1 |

#### 3.4.2 表格类

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-table | 数据表格 | header-cell/row/cell slots（含 -num/-actions 变体）| default/row-hover/row-selected | row-click/sort/select | data-table | 同屏字段≥5 + 扫描/排序/筛选 + 桌面优先（手机降级卡片，参 proto_data_display_selection.md §一）| manifest §4.2 |

#### 3.4.3 分页

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-pagination | 分页器 | current/total/per-page | default/disabled | jump | pagination | - | manifest §4.3 |

---

### 3.5 状态帧 state

| id | 业务语义 | D1 字段 | D2 状态 | D3 交互 | D4 语义 | D5 约束 | 详情 |
|----|---------|--------|--------|--------|--------|--------|------|
| fb-state-empty | 空状态帧 | title/subtitle/illustration/actions | - | - | empty（暂无数据） | 必须用 NoData_LightMode/DarkMode SVG | components/empty-loading.md + manifest §5 |
| fb-state-loading | 加载状态帧 | title/subtitle/illustration | - | - | loading（数据获取中） | 长时加载用本帧；短时用 fb-btn(loading) | components/empty-loading.md + manifest §5 |
| fb-state-error | 错误状态帧 | title/subtitle/illustration/actions | - | retry-action | error（接口/数据异常） | actions 必含"重试" | components/empty-loading.md + manifest §5 |
| fb-state-success | 成功状态帧 | title/subtitle/illustration/actions | - | - | success（操作成功页） | - | manifest §5 |
| fb-state-disabled | 不可用状态帧 | title/subtitle/illustration | - | - | disabled（功能未启用 / 无权限） | 不同于禁用按钮，是整页/整模块级 | manifest §5 |

> **状态帧 vs 普通组件状态**：fb-state-* 是整页 / 整模块级状态展示（如列表为空整页只显示空帧），不要与 fb-input.is-error / fb-btn.is-loading 这类组件级 modifier 混淆。

---

## 四、按业务场景反查（自然语言 → 组件）

> **使用场景**：PM 还没想清楚业务术语对应哪个组件名时，按"我要做什么"找。

### 4.1 数据展示场景

| 我需要做... | 候选组件 | 选用建议 |
|-----------|---------|---------|
| 显示状态文字（已完成 / 已取消等）| fb-tag | 重要状态用 selected modifier |
| 显示数量徽章（红点 / 数字）| fb-badge | 数字 >99 自动 99+；纯红点用 dot 变体 |
| 显示已选筛选条件（可关闭）| fb-chip | 不要用 fb-tag + 自定义 ×，chip 自带 close |
| 显示一个内容卡片 | fb-card | 4 个 variant，按媒体形态选 |
| 显示用户头像 | ⚠ pub 无组件，派生 proj | 协议见 proj_component_protocol.md |
| 显示一段商品 / 业务实体卡片 | ⚠ pub 通用 fb-card 不够时派生 proj | 看本项目 proj 索引 |
| 显示时间轴 | ⚠ pub 无组件，派生 proj | - |

### 4.2 数据输入场景

| 我需要做... | 候选组件 | 选用建议 |
|-----------|---------|---------|
| 输入一段文字 | fb-input(text) | type 由 PM 在 input 上写 |
| 输入数字（带加减按钮）| ⚠ pub 无 stepper，派生 proj | 不要用 fb-input(number) + 自定义按钮硬凑 |
| 输入多行文字 | fb-textarea | rows 自定 |
| 输入搜索关键词 | fb-search | 自带 search 图标 |
| 选一个选项（少量，5 项以内）| fb-radio | 明示性强 |
| 选一个选项（>5 项）| fb-select | 节省空间 |
| 选多个选项 | fb-checkbox | - |
| 选多个标签（点选高亮）| ⚠ pub 无 tag-multi-select，派生 proj | 不要用 fb-tag + 自定义 click 事件硬凑 |
| 二态开关（开 / 关）| fb-switch | - |
| 选一个日期 | ⚠ pub 无 date-picker，派生 proj | - |
| 上传图片 / 文件 | ⚠ pub 无 upload，派生 proj | - |
| 一个完整的表单行（label + 控件 + 错误提示）| fb-form-row | 包裹任意 fb-input/select/etc |

### 4.3 反馈 / 状态场景

| 我需要做... | 候选组件 | 选用建议 |
|-----------|---------|---------|
| 列表为空 | fb-state-empty | 必须用 NoData svg |
| 数据加载中（长时）| fb-state-loading | 短时按钮加载用 fb-btn.is-loading |
| 数据加载失败 | fb-state-error | actions 必含重试 |
| 操作成功结果页 | fb-state-success | - |
| 功能未启用 / 无权限 | fb-state-disabled | 整页级，不是按钮禁用 |
| 操作成功后短提示（顶部 / 底部浮层）| fb-toast(success) | 自动消失 |
| 操作失败短提示 | fb-toast(error) | - |
| 一般信息浮层 | fb-toast(info) | - |
| 警告浮层 | fb-toast(warning) | - |
| 字段级错误提示（输入框下方）| fb-hint(error) + fb-input(is-error) | 不要用 toast |

### 4.4 操作 / 导航场景

| 我需要做... | 候选组件 | 选用建议 |
|-----------|---------|---------|
| 主操作按钮（提交 / 确认 / 支付）| fb-btn(primary) | 同操作组只允许 1 个 |
| 次操作按钮（取消 / 返回）| fb-btn(default) | - |
| 弱化操作（更多 / 详情链接）| fb-btn(text) 或 fb-link | 链接语义用 fb-link |
| 危险操作（删除 / 不可逆）| fb-btn(danger) | 必须有二次确认 modal |
| 弹出确认对话框 | fb-modal | - |
| 列表分页 | fb-pagination | - |
| Tab 切换同级内容 | ⚠ pub 无 fallback class，需手写 CSS（参考 components/tag-tab.md Tab 部分）或派生 proj | tag-tab.md 有完整规范 |
| 步骤条 | ⚠ pub 无组件，派生 proj | - |
| 面包屑 | ⚠ pub 无组件，派生 proj | - |

### 4.5 容器 / 布局场景

| 我需要做... | 候选组件 | 选用建议 |
|-----------|---------|---------|
| 把信息装入卡片 | fb-card | - |
| 列表项 | fb-list + fb-list-item | - |
| 多字段数据表（扫描/排序/筛选/批量）| fb-table | 同屏字段≥5 + 桌面优先；手机端降级卡片（参 proto_data_display_selection.md §一）|
| 弹出对话框 | fb-modal | - |
| 抽屉 | ⚠ pub 无 drawer，派生 proj | - |
| 底栏操作组（frame/modal/drawer 通用，取消/保存等）| fb-action-bar | 单类覆盖三场景：frame 内 sticky 贴底 / modal·drawer 内静态居底（CSS 变量就近继承自动切换）；移动端 frame 直接子层按 data-purpose 判定（page-main / multi-select-batch / workflow-nav 合规，其他 WARN）；禁 inline position（S4-28 v3 R2）。旧 fb-frame-bottom-bar/fb-modal-footer/fb-drawer-footer 已 deprecated 别名 |
| 移动端顶部 sticky 容器（v2 支持 7 variant）| fb-navbar | 仅 phone/h5/miniprogram/tablet-frame 直接子层置首位；按 data-variant 区分 7 场景：detail（默认）/multi-select/confirm/edit/list/workflow/home；data-variant=detail/workflow 强制 .fb-nav-back（S4-35）；其他 variant 用 [取消]/[完成] 替代 |
| 列表多选态顶部栏（取消+计数+全选）| fb-navbar data-variant=multi-select | left:[取消]+center:.fb-nav-title(已选 N/M)+right:[全选]；底栏配合 fb-action-bar data-purpose=multi-select-batch |
| 表单/浮层顶部确认（取消+确认）| fb-navbar data-variant=confirm | left:[取消]+center:title+right:[确认 primary]；通常无底栏 |
| 编辑态密集操作 | fb-navbar data-variant=edit | left:[完成]+center:title+right:[···] |
| 列表入口页（多工具栏）| fb-navbar data-variant=list | left:[back?]+center:title+right:[筛选/搜索/新增]；可选返回入口 |
| 向导分步 | fb-navbar data-variant=workflow | left:[上一步]+center:步骤 X/N+right:[跳过]；底栏配合 fb-action-bar data-purpose=workflow-nav |
| 主页/Tab（无返回入口）| fb-navbar data-variant=home | left:—+center:logo+right:[搜索/我的]；底部 Tab 切换非 fb-action-bar |

---

## 五、按能力维度反查（D1-D5）

> **使用场景**：PM 已知所需能力维度（"我要支持 loading 状态"），按维度反查所有候选。
>
> **[Must] SSOT 主从约束**：本节各表是按 D1-D5 维度的**聚合视图**——数据 SSOT 在 `§三 组件总表`各组件的 D1-D5 列。任何 pub 组件能力增删（如新增 slot / 状态 / 交互）须**先改 §三对应组件行**，再同步本节相关反查表，禁止反向。

### 5.1 D1 字段 / 槽维度

> **使用场景**：PM 已知"业务需要 N 个字段"或"业务需要某类字段（标题/媒体/操作区）"，反查 pub 哪些组件 slot 能容下；slot 数量或语义不匹配时按 `proj_component_protocol.md §一.B` 派生 proj。

#### 5.1.1 按 slot 数量分组

| slot 数量 | 候选组件（含 slot 清单）| 业务对照 |
|----------|----------------------|---------|
| 1 | `fb-tag(text)` / `fb-link(text)` / `fb-label(text)` / `fb-icon(svg)` / `fb-hint(text)` | 单字段展示（标签 / 链接 / 图标 / 帮助文字）|
| 2 | `fb-btn(text+icon)` / `fb-input(value+placeholder)` / `fb-search(value+placeholder)` / `fb-checkbox(label+checked)` / `fb-switch(checked+label)` / `fb-chip(text+close-icon)` / `fb-badge(count+dot)` | 双字段控件 |
| 3 | `fb-textarea(value+placeholder+rows)` / `fb-form-row(label+control+error)` / `fb-modal(title+body+footer)` / `fb-radio(label+value+group)` / `fb-select(options+value+placeholder)` / `fb-list-item(item.title+item.desc+item.extra)` / `fb-pagination(current+total+per-page)` / `fb-state-loading(title+subtitle+illustration)` / `fb-state-disabled(title+subtitle+illustration)` | 三字段表单 / 弹层 / 列表行 / 分页 / 状态帧（无 actions）|
| 4 | `fb-state-empty(title+subtitle+illustration+actions)` / `fb-state-error(title+subtitle+illustration+actions)` / `fb-state-success(title+subtitle+illustration+actions)` | 状态帧（含 actions）|
| 5 | `fb-card(title+body+media+meta+actions)` | 复合卡片（pub 单组件 slot 上限）|
| 6+ | ⚠ pub 无组件，派生 proj | 业务自有产品卡 / 订单卡 / 用户卡 等含 6+ 固定字段的复合卡片 |

#### 5.1.2 按业务字段类型反查

| 业务字段类型 | 对应 slot | 候选组件 |
|------------|---------|---------|
| 标题文字 | `text` / `title` / `item.title` | `fb-btn(text)` / `fb-card(title)` / `fb-modal(title)` / `fb-state-*(title)` / `fb-list-item(item.title)` / `fb-tag(text)` / `fb-link(text)` |
| 描述文字 / 副标题 | `body` / `subtitle` / `item.desc` | `fb-card(body)` / `fb-modal(body)` / `fb-state-*(subtitle)` / `fb-list-item(item.desc)` |
| 占位提示 | `placeholder` | `fb-input` / `fb-textarea` / `fb-search` / `fb-select` |
| 媒体（图 / 视频 / 插画）| `media` / `illustration` | `fb-card(media)` / `fb-state-*(illustration)` |
| 操作区（按钮组 / footer）| `actions` / `footer` | `fb-card(actions)` / `fb-modal(footer)` / `fb-state-empty/error/success(actions)` |
| 错误提示 | `error` | `fb-form-row(error)` |
| 表单 label | `label` | `fb-label` / `fb-form-row(label)` / `fb-checkbox(label)` / `fb-radio(label)` / `fb-switch(label)` |
| 计数 / 红点 | `count` / `dot` | `fb-badge(count/dot)` |
| 元信息 / 标签栏 | `meta` / `item.extra` | `fb-card(meta)` / `fb-list-item(item.extra)` |
| 自由组合 5+ 业务字段（产品 / 订单 / 用户）| ⚠ pub 无 | 派生 `proj.L2.*`（如 product-card 含 image+name+price+stock-tag+buy-btn）|
| 头像 / 时间轴 / 步骤条 / stepper / date-picker / upload | ⚠ pub 无 | 派生 proj（详见 §四 业务场景反查） |

#### 5.1.3 D1 缺口判定规则

按 `proj_component_protocol.md §一.B` D1 字段缺口判定，**任一**条件成立即构成 D1 缺口、须派生 proj：

1. **slot 数量不足**：业务需要的字段数量 > pub 候选的 slot 数量（如业务需 5 字段产品卡，fb-card 仅 5 slot 但语义不匹配业务字段时也算缺口）
2. **slot 语义不匹配**：业务字段语义无法映射到现有 slot（如"商品价格"放进 `fb-card.body` 是语义错配）
3. **slot 类型冲突**：业务需要"2 个并列媒体（如商品主图 + 缩略图条）"但 pub 只有单 `media` slot
4. **强结构语义**：业务字段有强组合关系（如"价格 + 折扣 + 划线价"3 字段必须在同一行），pub 通用 slot 不约束布局

D1 缺口条目须在 `scaffold.json modules[].candidate_components.proj_gaps` 中以 `trigger: "B-D1"` 标注（B 触发因素 + D1 维度），并在 `outputs/components_*.md §二.1.A` 表的"派生原因"列写清具体不通过的子条件（如"slot 数量不足：5 字段 vs fb-card 5 slot 中 1 个语义不匹配"）。

### 5.2 D2 状态维度

| 状态名 | 候选组件 | 备注 |
|-------|---------|------|
| default | 所有组件 | 默认态 |
| hover (Web 限定) | fb-btn / fb-link / fb-card / fb-list-item | 仅桌面端 |
| focus | fb-btn / fb-input / fb-textarea / fb-search | 表单类聚焦 |
| active (Web 限定) | fb-btn | 按下态 |
| disabled | fb-btn / fb-input / fb-textarea / fb-select / fb-checkbox / fb-radio / fb-switch / fb-search / fb-tag / fb-pagination | 用 .is-disabled modifier |
| loading | fb-btn(.is-loading) / fb-state-loading | 短时按钮 / 长时整页 |
| error | fb-input(.is-error) / fb-textarea(.is-error) / fb-form-row + fb-form-error / fb-hint(.fb-hint-error) / fb-state-error / fb-toast(error) | 字段级 / 表单行 / 整页 / 浮层 |
| selected | fb-tag(.fb-tag-selected) / fb-radio / fb-checkbox / fb-list-item | - |
| open | fb-select / fb-modal | 下拉展开 / 模态打开 |
| readonly | fb-input(.fb-input-readonly) | - |
| required | fb-label(.fb-label-required) | 在 label 上加红星 |
| visible/hidden | fb-toast / fb-modal / fb-badge | 显隐控制 |

### 5.3 D3 交互维度

| 交互 | 候选组件 | 备注 |
|------|---------|------|
| click | fb-btn / fb-link / fb-card / fb-list-item / fb-table（row）/ fb-tag / fb-pagination | - |
| input（文字录入） | fb-input / fb-textarea / fb-search | - |
| select（选择）| fb-select / fb-radio | - |
| toggle（切换）| fb-checkbox / fb-switch | - |
| close（关闭） | fb-chip / fb-modal / fb-toast | - |
| submit（提交） | fb-search | - |
| confirm/cancel | fb-modal | dialog 确认取消 |
| jump（页面跳转） | fb-pagination | - |
| 自动消失 | fb-toast | 默认 3 秒 |
| 长按拖动 | ⚠ pub 无组件，派生 proj | - |
| 滑动展开 | ⚠ pub 无组件，派生 proj | - |
| 多指手势 | ⚠ pub 无组件，派生 proj | - |
| 键盘 Enter 提交 | fb-search / fb-modal(footer 主按钮) | 默认支持 |
| 键盘 Esc 关闭 | fb-modal | 默认支持 |
| Tab 焦点循环 | 所有可交互组件 | 必须支持（无障碍） |

### 5.4 D4 业务语义维度

| 语义 | 候选组件 / variant | 备注 |
|------|------------------|------|
| 主操作 | fb-btn(primary) | - |
| 次操作 | fb-btn(default) | - |
| 弱操作 | fb-btn(ghost / text) | - |
| 危险操作 | fb-btn(danger) | 红色 |
| 链接跳转 | fb-link | - |
| 表单标签 | fb-label | - |
| 必填标识 | fb-label(.fb-label-required) | - |
| 辅助说明 | fb-hint | - |
| 字段错误 | fb-hint(.fb-hint-error) / fb-form-error | - |
| 普通卡片 | fb-card | 4 个 variant |
| 业务实体卡片（商品 / 用户 / 项目）| ⚠ pub 通用 fb-card 字段不足，派生 proj | - |
| 筛选标签 | fb-tag | 可点选高亮 |
| 状态标签（已完成 / 已取消） | fb-tag | - |
| 已选条件 | fb-chip | 自带 × |
| 数量徽章 | fb-badge(count) | - |
| 红点徽章 | fb-badge(dot) | 未读标记 |
| 短时反馈（操作成功 / 失败） | fb-toast | 4 种语义色 |
| 字段级错误 | fb-hint(error) | - |
| 整页空态 | fb-state-empty | - |
| 整页错误 | fb-state-error | - |
| 整页加载 | fb-state-loading | - |
| 操作成功结果页 | fb-state-success | - |
| 无权限 / 未启用 | fb-state-disabled | - |
| 弹出对话框 | fb-modal | - |
| 列表分页 | fb-pagination | - |
| Tab 切换 | ⚠ pub 无 fallback class，看 components/tag-tab.md | - |
| 用户头像 | ⚠ pub 无组件，派生 proj | - |
| 步骤条 | ⚠ pub 无组件，派生 proj | - |
| 面包屑 | ⚠ pub 无组件，派生 proj | - |
| 时间轴 | ⚠ pub 无组件，派生 proj | - |
| 日期选择 | ⚠ pub 无组件，派生 proj | - |
| 文件 / 图片上传 | ⚠ pub 无组件，派生 proj | - |
| 抽屉 | ⚠ pub 无组件，派生 proj | - |
| 数字加减 stepper | ⚠ pub 无组件，派生 proj | - |
| 多选 tag 形态 | ⚠ pub 无 tag-multi-select，派生 proj | - |

### 5.5 D5 约束维度

| 约束类型 | 候选组件支持方式 |
|---------|----------------|
| required（必填）| fb-label(.fb-label-required) 在 label 上显示红星；表单项 HTML required 属性 |
| maxlength（最大长度）| fb-input / fb-textarea / fb-search 用 HTML maxlength 属性 |
| pattern（正则约束）| fb-input 用 HTML pattern 属性 |
| 文案 ≤2 行 | fb-card 标题强制截断 |
| 数字 ≤99 自动 99+ | fb-badge | - |
| 单行文案 | fb-toast 单行；超长截断 |
| 操作组主按钮唯一 | fb-btn(primary) 同组仅 1 个（PM 必须遵守） |

---

## 六、变更历史

| 日期 | 操作 | 组件 | 备注 |
|------|------|------|------|
| 2026-04-27 | INIT | 全 26 个 pub 组件首次入库 | 由 fb-fallback.css 真源 + components/*.md 已有规范整合 |
| 2026-04-29 | UPDATE | §五 D1-D5 反查表 | 补 §五.1 D1 字段/槽维度反查表（按 slot 数量分组 + 按业务字段类型反查 + D1 缺口判定规则）；现有 5.1-5.4 顺序后移为 5.2-5.5；§五.0 加 SSOT 主从约束声明（§三 D1-D5 列为权威源） |

> **变更约定**：
> - **NEW**：新增 pub 组件（须先在 fb-fallback.css 实现 + manifest 增章节，再加索引行）
> - **UPDATE**：修改 pub 组件能力（须同步更新真源 + 详情列）
> - **DEPRECATED**：弃用 pub 组件（保留索引行，状态列加 ⚠弃用 标记，备注列指向替代组件）
> - **PROMOTE-IN**：proj 升 pub（在本表追加 NEW 行；同时 proj 索引降级为 deprecated 并指向新 pub id）
