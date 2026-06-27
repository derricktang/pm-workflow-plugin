# CHANGELOG_L2 — 上游工作流框架（L2）升级日志（下游同步指引）

> **本文件定位**：面向**下游产品仓 PM / 编排器**的 L2 升级日志。每条记录上游 `claude-code-pm-workflow` 的一次工作流框架升级（precheck / assemble / gen_scaffold / 规范 / schema），并给出**下游 sync 后须知 + 整改指引**，让下游不必逐条读 commit / SSOT 锚就能理解"这次升级要我做什么"。
>
> **与既有记录的区别**：
> - `pm-workflow/nb_log.md` = 上游**开发内部**记账（NB 挂账 / 摘账），非下游向
> - `pm-workflow/rules/ssot_anchors.md` = SSOT 双锚**权威定义**（完整 5 要素，密度高）
> - **本文件** = 下游向**精简升级日志 + 整改 SOP**（消费者视角，actionable）
>
> **真源关系**：本文件是 `git log [L2-only]` commit 的**下游向派生视图**（curated）。权威仍是 commit message + ssot_anchors；本文件只做"下游怎么用"的翻译层。

---

## 如何使用本日志

**下游 PM sync 上游 L2 后的标准流程**：

```bash
# 1. 拉上游 L2 升级（下游仓内）
bash pm-workflow/scripts/sync_from_upstream.sh        # 或自然语言「同步上游」/ /syncUpstream

# 2. 查本日志：找到「上次 sync 的 commit」到「本次 HEAD」之间的所有条目，逐条看「sync 后须知」

# 3. 阶段 4 产物受影响时，重生 outputs（去 timestamp / 补兜底 / 重读 nav 等）
python3 pm-workflow/scripts/assemble.py spec --force-overwrite
python3 pm-workflow/scripts/assemble.py prd  --force-overwrite

# 4. 跑 precheck 看新校验 WARN，按本日志对应条目的「整改指引」处理
python3 pm-workflow/scripts/precheck_stage4.py
```

**强度约定**：
- **[Must]** = 不做会破坏产物 / 阻塞（如重生 outputs）
- **[Should]** = WARN 阶段新校验，逐步整改（dry-run 纪律 ≥ 2 仓 FP < 30% 后才升 FAIL）
- **[FYI]** = 仅规范 / 内部机制，下游无须动作

---

## 升级条目（倒序，最新在上）

### 2026-06-12 · 第二轮审计 hot-fix（CR 串行约束空转修复 + 中段审核 logic-only 闸 + 防御群）

| 维度 | 内容 |
|------|------|
| **类型** | changeRequest.md 1.1 修复 + 主管 §4.5 D-10 扩展 + 2 个新测试 + 5 处措辞/防御 |
| **一句话** | **P1 真 bug：CR 串行约束自上线起空转**——1.1 扫 `changes/CR-*.md` 找状态，但状态全流程只写 `state.md`「变更记录」章节（分析文件无状态字段）→ 永不 abort、多 CR 可并行。修复：1.1 改读 state.md 真源 + 闭环状态集补「❌ 执行中撤销」。P2：D-10 加第⑤项 logic-only（pages=[]）误标人工闸（误标 → Step 3/5 跳派、模块 spec 永不生成，schema 不拦）；template_purity 补测试（hook 行为守）。P3：版本号步禁中断注记 / SPEC_MODULES 唯一性 WARN / 注入顺序锁定测试等 |
| **下游影响** | 下游编排器跑 /changeRequest 时 1.1 检查行为变更（改读 state.md）——**此前若有并行 CR 历史属此 bug 放行**；中段审核多一项 D-10⑤ 核查 |

**sync 后须知 [Should]**：

- /changeRequest 1.1 现在以 `state.md`「变更记录」章节为状态真源——若 state.md 有历史 CR 条目状态字段缺失/非标，先补齐再启动新 CR。
- Step 1.X 中段审核按 D-10⑤ 逐个核对 `pages=[]` 模块（对照阶段 2 基线确认真 logic-only）。


### 2026-06-12 · 逻辑审计 hot-fix（#82 用法修正 + 派发清单分节注记 + 脚本边界修复）

| 维度 | 内容 |
|------|------|
| **类型** | 协议用法修正（主管 §4.4 spec 段）+ dispatch protocol 派发清单批量注记 + doc_query/备份脚本边界修复 + 计数漂移清理 |
| **一句话** | 产品总监触发逻辑审计（3 Explore + 核证：7 确认 / 4 误报剔除）。P0：§4.4 spec fetch 示例用裸编号短前缀（"S0"/"S2.M01"）实测必歧义 exit 2 → 改「outline 取完整结构树 → 节点清单进审核进度文件作 spec checklist → 完整标题逐节点 fetch」（spec/prd checklist 防漏同构）。P1：7+ 处子角色派发清单补分节注记；孤儿 FRAME-START 静默丢帧 → stderr WARN；计数漂移群按 SSOT #60 D 清理为动态指针。P2：fetch 同名去重 / 备份时间戳统一 UTC / 备份保留最近 20 份 |
| **下游影响** | Supervisor 终审 spec 侧用法变更（见 sync 后须知）；其余对下游透明 |

**sync 后须知 [Should]**：

