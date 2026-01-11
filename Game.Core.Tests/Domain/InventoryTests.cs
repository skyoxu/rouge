using Game.Core.Domain;
using Xunit;

namespace Game.Core.Tests.Domain;

public class InventoryTests
{
    [Fact]
    public void Add_and_Remove_respect_max_stack_and_counts()
    {
        var inv = new Inventory();
        Assert.Equal(0, inv.CountItem("potion"));
        var added = inv.Add("potion", count: 120, maxStack: 99);
        Assert.Equal(99, added);
        Assert.True(inv.HasItem("potion", atLeast: 50));

        var removed = inv.Remove("potion", count: 60);
        Assert.Equal(60, removed);
        Assert.Equal(39, inv.CountItem("potion"));

        removed = inv.Remove("potion", count: 100);
        Assert.Equal(39, removed);
        Assert.Equal(0, inv.CountItem("potion"));
    }

    [Fact]
    public void Add_with_non_positive_count_returns_zero_and_does_not_create_item()
    {
        var inv = new Inventory();
        Assert.Equal(0, inv.Add("x", count: 0));
        Assert.Equal(0, inv.Add("x", count: -1));
        Assert.Equal(0, inv.CountItem("x"));
        Assert.False(inv.HasItem("x"));
    }

    [Fact]
    public void Remove_with_non_positive_count_returns_zero()
    {
        var inv = new Inventory();
        inv.Add("x", count: 3);
        Assert.Equal(0, inv.Remove("x", count: 0));
        Assert.Equal(0, inv.Remove("x", count: -1));
        Assert.Equal(3, inv.CountItem("x"));
    }

    [Fact]
    public void Remove_missing_item_returns_zero()
    {
        var inv = new Inventory();
        Assert.Equal(0, inv.Remove("missing", count: 1));
        Assert.Equal(0, inv.Remove("missing", count: 99));
    }
}

