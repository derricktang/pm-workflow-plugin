# 原型生成策略决策记录 — 2026-04-27

> ⚠️ **2026-05-15 前提作废声明**：本文件围绕"fb-fallback CSS vs React+TDesign"的方向决策**已有结论且前提作废**。最终结论：PRD 原生 HTML 无法引入框架组件库（需构建工具，与 PRD 自包含静态 HTML 不兼容）；pub 库定为**原生 CSS（fb-fallback 体系）单库内建兜底**，正式库接入为后续 skill/CLI（详 `workflow_architecture_map.md §六`）。下方全部 React/TDesign PoC、4 方案对比、多端子方案、时间消耗内容**保留备查，不作为现行方向**。详 memory `component_library_architecture` / `pub_library_distribution_decision` + `workflow_architecture_map.md §六`。

> ⚠️ **2026-05-31 过期项数作废声明（L2 矛盾审计 #9 修复）**：本文件提及的 `precheck_stage4.py` 项数（如 "20 项检查"，L19/L196）**与现状严重不符** — 截至 2026-05-31 该脚本含 **49 个 check_ 函数**（脚本动态计数 `grep -c "^def check_"`），由 S4-30~S4-39 累计新增。本文件作为会话历史档案保留备查不持续维护（参 `pm-workflow/nb_log.md:5` 定位），新维护者请以脚本实际计数为准，**勿信此文中任何 precheck 数字**。

> **本文件定位**：记录"PM 阶段 4 原型生成路线"的方向决策点。当前两套方案并存（fb-fallback CSS 路线已落地 + React+TDesign PoC 已验证），需要后续决策走哪条路。
>
> **恢复阅读顺序**：① 当前状态快照 → ② 待决策核心问题 → ③ 多端方案对比 → ④ PoC 实证 → ⑤ 时间消耗 → ⑥ 决策建议

---

## 一、当前状态快照（决策时点）

### 已落地（fb-fallback.css 路线）

- **vendored mini-CSS 库**：`pm-workflow/rules/bujue-design-system/fb-fallback.css`，414 行，26 个 `fb-*` class 系列
- **pub 组件索引**：`pm-workflow/rules/bujue-design-system/pub_components_index.md`，含分类总览 + 业务场景反查 + D1-D5 能力反查 + 变更历史
- **proj 组件协议**：`pm-workflow/rules/proj_component_protocol.md`，含 §一双触发因素 + §二.1 索引段 + §二.2 详情段 + §三状态枚举强制清单
- **全工作流 9 个文件适配**：CLAUDE.md / agent_methodology.md（不动）/ agent_parameters.md / AI产品经理_Agent.md / AI产品主管_Agent.md / task_card_template.md / prd_expression_standard.md / proto_spec_md.md / rule_hard_constraints.md
- **precheck 机械保障**：`pm-workflow/scripts/precheck_stage4.py`，20 项检查，含 S4-23 PRD fb-* class 全部已登记核查
- **当前回归状态**：19 OK / 0 FAIL / 1 WARN（旧 components_反馈页_latest.md 兼容性提示）

### 已验证（React + TDesign PoC，目录已清理）

- **位置**：~~`poc-react-prototype/`~~（**2026-04-28 已删除**，占用 334MB；如需重做参见下方"PoC 重建步骤"）
- **技术栈**：vite v8 + react 19 + typescript（strict）+ tdesign-react
- **演示内容**：用户卡片（Avatar + Badge）+ 商品列表（Card + Tag + Button）+ 反馈表单（Input + Textarea + Button）
- **mock 数据形态**：`src/data/mock.ts` 直接 `import` 渲染，不走接口
- **验证结论**：
  - `npm run build` 成功，输出 `dist/`（HTML 0.46KB + CSS 99KB + JS 336KB；gzip 后 0.3 + 11.7 + 106KB）
  - `npm run dev` 跑通，浏览器访问 `http://localhost:5173/` 正常渲染
  - TS strict 模式编译过
  - 用户实测视觉、交互、状态切换、表单提交全部正常
- **意义**：技术风险已清零，方案 C+（PM 写示例数据 + 真实组件库渲染）可行

#### PoC 重建步骤（如未来重启该路线）

```bash
npm create vite@latest poc-react-prototype -- --template react-ts
cd poc-react-prototype && npm install tdesign-react && npm install
# 在 src/ 下放入用户卡片 / 商品列表 / 反馈表单三段示例 + src/data/mock.ts
npm run dev   # 浏览器访问 http://localhost:5173/
```

---

## 二、待决策的核心问题

### Q1：要不要从 fb-fallback 路线迁到 React + TDesign 路线？

#### 用户提出的核心动机

- 不要重复造轮子，提升原型生成效率
- 后续公司开发提供的组件库会参考 TDesign / Ant Design，不会是 fb-fallback 这种 mini-CSS 形态
- 直接用 React + TDesign：① 不影响开发现有架构习惯 ② 无缝对接市面成熟组件库

#### 4 个候选方案

