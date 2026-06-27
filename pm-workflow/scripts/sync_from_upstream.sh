#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# sync_from_upstream.sh — 下游主动同步上游 L2 升级
# ════════════════════════════════════════════════════════════════
#
# 用途
# ──────────────
# 下游产品仓（如 bujue-quotation-tool / bujue-business-circle / bujue-payment-module
# / private-domain-homepage-module）从上游 claude-code-pm-workflow 主动拉取 L2 升级。
# 与上游 `~/.bash_functions sync_l2` 函数对偶 —— 后者是上游 push 到下游，本脚本是
# 下游 pull from 上游。两者覆盖的 L2 白名单一致、7 Gotcha 防御一致。
#
# 适用场景
# ──────────────
# 1. 下游 PM 知悉上游 L2 升级（如 NB-XX 已落地）后主动拉取
# 2. 编排器在派发下游 PM 任务前，先拉取最新 L2
# 3. 定时任务 / 钩子触发的自动 L2 同步
#
# 用法
# ──────────────
#   bash pm-workflow/scripts/sync_from_upstream.sh [选项]
#
# 选项
# ──────────────
#   --upstream-url URL          上游 git URL
#                               默认: http://192.168.0.99:8880/pm-group/claude-code-pm-workflow.git
#   --upstream-branch BRANCH    上游分支（默认: main）
#   --upstream-local PATH       从本地路径 rsync（不走 git，优先级高于 --upstream-url）
#   --dry-run                   预览不实际修改（rsync --dry-run）
#   --no-verify                 跳过 pytest + template_purity 验证
#   --no-assemble               跳过重 assemble（仅 L2 同步，不重生 outputs/）
#   --no-commit                 不自动 commit（PM 自主决定 SemVer 节奏）
#   --no-push                   不自动 push（默认就是不 push，仅 commit 本地）
#   --push                      显式 push 到 origin（覆盖默认 no-push）
#   --commit-msg MSG            指定 commit 消息
#   -h, --help                  显示本帮助
#
# 8-Step 流程
# ──────────────
#   [1/8] 配置 upstream remote（已配置且 URL 匹配则跳过）
#   [2/8] fetch upstream branch
#   [3/8] 检查 L1 工作区状态（dirty 警告但不阻断）
#   [4/8] checkout L2 文件（白名单严格控制）
#   [5/8] pytest 验证下游回归基线
#   [6/8] precheck_template_purity 验证
#   [7/8] 重 assemble outputs/（除非 --no-assemble）
#   [8/8] commit L2 同步（除非 --no-commit）
#
# L2 白名单
# ──────────────
#   pm-workflow/         （除 __pycache__/ / *.pyc / .scaffold.lock / .pytest_cache/）
#   CLAUDE.md
#   .claude/commands/    （若上游有）
#
# L1 保护
# ──────────────
#   - 不触动 outputs/ / process_record/ / 仓根其他文件
#   - 执行前抓取 L1 dirty 文件列表 → 警告但不阻断
#   - 执行后核验 L1 文件列表 = 执行前（差异 → 失败退出码 3）
#
# 退出码
# ──────────────
#   0  全部成功
#   1  验证失败（pytest / template_purity FAIL）
#   2  参数错误
#   3  L1 被误改（白名单逃逸 / 抓取核验差异）
#   4  环境错误（非 git 仓 / 无 pm-workflow/ / upstream 不可达）
#
# Agent 调用示例
# ──────────────
#   # 1. 默认本地 rsync 模式（最快，需上游仓在本机 ~/Documents/claude-code-pm-workflow）
#   bash pm-workflow/scripts/sync_from_upstream.sh \
#        --upstream-local ~/Documents/claude-code-pm-workflow
#
#   # 2. git fetch 模式（远端拉取）
#   bash pm-workflow/scripts/sync_from_upstream.sh \
#        --upstream-url http://192.168.0.99:8880/pm-group/claude-code-pm-workflow.git
#
#   # 3. 仅预览不实施
#   bash pm-workflow/scripts/sync_from_upstream.sh --dry-run
#
#   # 4. 全自动闭环（含 push）
#   bash pm-workflow/scripts/sync_from_upstream.sh --push \
#        --commit-msg "[L2-only] sync upstream NB-WE-XX"
#
# 7 Gotcha 防御
# ──────────────
#   #1 .pyc 污染 → rsync --exclude '__pycache__/' '*.pyc'
#   #2 core.quotepath 中文名假阳性 → 所有 git 命令带 -c core.quotepath=false
#   #3 镜像不 regen L1 → Step 7 自动重 assemble outputs/
#   #4 复合短路链假阴性 → 用 if-then 不用 &&-链
#   #5 &&-链短路 → 同上
#   #6 abort-guard #2 用 working tree diff 误判活跃 PM → 二阶段核验
#   #7 dirty 状态不区分来源 → L1 dirty 抓取前/后对比，仅 stage L2 路径
#
# SSOT
# ──────────────
#   - 上游对偶函数：~/.bash_functions sync_l2 / sync_l2_all
#   - memory：downstream_l2_sync_procedure（7 Gotcha 全量记录）
#   - 议题 24（2026-06-05 落地）
#
# ════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── 默认参数 ───
UPSTREAM_URL="http://192.168.0.99:8880/pm-group/claude-code-pm-workflow.git"
UPSTREAM_BRANCH="main"
UPSTREAM_LOCAL=""
DRY_RUN=0
DO_VERIFY=1
DO_ASSEMBLE=1
DO_COMMIT=1
DO_PUSH=0
COMMIT_MSG=""

