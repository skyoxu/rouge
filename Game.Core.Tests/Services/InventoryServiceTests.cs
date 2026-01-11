using Game.Core.Domain;
using Game.Core.Services;
using Xunit;

namespace Game.Core.Tests.Services;

public class InventoryServiceTests
{
    [Fact]
    public void Add_respects_distinct_slot_capacity_for_new_items_only()
    {
        var inv = new Inventory();
        var svc = new InventoryService(inv, maxSlots: 1);

        Assert.Equal(1, svc.Add("potion", count: 1));
        Assert.True(svc.HasItem("potion"));

        // New item would exceed distinct slot capacity.
        Assert.Equal(0, svc.Add("elixir", count: 1));
        Assert.False(svc.HasItem("elixir"));

        // Existing stack is allowed even when distinct slot capacity is full.
        Assert.Equal(2, svc.Add("potion", count: 2, maxStack: 99));
        Assert.Equal(3, svc.CountItem("potion"));
        Assert.Equal(1, svc.CountDistinct());
    }
}

