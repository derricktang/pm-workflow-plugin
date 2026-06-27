# 工作流优化建议汇总报告 — 上游处理用

**复盘来源**：`process_record/issues/2026-05-14_0302.md`（68 条 / 全周期 v1.0~v7.0+CR-28）
**复盘时间**：2026-05-29
**复盘命令**：`/retro`
**已确认采纳决策**：
- 升级方案 G 全采（分层判定 + forward-only 因果链 + 三分类粒度反查 + 模板层次纪律）
- 未标注 UI 字面 = WARN 不阻断
- 撤回机械 grep 反证方案 E' / 反向残留扫描方案 E
**用途**：用户带去上游 `pm-group/claude-code-pm-workflow` 仓库走 `workflow-evolution` skill 修订 L2 文件

---

## 0. 优化总览（按 ROI 排序）

| 编号 | 名称 | 解决共性 | 强度 | 上游主文件 |
|------|------|---------|------|---------|
| **G** | 调整层次分类 + forward-only 因果链 + 粒度反查 + 模板层次纪律 | 共性 6+7（NB 同步盲区 + 决策残留盲区，根因 = 阶段间粒度污染）| [Must] | `pm-workflow/agents/AI产品经理_Agent.md` + `tmpl_需求分析.md` + `tmpl_功能规划.md` + `tmpl_产品定义.md` + `agents/AI产品主管_Agent.md` |
| **A** | precheck_stage4 多项配对/完整性校验 | 共性 2（PRD 精细化盲区 8 条）| [Must] / [Should] | `pm-workflow/scripts/precheck_stage4.py` |
| **B** | PM 评估"边界自检"强制声明 | 共性 3（PM 越界推荐 4 条）| [Must] | `pm-workflow/agents/AI产品经理_Agent.md` |
| **C** | 阶段 1 业务架构覆盖度自检清单 | 共性 4（业务架构晚识别）| [Must] | `pm-workflow/rules/tmpl_需求分析.md` + `agents/AI产品经理_Agent.md` |
| **D** | UI 表达"轻量优先 / 默认简洁"原则 | 共性 5（PM 实施"过重"）| [Should] | `pm-workflow/rules/proto_spec_md.md` + `proto_contract.md` |
| **F** | L2 升级批次窗口 + SSOT 单源约束 | 共性 1（L2 多轮迭代触发 L1 重做 + SSOT 多源抄引）| [Recommended] | `pm-workflow/skills/workflow-evolution/SKILL.md` + `ssot_anchors.md` |

---

## 1. 共性根因总结（7 项 / 覆盖 ~55 条意见）

### 🟥 共性 1：L2 框架快速迭代触发 L1 多轮重做 + L2/L1 同步规范不足

**代表 issue**：#30/#31/#32/#33（SSOT#41 骨架屏 4 轮升级）+ #58（PAD/tablet SSOT 多源分散）

**根因**：L2 升级未与 L1 落盘窗口解耦，缺"L2 稳定批次锁定 → 批量落 L1"机制；L2 多源 SSOT 表述让 PM 多源抄引引入 spec 内部矛盾。

### 🟥 共性 2：PRD 精细化盲区集中爆发

**代表 issue**：#28（M01 缺 APP 帧）/ #50（手机版竖向布局缺）/ #52+#53（tp-marker 飘到 phone-frame 角）/ #54（marker 编号错位）/ #55（modal 弹框层级错）/ #56（235 处 data-tp 缺 tp-marker）/ #57（prd section 真空 + mermaid label 引号未转义）

**根因**：precheck_stage4.py 校验只查"集合一致性"（如 116↔116 触点配平、93 帧三向相等），不查"配对完整性 / 包裹结构 / 视觉定位 / section 内容粒度"。

### 🟥 共性 3：PM 评估/推荐越界（不读 L2 真源 / 不核业务边界）

