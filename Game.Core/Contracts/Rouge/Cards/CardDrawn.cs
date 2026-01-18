namespace Game.Core.Contracts.Rouge.Cards;

/// <summary>
/// Domain event: core.card.drawn
/// Description: Emitted when a card is moved from DrawPile to Hand.
/// </summary>
/// <remarks>
/// Aligned with ADR-0004 (event bus and contracts). See docs/architecture/overlays/PRD-rouge-manager/08/08-Feature-Slice-Minimum-Playable-Loop.md.
/// </remarks>
public sealed record CardDrawn(
    string RunId,
    string BattleId,
    int Turn,
    string HeroId,
    string CardInstanceId,
    string CardDefinitionId,
    int DrawOrder
)
{
    public const string EventType = "core.card.drawn";
}
