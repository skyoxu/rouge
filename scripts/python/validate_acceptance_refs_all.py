#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate acceptance "Refs:" mapping for all view tasks (tasks_back/tasks_gameplay).

This is a thin orchestrator around scripts/python/validate_acceptance_refs.py which
only validates one task at a time.

Outputs:
  logs/ci/<YYYY-MM-DD>/validate-acceptance-refs-all/
    task-<id>.json
    task-<id>.stdout.log
    task-<id>.stderr.log
    summary.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _task_ids_from_views(root: Path) -> list[int]:
    back = _load_json(root / ".taskmaster" / "tasks" / "tasks_back.json")
    game = _load_json(root / ".taskmaster" / "tasks" / "tasks_gameplay.json")
    if not isinstance(back, list) or not isinstance(game, list):
        raise ValueError("Expected tasks_back.json and tasks_gameplay.json to be JSON arrays.")
    ids: set[int] = set()
    for entry in back + game:
        if not isinstance(entry, dict):
            continue
        tid = entry.get("taskmaster_id")
        if tid is None:
            continue
        ids.add(int(tid))
    return sorted(ids)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["red", "green", "refactor"], required=True)
    parser.add_argument(
        "--out-dir",
        default="",
        help="Output directory. Default: logs/ci/<today>/validate-acceptance-refs-all",
    )
    args = parser.parse_args()

    root = _repo_root()
    date = _dt.date.today().isoformat()
    out_dir_arg = str(args.out_dir or "").strip()
    if not out_dir_arg:
        out_dir = root / "logs" / "ci" / date / "validate-acceptance-refs-all"
    else:
        out_dir_path = Path(out_dir_arg)
        out_dir = out_dir_path if out_dir_path.is_absolute() else (root / out_dir_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    ids = _task_ids_from_views(root)
    fails: list[int] = []

    validator = root / "scripts" / "python" / "validate_acceptance_refs.py"
    for tid in ids:
        out_json = out_dir / f"task-{tid}.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(validator),
                "--task-id",
                str(tid),
                "--stage",
                args.stage,
                "--out",
                str(out_json),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        (out_dir / f"task-{tid}.stdout.log").write_text(proc.stdout, encoding="utf-8")
        (out_dir / f"task-{tid}.stderr.log").write_text(proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            fails.append(tid)

    summary = {"date": date, "stage": args.stage, "tasks": len(ids), "fails": fails}
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"VALIDATE_ACCEPTANCE_REFS_ALL tasks={len(ids)} fails={len(fails)} out={out_dir}")
    return 0 if not fails else 2


if __name__ == "__main__":
    raise SystemExit(main())
