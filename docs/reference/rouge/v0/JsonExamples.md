# Rouge v0 参考：默认内容配置样例包（非 SSoT，不进门禁）

- 本页以“单文件示例片段”的形式给出，方便实现侧快速落地加载链路。
- 当前仓库未必已按此目录落盘；以实现决定为准。

## 1. 建议目录形态（仅参考）
- `res://Assets/Config/Rouge/base/cards.json`
- `res://Assets/Config/Rouge/base/enemies.json`
- `res://Assets/Config/Rouge/base/encounters.json`
- `res://Assets/Config/Rouge/base/map_act1.json`
- `res://Assets/Config/Rouge/base/rewards.json`
- `res://Assets/Config/Rouge/base/shop.json`
- `res://Assets/Config/Rouge/base/events.json`
- `res://Assets/Config/Rouge/base/tuning.json`

## 2. cards.json（片段）
```json
{
  "contentVersion": "0.1.0",
  "cards": [
    {
      "id": "Rouge_Card_Strike",
      "nameKey": "打击",
      "rarity": "Common",
      "cost": 1,
      "targetRule": "SingleEnemy",
      "tags": ["Attack"],
      "effectCommands": [ { "type": "Damage", "amount": 6 } ]
    },
    {
      "id": "Rouge_Card_Defend",
      "nameKey": "防御",
      "rarity": "Common",
      "cost": 1,
      "targetRule": "Self",
      "tags": ["Skill"],
      "effectCommands": [ { "type": "GainShield", "amount": 5 } ]
    }
  ]
}
```

## 3. enemies.json（片段）
```json
{
  "contentVersion": "0.1.0",
  "enemies": [
    {
      "id": "Rouge_Enemy_Slime",
      "nameKey": "史莱姆",
      "maxHp": 24,
      "intentTable": [
        { "intentType": "Attack", "effectCommands": [ { "type": "Damage", "amount": 6 } ] },
        { "intentType": "Defend", "effectCommands": [ { "type": "GainShield", "amount": 5 } ] }
      ]
    }
  ]
}
```

## 4. encounters.json（片段）
```json
{
  "contentVersion": "0.1.0",
  "encounters": [
    {
      "id": "Rouge_Encounter_SlimeSolo",
      "enemyIds": ["Rouge_Enemy_Slime"],
      "isElite": false,
      "rewardPoolId": "Rouge_RewardPool_Act1"
    }
  ]
}
```

## 5. map_act1.json（片段）
```json
{
  "contentVersion": "0.1.0",
  "id": "Rouge_Map_Act1",
  "act": 1,
  "nodes": [
    { "nodeId": "N1", "nodeType": "Battle", "encounterId": "Rouge_Encounter_SlimeSolo", "nextNodeIds": ["N2"] },
    { "nodeId": "N2", "nodeType": "Shop", "shopId": "Rouge_Shop_Act1", "nextNodeIds": ["N3"] },
    { "nodeId": "N3", "nodeType": "Boss", "encounterId": "Rouge_Encounter_Boss", "nextNodeIds": [] }
  ]
}
```

## 6. rewards.json（片段）
```json
{
  "contentVersion": "0.1.0",
  "rewardPools": [
    {
      "id": "Rouge_RewardPool_Act1",
      "gold": { "min": 10, "max": 25 },
      "cardRewards": [
        { "cardId": "Rouge_Card_Strike", "weight": 10 },
        { "cardId": "Rouge_Card_Defend", "weight": 10 }
      ]
    }
  ]
}
```

## 7. events.json（片段）
```json
{
  "contentVersion": "0.1.0",
  "events": [
    {
      "id": "Rouge_Event_HealingFountain",
      "titleKey": "治疗之泉",
      "descriptionKey": "你发现一汪清泉…",
      "choices": [
        { "choiceId": "Drink", "textKey": "饮用", "effects": [ { "type": "Heal", "amount": 10 } ] },
        { "choiceId": "Leave", "textKey": "离开", "effects": [] }
      ]
    }
  ]
}
```

## 8. tuning.json（片段）
```json
{
  "contentVersion": "0.1.0",
  "tuning": {
    "Battle_EnergyPerTurn": 3,
    "Battle_HandSize": 5,
    "Reward_CardPickOptions": 3,
    "Run_AutoSaveAfterNode": true
  }
}
```
