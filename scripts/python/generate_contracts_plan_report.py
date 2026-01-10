#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a contracts plan report from PRD + Overlay + Tasks + existing Contracts.

This script is deterministic (no LLM). It writes audit/report artifacts under logs/ci/**.

What it does:
  - Inventory existing C# contracts under Game.Core/Contracts/**:
      * Domain events: records/classes containing `public const string EventType = "..."`
      * DTO/value types: other public records/enums/classes under Game.Core/Contracts/Rouge/**
      * Interfaces: (currently none under Game.Core/Contracts/**; reported separately)
  - Extract event-type strings referenced by tasks text (acceptance/description/details) and contractRefs.
  - Cross-check:
      * contractRefs -> unknown vs existing EventType
      * acceptance/details mentioned event types -> missing from contractRefs
      * "core.rouge.*" (or other non-canonical prefixes) -> flagged as naming drift vs ADR-0004 / overlay docs
  - Summarize per task (for view tasks in tasks_back/tasks_gameplay):
      * task id, title, layer, adr_refs, chapter_refs, overlay_refs, test_refs
      * existing contractRefs
      * events mentioned in text
      * missing refs, unknown refs, naming drift

Outputs:
  logs/ci/<YYYY-MM-DD>/contracts-plan/
    - contracts_inventory.json
    - tasks_contracts_matrix.json
    - tasks_contracts_matrix.md
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any


EVENT_TYPE_CONST_RE = re.compile(r'EventType\s*=\s*"([^"]+)"')
PUBLIC_TYPE_RE = re.compile(r"\bpublic\s+(?:sealed\s+)?(?:partial\s+)?(record|class|enum|interface)\s+([A-Za-z_][A-Za-z0-9_]*)")
INTERFACE_NAME_RE = re.compile(r"\bI[A-Z][A-Za-z0-9_]*\b")
PASCAL_TOKEN_RE = re.compile(r"\b[A-Z][A-Za-z0-9_]*\b")
EVENT_STRING_RE = re.compile(r"\b(?:core|screen|ui\.menu)\.[a-z0-9_.-]+\b", flags=re.IGNORECASE)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _today_ci_dir(root: Path) -> Path:
    return root / "logs" / "ci" / _dt.date.today().isoformat()


def _inventory_contracts(root: Path) -> dict[str, Any]:
    contracts_root = root / "Game.Core" / "Contracts"
    events: list[dict[str, str]] = []
    types: list[dict[str, str]] = []

    for path in sorted(contracts_root.rglob("*.cs")):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue

        rel = str(path.relative_to(root)).replace("\\", "/")
        event_types = EVENT_TYPE_CONST_RE.findall(text)
        if event_types:
            for ev in event_types:
                # Try to also capture the first public record/class name as the event contract name.
                mname = PUBLIC_TYPE_RE.search(text)
                name = mname.group(2) if mname else ""
                events.append({"eventType": ev.strip(), "name": name, "path": rel})

        for kind, name in PUBLIC_TYPE_RE.findall(text):
            types.append({"kind": kind, "name": name, "path": rel})

    uniq_events: dict[str, dict[str, str]] = {}
    for e in events:
        et = e["eventType"]
        if et not in uniq_events:
            uniq_events[et] = {"eventType": et, "name": e.get("name", ""), "path": e["path"]}

    return {
        "events": [uniq_events[k] for k in sorted(uniq_events.keys())],
        "types": types,
    }


def _inventory_interfaces(root: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    core = root / "Game.Core"
    for base in [core / "Ports", core / "Repositories", core / "Services"]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.cs")):
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            for kind, name in PUBLIC_TYPE_RE.findall(text):
                if kind != "interface":
                    continue
                out.append({"name": name, "path": rel})
    # De-dup by name preserving first path.
    seen: set[str] = set()
    uniq: list[dict[str, str]] = []
    for item in out:
        n = item["name"]
        if n in seen:
            continue
        seen.add(n)
        uniq.append(item)
    return uniq


def _load_overlay_texts(root: Path) -> dict[str, str]:
    base = root / "docs" / "architecture" / "overlays" / "PRD-rouge-manager" / "08"
    out: dict[str, str] = {}
    if not base.exists():
        return out
    for p in sorted(base.glob("*.md")):
        out[str(p.relative_to(root)).replace("\\", "/")] = p.read_text(encoding="utf-8", errors="ignore")
    return out


def _extract_events_from_text(text: str) -> list[str]:
    return sorted(set(m.group(0) for m in EVENT_STRING_RE.finditer(text or "")))


def _detect_naming_drift(events: list[str]) -> list[str]:
    # Flag known drift patterns that are inconsistent with overlay docs in this repo.
    # Example drift: "core.rouge.battle.started" vs "core.battle.started".
    return sorted({e for e in events if e.lower().startswith("core.rouge.")})


def _matrix_for_tasks(root: Path, inventory: dict[str, Any]) -> dict[str, Any]:
    back = _load_json(root / ".taskmaster" / "tasks" / "tasks_back.json")
    gameplay = _load_json(root / ".taskmaster" / "tasks" / "tasks_gameplay.json")
    master = _load_json(root / ".taskmaster" / "tasks" / "tasks.json")

    existing_event_types = {e["eventType"] for e in inventory.get("events", []) if isinstance(e, dict) and e.get("eventType")}
    contract_type_names = {t["name"] for t in inventory.get("types", []) if isinstance(t, dict) and t.get("name")}
    interfaces = _inventory_interfaces(root)
    interface_names = {i["name"] for i in interfaces if i.get("name")}

    overlay_texts = _load_overlay_texts(root)
    overlay_events = sorted(
        set(e for t in overlay_texts.values() for e in _extract_events_from_text(t) if e.startswith(("core.", "screen.", "ui.menu.")))
    )

    tasks: list[dict[str, Any]] = []
    view_tasks = []
    if isinstance(back, list):
        view_tasks.extend([("back", x) for x in back if isinstance(x, dict)])
    if isinstance(gameplay, list):
        view_tasks.extend([("gameplay", x) for x in gameplay if isinstance(x, dict)])

    master_by_id: dict[int, dict[str, Any]] = {}
    for t in ((master.get("master") or {}).get("tasks") or []):
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or "").strip()
        if tid.isdigit():
            master_by_id[int(tid)] = t

    for view_name, entry in view_tasks:
        tid = entry.get("taskmaster_id")
        if tid is None:
            continue
        try:
            tid_i = int(tid)
        except Exception:
            continue

        contract_refs = [str(x).strip() for x in (entry.get("contractRefs") or []) if str(x).strip()]
        text_blob = "\n".join(
            [
                str(entry.get("title") or ""),
                str(entry.get("description") or ""),
                "\n".join([str(x) for x in (entry.get("acceptance") or [])]),
                "\n".join([str(x) for x in (entry.get("test_strategy") or [])]),
                str((master_by_id.get(tid_i) or {}).get("details") or ""),
            ]
        )

        text_events = _extract_events_from_text(text_blob)
        drift = _detect_naming_drift(text_events)

        # DTO/value-type references: only report those that already exist in Contracts.
        tokens = set(PASCAL_TOKEN_RE.findall(text_blob))
        referenced_contract_types = sorted([t for t in tokens if t in contract_type_names])
        referenced_interfaces = sorted([t for t in INTERFACE_NAME_RE.findall(text_blob) if t in interface_names])

        # Missing type candidates (helps answer "do we need new contract files?").
        # Keep it conservative: only a few common suffixes used in tasks/PRDs.
        missing_type_candidates: list[str] = []
        for t in sorted(tokens):
            if t in contract_type_names or t in interface_names:
                continue
            if t in {"Refs", "ADR", "CH", "JSON", "CSV", "HTTP", "HTTPS", "CI", "UI", "ID"}:
                continue
            if t.endswith(("Dto", "DTO", "Request", "Response", "Snapshot", "State", "Config", "Result", "Summary")):
                missing_type_candidates.append(t)

        unknown_contract_refs = sorted([r for r in contract_refs if r not in existing_event_types])
        missing_contract_refs = sorted([e for e in text_events if e in existing_event_types and e not in contract_refs])

        tasks.append(
            {
                "taskmaster_id": tid_i,
                "view": view_name,
                "id": entry.get("id"),
                "title": entry.get("title"),
                "layer": entry.get("layer"),
                "adr_refs": entry.get("adr_refs") or [],
                "chapter_refs": entry.get("chapter_refs") or [],
                "overlay_refs": entry.get("overlay_refs") or [],
                "test_refs": entry.get("test_refs") or [],
                "contractRefs": contract_refs,
                "events_mentioned_in_text": text_events,
                "events_naming_drift": drift,
                "missing_contractRefs_for_text_events": missing_contract_refs,
                "unknown_contractRefs": unknown_contract_refs,
                "referenced_contract_types": referenced_contract_types,
                "referenced_interfaces": referenced_interfaces,
                "missing_type_candidates": missing_type_candidates,
            }
        )

    # Extra: overlay events that are not referenced anywhere in contractRefs (helps spot missing linkage).
    all_contract_refs = sorted({r for t in tasks for r in (t.get("contractRefs") or [])})
    overlay_events_missing_in_any_contractRefs = sorted([e for e in overlay_events if e in existing_event_types and e not in all_contract_refs])

    return {
        "interfaces_inventory": interfaces,
        "overlay_events": overlay_events,
        "overlay_events_missing_in_any_contractRefs": overlay_events_missing_in_any_contractRefs,
        "tasks": sorted(tasks, key=lambda x: (int(x["taskmaster_id"]), str(x["view"]))),
    }


def _render_markdown(inventory: dict[str, Any], matrix: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Contracts Plan Report (Rouge)")
    lines.append("")
    lines.append("## Existing Domain Events (EventType)")
    for e in inventory.get("events", []):
        if not isinstance(e, dict):
            continue
        name = str(e.get("name") or "").strip()
        name_part = f" ({name})" if name else ""
        lines.append(f"- `{e.get('eventType')}`{name_part} — `{e.get('path')}`")
    lines.append("")
    lines.append("## Existing DTO / Value Types (Contracts/Rouge)")
    # Heuristic grouping by the folder segment after Contracts/Rouge.
    by_group: dict[str, list[str]] = {}
    for t in inventory.get("types", []):
        if not isinstance(t, dict):
            continue
        path = str(t.get("path") or "").replace("\\", "/")
        if "Game.Core/Contracts/Rouge/" not in path:
            continue
        kind = str(t.get("kind") or "")
        name = str(t.get("name") or "")
        if kind == "interface":
            continue
        group = "Rouge"
        parts = path.split("Game.Core/Contracts/Rouge/", 1)[1].split("/")
        if len(parts) >= 2:
            group = parts[0]
        by_group.setdefault(group, []).append(f"`{name}` — `{path}`")
    for group in sorted(by_group.keys()):
        lines.append(f"- **{group}**")
        for item in sorted(set(by_group[group])):
            lines.append(f"  - {item}")
    lines.append("")
    lines.append("## Interfaces (Ports/Repositories/Services)")
    if matrix.get("interfaces_inventory"):
        for it in matrix["interfaces_inventory"]:
            lines.append(f"- `{it.get('name')}` — `{it.get('path')}`")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Overlay Event Strings")
    for e in matrix.get("overlay_events", []):
        lines.append(f"- `{e}`")
    lines.append("")
    missing = matrix.get("overlay_events_missing_in_any_contractRefs") or []
    lines.append("## Overlay Events Missing In Any task.contractRefs")
    if missing:
        for e in missing:
            lines.append(f"- `{e}`")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Per-Task Summary (View tasks)")
    lines.append("")
    lines.append("| Task | View | Layer | ContractRefs (events) | Text drift | DTO/Types | Interfaces | Missing/Unknown |")
    lines.append("|---:|---|---|---|---|---|---|---|")
    for t in matrix.get("tasks", []):
        tid = t.get("taskmaster_id")
        view = t.get("view")
        layer = str(t.get("layer") or "")
        cr = ", ".join(f"`{x}`" for x in (t.get("contractRefs") or [])) or "(empty)"
        drift = ", ".join(f"`{x}`" for x in (t.get("events_naming_drift") or [])) or ""
        dto = ", ".join(f"`{x}`" for x in (t.get("referenced_contract_types") or [])) or ""
        ifaces = ", ".join(f"`{x}`" for x in (t.get("referenced_interfaces") or [])) or ""
        miss = ", ".join(f"`{x}`" for x in (t.get("missing_contractRefs_for_text_events") or [])) or ""
        unk = ", ".join(f"`{x}`" for x in (t.get("unknown_contractRefs") or [])) or ""
        missing_types = ", ".join(f"`{x}`" for x in (t.get("missing_type_candidates") or [])) or ""
        tail = "; ".join([p for p in [f"miss_ev={miss}" if miss else "", f"unk_ev={unk}" if unk else "", f"missing_types={missing_types}" if missing_types else ""] if p]) or ""
        lines.append(f"| {tid} | {view} | {layer} | {cr} | {drift} | {dto} | {ifaces} | {tail} |")
    lines.append("")
    lines.append("Notes:")
    lines.append("- `Text event drift` currently flags `core.rouge.*` strings (naming drift vs overlay docs).")
    lines.append("- `missing_types` are conservative candidates (suffix-based) that appear in task text but do not exist in current code; treat them as 'likely new contract/DTO to add' during implementation.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    root = _repo_root()
    out_dir = _today_ci_dir(root) / "contracts-plan"
    inventory = _inventory_contracts(root)
    matrix = _matrix_for_tasks(root, inventory)

    _write_json(out_dir / "contracts_inventory.json", inventory)
    _write_json(out_dir / "tasks_contracts_matrix.json", matrix)
    _write_text(out_dir / "tasks_contracts_matrix.md", _render_markdown(inventory, matrix))

    print(f"CONTRACTS_PLAN out={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
