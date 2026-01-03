namespace Game.Core.Contracts.Rouge.Run;

/// <summary>
/// Domain event: core.run.ended
/// Description: Emitted when a run ends (victory/defeat/abandoned).
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record RunEnded(
    string RunId,
    string Outcome, // victory | defeat | abandoned
    DateTimeOffset EndedAt,
    RunSummary Summary
)
{
    public const string EventType = "core.run.ended";
}

