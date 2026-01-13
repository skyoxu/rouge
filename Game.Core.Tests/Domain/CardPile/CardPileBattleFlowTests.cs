using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.ExceptionServices;
using System.Text.Json;
using System.Threading.Tasks;
using FluentAssertions;
using Game.Core.Contracts;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Domain;
using Game.Core.Services;
using Xunit;

namespace Game.Core.Tests.Domain.CardPile;

public sealed class CardPileBattleFlowTests
{
    [Fact]
    public void Task2_cardpile_public_api_is_present_for_deck_hand_discard_exhaust()
    {
        var type = GameCoreAssembly.GetType("Game.Core.Domain.CardPile", throwOnError: false, ignoreCase: false);

        type.Should().NotBeNull("Task 2 requires a public type Game.Core.Domain.CardPile (file: Game.Core/Domain/CardPile.cs)");
        type!.IsPublic.Should().BeTrue("CardPile must be public");
        type.IsAbstract.Should().BeFalse("CardPile must be instantiable");

        RequireConstructor(type);

        RequireMethod(type, "Draw", typeof(int));
        RequireMethod(type, "Discard", typeof(string));
        RequireMethod(type, "Exhaust", typeof(string));
        RequireMethod(type, "Shuffle");
        RequireMethod(type, "AddCard", typeof(CardDefinition));
        RequireMethod(type, "RemoveCard", typeof(string));
        RequireMethod(type, "UpgradeCard", typeof(string));

        var hasNamedPiles =
            HasPublicInstanceProperty(type, "DrawPile") &&
            HasPublicInstanceProperty(type, "Hand") &&
            HasPublicInstanceProperty(type, "DiscardPile") &&
            HasPublicInstanceProperty(type, "ExhaustPile");

        var hasGetPile = HasGetPileMethod(type);

        (hasNamedPiles || hasGetPile).Should().BeTrue(
            "CardPile must expose either DrawPile/Hand/DiscardPile/ExhaustPile properties or a GetPile(PileType) accessor");
    }

    // ACC:T2.2
    [Fact(DisplayName = "ACC:T2.2 Battle flow: draw reshuffles discard when draw pile empty")]
    public void ACC_T2_2_battle_flow_draw_reshuffles_discard_when_draw_pile_empty_and_publishes_events()
    {
        var sut = CreateCardPile(out var bus);

        InvokeVoid(sut, "AddCard", CreateCardDefinition("card_a"));
        InvokeVoid(sut, "AddCard", CreateCardDefinition("card_b"));
        InvokeVoid(sut, "AddCard", CreateCardDefinition("card_c"));
        InvokeVoid(sut, "AddCard", CreateCardDefinition("card_d"));

        InvokeVoid(sut, "Draw", 4);
        GetPileCardIds(sut, "Hand").Should().HaveCount(4);
        GetPileCardIds(sut, "DrawPile").Should().BeEmpty();

        var handBeforeExhaust = GetPileCardIds(sut, "Hand");
        var exhaustedId = handBeforeExhaust[0];
        InvokeVoid(sut, "Exhaust", exhaustedId);

        GetPileCardIds(sut, "Hand").Should().HaveCount(3);
        GetPileCardIds(sut, "ExhaustPile").Should().ContainSingle(x => x == exhaustedId);

        foreach (var id in GetPileCardIds(sut, "Hand").ToArray())
        {
            InvokeVoid(sut, "Discard", id);
        }

        GetPileCardIds(sut, "Hand").Should().BeEmpty();
        GetPileCardIds(sut, "DiscardPile").Should().HaveCount(3);
        GetPileCardIds(sut, "DrawPile").Should().BeEmpty();

        InvokeVoid(sut, "Draw", 2);

        GetPileCardIds(sut, "Hand").Should().HaveCount(2, "drawing should reshuffle DiscardPile into DrawPile when DrawPile is empty");
        GetPileCardIds(sut, "DiscardPile").Should().BeEmpty("discard should have been shuffled back into draw");
        GetPileCardIds(sut, "DrawPile").Should().HaveCount(1);

        var all = new[] { "DrawPile", "Hand", "DiscardPile", "ExhaustPile" }
            .SelectMany(p => GetPileCardIds(sut, p))
            .ToArray();

        all.Should().HaveCount(4);
        all.Should().OnlyHaveUniqueItems();
        all.Should().Contain(exhaustedId);

        bus.Events.Should().NotBeEmpty("CardPile should publish domain events via IEventBus (ADR-0004 envelope)");

        var drawn = bus.Events.Where(e => e.Type == "core.card.drawn").ToList();
        var discarded = bus.Events.Where(e => e.Type == "core.card.discarded").ToList();

        drawn.Should().HaveCount(6, "Draw(4) then Draw(2) should publish 6 draw events");
        discarded.Should().HaveCount(3, "discarding 3 cards should publish 3 discard events");

        foreach (var evt in drawn.Concat(discarded))
        {
            var cardId = TryReadCardInstanceId(evt);
            cardId.Should().NotBeNullOrWhiteSpace("event payload JSON should include CardInstanceId");
        }

        var drawOrders = drawn.Select(TryReadDrawOrder).ToArray();
        drawOrders.Should().NotContainNulls("draw events should include DrawOrder");
        drawOrders.Cast<int>().Should().Equal(new[] { 1, 2, 3, 4, 5, 6 }, "draw order should be monotonically increasing across draws");
    }

