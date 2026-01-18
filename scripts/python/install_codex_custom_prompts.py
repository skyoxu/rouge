#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install repo-shipped Codex custom prompts into the user's Codex home.

Why:
  - Codex CLI custom prompts are loaded from `~/.codex/prompts/*.md`.
  - Repo files are not automatically picked up for `/prompts:<name>` commands.
  - This script copies prompt templates from `scripts/codex/prompts/` into the
    user's Codex home directory so they show up as slash commands.

Artifacts (SSoT: logs/**):
  logs/ci/<YYYY-MM-DD>/codex-prompts-install/<run-id>/
    - summary.json
    - summary.log
    - copied_files.txt

Exit code:
  - 0 on success
  - 2 if source prompt folder is missing or empty
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, List


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _date_local() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _codex_home() -> Path:
    userprofile = os.environ.get("USERPROFILE")
    if not userprofile:
        return Path.home() / ".codex"
    return Path(userprofile) / ".codex"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default="", help="Destination codex prompts directory (default: ~/.codex/prompts)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing prompt files")
    args = parser.parse_args()

    repo_root = _repo_root()
    src_dir = repo_root / "scripts" / "codex" / "prompts"
    if not src_dir.exists():
        print(f"CODEX_PROMPTS_INSTALL status=missing src={src_dir.as_posix()}")
        return 2

    src_files = sorted([p for p in src_dir.glob("*.md") if p.is_file()])
    if not src_files:
        print(f"CODEX_PROMPTS_INSTALL status=empty src={src_dir.as_posix()}")
        return 2

    dest_dir = Path(args.dest) if args.dest else (_codex_home() / "prompts")
    _ensure_dir(dest_dir)

    run_id = f"{int(time.time())}"
    out_dir = repo_root / "logs" / "ci" / _date_local() / "codex-prompts-install" / run_id
    _ensure_dir(out_dir)

    copied: List[str] = []
    skipped: List[str] = []
    overwritten: List[str] = []

    for src in src_files:
        dst = dest_dir / src.name
        if dst.exists() and not args.force:
            skipped.append(dst.as_posix())
            continue
        if dst.exists() and args.force:
            overwritten.append(dst.as_posix())
        shutil.copy2(src, dst)
        copied.append(dst.as_posix())

    _write_text(out_dir / "copied_files.txt", "\n".join(copied) + ("\n" if copied else ""))
    report = {
        "status": "ok",
        "src_dir": src_dir.as_posix(),
        "dest_dir": dest_dir.as_posix(),
        "copied": copied,
        "skipped_existing": skipped,
        "overwritten": overwritten,
        "out_dir": out_dir.as_posix(),
    }
    _write_json(out_dir / "summary.json", report)
    _write_text(
        out_dir / "summary.log",
        f"CODEX_PROMPTS_INSTALL status=ok copied={len(copied)} skipped_existing={len(skipped)} dest={dest_dir.as_posix()} out={out_dir.as_posix()}\n",
    )

    print(f"CODEX_PROMPTS_INSTALL status=ok copied={len(copied)} dest={dest_dir.as_posix()} out={out_dir.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

