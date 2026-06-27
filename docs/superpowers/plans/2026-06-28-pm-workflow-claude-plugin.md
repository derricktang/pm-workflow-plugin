# PM Workflow → Claude Code 插件 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 pm-workflow 工作流框架（L2）封装成可 `/plugin install` 的 Claude Code 插件，单仓兼作 marketplace，发布到插件市场。

**Architecture:** 核心 `pm-workflow/`（rules/agents/scripts/skills/design-system，厂商中立）+ 薄 Claude 适配壳（commands/ + hooks/ + plugin.json）。框架文件进只读 cache（FRAMEWORK_ROOT），用户产物留项目 cwd（PROJECT_ROOT）。编排大脑 `orchestrator.md` 由仓根 `CLAUDE.md` 锚区生成，经 SessionStart hook 注入主编排器；subagent 拿不到注入，故路径约定经派发任务消息下传。

**Tech Stack:** Markdown（commands/skills/agents/rules）、Python 3（scripts + hooks）、Claude Code 插件清单（plugin.json / marketplace.json / hooks.json）。

**设计真源：** `docs/superpowers/specs/2026-06-28-pm-workflow-claude-plugin-design.md`（rev.3.2）。本计划是其落地。

**执行位置：** 在**发布仓**（原项目或新建 publish 仓）执行，**不在当前副本**。当前副本仅产出本计划与 spec。下文 `<REPO>` = 发布仓根。

## Global Constraints

- **插件名 `pm`**：命名空间 `/pm:<command>`（可全局改名，但全程保持一致）。
- **双根纪律**：框架文件（rules/templates/scripts/design-system）→ `FRAMEWORK_ROOT`（只读）；产物（`outputs/` `process_record/`）→ `PROJECT_ROOT`（读写）。**任何产物路径绝不挂 FRAMEWORK_ROOT。**
- **路径解析**：subagent 从 plain 文件（rules/agent-spec）读到的 `pm-workflow/...`（335 引用 + 98 引用 + 37 行 bash）按**派发任务消息携带的绝对 FRAMEWORK_ROOT** 解析；`${CLAUDE_PLUGIN_ROOT}`（加载时替换，非 env）仅用于 command 正文 / skill / agent 组件内容。
- **编排大脑单一真源**：`CLAUDE.md`（含 ANCHOR 标记）；`orchestrator.md` 为**生成物**，禁手维护。
- **CHANGELOG 单职**：`CHANGELOG.md` 仅 release notes；机构记忆只进 `nb_log.md`。
- **命令清单动态枚举**：不写死命令列表（现有 7 个：newRequirement/nextStage/projectStatus/changeRequest/retro/syncUpstream/investigate）。
- **双模过渡**：保留 `sync_from_upstream.sh`/`install_hooks.sh`/`pre-commit`/`syncUpstream`，README 标 deprecated。
- **频繁提交**：每个 Task 末尾 commit。Python 改动须保持 `pm-workflow/scripts/tests/` pytest 全绿。

---

## File Structure

**新建：**
- `<REPO>/.claude-plugin/marketplace.json` — 市场清单
- `<REPO>/plugins/pm/.claude-plugin/plugin.json` — 插件清单
- `<REPO>/plugins/pm/hooks/hooks.json` — SessionStart 两条 hook
- `<REPO>/plugins/pm/pm-workflow/scripts/pm_paths.py` — 双根 helper（单一真源）
- `<REPO>/plugins/pm/pm-workflow/scripts/gen_orchestrator.py` — 从 CLAUDE.md 锚区生成 orchestrator.md
- `<REPO>/plugins/pm/pm-workflow/scripts/hooks/session_start_inject.py` — 注入 orchestrator.md + 根声明
- `<REPO>/plugins/pm/pm-workflow/core/orchestrator.md` — 生成物（提交入库供插件加载）
- `<REPO>/plugins/pm/pm-workflow/scripts/tests/test_dual_root.py` — 双根红线测试
- `<REPO>/plugins/pm/pm-workflow/scripts/tests/test_orchestrator_sync.py` — 大脑一致性测试
- `<REPO>/README.md`、`<REPO>/CHANGELOG.md`

**搬迁（git mv，保留历史）：**
- `.claude/commands/*.md` → `<REPO>/plugins/pm/commands/`
- `pm-workflow/` 整树 → `<REPO>/plugins/pm/pm-workflow/`
- `CLAUDE.md` → **留 `<REPO>/CLAUDE.md`（仓根）**，不进插件 payload