- 阶段4终审 spec 侧：`outline <spec>` 取结构树 → 节点清单（完整标题）复制进审核进度文件作 spec checklist → **用完整标题**逐节点 fetch（禁 "S0"/"S2.M01" 短前缀查询词）。
- `frames` 输出若带「无配对 FRAME-END」WARN → 先修帧标记配对再开始终审（否则 checklist 漏帧）。
- 备份目录自动保留最近 20 份（更早自动清理）；时间戳统一 UTC。


### 2026-06-11 · SSOT #81 扩展：阶段4 三杠杆（子角色分节 + 两规范入分节 + TP 定点取节）

| 维度 | 内容 |
|------|------|
| **类型** | SECTION-MAP 表扩展（agent_dispatch_protocol）+ 元测试 MAPPED_FILES 3→5 + Step 1 TP 派发清单第 13 项 |
| **一句话** | 阶段4 各子角色派发上下文再压缩：a 子角色行（TP/FA/PI/S/P 各取自己的子阶段节，不再全读「阶段四」18k；六.X 对照表从写作子角色剥离）b `prd_expression_standard`（41k）+ `proto_spec_md`（19k）入分节（FA 取规格区族 ~16k / P 取帧规范族 ~25k / S 取模块草稿族 ~11k）c TP 定点 fetch「scaffold v2.0 schema」节（14.5k vs 全读 34k，顺治原「详见下方」悬空引用）|
| **下游影响** | 编排器派发阶段4子角色时按 §大文件分节读取规范 SOP 第 1 步新行选择规则组 fetch 命令；P 模块 PRD agent 等单派发再省 ~40k |

**sync 后须知 [Should]**：

- 阶段4 子角色派发 fetch 行 = 「全部 PM 任务」∪「阶段4 子角色通用」∪ 该子角色行（含 prd_expression/proto_spec 对应行）∪ rule_hard「通用+六」；整改未明子角色 → 「阶段4 PM fallback」行。
- TP 派发 prompt 加第 13 项 schema 定点 fetch 命令（Step 1 清单已更新）。
- 改 5 个纳管文件章节结构后跑 `pytest tests/test_section_coverage.py`。

### 2026-06-11 · SSOT #82 阶段4终审「机械全量 + 分节全量语义审查（默认）/抽样（降级）」协议

| 维度 | 内容 |
|------|------|
| **类型** | Supervisor 审核协议（`AI产品主管_Agent.md §4.4 终审读取与覆盖协议`）+ `doc_query.py` 新增 frames/fetch-frame + Supervisor 派发清单措辞 |
| **一句话** | 阶段4终审单次全文 Read spec+prd ≈ 430-700k tokens（实测私域 prd 143 帧 389k）注意力摊薄。改两层：①机械全量 = precheck 89 项报告为审核输入不重复人工查 ②语义审查**默认 = 分节全量遍历**（产品总监澄清：覆盖率全量 ⊥ 加载分批两正交概念）——doc_query 分批 fetch **全部**模块节+全部帧，**帧清单进审核进度文件作 checklist 逐帧 [x] 防漏**（终审结束必须全勾）；**抽样仅是上下文受限的降级模式**（深读 ≥⌈N/3⌉ 模块 + 非深读每模块 ≥3 帧 + 扩样升级 + 禁冒充全量）|
| **下游影响** | 编排器派发阶段4终审 Supervisor 时，prompt 注明「spec/prd 禁一次性全文 Read，按 §4.4 终审读取与覆盖协议默认分节全量遍历」；Supervisor 用 `doc_query.py frames/fetch-frame` 分批遍历 |

**sync 后须知 [Should]**：

- 阶段4终审派发 prompt 加注「按 `AI产品主管_Agent.md §4.4 终审读取与覆盖协议` 执行：禁一次性全文 Read；默认分节全量遍历（全部模块节 + 全部帧）」。
- Supervisor：`python3 pm-workflow/scripts/doc_query.py frames outputs/prd_*.html` 列帧清单 → **复制进审核进度文件作 checklist** → 逐帧 `fetch-frame` 审核 + 即时 [x]（每批 3-5 帧，批间结论落盘）；终审报告列「模块节 N/N + 帧 M/M 遍历完成」。
- 仅上下文受限（标准 200k 窗）时降级抽样模式，覆盖率声明改列抽样清单 + 占比，禁冒充全量。
- 整改复审/CR 后增量终审：git diff 定位变更帧全读；未变部分凭前轮 checklist 免重审。

### 2026-06-11 · SSOT #81 大文件分节读取机制（doc_query + 必读章节清单 + 防漏读元测试）

| 维度 | 内容 |
|------|------|
| **类型** | 新 `doc_query.py` 工具 + 派发协议（`agent_dispatch_protocol.md §大文件分节读取规范` 含 SECTION-MAP 必读章节清单）+ CLAUDE.md 开工第一步措辞 + 2 个新测试文件 |
| **一句话** | PM/Supervisor 派发基线 ~120k tokens 中 ~100k 是全阶段混装死重（AI产品经理/rule_hard 全读但单任务只用 25-40%）。3 个大文件改「outline 看架构 → fetch 必读章节」按需加载（实测阶段1 PM ≈11k vs 全读 ~60k）；防漏读三层：清单 L2 真源 + 元测试守漂移 + fetch fail-loud；`--max-tokens` 预算闸防跨章共读撑爆 |
| **下游影响** | 编排器派发 prompt 对 3 个大文件给 fetch 命令（从 SECTION-MAP 表复制通用行∪任务行）；subagent 不再 Read 这 3 个文件全文。Supervisor 阶段3/4 前序成果/spec 同样可 outline+fetch 涉审章节定位读 |

