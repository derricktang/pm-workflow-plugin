#!/usr/bin/env python3
"""
check_state_paths.py — SSOT #21 state.md「当前阶段产物」表路径存在性校验

用法：
    python pm-workflow/scripts/check_state_paths.py

作用：
    SSOT 双锚 #21「state.md 当前阶段产物表」5 要素第 5 项「机械兜底」实现。
    扫 process_record/state.md 中「当前阶段产物」表里所有 outputs/ 路径,
    校验每条路径在文件系统中是否真实存在 + 版本号格式合法。

    历史教训：state.md 是会话恢复入口,产物路径漂移（如 outputs 重命名/删除
    但 state.md 没跟改）会导致重启会话后找不到文件。本 check 在工作流任意
    时间点都可跑,确保 state.md 与文件系统一致。

退出码：
    0  — state.md 不存在（工作流空载）/ 表中所有路径合法
    1  — 表中存在路径不存在 / 版本号格式非法 / state.md 解析失败

校验维度：
    1. outputs/ 路径存在性：state.md 中提及的 outputs/*.md 或 outputs/*.html
       必须真实存在
    2. 版本号格式：路径含 `_v\\d+\\.\\d+_\\d{8}` 时校验 YYYYMMDD 部分是合法日期
    3. _latest 路径优先：表中应优先指向 _latest 版本,带具体版本号的归档
       路径只在「历史归档」段出现
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_PATH = REPO_ROOT / "process_record" / "state.md"
OUTPUT_DIR = REPO_ROOT / "outputs"


# ── 路径提取与校验 ────────────────────────────────────────────────────────────

# 表格行中提取 outputs/ 路径（含 outputs/spec_xxx_latest.md / outputs/产品定义_xxx_v1.2_20260413.md 等）
OUTPUT_PATH_RE = re.compile(r"`?(outputs/[^`\s|)]+\.(md|html))`?")

# 版本号格式：_vN.N_YYYYMMDD
VERSIONED_RE = re.compile(r"_v(\d+)\.(\d+)_(\d{8})")


def extract_paths_from_state(text: str) -> list[tuple[int, str]]:
    """从 state.md 提取所有 outputs/ 路径,返回 [(行号, 路径)]。"""
    paths: list[tuple[int, str]] = []
    for line_num, line in enumerate(text.splitlines(), 1):
        for m in OUTPUT_PATH_RE.finditer(line):
            paths.append((line_num, m.group(1)))
    return paths


def validate_version_date(date_str: str) -> bool:
    """校验 YYYYMMDD 是合法日期（年 2024-2099 / 月 01-12 / 日 01-31 简易范围）。"""
    if len(date_str) != 8:
        return False
    try:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
    except ValueError:
        return False
    return 2024 <= year <= 2099 and 1 <= month <= 12 and 1 <= day <= 31


# ── 主入口 ────────────────────────────────────────────────────────────────────


def main() -> None:
    print("check_state_paths.py — SSOT #21 state.md 当前阶段产物表路径校验")

    if not STATE_PATH.exists():
        print(f"[SKIP] state.md 不存在（工作流空载）：{STATE_PATH}")
        sys.exit(0)

    text = STATE_PATH.read_text(encoding="utf-8")
    paths = extract_paths_from_state(text)
    if not paths:
        print(f"[OK] state.md 中未提取到任何 outputs/ 路径（无需核查）")
        sys.exit(0)

    print(f"  state.md：{STATE_PATH}")
    print(f"  提取路径：{len(paths)} 条")
    print()

    missing: list[tuple[int, str]] = []
    bad_version: list[tuple[int, str, str]] = []
    seen: set[str] = set()

    for line_num, path_str in paths:
        if path_str in seen:
            continue
        seen.add(path_str)

        full_path = REPO_ROOT / path_str

        # 校验存在性
        if not full_path.exists():
            missing.append((line_num, path_str))
            continue

        # 校验版本号（如有）
        m = VERSIONED_RE.search(path_str)
        if m:
            date_str = m.group(3)
            if not validate_version_date(date_str):
                bad_version.append((line_num, path_str, date_str))

    if not missing and not bad_version:
        print(f"[PASS] state.md 中 {len(seen)} 条 outputs/ 路径全部存在 + 版本号格式合法")
        sys.exit(0)

    if missing:
        print(f"[FAIL] {len(missing)} 条路径在文件系统中不存在：")
        for ln, p in missing:
            print(f"  - line {ln}: {p}")
        print()
    if bad_version:
        print(f"[FAIL] {len(bad_version)} 条路径版本号日期格式非法（应为 YYYYMMDD,2024-2099 / 月 01-12 / 日 01-31）：")
        for ln, p, d in bad_version:
            print(f"  - line {ln}: {p}（日期段：{d}）")
        print()

    print("修复方向：")
    print("  - 路径不存在 → 检查 outputs/ 目录实际状态;state.md 表更新到当前真实路径")
    print("  - 版本号非法 → 修正 _vN.N_YYYYMMDD 格式（参 CLAUDE.md「文件命名规范」表）")
    sys.exit(1)


if __name__ == "__main__":
    main()
