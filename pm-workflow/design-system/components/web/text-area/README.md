# TextArea

Figma `不觉 Web 组件` / TextArea ComponentSet (`102:841`)
Source: <https://www.figma.com/file/hxksE13w1AZQivOylmZ9gn/?node-id=102-841>

5 axes · **120 enumerated variants**.

## Axes

| Axis | Values |
|---|---|
| State | Default / Error / Readonly |
| 边框  | 1级 (#EBEBEB) / 2级 (#DBDBDB) |
| 背景  | white / 灰底 / 暗底浅 / 暗底重 / 透明 |
| 内容  | 空 / 已填 |
| 计数  | 有 / 无 |

## Fixed dimensions

452 × 96px default · padding 8 12px · radius 8px.

## Usage

```html
<!-- Default + 空 + 无计数 -->
<div class="text-area-wrap">
  <textarea placeholder="请输入..."></textarea>
</div>

<!-- 已填 + 计数 -->
<div class="text-area-wrap">
  <textarea>多行内容文字示例。</textarea>
  <span class="text-area-wrap__counter">12/100</span>
</div>

<!-- Error -->
<div class="text-area-wrap text-area--error" data-state="error">
  <textarea>内容</textarea>
  <span class="text-area-wrap__counter">5/100</span>
</div>
```

Background axis modifiers: `text-area--bg-gray` / `text-area--bg-dark-soft` /
`text-area--bg-dark-strong` / `text-area--bg-transparent`. Border:
`text-area--border-2`.
