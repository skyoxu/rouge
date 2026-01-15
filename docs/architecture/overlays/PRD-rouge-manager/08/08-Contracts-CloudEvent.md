---
PRD-ID: PRD-rouge-manager
Title: CloudEvent 契约更新（事件封装与字段）
Status: Proposed
ADR-Refs:
  - ADR-0004
  - ADR-0005
  - ADR-0020
  - ADR-0022
Arch-Refs:
  - CH01
  - CH03
Test-Refs:
  - Game.Core.Tests/Services/EventBusTests.cs
  - Tests.Godot/tests/Adapters/test_event_bus_adapter.gd
---

## Scope
- 本页说明事件封装的对象结构与关键字段约束，便于对齐。

## Non-goals
- 不复制代码实现；不写扩展架构方案。

## References
- ADR-Refs: ADR-0004, ADR-0005, ADR-0020, ADR-0022
- Arch-Refs: CH01, CH03
- Related: `_index.md`

本页为功能纵切（08 章）对应“CloudEvent（DomainEvent）”契约更新的记录与验收口径。

变更意图（引用，不复制口径）

- 统一事件封装与字段必填校验（见 ADR-0004）；保持跨模块一致的事件命名规范 `<boundedContext>.<entity>.<action>`。
- 质量门禁引用 ADR-0005，相关测试与校验在 CI 执行。

影响范围

- 合同文件：`Game.Core/Contracts/DomainEvent.cs`
- 受影响模块：事件总线发布/订阅、日志关联与可观测性埋点、Godot Signal 桥接

验收要点（就地）

- xUnit 与 GdUnit4 对 EventBus/桥接路径有代表性覆盖（见 Test-Refs）
- 新增事件均使用 ADR-0004 的命名规则与前缀分层（core/screen/ui.menu）

