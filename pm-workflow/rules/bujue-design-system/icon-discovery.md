# 不觉设计系统：图标规范（icon-discovery.md）

> ⚠️ **内建兜底 pub 库（单库,2026-05-16 定案）**：本文件属于「pub 库（正式组件库,不觉设计系统）」的**内建兜底库** `pm-workflow/rules/bujue-design-system/`——工作流自带、git 跟踪长期保留,当前**唯一 pub 源,可走 `workflow-evolution` skill 直改**（**非**"外部接管 / 只读不可改"）。正式 pub 库接入为后续:终态由独立仓 `pm-group/bujue-design-system` 经 skill/CLI 消费(纯 Python CLI + 显式 `--root`,非 Read plugin),届时本库降离线 fallback,缺陷按 SSOT #31 NB 上报。详 `workflow_architecture_map.md §六` 组件库二元边界 + memory `pub_library_distribution_decision`。

> 来源：阿里 iconfont 项目「WEB_3.0」（项目 ID：5123795）
> 字体名：`iconfont`，类名前缀：`.icon-`，共 **200 个图标**
> 颜色规则：189 个 🎨 改色 + 11 个 🌈 彩色（不可改色）

---

## 〇、两种颜色规则

| 标记 | 类型 | 数量 | 资产形态 | 说明 |
|-----|------|-----|---------|------|
| 🎨 | **改色图标** | 189 | iconfont 字体 | 用 CSS `color` token 控制颜色 |
| 🌈 | **彩色图标** | 11 | 独立 SVG 资产 | **原色不可修改**，文件类型徽标 |

---

## 一、引入方式

### 1.1 改色图标（字体）

```css
@font-face {
  font-family: 'iconfont';
  src: url('//at.alicdn.com/t/c/font_5123795_06mxe0ztuy73.woff2?t=1775808309000') format('woff2'),
       url('//at.alicdn.com/t/c/font_5123795_06mxe0ztuy73.woff?t=1775808309000') format('woff'),
       url('//at.alicdn.com/t/c/font_5123795_06mxe0ztuy73.ttf?t=1775808309000') format('truetype');
}

.icon-bujue {
  font-family: 'iconfont' !important;
  font-size: 16px;
  font-style: normal;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

```html
<i class="icon-bujue icon-a-chakanxi" 
   style="color: var(--fb-text-333)"></i>
```

> ⚠️ 离线/内网部署改为本地字体文件路径。

### 1.2 彩色图标（SVG）

11 个文件徽标作为独立 SVG 资产管理，存放在项目 `assets/icons/file-types/` 目录。**SVG 文件名已规范化**（重命名了原本带怪后缀的两个）：

| iconfont 类名 | SVG 文件名 | 说明 |
|--------------|----------|------|
| `.icon-pdf` | `pdf.svg` | |
| `.icon-word` | `word.svg` | |
| `.icon-xlsx` | `xlsx.svg` | |
| `.icon-ppt` | `ppt.svg` | |
| `.icon-dwg` | `dwg.svg` | |
| `.icon-rvt` | `rvt.svg` | |
| `.icon-max` | `max.svg` | |
| `.icon-skp-` | `sketchup.svg` | ✏️ SVG 文件已重命名 |
| `.icon-txt` | `txt.svg` | |
| `.icon-weizhi` | `weizhi.svg` | |
| `.icon-yasuobao-chunse1` | `archive.svg` | ✏️ SVG 文件已重命名 |

**React 用法**（推荐）：

```jsx
import IconPdf from "@/assets/icons/file-types/pdf.svg";
import IconArchive from "@/assets/icons/file-types/archive.svg";

<img src={IconPdf} width={32} height={32} alt="PDF" />
<img src={IconArchive} width={32} height={32} alt="Archive" />
```

**HTML 直接使用**：

```html
<img src="/assets/icons/file-types/pdf.svg" width="32" height="32" alt="PDF" />
```

> ❌ **禁止**对彩色 SVG 应用 `color` / `fill` / `filter` 等改色样式。

---

## 二、颜色控制规范

### 2.1 改色图标（🎨）

```html
<!-- 默认正文 -->
<i class="icon-bujue icon-a-chakanxi" 
   style="color: var(--fb-text-333)"></i>

<!-- 错误状态 -->
<i class="icon-bujue icon-a-shanchuxi" 
   style="color: var(--fb-error)"></i>

<!-- 双箭头向左 + 任意颜色 -->
<i class="icon-bujue icon-a-shuangjiantouxiangzuoxi-heise" 
   style="color: var(--fb-error)"></i>
