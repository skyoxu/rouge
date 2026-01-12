using System;
using System.Collections.Generic;
using FluentAssertions;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Domain;
using Xunit;

namespace Game.Core.Tests.Domain;

public class CardDefinitionTests
{
    [Fact]
    public void Constructor_copies_effect_commands_to_prevent_external_mutation()
    {
        var effects = new List<EffectCommand>
        {
            new("Damage", new Dictionary<string, string> { ["amount"] = "3" }),
        };

        var def = new CardDefinition(
            Id: "card_mutation_test",
            Name: "MutationTest",
            Type: CardType.Attack,
            Cost: 1,
            TargetRule: TargetRule.SingleEnemy,
            EffectCommands: effects,
            TextKey: "card.mutation_test",
            Rarity: "Common",
            ClassTag: "Any"
        );

        effects.Clear();

        def.EffectCommands.Should().HaveCount(1);
        def.EffectCommands[0].Kind.Should().Be("Damage");
    }

    [Fact]
    public void With_expression_creates_new_instance_without_mutating_original()
    {
        var def = new CardDefinition(
            Id: "card_with_test",
            Name: "WithTest",
            Type: CardType.Skill,
            Cost: 1,
            TargetRule: TargetRule.Random,
            EffectCommands: new List<EffectCommand>(),
            TextKey: "card.with_test",
            Rarity: "Common",
            ClassTag: "Any"
        );

        var changed = def with { Cost = 2 };
        changed.Cost.Should().Be(2);
        def.Cost.Should().Be(1);
    }

    [Fact]
    public void CreateOrThrow_ShouldThrow_WhenIdIsBlank()
    {
        var act = () => CardDefinition.CreateOrThrow(
            id: " ",
            name: "Name",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.any",
            rarity: "Common",
            classTag: "Any"
        );

        act.Should().Throw<ArgumentException>().WithParameterName("id");
    }

    [Fact]
    public void CreateOrThrow_ShouldThrow_WhenNameIsBlank()
    {
        var act = () => CardDefinition.CreateOrThrow(
            id: "card_blank_name",
            name: " ",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.any",
            rarity: "Common",
            classTag: "Any"
        );

        act.Should().Throw<ArgumentException>().WithParameterName("name");
    }

    [Fact]
    public void CreateOrThrow_ShouldThrow_WhenCostOutOfRange()
    {
        var act = () => CardDefinition.CreateOrThrow(
            id: "card_bad_cost",
            name: "BadCost",
            type: CardType.Skill,
            cost: 11,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.any",
            rarity: "Common",
            classTag: "Any"
        );

        act.Should().Throw<ArgumentOutOfRangeException>().WithParameterName("cost");
    }

    [Fact]
    public void CreateOrThrow_ShouldThrow_WhenNumericIdIsNotPositive()
    {
        var act = () => CardDefinition.CreateOrThrow(
            id: "0",
            name: "NumericId",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.numeric_id",
            rarity: "Common",
            classTag: "Any"
        );

        act.Should().Throw<ArgumentException>().WithParameterName("id");
    }

    [Fact]
    public void CreateOrThrow_ShouldThrow_WhenUpgradedIdEqualsId()
    {
        var act = () => CardDefinition.CreateOrThrow(
            id: "card_same",
            name: "Same",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.any",
            rarity: "Common",
            classTag: "Any",
            upgradedId: "card_same"
        );

        act.Should().Throw<ArgumentException>().WithParameterName("upgradedId");
    }

    [Fact]
    public void CreateOrThrow_ShouldThrow_WhenUpgradedIdIsWhitespace()
    {
        var act = () => CardDefinition.CreateOrThrow(
            id: "card_upgrade_whitespace",
            name: "UpgradeWhitespace",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.any",
            rarity: "Common",
            classTag: "Any",
            upgradedId: " "
        );

        act.Should().Throw<ArgumentException>().WithParameterName("upgradedId");
    }

    [Fact]
    public void CreateOrThrow_ShouldThrow_WhenEffectCommandsContainNullItem()
    {
        var effects = new List<EffectCommand> { null! };

        var act = () => CardDefinition.CreateOrThrow(
            id: "card_effect_null_item",
            name: "EffectNullItem",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: effects,
            textKey: "card.effect_null_item",
            rarity: "Common",
            classTag: "Any"
        );

        act.Should().Throw<ArgumentException>().WithParameterName("effectCommands");
    }

    [Fact]
    public void CreateOrThrow_ShouldThrow_WhenEffectCommandKindIsBlank()
    {
        var effects = new List<EffectCommand>
        {
            new(" ", new Dictionary<string, string>()),
        };

        var act = () => CardDefinition.CreateOrThrow(
            id: "card_effect_blank_kind",
            name: "EffectBlankKind",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: effects,
            textKey: "card.effect_blank_kind",
            rarity: "Common",
            classTag: "Any"
        );

        act.Should().Throw<ArgumentException>().WithParameterName("effectCommands");
    }

    [Fact]
    public void ResolveUpgradedId_ShouldPreferExplicitUpgradedId()
    {
        var def = CardDefinition.CreateOrThrow(
            id: "card_base",
            name: "Base",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.base",
            rarity: "Common",
            classTag: "Any",
            upgradedId: "card_base_plus"
        );

        def.ResolveUpgradedId().Should().Be("card_base_plus");
        def.GetUpgradedIdOrThrow().Should().Be("card_base_plus");
    }

    [Fact]
    public void ResolveUpgradedId_ShouldReturnNull_WhenNoExplicitOrMap()
    {
        var def = CardDefinition.CreateOrThrow(
            id: "card_no_mapping",
            name: "NoMapping",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.no_mapping",
            rarity: "Common",
            classTag: "Any"
        );

        def.ResolveUpgradedId().Should().BeNull();
    }

    [Fact]
    public void ResolveUpgradedId_ShouldUseProvidedMap_WhenUpgradedIdMissing()
    {
        var def = CardDefinition.CreateOrThrow(
            id: "card_map_base",
            name: "Base",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.base",
            rarity: "Common",
            classTag: "Any"
        );

        var map = new Dictionary<string, string> { ["card_map_base"] = "card_map_plus" };
        def.ResolveUpgradedId(map).Should().Be("card_map_plus");
        def.GetUpgradedIdOrThrow(map).Should().Be("card_map_plus");
    }

    [Fact]
    public void ResolveUpgradedId_ShouldReturnNull_WhenMapValueIsBlank()
    {
        var def = CardDefinition.CreateOrThrow(
            id: "card_map_blank_value",
            name: "MapBlankValue",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.map_blank_value",
            rarity: "Common",
            classTag: "Any"
        );

        var map = new Dictionary<string, string> { ["card_map_blank_value"] = " " };
        def.ResolveUpgradedId(map).Should().BeNull();
    }

    [Fact]
    public void GetUpgradedIdOrThrow_ShouldThrow_WhenNoMappingExists()
    {
        var def = CardDefinition.CreateOrThrow(
            id: "card_no_upgrade",
            name: "NoUpgrade",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.no_upgrade",
            rarity: "Common",
            classTag: "Any"
        );

        var act = () => def.GetUpgradedIdOrThrow();
        act.Should().Throw<InvalidOperationException>();
    }
}
