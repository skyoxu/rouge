---
PRD-ID: PRD-rouge-manager
Title: 08 章功能纵切索引（契约与测试对齐）
Status: Active
ADR-Refs: []
Arch-Refs:
  - CH01
  - CH03
Test-Refs:
  - Game.Core.Tests/Docs/OverlayTestRefsTests.cs
  - Game.Core.Tests/Domain/CardTests.cs
---


## 非 SSoT 声明
- 本 overlays 目录仅用于“功能纵切的架构口径/验收骨架/导航”。
- 任务真相（SSoT）以任务文件为准：`.taskmaster/tasks/tasks.json` 与视图任务文件（如 `.taskmaster/tasks/tasks_gameplay.json`）。
- PRD 仅作参考；本目录不承载任务拆分、排期或实现细节。

## 编辑纪律（最小规则）
- 新增/删除/重命名任一 `08/*.md`：必须同步更新本页 `## Catalog`（保证导航不漂移）。
- 修改任一页面口径：必须检查其 Front-Matter 的 `Status/ADR-Refs/Arch-Refs/Test-Refs` 是否仍准确；`Test-Refs` 允许空数组但必须存在。
- 提交前必须运行 overlays 自检并留痕到 `logs/ci/<YYYY-MM-DD>/overlay-08-audit/`（至少包含 `summary.json` 与 `summary.log`；命令：`py -3 scripts/python/generate_overlay_08_audit.py --prd-id PRD-rouge-manager`）。
- 禁止在 08 页面复制 Base/ADR 的阈值与策略；只允许引用。
## Scope
- 本页是 08 章的目录与防误用提示，便于快速找到对应页面。

## Non-goals
- 不承载任务列表、代码细节或执行步骤；只提供导航与口径优先级。

## Catalog
- `08-Feature-Slice-Minimum-Playable-Loop.md`: 最小可玩闭环的纵切验收骨架，用于统一口径。
- `08-Contracts-Security.md`: 纵切的安全落点（引用 ADR/Base），避免重复。
- `08-Contracts-Allowed-External-Hosts.md`: 外链与主机白名单相关的纵切对齐页。
- `08-Contracts-Quality-Metrics.md`: 纵切的质量指标与门禁落点（引用 ADR/Base）。
- `08-Contracts-CloudEvent.md`: 事件封装对象与关键字段约束口径说明。
- `08-Contracts-CloudEvents-Core.md`: 事件系统核心概念与公共约束。
- `08-Contracts-Rouge-Run-Events.md`: 跑局过程的事件类型索引页。
- `08-Contracts-Rouge-Run-State.md`: 存档与跑局状态快照的 DTO 索引页。
- `08-Contracts-Rouge-Shop-DTOs.md`: 商店相关的 DTO 索引页。
- `ACCEPTANCE_CHECKLIST.md`: 交付前自检清单（Template），用于防遗漏。

## Cross-links
- `Game.Core/Contracts/DomainEvent.cs`: 事件封装的参考位置（代码为准）。
- `Game.Godot/Adapters/EventBusAdapter.cs`: 引擎适配层的参考位置（代码为准）。