**代表 issue**：#46（PM 设计"每节点旁挂取消按钮"误导用户）/ #52 PM 初判 L2 CSS 偏差（实为 L1 tp-wrap 缺失）/ #58 PM 诊断"L2 双写冲突"（Explore cross-check 证伪为 PM 多源抄引）/ #63（PM 推荐"顶栏 logo 回主页"违反容器层边界）

**根因**：PM 评估时没有强制读边界规范文件 / Explore L2 真源，编排器又禁止自审范围；导致 PM 评估结论可能"自圆其说但越界"。

### 🟥 共性 4：业务架构洞察延迟（"晚识别"模式）

**代表 issue**：#1（超管角色 R-03）/ #7（文档生成）/ #15（云盘容量）/ #34（审查中预览）/ #59-#65（异步主页恢复 + M03+M07 双路径共享 + P01 双卡片）

**根因**：阶段 1 需求分析的角色覆盖与跨场景关联建模不充分；JTBD/persona/OST 4 步分析法没有强制要求"业务架构覆盖度自检"+"跨场景关联分析"，导致重要架构关系被遗漏。

### 🟥 共性 5：UI 实现"过重"成为反复出现的偏差

**代表 issue**：#33（骨架屏画得过详尽）/ #46（每节点旁挂取消按钮）/ #51（仪式感弱，反向）/ #66（取消反馈显示资源详单）/ #67（取消弹窗显示详单）

**根因**：proto_spec_md / proto_contract / PM Agent 规范没有显式 "UI 克制 / 默认简洁"原则；PM 实施时倾向"信息密集 / 全表达"。

### 🟥 共性 6：NB 决策修订后跨阶段同步盲区

**代表表现**：CR-28 N-1（阶段 1 文件头 NB 数字漂移 104→108）/ NB-247 ⑧项跨阶段同步 / SNB-W1（eval "429 vs 433" 行数）

**根因**：CLAUDE.md / changeRequest.md / nextStage.md 没有强制规定"NB 决策修订后必须跨阶段 grep 同步 + 自动登记 §八收尾批量同步清单"。

### 🟥 共性 7：决策落地后"残留旧字面"盲区 + 阶段间粒度污染（共性 6 同根本因深层）

**代表 issue**：#68 — issue#66/#67 决策"取消 UI 一律简化"后，文档其他位置仍残留"资源回收范围预览"等冲突描述（阶段 3 §744 / spec line 1130/1182/1183/1184/1185/1187 共 7 处）

**根因辨析（关键 — 用户深度反驳后的精确表述）**：
- **表层**：PM 范围评估漏（issue #66 评估报告把"§一/§二/§三"列为"未受影响章节"，但实测 §一 M1-13 + §二 mermaid line 255/380 含决策核心冲突字面）
- **底层**：阶段 1/2 把 UI 细节"资源回收范围预览"前置写进文档 → UI 调整时必然跨阶段同步 → 范围评估天然复杂 → 漏的概率大
- **"反向不成立"**：阶段 1 含某 UI 字面 ≠ 该处属底层逻辑；可能因"上游粒度污染"或合法承载客户原始诉求 — 简单 grep 关键词会把两者混在一起

---

## 2. 优化 G — 调整层次分类 + Forward-only 因果链 + 粒度反查 + 模板层次纪律

**根因背景**：CLAUDE.md 第二步范围评估 [Must] 已强制 grep 多文件，但 PM 评估时凭"想象哪些章节受影响"代替 grep 实证；机械 grep 反证又把"粒度污染残留"与"真业务逻辑"混在一起处理 — 真正根治在于把"调整层次性质"作为评估前提 + 上游粒度污染反查 + 阶段模板源头约束粒度。

### G.1 PM 评估强制三段分类 [Must]

**上游文件**：`pm-workflow/agents/AI产品经理_Agent.md`（PM 评估范围段）+ `CLAUDE.md`（调整意见自动记录规则第二步）