```

> ❌ **禁止**硬编码 hex 值，必须使用 token

### 2.2 彩色图标（🌈）

```html
<img src="/assets/icons/file-types/pdf.svg" width="32" height="32" />
```

> ❌ 不要给彩色 SVG 改色（filter/mask/color 等任何方式）
> ❌ 不要把彩色 SVG 转字体后再用（iconfont 里 `.icon-pdf` 等扁平字体版禁止用）

### 2.3 颜色 Token 与 CSS 变量映射

| 场景 | CSS Token | 对应不觉色 |
|------|----------|---------|
| 默认正文图标 | `var(--fb-text-333)` | `白版/文字 #333` |
| 次级图标 | `var(--fb-text-666)` | `白版/文字 #666` |
| 弱化图标 | `var(--fb-text-999)` | `白版/文字 #999` |
| 禁用图标(浅底) | `var(--fb-disabled-ccc)` | `白版/禁用色 #ccc` |
| 错误/危险图标 | `var(--fb-error)` | `白版/错误色 #E60023` |
| 反白图标(深底) | `var(--fb-white)` | `白版/白色 #FFF` |
| 反白弱化(深底) | `var(--fb-fff-65)` | `黑板/文字 #FFF 65%` |
| 反白禁用(深底) | `var(--fb-fff-25)` | `黑板/禁用色 #FFF 25%` |

### 2.4 尺寸规范

| 场景 | 尺寸 | Token |
|------|------|-------|
| Web 按钮内（XS） | 12px | `token(btn.icon.size.xs)` |
| Web 按钮内（S~XXL） | 24px | `token(btn.icon.size.s/m/l/xl/xxl)` |
| App 导航栏 | `token(nav.icon.size.app)` | — |
| 输入框前后缀（Web） | 24px | — |
| 输入框前后缀（App） | 20px | — |
| Tag/Tab 内图标（Pad/手机） | 20px | — |
| 文件徽标（列表） | 24×24px | — |
| 文件徽标（卡片大图） | 48×48px 或 64×64px | — |

---

## 三、双箭头方向（4 个推荐）

| 方向 | 类名 |
|------|-----|
| ⬅️ 向左 | `.icon-a-shuangjiantouxiangzuoxi-heise` |
| ⬆️ 向上 | `.icon-a-shuangjiantouxiangshangxi-heise` |
| ⬇️ 向下 | `.icon-a-shuangjiantouxiangxiaxi-heise` |
| ➡️ 向右 | `.icon-a-shuangjiantouxixiangyou-hei` |

```html
<!-- 任意颜色用 CSS color 改色 -->
<i class="icon-bujue icon-a-shuangjiantouxiangzuoxi-heise" 
   style="color: var(--fb-text-333)"></i>

<i class="icon-bujue icon-a-shuangjiantouxiangzuoxi-heise" 
   style="color: var(--fb-error)"></i>
```

> 💡 **建议**：让设计师下次在 iconfont 里**新增 4 个无后缀的 base 版本**（如 `.icon-a-shuangjiantouxiangzuoxi`），届时类名会更干净。当前先用 `-heise/-hei` 作为事实基础版。

---

## 四、彩色图标专章 🌈（11 个）

### 4.1 完整清单

| 类名 | 文件类型 | SVG 文件 |
|------|---------|---------|
| `.icon-pdf` | PDF | `pdf.svg` |
| `.icon-word` | Word | `word.svg` |
| `.icon-xlsx` | Excel | `xlsx.svg` |
| `.icon-ppt` | PowerPoint | `ppt.svg` |
| `.icon-dwg` | AutoCAD | `dwg.svg` |
| `.icon-rvt` | Revit | `rvt.svg` |
| `.icon-max` | 3ds Max | `max.svg` |
| `.icon-skp-` | SketchUp | `sketchup.svg` |
| `.icon-txt` | 文本 | `txt.svg` |
| `.icon-weizhi` | 未知文件类型 | `weizhi.svg` |
| `.icon-yasuobao-chunse1` | 压缩包 | `archive.svg` |

> ⚠️ **iconfont 类名 vs SVG 文件名**：iconfont 项目里的类名是设计师配置的（暂不动），SVG 文件名我们已规范化。在代码中，**业务直接引用 SVG 文件名**（如 `import "./sketchup.svg"`），不会暴露 iconfont 那边的怪命名。

### 4.2 推荐使用场景

