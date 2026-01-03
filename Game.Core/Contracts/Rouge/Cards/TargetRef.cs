namespace Game.Core.Contracts.Rouge.Cards;

/// <summary>
/// A minimal target reference for card play events.
/// </summary>
/// <remarks>
/// Pure contract type stored under Game.Core/Contracts/** per ADR-0020.
/// </remarks>
public sealed record TargetRef(
    string TargetType, // hero | enemy | self | all_enemies | random_enemy
    string TargetId
);

