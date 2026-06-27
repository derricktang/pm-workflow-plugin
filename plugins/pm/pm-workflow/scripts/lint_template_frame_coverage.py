#!/usr/bin/env python3
"""
lint_template_frame_coverage.py — L2 模板多端 frame CSS 覆盖度机械检查

模块定位:
    建议 8 落地(/retro issue # 11 / # 16 复盘根因 H):
    扫 `pm-workflow/rules/prd_template.html` 中所有 `.X-frame { ... }` CSS 定义,
    与多端枚举(`pm-workflow/rules/proto_platform_*.md`)对比,识别:
    - 缺失的端类 frame CSS(如 .tablet-frame / .miniprogram-frame 未定义)
    - 已定义但缺关键属性(`position: relative` / `width` / `min-height` / `overflow` / `flex-shrink`)
    任一不合规触发 ERROR;全部合规时退出码 0。

SSOT 真源:
    pm-workflow/rules/prd_expression_standard.md §零.2 支柱 1.b(2026-05-12 NB-WE-25)
    pm-workflow/rules/prd_template.html `.phone-frame` / `.desktop-frame` / `.h5-frame` 真源

触发时机:
    1. L2 sync 后:`pm-workflow/rules/workflow_maintenance_protocol.md` 维护清单要求每次
       L2 sync 触及 prd_template.html / proto_platform_*.md 时跑一遍
    2. workflow-evolution skill Step 7 SSOT 同步检查时
    3. 任何 modal 漂移类 bug 复盘后

依赖:
    仅 stdlib(re, pathlib)

用法:
    python3 pm-workflow/scripts/lint_template_frame_coverage.py
    退出码 0 = PASS,1 = FAIL
"""

import re
import sys
from pathlib import Path


import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_paths import FRAMEWORK_ROOT, PROJECT_ROOT
TEMPLATE_PATH = FRAMEWORK_ROOT / "pm-workflow" / "rules" / "prd_template.html"
PLATFORM_DIR = FRAMEWORK_ROOT / "pm-workflow" / "rules"

# 多端枚举 — 应有 frame CSS 的端类清单
EXPECTED_FRAMES = {
    "phone-frame": "pm-workflow/rules/proto_platform_app.md (手机端)",
    "desktop-frame": "pm-workflow/rules/proto_platform_desktop.md (桌面端)",
    "h5-frame": "pm-workflow/rules/proto_platform_h5.md (H5 移动 Web)",
    "tablet-frame": "pm-workflow/rules/proto_platform_app.md (PAD 端)",
    "miniprogram-frame": "pm-workflow/rules/proto_platform_miniprogram.md (微信小程序)",
}

# 每个 frame 必含的关键属性
REQUIRED_ATTRS = [
    ("position", "relative"),
    ("width", None),  # 任意值
    ("min-height", None),
    ("overflow", None),  # hidden / visible / clip 等
    ("flex-shrink", None),
]


def extract_frame_css_blocks(template_content: str) -> dict[str, str]:
    """从 prd_template.html 抽取所有 `.X-frame { ... }` 块。

    返回 {frame_name: body_string} dict,其中 frame_name 是不含点号的类名,
    body_string 是花括号内的属性文本(供后续 grep 关键属性)。
    """
    frames: dict[str, str] = {}
    for m in re.finditer(
        r"\.([\w-]+-frame)\s*\{([^}]*)\}", template_content
    ):
        frames[m.group(1)] = m.group(2)
    return frames


def check_frame_attrs(frame_name: str, body: str, errors: list[str]) -> None:
    """检查单个 frame CSS body 是否含全部必要属性,缺则追加 error。"""
    for attr, expected_val in REQUIRED_ATTRS:
        # 简单 grep,容忍空白
        pattern = rf"\b{re.escape(attr)}\s*:\s*([^;]+);"
        m = re.search(pattern, body)
        if not m:
            errors.append(
                f"  ❌ .{frame_name} 缺属性 `{attr}` — "
                f"参 §零.2 支柱 1.b / §零.3 父容器契约"
            )
            continue
        actual_val = m.group(1).strip()
        if expected_val and expected_val not in actual_val:
            errors.append(
                f"  ❌ .{frame_name} 属性 `{attr}: {actual_val}` — "
                f"期望含 `{expected_val}`(如 `{attr}: {expected_val}`);"
                f"否则 .fb-modal-overlay 等 absolute 子元素冒泡到 viewport"
            )


def main() -> int:
    if not TEMPLATE_PATH.exists():
        print(f"[ERROR] prd_template.html 不存在:{TEMPLATE_PATH}", file=sys.stderr)
        return 1

    template_content = TEMPLATE_PATH.read_text(encoding="utf-8")
    frames = extract_frame_css_blocks(template_content)

    print(f"扫描:{TEMPLATE_PATH.relative_to(FRAMEWORK_ROOT)}")
    print(f"已发现 frame CSS 定义:{len(frames)} 个 — {sorted(frames.keys())}")

    errors: list[str] = []

    # 1. 必有 frame 端类覆盖度
    for expected_name, source_doc in EXPECTED_FRAMES.items():
        if expected_name not in frames:
            errors.append(
                f"❌ 缺失 `.{expected_name}` CSS 定义 — "
                f"该端类在 {source_doc} 中声明,但 prd_template.html 无对应 frame 规则;"
                f"产品若使用该端任何 modal 都会漂移到 viewport"
            )

    # 2. 已存在 frame 的关键属性合规性
    for frame_name, body in frames.items():
        if frame_name not in EXPECTED_FRAMES:
            # 自定义 frame(非多端清单内),仅警告"未在标准清单"
            print(f"  ⚠ 非多端枚举 frame: `.{frame_name}`(自定义,不强校验)")
            continue
        check_frame_attrs(frame_name, body, errors)

    if errors:
        print("\n=== ERROR(L2 模板多端 frame CSS 覆盖度不合规) ===", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        print(
            "\n修复建议:在 pm-workflow/rules/prd_template.html 补齐缺失 frame 块,"
            "参 .phone-frame / .desktop-frame / .h5-frame 已有写法。",
            file=sys.stderr,
        )
        return 1

    print("\n✅ PASS — 多端 frame CSS 覆盖度合规,所有 frame 含 5 个关键属性")
    return 0


if __name__ == "__main__":
    sys.exit(main())
