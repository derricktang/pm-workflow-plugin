# 不觉设计系统 · 仓库索引

> 给下游 agent（如页面级高保真原型生成器）的 **整体架构地图**。读这一份就知道仓库里有什么、放在哪、按什么规则组织。

最后同步：**2026-05-12** · 维护者 agent：`figma-component-builder` (本仓库 `.claude/agents/`)

---

## 1. 高层结构

```
ui-component/
├── tokens/                ← ★ 共享：颜色 / 间距 / 圆角 / 阴影 / 字体
├── icons/                 ← ★ 共享：所有 SVG 图标，分类目录
├── components/            ← 按消费平台拆分
│   ├── catalog.json       ← 平台索引（Web vs App）
│   ├── web/               ← Web 端组件库（桌面浏览器）
│   │   ├── catalog.json   ← Web 平台 ComponentSet 列表
│   │   ├── button/
│   │   ├── icon-button/
│   │   ├── ...
│   └── app/               ← App 端组件库（移动 / Pad 触控）
│       ├── catalog.json   ← 当前空（未启动）
│       └── (待 /build-ui --platform=app 填充)
├── _prototype.css         ← showcase 页面 chrome（仅本仓库自用）
├── index.html             ← 本仓库的可视化总览页（仅自用，下游不需要）
├── CLAUDE.md              ← 本仓库规则（agent 启动自动读）
├── INDEX.md               ← 本文件
├── README.md
├── .gitignore
└── .figma-sync/           ← 内部同步状态（gitignored，下游不读）
    ├── state-tokens.json        sync ledger for tokens
    ├── state-components.json    sync ledger for components
    ├── *-variants-raw.json      intermediate parse cache
    └── .gen-*.py                code-gen scripts
```

**3 个共享/分平台层**
- 共享层（任何平台都用同一份）：`tokens/`、`icons/`
- 平台层（Web 一份、App 一份）：`components/web/`、`components/app/`

---

## 2. 下游 agent 的消费协议

**核心读取顺序**：

1. `tokens/catalog.json` —— 拿全部 CSS 变量定义（颜色/间距/字体等）。78 个 token。
2. `icons/catalog.json` —— 拿全部图标元数据（SVG 文件路径 / 默认色 / 尺寸）。51 个 icon。
3. `components/catalog.json` —— 看支持的**平台**（web / app）。
4. `components/<platform>/catalog.json` —— 列出该平台所有 ComponentSet 索引。
5. `components/<platform>/<set>/catalog.json` —— 拿某个 ComponentSet 的全量 variant 描述。

**实际开发流程**（高保真原型生成 agent 视角）：

```text
任务：生成一个 Web 登录页面
1. Read tokens/catalog.json + icons/catalog.json
2. Read components/web/catalog.json
3. 查需要 Button / Input → Read components/web/button/catalog.json
                              + components/web/input/catalog.json
4. 在每个 catalog.json.variants[] 里按需求挑变体（如 black-m-default / default）
5. 直接拷贝 variants[*].exampleHtml 到生成的页面里
6. 页面 <link rel="stylesheet"> 引入：
     tokens/index.css
     components/web/button/button.css
     components/web/input/input.css
   等需要的 CSS 文件
7. 装配完成，零额外 CSS 编写
```

**为什么 catalog.json 是入口？**
- 每个 catalog 是**自描述**的（schema 内嵌在文件开头的 `schema` 字段里）
- 不需要扫文件、不需要解析 CSS、不需要猜测命名
- `variants[*].exampleHtml` 是开箱即用的 HTML 片段，含正确的 modifier class 组合

---

## 3. 数据来源

两个 Figma 源文件：

| fileKey                    | 名称              | 用途           | 落在仓库的什么位置 |
|----------------------------|------------------|----------------|--------------------|
| `B1KFmcQrMgQiqKsyppory3`   | 不觉组件库        | tokens + icons | `tokens/` + `icons/` |
| `hxksE13w1AZQivOylmZ9gn`   | 不觉 Web 组件      | Web components | `components/web/` |
| _(待添加)_                  | 不觉 App 组件      | App components | `components/app/` |

