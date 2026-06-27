"""pytest 共享 fixtures — 阶段 4 / 阶段 3 precheck 测试基建。

用法：
    cd pm-workflow/scripts && pytest

设计原则：
- 不读真实 outputs/ 目录；所有产物用 tmp_path 创建临时文件
- 不依赖网络 / CI；标准库 + pytest，零外部依赖
- fixture 提供"最小合法产物"作为基线，测试用例按需增量改写后传入被测函数
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ── sys.path 注入：让 tests/ 可以 import precheck_stage* ────────────────────────
# pytest 从 pm-workflow/scripts/ 运行（pytest.ini testpaths=tests），
# scripts/ 自身不在默认 sys.path 中（只有 tests/ 目录在）；这里手动注入。
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ── 通用 fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def fake_scaffold_v2() -> dict:
    """返回最小可用的 v2.0 schema scaffold dict（1 模块 / 1 页面 / 1 状态）。

    用例可在 fixture 返回后增量改写（深拷贝再改）：
        import copy
        s = copy.deepcopy(fake_scaffold_v2)
        s["modules"][0]["pages"][0]["states"].append({...})
    """
    return {
        "schema_version": "v2.0",
        "product": "测试产品",
        "platforms": ["桌面Web"],
        "version": "v1.0",
        "description": "用于 pytest 的最小 scaffold 实例",
        "status": "草稿",
        "changelog": [
            {
                "version": "v1.0",
                "date": "2026-05-05",
                "author": "test",
                "desc": "init",
            }
        ],
        "modules": [
            {
                "id": "M01",
                "name": "测试模块",
                "task_card": "process_record/tasks/task_M01_测试模块.md",
                "depends_on": [],
                "candidate_components": {"pub": [], "proj_gaps": []},
                "owner_assignments": {},
                "pages": [
                    {
                        "id": "P01",
                        "name": "测试页面",
                        "spec_id": "spec-M01-P01",
                        "route": "/test",
                        "states": [
                            {
                                "name": "default",
                                "prd_id": "H-M01-P01-default",
                                "roles": ["普通用户"],
                            },
                            {
                                "name": "loading",
                                "prd_id": "H-M01-P01-loading",
                                "roles": ["普通用户"],
                            },
                            {
                                "name": "error",
                                "prd_id": "H-M01-P01-error",
                                "roles": ["普通用户"],
                            },
                        ],
                    }
                ],
            }
        ],
    }


@pytest.fixture
def tmp_outputs_dir(tmp_path: Path) -> Path:
    """pytest 内置 tmp_path fixture 的封装；创建临时 outputs/ 目录。

    用例可在该目录下写入临时 prd / spec 文件，测试结束后由 pytest 自动清理。
    """
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    return outputs


@pytest.fixture
def sample_prd_html_minimal() -> str:
    """最小合法 PRD HTML 片段（含 proto-section + frame-card + interaction-card 同级结构）。

    用于 check_section_nesting / check_prd / check_state_coverage 等函数的输入。
    覆盖：合法嵌套（issue #3/#4 PASS 路径）。
    """
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head><title>Test PRD</title><style>.demo {}</style></head>
<body>
<section id="cover-page" class="cover-page">
  <h1>测试封面</h1>
</section>
<section id="spec-background"><p>背景</p></section>
<section id="spec-persona"><p>画像</p></section>
<section id="spec-permission"><p>权限</p></section>
<section id="spec-journey"><p>旅程</p></section>
<section id="spec-business-flow"><p>业务流程图</p></section>
<section id="spec-feature"><p>功能</p></section>
<section id="spec-data"><p>数据</p></section>
<section id="spec-exception"><p>异常</p></section>
<section id="spec-nonfunc"><p>非功能</p></section>
<section id="H-M01-P01-default" class="proto-section">
  <div class="section-header"><h2>默认态</h2></div>
  <div class="frame-card">
    <div class="frame-wrapper">
      <div class="phone-frame">默认内容</div>
    </div>
  </div>
  <div class="interaction-card">
    <table><tr><th>触点</th></tr><tr><td>M01-P01-T01</td></tr></table>
  </div>
</section>
</body>
</html>
"""


