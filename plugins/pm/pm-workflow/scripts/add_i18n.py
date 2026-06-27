#!/usr/bin/env python3
"""
add_i18n.py — 阶段四 prd 草稿 i18n 工具化（B+ 档位）

触发条件（prd_expression_standard.md §十）：
    产品定义明确要求多语言支持（中/英文切换）时,PM 在写完 8 份
    prd_M0X_draft.html 后跑本脚本注入 data-zh / data-en 双语属性。
    主模板侧栏底部 lang-switcher 调 setLang(lang) 切换 textContent。

用法：
    python pm-workflow/scripts/add_i18n.py --extract
        扫描 process_record/drafts/prd_M*_draft.html → 输出
        process_record/i18n_dict.json 骨架(中文 key + 英译留空)。
        已存在字典时 merge: 保留旧翻译,仅追加新增 key。

    python pm-workflow/scripts/add_i18n.py --inject
        读 process_record/i18n_dict.json → regex 注入 data-zh / data-en 到
        drafts。字典 value 留空时 data-en = data-zh (保留中文 fallback)。
        幂等: 重复跑不破坏已注入属性。

设计约束（避免历史踩坑）：
    - 不用 BeautifulSoup (issue # 10/# 11/# 12 toast/modal/scroll 序列化副作用根因)
    - 注入采用 regex 字符串替换,保留 HTML 字节级结构 (仅追加属性)
    - extract 用 HTMLParser 做祖先链检测 + leaf 文本节点识别
    - extract 跳过 interaction-card / tp-marker / frame-platform-note 子树
    - inject 不做祖先过滤 (信任 dict 已被 extract 过滤,B+ 档位简化)

幂等：
    - extract 已存在的 i18n_dict.json 仅追加新 key
    - inject 已注入 data-zh 的元素 skip (regex 匹配时检测 attrs)
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

# ── 路径约定 ──────────────────────────────────────────────────────────────────
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_paths import FRAMEWORK_ROOT, PROJECT_ROOT
DRAFTS_DIR = PROJECT_ROOT / "process_record" / "drafts"
DICT_PATH = PROJECT_ROOT / "process_record" / "i18n_dict.json"
DRAFTS_GLOB = "prd_M*_draft.html"

# ── extract: 容器 / 跳过 class ────────────────────────────────────────────────
CONTAINER_CLASSES = {"phone-frame", "desktop-frame", "h5-frame"}
SKIP_CLASSES = {"interaction-card", "tp-marker", "frame-platform-note"}

# ── inject: 允许注入的 leaf-style 标签 (避免误伤 script/style/svg 等) ──────────
SAFE_TAGS = (
    "span", "div", "button", "p", "a", "li", "td", "th",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "label", "strong", "em", "b", "i",
)

# 中文字符检测 (CJK 统一汉字基本区,涵盖 99% 业务文本)
CN_CHAR_RE = re.compile(r"[一-鿿]")

# ── PROTECTED_ATTRS 守护清单(建议 3 / issue # 10 / # 11 复盘根因 B 兜底)─────────
#
# 即使本脚本通过 regex 字符串替换(非 BeautifulSoup)架构层面规避了"序列化丢属性"风险,
# 仍要求 inject 前后这些条件渲染属性的总命中数严格相等,作为机械兜底:
# - display:none / display:block / display:flex inline style:控制元素可见性
# - data-frame-state:控制状态帧条件渲染
# - aria-modal / aria-hidden / role:无障碍 + ARIA 状态
# - hidden 属性:HTML 5 内置隐藏标记
#
# 若 inject 前后 count 不一致 → 立即 FAIL,提示后处理脚本破坏了条件渲染属性
PROTECTED_ATTR_PATTERNS = [
    r'style="[^"]*display:\s*none',
    r'style="[^"]*display:\s*block',
    r'style="[^"]*display:\s*flex',
    r'style="[^"]*visibility:\s*hidden',
    r'data-frame-state=',
    r'aria-modal=',
    r'aria-hidden=',
    r'role="dialog"',
    r'role="alertdialog"',
    r'\shidden(\s|>)',
]


def count_protected_attrs(html: str) -> dict[str, int]:
    """统计条件渲染属性出现次数,返回 {pattern: count} dict。"""
    return {p: len(re.findall(p, html)) for p in PROTECTED_ATTR_PATTERNS}


def assert_protected_attrs_intact(
    before: str, after: str, label: str
) -> None:
    """inject 前后对比 PROTECTED_ATTRS 数量,不一致则 raise(让 caller 决定 exit code)。"""
    before_counts = count_protected_attrs(before)
    after_counts = count_protected_attrs(after)
    drifts = []
    for p, before_n in before_counts.items():
        after_n = after_counts[p]
        if after_n != before_n:
            drifts.append(f"  - 模式 `{p}`: {before_n} → {after_n}")
    if drifts:
        msg = (
            f"[FAIL][{label}] PROTECTED_ATTRS 数量在 inject 前后不一致(建议 3 / "
            f"issue # 10 / # 11 复盘根因 B 兜底):\n" + "\n".join(drifts) +
            f"\n后处理脚本破坏了条件渲染属性 → toast / modal / 默认状态会全局常驻显示。"
        )
        raise RuntimeError(msg)


# ── extract 部分 ──────────────────────────────────────────────────────────────

class ChineseLeafExtractor(HTMLParser):
    """扫 HTML 收集"叶子中文文本节点",按祖先链 + class 过滤。

    叶子节点判定: handle_data 每次调用对应一段相邻文本数据;若文本两侧紧贴
    起止 tag 而中间无嵌套 tag,即是叶子节点。HTMLParser 天然按此节奏切分,
    无需额外判定。

    祖先链过滤:
      - 必须在 CONTAINER_CLASSES (phone-frame / desktop-frame / h5-frame) 内
      - 任一祖先含 SKIP_CLASSES (interaction-card / tp-marker / frame-platform-note) 即跳过
      - 直接父或任一祖先已有 data-zh 即跳过 (幂等)
    """

    def __init__(self) -> None:
        # convert_charrefs=False: 保留 &amp; / &quot; 等实体原样
        # 与 prd_expression_standard.md §十 spec 一致 (HTML 实体不二次转义)
        super().__init__(convert_charrefs=False)
        self.in_container = 0  # 容器嵌套计数
        self.skip_subtree = 0  # 跳过子树嵌套计数
        self.has_data_zh = 0  # 祖先含 data-zh 嵌套计数
        self.candidates: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs_dict = dict(attrs)
        classes = set((attrs_dict.get("class") or "").split())
        if classes & CONTAINER_CLASSES:
            self.in_container += 1
        if classes & SKIP_CLASSES:
            self.skip_subtree += 1
        if "data-zh" in attrs_dict:
            self.has_data_zh += 1
        # 用栈记录每层的标记,endtag 时正确弹出
        self._stack.append((classes & CONTAINER_CLASSES,
                            classes & SKIP_CLASSES,
                            "data-zh" in attrs_dict))

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        # 自闭合标签 (<br/> / <img/>) 不进栈,不影响计数
        pass

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            return
        c_marks, s_marks, dz_mark = self._stack.pop()
        if c_marks:
            self.in_container -= 1
        if s_marks:
            self.skip_subtree -= 1
        if dz_mark:
            self.has_data_zh -= 1

    def handle_data(self, data: str) -> None:
        if self.in_container == 0:
            return
        if self.skip_subtree > 0:
            return
        if self.has_data_zh > 0:
            return
        text = data.strip()
        if not text:
            return
        # 跳过纯英文 / 纯数字 / 仅含标点 — 必须含至少一个中文字符
        if not CN_CHAR_RE.search(text):
            return
        self.candidates.add(text)

    def reset(self) -> None:
        super().reset()
        self._stack: list[tuple[set, set, bool]] = []
        self.in_container = 0
        self.skip_subtree = 0
        self.has_data_zh = 0
        # 注意: self.candidates 不在 reset 中清空,允许跨文件累积。
        # 每个 extractor 实例独立,不复用。


def extract_candidates(html: str) -> set[str]:
    """从单份 HTML 中提取候选中文文本节点 (含祖先链过滤)。"""
    extractor = ChineseLeafExtractor()
    extractor.feed(html)
    return extractor.candidates


def merge_dict(existing: dict, new_keys: set[str]) -> dict:
    """合并: 保留 existing 中已有翻译,仅追加 new_keys 中尚未在 dict 中的 key (value 留空)。
    返回 (新 dict, 新增 key 数, 保留 key 数)。"""
    if not existing:
        existing = {}
    dict_section = existing.get("dict", {}) if isinstance(existing.get("dict"), dict) else {}
    for key in new_keys:
        if key not in dict_section:
            dict_section[key] = ""
    return dict_section


def cmd_extract() -> int:
    """extract 模式入口: 扫描 drafts → 写 i18n_dict.json (merge 模式)。"""
    if not DRAFTS_DIR.exists():
        print(f"[ERROR] drafts 目录不存在: {DRAFTS_DIR}", file=sys.stderr)
        return 1

    drafts = sorted(DRAFTS_DIR.glob(DRAFTS_GLOB))
    if not drafts:
        print(f"[ERROR] {DRAFTS_DIR} 下未发现 {DRAFTS_GLOB} 草稿", file=sys.stderr)
        return 1

    all_candidates: set[str] = set()
    for draft in drafts:
        html = draft.read_text(encoding="utf-8")
        cands = extract_candidates(html)
        print(f"  [+] {draft.name} — {len(cands)} 候选中文文本")
        all_candidates |= cands

    # 加载既有 dict (merge 模式)
    existing: dict = {}
    if DICT_PATH.exists():
        try:
            existing = json.loads(DICT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"[ERROR] 既有 i18n_dict.json 解析失败: {e}", file=sys.stderr)
            return 1

    old_dict_section = existing.get("dict", {}) if isinstance(existing.get("dict"), dict) else {}
    old_count = len(old_dict_section)
    merged_dict = merge_dict(existing, all_candidates)
    added = sorted(set(merged_dict.keys()) - set(old_dict_section.keys()))

    output = {
        "_meta": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_files": [d.name for d in drafts],
            "total_unique": len(merged_dict),
            "added_this_run": len(added),
            "preserved_translations": sum(1 for k, v in merged_dict.items() if v),
        },
        "dict": merged_dict,
    }

    DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DICT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print()
    print(f"[OK] 字典已写入: {DICT_PATH}")
    print(f"     扫描 {len(drafts)} 个草稿 / 累计 {len(all_candidates)} unique 中文文本")
    print(f"     旧 dict {old_count} key → 新 dict {len(merged_dict)} key (新增 {len(added)} 项)")
    if added:
        print("     新增 key 预览 (前 10 条):")
        for k in added[:10]:
            print(f"       · {k}")
    print()
    print("[NEXT] PM 维护字典 value 填英译 (留空 = 保留中文作 data-en),再跑 --inject。")
    return 0


# ── inject 部分 ───────────────────────────────────────────────────────────────

def _escape_attr(text: str) -> str:
    """转义属性值中的双引号: " → &quot;。其他特殊字符按 spec 原样保留 (含 &amp; 等)。"""
    return text.replace('"', "&quot;")


