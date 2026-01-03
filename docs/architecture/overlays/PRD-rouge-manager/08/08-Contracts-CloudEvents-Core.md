---
PRD-ID: PRD-rouge-manager
Title: CloudEvents Core 契约更新
Arch-Refs:
  - CH01
  - CH03
ADR-Refs:
  - ADR-0004
  - ADR-0005
  - ADR-0003
Test-Refs:
  - Game.Core.Tests/Services/EventBusTests.cs
  - Tests.Godot/tests/Adapters/test_event_bus_adapter.gd
Contracts-Refs:
  - Game.Core/Contracts/DomainEvent.cs
  - Game.Core/Services/EventBus.cs
Status: Proposed
---

本页为功能纵切（08 章）对应“CloudEvents Core”契约的变更登记与验收要点（仅引用 01/02/03 章口径，不复制阈值/策略）。

变更意图（引用）

- 事件封装字段统一与命名规范：见 ADR-0004（事件与契约统一口径）。
- 可观测性与发布健康：见 ADR-0003（结构化日志、Release Health）。
- 质量门禁与一致性校验：见 ADR-0005（质量门禁）。

影响范围

- 合同文件：`Game.Core/Contracts/DomainEvent.cs`
- 受影响模块：事件发布/订阅、日志与可观测性链路

验收要点

- 基础事件封装可用且字段完整（见 Test-Refs）
- 任何新增“Core”事件仅登记影响与测试，不在 08 复制阈值/策略