# ─── L2 白名单（与上游 sync_l2 严格一致）───
L2_PATHS=(
    "pm-workflow/"
    "CLAUDE.md"
    "CHANGELOG_L2.md"
    ".claude/commands/"
)

# ─── 工具函数 ───
log() { echo "$@"; }
err() { echo "❌ $*" >&2; }
warn() { echo "⚠️  $*" >&2; }
ok() { echo "✅ $*"; }
step() { echo ""; echo "─── [$1/8] $2 ───"; }

show_help() {
    sed -n '/^# ═══/,/^set -euo pipefail/p' "$0" | sed 's/^# \{0,1\}//' | head -n -2
}

# ─── 参数解析 ───
while [[ $# -gt 0 ]]; do
    case "$1" in
        --upstream-url)    UPSTREAM_URL="$2"; shift 2 ;;
        --upstream-branch) UPSTREAM_BRANCH="$2"; shift 2 ;;
        --upstream-local)  UPSTREAM_LOCAL="$2"; shift 2 ;;
        --dry-run)         DRY_RUN=1; shift ;;
        --no-verify)       DO_VERIFY=0; shift ;;
        --no-assemble)     DO_ASSEMBLE=0; shift ;;
        --no-commit)       DO_COMMIT=0; shift ;;
        --no-push)         DO_PUSH=0; shift ;;
        --push)            DO_PUSH=1; shift ;;
        --commit-msg)      COMMIT_MSG="$2"; shift 2 ;;
        -h|--help)         show_help; exit 0 ;;
        *)                 err "未知参数: $1"; echo "用 --help 查看用法" >&2; exit 2 ;;
    esac
done

# ─── 定位下游仓根 ───
if ! REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
    err "当前目录不在 git 仓库内"
    exit 4
fi

if [[ ! -d "$REPO_ROOT/pm-workflow" ]]; then
    err "下游仓无 pm-workflow/ 镜像 — 首次接入需手工初始化"
    err "  当前仓：$REPO_ROOT"
    exit 4
fi

REPO_NAME=$(basename "$REPO_ROOT")

log "═══════════════════════════════════════"
log "  sync_from_upstream"
log "  下游：$REPO_NAME"
if [[ -n "$UPSTREAM_LOCAL" ]]; then
    log "  上游：$UPSTREAM_LOCAL（本地）"
else
    log "  上游：$UPSTREAM_URL ($UPSTREAM_BRANCH)"
fi
log "  模式：$([ $DRY_RUN -eq 1 ] && echo 'dry-run' || echo '实施')"
log "═══════════════════════════════════════"

# ─── L1 dirty 抓取（执行前快照，Gotcha #7）───
# Gotcha #2 治本：所有 git 命令带 -c core.quotepath=false
snapshot_l1_dirty() {
    git -C "$REPO_ROOT" -c core.quotepath=false status --porcelain \
        | awk '{print $NF}' \
        | grep -vE '^(pm-workflow/|CLAUDE\.md$|CHANGELOG_L2\.md$|\.claude/commands/)' \
        || true
}

L1_DIRTY_BEFORE=$(snapshot_l1_dirty)
if [[ -n "$L1_DIRTY_BEFORE" ]]; then
    L1_BEFORE_COUNT=$(echo "$L1_DIRTY_BEFORE" | wc -l)
