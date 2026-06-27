# fb-fallback-manifest.md — 兜底组件库调用清单（批次 1）

> ⚠️ **内建兜底 pub 库（单库,2026-05-16 定案）**：本文件属于「pub 库（正式组件库,不觉设计系统）」的**内建兜底库** `pm-workflow/rules/bujue-design-system/`——工作流自带、git 跟踪长期保留,当前**唯一 pub 源,可走 `workflow-evolution` skill 直改**（**非**"外部接管 / 只读不可改"）。正式 pub 库接入为后续:终态由独立仓 `pm-group/bujue-design-system` 经 skill/CLI 消费(纯 Python CLI + 显式 `--root`,非 Read plugin),届时本库降离线 fallback,缺陷按 SSOT #31 NB 上报。详 `workflow_architecture_map.md §六` 组件库二元边界 + memory `pub_library_distribution_decision`。

> **本文件定位**：当公司前端组件库（pub 库工程化实现）尚未就位时，PM 在阶段 4 PRD Agent 派发时**必读**本文件 + `fb-fallback.css`，按本清单引用 `fb-*` 类生成 PRD HTML。
>
> **[Must] 查询入口（SSOT #52）**：PM 在写 PRD 章节前 / 涉及组件 / token / 端规范选型时，**必须先 Read `pm-workflow/skills/fb-design-query/SKILL.md`** 走 Q1-Q8 决策树（PRD Agent `[Must]` / Spec Agent `[Should]`）。决策树终点 Read 本文件 §三 对应组件段；本文件 + `pub_components_index.md §四/五` 是查询路径的真源知识库（skill 仅引用不重复）。治 PM "凭直觉选 class / 漏读 §3.2 移动端 Sheet 等隐藏跨平台支持"根因。详 `ssot_anchors.md #52` 三锚关系。
>
> **接入方式**：`assemble.py prd` 在拼装 PRD 时**自动注入** `fb-fallback.css` 内容到 PRD `<style>` 块顶部，PRD 自包含、可单独发送给设计 / 开发团队。
>
> **不要重写 CSS**：本清单覆盖的所有 `fb-*` 类**已在 fb-fallback.css 中定义**，PM 在 PRD 中**只引用 class 名**，不在 PRD 内重写这些组件的 CSS。仅 proj 组件需要 PM 自己写 CSS（参见 `proj_component_protocol.md`）。
>
> **[Must] SSOT 主从架构（与 `fb-fallback.css` 双锚关系）**：
> - 本文件是 `fb-fallback.css` 的**派生视图**——HTML 模板调用文档，供 PM 在阶段 4 PRD 撰写时按调用示例引用 `fb-*` class
> - `fb-fallback.css` 是**技术真源**（SSOT），决定浏览器实际渲染效果
> - **调整方向**：任何 `fb-*` class 增 / 删 / 改须**先改 `fb-fallback.css`**，再同步本文件的 HTML 模板示例；**禁止反向**（本文件写了但 css 没实现 = PM 引用后浏览器渲染塌陷）
> - **兜底校验**：`precheck_stage4.py check_fb_fallback_sync` 双向 diff（only_css 报 fail / only_manifest 报 fail），拦截漂移

---

## [Must] data-tp 占位约定（与 S4-24 联动）

下方所有 HTML 模板中出现的 `data-tp="M[XX]-P[YY]-T[ZZ]"` 是**占位符**，PM 拷贝模板进 PRD 草稿时**必须**逐个替换为本模块的实际触点编号（与 spec 触点表 ID 一致；编号规则见 `proto_contract.md §四`）：
- `M[XX]` → 当前模块号，如 `M01`
- `P[YY]` → 当前页面号，如 `P02`
- `T[ZZ]` / `D[ZZ]` → 触点序号；普通触点用 `T01/T02/...`，不可逆/危险触点用 `D01/D02/...`

**触发范围**（来自 `rule_hard_constraints.md S4-24` + `precheck_stage4.py INTERACTIVE_FB_CLASSES`）：含 `fb-btn-*` / `fb-input` / `fb-textarea` / `fb-search` / `fb-select` / `fb-checkbox` / `fb-radio` / `fb-switch` / `fb-link` / `fb-list-item` / `fb-pagination` / `fb-chip` 的元素，以及任何 `<button>` / `<input>` / `<select>` / `<textarea>` / `<a href!='#'>` / `onclick=` 元素，**全部**必须含 `data-tp`。漏一个 → precheck S4-24 fail。

> 占位符 `M[XX]-P[YY]-T[ZZ]` 字面值不会被 precheck 通过——这是故意的：PM 若忘记替换，precheck 会直接报 "data-tp 值不在 spec 触点表中"，把疏漏拦在自审之前。

---

## 索引

| 类别 | class 系列 | 数量 |
|------|-----------|------|
| 1. 原子 | btn / input / textarea / icon / label / hint / link | 7 |
| 2. 表单 | form-row / select / checkbox / radio / switch / search | 6 |
| 3. 容器 | card / modal / toast / tag / chip / badge | 6 |
| 4. 列表 | list / list-item / pagination | 2 |
| 5. 状态帧（L4） | state-empty / state-loading / state-error / state-success / state-disabled | 5 |
| 6. 其它 | tp-marker（触点徽章，与 proto_contract §四 联动）| — |

**端口自适应**：默认值按桌面 Web 基线；在 `.phone-frame` / `.tablet-frame` / `.miniprogram-frame` 容器内自动调大触控目标 + 字号 + 圆角降为 4px。**PM 不需要为不同端写不同 class**，只需把组件放在正确的 frame 容器内。

---

## `[Must]` PM 按需精读 SOP（避免 Read 全文 474 行）

`[Must]` PM 写 PRD 草稿时**禁止 Read 整个 manifest 全文**（PM 实际只用 5-8 个组件,Read 全文 ~80% token 浪费）。改用 **anchor + 范围读取** 两步:

