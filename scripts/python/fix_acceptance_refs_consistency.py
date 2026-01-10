#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix deterministic acceptance 'Refs:' consistency rules for view tasks.

This aligns with scripts/python/validate_acceptance_refs.py hard rules:
  1) If acceptance mentions xUnit -> include at least one .cs ref
  2) If acceptance mentions GdUnit4 -> include at least one .gd ref
  3) If acceptance mentions Game.Core -> include at least one Game.Core.Tests/*.cs ref

This script does NOT create test files. It only amends refs (and task-level test_refs)
so that stage=red validation can pass deterministically.

All changes are logged under logs/ci/<date>/fix-acceptance-refs-consistency.json
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any


REFS_RE = re.compile(r"\bRefs\s*:\s*(.+)$", flags=re.IGNORECASE)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _split_refs_blob(blob: str) -> list[str]:
    s = str(blob or "").replace("`", " ").replace(",", " ").replace(";", " ")
    parts = [p.strip().replace("\\", "/") for p in s.split() if p.strip()]
    return parts


def _parse_acceptance_item(text: str) -> tuple[str, list[str]]:
    s = str(text or "").strip()
    m = REFS_RE.search(s)
    if not m:
        return s, []
    refs = _split_refs_blob(m.group(1).strip())
    return s, refs


def _replace_refs(text: str, refs: list[str]) -> str:
    base = _strip_refs(text)
    uniq: list[str] = []
    seen = set()
    for r in refs:
        rr = str(r or "").strip().replace("\\", "/")
        if not rr:
            continue
        if rr in seen:
            continue
        seen.add(rr)
        uniq.append(rr)
    if not uniq:
        return base
    return f"{base} Refs: {' '.join(uniq)}"


def _strip_refs(text: str) -> str:
    m = REFS_RE.search(str(text or ""))
    return str(text or "").strip()[: m.start()].rstrip() if m else str(text or "").strip()


def _has_suffix(refs: list[str], suffix: str) -> bool:
    suf = suffix.lower()
    return any(str(r).lower().endswith(suf) for r in refs)


def _has_prefix(refs: list[str], prefix: str) -> bool:
    pfx = prefix.replace("\\", "/").lower()
    return any(str(r).replace("\\", "/").lower().startswith(pfx) for r in refs)


def _default_cs_ref(task_id: int) -> str:
    return f"Game.Core.Tests/Tasks/Task{task_id}AcceptanceTests.cs"


def _default_gd_ref(task_id: int) -> str:
    return f"Tests.Godot/tests/Tasks/test_task{task_id}_acceptance.gd"


def _ensure_test_refs_list(entry: dict[str, Any]) -> list[str]:
    tr = entry.get("test_refs")
    if isinstance(tr, list):
        return [str(x).strip().replace("\\", "/") for x in tr if str(x).strip()]
    entry["test_refs"] = []
    return []


def _add_to_test_refs(entry: dict[str, Any], refs: list[str]) -> None:
    tr = _ensure_test_refs_list(entry)
    seen = set(tr)
    for r in refs:
        if r not in seen:
            tr.append(r)
            seen.add(r)
    entry["test_refs"] = tr


def _fix_entry(*, entry: dict[str, Any], view: str) -> list[dict[str, Any]]:
    task_id = int(entry.get("taskmaster_id"))
    acceptance = entry.get("acceptance")
    if not isinstance(acceptance, list):
        return []

    changes: list[dict[str, Any]] = []
    new_acceptance: list[str] = []
    for idx, raw in enumerate(acceptance):
        text = str(raw or "").strip()
        full, refs = _parse_acceptance_item(text)
        lower = _strip_refs(full).lower()
        before_refs = list(refs)

        # Rule 1: xUnit -> at least one .cs
        if "xunit" in lower and not _has_suffix(refs, ".cs"):
            refs.append(_default_cs_ref(task_id))

        # Rule 2: GdUnit4 -> at least one .gd
        if "gdunit4" in lower and not _has_suffix(refs, ".gd"):
            refs.append(_default_gd_ref(task_id))

        # Rule 3: Game.Core -> at least one Game.Core.Tests/*.cs
        if "game.core" in lower:
            if not (_has_suffix(refs, ".cs") and _has_prefix(refs, "Game.Core.Tests/")):
                refs.append(_default_cs_ref(task_id))

        # If still empty, add a deterministic default so every acceptance item is traceable.
        if not refs:
            prefer_gd = str(view).strip().lower() == "gameplay"
            refs.append(_default_gd_ref(task_id) if prefer_gd else _default_cs_ref(task_id))

        updated_text = _replace_refs(full, refs) if refs else full
        new_acceptance.append(updated_text)

        if before_refs != refs:
            changes.append(
                {
                    "taskmaster_id": task_id,
                    "acceptance_index": idx,
                    "before_refs": before_refs,
                    "after_refs": refs,
                }
            )
            _add_to_test_refs(entry, refs)

    if changes:
        entry["acceptance"] = new_acceptance
    return changes


def main() -> int:
    root = _repo_root()
    back_path = root / ".taskmaster" / "tasks" / "tasks_back.json"
    gameplay_path = root / ".taskmaster" / "tasks" / "tasks_gameplay.json"
    back = _load_json(back_path)
    gameplay = _load_json(gameplay_path)

    if not isinstance(back, list) or not isinstance(gameplay, list):
        raise SystemExit("Expected tasks_back.json and tasks_gameplay.json to be JSON arrays.")

    audit: dict[str, Any] = {
        "date": _dt.date.today().isoformat(),
        "changes": {"tasks_back": [], "tasks_gameplay": []},
    }

    for entry in back:
        if isinstance(entry, dict) and "taskmaster_id" in entry:
            audit["changes"]["tasks_back"].extend(_fix_entry(entry=entry, view="back"))

    for entry in gameplay:
        if isinstance(entry, dict) and "taskmaster_id" in entry:
            audit["changes"]["tasks_gameplay"].extend(_fix_entry(entry=entry, view="gameplay"))

    _write_json(back_path, back)
    _write_json(gameplay_path, gameplay)

    out_dir = root / "logs" / "ci" / audit["date"]
    out_path = out_dir / "fix-acceptance-refs-consistency.json"
    _write_json(out_path, audit)

    changed = len(audit["changes"]["tasks_back"]) + len(audit["changes"]["tasks_gameplay"])
    print(f"FIX_ACCEPTANCE_REFS_CONSISTENCY changed_items={changed} out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
