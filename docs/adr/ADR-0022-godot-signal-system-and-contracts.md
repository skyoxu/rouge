---
ADR-ID: ADR-0022
title: Godot Signal System and Contracts
status: Accepted
decision-time: '2025-11-08'
deciders: [Architecture Team]
archRefs: [CH08]
depends-on: [ADR-0018]
supersedes: [ADR-0004]
---

# ADR-0022: Godot Signal System and Contracts

## Context
Map vitegame event bus/CloudEvents contracts to Godot Signals with clear naming and ownership.

## Decision
- Use Signals for intra-scene events; Autoload singleton as global bus when needed.
- Naming: `snake_case` for signals; document payload shapes in contracts.
- Decouple: emit/subscribe via small adapter methods; avoid direct node coupling.

## Consequences
- Positive: simpler runtime model; editor-visible wiring; fewer runtime deps.
- Negative: requires contract docs and discipline to avoid tight coupling.

## References
- Godot Signals docs
