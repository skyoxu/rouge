#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix text-level event naming drift: replace `core.rouge.*` strings with existing `core.*` event semantics.

Scope (explicit, per user request):
  Only tasks with master ids: 7, 16, 20, 22, 29, 56

Targets:
  - .taskmaster/tasks/tasks_gameplay.json (view tasks) fields:
      title, description, acceptance[*] (prefix only; preserve "Refs:" suffix verbatim), test_strategy[*]
  - .taskmaster/tasks/tasks.json (master tasks) fields:
      description, details, testStrategy, subtasks[*].description/details/testStrategy

This script does NOT modify contractRefs.
It writes an audit JSON to logs/ci/<YYYY-MM-DD>/fix-core-rouge-eventtype-drift.json
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_TARGET_TASK_IDS = [7, 16, 20, 22, 29, 56]

# Keep this mapping minimal and explicit to avoid accidental semantics drift.
# If a new core.rouge.* string appears in these tasks, the script will fail fast.
REWRITE_MAP: dict[str, str] = {
    # battle lifecycle
    "core.rouge.battle.started": "core.battle.started",
    "core.rouge.battle.won": "core.battle.ended",
    "core.rouge.battle.lost": "core.battle.ended",
    # turn lifecycle (no dedicated "player ended" event in current contract set; map to enemy turn started transition)
    "core.rouge.turn.player.started": "core.battle.turn.player.started",
    "core.rouge.turn.player.ended": "core.battle.turn.enemy.started",
    # granular effect sub-events (represented by EffectsResolved payload)
    "core.rouge.combat.damage.applied": "core.effect.resolved",
    "core.rouge.status.applied": "core.effect.resolved",
    # node lifecycle (represented by MapNodeSelected in current contract set)
    "core.rouge.run.node.entered": "core.map.node.selected",
}

ROUGE_EVENT_RE = re.compile(r"\bcore\.rouge\.[a-z0-9_.-]+\b", flags=re.IGNORECASE)
REFS_RE = re.compile(r"\bRefs\s*:\s*.+$", flags=re.IGNORECASE)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _split_refs_suffix(text: str) -> tuple[str, str]:
    s = str(text or "")
    m = REFS_RE.search(s)
    if not m:
        return s, ""
    return s[: m.start()].rstrip(), s[m.start() :].strip()


def _rewrite_text(text: str, *, allow_no_change: bool = True) -> tuple[str, list[dict[str, str]], list[str]]:
    """
    Returns: (new_text, replacements[], unmatched_rouge_event_strings[])
    """
    s = str(text or "")
    found = [m.group(0) for m in ROUGE_EVENT_RE.finditer(s)]
    if not found:
        return s, [], []

    # Normalize to the exact lowercase key for mapping.
    replacements: list[dict[str, str]] = []
    unmatched: list[str] = []

    new_s = s
    for raw in sorted(set(found), key=lambda x: (len(x), x)):
        key = raw.lower()
        mapped = REWRITE_MAP.get(key)
        if not mapped:
            unmatched.append(raw)
            continue
        # Replace case-insensitively but only for this exact token.
        new_s2, n = re.subn(re.escape(raw), mapped, new_s, flags=re.IGNORECASE)
        if n > 0:
            replacements.append({"from": raw, "to": mapped, "count": str(n)})
            new_s = new_s2

    if unmatched and not allow_no_change:
        raise ValueError(f"Unmatched core.rouge.* event types: {unmatched}")

    return new_s, replacements, unmatched


def _update_entry(entry: dict[str, Any], *, audit: list[dict[str, Any]], path_label: str, target_ids: set[int]) -> None:
    tid = int(entry.get("taskmaster_id"))
    if tid not in target_ids:
        return

    def rewrite_field(field: str) -> None:
        before = entry.get(field)
        if before is None:
            return
        after, repl, unmatched = _rewrite_text(str(before))
        if unmatched:
            raise ValueError(f"{path_label} task {tid} field {field} contains unknown drift: {unmatched}")
        if after != str(before):
            entry[field] = after
            audit.append({"where": path_label, "task_id": tid, "field": field, "replacements": repl})

    rewrite_field("title")
    rewrite_field("description")

    # acceptance: preserve "Refs:" suffix verbatim.
    acc = entry.get("acceptance")
    if isinstance(acc, list):
        new_acc: list[str] = []
        for i, raw in enumerate(acc):
            prefix, refs = _split_refs_suffix(str(raw))
            new_prefix, repl, unmatched = _rewrite_text(prefix)
            if unmatched:
                raise ValueError(f"{path_label} task {tid} acceptance[{i}] contains unknown drift: {unmatched}")
            new_line = (new_prefix + (" " + refs if refs else "")).strip()
            if new_line != str(raw).strip() and repl:
                audit.append({"where": path_label, "task_id": tid, "field": f"acceptance[{i}]", "replacements": repl})
            new_acc.append(new_line)
        entry["acceptance"] = new_acc

    ts = entry.get("test_strategy")
    if isinstance(ts, list):
        new_ts: list[str] = []
        for i, raw in enumerate(ts):
            after, repl, unmatched = _rewrite_text(str(raw))
            if unmatched:
                raise ValueError(f"{path_label} task {tid} test_strategy[{i}] contains unknown drift: {unmatched}")
            if after != str(raw) and repl:
                audit.append({"where": path_label, "task_id": tid, "field": f"test_strategy[{i}]", "replacements": repl})
            new_ts.append(after)
        entry["test_strategy"] = new_ts


