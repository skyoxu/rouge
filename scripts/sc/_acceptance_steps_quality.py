from __future__ import annotations

from pathlib import Path

from _quality_rules import scan_quality_rules
from _step_result import StepResult
from _taskmaster import TaskmasterTriplet
from _test_quality import assess_test_quality
from _util import repo_root, write_json, write_text


def step_test_quality_soft(out_dir: Path, triplet: TaskmasterTriplet, *, strict: bool) -> StepResult:
    title = str(triplet.master.get("title") or "")
    details_blob = "\n".join(
        [
            str(triplet.master.get("details") or ""),
            str((triplet.back or {}).get("details") or ""),
            str((triplet.gameplay or {}).get("details") or ""),
        ]
    )
    taskdoc_path = Path(triplet.taskdoc_path) if triplet.taskdoc_path else None

    report = assess_test_quality(
        repo_root=repo_root(),
        task_id=triplet.task_id,
        title=title,
        details_blob=details_blob,
        taskdoc_path=taskdoc_path,
    )
    write_json(out_dir / "test-quality.json", report)

    verdict = str(report.get("verdict") or "OK")
    findings = report.get("findings") if isinstance(report.get("findings"), dict) else {}
    p1 = findings.get("p1") if isinstance(findings.get("p1"), list) else []
    p2 = findings.get("p2") if isinstance(findings.get("p2"), list) else []

    lines: list[str] = []
    lines.append(
        f"TEST_QUALITY verdict={verdict} ui_task={bool(report.get('ui_task'))} scanned={report.get('gdunit', {}).get('tests_scanned')}"
    )
    for x in p1[:20]:
        lines.append(f"P1 {x}")
    for x in p2[:20]:
        lines.append(f"P2 {x}")
    log_path = out_dir / "test-quality.log"
    write_text(log_path, "\n".join(lines) + "\n")

    status = "fail" if (strict and verdict == "Needs Fix") else "ok"
    return StepResult(name="test-quality", status=status, rc=0 if status == "ok" else 1, log=str(log_path), details=report)


def step_quality_rules(out_dir: Path, *, strict: bool) -> StepResult:
    report = scan_quality_rules(repo_root=repo_root())
    write_json(out_dir / "quality-rules.json", report)

    verdict = str(report.get("verdict") or "OK")
    counts = report.get("counts") if isinstance(report.get("counts"), dict) else {}

    lines: list[str] = []
    lines.append(f"QUALITY_RULES verdict={verdict} total={counts.get('total')} p0={counts.get('p0')} p1={counts.get('p1')}")
    findings = report.get("findings") if isinstance(report.get("findings"), dict) else {}
    for sev in ["p0", "p1"]:
        items = findings.get(sev) if isinstance(findings.get(sev), list) else []
        for it in items[:50]:
            if not isinstance(it, dict):
                continue
            f = it.get("file")
            ln = it.get("line")
            msg = it.get("message")
            lines.append(f"{sev.upper()} {f}:{ln} {msg}")

    log_path = out_dir / "quality-rules.log"
    write_text(log_path, "\n".join(lines) + "\n")

    status = "fail" if (strict and verdict == "Needs Fix") else "ok"
    return StepResult(name="quality-rules", status=status, rc=0 if status == "ok" else 1, log=str(log_path), details=report)

