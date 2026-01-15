---
PRD-ID: PRD-rouge-manager
Title: Rouge DTO：Shop Inventory & Pricing（商店库存与定价）
Status: Proposed
ADR-Refs:
  - ADR-0020
  - ADR-0021
Arch-Refs:
  - CH01
  - CH05
  - CH06
Test-Refs:
  - Game.Core.Tests/Contracts/RougeShopDtoContractsTests.cs
---

## Scope
- 本页定义商店相关的 DTO 概念与详细字段说明，便于检索与演进。

## Non-goals
- 不写定价策略或平衡参数；详细规则以其他参考文档为准。

## References
- ADR-Refs: ADR-0020, ADR-0021
- Arch-Refs: CH01, CH05, CH06
- Related: `_index.md`

本页记录 PRD-rouge-manager 的 Shop（商店节点）相关 DTO 契约，用于 Core 与适配层/UI 之间的数据交换（不依赖 Godot API，可 xUnit 单测）。

## 契约定义

### DTO
- **ShopInventory**
  - 用途：当玩家进入/刷新商店节点时，Core 输出“商店可购买卡牌列表 + 价格 + 移除卡牌价格”等信息给 UI 展示
  - 字段：
    - `RunId`：当前 Run 的唯一标识
    - `NodeId`：地图节点标识（用于定位当前商店节点）
    - `Cards`：可购买卡牌列表（`ShopCardOffer[]`）
    - `RemoveCardPrice`：移除卡牌的价格（gold）
  - 契约位置：`Game.Core/Contracts/Rouge/Shop/ShopInventory.cs`
- **ShopCardOffer**
  - 用途：单个可购买卡牌的报价条目
  - 字段：`CardId`, `Price`
  - 契约位置：`Game.Core/Contracts/Rouge/Shop/ShopInventory.cs`

## 触发/使用约定
- ShopInventory 作为 **DTO**：由 Core 服务（例如 `IShopService`）输出给 UI；UI 不应直接在 DTO 上承载业务逻辑。
- 当玩家执行“购买/移除/其他会改变状态的选择”时，状态变化以 **领域事件** `EffectsResolved`（`core.effect.resolved`）为主进行回传与刷新（参见 `08-Contracts-Rouge-Run-Events.md` 与 `08-Feature-Slice-Minimum-Playable-Loop.md`）。

## 测试与回链
- `Test-Refs`：`Game.Core.Tests/Contracts/RougeShopDtoContractsTests.cs` 负责验证 DTO 可序列化（避免引入不稳定类型）。
