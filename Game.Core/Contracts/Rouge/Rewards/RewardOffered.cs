namespace Game.Core.Contracts.Rouge.Rewards;

/// <summary>
/// Domain event: core.reward.offered
/// Description: Emitted when reward candidates are generated and shown to the player.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record RewardOffered(
    string RunId,
    string NodeId,
    IReadOnlyList<RewardOption> Rewards
)
{
    public const string EventType = "core.reward.offered";
}

