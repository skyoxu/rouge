using Godot;
using System;
using System.IO;
using System.Text.Json;

namespace Game.Godot.Scripts.Security;

public partial class SecurityAudit : Node
{
    public override void _Ready()
    {
        try
        {
            var info = new
            {
                ts = DateTime.UtcNow.ToString("O"),
                event_type = "SECURITY_BASELINE",
                app = (string)(ProjectSettings.GetSetting("application/config/name") ?? "GodotGame"),
                godot = Engine.GetVersionInfo()["string"].AsStringName().ToString(),
                db_backend = Environment.GetEnvironmentVariable("GODOT_DB_BACKEND") ?? "default",
                demo = (Environment.GetEnvironmentVariable("TEMPLATE_DEMO") ?? "0").ToLowerInvariant() == "1",
                plugin_sqlite = ClassDB.CanInstantiate("SQLite"),
            };

            var json = JsonSerializer.Serialize(info);
            var dir = ProjectSettings.GlobalizePath("user://logs/security");
            Directory.CreateDirectory(dir);
            var path = Path.Combine(dir, "security-audit.jsonl");
            File.AppendAllText(path, json + Environment.NewLine);
        }
        catch (Exception ex)
        {
            GD.PushWarning($"[SecurityAudit] write failed: {ex.Message}");
        }
    }
}

