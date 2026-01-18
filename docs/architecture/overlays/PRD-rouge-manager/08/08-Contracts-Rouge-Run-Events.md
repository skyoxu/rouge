---
PRD-ID: PRD-rouge-manager
Title: Rouge Run 事件（Rouge Run Events）契约更新
Status: Proposed
ADR-Refs:
  - ADR-0004
  - ADR-0005
  - ADR-0020
  - ADR-0021
Arch-Refs:
  - CH01
  - CH03
Test-Refs:
  - Game.Core.Tests/Services/EventBusTests.cs
  - Tests.Godot/tests/Adapters/test_event_bus_adapter.gd
---

## Scope
- 本页列出跑局过程中的事件类型与其用途分类，便于检索与讨论。

## Non-goals
- 不作为实现源码的唯一依据；具体字段以代码为准。

## References
- ADR-Refs: ADR-0004, ADR-0005, ADR-0020, ADR-0021
- Arch-Refs: CH01, CH03
- Related: `_index.md`

本页为功能纵切（08 章）对应“最小可玩闭环（MVP Run）”的领域事件清单建议与验收口径。

变更意图（引用，不复制口径）

- 事件命名遵循统一规范 `<boundedContext>.<entity>.<action>`（ADR-0004）
- 质量门禁与变更追踪引用 ADR-0005
- 契约位置统一：`Game.Core/Contracts/**`（ADR-0020），并保持 Core 不依赖 Godot（ADR-0021）

影响范围

- 事件封装：`Game.Core/Contracts/DomainEvent.cs`（CloudEvents 风格）
- 事件桥接：`Game.Godot/Adapters/EventBusAdapter.cs`（Signal 输出给场景）
- 受影响模块：Run/Map/Battle/Card/Reward 的状态机推进与 UI 同步（参见 prd.txt）

验收要点（就地）

- xUnit 与 GdUnit4 对事件发布/桥接路径有代表性覆盖（见 Test-Refs）
- 事件类型必须落在 `core.*.*` / `screen.*.*` / `ui.menu.*` 三类前缀之一（ADR-0004）

## T2 最小事件集合（建议）

> 说明：本清单来源于 prd.txt 的“闭环流程 + 回合机制 + 统一效果系统”要求；字段以“最少可追溯”为目标，避免为 UI 动画引入逻辑依赖。

### Run / Map

- **RunStarted** (`core.run.started`)
  - 触发时机：开始新局（确定 RunSeed / 初始队伍与牌组后）
  - 字段建议：RunId, RunSeed, PartySnapshot, StartedAt
- **MapGenerated** (`core.map.generated`)
  - 触发时机：地图生成完成（节点图落地）
  - 字段建议：RunId, MapId, NodeCount, Depth, GeneratedAt
- **MapNodeSelected** (`core.map.node.selected`)
  - 触发时机：玩家选择下一节点（且满足连线可达规则）
  - 字段建议：RunId, NodeId, NodeType, Depth, SelectedAt
- **MapNodeCompleted** (`core.map.node.completed`)
  - 触发时机：节点内容完成并回到地图
  - 字段建议：RunId, NodeId, NodeType, Result, CompletedAt

### Encounter / Battle

- **BattleStarted** (`core.battle.started`)
  - 触发时机：进入战斗节点并初始化战斗实例（生成敌群与 Intent）
  - 字段建议：RunId, BattleId, EncounterId, EnemyGroupId, StartedAt
- **PlayerTurnStarted** (`core.battle.turn.player.started`)
  - 触发时机：玩家回合开始（重置能量/抽牌/OnTurnStart 结算后）
  - 字段建议：RunId, BattleId, Turn, HeroesEnergy, DrawCount
- **CardPlayed** (`core.card.played`)
  - 触发时机：卡牌通过校验并提交给 EffectResolver
  - 字段建议：RunId, BattleId, Turn, HeroId, CardId, Targets
- **CardDrawn** (`core.card.drawn`)
  - ?????? DrawPile ???? Hand ?
  - ???RunId, BattleId, Turn, HeroId, CardInstanceId, CardDefinitionId, DrawOrder
  - ?????`Game.Core/Contracts/Rouge/Cards/CardDrawn.cs`
- **CardDiscarded** (`core.card.discarded`)
  - ?????? Hand ???? DiscardPile ?
  - ???RunId, BattleId, Turn, HeroId, CardInstanceId, CardDefinitionId
  - ?????`Game.Core/Contracts/Rouge/Cards/CardDiscarded.cs`

- **EffectsResolved** (`core.effect.resolved`)
  - 触发时机：一张卡/一次敌方 Intent 的效果指令序列完成结算
  - 字段建议：RunId, BattleId, SourceType, Commands, DeltaSummary
- **EnemyTurnStarted** (`core.battle.turn.enemy.started`)
  - 触发时机：敌方回合开始（按 Intent 执行）
  - 字段建议：RunId, BattleId, Turn, IntentSummary
- **BattleEnded** (`core.battle.ended`)
  - 触发时机：胜负判定结束（敌全灭/队伍全灭）
  - 字段建议：RunId, BattleId, Result, EndedAt

### Reward / Shop / Rest / Event
> Shop 交互通常需要 DTO（库存/报价/移除费用等）：见 `08-Contracts-Rouge-Shop-DTOs.md`；购买/移除等选择导致的状态变化应以 `EffectsResolved`（`core.effect.resolved`）回传并驱动 UI 刷新。


- **RewardOffered** (`core.reward.offered`)
  - 触发时机：战斗胜利后生成奖励候选（如 3 选 1 卡牌）
  - 字段建议：RunId, NodeId, Rewards
- **RewardSelected** (`core.reward.selected`)
  - 触发时机：玩家选择奖励并落盘到牌组/金币
  - 字段建议：RunId, NodeId, Selection, AppliedAt
- **EventChoiceResolved** (`core.event.choice.resolved`)
  - 触发时机：事件节点选择后，effects 指令集执行完毕
  - 字段建议：RunId, EventId, ChoiceId, DeltaSummary

### Run End

- **RunEnded** (`core.run.ended`)
  - 触发时机：击败 Boss 或全灭
  - 字段建议：RunId, Outcome, EndedAt, Summary

> 约定：当这些事件从“清单建议”进入“代码实现”时：
> - 契约落盘到 `Game.Core/Contracts/<Module>/`（per ADR-0020）
> - UI/Godot 侧仅订阅，不回写逻辑（参见 prd.txt 5.4）

