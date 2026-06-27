# 硬规则清单（Hard Constraints）

> **用途**：PM / Supervisor Agent 执行任何阶段任务的硬性约束清单。
> **使用时机**：每阶段开工前必读本文件对应阶段章节；每步完成后按分步自审指令自查；提交前逐条核对。
> **违反后果**：违反任何一条 `[MUST]` 规则均视为缺陷，主管审核必须退回整改。

---

## 一、使用规范

### 1.1 PM Agent 使用方式

**开工前**：
1. 读取本文件「跨阶段通用规则」+「阶段 N 规则」两节
2. 将所有 `[MUST]` 规则转化为进度文件「任务专属检查清单」中的具体检查点（结合本次任务实际内容展开，而非抄录规则标题）
3. 对于含**分步自审指令**的规则（如 S4-03 / S4-10），将自审步骤嵌入进度文件的 W/S/H 步骤中

**每步完成后**：
1. 按本步涉及的规则执行分步自审（使用 Bash/Grep 工具运行 grep / wc 等命令）
2. 任一不通过，立即修正再继续下一步（禁止积累到提交前才处理）

**提交前**：
1. 逐条核对本文件对应阶段清单
2. 在自审报告中明确标注每条 `[MUST]` 的核查结果

### 1.2 Supervisor Agent 使用方式

**审核开始前**：读取本文件对应阶段章节
**审核中**：按清单执行自动化核查（grep / wc 等批量验证），重点用工具而非肉眼
**审核结论**：发现违反 `[MUST]` 规则直接退回整改，不得仅标注为非阻塞问题放行

---

## 二、跨阶段通用硬规则

### G-01 `[MUST]` 文件命名与归档

- 当前版本文件：`outputs/[阶段名]_[产品名]_latest.{md|html}`（路径永不变更）
- 历史版本归档：`process_record/versions/[阶段名]_[产品名]_v[主].[次]_[YYYYMMDD].md`
- 初次创建时必须同步复制初始版本快照至 versions 目录（阶段 1-3 = v1.0；阶段 4 = v0.1，未交付态信号）
- 每次**对外可见版本变更**前先归档当前 latest，再写入新内容

### G-02 `[MUST]` 变更记录表格式

- 列头固定 6 列：`| 版本 | 变更内容 | 变更原因 | 变更人 | 审核人 | 日期 |`
- 每次修订追加新行，禁止删除历史行
- 「审核人」列由 Supervisor 审核通过后填入 `Supervisor Agent`，PM 创建时留空
- 版本号规则（阶段 1-3 vs 阶段 4 二元）：
  - **阶段 1-3**：初创 v1.0；主管退回整改次版本 +1；变更请求触发主版本 +1 次版本归零
  - **阶段 4（SemVer 化，变更记录表仅记需求变更）**：仅 3 种对外可见版本变更触发点 → ①启动 **v0.1**；②总监 `/nextStage` **首次**终审通过 **v0.1→v1.0**（无论 v0.1 期间经过多少次 /changeRequest）；③ **v1.0 之后** `/changeRequest` 触发主版本 +1 次版本归零（**vX.0**，v1.x 序列取消）
  - **其他场景一律不动版本号 + 不追加表行**：含 PM 自审整改 / Sup 退回整改 / Step 1-7 完成 / **v0.1 期间总监走 /changeRequest 提大需求变更**（仍未对外 release，开发态内部迭代）/ **v1.0 后总监意见整改通过** / polish / 补遗漏（产品阶段内部问题，不暴露下游；与 SemVer 0.x 标准语义一致）
  - **非需求变更内部记录入口**（PM/Supervisor/产品总监三方可查，下游不消费 process_record/）：①产品总监原始意见 → `process_record/issues/YYYY-MM-DD_HHMM.md`；②PM 整改进度 → `process_record/progress/stage4_[产品名]_plan.md`；③文件级 diff → `git log -- outputs/spec_*.md outputs/prd_*.html`
  - **变更记录表行新增时机**：仅 3 种需求变更触发点追加行（v0.1 / v1.0 / vX.0）；其余禁追加，避免污染对下游的需求变更日志
  - **`[Must]` 「变更原因」列承接类别（使用指南，SSOT #79 配对）**：本列承接的溯源类别 = 版本沿革 / 变更请求 `CR-XXXX` / 调整意见号（issues 文件名）/ `NB-XXX` 引用 / G-07 授权。**变更溯源只写本列 + `decisions_ledger.md`（SSOT #18），禁写进成果正文内联标记**（与 S4-68 配对：禁令在正文，去向在本表 + ledger + git）

### G-03 `[MUST]` 进度文件维护

- 每完成一步立即 `[ ]` → `[x]`，**严禁批量完成后统一更新**
- 进度文件路径：所有阶段统一为 `process_record/progress/stage[N]_[产品名]_plan.md`（如 `stage4_报价工具_plan.md`）
- 中断恢复时从第一个 `[ ]` 继续，不重复已完成步骤

### G-04 `[MUST]` 章节结构不得改动

- 按各阶段模板（`pm-workflow/rules/{tmpl_需求分析|tmpl_功能规划|tmpl_产品定义}`）规定的章节标题、顺序、表格列名撰写，禁止增删或改名
- 模板中 `<!-- -->` 注释块的填写规范不得违反

### G-05 `[MUST]` 问题清单分级完整

- 阻塞性问题 / 非阻塞性问题两子节必须同时存在
- 无问题时填占位行（如"本阶段无 XX 问题"），禁止删除整个子节
- 状态列使用固定选项：待确认 / 已确认

### G-06 `[MUST]` 修改前必须分析影响范围

- 对任何已有内容（章节、字段、页面、组件、尺寸等）进行修改前，必须先列出所有可能受影响的关联位置
- 修复类任务：必须先说明根因再动手；修复完成后全局扫描同根因的其他位置
- 禁止只改目标位置而遗漏连带位置

### G-07 `[MUST]` 产品总监已确认决策不得回退

- 产品总监已确认的调整决策必须完全遵循。决策载体是 `process_record/decisions_ledger.md`（SSOT #18 已决策清单单一权威源，append-only），分布于两表：
  - 「已解答阻塞性问题」表（解答内容列即决策内容）
  - 「已决策非阻塞性问题」表（决策内容列即决策内容）
- PM / Supervisor 开工前必须 Read `decisions_ledger.md` 全文并把上述两类已决策条目纳入约束（state.md 仅保留当前阶段 ⏳ 开放问题，尚未决策、不构成回退约束）
- 如需偏离须重新与产品总监确认并记录，PM/Supervisor 不得自行判断
- **G-07 授权痕从正文清理的留存形式（SSOT #79 配对）**：当 S4-68 要求从成果正文清理 `（…G-07 授权）` 等内联授权标记时，授权溯源**须确保已在 `decisions_ledger.md`（决策真源）+ 必要时变更记录表「变更原因」列留痕**；清理前先核验 ledger 已有该授权条目（**先存后删**，详 `AI产品经理_Agent.md §8.3`），正文以**纯当前态描述**呈现、不留内联授权标记（也不挂指向 ledger 的内联指针——指针本身即一种变更痕迹）——决策痕迹的权威信道是 ledger，正文只陈述当前态事实

### G-08 `[MUST]` 重做计数边界（三层独立循环）

借鉴 superpowers 插件三轮独立评审模式（issue 2026-05-10_0446 项 2）,显式区分以下 3 类循环:

- **L1 机械循环**:precheck FAIL → PM 整改 → 重跑 precheck → 直至 PASS
  - **不计入** Supervisor 重做 3 次额度;PM 内部闭环,反复几次都允许
- **L2 PM 自审局部循环**:precheck PASS 后,PM 走自审清单某项 FAIL → 局部修 → 重跑该项 → PASS
  - **不计入** Supervisor 重做 3 次额度;PM 内部闭环
- **L3 Supervisor 整改循环**:Supervisor 终审退回 → PM 重新执行**完整阶段** → 再次派发 Supervisor
  - **每次 L3 触发计 1 次重做**,3 次后须升级处理策略（拆分问题 / 多套候选方案 / 提交产品总监裁决）
  - **触发源限定**：**仅 Supervisor 终审退回**才计 L3。产品总监修改意见 / 需求变更 / 补充触发的"返回步骤 A 重做"**不计 L3**——因 G-08 信号意图是捕获"PM 思路 ↔ Supervisor 标准方向性冲突"，产品总监主动改方向不属于该信号（输入变了不是 PM 解不了），混算会污染信号导致升级 SOP 空触发

**判定原则**:
- 是 L1/L2 还是 L3,以"**Supervisor 派发-审核-退回**"为唯一边界（其中"退回"是关键）
- 触发源辨别：①Supervisor 终审输出"审核不通过" → L3 +1；②产品总监终审时回复意见（CLAUDE.md「调整意见自动记录规则」路径 A）→ **不 +1**
- 例外:同一问题经 L3 反复 3 次仍未通过,**禁止继续相同思路**,须升级处理策略后再推进
- 重做计数记录于进度文件「整改循环计数」段（SSOT #17 真源）的 `terminal_rework_used` 字段,L1/L2 不写入此字段

**违反场景反例**:
- ❌ PM 把 precheck 反复 FAIL 计入重做额度（误导上层 / 浪费额度）
- ❌ 自审清单某项漂移导致重审整轮自审 → 计 L3 重做（应只重审该项）
- ❌ Supervisor 给反馈后 PM 仅修部分,跳过整阶段重做 → L3 应由 PM 完整重执行
- ❌ **产品总监终审时给修改意见 → PM 计 L3 +1**（信号污染：根本矛盾不存在,升级 SOP 空抽象；输入变了 ≠ PM 解不了）
- ❌ **PM 上报阻塞性问题、用户回答后返回步骤 A → 计 L3 +1**（用户回答是给输入，PM 之前没失败、是在等待，重做不计）
- ❌ **升级处理后产品总监裁决、PM 返回步骤 A 执行裁决 → 再 +1 L3**（升级时已因 3/3 触发，裁决是新方向的输入，执行新方向不属于"Supervisor 退回循环"语义）
- ❌ /changeRequest 流程的重做 → 计 L3（变更请求是独立流程，主版本 +1，与 L3 信号无关）

---

## 三、阶段1 硬规则（需求分析）

### S1-01 `[MUST]` 需求概述三问必答

- 「需求背景 / 业务目标 / 成功标志」三项全部填写，无"待定""TBD"等模糊表述
- 业务目标须描述期望结果（动词开头），禁止描述手段
- 成功标志须可客观观测（可观测行为或量化指标）

### S1-02 `[MUST]` 用户角色规范

- 用户角色表含「核心诉求」列
- 章节末附「权限边界说明」段落
- 角色命名全文统一（如"销售人员"不与"业务员"混用）

### S1-03 `[MUST]` 核心场景三要素

每个核心业务场景必含：
- **触发条件**：一句话说明何时由谁触发
- **主流程**：每步格式 `步骤描述 → 系统：系统响应`，禁止只描述用户动作
- **边缘情况**：必须使用三列标准表格（边缘情况 / 触发条件 / 系统处理方式），禁止自由段落

### S1-04 `[MUST]` 功能边界双表齐全

- §4.1 本次包含的功能、§4.2 明确排除的功能 两表必须同时存在
- §4.2「后续安排」列使用固定选项：后续迭代 / 已有模块 / 超出范围 / 待评估

### S1-05 `[MUST]` 约束条件三类齐全

- 技术约束 / 平台约束 / 范围约束 三子节均存在
- 每条描述具体可执行，禁用"需要考虑 X"等模糊表述，须写"需评估 X 方案"或"受 X 限制不得使用 Y"

### S1-06 `[MUST]` 4 步分析法按序应用

- `proto-persona` → `jobs-to-be-done` → `problem-statement` → `opportunity-solution-tree` 按序应用
- **应用机制**：Read `pm-workflow/skills/<框架名>/SKILL.md` + `template.md`，按其 schema 产出中间分析产物（不依赖 Claude Code 的 Skill 工具）
- **判定标准**：中间产出物结构符合 SKILL.md 规定的 schema；结论写入对应章节（详见 PM Agent §四.阶段一分析框架）

### S1-07 `[MUST]` 现网已有模块识别

- 需求分析阶段必须明确列出项目所属上位系统已有的基础能力（账号体系/权限/导航/通知等）
- 上述模块须在 §四.2 排除功能 + §五.3 范围约束 **双重登记**，避免重复设计
- §四.2「后续安排」列标注「已有模块」；§五.3 注明「本模块所有页面均在现网已登录态下访问，不设计未登录场景」
- 阶段2-4 承继此约束：功能规划不得为已有模块规划子功能；产品定义路由表不得出现已有模块页面；交付文档不得设计已有模块的交互帧

---

## 四、阶段2 硬规则（功能规划）

### S2-01 `[MUST]` 功能模块与需求分析严格对齐

- §一 功能模块清单必须覆盖需求分析 §4.1 全部功能，无扩展、无遗漏
- 模块划分可重组，但功能项不得增减

### S2-02 `[MUST]` 编号与优先级

- 子功能编号格式 `MN-XX`（如 M1-01）
- 优先级仅使用 P0 / P1 / P2，禁用"高/中/低""核心/次要"
- 子功能描述含触发条件 + 系统行为，禁用"支持 X""允许 Y"等无主语表述

### S2-03 `[MUST]` 流程图 4 条格式规则

1. **终态完整**：每条路径末端必须有终态节点，格式 `([文字])`
2. **判断节点全覆盖**：每个菱形 `{}` 节点所有分支均标注出口条件
3. **模块编号标注**：涉及功能操作的节点用括号标注对应子功能编号
4. **无孤岛节点**：所有节点必须有入边或出边

### S2-04 `[MUST]` 产品架构三子节齐全

- §3.1 页面架构树 + §3.2 模块依赖关系 + §3.3 核心页面说明
- §3.3「端」列使用固定选项：手机端 / 桌面端 / 两端 / 移动端响应式

### S2-05 `[MUST]` 3 步分析法按序应用

- `epic-breakdown-advisor` → `user-story-mapping` → `user-story` 按序应用
- **应用机制**：Read `pm-workflow/skills/<框架名>/SKILL.md` + `template.md`，按其 schema 产出中间分析产物（不依赖 Claude Code 的 Skill 工具）
- **判定标准**：中间产出物结构符合 SKILL.md 规定的 schema；结论写入对应章节（详见 PM Agent §四.阶段二分析框架）

### S2-06 `[MUST]` 现网已有模块承继约束

- 功能模块清单（§一）不得为阶段1 §四.2 标注「已有模块」的现网已有模块规划子功能
- §3.2 模块依赖关系表：对现网已有模块的依赖须标注「外部依赖-现网已有」，不得仅写模块名
- §3.3 核心页面说明：不得包含现网已有模块页面（如登录页、个人中心页等）

---

## 五、阶段3 硬规则（产品定义）

### S3-01 `[MUST]` 章节完整

- 包含 `tmpl_产品定义.md` 规定的全部章节 §0–§18 + **§5.5 业务流程图复述**，无遗漏
- §14 技术建议 **必须留白**（使用"【开发 Agent 填】"占位），由后续开发 Agent 填写；**例外**：涉及现网已有模块的接口/鉴权条目按 S3-06 处理（注明「调用现网[模块名]，本模块不定义」并保留编号），此类注明属于范围声明而非技术实现建议，不与留白冲突
- §5.5 业务流程图复述：全部 mermaid 块由阶段 2 §二原样迁入,**禁止凭空写新流程图**;阶段 2 §二有 N 个 mermaid 块则 §5.5 须有 N 个；precheck_stage3.check_section_5_5 兜底（SSOT #30 派生约束）
- 其余章节全量完成，无"待定""TBD"

### S3-02 `[MUST]` 数据字段精确性

- §9 数据字段必须明确：类型 / 长度 / 校验规则
- 示例：`project_name string(1-50)`、`phone regex ^1[3-9]\d{9}$`、`discount_ratio decimal(1,3) 范围[0, 1]`
- 禁用"大概""可能""类似""暂定"等模糊词

### S3-03 `[MUST]` 接口规范完整

- §10 每个接口含：URL / 请求（method + body） / 响应（status + body） / 错误码
- 仅写 URL 不含请求响应视为未完成

### S3-04 `[MUST]` 异常覆盖

- §11 异常处理全景必须覆盖正常场景的每一种异常路径
- 至少覆盖：网络中断 / 登录失效 / 权限不足 / 数据冲突 / 并发操作 / 外部依赖失败

### S3-05 `[MUST]` 全文一致性

- 字段名称 / 页面编号 / 接口编号 / 功能编号前后统一
- 禁止同一字段在不同章节使用不同名称（如"标题"与"名称"混用）

### S3-06 `[MUST]` 现网已有模块承继约束

- §6 路由表不得出现阶段1 §四.2 标注为「已有模块」的页面（可保留编号作为「外部占位」说明，但不写完整路由定义）
- §11 异常处理全景表不得包含由现网已有模块负责的行项（如"登录失效→跳转登录页"须改为"由现网[模块名]处理，本模块不定义"）
- §14 技术建议中涉及现网已有模块的接口/鉴权条目，说明须注明「调用现网[模块名]，本模块不定义」，**保留条目编号不删除**

---

## 六、阶段4 硬规则（交付文档）— 重点，工作量大易遗漏

> 阶段4 PM 上下文负载最重（产品定义 + 原型设计规范 + 渐增的 spec.md/prd.html），易遗漏规则。本节规则必须严格分步自审。

### S4-01 `[MUST]` 生成顺序

- spec.md 所有 S 步骤完成（进度文件全部 `[x]`）后，才能开始 prd.html 任何 H 步骤
- prd.html 每节内容以对应 spec.md 章节为**唯一输入来源**，不得自由发挥
- 反馈触发的任何修改必须先改 spec.md，再根据修改后的 spec.md 重新生成 prd.html 对应章节，禁止只改 prd.html

### S4-02 `[MUST]` ⚠️ 双文件对称性（零误差）

- **逐页核对**：spec.md 状态表行数 = prd.html 视觉帧数
- **逐页核对**：spec.md 触点表行数 = prd.html 触点卡片数
- **页面编号 / 状态ID / 触点ID 三套体系完全共享**

**分步自审指令**（每完成一个 H 步骤立即执行）：
```bash
# 1. 对比本页 frame-card 数 与 spec 状态行数
grep -c 'class="frame-card"' outputs/prd_xxx_latest.html  # 仅本页区域
# 在 spec.md 找到对应 S 章节的状态枚举表，手动计数行数
# 两者必须相等，差 1 即视为违反 S4-02
```

### S4-03 `[MUST]` ⚠️ HTML section id 全局唯一

- 所有 `<section id="H-PXX">` 必须全局唯一
- 追加写入时务必先检测是否已存在同 id

**分步自审指令**（每完成一个 H 步骤立即执行）：
```bash
# 本步骤新增的 id 全局计数必须 = 1
grep -c 'id="H-P16"' outputs/prd_xxx_latest.html
# 若返回值 > 1，说明追加时重复，必须删除多余 section
```

### S4-04 `[MUST]` 平台覆盖

- 按产品定义「目标平台」字段确定覆盖范围
- APP端：手机帧（440×956 pt）+ PAD帧（1376×1032 pt 横屏）
- 桌面端：1440×900 pt
- 双端产品每页同时绘制多端帧（布局一致可简化 PAD，标注"布局同手机帧"）
- 仅某一端独有的页面在页面清单「访问权限」列注明

### S4-05 `[MUST]` 状态清单覆盖

每页状态枚举表必须覆盖：
- 默认态 / 加载态 / 空态 / 错误态 / 禁用态
- 含权限矩阵的页面：越权提示态
- 含不可逆操作的页面：确认弹窗态
- 含多角色的页面：角色差异态

### S4-06 `[MUST]` 叠加态覆盖

- 所有触发弹框 / Sheet / 抽屉的操作按钮必须有对应叠加态状态帧
- 入口帧 → 叠加态帧链路完整
- 禁止只实现入口按钮而缺少触发后的叠加态
- 弹框/抽屉以「叠加态」方式绘制在父级页面帧内，不单独作为独立帧（§2.10 例外除外）

### S4-07 `[MUST]` 外部依赖组件处理

- 按 `proto_cross_platform.md §五.流程图与外部依赖页面处理` 处理
- 类型一（流程关键步骤）：简化版页面 + 标注「[外部模块-简化版]」
- 类型二（仅来源/去向）：占位节点
- 不作为主流程完整设计目标

### S4-08 `[MUST]` cursor:pointer 全覆盖

- 所有 phone-frame / tablet-frame / desktop-frame 内可点击元素必须添加 `cursor:pointer`
- 重点：按钮、列表项、菜单项、nav-back、nav-action 子元素等

