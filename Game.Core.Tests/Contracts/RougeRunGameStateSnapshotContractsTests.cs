using System;
using System.Text.Json;
using FluentAssertions;
using Game.Core.Contracts.Rouge.Run;
using Xunit;

namespace Game.Core.Tests.Contracts;

public class RougeRunGameStateSnapshotContractsTests
{
    [Fact]
    public void RunGameStateSnapshot_can_roundtrip_json()
    {
        var now = new DateTimeOffset(2025, 01, 02, 3, 4, 5, TimeSpan.Zero);

        var snapshot = new RunGameStateSnapshot(
            Version: 1,
            RunSeed: 123456,
            CurrentAct: 1,
            Map: new AdventureMapSnapshot(
                MapId: "map_1",
                Depth: 3,
                CurrentNodeId: "n_1_1",
                CompletedNodeIds: new[] { "n_0_0" },
                UpdatedAt: now
            ),
            Party: new PartySnapshot(
                HeroIds: new[] { "hero_a", "hero_b" },
                StartingDeckCardIds: new[] { "card_strike", "card_defend" }
            ),
            Statistics: new RunStatisticsSnapshot(
                BattlesWon: 1,
                BattlesLost: 0,
                NodesCompleted: 1,
                GoldDelta: 10,
                CardsAdded: 1,
                CardsRemoved: 0,
                CardsUpgraded: 0
            ),
            SavedAtUtc: now
        );

        var json = JsonSerializer.Serialize(snapshot);
        json.Should().Contain("\"Version\":1");
        json.Should().Contain("\"RunSeed\":123456");
        json.Should().Contain("\"CurrentAct\":1");
        json.Should().Contain("\"MapId\":\"map_1\"");

        var roundtrip = JsonSerializer.Deserialize<RunGameStateSnapshot>(json);
        roundtrip.Should().NotBeNull();
        roundtrip!.Version.Should().Be(1);
        roundtrip.Map.MapId.Should().Be("map_1");
        roundtrip.Party.HeroIds.Should().Contain("hero_a");
        roundtrip.Statistics.Should().NotBeNull();
        roundtrip.Statistics!.GoldDelta.Should().Be(10);
    }

    [Fact]
    public void RunGameStateSnapshot_allows_null_statistics()
    {
        var now = new DateTimeOffset(2025, 01, 02, 3, 4, 5, TimeSpan.Zero);

        var snapshot = new RunGameStateSnapshot(
            Version: 1,
            RunSeed: 123456,
            CurrentAct: 1,
            Map: new AdventureMapSnapshot(
                MapId: "map_1",
                Depth: 1,
                CurrentNodeId: "n_0_0",
                CompletedNodeIds: Array.Empty<string>(),
                UpdatedAt: now
            ),
            Party: new PartySnapshot(
                HeroIds: new[] { "hero_a" },
                StartingDeckCardIds: new[] { "card_strike" }
            ),
            Statistics: null,
            SavedAtUtc: now
        );

        var json = JsonSerializer.Serialize(snapshot);
        var roundtrip = JsonSerializer.Deserialize<RunGameStateSnapshot>(json);

        roundtrip.Should().NotBeNull();
        roundtrip!.Statistics.Should().BeNull();
    }
}

