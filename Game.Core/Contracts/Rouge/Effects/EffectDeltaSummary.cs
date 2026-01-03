namespace Game.Core.Contracts.Rouge.Effects;

/// <summary>
/// Minimal numerical summary of changes produced by resolving effect commands.
/// </summary>
/// <remarks>
/// Stored under Game.Core/Contracts/** per ADR-0020.
/// </remarks>
public sealed record EffectDeltaSummary(
    int DamageDealt,
    int DamageTaken,
    int BlockGained,
    int HealingDone,
    int GoldDelta
);

