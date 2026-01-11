using Game.Core.Domain;
using Game.Core.Services;
using Xunit;

namespace Game.Core.Tests.Services;

public class ScoreServiceTests
{
    [Fact]
    public void ComputeAddedScore_respects_multiplier_and_difficulty()
    {
        var svc = new ScoreService();
        var cfg = new GameConfig(
            MaxLevel: 50,
            InitialHealth: 100,
            ScoreMultiplier: 1.5,
            AutoSave: false,
            Difficulty: Difficulty.Medium
        );

        var added = svc.ComputeAddedScore(100, cfg);
        Assert.Equal(150, added); // 100 * 1.5 * 1.0

        cfg = cfg with { Difficulty = Difficulty.Hard };
        var hardAdded = svc.ComputeAddedScore(100, cfg);
        Assert.Equal(180, hardAdded); // 100 * 1.5 * 1.2
    }

    [Fact]
    public void Add_accumulates_and_reset_clears_score()
    {
        var svc = new ScoreService();
        var cfg = new GameConfig(50, 100, 1.0, false, Difficulty.Medium);

        svc.Add(10, cfg);
        svc.Add(20, cfg);

        Assert.True(svc.Score > 0);

        var before = svc.Score;
        Assert.Equal(before, svc.Score);

        svc.Reset();
        Assert.Equal(0, svc.Score);
    }

    [Fact]
    public void ComputeAddedScore_clamps_negative_points_and_handles_easy_and_unknown_difficulty()
    {
        var svc = new ScoreService();

        var cfg = new GameConfig(
            MaxLevel: 50,
            InitialHealth: 100,
            ScoreMultiplier: 1.0,
            AutoSave: false,
            Difficulty: Difficulty.Easy
        );

        Assert.Equal(0, svc.ComputeAddedScore(-10, cfg));
        Assert.Equal(9, svc.ComputeAddedScore(10, cfg)); // 10 * 1.0 * 0.9

        cfg = cfg with { Difficulty = (Difficulty)999 };
        Assert.Equal(10, svc.ComputeAddedScore(10, cfg)); // default branch => 1.0
    }
}

