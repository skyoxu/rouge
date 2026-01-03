using Game.Core.Contracts.Rouge.Effects;

namespace Game.Core.Contracts.Rouge.Events;

/// <summary>
/// Domain event: core.event.choice.resolved
/// Description: Emitted when a narrative event choice is selected and its effects are fully applied.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record EventChoiceResolved(
    string RunId,
    string EventId,
    string ChoiceId,
    EffectDeltaSummary DeltaSummary
)
{
    public const string EventType = "core.event.choice.resolved";
}

