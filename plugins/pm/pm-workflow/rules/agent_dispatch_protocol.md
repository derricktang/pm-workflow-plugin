# Agent 调用规范

> **本文件定位**：从 `CLAUDE.md` 拆出，集中承载 L1/L2 派发路径决策、PM/Supervisor 派发 prompt 模板、阶段 4 模块化派发 7 步流程、scaffold v2.0 schema、整改回退决策表等高密度规范内容（原 CLAUDE.md line 227-812）。
>
> **反向引用**：`CLAUDE.md` § Agent 调用规范段保留 L1/L2 二元判定表精简版 + 指针指向本文件；详细规范以本文件为权威源（SSOT 真源）。
>
> **派发场景适用**：编排器派发 PM Agent / Supervisor Agent 时按本文件第 X 段构造 prompt 路径清单 + 注明段；PM 在 L1 业务任务期间发现 L2 缺陷时按本文件「PM L2 修订诉求 NB 上报标准 SOP」上报。

---

### 派发路径选择（L1 派 Agent vs L2 走 Skill）

`[Must]` 编排器收到任务后，**按修改文件归属 L1/L2 二元判定路径**：

| 修改文件归属 | 路径 |
|-------------|------|
| **L2 文件**（任一）：`pm-workflow/agents/*` / `pm-workflow/rules/*` / `pm-workflow/scripts/*` / `pm-workflow/skills/*` / `CLAUDE.md` / `agent_methodology.md`（属 `pm-workflow/rules/`，单列强调）/ `agent_parameters.md`（属 `pm-workflow/rules/`，单列强调）/ `.claude/commands/*` | **走 `workflow-evolution` skill**（编排器直做）|
| **L1 文件**：`outputs/`（PRD/spec/阶段产物）/ `process_record/state.md` / `process_record/tasks/` | 派 PM Agent + Supervisor Agent |
| **混合任务** | L2 部分走 skill / L1 部分派 Agent（拆分执行）|

**L1 vs L2 本质判定**：
- 产品需求方驱动 + 产出 PRD/spec/阶段产物 → **L1**（消费者：真实业务方）
- 工作流维护者驱动 + 产出元规范/校验脚本/SSOT 双锚/测试基础设施 → **L2**（消费者：工作流维护者 + 编排器）

**为什么 L1/L2 二元判定**（取代旧多维阈值）：
- 客观：文件路径判定无主观空间，避免"超不超阈值"争论
- 编排器主对话天然持有 L2 上下文，派 PM Agent 重 Read 同样规范是浪费
- 责任清晰：L2 工作流维护是编排器的固有职责（PM/Supervisor 仅参与 L1 业务）；L2 质量保障由 SKILL.md §L2 三道质量门负责（机械检查 + 编排器自审 + 人类审 diff）

**大型 L2 任务**（> 200K token / > 5 文件 / 重大重构）**仍走 skill 路径**，编排器**分批执行**（不一次性 Read 全部文件，拆 atomic step 为多组，批间写进度 checkpoint）。

**走 skill 路径时**：编排器 Read `pm-workflow/skills/workflow-evolution/SKILL.md` 按其 8 步流程执行（任务理解 → 必读 → 进度记录 → atomic step → 实施 → 机械自检 → SSOT 同步 → 完成报告）。

**走 Agent 路径时**：按下方既有规范派发（路径清单 + 必读路径 + 进度文件 + 整改循环 + Supervisor 审核闭环）。

> **[Must] 传路径而非传内容**：派发 Agent 的 prompt 必须使用**文件路径 + Read 指令**模式，**禁止**把规范文件、角色文件、前序成果文件的完整内容粘贴进 prompt。这样可以避免主 agent（编排器）自身读取并承载所有大文件的上下文，从根本上控制 token 消耗。
>
> **[Must] 编排器读文件边界**：编排器只能 Read 以下文件用于调度判断：①`process_record/state.md`；②`process_record/progress/` 下的进度文件（用于判断步骤推进）；③`process_record/tasks/scaffold.json`（用于阶段四模块依赖分析）；④`process_record/reviews/` 下的审核报告（用于判断通过/不通过、提取整改意见）；⑤`outputs/` 下成果文件的**文件头**（读 ≤ 30 行用于确认存在性和状态标记，禁止读全文）。其他所有文件（角色规范、阶段模板、规范文件、前序成果、任务卡等）**一律不得由编排器 Read**，必须通过路径由 subagent 自行 Read。
>
> **[Must] subagent 开工第一步**：所有 PM / Supervisor subagent 收到 prompt 后，必须先逐个 Read 路径列表中的所有文件（角色规范、规范文件、前序成果、任务卡等），读完后再制定分步计划、再动手生产内容。路径列表中任何一个文件未读即开工，视为违反硬规则。

> **[Must] PM / Supervisor Agent 文件改动权限边界**：PM Agent 与 Supervisor Agent 在 L1 业务任务（PRD / spec 生产、阶段产物修订、调整意见整改等）执行过程中，**只允许**修改下表「允许写入」列的文件，**禁止**修改 L2 工作流维护层文件。
>
> | 类别 | 路径 | 允许写入？ |
> |------|------|-----------|
> | **L1 业务产物** | `outputs/`（PRD / spec / 阶段产物 / components / 产品定义等）| ✅ 允许 |
> | **L1 过程记录** | `process_record/state.md` / `process_record/tasks/` / `process_record/progress/`（自己模块子文件）/ `process_record/reviews/`（Supervisor 写）| ✅ 允许 |
> | **L2 角色规范** | `pm-workflow/agents/*` | ❌ 禁止 |
> | **L2 规范文件** | `pm-workflow/rules/*`（含 `bujue-design-system/` / 模板 / 协议 / 硬规则 / 方法论 / 参数声明 / PRD template）| ❌ 禁止 |
> | **L2 校验脚本** | `pm-workflow/scripts/*`（含 `tests/`）| ❌ 禁止 |
> | **L2 skill 三件套** | `pm-workflow/skills/*` | ❌ 禁止 |
> | **L2 顶层元规范** | `CLAUDE.md` / `.claude/commands/*` | ❌ 禁止 |
>
> **Why**：L2 文件是工作流框架本身的元规范 / 校验逻辑，由编排器通过 `/retro` / `/changeRequest` / `workflow-evolution` skill 等显式入口维护；L1 业务任务期间夹带 L2 修订会导致：①责任不清（业务流程改动与工作流演化交织）②commit message 含糊（"修复问题"无法区分业务修复 vs 工作流演化）③规范变更绕过 SSOT 双锚同步检查清单。**历史已发生违规**（如 commit 616bd71 / d685800 在产品业务 commit 中混合 L2 脚本 +349/+477 行），需从规范层固化此边界。
>
> **How to apply**：
>
> 1. **PM Agent 自审清单**（`AI产品经理_Agent.md §五`）须含一项："本次任务修改的文件路径不含上表 L2 类别中标 ❌ 的路径"——发现 L2 文件需修改时立即 NB 上报（见下方第 4 点）
> 2. **Supervisor Agent 审核清单**（`AI产品主管_Agent.md`）须将 PM 是否越界改 L2 文件作为 P0 审核项——一票否决，进入整改循环
> 3. **编排器派发 prompt 必含此边界声明**：派发 PM/Supervisor Agent 时，prompt 末段须显式列出「PM 文件改动权限边界」+ 引用本节作为权威源（避免每次靠角色规范遗漏触发）
> 4. **遇到必须改 L2 的合理需求** —— **NB 上报标准 SOP**（PM 暂停 + 编排器审根源 + 驳回机制 + 分级处置；详见下方第 6 条独立段）
> 5. **机械兜底**（已落地）：git pre-commit hook 检测 L1+L2 混合 commit —— `pm-workflow/scripts/hooks/pre-commit` 在 commit 同时含 L1 路径（`outputs/` / `process_record/`）+ L2 路径（`pm-workflow/agents|rules|scripts|skills/*` / `CLAUDE.md` / `.claude/commands/*`）时拒绝 commit 并提示。新克隆的本地仓库须执行一次 `bash pm-workflow/scripts/install_hooks.sh` 安装。

#### `[Must]` 第 6 条：PM L2 修订诉求 NB 上报标准 SOP

> **本节定位**：PM 在 L1 业务任务执行过程中，若**确认**当前 atomic step 卡点根因是 L2 文件本身有缺陷（precheck 漏检 / 模板字段不足 / 规范错位等），按本 SOP 执行。**禁止**在 L1 业务任务期间自行 Edit 任何 L2 文件——这是 git pre-commit hook 兜底的硬边界。

##### 标准流程

```
PM 发现疑似需要 L2 修订
    │
    ▼
[第 1 步] PM 暂停当前 atomic step，写检查点到自己的进度文件
    │
    ▼
[第 2 步] PM NB 上报「Bxx-need-L2-fix」必含 4 字段：
    ① 涉及 L2 文件路径
    ② 现象描述（PM 观察到的卡点 / FAIL / 漂移）
    ③ PM 自行核对 SSOT 真源后的判断（"我认为根因是 L2 缺陷而非我的产物错误，因为 ..."）
    ④ 建议修订方向（具体到 check 函数 / 字段 / 段落级别）
    │
    ▼
[第 3 步] 编排器深度思考分析根源（必须，禁止跳过）：
    ① Read 涉及 L2 文件 + 真源 + PM 产物 + precheck 实际报错
    ② 核对：是 L2 缺陷？还是 PM 误读规范 / 用错路径 / 产物违反 SSOT？
    ③ 输出根源分析（写入 NB 处置记录），明确判定「合理」或「不合理」
    │
    ├── 不合理（PM 误读 / 误用）
    │     │
    │     ▼
    │   [第 4a 步] 编排器驳回 NB，反馈：
    │     ① 根源分析（哪里误解 / 为什么不是 L2 缺陷）
    │     ② 更合理的实施方案（让 PM 改产物 / 重新选路径 / 重读哪份规范）
    │     │
    │     ▼
    │   PM 接驳回反馈 → 重新思考方案 → 继续推进 L1 业务
    │   （同一 NB 同根因驳回 ≥ 3 次 → 升级产品总监裁决，禁止 PM 第 4 次推同思路）
    │
    └── 合理（确为 L2 缺陷）
          │
          ▼
       [第 4b 步] 编排器判分级：
         ├── 阻塞型：不修 L2，PM 当前 atomic step 无法完成
         │     → PM 完全暂停，编排器立即切 workflow-evolution skill 修 L2
         │     → 修完通知 PM 从检查点恢复 L1 业务
         │
         └── 非阻塞型：当前 atomic step 能完成，L2 缺陷仅影响后续兜底 / 跨模块场景
               → PM 完成当前 atomic step 后再暂停（保证业务节奏）
               → 编排器切 workflow-evolution skill 修 L2
               → 修完 PM 仅重跑受影响兜底环节，其余成果不动
```

##### 关键规则

- **PM 必须暂停**：上报 NB 后**禁止**继续往后做（即使是非阻塞场景也要在当前 atomic step 完成后停下，等编排器分级判定，不允许 PM 自己往后推进多个 atomic step）
- **编排器必须深度分析根源**：禁止"PM 说要改就改"——必须输出根源分析（合理性判定 + 反例验证），写入 NB 处置记录
- **驳回不是终点**：驳回时必须给"更合理的实施方案"，让 PM 有明确接续动作
- **驳回上限 3 次**：同一 NB 同根因驳回 ≥ 3 次仍纠缠 → 升级产品总监裁决，PM 不得第 4 次推同思路
- **L2 修订独立计数**：编排器切 skill 修完后 PM 恢复，**不计入** L1 业务的"3 次重做"额度（L2 修复 vs 业务重做是两个独立维度）
- **进度文件留痕**：NB 编号 / 编排器根源分析 / 处置结果（驳回 / 阻塞修复 / 非阻塞修复）须在 PM 进度文件 + L2 修订进度文件双向 link

##### 与既有规则的关系

- 取代旧第 4 条的简短版本（"NB 上报 → 编排器判断"），第 4 条改为指向本 SOP
- 配合第 5 条 git pre-commit hook 形成双层防御：本 SOP 是**规范层**（PM 该怎么做），hook 是**机械层**（违规时硬拦）
- PM §二 准则 8 / §5.0 自审清单 / Supervisor §四.0 通用前置审核 须引用本 SOP（不重复正文，避免漂移）

#### `[Must]` 第 7 条：派发接力基线同步纪律（subagent baton-pass freshness）

> **本节定位**：所有 subagent 派发的**通用基线纪律**——确保每一棒派发都接在最新基线上，避免接力丢改、覆盖上一棒产出。**普适于** PM / Supervisor / Plan / Explore / 调研 / 任意 subagent；隔离（`isolation: "worktree"`）与非隔离派发场景均适用。
>
> **触发场景**（高风险）：①串行整改循环（PM → Supervisor → PM rework → Supervisor）②阶段 4 多步骤接力（Step 1 → 1.X → 2 → 2.5 → 3 → 4 → 5 → 6 → 6.5 → 7）③阶段 4 模块并行派发（Step 3 / Step 5 同时启 N 个 spec/prd 模块 Agent）④调整意见多轮派发（编排器一日内多次派 PM / Explore / 调研 subagent）。

##### 根因背景

下游 /retro 共性根因 E：接力派发时，后续 subagent 基于"陈旧基线"作业，导致上一棒改动**丢失 / 被覆盖 / 重复劳动**。两种典型表现：
- **隔离 worktree 副本场景**（`isolation: "worktree"`）：worktree 在派发时刻从主仓 HEAD 创建，若主仓有未 commit 改动 → 副本不含，subagent 作业基线已陈旧
- **整改判定误用 `git status`**：PM 已 commit 整改后 `git status` 干净，Supervisor 仅看 `git status` 误判"整改未发生" → 错入二次重做循环

##### 三端锁（派发前 / 派发时 / 派发后）

**① 派发前（编排器）**——确认主仓库 HEAD 已含上一棒全部改动：
- 跑 `git status` 期望干净（无 staged / unstaged）
- 若上一棒 subagent 产物已落入工作树但未 commit → 编排器**先与产品总监确认后 commit，再派发下一棒**（commit message 注明上一棒 atomic step 产出，便于后续接力者 `git log` 核查）
- 若主对话本身有未 commit 改动（与上一棒无关的产物）→ 暂停派发，先与产品总监确认是否 commit / discard
- **不得**在 HEAD 不含上一棒产出的状态下派发"依赖该产出"的下一棒（典型反例：PM 整改完成但未 commit 即派发 Supervisor 审核——Supervisor 在隔离副本中看到的是整改前的旧 HEAD）

**② 派发时（subagent 内部）**——prompt 必含"第一步基线核查"硬指令：
- **非隔离副本**（默认 Agent 调度，无 `isolation: worktree`）→ subagent 第一步跑 `git log --oneline -3` 确认 HEAD 含上一棒预期 commit；working tree 即主仓最新（无需额外 sync）
- **隔离 worktree**（`isolation: "worktree"`）→ subagent 第一步跑 `git fetch && git reset --hard <main 分支名>` 确保副本与主仓 HEAD 一致；再 Read 路径清单
- 任何 subagent 发现 HEAD 不含预期上一棒 commit / 文件内容不符 → 立即停工 NB 上报，**禁止**基于陈旧基线作业

**③ 派发后（subagent 收尾 + 编排器交接）**——改动落回主仓库 + 核查 HEAD 状态后再派下一棒：
- subagent 完成 atomic step 后，显式 `git add` 已改文件（落回主仓工作树）；本工作流惯例 commit 由编排器在用户确认后做，subagent 自身不 commit（除非 prompt 显式授权）
- 编排器接收 subagent 完成回报后，**立即 `git diff` + `git log --oneline -1` 核查 HEAD 与工作树状态**，确认本棒产出已落地后再派下一棒
- 隔离 worktree 场景须额外 merge / cherry-pick 回主分支（避免改动留在副本被销毁）
- 在编排器与产品总监确认本棒 commit 前，**禁止派发"依赖本棒产出的隔离 subagent"**——若必须接力，须降级为非隔离派发（subagent 直接看主仓未 commit 工作树）

##### `[Must]` PM progress 自报 sha 一致性审计（commit 流程 sha 实证）

`[Must]` PM 在 progress 文件（`process_record/progress/stage[N]_*_plan.md`）自报"本步整改落地"时，若涉及**文件级 sha 字面**（如「`drafts/prd_M01_draft.html` sha = 8b74363b…」），**必须配套 `sha256sum` 实证**：

