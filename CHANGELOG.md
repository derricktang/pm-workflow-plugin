# CHANGELOG

> Release notes only. For L2 framework evolution history, see [`CHANGELOG_L2.md`](CHANGELOG_L2.md).

---

## v1.0.0 — 插件化首发 (2026-06-28)

- **插件封装**：将 pm-workflow 框架打包为 Claude Code 插件（marketplace id: `pm`），通过 `claude plugin marketplace add` + `/plugin install pm@pm-workflow-market` 一键安装，不再需要手动复制目录。
- **双根隔离**：插件文件安装在只读 Claude 缓存目录；`process_record/`、`outputs/` 等运行时产物仍落在用户项目根目录，互不干扰，支持多产品仓库复用同一插件版本。
- **编排器脑注入**：SessionStart hook 在每次会话启动时自动注入工作流状态摘要（产品名 / 当前阶段 / 开放问题数 / 产物路径），无需用户手动唤起。
- **命令命名空间**：所有斜杠命令统一以 `/pm:` 为前缀（如 `/pm:newRequirement`、`/pm:nextStage`），避免与用户项目中其他插件命令冲突。
- **git-copy / syncUpstream 过渡通道保留**：原 `install_hooks` + `/pm:syncUpstream` 的 git-copy 安装方式标记为 **deprecated / 过渡**，现阶段仍可用，后续版本移除。

详细 L2 演进历史见 `CHANGELOG_L2.md`。
