namespace Game.Core.Contracts.Rouge.Effects;

/// <summary>
/// Domain event: core.effect.resolved
/// Description: Emitted when a sequence of effect commands completes resolution.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record EffectsResolved(
    string RunId,
    string BattleId,
    string SourceType, // card | enemy_intent | event_choice | reward
    IReadOnlyList<EffectCommand> Commands,
    EffectDeltaSummary DeltaSummary
)
{
    public const string EventType = "core.effect.resolved";
}