@pytest.fixture
def sample_spec_md_minimal() -> str:
    """最小合法 spec.md 内容（含 S0 / 全量页面清单 / 跳转关系总表 / 模块 M01 / 尾部章节）。"""
    return """# 测试产品 spec

## S0 文档元信息
产品：测试产品

## S0.5 全局上下文

### 全量页面清单

| 页面 ID | 页面名 | 路由 |
|---------|-------|------|
| spec-M01-P01 | 测试页面 | /test |

### 跳转关系总表

| 起点 | 终点 | 触发 |
|-----|-----|-----|
| - | - | - |

## S1 全局背景

## S2.M01 测试模块

### S2.M01.1 业务说明
H-M01-P01-default 默认态。

## 变更记录

| 版本 | 日期 | 作者 | 说明 |
|-----|------|-----|------|
| v1.0 | 2026-05-05 | test | init |

## 非阻塞性问题清单

无。
"""


@pytest.fixture
def sample_产品定义_md_minimal() -> str:
    """最小合法产品定义 md 内容（含 §0–§18 + §5.5 业务流程图 + 变更日志 + Tier 2 FMT-1~6 段落）。

    主要用于 precheck_stage3 测试；只覆盖被测试用例需要校验的章节。
    完整模板见 pm-workflow/rules/tmpl_产品定义.md。
    """
    return """# 测试产品 产品定义

## 0. 文档导读

| Agent | 必读章节 | 可跳过章节 | 核心任务 |
|-------|---------|-----------|---------|
| PM    | 全部     | 无         | 起草    |

## 1. 问题陈述

**谁有这个问题？**

普通用户。

**问题是什么？**

测试问题。

**为什么痛？**

测试痛点。

**用户证据**

用户访谈。

## 2. 战略背景

**业务目标关联**

关联 OKR：测试目标。

**为什么是现在**

现在做。

## 3. 用户画像

### 角色一：普通用户

- **角色 ID**：[`role-1`]
- **角色名**：[普通用户]

| 属性 | 描述 |
|-----|------|
| 典型用户 | 测试用户 |
| 核心诉求 | 测试 |
| 使用场景 | 测试 |
| 关键痛点 | 测试 |
| Jobs-to-be-done | 测试 |

## 4. 权限矩阵

| 功能点 | 普通用户 |
|-------|---------|
| 测试   | ✅      |

## 5. 用户旅程

| 序号 | 阶段名 | 用户行为 | 涉及页面 | 触点 | 痛点 | 期望 | 系统响应 | 异常 / 边界 |
|-----|-------|---------|---------|-----|------|------|---------|----------|
| 1   | 进入  | 打开    | P01    | T01 | 慢  | 快   | 加载页面 | 网络异常  |

`[Should]` 多旅程产品组织规则

无（单旅程产品）。

## 5.5 业务流程图

```mermaid
flowchart TD
    Start([入口]) --> A[操作]
    A --> End([终态])
```

## 6. 页面路由

| 页面 ID | 页面名称 | 路由地址 | 父页面 | 对应功能 | 访问权限 | 类型 | 对客 |
|---------|---------|---------|-------|---------|---------|------|------|
| P01     | 测试页面 | /test   | -    | F-001   | 公开    | 主页 | 是   |

`[Should]` 复杂跳转用 Mermaid 补充

无。

## 6.5 产品架构（来源：阶段 2 §三）

> SSOT 派生约束：复述自阶段 2 §三。

| 模块 | 名称 | 职责（一句话） | 依赖于（模块 + 原因）|
|------|------|---------------|---------------------|
| M1 | 测试模块一 | 负责测试功能 | 无 |
| M2 | 测试模块二 | 负责辅助功能 | M1：读测试数据 |

## 7. 功能需求

`[Must]` 交互说明表元素最小集

包含表单字段 / 操作按钮 / 成功反馈 / 异常态。

`[Must]` 业务规则格式约束

数据规模/数据来源用表格。

`[Must]` 验收场景选取标准

四类穷举（正常 / 枚举 / 约束 / 异常）。

### F-001：测试功能

```gherkin
Given 用户登录
When 点击按钮
Then 显示成功
```

## 8. 状态流转

```mermaid
flowchart LR
A --> B
```

| 当前状态 | 触发条件 | 目标状态 | 操作权限 | 不可逆说明 |
|---------|---------|---------|---------|-----------|
| 草稿    | 提交    | 待审    | 用户    | 否        |

## 9. 数据字段说明

| 字段 | 业务含义 | 约束 / 说明 | 数据来源 |
|-----|---------|-----------|---------|
| id  | 主键    | required  | DB      |

## 10. 接口需求说明

| 接口 ID | 对应功能 | 业务能力描述 | 输入（业务语言） | 输出（业务语言） | 关键业务约束 |
|---------|---------|-------------|---------------|---------------|------------|
| API-001 | F-001   | 提交        | 数据          | 结果          | 必填        |

## 11. 异常处理全景

| 场景类型 | 具体场景 | 触发条件 | 用户反馈（界面表现） | 系统处理逻辑 |
|---------|---------|---------|------------------|------------|
| 网络    | 断网    | 提交时  | toast 提示       | 重试        |

## 12. 数据埋点需求

| 埋点 ID | 触发时机 | 记录内容 | 用途 |
|---------|---------|---------|------|
| EVT-01  | 点击    | 字段    | 分析  |

## 13. 非功能需求

`[Must]` 体验意图填写格式

格式 [业务角色] 在 [触发场景] 时 [遭遇的具体问题]，导致 [可量化的业务后果]。

❌ 反例（抽象，无可执行性）

| 反例 | 正例 |
|-----|------|
| 慢   | 用户在提交时遇到加载超过 3s，导致 30% 用户放弃，次日留存下降 ~10% |

| 指标 | 目标值 | 测量条件 | 体验意图（PM 填：不达标时用户会遇到什么问题） |
|-----|-------|---------|-------------------------------------|
| 响应 | <2s   | 99%请求 | 用户在提交时遇到延迟，导致放弃率上升 20%      |

### 兼容性

iOS 12+ / Android 8+。

## 14. 技术实现建议

（⚙️ 开发 Agent 自动生成，PM 不填）

## 15. 测试数据准备

| 对应场景 | 所需前置数据 | 准备方式 | 准备责任方 |
|---------|------------|---------|----------|
| 测试    | 数据       | 手工    | QA       |

## 16. 待解决问题

| # | 问题描述 | 影响范围 | 负责人 | 截止日期 | 状态 |
|---|---------|---------|-------|---------|------|
| 1 | 无      | 无      | -    | -      | 关闭  |

## 17. 依赖与风险

| 类型 | 描述 | 影响范围 | 当前状态 | 应对措施 |
|-----|------|---------|---------|---------|
| 系统 | -    | -       | -       | -       |

## 18. 里程碑

| 节点 | 计划日期 | 交付内容 | 负责方 |
|-----|---------|---------|-------|
| MS1 | 2026-06 | v1.0    | PM    |

## 变更日志

| 版本 | 变更内容 | 变更原因 | 变更人 | 审核人 | 日期 |
|------|---------|---------|--------|--------|------|
| v1.0 | init    | 初稿    | PM Agent |       | 2026-05-05 |
"""


