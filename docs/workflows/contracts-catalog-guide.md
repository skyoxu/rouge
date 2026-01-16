# Contracts Catalog（代码契约目录）生成与使用指南

本指南只解决一件事：**快速盘点 `Game.Core/Contracts/**` 现有的代码契约，形成可对照的目录**。

注意：

- 这是“对照/浏览/审计留痕”的工具，不是门禁统计的一部分。
- 它不会修改任何代码或文档。
- overlays 是否回填契约信息、何时回填，以你的整体节奏为准；本脚本不推动、不绑定该节奏。

## 输出与留痕（SSoT：logs/**）

脚本会把报告输出到：

- `logs/ci/<YYYY-MM-DD>/contracts-catalog/contracts_inventory.json`
- `logs/ci/<YYYY-MM-DD>/contracts-catalog/catalog.md`
- `logs/ci/<YYYY-MM-DD>/contracts-catalog/summary.log`

这些产物用于排障、审计与归档，默认不要求入库。

## 推荐用法（Windows）

在仓库根目录运行：

```bat
py -3 scripts/python/generate_contracts_catalog.py
```

如果你把契约根目录放在其他位置，可指定：

```bat
py -3 scripts/python/generate_contracts_catalog.py --contracts-root Game.Core/Contracts
```

## 目录内容说明

`contracts_inventory.json` 会把 `Game.Core/Contracts/**` 的 C# 文件做简单归类：

- **Domain Events**：文件内包含 `public const string EventType = "..."` 的类型
- **DTO/Value Types**：`public record/class/enum` 且不包含 `EventType`
- **Interfaces**：`public interface ...`

并额外报告 `EventType` 的重复定义（仅提示，不作为 gate）。

## 相关但不同的工具（避免混淆）

- overlays/08 文档结构自检：`py -3 scripts/python/generate_overlay_08_audit.py --prd-id PRD-rouge-manager`
- overlays ↔ Contracts 回链校验（引用的契约文件是否存在）：`py -3 scripts/python/validate_contracts.py`
- Tasks/Views ↔ Contracts 的对照矩阵（更偏“计划/差距分析”）：`py -3 scripts/python/generate_contracts_plan_report.py`

