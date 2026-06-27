#!/usr/bin/env python3
"""
assemble.py — 阶段四产出物拼装脚本

用法：
    python pm-workflow/scripts/assemble.py spec [--force-overwrite]
    python pm-workflow/scripts/assemble.py prd  [--force-overwrite]

可选参数：
    --force-overwrite   强制覆盖 outputs/ 下被手改的文件
                        （默认拼装会比对 sidecar fingerprint,检测到手改即 ERROR
                        中止以防数据丢失。当你确认手改可被覆盖,或仅改了「保留区」
                        时使用本标志）

前置条件（spec 模式）：
    - Foundation Agent 已向 outputs/spec_[产品名]_latest.md 追加 S0+S0.5+S1
    - 各模块 spec 草稿就绪：process_record/drafts/spec_M[XX]_draft.md

前置条件（prd 模式）：
    - outputs/prd_[产品名]_latest.html 骨架已由 gen_scaffold.py 生成
    - Foundation Agent 已填入产品规格区 A-01~A-08
    - 各模块 prd 草稿就绪：process_record/drafts/prd_M[XX]_draft.html
"""

import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# ── 路径约定 ──────────────────────────────────────────────────────────────────
REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
SCAFFOLD   = REPO_ROOT / "process_record" / "tasks" / "scaffold.json"
DRAFTS_DIR = REPO_ROOT / "process_record" / "drafts"
OUTPUT_DIR = REPO_ROOT / "outputs"
FALLBACK_CSS_PATH = REPO_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "fb-fallback.css"
FINGERPRINT_DIR = REPO_ROOT / "process_record" / "versions" / ".assemble_fingerprints"
BACKUP_DIR = REPO_ROOT / "process_record" / "versions" / ".assemble_backups"
PRD_TEMPLATE_PATH = REPO_ROOT / "pm-workflow" / "rules" / "prd_template.html"

# template hash 注释标记（嵌入 outputs/prd 头部，用于检测主模板升级）
TEMPLATE_HASH_COMMENT_PATTERN = r"<!--\s*template-hash:\s*([0-9a-f]{64})\s*-->"
TEMPLATE_HASH_COMMENT_FORMAT = "<!-- template-hash: {sha} -->"

# 兜底 CSS 注入标记（用于幂等检测）
FB_FALLBACK_START = "/* === FB FALLBACK START — auto-injected by assemble.py === */"
FB_FALLBACK_END   = "/* === FB FALLBACK END === */"

# proj 组件 CSS 注入标记（来自模块草稿，由 assemble.py prd 合并）
PROJ_CSS_START = "/* === [PROJ-CSS-START] auto-injected by assemble.py === */"
PROJ_CSS_END   = "/* === [PROJ-CSS-END] === */"

# ── 页面层级架构（提议1，SSOT 双锚 #38）──────────────────────────────────────
# 真源 = scaffold.json modules[].pages[]；assemble.py 现场派生「模块→页面」两层
# mermaid，注入 spec.md §3.0 + PRD spec-sitemap section。**不预烘焙**（H1=(c)
# 按引用消费）：无 spec_sitemap_draft.md，gen_scaffold 仅出空壳，内容由本脚本
# 在 Step4/6 现场读 scaffold 派生。改 scaffold 后重派 Step3/5 → 重跑本脚本自动
# 刷新；禁重跑 gen_scaffold。
# （2026-05-25 WE-LRTB 移除 SITEMAP_PAGE_THRESHOLD：原大/小产品 subgraph 分支
# 已统一改为始终 subgraph 分组——LR 布局下分组是必须的视觉锚，规模无关。）

# spec.md §3.0：Foundation 在区块1 顶写 SITEMAP_SPEC_MARKER 首次占位；
# assemble 替换为 START..END 包裹块，重跑时正则替换中间内容（FRAME 同型幂等）
SITEMAP_SPEC_MARKER = "<!-- [SITEMAP-3.0] -->"
SITEMAP_SPEC_START  = "<!-- [SITEMAP-3.0-START] auto-injected by assemble.py -->"
SITEMAP_SPEC_END    = "<!-- [SITEMAP-3.0-END] -->"

# WE-H（SSOT #41 per-archetype 单源）：Foundation 范式骨架草稿文件名
# （gen_scaffold.FOUNDATION_SKELETON_DRAFT_NAME 的对侧；改名须双向同步）。
FOUNDATION_SKELETON_DRAFT = "spec_foundation_draft.md"

# PRD spec-sitemap section：gen_scaffold 出空壳含 SITEMAP_PRD_PLACEHOLDER；
# assemble 替换为 START..END 包裹块，重跑幂等
SITEMAP_PRD_PLACEHOLDER = "<!-- [SITEMAP-PRD] -->"
SITEMAP_PRD_START       = "<!-- [SITEMAP-PRD-START] auto-injected by assemble.py -->"
SITEMAP_PRD_END         = "<!-- [SITEMAP-PRD-END] -->"


def _mermaid_escape(text) -> str:
    """Mermaid 节点标签转义（H4）：标签恒被双引号包裹，转义会破坏 mermaid 语法
    的字符。注意**非 HTML 转义域**——mermaid 在引号标签内用 HTML 实体表达特殊字符。"""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("[", "&#91;").replace("]", "&#93;")
        .replace("{", "&#123;").replace("}", "&#125;")
        .replace("(", "&#40;").replace(")", "&#41;")
        .replace("<", "&lt;").replace(">", "&gt;")
        .replace("|", "&#124;")
    )


def build_hierarchy_mermaid(data: dict) -> str:
    """从 scaffold 派生「产品根→模块→页面」两层层级 mermaid 源码（不含 fence / <pre>）。

    设计（提议1，B1 决定；2026-05-25 WE-LRTB 重构布局方向）：
    - 粒度仅到页面级（状态已在侧栏三层 + spec §3.2 流转图，不在此重复）。
    - 页面节点 ID 固定 `M\\d+_P\\d+` 形态 → precheck_stage4 check① 可靠计数
      （distinct 页面节点数 == scaffold 全量 pages 数），不受标签内容干扰。
    - **布局方向 `graph LR` + subgraph 内 `direction TB`**：mermaid 的 direction
      只控流向且反相关——TD/TB 同级横排（旧版痛点：每模块多页时横向挤压字号过
      小，[[issue 2026-05-18_1553_analyzed]] / [[issue 2026-05-25_1946]] 两次反
      馈未真改）；LR 流向左→右、同级竖排。外层 LR 让 PRODUCT_ROOT 在左、各模块
      subgraph 竖向堆叠在中列；模块 subgraph 内 `direction TB` 让该模块的页面
      竖排堆叠——两维空间各司其职（横轴=层级深度，竖轴=广度），文字默认横向。
    - **始终用 subgraph 分组**（统一形态，原 SITEMAP_PAGE_THRESHOLD 大/小产品
      分支已废除）：分组让模块边界清晰、避免所有页面挤入同一虚拟列。
    - route 用 ` · ` 分隔附在标签内（不用 <br/>，规避 mermaid htmlLabels 配置依赖）。
    """
    modules = data.get("modules", []) or []
    product = data.get("product", "产品")
    # 单图 frontmatter 切 ELK 渲染器——mermaid 默认 dagre 渲染器**忽略 subgraph
    # 内 direction 子语句**（mermaid 官方限制），导致 `direction TB` 失效、
    # subgraph 内 page 节点仍横排。ELK 渲染器尊重 subgraph 内 direction，让
    # page 真正竖排。**仅本图启用 ELK**，其他 mermaid 图（业务流程/用户旅程/
    # 模块依赖）保持 dagre 默认避免视觉回归。
    #
    # **架构限制：ELK 不支持 curve 配置**（mermaid 10.x 设计决策）——mermaid
    # ELK config schema 仅暴露 5 参数（mergeEdges / nodePlacementStrategy /
    # cycleBreakingStrategy / forceNodeModelOrder / considerModelOrder），不
    # 暴露 edgeRouting；ELK 自身硬编码 rounded right-angle（mermaid issue
    # #7213 修复后），无法通过 frontmatter 改成 B 样条曲线。**不加 curve:
    # basis**（dagre-only 参数，ELK 下被忽略且无效）。如未来 mermaid 修复
    # ELK + edgeRouting 暴露，可考虑加 elk: { edgeRouting: SPLINES }。
    # trade-off 已与产品总监确认：page 竖排是核心诉求，连线让步。
    lines: list[str] = [
        "---",
        "config:",
        "  flowchart:",
        "    defaultRenderer: elk",
        "---",
        "graph LR",
    ]

    def _page_node(mid: str, page: dict) -> tuple[str, str]:
        pid = page.get("id", "P??")
        node_id = f"{mid}_{pid}"
        label = _mermaid_escape(f'{pid} {page.get("name", "")}'.strip())
        route = page.get("route", "")
        if route:
            label += " · " + _mermaid_escape(route)
        return node_id, label

    root = "PRODUCT_ROOT"
    lines.append(f'  {root}["{_mermaid_escape(product)}"]')
    for mod in modules:
        mid = mod.get("id", "M??")
        mname = _mermaid_escape((mid + " " + mod.get("name", "")).strip())
        lines.append(f"  {root} --> {mid}")
        lines.append(f'  subgraph {mid}["{mname}"]')
        lines.append("    direction TB")
        for page in mod.get("pages", []) or []:
            node_id, label = _page_node(mid, page)
            lines.append(f'    {node_id}["{label}"]')
        lines.append("  end")
    return "\n".join(lines)


def _iter_page_archetype_map(data: dict):
    """yield (页面标签 'M01-P01', archetype_id) 覆盖全部模块页面。"""
    for mod in data.get("modules", []) or []:
        mid = mod.get("id", "M??")
        for p in mod.get("pages", []) or []:
            yield f"{mid}-{p.get('id', 'P??')}", p.get("archetype", "")


def build_archetype_contract_md(data: dict) -> str:
    """提议2（SSOT #39）：从 scaffold.page_archetypes 现场派生「页面结构范式契约」
    markdown（范式定义表 + 页面→范式映射表）。无 page_archetypes → 返回 ""
    （优雅降级：非提议2 scaffold 仅渲染 hierarchy，保 Commit1 行为 + 向后兼容）。"""
    archs = data.get("page_archetypes") or []
    if not archs:
        return ""
    lines = [
        "#### 页面结构范式契约",
        "",
        "> 由 `assemble.py` 从 `scaffold.json page_archetypes` 现场派生（SSOT #39），"
        "禁手改。Step3/5 模块 subagent 填页前须按本契约做容纳性二值校验"
        "（详见 `proto_spec_md.md`「页面结构范式契约」段）。",
        "",
        "**范式定义**",
        "",
        "| 范式 id | 名称 | 区域（slot → 容纳） | 不变量 | 扩展位 |",
        "|---------|------|--------------------|--------|--------|",
    ]
    for a in archs:
        regions = "； ".join(
            f"`{r.get('slot', '?')}`→{r.get('hosts', '')}"
            for r in (a.get("regions") or [])
        )
        inv = "；".join(a.get("invariants") or []) or "—"
        ext = "、".join(f"`{e}`" for e in (a.get("extension") or [])) or "—"
        lines.append(
            f"| `{a.get('id', '?')}` | {a.get('name', '')} | {regions} | {inv} | {ext} |"
        )
    lines += ["", "**页面 → 范式映射**", "", "| 页面 | 范式 |", "|------|------|"]
    for plabel, aid in _iter_page_archetype_map(data):
        lines.append(f"| {plabel} | `{aid}` |")
    return "\n".join(lines)


def build_archetype_contract_html(data: dict) -> str:
    """提议2（SSOT #39）：契约 HTML（注入 PRD spec-sitemap section）。
    无 page_archetypes → 返回 ""（优雅降级，同 md 版）。"""
    import html as _html

    archs = data.get("page_archetypes") or []
    if not archs:
        return ""

    def esc(x) -> str:
        return _html.escape(str(x))

    rows_def = []
    for a in archs:
        regions = "；".join(
            f"{esc(r.get('slot', '?'))}→{esc(r.get('hosts', ''))}"
            for r in (a.get("regions") or [])
        )
        inv = "；".join(esc(i) for i in (a.get("invariants") or [])) or "—"
        ext = "、".join(esc(e) for e in (a.get("extension") or [])) or "—"
        rows_def.append(
            f"<tr><td><code>{esc(a.get('id', '?'))}</code></td>"
            f"<td>{esc(a.get('name', ''))}</td><td>{regions}</td>"
            f"<td>{inv}</td><td>{ext}</td></tr>"
        )
    rows_map = [
        f"<tr><td>{esc(pl)}</td><td><code>{esc(aid)}</code></td></tr>"
        for pl, aid in _iter_page_archetype_map(data)
    ]
    return (
        '<div class="spec-block"><h3>页面结构范式契约</h3>'
        '<p style="color:var(--fb-text-hint);font-size:12px;">由 assemble.py 从 '
        "scaffold.json page_archetypes 现场派生（SSOT #39），禁手改。</p>"
        '<table class="spec-table full-width"><thead><tr>'
        "<th>范式 id</th><th>名称</th><th>区域（slot → 容纳）</th>"
        "<th>不变量</th><th>扩展位</th></tr></thead><tbody>"
        + "".join(rows_def)
        + '</tbody></table><table class="spec-table full-width" '
        'style="margin-top:12px;"><thead><tr><th>页面</th><th>范式</th></tr>'
        "</thead><tbody>"
        + "".join(rows_map)
        + "</tbody></table></div>"
    )


def _module_dep_mermaid_lines(modules: list) -> list[str]:
    """模块依赖 graph TB 源行（节点=模块，边=depends_on kind→目标模块）。

    Item 3（2026-05-18，issue #3）：方向由 `graph LR`→`graph TB`——并列模块
    竖向堆叠（利用纵向空间），规避 LR + 中文标签横排导致整体过宽不便阅读。
    #38 层级图本就 `graph TD`（同向）；本函数是 spec-sitemap 唯一 LR 源。
    超宽场景（泳道角色多）由 prd_template.html 全屏预览 modal 兜底（覆盖全
    mermaid，含 Foundation 手绘的 A-04/A-04.2）。"""
    lines = ["graph TB"]
    for m in modules:
        mid = m.get("id", "M??")
        lines.append(
            f'  {mid}["{_mermaid_escape((mid + " " + m.get("name", "")).strip())}"]'
        )
    for m in modules:
        mid = m.get("id", "M??")
        for d in (m.get("depends_on", []) or []):
            tgt = d.get("module", "")
            if tgt:
                lines.append(
                    f'  {mid} -->|{_mermaid_escape(d.get("kind", "?"))}| {tgt}'
                )
    return lines


def build_module_arch_md(data: dict) -> str:
    """提议3（SSOT #40）：从 scaffold.modules[] 现场派生「模块架构说明」markdown
    （模块表 + 模块依赖 mermaid）。modules 空 → ""（优雅降级）。purpose 为
    **可选**字段——缺省时职责列回退 "—"（不 FAIL，D2 决定）。"""
    modules = data.get("modules", []) or []
    if not modules:
        return ""
    lines = [
        "#### 模块架构说明",
        "",
        "> 由 `assemble.py` 从 `scaffold.json modules[]`（name / 可选 purpose / "
        "depends_on）现场派生（SSOT #40），禁手改；改 scaffold 后重跑 assemble 刷新。",
        "",
        "| 模块 | 名称 | 职责 | 依赖（kind→目标模块）|",
        "|------|------|------|---------------------|",
    ]
    for m in modules:
        mid = m.get("id", "M??")
        deps = m.get("depends_on", []) or []
        dep_str = "；".join(
            f"{d.get('kind', '?')}→{d.get('module', '?')}" for d in deps
        ) or "—"
        lines.append(
            f"| `{mid}` | {m.get('name', '')} | {m.get('purpose') or '—'} | {dep_str} |"
        )
    lines += ["", "**模块依赖关系**", "", "```mermaid"]
    lines += _module_dep_mermaid_lines(modules)
    lines.append("```")
    return "\n".join(lines)


def build_module_arch_html(data: dict) -> str:
    """提议3（SSOT #40）：模块架构说明 HTML（注入 PRD spec-sitemap section）。
    modules 空 → ""（优雅降级，同 md 版）。"""
    import html as _html

    modules = data.get("modules", []) or []
    if not modules:
        return ""

    def esc(x) -> str:
        return _html.escape(str(x))

    rows = []
    for m in modules:
        deps = m.get("depends_on", []) or []
        dep_str = "；".join(
            f"{esc(d.get('kind', '?'))}→{esc(d.get('module', '?'))}" for d in deps
        ) or "—"
        rows.append(
            f"<tr><td><code>{esc(m.get('id', 'M??'))}</code></td>"
            f"<td>{esc(m.get('name', ''))}</td>"
            f"<td>{esc(m.get('purpose') or '—')}</td><td>{dep_str}</td></tr>"
        )
    mermaid_src = "\n".join(_module_dep_mermaid_lines(modules))
    return (
        '<div class="spec-block"><h3>模块架构说明</h3>'
        '<p style="color:var(--fb-text-hint);font-size:12px;">由 assemble.py 从 '
        "scaffold.json modules[] 现场派生（SSOT #40），禁手改。</p>"
        '<table class="spec-table full-width"><thead><tr><th>模块</th>'
        "<th>名称</th><th>职责</th><th>依赖（kind→目标模块）</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
        f'<pre class="mermaid">\n{mermaid_src}\n</pre></div>'
    )


def extract_spec_skeletons(
    data: dict,
) -> list[tuple[str, str, str, str, list[tuple[str | None, str]]]]:
    """SSOT #41：从各 `spec_M[XX]_draft.md` 的 `S2.M[XX].1 页面概述` 段提取
    (module_id, module_name, page_id, page_name, [(platform|None, skeleton_inner), …])。

    锚点 = gen_scaffold 预生成的 `- **P[XX] 页面名** …` 锚行 + 紧随其后的
    ```skeleton 围栏块（非 `### P-{ID}` 标题——v2.0 无此分割，详
    `proto_spec_md.md §三.5`）。提取范围严格限定在 `## S2.<mid>.1` 段内
    （至下一 `## ` 标题止），杜绝误抓 .2~.6 内容。

    **WE-G 条件 per-platform（2026-05-19）**：围栏 info-string ` ```skeleton `
    （platform=None，全平台通用）或 ` ```skeleton:{frame} `（platform=frame
    token，跨端发散页）。**一页内取 segment 内全部 ```skeleton(:plat)? 块**
    （EITHER 1 agnostic OR ≥1 per-platform；1-vs-N 是 PM 判断，本函数只如实
    收集、不强制）。

    spec draft 缺失 / 段内无骨架块 → 跳过该模块（优雅降级，**不阻断 PRD
    主拼装**——精确性兜底由 `precheck_stage4` S4-32 对 assembled spec.md 负责，
    与 sitemap / proj-css 等"缺失即 WARN 跳过 + precheck FAIL 兜底"同型）。
    """
    import re
    anchor_re = re.compile(r"^[ \t]*-[ \t]*\*\*(P\d+)[ \t]+(.+?)\*\*", re.MULTILINE)
    # WE-G：可选 :platform 标签（围栏 info-string）
    fence_re = re.compile(r"```skeleton(?::(\w+))?[ \t]*\n(.*?)\n```", re.DOTALL)
    out: list[tuple[str, str, str, str, list[tuple[str | None, str]]]] = []
    for mod in data.get("modules", []) or []:
        mid = mod.get("id", "M??")
        mname = mod.get("name", "")
        draft = DRAFTS_DIR / f"spec_{mid}_draft.md"
        if not draft.exists():
            print(
                f"[WARN] {draft.name} 缺失，逐页骨架跳过 {mid}"
                f"（precheck_stage4 S4-32 对 spec.md 兜底）",
                file=sys.stderr,
            )
            continue
        text = draft.read_text(encoding="utf-8")
        sec = re.search(
            r"##[ \t]*S2\.[^\s.]+\.1[ \t].*?(?=\n##[ \t]|\Z)", text, re.DOTALL
        )
        scope = sec.group(0) if sec else text
        anchors = list(anchor_re.finditer(scope))
        for i, m in enumerate(anchors):
            seg_end = anchors[i + 1].start() if i + 1 < len(anchors) else len(scope)
            seg = scope[m.end():seg_end]
            blocks = [
                (f.group(1) or None, f.group(2).strip())
                for f in fence_re.finditer(seg)
            ]
            if not blocks:
                continue
            out.append((mid, mname, m.group(1), m.group(2).strip(), blocks))
    return out


def extract_archetype_skeletons(
    data: dict,
) -> dict[str, dict]:
    """SSOT #41（WE-H per-archetype 单源，含 `prose` 散文段提取）：从
    Foundation 草稿 `spec_foundation_draft.md` 的
    `## 范式骨架` 段提取 `{archetype_id: {"prose": str, "blocks": [(platform|None,
    skeleton_inner), …]}}`。

    锚点 = gen_scaffold 预生成的 `- **<aid> 名称**` 锚行（aid 必 ∈
    scaffold.page_archetypes ids——白名单校验，杜绝误抓正文 bold）+ 紧随其后的
    ```skeleton(:plat)? 围栏块。提取范围严格限定 `## 范式骨架` 段内（至下一
    `## ` 标题止）。**WE-G 条件 per-platform 在 archetype 级复用**：围栏正则
    与 per-page 同——` ```skeleton `（agnostic）/ ` ```skeleton:{frame} `；一
    范式内取 segment 内全部块（EITHER 1 agnostic OR ≥1 per-platform，1-vs-N
    由 Foundation 判断，本函数只如实收集）。

    **`prose` 散文段**：锚行下到首
    个 ```skeleton 围栏前的散文段（去除前后空行 + 去除空 `[Foundation 填：…]`
    占位行）是该范式的**业务语义文字说明**，与 ```skeleton 同属真源；
    `build_archetype_skeleton_md/_html` 派生时一并注入 outputs，让下游 PM /
    Supervisor / 产品总监在 spec §3.0 + PRD sk-askel 阅读处直接看到 archetype
    业务语义。proto_spec_md.md §四 明示文字段是真源一部分。

    草稿缺失 / 段内某 archetype 无骨架块 → 该 aid 不入 dict（优雅降级——
    精确性兜底由 precheck_stage4 S4-32「每 archetype 有良构骨架」对 assembled
    产物 WARN 负责，与 sitemap/proj-css 同型）。"""
    import re
    archs = data.get("page_archetypes") or []
    if not archs:
        return {}
    valid_ids = {a.get("id", "") for a in archs if a.get("id")}
    draft = DRAFTS_DIR / FOUNDATION_SKELETON_DRAFT
    if not draft.exists():
        print(
            f"[WARN] {FOUNDATION_SKELETON_DRAFT} 缺失，范式骨架跳过"
            f"（precheck_stage4 S4-32 对 §3.0 产物 WARN 兜底）",
            file=sys.stderr,
        )
        return {}
    text = draft.read_text(encoding="utf-8")
    sec = re.search(r"##[ \t]*范式骨架[ \t]*\n.*?(?=\n##[ \t]|\Z)", text, re.DOTALL)
    scope = sec.group(0) if sec else text
    anchor_re = re.compile(r"^[ \t]*-[ \t]*\*\*([\w-]+)[ \t]+(.+?)\*\*", re.MULTILINE)
    fence_re = re.compile(r"```skeleton(?::(\w+))?[ \t]*\n(.*?)\n```", re.DOTALL)
    placeholder_re = re.compile(r"^\s*\[Foundation 填[:：][^\]]*\]\s*$", re.MULTILINE)
    out: dict[str, dict] = {}
    anchors = list(anchor_re.finditer(scope))
    for i, m in enumerate(anchors):
        aid = m.group(1)
        if aid not in valid_ids:
            continue  # 非 scaffold 范式 id 的 bold 行，跳过（白名单纪律）
        seg_end = anchors[i + 1].start() if i + 1 < len(anchors) else len(scope)
        seg = scope[m.end():seg_end]
        # 提取散文段：锚行 end 到首个 ```skeleton 围栏 start 之间的内容
        first_fence = fence_re.search(seg)
        prose_raw = seg[:first_fence.start()] if first_fence else seg
        # 清理：去除空 `[Foundation 填：…]` 占位行 + 前后 strip
        prose = placeholder_re.sub("", prose_raw).strip()
        blocks = [
            (f.group(1) or None, f.group(2).strip())
            for f in fence_re.finditer(seg)
        ]
        if blocks or prose:
            out[aid] = {"prose": prose, "blocks": blocks}
    return out


def build_archetype_skeleton_md(data: dict) -> str:
    """SSOT #41（WE-H，子决策B 独立子节）：从 Foundation 草稿派生「范式骨架」
    markdown，置于 §3.0 #39 契约表后（assemble.inject_spec_sitemap 串接）。
    无 page_archetypes → ""（优雅降级，同 build_archetype_contract_md）。
    每范式一块：` ```skeleton ` 围栏 verbatim（per-platform 多块带平台标签）；
    Foundation 未填该范式 → 占位说明（precheck S4-32 WARN 兜底，非静默）。"""
    archs = data.get("page_archetypes") or []
    if not archs:
        return ""
    sk_map = extract_archetype_skeletons(data)
    lines = [
        "#### 范式骨架",
        "",
        "> 由 `assemble.py` 从 Foundation 草稿 `spec_foundation_draft.md`「## 范式"
        "骨架」段现场提取（SSOT #41，#41=#39 视觉化身），禁手改 outputs；与上方"
        "页面结构范式契约 colocate。每范式一代表性 2D 平面布局，被所有引用该范式"
        "的页复用（默认零 per-page 撰写；个别页确无法套范式才在模块草稿 per-page "
        "override）。",
        "",
    ]
    for a in archs:
        aid = a.get("id", "?")
        lines.append(f"**{a.get('name', '')}**（`{aid}`）")
        lines.append("")
        entry = sk_map.get(aid)
        if not entry:
            lines += [
                "> （范式骨架待 Foundation 子阶段二填；precheck S4-32 WARN 兜底）",
                "",
            ]
            continue
        # 注入散文段：业务语义文字
        # 说明与 ```skeleton 同属真源；spec §3.0 阅读处直接看到 archetype 语义。
        prose = entry.get("prose") or ""
        if prose:
            lines += [prose, ""]
        blocks = entry.get("blocks") or []
        if not blocks:
            lines += [
                "> （范式骨架代码块待 Foundation 子阶段二填；precheck S4-32 WARN 兜底）",
                "",
            ]
            continue
        for plat, sk in blocks:
            if plat is not None:
                lbl = PAGE_SKELETON_PLATFORM_LABEL.get(plat, plat)
                lines.append(f"_{lbl} 布局_")
                lines.append("")
            lines += [f"```skeleton{':' + plat if plat else ''}", sk, "```", ""]
    return "\n".join(lines).rstrip()


def build_archetype_skeleton_html(data: dict) -> str:
    """SSOT #41（WE-H）：范式骨架 HTML（注入 PRD spec-sitemap，子决策B 独立
    子节）。每范式 `<div id="sk-askel-<aid>">` 子锚——非 override 页帧旁范式
    chip `showSection('sk-askel-<aid>')` 据此深链（复用 WE-B/WE-F sk-* 锚机制，
    WE-F R1 已让 check_prd 解析 sk-* div 锚）。无 page_archetypes → ""（优雅
    降级，同 build_archetype_contract_html）。骨架内 sk-* div verbatim 注入
    （同 inject_page_skeletons 信任模型；.sk-* CSS + applySkeletonDims 渲染）。"""
    import html as _html
    import re

    archs = data.get("page_archetypes") or []
    if not archs:
        return ""
    sk_map = extract_archetype_skeletons(data)
    parts = [
        '<div class="spec-block"><h3>范式骨架</h3>'
        '<p style="color:var(--fb-text-hint);font-size:12px;">由 assemble.py 从 '
        "Foundation 草稿 spec_foundation_draft.md「范式骨架」段现场提取（SSOT "
        "#41，#41=#39 视觉化身），禁手改。每范式一代表性平面布局，被所有引用"
        "该范式的页复用；个别页确无法套范式才在模块草稿 per-page override。</p>"
    ]
    for a in archs:
        aid = a.get("id", "?")
        parts.append(
            f'<div id="sk-askel-{_html.escape(aid)}" style="margin:14px 0;">'
            f'<div style="color:var(--fb-text-secondary);font-size:13px;'
            f'font-weight:600;margin-bottom:6px;">{_html.escape(a.get("name", ""))}'
            f'（<code>{_html.escape(aid)}</code>）</div>'
        )
        entry = sk_map.get(aid)
        # 注入散文段：业务语义文字
        # 说明与 ```skeleton 同属真源；PRD sk-askel 阅读处直接看到 archetype 语义。
        prose = (entry or {}).get("prose") or ""
        if prose:
            # 基础 markdown → HTML：双换行 → 段落、单换行 → <br>；保留 ** bold ** / `code`
            prose_esc = _html.escape(prose)
            # 处理 bold `**xxx**` → `<strong>xxx</strong>`
            prose_html = re.sub(r'\*\*([^*\n]+)\*\*', r'<strong>\1</strong>', prose_esc)
            # 处理 inline code `xxx` → `<code>xxx</code>`
            prose_html = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', prose_html)
            # 段落分隔：双换行 → </p><p>；单换行 → <br>
            paragraphs = [p.strip().replace('\n', '<br>') for p in re.split(r'\n\s*\n', prose_html) if p.strip()]
            prose_html = ''.join(f'<p style="margin:6px 0;">{p}</p>' for p in paragraphs)
            parts.append(
                f'<div style="color:var(--fb-text-secondary);font-size:13px;'
                f'line-height:1.6;margin-bottom:8px;">{prose_html}</div>'
            )
        blocks = (entry or {}).get("blocks") or []
        if not blocks:
            parts.append(
                '<div style="color:var(--fb-text-hint);font-size:12px;">'
                "（范式骨架代码块待 Foundation 子阶段二填；precheck S4-32 WARN 兜底）</div>"
            )
        else:
            # 含 per-platform 块时包 .sk-archetype-platforms flex 容器,让多端骨架
            # 横排左右对比（CSS flex-wrap:wrap,窄视口自动换行兜底）；agnostic 单块零包裹
            has_per_platform = any(plat is not None for plat, _ in blocks)
            if has_per_platform:
                parts.append('<div class="sk-archetype-platforms">')
            for plat, sk in blocks:
                if plat is not None:
                    lbl = PAGE_SKELETON_PLATFORM_LABEL.get(plat, _html.escape(plat))
                    plat_esc = _html.escape(plat)
                    # 平台几何 wrapper：phone/h5/mp 端 .sk-page 据 CSS 自动收窄至窄宽
                    # portrait（详 .sk-platform-* CSS），让 reviewer 一眼看出平台差异
                    parts.append(f'<div class="sk-platform sk-platform-{plat_esc}">')
                    parts.append(
                        f'<div style="margin:6px 0 4px;color:var(--fb-text-secondary);'
                        f'font-size:12px;font-weight:600;">{lbl} 布局</div>'
                    )
                    parts.append(sk)
                    parts.append("</div>")
                else:
                    parts.append(sk)
            if has_per_platform:
                parts.append('</div>')
        parts.append("</div>")
    parts.append("</div>")
    return "".join(parts)


