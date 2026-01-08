#!/usr/bin/env python3
"""Validate contractRefs in TaskMaster view files.

In this repo, `contractRefs` is a *view-layer* field (SSoT) stored in:
- .taskmaster/tasks/tasks_back.json
- .taskmaster/tasks/tasks_gameplay.json

Rules:
- contractRefs is a list of domain event type strings (EventType), e.g. `core.run.started`.
- Only allow prefixes: `core.` / `ui.menu.` / `screen.` (ADR-0004 baseline).
- Every referenced event type must exist as a `public const string EventType = "..."` constant
  in `Game.Core/Contracts/**/*.cs`.

Outputs:
- Writes a JSON report under logs/ci/<YYYY-MM-DD>/task-semantic/ by default.
- Prints a short ASCII summary for log capture.

Exit codes:
- 0: ok
- 1: fail (invalid/missing contractRefs)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Iterable


EVENT_TYPE_RE = re.compile(r'public\s+const\s+string\s+EventType\s*=\s*"([^"]+)"\s*;')
EVENT_TYPE_FORMAT_RE = re.compile(r"^[a-z0-9]+(?:\.[a-z0-9]+){2,}$")
ALLOWED_PREFIXES = ("core.", "ui.menu.", "screen.")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def to_posix(path: Path) -> str:
    return str(path).replace("\\", "/")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_tasks(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        return [t for t in obj if isinstance(t, dict)]
    if isinstance(obj, dict) and isinstance(obj.get("tasks"), list):
        return [t for t in obj["tasks"] if isinstance(t, dict)]
    raise ValueError("task view json must be a list (or an object with a 'tasks' array)")


def normalize_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for v in value:
        if not isinstance(v, str):
            continue
        s = v.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def scan_contract_event_types(contracts_root: Path) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    root = repo_root()
    if not contracts_root.exists():
        return mapping
    for cs_file in sorted(contracts_root.rglob("*.cs")):
        rel = to_posix(cs_file.relative_to(root))
        text = cs_file.read_text(encoding="utf-8", errors="ignore")
        for m in EVENT_TYPE_RE.finditer(text):
            evt = str(m.group(1) or "").strip()
            if not evt:
                continue
            mapping.setdefault(evt, []).append(rel)
    return mapping


def iter_view_refs(view_name: str, tasks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for t in tasks:
        task_id = t.get("id")
        refs = normalize_str_list(t.get("contractRefs"))
        rows.append(
            {
                "view": view_name,
                "id": str(task_id) if task_id is not None else None,
                "taskmaster_id": t.get("taskmaster_id"),
                "contractRefs": refs,
            }
        )
    return rows


def default_out_path(root: Path) -> Path:
    date = dt.date.today().strftime("%Y-%m-%d")
    return root / "logs" / "ci" / date / "task-semantic" / "task-contract-refs.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate contractRefs in tasks_back/tasks_gameplay against Contracts EventType constants.")
    ap.add_argument("--tasks-back", default=".taskmaster/tasks/tasks_back.json")
    ap.add_argument("--tasks-gameplay", default=".taskmaster/tasks/tasks_gameplay.json")
    ap.add_argument("--contracts-root", default="Game.Core/Contracts")
    ap.add_argument("--out", default=None, help="Output JSON path (default: logs/ci/<date>/task-semantic/task-contract-refs.json)")
    args = ap.parse_args()

    root = repo_root()
    tasks_back_path = (root / args.tasks_back).resolve() if not Path(args.tasks_back).is_absolute() else Path(args.tasks_back).resolve()
    tasks_gameplay_path = (root / args.tasks_gameplay).resolve() if not Path(args.tasks_gameplay).is_absolute() else Path(args.tasks_gameplay).resolve()
    contracts_root = (root / args.contracts_root).resolve() if not Path(args.contracts_root).is_absolute() else Path(args.contracts_root).resolve()
    out_path = (root / args.out).resolve() if (args.out and not Path(args.out).is_absolute()) else (Path(args.out).resolve() if args.out else default_out_path(root))

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if not tasks_back_path.exists():
        errors.append({"error": "missing_tasks_back", "path": to_posix(tasks_back_path)})
    if not tasks_gameplay_path.exists():
        errors.append({"error": "missing_tasks_gameplay", "path": to_posix(tasks_gameplay_path)})
    if not contracts_root.exists():
        errors.append({"error": "missing_contracts_root", "path": to_posix(contracts_root)})

    views: list[dict[str, Any]] = []
    unique_refs: set[str] = set()

    if tasks_back_path.exists():
        back_tasks = iter_tasks(load_json(tasks_back_path))
        views.append({"name": "tasks_back", "path": to_posix(tasks_back_path.relative_to(root)), "tasks": iter_view_refs("tasks_back", back_tasks)})
        for t in back_tasks:
            unique_refs.update(normalize_str_list(t.get("contractRefs")))
    if tasks_gameplay_path.exists():
        gp_tasks = iter_tasks(load_json(tasks_gameplay_path))
        views.append({"name": "tasks_gameplay", "path": to_posix(tasks_gameplay_path.relative_to(root)), "tasks": iter_view_refs("tasks_gameplay", gp_tasks)})
        for t in gp_tasks:
            unique_refs.update(normalize_str_list(t.get("contractRefs")))

    contracts_map = scan_contract_event_types(contracts_root) if contracts_root.exists() else {}

    invalid_format: list[str] = []
    invalid_prefix: list[str] = []
    missing: list[str] = []

    for ref in sorted(unique_refs):
        if not EVENT_TYPE_FORMAT_RE.match(ref):
            invalid_format.append(ref)
            continue
        if not ref.startswith(ALLOWED_PREFIXES):
            invalid_prefix.append(ref)
            continue
        if ref not in contracts_map:
            missing.append(ref)

    if invalid_format:
        errors.append({"error": "invalid_event_type_format", "items": invalid_format})
    if invalid_prefix:
        errors.append({"error": "invalid_event_type_prefix", "allowed_prefixes": list(ALLOWED_PREFIXES), "items": invalid_prefix})
    if missing:
        errors.append({"error": "missing_event_types_on_disk", "items": missing})

    report: dict[str, Any] = {
        "status": "ok" if not errors else "fail",
        "date": dt.date.today().strftime("%Y-%m-%d"),
        "allowed_prefixes": list(ALLOWED_PREFIXES),
        "paths": {
            "tasks_back": to_posix(tasks_back_path.relative_to(root)) if tasks_back_path.exists() else to_posix(tasks_back_path),
            "tasks_gameplay": to_posix(tasks_gameplay_path.relative_to(root)) if tasks_gameplay_path.exists() else to_posix(tasks_gameplay_path),
            "contracts_root": to_posix(contracts_root.relative_to(root)) if contracts_root.exists() else to_posix(contracts_root),
        },
        "stats": {
            "views": {
                "tasks_back": len(views[0]["tasks"]) if views else 0,
                "tasks_gameplay": len(views[1]["tasks"]) if len(views) > 1 else 0,
            },
            "unique_contract_refs": len(unique_refs),
            "event_types_on_disk": len(contracts_map),
        },
        "unique_contractRefs": sorted(unique_refs),
        "contracts_index": {"event_type_to_files": contracts_map},
        "errors": errors,
        "warnings": warnings,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(
        f"TASK_CONTRACT_REFS status={report['status']} unique_refs={len(unique_refs)} "
        f"missing={len(missing)} invalid_format={len(invalid_format)} invalid_prefix={len(invalid_prefix)} "
        f"out={to_posix(out_path.relative_to(root))}"
    )
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

