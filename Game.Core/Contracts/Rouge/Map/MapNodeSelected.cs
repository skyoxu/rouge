namespace Game.Core.Contracts.Rouge.Map;

/// <summary>
/// Domain event: core.map.node.selected
/// Description: Emitted when the player selects the next reachable node.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record MapNodeSelected(
    string RunId,
    string NodeId,
    string NodeType, // see MapNodeTypes
    int Depth,
    DateTimeOffset SelectedAt
)
{
    public const string EventType = "core.map.node.selected";
}
