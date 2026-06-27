"""测试 S4-33 mermaid 语法校验（SSOT 双锚 #43）。

覆盖：
- _extract_mermaid_blocks：PRD <pre class="mermaid"> 优先 / spec ```mermaid 回退 /
  html.unescape（&gt; → > 等运行时一致）
- _find_mmdc：返回字符串或 None（环境相关，仅断言类型）
- check_mermaid_syntax：mmdc 缺失分支（monkeypatch _find_mmdc → None）WARN 跳过不阻断 /
  无块 OK / 合法块 OK（真实 mmdc，skipif）/ 语法错块 WARN（真实 mmdc，skipif）
"""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import precheck_stage4
from precheck_stage4 import (
    Report,
    _extract_mermaid_blocks,
    _find_mmdc,
    check_mermaid_syntax,
)

_MMDC = _find_mmdc()
_needs_mmdc = pytest.mark.skipif(_MMDC is None, reason="mmdc 未安装，跳过真实 parse 测试")


# ── _extract_mermaid_blocks ──────────────────────────────────────────────────


def test_extract_prd_pre_priority():
    """PRD <pre class="mermaid"> 块优先于 spec。"""
    prd = '<pre class="mermaid">\ngraph TD\n  A --> B\n</pre>'
    spec = "```mermaid\ngraph LR\n  X --> Y\n```"
    blocks = _extract_mermaid_blocks(spec, prd)
    assert len(blocks) == 1
    assert blocks[0][0] == "prd#1"
    assert "graph TD" in blocks[0][1]


def test_extract_spec_fence_fallback():
    """PRD 无 mermaid 块时回退提取 spec ```mermaid。"""
    prd = "<html><body>no mermaid here</body></html>"
    spec = "前言\n```mermaid\ngraph TD\n  A --> B\n```\n后文"
    blocks = _extract_mermaid_blocks(spec, prd)
    assert len(blocks) == 1
    assert blocks[0][0] == "spec#1"
    assert "graph TD" in blocks[0][1]


def test_extract_html_unescape():
    """PRD 块内容经 html.unescape（匹配 mermaid.js 运行时读 textContent）。"""
    prd = '<pre class="mermaid">\ngraph LR\n  A --&gt;|&quot;x&amp;y&quot;| B\n</pre>'
    blocks = _extract_mermaid_blocks("", prd)
    assert len(blocks) == 1
    content = blocks[0][1]
    assert "-->" in content
    assert '"x&y"' in content
    assert "&gt;" not in content and "&amp;" not in content


def test_extract_multiple_blocks():
    prd = (
        '<pre class="mermaid">\ngraph TD\n  A --> B\n</pre>'
        "<p>中间</p>"
        '<pre class="mermaid">\ngraph LR\n  X --> Y\n</pre>'
    )
    blocks = _extract_mermaid_blocks("", prd)
    assert [b[0] for b in blocks] == ["prd#1", "prd#2"]


def test_extract_none():
    blocks = _extract_mermaid_blocks("纯文本 spec", "<html>无 mermaid</html>")
    assert blocks == []


# ── _find_mmdc ───────────────────────────────────────────────────────────────


def test_find_mmdc_type():
    """探测返回 str（已装）或 None（未装），不抛异常。"""
    result = _find_mmdc()
    assert result is None or isinstance(result, str)


# ── check_mermaid_syntax：mmdc 缺失分支（确定性，monkeypatch）─────────────────


def test_mmdc_missing_warns_not_blocks(monkeypatch):
    """mmdc 未安装 → WARN 跳过，不进 errors（不阻断 exit code）。"""
    monkeypatch.setattr(precheck_stage4, "_find_mmdc", lambda: None)
    r = Report()
    prd = '<pre class="mermaid">\ngraph TD\n  A --> B\n</pre>'
    check_mermaid_syntax("", prd, r)
    assert len(r.errors) == 0
    assert len(r.warnings) == 1
    assert "mmdc 未安装" in r.warnings[0]


def test_no_blocks_ok(monkeypatch):
    """有 mmdc 但无 mermaid 块 → OK，不 WARN。"""
    monkeypatch.setattr(precheck_stage4, "_find_mmdc", lambda: "/fake/mmdc")
    r = Report()
    check_mermaid_syntax("纯文本", "<html>无 mermaid</html>", r)
    assert len(r.errors) == 0
    assert len(r.warnings) == 0
    assert r.passed == 1


# ── check_mermaid_syntax：真实 mmdc parse（skipif）────────────────────────────


@_needs_mmdc
def test_valid_mermaid_passes():
    r = Report()
    prd = '<pre class="mermaid">\ngraph TD\n  A[开始] --> B{判断}\n  B -->|是| C[执行]\n</pre>'
    check_mermaid_syntax("", prd, r)
    assert len(r.errors) == 0
    assert len(r.warnings) == 0
    assert r.passed == 1


@_needs_mmdc
def test_invalid_mermaid_warns():
    """语法错（未引号括号）→ WARN，不进 errors（WARN 阶段）。"""
    r = Report()
    prd = '<pre class="mermaid">\ngraph TD\n  A[坏 (括号)] --> B[end]\n</pre>'
    check_mermaid_syntax("", prd, r)
    assert len(r.errors) == 0
    assert len(r.warnings) == 1
    assert "语法错误" in r.warnings[0]
