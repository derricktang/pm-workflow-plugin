# 工作流维护守则

> **本文件定位**：从 `CLAUDE.md` 拆出（原 CLAUDE.md line 813-988，剔除 SSOT 双锚清单部分——后者迁至 `ssot_anchors.md`）。本文件规定 **工作流框架文件本身**（CLAUDE.md / 角色规范 / 模板 / 命令文件 / 兜底脚本 / 索引文件）的维护纪律，针对历史复盘识别的系统性根因（schema 升级双锚漂移、SSOT 缺失、文档承诺与代码漂移、撞自家红线）从规范层面预防同类问题。
>
> **反向引用**：`CLAUDE.md` 顶部「工作流维护守则」段保留指针指向本文件；SSOT 双锚清单单独归档至 `pm-workflow/rules/ssot_anchors.md`。
>
> **维护场景**：编排器在 `workflow-evolution` skill 流程中按本文件「重大升级 / Schema 变更同步检查清单」核查；新对象入库（skill / pub 组件 / proj 组件类型 / agent 类型）按「新对象入库对照清单」核查；模板 / 规范类章节描述按「模板/规范描述粒度原则」执行。

---

### 重大升级 / Schema 变更同步检查清单

`[Must]` 任何 schema / 协议 / 工作流升级（含 v2.0 hard-cutover 类、字段语义变更、流程节奏调整）须显式核查以下次锚是否同步——核查以"清单逐项打钩"形式落实，禁止"应该都改了"式的概略判断：

| 次锚类型 | 核查范围 | 漂移信号 |
|---------|---------|---------|
| 角色规范文件 | `pm-workflow/agents/AI产品经理_Agent.md` / `AI产品主管_Agent.md` 各章节 + §五 自审清单段 | 任务定义改了但自审清单没改、或反向 |
| 模板文件 | `pm-workflow/rules/task_card_template.md` / `proto_*.md` / `tmpl_*.md` 字段说明 + 表头 | 模板中的字段名/格式与 schema 描述不一致 |
| 命令文件 | `.claude/commands/{newRequirement,nextStage,changeRequest,projectStatus,retro}.md` | 命令调度逻辑/状态展示与新流程不符 |
| 兜底校验代码 | `pm-workflow/scripts/{precheck_stage4,gen_scaffold,assemble}.py` | gen_scaffold 校验改了但 precheck 兜底没改、或反向 |
| 双层防御深度 | "主校验失效时是否有第二层兜底" | 单层防御（如 assemble WARN 但 precheck 也沉默）|
| 死代码清理 | 旧版本兼容分支（如向下兼容字符串数组的 else 分支） | hard-cutover 后保留兼容分支让读者怀疑"是否真的硬拒绝" |
| 消费者覆盖矩阵 | 协议/schema/模板文件末段消费者清单（"谁会读取本产物 / 用来做什么"）↔ schema 字段集合 | 消费场景列了但 schema 无对应字段、或新加字段未列消费场景；详见下方「模板/规范描述粒度原则·消费者视角对偶」 |

**配套机制**：升级 PR / commit message 须显式列出已核查的次锚清单（"核查 [角色规范 / 模板 / 命令 / 代码 / 双层防御 / 死代码 / 消费者覆盖] = ✅"），未列出视为升级未完成。

### 模板/规范描述粒度原则

`[Must]` 所有标 `[Must]` 的模板章节、规范条款描述须达到「两个独立 PM 实现得到格式一致产出」的零猜测粒度，最低粒度要求：

1. **必备字段集合**：显式列出该章节须含字段清单（如表格列名、bullet 子项名、必填段标题）
2. **数据结构选择**：明确"必须用表格" / "必须用 markdown bullet" / "必须用段落"，禁止允许多样（如"可表格可列表"）
3. **数值/格式约束**：所有数值（间距 / 字号 / 颜色 / 行数）、token 引用（`var(--fb-*)`）、格式约束（如 `场景：[简短描述]` 命名格式）须显式声明，禁止"灵活掌握" / "酌情" / "适当"等措辞

**判定标准**：若同一章节由两个 PM 按规范实现得到格式不一致的产出 → 规范粒度不足，按本条款补充。

**与既有元规范的关系**：本条款是 `prd_expression_standard.md §零·元规范"零猜测实现粒度"原则` 从视觉规范扩展到所有模板/规范章节描述的通用版（视觉规范保留更细的 CSS 级要求）。

#### 消费者视角对偶（Schema/协议设计必读）

`[Must]` 上述粒度原则保障"两个独立**生产者**实现得到格式一致产出"——属于生产者视角的零猜测。所有 schema / 协议 / 模板章节还须满足**对偶要求**：「**两个独立消费者**拿到产物能提取一致信息」——即消费者视角的零猜测。

**Why**：协议作者天然站在生产者视角思考（"我交付 schema = 完成"），易遗漏下游消费者实际拿到产物后的信息需求。本次 `proj_component_protocol.md` v1.0/v1.1 schema 的"业务语义层缺位"（boundary / usage / interaction 三段缺失）即由此根因导致——工程实现层完备但下游开发拿到 schema 仍需反复回查产品定义 §7。

**How to apply**（schema / 协议 / 模板新建或重大修订时执行）：

1. **列出消费者清单**：在文件末段（如 `§相关文件引用` 或同等位置）显式列出本产物的消费者类型 + 消费场景 + 信息需求，建议表格形式：

   | 消费者类型 | 消费场景 | 期望从产物中提取的信息 | 当前覆盖位置 |
   |-----------|---------|---------------------|-------------|
   | （如：下游开发） | （如：构建组件） | （如：边界 / 状态语义 / 字段约束） | （如：§二.2 boundary 段） |

2. **核查覆盖度**：每条消费场景所需信息须能在 schema 字段中找到落点；任一缺口须**补字段**或**显式豁免**（如"该消费者仅消费 §X 字段，其他无关"），禁止"应该够用了"式概略判断
3. **演进时回查**：协议字段增删时，反向核查消费者清单是否仍完备；新增消费者时，反向核查现有字段是否覆盖其需求

**与「重大升级 / Schema 变更同步检查清单」的关系**：消费者覆盖矩阵是该清单的次锚类型之一（详见前节末行），重大升级须显式核查。