    private static Assembly GameCoreAssembly => Assembly.Load("Game.Core");

    private static void RequireConstructor(Type cardPileType)
    {
        var ctors = cardPileType.GetConstructors(BindingFlags.Public | BindingFlags.Instance);

        var ok = ctors.Any(c =>
        {
            var ps = c.GetParameters();
            if (ps.Length == 2)
            {
                var hasRng = ps.Any(p => p.ParameterType == typeof(IRngService));
                var hasBus = ps.Any(p => p.ParameterType == typeof(IEventBus));
                return hasRng && hasBus;
            }

            if (ps.Length == 1)
            {
                return ps[0].ParameterType == typeof(IRngService);
            }

            return ps.Length == 0;
        });

        ok.Should().BeTrue("CardPile should be constructible for unit tests (prefer: CardPile(IRngService rng, IEventBus? bus = null)");
    }

    private static bool HasPublicInstanceProperty(Type type, string name)
    {
        var prop = type.GetProperty(name, BindingFlags.Public | BindingFlags.Instance);
        return prop is not null;
    }

    private static bool HasGetPileMethod(Type type)
    {
        var methods = type.GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .Where(m => string.Equals(m.Name, "GetPile", StringComparison.Ordinal))
            .Where(m => m.GetParameters().Length == 1)
            .ToArray();

        return methods.Any(m => m.GetParameters()[0].ParameterType.IsEnum);
    }

    private static void RequireMethod(Type type, string name, params Type[] parameterTypes)
    {
        var mi = type.GetMethod(name, BindingFlags.Public | BindingFlags.Instance, binder: null, types: parameterTypes, modifiers: null);
        mi.Should().NotBeNull($"Expected public instance method {type.FullName}.{name}({string.Join(", ", parameterTypes.Select(t => t.Name))})");
    }

    private static object CreateCardPile(out CapturingEventBus bus)
    {
        var type = GameCoreAssembly.GetType("Game.Core.Domain.CardPile", throwOnError: false, ignoreCase: false);
        type.Should().NotBeNull("Task 2 requires Game.Core.Domain.CardPile to exist");

        var rng = new RngService();
        rng.SetSeed(123);
        bus = new CapturingEventBus();

        var ctors = type!.GetConstructors(BindingFlags.Public | BindingFlags.Instance);

        object? instance = null;

        instance = TryCreate(ctors, rng, bus);
        instance ??= TryCreate(ctors, rng, null);
        instance ??= TryCreate(ctors, rng);
        instance ??= TryCreate(ctors);

        instance.Should().NotBeNull("CardPile must be instantiable via a public constructor");
        return instance!;
    }