1. **grep 定位**：`grep -n "FB-MODEL: {组件 id}" fb-fallback-manifest.md`
   - 每个组件章节顶部含 `<!-- [FB-MODEL: {组件 id}] -->` 单行 anchor 注释
   - 组件 id 与 class 一致（如 `fb-btn` / `fb-input` / `fb-card` / `fb-state` / `tp-marker`）
   - 状态帧 L4 用统一 anchor `fb-state`（5 类共享）；label/hint/link 三件套同章节多 anchor: `fb-label` / `fb-hint` / `fb-link`（指向同一 ```html 块）
2. **范围读取**：`Read offset:N limit:M`
   - N = grep 返回的行号
   - M = 25-40 行（典型组件块大小,不够再追加 Read）
   - 边界:下一个 `FB-MODEL:` anchor 即组件结束(可先 grep 全部 anchor 行号一次性掌握分段)

### 完整 anchor 清单（按出现顺序,共 30 个 id；§1.5 三件套各 1 anchor）

| 章节 | anchor id | 用例 |
|------|-----------|------|
| 1.1 | `fb-btn` | 按钮 |
| 1.2 | `fb-input` | 输入框 |
| 1.3 | `fb-textarea` | 文本域 |
| 1.4 | `fb-icon` | 图标容器 |
| 1.5 | `fb-label` / `fb-hint` / `fb-link` | label / hint / link 三件套（同 ```html 块,3 anchor 对应 fallback.css 各自 selector） |
| 2.1 | `fb-form-row` | 表单行 |
| 2.2 | `fb-select` | 下拉选择 |
| 2.3 | `fb-checkbox` | 复选框 |
| 2.4 | `fb-radio` | 单选框 |
| 2.5 | `fb-switch` | 开关 |
| 2.6 | `fb-search` | 搜索框 |
| 3.1 | `fb-card` | 卡片 |
| 3.2 | `fb-modal` | 弹框 |
| 3.3 | `fb-toast` | 轻提示 |
| 3.4 | `fb-drawer` | 抽屉（容器型） |
| 3.5 | `fb-dropdown` | 下拉菜单（浮层） |
| 3.6 | `fb-popover` | 气泡弹层（浮层） |
| 3.7 | `fb-tooltip` | 文字提示（浮层） |
| 3.8 | `fb-tag` | 标签 |
| 3.9 | `fb-chip` | 筹码 |
| 3.10 | `fb-badge` | 角标 |
| 3.11 | `fb-action-bar` | 统一底栏操作组（frame 内 sticky 贴底 / modal·drawer 内静态居底，CSS 变量就近继承自动切换）。**deprecated 别名**（v3 兼容期保留）：`fb-frame-bottom-bar` / `fb-modal-footer` / `fb-drawer-footer` |
| 3.12 | `fb-navbar` | 移动类端口次级页面顶部导航栏（含 fb-nav-back / -title / -action） |
| 4.1 | `fb-list` | 列表 + 列表项 |
| 4.2 | `fb-table` | 表格（多字段对比 / B 端专业 / 桌面优先）|
| 4.3 | `fb-pagination` | 分页 |
| 5 | `fb-state` | 状态帧（5 类共享） |
| 6 | `tp-marker` | 触点徽章 |

> **派发 prompt 配套**：编排器派发 PM 时,prompt 应明示"按 anchor 精读单组件,不读全文 manifest"（详见 `pm-workflow/rules/agent_dispatch_protocol.md §阶段4规范文件传入策略` fb-fallback-manifest.md 行）。

---

## 1. 原子组件

### 1.1 Button — `.fb-btn`
<!-- [FB-MODEL: fb-btn] -->

| 主题 modifier | 用途 | 默认视觉 |
|---------------|------|---------|
| `.fb-btn-primary` | 主要操作（同操作组内仅 1 个）| 黑底白字 |
| `.fb-btn-default` | 次要操作 | 白底黑字 + 灰边 |
| `.fb-btn-ghost` | 弱化操作 | 浅灰底黑字 |
| `.fb-btn-text` | 极弱操作（无背景）| 透明底黑字 |
| `.fb-btn-danger` | 不可逆危险操作 | 红底白字 |

| 尺寸 modifier | Web 高度 | 移动端高度 |
|--------------|---------|-----------|
| `.fb-btn-sm` | 28px | 32px |
| `.fb-btn-md`（默认）| 32px | 44px |
| `.fb-btn-lg` | 40px | 48px |
| `.fb-btn-xl` | 48px | 52px |

**状态 modifier**: `.is-disabled` / `.is-loading`

**HTML 模板：**
```html
<button class="fb-btn fb-btn-primary" data-tp="M[XX]-P[YY]-T[ZZ]">提交</button>
<button class="fb-btn fb-btn-default fb-btn-sm" data-tp="M[XX]-P[YY]-T[ZZ]">取消</button>
<button class="fb-btn fb-btn-primary is-loading" data-tp="M[XX]-P[YY]-T[ZZ]">提交中</button>
<button class="fb-btn fb-btn-primary is-disabled" data-tp="M[XX]-P[YY]-T[ZZ]">不可用</button>
```

### 1.2 Input — `.fb-input`
<!-- [FB-MODEL: fb-input] -->

| 状态 modifier | 含义 |
|--------------|------|
| `.is-focus` | 聚焦态（黑色边框）|
| `.is-error` | 错误态（红色边框）|
| `.is-disabled` | 禁用态 |
| `.fb-input-readonly` | 只读态 |

**HTML 模板：**
```html
<input class="fb-input" placeholder="请输入" data-tp="M[XX]-P[YY]-T[ZZ]" />
<input class="fb-input is-focus" value="正在输入" data-tp="M[XX]-P[YY]-T[ZZ]" />
<input class="fb-input is-error" value="错误内容" data-tp="M[XX]-P[YY]-T[ZZ]" />
<input class="fb-input is-disabled" value="禁用" disabled data-tp="M[XX]-P[YY]-T[ZZ]" />
```

### 1.3 Textarea — `.fb-textarea`
<!-- [FB-MODEL: fb-textarea] -->

```html
<textarea class="fb-textarea" placeholder="请输入多行内容" rows="4" data-tp="M[XX]-P[YY]-T[ZZ]"></textarea>
<textarea class="fb-textarea is-error" data-tp="M[XX]-P[YY]-T[ZZ]">错误内容</textarea>
```

### 1.4 Icon container — `.fb-icon`
<!-- [FB-MODEL: fb-icon] -->

容器 class，用于规范图标尺寸/颜色。具体 SVG / 字符由调用方提供。

| 尺寸 | 边长 |
|------|------|
| `.fb-icon-sm` | 16px |
| `.fb-icon`（默认）| 24px |
| `.fb-icon-lg` | 32px |

```html
<span class="fb-icon">→</span>
<span class="fb-icon-sm">×</span>
<span class="fb-icon"><svg>...</svg></span>
```

### 1.5 Label / Hint / Link
<!-- [FB-MODEL: fb-label] -->
<!-- [FB-MODEL: fb-hint] -->
<!-- [FB-MODEL: fb-link] -->

```html
<label class="fb-label">标题</label>
<label class="fb-label fb-label-required">必填项</label>
<p class="fb-hint">辅助说明文字</p>
<p class="fb-hint fb-hint-error">错误提示</p>
<a class="fb-link" data-tp="M[XX]-P[YY]-T[ZZ]">查看详情</a>
```

---

## 2. 表单组件

### 2.1 FormRow — `.fb-form-row`
<!-- [FB-MODEL: fb-form-row] -->

```html
<!-- 纵向（标题在上，字段在下）-->
<div class="fb-form-row">
  <label class="fb-label fb-label-required">手机号</label>
  <input class="fb-input" placeholder="请输入手机号" data-tp="M[XX]-P[YY]-T[ZZ]" />
  <p class="fb-form-error">请输入正确的手机号</p>
</div>

<!-- 横向（标题在左）-->
<div class="fb-form-row fb-form-row-inline">
  <label class="fb-label">用户名</label>
  <input class="fb-input" data-tp="M[XX]-P[YY]-T[ZZ]" />
</div>
```

### 2.2 Select — `.fb-select`
<!-- [FB-MODEL: fb-select] -->

```html
<!-- 关闭态 -->
<div class="fb-select" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span>请选择</span>
</div>

<!-- 打开态 + 选项列表 -->
<div class="fb-select is-open" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-select-placeholder">请选择</span>
  <div class="fb-select-dropdown">
    <div class="fb-select-option">选项一</div>
    <div class="fb-select-option is-selected">选项二（已选）</div>
    <div class="fb-select-option">选项三</div>
  </div>
</div>
```

### 2.3 Checkbox — `.fb-checkbox`
<!-- [FB-MODEL: fb-checkbox] -->

