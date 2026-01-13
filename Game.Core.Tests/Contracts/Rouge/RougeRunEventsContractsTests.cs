using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using FluentAssertions;
using Xunit;

namespace Game.Core.Tests.Contracts.Rouge;

public sealed class RougeRunEventsContractsTests
{
    private static Type? FindType(string fullName)
    {
        return AppDomain.CurrentDomain
            .GetAssemblies()
            .Where(a => !a.IsDynamic)
            .Select(a => a.GetType(fullName, throwOnError: false, ignoreCase: false))
            .FirstOrDefault(t => t is not null);
    }

    private static string? GetPublicConstString(Type type, string fieldName)
    {
        var field = type.GetField(fieldName, BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy);
        if (field is null)
        {
            return null;
        }

        if (field.FieldType != typeof(string))
        {
            return null;
        }

        return field.GetRawConstantValue() as string;
    }

    // ACC:T2.3
    [Fact]
    public void Card_draw_and_discard_events_are_defined_as_contracts()
    {
        const string cardDrawn = "Game.Core.Contracts.Rouge.Cards.CardDrawn";
        const string cardDiscarded = "Game.Core.Contracts.Rouge.Cards.CardDiscarded";

        var drawnType = FindType(cardDrawn);
        var discardedType = FindType(cardDiscarded);

        drawnType.Should().NotBeNull($"expected contract type '{cardDrawn}' to exist");
        discardedType.Should().NotBeNull($"expected contract type '{cardDiscarded}' to exist");
    }

    [Fact]
    public void Card_draw_and_discard_events_have_core_event_type_constants()
    {
        var expected = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["Game.Core.Contracts.Rouge.Cards.CardDrawn"] = "core.card.drawn",
            ["Game.Core.Contracts.Rouge.Cards.CardDiscarded"] = "core.card.discarded",
        };

        var eventTypes = new List<string>();

        foreach (var kvp in expected)
        {
            var type = FindType(kvp.Key);
            type.Should().NotBeNull($"expected contract type '{kvp.Key}' to exist");

            var eventType = GetPublicConstString(type!, "EventType");
            eventType.Should().NotBeNull($"expected '{kvp.Key}.EventType' to be defined as public const string");
            eventType.Should().Be(kvp.Value);

            eventTypes.Add(eventType!);
        }

        eventTypes.Should().OnlyHaveUniqueItems();
        eventTypes.Should().AllSatisfy(et => et.Should().StartWith("core."));
    }

    [Theory]
    [InlineData("Game.Core.Contracts.Rouge.Cards.CardDrawn")]
    [InlineData("Game.Core.Contracts.Rouge.Cards.CardDiscarded")]
    public void Card_draw_discard_payloads_include_minimum_trace_fields(string fullName)
    {
        var type = FindType(fullName);
        type.Should().NotBeNull($"expected contract type '{fullName}' to exist");

        var required = new Dictionary<string, Type>(StringComparer.Ordinal)
        {
            ["RunId"] = typeof(string),
            ["BattleId"] = typeof(string),
            ["Turn"] = typeof(int),
            ["HeroId"] = typeof(string),
            ["CardInstanceId"] = typeof(string),
            ["CardDefinitionId"] = typeof(string),
        };

        if (string.Equals(fullName, "Game.Core.Contracts.Rouge.Cards.CardDrawn", StringComparison.Ordinal))
        {
            required["DrawOrder"] = typeof(int);
        }

        foreach (var kvp in required)
        {
            var prop = type!.GetProperty(kvp.Key, BindingFlags.Public | BindingFlags.Instance);
            prop.Should().NotBeNull($"expected property '{kvp.Key}' on '{fullName}'");
            prop!.PropertyType.Should().Be(kvp.Value, $"expected '{fullName}.{kvp.Key}' to be '{kvp.Value.Name}'");
        }
    }
}