**示范文件**：`pm-workflow/rules/proj_component_protocol.md §十一·消费者清单` 是本原则的最小落地示范。其他既有协议（`proto_contract.md` / `prd_expression_standard.md` / `proto_spec_md.md` 等）**不主动反向回填**，下次自然修订时再补即可。

#### 文档层 ↔ 视觉层对偶（视觉规范设计专用）

`[Must]` 任何在**文档层**（章节文字标识 / 表格枚举 / 标识符命名等）建立的标识体系，规范设计时须**同步核查视觉层是否有对偶表达**——文档层用文字区分（如"手机"/"桌面"/"平板"），视觉层须有对应的可视标识（颜色 / 标签 / 形状 / 位置），否则就是"文档层完备但视觉层失语"的割裂状态。

**Why**：本次 `frame-wrapper` 端口标签缺位（issue 2026-05-06_2319）、上轮 proj 组件三段缺位（issue 2026-05-07_1117）都属同一类盲区——规范作者只在一个维度（文档/工程）思考，遗漏对偶维度（视觉/业务语义）。`proto_contract.md §五` 早就有"平台标签"机制但仅文档文本层，视觉层 frame-type CSS 无可视化端口名标识，直到产生多端并列场景才暴露割裂。

**How to apply**（视觉规范类文件如 `prd_expression_standard.md` / `proto_contract.md` / `proto_cross_platform.md` 新加章节时执行）：

1. **列出文档层标识体系清单**：本章节涉及的文档层标识（如端口标签、状态名、触点编号、角色名、字段名）
2. **核查视觉层对偶表达**：每条标识对应的 PRD 视觉规范是否有可视标识（CSS class / 视觉模板 / DOM 标记），任一缺失须当期补 CSS class + 在 `prd_template.html` 落地，**禁止"先用着、回头补"**——参见前节末「重大升级 / Schema 变更同步检查清单」
3. **显式豁免**：若标识仅文档层有意义（如内部数据字段名 `product_id` / 内部编号 `P-03`），可在规范末段标注豁免理由

**与既有元规范的关系**：

- 「消费者视角对偶」管"产物对消费者的信息覆盖"——产物 schema 字段 ↔ 消费者信息需求
- 本「文档层 ↔ 视觉层对偶」管"同一信息在不同呈现层的对偶覆盖"——文档层标识 ↔ 视觉层可视标识
- 两者同根（设计阶段单视角思考的盲区），不同侧（消费者维度 / 呈现层维度），互相补充

**示范规则**：`prd_expression_standard.md §四 区块 B`「frame-wrapper 端口标签」`[Must]` 规则是本原则的最小落地示范——文档层 `proto_contract.md §五` 平台标签（手机/桌面...）↔ 视觉层 `.frame-platform-tag` CSS（左上角外侧标记）。

### 编排器决策点红线自检清单

`[Must]` CLAUDE.md 增加新派发场景 / 新中断恢复路径 / 新进度结构 / 新整改循环时，强制核对以下既有红线：

1. **派发 prompt 必列项**：方法论 + 参数声明 + 角色规范 + 硬规则 + 必读路径——任何 PM/Supervisor 派发模板缺这 5 项视为"派发模板退化"
2. **中断恢复 SSOT 表完整性**：每个 Step（含整改循环、中段审核等独立计数步骤）都有对应行；编排器中断恢复时按 SSOT 表"找第一个 ⬜ 未开始项"驱动，**不参照** CLAUDE.md 派发顺序文档
3. **进度文件并发约束**：按 `AI产品经理_Agent.md §五·模块进度并发纪律`  SSOT 表执行（PM 写自己子文件 / 编排器单线程勾主文件）
4. **整改场景计数表达**：独立计数（不占用终审 3 次额度）vs 计入终审，须在 prompt + 进度文件结构中明示
5. **双向引用同步**：派发场景 / 路由跳转 / 进度结构涉及 ≥ 2 个文件时，相关文件须双向 link，禁止单向引用

`[Should]` 自检清单核查发现红线撞自家流程时，必须立即修复 + 在 issues 文件留痕，不得"先用着、回头改"。

### 新对象入库对照清单

> **本节双层入库纪律**：①**文件入库**（结构性入库）= 加新 skill / pub 组件 / proj 类型 / agent 类型时按下表核对必备文件齐全 ②**编号入库**（数量性入库，SSOT #60）= 加新 SSOT 锚号 / S-XX / D-XX / G-XX / check_* 等编号时按下方第二段四项 grep 自检。两者并行执行，缺一即视为入库不完整。

#### 第一段：文件入库对照（结构性）

`[Must]` 新加 skill / pub 组件 / proj 组件类型 / agent 类型时，**必须先 Read 同类已有 ≥ 2 个对象的目录结构**，按下表核对必备文件齐全；缺项即视为入库不完整。

| 对象类型 | 必备文件清单 | 检查方式 | 同类参考 |
|---------|-------------|---------|---------|
| **skill**（PM 阶段方法）| `pm-workflow/skills/<name>/SKILL.md` + `template.md` + `examples/sample.md` | `python pm-workflow/scripts/structure_check.py` 或 `ls pm-workflow/skills/<name>/` | jobs-to-be-done / problem-statement / user-story 三件套已对齐 |
| **pub 组件**（跨产品基础组件）| `bujue-design-system/components/<name>.md` 详情 + `pub_components_index.md §三` 总表行登记 + `§五` D1-D5 反查行 + `fb-fallback.css` 实际 selector | `grep <name>` 三处必中 + `precheck check_fb_fallback_sync` | button.md / input.md / card.md |
| **proj 组件类型**（项目内派生）| `outputs/components_<产品>_latest.md §二.1` 索引段 4 张表（A active / B deprecated / C proposed-promote / D 按模块反查）齐全 + `§二.2` 详情段 schema | `precheck check_proj_index` + `check_proj_owner` | 见 `proj_component_protocol.md §二` 完整 schema 模板 |
| **agent 类型**（如新增专项 Agent）| `agents/<name>_Agent.md` + `agent_parameters.md` 矩阵补对应列 + 派发模板路径清单含本 agent | 派发流程 review；`agent_parameters.md` 表格行数 = `agents/` 目录下 .md 数 | AI产品经理_Agent / AI产品主管_Agent |

**执行纪律**：
- **[Must]** 加新对象前 Read ≥ 2 个同类对象做模式对照，**禁止凭记忆模仿**
- **[Must]** 加完执行 `structure_check.py`（若已落地）或手动按上表逐项核查，**禁止"先用着、回头补"**
- **[Should]** 新对象的命名遵循同类已有对象的命名风格（如 skill 一律 `kebab-case`、pub 组件用业务语义命名）

