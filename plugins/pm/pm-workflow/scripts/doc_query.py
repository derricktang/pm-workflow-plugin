#!/usr/bin/env python3
"""doc_query.py — 大文档目录 + 按需分节读取（SSOT #81，治派发全读死重）

PM / Supervisor subagent 面对大规范 / 大成果文件（如 `AI产品经理_Agent.md` ~52k
tokens / `rule_hard_constraints.md` ~48k tokens / 产品定义 / spec），不再 Read 全文，
而是「先 outline 看架构 → 按标题 fetch 本任务相关章节」，按需加载上下文。

用法：
    python3 pm-workflow/scripts/doc_query.py outline <file.md>
    python3 pm-workflow/scripts/doc_query.py fetch <file.md> <标题1> [标题2 ...] [--max-tokens N]
    python3 pm-workflow/scripts/doc_query.py locate <file.md> <正则或子串>
    python3 pm-workflow/scripts/doc_query.py frames <prd.html>
    python3 pm-workflow/scripts/doc_query.py fetch-frame <prd.html> <prd_id ...> [--max-tokens N]

子命令：
    outline  打印标题树（层级 / 行区间 / 字符数 / ≈tokens），先看架构再决定取哪节
    fetch    按标题取章节内容（含子节；标题支持唯一子串匹配；可一次取多节）。
             多节合计超 --max-tokens 预算（默认 25000 估算 tokens）→ 拒绝
             输出内容，改吐各节尺寸 + 超额节的子目录，引导收窄到子节再取
             （防跨章共读撑爆上下文的机械闸）
    locate   按正则反查命中行所属章节路径（"这个 ID / 关键词在哪节" → 再 fetch）
    frames   列 outputs/prd_*.html 的 FRAME 块（prd_id / 行区间 / ≈tokens）——
             阶段4终审「机械全量 + 语义抽样」（SSOT #82）的帧级抽样入口
    fetch-frame  按 prd_id 取帧内容（唯一子串匹配 + 同预算闸），供 Supervisor
             抽样深读单帧而非全读 prd.html

设计约定：
- 仅解析 markdown ATX 标题（#{1,6} ），自动跳过 ``` / ~~~ 围栏代码块内的 # 行
- 章节跨度 = 本标题行 → 下一个同级或更高级标题前（自然含全部子节）
- token 估算 = CJK 字符 ×1 + 其他字符 ÷4（CJK 启发式，±30%）
- 子串匹配命中多节 → 列候选 + 行号退出（exit 2），用更长子串消歧
"""

import argparse
import os
import re
import sys
from pathlib import Path

# Ensure pm_paths is importable regardless of caller's cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_paths import FRAMEWORK_ROOT

DEFAULT_MAX_TOKENS = 25_000  # 估算 tokens，预算闸默认值

_ATX_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_CJK_RE = re.compile(r"[　-鿿豈-﫿＀-￯]")


def _est_tokens_text(text: str) -> int:
    cjk = len(_CJK_RE.findall(text))
    return cjk + (len(text) - cjk) // 4


class Section:
    __slots__ = ("level", "title", "start", "end", "chars", "tokens")

    def __init__(self, level: int, title: str, start: int):
        self.level = level
        self.title = title
        self.start = start  # 1-based 标题行号
        self.end = start    # 1-based 末行号（含）
        self.chars = 0
        self.tokens = 0


def parse_sections(lines: list) -> list:
    """解析 ATX 标题为 Section 列表（含 end / chars），跳过围栏代码块。"""
    heads = []
    in_fence = False
    fence_mark = ""
    for i, line in enumerate(lines, 1):
        fm = _FENCE_RE.match(line)
        if fm:
            mark = fm.group(1)
            if not in_fence:
                in_fence, fence_mark = True, mark
            elif mark == fence_mark:
                in_fence = False
            continue
        if in_fence:
            continue
        m = _ATX_RE.match(line)
        if m:
            heads.append(Section(len(m.group(1)), m.group(2), i))

    total = len(lines)
    for idx, sec in enumerate(heads):
        end = total
        for nxt in heads[idx + 1:]:
            if nxt.level <= sec.level:
                end = nxt.start - 1
                break
        sec.end = end
        body = "\n".join(lines[sec.start - 1:sec.end])
        sec.chars = len(body)
        sec.tokens = _est_tokens_text(body)
    return heads


def _match_sections(heads: list, query: str) -> list:
    exact = [s for s in heads if s.title == query]
    if exact:
        return exact
    return [s for s in heads if query in s.title]


