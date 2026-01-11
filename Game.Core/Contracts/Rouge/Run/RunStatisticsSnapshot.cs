namespace Game.Core.Contracts.Rouge.Run;

/// <summary>
/// DTO: lightweight run statistics snapshot for save/load and UI display.
/// </summary>
/// <remarks>
/// References: ADR-0006 (data storage), ADR-0004 (contracts). See overlay:
/// docs/architecture/overlays/PRD-rouge-manager/08/08-Contracts-Rouge-Run-State.md
/// </remarks>
public sealed record RunStatisticsSnapshot(
    int BattlesWon,
    int BattlesLost,
    int NodesCompleted,
    int GoldDelta,
    int CardsAdded,
    int CardsRemoved,
    int CardsUpgraded
);