#### 第二段：编号入库对照（数量性，SSOT #60）

`[Must]` 新加 SSOT 锚号 / S-XX 规则 / D-XX 维度 / G-XX 通用规则 / `check_*` 函数 / 规则对照表行时，按下表四维度自检；缺项即视为编号入库不完整（详细 grep 命令 + 自检产出见 `pm-workflow/skills/workflow-evolution/SKILL.md Step 7.4`）。

| 维度 | 自检操作 | 强度 | 防御失败模式 |
|------|---------|------|------------|
| **A. 编号空间冲突自检** | 新编号在全仓 grep 同号；命中既有 → 递增至下一未占用编号；按编号家族判定（如「承继系列 S{N}-X」与「G.5 系列 S{N}-Y」是两个家族，撞号判定按家族 + 编号双键） | `[Must]` | 一物二用（如 S3-06 给两条强度截然不同规则）→ precheck rule_id_map 漂移 + 强度冲突 + 对照表无法收两条 |
| **B. 文档基数同步自检** | 新增 check_/表行/维度 → grep 所有 "N 项" / "N 对" / "N 个维度" 字面同步；基数 = 脚本动态计数（`grep -c "^def check_"` / `awk -F'|' '/^\| [0-9]+ /{c++}END{print c}'`） | `[Must]` | 文档侧基数失修（如 "24 项 vs 49 项" / "36 对 vs 59 对"）→ 机械化覆盖度感知严重偏低 + 新人误读 |
| **C. 对照表 / 维度表同步** | S4-XX → `rule_hard_constraints §六.X` 对照表加行；D-XX → `AI产品主管_Agent.md §4.5` 维度表 + SOP 数字；SSOT → ssot_anchors 5 要素 | `[Should]` | 对照表脱节（如 D-08/D-09 加在表但 SOP 仍写 "D-01~D-07"）→ Sup 严格按 SOP 跑 → 新维度漏审 |
| **D. 动态计数语义替代硬编码** | 基数在 ≥ 3 处冗余 → 改"动态计数（grep 命令）"语义 + 引用唯一权威源；2 处 → 加交叉引用脚注；1 处 → 不动 | `[Should]` | 数字基数多文档冗余 → 任一文档失修就漂移 + 维护成本 N 倍 |

**执行纪律**：
- **[Must]** A + B 二项 grep 自检 → 命中即修复，**禁止"挂账后续"**
- **[Should]** C + D 二项 → 可挂 NB-WE-NN 短期挂账（如动态计数语义改造工作量大）
- **机械兜底现状**：当前文档级四道纪律 + workflow-evolution skill Step 7.4 强制清单；后续 ROI 评估补 `precheck_l2_id_collision.py`（B 组架构债待补）

**为什么把"编号入库"与"文件入库"并列**：本协议原版仅覆盖"加文件齐全度"（结构性入库），未显式覆盖"加编号空间纪律"（数量性入库）。L2 矛盾审计实证：批次落盘场景（同一 SSOT 锚号 ≥ 2 commit）下编号撞号 + 基数失修是高频系统性盲区，**必须把"编号入库"提升到与"文件入库"对等的纪律层级**，二者协同形成 L2 演化的完整入库纪律。

### 机械兜底必要性 ROI 决策标准

`[Must]` 发现某个文档级硬规则（如 `rule_hard_constraints.md` G-XX / S-XX）存在漂移点时,**先派 Explore 排查全工作流漂移面**,再按下表 ROI 评估是否值得加机械兜底（precheck / 测试 / SSOT 同步）;低 ROI 项保留人工兜底,**禁止"既然是 [MUST] 就必须机械化"的盲目机械化**。

| 判据 | 说明 | 评分 |
|------|------|------|
| **漂移代价高** | 漂移会导致下游 Agent 失败 / 业务方误读 / 难回滚 | 1 |
| **历史踩坑 ≥ 2 次** | 实战触发 ≥ 2 次（commit 历史可查） | 1 |
| **漂移频率高** | 每月 ≥ 1 次（按 commit 频率估）| 1 |
| **范围扫描结果** ≥ 2 处当前漂移 | Explore 派出后报告非"零漂移" | 1 |

**决策规则**：
- **得分 ≥ 2** → 加机械兜底（precheck check 函数 + 测试 ≥ 3 用例 + SSOT #N 派生字段同步）
- **得分 = 1** → WARN 级软兜底（不阻断流程,提示 PM/Supervisor 关注）
- **得分 = 0** → 保留人工兜底（不加 precheck）;在 SSOT 双锚清单 / `rule_hard_constraints` 元 SSOT 对照表中显式标"—（人工兜底）+ 理由"

**典型案例**（沉淀历史决策）：

| 规则 | 漂移代价 | 历史踩坑 | 频率 | 当前漂移 | 总分 | 决策 |
|------|--------|---------|------|--------|------|------|
| SSOT #14 状态命名（NB-WE-13）| 高（UI Agent 失败）| 2 次（bujue 实战）| 中 | 0 | 3 | ✅ 加机械兜底（commit a7e3788）|
| SSOT #4 PRD CSS sync（NB-WE-09）| 中 | 9 处历史漂移 | 中 | 9 | 3 | ✅ 加 check_css_sync.py |
| G-02 变更日志 6 列（2026-05-09）| 低（仅文档审计）| 1 次（tmpl_产品定义）| 极低 | 0（已修复后扫描）| 0 | ⚪ 保留人工兜底（Supervisor 审核已含）|

`[Must]` 决策完成后,在 commit message 中**显式记录评分与决策**（如 `ROI 评分 0/4,保留人工兜底`）,便于后续追溯。

`[Should]` 已保留人工兜底的项,周期性（每 3 个月）复评:若期间踩坑 ≥ 2 次或漂移频率上升,重新评估升级到机械兜底。

### `[Should]` 机械兜底覆盖度 8 维度自检（2026-06-02 治"兜底盲区高频踩"根因）

设计 precheck / hook / regex 兜底前必跑下方 8 维度自检（命中任一维度 → 评估是否需扩展覆盖）：