- **文件列表 / 文件管理界面**：每个文件项前置一个徽标
- **附件展示**：邮件、聊天、评论中附件预览
- **上传/下载状态**：上传进度卡片中显示文件类型
- **空状态插画**：当文件夹为空时，可叠加多个徽标示意支持的格式

### 4.3 用 React 组件做封装（推荐）

```jsx
// FileTypeIcon.jsx
import IconPdf from "@/assets/icons/file-types/pdf.svg";
import IconWord from "@/assets/icons/file-types/word.svg";
import IconXlsx from "@/assets/icons/file-types/xlsx.svg";
import IconPpt from "@/assets/icons/file-types/ppt.svg";
import IconDwg from "@/assets/icons/file-types/dwg.svg";
import IconRvt from "@/assets/icons/file-types/rvt.svg";
import IconMax from "@/assets/icons/file-types/max.svg";
import IconSketchup from "@/assets/icons/file-types/sketchup.svg";
import IconTxt from "@/assets/icons/file-types/txt.svg";
import IconArchive from "@/assets/icons/file-types/archive.svg";
import IconUnknown from "@/assets/icons/file-types/weizhi.svg";

const FILE_ICON_MAP = {
  pdf: IconPdf,
  doc: IconWord, docx: IconWord,
  xls: IconXlsx, xlsx: IconXlsx,
  ppt: IconPpt, pptx: IconPpt,
  dwg: IconDwg,
  rvt: IconRvt,
  max: IconMax, "3ds": IconMax,
  skp: IconSketchup,
  txt: IconTxt,
  zip: IconArchive, rar: IconArchive, "7z": IconArchive,
};

export const FileTypeIcon = ({ ext, size = 24 }) => {
  const Icon = FILE_ICON_MAP[ext.toLowerCase()] || IconUnknown;
  return <img src={Icon} width={size} height={size} alt={ext} />;
};
```

---

## 五、图标分类总览（200 个）


### 5.1 方向 / 箭头（20 个）（20 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-danjiantouxiangshangxi` | 单箭头（向上）（细） | 🎨 改色 |
| `.icon-a-danjiantouxiangxiaxi` | 单箭头（向下）（细） | 🎨 改色 |
| `.icon-a-danjiantouxiangyouxi` | 单箭头（向右）（细） | 🎨 改色 |
| `.icon-a-danjiantouxiangzuoxi` | 单箭头（向左）（细） | 🎨 改色 |
| `.icon-a-shuangjiantouxiangshangxi-heise` | 双箭头（向上）（细）-黑色 | 🎨 改色 |
| `.icon-a-shuangjiantouxiangxiaxi-heise` | 双箭头（向下）（细）-黑色 | 🎨 改色 |
| `.icon-a-shuangjiantouxiangzuoxi-heise` | 双箭头（向左）（细）-黑色 | 🎨 改色 |
| `.icon-a-shuangjiantouxixiangyou-hei` | 双箭头（细向右）-黑 | 🎨 改色 |
| `.icon-a-jiantoushitixiangshang` | 箭头实体（向上） | 🎨 改色 |
| `.icon-a-jiantoushitixiangxia` | 箭头实体（向下） | 🎨 改色 |
| `.icon-a-jiantoushitixiangyou` | 箭头实体（向右） | 🎨 改色 |
| `.icon-a-jiantoushitixiangzuo` | 箭头实体（向左） | 🎨 改色 |
| `.icon-a-jiantoushitizuhe-wushuzi` | 箭头实体（组合）-无数字 | 🎨 改色 |
| `.icon-a-jiantoushitizuhe-youshuzi` | 箭头实体（组合）-有数字 | 🎨 改色 |
| `.icon-a-jiantoushitizuhe-youshuziqiedaozuiduo` | 箭头实体（组合）-有数字且到最多 | 🎨 改色 |
| `.icon-a-jiantoushitizuhe-youshuziqiedaozuishao` | 箭头实体（组合）-有数字且到最少 | 🎨 改色 |
| `.icon-a-jiantouxiangshangxi` | 箭头（向上)（细） | 🎨 改色 |
| `.icon-a-jiantouxiangxiaxi` | 箭头（向下)（细） | 🎨 改色 |
| `.icon-a-jiantouxiangyouxi` | 箭头（向右)（细） | 🎨 改色 |
| `.icon-a-jiantouxiangzuoxi` | 箭头（向左)（细） | 🎨 改色 |