**修改：**
- 17 个 `pm-workflow/scripts/*.py`（含 `assemble.py` `add_i18n.py` 等）— 改用 `pm_paths`
- `pm-workflow/rules/agent_dispatch_protocol.md` — 加「插件根解析」派发约定
- 4 个 command 正文里的 bash — 改 `${CLAUDE_PLUGIN_ROOT}`
- `CLAUDE.md` — **不改**（上游暂不瘦身；orchestrator.md 由 C2 整文件复制生成）

---

## Phase A — 仓骨架与清单

### Task A1: 建仓结构 + 搬迁核心

**Files:**
- Create dir: `<REPO>/plugins/pm/`
- Move: `pm-workflow/` → `<REPO>/plugins/pm/pm-workflow/`；`.claude/commands/*.md` → `<REPO>/plugins/pm/commands/`
- Keep: `CLAUDE.md` 在 `<REPO>/` 根

- [ ] **Step 1: 初始化发布仓（若新建）**

```bash
cd <REPO> && git init 2>/dev/null; mkdir -p plugins/pm
```

- [ ] **Step 2: 搬迁（用 git mv 保历史；新仓用普通 mv 后 add）**

```bash
git mv pm-workflow plugins/pm/pm-workflow
mkdir -p plugins/pm/commands
git mv .claude/commands/*.md plugins/pm/commands/
```

- [ ] **Step 3: 验证目录树**

Run: `find plugins/pm -maxdepth 2 -type d`
Expected: 含 `plugins/pm/commands`、`plugins/pm/pm-workflow/{agents,rules,scripts,skills,design-system}`

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "chore: scaffold plugin layout (move core + commands under plugins/pm)"
```

### Task A2: plugin.json + marketplace.json

**Files:**
- Create: `<REPO>/plugins/pm/.claude-plugin/plugin.json`
- Create: `<REPO>/.claude-plugin/marketplace.json`

**Interfaces:**
- Produces: 插件名 `pm`；skills 路径 `./pm-workflow/skills/`；marketplace relative source `./plugins/pm`（相对 marketplace 根，即含 `.claude-plugin/` 的 `<REPO>`）

- [ ] **Step 1: 写 plugin.json**

```json
{
  "name": "pm",
  "description": "结构化 AI 产品经理工作流：需求分析→功能规划→产品定义→交付文档，多层审核、可控变更。",
  "version": "1.0.0",
  "author": { "name": "TODO-填发布前" },
  "skills": "./pm-workflow/skills/",
  "commands": "./commands/",
  "hooks": "./hooks/hooks.json"
}
```
> 注：**不写 `agents` 字段**（角色文件无 frontmatter、本工作流派通用 subagent 再 Read 路径，非注册 agent）。**`homepage`/`repository`/`license` 一并省略**——它们是可选字段，且非空时按 URI / SPDX 校验，写 `"TODO"` 占位会**校验失败**（final-review 实测）；发布前填真实值再加。`author.name` 为普通字符串，留占位无妨。

- [ ] **Step 2: 写 marketplace.json**

```json
{
  "name": "pm-workflow-market",
  "displayName": "PM Workflow Marketplace",
  "description": "AI 产品经理工作流插件市场",
  "version": "1.0.0",
  "author": { "name": "TODO" },
  "plugins": [
    {
      "name": "pm",
      "displayName": "PM Workflow",
      "description": "结构化 AI 产品经理工作流",
      "source": "./plugins/pm"
    }
  ]
}
```

- [ ] **Step 3: JSON 合法性校验**

Run: `python3 -c "import json; json.load(open('plugins/pm/.claude-plugin/plugin.json',encoding='utf-8')); json.load(open('.claude-plugin/marketplace.json',encoding='utf-8')); print('JSON OK')"`
Expected: `JSON OK`

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin plugins/pm/.claude-plugin && git commit -m "feat: add plugin.json and marketplace.json (name=pm)"
```

---

## Phase B — 双根改造（P0-1，最高风险）

### Task B1: pm_paths 双根 helper（先建测试）

**Files:**
- Create: `plugins/pm/pm-workflow/scripts/pm_paths.py`
- Test: `plugins/pm/pm-workflow/scripts/tests/test_dual_root.py`

**Interfaces:**
- Produces: `FRAMEWORK_ROOT: Path`（脚本所在框架根 = `parents[2]`）、`PROJECT_ROOT: Path`（`$CLAUDE_PROJECT_DIR` 或 cwd）。git-copy 模式下两者相等（向后兼容）。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_dual_root.py
import os, importlib
from pathlib import Path

def test_framework_root_is_repo_root(monkeypatch):
    import pm_paths; importlib.reload(pm_paths)
    # pm_paths.py 在 <root>/pm-workflow/scripts/ → FRAMEWORK_ROOT 末两级为 pm-workflow/.. 的父
    assert (pm_paths.FRAMEWORK_ROOT / "pm-workflow" / "scripts" / "pm_paths.py").exists()