**分步自审指令**（阶段末执行一次）：
```bash
# 统计所有 .btn / .list-item / .menu-item 是否都含 cursor
grep -c 'class="btn' outputs/prd_xxx_latest.html
grep -c 'cursor:pointer' outputs/prd_xxx_latest.html
# 后者不应显著小于前者
```

### S4-09 `[MUST]` 触点编号规范

- 格式：`M[XX]-P[XX]-T[NN]`（如 M01-P01-T01），与 `proto_contract.md §四` 触点编号系统保持一致
- 弹窗 / 抽屉内触点使用 D 前缀独立编号（如 M01-P05-D01）
- 同一触点 ID 在 spec.md 与 prd.html 中完全一致
- 徽章样式按 `prd_expression_standard.md §六.触点徽章`

### S4-10 `[MUST]` 分步自审（每完成一个 H 步骤必做）

每完成一个 H 步骤，立即执行以下 4 项核查：

1. **本页 section id 全局唯一**（grep -c 必须 = 1）
2. **本页 frame-card 数 = spec 对应 S 章节状态行数**（零误差）
3. **本页 interaction-card 数 = spec 对应触点表行数**（零误差）
4. **本页触点 ID 集合 = spec 对应触点表 ID 集合**（完全一致）

任一不通过，立即修正再继续下一步，**禁止积累到提交前统一处理**。

### S4-11 `[MUST]` API 编号唯一来源

- 本阶段使用的 API 编号必须全部来自产品定义 §10 或 spec.md 权威映射表
- 禁止使用"内部占位编号 + 后续回填"模式（经实践验证此模式 100% 遗漏回填）
- 多章节协同写作前必先读权威映射表

### S4-12 `[MUST]` 界面文案唯一来源

- 界面文案以 spec.md 对应章节为唯一来源
- prd.html 的交互卡片、标签、提示文案均须与 spec.md 逐字一致
- 禁止 prd.html 出现 spec.md 中没有的业务描述

### S4-13 `[MUST]` 导航闭环

- 列出本次原型所有页面的所有功能按钮，逐项确认已绑定 onclick 跳转目标
- 重点核查：···更多按钮 / 导出按钮 / 分享按钮 / 列表卡片点击 / 底部操作栏全部按钮
- 跳转目标均为页面编号，禁用"下一页"等模糊描述

### S4-14 `[MUST]` 数据回显行

- 每个状态帧的交互说明表包含「数据回显」行
- 含：数据来源接口名 / 展示字段 / 空值·加载·错误兜底策略
- 纯加载骨架帧和叠加弹窗帧可省略但须在注记中说明原因

### S4-15 `[MUST]` 现网已有模块承继约束

- spec.md 和 prd.html 不得包含现网已有模块页面的完整交互帧（状态枚举表 + 触点定义 + 交互说明）
- 若主流程需经过现网已有模块，以骨架屏占位或「外部模块」节点引用，按 S4-07 处理
- 流程图和跳转关系表中涉及现网已有模块的跳转，须标注「由现网[模块名]处理」，不得描述为普通页面跳转

### S4-16 `[MUST]` 产品规格区与产品背景完整性

**spec.md**：必须包含完整的「产品背景」区块（区块 0.5），依次覆盖以下所有子章节（来源括号内为产品定义对应章节编号）：
- 问题陈述（来源：§1）
- 用户画像（来源：§3，每角色独立小节）
- 权限矩阵（来源：§4）
- 用户旅程（来源：§5，每条旅程步骤表）
- 功能需求规格（来源：§7，每个 F-xxx 独立小节，含交互说明/业务规则/验收标准）
- 数据字段说明（来源：§9，每实体独立表）
- 异常处理全景（来源：§11）
- 非功能需求（来源：§13，含性能/兼容性/可靠性/安全）

**prd.html**：必须包含完整的「区域 A — 产品规格区」（A-01 至 A-08，**额外含 A-04.2 业务流程图独立 section**,共 9 个 spec-* section）。内容以 spec.md 区块 0.5 + spec §3.4（业务流程图）为唯一来源，不得跳过任一子区块，不得自由发挥。

**Supervisor 审核检查项**：
- [ ] spec.md 是否包含区块 0.5，且上述 8 个子章节均存在且内容非空
- [ ] spec.md §3.4 业务流程图是否含阶段 2 §二全部 mermaid 块（SSOT #30）
- [ ] prd.html 是否包含 `id="spec-background"` 至 `id="spec-nonfunc"` 的全部 8 个 section 节点 + `id="spec-business-flow"` 业务流程图 section（共 9 个 spec-* section）

### S4-17 `[MUST]` proj 组件状态枚举完整性

新增 proj 级组件时，`outputs/components_[产品名]_latest.md` 中该组件的 `states.applicable` 必须按 `proj_component_protocol.md §三` 的 8 项清单（hover / active / disabled / loading / error / empty / selected / focused）**逐条**判定，每条必须含 `needed: yes/no` + `reason: <一句话理由>`，不允许简写或遗漏。

**Supervisor 审核检查项**：
- [ ] 每个 proj 组件 schema 含全部 8 项 `applicable` 状态键
- [ ] 每项判定均含 `needed` + `reason` 字段
- [ ] precheck_stage4.py 状态枚举完整性检查通过

### S4-18 `[MUST]` proj 组件可视化完整性

每个 proj 组件必须在 prd.html 中提供独立状态展示区（`<section id="proj-component-{name}">`），区内按 schema 中所有 `needed: yes` 的状态各渲染一行可见样例 + default 一行（中保真级别，详见 `proj_component_protocol.md §四`）。模块帧内的使用**不替代**独立状态展示区——两者必须并存。

**Supervisor 审核检查项**：
- [ ] `outputs/components_[产品名]_latest.md` 中每个 proj 组件 id 在 prd.html 中均有对应 `id="proj-component-{name}"` 的 section
- [ ] 状态展示区内 `.showcase-row` 数量 = schema `needed: yes` 计数 + 1（default）
- [ ] 状态视觉差异肉眼可辨（中保真）；纯占位渲染（如仅有线框）视为不通过

### S4-19 `[MUST]` proj 组件 CSS 抽象纪律

每个 proj 组件**必须**在 prd.html 顶部 `<style>` 块定义一份 CSS class（base + 全部 `needed: yes` 状态对应的 `.proj-XXX.is-{state}` modifier 选择器）；所有使用处**只能引用 class 名**，禁止在使用处用 `style="..."` 实现组件视觉细节。仅以下两种例外允许 inline style：
- 数据驱动的 CSS 变量（如 `style="--col-count: 3;"`）
- slot 内容真实数据属性（如 `<img src="...">`、`<a href="...">`）

详见 `proj_component_protocol.md §五`。

**Supervisor 审核检查项**：
- [ ] 任何 `class="proj-XXX"` 元素不得含 `style="..."`（除允许的 CSS 变量与数据属性外）
- [ ] HTML 中出现的每个 `.proj-XXX` 类必须在 `<style>` 块中有 selector 定义
- [ ] 每个 `needed: yes` 状态对应 `.proj-XXX.is-{state}` modifier 必须存在
- [ ] precheck_stage4.py CSS 抽象纪律检查通过

### S4-20 `[MUST]` fb-* class 选择正确性（业务-语义匹配）

PRD 中引用 `fb-*` fallback 类时，所选 class 必须与业务语义 / 状态 / 必填性匹配。**视觉是否对得上不重要**（fallback CSS 已保证），**业务语义是否对得上才重要**。

**首要权威**：`pm-workflow/rules/bujue-design-system/pub_components_index.md §三 组件总表 + §五.D4 业务语义反查表`；HTML 模板细节见 `fb-fallback-manifest.md`。

**强制对应表（违反即视为缺陷）：**

| 业务语义 | 必须使用的 class |
|---------|----------------|
| 主操作（同操作组仅 1 个）| `.fb-btn-primary` |
| 次要操作 | `.fb-btn-default` 或 `.fb-btn-ghost` |
| 弱化操作（无背景）| `.fb-btn-text` |
| 不可逆危险操作（删除/销毁/扣费）| **`.fb-btn-danger`**（不得用 `.fb-btn-primary`）|
| 必填字段标签 | **`.fb-label-required`**（不得仅用 `.fb-label`）|
| 错误态输入框 | 加 `.is-error` modifier |
| 禁用态可交互元素 | 加 `.is-disabled` modifier |
| 加载中按钮 | 加 `.is-loading` modifier |
| 选中态 Tag | `.fb-tag-selected`（不得用 `.fb-tag` + 自定义颜色）|
| 成功态全页提示 | `.fb-state.fb-state-success`（不得用 `.fb-state-empty` 或自定义类）|
| 错误态全页提示 | `.fb-state.fb-state-error` |
| 加载中全页态 | `.fb-state.fb-state-loading` |

**"硬凑"vs "合法组合" 判据：**

- ✅ **合法组合**（允许，不视为硬凑）：
  - fb-* 类间天然嵌套关系：如 `.fb-card` 内含 `.fb-btn-primary`、`.fb-form-row` 内含 `.fb-label` + `.fb-input`
  - 单实例使用，不需对 fb-* 视觉做任何调整即可表达业务语义

- ❌ **硬凑**（禁止）：
  1. 用 inline style 调整 fb-* 元素位置 / 颜色 / 边框 / 字号让其"看起来像别的"——违反 S4-19 抽象纪律
  2. 同一 fb-* 组合在 ≥ 2 处重复出现且每处都需做调整——应派生 proj 一次性表达
  3. 按 `proj_component_protocol.md §一.B` 5 维清单（D1-D5）任一维度不通过却仍用 fb-* 硬凑

**fallback 不能覆盖时 PM 必须自己处理（不依赖外部 fallback 维护）：**

PM 在阶段 4 发现业务需求超出 fb-fallback 能力时（按 5 维清单判定 fallback 不通过），**必须由 PM 自己处理**——不依赖外部 fallback 库扩展、不上报"NB 建议补 fallback"等待他人：

| 情况 | PM 处理方式 | 文档体现 |
|------|------------|---------|
| 现有 pub/fb-* 组件能力不足，但有可派生的基础 | PM **派生 proj 组件**（基于 pub 扩展）；CSS 写在 PRD `<style>` 块（在 fallback CSS 之后），按 `proj_component_protocol.md` 全套协议执行 | 在 spec 与 prd 的「组件变更清单」中**新增**一条记录 |
| 完全没有合适的现有组件 | PM **创建全新 proj 组件**；schema 含 `inherits: null` 或 `inherits: 自创`；其余按 proj 协议执行 | 同上，组件变更清单"新增"条目 |
| 现有 proj 组件需要修改（字段/状态/交互演进） | PM **更新已有 proj 组件**；改动幅度小则就地修改；改动大需弃用旧组件、创建新组件 | 在「组件变更清单」中体现"修改"或"弃用 + 新增"|

**唯一不需 PM 自处理的场景**：fb-fallback 完全能覆盖（5 维清单全通过）→ 直接引用 class，不创建 proj。

**Supervisor 审核检查项**：
- [ ] 危险操作按钮全部使用 `.fb-btn-danger`（grep `fb-btn-danger` 数量 ≥ 业务定义中的危险操作数）
- [ ] 必填字段全部使用 `.fb-label-required`（按产品定义 §9 数据字段表中 `required: true` 的字段计数）
- [ ] 状态 modifier（`.is-error` / `.is-disabled` / `.is-loading` / `.is-focus`）使用合理，不混淆语义
- [ ] 业务能力超出 fallback 时，PM 已**自行**派生/创建/更新 proj 组件，**未**用 inline style 硬凑、**未**仅停留在 NB 上报
- [ ] 涉及组件变更时，spec 与 prd 的「组件变更清单」均已对应记录（增/删/改/升级建议）

### S4-21 `[MUST]` spec ↔ prd 字段绑定一致性

PRD 中所有表单元素（`<input>` / `<select>` / `<textarea>` / `<checkbox>` / `<radio>`）的 `name` 属性（或 `data-field` 属性）**必须**与 spec.md `§9 数据字段表` 中的字段名**严格一致**——区分大小写、不得简写、不得缩写。

**强制对应关系：**

| spec.md §9 字段名 | prd.html 表单元素属性 | 示例 |
|------------------|---------------------|------|
| `productName` | `<input name="productName">` 或 `<input data-field="productName">` | ✅ 严格一致 |
| `productName` | `<input name="product_name">` | ❌ 命名规范不同（snake vs camel）|
| `email` | `<input name="email_addr">` | ❌ 不得自由简写/扩写 |
| `phone` | 缺失字段绑定 | ❌ 必须绑定 |

**适用范围：** 仅适用于"用户可输入/可选择"的表单元素。纯展示元素（`<span>` / `<p>` / `<div>` 等）不需要字段绑定。

**Supervisor 审核检查项**：
- [ ] grep PRD 中所有 `<input` / `<select` / `<textarea`，提取 `name` / `data-field` 值，与 spec.md `§9` 字段名表对照
- [ ] 所有 spec §9 中标注 `required: true` 的字段在 PRD 表单中均有对应元素（不得遗漏）
- [ ] 字段名大小写、拼写完全一致，不得有 `productName` vs `product_name` 等命名风格漂移

### S4-22 `[MUST]` 组件变更清单完整性

每当本期阶段 4 出现 proj 组件的**新增 / 修改 / 弃用**，或 PM 识别到适合**升级 proj→pub** 的候选，**必须**在以下两处对应记录：

- spec.md `§八 组件变更清单`（详见 `proto_spec_md.md §八`）
- prd.html `<section id="component-changelog">`（详见 `prd_expression_standard.md §十一`）

**4 类变更条目内容**：

| 类型 | 必备字段 |
|------|---------|
| **新增（NEW）** | 组件 ID / 类型 / 触发原因（A/B + 5 维 D1-D5）/ 使用模块 / spec & prd 锚点 |
| **修改（UPDATE）** | 组件 ID / 修改类型 / 修改描述 / 上一版本 / 本版本 / 影响模块 |
| **弃用（DEPRECATED）** | 组件 ID / 弃用版本 / 弃用原因 / 替代组件 ID（**必须**是本清单"新增"或已存在的组件，不得指向虚空）|
| **建议升级 proj→pub** | 组件 ID / 建议原因 / 当前使用项目数 / 复用价值评估 |

**弃用边缘场景（强制保留 audit trail）**：

组件**大重构**（API 不兼容 / 视觉完全重做 / 字段集合大变）时：
1. **保留旧组件 section**，添加可视"已弃用"标记
2. **添加新组件指针**（旧 section 顶部跳转链接）
3. **新组件作为单独 section** + 单独"新增"条目
4. **变更清单"弃用"+ "新增"双条目对应**
5. **禁止**直接删除旧组件 section 或就地改成新组件

**spec ↔ prd 一致性**：两份文件的变更清单**逐行对应**（条目数完全相等、字段语义一致）；diff 双方应等价。

**Supervisor 审核检查项**：
- [ ] spec `§八` 与 prd `#component-changelog` 两份清单的条目数完全相等
- [ ] 每个新增 / 修改 / 弃用条目均有对应的 proj 组件 schema 在 components 文件中（grep 验证）
- [ ] 弃用条目的"替代组件"必须存在于本清单"新增"段或已存在的 proj 组件
- [ ] 大重构场景：旧组件 section 保留 + 含"已弃用"标记 + 含新组件指针；旧组件未被删除
- [ ] 4 个 sub-section（NEW / UPDATE / DEPRECATED / PROMOTE）全部保留，无内容时填占位

### S4-23 `[MUST]` PRD 中所有 fb-* class 必须已在 pub 索引或 fallback.css 登记

PRD 中所写的每一个 `fb-*` class **必须**存在于"合法 class 清单"中。**查不到的 class 一律视为 PM 自创、自合成或拼写错误，全部不通过审核**。

**合法 class 清单 = pub_components_index.md ∪ fb-fallback.css 实际选择器**：

| 来源 | 内容 | 用途 |
|------|------|------|
| `pub_components_index.md` 全文中的 `fb-*` token | 26 个组件 id + 业务场景反查 + 能力反查中提及的 token | 业务语义层面的 PM 检索入口（"我要用主操作按钮"→ `fb-btn-primary`）|
| `fb-fallback.css` 中实际定义的 `.fb-*` 选择器 | 子元素 / modifier / 状态 modifier 的完整 class 名 | 技术真源（CSS 实际渲染依据）|

两者**并集**即合法 class 清单。任何 class 必须至少在其中一处出现。

**适用范围：**

- 所有 `class="..."` 属性中的 `fb-` 前缀 token
- 不包括 `is-*` 状态 modifier（`is-error` / `is-loading` 等是状态后缀，非组件 id）
- 不包括 `proj-*` 类（属于 proj 协议管辖）

**判定方法（机械可查）：**

```bash
# 1. 提取 PRD 中全部 fb-* token
grep -oE 'fb-[a-z-]+' outputs/prd_[产品名]_latest.html | sort -u

# 2. 抓权威集合
grep -oE 'fb-[a-z-]+' pm-workflow/rules/bujue-design-system/pub_components_index.md > /tmp/registered.txt
grep -oE '\.fb-[a-z-]+' pm-workflow/rules/bujue-design-system/fb-fallback.css | sed 's/^\.//' >> /tmp/registered.txt
sort -u /tmp/registered.txt > /tmp/registered_uniq.txt

# 3. 第 1 步结果中**不在第 2 步集合内**的 token 即违反 S4-23
# 实际由 precheck_stage4.py 自动核查
```

**典型违反场景：**

| PM 写法 | 错误类型 | 正确处理 |
|---------|---------|---------|
| `fb-bnt-primary` | 拼写错误 | 改为 `fb-btn-primary` |
| `fb-card-elevated` | 自合成（pub 索引仅有 `fb-card`） | 派生 `proj.L2.elevated-card` 或上报"建议补 fb-card-elevated 至 pub" |
| `fb-banner-warning` | 自合成（pub 索引无 banner 系列） | 用 `fb-toast(warning)` 或 `fb-state-error` 或派生 proj |
| `fb-button-large` | 命名错误（pub 索引为 `fb-btn-lg`） | 改为 `fb-btn-lg` |

**Supervisor 审核检查项**：
- [ ] grep PRD 全部 fb-* token，逐一比对 pub 索引 §三 已登记 id 集合，无遗漏
- [ ] precheck_stage4.py 已机械支持本检查（pub 索引一致性段），但 Supervisor 仍须人工抽查 5-10 个高风险 class（拼写易错、易合成）
- [ ] 若发现未登记 class，PM 必须按"先 pub 索引 → 业务实际能否用 pub → 否则派生 proj"链路整改，**禁止**直接补登记到 pub 索引（pub 索引由工作流维护者管控，PM 不得擅自写入）

### S4-24 `[MUST]` 交互元素可识别标识符（data-tp 绑定）

PRD 中每个交互元素（含 `<button>` / `<a>` / 表单元素 / 自定义可点击 div / 列表项 / Tab 切换 / 分页等）**必须**含 `data-tp` 属性，值与 spec 触点表 ID 严格一致——目的是让产品总监 / 主管 / 开发用机械路径精确指代任一交互元素，而非用位置 / 样子描述。

**`[Must]` 交互元素粒度定义（2026-06-02 SSOT #64 概念升级，下游 D2 治本）**：

"交互元素" = **逻辑交互单元**（用户视角的 1 个可识别交互），**不是 DOM 元素粒度**：
- chip group / radio / tab / button-group：子选项共享 1 个 callback/state → 1 个逻辑交互单元 → 容器级标 1 次（不在每选项重复）
- list / table 同模板多实例：每行独立 callback/跳转 → N 个交互实例 → 每实例标 N 次（合规多次）

详见 `proto_contract.md §四 触点容器级唯一性纪律` + `rule_hard_constraints.md §S4-43` 机械兜底。

**强制对应关系（详见 `prd_expression_standard.md §6.1`）**：

| 项 | 规则 |
|----|------|
| 属性名 | 固定 `data-tp` |
| 取值格式 | `M[XX]-P[XX]-T[NN]`（页面）或 `M[XX]-P[XX]-D[NN]`（弹层/抽屉）|
| 取值来源 | spec.md `§S2.M[XX].3 触点表` 触点 ID 列 |
| 与 tp-marker 一致性 | 同 `tp-wrap` 内 `.tp-marker` 文字 = `data-tp` 末段（`T01` 去 `T` = `01`）|

**机械化覆盖（与本会话复盘修订的"S4 机械化优先级原则"对齐）：可机械化档**

- precheck 扫所有交互元素的 `data-tp` 集合 ↔ spec 触点表 ID 集合双向对照（缺失或多余一律 fail）
- precheck 扫同 `tp-wrap` 内 `.tp-marker` 数字 ↔ 兄弟元素 `data-tp` 末段一致性

**例外（免 data-tp）**：

