#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repair task text fields from a known-good Git revision.

Background:
- Some files may get text-corrupted (e.g., turned into "????") due to a bad editor/encoding pipeline.
- This script restores specific text fields from `git show <rev>:<path>` when corruption is detected.

Current targets (repo conventions):
- .taskmaster/tasks/tasks_gameplay.json: restore task["description"] for tasks whose description contains "????".
- .taskmaster/tasks/tasks.json (Task Master): restore master.tasks[*]["details"] for tasks whose details contains "????".

Policy:
- UTF-8 read/write.
- Conservative: only repairs fields that match the corruption marker.
- Writes an audit report under logs/ci/<YYYY-MM-DD>/encoding/.

Usage (Windows):
  py -3 scripts/python/repair_tasks_text_from_git.py --write
  py -3 scripts/python/repair_tasks_text_from_git.py --commit bed50db --write
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CORRUPTION_MARKER = "????"


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_show(rev: str, relpath: str) -> str:
    out = subprocess.check_output(
        ["git", "show", f"{rev}:{relpath}"],
        cwd=str(ROOT),
    )
    return out.decode("utf-8")


def repair_tasks_gameplay(*, current: list[dict[str, Any]], current_path: Path, baseline_rev: str) -> dict[str, Any]:
    relpath = current_path.relative_to(ROOT).as_posix()
    baseline_text = git_show(baseline_rev, relpath)
    baseline = json.loads(baseline_text)

    if not isinstance(baseline, list) or not isinstance(current, list):
        raise ValueError("tasks_gameplay.json must be a JSON array")

    baseline_by_id: dict[str, dict[str, Any]] = {
        str(t.get("id")): t for t in baseline if isinstance(t, dict) and str(t.get("id", "")).strip()
    }

    repaired: list[dict[str, Any]] = []
    missing_in_baseline: list[str] = []
    for t in current:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or "").strip()
        if not tid:
            continue
        desc = t.get("description")
        if not isinstance(desc, str) or CORRUPTION_MARKER not in desc:
            continue
        b = baseline_by_id.get(tid)
        if not b:
            missing_in_baseline.append(tid)
            continue
        b_desc = b.get("description")
        if isinstance(b_desc, str) and CORRUPTION_MARKER not in b_desc:
            t["description"] = b_desc
            repaired.append({"id": tid, "field": "description"})

    return {
        "path": relpath,
        "repaired": repaired,
        "missing_in_baseline": sorted(set(missing_in_baseline)),
    }


def repair_tasks_json_details(
    *, current: dict[str, Any], current_path: Path, baseline_rev: str, tag: str
) -> dict[str, Any]:
    relpath = current_path.relative_to(ROOT).as_posix()
    baseline_text = git_show(baseline_rev, relpath)
    baseline = json.loads(baseline_text)

    if not isinstance(baseline, dict) or not isinstance(current, dict):
        raise ValueError("tasks.json must be a JSON object")

    b_tag = baseline.get(tag)
    c_tag = current.get(tag)
    if not isinstance(b_tag, dict) or not isinstance(c_tag, dict):
        raise ValueError(f"tasks.json missing tag object: {tag}")

    b_tasks = b_tag.get("tasks")
    c_tasks = c_tag.get("tasks")
    if not isinstance(b_tasks, list) or not isinstance(c_tasks, list):
        raise ValueError(f"tasks.json[{tag}].tasks must be a list")

    baseline_by_id: dict[str, dict[str, Any]] = {
        str(t.get("id")): t for t in b_tasks if isinstance(t, dict) and str(t.get("id", "")).strip()
    }

    repaired: list[dict[str, Any]] = []
    missing_in_baseline: list[str] = []
    for t in c_tasks:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or "").strip()
        if not tid:
            continue
        details = t.get("details")
        if not isinstance(details, str) or CORRUPTION_MARKER not in details:
            continue
        b = baseline_by_id.get(tid)
        if not b:
            missing_in_baseline.append(tid)
            continue
        b_details = b.get("details")
        if isinstance(b_details, str) and CORRUPTION_MARKER not in b_details:
            t["details"] = b_details
            repaired.append({"id": tid, "field": "details"})

    return {
        "path": relpath,
        "tag": tag,
        "repaired": repaired,
        "missing_in_baseline": sorted(set(missing_in_baseline)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair corrupted task text fields from a Git revision.")
    ap.add_argument("--commit", default="HEAD", help="Git revision used as baseline (default: HEAD).")
    ap.add_argument("--tag", default="master", help="Task Master tag for tasks.json (default: master).")
    ap.add_argument("--write", action="store_true", help="Write repaired files (default: dry-run).")
    args = ap.parse_args()

    gameplay_path = ROOT / ".taskmaster" / "tasks" / "tasks_gameplay.json"
    tasks_json_path = ROOT / ".taskmaster" / "tasks" / "tasks.json"

    report: dict[str, Any] = {
        "ts": utc_now_iso(),
        "baseline_commit": str(args.commit),
        "corruption_marker": CORRUPTION_MARKER,
        "results": {},
    }

    # 1) Repair tasks_gameplay descriptions.
    gameplay_current = load_json(gameplay_path)
    gameplay_result = repair_tasks_gameplay(current=gameplay_current, current_path=gameplay_path, baseline_rev=args.commit)
    report["results"]["tasks_gameplay"] = gameplay_result

    # 2) Repair tasks.json details.
    tasks_json_current = load_json(tasks_json_path)
    tasks_json_result = repair_tasks_json_details(
        current=tasks_json_current,
        current_path=tasks_json_path,
        baseline_rev=args.commit,
        tag=str(args.tag),
    )
    report["results"]["tasks_json"] = tasks_json_result

    # Determine if there are changes (repaired fields).
    changed_gameplay = len(gameplay_result.get("repaired") or []) > 0
    changed_tasks_json = len(tasks_json_result.get("repaired") or []) > 0

    if args.write:
        if changed_gameplay:
            write_json(gameplay_path, gameplay_current)
            print(f"Wrote: {gameplay_path}")
        if changed_tasks_json:
            write_json(tasks_json_path, tasks_json_current)
            print(f"Wrote: {tasks_json_path}")
    else:
        print("[DRY-RUN] Not writing task files (use --write).")

    date = dt.date.today().isoformat()
    out_path = ROOT / "logs" / "ci" / date / "encoding" / "repair-tasks-text-from-git.json"
    write_json(out_path, report)
    print(f"Wrote report: {out_path}")

    repaired_total = len((gameplay_result.get("repaired") or [])) + len((tasks_json_result.get("repaired") or []))
    if repaired_total == 0:
        print("No corrupted fields detected; nothing repaired.")
    else:
        print(f"Repaired fields: {repaired_total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
