"""防漏读元测试（SSOT #81）— 分节读取必读章节清单 ↔ 文档真实章节 双向守。

治「有必读文件清单、无必读章节清单 → 分节读取后章节漏读」根因（产品总监
2026-06-11 指出）。两个方向：

1. **漏读漂移**：3 个分节大文件的每个真实章节，必须被
   `agent_dispatch_protocol.md` 必读章节清单表的 ≥1 行（含豁免行）声明——
   文档新增章节但未入表 → FAIL（否则该章节永远没有任务读到）。
2. **悬空声明**：表里声明的章节标题必须在文档真实存在且唯一命中——
   章节改名/删除但表未同步 → FAIL（否则 fetch 运行期才报错）。

覆盖粒度：level-2 章节；配置了「子级覆盖父节」的（如 PM §四/§五 全阶段混装节）
要求其 level-3 子节逐个被声明。
"""

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import doc_query

REPO_ROOT = SCRIPTS_DIR.parent.parent
PROTOCOL = REPO_ROOT / "pm-workflow" / "rules" / "agent_dispatch_protocol.md"

# 分节体系纳管的文件 → 需子级覆盖的父节标题（全阶段混装节，level-2 自身覆盖不够）
MAPPED_FILES = {
    "pm-workflow/agents/AI产品经理_Agent.md": ["四、四阶段工作规范", "五、自审检查清单"],
    "pm-workflow/rules/rule_hard_constraints.md": [],
    "pm-workflow/agents/AI产品主管_Agent.md": ["四、分阶段审核规范"],
    # 阶段4 三杠杆 b（2026-06-11 产品总监立项）：两大阶段4规范入分节体系
    "pm-workflow/rules/prd_expression_standard.md": [],
    "pm-workflow/rules/proto_spec_md.md": [],
}

_ROW_RE = re.compile(r"^\|([^|]+)\|([^|]+)\|(.+)\|\s*$")


def _parse_section_map() -> dict:
    """解析 SECTION-MAP 表 → {file_rel: [claimed_title, ...]}（含豁免行）。"""
    text = PROTOCOL.read_text(encoding="utf-8")
    m = re.search(r"<!-- SECTION-MAP-START -->(.*?)<!-- SECTION-MAP-END -->",
                  text, re.DOTALL)
    assert m, "agent_dispatch_protocol.md 缺 SECTION-MAP-START/END 标记块"
    claims: dict = {}
    for line in m.group(1).splitlines():
        row = _ROW_RE.match(line.strip())
        if not row:
            continue
        task, file_rel, titles = (c.strip() for c in row.groups())
        if task in ("任务", "---") or file_rel.startswith("-"):
            continue
        for t in titles.split("；"):
            t = t.strip().rstrip("|").strip()
            if not t or t.startswith("（另加"):  # 动态补充说明，非标题
                continue
            claims.setdefault(file_rel, []).append(t)
    return claims


def _sections(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return doc_query.parse_sections(lines)


def _required_titles(heads, child_cover_parents):
    """要求覆盖的章节集 = 全部 level-2，配置的父节替换为其 level-3 子节。"""
    required = []
    for s in heads:
        if s.level != 2:
            continue
        parent_hit = next((p for p in child_cover_parents if p in s.title), None)
        if parent_hit:
            kids = [k for k in heads
                    if k.level == 3 and s.start < k.start and k.end <= s.end]
            required.extend(kids)
        else:
            required.append(s)
    return required


def test_every_section_claimed_no_omission():
    """方向 1：每个真实章节须被清单 ≥1 行声明（漏读漂移守）。"""
    claims = _parse_section_map()
    problems = []
    for file_rel, parents in MAPPED_FILES.items():
        claimed = claims.get(file_rel, [])
        assert claimed, f"清单表无 {file_rel} 的任何行"
        heads = _sections(REPO_ROOT / file_rel)
        for sec in _required_titles(heads, parents):
            if not any(c in sec.title for c in claimed):
                problems.append(f"{file_rel} :: [L{sec.start}] {sec.title}")
    assert not problems, (
        "以下章节未被必读章节清单任何行（含豁免行）声明 → 分节读取下将漏读：\n  "
        + "\n  ".join(problems)
        + "\n→ 在 agent_dispatch_protocol.md SECTION-MAP 表补行（或加入豁免行并注明理由）"
    )


def test_every_claim_resolves_uniquely():
    """方向 2：清单声明的标题须在文档唯一命中（悬空/歧义声明守）。"""
    claims = _parse_section_map()
    problems = []
    for file_rel, claimed in claims.items():
        path = REPO_ROOT / file_rel
        assert path.exists(), f"清单引用的文件不存在：{file_rel}"
        heads = _sections(path)
        for c in claimed:
            hits = [s for s in heads if c in s.title]
            if len(hits) == 0:
                problems.append(f"{file_rel} :: 悬空声明（文档无此标题）：{c}")
            elif len(hits) > 1 and not any(s.title == c for s in hits):
                problems.append(
                    f"{file_rel} :: 歧义声明（命中 {len(hits)} 节，fetch 会拒）：{c}")
    assert not problems, (
        "清单声明与文档真实标题脱节（改名/删除未同步表）：\n  "
        + "\n  ".join(problems)
    )


def test_mapped_files_config_in_sync_with_table():
    """配置与表一致：MAPPED_FILES 的每个文件在表中有行；表中文件都在配置里。"""
    claims = _parse_section_map()
    assert set(claims) == set(MAPPED_FILES), (
        f"表中文件 {set(claims)} ≠ 元测试 MAPPED_FILES 配置 {set(MAPPED_FILES)}"
        "——新增分节文件须两处同步"
    )
