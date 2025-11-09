---
ADR-ID: ADR-0018
title: Godot Runtime and Distribution
status: Accepted
decision-time: '2025-11-08'
deciders: [Architecture Team]
archRefs: [CH01, CH07]
depends-on: [ADR-0011]
supersedes: [ADR-0001]
---

# ADR-0018: Godot Runtime and Distribution

## Context
Replace Electron/Phaser stack with Godot 4.5 (.NET) for Windows-only runtime. Standardize packaging, export, and runtime policies.

## Decision
- Engine: Godot 4.5.x (.NET/mono) pinned; tooling .NET 8 LTS.
- Platform: Windows Desktop only; export via official export templates.
- Artifacts: `.exe` + `.pck` distribution; cache export templates in CI.
- Paths: Use `res://` for resources, `user://` for writable data.

## Consequences
- Positive: Unified runtime + editor, faster startup, simpler deploy.
- Negative: Full rewrite of UI/renderer/test stack; retraining on Scene Tree/Signals.

## Implementation Notes
- Add export presets; ensure templates installed on CI.
- Document `GODOT_BIN` usage for CLI build/test.
- Keep Godot minor versions aligned across team.

## References
- Godot docs: https://docs.godotengine.org/en/stable/
- C# in Godot: https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/