**sync 后须知 [Should]**：

- 编排器派发 PM/Supervisor 时，对 `AI产品经理_Agent.md` / `AI产品主管_Agent.md` / `rule_hard_constraints.md` 按 `agent_dispatch_protocol.md §大文件分节读取规范` 给 fetch 命令，prompt 注明「禁全读」。
- subagent：`python3 pm-workflow/scripts/doc_query.py outline <file>` 先看架构 → 按 prompt fetch；标题未命中必上报（章节可能改名）；清单是下限，任务涉及清单外章节先 outline 再补 fetch。
- 改这 3 个文件的章节结构后跑 `pytest tests/test_section_coverage.py`（漏读漂移守）。

### 2026-06-11 · SSOT #80 阶段 4 派生链路真源完整性 + 破坏性操作备份兜底

| 维度 | 内容 |
|------|------|
| **类型** | 规则（CLAUDE.md 区域→真源对照表 + AI产品经理 §三.5 G.0）+ **脚本行为**（`assemble.py` / `gen_scaffold.py` 覆盖前自动备份 + force-overwrite 去静默）|
| **一句话** | 私域主页 force-rescaffold 冲掉前几天积累 prd 调整。根因：① C-4 业务契约 / A-05 功能索引在 prd 是从 spec **派生注入**，改 prd draft 必被重装盖回 ② `gen_scaffold --force-rescaffold` 会**覆盖已填 module drafts**（源层被擦，重装救不回）。治本：区域→真源对照表（改对层）+ 破坏性覆盖前自动备份 + 去静默警告 |
| **下游影响** | ① 教育：PM 改 C-4/A-05 **必改 `spec_M[XX]_draft.md .4B/.5B/.7` 走全四步**，禁只改 prd draft ② 行为：`assemble --force-overwrite` / `gen_scaffold --force-rescaffold` 现在覆盖前自动快照到 `process_record/versions/.assemble_backups/`（无须动作，冲掉能找回）|

**sync 后须知 [Should]**：

- **改 prd 的 C-4 业务契约 / A-05 功能索引** → 改 `process_record/drafts/spec_M[XX]_draft.md` 的 `.4B/.5B/.7` 段 → `assemble.py spec --force-overwrite` → `assemble.py prd --force-overwrite`（C-4/A-05 自动派生下来）。**禁**在 prd draft 改这两区（重装必丢）。
- **`gen_scaffold --force-rescaffold` 仅结构级变更（/changeRequest 编号变更）才用** —— 它会覆盖已填 module drafts；用前确认 drafts 已 commit。现已加覆盖前自动备份兜底。
- 备份目录 `process_record/versions/.assemble_backups/<时间戳>_<tag>/`（已被 `process_record/` gitignore，本地保留）；冲掉后从此目录取回。

### 2026-06-11 · SSOT #79 内联变更标记正向指引补强（5 项：禁令→闭环）

| 维度 | 内容 |
|------|------|
| **类型** | 规范补强（`rule_hard_constraints.md` G-02/G-07/S4-68 + `AI产品经理_Agent.md` §8.3 + `AI产品主管_Agent.md` §4.0.4 + 3× `tmpl_*.md`），**无脚本 / schema 改动** |
| **一句话** | 下游 PM NB（按 SSOT #31 上报）：原「禁内联标记」规则只有禁令一头，PM 知道「不该写什么」、不知「该怎么做」，清完会再犯。补 5 项形成闭环：①正向「当前态-only」原则 ②G-02「变更原因」列承接类别使用指南 ③先存后删清理 SOP ④G-07 授权痕清理留存形式 ⑤WARN→FAIL 升级触发界定 |
| **下游影响** | 纯规范层。PM 写产物 / 清理存量标记时多了正向操作指引；precheck 行为不变（仍 WARN，但升 FAIL 条件已明确界定 = ≥2 独立产品仓 + 清理 ≥90% + workflow-evolution 评估） |

**sync 后须知 [Should]**：

- **写产物时（防增量）**：成果正文只描述产品**当前态**，版本演进信息只进变更记录表「变更原因」列 + git，正文不留新旧对照 / 演进批注（`git diff` 查差异）。
- **清理存量标记时（先存后删）**：删正文内联标记前先确认该溯源已在变更记录表 / `decisions_ledger.md` 留痕，没有则先补；删除**只去标记、不改正文语义**（机械删除损伤语义）；用 `strip_inline_change_markers.py` 只读报告定位 + 人工删；Supervisor 终审抽检「删除 ≠ 改义」。
- 无须重生 outputs / 无新 precheck WARN。

### 2026-06-11 · 变更循环闭环前必提交（[Must] 规则 + check_uncommitted_l1.py 机械兜底）

