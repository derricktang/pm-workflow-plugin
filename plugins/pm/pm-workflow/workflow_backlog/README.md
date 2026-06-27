# workflow_backlog/ — 工作流升级 backlog 归档

> **目录用途**：归档下游仓 PM 通过 `/retro` 复盘产生的「上游处理用」工作流优化建议汇总报告，作为 L2 升级 backlog 留档。**单独存放** + **不立即实施** + **按优先级分批通过 `workflow-evolution` skill 逐项落地**。
>
> **为什么独立目录**：
> - 与 `process_record/` 隔离（process_record/ 是下游 L1 产物，本仓为 L2 框架仓不含 L1）
> - 与 `issues/` 隔离（`process_record/issues/` 仅承载产品总监对成果文件的修改意见，不属下游 PM 复盘产物）
> - 与 `nb_log.md` 隔离（NB 记账是 SSOT 真源债，本目录是改进建议 backlog）

## 命名规范

```
YYYY-MM-DD_{source}_{summary}.md
```

- `source` ∈ {retro / downstream-pm / supervisor-review / etc.}
- `summary` 用 kebab-case 简述（如 `optimization-from-downstream` / `precheck-extension-batch`）

## 当前 backlog 清单

| 文件 | 来源 | 内容 | 状态 |
|---|---|---|---|
| [2026-05-29_retro_optimization_from_downstream.md](2026-05-29_retro_optimization_from_downstream.md) | 下游 quotation-tool `/retro` 复盘（68 条 / 全周期 v1.0~v7.0+CR-28）| 7 共性根因 + 6 方案（G/A/B/C/D/F）| **G ✅ 已落地**（SSOT #54，commit fc3cae3/26cf1c2/3d73cb6/b09394e/aef2f59）<br>**A ✅ 已落地**（SSOT #55，commit 64d4171/828222d + C3/C4）<br>**B ✅ 已落地**（SSOT #56，commit 79815fb + 4 仓 sync 完成）<br>**C ✅ 已落地**（SSOT #57，commit 41a9ef4/4eee963 + 4 仓 sync 完成）<br>**D ✅ 已落地**（SSOT #58，commit c58da67 + 4 仓 sync 完成）<br>**F ✅ 已落地**（SSOT #59，commit 待 C1/C2 + 4 仓 sync）<br>**🎉 retro backlog 6 方案全部完成（G/A/B/C/D/F）**|

## 处理 SOP（每条 backlog 走 workflow-evolution skill）

按 [`pm-workflow/skills/workflow-evolution/SKILL.md`](../skills/workflow-evolution/SKILL.md) 8 步流程，每条 backlog 处理：

1. **选定优先级**：按 ROI 选 1-2 个方案启动（如 retro 文件 G+A 是 [Must]，优先于 D+F）
2. **评估覆盖度**：检查本会话 / 历史已实施 L2 升级是否已部分覆盖（如 retro 方案 B 部分被 fb-design-query skill 覆盖 ~30%）
3. **设计定稿**：按 workflow-evolution skill 走完整设计阶段 + 用户 review
4. **L2 落盘**：Phase 2-3 commit 切分 + 4 仓 sync
5. **归档**：实施完成的方案在 backlog 文件内标 ✅，本 README 状态更新
6. **未实施部分继续保留**：直到全部 6 方案处理完毕或 backlog 文件标 `[Closed]`

## 与本会话已实施 L2 升级的边界

本会话已落地的 L2 升级（commit 链）：
- `7281bc8` logic-only 模块（SSOT #50）
- `4c0fc1b` 文档幻觉修订
- `a5102db` logic-only 派生链路 5 缺陷
- `4165d81` S4-28 inline 反规避双层兜底
- `a6a8932` S4-28 v3 .fb-action-bar CSS 变量继承
- `d75d334` fb-design-query skill（SSOT #52）
- `7f369a5/6aad3e9/70d7fe9/d753b4e` navbar v2 7 variant + S4-28 R2（SSOT #53）

与 retro 6 方案**正交**（~15-20% 覆盖度）— 不重叠，可独立推进。

## 反 pattern（禁止）

- ❌ 把 backlog 文件放在仓库根目录（污染 ls 显示 + 与本仓主体内容混淆）
- ❌ 把下游 PM 复盘产物放进 `issues/`（违反 issues/ 语义边界硬约束）
- ❌ 立即一次性实施所有方案（耗时长 + 跨多重 L2 改动风险高）
- ❌ 实施前不评估与历史 L2 升级的覆盖度（重复工作）
