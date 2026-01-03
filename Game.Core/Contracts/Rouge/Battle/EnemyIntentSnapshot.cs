namespace Game.Core.Contracts.Rouge.Battle;

/// <summary>
/// Minimal enemy intent snapshot for UI and audit trails.
/// </summary>
/// <remarks>
/// Pure contract type stored under Game.Core/Contracts/** per ADR-0020.
/// </remarks>
public sealed record EnemyIntentSnapshot(
    string EnemyId,
    string IntentId,
    string? TargetId,
    int? Amount,
    string? Notes
);