```html
<label class="fb-checkbox" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-checkbox-box"></span>
  <span>未选中</span>
</label>

<label class="fb-checkbox is-checked" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-checkbox-box"></span>
  <span>已选中</span>
</label>

<label class="fb-checkbox is-disabled" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-checkbox-box"></span>
  <span>禁用</span>
</label>
```

### 2.4 Radio — `.fb-radio`
<!-- [FB-MODEL: fb-radio] -->

```html
<label class="fb-radio" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-radio-dot"></span>
  <span>选项一</span>
</label>

<label class="fb-radio is-checked" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-radio-dot"></span>
  <span>选项二（已选）</span>
</label>
```

### 2.5 Switch — `.fb-switch`
<!-- [FB-MODEL: fb-switch] -->

```html
<div class="fb-switch" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-switch-thumb"></span>
</div>

<div class="fb-switch is-checked" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-switch-thumb"></span>
</div>

<div class="fb-switch is-disabled" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-switch-thumb"></span>
</div>
```

### 2.6 Search — `.fb-search`
<!-- [FB-MODEL: fb-search] -->

```html
<div class="fb-search" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-search-icon fb-icon-sm">🔍</span>
  <input class="fb-search-input" placeholder="搜索" data-tp="M[XX]-P[YY]-T[ZZ]" />
</div>
```

> 同模板内出现两个 `data-tp` 占位是因为 precheck 同时按 class 信号（外层 `fb-search`）和标签信号（内层 `<input>`）识别交互元素；PM 落地时若两者共用同一触点编号即可写相同值，否则按业务拆为两个触点。

---

## 3. 容器组件

### 3.1 Card — `.fb-card`
<!-- [FB-MODEL: fb-card] -->

```html
<article class="fb-card">
  <img class="fb-card-media" src="..." alt="">
  <div class="fb-card-body">
    <div class="fb-card-title">卡片标题</div>
    <div class="fb-card-meta">辅助元信息</div>
  </div>
  <div class="fb-card-actions">
    <button class="fb-btn fb-btn-text fb-btn-sm" data-tp="M[XX]-P[YY]-T[ZZ]">详情</button>
    <button class="fb-btn fb-btn-primary fb-btn-sm" data-tp="M[XX]-P[YY]-T[ZZ]">操作</button>
  </div>
</article>
```

> 整卡可点时（如列表卡片跳详情），在 `<article class="fb-card" onclick="...">` 上加 `data-tp="M[XX]-P[YY]-T[ZZ]"`；纯展示卡片不需要。

### 3.2 Modal — `.fb-modal`
<!-- [FB-MODEL: fb-modal] -->

**`[Must]` 默认可见性**：`.fb-modal-overlay` **默认 `display:none`**（在 `fb-fallback.css` 已规定）。在 PRD 中对应"弹框已弹出"的状态帧时，须额外加 `is-visible` 修饰类才会可见；其它帧不加此修饰类即保持隐藏。

**`[Must]` 嵌入帧机制**：`.fb-modal-overlay` 真源 `position: absolute`，**嵌入 `frame-card` 内**（`frame-card { isolation: isolate }` 已建立独立 stacking context，弹框 z-index 不会溢出到 sidebar / section-header）。`.fb-modal-overlay` 自带 `z-index: 50` (Z-50 overlay 遮罩)，**PM 不需要也不允许**写自定义 z-index。

```html
<!-- 默认状态：弹框未弹出（隐藏，无需 is-visible） -->
<div class="fb-modal-overlay">
  <div class="fb-modal">…</div>
</div>

<!-- 弹框已弹出状态帧（如 H-M01-P02-modal-confirm-delete）：加 is-visible -->
<div class="fb-modal-overlay is-visible">
  <div class="fb-modal">
    <div class="fb-modal-header">
      <div class="fb-modal-title">操作确认</div>
    </div>
    <div class="fb-modal-body">
      <p>确认要删除该项目吗？此操作不可撤销。</p>
    </div>
    <div class="fb-action-bar">
      <button class="fb-btn fb-btn-default" data-tp="M[XX]-P[YY]-T[ZZ]">取消</button>
      <button class="fb-btn fb-btn-danger" data-tp="M[XX]-P[YY]-D[ZZ]">确认删除</button>
    </div>
  </div>
</div>
```

> 危险操作（删除 / 不可逆）使用 `D[ZZ]` 占位段，对应 spec 触点表里的 D 类编号。
>
> **`[Must]` 禁止 inline 覆盖**：禁止用 `style="display:flex"` / `style="position:fixed"` / `style="z-index:..."` 强制显示或定位弹框 — 默认状态保持 class 完整 + 弹出态加 `.is-visible`，z-index / position 已由 css 真源预设（保持 SSOT 单一真源 + 便于状态机控制）。

**`[Must]` 移动端 Action Sheet 自动适配**（/retro 2026-05-13 # 5 复盘升级）：

在 `.phone-frame` / `.miniprogram-frame` 内，`.fb-modal` **由真源 CSS 自动变为底部上滑全宽弹层（Action Sheet 形态）**，PM 不需也不允许自行实现：

- **真源 CSS**：`fb-fallback.css` L509-510 `.phone-frame .fb-modal, .miniprogram-frame .fb-modal { border-radius: 12px 12px 0 0; align-self: flex-end; width: 100%; max-width: 100% }` — ① 上方圆角下方贴边 ② `align-self: flex-end` 在 `.fb-modal-overlay { display:flex }` 容器内自动锚到 cross-axis 末端 = 视觉贴 frame 底部 ③ 占满 frame 宽度
- **遮罩**：`.fb-modal-overlay.is-visible` 自带 `background: var(--fb-overlay)`，sheet 形态下遮罩与桌面 modal 完全一致，无须额外配置
- **PM 唯一职责**：在状态帧 HTML 用标准结构 `<div class="fb-modal-overlay is-visible"><div class="fb-modal">…</div></div>`，sheet 形态全自动出

**`[Must]` 反例禁令**：**禁止** PM 在 `.phone-frame` / `.miniprogram-frame` 内用自定义 class（`.sheet` / `.bottom-sheet` / `.action-sheet` / `.popup` / `.modal-mask` / `.dialog` 等）+ inline `position: relative / absolute` + `flex: 1` 等自由发挥写法**完全规避** `.fb-modal-overlay + .fb-modal` 标准结构 — 历史案例（/retro 2026-05-13 # 5 复盘根因 B）：PM 在 phone-frame 写 sheet 时绕开真源 class，导致 ① 缺遮罩（自定义 div 无 `.fb-modal-overlay` 自动遮罩） ② 不贴底（绕开真源 `align-self: flex-end` 锚定）。机械兜底：`precheck_stage4 rule-5 check_panel_class_evasion` 扫 phone-frame / miniprogram-frame 内 class 含 `sheet|bottom-sheet|action-sheet|popup` 字面但非 `fb-*` 真源 → WARN（v1）→ 下迭代升 FAIL。

### 3.3 Toast — `.fb-toast`
<!-- [FB-MODEL: fb-toast] -->

**`[Must]` 默认可见性**：`.fb-toast` **默认 `display:none`**（在 `fb-fallback.css` 已规定）。Toast 仅在"操作反馈短暂展示"的状态帧（典型 3-4 秒后消失）才加 `is-visible` 修饰类显示；其它帧不加此修饰类即保持隐藏。

