#!/usr/bin/env python3
"""
check_rule_coverage.py — SSOT #22 元 SSOT(precheck ↔ rule_hard_constraints)coverage 矩阵

用法：
    python pm-workflow/scripts/check_rule_coverage.py [--strict]

作用：
    SSOT 双锚 #22「precheck ↔ rule_hard_constraints 对应」5 要素第 5 项「机械兜底」
    实现的第 1 步（其余文档级双向标注挂 NB-WE-12 渐进）。

    扫 rule_hard_constraints.md 提取所有 S/G 规则编号,与 precheck_stage1/2/3/4.py
    + assemble.py 中提及的 S/G 编号做集合对比,输出 coverage 矩阵报告。

    维度：
    - rules_in_doc：rule_hard_constraints 声明的全部规则集合
    - rules_in_code：precheck/assemble 引用的规则集合（通过 grep 注释/字符串）
    - 未机械化规则：rules_in_doc - rules_in_code
    - 代码引用但未在 doc 声明的规则：rules_in_code - rules_in_doc（漂移信号）

退出码：
    0  — 报告已输出（默认非严格模式总是 0；--strict 时未机械化规则数 > 0 → 1）
    1  — --strict 模式下检测到漂移
"""

import re
import sys
from pathlib import Path

import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_paths import FRAMEWORK_ROOT, PROJECT_ROOT
RULES_PATH = FRAMEWORK_ROOT / "pm-workflow" / "rules" / "rule_hard_constraints.md"
SCRIPTS_DIR = FRAMEWORK_ROOT / "pm-workflow" / "scripts"

# 规则编号格式：S1-01 / S2-03 / S3-15 / S4-22 / G-01 / G-07
RULE_ID_RE = re.compile(r"\b([SG][1-4]?-\d{2})\b")


def extract_rules_from_doc() -> set[str]:
    """从 rule_hard_constraints.md 提取所有声明的规则编号。
    两种声明形式：① `### S4-XX 标题` 章节级；② `| S4-XX … | … |` S4 规则对照表行
    （首单元格即规则号，与 §六 对照表同型——S4-65~68 等仅以表行声明，非 ### 章节）。"""
    if not RULES_PATH.exists():
        return set()
    text = RULES_PATH.read_text(encoding="utf-8")
    rules: set[str] = set()
    for line in text.splitlines():
        if line.startswith("### "):
            for m in RULE_ID_RE.finditer(line):
                rules.add(m.group(1))
        elif line.startswith("|"):
            # 对照表行：仅当规则号是首单元格（声明），非行内引用
            m = re.match(r"\|\s*([SG][1-4]?-\d{2})\b", line)
            if m:
                rules.add(m.group(1))
    return rules


def extract_rules_from_code() -> dict[str, set[str]]:
    """从 precheck_stage1/2/3/4 + assemble.py 提取代码中引用的规则编号。
    返回 {规则 id: {引用文件名集合}}。"""
    refs: dict[str, set[str]] = {}
    target_files = list(SCRIPTS_DIR.glob("precheck_stage*.py")) + [SCRIPTS_DIR / "assemble.py"]
    for f in target_files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        for m in RULE_ID_RE.finditer(text):
            refs.setdefault(m.group(1), set()).add(f.name)
    return refs


def main() -> None:
    strict = "--strict" in sys.argv
    print("check_rule_coverage.py — SSOT #22 元 SSOT coverage 矩阵")
    print()

    doc_rules = extract_rules_from_doc()
    code_refs = extract_rules_from_code()
    code_rules = set(code_refs.keys())

    print(f"  rule_hard_constraints.md 声明规则：{len(doc_rules)} 条")
    print(f"  precheck/assemble 代码引用规则：{len(code_rules)} 条")
    print()

    # 1. 未机械化规则（doc 声明但代码无引用）
    uncovered = sorted(doc_rules - code_rules)
    print(f"未机械化规则（doc 声明但 precheck/assemble 未引用,可能仅文档/人工兜底）: {len(uncovered)}")
    if uncovered:
        for rid in uncovered:
            print(f"  - {rid}")
    print()

    # 2. 代码引用但 doc 未声明（漂移信号 — 可能是过期编号或新规则未登记 doc）
    drift = sorted(code_rules - doc_rules)
    print(f"代码引用但 doc 未声明（漂移信号）: {len(drift)}")
    if drift:
        for rid in drift:
            files = ", ".join(sorted(code_refs[rid]))
            print(f"  - {rid} 引用于：{files}")
    print()

    # 3. 双向覆盖矩阵（前 30 条作示例,完整需 markdown 报告）
    covered = sorted(doc_rules & code_rules)
    print(f"双向覆盖（doc + code 均含,机械化规则）: {len(covered)}")
    for rid in covered[:15]:
        files = ", ".join(sorted(code_refs[rid]))
        print(f"  ✓ {rid} → {files}")
    if len(covered) > 15:
        print(f"  ...（共 {len(covered)} 条,仅显示前 15）")
    print()

    print("─" * 60)
    cov_pct = (len(covered) / len(doc_rules) * 100) if doc_rules else 0
    print(f"机械化覆盖率: {len(covered)}/{len(doc_rules)} = {cov_pct:.1f}%")
    print()
    if drift:
        print("[WARN] 存在代码 → doc 漂移,需检查 doc 是否漏声明 / 代码是否用错过期编号")

    if strict and (uncovered or drift):
        print("\n[FAIL] --strict 模式：存在未机械化规则或漂移")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
