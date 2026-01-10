from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from _step_result import StepResult
from _taskmaster import TaskmasterTriplet
from _util import repo_root, run_cmd, today_str, write_json, write_text

ADR_STATUS_RE = re.compile(r"^\s*-?\s*(?:Status|status)\s*:\s*([A-Za-z]+)\s*$", re.MULTILINE)
REFS_RE = re.compile(r"\bRefs\s*:\s*(.+)$", flags=re.IGNORECASE)


def find_adr_file(root: Path, adr_id: str) -> Path | None:
    adr_dir = root / "docs" / "adr"
    if not adr_dir.exists():
        return None
    matches = sorted(adr_dir.glob(f"{adr_id}-*.md"))
    if matches:
        return matches[0]
    exact = adr_dir / f"{adr_id}.md"
    return exact if exact.exists() else None


def read_adr_status(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = ADR_STATUS_RE.search(text)
    return m.group(1).strip() if m else None


def run_and_capture(out_dir: Path, name: str, cmd: list[str], timeout_sec: int) -> StepResult:
    rc, out = run_cmd(cmd, cwd=repo_root(), timeout_sec=timeout_sec)
    log_path = out_dir / f"{name}.log"
    write_text(log_path, out)
    return StepResult(name=name, status="ok" if rc == 0 else "fail", rc=rc, cmd=cmd, log=str(log_path))


def run_and_capture_mode(out_dir: Path, name: str, cmd: list[str], timeout_sec: int, *, mode: str) -> StepResult:
    """
    mode:
      - require: fail on rc!=0
      - warn: never fail (record rc in details)
      - skip: do not run
    """
    mode = str(mode or "require").strip().lower()
    if mode == "skip":
        return StepResult(name=name, status="skipped", rc=0, cmd=cmd, details={"mode": "skip"})
    rc, out = run_cmd(cmd, cwd=repo_root(), timeout_sec=timeout_sec)
    log_path = out_dir / f"{name}.log"
    write_text(log_path, out)
    if mode == "warn":
        return StepResult(name=name, status="ok", rc=0, cmd=cmd, log=str(log_path), details={"mode": "warn", "rc": rc})
    return StepResult(name=name, status="ok" if rc == 0 else "fail", rc=rc, cmd=cmd, log=str(log_path), details={"mode": "require"})


def step_adr_compliance(out_dir: Path, triplet: TaskmasterTriplet, *, strict_status: bool) -> StepResult:
    root = repo_root()
    adr_refs = triplet.adr_refs()
    arch_refs = triplet.arch_refs()
    overlay = triplet.overlay()

    details: dict[str, Any] = {
        "task_id": triplet.task_id,
        "title": triplet.master.get("title"),
        "adrRefs": adr_refs,
        "archRefs": arch_refs,
        "overlay": overlay,
        "adrStatus": {},
        "errors": [],
        "warnings": [],
        "strict_status": bool(strict_status),
    }

    if not adr_refs:
        details["errors"].append("missing adrRefs in tasks.json (master task)")
    if not arch_refs:
        details["errors"].append("missing archRefs in tasks.json (master task)")
    if not overlay:
        details["errors"].append("missing overlay in tasks.json (master task)")

    accepted = 0
    for adr in adr_refs:
        adr_path = find_adr_file(root, adr)
        if not adr_path:
            details["errors"].append(f"adr_not_found:{adr}")
            continue
        status = read_adr_status(adr_path) or "Unknown"
        details["adrStatus"][adr] = status
        if status == "Accepted":
            accepted += 1
        else:
            msg = f"adr_status_not_accepted:{adr}:{status}"
            (details["errors"] if strict_status else details["warnings"]).append(msg)

    details["accepted_count"] = accepted
    write_json(out_dir / "adr-compliance.json", details)
    return StepResult(name="adr-compliance", status="ok" if not details["errors"] else "fail", rc=0 if not details["errors"] else 1, details=details)


def step_task_links_validate(out_dir: Path) -> StepResult:
    return run_and_capture(out_dir, "task-links-validate", ["py", "-3", "scripts/python/task_links_validate.py"], 300)


def step_sc_internal_imports(out_dir: Path) -> StepResult:
    out_json = out_dir / "sc-internal-imports.json"
    cmd = ["py", "-3", "scripts/python/check_sc_internal_imports.py", "--out", str(out_json)]
    return run_and_capture(out_dir, "sc-internal-imports", cmd, 60)


def step_sc_analyze_task_context(
    out_dir: Path,
    *,
    task_id: str,
    mode: str,
    focus: str = "all",
    depth: str = "quick",
    timeout_sec: int = 900,
) -> StepResult:
    """
    Produces sc-analyze artifacts under logs/ci/<date>/sc-analyze and also writes a per-task copy into out_dir.

    mode:
      - require: fail on error
      - warn: do not fail (record rc in details)
      - skip: do not run
    """
    mode_n = str(mode or "require").strip().lower()
    cmd = [
        "py",
        "-3",
        "scripts/sc/analyze.py",
        "--task-id",
        str(task_id),
        "--focus",
        str(focus),
        "--depth",
        str(depth),
        "--format",
        "json",
    ]
    if mode_n == "skip":
        return StepResult(name="sc-analyze", status="skipped", rc=0, cmd=cmd, details={"mode": "skip"})

    rc, out = run_cmd(cmd, cwd=repo_root(), timeout_sec=int(timeout_sec))
    log_path = out_dir / "sc-analyze.log"
    write_text(log_path, out)

    sc_dir = repo_root() / "logs" / "ci" / today_str() / "sc-analyze"
    ctx_src = sc_dir / "task_context.json"
    ctx_dst_sc = sc_dir / f"task_context.{task_id}.json"
    ctx_dst_local = out_dir / f"task_context.{task_id}.json"

    details: dict[str, Any] = {
        "mode": mode_n,
        "task_id": str(task_id),
        "sc_analyze_dir": str(sc_dir.relative_to(repo_root())).replace("\\", "/"),
        "task_context": str(ctx_src.relative_to(repo_root())).replace("\\", "/") if ctx_src.exists() else None,
    }

    effective_rc = rc
    if rc == 0 and not ctx_src.exists():
        details["error"] = "missing_task_context_json"
        effective_rc = 2

    if rc == 0 and ctx_src.exists():
        try:
            shutil.copyfile(ctx_src, ctx_dst_sc)
            shutil.copyfile(ctx_src, ctx_dst_local)
            details["task_context_per_task"] = str(ctx_dst_sc.relative_to(repo_root())).replace("\\", "/")
            details["task_context_local"] = str(ctx_dst_local.relative_to(repo_root())).replace("\\", "/")
        except Exception as exc:  # noqa: BLE001
            details["error"] = f"copy_failed:{exc}"
            effective_rc = 3

    if mode_n == "warn" and effective_rc != 0:
        details["rc"] = effective_rc
        return StepResult(name="sc-analyze", status="ok", rc=0, cmd=cmd, log=str(log_path), details=details)

    return StepResult(
        name="sc-analyze",
        status="ok" if effective_rc == 0 else "fail",
        rc=0 if effective_rc == 0 else 1,
        cmd=cmd,
        log=str(log_path),
        details=details,
    )


def step_task_context_required_fields(
    out_dir: Path,
    *,
    task_id: str,
    mode: str,
    stage: str = "refactor",
    context_path: Path | None = None,
    timeout_sec: int = 120,
) -> StepResult:
    """
    Validates that the deterministic sc-analyze task_context.json includes all required fields for the given stage.

    mode:
      - require: fail on error
      - warn: do not fail (record rc in details)
      - skip: do not run
    """
    mode_n = str(mode or "require").strip().lower()
    ctx = context_path or (repo_root() / "logs" / "ci" / today_str() / "sc-analyze" / f"task_context.{task_id}.json")
    out_json = out_dir / "task-context-required.json"
    cmd = [
        "py",
        "-3",
        "scripts/python/validate_task_context_required_fields.py",
        "--task-id",
        str(task_id),
        "--stage",
        str(stage),
        "--context",
        str(ctx),
        "--out",
        str(out_json),
    ]
    if mode_n == "skip":
        return StepResult(name="task-context-required", status="skipped", rc=0, cmd=cmd, details={"mode": "skip"})

    details: dict[str, Any] = {
        "mode": mode_n,
        "task_id": str(task_id),
        "stage": str(stage),
        "context": str(ctx.relative_to(repo_root())).replace("\\", "/") if ctx.exists() else str(ctx),
        "out": str(out_json.relative_to(repo_root())).replace("\\", "/"),
    }

    if not ctx.exists():
        details["error"] = "missing_context_json"
        if mode_n == "warn":
            return StepResult(name="task-context-required", status="ok", rc=0, cmd=cmd, details={**details, "rc": 2})
        return StepResult(name="task-context-required", status="fail", rc=1, cmd=cmd, details=details)

    rc, out = run_cmd(cmd, cwd=repo_root(), timeout_sec=int(timeout_sec))
    log_path = out_dir / "task-context-required.log"
    write_text(log_path, out)

    if mode_n == "warn" and rc != 0:
        return StepResult(name="task-context-required", status="ok", rc=0, cmd=cmd, log=str(log_path), details={**details, "rc": rc})

    return StepResult(
        name="task-context-required",
        status="ok" if rc == 0 else "fail",
        rc=0 if rc == 0 else 1,
        cmd=cmd,
        log=str(log_path),
        details=details,
    )


def step_task_test_refs_validate(out_dir: Path, *, task_id: str, require_non_empty: bool) -> StepResult:
    out_json = out_dir / "task-test-refs.json"
    cmd = ["py", "-3", "scripts/python/validate_task_test_refs.py", "--task-id", str(task_id), "--out", str(out_json)]
    if require_non_empty:
        cmd.append("--require-non-empty")
    return run_and_capture(out_dir, "task-test-refs-validate", cmd, 120)


def step_acceptance_refs_validate(out_dir: Path, *, task_id: str) -> StepResult:
    out_json = out_dir / "acceptance-refs.json"
    cmd = ["py", "-3", "scripts/python/validate_acceptance_refs.py", "--task-id", str(task_id), "--stage", "refactor", "--out", str(out_json)]
    return run_and_capture(out_dir, "acceptance-refs-validate", cmd, 120)


def step_acceptance_anchors_validate(out_dir: Path, *, task_id: str) -> StepResult:
    out_json = out_dir / "acceptance-anchors.json"
    cmd = ["py", "-3", "scripts/python/validate_acceptance_anchors.py", "--task-id", str(task_id), "--stage", "refactor", "--out", str(out_json)]
    return run_and_capture(out_dir, "acceptance-anchors-validate", cmd, 120)


def step_acceptance_execution_evidence(out_dir: Path, *, task_id: str, run_id: str) -> StepResult:
    out_json = out_dir / "acceptance-executed-evidence.json"
    cmd = [
        "py",
        "-3",
        "scripts/python/validate_acceptance_execution_evidence.py",
        "--task-id",
        str(task_id),
        "--run-id",
        str(run_id),
        "--out",
        str(out_json),
    ]
    return run_and_capture(out_dir, "acceptance-executed-evidence", cmd, 120)


def step_overlay_validate(out_dir: Path) -> StepResult:
    primary = run_and_capture(out_dir, "validate-task-overlays", ["py", "-3", "scripts/python/validate_task_overlays.py"], 120)
    details: dict[str, Any] = {"primary": primary.__dict__}
    ok = primary.status == "ok"
    log_p = out_dir / "validate-task-overlays.log"
    if log_p.exists():
        log_text = log_p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^\s*VALIDATE_TASK_OVERLAYS_JSON\s*=\s*(\{.*\})\s*$", log_text, flags=re.MULTILINE | re.DOTALL)
        if m:
            try:
                details["parsed"] = json.loads(m.group(1))
            except Exception:
                details["parsed_error"] = "failed_to_parse_inline_json"
    write_json(out_dir / "validate-task-overlays.json", details)
    return StepResult(name="validate-task-overlays", status="ok" if ok else "fail", rc=0 if ok else 1, cmd=primary.cmd, log=primary.log, details=details)


def step_contracts_validate(out_dir: Path) -> StepResult:
    steps: list[StepResult] = []
    steps.append(run_and_capture(out_dir, "validate-contracts", ["py", "-3", "scripts/python/validate_contracts.py"], 300))
    steps.append(run_and_capture(out_dir, "check-gameloop-contracts", ["py", "-3", "scripts/python/check_gameloop_contracts.py"], 60))
    steps.append(
        run_and_capture(
            out_dir,
            "validate-task-contract-refs",
            ["py", "-3", "scripts/python/validate_task_contract_refs.py", "--out", str(out_dir / "task-contract-refs.json")],
            60,
        )
    )
    hard_failed = any(s.status == "fail" for s in steps)
    details = {"steps": [s.__dict__ for s in steps]}
    write_json(out_dir / "contracts-validate.json", details)
    return StepResult(name="contracts-validate", status="fail" if hard_failed else "ok", rc=1 if hard_failed else 0, details=details)


def step_architecture_boundary(out_dir: Path) -> StepResult:
    return run_and_capture(
        out_dir,
        "architecture-boundary",
        ["py", "-3", "scripts/python/check_architecture_boundary.py", "--out", str(out_dir / "architecture-boundary.json")],
        120,
    )


def step_build_warnaserror(out_dir: Path, *, target: str = "Rouge.csproj") -> StepResult:
    return run_and_capture(out_dir, "dotnet-build-warnaserror", ["py", "-3", "scripts/sc/build.py", target, "--type", "dev"], 1_800)


def step_security_soft(out_dir: Path) -> StepResult:
    steps: list[StepResult] = []
    steps.append(run_and_capture(out_dir, "check-sentry-secrets", ["py", "-3", "scripts/python/check_sentry_secrets.py"], 60))
    steps.append(run_and_capture(out_dir, "check-domain-contracts", ["py", "-3", "scripts/python/check_domain_contracts.py"], 60))
    steps.append(
        run_and_capture(
            out_dir,
            "security-soft-scan",
            ["py", "-3", "scripts/python/security_soft_scan.py", "--out", str(out_dir / "security-soft-scan.json")],
            120,
        )
    )
    steps.append(run_and_capture(out_dir, "check-encoding-since-today", ["py", "-3", "scripts/python/check_encoding.py", "--since-today"], 300))
    details = {"steps": [s.__dict__ for s in steps]}
    write_json(out_dir / "security-soft.json", details)
    return StepResult(name="security-soft", status="ok", details=details)


def step_security_hard(out_dir: Path, *, path_mode: str, sql_mode: str, audit_schema_mode: str) -> StepResult:
    path_out = out_dir / "security-path-gate.json"
    sql_out = out_dir / "security-sql-gate.json"
    audit_out = out_dir / "security-audit-gate.json"
    steps: list[StepResult] = []
    steps.append(
        run_and_capture_mode(
            out_dir,
            "security-path-gate",
            ["py", "-3", "scripts/python/security_hard_path_gate.py", "--out", str(path_out)],
            120,
            mode=path_mode,
        )
    )
    steps.append(
        run_and_capture_mode(
            out_dir,
            "security-sql-gate",
            ["py", "-3", "scripts/python/security_hard_sql_gate.py", "--out", str(sql_out)],
            120,
            mode=sql_mode,
        )
    )
    steps.append(
        run_and_capture_mode(
            out_dir,
            "security-audit-gate",
            ["py", "-3", "scripts/python/security_hard_audit_gate.py", "--out", str(audit_out)],
            120,
            mode=audit_schema_mode,
        )
    )
    hard_failed = any(s.status == "fail" for s in steps)
    details: dict[str, Any] = {"steps": [s.__dict__ for s in steps]}
    write_json(out_dir / "security-hard.json", details)
    return StepResult(name="security-hard", status="fail" if hard_failed else "ok", rc=1 if hard_failed else 0, details=details)


def step_ui_event_security(out_dir: Path, *, json_guards_mode: str, source_verify_mode: str) -> StepResult:
    steps: list[StepResult] = []
    steps.append(
        run_and_capture_mode(
            out_dir,
            "ui-event-json-guards",
            ["py", "-3", "scripts/python/validate_ui_event_json_guards.py", "--out", str(out_dir / "ui-event-json-guards.json")],
            120,
            mode=json_guards_mode,
        )
    )
    steps.append(
        run_and_capture_mode(
            out_dir,
            "ui-event-source-verify",
            ["py", "-3", "scripts/python/validate_ui_event_source_verification.py", "--out", str(out_dir / "ui-event-source-verify.json")],
            120,
            mode=source_verify_mode,
        )
    )
    hard_failed = any(s.status == "fail" for s in steps)
    details: dict[str, Any] = {"steps": [s.__dict__ for s in steps]}
    write_json(out_dir / "ui-event-security.json", details)
    return StepResult(name="ui-event-security", status="fail" if hard_failed else "ok", rc=1 if hard_failed else 0, details=details)


def step_security_audit_evidence(out_dir: Path, *, expected_run_id: str, mode: str) -> StepResult:
    out_json = out_dir / "security-audit-executed-evidence.json"
    cmd = ["py", "-3", "scripts/python/validate_security_audit_execution_evidence.py", "--run-id", str(expected_run_id), "--out", str(out_json)]
    return run_and_capture_mode(out_dir, "security-audit-executed-evidence", cmd, 120, mode=mode)


def _split_refs_blob(blob: str) -> list[str]:
    s = str(blob or "").replace("`", " ").replace(",", " ").replace(";", " ")
    return [p.strip().replace("\\", "/") for p in s.split() if p.strip()]


def task_requires_headless_e2e(triplet: Any) -> bool:
    for view in [getattr(triplet, "back", None), getattr(triplet, "gameplay", None)]:
        if not isinstance(view, dict):
            continue
        acceptance = view.get("acceptance") or []
        if not isinstance(acceptance, list):
            continue
        for raw in acceptance:
            text = str(raw or "").strip()
            m = REFS_RE.search(text)
            if not m:
                continue
            if any(r.lower().endswith(".gd") for r in _split_refs_blob(m.group(1))):
                return True
    return False


def step_headless_e2e_evidence(out_dir: Path, *, expected_run_id: str) -> StepResult:
    root = repo_root()
    date = today_str()
    sc_test_summary = root / "logs" / "ci" / date / "sc-test" / "summary.json"
    e2e_dir = root / "logs" / "e2e" / date / "sc-test" / "gdunit-hard"
    e2e_run_id = e2e_dir / "run_id.txt"

    details: dict[str, Any] = {
        "date": date,
        "expected_run_id": expected_run_id,
        "sc_test_summary": str(sc_test_summary.relative_to(root)).replace("\\", "/"),
        "e2e_dir": str(e2e_dir.relative_to(root)).replace("\\", "/"),
        "e2e_run_id_file": str(e2e_run_id.relative_to(root)).replace("\\", "/"),
    }

    if not sc_test_summary.exists():
        write_json(out_dir / "headless-e2e-evidence.json", {**details, "error": "missing_sc_test_summary"})
        return StepResult(name="headless-e2e-evidence", status="fail", rc=1, details={**details, "error": "missing_sc_test_summary"})

    try:
        parsed = json.loads(sc_test_summary.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        write_json(out_dir / "headless-e2e-evidence.json", {**details, "error": f"invalid_sc_test_summary:{exc}"})
        return StepResult(name="headless-e2e-evidence", status="fail", rc=1, details={**details, "error": f"invalid_sc_test_summary:{exc}"})

    steps = parsed.get("steps") if isinstance(parsed.get("steps"), list) else []
    gdunit = next((s for s in steps if isinstance(s, dict) and s.get("name") == "gdunit-hard"), None)
    details["gdunit_step"] = gdunit
    if not gdunit or int(gdunit.get("rc") or 0) != 0:
        write_json(out_dir / "headless-e2e-evidence.json", {**details, "error": "gdunit_step_missing_or_failed"})
        return StepResult(name="headless-e2e-evidence", status="fail", rc=1, details={**details, "error": "gdunit_step_missing_or_failed"})

    if not e2e_dir.exists() or not e2e_run_id.exists():
        write_json(out_dir / "headless-e2e-evidence.json", {**details, "error": "e2e_artifacts_missing"})
        return StepResult(name="headless-e2e-evidence", status="fail", rc=1, details={**details, "error": "e2e_artifacts_missing"})

    run_id = e2e_run_id.read_text(encoding="utf-8", errors="ignore").strip()
    details["e2e_run_id"] = run_id
    ok = bool(run_id) and run_id == expected_run_id
    write_json(out_dir / "headless-e2e-evidence.json", {**details, "ok": ok})
    return StepResult(name="headless-e2e-evidence", status="ok" if ok else "fail", rc=0 if ok else 1, details={**details, "ok": ok})


def step_tests_all(
    out_dir: Path,
    godot_bin: str | None,
    *,
    run_id: str | None = None,
    test_type: str = "all",
) -> StepResult:
    tt = str(test_type or "").strip().lower() or ("all" if godot_bin else "unit")
    if tt not in ("unit", "all"):
        tt = "all" if godot_bin else "unit"
    cmd = ["py", "-3", "scripts/sc/test.py", "--type", tt]
    if run_id:
        cmd += ["--run-id", str(run_id)]
    if tt != "unit" and godot_bin:
        cmd += ["--godot-bin", godot_bin]
    return run_and_capture(out_dir, "tests-all", cmd, 3_600)
