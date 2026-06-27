#!/usr/bin/env python3
"""
gen_scaffold.py — 阶段四骨架生成器

用法：
    python pm-workflow/scripts/gen_scaffold.py [scaffold.json 路径] [flags]

    scaffold.json 默认路径：process_record/tasks/scaffold.json

    标志（推荐细分使用，避免一个标志同时跳过多个保护）：
    --force-rescaffold      覆盖已被 Foundation 或后续 Step 写入的骨架（破坏性）
    --skip-task-card-check  跳过任务卡完整性检查（缺『候选组件清单』段时仍允许继续）
    --force                 兼容旧版，等同同时启用上述两个；不推荐使用

输出：
    outputs/spec_[产品名]_latest.md   空骨架，供 Foundation Agent 追加写入
    outputs/prd_[产品名]_latest.html  带全量导航 + 占位注释的骨架
    process_record/drafts/            目录（自动创建）
    process_record/tasks/.scaffold.lock  scaffold.json 的 sha256 + 时间戳，
                                       用于检测后续 Step 重跑时的编号变化

幂等性：
    若 spec/prd 已被 Foundation 写入（spec 含 `## S0` 或 prd 9 个产品规格 section
    内 `<!-- Foundation Agent 填充 -->` 已被替换,9 节 = 8 个 A-XX + spec-business-flow
    A-04.2 业务流程图）,默认报错并要求 --force。
    若 .scaffold.lock 与当前 scaffold.json hash 一致 + 骨架已生成 → 跳过重跑。
"""

import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# ── 路径约定 ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = REPO_ROOT / "pm-workflow" / "rules" / "prd_template.html"
DEFAULT_SCAFFOLD = REPO_ROOT / "process_record" / "tasks" / "scaffold.json"
OUTPUT_DIR = REPO_ROOT / "outputs"
DRAFTS_DIR = REPO_ROOT / "process_record" / "drafts"
SCAFFOLD_LOCK = REPO_ROOT / "process_record" / "tasks" / ".scaffold.lock"
BACKUP_DIR = REPO_ROOT / "process_record" / "versions" / ".assemble_backups"

# 产品规格区固定条目（A-01~A-08 + A-04.2 业务流程图，共 9 节；
# spec-business-flow 位置介于 spec-journey 与 spec-feature 之间，与 prd_expression_standard.md
# §二「子区块固定顺序」声明对齐）
SPEC_ITEMS = [
    ("spec-background",     "需求背景"),
    ("spec-persona",        "用户画像"),
    ("spec-permission",     "权限矩阵"),
    ("spec-journey",        "用户旅程"),
    ("spec-business-flow",  "业务流程图"),  # A-04.2 业务流程图（工程视角,与 A-04 用户旅程互补）
    ("spec-feature",        "功能索引"),
    ("spec-data",           "数据字段"),
    ("spec-exception",      "异常处理全景"),
    ("spec-nonfunc",        "非功能需求"),
]

# 提议1（SSOT 双锚 #38）：gen_scaffold **派生注入**的产品规格区 section，与
# SPEC_ITEMS（Foundation 手填，占位 `<!-- Foundation Agent 填充 -->`）**解耦**。
# 关键（B5）：`detect_foundation_written` 的 total_placeholders 仍 = len(SPEC_ITEMS)，
# 不含本组——本组 section 内置 `<!-- [SITEMAP-PRD] -->` 占位（非 Foundation 占位），
# 内容由 assemble.py 在 Step6 现场读 scaffold 派生，故新鲜骨架 Foundation 占位数
# 恒 = len(SPEC_ITEMS)，不会因 9<10 被误判为「Foundation 已部分写入」。
# 本列表仅驱动 **section DOM** 生成（build_spec_sections）——spec-sitemap
# `<section>` 仍紧接 SPEC_ITEMS 节后、原型区前。**nav 入口 2026-05-18 Item 2
# 升为独立顶层组「页面架构总览」**（不再 append 「产品规格」组末位），由
# build_sitemap_nav 驱动（4 锚点子项），见 SITEMAP_NAV_ANCHORS。
# 议题 27 2026-06-06：业务流程图 nav 归"产品规格"组紧跟用户旅程（按
# prd_expression_standard.md §A-04.2 L642 [Must]「侧栏导航须含业务流程分组
# 与 A-04 用户旅程分组并列」规范修复 L250-251 vs L642 内部矛盾）— 删除
# SITEMAP_NAV_MOVED_SECTIONS 机制（不再有 nav 移入项），build_spec_nav
# 直接遍历 SPEC_ITEMS 全量 9 项 + build_sitemap_nav 只遍历 SITEMAP_NAV_ANCHORS 4 项。
DERIVED_SPEC_ITEMS = [
    ("spec-sitemap",        "页面架构总览"),
]


# ── HTML 替换工具 ──────────────────────────────────────────────────────────────

def replace_comment_block(html: str, start_prefix: str, replacement: str) -> str:
    """将 <!-- [start_prefix] ... --> 整个注释块替换为 replacement。"""
    pattern = re.compile(re.escape(start_prefix) + r".*?-->", re.DOTALL)
    return pattern.sub(replacement, html, count=1)


def replace_single_line_comment(html: str, marker: str, replacement: str) -> str:
    """将含有 marker 的整行替换为 replacement。"""
    lines = html.split("\n")
    out = []
    for line in lines:
        out.append(replacement if marker in line else line)
    return "\n".join(out)


def replace_block_range(html: str, start_marker: str, end_marker: str, replacement: str) -> str:
    """将从含 start_marker 的行到含 end_marker 的行（含两端）替换为 replacement。"""
    lines = html.split("\n")
    out = []
    skipping = False
    for line in lines:
        if start_marker in line:
            skipping = True
            out.append(replacement)
        elif end_marker in line:
            skipping = False
        elif not skipping:
            out.append(line)
    return "\n".join(out)


# ── 导航生成 ──────────────────────────────────────────────────────────────────

# 「页面架构总览」顶层组（Item 2，2026-05-18）：spec-sitemap 单 section 内 4 个
# assemble 现场派生块各带 id 锚，nav 子项 onclick `showSection('sk-*')` 锚点滚动
# （showSection 对任意 id 元素生效，非仅 <section>）。
# id 锚真源 = `assemble.py inject_prd_sitemap`（4 块 <div id="sk-*">）；改名须同步。
# WE-E（2026-05-19）：sk-gallery 移除——#41 骨架屏改逐页注入各页首帧前。
# WE-H（2026-05-19，#41 颗粒度重设 per-page→per-archetype）：#41 单源回 §3.0
# per-archetype（pre-WE-E 概览位对其本就正确），新增 `sk-askel`「范式骨架」
# 子项（#39 契约表后，子决策B 独立子节；per-archetype 是 ~N 小目录，非旧
# per-page sk-gallery）→ SITEMAP_NAV_ANCHORS 3→4。
# 议题 27 2026-06-06：业务流程图 nav 归"产品规格"组紧跟用户旅程（按
# §A-04.2 L642 [Must] 规范修复），本组 5→4 项（删 SITEMAP_NAV_MOVED_SECTIONS 机制）。
SITEMAP_NAV_ANCHORS = [
    ("sk-hier",    "页面层级图"),   # 提议1 #38
    ("sk-arch",    "页面结构契约"),  # 提议2 #39
    ("sk-askel",   "范式骨架"),      # #41 WE-H per-archetype（子决策B 独立子节）
    ("sk-mod",     "模块架构"),      # 提议3 #40
]


def build_spec_nav() -> str:
    """「产品规格」组 nav：SPEC_ITEMS 全量 9 项（含 spec-business-flow 业务流程图
    紧跟用户旅程，议题 27 按 §A-04.2 L642 [Must]「侧栏导航须含业务流程分组与
    A-04 用户旅程并列」规范修复 L250-251 vs L642 内部对立）。
    **不再** append DERIVED_SPEC_ITEMS（spec-sitemap 升独立顶层组，见 build_sitemap_nav）。
    SPEC_ITEMS / build_spec_sections / detect_foundation_written 均不动。"""
    lines = []
    for sid, label in SPEC_ITEMS:
        lines.append(
            f'      <div class="sidebar-spec-item" data-target="{sid}" '
            f"onclick=\"showSection('{sid}')\">{label}</div>"
        )
    return "\n".join(lines)


def build_sitemap_nav() -> str:
    """「页面架构总览」顶层组 nav（Item 2，SSOT #38/#39/#41/#40）：4 个
    spec-sitemap 块内锚点滚动子项（#38 层级 / #39 契约 / #41 范式骨架 /
    #40 模块架构）= 4 项（议题 27 业务流程图 nav 归"产品规格"组按 §A-04.2 L642
    [Must] 规范修复，本组 5→4）。
    注入 prd_template.html `<!-- [SITEMAP-NAV] -->` 占位。"""
    lines = []
    for aid, label in SITEMAP_NAV_ANCHORS:
        lines.append(
            f'      <div class="sidebar-spec-item" data-target="{aid}" '
            f"onclick=\"showSection('{aid}')\">{label}</div>"
        )
    return "\n".join(lines)


def iter_page_prd_ids(page: dict):
    """yield 本页全部 prd_id：先直挂 states，再 embedded_components[].states
    （SSOT #76 R3 内嵌子组件）。所有"收集本页全部 prd_id / 全部出帧状态"的路径
    **统一用本 helper**——防漏内嵌帧致 #72 frame 一致性误判漂移（设计降风险关键）。

    内嵌子组件（embedded_components）的状态帧复用 page 的 prd_id→section→FRAME→nav
    全套机器，但**不占独立 page/route / 不计页面数 / 不受 page_source #74 约束**。
    字段可选——无 embedded_components → 仅 yield 直挂 states（向后兼容，行为零变化）。
    """
    if not isinstance(page, dict):
        return
    for state in page.get("states", []) or []:
        if isinstance(state, dict) and state.get("prd_id"):
            yield state["prd_id"]
    for emb in page.get("embedded_components", []) or []:
        if not isinstance(emb, dict):
            continue
        for state in emb.get("states", []) or []:
            if isinstance(state, dict) and state.get("prd_id"):
                yield state["prd_id"]


