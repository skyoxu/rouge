using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.ExceptionServices;
using System.Threading.Tasks;
using FluentAssertions;
using Game.Core.Contracts;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Domain;
using Game.Core.Services;
using Xunit;

namespace Game.Core.Tests.Domain.CardPile;

public sealed class CardPileModelingTests
{
    // References: ADR-0004-event-bus-and-contracts, ADR-0005-quality-gates.

    private static Assembly GameCoreAssembly => Assembly.Load("Game.Core");

    // ACC:T2.1
    [Fact(DisplayName = "ACC:T2.1 Model: CardPile exposes required API surface")]
    public void ACC_T2_1_model_cardpile_exposes_required_api_surface()
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

    // ACC:T2.1
    [Fact(DisplayName = "ACC:T2.1 Model: UpgradeCard replaces with upgraded id in-place")]
    public void ACC_T2_1_model_upgradecard_replaces_with_upgraded_id_in_place()
    {
        var sut = CreateCardPile(out _);

        var baseId = "card_strike";
        var upgradedId = "card_strike_plus";

        var def = CardDefinition.CreateOrThrow(
            id: baseId,
            name: "Strike",
            type: CardType.Attack,
            cost: 1,
            targetRule: TargetRule.SingleEnemy,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.strike",
            rarity: "common",
            classTag: "starter",
            upgradedId: upgradedId
        );

        InvokeVoid(sut, "AddCard", def);
        InvokeVoid(sut, "Draw", 1);

        var handBefore = GetPileItems(sut, "Hand");
        handBefore.Should().HaveCount(1, "Draw(1) should place one card into Hand");

        var itemBefore = handBefore[0];
        var cardRefId = ExtractCardRefId(itemBefore);
        cardRefId.Should().NotBeNullOrWhiteSpace("a drawn card must have an observable reference id for Discard/Exhaust/Upgrade operations");

        InvokeVoid(sut, "UpgradeCard", cardRefId);

        var handAfter = GetPileItems(sut, "Hand");
        handAfter.Should().HaveCount(1, "UpgradeCard should not move the card between piles");

        var upgradedItem =
            handAfter.FirstOrDefault(i => string.Equals(ExtractCardRefId(i), cardRefId, StringComparison.Ordinal))
            ?? handAfter.FirstOrDefault(i => string.Equals(TryExtractCardDefinitionId(i) ?? string.Empty, upgradedId, StringComparison.Ordinal))
            ?? handAfter.FirstOrDefault(i => string.Equals(ExtractCardRefId(i), upgradedId, StringComparison.Ordinal));

        upgradedItem.Should().NotBeNull("Upgraded card should remain in Hand and be observable");

        var definitionId = TryExtractCardDefinitionId(upgradedItem!) ?? ExtractCardRefId(upgradedItem!);
        definitionId.Should().Be(upgradedId, "UpgradeCard(cardId) must replace the card's definition id with the upgraded id");

        var isUpgraded = TryExtractIsUpgraded(upgradedItem!);
        if (isUpgraded.HasValue)
        {
            isUpgraded.Value.Should().BeTrue("Upgraded cards should expose IsUpgraded=true when available");
        }
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

        ok.Should().BeTrue("CardPile should be constructible for unit tests (prefer: CardPile(IRngService rng, IEventBus bus))");
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
        foreach (var c in ctors)
        {
            var ps = c.GetParameters();
            if (ps.Length != args.Length) continue;

            var ok = true;
            for (var i = 0; i < ps.Length; i++)
            {
                var a = args[i];
                if (a is null)
                {
                    if (ps[i].ParameterType.IsValueType && Nullable.GetUnderlyingType(ps[i].ParameterType) is null)
                    {
                        ok = false;
                    }
                    continue;
                }

                ok = ps[i].ParameterType.IsInstanceOfType(a);
                if (!ok) break;
            }

            if (!ok) continue;

            try
            {
                return c.Invoke(args);
            }
            catch (TargetInvocationException ex) when (ex.InnerException is not null)
            {
                ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
                throw;
            }
        }

        return null;
    }

    private static void InvokeVoid(object instance, string method, params object?[] args)
    {
        _ = Invoke(instance, method, args);
    }

    private static object? Invoke(object instance, string method, params object?[] args)
    {
        var t = instance.GetType();

        var mis = t.GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .Where(m => string.Equals(m.Name, method, StringComparison.Ordinal))
            .ToArray();

        mis.Should().NotBeEmpty($"Expected method {t.FullName}.{method} to exist");

        foreach (var mi in mis)
        {
            var ps = mi.GetParameters();
            if (ps.Length != args.Length) continue;

            var ok = true;
            for (var i = 0; i < ps.Length; i++)
            {
                var a = args[i];
                if (a is null)
                {
                    if (ps[i].ParameterType.IsValueType && Nullable.GetUnderlyingType(ps[i].ParameterType) is null)
                    {
                        ok = false;
                    }
                    continue;
                }

                ok = ps[i].ParameterType.IsInstanceOfType(a);
                if (!ok) break;
            }

            if (!ok) continue;

            try
            {
                return mi.Invoke(instance, args);
            }
            catch (TargetInvocationException ex) when (ex.InnerException is not null)
            {
                ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
                throw;
            }
        }

        throw new InvalidOperationException($"Could not find an overload for {t.FullName}.{method} matching provided arguments.");
    }

    private static List<object> GetPileItems(object instance, string logicalPileName)
    {
        var pile = GetPile(instance, logicalPileName);
        return ToObjectList(pile);
    }

    private static object GetPile(object instance, string logicalPileName)
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

        getPile.Should().NotBeNull($"Expected either property {t.FullName}.{logicalPileName} or method {t.FullName}.GetPile(PileType) to exist");

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

    private static string ExtractCardRefId(object item)
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

    private static string? TryExtractCardDefinitionId(object item)
    {
        if (item is string s) return s;

        var t = item.GetType();

        var direct = t.GetProperty("DefinitionId", BindingFlags.Public | BindingFlags.Instance);
        if (direct is not null && direct.PropertyType == typeof(string))
        {
            return direct.GetValue(item) as string;
        }

        var jsonName = t.GetProperty("CardDefinitionId", BindingFlags.Public | BindingFlags.Instance);
        if (jsonName is not null && jsonName.PropertyType == typeof(string))
        {
            return jsonName.GetValue(item) as string;
        }

        var defProp = t.GetProperty("Definition", BindingFlags.Public | BindingFlags.Instance);
        if (defProp is null) return null;

        var def = defProp.GetValue(item);
        if (def is null) return null;

        var defIdProp = def.GetType().GetProperty("Id", BindingFlags.Public | BindingFlags.Instance);
        if (defIdProp is null || defIdProp.PropertyType != typeof(string)) return null;

        return defIdProp.GetValue(def) as string;
    }

    private static bool? TryExtractIsUpgraded(object item)
    {
        var t = item.GetType();
        var p = t.GetProperty("IsUpgraded", BindingFlags.Public | BindingFlags.Instance);
        if (p is null || p.PropertyType != typeof(bool)) return null;
        return (bool?)p.GetValue(item);
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