- 纯展示元素（无 onclick / 非表单 / 非链接）
- 触点徽章 `.tp-marker` 自身（属于显示装饰）
- 状态展示区（`#proj-component-{name}` section 内的样例渲染，属于规格展示）
- 浏览器原生 form 内的 hidden input / submit button（无独立触点）

**Supervisor 审核检查项**：
- [ ] 每个 `class` 含 `fb-btn` / `fb-input` / `fb-textarea` / `fb-select` / `fb-checkbox` / `fb-radio` / `fb-switch` / `fb-link` / `fb-tag(可点)` / `fb-pagination` / `fb-card(可点)` / `fb-list-item` 的元素都有 `data-tp` 属性（precheck 已机械化）
- [ ] `data-tp` 值集合与 spec 触点表 ID 集合双向一致（precheck 已机械化）
- [ ] 同 `tp-wrap` 内的 `tp-marker` 数字与 `data-tp` 末段对应一致（precheck 已机械化）
- [ ] 抽查若干典型交互（保存 / 取消 / 关闭 / 提交）的 `data-tp` 命名是否符合 `proto_contract.md §四` 触点格式细则

### S4-25 `[MUST]` 移动端 sheet 形态须用标准 `.fb-modal-overlay + .fb-modal` 结构

PRD 中 `.phone-frame` / `.miniprogram-frame` 内的 modal 弹层（含 Action Sheet 形态）**必须**使用标准 `.fb-modal-overlay + .fb-modal` 结构 + `.is-visible` 触发；**禁止**用自定义 class（如 `.sheet` / `.bottom-sheet` / `.action-sheet` / `.popup` / `.modal-mask` / `.dialog`）+ inline `position: relative / absolute` + `flex: 1` 等自由发挥**完全规避**真源 class。

**Why**：`fb-fallback.css` L509-510 已实现 `.phone-frame .fb-modal { align-self: flex-end; width: 100%; max-width: 100% }` 自动 sheet 形态适配 — 标准 class 一加遮罩 + 贴底 + 全宽自动出，PM 自由发挥写 `<div class="sheet">` 会导致 ① 缺遮罩（无 `.fb-modal-overlay` 的 `background: var(--fb-overlay)`） ② 不贴底（绕开 `align-self: flex-end` flex 锚定）— /retro 2026-05-13 # 5 复盘根因 B 实际发生过。

**强制对应关系**（详见 `prd_expression_standard.md §零.2 反例禁令第 4 条 + 状态帧约束第 5 条` + `fb-fallback-manifest.md §3.2 Modal「移动端 Action Sheet 自动适配」`）：

| 项 | 规则 |
|----|------|
| 触发范围 | 仅 `.phone-frame` / `.miniprogram-frame` 容器内（`.desktop-frame` / `.h5-frame` / `.tablet-frame` 不在范围）|
| 标准结构 | `<div class="fb-modal-overlay is-visible"><div class="fb-modal">…</div></div>` |
| 自由发挥禁令 | class 含 `sheet` / `bottom-sheet` / `action-sheet` / `popup` / `modal-mask` / `dialog` 字面且非 `fb-*` 真源 → 视为违反 |
| 豁免 | `fb-*` 真源 class / proj.* 派生组件（class 含 `.`）/ 单纯 frame 容器自身 |

**机械化覆盖（可机械化档）**：

- `precheck_stage4.check_panel_class_evasion`（rule-5）扫 phone-frame / miniprogram-frame 容器内含 `SHEET_EVASION_KEYWORDS={sheet, popup, modal-mask, dialog}` 字面但非 `fb-*` 前缀的 class → WARN（v1）→ 下迭代评估升 FAIL

**Supervisor 审核检查项**：
- [ ] 抽查 `.phone-frame` / `.miniprogram-frame` 内是否有自定义 sheet/popup class 替代 `.fb-modal-overlay`（precheck 已机械化 WARN）
- [ ] 抽查 modal 状态帧是否含 `.fb-modal-overlay is-visible` 标准结构（与 §零.2 状态帧约束第 5 条对齐）

### S4-26 `[MUST]` 组件变更清单 thead 字面规范化

PRD `<section id="component-changelog">` 内 4 个 `changelog-group` (changelog-new / -update / -deprecated / -promote) 的 `<thead>` 字面**必须**与 `prd_expression_standard.md §11.1` + `proto_spec_md.md §八` 规范一致；**禁止**沿用旧版本表头字面（详 [禁用字面] 段）。

**强制对应关系**（详见 `prd_expression_standard.md §11.1 Section 结构` + `proto_spec_md.md §八 格式`）：

| sub-section | 期望 thead 字面 |
|------------|---------------|
| `changelog-new` | `组件 ID \| 派生原因 \| 使用页面 \| 组件说明锚点`（4 列）|
| `changelog-update` | `组件 ID \| 修改类型 \| 修改描述 \| 上一版本 \| 本版本 \| 影响页面`（6 列）|
| `changelog-deprecated` | `组件 ID \| 弃用版本 \| 弃用原因 \| 替代组件`（4 列）|
| `changelog-promote` | `组件 ID \| 建议原因 \| 当前使用项目数 \| 复用价值评估`（4 列）|

**禁用字面**（已废弃,不得出现）：

| 旧字面 | 废弃原因 |
|-------|---------|
| `类型`（新增段）| 与组件 ID 前缀 `proj.L*` + sub-section 分类信息冗余 |
| `触发原因`（新增段）| 重命名为「派生原因」语义更精确（仅新增段用，SSOT #8 双触发条件）|
| `使用模块`（新增段）| 升级到「使用页面」细粒度 `M{XX}-P{YY}` 可点击跳转 |
| `影响模块`（修改段）| 升级到「影响页面」（同上）|
| `spec / prd 锚点`（新增段）| 重命名为「组件说明锚点」（值仅指 §7.1 集中容器 `proj-component-{name}`，spec § 引用无实际用处）|

**机械化覆盖（可机械化档）**：

- `precheck_stage4.check_changelog_thead`：扫 component-changelog section 内每个 changelog-group 的 thead 字面 ↔ 期望列表严格 == 比对 + 禁用字面命中即 FAIL（含具体废弃原因提示）
- 无对应 group 静默豁免（本期某类无变更时 PRD 可整段不渲染该 group）

**Supervisor 审核检查项**：
- [ ] 4 个 changelog-group thead 字面与 §11.1 一致（precheck 已机械化 FAIL）
- [ ] 无禁用旧字面残留（precheck 已机械化）
- [ ] 「使用页面」/「影响页面」列实际值已升级到 `M{XX}-P{YY}` 细粒度（即使 assemble.py 兼容老 `M{XX}` 兜底,新产物应按 P 级粒度填）

### S4-27 `[MUST]` 派生模块引用 owner proj 组件的内部 slot class 完整性

派生模块（非 owner）在 PRD 草稿引用 owner 的 proj 组件时，**HTML 内部结构必须完整使用 owner 在 PROJ-CSS 中定义的全套 slot class**（容器 class + 所有内部子元素 class）；**禁止**用通用 `fb-*` class（如 `fb-tag` / `fb-chip` / 裸 `fb-search`）平铺替代 owner 定义的专用 slot class，**也禁止**完全退化为单行字面文本而不写任何 slot 结构。

**Why**：`§5.1` 规定 PROJ-CSS 真源唯一（owner 单源写、派生不重复声明）。SSOT 的完整外延是 **owner 定义的全套 class 名空间**（容器 class + 内部 slot class + 状态 modifier），派生引用时不可只取容器 class 而省略内部 slot class — 否则 owner 已为内部 slot 写好的样式（如 `.pf-status-chip { padding:4px 12px; border-radius:14px; background:var(--fb-primary-bg-light); }`）就因派生层 HTML 不写 `.pf-status-chip` 而无法作用，视觉退化为浏览器默认 `<span>` + 默认 background。

**强制对应关系**（详见 `proj_component_protocol.md §5.1` 末尾「派生模块引用 owner 组件的内部结构规则」）：

| 维度 | owner 模块 | 派生模块 |
|------|----------|---------|
| PROJ-CSS 块 | 写完整（base + 全部内部子元素 class + 全部状态 modifier）| 不写（重复声明触发 precheck FAIL）|
| HTML 引用 | 容器 class + owner 定义的全套内部 slot class | 容器 class + **同 owner 全套内部 slot class**（不可降级为通用 fb-* 平铺，也不可退化为单行字面） |
| 数据值 / 业务规则 | owner 自身视角 | 派生模块自身视角（仅数据值 + 业务规则差异） |
| 状态 modifier | owner + 派生均可用 | 派生按本模块业务态选择 modifier 组合 |

**机械化覆盖（可机械化档，v2 双分支判定）**：

`precheck_stage4.check_proj_slot_class_completeness` 算法：
1. 从 `scaffold.owner_assignments` 推算 `{proj_id → owner_module}`
2. 读 owner draft 的 `[PROJ-CSS-START..END]` 块，grep `.proj-{suffix}(?:.is-XXX)? .{prefix}-{name}` 提取 slot class 名集合
3. 扫派生 draft 中容器 `class="...proj-{suffix}..."` 处 30 行窗口
4. v2 双分支判定：
   - **分支 v1**：slot=0 且 `fb-tag` ≥ 2 → WARN（疑似 fb-tag 平铺）
   - **分支 v2**：slot=0 且 `fb-tag` = 0 且 可视文本长度 ≥ 20 → WARN（疑似完全退化为单行字面，NB-WE-33 增强）

**Supervisor 审核检查项**：
- [ ] 派生模块 draft 引用 owner proj 容器时，内部 slot class 集合 = owner default 帧的 DOM slot class 集合（precheck 已机械化 WARN）
- [ ] 无 fb-tag 平铺替代 owner 专用 slot class 的情况（precheck 已机械化）
- [ ] 无完全退化为单行字面文本（precheck 已机械化）

### S4-28 `[MUST · v3 CSS 变量继承 · WARN 阶段]` 统一底栏操作组结构完整性

> **状态**：v3 CSS Custom Property 继承机制（`.fb-action-bar` 统一类）替代 v2 三 class（`.fb-frame-bottom-bar` / `.fb-modal-footer` / `.fb-drawer-footer`），**当前 WARN 阶段**（下游迁移缓冲期）。下游全部迁移完 + dry-run 通过（≥ 2 下游实测 + FP < 30%）后升 **FAIL**。旧 3 class 保留作 deprecated 别名，v4 触发条件（全部迁移完成 + ≥ 3 个月）后删别名。

**规则文本（v3）**：

`[MUST]` 任意底栏操作组（"取消 / 保存"贴底按钮栏、表单提交栏、modal/drawer 内底栏等）：

1. **必须用 pub 组件 `.fb-action-bar`**（真源 `fb-fallback.css`，HTML 模板 `fb-fallback-manifest.md §3.11`），CSS 变量就近继承自动切换行为（frame 内 sticky 贴底 / modal·drawer 内静态居底）；
2. **嵌套深度不敏感**：`.fb-action-bar` 不依赖直子选择器（`>`）或兄弟选择器（`+`），可在任意深度嵌套使用；行为由 DOM 最近祖先容器（`.fb-modal` / `.fb-drawer` / `.{*}-frame`）声明的 `--bar-*` 变量决定，**就近优先天然胜出**；
3. **禁止** PM 在底栏元素写 inline `style="position:sticky/fixed"` / `bottom:0` / `background:...` 等真源管控的属性（绕过组件协议且复现 v2 inline 污染，quotation-tool L8705 实证；非真源管控属性如 `display:flex` 等 PM 可保留 — 但通常无需）；
4. **移动端 frame 直接子层 `.fb-action-bar` 按 `data-purpose` 判定**（v3 R2 升级，对齐 `proto_cross_platform.md §三 v2` 按页面状态分类）：
   - **合规白名单**：`data-purpose ∈ {page-main, multi-select-batch, workflow-nav}` → 合规
     - `page-main`：详情页主操作（≤ 4 个并列，配合 navbar `data-variant="detail"` 或 `"edit"`）
     - `multi-select-batch`：多选态批量操作（≤ 3 个并列，配合 navbar `data-variant="multi-select"`）
     - `workflow-nav`：向导上一步/下一步（配合 navbar `data-variant="workflow"`）
   - **其他场景 WARN**：无 `data-purpose` 或值不在白名单 → WARN（提示加显式 data-purpose 或改走 navbar variant + 「···」菜单 / modal/drawer 内嵌套）
   - **例外（不变）**：移动端 frame 内嵌套的 `.fb-modal` / `.fb-drawer` 内可用（变量继承自动取静态行为）；
5. **旧 v2 三 class 已 deprecated**（`.fb-frame-bottom-bar` / `.fb-modal-footer` / `.fb-drawer-footer`）：CSS 别名保留兼容期间仍生效（行为与 `.fb-action-bar` 完全等价），precheck 扫到 → WARN 提示迁移；下游可用 `pm-workflow/scripts/migrate_action_bar.py` 自动迁移。

**Why v3 CSS 变量继承（彻底治本）**：

- **v2 根因**：3 个独立 class（frame/modal/drawer 各一）命名冗余 + 视觉表现 95% 相同，PM 认知混乱致 16/24 处误叠加（`class="fb-modal-footer fb-frame-bottom-bar"`）；规范层未给清晰区分指引，机械 checker 仅扫结构层（父链路）无视语义层（用错 class）。
- **v3 治本**：5 个 CSS 变量（`--bar-position` / `--bar-bottom` / `--bar-margin-top` / `--bar-background` / `--bar-padding`），frame 类容器声明默认 sticky 行为基线，`.fb-modal` / `.fb-drawer` 容器覆盖为静态行为；`.fb-action-bar` 使用 `var(--bar-*)` 取值，CSS 引擎按 DOM 最近祖先值取 → 就近优先无源码顺序仲裁、嵌套深度不敏感。PM 只记一个 class，CSS 层透明自适应。
- **后代选择器 / 容器查询路径已否决**：后代选择器（`.phone-frame .fb-action-bar` vs `.fb-modal .fb-action-bar`）特异性相同时走源码顺序，cascade 重排即失效；容器查询（`@container`）按名字独立解析，不增特异性，多条命中仍走源码顺序——CSS 变量继承是唯一结构性"就近优先"机制。

**v1 / v2 / v3 演进史**：

| 版本 | 机制 | 失败 / 升级原因 |
|---|---|---|
| v1（2026-05-15 上线同日下线）| 启发式（`display:flex` + `button_count` 冒泡）"猜"底栏 | 5/5 false positive（quotation-tool 实战），PM 被 WARN 误导加 5 处 inline 污染（outputs L18812/L19350/L19628/L19813/L20489）|
| v2 档 C（2026-05-15 起）| 真源 class 匹配（`.fb-frame-bottom-bar` desktop/tablet）+ 5/29 加 inline 反规避 | PM 认知混乱致 16/24 处误叠加 modal-footer + frame-bottom-bar；下游 NB「pub 库缺 phone 类」推断错诊，真因是 v2 三 class 命名冗余 |
| v3（CSS 变量继承）| 单 class `.fb-action-bar` + 5 个 CSS 变量就近继承 | 治本：单 class 覆盖 frame/modal/drawer 三场景；嵌套深度不敏感；modal/drawer 未来分化无切换成本 |

**强制对应关系（SSOT #2 + #51 派生链，改任一处须全链同步）**：

| 角色 | 位置 |
|------|------|
| 技术真源 | `fb-fallback.css`：5 个 CSS 变量基线（`:where(.{*}-frame)`）+ `.fb-modal` / `.fb-drawer` 命名覆盖块 + `.fb-action-bar` 基础类（使用 `var(--bar-*)`）+ 3 旧 class deprecated 别名块 |
| 派生：HTML 模板 | `fb-fallback-manifest.md §3.11`（Action Bar 段，含 modal/drawer 内底栏示例 + 移动端禁令 + v4 演进预案） |
| 派生：组件索引 | `pub_components_index.md §3.3.5 布局类` + §4.5 反查行（fb-action-bar 单类覆盖三场景）|
| 派生：modal 段 | `fb-fallback-manifest.md §3.2 Modal`（modal-footer 示例改 `.fb-action-bar`） |
| 派生：drawer 段 | `fb-fallback-manifest.md §3.4 Drawer`（drawer-footer 示例改 `.fb-action-bar`） |
| 派生：端规范 | `proto_platform_desktop.md §三` + `proto_platform_app.md §三`（行文改 `.fb-action-bar`） |
| 派生：PRD 表达规范 | `prd_expression_standard.md §零.2.5` |
| 机械兜底（结构层）| `precheck_stage4.check_desktop_sticky_completeness`（升级：扫 `.fb-action-bar` / 3 deprecated 别名；检查移动端 frame 直接子层 + 旧 class deprecation WARN）|
| 机械兜底（inline 层）| `precheck_stage4.check_inline_position_compliance`（保留，错误信息更新指向 `.fb-action-bar`）|
| 自动迁移 | `pm-workflow/scripts/migrate_action_bar.py`（旧 3 class + 双重叠加 → `.fb-action-bar` 自动替换）|

**Supervisor 审核项（§4.4）**：抽样底栏操作组 → 核查是否用 `.fb-action-bar`（v3 标准）或旧 3 class（deprecated 别名，仍生效但 PM 应迁移）；precheck 标"已机械化（WARN）"，看 precheck 报告即可。

**v1 失败教训（前车之鉴，勿删）**：v1 启发式 2026-05-15 上线同日下线（< 1 小时），上游 /tmp 原型仅 1 处 false positive、下游真实 PRD 暴增 5/5——证明"启发式只适合特征空间可枚举的小场景，生产 PRD 多样性高时必踩坑"。dry-run 纪律已沉淀至 `workflow_maintenance_protocol.md`（NB-LIT-25-B B.2）：新增/大改 precheck 规则上线前须 ≥ 2 下游实测 + 人工核查命中样本 + false positive 率 < 30%。v1 原文见 commit `8dcf09e`（落盘）/ `18562db`（下线）。

**v3 关键设计原则（不变式守纪律）**：

- 5 类 frame 容器声明默认 sticky 行为基线（`:where()` 块，特异性 0，不与既有 inline 打架）；frame 容器**永不命名化**为命名容器（如 container queries 的 `container-name`），仅作 base 默认环境
- 命名覆盖容器（`.fb-modal` / `.fb-drawer`）当前覆盖值字面相同（都是 static + transparent + 12px 20px）— 未来某一项需分化时直接独立改其变量值即可（如 `.fb-drawer` 内底栏需特殊 padding），**无需重构 CSS 架构**——CSS 变量继承天然支持就近优先，新值随 DOM 嵌套自动胜出
- 加新容器（如未来 `.fb-popup` / `.fb-side-panel` 等）只需声明所需变量，自动加入就近优先链；新容器决策：base 行为（不声明变量）or 命名覆盖（声明覆盖变量）

---

### S4-29 `[MUST]` 页面层级架构（spec §3.0 / PRD spec-sitemap）SSOT 同步

**规则文本**：

`[MUST]` spec.md 区块1 须含 `### 3.0 页面层级架构`、PRD 产品规格区须含 `<section id="spec-sitemap">`「页面架构总览」（侧栏「产品规格」组末位）。两侧层级图均**由 `assemble.py build_hierarchy_mermaid` 从 `scaffold.json modules[].pages[]` 现场派生**「产品根→模块→页面」两层 mermaid（SSOT 双锚 #38）：

1. **禁止 Foundation / 任何 PM 凭空写或手改本节**；Foundation 仅在 spec 区块1 顶（§3.1 之前）写占位 marker `<!-- [SITEMAP-3.0] -->`，内容由 assemble Step4 替换；
2. 粒度仅到页面级（状态已在侧栏三层 + §3.2 流转图覆盖，不重复）；页面总数 > 40 自动按模块拆 subgraph；
3. 改 scaffold 后须重跑 `assemble.py spec` + `assemble.py prd` 刷新派生层（禁反向手改 outputs）；
4. 页面节点 ID 固定 `M{XX}_P{YY}` 形态——precheck 据此可靠计数，PM 禁改派生产物节点 ID。

**Why（派生 + 数对称兜底，非启发式）**：

- 下游（开发 / 测试 / 设计）深入逐页规格前缺「按模块分组的页面树」整体定位地图（现状散在 stage3 路由表 / spec §3.1 扁平清单 / §3.2 流转图）；§3.0 填此结构性缺口。
- 单一真源 = scaffold.json，assemble 现场派生（**不预烘焙**，H1=(c) 按引用消费）→ 零漂移面、零 Foundation 手写负担；与 §3.4 业务流程图（SSOT #30）「源在别处·本地放置·precheck 数对称」同构。
- 判定为"数对称 diff"而非启发式：节点 ID `M\d+_P\d+` 由 `build_hierarchy_mermaid` 严格生成，distinct 计数与 scaffold pages 数严格 diff，≈ 0 false positive。