**插入条款草稿**：

```markdown
### §X.X 调整层次分类 + 影响阶段推导 [Must]

PM Agent 在第二步范围评估前必须以显式三段写入评估报告 §0：

A. 调整层次性质判定（四选一或多选）
   □ 业务逻辑层（规则 / 状态机 / 算法 / 数据流 / NB 决策）
   □ UI/UX 表达层（视觉 / 文案 / 反馈 / 交互细节）
   □ Schema 层（字段 / 实体 / 接口 schema）
   □ 跨层综合（同时含多层）

B. 按层次推导影响阶段（forward-only，不反向推导）
   业务逻辑层 → 必影响 阶段 1 ∪ 2 ∪ 3 ∪ 4（全链路同步）
   Schema 层 → 必影响 阶段 3 ∪ 4
   UI/UX 表达层 → 主要影响 阶段 4
                  阶段 3 可能影响（描述层）
                  阶段 1/2 仅当承载客户原始诉求 UI 时影响（详 §G.2）
   跨层 → 各子层并集

C. 反向不可推导声明
   靠前阶段含某 UI 字面 ≠ 该处属底层逻辑
   → 必须走 §G.2 上游粒度污染反查三分类后再裁定

任一段缺失 → 评估报告 FAIL，Supervisor 一票否决
```

### G.2 上游"含字面残留"识别三分类 [Should]

**插入条款草稿**：

```markdown
### §X.X 上游粒度污染反查（处理"反向不成立"）[Should]

触发条件：分类 = UI/UX 表达层 + 靠前阶段（1/2/3）含该 UI 字面

第一步：派 Explore subagent 反向定位 + 来源辨识
       逐处命中,Explore 上下文识别该字面是否属：
       ① 客户原始诉求 UI（标注【来源：…】或在客户诉求枚举段）
       ② PM 推导粒度污染（无来源标注 / 出现在实现细节段）
       ③ 未标注 / 模糊（历史遗留）

第二步：按三分类处理
   ① 客户原始诉求 UI（合法承载）
      → 走 c2 就地同步（按新决策更新字面,保留诉求语义 + 来源标注不动）
      → 示例：issue #25 "暂未配置主页包"提示页 UI 调整时
              阶段 1 同步改文案,标注保持

   ② PM 推导粒度污染（违规承载）
      → 走 c1 清回业务粒度（删 UI 细节,留业务语义）
      → 示例：issue #66 阶段 1 M1-13 "资源回收范围预览矩阵"
              清回为 "清理对应节点资源（按 NB-210 资源回收矩阵）"

   ③ 未标注来源 / 模糊（待判定）
      → 派 PM Agent 评估归类后按 ①/② 路径处理
      → 评估同时要求 PM 给出"来源标注补全建议"防再次模糊

第三步：选定处理路径写入评估报告 §粒度反查段
       Supervisor 复审核三分类完备性 + 路径选择合理性
```

### G.3 阶段模板层次纪律 [Must]

**上游文件**：`tmpl_需求分析.md` + `tmpl_功能规划.md` + `tmpl_产品定义.md`（各在顶部规范段插入）

**插入条款草稿**：

```markdown
### §X.X 阶段分层粒度纪律 [Must]

各阶段产物描述粒度严格分层 + UI 字面来源标注：

阶段 1 需求分析：
  ✅ 主体写：业务目标 / 角色诉求 / 场景流程 / 业务规则 / NB 决策
  ✅ 允许 UI 字面承载客户原始诉求,[Must] 标注来源：
      格式：【来源：产品总监诉求 / 客户访谈 / issue #N】
  ❌ 禁写 PM 推导的 UI 实现细节（属阶段 4 落点）

阶段 2 功能规划：
  ✅ 主体写：模块拆解 / 子功能 / 依赖关系 / mermaid 节点语义
  ✅ 允许 UI 字面承载客户原始诉求（标注同阶段 1 要求）
  ❌ 禁写 mermaid label 内 UI 排版细节（如 "+ 资源详单"/"+ 矩阵预览"）

阶段 3 产品定义：
  ✅ 写：交互意图 / 状态机 / 行为描述 / 接口 schema
  ✅ 允许具体 UI 描述（归"交互意图层"，视觉/文案落点仍归阶段 4）
  ❌ 禁视觉细节 / 文案最终字面 / 元素排布 schema（属 spec/prd）

阶段 4 spec/prd：UI 细节最终落点（文案 / 视觉 / 帧 / 触点）
  ✅ 任意 UI 细节
```

