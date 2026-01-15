# Overlay 08 Catalog（契约页目录）生成与使用指南

本指南只解决一件事：**让 `docs/architecture/overlays/<PRD-ID>/08/` 自己可维护、可检索、可避免误用**。

这里的“Catalog/契约页目录”指的是 overlays/08 下 `08-Contracts-*.md` 这一类**文档页**的目录与审计输出。
它不生成、也不修改任何 `Game.Core/Contracts/**` 的代码契约（代码契约的建设与回填不在本阶段讨论）。

## 输出与留痕（SSoT：logs/**）

脚本会把报告输出到：

- `logs/ci/<YYYY-MM-DD>/overlay-08-audit/summary.json`
- `logs/ci/<YYYY-MM-DD>/overlay-08-audit/summary.log`
- `logs/ci/<YYYY-MM-DD>/overlay-08-audit/catalog.md`

这些产物用于排障、审计与归档，默认不要求入库。

## 推荐用法（Windows）

在仓库根目录运行：

```bat
py -3 scripts/python/generate_contracts_catalog.py --prd-id PRD-rouge-manager
```

常见场景：

- 你改了任意 `docs/architecture/overlays/PRD-rouge-manager/08/*.md`，想确认：
  - 每页 Front-Matter 是否包含最小 schema（PRD-ID/Title/Status/ADR-Refs/Arch-Refs/Test-Refs）
  - `_index.md` 的目录是否仍可用（无坏链接）
  - 文档中是否出现替换字符（U+FFFD，通常意味着编码或复制问题）

## 约束

- 本脚本只审计 overlays/08 的文档结构与链接，不做任务文件或代码契约的读写与同步。

## 生成产物与版本控制规则

- 生成产物默认写入 `logs/ci/<YYYY-MM-DD>/...`，作为 CI/本地审计证据。
- 如果你确实希望把“某个 PRD 的契约目录”放进 `docs/` 供团队查阅：
  - 建议写入 `docs/workflows/generated/`（默认被 `.gitignore` 忽略）。
  - 不建议把带业务项目名/事件列表的目录文档作为模板仓的长期文档入口，以免误导后续新项目。

