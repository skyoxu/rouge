namespace Game.Core.Contracts.Rouge.Battle;

/// <summary>
/// Domain event: core.battle.ended
/// Description: Emitted when a battle ends (victory/defeat/escaped).
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record BattleEnded(
    string RunId,
    string BattleId,
    string Result, // victory | defeat | escaped
    DateTimeOffset EndedAt
)
{
    public const string EventType = "core.battle.ended";
}