    private static object? TryCreate(ConstructorInfo[] ctors, params object?[] args)
    {
        foreach (var ctor in ctors)
        {
            var ps = ctor.GetParameters();
            if (ps.Length != args.Length) continue;

            bool matches = true;
            for (int i = 0; i < ps.Length; i++)
            {
                var expected = ps[i].ParameterType;
                var provided = args[i];

                if (provided is null)
                {
                    if (expected.IsValueType && Nullable.GetUnderlyingType(expected) is null) { matches = false; break; }
                    continue;
                }

                if (!expected.IsInstanceOfType(provided)) { matches = false; break; }
            }

            if (!matches) continue;

            try
            {
                return ctor.Invoke(args);
            }
            catch (TargetInvocationException ex) when (ex.InnerException is not null)
            {
                ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
                throw;
            }
        }

        return null;
    }

    private static CardDefinition CreateCardDefinition(string id)
    {
        return new CardDefinition(
            Id: id,
            Name: id,
            Type: CardType.Skill,
            Cost: 0,
            TargetRule: TargetRule.Random,
            EffectCommands: Array.Empty<EffectCommand>(),
            TextKey: "card." + id,
            Rarity: "Common",
            ClassTag: "Any"
        );
    }

    private static void InvokeVoid(object instance, string methodName, params object?[] args)
    {
        var t = instance.GetType();
        var types = args.Select(a => a?.GetType() ?? typeof(object)).ToArray();

        MethodInfo? mi = null;

        var candidates = t.GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .Where(m => string.Equals(m.Name, methodName, StringComparison.Ordinal))
            .ToArray();

        foreach (var cand in candidates)
        {
            var ps = cand.GetParameters();
            if (ps.Length != args.Length) continue;

            bool ok = true;
            for (int i = 0; i < ps.Length; i++)
            {
                var expected = ps[i].ParameterType;
                var provided = args[i];
                if (provided is null)
                {
                    if (expected.IsValueType && Nullable.GetUnderlyingType(expected) is null) { ok = false; break; }
                    continue;
                }

                if (!expected.IsInstanceOfType(provided)) { ok = false; break; }
            }

            if (!ok) continue;
            mi = cand;
            break;
        }

        mi.Should().NotBeNull($"Expected {t.FullName}.{methodName} with {args.Length} parameter(s) to exist.");

        try
        {
            _ = mi!.Invoke(instance, args);
        }
        catch (TargetInvocationException ex) when (ex.InnerException is not null)
        {
            ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
            throw;
        }
    }

    private static IReadOnlyList<string> GetPileCardIds(object instance, string logicalPileName)
    {
        var pile = GetPileObject(instance, logicalPileName);
        var items = ToObjectList(pile);
        return items.Select(ExtractCardId).ToArray();
    }

    private static object GetPileObject(object instance, string logicalPileName)
    {
        var t = instance.GetType();

        var prop = t.GetProperty(logicalPileName, BindingFlags.Public | BindingFlags.Instance);
        if (prop is not null)
        {
            var value = prop.GetValue(instance);
            value.Should().NotBeNull($"{t.FullName}.{logicalPileName} must not be null");
            return value!;
        }

        var getPile = t.GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m => string.Equals(m.Name, "GetPile", StringComparison.Ordinal) && m.GetParameters().Length == 1);

        getPile.Should().NotBeNull(
            $"Expected either property {t.FullName}.{logicalPileName} or method {t.FullName}.GetPile(PileType) to exist");

        var paramType = getPile!.GetParameters()[0].ParameterType;
        paramType.IsEnum.Should().BeTrue("GetPile parameter must be an enum (PileType)");

        var enumValue = ResolvePileTypeValue(paramType, logicalPileName);

