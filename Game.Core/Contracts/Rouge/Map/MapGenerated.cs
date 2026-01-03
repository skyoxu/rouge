namespace Game.Core.Contracts.Rouge.Map;

/// <summary>
/// Domain event: core.map.generated
/// Description: Emitted when the run map is generated and ready.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record MapGenerated(
    string RunId,
    string MapId,
    int NodeCount,
    int Depth,
    DateTimeOffset GeneratedAt
)
{
    public const string EventType = "core.map.generated";
}

