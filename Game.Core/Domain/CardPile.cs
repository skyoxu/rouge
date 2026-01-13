using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Game.Core.Contracts;
using Game.Core.Contracts.Rouge.Cards;
using Game.Core.Services;

namespace Game.Core.Domain;

public enum PileType
{
    DrawPile = 0,
    Hand = 1,
    DiscardPile = 2,
    ExhaustPile = 3,
}

public sealed record CardRef(string Id, string DefinitionId, bool IsUpgraded = false);

public sealed class CardPile
{
    private const int DefaultHandLimit = 10;

    private readonly IRngService _rng;
    private readonly IEventBus? _bus;

    private readonly Dictionary<string, string> _upgradeMap = new(StringComparer.Ordinal);

    private readonly List<CardRef> _drawPile = new();
    private readonly List<CardRef> _hand = new();
    private readonly List<CardRef> _discardPile = new();
    private readonly List<CardRef> _exhaustPile = new();

    private int _drawOrder;

    public string RunId { get; }
    public string BattleId { get; }
    public string HeroId { get; }
    public int Turn { get; private set; }

    public IReadOnlyList<CardRef> DrawPile => _drawPile;
    public IReadOnlyList<CardRef> Hand => _hand;
    public IReadOnlyList<CardRef> DiscardPile => _discardPile;
    public IReadOnlyList<CardRef> ExhaustPile => _exhaustPile;

    public Action<Exception, DomainEvent>? OnPublishError { get; set; }

    public CardPile(IRngService rng, IEventBus? bus = null)
    {
        _rng = rng ?? throw new ArgumentNullException(nameof(rng));
        _bus = bus;

        RunId = Guid.NewGuid().ToString("N");
        BattleId = Guid.NewGuid().ToString("N");
        HeroId = "hero_0";
        Turn = 0;
        _drawOrder = 0;
    }

    public IEnumerable<CardRef> GetPile(PileType pileType)
    {
        return pileType switch
        {
            PileType.DrawPile => DrawPile,
            PileType.Hand => Hand,
            PileType.DiscardPile => DiscardPile,
            PileType.ExhaustPile => ExhaustPile,
            _ => Array.Empty<CardRef>(),
        };
    }

    public void SetTurn(int turn)
    {
        if (turn < 0) throw new ArgumentOutOfRangeException(nameof(turn), "turn must be non-negative.");
        Turn = turn;
    }

    public void AddCard(CardDefinition cardDef)
    {
        ArgumentNullException.ThrowIfNull(cardDef);

        var instanceId = Guid.NewGuid().ToString("N");
        _drawPile.Add(new CardRef(Id: instanceId, DefinitionId: cardDef.Id, IsUpgraded: false));

        var upgradedId = cardDef.ResolveUpgradedId();
        if (!string.IsNullOrWhiteSpace(upgradedId))
        {
            _upgradeMap[cardDef.Id] = upgradedId!;
        }
    }

    public void RemoveCard(string cardId)
    {
        if (string.IsNullOrWhiteSpace(cardId)) return;
        _ = RemoveByInstanceId(_drawPile, cardId);
        _ = RemoveByInstanceId(_hand, cardId);
        _ = RemoveByInstanceId(_discardPile, cardId);
        _ = RemoveByInstanceId(_exhaustPile, cardId);
    }

    public void UpgradeCard(string cardId)
    {
        if (string.IsNullOrWhiteSpace(cardId)) return;

        if (TryUpgradeInPile(_hand, cardId))
            return;

        _ = TryUpgradeInPile(_drawPile, cardId);
        _ = TryUpgradeInPile(_discardPile, cardId);
        _ = TryUpgradeInPile(_exhaustPile, cardId);
    }

    public void Shuffle()
    {
        _rng.Shuffle(_drawPile);
    }

    public void Draw(int n)
    {
        if (n <= 0) return;

        for (var i = 0; i < n; i++)
        {
            if (_hand.Count >= DefaultHandLimit) return;

            if (_drawPile.Count == 0)
            {
                if (_discardPile.Count == 0) return;

                _drawPile.AddRange(_discardPile);
                _discardPile.Clear();
                _rng.Shuffle(_drawPile);
            }

            if (_drawPile.Count == 0) return;

            // Treat the end of the list as the top of the pile to avoid O(n) head removals.
            var last = _drawPile.Count - 1;
            var card = _drawPile[last];
            _drawPile.RemoveAt(last);
            _hand.Add(card);

            var drawOrder = ++_drawOrder;
            Publish(
                CardDrawn.EventType,
                new CardDrawn(
                    RunId,
                    BattleId,
                    Turn,
                    HeroId,
                    CardInstanceId: card.Id,
                    CardDefinitionId: card.DefinitionId,
                    DrawOrder: drawOrder
                )
            );
        }
    }

