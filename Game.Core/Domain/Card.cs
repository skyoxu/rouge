using System;
using System.Collections.Generic;
using System.Linq;
using Game.Core.Contracts.Rouge.Effects;

namespace Game.Core.Domain;

public enum TargetRule
{
    SingleEnemy = 0,
    AllEnemies = 1,
    SingleAlly = 2,
    AllAllies = 3,
    Random = 4,
}

public enum CardType
{
    Attack = 0,
    Defense = 1,
    Skill = 2,
}

public sealed record CardDefinition
{
    public const int MinCost = 0;
    public const int MaxCost = 10;

    public static readonly IReadOnlyDictionary<string, string> UpgradeIdMap =
        new Dictionary<string, string>(StringComparer.Ordinal);

    public string Id { get; init; }
    public string Name { get; init; }
    public CardType Type { get; init; }
    public int Cost { get; init; }
    public TargetRule TargetRule { get; init; }
    public IReadOnlyList<EffectCommand> EffectCommands { get; init; }
    public string TextKey { get; init; }
    public string Rarity { get; init; }
    public string ClassTag { get; init; }
    public string? UpgradedId { get; init; }

    public CardDefinition(
        string Id,
        string Name,
        CardType Type,
        int Cost,
        TargetRule TargetRule,
        IReadOnlyList<EffectCommand> EffectCommands,
        string TextKey,
        string Rarity,
        string ClassTag,
        string? UpgradedId = null
    )
    {
        ValidateId(Id);
        ValidateName(Name);
        ValidateCost(Cost);
        ValidateEffectCommands(EffectCommands);
        ValidateTextKey(TextKey);
        ValidateRarity(Rarity);
        ValidateClassTag(ClassTag);
        ValidateUpgradeId(Id, UpgradedId);

        this.Id = Id;
        this.Name = Name;
        this.Type = Type;
        this.Cost = Cost;
        this.TargetRule = TargetRule;
        this.EffectCommands = (EffectCommands ?? Array.Empty<EffectCommand>()).ToArray();
        this.TextKey = TextKey;
        this.Rarity = Rarity;
        this.ClassTag = ClassTag;
        this.UpgradedId = UpgradedId;
    }

    public static CardDefinition CreateOrThrow(
        string id,
        string name,
        CardType type,
        int cost,
        TargetRule targetRule,
        IReadOnlyList<EffectCommand>? effectCommands,
        string textKey,
        string rarity,
        string classTag,
        string? upgradedId = null
    )
    {
        return new CardDefinition(
            Id: id,
            Name: name,
            Type: type,
            Cost: cost,
            TargetRule: targetRule,
            EffectCommands: effectCommands ?? Array.Empty<EffectCommand>(),
            TextKey: textKey,
            Rarity: rarity,
            ClassTag: classTag,
            UpgradedId: upgradedId
        );
    }

    public string? ResolveUpgradedId(IReadOnlyDictionary<string, string>? upgradeMap = null)
    {
        if (!string.IsNullOrWhiteSpace(UpgradedId))
        {
            return UpgradedId;
        }

        upgradeMap ??= UpgradeIdMap;

        return upgradeMap.TryGetValue(Id, out var mapped) && !string.IsNullOrWhiteSpace(mapped)
            ? mapped
            : null;
    }

    public string GetUpgradedIdOrThrow(IReadOnlyDictionary<string, string>? upgradeMap = null)
    {
        var id = ResolveUpgradedId(upgradeMap);
        if (!string.IsNullOrWhiteSpace(id))
        {
            return id;
        }

        throw new InvalidOperationException("CardDefinition has no upgraded id mapping.");
    }