@pytest.fixture
def make_prd_with_violation():
    """工厂 fixture：返回一个 callable，按 violation 类型生成对应的 PRD HTML 片段。

    用法：
        prd_html = make_prd_with_violation("section_header_in_frame_card")
    """

    templates = {
        "section_header_in_frame_card": """<section id="H-M01-P01-default" class="proto-section">
  <div class="frame-card">
    <div class="section-header"><h2>不应该在这里</h2></div>
    <div class="frame-wrapper">内容</div>
  </div>
</section>
""",
        "interaction_card_in_frame_card": """<section id="H-M01-P02-default" class="proto-section">
  <div class="section-header"><h2>头部</h2></div>
  <div class="frame-card">
    <div class="frame-wrapper">内容</div>
    <div class="interaction-card">不应该在这里</div>
  </div>
</section>
""",
        "interaction_card_deep_nested": """<section id="H-M01-P03-default" class="proto-section">
  <div class="section-header"><h2>头部</h2></div>
  <div class="frame-card">
    <div class="frame-wrapper">
      <div class="some-wrapper">
        <div class="interaction-card">深层嵌套也不行</div>
      </div>
    </div>
  </div>
</section>
""",
        "no_proto_section": """<section id="cover-page" class="cover-page">
  <div class="frame-card">
    <div class="section-header">封面区不约束</div>
  </div>
</section>
""",
    }

    def _make(violation_type: str) -> str:
        if violation_type not in templates:
            raise ValueError(f"unknown violation type: {violation_type}")
        return templates[violation_type]

    return _make