**强制对应关系（SSOT #38 派生链，改任一处须全链同步）**：

| 角色 | 位置 |
|------|------|
| 数据真源 | `process_record/tasks/scaffold.json modules[].pages[]` |
| 派生算法 | `assemble.py build_hierarchy_mermaid` / `inject_spec_sitemap` / `inject_prd_sitemap` |
| 派生：空壳 | `gen_scaffold.py DERIVED_SPEC_ITEMS`（spec-sitemap 空壳 + `<!-- [SITEMAP-PRD] -->` 占位，与 SPEC_ITEMS 解耦） |
| 派生：spec | spec.md 区块1 `### 3.0 页面层级架构`（Foundation 仅写 `<!-- [SITEMAP-3.0] -->` marker） |
| 派生：prd | `<section id="spec-sitemap">`「页面架构总览」 |
| 规范 | `proto_spec_md.md §3.0` + `prd_expression_standard.md §一/§二` + `agent_dispatch_protocol.md Step2` |
| 机械兜底 | `precheck_stage4.check_page_hierarchy_sitemap`（两侧存在性 + mermaid 页面节点 `M\d+_P\d+` distinct 数 == scaffold pages 数；FAIL 阻断 Step 7 自审）|
| **同族对称依赖（必成对，缺则死锁）** | 本规则强制 spec-sitemap **必含 mermaid**，故 `check_prd` 局部豁免白名单**必须**含该 section：`proto_contract.md §十一`（真源，含 `sitemap` 行）⇔ `precheck_stage4.MERMAID_ALLOWED_SECTION_KEYWORDS`（派生，含 `"sitemap"`）。二者须同增同改——缺则与本规则互斥死锁（agent_methodology §七.2；下游 NB 上报已修，prevent 复发）|

**Supervisor 审核项（§4.4）**：precheck 标"已机械化（FAIL）"——看 precheck 报告即可，无需精读层级图（数对称由脚本保证）；仅需确认 Foundation 写了 `<!-- [SITEMAP-3.0] -->` marker（漏写 precheck 已 FAIL）。

---

### S4-30 `[MUST]` 页面结构范式契约（提议2）— 结构+过程 A 级兜底 / 判断层 B 组挂账

**规则文本**：

`[MUST]` scaffold.json 顶层须含 `page_archetypes[]`（页面结构范式定义本体，每条 `{id,name,regions:[{slot,hosts}],invariants:[],extension:[]}`），每个 `modules[].pages[].archetype` 必填且引用合法（∈ page_archetypes ids）。Step3/5 模块 subagent 填/绘每页前**强制前置**做容纳性二值校验（按 `proto_spec_md.md`「页面结构范式契约」SOP）：

1. 从 scaffold **现场读** archetype + 定义（不预烘焙，H1=(c)）；
2. 枚举本页强制元素（**H3 分步**：Step3 = scaffold states + 产品定义功能点；Step5 = 完整 spec 草稿含触点）；
3. 二值判定：PASS → 严格照范式结构填/绘、零自由度；FAIL → 不填该页 + 结构化冲突报告、仅阻塞该页、回报编排器（复用 SSOT #31 → 路径 B 改 scaffold.page_archetypes）；
4. 无论 PASS/FAIL，每页一行**定长记录**写入模块子进度文件 `## 页面结构容纳性校验记录` 段；
5. 范式增殖纪律：系统性结构问题改共享范式定义（路径 i），仅独立结构类型才新建范式（路径 ii），Step1.X D-08 审核。

**Why（A+C 债处理，诚实分层）**：

- 提议2 解决"Step5 模块 PRD 按模块并行绘制 → 相似页面跨模块布局发散"的结构性风险；契约在并行前由 PM 定、Step1.X 审。
- **结构层 + 过程层 = A 级机械兜底**；**判断层（每条容纳判断对不对）不可脚本化 → B 组低优挂账**（靠 Step1.X + 终审 + subagent 二值闸三道非脚本门）。**不做**事后启发式 archetype 错配 precheck（违 `workflow_maintenance_protocol §dry-run 纪律` FP≥30% 禁上线 + NB-LIT-25-B 教训）。

**强制对应关系（SSOT #39 派生链，改任一处须全链同步）**：

| 角色 | 位置 |
|------|------|
| 数据真源 | `scaffold.json page_archetypes` + `modules[].pages[].archetype` |
| 派生算法 | `assemble.py build_archetype_contract_md` / `_html` / `_iter_page_archetype_map`（注入 Commit1 §3.0/spec-sitemap，colocate）|
| 结构兜底（首次闸）| `gen_scaffold.validate_v2_schema`（page_archetypes 必备键 + archetype 引用不悬空，Step1.5）|
| 结构兜底（恒跑承接）| `precheck_stage4.check_page_archetype_contract`（Step6.5——post-Foundation gen_scaffold 不再跑，由此承接）|
| 过程兜底（C，拉回 A）| `precheck_stage4.check_archetype_containment_record`（定长记录每页齐全+覆盖；不校验判断对不对）|
| 规范 | `proto_spec_md.md`「页面结构范式契约」段 + `agent_dispatch_protocol.md` Step1/1.X/Step3/Step5 + 回退决策表 |
| 角色 | `AI产品经理_Agent.md` 子阶段一步骤8 / 子阶段三·五步骤4.5 + `AI产品主管_Agent.md §4.5 D-08` |
| 判断层（B 组，不可机械化）| Step1.X Supervisor D-08 + 终审 + subagent 二值闸（非脚本门）|

**Supervisor 审核项（§4.4）**：结构+过程层 precheck 标"已机械化（FAIL）"看报告即可；判断层须按 §4.5 D-08 人工核查 page_archetypes 范式合理性 + 每页 archetype 分配 + 无范式增殖（系统性问题应路径 i 改共享定义）。

---

### S4-31 `[MUST]` 模块架构说明（提议3）— 跨阶段一致，干净 A 组数对称

**规则文本**：

`[MUST]` 模块架构（模块清单 + 依赖 + 职责）须从阶段 2 §三贯穿到阶段 4：

1. 阶段 3 `tmpl_产品定义.md §6.5 产品架构` 复述自阶段 2 §三（模块清单+依赖+职责，禁凭空写，字面与阶段 2 一致）；
2. PM 子阶段一据阶段 3 §6.5 构建 `scaffold.json modules[]`：`name`（必）+ `depends_on`（复用既有，作依赖边）+ `purpose`（**可选**，缺省不阻断、assemble 回退 `—`）；
3. 阶段 4 `assemble.py build_module_arch_*` 从 scaffold.modules 现场派生「模块架构说明」（模块表 + 模块依赖 `graph TB`，Item 3 方向 LR→TB），与 §3.0 页面层级图、提议2 契约 **colocate** 注入 spec §3.0 / PRD spec-sitemap，禁手改；
4. 改 scaffold.modules 后须重跑 `assemble.py spec`+`prd` 刷新；阶段 2 §三 改动须逐层下传（§6.5 复述 → scaffold → assemble），禁反向。

**Why（与 #30 同型，全数对称无判断层）**：

- 补齐 §3.0 页面层级（结构树）、§3.4 业务流程（系统协作）之外的**模块组成与依赖视图**——下游开发/测试读 spec 即得"产品由哪些模块、谁依赖谁、各负责什么"，无需回溯阶段 2。
- 判定均为**数对称 diff**（阶段3 §6.5 模块数 == 阶段2 §一模块数；spec/PRD 模块表行数 == scaffold.modules 数；依赖边数 == depends_on 总数）——**无判断层、≈0 false positive，SSOT #40 干净 A 组 5/5**（区别于 #39 带 B 组债）。

**强制对应关系（SSOT #40 派生链，改任一处须全链同步）**：

| 角色 | 位置 |
|------|------|
| 业务定义真源 | `tmpl_功能规划.md §三 产品架构`（尤 3.2 模块依赖关系表）|
| 派生1（阶段3 复述）| `tmpl_产品定义.md §6.5 产品架构` |
| 派生2（scaffold）| `scaffold.json modules[]` {name, 可选 purpose, depends_on} — PM 子阶段一据 §6.5 构建 |
| 派生3（阶段4 渲染）| `assemble.py build_module_arch_md/_html` → spec §3.0 / PRD spec-sitemap「模块架构说明」(colocate) |
| 规范 | `proto_spec_md.md §3.0`「模块架构说明」段 + `prd_expression_standard.md`（spec-sitemap colocate）+ `agent_dispatch_protocol.md`（purpose 字段/Step1）|
| 角色 | `AI产品经理_Agent.md` 阶段3 执行要点 + 子阶段一步骤9 / `AI产品主管_Agent.md §4.3 + §4.5 D-09` |
| 机械兜底 | `precheck_stage3.check_section_6_5`（阶段3 §6.5 模块数 == 阶段2 §一）+ `precheck_stage4.check_module_architecture`（S4-31，spec+PRD 模块表行数/依赖边数 == scaffold；FAIL 阻断）+ `gen_scaffold.validate_v2_schema`（purpose 可选类型）|
| **同族对称依赖（必成对，缺则死锁）** | 模块依赖图 mermaid 同在 spec-sitemap，本规则强制其存在 → `check_prd` 局部豁免须含 `sitemap`：`proto_contract.md §十一`（真源）⇔ `precheck_stage4.MERMAID_ALLOWED_SECTION_KEYWORDS`（派生），同 S4-29，须同增同改（agent_methodology §七.2）|

**Supervisor 审核项（§4.4）**：全机械化（FAIL）——precheck 报告即可；§4.3「产品架构跨阶段一致性」+ §4.5 D-09 仅人审字面值（模块名/职责是否如实复述，数对称已由脚本兜底）。

---

### S4-32 `[MUST · WARN 档 C · WARN 阶段]` 页面骨架屏（SSOT 双锚 #41，WE-H per-archetype）— 单源双渲染

> **状态**：2026-05-18 降 WARN 阶段（对齐 S4-25/S4-28）；**2026-05-19 WE-H #41 颗粒度重设 per-page → per-archetype + 条件 per-page override**（原始构想即"一类页面一个骨架、页面架构章节统一说明"——WE-A→WE-G 误优化成 per-page，SNB-006/WE-G 成本皆该错颗粒度的；#41 = #39 视觉化身，本批回正）。仍 WARN 阶段。**升 FAIL 条件（重基线）**：下游全部完成 **per-archetype 范式骨架良构 + 个别 override 良构**迁移后，按 `workflow_maintenance_protocol.md §dry-run 纪律`（≥2 下游实测 + 人工核查 + FP < 30%）升 **FAIL**（逆向**当前 WE-H 后** check 结构，**非 WE-D2/WE-G 旧基线**；1-vs-N/per-platform token 仍判断层 WARN，不入 FAIL）。

**规则文本（WE-H per-archetype + 条件 per-page override）**：

`[MUST]` 平面布局以**单源 ```skeleton 片段**表达，颗粒度 = **per-archetype**：

- **范式骨架（默认主体）**：唯一源 = `drafts/spec_foundation_draft.md`「## 范式骨架」内每范式 `- **<aid> 范式名**` 锚行下的 ```skeleton 块（gen_scaffold 据 `scaffold.page_archetypes` 预生成 ~N 占位，**Foundation 子阶段二**按范式填一次，被所有引用该范式的页复用）。
- **per-page override（罕见，条件）**：默认页复用其 `archetype` 的范式骨架（`S2.M[XX].1` per-page 槽是纯注释 marker，**非活动围栏，无"每页必填"压力**）；仅当某页 2D 排布确无法套范式（判断层、不机械化）才在该页 marker 下新增 ```skeleton 覆盖块。

约束（范式骨架 / override 共用）：

1. 围栏 ` ```skeleton `（agnostic）**或** ` ```skeleton:{frame} `（frame ∈ {phone,desktop,tablet,h5,mp}，WE-G 条件 per-platform，archetype/override 级均适用）；每块首内容行**字面恒为**固定免责注释（`SKELETON_DISCLAIMER`，三处字面同步：`proto_spec_md.md §四`真源 ⇔ `gen_scaffold.py` ⇔ `precheck_stage4.py`）；一范式/一 override 内 EITHER 1 agnostic OR ≥1 per-platform、**不混用**，非法/未知 frame token → WARN；
2. 白名单：仅 `<div>`；`class ∈ {sk-page,sk-row,sk-col,sk-region}`；属性仅 `data-r`/`data-w`/`data-h`；禁真实组件标签 / inline `style=` / 真实文案 / 嵌套 > 3 层（逐块校验）；
3. `data-r` 值必 ⊆ 该 archetype 的 `page_archetypes[].regions[].slot ∪ extension`（范式骨架据其 `<aid>`、override 据本页 `archetype`；**#39 仍为容纳权威**，骨架屏是其符合性视图，非组件树 / 非实现 DOM）；
4. `assemble.build_archetype_skeleton_md/_html` 据 `- **<aid>**` 白名单映射，派生注入 spec.md §3.0「#### 范式骨架」子节（#39 契约表后，子决策B 独立子节）+ PRD spec-sitemap `<div id="sk-askel">`（每范式 `<div id="sk-askel-<aid>">` 子锚）；`assemble.inject_page_skeletons` 对非 override 页注入「结构范式」chip 深链 `sk-askel-<aid>`、对 override 页注入专属骨架 + distinct 标记（每页首帧前 `<!-- [PAGE-SKELETON: {mid}-{pid}] -->` 占位）；PRD 侧禁另写骨架，杜绝漂移；
5. 调整方向：先改 `spec_foundation_draft.md`「## 范式骨架」/ 模块草稿 override，重跑 `assemble.py spec`+`prd` 刷新；禁反向手改 outputs。

**Why（per-archetype + WARN 阶段 + exact 判定，诚实分层）**：

- **per-archetype 而非 per-page**：#41 = #39（page_archetypes）的视觉化身——"一类页面一个骨架"本就是 #39 既有概念的可视化，per-page 是错颗粒度（SNB-006 追溯 BLOCK / WE-G 跨端发散成本 / "排列太乱"皆其症状）。回正后：范式数 N ≪ 页数，下游撰写量骤降；非 override 页帧旁仅小 chip 无骨架，"排列太乱"基本消解；pre-WE-E 概览位（spec-sitemap）对 per-archetype 本就正确（非 WE-E 批"重复页清单"——是 ~N 小目录）。
- 取代原 ASCII 树；单源双渲染（spec.md §3.0 结构解析 + PRD sk-askel 色块画廊）杜绝双写漂移。
- 判定为高精度 exact（每范式 ≥1 良构骨架 / 首行免责字面 / 非 div / inline style / class 越白名单 / `data-r` ⊄ archetype / override 良构 / PRD sk-askel + 子锚齐全 / per-platform token 合法）+ 启发项（嵌套 > 3）——**但当前全 r.warn 不 FAIL**（WARN 阶段 档 C），存量迁移完升 FAIL。exact 判定 ≈0 FP，WARN 仅为迁移缓冲。
- **为何不机械化「1-vs-N / 是否 per-platform / 是否 override」**：`#41` 价值 = 2D 排布+占比（相对 #39 区域清单的增量），"布局是否跨端发散"/"该页是否无法套范式" 是设计判断（同 #39 容纳判断属判断层）——事后启发式必高 FP（违 `workflow_maintenance_protocol §dry-run 纪律` FP≥30% 禁上线 + NB-LIT-25-B + S4-32 自身 SNB-006 追溯硬阻断教训）。故 S4-32 **只逐块校形 + 平台 token 合法 + 每范式有骨架**（exact），**不判**"该不该 per-platform / 该不该 override"（判断层，靠 §四指引 + 设计/终审人审）。
- **dry-run 纪律 + 教训**：新结构 precheck 规则即便 exact 判定，凡**追溯性作用于存量产物**者必先 WARN-phase（S4-25/S4-28/本规则同型，SNB-006 教训：WE-A4 误以 FAIL 上线致 17 页 BLOCK）；不伪造 dry-run 数据亦不跳过 WARN 缓冲。WE-H 颗粒度回正后下游迁移量骤降（N 范式 vs 17+ 页），但仍守 WARN-phase 迁移纪律。

**强制对应关系（SSOT #41 派生链，改任一处须全链同步）**：

| 角色 | 位置 |
|------|------|
| 数据真源（范式骨架，单源）| `drafts/spec_foundation_draft.md`「## 范式骨架」内每范式 `- **<aid>**` 锚行下 ```skeleton（Foundation 子阶段二填）|
| 数据真源（per-page override，条件）| 模块草稿 `S2.M[XX].1` 该页 marker 下新增的 ```skeleton（罕见，PM 子阶段三判断）|
| 占位/锚行生成 | `gen_scaffold.build_foundation_skeleton_draft`（每范式 `- **<aid>**` 锚 + ```skeleton 占位 + `SKELETON_DISCLAIMER` 首行）+ `build_spec_module_draft`（per-page override-only 纯注释 marker）|
| 派生1（spec.md §3.0 范式骨架子节）| `assemble.build_archetype_skeleton_md` → `inject_spec_sitemap`（#39 契约表后，子决策B）|
| 派生2（PRD sk-askel 画廊 + 帧旁 chip/override）| `assemble.build_archetype_skeleton_html` → `inject_prd_sitemap`（`<div id="sk-askel">` + 每范式 `sk-askel-<aid>` 子锚）+ `inject_page_skeletons`（非 override 页 chip 深链 / override 页专属骨架，START/END 幂等）|
| 结构兜底 | `precheck_stage4.check_page_skeleton`（S4-32：① 每 archetype 有良构骨架 + data-r⊆该范式 ② per-page override 良构 ③ PRD sk-askel + 子锚齐全 + 嵌套/平台token **全 WARN**（档 C，迁移完升 FAIL）；`_validate_skeleton_blocks` 共享校验器）|
| 规范 | `proto_spec_md.md §四「页面结构（骨架屏）」`（真源）+ `§三.5`（.1 override-only 槽 + §四↔§三.5 对齐）+ `prd_expression_standard.md §A-09`（范式骨架画廊 + 帧旁 chip/override + 区域A CSS 镜像）|
| 视觉真源 | `prd_template.html <style> .sk-*` + `applySkeletonDims()`（SSOT #4 真源，`§A-09` 区域A CSS 字面镜像）|
| 角色 | `AI产品经理_Agent.md` 子阶段二（Foundation 填范式骨架）/ 子阶段三 5.1（默认复用、罕见 override 判断）/ `AI产品主管_Agent.md`（骨架屏审核项）|

**Supervisor 审核项（§4.4）**：结构层机械化但 **WARN 阶段（档 C）不阻断**——precheck WARN 清单须同步入 state.md 非阻塞清单（同 S4-28）；人审"范式骨架是否如实示意该类页面平面布局 + override 是否确属无法套范式"（语义层 + 范式增殖/override 滥用纪律）+ 存量产物 per-archetype 迁移进度（升 FAIL 前置）。

---

### S4-33 `[MUST · WARN 阶段]` mermaid 块语法校验（mmdc 实际 parse，SSOT 双锚 #43）

> **状态**：2026-05-22 落地，WARN 阶段（下游反馈批 2，根因 B 整类消除）。**升 FAIL 条件**：按 `workflow_maintenance_protocol.md §dry-run 纪律`（≥2 下游实测 + 人工核查 + FP < 30%）；mmdc parse 是 deterministic、FP ≈ 0，下游 3 仓 dry-run 通过后即可升 FAIL（带语法错的图进不了产物）。

**规则文本**：

`[MUST]` PRD `<pre class="mermaid">` / spec ```mermaid 块**必须能被 mermaid 引擎实际 parse**——precheck 调用 `mmdc`（@mermaid-js/mermaid-cli）对每个 mermaid 块实际渲染，语法错（括号未引号 / edge label 缺失 / 时序图语法 / flowchart 节点定义错等）则报告，一次性消除 #23/#26/#34/#35 类 mermaid 语法反复。

约束：

1. 提取范围：PRD `<pre class="mermaid">` 块（人类交付超集，经 `html.unescape` 匹配 mermaid.js 运行时所见）优先；PRD 无块时回退校 spec ```mermaid 块；
2. 性能：所有块拼一个临时 markdown 文件，mmdc 单次渲染（chrome 仅启一次，~1-2s/十余块），不逐块 launch；
3. 降级纪律：mmdc 未安装（`npm install -g @mermaid-js/mermaid-cli`）/ 渲染超时 / 调用异常 → **WARN 跳过，不阻断**（下游无 mmdc 时静默降级）；puppeteer 需 `--no-sandbox`（Ubuntu 23.10+ unprivileged userns 限制），由临时 config 注入；
4. mmdc 在首个错误块停止——WARN 提示"修复后重跑捕获后续"。