def _breadcrumb(heads: list, line_no: int) -> str:
    """返回某行所属章节路径（h1 > h2 > h3 …）。"""
    path = {}
    for s in heads:
        if s.start <= line_no:
            path[s.level] = s.title
            for lv in list(path):
                if lv > s.level:
                    del path[lv]
        else:
            break
    owner = [path[lv] for lv in sorted(path)]
    return " > ".join(owner) if owner else "(文件头，无所属章节)"


def cmd_outline(heads: list, args) -> int:
    if not heads:
        print("(无 ATX 标题)")
        return 0
    top = min(h.level for h in heads)
    total_tok = sum(s.tokens for s in heads if s.level == top)
    print(f"# outline: {args.file}（~{total_tok} tokens 总量估算）")
    for s in heads:
        indent = "  " * (s.level - 1)
        print(f"{indent}- [L{s.start}-L{s.end}] {s.title}"
              f"  ({s.chars} chars ≈ {s.tokens} tok)")
    return 0


def _sub_outline(heads: list, sec: Section) -> str:
    subs = [s for s in heads
            if s.start > sec.start and s.end <= sec.end and s.level == sec.level + 1]
    if not subs:
        return "    (无子节 — 用 locate 定位后 Read offset/limit 取片段)"
    return "\n".join(
        f"    - [L{s.start}-L{s.end}] {s.title} ({s.chars} chars ≈ {s.tokens} tok)"
        for s in subs)


def cmd_fetch(heads: list, lines: list, args) -> int:
    picked = []
    for q in args.titles:
        hits = _match_sections(heads, q)
        if not hits:
            print(f"[ERROR] 标题未命中：{q!r}（先跑 outline 看实际标题）", file=sys.stderr)
            return 2
        if len(hits) > 1:
            print(f"[ERROR] 标题歧义：{q!r} 命中 {len(hits)} 节，用更长子串消歧：",
                  file=sys.stderr)
            for s in hits:
                print(f"  - [L{s.start}] {s.title}", file=sys.stderr)
            return 2
        picked.append(hits[0])

    # 同节去重（同一标题传两次 → 同对象，先按对象身份去重防双倍输出）
    picked = list(dict.fromkeys(picked))
    # 重叠合并：被其他选中节包含的节去重（防同内容双倍输出）
    picked = [s for s in picked
              if not any(o is not s and o.start <= s.start and o.end >= s.end
                         for o in picked)]

    budget = args.max_tokens
    total = sum(s.tokens for s in picked)
    if total > budget:
        print(f"[BUDGET] 请求 {len(picked)} 节合计 ≈{total} tokens，"
              f"超预算 --max-tokens={budget}。拒绝输出全文，请收窄到子节：",
              file=sys.stderr)
        for s in sorted(picked, key=lambda x: -x.tokens):
            print(f"  ■ [L{s.start}-L{s.end}] {s.title} "
                  f"({s.chars} chars ≈ {s.tokens} tok)", file=sys.stderr)
            print(_sub_outline(heads, s), file=sys.stderr)
        return 2

    for s in picked:
        print(f"===== [L{s.start}-L{s.end}] {s.title} (≈{s.tokens} tok) =====")
        print("\n".join(lines[s.start - 1:s.end]))
        print()
    return 0


_FRAME_START_RE = re.compile(r"<!--\s*\[FRAME-START:\s*([^\]|]+?)(?:\s*\|[^\]]*)?\]\s*-->")
_FRAME_END_RE = re.compile(r"<!--\s*\[FRAME-END:\s*([^\]]+?)\]\s*-->")


def parse_frames(lines: list) -> list:
    """解析 outputs/prd 的 [FRAME-START: id |…] / [FRAME-END: id] 块（assemble 注入）。"""
    frames = []
    open_at = {}
    for i, line in enumerate(lines, 1):
        m = _FRAME_START_RE.search(line)
        if m:
            open_at[m.group(1).strip()] = i
            continue
        m = _FRAME_END_RE.search(line)
        if m:
            fid = m.group(1).strip()
            if fid in open_at:
                sec = Section(0, fid, open_at.pop(fid))
                sec.end = i
                body = "\n".join(lines[sec.start - 1:sec.end])
                sec.chars = len(body)
                sec.tokens = _est_tokens_text(body)
                frames.append(sec)
    if open_at:  # 孤儿 FRAME-START（无配对 END）：静默丢弃 = 终审 checklist 漏帧
        print(f"[WARN] {len(open_at)} 个 FRAME-START 无配对 FRAME-END，"
              f"未列入帧清单（漏审风险，先修配对）：", file=sys.stderr)
        for fid, ln in sorted(open_at.items(), key=lambda kv: kv[1]):
            print(f"  - L{ln} {fid}", file=sys.stderr)
    return frames