### 5.2 编辑 / 操作（13 个）（13 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-shangchuanrenwuxi` | 上传任务(细） | 🎨 改色 |
| `.icon-a-xiazaiAPPxi` | 下载APP（细） | 🎨 改色 |
| `.icon-a-xiazaifujian1xi` | 下载附件1(细) | 🎨 改色 |
| `.icon-a-baocunxi` | 保存（细） | 🎨 改色 |
| `.icon-a-jianxi` | 减(细) | 🎨 改色 |
| `.icon-a-shanchuxi` | 删除(细) | 🎨 改色 |
| `.icon-a-jiaxi` | 加(细) | 🎨 改色 |
| `.icon-a-fuzhixi` | 复制（细） | 🎨 改色 |
| `.icon-a-weituotianjiaxi` | 委托添加（细） | 🎨 改色 |
| `.icon-a-daochuxi` | 导出(细) | 🎨 改色 |
| `.icon-a-shoudongtianjiaxi` | 手动添加(细) | 🎨 改色 |
| `.icon-a-chexiaoxi` | 撤销（细） | 🎨 改色 |
| `.icon-a-bianjixi` | 编辑(细) | 🎨 改色 |

### 5.3 查看 / 搜索（6 个）（6 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-sousuoxi1` | 搜索(细) | 🎨 改色 |
| `.icon-a-sousuoxi` | 搜索(细) | 🎨 改色 |
| `.icon-a-chakanxi` | 查看(细) | 🎨 改色 |
| `.icon-a-shaixuanxi` | 筛选（细） | 🎨 改色 |
| `.icon-a-yincangxi` | 隐藏（细） | 🎨 改色 |
| `.icon-a-yanseshaixuanxi` | 颜色筛选（细） | 🎨 改色 |

### 5.4 社交 / 互动（5 个）（5 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-fenxiangxi` | 分享(细） | 🎨 改色 |
| `.icon-a-yishoucangxi-heise` | 已收藏（细）-黑色 | 🎨 改色 |
| `.icon-a-yidianzanxi-heise` | 已点赞（细）-黑色 | 🎨 改色 |
| `.icon-a-shoucangxi` | 收藏（细） | 🎨 改色 |
| `.icon-a-dianzanxi` | 点赞（细） | 🎨 改色 |

### 5.5 文件 / 媒体（28 个）（含 11 个 🌈 彩色，17 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-dwg` | dwg | 🌈 彩色（不可改色） |
| `.icon-max` | max | 🌈 彩色（不可改色） |
| `.icon-pdf` | pdf | 🌈 彩色（不可改色） |
| `.icon-ppt` | ppt | 🌈 彩色（不可改色） |
| `.icon-rvt` | rvt | 🌈 彩色（不可改色） |
| `.icon-skp-` | skp- | 🌈 彩色（不可改色） |
| `.icon-txt` | txt | 🌈 彩色（不可改色） |
| `.icon-word` | word | 🌈 彩色（不可改色） |
| `.icon-xlsx` | xlsx | 🌈 彩色（不可改色） |
| `.icon-a-shangchuantupianxi` | 上传图片（细） | 🎨 改色 |
| `.icon-a-shangchuanwenjianjiaxi` | 上传文件夹（细） | 🎨 改色 |
| `.icon-a-shangchuanwenjianxi` | 上传文件（细） | 🎨 改色 |
| `.icon-a-erweimaxi` | 二维码（细） | 🎨 改色 |
| `.icon-a-weizhixi` | 位置（细） | 🎨 改色 |
| `.icon-a-chuangjianwenjianjiaxi` | 创建文件夹（细） | 🎨 改色 |
| `.icon-yasuobao-chunse1` | 压缩包-纯色 | 🌈 彩色（不可改色） |
| `.icon-a-quxiaotupianquanpingxi` | 取消图片全屏（细） | 🎨 改色 |
| `.icon-a-tupianquanpingxi` | 图片全屏（细） | 🎨 改色 |
| `.icon-a-tupianxi` | 图片（细） | 🎨 改色 |
| `.icon-a-fuzhitupianxi` | 复制图片（细） | 🎨 改色 |
| `.icon-a-duotupianxi` | 多图片（细） | 🎨 改色 |
| `.icon-a-duowendangxi` | 多文档（细） | 🎨 改色 |
| `.icon-a-saomaxi` | 扫码（细） | 🎨 改色 |
| `.icon-a-wenjianjiaxi` | 文件夹（细） | 🎨 改色 |
| `.icon-a-tihuantupianxi` | 替换图片（细） | 🎨 改色 |
| `.icon-weizhi` | 未知 | 🌈 彩色（不可改色） |
| `.icon-a-bianjitupianxi` | 编辑图片（细） | 🎨 改色 |
| `.icon-a-zhongzhitupianxi` | 重置图片（细） | 🎨 改色 |

