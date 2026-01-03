namespace Game.Core.Contracts.Rouge.Battle;

/// <summary>
/// Energy snapshot for a hero at the start of a player turn.
/// </summary>
/// <remarks>
/// Pure contract type stored under Game.Core/Contracts/** per ADR-0020.
/// </remarks>
public sealed record HeroEnergySnapshot(
    string HeroId,
    int Energy
);

