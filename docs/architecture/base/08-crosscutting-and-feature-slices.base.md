---
title: 08 crosscutting and feature slices.base
status: base-SSoT
adr_refs: [ADR-0003, ADR-0004, ADR-0005, ADR-0019, ADR-0020, ADR-0022]
placeholders: unknown-app, Unknown Product, unknown-product, gamedev, production, dev, dev-team, dev-project
derived_from: arc42 ch8 (crosscutting concepts), C4 (Context/Container) minimal
last_generated: 2026-01-08
---

> 本页是 Base 的第 08 章模板：定义“功能纵切（Vertical Slice）”在本仓库如何写、写到哪里、如何回链。
>
> 具体功能模块文档必须写在 `docs/architecture/overlays/<PRD_ID>/08/`，Base 只能提供约束与模板。

## 08.1 范围与 SSoT

- Base（01/02/03/07/09/10 等）定义跨切面规则、阈值口径、事件命名与安全基线。
- Overlay 08 只描述一个功能纵切：实体/事件/接口/验收/测试占位与回链，不复制阈值/策略文本。
- 契约（Events/DTO/Ports）只有一个 SSoT：`Game.Core/Contracts/**`（ADR-0020）。

## 08.2 契约（Contracts）口径

### 08.2.1 契约落盘位置（ADR-0020）

- 事件/DTO/Ports 必须落盘到 `Game.Core/Contracts/**`。
- Contracts 不依赖 Godot API（禁止 `using Godot;`），只使用 BCL 类型（string, DateTimeOffset 等）。
- 这样 Core 层可以在纯 .NET xUnit 环境快速验证。

### 08.2.2 事件命名与 EventType（ADR-0004）

- `EventType` 对齐 CloudEvents 1.0 的 `type` 字段：必须常量化，文档/代码/任务引用一致。
- 分域约定（示例）：
  - `core.*.*`：领域/系统级事件
  - `ui.menu.*`：菜单/UI 交互事件
  - `screen.*.*`：屏幕/场景事件
- 注意：C# 的 PascalCase 类名不是 EventType；EventType 必须是小写点分字符串常量。

### 08.2.3 模板（C#）

#### Domain Event

路径：`Game.Core/Contracts/<Module>/<EventName>.cs`

```csharp
using System;

namespace Game.Core.Contracts.<Module>;

/// <summary>
/// Domain event: ${DOMAIN_PREFIX}.<entity>.<action>
/// 说明：当 <action> 发生时发布，用于跨模块/跨层通信。
/// </summary>
/// <remarks>
/// References: ADR-0004-event-bus-and-contracts, ADR-0020-contract-location-standardization.
/// </remarks>
public sealed record <EventName>(
    string <EntityId>,
    DateTimeOffset OccurredAt
)
{
    public const string EventType = "core.<entity>.<action>";
}
```

#### DTO（请求/响应/跨层传输结构）

路径：`Game.Core/Contracts/<Module>/<DtoName>.cs`

```csharp
namespace Game.Core.Contracts.<Module>;

/// <summary>
/// DTO: <DtoName>
/// Purpose: request/response or adapter-core payload.
/// </summary>
public sealed record <DtoName>(
    string <Field1>,
    int <Field2>
);
```

#### Ports（接口契约）

路径：`Game.Core/Contracts/<Module>/I<Something>Port.cs`

```csharp
using System.Threading;
using System.Threading.Tasks;

namespace Game.Core.Contracts.<Module>;

/// <summary>
/// Port contract: <what this port does>
/// </summary>
public interface I<Something>Port
{
    Task<<DtoName>> ExecuteAsync(<DtoName> request, CancellationToken ct);
}
```

## 08.3 测试与验收（与 CH07 对齐）

- xUnit：覆盖 Core 的算法/状态机/DTO 映射与契约默认值（不依赖引擎）。
- GdUnit4：覆盖 Scenes/Signals 连通性、关键节点可见性与资源路径（headless 产出到 `logs/e2e/**`）。
- 安全烟测：如涉及外链/网络/文件/权限，必须包含 allow/deny/invalid + 审计校验（引用 ADR-0019）。

## 08.4 Overlay 08 目录结构（仅示例）

路径：`docs/architecture/overlays/<PRD_ID>/08/`

- `_index.md`：本 PRD 的 08 章目录与总览
- `ACCEPTANCE_CHECKLIST.md`：最小可玩闭环/验收清单与 Test-Refs
- `08-Feature-Slice-<Feature>.md`：某个纵切模块（一个文件一条纵切）

> 注意：08 章只引用 CH01/CH02/CH03 的口径，不复制阈值/策略文本。

## 08.5 任务回链（ADR/CH/Overlay）

- `tasks.json`（Task Master 主任务集）与视图任务（如 NG/GM）使用 `adr_refs`/`chapter_refs`/`overlay_refs` 作为回链 SSoT。
- 校验工具：
  - `py -3 scripts/python/task_links_validate.py`
  - `py -3 scripts/python/validate_task_master_triplet.py`