    public static void ValidateId(string id)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("CardDefinition.Id must not be empty.", nameof(id));
        }

        var trimmed = id.Trim();
        if (trimmed.All(char.IsDigit) && long.TryParse(trimmed, out var numeric) && numeric <= 0)
        {
            throw new ArgumentException("CardDefinition.Id must be > 0 when numeric.", nameof(id));
        }
    }

    public static void ValidateName(string name)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("CardDefinition.Name must not be empty.", nameof(name));
        }
    }

    public static void ValidateCost(int cost)
    {
        if (cost < MinCost || cost > MaxCost)
        {
            throw new ArgumentOutOfRangeException(nameof(cost), cost, $"CardDefinition.Cost must be within [{MinCost}, {MaxCost}].");
        }
    }

    public static void ValidateEffectCommands(IReadOnlyList<EffectCommand>? effectCommands)
    {
        if (effectCommands is null)
        {
            return;
        }

        for (var i = 0; i < effectCommands.Count; i++)
        {
            var cmd = effectCommands[i];
            if (cmd is null)
            {
                throw new ArgumentException("CardDefinition.EffectCommands must not contain null items.", nameof(effectCommands));
            }

            if (string.IsNullOrWhiteSpace(cmd.Kind))
            {
                throw new ArgumentException("EffectCommand.Kind must not be empty.", nameof(effectCommands));
            }
        }
    }

    public static void ValidateTextKey(string textKey)
    {
        if (string.IsNullOrWhiteSpace(textKey))
        {
            throw new ArgumentException("CardDefinition.TextKey must not be empty.", nameof(textKey));
        }
    }

    public static void ValidateRarity(string rarity)
    {
        if (string.IsNullOrWhiteSpace(rarity))
        {
            throw new ArgumentException("CardDefinition.Rarity must not be empty.", nameof(rarity));
        }
    }

    public static void ValidateClassTag(string classTag)
    {
        if (string.IsNullOrWhiteSpace(classTag))
        {
            throw new ArgumentException("CardDefinition.ClassTag must not be empty.", nameof(classTag));
        }
    }

    public static void ValidateUpgradeId(string id, string? upgradedId)
    {
        if (upgradedId is null)
        {
            return;
        }

        if (string.IsNullOrWhiteSpace(upgradedId))
        {
            throw new ArgumentException("CardDefinition.UpgradedId must be null or non-empty.", nameof(upgradedId));
        }

        if (string.Equals(id, upgradedId, StringComparison.Ordinal))
        {
            throw new ArgumentException("CardDefinition.UpgradedId must not equal Id.", nameof(upgradedId));
        }
    }
}

public sealed record CardInstance
{
    public CardDefinition Definition { get; init; }
    public int TemporaryCostDelta { get; init; }
    public IReadOnlySet<string> TurnFlags { get; init; }
    public bool IsUpgraded { get; init; }

    public CardInstance(
        CardDefinition Definition,
        int TemporaryCostDelta,
        IReadOnlySet<string> TurnFlags,
        bool IsUpgraded
    )
    {
        this.Definition = Definition ?? throw new ArgumentNullException(nameof(Definition));
        this.TemporaryCostDelta = TemporaryCostDelta;
        this.TurnFlags = new HashSet<string>(TurnFlags is null ? Array.Empty<string>() : TurnFlags, StringComparer.Ordinal);
        this.IsUpgraded = IsUpgraded;
    }

    public static CardInstance CreateOrThrow(CardDefinition definition)
    {
        return new CardInstance(
            Definition: definition ?? throw new ArgumentNullException(nameof(definition)),
            TemporaryCostDelta: 0,
            TurnFlags: new HashSet<string>(StringComparer.Ordinal),
            IsUpgraded: false
        );
    }

    public static CardInstance CreateOrThrow(
        CardDefinition definition,
        int temporaryCostDelta,
        IReadOnlySet<string>? turnFlags,
        bool isUpgraded,
        IReadOnlyDictionary<string, string>? upgradeMap = null
    )
    {
        if (definition is null)
        {
            throw new ArgumentNullException(nameof(definition));
        }

        ValidateUpgradeId(definition, isUpgraded, upgradeMap);

        return new CardInstance(
            Definition: definition,
            TemporaryCostDelta: temporaryCostDelta,
            TurnFlags: turnFlags ?? new HashSet<string>(StringComparer.Ordinal),
            IsUpgraded: isUpgraded
        );
    }

    public static void ValidateUpgradeId(
        CardDefinition definition,
        bool isUpgraded,
        IReadOnlyDictionary<string, string>? upgradeMap = null
    )
    {
        if (!isUpgraded)
        {
            return;
        }

        _ = definition.GetUpgradedIdOrThrow(upgradeMap);
    }
}
