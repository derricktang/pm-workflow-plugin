"""测试 sync_from_upstream.sh — 下游主动同步 L2 脚本（议题 24）

覆盖：
- 参数解析（--help / --dry-run / 未知参数 / --upstream-local / 等）
- L2 白名单严格控制（仅 pm-workflow/ + CLAUDE.md + .claude/commands/）
- L1 保护（rsync 不触动 L1，二阶段核验）
- 退出码语义（0/2/3/4 各分支）
- idempotent（重跑等价）
- dry-run 完整预览（无实际改动）

实现：subprocess 调脚本 + 临时 git 仓（fixtures），不依赖网络。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SCRIPTS_DIR / "sync_from_upstream.sh"


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _run_script(args: list[str], cwd: Path, env: dict | None = None,
                timeout: int = 30) -> subprocess.CompletedProcess:
    """运行 sync_from_upstream.sh，返回 CompletedProcess。"""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", str(SCRIPT)] + args,
        cwd=cwd,
        env=full_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _init_git_repo(path: Path, with_pm_workflow: bool = True,
                   with_claude_md: bool = True) -> None:
    """初始化一个最小 git 仓库（含 L2 镜像）。"""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"],
                   cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=path, check=True)
    # 默认分支名一致（main）
    subprocess.run(["git", "checkout", "-b", "main", "-q"],
                   cwd=path, check=False)

    if with_pm_workflow:
        (path / "pm-workflow").mkdir(exist_ok=True)
        (path / "pm-workflow" / "rules").mkdir(exist_ok=True)
        (path / "pm-workflow" / "scripts").mkdir(exist_ok=True)
        (path / "pm-workflow" / "rules" / "dummy.md").write_text("dummy\n")
    if with_claude_md:
        (path / "CLAUDE.md").write_text("# CLAUDE.md\nbaseline\n")

    # initial commit
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    result = subprocess.run(
        ["git", "commit", "-m", "init", "-q"],
        cwd=path, capture_output=True, text=True,
    )
    # commit 即使失败（空仓）也容忍


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def downstream_repo(tmp_path: Path) -> Path:
    """下游仓 fixture（含 pm-workflow/ + CLAUDE.md 镜像）。"""
    repo = tmp_path / "downstream"
    _init_git_repo(repo)
    return repo


@pytest.fixture
def upstream_repo(tmp_path: Path) -> Path:
    """上游仓 fixture（含 pm-workflow/ + CLAUDE.md 新版本内容）。"""
    repo = tmp_path / "upstream"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "up@up.com"],
                   cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "up"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-b", "main", "-q"],
                   cwd=repo, check=False)

    (repo / "pm-workflow").mkdir()
    (repo / "pm-workflow" / "rules").mkdir()
    (repo / "pm-workflow" / "scripts").mkdir()
    (repo / "pm-workflow" / "rules" / "dummy.md").write_text("dummy v2\n")
    (repo / "pm-workflow" / "rules" / "new_rule.md").write_text(
        "# new L2 rule (upstream only)\n"
    )
    (repo / "CLAUDE.md").write_text("# CLAUDE.md\nnew version from upstream\n")

    # outputs/ + process_record/ 在上游仓不存在（L2-only）

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "upstream init", "-q"],
                   cwd=repo, check=True)
    return repo


# ── 参数 / --help / 未知参数 ─────────────────────────────────────────────────

class TestArgs:
    def test_help_flag(self, tmp_path: Path):
        """--help 退出码 0 且输出含用法信息。"""
        result = _run_script(["--help"], cwd=tmp_path)
        assert result.returncode == 0
        assert "sync_from_upstream.sh" in result.stdout
        assert "用法" in result.stdout or "Usage" in result.stdout
        # 关键选项必现
        assert "--dry-run" in result.stdout
        assert "--upstream-local" in result.stdout
        assert "--no-commit" in result.stdout

    def test_short_help_flag(self, tmp_path: Path):
        """-h 与 --help 等价。"""
        result = _run_script(["-h"], cwd=tmp_path)
        assert result.returncode == 0
        assert "sync_from_upstream" in result.stdout

    def test_unknown_arg_exits_2(self, downstream_repo: Path):
        """未知参数 → 退出码 2。"""
        result = _run_script(["--bogus-flag"], cwd=downstream_repo)
        assert result.returncode == 2
        assert "未知参数" in result.stderr or "未知参数" in result.stdout

    def test_not_in_git_repo_exits_4(self, tmp_path: Path):
        """非 git 仓 → 退出码 4。"""
        non_git = tmp_path / "not_a_repo"
        non_git.mkdir()
        result = _run_script(["--dry-run"], cwd=non_git)
        assert result.returncode == 4

    def test_no_pm_workflow_exits_4(self, tmp_path: Path):
        """git 仓但无 pm-workflow/ → 退出码 4。"""
        repo = tmp_path / "no_pm"
        _init_git_repo(repo, with_pm_workflow=False)
        result = _run_script(["--dry-run"], cwd=repo)
        assert result.returncode == 4
        assert "pm-workflow" in result.stderr or "pm-workflow" in result.stdout


# ── dry-run 模式 ─────────────────────────────────────────────────────────────

class TestDryRun:
    def test_dry_run_no_file_change(
        self, downstream_repo: Path, upstream_repo: Path
    ):
        """--dry-run 不应改任何文件。"""
        # 记录 dry-run 前的所有文件 + 内容 hash
        before = _file_snapshot(downstream_repo)

        result = _run_script(
            ["--dry-run", "--upstream-local", str(upstream_repo)],
            cwd=downstream_repo,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        after = _file_snapshot(downstream_repo)
        assert before == after, "dry-run 修改了文件"

    def test_dry_run_no_git_changes(
        self, downstream_repo: Path, upstream_repo: Path
    ):
        """--dry-run 不应产生 git status 改动。"""
        result = _run_script(
            ["--dry-run", "--upstream-local", str(upstream_repo)],
            cwd=downstream_repo,
        )
        assert result.returncode == 0

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=downstream_repo, capture_output=True, text=True,
        )
        assert status.stdout.strip() == "", \
            f"dry-run 后 git status 有改动:\n{status.stdout}"

    def test_dry_run_completes_all_8_steps(
        self, downstream_repo: Path, upstream_repo: Path
    ):
        """dry-run 应完整跑完 8 step（防 SIGPIPE 中断回归）。

        历史 bug：rsync | grep | head -20 在 pipefail 下因 head 关闭管道
        触发 SIGPIPE，脚本中途退出码 1。修复：dry-run 预览段临时关闭 pipefail。
        """
        result = _run_script(
            ["--dry-run", "--upstream-local", str(upstream_repo)],
            cwd=downstream_repo,
        )
        assert result.returncode == 0
        # 8 step 标识全在输出中
        for n in range(1, 9):
            assert f"[{n}/8]" in result.stdout, \
                f"step {n}/8 缺失（可能中途 SIGPIPE 退出）"
        # 完成标识
        assert "dry-run 完成" in result.stdout


# ── L2 同步 + L1 保护 ────────────────────────────────────────────────────────

class TestL2WhitelistSync:
    def test_local_sync_updates_l2_only(
        self, downstream_repo: Path, upstream_repo: Path
    ):
        """本地 rsync 同步：只动 L2，L1 不动。"""
        # 在下游仓预先放 L1 dirty 文件
        (downstream_repo / "outputs").mkdir(exist_ok=True)
        l1_file = downstream_repo / "outputs" / "prd_test_latest.html"
        l1_file.write_text("<html>L1 PM content</html>")
        l1_hash_before = _content_hash(l1_file)

        result = _run_script(
            [
                "--upstream-local", str(upstream_repo),
                "--no-verify", "--no-assemble", "--no-commit",
            ],
            cwd=downstream_repo,
        )
        assert result.returncode == 0, \
            f"exit={result.returncode}\nstdout:{result.stdout}\nstderr:{result.stderr}"

        # L2 已更新
        assert (downstream_repo / "pm-workflow" / "rules" / "new_rule.md").exists()
        assert "new version from upstream" in \
            (downstream_repo / "CLAUDE.md").read_text()

        # L1 未触动
        assert l1_file.exists()
        assert _content_hash(l1_file) == l1_hash_before, "L1 文件被改"

    def test_outputs_not_touched_by_l2_sync(
        self, downstream_repo: Path, upstream_repo: Path
    ):
        """outputs/ + process_record/ 不在 L2 白名单内，不应被 rsync 触动。"""
        (downstream_repo / "outputs").mkdir(exist_ok=True)
        (downstream_repo / "outputs" / "spec_x.md").write_text("L1 spec")
        (downstream_repo / "process_record").mkdir(exist_ok=True)
        (downstream_repo / "process_record" / "state.md").write_text("L1 state")

        result = _run_script(
            [
                "--upstream-local", str(upstream_repo),
                "--no-verify", "--no-assemble", "--no-commit",
            ],
            cwd=downstream_repo,
        )
        assert result.returncode == 0

        # outputs / process_record 内容应完全不变
        assert (downstream_repo / "outputs" / "spec_x.md").read_text() == "L1 spec"
        assert (downstream_repo / "process_record" / "state.md").read_text() == "L1 state"

    def test_l1_dirty_warning_not_blocking(
        self, downstream_repo: Path, upstream_repo: Path
    ):
        """L1 dirty 触发 warning 但不阻断流程。"""
        # 制造 L1 dirty
        (downstream_repo / "outputs").mkdir(exist_ok=True)
        (downstream_repo / "outputs" / "dirty.md").write_text("uncommitted")

        result = _run_script(
            [
                "--upstream-local", str(upstream_repo),
                "--no-verify", "--no-assemble", "--no-commit",
            ],
            cwd=downstream_repo,
        )
        # 不阻断
        assert result.returncode == 0
        # 出现 warning 措辞（PM 工作残留 / dirty 等关键词）
        combined = result.stdout + result.stderr
        assert "dirty" in combined or "L1" in combined


# ── idempotent 重跑 ──────────────────────────────────────────────────────────

class TestIdempotent:
    def test_rerun_no_change(
        self, downstream_repo: Path, upstream_repo: Path
    ):
        """同步后立即再跑：L2 无变化，不报错。"""
        # 第一次同步
        result1 = _run_script(
            [
                "--upstream-local", str(upstream_repo),
                "--no-verify", "--no-assemble", "--no-commit",
            ],
            cwd=downstream_repo,
        )
        assert result1.returncode == 0

        # 把改动 commit 掉，模拟"同步成功后已落地"
        subprocess.run(
            ["git", "add", "-A"], cwd=downstream_repo, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "synced", "-q"],
            cwd=downstream_repo, check=True,
        )

        # 第二次同步：应识别"无变化"
        result2 = _run_script(
            [
                "--upstream-local", str(upstream_repo),
                "--no-verify", "--no-assemble", "--no-commit",
            ],
            cwd=downstream_repo,
        )
        assert result2.returncode == 0
        # 输出含"无变化 / 已同步"等关键词
        combined = result2.stdout + result2.stderr
        assert "无变化" in combined or "已同步" in combined or "无改动" in combined


# ── 各 --no-* 选项 ───────────────────────────────────────────────────────────

class TestSkipFlags:
    def test_no_verify_skips_pytest(
        self, downstream_repo: Path, upstream_repo: Path
    ):
        """--no-verify 应跳过 pytest 步骤。"""
        result = _run_script(
            [
                "--upstream-local", str(upstream_repo),
                "--no-verify", "--no-assemble", "--no-commit",
            ],
            cwd=downstream_repo,
        )
        assert result.returncode == 0
        # 输出含"跳过"或 "--no-verify"
        assert "no-verify" in result.stdout or "跳过" in result.stdout

    def test_no_commit_leaves_dirty(
        self, downstream_repo: Path, upstream_repo: Path
    ):
        """--no-commit 后 git status 应有未提交的 L2 改动。"""
        result = _run_script(
            [
                "--upstream-local", str(upstream_repo),
                "--no-verify", "--no-assemble", "--no-commit",
            ],
            cwd=downstream_repo,
        )
        assert result.returncode == 0

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=downstream_repo, capture_output=True, text=True,
        )
        assert status.stdout.strip() != "", \
            "--no-commit 后应有未提交改动"
        # 改动须仅涉及 L2
        # git status --porcelain 格式: "XY path"（X/Y 状态 char，空格分隔 path）
        for line in status.stdout.strip().split("\n"):
            # 安全 split：parts[0] = 状态码, 其余拼成 path
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                continue
            path = parts[1].strip().strip('"')
            assert (
                path.startswith("pm-workflow/")
                or path == "CLAUDE.md"
                or path.startswith(".claude/commands/")
            ), f"非 L2 路径被改: {path!r} (原行: {line!r})"


# ── 工具函数（snapshot / hash）───────────────────────────────────────────────

def _file_snapshot(repo: Path) -> dict[str, str]:
    """返回 {relpath: content_hash} dict（忽略 .git/）。"""
    import hashlib
    result = {}
    for p in repo.rglob("*"):
        if p.is_file() and ".git" not in p.parts:
            rel = p.relative_to(repo).as_posix()
            result[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def _content_hash(file: Path) -> str:
    import hashlib
    return hashlib.sha256(file.read_bytes()).hexdigest()


# ── 回归锁：pipefail+set -e 下 diff 退出码崩溃 bug（下游 PM 实测，commit 前崩）──────
def test_diff_pipelines_have_pipefail_guard():
    """set -euo pipefail 下，`diff <(a) <(b)` 在输入不同时返回 exit 1，经 pipefail 冒泡到
    命令替换赋值 / standalone 管道会触发 set -e 在 git commit 前中止整脚本（下游 PM 实测：
    Step 7 assemble 改 outputs/ → 二阶段核验 BEFORE!=FINAL → diff exit 1 → 必崩）。
    所有 `diff <(` 管道**必须**有 `|| true` 兜底吞掉信息性退出码。本测试静态锁定，防回退。"""
    lines = SCRIPT.read_text(encoding="utf-8").splitlines()
    offenders = []
    for i, ln in enumerate(lines):
        if "diff <(" in ln:
            chunk, j = ln, i
            while chunk.rstrip().endswith("\\") and j + 1 < len(lines):
                j += 1
                chunk += "\n" + lines[j]
            if "|| true" not in chunk:
                offenders.append((i + 1, ln.strip()[:70]))
    assert not offenders, (
        f"diff <( 管道缺 `|| true` 兜底（pipefail+set -e 会在 commit 前崩）：{offenders}"
    )