**`[Must]` 嵌入帧机制**：`.fb-toast` 真源 `position: absolute; left: 50%; transform: translateX(-50%)`，**嵌入 `frame-card` 内**（依赖 `frame-card { isolation: isolate }` 隔离）。自带 `z-index: 150` (Z-150 toast 反馈层)，**高于 dropdown / modal 等所有面板**，保证模态弹框打开时 toast 仍可见。**PM 不需要也不允许**写自定义 z-index / position。

| 主题 modifier | 用途 |
|---------------|------|
| `.fb-toast-info`（默认）| 普通信息（黑底白字）|
| `.fb-toast-success` | 成功反馈（绿底白字）|
| `.fb-toast-error` | 错误反馈（红底白字）|
| `.fb-toast-warning` | 警告反馈（橙底白字）|

| 可见性修饰类 | 用途 |
|------------|------|
| `.is-visible` | **`[Must]`** Toast 当前显示态（PRD 状态帧中 toast 出现帧须含此类） |

```html
<!-- 默认状态：toast 未触发（隐藏，无需 is-visible） -->
<div class="fb-toast fb-toast-success">操作成功</div>

<!-- toast 显示态状态帧（如 H-M01-P02-toast-success）：加 is-visible -->
<div class="fb-toast fb-toast-success is-visible">操作成功</div>
<div class="fb-toast fb-toast-error is-visible">网络异常，请重试</div>
```

> **`[Must]` 禁止 inline 覆盖**：禁止用 `style="display:inline-flex"` / `style="position:..."` / `style="z-index:..."` 强制显示或定位 toast — 须用 `is-visible` 修饰类（保持 SSOT 单一真源 + 便于状态机控制）。

### 3.4 Drawer — `.fb-drawer`
<!-- [FB-MODEL: fb-drawer] -->

抽屉，从 frame-card 边缘滑入，常用于侧边详情 / 筛选条件 / 多步表单等需要保留主页面上下文的场景。

**`[Must]` 默认可见性 + 嵌入帧机制**：`.fb-drawer-overlay` / `.fb-drawer` 真源默认 `display: none` + `position: absolute`，嵌入 frame-card；`.fb-drawer-overlay` 自带 `z-index: 40` (Z-40)，`.fb-drawer` 自带 `z-index: 41`（略高于遮罩，确保内容可点）。

| 方向修饰类 | 用途 |
|----------|------|
| `.fb-drawer-right`（默认）| 从右滑入，宽 360px |
| `.fb-drawer-left` | 从左滑入 |
| `.fb-drawer-top` | 从上滑入，高 50% |
| `.fb-drawer-bottom` | 从下滑入 |

```html
<!-- 默认状态：drawer 未弹出（隐藏） -->
<div class="fb-drawer-overlay">
  <aside class="fb-drawer fb-drawer-right">…</aside>
</div>

<!-- drawer 显示态状态帧（如 H-M01-P02-drawer-detail）：双层都加 is-visible -->
<div class="fb-drawer-overlay is-visible">
  <aside class="fb-drawer fb-drawer-right is-visible">
    <div class="fb-drawer-header">详情面板</div>
    <div class="fb-drawer-body">…</div>
    <div class="fb-action-bar">
      <button class="fb-btn fb-btn-default" data-tp="M[XX]-P[YY]-T[ZZ]">关闭</button>
      <button class="fb-btn fb-btn-primary" data-tp="M[XX]-P[YY]-T[ZZ]">保存</button>
    </div>
  </aside>
</div>
```

> **`[Must]` 禁止 inline 覆盖**：同 modal，禁止用 inline style 强制显示或定位 drawer。

### 3.5 Dropdown — `.fb-dropdown`
<!-- [FB-MODEL: fb-dropdown] -->

下拉浮层，常用于操作菜单 / 二级选项 / 自定义 select 替代。**与 `.fb-select-dropdown`**（select 组件内置）不同：fb-dropdown 是独立浮层，可挂在任意 trigger 上。

**`[Must]` 默认可见性 + 嵌入帧机制**：默认 `display: none` + `position: absolute`；自带 `z-index: 100` (Z-100 dropdown / select)。预期由父 trigger 元素 `position: relative`，dropdown 用 `top: 100%; left: 0` 锚定（默认下方左对齐）。

**`[Should]` 方向修饰类**（与 popover §3.6 / tooltip §3.7 同族对称）：当 trigger 位置使默认下方左对齐导致出屏 / 遮挡内容时，用方向修饰类指定 dropdown 锚点：

| 方向修饰类 | 锚点（CSS）| 典型业务场景 |
|----------|-----------|------------|
| `.fb-dropdown-bottom`（默认）| `top: 100%; left: 0` | 多数场景（trigger 下方有空间）|
| `.fb-dropdown-top` | `bottom: 100%; left: 0` | trigger 靠近 frame 底部 / 键盘弹出场景 |
| `.fb-dropdown-right` | `top: 100%; right: 0; left: auto` | trigger 靠近 frame 右边界（如表格右侧列状态切换菜单）|
| `.fb-dropdown-left` | `top: 100%; left: 0; right: auto` | 显式标注左对齐（与默认等效；写出方便意图明示）|

```html
<!-- 表格右侧列：用右对齐 dropdown 避免出屏 -->
<div style="position: relative;">
  <button class="fb-btn fb-btn-default">操作 ▾</button>
  <div class="fb-dropdown fb-dropdown-right is-visible">
    <div class="fb-dropdown-item">编辑</div>
    <div class="fb-dropdown-item">删除</div>
  </div>
</div>
```

**`[Must]` 禁 inline style 覆盖方向**：PM 在 prd.html 中**不得**写 `style="right:0; left:auto"` / `style="bottom:100%; top:auto"` 等 inline 强制方向——必须用 `.fb-dropdown-{bottom|top|right|left}` 修饰类（与 modal/drawer 禁 inline z-index 同精神）。

```html
<!-- 默认状态：未展开 -->
<div style="position: relative;">
  <button class="fb-btn fb-btn-default" data-tp="M[XX]-P[YY]-T[ZZ]">操作 ▾</button>
  <div class="fb-dropdown">
    <div class="fb-dropdown-item" data-tp="M[XX]-P[YY]-T[ZZ]">编辑</div>
    <div class="fb-dropdown-item" data-tp="M[XX]-P[YY]-T[ZZ]">复制</div>
    <div class="fb-dropdown-divider"></div>
    <div class="fb-dropdown-item" data-tp="M[XX]-P[YY]-D[ZZ]">删除</div>
  </div>
</div>

<!-- 展开状态：加 is-visible -->
<div class="fb-dropdown is-visible">
  <div class="fb-dropdown-item is-selected">已选项</div>
  <div class="fb-dropdown-item">备选项</div>
  <div class="fb-dropdown-item is-disabled">禁用项</div>
</div>
```

| 状态 modifier | 用途 |
|--------------|------|
| `.is-visible` | 当前展开态 |
| `.is-selected` | dropdown-item 选中态 |
| `.is-disabled` | dropdown-item 禁用态 |

### 3.6 Popover — `.fb-popover`
<!-- [FB-MODEL: fb-popover] -->

悬浮气泡，常用于「点击查看详情 / 富内容触发提示」（比 tooltip 内容多、可含按钮）。

**`[Must]` 默认可见性 + 嵌入帧机制**：默认 `display: none` + `position: absolute`；自带 `z-index: 60` (Z-60 tooltip / popover)。

