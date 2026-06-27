"""测试 doc_query.py — 大文档目录 + 按需分节读取（SSOT #81）。

覆盖：ATX 解析跳过 code fence / 章节跨度含子节 / fetch 唯一子串 + 歧义 exit 2 /
预算闸超额拒输出 + 吐子目录 / locate 章节路径反查 / 重叠请求去重。
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import doc_query

SAMPLE = """# 总标题

序言。

## 一、角色

身份内容。

```bash
# 这行围栏内的井号不是标题
echo hi
```

## 二、规范

### 2.1 子节A

A 内容。

### 2.2 子节B

B 内容。

## 三、规范补充

补充内容。
"""


def _write(tmp_path, text=SAMPLE):
    p = tmp_path / "doc.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_parse_skips_fence_and_spans_include_children(tmp_path):
    p = _write(tmp_path)
    heads = doc_query.parse_sections(p.read_text(encoding="utf-8").splitlines())
    titles = [h.title for h in heads]
    assert "这行围栏内的井号不是标题" not in " ".join(titles)
    sec2 = next(h for h in heads if h.title == "二、规范")
    sub_a = next(h for h in heads if h.title == "2.1 子节A")
    assert sec2.start < sub_a.start <= sec2.end  # 跨度含子节


def test_outline_and_fetch_unique_substring(tmp_path, capsys):
    p = _write(tmp_path)
    assert doc_query.main(["outline", str(p)]) == 0
    out = capsys.readouterr().out
    assert "一、角色" in out and "tok)" in out

    assert doc_query.main(["fetch", str(p), "子节A"]) == 0
    out = capsys.readouterr().out
    assert "A 内容" in out and "B 内容" not in out


def test_fetch_ambiguous_and_missing_exit2(tmp_path, capsys):
    p = _write(tmp_path)
    assert doc_query.main(["fetch", str(p), "规范"]) == 2  # 命中 二/2.x/三 歧义
    err = capsys.readouterr().err
    assert "歧义" in err
    assert doc_query.main(["fetch", str(p), "不存在的标题"]) == 2


def test_fetch_budget_gate_refuses_and_prints_suboutline(tmp_path, capsys):
    p = _write(tmp_path)
    rc = doc_query.main(["fetch", str(p), "二、规范", "--max-tokens", "1"])
    captured = capsys.readouterr()
    assert rc == 2
    assert "BUDGET" in captured.err and "子节A" in captured.err  # 吐子目录引导收窄
    assert "A 内容" not in captured.out  # 拒绝输出正文


def test_fetch_overlap_dedup(tmp_path, capsys):
    p = _write(tmp_path)
    assert doc_query.main(["fetch", str(p), "二、规范", "子节A"]) == 0
    out = capsys.readouterr().out
    assert out.count("A 内容") == 1  # 子节被父节包含,不双倍输出


def test_locate_breadcrumb(tmp_path, capsys):
    p = _write(tmp_path)
    assert doc_query.main(["locate", str(p), "B 内容"]) == 0
    out = capsys.readouterr().out
    assert "二、规范 > 2.2 子节B" in out


SAMPLE_PRD = """<html><body>
<!-- [FRAME-START: H-M01-P01-default | from=prd_M01_draft.html | sha256:abc] -->
<section id="H-M01-P01-default">默认帧内容</section>
<!-- [FRAME-END: H-M01-P01-default] -->
<!-- [FRAME-START: H-M01-P01-error] -->
<section id="H-M01-P01-error">异常帧内容</section>
<!-- [FRAME-END: H-M01-P01-error] -->
</body></html>
"""


def _write_prd(tmp_path):
    p = tmp_path / "prd.html"
    p.write_text(SAMPLE_PRD, encoding="utf-8")
    return p


def test_frames_lists_blocks(tmp_path, capsys):
    p = _write_prd(tmp_path)
    assert doc_query.main(["frames", str(p)]) == 0
    out = capsys.readouterr().out
    assert "2 帧" in out and "H-M01-P01-default" in out and "H-M01-P01-error" in out


def test_fetch_frame_unique_and_ambiguous(tmp_path, capsys):
    p = _write_prd(tmp_path)
    assert doc_query.main(["fetch-frame", str(p), "H-M01-P01-error"]) == 0
    out = capsys.readouterr().out
    assert "异常帧内容" in out and "默认帧内容" not in out
    # "H-M01-P01" 命中 2 帧 → 歧义 exit 2
    assert doc_query.main(["fetch-frame", str(p), "H-M01-P01"]) == 2


def test_fetch_same_title_twice_outputs_once(tmp_path, capsys):
    p = _write(tmp_path)
    assert doc_query.main(["fetch", str(p), "子节A", "子节A"]) == 0
    out = capsys.readouterr().out
    assert out.count("A 内容") == 1  # 审计 hot-fix：同标题重复传参不双倍输出


def test_frames_orphan_start_warns(tmp_path, capsys):
    p = tmp_path / "prd.html"
    p.write_text(SAMPLE_PRD.replace("<!-- [FRAME-END: H-M01-P01-error] -->", ""),
                 encoding="utf-8")
    assert doc_query.main(["frames", str(p)]) == 0
    captured = capsys.readouterr()
    assert "H-M01-P01-default" in captured.out          # 配对帧正常列出
    assert "H-M01-P01-error" not in captured.out        # 孤儿不入清单
    assert "无配对 FRAME-END" in captured.err and "H-M01-P01-error" in captured.err  # 但必告警


def test_fetch_frame_budget_gate(tmp_path, capsys):
    p = _write_prd(tmp_path)
    rc = doc_query.main(["fetch-frame", str(p), "H-M01-P01-default",
                         "H-M01-P01-error", "--max-tokens", "1"])
    captured = capsys.readouterr()
    assert rc == 2 and "BUDGET" in captured.err
    assert "默认帧内容" not in captured.out