def build_proto_nav(modules: list) -> str:
    """构造侧栏 proto 导航树:模块 → 页面 → 状态 三层结构(+ 内嵌子组件第 4 层)。

    设计规则(2026-05-12 /retro 后修订,issue 2026-05-12_1521 # 1 + non-leaf toggle 2026-05-12 追加):
    - **所有模块**均须呈现「模块 → 页面 → 状态」**完整三层结构**,
      无论模块只 1 页 / 页面只 1 状态,均不省略中间页面层级。
    - **non-leaf 节点(模块/页面)支持折叠展开**:点击 toggle icon 折叠/展开下方子项,
      点击文字 onclick 不动(模块/页面不直接跳转,跳转走具体状态)。
    - 缩进:模块层 16px(.sidebar-page 既有)/ 页面层 28px / 状态层 44px。
    - **内嵌子组件(embedded_components,SSOT #76 R3)**:page 下第 4 层 non-leaf
      子组(缩进 44px,含 ⤷ 前缀),其状态帧缩进 60px;无 route 不占页面数。
      字段缺省 → 不渲染第 4 层(向后兼容)。
    """
    lines = []
    for mod in modules:
        mod_id, mod_name = mod["id"], mod["name"]
        mod_subgroup = f"module-{mod_id}"
        lines.append('      <div class="sidebar-group">')
        # 模块层:non-leaf toggle(点 icon 折叠/展开模块所有页面+状态)
        lines.append(
            f'        <div class="sidebar-page" data-subgroup="{mod_subgroup}" '
            f'onclick="handleSubgroupClick(event, \'{mod_subgroup}\', null)">'
            f'<span class="sidebar-subgroup-icon">−</span>{mod_id} {mod_name}</div>'
        )
        lines.append(f'        <div class="sidebar-subgroup-body" data-subgroup-body="{mod_subgroup}">')
        for page in mod["pages"]:
            page_subgroup = f"page-{mod_id}-{page['id']}"
            # 页面层:non-leaf toggle(点 icon 折叠/展开该页面所有状态)
            lines.append(
                f'          <div class="sidebar-state" style="padding-left:28px;'
                f' font-weight:600; color:var(--fb-text-primary);" '
                f'data-subgroup="{page_subgroup}" '
                f'onclick="handleSubgroupClick(event, \'{page_subgroup}\', null)">'
                f'<span class="sidebar-subgroup-icon">−</span>{page["id"]} {page["name"]}</div>'
            )
            lines.append(f'          <div class="sidebar-subgroup-body" data-subgroup-body="{page_subgroup}">')
            for state in page["states"]:
                prd_id = state["prd_id"]
                state_name = state["name"]
                lines.append(
                    f'            <div class="sidebar-state" style="padding-left:44px;"'
                    f' data-target="{prd_id}"'
                    f' onclick="showSection(\'{prd_id}\')">'
                    f'{state_name}</div>'
                )
            # 第 4 层:内嵌子组件(embedded_components,SSOT #76 R3)——直挂 states 之后,
            # 每个内嵌子组件渲染为 page 下 non-leaf 折叠子组(缩进 44px,⤷ 前缀),
            # 其状态帧缩进 60px。字段缺省 → 不进入循环(向后兼容,零变化)。
            for emb in page.get("embedded_components", []) or []:
                emb_id = emb["id"]
                emb_name = emb.get("name", emb_id)
                emb_subgroup = f"embed-{mod_id}-{page['id']}-{emb_id}"
                lines.append(
                    f'            <div class="sidebar-state" style="padding-left:44px;'
                    f' font-weight:600; color:var(--fb-text-secondary);" '
                    f'data-subgroup="{emb_subgroup}" '
                    f'onclick="handleSubgroupClick(event, \'{emb_subgroup}\', null)">'
                    f'<span class="sidebar-subgroup-icon">−</span>⤷ {emb_name}</div>'
                )
                lines.append(
                    f'            <div class="sidebar-subgroup-body" data-subgroup-body="{emb_subgroup}">'
                )
                for state in emb.get("states", []) or []:
                    prd_id = state["prd_id"]
                    state_name = state["name"]
                    lines.append(
                        f'              <div class="sidebar-state" style="padding-left:60px;"'
                        f' data-target="{prd_id}"'
                        f' onclick="showSection(\'{prd_id}\')">'
                        f'{state_name}</div>'
                    )
                lines.append("            </div>")
            lines.append("          </div>")
        lines.append("        </div>")
        lines.append("      </div>")
    return "\n".join(lines)


# ── 区域 A — 产品规格区 section 骨架 ─────────────────────────────────────────

def build_spec_sections() -> str:
    lines = []
    for sid, label in SPEC_ITEMS:
        lines += [
            f'      <section id="{sid}">',
            f'        <div class="spec-section">',
            f'          <div class="spec-header">{label}</div>',
            f'          <div class="spec-body">',
            f'            <!-- Foundation Agent 填充 -->',
            f'          </div>',
            f'        </div>',
            f'      </section>',
        ]
    # 提议1：派生 section 空壳（SSOT #38）。内置 `<!-- [SITEMAP-PRD] -->` 占位
    # （**非** Foundation 占位，故不计入 detect_foundation_written），内容由
    # assemble.py 在 Step6 现场读 scaffold 派生注入。
    for sid, label in DERIVED_SPEC_ITEMS:
        lines += [
            f'      <section id="{sid}">',
            f'        <div class="spec-section">',
            f'          <div class="spec-header">{label}</div>',
            f'          <div class="spec-body">',
            f'            <!-- [SITEMAP-PRD] -->',
            f'          </div>',
            f'        </div>',
            f'      </section>',
        ]
    return "\n".join(lines)


# ── 区域 B — 模块占位注释 ──────────────────────────────────────────────────────

def build_module_sections(modules: list) -> str:
    """
    为每个模块的每个状态生成带 section-header（含 state-chips）的 section 骨架。
    帧内容区保留 <!-- [FRAME: prd_id] --> 占位，由 assemble.py prd 填入。

    WE-E（SSOT #41 重设）：每页**首个 state** 的 section-header 之后、
    [FRAME] 之前 emit 一次 `<!-- [PAGE-SKELETON: {mid}-{pid}] -->` 占位
    （骨架是 per-page 平面布局、与 state 无关，故每页一次随首帧）；
    assemble.inject_page_skeletons 据 spec draft ```skeleton 现场填充
    （取代旧 spec-sitemap 画廊——per-page-concrete 应随页落帧前，详 §A-09）。
    """
    lines = []
    for mod in modules:
        mod_id, mod_name = mod["id"], mod["name"]
        lines.append(f"      <!-- ── {mod_id} {mod_name} ── -->")
        for page in mod["pages"]:
            page_states = page["states"]
            for idx, state in enumerate(page_states):
                prd_id = state["prd_id"]
                roles_str = " / ".join(state["roles"])
                # state-chips：本页所有状态，当前高亮
                chips = []
                for s in page_states:
                    active = " active" if s["prd_id"] == prd_id else ""
                    chips.append(
                        f'            <button class="state-chip{active}"'
                        f' onclick="showSection(\'{s["prd_id"]}\')">'
                        f'{s["name"]}</button>'
                    )
                lines += [
                    f'      <section id="{prd_id}" class="proto-section">',
                    f'        <div class="section-header">',
                    f'          <div class="section-meta">',
                    f'            <div class="section-title-row">',
                    f'              <span class="page-id">{mod_id} / {page["id"]}</span>',
                    f'              <span class="page-name">{page["name"]}</span>',
                    f'            </div>',
                    f'            <div class="section-tag-row">',
                    f'              <span class="role-tag">视角：{roles_str}</span>',
                    f'              <span class="func-tag">路由：{page["route"]}</span>',
                    f'            </div>',
                    f'          </div>',
                    f'          <div class="state-chips">',
                    *chips,
                    f'          </div>',
                    f'        </div>',
                ]
                # WE-E：每页首 state 注入 per-page 骨架占位（每页一次）
                if idx == 0:
                    lines.append(
                        f'        <!-- [PAGE-SKELETON: {mod_id}-{page["id"]}] -->'
                    )
                lines += [
                    f'        <!-- [FRAME: {prd_id}] -->',
                    f'      </section>',
                ]
            # 内嵌子组件(embedded_components,SSOT #76 R3):每个内嵌状态复用同一
            # section + state-chips + [FRAME] 结构(复用 prd_id→section→FRAME 机器),
            # 但 page-name 标注 `· {emb_name}` / route 标「内嵌于父页」/ 不 emit
            # PAGE-SKELETON(骨架 per-page,已随首帧)。字段缺省 → 不进入循环(向后兼容)。
            for emb in page.get("embedded_components", []) or []:
                emb_states = emb.get("states", []) or []
                emb_name = emb.get("name", emb["id"])
                for state in emb_states:
                    prd_id = state["prd_id"]
                    roles_str = " / ".join(state.get("roles", []) or []) or "（继承父页）"
                    chips = []
                    for s in emb_states:
                        active = " active" if s["prd_id"] == prd_id else ""
                        chips.append(
                            f'            <button class="state-chip{active}"'
                            f' onclick="showSection(\'{s["prd_id"]}\')">'
                            f'{s["name"]}</button>'
                        )
                    lines += [
                        f'      <section id="{prd_id}" class="proto-section">',
                        f'        <div class="section-header">',
                        f'          <div class="section-meta">',
                        f'            <div class="section-title-row">',
                        f'              <span class="page-id">{mod_id} / {page["id"]}</span>',
                        f'              <span class="page-name">{page["name"]} · {emb_name}</span>',
                        f'            </div>',
                        f'            <div class="section-tag-row">',
                        f'              <span class="role-tag">视角：{roles_str}</span>',
                        f'              <span class="func-tag">内嵌于 {page["id"]}（无独立路由）</span>',
                        f'            </div>',
                        f'          </div>',
                        f'          <div class="state-chips">',
                        *chips,
                        f'          </div>',
                        f'        </div>',
                        f'        <!-- [FRAME: {prd_id}] -->',
                        f'      </section>',
                    ]
    return "\n".join(lines)


STATUS_CLASS = {"草稿": "draft", "评审中": "review", "已批准": "approved"}

# ── 封面页 & 使用说明页 ────────────────────────────────────────────────────────

def build_cover_page(data: dict, today: str) -> str:
    product = data["product"]
    # cover-version 单源：优先取 changelog 末行 version（与 assemble.py
    # _overwrite_cover_version_from_scaffold_changelog 同一真源，消除 data["version"] 粗粒度
    # 与 changelog 末行不一致的隐患），回退 data["version"]，再回退 v0.1（阶段 4 启动未交付态）。
    _changelog = data.get("changelog") or []
    version = (
        (_changelog[-1].get("version") if isinstance(_changelog[-1], dict) else None)
        if _changelog else None
    ) or data.get("version") or "v0.1"
    description = data.get("description", "")
    status = data.get("status", "")
    platforms = data["platforms"]

    platform_tags = "\n".join(
        f'          <span class="cover-platform-tag">{p}</span>'
        for p in platforms
    )
    status_html = (
        f'\n            <span class="cover-status {STATUS_CLASS.get(status, "draft")}">{status}</span>'
        if status else ""
    )
    desc_html = (
        f'\n          <div class="cover-description">{description}</div>'
        if description else ""
    )

    return (
        f'      <section id="doc-cover" class="cover-page">\n'
        f'        <div class="cover-inner">\n'
        f'          <div class="cover-product-name">{product}</div>\n'
        f'          <div class="cover-badge-row">\n'
        f'            <span class="cover-version">{version}</span>\n'
        f'            <span class="cover-date">{today}</span>{status_html}\n'
        f'          </div>\n'
        f'          <div class="cover-platforms">\n'
        f'{platform_tags}\n'
        f'          </div>{desc_html}\n'
        f'          <div class="cover-divider"></div>\n'
        f'          <div class="cover-footer">AI 产品工作流 · 自动生成</div>\n'
        f'        </div>\n'
        f'      </section>'
    )


def build_changelog_page(data: dict) -> str:
    # G-02 [MUST] 6 列对齐（与 spec §变更记录列序/字段 1:1 — 详 assemble.py:985）。
    # 2026-06-01 NB-WE-21 部分摘账：prd thead 4→6 列（变更原因 + 审核人补齐）；
    # changelog JSON 旧数据缺 reason/reviewer 字段时 .get() 返回空字符串向后兼容。
    # precheck check_prd_doc_changelog_columns 校验 + ssot_anchors #22 升 A 组留下次批次。
    changelog = data.get("changelog", [])
    if changelog:
        rows = "\n".join(
            f'                  <tr>'
            f'<td>{e.get("version", "")}</td>'
            f'<td>{e.get("desc", "")}</td>'
            f'<td>{e.get("reason", "")}</td>'
            f'<td>{e.get("author", "")}</td>'
            f'<td>{e.get("reviewer", "")}</td>'
            f'<td>{e.get("date", "")}</td>'
            f'</tr>'
            for e in changelog
        )
    else:
        rows = (
            '                  <tr><td colspan="6" style="color:var(--fb-text-hint);'
            'text-align:center;">暂无变更记录</td></tr>'
        )
    return (
        '      <section id="doc-changelog">\n'
        '        <div class="spec-section">\n'
        '          <div class="spec-header">变更记录</div>\n'
        '          <div class="spec-body">\n'
        '            <div class="spec-block">\n'
        '              <table class="spec-table full-width">\n'
        '                <thead><tr><th>版本</th><th>变更内容</th><th>变更原因</th><th>变更人</th><th>审核人</th><th>日期</th></tr></thead>\n'
        f'                <tbody>\n{rows}\n                </tbody>\n'
        '              </table>\n'
        '            </div>\n'
        '          </div>\n'
        '        </div>\n'
        '      </section>'
    )


