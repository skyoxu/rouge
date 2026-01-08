namespace Game.Core.Contracts.Rouge.Effects;

/// <summary>
/// Allowed values for <see cref="EffectsResolved.SourceType"/> in Rouge contracts.
/// </summary>
public static class EffectSourceTypes
{
    public const string Card = "card";
    public const string EnemyIntent = "enemy_intent";
    public const string EventChoice = "event_choice";
    public const string Reward = "reward";

    public static readonly string[] All =
    {
        Card,
        EnemyIntent,
        EventChoice,
        Reward,
    };
}

