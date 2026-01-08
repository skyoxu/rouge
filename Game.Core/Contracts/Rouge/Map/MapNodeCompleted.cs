namespace Game.Core.Contracts.Rouge.Map;

/// <summary>
/// Domain event: core.map.node.completed
/// Description: Emitted when a node's content is completed and control returns to the map.
/// </summary>
/// <remarks>
/// Follows ADR-0004 event contracts for the domain. Contract location per ADR-0020.
/// </remarks>
public sealed record MapNodeCompleted(
    string RunId,
    string NodeId,
    string NodeType, // see MapNodeTypes
    string Result, // see MapNodeResults
    DateTimeOffset CompletedAt
)
{
    public const string EventType = "core.map.node.completed";
}
