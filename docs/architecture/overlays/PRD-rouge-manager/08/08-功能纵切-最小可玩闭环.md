---
PRD-ID: PRD-rouge-manager
Story-ID: PRD-ROUGE-T2-VS-0001
Title: 功能纵切 — 最小可玩闭环（MVP Run）
Status: Active
ADR-Refs:
  - ADR-0018  # Godot runtime & distribution
  - ADR-0011  # Windows-only platform & CI
  - ADR-0004  # Event bus & contracts (CloudEvents)
  - ADR-0020  # Contract location standardization
  - ADR-0021  # C# domain layer architecture
  - ADR-0024  # Godot test strategy
  - ADR-0006  # Data storage (SQLite)
  - ADR-0005  # Quality gates
  - ADR-0015  # Performance budgets
  - ADR-0003  # Observability & release health
  - ADR-0019  # Godot security baseline
Test-Refs:
  # Core 领域逻辑（xUnit）
  - Game.Core.Tests/Services/EventBusTests.cs
  - Game.Core.Tests/State/GameStateMachineTests.cs
  # 场景与 UI（GdUnit4）
  - Tests.Godot/tests/Scenes/Smoke/test_main_scene_smoke.gd
  - Tests.Godot/tests/Integration/test_screen_navigation_flow.gd
  - Tests.Godot/tests/Adapters/test_event_bus_adapter.gd
  # 安全/审计（GdUnit4）
  - Tests.Godot/tests/Integration/Security/test_security_http_allowed_audit.gd
  - Tests.Godot/tests/Integration/Security/test_security_http_audit.gd
  - Tests.Godot/tests/Security/Hard/test_db_open_denied_writes_audit_log.gd
  # CI / Smoke 汇总
  - logs/ci/<date>/ci-pipeline-summary.json
  - logs/e2e/<date>/smoke/selfcheck-summary.json
---

本页仅作为“功能纵切（08 章）”对 Rouge 项目的 **T2 最小可玩闭环（MVP Run）** 的实现约束与测试挂钩索引：

- 阈值/策略/门禁等跨切面口径仅“引用”Base 与 ADR，不在 08 复制：
  - 安全与 Godot 基线：参见 CH02 与 ADR-0019
  - 事件/契约统一：参见 CH01/CH03 与 ADR-0004、ADR-0020、ADR-0022
  - 质量门禁/发布健康与性能预算：参见 CH03/CH07/CH09 与 ADR-0005、ADR-0003、ADR-0015
- 具体事件/DTO 与端口定义一律以 `Game.Core/Contracts/<Module>/` 为 SSoT（per ADR-0020）；08 仅登记功能影响与测试范围。
- 测试入口按 Test-Refs 落地（xUnit + GdUnit4），CI 会据此做就地验收与追溯。

## 功能闭环范围（来自 prd.txt）

- 新局（Run）开始：选择队伍/初始构筑（T2 可简化为固定队伍/预置牌组）
- 地图推进：分层节点图（战斗/事件/休息/商店/精英/Boss），节点完成后回到地图继续选择
- 战斗回合：抽牌/能量/出牌/目标选择/效果结算；敌方 Intent 可见且执行
- 奖励与构筑：战斗胜利后选牌入组、获得金币；休息回血/升级卡；商店买牌/移除卡
- 结算：击败 Boss 进入通关结算；全灭进入失败结算；均可快速重开下一局

## 统一效果系统（T2 最关键约束）

卡牌效果、敌人意图、事件选项、奖励结算必须复用同一套“效果指令 -> EffectResolver -> 状态/数值变更”（详见 prd.txt 5.5）。

T2 指令最小集（PRD 约束，建议以纯 C# 落地并可单测）：

- Damage(target, amount, type)
- GainBlock(target, amount)
- Heal(target, amount)
- ApplyStatus(target, statusId, stacks, duration)
- Draw(hero, n)
- ChangeEnergy(hero, delta)
- GainGold(amount) / LoseGold(amount)
- AddCardToDeck(hero, cardId)
- RemoveCardFromDeck(hero, cardId)
- UpgradeCardInDeck(hero, cardId)
- TriggerBattle(encounterId)（事件用，可选）
- SetFlag(flagId, value)（事件链预留）

## 事件与契约（概览）

事件命名遵循 ADR-0004 的 `<boundedContext>.<entity>.<action>`，在 Godot 变体中推荐：

- `core.<entity>.<action>`：领域事件（Run/Map/Battle/Card/Reward）
- `screen.<name>.<action>`：Screen 生命周期事件
- `ui.menu.<action>`：菜单命令事件

本功能纵切对应的领域事件清单与字段建议见：`08-Contracts-Rouge-Run-Events.md`。

示例：当前 Godot+C# 契约引用

- 事件封装（CloudEvents 风格）：`Game.Core/Contracts/DomainEvent.cs`
- 事件桥接（Signal）：`Game.Godot/Adapters/EventBusAdapter.cs`

注：如本闭环引入新的事件或契约，请先更新 `Game.Core/Contracts/<Module>/`（per ADR-0020），再在 Overlay/08 以“引用”方式登记变更，并补充/更新 Test-Refs。