- PM 写 progress 行时禁口述 sha 字面（凭印象 / 历史 commit 复制 → 与当前工作树脱节风险）；必跑 `sha256sum <file>` 实测后引用前 8-12 位前缀
- 编排器接收 PM 完成回报 + 准备 commit 时，**必须比对 PM 自报 sha 与当前工作树 sha**：`sha256sum <file>` 实跑前缀 = progress 行字面前缀 → 一致放行 commit；不一致 → 暂停 commit + 与 PM 对账（progress 字面错 / 工作树被其他棒覆盖 / 历史残留）
- commit 后，编排器**必须再跑** `git show <new-commit>:<file> | sha256sum` 与 progress 自报 sha 三方一致（progress 字面 = pre-commit 工作树 = commit 落盘）；不一致 → 立即 revert + 排查（治 SNB-R4-01 同型"自报 sha 在 git 历史不存在 + 时序上下棒不可能覆盖"事故）
- progress 模板字面字段建议（PM 写入）：`sha256sum (实测前缀)：abc12345…`，编排器 commit 后追加 `commit-side verify：通过 / 不通过`

**Why（治 SNB-R4-01 元错型）**：PM R3 自报"24 帧治本」commit 进 0fe3457，progress 含 sha `8b74363b…`，但该 sha 在 git 历史不存在 + 时序上后续 commit `2b21630` 早于 R3 22 小时不可能覆盖。根因：编排器 commit 时未实证 PM 自报 sha 与 commit 后 git show 一致——本条把"未实证"升级为"必须实证 + 三方对账"。配套 precheck 兜底见 `precheck_stage4.py check_progress_sha_consistency`（可选，扫 progress 字面 sha vs 最近 commit 文件 sha 对比 → WARN 不一致）。

##### `[Must]` Supervisor 整改判定红线

`[Must]` Supervisor 判定"PM 是否整改"时：
- ❌ **禁止仅依赖 `git status`** 判定"整改未发生"——`git status` 只显示未 commit 改动，若 PM 整改后已 commit 则 `git status` 干净，但 HEAD 已变；此时误判会让 PM 二次重做相同内容（无意义的整改循环）
- ✅ **必须比对 HEAD 文件内容** 与整改要求逐项核查：
  - `git show HEAD:<file>` 查看当前 HEAD 文件内容
  - `git diff <pre-rework-commit> HEAD -- <file>` 看本轮整改 diff
  - 或直接 Read 文件 + 逐项核查整改清单是否落地
- ✅ 若判定整改未落地 → 在审核报告中**展示 HEAD 文件 grep / diff 实证**，不得仅口述"未整改"

##### `[Must]` Untracked 文件论证规范（SSOT #31 hook 盲区配套）

`[Must]` 判定 untracked 文件（典型：`outputs/` 整目录 / `process_record/tasks/scaffold.json` / `process_record/state.md` 等）**是否变更**时：
- ❌ **禁止仅凭 `git diff <path>` 输出为空**判定"未变更"——untracked 文件**永不进 git index**，`git diff` 对其恒为空，这是**逻辑空真**而非"未变更"证据（同型陷阱：`git status` 对 .gitignore 内文件恒"干净"）
- ❌ **禁止仅凭 `git ls-files <path>` 输出为空**佐证"无改动"——0 命中只证未跟踪，不证未变更
- ✅ **必须用 mtime / sha 基线**实证：
  - 基线快照：`find <untracked-paths> -type f | LC_ALL=C sort | xargs sha256sum | sha256sum` 取整体 sha
  - 比对前后：操作前后各取一次整体 sha，**字节一致 → 真未变更**；不一致 → 已被修改（即使 hook/diff 均未捕获）
  - 或 per-file：`stat -c "%Y %s %n" <file>` 取 mtime+size 元组比对
- ✅ Supervisor 审核报告 / PM 自审报告若结论含"L1 未变更 / outputs 未触 / scaffold 未改"，**必须附 mtime 或 sha 基线证据**，不得仅引 `git diff` 空输出

**Why（SSOT #31 hook 盲区根因）**：git pre-commit hook 用 `git diff --cached --name-only` 检 staged 文件；下游 `outputs/` 未 add 进 git、`process_record/` 整目录 .gitignore，**两类 L1 产物全程 untracked**。Hook L1+L2 混提兜底对这两类盲区——L1 改 50 次 hook 也看不到。**机械兜底缺位时，论证模式不能蹋空**；本条把"未变更"举证义务从 `git diff` 空（空真）升级到 mtime/sha 基线（实证）。

**典型场景**：
- 编排器同步 L2 时验证 L1 未污染 → 用 `find outputs process_record -type f | xargs sha256sum | sha256sum` 前后对比（已在 `downstream_l2_sync_procedure` memory Gotcha #6 修复路径落地）
- Supervisor 复审"PM 仅改 L2 未触 L1" → 报告须附 L1 sha 基线
- /retro 论证"outputs/scaffold 历次未变更" → 必须查 mtime 历史或 sha 快照档案，不得仅 `git diff` 空

##### 与既有规则的关系

- 取代旧"事后 reset 兜底"方案（事后兜底不可靠，且 reset 可能丢未 commit 的合理改动）
- 与第 6 条 PM L2 NB SOP 互补：第 6 条解决"PM 越界改 L2"问题，本条解决"接力丢改"问题；两条都属于通用前置纪律，PM 自检 / Supervisor 审核均须遵守
- 配合 `git pre-commit hook`（第 5 条）形成多层防御：hook 拦截 L1+L2 混提，本条防接力丢改
- PM Agent `§二 核心行为准则` 准则 10 / Supervisor Agent `§4.0 通用前置审核` 4.0.3 须引用本条作为权威源（不复刻正文，避免漂移）

派发 PM Agent 时，prompt 必须包含以下**路径清单与指令**（不得贴入文件完整内容）：
1. **方法论路径**（必列）：`pm-workflow/rules/agent_methodology.md`（要求 PM 开工前 Read，建立任务执行节奏的不变式认知）
2. **参数声明路径**（必列）：`pm-workflow/rules/agent_parameters.md`（要求 PM 开工前 Read，建立本角色在方法论下的具体参数实例化——必读路径、编号前缀、上报路径、atomic step 切分清单等）
3. 角色规范路径：`pm-workflow/agents/AI产品经理_Agent.md`（**分节读取** — 按 §大文件分节读取规范（SSOT #81）fetch 本任务必读章节，禁 Read 全文）
4. 原始需求路径：`需求简述.md`（若产品总监以纯文本形式提供需求，则直接以短文本插入，不需要路径）
5. 前序阶段成果**路径清单**（从 state.md「当前阶段产物」表读取，列出路径即可，不得 Read 后粘贴内容）
6. 已决策约束的获取指引（SSOT #18）：「请 Read `process_record/decisions_ledger.md` 全文，提取『已解答阻塞性问题』+『已决策非阻塞性问题』两表的所有 ✅已解答 / ✅已决策 条目并遵守——这是已决策清单的单一权威源；另 Read `process_record/state.md` 取当前阶段待处理的 ⏳ 开放问题」
7. 本轮整改要求：若为重做，可直接贴入整改意见（通常较短）或指向 `process_record/reviews/stage[N]_review.md`
8. 进度文件检查指引：给出进度文件路径 + 「存在则从第一个 `[ ]` 继续，不存在则创建」
9. **受影响阶段的规范文件路径清单**（根据本次调整所涉及的阶段显式列出，要求 PM 开工前逐个 Read；**禁止**粘贴文件完整内容）：
   - 调整涉及阶段1成果 → 路径 `pm-workflow/rules/tmpl_需求分析.md`
   - 调整涉及阶段2成果 → 路径 `pm-workflow/rules/tmpl_功能规划.md`
   - 调整涉及阶段3成果 → 路径 `pm-workflow/rules/tmpl_产品定义.md`
   - 调整涉及阶段4成果 → 按「阶段4规范文件传入策略」列出受影响的路径清单
   - 调整同时涉及多个阶段 → 逐一列出所有受影响阶段的路径
10. **硬性要求**（必须写入 prompt）：「开工前必须逐个 Read 上述路径清单中的所有文件（含方法论 + 参数声明 + 角色规范），读完后再按方法论 T1-T6 + X1-X4 节奏制定分步计划并动手，禁止仅凭路径或文件名猜测内容。」**大文件分节读取例外（SSOT #81）**：清单中标注「分节读取」的大文件**不 Read 全文**，按 prompt 给出的 `doc_query.py fetch` 命令取必读章节（命令由编排器从 §大文件分节读取规范 的必读章节清单表复制）；**清单是下限不是上限**——任务涉及清单外内容时先 `outline` 看架构再补 fetch / `locate`，禁因"清单没列"而跳过任务实际需要的章节。

#### `[Must]` 第 8 条：页面集守恒缺页 escalation SOP（PM 禁擅自增页，SSOT #74）

> **本节定位**：阶段 2 §3.1/§3.3 页面集是产品总监审核过的 SSOT 基线（`tmpl_功能规划.md` 双锚 #74）。后续阶段（阶段 3 §6 / 阶段 4 scaffold pages）页面集**必须 ⊆ 基线**，PM **不得擅自增页**。当 PM 判断现有页面结构致某业务流程无法闭环（缺承载页则业务路径走不通）时，按本 SOP 上报产品总监拍板——**与第 6 条 NB 上报 SOP 的区别**：第 6 条是 L2 文件缺陷（编排器走 skill 修）；本条是**业务页面集需扩张**（产品总监决策 + 回写阶段 2 基线，非 L2 改动）。

##### 标准流程

```
PM 判断现有页面集致某业务流程无法闭环
    │
    ▼
[第 1 步] PM 暂停当前 atomic step，写检查点；禁止擅自在 scaffold / draft 加页绕过
    │
    ▼
[第 2 步] PM 书面上报「缺页 escalation」必含 4 字段：
    ① 缺口位置（哪条业务流程 / 哪个状态走不通）
    ② 为何现有页无法闭承载（逐条排除现有页 + 内嵌/子状态承载可能性）
    ③ 建议新增页（页名 / 端 / 访问者 / 关键交互 / 是否对客）
    ④ 影响范围（涉及阶段 2 §3.3 + 阶段 3 §6 + scaffold + drafts + outputs）
    │
    ▼
[第 3 步] 编排器深度核验（必须，禁跳过）：
    ① Read 阶段 2 §3.1/§3.3 基线 + 阶段 3 §6 + scaffold pages + 相关业务流程
    ② 核对：是真缺承载页（业务闭环硬缺口）？还是 PM 误判（现有页/内嵌/子状态可承载，
       属「擅自增页」越界——典型：把本该内嵌的子卡片/弹窗抬成独立页）
    ③ 输出核验结论（写入进度文件）：「真缺口」或「误判越界」
    │
    ├── 误判越界（现有页/内嵌可承载）
    │     → 编排器驳回，反馈正确承载方式（内嵌子状态 / 子区域 / modal）
    │     → PM 改用承载方式，scaffold page 标 `page_source: stage2`
    │     （同一缺口误判驳回 ≥ 3 次 → 升产品总监裁决）
    │
    └── 真缺口（业务闭环硬缺承载页）
          ▼
       [第 4 步] 编排器呈产品总监（AskUserQuestion）：缺口分析 + 建议新增页 + 影响范围
          │
          ├── 产品总监否决 → PM 改用现有页/内嵌承载（同误判分支）
          │
          └── 产品总监批准
                ▼
             [第 5 步] 回写阶段 2 §3.3 基线（编排器走 workflow-evolution 或 PM 阶段 2 回改）
                + scaffold 新页标 `page_source: director_approved:<YYYY-MM-DD>`
                + 向下游阶段 3 §6 / scaffold / drafts 传导
```

##### 关键规则

- **PM 禁擅自增页**：上报后禁止自行在 scaffold / draft 加页绕过 escalation（机械兜底 `check_page_source_provenance` 缺 page_source 标注 → WARN）
- **内嵌 ≠ 独立页**：阶段 2 标「内嵌某页」的 UI 面，下游只能子状态 / 子区域承载，禁外化独立 page（治实验报告决定性案例：强制下架卡片两源明文内嵌，PM 凭空抬独立页 + 误套 admin-form-flow 表单范式）
- **产品总监拍板回写基线**：新增页**必须**先回写阶段 2 §3.3（基线随之升级），不得只在下游 scaffold 加（否则页面集漂移、基线失真）
- **Supervisor 反查兜底**：Step 1.X 中段审核「scaffold 每页可追溯阶段 2 §3.3 / page_source 标注」逐页核对（详 `AI产品主管_Agent.md`）——报告 3.5 实证：AI 拆 + AI 自审双双漏掉越界，人类拿阶段 2 明文反向校验才抓出，这是机械层抓不到的语义卡点

##### 与既有规则的关系

- 与第 6 条（PM L2 修订 NB 上报）正交：第 6 条治 L2 文件缺陷，本条治业务页面集扩张（产品总监决策非 L2 改动）
- 真源 `tmpl_功能规划.md §3.1/§3.3`（双锚 #74）；本 SOP 是 escalation 执行层，不重复基线正文
- 与 SSOT #38 正交：#38 管页面层级渲染派生方向（scaffold 仍是阶段 4 真源），#74 管页面集成员守恒

#### 阶段4规范文件传入策略

> **[Must]**：阶段4所有「传入」均为**路径传入**——编排器在派发 Agent 的 prompt 中列出文件路径，要求 subagent 开工前自行 Read。**禁止**编排器 Read 这些文件后将内容粘贴进 prompt。按需列表，不得全量列出所有规范文件路径。

| 文件路径 | 列入路径清单的条件 |
|------|---------|
| `pm-workflow/rules/proto_contract.md` | **必列**，无论任何子任务 |
| `pm-workflow/rules/bujue-design-system/pub_components_index.md` | **阶段 4 任何子任务必列**（pub 组件统一检索入口——分类总览 + 业务场景反查 + D1-D5 能力反查；PM 先读本索引找候选，再按需精读 `components/*.md` 详情） |
| `pm-workflow/rules/prd_expression_standard.md` | 涉及 prd.html 生成或修改时列入（文档结构、标准区块规范） |
| `pm-workflow/rules/proto_spec_md.md` | 涉及 spec.md 生成或修改时列入 |
| `pm-workflow/rules/proto_platform_app.md` | 产品覆盖 APP（手机 / PAD / iOS / Android）时列入 |
| `pm-workflow/rules/proto_platform_desktop.md` | 产品覆盖桌面 Web 时列入 |
| `pm-workflow/rules/proto_platform_miniprogram.md` | 产品覆盖微信小程序时列入 |
| `pm-workflow/rules/proto_platform_h5.md` | 产品覆盖手机 H5 时列入 |
| `pm-workflow/rules/proto_cross_platform.md` | 产品覆盖 2 个及以上端口时列入（含移动端操作布局规范、弹框规范） |
| `pm-workflow/rules/bujue-design-system/tokens.md` | 涉及 prd.html 生成或修改时**必列**（颜色/字体/间距/圆角/阴影唯一来源） |
| `pm-workflow/rules/bujue-design-system/fb-fallback-manifest.md` | 涉及 prd.html 生成或修改时**必列**（兜底 CSS 调用清单——27 个 anchor `fb-*` HTML 模板（含 §1.5 三件套独立 anchor + tp-marker + §3.4-§3.7 面板/浮层 4 组件 issue # 10/# 11/# 12 新增））。**`[Must]` PM 按需精读,禁止 Read 全文**（manifest 600+ 行,PM 典型只用 5-8 个组件,Read 全文 ~80% 浪费）：① `grep -n "FB-MODEL: {组件 id}"` 定位行号 ② `Read offset:N limit:25-40` 精读单组件块。完整 27 个 anchor 清单见 manifest 顶部「§PM 按需精读 SOP」段。CSS 由 `assemble.py prd` 自动注入到 PRD `<style>` 顶部，PM 无需粘贴 CSS。|
| `pm-workflow/rules/bujue-design-system/components/empty-loading.md` | 涉及 prd.html 生成或修改时**必列**（空状态 SVG 路径 + Loading CDN 规范） |
| `pm-workflow/rules/bujue-design-system/components/button.md` | 产品定义包含按钮交互时列入（几乎必列） |
| `pm-workflow/rules/bujue-design-system/components/input.md` | 产品定义包含表单/输入框时列入 |
| `pm-workflow/rules/bujue-design-system/components/tag-tab.md` | 产品定义包含筛选 Tag 或 Tab 切换时列入 |
| `pm-workflow/rules/bujue-design-system/components/card.md` | 产品定义包含列表卡片布局时列入 |

> **三层引用关系**：`pub_components_index.md`（一级检索入口）→ `components/*.md`（按需精读单个组件详细规范）→ `fb-fallback-manifest.md`（实际 HTML 模板与 class 调用方式）。PM 不必同时全列，按子任务需要从一级展开。

