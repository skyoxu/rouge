using System;
using System.Collections.Generic;
using FluentAssertions;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Domain;
using Xunit;

namespace Game.Core.Tests.Domain;

public class CardInstanceTests
{
    [Fact]
    public void Constructor_copies_turn_flags_to_prevent_external_mutation()
    {
        var def = new CardDefinition(
            Id: "card_instance_mutation_test",
            Name: "InstanceMutationTest",
            Type: CardType.Skill,
            Cost: 1,
            TargetRule: TargetRule.Random,
            EffectCommands: new List<EffectCommand>(),
            TextKey: "card.instance_mutation_test",
            Rarity: "Common",
            ClassTag: "Any"
        );

        var flags = new HashSet<string>(StringComparer.Ordinal) { "retained" };
        var inst = new CardInstance(
            Definition: def,
            TemporaryCostDelta: 0,
            TurnFlags: flags,
            IsUpgraded: false
        );

        flags.Add("generated");

        inst.TurnFlags.Should().ContainSingle(x => x == "retained");
        inst.TurnFlags.Should().NotContain("generated");
    }

    [Fact]
    public void Constructor_throws_when_definition_is_null()
    {
        var ex = Assert.Throws<ArgumentNullException>(() => new CardInstance(
            Definition: null!,
            TemporaryCostDelta: 0,
            TurnFlags: new HashSet<string>(),
            IsUpgraded: false
        ));
        ex.ParamName.Should().Be("Definition");
    }

    [Fact]
    public void CreateOrThrow_ShouldCreateDefaultInstance()
    {
        var def = CardDefinition.CreateOrThrow(
            id: "card_default_instance",
            name: "DefaultInstance",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.default_instance",
            rarity: "Common",
            classTag: "Any"
        );

        var inst = CardInstance.CreateOrThrow(def);

        inst.Definition.Should().BeSameAs(def);
        inst.TemporaryCostDelta.Should().Be(0);
        inst.IsUpgraded.Should().BeFalse();
        inst.TurnFlags.Should().NotBeNull();
        inst.TurnFlags.Should().BeEmpty();
    }

    [Fact]
    public void CreateOrThrow_ShouldThrow_WhenUpgradedRequestedButNoMapping()
    {
        var def = CardDefinition.CreateOrThrow(
            id: "card_no_upgrade_mapping",
            name: "NoUpgradeMapping",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.no_upgrade_mapping",
            rarity: "Common",
            classTag: "Any"
        );

        var act = () => CardInstance.CreateOrThrow(
            definition: def,
            temporaryCostDelta: 0,
            turnFlags: null,
            isUpgraded: true
        );

        act.Should().Throw<InvalidOperationException>();
    }

    [Fact]
    public void CreateOrThrow_ShouldAllowUpgraded_WhenMappingProvided()
    {
        var def = CardDefinition.CreateOrThrow(
            id: "card_upgrade_base",
            name: "UpgradeBase",
            type: CardType.Skill,
            cost: 0,
            targetRule: TargetRule.Random,
            effectCommands: Array.Empty<EffectCommand>(),
            textKey: "card.upgrade_base",
            rarity: "Common",
            classTag: "Any"
        );

        var map = new Dictionary<string, string> { ["card_upgrade_base"] = "card_upgrade_plus" };

        var inst = CardInstance.CreateOrThrow(
            definition: def,
            temporaryCostDelta: 0,
            turnFlags: null,
            isUpgraded: true,
            upgradeMap: map
        );

        inst.IsUpgraded.Should().BeTrue();
    }
}