def test_project_root_uses_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    import pm_paths; importlib.reload(pm_paths)
    assert pm_paths.PROJECT_ROOT == tmp_path.resolve()

def test_project_root_falls_back_to_framework_root(monkeypatch, tmp_path):
    # 无 env 时回退到 FRAMEWORK_ROOT（而非 cwd）——保证 git-copy/测试零回归
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)  # 故意换 cwd，证明不依赖 cwd
    import pm_paths; importlib.reload(pm_paths)
    assert pm_paths.PROJECT_ROOT == pm_paths.FRAMEWORK_ROOT
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd plugins/pm/pm-workflow/scripts && python3 -m pytest tests/test_dual_root.py -v`
Expected: FAIL（`ModuleNotFoundError: pm_paths`）

- [ ] **Step 3: 写 pm_paths.py**

```python
"""双根定位（SSOT）。框架文件用 FRAMEWORK_ROOT（只读），产物用 PROJECT_ROOT（读写）。
插件模式：Claude Code 设 CLAUDE_PROJECT_DIR → PROJECT_ROOT=用户项目；FRAMEWORK_ROOT 在只读 cache。
git-copy / 测试模式：无 CLAUDE_PROJECT_DIR → PROJECT_ROOT 回退到 FRAMEWORK_ROOT（= 旧 REPO_ROOT 行为，零回归）。"""
import os
from pathlib import Path

# 本文件位于 <plugin_root>/pm-workflow/scripts/pm_paths.py → parents[2] = <plugin_root>（含 pm-workflow/ 的目录）
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
# 回退到 FRAMEWORK_ROOT（而非 cwd）：保证无 env 时与旧 REPO_ROOT=__file__ 行为一致，现有测试不破
PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or FRAMEWORK_ROOT).resolve()
```
> **关键**：回退用 `FRAMEWORK_ROOT` 不用 `cwd`——旧代码 `REPO_ROOT=Path(__file__)...parents[2]` 是确定性的；用 cwd 回退会让测试（cwd=scripts）算错根、破坏现有 798 passing。

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_dual_root.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/pm/pm-workflow/scripts/pm_paths.py plugins/pm/pm-workflow/scripts/tests/test_dual_root.py
git commit -m "feat: add pm_paths dual-root helper (FRAMEWORK_ROOT + PROJECT_ROOT)"
```

### Task B2: 迁移 17 脚本到 pm_paths（canonical: assemble.py）

**Files:**
- Modify: `plugins/pm/pm-workflow/scripts/assemble.py:33-40`（及其余 16 脚本同型）

**Interfaces:**
- Consumes: `pm_paths.FRAMEWORK_ROOT` / `pm_paths.PROJECT_ROOT`
- 转换规则（对每个脚本）：产物路径（`outputs/` `process_record/` `versions/` `drafts/` `tasks/`）挂 **PROJECT_ROOT**；框架路径（`pm-workflow/rules/...` 模板/CSS/schema）挂 **FRAMEWORK_ROOT**；删除本地 `REPO_ROOT = Path(__file__)...`。

- [ ] **Step 1: 枚举 17 个待改脚本**

Run: `grep -rl "Path(__file__).resolve().parent" plugins/pm/pm-workflow/scripts/*.py`
Expected: 17 个文件（含 assemble.py / add_i18n.py / gen_scaffold.py / precheck_*.py / check_*.py / structure_check.py 等）

- [ ] **Step 2: 改 canonical 文件 assemble.py（实际编辑）**

把 `assemble.py:33-40` 由：
```python
REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
SCAFFOLD   = REPO_ROOT / "process_record" / "tasks" / "scaffold.json"
DRAFTS_DIR = REPO_ROOT / "process_record" / "drafts"
OUTPUT_DIR = REPO_ROOT / "outputs"
FALLBACK_CSS_PATH = REPO_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "fb-fallback.css"
FINGERPRINT_DIR = REPO_ROOT / "process_record" / "versions" / ".assemble_fingerprints"
BACKUP_DIR = REPO_ROOT / "process_record" / "versions" / ".assemble_backups"
PRD_TEMPLATE_PATH = REPO_ROOT / "pm-workflow" / "rules" / "prd_template.html"
```
改为：
```python
from pm_paths import FRAMEWORK_ROOT, PROJECT_ROOT
# 产物 → PROJECT_ROOT
SCAFFOLD   = PROJECT_ROOT / "process_record" / "tasks" / "scaffold.json"
DRAFTS_DIR = PROJECT_ROOT / "process_record" / "drafts"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FINGERPRINT_DIR = PROJECT_ROOT / "process_record" / "versions" / ".assemble_fingerprints"
BACKUP_DIR = PROJECT_ROOT / "process_record" / "versions" / ".assemble_backups"
# 框架 → FRAMEWORK_ROOT
FALLBACK_CSS_PATH = FRAMEWORK_ROOT / "pm-workflow" / "rules" / "bujue-design-system" / "fb-fallback.css"
PRD_TEMPLATE_PATH = FRAMEWORK_ROOT / "pm-workflow" / "rules" / "prd_template.html"
```
> import 生效前提：脚本以 `scripts/` 为 cwd 运行或同目录 import。若脚本被从他处调用，在文件顶部加：`import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` 再 `from pm_paths import ...`。

