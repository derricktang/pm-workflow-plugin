# InputBlock

Figma `不觉 Web 组件` / InputBlock ComponentSet (`94:841`)
Source: <https://www.figma.com/file/hxksE13w1AZQivOylmZ9gn/?node-id=94-841>

4 axes · **24 enumerated variants**. Composition of label + Input + (optional helper/counter).

## Axes

| Axis | Values |
|---|---|
| State | Default / Error / Readonly |
| 必填  | 是 / 否 (asterisk shown when 是) |
| 帮助  | 有 / 无 (`?` icon next to label) |
| 计数  | 有 / 无 (counter `0/100` at bottom-right) |

## Width: 452px

## Usage

```html
<!-- Required + help + counter + Default -->
<div class="input-block">
  <div class="input-block__label-row">
    <span>Label</span>
    <span class="input-block__required">*</span>
    <span class="input-block__help-icon">?</span>
  </div>
  <input type="text" class="input input-block__input" placeholder="请输入...">
  <div class="input-block__bottom">
    <span class="input-block__helper"></span>
    <span class="input-block__counter">0/100</span>
  </div>
</div>

<!-- Error -->
<div class="input-block" data-state="error">
  <div class="input-block__label-row"><span>Label</span><span class="input-block__required">*</span></div>
  <input type="text" class="input input--error" data-state="error" value="invalid">
  <div class="input-block__bottom">
    <span class="input-block__helper">错误提示文字</span>
  </div>
</div>
```