### 5.6 UI 控件 / 视图（16 个）（16 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-zhuyexi` | 主页（细） | 🎨 改色 |
| `.icon-a-quanpingmoshixi` | 全屏模式（细） | 🎨 改色 |
| `.icon-a-guanbixi` | 关闭(细) | 🎨 改色 |
| `.icon-a-diqiuxi` | 地球（细） | 🎨 改色 |
| `.icon-a-dagouxi` | 打钩(细) | 🎨 改色 |
| `.icon-a-gengduoxi` | 更多(细) | 🎨 改色 |
| `.icon-a-jinzhixi` | 禁止（细） | 🎨 改色 |
| `.icon-a-siyushezhixi` | 私域设置（细） | 🎨 改色 |
| `.icon-a-shugengduoxi` | 竖更多(细) | 🎨 改色 |
| `.icon-a-caidanxi` | 菜单（细） | 🎨 改色 |
| `.icon-a-shezhixi` | 设置（细） | 🎨 改色 |
| `.icon-a-gouwulanxi` | 购物篮（细） | 🎨 改色 |
| `.icon-a-jinruxi` | 进入（细） | 🎨 改色 |
| `.icon-a-tuichuquanpingxi` | 退出全屏（细） | 🎨 改色 |
| `.icon-a-tuichuxi` | 退出（细） | 🎨 改色 |
| `.icon-a-heibaibanqiehuanxi` | 黑白版切换（细） | 🎨 改色 |

### 5.7 业务 / 属性（16 个）（16 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-3Dmoxingxi` | 3D模型（细） | 🎨 改色 |
| `.icon-a-chanpincexi` | 产品册（细） | 🎨 改色 |
| `.icon-a-chanpinxi` | 产品（细） | 🎨 改色 |
| `.icon-a-jieshaoxian` | 介绍（线） | 🎨 改色 |
| `.icon-a-qiyejieshaoxi` | 企业介绍（细） | 🎨 改色 |
| `.icon-a-gonghuozhouqixi` | 供货周期（细） | 🎨 改色 |
| `.icon-a-pinpaixi` | 品牌（细） | 🎨 改色 |
| `.icon-a-beizhuxi` | 备注（细） | 🎨 改色 |
| `.icon-a-chicunguigexi` | 尺寸规格（细） | 🎨 改色 |
| `.icon-a-daishenhexi` | 待审核（细） | 🎨 改色 |
| `.icon-a-fuwufanweixi` | 服务范围（细） | 🎨 改色 |
| `.icon-a-fuwuxi` | 服务（细） | 🎨 改色 |
| `.icon-a-xiliexinghaoxi` | 系列型号（细） | 🎨 改色 |
| `.icon-a-sucaixi` | 素材（细） | 🎨 改色 |
| `.icon-a-sheweifengmianxi` | 设为封面（细） | 🎨 改色 |
| `.icon-a-zicaileixingxi` | 资材类型（细） | 🎨 改色 |

### 5.8 设计 / 编辑工具（12 个）（12 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-shangxiajingxiangxi` | 上下镜像（细） | 🎨 改色 |
| `.icon-a-daoyingxi` | 倒影（细） | 🎨 改色 |
| `.icon-a-liubianxingxi` | 六边形（细） | 🎨 改色 |
| `.icon-a-yuanxingxi` | 圆形（细） | 🎨 改色 |
| `.icon-a-zitijiacuxi` | 字体加粗（细） | 🎨 改色 |
| `.icon-a-zuoyoujingxiangxi` | 左右镜像（细） | 🎨 改色 |
| `.icon-a-koutuxi` | 抠图（细） | 🎨 改色 |
| `.icon-a-wenzixiahuaxian-quxianxi` | 文字下滑线-去线（细） | 🎨 改色 |
| `.icon-a-wenzixiahuaxianxi` | 文字下滑线（细） | 🎨 改色 |
| `.icon-a-wenziyanse-quxianxi` | 文字颜色-去线（细） | 🎨 改色 |
| `.icon-a-wenziyansexi` | 文字颜色（细） | 🎨 改色 |
| `.icon-a-xietixi` | 斜体（细） | 🎨 改色 |

