#!/usr/bin/env python3
"""SessionStart hook — 注入 process_record/state.md 摘要到新会话上下文。

目标：会话启动时自动给 Claude Code 注入当前工作流状态（当前阶段 / 当前阶段开放问题 /
产物路径），省去人工 cat state.md 步骤。借鉴 superpowers 插件 SessionStart
机制（issue 2026-05-10_0442 项 1）。

注：B1 拆分后已决策条目在 process_record/decisions_ledger.md（SSOT #18 真源），
本 hook 仅摘要 state.md（活动态）；恢复指引提示同时 Read ledger。

协议：Claude Code SessionStart hook stdout 输出 JSON,含
    {"hookSpecificOutput": {"hookEventName": "SessionStart",
                             "additionalContext": "..."}}

容错：state.md 不存在 → 输出空 context（exit 0,不阻断会话启动）。

注册：通过 .claude/settings.json hooks.SessionStart 配置:
    {"type": "command", "command": "python pm-workflow/scripts/hooks/session_start_state_summary.py"}
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# 优先用 Claude Code 注入的 CLAUDE_PROJECT_DIR,fallback cwd（用户启动 Claude Code 的目录）
# 不用 __file__ 相对路径,因为脚本可能被多个项目软链复用,需指向"当前会话项目"而非"脚本所在仓库"
REPO_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
STATE_PATH = REPO_ROOT / "process_record" / "state.md"


def _emit_context(context: str) -> None:
    """统一输出 SessionStart 协议 JSON 并退出。"""
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(0)


def _extract_field(text: str, label: str) -> str:
    """从 `当前阶段：4` 这类行提取值。"""
    m = re.search(rf"^{re.escape(label)}\s*[：:]\s*(.+?)$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _extract_section_table(text: str, section_title: str) -> list[list[str]]:
    """提取 `## {section_title}` 下的 markdown 表格,返回 list of rows(每行 cell list)。"""
    # 标题行容忍尾随说明文字（如 "## 阻塞性问题清单（仅 ⏳ 开放项）"）——只要求标题前缀匹配
    pat = re.compile(
        rf"^##\s*{re.escape(section_title)}[^\n]*$(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pat.search(text)
    if not m:
        return []
    block = m.group(1)
    rows: list[list[str]] = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        if re.match(r"^\|[\s\-|]+\|$", line):
            continue  # 分隔行
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows[1:] if rows else []  # 去掉表头


def _count_status_pending(rows: list[list[str]], status_col_idx: int) -> int:
    """统计指定列含 ⏳/未决 关键字的行数。"""
    if not rows:
        return 0
    count = 0
    for row in rows:
        if status_col_idx >= len(row):
            continue
        status = row[status_col_idx]
        if "⏳" in status or "待" in status or "进行" in status:
            count += 1
    return count


def _recent_commit() -> str:
    """读最近 1 条 git commit 摘要,失败返空。"""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "log", "-1", "--pretty=%h %s"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return out.decode("utf-8", errors="replace").strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def main() -> None:
    if not STATE_PATH.exists():
        _emit_context("")  # state.md 不存在 → 静默,不打扰

    try:
        text = STATE_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        _emit_context("")

    # 提取关键字段
    product = _extract_field(text, "产品名称") or "(未命名)"
    stage = _extract_field(text, "当前阶段") or "?"
    status = _extract_field(text, "当前状态") or "?"

    blocking_rows = _extract_section_table(text, "阻塞性问题清单")
    nonblocking_rows = _extract_section_table(text, "非阻塞性问题清单")
    products_rows = _extract_section_table(text, "当前阶段产物")

    # B1 拆分后 state.md 两表均为「开放-only」5 列:编号/阶段/来源/问题描述/状态(idx 4),
    # 行内状态恒为 ⏳(已解答/已决策条目已移入 decisions_ledger.md),故计数 ≈ 开放问题数。
    blocking_pending = _count_status_pending(blocking_rows, 4)
    nonblocking_pending = _count_status_pending(nonblocking_rows, 4)

    # 产物路径速记（最新 3 条）
    products_summary = []
    for row in products_rows[:6]:
        if len(row) >= 3:
            products_summary.append(f"  - {row[0]}: {row[1]} ({row[2]})")
    products_text = "\n".join(products_summary) if products_summary else "  (无)"

    commit = _recent_commit()
    commit_line = f"\n最近 commit: {commit}" if commit else ""

    # 拼装摘要
    context = (
        f"## 工作流状态摘要（自 process_record/state.md 自动注入）\n\n"
        f"- 产品：{product}\n"
        f"- 当前阶段：{stage}（{status}）\n"
        f"- 阻塞性问题（当前阶段开放·待解）：{blocking_pending} 条\n"
        f"- 非阻塞性问题（当前阶段开放·待决策）：{nonblocking_pending} 条\n"
        f"- 当前阶段产物：\n{products_text}"
        f"{commit_line}\n\n"
        f"恢复工作:**先 Read process_record/decisions_ledger.md**（SSOT #18 已决策清单真源,执行时不得忽略）"
        f"+ **Read process_record/state.md**（当前阶段 / 产物路径 / ⏳ 开放问题）;再决定下一步。"
    )
    _emit_context(context)


if __name__ == "__main__":
    main()
