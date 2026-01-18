# rouge 项目文档索引（SSoT）

> 最后更新：2025-12-21  
> 适用范围：本仓库（Windows-only，Godot 4.5 + C#/.NET 8）

本索引用于把“当前口径的入口”集中到一个地方，避免旧项目/旧技术栈文档对人或 LLM 造成误导。

---

## 0. 快速入口（先读这些）

- 项目快速上手：[`../README.md`](../README.md)
- 协作规则（单一真相来源）：[`../AGENTS.md`](../AGENTS.md)
- 补充规则/写作约束：[`../CLAUDE.md`](../CLAUDE.md)
- 测试框架（xUnit + GdUnit4）：[`testing-framework.md`](testing-framework.md)
- 文档口径全量收敛手册（Base + Migration）：[`workflows/doc-stack-convergence-guide.md`](workflows/doc-stack-convergence-guide.md)
- 项目能力状态总览（模板能力/Backlog）：[`PROJECT_CAPABILITIES_STATUS.md`](PROJECT_CAPABILITIES_STATUS.md)

---

## 1. ADR（架构决策记录）

ADR 是“当前有效口径”的决策记录，任何改变阈值/契约/安全口径的变更，都应新增或 Supersede 对应 ADR。

- ADR 目录：[`adr/`](adr/)
- ADR 索引（Godot 口径）：[`architecture/ADR_INDEX_GODOT.md`](architecture/ADR_INDEX_GODOT.md)

建议优先阅读（与本仓库主干强相关）：

- 技术栈与平台：[`adr/ADR-0018-godot-runtime-and-distribution.md`](adr/ADR-0018-godot-runtime-and-distribution.md)、[`adr/ADR-0011-windows-only-platform-and-ci.md`](adr/ADR-0011-windows-only-platform-and-ci.md)
- 安全基线：[`adr/ADR-0019-godot-security-baseline.md`](adr/ADR-0019-godot-security-baseline.md)
- 可观测性与发布健康：[`adr/ADR-0003-observability-release-health.md`](adr/ADR-0003-observability-release-health.md)
- 事件总线与契约：[`adr/ADR-0004-event-bus-and-contracts.md`](adr/ADR-0004-event-bus-and-contracts.md)、[`adr/ADR-0020-contract-location-standardization.md`](adr/ADR-0020-contract-location-standardization.md)、[`adr/ADR-0022-godot-signal-system-and-contracts.md`](adr/ADR-0022-godot-signal-system-and-contracts.md)
- 质量门禁与性能预算：[`adr/ADR-0005-quality-gates.md`](adr/ADR-0005-quality-gates.md)、[`adr/ADR-0015-performance-budgets-and-gates.md`](adr/ADR-0015-performance-budgets-and-gates.md)
- 测试策略：[`adr/ADR-0024-godot-test-strategy.md`](adr/ADR-0024-godot-test-strategy.md)

---

## 2. Base-Clean 架构文档（arc42 12 章）

Base 文档是跨切面与系统骨干的 SSoT：只写可复用口径与约束；禁止出现具体 PRD-ID；禁止在 Base 写具体“功能纵切”。

- Base 入口：[`architecture/base/00-README.md`](architecture/base/00-README.md)
- 01 引言与目标：[`architecture/base/01-introduction-and-goals-v2.md`](architecture/base/01-introduction-and-goals-v2.md)
- 02 安全基线（Godot）：[`architecture/base/02-security-baseline-godot-v2.md`](architecture/base/02-security-baseline-godot-v2.md)
- 03 可观测性与日志：[`architecture/base/03-observability-sentry-logging-v2.md`](architecture/base/03-observability-sentry-logging-v2.md)
- 04 系统上下文与事件流：[`architecture/base/04-system-context-c4-event-flows-v2.md`](architecture/base/04-system-context-c4-event-flows-v2.md)
- 05 数据模型与存储端口：[`architecture/base/05-data-models-and-storage-ports-v2.md`](architecture/base/05-data-models-and-storage-ports-v2.md)
- 06 运行时/循环/状态机：[`architecture/base/06-runtime-view-loops-state-machines-error-paths-v2.md`](architecture/base/06-runtime-view-loops-state-machines-error-paths-v2.md)
- 07 Dev/Build/Gates：[`architecture/base/07-dev-build-and-gates-v2.md`](architecture/base/07-dev-build-and-gates-v2.md)
- 08 功能纵切模板（Base 仅模板）：[`architecture/base/08-crosscutting-and-feature-slices.base.md`](architecture/base/08-crosscutting-and-feature-slices.base.md)
- 09 性能与容量：[`architecture/base/09-performance-and-capacity-v2.md`](architecture/base/09-performance-and-capacity-v2.md)
- 10 i18n/Ops/Release：[`architecture/base/10-i18n-ops-release-v2.md`](architecture/base/10-i18n-ops-release-v2.md)
- 11 风险与技术债：[`architecture/base/11-risks-and-technical-debt-v2.md`](architecture/base/11-risks-and-technical-debt-v2.md)
- 12 术语表：[`architecture/base/12-glossary-v2.md`](architecture/base/12-glossary-v2.md)

