using Game.Core.Domain;
using Game.Core.Domain.ValueObjects;
using Game.Core.Engine;
using Xunit;

namespace Game.Core.Tests.Engine;

public class GameEngineCoreNoBusTests
{
    [Fact]
    public void Engine_works_without_event_bus()
    {
        var cfg = new GameConfig(
            MaxLevel: 10,
            InitialHealth: 100,
            ScoreMultiplier: 1.0,
            AutoSave: false,
            Difficulty: Difficulty.Medium
        );
        var inv = new Inventory();
        var engine = new GameEngineCore(cfg, inv, bus: null);

        var s0 = engine.Start();
        Assert.NotNull(s0);

        var s1 = engine.Move(1, 2);
        Assert.Equal(new Position(1, 2), s1.Position);

        var s2 = engine.ApplyDamage(new Damage(Amount: 1, Type: DamageType.Physical, IsCritical: false));
        Assert.Equal(99, s2.Health);
    }
}