| 方案 | 思路 | 改造代价 | 主要权衡 |
|------|------|---------|---------|
| **A：保留 fb-，加映射手册** | PM 仍写 fb-*；新建 `fb-to-vendor-mapping.md`：每个 fb-* 列出 TDesign / Ant Design / 自研库的等价 class | 1-2 小时，仅加文档 | 还是绕一层；本质是给当前架构打补丁 |
| **B：抽象为业务语义契约 + 项目级映射** | PRD 中写 `data-component="primary-button"`；项目首期声明映射到哪个组件库；拼装时按映射表注入实际 class | 半天，需改 PRD 模板 + 拼装脚本 + precheck | 学习成本高；得为每个组件库写完整映射 |
| **C：自定义 JSON + 自研渲染器** | PM 写 JSON 描述结构 / props / state；自研渲染器读 JSON → 调用 TDesign 渲染 | 7-9 周 | 渲染器持续维护；JSON Schema 设计成本 |
| **C+：PM 写真实 React 代码 + mock data**（**用户最终选定方向**）| PM/AI 直接写 React JSX + mock.ts；vite + tdesign-react；vite build 输出静态 HTML | 5-6 周 | 砍掉自研中间层；学习曲线低（AI 见过海量 React 代码）；PRD 自包含可发 |

**用户最终倾向**：C+。已通过 PoC 实证可行性。

---

### Q2：方案 C+ 的多端怎么处理？（**当前讨论的最后停留点**）

#### 多端组件库的天然分裂

| 端 | TDesign 包 | Ant Design 包 | 写法 |
|----|------------|--------------|------|
| Web 桌面 | `tdesign-react` / `tdesign-vue-next` | `antd` | React/Vue |
| Mobile H5 | `tdesign-mobile-react` / `tdesign-mobile-vue` | `antd-mobile` | React/Vue（API 与 Web 版不同）|
| 小程序 | `tdesign-miniprogram` | `ant-design-mini` | **原生小程序 WXML/WXSS**（不是 React/Vue）|

**核心问题**：同一个"按钮"在三端写法不同，**不能复用代码，只能复用 mock data**。

#### 4 个子方案

| 子方案 | 思路 | 一产品线写几份代码 | 视觉真实度 | 学习成本 |
|------|------|-----------------|----------|---------|
| **A：每端独立 React 项目** | `shopping-mall/web` + `shopping-mall/mobile` + `shopping-mall/miniprogram` 各独立项目，共享 `shared/mock.ts` | 每端 1 份 = 2-3 份 | 100% | 低，但工作量翻倍 |
| **B：Taro 一套代码三端编译** | 一份 Taro+React 代码，跑 `taro build --type weapp/h5/web` 出三端原型 | 1 份 | 90%（Taro 抽象会漏底）| 高，第一次有坑 |
| **C：只做 Web + Mobile H5（同 React 项目）** | 一个项目，按路由 `/web/*` 和 `/mobile/*` 切，分别用 tdesign-react 和 tdesign-mobile-react；小程序仅截图占位 | 2 份 | Web 100% / Mobile 100% / 小程序 0% | 低 |
| **D：Web 响应式模拟移动端** | 一份 tdesign-react 代码，用媒体查询 + 设备模拟器看手机视图 | 1 份 | Web 100% / Mobile 60% / 小程序 0% | 极低 |

#### 我的推荐（待用户确认）

**分两步走**：

1. **第一步：方案 C**（Web + Mobile H5 同项目）做 1-2 个产品线
   - 80% 真实场景能覆盖
   - 与今天 PoC 的 React + tdesign-react 结构一致，扩展成本最小
   - 小程序需要时手动做关键页面截图占位

2. **第二步：等遇到第一个真正需要小程序原型的产品线**，再升级到方案 B（Taro）
   - 此时已有几个产品线沉淀，团队对 React + mock 写法熟练
   - Taro 学习曲线陡的部分集中投入 1 周一次性踩平
   - 之前的 React 项目可保留不迁移

**主要权衡：**

- 方案 C 是**确定性短期收益**（与今天 PoC 直接延续，0 学习成本）
- 方案 B 是**长期更优解**（一份代码三端是真正的"全端原型"）
- 一上来就方案 B 风险高（Taro 第一次接入坑多 + TDesign 多端版本协同问题，可能挡住整体迁移节奏 1-2 周）

---

### Q3：用户提出的最后架构

> "一个产品线对应一个 React 项目，再加一层整体的项目说明和导航页面"

#### 推荐目录架构

```
claude-code-pm-workflow/
├── pm-workflow/                  # 工作流框架（保留，但阶段 4 规范要重写）
├── prototypes/                   # ✨ 新增：所有产品原型集合
│   ├── _hub/                     # 顶层导航站（项目说明 + 跳转入口）
│   ├── _template-web/            # ✨ 种子：基于 PoC 改造的 Web 模板
│   ├── _template-mobile/         # ✨ 种子：tdesign-mobile-react 模板（待建）
│   ├── feedback-page/            # 产品线 1（已有的反馈页）
│   │   └── web/                  # 复制自 _template-web
│   ├── shopping-mall/            # 产品线 2
│   │   ├── shared/               # mock data + types（双端共享）
│   │   ├── web/                  # 复制自 _template-web
│   │   └── mobile/               # 复制自 _template-mobile
│   └── admin-console/            # 产品线 3
└── outputs/                      # 阶段 1-3 文档（spec / 产品定义保留 markdown）
```