**典型场景示例（路径清单）**：
- 仅生成 APP 端文档（含表单+列表） → `proto_contract.md` + `prd_expression_standard.md` + `proto_spec_md.md` + `proto_platform_app.md` + `tokens.md` + `empty-loading.md` + `button.md` + `input.md` + `card.md`（共 9 个路径）
- 全端产品（APP + 桌面 + 小程序 + H5，含全部组件）→ 上述全部 `proto_*.md` 平台文件 + `tokens.md` + `empty-loading.md` + 所有 `components/*.md`（`_pending.md` 除外）

**[Must] 严格按需列入**：prompt 中只列出本次任务**实际需要**的路径，禁止"保险起见"把所有路径都列上——那等同于强迫 subagent Read 全部规范文件，规模效应下同样会炸上下文。例如：纯 spec 生成任务只需 `proto_contract.md` + `proto_spec_md.md`，不得列入 `prd_expression_standard.md` / `tokens.md` / `components/*.md`。

#### 阶段四模块化派发规范

阶段四不做整体一次性派发，编排器按以下 7 步顺序协调执行（拼装步骤由编排器直接完成，无需派发 Agent）：

> **[Must] 全部 PM Agent 派发的前置必列项**：阶段四 Step 1 / 2 / 3 / 5 / 7 任一 PM Agent 派发的 prompt 路径清单，**必须把以下两条作为编号 1、2 显式列出**（已在各 Step 路径清单中落实）：
> - `pm-workflow/rules/agent_methodology.md`（方法论）
> - `pm-workflow/rules/agent_parameters.md`（参数声明）
>
> subagent 收到 prompt 后开工前必须先 Read 这两条以建立方法论遵循和参数实例化的认知基础。如发现某 Step 路径清单缺失这两条，视为派发模板退化，须按本节要求补回。

> **[Must] 组件检索 SOP（Step 1 / 2.5 / 3 / 5 全部 PM Agent 适用）**：subagent 在涉及"使用 / 评估 / 引用 pub 或 proj 组件"的任何工作前，按以下 5 步先粗后精检索：
> 1. **扫 pub 索引分类总览**：先读 `pub_components_index.md §二`，按业务直觉锁一级类（atom / form / container / list / state）
> 2. **在该类的子类下找候选**：在 §三 组件总表对应类别块中圈定 ≤ 3 个候选 id
> 3. **D1-D5 验能力**：用 §五 能力反查表逐维度核对候选是否覆盖业务需求
> 4. **业务术语模糊时改走 §四 业务场景反查**：自然语言入口（"我要做..."→候选）
> 5. **判定结论**：全覆盖 → 引用 pub；部分命中 → 走 `proj_component_protocol.md §一.B` 派生 proj
>
> 凡 §四 / §五 中标 `⚠ pub 无` 的能力，必须按 proj_component_protocol 派生，不得用现有 pub 组件硬凑（违反 S4-19）。

**Step 1｜派发任务规划 PM Agent**

> **[v2.0 重大职责变更]**：本步从单纯的"模块拆分 + 编号预分配"扩展为"**蓝图层全决策**"——PM 必须在本步完成对每个模块的组件候选 D1-D5 评估、proj 派生缺口识别、owner 推算、depends_on 结构化。这是为了在 Step 1.X 中段审核中暴露所有蓝图问题，避免后期返工。
> 子阶段二.5 不再做"识别 + 派生决策"，仅做"实现层 schema 详情"。子阶段一耗时上升约 30-50%，但蓝图错误前置暴露，整体效率更高。

- prompt 以**路径清单**方式列出（禁止贴入文件内容）：
  1. 方法论路径 `pm-workflow/rules/agent_methodology.md`
  2. 参数声明路径 `pm-workflow/rules/agent_parameters.md`（PM Agent 列）
  3. 角色规范路径 `pm-workflow/agents/AI产品经理_Agent.md`（**分节读取**——行选择按 §大文件分节读取规范 SOP 第 1 步子角色规则，禁全读）
  4. 硬规则清单路径 `pm-workflow/rules/rule_hard_constraints.md`（**分节读取**——通用行 + 本阶段/角色行，详 §大文件分节读取规范）
  5. 需求简述路径 `需求简述.md`
  6. 产品定义路径（从 state.md 读取，通常为 `outputs/产品定义_[产品名]_latest.md`）
  7. 已决策约束路径 `process_record/decisions_ledger.md`（要求 PM Read 全文提取已解答 / 已决策条目，SSOT #18）+ state.md 路径 `process_record/state.md`（取当前阶段产物 / ⏳ 开放问题）
  8. 任务卡模板路径 `pm-workflow/rules/task_card_template.md`
  9. 全局约束路径 `pm-workflow/rules/proto_contract.md`（必传）
  10. **pub 组件索引路径 `pm-workflow/rules/bujue-design-system/pub_components_index.md`**（必读；PM 须为**每个模块**逐一按 D1-D5 评估 pub 覆盖度并识别 proj 缺口，结果写入 scaffold.json `candidate_components` 字段）
  11. **proj 协议路径 `pm-workflow/rules/proj_component_protocol.md`**（必读 §一 双触发 A/B + D1-D5 5 维清单，作为缺口识别 SOP）
  12. 进度文件路径 `process_record/progress/stage4_[产品名]_plan.md` + 存在性检查指引
  13. **scaffold v2.0 schema 定点读取指令（SSOT #81 杠杆 c）**：`python3 pm-workflow/scripts/doc_query.py fetch pm-workflow/rules/agent_dispatch_protocol.md "scaffold v2.0 schema"`——**禁 Read 本协议全文**（~34k tokens，其余节为编排器面向内容；schema 节 ~14.5k 是 TP 唯一必读，原「详见下方」对 TP 是悬空引用，本项治之）
- prompt 中明确注明：「角色：任务规划」，并加入「**[Must]** 开工前请逐个 Read 上述路径清单中的所有文件（标注分节/定点读取的按指令 fetch）；按角色规范"组件检索 SOP"5 步对**每个模块**逐一评估候选 pub 与 proj 缺口；scaffold.json 必须用 v2.0 schema（**用第 13 项 doc_query 命令取 schema 节**）」
- **PM 输出物**：
  - 各模块任务卡 `process_record/tasks/task_M[XX]_*.md`（候选组件清单段**留空占位**，由 gen_scaffold 在 Step 1.5 自动从 scaffold.candidate_components 衍生写入；PM 不手填该段）
  - `process_record/tasks/scaffold.json`（v2.0 schema，含 modules / 候选组件 / depends_on 对象 / owner_assignments / **`page_archetypes` 顶层 + 每页 `archetype` 引用**——提议2 页面结构范式契约，PM 按页面类型产出范式定义本体并为每页指派范式 id；系统性结构问题优先扩充/修订共享范式定义（路径 i），仅当该页确属独立结构类型才新建范式（路径 ii），防范式增殖稀释统一价值 / **每模块可选 `purpose`**——提议3 SSOT #40，PM 从阶段 3 §6.5 产品架构提炼一句话模块职责，缺省不阻断；`depends_on` 复用作模块依赖边）
  - **不再**手动构建任何骨架文件（spec/prd 主文件骨架 + 各模块草稿骨架 全部由 gen_scaffold 在 Step 1.5 生成）
- **编号锁定要求**（来自 `proto_contract.md §三`）：任务规划阶段须一次性确定所有模块（M）、页面（P）、状态编号并写入 scaffold.json；scaffold.json 生成后三层编号不得修改，如需变更须走 `/changeRequest` 流程；触点编号（T/D）由后续 Spec Agent 分配

#### scaffold v2.0 schema（PM 子阶段一必须按此结构产出）

```json
{
  "schema_version": "v2.0",
  "product": "[产品名]",
  "platforms": ["桌面Web" | "APP" | "小程序" | "H5", ...],
  "version": "v1.0",
  "description": "[一句话产品简述]",
  "status": "草稿" | "评审中" | "已批准",
  "changelog": [{"version": "v1.0", "desc": "...", "reason": "...", "author": "...", "reviewer": "", "date": "..."}],

  "page_archetypes": [
    {
      "id": "list",
      "name": "列表页范式",
      "regions": [
        {"slot": "filter-bar",  "hosts": "筛选 / 搜索 / 排序控件"},
        {"slot": "data-area",   "hosts": "表格 / 卡片列表 + 空 / 加载 / 错误态"},
        {"slot": "bulk-action", "hosts": "批量操作区"},
        {"slot": "pagination",  "hosts": "分页 / 加载更多"}
      ],
      "invariants": ["filter-bar 恒在 data-area 之上", "bulk-action 不并入 filter-bar"],
      "extension": ["extra-toolbar"]
    }
  ],

  "modules": [
    {
      "id": "M01",
      "name": "[模块业务名]",
      "task_card": "process_record/tasks/task_M01_[模块名].md",

      "depends_on": [
        {
          "module": "M02",
          "kind": "section_jump" | "shared_component" | "data_flow" | "permission",
          "target": "H-M02-P01-default" | "proj.L2.product-card" | "[字段名]" | "[角色名]"
        }
      ],

      "candidate_components": {
        "pub": [
          {"id": "fb-textarea", "purpose": "反馈内容输入"},
          {"id": "fb-btn-primary", "purpose": "提交按钮（主操作）"}
        ],
        "proj_gaps": [
          {
            "name": "rich-textarea",
            "trigger": "B-D3",
            "reason": "pub fb-textarea 无富文本/表情能力（D3 交互缺口）",
            "inherits": "pub.L1.textarea",
            "shared_with_modules": []
          }
        ]
      },

      "owner_assignments": {
        "proj.L2.product-card": "M01"
      },

      "pages": [
        {
          "id": "P01",
          "name": "[页面名]",
          "spec_id": "spec-M01-P01",
          "route": "/feedback",
          "archetype": "list",
          "states": [
            {"name": "default", "prd_id": "H-M01-P01-default", "roles": ["..."]}
          ],
          "touchpoints": [
            {"id": "T01", "kind": "trigger", "element": "新建按钮", "action": "点击"},
            {"id": "D01", "kind": "data", "element": "名称回显"}
          ]
        }
      ]
    }
  ]
}
```

**v2.0 关键字段说明**：

| 字段 | 必填 | 说明 |
|------|-----|------|
| `schema_version` | ✅ | 固定 `"v2.0"`；缺失或低于 v2.0 → gen_scaffold 报错并要求升级 |
| `modules[].depends_on` | ✅ | 对象数组（不再是字符串数组）；空依赖填 `[]`；`kind` 必须是枚举内一种；`target` 必须能在被依赖模块中解析到（precheck 校验） |
| `modules[].candidate_components.pub` | ✅ | 本模块要用的 pub 组件清单（id + 一句话用途）；空填 `[]` |
| `modules[].candidate_components.proj_gaps` | ✅ | 本模块按 D1-D5 评估发现的 proj 缺口；空填 `[]`；每条含 trigger（A/B + 维度）+ reason + inherits + shared_with_modules（其他共用模块） |
| `modules[].owner_assignments` | ✅ | 仅当本模块是某 proj 组件的 owner 时填写；owner = 共用该 proj 的模块中 scaffold.json `modules[]` 顺序最靠前者；空填 `{}` |
| `modules[].pages` | ✅ | 数组，每项 `{id, name, route, states, archetype, touchpoints?, embedded_components?}`。**普通模块必非空**（至少 1 页）；**logic-only 模块必为 `[]`**（详 `modules[].ui_carrier_modules` 字段定义）。机械兜底（双层）：①`gen_scaffold.py validate_v2_schema`（缺字段 / 非数组 → FAIL；空数组 → 转 logic-only 校验）②`precheck_stage4.py check_scaffold`（同三层校验，终审兜底）|
| `modules[].pages[].states[].roles` | ✅ | 数组（list of strings），每个元素是产品定义 §3 用户画像中的「角色 ID」字面值（如 `"role-1"`）或「角色名」字面值（如 `"销售"`）；**同一 scaffold 文件内必须统一使用 ID 或名,不得混用**（precheck_stage4 强制校验）；推荐用 ID 因业务名变更时仅改 §3 真源、scaffold 不动；空数组 `[]` 表示无角色限制（公开访问）；抽取算法见 `tmpl_产品定义.md §5「角色名抽取算法」`段 |
| `page_archetypes` | ✅ | **顶层**非空数组（提议2，SSOT 双锚 #39）——页面结构范式定义本体，每产品定义一次、被多页共用。每条：`id`（唯一）/ `name` / `regions`（非空数组，每项 `{slot, hosts}`：具名区域 + 容纳什么）/ `invariants`（结构不变量，如"filter-bar 恒在 data-area 之上"）/ `extension`（声明的扩展位）。PM 子阶段一按页面类型（列表 / 详情 / 表单 / 向导…）产出；gen_scaffold.validate_v2_schema 首次闸 + precheck_stage4 Step6.5 承接校验 |
| `modules[].pages[].archetype` | ✅ | 该页引用的范式 id（薄引用，必 ∈ `page_archetypes[].id`，悬空 FAIL）。多页指同一 archetype = 强制套同一结构契约 → 跨模块相似页面统一。Step3/5 模块 subagent **现场读 scaffold**（不预烘焙，H1=(c)）取本页 archetype 做容纳性二值校验 |
| `modules[].purpose` | ⬚ 可选 | 一句话模块职责（提议3，SSOT #40）。PM 子阶段一从阶段 3 `tmpl_产品定义.md §6.5 产品架构`提炼。**可选**：填则须为字符串，缺省不报错（D2——下游无破坏性迁移）；assemble 派生「模块架构说明」时，有则渲染职责列、无则回退 `—`。`modules[].depends_on` 复用既有字段作模块依赖边 |
| `modules[].pages[].touchpoints` | ⬚ 可选（`[Should]` 治本） | **触点 canonical 单源**（item 6 治本，SSOT #44 / S4-34）。数组，每项 `{id: "T01"/"D01"（T=主页触点 / D=弹窗抽屉内，页面内唯一）, kind: "trigger"/"data", element, action}`。PM 子阶段一预声明全量触点 → gen_scaffold 据此**预填 spec 触点表 canonical ID 行**（Spec Agent 仅补描述、禁增删 / 改 ID）；precheck `check_touchpoint_canonical` 校 spec/prd 引用 ⊆ canonical。**可选 + 向后兼容**：缺省走旧两段式（Spec Agent 手写 T[NN]，但反复手写偏差，故 [Should] 迁移）。增删触点须回 scaffold 重跑 gen_scaffold |
| `modules[].pages[].embedded_components` | ⬚ 可选（SSOT #76 R3） | **内嵌子组件构造**——隶属本页的子卡片 / 子 modal，含自己的 `states`（各带 `prd_id`），复用 prd_id→section→FRAME→nav 全套机器，**不占独立 page/route / 不计页面数 / 不受 page_source #74 约束**。数组，每项 `{id（页内唯一）, name?, archetype?, states: [{name, prd_id, roles?}]}`；内嵌 `prd_id` 约定形如 `H-M[XX]-P[XX]-<embed_id>-<state>`（须以父页 `H-M[XX]-P[XX]-` 前缀开头）。**用途**：治"scaffold 缺内嵌带状态构造 → PM 为出帧把内嵌子卡片/弹窗逼成独立页"根因（实验报告决定性案例：强制下架卡片）；与 #74 R1 禁擅自增页正交（R1 纪律层 / R3 根因层）。**可选 + 向后兼容**：缺省零变化。**双层机械兜底**：①蓝图层 `gen_scaffold.validate_v2_schema`（id 页内唯一 + states 非空 + prd_id 父页作用域 + 同页撞号）②终审层 `precheck_stage4.check_scaffold`（格式 + 全局唯一）+ `#72 check_scaffold_outputs_frame_consistency`（frame 一致性含内嵌，统一 helper `iter_page_prd_ids` 收集防漏）|
| `modules[].ui_carrier_modules` | ⬚ 仅 **logic-only 模块**必填 | **logic-only 模块声明字段**（业务逻辑层 / API 层 / 数据契约模块，无独立 UI 页面）。当 `modules[].pages == []` 时**必填**：数组（list of strings），元素为承载本模块 UI 表现的其他模块 id（必 ⊂ `scaffold.modules[].id`）。语义：本 logic-only 模块的 UI 表现内嵌在 `ui_carrier_modules` 列表中模块的页面状态帧。**适用判定**（PM 子阶段一）：当模块所有 UI 表现都可内嵌于其他模块的状态帧 / 触点 / 数据流时（如官方分类树消费 / 编号生成事务 / 后端 API 模块），可设 `pages=[]` + `ui_carrier_modules=[承载模块 id]`；**禁滥用**——若有任一独立路由 / 独立交互入口 / 独立角色权限分支，禁标 logic-only，须设独立 pages。**双层机械兜底**：①蓝图层 `gen_scaffold.py validate_v2_schema`（Step 1.5 之前）②终审层 `precheck_stage4.py check_scaffold`（Step 6.5）；均校验 `pages=[]` → 必含 `ui_carrier_modules` 非空数组 + 引用 ⊆ scaffold.modules[].id，任一违反 FAIL |

