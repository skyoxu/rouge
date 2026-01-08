#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_task_optional_hints_to_views (deterministic)

Goal:
  Reduce semantic drift ("done not real") by removing non-core / non-portable
  optional hints from `.taskmaster/tasks/tasks.json` (master fields) and
  migrating them into view task files:
    - `.taskmaster/tasks/tasks_back.json`
    - `.taskmaster/tasks/tasks_gameplay.json`

Policy (conservative):
  A line is treated as an optional hint if it matches one of:
    - Explicit optional/hint prefixes: Optional:/可选:/建议:/加固:/演示:/示例:/参考:
    - Extra hints: Supplement:/Add-on:/Extra:
    - Local demo references / absolute Windows paths

Where it goes:
  - View task `test_strategy` list (normalized to a single "Optional: ..." prefix).

Outputs (audit trail):
  logs/ci/<YYYY-MM-DD>/migrate-task-optional-hints/
    - summary.json
    - report.md

Usage (Windows):
  py -3 scripts/python/migrate_task_optional_hints_to_views.py
  py -3 scripts/python/migrate_task_optional_hints_to_views.py --write
  py -3 scripts/python/migrate_task_optional_hints_to_views.py --task-ids 6,12 --write
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass
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


def write_text(path: Path, text: str) -> None:
    path.write_text(str(text).replace("\r\n", "\n"), encoding="utf-8", newline="\n")


ABS_PATH_RE = re.compile(r"\b[A-Za-z]:\\")
DEMO_REF_RE = re.compile(r"(?i)\b(?:demo/|demo\\|godot-demo-projects|awesome-godot)\b")

_CN_OPT = r"\u53ef\u9009"  # 可选
_CN_SUG = r"\u5efa\u8bae"  # 建议
_CN_HARDEN = r"\u52a0\u56fa"  # 加固
_CN_DEMO = r"\u6f14\u793a"  # 演示
_CN_EXAMPLE = r"\u793a\u4f8b"  # 示例
_CN_REF = r"\u53c2\u8003"  # 参考

PREFIX_RE = re.compile(
    rf"^\s*(?:"
    r"Optional|"
    rf"{_CN_OPT}|{_CN_SUG}|{_CN_HARDEN}|{_CN_DEMO}|{_CN_EXAMPLE}|{_CN_REF}|"
    r"Supplement|Add-on|Extra"
    r")\s*:\s*(.+)\s*$",
    flags=re.IGNORECASE,
)


def normalize_optional_line(raw: str) -> str | None:
    line = str(raw or "").strip()
    if not line:
        return None
    m = PREFIX_RE.match(line)
    if m:
        body = str(m.group(1) or "").strip()
        return f"Optional: {body}" if body else "Optional: (empty)"
    if ABS_PATH_RE.search(line) or DEMO_REF_RE.search(line):
        return f"Optional: {line}"
    return None


def split_lines(text: str) -> list[str]:
    return str(text or "").replace("\r\n", "\n").split("\n")


def join_lines(lines: list[str]) -> str:
    # Preserve a trailing newline in the stored string for diff stability.
    return "\n".join(lines).rstrip() + "\n"


def parse_task_ids(csv: str | None) -> set[str]:
    if not csv:
        return set()
    out: set[str] = set()
    for part in str(csv).split(","):
        s = part.strip()
        if s:
            out.add(s)
    return out


def find_view_task(view_tasks: list[dict[str, Any]], task_id: str) -> dict[str, Any] | None:
    try:
        tid_int = int(str(task_id))
    except ValueError:
        return None
    for t in view_tasks:
        if not isinstance(t, dict):
            continue
        if t.get("taskmaster_id") == tid_int:
            return t
    return None


