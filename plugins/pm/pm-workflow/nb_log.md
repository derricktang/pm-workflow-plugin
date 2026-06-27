# NB 累积台账（L2 工作流维护视图）

> **本文件定位**：L2 维护层文件，集中登记会话产生的 NB-WE-NN 编号（散布在各 `process_record/progress/*` 文件「NB 清单」段 + ssot_anchors.md「缺什么」列 + commit message），便于工作流维护者一键盘点 + 清理 process_record 中可删的 progress 文件。
>
> **路径**：放 `pm-workflow/nb_log.md`（pm-workflow/ 顶层,与 agents/ rules/ scripts/ skills/ 平级）。本台账不限于 rules 范畴,而是工作流整体维护视图（L2）;放 process_record/ 不合适,因后者是产品执行运行时（L1,被 .gitignore 整体忽略）。同目录的 HANDOFF.md / PROTOTYPE_STRATEGY_DECISION.md 是会话历史档案,不持续维护。
>
> **维护规则**：每条 NB 在挂账时由编排器追加一行；处理完成时改"状态"+"处理 commit"；可清理的进度文件只在所有相关 NB 已完成后清理。
>
> **不替代源**：本文件是派生汇总视图,不是真源。NB 详情仍以原 progress 文件 / ssot_anchors.md 为准。

## SSOT 双锚清单总结(34 对)

- **A 组 5/5 完备**:34 对（全部完备）
- **B 组 3-4/5**:0 对（#14 NB-WE-13 commit 后升 A 组）
- **C 组 ≤2/5**:0 对（#22 NB-WE-12 commit 后升 A 组）

🎯 全部 34 对 SSOT 双锚 5/5 完备,架构债清空。

## 已完成 NB（process_record/progress/ 文件可清理）