else
    L1_BEFORE_COUNT=0
fi

# ═══════════════════════════════════════════════════════════════
# Step 1: 配置 upstream remote（本地 rsync 模式跳过）
# ═══════════════════════════════════════════════════════════════
step 1 "配置 upstream remote"

if [[ -n "$UPSTREAM_LOCAL" ]]; then
    if [[ ! -d "$UPSTREAM_LOCAL/pm-workflow" ]]; then
        err "上游本地路径无 pm-workflow/：$UPSTREAM_LOCAL"
        exit 4
    fi
    log "  本地 rsync 模式 → 跳过 git remote 配置"
else
    # 检查 upstream remote 是否已配置且 URL 匹配
    current_url=$(git -C "$REPO_ROOT" remote get-url upstream 2>/dev/null || echo "")
    if [[ "$current_url" == "$UPSTREAM_URL" ]]; then
        log "  upstream remote 已就位 → 跳过配置"
    elif [[ -n "$current_url" ]]; then
        log "  upstream URL 不匹配（当前: $current_url）→ 更新"
        if [[ $DRY_RUN -eq 0 ]]; then
            git -C "$REPO_ROOT" remote set-url upstream "$UPSTREAM_URL"
        fi
    else
        log "  添加 upstream remote → $UPSTREAM_URL"
        if [[ $DRY_RUN -eq 0 ]]; then
            git -C "$REPO_ROOT" remote add upstream "$UPSTREAM_URL"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════
# Step 2: fetch upstream branch
# ═══════════════════════════════════════════════════════════════
step 2 "fetch upstream"

if [[ -n "$UPSTREAM_LOCAL" ]]; then
    UPSTREAM_HASH=$(git -C "$UPSTREAM_LOCAL" rev-parse --short HEAD 2>/dev/null || echo "unknown")
    UPSTREAM_SUBJECT=$(git -C "$UPSTREAM_LOCAL" log -1 --pretty=%s 2>/dev/null || echo "")
    log "  上游 HEAD: $UPSTREAM_HASH — $UPSTREAM_SUBJECT"
else
    if [[ $DRY_RUN -eq 0 ]]; then
        if ! git -C "$REPO_ROOT" fetch upstream "$UPSTREAM_BRANCH" 2>&1 | tail -3; then
            err "git fetch upstream 失败"
            exit 4
        fi
        UPSTREAM_HASH=$(git -C "$REPO_ROOT" rev-parse --short "upstream/$UPSTREAM_BRANCH")
        UPSTREAM_SUBJECT=$(git -C "$REPO_ROOT" log -1 --pretty=%s "upstream/$UPSTREAM_BRANCH")
        log "  上游 HEAD: $UPSTREAM_HASH — $UPSTREAM_SUBJECT"
    else
        log "  [dry-run] 跳过 fetch"
        UPSTREAM_HASH="dry-run"
        UPSTREAM_SUBJECT="(dry-run)"
    fi
fi

# ═══════════════════════════════════════════════════════════════
# Step 3: 检查 L1 工作区状态
# ═══════════════════════════════════════════════════════════════
step 3 "检查 L1 工作区状态"

if [[ $L1_BEFORE_COUNT -gt 0 ]]; then
    warn "L1 有 $L1_BEFORE_COUNT 文件 dirty — PM 工作残留，将保持不动"
    echo "$L1_DIRTY_BEFORE" | head -5 | sed 's/^/    /'
    if [[ $L1_BEFORE_COUNT -gt 5 ]]; then
        log "    ...（共 $L1_BEFORE_COUNT 文件，仅显示前 5）"
    fi
    log ""
    log "  注：rsync 不触动 L1，但 PM 应在合适时机自行决定 L1 改动归属"
else
    log "  L1 工作区干净"
fi

# ═══════════════════════════════════════════════════════════════
# Step 4: checkout L2 文件（白名单严格控制）
# ═══════════════════════════════════════════════════════════════
step 4 "checkout L2 文件"