- [ ] **Step 3: 对其余 16 个脚本逐一套用同规则**

对 Step 1 列出的每个文件：①找其 `REPO_ROOT = Path(__file__)...` 行；②`grep -n "REPO_ROOT" <file>` 列出所有用法；③产物路径改 PROJECT_ROOT、框架路径改 FRAMEWORK_ROOT、加 `from pm_paths import ...`。逐个文件改完即 `git add` 该文件。

判定口诀：路径含 `outputs`/`process_record`/`versions`/`drafts`/`tasks` → PROJECT_ROOT；含 `pm-workflow/`（模板/规则/CSS/schema/i18n 模板）→ FRAMEWORK_ROOT。

- [ ] **Step 4: 确认无残留裸 REPO_ROOT 定义**

Run: `grep -rn "REPO_ROOT *= *Path(__file__)" plugins/pm/pm-workflow/scripts/*.py`
Expected: 无输出（全部已替换）

- [ ] **Step 5: 跑全量脚本单测**

Run: `cd plugins/pm/pm-workflow/scripts && python3 -m pytest -q`
Expected: 全绿（git-copy 模式下 FRAMEWORK_ROOT==PROJECT_ROOT，行为不变）

- [ ] **Step 6: Commit**

```bash
git add plugins/pm/pm-workflow/scripts/*.py
git commit -m "refactor: 17 scripts use pm_paths dual-root (products→PROJECT_ROOT, framework→FRAMEWORK_ROOT)"
```

### Task B3: 双根红线测试（产物绝不写框架根）

**Files:**
- Modify: `plugins/pm/pm-workflow/scripts/tests/test_dual_root.py`

- [ ] **Step 1: 加红线测试（模拟插件模式：FRAMEWORK ≠ PROJECT）**

```python
def test_products_never_under_framework_root(monkeypatch, tmp_path):
    # 模拟插件模式：项目根另设，框架根=脚本所在。断言产物 dir 落项目根、不在框架根下。
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    import importlib, pm_paths; importlib.reload(pm_paths)
    import assemble; importlib.reload(assemble)
    for d in (assemble.OUTPUT_DIR, assemble.DRAFTS_DIR, assemble.SCAFFOLD.parent):
        assert str(d).startswith(str(tmp_path)), f"{d} 未落 PROJECT_ROOT"
        assert not str(d).startswith(str(pm_paths.FRAMEWORK_ROOT / "pm-workflow")), f"{d} 落在框架根！"
    assert str(assemble.PRD_TEMPLATE_PATH).startswith(str(pm_paths.FRAMEWORK_ROOT))
```

- [ ] **Step 2: 跑测试确认通过**

Run: `python3 -m pytest tests/test_dual_root.py::test_products_never_under_framework_root -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add plugins/pm/pm-workflow/scripts/tests/test_dual_root.py
git commit -m "test: red-line assert products land in PROJECT_ROOT not framework cache"
```

---

## Phase C — 编排大脑生成（上游「不动 CLAUDE.md」版）

### Task C1: ⏭ SKIPPED — 不加锚、不动 CLAUDE.md（上游 2026-06-28 决策）

上游明确暂不瘦身、不动 CLAUDE.md。故**不加 ANCHOR 标记**；`orchestrator.md` = CLAUDE.md 逐字复制（C2 无锚整文件复制路径）。本任务无操作。未来若瘦身，再加锚并启用 C2 的锚提取分支。

### Task C2: gen_orchestrator.py（无锚整文件复制）+ 生成 orchestrator.md

**Files:**
- Create: `plugins/pm/pm-workflow/scripts/gen_orchestrator.py`
- Create (generated): `plugins/pm/pm-workflow/core/orchestrator.md`
- Test: `plugins/pm/pm-workflow/scripts/tests/test_orchestrator_sync.py`