| 编号 | 标题 | 来源 | 处理 commit | 状态 |
|------|------|------|-------------|------|
| NB-WE-01 | SKILL ↔ template 双锚未登记 SSOT 清单 | progress/workflow_evolution_2026-05-07_2349.md | ebea7e1 | ✅ 升 A 组 #33 |
| NB-WE-02 | sample.md 待加新案例 | progress/workflow_evolution_2026-05-07_2349.md | 195eeb3 | ✅ 加 4 案例 |
| NB-WE-03 | CLAUDE.md 行 232 弱论据"质量未降"待删 | progress/workflow_evolution_2026-05-07_2349.md | 4fe6357 | ✅ 删 + 改为边界陈述 |
| NB-WE-04 | check_scaffold_roles_format 专项测试用例 | progress/workflow_evolution_2026-05-08_0024.md | 76d4d4a | ✅ 加 5 用例 |
| NB-WE-05 | tests/ 偶发删除根因 | progress/workflow_evolution_2026-05-08_0304.md | 4fe6357 | ✅ 已澄清(用户主动删除,非 bug);两次"删除"事件均为用户操作,编排器误判为偶发问题 |
| NB-WE-06 | precheck_stage4 视觉一致性机械化（z-index 集合 / 同状态名 / 同字段格式） | progress/workflow_evolution_2026-05-08_1348.md + progress/workflow_evolution_2026-05-11_1925.md | f164cc5 + (本提交) | ✅ z-index / 同状态名 / 同字段格式 三维度全机械化（NB-WE-10/13 commit 469b5a6/a7e3788 落地）+ 2026-05-11 issue_1925 派生漂移修复:legal_set 8→9 值（追加 Z-150 toast / Z-41 drawer-content）+ 加 `_parse_z_index_truth_source` 运行时反向解析 §零.1 表 + §零.2 协议 + `_check_z_index_legal_set_drift` 双向对账（5 要素第 5 要素机械兜底,根除硬编码漂移面）+ 4 新测试（toast/drawer-content/drift warn/缺失静默） |
| NB-WE-07 | ssot_anchors 加 #32 产品边界跨阶段双锚 | progress/workflow_evolution_2026-05-08_1348.md | 4fe6357 | ✅ 升 A 组 #32 |
| NB-WE-08 | precheck S4-23 应扫 template 真源 | progress/workflow_evolution_2026-05-08_1606.md | 1ff41d4 | ✅ 加 check_prd_template_fb_registration |
| NB-WE-09 | 9 条历史 CSS 漂移清理 | progress/workflow_evolution_2026-05-08_1615.md | 7e6b599 | ✅ 全清 + check_css_sync [PASS] |
| NB-WE-11 | hook L2 模式扩展覆盖 `pm-workflow/*.md` 顶层文件 | progress/workflow_evolution_2026-05-08_2030.md | ad0e437 | ✅ L2_PATTERN 加 `pm-workflow/[^/]+\.md$` 分支,10 路径单元 + 4 端到端测试全过 |
| NB-WE-13 | SSOT #14 状态枚举 ↔ 视觉帧映射机械化（spec 状态名 ↔ scaffold prd_id 后缀字面一致性扫描） | progress/workflow_evolution_2026-05-08_2100.md | a7e3788 | ✅ 加 check_state_naming_convention + check_spec_state_table_count + 10 测试用例,实战 bujue 97 状态全过；#14 升 A 组 5/5 |
| NB-WE-10 | precheck_stage4 视觉一致性机械化剩余 2 维度（同状态名跨帧 + 同字段格式跨页 normalize） | progress/workflow_evolution_2026-05-08_2200.md | 469b5a6 | ✅ 加 check_frame_page_metadata_consistency（维度 A,WARN 级）+ check_field_format_consistency_across_pages（维度 B,WARN 级）+ 8 测试用例。bujue 实测：维度 A 1 处合理差异 + 维度 B 24 处疑似漂移留 PM 人审 |
| NB-WE-12 | rule_hard_constraints 双向引用渐进（每条规则标注"由 precheck 第 X 步检查" + precheck 注释反指真源） | progress/workflow_evolution_2026-05-08_2300.md | (此提交) | ✅ 修正六.X 表 4 条过期"—"为已机械化（S4-04/08/21/22）+ docstring 反指既有；#22 升 A 组 5/5,SSOT 双锚 33 对全部完备（彼时） |
| NB-WE-16 | 嵌套 section 剔除算法（深度计数器替代非贪婪 regex） | progress/workflow_evolution_2026-05-11_0019.md | (此提交) | ✅ 接收下游 PM 修订（场景：proj-component-{name} 状态展示区内嵌套 <section>）；旧 regex `<section...>.*?</section>` 在嵌套场景漏剔（停在第一个 </section>,残留外层按钮）→ 加 `_remove_sections_by_id_prefix` helper 用平衡标签 depth counter；3 测试用例（嵌套 / 多同前缀 / 无目标）；pytest 117 passed |
| NB-WE-17 | 下游 bujue-quotation-tool 3 个 L2 commits 同步 + e898763 派生同步残缺补齐 | progress/workflow_evolution_2026-05-11_0336.md | (此提交) | ✅ git am 应用 3 commits (4c93417 settings.json $schema / e898763 面板浮层规范化 / 5e3f385 §零.2 嵌入帧不可突破原则)；e898763 缺 3 处派生同步（prd_expression_standard .frame-card 缺 isolation:isolate / manifest 顶部 anchor 清单未加 4 行 / manifest §3.4-§3.6 编号冲突 / dispatch_protocol 计数 23→27）→ 4th commit 补齐；pytest 117 + check_css_sync PASS + structure_check anchor 三向一致 27=27=27 |
| NB-阶段4-D | i18n 工具化工作流升级（B+ 档位 — prd_expression_standard §十 触发条件未在 PM Agent 派单模板显式提及导致下游漏写 data-zh/data-en） | progress/workflow_evolution_2026-05-11_1716.md | (此提交) | ✅ 已闭环（2026-05-11）。问题：下游 bujue 项目 PM 在 Step 5 写 8 份 prd_M0X_draft.html 时漏写 §十 i18n 属性,前期用一次性脚本 add_i18n_v2.py（已随 Python/ 清理删除）批量补 prd.html 派生层 → 违反 SSOT 派生原则 + 引发 issue # 10/# 11/# 12（toast/modal/scroll 序列化副作用）。B+ 决策方案：① 新增 `pm-workflow/scripts/add_i18n.py`（extract / inject 双模式 + 13 测试 PASS,regex 替换不动其他位置 byte-level 0 副作用） ② 新增 `pm-workflow/rules/i18n_dict_template.json`（业务术语示例 + 写词规范） ③ `AI产品经理_Agent.md` 阶段 4 Step 5 加条件性触发（多语言产品 → 跑工具,无 → 跳过） ④ `precheck_stage4.py` 加 `check_i18n_minimum`（触发 i18n 但 data-zh = 0 → BLOCK；4 测试 PASS） ⑤ 不动 SSOT 双锚 / 不大改 §十主体。档位：B+ 中量化（vs 档位 C 完整叶子节点对账）;ROI 评分 3.5/4（漂移代价 1 + 历史踩坑 1 + 漂移频率 0.5 + 当前漂移面 1）。pytest 134 PASS（117 → 134,新增 17 用例全过）|
| NB-WE-18 | §零.1 表加 Z-41 行让真源自洽（NB-WE-06 第 5 要素加固后续延伸） | progress/workflow_evolution_2026-05-11_1925.md | (此提交,同会话解决) | ✅ NB-WE-06 第 5 要素加固时发现 Z-41 散落 §零.2 line 99 散文里(`Z-(\d+) drawer 内容` regex 兜底),真源自身不自洽 → 同会话决策同时处理:①§零.1 表加 Z-41 独立行（drawer 内容 / 41 / `.fb-drawer`）+ 拆 Z-40 行（剥离 `.fb-drawer` 到 Z-41,Z-40 改为 modal / drawer 遮罩）+ line 58 集合字面同步含 1（9 值与表 9 行 1:1）；②§零.2 line 99 改为引用 §零.1 表（去隐式兜底）；③`_parse_z_index_truth_source` 简化为单源 regex `^\| Z-(\d+) \|`（去 `drawer 内容` 兜底）；④运行时验证真源解析 `{1,10,40,41,50,60,100,150,200}` 9 值与 legal_set 一致；pytest 138 PASS |
| NB-WE-19 | assemble.py 剥离 autofocus 防御性兜底（下游 # 13 默认显示 M07/P10 漂移） | progress/workflow_evolution_2026-05-12_0026.md | (此提交) | ✅ 下游 PM 在 drafts 误写 `<input autofocus>` → 浏览器加载时触发 scrollIntoView,路过 100+ sticky 元素引发合成层风暴 → 破坏默认显示首帧 + 滚动条闪烁（与 # 14 关联）。真源修在 drafts 删 autofocus（L1）,L2 加 `_strip_autofocus_attributes(html)` helper 在 assemble_prd write 之前剥除,正则 `\s+autofocus(?=[\s>])` 避免误伤 data-autofocus 等；剥除时 print 计数 + 标 NB-WE-19。 |
| NB-WE-20 | `.frame-card { isolation: isolate }` 派生漂移修复 + §零.2 rule-3 机械兜底实装（下游 # 14 滚动条闪烁辅因） | progress/workflow_evolution_2026-05-12_0026.md | (此提交) | ✅ 双层防御。**根因**:`prd_template.html` L343 加 isolation 后,assemble_prd 仅 `prd_path.read_text()` 然后 inject frames,**从不重读 template `<style>` 段** → outputs/prd 派生层 `.frame-card` 规则缺 isolation,frame 内弹框 z-index 溢出到 sticky section-header。**§零.2 rule-3 早已规定 isolation 必备但 precheck_stage4 未实装**(grep "isolation" 计数 = 0),机械层无报警。**修订**:①assemble.py 加 `_overwrite_first_style_from_template(html)` helper — 全量重读 template `<style>` 段覆盖 outputs/prd 同位置（lambda 避免 backreference 误解释；template/outputs 缺 `<style>` → warn 跳过）;②precheck_stage4 加 `check_frame_card_isolation(prd_html, r)` 实装 §零.2 rule-3（无 .frame-card 静默豁免）;③test_precheck_stage4 加 `TestFrameCardIsolation` 3 用例（PASS含 / FAIL缺 / 豁免无）;④主流程 z-index check 同位置调用。pytest 138→141 PASS。**ROI**:3.5/4（漂移代价 1 + 历史踩坑 1 + 漂移频率 0.5 + 漂移面 1）。 |