def build_guide_page() -> str:
    return (
        '      <section id="doc-guide">\n'
        '        <div class="spec-section">\n'
        '          <div class="spec-header">使用说明</div>\n'
        '          <div class="spec-body">\n'
        '            <div class="spec-block">\n'
        '              <h3>如何使用本文档</h3>\n'
        '              <table class="spec-table full-width">\n'
        '                <thead><tr><th>功能</th><th>操作</th></tr></thead>\n'
        '                <tbody>\n'
        '                  <tr><td>导航至指定页面</td><td>点击左侧侧栏对应的页面 / 状态条目，内容区自动滚动定位</td></tr>\n'
        '                  <tr><td>切换同一页面的不同状态</td><td>点击页面顶部的状态切换胶囊（State Chips），内容区跳转至对应状态帧</td></tr>\n'
        '                  <tr><td>查看产品规格</td><td>侧栏「产品规格」区包含需求背景、用户画像、权限矩阵等规格文档；「交互原型」区包含各页面状态帧及交互说明</td></tr>\n'
        '                  <tr><td>触点对照</td><td>交互帧内的蓝色序号徽章（01 / 02…）与交互说明表格中的「序号」列一一对应</td></tr>\n'
        '                </tbody>\n'
        '              </table>\n'
        '            </div>\n'
        '            <div class="spec-block">\n'
        '              <h3>编号规则说明</h3>\n'
        '              <table class="spec-table full-width">\n'
        '                <thead><tr><th>层级</th><th>格式</th><th>示例</th><th>说明</th></tr></thead>\n'
        '                <tbody>\n'
        '                  <tr><td>模块</td><td>M[XX]</td><td>M01、M02</td><td>全产品唯一，任务规划阶段统一分配，后续不可变更</td></tr>\n'
        '                  <tr><td>页面</td><td>P[XX]（模块内）</td><td>M01-P01、M02-P01</td><td>模块内唯一，同一模块页面从 P01 起依次递增</td></tr>\n'
        '                  <tr><td>状态</td><td>语义名</td><td>default、empty、loading</td><td>页面内唯一，任务规划阶段预定义</td></tr>\n'
        '                  <tr><td>原型帧 ID</td><td>H-M[XX]-P[XX]-[状态名]</td><td>H-M01-P01-default</td><td>全局唯一，用于侧栏导航锚点和 spec.md 跨模块跳转引用</td></tr>\n'
        '                  <tr><td>触点</td><td>M[XX]-P[XX]-T[NN]</td><td>M01-P01-T01</td><td>页面内唯一；弹窗 / 抽屉内用 D 替换 T；序号从 01 起递增</td></tr>\n'
        '                  <tr><td>功能需求</td><td>F-[XXX]</td><td>F-001、F-012</td><td>全产品唯一，阶段三产品定义阶段分配</td></tr>\n'
        '                </tbody>\n'
        '              </table>\n'
        '            </div>\n'
        '          </div>\n'
        '        </div>\n'
        '      </section>'
    )


# ── spec.md 骨架 ──────────────────────────────────────────────────────────────

def generate_spec_skeleton(data: dict, output_dir: Path) -> Path:
    product = data["product"]
    today = date.today().isoformat()
    platforms = ", ".join(data["platforms"])
    content = (
        f"<!-- ================================================================\n"
        f"     spec_{product}_latest.md\n"
        f"     自动生成 {today} | 端口：{platforms}\n"
        f"     骨架由 gen_scaffold.py 创建，各章节内容由对应 Agent 追加写入\n"
        f"================================================================ -->\n"
    )
    path = output_dir / f"spec_{product}_latest.md"
    path.write_text(content, encoding="utf-8")
    return path


# ── prd.html 骨架 ─────────────────────────────────────────────────────────────

def generate_prd_skeleton(data: dict, template_path: Path, output_dir: Path) -> Path:
    product = data["product"]
    today = date.today().isoformat()
    modules = data["modules"]

    html = template_path.read_text(encoding="utf-8")

    # 1. 替换 <title>
    html = html.replace("[产品名] PRD — [YYYY-MM-DD]", f"{product} PRD — {today}")

    # 2. [SPEC-NAV] 注释块 → 实际导航条目
    html = replace_comment_block(html, "<!-- [SPEC-NAV]", build_spec_nav())

    # 2.1 [SITEMAP-NAV] 注释块 → 「页面架构总览」顶层组导航条目（Item 2）
    html = replace_comment_block(html, "<!-- [SITEMAP-NAV]", build_sitemap_nav())

    # 3. [PROTO-NAV] 注释块 → 实际导航条目
    html = replace_comment_block(html, "<!-- [PROTO-NAV]", build_proto_nav(modules))

    # 4. [COVER-PAGE] 单行注释 → 封面 section
    html = replace_single_line_comment(html, "<!-- [COVER-PAGE]", build_cover_page(data, today))

    # 5. [GUIDE-PAGE] 单行注释 → 使用说明 section
    html = replace_single_line_comment(html, "<!-- [GUIDE-PAGE]", build_guide_page())

    # 6. [CHANGELOG-PAGE] 单行注释 → 变更记录 section
    html = replace_single_line_comment(html, "<!-- [CHANGELOG-PAGE]", build_changelog_page(data))

    # 7. [MODULE SPEC] 单行注释 → 8 个空 section
    html = replace_single_line_comment(
        html, "<!-- [MODULE SPEC]", build_spec_sections()
    )

    # 8. [MODULE M-01] 示例占位区 → 实际模块 section 骨架（含 state-chips）
    html = replace_block_range(
        html,
        "<!-- [MODULE M-01]: 待拼装 -->",
        "<!-- 依此类推",
        build_module_sections(modules),
    )

    path = output_dir / f"prd_{product}_latest.html"
    path.write_text(html, encoding="utf-8")
    return path


# ── 幂等检测与编号锁定 ─────────────────────────────────────────────────────────

def detect_foundation_written(spec_path: Path, prd_path: Path) -> list[str]:
    """检测 spec/prd 是否已被 Foundation 或后续 Step 写入。
    返回非空的"已写入"信号清单，空列表表示未被写入。"""
    signals: list[str] = []
    if spec_path.exists():
        text = spec_path.read_text(encoding="utf-8")
        for marker in ("## S0", "## S0.5", "## S1"):
            if marker in text:
                signals.append(f"spec.md 已含 {marker}")
                break
    if prd_path.exists():
        html = prd_path.read_text(encoding="utf-8")
        # 9 个产品规格 section 内的 Foundation 占位若已被全部替换,视为 Foundation 已写入
        # 数量动态绑定 SPEC_ITEMS（含 A-04.2 业务流程图独立 section,共 9 节）
        total_placeholders = len(SPEC_ITEMS)
        foundation_placeholder_count = html.count("<!-- Foundation Agent 填充 -->")
        if 0 < foundation_placeholder_count < total_placeholders:
            replaced = total_placeholders - foundation_placeholder_count
            signals.append(f"prd.html Foundation 占位部分已替换（{replaced} / {total_placeholders}）")
        elif foundation_placeholder_count == 0:
            # 全部被替换,或 prd.html 完全不是骨架（被 assemble 后的产物）
            if "<section" in html and 'id="A-' in html:
                signals.append("prd.html Foundation 占位全部已替换")
        # 检测 FRAME 标记是否已被替换为 FRAME-START/END（assemble.py prd 已运行过）
        if "<!-- [FRAME-START:" in html:
            signals.append("prd.html 已被 assemble.py prd 拼装")
    return signals


def hash_scaffold(scaffold_path: Path) -> str:
    return hashlib.sha256(scaffold_path.read_bytes()).hexdigest()


def write_scaffold_lock(scaffold_hash: str) -> None:
    SCAFFOLD_LOCK.parent.mkdir(parents=True, exist_ok=True)
    SCAFFOLD_LOCK.write_text(
        f"sha256: {scaffold_hash}\ngenerated_at: {datetime.now().isoformat(timespec='seconds')}\n",
        encoding="utf-8",
    )


def read_scaffold_lock() -> str | None:
    if not SCAFFOLD_LOCK.exists():
        return None
    for line in SCAFFOLD_LOCK.read_text(encoding="utf-8").splitlines():
        if line.startswith("sha256:"):
            return line.split(":", 1)[1].strip()
    return None


# ── v2.0 schema 校验 ──────────────────────────────────────────────────────────

VALID_DEPENDS_KINDS = {"section_jump", "shared_component", "data_flow", "permission"}

# SSOT #75-R5 archetype 语义类别枚举（可选 page_archetypes[].semantic_category）
_VALID_ARCHETYPE_SEMANTICS = {
    "form", "readonly-status", "list", "detail", "modal-confirm", "wizard", "dialog-flow",
}


