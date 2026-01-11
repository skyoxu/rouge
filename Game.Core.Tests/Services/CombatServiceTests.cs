using System;
using Game.Core.Domain;
using Game.Core.Domain.ValueObjects;
using Game.Core.Services;
using Xunit;
using System.Threading.Tasks;
using Game.Core.Contracts;

namespace Game.Core.Tests.Services;

public class CombatServiceTests
{
    [Fact]
    public void CalculateDamage_applies_resistance_and_critical()
    {
        var cfg = new CombatConfig { CritMultiplier = 2.0 };
        cfg.Resistances[DamageType.Fire] = 0.5; // 50% resist

        var svc = new CombatService();
        var baseFire = new Damage(100, DamageType.Fire);
        var reduced = svc.CalculateDamage(baseFire, cfg);
        Assert.Equal(50, reduced);

        var crit = new Damage(100, DamageType.Fire, IsCritical: true);
        var reducedCrit = svc.CalculateDamage(crit, cfg);
        Assert.Equal(100, reducedCrit); // 100 * 0.5 * 2.0
    }

    [Fact]
    public void CalculateDamage_with_armor_mitigates_linearly()
    {
        var cfg = new CombatConfig();
        var svc = new CombatService();
        var dmg = new Damage(40, DamageType.Physical);
        var res = svc.CalculateDamage(dmg, cfg, armor: 10);
        Assert.Equal(30, res);
    }

    [Fact]
    public void ApplyDamage_reduces_player_health()
    {
        var p = new Player(maxHealth: 100);
        var svc = new CombatService();
        svc.ApplyDamage(p, new Damage(25, DamageType.Physical));
        Assert.Equal(75, p.Health.Current);
    }

    [Fact]
    public void CalculateDamage_uses_default_config_when_null_and_clamps_negative_amount()
    {
        var svc = new CombatService();

        var negative = new Damage(-10, DamageType.Physical);
        Assert.Equal(0, svc.CalculateDamage(negative, config: null));

        var normal = new Damage(10, DamageType.Physical);
        Assert.Equal(10, svc.CalculateDamage(normal, config: null));
    }

    [Fact]
    public async Task ApplyDamage_publishes_event_when_bus_is_provided()
    {
        var bus = new CapturingEventBus();
        var svc = new CombatService(bus);
        var p = new Player(maxHealth: 10);

        svc.ApplyDamage(p, new Damage(3, DamageType.Fire, IsCritical: false));
        await bus.WaitAsync();

        Assert.Equal(7, p.Health.Current);
        Assert.NotNull(bus.LastEvent);
        Assert.Equal("core.player.damaged", bus.LastEvent!.Type);
    }

    [Fact]
    public async Task ApplyDamage_with_config_publishes_event_and_clamps_crit_multiplier_to_at_least_one()
    {
        var bus = new CapturingEventBus();
        var svc = new CombatService(bus);
        var p = new Player(maxHealth: 100);

        var cfg = new CombatConfig { CritMultiplier = 0.5 };
        cfg.Resistances[DamageType.Fire] = -1.0; // intentionally invalid to exercise clamp-to-zero branch

        svc.ApplyDamage(p, new Damage(10, DamageType.Fire, IsCritical: true), cfg);
        await bus.WaitAsync();

        Assert.Equal(100, p.Health.Current); // damage clamped to 0
        Assert.NotNull(bus.LastEvent);
        Assert.Equal("core.player.damaged", bus.LastEvent!.Type);
    }

    [Fact]
    public void CalculateDamage_with_armor_handles_negative_and_excessive_values()
    {
        var svc = new CombatService();
        var cfg = new CombatConfig();
        var dmg = new Damage(10, DamageType.Physical);

        Assert.Equal(10, svc.CalculateDamage(dmg, cfg, armor: -5));
        Assert.Equal(0, svc.CalculateDamage(dmg, cfg, armor: 999));
    }

    [Fact]
    public void ApplyDamage_with_config_does_not_throw_when_bus_is_null()
    {
        var svc = new CombatService(bus: null);
        var p = new Player(maxHealth: 10);
        var cfg = new CombatConfig();

        svc.ApplyDamage(p, new Damage(1, DamageType.Physical), cfg);
        Assert.Equal(9, p.Health.Current);
    }

    private sealed class CapturingEventBus : IEventBus
    {
        private readonly TaskCompletionSource<bool> _tcs = new(TaskCreationOptions.RunContinuationsAsynchronously);

        public DomainEvent? LastEvent { get; private set; }

        public Task PublishAsync(DomainEvent evt)
        {
            LastEvent = evt;
            _tcs.TrySetResult(true);
            return Task.CompletedTask;
        }

        public IDisposable Subscribe(Func<DomainEvent, Task> handler) => throw new NotSupportedException();

        public Task WaitAsync() => _tcs.Task;
    }
}
