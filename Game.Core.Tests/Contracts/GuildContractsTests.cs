using System;
using Game.Core.Contracts.Guild;
using Xunit;

namespace Game.Core.Tests.Contracts;

public class GuildContractsTests
{
    [Fact]
    public void GuildMemberJoined_contract_can_be_constructed()
    {
        var now = DateTimeOffset.UtcNow;
        var evt = new GuildMemberJoined("u1", "g1", now, "member");
        Assert.Equal("u1", evt.UserId);
        Assert.Equal("g1", evt.GuildId);
        Assert.Equal(now, evt.JoinedAt);
        Assert.Equal("member", evt.Role);
        Assert.Equal("core.guild.member.joined", GuildMemberJoined.EventType);
    }
}

