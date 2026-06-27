#!/usr/bin/env python3
"""strip_inline_change_markers.py — spec/prd 正文内联变更标记 **诊断报告工具（只读）**

治理对象：PM 手写进各阶段产物正文的内联变更 / 过程标记，如
  【v4.0 新增】 / 【CR-20260609-01 SUP-5】 / 【历史留痕 — 议题 9…】
  （CR-20260609-01 新增） / （议题 #2 2026-06-09） / （SSOT #61 … 新增 [Must] 子块）
这些把"变更历史 / 内部过程追溯"泄漏进交付给下游的正文，影响下游阅读。
真源纪律（SSOT #79「正文禁内联变更标记」）：变更历史只走 **变更记录表 + git**，
**查版本差异用 `git diff`**，正文不写内联标记。

**只读定位（不写文件）**：本工具只**定位 + 分类**标记，告诉 PM「哪里有 / 是哪类」，
**实际删除一律由 PM 手动做**。原因（审计实证 2026-06-10）：机械"删除"会损伤语义——
①共存新旧版本标记删后合并成矛盾句（`【v3.0】旧逻辑【v4.0】新逻辑` → `旧逻辑新逻辑`）
②需求与追溯同括号无法机械拆分（`（不进 phase_e；NB-256…G-07 授权）`）③悬挂分隔/空括号
等连带损伤。故移除了原 `--write` 自动删除，工具退回纯报告。

分类（仅供 PM 判断优先级，**均需人工改**）：
  version  版本标签   【vN.N…】              → 删标签留内容；**注意共存新旧勿合并**
  pure_ref 纯追溯     剔元数据后残留为空      → 整条删（无需求内容）
  mixed    融合       内容 + 追溯残留非空     → PM 拆（需求留正文 / 追溯进变更记录表）
  schema   结构白名单 【触发态】【组件】…       → 永不视为标记

用法（只读，永不改文件）：
  python3 strip_inline_change_markers.py outputs/spec_*.md outputs/产品定义_*.md
  python3 strip_inline_change_markers.py --show-fused outputs/spec_*.md   # 连融正文圆括号一并逐条列
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ── schema 结构标记白名单（R8 渲染契约 4 元素 + 5 维页面概述，永不视为变更标记）──────
SCHEMA_LABELS = frozenset({
    "触发态", "组件", "区域", "字段回显",          # R8 / SSOT #65/#77 触点 4 元素
    "业务定位", "页面区域构成", "核心交互链路",       # 5 维页面概述 / SSOT #61
    "跨平台关键差异", "跨模块关联",
})

# 来源标注 schema 前缀（proto_spec_md.md「（来源：§N）/（来源：阶段 N …）」必填派生标注，
# 含 vN.N 版本号也是合法溯源，**非**变更标记，永不视为污染）。
_SOURCE_PREFIX = ("来源", "来源：", "来源:")

# ── 元数据 token（用于 Tier 2a「纯 traceability」判定：剔除后残留为空即纯 ref）─────────
_META_TOKEN = re.compile(
    r"v\d+\.\d+"                                  # 版本号
    r"|CR-[0-9A-Za-z-]+"                          # 变更请求 ID
    r"|S?NB-[0-9A-Za-z-]+"                        # NB / SNB 编号
    r"|SUP-\d+"                                   # Supervisor NB
    r"|议题\s*#?\d+(?:\.\d+)?"                     # 议题 #N
    r"|SSOT\s*#\d+"                               # SSOT 锚号
    r"|\d{4}-\d{2}-\d{2}"                         # 日期
    r"|F-\d+"                                     # 功能号
    r"|新增|修订|变更|调整|删除|落地|备查|深化|部分回退|子块"
    r"|历史留痕|完整应用版|路径\s*[A-Z]|第[一二三四五六七八九十\d]+批"
    r"|\[Must\]|\[Should\]|★|✅"
    r"|[、，,；;：:。.\s\-—·／/]"                    # 分隔 / 标点 / 空白
)

# ── Tier 1：版本 tag（短，安全自动删）──────────────────────────────────────────────
_VERSION_TAG = re.compile(r"【\s*v\d+\.\d+(?:\s*(?:新增|修订|变更|调整|删除))?\s*】")

# ── 候选变更标记：含追溯信号的 【…】 / （…）（schema 白名单除外）────────────────────
# 注意：workflow-state 信号（PM 自审 / 提交主管）**不在此列**——它们是流程状态标记非
# 变更标记，且 precheck_stage1/2/3 check_submit_marker 强制要求其存在（勿与本规则冲突）。
_TRACE_SIGNAL = re.compile(
    r"v\d+\.\d+|CR-\d|S?NB-\d|SUP-\d|议题\s*#?\d|SSOT\s*#\d"
    r"|历史留痕|调整意见|完整应用版"
)
_BRACKET = re.compile(r"【([^】]*)】")
_PAREN = re.compile(r"（([^（）]*)）")

# precheck 复用：高置信 WARN pattern（紧，低 FP）— Tier1 版本 tag + 含强追溯信号的括号
# （workflow-state 标记 PM 自审 / 提交主管 不计入——见 _TRACE_SIGNAL 注释）
PRECHECK_BRACKET_RE = re.compile(
    r"【[^】]*(?:v\d+\.\d+|CR-\d|议题\s*#?\d|SSOT\s*#\d|历史留痕)[^】]*】"
)
PRECHECK_PAREN_RE = re.compile(
    r"（[^（）]*(?:CR-\d{4}|议题\s*#?\d|调整意见|SSOT\s*#\d)[^（）]*）"
)


def warn_inline_markers(label: str, text: str, r) -> int:
    """precheck 复用：扫一份阶段产物正文内联变更标记，命中经 r.warn 提示（调用方先开 r.section）。
    返回命中总数。**stage1/2/3/4 precheck 共用**——确保检测 pattern + WARN 文案单源（SSOT #79 / S4-68）。
    r 需有 .ok/.warn（各 precheck Report 同 API）。"""
    # 与 classify() 一致：`（来源：…）`/`【来源：…】` 派生溯源标注豁免（即便含 CR-/版本号）
    def _keep(matches: list[str]) -> list[str]:
        return [x for x in matches if not x[1:].lstrip().startswith(_SOURCE_PREFIX)]
    brackets = _keep(PRECHECK_BRACKET_RE.findall(text))
    parens = _keep(PRECHECK_PAREN_RE.findall(text))
    total = len(brackets) + len(parens)
    if total == 0:
        r.ok(f"[内联变更标记] {label} 正文无内联变更标记")
        return 0
    samples = (brackets + parens)[:8]
    more = f"（首 8 例，共 {total} 处）" if total > 8 else ""
    r.warn(
        f"[内联变更标记] {label} 正文含 {total} 处内联变更标记"
        f"（方括号 {len(brackets)} + 含 CR-/议题/SSOT/调整意见 圆括号 {len(parens)}）"
        f"——变更历史只走变更记录表 + git；**查版本差异用 `git diff`**，正文勿留内联标记（影响下游阅读、"
        f"且会顺前序阶段搬进交付 spec/prd）。定位（只读报告，删除 PM 手动做）："
        f"`python3 pm-workflow/scripts/strip_inline_change_markers.py <本文件>`。样例{more}：{' '.join(samples)}"
    )
    return total


def classify(inner: str, kind: str) -> str:
    """对一处标记内文 inner 分类。kind = 'bracket' | 'paren'。
    返回：'schema' | 'version' | 'pure_ref' | 'mixed' | 'content'。"""
    stripped = inner.strip()
    if kind == "bracket" and stripped in SCHEMA_LABELS:
        return "schema"
    if stripped.startswith(_SOURCE_PREFIX):     # （来源：…）派生溯源标注，非变更标记
        return "schema"
    if kind == "bracket" and _VERSION_TAG.fullmatch(f"【{inner}】"):
        return "version"
    if stripped in ("新增", "修订", "变更", "删除"):
        return "pure_ref"          # 裸变更动词括号（如（新增））→ 高置信标记
    if not _TRACE_SIGNAL.search(inner):
        return "content"           # 无追溯信号 → 视为正文，不动
    residue = _META_TOKEN.sub("", inner).strip()
    return "pure_ref" if residue == "" else "mixed"


def is_actionable(hit: dict) -> bool:
    """是否进"可逐处处理"清单。括号标记（有定界，清晰）一律列；圆括号 mixed
    因与正文深度融合（PM 预言的难点）只计数不逐条列，避免清单噪声淹没。"""
    if hit["kind"] == "bracket":
        return True
    return hit["tier"] in ("version", "pure_ref")


def scan(text: str) -> list[dict]:
    """扫描全文，返回每处标记 {line, col, raw, inner, kind, tier}。"""
    hits: list[dict] = []
    line_starts = [0]
    for m in re.finditer(r"\n", text):
        line_starts.append(m.end())

    def lineno(pos: int) -> int:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    for rx, kind in ((_BRACKET, "bracket"), (_PAREN, "paren")):
        for m in rx.finditer(text):
            inner = m.group(1)
            tier = classify(inner, kind)
            if tier in ("schema", "content"):
                continue
            hits.append({
                "line": lineno(m.start()),
                "raw": m.group(0),
                "inner": inner,
                "kind": kind,
                "tier": tier,
            })
    return hits


TIER_LABEL = {
    "version": "版本标签（删标签留内容；注意共存新旧勿合并）",
    "pure_ref": "纯追溯（整条删，无需求内容）",
    "mixed": "融合（PM 拆：需求留正文 / 追溯进变更记录表）",
}


def report(path: Path, hits: list[dict], show_fused: bool = False) -> dict:
    counts = {"version": 0, "pure_ref": 0, "mixed": 0}
    for h in hits:
        counts[h["tier"]] += 1
    fused = [h for h in hits if not is_actionable(h)]          # 圆括号 mixed，只计数
    print(f"\n══ {path} ══")
    print(f"  version  版本标签        : {counts['version']:>4}（{TIER_LABEL['version']}）")
    print(f"  pure_ref 纯追溯          : {counts['pure_ref']:>4}（{TIER_LABEL['pure_ref']}）")
    print(f"  mixed    融合（方括号）  : {counts['mixed'] - len(fused):>4}（{TIER_LABEL['mixed']}；下列出）")
    print(f"  融入正文圆括号（PM 判断）: {len(fused):>4}（与正文撞词，不逐条列；加 --show-fused 查看）")
    for h in [x for x in hits if is_actionable(x)][:40]:
        print(f"      L{h['line']} [{h['tier']}]: {h['raw']}")
    if show_fused:
        print("  — 融入正文圆括号（需 PM 逐处判断是否变更标记）：")
        for h in fused:
            print(f"      L{h['line']}: {h['raw']}")
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="spec/prd 正文内联变更标记 诊断报告（只读，不改文件；删除由 PM 手动做）")
    ap.add_argument("files", nargs="+", help="目标产物路径（spec/prd/需求分析/功能规划/产品定义，支持多个）")
    ap.add_argument("--show-fused", action="store_true",
                    help="报告里逐条列出融入正文的圆括号（默认仅计数）")
    args = ap.parse_args(argv)

    total = {"version": 0, "pure_ref": 0, "mixed": 0}
    for f in args.files:
        p = Path(f)
        if not p.is_file():
            print(f"[WARN] 跳过不存在的文件：{p}", file=sys.stderr)
            continue
        text = p.read_text(encoding="utf-8")
        hits = scan(text)
        counts = report(p, hits, show_fused=args.show_fused)
        for k in total:
            total[k] += counts[k]

    print(f"\n══ 合计 ══  version={total['version']}  "
          f"pure_ref={total['pure_ref']}  mixed={total['mixed']}")
    print("（只读报告，未改任何文件。删除一律 PM 手动做——机械删除会损伤语义，"
          "见脚本头注释。查版本差异用 `git diff`。）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
