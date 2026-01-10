#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect sc-llm-check-subtasks-coverage outputs into one batch report.

Reads:
  logs/ci/<date>/sc-llm-subtasks-coverage-task-<id>/verdict.json
and enriches with master task titles from:
  .taskmaster/tasks/tasks.json

Writes:
  logs/ci/<date>/sc-llm-subtasks-coverage-batch/
    - summary.json
    - summary.md

This script does not modify any task files.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: Any) -> None:
    _write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _default_task_ids(root: Path) -> list[int]:
    tasks = (_load_json(root / ".taskmaster" / "tasks" / "tasks.json").get("master") or {}).get("tasks") or []
    out: list[int] = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        subs = t.get("subtasks") or []
        if not isinstance(subs, list) or not subs:
            continue
        try:
            tid = int(t.get("id"))
        except Exception:
            continue
        out.append(tid)
    return sorted(out)


def _task_titles(root: Path) -> dict[int, str]:
    tasks = (_load_json(root / ".taskmaster" / "tasks" / "tasks.json").get("master") or {}).get("tasks") or []
    out: dict[int, str] = {}
    for t in tasks:
        if not isinstance(t, dict):
            continue
        try:
            tid = int(t.get("id"))
        except Exception:
            continue
        out[tid] = str(t.get("title") or "").strip()
    return out


def _read_verdict(root: Path, date: str, task_id: int) -> dict[str, Any]:
    verdict_path = root / "logs" / "ci" / date / f"sc-llm-subtasks-coverage-task-{task_id}" / "verdict.json"
    if not verdict_path.exists():
        return {"task_id": task_id, "status": "missing", "error": f"verdict.json not found: {verdict_path}"}
    data = _load_json(verdict_path)
    if not isinstance(data, dict):
        return {"task_id": task_id, "status": "invalid", "error": "verdict.json is not an object"}
    return data


def _summarize_verdict(task_id: int, title: str, verdict: dict[str, Any]) -> dict[str, Any]:
    subtasks = verdict.get("subtasks") or []
    uncovered_ids = set((verdict.get("uncovered_subtask_ids") or []) if isinstance(verdict.get("uncovered_subtask_ids"), list) else [])
    uncovered: list[dict[str, Any]] = []
    if isinstance(subtasks, list):
        for st in subtasks:
            if not isinstance(st, dict):
                continue
            sid = str(st.get("id") or "").strip()
            if sid and sid in uncovered_ids:
                uncovered.append(
                    {
                        "id": sid,
                        "title": str(st.get("title") or "").strip(),
                        "reason": str(st.get("reason") or "").strip(),
                        "matches": st.get("matches") or [],
                    }
                )
    return {
        "task_id": task_id,
        "title": title,
        "status": verdict.get("status"),
        "uncovered_subtask_ids": sorted(uncovered_ids, key=lambda x: (len(x), x)),
        "uncovered_subtasks": uncovered,
        "notes": verdict.get("notes") or [],
        "out_dir": f"logs/ci/{_dt.date.today().isoformat()}/sc-llm-subtasks-coverage-task-{task_id}",
    }


def _to_markdown(items: list[dict[str, Any]], *, date: str) -> str:
    lines: list[str] = []
    lines.append(f"# Subtasks coverage batch report ({date})")
    lines.append("")
    for it in items:
        lines.append(f"## T{it['task_id']}: {it.get('title','')}".rstrip())
        lines.append(f"- Status: {it.get('status')}")
        uncovered = it.get("uncovered_subtasks") or []
        if uncovered:
            lines.append("- Uncovered subtasks:")
            for st in uncovered:
                rid = st.get("id", "")
                rtitle = st.get("title", "")
                reason = (st.get("reason") or "").strip()
                lines.append(f"  - {rid}: {rtitle}".rstrip())
                if reason:
                    lines.append(f"    - reason: {reason}")
        else:
            lines.append("- Uncovered subtasks: (none)")
        lines.append(f"- Evidence: `logs/ci/{date}/sc-llm-subtasks-coverage-task-{it['task_id']}/`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=_dt.date.today().isoformat(), help="CI date folder under logs/ci (default: today)")
    parser.add_argument("--task-ids", default="", help="Comma-separated task ids. Default: all tasks that have subtasks.")
    args = parser.parse_args()

    root = _repo_root()
    date = str(args.date).strip()
    titles = _task_titles(root)

    if str(args.task_ids).strip():
        task_ids = [int(x.strip()) for x in str(args.task_ids).split(",") if x.strip()]
    else:
        task_ids = _default_task_ids(root)

    results: list[dict[str, Any]] = []
    for tid in task_ids:
        verdict = _read_verdict(root, date, tid)
        results.append(_summarize_verdict(tid, titles.get(tid, ""), verdict))

    out_dir = root / "logs" / "ci" / date / "sc-llm-subtasks-coverage-batch"
    _write_json(out_dir / "summary.json", {"date": date, "tasks": results})
    _write_text(out_dir / "summary.md", _to_markdown(results, date=date))
    print(f"SUBTASKS_COVERAGE_BATCH out={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

