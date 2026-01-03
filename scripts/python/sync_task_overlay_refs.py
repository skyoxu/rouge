#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synchronize overlay_refs in task SSoT files.

Why this exists:
- Task files (.taskmaster/tasks/tasks_back.json, tasks_gameplay.json) are the SSoT for rich metadata.
- We want a deterministic, repo-local way to keep overlay_refs consistent with the current PRD overlay folder.
- This script updates overlay_refs in-place (UTF-8) and prints a small report.

Safety:
- No network access.
- Only reads/writes task JSON files and reads overlay markdown filenames for discovery.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _normalize_path(p: str) -> str:
    return p.replace("\\", "/")


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list at {path}")
    return data


def _write_json_list(path: Path, tasks: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _extract_overlay_prd_from_overlay_refs(tasks: list[dict[str, Any]]) -> str | None:
    pat = re.compile(r"^docs/architecture/overlays/([^/]+)/08/", re.IGNORECASE)
    for t in tasks:
        for ref in t.get("overlay_refs", []) or []:
            m = pat.match(_normalize_path(str(ref)))
            if m:
                return m.group(1)
    return None


def _auto_detect_overlay_prd(root: Path, gameplay_tasks: list[dict[str, Any]]) -> str:
    from_refs = _extract_overlay_prd_from_overlay_refs(gameplay_tasks)
    if from_refs:
        return from_refs

    overlays_root = root / "docs" / "architecture" / "overlays"
    if overlays_root.exists():
        prd_dirs = [p.name for p in overlays_root.iterdir() if p.is_dir()]
        if len(prd_dirs) == 1:
            return prd_dirs[0]

    raise SystemExit(
        "Cannot determine overlay PRD directory. "
        "Pass --overlay-prd (e.g. PRD-rouge-manager)."
    )


def _parse_front_matter_kv(path: Path) -> dict[str, str]:
    """Parse only top-level `Key: Value` pairs in YAML front-matter."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = parts[1]
    result: dict[str, str] = {}
    for raw in fm.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and not line.startswith("-") and not line.startswith(" "):
            k, v = line.split(":", 1)
            result[k.strip()] = v.strip()
    return result


def _collect_overlay_files(root: Path, overlay_prd: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    overlay_08 = root / "docs" / "architecture" / "overlays" / overlay_prd / "08"
    if not overlay_08.exists():
        raise SystemExit(f"Overlay folder not found: {overlay_08}")

    by_name: dict[str, str] = {}
    story_docs: dict[str, list[str]] = {}

    for p in overlay_08.glob("*.md"):
        rel = _normalize_path(str(p.relative_to(root)))
        by_name[p.name] = rel

        fm = _parse_front_matter_kv(p)
        story_id = fm.get("Story-ID")
        if story_id:
            story_docs.setdefault(story_id, []).append(rel)

    return by_name, story_docs


def _ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it in seen:
            continue
        seen.add(it)
        out.append(it)
    return out


def _sync_one_task(
    task: dict[str, Any],
    overlay_by_name: dict[str, str],
    story_docs: dict[str, list[str]],
    include_story_docs_for_ng: bool,
) -> tuple[bool, list[str], list[str]]:
    """Returns: (changed, before, after)."""
    before = [_normalize_path(p) for p in (task.get("overlay_refs") or [])]
    before_set = set(before)

    tid = str(task.get("id", ""))
    labels = set(task.get("labels", []) or [])
    story_id = task.get("story_id")
    is_gm = tid.startswith("GM-")
    is_ng = tid.startswith("NG-")

    # Known overlay docs (by filename).
    idx = overlay_by_name.get("_index.md")
    acc = overlay_by_name.get("ACCEPTANCE_CHECKLIST.md")
    quality = overlay_by_name.get("08-Contracts-Quality-Metrics.md")
    security = overlay_by_name.get("08-Contracts-Security.md")
    allowed_hosts = overlay_by_name.get("08-Contracts-Allowed-External-Hosts.md")
    cloud_event = overlay_by_name.get("08-Contracts-CloudEvent.md")
    cloud_events_core = overlay_by_name.get("08-Contracts-CloudEvents-Core.md")
    run_events = overlay_by_name.get("08-Contracts-Rouge-Run-Events.md")

    required = [idx, acc]
    missing_required = [p for p in required if not p]
    if missing_required:
        raise SystemExit(
            "Missing required overlay docs: _index.md and/or ACCEPTANCE_CHECKLIST.md "
            f"under docs/architecture/overlays/**/08. ({missing_required})"
        )

    desired: set[str] = set(before_set)
    # Policy:
    # - GM (feature slice) tasks: keep the 08 index + acceptance checklist for navigation.
    # - NG (crosscutting/backbone) tasks: do NOT attach the feature-slice index; only attach
    #   contract pages + acceptance checklist.
    if is_gm:
        desired.add(idx)
    desired.add(acc)

    # Story docs: exact Story-ID match (GM tasks), optionally also for NG.
    story_paths = sorted(story_docs.get(str(story_id), [])) if story_id else []
    if is_gm:
        desired.update(story_paths)
    elif include_story_docs_for_ng and is_ng:
        desired.update(story_paths)

    if is_gm:
        for p in [run_events, security, quality]:
            if p:
                desired.add(p)
    elif is_ng:
        if labels & {
            "ci",
            "quality-gates",
            "perf",
            "coverage",
            "observability",
            "release-health",
            "release",
            "build",
            "export",
            "architecture-tests",
            "docs",
        }:
            if quality:
                desired.add(quality)

        if "security" in labels or "audit" in labels or "filesystem" in labels or "process" in labels:
            if security:
                desired.add(security)

        if labels & {"url", "allowlist", "offline-mode"}:
            if allowed_hosts:
                desired.add(allowed_hosts)

        if "contracts" in labels:
            for p in [cloud_event, cloud_events_core]:
                if p:
                    desired.add(p)
            if run_events:
                desired.add(run_events)

        if "signals" in labels:
            if run_events:
                desired.add(run_events)

        # Enforce NG policy: only contract pages + acceptance checklist.
        for p in list(desired):
            name = p.rsplit("/", 1)[-1]
            if name == "ACCEPTANCE_CHECKLIST.md":
                continue
            if name.startswith("08-Contracts-"):
                continue
            desired.discard(p)

    # Canonical ordering: keep it stable and human-scannable.
    after: list[str] = []
    if is_gm and idx in desired:
        after.append(idx)

    # Story docs (if any) right after index.
    for p in story_paths:
        if p in desired:
            after.append(p)

    canonical_names = [
        "08-Contracts-CloudEvent.md",
        "08-Contracts-CloudEvents-Core.md",
        "08-Contracts-Rouge-Run-Events.md",
        "08-Contracts-Allowed-External-Hosts.md",
        "08-Contracts-Security.md",
        "08-Contracts-Quality-Metrics.md",
    ]
    for name in canonical_names:
        p = overlay_by_name.get(name)
        if p and p in desired:
            after.append(p)

    if acc in desired:
        after.append(acc)

    # Preserve any extra overlays not covered by canonical ordering (stable sort).
    extras = sorted(p for p in desired if p not in set(after))
    after.extend(extras)

    after = _ordered_unique(after)
    task["overlay_refs"] = after
    changed = before != after
    return changed, before, after


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync overlay_refs for task SSoT files (UTF-8).")
    parser.add_argument(
        "--overlay-prd",
        type=str,
        default=None,
        help="Overlay directory name under docs/architecture/overlays (e.g. PRD-rouge-manager).",
    )
    parser.add_argument(
        "--tasks-file",
        action="append",
        default=[],
        help="Task JSON file to update (repeatable). Defaults to tasks_back.json + tasks_gameplay.json.",
    )
    parser.add_argument(
        "--include-story-docs-for-ng",
        action="store_true",
        help="Also add Story-ID matched overlay docs for NG tasks (default: off).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write changes to files (default: dry-run).",
    )

    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]

    default_files = [
        root / ".taskmaster" / "tasks" / "tasks_back.json",
        root / ".taskmaster" / "tasks" / "tasks_gameplay.json",
    ]
    task_files = [Path(p) for p in args.tasks_file] if args.tasks_file else default_files
    task_files = [p if p.is_absolute() else (root / p) for p in task_files]

    # Load gameplay first for auto-detection.
    gameplay_path = root / ".taskmaster" / "tasks" / "tasks_gameplay.json"
    gameplay_tasks = _read_json_list(gameplay_path) if gameplay_path.exists() else []

    overlay_prd = args.overlay_prd or _auto_detect_overlay_prd(root, gameplay_tasks)
    overlay_by_name, story_docs = _collect_overlay_files(root, overlay_prd)

    print(f"overlay_prd: {overlay_prd}")
    print(f"overlay_08_files: {len(overlay_by_name)}")
    print(f"story_docs: {len(story_docs)} story-id(s)")
    print(f"mode: {'write' if args.write else 'dry-run'}")

    any_change = False
    for task_file in task_files:
        tasks = _read_json_list(task_file)
        changed_count = 0

        for t in tasks:
            changed, before, after = _sync_one_task(
                t,
                overlay_by_name=overlay_by_name,
                story_docs=story_docs,
                include_story_docs_for_ng=args.include_story_docs_for_ng,
            )
            if changed:
                changed_count += 1
                any_change = True
                tid = t.get("id")
                print(f"- {task_file.name}: {tid} overlay_refs {len(before)} -> {len(after)}")

        if args.write and changed_count > 0:
            _write_json_list(task_file, tasks)

        print(f"{task_file.name}: {changed_count}/{len(tasks)} tasks updated")

    if any_change and not args.write:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
