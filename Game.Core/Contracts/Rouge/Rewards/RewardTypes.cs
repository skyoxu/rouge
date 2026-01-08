namespace Game.Core.Contracts.Rouge.Rewards;

/// <summary>
/// Allowed values for <see cref="RewardOption.RewardType"/> and <see cref="RewardSelection.RewardType"/>.
/// </summary>
public static class RewardTypes
{
    public const string CardPick = "card_pick";
    public const string Gold = "gold";
    public const string Heal = "heal";
    public const string Relic = "relic";
    public const string RemoveCard = "remove_card";
    public const string UpgradeCard = "upgrade_card";

    public static readonly string[] All =
    {
        CardPick,
        Gold,
        Heal,
        Relic,
        RemoveCard,
        UpgradeCard,
    };
}

