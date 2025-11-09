---
ADR-ID: ADR-0021
title: C# Domain Layer Architecture
status: Accepted
decision-time: '2025-11-08'
deciders: [Architecture Team]
archRefs: [CH04, CH05]
depends-on: []
supersedes: []
---

# ADR-0021: C# Domain Layer Architecture

## Context
Separate core game logic from Godot runtime via a clean domain layer in C#.

## Decision
- Projects: `Game.Core` (pure C#), `Game.Core.Tests` (xUnit).
- Structure: Domain (Entities, ValueObjects), Services, Interfaces (ports).
- Adapters: Godot-facing layer implements ports (time, input, resource load).
- Testing: domain covered by xUnit; adapters by xUnit with fakes.

## Consequences
- Positive: deterministic tests; portability; clearer seams for AI-assisted code.
- Negative: extra adapter code; discipline to avoid Godot leakage into domain.

## References
- Ports & Adapters pattern
