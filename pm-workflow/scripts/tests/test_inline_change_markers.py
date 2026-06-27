"""测试 spec/prd 正文内联变更标记 诊断 + 清理（SSOT #79 / S4-68，议题 24）。

覆盖：
- strip_inline_change_markers.classify：schema 白名单 / 版本 tag / 纯 ref / 混合 / 来源豁免 / 正文
- strip_inline_change_markers.strip_text：Tier1 + Tier2a 删除无损 + schema/正文保留 + 悬挂分隔清理
- strip_inline_change_markers.scan：行号 + tier 标注
- precheck_stage4.check_no_inline_change_markers：净文本 OK / 含标记 WARN
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import strip_inline_change_markers as strip
import precheck_stage4
from precheck_stage4 import Report, check_no_inline_change_markers


# ── classify 分类 ───────────────────────────────────────────────────────────────
def test_classify_schema_whitelist():
    for lbl in ("触发态", "组件", "区域", "字段回显", "业务定位", "核心交互链路"):
        assert strip.classify(lbl, "bracket") == "schema"


def test_classify_source_prefix_exempt():
    # （来源：…）派生溯源标注（含版本号也合法）→ schema，非变更标记
    assert strip.classify("来源：§7", "paren") == "schema"
    assert strip.classify("来源：阶段 3 产品定义 v1.3 §7", "paren") == "schema"


def test_classify_version_tag():
    assert strip.classify("v3.0", "bracket") == "version"
    assert strip.classify("v4.0 新增", "bracket") == "version"
    assert strip.classify("v5.0 修订", "bracket") == "version"


def test_classify_pure_ref():
    # 剔除元数据 token 后残留为空 → 纯 traceability，可自动删
    assert strip.classify("CR-20260526-01 新增", "paren") == "pure_ref"
    assert strip.classify("v5.0 NB-252", "bracket") == "pure_ref"
    assert strip.classify("新增", "paren") == "pure_ref"


def test_classify_mixed():
    # 含内容残留 → 混合，PM 逐处审，禁自动删
    assert strip.classify("v3.0 M07 双时机入口", "bracket") == "mixed"
    assert strip.classify("CR-20260609-01 F-008 深化，引导问题配置", "paren") == "mixed"


def test_classify_content_no_signal():
    # 无追溯信号（新增/变更 作正文词，非 CR/NB/SSOT ref）→ 正文，不动
    assert strip.classify("无变更时禁用", "paren") == "content"
    assert strip.classify("卡片视图 ↔ 编辑表单视图 ↔ 新增表单子区", "paren") == "content"
    assert strip.classify("请调整过滤条件或检索关键词", "paren") == "content"


# ── 只读：工具不再提供 strip_text 自动删除（审计实证会损伤语义，2026-06-10 移除）──────
def test_no_auto_strip_api():
    # report-only：strip_text / --write 已移除，杜绝机械删除损伤语义
    assert not hasattr(strip, "strip_text")


# ── scan 行号 + tier ─────────────────────────────────────────────────────────────
def test_scan_lineno_and_tier():
    text = "第一行无标记\n【v4.0 新增】异步\n正文（无变更时禁用）保留\n"
    hits = strip.scan(text)
    assert len(hits) == 1
    assert hits[0]["line"] == 2 and hits[0]["tier"] == "version"


# ── precheck check ──────────────────────────────────────────────────────────────
def test_precheck_clean_text_ok():
    r = Report()
    check_no_inline_change_markers("纯净 spec 正文，无标记。", "<p>纯净 prd</p>", r)
    assert len(r.errors) == 0 and len(r.warnings) == 0


def test_precheck_flags_markers():
    spec = "状态【v4.0 新增】异步（CR-20260609-01 新增）说明。"
    r = Report()
    check_no_inline_change_markers(spec, "<p>干净</p>", r)
    assert len(r.warnings) >= 1


def test_precheck_schema_not_flagged():
    # schema 标记 + 来源标注 不应触发 WARN
    spec = "【触发态】默认 【组件】fb-card （来源：§7）字段。"
    r = Report()
    check_no_inline_change_markers(spec, "<p>干净</p>", r)
    assert len(r.warnings) == 0


# ── workflow 信号豁免（PM 自审 / 提交主管，非变更标记）─────────────────────────────
def test_submit_marker_exempt():
    # 【✅ PM 自审完成，提交主管审核】是 check_submit_marker 强制的 workflow 信号，
    # **不得**被内联变更标记 pattern 命中（否则与 check_submit_marker 冲突）
    sm = "【✅ PM 自审完成，提交主管审核】"
    assert len(strip.PRECHECK_BRACKET_RE.findall(sm)) == 0
    assert strip.classify(sm[1:-1], "bracket") == "content"


# ── 共享 helper warn_inline_markers（stage1/2/3/4 单源）──────────────────────────
def test_warn_inline_markers_clean():
    r = Report()
    n = strip.warn_inline_markers("需求分析", "纯净正文无标记。", r)
    assert n == 0 and len(r.warnings) == 0 and r.passed >= 1


def test_warn_inline_markers_dirty():
    r = Report()
    n = strip.warn_inline_markers("产品定义", "状态【v4.0 新增】（CR-20260609-01 新增）。", r)
    assert n == 2 and len(r.warnings) == 1


# ── stage1/2/3 precheck 集成 ────────────────────────────────────────────────────
def test_stage_prechecks_have_inline_marker_check():
    import precheck_stage1
    import precheck_stage2
    import precheck_stage3
    for mod, clean, dirty in (
        (precheck_stage1, "需求干净正文。", "需求【v4.0 新增】异步。"),
        (precheck_stage2, "功能干净正文。", "功能（CR-20260609-01 新增）。"),
        (precheck_stage3, "定义干净正文。", "定义【历史留痕 — 议题 9 已被 CR-20260609-01 覆盖】旧。"),
    ):
        assert hasattr(mod, "check_no_inline_change_markers")
        r_clean = mod.Report()
        mod.check_no_inline_change_markers(clean, r_clean)
        assert len(r_clean.warnings) == 0
        r_dirty = mod.Report()
        mod.check_no_inline_change_markers(dirty, r_dirty)
        assert len(r_dirty.warnings) >= 1
