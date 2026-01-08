---
title: 12 glossary v2
status: base-SSoT
adr_refs: [ADR-0003, ADR-0004, ADR-0005, ADR-0018, ADR-0019]
placeholders: unknown-app, Unknown Product, unknown-product, gamedev, dev-team, dev-project, dev, 0.0.0, production, ${I18N_KEY_PREFIX}
derived_from: 12-glossary-v2.md
last_generated: 2026-01-08
---

> 目标：统一仓库关键术语，减少新人/LLM 误读。

## 术语表（Base）

- **ADR**：Architecture Decision Record。`Accepted` 表示当前有效口径；`Superseded` 表示已被替代。
- **SSoT**：Single Source of Truth。阈值/策略/契约等应有唯一权威来源，避免复制导致漂移。
- **Base-Clean**：`docs/architecture/base/**` 的清洁版本；禁止出现具体 `PRD_ID` 标识与具体 08 内容。
- **Overlay 08**：`docs/architecture/overlays/<PRD_ID>/08/**` 的功能纵切章节；只做引用与验收，不复制阈值。
- **Contracts**：事件/DTO/端口契约的 SSoT，落盘 `Game.Core/Contracts/**`，不依赖 `Godot.*`。
- **Domain Event**：领域事件（跨模块/跨层通信）。EventType 遵循 ADR-0004 的 `core.*.*`/`ui.menu.*`/`screen.*.*`。
- **Signal (Godot)**：Godot 的信号机制，用于节点间事件；通常只作为 UI glue/适配层转发。
- **Autoload**：Godot 项目设置中的全局单例节点。用于初始化事件总线/配置/Sentry 等（按 ADR 约束）。
- **res://**：Godot 资源路径（只读）。
- **user://**：Godot 用户数据路径（读写）。所有写入必须走白名单与审计（ADR-0019）。
- **Headless**：无窗口模式运行（CI 冒烟/安全/性能常用），输出落 `logs/**`。
- **xUnit**：.NET 单元测试框架，用于 Core 层快速 TDD。
- **GdUnit4**：Godot 集成测试框架，用于 Scenes/Signals/headless 测试。
- **Release Health**：发布健康度（Crash-Free Sessions/Users）。门禁口径见 ADR-0003。
- **Crash-Free Sessions/Users**：Sentry Sessions 指标，用于衡量崩溃率与放量门禁。