def inject_attributes(html: str, dict_data: dict) -> tuple[str, int, int]:
    """对单份 HTML 注入 data-zh / data-en 属性。

    实现:
      - 用 regex 匹配 <SAFE_TAG attrs>cn_text</SAFE_TAG> 模式
      - attrs 含 'data-zh=' 则 skip (幂等)
      - 字典 value 为空 → data-en = data-zh (fallback 同值)
      - cn_text / en_text 中的 " 转义为 &quot; 写入属性值

    返回 (新 html, 注入属性数, fallback 同值数)。
    """
    inject_count = 0
    fallback_count = 0
    safe_tags_alt = "|".join(SAFE_TAGS)

    for cn_text, en_text in dict_data.items():
        if not cn_text or not isinstance(cn_text, str):
            continue
        cn_text_stripped = cn_text.strip()
        if not cn_text_stripped:
            continue
        if not CN_CHAR_RE.search(cn_text_stripped):
            continue  # value-side: dict 可能含非法 key,防御性跳过

        is_fallback = not en_text  # value 空/None/空串
        en_text_inject = cn_text if is_fallback else en_text

        cn_escaped = re.escape(cn_text)
        # 匹配 <TAG ATTRS>cn_text</TAG>; ATTRS 不含 >; 标签必须配对
        pattern = re.compile(
            rf'<({safe_tags_alt})([^>]*)>{cn_escaped}</\1>',
            re.IGNORECASE,
        )

        per_key_injected = 0
        per_key_fallback = 0

        def replace_one(m: re.Match) -> str:
            nonlocal per_key_injected, per_key_fallback
            tag = m.group(1)
            attrs = m.group(2)
            # 幂等: 已注入 data-zh 不重复
            if "data-zh=" in attrs:
                return m.group(0)
            per_key_injected += 1
            if is_fallback:
                per_key_fallback += 1
            zh_attr = _escape_attr(cn_text)
            en_attr = _escape_attr(en_text_inject)
            return f'<{tag}{attrs} data-zh="{zh_attr}" data-en="{en_attr}">{cn_text}</{tag}>'

        html = pattern.sub(replace_one, html)
        inject_count += per_key_injected
        fallback_count += per_key_fallback

    return html, inject_count, fallback_count


