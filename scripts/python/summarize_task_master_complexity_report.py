"""
Summarize a Task Master complexity report JSON (output of `task-master analyze-complexity`).

Outputs UTF-8 artifacts under logs/ci/<YYYY-MM-DD>/task-master-complexity/ by default.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Row:
    task_id: str
    title: str
    score: int | None
    recommended_subtasks: int | None


def _today_yyyy_mm_dd() -> str:
    return _dt.date.today().isoformat()


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError("report must be a JSON object")
    return data


def _write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _rows(report: dict[str, Any]) -> list[Row]:
    items = report.get("complexityAnalysis") or []
    if not isinstance(items, list):
        raise TypeError("report.complexityAnalysis must be a list")
    rows: list[Row] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        rows.append(
            Row(
                task_id=str(it.get("taskId", "")).strip(),
                title=str(it.get("taskTitle", "")).strip(),
                score=_to_int_or_none(it.get("complexityScore")),
                recommended_subtasks=_to_int_or_none(it.get("recommendedSubtasks")),
            )
        )
    return rows


def _distribution(rows: list[Row]) -> dict[str, int]:
    low = sum(1 for r in rows if r.score is not None and 1 <= r.score <= 4)
    medium = sum(1 for r in rows if r.score is not None and 5 <= r.score <= 7)
    high = sum(1 for r in rows if r.score is not None and 8 <= r.score <= 10)
    unknown = sum(1 for r in rows if r.score is None)
    return {"low_1_4": low, "medium_5_7": medium, "high_8_10": high, "unknown": unknown}


def _sorted_rows(rows: list[Row]) -> list[Row]:
    def id_key(s: str) -> int:
        return int(s) if s.isdigit() else 10**9

    return sorted(
        rows,
        key=lambda r: (-(r.score if r.score is not None else -1), id_key(r.task_id), r.task_id),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        default=os.path.join(
            "logs", "ci", _today_yyyy_mm_dd(), "task-master-complexity", "task-complexity-report.analyzed.json"
        ),
        help="Path to task-master analyze-complexity output JSON",
    )
    parser.add_argument(
        "--out-dir",
        default=os.path.join("logs", "ci", _today_yyyy_mm_dd(), "task-master-complexity"),
        help="Output directory for summary artifacts",
    )
    parser.add_argument("--top", type=int, default=15, help="Top N tasks by complexity to include")
    parser.add_argument("--high-threshold", type=int, default=8, help="High complexity threshold (inclusive)")
    args = parser.parse_args()

    report = _load_json(args.report)
    meta = report.get("meta") or {}
    rows = _rows(report)
    dist = _distribution(rows)
    sorted_rows = _sorted_rows(rows)
    top = sorted_rows[: max(0, args.top)]
    high = [r for r in sorted_rows if r.score is not None and r.score >= args.high_threshold]

    summary = {
        "meta": {
            "generatedAt": meta.get("generatedAt"),
            "tasksAnalyzed": meta.get("tasksAnalyzed"),
            "totalTasks": meta.get("totalTasks"),
            "thresholdScore": meta.get("thresholdScore"),
            "projectName": meta.get("projectName"),
            "usedResearch": meta.get("usedResearch"),
        },
        "distribution": dist,
        "top": [
            {
                "taskId": r.task_id,
                "score": r.score,
                "recommendedSubtasks": r.recommended_subtasks,
                "title": r.title,
            }
            for r in top
        ],
        "high": [
            {
                "taskId": r.task_id,
                "score": r.score,
                "recommendedSubtasks": r.recommended_subtasks,
                "title": r.title,
            }
            for r in high
        ],
    }

    out_json = os.path.join(args.out_dir, "complexity-summary.analyzed.json")
    _write_json(out_json, summary)

    def fmt_row(r: Row) -> str:
        return f"- {r.task_id}: score={r.score} recSub={r.recommended_subtasks} title={r.title}"

    md = (
        "# Task complexity summary (task-master analyze-complexity)\n\n"
        f"- generatedAt: {summary['meta']['generatedAt']}\n"
        f"- tasksAnalyzed: {summary['meta']['tasksAnalyzed']}\n"
        f"- totalTasks: {summary['meta']['totalTasks']}\n"
        f"- thresholdScore: {summary['meta']['thresholdScore']}\n"
        f"- projectName: {summary['meta']['projectName']}\n"
        f"- usedResearch: {summary['meta']['usedResearch']}\n\n"
        "## Distribution\n"
        f"- Low (1-4): {dist['low_1_4']}\n"
        f"- Medium (5-7): {dist['medium_5_7']}\n"
        f"- High (8-10): {dist['high_8_10']}\n"
        f"- Unknown: {dist['unknown']}\n\n"
        f"## High (>= {args.high_threshold})\n"
        + ("\n".join(fmt_row(r) for r in high) if high else "- (none)")
        + "\n\n"
        f"## Top {args.top}\n"
        + ("\n".join(fmt_row(r) for r in top) if top else "- (none)")
        + "\n"
    )
    out_md = os.path.join(args.out_dir, "complexity-summary.analyzed.md")
    _write_text(out_md, md)

    print(f"[ok] wrote: {out_json}")
    print(f"[ok] wrote: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