### G.4 Supervisor 复审强制核查 [Must] / WARN 档

**上游文件**：`pm-workflow/agents/AI产品主管_Agent.md` §4.0.X

**插入条款草稿**：

```markdown
### §4.0.X 调整层次纪律核查 [Must]

Supervisor 在通用前置审核段必核查 PM 评估报告：

1. 是否明示"调整层次性质"+ 按因果链推导影响阶段（§G.1 三段）
2. 若分类 = UI/UX 且靠前阶段命中 → 是否走 §G.2 三分类处理
3. 阶段 1-3 产物 UI 字面是否带【来源：…】标注：
   未标注的 UI 字面 → **WARN 档**（不阻断终审，建议派 PM 补标
   或评估归类 ② 清回 — 产品总监已决策 WARN 不阻断 2026-05-29）
   标注的 UI 字面 → PASS（视为合法承载）
4. PM 提交阶段 1-3 时 UI 字面无标注 → precheck WARN 档

任一未核 → Supervisor 自审失败
```

### G.5 配套 precheck 检测器（可选 [Recommended]）

**上游文件**：`pm-workflow/scripts/precheck_stage1.py` / `precheck_stage2.py` / `precheck_stage3.py`

```markdown
### S1-XX / S2-XX / S3-XX UI 字面来源标注校验 [Recommended]

正则扫描阶段 1-3 产物中疑似 UI 细节字面（关键词候选清单：
"显示...详单|显示...预览|弹窗...排版|toast|文案...字号|颜色...号|按钮...右上"等）
→ 上下文 ±2 行无【来源：…】标注 → WARN 档（不阻断 EXIT=0）
```

---

## 3. 优化 A — precheck_stage4 多项配对/完整性校验

**根因背景**：阶段 4 终审等待期密集 8 条 PRD 实现偏差（issue #28/#50/#52/#53/#54/#55/#56/#57）全是 precheck 既有校验粒度盲区。

**上游文件**：`pm-workflow/scripts/precheck_stage4.py`

### A.1 S4-XX `data-tp ⟺ tp-marker` 配对完整性校验 [Must]

```markdown
规则：每个 data-tp 元素必有同级或父级 <span class="tp-marker">NN</span>，
     且 NN = data-tp 的 T 编号

豁免（白名单）：
  - showcase 区（class 含 "showcase-only"）
  - 未选中 fb-radio（class 含 "is-unchecked"）
  - 未选中 nav（class 含 "nav-inactive"）

违规 → FAIL EXIT=1
来源：issue #56 暴露,235 处 data-tp 缺 marker
```

### A.2 S4-XX `tp-wrap` 包裹结构校验 [Must]

```markdown
规则：所有 <span class="tp-marker"> 必有父级 tp-wrap（确保 position:relative
     定位基准）

豁免：
  - tp-marker 直接置于已 position:relative 的容器内（显式标 data-tp-no-wrap）

违规 → FAIL EXIT=1
来源：issue #53 暴露,103 处 marker 飞到 phone-frame
```

### A.3 S4-XX `prd section` 最小内容粒度校验 [Should]

```markdown
规则：每个 <section id="..."> 字符数 ≥ 阈值（建议 ≥ 500B 非空壳）

豁免：显式标注 <!-- section-shell-by-design: <reason> -->

违规 → WARN 档
来源：issue #57 暴露,spec-background/spec-data 仅壳
```