| 维度 | 内容 |
|------|------|
| **类型** | CLAUDE.md [Must] 规则 + 新 `check_uncommitted_l1.py` + changeRequest/nextStage 命令流程接入 |
| **一句话** | SSOT #79「查版本差异用 git diff」的前置：**开始新变更循环（调整意见/CR/nextStage）前，上一循环 L1 必已提交**（message 带 issue/CR/SNB 编号）——否则 git diff 混多变更、git log 无法精确归属，PM 退回内联标记。机械兜底 `check_uncommitted_l1.py` 扫 `outputs/` 未提交 → WARN |
| **下游影响** | 新增机械兜底（[Should] WARN 恒退出 0 不阻断）：编排器在调整意见第四步 step 0 / changeRequest 1.2 / nextStage 第一步 跑该脚本，提示「上批未提交先 commit」 |

**sync 后须知 [Should]**：

- 编排器开始新变更循环前跑 `python3 pm-workflow/scripts/check_uncommitted_l1.py`（缺省扫当前仓 `outputs/`）；有未提交 → 先 commit（带编号）再开始下一个。
- 粒度 = 变更循环（一个调整意见内多文件一起提交；不同循环禁堆未提交）。**查版本差异用 `git diff`**。
- 不阻断（退出码恒 0）——同循环批处理 / 首次循环可忽略 WARN。

---

### 2026-06-10 · 🐞 修复 sync_from_upstream.sh 在 commit 前崩溃（pipefail + diff 退出码，下游 PM 实测）

| 维度 | 内容 |
|------|------|
| **类型** | sync_from_upstream.sh bug fix（二阶段核验 `diff <(…)` 管道加 `\|\| true`）|
| **一句话** | `set -euo pipefail` 下 `diff <(BEFORE) <(FINAL)` 在两输入不同时返回 exit 1，经 pipefail 冒泡到命令替换赋值触发 `set -e`，在 `git commit` 前中止整脚本——而 Step 7 assemble 必改 `outputs/` → 二阶段核验 `BEFORE != FINAL` 必成立 → **每次真实 sync（跑了 assemble）必崩** |
| **下游影响** | **修复后 sync 正常完成 commit**，不再 commit 前崩。之前若遇「sync 跑完 assemble 后崩、需手动补 L2-only commit」即此 bug（line 487 + line 382 latent 同型一并加固）|

**sync 后须知 [Must]**：

- 拉本次修复后，`sync_from_upstream.sh` 不再在 commit 前因 assemble 改 outputs/ 而崩；正常走到 `[8.2] git commit`。
- 若之前手动补过 commit：本次只需确认脚本已更新（`grep -n 'diff <(' pm-workflow/scripts/sync_from_upstream.sh` 两处均应带 `|| true`），无需回滚已补的 commit。
- 回归锁：`tests/test_sync_from_upstream.py::test_diff_pipelines_have_pipefail_guard` 静态校验所有 `diff <(` 管道带 `|| true`，防回退。

---

### 2026-06-10 · strip_inline_change_markers 改为只读报告（移除 --write 自动删除，审计实证损伤语义）

| 维度 | 内容 |
|------|------|
| **类型** | strip_inline_change_markers.py 重构（移除 `strip_text` + `--write` + `--version-only`，退回只读报告）|
| **一句话** | 审计发现机械"自动删除"会损伤语义（①共存新旧版本标记删后合并矛盾 `【v3.0】旧【v4.0】新`→`旧新` ②需求与追溯同括号不可机械拆 `（不进 phase_e；NB-256…G-07 授权）` ③悬挂分隔/空括号连带损伤），故工具退回**纯定位 + 分类报告**，删除一律 PM 手动做 |
| **下游影响** | 工具命令行变更：**不再有 `--write`**；跑后只出报告（version/pure_ref/mixed 分类 + 行号），不改文件。检测/precheck WARN 行为不变 |

**sync 后须知 [Should]**：

- 之前若有脚本/习惯用 `strip_inline_change_markers.py --write` 自动清理——**已移除**，改为据只读报告 PM 手动改。
- 报告分类含义：`version`=删标签留内容（注意共存新旧勿合并）/ `pure_ref`=整条删 / `mixed`=PM 拆（需求留正文、追溯进变更记录表）。
- **查版本差异用 `git diff`**，不靠正文内联标记。

---

### 2026-06-10 · SSOT #79 防线前移至全阶段（禁内联标记 stage1/2/3/4；版本差异用 git diff）

| 维度 | 内容 |
|------|------|
| **类型** | precheck_stage1/2/3 各加 check_no_inline_change_markers（WARN，单源自 strip 脚本 warn_inline_markers）+ tmpl_需求分析/功能规划/产品定义 + CLAUDE.md + PM Agent §8.2 升跨阶段 |
| **一句话** | 内联变更标记禁令从**仅阶段 4**前移到**阶段 1/2/3/4 全链路**——根因：标记源头在前序阶段（实证私域 需求 478/功能 508/产品定义 618），会顺管线搬进交付 spec/prd；**查版本差异请用 `git diff`**，不在正文留标记 |
| **下游影响** | precheck_stage1/2/3 新增 WARN（不阻塞）：阶段 1-3 产物含内联标记会报 WARN + 给 git diff 提示 + 清理命令。**workflow 信号 `【✅ PM 自审完成…】` 已从 pattern 移除豁免**（与 check_submit_marker 不冲突）|

**sync 后须知 [Should]**（WARN 阶段，全阶段守源头）：

