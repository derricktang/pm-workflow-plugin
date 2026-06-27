# pm-workflow/scripts/tests — pytest 最小可用版

> **本目录定位**：把历史会话中"5 测试用例烟测"沉淀为可复用的 pytest 用例，让 PM/Supervisor 整改 precheck 脚本时无需手动重测。
> **建立时间**：2026-05-05（建议 5 实施轮次，PT-1 至 PT-6）。
> **消化的 NB**：NB-IC-EXT-03（IC-EXT 5 用例）+ NB-HC-05（HC-3 5 用例）。

---

## 前置依赖

`pytest` 不在项目根目录的 `requirements.txt` 中（项目当前**无依赖管理文件**）。

**安装方式（任选其一）**：

```bash
# 方式 1：直接 pip 安装到当前环境
pip install pytest

# 方式 2：用 uv 安装为独立工具（不污染 site-packages）
uv tool install pytest
```

无需其他第三方包；测试仅依赖标准库 + pytest。

---

## 运行方式

```bash
cd pm-workflow/scripts && pytest
```

**`pytest.ini` 同级位于 `pm-workflow/scripts/`**——`testpaths = tests` 指向本目录。从其他目录运行 pytest 会找不到配置。

**仅运行单个文件**：

```bash
cd pm-workflow/scripts && pytest tests/test_precheck_stage4.py -v
```

**仅运行单个用例**：

```bash
cd pm-workflow/scripts && pytest tests/test_precheck_stage4.py::TestSectionNesting::test_check_section_nesting_pass -v
```

---

## 用例命名规范

| 元素 | 格式 | 示例 |
|------|------|------|
| 测试文件 | `test_<scriptname>.py` | `test_precheck_stage4.py` |
| 测试类 | `Test<功能/章节>` | `TestSectionNesting` / `TestStateCoverage` |
| 测试函数 | `test_<scriptname>_<feature>_<expectation>` 或 `test_<feature>_<expectation>` | `test_check_section_nesting_pass` / `test_stage3_fail_fmt1_missing_interaction_minset` |

**期望状态命名**：
- `_pass` 后缀：合法输入预期通过
- `_fail_<reason>` 后缀：违规输入预期 fail，明示 fail 原因（便于回溯）

---

## 当前覆盖范围

| 测试文件 | 覆盖脚本 | 覆盖函数 | 用例数 | 历史来源 |
|---------|---------|---------|-------|---------|
| `test_precheck_stage4.py` | `precheck_stage4.py` | `check_section_nesting` + `check_state_coverage` | 13 | IC-EXT 5 + 边界扩展 + S4-05 烟测 |
| `test_precheck_stage3.py` | `precheck_stage3.py` | `check_sections` + `check_section_3/5/7/13` + Tier 2 FMT-1/3/4/6 | 13 | HC-3 5 用例 + 章节增补 |

合计 **26 个 pytest 用例**，覆盖最高复杂度的两个 precheck 脚本。

---

## 共享 fixtures（conftest.py）

| Fixture | 类型 | 用途 |
|---------|-----|------|
| `fake_scaffold_v2` | dict | 最小可用 v2.0 schema scaffold（1 模块 / 1 页面 / 3 状态）|
| `tmp_outputs_dir` | Path | tmp_path 包装的临时 outputs 目录 |
| `sample_prd_html_minimal` | str | 最小合法 PRD HTML（含 proto-section + frame-card + interaction-card 同级合法结构）|
| `sample_spec_md_minimal` | str | 最小合法 spec.md（含 S0/S0.5/M01/变更记录/非阻塞清单）|
| `sample_产品定义_md_minimal` | str | 最小合法产品定义 md（含 §0–§18 + §5.5 业务流程图 + Tier 2 FMT-1~6 全部段落）|
| `make_prd_with_violation` | factory | 工厂函数，返回 4 种违反 issue #3/#4 的 PRD 片段（按 violation 类型）|

---

## 增加新测试指引

**[Recommended] 步骤**：

1. **在 conftest.py 中新增/复用 fixture**：若新测试需要新的输入数据形态，先在 `conftest.py` 加 fixture（避免每个用例自己构造同一数据）；若现有 fixture 可复用（如 `fake_scaffold_v2` + 深拷贝改写），直接 import 使用。

2. **在 `test_<scriptname>.py` 中新增测试类/函数**：
    - 同一被测函数的多个用例放在同一 `Test<X>` 类下
    - 用例名前缀 `test_` + 明示期望（`_pass` / `_fail_<reason>`）
    - 每个用例独立产出 `Report` 对象（不共享）

3. **断言形式**：
   ```python
   r = Report()
   被测函数(输入, r)
   assert r.errors == []  # PASS 用例
   # 或
   assert any("S4-05" in e for e in r.errors)  # FAIL 用例
   ```

4. **示例**（test_precheck_stage4.py 中典型用例）：

   ```python
   def test_check_state_coverage_pass(self, fake_scaffold_v2: dict) -> None:
       """状态枚举包含 default + loading + error → 应 pass。"""
       r = Report()
       check_state_coverage(fake_scaffold_v2, r)
       assert r.errors == [], f"完整三类状态应 PASS,实际错误：{r.errors}"
       assert r.passed >= 1
   ```

