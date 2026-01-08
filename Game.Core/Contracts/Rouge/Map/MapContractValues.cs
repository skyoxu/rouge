namespace Game.Core.Contracts.Rouge.Map;

/// <summary>
/// Allowed values for <see cref="MapNodeSelected.NodeType"/> and <see cref="MapNodeCompleted.NodeType"/>.
/// </summary>
public static class MapNodeTypes
{
    public const string Battle = "battle";
    public const string Elite = "elite";
    public const string Boss = "boss";
    public const string Shop = "shop";
    public const string Rest = "rest";
    public const string Event = "event";
    public const string Treasure = "treasure";

    public static readonly string[] All =
    {
        Battle,
        Elite,
        Boss,
        Shop,
        Rest,
        Event,
        Treasure,
    };
}

/// <summary>
/// Allowed values for <see cref="MapNodeCompleted.Result"/>.
/// </summary>
public static class MapNodeResults
{
    public const string Ok = "ok";
    public const string Fail = "fail";
    public const string Aborted = "aborted";

    public static readonly string[] All =
    {
        Ok,
        Fail,
        Aborted,
    };
}