    public void Discard(string cardId)
    {
        if (string.IsNullOrWhiteSpace(cardId)) return;
        var idx = _hand.FindIndex(c => string.Equals(c.Id, cardId, StringComparison.Ordinal));
        if (idx < 0) return;

        var card = _hand[idx];
        _hand.RemoveAt(idx);

        _discardPile.Add(card);
        Publish(
            CardDiscarded.EventType,
            new CardDiscarded(
                RunId,
                BattleId,
                Turn,
                HeroId,
                CardInstanceId: card.Id,
                CardDefinitionId: card.DefinitionId
            )
        );
    }

    public void Exhaust(string cardId)
    {
        if (string.IsNullOrWhiteSpace(cardId)) return;
        var idx = _hand.FindIndex(c => string.Equals(c.Id, cardId, StringComparison.Ordinal));
        if (idx < 0) return;

        var card = _hand[idx];
        _hand.RemoveAt(idx);
        _exhaustPile.Add(card);
    }

    private bool TryUpgradeInPile(List<CardRef> pile, string instanceId)
    {
        for (var i = 0; i < pile.Count; i++)
        {
            if (!string.Equals(pile[i].Id, instanceId, StringComparison.Ordinal)) continue;

            var current = pile[i];
            if (!_upgradeMap.TryGetValue(current.DefinitionId, out var upgradedId)) return false;
            if (string.IsNullOrWhiteSpace(upgradedId)) return false;

            pile[i] = current with { DefinitionId = upgradedId, IsUpgraded = true };
            return true;
        }
        return false;
    }

    private static bool RemoveByInstanceId(List<CardRef> pile, string instanceId)
    {
        var idx = pile.FindIndex(c => string.Equals(c.Id, instanceId, StringComparison.Ordinal));
        if (idx < 0) return false;
        pile.RemoveAt(idx);
        return true;
    }

    private void Publish(string type, object data)
    {
        if (_bus is null) return;

        var json = JsonSerializer.Serialize(data);
        var evt = new DomainEvent(
            Type: type,
            Source: nameof(CardPile),
            DataJson: json,
            Timestamp: DateTimeOffset.UtcNow,
            Id: Guid.NewGuid().ToString("N")
        );

        Task task;
        try
        {
            task = _bus.PublishAsync(evt);
        }
        catch (Exception ex)
        {
            OnPublishError?.Invoke(ex, evt);
            throw new InvalidOperationException($"Failed to publish domain event '{type}'.", ex);
        }

        if (task.IsFaulted)
        {
            var ex = (Exception?)task.Exception ?? new InvalidOperationException("PublishAsync returned a faulted task.");
            OnPublishError?.Invoke(ex, evt);
            throw new InvalidOperationException($"Failed to publish domain event '{type}'.", ex);
        }

        if (task.IsCanceled)
        {
            var ex = new TaskCanceledException(task);
            OnPublishError?.Invoke(ex, evt);
            throw new OperationCanceledException($"Publishing domain event '{type}' was canceled.", ex, CancellationToken.None);
        }

        if (!task.IsCompletedSuccessfully)
        {
            _ = task.ContinueWith(
                t =>
                {
                    var ex = t.Exception;
                    if (ex is not null)
                    {
                        OnPublishError?.Invoke(ex, evt);
                    }
                },
                CancellationToken.None,
                TaskContinuationOptions.ExecuteSynchronously | TaskContinuationOptions.OnlyOnFaulted,
                TaskScheduler.Default
            );

            _ = task.ContinueWith(
                _ =>
                {
                    var ex = new TaskCanceledException(task);
                    OnPublishError?.Invoke(ex, evt);
                },
                CancellationToken.None,
                TaskContinuationOptions.ExecuteSynchronously | TaskContinuationOptions.OnlyOnCanceled,
                TaskScheduler.Default
            );
        }
    }
}