**logic-only 模块说明**（v2.0 新增模式，源自 2026-05-28 quotation-tool CR-20260526-01 M09 案例落地）：
- **定义**：业务逻辑层模块（无 UI），UI 表现 100% 内嵌于其他承载模块的状态帧 / 触点 / 数据流
- **典型场景**：①外部数据消费层（如官方分类树消费、第三方 API 适配）②业务规则引擎（如编号生成事务、价格计算逻辑）③数据契约模块（如类型定义、API schema）
- **不适用场景**：模块有任一独立 UI 入口 / 独立路由 / 独立角色权限分支（应设独立 pages）
- **机械兜底（双层防御深度）**：①蓝图层 `gen_scaffold.py validate_v2_schema`（Step 1.5 之前拦截）②终审层 `precheck_stage4.py check_scaffold`（Step 6.5 兜底）；均校验 pages=[] → 必含 ui_carrier_modules 非空数组 + 引用完整性
- **派生影响**：①spec / prd「页面架构总览」mermaid 不渲染该模块的页面节点（pages=[] 自然为空）②模块依赖图仍渲染（depends_on 关系不变）③模块架构说明列表渲染该模块 + 标注「logic-only，UI 内嵌于 [ui_carrier_modules]」

**内嵌子组件 embedded_components 说明**（v2.0 新增构造，SSOT #76 R3，2026-06-10 落地，源自 pdhm-exp-manual-task-split 人工拆任务对照实验问题 4）：
- **定义**：隶属某 page 的子卡片 / 子 modal，**含自己的 states（各带独立 prd_id）但不占独立 page/route**——复用 page 的 prd_id→section→FRAME→nav 全套机器出帧。
- **适用判定**（PM 子阶段一 / 拆任务阶段）：阶段 2 标注为「内嵌某页」的 UI 面（如"M01-P01 卡片 1 内嵌强制下架"），需单独出状态帧但**不是独立页**时 → 用 `embedded_components` 承载，**禁外化为独立 page**（违 #74 页面集守恒）。
- **不适用场景**：有独立路由 / 独立页面语义的 UI 面 → 用正常 `pages[]`（embedded ≠ page）。
- **与 logic-only 模块的区别**：logic-only 是**模块**无 UI（pages=[]，UI 由其他模块承载）；embedded 是**页内子组件**有自己的帧（隶属某 page，复用该 page 的渲染机器）。
- **派生影响**：①`gen_scaffold` build_proto_nav 渲染为 page 下第 4 层折叠子组 + build_module_sections 出 section + [FRAME] 占位 + build_prd_module_draft 出 FRAME 草稿块（PM 填）②`precheck` 各 prd_id 收集路径经 `iter_page_prd_ids` helper 统一含内嵌（#72 frame 一致性 / check_prd / check_scaffold）③**v1 限制（NB）**：内嵌帧不派生 C-4 业务契约（spec 侧无内嵌条目，assemble lookup 未命中跳过无错；内嵌帧有 interaction-card 交互说明，完整 C-4 属未来增强）；内嵌状态不进 page-only 语义校验（check_state_coverage / check_archetype_semantics / check_spec_state_table_count，避免污染页级语义推断）。

**owner 推算规则**（PM 子阶段一必须执行）：

1. 收集本期全部 proj_gaps（跨模块去重）
2. 对每个 proj 组件，查 `proj_gaps[].shared_with_modules ∪ {本模块}` 得到共用模块集合
3. 共用模块集合 ∩ scaffold.modules[] 取顺序最靠前者，作为该 proj 的 owner
4. 在 owner 模块的 `owner_assignments` 中记录；非 owner 模块的 owner_assignments 中**不**记录该 proj

**owner 流转链路**（单一事实源 SSOT；防止多处独立计算导致漂移）：

```
PM 子阶段一【计算并写入】scaffold.modules[].owner_assignments        ← 唯一权威源
        ↓
   Step 1.X 主管【校验】owner 推算正确性（D-04 维度，对照算法）
        ↓
   gen_scaffold.py（Step 1.5）【读取】→ 任务卡 C 表 + PRD 草稿 OWNER-INFO 注释
        ↓
   PM 子阶段二.5【读取】→ components_*.md A 表 owner 列（直接抄入，禁止重算）
        ↓
   编排器 Step 5【读取】→ 注入 PRD Agent prompt 的「本模块 proj 归属」段
        ↓
   precheck（Step 6.5）【兜底校验】→ A 表 owner = 算法期望值 + 草稿 PROJ-CSS 归属一致
```

**[Must] 单一事实源约束**：除"PM 子阶段一计算"和"precheck 兜底校验"两处外，**所有其他角色一律只读不算**。算法定义（modules[] 顺序最靠前者）仅在这两处适用；其他文档中出现的算法描述均为同一规则的语义重述，不构成独立计算授权。若 PM 子阶段二.5 / 编排器 / 下游脚本擅自重算，构成对 v2.0 [Must] 不重做评估的违反——须通过**自然语言调整路径**（CLAUDE.md「调整意见自动记录规则」路径 B）派发 PM 修正 scaffold.owner_assignments 后再继续；涉及跨阶段联动 / 三层编号变化的重大场景升级到 `/changeRequest`。**禁止就地纠偏**（在 components_*.md 直接改 owner 列、跳过 scaffold 修正）。

PM 完成后，编排器**先派发 Step 1.X Supervisor 中段审核**，审核通过后再进入 Step 1.5（参见下方 Step 1.X）。

**Step 1.X｜派发 Supervisor 中段审核（v2.0 新增）**

> **目的**：在脚本写骨架之前审核"蓝图"——scaffold.json + 任务卡内容。骨架是"已审核蓝图"的衍生产物，不再依赖事后机械检查"占位是否填满"。
>
> **审核者**：Supervisor Agent（与终审同一角色，但以"中段视角"出发——只审蓝图层决策，不审实现细节）。

- prompt 以**路径清单**方式列出（禁止贴入文件内容）：
  1. 方法论路径 `pm-workflow/rules/agent_methodology.md`
  2. 参数声明路径 `pm-workflow/rules/agent_parameters.md`（Supervisor 列）
  3. 角色规范路径 `pm-workflow/agents/AI产品主管_Agent.md`（**重点 §四.5 scaffold 中段审核**）
  4. 硬规则清单路径 `pm-workflow/rules/rule_hard_constraints.md`（**分节读取**——通用行 + 本阶段/角色行，详 §大文件分节读取规范）
  5. scaffold.json 路径 `process_record/tasks/scaffold.json`
  6. 各模块任务卡路径 `process_record/tasks/task_M[XX]_*.md`（逐一 Read）
  7. 产品定义路径（从 state.md 读取）
  8. pub 组件索引路径 `pm-workflow/rules/bujue-design-system/pub_components_index.md`（用于核查 candidate_components.pub 中 id 是否合法）
  9. proj 协议路径 `pm-workflow/rules/proj_component_protocol.md`（用于核查 proj_gaps 触发因素 + D1-D5 推理是否合理）
  10. 审核报告路径 `process_record/reviews/stage4_scaffold_review.md` + 「不存在则创建」指引
- prompt 中明确注明：「角色：scaffold 中段审核 Supervisor」+「**[Must]** 开工前请逐个 Read 上述路径清单中的所有文件；按角色规范 §四.5 维度逐项审核：模块拆分合理性 / candidate_components 覆盖度 / proj_gaps 触发因素准确性（A/B + D1-D5 推理）/ owner 推算正确性 / depends_on 结构化完整性 / 编号体系合规 / **页面结构范式契约合理性（page_archetypes 范式定义是否覆盖各页面类型、每页 archetype 分配是否恰当、是否存在范式增殖——同类页面应复用同一范式而非各建一个；系统性结构问题应走路径 i 改共享定义而非路径 ii 增范式）**」+「输出审核报告写入 stage4_scaffold_review.md，结尾标注 ✅ PASS 或 ❌ FAIL + 整改清单」
- **路由**：
  - 通过（✅ PASS）→ 编排器进入 Step 1.5（gen_scaffold）
  - 不通过（❌ FAIL）→ 编排器按下方「Step 1.X 整改派发 prompt 模板」派发 PM 子阶段一整改 scaffold + 任务卡，整改后重派 Step 1.X
  - 整改循环上限：**3 轮**；超过仍不通过须升级处理（拆分问题 / 多套候选方案 / 提交产品总监裁决）
  - **本步整改不计入终审 3 次重做额度**，独立计数（蓝图层审核与实现层审核解耦）

**Step 1.X 整改派发 prompt 模板**（FAIL 路由专用，不得退化为"派一个简单 PM"）：

> **[Must] 红线**：本模板存在的目的就是补齐 §阶段四派发规范开头「全部 PM Agent 派发前置必列项」的 Step 1.X 覆盖空白——任何整改派发 prompt **必须**把方法论 + 参数声明作为编号 1、2 显式列出。如发现编排器实际派发的 prompt 缺失这两条或下方任一必列项，视为派发模板退化，需按 [Must] 修复后重派。

prompt 以**路径清单**方式列出（禁止贴入文件内容；与 Step 1 首次派发同源，仅在 #11/#12/#13 增量整改约束）：

1. 方法论路径 `pm-workflow/rules/agent_methodology.md`
2. 参数声明路径 `pm-workflow/rules/agent_parameters.md`（PM Agent 列）
3. 角色规范路径 `pm-workflow/agents/AI产品经理_Agent.md`（**分节读取**——行选择按 §大文件分节读取规范 SOP 第 1 步子角色规则，禁全读）
4. 硬规则清单路径 `pm-workflow/rules/rule_hard_constraints.md`（**分节读取**——通用行 + 本阶段/角色行，详 §大文件分节读取规范）
5. 需求简述路径 `需求简述.md`
6. 产品定义路径（从 state.md 读取，通常为 `outputs/产品定义_[产品名]_latest.md`）
7. state.md 路径 `process_record/state.md`
8. 任务卡模板路径 `pm-workflow/rules/task_card_template.md`
9. 全局约束路径 `pm-workflow/rules/proto_contract.md`
10. pub 组件索引路径 `pm-workflow/rules/bujue-design-system/pub_components_index.md`
11. proj 协议路径 `pm-workflow/rules/proj_component_protocol.md`
12. **【整改专属】审核报告路径** `process_record/reviews/stage4_scaffold_review.md`（**整改意见唯一来源**——PM 必须 Read 此文件取整改清单，不得猜测）
13. **【整改专属】当前蓝图产物路径**：`process_record/tasks/scaffold.json` + 各模块任务卡 `process_record/tasks/task_M[XX]_*.md`（PM 必须 Read 当前已产出的蓝图作为修改基线，**不得从零重写**）
14. 进度文件路径 `process_record/progress/stage4_[产品名]_plan.md` + 「整改场景特殊说明」（详见下方指令）

prompt 中明确注明（**整改专属指令，必须全部写入 prompt**）：

```
角色：任务规划 Agent — 整改场景

[Must] 开工前必须逐个 Read 上述路径清单中的所有文件（含方法论 + 参数声明 + 角色规范 +
审核报告 + 当前蓝图产物），读完后再制定分步计划并动手；禁止仅凭路径或文件名猜测内容。

[Must] 整改范围限定：
- 仅整改 stage4_scaffold_review.md 审核报告中明确指出的具体项
- 不重做模块拆分（已通过审核的 TP1 模块边界 / 编号体系不得变动）
- 不扩大修改范围至审核未涉及的部分（防止引入新错误）

[Must] 进度文件特殊说明：
- 进度文件 stage4_[产品名]_plan.md 中 TP1-TP5 全部已为 [x]——这是整改场景，
  不按 X1「从第一个 [ ] 继续」的中断恢复规则处理
- PM 须在进度文件「整改轮次」段（不存在则在 TP5 行下方追加）新增一条：
  `## 第 N 轮整改（本步独立计数，不占用终审 3 次额度）`
  下列出本轮整改对应的审核条目编号 + 修改前后对照
- 修复完毕后将本轮整改条目逐项标 [x]，但 TP1-TP5 主步骤仍保持 [x] 不重置

[Must] 独立计数告知：
- 本轮整改属于「Step 1.X 中段审核循环」，**不计入阶段 4 终审 3 次重做额度**
- Step 1.X 自身循环上限独立计数（≤3 轮），超过须按 CLAUDE.md「关键自动化规则」升级处理
- 不要因为"已用 1/3 额度"心理预设而主动建议升级，按整改要求继续推进即可

[Must] 整改产出：
- 修复后的 scaffold.json + 修复后的 task_M[XX]_*.md（仅修改受影响模块的任务卡）
- 写入完成标记后通知编排器重派 Step 1.X Supervisor 中段审核
```

**编排器路由约束**：FAIL 收到后必须按本模板派发，**不得**简化为"贴整改意见 + 让 PM 重做"。如果编排器自身无 Read 角色规范的边界（详见「[Must] 编排器读文件边界」），不应基于"心理省略"裁剪本模板。

**Step 1.5｜编排器执行骨架生成脚本（编排器直接执行）**
```bash
python pm-workflow/scripts/gen_scaffold.py
```
- 前置：Step 1.X 必须 PASS；否则脚本即使能运行，也违反工作流纪律
- 脚本读取**已审核通过**的 `process_record/tasks/scaffold.json`，输出：
  - `outputs/spec_[产品名]_latest.md`（空骨架，供 Foundation Agent 追加）
  - `outputs/prd_[产品名]_latest.html`（带全量导航 + 模块占位注释的骨架）
  - **【v2.0 新增】**`process_record/drafts/spec_M[XX]_draft.md`（每模块 spec 草稿骨架，含固定子章节占位；WE-H：S2.M[XX].1 per-page 槽为 override-only 纯注释 marker）
  - **【WE-H 新增，SSOT #41】**`process_record/drafts/spec_foundation_draft.md`（Foundation 范式骨架草稿，据 `scaffold.page_archetypes` 每范式一 ```skeleton 占位，Foundation 子阶段二填）
  - **【v2.0 新增】**`process_record/drafts/prd_M[XX]_draft.html`（每模块 prd 草稿骨架，含 FRAME 占位 + OWNER-INFO 注释）
  - **【v2.0 新增】**任务卡「候选组件清单」段：从 scaffold.candidate_components 自动衍生写入
- 脚本输出模块摘要（模块数、页面数、状态帧数 + 候选组件统计），编排器确认无误后进入 Step 2

**Step 2｜派发 Foundation Agent**
- prompt 以**路径清单**方式列出（禁止贴入文件内容）：
  1. 方法论路径 `pm-workflow/rules/agent_methodology.md`
  2. 参数声明路径 `pm-workflow/rules/agent_parameters.md`（PM Agent 列）
  3. 角色规范路径 `pm-workflow/agents/AI产品经理_Agent.md`（**分节读取**——行选择按 §大文件分节读取规范 SOP 第 1 步子角色规则，禁全读）
  4. 硬规则清单路径 `pm-workflow/rules/rule_hard_constraints.md`（**分节读取**——通用行 + 本阶段/角色行，详 §大文件分节读取规范）
  5. scaffold.json 路径 `process_record/tasks/scaffold.json`
  6. 产品定义路径（从 state.md 读取）
  7. **阶段 2 功能规划路径**（从 state.md 读取,通常为 `outputs/功能规划_[产品名]_latest.md`）—— **Foundation 写 spec §3.4 业务流程图的 [Must] SSOT 真源**（迁入自阶段 2 §二全部 mermaid 块,详见 proto_spec_md.md §3.4）
  8. `pm-workflow/rules/proto_contract.md`
  9. `pm-workflow/rules/proto_spec_md.md`
  10. `pm-workflow/rules/prd_expression_standard.md`
  11. `pm-workflow/rules/bujue-design-system/tokens.md`
  12. 进度文件路径 + 存在性检查指引
  13. **【WE-H，SSOT #41】Foundation 范式骨架草稿路径** `process_record/drafts/spec_foundation_draft.md`（gen_scaffold Step1.5 已据 `scaffold.page_archetypes` 预生成每范式 ```skeleton 占位）
