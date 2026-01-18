using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Game.Core.Contracts;
using Game.Core.Domain;
using Game.Core.Ports;
using Game.Core.State;
using Xunit;

namespace Game.Core.Tests.State;

internal sealed class InMemoryDataStore : IDataStore
{
    private readonly Dictionary<string,string> _dict = new();
    public Task SaveAsync(string key, string json) { _dict[key] = json; return Task.CompletedTask; }
    public Task<string?> LoadAsync(string key) { _dict.TryGetValue(key, out var v); return Task.FromResult(v); }
    public Task DeleteAsync(string key) { _dict.Remove(key); return Task.CompletedTask; }
    public IReadOnlyDictionary<string,string> Snapshot => _dict;
}

public class GameStateManagerTests
{
    private static GameState MakeState(int level=1, int score=0)
        => new(
            RunSeed: 0,
            Id: Guid.NewGuid().ToString(),
            Level: level,
            Score: score,
            Health: 100,
            Inventory: Array.Empty<string>(),
            Position: new Game.Core.Domain.ValueObjects.Position(0,0),
            Timestamp: DateTime.UtcNow
        );

    private static GameConfig MakeConfig()
        => new(
            MaxLevel: 50,
            InitialHealth: 100,
            ScoreMultiplier: 1.0,
            AutoSave: false,
            Difficulty: Difficulty.Medium
        );

    [Fact]
    public async Task Save_load_delete_and_index_flow_works_with_compression()
    {
        var store = new InMemoryDataStore();
        var opts = new GameStateManagerOptions(MaxSaves: 2, EnableCompression: true);
        var mgr = new GameStateManager(store, opts);

        var seen = new List<string>();
        mgr.OnEvent(e => seen.Add(e.Type));

        mgr.SetState(MakeState(level:2), MakeConfig());
        var id1 = await mgr.SaveGameAsync("slot1");
        Assert.Contains("core.game.save.created", seen);
        Assert.True(store.Snapshot.ContainsKey(id1));
        Assert.StartsWith("gz:", store.Snapshot[id1]);

        mgr.SetState(MakeState(level:3), MakeConfig());
        var id2 = await mgr.SaveGameAsync("slot2");
        var list = await mgr.GetSaveListAsync();
        Assert.True(list.Count >= 2);

        // Trigger cleanup by saving third; MaxSaves=2 => first gets deleted from store
        mgr.SetState(MakeState(level:4), MakeConfig());
        var id3 = await mgr.SaveGameAsync("slot3");

        var saveIndexKey = opts.StorageKey + ":index";
        var indexJson = await store.LoadAsync(saveIndexKey);
        Assert.NotNull(indexJson);
        var ids = JsonSerializer.Deserialize<List<string>>(indexJson!)!;
        Assert.Equal(2, ids.Count);
        Assert.DoesNotContain(id1, ids);

        // load latest
        var (state, cfg) = await mgr.LoadGameAsync(id3);
        Assert.Equal(4, state.Level);
        Assert.Equal(100, cfg.InitialHealth);

        // delete second
        await mgr.DeleteSaveAsync(id2);
        indexJson = await store.LoadAsync(saveIndexKey);
        ids = JsonSerializer.Deserialize<List<string>>(indexJson!)!;
        Assert.DoesNotContain(id2, ids);
    }

    [Fact]
    public async Task AutoSave_toggle_and_tick()
    {
        var store = new InMemoryDataStore();
        var mgr = new GameStateManager(store);
        mgr.SetState(MakeState(level:5), MakeConfig());
        mgr.EnableAutoSave();
        await mgr.AutoSaveTickAsync();
        mgr.DisableAutoSave();
        var idx = await store.LoadAsync("guild-manager-game:index");
        Assert.NotNull(idx);
    }

    [Fact]
    public async Task AutoSave_enable_disable_are_idempotent()
    {
        var store = new InMemoryDataStore();
        var mgr = new GameStateManager(store);
        mgr.SetState(MakeState(level: 6), MakeConfig());

        mgr.EnableAutoSave();
        mgr.EnableAutoSave(); // should no-op
        await mgr.AutoSaveTickAsync();

        mgr.DisableAutoSave();
        mgr.DisableAutoSave(); // should no-op
        await mgr.AutoSaveTickAsync(); // should no-op when disabled

        var idx = await store.LoadAsync("guild-manager-game:index");
        Assert.NotNull(idx);
    }

    [Fact]
    public async Task Save_throws_when_state_missing_or_title_too_long()
    {
        var store = new InMemoryDataStore();
        var mgr = new GameStateManager(store);
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await mgr.SaveGameAsync());

        mgr.SetState(MakeState(), MakeConfig());
        var tooLong = new string('x', 101);
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(async () => await mgr.SaveGameAsync(tooLong));
    }

    [Fact]
    public async Task Save_throws_when_screenshot_too_large()
    {
        var store = new InMemoryDataStore();
        var mgr = new GameStateManager(store);
        mgr.SetState(MakeState(), MakeConfig());

        var tooLarge = new string('x', 2_000_001);
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(async () => await mgr.SaveGameAsync(name: "slot", screenshot: tooLarge));
    }

    [Fact]
    public async Task Load_throws_when_checksum_mismatch_and_reads_uncompressed_payload()
    {
        var store = new InMemoryDataStore();
        var opts = new GameStateManagerOptions(EnableCompression: false);
        var mgr = new GameStateManager(store, opts);

        var state = MakeState(level: 1);
        var cfg = MakeConfig();

        var save = new SaveData(
            Id: "save_bad_checksum",
            State: state,
            Config: cfg,
            Metadata: new SaveMetadata(DateTime.UtcNow, DateTime.UtcNow, "1.0.0", "BAD"),
            Screenshot: null,
            Title: "bad"
        );

        await store.SaveAsync(save.Id, JsonSerializer.Serialize(save));

        await Assert.ThrowsAsync<InvalidOperationException>(async () => await mgr.LoadGameAsync(save.Id));
    }

    [Fact]
    public async Task Load_throws_when_save_not_found()
    {
        var store = new InMemoryDataStore();
        var mgr = new GameStateManager(store);

        await Assert.ThrowsAsync<InvalidOperationException>(async () => await mgr.LoadGameAsync("missing_save"));
    }

    [Fact]
    public async Task GetSaveList_ignores_broken_entries_in_index()
    {
        var store = new InMemoryDataStore();
        var opts = new GameStateManagerOptions(EnableCompression: false);
        var mgr = new GameStateManager(store, opts);

        var goodId = "save_good";
        var badId = "save_bad_json";

        var save = new SaveData(
            Id: goodId,
            State: MakeState(level: 7),
            Config: MakeConfig(),
            Metadata: new SaveMetadata(DateTime.UtcNow, DateTime.UtcNow, "1.0.0", "OK"),
            Screenshot: null,
            Title: "ok"
        );

        await store.SaveAsync(goodId, JsonSerializer.Serialize(save));
        await store.SaveAsync(badId, "{not-json");
        await store.SaveAsync(opts.StorageKey + ":index", JsonSerializer.Serialize(new List<string> { goodId, badId }));

        var list = await mgr.GetSaveListAsync();

        Assert.Contains(list, s => s.Id == goodId);
        Assert.DoesNotContain(list, s => s.Id == badId);
    }
}