def validate_v2_schema(data: dict) -> list[str]:
    """v2.0 schema 必填字段 + 结构校验。返回错误清单，空表示通过。"""
    errors: list[str] = []
    if data.get("schema_version") != "v2.0":
        errors.append(
            f"schema_version 必须为 'v2.0'（当前：{data.get('schema_version', '缺失')!r}）；"
            "v2.0 是 PM 子阶段一升级后的新格式，含 candidate_components / depends_on 对象 / owner_assignments"
        )

    # 跨模块 owner 冲突收集：proj_id -> [声明它的模块]
    ownership_claims: dict[str, list[str]] = {}

    # logic-only 模块引用完整性校验：先收集全部模块 id（供 ui_carrier_modules 反查）
    all_mod_ids = {m.get("id") for m in data.get("modules", []) if m.get("id")}

    for mod in data.get("modules", []):
        mid = mod.get("id", "?")
        # 提议3（SSOT #40）：modules[].purpose 为**可选**字段（D2 决定）——
        # 缺省不报错（下游无需破坏性迁移）；存在则须为字符串
        if "purpose" in mod and not isinstance(mod["purpose"], str):
            errors.append(
                f"[{mid}] purpose 字段存在但非字符串（可选字段，填则须为一句话模块职责）"
            )
        # pages 字段必填 + 类型校验（v2.0 schema 强制；与 precheck_stage4 等价双层）
        # 缺失 / 非数组 → 严格 FAIL（不静默回退）；空数组 [] 视为 logic-only 模块语义
        pages_field = mod.get("pages")
        if pages_field is None:
            errors.append(
                f"[{mid}] 缺 pages 字段（v2.0 必填；logic-only 模块填 `[]` + `ui_carrier_modules`，"
                f"普通模块填非空数组）"
            )
            # 缺 pages 时不再进入 logic-only 校验，避免连锁误报
            continue
        if not isinstance(pages_field, list):
            errors.append(
                f"[{mid}] pages 必须为数组（当前类型：{type(pages_field).__name__}）"
            )
            continue
        # logic-only 模块校验（SSOT #50）：pages=[] → 必须含 ui_carrier_modules 非空数组 +
        # 引用 ⊂ scaffold.modules[].id（且引用目标须为 pages 非空模块，禁自引 / 禁指向其他 logic-only，
        # 防链式 / 环引）。详见 agent_dispatch_protocol.md「logic-only 模块说明」。
        # 注：此校验与 precheck_stage4.py check_scaffold 双层兜底（gen_scaffold 蓝图层闸 + precheck 终审闸）。
        if len(pages_field) == 0:
            ui_carriers = mod.get("ui_carrier_modules")
            if ui_carriers is None:
                errors.append(
                    f"[{mid}] pages=[] 视为 logic-only 模块，必须含 ui_carrier_modules 字段"
                    f"（指向承载本模块 UI 的模块 id 数组；详 agent_dispatch_protocol.md logic-only 说明）"
                )
            elif not isinstance(ui_carriers, list) or len(ui_carriers) == 0:
                errors.append(
                    f"[{mid}] ui_carrier_modules 必须为非空数组（当前：{ui_carriers!r}）"
                )
            else:
                # 自引检查（SSOT #50 D-自引防御）：本模块不可承载自己的 UI
                if mid in ui_carriers:
                    errors.append(
                        f"[{mid}] ui_carrier_modules 含本模块自身 id={mid!r}（自引非法，"
                        f"logic-only 模块的 UI 必须由其他承载模块承担）"
                    )
                # 引用完整性
                invalid_refs = [ref for ref in ui_carriers if ref not in all_mod_ids]
                if invalid_refs:
                    errors.append(
                        f"[{mid}] ui_carrier_modules 引用不存在的模块 id：{invalid_refs}"
                        f"（合法范围：{sorted(all_mod_ids)}）"
                    )
                # 禁指向其他 logic-only 模块（SSOT #50 D-链式/环引防御）：承载者必须是 pages 非空的真实 UI 模块
                # 收集所有 pages=[] 模块 id（含本模块），引用任一 pages=[] 即 FAIL
                logic_only_ids = {
                    m.get("id") for m in data.get("modules", [])
                    if m.get("id") and isinstance(m.get("pages"), list) and len(m.get("pages", [])) == 0
                }
                # 排除本模块自身（已被自引检查覆盖）+ 不存在引用（已被完整性检查覆盖），避免双报
                logic_only_refs = [
                    ref for ref in ui_carriers
                    if ref != mid and ref in all_mod_ids and ref in logic_only_ids
                ]
                if logic_only_refs:
                    errors.append(
                        f"[{mid}] ui_carrier_modules 指向其他 logic-only 模块：{logic_only_refs}"
                        f"（承载者必须是 pages 非空的真实 UI 模块；禁链式 / 禁环引）"
                    )
        # SSOT #74 页面集守恒：page_source 字段格式校验（R1，2026-06-09）
        # 每页可选 `page_source`：'stage2'（追溯阶段 2 §3.3 基线）/ 'director_approved:<YYYY-MM-DD>'
        # （escalation 批准）。**可选**——缺失不在此报错（迁移友好，由 precheck_stage4
        # check_page_source_provenance WARN 提醒）；仅当存在时校验格式合法。
        # 治实验报告决定性案例：PM 把内嵌子卡片擅自抬成独立页（阶段 2 基线未定义）。
        for page in pages_field if isinstance(pages_field, list) else []:
            if not isinstance(page, dict):
                continue
            ps = page.get("page_source")
            if ps is None:
                continue  # 可选字段，缺失不报错（precheck WARN 提醒）
            pid = page.get("id", "?")
            if ps == "stage2":
                continue
            if isinstance(ps, str) and ps.startswith("director_approved:"):
                date_part = ps[len("director_approved:"):]
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_part):
                    errors.append(
                        f"[{mid}/{pid}] page_source='director_approved:...' 后须接 "
                        f"YYYY-MM-DD 日期（当前：{ps!r}）"
                    )
                continue
            errors.append(
                f"[{mid}/{pid}] page_source={ps!r} 不合法（须为 'stage2' 或 "
                f"'director_approved:<YYYY-MM-DD>'；SSOT #74 页面集守恒）"
            )

        # SSOT #76 R3 内嵌子组件（embedded_components）结构校验（可选字段）：
        # 隶属某 page、含自己的 states（各带 prd_id），不占独立 page/route。
        # 治实验报告问题 4 根因：scaffold 缺"内嵌带状态构造" → PM 逼出页膨胀。
        # **可选**——无字段不报错（向后兼容）；存在则校验良构。全局 prd_id 唯一性
        # 由 precheck check_scaffold 终审（本处校蓝图层结构 + 页内唯一 + 父页作用域）。
        for page in pages_field if isinstance(pages_field, list) else []:
            if not isinstance(page, dict):
                continue
            embs = page.get("embedded_components")
            if embs is None:
                continue  # 可选字段缺省
            pid = page.get("id", "?")
            if not isinstance(embs, list):
                errors.append(
                    f"[{mid}/{pid}] embedded_components 字段存在但非数组（可选；填则须为数组）"
                )
                continue
            # 页内 prd_id 池（含直挂 states + 已校内嵌 states）查撞号 + 内嵌 id 页内唯一
            page_prd_ids: set[str] = {
                s.get("prd_id") for s in (page.get("states") or [])
                if isinstance(s, dict) and s.get("prd_id")
            }
            seen_emb_ids: set[str] = set()
            for ei, emb in enumerate(embs):
                if not isinstance(emb, dict):
                    errors.append(f"[{mid}/{pid}] embedded_components[{ei}] 必须是对象 {{id, states}}")
                    continue
                eid = emb.get("id")
                if not eid or not isinstance(eid, str):
                    errors.append(f"[{mid}/{pid}] embedded_components[{ei}] 缺合法 id（非空字符串）")
                elif eid in seen_emb_ids:
                    errors.append(f"[{mid}/{pid}] embedded_components id 页内重复：{eid!r}")
                else:
                    seen_emb_ids.add(eid)
                emb_states = emb.get("states")
                if not isinstance(emb_states, list) or not emb_states:
                    errors.append(
                        f"[{mid}/{pid}] embedded_components[{eid or ei}] states 必须为非空数组"
                        f"（内嵌子组件至少 1 个状态，各带 prd_id）"
                    )
                    continue
                for si, st in enumerate(emb_states):
                    if not isinstance(st, dict):
                        errors.append(f"[{mid}/{pid}] embedded_components[{eid or ei}].states[{si}] 非对象")
                        continue
                    if not st.get("name"):
                        errors.append(f"[{mid}/{pid}] embedded_components[{eid or ei}].states[{si}] 缺 name")
                    epid = st.get("prd_id")
                    if not epid or not isinstance(epid, str):
                        errors.append(
                            f"[{mid}/{pid}] embedded_components[{eid or ei}].states[{si}] 缺 prd_id"
                        )
                        continue
                    # 内嵌 prd_id 须作用域于父页（约定 H-M[XX]-P[XX]-<embed_id>-<state>）
                    expected_prefix = f"H-{mid}-{pid}-"
                    if not epid.startswith(expected_prefix):
                        errors.append(
                            f"[{mid}/{pid}] 内嵌 prd_id={epid!r} 须以 {expected_prefix!r} 开头"
                            f"（内嵌帧作用域于父页，约定 H-M[XX]-P[XX]-<embed_id>-<state>；SSOT #76）"
                        )
                    if epid in page_prd_ids:
                        errors.append(
                            f"[{mid}/{pid}] 内嵌 prd_id={epid!r} 与本页已有 prd_id 撞号"
                            f"（直挂 states 或其他内嵌状态）"
                        )
                    else:
                        page_prd_ids.add(epid)

        # candidate_components 必填
        if "candidate_components" not in mod:
            errors.append(f"[{mid}] 缺 candidate_components 字段（必填，含 pub + proj_gaps；空填 {{\"pub\": [], \"proj_gaps\": []}}）")
        else:
            cc = mod["candidate_components"]
            if not isinstance(cc.get("pub"), list):
                errors.append(f"[{mid}] candidate_components.pub 必须是数组")
            if not isinstance(cc.get("proj_gaps"), list):
                errors.append(f"[{mid}] candidate_components.proj_gaps 必须是数组")
            else:
                # SSOT #8 NB-WE-WE-D1: trigger 字段枚举校验
                # 合法值：A-D1 ~ A-D5（跨模块复用 + D1-D5 维度）/ B-D1 ~ B-D5（能力缺口 + D1-D5）
                # 详见 proj_component_protocol.md §一 双触发条件
                LEGAL_TRIGGERS = {
                    "A-D1", "A-D2", "A-D3", "A-D4", "A-D5",
                    "B-D1", "B-D2", "B-D3", "B-D4", "B-D5",
                }
                for gi, gap in enumerate(cc.get("proj_gaps", [])):
                    if not isinstance(gap, dict):
                        continue  # 由其他校验处理
                    trig = gap.get("trigger")
                    if trig is None:
                        errors.append(f"[{mid}] proj_gaps[{gi}] 缺 trigger 字段（合法枚举：A-D1~A-D5 / B-D1~B-D5）")
                    elif trig not in LEGAL_TRIGGERS:
                        errors.append(
                            f"[{mid}] proj_gaps[{gi}].trigger={trig!r} 非法（合法枚举：A-D1~A-D5 / B-D1~B-D5；"
                            f"详见 proj_component_protocol.md §一 双触发条件）"
                        )
        # owner_assignments 必填（空 {} 也要显式写）
        if "owner_assignments" not in mod:
            errors.append(f"[{mid}] 缺 owner_assignments 字段（必填；本模块非任何 proj 的 owner 时填空对象 {{}}）")
        elif not isinstance(mod["owner_assignments"], dict):
            errors.append(f"[{mid}] owner_assignments 必须是对象 {{proj_id: owner_module_id}}")
        else:
            for proj_id, declared_owner in mod["owner_assignments"].items():
                # 收集声明者，供下方跨模块冲突检测
                ownership_claims.setdefault(proj_id, []).append(mid)
                # value 必须等于声明该项的模块自身 id
                # （`pm-workflow/rules/agent_dispatch_protocol.md` v2.0「owner 推算规则」第 4 条：owner 模块在自己的
                # owner_assignments 中记录；非 owner 模块不记录该 proj——
                # 故 value 永远 = 声明它的模块 id，不会指向其他模块）
                if declared_owner != mid:
                    errors.append(
                        f"[{mid}] owner_assignments[{proj_id!r}] 值={declared_owner!r}，"
                        f"v2.0 规定 owner 模块在自己的 owner_assignments 中声明自身，应为 {mid!r}；"
                        f"如 {declared_owner!r} 才是真实 owner，应将该项移到 modules[{declared_owner!r}].owner_assignments"
                    )
        # depends_on 对象格式
        deps = mod.get("depends_on", [])
        if not isinstance(deps, list):
            errors.append(f"[{mid}] depends_on 必须是数组")
        else:
            for i, dep in enumerate(deps):
                if not isinstance(dep, dict):
                    errors.append(
                        f"[{mid}] depends_on[{i}] 必须是对象 {{module, kind, target}}；"
                        "v2.0 不再支持字符串数组格式，需结构化为对象"
                    )
                    continue
                for k in ("module", "kind", "target"):
                    if k not in dep:
                        errors.append(f"[{mid}] depends_on[{i}] 缺 {k} 字段")
                if dep.get("kind") not in VALID_DEPENDS_KINDS:
                    errors.append(
                        f"[{mid}] depends_on[{i}].kind={dep.get('kind')!r} 不在枚举 "
                        f"{sorted(VALID_DEPENDS_KINDS)} 内"
                    )

    # 跨模块 owner 冲突：同一 proj_id 被多个模块声明 → 下游 dict 静默覆盖
    # 会让任务卡 C 表 / PRD 草稿 OWNER-INFO / Step 5 编排器 prompt 三处
    # 拿到不一致的 owner，破坏 SSOT
    scaffold_module_ids_ordered = [
        m.get("id", "") for m in data.get("modules", []) if isinstance(m, dict)
    ]
    for proj_id, claimers in ownership_claims.items():
        if len(claimers) > 1:
            # 按 v2.0 owner 推算规则给出明确的修复指引
            expected_owner = next(
                (mid for mid in scaffold_module_ids_ordered if mid in claimers),
                claimers[0],
            )
            others = [m for m in claimers if m != expected_owner]
            errors.append(
                f"proj_id {proj_id!r} 被多个模块同时声明为 owner: {claimers}；"
                f"按 v2.0 owner 推算规则（共用模块 ∩ scaffold.modules[] 取顺序最靠前者），"
                f"仅 modules[{expected_owner!r}] 应保留 owner_assignments[{proj_id!r}]，"
                f"其余模块 {others} 须从各自 owner_assignments 中删除该项；"
                f"该项是 PM 子阶段一 dedupe 算法漏执行导致——通常 PM 把同一 proj 在每个共用模块里都标了 owner，"
                f"应改为仅在顺序最靠前者标注"
            )

    # ── 提议2（SSOT 双锚 #39）：page_archetypes 顶层定义 + 每页 archetype 引用 ──
    # 结构层 A 级硬兜底（首次闸，Step1.5）。注意：post-Foundation 不再重跑
    # gen_scaffold，故结构兜底由 precheck_stage4.check_page_archetype_contract
    # 在 Step6.5 承接（恒跑）；本处是蓝图层第一道闸（Step1.X 之前）。
    archetypes = data.get("page_archetypes")
    archetype_ids: set[str] = set()
    if archetypes is None:
        errors.append(
            "缺 page_archetypes 顶层字段（提议2 必填——页面结构范式契约定义本体；"
            "PM 子阶段一须按页面类型产出 list/detail/form 等范式，详见 "
            "agent_dispatch_protocol.md §scaffold v2.0 schema + proto_spec_md.md "
            "「页面结构范式契约」段）"
        )
    elif not isinstance(archetypes, list) or not archetypes:
        errors.append("page_archetypes 必须是非空数组（至少 1 个范式定义）")
    else:
        for i, arch in enumerate(archetypes):
            if not isinstance(arch, dict):
                errors.append(
                    f"page_archetypes[{i}] 必须是对象 "
                    f"{{id,name,regions,invariants,extension}}"
                )
                continue
            aid = arch.get("id")
            if not aid or not isinstance(aid, str):
                errors.append(f"page_archetypes[{i}] 缺合法 id（非空字符串）")
            elif aid in archetype_ids:
                errors.append(f"page_archetypes id 重复：{aid!r}")
            else:
                archetype_ids.add(aid)
            if not arch.get("name"):
                errors.append(f"page_archetypes[{aid or i}] 缺 name")
            regions = arch.get("regions")
            if not isinstance(regions, list) or not regions:
                errors.append(
                    f"page_archetypes[{aid or i}] regions 必须是非空数组"
                    f"（具名区域 + 容纳规则）"
                )
            else:
                for ri, reg in enumerate(regions):
                    if not isinstance(reg, dict) or "slot" not in reg or "hosts" not in reg:
                        errors.append(
                            f"page_archetypes[{aid or i}].regions[{ri}] "
                            f"必须含 slot + hosts 字段"
                        )
            for fld in ("invariants", "extension"):
                if not isinstance(arch.get(fld), list):
                    errors.append(
                        f"page_archetypes[{aid or i}] {fld} 必须是数组（无则填 []）"
                    )
            # SSOT #75-R5 archetype 语义匹配：可选 semantic_category 字段格式校验
            # （form/readonly-status/list/detail/modal-confirm/wizard/dialog-flow）。
            # **可选**——缺失不报错（precheck check_archetype_semantics 用关键字启发式降级）；
            # 仅当存在时校验枚举合法。治"只读页误套表单范式"——显式标语义类别后判定更准。
            sem = arch.get("semantic_category")
            if sem is not None and sem not in _VALID_ARCHETYPE_SEMANTICS:
                errors.append(
                    f"page_archetypes[{aid or i}] semantic_category={sem!r} 不在枚举 "
                    f"{sorted(_VALID_ARCHETYPE_SEMANTICS)} 内（SSOT #75-R5）"
                )

    # 每页必须声明 archetype 且引用合法（悬空引用 FAIL）
    if isinstance(archetypes, list) and archetypes:
        for mod in data.get("modules", []):
            mid = mod.get("id", "?")
            # 防御：pages 非 list 时不进入循环（已由前置校验 FAIL；此处防 crash）
            pages_raw = mod.get("pages")
            if not isinstance(pages_raw, list):
                continue
            for p in pages_raw:
                pid = p.get("id", "?")
                pa = p.get("archetype")
                if not pa:
                    errors.append(
                        f"[{mid}-{pid}] 缺 archetype 字段"
                        f"（必填，引用 page_archetypes[].id）"
                    )
                elif pa not in archetype_ids:
                    errors.append(
                        f"[{mid}-{pid}] archetype={pa!r} 悬空——不在 page_archetypes "
                        f"ids {sorted(archetype_ids)} 内"
                    )

    # 触点 canonical 校验（SSOT #44 / S4-34，item 6 治本①）：
    # pages[].touchpoints[] 为**可选**字段（向后兼容——缺省走旧两段式，下游无需破坏性迁移）；
    # 存在则须为良构：每项 dict 含 id（形如 T01/D01，页面内唯一）+ kind（trigger/data）+
    # element/action 描述。canonical 全量 ID = f"{mid}-{pid}-{tp.id}"，由 precheck
    # check_touchpoint_canonical 消费校验 spec/prd 引用 ⊆ canonical。
    _TP_ID_RE = re.compile(r"^[TD]\d{2}$")
    _TP_KINDS = {"trigger", "data"}
    for mod in data.get("modules", []):
        mid = mod.get("id", "?")
        # 防御：pages 非 list 时不进入循环（已由前置校验 FAIL；此处防 crash）
        pages_raw = mod.get("pages")
        if not isinstance(pages_raw, list):
            continue
        for p in pages_raw:
            pid = p.get("id", "?")
            tps = p.get("touchpoints")
            if tps is None:
                continue  # 可选字段缺省，跳过（向后兼容）
            if not isinstance(tps, list):
                errors.append(f"[{mid}-{pid}] touchpoints 字段存在但非数组（可选；填则须为数组）")
                continue
            seen_ids: set[str] = set()
            for ti, tp in enumerate(tps):
                if not isinstance(tp, dict):
                    errors.append(f"[{mid}-{pid}] touchpoints[{ti}] 非对象")
                    continue
                tid = tp.get("id")
                if not tid or not _TP_ID_RE.match(str(tid)):
                    errors.append(
                        f"[{mid}-{pid}] touchpoints[{ti}].id={tid!r} 非法"
                        f"（须形如 T01/D01：T=主页触点 / D=弹窗抽屉内触点，两位数字）"
                    )
                elif tid in seen_ids:
                    errors.append(f"[{mid}-{pid}] touchpoints[{ti}].id={tid!r} 页面内重复")
                else:
                    seen_ids.add(tid)
                kind = tp.get("kind")
                if kind is not None and kind not in _TP_KINDS:
                    errors.append(
                        f"[{mid}-{pid}] touchpoints[{ti}].kind={kind!r} 非法"
                        f"（合法：trigger / data；缺省不报错）"
                    )

    return errors


