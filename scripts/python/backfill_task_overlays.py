#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill overlay references into Task Master tasks.json `details`.

Why:
- Task Master tasks.json cannot add new fields beyond the MCP schema.
- `overlay_refs` live in NG/GM SSoT files (tasks_back.json / tasks_gameplay.json).
- To keep "task -> overlay" traceability visible in Task Master views, we inject
  a single "Overlays: ..." line into the existing `details` field.

Policy:
- Does NOT add fields to tasks.json.
- Does NOT remove or rewrite subtasks.
- Only updates the `details` string for tasks that have an overlay_refs mapping.

Usage:
  py -3 scripts/python/backfill_task_overlays.py
  py -3 scripts/python/backfill_task_overlays.py --dry-run
  py -3 scripts/python/backfill_task_overlays.py --tag master
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_TASKMASTER_TASKS = ROOT / ".taskmaster" / "tasks" / "tasks.json"
DEFAULT_SOURCES = [
    ROOT / ".taskmaster" / "tasks" / "tasks_back.json",
    ROOT / ".taskmaster" / "tasks" / "tasks_gameplay.json",
]

OVERLAYS_LINE_RE = re.compile(r"(?im)^Overlays:\s*.*$", re.MULTILINE)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_task_list(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("tasks"), list):
        return [x for x in data["tasks"] if isinstance(x, dict)]
    return []


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip()


def normalize_overlay_refs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = [str(x) for x in value]
    else:
        return []

    out: list[str] = []
    seen: set[str] = set()
    for raw in items:
        v = normalize_path(raw)
        if not v:
            continue
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def build_overlay_map(sources: list[Path]) -> dict[int, list[str]]:
    overlay_by_tm_id: dict[int, list[str]] = {}
    collisions: list[str] = []

    for src in sources:
        tasks = load_task_list(src)
        for t in tasks:
            tm_id = t.get("taskmaster_id")
            if tm_id is None:
                continue
            try:
                tm_id_int = int(tm_id)
            except Exception:
                continue

            overlay_refs = normalize_overlay_refs(t.get("overlay_refs"))
            if not overlay_refs:
                continue

            if tm_id_int in overlay_by_tm_id:
                # Keep the first mapping, but surface a warning.
                collisions.append(f"{tm_id_int}: {src.name} -> {t.get('id')}")
                continue

            overlay_by_tm_id[tm_id_int] = overlay_refs

    if collisions:
        print("[WARN] overlay map collisions detected (kept first mapping):")
        for line in collisions[:20]:
            print("  - " + line)
        if len(collisions) > 20:
            print("  ...")

    return overlay_by_tm_id


def upsert_overlays_line(details: str, overlays_line: str) -> tuple[str, bool]:
    if details is None:
        details = ""

    if OVERLAYS_LINE_RE.search(details):
        updated = OVERLAYS_LINE_RE.sub(overlays_line, details, count=1)
        return updated, updated != details

    if details.strip():
        return details.rstrip() + "\n" + overlays_line, True
    return overlays_line, True


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill overlay refs into tasks.json details.")
    parser.add_argument("--tasks-json", default=str(DEFAULT_TASKMASTER_TASKS), help="Path to .taskmaster/tasks/tasks.json")
    parser.add_argument("--tag", default="master", help="Task Master tag to update (default: master)")
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes without writing.")
    args = parser.parse_args()

    tasks_json_path = Path(args.tasks_json)
    if not tasks_json_path.is_absolute():
        tasks_json_path = ROOT / tasks_json_path

    overlay_by_tm_id = build_overlay_map(DEFAULT_SOURCES)
    if not overlay_by_tm_id:
        print("No overlay mappings found in source task files; nothing to do.")
        return 0

    data = load_json(tasks_json_path)
    if not isinstance(data, dict):
        print("ERROR: tasks.json is not a JSON object.")
        return 1

    tag_obj = data.get(args.tag)
    if not isinstance(tag_obj, dict):
        print(f"ERROR: tag '{args.tag}' not found or not an object in tasks.json.")
        return 1

    tag_tasks = tag_obj.get("tasks")
    if not isinstance(tag_tasks, list):
        print(f"ERROR: tasks.json[{args.tag}].tasks is not a list.")
        return 1

    changed = 0
    touched = 0
    for t in tag_tasks:
        if not isinstance(t, dict):
            continue
        tm_id_raw = t.get("id")
        tm_id_int: int | None = None
        if isinstance(tm_id_raw, int):
            tm_id_int = tm_id_raw
        elif isinstance(tm_id_raw, str) and tm_id_raw.strip().isdigit():
            tm_id_int = int(tm_id_raw.strip())
        if tm_id_int is None:
            continue
        overlay_refs = overlay_by_tm_id.get(tm_id_int)
        if not overlay_refs:
            continue

        overlays_line = "Overlays: " + "; ".join(overlay_refs)
        details = t.get("details") or ""
        new_details, did_change = upsert_overlays_line(str(details), overlays_line)
        touched += 1
        if did_change:
            changed += 1
            t["details"] = new_details

    print(f"Tasks with overlay mapping: {touched}")
    print(f"Tasks changed: {changed}")

    if changed == 0:
        print("No changes required.")
        return 0

    if args.dry_run:
        print("[DRY-RUN] Not writing tasks.json.")
        return 0

    tasks_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote: {tasks_json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