| # | 维度 | 实证根因 | 治本建议 |
|---|------|---------|--------|
| 1 | **边界条件**（单帧/空 changelog/0 元素）| precheck check_frame_platform_tag 单帧静默跳过（issues #12 / SNB-005）| 边界路径显式 FAIL / WARN，不静默跳过 |
| 2 | **untracked 文件覆盖** | pre-commit hook 仅扫 staged，untracked outputs/scaffold 0 命中（issues #15 / SNB-009）| 加 mtime/sha 基线 sidecar |
| 3 | **多源对账**（spec vs prd / scaffold vs json）| SPEC_FOOTER 硬编码 vs build_changelog_page 消费 scaffold.json 二模板源不一致（issues #41）| 同源消费 + parity check |
| 4 | **版本号合规**（SSOT #48 SemVer）| quotation-tool scaffold.json["changelog"] 9 条 v1.0-v2.0 违规历史散文（issues #42）| 升 fallback + precheck 拦截 |
| 5 | **静态 vs 运行时**（mermaid SVG getBBox / cytoscape #cy）| 静态 HTML 查不到运行时动态注入 DOM（issues #40 #cy）| 调用方兜底 CSS / JS |
| 6 | **模板纯净度**（precheck_template_purity 6 文件白名单）| 模板注释带 YYYY-MM-DD / NB / issue / retro 运维痕迹（CLAUDE.md 顶部 setup hook 警告）| 模板 6 文件白名单机械拦截 |
| 7 | **SNB-007 同型污染**（PM 自审报告误写真源）| _strip_pm_selfreview 仅扫 drafts 不扫 outputs/spec（issues #41 私域 spec L8）| 扩展扫真源 + 精确剥段 |
| 8 | **编号空间冲突**（SSOT #60 SOP A 维度）| S3-06 编号一物二用（issues #19）| grep 同号 + 编号家族判定 |

**违反信号**：本会话 issues #12/#15/#16/#41/#42 多次踩盲区，事后才补单点防御；本 8 维度清单可在设计阶段一次性覆盖。

---

## 通用 L2 注释纯净度准则（总纲）

`[Must]` 所有 L2 真源文件（`pm-workflow/*` + `CLAUDE.md` + `.claude/commands/*`）的注释 / 说明文字**只描述规则**（当前是什么 + 为什么这样写），**不描述运维史**（什么时候为什么改成现在这样 / issue / NB / retro 引用 / TODO / commit hash 跨文件引用）。

### 核心精神

| ✅ 应描述（规则） | ❌ 不应描述（运维史） |
|---------------|-------------------|
| 规则是什么（当前约束 / 默认值 / 适用场景）| 何时为何改成现在这样（日期 / issue 编号 / NB-WE-X / retro 引用 / 复盘根因）|
| 为什么这样写（设计意图 / 跨文件 SSOT 关系）| 历史诊断笔记（"某 issue 真根因 = ..."）|
| 怎样使用（调用约定 / 边界场景）| 跨文件 commit hash 引用（如 `dc8f582 既有 :where() 集合`）|
| 反例 / 正例（教学价值）| 待办 TODO（"待后续评估加 .fb-bottom-bar"）|

### 二元分类：代码类 vs 规范类

L2 文件按"是否参与 outputs 渲染"分两类，严格度不同：

| 分类 | 严格度 | 适用文件 | 兜底 |
|------|--------|---------|------|
| **代码类**（[Must] 严格）| 注释**绝不**含运维痕迹 | 5 模板（PM fork 起点）+ pub 库 CSS / HTML 真源（`fb-fallback.css` / `prd_template.html` — 注入到 outputs） | 机械兜底 `precheck_template_purity.py` 6 文件白名单 + pre-commit hook FAIL |
| **规范类**（[Should] 宽松）| 允许"来源历史"字面作为 SSOT 5 要素合法补充 | `ssot_anchors.md` 双锚清单 + `rule_hard_constraints.md` S/G 规则 + `proj_component_protocol.md` 等 — PM 读但不复制 | 人工自审 + 编排器 sync 时核查 |

**代码类与规范类边界 grep**：文件是否会被 `assemble.py` / `gen_scaffold.py` / PM 复制粘贴到 outputs / process_record/tasks → 是即代码类，否即规范类。

### 归档去处（运维史合法位置）

运维痕迹**应**在以下位置而非 L2 真源：

| 信息类型 | 归档去处 |
|---------|---------|
| 时间戳 / 修复时机 | git log + git blame |
| issue / NB / retro 编号 | `process_record/issues/*_analyzed.md` + `process_record/progress/*.md` |
| commit hash 跨文件引用 | git log（不需要在代码注释中固化）|
| TODO / 待评估 | NB-WE 挂账（含产品级 + L2 级）|
| 修复诊断笔记 | commit message + `process_record/issues/` 复盘段 |

### `[Must]` PM 改 L2 边界重申（SSOT #31）

**理论上 PM 不允许直改 L2 文件**——按 `agent_dispatch_protocol.md §6 第 6 条 PM L2 修订诉求 NB 上报 SOP`，PM 在 L1 任务期间发现 L2 缺陷**只能 NB 上报**，由编排器走 `workflow-evolution` skill 实施。

**实际近期暴露的模式**（本会话连续 3 轮）：PM 在下游 L1 仓库直改 L2 文件 + 把诊断笔记 / TODO / issue 编号沉淀进真源 — 编排器 sync 时需**双重清理**：①规则改动本身的合理性 ②清理 PM 误加的运维痕迹（按本节准则）。

**编排器 sync 拒绝边界**：
- 下游 L2 改动经核查技术合理 → 同步进上游前**必须**先清运维痕迹
- 清理范围按二元分类：代码类清干净（[Must]）/ 规范类保留"来源历史"但**不留** TODO 和 commit hash 跨文件引用
- 清理后 pre-commit hook 对代码类自动兜底（precheck_template_purity 6 文件白名单）

### 与既有规则关系

- §「模板纯净度红线」是本总纲在 5 模板 + 1 CSS 上的**机械化落地**（6 文件白名单 + precheck）
- §「Shell hook 脚本边界规则」是本总纲在 hook 脚本上的**特定子集**（脚本边界 + 实测）
- §「机械兜底反向真源解析准则」是本总纲在 precheck 硬编码字典上的**特定子集**

未来发现新文件类别 / 注释边界场景 → 优先归入二元分类，再决定是否升级机械兜底。

---

## 模板纯净度红线（防止整改原因注释污染 outputs）