**全部通过官方 `figma-developer-mcp` MCP server 读取**。本仓库不直接调 `https://api.figma.com`。

---

## 4. 当前实现状态

### Tokens (`tokens/`)

| 类别 | 数量 | CSS 文件 | catalog |
|---|---|---|---|
| Colors light | 15 | `tokens/colors.css` | `tokens/catalog.json` `categories.colors-light[]` |
| Colors dark  | 15 | 同上                | `categories.colors-dark[]` |
| Spacing      | 9  | `tokens/spacing.css` | `categories.spacing[]` |
| Radii        | 6  | 同上                | `categories.radii[]` |
| Effects      | 5  | `tokens/effects.css` | `categories.effects[]` |
| Typography   | 28 | `tokens/typography.css` | `categories.typography[]` |
| **总计**     | **78** | | |

### Icons (`icons/`)

| 分类 | 数量 | 路径 |
|---|---|---|
| direction-arrow | 16 | `icons/direction-arrow/*.svg` |
| view-search     | 6  | `icons/view-search/*.svg` |
| edit-action     | 29 | `icons/edit-action/*.svg` |
| **总计**         | **51** | (全 `currentColor` 主色，部分含 `#666` 次色) |

### Components — Web (`components/web/`)

| name | displayName | 变体数 | Figma node |
|---|---|---|---|
| button         | Button             | 1000 | `12:1442` |
| icon-button    | IconButton         | 480  | `70:2935` |
| loading-button | LoadingButton      | 70   | `75:2950` |
| input          | Input              | 240  | `87:642`  |
| input-block    | InputBlock         | 24   | `94:841`  |
| text-area      | TextArea           | 120  | `102:841` |
| list-input     | 列表项输入框        | 8    | `129:768` |
| tag            | Tag                | 540  | `176:524` |
| tab-underline  | Tab/下划线型        | 27   | `198:166` |
| tab-toggle     | Tab/胶囊·Toggle    | 162  | `199:686` |
| tab-segmented  | Tab/胶囊·分段容器   | 54   | `200:633` |
| **合计**        | **11 sets**        | **2725** | |

**待补**（参见 `components/web/catalog.json` `status.pendingPages[]` 完整信息）：

| Figma page | title | 状态 |
|---|---|---|
| 1:6  | 卡片 / Card           | **8 个 ComponentSet 已发现**：3 个 ready-to-implement（作品卡片 40 / 作品详情卡 32 / 资材展示卡 4），5 个 Figma 标紫色虚线 WIP（资材卡片、Component 1、SKU、Group 1004、创意版-素材卡）|
| 1:7  | 导航 / NavigationBar  | Figma 该页面为空，未画 |
| 1:8  | 表格 / Table          | Figma 该页面为空，未画 |
| 1:9  | 弹窗 / Modal          | Figma 该页面为空，未画 |
| 1:10 | 表单 / Checkbox · Radio · Switch · Dropdown | Figma 该页面为空，未画 |

### Components — App (`components/app/`)

未启动。等用户运行 `/build-ui --platform=app <figma-app-url>` 填充。

---

## 5. Schema 速查

### `tokens/catalog.json`

```jsonc
{
  "schemaVersion": 1,
  "kind": "tokens",
  "totalTokens": 78,
  "categories": {
    "colors-light": [{ "cssVar": "--color-light-text-1", "value": "#333333", "displayName": "白版/文字 #333", "description": "正文主色 / 标题", "figmaNode": "1:2" }, ...],
    "colors-dark": [...],
    "spacing": [...],
    "radii": [...],
    "effects": [...],
    "typography": [...]
  }
}
```

### `icons/catalog.json`

```jsonc
{
  "schemaVersion": 1,
  "kind": "icons",
  "icons": [{
    "name": "arrow-up",
    "displayName": "箭头-上",
    "category": "direction-arrow",
    "file": "icons/direction-arrow/arrow-up.svg",
    "size": { "width": 24, "height": 24 },
    "defaultColor": "currentColor",
    "secondaryColors": [],
    "tokensReferenced": ["--color-light-text-1"]
  }, ...]
}
```

