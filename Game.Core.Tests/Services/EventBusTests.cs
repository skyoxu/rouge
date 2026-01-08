using System;
using System.IO;
using System.Text.Json;
using Game.Core.Contracts;
using Game.Core.Services;
using Xunit;
using System.Threading.Tasks;

namespace Game.Core.Tests.Services;

public class EventBusTests
{
    [Fact]
    public async Task Publish_invokes_subscribers_and_unsubscribe_works()
    {
        var bus = new InMemoryEventBus();
        int called = 0;
        var sub = bus.Subscribe(async e => { called++; await Task.CompletedTask; });

        await bus.PublishAsync(new DomainEvent(
            Type: "test.evt",
            Source: nameof(EventBusTests),
            DataJson: JsonSerializer.Serialize(new { ok = true }),
            Timestamp: DateTimeOffset.UtcNow,
            Id: Guid.NewGuid().ToString()
        ));

        Assert.Equal(1, called);
        sub.Dispose();

        await bus.PublishAsync(new DomainEvent(
            Type: "test.evt2",
            Source: nameof(EventBusTests),
            DataJson: "null",
            Timestamp: DateTimeOffset.UtcNow,
            Id: Guid.NewGuid().ToString()
        ));
        Assert.Equal(1, called);
    }

    [Fact]
    public async Task Subscriber_exception_is_swallowed_and_others_still_called()
    {
        var repoRoot = FindRepoRoot();
        var auditRoot = Path.Combine(
            repoRoot,
            "logs",
            "ci",
            DateTime.UtcNow.ToString("yyyy-MM-dd"),
            "unit-eventbus-audit",
            Guid.NewGuid().ToString("N")
        );
        var bus = new InMemoryEventBus(auditLogRoot: auditRoot);
        int ok = 0;
        bus.Subscribe(_ => throw new InvalidOperationException("boom"));
        bus.Subscribe(_ => { ok++; return Task.CompletedTask; });

        await bus.PublishAsync(new DomainEvent(
            Type: "evt",
            Source: nameof(EventBusTests),
            DataJson: "null",
            Timestamp: DateTimeOffset.UtcNow,
            Id: Guid.NewGuid().ToString()
        ));
        Assert.Equal(1, ok);

        var auditPath = Path.Combine(auditRoot, "security-audit.jsonl");
        Assert.True(File.Exists(auditPath), $"Missing audit log: {auditPath}");

        var lines = File.ReadAllLines(auditPath);
        Assert.NotEmpty(lines);

        bool found = false;
        foreach (var raw in lines)
        {
            var s = raw.Trim();
            if (string.IsNullOrEmpty(s)) continue;
            using var doc = JsonDocument.Parse(s);
            var root = doc.RootElement;
            if (root.ValueKind != JsonValueKind.Object) continue;

            Assert.True(root.TryGetProperty("ts", out _));
            Assert.True(root.TryGetProperty("action", out var action));
            Assert.True(root.TryGetProperty("reason", out _));
            Assert.True(root.TryGetProperty("target", out var target));
            Assert.True(root.TryGetProperty("caller", out _));

            if (action.ValueKind == JsonValueKind.String && action.GetString() == "eventbus.handler.exception")
            {
                found = true;
                Assert.Equal("evt", target.GetString());
                break;
            }
        }

        Assert.True(found, "Expected audit entry action=eventbus.handler.exception not found.");
    }

    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        for (int i = 0; i < 24 && dir != null; i++, dir = dir.Parent)
        {
            var full = dir.FullName;
            if (File.Exists(Path.Combine(full, "project.godot"))) return full;
            if (File.Exists(Path.Combine(full, "Rouge.sln"))) return full;
            if (Directory.Exists(Path.Combine(full, ".git"))) return full;
        }

        throw new InvalidOperationException("Could not locate repo root (expected project.godot or Rouge.sln).");
    }
}
