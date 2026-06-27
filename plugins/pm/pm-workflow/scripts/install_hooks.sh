#!/usr/bin/env bash
# pm-workflow git hook 安装脚本
#
# 用法：bash pm-workflow/scripts/install_hooks.sh
#
# 作用：把 pm-workflow/scripts/hooks/* 软链到 .git/hooks/，让 git 在 commit 时自动调用
#
# SSOT 真源：`pm-workflow/rules/agent_dispatch_protocol.md`「PM / Supervisor Agent 文件改动权限边界」第 5 条

set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
SRC_DIR="$REPO_ROOT/pm-workflow/scripts/hooks"
DST_DIR="$REPO_ROOT/.git/hooks"

if [ ! -d "$SRC_DIR" ]; then
    echo "✗ 找不到 hook 源目录：$SRC_DIR"
    exit 1
fi

if [ ! -d "$DST_DIR" ]; then
    echo "✗ 找不到 .git/hooks 目录（当前不在 git 仓库中？）：$DST_DIR"
    exit 1
fi

installed=0
for hook_path in "$SRC_DIR"/*; do
    if [ ! -f "$hook_path" ]; then continue; fi
    hook_name=$(basename "$hook_path")
    chmod +x "$hook_path"

    target="$DST_DIR/$hook_name"
    if [ -L "$target" ] || [ -f "$target" ]; then
        rm -f "$target"
    fi
    ln -s "$hook_path" "$target"
    echo "✓ 安装 $hook_name → $target"
    installed=$((installed + 1))
done

echo ""
echo "完成：共安装 $installed 个 hook。"
echo ""
echo "测试：在工作目录改动 outputs/ + pm-workflow/scripts/ 各一个文件后 git commit，应被拒绝。"
echo "绕过（仅 L2-only 独立 commit 用）：git commit --no-verify"