**Interfaces:**
- Consumes: `<REPO>/CLAUDE.md` 锚区
- Produces: `orchestrator.md` = 生成头 + 各锚区拼接 + 一段「插件根声明」占位（运行时由 hook 替换实际根）

- [ ] **Step 1: 写失败测试（生成幂等 + 含锚内容）**

```python
# tests/test_orchestrator_sync.py
import subprocess, sys, pathlib
SCRIPTS = pathlib.Path(__file__).resolve().parents[1]
def test_orchestrator_regenerates_identically(tmp_path):
    out = SCRIPTS.parents[1] / "CLAUDE.md"  # <root>/CLAUDE.md (git-copy) — 见脚本对 --claude-md 的解析
    gen = SCRIPTS / "gen_orchestrator.py"
    r = subprocess.run([sys.executable, str(gen), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, f"orchestrator.md 与 CLAUDE.md 锚区不同步:\n{r.stdout}\n{r.stderr}"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd plugins/pm/pm-workflow/scripts && python3 -m pytest tests/test_orchestrator_sync.py -v`
Expected: FAIL（gen_orchestrator.py 不存在）

- [ ] **Step 3: 写 gen_orchestrator.py**

```python
"""从 CLAUDE.md 的 <!-- ANCHOR:start/end --> 区段生成 core/orchestrator.md。
用法：gen_orchestrator.py            # 生成/覆盖 orchestrator.md
     gen_orchestrator.py --check    # 仅校验已存在副本与重生成是否一致（CI/test 用）"""
import re, sys
from pm_paths import FRAMEWORK_ROOT

# CLAUDE.md：插件布局在仓根（FRAMEWORK_ROOT.parent/.. 视搬迁而定）。优先仓根，回退框架根上一级。
def find_claude_md():
    for cand in (FRAMEWORK_ROOT.parent.parent / "CLAUDE.md",   # <REPO>/CLAUDE.md（plugins/pm/pm-workflow → 上三级=REPO）
                 FRAMEWORK_ROOT / "CLAUDE.md"):                 # git-copy 同级回退
        if cand.exists():
            return cand
    raise SystemExit("找不到 CLAUDE.md")

ANCHOR = re.compile(r"<!-- ANCHOR:start -->(.*?)<!-- ANCHOR:end -->", re.S)
HEADER = ("<!-- GENERATED by gen_orchestrator.py from CLAUDE.md anchors. DO NOT EDIT. -->\n"
          "<!-- 真源 = 仓根 CLAUDE.md 的 ANCHOR 区段；改这里无效，改 CLAUDE.md 后重生成。-->\n\n"
          "# 编排器常驻锚\n\n"
          "> 框架文件位于插件根（运行时由 SessionStart 注入绝对路径）；所有 `pm-workflow/...` "
          "路径相对该根解析；用户产物 `outputs/`、`process_record/` 相对项目 cwd。\n\n")

def build():
    src = find_claude_md().read_text(encoding="utf-8")
    blocks = [m.group(1).strip() for m in ANCHOR.finditer(src)]
    if not blocks:
        # 上游暂不瘦身：无锚 → 整份 CLAUDE.md 逐字复制（当前路径）
        blocks = [src.strip()]
    return HEADER + "\n\n---\n\n".join(blocks) + "\n"

def main():
    target = FRAMEWORK_ROOT / "pm-workflow" / "core" / "orchestrator.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    new = build()
    if "--check" in sys.argv:
        cur = target.read_text(encoding="utf-8") if target.exists() else ""
        if cur != new:
            print("orchestrator.md 过期，请运行 gen_orchestrator.py 重生成")
            sys.exit(1)
        print("orchestrator.md in sync"); return
    target.write_text(new, encoding="utf-8")
    print(f"written {target}")

if __name__ == "__main__":
    import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
```

- [ ] **Step 4: 生成 orchestrator.md**

Run: `cd plugins/pm/pm-workflow/scripts && python3 gen_orchestrator.py`
Expected: `written .../core/orchestrator.md`，且文件非空、含锚区正文

- [ ] **Step 5: 跑一致性测试确认通过**

Run: `python3 -m pytest tests/test_orchestrator_sync.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add plugins/pm/pm-workflow/scripts/gen_orchestrator.py plugins/pm/pm-workflow/core/orchestrator.md plugins/pm/pm-workflow/scripts/tests/test_orchestrator_sync.py
git commit -m "feat: generate orchestrator.md from CLAUDE.md anchors + sync test"
```

---

## Phase D — SessionStart 注入 hook

### Task D1: session_start_inject.py + hooks.json