## 待办 NB

| 编号 | 标题 | 来源 | 优先级 | 备注 |
|------|------|------|--------|------|
| NB-WE-14 | 阶段 4 PM Agent skill 化拆分（superpowers 借鉴 项 3）| 用户 2026-05-10 决策延后,issues/2026-05-10_0442.md ROI 讨论后挂账 | ⭐⭐ | 把 `AI产品经理_Agent.md` 阶段 4 内容（Foundation / 项目组件识别 / 模块 Spec / 模块 PRD / 拼装 / 终审 6 sub-agent 段）抽出为独立 skill `pm-workflow/skills/stage4-delivery/`(SKILL.md + template.md + examples/sample.md),解决单文件 967 行单次 Read 浪费 token 问题。建议分两 commit:先建 skill 保留双份 → 验证一段时间后删旧。工时 ~3-4 h,影响 L1 业务流程,需独立窗口执行。SSOT 双锚 #34 待新建（按 #33 workflow-evolution skill 模式）|

## 进度文件清理状态

> 当 progress/workflow_evolution_*.md 中所有 NB-WE-NN 都进入"已完成 NB"段时,该 progress 文件可删除（commit 历史保留任务详情）。

**2026-05-08 清理执行**：删 11 个已完成 progress 文件,保留 1 个含未完成 NB 的文件。

| progress 文件 | 状态 |
|---------------|------|
| workflow_evolution_2026-05-08_1348.md | ⚠ 保留（含 NB-WE-10 未完成） |
| ~~其他 11 个 progress 文件~~ | ✅ 已删（commit 历史保留详情） |

## issue 清理状态

| issue 文件 | 状态 |
|------------|------|
| process_record/issues/2026-05-08_0024_analyzed.md | ✅ 已改名 + 状态更新「已分析」+ 含 4 条意见处理 commit 引用（eef8cdd / 601c4aa / be5f6b8 / 41953ac）|
