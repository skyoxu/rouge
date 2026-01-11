# Rouge v0 参考：内容平衡参数表（非 SSoT，不进门禁）

- 本表仅用于集中“可调参数”，避免散落在代码常量里。
- v0 原则：先覆盖闭环可测性/可玩性所需参数；复杂曲线与经济周期后置。

| Key | Type | Default | 用途 | 触及模块 |
|---|---|---:|---|---|
| Battle_EnergyPerTurn | int | 3 | 每回合基础能量 | Battle/Card |
| Battle_HandSize | int | 5 | 起始/回合抽牌基准 | Battle/Card |
| Battle_MaxHandSize | int | 10 | 手牌上限 | Battle |
| Battle_BlockDecayEachTurn | bool | true | 护盾回合衰减 | Battle |
| Reward_CardPickOptions | int | 3 | 战后选卡数量 | Reward |
| Reward_GoldMin | int | 10 | 战后金币下限 | Reward |
| Reward_GoldMax | int | 25 | 战后金币上限 | Reward |
| Shop_RerollCost | int | 25 | 商店刷新成本（若实现） | Shop |
| Shop_RemoveCardCost | int | 50 | 移除卡价格（若实现） | Shop/Deck |
| Run_AutoSaveAfterNode | bool | true | 完成节点后自动存档 | Run/Save |
| Run_SaveFileRelativePath | string | user://saves/current_run.json | 存档路径（固定，不接受输入） | Save/Security |
| Rng_UseSeededRng | bool | true | 随机性可复现 | Core |

## 2. 经验/成长（占位）

- 若后续引入经验曲线/局外成长：建议另起独立任务与文档，并把曲线/权重的校验纳入可测试范围。