`[Must]` **背景**：阶段 4 PM fork `prd_template.html` 生成 `outputs/prd_*.html` 时,模板中含"整改原因注释"（日期 / issue / NB / retro 引用 / 复盘根因 / 建议 N 落地 等运维痕迹）会**连带复制进产品交付物**,污染产品总监看到的 PRD。维护历史的真源是 git log + `process_record/issues/*_analyzed.md`,不应污染下游 outputs。

### 适用范围（6 个「代码类」文件）

| 文件 | 流向 outputs |
|------|------------|
| `pm-workflow/rules/prd_template.html` | PM fork → `outputs/prd_*.html` |
| `pm-workflow/rules/tmpl_需求分析.md` | PM 复制结构 → `outputs/需求分析_*_latest.md` |
| `pm-workflow/rules/tmpl_功能规划.md` | PM 复制结构 → `outputs/功能规划_*_latest.md` |
| `pm-workflow/rules/tmpl_产品定义.md` | PM 复制结构 → `outputs/产品定义_*_latest.md` |
| `pm-workflow/rules/task_card_template.md` | gen_scaffold 复制 → `process_record/tasks/task_M*_*.md` |
| `pm-workflow/rules/bujue-design-system/fb-fallback.css` | assemble.py 注入 → `outputs/prd_*.html` `<style>` 顶部 |

### 三条红线（`[Must]` 维护时必守）

> **适用范围澄清**（2026-05-31 L2 矛盾审计 #32 显式化）：本节三条红线**仅对 6 文件白名单生效**（5 模板 + fb-fallback.css，详 §机械兜底段）。**`process_record/issues/YYYY-MM-DD_HHMM.md` / `process_record/progress/*.md` / `process_record/issues/*_analyzed.md` 等运维归档目录的 YYYY-MM-DD 是合规命名**（运维痕迹的归档位置不受本红线约束，反而是 §模板文件中"禁止运维痕迹"的对偶——禁出现在交付物模板里，但必须落到运维归档里）。

**红线 1：禁止运维痕迹字面**

模板文件中**禁止**出现以下字面（无论注释 / 表格 / 说明文字）：
- 日期字面：`YYYY-MM-DD` / `YYYY-MM-DD_HHMM`（模板占位 `[YYYY-MM-DD]` 豁免）
- issue 引用：`issue # N` / `issue YYYY-MM-DD_NNNN`
- NB 编号：`NB-WE-NN` / `NB-阶段X-Y`
- /retro 引用：`/retro YYYY-MM-DD`
- 复盘语义：`复盘根因`
- 建议编号：`建议 N 落地` / `建议 N 配套` / `建议 N 预防侧`

**红线 2：注释只描述语义，不描述运维史**

- ✅ 正例：`/* 5 frame 启用 flex column,让底部 sticky panel 贴 frame 底部 */`
- ❌ 反例：`/* 2026-05-13 修复:5 frame 启用 flex column... (NB-WE-25 落地) */`

注释回答"规则是什么 / 为什么这样写"（语义），不回答"什么时候为什么改成现在这样"（运维史）。

**红线 3：维护历史归档去处**

- 时间戳 / 修复时机 → git log + git blame
- issue / NB / retro 编号 → `process_record/issues/*_analyzed.md` + `process_record/progress/*.md`
- 建议编号 → `process_record/issues/` 中对应复盘段
- 模板内**只**保留对未来读者有用的语义

### 机械兜底

`[Must]` `pm-workflow/scripts/precheck_template_purity.py`：扫 6 文件白名单（5 模板 + 1 兜底 CSS — `prd_template.html` + 3 个 `tmpl_*.md` + `task_card_template.md` + `fb-fallback.css`；2026-05-31 L2 矛盾审计 #6 修复，原文"5 个模板"基数与上方表格 6 行 + L157/L183/L187 描述统一为"6 文件白名单"）+ 检测红线 1 字面 + 白名单豁免（模板占位 `[YYYY-MM-DD]` / 版本号 `vN.N` / 行含 `.md` 路径引用且无修复动词）+ 集成到 `git pre-commit hook` 硬拦截。

- 命令：`python3 pm-workflow/scripts/precheck_template_purity.py`
- PASS：退出码 0 / FAIL：退出码 1 + 命中行号 + 字面
- 集成：`pm-workflow/scripts/hooks/pre-commit` 调用本脚本，命中 FAIL 则阻止 commit

### Skill 流程联动

`workflow-evolution/template.md` Step 7 SSOT 同步检查清单第 8 项「模板纯净度复检」— 改 L2 模板时人工核查（与机械兜底双道防御）。

### Why 这是 `[Must]` 而非 `[Should]`

- **每次产品交付都触发污染**：PRD 模板被复制到 outputs/ 是阶段 4 必经路径，污染面 100%
- **机械化成本极低**：~120 行脚本 + < 0.1s 运行 + 0 false positive（已实测）
- **维护历史 0 损失**：归档去处（git log + issues/）完整保留追溯链

---

## 机械兜底反向真源解析准则

`[Should]` 所有 precheck 函数中的「合法集合 / 枚举字面 / 期望表头 / 期望列字面」等**字面字典**，**应**附加 `_parse_X_truth_source()` 运行时反向 grep 真源对照逻辑，本地字典 vs 真源差异 → `r.warn` 漂移信号。

### 背景

历史上多次发生「真源升级 → precheck 硬编码字典漂移」事故（最严重的一次：`§零.1` 表新增 Z-150 / Z-41 后 `precheck_stage4.legal_set` 仍按旧 7 值集合校验，下游 PM 报假阳性 FAIL 反而想去改本来合规的 css）。根因是 precheck 函数把"合法集合"硬编码为 Python 字面字典，与真源文档双源化。

### 已有先例（实战证明）

`precheck_stage4.check_z_index_compliance` 顶部加 `_parse_z_index_truth_source()` 运行时反向 grep `prd_expression_standard.md §零.1` 表 `^\| Z-(\d+) \|` + §零.2 `Z-(\d+) drawer 内容` 41 协议得真源集合 + `_check_z_index_legal_set_drift()` 与本地 `legal_set` 双向对账，差异 → `r.warn` 派生漂移信号 — 已根除"真源升级 PM 漏改 precheck"硬编码漂移面。

### 通用适用场景

