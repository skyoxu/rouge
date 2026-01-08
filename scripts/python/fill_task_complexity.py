#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fill `.taskmaster/tasks/tasks.json` task complexity values.

This is an LLM-assisted heuristic mapping aligned to the `sanguo` repo style:
- complexity is an integer (roughly 3..8)
- higher means larger cross-cutting scope, higher integration cost, and higher risk

Outputs an audit report to `logs/ci/<YYYY-MM-DD>/taskmaster-rouge/fill_task_complexity.json`.

Windows:
  py -3 scripts/python/fill_task_complexity.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASKS_JSON = ROOT / ".taskmaster" / "tasks" / "tasks.json"


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_int_like_id(v: object) -> int | None:
    if isinstance(v, int):
        return v
    s = str(v or "").strip()
    if not s:
        return None
    return int(s) if s.isdigit() else None


@dataclass(frozen=True)
class UpdateResult:
    task_id: str
    title: str
    before: int | None
    after: int | None


# LLM-chosen complexity values (3..8) for rouge tasks.
COMPLEXITY_BY_ID: dict[int, int] = {
    1: 5,
    2: 6,
    3: 6,
    4: 6,
    5: 5,
    6: 7,
    7: 8,
    8: 6,
    9: 5,
    10: 4,
    11: 6,
    12: 6,
    13: 6,
    14: 5,
    15: 6,
    16: 8,
    17: 5,
    18: 5,
    19: 5,
    20: 6,
    21: 6,
    22: 5,
    23: 4,
    24: 5,
    25: 5,
    26: 4,
    27: 4,
    28: 7,
    29: 7,
    30: 6,
    31: 6,
    32: 5,
    33: 4,
    34: 4,
    35: 5,
    36: 6,
    37: 5,
    38: 6,
    39: 5,
    40: 7,
    41: 6,
    42: 4,
    43: 3,
    44: 5,
    45: 5,
    46: 5,
    47: 6,
    48: 4,
    49: 4,
    50: 5,
    51: 5,
    52: 6,
    53: 4,
    54: 6,
    55: 7,
    56: 5,
}


def main() -> int:
    if not TASKS_JSON.exists():
        print(f"ERROR: missing {TASKS_JSON}")
        return 2

    data = load_json(TASKS_JSON)
    master = data.get("master")
    if not isinstance(master, dict):
        print("ERROR: tasks.json missing master object")
        return 2

    tasks = master.get("tasks")
    if not isinstance(tasks, list):
        print("ERROR: tasks.json master.tasks is not a list")
        return 2

    updates: list[UpdateResult] = []
    missing_ids: list[str] = []

    for t in tasks:
        if not isinstance(t, dict):
            continue
        tid_int = parse_int_like_id(t.get("id"))
        tid_str = str(t.get("id"))
        title = str(t.get("title") or "")
        before = t.get("complexity") if isinstance(t.get("complexity"), int) else None

        if tid_int is None:
            missing_ids.append(tid_str)
            continue
        after = COMPLEXITY_BY_ID.get(tid_int)
        if after is None:
            missing_ids.append(tid_str)
            continue

        if before != after:
            t["complexity"] = after
            updates.append(UpdateResult(task_id=tid_str, title=title, before=before, after=after))

    TASKS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "file": str(TASKS_JSON.relative_to(ROOT)).replace("\\", "/"),
        "tasks_total": len([x for x in tasks if isinstance(x, dict)]),
        "updated": len(updates),
        "missing_ids": missing_ids,
        "updates": [
            {"id": u.task_id, "title": u.title, "before": u.before, "after": u.after}
            for u in updates[:200]
        ],
    }

    out = ROOT / "logs" / "ci" / today_str() / "taskmaster-rouge" / "fill_task_complexity.json"
    write_json(out, report)

    status = "ok" if not missing_ids else "warn"
    print(f"TASK_COMPLEXITY_FILL status={status} updated={len(updates)} missing={len(missing_ids)} out={out}")
    return 0 if status == "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
