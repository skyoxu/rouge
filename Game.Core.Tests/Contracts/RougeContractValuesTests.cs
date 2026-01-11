using System;
using System.Linq;
using Game.Core.Contracts.Rouge.Battle;
using Game.Core.Contracts.Rouge.Cards;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Contracts.Rouge.Map;
using Game.Core.Contracts.Rouge.Rewards;
using Xunit;

namespace Game.Core.Tests.Contracts;

public class RougeContractValuesTests
{
    [Fact]
    public void MapNodeTypes_All_contains_all_constants_and_has_no_duplicates()
    {
        MapNodeTypes.All.ShouldContainExact(
            MapNodeTypes.Battle,
            MapNodeTypes.Elite,
            MapNodeTypes.Boss,
            MapNodeTypes.Shop,
            MapNodeTypes.Rest,
            MapNodeTypes.Event,
            MapNodeTypes.Treasure
        );
    }

    [Fact]
    public void MapNodeResults_All_contains_all_constants_and_has_no_duplicates()
    {
        MapNodeResults.All.ShouldContainExact(
            MapNodeResults.Ok,
            MapNodeResults.Fail,
            MapNodeResults.Aborted
        );
    }

    [Fact]
    public void RewardTypes_All_contains_all_constants_and_has_no_duplicates()
    {
        RewardTypes.All.ShouldContainExact(
            RewardTypes.CardPick,
            RewardTypes.Gold,
            RewardTypes.Heal,
            RewardTypes.Relic,
            RewardTypes.RemoveCard,
            RewardTypes.UpgradeCard
        );
    }

    [Fact]
    public void TargetTypes_All_contains_all_constants_and_has_no_duplicates()
    {
        TargetTypes.All.ShouldContainExact(
            TargetTypes.Hero,
            TargetTypes.Enemy,
            TargetTypes.Self,
            TargetTypes.AllEnemies,
            TargetTypes.RandomEnemy
        );
    }

    [Fact]
    public void EffectSourceTypes_All_contains_all_constants_and_has_no_duplicates()
    {
        EffectSourceTypes.All.ShouldContainExact(
            EffectSourceTypes.Card,
            EffectSourceTypes.EnemyIntent,
            EffectSourceTypes.EventChoice,
            EffectSourceTypes.Reward
        );
    }

    [Fact]
    public void BattleResults_All_contains_all_constants_and_has_no_duplicates()
    {
        BattleResults.All.ShouldContainExact(
            BattleResults.Victory,
            BattleResults.Defeat,
            BattleResults.Escaped
        );
    }
}

internal static class AssertExtensions
{
    public static void ShouldContainExact(this string[] actual, params string[] expected)
    {
        Assert.NotNull(actual);
        Assert.NotNull(expected);

        actual.ShouldNotContainNullOrWhitespace();
        expected.ShouldNotContainNullOrWhitespace();

        Assert.Equal(expected.Length, actual.Length);
        Assert.True(actual.SequenceEqual(expected), $"Expected exact ordering [{string.Join(", ", expected)}] but got [{string.Join(", ", actual)}].");
        Assert.Equal(expected.Length, actual.Distinct(StringComparer.Ordinal).Count());
    }

    public static void ShouldNotContainNullOrWhitespace(this string[] values)
    {
        foreach (var v in values)
        {
            Assert.False(string.IsNullOrWhiteSpace(v), "Expected non-empty contract value.");
        }
    }
}

