using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using FluentAssertions;
using Game.Core.Contracts;
using Game.Core.Domain;
using Game.Core.Domain.ValueObjects;
using Game.Core.Engine;
using Game.Core.Services;
using Xunit;

namespace Game.Core.Tests.Engine;

public class GameEngineCoreEventTests
{
    // ADR-0004: Event naming conventions and CloudEvents 1.0 baseline (id/source/type/specversion).
    private static void AssertCloudEventsBaseline(DomainEvent evt)
    {
        evt.Id.Should().NotBeNullOrWhiteSpace();
        evt.Source.Should().NotBeNullOrWhiteSpace();
        evt.Type.Should().NotBeNullOrWhiteSpace();
        evt.SpecVersion.Should().Be("1.0");
        evt.DataContentType.Should().Be("application/json");
        evt.Timestamp.Offset.Should().Be(TimeSpan.Zero);
        evt.Type.Should().MatchRegex("^(core\\.|ui\\.menu\\.|screen\\.)");
        JsonDocument.Parse(evt.DataJson);
    }

    private sealed class CapturingEventBus : IEventBus
    {
        public List<DomainEvent> Published { get; } = new();

        public Task PublishAsync(DomainEvent evt)
        {
            Published.Add(evt);
            return Task.CompletedTask;
        }

        public IDisposable Subscribe(Func<DomainEvent, Task> handler) => new DummySubscription();

        private sealed class DummySubscription : IDisposable
        {
            public void Dispose()
            {
            }
        }
    }

    private static GameEngineCore CreateEngineAndBus(out CapturingEventBus bus)
    {
        var config = new GameConfig(
            MaxLevel: 10,
            InitialHealth: 100,
            ScoreMultiplier: 1.0,
            AutoSave: false,
            Difficulty: Difficulty.Medium
        );
        var inventory = new Inventory();
        bus = new CapturingEventBus();
        return new GameEngineCore(config, inventory, bus);
    }

    [Fact]
    public void Start_publishes_game_started_event()
    {
        // Arrange
        var engine = CreateEngineAndBus(out var bus);

        // Act
        engine.Start();

        // Assert
        bus.Published.Should().ContainSingle();
        var evt = bus.Published[0];
        evt.Type.Should().Be("core.game.started");
        evt.Source.Should().Be(nameof(GameEngineCore));
        evt.DataJson.Should().NotBeNullOrWhiteSpace();
        AssertCloudEventsBaseline(evt);
    }

    [Fact]
    public void AddScore_publishes_score_changed_event()
    {
        // Arrange
        var engine = CreateEngineAndBus(out var bus);
        engine.Start();
        bus.Published.Clear();

        // Act
        engine.AddScore(10);

        // Assert
        bus.Published.Should().ContainSingle();
        var evt = bus.Published[0];
        evt.Type.Should().Be("core.score.updated");
        evt.Source.Should().Be(nameof(GameEngineCore));
        evt.DataJson.Should().NotBeNullOrWhiteSpace();
        AssertCloudEventsBaseline(evt);
    }

    [Fact]
    public void ApplyDamage_publishes_player_health_changed_event()
    {
        // Arrange
        var engine = CreateEngineAndBus(out var bus);
        engine.Start();
        bus.Published.Clear();

        // Act
        engine.ApplyDamage(new Damage(Amount: 10, Type: DamageType.Physical, IsCritical: false));

        // Assert
        bus.Published.Should().ContainSingle();
        var evt = bus.Published[0];
        evt.Type.Should().Be("core.health.updated");
        evt.Source.Should().Be(nameof(GameEngineCore));
        evt.DataJson.Should().NotBeNullOrWhiteSpace();
        AssertCloudEventsBaseline(evt);
    }

    [Fact]
    public void All_published_events_follow_naming_and_required_fields()
    {
        // Arrange
        var engine = CreateEngineAndBus(out var bus);

        // Act
        engine.Start();
        engine.Move(1, 0);
        engine.AddScore(5);
        engine.ApplyDamage(new Damage(Amount: 1, Type: DamageType.Physical, IsCritical: false));
        engine.End();

        // Assert
        bus.Published.Should().HaveCount(5);
        foreach (var evt in bus.Published)
        {
            AssertCloudEventsBaseline(evt);
        }
    }
}