        try
        {
            var raw = getPile.Invoke(instance, new[] { enumValue });
            raw.Should().NotBeNull($"{t.FullName}.GetPile({enumValue}) must not return null");
            return raw!;
        }
        catch (TargetInvocationException ex) when (ex.InnerException is not null)
        {
            ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
            throw;
        }
    }

    private static object ResolvePileTypeValue(Type enumType, string logicalPileName)
    {
        var names = Enum.GetNames(enumType);

        string[] candidates = logicalPileName switch
        {
            "DrawPile" => new[] { "DrawPile", "Draw", "Deck" },
            "Hand" => new[] { "Hand" },
            "DiscardPile" => new[] { "DiscardPile", "Discard" },
            "ExhaustPile" => new[] { "ExhaustPile", "Exhaust" },
            _ => new[] { logicalPileName },
        };

        foreach (var c in candidates)
        {
            var match = names.FirstOrDefault(n => string.Equals(n, c, StringComparison.OrdinalIgnoreCase));
            if (match is null) continue;
            return Enum.Parse(enumType, match, ignoreCase: true);
        }

        throw new InvalidOperationException(
            $"Could not map logical pile '{logicalPileName}' to enum {enumType.FullName}. Available: {string.Join(", ", names)}");
    }

    private static List<object> ToObjectList(object enumerable)
    {
        enumerable.Should().BeAssignableTo<IEnumerable>("pile must be enumerable");

        var list = new List<object>();
        foreach (var item in (IEnumerable)enumerable)
        {
            if (item is null) continue;
            list.Add(item);
        }

        return list;
    }

    private static string ExtractCardId(object item)
    {
        if (item is string s) return s;

        var t = item.GetType();

        var idProp = t.GetProperty("Id", BindingFlags.Public | BindingFlags.Instance);
        if (idProp is not null && idProp.PropertyType == typeof(string))
        {
            var raw = idProp.GetValue(item) as string;
            if (!string.IsNullOrWhiteSpace(raw)) return raw;
        }

        var defProp = t.GetProperty("Definition", BindingFlags.Public | BindingFlags.Instance);
        if (defProp is not null)
        {
            var def = defProp.GetValue(item);
            if (def is not null)
            {
                var defIdProp = def.GetType().GetProperty("Id", BindingFlags.Public | BindingFlags.Instance);
                if (defIdProp is not null && defIdProp.PropertyType == typeof(string))
                {
                    var raw = defIdProp.GetValue(def) as string;
                    if (!string.IsNullOrWhiteSpace(raw)) return raw;
                }
            }
        }

        throw new InvalidOperationException($"Could not extract CardId from pile item type {t.FullName}.");
    }

    private static string? TryReadCardInstanceId(DomainEvent evt)
    {
        if (string.IsNullOrWhiteSpace(evt.DataJson)) return null;

        try
        {
            using var doc = JsonDocument.Parse(evt.DataJson);
            var root = doc.RootElement;
            if (root.ValueKind != JsonValueKind.Object) return null;

            foreach (var prop in root.EnumerateObject())
            {
                if (!string.Equals(prop.Name, "CardInstanceId", StringComparison.OrdinalIgnoreCase)) continue;
                if (prop.Value.ValueKind != JsonValueKind.String) return null;
                return prop.Value.GetString();
            }

            return null;
        }
        catch
        {
            return null;
        }
    }

    private static int? TryReadDrawOrder(DomainEvent evt)
    {
        if (string.IsNullOrWhiteSpace(evt.DataJson)) return null;

        try
        {
            using var doc = JsonDocument.Parse(evt.DataJson);
            var root = doc.RootElement;
            if (root.ValueKind != JsonValueKind.Object) return null;

            foreach (var prop in root.EnumerateObject())
            {
                if (!string.Equals(prop.Name, "DrawOrder", StringComparison.OrdinalIgnoreCase)) continue;
                if (prop.Value.ValueKind != JsonValueKind.Number) return null;
                if (!prop.Value.TryGetInt32(out var value)) return null;
                return value;
            }

            return null;
        }
        catch
        {
            return null;
        }
    }

    private sealed class CapturingEventBus : IEventBus
    {
        public List<DomainEvent> Events { get; } = new();

        public Task PublishAsync(DomainEvent evt)
        {
            Events.Add(evt);
            return Task.CompletedTask;
        }

        public IDisposable Subscribe(Func<DomainEvent, Task> handler) => throw new NotSupportedException();
    }
}