| 方向修饰类 | 用途 |
|----------|------|
| `.fb-popover-bottom`（默认）| 下方展开 |
| `.fb-popover-top` | 上方展开 |
| `.fb-popover-left` | 左侧展开 |
| `.fb-popover-right` | 右侧展开 |

```html
<!-- 默认隐藏 -->
<div style="position: relative;">
  <span class="fb-icon" data-tp="M[XX]-P[YY]-T[ZZ]">ℹ</span>
  <div class="fb-popover fb-popover-bottom">
    <div class="fb-popover-title">字段说明</div>
    <div class="fb-popover-body">本字段用于…</div>
  </div>
</div>

<!-- 显示态：加 is-visible -->
<div class="fb-popover fb-popover-bottom is-visible">
  <div class="fb-popover-title">操作提示</div>
  <div class="fb-popover-body">
    点击下方按钮可触发批量操作…
    <button class="fb-btn fb-btn-primary fb-btn-sm" data-tp="M[XX]-P[YY]-T[ZZ]">了解更多</button>
  </div>
</div>
```

### 3.7 Tooltip — `.fb-tooltip`
<!-- [FB-MODEL: fb-tooltip] -->

轻量提示，常用于「hover 简短说明」（比 popover 简单、不含交互）。

**`[Must]` 默认可见性 + 嵌入帧机制**：默认 `display: none` + `position: absolute`；自带 `z-index: 60` (Z-60)。

| 方向修饰类 | 用途 |
|----------|------|
| `.fb-tooltip-top`（默认）| 上方提示 |
| `.fb-tooltip-bottom` | 下方提示 |
| `.fb-tooltip-left` | 左侧提示 |
| `.fb-tooltip-right` | 右侧提示 |

```html
<!-- 默认隐藏 -->
<span style="position: relative;">
  <span class="fb-icon" data-tp="M[XX]-P[YY]-T[ZZ]">⚙</span>
  <span class="fb-tooltip fb-tooltip-top">设置</span>
</span>

<!-- hover 显示态：加 is-visible -->
<span class="fb-tooltip fb-tooltip-top is-visible">设置</span>
```

> Tooltip 内容应为单行短文本（典型 ≤ 16 字），需多行/含交互请改用 `.fb-popover`。

### 3.8 Tag — `.fb-tag`
<!-- [FB-MODEL: fb-tag] -->

| 状态 / modifier | 用途 |
|----------------|------|
| `.fb-tag`（默认）| 普通标签（白底灰字 + 描边）|
| `.fb-tag-selected` | 选中态（深灰底黑字）|
| `.fb-tag-disabled` | 禁用态 |
| `.fb-tag-pill` | 胶囊形（圆角 100px）|

| 尺寸 | 高度 |
|------|------|
| 默认 | 24px（Web）/ 28px（移动）|
| `.fb-tag-md` | 36px |
| `.fb-tag-lg` | 40px |

```html
<span class="fb-tag">分类标签</span>
<span class="fb-tag fb-tag-selected">已选中</span>
<span class="fb-tag fb-tag-pill fb-tag-md">胶囊形大号</span>
```

> Tag 默认为展示元素，**不需要** `data-tp`。仅当 Tag 用作可点击筛选项（带 `onclick=`）时才补 `data-tp`，并按交互语义考虑改用 `fb-chip`（自带关闭按钮）。

### 3.9 Chip — `.fb-chip`
<!-- [FB-MODEL: fb-chip] -->

带关闭按钮的标签，用于"已选筛选项"等可移除场景。

```html
<span class="fb-chip" data-tp="M[XX]-P[YY]-T[ZZ]">
  已选标签
  <span class="fb-chip-close" onclick="..." data-tp="M[XX]-P[YY]-T[ZZ]">×</span>
</span>
```

> `fb-chip-close` 不在 INTERACTIVE_FB_CLASSES 里，但因为带 `onclick=` 会被 precheck 标签信号识别为交互元素——所以也必须有独立 `data-tp`。

### 3.10 Badge — `.fb-badge`
<!-- [FB-MODEL: fb-badge] -->

```html
<span class="fb-badge">99+</span>
<span class="fb-badge fb-badge-dot"></span>     <!-- 红点（无数字）-->
```

### 3.11 Action Bar — `.fb-action-bar`
<!-- [FB-MODEL: fb-action-bar] -->

**`[Must]` 用途**：统一底栏操作组（如"取消 / 保存"按钮组）。**单一 class 覆盖所有底栏场景**：frame 直接子层（sticky 贴底）/ modal 内（静态居底）/ drawer 内（静态居底）。CSS Custom Property 继承机制按 DOM 最近祖先值自动切换行为，PM **只需记一个 class**，环境自适应由真源 CSS 完成。

**`[Must]` 行为切换机制（CSS 变量就近继承）**：

| 父链路最近祖先 | 行为 | 实现机制 |
|---|---|---|
| `.{desktop|tablet|phone|h5|miniprogram}-frame` | sticky 贴底 + 背景 `--fb-bg-1` + padding `12px 24px` | 5 类 frame 容器声明默认变量基线（`:where(...)` 块）|
| `.fb-modal` | static + 透明背景 + padding `12px 20px` | `.fb-modal` 覆盖 `--bar-*` 变量为静态值 |
| `.fb-drawer` | 同 modal | `.fb-drawer` 覆盖（v3 期间与 modal 一致；分化时此处独立调整）|

**核心特性**：① 嵌套深度不敏感（不依赖 `>` 直子 / `+` 兄弟选择器）② 就近优先天然支持（无源码顺序仲裁）③ modal 嵌套 frame 时取 modal 行为（更近）③ 未来 modal/drawer 分化只需独立改其变量值

```html
<!-- 桌面 frame 内底栏（sticky 贴底）-->
<div class="desktop-frame">
  <!-- …sidebar / main 内容区… -->
  <div class="fb-action-bar">
    <button class="fb-btn fb-btn-default" data-tp="M[XX]-P[YY]-T[ZZ]">取消</button>
    <button class="fb-btn fb-btn-primary" data-tp="M[XX]-P[YY]-T[ZZ]">保存</button>
  </div>
</div>

<!-- modal 弹框内底栏（静态居底，自动适配，与 §3.2 modal 示例一致）-->
<div class="fb-modal-overlay is-visible">
  <div class="fb-modal">
    <div class="fb-modal-header">…</div>
    <div class="fb-modal-body">…</div>
    <div class="fb-action-bar">    <!-- 父链路 .fb-modal 自动覆盖为静态行为 -->
      <button class="fb-btn">取消</button>
      <button class="fb-btn fb-btn-primary">确认</button>
    </div>
  </div>
</div>

<!-- drawer 抽屉内底栏（静态居底，与 §3.4 drawer 示例一致）-->
<aside class="fb-drawer fb-drawer-right is-visible">
  <div class="fb-drawer-header">详情面板</div>
  <div class="fb-drawer-body">…</div>
  <div class="fb-action-bar">      <!-- 父链路 .fb-drawer 自动覆盖为静态行为 -->
    <button class="fb-btn">关闭</button>
    <button class="fb-btn fb-btn-primary">保存</button>
  </div>
</aside>
```

