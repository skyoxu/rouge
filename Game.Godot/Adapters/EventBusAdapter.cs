using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Godot;
using Game.Core.Contracts;
using Game.Core.Services;

namespace Game.Godot.Adapters;

public partial class EventBusAdapter : Node, IEventBus
{
    [Signal]
    public delegate void DomainEventEmittedEventHandler(string type, string source, string dataJson, string id, string specVersion, string dataContentType, string timestampIso);

    private readonly List<Func<DomainEvent, Task>> _handlers = new();
    private readonly object _gate = new();
    private static readonly object AuditGate = new();

    public Task PublishAsync(DomainEvent evt)
    {
        // Emit Godot signal for scene-level listeners
        var dataJson = string.IsNullOrWhiteSpace(evt.DataJson) ? "{}" : evt.DataJson;
        EmitSignal(SignalName.DomainEventEmitted, evt.Type, evt.Source, dataJson, evt.Id, evt.SpecVersion, evt.DataContentType, evt.Timestamp.ToString("o"));

        // Notify in-process subscribers
        List<Func<DomainEvent, Task>> snapshot;
        lock (_gate) snapshot = _handlers.ToList();
        return Task.WhenAll(snapshot.Select(h => SafeInvoke(h, evt)));
    }

    private static async Task SafeInvoke(Func<DomainEvent, Task> h, DomainEvent evt)
    {
        try { await h(evt); }
        catch (Exception ex)
        {
            AuditHandlerException(evt, h, ex);
        }
    }

    private static void AuditHandlerException(DomainEvent evt, Func<DomainEvent, Task> handler, Exception ex)
    {
        try
        {
            var date = DateTime.UtcNow.ToString("yyyy-MM-dd");
            var root = ResolveAuditRoot(date);
            Directory.CreateDirectory(root);

            var path = Path.Combine(root, "security-audit.jsonl");

            string handlerName;
            try
            {
                var decl = handler.Method.DeclaringType?.FullName ?? "<unknown>";
                handlerName = $"{decl}.{handler.Method.Name}";
            }
            catch { handlerName = "<unknown>"; }

            var obj = new Dictionary<string, object?>
            {
                ["ts"] = DateTime.UtcNow.ToString("o"),
                ["action"] = "eventbus.handler.exception",
                ["reason"] = $"{ex.GetType().FullName}: {Truncate(ex.Message, 512)}",
                ["target"] = evt.Type,
                ["caller"] = System.Environment.UserName,
                ["event_source"] = evt.Source,
                ["event_id"] = evt.Id,
                ["handler"] = handlerName,
                ["exception_type"] = ex.GetType().FullName,
                ["exception_message"] = Truncate(ex.Message, 4096),
                ["stack"] = Truncate(ex.StackTrace ?? string.Empty, 16384),
            };

            var json = JsonSerializer.Serialize(obj);
            lock (AuditGate) File.AppendAllText(path, json + System.Environment.NewLine);
        }
        catch
        {
            // ignore audit failures; do not break gameplay
        }
    }

    private static string ResolveAuditRoot(string date)
    {
        var root = System.Environment.GetEnvironmentVariable("AUDIT_LOG_ROOT");
        if (!string.IsNullOrWhiteSpace(root))
        {
            if (Path.IsPathRooted(root)) return root;
            var repo = TryFindRepoRoot();
            return string.IsNullOrWhiteSpace(repo) ? root : Path.Combine(repo, root);
        }

        var repoRoot = TryFindRepoRoot();
        return string.IsNullOrWhiteSpace(repoRoot)
            ? Path.Combine("logs", "ci", date)
            : Path.Combine(repoRoot, "logs", "ci", date);
    }

    private static string? TryFindRepoRoot()
    {
        try
        {
            var dir = new DirectoryInfo(AppContext.BaseDirectory);
            for (int i = 0; i < 24 && dir != null; i++, dir = dir.Parent)
            {
                var full = dir.FullName;
                if (File.Exists(Path.Combine(full, "project.godot"))) return full;
                if (File.Exists(Path.Combine(full, "Rouge.sln"))) return full;
                if (Directory.Exists(Path.Combine(full, ".git"))) return full;
            }
        }
        catch
        {
            // ignore repo root discovery failures
        }
        return null;
    }

    private static string Truncate(string s, int max)
    {
        if (string.IsNullOrEmpty(s)) return s ?? string.Empty;
        return s.Length <= max ? s : s.Substring(0, max);
    }

    public IDisposable Subscribe(Func<DomainEvent, Task> handler)
    {
        lock (_gate) _handlers.Add(handler);
        return new Unsubscriber(_handlers, handler, _gate);
    }

    // Simple publish for GDScript tests without needing DomainEvent construction
    public void PublishSimple(string type, string source, string data_json)
    {
        var evt = new DomainEvent(
            Type: type,
            Source: source,
            DataJson: string.IsNullOrWhiteSpace(data_json) ? "{}" : data_json,
            Timestamp: DateTimeOffset.UtcNow,
            Id: Guid.NewGuid().ToString("N")
        );
        _ = PublishAsync(evt);
    }

    private sealed class Unsubscriber : IDisposable
    {
        private readonly List<Func<DomainEvent, Task>> _list;
        private readonly Func<DomainEvent, Task> _handler;
        private readonly object _gate;
        private bool _disposed;

        public Unsubscriber(List<Func<DomainEvent, Task>> list, Func<DomainEvent, Task> handler, object gate)
        { _list = list; _handler = handler; _gate = gate; }

        public void Dispose()
        {
            if (_disposed) return;
            lock (_gate) _list.Remove(_handler);
            _disposed = true;
        }
    }
}
