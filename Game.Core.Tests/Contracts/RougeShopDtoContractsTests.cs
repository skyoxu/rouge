using System;
using System.Text.Json;
using FluentAssertions;
using Game.Core.Contracts.Rouge.Shop;
using Xunit;

namespace Game.Core.Tests.Contracts;

public class RougeShopDtoContractsTests
{
    [Fact]
    public void Shop_inventory_can_be_serialized_to_json()
    {
        var dto = new ShopInventory(
            RunId: "run_1",
            NodeId: "node_shop_1",
            Cards: new[]
            {
                new ShopCardOffer(CardId: "card_a", Price: 50),
                new ShopCardOffer(CardId: "card_b", Price: 75),
            },
            RemoveCardPrice: 75
        );

        Action act = () => _ = JsonSerializer.Serialize(dto);
        act.Should().NotThrow();

        var json = JsonSerializer.Serialize(dto);
        json.Should().Contain("\"RunId\"");
        json.Should().Contain("\"RemoveCardPrice\":75");
    }
}