PAGE_SKELETON_START = "<!-- [PAGE-SKELETON-START: {tag}] auto-injected by assemble.py -->"
PAGE_SKELETON_END = "<!-- [PAGE-SKELETON-END: {tag}] -->"

# WE-G：frame token → 展示标签（per-platform 骨架块前置小标题）
PAGE_SKELETON_PLATFORM_LABEL = {
    "phone": "📱 APP", "desktop": "🖥 桌面 Web", "tablet": "📲 PAD",
    "h5": "📱 H5", "mp": "💬 小程序",
}


def inject_page_skeletons(html: str, data: dict) -> tuple[str, tuple[int, int]]:
    """SSOT #41（WE-H per-archetype 重设，2026-05-19）：填每页首帧 proto-section
    内 `<!-- [PAGE-SKELETON: {mid}-{pid}] -->` 占位。**Why WE-H**：#41 = #39 的
    视觉化身，单源回 per-archetype（一类页一骨架，§3.0 中央定义）；per-page
    具体只在罕见「确无法套范式」时 override。故每页帧旁渲染**二选一**：

    - **非 override 页（默认，绝大多数）**：轻量「结构范式」chip——`结构范式：
      <aid> ▸ 见 页面架构总览 › 范式骨架`，onclick `showSection('sk-askel-<aid>')`
      深链中央 archetype 骨架（复用 WE-B/WE-F sk-* 锚机制，WE-F R1 已让
      check_prd 解析 sk-* div 锚；showSection 同 state-chip/nav，doc-chrome）。
      **零 per-page 撰写**——「排列太乱」基本消解（多数页帧旁仅小 chip 无骨架）。
    - **override 页（罕见）**：模块草稿该页 per-page 槽新增了 ```skeleton 覆盖块
      → 帧旁渲该 override 骨架 + `页面专属骨架（覆盖范式 <aid>）` distinct 标记
      区分中央范式骨架/普通帧。WE-G per-platform 在 override 级仍适用（多块堆叠
      + 平台标签）。

    占位真源 = `gen_scaffold.build_module_sections`（每页首 state 一次，WE-H 不
    变）；override 映射 = `extract_spec_skeletons`（per-page 槽 WE-H 已 override-
    only：未 override = 纯注释 marker 无围栏 → 不提取 → 自动走 chip 分支，无
    "每页必填"压力 / 无 SNB-006 redux）；page→archetype 取 scaffold 现场。
    占位替换 / START..END 重入幂等（同 FRAME 型）。override 骨架 verbatim 注入
    （同 extract_frames 信任模型；.sk-* CSS + applySkeletonDims 渲染）。

    占位不存在（旧骨架未重生 gen_scaffold）→ 优雅跳过该页（precheck S4-32
    对 §3.0/spec 产物 WARN 兜底）。返回 (新 html, (override 页数, chip 页数))。
    """
    import re, html as _html
    overrides = {
        (mid, pid): blocks
        for mid, _mn, pid, _pn, blocks in extract_spec_skeletons(data)
    }
    n_override = n_chip = 0
    for mod in data.get("modules", []) or []:
        mid = mod.get("id", "M??")
        for p in mod.get("pages", []) or []:
            pid = p.get("id", "P??")
            pname = p.get("name", "")
            aid = p.get("archetype", "")
            tag = f"{mid}-{pid}"
            ov = overrides.get((mid, pid))
            parts = [PAGE_SKELETON_START.format(tag=tag)]
            if ov:
                parts.append(
                    f'        <div style="margin:14px 0 6px;color:var(--fb-warning,'
                    f'#b26a00);font-size:12px;font-weight:600;">页面专属骨架'
                    f'（覆盖范式 <code>{_html.escape(aid or "?")}</code>，本页 2D '
                    f'排布无法套范式骨架）— {_html.escape(mid)} / {_html.escape(pid)} '
                    f'{_html.escape(pname)}</div>'
                )
                # 同 build_archetype_skeleton_html：含 per-platform 时包横排 flex 容器
                ov_has_per_platform = any(p is not None for p, _ in ov)
                if ov_has_per_platform:
                    parts.append('        <div class="sk-archetype-platforms">')
                for plat, sk_html in ov:
                    if plat is not None:
                        lbl = PAGE_SKELETON_PLATFORM_LABEL.get(plat, _html.escape(plat))
                        plat_esc = _html.escape(plat)
                        # 平台几何 wrapper（同 build_archetype_skeleton_html）：phone/h5/mp 自动收窄
                        parts.append(f'        <div class="sk-platform sk-platform-{plat_esc}">')
                        parts.append(
                            f'        <div style="margin:8px 0 4px;color:'
                            f'var(--fb-text-secondary);font-size:12px;font-weight:600;">'
                            f'{lbl} 布局</div>'
                        )
                        parts.append(sk_html)
                        parts.append('        </div>')
                    else:
                        parts.append(sk_html)
                if ov_has_per_platform:
                    parts.append('        </div>')
                n_override += 1
            elif aid:
                parts.append(
                    f'        <div class="sk-archetype-chip" style="margin:12px 0 6px;'
                    f'font-size:12px;color:var(--fb-text-hint);">结构范式：'
                    f'<code>{_html.escape(aid)}</code> ▸ '
                    f'<span style="cursor:pointer;color:var(--fb-primary,#2563eb);" '
                    f'onclick="showSection(\'sk-askel-{_html.escape(aid)}\')">'
                    f'见 页面架构总览 › 范式骨架</span></div>'
                )
                n_chip += 1
            else:
                # 无 archetype（agnostic scaffold）且无 override → 占位保留原样
                continue
            parts.append("        " + PAGE_SKELETON_END.format(tag=tag))
            block = "\n".join(parts)
            reentry = re.compile(
                re.escape(PAGE_SKELETON_START.format(tag=tag))
                + r".*?"
                + re.escape(PAGE_SKELETON_END.format(tag=tag)),
                re.DOTALL,
            )
            if reentry.search(html):
                html = reentry.sub(lambda _m: block, html, count=1)
                continue
            placeholder = f"<!-- [PAGE-SKELETON: {tag}] -->"
            if placeholder in html:
                html = html.replace(placeholder, block, 1)
            else:
                # 占位不存在 → 回退计数（未实际注入）
                if ov:
                    n_override -= 1
                elif aid:
                    n_chip -= 1
    return html, (n_override, n_chip)


def inject_spec_sitemap(spec_text: str, data: dict) -> tuple[str, bool]:
    """把派生层级图注入 spec.md §3.0（marker 替换 / START..END 重入幂等）。

    Foundation 在区块1 顶写 SITEMAP_SPEC_MARKER；首次拼装替换 marker，重跑时
    替换 START..END 中间内容（与 FRAME 同型，重跑自动刷新；改 scaffold 后下次
    Step4 自然重生）。Foundation 未写 marker 且无既有块 → WARN + 跳过，
    precheck_stage4 check① FAIL 兜底（不阻断 spec 主拼装）。
    返回 (新文本, 是否注入)。
    """
    import re
    mermaid_src = build_hierarchy_mermaid(data)
    contract_md = build_archetype_contract_md(data)  # 提议2，无 page_archetypes → ""
    contract_block = f"\n{contract_md}\n" if contract_md else ""
    # WE-H（SSOT #41，子决策B）：#39 契约表后紧跟「范式骨架」独立子节
    skeleton_md = build_archetype_skeleton_md(data)  # 无 page_archetypes → ""
    skeleton_block = f"\n{skeleton_md}\n" if skeleton_md else ""
    mod_arch_md = build_module_arch_md(data)  # 提议3，无 modules → ""
    mod_arch_block = f"\n{mod_arch_md}\n" if mod_arch_md else ""
    block = (
        f"{SITEMAP_SPEC_START}\n"
        f"### 3.0 页面层级架构\n\n"
        f"> 本节由 `assemble.py` 从 `scaffold.json` 现场派生（模块→页面两层），"
        f"禁止手改；改 scaffold 后重跑 Step4 自动刷新（SSOT 双锚 #38）。\n\n"
        f"```mermaid\n{mermaid_src}\n```\n"
        f"{contract_block}"
        f"{skeleton_block}"
        f"{mod_arch_block}"
        f"{SITEMAP_SPEC_END}"
    )
    reentry_re = re.compile(
        re.escape(SITEMAP_SPEC_START) + r".*?" + re.escape(SITEMAP_SPEC_END),
        re.DOTALL,
    )
    if reentry_re.search(spec_text):
        return reentry_re.sub(lambda _m: block, spec_text, count=1), True
    if SITEMAP_SPEC_MARKER in spec_text:
        return spec_text.replace(SITEMAP_SPEC_MARKER, block, 1), True
    print(
        "[WARN] spec.md 区块1 未发现 [SITEMAP-3.0] marker（Foundation 应在区块1 顶写入）；"
        "跳过 §3.0 注入，precheck_stage4 check① 会 FAIL 兜底",
        file=sys.stderr,
    )
    return spec_text, False


def inject_prd_sitemap(html: str, data: dict) -> tuple[str, bool]:
    """填 PRD spec-sitemap section 内容（占位替换 / START..END 重入幂等）。

    gen_scaffold 出 spec-sitemap 空壳含 SITEMAP_PRD_PLACEHOLDER；assemble 现场
    读 scaffold 派生 `<pre class="mermaid">`。复用与 A-04.2 同一 mermaid 初始化/CDN
    （SSOT #2 派生5 `_overwrite_scripts_from_template` 已覆盖 mermaid CDN+内联）；
    但 sitemap **无 toggle**，渲染由 template `<script>` 的 `renderStaticMermaid()`
    在 DOMContentLoaded 急渲染触发（非 switchJourneyView——后者只渲 .journey-flow-view；
    init≠render，详 prd_expression_standard.md §A-04.1.4 第 4 项）。

    本 section colocate 四块（**可复用 / 概览**语义层）：#38 层级图 + #39 页面
    结构范式契约 + **#41 范式骨架（WE-H 单源回 per-archetype，sk-askel；子决策B
    独立子节，#39 契约后）** + #40 模块架构说明。**WE-H**：#41=#39 视觉化身，
    pre-WE-E 概览位对 per-archetype 本就正确（非 WE-E 批"重复页清单"——per-
    archetype 是 ~N 小目录）；per-page 具体只在罕见 override 时随帧（见
    `inject_page_skeletons`，默认页帧旁仅 chip 深链 sk-askel-<aid>）。
    返回 (新 html, 是否注入)。
    """
    import re
    mermaid_src = build_hierarchy_mermaid(data)
    contract_html = build_archetype_contract_html(data)  # 提议2，无 → ""
    skeleton_html = build_archetype_skeleton_html(data)  # WE-H #41，无 → ""
    mod_arch_html = build_module_arch_html(data)  # 提议3，无 modules → ""
    # Item 2（2026-05-18）/ WE-H（2026-05-19）：4 块各裹 `<div id="sk-*">` 锚——
    # 「页面架构总览」顶层组 nav 子项 `showSection('sk-*')` 据此锚点滚动
    # （spec-sitemap 单 section 不拆，precheck S4-29/30/31 仍在本 section 找内容、
    # 零回归；锚 id 是 gen_scaffold.SITEMAP_NAV_ANCHORS 的派生对侧，改名须同步）。
    # 始终输出 4 锚 div（内容可空——优雅降级时 nav 仍可点不死链）。sk-askel 内
    # 含每范式 <div id="sk-askel-<aid>"> 子锚（非 override 页帧旁 chip 深链对侧）。
    block = (
        f"{SITEMAP_PRD_START}\n"
        f'            <div id="sk-hier"><pre class="mermaid">\n{mermaid_src}\n            </pre></div>\n'
        f'            <div id="sk-arch">{contract_html}</div>\n'
        f'            <div id="sk-askel">{skeleton_html}</div>\n'
        f'            <div id="sk-mod">{mod_arch_html}</div>\n'
        f"            {SITEMAP_PRD_END}"
    )
    reentry_re = re.compile(
        re.escape(SITEMAP_PRD_START) + r".*?" + re.escape(SITEMAP_PRD_END),
        re.DOTALL,
    )
    if reentry_re.search(html):
        return reentry_re.sub(lambda _m: block, html, count=1), True
    if SITEMAP_PRD_PLACEHOLDER in html:
        return html.replace(SITEMAP_PRD_PLACEHOLDER, block, 1), True
    print(
        "[WARN] prd.html 未发现 [SITEMAP-PRD] 占位（gen_scaffold spec-sitemap 空壳应含）；"
        "跳过 sitemap 注入，precheck_stage4 check① 会 FAIL 兜底",
        file=sys.stderr,
    )
    return html, False


def load_scaffold() -> dict:
    if not SCAFFOLD.exists():
        print(f"[ERROR] scaffold.json 不存在：{SCAFFOLD}", file=sys.stderr)
        sys.exit(1)
    return json.loads(SCAFFOLD.read_text(encoding="utf-8"))


# ── outputs 手改保护 ─────────────────────────────────────────────────────────
#
# 风险：assemble.py 重跑时,会用 drafts/ 内容覆盖 outputs/ 的 FRAME / PROJ-CSS /
# FB FALLBACK / spec 模块段——若 PM 或产品总监在两次 assemble 之间手改了 outputs,
# 改动会被静默丢失。
#
# 防御：每次拼装结束写 sidecar fingerprint（sha256 + 时间戳），下次拼装前比对：
#   - sidecar 不存在 → 首次拼装,跳过
#   - hash 一致 → 安全覆盖
#   - hash 不一致 → ERROR + 三种修复建议（同步回 drafts / --force-overwrite / 删 sidecar）

def _fingerprint_path(product: str, mode: str) -> Path:
    return FINGERPRINT_DIR / f"{product}_{mode}.txt"


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_no_manual_drift(
    output_path: Path, product: str, mode: str, force: bool
) -> None:
    """比对 sidecar fingerprint ↔ 当前 outputs 文件 hash。
    不一致即视为两次 assemble 之间的手改,默认 ERROR；--force-overwrite 降级为 WARN。"""
    fp_path = _fingerprint_path(product, mode)
    if not fp_path.exists():
        return  # 首次拼装,无前次记录
    if not output_path.exists():
        return  # outputs 已被删,后续 assemble 流程自身会再做存在性校验

    expected_lines = fp_path.read_text(encoding="utf-8").strip().splitlines()
    if not expected_lines:
        return  # sidecar 文件存在但内容损坏,跳过比对
    expected_sha = expected_lines[0].strip()
    actual_sha = _file_sha256(output_path)
    if actual_sha == expected_sha:
        return

    if force:
        zones = "FRAME / PROJ-CSS / FB FALLBACK" + (" / spec 模块段" if mode == "spec" else "")
        print(
            f"[WARN] {output_path.name} 自上次 assemble.py {mode} 后被手改,"
            f"--force-overwrite 将覆盖以下刷新区内的手改：{zones}\n"
            f"       （B2 SSOT #80：覆盖前已自动备份,见上方 [BACKUP] 行 / "
            f"{BACKUP_DIR.name}/；若手改属真源内容请改回 drafts 再重跑）\n"
            f"       上次拼装 sha256 = {expected_sha[:16]}... / 当前 = {actual_sha[:16]}...",
            file=sys.stderr,
        )
        return

    last_at = expected_lines[1].strip() if len(expected_lines) > 1 else "(未知)"
    print(
        f"[ERROR] {output_path.name} 自上次 assemble.py {mode} 后被改动,重跑会"
        f"覆盖 FRAME / PROJ-CSS / FB FALLBACK"
        f"{' / spec 模块段' if mode == 'spec' else ''} 等刷新区内的手改：\n"
        f"  上次拼装结束 sha256 = {expected_sha}\n"
        f"  上次拼装时间        = {last_at}\n"
        f"  当前文件      sha256 = {actual_sha}\n"
        f"\n"
        f"可能原因：\n"
        f"  · PM/产品总监在 outputs 上做了 typo / 文案 / CSS 微调\n"
        f"  · 备份恢复 / git checkout / 外部工具改写了文件\n"
        f"\n"
        f"可选处理：\n"
        f"  (a) 把手改同步回 process_record/drafts/ 对应草稿后重跑（最安全；改动随下次 assemble 自动重现）\n"
        f"  (b) 加 --force-overwrite 强制覆盖（破坏性；先 git diff outputs/ 确认丢失内容可接受）：\n"
        f"      python pm-workflow/scripts/assemble.py {mode} --force-overwrite\n"
        f"  (c) 若仅改了「保留区」（spec Foundation S0/S0.5/S1 / prd 产品规格区 / 导航等\n"
        f"      不在 FRAME / PROJ-CSS / FB FALLBACK 标记内的内容）,加 --force-overwrite 安全：\n"
        f"      保留区会被 assemble 原样保留,仅刷新区内容会被 drafts 覆盖\n"
        f"  (d) 改动已无价值,删 fingerprint 后重跑：\n"
        f"      rm {fp_path}\n",
        file=sys.stderr,
    )
    sys.exit(1)


