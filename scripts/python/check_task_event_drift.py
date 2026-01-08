#!/usr/bin/env python3
"""Detect drifted event-like terms in TaskMaster task descriptions.

This gate prevents re-introducing legacy/non-SSoT event names into:
- .taskmaster/tasks/tasks.json (master)
- .taskmaster/tasks/tasks_gameplay.json (view)

The project enforces a minimal domain event set (core.*) and uses snapshots/EffectsResolved
instead of fine-grained UI animation events.

Outputs:
- Writes a JSON report to --out.
- Prints a short ASCII summary for log capture.

Exit codes:
- 0: ok (no drift tokens found)
- 1: fail (drift tokens found)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


DRIFT_TOKENS: list[str] = [
    # Legacy / non-SSoT event names that caused cross-layer drift.
    "BattleWon",
    "BattleLost",
    "BattleStart",
    "BattleEnd",
    "PlayerTurnStart",
    "PlayerTurnEnd",
    "OnTurnStart",
    "OnTurnEnd",
    "UnitDamaged",
    "StatusApplied",
    "NodeEntered",
]


def compile_token(token: str) -> re.Pattern[str]:
    # Match token as a standalone identifier-ish fragment.
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])")


TOKEN_PATTERNS: dict[str, re.Pattern[str]] = {t: compile_token(t) for t in DRIFT_TOKENS}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_tasks_from_master(obj: dict[str, Any]) -> list[dict[str, Any]]:
    return (obj.get("master") or {}).get("tasks") or []


def scan_task_fields(task: dict[str, Any], *, fields: list[str]) -> dict[str, list[str]]:
    matches: dict[str, list[str]] = {}
    for field in fields:
        raw = task.get(field)
        if raw is None:
            continue
        text = str(raw)
        hits = [tok for tok, pat in TOKEN_PATTERNS.items() if pat.search(text)]
        if hits:
            matches[field] = hits
    return matches


def scan_master(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        matches = scan_task_fields(t, fields=["title", "description", "details", "expansionPrompt"])
        if matches:
            results.append(
                {
                    "id": str(t.get("id")),
                    "title": t.get("title"),
                    "matches": matches,
                }
            )
    return results


def scan_view(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        matches = scan_task_fields(t, fields=["id", "title", "description"])  # id included defensively
        # id matches are usually false positives; drop them unless other fields hit.
        if matches and not (len(matches) == 1 and "id" in matches):
            results.append(
                {
                    "id": str(t.get("id")),
                    "taskmaster_id": t.get("taskmaster_id"),
                    "title": t.get("title"),
                    "matches": {k: v for k, v in matches.items() if k != "id"},
                }
            )
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect drifted event-like tokens in task descriptions.")
    ap.add_argument(
        "--out",
        default=None,
        help="Output JSON path. Default: logs/ci/<YYYY-MM-DD>/task-semantic/task-event-drift.json",
    )
    args = ap.parse_args()

    root = repo_root()
    date = dt.date.today().strftime("%Y-%m-%d")
    out = Path(args.out) if args.out else (root / "logs" / "ci" / date / "task-semantic" / "task-event-drift.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    master_path = root / ".taskmaster" / "tasks" / "tasks.json"
    gameplay_path = root / ".taskmaster" / "tasks" / "tasks_gameplay.json"

    master_obj = load_json(master_path)
    gameplay_obj = load_json(gameplay_path)

    if not isinstance(master_obj, dict):
        raise ValueError("tasks.json must be an object")
    if not isinstance(gameplay_obj, list):
        raise ValueError("tasks_gameplay.json must be an array")

    master_hits = scan_master(iter_tasks_from_master(master_obj))
    gameplay_hits = scan_view(gameplay_obj)

    ok = (len(master_hits) == 0) and (len(gameplay_hits) == 0)
    report = {
        "status": "ok" if ok else "fail",
        "date": date,
        "tokens": DRIFT_TOKENS,
        "master": {
            "path": str(master_path.relative_to(root)).replace("\\", "/"),
            "hits": master_hits,
        },
        "tasks_gameplay": {
            "path": str(gameplay_path.relative_to(root)).replace("\\", "/"),
            "hits": gameplay_hits,
        },
    }

    out.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"TASK_EVENT_DRIFT status={report['status']} master_hits={len(master_hits)} gameplay_hits={len(gameplay_hits)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

