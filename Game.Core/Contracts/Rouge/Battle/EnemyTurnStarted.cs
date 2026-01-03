namespace Game.Core.Contracts.Rouge.Battle;

/// <summary>
/// Domain event: core.battle.turn.enemy.started
/// Description: Emitted when the enemy turn starts (intent execution phase).
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record EnemyTurnStarted(
    string RunId,
    string BattleId,
    int Turn,
    IReadOnlyList<EnemyIntentSnapshot> IntentSummary
)
{
    public const string EventType = "core.battle.turn.enemy.started";
}