def _update_master_task(master_task: dict[str, Any], *, audit: list[dict[str, Any]], path_label: str, target_ids: set[int]) -> None:
    tid = int(str(master_task.get("id")))
    if tid not in target_ids:
        return

    def rewrite_key(key: str) -> None:
        before = master_task.get(key)
        if before is None:
            return
        after, repl, unmatched = _rewrite_text(str(before))
        if unmatched:
            raise ValueError(f"{path_label} master task {tid} key {key} contains unknown drift: {unmatched}")
        if after != str(before) and repl:
            master_task[key] = after
            audit.append({"where": path_label, "task_id": tid, "field": key, "replacements": repl})

    for k in ["description", "details", "testStrategy"]:
        rewrite_key(k)

    subs = master_task.get("subtasks")
    if isinstance(subs, list):
        for sidx, sub in enumerate(subs):
            if not isinstance(sub, dict):
                continue
            for k in ["title", "description", "details", "testStrategy"]:
                before = sub.get(k)
                if before is None:
                    continue
                after, repl, unmatched = _rewrite_text(str(before))
                if unmatched:
                    raise ValueError(f"{path_label} master task {tid} subtasks[{sidx}].{k} contains unknown drift: {unmatched}")
                if after != str(before) and repl:
                    sub[k] = after
                    audit.append({"where": path_label, "task_id": tid, "field": f"subtasks[{sidx}].{k}", "replacements": repl})


def _detect_target_ids_from_tasks_json(tasks_json: dict[str, Any]) -> set[int]:
    tasks = (tasks_json.get("master") or {}).get("tasks") or []
    out: set[int] = set()
    if not isinstance(tasks, list):
        return out
    for t in tasks:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or "").strip()
        if not tid.isdigit():
            continue
        blob = json.dumps(t, ensure_ascii=False)
        if ROUGE_EVENT_RE.search(blob):
            out.add(int(tid))
    return out


def _detect_target_ids_from_gameplay_view(gameplay: list[dict[str, Any]]) -> set[int]:
    out: set[int] = set()
    for t in gameplay:
        if not isinstance(t, dict):
            continue
        tid = t.get("taskmaster_id")
        if tid is None:
            continue
        try:
            tid_i = int(tid)
        except Exception:
            continue
        blob = json.dumps(t, ensure_ascii=False)
        if ROUGE_EVENT_RE.search(blob):
            out.add(tid_i)
    return out


def main() -> int:
    root = _repo_root()
    gameplay_path = root / ".taskmaster" / "tasks" / "tasks_gameplay.json"
    tasks_json_path = root / ".taskmaster" / "tasks" / "tasks.json"

    gameplay = _load_json(gameplay_path)
    tasks_json = _load_json(tasks_json_path)

    if not isinstance(gameplay, list):
        raise SystemExit("tasks_gameplay.json must be an array")

    master_tasks = (tasks_json.get("master") or {}).get("tasks") or []
    if not isinstance(master_tasks, list):
        raise SystemExit("tasks.json master.tasks must be an array")

    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--task-ids",
        default="",
        help="Optional CSV task ids to process. Default: auto-detect tasks containing core.rouge.* in tasks.json/tasks_gameplay.",
    )
    ap.add_argument(
        "--use-default-targets",
        action="store_true",
        help="Process the historical default target set only (7,16,20,22,29,56).",
    )
    args = ap.parse_args()

    if str(args.task_ids).strip():
        target_ids = {int(x.strip()) for x in str(args.task_ids).split(",") if x.strip().isdigit()}
    elif bool(args.use_default_targets):
        target_ids = set(DEFAULT_TARGET_TASK_IDS)
    else:
        target_ids = _detect_target_ids_from_tasks_json(tasks_json) | _detect_target_ids_from_gameplay_view(gameplay)

    if not target_ids:
        print("FIX_CORE_ROUGE_EVENTTYPE_DRIFT changed=0 reason=no_targets_found")
        return 0

    audit: list[dict[str, Any]] = []

    for entry in gameplay:
        if isinstance(entry, dict) and entry.get("taskmaster_id") is not None:
            _update_entry(entry, audit=audit, path_label="tasks_gameplay.json", target_ids=target_ids)

    for t in master_tasks:
        if not isinstance(t, dict):
            continue
        tid_s = str(t.get("id") or "").strip()
        if tid_s.isdigit() and int(tid_s) in target_ids:
            _update_master_task(t, audit=audit, path_label="tasks.json", target_ids=target_ids)

    _write_json(gameplay_path, gameplay)
    _write_json(tasks_json_path, tasks_json)

    out_path = root / "logs" / "ci" / _dt.date.today().isoformat() / "fix-core-rouge-eventtype-drift.json"
    _write_json(out_path, {"targets": sorted(target_ids), "rewrite_map": REWRITE_MAP, "changes": audit})

    print(f"FIX_CORE_ROUGE_EVENTTYPE_DRIFT changed={len(audit)} out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