def cmd_frames(frames: list, args) -> int:
    if not frames:
        print("(无 FRAME 块 — 非 assemble 拼装产物或骨架未填)")
        return 0
    print(f"# frames: {args.file}（{len(frames)} 帧，"
          f"合计 ≈{sum(f.tokens for f in frames)} tokens）")
    for f in frames:
        print(f"- [L{f.start}-L{f.end}] {f.title} ({f.chars} chars ≈ {f.tokens} tok)")
    return 0


def cmd_fetch_frame(frames: list, lines: list, args) -> int:
    picked = []
    for q in args.ids:
        hits = [f for f in frames if f.title == q] or [f for f in frames if q in f.title]
        if not hits:
            print(f"[ERROR] prd_id 未命中：{q!r}（先跑 frames 看清单）", file=sys.stderr)
            return 2
        if len(hits) > 1:
            print(f"[ERROR] prd_id 歧义：{q!r} 命中 {len(hits)} 帧：", file=sys.stderr)
            for f in hits:
                print(f"  - [L{f.start}] {f.title}", file=sys.stderr)
            return 2
        picked.append(hits[0])

    total = sum(f.tokens for f in picked)
    if total > args.max_tokens:
        print(f"[BUDGET] 请求 {len(picked)} 帧合计 ≈{total} tokens，"
              f"超预算 --max-tokens={args.max_tokens}。请减少单次帧数：", file=sys.stderr)
        for f in sorted(picked, key=lambda x: -x.tokens):
            print(f"  ■ [L{f.start}-L{f.end}] {f.title} (≈{f.tokens} tok)", file=sys.stderr)
        return 2

    for f in picked:
        print(f"===== [L{f.start}-L{f.end}] FRAME {f.title} (≈{f.tokens} tok) =====")
        print("\n".join(lines[f.start - 1:f.end]))
        print()
    return 0


def cmd_locate(heads: list, lines: list, args) -> int:
    try:
        pat = re.compile(args.pattern)
    except re.error:
        pat = re.compile(re.escape(args.pattern))
    hits = 0
    for i, line in enumerate(lines, 1):
        if pat.search(line):
            hits += 1
            print(f"L{i} [{_breadcrumb(heads, i)}]")
            print(f"    {line.strip()[:160]}")
            if hits >= args.limit:
                print(f"(已截断至前 {args.limit} 条命中)")
                break
    if not hits:
        print(f"(0 命中：{args.pattern!r})")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="大文档目录 + 按需分节读取（SSOT #81）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_o = sub.add_parser("outline", help="打印标题树")
    p_o.add_argument("file")

    p_f = sub.add_parser("fetch", help="按标题取章节（可多节）")
    p_f.add_argument("file")
    p_f.add_argument("titles", nargs="+")
    p_f.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)

    p_l = sub.add_parser("locate", help="正则反查命中行所属章节")
    p_l.add_argument("file")
    p_l.add_argument("pattern")
    p_l.add_argument("--limit", type=int, default=50)

    p_fr = sub.add_parser("frames", help="列 outputs/prd 的 FRAME 块（SSOT #82 抽样入口）")
    p_fr.add_argument("file")

    p_ff = sub.add_parser("fetch-frame", help="按 prd_id 取帧内容")
    p_ff.add_argument("file")
    p_ff.add_argument("ids", nargs="+")
    p_ff.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)

    args = ap.parse_args(argv)
    path = Path(args.file)
    if not path.exists():
        alt = FRAMEWORK_ROOT / args.file
        if alt.exists():
            path = alt
    if not path.exists():
        print(f"[ERROR] 文件不存在：{path}", file=sys.stderr)
        return 2
    lines = path.read_text(encoding="utf-8").splitlines()

    if args.cmd == "frames":
        return cmd_frames(parse_frames(lines), args)
    if args.cmd == "fetch-frame":
        return cmd_fetch_frame(parse_frames(lines), lines, args)

    heads = parse_sections(lines)
    if args.cmd == "outline":
        return cmd_outline(heads, args)
    if args.cmd == "fetch":
        return cmd_fetch(heads, lines, args)
    return cmd_locate(heads, lines, args)


if __name__ == "__main__":
    sys.exit(main())