### `components/catalog.json` (top-level)

```jsonc
{
  "schemaVersion": 4,
  "kind": "components-index",
  "platforms": {
    "web": { "catalog": "components/web/catalog.json", "figmaFile": "hxksE13w1AZQivOylmZ9gn", "figmaFileName": "不觉 Web 组件" },
    "app": { "catalog": "components/app/catalog.json", "figmaFile": null, "figmaFileName": null }
  }
}
```

### `components/<platform>/catalog.json`

```jsonc
{
  "schemaVersion": 1,
  "kind": "components-platform-index",
  "platform": "web",
  "totalComponentSets": 8,
  "totalVariants": 2482,
  "componentSets": [{
    "name": "button",
    "displayName": "Button",
    "variantCount": 1000,
    "catalog": "components/web/button/catalog.json",
    "files": { "css": "components/web/button/button.css", "readme": "...", "html": null, "js": null, "thumb": null }
  }, ...]
}
```

### `components/<platform>/<set>/catalog.json`

```jsonc
{
  "schemaVersion": 2,
  "kind": "component",
  "name": "button",
  "displayName": "Button",
  "platform": "web",
  "figmaFileKey": "hxksE13w1AZQivOylmZ9gn",
  "figmaNodeId": "12:1442",
  "axes": [
    {"name": "Style", "values": ["Black","Black30","DarkL3", ...]},
    {"name": "Size",  "values": ["XS","S","M","L","XL","XXL"]},
    ...
  ],
  "states": [{"selector":":hover","trigger":"pseudo","description":"..."}],
  "modifiers": [{"class":"btn--black","axis":"Style","value":"Black"}, ...],
  "slots": [...],
  "tokensReferenced": ["--color-light-text-1", ...],
  "variantCount": 1000,
  "variants": [{
    "name": "black-m-default",
    "figmaNodeId": "6:100",
    "figmaVariantPath": "Style=Black, Size=M, State=Default, 图标=无, 圆角=默认",
    "modifiers": ["btn--black","btn--m"],
    "attrs": {"disabled": false, "data-state": null},
    "exampleHtml": "<button class=\"btn btn--black btn--m\">Button</button>"
  }, ...]
}
```

---

## 6. 命令

```bash
# Tokens / icons（共享层，--platform 被忽略）
/build-ui https://www.figma.com/design/B1KFmcQrMgQiqKsyppory3/?node-id=1-2     # 颜色-白版
/build-ui https://www.figma.com/design/B1KFmcQrMgQiqKsyppory3/?node-id=20-3    # 编辑图标

# Web 端组件（默认 --platform=web，已知 fileKey）
/build-ui https://www.figma.com/design/hxksE13w1AZQivOylmZ9gn/?node-id=1-2     # Button 页

# App 端组件（必须显式 --platform=app）
/build-ui --platform=app https://www.figma.com/design/<APP_FILEKEY>/?node-id=1-2
```

其他 flags：`--incremental` `--dry-run` `--force` `--only=name1,name2`。

---

## 7. 设计原则（速查）

| 原则 | 在哪里实现 |
|---|---|
| 1:1 Figma 还原（不加棋盘格、不加边框、verbatim 文案） | `CLAUDE.md` `## 1:1 design reproduction` |
| 参数化源 + flat manifest 出口 | 每个 set 的 CSS 是 BEM 参数化，catalog `variants[]` 全枚举 |
| 视觉规格必须采样实测 | 每个 Style/State 至少 1 个 MCP `get_figma_data` 采样；不靠 token 名推断 |
| 共享 vs 平台 | tokens/icons 共享，components 按 web/app 拆分 |
| Internal vs Outbound | `.figma-sync/` 内部、gitignored；其他都是对外契约 |

详细约束在 **`CLAUDE.md`**。

---

*本文件由 `figma-component-builder` agent 在每次重大结构变更时手动同步。*