### A.4 S4-XX `mermaid` label 字符安全校验 [Should]

```markdown
规则：扫描所有 mermaid block 节点 label 内：
  - 双引号 / 单引号未转义
  - 中文标点（，。；："" ''）混入

违规 → WARN 档 + 建议字面（"..." → '...' 或转义为 &quot;）
来源：issue #57 暴露,EmptyState label 含 "..." 触发 mermaid parse 错
```

---

## 4. 优化 B — PM 评估"边界自检"强制声明 ✅ 已落地（SSOT #56，2026-05-30）

**根因背景**：issue #46/#52/#58/#63 共 4 条 PM 越界推荐（设计/L2/容器边界/同业先例）。

**上游文件**：`pm-workflow/agents/AI产品经理_Agent.md`（PM 评估 / 推荐方案段）

**插入条款草稿**：

```markdown
### §X.X PM 评估/推荐方案前必读边界 [Must]

PM Agent 在派发"评估方案 / 推荐方案"前,必须在自审清单以显式自检段回答：

1. 业务边界自检
   本推荐是否涉及"管理后台容器 / 跨模块边界 / 跨层职责 / 现网公共能力"？
   涉及则 [Must] 列出该边界的 SSOT 真源（如 proto_platform_app.md /
   现网容器规范 / 阶段 1 §五.3 范围约束）+ 引用行号
   证明推荐方案未越界

2. L2 真源自检
   本推荐依据的 L2 规范文件（proto_*.md / agent_*.md / scaffold schema）
   是否实际 Read？
   真源 Read 路径 + 引用行号必须落盘到自审清单

3. 同业经验自检
   本推荐 UI 形态 / 状态机 / 流程结构是否引用同业先例？
   引用条目须附"先例与本场景的边界差异说明"

任一自检为空 / 未做实质核查 → 自审 FAIL
PM 自己提交主管前必须自检通过
Supervisor 复审段必核查三项自检是否落盘
```

---

## 5. 优化 C — 阶段 1 业务架构覆盖度自检清单 ✅ 已落地（SSOT #57，2026-05-30）

**根因背景**：阶段 1 多次"业务架构晚识别"（issue #1 超管 / #7 文档生成 / #15 云盘 / #34 审查中预览 / #59-#65 异步主页恢复 + 双路径共享 + P01 双卡片）— JTBD/persona/OST 4 步分析法未强制覆盖度自检。

**上游文件**：`pm-workflow/rules/tmpl_需求分析.md` + `pm-workflow/agents/AI产品经理_Agent.md` §阶段 1 任务段

**插入条款草稿**：

```markdown
### §X.X 阶段 1 业务架构覆盖度自检 [Must]

阶段 1 PM 自审前必须完成以下覆盖度自检（落盘 §七 自审清单）：

1. 角色全集自检
   列出本产品涉及所有角色枚举（含管理员 / 访客 / 超管 / 系统 / 第三方）
   每角色独立诉求段 + 验证未漏（参考枚举：业务用户 / 管理员 / 运维 /
   超管 / 客户访客 / 第三方服务 / 系统自动化 等通用全集）

2. 跨场景关联建模
   列出所有"信息流 / 操作流"中的跨场景共享环节
   （如 M01/M03/M07 三触发源是否共享 LLM/审查/OSS/CDN）
   证明哪些步骤可共享 vs 必须独立 + 共享契约登记到 NB

3. 异步 / 跨页面状态自检
   列出所有耗时操作（≥ X 秒,X 由业务定）
   判定"用户可否离开 + 是否需主页恢复 + 跨设备状态同步"
   每条耗时操作必有明示结论

4. 跨层边界自检
   明示本模块 vs 现网容器层 / 现网公共服务 / 第三方 SaaS 的边界划分
   不可越界承载（声明 "本模块仅消费 X 服务,不实现 X 服务本身"）

任一自检为空 → 阶段 1 不得提交 Supervisor
Supervisor §四 复审段必核查四项自检是否落盘 + 合理
```

