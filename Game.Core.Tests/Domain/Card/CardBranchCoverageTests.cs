using System;
using FluentAssertions;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Domain;
using Xunit;

namespace Game.Core.Tests.Domain.Card;

public sealed class CardBranchCoverageTests
{
    [Fact]
    public void CardDefinition_throws_when_cost_is_out_of_range()
    {
        Action act = () => _ = CardDefinition.CreateOrThrow(
            id: "card_bad_cost",
            name: "Bad Cost",
            type: CardType.Attack,
            cost: CardDefinition.MaxCost + 1,
            targetRule: TargetRule.SingleEnemy,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card_bad_cost",
            rarity: "common",
            classTag: "test",
            upgradedId: null
        );

        act.Should().Throw<ArgumentOutOfRangeException>()
            .WithMessage("*CardDefinition.Cost*");
    }

    [Fact]
    public void CardDefinition_throws_when_text_key_is_blank()
    {
        Action act = () => _ = CardDefinition.CreateOrThrow(
            id: "card_bad_textkey",
            name: "Bad TextKey",
            type: CardType.Attack,
            cost: 1,
            targetRule: TargetRule.SingleEnemy,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: " ",
            rarity: "common",
            classTag: "test",
            upgradedId: null
        );

        act.Should().Throw<ArgumentException>()
            .WithMessage("*CardDefinition.TextKey*");
    }

    [Fact]
    public void CardInstance_allows_isUpgraded_true_when_definition_has_upgraded_id()
    {
        var def = CardDefinition.CreateOrThrow(
            id: "card_base",
            name: "Base",
            type: CardType.Attack,
            cost: 1,
            targetRule: TargetRule.SingleEnemy,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card_base",
            rarity: "common",
            classTag: "test",
            upgradedId: "card_plus"
        );

        var instance = CardInstance.CreateOrThrow(
            definition: def,
            temporaryCostDelta: 0,
            turnFlags: null,
            isUpgraded: true
        );

        instance.IsUpgraded.Should().BeTrue();
        instance.Definition.Id.Should().Be("card_base");
        def.GetUpgradedIdOrThrow().Should().Be("card_plus");
    }
}

