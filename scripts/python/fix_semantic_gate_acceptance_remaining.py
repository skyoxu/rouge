#!/usr/bin/env python3
"""
Fix remaining semantic-gate mismatches by tightening acceptance to match master details,
without introducing new scope.

Targets:
  Updates acceptance lines for specific taskmaster_id entries in:
    .taskmaster/tasks/tasks_gameplay.json

Audit:
  logs/ci/<YYYY-MM-DD>/sc-semantic-gate-all/fix-remaining-acceptance.json
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def today_str() -> str:
    return dt.date.today().strftime("%Y-%m-%d")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    root = repo_root()
    gameplay_path = root / ".taskmaster" / "tasks" / "tasks_gameplay.json"
    back_path = root / ".taskmaster" / "tasks" / "tasks_back.json"
    gameplay = read_json(gameplay_path)
    back = read_json(back_path)
    if not isinstance(gameplay, list):
        print("FIX_SEMANTIC_GATE status=fail reason=tasks_gameplay_not_array")
        return 2
    if not isinstance(back, list):
        print("FIX_SEMANTIC_GATE status=fail reason=tasks_back_not_array")
        return 2

    fixes: dict[int, list[str]] = {
        1: [
            "在 `Game.Core/Domain/Card.cs` 中实现纯 C#（不依赖 Godot）的领域模型：包含 `CardDefinition`（卡牌静态配置：ID、名称、消耗、目标规则、效果指令列表、textKey、稀有度、职业标签、upgradedId）与 `CardInstance`（运行时实例：引用 `CardDefinition`、临时费用变化、回合内标记、升级状态）；并定义 `TargetRule` 枚举（`SingleEnemy/AllEnemies/SingleAlly/AllAllies/Random`）与 `CardType` 枚举（`Attack/Defense/Skill`）。",
            "补齐并通过 xUnit 单元测试验证 `CardDefinition/CardInstance` 的字段映射与 record 不可变性（修改需通过创建新实例而非就地变更）；在 Windows 上 `dotnet test` 通过。",
            "若引入或变更契约/事件/DTO：必须落盘到 `Game.Core/Contracts/Rouge/**`，并保持相关 Overlay 文档的 Test-Refs 与实现/测试一致（可通过文本检索与路径核对验证）。",
        ],
        4: [
            "在 `Game.Core/Domain/Status.cs` 与 `Game.Core/Services/StatusManager.cs` 中实现纯 C#（不依赖 Godot）的状态模型与管理：定义 `StatusDefinition`（包含 ID/名称/结算时机 `TurnStart/TurnEnd/OnDealDamage/OnTakeDamage`/叠加规则/UI 图标 key）与 `StatusInstance`（statusId/stacks/duration/ownerUnitId）；内置最小状态集合 Strength/Weak/Vulnerable/Poison/Block，并可按状态 ID 验证存在。",
            "实现并可验证叠加/衰减语义：相同状态 stacks 累加且 duration 取最大值，不同状态可共存；duration 衰减并在到期时移除；对无效 statusId、负 duration、非法 stacks 等输入明确拒绝且目标状态集合保持不变（可通过公开查询/返回值/可观察结果验证）。",
            "实现并用 xUnit 在 Windows 上可复现验证结算与数值计算：TurnStart 结算 Poison（伤害与衰减）、TurnEnd 清零 Block 并衰减持续状态；伤害修正包含 Strength/Weak（source）与 Vulnerable（target）且修正顺序为先 source 后 target；`dotnet test` 通过。若引入/变更契约或事件，则落盘到 `Game.Core/Contracts/Rouge/**` 并保持 Overlay 的 Test-Refs 对齐。",
        ],
        5: [
            "在 `Game.Core/Domain/Hero.cs` 中实现纯 C#（不依赖 Godot）的英雄领域模型，并按任务要求“继承或使用现有 `Player` 类”进行扩展（不得复制一份功能重复的 Player）：包含 `HeroId`、`Name`、`ClassId`、`MaxHealth`、`CurrentHealth`、`BaseEnergyMax` 与 `CurrentEnergy`；对无效值（如 `MaxHealth<=0`、`BaseEnergyMax<0`）必须拒绝并提供 xUnit 用例覆盖。",
            "在 `Hero` 中加入牌堆与战斗临时状态：`Deck/Hand/Discard/Exhaust` 四个字段均为 `CardPile` 且初始化后不为 null；包含 `Shield` 与 `Statuses: List<StatusInstance>`；实现 `ClearCombatState()` 使战斗结束后 `Shield` 归零且 `Statuses` 清空，同时 `CurrentHealth` 保持不变；提供 xUnit 用例覆盖上述行为。",
            "实现并用 xUnit 验证核心战斗行为：`TakeDamage(amount)`（amount<0 拒绝；amount>=0 先扣 Shield、剩余再扣 CurrentHealth 且生命不低于 0）、`Heal(amount)`（amount<0 拒绝；amount>=0 不超过 MaxHealth）、`GainShield(amount)`（amount<0 拒绝；amount>=0 累加）、`RefreshEnergy()`（回合开始将 `CurrentEnergy` 重置为 `BaseEnergyMax`）；在 Windows 上 `dotnet test` 通过。",
        ],
        3: [
            "在 `Game.Core/Services/EffectResolver.cs` 中实现纯 C#（不依赖 Godot）的效果系统：定义 `EffectCommand` 抽象类或接口，并提供任务清单中的命令类型（如 `DamageCommand/GainBlockCommand/HealCommand/ApplyStatusCommand/DrawCommand/ChangeEnergyCommand/GainGoldCommand/AddCardToDeckCommand/RemoveCardFromDeckCommand/UpgradeCardCommand/TriggerBattleCommand/SetFlagCommand`）。使用 `BattleContext` 传递所需的战斗/队伍状态引用。",
            "实现 `ExecuteEffect(cmd, context)` 与 `ExecuteEffects(list, context)`：单条与批量执行入口可被单元测试验证；`ExecuteEffects` 完成后必须“触发事件”（可通过 IEventBus/事件总线接口或等价机制实现，但不在本任务强制具体事件名），并且该事件触发可被 xUnit 观测（例如通过替身总线捕获调用）。",
            "补齐并通过 xUnit 单元测试覆盖：至少 3 类命令的执行效果与参数校验，以及批量执行（全成功/部分失败/空列表）的可观察结果；在 Windows 上 `dotnet test` 通过。若引入或变更契约/事件，则必须落盘到 `Game.Core/Contracts/Rouge/**` 并同步更新相关 Overlay 文档的 Test-Refs。",
        ],
        6: [
            "在 `Game.Core/Domain/Enemy.cs` 落地 `Enemy` 领域模型：包含 `EnemyId/Name/EncounterId/MaxHealth/CurrentHealth/Shield/Statuses(List<StatusInstance>)`，并实现 `TakeDamage/Heal/GainShield`（护盾优先，溢出伤害进入血量）。`Game.Core` 不得引用任何 Godot API/类型。",
            "按任务口径实现意图系统：定义 `Intent`（至少包含 `IntentType/TargetId/EffectCommands`）与 `IntentType` 枚举，且必须包含 `Attack/Defend/Buff/Debuff/Special`；在 `Game.Core/Services/EnemyAI.cs` 提供 `IntentTable` 与 `GenerateIntent(enemy, battleContext)` 的最小实现为“顺序循环技能表”。",
            "补齐并通过 xUnit 单元测试验证：`Enemy` 的伤害/治疗/护盾语义，以及 `EnemyAI.GenerateIntent` 在固定技能表下生成确定的意图序列；在 Windows 上 `dotnet test` 通过。若本任务引入或变更契约/事件，则必须落盘到 `Game.Core/Contracts/Rouge/**` 并同步更新相关 Overlay 文档的 Test-Refs。",
        ],
        7: [
            "在 `Game.Core/Services/BattleManager.cs` 实现纯 C#（不得依赖 Godot 程序集/命名空间）的 `BattleManager` 与战斗阶段枚举（至少包含：`core.rouge.battle.started`、`core.rouge.turn.player.started`、`PlayerMain`、`core.rouge.turn.player.ended`、`EnemyTurn`、`core.rouge.battle.won`、`core.rouge.battle.lost`），并且战斗阶段推进语义可验证：`StartBattle(heroes,enemies)` 进入/发布 `core.rouge.battle.started`；`StartPlayerTurn()` 进入/发布 `core.rouge.turn.player.started`；玩家主操作阶段为 `PlayerMain`；`EndPlayerTurn()` 进入/发布 `core.rouge.turn.player.ended` 并转入 `EnemyTurn`；`ExecuteEnemyTurn()` 完成后回到玩家回合或进入胜负阶段（胜负阶段后不再推进到其他阶段）。",
            "提供并通过 xUnit 单元测试（Windows 上 `dotnet test` 通过），用 Mock 的 `StatusManager` 与 `EffectResolver` 隔离依赖，覆盖以下可证伪行为：1) 状态机推进顺序（Started → PlayerStarted → PlayerMain → PlayerEnded → EnemyTurn → 循环/胜负）；2) `StartBattle`/`StartPlayerTurn` 的能量刷新与“抽牌行为”（不要求固定数量，但需可观察到手牌区变化）；3) `PlayCard(heroId,cardId,targetId)` 在非 `PlayerMain`、能量不足、目标非法、或英雄不持有卡牌时必须拒绝且不改变能量/牌区/阶段；成功出牌时必须执行卡牌 EffectCommands（通过 `EffectResolver` 调用可验证）、扣除能量并将卡牌移出手牌（进入弃牌堆或等价区域）。",
            "提供并通过 xUnit 单元测试验证结算/死亡/胜负与事件集合：`StartPlayerTurn()` 结算 `turn_start_settlement`；`EndPlayerTurn()` 弃掉剩余手牌并结算 `turn_end_settlement`（至少护盾清零可验证）且刷新敌人意图；`ExecuteEnemyTurn()` 遍历存活敌人并复用 `EffectResolver` 执行意图；当任意单位 HP ≤ 0 时立即触发死亡处理并发布 `UnitDied` 与胜负检查（敌方全灭发布 `core.rouge.battle.won`、我方全灭发布 `core.rouge.battle.lost`）；伤害结算发布 `core.rouge.combat.damage.applied`；并且成功出牌必须发布 `CardPlayed`（或命名等价的既有事件/契约）。若引入/变更契约或事件，必须落盘到 `Game.Core/Contracts/Rouge/**` 并同步更新相关 Overlay 文档的 Test-Refs。",
        ],
        26: [
            "实现本任务所需的 Godot UI/场景/脚本：创建 `Game.Godot/Scenes/MainMenu.tscn` 并挂载 `Game.Godot/Scripts/MainMenuController.cs`；主菜单在屏幕中央显示游戏标题与按钮（\"开始新局\"/\"继续\"/\"设置\"/\"退出\"），按钮样式与现有主题一致。",
            "点击\"开始新局\"会以随机 Seed 调用 `RunManager.StartNewRun(...)` 并切换到 MapScreen；点击\"设置\"打开设置面板；点击\"退出\"退出游戏；\"继续\"按钮为可选：T2 允许先占位不实现（禁用/提示），若实现则加载存档并切换到 MapScreen。",
            "新增至少 1 个 headless GdUnit4 或 E2E 冒烟测试（see test_refs），验证 MainMenu 场景可无错误加载且\"开始新局\"触发开局并进入/加载 MapScreen；测试产物输出到 `logs/e2e/**`。",
        ],
        54: [
            "Provide reusable CardView + HandLayout components and keep gameplay rules in Game.Core; CardView renders front-facing card info (at least name, cost, and a visual hint for type/target/rarity) and HandLayout arranges a variable-sized hand with consistent spacing/fan and supports a max-hand constraint.",
            "Hover preview works in both mouse and keyboard focus navigation scenarios (e.g., focus/highlight moves across cards and still shows preview).",
            "Add at least one headless GdUnit4 UI test (see test_refs) and produce artifacts under logs/e2e/**.",
        ],
        8: [
            "在 `Game.Core/Domain/AdventureMap.cs` 实现纯 C#（不依赖 Godot）的领域模型：定义 `NodeType` 枚举（Combat/Event/Rest/Shop/Elite/Boss）与 `MapNode`（包含 `NodeId`、`NodeType`、`Layer`、`Connections`、`Completed`、`Parameters`），以及 `AdventureMap`（包含 `Nodes`、`CurrentNodeId`、`CompletedNodes`、`StartNodeId`、`BossNodeId`）。",
            "在 `AdventureMap` 中实现并可验证以下行为：`GetAvailableNodes()` 返回当前可达节点（下一层连线节点）；`MoveToNode(nodeId)` 仅在 `nodeId` 可达时更新 `CurrentNodeId`，否则拒绝移动且 `CurrentNodeId` 保持不变；`CompleteNode(nodeId)` 标记完成并更新 `CompletedNodes`；`IsPathComplete()` 在 Boss 节点完成前为 false，完成后为 true。",
            "地图生成逻辑采用硬编码模板（8–12 普通节点 + Boss，总 9–13），并满足连线“分层递进（仅从当前层指向下一层）”；同时预留随机生成接口但默认实现必须使用模板。新增/调整 xUnit 测试覆盖：可达节点计算、移动/完成/章节完成判定，以及基本边界用例；在 Windows 上 `dotnet test` 通过。",
        ],
        9: [
            "在 `Game.Core/Domain/Party.cs` 实现纯 C# 的 `Party`：包含 `Heroes: List<Hero>`、`Gold:int`、`Flags: Dictionary<string, object>`，并实现 `AddHero/GetHero/GainGold/SpendGold/SetFlag/GetFlag/IsPartyAlive` 等方法。",
            "`Heroes` 的数量不做强制限制（任务仅为 T2 建议 2 名英雄）；`IsPartyAlive()` 的语义与任务一致：当且仅当所有英雄 `HP <= 0` 时判定为全灭。",
            "预留 `EquipmentSlots`/`TalentTree` 占位字段（T2 不实现但保留结构），并补齐 xUnit 测试覆盖金币操作与 `IsPartyAlive` 判定；在 Windows 上 `dotnet test` 通过。",
        ],
        12: [
            "在 `Game.Core/Services/RewardManager.cs` 实现 `GenerateCardRewards(heroClassId, count=3)` 与 `GenerateGoldReward(nodeType)`；支持按 `heroClassId`/`ClassTags` 过滤卡池，并按稀有度权重随机抽取（Common 70%、Uncommon 25%、Rare 5%）。",
            "随机必须可复现：使用 `RngService.PickRandom`/`Shuffle`（或等价接口）保证同一 Seed 下生成一致结果；奖励配置允许先硬编码，后续再抽取到配置文件（JSON/Resource）。",
            "补齐 xUnit 测试覆盖：职业过滤、权重路径（可用可控 RNG stub 验证分支）、金币奖励按节点类型返回范围/值；在 Windows 上 `dotnet test` 通过。若引入/变更契约/事件/DTO，必须落盘到 `Game.Core/Contracts/Rouge/**` 并同步更新相关 Overlay 文档的 Test-Refs。",
        ],
        13: [
            "在 `Game.Core/Domain/Event.cs` 与 `Game.Core/Services/EventManager.cs` 落地事件系统：实现 `EventDefinition`（含 `EventId/TextKey/Options`）与 `EventOption`（含 `OptionTextKey/Requirements/Effects`，Effects 复用 `EffectCommand`）。",
            "实现 `EventManager.GetEvent/SelectOption/CheckRequirement`：金币不足等条件必须导致选项不可选（置灰语义在 UI 层呈现，但 Core 必须能判定可选性）；选择选项后执行其 `Effects` 并应用到 `Party`（必要时通过适配层触发战斗/跳转等）。",
            "事件抽取逻辑从事件池随机选择（使用 `RngService`），T2 允许先硬编码少量事件。补齐 xUnit 测试覆盖：Requirement 判定、选项执行 Effects 对 Party 的可验证变更；在 Windows 上 `dotnet test` 通过。",
        ],
        15: [
            "在 `Game.Core/Services/ShopService.cs` 实现纯 C# 的 `ShopService`：实现 `GenerateShopInventory(heroClassId, count=5)`（职业过滤 + 稀有度随机）、`PurchaseCard(party, hero, cardId, price)`、`RemoveCard(party, hero, cardId, price)`；金币不足时必须失败且不得改变 `party.Gold` 与牌组状态；成功时扣金币并修改牌组。",
            "价格策略允许先硬编码（例如 Common 50、Uncommon 75、移除 75；可后续配置化），稀有度权重若需要具体数值则与 `RewardManager` 同口径（Common 70%、Uncommon 25%、Rare 5%）。",
            "补齐 xUnit 测试覆盖库存生成可复现（可控 RNG）、职业过滤、购买/移除成功与失败路径（金币不足、卡不存在等）；在 Windows 上 `dotnet test` 通过。若引入/变更契约/事件/DTO，必须落盘到 `Game.Core/Contracts/Rouge/**` 并同步更新相关 Overlay 文档的 Test-Refs。",
        ],
        30: [
            "在 Windows headless 环境下能够运行 `py -3 scripts/python/quality_gates.py`（覆盖率门禁、性能烟测、安全烟测），并产出可核验工件：`logs/unit/coverage.json`、`logs/perf/summary.json`、`logs/ci/security-audit.jsonl`。",
            "门禁判定与退出码可证伪：hard gate 未达标必须返回非 0 退出码；soft gate 未达标必须在 `logs/ci/**` 记录 warning（包含门禁项、阈值、实测值与触发命令/位置）。",
            "门禁内容与 ADR-0005（quality gates）与 ADR-0015（performance budgets）语义对齐且不引入新的工具链依赖；覆盖率/性能/安全的阈值与产物路径以本任务 details 所列为准，并可通过脚本输出与日志文件共同验证。",
        ],
        55: [
            "BattleScreen supports click-to-select and target selection based on TargetRule; cancel path is supported; user actions are wired to BattleManager.PlayCard(heroId, cardId, targetId) with matching parameter semantics.",
            "Invalid plays (no energy / invalid target) do not mutate battle state and show a clear reason; BattleManager.PlayCard must not mutate state on rejected operations.",
            "Add at least one headless GdUnit4 integration test (see test_refs) that covers a full play+cancel+invalid attempt flow.",
        ],
        14: [
            "在 `Game.Core/Services/RestService.cs` 实现纯 C# 的 `RestService`（不得依赖 Godot）：提供且仅提供两个独立用例 `HealParty(party, amount)` 与 `UpgradeCard(hero, cardId)`（二选一逻辑在 UI 层处理，Core 层不得实现选择流程）。",
            "`HealParty` 为所有英雄回血（固定值或百分比均可，允许先硬编码如 30% MaxHP），且不超过 MaxHealth；`UpgradeCard` 通过 `CardDefinition.UpgradedId` 将卡牌 ID 替换为升级版 ID。提供 xUnit 测试覆盖回血上限与升级映射语义；在 Windows 上 `dotnet test` 通过。",
            "若引入或变更契约/事件/DTO：必须落盘到 `Game.Core/Contracts/Rouge/**`，并保持相关 Overlay 文档的 Test-Refs 与实现/测试一致（可通过文本检索与路径核对验证）。",
        ],
        17: [
            "在 `Game.Core/Data` 或 Godot Resources 中创建卡牌静态配置（JSON 数组或 `.tres`）：总数至少 20（战士 5、法师 5、通用 10），并包含任务清单中的最低集合；每张卡包含字段：id、name、cost、cardType、targetRule、effects（EffectCommand 序列化）、textKey、rarity、classTags、upgradedId。",
            "升级版映射满足任务口径：`upgradedId` 指向升级版卡牌，升级版体现“消耗 -1 或伤害 +3 或效果增强”之一（允许先用最小可用实现）。",
            "补齐 xUnit 测试验证静态配置的可读取性（测试可直接读取 JSON/资源文件）、id 唯一性、字段完整性、升级映射存在性；在 Windows 上 `dotnet test` 通过。若引入/变更契约/事件/DTO，必须落盘到 `Game.Core/Contracts/Rouge/**` 并同步更新相关 Overlay 文档的 Test-Refs。",
        ],
        18: [
            "在 `Game.Core/Data` 或 Godot Resources 中创建敌人静态配置：`EnemyDefinition`（包含 id/name/maxHealth/intentTable）至少 10 个敌人定义，并包含任务最低集合（史莱姆/哥布林/强盗/巫师/骑士/精英-狂战士/精英-黑暗法师/Boss-龙王）。",
            "创建遭遇静态配置：`EncounterDefinition`（包含 id/enemyIds/difficulty）至少 5 个遭遇配置；普通遭遇满足 2–3 小怪，精英遭遇为 1 精英 + 1 小怪，Boss 遭遇为 Boss 单体或 Boss+护卫；并确保所有 `enemyIds` 引用的敌人 id 均存在且无悬挂引用。",
            "补齐 xUnit 测试验证静态配置可读取、id 唯一、遭遇引用有效；在 Windows 上 `dotnet test` 通过。若引入/变更契约/事件/DTO，必须落盘到 `Game.Core/Contracts/Rouge/**` 并同步更新相关 Overlay 文档的 Test-Refs。",
        ],
        19: [
            "在 `Game.Core/Data` 或 Godot Resources 中创建事件静态配置（至少包含 EventId/TextKey/Options）：Options 中的 `EventOption` 包含 `OptionTextKey`、`Requirements`（可选，如金币门槛）与 `Effects: List<EffectCommand>`（复用 EffectResolver 命令）。",
            "静态配置至少包含任务最低事件集合（神秘宝箱/流浪商人/强盗伏击/神殿祝福/诅咒祭坛），并满足关键语义：强盗伏击选项 B 为“交 50 金离开”且要求金币 ≥ 50；T2 允许先硬编码这些最小事件集合。",
            "补齐 xUnit 测试验证静态配置可读取、字段结构与金币门槛可被判定（例如 Requirements 包含 GoldRequired）；在 Windows 上 `dotnet test` 通过。若引入/变更契约/事件/DTO，必须落盘到 `Game.Core/Contracts/Rouge/**` 并同步更新相关 Overlay 文档的 Test-Refs。",
        ],
    }

    updated: list[dict[str, Any]] = []
    missing: list[int] = []
    for task_id, new_acc in fixes.items():
        entry = next((t for t in gameplay if isinstance(t, dict) and t.get("taskmaster_id") == task_id), None)
        if entry is None:
            missing.append(task_id)
            continue
        before = entry.get("acceptance") or []
        entry["acceptance"] = new_acc
        updated.append({"taskmaster_id": task_id, "id": entry.get("id"), "before_len": len(before), "after_len": len(new_acc)})

    write_json(gameplay_path, gameplay)
    # Update specific back task (taskmaster_id=45) to make the layer boundary explicit and machine-auditable.
    back_updated = False
    back_entry = next((t for t in back if isinstance(t, dict) and t.get("taskmaster_id") == 45), None)
    if isinstance(back_entry, dict):
        acc = list(back_entry.get("acceptance") or [])
        if acc:
            # Make the "only Adapters may touch Godot" rule explicit in a single, searchable sentence.
            acc[0] = (
                "运行 `dotnet test` 时：`Game.Core.Tests/Architecture/LayerDependencyTests.cs` 必须以可执行、可复现的方式判定："
                "`Game.Core` 不得引用/依赖任何 `Godot` 命名空间或类型（命中即测试失败）；并且以文字明确声明“与 Godot 交互仅允许发生在 Adapters 层/运行时层（例如 `Scripts/Adapters/**`、`Game.Godot/**`），Core 领域层不得触达 Godot”。"
            )
            back_entry["acceptance"] = acc
            back_updated = True
            write_json(back_path, back)

    # Fix wording conflict for release workflow acceptance (taskmaster_id=51): success should be conditional on smoke pass.
    release_entry = next((t for t in back if isinstance(t, dict) and t.get("taskmaster_id") == 51), None)
    if isinstance(release_entry, dict):
        acc = list(release_entry.get("acceptance") or [])
        if acc:
            acc[0] = (
                "仓库中必须存在一个专用的 Windows Release GitHub Actions workflow；当由 tag push 或通过 workflow_dispatch 触发时，该 workflow 必须执行导出与 smoke 验证："
                "smoke 通过则 run 成功退出并发布 Windows 构建 artifacts；smoke 失败则该次 run 必须失败（不得吞掉失败）。"
                "对同一 tag/同一 workflow_dispatch 输入参数，artifact 命名必须保持一致且可预测（可通过对比两次运行的 artifact 列表验证）。"
            )
            release_entry["acceptance"] = acc
            back_updated = True
            write_json(back_path, back)

    # Strengthen offline-mode semantics for external URL policy (taskmaster_id=35) to match view description.
    offline_entry = next((t for t in back if isinstance(t, dict) and t.get("taskmaster_id") == 35), None)
    if isinstance(offline_entry, dict):
        acc = list(offline_entry.get("acceptance") or [])
        if len(acc) >= 3:
            acc[2] = (
                "GD_OFFLINE_MODE=1 时必须拒绝所有“出网/网络样行为”，至少包含：外部 URL 打开（OS.ShellOpen 适配器）与安全 HTTP 客户端/网络请求入口；"
                "拒绝必须留下审计记录（logs/ci/<date>/security-audit.jsonl 或等价路径），并可由 xUnit 测试覆盖 offline 行为。"
            )
            offline_entry["acceptance"] = acc
            back_updated = True
            write_json(back_path, back)

    audit_dir = root / "logs" / "ci" / today_str() / "sc-semantic-gate-all"
    audit_path = audit_dir / "fix-remaining-acceptance.json"
    write_json(audit_path, {"updated": updated, "missing": missing, "back_updated": back_updated})

    print(f"FIX_SEMANTIC_GATE status=ok updated={len(updated)} missing={len(missing)} audit={audit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
