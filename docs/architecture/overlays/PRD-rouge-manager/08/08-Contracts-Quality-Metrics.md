---
PRD-ID: PRD-rouge-manager
Title: 质量指标（Quality Metrics）契约更新
Arch-Refs:
  - CH01
  - CH03
ADR-Refs:
  - ADR-0004
  - ADR-0005
Test-Refs:
  - scripts/python/quality_gates.py
  - scripts/ci/quality_gate.ps1
Contracts-Refs:
  - scripts/python/quality_gates.py
  - scripts/python/task_links_validate.py
  - scripts/ci/quality_gate.ps1
Status: Proposed
---

本页为功能纵切（08 章）对应“质量指标”契约更新的记录与验收口径。

变更意图（引用，不复制口径）

- 指标事件与工件归档的统一口径：事件/契约治理见 ADR-0004；阈值与门禁由基线章节维护（ADR-0005），此处仅登记功能影响与测试。

影响范围

- 产出契约（脚本与工件）：
  - 质量门禁入口：`scripts/ci/quality_gate.ps1`、`scripts/python/quality_gates.py`
  - 回链校验：`scripts/python/task_links_validate.py`
- 受影响模块：质量门禁、审计日志与归档工件

验收要点（就地）

- 质量门禁脚本可在 Windows 环境执行，并将结果归档到 `logs/ci/`（口径见 Base CH07/CH03/CH02）