### 5.9 面性图标（8 个）（8 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-renmian` | 人（面） | 🎨 改色 |
| `.icon-a-jieshaomian` | 介绍（面） | 🎨 改色 |
| `.icon-a-daoxumian` | 倒序（面） | 🎨 改色 |
| `.icon-a-pinpaimian` | 品牌（面） | 🎨 改色 |
| `.icon-a-tuodongmian` | 拖动（面） | 🎨 改色 |
| `.icon-a-weipaixumian` | 未排序（面） | 🎨 改色 |
| `.icon-a-zhengxumian` | 正序（面） | 🎨 改色 |
| `.icon-a-wenhaoxi-mian` | 问号（细）-面 | 🎨 改色 |

### 5.10 时间 / 日历（5 个）（5 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-rilixi` | 日历（细） | 🎨 改色 |
| `.icon-a-shijianxi` | 时间（细） | 🎨 改色 |
| `.icon-a-zhongzuoxi` | 重做（细） | 🎨 改色 |
| `.icon-a-zhongxinrenzhengxi` | 重新认证（细） | 🎨 改色 |
| `.icon-a-zhongzhixi` | 重置（细） | 🎨 改色 |

### 5.11 商务 / 交易（1 个）（1 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-jiagexi` | 价格（细） | 🎨 改色 |

### 5.12 用户 / 账号（1 个）（1 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-mingpianxi` | 名片（细） | 🎨 改色 |

### 5.13 其他（69 个）（69 个 🎨 改色）

