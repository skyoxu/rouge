using System;

namespace Game.Core.Contracts.Rouge.Run;

/// <summary>
/// DTO: persisted run state snapshot used for save/load between Game.Core and adapters.
/// </summary>
/// <remarks>
/// References: ADR-0006 (data storage), ADR-0004 (contracts). See overlay:
/// docs/architecture/overlays/PRD-rouge-manager/08/08-Contracts-Rouge-Run-State.md
/// </remarks>
public sealed record RunGameStateSnapshot(
    int Version,
    int RunSeed,
    int CurrentAct,
    AdventureMapSnapshot Map,
    PartySnapshot Party,
    RunStatisticsSnapshot? Statistics,
    DateTimeOffset SavedAtUtc
);

