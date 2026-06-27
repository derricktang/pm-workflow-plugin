#!/usr/bin/env python3
"""check_uncommitted_l1.py — 变更循环闭环前必提交 机械兜底（SSOT #79 推论）

**开始新变更循环（调整意见 / CR / nextStage）前**运行：扫工作区是否有未提交的 L1
交付物改动（`outputs/`）。有 → WARN「上个变更循环可能未提交，先 commit（带 issue/CR/SNB
编号）再开始下一个，否则 `git diff` 把多变更混团、`git log -- outputs/` 无法精确归属」。

为何只扫 `outputs/`：变更追踪关心的是**交付物**（spec/prd/阶段产物）的 diff；
`process_record/` 多为过程记录（常 gitignore，且非下游可见交付物），不在追踪 diff 范围。

强度 [Should] WARN —— **退出码恒 0，不阻断**（不阻塞合理的同循环批处理 / 首次循环 /
无 git 环境）。真源规则：CLAUDE.md §「文件命名规范」git-diff 原则旁「变更循环闭环前必提交」
推论 + §「调整意见自动记录规则」第四步 step 5。

用法：python3 pm-workflow/scripts/check_uncommitted_l1.py [repo_root]
（repo_root 缺省 = 当前目录；编排器在三入口流程开始时调用）
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SAMPLE_N = 10


def scan_uncommitted_outputs(repo: Path) -> list[str]:
    """返回 outputs/ 下未提交（含 untracked）改动的 porcelain 行；git 不可用返回 []。"""
    try:
        proc = subprocess.run(
            ["git", "-c", "core.quotepath=false", "-C", str(repo),
             "status", "--porcelain", "--", "outputs/"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return []
    if proc.returncode != 0:  # 非 git 仓 / outputs 不存在等 → 静默跳过
        return []
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv
    repo = Path(args[1]).resolve() if len(args) > 1 else Path.cwd()

    lines = scan_uncommitted_outputs(repo)
    if not lines:
        print("[OK] outputs/ 无未提交改动 — 可安全开始新变更循环")
        return 0

    print(f"[WARN] outputs/ 有 {len(lines)} 处未提交改动（上个变更循环可能未提交）：",
          file=sys.stderr)
    for ln in lines[:SAMPLE_N]:
        print(f"    {ln}", file=sys.stderr)
    if len(lines) > SAMPLE_N:
        print(f"    …共 {len(lines)} 处", file=sys.stderr)
    print(
        "  → 开始新调整意见 / CR / nextStage 前，先 commit 本批 outputs/"
        "（commit message 带 issue / CR / SNB 编号），否则 `git diff` 把多变更混成一团、"
        "`git log -- outputs/` 无法精确归属（SSOT #79「变更循环闭环前必提交」推论）。",
        file=sys.stderr,
    )
    print("  （[Should] WARN，不阻断——同循环批处理 / 首次循环可忽略）", file=sys.stderr)
    return 0  # 恒 0：WARN 不 FAIL


if __name__ == "__main__":
    raise SystemExit(main())
