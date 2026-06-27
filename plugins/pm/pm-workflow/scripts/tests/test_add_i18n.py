"""测试 pm-workflow/scripts/add_i18n.py 的 extract / inject 双模式。

覆盖范围（B+ 档位 11 测试）：
  extract: 叶子节点识别 / 祖先链过滤 / 去重 / 合并模式 / 跳过纯英文数字
  inject : 幂等 / fallback 同值 / HTML 实体保留 / byte-level 副作用 0
"""

from __future__ import annotations

import json

import add_i18n


# ── extract 部分 ──────────────────────────────────────────────────────────────


def test_extract_leaf_nodes_only():
    """叶子文本节点正确提取;含子 tag 的非叶子文本不被当作整体提取。"""
    html = """
    <div class="phone-frame">
      <span>确认报价</span>
      <div>取消<b>操作</b></div>
    </div>
    """
    cands = add_i18n.extract_candidates(html)
    # 叶子: "确认报价" / "取消" / "操作"; 非叶子的 div 不应作为单一 "取消操作" 提取
    assert "确认报价" in cands
    assert "取消" in cands
    assert "操作" in cands
    assert "取消操作" not in cands


def test_skip_interaction_card():
    """interaction-card 子树内文本被 skip。"""
    html = """
    <div class="phone-frame">
      <span>页面标题</span>
      <div class="interaction-card">
        <table><tr><td>这里是触点说明</td></tr></table>
      </div>
    </div>
    """
    cands = add_i18n.extract_candidates(html)
    assert "页面标题" in cands
    assert "这里是触点说明" not in cands


def test_skip_tp_marker():
    """tp-marker 内文本(通常是触点编号)被 skip。"""
    html = """
    <div class="phone-frame">
      <button>提交</button>
      <span class="tp-marker">触点 1</span>
    </div>
    """
    cands = add_i18n.extract_candidates(html)
    assert "提交" in cands
    assert "触点 1" not in cands


def test_skip_frame_platform_note():
    """frame-platform-note 内文本(端口说明)被 skip。"""
    html = """
    <div class="phone-frame">
      <span>首页</span>
    </div>
    <div class="frame-platform-note">本端口仅 iOS 支持手势返回</div>
    """
    cands = add_i18n.extract_candidates(html)
    assert "首页" in cands
    assert "本端口仅 iOS 支持手势返回" not in cands


def test_skip_pure_english_or_digit():
    """纯英文 / 纯数字 / 仅含标点的文本被 skip(不需翻译)。"""
    html = """
    <div class="phone-frame">
      <span>Submit</span>
      <span>2026-05-11</span>
      <span>... -- !!!</span>
      <span>已提交</span>
    </div>
    """
    cands = add_i18n.extract_candidates(html)
    assert "Submit" not in cands
    assert "2026-05-11" not in cands
    assert "... -- !!!" not in cands
    assert "已提交" in cands


def test_extract_dedup():
    """同一中文文本在多帧 / 同帧多处出现,只生成 1 条 dict entry。"""
    html = """
    <div class="phone-frame">
      <span>确认</span>
      <span>确认</span>
      <button>确认</button>
    </div>
    <div class="desktop-frame">
      <span>确认</span>
    </div>
    """
    cands = add_i18n.extract_candidates(html)
    # set 天然去重: "确认" 仅 1 个 entry
    assert "确认" in cands
    confirms = [c for c in cands if c == "确认"]
    assert len(confirms) == 1


def test_extract_merge_existing():
    """已有 dict 时,merge 模式保留旧翻译,仅追加新增 key。"""
    existing = {
        "_meta": {"generated_at": "2026-05-01T00:00:00Z"},
        "dict": {
            "确认": "Confirm",  # 已有翻译,必须保留
            "取消": "Cancel",
        },
    }
    new_keys = {"确认", "取消", "提交"}  # "提交" 是新增
    merged = add_i18n.merge_dict(existing, new_keys)
    assert merged["确认"] == "Confirm", "已有翻译被覆盖"
    assert merged["取消"] == "Cancel", "已有翻译被覆盖"
    assert merged["提交"] == "", "新增 key 应留空 value"
    assert len(merged) == 3


# ── inject 部分 ───────────────────────────────────────────────────────────────


def test_inject_idempotent():
    """重复 inject 不破坏已注入 attrs(不重复 data-zh 也不二次添加)。"""
    html = '<div class="phone-frame"><span>确认</span></div>\n'
    dict_data = {"确认": "Confirm"}
    new_html_1, n1, _ = add_i18n.inject_attributes(html, dict_data)
    assert n1 == 1
    assert 'data-zh="确认"' in new_html_1
    assert 'data-en="Confirm"' in new_html_1
    # 二次注入
    new_html_2, n2, _ = add_i18n.inject_attributes(new_html_1, dict_data)
    assert n2 == 0, f"幂等违反:二次注入新增 {n2} 属性"
    assert new_html_1 == new_html_2, "幂等违反:二次注入修改了 HTML"