**Files:**
- Create: `plugins/pm/pm-workflow/scripts/hooks/session_start_inject.py`
- Modify: `plugins/pm/pm-workflow/scripts/hooks/session_start_state_summary.py`（产物路径改 PROJECT_ROOT）
- Create: `plugins/pm/hooks/hooks.json`

**Interfaces:**
- 两条 SessionStart hook：①inject（静态：orchestrator.md + 绝对根声明）②state_summary（动态：读 PROJECT_ROOT/process_record/state.md）。静态在前护 cache。

- [ ] **Step 1: 写 session_start_inject.py**

```python
"""SessionStart：注入 orchestrator.md（静态）+ 绝对插件根声明。stdout 必须只有 JSON。"""
import json, os
from pathlib import Path

root = os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).resolve().parents[3])  # hooks/→scripts→pm-workflow→pm(plugin root)
orch = Path(root) / "pm-workflow" / "core" / "orchestrator.md"
body = orch.read_text(encoding="utf-8") if orch.exists() else "(orchestrator.md 缺失)"
decl = (f"\n\n[插件根] 框架文件绝对根 = {root}。"
        f"派发任何 subagent 时，prompt 必须声明：所有 `pm-workflow/...` 路径相对 {root} 解析；"
        f"产物 outputs/、process_record/ 相对项目 cwd。")
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": body + decl}}))
```

- [ ] **Step 2: 改 state_summary 产物路径为 PROJECT_ROOT**

把 `session_start_state_summary.py` 里读 `state.md` 的根由 `CLAUDE_PROJECT_DIR:-.` / `__file__` 派生统一为 `os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()`。

- [ ] **Step 3: 写 hooks.json**

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "*", "hooks": [
        { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/hooks/session_start_inject.py\"" },
        { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/hooks/session_start_state_summary.py\"" }
      ] }
    ]
  }
}
```

- [ ] **Step 4: 校验 inject stdout 为单 JSON 行**

Run: `cd plugins/pm/pm-workflow/scripts/hooks && python3 session_start_inject.py 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK', len(d['hookSpecificOutput']['additionalContext']))"`
Expected: `OK <非零长度>`

- [ ] **Step 5: Commit**

```bash
git add plugins/pm/pm-workflow/scripts/hooks/ plugins/pm/hooks/hooks.json
git commit -m "feat: SessionStart inject orchestrator.md + plugin-root declaration"
```

---

## Phase E — subagent 路径解析（P0-2 + A1/A2）

### Task E1: dispatch 协议加「插件根解析」约定

**Files:**
- Modify: `plugins/pm/pm-workflow/rules/agent_dispatch_protocol.md`

**Interfaces:**
- Produces: 一条 [Must]：编排器派发任何 subagent（PM/Supervisor/Explore）时，prompt 顶部必须注入「框架绝对根 = <根>；你读到的所有 `pm-workflow/...` 路径相对此根解析；执行 bash 脚本时用该根拼绝对路径；产物相对项目 cwd」。

- [ ] **Step 1: 在派发清单加约定段**

在 `agent_dispatch_protocol.md` 的 PM/Supervisor/Explore 派发清单各加一行 [Must]：派发 prompt 第 0 行写「框架根：{从 SessionStart 注入的[插件根]复制绝对路径} — 所有 pm-workflow/... 相对它解析」。

- [ ] **Step 2: 加 doc_query 复制改写约定（SSOT #81/#82 关键）**

在 `§大文件分节读取规范` 加一行 [Must]：编排器从 SECTION-MAP 表**复制 `doc_query.py` 命令进派发 prompt 时，必须把命令里的两处 `pm-workflow/...` 都改写为绝对框架根** —— ①脚本路径 `python3 {根}/pm-workflow/scripts/doc_query.py` ②目标文件参数 `{根}/pm-workflow/rules/X.md`。给出改写后样例命令。

- [ ] **Step 3: 校验三类派发 + doc_query 都覆盖**

Run: `grep -cE "框架根|插件根解析|doc_query.*绝对" plugins/pm/pm-workflow/rules/agent_dispatch_protocol.md`
Expected: ≥4

- [ ] **Step 4: Commit**

```bash
git add plugins/pm/pm-workflow/rules/agent_dispatch_protocol.md
git commit -m "feat: dispatch protocol injects absolute framework root (incl doc_query script+arg paths)"
```

### Task E2: 4 行 command-body bash 用 ${CLAUDE_PLUGIN_ROOT}

**Files:**
- Modify: `plugins/pm/commands/*.md`（含 bash 调脚本的 4 行）

- [ ] **Step 1: 定位 command 正文 bash 调用**