5. **运行验证**：
   ```bash
   cd pm-workflow/scripts && pytest tests/test_<scriptname>.py -v
   ```

---

## 渐进迁移路线图

`[Recommended]` 当前覆盖 stage3 + stage4 关键函数；其他脚本按下表渐进迁移：

| 优先级 | 待迁移脚本 | 已有烟测来源 | 工作量预估 | 触发时机 |
|-------|----------|-----------|-----------|---------|
| P1 | `precheck_stage1.py` | HC-1 5 用例（issues/2026-05-06_0032 plan）| 0.5–1 小时 | 下次 stage1 整改时一并完成 |
| P1 | `precheck_stage2.py` | HC-2 5 用例（issues/2026-05-06_0032 plan）| 0.5–1 小时 | 下次 stage2 整改时一并完成 |
| P2 | `precheck_stage4.py` 其他函数 | 各历史轮次零散烟测 | 1–2 小时（按需） | 当某函数发生 ≥ 2 次整改时优先沉淀 |
| P3 | `gen_scaffold.py` | 主要为 schema 校验,有完整 IC-6 烟测 | 1–1.5 小时 | scaffold v2.0 schema 升级时引入 |
| P3 | `assemble.py` | 拼装产物校验，已有手动验证记录 | 1.5–2 小时 | assemble 出现拼装漏洞时补 |
| P4 | `structure_check.py` | 简单脚本，烟测较少 | 0.5 小时 | 低优先级 |

**总工作量**：剩余 5 个脚本完整沉淀约 **5–8 小时**（按部就班，不必一次完成）。

---

## CI/CD 接入（未来计划，非本期范围）

`[Optional]` 未来可考虑的接入点：

1. **本地 git pre-commit hook**：在 `pm-workflow/scripts/` 改动时自动跑 `pytest`
2. **GitHub Actions / GitLab Pipeline**：PR 提交时自动跑全套 pytest
3. **覆盖率报告**：引入 `pytest-cov` 生成覆盖率报告（pytest-cov 是单独依赖，本期未引入）

**本期决策**：仅建立框架 + 最小用例集，**不**接入 CI/CD（避免引入不必要的复杂度；需要时再加）。

---

## 已知限制（NB-PT 系列）

- **NB-PT-01**：测试 ↔ 被测脚本是事实上的 SSOT 双锚（脚本变更须同步更新测试），但本期**未**在 ``pm-workflow/rules/ssot_anchors.md``正式登记。理由：当前用例覆盖率较低（仅 stage3 + stage4 关键函数），登记后会触发"主源改了派生未跟改"的 lint，但实际上现阶段还有大量未覆盖函数，登记会产生大量假报。挂账：当 stage1/2 完成迁移、覆盖率 ≥ 80% 时，再行登记 SSOT 双锚。
- **NB-PT-02**：本期仅引入 pytest 一个依赖；不引入 `pytest-cov`（覆盖率）/ `pytest-xdist`（并行）/ `pytest-mock`（mock 增强）等扩展。理由：最小可用版优先，扩展依赖按需引入。
- **NB-PT-03**：`conftest.py` 中 `sample_产品定义_md_minimal` 是简化版（只覆盖被测试用例需要校验的章节）；不是 `tmpl_产品定义.md` 完整模板的镜像。若 stage3 测试需要校验未覆盖的章节，须扩展 fixture 或新建 fixture。
- **NB-PT-04**：测试假设 pytest 从 `pm-workflow/scripts/` 运行（pytest.ini testpaths 配置）。若用户从项目根目录或其他目录运行 `pytest`，会找不到配置；需要先 `cd pm-workflow/scripts`。

---

## 故障排查

**问题**：`ModuleNotFoundError: No module named 'precheck_stage4'`

**解决**：确认 `conftest.py` 存在且包含 `sys.path.insert(0, str(SCRIPTS_DIR))`；从 `pm-workflow/scripts/` 目录运行 pytest。

**问题**：`pytest: command not found`

**解决**：见上方"前置依赖"章节，安装 pytest。

**问题**：单个测试文件运行可以，但跑 `pytest` 提示找不到 testpaths

**解决**：必须 `cd pm-workflow/scripts && pytest`，pytest.ini 在该目录下。

---

## 历史链路（可追溯性）

| 时间 | 事件 | 文档锚点 |
|-----|------|---------|
| 2026-05-06 IC-EXT 期间 | check_section_nesting 5 用例烟测在对话中执行，挂 NB-IC-EXT-03 | progress/issue_2026-05-06_0032_plan.md L269 |
| 2026-05-06 HC-3 期间 | precheck_stage3 5 用例烟测在对话中执行，挂 NB-HC-05 | progress/issue_2026-05-06_0032_plan.md L439 |
| 2026-05-05 PT-1~6 | 本期 pytest 最小可用版建立，消化两条 NB | progress/issue_2026-05-06_0032_plan.md L516+ |