**`[Must]` 移动端 frame 底栏禁令**：`.phone-frame` / `.h5-frame` / `.miniprogram-frame` **直接子层禁用 `.fb-action-bar`**（违 `proto_cross_platform.md §三` 移动端应用 `fb-navbar` 顶部 + 「···」菜单的设计哲学）。precheck 扫到 → WARN，PM 应改用导航栏菜单方案。**例外**：移动端 frame 内**嵌套**的 `.fb-modal` / `.fb-drawer` 内可用（变量继承自动取 modal/drawer 静态行为）。

**`[Must]` 禁 inline position**：禁止 PM 写 `style="position:sticky"` / `style="position:fixed"` / `style="bottom:0"` — 行为由真源变量管控；inline 写法绕过组件协议且复现 v2 inline 污染（24 处实证）。precheck `check_inline_position_compliance` 扫 → WARN。

**`[Should]` 旧 class 迁移**：

v2 三 class（`fb-frame-bottom-bar` / `fb-modal-footer` / `fb-drawer-footer`）已**deprecated 别名**，行为与 `.fb-action-bar` 完全等价（无视觉差异）。迁移路径：

| 旧 v2 写法 | 新 v3 写法 |
|---|---|
| `<div class="fb-frame-bottom-bar">` | `<div class="fb-action-bar">` |
| `<div class="fb-modal-footer">` | `<div class="fb-action-bar">` |
| `<div class="fb-drawer-footer">` | `<div class="fb-action-bar">` |
| `<div class="fb-modal-footer fb-frame-bottom-bar">`（误叠加 16 处实证）| `<div class="fb-action-bar">` |

下游可用 `pm-workflow/scripts/migrate_action_bar.py` 自动迁移。

**v4 演进预案**（仅当 modal/drawer 行为分化时触发）：当前 modal 与 drawer 覆盖值字面相同（都是 static + transparent + 12px 20px）。若未来某天需差异化（如 drawer 内底栏需特殊 padding），直接独立改 `.fb-drawer` 块内 `--bar-*` 变量即可；CSS 变量继承机制天然支持就近优先，**无需重构 CSS 架构**。

### 3.12 Navbar — `.fb-navbar`（v2 支持 7 variant）
<!-- [FB-MODEL: fb-navbar] -->

**`[Must]` 用途**：移动类端口（`.phone-frame` / `.h5-frame` / `.miniprogram-frame` / `.tablet-frame`）**顶部 sticky 容器**——3 slot 灵活布局（left / center / right），按业务场景填充不同子组件。sticky 贴顶由本 class 真源自带（`position:sticky;top:0`），**PM 禁止写 inline `position:sticky` / `top:0`**。桌面 Web（`.desktop-frame`）用 sidebar 导航，不用本组件。

**`[Must]` 结构约束**：`.fb-navbar` 必须是移动类 `*-frame` 的**直接子元素**（置于首位，与主内容区同层）。具体 slot 填充按 7 variant 决定（详下表）。

**`[Must]` data-variant 显式声明**：PM 写 `.fb-navbar` 时**必须**在元素加 `data-variant="XXX"` 属性明示业务场景。precheck 按此精确判定（零启发式，避免 v1 启发式 5/5 FP 教训）。default `data-variant="detail"`（向后兼容现有用法，未声明等同 detail）。

**center slot 容器约定**：PM 总用 `.fb-nav-title` 作 center 子元素（已有 `flex:1 1 auto` 自动占据剩余空间居中），**即使内容是"已选 N/M"/"步骤 X/N"等非标题文字**。这保证 CSS 无需新增即支持 7 variant，且 center 永远居中。

### 7 variant slot 填充矩阵

| data-variant | 业务场景 | left slot | center slot (.fb-nav-title) | right slot | S4-35 .fb-nav-back |
|---|---|---|---|---|---|
| `detail` （默认）| 次级详情页（浏览态）| `.fb-nav-back` ← | 页面标题 | `.fb-nav-action` ≤1 | **强制** |
| `multi-select` | 列表多选态 | `.fb-btn-text`（取消）| "已选 N/M" | `.fb-btn-text`（全选/反选）| 不强制 |
| `confirm` | 表单/浮层确认 | `.fb-btn-text`（取消）| 表单标题 | `.fb-btn-primary`（确认）| 不强制 |
| `edit` | 编辑态密集操作 | `.fb-btn-text`（完成/保存）| 页面标题 | `.fb-nav-action`（···）| 不强制 |
| `list` | 列表入口页 | `.fb-nav-back`（可选）| 页面标题 | `.fb-nav-action` × N（筛选/搜索/新增）| 可选 |
| `workflow` | 向导分步 | `.fb-nav-back`（上一步）| "步骤 X/N" | `.fb-nav-action`（跳过）| **强制** |
| `home` | 主页 / 一级 Tab | — | logo/title | `.fb-nav-action` × N（搜索/我的）| 不强制 |

### 装饰背景 navbar 选择指引（modal-bg 场景）

**场景**：`.phone-frame.is-modal-bg` / `.h5-frame.is-modal-bg` / `.miniprogram-frame.is-modal-bg` 内的 navbar 仅作**背景层视觉表达**（modal 遮罩覆盖后不可交互，无返回/操作语义），与上方 7 variant"真在用"的语义假设不匹配。

**`[Should]` 推荐写法**（兜底而非新增 variant）：

```html
<!-- modal-bg 装饰: list variant 兜底（背景层无返回语义）-->
<div class="phone-frame is-modal-bg">
  <div class="fb-navbar" data-variant="list" style="opacity:0.5;">
    <span class="fb-nav-title">背景页面标题</span>
  </div>
  <div class="fb-modal-overlay is-visible">...</div>
</div>
```

**为什么选 list**：
- `detail` 会触发 S4-35 强制 `.fb-nav-back` → 加 nav-back 会污染触点表（无人会点的装饰触点）
- `list` 不强制 nav-back（precheck check_back_entry `BACK_REQUIRED_VARIANTS = {"detail", "workflow"}`）→ 合规

**纪律 4 项**：
- **`[Should]` 注释豁免必填**：`<!-- modal-bg 装饰: list variant 兜底（背景层无返回语义）-->` 显式声明意图（同 SSOT #58 D 方案注释豁免同型）
- **`[Should]` 仅渲染 `.fb-nav-title`**：去掉 `.fb-nav-back` / `.fb-nav-action`（避免无效触点 + 视觉简洁）
- **`[Should]` 加 `style="opacity:0.5"`**：视觉降权与"背景层失焦"表达一致
- **`[Recommended]` 真实业务对齐**：若背景层确是 detail/edit/workflow 业务页（审阅者能从 modal 缝隙认出），可写真实 variant + opacity:0.5；触点表登记的 `.fb-nav-back data-tp` **复用主业务帧的触点编号**（不新建 T 编号）

**`[Recommended]` ROI 判定**：本场景 ROI 1/4 不达机械兜底门槛（按 `workflow_maintenance_protocol.md §机械兜底必要性 ROI 决策标准`），保持文档级规范 + 注释豁免人工兜底；**不新增 `data-variant="placeholder"` 变体**（避免 7→8 variant 升级 + 5 处协调的重运维成本）。

### 7 variant HTML 示例

