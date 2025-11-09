---
ADR-ID: ADR-0020
title: Godot Test Strategy (TDD + GdUnit4)
status: Accepted
decision-time: '2025-11-08'
deciders: [Architecture Team]
archRefs: [CH07]
depends-on: []
supersedes: []
---

# ADR-0020: Godot Test Strategy (TDD + GdUnit4)

## Context
Rebuild test pyramid for Godot+C# stack and CLI-friendly execution with reports.

## Decision
- Unit (80%): xUnit + FluentAssertions + NSubstitute for pure C# logic.
- Scene (15%): GdUnit4 for node lifecycle, signals, resources.
- E2E (5%): headless smoke; only key flows.
- Reports: GdUnit4 HTML/JUnit to `reports/`; coverage via coverlet.

## Execution
- Windows: `addons\gdUnit4\runtest.cmd --godot_binary %GODOT_BIN% -a res://tests`
- Direct: `"%GODOT_BIN%" --path . -s -d res://addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests`
- Headless: add `--ignoreHeadlessMode` when needed.

## Consequences
- Positive: fast feedback on C#; stable scene tests; CI-friendly outputs.
- Negative: two frameworks to maintain; discipline needed for pyramid shape.

## References
- docs/testing-framework.md
- GdUnit4 documentation
