namespace Game.Core.Contracts.Rouge.Effects;

/// <summary>
/// A minimal effect command for T2 audit trails and UI updates.
/// </summary>
/// <remarks>
/// This intentionally models a command as (Kind + Parameters) to keep the contract stable while the effect system evolves.
/// Stored under Game.Core/Contracts/** per ADR-0020.
/// </remarks>
public sealed record EffectCommand(
    string Kind, // Damage | GainBlock | Heal | ApplyStatus | Draw | ChangeEnergy | GainGold | LoseGold | AddCardToDeck | RemoveCardFromDeck | UpgradeCardInDeck | TriggerBattle | SetFlag
    IReadOnlyDictionary<string, string> Parameters
);

