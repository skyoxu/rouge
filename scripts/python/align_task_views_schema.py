#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalize NG/GM view task files schema (Rouge).

Files:
- .taskmaster/tasks/tasks_back.json
- .taskmaster/tasks/tasks_gameplay.json

Policy:
- View task files are SSoT for cross-references via snake_case fields:
  - adr_refs
  - chapter_refs
  - overlay_refs
- Remove legacy Task Master context fields from view files:
  - adrRefs
  - archRefs
  - overlay
- Keep optional additive fields for downstream tooling:
  - contractRefs (list)

This script does NOT populate any derived values. It only normalizes presence/absence.
All writes are UTF-8 with LF newlines.

Outputs:
- logs/ci/<YYYY-MM-DD>/taskmaster-rouge/align_task_views_schema.json

Windows:
  py -3 scripts/python/align_task_views_schema.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


@dataclass
class FileReport:
    path: str
    tasks_total: int
    tasks_changed: int
    added_fields: dict[str, int]
    removed_fields: dict[str, int]


LEGACY_FIELDS: tuple[str, ...] = (
    "adrRefs",
    "archRefs",
    "overlay",
)

REQUIRED_FIELDS: dict[str, Any] = {
    "contractRefs": [],
}


def align_task_item(task: dict[str, Any]) -> tuple[bool, dict[str, int], dict[str, int]]:
    changed = False
    added: dict[str, int] = {k: 0 for k in REQUIRED_FIELDS}
    removed: dict[str, int] = {k: 0 for k in LEGACY_FIELDS}

    for k in LEGACY_FIELDS:
        if k in task:
            task.pop(k, None)
            removed[k] += 1
            changed = True

    for k, default in REQUIRED_FIELDS.items():
        if k not in task:
            task[k] = default if not isinstance(default, (list, dict)) else json.loads(json.dumps(default))
            added[k] += 1
            changed = True

    return changed, added, removed


def align_file(path: Path) -> FileReport:
    obj = load_json(path)
    tasks: list[dict[str, Any]]
    if isinstance(obj, list):
        tasks = [t for t in obj if isinstance(t, dict)]
    elif isinstance(obj, dict) and isinstance(obj.get("tasks"), list):
        tasks = [t for t in obj["tasks"] if isinstance(t, dict)]
    else:
        raise ValueError(f"Unsupported JSON root for {path}: {type(obj)}")

    changed_count = 0
    added_total: dict[str, int] = {k: 0 for k in REQUIRED_FIELDS}
    removed_total: dict[str, int] = {k: 0 for k in LEGACY_FIELDS}

    for t in tasks:
        changed, added, removed = align_task_item(t)
        if changed:
            changed_count += 1
        for k, v in added.items():
            added_total[k] += int(v)
        for k, v in removed.items():
            removed_total[k] += int(v)

    dump_json(path, obj)

    return FileReport(
        path=str(path.relative_to(ROOT)).replace("\\", "/"),
        tasks_total=len(tasks),
        tasks_changed=changed_count,
        added_fields=added_total,
        removed_fields=removed_total,
    )


def main() -> int:
    back = ROOT / ".taskmaster" / "tasks" / "tasks_back.json"
    gameplay = ROOT / ".taskmaster" / "tasks" / "tasks_gameplay.json"
    if not back.exists() or not gameplay.exists():
        print("ERROR: missing tasks view files under .taskmaster/tasks/")
        return 2

    reports = [align_file(back), align_file(gameplay)]

    out = ROOT / "logs" / "ci" / today_str() / "taskmaster-rouge" / "align_task_views_schema.json"
    write_json(
        out,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "removed_fields": list(LEGACY_FIELDS),
            "required_fields": list(REQUIRED_FIELDS.keys()),
            "reports": [
                {
                    "path": r.path,
                    "tasks_total": r.tasks_total,
                    "tasks_changed": r.tasks_changed,
                    "added_fields": r.added_fields,
                    "removed_fields": r.removed_fields,
                }
                for r in reports
            ],
        },
    )

    print(
        "TASK_VIEWS_SCHEMA_ALIGN status=ok "
        f"files=2 changed={sum(r.tasks_changed for r in reports)} out={str(out).replace('\\', '/')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
