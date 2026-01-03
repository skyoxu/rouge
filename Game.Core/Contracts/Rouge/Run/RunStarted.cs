namespace Game.Core.Contracts.Rouge.Run;

/// <summary>
/// Domain event: core.run.started
/// Description: Emitted when a new run is initialized and starts.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record RunStarted(
    string RunId,
    int RunSeed,
    PartySnapshot Party,
    DateTimeOffset StartedAt
)
{
    public const string EventType = "core.run.started";
}

