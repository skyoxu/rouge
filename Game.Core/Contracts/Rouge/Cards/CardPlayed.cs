namespace Game.Core.Contracts.Rouge.Cards;

/// <summary>
/// Domain event: core.card.played
/// Description: Emitted when a card passes validation and is submitted to the effect resolver.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record CardPlayed(
    string RunId,
    string BattleId,
    int Turn,
    string HeroId,
    string CardId,
    IReadOnlyList<TargetRef> Targets
)
{
    public const string EventType = "core.card.played";
}

