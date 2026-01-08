namespace Game.Core.Contracts.Rouge.Cards;

/// <summary>
/// Allowed values for <see cref="TargetRef.TargetType"/> in Rouge contracts.
/// </summary>
public static class TargetTypes
{
    public const string Hero = "hero";
    public const string Enemy = "enemy";
    public const string Self = "self";
    public const string AllEnemies = "all_enemies";
    public const string RandomEnemy = "random_enemy";

    public static readonly string[] All =
    {
        Hero,
        Enemy,
        Self,
        AllEnemies,
        RandomEnemy,
    };
}