# ── 任务卡候选清单段衍生 ──────────────────────────────────────────────────────

def _resolve_proj_id(gap: dict, global_owners: dict | None = None) -> str:
    """根据 proj_gap 推算 proj 组件 id（proj.L{tier}.{name}）。

    等级解析优先级（从权威到 fallback）：
    1. global_owners（来自 _build_global_owners）中存在 `proj.LX.{name}` 形态的键 → 直接返回该键。
       owner_assignments 是 v2.0 schema 中 proj 等级的真源——L1 组件 inherits 通常为 null（无 pub 继承源），
       但其等级在 owner_assignments 的 proj id 字面值（如 `proj.L1.lang-switcher`）中被显式登记。
    2. 解析 inherits 字段中的 `L\\d+`（带 None / 空串容错）。inherits 多见于 L2/L3 组件（如 `pub.L2.card`）。
    3. 全部失败 → 标 `proj.LX.{name}`（X = 未知层级，下游可继续渲染但提示语义异常）。
    """
    name = gap.get("name", "?")

    if global_owners:
        for proj_id in global_owners:
            parts = proj_id.split(".")
            if len(parts) == 3 and parts[2] == name:
                return proj_id

    inherits = gap.get("inherits") or ""
    m = re.search(r"L(\d+)", inherits)
    tier = m.group(1) if m else "X"
    return f"proj.L{tier}.{name}"


def _build_global_owners(all_modules: list) -> dict[str, str]:
    """构建全局 owner 视图（proj_id → owner_module_id）。

    防御深度第二层：validate_v2_schema 已在 main 入口拦截多模块声明同一 proj_id
    的冲突；此处再加一次 assert，防止下游开发引入新代码路径绕过 validate
    （或测试桩直接调本函数）时静默丢失冲突信号。
    """
    owners: dict[str, str] = {}
    for m in all_modules:
        mid = m.get("id", "?")
        for proj_id, owner_mid in m.get("owner_assignments", {}).items():
            if proj_id in owners and owners[proj_id] != owner_mid:
                raise ValueError(
                    f"内部不变量违反：proj_id {proj_id!r} 在 modules[{owners[proj_id]!r}] "
                    f"和 modules[{mid!r}] 中均声明为 owner（owner_mid 分别为 "
                    f"{owners[proj_id]!r} / {owner_mid!r}）。validate_v2_schema 应已在 main "
                    f"入口拦下此冲突；本异常说明调用路径绕过了 schema 校验。"
                )
            owners[proj_id] = owner_mid
    return owners


def build_candidate_section(mod: dict, all_modules: list) -> str:
    """衍生任务卡「候选组件清单」段内容。"""
    cc = mod.get("candidate_components", {})
    pub_list = cc.get("pub", [])
    proj_gaps = cc.get("proj_gaps", [])

    # 全局 owner 视图（proj_id → owner_module_id）
    global_owners = _build_global_owners(all_modules)

    parts: list[str] = []
    # A 表
    parts.append("### A. 候选 pub 组件（衍生自 scaffold.candidate_components.pub）\n")
    if pub_list:
        parts.append("| 组件 id | 业务用途 |")
        parts.append("|---------|---------|")
        for p in pub_list:
            parts.append(f"| `{p.get('id', '?')}` | {p.get('purpose', '')} |")
    else:
        parts.append("（本模块无候选 pub 组件）")
    parts.append("")
    # B 表
    parts.append("### B. 候选派生 proj 组件（衍生自 scaffold.candidate_components.proj_gaps）\n")
    if proj_gaps:
        parts.append("| 候选 proj 名 | 触发因素 | 派生原因 | inherits | 共用模块 |")
        parts.append("|-------------|---------|---------|---------|---------|")
        for g in proj_gaps:
            shared = g.get("shared_with_modules") or []
            shared_set = sorted(set([mod["id"]] + shared))
            shared_str = " / ".join(shared_set)
            parts.append(
                f"| `{_resolve_proj_id(g, global_owners)}` | {g.get('trigger', '?')} | "
                f"{g.get('reason', '')} | `{g.get('inherits') or ''}` | {shared_str} |"
            )
    else:
        parts.append("（本模块无 proj 派生缺口）")
    parts.append("")
    # C 表
    parts.append("### C. owner 分配（衍生自 scaffold.modules[].owner_assignments）\n")
    if proj_gaps:
        parts.append("| proj 组件 | 本模块是否 owner | owner 模块 |")
        parts.append("|----------|----------------|----------|")
        for g in proj_gaps:
            proj_id = _resolve_proj_id(g, global_owners)
            owner = global_owners.get(proj_id, "?")
            mark = "✅ 是" if owner == mod["id"] else "❌ 否（仅引用 class）"
            parts.append(f"| `{proj_id}` | {mark} | {owner} |")
    else:
        parts.append("（本模块无 proj 组件，无 owner 分配）")
    parts.append("")
    # D 表
    parts.append("### D. 跳过说明")
    parts.append("")
    if not pub_list and not proj_gaps:
        parts.append("- 子阶段一已扫描维度：D1 字段 / D2 状态 / D3 交互 / D4 语义 / D5 约束 全部通过")
        parts.append("- 结论：本模块未识别需要的 pub / proj 组件（裸文本/纯展示模块）")
    else:
        parts.append("（本模块有候选，跳过说明不适用）")

    return "\n".join(parts)


