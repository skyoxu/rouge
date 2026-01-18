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

public sealed class CardPileTests
{
    // References: ADR-0004-event-bus-and-contracts, ADR-0005-quality-gates.

    private static Assembly GameCoreAssembly => Assembly.Load("Game.Core");

    // ACC:T2.3
    [Fact(DisplayName = "ACC:T2.3 Events: draw/discard publish contract-shaped payloads")]
    public void ACC_T2_3_events_draw_discard_publish_contract_shaped_payloads()
    {
        var drawnContract = RequireContractType("Game.Core.Contracts.Rouge.Cards.CardDrawn");
        var discardedContract = RequireContractType("Game.Core.Contracts.Rouge.Cards.CardDiscarded");

        var drawnEventType = RequirePublicConstString(drawnContract, "EventType");
        var discardedEventType = RequirePublicConstString(discardedContract, "EventType");

        var sut = CreateCardPile(out var bus);

        var def = CreateCardDefinition("card_alpha");
        InvokeVoid(sut, "AddCard", def);

        InvokeVoid(sut, "Draw", 1);

        var hand = GetPileCardIds(sut, "Hand");
        hand.Should().ContainSingle("Draw(1) should move one card into Hand");

        var cardInstanceId = hand.Single();
        InvokeVoid(sut, "Discard", cardInstanceId);

        bus.Events.Should().NotBeEmpty("CardPile should publish events via IEventBus");

        var drawn = bus.Events.Where(e => string.Equals(e.Type, drawnEventType, StringComparison.Ordinal)).ToList();
        var discarded = bus.Events.Where(e => string.Equals(e.Type, discardedEventType, StringComparison.Ordinal)).ToList();

        drawn.Should().HaveCount(1, "Draw(1) should publish exactly one draw event");
        discarded.Should().HaveCount(1, "Discard(cardId) should publish exactly one discard event");

        AssertContractPayloadShape(drawn.Single(), expectedInstanceId: cardInstanceId, expectedDefinitionId: def.Id);
        AssertContractPayloadShape(discarded.Single(), expectedInstanceId: cardInstanceId, expectedDefinitionId: def.Id);
    }

    private static void AssertContractPayloadShape(DomainEvent evt, string expectedInstanceId, string expectedDefinitionId)
    {
        evt.Should().NotBeNull();
        evt.Source.Should().NotBeNullOrWhiteSpace("event envelope Source must be set");
        evt.Id.Should().NotBeNullOrWhiteSpace("event envelope Id must be set");
        evt.Timestamp.Should().NotBe(default);

        var root = ParseJsonObject(evt.DataJson);

        ReadRequiredNonEmptyString(root, "RunId");
        ReadRequiredNonEmptyString(root, "BattleId");
        ReadRequiredNonEmptyString(root, "HeroId");

        var turn = ReadRequiredInt(root, "Turn");
        turn.Should().BeGreaterThanOrEqualTo(0, "Turn must be a non-negative integer");

        var cardInstanceId = ReadRequiredNonEmptyString(root, "CardInstanceId");
        cardInstanceId.Should().Be(expectedInstanceId, "CardInstanceId should identify the affected card instance");

        var cardDefinitionId = ReadRequiredNonEmptyString(root, "CardDefinitionId");
        cardDefinitionId.Should().Be(expectedDefinitionId, "CardDefinitionId should identify the affected card definition");
    }

    private static JsonElement ParseJsonObject(string json)
    {
        json.Should().NotBeNullOrWhiteSpace("event payload DataJson must be present");

        using var doc = JsonDocument.Parse(json);
        doc.RootElement.ValueKind.Should().Be(JsonValueKind.Object, "event payload must be a JSON object");
        return doc.RootElement.Clone();
    }

    private static string ReadRequiredNonEmptyString(JsonElement obj, string name)
    {
        obj.TryGetProperty(name, out var prop).Should().BeTrue($"payload must include '{name}'");
        prop.ValueKind.Should().Be(JsonValueKind.String, $"'{name}' must be a JSON string");
        var value = prop.GetString();
        value.Should().NotBeNullOrWhiteSpace($"'{name}' must be non-empty");
        return value!;
    }

    private static int ReadRequiredInt(JsonElement obj, string name)
    {
        obj.TryGetProperty(name, out var prop).Should().BeTrue($"payload must include '{name}'");
        prop.ValueKind.Should().Be(JsonValueKind.Number, $"'{name}' must be a JSON number");
        prop.TryGetInt32(out var value).Should().BeTrue($"'{name}' must fit Int32");
        return value;
    }

    private static Type RequireContractType(string fullName)
    {
        var t = AppDomain.CurrentDomain
            .GetAssemblies()
            .Where(a => !a.IsDynamic)
            .Select(a => a.GetType(fullName, throwOnError: false, ignoreCase: false))
            .FirstOrDefault(x => x is not null);

        t.Should().NotBeNull($"expected contract type '{fullName}' to exist");
        return t!;
    }

    private static string RequirePublicConstString(Type type, string fieldName)
    {
        var field = type.GetField(fieldName, BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy);
        field.Should().NotBeNull($"expected '{type.FullName}.{fieldName}' to exist");
        field!.FieldType.Should().Be(typeof(string), $"expected '{type.FullName}.{fieldName}' to be a string");

        var raw = field.GetRawConstantValue();
        raw.Should().BeOfType<string>($"expected '{type.FullName}.{fieldName}' to be a const string");

        var value = (string)raw!;
        value.Should().NotBeNullOrWhiteSpace($"expected '{type.FullName}.{fieldName}' to be non-empty");
        return value;
    }

    private static CardDefinition CreateCardDefinition(string id)
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
            classTag: "test"
        );
    }

    private static object CreateCardPile(out CapturingEventBus bus)
    {
        var type = GameCoreAssembly.GetType("Game.Core.Domain.CardPile", throwOnError: false, ignoreCase: false);
        type.Should().NotBeNull("Task 2 requires Game.Core.Domain.CardPile to exist (file: Game.Core/Domain/CardPile.cs)");

        var rng = new RngService();
        rng.SetSeed(123);

        bus = new CapturingEventBus();

        var ctors = type!.GetConstructors(BindingFlags.Public | BindingFlags.Instance);

        object? instance = null;
        instance = TryCreate(ctors, rng, bus);
        instance ??= TryCreate(ctors, rng, null);
        instance ??= TryCreate(ctors, rng);
        instance ??= TryCreate(ctors);

        instance.Should().NotBeNull("CardPile must be instantiable via a public constructor (prefer: CardPile(IRngService rng, IEventBus bus))");
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

    private static List<string> GetPileCardIds(object instance, string logicalPileName)
    {
        var pile = GetPile(instance, logicalPileName);
        return ToObjectList(pile).Select(ExtractCardId).ToList();
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