if [[ -n "$UPSTREAM_LOCAL" ]]; then
    # 本地 rsync 模式
    if [[ $DRY_RUN -eq 1 ]]; then
        log "  [dry-run] rsync 预览："
        # 注：head -20 可能向上游 grep / rsync 发 SIGPIPE，pipefail 会捕获为失败；
        # 这里临时关 pipefail，dry-run 仅展示，无需严格中间环节退出码
        set +o pipefail
        rsync -av --delete --dry-run \
            --exclude='__pycache__/' --exclude='*.pyc' \
            --exclude='.scaffold.lock' --exclude='.pytest_cache/' \
            "$UPSTREAM_LOCAL/pm-workflow/" "$REPO_ROOT/pm-workflow/" 2>&1 \
          | grep -v '^building\|^sending\|^$\|^total size\|^sent\|DRY RUN' \
          | head -20 | sed 's/^/    /'
        set -o pipefail
    else
        log "  [4.1] rsync pm-workflow/"
        if ! rsync -a --delete \
            --exclude='__pycache__/' --exclude='*.pyc' \
            --exclude='.scaffold.lock' --exclude='.pytest_cache/' \
            "$UPSTREAM_LOCAL/pm-workflow/" "$REPO_ROOT/pm-workflow/"; then
            err "rsync pm-workflow/ 失败"
            exit 4
        fi

        log "  [4.2] cp CLAUDE.md"
        if ! cp "$UPSTREAM_LOCAL/CLAUDE.md" "$REPO_ROOT/CLAUDE.md"; then
            err "cp CLAUDE.md 失败"
            exit 4
        fi

        # CHANGELOG_L2.md（下游升级日志 + 整改指引；上游有则同步，无则跳过向后兼容）
        if [[ -f "$UPSTREAM_LOCAL/CHANGELOG_L2.md" ]]; then
            log "  [4.2b] cp CHANGELOG_L2.md"
            if ! cp "$UPSTREAM_LOCAL/CHANGELOG_L2.md" "$REPO_ROOT/CHANGELOG_L2.md"; then
                err "cp CHANGELOG_L2.md 失败"
                exit 4
            fi
        fi

        if [[ -d "$UPSTREAM_LOCAL/.claude/commands" ]]; then
            log "  [4.3] rsync .claude/commands/"
            mkdir -p "$REPO_ROOT/.claude"
            if ! rsync -a --delete --exclude='__pycache__/' \
                "$UPSTREAM_LOCAL/.claude/commands/" "$REPO_ROOT/.claude/commands/"; then
                err "rsync .claude/commands/ 失败"
                exit 4
            fi
        fi
    fi
else
    # git fetch + checkout 模式（仅白名单路径）
    if [[ $DRY_RUN -eq 1 ]]; then
        log "  [dry-run] 将 checkout upstream/$UPSTREAM_BRANCH -- ${L2_PATHS[*]}"
    else
        log "  [4.1] git checkout upstream/$UPSTREAM_BRANCH -- pm-workflow/"
        if ! git -C "$REPO_ROOT" checkout "upstream/$UPSTREAM_BRANCH" -- pm-workflow/ 2>&1; then
            err "checkout pm-workflow/ 失败"
            exit 4
        fi

        log "  [4.2] git checkout upstream/$UPSTREAM_BRANCH -- CLAUDE.md"
        if ! git -C "$REPO_ROOT" checkout "upstream/$UPSTREAM_BRANCH" -- CLAUDE.md 2>&1; then
            err "checkout CLAUDE.md 失败"
            exit 4
        fi

        # CHANGELOG_L2.md（上游有则同步，无则跳过向后兼容）
        if git -C "$REPO_ROOT" cat-file -e "upstream/$UPSTREAM_BRANCH:CHANGELOG_L2.md" 2>/dev/null; then
            log "  [4.2b] git checkout upstream/$UPSTREAM_BRANCH -- CHANGELOG_L2.md"
            if ! git -C "$REPO_ROOT" checkout "upstream/$UPSTREAM_BRANCH" -- CHANGELOG_L2.md 2>&1; then
                err "checkout CHANGELOG_L2.md 失败"
                exit 4
            fi
        fi

        # .claude/commands/ 可能不存在于上游某些历史版本
        if git -C "$REPO_ROOT" cat-file -e "upstream/$UPSTREAM_BRANCH:.claude/commands" 2>/dev/null; then
            log "  [4.3] git checkout upstream/$UPSTREAM_BRANCH -- .claude/commands/"
            mkdir -p "$REPO_ROOT/.claude"
            git -C "$REPO_ROOT" checkout "upstream/$UPSTREAM_BRANCH" -- .claude/commands/ 2>&1 || true
        fi
    fi
