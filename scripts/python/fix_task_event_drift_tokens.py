#!/usr/bin/env python3
"""
Fix drifted event-like tokens in TaskMaster task text fields.

Why:
  scripts/python/check_task_event_drift.py is a hard gate in ci_pipeline.py.
  It blocks legacy/non-SSoT event names such as "BattleWon" / "OnTurnStart".
  We replace those exact tokens with CloudEvents-style SSoT event types
  (ADR-0004 naming: core.*.*).

Design:
  - Minimal-diff: operate on raw file text and only replace exact token matches
    with identifier-boundary regex, preserving original JSON formatting/order.
  - UTF-8 IO with LF newlines.
  - Writes an audit JSON to logs/ci/<YYYY-MM-DD>/task-semantic/fix-task-event-drift.json

Usage:
  py -3 scripts/python/fix_task_event_drift_tokens.py --apply
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


TOKEN_REPLACEMENTS: list[tuple[str, str]] = [
    ("BattleWon", "core.rouge.battle.won"),
    ("BattleLost", "core.rouge.battle.lost"),
    ("BattleStart", "core.rouge.battle.started"),
    ("BattleEnd", "core.rouge.battle.ended"),
    ("PlayerTurnStart", "core.rouge.turn.player.started"),
    ("PlayerTurnEnd", "core.rouge.turn.player.ended"),
    # These are settlement hooks, not UI animation events; keep them descriptive but non-legacy.
    ("OnTurnStart", "turn_start_settlement"),
    ("OnTurnEnd", "turn_end_settlement"),
    ("UnitDamaged", "core.rouge.combat.damage.applied"),
    ("StatusApplied", "core.rouge.status.applied"),
    ("NodeEntered", "core.rouge.run.node.entered"),
]


def compile_token(token: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])")


def replace_all(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    out = text
    for src, dst in TOKEN_REPLACEMENTS:
        pat = compile_token(src)
        out, n = pat.subn(dst, out)
        if n:
            counts[src] = n
    return out, counts


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes back to files.")
    args = ap.parse_args()

    root = repo_root()
    date = dt.date.today().strftime("%Y-%m-%d")
    out_dir = root / "logs" / "ci" / date / "task-semantic"
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_path = out_dir / "fix-task-event-drift.json"

    targets = [
        root / ".taskmaster" / "tasks" / "tasks.json",
        root / ".taskmaster" / "tasks" / "tasks_gameplay.json",
    ]

    audit: dict[str, object] = {
        "date": date,
        "apply": bool(args.apply),
        "replacements": [{"from": a, "to": b} for a, b in TOKEN_REPLACEMENTS],
        "files": [],
        "status": "ok",
    }

    any_changes = False
    for path in targets:
        original = path.read_text(encoding="utf-8")
        updated, counts = replace_all(original)
        changed = updated != original
        any_changes = any_changes or changed
        audit["files"].append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "changed": changed,
                "counts": counts,
            }
        )
        if changed and args.apply:
            write_text(path, updated)

    if any_changes and not args.apply:
        audit["status"] = "needs_apply"
    write_text(audit_path, json.dumps(audit, ensure_ascii=False, indent=2) + "\n")

    print(f"FIX_TASK_EVENT_DRIFT status={audit['status']} out={audit_path}")
    return 0 if audit["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())