- prompt 中明确注明：「角色：Foundation Agent」，并加入「**[Must]** 开工前请逐个 Read 上述路径清单中的所有文件，读完后再动手；
  - **§3.0 页面层级架构（SSOT 双锚 #38）：禁止 Foundation 凭空写或手画层级图**。Foundation 写 spec 区块1 时，仅在区块1 顶部（§3.1 全量页面清单**之前**）写一行占位 marker `<!-- [SITEMAP-3.0] -->`，**§3.0 真实内容不写**——它由 `assemble.py`（Step4）从 `scaffold.json` 现场派生替换该 marker（详见 `proto_spec_md.md §3.0`）。漏写 marker → precheck_stage4 check① FAIL 阻断 Step 7 自审；
  - **【WE-H，SSOT #41 / S4-32】范式骨架（per-archetype 单源）**：在 `spec_foundation_draft.md`「## 范式骨架」段内，**按范式逐个**把每个 `- **<aid> 范式名**` 锚行下的 ```skeleton 占位替换为该范式代表性 2D 平面布局骨架——一次定义、所有引用该范式的页复用（下游 Step3/5 默认复用、不逐页画）。**[Must]**：不动 `- **<aid>**` 锚行；首行字面保留固定免责注释；仅 `<div>` + `class∈{sk-page,sk-row,sk-col,sk-region}` + 属性仅 `data-r/data-w/data-h`；每个 `data-r` 必 ⊆ 该范式 `regions[].slot∪extension`（#39 权威）；禁真实组件标签/inline style/真实文案/嵌套>3层；跨端实质发散范式才拆 ` ```skeleton:{phone|desktop|tablet|h5|mp} `（EITHER 1 agnostic OR ≥1 per-platform、不混用）。assemble 自动派生注入 spec §3.0「范式骨架」子节 + PRD sk-askel 画廊；详 `proto_spec_md.md §四`；
  - **§3.4 业务流程图须按 proto_spec_md.md §3.4 [Must] 来源约束 + 完整性约束直接迁入阶段 2 §二全部 mermaid 块（含 2.1 主流程 / 2.2 跨角色交互 / 2.3 补充流程）,禁止凭空写或省略——SSOT 双锚 #30 precheck_stage4 会校验 mermaid 数对称,漏迁入将 FAIL 阻断 Step 7 自审**；
  - **PRD 规格区须含 A-04.2 业务流程图 section**（工程视角,与 A-04 用户旅程互补,不可互替）：填 `<section id="spec-business-flow">`,源同 spec §3.4（阶段 2 §二）,按 `prd_expression_standard.md §A-04.2` 三类子 spec-block + 双视图 toggle + 多角色 subgraph 泳道渲染;复用 A-04.1 已有 CSS class（`journey-toggle` / `journey-view-btn` / `journey-table-view` / `journey-flow-view`）+ JS 函数（`switchJourneyView`）,无需重复实现**；
  - **写 S0.5 / 规格区时,产品定义中以下结构化 [Must]/[Should] 子节须完整迁入,不得摘要**（参 SSOT 双锚 #28 真源 tmpl_产品定义.md）：
    - §3 用户画像 — 含每个角色块 `**角色 ID**：[role-N]` + `**角色名**：[xxx]` 结构化字段（SSOT 双锚 #24,precheck_stage4 校验）
    - §4 权限矩阵 — 完整表格（功能点 × 各角色 ✅/❌）
    - §5 用户旅程 — 含 **§5.1 [Must] 旅程步骤表**（结构化主源 9 列）+ **§5.2 [Must] 多角色参与矩阵**（≥ 2 角色时必填,4 列）+ **§5 [Should] 多旅程组织规则**（≥ 2 条独立旅程时按 FMT-4 拆分）
    - §5.5 业务流程图 — **mermaid 块（5.5.1 主流程 / 5.5.2 跨角色 / 5.5.3 补充）必须由阶段 2 §二原样迁入**（SSOT #30 派生约束,precheck_stage3.check_section_5_5 校验数对称）;Foundation 在 S0.5 写产品规格区时此处不渲染（spec §3.4 + PRD A-04.2 是阶段 4 派生路径,与本节并列从阶段 2 §二派生）
    - §6 页面路由 — 含路由表 8 列 + **§6 [Should] 复杂跳转 mermaid 补充**（FMT-5,有跨页判断流时必有）
    - §13 非功能需求 — 含 **[Must] 体验意图填写格式**（FMT-6 四要素 `[业务角色] 在 [触发场景] 时 [遭遇的问题]，导致 [可量化后果]`）
  - 上述结构化段在产品定义中已由 precheck_stage3 强制兜底（章节齐全 + 表格列 + FMT 段存在）,Foundation 写 S0.5 时按原结构保留行数与字段,**禁止压缩为段落叙述**——下游 PRD A-04 用户旅程 / 权限矩阵 / 用户画像卡片渲染依赖这些结构化输入」
- Foundation 完成后，进入 Step 2.5

**Step 2.5｜派发项目组件识别 PM Agent**
- prompt 以**路径清单**方式列出（禁止贴入文件内容）：
  1. 方法论路径 `pm-workflow/rules/agent_methodology.md`
  2. 参数声明路径 `pm-workflow/rules/agent_parameters.md`（PM Agent 列）
  3. 角色规范路径 `pm-workflow/agents/AI产品经理_Agent.md`（**分节读取**——行选择按 §大文件分节读取规范 SOP 第 1 步子角色规则，禁全读）
  4. 硬规则清单路径 `pm-workflow/rules/rule_hard_constraints.md`（**分节读取**——通用行 + 本阶段/角色行，详 §大文件分节读取规范）（必读 S4-17 / S4-18 / S4-19）
  5. **proj 组件协议路径 `pm-workflow/rules/proj_component_protocol.md`**（必读，本步执行的核心规范）
  6. **pub 组件索引路径 `pm-workflow/rules/bujue-design-system/pub_components_index.md`**（必读，本步双触发判定的参照系；A 触发的 pub 模板覆盖判断 + B 触发的能力缺口判断都基于本索引）
  7. scaffold.json 路径 `process_record/tasks/scaffold.json`
  8. 产品定义路径（从 state.md 读取）
  9. 阶段3 各模块任务卡路径列表 `process_record/tasks/task_M[XX]_*.md`（逐一 Read，识别跨模块复用模式）
  10. 进度文件路径 + 存在性检查指引
- prompt 中明确注明：「角色：项目组件识别 Agent」，并加入「**[Must]** 开工前请逐个 Read 上述路径清单中的所有文件；本步严格按 `proj_component_protocol.md §一` 双触发条件判定（A 跨模块复用 / B 能力缺口，任一成立即触发派生），不擅自硬造组件，也不漏识别能力缺口；写入 `outputs/components_[产品名]_latest.md` 时**必须**先按 `proj_component_protocol.md §二.1` 落地索引段（A/B/C/D 4 张表），再写详情段——即使本期无 proj 组件，索引段框架也不得省略」
- **判定流程**（PM 须按此顺序执行）：
  1. **扫描 A 触发因素（跨模块复用）**：扫 scaffold.json 全部模块 + 产品定义 §7 功能 / §9 数据字段，对照 `pub_components_index.md §三` 组件总表，识别"在 ≥ 2 个模块出现 + 字段一致 + 现有 pub 组件 slot/语义无法直接覆盖"的候选
  2. **扫描 B 触发因素（能力缺口）**：逐模块对照产品定义业务需求与 `pub_components_index.md §五` D1-D5 能力反查表，识别"pub 组件存在但字段/状态/交互/语义/约束不足以覆盖本次需求"的候选（**即使仅在单模块出现也算**）。`pub_components_index §四 / §五` 中标 `⚠ pub 无` 的能力，**直接列入 B 候选**
  3. 合并 A + B 候选清单（A+B 同时满足时按 A 处理，命名沿用跨模块语义）
  4. 写 §二.1 索引段 4 张表（A active / B deprecated / C proposed-promote / D 按模块反查）；本期为首次构建产品时 B 表必为空、C 表通常为空、D 表必填全部模块
  5. 对每个候选组件，按 `proj_component_protocol.md §二.2` Schema 模板逐项填写详情段
  6. 按 `proj_component_protocol.md §三` 8 项状态清单**逐条**判定 needed + reason
  7. 全文写入 `outputs/components_[产品名]_latest.md`
- **跳过条件**（A 和 B 都不触发时）：
  - scaffold.json 仅 1 个模块 + pub 索引覆盖全部业务需求 → 跳过详情段
  - 多模块但无重复 pattern + pub 索引覆盖全部业务需求 → 跳过详情段
  - 跳过时 `outputs/components_[产品名]_latest.md` **仍须**保留 §二.1 索引段 4 张表（A/B/C 表内写"本期无新建 proj 组件"，D 表填全部模块的"引用 proj 组件"列为空），并在文件头附**触发因素扫描结果**（A 候选 0 个 + B 候选 0 个 + 已对照的 pub 索引版本号）。**不**为产出而硬造组件
- **不要遗漏能力缺口**：单模块产品下若 pub 索引不能覆盖某项业务需求（pub 索引中标 `⚠ pub 无`），**必须**作为 B 触发派生 proj，不可因为"只有一个模块"就跳过
- PM 输出：`outputs/components_[产品名]_latest.md`（含 0 至 N 个 proj 组件 schema）
- 完成后，进入 Step 3

**Step 3｜派发各模块 Spec Agent（无依赖的模块可并行）**
- **[Must] logic-only 模块跳过派发（SSOT #50）**：编排器派发前先过滤 `pages` 非空模块，**`pages=[]` 的 logic-only 模块不派 Spec Agent**——其无独立 UI 页面（业务逻辑层 / API 层 / 数据契约层），spec 章节不生成；其 UI 表现已由 `ui_carrier_modules` 指向的承载模块在 Step 3 派发时覆盖（承载模块的状态帧 / 触点 / 数据流中体现 logic-only 模块逻辑）。详 §scaffold v2.0 schema「logic-only 模块说明」段。
- 每个模块单独一次派发；依赖其他模块的模块须等被依赖模块完成后再派发
- **[Must] 进度文件并发约束**：按 `AI产品经理_Agent.md §五「模块进度并发纪律（SSOT 单一权威源）」`执行（仅写本模块子文件；禁止 PM 写主文件 MS-/MP- 行；编排器单线程勾选；调整须先改 SSOT 源）。
- prompt 以**路径清单**方式列出（禁止贴入文件内容）：
  1. 方法论路径 `pm-workflow/rules/agent_methodology.md`
  2. 参数声明路径 `pm-workflow/rules/agent_parameters.md`（PM Agent 列）
  3. 角色规范路径 `pm-workflow/agents/AI产品经理_Agent.md`（**分节读取**——行选择按 §大文件分节读取规范 SOP 第 1 步子角色规则，禁全读）
  4. 硬规则清单路径 `pm-workflow/rules/rule_hard_constraints.md`（**分节读取**——通用行 + 本阶段/角色行，详 §大文件分节读取规范）
  5. 本模块任务卡路径 `process_record/tasks/task_M[XX]_[模块名].md`（PM 自行从任务卡「规格内容来源」表获取产品定义对应章节，自行 Read 取用）
  6. 产品定义路径（从 state.md 读取）
  7. `pm-workflow/rules/proto_contract.md`
  8. `pm-workflow/rules/proto_spec_md.md`
  9. **pub 组件索引路径 `pm-workflow/rules/bujue-design-system/pub_components_index.md`**（必读，spec 中引用的所有 pub 组件 id 必须能在本索引中找到）
  10. 项目组件库路径 `outputs/components_[产品名]_latest.md`（**Step 2.5 产物**；先读其顶部索引段 §二.1 D 表确认本模块已派生哪些 proj 组件，再在 spec 中按 id 引用，不重复声明 schema）
  11. **模块子进度文件路径** `process_record/progress/stage4_[产品名]_M[XX]_plan.md` + 「存在则从第一个 `[ ]` 继续，不存在则按 PM Agent 角色规范的「模块子文件结构」创建」指引
  12. **scaffold.json 路径 `process_record/tasks/scaffold.json`**（提议2，SSOT #39——本模块各页 `archetype` + 顶层 `page_archetypes` 范式定义的权威源；**现场读，不依赖任何预烘焙副本**，H1=(c) 按引用消费）
  13. **fb-design-query skill 路径 `pm-workflow/skills/fb-design-query/SKILL.md`**（**`[Should]` Spec Agent 子阶段三**；触点表 / 状态描述 / 业务规则涉及具体组件语义时按 Q1-Q8 决策树走结构化路径，避免 spec 文字与下游 PRD 组件选型脱节；SSOT #52）
- prompt 中明确注明：「角色：M[XX] Spec Agent，只写 process_record/drafts/spec_M[XX]_draft.md + 自己的模块子进度文件」，并加入「**[Must]** 开工前请逐个 Read 上述路径清单中的所有文件，读完后再动手；禁止仅凭路径或文件名猜测内容；本模块若使用 pub 组件，按 `fb-*` id 引用并以 pub_components_index 为权威；若使用 proj 组件，按 `proj.L{tier}.{name}` id 引用并以 components_[产品名]_latest.md 索引段 D 表为权威，不重复声明 schema；**禁止写主进度文件 stage4_[产品名]_plan.md 的 MS-/MP- 行**；**[Must] 提议2 容纳性二值校验（填每页前强制前置，SSOT #39）**：从 scaffold 读本页 `archetype` 解析 `page_archetypes` 定义 → 枚举本页强制元素（Step3 输入 = 本页 scaffold states + 产品定义对应功能点；触点本步才产出，不计入）→ 逐元素核对范式 regions/extension 有无可容纳 slot → 二值：①全部有归属 = PASS，严格照范式结构填、零自由度（"我想换布局"不构成偏离理由）；②任一强制元素无 slot 且无扩展位 = FAIL，**不填该页**，按 `proto_spec_md.md`「页面结构范式契约」定长格式产出冲突报告写入模块子进度文件「## 页面结构容纳性校验记录」段，仅阻塞该页、继续本模块其他页，并回报编排器（编排器复用 SSOT #31 NB 上报 SOP 走自然语言路径B 派 PM 改 scaffold.page_archetypes）；③无论 PASS/FAIL 均须把每页一行定长记录写入该段（precheck S4-30 校验记录齐全+覆盖）；**[Must] SSOT #41 / S4-32 骨架屏（WE-H per-archetype，默认复用范式骨架不逐页画）**：范式骨架已由 Foundation 子阶段二在 `spec_foundation_draft.md`「## 范式骨架」按范式填一次（单源）——`S2.M[XX].1` 每页 per-page 槽是纯注释 marker，**默认页直接复用其 `archetype` 范式骨架，你无需在此填任何 ```skeleton**（assemble 自动渲帧旁「结构范式」chip 深链 sk-askel-<aid>）；**仅当本页 2D 排布确无法套用其范式骨架时**（罕见——优先回报改 #39 archetype 路径 i/ii，仅排布/占比根本不同才 override）才在该页 marker 下新增一个 ```skeleton 覆盖块（首行字面保留固定免责注释、仅 `<div>`+`class∈{sk-page,sk-row,sk-col,sk-region}`+属性仅 `data-r/data-w/data-h`、每个 `data-r` 必 ⊆ 本页 archetype `regions[].slot∪extension`、禁真实组件标签/inline style/真实文案/嵌套>3层、跨端发散可拆 `:{phone|desktop|tablet|h5|mp}`）；PRD 侧禁另写骨架；完成通知须列 override 页数（默认 0）+ 理由；详 `proto_spec_md.md §四「页面结构（骨架屏）」`」
- 模块完成后，**编排器**单线程勾选主文件 `MS-M[XX]` 行
- 所有模块 spec 草稿完成后，进入 Step 4

**Step 4｜执行 spec.md 拼装脚本（编排器直接执行）**
```bash
python pm-workflow/scripts/assemble.py spec
```
- 按 scaffold.json 模块顺序，将所有 `spec_M[XX]_draft.md` 追加至 `outputs/spec_[产品名]_latest.md`（Foundation 已写入 S0+S0.5+S1），再追加变更记录表 + 问题清单占位
- 更新进度文件 AS 步骤 `[x]`
- 完成后进入 Step 5
- **手改保护**：脚本会比对 `process_record/versions/.assemble_fingerprints/[产品名]_spec.txt` 与当前 `outputs/spec_*_latest.md` 的 sha256；若两次 assemble 之间 outputs 被手改且 hash 不一致 → ERROR 中止。处理路径见 `assemble.py` 错误信息顶部（同步回 drafts / `--force-overwrite` 强制 / 删 sidecar 跳过）。/issueReview 等调整流程产生的修改应先回到对应 `spec_M[XX]_draft.md`，再重跑 Step 4，避免依赖 `--force-overwrite`

