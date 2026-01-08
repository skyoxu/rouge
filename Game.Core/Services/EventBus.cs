using Game.Core.Contracts;

namespace Game.Core.Services;

public interface IEventBus
{
    Task PublishAsync(DomainEvent evt);
    IDisposable Subscribe(Func<DomainEvent, Task> handler);
}

public class InMemoryEventBus : IEventBus
{
    private readonly List<Func<DomainEvent, Task>> _handlers = new();
    private readonly object _gate = new();
    private static readonly object AuditGate = new();
    private readonly string? _auditLogRoot;

    public InMemoryEventBus(string? auditLogRoot = null)
    {
        _auditLogRoot = auditLogRoot;
    }

    public Task PublishAsync(DomainEvent evt)
    {
        List<Func<DomainEvent, Task>> snapshot;
        lock (_gate) snapshot = _handlers.ToList();
        return Task.WhenAll(snapshot.Select(h => SafeInvoke(h, evt)));
    }

    private async Task SafeInvoke(Func<DomainEvent, Task> h, DomainEvent evt)
    {
        try { await h(evt); }
        catch (Exception ex)
        {
            AuditHandlerException(evt, h, ex);
        }
    }

    private void AuditHandlerException(DomainEvent evt, Func<DomainEvent, Task> handler, Exception ex)
    {
        try
        {
            var date = DateTime.UtcNow.ToString("yyyy-MM-dd");
            var root = ResolveAuditRoot(date);
            System.IO.Directory.CreateDirectory(root);

            var path = System.IO.Path.Combine(root, "security-audit.jsonl");

            string handlerName;
            try
            {
                var decl = handler.Method.DeclaringType?.FullName ?? "<unknown>";
                handlerName = $"{decl}.{handler.Method.Name}";
            }
            catch { handlerName = "<unknown>"; }

            var obj = new System.Collections.Generic.Dictionary<string, object?>
            {
                ["ts"] = DateTime.UtcNow.ToString("o"),
                ["action"] = "eventbus.handler.exception",
                ["reason"] = $"{ex.GetType().FullName}: {Truncate(ex.Message, 512)}",
                ["target"] = evt.Type,
                ["caller"] = Environment.UserName,
                ["event_source"] = evt.Source,
                ["event_id"] = evt.Id,
                ["handler"] = handlerName,
                ["exception_type"] = ex.GetType().FullName,
                ["exception_message"] = Truncate(ex.Message, 4096),
                ["stack"] = Truncate(ex.StackTrace ?? string.Empty, 16384),
            };

            var json = System.Text.Json.JsonSerializer.Serialize(obj);
            lock (AuditGate) System.IO.File.AppendAllText(path, json + Environment.NewLine);
        }
        catch
        {
            // ignore audit failures; do not break gameplay
        }
    }

    private string ResolveAuditRoot(string date)
    {
        var root = _auditLogRoot;
        if (string.IsNullOrWhiteSpace(root))
        {
            root = Environment.GetEnvironmentVariable("AUDIT_LOG_ROOT");
        }

        if (!string.IsNullOrWhiteSpace(root))
        {
            if (System.IO.Path.IsPathRooted(root)) return root;
            var repo = TryFindRepoRoot();
            return string.IsNullOrWhiteSpace(repo) ? root : System.IO.Path.Combine(repo, root);
        }

        var repoRoot = TryFindRepoRoot();
        return string.IsNullOrWhiteSpace(repoRoot)
            ? System.IO.Path.Combine("logs", "ci", date)
            : System.IO.Path.Combine(repoRoot, "logs", "ci", date);
    }

    private static string? TryFindRepoRoot()
    {
        try
        {
            var dir = new System.IO.DirectoryInfo(AppContext.BaseDirectory);
            for (int i = 0; i < 24 && dir != null; i++, dir = dir.Parent)
            {
                var full = dir.FullName;
                if (System.IO.File.Exists(System.IO.Path.Combine(full, "project.godot"))) return full;
                if (System.IO.File.Exists(System.IO.Path.Combine(full, "Rouge.sln"))) return full;
                if (System.IO.Directory.Exists(System.IO.Path.Combine(full, ".git"))) return full;
            }
        }
        catch
        {
            // ignore repo root discovery failures
        }
        return null;
    }

    public IDisposable Subscribe(Func<DomainEvent, Task> handler)
    {
        lock (_gate) _handlers.Add(handler);
        return new Unsubscriber(_handlers, handler, _gate);
    }

    private static string Truncate(string s, int max)
    {
        if (string.IsNullOrEmpty(s)) return s ?? string.Empty;
        return s.Length <= max ? s : s.Substring(0, max);
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

