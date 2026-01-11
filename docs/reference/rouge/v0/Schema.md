# Rouge v0 参考：数据字典与 Schema（非 SSoT，不进门禁）

- 本目录仅用于对齐术语与字段形状，不进入任何门禁与验收判定。
- 真正的 SSoT：`docs/adr/**`、`docs/architecture/base/**`、`docs/architecture/overlays/PRD-rouge-manager/**`、`Game.Core/Contracts/**`、以及任务视图文件（`.taskmaster/tasks/tasks_back.json`、`.taskmaster/tasks/tasks_gameplay.json`）。
- 若本页与 SSoT 不一致：以 SSoT 为准，本页允许滞后。

## 1. 通用约定（必须统一）

### 1.1 ID 命名空间
- 所有引用一律用 `id` 字符串，不用数组下标。
- 建议内容 ID 前缀：`Rouge_`（示例：`Rouge_Card_Strike`、`Rouge_Enemy_Slime`）。

### 1.2 时间单位
- 所有周期/间隔字段默认单位：`seconds`（整数或浮点均可）。

### 1.3 百分比表示
- 概率/百分比统一用小数：`0.1 = 10%`。

### 1.4 本地化（可选但建议）
- 建议保留 `nameKey` / `descKey` 字段；v0 可先直接用中文字符串，但字段保留。

### 1.5 权重表（掉落/候选）
- 权重字段名统一：`weight`（整数，>=0）。
- 可选 `min`/`max` 控制数量范围。

### 1.6 版本字段
- 内容配置建议在文件级包含：`contentVersion`（字符串，如 `0.1.0`）。
- 存档/跑局快照必须包含版本字段；本仓库 Contracts 当前采用 `Version:int`（例如 `RunGameStateSnapshot.Version`）。

### 1.7 安全边界（单机离线）
- 配置读取：`res://`（只读）。
- 存档读写：仅 `user://`；禁止绝对路径与路径穿越输入。

## 2. 任务语义覆盖范围（当前三个任务文件会触及的场景）

- 卡牌与效果：CardDefinition / EffectCommand / TargetRule
- 战斗循环：BattleRules / Status / EnemyIntent
- 敌人 AI：意图表（IntentTable）与可预测输出
- 地图与节点：AdventureMap / MapNode / Encounter
- 奖励与商店：RewardPool / ShopCatalog
- 事件抉择：EventDefinition / Choices
- 跑局状态与存档：RunGameStateSnapshot（Contracts 已落盘）

## 3. 数据字典（v0 形状，JSON 视角）

> 说明：这里是“配置/存档的数据形状参考”。实现侧的 Domain/Services 可以拆分或重命名，但需要保持可测试、可迁移。

### 3.1 CardDefinition
- `id: string`
- `nameKey: string`
- `rarity: string`（Common/Rare/...）
- `cost: int`
- `targetRule: string`（SingleEnemy/AllEnemies/SingleAlly/AllAllies/Self/None）
- `tags: string[]`
- `effectCommands: EffectCommand[]`

### 3.2 EffectCommand（枚举式）
- `type: string`（Damage/Heal/GainShield/ApplyStatus/DrawCards/...）
- `amount?: int`
- `statusId?: string`
- `stacks?: int`

### 3.3 EnemyDefinition
- `id: string`
- `nameKey: string`
- `maxHp: int`
- `intentTable: EnemyIntent[]`

### 3.4 EnemyIntent
- `intentType: string`（Attack/Defend/Buff/Debuff/Special）
- `telegraphKey?: string`（UI 文本/图标 key）
- `effectCommands: EffectCommand[]`
- `weight?: int`（若采用权重抽取）

### 3.5 EncounterDefinition
- `id: string`
- `enemyIds: string[]`
- `isElite: bool`
- `rewardPoolId?: string`

### 3.6 AdventureMapDefinition
- `id: string`
- `act: int`
- `nodes: MapNodeDefinition[]`

### 3.7 MapNodeDefinition
- `nodeId: string`
- `nodeType: string`（Battle/Event/Shop/Rest/Elite/Boss）
- `encounterId?: string`
- `eventId?: string`
- `shopId?: string`
- `nextNodeIds: string[]`

### 3.8 RewardPoolDefinition
- `id: string`
- `gold?: { min: int, max: int }`
- `cardRewards?: { cardId: string, weight: int }[]`

### 3.9 ShopCatalog
- `id: string`
- `items: { type: string, refId: string, price: int, weight?: int }[]`

### 3.10 EventDefinition
- `id: string`
- `titleKey: string`
- `descriptionKey: string`
- `choices: { choiceId: string, textKey: string, effects: EffectCommand[] }[]`

## 4. 与本仓库现有 Contracts 的关系（指针）

- 跑局快照 DTO（已落盘）：
  - `Game.Core/Contracts/Rouge/Run/RunGameStateSnapshot.cs`
  - `Game.Core/Contracts/Rouge/Run/AdventureMapSnapshot.cs`
  - `Game.Core/Contracts/Rouge/Run/RunStatisticsSnapshot.cs`
- 对应 xUnit：`Game.Core.Tests/Contracts/RougeRunGameStateSnapshotContractsTests.cs`
- Overlay 记录：`docs/architecture/overlays/PRD-rouge-manager/08/08-Contracts-Rouge-Run-State.md`