**Why（机械门禁治本 vs 人审反复）**：mermaid 语法错是 #23/#26/#34/#35 反复出现的整类问题——人审 / 现有 check_prd「游离 mermaid」位置校验都抓不到"块本身能否 parse"（位置对但语法错仍渲染失败白屏）。mmdc 实际 parse 是唯一可靠判据。WARN 阶段是 dry-run 纪律（即便 FP≈0 也先 WARN 给下游缓冲），非语义不确定。

**强制对应关系（SSOT #43 派生链）**：

| 角色 | 位置 |
|------|------|
| 机械兜底真源 | `precheck_stage4.check_mermaid_syntax`（提取 + mmdc 单次渲染 + WARN）+ `_find_mmdc`（PATH→npm prefix→常见位置探测）+ `_extract_mermaid_blocks`（pre/fence 双格式 + html.unescape）|
| 工具依赖 | `mmdc`（@mermaid-js/mermaid-cli，npm install -g）；缺失则 WARN 跳过 |
| 与既有 check 边界 | 与 `check_prd`「游离 mermaid」位置校验正交——本规则校**语法（能否 parse）**，check_prd 校**位置（该不该出现在此 section）** |

**Supervisor 审核项（§4.4）**：WARN 阶段不阻断——precheck WARN 清单须同步入 state.md 非阻塞清单（同 S4-28/S4-32）；下游 dry-run + FP<30% 通过后升 FAIL。

---

### S4-34 `[MUST · WARN 阶段]` 触点 canonical 引用完整性（SSOT 双锚 #44，item 6 治本）

> **状态**：2026-05-22 落地，WARN 阶段（下游反馈批 2，根因 D 治本）。**升 FAIL 条件**：按 `workflow_maintenance_protocol.md §dry-run 纪律`（≥2 下游实测 + 人工核查 + FP<30%）；canonical 集合成员校验是 deterministic、FP≈0，下游 3 仓预声明 touchpoints + dry-run 通过后升 FAIL。

**规则文本（治本①②）**：

`[MUST]` 触点编号从 **scaffold.pages[].touchpoints[] canonical 清单**生成/引用，PM 不在 spec/prd 手写：

- **① canonical 单源**：`scaffold.pages[].touchpoints[]`（每项 `{id: "T01"/"D01", kind: "trigger"/"data", element, action}`，T=主页触点 / D=弹窗抽屉内触点，页面内唯一）；canonical 全 ID = `{mid}-{pid}-{tp.id}`（如 M01-P01-T01）。任务规划 PM 子阶段一在 scaffold 预声明（取代旧两段式中 Spec Agent 自由分配 T[NN]）。
- **生成**：`gen_scaffold.build_spec_module_draft` 据 scaffold.touchpoints 预填 spec 触点表行（canonical ID 行机器生成），Spec Agent 仅补描述列（元素 / 触发动作 / 系统响应），**禁止增删 / 修改 ID**。
- **② 引用校验**：`precheck_stage4.check_touchpoint_canonical` 扫 spec/prd 中所有 `M[XX]-P[YY]-[TDC][NN]` 引用必 ⊆ canonical 集合；不在集合内（PM 手写偏差 / 拼写错 / 跨页串号）→ WARN。比"补少位正则"更根本——杜绝 D4/D5 类一切手写偏差。

**`[Must]` v2 升级（SSOT #65，2026-06-02 下游 D3 治本）**：触点前缀正则 `[TD]` → `[TDC]` 扩 T/D/C 三系（详 `proto_contract.md §四.A`）：
- **T** = Trigger（用户主动触发的交互入口）
- **D** = Data display（单字段被动回显）
- **C** = Container（多字段聚合的展示单元 ≥ 2 字段 UI 块）
- precheck `check_touchpoint_canonical` 正则 `M\d+-P\d+-[TDC]\d+` 已升级，向后兼容（旧 T/D 触点 ID 仍匹配）
- scaffold `touchpoints[].kind` 字段建议扩 `"container"` 值（NB-WE-06 待后续，本批次未实装 schema 扩展 + gen_scaffold validate 同步）
- C 触点判定条件 ≥ 2 项满足启发式空间复杂，当期不实装独立 precheck（NB-WE-06 挂账）

约束：

1. **向后兼容**：scaffold 无 touchpoints[] 声明（旧两段式产物）→ check 跳过（OK），不阻断迁移；gen_scaffold 保留旧静态占位 + 两段式提示（标 `[Should] 治本路径`）；
2. canonical 增删触点须回 scaffold.touchpoints[] 重跑 gen_scaffold，禁止在 spec/prd 直接增删 ID（违反即 outside-canonical WARN）；
3. 未引用 canonical（scaffold 声明但页面未用）也 WARN（核对漏渲染 / 多声明）。

**Why（canonical 单源 vs 两段式手写）**：旧两段式（Step 1 预分配前缀 + Step 3 Spec Agent 填 T[NN]）中 T[NN] 由 Spec Agent 手写，反复出现 D4/D5 类偏差（补少位 / 拼写 / 跨页串号）。治本 = 把全量触点 ID 上移到 scaffold canonical 单源，gen_scaffold 机器生成、precheck 集合校验——从根消除手写空间。WARN 阶段是 dry-run 纪律（下游需迁移到预声明 touchpoints），非语义不确定。

**强制对应关系（SSOT #44 派生链）**：

| 角色 | 位置 |
|------|------|
| canonical 单源 | `scaffold.json pages[].touchpoints[]`（PM 子阶段一预声明）|
| schema 校验 | `gen_scaffold.validate_v2_schema`（touchpoints 可选；存在则 id `^[TD]\d{2}$` + 页面内唯一 + kind∈{trigger,data}）|
| 生成 | `gen_scaffold.build_spec_module_draft`（据 touchpoints 预填 spec 触点表 canonical 行）|
| 引用校验兜底 | `precheck_stage4.check_touchpoint_canonical`（`_build_touchpoint_canonical` 构集 + spec/prd 引用 ⊆ canonical，WARN）|
| 规范 | `proto_contract.md §三/§四`（触点编号体系：canonical 单源取代两段式手写）|
| 角色 | `AI产品经理_Agent.md` 子阶段一（scaffold 预声明 touchpoints）/ 子阶段三（Spec Agent 仅补描述，禁改 ID）|

**Supervisor 审核项（§4.4）**：WARN 阶段不阻断——precheck WARN 清单须同步入 state.md 非阻塞清单（同 S4-28/S4-32/S4-33）；下游迁移到预声明 touchpoints + dry-run + FP<30% 后升 FAIL。

---

### S4-35 `[MUST · v2 data-variant · WARN 阶段]` 移动端 navbar 7 variant + 返回入口完整性（SSOT 双锚 #45，item 2① 配套）

> **状态**：v2 升级 2026-05-30 落地（7 variant data-variant 显式声明机制），WARN 阶段（下游迁移缓冲期）。v1 → v2 升级动因：v1 仅"次级页面 navbar 强制 .fb-nav-back"过于单一，无法覆盖列表多选态 / 表单确认 / 编辑态 / 主页等 6 个非 detail 场景；quotation-tool 多选态 PM 用 inline div 自由发挥实证（multi-select 顶部 `<div style="padding:8px 16px">` 已选 N/M + 退出）。v2 治本：navbar 单一类 + 3 slot + PM 显式 `data-variant` 自报；零启发式 precheck 按字面判定（避免 v1 启发式 5/5 FP 教训）。**升 FAIL 条件**：下游迁移完成 + dry-run（≥ 2 仓实测 + FP < 30%）后升 FAIL。

**规则文本（v2）**：

`[MUST]` 移动类端口（`.phone-frame` / `.h5-frame` / `.miniprogram-frame` / `.tablet-frame`）顶部 sticky 容器用 pub 通用组件 `.fb-navbar`，按 7 variant 区分业务场景：

- **① 结构约束**：`.fb-navbar` 须为移动类 `*-frame` 的**直接子元素**（置首位、与主内容区同层）；sticky 贴顶由真源 class 自带（`position:sticky;top:0`），PM 禁写 inline `position:sticky` / `top:0`。放错层 → sticky 失效（WARN）。
- **② data-variant 显式声明**：PM 写 `.fb-navbar` 时**必须**加 `data-variant="XXX"` 属性明示业务场景；未声明默认 `detail`（向后兼容现有用法）。零启发式 + 严格字面判定 + FP ≈ 0。
- **③ 7 variant + S4-35 .fb-nav-back 强制范围**：

| data-variant | 业务场景 | left slot | center slot | right slot | .fb-nav-back |
|---|---|---|---|---|---|
| `detail`（默认）| 次级详情页 | `.fb-nav-back` | `.fb-nav-title` | `.fb-nav-action` ≤1 | **强制** |
| `multi-select` | 列表多选态 | `.fb-btn-text`（取消）| `.fb-nav-title`（已选 N/M）| `.fb-btn-text`（全选）| 不强制 |
| `confirm` | 表单/浮层确认 | `.fb-btn-text`（取消）| `.fb-nav-title` | `.fb-btn-primary`（确认）| 不强制 |
| `edit` | 编辑态密集 | `.fb-btn-text`（完成）| `.fb-nav-title` | `.fb-nav-action`（···）| 不强制 |
| `list` | 列表入口页 | `.fb-nav-back`（可选）| `.fb-nav-title` | `.fb-nav-action` × N | 可选 |
| `workflow` | 向导分步 | `.fb-nav-back`（上一步）| `.fb-nav-title`（步骤 X/N）| `.fb-nav-action`（跳过）| **强制** |
| `home` | 主页/Tab | — | `.fb-nav-title`（logo）| `.fb-nav-action` × N | 不强制 |

- **④ center slot 容器约定**：PM 总用 `.fb-nav-title` 作 center 子元素（已有 `flex:1 1 auto` 自动占据剩余空间居中），即使内容是"已选 N/M" / "步骤 X/N" 等非标题文字。
- **⑤ 自由发挥禁令**：禁止 PM 用 inline `<div style="position:sticky;top:0">` 或自定义 class（`.toolbar` / `.top-bar` / `.action-strip` 等）实现顶部 sticky 容器，必须用 `.fb-navbar` + 适当 variant。`precheck_stage4.check_panel_class_evasion` 扩展拦截移动端 frame 直接子层 inline sticky 顶部容器（WARN）。

**Why v2（治本路径）**：

- **v1 根因**：navbar API 单一（仅 detail 模式 .fb-nav-back/.fb-nav-title/.fb-nav-action），无法表达多选态 / 确认 / 编辑等场景 → PM 无 pub 组件可用 → 自由发挥写 inline div（multi-select 顶部 inline 实证）→ 违反 SSOT 派生层禁修真源精神。
- **v2 治本**：单一 `.fb-navbar` 类 + 3 slot 灵活布局 + 7 variant 按 PM 自报 `data-variant` 判定；不新增 modifier class（保持 v3 单一类哲学）；CSS 实际 0 改动（.fb-nav-title `flex:1 1 auto` 已支持 center 自动居中）。
- **后代选择器 / 启发式判定路径已否决**：依"页面类型"启发式推断 variant 会重蹈 v1 启发式 5/5 FP 教训（quotation-tool 实战）；data-variant 显式声明是唯一结构性"零启发式"机制。

**v1 / v2 演进史**：

| 版本 | 机制 | 升级原因 |
|---|---|---|
| v1（2026-05-22 起）| navbar 单一 detail 模式 + 强制 .fb-nav-back | quotation-tool multi-select 实证 PM 用 inline div 自由发挥 → API 单一致 PM 绕过 SSOT |
| v2（2026-05-30 起 data-variant）| 7 variant + 显式声明 + 零启发式 | 单一类哲学 + 单一 API 覆盖 7 场景 + 0 FP |

**强制对应关系（SSOT #45 派生链）**：

| 角色 | 位置 |
|------|------|
| 视觉真源 | `bujue-design-system/fb-fallback.css` `.fb-navbar`（注释升级 v2 7 variant 说明）/ `.fb-nav-back` / `.fb-nav-title` / `.fb-nav-action` |
| 调用模板 | `bujue-design-system/fb-fallback-manifest.md §3.12 v2`（7 variant slot 填充矩阵 + 7 HTML 示例 + data-variant 显式声明）|
| 索引 | `bujue-design-system/pub_components_index.md §3.3.5 布局类 + §四 4.5`（navbar 7 variant 行 + 6 反查行）|
| 规范 | `proto_cross_platform.md §三 v2`（按页面状态分类替代按操作数量分类 + 7 场景矩阵 + 5 处实证转合规路径）/ `proto_platform_h5.md` / `proto_platform_miniprogram.md` |
| 引用校验兜底（结构层）| `precheck_stage4.check_back_entry` v2（按 `data-variant` 精确判定：仅 detail/workflow 强制 .fb-nav-back，其他 variant 用 [取消]/[完成] 替代；缺省 data-variant 等同 detail）|
| 引用校验兜底（反规避层）| `precheck_stage4.check_panel_class_evasion` 扩展（移动 frame 直接子层 inline `position:sticky;top:0` 自由发挥 → WARN，提示用 `.fb-navbar data-variant=`）|

**Supervisor 审核项（§4.4）**：WARN 阶段不阻断——precheck WARN 清单须同步入 state.md 非阻塞清单（同 S4-28/S4-32/S4-33/S4-34）；下游迁移到 v2 + dry-run + FP<30% 后升 FAIL。Supervisor 抽样审：PM 是否漏标 data-variant（默认 detail 是否符合实际场景）/ 是否用 inline div 自由发挥（应被 evasion 检查拦截）/ slot 填充是否按 7 variant 约定。

---

### S4-36 `[MUST · WARN 阶段]` data-tp ↔ tp-marker 配对完整性（A 方案 A.1，SSOT #55）

> **状态**：v1 落地，WARN 阶段（下游迁移缓冲期）。下游迁移完 + dry-run（≥ 2 仓 + FP < 30%）后升 FAIL。retro 优化方案 A.1（issue #56 235 处 data-tp 缺 marker 实证）。

**规则文本**：

`[MUST]` 每个 `data-tp="M[XX]-P[YY]-T[ZZ]"` 元素必有同级或父级 `<span class="tp-marker">NN</span>`，且 NN = data-tp 的 T/D 编号（NN 取 ZZ）。

**豁免白名单**（class 含任一即跳过）:
- `showcase-only`: showcase 区元素（仅展示）
- `is-unchecked`: 未选中 fb-radio（待选触点）
- `nav-inactive`: 未选中 nav（待选状态）

**Why（治"data-tp 缺 marker 235 处"根因）**：
- v1 仅 check_touchpoint_canonical 校 spec ↔ prd ID 一致性，不校"每个 data-tp 是否有 marker 配对"
- issue #56 实证：quotation-tool 235 处 data-tp 缺 marker → 用户实际操作时找不到触点视觉锚
- 治本：精确配对校验（编号匹配 + 父链路 ±500 字符搜索）+ 显式豁免白名单

**强制对应关系（SSOT #55 派生链）**：

| 角色 | 位置 |
|------|------|
| 真源 | `rule_hard_constraints.md §S4-36 v1`（4 sub-rule 协同 A 方案）|
| 派生：HTML 模板 | `fb-fallback-manifest.md §6 tp-marker`（触点徽章规范）|
| 派生：规范 | `proto_contract.md §四 触点编号规则` |
| 引用校验兜底 | `precheck_stage4.check_tp_marker_pairing`（扫 data-tp → ±500 字符内 tp-marker 编号匹配 + 豁免白名单，否则 WARN）|

**Supervisor 审核项（§4.4）**：WARN 阶段不阻断；下游迁移完 + dry-run + FP<30% 后升 FAIL。

---

### S4-37 `[MUST · WARN 阶段]` tp-marker tp-wrap 包裹结构（A 方案 A.2，SSOT #55）

> **状态**：v1 落地，WARN 阶段。下游迁移完 + dry-run（≥ 2 仓 + FP < 30%）后升 FAIL。retro 优化方案 A.2（issue #53 103 处 marker 飞到 phone-frame 角实证）。

**规则文本**：

`[MUST]` 所有 `<span class="tp-marker">` 必有父级或祖先（≤ 2 层）含 `.tp-wrap` class，确保 `position:relative` 定位基准；否则 marker 飞到 frame 角。

**豁免**：tp-marker 自身或父祖先（≤ 2 层）显式标 `data-tp-no-wrap` 属性（PM 已确认在已 position:relative 容器内）。

**Why（治"marker 飞到 frame 角 103 处"根因）**：
- v1 无父链路 wrap 校验；PM 直接放 `.tp-marker` 而无 `.tp-wrap` 父 → 缺 position:relative → marker absolute 相对最近 positioned 祖先（往往 frame）→ 飞到角
- issue #53 实证：quotation-tool 103 处 marker 视觉飞位
- 治本：父链路 ±300 字符内 tp-wrap class 或 data-tp-no-wrap 属性 双白名单

**强制对应关系（SSOT #55 派生链）**：

| 角色 | 位置 |
|------|------|
| 真源 | `rule_hard_constraints.md §S4-37 v1` |
| 派生：HTML 模板 | `fb-fallback-manifest.md §6 tp-marker`（含 tp-wrap 包裹示例）|
| 引用校验兜底 | `precheck_stage4.check_tp_marker_wrap`（扫 .tp-marker → ±300 字符内 tp-wrap class 或 data-tp-no-wrap 属性，否则 WARN）|

**Supervisor 审核项（§4.4）**：同 S4-36。

---

### S4-38 `[Should · WARN]` PRD section 最小内容粒度（A 方案 A.3，SSOT #55）

> **状态**：v1 落地，[Should] WARN 永远不阻断 EXIT=0（不像 A.1/A.2 升 FAIL）。retro 优化方案 A.3（issue #57 spec-background / spec-data 仅壳实证）。

**规则文本**：每个 `<section id="...">` inner 字节数 ≥ 500B（非空壳）。

**豁免**：section 内含 `<!-- section-shell-by-design: <reason> -->` 注释。

**强制对应关系**：
- 真源：`rule_hard_constraints.md §S4-38 v1`
- 引用校验兜底：`precheck_stage4.check_section_min_content`（正则 section 配对 + UTF-8 字节数 + 豁免标）

---

### S4-39 `[Should · WARN]` Mermaid label 字符安全（A 方案 A.4，SSOT #55）

> **状态**：v1 落地（v2 算法 FP 收敛），[Should] WARN 永远不阻断 EXIT=0。retro 优化方案 A.4（issue #57 EmptyState `"..."` parse 错实证）。

**规则文本**：扫所有 mermaid block 节点 label 内 3 类硬违规 → WARN：
- 奇数个 `"`（必未闭合）
- ≥ 4 个 `"`（必嵌套未转义）
- 中文标点 / 中文引号（， 。 ； ： “ ” ‘ ’）混入

