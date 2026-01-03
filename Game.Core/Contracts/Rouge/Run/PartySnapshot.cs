namespace Game.Core.Contracts.Rouge.Run;

/// <summary>
/// Snapshot of the party state at run start (T2 minimal contract).
/// </summary>
/// <remarks>
/// Contract location follows ADR-0020. Pure C# contract (no Godot dependencies) per ADR-0021.
/// </remarks>
public sealed record PartySnapshot(
    IReadOnlyList<string> HeroIds,
    IReadOnlyList<string> StartingDeckCardIds
);

