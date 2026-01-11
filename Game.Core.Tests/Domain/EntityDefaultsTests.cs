using Game.Core.Domain.Entities;
using Xunit;

namespace Game.Core.Tests.Domain;

public class EntityDefaultsTests
{
    [Fact]
    public void User_defaults_are_sane()
    {
        var u = new User();
        Assert.Equal(string.Empty, u.Id);
        Assert.Equal(string.Empty, u.Username);
        Assert.Equal(0, u.CreatedAt);
        Assert.Null(u.LastLogin);
    }

    [Fact]
    public void SaveGame_defaults_are_sane()
    {
        var s = new SaveGame();
        Assert.Equal(string.Empty, s.Id);
        Assert.Equal(string.Empty, s.UserId);
        Assert.Equal(0, s.SlotNumber);
        Assert.Equal(string.Empty, s.Data);
        Assert.Equal(0L, s.CreatedAt);
        Assert.Equal(0L, s.UpdatedAt);
    }

    [Fact]
    public void Achievement_defaults_are_sane()
    {
        var a = new Achievement();
        Assert.Equal(string.Empty, a.Id);
        Assert.Equal(string.Empty, a.UserId);
        Assert.Equal(string.Empty, a.AchievementKey);
        Assert.Equal(0L, a.UnlockedAt);
        Assert.Equal(0d, a.Progress);
    }
}

