# LoadingButton

Source: Figma `不觉 Web 组件` / LoadingButton ComponentSet (`75:2950`)
Figma URL: <https://www.figma.com/file/hxksE13w1AZQivOylmZ9gn/?node-id=75-2950>

3 axes · 70 enumerated variants. Two animated dots, no text.

## Axes

| Axis | Values | CSS modifier |
|---|---|---|
| Style | Black / Black30 / DarkL3 / DarkL4 / F5 / Outline1 / Outline2 / Red / TextOnly / White | `loading-btn--<style>` |
| Size  | XS / S / M / L / XL / XXL | `loading-btn--<size>` |
| 圆角  | default / 胶囊 | omit / `loading-btn--radius-pill` |

No State axis — LoadingButton is itself a "loading" state representation.
The button is always rendered with `disabled` to prevent re-clicks while loading.

## Usage

```html
<button class="loading-btn loading-btn--black loading-btn--m" disabled aria-label="Loading">
  <span class="loading-btn__dots" aria-hidden="true">
    <span class="loading-btn__dot"></span><span class="loading-btn__dot"></span>
  </span>
</button>
```

The dots animate via CSS keyframes; no JS needed. Dots inherit `currentColor`
so they swap between `#FFF` (on dark Styles) and the text color (on light
Styles) per the Figma note "深底白点浅底文字色点".
