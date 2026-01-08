---
title: 10 i18n ops release v2
status: base-SSoT
adr_refs: [ADR-0028, ADR-0011, ADR-0018, ADR-0008, ADR-0003, ADR-0005]
placeholders: Unknown Product, unknown-product, gamedev, dev-team, dev, 0.0.0, production
derived_from: 10-i18n-ops-release-v2.md
last_generated: 2026-01-08
---

> 目标：给出 Godot+C#（Windows-only）的 i18n、运维与发布口径（SSoT），并说明与 CI/Release Health 的对齐方式。

## 1. i18n（SSoT：ADR-0028）

- 文本资源：以 Godot 的翻译资源（`.translation`/`.po` 等）与 `TranslationServer` 为主。
- 约束：UI 文本必须使用 key 绑定，不允许把中文/英文硬编码散落在场景脚本里。
- Overlay 08：只描述“某功能纵切需要哪些 key/资源”，不复制 i18n 流程细节。

## 2. Ops（Windows-only + 可观测性）

- 平台：Windows-only（ADR-0011）。
- 日志与取证：遵循 CH03（`logs/**`），CI 产物可回溯。
- 安全基线：遵循 CH02/ADR-0019（外链/网络/文件/权限均需审计）。

## 3. Release（发布与回滚）

### 3.1 版本与标识

- 版本号与产品名建议在 `project.godot`/`export_presets.cfg` 与 CI Tag 规则中统一维护。
- GitHub Actions：参考 `.github/workflows/windows-release*.yml`（按仓库实际工作流为准）。

### 3.2 导出与 EXE 冒烟

- 导出脚本：`scripts/ci/export_windows.ps1`
- EXE 冒烟：`scripts/ci/smoke_exe.ps1`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ci/export_windows.ps1 -GodotBin $env:GODOT_BIN -Output build/Rouge.exe
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ci/smoke_exe.ps1 -ExePath build/Rouge.exe
```

### 3.3 分阶段发布（可选）

- 分阶段/灰度策略属于部署发布口径（ADR-0008）；如果需要历史对照材料，放在 `docs/migration/**`。

### 3.4 Release Health（引用 CH01/CH03）

- Crash-Free Sessions/Users 的口径与门禁阈值只在 ADR/Base 维护；Overlay 08 不复制阈值。
- Secrets 预检：`py -3 scripts/python/check_sentry_secrets.py`。

## 4. 工件与留痕

- 发布产物：`build/*.exe` 与 `.pck`（如使用）。
- 取证工件：`logs/**`（CI/unit/e2e/perf/security/release-health 等）。
