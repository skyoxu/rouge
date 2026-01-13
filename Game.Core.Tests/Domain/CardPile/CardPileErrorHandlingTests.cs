using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using FluentAssertions;
using Game.Core.Contracts;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Domain;
using Game.Core.Services;
using Xunit;

namespace Game.Core.Tests.Domain.CardPile;

public sealed class CardPileErrorHandlingTests
{
    [Fact]
    public void SetTurn_rejects_negative_values()
    {
        var sut = CreateSut(bus: null);
        Action act = () => sut.SetTurn(-1);
        act.Should().Throw<ArgumentOutOfRangeException>();
    }

    [Fact]
    public void Publish_throws_with_context_when_eventbus_throws_synchronously()
    {
        var sut = CreateSut(bus: new ThrowingEventBus());
        Exception? captured = null;
        sut.OnPublishError = (ex, _) => captured = ex;

        sut.AddCard(CreateCardDefinition("card_a"));

        Action act = () => sut.Draw(1);

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("*core.card.drawn*");
        captured.Should().NotBeNull();
    }

    [Fact]
    public void Publish_calls_error_handler_when_eventbus_task_faults()
    {
        var sut = CreateSut(bus: new FaultedEventBus());
        Exception? captured = null;
        DomainEvent? evt = null;
        sut.OnPublishError = (ex, e) => { captured = ex; evt = e; };

        sut.AddCard(CreateCardDefinition("card_a"));

        Action act = () => sut.Draw(1);
        act.Should().Throw<InvalidOperationException>()
            .WithMessage("*core.card.drawn*");

        captured.Should().NotBeNull();
        evt.Should().NotBeNull();
        evt!.Type.Should().Be("core.card.drawn");
    }

    [Fact]
    public void UpgradeCard_updates_definition_id_and_keeps_instance_id()
    {
        var sut = CreateSut(bus: null);

        sut.AddCard(CreateCardDefinition("card_base", upgradedId: "card_plus"));
        sut.Draw(1);

        var instance = sut.Hand.Single();
        var instanceId = instance.Id;

        sut.UpgradeCard(instanceId);

        sut.Hand.Should().ContainSingle(c => c.Id == instanceId);
        var upgraded = sut.Hand.Single(c => c.Id == instanceId);
        upgraded.DefinitionId.Should().Be("card_plus");
        upgraded.IsUpgraded.Should().BeTrue();
    }

    [Fact]
    public void Publish_throws_when_eventbus_task_is_canceled_immediately()
    {
        var sut = CreateSut(bus: new ImmediatelyCanceledEventBus());
        Exception? captured = null;
        sut.OnPublishError = (ex, _) => captured = ex;
        sut.AddCard(CreateCardDefinition("card_a"));

        Action act = () => sut.Draw(1);
        act.Should().Throw<OperationCanceledException>();
        captured.Should().NotBeNull();
        captured.Should().BeOfType<TaskCanceledException>();
    }

    [Fact]
    public void Publish_calls_error_handler_when_eventbus_task_is_canceled_after_return()
    {
        var bus = new DelayedCancelEventBus();
        var sut = CreateSut(bus: bus);

        Exception? captured = null;
        sut.OnPublishError = (ex, _) => captured = ex;

        sut.AddCard(CreateCardDefinition("card_a"));

        sut.Draw(1);

        bus.Cancel();

        captured.Should().NotBeNull();
        captured.Should().BeOfType<TaskCanceledException>();
    }

    [Fact]
    public async Task Publish_calls_error_handler_when_eventbus_task_faults_after_return()
    {
        var bus = new DelayedFaultEventBus();
        var sut = CreateSut(bus: bus);

        var seen = new TaskCompletionSource<Exception>(TaskCreationOptions.RunContinuationsAsynchronously);
        sut.OnPublishError = (ex, _) => seen.TrySetResult(ex);

        sut.AddCard(CreateCardDefinition("card_a"));

        sut.Draw(1);
        bus.Fault(new InvalidOperationException("fault later"));

        var ex = await seen.Task.WaitAsync(TimeSpan.FromSeconds(1));
        ex.Should().BeOfType<AggregateException>();
        ((AggregateException)ex).InnerExceptions.Should().ContainSingle()
            .Which.Message.Should().Be("fault later");
    }

    private static Game.Core.Domain.CardPile CreateSut(IEventBus? bus)
    {
        var rng = new RngService();
        rng.SetSeed(123);
        return new Game.Core.Domain.CardPile(rng, bus);
    }

    private static CardDefinition CreateCardDefinition(string id, string? upgradedId = null)
    {
        return CardDefinition.CreateOrThrow(
            id: id,
            name: id,
            type: CardType.Attack,
            cost: 1,
            targetRule: TargetRule.SingleEnemy,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: id,
            rarity: "common",
            classTag: "test",
            upgradedId: upgradedId
        );
    }

    private sealed class ThrowingEventBus : IEventBus
    {
        public Task PublishAsync(DomainEvent evt) => throw new InvalidOperationException("sync throw");
        public IDisposable Subscribe(Func<DomainEvent, Task> handler) => throw new NotSupportedException();
    }

    private sealed class FaultedEventBus : IEventBus
    {
        public Task PublishAsync(DomainEvent evt) => Task.FromException(new InvalidOperationException("faulted"));
        public IDisposable Subscribe(Func<DomainEvent, Task> handler) => throw new NotSupportedException();
    }

    private sealed class ImmediatelyCanceledEventBus : IEventBus
    {
        public Task PublishAsync(DomainEvent evt) => Task.FromCanceled(new CancellationToken(canceled: true));
        public IDisposable Subscribe(Func<DomainEvent, Task> handler) => throw new NotSupportedException();
    }

    private sealed class DelayedCancelEventBus : IEventBus
    {
        private readonly TaskCompletionSource _tcs = new();

        public Task PublishAsync(DomainEvent evt) => _tcs.Task;

        public void Cancel()
        {
            _tcs.TrySetCanceled();
        }

        public IDisposable Subscribe(Func<DomainEvent, Task> handler) => throw new NotSupportedException();
    }

    private sealed class DelayedFaultEventBus : IEventBus
    {
        private readonly TaskCompletionSource _tcs = new();

        public Task PublishAsync(DomainEvent evt) => _tcs.Task;

        public void Fault(Exception ex)
        {
            _tcs.TrySetException(ex);
        }

        public IDisposable Subscribe(Func<DomainEvent, Task> handler) => throw new NotSupportedException();
    }
}