def update_task_card_candidate_section(
    task_card_path: Path, mod: dict, all_modules: list
) -> bool:
    """替换任务卡「## 候选组件清单」段内容。返回是否实际更新。"""
    if not task_card_path.exists():
        return False
    text = task_card_path.read_text(encoding="utf-8")
    start_re = re.compile(r"^## 候选组件清单.*?$", re.MULTILINE)
    next_section_re = re.compile(r"^## ", re.MULTILINE)
    m = start_re.search(text)
    if not m:
        return False
    next_match = next_section_re.search(text, m.end())
    end_pos = next_match.start() if next_match else len(text)
    content = build_candidate_section(mod, all_modules)
    new_block = (
        f"## 候选组件清单（v2.0 自动衍生 — gen_scaffold 在 Step 1.5 注入，PM 不手填）\n\n"
        f"> **数据真源**：scaffold.json `modules[{mod['id']}].candidate_components` 与 `modules[].owner_assignments`\n"
        f"> **衍生时间**：{datetime.now().isoformat(timespec='seconds')}\n\n"
        f"{content}\n\n"
    )
    new_text = text[: m.start()] + new_block + text[end_pos:]
    task_card_path.write_text(new_text, encoding="utf-8")
    return True


# ── 页面骨架屏占位（SSOT 双锚 #41）────────────────────────────────────────────
# WE-H（2026-05-19，#41 颗粒度重设 per-page → per-archetype + 条件 per-page
# override）：#41 = #39 的视觉化身，单源从 per-page 改为 **per-archetype**。
# 单源 = Foundation 草稿 `spec_foundation_draft.md`「## 范式骨架」段内每 archetype
# 一 ```skeleton 块（Foundation 子阶段二填一次，按 `**<aid> 名称**` 锚行键）；
# assemble.build_archetype_skeleton_md/_html 提取 → 注入 spec §3.0「范式骨架」
# 子节（#39 契约表后，子决策B 独立子节）+ 镜像 PRD spec-sitemap（per-archetype
# 是 ~N 小目录，pre-WE-E 画廊位对其本就正确）。**默认页复用其 archetype 骨架
# （零 per-page 撰写）**；per-page ```skeleton 槽改 **override-only**——仅当本页
# 2D 排布确无法套范式骨架（罕见，PM 判断层不机械化）才在模块草稿 per-page 填。
# SKELETON_DISCLAIMER 真源 = proto_spec_md.md §四「页面结构（骨架屏）」首行免责注释；
# 本常量 / precheck_stage4 S4-32 / prd_expression_standard §A-09 须与之字面一致
# （调整方向：先改 proto_spec_md.md §四，再同步本常量 + precheck + standard，禁反向）。
SKELETON_DISCLAIMER = (
    "<!-- 平面布局示意，非组件层级/非实现 DOM 依据；容纳权威归 page_archetypes(#39) -->"
)


def _archetype_region_slots(arch: dict) -> str:
    """本范式可用 data-r 取值 = regions[].slot ∪ extension（提示串，给 Foundation
    填骨架时对照；与 precheck S4-32「data-r ⊆ 该 archetype regions∪extension」同一
    #39 权威）。"""
    slots = [r.get("slot", "") for r in (arch.get("regions") or []) if r.get("slot")]
    slots += [e for e in (arch.get("extension") or []) if e]
    return "、".join(f"`{s}`" for s in slots) or "（本范式未声明 regions/extension）"


def _archetype_skeleton_placeholder(arch: dict) -> str:
    """每 archetype 一 ```skeleton 占位块（Foundation 子阶段二替换为该范式的代表性
    2D 平面布局骨架，一次定义、被所有引用该范式的页复用）。首行恒为
    SKELETON_DISCLAIMER（S4-32 字面校验）；占位 region data-r 留空 → Foundation
    未填时 precheck S4-32「每 archetype 有良构骨架 + data-r ⊆ 该 archetype
    regions∪extension」自然命中（WARN 档 C，暴露漏填非静默放行）。

    WE-G 条件 per-platform（SSOT #41，archetype 级复用）：默认单块 ` ```skeleton `
    （agnostic，应用本范式全平台）；**仅当本范式 2D 布局跨产品平台实质发散**
    （如 phone 竖叠+底导 vs desktop 侧栏+多列）时，Foundation 将本单块替换为
    **多个** ` ```skeleton:{frame} ` 块（frame ∈ phone|desktop|tablet|h5|mp，
    对齐帧 class 根），一范式内 EITHER 1 agnostic OR ≥1 per-platform、不混用。
    1-vs-N 由 Foundation 按布局是否发散判断（判断层、非机械强制）。"""
    return (
        "```skeleton\n"
        f"{SKELETON_DISCLAIMER}\n"
        "<!-- Foundation 填：本范式代表性平面布局骨架（一次定义，所有引用本范式的页\n"
        "     复用）。仅 <div>；class ∈ {sk-page,sk-row,sk-col,sk-region}；属性仅\n"
        f"     data-r(区域键,须 ⊆ 本范式 regions∪extension：{_archetype_region_slots(arch)})\n"
        "     /data-w(同级占比%)/data-h(高 px)；禁真实组件标签/inline style/真实\n"
        "     文案/嵌套>3层。\n"
        "     【WE-G 条件 per-platform】默认本单块=全平台通用；若本范式布局跨端\n"
        "     实质发散，改为多个围栏 ```skeleton:phone / ```skeleton:desktop /\n"
        "     ```skeleton:tablet / ```skeleton:h5 / ```skeleton:mp（一范式 EITHER\n"
        "     单 agnostic OR 多 per-platform、不混用；发散与否由 Foundation 判断）。\n"
        "     详 proto_spec_md.md §四「页面结构（骨架屏，SSOT #41）」 -->\n"
        '<div class="sk-page">\n'
        '  <div class="sk-region" data-r="">[替换为本范式真实区域；data-r 取本范式 regions slot / extension]</div>\n'
        "</div>\n"
        "```"
    )


def _spec_page_override_marker(aid: str) -> str:
    """per-page 骨架槽（WE-H override-only）：默认页复用其 archetype 范式骨架，
    **不写 ```skeleton 块**——故占位为纯注释 marker（非空 data-r 的活动围栏，
    避免重演"每页必填"压力 / SNB-006）。仅当本页 2D 排布确无法套用范式骨架
    （罕见，PM 判断层不机械化）时，PM 才在本 marker 处**新增**一个
    ```skeleton 覆盖块（格式同范式骨架；首行免责注释；data-r ⊆ 本页 archetype
    regions∪extension；可 per-platform）；assemble.extract_spec_skeletons 仅对
    有 override 围栏的页 fire（无围栏 = 复用范式 = 不提取、不 FAIL）。"""
    return (
        f"<!-- 页面骨架：默认复用本页 archetype `{aid}` 的范式骨架"
        "（见 spec §3.0「范式骨架」子节 / PRD 页面架构总览），**无需在此填写**。\n"
        "     仅当本页 2D 排布确无法套用该范式骨架（罕见）时，才在本注释下方\n"
        "     新增一个 ```skeleton 覆盖块（格式同范式骨架：首行固定免责注释；\n"
        "     仅 sk-* div；data-r ⊆ 本页 archetype 的 regions∪extension；如跨端\n"
        "     发散可改多个 ```skeleton:{phone|desktop|tablet|h5|mp}）。是否 override\n"
        "     由 PM 判断（非机械强制）。详 proto_spec_md.md §四「页面结构（骨架屏，\n"
        "     SSOT #41）」 -->"
    )


# ── 模块草稿骨架 ──────────────────────────────────────────────────────────────

def build_spec_module_draft(mod: dict) -> str:
    states_rows = []
    for page in mod["pages"]:
        for state in page["states"]:
            states_rows.append(
                f"| {page['id']} | {state['name']} | [触发条件] | [主要差异] | `{state['prd_id']}` |"
            )
    states_table = (
        "| 页面 | 状态名 | 触发条件 | 主要差异 | prd_id |\n"
        "|------|--------|---------|---------|--------|\n"
        + "\n".join(states_rows)
    )

    deps_lines: list[str] = []
    for dep in mod.get("depends_on", []):
        deps_lines.append(
            f"- 依赖模块 `{dep.get('module','?')}`（kind: `{dep.get('kind','?')}`）→ target: `{dep.get('target','?')}`"
        )
    deps_section = "\n".join(deps_lines) if deps_lines else "（本模块无跨模块依赖）"

    # 触点表 canonical 预生成（item 6 治本①，SSOT #44）：若 scaffold.pages[].touchpoints[]
    # 存在，则按 canonical ID `{mid}-{pid}-{tp.id}` 预填行（Spec Agent 只补描述列，禁增删/改 ID）；
    # 缺省（无 touchpoints）则保留旧静态占位 + 两段式提示（向后兼容）。
    _tp_rows: list[str] = []
    for p in mod["pages"]:
        for tp in p.get("touchpoints", []) or []:
            tid = tp.get("id", "?")
            canonical = f"{mod['id']}-{p['id']}-{tid}"
            element = tp.get("element", "[元素]")
            action = tp.get("action", "[动作]")
            state = tp.get("state", "[状态]")
            _tp_rows.append(
                f"| {canonical} | {state} | {element} | {action} | [响应] |"
            )
    if _tp_rows:
        touchpoint_body = "\n".join(_tp_rows)
        touchpoint_hint = (
            f"[触点 ID 已由 scaffold canonical 预生成（{len(_tp_rows)} 个，SSOT #44）；"
            f"Spec Agent **仅补全描述列（元素 / 触发动作 / 系统响应）**，"
            f"**禁止增删 / 修改触点 ID**——如需增删触点须回 scaffold 改 touchpoints[] 重跑 gen_scaffold]"
        )
    else:
        touchpoint_body = f"| {mod['id']}-P01-T01 | [状态] | [元素] | [动作] | [响应] |"
        touchpoint_hint = (
            f"[Spec Agent 按本模块状态枚举 + 业务交互产出全部触点；"
            f"ID 格式 {mod['id']}-P[XX]-T[NN]，弹窗用 D 替换 T。"
            f"**[Should] 治本路径**：在 scaffold.pages[].touchpoints[] 预声明触点 canonical，"
            f"由 gen_scaffold 预生成本表 ID 行（避免手写偏差，SSOT #44）]"
        )

    # S2.M[XX].1 per-page 块：`**P[XX] 页面名**` 锚行（assemble.py 据此映射
    # override skeleton→页面，SSOT #41）+ 交互意图占位 + per-page 骨架槽
    # （WE-H override-only：默认复用本页 archetype 范式骨架，纯注释 marker；
    # 仅本页无法套范式才在此新增 ```skeleton 覆盖块）。
    page_overview_blocks = []
    for p in mod["pages"]:
        page_overview_blocks.append(
            f"- **{p['id']} {p['name']}** · 路由 `{p['route']}` · 共 {len(p['states'])} 个状态\n\n"
            f"[Spec Agent 填：{p['name']} 主要交互意图 / 业务流程入口 / 与其他页面关系]\n\n"
            f"{_spec_page_override_marker(p.get('archetype', '?'))}"
        )
    pages_overview = "\n\n".join(page_overview_blocks)

    return f"""\
# spec — {mod['id']} {mod['name']}（草稿）

> 本草稿由 `gen_scaffold.py` 在 Step 1.5 生成。Step 3 模块 Spec PM **在固定占位填空**，禁止改章节顺序/标题。
> 拼装时 `assemble.py spec` 按 scaffold modules 顺序追加到 `outputs/spec_*_latest.md`。

## S2.{mod['id']} 模块概述

[Spec Agent 填：模块业务定位 / 关键路由 / 核心角色 / 与产品定义 §7 的功能映射]

## S2.{mod['id']}.1 页面概述

页面清单已由 scaffold 锁定，禁止增删；**每页须填** `**P[XX] …**` 锚行下的交互意图段。**骨架屏（SSOT #41，WE-H per-archetype）**：默认本页复用其 `archetype` 的范式骨架（Foundation 子阶段二在 `spec_foundation_draft.md`「## 范式骨架」按范式填一次，单源；详 `proto_spec_md.md` §四「页面结构（骨架屏，SSOT #41）」+ §三.5）——per-page 槽为纯注释 marker，**无需逐页填骨架**；仅当本页 2D 排布确无法套用范式骨架（罕见，PM 判断）时，才在该页 marker 下新增一个 ```skeleton 覆盖块（首行免责注释字面不可改、`data-r` 须 ⊆ 本页 archetype 的 regions∪extension，precheck S4-32 校验）：

{pages_overview}

## S2.{mod['id']}.2 状态枚举

{states_table}

[Spec Agent 补全上表「触发条件」与「主要差异」列]

## S2.{mod['id']}.3 触点表

| 触点 ID | 所在状态 | 元素 | 触发动作 | 系统响应 |
|---------|---------|------|---------|---------|
{touchpoint_body}

{touchpoint_hint}

## S2.{mod['id']}.4 数据字段绑定

| 页面 | 字段名 | 类型 | 来源（spec §9）| 必填 |
|------|-------|------|--------------|------|
| P01 | [字段] | string | [§9.X] | ✓ |

[Spec Agent 按页面表单元素逐项填入；纯展示元素免填本表]

## S2.{mod['id']}.5 跨模块跳转引用

{deps_section}

[Spec Agent 在每条依赖下展开：跳转触发条件 / 携带参数 / 返回行为；本表与 scaffold.depends_on 一一对应]

## S2.{mod['id']}.6 API 摘要（详 产品定义 §10）

[Spec Agent 按本模块涉及 API 编号补全：`| API 编号 | 端点摘要 | 触发场景 | 真源引用 |` 4 列；模块**无 API 涉及**时本段可省略；SSOT #61 [Should] 升级后 .6 编号空间。v2.0 .6 异常路径已撤销 → §S5 异常场景全景（Foundation 子阶段二在 spec_foundation_draft.md 撰写）]
"""


