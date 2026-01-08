---
title: 11 risks and technical debt v2
status: base-SSoT
adr_refs: [ADR-0005, ADR-0019, ADR-0015, ADR-0003]
placeholders: Unknown Product, unknown-product, gamedev, dev, production, 0.0.0
derived_from: 11-risks-and-technical-debt-v2.md
last_generated: 2026-01-08
---

> 目标：统一风险与技术债的记录方式，确保每一条风险/债务都能在 CI 工件与 Issue 中被追踪（与 CH07/CH03/CH02/CH09 对齐）。

## 1. 风险（Risks）

- 每条风险必须有 owner、影响面、触发条件、缓解措施与取证路径（`logs/**` + Issue/PR）。
- 优先级建议：先安全/数据损坏/不可回滚，再性能/可玩性，再体验/便利性。

示例（仅示例，按项目实际补充）：

| 风险ID | 描述 | 影响 | 可能性 | 缓解/检测 | 取证 |
| --- | --- | --- | --- | --- | --- |
| R-SEC-01 | 外链/文件越权导致安全事故 | 高 | 中 | CH02 + 安全烟测 + 审计 | `logs/ci/<date>/security-*.jsonl` |
| R-PERF-01 | 帧耗时回退导致卡顿 | 中 | 中 | CH09 perf smoke + perf gate | `logs/perf/<date>/summary.json` |

## 2. 技术债（Technical Debt）

- 允许有技术债，但必须“可回迁”：写清 owner、截止日期、Issue 链接与回迁计划。
- 任何临时放行（例如安全策略放宽/门禁阈值放宽）必须在 PR 说明，并落 Issue。
- 取证优先：把当时的 `logs/**` 工件附在 Issue 里，便于复盘。

## 3. 与 CH03/CH07 的关系

- CH03：可观测性与取证落盘。
- CH07：质量门禁与 CI 运行方式。
- CH11：风险/债务如何记录与追踪（本页）。