| 类名 | 中文名 | 颜色规则 |
|------|-------|---------|
| `.icon-a-buxianshixi` | 不显示（细） | 🎨 改色 |
| `.icon-a-buquerenxi` | 不确认(细) | 🎨 改色 |
| `.icon-a-bujueyunxi` | 不觉云（细） | 🎨 改色 |
| `.icon-a-zuopinjixi` | 作品集（细） | 🎨 改色 |
| `.icon-a-guangxianchongzuxi` | 光线充足(细) | 🎨 改色 |
| `.icon-a-neirongzongshuxi` | 内容总数（细） | 🎨 改色 |
| `.icon-a-neirongguanlixi` | 内容管理（细） | 🎨 改色 |
| `.icon-a-fenlei1xi` | 分类1（细） | 🎨 改色 |
| `.icon-a-fenleixi` | 分类（细） | 🎨 改色 |
| `.icon-a-lieshuxi` | 列数（细） | 🎨 改色 |
| `.icon-a-jiazaixi` | 加载（细） | 🎨 改色 |
| `.icon-a-dantuqiehuanxi` | 单图切换（细） | 🎨 改色 |
| `.icon-a-quxiaolianjiexi` | 取消链接（细） | 🎨 改色 |
| `.icon-a-hezuoxi` | 合作（细） | 🎨 改色 |
| `.icon-a-hejifangshixi` | 合集方式（细） | 🎨 改色 |
| `.icon-a-tudingxi` | 图钉（细） | 🎨 改色 |
| `.icon-a-duoxuanxi` | 多选(细) | 🎨 改色 |
| `.icon-a-xiaochengxuxi` | 小程序（细） | 🎨 改色 |
| `.icon-a-zhankaixi` | 展开（细） | 🎨 改色 |
| `.icon-a-yishangjiaxi` | 已上架（细） | 🎨 改色 |
| `.icon-a-pingpumoshixi` | 平铺模式（细） | 🎨 改色 |
| `.icon-a-pingpuxi` | 平铺（细） | 🎨 改色 |
| `.icon-a-weixintianchong` | 微信（填充） | 🎨 改色 |
| `.icon-a-weixinxi` | 微信（细） | 🎨 改色 |
| `.icon-a-gantanhaoxi` | 感叹号（细） | 🎨 改色 |
| `.icon-a-chengyuanxi` | 成员（细） | 🎨 改色 |
| `.icon-a-shoujixiankuangxi` | 手机线框（细） | 🎨 改色 |
| `.icon-a-shoujixi` | 手机（细） | 🎨 改色 |
| `.icon-a-piliangrukuxi` | 批量入库（细） | 🎨 改色 |
| `.icon-a-piliangfenleixi` | 批量分类（细） | 🎨 改色 |
| `.icon-a-paixuxi` | 排序（细） | 🎨 改色 |
| `.icon-a-tishixi` | 提示（细） | 🎨 改色 |
| `.icon-a-bofangxi` | 播放（细） | 🎨 改色 |
| `.icon-a-xuanzhuanhuabuxi` | 旋转画布（细） | 🎨 改色 |
| `.icon-a-xianshixi` | 显示（细） | 🎨 改色 |
| `.icon-a-zantingxi` | 暂停（细） | 🎨 改色 |
| `.icon-a-gengxinxi` | 更新（细） | 🎨 改色 |
| `.icon-a-weishangjiaxi` | 未上架（细） | 🎨 改色 |
| `.icon-a-anlixi` | 案例（细） | 🎨 改色 |
| `.icon-a-tixingxi` | 梯形（细） | 🎨 改色 |
| `.icon-a-zhuxiaoshangjiaxi` | 注销商家（细） | 🎨 改色 |
| `.icon-a-pubuliuxi` | 瀑布流（细） | 🎨 改色 |
| `.icon-a-diannaoxi` | 电脑（细） | 🎨 改色 |
| `.icon-a-juxingxi` | 矩形（细） | 🎨 改色 |
| `.icon-a-querenxi` | 确认(细) | 🎨 改色 |
| `.icon-a-siyumingchengxi` | 私域名称（细） | 🎨 改色 |
| `.icon-a-tongjibiaoxi` | 统计表（细） | 🎨 改色 |
| `.icon-a-wangluoqiehuanxi` | 网络切换（细） | 🎨 改色 |
| `.icon-a-zhidingxi` | 置顶（细） | 🎨 改色 |
| `.icon-a-zhiweixi` | 职位（细） | 🎨 改色 |
| `.icon-a-lianzaiqujingkuangneixi` | 脸在取景框内(细) | 🎨 改色 |
| `.icon-a-lianzhengduipingmuxi` | 脸正对屏幕(细) | 🎨 改色 |
| `.icon-a-zidingyixi` | 自定义（细） | 🎨 改色 |
| `.icon-a-caijianxi` | 裁剪（细） | 🎨 改色 |
| `.icon-a-renzhengjiluxi` | 认证记录（细） | 🎨 改色 |
| `.icon-a-xunjiaxi` | 询价（细） | 🎨 改色 |
| `.icon-a-tietuxi` | 贴图（细） | 🎨 改色 |
| `.icon-a-zhuanhuan-xi` | 转换-(细) | 🎨 改色 |
| `.icon-a-zhezhaoxi` | 遮罩（细） | 🎨 改色 |
| `.icon-a-youxiangxi` | 邮箱（细） | 🎨 改色 |
| `.icon-a-suoAxi` | 锁A（细） | 🎨 改色 |
| `.icon-a-suoBxi` | 锁B（细） | 🎨 改色 |
| `.icon-a-suoCxi` | 锁C（细） | 🎨 改色 |
| `.icon-a-suoxi` | 锁（细） | 🎨 改色 |
| `.icon-a-changtuxi` | 长图（细） | 🎨 改色 |
| `.icon-a-wenhaoxi` | 问号（细） | 🎨 改色 |
| `.icon-a-yinyingxi` | 阴影（细） | 🎨 改色 |
| `.icon-a-fujianxi` | 附件（细） | 🎨 改色 |
| `.icon-a-yulanxi` | 预览（细） | 🎨 改色 |


---

## 六、高频图标速查表（中英映射）

### 6.1 高频操作

| 场景 | 图标类名 | 中文 |
|------|--------|------|
| 查看 | `.icon-a-chakanxi` | 查看（细） |
| 编辑 | `.icon-a-bianjixi` | 编辑（细） |
| 删除 | `.icon-a-shanchuxi` | 删除（细） |
| 添加 | `.icon-a-jiaxi` | 加（细） |
| 分享 | `.icon-a-fenxiangxi` | 分享（细） |
| 收藏 | `.icon-a-shoucangxi` | 收藏（细） |
| 已收藏 | `.icon-a-yishoucangxi-heise` | 已收藏（细）-黑色 |
| 点赞 | `.icon-a-dianzanxi` | 点赞（细） |
| 已点赞 | `.icon-a-yidianzanxi-heise` | 已点赞（细）-黑色 |
| 确认 | `.icon-a-querenxi` | 确认（细） |
| 取消 | `.icon-a-buquerenxi` | 不确认（细） |
| 多选 | `.icon-a-duoxuanxi` | 多选（细） |
| 排序 | `.icon-a-paixuxi` | 排序（细） |
| 退出 | `.icon-a-tuichuxi` | 退出（细） |
| 加载 | `.icon-a-jiazaixi` | 加载（细） |
| 提示 | `.icon-a-tishixi` | 提示（细） |
| 问号 | `.icon-a-wenhaoxi` | 问号（细） |
| 感叹号 | `.icon-a-gantanhaoxi` | 感叹号（细） |
| 暂停 | `.icon-a-zantingxi` | 暂停（细） |
| 播放 | `.icon-a-bofangxi` | 播放（细） |
| 全屏 | `.icon-a-quanpingmoshixi` | 全屏模式（细） |
| 退出全屏 | `.icon-a-tuichuquanpingxi` | 退出全屏（细） |
| 主页 | `.icon-a-zhuyexi` | 主页（细） |