**Why（治"`"..."` parse 错"根因 + FP 收敛）**：
- v1 严格检测"label 中间含未转义 `"`"，但 mermaid 合法 string literal `A["text"]` + subroutine shape `A[["text"]]` 误判
- quotation-tool 实测 v1 误报 214 处 → v2 算法收敛为 2 处真实（中文逗号），FP 大幅降低
- 简化原则：mermaid mmdc parse（S4-33）兜底语法错；本规则仅捕"明显违规"避免重复

**强制对应关系**：
- 真源：`rule_hard_constraints.md §S4-39 v1`
- 引用校验兜底：`precheck_stage4.check_mermaid_label_chars`（复用 `_extract_mermaid_blocks` + 3 类硬违规检测）
- 关联：`S4-33 check_mermaid_syntax`（mmdc parse 兜底剩余语法错）

---

### S4-40 `[Must · WARN]` .interaction-card 内禁 inline 字号覆盖（SSOT #62 E.3 第 1 条）

> **状态**：v1 落地，[Must · WARN] 阶段（dry-run ≥ 2 仓 + FP < 30% 后升 FAIL）。治产品总监跨项目反馈「字体有大有小」根因——PM 在 drafts 中 inline 覆盖模板硬编码字号体系。

**规则文本**：扫 prd.html 中所有 `.interaction-card` 块内任何元素（含 `.card-title` / `.state-diff-note` / `.data-sub-title` / `<table>` / `<th>` / `<td>` 等）的 `style` 属性，若含 `font-size:...` 字面 → WARN。

**Why（治"跨项目字号散乱"根因）**：
- 模板 `prd_template.html` `.interaction-card` 段已硬编码字号体系（card-title 13px / state-diff-note 12px / data-sub-title 11px / table 12px + padding + line-height）
- 但 PM 在 drafts 中可写 `<table style="font-size:14px">` inline 覆盖，跨项目字号体系散乱
- 本规则通过 `HTMLParser` 追踪 `.interaction-card` 嵌套深度，flag 打开期间扫所有元素 style；嵌套安全

**强制对应关系**：
- 真源：`prd_expression_standard.md` 区块 C E.3 第 1 条 + `rule_hard_constraints.md §S4-40 v1`
- 引用校验兜底：`precheck_stage4.check_interaction_card_no_inline_font`（`_InteractionCardInlineFontChecker` HTMLParser 追踪嵌套深度 + 扫 style font-size 字面，零启发式 FP≈0）
- 关联：E.3 第 2 条由 S4-41 兜底（NB-WE-04 已闭环）

---

### S4-41 `[Must · WARN]` 典型交互说明字面必须在 .interaction-card 内（SSOT #62 E.3 第 2 条）

> **状态**：v1 落地（2026-06-02 NB-WE-04 闭环实装），[Must · WARN] 阶段（dry-run ≥ 2 仓 + FP < 30% 后升 FAIL）。治 E.3 第 2 条「禁自造 div 替代 .interaction-card 结构」原"启发式空间复杂"判定 — 反向扫策略颠覆该判定（典型字面在 PRD 中仅出现在 .interaction-card 内，零启发式 FP≈0）。

**规则文本**：扫 prd.html 中含 5 类信号字面（「交互说明 —」/「状态差异说明」/「列表回显说明」/「数据展示说明」/「触点交互说明」）的文本，若元素父链路**不含** `.interaction-card` 容器（且不在 `<pre>` / `<code>` 块豁免范围）→ WARN。

**Why（治"PM 自造结构"根因）**：
- PM 可能用 `<div class="my-custom">` / `<section>` / `<h3>` 等自造结构替代标准 `.interaction-card > (.card-title + .state-diff-note + .data-sub-title + <table>)` 容器
- 5 类信号字面来自 `prd_expression_standard.md` 区块 C 模板的固定字面（card-title + 四 sub-title），PRD 中这些字面应**仅**出现在 `.interaction-card` 内
- 反向扫策略：字面出现在 `.interaction-card` 外 = 自造结构嫌疑（零启发式 FP≈0）
- 豁免：`<pre>` / `<code>` 块内（spec/示例代码引用）；changelog 表「修改交互说明」（无 em-dash 字面不命中）

**强制对应关系**：
- 真源：`prd_expression_standard.md` 区块 C E.3 第 2 条 + `rule_hard_constraints.md §S4-41 v1`
- 引用校验兜底：`precheck_stage4.check_interaction_card_class_compliance`（`_InteractionCardClassComplianceChecker` HTMLParser 追踪 div+pre+code 嵌套 + handle_data 扫 5 类信号字面 vs `.interaction-card` 父链路验证）
- 关联：S4-40 同 SSOT #62 E.3 双闸点防御（第 1 条 inline 字号 / 第 2 条自造结构）

---

### S4-64 `[Should · WARN]` interaction-card sub-title 顺序 + 完整性校验（议题 16 / NB-R3-02，SSOT #69 延伸）

> **状态**：v1 落地，[Should · WARN] dry-run 阶段（按 S4-49~63 同型纪律待 ≥ 2 仓真实 PM 反馈 + FP 持续 < 30% 后升 [Must] FAIL）。议题 16 / NB-R3-02 治理"PM 在 interaction-card 内省略 sub-title 头（C-1 列表回显 / C-2 数据展示 / C-3 触点交互 / C-4 业务契约）"反 pattern。

**规则描述**：

| 规则 | 检测维度 | precheck 函数 | SSOT |
|------|---------|--------------|------|
| **S4-64** | interaction-card 内 4 个标准 sub-title 头（C-1/C-2/C-3/C-4）容器锁定存在 + 顺序合规（C-1 < C-2 < C-3 < C-4）→ 任一缺失或乱序 WARN | `check_interaction_card_subtitle_order` | #69 延伸 |

**Why（治本路径）**：assemble 派生层（议题 15 / NB-R3-01）三函数 `_inject_c1/c2/c3_placeholder_when_missing` 在 PM 写源缺 sub-title 时注入豁免占位（idempotent）；S4-64 校验"派生兜底是否生效 + sub-title 顺序是否合规"。配套 prd_expression_standard.md §四 区块 C 顶部"真无内容豁免规范"教育层（豁免文案显式列出 + 反 pattern 警示）。三层协同：规范教育 + 派生兜底 + precheck 校验。

**强制对应关系**：

- 真源（机械兜底）：`precheck_stage4.py check_interaction_card_subtitle_order` + 测试 `tests/test_precheck_stage4.py TestS464`
- 真源（规范）：`prd_expression_standard.md §四 区块 C 真无内容豁免规范`（4 子区块豁免文案 + 反 pattern）
- 真源（派生）：`assemble.py _inject_c1_placeholder_when_missing` / `_inject_c2_placeholder_when_missing` / `_inject_c3_placeholder_when_missing` 三函数
- 关联：S4-64 与 S4-58/59/60（议题 17 二级判定升级）同 sub-title 容器锁定 regex 同源

**rollout 纪律**：

- WARN 阶段（dry-run 缓冲），≥ 2 仓真实 PM 反馈 + FP 持续 < 30% 后升 [Must] FAIL（同 S4-28 v3 / S4-44~48 / S4-49~63 同型纪律）

---

### S4-61 / S4-62 / S4-63 `[Should · WARN]` 3 议题综合 hot fix（议题 2A + 议题 2B + 议题 3，SSOT #65/#69 延伸，2026-06-04 落地）

> **状态**：v1 落地（2026-06-04），3 函数均 [Should · WARN] dry-run 阶段（按 S4-49~60 同型纪律待 ≥ 2 仓真实 PM 反馈 + FP 持续 < 30% 后升 [Must] FAIL）。议题 2A（C-4 表达规范化 + 字号统一 → S4-63）+ 议题 2B（私域主页 95/143 双业务规则段实证 → S4-61）+ 议题 3（bujue-quotation-tool 14 处悬空 marker 实证 → S4-62）三个 retro 议题综合 hot fix。

**3 条规则统一描述**：

| 规则 | 检测维度 | precheck 函数 | SSOT |
|------|---------|--------------|------|
| **S4-61** | interaction-card 内 3 子标题（业务规则/数据回显/验收标准）任一字面 ≥ 2 次 → WARN | `check_interaction_card_double_subsection` | #69 延伸 |
| **S4-62** | tp-marker 数字 NN 在 ±500 字符内无配对 data-tp 末段 = NN → WARN（与 S4-36 对偶）| `check_tp_marker_reverse_pairing` | #65 延伸 |
| **S4-63** | interaction-card 含 [C4-START: 注入标记的卡 C-4.A 必为 `<table class="c4-business-rules">` / C-4.B 必为 `<table class="c4-data-scale">` / C-4.C 必为 `<pre class="gherkin">` → WARN | `check_interaction_card_c4_format` | #69 延伸 |

**Why（治本路径）**：

- **议题 2A / S4-63**：assemble.py `_build_c4_content_html` 历史用 `<ul class="c4-business-rules">` + `<p class="c4-data-scale">单段` 派生 C-4.A/.B，C-4.A 列表条目与 C-1/C-2/C-3 表格视觉割裂 + C-4.B 单段难以解析三维度。议题 2A 改 C-4.A 为 2 列表格（# + 业务规则）+ C-4.B 为 2 列表格（维度 + 值，按 "/" 拆解），C-4.C 保留 `<pre class="gherkin">`（Gherkin 三段语义代码）。配套 prd_template.html `.interaction-card` 内 td/th/p/li 字号统一 13px line-height 1.6 治"interaction-card 内 inline font-size 611 处 + PM 手写 `<p>` 661 处字号散乱"。S4-63 反向校验派生与规范一致性。
- **议题 2B / S4-61**：PM 在 interaction-card 内既写了「`<p><strong>业务规则</strong>...</p>`」段（C-3/C-4 之前的手写形态），assemble 又派生注入了「`<div class="c4-sub-title">业务规则</div>`...」段（SSOT #68 C-4 派生），二段并存 → 视觉重复 + 内容不一致风险。治本：让 C-4 派生层（SSOT #68）作业务规则唯一来源，PM 删手写形态。S4-61 兜底 95 处历史漂移。
- **议题 3 / S4-62**：S4-36 正向校验（每个 data-tp 必有 tp-marker）能抓"缺 marker"漏洞，但不抓"悬空 marker"漏洞（PM 删 data-tp 后忘删 marker / 重复粘贴未清理）。S4-62 反向校验补全 marker→data-tp 闭环防御。bujue-quotation-tool 14 处实证。

**强制对应关系**：

- 真源（机械兜底）：`precheck_stage4.py` `check_interaction_card_double_subsection` + `check_tp_marker_reverse_pairing` + `check_interaction_card_c4_format` + `tests/test_precheck_stage4.py TestS461 / TestS462 / TestS463` 用例
- 真源（规范）：`prd_expression_standard.md §四 区块 C C-4 schema`（含 C-4.A/.B 表格列结构）+ `proto_contract.md §六 tp-marker 配对纪律` + SSOT #65 / #69
- 真源（派生）：`assemble.py _build_c4_content_html` C-4.A 2 列表格 + C-4.B 2 列表格（按 "维度：值" 拆解）派生
- 关联：S4-61 / S4-63 与 S4-49~60 同 WARN 阶段纪律；S4-62 与 S4-36（正向）形成 marker 配对完整闭环

**rollout 纪律**：
- WARN 阶段（dry-run 缓冲），≥ 2 仓真实 PM 反馈 + FP 持续 < 30% 后升 [Must] FAIL（同 S4-28 v3 / S4-44~48 / S4-49~60 同型纪律）
- 初版实证：S4-61 私域主页 95/143（FP 评估：0/95 = 0%）；S4-62 bujue-quotation-tool 14 处（FP 评估：0/14 = 0%，含 L5712/L6908/L8426 等真悬空）；S4-63 重 assemble 后规范派生 → 历史 PRD（未重 assemble）C-4.A `<ul>` / C-4.B `<p>` 命中（FP 评估：0%，由 assemble.py 重生治本）

---

### S4-49 / S4-50 / S4-51 / S4-52 / S4-53 / S4-54 / S4-55 / S4-56 / S4-57 / S4-58 / S4-59 / S4-60 `[Should · WARN]` SSOT #67/#68/#69 prd/spec 派生层 + interaction-card schema 机械化（2026-06-04 落地）

> **状态**：v1 落地（2026-06-04），12 函数均 [Should · WARN] dry-run 阶段（按 S4-28 v3 / S4-44~48 同型纪律待 ≥ 2 仓真实 PM 反馈 + FP 持续 < 30% 后升 [Must] FAIL）。落地 SSOT #67 A-05 信息架构重组 + SSOT #68 C-4 业务契约派生 + SSOT #69 interaction-card C-0~C-3 schema 校验三锚配套强约束。

**12 条规则统一描述**（按 SSOT 锚分组）：

| 规则 | 检测维度 | precheck 函数 | SSOT |
|------|---------|--------------|------|
| **S4-49** | spec §S2.MXX.4B 业务规则段头存在 + 非空 | `check_spec_section_4B_business_rules` | #68 |
| **S4-50** | spec §S2.MXX.5B 数据规模段头存在 + 非空 | `check_spec_section_5B_data_scale` | #68 |
| **S4-51** | spec F-xxx 主页面字段存在 + ∈ 涉及页面集合 | `check_spec_function_main_page_field` | #68 |
| **S4-52** | spec F-xxx 4 必填字段（优先级 / 所属旅程 / 涉及页面 / 主页面）齐全 | `check_spec_function_xxx_required` | #68 |
| **S4-53** | prd interaction-card C-4 派生闭环（[C4-START/END] ∪ c4-cross-page-note 覆盖率 ≥ 50%）| `check_prd_c4_derivation_closure` | #68 |
| **S4-54** | prd A-05 章节已重组为「功能索引」（spec-feature section 内无 feature-block 旧 article）| `check_prd_a05_removed` | #67 |
| **S4-55** | prd A-索引 4 列齐全（编号 / 功能名 / 优先级 / 主页面）+ 行数 == spec.md F-xxx 节数 | `check_prd_a_index_complete` | #67 |
| **S4-56** | interaction-card C-0 `<div class="state-diff-note">` 子区块存在 | `check_interaction_c0_state_diff_note` | #69 |
| **S4-57** | interaction-card C-1 列表回显 4 行固定行目（排序规则 / 加载方式 / 总数回显 / 空列表判断）| `check_interaction_c1_list_table` | #69 |
| **S4-58** | interaction-card C-2.A 索引层 6 列（C 触点 ID / 单元名称 / 是否封装为组件 / 渲染时机 / 跨平台差异 / 关联 T 触点）| `check_interaction_c2a_unit_index` | #69 |
| **S4-59** | interaction-card C-2.B 字段子表 5 列含 D 触点 ID（D 触点 ID / 字段名 / 接口字段 / 显示格式 / 空值处理）| `check_interaction_c2b_field_table` | #69 |
| **S4-60** | interaction-card C-3 触点表 6 列含跳转/边缘（序号 / 触点说明 / 触发 / 行为 / 跳转 / 边缘）| `check_interaction_c3_touchpoint_table` | #69 |

**Why（治本路径）**：SSOT #67/#68/#69 三锚配套同批落地后形成 PRD interaction-card 5 子区块完整 schema 防御 + A-05 信息架构重组的派生闭环；本批 12 个 check_* 函数在规范层（Commit 1）+ assemble 派生层（Commit 2）基础上补 precheck 机械强约束（Commit 3）—— 治"PM 写 PRD interaction-card 实际 DOM 与规范 schema 严重脱节"+ "F-xxx 缺主页面字段导致 A-05 跳转目标空 + C-4 派生失败连锁"两类根因。

**强制对应关系**：
- 真源 1（机械兜底）：`precheck_stage4.py` 12 个新 check_* 函数（S4-49 ~ S4-60）+ `tests/test_precheck_stage4.py TestS449 ~ TestS460` 44 用例
- 真源 2（规范）：`prd_expression_standard.md §三 A-05` + `§四 区块 C C-0~C-4` + `proto_spec_md.md §三.5 .4B/.5B + F-xxx 4 必填字段`
- 引用校验兜底：`precheck_stage4.py` main() 7 函数（S4-49~52 spec_path.exists() 块 + S4-53/55 spec+prd 共用块 + S4-54/56~60 prd_path.exists() 块）
- 关联：与 SSOT #66 协同（#66 spec.md 输入 schema / #67/#68/#69 prd 输出 schema + 派生闭环）；与 S4-40/41/42/43/44~48 同 WARN 阶段纪律；assemble.py 派生 7 函数 (`extract_business_rules` / `extract_data_scale` / `extract_gherkin` / `extract_main_page` / `inject_c4_into_interaction_card` / `build_function_overview_index` / `build_function_overview_index_with_jump`) 作为 spec→prd 单向派生链路

---

### S4-44 / S4-45 / S4-46 / S4-47 / S4-48 `[Must · WARN]` spec.md SSOT 输入 schema 严格化（SSOT #66，2026-06-04 落地）

> **状态**：v1 落地（2026-06-04），5 函数均 [Must · WARN] dry-run 阶段（按 S4-28 v3 纪律待 ≥ 2 仓真实 PM 反馈 + FP 持续 < 30% 后升 FAIL）。兑现 SSOT #61 "后续 ROI 评估补 precheck_stage4 章节完整度校验" B 组待补承诺；治 SSOT #61 文档级三层后 PM 写 spec 仍存在的 5 类规范↔实施漂移。dry-run 3 仓（报价工具 / 私域主页 / 商业圈子）FP = 0% 验收。

**5 条规则统一描述**（同族协同，5 函数共享启发式豁免：spec 顶层无 `^## S2\.M\d+` 段头 → 旧版 spec 跳过）：

