#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill Task Master context fields in `.taskmaster/tasks/tasks.json` from SSoT view files.

Why:
- `.taskmaster/tasks/tasks_back.json` and `.taskmaster/tasks/tasks_gameplay.json` are the SSoT for
  ADR/CH/Overlay references via: adr_refs / chapter_refs / overlay_refs.
- `scripts/sc/sc-acceptance-check` and `scripts/sc/analyze` expect the Task Master view file
  (`tasks.json`) to provide:
    - adrRefs: string[]
    - archRefs: string[]
    - overlay: string (a single primary overlay file path)

Policy:
- Never uses network.
- UTF-8 read/write; normalizes paths to forward slashes.
- Does NOT edit the NG/GM view files; only updates tasks.json.
- Conservative merge: only fills missing/empty fields unless --overwrite is set.

Usage (Windows):
  py -3 scripts/python/backfill_taskmaster_context_fields.py --write
  py -3 scripts/python/backfill_taskmaster_context_fields.py --dry-run
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


def today_str() -> str:
    return dt.date.today().strftime("%Y-%m-%d")


def ci_out_dir(name: str) -> Path:
    out = repo_root() / "logs" / "ci" / today_str() / name
    out.mkdir(parents=True, exist_ok=True)
    return out


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def normalize_path(p: str) -> str:
    return str(p or "").replace("\\", "/").strip()


def normalize_str_list(v: Any) -> list[str]:
    if not isinstance(v, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for x in v:
        s = str(x).strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


OVERLAYS_LINE_RE = re.compile(r"(?im)^\s*Overlays\s*:\s*(.+?)\s*$", re.MULTILINE)


def parse_overlay_refs_from_details(details: Any) -> list[str]:
    text = str(details or "")
    m = OVERLAYS_LINE_RE.search(text)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(";")]
    return [normalize_path(p) for p in parts if normalize_path(p)]


def choose_primary_overlay(
    overlay_refs: list[str],
    *,
    kind: str,
) -> str:
    """
    kind:
      - "gm": gameplay feature-slice task
      - "ng": crosscutting/backbone task
      - "unknown": fallback
    """

    refs = [normalize_path(x) for x in overlay_refs if normalize_path(x)]
    if not refs:
        return ""

    def by_name(name: str) -> str | None:
        for r in refs:
            if r.rsplit("/", 1)[-1] == name:
                return r
        return None

    if kind == "gm":
        preferred = [
            "08-Feature-Slice-Minimum-Playable-Loop.md",
            "_index.md",
            "ACCEPTANCE_CHECKLIST.md",
        ]
        for name in preferred:
            hit = by_name(name)
            if hit:
                return hit
        return refs[0]

    if kind == "ng":
        preferred = [
            "ACCEPTANCE_CHECKLIST.md",
        ]
        for name in preferred:
            hit = by_name(name)
            if hit:
                return hit
        for r in refs:
            if r.rsplit("/", 1)[-1].startswith("08-Contracts-"):
                return r
        return refs[0]

    # unknown
    for name in ("ACCEPTANCE_CHECKLIST.md", "08-Feature-Slice-Minimum-Playable-Loop.md", "_index.md"):
        hit = by_name(name)
        if hit:
            return hit
    return refs[0]