```html
<!-- 1. detail — 次级详情页（默认，向后兼容现有写法）-->
<div class="phone-frame">
  <div class="fb-navbar" data-variant="detail">
    <span class="fb-nav-back" data-tp="M[XX]-P[YY]-T[ZZ]">←</span>
    <span class="fb-nav-title">页面标题</span>
    <span class="fb-nav-action">
      <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">···</button>
    </span>
  </div>
  <!-- …主内容区… -->
</div>

<!-- 2. multi-select — 列表多选态（quotation-tool M03-P03-multi-select 同型）-->
<div class="phone-frame">
  <div class="fb-navbar" data-variant="multi-select">
    <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">取消</button>
    <span class="fb-nav-title">已选 2 / 8</span>
    <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">全选</button>
  </div>
  <!-- …多选列表… -->
  <div class="fb-action-bar" data-purpose="multi-select-batch">
    <button class="fb-btn fb-btn-danger" data-tp="M[XX]-P[YY]-D[ZZ]">批量删除</button>
    <button class="fb-btn fb-btn-default" data-tp="M[XX]-P[YY]-T[ZZ]">调整数量</button>
  </div>
</div>

<!-- 3. confirm — 表单/浮层确认 -->
<div class="phone-frame">
  <div class="fb-navbar" data-variant="confirm">
    <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">取消</button>
    <span class="fb-nav-title">编辑信息</span>
    <button class="fb-btn fb-btn-primary" data-tp="M[XX]-P[YY]-T[ZZ]">确认</button>
  </div>
  <!-- …表单… -->
</div>

<!-- 4. edit — 编辑态密集操作 -->
<div class="phone-frame">
  <div class="fb-navbar" data-variant="edit">
    <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">完成</button>
    <span class="fb-nav-title">草稿编辑</span>
    <span class="fb-nav-action">
      <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">···</button>
    </span>
  </div>
  <!-- …编辑内容… -->
</div>

<!-- 5. list — 列表入口页（多工具操作）-->
<div class="phone-frame">
  <div class="fb-navbar" data-variant="list">
    <span class="fb-nav-back" data-tp="M[XX]-P[YY]-T[ZZ]">←</span>
    <span class="fb-nav-title">订单列表</span>
    <span class="fb-nav-action">
      <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">筛选</button>
      <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">搜索</button>
      <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">新增</button>
    </span>
  </div>
  <!-- …列表… -->
</div>

<!-- 6. workflow — 向导分步 -->
<div class="phone-frame">
  <div class="fb-navbar" data-variant="workflow">
    <span class="fb-nav-back" data-tp="M[XX]-P[YY]-T[ZZ]">←</span>
    <span class="fb-nav-title">步骤 2 / 4</span>
    <span class="fb-nav-action">
      <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">跳过</button>
    </span>
  </div>
  <!-- …向导内容… -->
  <div class="fb-action-bar" data-purpose="workflow-nav">
    <button class="fb-btn fb-btn-default" data-tp="M[XX]-P[YY]-T[ZZ]">上一步</button>
    <button class="fb-btn fb-btn-primary" data-tp="M[XX]-P[YY]-T[ZZ]">下一步</button>
  </div>
</div>

<!-- 7. home — 主页 / 一级 Tab（无返回入口）-->
<div class="phone-frame">
  <div class="fb-navbar" data-variant="home">
    <span class="fb-nav-title" style="text-align:left">App 名称</span>
    <span class="fb-nav-action">
      <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">搜索</button>
      <button class="fb-btn fb-btn-text" data-tp="M[XX]-P[YY]-T[ZZ]">我的</button>
    </span>
  </div>
  <!-- …主页内容… -->
  <!-- 底部 Tab 切换（非 .fb-action-bar，是底部 Tab 组件待加；命名建议详 SSOT 双锚扩展）-->
</div>
```

### 子元素 class 总览

| class | 位置 | 用途 |
|-------|------|------|
| `.fb-nav-back` | 左 | 返回入口（←），须带 `data-tp` 触点编号；仅 detail/workflow variant 强制 |
| `.fb-nav-title` | 中 | center slot 容器（标题/计数/步骤等），自动居中（`flex:1 1 auto`）|
| `.fb-nav-action` | 右 | 操作按钮组容器（1 或多个）/「···」更多菜单，可省略 |
| 直接放 `.fb-btn` 系列 | 左/右 | multi-select/confirm/edit variant 时直接用按钮（取消/确认/全选/完成 等）|

### precheck 校验机制（S4-35 v2）

`precheck_stage4.check_back_entry` 按 `data-variant` 精确判定：
- `data-variant="detail"` 或缺省 → 强制含 `.fb-nav-back`
- `data-variant="workflow"` → 强制含 `.fb-nav-back`（上一步）
- 其他 variant → 不查 `.fb-nav-back`（用 [取消]/[完成] 等替代）

> **关联底栏**：移动端 frame 直接子层 `.fb-action-bar` 按 `data-purpose` 判定合规（详 §3.11 v2 + S4-28 v3 R2 重审）。两组件配合使用规范见 `proto_cross_platform.md §三 移动端操作布局矩阵`。

---

## 4. 列表组件

### 4.1 List + ListItem — `.fb-list` / `.fb-list-item`
<!-- [FB-MODEL: fb-list] -->

```html
<div class="fb-list">
  <div class="fb-list-item" data-tp="M[XX]-P[YY]-T[ZZ]">
    <span class="fb-icon">📁</span>
    <div class="fb-list-item-content">
      <div class="fb-list-item-title">条目标题</div>
      <div class="fb-list-item-desc">辅助说明</div>
    </div>
    <span class="fb-list-item-extra">→</span>
  </div>
  <div class="fb-list-item" data-tp="M[XX]-P[YY]-T[ZZ]">
    <!-- ... -->
  </div>
</div>
```

> 真实 PRD 中每个 list-item 的 `data-tp` 必须**不重复**——按列表行的索引或 ID 在 spec 触点表里登记不同的 T 编号。

### 4.2 Table — `.fb-table` / `.fb-table-row` / `.fb-table-cell`
<!-- [FB-MODEL: fb-table] -->

```html
<table class="fb-table">
  <thead class="fb-table-header">
    <tr>
      <th class="fb-table-header-cell">项目名</th>
      <th class="fb-table-header-cell">业主</th>
      <th class="fb-table-header-cell">电话</th>
      <th class="fb-table-header-cell">最近报价时间</th>
      <th class="fb-table-header-cell">状态</th>
    </tr>
  </thead>
  <tbody>
    <tr class="fb-table-row" data-tp="M[XX]-P[YY]-T[ZZ]">
      <td class="fb-table-cell">永和小区 12 号楼</td>
      <td class="fb-table-cell">王建国</td>
      <td class="fb-table-cell">18800001234</td>
      <td class="fb-table-cell">2026-05-08</td>
      <td class="fb-table-cell"><span class="fb-tag">进行中</span></td>
    </tr>
    <tr class="fb-table-row" data-tp="M[XX]-P[YY]-T[ZZ]">
      <!-- ... -->
    </tr>
  </tbody>
</table>
```

**适用场景**(参 `proto_data_display_selection.md §一` Q1-Q4 决策):
- 同屏字段数 ≥ 5(强对比)
- 用户主任务 = 扫描 / 排序 / 筛选 / 批量操作
- B 端专业高频(运营 / 商户后台 / 报价工具等)
- 桌面端为主(手机端表格难用,降级卡片)

**关键 modifier / 变体 class**:
- `.fb-table-row.is-selected`:批量勾选高亮
- `.fb-table-cell-num`:数字列右对齐 + tabular-nums 等宽对齐(金额 / 数量)
- `.fb-table-cell-actions`:操作列右对齐(编辑 / 删除按钮)

