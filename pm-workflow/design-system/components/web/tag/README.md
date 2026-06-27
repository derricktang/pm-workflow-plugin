# Tag

Figma `不觉 Web 组件` / Tag ComponentSet (`176:524`)
Source: <https://www.figma.com/file/hxksE13w1AZQivOylmZ9gn/?node-id=176-524>

6 axes · **540 enumerated variants**.

## Axes

| Axis | Values | CSS modifier |
|---|---|---|
| 状态  | Default / Selected / Disabled | `:hover` / `tag--selected` / `tag--disabled` |
| 高度  | 20 / 28 / 40 | `tag--h-20` / `tag--h-28` / `tag--h-40` |
| 圆角  | 4 / 8 / 100 | `tag--r-4` / `tag--r-8` / `tag--r-pill` |
| 图标  | 无 / 左 / 右 | omit / `tag--icon-left` / `tag--icon-right` |
| 样式  | 浅描边 / 浅填充 / 深实心 / 暗描边 / 暗 L4 / 暗 L5 | `tag--style-outline / -fill / -solid / -dark-outline / -dark-l4 / -dark-l5` |
| OOS   | 否 / 是 (仅 40h+8r) | omit / `tag--oos` (changes inner layout) |

## Usage

```html
<!-- 浅填充 28h Default -->
<span class="tag tag--h-28 tag--r-4 tag--style-fill">标签</span>

<!-- 暗 L4 28h Default — 用在 #151515 暗底容器内 -->
<span class="tag tag--h-28 tag--r-4 tag--style-dark-l4">标签</span>

<!-- 胶囊 + 左 icon + Selected -->
<span class="tag tag--h-28 tag--r-pill tag--style-fill tag--selected tag--icon-left">
  <span class="tag__icon">✓</span>标签
</span>

<!-- OOS 缺货 -->
<span class="tag tag--h-40 tag--r-8 tag--style-fill tag--oos">
  <span class="tag__text-area">标签</span>
  <span class="tag__oos-badge">缺货</span>
</span>
```

## Page note

Figma 副标题："样式：浅描边/浅填充/深实心/暗描边/暗L4/暗L5。OOS 仅 40h+8r。"
6 样式覆盖浅底（前 3）+ 暗底（后 3）容器场景。OOS 缺货态只在 40h+8r 上有，
inner 结构变成 [Text Area + 36×20 黑色 "缺货" Badge]。
