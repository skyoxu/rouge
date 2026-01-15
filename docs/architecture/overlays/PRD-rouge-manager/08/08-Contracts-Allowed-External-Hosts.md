---
PRD-ID: PRD-rouge-manager
Title: 外链白名单（AllowedDomains / ALLOWED_EXTERNAL_HOSTS）契约调整
Status: Proposed
ADR-Refs:
  - ADR-0019
  - ADR-0004
  - ADR-0005
Arch-Refs:
  - CH01
  - CH03
Test-Refs:
  - Tests.Godot/tests/Integration/Security/test_security_http_allowed_audit.gd
  - Tests.Godot/tests/Integration/Security/test_security_http_audit.gd
  - Tests.Godot/tests/Integration/Security/test_security_http_block_signal.gd
  - Tests.Godot/tests/Integration/Security/test_security_http_client.gd
---

## Scope
- 本页记录该纵切需要的外链与主机白名单口径（便于审计）。

## Non-goals
- 不写详细网络实现；不写外网依赖的引入方案。

## References
- ADR-Refs: ADR-0019, ADR-0004, ADR-0005
- Arch-Refs: CH01, CH03
- Related: `_index.md`

本页为功能纵切（08 章）对应“外链白名单（AllowedDomains / ALLOWED_EXTERNAL_HOSTS）”契约的变更说明与验收约束。

变更意图（引用，不复制口径）

- 引用 01/02/03 章的统一口径：事件与契约治理（ADR-0004）、质量门禁（ADR-0005）。
- 在 Godot + C# 模板中，外链访问必须通过白名单统一管理（见 ADR-0019）；任何新增对外暴露能力需在契约中显式声明并通过此页落档。

适用范围（Rouge PRD 约束）

- 本项目为单机单人离线游戏；默认不依赖任何外部联网能力。
- 唯一允许的出网场景应当是“可选的可观测性/崩溃上报”（如 Sentry），且必须满足：
  - 仅 HTTPS
  - Host 白名单
  - 失败必审计（security audit）

影响范围

- 相关实现（见 Contracts-Refs）：
  - HTTP 外链校验与审计：`Game.Godot/Scripts/Security/SecurityHttpClient.cs`
  - 安全基线审计：`Game.Godot/Scripts/Security/SecurityAudit.cs`
- 受影响模块：外链访问、审计日志与安全告警链路

验收要点（就地）

- GdUnit4 测试覆盖 allow/deny/invalid 三态，并校验审计输出存在（见 Test-Refs）
- 未授权外链不得通过（包括非 https、file://、非白名单域名、方法不在白名单等）

回归与风控

- 仅允许通过统一的 SecurityHttpClient 暴露出网能力；禁止绕过 ADR-0019 中定义的 Godot 安全基线（外链/文件/权限等约束）。