@dataclass(frozen=True)
class Change:
    task_id: str
    moved_from: str  # details|testStrategy
    optional_lines: list[str]


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate optional hints from tasks.json into tasks_back/tasks_gameplay views.")
    ap.add_argument("--write", action="store_true", help="Apply changes (default: dry run).")
    ap.add_argument("--task-ids", default=None, help="Comma-separated task ids to process (default: all).")
    args = ap.parse_args()

    root = repo_root()
    out_dir = ci_out_dir("migrate-task-optional-hints")

    tasks_json_path = root / ".taskmaster" / "tasks" / "tasks.json"
    back_path = root / ".taskmaster" / "tasks" / "tasks_back.json"
    gameplay_path = root / ".taskmaster" / "tasks" / "tasks_gameplay.json"

    report: dict[str, Any] = {
        "status": "fail",
        "write": bool(args.write),
        "task_ids_filter": sorted(parse_task_ids(args.task_ids)) if args.task_ids else None,
        "paths": {
            "tasks_json": str(tasks_json_path).replace("\\", "/"),
            "tasks_back": str(back_path).replace("\\", "/"),
            "tasks_gameplay": str(gameplay_path).replace("\\", "/"),
        },
        "changes": [],
        "errors": [],
    }

    if not tasks_json_path.exists():
        report["errors"].append("missing_tasks_json")
        write_json(out_dir / "summary.json", report)
        return 1

    tasks_json = read_json(tasks_json_path)
    master = (tasks_json.get("master") or {}) if isinstance(tasks_json, dict) else {}
    tasks = master.get("tasks") if isinstance(master, dict) else None
    if not isinstance(tasks, list):
        report["errors"].append("invalid_tasks_json_schema")
        write_json(out_dir / "summary.json", report)
        return 1

    back_view = read_json(back_path) if back_path.exists() else []
    gameplay_view = read_json(gameplay_path) if gameplay_path.exists() else []
    if not isinstance(back_view, list):
        back_view = []
    if not isinstance(gameplay_view, list):
        gameplay_view = []

    allowed_ids = parse_task_ids(args.task_ids)
    changes: list[Change] = []

    for t in tasks:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or "").strip()
        if not tid:
            continue
        if allowed_ids and tid not in allowed_ids:
            continue

        moved: list[Change] = []
        for field in ("details", "testStrategy"):
            raw = str(t.get(field) or "")
            lines = split_lines(raw)
            kept: list[str] = []
            opt: list[str] = []
            for line in lines:
                normalized = normalize_optional_line(line)
                if normalized:
                    opt.append(normalized)
                else:
                    kept.append(line)
            # Only record change when we actually move something meaningful.
            opt = [x for x in opt if x and x.strip()]
            if not opt:
                continue
            t[field] = join_lines([x for x in kept if x is not None])
            moved.append(Change(task_id=tid, moved_from=field, optional_lines=opt))

        if not moved:
            continue

        # Apply to views (if present).
        back_task = find_view_task(back_view, tid)
        gameplay_task = find_view_task(gameplay_view, tid)
        for ch in moved:
            for view_name, view_task in (("back", back_task), ("gameplay", gameplay_task)):
                if not isinstance(view_task, dict):
                    continue
                ts = view_task.get("test_strategy")
                if not isinstance(ts, list):
                    ts = []
                existing = {str(x).strip() for x in ts if str(x).strip()}
                for opt in ch.optional_lines:
                    if opt not in existing:
                        ts.append(opt)
                        existing.add(opt)
                view_task["test_strategy"] = ts

        changes.extend(moved)

    report["changes"] = [
        {"task_id": c.task_id, "moved_from": c.moved_from, "count": len(c.optional_lines), "lines": c.optional_lines}
        for c in changes
    ]

    if args.write:
        tasks_json_path.write_text(json.dumps(tasks_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        if back_path.exists():
            back_path.write_text(json.dumps(back_view, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        if gameplay_path.exists():
            gameplay_path.write_text(json.dumps(gameplay_view, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    report["status"] = "ok"
    write_json(out_dir / "summary.json", report)

    md_lines: list[str] = []
    md_lines.append("# migrate_task_optional_hints_to_views report")
    md_lines.append("")
    md_lines.append(f"- date: {today_str()}")
    md_lines.append(f"- write: {bool(args.write)}")
    md_lines.append(f"- changes: {len(changes)}")
    md_lines.append("")
    for c in changes:
        md_lines.append(f"## Task {c.task_id} ({c.moved_from})")
        for line in c.optional_lines:
            md_lines.append(f"- {line}")
        md_lines.append("")
    write_text(out_dir / "report.md", "\n".join(md_lines) + "\n")

    print(f"MIGRATE_OPTIONAL_HINTS status=ok changes={len(changes)} write={bool(args.write)} out={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

