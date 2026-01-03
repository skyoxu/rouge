namespace Game.Core.Contracts.Rouge.Rewards;

/// <summary>
/// A minimal reward option (e.g. card pick, gold, heal) for T2.
/// </summary>
/// <remarks>
/// Stored under Game.Core/Contracts/** per ADR-0020.
/// </remarks>
public sealed record RewardOption(
    string RewardType, // card_pick | gold | heal | relic | remove_card | upgrade_card
    IReadOnlyList<string> ItemIds,
    int? Amount
);

