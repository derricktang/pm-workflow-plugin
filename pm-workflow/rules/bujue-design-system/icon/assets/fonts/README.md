# 字体文件目录（assets/fonts/）

> 不觉规范使用**双字体策略**：中文用 **Source Han Sans CN**，越南语用 **Be Vietnam Pro**。
> 两者均为 **SIL OFL 开源协议**，可商用免费。

---

## 一、需要下载的字体文件

把下面的字体文件下载好后**放到本目录**（`assets/fonts/`），文件名必须严格按下表，否则 `setup.md` 中的 `@font-face` 路径会找不到。

| 文件名（必须） | 字重 | 用途 |
|------|------|------|
| `SourceHanSansCN-Normal.otf` | 350 | 中文默认正文 |
| `SourceHanSansCN-Regular.otf` | 400 | 中文模块标题 / 弱强调 |
| `SourceHanSansCN-Medium.otf` | 500 | 中文大标题 / 关键层级 |
| `BeVietnamPro-Variable.ttf` | 350~500 | 越南语全字重（可变字体） |

---

## 二、Source Han Sans CN（思源黑体）

### 下载来源

GitHub 官方仓库：**adobe-fonts/source-han-sans**
- 仓库地址：`https://github.com/adobe-fonts/source-han-sans`
- 推荐下载：Releases 页面的 `SourceHanSansCN.zip`（仅简体中文子集，约 20 MB）
- 完整包：`SourceHanSans.ttc.zip`（含所有 CJK 子集，约 130 MB，**多数项目不需要**）

### 字重对应关系

下载的 ZIP 解压后，会有 7 档字重的 `.otf` 文件：

| 不觉档位 | 数值 | 对应文件名 |
|---------|-----|----------|
| Normal | 350 | `SourceHanSansCN-Normal.otf` |
| Regular | 400 | `SourceHanSansCN-Regular.otf` |
| Medium | 500 | `SourceHanSansCN-Medium.otf` |

> 其他字重（ExtraLight 250 / Light 300 / Bold 700 / Heavy 900）不觉规范不使用，可不放入项目。

### License

- **SIL Open Font License (OFL) 1.1**
- 可商用免费，可嵌入产品 / 网站 / App
- 详见仓库根目录的 `LICENSE.txt`

---

## 三、Be Vietnam Pro（越南语字体）

### 下载来源

**Google Fonts**：`https://fonts.google.com/specimen/Be+Vietnam+Pro`

或 GitHub：**bettergui/BeVietnamPro**
- 仓库地址：`https://github.com/bettergui/BeVietnamPro`

### 推荐下载方式

下载 **Variable Font 版本**（一个文件覆盖所有字重）：
- 文件名：`BeVietnamPro[wght].ttf` 或 `BeVietnamPro-VariableFont_wght.ttf`
- **重命名为** `BeVietnamPro-Variable.ttf` 放入本目录

如果只下载到固定字重版本，按以下对照重命名：

| 不觉档位 | 数值 | 对应文件 |
|---------|-----|---------|
| Normal | 350 | 用 Light (300) 或 Regular (400) 接近 |
| Regular | 400 | `BeVietnamPro-Regular.ttf` |
| Medium | 500 | `BeVietnamPro-Medium.ttf` |

> 若用固定字重版本，需要在 `setup.md` 的 `@font-face` 里改为 3 段独立声明（参考 Source Han Sans CN 的写法）。

### License

- **SIL Open Font License (OFL) 1.1**
- 可商用免费

---

## 四、为什么要双字体策略？

简单说：**Source Han Sans CN 不能很好地渲染越南语**。

- Source Han Sans CN（CN 子集）虽然包含基础拉丁字符，但**没有为越南语**特有的双层变音符号（如 `ấ ố ợ`）做字距与堆叠优化
- Be Vietnam Pro 专为越南语设计，字符更地道

CSS `font-family` 是**按字符级 fallback** 的：

```css
font-family: 'Source Han Sans CN', 'Be Vietnam Pro', ...;
```

- 中文字符 → Source Han Sans CN 命中
- 越南语字符 → Source Han Sans CN 渲染不好，自动 fallback 到 Be Vietnam Pro
- 无需手动切换

详见 `foundations/typography.md` § 一。

---

## 五、下载完成后的目录结构

```
assets/fonts/
├── README.md                              ← 本文件
├── SourceHanSansCN-Normal.otf             ← 你下载的
├── SourceHanSansCN-Regular.otf            ← 你下载的
├── SourceHanSansCN-Medium.otf             ← 你下载的
└── BeVietnamPro-Variable.ttf              ← 你下载的
```

---

## 六、引入字体（参考）

`@font-face` 声明详见 `setup.md` § Font setup。简述：

```css
@font-face {
  font-family: 'Source Han Sans CN';
  font-weight: 350;
  src: url('/assets/fonts/SourceHanSansCN-Normal.otf') format('opentype');
}
/* ...其他字重同理 */

@font-face {
  font-family: 'Be Vietnam Pro';
  font-weight: 350 500;
  src: url('/assets/fonts/BeVietnamPro-Variable.ttf') format('truetype-variations');
}

body {
  font-family: 'Source Han Sans CN', 'Be Vietnam Pro', -apple-system, "PingFang SC", sans-serif;
  font-weight: 350;
  letter-spacing: 0;
}
```