def build_prd_module_draft(mod: dict, all_modules: list) -> str:
    # 从全局 owner_assignments 计算本模块对每个 proj 的归属
    global_owners = _build_global_owners(all_modules)

    # 本模块 proj_gaps 涉及的全部 proj id
    my_gaps_ids = {_resolve_proj_id(g, global_owners) for g in mod.get("candidate_components", {}).get("proj_gaps", [])}
    # 加上其他模块声明 owner=本模块 的（按理 my_gaps_ids 应已包含）
    for proj_id, owner_mid in global_owners.items():
        if owner_mid == mod["id"]:
            my_gaps_ids.add(proj_id)

    owner_lines: list[str] = []
    is_owner_for_any = False
    for proj_id in sorted(my_gaps_ids):
        owner = global_owners.get(proj_id, "?")
        if owner == mod["id"]:
            owner_lines.append(f"  - {proj_id}: ✅ owner（须写完整 PROJ-CSS）")
            is_owner_for_any = True
        else:
            owner_lines.append(f"  - {proj_id}: ❌ non-owner（仅引用 class，禁止重复声明 CSS）")

    if owner_lines:
        owner_block = (
            "<!-- [OWNER-INFO]\n"
            f"  本模块对本期 proj 组件的归属（编排器从 scaffold.owner_assignments 读出）：\n"
            + "\n".join(owner_lines) + "\n-->"
        )
    else:
        owner_block = "<!-- [OWNER-INFO] 本模块无 proj 组件归属（candidate_components.proj_gaps 为空） -->"

    if is_owner_for_any:
        proj_css = (
            "<!-- [PROJ-CSS-START] -->\n"
            "/* PRD Agent 填：本模块作为 owner 的 proj 组件完整 CSS（base + 全部 needed:yes 状态 modifier）*/\n"
            "<!-- [PROJ-CSS-END] -->"
        )
    else:
        proj_css = "<!-- 本模块非任何 proj 的 owner，禁写 PROJ-CSS 块 -->"

    def _frame_block(prd_id: str, page_name: str, state_name: str) -> str:
        # 草稿骨架结构（与 prd_template.html / prd_expression_standard.md §四 / task_card_template.md SSOT 双锚一致）：
        #   - frame-card：仅包裹 frame-wrapper（视觉帧主体）
        #   - interaction-card：proto-section 直接子元素，与 frame-card 同级兄弟（位于 frame-card 之后）
        #   - 两者共同被 [FRAME: prd_id]...[/FRAME: prd_id] 标记包裹（assemble.py 整体替换主 PRD 占位）
        return (
            f"<!-- [FRAME: {prd_id}] -->\n"
            f'<div class="frame-card">\n'
            f'  <div class="frame-wrapper">\n'
            f"    <!-- PRD Agent 填：{page_name} - {state_name} 视觉帧（phone-frame / desktop-frame / tablet-frame 等） -->\n"
            f'  </div>\n'
            f'</div>\n'
            f'<div class="interaction-card">\n'
            f"  <!-- PRD Agent 填：{page_name} - {state_name} 交互说明（触点说明 / 数据回显 / 边缘情况 / 业务规则） -->\n"
            f'</div>\n'
            f"<!-- [/FRAME: {prd_id}] -->"
        )

    frame_blocks = []
    for page in mod["pages"]:
        for state in page["states"]:
            frame_blocks.append(_frame_block(state["prd_id"], page["name"], state["name"]))
        # 内嵌子组件 FRAME 块（embedded_components,SSOT #76 R3）：每个内嵌状态出一个
        # FRAME 草稿块（PM 填视觉帧 + 交互说明；assemble extract_frames 自动提取注入
        # outputs/prd 内嵌 placeholder）。字段缺省 → 不进入循环（向后兼容，零变化）。
        for emb in page.get("embedded_components", []) or []:
            emb_name = emb.get("name", emb["id"])
            for state in emb.get("states", []) or []:
                frame_blocks.append(
                    _frame_block(state["prd_id"], f"{page['name']} · {emb_name}", state["name"])
                )

    return f"""<!-- prd 草稿 — {mod['id']} {mod['name']} -->
<!-- 由 gen_scaffold.py 在 Step 1.5 生成。Step 5 模块 PRD PM 在 FRAME 占位填内容，禁止改 FRAME id / 增删 FRAME。 -->
<!-- 拼装时 assemble.py prd 提取 FRAME 内容替换 prd 主文件占位。 -->

{owner_block}

{proj_css}

{chr(10).join(frame_blocks)}
"""


# ── Foundation 范式骨架草稿（SSOT #41 per-archetype 单源，WE-H）──────────────
# 单源 = 本草稿「## 范式骨架」段内每 archetype 一 ```skeleton 块；Foundation
# 子阶段二填一次（按 `**<aid> 名称**` 锚行键，与 per-page `**P[XX]**` 锚同型）；
# assemble.extract_archetype_skeletons 据此提取 → build_archetype_skeleton_md/_html
# 注入 spec §3.0「范式骨架」子节（#39 契约表后）+ 镜像 PRD spec-sitemap。
FOUNDATION_SKELETON_DRAFT_NAME = "spec_foundation_draft.md"


def build_foundation_skeleton_draft(data: dict) -> str:
    """生成 Foundation 范式骨架草稿（每 archetype 一 ```skeleton 占位，按
    `**<aid> 名称**` 锚行键）。无 page_archetypes（向后兼容 / agnostic scaffold）
    → 仍出草稿但「## 范式骨架」段写明 N/A（assemble.build_archetype_skeleton_*
    无 archetype 时返回 "" 优雅降级，§3.0 范式骨架子节不生成）。"""
    archs = data.get("page_archetypes") or []
    if not archs:
        body = (
            "> 本 scaffold 无 `page_archetypes`（向后兼容 / 平台无关场景）——"
            "本产品不适用 per-archetype 范式骨架，§3.0「范式骨架」子节不生成"
            "（assemble 优雅降级）。\n"
        )
    else:
        blocks = []
        for a in archs:
            aid = a.get("id", "?")
            aname = a.get("name", "")
            blocks.append(
                f"- **{aid} {aname}**\n\n"
                f"[Foundation 填：本范式代表性 2D 平面布局意图 / 区域职责说明]\n\n"
                f"{_archetype_skeleton_placeholder(a)}"
            )
        body = "\n\n".join(blocks)
    return f"""\
# spec — 页面范式骨架（Foundation 草稿，SSOT #41 per-archetype 单源）

> 本草稿由 `gen_scaffold.py` 在 Step 1.5 生成。**Foundation Agent 子阶段二**按
> 范式逐个填 ```skeleton 平面布局骨架（一次定义、所有引用该范式的页复用），
> 禁止改章节顺序 / 标题 / 增删 archetype 锚行（锚源 = scaffold.page_archetypes）。
> `assemble.py spec/prd` 提取「## 范式骨架」段 → 注入 spec §3.0「范式骨架」
> 子节（#39 契约表后）+ 镜像 PRD 页面架构总览（禁手改 outputs）。
> **per-page override**：默认页复用本范式骨架（零 per-page 撰写）；仅个别页
> 2D 排布确无法套范式（罕见）才在对应模块草稿 `spec_M[XX]_draft.md` 的该页
> per-page 槽新增 ```skeleton 覆盖块（详 `proto_spec_md.md` §四 / §三.5）。

## 范式骨架

{body}
"""


def generate_module_drafts(modules: list, drafts_dir: Path, force: bool, prune_orphans: bool = False) -> None:
    drafts_dir.mkdir(parents=True, exist_ok=True)
    for mod in modules:
        spec_p = drafts_dir / f"spec_{mod['id']}_draft.md"
        prd_p = drafts_dir / f"prd_{mod['id']}_draft.html"

        # 幂等：草稿已存在且非空 → 跳过（避免覆盖 PM 已填内容）
        if spec_p.exists() and spec_p.stat().st_size > 100 and not force:
            print(f"  [skip] {spec_p.name}（已存在；--force-rescaffold 可覆盖）")
        else:
            spec_p.write_text(build_spec_module_draft(mod), encoding="utf-8")
            print(f"  [+] {spec_p.name}")

        if prd_p.exists() and prd_p.stat().st_size > 100 and not force:
            print(f"  [skip] {prd_p.name}（已存在；--force-rescaffold 可覆盖）")
        else:
            prd_p.write_text(build_prd_module_draft(mod, modules), encoding="utf-8")
            print(f"  [+] {prd_p.name}")

    # —— 孤立草稿检测（变更后旧 modules 已不在 scaffold 中但 drafts 残留）——
    # 触发场景：自然语言调整 / changeRequest 删除模块 / 模块 ID 重排（最危险，含语义错配）
    current_ids = {mod["id"] for mod in modules}
    orphans: list[Path] = []
    for f in drafts_dir.glob("spec_M*_draft.md"):
        mod_id = f.stem.removeprefix("spec_").removesuffix("_draft")
        if mod_id not in current_ids:
            orphans.append(f)
    for f in drafts_dir.glob("prd_M*_draft.html"):
        mod_id = f.stem.removeprefix("prd_").removesuffix("_draft")
        if mod_id not in current_ids:
            orphans.append(f)

    if orphans:
        if prune_orphans:
            for f in orphans:
                f.unlink()
                print(f"  [pruned orphan] {f.name}")
            print(f"  → 已清理 {len(orphans)} 个孤立草稿")
        else:
            print(f"\n[WARN] 发现 {len(orphans)} 个孤立草稿（scaffold 中已无对应模块）：", file=sys.stderr)
            for f in sorted(orphans):
                print(f"  - {f.name}", file=sys.stderr)
            print(
                "  → 加 --prune-orphans 自动删除；或手动 rm 后继续。"
                "未清理可能导致 assemble.py 拒绝拼装（双向检测）",
                file=sys.stderr,
            )


