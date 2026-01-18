using System;
using System.Linq;
using FluentAssertions;
using Game.Core.Contracts.Rouge.Effects;
using Game.Core.Domain;
using Game.Core.Services;
using Xunit;
using DomainCardPile = Game.Core.Domain.CardPile;

namespace Game.Core.Tests.Domain.CardPile;

public sealed class CardPileBranchCoverageTests
{
    [Fact]
    public void Ctor_throws_when_rng_is_null()
    {
        Action act = () => _ = new DomainCardPile(rng: null!, bus: null);
        act.Should().Throw<ArgumentNullException>().WithParameterName("rng");
    }

    [Fact]
    public void Draw_does_nothing_when_n_is_non_positive()
    {
        var sut = CreateSut();
        sut.AddCard(CreateCard("card_a"));

        sut.Draw(0);
        sut.Hand.Should().BeEmpty();
        sut.DrawPile.Should().ContainSingle(c => c.DefinitionId == "card_a");

        sut.Draw(-1);
        sut.Hand.Should().BeEmpty();
        sut.DrawPile.Should().ContainSingle(c => c.DefinitionId == "card_a");
    }

    [Fact]
    public void SetTurn_allows_non_negative_values()
    {
        var sut = CreateSut();
        sut.SetTurn(3);
        sut.Turn.Should().Be(3);
    }

    [Fact]
    public void Draw_stops_at_hand_limit()
    {
        var sut = CreateSut();
        for (var i = 0; i < 11; i++)
        {
            sut.AddCard(CreateCard($"card_{i}"));
        }

        sut.Draw(11);

        sut.Hand.Should().HaveCount(10);
        sut.DrawPile.Should().HaveCount(1, "hand limit should stop drawing early");
    }

    [Fact]
    public void Draw_returns_when_both_draw_and_discard_are_empty()
    {
        var sut = CreateSut();

        sut.Draw(1);

        sut.Hand.Should().BeEmpty();
        sut.DrawPile.Should().BeEmpty();
        sut.DiscardPile.Should().BeEmpty();
    }

    [Fact]
    public void RemoveCard_is_no_op_for_whitespace_or_missing_ids()
    {
        var sut = CreateSut();
        sut.AddCard(CreateCard("card_a"));

        sut.RemoveCard(" ");
        sut.RemoveCard("card_missing");

        sut.DrawPile.Should().HaveCount(1);
        sut.Hand.Should().BeEmpty();
        sut.DiscardPile.Should().BeEmpty();
        sut.ExhaustPile.Should().BeEmpty();
    }

    [Fact]
    public void Discard_ignores_unknown_or_whitespace_card_ids()
    {
        var sut = CreateSut();
        sut.AddCard(CreateCard("card_a"));
        sut.Draw(1);

        sut.Discard(" ");
        sut.Discard("card_missing");

        sut.Hand.Should().ContainSingle(c => c.DefinitionId == "card_a");
        sut.DiscardPile.Should().BeEmpty();
    }

    [Fact]
    public void GetPile_exposes_each_pile_type()
    {
        var sut = CreateSut();
        sut.AddCard(CreateCard("card_a"));
        sut.AddCard(CreateCard("card_b"));
        sut.AddCard(CreateCard("card_c"));

        sut.Draw(2);
        var handCard = sut.Hand.First();
        sut.Discard(handCard.Id);

        sut.Draw(1);
        var exhaustCard = sut.Hand.First();
        sut.Exhaust(exhaustCard.Id);

        sut.GetPile(PileType.DrawPile).Should().BeEquivalentTo(sut.DrawPile);
        sut.GetPile(PileType.Hand).Should().BeEquivalentTo(sut.Hand);
        sut.GetPile(PileType.DiscardPile).Should().BeEquivalentTo(sut.DiscardPile);
        sut.GetPile(PileType.ExhaustPile).Should().BeEquivalentTo(sut.ExhaustPile);
    }

    [Fact]
    public void UpgradeCard_is_no_op_when_no_upgrade_mapping_exists()
    {
        var sut = CreateSut();
        sut.AddCard(CreateCard("card_base", upgradedId: null));
        sut.Draw(1);

        var instanceId = sut.Hand.Single().Id;
        sut.UpgradeCard(instanceId);

        sut.Hand.Should().ContainSingle(c => c.DefinitionId == "card_base" && c.IsUpgraded == false);
    }

    [Fact]
    public void UpgradeCard_can_skip_non_matching_items_in_pile()
    {
        var sut = CreateSut();
        sut.AddCard(CreateCard("card_base_a"));
        sut.AddCard(CreateCard("card_base_b"));
        sut.Draw(2);

        var target = sut.Hand.Last();
        var targetId = target.Id;

        sut.UpgradeCard(targetId);

        sut.Hand.Should().ContainSingle(c => c.Id == targetId && c.IsUpgraded);
    }

    [Fact]
    public void GetPile_returns_empty_for_unknown_pile_type_value()
    {
        var sut = CreateSut();
        sut.AddCard(CreateCard("card_a"));

        sut.GetPile((PileType)999).Should().BeEmpty();
        sut.GetPile(PileType.DrawPile).Should().Contain(c => c.DefinitionId == "card_a");
    }

    private static DomainCardPile CreateSut()
    {
        var rng = new RngService();
        rng.SetSeed(123);
        return new DomainCardPile(rng, bus: null);
    }

    private static CardDefinition CreateCard(string id, string? upgradedId = "card_plus")
    {
        // Note: upgradedId may be null to cover the "no mapping" branches.
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
}
