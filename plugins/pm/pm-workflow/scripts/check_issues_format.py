#!/usr/bin/env python3
"""
check_issues_format.py — SSOT #19 issues/ 调整意见文件格式校验

用法：
    python pm-workflow/scripts/check_issues_format.py

作用：
    SSOT 双锚 #19「issues/ 调整意见记录格式」5 要素第 5 项「机械兜底」实现。
    扫 process_record/issues/ 目录所有 .md 文件,校验格式合法。

    历史教训：缺"状态：未分析"会致 /retro 第 5b 步崩溃（因找不到状态字段
    无法转移到 _analyzed 后缀）。本 check 提前在文件创建/修改时拦截。

校验维度：
    1. 文件名格式：YYYY-MM-DD_HHMM[_analyzed].md（CLAUDE.md「调整意见自动记录规则」）
    2. 文件头：`# 调整意见 — YYYY-MM-DD HH:MM`
    3. 状态字段：`状态：未分析` 或 `状态：已分析`（与文件名 _analyzed 后缀一致）
    4. 表格表头：`| # | 完整描述 | 影响成果文件 | 业务 | 功能逻辑 |` 5 列
    5. 至少 1 行数据（# 列从 1 开始）

退出码：
    0  — issues/ 目录不存在 / 全部文件格式合法
    1  — 任一文件格式非法
"""

import re
import sys
from pathlib import Path

import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_paths import FRAMEWORK_ROOT, PROJECT_ROOT
ISSUES_DIR = PROJECT_ROOT / "process_record" / "issues"


# ── 校验规则 ──────────────────────────────────────────────────────────────────

# 文件名格式：YYYY-MM-DD_HHMM.md / YYYY-MM-DD_HHMM_analyzed.md
FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})_(\d{4})(_analyzed)?\.md$")

# 文件头：# 调整意见 — YYYY-MM-DD HH:MM
HEADER_RE = re.compile(r"^#\s+调整意见\s+[—-]\s+(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})\s*$", re.MULTILINE)

# 状态字段
STATUS_RE = re.compile(r"^状态[:：]\s*(未分析|已分析)\s*$", re.MULTILINE)

# 表格表头（前 3 列严格,业务/功能逻辑可有)
EXPECTED_HEADERS = ["#", "完整描述", "影响成果文件"]


def validate_one(path: Path) -> list[str]:
    """校验一个 issue 文件,返回错误清单（空列表表示合法）。"""
    errors: list[str] = []

    # 1. 文件名格式
    fn_m = FILENAME_RE.match(path.name)
    if not fn_m:
        errors.append(f"文件名格式非法（应 YYYY-MM-DD_HHMM[_analyzed].md）：{path.name}")
        return errors  # 文件名错则不再深入检测

    is_analyzed_filename = fn_m.group(5) is not None

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        errors.append(f"文件读取失败：{e}")
        return errors

    # 2. 文件头
    if not HEADER_RE.search(text):
        errors.append(
            "缺文件头 `# 调整意见 — YYYY-MM-DD HH:MM`（首行）"
        )

    # 3. 状态字段
    status_m = STATUS_RE.search(text)
    if not status_m:
        errors.append("缺 `状态：未分析` 或 `状态：已分析` 字段")
    else:
        status_val = status_m.group(1)
        # 状态字段与文件名 _analyzed 后缀一致性核查
        if is_analyzed_filename and status_val != "已分析":
            errors.append(
                f"文件名含 _analyzed 但状态字段为 `{status_val}`,应为 `已分析`"
            )
        elif not is_analyzed_filename and status_val != "未分析":
            errors.append(
                f"文件名不含 _analyzed 但状态字段为 `{status_val}`,应为 `未分析`"
            )

    # 4. 表格表头（含 #/完整描述/影响成果文件 三必备列）
    table_header_re = re.compile(
        r"^\|(.+?)\|\s*$\n\|[\s\-:|]+\|", re.MULTILINE
    )
    headers = []
    for h_m in table_header_re.finditer(text):
        cols = [c.strip() for c in h_m.group(1).split("|")]
        headers.append(cols)
    if not headers:
        errors.append("缺调整意见表（`| # | 完整描述 | 影响成果文件 | ... |` 5 列）")
    else:
        first = headers[0]
        for required in EXPECTED_HEADERS:
            if required not in first:
                errors.append(
                    f"表格表头缺必备列 `{required}`,实际表头：{first}"
                )

    # 5. 至少 1 行数据（在表格中）
    if headers:
        # 简易：扫描含 `^| 1 |` 的行
        if not re.search(r"^\|\s*\d+\s*\|", text, re.MULTILINE):
            errors.append("表格无任何数据行（应至少 1 条调整意见）")

    return errors


# ── 主入口 ────────────────────────────────────────────────────────────────────


def main() -> None:
    print("check_issues_format.py — SSOT #19 issues/ 调整意见文件格式校验")

    if not ISSUES_DIR.exists():
        print(f"[SKIP] issues/ 目录不存在（无调整意见档案）：{ISSUES_DIR}")
        sys.exit(0)

    files = sorted(ISSUES_DIR.glob("*.md"))
    if not files:
        print(f"[OK] issues/ 目录为空（无文件需核查）")
        sys.exit(0)

    print(f"  目录：{ISSUES_DIR}")
    print(f"  文件数：{len(files)}")
    print()

    bad: list[tuple[Path, list[str]]] = []
    for f in files:
        errors = validate_one(f)
        if errors:
            bad.append((f, errors))

    if not bad:
        print(f"[PASS] {len(files)} 个 issue 文件格式全部合法")
        sys.exit(0)

    print(f"[FAIL] {len(bad)} 个文件格式非法：")
    for f, errors in bad:
        print(f"  {f.name}:")
        for e in errors:
            print(f"    - {e}")
    print()
    print("修复方向：参 CLAUDE.md「调整意见自动记录规则」第一步格式规范")
    sys.exit(1)


if __name__ == "__main__":
    main()