辅助文档：

- 完整性检查清单：[`architecture/base/architecture-completeness-checklist.md`](architecture/base/architecture-completeness-checklist.md)
- Front-Matter 规范示例：[`architecture/base/front-matter-standardization-example.md`](architecture/base/front-matter-standardization-example.md)

---

## 3. Overlays（功能纵切：08 章）

Overlay 用于落地“具体 PRD 的功能纵切”，08 章只描述纵切（实体/事件/验收/测试占位/SLI），跨切面口径一律引用 Base/ADR，禁止复制阈值。

- Rouge 纵切索引：[`architecture/overlays/PRD-rouge-manager/08/_index.md`](architecture/overlays/PRD-rouge-manager/08/_index.md)
- Rouge 验收清单：[`architecture/overlays/PRD-rouge-manager/08/ACCEPTANCE_CHECKLIST.md`](architecture/overlays/PRD-rouge-manager/08/ACCEPTANCE_CHECKLIST.md)

---

## 4. PRD 与任务（Taskmaster）

- PRD（SSoT）：`.taskmaster/docs/prd.txt`
- 任务清单：`.taskmaster/tasks/tasks.json`

常用命令（Windows）：

- 生成/更新 Tasks（可选）：`npx task-master parse-prd .taskmaster\\docs\\prd.txt -n <num>`
- BMAD（可选，Windows）：`py -3 scripts/python/run_bmad.py -- --version`（避免 PowerShell 执行策略阻止 `npm.ps1`）
- 校验任务/回链：`py -3 scripts\\python\\task_links_validate.py`

---

## 5. 工作流与脚本（Windows）

工作流文档（按需阅读）：

- Taskmaster + SuperClaude 协作指南：[`workflows/task-master-superclaude-integration.md`](workflows/task-master-superclaude-integration.md)
- Serena 使用参考：[`workflows/serena-mcp-command-reference.md`](workflows/serena-mcp-command-reference.md)
- SuperClaude 命令参考：[`workflows/superclaude-command-reference.md`](workflows/superclaude-command-reference.md)

本地可复现入口（产物统一落 `logs/**`）：

- Base-Clean（硬门禁）：`powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\ci\\verify_base_clean.ps1`
- 一键门禁（建议）：`py -3 scripts\\python\\quality_gates.py --typecheck --lint --unit --scene --security --perf`
- 编码与疑似乱码扫描：`py -3 scripts\\python\\check_encoding.py --root docs`、`py -3 scripts\\python\\scan_garbled.py --root docs`
- 旧技术栈术语扫描（取证）：`py -3 scripts\\python\\scan_doc_stack_terms.py --root docs --out logs\\ci\\<YYYY-MM-DD>\\doc-stack-scan\\full`
- 旧技术栈术语扫描（严格，硬门禁范围：Base + 入口 + Overlay 08）：`py -3 scripts\python\scan_doc_stack_terms.py --root docs\architecture\base --fail-on-hits --out logs\ci\<YYYY-MM-DD>\doc-stack-scan\base`（入口/Overlay 见收敛手册；CI 由 `scripts/python/ci_pipeline.py` 执行）

---

## 6. 迁移归档（仅对照，不代表当前口径）

迁移文档用于保留过程对照材料；如必须提及旧技术栈，优先使用“旧桌面壳/旧前端栈/旧项目”等中性描述，避免被误读为当前口径。

- Migration 索引：[`migration/MIGRATION_INDEX.md`](migration/MIGRATION_INDEX.md)
- Legacy Base：[`migration/legacy-base/`](migration/legacy-base/)
- Legacy Overlays：[`migration/legacy-overlays/PRD-Guild-Manager/README.md`](migration/legacy-overlays/PRD-Guild-Manager/README.md)
- Legacy PRD：[`migration/legacy-prd/README.md`](migration/legacy-prd/README.md)
- Legacy Workflows：[`migration/legacy-workflows/README.md`](migration/legacy-workflows/README.md)