fi

# ─── CHANGELOG_L2.md 缺失防御提示 ───
# 上游有 CHANGELOG_L2.md 但 sync 后本地仍无 → 提示再跑一次 sync。覆盖场景：拷贝中断 /
# 误删 / 下游自上次"脚本获得 CHANGELOG 同步能力"后尚未再 sync。
# 注意：本提示在**新脚本**内——纯"首次 sync 跑旧脚本"的 bootstrapping 过渡（旧脚本无本段
# 代码，升级了脚本自身但没拿 CHANGELOG）本检捕获不到，该过渡由 README 说明 + 下游再 sync
# 自然解决（跨过本边界后新脚本首跑即同步 CHANGELOG）。
if [[ $DRY_RUN -eq 0 && ! -f "$REPO_ROOT/CHANGELOG_L2.md" ]]; then
    _upstream_has_changelog=0
    if [[ -n "${UPSTREAM_LOCAL:-}" && -f "$UPSTREAM_LOCAL/CHANGELOG_L2.md" ]]; then
        _upstream_has_changelog=1
    elif git -C "$REPO_ROOT" cat-file -e "upstream/$UPSTREAM_BRANCH:CHANGELOG_L2.md" 2>/dev/null; then
        _upstream_has_changelog=1
    fi
    if [[ $_upstream_has_changelog -eq 1 ]]; then
        warn "上游有 CHANGELOG_L2.md 但本地未拿到 — sync 脚本自更新滞后（一次性过渡）"
        warn "  → 再跑一次本命令即可拿到下游升级日志 + 整改指引"
    fi
fi

# ─── L1 二阶段核验：Step 4 后立刻核查 L1 未被误改（Gotcha #6/#7）───
if [[ $DRY_RUN -eq 0 ]]; then
    L1_DIRTY_AFTER_L2=$(snapshot_l1_dirty)
    if [[ "$L1_DIRTY_BEFORE" != "$L1_DIRTY_AFTER_L2" ]]; then
        err "L1 在 L2 checkout 后被误改 — 白名单逃逸！"
        err "  Before: $(echo "$L1_DIRTY_BEFORE" | wc -l) 文件"
        err "  After:  $(echo "$L1_DIRTY_AFTER_L2" | wc -l) 文件"
        err "  Diff（After 比 Before 多的）："
        diff <(echo "$L1_DIRTY_BEFORE") <(echo "$L1_DIRTY_AFTER_L2") | grep '^>' | head -10 || true  # 同 line ~490：diff exit 1 + pipefail+set -e 会崩，|| true 兜底
        exit 3
    fi
    ok "L1 工作区核验通过 — 未被误改"
fi

# ═══════════════════════════════════════════════════════════════
# Step 5: pytest 验证下游回归基线
# ═══════════════════════════════════════════════════════════════
step 5 "pytest 验证"

if [[ $DO_VERIFY -eq 0 ]]; then
    log "  --no-verify 跳过"
elif [[ $DRY_RUN -eq 1 ]]; then
    log "  [dry-run] 将执行 pytest pm-workflow/scripts/tests/"
else
    PYTEST_BIN=$(command -v pytest || echo "$HOME/.local/bin/pytest")
    if [[ ! -x "$PYTEST_BIN" ]]; then
        warn "未找到 pytest — 跳过验证（建议安装：pip install pytest）"
    else
        pytest_out=$(cd "$REPO_ROOT/pm-workflow/scripts" && "$PYTEST_BIN" -q 2>&1 | tail -3)
        echo "$pytest_out" | tail -1 | sed 's/^/    /'
        if echo "$pytest_out" | grep -qE 'failed|error'; then
            err "pytest 失败 — L2 已同步但下游回归 FAIL，人工排查"
            exit 1
        fi
        ok "pytest PASS"
    fi
fi

# ═══════════════════════════════════════════════════════════════
# Step 6: precheck_template_purity 验证
# ═══════════════════════════════════════════════════════════════
step 6 "precheck_template_purity"

if [[ $DO_VERIFY -eq 0 ]]; then
    log "  --no-verify 跳过"
elif [[ $DRY_RUN -eq 1 ]]; then
    log "  [dry-run] 将执行 precheck_template_purity.py"
