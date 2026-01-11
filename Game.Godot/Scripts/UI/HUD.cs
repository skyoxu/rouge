using System;
using Godot;
using Game.Godot.Adapters;
using System.Text.Json;

namespace Game.Godot.Scripts.UI;

public partial class HUD : Control
{
    private Label _score = default!;
    private Label _health = default!;
    private EventBusAdapter? _bus;
    private Callable _domainEventCallable;
    private bool _connected;

    private static readonly JsonDocumentOptions JsonOptions = new()
    {
        MaxDepth = 32,
        AllowTrailingCommas = false,
        CommentHandling = JsonCommentHandling.Disallow,
    };

    public override void _Ready()
    {
        _score = GetNode<Label>("TopBar/HBox/ScoreLabel");
        _health = GetNode<Label>("TopBar/HBox/HealthLabel");

        _bus = GetNodeOrNull<EventBusAdapter>("/root/EventBus");
        if (_bus != null)
        {
            _domainEventCallable = new Callable(this, nameof(OnDomainEventEmitted));
            _bus.Connect(EventBusAdapter.SignalName.DomainEventEmitted, _domainEventCallable);
            _connected = true;
        }
    }

    public override void _ExitTree()
    {
        if (_connected && _bus != null)
        {
            try
            {
                if (_bus.IsConnected(EventBusAdapter.SignalName.DomainEventEmitted, _domainEventCallable))
                {
                    _bus.Disconnect(EventBusAdapter.SignalName.DomainEventEmitted, _domainEventCallable);
                }
            }
            catch (Exception ex)
            {
                GD.PrintErr($"[HUD] Failed to disconnect DomainEventEmitted: {ex.GetType().FullName}: {ex.Message}");
            }
            finally
            {
                _connected = false;
                _bus = null;
            }
        }
    }

    private void OnDomainEventEmitted(string type, string source, string dataJson, string id, string specVersion, string dataContentType, string timestampIso)
    {
        if (type == "core.score.updated")
        {
            try
            {
                using var doc = JsonDocument.Parse(dataJson, JsonOptions);
                int v = 0;
                if (doc.RootElement.TryGetProperty("value", out var val)) v = val.GetInt32();
                else if (doc.RootElement.TryGetProperty("score", out var sc)) v = sc.GetInt32();
                _score.Text = $"Score: {v}";
            }
            catch { }
        }
        else if (type == "core.health.updated")
        {
            try
            {
                using var doc = JsonDocument.Parse(dataJson, JsonOptions);
                int v = 0;
                if (doc.RootElement.TryGetProperty("value", out var val)) v = val.GetInt32();
                else if (doc.RootElement.TryGetProperty("health", out var hp)) v = hp.GetInt32();
                _health.Text = $"HP: {v}";
            }
            catch { }
        }
    }

    public void SetScore(int v) => _score.Text = $"Score: {v}";
    public void SetHealth(int v) => _health.Text = $"HP: {v}";
}