- 各阶段跑 `precheck_stage[N].py` 看「内联变更标记纪律」section 的 WARN 数。
- 清理任意阶段产物：`python3 pm-workflow/scripts/strip_inline_change_markers.py outputs/需求分析_*.md outputs/功能规划_*.md outputs/产品定义_*.md outputs/spec_*.md outputs/prd_*.html`。
- **今后写任何阶段产物**：变更历史走变更记录表 + git，**查版本差异用 `git diff`**，正文不留 `【vN.N 新增】`/`（CR-…）` 等内联标记。

---

### 2026-06-10 · SSOT #79 / S4-68 spec/prd 正文禁内联变更标记（防复发 + 清理工具）

| 维度 | 内容 |
|------|------|
| **类型** | 新增 `precheck_stage4.check_no_inline_change_markers`(S4-68，WARN) + 新脚本 `strip_inline_change_markers.py` + 规范（rule_hard_constraints / proto_spec_md / prd_expression_standard / PM Agent §8.2）|
| **一句话** | spec/prd 正文**禁**内联变更 / 过程标记（`【vN.N 新增】`/`【历史留痕…】`/含 `CR-`/`议题 #`/`SSOT #`/`调整意见` 的圆括号）——变更历史只走变更记录表 + git；schema 标记（`【触发态】【组件】…`）+ `（来源：…）` 豁免 |
| **下游影响** | precheck 新增 S4-68 **WARN**（不阻塞）：既有下游正文含历史内联标记会报 WARN + 给清理命令；实证 private-domain spec=589/prd=480、business-circle spec=0/prd=2，FP≈0% |

**sync 后须知 [Should]**（WARN 阶段，渐进清理）：

- 跑 `python3 pm-workflow/scripts/precheck_stage4.py` 看 S4-68 WARN 数（0 = 正文干净，无需动作）。
- 定位存量：`python3 pm-workflow/scripts/strip_inline_change_markers.py outputs/spec_*.md outputs/prd_*.html`（**只读报告**，按 version/pure_ref/mixed 分类 + 行号列出；`--show-fused` 看融正文圆括号）→ **删除一律 PM 手动做**（2026-06-10 审计移除自动删除——机械删除会损伤语义：共存新旧版本合并矛盾 / 需求与追溯同括号不可拆）。**查版本差异用 `git diff`**。
- **优先在 drafts 上清理后重 assemble**（outputs 是 drafts 派生，否则下次 re-assemble 丢改动）。
- 今后 PM 写 spec/prd 草稿**禁**手写内联变更标记（PM Agent §8.2 + S4-68）；变更历史走变更记录表 + git。

---

### 2026-06-10 · spec.md 变更记录段去内部过程 meta 文字 + cover-version 单源加固

| 维度 | 内容 |
|------|------|
| **类型** | assemble.py（SPEC_FOOTER）+ gen_scaffold.py（build_cover_page）|
| **一句话** | spec.md `## 变更记录` 段删除两段渲染进输出的内部过程 meta 文字（版本触发点叙述 + 「变更内容」字段格式 authoring 指令），**保留** G-02 变更记录表本身；gen_scaffold cover-version 改优先读 `changelog[-1].version` 单源 |
| **下游影响** | re-assemble spec 后，下游 spec.md `## 变更记录` 上方不再出现「本表仅记需求变更…下游无需理会」「[Must] 变更内容字段格式…」两段 meta 文字，仅留变更记录表；prd cover-version 行为不变（assemble overwrite 早已治本，本次仅初始单源加固）|

**sync 后须知 [Should]**：

- 跑 `python3 pm-workflow/scripts/assemble.py spec --force-overwrite` 重生 spec.md，变更记录段即清爽（无 meta 文字 + 保留表）。
- 「变更内容」字段强制分点格式规则**未丢**——真源在 PM Agent §5.0 + nextStage.md 场景 A/B（升版本时按其格式填表）。
- prd 端无 meta 文字（gen_scaffold build_changelog_page 本就只渲染表格），无需动作。

---

### 2026-06-10 · [FYI] mermaid CDN 升级 v10 → v11

| 维度 | 内容 |
|------|------|
| **类型** | prd_template.html CDN 版本 bump（+ 配套文档） |
| **一句话** | mermaid CDN 由 `mermaid@10` → `mermaid@11`（`https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js`）|
| **下游影响** | 自动——`assemble._overwrite_scripts_from_template`（版本无关正则）下次 re-assemble 时把 outputs/prd 的 mermaid 标签同步为 @11，**无需手动动作** |

**sync 后须知 [FYI]**：

- 重跑 `assemble.py prd --force-overwrite` 后 outputs/prd 的 mermaid CDN 即为 @11；无需改任何草稿。
- 初始化 API（`mermaid.initialize({startOnLoad:false, theme:'neutral', flowchart:{...}})` + `mermaid.run({nodes})`）v10/v11 兼容，无代码改动；init 仍 try/catch 优雅降级。
- **建议视觉抽验**：v11 是大版本，打开一个含 mermaid 图的 outputs/prd（如页面架构总览 / 业务流程图）确认渲染正常（机械检查覆盖不到视觉）。

---

### 2026-06-10 · SSOT #78 端口帧 CSS 类名一致性（小程序帧 mp-frame → miniprogram-frame）

