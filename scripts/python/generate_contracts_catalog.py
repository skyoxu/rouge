#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contracts catalog generator (code inventory).

This script inventories *code contracts* under Game.Core/Contracts/** and writes
human-friendly + machine-readable artifacts under logs/**.

It is intentionally NOT a gate. It is a compare/reference utility to:
  - browse current event types and DTOs quickly
  - support later overlay backfill (after contracts are finalized)
  - support reviews without treating docs/overlays as SSoT

Outputs (default):
  logs/ci/<YYYY-MM-DD>/contracts-catalog/contracts_inventory.json
  logs/ci/<YYYY-MM-DD>/contracts-catalog/catalog.md
  logs/ci/<YYYY-MM-DD>/contracts-catalog/summary.log
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


EVENT_TYPE_CONST_RE = re.compile(r'public\s+const\s+string\s+EventType\s*=\s*"([^"]+)"\s*;')
NAMESPACE_FILE_RE = re.compile(r"^\s*namespace\s+([A-Za-z0-9_.]+)\s*;\s*$", re.MULTILINE)
NAMESPACE_BLOCK_RE = re.compile(r"^\s*namespace\s+([A-Za-z0-9_.]+)\s*\{\s*$", re.MULTILINE)
PUBLIC_TYPE_RE = re.compile(
    r"\bpublic\s+(?:sealed\s+)?(?:partial\s+)?(record|class|enum|interface)\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)


def read_text_utf8_sig(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig", errors="replace")


def ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def detect_namespace(text: str) -> str:
    m = NAMESPACE_FILE_RE.search(text)
    if m:
        return m.group(1)
    m = NAMESPACE_BLOCK_RE.search(text)
    if m:
        return m.group(1)
    return ""


def first_public_type(text: str) -> Optional[dict[str, str]]:
    m = PUBLIC_TYPE_RE.search(text)
    if not m:
        return None
    return {"kind": m.group(1), "name": m.group(2)}


def event_type_value(text: str) -> Optional[str]:
    m = EVENT_TYPE_CONST_RE.search(text)
    return m.group(1) if m else None


def rel_posix(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def inventory_contracts(repo_root: Path, contracts_root: Path) -> dict[str, Any]:
    cs_files = sorted(contracts_root.rglob("*.cs"))

    events: list[dict[str, Any]] = []
    dtos: list[dict[str, Any]] = []
    interfaces: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []

    event_types_seen: dict[str, str] = {}
    duplicates: list[dict[str, Any]] = []

    for cs in cs_files:
        text = read_text_utf8_sig(cs)
        ns = detect_namespace(text)
        first_type = first_public_type(text) or {"kind": "", "name": cs.stem}
        evt = event_type_value(text)

        item = {
            "path": rel_posix(repo_root, cs),
            "namespace": ns,
            "type_kind": first_type["kind"],
            "type_name": first_type["name"],
        }

        if evt:
            item["event_type"] = evt
            events.append(item)
            if evt in event_types_seen:
                duplicates.append({"event_type": evt, "first": event_types_seen[evt], "second": item["path"]})
            else:
                event_types_seen[evt] = item["path"]
            continue

        if first_type["kind"] == "interface":
            interfaces.append(item)
            continue

        if first_type["kind"] in {"record", "class", "enum"}:
            dtos.append(item)
            continue

        unknown.append(item)

    events_sorted = sorted(events, key=lambda x: (x.get("event_type", ""), x.get("path", "")))
    dtos_sorted = sorted(dtos, key=lambda x: (x.get("namespace", ""), x.get("type_name", ""), x.get("path", "")))
    interfaces_sorted = sorted(interfaces, key=lambda x: (x.get("namespace", ""), x.get("type_name", ""), x.get("path", "")))

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "contracts_root": rel_posix(repo_root, contracts_root),
        "totals": {
            "cs_files": len(cs_files),
            "events": len(events_sorted),
            "dtos": len(dtos_sorted),
            "interfaces": len(interfaces_sorted),
            "unknown": len(unknown),
            "duplicate_event_types": len(duplicates),
        },
        "events": events_sorted,
        "dtos": dtos_sorted,
        "interfaces": interfaces_sorted,
        "unknown": unknown,
        "duplicate_event_types": duplicates,
    }


def render_catalog_md(inv: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Contracts Catalog (Code Inventory)")
    lines.append("")
    lines.append(f"- Generated: {inv['generated_at']}")
    lines.append(f"- Root: `{inv['contracts_root']}`")
    lines.append("")
    totals = inv["totals"]
    lines.append("## Totals")
    lines.append(f"- cs_files: {totals['cs_files']}")
    lines.append(f"- events: {totals['events']}")
    lines.append(f"- dtos: {totals['dtos']}")
    lines.append(f"- interfaces: {totals['interfaces']}")
    lines.append(f"- duplicate_event_types: {totals['duplicate_event_types']}")
    lines.append("")

    lines.append("## Domain Events")
    if not inv["events"]:
        lines.append("- (none)")
    else:
        for e in inv["events"]:
            lines.append(f"- `{e['event_type']}` -> `{e['path']}`")
    lines.append("")

    lines.append("## DTO / Value Types")
    if not inv["dtos"]:
        lines.append("- (none)")
    else:
        for d in inv["dtos"]:
            kind = d.get("type_kind") or "type"
            lines.append(f"- `{d['type_name']}` ({kind}) -> `{d['path']}`")
    lines.append("")

    lines.append("## Interfaces")
    if not inv["interfaces"]:
        lines.append("- (none)")
    else:
        for it in inv["interfaces"]:
            lines.append(f"- `{it['type_name']}` -> `{it['path']}`")
    lines.append("")

    if inv.get("duplicate_event_types"):
        lines.append("## Duplicate EventType (Warning)")
        for dup in inv["duplicate_event_types"]:
            lines.append(f"- `{dup['event_type']}`: `{dup['first']}` vs `{dup['second']}`")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contracts-root", default="Game.Core/Contracts", help="Contracts root directory (default: Game.Core/Contracts)")
    parser.add_argument("--out-dir", default="", help="Optional output directory (default: logs/ci/<date>/contracts-catalog)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    contracts_root = (repo_root / args.contracts_root).resolve()
    if not contracts_root.exists():
        raise SystemExit(f"contracts root not found: {contracts_root}")

    date = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(args.out_dir) if args.out_dir else (repo_root / "logs" / "ci" / date / "contracts-catalog")
    ensure_out_dir(out_dir)

    inv = inventory_contracts(repo_root, contracts_root)
    write_json(out_dir / "contracts_inventory.json", inv)
    write_text(out_dir / "catalog.md", render_catalog_md(inv))
    write_text(
        out_dir / "summary.log",
        f"CONTRACTS_CATALOG_DONE events={inv['totals']['events']} dtos={inv['totals']['dtos']} interfaces={inv['totals']['interfaces']} out={out_dir.as_posix()}\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

