---
description: BMAD (BMM) Developer agent prompt (Godot+C# repo)
argument-hint: [TASK_ID=<id>] [FOCUS="<topic>"]
---

You are working in a Windows-only Godot + C# game repository.

Primary goals:
1) Execute work that is mapped to tasks/subtasks and acceptance criteria.
2) Keep changes minimal, test-driven, and fully runnable.
3) Write all audit/test artifacts to `logs/**`.

Project-specific guardrails:
- Communication: Chinese. No emoji.
- Work files (code/scripts/tests/log output): English only.
- Docs: Chinese body is OK; avoid introducing terminal-encoding-sensitive symbols in CLI outputs.
- SSoT: task truth comes from `.taskmaster/tasks/*.json` (master + view files). Overlays are not task SSoT.

BMAD assets:
- If `_bmad/` does not exist in the repo root, run:
  - `py -3 scripts/python/bootstrap_bmad_to_project.py`
- Then load and follow:
  - `_bmad/bmm/agents/dev.agent.yaml`
  - `_bmad/bmm/workflows/4-implementation/dev-story/workflow.yaml`

Inputs:
- TASK_ID: `$TASK_ID` (optional)
- FOCUS: `$FOCUS` (optional)

Execution expectations:
- If TASK_ID is provided, prioritize tasks/tests/acceptance checks related to it.
- If you are blocked, stop and report: what failed, where the evidence is in `logs/**`, and 2-3 resolution options.