### 6.2 双箭头方向（4 个）

| 方向 | 类名 |
|------|-----|
| ⬅️ 向左 | `.icon-a-shuangjiantouxiangzuoxi-heise` |
| ⬆️ 向上 | `.icon-a-shuangjiantouxiangshangxi-heise` |
| ⬇️ 向下 | `.icon-a-shuangjiantouxiangxiaxi-heise` |
| ➡️ 向右 | `.icon-a-shuangjiantouxixiangyou-hei` |

### 6.3 文件类型徽标 🌈

> 见第四章详细规范，业务里使用 SVG 资产。

| 类名 | SVG 文件 | 文件类型 |
|------|---------|---------|
| `.icon-pdf` | `pdf.svg` | PDF |
| `.icon-word` | `word.svg` | Word |
| `.icon-xlsx` | `xlsx.svg` | Excel |
| `.icon-ppt` | `ppt.svg` | PowerPoint |
| `.icon-dwg` | `dwg.svg` | AutoCAD |
| `.icon-rvt` | `rvt.svg` | Revit |
| `.icon-max` | `max.svg` | 3ds Max |
| `.icon-skp-` | `sketchup.svg` | SketchUp |
| `.icon-txt` | `txt.svg` | 文本 |
| `.icon-yasuobao-chunse1` | `archive.svg` | 压缩包 |
| `.icon-weizhi` | `weizhi.svg` | 未知 |

### 6.4 面性图标（solid 风格）

| 类名 | 中文 | 配套线性版本（如有） |
|------|------|------------------|
| `.icon-a-jieshaomian` | 介绍（面） | — |
| `.icon-a-pinpaimian` | 品牌（面） | `.icon-a-pinpaixi` |
| `.icon-a-wenhaoxi-mian` | 问号（面） | `.icon-a-wenhaoxi` |
| `.icon-a-weipaixumian` | 未排序（面） | `.icon-a-paixuxi`（排序） |
| `.icon-a-zhengxumian` | 正序（面） | — |
| `.icon-a-daoxumian` | 倒序（面） | — |
| `.icon-a-renmian` | 人（面） | — |
| `.icon-a-tuodongmian` | 拖动（面） | — |

> 「-面」是 solid（实心）风格，对应"-细"是 line（线性）风格。两者不存在哪个更"基础"，按 UX 场景选用。

---

## 七、规范要求（强制）

1. **不得猜图标名**：所有图标使用前必须在本文档中查到，找不到则与设计师确认
2. **🎨 改色图标**：颜色必须用 CSS `color` token 控制，禁止使用 hex 字面量
3. **🌈 彩色图标**：必须使用 SVG 资产，**禁止改色**（包括 filter / mask / color 等任何方式）
4. **🌈 彩色图标禁止用字体版**：iconfont 字体里虽然存在 `.icon-pdf` 等扁平版本，但本规范要求业务用 SVG 资产
5. **图标尺寸统一用规范 token**：详见第 2.4 节
6. **改色图标必须搭配 `.icon-bujue` 基础类**：单独使用 `.icon-xxx` 不会渲染
7. **命名遗留问题（建议下次让设计师清理 iconfont 项目）**：
   - `.icon-skp-` → 建议重命名为 `.icon-sketchup`
   - `.icon-yasuobao-chunse1` → 建议重命名为 `.icon-archive`
   - 双箭头当前用 `-heise/-hei` 后缀 → 建议新增无后缀 base 版本
   - 28 个旧的双箭头多色变体 → 建议从 iconfont 项目中删除

---

## 附录：图标可视化预览

完整 200 个图标的视觉预览见同目录 `iconfont-preview.html`。预览页中：
- 🎨 改色图标：随顶部"颜色 swatch"切换实时预览
- 🌈 彩色图标：以原始 SVG 渲染，颜色不会变化