| 规则 | 检测维度 | precheck 函数 |
|------|---------|--------------|
| **S4-44** | 模块子块完整度（每模块 7 必填 .1/.2/.2A/.3/.3A/.4/.5/.7）| `check_spec_module_subsections_completeness` |
| **S4-45** | Gherkin 完整度（S2.MXX.7 每状态含 4 子项「互斥说明/触发条件/页面表现/验收标准」+ ```gherkin 围栏 Given/When/Then 三段；适配两种状态锚格式 `**P\d+-`（旧）/ `**S\d+：`（SSOT #61 升级后））| `check_spec_gherkin_completeness` |
| **S4-46** | API ID 引用闭环（spec.md 所有 `API-XXX` ⊆ 产品定义 §10 API-XXX 定义集合；产品定义文件不存在 → 启发式豁免）| `check_spec_api_id_closure` |
| **S4-47** | NB ID 引用闭环（spec.md 所有业务 `NB-XXX` ⊆ decisions_ledger.md ∪ scaffold.notes ∪ §S0.5 ∪ 产品定义；L2 工作流 NB 前缀 `NB-WE-` / `NB-LIT-` / `NB-SSOT` / `NB-SNB` 启发式豁免）| `check_spec_nb_id_closure` |
| **S4-48** | 模块编号连续性（S2.MXX M01~MNN 无跳号）+ 子段层级父子约束（.2A 必有父 .2 / .3A 必有父 .3）| `check_spec_section_numbering_consistency` |

**Why（治本路径）**：SSOT #61 文档级三层（规范 + PM 自审 + Foundation 落地）覆盖 ~50%，本批 5 函数补全 50% — 二者合起来形成 spec.md schema 完整防御体系。dry-run 实证暴露真违规：私域主页 60/114 状态缺 Gherkin 完整度（PM 真违规暴露）+ 报价工具 9/60 API 引用占位字面（API-M10-XX 等）+ 报价工具 .6 全缺（治 §三.5 `.6` 撞号 PM "两个都不写"根因，已 2026-06-04 WE-1 修复 .6 = API 摘要统一）。

**强制对应关系**：
- 真源 1（机械兜底）：`precheck_stage4.py` 5 个新 check_* 函数（S4-44 ~ S4-48）+ `tests/test_precheck_stage4.py TestS444 ~ TestS448` 20 用例
- 真源 2（规范）：`proto_spec_md.md §三.5 子章节内部细则`（SSOT #61 升级后 7 必填 + 3 可选）+ §三.5 末尾「反 pattern」段（SSOT #66）
- 引用校验兜底：`precheck_stage4.py` main() spec_path.exists() 分支 5 函数顺序调用
- 关联：与 SSOT #61 协同（#61 文档级三层 + #66 精确机械化兜底）；与 S4-40/S4-41/S4-42/S4-43 同模式（dry-run WARN 阶段 + 启发式豁免 + 待升 FAIL）；同步 `gen_scaffold.py L1168` 模块骨架预生成 `.6 = API 摘要`（治 v2.0 顶层 vs SSOT #61 升级三方不同步）

---

### S4-43 `[Must · WARN]` data-tp 容器级唯一性纪律（SSOT #64，下游 D2 治本）

> **状态**：v1 落地（2026-06-02），[Must · WARN] dry-run 阶段；list/table 多实例豁免启发式待样本充分后设计 + 升 FAIL。治产品总监跨项目反馈「触点 ID 重复 / chip group 自由发挥」根因——PM 在 chip group/radio/tab 每子选项重复标 data-tp，违反容器级唯一性。

**规则文本**：扫 prd.html 中每个 `*-frame`（phone-frame/desktop-frame/h5-frame/tablet-frame/miniprogram-frame）内同 `data-tp` ID 出现次数；> 1 次 → WARN。豁免判定（dry-run 阶段不机械化）：list/table 同模板多实例由 PM/Sup 看上下文人审。

**Why（治"PM 自由发挥每选项标 data-tp"根因）**：
- S4-24 强制"每交互元素标 data-tp" — 没说清"什么算交互元素"
- PM 在 chip group 每选项标 data-tp（错把 DOM 元素当交互单元）
- 本规则反向扫每 frame 内 data-tp 重复，让 PM 看具体行号 + 上下文判定是 chip 反 pattern 还是 list 合规多实例

**强制对应关系**：
- 真源：`proto_contract.md §四 触点容器级唯一性纪律` + `rule_hard_constraints.md §S4-43 v1` + `§S4-24` 概念升级注记
- 引用校验兜底：`precheck_stage4.check_prd_data_tp_container_uniqueness`（`_DataTpContainerUniquenessChecker` HTMLParser 追踪 div 嵌套 + 标识 *-frame + 按 frame 收集 data-tp 出现统计）
- 关联：与 S4-24（强制标）协同（S4-24 = 强制存在性 / S4-43 = 容器级粒度）+ S4-36（data-tp ↔ tp-marker 配对）

---

### S4-42 `[Must · WARN]` .fb-state-loading 内禁 inline padding 覆盖（SSOT #63 Skeleton tokens）

> **状态**：v1 落地（2026-06-02），[Must · WARN] 阶段（dry-run ≥ 2 仓 + FP < 30% 后升 FAIL）。治产品总监跨项目反馈「同平台骨架屏尺寸不一致」根因——PM 在 drafts 中 inline 覆盖模板默认 padding，跨产品 padding 散乱。

**规则文本**：扫 prd.html 中 `.fb-state-loading` 元素 `style` 属性是否含 `padding:...` 字面 → WARN。

**Why（治"跨产品骨架屏散乱"根因）**：
- 模板 `prd_template.html` `:root` 已声明 `--skel-*-padding` tokens（phone 32px / desktop 48px 32px / h5 40px 24px / modal 24px 16px）+ 平台 selector 自动应用
- 真源在 `bujue-design-system/tokens.md` skeleton 段
- PM 在 drafts 中 inline 覆盖 → 跨产品 padding 散乱（如 quotation-tool 实证 8 实例同平台差异率 ≥ 50%）
- 本规则反向扫 inline padding，零启发式 FP≈0

**强制对应关系**：
- 真源：`bujue-design-system/tokens.md` skeleton tokens 段 + `rule_hard_constraints.md §S4-42 v1`
- 引用校验兜底：`precheck_stage4.check_skeleton_inline_padding`（`_SkeletonInlinePaddingChecker` HTMLParser 扫 .fb-state-loading 元素 style padding 字面）
- 关联：与 S4-40/S4-41 同模式（模板硬编码字号 + token 化集中管理 vs PM 在 drafts inline 散乱）

---

### S1-08 `[Recommended · WARN]` 阶段 1 UI 字面来源标注校验（G 方案 G.5，SSOT #54）

> **状态**：v1 落地（G/C3），WARN [Recommended] 不阻断 EXIT=0（产品总监已决策兼容现有产物）。

**规则文本**：扫阶段 1 产物中疑似 UI 实现细节字面（9 类关键词），上下文 ±2 行无 `【来源：...】` 标注 → WARN。

**强制对应关系**：
- 真源：`CLAUDE.md §调整意见自动记录规则第二步 G.1` + `tmpl_需求分析.md` 顶部阶段分层粒度纪律
- 引用校验兜底：`precheck_common.check_ui_source_annotation`（共享 + rule_id_map: 1 → S1-08）+ `precheck_stage1.py main()` 调用

---

### S2-07 `[Recommended · WARN]` 阶段 2 UI 字面来源标注校验（G 方案 G.5，SSOT #54）

> 同 S1-08（共享 check_ui_source_annotation 函数，rule_id_map: 2 → S2-07）。

**真源**：`tmpl_功能规划.md` 顶部阶段分层粒度纪律（含 mermaid label UI 排版禁令）。

---

### S3-07 `[Recommended · WARN]` 阶段 3 UI 字面来源标注校验（G 方案 G.5，SSOT #54）

> 同 S1-08（共享 check_ui_source_annotation 函数，rule_id_map: 3 → S3-07）。
>
> **编号说明**：原标号 S3-06 与「现网已有模块承继约束系列」（S1-07 / S2-06 / **S3-06**）撞号，于 2026-05-31 L2 矛盾审计后改为 S3-07（与 S1-08 / S2-07 同档 G.5 系列递增）。

**真源**：`tmpl_产品定义.md` 顶部阶段分层粒度纪律（含视觉细节 / 文案最终字面 / 元素排布 schema 禁令）。

---

## 六.X S4 规则与检查点对照表

> 本表追溯每条 S4-XX 硬规则在 PM 自审 / Supervisor 审核 / precheck 三处的检查点位置——便于规则修改时同步更新所有检查清单，也便于违规时快速定位"由谁负责检查"。
>
> 每次新增 / 修改 S4 规则，必须同步更新本表 + 对应的检查点位置；不允许只动规则不动检查点（否则视为"规则空转"）。

| 规则 | 检查维度 | PM 自审 §5.4 | Supervisor §4.4 | precheck 函数 |
|------|---------|------------|---------------|--------------|
| S4-01 生成顺序 | 执行流程 | 「生成顺序自查」 | 「执行流程合规」 | — |
| S4-02 双文件对称性 | spec ↔ prd | 「页面对称性」 | 「双文件对称」 | `check_prd` + `check_touchpoint_consistency` |
| S4-03 section id 全局唯一 | HTML 结构 | 「section id 唯一」 | 已机械化（精读） | `check_prd`（占位 + section 集合） |
| S4-04 平台覆盖 | 业务语义 | 「平台覆盖」 | 已机械化 | `check_platform_coverage`（scaffold.platforms ↔ prd frame 类型双向对照） |
| S4-05 状态清单覆盖 | 业务语义 | 「状态清单」 | 已机械化（基线三类）+ 人工补条件态 | `check_state_coverage`（每页须覆盖 default + loading/empty + error/disabled 三类语义；条件附加状态——越权提示 / 确认弹窗 / 角色差异——仍由 Agent 人工兜底）|
| S4-06 叠加态覆盖 | 业务语义 | 「叠加态」 | 「叠加态链路」 | — |
| S4-07 外部依赖组件处理 | 业务语义 | 「外部依赖处理」 | 「外部依赖」 | — |
| S4-08 cursor:pointer 全覆盖 | 视觉规范 | 「cursor 覆盖」 | 已机械化 | `check_cursor_pointer_coverage`（所有 onclick 元素 inline 或 class 含 cursor:pointer）|
| S4-09 触点编号规范 | 编号一致性 | 「触点编号」 | 已机械化 | `check_touchpoint_consistency` + `check_spec`（触点格式） |
| S4-10 分步自审 | 流程纪律 | 「分步自审」 | — | — |
| S4-11 API 编号唯一来源 | 编号一致性 | 「API 编号」 | 「API 编号」 | — |
| S4-12 界面文案唯一来源 | 内容一致性 | 「文案一致」 | 「文案一致」 | — |
| S4-13 导航闭环 | 跳转完整性 | 「导航闭环」 | 已机械化 | `check_prd`（showSection 目标可解析；WE-F 2026-05-19：解析集 = `<section id>` ∪ `<div id="sk-*">` WE-B sitemap 锚——showSection 用 getElementById 对任意元素生效，下游 R1 修） |
| S4-14 数据回显行 | 业务语义 | 「数据回显」 | 「数据回显」 | — |
| S4-15 现网已有模块承继 | 业务语义 | 「现网模块承继」 | 「现网承继」 | — |
| S4-16 产品规格区与产品背景完整性 | 结构完整性 | 「产品规格区」 | 已机械化 | `check_prd`（产品规格区 9 节齐全,含 A-04.2 业务流程图） + `check_spec`（模块覆盖 + 尾部章节） |
| S4-17 proj 状态枚举完整性 | 组件协议 | 「proj 8 状态」 | 已机械化 | `check_proj_components`（状态枚举完整性） |
| S4-18 proj 可视化完整性 | 组件协议 | 「proj 状态展示区」 | 已机械化 | `check_proj_components`（状态展示区 + 行数） |
| S4-19 proj CSS 抽象纪律 | 组件协议 | 「proj CSS 抽象」 | 已机械化 | `check_proj_components`（CSS 定义 + modifier + inline 禁用） + `check_proj_owner`（owner 归属） + `check_proj_css_selector_unique`（PROJ-CSS selector 唯一） |
| S4-20 fb-* 业务-语义匹配 | 组件选择 | 「fb-* 业务语义」 | 「fb-* 语义匹配」 | 部分（`check_prd_fb_registration` 仅查登记，不查语义） |
| S4-21 spec ↔ prd 字段绑定 | 字段一致性 | 「字段绑定」 | 已机械化 | `check_field_binding_consistency`（spec §9 字段名 ↔ prd 表单 name/data-field 集合一致 + 必填字段绑定）|
| S4-22 组件变更清单完整性 | 变更追溯 | 「组件变更清单」 | 已机械化 | `check_component_changelog_consistency`（spec §八 ↔ prd #component-changelog 三类 sub-section 集合 + 占位状态对称）|
| S4-23 PRD fb-* 已登记 | class 合法性 | 「fb-* 登记」 | 已机械化 | `check_prd_fb_registration` |
| S4-24 交互元素 data-tp 绑定 | 实例可指代性 | 「data-tp 绑定」 | 已机械化 | `check_interactive_data_tp`（豁免：`NON_BUSINESS_NAV_CLASSES` + `NON_BUSINESS_ONCLICK_PATTERNS`；WE-F 2026-05-19 加 mmd-fs 全屏预览 doc-chrome 豁免 `openMermaidFs/closeMermaidFs/resetMermaidFsView` + `mmd-fs-btn`，同 switchJourneyView 类，下游 R2 修） |
| S4-25 移动端 sheet 标准结构 | 组件协议 | 「sheet 规避检查」 | 已机械化（WARN）| `check_panel_class_evasion`（phone-frame/miniprogram-frame 内 SHEET_EVASION_KEYWORDS 非 fb-* class 扫描；v1 WARN 下迭代升 FAIL）|
| S4-26 changelog thead 字面规范化 | 组件协议 | 「changelog thead」 | 已机械化（FAIL）| `check_changelog_thead`（4 个 changelog-group thead 字面严格 == 期望 + 禁用旧字面命中即 FAIL）|
| S4-27 派生模块 slot class 完整性 | 组件协议 | 「派生 slot 完整性」 | 已机械化（WARN，v2 双分支）| `check_proj_slot_class_completeness`（scaffold.owner_assignments 推算 owner + PROJ-CSS slot 集合提取 + 派生 draft 30 行窗口扫描；v1 fb-tag 平铺 + v2 单行字面退化 双分支判定；SSOT #37 兜底）|
| S4-28 统一底栏操作组（`.fb-action-bar` v3 CSS 变量继承）| 组件协议 / 布局 | 「底栏 .fb-action-bar 单类覆盖 frame/modal/drawer」| 已机械化（WARN，v3 三层）| **结构层** `check_desktop_sticky_completeness`（升级：扫 .fb-action-bar + 3 deprecated 别名 + 移动端 frame 直接子层 WARN）+ **inline 层** `check_inline_position_compliance`（保留，错误信息指向 .fb-action-bar）+ **deprecation 层** `check_deprecated_class_usage`（旧 3 class → WARN 迁移提示，SSOT #51 v3）；均 WARN 阶段，下游迁移完升 FAIL |
| S4-29 页面层级架构 SSOT 同步 | 结构完整性 / 派生一致 | 「§3.0 marker 已写」| 已机械化（FAIL）| `check_page_hierarchy_sitemap`（spec §3.0 + PRD spec-sitemap 存在性 + mermaid 页面节点 `M\d+_P\d+` distinct 数 == scaffold pages 数；SSOT #38 兜底）|
| S4-30 页面结构范式契约 | 结构完整性 / 跨模块结构统一 | 「容纳性二值校验已做+记录」| 结构+过程已机械化（FAIL）；判断层人工（D-08）| `check_page_archetype_contract`（page_archetypes 必备键 + 每页 archetype 引用合法 + 契约表注入存在性）+ `check_archetype_containment_record`（定长记录每页齐全+覆盖，C 拉回 A）+ `gen_scaffold.validate_v2_schema`（首次闸）；判断层"对不对"由 Step1.X D-08 + 终审 + subagent 二值闸（B 组，SSOT #39）|
| S4-31 模块架构说明 | 结构完整性 / 跨阶段一致 | 「§6.5 复述自阶段2 §三」| 全机械化（FAIL，干净 A 组）| `precheck_stage3.check_section_6_5`（阶段3 §6.5 模块数 == 阶段2 §一）+ `precheck_stage4.check_module_architecture`（spec §3.0+PRD spec-sitemap 模块表行数/依赖边数 == scaffold.modules/depends_on）+ `gen_scaffold.validate_v2_schema`（purpose 可选类型）；全数对称无判断层（SSOT #40 A 组 5/5）|
| S4-32 页面骨架屏 | 结构完整性 / 单源双渲染（per-archetype）| 「每 archetype 有良构范式骨架 + data-r⊆该范式 + override 良构」| 结构层机械化但 **WARN 阶段（档 C）不阻断**；WARN 入 state.md + 语义层人审（范式如实示意 / override 是否确属无法套范式 / 范式增殖纪律）+ 存量 per-archetype 迁移进度 | `gen_scaffold.build_foundation_skeleton_draft`（每范式锚行+占位+免责首行，首次闸）+ `build_spec_module_draft`（per-page override-only 纯注释 marker）+ `precheck_stage4.check_page_skeleton`（① 每 archetype ≥1 良构骨架+data-r⊆该范式 ② override 良构 ③ PRD sk-askel+每范式子锚齐全 + 首行免责字面/非div/inline style/class越白名单/per-platform token/嵌套>3 **全 WARN**，档 C，`_validate_skeleton_blocks` 共享；存量迁移完升 FAIL；**WE-G 条件 per-platform** archetype/override 级复用，1-vs-N/是否 override 判断层不机械化）；exact 判定 WARN 阶段，SSOT #41（WE-H per-archetype 2026-05-19：#41=#39 视觉化身，回正 per-page 错颗粒度 + dry-run NB-WE-01 + WARN-phase SNB-006 收口 + WE-G per-platform）|

| S4-33 mermaid 块语法校验 | 渲染正确性 | 「mermaid 块可 parse」| 已机械化（WARN）| `check_mermaid_syntax`（提取 PRD `<pre class="mermaid">`/spec ```mermaid → html.unescape → mmdc 单次渲染 parse；mmdc 缺失/超时 WARN 跳过；与 check_prd「游离 mermaid」位置校验正交——本规则校语法能否 parse）+ `_find_mmdc` + `_extract_mermaid_blocks`；WARN 阶段，3 仓 dry-run + FP<30% 后升 FAIL（SSOT #43）|
| S4-34 触点 canonical 引用完整性 | 编号一致性 / 手写偏差治本 | 「触点 ID 从 scaffold canonical 生成」| 已机械化（WARN）| `gen_scaffold.validate_v2_schema`（touchpoints 可选 schema 校验）+ `gen_scaffold.build_spec_module_draft`（据 touchpoints 预填 canonical 行）+ `precheck_stage4.check_touchpoint_canonical`（`_build_touchpoint_canonical` 构集 + spec/prd 引用 ⊆ canonical，outside/unreferenced WARN）；向后兼容 scaffold 无 touchpoints 跳过；WARN 阶段，3 仓 dry-run + FP<30% 后升 FAIL（SSOT #44）|
| S4-35 移动端次级页面返回入口完整性 | 结构完整性 / 导航闭环 | 「次级页面用 fb-navbar 含返回入口」| 已机械化（WARN，零启发式）| `precheck_stage4.check_back_entry`（扫 `.fb-navbar`：① 父须移动类 *-frame 直接子层 ② 含 `.fb-nav-back` 后代，否则 WARN）；keys off `.fb-navbar` 组件存在性、放弃页面类型推断（FP≈0，对齐 S4-28 v2 教训）；0 命中=下游未迁移正常；WARN 阶段，3 仓 dry-run + FP<30% 后升 FAIL（SSOT #45）|
| S4-36 data-tp ↔ tp-marker 配对完整性 | 触点视觉锚 / 配对完整性 | 「每个 data-tp 必有同级/父级 tp-marker 编号匹配」| 已机械化（WARN，零启发式）| `precheck_stage4.check_tp_marker_pairing`（扫 data-tp → ±500 字符内 tp-marker 编号匹配 + 豁免白名单 showcase-only/is-unchecked/nav-inactive）；治 issue #56 235 处 data-tp 缺 marker 实证；WARN 阶段，下游迁移完升 FAIL（SSOT #55，A 方案 A.1）|
| S4-37 tp-marker tp-wrap 包裹结构 | 视觉定位基准 / 结构完整性 | 「tp-marker 父链路必含 tp-wrap 或 data-tp-no-wrap」| 已机械化（WARN，零启发式）| `precheck_stage4.check_tp_marker_wrap`（扫 .tp-marker → ±300 字符父链路找 tp-wrap class 或 data-tp-no-wrap 属性双白名单）；治 issue #53 103 处 marker 飞到 frame 角实证；WARN 阶段，下游迁移完升 FAIL（SSOT #55，A 方案 A.2）|
| S4-38 PRD section 最小内容粒度 | 内容粒度 / 防空壳 | 「section inner ≥ 500B 或显式豁免」| 已机械化（[Should] WARN 永不阻断）| `precheck_stage4.check_section_min_content`（正则 section 配对 + UTF-8 字节数 + `<!-- section-shell-by-design: ... -->` 豁免）；治 issue #57 spec-background/spec-data 仅壳实证（SSOT #55，A 方案 A.3）|
| S4-39 Mermaid label 字符安全 | 字符安全 / parse 错防御 | 「label 内 3 类硬违规：奇数 `"` / ≥4 个 `"` / 中文标点引号」| 已机械化（[Should] WARN 永不阻断）| `precheck_stage4.check_mermaid_label_chars`（复用 `_extract_mermaid_blocks` + 3 类硬违规检测）；治 issue #57 EmptyState `"..."` parse 错实证；v2 算法 FP 收敛（quotation-tool 实测 v1 误报 214 → v2 2 处真实）；与 S4-33 mmdc parse 兜底正交（SSOT #55，A 方案 A.4）|
| S4-40 .interaction-card 内禁 inline 字号覆盖 | 跨项目字号一致性 / 表达规范 | 「.interaction-card 内任何元素 style 禁含 font-size」| 已机械化（[Must] WARN）| `precheck_stage4.check_interaction_card_no_inline_font`（`_InteractionCardInlineFontChecker` HTMLParser 追踪 `.interaction-card` 嵌套深度 + 扫所有元素 style font-size 字面，零启发式 FP≈0；模板已硬编码字号体系于 `prd_template.html` `.interaction-card` 段）；治产品总监跨项目反馈「字体有大有小」根因（SSOT #62，E.3 第 1 条）|
| S4-41 典型交互说明字面必须在 .interaction-card 内 | 标准容器使用 / 防自造结构 | 「5 类信号字面在 `.interaction-card` 父链路内（pre/code 豁免）」| 已机械化（[Must] WARN）| `precheck_stage4.check_interaction_card_class_compliance`（`_InteractionCardClassComplianceChecker` HTMLParser 追踪 div+pre+code 嵌套 + handle_data 扫 5 类信号字面「交互说明 —」/「状态差异说明」/「列表回显说明」/「数据展示说明」/「触点交互说明」vs `.interaction-card` 父链路验证，反向扫零启发式 FP≈0；2026-06-02 SSOT #62 v2 升级"卡片字段说明" → "数据展示说明"）；2026-06-02 NB-WE-04 闭环实装（反向扫策略颠覆原"启发式空间复杂"判定）；治产品总监跨项目反馈「触点统一样式要求」根因（SSOT #62，E.3 第 2 条）|
| S4-42 .fb-state-loading 内禁 inline padding 覆盖 | 跨平台骨架屏一致性 / 表达规范 | 「.fb-state-loading 元素 style 禁含 padding」| 已机械化（[Must] WARN）| `precheck_stage4.check_skeleton_inline_padding`（`_SkeletonInlinePaddingChecker` HTMLParser 扫 .fb-state-loading 元素 style padding 字面，零启发式 FP≈0；模板 :root 已声明 --skel-*-padding tokens + 平台 selector 自动应用）；治产品总监跨项目反馈「同平台骨架屏尺寸不一致」根因（SSOT #63，下游 D1 治本）|
| S4-43 data-tp 容器级唯一性纪律 | 触点 ID 粒度 / 防 PM 自由发挥 | 「同 *-frame 内同 data-tp 出现 > 1 次 → WARN」| 已机械化（[Must] WARN dry-run）| `precheck_stage4.check_prd_data_tp_container_uniqueness`（`_DataTpContainerUniquenessChecker` HTMLParser 追踪 div 嵌套 + 标识 *-frame + 按 frame 收集 data-tp 出现统计；list/table 多实例豁免由 PM/Sup 看上下文人审）；与 S4-24 协同（S4-24 强制存在 / S4-43 容器级粒度）；治产品总监跨项目反馈「触点 ID 重复 / chip group 自由发挥」根因（SSOT #64，下游 D2 治本）|
| S4-44 spec 模块子块完整度 | 章节完整性 / SSOT #61 实施纪律 | 「每模块 7 必填 .1/.2/.2A/.3/.3A/.4/.5/.7 子块齐全」| 已机械化（[Must] WARN）| `precheck_stage4.check_spec_module_subsections_completeness`（扫 spec.md S2.MXX 模块段头 + 每模块 7 必填子段 grep；启发式豁免：无 S2.MXX 段头跳过旧版 spec）；兑现 SSOT #61 B 组待补承诺；与 S4-45~48 协同（SSOT #66）|
| S4-45 S2.MXX.7 Gherkin 完整度 | 验收契约完整性 / 测试 Agent 输入 | 「每状态条目含 4 子项 + ```gherkin 围栏 Given/When/Then 三段」| 已机械化（[Must] WARN）| `precheck_stage4.check_spec_gherkin_completeness`（扫 .7 段每状态锚 `**P\d+-` 或 `**S\d+：` + 4 子项「互斥说明 / 触发条件 / 页面表现 / 验收标准」+ ```gherkin 围栏 + Given/When/Then 三段；适配 SSOT #61 升级前后两种状态锚格式）；治"PM 漏写完整 Gherkin"反 pattern（dry-run 私域主页 60/114 状态缺要素，真违规暴露）（SSOT #66）|
| S4-46 API ID 引用闭环 | 编号一致性 / 跨文件闭环 | 「spec API-XXX ⊆ 产品定义 §10 定义集合」| 已机械化（[Must] WARN）| `precheck_stage4.check_spec_api_id_closure`（grep API-XXX 引用 vs 产品定义文件定义集合 + 差集 WARN；启发式豁免：产品定义文件不存在跳过）；治"PM 写 API-M10-XX 占位字面未替换"反 pattern（dry-run 报价工具 9/60 占位实证）（SSOT #66）|
| S4-47 NB ID 引用闭环 | 编号一致性 / 决策追溯 | 「spec NB-XXX ⊆ ledger ∪ scaffold.notes ∪ §S0.5 ∪ 产品定义」| 已机械化（[Must] WARN）| `precheck_stage4.check_spec_nb_id_closure`（grep NB-XXX 引用 vs 4 源定义集合 + 差集 WARN；启发式豁免：L2 工作流前缀 NB-WE-/NB-LIT-/NB-SSOT/NB-SNB 跳过）；治"PM 自定义 NB 命名未在 ledger 登记"反 pattern（SSOT #66）|
| S4-48 模块编号连续性 + 子段父子约束 | 编号一致性 / 层级完整性 | 「S2.MXX M01~MNN 无跳号 + .2A 必有父 .2 + .3A 必有父 .3」| 已机械化（[Must] WARN）| `precheck_stage4.check_spec_section_numbering_consistency`（扫 S2.MXX 模块编号连续性 + .2A/.3A 子段父父子层级；启发式豁免：无 S2.MXX 跳过）；治"PM 删模块后未重编号"反 pattern（SSOT #66）|
| S4-49 spec §S2.MXX.4B 业务规则段头 | 章节完整性 / SSOT #68 派生输入 | 「每模块含 .4B 业务规则段头 + 段内非空」| 已机械化（[Should] WARN）| `precheck_stage4.check_spec_section_4B_business_rules`（扫 spec.md S2.MXX 模块 + 每模块 .4B 段头存在 + 段内字符 ≥ 5；启发式豁免：无 S2.MXX 段头跳过旧版 spec）；治"PM 漏写业务规则导致 C-4 派生失败"反 pattern（SSOT #68）|
| S4-50 spec §S2.MXX.5B 数据规模段头 | 章节完整性 / SSOT #68 派生输入 | 「每模块含 .5B 数据规模段头 + 段内非空」| 已机械化（[Should] WARN）| `precheck_stage4.check_spec_section_5B_data_scale`（扫 spec.md S2.MXX 模块 + 每模块 .5B 段头存在 + 段内字符 ≥ 5；启发式豁免：无 S2.MXX 段头跳过旧版 spec）；治"PM 漏写数据规模导致 C-4 派生失败"反 pattern（SSOT #68）|
| S4-51 spec F-xxx 主页面字段 | 派生路径完整性 / SSOT #68 枢纽字段 | 「每 F-xxx 节含主页面字段 + 值 ∈ 涉及页面集合」| 已机械化（[Should] WARN）| `precheck_stage4.check_spec_function_main_page_field`（扫 F-xxx 节 + 主页面字段抽取 + 涉及页面集合交集）；治"PM 漏写主页面字段 → A-05 跳转目标空 + C-4 派生失败连锁"根因（SSOT #68）|
| S4-52 spec F-xxx 4 必填字段 | 章节完整性 / 派生输入 | 「每 F-xxx 节含 4 必填字段：优先级 / 所属旅程 / 涉及页面 / 主页面」| 已机械化（[Should] WARN）| `precheck_stage4.check_spec_function_xxx_required`（扫 F-xxx 节 + 4 字段 regex 抽取）；治"PM 写 F-xxx 节缺关键字段"反 pattern（SSOT #68）|
| S4-53 prd interaction-card C-4 派生闭环 | 派生闭环 / SSOT #68 输出验证 | 「interaction-card C-4 痕迹（[C4-START/END] ∪ c4-cross-page-note）覆盖率 ≥ 50%」| 已机械化（[Should] WARN）| `precheck_stage4.check_prd_c4_derivation_closure`（统计 interaction-card 数 + C-4 注入痕迹数 + 覆盖率阈值；启发式豁免：无 .interaction-card / 无 F-xxx 跳过）；治"assemble.inject_c4 派生失败但 PM 未发现"根因（SSOT #68）|
| S4-54 prd A-05 旧 article 形态清除 | 信息架构重组 / SSOT #67 输出验证 | 「spec-feature section 内无 feature-block 旧 article 形态」| 已机械化（[Should] WARN）| `precheck_stage4.check_prd_a05_removed`（regex 扫 spec-feature section 内含 feature-block 即 WARN）；治"SSOT #67 重组后残留旧 article 形态"漂移（SSOT #67）|
| S4-55 prd A-索引 4 列 + 行数对齐 | 派生闭环 / SSOT #67 输出验证 | 「spec-feature section 含 4 列 thead + tbody 行数 == spec.md F-xxx 节数」| 已机械化（[Should] WARN）| `precheck_stage4.check_prd_a_index_complete`（regex 扫 4 列 thead + tbody tr 数 vs F-xxx 节数对齐；启发式豁免：无 section / 无 F-xxx 跳过）；治"assemble.build_function_overview_index 派生不完整或 spec 添加 F 后未重 assemble"根因（SSOT #67）|
| S4-56 interaction-card C-0 状态差异说明 | schema 合规 / SSOT #69 | 「每 .interaction-card 含 `<div class="state-diff-note">` 子区块」| 已机械化（[Should] WARN）| `precheck_stage4.check_interaction_c0_state_diff_note`（迭代每 .interaction-card + 扫 state-diff-note class 字面；启发式豁免：无 card 跳过）；治"PM 用 `<p>` 字面替代 .state-diff-note"反 pattern（SSOT #69）|
| S4-57 interaction-card C-1 列表 4 行表 | schema 合规 / SSOT #69 | 「含列表回显说明的卡须含 4 固定行目（排序规则 / 加载方式 / 总数回显 / 空列表判断）」| 已机械化（[Should] WARN）| `precheck_stage4.check_interaction_c1_list_table`（扫卡内「列表回显说明」标题后 1500 字符 + 4 key 字面；豁免：「本帧无列表」显式注明）；治"C-1 列表表格列不齐（缺空列表判断）"反 pattern（SSOT #69）|
| S4-58 interaction-card C-2.A 6 列单元清单 | schema 合规 / SSOT #69 | 「含数据展示说明的卡 thead 须含 6 列（C 触点 ID / 单元名称 / 是否封装为组件 / 渲染时机 / 跨平台差异 / 关联 T 触点）」| 已机械化（[Should] WARN）| `precheck_stage4.check_interaction_c2a_unit_index`（扫卡内「数据展示说明」标题后 thead + 6 列字面；豁免：「本帧无数据展示」）；治"PM 直接放字段子表，缺索引层"反 pattern（SSOT #69）|
| S4-59 interaction-card C-2.B 5 列含 D 触点 ID | schema 合规 / SSOT #69 | 「含字段说明子标题的卡 thead 须含 5 列（D 触点 ID / 字段名 / 接口字段 / 显示格式 / 空值处理）」| 已机械化（[Should] WARN）| `precheck_stage4.check_interaction_c2b_field_table`（扫卡内「字段说明」子标题后 thead + 5 列字面）；治"C-2.B 缺 D 触点 ID 列"反 pattern（SSOT #69）|
| S4-60 interaction-card C-3 触点表 6 列 | schema 合规 / SSOT #69 | 「含触点交互说明的卡 thead 须含 6 列（序号 / 触点说明 / 触发 / 行为 / 跳转 / 边缘）」| 已机械化（[Should] WARN）| `precheck_stage4.check_interaction_c3_touchpoint_table`（扫卡内「触点交互说明」标题后 thead + 6 列字面；豁免：「本帧无交互触点」）；治"C-3 触点表缺跳转 / 边缘列"反 pattern（SSOT #69）|
| S4-61 interaction-card 同名子区块重复检测 | schema 合规 / SSOT #69 延伸（议题 2B）| 「每 .interaction-card 内同名子标题字面（业务规则 / 数据回显 / 验收标准）出现 ≥ 2 次 → WARN」| 已机械化（[Should] WARN）| `precheck_stage4.check_interaction_card_double_subsection`（扫每卡 3 子标题 key 的两类形态：PM 手写 `<p><strong>KEY</strong>` + C-4 派生 `<div class="c4-sub-title">KEY</div>` / `<div class="data-sub-title">KEY</div>`，并集 ≥ 2 → WARN）；治"PM 手写业务规则段 + C-4 派生业务规则段双段并存"反 pattern（私域主页 95/143 实证）|
| S4-62 tp-marker 反向配对 | schema 合规 / SSOT #65 延伸（议题 3）| 「每 `<span class="tp-marker">NN</span>` 必有同级或邻近 ≤ 500 字符内 data-tp 末段数字 = NN 配对」| 已机械化（[Should] WARN）| `precheck_stage4.check_tp_marker_reverse_pairing`（与 S4-36 对偶：正向 data-tp→marker / 反向 marker→data-tp；豁免 class 同 S4-36：showcase-only / is-unchecked / nav-inactive）；治"PM 删 data-tp 后忘删悬空 marker / 重复粘贴未清理"反 pattern（bujue-quotation-tool 14 处实证）|
| S4-63 interaction-card C-4 表达形式校验 | schema 合规 / SSOT #69 延伸（议题 2A）| 「含 [C4-START: 注入标记的 .interaction-card：C-4.A 必为 `<table class="c4-business-rules">` / C-4.B 必为 `<table class="c4-data-scale">` / C-4.C 必为 `<pre class="gherkin">`」| 已机械化（[Should] WARN）| `precheck_stage4.check_interaction_card_c4_format`（扫含 C-4 注入标记的 .interaction-card，3 子区块表达形式合规度；豁免：无 .interaction-card / 无 C-4 注入标记）；治"C-4.A 用 `<ul>` / C-4.B 用 `<p>` 单段（议题 2A 前历史 PRD 派生层）"反 pattern；重 assemble 后规范派生自动合规 |
| S4-64 interaction-card sub-title 顺序 + 完整性 | schema 合规 / SSOT #69 延伸（议题 16，NB-R3-02）| 「每 .interaction-card 内 4 个标准 sub-title 头（C-1 列表回显 / C-2 数据展示 / C-3 触点交互 / C-4 业务契约）须按规范固定顺序出现；缺失任一 → WARN（含『真无内容』豁免：sub-title 头存在 + 紧跟「本帧无 XXX」豁免文案合规）」| 已机械化（[Should] WARN）| `precheck_stage4.check_interaction_card_subtitle_order`（扫每 .interaction-card 4 sub-title 头顺序 + 完整性，含 49 处真无内容豁免 placeholder 注入完整性校验；豁免：prd.html 无 .interaction-card）；治"私域主页 PM R3 自报 24 帧 C-3 sub-title 头治本实际未 commit"反 pattern（SNB-R4-01 sha 审计同议题）|
| S4-65 scaffold.json version ↔ changelog 末行 version 一致性 | 数据一致性 / SSOT #48（议题 20 NB-WE-2A-R8-03 P1）| 「scaffold.json[\"version\"] 必与 [\"changelog\"][-1][\"version\"] 一致（SSOT #48 仅允许 v0.1/v1.0/vN.0 三类触发点）」| 已机械化（[Should] WARN）| `precheck_stage4.check_scaffold_version_changelog_consistency`（扫 scaffold 内部 version vs changelog 末行 version 一致性；豁免：scaffold 不存在 / 解析失败 / version 或 changelog 缺）；治"私域主页 R8-03 实证 scaffold.json version=v4.0 vs changelog 末行 v0.1 不同步"反 pattern；配套 assemble.py 派生层 _overwrite_cover_version_from_spec_changelog 强制对齐 prd 封面字面 |
| S4-66 §A-04.2 业务流程图双视图三件套 | schema 合规 / SSOT #30 派生方完整化（议题 25）| 「`<section id="spec-business-flow">` 内每个含 `<pre class="mermaid">` 的 spec-block 必同时含 journey-toggle + journey-table-view + journey-flow-view 三件套字面（同构复刻 A-04.1 用户旅程）」| 已机械化（[Should] WARN）| `precheck_stage4.check_spec_business_flow_double_view`（扫每 spec-block 含 mermaid 的三件套字面齐全，缺一即 WARN 列出违规 spec-block 标题 + 缺失件套；豁免：spec-business-flow 不存在 / section 内无 mermaid）；治"Foundation Agent 漏实现 §A-04.2 双视图规范"漏洞（报价工具 3/3 PASS 实证可做对 / 私域 5/5 命中 实证漏实现）；dry-run FP=0% 远 < 30% 后续升 FAIL |
| S4-67 渲染契约标记完整性（R8）| 完整性 / SSOT #77（实验 §8 批量摊薄漏搬运）| 「契约期望触点 ID（spec .3 转录）⊆ 帧内 `data-tp` 标记集 + 期望字段（.4 转录）⊆ 本页帧 `data-field` 标记集；缺标记 = 漏渲染或漏标记」| 已机械化（[Should] WARN）| `precheck_stage4.check_render_contract`（复用 gen_render_contract 转录器，**验标记 presence 零 FP-by-design 非"渲染没"语义猜测**；勾是自报标记是物证 → 验标记不验勾；豁免：无 modules / prd 无 FRAME 块 / spec 无 .3/.4）；dry-run 私域触点 76% / 字段 36% 有标记（baseline gap = 搬运漏损）；data-field 新约定既有下游普遍未标 → WARN 不阻塞，≥2 仓反馈 + FP<30% 升 FAIL；语义正确性交 Supervisor §4.4 抽样（机械验完整性 + 人工验正确性分工）|
| S4-68 全阶段产物正文禁内联变更标记（**跨阶段**）| 下游可读性 / SSOT #79（议题 24）| 「**阶段 1/2/3/4 所有产物**正文禁含内联变更标记——`【vN.N…】`/`【历史留痕…】` 等方括号标记，及含 `CR-NNNN`/`议题 #N`/`SSOT #N`/`调整意见` 的圆括号；变更历史只走变更记录表 + git，**查版本差异用 `git diff`**。**正向配对（怎么写）**：成果正文只描述产品**当前态**（本版应有的样子），版本演进信息只进变更记录表 + git，不在正文留新旧版本对照 / 演进批注——禁令（不该写什么）+ 正向原则（该怎么写）双全，PM 才不会清完再犯。schema 标记（`【触发态】【组件】【区域】【字段回显】【业务定位】`…）+ 派生溯源（`（来源：…）`）+ workflow 信号（`【✅ PM 自审完成，提交主管审核】`，check_submit_marker 强制）不在此列」| 已机械化（[Should] WARN，**4 阶段守源头**）| **`precheck_stage1/2/3/4` 各 `check_no_inline_change_markers`**（检测 + 文案单源自 `strip_inline_change_markers.warn_inline_markers`，**schema 白名单 + `来源：`/workflow 信号豁免**）；前移根因：实证私域各阶段标记数 需求 478/功能 508/产品定义 618/spec 589，证明源头在前序阶段、stage4-only 是 sink 被动修补；定位用 `strip_inline_change_markers.py`（**只读报告**，按 version/pure_ref/mixed 分类 + 行号列出供 PM 手动改——2026-06-10 审计移除 `--write` 自动删除：机械删除会损伤语义（共存新旧版本合并矛盾 / 需求与追溯同括号不可拆 / 悬挂分隔）；**删除一律 PM 手动做**）；dry-run business-circle spec=0 + private-domain 全阶段命中 FP≈0% 远 < 30%；既有下游普遍含历史标记 → WARN 渐进清理。**WARN→FAIL 升级触发界定（消除"模糊期限"）**：当 ①≥2 个**独立产品仓** PM 反馈确认该规则有效 + ②该仓存量内联标记清理覆盖 ≥90% + ③由 `workflow-evolution` 评估通过 三条件同时满足后，方议升 FAIL；在此之前永久 WARN（与 S4-33/34/35「下游迁移完升 FAIL」+ SSOT #66「≥2 仓 + FP<30% 升 FAIL」同范式；"≥2 仓" = 2 个不同产品仓而非同仓 2 次） |