| 维度 | 内容 |
|------|------|
| **类型** | L2 模板/校验缺陷修复（帧类名统一）+ 新回归测试 |
| **一句话** | 小程序帧 canonical 类名分裂——S4-04 白名单 + 端口帧表用 `mp-frame`，但全部帧样式（设计系统 + 模板）用 `.miniprogram-frame`；产品按 canonical `mp-frame` 写帧拿不到任何样式（帧塌缩 + 移动抽屉逃逸污染 sidebar）。统一为 `miniprogram-frame`（对齐样式真源） |
| **下游影响** | ① S4-04 白名单 + 平台覆盖：`mp-frame` → `miniprogram-frame`（**用 `mp-frame` 的帧现在会 FAIL S4-04**）② 来源：私域 NB-WE-MP-FRAME-CSS-NAME 上报（议题 #24 反复治标根因）|

**sync 后须知 [Must]**：

1. **若你的产品声明了小程序端口且帧用了 `.mp-frame`**（曾按 `proto_cross_platform §端口帧表` 旧 canonical 或自行止血补的 `.mp-frame` CSS）：
   - 把 prd 草稿 / outputs 里所有 `.mp-frame` / `mp-frame` → `.miniprogram-frame` / `miniprogram-frame`
   - **撤掉**任何为 `.mp-frame` 手补的 PROJ-CSS 止血块（`miniprogram-frame` 现在有设计系统 + 模板的全套帧样式，无需自补）
   - 重跑 `assemble.py prd --force-overwrite` + `precheck_stage4.py` 确认 S4-04 PASS
2. **若你的产品已用 `.miniprogram-frame`**（如 business-circle）：**无须动作**——canonical 就是它，样式齐全。
- **根因 + 预防**：本 bug 因「S4-04 白名单声明的帧类 ≠ 样式真源实现」漂移且无机械兜底而反复治标；本次新增 `tests/test_frame_class_css_coverage.py` 锁定「每个白名单帧类必在 prd_template.html 有 CSS」，L2 改动时即拦下同类漂移。

---

### 2026-06-10 · SSOT #77 PRD 帧级渲染契约（R8 标记式方案，5 层）

| 维度 | 内容 |
|------|------|
| **类型** | 新脚本 `gen_render_contract.py` + 新 precheck WARN（S4-67）+ 新 prd 标记约定（`data-field` [Must]）+ Step 5 派发流程 + Supervisor 新审核维度 |
| **一句话** | 阶段 4 批量 PRD 生成易因注意力摊薄漏搬运 spec 已有细节（Pad 端/触点源/字段）；本方案从 spec 权威列导出 per-frame「必画清单」落任务卡，PRD agent 逐条强制渲染 + 打可追溯标记，机械核标记完整性（零 FP）+ Supervisor 抽样核内容正确性 |
| **下游影响** | ① 新增 `precheck_stage4` S4-67 WARN（验 `data-tp`/`data-field` 标记完整性）② `data-field` 升 [Must]（既有 prd 普遍未标 → WARN，非阻塞）③ 阶段 4 Step 5 流程：编排器派发前跑 `gen_render_contract --write` 落契约 checklist 进任务卡 |

**sync 后须知 [Should]**：

1. 跑 `precheck_stage4.py` → SSOT #77 / S4-67 会对**契约期望但帧内缺 `data-tp`/`data-field` 标记**的项 WARN
   - `data-tp`（触点）既有 [Must]（§6.1）→ 多数已标，缺的是真·触点漏渲染/漏标记
   - `data-field`（字段）是**本次新 [Must]**（§6.2）→ 既有 prd 普遍未标，WARN 量大属**迁移基线**非错误，逐帧补标即可（按任务卡渲染契约 checklist）
2. **新生产阶段 4 PRD 的下游**：编排器在 Step 4（spec 完成）后、派发 PRD Agent 前跑一次 `python3 pm-workflow/scripts/gen_render_contract.py --write`（落 per-frame 必画清单 checklist 进各任务卡 `[RENDER-CONTRACT-START]…[END]`）；PRD Agent 逐条渲染 + 完成即勾 `[ ]→[x]` + 打 `data-tp`/`data-field` 标记（详 `prd_expression_standard §6.2` + `agent_dispatch_protocol Step 5`）
3. **Supervisor 终审**：新增「渲染契约标记语义抽样」维度（§4.4）——抽 ≥5 标记元素核内容正确性（机械验完整性 + 人工验正确性分工；catch 空标记注水）
- **设计要点**：机械层**验标记 presence 不验勾**（勾是自报不可信）→ 零 FP-by-design；不可枚举模糊项（§11 异常/NB 边缘态）显式划归任务卡「人工对照」段，归 Supervisor 抽样、不进机械 check。
- **已知 v1 边界**：modal 内部交互元素若在 spec `.2 页面表现` 自由文本描述而未编入 `.3 触点表` → 归人工对照区，不强制 `data-tp`。

---

### 2026-06-10 · SSOT #76 scaffold 内嵌子组件构造 embedded_components（R3）

| 维度 | 内容 |
|------|------|
| **类型** | 新增 scaffold 可选构造 + gen_scaffold 渲染 + precheck 收集扩展（**向后兼容，零强制迁移**）|
| **一句话** | scaffold 新增 `modules[].pages[].embedded_components[]` 构造——页内子卡片/子 modal 含自己的状态帧但不占独立 page/route，从源头消除"PM 为出帧把内嵌面逼成独立页"的页膨胀压力 |
| **下游影响** | 纯**新增可选字段**：不用 = 行为零变化；用了 = 内嵌帧自动获得 section/FRAME/nav/draft 全套渲染 + #72 frame 一致性覆盖 |

