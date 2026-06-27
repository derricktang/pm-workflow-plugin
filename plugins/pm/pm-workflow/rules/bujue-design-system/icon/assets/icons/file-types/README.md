# 文件类型徽标 SVG（assets/icons/file-types/）

> 11 个文件类型彩色徽标，作为独立 SVG 资产管理。
> 详细使用规范见根目录 `icon-discovery.md` § 四。

---

## 一、文件清单

| SVG 文件 | 文件类型 |
|---------|---------|
| `pdf.svg` | PDF |
| `word.svg` | Word |
| `xlsx.svg` | Excel |
| `ppt.svg` | PowerPoint |
| `dwg.svg` | AutoCAD |
| `rvt.svg` | Revit |
| `max.svg` | 3ds Max |
| `sketchup.svg` | SketchUp |
| `txt.svg` | 文本 |
| `archive.svg` | 压缩包 |
| `weizhi.svg` | 未知文件类型 |

---

## 二、使用方式

### React（推荐）

```jsx
// FileTypeIcon.jsx
import IconPdf from '@/assets/icons/file-types/pdf.svg';
import IconWord from '@/assets/icons/file-types/word.svg';
import IconXlsx from '@/assets/icons/file-types/xlsx.svg';
import IconPpt from '@/assets/icons/file-types/ppt.svg';
import IconDwg from '@/assets/icons/file-types/dwg.svg';
import IconRvt from '@/assets/icons/file-types/rvt.svg';
import IconMax from '@/assets/icons/file-types/max.svg';
import IconSketchup from '@/assets/icons/file-types/sketchup.svg';
import IconTxt from '@/assets/icons/file-types/txt.svg';
import IconArchive from '@/assets/icons/file-types/archive.svg';
import IconUnknown from '@/assets/icons/file-types/weizhi.svg';

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

### HTML 直接使用

```html
<img src="/assets/icons/file-types/pdf.svg" width="32" height="32" alt="PDF" />
```

---

## 三、强制规则

- ❌ **禁止改色**：不要对这 11 个 SVG 应用 `color` / `fill` / `filter` 等改色样式
- ❌ **禁止用字体版**：iconfont 字体里虽然存在 `.icon-pdf` 等扁平版本，但本规范要求用 SVG 资产
- ✅ **推荐尺寸**：列表 `24×24`，卡片大图 `48×48` 或 `64×64`

---

## 四、推荐使用场景

- 文件列表 / 文件管理界面：每个文件项前置一个徽标
- 附件展示：邮件、聊天、评论中的附件预览
- 上传 / 下载状态：上传进度卡片中显示文件类型
- 空状态插画：当文件夹为空时叠加多个徽标示意支持的格式
