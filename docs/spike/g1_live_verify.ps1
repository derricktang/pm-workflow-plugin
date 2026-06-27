# G1 LIVE verification — run in a NORMAL PowerShell terminal (NOT inside Claude Code; nested = 403).
# Installs the built plugin from disk into a throwaway project and exercises the full chain:
#   plugin loads -> /pm: commands -> ${CLAUDE_PLUGIN_ROOT} in command bash -> SessionStart inject ->
#   subagent transitive path resolution -> products land in PROJECT (not the read-only cache).
$ErrorActionPreference = "Stop"
$repo = "E:\claude_code\projects\pm-workflow-plugin"
$plugin = "$repo\plugins\pm"
$proj = Join-Path $env:TEMP ("pmg1_" + (Get-Random))
New-Item -ItemType Directory -Force $proj | Out-Null
Set-Location $proj
Write-Host "=== scratch project: $proj ===" -ForegroundColor Cyan

$probe = @'
诊断探针，请严格执行并只输出标记行：
1) 列出你可见的、以 pm: 命名空间开头的斜杠命令名称，打印： CMDS=<逗号分隔列表>
2) 用 Bash 运行（确认 ${CLAUDE_PLUGIN_ROOT} 在命令体里展开 + doc_query 可达）：
   python3 "${CLAUDE_PLUGIN_ROOT}/pm-workflow/scripts/doc_query.py" outline "${CLAUDE_PLUGIN_ROOT}/pm-workflow/rules/agent_dispatch_protocol.md" | head -3
   打印： DOCQUERY=<OK 若有 outline 输出 / FAIL>
3) 派发一个 general-purpose subagent，prompt 里写明「框架根 = <你从 SessionStart 注入看到的插件根绝对路径>；所有 pm-workflow/... 相对它解析」，要求它 Read pm-workflow/rules/ssot_anchors.md 的前 5 行并回报成功与否。打印： SUBAGENT_READ=<OK/FAIL>
4) 用 Bash 创建 ./outputs/_g1probe.txt 写入 "hi"，再打印该文件绝对路径： PRODUCT_PATH=<路径>
最后打印： G1_DONE
'@

claude --plugin-dir "$plugin" -p $probe --permission-mode bypassPermissions --output-format text
Write-Host "`n=== expected ===" -ForegroundColor Cyan
Write-Host "CMDS includes newRequirement/nextStage/...; DOCQUERY=OK; SUBAGENT_READ=OK; PRODUCT_PATH under $proj (NOT under $plugin); G1_DONE"