Run: `grep -rn "python3 pm-workflow/scripts\|bash pm-workflow/scripts" plugins/pm/commands/`
Expected: 4 行（A2 中确认）

- [ ] **Step 2: 改为绝对根写法**

每行 `python3 pm-workflow/scripts/X.py ...` → `python3 "${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/X.py" ...`

- [ ] **Step 3: 确认改全**

Run: `grep -rn "python3 pm-workflow/scripts\|bash pm-workflow/scripts" plugins/pm/commands/`
Expected: 无输出（都已带变量）

- [ ] **Step 4: Commit**

```bash
git add plugins/pm/commands/
git commit -m "feat: command-body bash uses CLAUDE_PLUGIN_ROOT (load-time substitution)"
```

### Task E3: doc_query.py 框架根回退（加固，降 16 处调用风险）

**Files:**
- Modify: `plugins/pm/pm-workflow/scripts/doc_query.py:300`（`path = Path(args.file)` 处）
- Test: `plugins/pm/pm-workflow/scripts/tests/test_doc_query_root.py`

**Interfaces:**
- Consumes: `pm_paths.FRAMEWORK_ROOT`
- 行为：若传入的 `file` 相对 cwd 不存在，但相对 FRAMEWORK_ROOT 存在，则用后者。使 doc_query 的**文件参数**无论调用方写裸 `pm-workflow/...` 还是绝对路径都能定位（脚本路径仍由派发改写/`${CLAUDE_PLUGIN_ROOT}` 负责）。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_doc_query_root.py
import subprocess, sys, pathlib, os
SCRIPTS = pathlib.Path(__file__).resolve().parents[1]
def test_resolves_framework_relative_path(tmp_path, monkeypatch):
    # 在一个非框架 cwd 下，传裸 pm-workflow/... 路径仍能 outline 成功
    monkeypatch.chdir(tmp_path)
    target = "pm-workflow/rules/agent_dispatch_protocol.md"
    r = subprocess.run([sys.executable, str(SCRIPTS/"doc_query.py"), "outline", target],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"未能按 FRAMEWORK_ROOT 解析裸路径:\n{r.stderr}"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd plugins/pm/pm-workflow/scripts && python3 -m pytest tests/test_doc_query_root.py -v`
Expected: FAIL（cwd 下找不到文件）

- [ ] **Step 3: 加框架根回退**

在 `doc_query.py` 的 `path = Path(args.file)` 之后插入：
```python
if not path.exists():
    import os, sys as _s
    _here = pathlib.Path(__file__).resolve().parents[2] if 'pathlib' in dir() else None
    from pm_paths import FRAMEWORK_ROOT  # 顶部确保可 import（见 B2 sys.path 备注）
    alt = FRAMEWORK_ROOT / args.file
    if alt.exists():
        path = alt
```
（实现等价即可：未找到则尝试 `FRAMEWORK_ROOT / args.file`。`import pathlib`、`from pm_paths import FRAMEWORK_ROOT` 放文件顶部。）

- [ ] **Step 4: 跑测试确认通过 + 全量 pytest**

Run: `python3 -m pytest tests/test_doc_query_root.py -v && python3 -m pytest -q`
Expected: PASS + 全绿

- [ ] **Step 5: Commit**

```bash
git add plugins/pm/pm-workflow/scripts/doc_query.py plugins/pm/pm-workflow/scripts/tests/test_doc_query_root.py
git commit -m "feat: doc_query resolves bare pm-workflow/ file args against FRAMEWORK_ROOT"
```

---

## Phase F — 打包卫生（清理/文档/双模）

### Task F1: 包含/排除 + .gitignore + CHANGELOG/README

**Files:**
- Create: `<REPO>/CHANGELOG.md`、`<REPO>/README.md`
- Modify: `<REPO>/.gitignore`

- [ ] **Step 1: 排除运行态/内部件不进 payload**

确认 `plugins/pm/` 下**不含** `process_record/`、`outputs/`、`nb_log.md`、`HANDOFF.md`、`workflow_backlog/`、`PROTOTYPE_STRATEGY_DECISION.md`、`__pycache__`。若误带，`git rm -r --cached` 并加 `.gitignore`。

Run: `find plugins/pm -name "__pycache__" -o -name "process_record" -o -name "outputs"`
Expected: 无输出

- [ ] **Step 2: 写 .gitignore（追加）**

```
__pycache__/
*.pyc
.pytest_cache/
process_record/
outputs/
```

- [ ] **Step 3: 写 CHANGELOG.md（仅 release notes）+ README.md（含安装 + 两模式对照 + L2 演化=纯消费者）**

CHANGELOG 首条：`## v1.0.0 — 插件化首发`。README 含：① `claude plugin marketplace add <repo>` + `/plugin install pm@pm-workflow-market`；②两模式对照表（插件 `/plugin update` vs git-copy `install_hooks+syncUpstream`，deprecated）；③L2 演化：插件用户=纯消费者，改进走源仓 issue/PR，contributor 可 git-clone。

- [ ] **Step 4: Commit**

```bash
git add .gitignore CHANGELOG.md README.md && git commit -m "docs: changelog (release-notes only) + README (install + dual-mode + L2 evolution)"
```

---

## Phase G — 集成验证（装插件跑通）

### Task G1: 本地装插件 + 四阶段冒烟 + 双根/路径断言

**Files:** 无（验证任务）

- [ ] **Step 1: 本地装插件（独立空项目）**

```bash
mkdir -p /tmp/pmproj && cd /tmp/pmproj
claude --plugin-dir <REPO>/plugins/pm -p "/pm:projectStatus" --permission-mode bypassPermissions --output-format text
```
Expected: 命令被识别执行（不报"unknown command"）；SessionStart 注入 orchestrator 内容可见。

- [ ] **Step 2: 跑一个轻量需求过 stage 1（或直接触发 precheck 脚本路径）**

在 `/tmp/pmproj` 触发一次会写产物的流程（如 `/pm:newRequirement` 一句话需求，进行到产出 outputs/）。

- [ ] **Step 3: 断言产物落项目、框架在 cache（双根红线现场验证）**

```bash
ls /tmp/pmproj/outputs /tmp/pmproj/process_record 2>/dev/null && echo "PRODUCTS_IN_PROJECT_OK"
find <REPO>/plugins/pm/pm-workflow/outputs 2>/dev/null && echo "LEAK!" || echo "NO_LEAK_INTO_FRAMEWORK"
```
Expected: `PRODUCTS_IN_PROJECT_OK` + `NO_LEAK_INTO_FRAMEWORK`

- [ ] **Step 4: transitive 套根 spot-check（治残留①，承认抽样非穷尽）**

派发一个 subagent，任务 = 「按派发约定，从最高密度文件 `agent_dispatch_protocol.md`（143 处 `pm-workflow/` 引用）里**实际 follow 至少 5 个不同的 transitive 引用**（含一条 doc_query 命令），逐一 Read/执行成功并回报解析后的绝对路径」。
Expected: 5/5 解析到 cache 真实文件、无 "file not found"。
**若任一失败** → 说明模型未可靠套根 → 加固：把"插件根 + 解析约定"做成**预加载 skill**（§13.5 D：subagent 启动加载预加载 skill）再重测。
> 注：这是**抽样**，不证明全部 433 处都被可靠套根；transitive 可靠性是承认的残留风险（设计 §13.5），通用规则 + fallback + 本 spot-check 是管控手段，非消除。

- [ ] **Step 5: 全量 pytest 终验**

Run: `cd <REPO>/plugins/pm/pm-workflow/scripts && python3 -m pytest -q`
Expected: 全绿（含 test_dual_root、test_orchestrator_sync）

- [ ] **Step 6: Commit（如有验证脚本/修复）**

```bash
git add -A && git commit -m "test: integration — plugin install, four-stage smoke, dual-root + path resolution verified"
```

---

## Self-Review（已执行）

- **Spec 覆盖**：①核心+适配壳布局→A1/A2 ②双根 P0-1→B1/B2/B3 ③orchestrator 生成+一致性→C1/C2 ④SessionStart 注入→D1 ⑤subagent 路径 P0-2/A1/A2→E1/E2 ⑥包含排除/CHANGELOG 单职/README 双模/L2 演化→F1 ⑦集成测试（双根红线+路径）→G1 ⑧B/C 待核（自定义路径/relative 根）→已由 A2 布局体现。
- **占位扫描**：plugin.json 的 `author/homepage/repository/license` 是发布前元数据（非代码占位，已注明）；其余无 TBD/TODO 代码占位。
- **类型一致**：`FRAMEWORK_ROOT`/`PROJECT_ROOT` 全程同名；`gen_orchestrator.py --check` 与测试一致；hooks.json 命令路径与脚本实际位置一致。

## 已知执行注意
- B2 的 import：若某脚本被跨目录调用，按 Step 2 备注加 `sys.path.insert`。
- C2 的 `find_claude_md()` 上级层数依最终搬迁深度（plugins/pm/pm-workflow）核对：`parents` 级数 = REPO 到 scripts 的层级，执行时用 `pwd` 实测一次。
- 命名 `pm` 如改名：全局替换 plugin.json name + marketplace 条目 + 文档命令前缀。
