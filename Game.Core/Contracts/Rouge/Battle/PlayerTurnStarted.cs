namespace Game.Core.Contracts.Rouge.Battle;

/// <summary>
/// Domain event: core.battle.turn.player.started
/// Description: Emitted when the player turn starts (after OnTurnStart resolutions).
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record PlayerTurnStarted(
    string RunId,
    string BattleId,
    int Turn,
    IReadOnlyList<HeroEnergySnapshot> HeroesEnergy,
    int DrawCount
)
{
    public const string EventType = "core.battle.turn.player.started";
}

