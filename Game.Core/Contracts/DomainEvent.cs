using System;

namespace Game.Core.Contracts;

/// <summary>
/// CloudEvents-like event envelope used by the in-process event bus.
/// </summary>
/// <remarks>
/// Baseline follows ADR-0004 (type/source/id/specversion). The payload is stored as JSON text to keep
/// this contract engine-agnostic and testable in pure .NET without Godot dependencies.
/// </remarks>
public sealed record DomainEvent(
    string Type,
    string Source,
    string DataJson,
    DateTimeOffset Timestamp,
    string Id,
    string SpecVersion = "1.0",
    string DataContentType = "application/json"
);