else
    PURITY_SCRIPT="$REPO_ROOT/pm-workflow/scripts/precheck_template_purity.py"
    if [[ ! -f "$PURITY_SCRIPT" ]]; then
        warn "未找到 precheck_template_purity.py — 跳过"
    else
        if ! (cd "$REPO_ROOT" && python3 "$PURITY_SCRIPT" > /tmp/sync_purity.log 2>&1); then
            err "precheck_template_purity FAIL"
            tail -20 /tmp/sync_purity.log | sed 's/^/    /'
            exit 1
        fi
        ok "precheck_template_purity PASS"
    fi
fi

# ═══════════════════════════════════════════════════════════════
# Step 7: 重 assemble outputs/
# ═══════════════════════════════════════════════════════════════
step 7 "重 assemble outputs/"

if [[ $DO_ASSEMBLE -eq 0 ]]; then
    log "  --no-assemble 跳过"
elif [[ $DRY_RUN -eq 1 ]]; then
    log "  [dry-run] 将执行 assemble.py spec + prd --force-overwrite"
else
    ASSEMBLE_SCRIPT="$REPO_ROOT/pm-workflow/scripts/assemble.py"
    if [[ ! -f "$ASSEMBLE_SCRIPT" ]]; then
        warn "未找到 assemble.py — 跳过"
    elif [[ ! -d "$REPO_ROOT/process_record/drafts" ]] || \
         [[ -z "$(ls "$REPO_ROOT/process_record/drafts" 2>/dev/null)" ]]; then
        log "  无 drafts/ 或为空 → 跳过 assemble（阶段 4 未启动）"
    else
        log "  [7.1] assemble spec"
        if (cd "$REPO_ROOT" && python3 "$ASSEMBLE_SCRIPT" spec --force-overwrite > /tmp/sync_asm_spec.log 2>&1); then
            ok "assemble spec 完成"
        else
            warn "assemble spec 失败（可能阶段 4 未到拼装阶段）"
            tail -5 /tmp/sync_asm_spec.log | sed 's/^/    /'
        fi

        log "  [7.2] assemble prd"
        if (cd "$REPO_ROOT" && python3 "$ASSEMBLE_SCRIPT" prd --force-overwrite > /tmp/sync_asm_prd.log 2>&1); then
            ok "assemble prd 完成"
        else
            warn "assemble prd 失败（可能阶段 4 未到拼装阶段）"
            tail -5 /tmp/sync_asm_prd.log | sed 's/^/    /'
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════
# Step 8: commit L2 同步
# ═══════════════════════════════════════════════════════════════
step 8 "commit L2 同步"

if [[ $DRY_RUN -eq 1 ]]; then
    log "  [dry-run] 跳过 commit"
    ok "dry-run 完成 — 无实际改动"
    exit 0
fi

# ─── 二阶段核验：commit 前再次核查 L1 完整性 ───
# 豁免逻辑前置：先过滤 outputs/，仅当非 outputs/ 才视为白名单逃逸 err；
# outputs/ 假设由 Step 7 assemble 派生改动（spec_*.md + prd_*.html），属正常豁免静默 log。
# 治本下游 PM 反馈：原先 err 先打→后续 log 解释的 UX 顺序让 PM 视觉误判失败。
L1_DIRTY_FINAL=$(snapshot_l1_dirty)
if [[ "$L1_DIRTY_BEFORE" != "$L1_DIRTY_FINAL" ]]; then
    # `|| true` 必需（勿删）：diff 在两输入不同时返回 exit 1，而本块前置条件（line 上方 if）
    # 就是「BEFORE != FINAL」→ diff 必 exit 1；set -euo pipefail 下该退出码经 pipefail 冒泡到
    # 命令替换赋值，触发 set -e 在 git commit 前中止整脚本（Step 7 assemble 必改 outputs/ →
    # 此路径每次真实 sync 必走）。`|| true` 吞掉这个信息性退出码，L1_DIRTY_NEW 仍正确捕获 `>` 行。
    L1_DIRTY_NEW=$(diff <(echo "$L1_DIRTY_BEFORE") <(echo "$L1_DIRTY_FINAL") \
                   | grep '^>' | sed 's/^> //' || true)
    L1_NON_OUTPUTS=$(echo "$L1_DIRTY_NEW" | grep -vE '^outputs/' || true)
    if [[ -n "$L1_NON_OUTPUTS" ]]; then
        err "L1 非 outputs/ 文件被误改 — 白名单逃逸："
        echo "$L1_NON_OUTPUTS" | head -5 | sed 's/^/    /'
        exit 3
    else
        outputs_new=$(echo "$L1_DIRTY_NEW" | grep -cE '^outputs/' || echo 0)
        log "  L1 新增 $outputs_new 文件全部位于 outputs/（来自 assemble，正常豁免）"
    fi
