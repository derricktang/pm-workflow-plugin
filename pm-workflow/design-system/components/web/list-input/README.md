# 列表项输入框 / List Input

Figma `不觉 Web 组件` / 列表项输入框 ComponentSet (`129:768`)
Source: <https://www.figma.com/file/hxksE13w1AZQivOylmZ9gn/?node-id=129-768>

3 axes · **8 enumerated variants**. Input row with drag handle (left) + delete (right).

## Axes

| Axis | Values |
|---|---|
| State | 默认 / 错误 |
| 错误提示文字 | 有 / 无 |
| 内容 | 空 / 已填 |

## Width: 452px column layout

## Usage

```html
<div class="list-input">
  <span class="list-input__label">备注</span>
  <div class="list-input__box">
    <span class="list-input__handle" aria-label="drag"><svg>…</svg></span>
    <input type="text" class="list-input__text" placeholder="请填写备注">
    <span class="list-input__handle list-input__handle--delete" aria-label="delete"><svg>…</svg></span>
  </div>
</div>

<!-- Error + 错误提示 -->
<div class="list-input list-input--error" data-state="error">
  <span class="list-input__label">备注</span>
  <div class="list-input__box">…</div>
  <div class="list-input__error">! 请填写必填项</div>
</div>
```
