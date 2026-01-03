---
PRD-ID: PRD-rouge-manager
Title: PRD-rouge-manager 功能纵切实现验收清单（Godot + C#）
Status: Template
Arch-Refs:
  - CH01
  - CH03
ADR-Refs:
  - ADR-0018  # Godot 4.5 + C# 技术栈
  - ADR-0019  # Godot 安全基线
  - ADR-0004  # 事件总线与契约
  - ADR-0020  # 契约文件位置标准
  - ADR-0021  # C# 领域层架构
  - ADR-0024  # Godot 测试策略
  - ADR-0006  # 数据存储
  - ADR-0005  # 质量门禁
  - ADR-0003  # 可观测性与发布健康
  - ADR-0015  # 性能预算
  - ADR-0011  # Windows-only 平台与 CI
Test-Refs:
  # 具体项目应将占位路径替换为真实测试文件（或在实现落地前保持最小集）
  - Game.Core.Tests/Services/EventBusTests.cs
  - Game.Core.Tests/State/GameStateMachineTests.cs
  - Tests.Godot/tests/Scenes/Smoke/test_main_scene_smoke.gd
  - Tests.Godot/tests/Scenes/Smoke/test_glue_connections.gd
  - Tests.Godot/tests/Adapters/test_event_bus_adapter.gd
  - Tests.Godot/tests/Integration/test_screen_navigation_flow.gd
  - Tests.Godot/tests/Integration/Security/test_security_http_audit.gd
  - logs/ci/<date>/ci-pipeline-summary.json
  - logs/e2e/<date>/smoke/selfcheck-summary.json
---

> 说明：本清单用于 rouge（Godot 4.5 + C#）下的 “PRD-rouge-manager / T2 最小可玩闭环（MVP Run）” 功能纵切验收骨架。

本清单只做 **结构与对齐检查**，所有阈值/策略/门禁的具体口径一律引用：

- Base 文档：docs/architecture/base/01-03、07、09 章
- ADR：ADR-0018、ADR-0019、ADR-0004、ADR-0020、ADR-0005、ADR-0003、ADR-0015、ADR-0011

不在本清单中重复具体数值或策略，避免与 Base/ADR 口径漂移。

---

## 一、文档完整性验收

- [ ] 功能纵切文档存在且 Front-Matter 完整：
  - `docs/architecture/overlays/PRD-rouge-manager/08/08-功能纵切-最小可玩闭环.md`
  - `_index.md` 中已收录 PRD-rouge-manager 相关条目
- [ ] 08 章仅作“引用”，不复制 01/02/03 章中的阈值/策略/门禁具体数值：
  - 安全：引用 CH02 + ADR-0019
  - 可观测性与发布健康：引用 CH03 + ADR-0003/0005/0015
  - 性能预算：引用 CH09 + ADR-0015
- [ ] PRD 与 Overlay 对齐：
  - `.taskmaster/docs/prd.txt`（与 `prd.txt`）中的 T2 闭环模块在 08 章有对应小节或引用
  - Overlay 中引用的 Contracts/Tests 均指向当前 Godot+C# 代码与测试路径

---

## 二、架构设计验收（Arc42/三层结构对齐）

- [ ] 三层结构落地：
  - Game.Core：纯 C# 域模型与服务（无 Godot 依赖）
  - Game.Godot：Godot 适配层与场景/脚本，仅通过接口依赖 Core
  - Tests.Godot：GdUnit4 场景与集成测试工程
- [ ] 事件与契约（ADR-0004/0020/0022）：
  - 事件命名遵循 `<boundedContext>.<entity>.<action>`，并使用前缀分层：`core.*` / `screen.*` / `ui.menu.*`
  - Contracts SSoT 存在于 `Game.Core/Contracts/**`，且不依赖 Godot
  - 事件封装示例：`Game.Core/Contracts/DomainEvent.cs`
- [ ] 事件命名规范验证（示例脚本）
  - 所有事件常量必须匹配正则：`^[a-z]+(\\.[a-z0-9_]+){2,}$`
  - 禁止前缀：`demo.*`（仅模板示例保留）
  - 验证命令（扫描所有 EventType 常量定义）：
    ```powershell
    # Windows PowerShell
    Get-ChildItem -Recurse -Include *.cs Game.Core/Contracts |
    Select-String 'EventType\\s*=\\s*\"([^\"]+)\"' |
    ForEach-Object {
      $evt = $_.Matches.Groups[1].Value
      if ($evt -notmatch '^[a-z]+(\\.[a-z0-9_]+){2,}$') {
        Write-Host \"FAIL: Invalid event name: $evt in $($_.Path)\"
        exit 1
      }
      if ($evt -like 'demo.*') {
        Write-Host \"FAIL: demo.* events are not allowed in product code: $evt in $($_.Path)\"
        exit 1
      }
    }
    Write-Host \"PASS: Event naming OK\"
    ```

---

## 三、代码实现验收（Godot + C#）

- [ ] 单机单人约束明确且可执行：
  - 不依赖多人/联机/远程存档
  - 出网能力（如存在）必须走白名单与审计（见 ADR-0019 与 `08-Contracts-Allowed-External-Hosts.md`）
- [ ] T2 可玩闭环（来自 prd.txt 6.1）能跑通：
  - [ ] 主菜单可开始新局
  - [ ] 地图生成并可选择节点（至少包含战斗/事件/休息/商店/Boss）
  - [ ] 节点完成后回到地图并可继续推进
  - [ ] Boss 胜利进入通关结算；全灭进入失败结算；均可快速重开下一局
- [ ] 统一效果系统作为唯一结算入口（prd.txt 5.5）：
  - 事件/卡牌/敌人意图/奖励复用同一指令集与解析器
  - 结算点固定（OnTurnStart/OnTurnEnd/OnHit）并可通过单元测试回归

---

## 四、测试框架验收（xUnit + GdUnit4）

- [ ] Core 层（xUnit）：
  - 有覆盖战斗状态机/效果解析/牌堆操作的单测
  - 覆盖率阈值不在此复制，引用 ADR-0005 与 Base CH07
- [ ] 场景与冒烟（GdUnit4 headless）：
  - 至少包含一条“启动 -> 主菜单 -> 进入主场景 -> 返回/退出”的冒烟用例（见 Test-Refs）
  - 安全相关用例存在（外链审计/DB 路径拒绝），并产出审计文件到 `logs/`

---

## 五、性能与监控验收（引用 ADR-0015/0003）

- [ ] 性能采集与归档存在（阈值不在此复制）：
  - CI 工件落盘到 `logs/perf/<YYYY-MM-DD>/summary.json`
- [ ] 结构化日志与审计按 Base/ADR 口径落盘到 `logs/`，便于追溯

---

## 六、CI / 发布与平台约束验收

- [ ] Windows-only CI 与构建（ADR-0011）：
  - CI 工作流在 Windows Runner 上可通过
  - 质量门禁脚本可本地运行（示例）：
    ```powershell
    py -3 scripts/python/quality_gates.py --typecheck --lint --unit --scene --security
    ```
- [ ] 质量门禁：
  - 具体阈值由 ADR-0005/0015/CH07/CH09 负责，本清单只检查“门禁存在且已集成到 CI”

---

## 七、最终验收状态（模板级）

- [ ] 架构对齐：三层结构、本地/CI 流程、安全/性能/可观测性均与 ADR/CH 口径一致
- [ ] 文档对齐：PRD、Base、ADR、Overlay/08 之间有清晰回链
- [ ] 测试与门禁：最小 xUnit/GdUnit/Smoke 流程跑通
