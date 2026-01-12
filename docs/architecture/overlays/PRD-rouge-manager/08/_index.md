---
PRD-ID: PRD-rouge-manager
Title: 08 章功能纵切索引（契约与测试对齐）
Updated: true
Arch-Refs:
  - CH01
  - CH03
Test-Refs:
  - Game.Core.Tests/Docs/OverlayTestRefsTests.cs
  - Game.Core.Tests/Domain/CardTests.cs
---

本目录聚合 PRD-rouge-manager（单机单人卡牌构筑RPG：T2 最小可玩闭环）的功能纵切页面与对应测试引用（仅引用 01/02/03 章口径，不在此复制阈值/策略）。

- 最小可玩闭环（MVP Run）— 见 `08-Feature-Slice-Minimum-Playable-Loop.md`
- 外链白名单（AllowedDomains / ALLOWED_EXTERNAL_HOSTS）— 见 `08-Contracts-Allowed-External-Hosts.md`
- CloudEvent 契约 — 见 `08-Contracts-CloudEvent.md`
- CloudEvents Core 契约 — 见 `08-Contracts-CloudEvents-Core.md`
- Rouge 跑局存档 DTO 契约 — 见 `08-Contracts-Rouge-Run-State.md`
- Rouge Run 事件契约 — 见 `08-Contracts-Rouge-Run-Events.md`
- Rouge DTO：Shop Inventory & Pricing（商店库存与定价）— 见 `08-Contracts-Rouge-Shop-DTOs.md`
- 质量指标（Quality Metrics）— 见 `08-Contracts-Quality-Metrics.md`
- 安全契约 — 见 `08-Contracts-Security.md`
- 验收清单（PR 交付前自检）— 见 `ACCEPTANCE_CHECKLIST.md`

示例：当前 Godot+C# 契约引用

- 事件封装（CloudEvents 风格）：`Game.Core/Contracts/DomainEvent.cs`（per ADR-0004/ADR-0020）
- 事件桥接（Signal）：`Game.Godot/Adapters/EventBusAdapter.cs`（per ADR-0004/ADR-0022）

