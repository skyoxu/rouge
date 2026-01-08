namespace Game.Core.Contracts.Rouge.Battle;

/// <summary>
/// Allowed values for <see cref="BattleEnded.Result"/> in Rouge contracts.
/// </summary>
public static class BattleResults
{
    public const string Victory = "victory";
    public const string Defeat = "defeat";
    public const string Escaped = "escaped";

    public static readonly string[] All =
    {
        Victory,
        Defeat,
        Escaped,
    };
}