**对照表使用方式**：

- **PM 写自审报告**：按行核查每条 S4-XX 的"PM 自审 §5.4"列对应章节是否已写
- **Supervisor 写审核报告**：按行核查每条 S4-XX 的"Supervisor §4.4"列；标"已机械化"的看 precheck 报告即可
- **precheck 维护**：表中"precheck 函数"列即是对应 `precheck_stage4.py` 中的函数名，修改函数时回查本表

### S4 规则机械化优先级原则（新增 / 修订 S4 规则时强制评估）

`[Should]` 新增 S4 规则时**必须**评估机械化可行性（在 PR / commit message 中显式记录评估结论），按以下三档分类：

| 档位 | 判据 | 处置 |
|------|------|------|
| **可机械化**（首选）| 数据源在 scaffold / spec / prd / CSS 内，且可严格 diff / regex 校验（如条目数对照、字段集合 diff、selector 唯一性、prd_id 集合解析）| 在 `precheck_stage4.py` 实现兜底 + 对照表"precheck 函数"列填实函数名 |
| **部分机械化** | 含语义判断但有结构性兜底点（如 fb-* 已登记是机械的、业务-语义匹配是人工的）| 实现可校验部分 + 对照表"precheck 函数"列标"部分（{校验维度}）"；文档明示语义部分由人工 |
| **纯人工兜底** | 业务语义 / 自然语言 / 视觉判断 / 流程纪律，无 SSOT 解析点 | 保留人工兜底，**对照表 precheck 列必须显式标"—（人工兜底）"+ 在 S4 规则正文加"`[人工兜底]` 理由：xxx"** |

`[Should]` 现有规则中标注"—"的人工兜底项须周期性复评是否可机械化——截至 2026-05-08（NB-WE-12 commit），原"人工兜底"已陆续升级 7 条：S4-04（平台覆盖）/ S4-05（状态覆盖）/ S4-08（cursor:pointer）/ S4-09（触点编号）/ S4-13（导航闭环）/ S4-21（字段绑定）/ S4-22（组件变更清单）；剩余真"—"集中在业务语义 / 流程纪律类（S4-01/06/07/10/11/12/14/15/20），机械化可行性低,优先保留人工兜底。

`[Recommended]` 已机械化规则的 precheck 函数应至少有 3 个烟雾测试用例（合法 / 违规 / 边界），写在测试目录或函数 docstring 内。

---

## 七、审核方自动化核查清单（Supervisor 用）

### 阶段4 审核核查工具命令（推荐使用 Grep 工具）

```
# 1. 所有 section id 唯一性检查
grep -oE 'id="H-P[0-9]+"' outputs/prd_xxx_latest.html | sort | uniq -c
# 任何 count > 1 的即为 S4-03 违反

# 2. 本页 frame-card 数抽样（以 P02 为例）
# 在 prd.html 中定位 <section id="H-P02"> 区域统计 frame-card 数
# 在 spec.md 中定位 S5 章节统计状态表行数
# 两者必须相等

# 3. 触点 ID 集合对比
grep -oE 'P[0-9]+-T[0-9]+' outputs/spec_xxx_latest.md | sort -u
grep -oE 'P[0-9]+-T[0-9]+' outputs/prd_xxx_latest.html | sort -u
# 两个集合必须完全相同

# 4. API 编号残留检查（本期权威映射以 SN.4 为准）
# 将旧内部编号列表 vs SN.4 权威编号列表对比，全文搜索旧编号应 = 0

# 5. cursor:pointer 覆盖率
grep -c 'class="btn' outputs/prd_xxx_latest.html
grep -c 'cursor:pointer' outputs/prd_xxx_latest.html
# 前者应 ≤ 后者
```

---

## 八、维护规则

- 本文件由工作流维护者增补；每次阶段执行中发现新的普遍性遗漏风险，须补充相应 `[MUST]` 规则
- 更新时必须同步在本文件末尾追加变更记录

---

## 变更记录

| 版本 | 变更内容 | 日期 |
|------|---------|------|
| v1.0 | 初版创建；汇总阶段1-4硬规则；重点细化阶段4分步自审指令 | 2026-04-19 |
