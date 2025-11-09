using System;
using System.Threading.Tasks;
using Game.Core.Domain.Entities;
using Game.Core.Ports;
using Game.Core.Repositories;

namespace Game.Godot.Adapters.Db;

public class UserRepository : IUserRepository
{
    private readonly ISqlDatabase _db;
    public UserRepository(ISqlDatabase db) => _db = db;

    public Task UpsertAsync(User user)
    {
        if (string.IsNullOrEmpty(user.Id)) user.Id = Guid.NewGuid().ToString();
        if (user.CreatedAt == 0) user.CreatedAt = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        _db.Execute("INSERT INTO users(id, username, created_at, last_login) VALUES(@0,@1,@2,@3) ON CONFLICT(id) DO UPDATE SET username=@1, last_login=@3;",
            user.Id, user.Username, user.CreatedAt, user.LastLogin ?? (object)DBNull.Value);
        return Task.CompletedTask;
    }

    public Task<User?> FindByUsernameAsync(string username)
    {
        var rows = _db.Query("SELECT id, username, created_at, last_login FROM users WHERE username=@0 LIMIT 1;", username);
        if (rows.Count == 0) return Task.FromResult<User?>(null);
        var r = rows[0];
        var u = new User
        {
            Id = r.GetValueOrDefault("id")?.ToString() ?? string.Empty,
            Username = r.GetValueOrDefault("username")?.ToString() ?? string.Empty,
            CreatedAt = Convert.ToInt64(r.GetValueOrDefault("created_at") ?? 0),
            LastLogin = r["last_login"] == null ? null : Convert.ToInt64(r["last_login"]) 
        };
        return Task.FromResult<User?>(u);
    }
}

