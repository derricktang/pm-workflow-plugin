# Iconfont 字体图标目录（assets/iconfont/）

> 不觉规范使用阿里 iconfont 项目「WEB_3.0」（项目 ID：5123795），共 **200 个图标**。

---

## 一、本目录文件清单

| 文件 | 作用 | 必需 |
|------|------|------|
| `iconfont.css` | 字体声明 + 200 个图标的 unicode 映射 | ✅ 必需 |
| `iconfont.woff2` | WOFF2 字体文件（现代浏览器优先） | ✅ 必需 |
| `iconfont.woff` | WOFF 字体文件（兼容性 fallback） | ✅ 推荐 |
| `iconfont.ttf` | TrueType 字体文件（最广兼容） | ✅ 推荐 |

> 这些文件是从 iconfont.cn 项目页直接下载的离线包。`iconfont.css` 顶部已经把 woff2 用 base64 内嵌了，相对路径的 woff/ttf 作为 fallback。**全部文件放在同一目录即可工作，无需联网**。

---

## 二、如何引入项目

### 方案 A：直接 import 整个 css（推荐）

```css
/* 在你的全局样式 main.css 顶部 */
@import './assets/iconfont/iconfont.css';
```

或者在 JS / TS 入口：

```jsx
// src/main.jsx
import './assets/iconfont/iconfont.css';
```

### 方案 B：拆开管理（高级用法）

如果你想控制字体声明和类名映射的位置：

```css
/* 你自己的 styles/iconfont.css */
@font-face {
  font-family: 'iconfont';
  src: url('/assets/iconfont/iconfont.woff2') format('woff2'),
       url('/assets/iconfont/iconfont.woff') format('woff'),
       url('/assets/iconfont/iconfont.ttf') format('truetype');
}

.icon-bujue {
  font-family: 'iconfont' !important;
  font-style: normal;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 然后单独 @import 类名映射部分（从 iconfont.css 复制 .icon-xxx 类） */
```

---

## 三、使用方式

```html
<!-- 必须搭配 .icon-bujue 基础类 + 具体图标类 -->
<i class="icon-bujue icon-a-chakanxi" 
   style="color: var(--bj-text-333)"></i>
```

**完整 200 个图标列表** + 中英映射详见根目录 `icon-discovery.md`。

**视觉预览**（带搜索 / 颜色切换 / 分类筛选）：根目录 `iconfont-preview.html`，用浏览器打开即可。

---

## 四、颜色规则

| 标记 | 类型 | 数量 | 颜色控制 |
|-----|------|-----|---------|
| 🎨 | 改色图标 | 189 | CSS `color` token 控制（如 `var(--bj-text-333)`） |
| 🌈 | 彩色图标 | 11 | **不可改色**，但这 11 个**不在本字体里** —— 它们是独立的彩色 SVG |

⚠️ **重要**：iconfont 字体里虽然存在 `.icon-pdf` / `.icon-word` 等扁平字体版本，但**不觉规范禁止使用**。文件类型徽标必须用独立的 SVG 资产（在 `../icons/file-types/` 目录），保持原色。

详见 `icon-discovery.md` § 一、§ 四。

---

## 五、更新 iconfont 字体

iconfont.cn 项目修改后，需要重新下载并替换本目录文件：

1. 登录 iconfont.cn，进入项目「WEB_3.0」（ID：5123795）
2. 项目主页右上角点「下载至本地」
3. 解压下载的 zip
4. 把 `iconfont.css` / `iconfont.woff2` / `iconfont.woff` / `iconfont.ttf` 替换到本目录
5. **同时更新** `icon-discovery.md` 和 `iconfont-preview.html`（建议联系负责设计系统的同学）

> ⚠️ 文件 hash 后缀可能变化（如 `font_5123795_06mxe0ztuy73`），不影响使用，但若用 CDN 引入需要同步 URL。

---

## 六、命名待办（同步设计师）

iconfont 项目里有几个命名不规范的图标，建议下次清理时一并修复：

- `.icon-skp-`（带尾 `-`）→ 重命名为 `.icon-sketchup`
- `.icon-yasuobao-chunse1`（带数字后缀）→ 重命名为 `.icon-archive`
- 4 个推荐双箭头当前用 `-heise/-hei` 后缀 → 建议新增无后缀 base 版本（如 `.icon-a-shuangjiantouxiangzuoxi`）
- 28 个旧的双箭头多色变体 → 建议从 iconfont 项目中删除（已从本规范文档中移除）

详见 `icon-discovery.md` § 七。
