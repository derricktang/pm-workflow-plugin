# IconButton

Source: Figma `不觉 Web 组件` / IconButton ComponentSet (`70:2935`)
Figma URL: <https://www.figma.com/file/hxksE13w1AZQivOylmZ9gn/?node-id=70-2935>

4 axes · 480 enumerated variants. Square button containing only an icon (no text).

## Axes

| Axis | Values | CSS modifier |
|---|---|---|
| Style | Black / Black30 / DarkL3 / DarkL4 / F5 / Outline1 / Outline2 / Red / TextOnly / White | `icon-btn--<style>` |
| Size  | xs / s / m / l / xl / xxl (note: Figma uses lowercase here, unlike Button) | `icon-btn--<size>` |
| State | Default / Hover / Active / Disabled | `:hover` / `[disabled]` / `[data-state="..."]` |
| 圆角  | default / 胶囊 | omit / `icon-btn--radius-pill` |

## Usage

```html
<button class="icon-btn icon-btn--black icon-btn--m" aria-label="Add">
  <span class="icon-btn__icon"><svg>…</svg></span>
</button>
```

Always supply `aria-label` since the button has no text.
