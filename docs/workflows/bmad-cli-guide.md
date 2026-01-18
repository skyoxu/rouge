# BMAD CLI（Windows）使用指南

本仓库的 BMAD 使用目标是：在 **PowerShell 执行策略阻止 `npm.ps1/npx.ps1`** 的环境下，仍能稳定调用已安装的 `bmad` 命令，并把证据写入 `logs/**` 便于审计与排障。

## 前提

- 你已在本机以用户级方式安装 BMAD（例如 `bmad-method@6.x`），并且 `bmad` 在 PATH 上可用。
- 本仓库不把 BMAD 作为硬依赖门禁；BMAD 属于“可选的辅助工具”。

## 推荐用法（Windows + Python）

在仓库根目录运行（统一入口，避免触发 `npm.ps1`）：

```bat
py -3 scripts/python/run_bmad.py -- --version
```

查看帮助：

```bat
py -3 scripts/python/run_bmad.py -- --help
```

执行 BMAD 安装子命令（示例）：

```bat
py -3 scripts/python/run_bmad.py -- install
```

## 日志与取证（SSoT：logs/**）

每次执行会产出到：

- `logs/ci/<YYYY-MM-DD>/bmad/<run-id>/meta.json`
- `logs/ci/<YYYY-MM-DD>/bmad/<run-id>/stdout.log`
- `logs/ci/<YYYY-MM-DD>/bmad/<run-id>/stderr.log`
- `logs/ci/<YYYY-MM-DD>/bmad/<run-id>/summary.json`
- `logs/ci/<YYYY-MM-DD>/bmad/<run-id>/summary.log`

## 常见问题

### 1) PowerShell 里直接运行 `npm` 报错 “running scripts is disabled”

这是执行策略阻止 `npm.ps1/npx.ps1`。本仓库建议用：

- `py -3 scripts/python/run_bmad.py ...`（BMAD）
- 或在 PowerShell 中用 `cmd /c npm ...`（如你必须直接用 npm）

