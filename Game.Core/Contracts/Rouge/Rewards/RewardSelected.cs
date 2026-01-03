namespace Game.Core.Contracts.Rouge.Rewards;

/// <summary>
/// Domain event: core.reward.selected
/// Description: Emitted when the player selects a reward and it is applied to the run state.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record RewardSelected(
    string RunId,
    string NodeId,
    RewardSelection Selection,
    DateTimeOffset AppliedAt
)
{
    public const string EventType = "core.reward.selected";
}