---

## 6. 优化 D — UI 表达"轻量优先 / 默认简洁"原则 ✅ 已落地（SSOT #58，2026-05-30）

**根因背景**：issue #33 骨架屏过详尽 / #46 每节点旁挂取消按钮 / #50 手机版竖向缺 / #66 取消显示资源详单 / #67 取消弹窗显示详单 — PM 实施倾向"信息密集 / 全表达"。

**上游文件**：`pm-workflow/rules/proto_spec_md.md` + `pm-workflow/rules/proto_contract.md`

**插入条款草稿**：

```markdown
### §X.X UI 表达克制原则 [Should]

PM 画 skeleton / frame / 反馈提示时遵循"轻量优先 + 默认简洁"：

1. skeleton 块
   data-h 取轻量标度（小条 32-40 / 主内容 ≤ 160 / 弹层主体 120 / 兜底插画 96）
   单页 skeleton 区域数 ≤ 6
   嵌套深度 ≤ 3

2. 反馈 toast / 弹窗
   默认不展示资源清理详单 / 数据流转明细 / 内部状态枚举
   仅简洁语义（如"已取消" / "已发布" / "操作成功" + 一句关键提示）

3. 多节点流程 UI
   取消 / 重试 / 跳过等高破坏操作仅一处全局入口
   不旁挂到每节点（避免误导用户可跳过 / 部分操作）

4. 仪式感 vs 克制对偶
   成功 / 完成态可显式增强（如绿色对勾 + 激励文案 + 关键 CTA）
   失败 / 中间态保持克制（仅必要信息 + 兜底 / 重试入口）

违反 → Supervisor §X 复审段 WARN 档（非阻断,提示精化）
```

---

## 7. 优化 F — L2 升级批次窗口 + SSOT 单源约束 ✅ 已落地（SSOT #59，2026-05-30）

**根因背景**：SSOT#41 骨架屏 4 轮单 commit 升级（issue #30 WE-A → #31 WE-E → #32 WE-G/H → #33 精简）触发 L1 4 轮 v1.3→v1.6 重 assemble；issue #58 PAD/tablet 规则 SSOT 多源分散致 PM 多源抄引。

**上游文件**：`pm-workflow/skills/workflow-evolution/SKILL.md` + `pm-workflow/rules/ssot_anchors.md`

**插入条款草稿**：

```markdown
### §X.X L2 重大架构升级批次窗口 [Recommended]

L2 框架重大架构升级（涉及 ssot_anchors / proto_*.md / scaffold schema）建议：

1. 批次基线锁定
   相关 commit 在上游连续完成后,先锁定批次基线
   （如 WE-A~WE-Z 系列一并落盘）

2. 批次窗口同步 L1
   避免 L2 单 commit 频繁触发 L1 落盘
   （如 SSOT#41 4 轮单 commit 触发 L1 4 轮 v1.3-v1.6 重 assemble）
   建议批次窗口 = 同 SSOT 锚号下的 commit 序列一并落 L1

### §X.X L2 SSOT 单源约束 [Must]

同一规则（如 PAD/tablet 横向 / 同手机帧豁免 / mermaid direction 规则）
必须明示 SSOT 真源文件,其他文件 [Must] 只能引用不得抄写：

引用格式：
  `详见 pm-workflow/rules/proto_platform_app.md §三（SSOT 真源）`

PM 写 spec/prd 时若引用该规则,只能 grep SSOT 真源行号引用,
不得抄写规则正文（issue #58 同型根因）

ssot_anchors.md 维护 SSOT 真源登记表,
每条 SSOT 锚附:
  - 真源文件路径 + 锚行号
  - 派生引用方清单（grep 反向检查派生方是否抄写而非引用）
```

