#!/usr/bin/env python3
"""
sc-acceptance-check: local, reproducible acceptance gate.

Deterministic by default (no LLM subagents), with an optional LLM-backed subtasks coverage gate.
"""

from __future__ import annotations

import argparse
import os
import uuid
from pathlib import Path
from typing import Any

from _acceptance_report import write_markdown_report
from _acceptance_steps import (
    StepResult,
    step_acceptance_anchors_validate,
    step_acceptance_execution_evidence,
    step_acceptance_refs_validate,
    step_adr_compliance,
    step_architecture_boundary,
    step_build_warnaserror,
    step_contracts_validate,
    step_headless_e2e_evidence,
    step_overlay_validate,
    step_sc_analyze_task_context,
    step_perf_budget,
    step_quality_rules,
    step_security_audit_evidence,
    step_security_hard,
    step_security_soft,
    step_sc_internal_imports,
    step_subtasks_coverage_llm,
    step_task_context_required_fields,
    step_task_links_validate,
    step_task_test_refs_validate,
    step_test_quality_soft,
    step_tests_all,
    step_ui_event_security,
    task_requires_headless_e2e,
)
from _risk_summary import write_risk_summary
from _taskmaster import resolve_triplet
from _unit_metrics import collect_unit_metrics
from _util import ci_dir, repo_root, today_str, write_json, write_text


def _parse_task_id(value: str | None) -> str | None:
    if not value:
        return None
    s = str(value).strip()
    return s.split(".", 1)[0] if s else None


