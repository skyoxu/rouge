using System;
using System.Collections.Generic;
using FluentAssertions;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Domain;
using Xunit;

namespace Game.Core.Tests.Domain;

public class CardTests
{
    [Fact]
    public void TargetRule_ShouldContainRequiredMembers()
    {
        var names = Enum.GetNames<TargetRule>();

        names.Should().Contain(new[]
        {
            nameof(TargetRule.SingleEnemy),
            nameof(TargetRule.AllEnemies),
            nameof(TargetRule.SingleAlly),
            nameof(TargetRule.AllAllies),
            nameof(TargetRule.Random),
        });
    }

    [Fact]
    public void CardType_ShouldContainRequiredMembers()
    {
        var names = Enum.GetNames<CardType>();

        names.Should().Contain(new[]
        {
            nameof(CardType.Attack),
            nameof(CardType.Defense),
            nameof(CardType.Skill),
        });
    }

    // ACC:T1.1
    [Fact]
    public void CardDefinition_ShouldKeepDeclaredFields_AndSupportWithExpression()
    {
        var effects = new List<EffectCommand>
        {
            new(
                Kind: "Damage",
                Parameters: new Dictionary<string, string>(StringComparer.Ordinal)
                {
                    ["amount"] = "6",
                    ["target"] = "enemy",
                }
            ),
        };

        var def = new CardDefinition(
            Id: "card_strike",
            Name: "Strike",
            Type: CardType.Attack,
            Cost: 1,
            TargetRule: TargetRule.SingleEnemy,
            EffectCommands: effects,
            TextKey: "card.strike",
            Rarity: "Common",
            ClassTag: "Warrior"
        );

        def.Id.Should().Be("card_strike");
        def.Name.Should().Be("Strike");
        def.Type.Should().Be(CardType.Attack);
        def.Cost.Should().Be(1);
        def.TargetRule.Should().Be(TargetRule.SingleEnemy);
        def.TextKey.Should().Be("card.strike");
        def.Rarity.Should().Be("Common");
        def.ClassTag.Should().Be("Warrior");

        def.EffectCommands.Should().NotBeNull();
        def.EffectCommands.Should().HaveCount(1);
        def.EffectCommands[0].Kind.Should().Be("Damage");
        def.EffectCommands[0].Parameters.Should().ContainKey("amount");

        var def2 = def with { Cost = 2 };
        ReferenceEquals(def, def2).Should().BeFalse();
        def.Cost.Should().Be(1);
        def2.Cost.Should().Be(2);
        def2.Id.Should().Be(def.Id);
    }

    // ACC:T1.2
    [Fact]
    public void CardInstance_ShouldTrackRuntimeState_WithoutMutatingDefinition()
    {
        var def = new CardDefinition(
            Id: "card_defend",
            Name: "Defend",
            Type: CardType.Defense,
            Cost: 1,
            TargetRule: TargetRule.SingleAlly,
            EffectCommands: new List<EffectCommand>(),
            TextKey: "card.defend",
            Rarity: "Common",
            ClassTag: "Warrior"
        );

        var instance = new CardInstance(
            Definition: def,
            TemporaryCostDelta: -2,
            TurnFlags: new HashSet<string>(StringComparer.Ordinal) { "retained", "generated" },
            IsUpgraded: false
        );

        instance.Definition.Should().BeSameAs(def);
        instance.TemporaryCostDelta.Should().Be(-2);
        instance.IsUpgraded.Should().BeFalse();
        instance.TurnFlags.Should().NotBeNull();
        instance.TurnFlags.Should().Contain(new[] { "retained", "generated" });

        var effectiveCost = Math.Max(0, instance.Definition.Cost + instance.TemporaryCostDelta);
        effectiveCost.Should().Be(0);

        var upgraded = instance with { IsUpgraded = true, TemporaryCostDelta = 1 };
        ReferenceEquals(instance, upgraded).Should().BeFalse();
        instance.IsUpgraded.Should().BeFalse();
        upgraded.IsUpgraded.Should().BeTrue();
        def.Cost.Should().Be(1);
    }

    [Fact]
    public void CardDefinition_accepts_null_effect_commands_and_creates_empty_list()
    {
        var def = new CardDefinition(
            Id: "card_null_effects",
            Name: "NullEffects",
            Type: CardType.Skill,
            Cost: 0,
            TargetRule: TargetRule.Random,
            EffectCommands: null!,
            TextKey: "card.null_effects",
            Rarity: "Common",
            ClassTag: "Any"
        );

        def.EffectCommands.Should().NotBeNull();
        def.EffectCommands.Should().BeEmpty();
    }

    [Fact]
    public void CardInstance_accepts_null_turn_flags_and_creates_empty_set()
    {
        var def = new CardDefinition(
            Id: "card_null_flags",
            Name: "NullFlags",
            Type: CardType.Skill,
            Cost: 0,
            TargetRule: TargetRule.Random,
            EffectCommands: new List<EffectCommand>(),
            TextKey: "card.null_flags",
            Rarity: "Common",
            ClassTag: "Any"
        );

        var instance = new CardInstance(
            Definition: def,
            TemporaryCostDelta: 0,
            TurnFlags: null!,
            IsUpgraded: false
        );

        instance.TurnFlags.Should().NotBeNull();
        instance.TurnFlags.Should().BeEmpty();
    }
}