def cmd_inject() -> int:
    """inject 模式入口: 读字典 → 注入 drafts → 覆盖写回。"""
    if not DICT_PATH.exists():
        print(
            f"[ERROR] i18n 字典不存在: {DICT_PATH}\n"
            f"  请先跑 `python pm-workflow/scripts/add_i18n.py --extract` 生成骨架,"
            f"维护英译后再跑 --inject。",
            file=sys.stderr,
        )
        return 1

    try:
        loaded = json.loads(DICT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[ERROR] i18n_dict.json 解析失败: {e}", file=sys.stderr)
        return 1

    dict_section = loaded.get("dict", {}) if isinstance(loaded.get("dict"), dict) else {}
    if not dict_section:
        print(f"[ERROR] i18n_dict.json 的 `dict` 段为空,无可注入 key", file=sys.stderr)
        return 1

    if not DRAFTS_DIR.exists():
        print(f"[ERROR] drafts 目录不存在: {DRAFTS_DIR}", file=sys.stderr)
        return 1

    drafts = sorted(DRAFTS_DIR.glob(DRAFTS_GLOB))
    if not drafts:
        print(f"[ERROR] {DRAFTS_DIR} 下未发现 {DRAFTS_GLOB} 草稿", file=sys.stderr)
        return 1

    total_files_changed = 0
    total_inject = 0
    total_fallback = 0

    for draft in drafts:
        original = draft.read_text(encoding="utf-8")
        new_html, n_inject, n_fallback = inject_attributes(original, dict_section)
        if new_html == original:
            print(f"  [=] {draft.name} — 0 新增 (已幂等)")
            continue
        # 建议 3 兜底:inject 前后对比 PROTECTED_ATTRS 数量,不一致则 FAIL(不写回)
        try:
            assert_protected_attrs_intact(original, new_html, draft.name)
        except RuntimeError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            print(
                f"[ABORT] {draft.name} 未写回,inject 失败 — 排查 inject_attributes "
                f"regex 是否误吞条件渲染属性",
                file=sys.stderr,
            )
            return 1
        draft.write_text(new_html, encoding="utf-8")
        total_files_changed += 1
        total_inject += n_inject
        total_fallback += n_fallback
        fb_hint = f"(fallback 同值 {n_fallback})" if n_fallback else ""
        print(f"  [+] {draft.name} — 注入 {n_inject} 属性 {fb_hint}")

    print()
    print(
        f"[OK] inject 完成 — {total_files_changed}/{len(drafts)} 文件改动 / "
        f"{total_inject} 属性注入 / {total_fallback} fallback 同值"
    )
    return 0


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="add_i18n.py",
        description=(
            "阶段四 prd 草稿 i18n 工具化 (extract/inject 双模式)。"
            "触发条件: 产品定义含多语言需求 (prd_expression_standard.md §十)。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--extract", action="store_true",
        help="扫描 drafts/prd_M*_draft.html → 输出 process_record/i18n_dict.json 骨架 (merge 模式)",
    )
    group.add_argument(
        "--inject", action="store_true",
        help="读 i18n_dict.json → regex 注入 data-zh/data-en 到 drafts (幂等)",
    )

    args = parser.parse_args()

    if args.extract:
        return cmd_extract()
    if args.inject:
        return cmd_inject()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