def main() -> int:
    ap = argparse.ArgumentParser(description="sc-acceptance-check (reproducible acceptance gate)")
    ap.add_argument("--task-id", default=None, help="Taskmaster id (e.g. 10 or 10.3). Default: first status=in-progress task.")
    ap.add_argument("--godot-bin", default=None, help="Godot mono console path (or set env GODOT_BIN)")
    ap.add_argument("--out-per-task", action="store_true", help="Write outputs to sc-acceptance-check-task-<id>/ to avoid overwriting.")
    ap.add_argument("--perf-p95-ms", type=int, default=None, help="Enable perf hard gate by parsing [PERF] p95_ms from latest logs/ci/**/headless.log. 0 disables.")
    ap.add_argument("--require-perf", action="store_true", help="(legacy) enable perf hard gate using env PERF_P95_THRESHOLD_MS (or default 20ms)")
    ap.add_argument("--strict-adr-status", action="store_true", help="fail if any referenced ADR is not Accepted")
    ap.add_argument("--strict-test-quality", action="store_true", help="fail if deterministic test-quality heuristics report verdict=Needs Fix")
    ap.add_argument("--strict-quality-rules", action="store_true", help="fail if deterministic quality rules report verdict=Needs Fix")
    ap.add_argument("--require-task-test-refs", action="store_true", help="fail if tasks_back/tasks_gameplay test_refs is empty for the resolved task id")
    ap.add_argument("--require-executed-refs", action="store_true", help="fail if acceptance anchors cannot be proven executed in this run (TRX/JUnit evidence)")
    ap.add_argument("--task-context-required", default="skip", choices=["skip", "warn", "require"], help="run sc-analyze + validate required task context fields (triplet semantics)")
    ap.add_argument("--security-path-gate", default="require", choices=["skip", "warn", "require"])
    ap.add_argument("--security-sql-gate", default="require", choices=["skip", "warn", "require"])
    ap.add_argument("--security-audit-schema-gate", default="require", choices=["skip", "warn", "require"])
    ap.add_argument("--ui-event-json-guards", default="skip", choices=["skip", "warn", "require"])
    ap.add_argument("--ui-event-source-verify", default="skip", choices=["skip", "warn", "require"])
    ap.add_argument("--security-audit-evidence", default="skip", choices=["skip", "warn", "require"])
    ap.add_argument("--require-headless-e2e", action="store_true", help="fail when acceptance refs include .gd but this run does not produce headless artifacts")
    ap.add_argument("--subtasks-coverage", default="skip", choices=["skip", "warn", "require"])
    ap.add_argument("--subtasks-timeout-sec", type=int, default=600, help="Timeout for subtasks coverage LLM gate.")
    ap.add_argument("--only", default=None, help="Comma-separated step filter (adr,links,subtasks,overlay,contracts,arch,build,security,quality,rules,tests,perf,risk). Default: all.")
    args = ap.parse_args()

    task_id = _parse_task_id(args.task_id)
    try:
        triplet = resolve_triplet(task_id=task_id)
    except Exception as exc:  # noqa: BLE001
        print(f"[sc-acceptance-check] ERROR: failed to resolve task: {exc}")
        return 2

    out_dir = ci_dir(f"sc-acceptance-check-task-{triplet.task_id}") if bool(args.out_per_task) else ci_dir("sc-acceptance-check")
    only = {x.strip() for x in str(args.only).split(",") if x.strip()} if args.only else None

    def enabled(key: str) -> bool:
        return True if only is None else (key in only)

    steps: list[StepResult] = []
    has_gd_refs = task_requires_headless_e2e(triplet)
    needs_headless = bool(args.require_headless_e2e) and has_gd_refs
    require_executed = bool(args.require_executed_refs)
    subtasks_mode = str(args.subtasks_coverage or "skip").strip().lower()
    audit_mode = str(args.security_audit_evidence or "skip").strip().lower()
    ctx_mode = str(args.task_context_required or "skip").strip().lower()
    run_id = uuid.uuid4().hex
    write_text(out_dir / "run_id.txt", run_id + "\n")

    if enabled("adr"):
        steps.append(step_adr_compliance(out_dir, triplet, strict_status=bool(args.strict_adr_status)))
    if enabled("links"):
        steps.append(step_sc_analyze_task_context(out_dir, task_id=str(triplet.task_id), mode=ctx_mode))
        steps.append(step_task_context_required_fields(out_dir, task_id=str(triplet.task_id), mode=ctx_mode, stage="refactor"))
        steps.append(step_sc_internal_imports(out_dir))
        steps.append(step_task_links_validate(out_dir))
        steps.append(step_task_test_refs_validate(out_dir, task_id=str(triplet.task_id), require_non_empty=bool(args.require_task_test_refs)))
        steps.append(step_acceptance_refs_validate(out_dir, task_id=str(triplet.task_id)))
        steps.append(step_acceptance_anchors_validate(out_dir, task_id=str(triplet.task_id)))
    elif ctx_mode in ("warn", "require"):
        steps.append(
            StepResult(
                name="task-context-required",
                status="fail" if ctx_mode == "require" else "skipped",
                rc=1 if ctx_mode == "require" else 0,
                details={"error": "links_step_disabled", "hint": "include 'links' in --only (or omit --only) when using --task-context-required warn|require"},
            )
        )
    if enabled("subtasks"):
        if subtasks_mode == "skip":
            steps.append(StepResult(name="subtasks-coverage", status="skipped", rc=0, details={"reason": "subtasks_coverage_skip"}))
        else:
            steps.append(step_subtasks_coverage_llm(out_dir, triplet, timeout_sec=int(args.subtasks_timeout_sec)))
    elif subtasks_mode in ("warn", "require"):
        steps.append(
            StepResult(
                name="subtasks-coverage",
                status="fail" if subtasks_mode == "require" else "skipped",
                rc=1 if subtasks_mode == "require" else 0,
                details={"error": "subtasks_step_disabled", "hint": "include 'subtasks' in --only (or omit --only) when using --subtasks-coverage warn|require"},
            )
        )
    if enabled("overlay"):
        steps.append(step_overlay_validate(out_dir))
    if enabled("contracts"):
        steps.append(step_contracts_validate(out_dir))
    if enabled("arch"):
        steps.append(step_architecture_boundary(out_dir))
    if enabled("build"):
        steps.append(step_build_warnaserror(out_dir))
    if enabled("quality"):
        steps.append(step_test_quality_soft(out_dir, triplet, strict=bool(args.strict_test_quality)))
    if enabled("rules"):
        steps.append(step_quality_rules(out_dir, strict=bool(args.strict_quality_rules)))
    if enabled("security"):
        steps.append(step_security_hard(out_dir, path_mode=str(args.security_path_gate), sql_mode=str(args.security_sql_gate), audit_schema_mode=str(args.security_audit_schema_gate)))
        steps.append(step_ui_event_security(out_dir, json_guards_mode=str(args.ui_event_json_guards), source_verify_mode=str(args.ui_event_source_verify)))
        steps.append(step_security_soft(out_dir))

    godot_bin = args.godot_bin or os.environ.get("GODOT_BIN")
    if enabled("tests"):
        test_type = "all" if has_gd_refs else "unit"
        if test_type != "unit" and not godot_bin:
            steps.append(StepResult(name="tests-all", status="fail", rc=2, details={"error": "missing_godot_bin", "hint": "set --godot-bin or env GODOT_BIN"}))
        else:
            steps.append(step_tests_all(out_dir, godot_bin, run_id=run_id, test_type=test_type))
            if needs_headless:
                steps.append(step_headless_e2e_evidence(out_dir, expected_run_id=run_id))
            if require_executed:
                steps.append(step_acceptance_execution_evidence(out_dir, task_id=str(triplet.task_id), run_id=run_id))
            steps.append(step_security_audit_evidence(out_dir, expected_run_id=run_id, mode=audit_mode))
    elif needs_headless:
        steps.append(StepResult(name="headless-e2e-evidence", status="fail", rc=1, details={"error": "tests_step_disabled", "hint": "include 'tests' in --only (or omit --only) when using --require-headless-e2e"}))
    elif require_executed:
        steps.append(StepResult(name="acceptance-executed-evidence", status="fail", rc=1, details={"error": "tests_step_disabled", "hint": "include 'tests' in --only (or omit --only) when using --require-executed-refs"}))
    elif audit_mode == "require":
        steps.append(StepResult(name="security-audit-executed-evidence", status="fail", rc=1, details={"error": "tests_step_disabled", "hint": "include 'tests' in --only (or omit --only) when using --security-audit-evidence require"}))
    elif audit_mode == "warn":
        steps.append(StepResult(name="security-audit-executed-evidence", status="ok", rc=0, details={"mode": "warn", "reason": "tests_step_disabled"}))

    env_v = os.environ.get("PERF_P95_THRESHOLD_MS")
    env_p95 = int(env_v) if (env_v and env_v.isdigit()) else None
    perf_p95_ms = max(0, int(args.perf_p95_ms)) if args.perf_p95_ms is not None else (env_p95 if env_p95 is not None else (20 if args.require_perf else 0))
    if enabled("perf"):
        steps.append(step_perf_budget(out_dir, max_p95_ms=perf_p95_ms))

    hard_failed = False
    for s in steps:
        if s.name == "security-soft":
            continue
        if s.name == "subtasks-coverage" and subtasks_mode != "require":
            continue
        if s.status == "fail":
            hard_failed = True

    metrics: dict[str, Any] = {}
    tests_step = next((s for s in steps if s.name == "tests-all" and s.log), None)
    tests_log = Path(tests_step.log) if (tests_step and tests_step.log) else None
    unit = collect_unit_metrics(tests_all_log=tests_log, fallback_unit_dir=(repo_root() / "logs" / "unit" / today_str()))
    if unit:
        metrics["unit"] = unit
    perf_step = next((s for s in steps if s.name == "perf-budget" and isinstance(s.details, dict)), None)
    if perf_step and isinstance(perf_step.details, dict):
        metrics["perf"] = perf_step.details

    risk_summary_rel: str | None = None
    if enabled("risk"):
        try:
            risk_path, risk_payload = write_risk_summary(
                out_dir=out_dir,
                task_id=str(triplet.task_id),
                run_id=run_id,
                acceptance_status="fail" if hard_failed else "ok",
                steps=steps,
                metrics=metrics or None,
            )
            risk_summary_rel = str(risk_path.relative_to(repo_root())).replace("\\", "/")
            steps.append(StepResult(name="risk-summary", status="ok", rc=0, details={"risk_summary": risk_summary_rel, "verdict": (risk_payload or {}).get("verdict")}))
        except Exception as exc:  # noqa: BLE001
            hard_failed = True
            steps.append(StepResult(name="risk-summary", status="fail", rc=1, details={"error": str(exc)}))

    summary: dict[str, Any] = {
        "cmd": "sc-acceptance-check",
        "date": today_str(),
        "run_id": run_id,
        "task_id": triplet.task_id,
        "title": triplet.master.get("title"),
        "only": args.only,
        "status": "fail" if hard_failed else "ok",
        "steps": [s.__dict__ for s in steps],
        "out_dir": str(out_dir),
        "subtasks_coverage_mode": subtasks_mode,
    }
    if risk_summary_rel:
        summary["risk_summary"] = risk_summary_rel
    if metrics:
        summary["metrics"] = metrics

    write_json(out_dir / "summary.json", summary)
    write_markdown_report(out_dir, triplet, steps, metrics=metrics or None)

    print(f"SC_ACCEPTANCE status={summary['status']} out={out_dir}")
    return 0 if not hard_failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