---

## 三、PoC 项目处置选项

| 选项 | 说明 |
|------|------|
| **A：保留为 _template-web/ 种子**（已失效——目录已删） | ~~把 `poc-react-prototype/` 改名为 `prototypes/_template-web/`~~；如要走此方向，按本文「PoC 重建步骤」重新创建即可 |
| **B：独立保留作为 PoC 实证**（已失效——目录已删） | ~~`poc-react-prototype/` 留着不动~~ |
| **C：直接弃置** | 完全删掉，等正式动手做迁移时重新做 |

**推荐 A**——种子已经写出来了，保留就是直接收益。改名 + 加一份 `_template-web/README.md` 写清"如何基于本模板新建产品原型"，约 20 分钟，立即可用。

---

## 四、走方案 C+ 的时间消耗

| 阶段 | 子任务 | 人天 |
|------|-------|------|
| **Phase 0 PoC** | vite + react + tdesign + mock data 验证 | 0.5（**已完成**）|
| **Phase 1 基础设施** | 模板项目 + lint/typecheck + 状态切换器 + 触点叠加 + 多语言切换器 + assemble.py 改造（调用 vite build）+ precheck 改造（tsc + eslint）+ proj 组件改造（本地 Vue 组件）+ gen_scaffold.py 改造 | 6-8 |
| **Phase 2 规范全面改写** | proto_contract / prd_expression_standard / proj_component_protocol / proto_spec_md / rule_hard_constraints / task_card_template / CLAUDE.md / 经理 + 主管角色规范 / agent_parameters / **pub_components_index 重建（基于 TDesign 文档）** | 8-10 |
| **Phase 3 脚本/回归/文档** | 斜杠命令更新 + 历史项目迁移示范（反馈页 → 新格式）+ 全量回归 + bug 修复 + 使用手册 | 5-6 |
| **小计** | | 19.5-24.5 |
| **+ 30% 风险缓冲** | AI 写代码格式正确性迭代 / TDesign 静态构建可能问题 / 多端整合 / 中途设计调整 | 25.5-32 |

**全量改造：约 5-6 周（1 人全职）**

---

## 五、决策建议（基于产品规模）

| 项目数预期 | 投入产出 |
|-----------|---------|
| **短期 1 个产品** | **不划算**（5-6 周改造 vs 当前 1 周阶段 4），保留当前 fb-fallback 路线 |
| **短期 2-3 个产品** | **临界点**（改造成本约等于 3 个产品的累计阶段 4 时间）|
| **长期 3+ 个产品** | **强烈推荐**（PM 效率 5x，第 4 个项目起开始净赚）|

---

## 六、未决事项 / 恢复时的下一步

恢复阅读时按此顺序处理：

1. **决策 Q1**：是否走 React + TDesign 路线？（如否，本文件归档；如是，进入 2）
2. **决策 Q2**：多端策略选哪个？（推荐分两步：先方案 C，遇到小程序需求时升级方案 B）
3. **决策 PoC 处置**：A/B/C？（推荐 A，改名为 _template-web/）
4. **排迁移路线表**：按 Phase 0/1/2/3 分阶段排日历（5-6 周）
5. **同步更新 HANDOFF.md "待评估开放问题"**：本文件作为问题 3 的延展记录

---

## 七、关键引用与现状文件路径

| 文件 | 用途 |
|------|------|
| ~~`poc-react-prototype/src/App.tsx`~~ | PoC 主代码（用户已浏览验证）—— **目录已于 2026-04-28 删除**；按本文「PoC 重建步骤」可快速复现 |
| ~~`poc-react-prototype/src/data/mock.ts`~~ | mock data 形态示范 —— 同上 |
| `poc-react-prototype/package.json` | 依赖清单（react 19 + tdesign-react + vite 8）|
| `pm-workflow/rules/bujue-design-system/fb-fallback.css` | 当前路线的 vendored CSS（如走 C+ 则废弃）|
| `pm-workflow/rules/bujue-design-system/pub_components_index.md` | 当前路线的组件检索入口（如走 C+ 则需基于 TDesign 文档重建）|
| `pm-workflow/rules/proj_component_protocol.md` | proj 协议（如走 C+ 则 §四 §五 §六 需重写为 Vue/React 组件方式）|
| `pm-workflow/scripts/precheck_stage4.py` | 当前路线的 20 项机械检查（如走 C+ 则改为 tsc + eslint）|

---

## 八、变更记录

| 日期 | 事件 |
|------|------|
| 2026-04-27 上午 | fb-fallback 路线全工作流适配完成（含 pub 索引、9 个文件、20 项 precheck）|
| 2026-04-27 下午 | 用户提出方向疑问 → 讨论 4 方案 → 选定 C+ → 跑 PoC 实证 → 验证可行 → 提出多端方案 → 列时间消耗 → 决定记录待后续考虑 |