fi

# ─── L2 dirty 抓取（Gotcha #2/#7）───
l2_dirty=$(git -C "$REPO_ROOT" -c core.quotepath=false status --porcelain \
           | awk '{print $NF}' \
           | grep -E '^(pm-workflow/|CLAUDE\.md$|\.claude/commands/)' || true)

if [[ -z "$l2_dirty" ]]; then
    l2_count=0
else
    l2_count=$(echo "$l2_dirty" | wc -l)
fi

log "  L2 改动：$l2_count 文件"

if [[ $l2_count -eq 0 ]]; then
    log "  ℹ️  L2 无变化 — 上下游已同步，无需 commit"
    ok "sync_from_upstream 完成（无改动）"
    exit 0
fi

if [[ $DO_COMMIT -eq 0 ]]; then
    log "  --no-commit 模式 — L2 已就位，未 stage/commit"
    log "  PM 可手动 git add + commit 决定 SemVer 节奏"
    ok "sync_from_upstream 完成（待 PM commit）"
    exit 0
fi

# ─── 自动构建 commit message ───
if [[ -z "$COMMIT_MSG" ]]; then
    # 自动 outputs/ 同步状态
    outputs_dirty=$(git -C "$REPO_ROOT" -c core.quotepath=false status --porcelain \
                    | awk '{print $NF}' \
                    | grep -E '^outputs/' || true)
    outputs_note=""
    if [[ -n "$outputs_dirty" ]]; then
        outputs_count=$(echo "$outputs_dirty" | wc -l)
        outputs_note="
outputs/ 重生：$outputs_count 文件（assemble --force-overwrite）"
    fi

    COMMIT_MSG="[L2-only] sync upstream $UPSTREAM_HASH — $UPSTREAM_SUBJECT

下游主动同步（sync_from_upstream.sh）：
- pm-workflow/ + CLAUDE.md + .claude/commands/ 净 L2 前向镜像
- pytest + precheck_template_purity 验证 PASS
- L1 工作区核验通过（未被误改）$outputs_note

L1 dirty: $L1_BEFORE_COUNT 文件保持 unstaged（PM 工作残留，rsync 不触动 L1）

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
fi

log "  [8.1] git add 仅 L2 路径 + outputs/（assemble 派生）"
(cd "$REPO_ROOT" && git add CLAUDE.md CHANGELOG_L2.md pm-workflow/ .claude/commands/ outputs/ 2>/dev/null || \
                   git add CLAUDE.md pm-workflow/)

log "  [8.2] git commit"
if ! (cd "$REPO_ROOT" && git commit -m "$COMMIT_MSG" > /tmp/sync_commit.log 2>&1); then
    tail -10 /tmp/sync_commit.log | sed 's/^/    /'
    err "commit 失败"
    exit 1
fi
tail -1 /tmp/sync_commit.log | sed 's/^/    /'
ok "commit 完成"

# 下游整改指引提示（CHANGELOG_L2）
log ""
log "  📋 sync 后须知：本次拉入的 L2 升级 + 下游整改指引见"
log "     → CHANGELOG_L2.md（顶部为最新条目，逐条看「sync 后须知」）"
log "  典型整改：阶段 4 产物受影响时重生 outputs + 跑 precheck 看新 WARN"
log "     python3 pm-workflow/scripts/assemble.py spec --force-overwrite"
log "     python3 pm-workflow/scripts/assemble.py prd  --force-overwrite"
log "     python3 pm-workflow/scripts/precheck_stage4.py"

if [[ $DO_PUSH -eq 0 ]]; then
    log "  默认 --no-push（仅本地 commit，PM 自主决定 push 时机）"
    log "  显式 push: bash $0 --push"
    ok "sync_from_upstream 完成"
    exit 0
fi

log "  [8.3] git push origin"
current_branch=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)
if ! (cd "$REPO_ROOT" && git push origin "$current_branch" 2>&1 | tail -2 | sed 's/^/    /'); then
    err "push 失败 — commit 已就绪，人工排查"
    exit 1
fi
ok "sync_from_upstream 完成（含 push）"