def test_inject_fallback_same_value():
    """字典 value 留空时 data-en = data-zh(保留中文 fallback)。"""
    html = '<div class="phone-frame"><span>张三</span></div>\n'
    dict_data = {"张三": ""}  # 人名等示例数据保留中文
    new_html, n_inject, n_fallback = add_i18n.inject_attributes(html, dict_data)
    assert n_inject == 1
    assert n_fallback == 1
    assert 'data-zh="张三"' in new_html
    assert 'data-en="张三"' in new_html


def test_inject_html_entities():
    """文本含 &amp; 等已转义实体保留原样,不二次转义。"""
    html = '<div class="phone-frame"><span>确认&amp;取消</span></div>\n'
    dict_data = {"确认&amp;取消": "Confirm & Cancel"}
    new_html, n_inject, _ = add_i18n.inject_attributes(html, dict_data)
    assert n_inject == 1
    assert 'data-zh="确认&amp;取消"' in new_html, "&amp; 被二次转义"
    assert "<span data-zh=" not in new_html or 'data-zh="确认&amp;取消"' in new_html


def test_inject_no_beautifulsoup_side_effect():
    """注入前后 HTML byte-level 对比:仅多了 data-zh/data-en 属性,其他位置 0 差异。

    关键测试:验证 issue # 10/# 11/# 12 (BeautifulSoup 序列化导致 toast/modal/scroll
    bug) 不再复现 — regex 替换不动其他位置的 HTML 字节。
    """
    html = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head><style>\n"
        ".toast { animation: fadeIn 0.3s; }\n"
        ".modal { z-index: 9999; }\n"
        "</style></head>\n"
        "<body>\n"
        '<div class="phone-frame">\n'
        "  <span>确认</span>\n"
        "  <!-- 注释保留 -->\n"
        '  <button onclick="handleClick()">提交</button>\n'
        "</div>\n"
        "</body>\n"
        "</html>\n"
    )
    dict_data = {"确认": "Confirm", "提交": "Submit"}
    new_html, _, _ = add_i18n.inject_attributes(html, dict_data)

    # 移除注入的 data-zh / data-en 属性后,应与原文 byte-level 等价
    import re
    stripped = re.sub(r' data-zh="[^"]*"', "", new_html)
    stripped = re.sub(r' data-en="[^"]*"', "", stripped)
    assert stripped == html, (
        "注入引入了非属性的副作用 (序列化漂移)\n"
        f"原文:\n{html!r}\n注入并剥离后:\n{stripped!r}"
    )


# ── extract 集成: 全文件级 ───────────────────────────────────────────────────


def test_skip_data_zh_already_present():
    """已带 data-zh 的元素不被再次提取(幂等)。"""
    html = """
    <div class="phone-frame">
      <span data-zh="确认" data-en="Confirm">确认</span>
      <span>取消</span>
    </div>
    """
    cands = add_i18n.extract_candidates(html)
    assert "确认" not in cands, "已有 data-zh 的元素文本不应被提取"
    assert "取消" in cands


# ── inject 实战: end-to-end via tmp_path ────────────────────────────────────


def test_inject_end_to_end_via_tmp_drafts(tmp_path, monkeypatch):
    """用 tmp_path 模拟 drafts 目录,验证 cmd_inject 完整路径。"""
    drafts_dir = tmp_path / "process_record" / "drafts"
    drafts_dir.mkdir(parents=True)
    draft = drafts_dir / "prd_M01_draft.html"
    draft.write_text(
        '<div class="phone-frame"><span>确认</span></div>\n',
        encoding="utf-8",
    )

    dict_path = tmp_path / "process_record" / "i18n_dict.json"
    dict_path.parent.mkdir(parents=True, exist_ok=True)
    dict_path.write_text(
        json.dumps({
            "_meta": {"generated_at": "2026-05-11T00:00:00Z"},
            "dict": {"确认": "Confirm"},
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(add_i18n, "DRAFTS_DIR", drafts_dir)
    monkeypatch.setattr(add_i18n, "DICT_PATH", dict_path)

    rc = add_i18n.cmd_inject()
    assert rc == 0

    new_content = draft.read_text(encoding="utf-8")
    assert 'data-zh="确认"' in new_content
    assert 'data-en="Confirm"' in new_content
