---
PRD-ID: PRD-rouge-manager
Title: 安全事件与策略契约更新（Security Contracts）
Status: Proposed
ADR-Refs:
  - ADR-0019
  - ADR-0004
  - ADR-0005
Arch-Refs:
  - CH01
  - CH03
Test-Refs:
  - Tests.Godot/tests/Scenes/Smoke/test_main_scene_smoke.gd
  - Tests.Godot/tests/Security/Hard/test_db_open_denied_writes_audit_log.gd
  - Tests.Godot/tests/Security/Hard/test_db_path_rejection.gd
  - Tests.Godot/tests/Integration/Security/test_security_http_audit.gd
---

## Scope
- 本页说明该纵切中安全口径的落点，只引用 Base/ADR，避免重复。

## Non-goals
- 不复制策略与阈值；不超越本页责任范围写其他模块的规范。

## References
- ADR-Refs: ADR-0019, ADR-0004, ADR-0005
- Arch-Refs: CH01, CH03
- Related: `_index.md`

本页为功能纵切（08 章）对应“Security Contracts”变更登记与验收要点（仅引用 01/02/03 章口径，不复制阈值/策略）。

变更意图（引用）

- Godot 安全基线：见 ADR-0019（资源与文件访问、外链与权限约束）
- 契约与事件统一：见 ADR-0004
- 质量门禁与发布健康：见 ADR-0005

影响范围

- 相关实现（见 Contracts-Refs）：
  - 外链审计与阻断：`Game.Godot/Scripts/Security/SecurityHttpClient.cs`
  - 安全基线审计：`Game.Godot/Scripts/Security/SecurityAudit.cs`
  - 数据库路径安全（user:// + 禁止 traversal）：`Game.Godot/Adapters/SqliteDataStore.cs`
- 受影响模块：安全校验、审计日志与告警链路

验收要点

- GdUnit4 场景测试存在（见 Test-Refs），覆盖：外链审计、DB 路径拒绝、审计落盘
- 失败路径必须产生审计条目，且不允许吞错导致静默放行

