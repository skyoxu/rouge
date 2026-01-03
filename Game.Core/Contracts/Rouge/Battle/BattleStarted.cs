namespace Game.Core.Contracts.Rouge.Battle;

/// <summary>
/// Domain event: core.battle.started
/// Description: Emitted when a battle encounter is initialized.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record BattleStarted(
    string RunId,
    string BattleId,
    string EncounterId,
    string EnemyGroupId,
    DateTimeOffset StartedAt
)
{
    public const string EventType = "core.battle.started";
}

