using System;

namespace Game.Core.Contracts.Rouge.Run;

/// <summary>
/// DTO: persisted map progress snapshot for a run save.
/// </summary>
/// <remarks>
/// References: ADR-0006 (data storage), ADR-0004 (contracts). See overlay:
/// docs/architecture/overlays/PRD-rouge-manager/08/08-Contracts-Rouge-Run-State.md
/// </remarks>
public sealed record AdventureMapSnapshot(
    string MapId,
    int Depth,
    string CurrentNodeId,
    string[] CompletedNodeIds,
    DateTimeOffset UpdatedAt
);