**Step 5｜派发各模块 PRD Agent（无依赖的模块可并行）**
- **[Must] logic-only 模块跳过派发（SSOT #50）**：同 Step 3 — 编排器派发前过滤 `pages` 非空模块，`pages=[]` 的 logic-only 模块不派 PRD Agent（其 UI 已由 `ui_carrier_modules` 承载模块的 PRD 覆盖）。详 §scaffold v2.0 schema「logic-only 模块说明」段。
- **[Must] R8 layer 2：派发前编排器跑渲染契约落地（SSOT #77，治 §8 批量摊薄漏搬运）**：Step 4 spec 完成后、**首次**派发 PRD Agent 前，编排器跑一次 `python3 pm-workflow/scripts/gen_render_contract.py --write`（读 spec+scaffold → per-frame 渲染契约 checklist 落进各任务卡 `[RENDER-CONTRACT-START]…[END]` 块，全 `[ ]` 新契约）。**只跑一次**——之后 PRD Agent 逐条勾 `[x]`，编排器**不再重跑**（重跑重置勾态 = 新契约语义，仅 scaffold/spec 变更才重跑）。脚本「忠实转录 spec 权威列禁推断」+ 含内嵌帧 + 确定性。
- 每个模块单独一次派发
- **[Must] 进度文件并发约束**：按 `AI产品经理_Agent.md §五「模块进度并发纪律（SSOT 单一权威源）」`执行（同 Step 3，本步聚焦 MP-M[XX] 行）。
- **[v2.0] [Must] owner 状态由编排器从 scaffold.owner_assignments 读出后写入 prompt**（不让 PRD Agent 自己判断）：编排器 Read `process_record/tasks/scaffold.json`，遍历全部模块 `owner_assignments`，对**当前派发模块**生成「本模块 proj 归属」段并嵌入 prompt：
  ```
  本模块 M[XX] 对本期 proj 组件的归属（由编排器从 scaffold.owner_assignments 读出）：
  - proj.L2.product-card → owner（必须写完整 PROJ-CSS：base + 全部 needed:yes 状态 modifier）
  - proj.L1.rich-textarea → non-owner（仅引用 class，禁止重复声明 CSS）
  - proj.L0.tag-badge → 不使用
  ```
  PRD Agent **直接照办**，不再自己读 components A 表判断 owner。
- prompt 以**路径清单**方式列出（禁止贴入文件内容）：
  1. 方法论路径 `pm-workflow/rules/agent_methodology.md`
  2. 参数声明路径 `pm-workflow/rules/agent_parameters.md`（PM Agent 列）
  3. 角色规范路径 `pm-workflow/agents/AI产品经理_Agent.md`（**分节读取**——行选择按 §大文件分节读取规范 SOP 第 1 步子角色规则，禁全读）
  4. 硬规则清单路径 `pm-workflow/rules/rule_hard_constraints.md`（**分节读取**——通用行 + 本阶段/角色行，详 §大文件分节读取规范）
  5. 本模块任务卡路径 `process_record/tasks/task_M[XX]_[模块名].md`
  6. **任务卡模板路径** `pm-workflow/rules/task_card_template.md`（供 PM 反查模块 5「执行要求」段的草稿格式 / FRAME / PROJ-CSS 约定与验收清单，避免漏 FRAME 标记或写错占位）
  7. 本模块 spec 草稿路径 `process_record/drafts/spec_M[XX]_draft.md`
  8. **pub 组件索引路径 `pm-workflow/rules/bujue-design-system/pub_components_index.md`**（必列；PM 用本索引锁定要用的 fb-* 组件 id 后，再去 `fb-fallback-manifest.md` 取对应 HTML 模板与 class 调用方式）
  9. 项目组件库路径 `outputs/components_[产品名]_latest.md`（**Step 2.5 产物**；先读其 §二.1 索引段 D 表确认本模块用到的 proj 组件，再读对应详情段，按 schema 在 PRD 中渲染状态展示区与模块帧实例）
  10. **proj 组件协议路径 `pm-workflow/rules/proj_component_protocol.md`**（**当 components 文件含至少一个 proj 组件时必列**；空文件可省略）
  11. 按「阶段4规范文件传入策略」确定的规范文件**路径清单**（必列 `proto_contract.md` + `prd_expression_standard.md` + `tokens.md` + `empty-loading.md` + `fb-fallback-manifest.md`；按产品覆盖端口列入 `proto_platform_*.md` / `proto_cross_platform.md`；按本模块实际组件列入 `components/*.md`；**严格按需，不得保险起见全列**）
  12. **模块子进度文件路径** `process_record/progress/stage4_[产品名]_M[XX]_plan.md` + 「存在则从第一个 `[ ]` 继续，不存在则按 PM Agent 角色规范的「模块子文件结构」创建」指引
  13. **scaffold.json 路径 `process_record/tasks/scaffold.json`**（提议2，SSOT #39——本模块各页 `archetype` + 顶层 `page_archetypes` 权威源；现场读，不依赖预烘焙副本，H1=(c)）
  14. **fb-design-query skill 路径 `pm-workflow/skills/fb-design-query/SKILL.md`**（**`[Must]` PRD Agent 子阶段五必读**；写每段 PRD HTML 前对每个 `class="fb-*"` 组件引用 / 设计 token / 端规范适配按 Q1-Q8 决策树**逐题答**走结构化路径定位精确组件 + 反 pattern + 关联场景，每次查询填查询记录到模块子进度文件「## fb-design-query 查询记录」段；治 PM 凭直觉选 class 致 v2 三 class 16 处误叠加同型 / 推断"pub 缺某能力"未走端规范核查致 NB-pub-phone-bar 错诊复现；SSOT #52）
- prompt 中明确注明：「角色：M[XX] PRD Agent，只写 process_record/drafts/prd_M[XX]_draft.html + 自己的模块子进度文件，禁止写入 html/head/body 标签」，并加入「**[Must]** 开工前请逐个 Read 上述路径清单中的所有文件（含 spec 草稿 + pub_components_index.md + components_[产品名]_latest.md），读完后再动手；prd 内容须以 spec 草稿为唯一来源；**本模块涉及的 proj 组件须按 `proj_component_protocol.md §四/§五/§六` 完成 CSS 抽象定义、独立状态展示区、模块帧引用三件事，禁用 inline style，禁用未在 `<style>` 块定义的 class**；**所用 pub 组件 class 必须在 pub_components_index 中存在**，禁用未登记的 fb-* class；**禁止写主进度文件 stage4_[产品名]_plan.md 的 MS-/MP- 行**；**[Must] 提议2 容纳性二值校验（绘每页帧前强制前置，SSOT #39）**：从 scaffold 读本页 `archetype` 解析 `page_archetypes` → 枚举本页强制元素（Step5 输入 = 本页**完整 spec 草稿**：状态枚举 + 触点表 + 字段绑定，触点此时已由 Step3 产出）→ 逐元素核对范式 regions/extension 有无可容纳 slot → 二值：①全有归属 = PASS，严格照范式结构绘帧、零自由度；②任一无 slot 且无扩展位 = FAIL，**不绘该页帧**，按定长格式写冲突报告入模块子进度文件「## 页面结构容纳性校验记录」段，仅阻塞该页、继续本模块其他页，回报编排器（复用 SSOT #31 → 路径B 改 scaffold.page_archetypes）；③每页一行定长记录必写入该段（precheck S4-30 校验齐全+覆盖）；**[Must] R8 layer 2/3 渲染契约逐条强制执行 + 打标记（SSOT #77，治 §8 注意力摊薄漏搬运）**：任务卡 `[RENDER-CONTRACT-START]…[END]` 块「机械可核」段每行 `- [ ] <id> …` 是本模块**必画清单**——**逐条渲染、每完成一项立即勾 `[ ]→[x]`（复用本文件分步执行规范，禁批量勾选）**，并在渲染的 DOM 元素上打对应标记（触点 `data-tp="<canonical-id>"`（复用 §6.1 既有 [Must]）/ 字段 `data-field="<name>"`，详 `prd_expression_standard.md §6.1/§6.2` 渲染契约标记约定）。**勾是自报、标记是物证**——机械层 `check_render_contract` 验标记不验勾 + 交叉核对勾↔标记（防自报注水，memory feedback_pm_self_reported_precheck_numbers）；「人工对照」段（§11/NB 模糊项）**不打标记**、归 Supervisor 抽样核」
- **草稿格式约束（详见 `prd_expression_standard.md §9.2 机器标记 audit trail` + `proj_component_protocol.md §五.1`）**：
  - 草稿头部（第一个 FRAME 之前）可选写 `<!-- [PROJ-CSS-START] -->...<!-- [PROJ-CSS-END] -->` 块，包裹本模块 proj 组件的 CSS 定义；首个使用某 proj 的模块写完整 CSS，其他模块仅引用 class
  - 之后写多组 `<!-- [FRAME: prd_id] -->...<!-- [/FRAME: prd_id] -->` 包裹的帧内容，prd_id 与 scaffold.json 中本模块全部 `prd_id` 一一对应
  - **禁止**写 `<section>...</section>` 外壳 / `<html>/<head>/<body>` 标签 / 拼装产物中的 `[FRAME-START/END]` / `[FB FALLBACK START/END]` / `[SPEC-MODULES-START/END]` 等机器标记（这些由脚本写入并维护）
- 模块完成后，**编排器**单线程勾选主文件 `MP-M[XX]` 行
- 所有模块 prd 草稿完成后，进入 Step 6

**Step 6｜执行 prd.html 拼装脚本（编排器直接执行）**
```bash
python pm-workflow/scripts/assemble.py prd
```
- 将每个 `prd_M[XX]_draft.html` 替换 `outputs/prd_[产品名]_latest.html` 中对应的 `<!-- [MODULE M[XX]: 模块名] -->` 占位注释
- 更新进度文件 AP 步骤 `[x]`
- 完成后进入 Step 6.5
- **手改保护**：同 Step 4，脚本比对 `process_record/versions/.assemble_fingerprints/[产品名]_prd.txt` 与当前 `outputs/prd_*_latest.html` 的 sha256；不一致 → ERROR 中止。重入区（FRAME / PROJ-CSS / FB FALLBACK 标记内）的手改会被覆盖；保留区（产品规格区 / 导航等标记外内容）会被原样保留——错误信息内会列出三种处理路径。/changeRequest 与 /issueReview 涉及 PRD 改动时应改对应 `prd_M[XX]_draft.html` 草稿，由本步重新拼装注入，不要直接改 outputs

**Step 6.5｜执行自审前置机械检查脚本（编排器直接执行，减轻 Supervisor 审核负担）**
```bash
python pm-workflow/scripts/precheck_stage4.py
```
- 脚本校验：scaffold 编号体系、prd.html 占位残留、prd.html ↔ scaffold 一致性（所有状态帧 section 就位、产品规格区 9 节齐全,含 A-04.2 业务流程图）、showSection 目标完整性、Mermaid 局部豁免（journey/flow 关键字 section）、HTML 基本结构、spec.md 模块覆盖与尾部章节
- **退出码 0**（无错误，可能有警告）→ 进入 Step 7 自审
- **退出码 1**（存在错误）→ **禁止进入 Step 7**，编排器须按错误清单分辨根因：
  - 若为 prd/spec 结构问题（占位残留、section 缺失、showSection 悬空、Mermaid 出现）→ 派发对应模块的 PRD Agent 或 Spec Agent 修复草稿，然后重新执行 Step 4/Step 6 拼装并重跑 Step 6.5
  - 若为 scaffold.json 编号问题（格式错误、重复、层级不一致）→ 原则上不应发生（任务规划阶段锁定后不得改动），一旦触发须升级为 `/changeRequest` 流程
- **警告**不阻断流程，但须记录到 state.md「非阻塞性问题清单」开放表（状态 ⏳ 待确认），供 Supervisor 复核
- 机械检查通过后才进入 Step 7；未通过时进入 Step 7 视为违反硬规则

**Step 7｜派发自审 PM Agent**
- prompt 以**路径清单**方式列出（禁止贴入文件内容）：
  1. 方法论路径 `pm-workflow/rules/agent_methodology.md`
  2. 参数声明路径 `pm-workflow/rules/agent_parameters.md`（PM Agent 列）
  3. 角色规范路径 `pm-workflow/agents/AI产品经理_Agent.md`（**分节读取**——行选择按 §大文件分节读取规范 SOP 第 1 步子角色规则，禁全读）
  4. 硬规则清单路径 `pm-workflow/rules/rule_hard_constraints.md`（**分节读取**——通用行 + 本阶段/角色行，详 §大文件分节读取规范）
  5. 最终 spec.md 路径（从 state.md 读取，通常为 `outputs/spec_[产品名]_latest.md`）
  6. 最终 prd.html 路径（从 state.md 读取，通常为 `outputs/prd_[产品名]_latest.html`）
  7. `pm-workflow/rules/proto_contract.md`
  8. 进度文件路径 + 存在性检查指引
- prompt 中明确注明：「角色：自审」，执行 §5.4 自审检查清单 + `proto_contract.md` §十五 视觉自检清单，写入提交标记；并加入「**[Must]** 开工前请逐个 Read 上述路径清单中的所有文件」
- 自审通过后，立即派发 Supervisor Agent 审核（同正式流程规则一致）

> **并行注意事项**：Step 3 和 Step 5 支持并行，但每个模块的 spec 草稿必须在该模块 prd 草稿开始前完成（同模块内 spec → prd 顺序不可颠倒）。

#### 阶段四整改回退决策表

Supervisor 审核不通过 → 编排器按问题类别从下表确定回退入口，**不全量重跑**。每次整改计入"3 次重做"额度：

| 问题类别 | 典型表现 | 回退入口 | 配套动作 |
|---------|---------|---------|---------|
| **scaffold 编号 / 模块结构错误** | 编号冲突 / 模块漏分 / depends_on 引用不存在 | 升级为 `/changeRequest` 流程（非阶段 4 内部整改）| 任务规划锁定后不可直接改 scaffold.json；编排器须显式发起 changeRequest |
| **Foundation 内容错误**（S0/S0.5/S1 或产品规格区 9 节,含 A-04.2 业务流程图） | 内容不准 / 漏填 / 与产品定义不一致 | 重派 Foundation Agent（Step 2）+ 跳过 Step 1.5 | gen_scaffold.py 默认拒绝覆盖已写入骨架，需 PM 手动修正而非重新生成 |
| **proj 组件识别错误**（漏识别 / 索引段缺失 / schema 不全）| components_*.md 索引段不全 / 派生缺口未识别 | 重派项目组件识别 Agent（Step 2.5）| 完成后受影响的模块需重派 Step 3 或 Step 5（取决于该模块草稿是否已生成）|
| **单模块 spec 错误** | 状态枚举漏 / 触点编号错 / 跨模块引用不存在 | 重派该模块 Spec Agent（Step 3，仅该模块）+ 重跑 Step 4 拼装 | 同模块 prd 草稿存在 → 必须重派 Step 5 + 重跑 Step 6（spec 改了 prd 必跟改）|
| **单模块 prd 错误** | FRAME id 集合不匹配 / fb-* 未登记 / 视觉混乱 | 重派该模块 PRD Agent（Step 5，仅该模块）+ 重跑 Step 6 拼装 | spec 草稿不动 |
| **跨模块一致性错误**（触点 ID 双向不一致 / 字段绑定漂移）| precheck N4 / S4-21 报错 | 定位不一致的双方所属模块 → 同时重派该模块 Step 3 + Step 5 | 修完两端后必跑 Step 4 + Step 6 + Step 6.5 |
| **页面结构范式契约不兼容**（提议2，SSOT #39）| Step3/5 subagent 容纳性二值校验 FAIL，回报某页强制元素无 slot | 走自然语言**路径 B**（CLAUDE.md 调整意见规则）派 PM 改 `scaffold.page_archetypes`：系统性缺陷改共享范式定义（路径 i）/ 该页确属独立类型新建范式+改指针（路径 ii）→ 重派 Step 1.X 复审修订后契约 → 受影响模块重派 Step 3/5 | **禁重跑 gen_scaffold**（archetype 现场消费不预烘焙，H1=(c)）；受影响模块重派后必重跑 Step 4/6 assemble → §3.0/spec-sitemap 契约表自然刷新；广播受影响并行模块；非编号变更不升 /changeRequest（与 owner_assignments 路径 B 先例同构）|
| **机械检查失败但 Agent 已尽力**（拼写错 / 漏标记 / 占位残留）| precheck FAIL 后 PM 已修但仍报错 | 重派对应 Step 的 PM Agent + 复跑该 Step 的脚本 | 不计入"3 次重做"，因为是机械检查的二次确认 |
| **重做超过 3 次仍不通过** | 同一类问题 3 次整改未消除 | **升级处理策略**：拆分问题 / 列多套候选方案 / 提交产品总监裁决 | 不允许 PM 第 4 次重复同一思路 |

