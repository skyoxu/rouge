#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify mapping integrity between task SSoT files and Taskmaster view.

Files:
- .taskmaster/tasks/tasks_back.json      (NG task SSoT)
- .taskmaster/tasks/tasks_gameplay.json  (GM task SSoT)
- .taskmaster/tasks/tasks.json           (Taskmaster view; expects master.tasks)

Hard checks:
1) Every Taskmaster task (master.tasks) has a source task by taskmaster_id.
2) Every source task with taskmaster_exported=true exists in master.tasks.
3) Source tasks preserve required metadata fields:
   layer, adr_refs, chapter_refs, overlay_refs, acceptance, story_id.
4) Taskmaster tasks preserve required fields:
   description, details, testStrategy, dependencies.

Soft check (visibility only):
- Whether master.tasks[*].details includes Story/ADR/CH/overlay markers.

Exit codes:
- 0: all hard checks pass
- 1: any hard check failed
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_list(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list at {path}")
    return data


def is_non_empty_list(v: object) -> bool:
    return isinstance(v, list) and len(v) > 0


def main() -> int:
    root = Path(__file__).resolve().parents[2]

    tasks_json_path = root / ".taskmaster" / "tasks" / "tasks.json"
    tasks_data = load_json(tasks_json_path)
    if not isinstance(tasks_data, dict):
        print("ERROR: tasks.json is not an object")
        return 1

    master_tasks = tasks_data.get("master", {}).get("tasks", [])
    if not isinstance(master_tasks, list):
        print("ERROR: tasks.json master.tasks is not a list")
        return 1

    source_files = [
        (root / ".taskmaster" / "tasks" / "tasks_back.json", "NG"),
        (root / ".taskmaster" / "tasks" / "tasks_gameplay.json", "GM"),
    ]

    source_by_tm_id: dict[int, dict[str, Any]] = {}
    exported_tm_ids: set[int] = set()
    source_metadata_missing: list[str] = []

    for file_path, kind in source_files:
        tasks = load_json_list(file_path)
        for t in tasks:
            tm_id = t.get("taskmaster_id")
            if tm_id is None:
                continue
            try:
                tm_id_int = int(tm_id)
            except Exception:
                source_metadata_missing.append(f"{t.get('id')} invalid taskmaster_id={tm_id!r}")
                continue

            enriched = dict(t)
            enriched["_source_file"] = str(file_path.relative_to(root)).replace("\\", "/")
            enriched["_source_kind"] = kind
            source_by_tm_id[tm_id_int] = enriched

            if t.get("taskmaster_exported"):
                exported_tm_ids.add(tm_id_int)

            missing_bits: list[str] = []
            if not str(t.get("layer", "")).strip():
                missing_bits.append("layer")
            if not is_non_empty_list(t.get("adr_refs")):
                missing_bits.append("adr_refs")
            if not is_non_empty_list(t.get("chapter_refs")):
                missing_bits.append("chapter_refs")
            if not is_non_empty_list(t.get("overlay_refs")):
                missing_bits.append("overlay_refs")
            if not is_non_empty_list(t.get("acceptance")):
                missing_bits.append("acceptance")
            if not str(t.get("story_id", "")).strip():
                missing_bits.append("story_id")

            if missing_bits:
                source_metadata_missing.append(f"{t.get('id')} missing {','.join(missing_bits)}")

    master_ids: list[int] = []
    master_field_missing: list[str] = []
    missing_source_mapping: list[int] = []

    story_marker = 0
    adr_marker = 0
    ch_marker = 0
    overlay_marker = 0

    for mt in master_tasks:
        tm_id = mt.get("id")
        if not isinstance(tm_id, int):
            master_field_missing.append(f"master task has non-int id: {tm_id!r}")
            continue
        master_ids.append(tm_id)

        if not str(mt.get("description", "")).strip():
            master_field_missing.append(f"{tm_id} missing description")
        if not str(mt.get("details", "")).strip():
            master_field_missing.append(f"{tm_id} missing details")
        if not str(mt.get("testStrategy", "")).strip():
            master_field_missing.append(f"{tm_id} missing testStrategy")
        deps = mt.get("dependencies")
        if deps is None or not isinstance(deps, list):
            master_field_missing.append(f"{tm_id} missing dependencies list")

        if tm_id not in source_by_tm_id:
            missing_source_mapping.append(tm_id)

        details = str(mt.get("details", ""))
        if "Story:" in details or "Story-ID:" in details:
            story_marker += 1
        if "ADR-" in details:
            adr_marker += 1
        if re.search(r"\bCH\d{2}\b", details):
            ch_marker += 1
        if "docs/architecture/overlays/" in details:
            overlay_marker += 1

    missing_exported_in_master = sorted(exported_tm_ids - set(master_ids))

    print("=" * 60)
    print("Task Mapping Report (SSoT NG/GM -> tasks.json master)")
    print("=" * 60)
    print(f"master.tasks: {len(master_tasks)}")
    print(f"source tasks with taskmaster_id: {len(source_by_tm_id)}")
    print(f"source tasks exported: {len(exported_tm_ids)}")
    print()

    hard_fail = False

    if missing_source_mapping:
        hard_fail = True
        print(f"[FAIL] {len(missing_source_mapping)} master task(s) missing source mapping:")
        print("  " + ", ".join(str(x) for x in missing_source_mapping[:30]))
        if len(missing_source_mapping) > 30:
            print("  ...")

    if missing_exported_in_master:
        hard_fail = True
        print(f"[FAIL] {len(missing_exported_in_master)} exported source task(s) missing in master.tasks:")
        print("  " + ", ".join(str(x) for x in missing_exported_in_master[:30]))
        if len(missing_exported_in_master) > 30:
            print("  ...")

    if source_metadata_missing:
        hard_fail = True
        print(f"[FAIL] {len(source_metadata_missing)} source task(s) missing required metadata fields:")
        for line in source_metadata_missing[:20]:
            print("  - " + line)
        if len(source_metadata_missing) > 20:
            print("  ...")

    if master_field_missing:
        hard_fail = True
        print(f"[FAIL] {len(master_field_missing)} master task(s) missing required fields:")
        for line in master_field_missing[:20]:
            print("  - " + line)
        if len(master_field_missing) > 20:
            print("  ...")

    print()
    print("[INFO] details markers (non-blocking):")
    print(f"  story markers:   {story_marker}/{len(master_tasks)}")
    print(f"  ADR markers:     {adr_marker}/{len(master_tasks)}")
    print(f"  CH markers:      {ch_marker}/{len(master_tasks)}")
    print(f"  overlay markers: {overlay_marker}/{len(master_tasks)}")
    print()

    if hard_fail:
        print("[RESULT] FAIL")
        return 1

    print("[RESULT] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
