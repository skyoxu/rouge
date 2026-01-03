namespace Game.Core.Contracts.Rouge.Run;

/// <summary>
/// Minimal run summary for the end-of-run event payload.
/// </summary>
/// <remarks>
/// This is intentionally small and stable for T2 reporting and audit trails.
/// Stored under Game.Core/Contracts/** per ADR-0020.
/// </remarks>
public sealed record RunSummary(
    int DepthReached,
    int NodesCompleted,
    int BattlesWon,
    int BattlesLost,
    int GoldDelta,
    int CardsAdded,
    int CardsRemoved,
    int CardsUpgraded
);