**sync 后须知 [FYI → 按需 Should]**：

1. **不用 embedded_components 的下游**：**无须任何动作**——无该字段时 gen_scaffold / precheck 行为与升级前**字节级一致**（已 dry-run 验证私域 35 prd_id 零影响）。
2. **想用 embedded_components 的下游**（治"内嵌子卡片被抬成独立页"，常见于阶段 2 标注"内嵌某页"的强制下架卡片/确认 modal 等）：
   - 在对应 page 加 `"embedded_components": [{"id": "<embed_id>", "name": "...", "archetype": "...", "states": [{"name": "default", "prd_id": "H-M[XX]-P[XX]-<embed_id>-default", "roles": [...]}]}]`
   - 内嵌 `prd_id` **必须**以父页 `H-M[XX]-P[XX]-` 前缀开头（precheck 校验）；不占页面数、不需 `route`
   - 重跑 `gen_scaffold.py`（生成内嵌 section + FRAME 占位 + draft FRAME 块）→ PM 填 draft → `assemble.py prd --force-overwrite`
   - 跑 `precheck_stage4.py` 确认 #72 frame 一致性 PASS（内嵌帧已纳入 scaffold↔outputs 对账）
3. **把既有"内嵌外化成独立页"重构为 embedded_components**（与 #74 配合）：把独立 page 的状态搬进父页的 `embedded_components[].states`，删除该独立 page entry，重跑 gen_scaffold + assemble。
- **v1 限制（NB）**：内嵌帧暂不派生 C-4 业务契约子区块（内嵌帧仍有 interaction-card 交互说明；完整 C-4 属未来增强）；内嵌状态不参与 page-only 语义校验（状态覆盖/archetype 语义/spec 状态表计数）。
- **关键边界**：与 #74「禁擅自增页」正交——#74 是纪律层（缺页须上报产品总监），#76 是根因层（补 schema 表达力让"该内嵌的"有正确落点）。

---

### 2026-06-09 · `f96fb18` · SSOT #75 阶段 4 蓝图质量三校验（R5/R6/R7）

| 维度 | 内容 |
|------|------|
| **类型** | 新增 precheck 校验（3 个，均 WARN 阶段）|
| **一句话** | scaffold 蓝图层加 3 个质量校验：archetype 语义匹配 / §11 异常覆盖 / depends_on 依赖环 |
| **下游影响** | `precheck_stage4.py` 新增 3 个 WARN；scaffold 可选新字段 `page_archetypes[].semantic_category` |

**sync 后须知 [Should]**：跑 `precheck_stage4.py`，可能出现 3 类新 WARN，按需整改：

1. **SSOT #75-R5 archetype 语义**：表单类范式（admin-form-flow 等）套了纯状态展示页 → WARN
   - **整改**：只读状态页改套只读/状态类 archetype；若确为表单页 → scaffold 该 archetype 加 `"semantic_category": "form"` 显式豁免
2. **SSOT #75-R6 §11 异常覆盖**：产品定义 §11 异常条目数 >> scaffold 错误类 state 数（< 50%）→ WARN
   - **整改**：人工对照产品定义 §11 异常全集，补 scaffold 缺承载的异常态（本检是**粗信号**，需人工确认非误报）
3. **SSOT #75-R7 depends_on 环**：data_flow/permission 运行时依赖成环 → WARN
   - **整改**：核查是否把「页面跳转入口」误建成 data_flow 反向依赖 → 改 `kind: section_jump`（跳转不计入运行时依赖图）；真循环依赖需重新建模数据流向

---

### 2026-06-09 · `c0ddbf7` · SSOT #74 阶段 2 页面集守恒（PM 禁擅自增页）

| 维度 | 内容 |
|------|------|
| **类型** | 新规则 + 新 precheck（WARN）+ Supervisor 新审核维度 |
| **一句话** | 阶段 2 §3.1/§3.3 页面集 = 产品总监审核的 SSOT 基线；下游不得擅自增页；缺页 → 上报产品总监拍板 |
| **下游影响** | scaffold 每页建议加 `page_source` 字段；`precheck_stage4` 新增 WARN；Supervisor 中段审核 +D-10 |

**sync 后须知 [Should]**：

1. 跑 `precheck_stage4.py` → SSOT #74 会对**每个缺 `page_source` 的页** WARN（既有 scaffold 普遍未标）
   - **整改**：逐页补 `"page_source": "stage2"`（追溯阶段 2 §3.3 基线的页）
2. **若发现某页是阶段 2 未定义的「擅自增页」**（如把内嵌子卡片抬成独立页）：
   - 内嵌项 → 改为承载页的子状态/子区域（**禁外化独立 page**）
   - 业务流程确实缺页无法闭环 → **禁擅自加**，按 `agent_dispatch_protocol.md 第 8 条` 上报产品总监拍板 → 批准后标 `"page_source": "director_approved:<YYYY-MM-DD>"` + 回写阶段 2 §3.3
