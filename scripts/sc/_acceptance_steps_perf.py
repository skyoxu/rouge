from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from _step_result import StepResult
from _util import repo_root, write_json

PERF_METRICS_RE = re.compile(
    r"\[PERF\]\s*frames=(\d+)\s+avg_ms=([0-9]+(?:\.[0-9]+)?)\s+p50_ms=([0-9]+(?:\.[0-9]+)?)\s+p95_ms=([0-9]+(?:\.[0-9]+)?)\s+p99_ms=([0-9]+(?:\.[0-9]+)?)"
)


def find_latest_headless_log() -> Path | None:
    ci_root = repo_root() / "logs" / "ci"
    if not ci_root.exists():
        return None
    candidates = list(ci_root.rglob("headless.log"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def step_perf_budget(out_dir: Path, *, max_p95_ms: int) -> StepResult:
    root = repo_root()
    headless_log = find_latest_headless_log()
    if not headless_log:
        details = {
            "status": "disabled" if max_p95_ms <= 0 else "enabled",
            "error": "no recent headless.log found under logs/ci (run smoke first)",
            "max_p95_ms": max_p95_ms,
        }
        write_json(out_dir / "perf-budget.json", details)
        return StepResult(name="perf-budget", status="skipped" if max_p95_ms <= 0 else "fail", details=details)

    content = headless_log.read_text(encoding="utf-8", errors="ignore")
    matches = list(PERF_METRICS_RE.finditer(content))
    if not matches:
        details = {
            "status": "disabled" if max_p95_ms <= 0 else "enabled",
            "error": "no [PERF] metrics found in headless.log",
            "headless_log": str(headless_log.relative_to(root)).replace("\\", "/"),
            "max_p95_ms": max_p95_ms,
        }
        write_json(out_dir / "perf-budget.json", details)
        return StepResult(name="perf-budget", status="skipped" if max_p95_ms <= 0 else "fail", details=details)

    last = matches[-1]
    frames = int(last.group(1))
    p95_ms = float(last.group(4))
    details: dict[str, Any] = {
        "headless_log": str(headless_log.relative_to(root)).replace("\\", "/"),
        "frames": frames,
        "p95_ms": p95_ms,
        "max_p95_ms": max_p95_ms,
        "budget_status": ("disabled" if max_p95_ms <= 0 else ("pass" if p95_ms <= max_p95_ms else "fail")),
        "note": "Extracts latest [PERF] metrics from headless.log; becomes a hard gate only when max_p95_ms > 0.",
    }
    write_json(out_dir / "perf-budget.json", details)
    if max_p95_ms <= 0:
        return StepResult(name="perf-budget", status="skipped", details=details)
    return StepResult(name="perf-budget", status="ok" if p95_ms <= max_p95_ms else "fail", details=details)