def index_view_by_taskmaster_id(view_tasks: list[dict[str, Any]], *, kind: str, source: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for t in view_tasks:
        if not isinstance(t, dict):
            continue
        tm_id = t.get("taskmaster_id")
        if tm_id is None:
            continue
        tm_key = str(tm_id).strip()
        if not tm_key:
            continue
        out[tm_key] = {
            "kind": kind,
            "source": source,
            "task": t,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill tasks.json adrRefs/archRefs/overlay from view SSoT files.")
    ap.add_argument("--tasks-json", default=".taskmaster/tasks/tasks.json")
    ap.add_argument("--tasks-back", default=".taskmaster/tasks/tasks_back.json")
    ap.add_argument("--tasks-gameplay", default=".taskmaster/tasks/tasks_gameplay.json")
    ap.add_argument("--write", action="store_true", help="Write changes to tasks.json (default: dry run).")
    ap.add_argument("--dry-run", action="store_true", help="Alias for default behavior (no write).")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite non-empty fields in tasks.json (dangerous).")
    args = ap.parse_args()

    root = repo_root()
    out_dir = ci_out_dir("taskmaster-rouge")

    tasks_json_path = root / str(args.tasks_json)
    back_path = root / str(args.tasks_back)
    gameplay_path = root / str(args.tasks_gameplay)

    report: dict[str, Any] = {
        "status": "fail",
        "write": bool(args.write) and not bool(args.dry_run),
        "overwrite": bool(args.overwrite),
        "paths": {
            "tasks_json": normalize_path(tasks_json_path.relative_to(root)),
            "tasks_back": normalize_path(back_path.relative_to(root)),
            "tasks_gameplay": normalize_path(gameplay_path.relative_to(root)),
        },
        "summary": {},
        "changes": [],
        "errors": [],
    }

    if not tasks_json_path.exists():
        report["errors"].append(f"missing_tasks_json:{report['paths']['tasks_json']}")
        write_json(out_dir / "backfill_taskmaster_context_fields.json", report)
        print("BACKFILL_TASKMASTER_CONTEXT status=fail reason=missing_tasks_json")
        return 1

    data = read_json(tasks_json_path)
    if not isinstance(data, dict) or not isinstance(data.get("master"), dict):
        report["errors"].append("invalid_tasks_json_schema: expected {master:{tasks:[...]}}")
        write_json(out_dir / "backfill_taskmaster_context_fields.json", report)
        print("BACKFILL_TASKMASTER_CONTEXT status=fail reason=invalid_tasks_json_schema")
        return 1

    master = data["master"]
    tasks = master.get("tasks")
    if not isinstance(tasks, list):
        report["errors"].append("invalid_tasks_json_schema: master.tasks is not a list")
        write_json(out_dir / "backfill_taskmaster_context_fields.json", report)
        print("BACKFILL_TASKMASTER_CONTEXT status=fail reason=invalid_tasks_json_schema")
        return 1

    back_view = read_json(back_path) if back_path.exists() else []
    gameplay_view = read_json(gameplay_path) if gameplay_path.exists() else []
    if not isinstance(back_view, list):
        back_view = []
    if not isinstance(gameplay_view, list):
        gameplay_view = []

    idx: dict[str, dict[str, Any]] = {}
    idx.update(index_view_by_taskmaster_id(back_view, kind="ng", source=normalize_path(back_path.relative_to(root))))
    idx.update(index_view_by_taskmaster_id(gameplay_view, kind="gm", source=normalize_path(gameplay_path.relative_to(root))))

    scanned = 0
    changed = 0
    missing_view = 0
    missing_overlays = 0
    missing_overlay_on_disk = 0

    for t in tasks:
        if not isinstance(t, dict):
            continue
        scanned += 1
        tm_id = str(t.get("id") or "").strip()
        if not tm_id:
            continue

        view_entry = idx.get(tm_id)
        kind = "unknown"
        src_path = None
        view_task: dict[str, Any] | None = None
        if view_entry:
            kind = str(view_entry.get("kind") or "unknown")
            src_path = str(view_entry.get("source") or "")
            view_task = view_entry.get("task") if isinstance(view_entry.get("task"), dict) else None
        else:
            missing_view += 1

        # Determine desired values.
        desired_adr = normalize_str_list((view_task or {}).get("adr_refs")) if view_task else []
        desired_arch = normalize_str_list((view_task or {}).get("chapter_refs")) if view_task else []
        desired_overlay_refs = normalize_str_list((view_task or {}).get("overlay_refs")) if view_task else []

        if not desired_overlay_refs:
            # Fallback to details "Overlays:" line if present.
            desired_overlay_refs = parse_overlay_refs_from_details(t.get("details"))

        if not desired_overlay_refs:
            missing_overlays += 1

        desired_overlay = choose_primary_overlay(desired_overlay_refs, kind=kind) if desired_overlay_refs else ""

        # Apply changes (conservative unless --overwrite).
        before = {
            "adrRefs": list(t.get("adrRefs") or []),
            "archRefs": list(t.get("archRefs") or []),
            "overlay": str(t.get("overlay") or ""),
        }

        def should_set_list(key: str, new_list: list[str]) -> bool:
            if args.overwrite:
                return True
            cur = t.get(key)
            return not (isinstance(cur, list) and any(str(x).strip() for x in cur))

        def should_set_str(key: str, new_val: str) -> bool:
            if args.overwrite:
                return True
            cur = str(t.get(key) or "").strip()
            return cur == ""

        did = False
        if desired_adr and should_set_list("adrRefs", desired_adr):
            t["adrRefs"] = desired_adr
            did = True
        if desired_arch and should_set_list("archRefs", desired_arch):
            t["archRefs"] = desired_arch
            did = True
        if desired_overlay and should_set_str("overlay", desired_overlay):
            t["overlay"] = desired_overlay
            did = True

        overlay_ok = True
        if str(t.get("overlay") or "").strip():
            overlay_p = root / normalize_path(str(t.get("overlay")))
            if not overlay_p.exists():
                overlay_ok = False
                missing_overlay_on_disk += 1

        if did:
            changed += 1
            report["changes"].append(
                {
                    "task_id": tm_id,
                    "title": t.get("title"),
                    "kind": kind,
                    "source": src_path,
                    "before": before,
                    "after": {
                        "adrRefs": list(t.get("adrRefs") or []),
                        "archRefs": list(t.get("archRefs") or []),
                        "overlay": str(t.get("overlay") or ""),
                    },
                    "overlay_ok": overlay_ok,
                }
            )

    report["summary"] = {
        "tasks_scanned": scanned,
        "tasks_changed": changed,
        "missing_view_entries": missing_view,
        "tasks_missing_overlay_refs": missing_overlays,
        "tasks_overlay_path_missing_on_disk": missing_overlay_on_disk,
    }

    # Always write audit report first.
    write_json(out_dir / "backfill_taskmaster_context_fields.json", report)

    if bool(args.write) and not bool(args.dry_run):
        write_json(tasks_json_path, data)

    report["status"] = "ok" if missing_overlay_on_disk == 0 else "warn"
    write_json(out_dir / "backfill_taskmaster_context_fields.json", report)

    print(
        "BACKFILL_TASKMASTER_CONTEXT "
        f"status={report['status']} scanned={scanned} changed={changed} "
        f"missing_view={missing_view} missing_overlay_refs={missing_overlays} overlay_missing_on_disk={missing_overlay_on_disk} "
        f"write={'yes' if (args.write and not args.dry_run) else 'no'}"
    )
    return 0 if report["status"] in {"ok", "warn"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

