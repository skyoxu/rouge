# 架构文档完整性检查清单（Base）

## 1) 核心 ADR 覆盖

### ADR-0019（安全基线）

- [ ] 路径策略：只允许 `res://`（只读）与 `user://`（读写），拒绝绝对/越权路径。
- [ ] 外链/网络：仅 HTTPS + 主机白名单；`GD_OFFLINE_MODE=1` 时拒绝出网并审计。
- [ ] OS.execute：默认禁用；CI/headless 下权限默认拒绝。
- [ ] 审计：失败必须落 `logs/**`（JSONL）。

### ADR-0003（可观测性与 Release Health）

- [ ] `logs/**` 取证口径明确且一致。
- [ ] Sentry 初始化时机与 Releases+Sessions 口径明确。
- [ ] Release Health 工件路径明确：`logs/ci/<date>/release-health.json`。

### ADR-0004（事件总线与契约）

- [ ] `EventType` 命名符合 `core.*.*` / `ui.menu.*` / `screen.*.*`。
- [ ] 契约 SSoT 在 `Game.Core/Contracts/**`，且不依赖 `Godot.*`。

### ADR-0005（质量门禁）

- [ ] `dotnet build -warnaserror` 作为编译门禁。
- [ ] `dotnet test` 运行 xUnit 单测。
- [ ] Godot headless smoke 可运行（例如 `scripts/ci/smoke_headless.ps1`）。
- [ ] 任务/文档回链可校验：`py -3 scripts/python/task_links_validate.py`。

## 2) Base-Clean 章节齐全

- [ ] `docs/architecture/base/00-README.md`
- [ ] `docs/architecture/base/01-introduction-and-goals-v2.md`
- [ ] `docs/architecture/base/02-security-baseline-godot-v2.md`
- [ ] `docs/architecture/base/03-observability-sentry-logging-v2.md`
- [ ] `docs/architecture/base/04-system-context-c4-event-flows-v2.md`
- [ ] `docs/architecture/base/05-data-models-and-storage-ports-v2.md`
- [ ] `docs/architecture/base/06-runtime-view-loops-state-machines-error-paths-v2.md`
- [ ] `docs/architecture/base/07-dev-build-and-gates-v2.md`
- [ ] `docs/architecture/base/08-crosscutting-and-feature-slices.base.md`
- [ ] `docs/architecture/base/09-performance-and-capacity-v2.md`
- [ ] `docs/architecture/base/10-i18n-ops-release-v2.md`
- [ ] `docs/architecture/base/11-risks-and-technical-debt-v2.md`
- [ ] `docs/architecture/base/12-glossary-v2.md`

## 3) 最小可执行验证集（本地/CI）

- [ ] Base 清洁度：`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ci/verify_base_clean.ps1`
- [ ] UTF-8/疑似乱码扫描：`py -3 scripts/python/check_encoding.py --root docs`
- [ ] 旧栈术语（严格）：`py -3 scripts/python/scan_doc_stack_terms.py --root docs/architecture/base --fail-on-hits`
- [ ] 旧栈术语（取证）：`py -3 scripts/python/scan_doc_stack_terms.py --root docs --out logs/ci/<date>/doc-stack-scan/full`
- [ ] 一键质量门禁：`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ci/quality_gate.ps1 -GodotBin $env:GODOT_BIN`

---

_提示：如果终端显示“乱码”，以 `logs/**` 中的 JSON 报告为准，不要用复制粘贴覆盖源文件。_
