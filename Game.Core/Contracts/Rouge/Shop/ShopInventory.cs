using System.Collections.Generic;

namespace Game.Core.Contracts.Rouge.Shop;

/// <summary>
/// A minimal shop inventory for a map node in T2.
/// </summary>
/// <remarks>
/// DTO contract used between Game.Core and adapters/UI.
/// Stored under Game.Core/Contracts/** per ADR-0020.
/// Currency: gold (integer).
/// </remarks>
public sealed record ShopInventory(
    string RunId,
    string NodeId,
    IReadOnlyList<ShopCardOffer> Cards,
    int RemoveCardPrice
);

/// <summary>
/// A purchasable card offer in a shop.
/// </summary>
/// <remarks>
/// Stored under Game.Core/Contracts/** per ADR-0020.
/// </remarks>
public sealed record ShopCardOffer(
    string CardId,
    int Price
);