# ── 主入口 ────────────────────────────────────────────────────────────────────

def _prune_old_backups(keep: int = 20) -> None:
    """保留策略：BACKUP_DIR 只留最近 keep 个备份目录（assemble.py 同款 helper）。"""
    if not BACKUP_DIR.exists():
        return
    dirs = sorted(d for d in BACKUP_DIR.iterdir() if d.is_dir())
    for old in dirs[:-keep] if len(dirs) > keep else []:
        import shutil
        shutil.rmtree(old, ignore_errors=True)


def backup_before_rescaffold() -> None:
    """B1（SSOT #80）：--force-rescaffold 会覆盖已填 module drafts + outputs 骨架,
    覆盖前自动快照 drafts/ + outputs/ 防 PM 积累被冲掉找不回。"""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # 与 assemble 统一 UTC
    dest = BACKUP_DIR / f"{ts}_rescaffold"
    n = 0
    for src_dir, sub in ((DRAFTS_DIR, "drafts"), (OUTPUT_DIR, "outputs")):
        if not src_dir.exists():
            continue
        for f in sorted(src_dir.glob("*")):
            if f.is_file():
                d = dest / sub / f.name
                d.parent.mkdir(parents=True, exist_ok=True)
                d.write_bytes(f.read_bytes())
                n += 1
    if n:
        print(
            f"[BACKUP] --force-rescaffold 覆盖前已快照 {n} 个 drafts/outputs 文件 → {dest}",
            file=sys.stderr,
        )
        _prune_old_backups()


def main():
    args = sys.argv[1:]
    # 两个独立的强制覆盖标志（避免一个 --force 同时跳过多个保护机制）
    force_rescaffold = "--force-rescaffold" in args  # 覆盖 Foundation 已写入的骨架
    skip_task_card_check = "--skip-task-card-check" in args  # 跳过任务卡完整性检查
    prune_orphans = "--prune-orphans" in args  # 清理 scaffold 中已无对应模块的孤立草稿
    # 兼容旧 --force：同时启用以上两项（仍保留但建议改用细分标志）
    legacy_force = "--force" in args
    if legacy_force:
        force_rescaffold = True
        skip_task_card_check = True
        print(
            "[NOTE] --force 已拆分为 --force-rescaffold + --skip-task-card-check 两个独立标志；"
            "继续兼容旧 --force（同时启用），但推荐改用细分标志以精确控制副作用。\n",
            file=sys.stderr,
        )
    args = [
        a for a in args
        if a not in ("--force", "--force-rescaffold", "--skip-task-card-check", "--prune-orphans")
    ]
    scaffold_path = Path(args[0]) if args else DEFAULT_SCAFFOLD

    for path, desc in [(scaffold_path, "scaffold.json"), (TEMPLATE, "prd_template.html")]:
        if not path.exists():
            print(f"[ERROR] {desc} 不存在：{path}", file=sys.stderr)
            sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    if force_rescaffold:
        backup_before_rescaffold()  # B1 SSOT #80：破坏性覆盖 drafts/outputs 前先快照

    data = json.loads(scaffold_path.read_text(encoding="utf-8"))
    modules = data["modules"]
    product = data["product"]

    # ── v2.0 schema 校验 ──
    schema_errors = validate_v2_schema(data)
    if schema_errors and not skip_task_card_check:
        print("[ABORT] scaffold.json v2.0 schema 校验失败：", file=sys.stderr)
        for e in schema_errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            "\nv2.0 schema 要求：schema_version='v2.0' / 每模块含 candidate_components / owner_assignments / depends_on（对象数组）。"
            "详见 `pm-workflow/rules/agent_dispatch_protocol.md` §阶段四 Step 1 的「scaffold v2.0 schema」段。"
            "如确认本期跳过校验（如旧项目暂不升级），加 --skip-task-card-check 显式忽略：\n"
            f"  python pm-workflow/scripts/gen_scaffold.py --skip-task-card-check\n",
            file=sys.stderr,
        )
        sys.exit(1)
    elif schema_errors and skip_task_card_check:
        print(
            f"[WARN] --skip-task-card-check 跳过 v2.0 schema 校验（{len(schema_errors)} 项警告）",
            file=sys.stderr,
        )
        for e in schema_errors[:3]:
            print(f"  - {e}", file=sys.stderr)
        if len(schema_errors) > 3:
            print(f"  ... 等 {len(schema_errors)} 项", file=sys.stderr)

    # ── 任务卡完整性检查（必含「候选组件清单」段，N25 拦截 PM 子阶段一漏填）──
    missing_task_card_sections: list[tuple[str, str]] = []
    for mod in modules:
        task_card_path = REPO_ROOT / mod.get("task_card", "")
        if not task_card_path.exists():
            missing_task_card_sections.append((mod.get("id", "?"), f"任务卡不存在：{task_card_path}"))
            continue
        text = task_card_path.read_text(encoding="utf-8")
        if "## 候选组件清单" not in text:
            missing_task_card_sections.append(
                (mod.get("id", "?"), f"任务卡 {task_card_path.name} 缺「## 候选组件清单」段")
            )

    if missing_task_card_sections and not skip_task_card_check:
        print("[ABORT] 任务卡完整性检查不通过：", file=sys.stderr)
        for mid, msg in missing_task_card_sections:
            print(f"  [{mid}] {msg}", file=sys.stderr)
        print(
            "\n按 PM Agent 子阶段一约定，每张任务卡必含「## 候选组件清单」段（A 候选 pub / B 候选派生 proj / C 跳过判定 三张表）。"
            "请补填后重跑；若确认本期跳过此约束（如历史项目迁移），加 --skip-task-card-check 显式忽略（不会同时影响 Foundation 幂等保护）：\n"
            f"  python pm-workflow/scripts/gen_scaffold.py --skip-task-card-check\n",
            file=sys.stderr,
        )
        sys.exit(1)
    elif missing_task_card_sections and skip_task_card_check:
        print(
            f"[WARN] --skip-task-card-check 跳过任务卡完整性检查（{len(missing_task_card_sections)} 张任务卡缺『候选组件清单』段）"
            "；下游 Spec/PRD Agent 将无法复用候选清单，可能漏识别 proj 派生缺口。\n",
            file=sys.stderr,
        )

    spec_path = OUTPUT_DIR / f"spec_{product}_latest.md"
    prd_path = OUTPUT_DIR / f"prd_{product}_latest.html"

    # ── 幂等检测 ──
    written_signals = detect_foundation_written(spec_path, prd_path)
    new_hash = hash_scaffold(scaffold_path)
    old_hash = read_scaffold_lock()

    if written_signals and not force_rescaffold:
        print("[ABORT] 检测到骨架已被后续 Step 写入：", file=sys.stderr)
        for sig in written_signals:
            print(f"  - {sig}", file=sys.stderr)
        print(
            "\n再次运行 gen_scaffold.py 会覆盖这些产物（含 Foundation 写入的 S0/S0.5/S1 与产品规格区）。"
            "若确认要重新生成骨架（如 /changeRequest 触发 scaffold.json 编号变更），请加 --force-rescaffold：",
            file=sys.stderr,
        )
        print(f"  python pm-workflow/scripts/gen_scaffold.py --force-rescaffold\n", file=sys.stderr)
        if old_hash and old_hash != new_hash:
            print(
                f"[WARN] scaffold.json 已变更（hash 不一致）。"
                f"按 `pm-workflow/rules/agent_dispatch_protocol.md`「编号锁定」原则，scaffold.json 在任务规划阶段后**不得修改**。"
                f"如确需变更编号，应走 /changeRequest 流程而非直接修改 scaffold.json + 重跑 gen_scaffold。\n",
                file=sys.stderr,
            )
        sys.exit(1)

    if old_hash and old_hash != new_hash and force_rescaffold:
        print(
            f"[WARN] --force-rescaffold 重跑：scaffold.json hash 已变更，"
            f"将会覆盖现有骨架与 Foundation 写入内容。请确认下游 Step 重跑路径。\n",
            file=sys.stderr,
        )

    spec_path = generate_spec_skeleton(data, OUTPUT_DIR)
    prd_path = generate_prd_skeleton(data, TEMPLATE, OUTPUT_DIR)
    write_scaffold_lock(new_hash)

    print(f"[OK] {spec_path.name}")
    print(f"[OK] {prd_path.name}")
    print(f"[OK] process_record/drafts/ 目录就绪")

    # ── v2.0 新增：衍生候选清单写入任务卡 ──
    print()
    print("更新任务卡候选清单段（v2.0 自动衍生）：")
    for mod in modules:
        task_card_path = REPO_ROOT / mod.get("task_card", "")
        if update_task_card_candidate_section(task_card_path, mod, modules):
            print(f"  [✎] {task_card_path.name}")

    # ── v2.0 新增：生成模块草稿骨架 ──
    print()
    print("生成模块草稿骨架（spec / prd）：")
    generate_module_drafts(modules, DRAFTS_DIR, force=force_rescaffold, prune_orphans=prune_orphans)

    # ── WE-H：生成 Foundation 范式骨架草稿（SSOT #41 per-archetype 单源）──
    foundation_sk = DRAFTS_DIR / FOUNDATION_SKELETON_DRAFT_NAME
    if foundation_sk.exists() and foundation_sk.stat().st_size > 100 and not force_rescaffold:
        print(f"  [skip] {foundation_sk.name}（已存在；--force-rescaffold 可覆盖）")
    else:
        foundation_sk.write_text(build_foundation_skeleton_draft(data), encoding="utf-8")
        print(f"  [+] {foundation_sk.name}")

    total_pages = sum(len(m["pages"]) for m in modules)
    total_states = sum(len(p["states"]) for m in modules for p in m["pages"])

    print()
    print(f"产品：{data['product']}   端口：{', '.join(data['platforms'])}")
    print(f"模块：{len(modules)} 个 / 页面：{total_pages} 个 / 状态帧：{total_states} 个")
    print()
    for mod in modules:
        deps = mod.get("depends_on", [])
        if deps:
            dep_str = "  依赖 " + ", ".join(f"{d['module']}({d['kind']})" for d in deps)
        else:
            dep_str = ""
        pages = mod["pages"]
        states = sum(len(p["states"]) for p in pages)
        cc = mod.get("candidate_components", {})
        cc_str = ""
        if cc:
            pub_n = len(cc.get("pub", []))
            gap_n = len(cc.get("proj_gaps", []))
            cc_str = f"  pub:{pub_n} / proj_gaps:{gap_n}"
        print(f"  {mod['id']} {mod['name']}  {len(pages)} 页 / {states} 帧{cc_str}{dep_str}")


if __name__ == "__main__":
    main()
