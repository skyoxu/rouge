---
title: 03 observability sentry logging v2
status: base-SSoT
adr_refs: [ADR-0003, ADR-0005, ADR-0018, ADR-0019, ADR-0011]
placeholders: unknown-app, Unknown Product, dev-team, production
last_generated: 2026-01-08
---

> 目标：在 Godot+C#（Windows-only）运行时建立最小可执行的可观测性基线：结构化日志、审计日志、Sentry Release Health，以及 CI 侧的取证工件（`logs/**`）。

## 1. `logs/**`：取证与排障的 SSoT

- 所有脚本/测试/审计输出统一落盘 `logs/**`（目录规范见“6.3 日志与工件（SSoT）”）。
- 推荐分层（只举例，不在 Overlay 08 复制）：
  - `logs/ci/<YYYY-MM-DD>/...`：CI 门禁、扫描、回链校验、Release Health
  - `logs/unit/<YYYY-MM-DD>/...`：xUnit + coverage
  - `logs/e2e/<YYYY-MM-DD>/...`：GdUnit4/headless 报告与截图
  - `logs/perf/<YYYY-MM-DD>/...`：性能烟测摘要（p50/p95 等）

### 1.1 安全审计（引用 ADR-0019）

- 审计采用逐行 JSON：`security-audit.jsonl`（JSONL）。
- 最小字段：`{ ts, action, reason, target, caller }`。
- 规则：不写敏感数据；必要时对 `target` 做脱敏/截断；失败必须审计。

## 2. Sentry：错误跟踪 + Release Health（引用 ADR-0003）

- 初始化时机：最早 Autoload 初始化 Sentry SDK（避免漏报启动期崩溃）。
- 目标：启用 Releases + Sessions，计算 Crash-Free Sessions/Users（用于发布健康门禁）。
- 采样与脱敏：遵循 ADR-0003 / ADR-0019；日志/事件字段做最小必要采集与脱敏。

Sentry secrets 预检（本地/CI）：
- `py -3 scripts/python/check_sentry_secrets.py`

## 3. Release Health 门禁对齐（引用 CH01/CH07）

- 阈值口径只在 ADR/Base 维护；Overlay 08 只能引用，不复制数字或策略文本。
- CI 产出建议：`logs/ci/<YYYY-MM-DD>/release-health.json`。

## 4. 性能标记（PERF markers，引用 ADR-0015）

- Headless smoke 过程可以输出 `[PERF] ...` marker（例如 `p95_ms`、`startup_ms`）。
- `scripts/ci/check_perf_budget.ps1` 解析 marker 并输出 perf 摘要到 `logs/perf/**`（门禁口径见 ADR-0015/CH09）。

## 5. 最小验收

- CI 里能找到 `logs/ci/**` 的摘要，并能回溯到 raw stdout/stderr。
- （可选）启用 Sentry 时，能看到对应 Release 的 Sessions，Release Health 可计算。
