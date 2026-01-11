using System;
using Game.Core.Domain;
using Xunit;

namespace Game.Core.Tests.Domain;

public class GameResultsTests
{
    [Fact]
    public void GameResult_records_can_be_constructed_and_compared()
    {
        var stats = new GameStatistics(
            TotalMoves: 10,
            ItemsCollected: 2,
            EnemiesDefeated: 3,
            DistanceTraveled: 12.5,
            AverageReactionTime: 0.25
        );

        var a = new GameResult(
            FinalScore: 123,
            LevelReached: 4,
            PlayTimeSeconds: 99.9,
            Achievements: new[] { "a1", "a2" },
            Statistics: stats
        );

        var b = a with { };

        Assert.Equal(a, b);
        Assert.Equal(123, a.FinalScore);
        Assert.Equal(4, a.LevelReached);
        Assert.True(a.PlayTimeSeconds > 0);
        Assert.NotNull(a.Achievements);
        Assert.Equal(2, a.Achievements.Count);
        Assert.Equal(10, a.Statistics.TotalMoves);
    }
}