| 类别 | 当前实现 | 建议升级（反向解析） |
|------|---------|-------------------|
| z-index 数值集合 | `legal_set = {200, 150, ...}` | ✅ 已落地（参 `check_z_index_compliance`）|
| `SHEET_EVASION_KEYWORDS = ("sheet", "popup", ...)` | 硬编码 tuple | 反向 grep `prd_expression_standard.md §零.2 反例禁令` 段中"`.sheet`/`.bottom-sheet`/..." 字面 |
| `CHANGELOG_EXPECTED_HEADERS = {...}` | 硬编码 dict | 反向 grep `prd_expression_standard.md §11.1` thead 字面 |
| `CHANGELOG_FORBIDDEN_HEADERS = {...}` | 硬编码 dict | 反向 grep `rule_hard_constraints.md S4-26` 禁用字面表 |
| `FRAME_CONTAINER_CLASSES = [".phone-frame", ...]` | 硬编码 list | 反向 grep `prd_expression_standard.md §零.2 支柱 1.b` 中 frame 类列举 |
| proj_gaps trigger 枚举 `{A-D1..A-D5, B-D1..B-D5}` | `gen_scaffold.validate_v2_schema` 硬编码 | 反向 grep `proj_component_protocol.md §一` 双触发表 |
| 角色名清单 | `precheck_common.extract_role_table` 已实装 | ✅ 已落地 |

### `[Should]` 不是 `[Must]` 的理由

- **复杂度成本**：每个反向解析逻辑 ~20-40 行 + 需写正则匹配真源表 + 边界场景测试
- **真源稳定性差异**：z-index 数值集合升级频率高（已发生过 3 次漂移）→ 必加反向解析；某些 trigger 枚举升级频率极低 → 硬编码 ROI 可接受
- **落地策略**：按 ROI 排序（升级频率高 + 漂移代价高的优先），允许部分场景**保留硬编码**但**必须**注明"为何不加反向解析"的判断（如"本枚举 5 年未变更，反向解析 ROI 低"）

### 落地优先级

`[Recommended]` 按以下 ROI 优先级补全（B 组架构债）：

1. **高优**：`SHEET_EVASION_KEYWORDS` 反向解析（与 `prd_expression_standard.md §零.2 反例禁令` 同步）— 与 #2 双锚关联
2. **高优**：`CHANGELOG_EXPECTED_HEADERS` / `CHANGELOG_FORBIDDEN_HEADERS` 反向解析（与 `S4-26` rule_hard 表同步）— 与 #22 元 SSOT 关联
3. **中优**：`FRAME_CONTAINER_CLASSES` 反向解析（5 个 frame 类清单可能扩展）
4. **低优**：proj_gaps trigger 枚举（升级频率低，硬编码可接受）

### 配套机械化（可选，下迭代）

`[Optional]` 新增 `pm-workflow/scripts/check_hardcoded_drift.py` 扫所有 precheck 函数中是否含未加反向解析的"集合/枚举/期望表头"字面字典，FAIL 报告"X 个字典缺反向解析，对应 SSOT 真源 Y"。

---

## Shell hook 脚本边界规则

`[Should]` 所有 git hook 脚本（`pm-workflow/scripts/hooks/*`）设 `set -o pipefail` 时，**必须**遵守以下 2 条边界规则，否则正常分支会被误判为 pipeline 失败，触发 `set -e` 阻断 commit。

### 背景

`pm-workflow/scripts/hooks/pre-commit` 在 2026-05-13 落地「SOP 偏离 WARN」段（/retro 共性根因 5 防御建议 E）后，先后暴露 2 个独立 bug：

| commit | bug | 触发场景 |
|--------|-----|---------|
| `7098bb2` 修复前 | `head -5` 截断关闭 stdin → `grep \| head -5` SIGPIPE (exit 141) → `set -o pipefail` 阻断 → 误阻 commit | 触发 SOP 段时（≥ 3 L2 文件 commit）|
| `4042684` 修复前 | `grep -c` 无匹配输出 "0" + exit 1 → `\|\| echo 0` 兜底叠加输出 → `$()` 捕获 "0\n0" → 整数比较报 `integer expression expected` → `set -e` 阻断 | commit **不含**任何 L2 文件时（纯 L1 outputs/ 改动） |

两个 bug 都是"正常场景"被 `set -o pipefail` + 边界写法误判，暴露了"hook 脚本边界条件容易遗漏"的共性。本节沉淀 2 条规则防再次发生。

### 规则 1：截断 pipeline 必须包 `|| true` 兜底 SIGPIPE

任何含 `head` / `tail` 截断的 pipeline，**必须**用 `{ ... } || true` 包裹兜底 SIGPIPE：

```bash
# ❌ 错误：head 截断关闭 stdin → 前序 grep/sed 写失败 SIGPIPE → pipefail 阻断
echo "$staged_files" | grep -E "$PATTERN" | head -5 | sed 's/^/  /'

# ✅ 正确：整个 pipeline 包 || true 兜底 141
{ echo "$staged_files" | grep -E "$PATTERN" | head -5 | sed 's/^/  /'; } || true
```

**原理**：`head -5` 读完 5 行后关闭 stdin，上游 `grep` 继续写时收到 SIGPIPE（141）→ `set -o pipefail` 把 pipeline 退出码标为 141 → `set -e` 触发 errexit 阻断。`{ ... } || true` 让 pipeline 失败被兜底，整体退出码归 0。

### 规则 2：失败 grep 兜底必须用 `|| true` + `:-X` 模式

**禁用** `cmd || echo X` 兜底失败 grep 的写法（cmd 失败**前**已写 stdout 会与 echo 兜底输出**叠加**）；**改用** `cmd || true` + `${var:-X}` 兜底空值：

```bash
# ❌ 错误：grep -c 无匹配时输出 "0" + exit 1 → 触发 || → echo 0 追加输出 "0"
#         → $() 捕获 = "0\n0" → 整数比较失败 "integer expression expected"
count=$(echo "$input" | grep -cE "$PATTERN" 2>/dev/null || echo 0)
if [ "$count" -ge 3 ]; then ...  # 报错!

# ✅ 正确：|| true 不产生 stdout,捕获仅来自 grep("0"),${:-0} 兜底空字符串
count=$(echo "$input" | grep -cE "$PATTERN" 2>/dev/null || true)
count=${count:-0}
if [ "$count" -ge 3 ]; then ...  # 正常
```