> **重跑链路核查**：每次回退后，编排器须按 `Step N → Step (N+1) → ... → Step 6.5` 顺序执行后续步骤；中间步骤（如 Foundation 没改但 spec 改了）的脚本（assemble.py）已设计为幂等可重入，无需顾虑。

---

派发 Supervisor Agent 时，prompt 以**路径清单**方式列出（禁止贴入文件内容）：
1. **方法论路径**（必列）：`pm-workflow/rules/agent_methodology.md`
2. **参数声明路径**（必列）：`pm-workflow/rules/agent_parameters.md`（Supervisor 列）
3. 角色规范路径 `pm-workflow/agents/AI产品主管_Agent.md`（**分节读取** — 按 §大文件分节读取规范（SSOT #81）fetch「全部 Supervisor」通用行 + 本阶段行，禁 Read 全文）
4. 原始需求路径 `需求简述.md`（或短文本需求直接贴入）
5. 待审核的成果文件路径（从 `process_record/state.md` 读取）。**阶段4终审例外（SSOT #82）**：`outputs/spec_*_latest.md` + `outputs/prd_*_latest.html` **禁一次性全文 Read**——按 `AI产品主管_Agent.md §4.4 终审读取与覆盖协议` 执行「机械全量（precheck 报告为输入）+ **分节全量语义审查**（默认：doc_query 分批遍历**全部**模块节 + 全部帧，帧清单 checklist 防漏；仅上下文受限时降级抽样）」，prompt 须显式注明此协议
6. 前序成果路径清单（阶段3/4 审核时 [Recommended] 用 `doc_query.py outline + fetch` 取涉审章节定位读，非整份全读）
7. 已决策约束路径 `process_record/decisions_ledger.md`（供 Supervisor Read 全文核对已解答 / 已决策条目，SSOT #18）+ state.md 路径 `process_record/state.md`（供读取产物清单和当前阶段 ⏳ 开放问题）
8. 审核进度文件路径 + 存在性检查指引
9. **硬性要求**（必须写入 prompt）：「**[Must]** 审核前请逐个 Read 上述路径清单中的所有文件（含方法论 + 参数声明），读完后再按方法论 T1-T6 + X1-X4 节奏出具审核意见；禁止仅凭路径或文件名猜测内容」。**分节例外（SSOT #81/#82）**：标注「分节读取」的角色规范 + 阶段4终审的 spec/prd 不 Read 全文，按对应协议 fetch/抽样；清单是下限，涉及未列章节先 outline 再补

> **变更场景额外要求**：在 `/changeRequest` 流程中派发 Supervisor 审核时，prompt 还需额外传入「变更编号」和「本次仅审核受变更影响的内容，不重审全文」的说明。

---

### 大文件分节读取规范（doc_query，SSOT #81）

> **治什么**：PM 派发基线 ~120k tokens 中 ~100k 是全阶段混装死重（`AI产品经理_Agent.md` + `rule_hard_constraints.md` 单任务只用 25-40%）。subagent 对下表 **5 个大文件**（角色规范 ×2 + rule_hard + `prd_expression_standard` + `proto_spec_md`，2026-06-11 阶段4 三杠杆批次扩展）**不 Read 全文**，改用 `python3 pm-workflow/scripts/doc_query.py`「outline 看架构 → fetch 必读章节」按需加载（阶段1 PM 实测 fetch 集 ≈ 11k vs 全读 ~60k tokens）。

**SOP（编排器派发时 + subagent 执行时）**：

1. **编排器**：派发 prompt 中对分节文件给出具体 fetch 命令 = **「全部 PM 任务 / 全部 Supervisor」通用行 ∪ 本任务行**的章节并集（从下表复制标题）。**阶段4 子角色派发的行选择（杠杆 a）**：「全部 PM 任务」行 ∪ 「阶段4 子角色通用」行 ∪ **该子角色行**（含其在 `prd_expression_standard` / `proto_spec_md` 的对应行）∪ rule_hard「通用 + 六」行（自审/审核场景再加「六.X 对照表」行）；**整改/通用任务未明确子角色时** → 用「阶段4 PM fallback」行；TP 另含 scaffold v2.0 schema 定点 fetch（杠杆 c，Step 1 第 13 项）
2. **subagent**：先 `outline <file>` 看全架构（~50 行，便宜）→ 按 prompt 的 fetch 命令取必读章节 → 任务涉及清单外内容时补 fetch / `locate <file> <关键词>` 反查所属章节
3. **预算闸**：fetch 多节合计超 `--max-tokens`（默认 25000）→ 脚本拒绝输出、吐各节尺寸 + 子目录，收窄到子节再取（防跨章共读撑爆上下文）
4. **fail-loud**：fetch「标题未命中」（章节改名/删除）→ **必须上报编排器**，禁静默跳过

**防漏读三层**（治"有必读文件清单、无必读章节清单 → 分节后漏读"风险）：① 下表是必读章节的 **L2 真源**（agent 不自行判断读什么）② `tests/test_section_coverage.py` 元测试守漂移——纳管文件（`MAPPED_FILES`，当前 5 个）新增章节未入下表任何行（含豁免行）→ pytest FAIL ③ 清单是**下限**（SOP 第 2 步可补读）。

**L1 大成果同样适用**（产品总监 2026-06-11 同意项 #3）：Supervisor 阶段 3/4 审核时，前序成果（需求分析/功能规划/产品定义）与 spec 用 outline + fetch **涉审章节**定位读，而非整份全读；跨章一致性大头已由 precheck 机械化（S3-05 / S4-21 / S4-46/47），语义审查只需小簇共读（2-4 章），超预算时主章全读 + 关联章 locate 摘录读。

#### 必读章节清单（元测试解析本表，行格式勿改；章节标题用唯一子串即可）

> **本表只管 5 个分节大文件的章节分配**；方法论 / 参数声明 / tmpl / proto 等其余必读文件仍按各派发清单以完整路径传递（本表非派发清单的替代）。

<!-- SECTION-MAP-START -->
| 任务 | 文件 | 必读章节（fetch 标题，`；` 分隔）|
|---|---|---|
| 全部 PM 任务 | pm-workflow/agents/AI产品经理_Agent.md | 一、角色身份；规则强度说明；二、核心行为准则；三、问题分级处理规则；三.7、引用 SSOT 真源纪律；5.0 通用前置自审；七、输出物格式要求 |
| 阶段1 PM | pm-workflow/agents/AI产品经理_Agent.md | 阶段一：需求分析；5.1 需求分析自审 |
| 阶段2 PM | pm-workflow/agents/AI产品经理_Agent.md | 阶段二：需求拆解与功能规划；5.2 功能规划自审 |
| 阶段3 PM | pm-workflow/agents/AI产品经理_Agent.md | 阶段三：产品定义；5.3 产品定义自审 |
| 阶段4 PM（整改/通用 fallback，未明确子角色时）| pm-workflow/agents/AI产品经理_Agent.md | 阶段四：交付文档；5.4 交付文档自审；六、PRD 撰写规范 |
| 阶段4 子角色通用（TP/FA/PI/S/P 派发均含）| pm-workflow/agents/AI产品经理_Agent.md | 组件检索 SOP；进度文件结构（模块化架构版；模块进度并发纪律；通用规则（模块化架构下全程适用）；子阶段七：自审与提交；5.4 交付文档自审；六、PRD 撰写规范 |
| 阶段4 TP 任务规划 | pm-workflow/agents/AI产品经理_Agent.md | 子阶段一：任务规划 |
| 阶段4 FA Foundation | pm-workflow/agents/AI产品经理_Agent.md | 子阶段二：Foundation Agent |
| 阶段4 PI 组件识别 | pm-workflow/agents/AI产品经理_Agent.md | 子阶段二.5：项目组件识别 |
| 阶段4 S 模块 Spec | pm-workflow/agents/AI产品经理_Agent.md | 子阶段三：模块 Spec Agent |
| 阶段4 P 模块 PRD | pm-workflow/agents/AI产品经理_Agent.md | 子阶段五：模块 PRD Agent |
| 调整意见 PM | pm-workflow/agents/AI产品经理_Agent.md | 三.5、调整意见处理 SOP；三.6、评估/推荐方案前边界自检 SOP；5.5 性能类 bug 首次诊断模板；（另加受影响阶段的「阶段N」+「5.N」节）|
| 全部 PM+Supervisor 任务 | pm-workflow/rules/rule_hard_constraints.md | 一、使用规范；二、跨阶段通用硬规则 |
| 阶段1 PM/Supervisor | pm-workflow/rules/rule_hard_constraints.md | 三、阶段1 硬规则 |
| 阶段2 PM/Supervisor | pm-workflow/rules/rule_hard_constraints.md | 四、阶段2 硬规则 |
| 阶段3 PM/Supervisor | pm-workflow/rules/rule_hard_constraints.md | 五、阶段3 硬规则 |
| 阶段4 PM/Supervisor | pm-workflow/rules/rule_hard_constraints.md | 六、阶段4 硬规则 |
| 阶段4 Supervisor + PM 自审（子阶段七）/整改 fallback | pm-workflow/rules/rule_hard_constraints.md | 六.X S4 规则与检查点对照表 |
| 阶段4 FA Foundation | pm-workflow/rules/prd_expression_standard.md | 文档架构：两大区域；区域 A：产品规格区；区域 B：交互原型区页面组织；九、主模板使用规则；多语言支持 |
| 阶段4 P 模块 PRD | pm-workflow/rules/prd_expression_standard.md | 元规范：视觉规范须达；全局 z-index 数值规范表；面板/浮层组件三大类规范；统一底栏操作组；组件父容器几何契约；状态帧强制结构；状态 Chip 导航；触点徽章；新增业务组件标注；内容分工规则；九、主模板使用规则；多语言支持；组件变更清单 section；UI 表达克制原则 |
| 阶段4 PI 组件识别 | pm-workflow/rules/prd_expression_standard.md | 新增业务组件标注；组件变更清单 section |
| 阶段4 终审 Supervisor | pm-workflow/rules/prd_expression_standard.md | 元规范：视觉规范须达；全局 z-index 数值规范表；面板/浮层组件三大类规范；统一底栏操作组；组件父容器几何契约；文档架构：两大区域；区域 A：产品规格区；区域 B：交互原型区页面组织；状态帧强制结构；状态 Chip 导航；触点徽章；新增业务组件标注；内容分工规则；九、主模板使用规则；多语言支持；组件变更清单 section；UI 表达克制原则 |
| （豁免—无任务必读）| pm-workflow/rules/prd_expression_standard.md | 变更记录 |
| 阶段4 FA Foundation | pm-workflow/rules/proto_spec_md.md | 一、文档整体结构；产品背景格式规范；页面流转总图；六、组件状态库；组件变更清单（文档尾部 |
| 阶段4 S 模块 Spec | pm-workflow/rules/proto_spec_md.md | Agent 阅读指引；单模块 spec 草稿章节标准；四、各页面区块格式；五、全局交互规则；异常场景全景 |
| 阶段4 终审 Supervisor | pm-workflow/rules/proto_spec_md.md | 一、文档整体结构；产品背景格式规范；Agent 阅读指引；页面流转总图；单模块 spec 草稿章节标准；四、各页面区块格式；五、全局交互规则；六、组件状态库；异常场景全景；组件变更清单（文档尾部 |
| 全部 Supervisor 任务 | pm-workflow/rules/rule_hard_constraints.md | 七、审核方自动化核查清单 |
| （豁免—无任务必读，L2 维护层）| pm-workflow/rules/rule_hard_constraints.md | 八、维护规则；变更记录 |
| 全部 Supervisor 任务 | pm-workflow/agents/AI产品主管_Agent.md | 一、角色身份；二、核心行为准则；三、问题分级处理规则；4.0 通用前置审核；五、流程监督规则；六、整改反馈格式；七、向上汇报规范；八、禁止行为清单 |
| Supervisor 阶段1 | pm-workflow/agents/AI产品主管_Agent.md | 4.1 需求分析审核 |
| Supervisor 阶段2 | pm-workflow/agents/AI产品主管_Agent.md | 4.2 功能规划审核 |
| Supervisor 阶段3 | pm-workflow/agents/AI产品主管_Agent.md | 4.3 产品定义审核 |
| Supervisor 阶段4 | pm-workflow/agents/AI产品主管_Agent.md | 4.4 交付文档审核 |
| Supervisor 中段审核（Step 1.X）| pm-workflow/agents/AI产品主管_Agent.md | 4.5 阶段4 scaffold 中段审核 |
<!-- SECTION-MAP-END -->

**维护纪律**：3 个文件新增/改名章节时同步本表（元测试 FAIL 会拦漏）；新大文件要纳入分节体系 → 加表行 + 元测试 `MAPPED_FILES` 配置（`prd_expression_standard.md` 等阶段4专属规范挂 NB 待下一批评估）。

### 调研 + 计划制定 subagent 派发规范（L1+L2 通用）

> **本节定位**：补全编排器派发「临时调研角色 / 计划制定」场景的规范。与本文件既有「业务执行型派发」（阶段 4 7 步 + PM/Supervisor 派发清单）**互补不重叠**：
> - 既有规范覆盖：L1 业务**执行**链路（PM 生产 / Sup 审核 / 阶段流水线固定环节）
> - 本节覆盖：**临时调研 + 计划制定**（一次性报告不落盘，或为后续执行铺路）

#### 一、概念区分（系统层 subagent vs 业务层 Agent 角色）

| 层 | 定义 | 实际是什么 |
|----|------|-----------|
| **系统层 subagent**（`Agent` 工具的 `subagent_type` 参数）| Claude Code 系统提供的通用执行单元 | `claude` / `Explore` / `general-purpose` / `Plan` / `claude-code-guide` / `statusline-setup` |
| **业务层 Agent 角色**（项目工作流定义的执行角色）| 通过 prompt 让 subagent 扮演的角色 | `PM Agent` / `Supervisor Agent`（来自 `pm-workflow/agents/`）/ Foundation Agent / 项目组件识别 Agent / Spec Agent / PRD Agent 等 |

**关键事实**：同一个系统层 subagent 可承担不同业务角色 — 取决于 prompt。如派 PM Agent 实际就是 `general-purpose` subagent + Read `AI产品经理_Agent.md` 角色规范。

#### 二、派发判定准则（决策树）

```
任务来了
   ↓
是 L1 业务相关 还是 L2 维护?
   │
   ├─ L1 业务
   │   ├─ 范围评估(调整意见,含潜在修改)    → PM Agent [Must] (本文件「调整意见自动记录规则」第二步既有)
   │   ├─ 计划制定(阶段链路 / 整改 / 模块拆分) → PM Agent [Must] (本节新增)
   │   ├─ 业务质量审核(终审 / 审 PRD)       → Supervisor Agent [Must] (既有阶段链路)
   │   ├─ 跨产品 audit / 一致性核查         → 临时审计员 (general-purpose)
   │   └─ 突发简单查询 / 找文件             → Explore subagent
   │
   └─ L2 维护
       ├─ 计划制定                          → 编排器自做 (workflow-evolution skill Step 1 任务理解)
       ├─ 跨文件 audit / 排查类调查         → 临时审计员 (general-purpose)
       ├─ 找文件 / grep symbol              → Explore subagent
       └─ 实施修订                          → 编排器自做 (走 skill 8 步)
```

`[Must]` **L1 计划制定必派 PM Agent，禁用 Plan agent**：
- **理由**：Plan agent 是通用软件架构师，**不读**产品定义 / **不知** SSOT 双锚 / **不懂**业务术语 / **不知** decisions_ledger.md 决策账本（SSOT #18）/ **不知**项目命名 SSOT
- **后果**：Plan agent 出的"计划"会脱离业务实际 / 漂移已决策方向 / 重新设计已有产物，比 PM 制定的计划更**不合理**
- **PM 拥有的领域知识**（Plan agent 缺失）：阶段 1-3 产物完整理解 / 项目命名 SSOT / 与产品总监确认的设计决策 / 业务术语 + 用户故事

#### 三、subagent 类型选型表

