#!/usr/bin/env python3
"""Minimal checks for Rouge run-loop contracts.

This script validates that the *minimum playable loop* (T2) domain events
exist on disk and expose the expected EventType constants and namespaces.

This is a stop-loss gate: it intentionally checks a small, stable event set
used by the run/map/battle/reward/event flow.

Contracts checked (SSoT):
- Game.Core/Contracts/Rouge/Run/RunStarted.cs
- Game.Core/Contracts/Rouge/Map/MapGenerated.cs
- Game.Core/Contracts/Rouge/Map/MapNodeSelected.cs
- Game.Core/Contracts/Rouge/Map/MapNodeCompleted.cs
- Game.Core/Contracts/Rouge/Battle/BattleStarted.cs
- Game.Core/Contracts/Rouge/Battle/PlayerTurnStarted.cs
- Game.Core/Contracts/Rouge/Cards/CardPlayed.cs
- Game.Core/Contracts/Rouge/Effects/EffectsResolved.cs
- Game.Core/Contracts/Rouge/Battle/EnemyTurnStarted.cs
- Game.Core/Contracts/Rouge/Battle/BattleEnded.cs
- Game.Core/Contracts/Rouge/Rewards/RewardOffered.cs
- Game.Core/Contracts/Rouge/Rewards/RewardSelected.cs
- Game.Core/Contracts/Rouge/Events/EventChoiceResolved.cs
- Game.Core/Contracts/Rouge/Run/RunEnded.cs

Exit code:
- 0 when all checks pass.
- 1 when any problem is detected.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ContractExpectation:
    path: str
    event_type: str
    namespace: str


EXPECTED: List[ContractExpectation] = [
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Run/RunStarted.cs",
        event_type="core.run.started",
        namespace="Game.Core.Contracts.Rouge.Run",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Map/MapGenerated.cs",
        event_type="core.map.generated",
        namespace="Game.Core.Contracts.Rouge.Map",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Map/MapNodeSelected.cs",
        event_type="core.map.node.selected",
        namespace="Game.Core.Contracts.Rouge.Map",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Map/MapNodeCompleted.cs",
        event_type="core.map.node.completed",
        namespace="Game.Core.Contracts.Rouge.Map",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Battle/BattleStarted.cs",
        event_type="core.battle.started",
        namespace="Game.Core.Contracts.Rouge.Battle",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Battle/PlayerTurnStarted.cs",
        event_type="core.battle.turn.player.started",
        namespace="Game.Core.Contracts.Rouge.Battle",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Cards/CardPlayed.cs",
        event_type="core.card.played",
        namespace="Game.Core.Contracts.Rouge.Cards",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Effects/EffectsResolved.cs",
        event_type="core.effect.resolved",
        namespace="Game.Core.Contracts.Rouge.Effects",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Battle/EnemyTurnStarted.cs",
        event_type="core.battle.turn.enemy.started",
        namespace="Game.Core.Contracts.Rouge.Battle",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Battle/BattleEnded.cs",
        event_type="core.battle.ended",
        namespace="Game.Core.Contracts.Rouge.Battle",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Rewards/RewardOffered.cs",
        event_type="core.reward.offered",
        namespace="Game.Core.Contracts.Rouge.Rewards",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Rewards/RewardSelected.cs",
        event_type="core.reward.selected",
        namespace="Game.Core.Contracts.Rouge.Rewards",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Events/EventChoiceResolved.cs",
        event_type="core.event.choice.resolved",
        namespace="Game.Core.Contracts.Rouge.Events",
    ),
    ContractExpectation(
        path="Game.Core/Contracts/Rouge/Run/RunEnded.cs",
        event_type="core.run.ended",
        namespace="Game.Core.Contracts.Rouge.Run",
    ),
]


def _extract_event_type_constant(text: str) -> Optional[str]:
    marker = 'public const string EventType = "'
    idx = text.find(marker)
    if idx < 0:
        return None
    start = idx + len(marker)
    end = text.find('";', start)
    if end < 0:
        return None
    return text[start:end]


def check_contract(exp: ContractExpectation) -> Dict[str, object]:
    rel = Path(exp.path)
    full = ROOT / rel
    result: Dict[str, object] = {
        "path": exp.path,
        "exists": full.exists(),
        "namespace_ok": False,
        "event_type_ok": False,
        "expected_event_type": exp.event_type,
        "expected_namespace": exp.namespace,
    }

    if not full.exists():
        return result

    text = full.read_text(encoding="utf-8")
    result["namespace_ok"] = f"namespace {exp.namespace};" in text
    actual = _extract_event_type_constant(text)
    result["actual_event_type"] = actual
    result["event_type_ok"] = actual == exp.event_type
    return result


def main() -> int:
    results = [check_contract(exp) for exp in EXPECTED]
    ok = all(r["exists"] and r["namespace_ok"] and r["event_type_ok"] for r in results)

    report = {
        "ok": ok,
        "expected_event_types": [e.event_type for e in EXPECTED],
        "contracts": results,
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
