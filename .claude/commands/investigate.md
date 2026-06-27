# /investigate 调查分析指令

> **用途**：对任何非平凡的**调查 / 排查 / 评估 / 审计 / 方案分析 / 逻辑缺陷检查**，走标准化三步动作，杜绝「单遍自评漏判」（实证根因见 memory `feedback_single_pass_evaluation_unreliable`）。
>
> **本文件定位**：调查分析**执行纪律 + 对抗 pass checklist 的 SSOT 真源**。其他地方（memory / 派发 prompt）只引用、不复制（SSOT #59 单源约束）。**派发选型**另有真源（Step 1），本文件不复述。

## 何时走本指令

- **用户显式触发**：「用调查分析指令 / 调查 / 排查 / 评估 / 分析 / 查逻辑缺陷 X」
- **编排器自检**：凡要给出非平凡**结论 / 建议 / 判断**前，自走本指令（尤其 Step 3 呈现前对抗 pass）——**不等用户说「再次检查」**

---

## Step 1 选执行者（先定谁来做，别默认自己上）

- **判定 + 选型 `[Must]` 按** `pm-workflow/rules/agent_dispatch_protocol.md §调研 + 计划制定 subagent 派发规范`（真源，含判定决策树 + 选型表 + prompt 7 要素 + 反 pattern，**勿在此复述**）
- **速记红线**：① L1 范围评估 / 开放式 audit / 跨文件一致性扫描 → **必派 Explore/PM，主上下文禁自审**（违反信号见 CLAUDE.md §调整意见第二步越界信号）② Explore 仅「找文件 / grep symbol」轻量定位，不适合 audit ③ 用 Explore 的结论**逐项核证**（Explore 会把假阴性判假阳性，11 误报实证）
- **委派传导（L1 调查 `[Must]`）**：派 PM/Explore 做 L1 调查时，**必须在 dispatch prompt 内注入** Step 2 取证纪律 + Step 3 checklist 的 A/C/D/E 段（B 按需）——否则取证严谨性停在编排器、传不到真正干活的 subagent（同插件 B-1「纪律到编排器、没到 subagent」缺口）。呈现 subagent 结论前，编排器仍自走 Step 3 复核

## Step 2 取证（事实配命令，禁推断）

- **大结构化文档**：先 `python3 pm-workflow/scripts/doc_query.py outline|fetch|locate <file>`（SSOT #81 分节读取）—— **禁行数粗估（awk/wc 行数）、禁全文 grep 当结构**（实证：行数把「工作流架构 203 行」误当四阶段循环，真大块是调整意见 SOP ~5.5k tok）
- **计数**：`grep -o` / `len(re.findall())`，**禁 `grep -c`**（数行 ≠ 数字面）
- **HTML 嵌套 / 平衡**：`html.parser` / BeautifulSoup，**禁 grep 缩进当 DOM 嵌套**
- 每个**数字 / 存在性**断言都附可复现命令；产出里分清「**事实**」与「**由事实推出的结论**」，推理链不跳步

## Step 3 呈现前对抗 pass（5 段 checklist，逐项过 —— 本指令 SSOT）

**A. 工具与事实层**
- [ ] 大文档已走 doc_query（非行数粗估）；计数用 grep -o/findall（非 -c）；HTML 用解析器（非 grep 缩进）
- [ ] 每个数字/存在性断言有可复现命令
- [ ] 已分清「事实」与「推出的结论」，无跳步

**B. 运行时态破点（本框架特有；过程 / L2 / 方案分析必过，纯 L1 内容审计按需——仅「subagent 隔离」一条恒适用）**
- [ ] `/clear` 或会话重启后还成立？（CLAUDE.md 自动重注入 vs command/rule 不重读；恢复只读 state.md+ledger）
- [ ] subagent 隔离上下文里成立？（主会话 / SessionStart 注入的不进 subagent）
- [ ] `/compact` 有损摘要后？只读 cache / 文件不可写时？

**C. 范围与一致性**
- [ ] L1 范围评估已派 Explore/PM（非主上下文自评）
- [ ] 跨文件一致性 / SSOT 派生漂移已查
- [ ] 引用的 file:line / 数字非过时（memory 点时观测 → 现核）

**D. 反向与诱惑结论**
- [ ] 反向不可推导未踩（靠前阶段含字面 ≠ 底层逻辑）
- [ ] 「合理但错」诱惑结论已找最小命令证伪
- [ ] Explore 结论已逐项核证

**E. 完备性 critic**
- [ ] 最大 / 最重要的目标块**未被结论意外排除**（被排除 = 漏判信号）
- [ ] 无「该查没查的模态 / 该核没核的断言」

---

## 输出格式

- **结论先行**：第一句给「是什么 / 发现了什么」
- 每条事实断言**挂命令证据**；不确定项**显式标注**
- 给**可执行的下一步**，不止于诊断

> **自审记录纪律**：若呈现后又发现缺陷（如二次检查），就地更新结论 + 留「自审记录」，标明原判错在哪 + 修正（对齐 SSOT #79 当前态描述）。
