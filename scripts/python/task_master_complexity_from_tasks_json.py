"""
Generate a Task Master complexity report from the existing `complexity` fields in tasks.json.

Why:
- `npx task-master analyze-complexity` depends on Claude Code CLI and may hang/fail in some environments.
- This script produces a report compatible with `task-master complexity-report` so we can still inspect
  complexity distributions deterministically.

Notes:
- UTF-8 only.
- Writes artifacts under logs/ci/<YYYY-MM-DD>/task-master-complexity/ by default.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class TaskRow:
    task_id: str
    title: str
    complexity: int | None
    status: str | None
    subtasks_count: int
    recommended_subtasks: int | None
    expansion_prompt: str | None


def _today_yyyy_mm_dd() -> str:
    return _dt.date.today().isoformat()


def _iso_utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json_utf8(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json_utf8(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _write_text_utf8(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _get_master_tasks(tasks_json: dict[str, Any]) -> list[dict[str, Any]]:
    master = tasks_json.get("master") or {}
    tasks = master.get("tasks") or tasks_json.get("tasks") or []
    if not isinstance(tasks, list):
        raise TypeError("tasks.json: expected master.tasks (or tasks) to be a list")
    return tasks


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


def _task_rows(tasks: Iterable[dict[str, Any]]) -> list[TaskRow]:
    rows: list[TaskRow] = []
    for t in tasks:
        task_id = str(t.get("id", "")).strip()
        title = str(t.get("title", "")).strip()
        complexity = _to_int_or_none(t.get("complexity"))
        status = (str(t.get("status")).strip() if t.get("status") is not None else None)
        subtasks = t.get("subtasks") or []
        subtasks_count = len(subtasks) if isinstance(subtasks, list) else 0
        recommended_subtasks = _to_int_or_none(t.get("recommendedSubtasks"))
        expansion_prompt = (
            str(t.get("expansionPrompt")).strip() if t.get("expansionPrompt") is not None else None
        )
        rows.append(
            TaskRow(
                task_id=task_id,
                title=title,
                complexity=complexity,
                status=status,
                subtasks_count=subtasks_count,
                recommended_subtasks=recommended_subtasks,
                expansion_prompt=expansion_prompt,
            )
        )
    return rows


def _report_from_rows(
    *,
    rows: list[TaskRow],
    tasks_file: str,
    threshold: int,
) -> dict[str, Any]:
    complexity_analysis: list[dict[str, Any]] = []
    for r in rows:
        task_id_int = _to_int_or_none(r.task_id)
        complexity_analysis.append(
            {
                "taskId": task_id_int if task_id_int is not None else r.task_id,
                "taskTitle": r.title,
                "complexityScore": r.complexity,
                "recommendedSubtasks": (
                    r.recommended_subtasks
                    if r.recommended_subtasks is not None
                    else r.subtasks_count
                ),
                "expansionPrompt": r.expansion_prompt or "",
                "reasoning": (
                    "Generated from tasks.json existing `complexity` field "
                    "(no LLM re-analysis performed)."
                ),
            }
        )

    total = len(rows)
    analyzed = total
    return {
        "meta": {
            "generatedAt": _iso_utc_now(),
            "tasksAnalyzed": analyzed,
            "totalTasks": total,
            "analysisCount": analyzed,
            "thresholdScore": threshold,
            "projectName": "rouge",
            "usedResearch": False,
            "sourceTasksFile": tasks_file.replace("\\", "/"),
        },
        "complexityAnalysis": complexity_analysis,
    }


def _summary_markdown(rows: list[TaskRow], threshold: int) -> str:
    dist: dict[int | None, int] = {}
    for r in rows:
        dist[r.complexity] = dist.get(r.complexity, 0) + 1

    def sort_key(k: int | None) -> tuple[int, int]:
        if k is None:
            return (1, 999)
        return (0, k)

    dist_lines = "\n".join(
        f"- complexity={k}: {dist[k]} task(s)" for k in sorted(dist.keys(), key=sort_key)
    )

    high_no_sub = [
        r for r in rows if (r.complexity is not None and r.complexity >= threshold and r.subtasks_count == 0)
    ]
    high_no_sub_lines = "\n".join(
        f"- {r.task_id}: complexity={r.complexity} title={r.title}" for r in sorted(high_no_sub, key=lambda x: (-int(x.complexity or 0), x.task_id))
    ) or "- (none)"

    top = sorted(
        rows,
        key=lambda r: (
            -(r.complexity if r.complexity is not None else -1),
            int(r.task_id) if r.task_id.isdigit() else 10**9,
            r.task_id,
        ),
    )[:15]
    top_lines = "\n".join(
        f"- {r.task_id}: complexity={r.complexity} subtasks={r.subtasks_count} status={r.status} title={r.title}"
        for r in top
    ) or "- (none)"

    return (
        "# Task complexity summary (from tasks.json)\n\n"
        "## Distribution\n"
        f"{dist_lines}\n\n"
        f"## complexity >= {threshold} and no subtasks\n"
        f"{high_no_sub_lines}\n\n"
        "## Top 15 by complexity\n"
        f"{top_lines}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tasks-file",
        default=r".taskmaster\tasks\tasks.json",
        help="Path to Task Master tasks.json",
    )
    parser.add_argument(
        "--out-dir",
        default=os.path.join("logs", "ci", _today_yyyy_mm_dd(), "task-master-complexity"),
        help="Output directory (UTF-8 artifacts)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=7,
        help="Threshold used to flag high-complexity tasks without subtasks",
    )
    args = parser.parse_args()

    tasks_file = args.tasks_file
    out_dir = args.out_dir
    threshold = args.threshold

    tasks_json = _load_json_utf8(tasks_file)
    tasks = _get_master_tasks(tasks_json)
    rows = _task_rows(tasks)

    report = _report_from_rows(rows=rows, tasks_file=tasks_file, threshold=threshold)
    report_path = os.path.join(out_dir, "task-complexity-report.from-tasks-json.json")
    _write_json_utf8(report_path, report)

    summary_path = os.path.join(out_dir, "complexity-summary.md")
    _write_text_utf8(summary_path, _summary_markdown(rows, threshold))

    print(f"[ok] wrote: {report_path}")
    print(f"[ok] wrote: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

