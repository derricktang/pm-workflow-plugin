# Input

Figma `不觉 Web 组件` / Input ComponentSet (`87:642`)
Source: <https://www.figma.com/file/hxksE13w1AZQivOylmZ9gn/?node-id=87-642>

5 axes · **240 enumerated variants** (see `catalog.json`).

## Axes

| Axis | Values |
|---|---|
| State | Default / Error / Readonly |
| 图标  | 无 / 左 / 右 / 双 |
| 边框  | 1级 (#EBEBEB) / 2级 (#DBDBDB) |
| 背景  | white / 灰底 (#F5F5F5) / 暗底浅 (rgba(255,255,255,0.08)) / 暗底重 (rgba(255,255,255,0.15)) / 透明 |
| 内容  | 空 / 已填 |

## Fixed dimensions

240 × 40px · padding 0 12px · radius 8px.
Icon presence shrinks the icon-side padding to 8px.

## Usage

```html
<!-- Default + 空 -->
<input type="text" class="input" placeholder="请输入...">

<!-- 灰底 + 已填 -->
<input type="text" class="input input--bg-gray" value="内容文字">

<!-- 左 icon (use input-row wrapper) -->
<div class="input-row input--icon-left">
  <span class="input__icon">▸</span>
  <input type="text" placeholder="请输入...">
</div>

<!-- Error: soft red 3px stroke (NOT solid red border) -->
<input type="text" class="input input--error" data-state="error" value="内容">

<!-- Readonly -->
<input type="text" class="input" readonly value="只读内容">
```

## Note

Figma 页注："**全部删除 Focus 态**（黑边框生硬）" — no Focus styling. Error state
uses a **soft red 3px stroke** (#FDE6E9, the selected-soft token), NOT
solid #E60023. This is intentional per the designer.
