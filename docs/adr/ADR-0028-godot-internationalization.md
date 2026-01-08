---
ADR-ID: ADR-0028
title: 国际化策略（Godot TranslationServer + 资源约定）
status: Accepted
decision-time: '2026-01-08'
deciders: [架构团队, UX团队]
archRefs: [CH10]
verification:
  - path: docs/architecture/base/10-i18n-ops-release-v2.md
    assert: Base i18n guidance aligns with Godot runtime and does not reference web toolchains
impact-scope:
  - Game.Godot/
  - Assets/i18n/
tech-tags: [i18n, godot, windows-only]
depends-on: [ADR-0018, ADR-0011]
depended-by: []
supersedes: [ADR-0010]
---

# ADR-0028: 国际化策略（Godot TranslationServer + 资源约定）

## Context and Problem Statement

本仓库已迁移为 Godot+C#（Windows-only）项目（ADR-0018/ADR-0011）。旧的 Web/i18next 方案不再适用，需要一套与 Godot 运行时一致、可测试、可演进的国际化策略，满足：

- UI 文本不硬编码，支持运行时切换语言
- 资源文件可版本化、可审阅（避免口径漂移）
- 不引入 Web/Node 工具链作为硬依赖

## Decision

- 使用 Godot 原生国际化能力：`TranslationServer` + 翻译资源（`.translation` 或 `.po`）。
- 文本 key 作为稳定标识：推荐 `${I18N_KEY_PREFIX}.<screen>.<control>.<text>`（仅为示例，具体按 Overlay 纵切落地）。
- 资源组织建议：
  - `res://Assets/i18n/<locale>.*`（例如 `zh-Hans.po`, `en.po`）
  -（可选）对大模块拆分 namespace（避免单文件过大）
- 测试策略：
  - 领域层不依赖 i18n（避免把文案写进 Core），UI 层通过 key 映射展示；
  - 场景测试（GdUnit4）只验证“语言切换后关键控件文本变化/回退语言生效”。  

## Consequences

- 优点：与 Godot 运行时一致；无需额外前端/Node 依赖；资源可审阅。
- 代价：需要维护 key 规范与翻译资源；需要在 UI 层建立统一的文本装配方式（避免散落）。
