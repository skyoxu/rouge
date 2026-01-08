namespace Game.Core.Contracts.Rouge.Rewards;

/// <summary>
/// The player's reward selection result.
/// </summary>
/// <remarks>
/// Stored under Game.Core/Contracts/** per ADR-0020.
/// </remarks>
public sealed record RewardSelection(
    string RewardType, // see RewardTypes
    string? SelectedItemId,
    int? Amount
);
