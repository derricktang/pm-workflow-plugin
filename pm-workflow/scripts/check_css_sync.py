#!/usr/bin/env python3
"""
check_css_sync.py — SSOT #4 PRD template CSS ↔ prd_expression_standard 机械兜底

用法：
    python pm-workflow/scripts/check_css_sync.py

作用：
    SSOT 双锚 #4「PRD template CSS ↔ prd_expression_standard」5 要素第 5 项「机械兜底」
    的实现。从 standard 提取所有 ```css 块的 (selector, rule_body) 集合，与 template
    `<style>` 块的同名 selector 对比，报告：
      - 漏同步：standard 含 selector, template 不含
      - 不一致：双侧 selector 同名但 rule body 字面不一致
      - template 独有：template 含 selector, standard 不含（豁免：合法的 template
        独有 CSS 如 :root 变量 / .layout / 暗色模式覆盖等不在 standard 范围）

退出码：
    0  — 全部通过（漏同步 + 不一致都为 0；template 独有不报）
    1  — 存在漏同步 / 不一致

设计：
    1. 从 standard 提取每个 ```css ... ``` 块（10 个左右）
    2. 用宽松正则提取每条 CSS rule：`selector { rule_body }`
    3. normalize rule_body（去注释 / 多空白合并 / 末尾分号统一）
    4. 集合对比：standard.selector ⊆ template.selector ?
    5. 同 selector 双侧 normalize 后字面一致 ?

不做：
    - 完整 CSS AST 对比（如属性顺序差异、嵌套规则）
    - 媒体查询 / @keyframes 内的 selector 对比（暂跳过）

SSOT 真源：prd_template.html（技术真源——拼装产物 base）
SSOT 派生：prd_expression_standard.md（规范描述）
调整方向：先改 template、再同步 standard（参 standard §九 / template §十一配套样式注释）
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_PATH = REPO_ROOT / "pm-workflow" / "rules" / "prd_template.html"
STANDARD_PATH = REPO_ROOT / "pm-workflow" / "rules" / "prd_expression_standard.md"


# ── CSS 块提取 ────────────────────────────────────────────────────────────────

CSS_BLOCK_FENCED_RE = re.compile(r"```css\s*\n(.*?)\n```", re.DOTALL)
CSS_BLOCK_STYLE_TAG_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
# 单条 CSS rule（宽松匹配,不处理嵌套 / @media）
# selector 允许多行（含逗号分隔的复合 selector）
CSS_RULE_RE = re.compile(
    r"(?P<selector>[^{};\n][^{};]*?)\s*\{(?P<body>[^}]*)\}",
    re.MULTILINE,
)
# CSS 注释剥离（/* ... */，多行）
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def normalize_rule_body(body: str) -> str:
    """
    normalize rule body：去注释 / 多空白合并 / trim / 末尾统一分号。
    用于双侧字面对比。
    """
    body = CSS_COMMENT_RE.sub("", body)
    # 折叠所有空白为单个空格
    body = re.sub(r"\s+", " ", body).strip()
    # 末尾统一分号（允许 standard 写最后一条不带分号）
    if body and not body.endswith(";"):
        body = body + ";"
    return body


def normalize_selector(sel: str) -> str:
    """normalize selector：去多空白 + trim。"""
    sel = CSS_COMMENT_RE.sub("", sel)
    sel = re.sub(r"\s+", " ", sel).strip()
    return sel


def extract_rules(css_text: str) -> dict[str, str]:
    """
    从 CSS 文本提取 (selector → normalized_body) 字典。
    重复 selector 用最后一条覆盖（与浏览器 cascade 行为一致）。
    """
    # 先剥离顶层注释（避免误匹配 /* selector { ... } */ 注释中的 selector）
    css_text = CSS_COMMENT_RE.sub("", css_text)
    rules: dict[str, str] = {}
    for m in CSS_RULE_RE.finditer(css_text):
        selector = normalize_selector(m.group("selector"))
        body = normalize_rule_body(m.group("body"))
        # 跳过 @ 规则 / 空 selector / 含 :root 等纯 token 声明（template 独有）
        if not selector or selector.startswith("@"):
            continue
        rules[selector] = body
    return rules


def extract_standard_css(text: str) -> dict[str, str]:
    """从 prd_expression_standard.md 提取所有 ```css 块的 selector → body 字典。
    逐块独立提取（避免 join 后块间文本被 regex 误识别为跨块 selector）。
    跳过示意性 CSS 块（含 `... 占位文字 ...` 等省略号字面量）。"""
    rules: dict[str, str] = {}
    for block in CSS_BLOCK_FENCED_RE.findall(text):
        # 跳过明显的示意性块（含 `...` 占位字面量,如 §9.1 fallback CSS 注入示例）
        if re.search(r"\.\.\..*\.\.\.", block):
            continue
        rules.update(extract_rules(block))
    return rules


def extract_template_css(text: str) -> dict[str, str]:
    """从 prd_template.html `<style>` 块提取所有 selector → body 字典。
    逐块独立提取（HTML 中 <style> 块通常只有 1 个,但保险起见）。"""
    rules: dict[str, str] = {}
    for block in CSS_BLOCK_STYLE_TAG_RE.findall(text):
        rules.update(extract_rules(block))
    return rules


# ── 比对 ──────────────────────────────────────────────────────────────────────

def compare_css(standard_rules: dict[str, str], template_rules: dict[str, str]) -> tuple[list[str], list[str]]:
    """
    返回 (missing_in_template, mismatched)：
      - missing_in_template: standard 含但 template 不含的 selector
      - mismatched: 双侧含同 selector 但 normalized body 不一致的 (selector, std_body, tpl_body)
    template 独有 selector 不报错（合法情况：:root / .layout / 暗色模式 / 模块占位等）。
    """
    missing: list[str] = []
    mismatched: list[str] = []
    for sel, std_body in standard_rules.items():
        if sel not in template_rules:
            missing.append(sel)
            continue
        tpl_body = template_rules[sel]
        if std_body != tpl_body:
            mismatched.append(
                f"{sel}\n        standard: {std_body[:120]}{'...' if len(std_body) > 120 else ''}\n"
                f"        template: {tpl_body[:120]}{'...' if len(tpl_body) > 120 else ''}"
            )
    return missing, mismatched


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main() -> None:
    if not TEMPLATE_PATH.exists():
        print(f"[ERROR] prd_template.html 不存在：{TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)
    if not STANDARD_PATH.exists():
        print(f"[ERROR] prd_expression_standard.md 不存在：{STANDARD_PATH}", file=sys.stderr)
        sys.exit(1)

    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    standard_text = STANDARD_PATH.read_text(encoding="utf-8")

    template_rules = extract_template_css(template_text)
    standard_rules = extract_standard_css(standard_text)

    print(f"check_css_sync.py — SSOT #4 PRD template ↔ prd_expression_standard 机械兜底")
    print(f"  prd_template.html      : {len(template_rules)} 条 selector")
    print(f"  prd_expression_standard: {len(standard_rules)} 条 selector")
    print()

    missing, mismatched = compare_css(standard_rules, template_rules)

    if not missing and not mismatched:
        print("[PASS] standard 中所有 selector 在 template 中存在且 rule body 字面一致")
        sys.exit(0)

    if missing:
        print(f"[FAIL] standard 含但 template 缺的 selector（漏同步,{len(missing)} 条）：")
        for sel in missing:
            print(f"  - {sel}")
        print()
    if mismatched:
        print(f"[FAIL] 双侧同 selector 但 rule body 不一致（{len(mismatched)} 条）：")
        for item in mismatched:
            print(f"  - {item}")
        print()

    print("修复方向：")
    print("  - 漏同步 → 在 prd_template.html `<style>` 块补全 standard 中已声明的 selector")
    print("  - 不一致 → 按调整方向「先改 template、再同步 standard」修真源,再回填规范")
    sys.exit(1)


if __name__ == "__main__":
    main()
