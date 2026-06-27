"""test_migrate_l1_ssot_67_68_69.py — L1 整改 migrate 脚本单元测试

覆盖：
- B2-1 段头骨架插入：基本插入 / idempotent / 锚点不存在边界
- B2-2 主页面字段派生：单页自动 / 多页占位 / 无涉及页面占位 / idempotent
- B2-3 PM 整改提示书生成：parse precheck 输出 / 文件生成
- 边界：无 F-xxx / 无 S2.MXX 模块 / spec 文件不存在
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import migrate_l1_ssot_67_68_69 as mig


# ── B2-1 段头骨架插入 ────────────────────────────────────────────────────


def _basic_module_spec(mid: str = "M01") -> str:
    """构造含 .1~.7 标准章节的 spec 片段。"""
    return (
        f"## S2.{mid} 模块概述\n\n"
        "业务定位...\n\n"
        f"## S2.{mid}.1 页面概述\n\n"
        "P-01 列表页...\n\n"
        f"## S2.{mid}.2 状态枚举\n\n"
        "表格...\n\n"
        f"## S2.{mid}.3 触点表\n\n"
        "表格...\n\n"
        f"## S2.{mid}.4 数据字段绑定\n\n"
        "字段表...\n\n"
        f"## S2.{mid}.5 跨模块跳转引用\n\n"
        "跳转列表...\n\n"
        f"## S2.{mid}.6 API 摘要\n\n"
        "API 列表...\n\n"
        f"## S2.{mid}.7 状态清单与验收标准\n\n"
        "Gherkin...\n"
    )


def test_b2_1_basic_insertion():
    """B2-1 基本：在 .5 前插 .4B；在 .6 前插 .5B。"""
    spec = _basic_module_spec("M01")
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_1(spec, r)
    assert "## S2.M01.4B 业务规则" in new_spec
    assert "## S2.M01.5B 数据规模" in new_spec
    # .4B 必在 .5 之前
    assert new_spec.index("## S2.M01.4B") < new_spec.index("## S2.M01.5 ")
    # .5B 必在 .6 之前
    assert new_spec.index("## S2.M01.5B") < new_spec.index("## S2.M01.6 ")
    # 含占位
    assert "[待 PM 补全]" in new_spec
    assert "插入 .4B 1 个 / .5B 1 个" in r.summary


def test_b2_1_idempotent():
    """B2-1 idempotent：重跑不重复插入。"""
    spec = _basic_module_spec("M01")
    r1 = mig.TaskResult("first")
    after_first = mig.task_b2_1(spec, r1)
    r2 = mig.TaskResult("second")
    after_second = mig.task_b2_1(after_first, r2)
    assert after_first == after_second
    # 第二次应全跳过：插入 0 个
    assert "插入 .4B 0 个" in r2.summary
    assert ".5B 0 个" in r2.summary
    assert "已存在 .4B 1 个" in r2.summary
    # .4B/.5B 各只出现一次（作为段头）
    assert after_second.count("## S2.M01.4B 业务规则") == 1
    assert after_second.count("## S2.M01.5B 数据规模") == 1


def test_b2_1_idempotent_partial():
    """B2-1 部分 idempotent：已有 .4B 但缺 .5B → 仅插 .5B。"""
    spec = _basic_module_spec("M01")
    spec = spec.replace(
        "## S2.M01.5 跨模块跳转引用",
        "## S2.M01.4B 业务规则\n\nPM 已填的业务规则\n\n## S2.M01.5 跨模块跳转引用",
    )
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_1(spec, r)
    assert "PM 已填的业务规则" in new_spec  # 原内容保留
    assert "## S2.M01.5B 数据规模" in new_spec  # .5B 新插入
    assert new_spec.count("## S2.M01.4B 业务规则") == 1


def test_b2_1_multi_module():
    """B2-1 多模块：每个模块都插入 .4B + .5B。"""
    spec = _basic_module_spec("M01") + "\n" + _basic_module_spec("M02")
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_1(spec, r)
    assert "## S2.M01.4B 业务规则" in new_spec
    assert "## S2.M02.4B 业务规则" in new_spec
    assert "## S2.M01.5B 数据规模" in new_spec
    assert "## S2.M02.5B 数据规模" in new_spec
    assert "插入 .4B 2 个 / .5B 2 个" in r.summary


def test_b2_1_no_modules():
    """B2-1 无 S2.MXX 模块：旧版 spec 跳过。"""
    spec = "# spec\n\n## 区块 0\n\n旧版内容\n"
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_1(spec, r)
    assert new_spec == spec
    assert "无 S2.MXX 模块段头" in r.summary


def test_b2_1_missing_anchor_falls_back():
    """B2-1 锚点缺失（无 .5/.6）→ 用后继段（next module）作为锚点。"""
    spec = (
        "## S2.M01 模块概述\n\n概述...\n\n"
        "## S2.M01.1 页面概述\n\n页面...\n\n"
        "## S2.M01.4 数据字段绑定\n\n字段...\n\n"
        "## S2.M02 模块概述\n\n概述...\n"
    )
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_1(spec, r)
    # .4B 应插在 .5 之前；.5 不存在 → 跳到 .6 / 下一模块
    # 接受任意一种插入策略：在 M02 之前
    assert "## S2.M01.4B 业务规则" in new_spec or "## S2.M01.5B 数据规模" in new_spec


# ── B2-2 F-xxx 主页面字段派生 ────────────────────────────────────────────


def _f_section(fid_num: str, content: str) -> str:
    return f"#### F-{fid_num}：测试功能 {fid_num}\n{content}\n"


def test_b2_2_single_page_auto_derive():
    """B2-2 单页 F → 自动派生主页面 = 该页。"""
    spec = _f_section(
        "001",
        "- **优先级**：P0　｜　**涉及页面**：P-002 项目创建表单",
    )
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_2(spec, r)
    assert "**主页面**：P-002" in new_spec
    assert "自动派生单页主页面 1 个" in r.summary


def test_b2_2_multi_page_placeholder():
    """B2-2 多页 F → 占位含候选列表。"""
    spec = _f_section(
        "002",
        "- **涉及页面**：P-002 详情页 / P-001 列表页",
    )
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_2(spec, r)
    assert "[待 PM 选" in new_spec
    assert "P-002" in new_spec and "P-001" in new_spec
    assert "多页占位 1 个" in r.summary


def test_b2_2_no_involved_placeholder():
    """B2-2 完全无涉及页面 → 占位「待 PM 补涉及页面后选」。"""
    spec = _f_section(
        "003",
        "- **业务规则**：随意",
    )
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_2(spec, r)
    assert "[待 PM 补涉及页面后选]" in new_spec
    assert "无涉及页面占位 1 个" in r.summary


def test_b2_2_existing_main_page_skipped():
    """B2-2 已有「主页面」字段 → 跳过（idempotent）。"""
    spec = _f_section(
        "004",
        "- **涉及页面**：P-001 / P-002\n- **主页面**：P-001",
    )
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_2(spec, r)
    assert new_spec.count("**主页面**：") == 1
    assert "已存在跳过 1 个" in r.summary


def test_b2_2_idempotent_full_rerun():
    """B2-2 整体 idempotent：跑两次结果一致。"""
    spec = (
        _f_section("001", "- **涉及页面**：P-002")
        + _f_section("002", "- **涉及页面**：P-001 / P-003")
        + _f_section("003", "- **业务规则**：x")
    )
    r1 = mig.TaskResult("first")
    after_first = mig.task_b2_2(spec, r1)
    r2 = mig.TaskResult("second")
    after_second = mig.task_b2_2(after_first, r2)
    assert after_first == after_second
    # 二次跑全跳过
    assert "已存在跳过 3 个" in r2.summary


def test_b2_2_no_f_sections():
    """B2-2 无 F-xxx：旧版 spec 跳过。"""
    spec = "# spec\n\n## 区块 0\n\n无 F-xxx 内容\n"
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_2(spec, r)
    assert new_spec == spec
    assert "无 F-xxx 节" in r.summary


def test_b2_2_mixed_three_branches():
    """B2-2 综合：单页 / 多页 / 无涉及 + 已有主页面 → 4 分支正确。"""
    spec = (
        _f_section("001", "- **涉及页面**：P-002")
        + _f_section("002", "- **涉及页面**：P-001 / P-003")
        + _f_section("003", "- **业务规则**：x")
        + _f_section("004", "- **涉及页面**：P-005\n- **主页面**：P-005")
    )
    r = mig.TaskResult("test")
    new_spec = mig.task_b2_2(spec, r)
    assert "自动派生单页主页面 1 个" in r.summary
    assert "多页占位 1 个" in r.summary
    assert "无涉及页面占位 1 个" in r.summary
    assert "已存在跳过 1 个" in r.summary
    # 主页面字段总数 == 4
    assert new_spec.count("**主页面**：") == 4


# ── B2-3 PM 整改提示书 ───────────────────────────────────────────────────


def test_b2_3_parse_precheck_sections():
    """B2-3 parse precheck output → 12 个 SSOT 规则分组。"""
    sample_output = (
        "SSOT #68 / S4-49 spec §S2.MXX.4B 业务规则段头（WARN）\n"
        "  [WARN] spec.md 2/3 个模块缺 .4B 业务规则段头：M01, M02\n"
        "SSOT #68 / S4-50 spec §S2.MXX.5B 数据规模段头（WARN）\n"
        "  [WARN] spec.md 3/3 个模块缺 .5B 数据规模段头\n"
        "SSOT #68 / S4-51 spec F-xxx 主页面字段（WARN）\n"
        "  [OK] spec.md 5 个 F-xxx 节主页面字段齐全 + ∈ 涉及页面\n"
    )
    parsed = mig._parse_precheck_sections(sample_output)
    assert "S4-49" in parsed
    assert parsed["S4-49"]["warn_count"] == 1
    assert parsed["S4-50"]["warn_count"] == 1
    assert parsed["S4-51"]["warn_count"] == 0


def test_b2_3_writes_issue_file(tmp_path: Path, monkeypatch):
    """B2-3 生成 PM 整改提示书文件到 process_record/issues/。"""
    # 构造伪仓
    root = tmp_path / "repo"
    (root / "outputs").mkdir(parents=True)
    (root / "process_record" / "issues").mkdir(parents=True)
    spec_file = root / "outputs" / "spec_测试产品_latest.md"
    spec_file.write_text(_basic_module_spec(), encoding="utf-8")

    # 伪造 _run_precheck
    def fake_run_precheck(_root):
        return "无任何 SSOT 节标题，全部 PASS", 0

    monkeypatch.setattr(mig, "_run_precheck", fake_run_precheck)

    r = mig.TaskResult("test")
    payload = mig.task_b2_3(root, "测试产品", r)
    assert payload is not None
    out_path, content = payload
    assert out_path.parent == root / "process_record" / "issues"
    assert "PM_整改_测试产品_SSOT_67_68_69_" in out_path.name
    assert out_path.suffix == ".md"
    # 12 节标题都应出现在 content（PASS 也写）
    for rid, _title in mig.SSOT_676869_SECTIONS:
        assert rid in content


def test_b2_3_remediation_examples_all_present():
    """B2-3 12 个规则均有整改示例（非空）。"""
    for rid, _title in mig.SSOT_676869_SECTIONS:
        ex = mig._remediation_example(rid)
        assert ex, f"{rid} 缺整改示例"
        assert "整改示例" in ex


# ── 工具函数边界 ──────────────────────────────────────────────────────────


def test_extract_pages_dedup_preserve_order():
    """_extract_pages_from_involved：保序去重。"""
    pages = mig._extract_pages_from_involved("P-002 详情 / P-001 列表 / P-002 again")
    assert pages == ["P-002", "P-001"]


def test_extract_pages_empty():
    """_extract_pages_from_involved：无 P-XX 返回空 list。"""
    assert mig._extract_pages_from_involved("纯文本无 ID") == []


def test_find_product_name_from_spec_path(tmp_path: Path):
    """find_product_name 解析正确。"""
    spec = tmp_path / "spec_报价工具_latest.md"
    spec.write_text("", encoding="utf-8")
    assert mig.find_product_name(spec) == "报价工具"


def test_find_spec_md_missing_returns_none(tmp_path: Path):
    """find_spec_md 在 outputs 不存在时返回 None。"""
    assert mig.find_spec_md(tmp_path) is None