---

## 8. 上游处理优先级建议

| 优先级 | 编号 | 预估上游工作量 | 影响面 |
|------|------|------------|------|
| P0 | G.1+G.2+G.3+G.4 | 大（涉 5 个 L2 文件 + Supervisor 核查规则）| 全 PM/Supervisor 派发链路 |
| P0 | A | 中（precheck_stage4.py 加 4 个 check 函数 + 配套 test）| 阶段 4 终审稳定性 |
| P0 | B | 小（AI产品经理_Agent.md 加 1 段三项自检）| PM 评估 / 推荐流程 |
| P1 | C | 小（tmpl_需求分析.md 加 4 项自检 + Agent 阶段 1 段）| 阶段 1 PM 派发 |
| P1 | D | 小（2 个 proto_ 文件加 1 段 4 项克制原则）| PM 实施 spec/prd |
| P2 | F | 中（SKILL.md 加批次窗口 + ssot_anchors.md 加单源约束）| L2 演进自纪律 |
| P3 | G.5 | 小（3 个 precheck 加正则扫描 [Recommended]）| 可选机械兜底 |

---

## 9. 配套示范案例（待用户上游 L2 改完后回流执行）

按 G.2 三分类处理已落地的"残留"作为示范案例（推迟到上游 L2 改完后由编排器派 PM 执行）：

| 残留位置 | 分类 | 处理路径 |
|---------|------|---------|
| 阶段 1 M1-13 line 67 "资源回收范围预览" | ② PM 推导粒度污染 | c1 清回业务粒度 |
| 阶段 2 mermaid line 255 / 380 "+ 资源回收范围预览" | ② PM 推导粒度污染 | c1 清回 mermaid label |
| 阶段 3 §744 / spec line 1130/1182/1183/1184/1185/1187 | 待 PM Explore 分类 | 按三分类逐位处理 |

---

## 10. 本次复盘未覆盖项 / 待后续讨论

- 跨层耦合识别（业务逻辑反向影响 UI / Schema 调整影响业务）— 用户暂未答复,留待后续
- G.2 是否增设"产品总监决策回退 UI"作独立合法承载类（区别于客户原始诉求）— 用户暂未答复,留待后续
- 关键词候选清单（G.5 [Recommended]）需上游补完精确正则集

---

## 11. 撤回项记录（思路演进留痕）

复盘过程中产品总监两次深度反驳后撤回的方案：

### 撤回 E — 决策落地后"反向残留扫描"
- 撤回原因：与 CLAUDE.md 第二步范围评估 [Must] 重复造轮子
- 用户实证：CLAUDE.md:158/164/276 三处已明示

### 撤回 E' — 范围评估"机械 grep 关键词反证"
- 撤回原因：机械 grep 不分粒度污染 vs 真业务残留,会把两者混在一起处理
- 用户实证："逻辑只能正向反向不一定成立 — 阶段 1 含某 UI 字面 ≠ 该处属底层逻辑"
- 替代方案：升级为方案 G（含分层判定 + 上游粒度污染反查三分类）

---

## 12. 后续动作

1. **用户上游处理**：按 §8 优先级顺序在 `pm-group/claude-code-pm-workflow` 走 `workflow-evolution` skill 8 步流程修订 L2 文件
2. **上游 commit → 本仓 sync 后**：编排器派 PM Agent 按 §9 示范案例对 issue #66/#67 已落地的"残留"逐位走 G.2 三分类处理（作为新规则首次实战验证）
3. **issue 文件标记**：本报告输出完毕后,编排器执行 `/retro` 第 5b 步将 `process_record/issues/2026-05-14_0302.md` 重命名为 `_analyzed.md` + 内顶部状态字段改为"已分析"+ 添加"分析时间：2026-05-29"（待用户裁决）

---

**报告完毕。**