**原理**：`grep` 失败前 stdout 已写入（如 `grep -c` 无匹配仍写 "0"），`|| echo X` 中的 echo 不替换前序输出而是追加，导致 `$()` 捕获叠加。`|| true` 不产生 stdout，配 `${var:-X}` 兜底变量真为空的边界（虽然 `grep -c` 几乎不会输出空，但 `set -u` 严格模式下保险）。

### 推广到所有 hook 脚本

`[Must]` 新增 / 修改 `pm-workflow/scripts/hooks/*` 时，**必须**：

1. 跑 `bash <hook_file> 2>&1; echo "exit: $?"` 手动验证 hook 在 **2 个场景**下 exit 0：
   - 含 staged 文件场景（典型场景）
   - 无 staged 文件场景（边界）
2. **特别验证** SOP 偏离段 / 类似 grep 计数段在 **3 个场景**下 exit 0：
   - L2 ≥ 3 文件（触发 WARN 段）
   - L2 < 3 文件（不触发但有匹配）
   - L2 = 0 文件（不触发且无匹配，最容易触发 grep -c 双输出 bug）

### 配套机械化（可选，下迭代）

`[Optional]` 新增 `pm-workflow/scripts/tests/test_hooks.sh` 用上述 3 + 2 = 5 个场景实测 `pre-commit` 退出码，CI 跑通；任何 hook 改动均须该测试 PASS 才能 commit。

---

## 新增 precheck 规则上线前 dry-run 纪律（NB-LIT-25-B B.2 v1 失败教训）

> **背景**：2026-05-15 S4-28 v1 落地 + 同日下线。v1 启发式（`flex + button + lastChild`）在上游 /tmp 原型只命中 1 处 false positive，被判定"严格判定可上线"；落地下游 quotation-tool 真实 PRD 后**暴增到 5/5 false positive**，PM 被 WARN 误导加 5 处 inline sticky 污染产物。**根因**：上游测试样本规模 / 多样性不足，启发式特征在生产规模下不收敛。

### `[Must]` 新增 / 修订 precheck 规则上线前的 dry-run 纪律

任何新增或大改既有 `check_*` 函数（含逻辑重写 / 启发式调整 / 阈值变更）的 commit **必须**满足以下前置条件，否则**禁止** commit 上线：

1. **`[Must]` 在 ≥ 2 个真实下游产物上跑过新规则**
   - 候选下游：`bujue-quotation-tool` / `bujue-business-circle` / `private-domain-homepage-module`
   - 至少**覆盖 2 个**（不能只测自己 /tmp 原型 + 1 个下游 — 启发式失效场景常需 ≥ 2 个 PRD 对照才暴露）
   - 命中数据 / 实战命中行号 / WARN 文本写入 commit message 或附在 NB 描述

2. **`[Must]` 人工核查 ≥ 1 个命中样本是否真违规**
   - 不是看"命中数对不对"，是开 PRD HTML / spec.md 打开命中行号附近 30 行**人眼判断**
   - 至少抽查 1 个，判定结果（真违规 / false positive / 误判根因）写入 commit message
   - 抽查样本量与命中总数挂钩：命中 ≤ 5 → 全部核查；命中 > 5 → 抽 3 个（首 / 中 / 末）

3. **`[Should]` false positive 率高于阈值时禁止上线**
   - 阈值：抽查样本 false positive 率 ≥ 30%（如抽 3 个有 1 个 false positive）→ 设计回炉
   - 阈值：抽查全部 false positive（如 5 个抽全部错）→ 立即放弃当前思路，重新设计真源（参 §S4-28 v1 启发式 vs 真源匹配 对话讨论）

4. **`[Should]` 启发式特征空间评估前置**
   - 上线前先用一句话回答：「本规则的特征（如 flex+button）在多少种 DOM 形态下成立？」
   - 若答案 > 1 种且其中 ≥ 1 种是"非目标场景"（如主体容器、全屏 section、toolbar 也用 flex）→ 启发式不可靠，改真源匹配
   - 若特征空间无法穷举（如"按钮密集区域"）→ 启发式不可靠

### Why 这是 `[Must]` 而非 `[Should]`

- **失败成本**：v1 启发式失效 ≠ 规则不命中，而是 **WARN 误导 PM 改坏 L1 产物**。本会话先例：S4-28 v1 → PM 加 5 处 inline sticky 污染主体容器 + 全屏 section
- **不收敛**：启发式补排除条件越加越复杂，本质是不收敛（典型决策树过拟合）；上游原型测试规模放大不出来，必须在生产规模 PRD 上验证
- **成本对称**：dry-run 在下游跑 1 次 precheck（< 1 min）+ 人眼核查 1 个样本（5 min）= 6 min 成本；下线 + 复盘 + 通知下游回滚污染产物 = 数倍时间 + token 浪费

### 实战先例

| 时间 | 规则 | 上游测试 | 下游实战 | 结果 |
|------|------|---------|---------|------|
| 2026-05-15 | S4-28 v1 desktop sticky 完整性 | /tmp 原型命中 1 处 false positive，主观判定可上线 | 下游 PRD 命中 5 处，**5/5 全 false positive** | **同日下线**，PM 已加 5 处污染需回滚 |

> 上述先例直接催生本规则。

### 配套机械化（可选，下迭代）

`[Optional]` 新增 `pm-workflow/scripts/tests/test_new_check_dry_run.sh`：
- 检测当前 commit 是否新增 / 改既有 `check_*` 函数（git diff）
- 若是 → 强制要求 commit message 含 "dry-run:" 段落 + "人工核查:" 段落
- 否则 pre-commit hook 拒绝 commit

`[Recommended]` 短期内由编排器在 `workflow-evolution` skill Step 6（机械自检）通过本节自查清单兜底，不立即建机械化脚本。

### Skill 流程联动

`workflow-evolution` skill Step 6 自查清单已隐式覆盖（机械自检通过 + 自审产出"实战命中数据"）。本节为该 Step 显式补充清单：

- [ ] 是否新增 / 大改 `check_*` 函数?
- [ ] 是 → 在 ≥ 2 个真实下游产物 dry-run 命中数据已附 commit message?
- [ ] 是 → 人工核查 ≥ 1 个命中样本结果已附 commit message?
- [ ] false positive 率 ≥ 30%? 是 → 设计回炉禁止上线
- [ ] 启发式特征空间穷举完成? 否 → 改真源匹配

