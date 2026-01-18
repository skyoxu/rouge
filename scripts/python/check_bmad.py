#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministic check: verify BMAD CLI availability without PowerShell npm.ps1.

This script is intended for local diagnostics (optional).
It writes artifacts under logs/ci/** and does not act as a hard gate.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _date_local() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> int:
    repo_root = _repo_root()
    run_id = f"{int(time.time())}"
    out_dir = repo_root / "logs" / "ci" / _date_local() / "bmad-check" / run_id
    _ensure_dir(out_dir)

    bmad = shutil.which("bmad")
    cmd = ["cmd.exe", "/c", "bmad --version"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)

    report = {
        "status": "ok" if (bmad and proc.returncode == 0) else ("missing" if not bmad else "fail"),
        "bmad_on_path": bmad,
        "rc": proc.returncode,
        "out_dir": out_dir.as_posix(),
    }
    _write_json(out_dir / "summary.json", report)
    _write_text(out_dir / "stdout.log", proc.stdout)
    _write_text(out_dir / "stderr.log", proc.stderr)
    _write_text(out_dir / "summary.log", f"BMAD_CHECK status={report['status']} rc={report['rc']} out={report['out_dir']}\n")

    print(f"BMAD_CHECK status={report['status']} rc={report['rc']} out={report['out_dir']}")
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())