**触点 data-tp 规则**:每个 `.fb-table-row` 一个 data-tp;若行内有独立操作按钮,按钮单独 data-tp(参 §1.1 button)。

**反例**:手机端用全功能表格 → 横向滚 + 点不准 → 改卡片(参 §一 反 pattern);卡片 + 强字段对比场景用 → 滚动远 + 字段对比难 → 改表格。

### 4.3 Pagination — `.fb-pagination`
<!-- [FB-MODEL: fb-pagination] -->

```html
<div class="fb-pagination" data-tp="M[XX]-P[YY]-T[ZZ]">
  <span class="fb-pagination-item is-disabled">‹</span>
  <span class="fb-pagination-item">1</span>
  <span class="fb-pagination-item is-active">2</span>
  <span class="fb-pagination-item">3</span>
  <span class="fb-pagination-item">›</span>
</div>
```

> 当前 `fb-pagination` 整体作为单触点（precheck 用 wrapper class 识别）；若业务需要逐页区分触点，PM 可将 `data-tp` 移到每个 `fb-pagination-item` 上并附 `onclick=`，wrapper 可保留单触点或改为非交互 class。

---

## 5. 状态帧模板（L4）
<!-- [FB-MODEL: fb-state] -->

页面级状态——用于「整页空 / 整页加载 / 整页错 / 整页成功 / 整页禁用」场景。**这是阶段 4 PRD Agent 写状态帧时的最高 ROI 模板**。

| 类型 | class | 视觉特征 |
|------|-------|---------|
| 空状态 | `.fb-state.fb-state-empty` | 居中插画 + 标题（次要色）+ 副说明 |
| 加载态 | `.fb-state.fb-state-loading` | 居中旋转环 + 标题 |
| 错误态 | `.fb-state.fb-state-error` | 居中插画 + 标题（红色）+ 副说明 + 重试按钮 |
| 成功态 | `.fb-state.fb-state-success` | 居中绿色对勾 + 标题 + 副说明 |
| 受限态 | `.fb-state.fb-state-disabled` | 居中插画 + 标题（提示色）+ 副说明 |

**HTML 模板（通用骨架）：**

```html
<section class="fb-state fb-state-empty">
  <div class="fb-state-illustration">
    <!-- 引用 pm-workflow/rules/bujue-design-system/icon/NoData_LightMode.svg -->
    <img src="..." alt="">
  </div>
  <div class="fb-state-title">暂无数据</div>
  <div class="fb-state-subtitle">您还没有创建任何项目</div>
  <div class="fb-state-actions">
    <button class="fb-btn fb-btn-primary" data-tp="M[XX]-P[YY]-T[ZZ]">立即创建</button>
  </div>
</section>
```

**加载态特殊**：`.fb-state-loading` 自带 CSS 加载环，`fb-state-illustration` 内可不放内容：

```html
<section class="fb-state fb-state-loading">
  <div class="fb-state-illustration"></div>
  <div class="fb-state-title">加载中…</div>
</section>
```

**成功态特殊**：`.fb-state-success` 自带绿色对勾：

```html
<section class="fb-state fb-state-success">
  <div class="fb-state-illustration"></div>
  <div class="fb-state-title">提交成功</div>
  <div class="fb-state-subtitle">我们将在 24 小时内回复您</div>
</section>
```

---

## 6. 触点徽章 — `.tp-marker`
<!-- [FB-MODEL: tp-marker] -->

与 `proto_contract.md §四` 触点编号系统联动，已在 PRD 模板中预定义。

```html
<button class="fb-btn fb-btn-primary" data-tp="M[XX]-P[YY]-T[ZZ]">
  确认
  <span class="tp-marker">[ZZ]</span>
</button>
```

**[Must]** 同 `tp-wrap` 内 `.tp-marker` 文字 = 兄弟元素 `data-tp` 末段去掉 `T`/`D` 前缀的两位数字（precheck S4-24 校验：`tp-marker=01` 必须对应 `data-tp="...-T01"` 或 `data-tp="...-D01"`）。

`tp-marker` 默认蓝底白字，`position: absolute`，由调用方控制具体定位（top / right）。

---

## 端口适配速查

下表说明在不同 frame 容器内，组件的关键差异：

| 组件 | desktop-frame | phone-frame / miniprogram-frame | tablet-frame |
|------|--------------|-------------------------------|-------------|
| Button (md) | h=32, radius=8 | h=44, radius=4 | h=40, radius=4 |
| Input | h=40, radius=8 | h=44, radius=4 | h=40, radius=4 |
| Card | radius=8 | radius=4 | radius=4 |
| Modal | 居中 480px 宽 | 底部全宽上滑 | 居中 |
| Tag | h=24, font=12 | h=28, font=13 | h=24, font=12 |

PM 编写 PRD 时**不需要手动套用上表**——只需把组件放在正确的 `<div class="phone-frame">` / `<div class="desktop-frame">` 容器内，CSS 自动根据父容器选择匹配尺寸。

---

## 调用纪律（强制）

1. **优先用 fb 类**：阶段 4 PRD 中任何标准 UI 元素（按钮、输入框、卡片等），**优先**用 fb-fallback 提供的 class，**禁止**为它们重写 CSS
2. **缺失场景上报为 NB**：如果 fb-fallback 不能覆盖某场景（如需要 ActionSheet / Tooltip / DatePicker 等批次 2-5 才有的组件），PM **必须**作为 NB 上报，而不是自己合成新 class
3. **fb 类本身不要扩展为 proj 类**：proj 组件应基于 pub 抽象（`inherits: pub.L2.card`），可以扩展 pub 库的 base，但不能在使用处用 inline style 修改 fb 类视觉
4. **CSS 由 assemble.py 自动注入**：PM 在 prd 草稿（`prd_M[XX]_draft.html`）中**不要**重复粘贴 fb-fallback.css 内容，由 `assemble.py prd` 拼装时自动注入到主 PRD 的 `<style>` 块顶部
5. **[Must] 交互元素必含 `data-tp`**：拷贝模板时**必须**把 `data-tp="M[XX]-P[YY]-T[ZZ]"` 占位替换为实际触点编号；漏一个或保留 `[XX]/[YY]/[ZZ]` 字面值 → precheck S4-24 fail（详见本文件顶部「data-tp 占位约定」）

---

## 后续批次（未交付）

| 批次 | 内容 | 包含组件 |
|------|------|---------|
| 批次 2 | 移动端专属 | ActionSheet / Tabbar / Picker / PullRefresh |
| 批次 3 | 桌面端专属 | Tooltip / Popover / Dropdown |
| 批次 4 | 小程序独有差异 | （部分继承移动端，少数独有）|
| 批次 5 | 触控/无障碍/键盘细节 | focus-visible 适配 / aria 增强 |

---

## 变更记录

| 版本 | 变更内容 | 日期 |
|------|---------|------|
| v1.0 | 批次 1 初版：26 个 class 系列覆盖原子 + 表单 + 容器 + 列表 + 状态帧（L4）+ 触点徽章 | 2026-04-26 |
| v1.1 | 全模板补 `data-tp="M[XX]-P[YY]-T[ZZ]"` 占位（与 S4-24 联动）；修正 §6 `data-touchpoint` → `data-tp`；新增 §「data-tp 占位约定」并入调用纪律第 5 条 | 2026-05-05 |
