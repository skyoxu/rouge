# Rouge 跑局存档 DTO 契约（Run State）

## 目的与边界

本页定义“跑局存档/读档”所需的 **DTO 契约**（可序列化、可单测、无 Godot 依赖），用于 `Game.Core` 与适配层（如 DataStoreAdapter）之间交换与持久化跑局状态。

约束：
- 契约仅使用 BCL 类型（`string/int/DateTimeOffset/...`），不得引用 `Godot.*`。
- DTO 字段必须稳定且可版本演进（迁移逻辑在实现层，不在契约层）。

## DTO

### RunGameStateSnapshot

- 用途：存档文件 `user://saves/current_run.json` 的“跑局状态快照”根对象（仅 DTO，不含业务逻辑）。
- 字段（最小集合）：
  - `Version:int`：存档结构版本号（用于迁移策略判定）。
  - `RunSeed:int`：随机种子（用于可重现）。
  - `CurrentAct:int`：章节号（T2 可先固定为 1）。
  - `Map:AdventureMapSnapshot`：地图进度快照（当前节点与已完成节点集合）。
  - `Party:PartySnapshot`：队伍快照（与事件契约复用）。
  - `Statistics:RunStatisticsSnapshot?`：可选统计（用于 UI 展示/诊断）。
  - `SavedAtUtc:DateTimeOffset`：存档时间戳（UTC）。
- 契约位置：`Game.Core/Contracts/Rouge/Run/RunGameStateSnapshot.cs`

### AdventureMapSnapshot

- 用途：地图进度快照（跑局层面的“你走到哪了”）。
- 字段：
  - `MapId:string`
  - `Depth:int`
  - `CurrentNodeId:string`
  - `CompletedNodeIds:string[]`
  - `UpdatedAt:DateTimeOffset`
- 契约位置：`Game.Core/Contracts/Rouge/Run/AdventureMapSnapshot.cs`

### RunStatisticsSnapshot

- 用途：跑局统计（可选）。
- 字段：
  - `BattlesWon:int`
  - `BattlesLost:int`
  - `NodesCompleted:int`
  - `GoldDelta:int`
  - `CardsAdded:int`
  - `CardsRemoved:int`
  - `CardsUpgraded:int`
- 契约位置：`Game.Core/Contracts/Rouge/Run/RunStatisticsSnapshot.cs`

## ADR / 章节引用

- ADR-0004（事件总线与契约）：约束契约是跨层边界的单一事实源。
- ADR-0006（数据存储）：存档结构需要稳定、可迁移、可审计。

## Test-Refs

- `Game.Core.Tests/Contracts/RougeRunGameStateSnapshotContractsTests.cs`

