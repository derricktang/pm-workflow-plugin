# Button

Source: Figma `不觉 Web 组件` / Button ComponentSet (`12:1442`)
Figma URL: <https://www.figma.com/file/hxksE13w1AZQivOylmZ9gn/?node-id=12-1442>

5 axes · 1000 enumerated variants (see `components.json` → `variants[]`).

## Axes

| Axis | Values | CSS modifier prefix |
|---|---|---|
| Style  | Black / Black30 / DarkL3 / DarkL4 / F5 / Outline1 / Outline2 / Red / TextOnly / White | `btn--<style>` (lowercase) |
| Size   | XS / S / M / L / XL / XXL | `btn--<size>` (lowercase) |
| State  | Default / Hover / Active / Disabled | `:hover` / `:active` / `[disabled]` (or `[data-state="..."]` for static) |
| 图标   | none / left / right / both | `btn--icon-{left,right,both}` (omit for none) |
| 圆角   | default / pill | omit / `btn--radius-pill` |

## Usage

```html
<!-- Black M Default -->
<button class="btn btn--black btn--m">Button</button>

<!-- Outline1 L with left icon -->
<button class="btn btn--outline1 btn--l btn--icon-left">
  <span class="btn__icon">…</span>
  Button
</button>

<!-- Red XL pill -->
<button class="btn btn--red btn--xl btn--radius-pill">Button</button>

<!-- Disabled (works on any combination) -->
<button class="btn btn--black btn--m" disabled>Button</button>

<!-- Force hover state in a static mockup -->
<button class="btn btn--black btn--m" data-state="hover">Button</button>
```

## Variant lookup

For static prototype assembly, downstream agents should consume
`components.json` → `components[name="button"].variants[]` to pick a
named variant (e.g. `"black-m-default"`, `"red-xl-pill-icon-left-hover"`)
and copy its `exampleHtml` verbatim. Do not compose modifier classes
manually unless the desired combination is not present in `variants[]`.

## Tokens referenced

- `--color-light-text-1`, `--color-light-white`, `--color-light-bg-1/2/3`,
  `--color-light-border-1/2`, `--color-light-disabled`, `--color-light-error`
- `--color-dark-bg-3/4/5` (used for DarkL3 / DarkL4 styles)
- `--radius-4`, `--radius-8`, `--radius-pill`
- `--text-web-body-lg-normal` (default text style)

## Known caveats (this sync)

- Visual specs ground-truthed only for Style=Black/Outline1, States Default/Hover/Disabled.
- Other Styles (Black30, DarkL3/4, F5, Outline2, Red, TextOnly, White) are
  inferred from token-name semantics and may need spot-fixes after visual review.
- Size L/XL height/padding inferred linearly from M=32/8 and XXL=56/16 anchors;
  re-sample if pixel-perfect alignment is critical.
- `:hover` darker shades for non-Black styles are best-effort approximations
  (e.g. Red hover #B8001B), not Figma-sampled.
