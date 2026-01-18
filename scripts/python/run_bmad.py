#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run BMAD CLI via cmd.exe to avoid PowerShell execution policy issues.

Why:
  - On some Windows machines, `npm.ps1` / `npx.ps1` are blocked by ExecutionPolicy.
  - `bmad` is installed as a .cmd shim (npm global bin), so it should be executed via cmd.exe.

This script:
  - Locates `bmad` on PATH
  - Executes `cmd.exe /c bmad <args...>`
  - Writes auditable artifacts under logs/ci/<YYYY-MM-DD>/bmad/<run-id>/

Exit codes:
  - 0: BMAD command succeeded
  - 2: BMAD not found on PATH
  - otherwise: propagated process return code
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_local() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _cmdline(args: List[str]) -> str:
    return subprocess.list2cmdline(args)


@dataclass(frozen=True)
class RunResult:
    rc: int
    stdout: str
    stderr: str


def run_bmad(args: List[str]) -> RunResult:
    bmad = shutil.which("bmad")
    if not bmad:
        return RunResult(rc=2, stdout="", stderr="bmad not found on PATH")

    # Use cmd.exe to run .cmd shims reliably.
    cmd = ["cmd.exe", "/c", _cmdline(["bmad", *args])]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    return RunResult(rc=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--out-dir",
        default="",
        help="Optional output directory. Default: logs/ci/<date>/bmad/<run-id>/",
    )
    parser.add_argument(
        "bmad_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to BMAD after `--`, e.g. `-- install` or `-- --version`.",
    )
    ns = parser.parse_args()

    args = ns.bmad_args
    if args and args[0] == "--":
        args = args[1:]

    repo_root = _repo_root()
    run_id = f"{int(time.time())}"
    default_out = repo_root / "logs" / "ci" / _date_local() / "bmad" / run_id
    out_dir = Path(ns.out_dir) if ns.out_dir else default_out
    _ensure_dir(out_dir)

    meta = {
        "tool": "bmad",
        "started_at_utc": _utc_ts(),
        "cwd": str(Path.cwd()),
        "repo_root": str(repo_root),
        "args": args,
        "bmad_on_path": shutil.which("bmad"),
        "node_on_path": shutil.which("node"),
    }
    _write_json(out_dir / "meta.json", meta)

    result = run_bmad(args)
    _write_text(out_dir / "stdout.log", result.stdout)
    _write_text(out_dir / "stderr.log", result.stderr)

    summary = {
        "status": "ok" if result.rc == 0 else ("missing" if result.rc == 2 else "fail"),
        "rc": result.rc,
        "out_dir": out_dir.as_posix(),
    }
    _write_json(out_dir / "summary.json", summary)
    _write_text(
        out_dir / "summary.log",
        f"BMAD_RUN status={summary['status']} rc={summary['rc']} out={summary['out_dir']}\n",
    )

    # Keep stdout ASCII-only to avoid terminal encoding confusion.
    print(f"BMAD_RUN status={summary['status']} rc={summary['rc']} out={summary['out_dir']}")
    return result.rc


if __name__ == "__main__":
    raise SystemExit(main())
