using System;
using System.Collections.Generic;
using System.Text.Json;
using FluentAssertions;
using Game.Core.Contracts;
using Game.Core.Contracts.Rouge.Battle;
using Game.Core.Contracts.Rouge.Cards;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Contracts.Rouge.Events;
using Game.Core.Contracts.Rouge.Map;
using Game.Core.Contracts.Rouge.Rewards;
using Game.Core.Contracts.Rouge.Run;
using Xunit;

namespace Game.Core.Tests.Contracts;

public class RougeRunEventContractsTests
{
    [Fact]
    public void EventType_constants_are_unique_and_use_core_prefix()
    {
        var types = new[]
        {
            RunStarted.EventType,
            MapGenerated.EventType,
            MapNodeSelected.EventType,
            MapNodeCompleted.EventType,
            BattleStarted.EventType,
            PlayerTurnStarted.EventType,
            CardPlayed.EventType,
            EffectsResolved.EventType,
            EnemyTurnStarted.EventType,
            BattleEnded.EventType,
            RewardOffered.EventType,
            RewardSelected.EventType,
            EventChoiceResolved.EventType,
            RunEnded.EventType,
        };

        types.Should().OnlyHaveUniqueItems();
        types.Should().AllSatisfy(t => t.Should().StartWith("core."));
    }

    [Fact]
    public void Rouge_run_event_payloads_can_be_serialized_to_json()
    {
        var now = new DateTimeOffset(2025, 01, 01, 0, 0, 0, TimeSpan.Zero);

        var payloads = new object[]
        {
            new RunStarted(
                RunId: "run_1",
                RunSeed: 123456,
                Party: new PartySnapshot(
                    HeroIds: new[] { "hero_a", "hero_b" },
                    StartingDeckCardIds: new[] { "card_strike", "card_defend" }
                ),
                StartedAt: now
            ),
            new MapGenerated(
                RunId: "run_1",
                MapId: "map_1",
                NodeCount: 12,
                Depth: 3,
                GeneratedAt: now
            ),
            new MapNodeSelected(
                RunId: "run_1",
                NodeId: "n_2_1",
                NodeType: MapNodeTypes.Battle,
                Depth: 2,
                SelectedAt: now
            ),
            new MapNodeCompleted(
                RunId: "run_1",
                NodeId: "n_2_1",
                NodeType: MapNodeTypes.Battle,
                Result: MapNodeResults.Ok,
                CompletedAt: now
            ),
            new BattleStarted(
                RunId: "run_1",
                BattleId: "battle_1",
                EncounterId: "encounter_1",
                EnemyGroupId: "group_slimes",
                StartedAt: now
            ),
            new PlayerTurnStarted(
                RunId: "run_1",
                BattleId: "battle_1",
                Turn: 1,
                HeroesEnergy: new[]
                {
                    new HeroEnergySnapshot(HeroId: "hero_a", Energy: 3),
                    new HeroEnergySnapshot(HeroId: "hero_b", Energy: 2),
                },
                DrawCount: 5
            ),
            new CardPlayed(
                RunId: "run_1",
                BattleId: "battle_1",
                Turn: 1,
                HeroId: "hero_a",
                CardId: "card_strike",
                Targets: new[]
                {
                    new TargetRef(TargetType: TargetTypes.Enemy, TargetId: "enemy_1"),
                }
            ),
            new EffectsResolved(
                RunId: "run_1",
                BattleId: "battle_1",
                SourceType: EffectSourceTypes.Card,
                Commands: new[]
                {
                    new EffectCommand(
                        Kind: "Damage",
                        Parameters: new Dictionary<string, string> { ["amount"] = "6", ["targetId"] = "enemy_1" }
                    ),
                },
                DeltaSummary: new EffectDeltaSummary(
                    DamageDealt: 6,
                    DamageTaken: 0,
                    BlockGained: 0,
                    HealingDone: 0,
                    GoldDelta: 0
                )
            ),
            new EnemyTurnStarted(
                RunId: "run_1",
                BattleId: "battle_1",
                Turn: 1,
                IntentSummary: new[]
                {
                    new EnemyIntentSnapshot(
                        EnemyId: "enemy_1",
                        IntentId: "attack",
                        TargetId: "hero_a",
                        Amount: 6,
                        Notes: null
                    ),
                }
            ),
            new BattleEnded(
                RunId: "run_1",
                BattleId: "battle_1",
                Result: BattleResults.Victory,
                EndedAt: now
            ),
            new RewardOffered(
                RunId: "run_1",
                NodeId: "n_2_1",
                Rewards: new[]
                {
                    new RewardOption(RewardType: RewardTypes.CardPick, ItemIds: new[] { "card_a", "card_b", "card_c" }, Amount: null),
                    new RewardOption(RewardType: RewardTypes.Gold, ItemIds: Array.Empty<string>(), Amount: 25),
                }
            ),
            new RewardSelected(
                RunId: "run_1",
                NodeId: "n_2_1",
                Selection: new RewardSelection(RewardType: RewardTypes.CardPick, SelectedItemId: "card_b", Amount: null),
                AppliedAt: now
            ),
            new EventChoiceResolved(
                RunId: "run_1",
                EventId: "event_shrine",
                ChoiceId: "pray",
                DeltaSummary: new EffectDeltaSummary(
                    DamageDealt: 0,
                    DamageTaken: 0,
                    BlockGained: 0,
                    HealingDone: 10,
                    GoldDelta: -25
                )
            ),
            new RunEnded(
                RunId: "run_1",
                Outcome: "victory",
                EndedAt: now,
                Summary: new RunSummary(
                    DepthReached: 3,
                    NodesCompleted: 7,
                    BattlesWon: 4,
                    BattlesLost: 0,
                    GoldDelta: 120,
                    CardsAdded: 3,
                    CardsRemoved: 1,
                    CardsUpgraded: 2
                )
            ),
        };

        foreach (var payload in payloads)
        {
            var evt = new DomainEvent(
                Type: "test.contract",
                Source: nameof(RougeRunEventContractsTests),
                DataJson: JsonSerializer.Serialize(payload),
                Timestamp: new DateTimeOffset(2025, 01, 01, 0, 0, 0, TimeSpan.Zero),
                Id: "evt_1"
            );

            Action act = () =>
            {
                _ = JsonSerializer.Serialize(payload);
                _ = JsonSerializer.Serialize(evt);
            };

            act.Should().NotThrow();
        }
    }
}
