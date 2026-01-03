#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate ADR/chapter/overlay refs for all Taskmaster tasks.

This script extends the logic of check_tasks_back_references.py to
cover all tasks in tasks_back.json and tasks_gameplay.json so that
we can reproduce the kind of report you saw in Claude Code.

It only reads JSON/ADR/overlay files and prints a summary; it does
not modify any files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ADR_FOR_CH: dict[str, list[str]] = {
    "ADR-0002": ["CH02"],
    "ADR-0019": ["CH02"],
    "ADR-0003": ["CH03"],
    "ADR-0004": ["CH04"],
    "ADR-0006": ["CH05"],
    "ADR-0007": ["CH05", "CH06"],
    "ADR-0005": ["CH07"],
    "ADR-0011": ["CH07", "CH10"],
    "ADR-0008": ["CH10"],
    "ADR-0015": ["CH09"],
    "ADR-0018": ["CH01", "CH06", "CH07"],
    "ADR-0024": ["CH06", "CH07"],
    "ADR-0023": ["CH05"],
}


def load_json_list(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_adr_ids(root: Path) -> set[str]:
    adr_dir = root / "docs" / "adr"
    ids: set[str] = set()
    if not adr_dir.exists():
        return ids
    for f in adr_dir.glob("ADR-*.md"):
        m = re.match(r"ADR-(\d{4})", f.stem)
        if m:
            ids.add(f"ADR-{m.group(1)}")
    return ids


def detect_overlay_prd_dir(root: Path, tasks: list[dict]) -> str | None:
    """Try to infer the overlay PRD directory name from overlay_refs."""
    pat = re.compile(r"^docs/architecture/overlays/([^/]+)/08/", re.IGNORECASE)
    for t in tasks:
        refs = t.get("overlay_refs") or []
        if not isinstance(refs, list):
            refs = [refs]
        for ref in refs:
            m = pat.match(str(ref).replace("\\", "/"))
            if m:
                return m.group(1)
    return None


def collect_overlay_paths(root: Path, overlay_prd_dir: str | None) -> set[str]:
    """Collect all overlay file paths under docs/architecture/overlays/<PRD>/08."""
    if not overlay_prd_dir:
        return set()

    overlay_root = root / "docs" / "architecture" / "overlays" / overlay_prd_dir / "08"
    if not overlay_root.exists():
        return set()

    paths: set[str] = set()
    for p in overlay_root.glob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(root)
        paths.add(str(rel).replace("\\", "/"))
    return paths


def check_tasks(tasks: list[dict], adr_ids: set[str], overlay_paths: set[str], label: str) -> bool:
    total = len(tasks)
    ok_count = 0
    print(f"\n=== Checking {label} ({total} tasks) ===")

    for t in sorted(tasks, key=lambda x: x.get("id", "")):
        tid = t.get("id")
        story_id = t.get("story_id")
        has_error = False

        # ADR refs
        missing_adrs = [a for a in t.get("adr_refs", []) if a not in adr_ids]
        if missing_adrs:
            print(f"- {tid}: missing ADRs {missing_adrs}")
            has_error = True

        # chapter_refs vs ADR_FOR_CH
        expected_ch: set[str] = set()
        for adr in t.get("adr_refs", []):
            expected_ch.update(ADR_FOR_CH.get(adr, []))
        current_ch = set(t.get("chapter_refs", []))
        missing_ch = expected_ch - current_ch
        extra_ch = current_ch - expected_ch
        if missing_ch:
            print(f"- {tid}: missing chapter_refs (from ADR): {sorted(missing_ch)}")
            has_error = True
        if extra_ch:
            print(f"- {tid}: extra chapter_refs (not implied by ADR map): {sorted(extra_ch)}")
            has_error = True

        # overlay_refs required for traceability (tasks -> overlay docs).
        refs = t.get("overlay_refs") or []
        if not isinstance(refs, list):
            refs = [refs]
        refs = [str(p).replace("\\", "/") for p in refs if str(p).strip()]
        if not refs:
            print(f"- {tid}: missing overlay_refs")
            has_error = True
        else:
            missing_overlays = [p for p in refs if p not in overlay_paths]
            if missing_overlays:
                print(f"- {tid}: missing overlays {missing_overlays}")
                has_error = True

        if not has_error:
            ok_count += 1

    print(f"Summary for {label}: {ok_count}/{total} tasks passed")
    return ok_count == total


def run_check_all(root: Path) -> bool:
    """Run full ADR/CH/overlay checks for all task files."""
    adr_ids = collect_adr_ids(root)

    back = load_json_list(root / ".taskmaster" / "tasks" / "tasks_back.json")
    gameplay = load_json_list(root / ".taskmaster" / "tasks" / "tasks_gameplay.json")

    overlay_prd_dir = detect_overlay_prd_dir(root, gameplay) or detect_overlay_prd_dir(root, back)
    if not overlay_prd_dir:
        # Fallback: if there's exactly one overlay folder, use it.
        overlays_root = root / "docs" / "architecture" / "overlays"
        if overlays_root.exists():
            prd_dirs = [p.name for p in overlays_root.iterdir() if p.is_dir()]
            if len(prd_dirs) == 1:
                overlay_prd_dir = prd_dirs[0]

    overlay_paths = collect_overlay_paths(root, overlay_prd_dir)

    print(f"known ADR ids (sample): {sorted(adr_ids)[:10]} ...")
    print(f"overlay prd dir: {overlay_prd_dir}")
    print(f"overlay files (08/*): {sorted(overlay_paths)}")

    ok_back = check_tasks(back, adr_ids, overlay_paths, label="tasks_back.json")
    ok_gameplay = check_tasks(gameplay, adr_ids, overlay_paths, label="tasks_gameplay.json")
    return ok_back and ok_gameplay


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    ok = run_check_all(root)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