def _save_fingerprint(output_path: Path, product: str, mode: str) -> None:
    """assemble 结束时记录 outputs 文件 hash + 时间戳,供下次重跑比对。"""
    fp_path = _fingerprint_path(product, mode)
    fp_path.parent.mkdir(parents=True, exist_ok=True)
    digest = _file_sha256(output_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fp_path.write_text(f"{digest}\n{timestamp}\n", encoding="utf-8")


def _prune_old_backups(keep: int = 20) -> None:
    """保留策略：BACKUP_DIR 只留最近 keep 个备份目录（UTC 时间戳命名可字典序排序），
    防高频 force 操作磁盘无限累积。gen_scaffold.py 有同款 helper（两脚本互不 import）。"""
    if not BACKUP_DIR.exists():
        return
    dirs = sorted(d for d in BACKUP_DIR.iterdir() if d.is_dir())
    for old in dirs[:-keep] if len(dirs) > keep else []:
        import shutil
        shutil.rmtree(old, ignore_errors=True)


def _backup_output_before_overwrite(output_path: Path, mode: str):
    """B1（SSOT #80）：--force-overwrite 覆盖 outputs 前自动快照当前文件,
    防破坏性重装把 PM 积累冲掉后找不回。返回备份路径(无则 None)。"""
    if not output_path.exists():
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest_dir = BACKUP_DIR / f"{ts}_assemble_{mode}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / output_path.name
    dest.write_bytes(output_path.read_bytes())
    print(f"[BACKUP] 覆盖前已快照 {output_path.name} → {dest}", file=sys.stderr)
    _prune_old_backups()
    return dest


# ── prd_template.html 升级检测（issue 2026-05-05_2243 复盘 T1-1）─────────────
# Why：bujue-quotation-tool 历史多次出现"主模板 CSS / JS 升级 → outputs/prd 未同步"
# 漂移。本组 helper 把 prd_template.html 当 SSOT 真源,outputs/prd 头部嵌入
# 嵌入时点的 template hash 注释；下次拼装时比对,不一致 → WARN 提示主模板已升级,
# 让编排器/PM 主动核查产物草稿是否需要适配新模板（不阻断,assemble 仍重新拼装）。
import re as _re_module


def _compute_template_hash() -> str | None:
    """计算 prd_template.html 当前 sha256。模板缺失返回 None（兜底,不阻断拼装）。"""
    if not PRD_TEMPLATE_PATH.exists():
        return None
    return hashlib.sha256(PRD_TEMPLATE_PATH.read_bytes()).hexdigest()


def _extract_template_hash_from_output(html: str) -> str | None:
    """从 outputs/prd HTML 中提取嵌入的 template-hash 注释值。无注释返回 None。"""
    m = _re_module.search(TEMPLATE_HASH_COMMENT_PATTERN, html)
    return m.group(1) if m else None


def _check_template_drift(prd_path: Path, current_template_hash: str | None) -> None:
    """比对 outputs/prd 中嵌入的 template-hash ↔ 当前 prd_template.html hash。
    不一致 → WARN（不阻断,因为 assemble 后 outputs 会用新 template 重生）；
    无嵌入注释 → 静默 backfill（旧产物兼容,本次拼装会写入注释）。"""
    if current_template_hash is None:
        return  # 模板缺失,跳过
    if not prd_path.exists():
        return  # 产物已删,跳过
    html = prd_path.read_text(encoding="utf-8")
    embedded = _extract_template_hash_from_output(html)
    if embedded is None:
        # 旧产物无 template-hash 注释,本次拼装会写入;静默
        return
    if embedded == current_template_hash:
        return  # 一致,无漂移
    print(
        f"[WARN] prd_template.html 自上次 assemble 以来已升级（template hash 漂移）：\n"
        f"       上次嵌入 hash = {embedded[:16]}...\n"
        f"       当前模板 hash = {current_template_hash[:16]}...\n"
        f"  本次拼装会用新 template 重生 outputs。请核查所有 PM 草稿是否仍适配\n"
        f"  新模板的 CSS/JS/规则,必要时通过 /retro 启动产物同步整改。\n"
        f"  详见 issue_2026-05-05_2243_review.md 根因 1（工作流升级 → 产物同步）。\n",
        file=sys.stderr,
    )


def _inject_template_hash(html: str, template_hash: str | None) -> str:
    """在 outputs/prd HTML 头部嵌入 / 更新 template-hash 注释。
    位置：紧跟 <!DOCTYPE html> 之后（若有）或文件起始。"""
    if template_hash is None:
        return html  # 模板缺失,不嵌入
    new_comment = TEMPLATE_HASH_COMMENT_FORMAT.format(sha=template_hash)
    # 已存在 → 替换
    if _re_module.search(TEMPLATE_HASH_COMMENT_PATTERN, html):
        return _re_module.sub(TEMPLATE_HASH_COMMENT_PATTERN, new_comment, html, count=1)
    # 不存在 → 在 <!DOCTYPE html> 后插入；无 DOCTYPE 则插在文件起始
    doctype_re = _re_module.compile(r"(<!DOCTYPE\s+html[^>]*>)", _re_module.IGNORECASE)
    m = doctype_re.search(html)
    if m:
        return html[:m.end()] + "\n" + new_comment + html[m.end():]
    return new_comment + "\n" + html


def check_drafts(modules: list, prefix: str, suffix: str) -> list[Path]:
    """验证所有模块草稿就绪，返回按顺序排列的草稿路径列表。

    双向检测（防 drafts 数据漂移）：
      - 单向：scaffold modules 中的每个 id 都应有对应草稿（缺失则 ERROR）
      - 反向：drafts 目录中不应有 scaffold 中无 id 对应的孤立草稿（变更后未清理）
    模块 ID 重排（M02 ↔ M03 swap）场景下，反向检测会捕获语义错配——
    旧 spec_M02 是旧 M02 内容但新 scaffold 中 M02 已是别的模块，
    若放任拼装会让幽灵内容渗入产物。
    """
    missing = []
    paths = []
    for mod in modules:
        p = DRAFTS_DIR / f"{prefix}{mod['id']}_draft.{suffix}"
        if not p.exists():
            missing.append(str(p))
        paths.append(p)
    if missing:
        print(f"[ERROR] 以下草稿文件缺失：", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        sys.exit(1)

    # 反向检测：drafts 目录中孤立草稿（scaffold 中已无对应 id）
    expected_names = {f"{prefix}{mod['id']}_draft.{suffix}" for mod in modules}
    existing_names = {f.name for f in DRAFTS_DIR.glob(f"{prefix}M*_draft.{suffix}")}
    orphans = sorted(existing_names - expected_names)
    if orphans:
        print(
            f"[ERROR] drafts 目录含 {len(orphans)} 个孤立草稿"
            f"（scaffold 中已无对应模块），拼装中止以防数据漂移：",
            file=sys.stderr,
        )
        for o in orphans:
            print(f"  - {o}", file=sys.stderr)
        print(
            "  → 重跑 `python pm-workflow/scripts/gen_scaffold.py --prune-orphans` 清理；"
            "或手动 rm 后重试",
            file=sys.stderr,
        )
        sys.exit(1)

    return paths


# ── spec.md 拼装 ──────────────────────────────────────────────────────────────

SPEC_MODULES_START = "<!-- [SPEC-MODULES-START] auto-marker by assemble.py -->"
SPEC_MODULES_END = "<!-- [SPEC-MODULES-END] auto-marker by assemble.py -->"

# SPEC_FOOTER 变更记录段说明（仅注释留痕，不渲染进下游 spec.md 输出 —— 避免内部过程
# meta 文字污染下游阅读）：
#   ① 变更记录表语义（仅记需求变更：v0.1 阶段 4 启动 / v1.0 首次终审 / vX.0 changeRequest
#      主版本三触发点；PM 整改 / polish / 内部循环不入表）真源 = CLAUDE.md G-02 + nextStage.md 步骤 0。
#   ② 「变更内容」字段强制分点格式（摘要短句 ≤50 字；每 bullet ≤30 字；≥2 bullet；禁大段连贯文字 /
#      禁嵌套括号 >2 层）真源 = PM Agent §5.0 + nextStage.md 场景 A/B。此处不再渲染该规则进输出。
SPEC_FOOTER = """\
{end_marker}

---

{foundation_sections}

---

## 变更记录

| 版本 | 变更内容 | 变更原因 | 变更人 | 审核人 | 日期 |
|------|---------|---------|--------|--------|------|
{changelog_rows}

---

## 非阻塞性问题清单

（待 PM 自审后补充）
"""


_SSOT48_VERSION_RE = re.compile(r"^v(0\.1|1\.0|[2-9]\.0|[1-9][0-9]+\.0)$")

# SSOT #61 §S3/§S4/§S5 派生注入（与 SSOT #41 extract_archetype_skeletons 同型，
# 2026-06-02 治本——Foundation 在 spec_foundation_draft.md 末尾撰写一份，assemble
# 派生注入 spec.md，避免 PM 写两遍 / 误以为 assemble 自动拼接）
_FOUNDATION_SECTION_RE = re.compile(
    r'^(## S[3-5][^\n]*\n.*?)(?=\n## |\Z)', re.MULTILINE | re.DOTALL
)
_FOUNDATION_SECTION_TITLES = {
    "S3": "S3 全局交互规则",
    "S4": "S4 组件状态库",
    "S5": "S5 异常场景全景",
}


def extract_foundation_sections() -> dict[str, str]:
    """SSOT #61 派生注入：从 spec_foundation_draft.md 提取 ## S3/## S4/## S5 段。

    Foundation Agent 子阶段二在 spec_foundation_draft.md 末尾撰写一份 §S3/§S4/§S5；
    assemble 派生注入到 spec.md（避免 PM 在两处维护，与 SSOT #41 范式骨架同模式）。

    返回 {"S3": "## S3 全局交互规则\\n...", "S4": ..., "S5": ...}（缺失键 → 不入 dict，
    优雅降级；build_foundation_sections_md 补占位）。
    """
    draft = DRAFTS_DIR / "spec_foundation_draft.md"
    if not draft.exists():
        return {}
    text = draft.read_text(encoding="utf-8")
    sections = {}
    for m in _FOUNDATION_SECTION_RE.finditer(text):
        full = m.group(1).strip()
        first_line = full.split('\n', 1)[0]  # 例 "## S3 全局交互规则"
        # 提取 S3/S4/S5 锚 id
        tokens = first_line.replace('##', '').strip().split()
        if tokens and tokens[0] in ("S3", "S4", "S5"):
            sections[tokens[0]] = full
    return sections


def build_foundation_sections_md() -> str:
    """SSOT #61：拼接 §S3/§S4/§S5 三段 markdown 供 SPEC_FOOTER 注入。

    Foundation 未填某段 → 占位说明（precheck WARN 兜底）；
    全无 → 三段占位均输出，避免 spec 末尾缺失（PM 上报 P0-1 治本）。
    """
    sections = extract_foundation_sections()
    parts = []
    for sid in ("S3", "S4", "S5"):
        if sid in sections:
            parts.append(sections[sid])
        else:
            parts.append(
                f"## {_FOUNDATION_SECTION_TITLES[sid]}\n\n"
                f"_[Foundation 子阶段二待填，详 `proto_spec_md.md §"
                f"{'五' if sid == 'S3' else ('六' if sid == 'S4' else '七')}` 模板]_"
            )
    return "\n\n---\n\n".join(parts)



# ── SSOT #67/#68 派生层（A-05 信息架构重组 + C-4 业务契约派生）────────────────
#
# 派生链路（与 SSOT #41 / #61 同模式）：
#   spec.md S2.MXX.4B/.5B/.7 段 + F-xxx 节「主页面」字段（真源）
#     → assemble.extract_business_rules / extract_data_scale / extract_gherkin /
#         extract_main_page (5 函数)
#     → inject_c4_into_interaction_card / build_function_overview_index (2 注入函数)
#     → outputs/prd_*_latest.html interaction-card C-4 子区块 + A-05 索引表（派生）
#
# 优雅降级（与 SSOT #61 同模式）：spec 缺 .4B / 缺 .5B / 缺主页面字段 → assemble 不报错，
# 注入占位说明或跳过；FAIL/ERROR 由 Commit 3 precheck（S4 系列，详 SSOT #67/#68）兜底。

# .4B / .5B 段头匹配（NB-WE-01：后缀模式 .4B/.5B 与 .4/.5 不撞号；
# 与 ssot_anchors #68 + proto_spec_md §三.5 真源字面一致）
_SECTION_4B_RE_TMPL = r"^## S2\.{mid}\.4B[ \t]+业务规则.*?(?=\n## |\Z)"
_SECTION_5B_RE_TMPL = r"^## S2\.{mid}\.5B[ \t]+数据规模.*?(?=\n## |\Z)"
_SECTION_7_RE_TMPL = r"^## S2\.{mid}\.7[ \t].*?(?=\n## |\Z)"

# 按页面分组锚：#### P[XX] 页面名（详 proto_spec_md.md §三.5 .4B / .5B 格式）
_PAGE_GROUP_RE = re.compile(r"^####[ \t]+(P\d+)[ \t]+([^\n]+)", re.MULTILINE)

# Gherkin 状态锚（双格式适配，与 check_spec_gherkin_completeness S4-45 同源）：
# 旧格式：**P01-default** / 新格式：**S01：default(...)**
_STATE_ANCHOR_RE = re.compile(
    r"^\*\*(P\d+-[\w-]+|S\d+[：:][^\*\n]{1,100})\*\*", re.MULTILINE
)
_GHERKIN_FENCE_RE = re.compile(r"```gherkin\b(.*?)```", re.DOTALL)

# F-xxx 节锚 + 主页面字段（详 proto_spec_md.md §三.5 F-xxx 4 必填字段）
_F_SECTION_RE = re.compile(
    r"^####[ \t]+(F-\d+)[：:][ \t]*([^\n]+)", re.MULTILINE
)
# 主页面字段：「主页面：P-XX」or「**主页面**：P-XX」（兼容 PM 写法）
_MAIN_PAGE_FIELD_RE = re.compile(
    r"(?:\*\*)?主页面(?:\*\*)?[：:]\s*(P-?\d+)"
)
# F-xxx 节内优先级字段
_PRIORITY_FIELD_RE = re.compile(
    r"(?:\*\*)?优先级(?:\*\*)?[：:]\s*(P[012])"
)

# A-05 节匹配（PRD 主体「功能需求规格」section 旧 article 形态 + 新「功能索引」表格）
# SSOT #67：assemble 在 A-05 位置注入 4 列「功能索引」表格替换原 F-xxx article 形态
_A05_SECTION_RE = re.compile(
    r'(<section\s+id\s*=\s*"spec-feature"[^>]*>)(.*?)(</section>)',
    re.DOTALL | re.IGNORECASE,
)
_FUNCTION_INDEX_PLACEHOLDER = "<!-- [FUNCTION-INDEX] -->"
_FUNCTION_INDEX_START = "<!-- [FUNCTION-INDEX-START] auto-injected by assemble.py -->"
_FUNCTION_INDEX_END = "<!-- [FUNCTION-INDEX-END] -->"


def _extract_module_section(spec_text: str, mid: str, section_re_tmpl: str) -> str:
    """从 spec.md 提取指定模块的某子段全文（如 `## S2.M01.4B 业务规则`）。

    `mid` 形如 "M01"。返回段内全文（含段头行），未找到返回 ""。
    """
    pattern = re.compile(
        section_re_tmpl.format(mid=re.escape(mid)),
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(spec_text)
    return m.group(0) if m else ""


def _extract_page_group(section_text: str, pid: str) -> str:
    """从段内按 `#### P[XX] 页面名` 锚分组提取指定页面的内容（不含锚行本身）。

    `pid` 形如 "P01"。返回该页面下到下一个 `####` 或段末的内容文字，未找到返回 ""。
    """
    if not section_text:
        return ""
    anchors = list(_PAGE_GROUP_RE.finditer(section_text))
    for i, m in enumerate(anchors):
        if m.group(1) == pid:
            start = m.end()
            end = anchors[i + 1].start() if i + 1 < len(anchors) else len(section_text)
            return section_text[start:end].strip()
    return ""


def extract_business_rules(spec_text: str, mid: str, pid: str) -> str:
    """SSOT #68：从 spec.md `## S2.M[XX].4B 业务规则` 段提取指定页面的业务规则列表。

    真源字面（NB-WE-01）：`## S2.M[XX].4B 业务规则`（**非** `.4`，与 SSOT #61
    .4 数据字段绑定不撞号；proto_spec_md.md §三.5 真源已锁）。

    返回该页面下的 markdown 列表文本（每条 `- {规则}`），无对应内容返回 ""
    （由 inject_c4_into_interaction_card 优雅降级注入占位）。

    优雅降级（SSOT #67/#68 派生层纪律，与 SSOT #61 同模式）：
    - 段头缺失 → ""（precheck（SSOT #68 .4B 段头校验）WARN 兜底）
    - 页面分组缺失 → ""（precheck（SSOT #68 .4B 段头校验）WARN 兜底）
    """
    section_text = _extract_module_section(spec_text, mid, _SECTION_4B_RE_TMPL)
    return _extract_page_group(section_text, pid)


def extract_data_scale(spec_text: str, mid: str, pid: str) -> str:
    """SSOT #68：从 spec.md `## S2.M[XX].5B 数据规模` 段提取指定页面的数据规模三维度。

    真源字面（NB-WE-01）：`## S2.M[XX].5B 数据规模`（**非** `.5`，与 SSOT #61
    .5 跨模块跳转引用不撞号；proto_spec_md.md §三.5 真源已锁）。

    返回该页面下的 markdown 文本（三维度 bullet：单用户数据量 / 单次返回量 /
    操作频率），无对应内容返回 ""。优雅降级同 extract_business_rules。
    """
    section_text = _extract_module_section(spec_text, mid, _SECTION_5B_RE_TMPL)
    return _extract_page_group(section_text, pid)


def extract_gherkin(spec_text: str, mid: str, pid: str, state_name: str) -> str:
    """SSOT #68：从 spec.md `## S2.M[XX].7 状态清单与验收标准` 段提取指定状态的
    Gherkin 验收契约（围栏内文本）。

    复用 check_spec_gherkin_completeness（S4-45）同源 regex：状态锚双格式适配——
    旧格式 `**P01-default**` / 新格式 `**S01：default(...)**`。

    `state_name` 是 scaffold.json `states[].name`（如 "default" / "loading" /
    "empty"）；本函数在 .7 段内按状态锚匹配，再提取该状态下的 ```gherkin 围栏。

    返回围栏内 Given/When/Then 文本（不含围栏标记本身），无匹配返回 ""。
    优雅降级：.7 段缺 / 状态锚无匹配 / 围栏缺失 → ""（precheck S4-45 兜底）。
    """
    section_text = _extract_module_section(spec_text, mid, _SECTION_7_RE_TMPL)
    if not section_text:
        return ""
    state_anchors = list(_STATE_ANCHOR_RE.finditer(section_text))
    # pid 归一化（与 _build_module_page_to_main_lookup 同型）
    pid_canonical = pid if pid.startswith("P") else f"P{pid}"
    pid_num = pid_canonical[1:].lstrip("-").lstrip("0") or "0"
    pid_forms = {pid_canonical, f"P{pid_num}"}
    for i, m in enumerate(state_anchors):
        anchor_label = m.group(1)
        # 双格式匹配：
        # 旧格式 `P01-default` / `P1-default` → anchor 须以 pid_form-state_name 开头
        # 新格式 `S01：default(...)` / `S01:default` → anchor 含 state_name 且不含 pid
        # 严格策略：pid_form-state_name 字面匹配（避免 "default" 字符串误匹配相邻页）
        matched = False
        for pf in pid_forms:
            if anchor_label.startswith(f"{pf}-{state_name}"):
                matched = True
                break
        # 新格式：S01：state_name (...)
        if not matched:
            if (
                f"：{state_name}" in anchor_label
                or f":{state_name}" in anchor_label
            ):
                matched = True
        if not matched:
            continue
        # 提取该状态条目下文（到下一个状态锚或段末）
        start = m.end()
        end = (
            state_anchors[i + 1].start()
            if i + 1 < len(state_anchors)
            else len(section_text)
        )
        sub_text = section_text[start:end]
        # 提取 ```gherkin``` 围栏内文本
        fence_m = _GHERKIN_FENCE_RE.search(sub_text)
        if fence_m:
            return fence_m.group(1).strip()
        return ""  # 状态锚命中但围栏缺
    return ""


def extract_main_page(spec_text: str, fid: str) -> tuple[str, str, str]:
    """SSOT #68：从 spec.md F-xxx 节内提取「主页面」字段。

    F-xxx 节锚：`#### F-001：{功能名}`（详 proto_spec_md.md §三.5 F-xxx 4 必填字段）。
    本函数提取：①优先级（P0/P1/P2）②主页面 ID（P-XX 形式）③功能名。

    返回 (priority, main_page_id, fname)；任一字段缺失对应位置为 ""。
    用于 build_function_overview_index 派生 A-05 4 列索引 + inject_c4_into_interaction_card
    判定主/副页面策略（主页面全量 C-4 / 副页面缩略）。

    优雅降级：F-xxx 节不存在 / 字段缺失 → 对应位置 ""（precheck（SSOT #68 主页面字段闭环校验）兜底）。
    """
    # F-xxx 节锚（向后扫到下一个 #### F-xxx 或文件末）
    pattern = re.compile(
        r"####[ \t]+" + re.escape(fid) + r"[：:][ \t]*([^\n]+)(.*?)(?=\n####[ \t]+F-|\Z)",
        re.DOTALL,
    )
    m = pattern.search(spec_text)
    if not m:
        return "", "", ""
    fname = m.group(1).strip()
    body = m.group(2)
    priority_m = _PRIORITY_FIELD_RE.search(body)
    main_page_m = _MAIN_PAGE_FIELD_RE.search(body)
    priority = priority_m.group(1) if priority_m else ""
    main_page_id = main_page_m.group(1) if main_page_m else ""
    return priority, main_page_id, fname


def _build_c4_content_html(
    business_rules_md: str,
    data_scale_md: str,
    gherkin_text: str,
) -> str:
    """SSOT #68：把 spec 派生的三段内容渲染为 PRD interaction-card C-4 子区块 HTML。

    优雅降级（与 SSOT #61 同模式）：任一段为空 → 注入「本帧无 {段名}」占位说明
    （precheck（SSOT #68 .4B/.5B 段头校验）WARN 兜底）。

    返回的 HTML 片段对齐 prd_expression_standard.md §四 区块 C C-4 schema（4 子标题）：
    业务契约 + 业务规则 (c4-business-rules) + 数据规模 (c4-data-scale) + 验收标准 (gherkin)。
    """
    import html as _html

    # C-4.A 业务规则：spec markdown bullet → <table>（# + 规则描述两列，议题 2A 表达统一）
    # thead 列名「规则描述」（非「业务规则」）— 避免与外层 .c4-sub-title「业务规则」字面重复
    # （子标题已承担分类语义，thead 内重述「业务规则」是冗余视觉噪音）。
    if business_rules_md.strip():
        rows = []
        for line in business_rules_md.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                rows.append(_html.escape(line[2:].strip()))
        if rows:
            # 序号包 <span class="tp-num"> — 与 C-3 触点交互表序号字面统一（普通文字 + mono 字体）
            tbody = "\n".join(
                f'<tr><td><span class="tp-num">{i + 1}</span></td><td>{txt}</td></tr>'
                for i, txt in enumerate(rows)
            )
            rules_html = (
                '<table class="c4-business-rules">\n'
                '<thead><tr><th>#</th><th>规则描述</th></tr></thead>\n'
                f'<tbody>\n{tbody}\n</tbody>\n'
                '</table>'
            )
        else:
            rules_html = (
                '<table class="c4-business-rules">\n'
                '<thead><tr><th>#</th><th>规则描述</th></tr></thead>\n'
                '<tbody><tr><td>—</td><td>（本帧无业务规则；详 spec.md §S2.MXX.4B）</td></tr></tbody>\n'
                '</table>'
            )
    else:
        rules_html = (
            '<table class="c4-business-rules">\n'
            '<thead><tr><th>#</th><th>规则描述</th></tr></thead>\n'
            '<tbody><tr><td>—</td><td>（本帧无业务规则；详 spec.md §S2.MXX.4B）</td></tr></tbody>\n'
            '</table>'
        )

    # C-4.B 数据规模：spec markdown bullet → <table>（维度 + 值两列，议题 2A 表达统一）
    # 维度提取：每个 bullet 优先视为「单维度（dim：val）」；仅在 bullet 无 dim：val
    # 模式时回退到「单行多维度（dim1：v1 / dim2：v2）」遗留启发式 — 议题 8
    # NB-WE-2A-R2-01 真因：值内含 ` / ` 多项列举（如 `销售典型 3 次/天/项目（A / B / C）`）
    # 被旧版 `line.split(" / ")` 先拆为 4 段 → 第 2-4 段无 ` / ` 后 dim 全失 → fallback
    # 单列「说明」（quotation-tool 51/113 fallback 真因 — private-domain 0/143 因
    # PM 值内未用 ` / ` 列举）。新启发式分两阶段：①先按 bullet 找 dim：val 锚；②命中
    # 即整 bullet 作单 pair（不再二次 split 值，值内 ` / ` 视为业务列举属正常文案）；
    # ③首段无 dim：val 才回退 split — 兼容罕见单行多 dim 写法。
    def _split_data_scale(line: str) -> list[tuple[str, str]]:
        """把数据规模 bullet 拆为 [(维度, 值), ...]。

        启发式升级（议题 8，2026-06-04）：
        - **主路径（单 dim 一行）**：bullet 以 `维度：值` 起首（首个 `：/:` 前是
          dim，后全为 val 含 ` / ` 列举） → [(dim, val)] 单元组（治
          NB-WE-2A-R2-01 假阳：值内 ` / ` 不再拆维度）
        - **回退路径（单行多 dim 遗留）**：bullet 不以 dim：val 起首（或起首段
          无冒号）→ 沿用旧 `line.split(" / ")` 多段启发式
        - **散文回退**：完全无冒号 → [("", line)] 单元组（precheck S4-XX WARN）

        典型形态：
        - 主路径：`单用户数据量：典型 N 个（场景 A / B / C）` → [("单用户数据量",
          "典型 N 个（场景 A / B / C）")]（值内 / 保留）
        - 回退：`dim1：v1 / dim2：v2 / dim3：v3` → 3 元组（旧形态）
        - 散文：`数据量较大` → [("", "数据量较大")]
        """
        line = line.strip()
        if not line:
            return []
        # 主路径：尝试以「整 bullet = 单 dim：val」解析（首个冒号锚 dim/val 边界）
        for sep in ("：", ":"):
            idx = line.find(sep)
            if idx > 0:
                dim_candidate = line[:idx].strip()
                # dim 候选必须是「短词 + 不含 ` / `」（含 ` / ` 表示 dim 段本身已含
                # 列举，应回退多 dim 启发式；空 dim 也回退）
                if dim_candidate and " / " not in dim_candidate and len(dim_candidate) <= 30:
                    val = line[idx + len(sep):].strip()
                    return [(dim_candidate, val)]
                break  # 首冒号 dim 无效 → 回退多 dim 启发式
        # 回退路径：单行多 dim 遗留启发式（与旧版语义一致）
        pairs: list[tuple[str, str]] = []
        for segment in line.split(" / "):
            segment = segment.strip()
            if not segment:
                continue
            for sep in ("：", ":"):
                if sep in segment:
                    dim, val = segment.split(sep, 1)
                    pairs.append((dim.strip(), val.strip()))
                    break
            else:
                pairs.append(("", segment))
        return pairs

    if data_scale_md.strip():
        all_pairs: list[tuple[str, str]] = []
        for line in data_scale_md.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                all_pairs.extend(_split_data_scale(line[2:].strip()))
        if all_pairs and all(dim for dim, _ in all_pairs):
            tbody = "\n".join(
                f"<tr><td>{_html.escape(dim)}</td><td>{_html.escape(val)}</td></tr>"
                for dim, val in all_pairs
            )
            scale_html = (
                '<table class="c4-data-scale">\n'
                '<thead><tr><th>维度</th><th>值</th></tr></thead>\n'
                f'<tbody>\n{tbody}\n</tbody>\n'
                '</table>'
            )
        elif all_pairs:
            # 回退：无明确维度（散文形式），用单列「说明」表格保留视觉一致
            tbody = "\n".join(
                f"<tr><td>{_html.escape(val)}</td></tr>" for _, val in all_pairs
            )
            scale_html = (
                '<table class="c4-data-scale">\n'
                '<thead><tr><th>说明</th></tr></thead>\n'
                f'<tbody>\n{tbody}\n</tbody>\n'
                '</table>'
            )
        else:
            scale_html = (
                '<table class="c4-data-scale">\n'
                '<thead><tr><th>维度</th><th>值</th></tr></thead>\n'
                '<tbody><tr><td>—</td><td>（本帧无数据规模；详 spec.md §S2.MXX.5B）</td></tr></tbody>\n'
                '</table>'
            )
    else:
        scale_html = (
            '<table class="c4-data-scale">\n'
            '<thead><tr><th>维度</th><th>值</th></tr></thead>\n'
            '<tbody><tr><td>—</td><td>（本帧无数据规模；详 spec.md §S2.MXX.5B）</td></tr></tbody>\n'
            '</table>'
        )

    # C-4.C 验收标准（Gherkin）：spec 围栏内文本 verbatim → <pre class="gherkin">
    if gherkin_text.strip():
        gherkin_html = f'<pre class="gherkin">{_html.escape(gherkin_text)}</pre>'
    else:
        gherkin_html = (
            '<pre class="gherkin">'
            "（本帧无验收标准；详 spec.md §S2.MXX.7）"
            "</pre>"
        )

    return (
        '<div class="data-sub-title">业务契约</div>\n'
        '<div class="c4-sub-title">业务规则</div>\n'
        f'{rules_html}\n'
        '<div class="c4-sub-title">数据规模</div>\n'
        f'{scale_html}\n'
        '<div class="c4-sub-title">验收标准</div>\n'
        f'{gherkin_html}'
    )


def _build_c4_cross_page_note(main_page_prd_id: str, main_page_label: str) -> str:
    """SSOT #68 副页面 C-4 缩略形态：跳转至主页面。

    `main_page_prd_id` 形如 `H-M01-P02-default`；`main_page_label` 形如 `P-02 主页面名`。
    对齐 prd_expression_standard.md §四 区块 C C-4 副页面缩略 schema。
    """
    import html as _html
    return (
        '<div class="data-sub-title">业务契约</div>\n'
        '<p class="c4-cross-page-note">本页业务契约详见主页面 '
        f'<a href="#" onclick="showSection(\'{_html.escape(main_page_prd_id)}\')">'
        f'{_html.escape(main_page_label)}</a></p>'
    )


def inject_c4_into_interaction_card(
    frame_html: str,
    c4_content: str,
    prd_id: str,
) -> str:
    """SSOT #68：把 C-4 子区块 HTML 注入到 frame_html 内 interaction-card 的 C-3 后。

    定位策略（与 prd_expression_standard.md §四 区块 C 顺序对齐）：
    - C-3「触点交互说明」是 interaction-card 最后一个原生子区块
    - C-4 插入位置：interaction-card 闭合 `</div>` 前（C-3 之后即 card 末尾）
    - 幂等：用 `<!-- [C4-START: prd_id] -->...<!-- [C4-END: prd_id] -->` 包裹

    无 interaction-card → 返回原 frame_html（优雅降级，precheck（SSOT #68 C-4 派生闭环校验）兜底）。
    """
    if not c4_content.strip():
        return frame_html

    c4_start = f"<!-- [C4-START: {prd_id}] auto-injected by assemble.py -->"
    c4_end = f"<!-- [C4-END: {prd_id}] -->"
    wrapped = f"{c4_start}\n{c4_content}\n{c4_end}"

    # 幂等：已存在 C4-START/END 包裹块 → 替换内容
    reentry_re = re.compile(
        re.escape(c4_start.rsplit(" -->", 1)[0])
        + r".*?-->"
        + r".*?"
        + re.escape(c4_end),
        re.DOTALL,
    )
    # 简化：通过完整 start 标签 + end 标签字面定位
    reentry_pattern = re.compile(
        r"<!--\s*\[C4-START:\s*" + re.escape(prd_id) + r"\][^>]*-->"
        + r".*?"
        + r"<!--\s*\[C4-END:\s*" + re.escape(prd_id) + r"\]\s*-->",
        re.DOTALL,
    )
    if reentry_pattern.search(frame_html):
        return reentry_pattern.sub(wrapped, frame_html, count=1)

    # 首次注入：找 interaction-card 闭合标签
    # interaction-card 是 `<div class="interaction-card">...</div>` 形态
    # 注入位置：interaction-card 内最后一个 `</div>` 前
    interaction_card_re = re.compile(
        r'(<div\s+class\s*=\s*"interaction-card"[^>]*>)(.*?)(</div>\s*(?=<!--\s*\[/FRAME|</section|$))',
        re.DOTALL,
    )
    m = interaction_card_re.search(frame_html)
    if not m:
        return frame_html  # 无 interaction-card，优雅降级
    head, body, tail = m.group(1), m.group(2), m.group(3)
    new_card = f"{head}{body.rstrip()}\n  {wrapped}\n{tail}"
    return frame_html[:m.start()] + new_card + frame_html[m.end():]


def build_function_overview_index(spec_text: str) -> str:
    """SSOT #67：从 spec.md F-xxx 节派生 A-05「功能索引」4 列 HTML 表格。

    4 列 schema（详 prd_expression_standard.md §三 A-05）：
    编号 / 功能名 / 优先级 / 主页面跳转

    主页面 ID 解析（SSOT #68）：F-xxx 节内「主页面：P-XX」字段 → 对应模块的
    `H-M[XX]-P[YY]-default` prd_id（首状态）。
    优雅降级（precheck（SSOT #67 A-索引完整性校验）WARN 兜底）：
    - F-xxx 节缺失 → 输出空表（仅表头）
    - 主页面字段缺失 → 跳转列填「—」
    - 主页面 ID 无法解析到 prd_id → 跳转列填字面（不带 onclick）
    """
    import html as _html

    rows = []
    for f_match in _F_SECTION_RE.finditer(spec_text):
        fid = f_match.group(1)
        fname = f_match.group(2).strip()
        priority, main_page_id, _ = extract_main_page(spec_text, fid)

        # 主页面跳转列
        if main_page_id:
            jump_html = f'<a href="#" onclick="alert(\'主页面 ID 解析需 scaffold 上下文，参 A-05 派生说明\');return false;">{_html.escape(main_page_id)}</a>'
        else:
            jump_html = "—"

        # 优先级 tag
        if priority:
            priority_html = f'<span class="priority-tag">{_html.escape(priority)}</span>'
        else:
            priority_html = "—"

        rows.append(
            f"        <tr>\n"
            f"          <td>{_html.escape(fid)}</td>\n"
            f"          <td>{_html.escape(fname)}</td>\n"
            f"          <td>{priority_html}</td>\n"
            f"          <td>{jump_html}</td>\n"
            f"        </tr>"
        )

    if not rows:
        rows_html = (
            '        <tr><td colspan="4" style="color:var(--fb-text-hint);'
            'font-size:12px;text-align:center;">'
            "（spec.md 无 F-xxx 节；详 proto_spec_md.md §三.3 功能需求规格 规范）"
            "</td></tr>"
        )
    else:
        rows_html = "\n".join(rows)

    return (
        '    <table class="spec-table full-width">\n'
        "      <thead><tr><th>编号</th><th>功能名</th>"
        "<th>优先级</th><th>主页面</th></tr></thead>\n"
        f"      <tbody>\n{rows_html}\n      </tbody>\n"
        "    </table>"
    )


def _pid_forms(pid: str) -> set[str]:
    """SSOT #67 P-XX 多形态归一化（议题 1 治本，2026-06-04）：

    把任意 P-XX 写法（如 `P01` / `P-01` / `P-1` / `P1` / `P001` / `P-001` /
    `P-002` 等）展开成等价形态集合，供 page_to_prd_id 字典登记 / 查询同时使用，
    确保 scaffold `P01` ↔ spec.md `P-002` 等不同位宽 / 是否带 dash 的写法
    都能落到同一映射项，避免 A-索引超链接 fallback 触发（输出纯文本无 <a>）。

    形态集合包括：
    - 原始形态（去前缀 P / P-）的数字部分（含/不含前导零的两种归一）
    - 与「PXX」「P-XX」「PXXX」「P-XXX」（最多 3 位前导零）字面拼接

    用于 build_function_overview_index_with_jump（A-索引派生）+
    build_subpage_main_page_lookup（C-4 副页面派生）共享。
    """
    if not pid:
        return set()
    # 提取数字部分
    raw = pid[1:] if pid.startswith("P") else pid
    num_part = raw.lstrip("-")
    if not num_part.isdigit():
        return {pid}
    num_int = int(num_part)
    num_stripped = str(num_int)               # 去前导零（如 "001" → "1"）
    num_2digit = f"{num_int:02d}"             # 2 位前导零（如 1 → "01"）
    num_3digit = f"{num_int:03d}"             # 3 位前导零（如 1 → "001"）
    return {
        f"P{num_stripped}",                   # P1
        f"P-{num_stripped}",                  # P-1
        f"P{num_2digit}",                     # P01
        f"P-{num_2digit}",                    # P-01
        f"P{num_3digit}",                     # P001
        f"P-{num_3digit}",                    # P-001
    }


def build_function_overview_index_with_jump(
    spec_text: str, modules: list
) -> str:
    """SSOT #67：build_function_overview_index 的 jump-aware 变体。

    `modules` 来自 scaffold.json modules[]，用于把主页面 ID（P-XX）解析为
    prd_id（H-M[XX]-P[XX]-default）启用真 onclick 跳转。

    主页面 ID 解析策略：F-xxx 节「主页面：P-XX」字段值在所有 modules 的 pages
    中查首个匹配项 → 该页 states[0].prd_id（与 make_changelog_pages_clickable
    同源策略）。歧义 ID（多模块同 P-XX）取首个；优雅降级（跳转目标不可解析）填字面。
    """
    import html as _html

    # 构建 P-XX → prd_id 映射（首个匹配；多形态登记覆盖 PM 写法差异）
    page_to_prd_id: dict[str, str] = {}
    page_to_name: dict[str, str] = {}
    for mod in modules:
        for page in mod.get("pages", []) or []:
            pid = page.get("id", "")
            states = page.get("states", []) or []
            if not states:
                continue
            prd_id = states[0].get("prd_id", "")
            page_name = page.get("name", "")
            for form in _pid_forms(pid):
                page_to_prd_id[form] = prd_id
                page_to_name[form] = page_name

    # 议题 1 治本（SSOT #67）：F-xxx「涉及页面」字段作 fallback —
    # 当主页面字段缺失时，用涉及页面的第一项作 prd_id 解析源（同时输出 <a>）。
    involved_pages_re = re.compile(
        r"(?:\*\*)?涉及页面(?:\*\*)?[：:]\s*([P\-\d,，\s/、]+)"
    )
    page_id_re = re.compile(r"P-?\d+")

    rows = []
    for f_match in _F_SECTION_RE.finditer(spec_text):
        fid = f_match.group(1)
        fname = f_match.group(2).strip()
        priority, main_page_id, _ = extract_main_page(spec_text, fid)

        # 议题 1 治本：主页面缺失 → 从涉及页面取首项（fallback）
        if not main_page_id:
            body_pattern = re.compile(
                r"####[ \t]+" + re.escape(fid)
                + r"[：:][^\n]+(.*?)(?=\n####[ \t]+F-|\Z)",
                re.DOTALL,
            )
            body_m = body_pattern.search(spec_text)
            if body_m:
                involved_m = involved_pages_re.search(body_m.group(1))
                if involved_m:
                    involved_ids = page_id_re.findall(involved_m.group(1))
                    if involved_ids:
                        main_page_id = involved_ids[0]

        # 主页面跳转列
        if main_page_id:
            prd_id = ""
            page_name = ""
            for form in _pid_forms(main_page_id):
                if form in page_to_prd_id:
                    prd_id = page_to_prd_id[form]
                    page_name = page_to_name.get(form, "")
                    break
            if prd_id:
                label = f"{main_page_id} {page_name}".strip()
                jump_html = (
                    f'<a href="#" onclick="showSection(\'{_html.escape(prd_id)}\')">'
                    f"{_html.escape(label)}</a>"
                )
            else:
                # 解析不到 prd_id → 显示字面（优雅降级，precheck（SSOT #67 A-索引完整性校验）兜底）
                jump_html = _html.escape(main_page_id)
        else:
            jump_html = "—"

        # 优先级 tag
        if priority:
            priority_html = f'<span class="priority-tag">{_html.escape(priority)}</span>'
        else:
            priority_html = "—"

        rows.append(
            f"        <tr>\n"
            f"          <td>{_html.escape(fid)}</td>\n"
            f"          <td>{_html.escape(fname)}</td>\n"
            f"          <td>{priority_html}</td>\n"
            f"          <td>{jump_html}</td>\n"
            f"        </tr>"
        )

    if not rows:
        rows_html = (
            '        <tr><td colspan="4" style="color:var(--fb-text-hint);'
            'font-size:12px;text-align:center;">'
            "（spec.md 无 F-xxx 节；详 proto_spec_md.md §三.3 功能需求规格 规范）"
            "</td></tr>"
        )
    else:
        rows_html = "\n".join(rows)

    return (
        '    <table class="spec-table full-width">\n'
        "      <thead><tr><th>编号</th><th>功能名</th>"
        "<th>优先级</th><th>主页面</th></tr></thead>\n"
        f"      <tbody>\n{rows_html}\n      </tbody>\n"
        "    </table>"
    )


def inject_function_overview_index(html: str, index_table: str) -> tuple[str, bool]:
    """SSOT #67：注入 A-05「功能索引」4 列表格到 PRD spec-feature section。

    定位策略：
    - 首次注入：在 spec-feature section 内查 `[FUNCTION-INDEX]` 占位 → 替换
    - 重入幂等：[FUNCTION-INDEX-START]...[FUNCTION-INDEX-END] 包裹块 → 替换中间
    - 兼容旧 PRD（无占位 / 无 START/END）：清空 spec-feature section body + 注入

    返回 (新 html, 是否注入)。spec-feature section 不存在 → 优雅降级返回 (原, False)。

    4 联 bug fix（2026-06-04 P0 hot fix）：
    - Bug 1：强制把 spec-feature section 内 `<div class="spec-header">功能需求规格</div>`
      改为「功能索引」（L2 真源 `prd_expression_standard.md` §三 A-05 L656，
      header 字面 = `功能索引`；私域/business-circle/quotation-tool 3 仓 100% 命中）。
    - Bug 2：tbody 空时（spec.md 无 F-xxx 节）占位行字面升级，显式锚定 SSOT
      #67/#68，提示 PM 整改而非静默占位。
    - Bug 3：清除 spec-feature section 内残留的 `<article id="spec-F[0-9]+">`
      旧 Foundation 形态（私域 6 处 / quotation-tool 2 处实证；仅删 sub-article
      `spec-F` 前缀，不误删 prd 其他位置的顶层 `<article id="A-XX">`）。
    - Bug 4：见 precheck_stage4.check_prd_a05_removed 升级覆盖。
    - Bug 5（2026-06-04 P0 hot fix）：清除 SSOT #67 v1 老版 inject_function_overview_index
      首次注入时残留的孤立尾巴（私域主页 L3165~L3180 实证：1 个孤立 `</article>`
      + 2 个孤立 `<div class="spec-block">业务规则|验收标准</div>`，无配对 open）。
      根因：commit 3848b88 老版用 `(<div class="spec-body">)(.*?)(</div>)` 非贪婪
      命中首个 spec-block 的 `</div>` 误为 spec-body 关闭 → 吃掉 F-001 的 open
      `<article>` 但残留其内部 spec-block + 后续 `</article>`。Bug 3 regex 只能
      配对 open+close 的 article 块，无法清孤立残留 → 后果：layout 提前闭合，
      所有 frame 跑到 layout 外（与 body 平级 / 与 `<div class="layout">` 平级）。
    """
    # Bug 2：占位行字面升级（spec.md 无 F-xxx 节 → 显式锚 SSOT #67/#68 提示 PM 整改）
    bug2_placeholder_marker = (
        "（spec.md 无 F-xxx 节；详 proto_spec_md.md §三.3 功能需求规格 规范）"
    )
    if bug2_placeholder_marker in index_table:
        index_table = index_table.replace(
            bug2_placeholder_marker,
            "⚠️ spec.md 无 F-xxx 节；本产品未按 SSOT #67/#68 升级 F-xxx 体系 — "
            "PM 需补 F-001~F-xxx 节（详 proto_spec_md.md §三.5 F-xxx 4 必填字段 + "
            "prd_expression_standard.md §三 A-05 派生规范）",
        )

    wrapped = (
        f"{_FUNCTION_INDEX_START}\n"
        f"{index_table}\n"
        f"    {_FUNCTION_INDEX_END}"
    )

    # Bug 1 + Bug 3 联动修复：先在 spec-feature section 内做两件事
    #   ① spec-header 字面 `功能需求规格` → `功能索引`（强制对齐 L2 真源 §三 A-05）
    #   ② 清除 sub-article `<article id="spec-F[0-9]+">...</article>` 残留
    # 然后再做 FUNCTION-INDEX 注入。两件事均限定在 spec-feature section 范围内，
    # 避免误改其他章节同名 header / 顶层 article。
    def _clean_spec_feature_section(html_in: str) -> tuple[str, bool]:
        """限定在 spec-feature section 内做 Bug 1 header 字面修复 + Bug 3 sub-article 清除。"""
        m = _A05_SECTION_RE.search(html_in)
        if not m:
            return html_in, False
        head, body, tail = m.group(1), m.group(2), m.group(3)
        # Bug 1：header 字面替换（仅 section 内首个，且仅当字面为 `功能需求规格`）
        body = re.sub(
            r'(<div\s+class\s*=\s*"spec-header"\s*>)功能需求规格(</div>)',
            r"\1功能索引\2",
            body,
            count=1,
        )
        # Bug 3：删除 sub-article（id 以 spec-F 开头的 article 块，含其内容到对应 </article>）
        # 用粗粒度匹配（嵌套 article 罕见，足够清理 Foundation 历史残留）
        body = re.sub(
            r'<article\s+id\s*=\s*"spec-F[0-9]+"[^>]*>.*?</article>\s*',
            "",
            body,
            flags=re.DOTALL,
        )
        # Bug 5：清除 v1 老版残留的孤立尾巴 + 平衡修正
        # 仅清理 spec-feature section body 内的：
        #   ①孤立 `<div class="spec-block">...</div>` （F-001 老内容残留：业务规则 / 验收标准）
        #   ②孤立 `</article>` （无配对 <article>）
        #   ③div 收支不平衡（v1 buggy 注入吃掉 article 的 open 但留下额外 </div>）→ 从尾巴删孤立 </div>
        # 限定 body 内 + 严格 spec-block class 字面 → 不误伤其他 section
        body = re.sub(
            r'<div\s+class\s*=\s*"spec-block"\s*>.*?</div>\s*',
            "",
            body,
            flags=re.DOTALL,
        )
        body = re.sub(r'</article>\s*', "", body)
        # Bug 5c：div 收支平衡校正（v1 buggy 输入会致 close > open，从尾巴删多余 </div>）
        div_opens = len(re.findall(r'<div[\s>]', body))
        div_closes = len(re.findall(r'</div>', body))
        excess_closes = div_closes - div_opens
        for _ in range(max(0, excess_closes)):
            # 从尾巴反向删第一个孤立 </div>（保留前面的合法关闭，避免误删 spec-section/spec-body）
            body = re.sub(r'</div>\s*(?!.*</div>)', "", body, count=1, flags=re.DOTALL)
        new_section = head + body + tail
        return html_in[:m.start()] + new_section + html_in[m.end():], True

    html, _section_found = _clean_spec_feature_section(html)

    # 优先匹配重入幂等的 START/END 包裹块
    reentry_re = re.compile(
        re.escape(_FUNCTION_INDEX_START) + r".*?" + re.escape(_FUNCTION_INDEX_END),
        re.DOTALL,
    )
    if reentry_re.search(html):
        return reentry_re.sub(wrapped, html, count=1), True

    # 首次注入：找 [FUNCTION-INDEX] 占位
    if _FUNCTION_INDEX_PLACEHOLDER in html:
        return html.replace(_FUNCTION_INDEX_PLACEHOLDER, wrapped, 1), True

    # 兼容旧 PRD：spec-feature section 内可能含 Foundation 旧 article 形态
    # → 清空 spec-feature 的 spec-body 内容，注入索引表
    m = _A05_SECTION_RE.search(html)
    if not m:
        print(
            "[WARN] prd.html 无 spec-feature section（SSOT #67 A-05 注入跳过；"
            "precheck（SSOT #67 A-索引完整性校验）兜底）",
            file=sys.stderr,
        )
        return html, False
    head, body, tail = m.group(1), m.group(2), m.group(3)
    # 找 spec-body 替换其内容
    spec_body_re = re.compile(
        r'(<div\s+class\s*=\s*"spec-body"[^>]*>)(.*?)(</div>)',
        re.DOTALL,
    )
    body_m = spec_body_re.search(body)
    if body_m:
        new_body_content = f"\n            {wrapped}\n          "
        new_inner_body = (
            body[:body_m.start()]
            + body_m.group(1)
            + new_body_content
            + body_m.group(3)
            + body[body_m.end():]
        )
        new_section = head + new_inner_body + tail
        return html[:m.start()] + new_section + html[m.end():], True

    # 兜底：spec-body 无（旧骨架），整段替换 section body
    new_section = (
        head
        + '\n        <div class="spec-section">\n'
        + '          <div class="spec-header">功能索引</div>\n'
        + '          <div class="spec-body">\n'
        + f"            {wrapped}\n"
        + "          </div>\n"
        + "        </div>\n      "
        + tail
    )
    return html[:m.start()] + new_section + html[m.end():], True


def _build_module_page_to_main_lookup(
    spec_text: str, modules: list
) -> dict[tuple[str, str], tuple[str, str, str]]:
    """SSOT #68：构建 (mid, pid) → (主页面 prd_id, 主页面 P-XX label, 主页面名)
    查找表，用于 inject_c4 判定副页面跳转目标。

    逻辑：扫所有 F-xxx 节 → 取「涉及页面」+「主页面」字段 → 对每个涉及页面登记
    其主页面 prd_id（同模块内首个匹配的 P-XX）。如同一页面被多个 F-xxx 标为
    涉及但归属不同主页面，取首个匹配（罕见，precheck（SSOT #68 主页面字段闭环校验）WARN 兜底）。

    返回字典 (mid, pid) → (main_prd_id, main_page_label, main_page_name)；
    未被任何 F-xxx 标为涉及页面 / 主页面字段缺失的页 → 不入字典（C-4 注入回退到
    优雅降级路径：spec 直接派生本页 .4B/.5B/.7，作主页处理）。
    """
    # 构建 P-XX → prd_id / page_name 映射（同 build_function_overview_index_with_jump，
    # 议题 1 治本：用统一 _pid_forms 多形态归一，覆盖 spec.md 3 位前导零写法）
    page_to_prd_id: dict[str, dict] = {}  # P-XX 或 P02 → {mid, pid, prd_id, name}
    for mod in modules:
        mid = mod.get("id", "")
        for page in mod.get("pages", []) or []:
            pid = page.get("id", "")
            states = page.get("states", []) or []
            if not states:
                continue
            entry = {
                "mid": mid,
                "pid": pid,
                "prd_id": states[0].get("prd_id", ""),
                "name": page.get("name", ""),
            }
            for form in _pid_forms(pid):
                page_to_prd_id[form] = entry

    # 扫 F-xxx → 涉及页面 + 主页面
    involved_pages_re = re.compile(
        r"(?:\*\*)?涉及页面(?:\*\*)?[：:]\s*([P\-\d,，\s]+)"
    )
    page_id_re = re.compile(r"P-?\d+")

    lookup: dict[tuple[str, str], tuple[str, str, str]] = {}
    for f_match in _F_SECTION_RE.finditer(spec_text):
        fid = f_match.group(1)
        priority, main_page_label, _ = extract_main_page(spec_text, fid)
        if not main_page_label:
            continue
        main_entry = None
        for form in _pid_forms(main_page_label):
            if form in page_to_prd_id:
                main_entry = page_to_prd_id[form]
                break
        if not main_entry:
            continue
        main_prd_id = main_entry["prd_id"]
        main_label_full = f"{main_page_label} {main_entry['name']}".strip()

        # F-xxx 节 body
        body_pattern = re.compile(
            r"####[ \t]+" + re.escape(fid) + r"[：:][^\n]+(.*?)(?=\n####[ \t]+F-|\Z)",
            re.DOTALL,
        )
        body_m = body_pattern.search(spec_text)
        if not body_m:
            continue
        body = body_m.group(1)
        involved_m = involved_pages_re.search(body)
        if not involved_m:
            continue
        involved_ids = page_id_re.findall(involved_m.group(1))
        for involved_pid in involved_ids:
            # 多形态归一化匹配（_pid_forms 覆盖所有写法）
            entry = None
            for form in _pid_forms(involved_pid):
                if form in page_to_prd_id:
                    entry = page_to_prd_id[form]
                    break
            if not entry:
                continue
            key = (entry["mid"], entry["pid"])
            if key in lookup:
                continue  # 取首个匹配
            # 主页面自身不在副页面表（避免主页面被回填为副页面缩略）
            if entry["prd_id"] == main_prd_id:
                continue
            lookup[key] = (main_prd_id, main_label_full, main_entry["name"])
    return lookup


def inject_c4_for_module(
    frame_html: str,
    spec_text: str,
    mid: str,
    pid: str,
    state_name: str,
    prd_id: str,
    secondary_lookup: dict[tuple[str, str], tuple[str, str, str]],
) -> str:
    """SSOT #68 派生总入口：决定本帧 C-4 注入策略（主页面全量 / 副页面缩略），
    并执行注入。

    判定（SSOT #68 多页 F 注入策略 - 选项 α）：
    - (mid, pid) 在 secondary_lookup → 副页面，注入跳转链接（缩略形态）
    - 否则 → 主页面，从 spec 派生 .4B/.5B/.7 全量内容注入
    - 派生为空（spec 缺段 / 缺页面分组）→ 仍注入占位 C-4（保持 schema 完整）
    """
    key = (mid, pid)
    if key in secondary_lookup:
        main_prd_id, main_label, _ = secondary_lookup[key]
        c4_content = _build_c4_cross_page_note(main_prd_id, main_label)
    else:
        business_rules = extract_business_rules(spec_text, mid, pid)
        data_scale = extract_data_scale(spec_text, mid, pid)
        gherkin = extract_gherkin(spec_text, mid, pid, state_name)
        c4_content = _build_c4_content_html(business_rules, data_scale, gherkin)
    return inject_c4_into_interaction_card(frame_html, c4_content, prd_id)


def _validate_changelog_ssot48(changelog: list) -> list[str]:
    """SSOT #48 合规校验：版本号仅允许 v0.1 / v1.0 / vN.0 (N≥2)。

    Returns: 违规版本号清单（空 = 全合规）
    SSOT #48 SemVer 规则：阶段 4 仅 3 种对外可见版本变更触发点
      ①v0.1 启动 ②v0.1→v1.0 首次终审 ③v1.0 后 /changeRequest → vX.0 主版本

    历史遗留场景（如 v0.1 期间填的 v1.1/v1.2/v1.6 等开发态内部迭代）→ 违反 SSOT #48。
    """
    violations = []
    for e in changelog:
        version = e.get("version", "")
        if not _SSOT48_VERSION_RE.match(version):
            violations.append(version)
    return violations


def _build_spec_changelog_rows(changelog: list, today_iso: str) -> str:
    """生成 spec.md 变更记录表 markdown 行（与 gen_scaffold.build_changelog_page 同源消费 scaffold.json["changelog"]）。

    G-02 [MUST] 6 列对齐 prd doc-changelog（NB-CHANGELOG-SCAFFOLD-DERIVATION-MISMATCH
    治本，2026-06-02）：版本 / 变更内容 / 变更原因 / 变更人 / 审核人 / 日期。

    向后兼容 + SSOT #48 防御（2026-06-02 下游 PM 反馈第 2 轮发现 quotation-tool
    历史 scaffold.json["changelog"] 含 v1.0-v2.0 9 条开发态散文违反 SSOT #48 SemVer）：
    - changelog 为空 → fallback 默认 v0.1 初始行（today_iso 占位日期）
    - changelog 含 SSOT #48 违规版本号 → fallback + stderr 警告（不污染 spec）
    - changelog 全合规 → 正常消费数组生成 6 列行
    """
    if not changelog:
        # Fallback：scaffold.json 无 changelog 时的初始 v0.1 行
        return (
            "| v0.1 | 阶段 4 启动（未交付态）：<br>- gen_scaffold 初次生成"
            "<br>- spec/prd 骨架就位 | 新需求启动 | PM Agent |  | "
            f"{today_iso} |"
        )
    # SSOT #48 防御：违规版本号 → fallback 不污染 spec
    violations = _validate_changelog_ssot48(changelog)
    if violations:
        print(
            f"  [!] scaffold.json[\"changelog\"] 含 {len(violations)} 条违反 SSOT #48 "
            f"SemVer 版本号: {violations}（仅允许 v0.1/v1.0/vN.0 N≥2）— fallback 到默认"
            f" v0.1 行；请清理 scaffold.json[\"changelog\"] 后重 assemble。",
            file=sys.stderr,
        )
        return (
            "| v0.1 | 阶段 4 启动（未交付态）：<br>- gen_scaffold 初次生成"
            "<br>- spec/prd 骨架就位 | 新需求启动 | PM Agent |  | "
            f"{today_iso} |"
        )
    rows = []
    for e in changelog:
        rows.append(
            f'| {e.get("version", "")} '
            f'| {e.get("desc", "")} '
            f'| {e.get("reason", "")} '
            f'| {e.get("author", "")} '
            f'| {e.get("reviewer", "")} '
            f'| {e.get("date", "")} |'
        )
    return "\n".join(rows)


def _strip_pm_selfreview(content: str) -> tuple[str, bool]:
    r"""SNB-007 防御性兜底（2026-05-18 下游审计上报）：剥离 spec 模块草稿尾部
    误混入的 PM 自审报告区。

    已知限界（2026-06-12 审计记账，不改 regex 防回归）：仅识别二级标题
    `## 机械检查结果`；PM 误写成 `### 机械检查结果` 不剥离（真源约束在
    PM Agent §三 8.1，本函数是兜底非首防）。

    根因：PM 自审报告（顶部固定 `## 机械检查结果` 小节 + §五.X 自审清单，
    SSOT #35）是**过程产物**，不应写进 spec 模块草稿；但下游实测 PM 把自审
    报告全文写进了 `spec_M[XX]_draft.md`，`assemble_spec` 整篇 read_text 拼进
    `outputs/spec` → precheck 各 section 正则在报告文本上误报+噪音（SNB-007）。

    真源修复在 agent 层（PM 自审报告独立产出 / 不写进 spec 草稿，
    `AI产品经理_Agent.md §五.0`）；本剥离是**防御性兜底**——与
    `_strip_autofocus_attributes` 同型（防未来 PM 误写，不依赖 PM 自觉）。

    判定（保守、低 FP）：§三.5 规定 spec 模块草稿仅含 `## S2.M[XX]` / `.1`~`.6`，
    `## 机械检查结果` 是 PM 自审报告**文档级唯一顶部锚**（SSOT #35），在 spec
    草稿内出现即 100% 污染。

    剥离逻辑（2026-06-02 升级精确剥段）：
    - 找首个 `^## 机械检查结果` 段
    - 段结束 = 下一个 `## ` 或文件末
    - 剥离段本身（前后内容保留）

    兼容两场景：
    - **module drafts PM 自审在尾部** → 段结束 = EOF → 等同旧"截到 EOF"行为
    - **spec 真源 PM 自审在顶部 / 中间**（2026-06-02 治私域主页模块 P0-3）→
      段结束 = 下一个 `## ` → 仅剥该段，前后内容（S0/S0.5/S1/S2.MXX 等）保留

    无该锚 → 原样返回（绝大多数干净草稿零影响）。
    返回 (清洗后内容, 是否剥离)。
    """
    import re
    # 精确剥离段本身：段起始 = ## 机械检查结果；段结束 = 下一 ## 或 EOF
    m = re.search(
        r"^##[ \t]*机械检查结果.*?(?=\n##[ \t]|\Z)",
        content,
        re.DOTALL | re.MULTILINE,
    )
    if not m:
        return content, False
    stripped = (
        content[:m.start()].rstrip()
        + "\n"
        + content[m.end():].lstrip()
    )
    return stripped, True


def assemble_spec(data: dict) -> None:
    product = data["product"]
    spec_path = OUTPUT_DIR / f"spec_{product}_latest.md"

    if not spec_path.exists():
        print(f"[ERROR] spec 骨架不存在：{spec_path}", file=sys.stderr)
        sys.exit(1)

    # 手改保护：比对 sidecar fingerprint
    force_overwrite = "--force-overwrite" in sys.argv
    if force_overwrite:
        _backup_output_before_overwrite(spec_path, "spec")  # B1 SSOT #80
    _check_no_manual_drift(spec_path, product, "spec", force_overwrite)

    # Foundation 写入前置检查：S0/S0.5/S1 必须已就位
    spec_text = spec_path.read_text(encoding="utf-8")

    # SNB-007 同型防御扩展（2026-06-02 治私域主页模块 spec L8-L18 PM 自审报告污染）：
    # PM 把自审报告（含 `## 机械检查结果` 区块）误写进 outputs/spec_*.md 真源
    # （而非模块 draft）→ 在 Foundation 保留区污染下游交付物。本扩展在读入后
    # 立即剥离剩余 spec_text（之前 _strip_pm_selfreview 仅扫 module drafts）。
    spec_text, did_strip_spec = _strip_pm_selfreview(spec_text)
    if did_strip_spec:
        print(
            f"  [!] outputs/spec_*.md 真源含 PM 自审报告（## 机械检查结果…）— "
            f"已剥离防污染（SNB-007 同型扩展防御；真源修复应在 PM Agent 层 "
            f"不写进 spec 真源）",
            file=sys.stderr,
        )

    missing_sections = [
        s for s in ("## S0", "## S0.5", "## S1")
        if s not in spec_text
    ]
    if missing_sections:
        print(
            f"[ERROR] spec.md 缺少 Foundation 应写入的章节：{missing_sections}",
            file=sys.stderr,
        )
        print(
            "  请确认子阶段二 Foundation Agent 已执行并向 "
            f"{spec_path} 追加 S0 / S0.5 / S1，再重跑本脚本",
            file=sys.stderr,
        )
        sys.exit(1)

    # 重跑场景：截断到 SPEC_MODULES_START 标记之前（仅作内存截断，最终一次性写盘）
    truncated = False
    if SPEC_MODULES_START in spec_text:
        n_marks = spec_text.count(SPEC_MODULES_START)
        if n_marks > 1:
            print(f"[WARN] spec 含 {n_marks} 个 SPEC_MODULES_START 标记（应仅 1 个），"
                  f"按首个截断——多余标记可能来自误复制，建议人工核查", file=sys.stderr)
        truncate_pos = spec_text.find(SPEC_MODULES_START)
        spec_text = spec_text[:truncate_pos].rstrip() + "\n"
        truncated = True

    # 提议1 §3.0 页面层级架构：现场读 scaffold 派生注入区块1（位于 Foundation
    # 保留区内，每次 assemble 重新派生 → 改 scaffold 后下次 Step4 自然刷新）
    spec_text, sitemap_ok = inject_spec_sitemap(spec_text, data)
    if sitemap_ok:
        print("  [+] §3.0 页面层级架构（从 scaffold 现场派生，SSOT #38）")

    modules = data["modules"]
    draft_paths = check_drafts(modules, "spec_", "md")

    # 全内存拼接：任何模块草稿读取异常都不会污染磁盘文件
    # （此前用 spec_path.open("a") 流式追加 + 中途 sys.exit(1) 会留半截 SPEC_MODULES_START 块）
    parts: list[str] = [spec_text, f"\n{SPEC_MODULES_START}\n"]
    stripped_reports = 0
    for mod, draft in zip(modules, draft_paths):
        content = draft.read_text(encoding="utf-8").strip()
        content, did_strip = _strip_pm_selfreview(content)  # SNB-007 防御兜底
        if did_strip:
            stripped_reports += 1
            print(
                f"  [!] {draft.name} 内含 PM 自审报告（## 机械检查结果…）—已剥离，"
                f"防污染 outputs/spec（SNB-007；真源修复应在 agent 层不写进草稿）",
                file=sys.stderr,
            )
        parts.append("\n\n---\n\n")
        parts.append(content.strip())
        parts.append("\n")
        print(f"  [+] {draft.name}")
    parts.append(SPEC_FOOTER.format(
        end_marker=SPEC_MODULES_END,
        foundation_sections=build_foundation_sections_md(),
        changelog_rows=_build_spec_changelog_rows(
            data.get("changelog", []),
            date.today().isoformat(),
        ),
    ))

    # 一次性写盘（与 assemble_prd 模式对齐）
    spec_path.write_text("".join(parts), encoding="utf-8")
    _save_fingerprint(spec_path, product, "spec")
    if truncated:
        print(f"  [↻] 检测到已拼装内容，已截断至 Foundation 末尾后重拼")

    print(f"\n[OK] spec.md 拼装完成 — {len(modules)} 个模块 + 文档尾")
    print(f"     {spec_path}")
    print(f"\n提示：草稿文件可在主管审核通过后删除（process_record/drafts/spec_M*_draft.md）")


# ── prd.html 拼装 ─────────────────────────────────────────────────────────────

def _strip_autofocus_attributes(html: str) -> tuple[str, int]:
    """剥离 PRD 中所有 autofocus 属性（NB-WE-19 防御性兜底,issue 2026-05-12 下游 # 13）。

    PRD 是多帧设计文档,`<input autofocus>` 会在浏览器加载时触发 scrollIntoView,
    路过 100+ sticky 元素引发合成层风暴 → 破坏默认显示首帧 + 滚动条闪烁。
    真源修复仍在 drafts 层删除 autofocus,本剥离是防御性兜底(防未来 PM 误写)。

    匹配规则:`\\s+autofocus(?=[\\s>])` — 仅匹配独立 autofocus 属性
    (前置空白 + 后接空白或 `>`),避免误伤 `data-autofocus` 等自定义属性。

    返回 (新 html, 剥离次数)。
    """
    import re
    pattern = re.compile(r"\s+autofocus(?=[\s>])")
    new_html, count = pattern.subn("", html)
    return new_html, count


def _overwrite_first_style_from_template(html: str) -> tuple[str, bool]:
    """全量重读 template `<style>` 段覆盖 outputs/prd 第一个 `<style>` 块。

    NB-WE-20 frame-card isolation 派生漂移修复（issue 2026-05-12 下游 # 14）：
    assemble_prd() 仅 prd_path.read_text() 然后 inject frames,从不重读 template,
    template 新增 / 修订 CSS 规则（如 .frame-card { isolation: isolate; }）
    不会自动同步到派生层 outputs/prd。本 helper 在 inject 链最前面把 template
    `<style>` 段强制覆盖,实现 SSOT「真源永远胜出」。

    后续步骤:_inject_template_hash → inject frames → inject_proj_css →
    inject_fallback_css(在 template `<style>` 顶部插入 FB-FALLBACK 块,幂等)。

    template 不存在 / 解析失败 → warn + 跳过（不阻断 assemble 主流程）。
    返回 (新 html, 是否实际替换)。
    """
    import re

    if not PRD_TEMPLATE_PATH.exists():
        print(
            f"[WARN] PRD template 不存在,跳过 `<style>` 同步:{PRD_TEMPLATE_PATH}",
            file=sys.stderr,
        )
        return html, False
    template_text = PRD_TEMPLATE_PATH.read_text(encoding="utf-8")
    template_style_m = re.search(r"<style>([\s\S]*?)</style>", template_text)
    if not template_style_m:
        print("[WARN] template 中无 `<style>` 块,跳过同步", file=sys.stderr)
        return html, False
    template_style = template_style_m.group(1)

    output_style_re = re.compile(r"<style>[\s\S]*?</style>")
    if not output_style_re.search(html):
        print("[WARN] outputs/prd 中无 `<style>` 块,跳过同步", file=sys.stderr)
        return html, False

    # 用 lambda 避免 re.sub 把 CSS 内容里可能出现的 `\g<...>` 等当作 backreference
    new_html = output_style_re.sub(
        lambda _m: f"<style>{template_style}</style>", html, count=1
    )
    return new_html, True


def _overwrite_spec_nav_label_from_template(html: str) -> tuple[str, int]:
    """议题 7 / NB-WE-2A-R2-02 P1 治本（2026-06-04）：把 `<div class="sidebar-spec-item"
    data-target="{sid}" onclick="showSection('{sid}')">{old_label}</div>` 中的
    `{old_label}` 强制对齐 SPEC_ITEMS 当前真源（gen_scaffold.py SPEC_ITEMS / commit
    2a7bc8b NB-HF-01/02 已锁），治"既有 PRD 的 sidebar 标签字面未跟随 SSOT 升级
    （3 仓 100% 命中：私域 / quotation-tool / business-circle 上线后 sidebar 仍含
    旧字面「功能需求规格」）"根因。

    与 `_overwrite_first_style_from_template` / `_overwrite_scripts_from_template`
    同模式（template / SSOT「真源永远胜出」），但本步**不**重读 template — sidebar
    section-title 的 SSOT 在 gen_scaffold.SPEC_ITEMS（template 内是注释示例非活动 DOM）。
    本函数内嵌一份 `SPEC_NAV_LABEL_OVERRIDE`，注释指明真源对侧（gen_scaffold L47-57）。

    idempotent：已是新字面 → 不动 + 计数 0；幂等重跑无副作用。

    覆盖范围（仅 sidebar nav 字面，不动 spec-header 字面 — spec-header 由
    inject_function_overview_index 单独处理）：
    - `data-target="{sid}"` 锚定（不易误命中其他元素）+ 整 `<div>` 内文本替换

    返回 (新 html, 替换的 label 条目数)。
    """
    import re as _re

    # SPEC_NAV_LABEL_OVERRIDE：sid → 当前真源标签（与 gen_scaffold.SPEC_ITEMS L47-57 + commit 2a7bc8b 同源；
    # 改名须双向同步 — 真源对侧 `gen_scaffold.SPEC_ITEMS` 单列即可）。
    SPEC_NAV_LABEL_OVERRIDE = {
        "spec-background":     "需求背景",
        "spec-persona":        "用户画像",
        "spec-permission":     "权限矩阵",
        "spec-journey":        "用户旅程",
        "spec-business-flow":  "业务流程图",
        "spec-feature":        "功能索引",  # 旧字面「功能需求规格」是治理目标
        "spec-data":           "数据字段",
        "spec-exception":      "异常处理全景",
        "spec-nonfunc":        "非功能需求",
    }

    replaced_count = 0
    for sid, canonical_label in SPEC_NAV_LABEL_OVERRIDE.items():
        # 匹配 `<div class="sidebar-spec-item" data-target="{sid}" onclick="...">{any}</div>`
        # 允许 class 顺序/扩展 + 额外属性 + 内文本任意（非 </ 字符），不跨标签
        pattern = _re.compile(
            r'(<div\s+class\s*=\s*"[^"]*\bsidebar-spec-item\b[^"]*"[^>]*\bdata-target\s*=\s*"'
            + _re.escape(sid)
            + r'"[^>]*>)([^<]*)(</div>)',
            _re.IGNORECASE,
        )

        def _sub(m: _re.Match) -> str:
            nonlocal replaced_count
            old_label = m.group(2).strip()
            if old_label == canonical_label:
                return m.group(0)  # idempotent — 不动
            replaced_count += 1
            return f"{m.group(1)}{canonical_label}{m.group(3)}"

        html = pattern.sub(_sub, html)

    return html, replaced_count


def _overwrite_sidebar_nav_structure_from_template(html: str) -> tuple[str, int]:
    """议题 28 NB-WE-NAV-OVERWRITE 治本（2026-06-06）：把 outputs/prd 中的 sidebar
    SPEC 组 + SITEMAP 组的 sidebar-spec-item div 段强制对齐 `gen_scaffold.build_spec_nav()`
    / `build_sitemap_nav()` 当前真源，治"议题 27 修改 prd_template.html sidebar 结构 +
    gen_scaffold.py build_*_nav 后 outputs/prd 不会自动重生 sidebar 结构（assemble.py
    仅重读 <style>/<script>/label，不重读 sidebar 结构）"哑修复根因（PM 上报实证：
    私域 outputs/prd L2287-2306 仍是 8+5 旧结构 + 业务流程图 nav 仍在 sitemap 段）。

    与 `_overwrite_first_style_from_template`（NB-WE-20）/ `_overwrite_scripts_from_template`
    （WE-ASM）同模式（template / SSOT「真源永远胜出」），覆盖 sidebar **结构层**
    （label 层由 `_overwrite_spec_nav_label_from_template` 议题 7 单独处理，本函数
    在其之前调用 — 结构重读后 label 已是真源，label 重读多数情况 idempotent）。

    覆盖范围（仅 SPEC + SITEMAP 两组 group-body 内的 sidebar-spec-item div 列表）：
    - `<div class="sidebar-group-body" data-group-body="spec">` 内容 → build_spec_nav()
    - `<div class="sidebar-group-body" data-group-body="sitemap">` 内容 → build_sitemap_nav()

    豁免：group-body 不存在（如旧版本 prd 无该结构）→ 跳过该段，不报错。
    idempotent：已是当前真源 → 不动 + 计数 0；幂等重跑无副作用。

    返回 (新 html, 替换段数 0/1/2)。
    """
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    # Import gen_scaffold（同 pm-workflow/scripts/ 目录；顶层无副作用）
    _scripts_dir = _Path(__file__).parent
    if str(_scripts_dir) not in _sys.path:
        _sys.path.insert(0, str(_scripts_dir))
    import gen_scaffold as _gen_scaffold

    replaced = 0

    # SPEC 组（议题 27 后全量 9 项含 spec-business-flow 紧跟 spec-journey）
    spec_nav_new = _gen_scaffold.build_spec_nav().strip()
    spec_re = _re.compile(
        r'(<div\s+class="sidebar-group-body"\s+data-group-body="spec">)'
        r'([\s\S]*?)'
        r'(</div>\s*<div\s+class="sidebar-section-title)',
        _re.IGNORECASE,
    )
    spec_m = spec_re.search(html)
    if spec_m and spec_m.group(2).strip() != spec_nav_new:
        new_block = f"{spec_m.group(1)}\n        {spec_nav_new}\n        {spec_m.group(3)}"
        html = html[: spec_m.start()] + new_block + html[spec_m.end() :]
        replaced += 1

    # SITEMAP 组（议题 27 后 4 项 sk-*，业务流程图已移到 SPEC 组）
    sitemap_nav_new = _gen_scaffold.build_sitemap_nav().strip()
    sitemap_re = _re.compile(
        r'(<div\s+class="sidebar-group-body"\s+data-group-body="sitemap">)'
        r'([\s\S]*?)'
        r'(</div>\s*<div\s+class="sidebar-section-title)',
        _re.IGNORECASE,
    )
    sitemap_m = sitemap_re.search(html)
    if sitemap_m and sitemap_m.group(2).strip() != sitemap_nav_new:
        new_block = f"{sitemap_m.group(1)}\n        {sitemap_nav_new}\n        {sitemap_m.group(3)}"
        html = html[: sitemap_m.start()] + new_block + html[sitemap_m.end() :]
        replaced += 1

    return html, replaced


def _ensure_layout_closing_before_body(html: str) -> tuple[str, int]:
    """议题 10 NB-WE-PROTO-NAV-OVERWRITE 机械兜底（2026-06-07）：用 html.parser 真 DOM
    解析跟踪 div 嵌套深度，若最终 depth > 0（缺 close）→ 在 `</body>` 前补足缺失的
    `</div>`，让 outputs/prd 真 DOM 平衡。

    与 `_overwrite_sidebar_nav_structure_from_template`（议题 28/10 PROTO 覆盖）协同
    形成 div 平衡防御链：前者治"sidebar 三组 nav 不重写残留"形式问题，本函数治"全文
    DOM 平衡"语义问题，二者正交（前者按 SSOT 真源胜出策略，本函数按浏览器 DOM 解析
    层平衡约束）。

    算法：
    - 用 stdlib html.parser（无三方依赖）遍历 html
    - 跳过 `<script>` / `<style>` 内容（浏览器不解析其内 div 字面）
    - 跟踪 `<div>` 开闭深度
    - 若 final depth > 0 → 缺 N 个 `</div>` → 在最末 `</body>` 前补 N 个 `</div>`
    - idempotent：已平衡 → depth 0 → 0 处补 + 计数 0

    豁免：
    - depth ≤ 0（平衡或多 close）→ 不补，不报错（多 close 由另独立机制处理）
    - 无 `</body>` → 不补，避免破坏非标准 HTML
    - html.parser 解析异常 → 兜底跳过 + WARN（不阻塞 assemble）

    返回 (新 html, 补足 `</div>` 数 0/N)。
    """
    from html.parser import HTMLParser as _HP

    class _DivDepth(_HP):
        def __init__(self) -> None:
            super().__init__()
            self.depth = 0
            self.in_skip = False

        def handle_starttag(self, tag: str, attrs: list) -> None:
            if tag in ("script", "style"):
                self.in_skip = True
                return
            if self.in_skip:
                return
            if tag == "div":
                self.depth += 1

        def handle_endtag(self, tag: str) -> None:
            if tag in ("script", "style"):
                self.in_skip = False
                return
            if self.in_skip:
                return
            if tag == "div":
                self.depth -= 1

    try:
        p = _DivDepth()
        p.feed(html)
    except Exception as e:
        print(
            f"[WARN] _ensure_layout_closing_before_body 跳过：html.parser 异常 {e}",
            file=sys.stderr,
        )
        return html, 0

    if p.depth <= 0:
        return html, 0  # 已平衡或多 close，不动

    body_close_idx = html.rfind("</body>")
    if body_close_idx == -1:
        return html, 0  # 无 </body>，不动

    pad = "  </div>\n" * p.depth
    return html[:body_close_idx] + pad + html[body_close_idx:], p.depth


def _overwrite_cover_version_from_scaffold_changelog(html: str) -> tuple[str, int]:
    """议题 20 / NB-WE-2A-R8-03 P1 治本：把 prd 封面 `<span class="cover-version">XXX</span>`
    强制对齐 scaffold.json["changelog"] 末行 `version` 真源（SemVer 化阶段 4 版本号触发点
    单源约束，G-02 派生）。

    缺陷背景（私域主页 R8-03 实证）：scaffold.json["version"] = "v4.0"（PM 历史遗留
    粗粒度填法），changelog 末行 `version` = "v0.1"（SSOT #48 v0.1 期间未升版本号合规填法）。
    重 assemble 时 prd 封面 cover-version 取 scaffold["version"] 渲染 → 显示 v4.0
    误导下游消费方（真实状态是 v0.1 未交付态）。

    与 `_overwrite_spec_nav_label_from_template` / `_overwrite_first_style_from_template`
    同模式（SSOT「真源永远胜出」），但本步**不**读 template — 封面版本号的 SSOT 在
    scaffold.json["changelog"] 末行 `version`（SemVer 化阶段 4 版本号触发点：v0.1 / v1.0 /
    vN.0；G-02 / SSOT #48 真源链）。

    idempotent：已与真源对齐 → 不动 + 计数 0；幂等重跑无副作用。

    覆盖范围（仅封面 `<span class="cover-version">`，不动其他元素）：
    - `<span class="cover-version">{XXX}</span>` 锚定，整 `<span>` 内文本替换为
      `scaffold["changelog"][-1]["version"]`

    异常优雅降级：
    - scaffold.json 不存在 / 解析失败 / changelog 空 / 末行无 version → 跳过 + WARN
      （不阻断 assemble；真源缺失场景 PM 应先修 scaffold）
    - prd html 内无 `cover-version` span → 跳过 + 计数 0（旧版 prd 无封面块场景）

    返回 (新 html, 替换数：0 / 1)。
    """
    import re as _re

    if not SCAFFOLD.exists():
        print(
            f"[WARN] scaffold.json 不存在，跳过 cover-version 同步：{SCAFFOLD}",
            file=sys.stderr,
        )
        return html, 0

    try:
        data = json.loads(SCAFFOLD.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(
            f"[WARN] scaffold.json 解析失败，跳过 cover-version 同步：{e}",
            file=sys.stderr,
        )
        return html, 0

    changelog = data.get("changelog", [])
    if not changelog:
        print(
            "[WARN] scaffold.json[\"changelog\"] 为空，跳过 cover-version 同步",
            file=sys.stderr,
        )
        return html, 0

    last_entry = changelog[-1]
    if not isinstance(last_entry, dict):
        print(
            "[WARN] scaffold.json[\"changelog\"] 末行格式非 dict，跳过 cover-version 同步",
            file=sys.stderr,
        )
        return html, 0

    canonical_version = (last_entry.get("version") or "").strip()
    if not canonical_version:
        print(
            "[WARN] scaffold.json[\"changelog\"] 末行无 version 字段，跳过 cover-version 同步",
            file=sys.stderr,
        )
        return html, 0

    # 匹配 `<span class="cover-version">{any}</span>`（class 顺序/扩展兼容；内文本任意非 <）
    pattern = _re.compile(
        r'(<span\s+class\s*=\s*"[^"]*\bcover-version\b[^"]*"[^>]*>)([^<]*)(</span>)',
        _re.IGNORECASE,
    )

    replaced = 0

    def _sub(m: _re.Match) -> str:
        nonlocal replaced
        old_text = m.group(2).strip()
        if old_text == canonical_version:
            return m.group(0)  # idempotent — 不动
        replaced += 1
        return f"{m.group(1)}{canonical_version}{m.group(3)}"

    new_html = pattern.sub(_sub, html)
    return new_html, replaced


def _overwrite_scripts_from_template(html: str) -> tuple[str, bool]:
    """全量重读 template 的 mermaid CDN `<script src>` 标签 + 尾部内联 `<script>`
    段，覆盖 outputs/prd 同位置（SSOT「真源永远胜出」，NB-WE-20 的 `<script>` 维度补盖）。

    缺陷背景（下游报告，2026-05-16）：`_overwrite_first_style_from_template`
    只覆盖第一个 `<style>` 块（CSS）。但 prd_template.html 的 JS 修复——如
    mermaid 初始化时序竞态修复 `ensureMermaidReady` / `renderMermaidWithRetry`
    （在 </body> 前的内联 `<script>` 段）+ head mermaid CDN `<script src ...
    onerror>`——均不在 `<style>` 内，旧机制不覆盖 → template JS 改动不同步到
    派生层 outputs/prd（与 NB-WE-20 同模式，JS 维度此前漏盖）。

    覆盖范围（prd_template.html 恰 2 个 `<script>` 构造，均纯模板逻辑——
    changelog / showcase / FRAME 注入为 body HTML，PROJ-CSS 在 `<style>` 内，
    无 PM/draft 内容注入 `<script>`，故整体覆盖安全）：
      1. head mermaid CDN 外链：`<script ... src="...mermaid..." ...></script>`
      2. 尾部内联块：`<script>...</script>`（字面无属性的 `<script>`）

    必须与 `_overwrite_first_style_from_template` 同处 inject 链最前面。
    template 不存在 / 缺对应块 → warn + 跳过（不阻断 assemble）。
    返回 (新 html, 是否实际替换任一)。
    """
    import re

    if not PRD_TEMPLATE_PATH.exists():
        print(
            f"[WARN] PRD template 不存在,跳过 `<script>` 同步:{PRD_TEMPLATE_PATH}",
            file=sys.stderr,
        )
        return html, False
    template_text = PRD_TEMPLATE_PATH.read_text(encoding="utf-8")
    changed = False

    # 1. mermaid CDN 外链 <script src=...mermaid...></script>（template 唯一外链 script）
    cdn_re = re.compile(
        r'<script\b[^>]*\bsrc=["\'][^"\']*mermaid[^"\']*["\'][^>]*></script>'
    )
    t_cdn = cdn_re.search(template_text)
    if not t_cdn:
        print("[WARN] template 中无 mermaid CDN <script src> 标签,跳过该项", file=sys.stderr)
    elif not cdn_re.search(html):
        print("[WARN] outputs/prd 中无 mermaid CDN <script src> 标签,跳过该项", file=sys.stderr)
    else:
        cdn_tag = t_cdn.group(0)
        html = cdn_re.sub(lambda _m: cdn_tag, html, count=1)
        changed = True

    # 2. 尾部内联 <script>...</script>（字面无属性的 <script>,template 唯一内联块）
    #    行首锚定 `^[ \t]*<script>$`：head 注释里有散文 `由本文件 <script> 段集中调用`,
    #    裸 `<script>` 正则会从该注释词误匹配到 CDN 的 `></script>`（实测 230 字垃圾块）;
    #    真内联块开标签独占一行（缩进 + `<script>` + 行尾）,行锚精确区分。
    #    lambda 替换：避免 re.sub 把 JS 内的 $ / \g<...> 当 backreference（同 <style> 处理）
    inline_re = re.compile(r"(?m)^[ \t]*<script>[ \t]*$[\s\S]*?</script>")
    t_inline = inline_re.search(template_text)
    if not t_inline:
        print("[WARN] template 中无内联 `<script>` 块,跳过该项", file=sys.stderr)
    elif not inline_re.search(html):
        print("[WARN] outputs/prd 中无内联 `<script>` 块,跳过该项", file=sys.stderr)
    else:
        inline_block = t_inline.group(0)
        html = inline_re.sub(lambda _m: inline_block, html, count=1)
        changed = True

    return html, changed


def inject_fallback_css(html: str) -> tuple[str, int]:
    """把 fb-fallback.css 内容注入到 PRD 第一个 <style> 块顶部。
    幂等：若已含 FB_FALLBACK_START/END 标记块，先移除旧块再注入新内容。
    返回 (新 html, 注入的 CSS 字节数)；CSS 文件不存在时返回 (原 html, 0)。"""
    import re

    if not FALLBACK_CSS_PATH.exists():
        print(f"[WARN] fb-fallback.css 不存在，跳过注入：{FALLBACK_CSS_PATH}", file=sys.stderr)
        return html, 0

    css_content = FALLBACK_CSS_PATH.read_text(encoding="utf-8").strip()

    # 幂等：移除已存在的注入块（含前后单一换行，避免吞噬其他空白）
    pattern = re.compile(
        r'\n?' + re.escape(FB_FALLBACK_START) + r'.*?' + re.escape(FB_FALLBACK_END) + r'\n?',
        re.DOTALL,
    )
    html = pattern.sub('', html)

    # 定位第一个 <style ...> 标签
    style_match = re.search(r'<style[^>]*>', html)
    if not style_match:
        print("[WARN] PRD 中无 <style> 块，无法注入 fb-fallback.css", file=sys.stderr)
        return html, 0

    insert_pos = style_match.end()
    block = f"\n{FB_FALLBACK_START}\n{css_content}\n{FB_FALLBACK_END}\n"
    new_html = html[:insert_pos] + block + html[insert_pos:]
    return new_html, len(css_content)


def extract_frames(draft_text: str) -> dict[str, str]:
    """从草稿中提取所有 <!-- [FRAME: id] --> ... <!-- [/FRAME: id] --> 片段。"""
    import re
    pattern = re.compile(
        r'<!--\s*\[FRAME:\s*(\S+)\]\s*-->(.*?)<!--\s*\[/FRAME:\s*\1\]\s*-->',
        re.DOTALL,
    )
    return {m.group(1): m.group(2).strip() for m in pattern.finditer(draft_text)}


def extract_proj_css(draft_text: str) -> str:
    """从草稿中提取 <!-- [PROJ-CSS-START] -->...<!-- [PROJ-CSS-END] --> 之间的 CSS 内容。
    草稿可包含 0 或 1 处。多处出现取并集（按出现顺序拼接）。返回不含包裹标记的纯 CSS。"""
    import re
    pattern = re.compile(
        r'<!--\s*\[PROJ-CSS-START\]\s*-->(.*?)<!--\s*\[PROJ-CSS-END\]\s*-->',
        re.DOTALL,
    )
    return "\n".join(m.group(1).strip() for m in pattern.finditer(draft_text))


def extract_proj_component_showcase(draft_text: str) -> str:
    """从单 module draft 提取所有 `<section id="proj-component-*" class="proj-component-showcase">` 块。

    多个 section 按出现顺序拼接返回(原样含 <section> 包裹)。无匹配返回空字符串。

    新增于 2026-05-12 /retro:用户提议把 proj-component-* showcase 从「散在各 module 内」
    集中到主模板的 `<section id="proj-component-area">` 容器,assemble 拼装时提取注入。
    """
    import re
    pattern = re.compile(
        r'<section\s+id\s*=\s*"proj-component-[^"]+"\s+class\s*=\s*"[^"]*\bproj-component-showcase\b[^"]*"[^>]*>.*?</section>',
        re.DOTALL,
    )
    return "\n\n".join(m.group(0) for m in pattern.finditer(draft_text))


def inject_proj_component_showcase(html: str, all_showcase: str) -> tuple[str, int]:
    """把所有 module drafts 的 proj-component-* showcase 集中注入到主模板
    [PROJ-COMPONENT-SHOWCASE-AREA] 占位处,幂等。

    幂等机制:用 [PROJ-COMPONENT-SHOWCASE-AREA-START/END] 包裹注入块,
    重跑时正则替换中间内容。
    """
    import re as _re

    placeholder = "<!-- [PROJ-COMPONENT-SHOWCASE-AREA]"
    # NB-LIT-01 同类修复:START 标记允许含 `auto-injected by assemble.py` 字面
    reentry_re = _re.compile(
        r"<!--\s*\[PROJ-COMPONENT-SHOWCASE-AREA-START\].*?-->"
        r".*?"
        r"<!--\s*\[PROJ-COMPONENT-SHOWCASE-AREA-END\].*?-->",
        _re.DOTALL,
    )

    if not all_showcase.strip():
        # 无 showcase → 注入空块(保留容器但无内容)
        injected = (
            "<!-- [PROJ-COMPONENT-SHOWCASE-AREA-START] auto-injected by assemble.py -->\n"
            '        <div style="color:var(--fb-text-hint);font-size:12px;padding:24px 0;">'
            "（本期无 proj 组件,使用 fallback 即可）</div>\n"
            "        <!-- [PROJ-COMPONENT-SHOWCASE-AREA-END] -->"
        )
    else:
        injected = (
            "<!-- [PROJ-COMPONENT-SHOWCASE-AREA-START] auto-injected by assemble.py -->\n"
            f"{all_showcase}\n"
            "        <!-- [PROJ-COMPONENT-SHOWCASE-AREA-END] -->"
        )

    if reentry_re.search(html):
        html = reentry_re.sub(injected, html, count=1)
        return html, len(all_showcase)
    # 首次:用占位匹配 — NB-LIT-01 同类修复:用 .*? + DOTALL 避免 [^<>] 在注释含 HTML 示例时卡住
    placeholder_re = _re.compile(
        r"<!--\s*\[PROJ-COMPONENT-SHOWCASE-AREA\].*?-->",
        _re.DOTALL,
    )
    if placeholder_re.search(html):
        html = placeholder_re.sub(injected, html, count=1)
        return html, len(all_showcase)

    # 兜底 3(NB-阶段4-C 修复 / NB-LIT 同类):section 容器存在但无 START/END、无占位
    # → 历史裸注入兜底:旧版 assemble 首次注入时尚无 START/END 包裹机制,占位字面被吃掉,
    #   导致后续升级的幂等机制找不到锚点而静默跳过。本兜底定位 <section id="proj-component-area"> 容器,
    #   以下一个 <section id="H-M..."> 业务帧作为外部 boundary,反向找 area 真闭合,
    #   在 area body 内找第一个 showcase 起点(<!-- ===== M -->)或 <section id="proj-component-{非 area}">,
    #   用 START/END 包裹的新 all_showcase 替换从起点到 area 闭合之间内容,
    #   保留 form-field-binding-anchors 等 showcase 前的兄弟元素。
    area_start_match = _re.search(r'<section\s+id="proj-component-area"[^>]*>', html)
    if not area_start_match:
        return html, 0  # 模板未含集中容器,静默跳过
    next_h_section = _re.search(r'<section\s+id="H-M\d', html[area_start_match.end():])
    if not next_h_section:
        return html, 0
    area_end_outer = area_start_match.end() + next_h_section.start()
    area_section_close_iter = list(
        _re.finditer(r"</section>", html[area_start_match.end():area_end_outer])
    )
    if not area_section_close_iter:
        return html, 0
    area_close_pos = area_start_match.end() + area_section_close_iter[-1].start()
    area_body = html[area_start_match.end():area_close_pos]
    showcase_start_match = _re.search(
        r'(\s*<!--\s*=====\s*M\d{2}|\s*<section\s+id="proj-component-(?!area)[\w-]+)',
        area_body,
    )
    if not showcase_start_match:
        return html, 0
    inject_start_pos = area_start_match.end() + showcase_start_match.start()
    injected_migrate = (
        "\n        <!-- [PROJ-COMPONENT-SHOWCASE-AREA-START] auto-injected by assemble.py -->\n"
        f"{all_showcase}\n"
        "        <!-- [PROJ-COMPONENT-SHOWCASE-AREA-END] -->\n      "
    )
    new_html = html[:inject_start_pos] + injected_migrate + html[area_close_pos:]
    return new_html, len(all_showcase)


def make_changelog_pages_clickable(html: str, modules: list) -> tuple[str, int]:
    """处理主体 `<section id="component-changelog">` 内 changelog 表「使用页面」/「影响页面」
    列的 td,把 `M{XX}-P{YY}` 或 `M{XX}` token 转为 onclick 跳转链接。

    跳转目标:
        - `M{XX}-P{YY}` 具体页面 → 该页面 scaffold states[0].prd_id (首状态)
        - `M{XX}` 纯模块 → 该模块 scaffold pages[0].states[0].prd_id (首页面首状态)

    幂等:已含 `<a onclick` 的 td 不再处理(只匹配纯文本 td)。

    新增于 2026-05-12 /retro:用户提议从 changelog 直接跳到组件使用页面。
    """
    import re as _re

    # 1. 构建 module → 兜底 prd_id 映射 + page → prd_id 映射(取首状态)
    module_first_state: dict[str, str] = {}  # "M01" → "H-M01-P01-default"
    page_first_state: dict[str, str] = {}  # "M01-P01" → "H-M01-P01-default"
    for mod in modules:
        mid = mod.get("id", "")
        pages = mod.get("pages", []) or []
        if not pages:
            continue
        first_page = pages[0]
        first_page_states = first_page.get("states", []) or []
        if first_page_states:
            module_first_state[mid] = first_page_states[0].get("prd_id", "")
        for page in pages:
            pid = f"{mid}-{page.get('id', '')}"
            states = page.get("states", []) or []
            if states:
                page_first_state[pid] = states[0].get("prd_id", "")

    if not module_first_state and not page_first_state:
        return html, 0

    # 2. 定位 changelog section
    changelog_re = _re.compile(
        r'(<section\s+id\s*=\s*"component-changelog"[^>]*>)(.*?)(</section>)',
        _re.DOTALL | _re.IGNORECASE,
    )
    m_cl = changelog_re.search(html)
    if not m_cl:
        return html, 0

    head, body, tail = m_cl.group(1), m_cl.group(2), m_cl.group(3)

    # 3. 处理每个 changelog-group:简化为「先找表头确定列索引,再逐 tr 替换该列 token」
    #    不依赖 group div 的精确边界,直接在 changelog section body 上滚 thead/tbody 配对处理
    # 兼容老表头(「使用模块」/「影响模块」)+ 新表头(「使用页面」/「影响页面」)
    # 升级路径:即使 PRD 仍用老表头,只要值含 M{XX}(-P{YY})? 仍能触发跳转
    target_headers = ("使用页面", "影响页面", "使用模块", "影响模块")
    total_replaced = 0

    # 配对 <thead> 和后续紧邻 <tbody>(在同一 changelog-group 内)
    table_re = _re.compile(
        r"(<thead[^>]*>(?P<thead>.*?)</thead>)"
        r"(?P<between>.*?)"
        r"(<tbody[^>]*>(?P<tbody>.*?)</tbody>)",
        _re.DOTALL | _re.IGNORECASE,
    )

    def process_table(table_match):
        nonlocal total_replaced
        thead_inner = table_match.group("thead")
        tbody_inner = table_match.group("tbody")

        # 找 thead 中 th 列表
        th_cells = _re.findall(r"<th[^>]*>(.*?)</th>", thead_inner, _re.DOTALL)
        target_idx = -1
        for idx, th in enumerate(th_cells):
            th_clean = _re.sub(r"<[^>]+>", "", th).strip()
            if th_clean in target_headers:
                target_idx = idx
                break
        if target_idx < 0:
            return table_match.group(0)  # 本 table 无目标列,跳过

        # 处理 tbody 内每个 tr
        td_full_re = _re.compile(r"<td[^>]*>.*?</td>", _re.DOTALL)
        td_inner_re = _re.compile(r"<td[^>]*>(.*?)</td>", _re.DOTALL)

        def process_tr(tr_match):
            nonlocal total_replaced
            tr_text = tr_match.group(0)  # 整个 <tr>...</tr>
            td_full_list = td_full_re.findall(tr_text)
            if target_idx >= len(td_full_list):
                return tr_text
            target_td_full = td_full_list[target_idx]  # 第 target_idx 个 <td>...</td>
            inner_m = td_inner_re.match(target_td_full)
            if not inner_m:
                return tr_text
            td_inner = inner_m.group(1)
            if "<a " in td_inner:  # 已含 anchor,幂等跳过
                return tr_text

            def replace_token(m):
                nonlocal total_replaced
                token = m.group(0)
                if "-P" in token:
                    target = page_first_state.get(token, "")
                    if not target:
                        target = module_first_state.get(token.split("-P")[0], "")
                else:
                    target = module_first_state.get(token, "")
                if not target:
                    return token
                total_replaced += 1
                return (
                    f'<a onclick="showSection(\'{target}\')" '
                    f'style="cursor:pointer;color:#1665ff;text-decoration:underline;">'
                    f'{token}</a>'
                )

            new_td_inner = _re.sub(r"\bM\d+(?:-P\d+)?\b", replace_token, td_inner)
            if new_td_inner == td_inner:
                return tr_text
            new_target_td_full = target_td_full.replace(td_inner, new_td_inner, 1)
            return tr_text.replace(target_td_full, new_target_td_full, 1)

        new_tbody_inner = _re.sub(
            r"<tr[^>]*>.*?</tr>", process_tr, tbody_inner, flags=_re.DOTALL
        )
        # 用新的 tbody_inner 替换原表
        return table_match.group(0).replace(tbody_inner, new_tbody_inner, 1)

    new_body = table_re.sub(process_table, body)
    html = html.replace(m_cl.group(0), head + new_body + tail, 1)
    return html, total_replaced


def make_changelog_anchor_clickable(html: str) -> tuple[str, int]:
    """处理主体 `<section id="component-changelog">` 内 changelog 表「组件说明锚点」列,
    把 `proj-component-{name}` 字面值转为 `<a onclick="showSection('proj-component-{name}')">查看组件说明</a>`
    跳转链接，方便读者从 changelog 直接跳到 §7.1 组件说明集中容器查看组件 schema/状态。

    兼容老表头「spec / prd 锚点」（升级前）+ 新表头「组件说明锚点」。
    幂等：表格中已含 `<a` 节点的 td 跳过(防重复转换)。

    SSOT：`prd_expression_standard.md §11.1 字段说明` 中「组件说明锚点」定义。
    """
    import re as _re

    changelog_re = _re.compile(
        r'(<section\s+id\s*=\s*"component-changelog"[^>]*>)(.*?)(</section>)',
        _re.DOTALL | _re.IGNORECASE,
    )
    m_cl = changelog_re.search(html)
    if not m_cl:
        return html, 0
    head, body, tail = m_cl.group(1), m_cl.group(2), m_cl.group(3)

    target_headers = ("组件说明锚点", "spec / prd 锚点")
    total_replaced = 0

    table_re = _re.compile(
        r"(<thead[^>]*>(?P<thead>.*?)</thead>)"
        r"(?P<between>.*?)"
        r"(<tbody[^>]*>(?P<tbody>.*?)</tbody>)",
        _re.DOTALL | _re.IGNORECASE,
    )

    def process_table(table_match):
        nonlocal total_replaced
        thead_inner = table_match.group("thead")
        tbody_inner = table_match.group("tbody")
        th_cells = _re.findall(r"<th[^>]*>(.*?)</th>", thead_inner, _re.DOTALL)
        target_idx = -1
        for idx, th in enumerate(th_cells):
            th_clean = _re.sub(r"<[^>]+>", "", th).strip()
            if th_clean in target_headers:
                target_idx = idx
                break
        if target_idx < 0:
            return table_match.group(0)

        td_full_re = _re.compile(r"<td[^>]*>.*?</td>", _re.DOTALL)
        td_inner_re = _re.compile(r"<td[^>]*>(.*?)</td>", _re.DOTALL)

        def process_tr(tr_match):
            nonlocal total_replaced
            tr_text = tr_match.group(0)
            td_full_list = td_full_re.findall(tr_text)
            if target_idx >= len(td_full_list):
                return tr_text
            target_td_full = td_full_list[target_idx]
            inner_m = td_inner_re.match(target_td_full)
            if not inner_m:
                return tr_text
            td_inner = inner_m.group(1)
            if "<a " in td_inner:  # 已含 anchor 节点,幂等跳过
                return tr_text

            # 匹配 proj-component-{name}(允许 kebab-case + 数字,可能含反引号包裹)
            anchor_re = _re.compile(r"`?(proj-component-[a-z0-9][a-z0-9-]*)`?")

            def replace_token(m):
                nonlocal total_replaced
                anchor = m.group(1)
                total_replaced += 1
                return (
                    f'<a onclick="showSection(\'{anchor}\')" '
                    f'style="cursor:pointer;color:#1665ff;text-decoration:underline;">'
                    f'查看组件说明</a>'
                )

            new_td_inner = anchor_re.sub(replace_token, td_inner, count=1)
            if new_td_inner == td_inner:
                return tr_text
            new_target_td_full = target_td_full.replace(td_inner, new_td_inner, 1)
            return tr_text.replace(target_td_full, new_target_td_full, 1)

        new_tbody_inner = _re.sub(
            r"<tr[^>]*>.*?</tr>", process_tr, tbody_inner, flags=_re.DOTALL
        )
        return table_match.group(0).replace(tbody_inner, new_tbody_inner, 1)

    new_body = table_re.sub(process_table, body)
    html = html.replace(m_cl.group(0), head + new_body + tail, 1)
    return html, total_replaced


def inject_component_changelog_nav(html: str) -> tuple[str, int]:
    """从 PRD §十一 component-changelog section 三个 group 派生 sidebar 导航条目,
    替换 [COMPONENT-CHANGELOG-NAV] 占位注释。

    数据源（SSOT）：PRD 主体 <section id="component-changelog"> 内
        <div class="changelog-group changelog-{new|update|deprecated}">
            <table>...<tbody><tr><td><code>proj.L*.{name}</code></td>...</tr>...</tbody>
    输出：每个组件一条 <div class="sidebar-spec-item"> + 状态 tag + onclick

    来源：issue 2026-05-07_1613（用户追加补充），Q1=A 单组件粒度

    幂等：重复跑会清除既有自动注入块,重新生成（FRAME-START/END 等价机制）。

    Returns: (修改后 html, 注入的组件数)
    """
    import re as _re

    # 0. 找占位（首次拼装）或既有注入块（重入）
    # NB-LIT-01 修复(2026-05-12 下游报):placeholder 改为正则,支持模板中多行长注释格式
    # 例:`<!-- [COMPONENT-CHANGELOG-NAV] assemble.py prd 自动注入...示例:<div...> -->`
    # 之前只匹配单行精确字面 `<!-- [COMPONENT-CHANGELOG-NAV] -->`,模板升级长注释后跑空(0 条目)
    placeholder_re = _re.compile(
        r"<!--\s*\[COMPONENT-CHANGELOG-NAV\].*?-->",
        _re.DOTALL,
    )
    # NB-LIT-01 连锁修复:reentry_re 的 START 标记原用 `\s*-->` 字面,但 inject_block
    # 实际 START 是 `<!-- [...START] auto-injected by assemble.py -->`(含说明字面),
    # `\s*` 不 match `auto-injected` → 重跑时既不识别既有块也不识别 placeholder
    # → 跑空注入。改为 `.*?-->` 允许 START 标记内任意内容(同时 END 也允许,future-proof)
    reentry_re = _re.compile(
        r"<!--\s*\[COMPONENT-CHANGELOG-NAV-START\].*?-->"
        r".*?"
        r"<!--\s*\[COMPONENT-CHANGELOG-NAV-END\].*?-->",
        _re.DOTALL,
    )
    if not placeholder_re.search(html) and not reentry_re.search(html):
        # 模板中无占位（旧骨架）→ 静默跳过,不阻断
        return html, 0

    # 1. 定位 component-changelog section 内容
    changelog_re = _re.compile(
        r'<section\s+id\s*=\s*"component-changelog"[^>]*>(.*?)</section>',
        _re.DOTALL | _re.IGNORECASE,
    )
    cm = changelog_re.search(html)
    if not cm:
        # PRD 主体无 component-changelog section → 注入空块（保留分组占位但无条目）
        injected_block = (
            "<!-- [COMPONENT-CHANGELOG-NAV-START] auto-injected by assemble.py -->\n"
            '        <div class="sidebar-spec-item" style="color:var(--fb-text-hint);font-size:11px;">'
            "（本期无组件变更）</div>\n"
            "        <!-- [COMPONENT-CHANGELOG-NAV-END] -->"
        )
        if reentry_re.search(html):
            html = reentry_re.sub(injected_block, html, count=1)
        else:
            html = placeholder_re.sub(injected_block, html, count=1)
        return html, 0

    changelog_html = cm.group(1)

    # 2. 在 changelog 内逐个 group 提取 (status, [proj_id, ...])
    group_re = _re.compile(
        r'<div\s+class\s*=\s*"[^"]*\bchangelog-(?P<status>new|update|deprecated)\b[^"]*"[^>]*>'
        r"(?P<body>.*?)"
        r"</div>\s*(?=<div\s+class\s*=\s*"
        r'"[^"]*\bchangelog-(?:new|update|deprecated|promote)\b'
        r"|</section>)",
        _re.DOTALL | _re.IGNORECASE,
    )
    component_re = _re.compile(
        r"<td>\s*<code>\s*(proj\.L\d+\.[a-z][\w-]*)\s*</code>\s*</td>",
        _re.IGNORECASE,
    )
    status_label = {"new": "新增", "update": "更新", "deprecated": "弃用"}
    status_class = {
        "new": "sidebar-status-new",
        "update": "sidebar-status-update",
        "deprecated": "sidebar-status-deprecated",
    }

    items: list[str] = []
    seen_ids: set[str] = set()  # 同一组件不重复注入
    for gm in group_re.finditer(changelog_html):
        status = gm.group("status").lower()
        body = gm.group("body")
        for proj_id in component_re.findall(body):
            if proj_id in seen_ids:
                continue
            seen_ids.add(proj_id)
            # proj.L2.product-card → proj-component-product-card
            name_part = proj_id.rsplit(".", 1)[-1]
            anchor_id = f"proj-component-{name_part}"
            label = status_label[status]
            cls = status_class[status]
            items.append(
                f'        <div class="sidebar-spec-subitem" data-target="{anchor_id}" '
                f"onclick=\"showSection('{anchor_id}')\">"
                f'<span class="sidebar-component-status {cls}">{label}</span>{proj_id}</div>'
            )

    # 3. 拼装注入块（含 START/END 标记便于重入幂等）
    if items:
        body_html = "\n".join(items)
    else:
        body_html = (
            '        <div class="sidebar-spec-item" style="color:var(--fb-text-hint);font-size:11px;">'
            "（本期无组件变更）</div>"
        )
    injected_block = (
        "<!-- [COMPONENT-CHANGELOG-NAV-START] auto-injected by assemble.py -->\n"
        f"{body_html}\n"
        "        <!-- [COMPONENT-CHANGELOG-NAV-END] -->"
    )

    # 4. 替换（重入或首次,NB-LIT-01:placeholder 改为正则 sub 支持多行长注释）
    if reentry_re.search(html):
        html = reentry_re.sub(lambda m: injected_block, html, count=1)
    else:
        html = placeholder_re.sub(lambda m: injected_block, html, count=1)

    # 5. 注入侧栏徽章数（issue 2026-05-09_1818 UX 优化）
    # 把模板中的 <span class="sidebar-changelog-badge" data-changelog-count style="display:none;"></span>
    # 替换为带计数 + 可见的样式;计数为 0 时保持隐藏
    badge_count = len(items)
    badge_re = _re.compile(
        r'(<span\s+class="sidebar-changelog-badge"\s+data-changelog-count\s+style=")[^"]*("\s*>)[^<]*(</span>)'
    )
    if badge_count > 0:
        html = badge_re.sub(
            rf'\g<1>display:inline-block;\g<2>{badge_count}\g<3>',
            html, count=1,
        )
    # else: 保留 display:none 占位,无需替换

    return html, badge_count


def inject_proj_css(html: str, all_proj_css: str) -> tuple[str, int]:
    """将所有模块草稿提取的 proj CSS 合并注入到 prd <style> 中的 [PROJ-CSS] 占位。
    幂等：若已注入过（PROJ_CSS_START..END 之间已有内容），先清空再注入新内容。
    返回 (新 html, 注入的 CSS 字节数)。"""
    import re
    pattern = re.compile(
        r'(' + re.escape(PROJ_CSS_START) + r')(.*?)(' + re.escape(PROJ_CSS_END) + r')',
        re.DOTALL,
    )
    if not pattern.search(html):
        # 模板缺 [PROJ-CSS] 占位 = 模板退化（gen_scaffold 生成的骨架本就含此占位）；
        # 静默 return 会让 owner 模块草稿写的完整 CSS 被丢弃，故强制 ERROR 退出。
        # 不论 all_proj_css 是否为空都拦截：本期为空但模板坏，下期会立即触发问题。
        print(
            f"[ERROR] prd.html 缺少 [PROJ-CSS] 注入区占位"
            f"（{PROJ_CSS_START} ... {PROJ_CSS_END}），拼装中止以防 owner 模块草稿 CSS 被静默丢弃。\n"
            "  原因：prd_template.html 退化或 outputs/prd_*.html 被手改删除了占位。\n"
            "  修复：恢复模板中的 [PROJ-CSS-START/END] 标记，或重跑 gen_scaffold.py 重建骨架。",
            file=sys.stderr,
        )
        sys.exit(1)

    if not all_proj_css:
        # 无 proj CSS 需注入；保留占位空块，便于将来重跑
        new_html = pattern.sub(
            lambda m: f"{m.group(1)}\n    /* 本期无 proj 组件 CSS */\n    {m.group(3)}",
            html, count=1,
        )
        return new_html, 0

    replacement = (
        f"{PROJ_CSS_START}\n"
        f"{all_proj_css}\n"
        f"    {PROJ_CSS_END}"
    )
    new_html = pattern.sub(lambda m: replacement, html, count=1)
    return new_html, len(all_proj_css)


def _strip_inline_font_size_in_interaction_cards(html: str) -> tuple[str, int]:
    """NB-2A-01 选项 C 后处理（治"PM 写源 inline font-size 优先级 > CSS 致字号不
    统一"）：在 `.interaction-card` 范围内删除 inline `font-size:XXpx` 声明，
    保留其他 inline style 属性（color / padding / margin / line-height 等）。

    背景：commit f36dd9d（议题 2A C-4 表格化 + CSS 字体统一）后 .interaction-card
    + 内嵌 .c4-business-rules / .c4-data-scale / pre.gherkin 已通过 CSS 统一字号，
    但 PM 写源若残留 `style="font-size:12px;"` 等 inline 声明（CSS 优先级更高）
    会破坏视觉统一。本后处理只在 .interaction-card 范围内 strip font-size，
    保留 frame-wrapper 等其他位置 PM 故意写的 inline 字号。

    范围限定（nesting-aware）：
    - 用 div 深度计数找 `<div class="...interaction-card...">` 的对应 </div>
    - 仅对此范围内的 `style="..."` 属性做 font-size 剥离

    保留其他 inline style 属性：
    - `style="color:red; font-size:11px; padding:8px"` → `style="color:red; padding:8px"`
    - `style="font-size:12px"` → 整个 style 属性删除（空 style 无意义）
    - 多 font-size 同 style 一次性全清

    边界处理：
    - font-size 在 style 开头 / 结尾 / 中间均正确处理（含 ; 分隔符吸收）
    - 前后空白（空格 / 制表符）正确吸收，不留垃圾
    - 含空格变体（`font-size : 12px`）也匹配
    - 单引号 style（`style='...'`）暂不处理（PRD 模板统一双引号，未发现单引号样本）

    idempotent：重跑无新作用（已无 font-size → regex 不匹配）。

    返回 (新 html, 删除的 font-size 声明数)。
    """
    import re

    # 找 .interaction-card open 标签
    card_open_re = re.compile(
        r'<div[^>]+class="[^"]*\binteraction-card\b[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    div_open_re = re.compile(r'<div\b', re.IGNORECASE)
    div_close_re = re.compile(r'</div>', re.IGNORECASE)

    def _find_card_close(text: str, start: int) -> int:
        """nesting-aware 找到 interaction-card open 后对应的 </div> 位置（结束 idx）。
        depth=1 从 open 标签结束后开始；扫到 depth=0 时返回 </div> 的 end 位置。"""
        depth = 1
        pos = start
        while depth > 0 and pos < len(text):
            no = div_open_re.search(text, pos)
            nc = div_close_re.search(text, pos)
            if nc is None:
                return len(text)  # 兜底：截到 EOF
            if no is None or nc.start() < no.start():
                depth -= 1
                pos = nc.end()
                if depth == 0:
                    return nc.end()
            else:
                depth += 1
                pos = no.end()
        return pos

    # font-size 声明剥离：style 属性内任意 `font-size <ws>: <ws> <值>;?` 段
    # 值可含 px / em / rem / % / var(...) 等，匹配到分号或引号边界
    # 用 lookahead "?|;" 避免吃掉 closing quote
    fs_decl_re = re.compile(
        r'(?:(?<=;)\s*|(?<=")\s*|(?<=\')\s*)?'  # 前导空白可能跟在 ; 或引号后
        r'font-size\s*:\s*[^;"\']*'              # font-size: <值>（不跨过 ; / 引号）
        r'\s*;?',                                # 可选尾分号
        re.IGNORECASE,
    )
    # 简化版（更稳）：在 style 内 substring 操作
    fs_in_style_re = re.compile(
        r'font-size\s*:\s*[^;"\']*\s*;?',
        re.IGNORECASE,
    )

    total_removed = 0

    def _strip_fs_in_style(style_attr_text: str) -> tuple[str, int]:
        """处理单个 style="..." 属性整段（含 style="" 引号）。
        返回 (新 style 整段 OR 空串表示删除整个属性, 删除的声明数)。
        """
        # match: style="..."
        m_st = re.match(r'(style\s*=\s*")([^"]*)(")', style_attr_text, re.IGNORECASE)
        if not m_st:
            return style_attr_text, 0
        prefix, inner, suffix = m_st.group(1), m_st.group(2), m_st.group(3)
        removed_count = len(fs_in_style_re.findall(inner))
        if removed_count == 0:
            return style_attr_text, 0
        new_inner = fs_in_style_re.sub("", inner)
        # 清理双分号 / 残留前导/尾随分号 / 多余空白
        new_inner = re.sub(r';\s*;+', ';', new_inner)
        new_inner = re.sub(r'^\s*;+', '', new_inner)
        new_inner = re.sub(r'\s+', ' ', new_inner).strip()
        # 末尾可能残留 ; 是合法的（其他声明的分号），保留
        if not new_inner:
            # style 全空 → 删整个属性（含 leading 空格）
            return "", removed_count
        return f'{prefix}{new_inner}{suffix}', removed_count

    style_attr_re = re.compile(r'style\s*=\s*"[^"]*"', re.IGNORECASE)

    # 收集所有 card range，从后往前修改以保持 idx 稳定
    cards = []
    for m in card_open_re.finditer(html):
        end = _find_card_close(html, m.end())
        cards.append((m.start(), end))

    # 从后往前替换
    result = html
    for c_start, c_end in reversed(cards):
        card_text = result[c_start:c_end]
        # 在 card_text 内对每个 style="..." 做剥离
        new_parts = []
        last = 0
        card_removed = 0
        for sm in style_attr_re.finditer(card_text):
            new_parts.append(card_text[last:sm.start()])
            new_attr, n = _strip_fs_in_style(sm.group(0))
            card_removed += n
            if new_attr == "":
                # 删整个属性 — 同时吸收前面单个空白（如 ` style="..."` → ``）
                # 检查 new_parts 最后一段尾部是否是单空白
                if new_parts and new_parts[-1].endswith(' '):
                    new_parts[-1] = new_parts[-1][:-1]
                # 也可能是 tag 结尾紧贴 `style=`（无前导空格）— 不动
            else:
                new_parts.append(new_attr)
            last = sm.end()
        new_parts.append(card_text[last:])
        new_card_text = "".join(new_parts)
        if card_removed > 0:
            result = result[:c_start] + new_card_text + result[c_end:]
            total_removed += card_removed

    return result, total_removed


_TP_SUFFIX_RE = re.compile(r'-([TDC])\d+\b')


def _classify_tp_system(data_tp_value: str) -> str:
    """从 data-tp 末段提取触点系（T/D/C）。

    输入：`M01-P01-T01` / `M01-P01-D02` / `M01-P01-C03` / `M01-P01`（无末段）
    返回：`"T"` / `"D"` / `"C"` / `""`（无识别系）
    """
    if not data_tp_value:
        return ""
    m = _TP_SUFFIX_RE.search(data_tp_value)
    return m.group(1) if m else ""


def _inject_tp_marker_system_attr(html: str) -> tuple[str, int]:
    """SNB-MARKER-VISUAL-PREFIX-T-D-C 治本（议题 6）：对每个 `<span class="tp-marker">NN</span>`
    扫描邻近 data-tp 末段（T/D/C），注入 `data-tp-system="T"/"D"/"C"` 属性，
    供 prd_template.html CSS `.tp-marker[data-tp-system="X"]::before { content: "X"; }` 渲染
    视觉前缀，消除数字空间冲突（marker "01" 在 T01/D01/C01 三系都显示同字面 → 加前缀辨别）。

    邻近探测覆盖 4 种 PM 写源嵌套场景：

    场景 A：tp-marker 自身已带 data-tp
        `<span class="tp-marker" data-tp="M01-P01-T01">01</span>`
        → 自取 data-tp 末段。

    场景 B：tp-marker 直接父元素带 data-tp（含 tp-wrap 父级）
        `<X data-tp="M01-P01-T01"><span class="tp-marker">01</span></X>`
        `<span class="tp-wrap" data-tp="..."><span class="tp-marker">..</span></span>`
        → 用直接父开标签的 data-tp。

    场景 C：tp-marker 紧邻前兄弟带 data-tp（同级直系兄弟，最常见 PM 写法）
        `<button data-tp="M01-P01-T01">+ 新建</button><span class="tp-marker">01</span>`
        `<button data-tp="...">X</button><span class="tp-wrap"><span class="tp-marker">..</span></span>`
        → 用前兄弟的 data-tp（含 tp-wrap 包裹的情况，需先找 tp-marker 的 tp-wrap 父，再用 tp-wrap 的前兄弟）。

    场景 D：tp-marker 父元素紧邻前兄弟带 data-tp（父级为 tp-wrap，父级前兄弟带 data-tp）
        `<span data-tp="M01-P01-T03">A</span><span class="tp-wrap"><span class="tp-marker">03</span></span>`
        → 父 tp-wrap 的前兄弟带 data-tp（其实是场景 C 的 tp-wrap 包裹变体）。

    idempotent：重入幂等 — 已有 data-tp-system 属性的 tp-marker 跳过（regex 匹配 class
    但只在缺 data-tp-system 时注入）。无邻近 data-tp 命中（如悬空 marker）→ 不注入，
    precheck S4-34 / S4-36 兜底报告悬空 marker。

    返回 (新 html, 注入的 data-tp-system 属性数)。

    限制：
    - 仅扫 `<span class="tp-marker">` 字面（PM 写源主流形态，与 prd_template.html
      `.tp-marker` CSS 一致）
    - 跳过 class 含 tp-marker 但已有 data-tp-system 的（幂等）
    - 跳过无法识别 T/D/C 末段的 data-tp（如 `data-tp="M01-P01"`，无明确触点系）
    """
    import re as _re

    # tp-marker open 标签匹配（class 内含 tp-marker 字面 — 先粗匹配候选，再用 token check 精筛
    # 避免 has-substring 误匹配如 "tp-marker-active"）
    tp_marker_open_re = _re.compile(
        r'<span\b([^>]*\bclass\s*=\s*"([^"]*)"[^>]*)>',
        _re.IGNORECASE,
    )

    def _class_contains_tp_marker(class_value: str) -> bool:
        """class 属性值按空白拆 token，判定是否含完整 `tp-marker` token（非 substring）"""
        return "tp-marker" in class_value.split()

    # data-tp 属性提取
    data_tp_attr_re = _re.compile(
        r'\bdata-tp\s*=\s*"([^"]*)"',
        _re.IGNORECASE,
    )

    # 已有 data-tp-system 的 marker 跳过（幂等）
    data_tp_system_attr_re = _re.compile(
        r'\bdata-tp-system\s*=\s*"',
        _re.IGNORECASE,
    )

    # tp-wrap open 检测（用于场景 D：marker 在 tp-wrap 内部，需找 tp-wrap 的前兄弟）
    tp_wrap_open_re = _re.compile(
        r'<span\b[^>]*\bclass\s*=\s*"[^"]*\btp-wrap\b[^"]*"[^>]*>',
        _re.IGNORECASE,
    )

    # 任意开标签前兄弟搜索：从给定 idx 向前回溯，找最近一个完整 closing tag `</xxx>`
    # 该 closing tag 对应的 open 标签即前兄弟（简化策略：本场景多为简单平铺，无需深度匹配）
    # 实战策略：从 marker idx 向前搜最近的 `data-tp="..."`（不跨过 frame-card 边界）
    # — 简化为「向前回溯 1000 字符内任一 data-tp 末段」启发式
    LOOKBACK_WINDOW = 1500  # PM 写源单 frame 内典型间距 < 1500 字符；防跨 frame 串接

    # frame 边界字面（防跨 frame 邻近探测窜元素）
    FRAME_BOUNDARY_PATTERNS = [
        '<!-- [/FRAME',
        '<!-- [FRAME',
        '</section',
        '<section ',
    ]

    def _find_nearest_data_tp_backward(text: str, end_idx: int) -> str:
        """从 end_idx 向前回溯，找最近 data-tp 值（限 LOOKBACK_WINDOW 字符 + 不跨 frame 边界）。
        """
        start = max(0, end_idx - LOOKBACK_WINDOW)
        chunk = text[start:end_idx]
        # 跨 frame 边界判定：若窗内含边界字面，截断到该边界后
        for boundary in FRAME_BOUNDARY_PATTERNS:
            bi = chunk.rfind(boundary)
            if bi != -1:
                chunk = chunk[bi + len(boundary):]
        # 在窗内找最后一个 data-tp 值
        matches = list(data_tp_attr_re.finditer(chunk))
        if matches:
            return matches[-1].group(1)
        return ""

    injected = 0
    # 从后向前替换，保持 idx 稳定
    matches = list(tp_marker_open_re.finditer(html))
    if not matches:
        return html, 0

    result_parts: list[str] = []
    last_end = 0

    for m in matches:
        attrs_segment = m.group(1)  # 含 class= 在内的整 attrs
        class_value = m.group(2)

        # token-level 精筛：class 内必须含完整 `tp-marker` token（非 substring）
        if not _class_contains_tp_marker(class_value):
            continue

        # 幂等：已有 data-tp-system 跳过
        if data_tp_system_attr_re.search(attrs_segment):
            continue

        # 场景 A：tp-marker 自身带 data-tp
        self_dt_m = data_tp_attr_re.search(attrs_segment)
        if self_dt_m:
            system = _classify_tp_system(self_dt_m.group(1))
        else:
            # 场景 B/C/D：向前回溯找邻近 data-tp
            # （邻近策略统一：从 marker 标签起始向前回溯 LOOKBACK_WINDOW 字符）
            nearest = _find_nearest_data_tp_backward(html, m.start())
            system = _classify_tp_system(nearest)

        if not system:
            continue  # 无识别系（如悬空 marker）— 不注入，precheck 兜底

        # 注入 data-tp-system 属性到 attrs 段末尾
        new_attrs = attrs_segment.rstrip() + f' data-tp-system="{system}"'
        new_open = f'<span{new_attrs}>'

        # 累积输出
        result_parts.append(html[last_end:m.start()])
        result_parts.append(new_open)
        last_end = m.end()
        injected += 1

    if injected == 0:
        return html, 0

    result_parts.append(html[last_end:])
    return "".join(result_parts), injected


# ── 议题 12 P3 / SSOT #69 C-2.B 无 C 触点绑定场景派生（方案 c）─────────────────
# 治"M10 admin-default 等纯字段表场景规范盲点 — PM 不知 sub-title 该写什么":
# `prd_expression_standard.md §四 C-2.B` schema 假设每 C 行 1 张 D 子表（sub-title
# 含 C 触点 ID 如「字段说明 — C01 项目卡片」），但实际产品中存在「页面无 C 触点
# 绑定（如纯字段管理页 / 系统设置 / 空态 / 错误态）但仍需展示字段说明」的场景，
# 此时 PM 既无 C 触点 ID 可填，也未必知道应回退「字段说明 — 数据展示」等通用名。
# 派生规则：检测 interaction-card 内 C-2.B 字段表前 `<div class="data-sub-title">`
# 缺失 + 该 card 所属 frame 无 C 触点绑定 → 从 frame section 派生页面名注入
# 「字段说明 — {派生名}」sub-title（与 S4-59 容器锁定 regex 兼容）。

# C-2.B 字段子表 thead 字面特征（与 precheck S4-59 _C2B_THEAD_COLS 同源）：
# `D 触点 ID` + `字段名` + `接口字段` + `显示格式` + `空值处理`（5 列齐全为强信号）
_C2B_TABLE_THEAD_RE = re.compile(
    r'<thead>\s*<tr>\s*(?:<th[^>]*>[^<]*</th>\s*){5}</tr>\s*</thead>',
    re.IGNORECASE,
)
# 强信号：thead 内含 `D 触点 ID` + `字段名`（避免误命中 C-1 列表回显说明 / C-3 触点表）
# 议题 22 精度防御（2026-06-05）：把扫描范围严格锁定在单个 `<thead>...</thead>` 内部，
# 禁止跨 thead 匹配（治"DOTALL 跨 thead 把 C-2.A 占位 thead 当 C-2.B 锚点"漂移）。
_C2B_THEAD_SIGNAL_RE = re.compile(
    r'<thead>(?:(?!</thead>).)*?D\s*触点\s*ID(?:(?!</thead>).)*?字段名(?:(?!</thead>).)*?</thead>',
    re.IGNORECASE | re.DOTALL,
)

# 检测 C-2.B 字段说明 sub-title 已存在（与 precheck S4-59 _C2B_SUB_TITLE_RE 同源）
_C2B_SUBTITLE_PRESENT_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>[^<]*字段说明[^<]*</div>',
    re.IGNORECASE,
)

# C 触点绑定检测：`data-tp="...-C\d+"` 命中即视为有 C 触点绑定（不派生）
_C_TP_BINDING_RE = re.compile(r'\bdata-tp\s*=\s*"[^"]*-C\d+"', re.IGNORECASE)

# frame section 元数据提取：`<span class="page-name">XXX</span>`
_PAGE_NAME_SPAN_RE = re.compile(
    r'<span\s+class\s*=\s*"[^"]*\bpage-name\b[^"]*"[^>]*>([^<]+)</span>',
    re.IGNORECASE,
)
# card-title 状态名提取：`<div class="card-title">交互说明 — XXX</div>` 抽取 em-dash 后
_CARD_TITLE_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bcard-title\b[^"]*"[^>]*>([^<]+)</div>',
    re.IGNORECASE,
)
# section open 标签 + id 提取（含 H-MXX-PYY-state 形态，回退 MXX-PYY 作派生名）
_SECTION_ID_RE = re.compile(
    r'<section\s+id\s*=\s*"(H-(M\d+-P\d+)[^"]*)"\s+class\s*=\s*"[^"]*\bproto-section\b',
    re.IGNORECASE,
)


def _derive_subtitle_name(section_html: str, card_html: str, section_id: str) -> str:
    """议题 12 派生命名（优先级 B → B 兜底 → A → C 终极兜底）。

    输入：
    - section_html：proto-section 完整 HTML（含 section-header / state-chips / frame / interaction-card）
    - card_html：当前待派生 sub-title 的 interaction-card HTML
    - section_id：section 的 id（如 `H-M10-P13-admin-default`）

    派生优先级：
    - **B（优先）**：从 section 的 `<span class="page-name">XXX</span>` 提取页面名
      → `字段说明 — XXX`（语义最明确，PM 已在 section-header 填）
    - **B 兜底**：从 card-title `<div class="card-title">交互说明 — STATE</div>` 抽 em-dash
      后状态名 → `字段说明 — STATE`（page-name 缺失时，状态名仍有语义）
    - **A**：从 section id 抽 `MXX-PYY` → `字段说明 — MXX-PYY`（无 page-name 也无 card-title）
    - **C（终极兜底）**：`字段说明 — 数据展示`（极端缺锚场景，与 §四 C-2.B 通用语义对齐）

    返回派生的 sub-title 全文本（含 `字段说明 — ` 前缀，与 S4-59 容器锁定 regex 兼容）。
    """
    # 优先级 B：page-name
    m_pn = _PAGE_NAME_SPAN_RE.search(section_html)
    if m_pn:
        name = m_pn.group(1).strip()
        if name:
            return f"字段说明 — {name}"
    # 优先级 B 兜底：card-title 状态名（`交互说明 — XXX`）
    m_ct = _CARD_TITLE_RE.search(card_html)
    if m_ct:
        title_text = m_ct.group(1).strip()
        # 抽取 em-dash 后状态名（兼容 — / -- / - 三种分隔符）
        for sep in ("—", "──", "--"):
            if sep in title_text:
                state_name = title_text.split(sep, 1)[1].strip()
                if state_name:
                    return f"字段说明 — {state_name}"
    # 优先级 A：section id 抽 MXX-PYY
    m_sid = _SECTION_ID_RE.search(section_html)
    if m_sid:
        mp = m_sid.group(2)  # MXX-PYY
        if mp:
            return f"字段说明 — {mp}"
    # 优先级 C 终极兜底
    return "字段说明 — 数据展示"


def _inject_c2b_subtitle_for_no_c_binding(html: str) -> tuple[str, int]:
    r"""议题 12 P3 / SSOT #69 派生（方案 c）：为「无 C 触点绑定 + 字段表前缺 C-2.B
    sub-title」的 interaction-card 注入派生 `<div class="data-sub-title">字段说明 — XXX</div>`，
    治 PM 写源在纯字段表场景下的规范盲点。

    扫描范围（nesting-aware）：
    1. 用 `_SECTION_ID_RE` 找所有 `<section class="proto-section">` 边界
    2. 在每个 section 内找所有 `<div class="interaction-card">` 范围（同
       `_strip_inline_font_size_in_interaction_cards` nesting-aware depth-1 扫描）
    3. 对每个 card：
       - 跳过：card 内已含 `字段说明` sub-title（idempotent，PM 写源保留 / 重跑无副作用）
       - 跳过：card 所在 section（含 frame body）内含 `data-tp="...-C\d+"`（有 C 触点
         绑定，规范原 schema 适用，不派生）
       - 命中：card 内含 C-2.B 字段子表 thead（5 列含「D 触点 ID」+「字段名」强信号）
         但 sub-title 缺失 → 在该 table 前注入派生 sub-title
    4. 派生命名委托 `_derive_subtitle_name`（优先级 B → A → C）

    idempotent：已有 `字段说明` sub-title → 不动 + 不计数；重入幂等。
    不破坏既有写源：PM 手填如「字段说明 — C01 项目卡片」/「字段说明 — 字段列表项 (...) 」
    形态保留（S4-59 容器锁定 regex 已覆盖派生形态）。

    议题 22 / NB-WE-2A-R7-01 P3 精度防御（2026-06-05）：派生 sub-title 必须紧贴 C-2.B
    `<table>` open，不能夹在 C-2.A 占位表 / 正文段（`</p>` / `</ul>` / `</ol>` / `</pre>` /
    其他 `</table>`）之前。不紧贴时按 fallback 仍插入 `<table>` 前（保持派生有效），
    stderr WARN 提示 PM 复核结构。本仓私域 R8 L1 已闭环，仅作长期跨产品防御。

    返回 (新 html, 注入的 sub-title 数)。
    """
    import re as _re

    # 1. 找所有 section 范围（proto-section 边界）
    section_open_re = _re.compile(
        r'<section\s+id\s*=\s*"[^"]*"\s+class\s*=\s*"[^"]*\bproto-section\b[^"]*"[^>]*>',
        _re.IGNORECASE,
    )
    section_close_token = '</section>'

    # 2. interaction-card open（同 _strip_inline_font_size_in_interaction_cards）
    card_open_re = _re.compile(
        r'<div[^>]+class="[^"]*\binteraction-card\b[^"]*"[^>]*>',
        _re.IGNORECASE,
    )
    div_open_re = _re.compile(r'<div\b', _re.IGNORECASE)
    div_close_re = _re.compile(r'</div>', _re.IGNORECASE)

    def _find_card_close(text: str, start: int) -> int:
        """nesting-aware 找 interaction-card open 后对应的 </div> 结束 idx（同 strip_font_size）"""
        depth = 1
        pos = start
        while depth > 0 and pos < len(text):
            no = div_open_re.search(text, pos)
            nc = div_close_re.search(text, pos)
            if nc is None:
                return len(text)
            if no is None or nc.start() < no.start():
                depth -= 1
                pos = nc.end()
                if depth == 0:
                    return nc.end()
            else:
                depth += 1
                pos = no.end()
        return pos

    def _find_section_close(text: str, start: int) -> int:
        """简化：找 section open 后第一个 `</section>`（proto-section 无嵌套 section）"""
        idx = text.find(section_close_token, start)
        return idx + len(section_close_token) if idx != -1 else len(text)

    # 收集所有 section 范围
    sections: list[tuple[int, int, str]] = []  # (start, end, section_id)
    for sm in section_open_re.finditer(html):
        sec_end = _find_section_close(html, sm.end())
        # 提取 section id（同 _SECTION_ID_RE，但已通过 section_open_re 命中）
        id_m = _re.search(r'\bid\s*=\s*"([^"]*)"', sm.group(0))
        section_id = id_m.group(1) if id_m else ""
        sections.append((sm.start(), sec_end, section_id))

    if not sections:
        return html, 0

    # 从后往前修改以保持 idx 稳定（同 _strip_inline_font_size）
    result = html
    total_injected = 0

    for sec_start, sec_end, section_id in reversed(sections):
        section_html = result[sec_start:sec_end]

        # 跳过：本 section 含 C 触点绑定 → 走原 schema，不派生
        if _C_TP_BINDING_RE.search(section_html):
            continue

        # 收集 section 内所有 interaction-card 范围
        cards: list[tuple[int, int]] = []
        for cm in card_open_re.finditer(section_html):
            card_end = _find_card_close(section_html, cm.end())
            cards.append((cm.start(), card_end))

        if not cards:
            continue

        # 从后往前处理 card（保持 section_html 内 idx 稳定）
        new_section_html = section_html
        section_injected = 0
        for c_start, c_end in reversed(cards):
            card_html = new_section_html[c_start:c_end]

            # 跳过：card 内已含「字段说明」sub-title（idempotent）
            if _C2B_SUBTITLE_PRESENT_RE.search(card_html):
                continue

            # 命中条件：card 内含 C-2.B 字段子表（5 列含「D 触点 ID」+「字段名」强信号）
            # 用 thead 信号字面（thead 内含「D 触点 ID」+「字段名」）精筛
            thead_m = _C2B_THEAD_SIGNAL_RE.search(card_html)
            if not thead_m:
                continue

            # 找该 thead 所属 `<table>` 的 open 标签 idx（向前回溯）
            # thead 必在 <table> 内（HTML 良构），向前找最近 `<table` open
            thead_start = thead_m.start()
            table_open_search = list(_re.finditer(r'<table\b[^>]*>', card_html[:thead_start], _re.IGNORECASE))
            if not table_open_search:
                continue
            table_open_idx = table_open_search[-1].start()

            # 议题 22 / NB-WE-2A-R7-01 P3 精度防御：派生 sub-title 必须紧贴 C-2.B 字段表，
            # 不能夹在 C-2.A 占位表前或其他元素中间。
            #
            # 检测：从 `<table>` open 向前回溯，跳过 whitespace 后命中的最近兄弟元素：
            #   - 紧贴允许的前置元素（不告警）：
            #     * card 内部起点（card open `>` 紧贴）
            #     * `<div class="card-title">…</div>` close（卡片标题紧贴 OK）
            #     * `<div class="state-diff-note">…</div>` close（C-0 差异说明）
            #     * `<div class="data-sub-title">…</div>` close（PM 自造 sub-title 如「卡片字段说明」）
            #   - 紧贴不可达（告警 + 回退到原插入逻辑）：
            #     * 命中其他 `</table>` close（C-2.A 占位表夹在前 / 其他字段表夹在前）
            #     * 命中 `</p>`、`</ul>`、`</ol>` 等正文段（含 PM 写的说明段）
            #
            # 检测结果用于决策：
            #   - 紧贴：直接在 `<table>` open 前插入（原行为）
            #   - 不紧贴：仍在 `<table>` open 前插入（保持派生有效），但 stderr WARN 提示 PM 检查
            preceding_text = card_html[:table_open_idx].rstrip()
            # 取 preceding_text 末尾 1KB 做兄弟元素探测（避免大 card 全扫）
            tail_snippet = preceding_text[-1024:]
            # 排查"紧贴不可达"信号：tail 末尾去掉 whitespace 后是否是其他 `</table>` 或正文段 close
            #   - 末尾 `</table>` → C-2.A 占位表夹前
            #   - 末尾 `</p>` / `</ul>` / `</ol>` / `</pre>` → 正文段夹前
            adjacency_violation_re = _re.compile(
                r'</(?:table|p|ul|ol|pre)>\s*$',
                _re.IGNORECASE,
            )
            is_not_adjacent = bool(adjacency_violation_re.search(tail_snippet))

            # 派生 sub-title 名（委托 _derive_subtitle_name）
            subtitle_name = _derive_subtitle_name(section_html, card_html, section_id)
            subtitle_block = f'<div class="data-sub-title">{subtitle_name}</div>\n'

            if is_not_adjacent:
                # 紧贴不可达 → fallback 仍按原插入逻辑（保持派生有效），WARN 提示 PM 检查
                # 提取近端 close 标签字面作 WARN context（前 80 字符）
                preceding_tail_for_msg = tail_snippet[-80:].replace('\n', ' ')
                print(
                    f"[WARN] _inject_c2b_subtitle_for_no_c_binding 议题 22 精度防御："
                    f"section {section_id!r} 派生 sub-title 「{subtitle_name}」未能紧贴 C-2.B 字段表"
                    f"（C-2.B `<table>` 与前置元素之间有夹杂内容；末端 80 字符：…{preceding_tail_for_msg}）；"
                    f"按 fallback 仍插入 `<table>` 前，建议 PM 复核「卡片字段说明」与 C-2.B 字段表之间结构。",
                    file=sys.stderr,
                )

            # 注入：在 <table> open 前插入 subtitle_block
            new_card_html = card_html[:table_open_idx] + subtitle_block + card_html[table_open_idx:]
            new_section_html = new_section_html[:c_start] + new_card_html + new_section_html[c_end:]
            section_injected += 1

        if section_injected > 0:
            result = result[:sec_start] + new_section_html + result[sec_end:]
            total_injected += section_injected

    return result, total_injected


# ── C-1 / C-2 / C-3 真无内容豁免占位派生（NB-R3-01 / 议题 15）─────────────────
# 治"interaction-card 缺 C-1 列表回显 / C-2 数据展示 / C-3 触点交互 sub-title"
# （私域主页 143 卡实证：C-1 缺 33 / C-2 缺 72 / C-3 缺 1 = 106 处）。
# 规范 §四 区块 C 要求 4 子区块（C-0/C-1/C-2/C-3）+ C-4 业务契约固定顺序，无内容
# 时须注明「本帧无 XXX」而非省略。派生层防御兜底：缺 sub-title → 注入占位
# `<div class="data-sub-title">XXX说明</div><p>本帧无XXX。</p>`
# （与 S4-58/59/60 二级判定容器锁定 regex 兼容；与 precheck S4-64 sub-title 顺序
# 校验协同）。
#
# 设计要点：
# - idempotent：已含对应 sub-title 容器（`<div class="data-sub-title">…X说明…</div>`）
#   → 不动 + 不计数
# - 插入位置：紧贴 interaction-card 内 `<div class="card-title">…</div>` 之后（C-0
#   `.state-diff-note` 之前或之后均合规——sub-title 占位 + 1 段 `<p>` 不破坏既存内容）
# - 插入顺序：本 batch 内若多个缺 → C-1 → C-2 → C-3 依次注入（与规范 §四 顺序一致）
# - 不动有内容的卡：通过 sub-title 容器锁定 regex 精确判定，避免误命中 narrative
#   `**列表回显说明**` 等 false signal

_C1_SUBTITLE_PRESENT_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>[^<]*列表回显说明[^<]*</div>',
    re.IGNORECASE,
)
_C2_SUBTITLE_PRESENT_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>[^<]*数据展示说明[^<]*</div>',
    re.IGNORECASE,
)
_C3_SUBTITLE_PRESENT_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>[^<]*触点交互说明[^<]*</div>',
    re.IGNORECASE,
)

# 卡片字段说明（PM 自造 sub-title）→ 视作隐式 C-2 段落，配合议题 18 C-2.A 索引层派生
_C2_CARD_FIELD_DESC_SUBTITLE_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bdata-sub-title\b[^"]*"[^>]*>[^<]*卡片字段说明[^<]*</div>',
    re.IGNORECASE,
)

# card-title 容器（用于定位插入锚点）
_INTERACTION_CARD_TITLE_RE = re.compile(
    r'<div\s+class\s*=\s*"[^"]*\bcard-title\b[^"]*"[^>]*>[^<]*</div>',
    re.IGNORECASE,
)

# C-4 派生区块开始标记（占位须放在 C-4 之前）
_C4_START_MARKER_RE = re.compile(r'<!--\s*\[C4-START:[^\]]*\]', re.IGNORECASE)


def _find_card_close_idx(text: str, open_end: int) -> int:
    """nesting-aware 找 interaction-card open 后对应的 </div> 结束 idx（同 _inject_c2b 内嵌函数）"""
    import re as _re
    div_open_re = _re.compile(r'<div\b', _re.IGNORECASE)
    div_close_re = _re.compile(r'</div>', _re.IGNORECASE)
    depth = 1
    pos = open_end
    while depth > 0 and pos < len(text):
        no = div_open_re.search(text, pos)
        nc = div_close_re.search(text, pos)
        if nc is None:
            return len(text)
        if no is None or nc.start() < no.start():
            depth -= 1
            pos = nc.end()
            if depth == 0:
                return nc.end()
        else:
            depth += 1
            pos = no.end()
    return pos


def _iter_interaction_card_ranges(html: str):
    """生成 (open_start, body_end_exclusive, close_end) — 即 interaction-card 范围三元组

    open_start：`<div class="interaction-card">` 开始位置
    body_end_exclusive：最后一个 `</div>` 起始（即 card 内容结束）
    close_end：`</div>` 结束位置（含）

    用于精确定位 card 内插入点（body 末尾 + close 前）。
    """
    import re as _re
    card_open_re = _re.compile(
        r'<div[^>]+class="[^"]*\binteraction-card\b[^"]*"[^>]*>',
        _re.IGNORECASE,
    )
    for m in card_open_re.finditer(html):
        open_start = m.start()
        open_end = m.end()
        close_end = _find_card_close_idx(html, open_end)
        # body_end_exclusive：close </div> 的起始 idx（向前回溯 6 字符）
        body_end = close_end - len('</div>')
        if body_end < open_end:
            body_end = open_end
        yield (open_start, open_end, body_end, close_end)


def _compute_card_insert_anchor(card_inner: str, subtitle_type: str = None) -> int:
    """在 card_inner（card open 后 / close 前的 body 区段）找占位插入锚点。

    议题 19 / NB-WE-2A-R5-01 — 串联查找优先级链（治"C-1/C-2/C-3 后注入堆到前面致顺序乱"）：

    subtitle_type 维度（C-1/C-2/C-3 注入方传入自身类型）：
    - "C-1" → 找 C-2 sub-title → C-3 sub-title → C-4 marker → body 末尾（取最早 anchor）
    - "C-2" → 找 C-3 sub-title → C-4 marker → body 末尾
    - "C-3" → 找 C-4 marker → body 末尾（同议题 15 现态）
    - None  → 旧行为 fallback（C-4 marker → body 末尾），向后兼容其他潜在调用方

    sub-title 检测复用议题 15 容器锁定 regex（`<div class="data-sub-title">{X 文案}</div>`），
    避免误命中 narrative `**列表回显说明**` 等 false signal。

    返回相对 card_inner 起始的 idx。

    Why C-1 找 C-2/C-3，C-2 找 C-3：
    PM 已有 C-3（仅 C-3 场景）时旧 anchor 一律是 C-4 marker → C-1/C-2 都插到 C-3 之后变成
    `C-3 < C-1 < C-2 < C-4`（乱）。新链路 C-1 找到 C-2 anchor 或 C-3 anchor → 插在最早 sub-title 之前 →
    顺序恢复为 `C-1 < C-2 < C-3 < C-4`。
    """
    candidates = []

    if subtitle_type == "C-1":
        # C-1 应排在 C-2 / C-3 之前
        m_c2 = _C2_SUBTITLE_PRESENT_RE.search(card_inner)
        if m_c2:
            candidates.append(m_c2.start())
        # 议题 18 C-2.A 派生路径：PM 自造「卡片字段说明」也视作 C-2 段（C-1 应排其前）
        m_c2_cfd = _C2_CARD_FIELD_DESC_SUBTITLE_RE.search(card_inner)
        if m_c2_cfd:
            candidates.append(m_c2_cfd.start())
        m_c3 = _C3_SUBTITLE_PRESENT_RE.search(card_inner)
        if m_c3:
            candidates.append(m_c3.start())
    elif subtitle_type == "C-2":
        # C-2 应排在 C-3 之前
        m_c3 = _C3_SUBTITLE_PRESENT_RE.search(card_inner)
        if m_c3:
            candidates.append(m_c3.start())
    # C-3 / None：仅 C-4 marker + body 末尾兜底（同议题 15 现态）

    # C-4 marker 兜底（所有 subtitle_type 均适用）
    m_c4 = _C4_START_MARKER_RE.search(card_inner)
    if m_c4:
        candidates.append(m_c4.start())

    if candidates:
        return min(candidates)
    return len(card_inner)


def _inject_c_subtitle_placeholder(
    html: str,
    present_re: re.Pattern,
    subtitle_text: str,
    placeholder_paragraph: str,
    subtitle_type: str = None,
) -> tuple[str, int]:
    """通用 C-X sub-title 占位注入辅助。

    扫所有 interaction-card：缺对应 sub-title 容器 → 在 anchor 位置插入
    `<div class="data-sub-title">{subtitle_text}</div>\n<p>{placeholder_paragraph}</p>\n`

    议题 19 / NB-WE-2A-R5-01：subtitle_type 透传给 `_compute_card_insert_anchor` 启用串联
    查找（C-1 → C-2/C-3/C-4；C-2 → C-3/C-4；C-3 → C-4；治后注入堆到前面致顺序乱）。

    idempotent：已含 → 跳过。从后往前修改以保持 idx 稳定。
    返回 (新 html, 注入数)。
    """
    ranges = list(_iter_interaction_card_ranges(html))
    if not ranges:
        return html, 0

    block = (
        f'<div class="data-sub-title">{subtitle_text}</div>\n'
        f'<p>{placeholder_paragraph}</p>\n'
    )

    result = html
    injected = 0
    # 从后往前
    for open_start, open_end, body_end, close_end in reversed(ranges):
        card_inner = result[open_end:body_end]
        if present_re.search(card_inner):
            continue  # idempotent
        anchor_in_inner = _compute_card_insert_anchor(card_inner, subtitle_type)
        new_inner = (
            card_inner[:anchor_in_inner] + block + card_inner[anchor_in_inner:]
        )
        result = result[:open_end] + new_inner + result[body_end:]
        injected += 1
    return result, injected


def _inject_c1_placeholder_when_missing(html: str) -> tuple[str, int]:
    """NB-R3-01 / 议题 15 — interaction-card 缺 C-1「列表回显说明」占位注入。

    检测 interaction-card 内 `<div class="data-sub-title">列表回显说明</div>` 容器
    缺失时，注入占位 sub-title + `<p>本帧无列表。</p>`（与 C-1 既有「本帧无列表」
    豁免文案一致，precheck S4-57 会因「本帧无列表」字面而跳过 4 行目校验）。

    议题 19：传 subtitle_type="C-1" 启用串联查找（C-1 应排在 C-2/C-3/C-4 之前）。

    idempotent：已含 sub-title 容器 → 跳过 + 不计数。
    返回 (新 html, 注入数)。
    """
    return _inject_c_subtitle_placeholder(
        html,
        _C1_SUBTITLE_PRESENT_RE,
        "列表回显说明",
        "本帧无列表。",
        subtitle_type="C-1",
    )


def _inject_c2_placeholder_when_missing(html: str) -> tuple[str, int]:
    """NB-R3-01 / 议题 15 — interaction-card 缺 C-2「数据展示说明」占位注入。

    检测 interaction-card 内 `<div class="data-sub-title">数据展示说明</div>` 容器
    缺失时，注入占位 sub-title + `<p>本帧无数据展示。</p>`（与既有「本帧无数据展示」
    豁免文案一致，precheck S4-58 会因该字面跳过 6 列校验）。

    议题 19：传 subtitle_type="C-2" 启用串联查找（C-2 应排在 C-3/C-4 之前）。

    idempotent：①已含 `数据展示说明` sub-title 容器 → 跳过；②含 `卡片字段说明`
    PM 自造 sub-title（议题 18 C-2.A 派生路径覆盖）→ 跳过避免双段并存。
    返回 (新 html, 注入数)。
    """
    # 复用辅助但二级判定：含 `卡片字段说明` 也视为已存在（让议题 18 C-2.A 索引派生兜底）
    ranges = list(_iter_interaction_card_ranges(html))
    if not ranges:
        return html, 0

    block = (
        '<div class="data-sub-title">数据展示说明</div>\n'
        '<p>本帧无数据展示。</p>\n'
    )

    result = html
    injected = 0
    for open_start, open_end, body_end, close_end in reversed(ranges):
        card_inner = result[open_end:body_end]
        if _C2_SUBTITLE_PRESENT_RE.search(card_inner):
            continue
        if _C2_CARD_FIELD_DESC_SUBTITLE_RE.search(card_inner):
            continue  # 让 议题 18 C-2.A 派生兜底
        anchor_in_inner = _compute_card_insert_anchor(card_inner, "C-2")
        new_inner = (
            card_inner[:anchor_in_inner] + block + card_inner[anchor_in_inner:]
        )
        result = result[:open_end] + new_inner + result[body_end:]
        injected += 1
    return result, injected


def _inject_c3_placeholder_when_missing(html: str) -> tuple[str, int]:
    """NB-R3-01 / 议题 15 — interaction-card 缺 C-3「触点交互说明」占位注入。

    检测 interaction-card 内 `<div class="data-sub-title">触点交互说明</div>` 容器
    缺失时，注入占位 sub-title + `<p>本帧无交互触点。</p>`（与 C-3 既有「本帧无
    交互触点」豁免文案一致，precheck S4-60 会因该字面跳过 6 列校验）。

    议题 19：传 subtitle_type="C-3" 启用串联查找（C-3 仅需排在 C-4 marker 之前，
    同议题 15 现态）。

    idempotent：已含 sub-title 容器 → 跳过 + 不计数。
    返回 (新 html, 注入数)。
    """
    return _inject_c_subtitle_placeholder(
        html,
        _C3_SUBTITLE_PRESENT_RE,
        "触点交互说明",
        "本帧无交互触点。",
        subtitle_type="C-3",
    )


# ── 议题 18 / NB-R4-01 C-2.A 索引层派生兜底（56 处「卡片字段说明」C-2.A 缺失）─
# 治 PM 自造 sub-title「卡片字段说明」+ 直接给字段表（C-2.B 形态变体）但缺少 C-2.A
# C 单元清单 6 列索引层（私域主页 M02/M03/M05/M08 实证 56 处）。规范 §四 C-2 要求
# 索引层 + 详情层双层结构，缺索引层 → C-2 信息架构残缺 + S4-58 校验失效。
# 治本方向：检测「卡片字段说明」sub-title + C-2.A 索引表缺失 → 注入 6 列占位表
# （列名与规范一致：C 触点 ID / 单元名称 / 是否封装为组件 / 渲染时机 / 跨平台差异 /
# 关联 T 触点；行内容统一 PM placeholder「（PM 待补完整 schema）」），让 PM 后续
# 整改时填入真实业务内容。

_C2A_TABLE_THEAD_SIGNAL_RE = re.compile(
    r'<thead>[^<]*(?:<[^>]+>[^<]*)*?C\s*触点\s*ID[^<]*(?:<[^>]+>[^<]*)*?单元名称',
    re.IGNORECASE | re.DOTALL,
)


def _inject_c2a_index_for_card_field_description(html: str) -> tuple[str, int]:
    """议题 18 / NB-R4-01 — 为「卡片字段说明」+ C-2.A 索引层缺失的 interaction-card
    注入 C-2.A 索引层占位表（6 列 schema + 占位行）。

    触发条件（必须全部满足）：
    1. interaction-card 内含 `<div class="data-sub-title">卡片字段说明</div>` PM 自造
       sub-title
    2. interaction-card 内**无** C-2.A 索引层 thead（强信号「C 触点 ID」+「单元名称」）
    3. interaction-card 内**无** `<div class="data-sub-title">数据展示说明</div>` 标准
       sub-title（避免双段并存）

    注入位置：紧贴「卡片字段说明」sub-title **之前**插入「数据展示说明」sub-title +
    6 列 C-2.A 索引表占位。注入后形态：
        <div class="data-sub-title">数据展示说明</div>
        <table>...6 列 thead...<tbody>（PM 待补完整 schema）...</tbody></table>
        <div class="data-sub-title">卡片字段说明</div>     ← PM 原写源保留
        <table>...PM 写源字段表...</table>

    占位内容：tbody 单行 6 列全部「（PM 待补完整 schema）」，PM 整改时按真实
    展示单元逐行填入。

    idempotent：已含 C-2.A 索引层 thead 强信号 → 跳过。
    返回 (新 html, 注入数)。
    """
    ranges = list(_iter_interaction_card_ranges(html))
    if not ranges:
        return html, 0

    placeholder_text = "（PM 待补完整 schema）"
    c2a_block = (
        '<div class="data-sub-title">数据展示说明</div>\n'
        '<table>\n'
        '<thead><tr>'
        '<th>C 触点 ID</th>'
        '<th>单元名称</th>'
        '<th>是否封装为组件</th>'
        '<th>渲染时机</th>'
        '<th>跨平台差异</th>'
        '<th>关联 T 触点</th>'
        '</tr></thead>\n'
        '<tbody>\n'
        f'<tr><td>{placeholder_text}</td>'
        f'<td>{placeholder_text}</td>'
        f'<td>{placeholder_text}</td>'
        f'<td>{placeholder_text}</td>'
        f'<td>{placeholder_text}</td>'
        f'<td>{placeholder_text}</td></tr>\n'
        '</tbody>\n'
        '</table>\n'
    )

    result = html
    injected = 0
    for open_start, open_end, body_end, close_end in reversed(ranges):
        card_inner = result[open_end:body_end]

        # 触发条件 1：含「卡片字段说明」PM 自造 sub-title
        cfd_m = _C2_CARD_FIELD_DESC_SUBTITLE_RE.search(card_inner)
        if not cfd_m:
            continue

        # 触发条件 3：避免双段并存 — 已含「数据展示说明」标准 sub-title 跳过
        if _C2_SUBTITLE_PRESENT_RE.search(card_inner):
            continue

        # 触发条件 2：无 C-2.A 索引层 thead 强信号
        if _C2A_TABLE_THEAD_SIGNAL_RE.search(card_inner):
            continue

        # 注入：紧贴「卡片字段说明」sub-title 之前插入 C-2.A 索引表占位
        insert_idx = cfd_m.start()
        new_inner = (
            card_inner[:insert_idx] + c2a_block + card_inner[insert_idx:]
        )
        result = result[:open_end] + new_inner + result[body_end:]
        injected += 1
    return result, injected


def assemble_prd(data: dict) -> None:
    product = data["product"]
    prd_path = OUTPUT_DIR / f"prd_{product}_latest.html"

    if not prd_path.exists():
        print(f"[ERROR] prd 骨架不存在：{prd_path}", file=sys.stderr)
        sys.exit(1)

    # 手改保护：比对 sidecar fingerprint
    force_overwrite = "--force-overwrite" in sys.argv
    if force_overwrite:
        _backup_output_before_overwrite(prd_path, "prd")  # B1 SSOT #80
    _check_no_manual_drift(prd_path, product, "prd", force_overwrite)

    # T1-1：检测主模板升级（issue 2026-05-05_2243 根因 1）
    current_template_hash = _compute_template_hash()
    _check_template_drift(prd_path, current_template_hash)

    modules = data["modules"]
    draft_paths = check_drafts(modules, "prd_", "html")

    html = prd_path.read_text(encoding="utf-8")

    # NB-WE-20 frame-card isolation 派生漂移修复（issue 2026-05-12 下游 # 14）：
    # 全量重读 template `<style>` 段覆盖 outputs/prd 第一个 `<style>` 块,
    # 确保 template CSS 改动（如 .frame-card { isolation: isolate; }）自动同步到派生层。
    # 必须在所有后续 inject 操作之前,因 inject_fallback_css 等会向 `<style>` 内插入新块。
    html, style_overwritten = _overwrite_first_style_from_template(html)
    if style_overwritten:
        print("[OK] 已从 prd_template.html 重读 `<style>` 段覆盖派生层（NB-WE-20）")

    # WE-ASM（2026-05-16 下游报告）：同理重读 template `<script>` 段（mermaid CDN
    # 外链 + 尾部内联块）覆盖派生层，根除"template JS 改动后 outputs/prd 不跟进"
    # 硬漂移面（与 NB-WE-20 的 `<style>` 同模式，JS 维度补盖）。
    html, scripts_overwritten = _overwrite_scripts_from_template(html)
    if scripts_overwritten:
        print("[OK] 已从 prd_template.html 重读 `<script>` 段（mermaid CDN + 内联）覆盖派生层（WE-ASM）")

    # 拼装前先嵌入 / 更新 template-hash 注释,后续修改 html 都基于已含注释版本
    html = _inject_template_hash(html, current_template_hash)
    total_frames = 0
    # 议题 12 NB-WE-12 治本（2026-06-07）：FRAME 占位缺失时 WARN + skip 累计统计
    skipped_frames: list[str] = []

    # SSOT #67/#68 派生准备：读 spec.md 作为 .4B/.5B/.7/F-xxx 真源 + 构建副页面查找表
    spec_path = OUTPUT_DIR / f"spec_{product}_latest.md"
    spec_text_for_derive = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    secondary_lookup = (
        _build_module_page_to_main_lookup(spec_text_for_derive, modules)
        if spec_text_for_derive else {}
    )
    # 构建 prd_id → (mid, pid, state_name) 反查表（用于 C-4 注入）
    prd_id_to_meta: dict[str, tuple[str, str, str]] = {}
    for mod in modules:
        mid = mod.get("id", "")
        for page in mod.get("pages", []) or []:
            pid = page.get("id", "")
            for state in page.get("states", []) or []:
                prd_id_local = state.get("prd_id", "")
                state_name = state.get("name", "")
                if prd_id_local:
                    prd_id_to_meta[prd_id_local] = (mid, pid, state_name)
    c4_injected = 0
    c4_secondary = 0

    import re as _re
    proj_css_chunks: list[str] = []
    proj_showcase_chunks: list[str] = []  # 2026-05-12 新增:集中收集各 module 的 proj-component-* showcase
    assembled_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history_records: list[str] = []
    for mod, draft in zip(modules, draft_paths):
        draft_text = draft.read_text(encoding="utf-8")
        draft_sha = hashlib.sha256(draft_text.encode("utf-8")).hexdigest()[:12]
        frames = extract_frames(draft_text)
        proj_css = extract_proj_css(draft_text)
        if proj_css:
            proj_css_chunks.append(f"/* — from {draft.name} — */\n{proj_css}")
        proj_showcase = extract_proj_component_showcase(draft_text)
        if proj_showcase:
            proj_showcase_chunks.append(
                f"<!-- ===== {mod.get('id', '?')} showcase (from {draft.name}) ===== -->\n"
                f"{proj_showcase}"
            )
        if not frames:
            print(f"[WARN] {draft.name} 中未发现任何 [FRAME: ...] 标记", file=sys.stderr)
        history_records.append(
            f"{assembled_at} | {draft.name} | sha256:{draft_sha} | frames={len(frames)}"
        )
        for prd_id, content in frames.items():
            # SSOT #68：注入 C-4 业务契约子区块（主页面全量 / 副页面缩略）
            meta = prd_id_to_meta.get(prd_id)
            if meta and spec_text_for_derive:
                mid_f, pid_f, state_name_f = meta
                content_with_c4 = inject_c4_for_module(
                    content,
                    spec_text_for_derive,
                    mid_f,
                    pid_f,
                    state_name_f,
                    prd_id,
                    secondary_lookup,
                )
                if content_with_c4 != content:
                    c4_injected += 1
                    if (mid_f, pid_f) in secondary_lookup:
                        c4_secondary += 1
                content = content_with_c4

            # 议题 13 NB-WE-ASSEMBLE-DETERMINISM 治本（2026-06-07）：去 `| assembled={assembled_at}`
            # 字段，让 outputs/prd sha 字节级确定性恢复（同 inputs → 同 outputs sha），与 CLAUDE.md
            # 「PM 自报 sha vs 工作树 sha vs Supervisor 复跑 sha 三方对账」硬约束兼容。
            # `from` + `sha256:` 已含全部追溯所需业务信息（drafts 文件名 + 内容 sha），timestamp
            # 维度通过 git log + 文件 mtime 提供，无须 outputs 内嵌。assembled_at 仍用于
            # process_record/versions/draft_history.log 写盘（不污染 outputs/prd）。
            wrapped = (
                f"<!-- [FRAME-START: {prd_id} | from={draft.name} | sha256:{draft_sha}] -->\n"
                f"{content}\n"
                f"<!-- [FRAME-END: {prd_id}] -->"
            )

            # 重跑场景：FRAME-START/END 已存在 → 用正则替换中间内容
            # 注意：FRAME-START 行可含 metadata（| assembled=... | sha256:...），用宽松匹配
            reentry_pattern = _re.compile(
                r'<!--\s*\[FRAME-START:\s*' + _re.escape(prd_id) + r'(?:\s*\|[^\]]*)?\]\s*-->'
                r'.*?'
                r'<!--\s*\[FRAME-END:\s*' + _re.escape(prd_id) + r'\]\s*-->',
                _re.DOTALL,
            )
            if reentry_pattern.search(html):
                html = reentry_pattern.sub(lambda m: wrapped, html, count=1)
                total_frames += 1
                continue

            # 首次拼装：替换 gen_scaffold 生成的 FRAME 占位
            placeholder = f"<!-- [FRAME: {prd_id}] -->"
            if placeholder not in html:
                # 议题 12 NB-WE-12 治本（2026-06-07）：FRAME 占位缺失 ERROR sys.exit(1) → WARN
                # + skip，让 reassembly 能跑完（典型场景：PM 加 scaffold 新 state 没重 gen_scaffold；
                # 或 PM 直 Edit outputs 删了 placeholder 但 scaffold 仍含）。议题 #10 + #11 实证
                # 私域 outputs/prd H-M01-P01-offshelf-* 4 状态全 ERROR 阻塞 reassembly。
                print(
                    f"[WARN] 骨架既未找到 {placeholder}，也未找到可重入 FRAME-START/END 包裹块"
                    f" — 跳过本帧（议题 12 NB-WE-12 治本，ERROR → WARN）",
                    file=sys.stderr,
                )
                skipped_frames.append(prd_id)
                continue
            html = html.replace(placeholder, wrapped, 1)
            total_frames += 1
        print(f"  [+] {draft.name} — {len(frames)} 个帧")

    # 注入 proj 组件 CSS（来自模块草稿，合并去前缀注释）到 [PROJ-CSS] 占位，幂等
    all_proj_css = "\n\n".join(proj_css_chunks)

    # A3: selector 重复声明检查（owner 写完整 CSS，非 owner 应只引用 class）
    if all_proj_css:
        selector_re = _re.compile(r"^\s*(\.proj-[\w-]+(?:\.is-[\w-]+)?)\s*\{", _re.MULTILINE)
        seen: dict[str, int] = {}
        for sel in selector_re.findall(all_proj_css):
            seen[sel] = seen.get(sel, 0) + 1
        dupes = sorted(s for s, n in seen.items() if n > 1)
        if dupes:
            print(
                f"[WARN] PROJ-CSS 检测到重复 selector：{dupes}（应仅 owner 模块写完整 CSS，"
                f"非 owner 模块只引用 class；详见 proj_component_protocol.md §五.1）",
                file=sys.stderr,
            )

    html, proj_css_bytes = inject_proj_css(html, all_proj_css)

    # 注入兜底 CSS（fb-fallback.css）到第一个 <style> 块顶部，幂等
    html, fallback_bytes = inject_fallback_css(html)

    # 注入 proj-component-* showcase 集中容器(2026-05-12 /retro 新增):
    # 从各 module drafts 提取 <section id="proj-component-*"> 块,集中堆放到主模板
    # [PROJ-COMPONENT-SHOWCASE-AREA] 占位处,与 §11 changelog 形成「全揽 → 详情」对偶
    all_proj_showcase = "\n\n".join(proj_showcase_chunks)
    html, showcase_bytes = inject_proj_component_showcase(html, all_proj_showcase)

    # 注入侧栏「组件变更」分组（issue 2026-05-07_1613），从 §十一
    # component-changelog section 派生组件清单 + 状态 tag，幂等
    html, changelog_nav_count = inject_component_changelog_nav(html)

    # 处理 changelog 表「使用页面」/「影响页面」列 clickable 跳转
    # 把 M{XX}-P{YY} 或 M{XX} token 转为 onclick="showSection('H-MX-PY-default')" 链接
    # 兼容老表头「使用模块」/「影响模块」(target_headers 兼容清单)
    html, clickable_count = make_changelog_pages_clickable(html, modules)

    # 处理 changelog 表「组件说明锚点」列 clickable 跳转
    # 把 proj-component-{name} 字面转 onclick="showSection('proj-component-{name}')"
    # 兼容老表头「spec / prd 锚点」
    html, anchor_clickable_count = make_changelog_anchor_clickable(html)

    # NB-WE-19 防御性兜底（issue 2026-05-12 下游 # 13）：剥离 autofocus 属性。
    # PRD 是多帧设计文档,任何 <input autofocus> 会在浏览器加载时触发 scrollIntoView,
    # 路过 100+ sticky 元素引发合成层风暴 → 破坏默认显示首帧 + 滚动条闪烁。
    # 真源修复仍在 drafts 层删 autofocus,本剥离是防御性兜底（防未来 PM 误写）。
    html, autofocus_count = _strip_autofocus_attributes(html)

    # SSOT #41（WE-H per-archetype）：每页首帧 PAGE-SKELETON 占位填 chip（默认，
    # 深链中央 sk-askel-<aid>）或 override 骨架（罕见，本页无法套范式）
    html, (sk_override, sk_chip) = inject_page_skeletons(html, data)

    # 提议1：填 PRD spec-sitemap section（现场读 scaffold 派生层级图，SSOT #38；
    # colocate #39 契约 / #41 范式骨架(sk-askel) / #40 模块架构）
    html, prd_sitemap_ok = inject_prd_sitemap(html, data)

    # SSOT #67 A-05 信息架构重组：从 spec.md F-xxx 节派生「功能索引」4 列表格
    # 注入 PRD spec-feature section，移除/替换原 A-05 article 形态
    index_html_a05_ok = False
    index_row_count = 0
    if spec_text_for_derive:
        index_table = build_function_overview_index_with_jump(
            spec_text_for_derive, modules
        )
        index_row_count = len(list(_F_SECTION_RE.finditer(spec_text_for_derive)))
        html, index_html_a05_ok = inject_function_overview_index(html, index_table)

    # NB-2A-01 选项 C（议题 2A C-4 表格化 + CSS 字体统一的后续治本）：
    # 在 .interaction-card 范围内剥离 inline `font-size:XXpx` 声明（PM 写源残留 inline
    # 字号优先级 > CSS 致视觉不统一）；保留其他位置 PM 故意写的 inline 字号（如
    # frame-wrapper 内的 PRD 元数据）。须在所有 inject_c4_* / inject_function_overview_index
    # 后做（这些 inject 函数自己写入的 inline style 也会被本步剥离覆盖，但只在 card 内）。
    html, font_size_stripped = _strip_inline_font_size_in_interaction_cards(html)

    # SNB-MARKER-VISUAL-PREFIX-T-D-C 治本（议题 6）：扫所有 `<span class="tp-marker">NN</span>`
    # 注入 `data-tp-system="T"/"D"/"C"` 属性，让 prd_template.html CSS `.tp-marker[data-tp-system]::before`
    # 渲染视觉前缀（消数字 "01" 在 T/D/C 三系同字面的视觉冲突）。
    # 邻近探测覆盖 4 种 PM 写源嵌套场景（自身 / 父 / 前兄弟 / 父之前兄弟），不跨 frame 边界。
    # 须在所有 inject_c4_* / inject_function_overview_index 后做（这些 inject 函数也会写入 tp-marker）。
    html, tp_marker_injected = _inject_tp_marker_system_attr(html)

    # 议题 28 NB-WE-NAV-OVERWRITE 治本：把 sidebar SPEC + SITEMAP 两组 group-body
    # 内的 sidebar-spec-item div 段强制对齐 gen_scaffold.build_spec_nav() /
    # build_sitemap_nav() 当前真源，治"议题 27 修改 prd_template.html sidebar 结构 +
    # gen_scaffold.py build_*_nav 后 outputs/prd 不会自动重生 sidebar 结构（assemble.py
    # 仅重读 <style>/<script>/label，不重读 sidebar 结构）"哑修复根因（PM 上报实证）。
    # 与 _overwrite_first_style (NB-WE-20) / _overwrite_scripts (WE-ASM) 同模式（真源永远胜出）。
    # 必须在 _overwrite_spec_nav_label 之前调用 — 结构重读后 label 已是真源，label 重读多数 idempotent。
    html, sidebar_nav_restructured = _overwrite_sidebar_nav_structure_from_template(html)
    if sidebar_nav_restructured > 0:
        print(
            f"[OK] 已重置 sidebar SPEC+SITEMAP 结构 {sidebar_nav_restructured} 段"
            f"（议题 28 NB-WE-NAV-OVERWRITE，gen_scaffold build_*_nav 真源）"
        )

    # 议题 7 / NB-WE-2A-R2-02 P1 治本：把 sidebar `<div class="sidebar-spec-item" data-target="{sid}">{label}`
    # 中的 label 强制对齐 SPEC_ITEMS 当前真源（commit 2a7bc8b NB-HF-01/02 已锁），治
    # 既有 PRD 上线后 sidebar 仍含旧字面（如「功能需求规格」）的"既有产物不跟随 SSOT 升级"根因。
    # 与 _overwrite_first_style / _overwrite_scripts 同模式（真源永远胜出，idempotent）。
    html, spec_nav_relabeled = _overwrite_spec_nav_label_from_template(html)
    if spec_nav_relabeled > 0:
        print(f"[OK] 已重置 sidebar spec-item label {spec_nav_relabeled} 处（议题 7 / NB-WE-2A-R2-02）")

    # 议题 20 / NB-WE-2A-R8-03 P1 治本：把 prd 封面 `<span class="cover-version">XXX</span>`
    # 强制对齐 scaffold.json["changelog"] 末行 version 真源（SemVer 化阶段 4 版本号触发点
    # 单源约束）；治"scaffold.version=v4.0 与 changelog 末行 v0.1 不同步致封面取错源"根因。
    # 与 _overwrite_spec_nav_label 同模式（真源永远胜出，idempotent）。
    html, cover_version_relabeled = _overwrite_cover_version_from_scaffold_changelog(html)
    if cover_version_relabeled > 0:
        print(
            f"[OK] 已重置 cover-version 字面 {cover_version_relabeled} 处"
            f"（议题 20 / NB-WE-2A-R8-03，scaffold changelog 末行真源）"
        )

    # 议题 12 P3 / SSOT #69 C-2.B 无 C 触点绑定场景派生（方案 c）：为「无 C 触点绑定 +
    # 字段表前缺 C-2.B sub-title」的 interaction-card 注入派生「字段说明 — {派生名}」
    # （命名优先级 B: page-name → B 兜底: card-title 状态名 → A: MXX-PYY → C: 数据展示）。
    # 治 PM 写源在纯字段表场景（如 M10 admin-default 自定义字段管理页）下的规范盲点。
    # 须在所有 inject_c4_* / inject_function_overview_index 后做（这些 inject 不写 C-2.B
    # sub-title，本步独立补齐）。与 S4-59 容器锁定 regex 兼容（派生形态合规）。
    html, c2b_subtitle_injected = _inject_c2b_subtitle_for_no_c_binding(html)
    if c2b_subtitle_injected > 0:
        print(
            f"[OK] 已派生 C-2.B 字段说明 sub-title {c2b_subtitle_injected} 处"
            f"（议题 12 P3 / SSOT #69，无 C 触点绑定场景）"
        )

    # 议题 18 / NB-R4-01 C-2.A 索引层派生（须在议题 15 C-2 placeholder 之前）：
    # 为「卡片字段说明」+ C-2.A 索引层缺失的 interaction-card 注入 6 列占位索引表。
    # 私域主页 M02/M03/M05/M08 实证 56 处「卡片字段说明」缺索引层。
    html, c2a_index_injected = _inject_c2a_index_for_card_field_description(html)
    if c2a_index_injected > 0:
        print(
            f"[OK] 已派生 C-2.A 索引层占位 {c2a_index_injected} 处"
            f"（议题 18 / NB-R4-01，「卡片字段说明」C-2.A 索引缺口）"
        )

    # 议题 15 / NB-R3-01 C-1/C-2/C-3 真无内容占位派生（须在议题 18 C-2.A 派生之后）：
    # 治"interaction-card 缺 C-1/C-2/C-3 sub-title"反 pattern，注入「本帧无 XXX」豁免
    # 占位（与既有规范豁免文案一致，precheck S4-57/58/60 因豁免字面跳过详细校验）。
    html, c1_placeholder_injected = _inject_c1_placeholder_when_missing(html)
    if c1_placeholder_injected > 0:
        print(
            f"[OK] 已派生 C-1 列表回显说明占位 {c1_placeholder_injected} 处"
            f"（议题 15 / NB-R3-01，本帧无列表豁免）"
        )
    html, c2_placeholder_injected = _inject_c2_placeholder_when_missing(html)
    if c2_placeholder_injected > 0:
        print(
            f"[OK] 已派生 C-2 数据展示说明占位 {c2_placeholder_injected} 处"
            f"（议题 15 / NB-R3-01，本帧无数据展示豁免）"
        )
    html, c3_placeholder_injected = _inject_c3_placeholder_when_missing(html)
    if c3_placeholder_injected > 0:
        print(
            f"[OK] 已派生 C-3 触点交互说明占位 {c3_placeholder_injected} 处"
            f"（议题 15 / NB-R3-01，本帧无交互触点豁免）"
        )

    # 议题 10 NB-WE-PROTO-NAV-OVERWRITE 治本（2026-06-07）：assemble 末尾机械兜底
    # 确保 outputs/prd `.layout` 容器闭合（PM 实证：私域下游 outputs/prd L25413 `</div>`
    # 闭合 .layout 但 html.parser 仍报 1 个未配对开 = +1 净差；真因可能 inline attribute
    # 含 `<div` 字面 / inject 链路某处吞闭合 / drafts 拼装边界 — 精确归因复杂，本兜底
    # 在 `</body>` 前补足缺失的 `</div>` 让 outputs/prd 真 DOM 平衡）。
    html, layout_padded = _ensure_layout_closing_before_body(html)
    if layout_padded > 0:
        print(
            f"[OK] 已补 .layout 闭合机械兜底 {layout_padded} 处"
            f"（议题 10 NB-WE-PROTO-NAV-OVERWRITE，html.parser DOM 平衡兜底）"
        )

    prd_path.write_text(html, encoding="utf-8")
    _save_fingerprint(prd_path, product, "prd")

    # 追加 audit trail 到 process_record/versions/draft_history.log
    if history_records:
        history_log = REPO_ROOT / "process_record" / "versions" / "draft_history.log"
        history_log.parent.mkdir(parents=True, exist_ok=True)
        with history_log.open("a", encoding="utf-8") as f:
            for rec in history_records:
                f.write(rec + "\n")

    print(f"\n[OK] prd.html 拼装完成 — {len(modules)} 个模块 / {total_frames} 个帧")
    if skipped_frames:
        # 议题 12 NB-WE-12：汇总输出跳过帧清单，便于 PM 一次性看清漂移点
        print(
            f"[WARN] 跳过 {len(skipped_frames)} 个 FRAME（scaffold 含 prd_id 但骨架无对应"
            f" placeholder / 重入块）："
        )
        for prd_id in skipped_frames[:10]:
            print(f"       - {prd_id}")
        if len(skipped_frames) > 10:
            print(f"       ...（共 {len(skipped_frames)} 个，仅显示前 10）")
        print(
            f"       修复方向：①重跑 `gen_scaffold.py --force-rescaffold` 重生骨架"
            f"（推荐）② 或手补 `<!-- [FRAME: <prd_id>] -->` 占位 ③ 详 precheck_stage4"
            f" SSOT #72 `check_scaffold_outputs_frame_consistency` 详细漂移报告"
        )
    if autofocus_count > 0:
        print(
            f"[OK] 剥离 {autofocus_count} 处 autofocus 属性"
            f"（NB-WE-19 防御性兜底,防 scrollIntoView 破坏默认显示）"
        )
    print(
        f"     · 页面骨架（SSOT #41 / WE-H per-archetype）— 范式 chip {sk_chip} 页"
        f" + override 专属骨架 {sk_override} 页"
        + (
            "（0 注入：PAGE-SKELETON 占位缺失/无 page_archetypes；precheck S4-32 对 §3.0 产物 WARN 兜底）"
            if not (sk_chip or sk_override) else ""
        )
    )
    if prd_sitemap_ok:
        print(f"     §页面架构总览（spec-sitemap）已注入 — 从 scaffold 现场派生（SSOT #38；#39 契约 / #41 范式骨架(sk-askel) / #40 colocate）")
    if c4_injected:
        print(
            f"     interaction-card C-4 业务契约（SSOT #68）— 主页面 {c4_injected - c4_secondary} 帧全量"
            f" + 副页面 {c4_secondary} 帧缩略跳转"
        )
    if index_html_a05_ok:
        print(
            f"     A-05「功能索引」（SSOT #67）已注入 — {index_row_count} 条 F-xxx 派生 4 列表"
        )
    if font_size_stripped > 0:
        print(
            f"     .interaction-card 内 inline font-size 剥离 — {font_size_stripped} 处"
            f"（NB-2A-01 选项 C；治 PM 写源 inline 字号优先级 > CSS 致字号不统一）"
        )
    if tp_marker_injected > 0:
        print(
            f"     tp-marker 视觉前缀属性注入 — {tp_marker_injected} 处"
            f"（SNB-MARKER-VISUAL-PREFIX-T-D-C；data-tp-system=T/D/C → CSS ::before 渲染前缀，"
            f"消数字 '01' 在 T/D/C 三系同字面的视觉冲突）"
        )
    if proj_css_bytes:
        print(f"     proj 组件 CSS 已注入 — {proj_css_bytes} 字符（来自 {len(proj_css_chunks)} 个模块草稿）")
    if fallback_bytes:
        print(f"     兜底 CSS 已注入 — fb-fallback.css ({fallback_bytes} 字符)")
    if showcase_bytes:
        print(f"     proj-component-* showcase 集中注入 — {showcase_bytes} 字符 / {len(proj_showcase_chunks)} 个 module")
    print(f"     侧栏「组件变更」已注入 — {changelog_nav_count} 个组件条目")
    if clickable_count > 0:
        print(f"     changelog 表「使用页面」/「影响页面」列 — {clickable_count} 个 token 转为 clickable")
    print(f"     {prd_path}")
    print(f"\n提示：草稿文件可在主管审核通过后删除（process_record/drafts/prd_M*_draft.html）")


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("spec", "prd"):
        print(
            "用法：python pm-workflow/scripts/assemble.py [spec|prd] [--force-overwrite]",
            file=sys.stderr,
        )
        sys.exit(1)

    # 校验未知参数,防止 typo（如 --force 被误打）
    valid_flags = {"--force-overwrite"}
    unknown = [a for a in sys.argv[2:] if a not in valid_flags]
    if unknown:
        print(
            f"[ERROR] 未知参数：{unknown}；合法参数仅 {sorted(valid_flags)}",
            file=sys.stderr,
        )
        sys.exit(1)

    mode = sys.argv[1]
    data = load_scaffold()

    print(f"产品：{data['product']} | 模式：{mode} 拼装\n")

    if mode == "spec":
        assemble_spec(data)
    else:
        assemble_prd(data)


if __name__ == "__main__":
    main()
