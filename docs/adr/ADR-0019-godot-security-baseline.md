---
ADR-ID: ADR-0019
title: Godot Security Baseline
status: Accepted
decision-time: '2025-11-08'
deciders: [Architecture Team]
archRefs: [CH02]
depends-on: [ADR-0011]
supersedes: [ADR-0002]
---

# ADR-0019: Godot Security Baseline

## Context
Electron security policies must be replaced with Godot-native guardrails for IO, HTTP, URL open, and runtime isolation.

## Decision
- External links: restrict to allowlist; wrap `OS.shell_open()` as `Security.open_url_safe()`.
- HTTP: centralize via wrapper on `HTTPRequest` with domain allowlist and audit logs.
- File system: restrict writes to `user://`; block absolute paths in game code.
- Code loading: forbid dynamic/native DLL loading and P/Invoke in gameplay code.
- Autoload: dedicated `Security` singleton to enforce and audit.
- Observability: integrate Sentry (Godot SDK) with user/session scrubbing.

## Consequences
- Positive: predictable, auditable interactions; reduced attack surface.
- Negative: adapters required; stricter review for any new IO/HTTP use.

## Verification
- CI script scans `.gd`/`.cs` for forbidden APIs; unit tests cover wrappers.
- GdUnit4 scenes verify guardrails on common scenarios.

## References
- Godot HTTPRequest, OS APIs
- Sentry Godot SDK