| 类型 | 适用 | 不适用 |
|------|------|--------|
| **Explore** | 快速定位代码 / 找文件 / grep symbol / "X 在哪定义" | code review / audit / 开放式分析 / cross-file consistency check（按工具描述明示）|
| **general-purpose** | 临时审计员 / 架构梳理 / 跨文件一致性 / 开放式分析 / multi-step 调研 / 业务角色载体（PM/Sup） | 简单单文件查找（用 Explore 更轻量）|
| **PM Agent**（业务角色，载体 general-purpose）| L1 业务计划制定 / 范围评估 / 整改执行（[Must]）| 跨产品 audit / L2 维护任务 |
| **Supervisor Agent**（业务角色，载体 general-purpose）| L1 业务质量审核（[Must]）| 调研 / 计划制定（角色定位不符）|
| **Plan** | （本工作流**罕用**）— 仅当出现非业务 / 纯技术架构场景时 | 本工作流大部分场景（业务背景敏感）|
| **claude** | 兜底（catch-all） | — |

#### 四、`[Must]` prompt 7 要素

编排器派发临时调研 / 计划制定 subagent 时，prompt **必须**含以下 7 要素：

1. **角色定位** —「你是 X audit / 调研 agent」/「你是 X 计划制定 agent」
2. **任务目标** — 一句话说明要干什么
3. **read-only 声明**（非实施任务必须）—「禁止 Edit / Write」
4. **必要 context** — 项目背景 + 已知信息（避免 subagent 重读 CLAUDE.md / ssot_anchors.md 浪费 token）
5. **调研范围** — 具体文件路径清单（不让 subagent 漫游 grep 半个 repo）
   - 5.1 **`[Must]` audit / 合规率 / "是否齐全 / 是否一致" 类任务必须显式 Read 实际产物**：prompt 中明示「必须先 Read [产物路径（PRD html / spec md / 代码 / state.md 等）]，然后基于实际内容判定，禁止仅凭规范文字描述 / 组件名 / 类名字面推断」。
   - **实战先例**：
     - 2026-05-15 派 Explore 查某项合规率，虚报 94%，提醒后 Read 实际 DOM 二次排查降至 65%（漏判 35%，过宽松）
     - 2026-05-13 派 Explore 查 desktop sticky 违规，估 51 处实际 6 处（误判 88%，过敏感）
     - 两类失误互补 — 都是"不开实际产物只看规范文字"的后果；无论派 Explore 还是 general-purpose，audit 任务必须强制开实际产物
   - 5.2 **`[Recommended]` 大文件 anchor 清单（≥ 3000 行 / ≥ 500KB 文件扫描时）**：派发 prompt 须显式列出 **grep anchor 字面清单**（如 `grep -n "<section id="` / `grep -n "^## "` / `grep -n "## 变更记录"` 等），要求 subagent 对每个 anchor **实测 grep 返回 byte 锚定行号 + 字面**，避免大文件纯语义扫描漏报（如下游 PM 报 prd.html 18000+ 行 doc-changelog 段漏扫）。
   - 5.3 **`[Recommended]` 编排器对 Explore "无违规 / 已合规" 结论二级 sanity check**：抽查 2-3 个关键 anchor 独立 verify（模式同 audit 任务的产物 Read 要求）；若抽查与 Explore 结论不一致 → 派第二个 subagent 交叉验证（同既有"过度推论检测"机制）
   - 5.4 **`[Must]` 下游 PM 反馈核查类任务必含反馈源仓显式锚词（2026-06-02 元错型治本）**：派 Explore 核查 PM 反馈类任务时，prompt 必须显式声明反馈源仓（按 `CLAUDE.md §调整意见自动记录规则 第零步` 已 AskUserQuestion 确认的结果）。**场景 A（下游仓本地可访问）**：prompt 起始段必含一行「反馈源：<repo 绝对路径>」+ 调研范围列出该仓具体文件路径（如 `/home/tangjun/Documents/private-domain-homepage-module/outputs/spec_私域主页模块_latest.md`）；**场景 B（下游仓不在本地，用户提供完整问题分析报告）**：prompt 起始段必含「反馈源：远程仓（用户提供报告，无本地访问）」+ 用户报告关键实证逐字复贴 + 调研范围仅限上游 L2 真源（`pm-workflow/rules/` / `pm-workflow/scripts/` 等）。**禁止**：用模糊词如「下游 PM 仓」「active PM 仓」「quotation-tool 仓」（未确认）。**违反信号**：本会话 6-02 早晨 + 下午连续踩 2 次（Explore prompt 写 "quotation-tool" 但实际反馈源是 private-domain-homepage-module → 核查错样本 → 误判 PM 0/3 + 误派 feedback；commit `e043606` 元错型治本）。
6. **输出格式** — 结构化（表格 / mermaid / 编号清单）
7. **字数限制** — `≤ N 字` 防溢出主对话

`[Must]` 派发 PM Agent / Supervisor Agent 时，按本文件既有派发清单（阶段 4 各 Step + 调整意见整改路径）执行，**不**走本节 7 要素 — 那里是路径清单 + 角色规范 Read 模式。

#### 五、反 pattern（禁用）

| 反例 | 问题 | 应改为 |
|------|------|--------|
| ❌「请帮我看看 X」 | 模糊任务，无目标无范围 | 7 要素齐全 |
| ❌ 不传项目背景 | subagent 重读规范文件浪费 token | 必要 context 段精简列出 |
| ❌ 不指定字数 | subagent 输出 5000 字溢出主对话 | 明确「≤ N 字」 |
| ❌「你看着办 / 自行决定」给 subagent 选择权 | 指令不明确 | 明确指令边界 |
| ❌ 派 Explore 做 audit / design-doc 评估 | 工具描述明示不适用 | 改派 general-purpose |
| ❌ 派 Plan agent 做 L1 业务计划 | 不懂业务，出脱节计划 | 改派 PM Agent |
| ❌ 派 PM Agent 做轻量调研（如查 1 个字段在哪）| Token 成本过高（PM 路径清单 ~150K） | 改派 Explore / general-purpose |
| ❌ 派 audit 类 subagent 仅凭规范文字 / 组件名推断合规率 | 漏判过宽松（虚高合规率）— 2026-05-15 实战 94→65% / 与 2026-05-13 88% 误判互补 | prompt 中显式列必读产物路径 + 验证措辞「先 Read 实际产物再判」（见 §四 第 5.1 项）|

#### 六、输出验收 SOP

subagent 返回后编排器**必须**：

1. **格式验证**：输出格式符合 prompt 要求（表格 / mermaid / 字数）
2. **证据验证**：关键结论有证据支撑（行号 / 文件路径 / grep 命令 / 实测数据）
3. **过度推论检测**：若 subagent 给出超出调研范围的结论，**派第二个 subagent 交叉验证**（先例：本会话有 audit agent 判 R4 = 8K 字符节省，实测仅 290 字符 — 误差 27 倍）

`[Recommended]` 高 ROI 调研结论（涉及多文件改动 / 长期机制设计）建议**默认派第二 agent 交叉验证**，单 agent 输出不直接落地。

#### 七、与既有规则的关系

| 既有规则 | 关系 |
|---------|------|
| 本文件「派发路径选择（L1/L2 二元判定速查）」 | L2 任务走 skill / L1 任务派 Agent — 本节细化"派什么 subagent / 何种角色" |
| 本文件「调整意见自动记录规则」第二步 | 该规则规定"范围评估必派 PM/Explore"，本节扩展到"L1 计划制定必派 PM"（同精神延伸）|
| 阶段 4 派发 7 步 + PM/Sup 派发清单 | 业务执行型派发（既有），本节是临时调研型派发（补全）|
| 编排器读文件边界硬约束 | 本节"必派 subagent"场景与该硬约束一致（编排器禁止越界 Read 规范文件）|
| `workflow-evolution` skill 8 步 | L2 维护"计划制定"由编排器在 skill Step 1 完成（不派 subagent）|

#### 八、Plan agent 在本工作流的实质位置

`[Not Recommended]` **Plan agent 在本工作流罕用**：
- 本工作流是"业务文档驱动"模式，所有计划都需领域知识（业务背景 / SSOT / 命名 / 决策记录）
- Plan agent 是通用软件架构师，**与本工作流的业务背景敏感性根本不匹配**
- 本会话实战观察：未派过 Plan agent 一次（即使遇到 NB-WE-28/29 改造、组件库解耦、字段优化等"实施计划"场景，都由 PM 或编排器制定）
- 选型表中保留 Plan 仅为完整性，**实际派发优先级最低**

未来如出现非业务 / 纯技术架构场景（如本工作流脚本本身的架构重构），才考虑派 Plan agent。

#### 九、`[Must]` 机械化优先决策树（subagent 派发前置）

> **本小节定位**：在派发 subagent **之前**强制做一道"能否不派"的前置判定。前面 1-8 节回答"派什么 / 怎么派"，本节回答"是否该派"。
>
> **诞生根因**：2026-05-13 desktop sticky 排查中 Explore subagent 误判率 88%（估 51 处违规，PM 实际只需修 6 处）。根因不是"Explore 不行"，而是任务本身是"CSS combinator 范围审计 + DOM 子节点穿透"——**可精确形式化为脚本**（HTML parser + cssselect），但派 subagent 做字面 grep 必然漏掉 ` > `（直接子）与空格（任意后代）的语义差异。
>
> **核心原则**：能形式化为脚本的任务一律先脚本，subagent 是"形式化不了"或"语义判断"时才用。

##### 9.1 决策树（任务派发前必跑）

```
任务来了
   ↓
能否精确形式化为可执行匹配逻辑?
（关键词：regex / 字面对账 / 集合运算 / 格式校验 / AST 查询 / CSS selector + DOM walker）
   │
   ├─ 能形式化（规则边界清晰，无歧义）
   │   → [Must] 优先用脚本
   │      ① 检查既有 precheck_*.py / check_*.py 能否复用
   │      ② 否则编排器写一次性 Bash（grep / wc / sort -u）或 python -c
   │      ③ 高频复用则新建 check_*.py 脚本沉淀
   │      ❌ 禁止派 subagent 做"我能 5 行 Bash 解决"的事
   │
   ├─ 部分形式化（核心机械 + 边界语义）
   │   → 流水线模式（先脚本预筛 → subagent 语义判断 → 脚本二次验证）
   │      详见 9.3
   │
   └─ 不能形式化（语义理解 / 推断意图 / 创新建议 / 业务计划 / 主观判断）
       → 派 subagent（按既有 1-8 节选型）
```

##### 9.2 形式化可行性评估清单（执行前自检）

派 subagent 前，编排器必须先问自己以下 5 个问题。**任何一项答"是"就改走脚本路径**：

| # | 自检问题 | 含义 |
|---|---------|------|
| 1 | 规则是否能写成 regex / CSS selector / XPath / AST 查询? | 形式化语言可直接表达 |
| 2 | 验收标准是否能写成"集合 A 减集合 B 应为空"? | 集合对账 |
| 3 | 任务本质是否是"统计 / 计数 / 大小对比 / 存在性检查"? | wc / grep -c / find / ls 即可 |
| 4 | 是否已有 precheck_* / check_* 脚本覆盖类似规则? | 复用现有脚本扩 case |
| 5 | 任务输出是否是"是 / 否 / 数字 / 命中清单"（非散文报告）? | 脚本天然适配此类输出 |

##### 9.3 流水线模式（部分机械化场景）

适用于"规则核心机械、但需语义判断'何时应用'"的任务（如规范优化空间审计）：

```
① 脚本预筛（机械层）
   - 体积统计 / 残留计数 / 集合对账 / 格式校验
   - 输出："命中 N 处，分布在 X/Y/Z 文件"
   ↓
② subagent 语义判断（语义层）
   - prompt context = 预筛结果（已是结构化清单，不再漫游）
   - 任务："对预筛清单做语义判断（哪些真违规 / 哪些可豁免）"
   - 字数限制 ≤ N 字
   ↓
③ 脚本二次验证关键数据
   - subagent 给出"删除 N 字符 / 命中 M 处"等数字结论
   - [Must] 编排器用脚本复核（先例：R4 27 倍误差 = subagent 估 8K 实测 290 字符）
```

##### 9.4 形式化工具速查表（核心难点 = 选对工具）

**关键洞察**：机械化失败往往不是"该不该机械化"，而是**没选对形式化工具**。文本 grep 处理嵌套结构 / DOM 层级 / 语法树时必然漏判。

| 任务类型 | 错误工具 → 必然漏判 | 正确工具 |
|---------|---------------------|---------|
| HTML 结构 / CSS selector 范围 | `grep` 字面匹配 | Python `BeautifulSoup` + `lxml.cssselect` |
| CSS combinator 语义（` > ` vs 空格）| `grep` 找 selector 字面 | `cssselect.GenericTranslator().css_to_xpath()` + DOM walker |
| 嵌套结构 / 配对括号 / 注释块 | `regex` | AST 解析（Python `ast` / JS `esprima`）|
| JSON / YAML schema 校验 | `regex` 找字段 | `jsonschema` / `pyyaml` + 显式验证 |
| 跨文件 SSOT 真源 ↔ 派生对账 | 派 Explore 逐文件查 | `grep -rn pattern dir1/ dir2/` + `diff <(sort A) <(sort B)` |
| 文件体积 / 行数 / 字符数 | 派 subagent 数 | `wc -m / -l / -c` |
| 文件存在性 / 命名规范 | 派 subagent 检查 | `find` / `ls` + regex |
| Python 函数 / 类签名提取 | regex | `ast.parse` + walk |
| 位置语义（顶部 bar vs 底部 bar / 第一 vs 最后子节点）| 按钮密集 / flex 启发式 | 父元素 `firstChild` / `lastChild` 位置判定 + `bottom:0` / `top:0` 字面值组合 |

##### 9.5 反例 table（机械化优先反例 + 已发生先例）

| 反例 | 误派类型 | 应改为 | 节约 / 代价 |
|------|---------|--------|------------|
| 派 agent 数文件字符数 / 行数 | Explore / general-purpose | `wc -m file` | ~50K token |
| 派 agent grep 全 repo 字面字符串 | Explore | `grep -rn pattern dir/` | ~30K token |
| 派 agent 找 CSS selector 命中元素 | Explore | `BeautifulSoup + cssselect` | ~50K token + 误判归零 |
| 派 agent 对账 SSOT 真源 ↔ 派生 | general-purpose | 既有 precheck_* 或 grep diff | ~30-80K token |
| **派 Explore 做 CSS combinator 范围审计**（2026-05-13 先例）| Explore | 脚本解析 CSS selector + 直接子节点 walker | ~50K token + 校正成本（88% 误判率，估 51 实修 6）|
| 派 agent 检查模板纯净度 | general-purpose | `precheck_template_purity.py`（已有）| 复用现有脚本 |
| 派 agent 检查 SOP 偏离 | general-purpose | `pre-commit` hook（已有 SSOT #31 兜底）| 复用机制 |

##### 9.6 何时机械化"失败"要回退派 subagent

机械化不是万能。以下信号出现 → 回退派 subagent：

- 规则需要"判断业务合理性"（如"这个字段是否冗余"）
- 规则需要"理解上下文意图"（如"这段话是否表达了 X 意思"）
- 规则需要"创造性建议"（如"如何优化此规范文档结构"）
- 规则边界本身需要先讨论确定（如"什么算'设计漂移'"）
- 形式化工具不存在或太复杂（如"自然语言 PRD 是否覆盖了所有用户场景"）
- 规则需"区分顶部 / 底部 / 第一 / 最后子节点"等位置语义时，按钮密集 / flex 启发式必有 false positive — 要么补 `firstChild` / `lastChild` 判定 + 字面值组合（如 `bottom:0`），要么走 9.3 流水线模式接 subagent 复核（本工作流先例：2026-05-14 实战测试中 desktop-frame 顶部 ribbon 被误判为底部 bar）

##### 9.7 与既有规则的关系

| 既有规则 | 关系 |
|---------|------|
| 本文件第 1-8 节 subagent 派发规范 | 本节是 1-8 节的**前置判定层**——先问"是否该派"，再问"派什么 / 怎么派" |
| 本文件「编排器读文件边界硬约束」 | 不冲突：脚本执行不算 Read 规范文件，编排器跑 `wc / grep / python -c` 不越界 |
| CLAUDE.md「范围评估必派 subagent」 | 不冲突：该规则针对**语义类**范围评估（含"是否一致 / 是否漂移"等）；纯机械范围评估（如"列出所有 file:line 含 X"）可走脚本 |
| `workflow-evolution` skill | L2 维护任务中遇到机械可形式化的检查项（如纯净度 / SSOT 对账），优先用脚本而非派 audit agent |

---