---

## L2 sync 后 L1 影响主动评估 SOP

`[Must]` L2 commit（编排器 sync 上游 或 workflow-evolution skill 改 L2）含**规则升级 / schema 变更 / SemVer 化 / 新规则约束 / SSOT 新增 / 模板升级**类关键词时，编排器**必须主动评估 L1 影响**——禁被动等产品总监 / 下游 PM 主动发现（已 ≥ 3 次踩坑——issue # 1 阶段 3 模板升级未检测 / issue # 6 §三.3.3 表列升级遗漏 / NB-WE-#1-R-002 quotation-tool 2 处 inline 未联动整改 / issue#2 v1.x 取消后 L1 残留靠产品总监主动发现——已触发硬兜底阈值）。

**SOP 核心步骤 + 三场景分发**：

1. **识别本次 L2 改动影响域**（`git show --name-only HEAD` + 看 commit message 关键词）

2. **派 Explore subagent 扫 L1 影响范围**（参 `agent_dispatch_protocol.md` §调研 7 要素，含 5.2 大文件 anchor 清单）：遍历 `outputs/*_latest.md` + `outputs/prd_*_latest.html` + `outputs/components_*_latest.md` + `process_record/drafts/`；对照新 L2 规范逐项 diff（章节 / 字段 / SSOT 派生 / class 字面 / inline workaround 等）

3. **按影响规模三场景分发**：

   | 场景 | 触发条件 | 落地载体 | 处理方式 |
   |------|---------|---------|---------|
   | **A 机械改动** | 影响 ≤ 3 处 + 改动机械（如版本号字面替换 / inline 改 class）| commit message 标注 + 立即派 PM Agent 闭环 | 后续 commit message 标 `[L1] L2-sync 派生 — <commit_short> 升级落盘` + 派 PM 在受影响仓内执行 |
   | **B 需 PM 判断** | 影响 ≥ 4 处 / 需 PM 判断 | `process_record/progress/stage[N]_[产品名]_l2sync_[commit_short]_plan.md` | 进度文件含「受影响清单 + 整改计划 + 完成标记」+ 派 PM 按 plan 执行；**`[Must]` 禁挂账 state.md「开放问题」段**（语义冲突——该段承载产品决策悬挂，非技术评估任务）|
   | **C 跨阶段 / 业务语义** | 触及业务定义（如 SemVer 规则影响多模块）| 主动询问产品总监走 `/changeRequest` | 编排器明示影响域 + 候选方案让产品总监决策；走 changeRequest 后按其 §一~§八 闭环 |

4. **`[Must]` 禁追加 issues/**（语义边界与 CLAUDE.md「调整意见自动记录规则」一致）：`issues/` 仅承载**产品总监对成果文件的修改意见 / 审阅反馈**。L2 sync 派生跟进任务、PM/Sup 自循环整改、precheck FAIL 整改 **一律不入 issues/**——三类各自载体：L2 sync 派生 → `progress/stage[N]_[产品名]_l2sync_*` / PM 自循环 → `progress/stage[N]_*_plan.md` / precheck FAIL → `reviews/` + `progress/`

5. **commit message 记决策链**：`L2 sync L1 影响评估：场景 A/B/C，N 项 [立即整改 / 挂 progress 待派发 / 询问 /changeRequest]，受影响仓 [仓名清单]`

---

### Diff 比对维度参考（主 SOP 步骤 2 的 Explore prompt 内容）

派 Explore 时 prompt 应含以下 diff 维度（避免重复在主 SOP 中展开）：

1. **章节结构**：`## XX` 标题集合是否完整（对照新 tmpl_*.md）
2. **必填字段 / 必填表头 / 子段**是否齐全
3. **SSOT 派生约束**：`agent_dispatch_protocol.md` 派生表 + `ssot_anchors.md` 双锚清单是否符合
4. **Tier 2 修订段**：模板中标 `[Must]` 的固定子段是否存在
5. **inline workaround**：扫 `outputs/prd_*.html` / `process_record/drafts/` 是否含违反新规则的 inline style 覆盖（如 dd19ac6 后扫 `style="right:0;left:auto"` → 改 `class="fb-dropdown-right"`）
6. **class 字面**：扫 PRD 使用的 `fb-*` class 是否在新规则下需调整（同族对称化等）

### ROI 决策演进档案

- **2026-05-08**：初次记账 `[Recommended]` 软兜底，2 次踩坑（issue # 1 / # 6）
- **2026-05-28**：4 次踩坑触发阈值（含 NB-WE-#1-R-002 quotation-tool inline 联动遗漏 + issue#2 v1.x 取消后 L1 残留靠产品总监主动发现），从 `[Recommended]` 升 `[Must]`
- **机械兜底偿还触发**：未来若 ≥ 5 次跳过 [Must] SOP → 升级机械兜底（新建 `pm-workflow/scripts/post_l2_sync_drift_scan.py`）

---

## L2 模板多端 frame CSS 覆盖度维护(建议 8 / issue # 11 / # 16 复盘根因 H)

`[Must]` 任何修改 `pm-workflow/rules/prd_template.html` 中 `.X-frame` CSS 块的 commit,**必须**在 commit 前跑一次 `lint_template_frame_coverage.py` 验证覆盖度:

```bash
python3 pm-workflow/scripts/lint_template_frame_coverage.py
```

退出码 0 才允许 commit。脚本会校验:
- 多端枚举(phone / desktop / h5 / tablet / miniprogram)的 `.X-frame` CSS 是否齐全
- 已定义的 frame 是否含 5 个关键属性(`position: relative` / `width` / `min-height` / `overflow` / `flex-shrink`)

**触发节点**:
- 修改 `prd_template.html` `.X-frame` 块时
- 修改 `proto_platform_*.md` 端类规范(新增/删除端类时同步更新 lint 脚本 `EXPECTED_FRAMES` dict)
- `workflow-evolution` skill Step 7 SSOT 同步检查时

**与 SSOT 双锚的关系**:
- 真源:`pm-workflow/rules/prd_template.html` `.X-frame` 块
- 派生:`pm-workflow/rules/proto_platform_*.md` 端类规范引用 frame class
- 调整方向:先改模板真源(增加新端 frame CSS 含 5 关键属性)、再同步 proto_platform 描述、最后 lint 脚本验证;**禁止反向**(先改规范再补真源会让 lint FAIL)
