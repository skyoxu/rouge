#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hard gate: ensure EventBus subscriber exceptions are not silently swallowed.

This gate enforces two things:
  1) Static mechanism exists in runtime code to audit subscriber exceptions to
     logs/ci/<date>/security-audit.jsonl (or AUDIT_LOG_ROOT).
  2) Runtime evidence exists for the current run: at least one JSONL line with
     action == "eventbus.handler.exception" and required schema keys:
       {ts, action, reason, target, caller}

This script is intended to run AFTER dotnet tests (which should trigger at least
one subscriber exception in a unit test).

Usage:
  py -3 scripts/python/eventbus_audit_gate.py --out logs/ci/<YYYY-MM-DD>/eventbus-audit-gate/summary.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


ACTION = "eventbus.handler.exception"
AUDIT_FILENAME = "security-audit.jsonl"
REQUIRED_KEYS = ("ts", "action", "reason", "target", "caller")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def static_check(root: Path) -> dict[str, Any]:
    files = [
        root / "Game.Core" / "Services" / "EventBus.cs",
        root / "Game.Godot" / "Adapters" / "EventBusAdapter.cs",
    ]
    findings: list[dict[str, Any]] = []
    ok = True

    for p in files:
        item: dict[str, Any] = {"file": p.relative_to(root).as_posix(), "exists": p.exists()}
        if not p.exists():
            item["ok"] = False
            ok = False
            findings.append(item)
            continue

        text = load_text(p)
        item["mentions_action"] = ACTION in text
        item["mentions_audit_file"] = AUDIT_FILENAME in text
        item["has_required_keys"] = {k: (f"\"{k}\"" in text) for k in REQUIRED_KEYS}
        item["ok"] = item["mentions_action"] and item["mentions_audit_file"] and all(item["has_required_keys"].values())
        ok = ok and item["ok"]
        findings.append(item)

    return {"ok": ok, "files": findings}


def iter_audit_candidates(root: Path, date: str) -> list[Path]:
    ci_root = root / "logs" / "ci" / date
    if not ci_root.exists():
        return []
    # Include nested audit logs (unit tests may write into subfolders).
    cands = sorted(ci_root.rglob(AUDIT_FILENAME))
    return [p for p in cands if p.is_file()]


def validate_jsonl_for_action(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    matched = 0
    schema_ok = 0
    parse_errors = 0
    last_error: str | None = None

    for raw in lines:
        try:
            obj = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            parse_errors += 1
            last_error = str(exc)
            continue
        if not isinstance(obj, dict):
            continue
        if not all(k in obj for k in REQUIRED_KEYS):
            continue
        schema_ok += 1
        if obj.get("action") == ACTION:
            matched += 1

    return {
        "path": path.as_posix(),
        "nonempty_lines": len(lines),
        "parse_errors": parse_errors,
        "last_parse_error": last_error,
        "schema_ok_lines": schema_ok,
        "matched_action_lines": matched,
        "ok": matched > 0,
    }


def runtime_check(root: Path, date: str) -> dict[str, Any]:
    cands = iter_audit_candidates(root, date)
    results = []
    for p in cands:
        results.append(validate_jsonl_for_action(p))
    selected = next((r for r in results if r.get("ok")), None)
    return {"ok": selected is not None, "date": date, "candidates": results, "selected": selected}


def main() -> int:
    ap = argparse.ArgumentParser(description="Hard gate: EventBus handler exception audit presence + runtime evidence.")
    ap.add_argument("--out", required=True, help="Output JSON path (under logs/ci/... recommended).")
    ap.add_argument("--date", default=None, help="Date folder (YYYY-MM-DD). Default: today (UTC).")
    args = ap.parse_args()

    root = repo_root()
    date = args.date or dt.date.today().strftime("%Y-%m-%d")

    report: dict[str, Any] = {
        "ok": False,
        "date": date,
        "static": static_check(root),
        "runtime": runtime_check(root, date),
        "required_keys": list(REQUIRED_KEYS),
        "action": ACTION,
    }
    report["ok"] = bool(report["static"].get("ok") and report["runtime"].get("ok"))

    out_path = Path(args.out)
    write_json(out_path, report)

    status = "ok" if report["ok"] else "fail"
    selected = (report.get("runtime") or {}).get("selected") or {}
    sel_path = selected.get("path") if isinstance(selected, dict) else None
    print(f"EVENTBUS_AUDIT_GATE status={status} date={date} selected={sel_path or 'n/a'} out={out_path.as_posix()}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
