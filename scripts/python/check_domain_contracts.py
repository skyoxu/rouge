#!/usr/bin/env python3
"""
Optional, domain-agnostic contracts consistency checks (deterministic).

This template repo keeps domain rules minimal to avoid coupling, but still
benefits from a stop-loss validator for obvious event contract invariants.

Checks (for Game.Core/Contracts/**/*.cs by default):
  - No Godot dependency leaks (using Godot / Godot. references)
  - If a file defines `public const string EventType = "...";`:
      - Value must be a lowercase dot-separated type: a.b.c (>= 3 segments)
      - Must match any `Domain event: ...` doc comment if present
  - EventType values must be unique across the contracts tree

Outputs:
  - JSON printed to stdout (CI-friendly).
  - Optional --out to also write JSON to a file under logs/ci/.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


EVENT_TYPE_RE = re.compile(r'public\s+const\s+string\s+EventType\s*=\s*"([^"]+)"\s*;')
DOMAIN_EVENT_DOC_RE = re.compile(r"^\s*///\s*Domain\s+event\s*:\s*([A-Za-z0-9_.-]+)\s*$", re.MULTILINE)
GODOT_USING_RE = re.compile(r"^\s*using\s+Godot\s*;\s*$", re.MULTILINE)
GODOT_NAMESPACE_RE = re.compile(r"\bGodot\.")
EVENT_TYPE_FORMAT_RE = re.compile(r"^[a-z0-9]+(?:\.[a-z0-9]+){2,}$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def to_posix(path: Path) -> str:
    return str(path).replace("\\", "/")


def main() -> int:
    ap = argparse.ArgumentParser(description="Optional domain contract consistency checks (deterministic).")
    ap.add_argument("--root", default="Game.Core/Contracts", help="Contracts root directory (repo-relative).")
    ap.add_argument("--out", default=None, help="Optional JSON output path (recommended under logs/ci/...).")
    args = ap.parse_args()

    root = repo_root()
    contracts_root = Path(args.root)
    if not contracts_root.is_absolute():
        contracts_root = (root / contracts_root).resolve()

    report: dict[str, Any] = {
        "status": "fail",
        "contracts_root": to_posix(contracts_root.relative_to(root)) if contracts_root.exists() else to_posix(contracts_root),
        "files_scanned": 0,
        "event_types": [],
        "errors": [],
        "warnings": [],
    }

    if not contracts_root.exists():
        report["errors"].append("contracts_root_missing")
        payload = json.dumps(report, ensure_ascii=False, indent=2)
        print(payload)
        if args.out:
            out_path = Path(args.out)
            if not out_path.is_absolute():
                out_path = (root / out_path).resolve()
            write_json(out_path, report)
        return 1

    seen_types: dict[str, list[str]] = {}

    for cs_file in sorted(contracts_root.rglob("*.cs")):
        if "__pycache__" in cs_file.parts:
            continue
        report["files_scanned"] += 1
        rel = to_posix(cs_file.relative_to(root))
        text = cs_file.read_text(encoding="utf-8", errors="ignore")

        if GODOT_USING_RE.search(text) or GODOT_NAMESPACE_RE.search(text):
            report["errors"].append({"file": rel, "error": "godot_dependency_leak"})

        m = EVENT_TYPE_RE.search(text)
        if not m:
            continue
        evt = str(m.group(1) or "").strip()
        doc_m = DOMAIN_EVENT_DOC_RE.search(text)
        doc_evt = str(doc_m.group(1)).strip() if doc_m else None

        entry = {"file": rel, "event_type": evt, "doc_event": doc_evt}
        report["event_types"].append(entry)

        if not EVENT_TYPE_FORMAT_RE.match(evt):
            report["errors"].append({"file": rel, "error": "invalid_event_type_format", "event_type": evt})

        if doc_evt and doc_evt != evt:
            report["errors"].append({"file": rel, "error": "doc_event_mismatch", "event_type": evt, "doc_event": doc_evt})

        seen_types.setdefault(evt, []).append(rel)

    for evt, files in sorted(seen_types.items()):
        if len(files) > 1:
            report["errors"].append({"error": "duplicate_event_type", "event_type": evt, "files": files})

    report["status"] = "ok" if not report["errors"] else "fail"

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = (root / out_path).resolve()
        write_json(out_path, report)

    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