- **关键边界**：scaffold 仍是阶段 4 的 SSOT（页面层级渲染派生方向不变）；#74 只约束「页面集成员不得擅自扩张」，与 #38 正交

---

### 2026-06-07 · `e378d5f` · SSOT #73 outputs/prd assemble 输出确定性

| 维度 | 内容 |
|------|------|
| **类型** | assemble 治本 + 新 precheck（WARN）|
| **一句话** | assemble 不再往 outputs/prd 注入 wall-clock 时间戳 → sha 字节级确定性恢复 |
| **下游影响** | outputs/prd 重生后 sha 变化（一次性 baseline 升级）；之后两次 assemble sha 一致 |

**sync 后须知 [Must]**：

1. 跑 `assemble.py prd --force-overwrite` 重生 outputs/prd（清除残留 `assembled=<时间戳>` 字面）
2. 验证：连跑两次 `assemble.py prd --force-overwrite` + `sha256sum outputs/prd_*.html` → **两次 sha 应字节级一致**
3. `precheck_stage4.py` SSOT #73 应 PASS（`assembled=` 0 命中）
- **收益**：outputs/prd 恢复字节级确定性 → CLAUDE.md「PM 自报 sha vs 工作树 sha vs Supervisor 复跑 sha 三方对账」对 outputs/prd 重新生效（之前因时间戳每次 assemble sha 必差而失效）

---

### 2026-06-07 · `d197b67` · SSOT #72 scaffold ↔ outputs FRAME 一致性

| 维度 | 内容 |
|------|------|
| **类型** | assemble 容错降级 + 新 precheck（WARN）|
| **一句话** | FRAME 占位缺失从 ERROR 退出 → WARN + skip（reassembly 不再被阻塞）+ 漂移双向检测 |
| **下游影响** | `assemble.py prd --force-overwrite` 遇 scaffold/outputs 漂移不再 `sys.exit(1)` 崩 |

**sync 后须知 [Should]**：

1. 跑 `precheck_stage4.py` → SSOT #72 报 scaffold ↔ outputs FRAME 漂移（A：scaffold 有 outputs 无 / B：outputs 残留孤儿）
2. **整改**（二选一）：
   - 推荐：`python3 pm-workflow/scripts/gen_scaffold.py --force-rescaffold` 重生骨架（A 自动补 placeholder + B 清孤儿）⚠️ 注意：会覆盖未 commit 的 drafts，**先 commit/stash 工作树**
   - 手动：补缺失 placeholder + 定位删孤儿 frame

---

### 2026-06-07 · `bb83fd7` · SSOT #71 outputs/prd 真 DOM div 平衡

| 维度 | 内容 |
|------|------|
| **类型** | assemble PROTO nav 覆盖 + div 平衡兜底 + 新 precheck（WARN）|
| **一句话** | sidebar PROTO 组 nav 也从 scaffold 真源重写（补议题 28 SPEC/SITEMAP）+ outputs/prd div 平衡兜底 |
| **下游影响** | page 增删后 sidebar PROTO nav 自动重生；outputs/prd 缺 `</div>` 自动补 |

**sync 后须知 [Should]**：

1. 跑 `assemble.py prd --force-overwrite` → PROTO nav 自动对齐当前 scaffold + `.layout` 缺闭合自动补
2. 跑 `precheck_stage4.py` → SSOT #71 真 DOM div 平衡应 PASS（depth=0）
   - 若 WARN depth≠0 → 多半是 PM 直 Edit outputs/prd 留下不平衡（违反「outputs 走 drafts→assemble 链路」），排查后重生
- **重要提示**：HTML 字面计数**禁用** `grep -c`（数行不数字面）；用 `grep -o '<div' | wc -l` 或 Python `html.parser` 真 DOM 解析

---

### 早期条目（多数下游已同步，简表）

| 日期 | commit | 一句话 | 下游须知 |
|------|--------|--------|---------|
| 2026-06-06 | `ec540e4` | CLAUDE.md /changeRequest vs 调整意见判定对照表 | [FYI] 规范防误读，无产物动作 |
| 2026-06-06 | `98b4495` | assemble 补 sidebar SPEC/SITEMAP 结构重读 | [Should] 重 assemble 让 nav 对齐真源 |
| 2026-06-06 | `a136ddb` | SSOT #30 业务流程图双视图三件套机械兜底（S4-66）| [Should] 重 assemble + precheck 看 S4-66 |
| 2026-06-06 | `4856306`~`555403c` | SSOT #70 业务流程图选型规范 + `check_business_flow_diagrams` | [Should] precheck 看流程图选型 WARN |
| 2026-06-05 | `2d7d4f5` | `sync_from_upstream.sh` 下游主动同步脚本 | [Must] 用此脚本拉上游 L2 |

> 更早历史见 `git log --oneline | grep "L2-only"` + `ssot_anchors.md`。

---

## 维护约定（上游编排器）

`[Should]` 上游每次 **影响下游产物 / 行为** 的 L2 commit（precheck 新增 / assemble 改动 / gen_scaffold schema / template / 规范硬约束）后，在本文件**顶部追加一条**，含：类型 + 一句话 + 下游影响 + **sync 后须知（actionable 整改指引）**。纯内部机制 / 文档措辞改动可省（标 [FYI] 或不记）。详 `pm-workflow/skills/workflow-evolution/SKILL.md` Step 8。
