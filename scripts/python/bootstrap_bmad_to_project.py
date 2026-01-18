#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bootstrap BMAD project folder (`_bmad/`) from the globally installed `bmad-method`.

Context / stop-loss:
  - BMAD v6 installs BMAD assets per-project (default folder name: `_bmad`).
  - Many users assume a "user-level .bmad" exists; in practice it often does not.
  - This script copies the BMAD assets shipped inside the npm global package
    into the current repo so tools/LLMs can read them locally.
  - It does NOT run the interactive `bmad install` flow.

What it copies (from bmad-method package):
  - src/core    -> <repo>/_bmad/core
  - src/modules -> <repo>/_bmad/<moduleName> (e.g. bmgd, bmm, ...)
  - src/utility -> <repo>/_bmad/utility

Artifacts (SSoT: logs/**):
  logs/ci/<YYYY-MM-DD>/bmad-bootstrap/<run-id>/
    - summary.json
    - summary.log
    - copied_files.txt

Exit code:
  - 0 on success
  - 2 if bmad-method source directory is not found
  - 3 if destination already exists and --force is not set
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _date_local() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _default_bmad_method_src() -> Path:
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return Path("")
    return Path(appdata) / "npm" / "node_modules" / "bmad-method" / "src"


def _iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p


@dataclass(frozen=True)
class CopyResult:
    copied: int
    skipped: int
    files: List[str]


def _copy_tree(src: Path, dst: Path) -> CopyResult:
    copied = 0
    skipped = 0
    files: List[str] = []

    for f in _iter_files(src):
        rel = f.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            skipped += 1
            continue
        shutil.copy2(f, out)
        copied += 1
        files.append(out.as_posix())

    return CopyResult(copied=copied, skipped=skipped, files=files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="", help="Source directory of bmad-method src (default: %APPDATA%/npm/node_modules/bmad-method/src)")
    parser.add_argument("--dest", default="_bmad", help="Destination folder under repo root (default: _bmad)")
    parser.add_argument("--force", action="store_true", help="Allow overwriting existing destination folder (will delete it first)")
    args = parser.parse_args()

    repo_root = _repo_root()
    src_root = Path(args.source) if args.source else _default_bmad_method_src()
    if not src_root.exists():
        print(f"BMAD_BOOTSTRAP status=missing source={src_root.as_posix()}")
        return 2

    dest_root = (repo_root / args.dest).resolve()
    if dest_root.exists():
        if not args.force:
            print(f"BMAD_BOOTSTRAP status=exists dest={dest_root.as_posix()}")
            return 3
        shutil.rmtree(dest_root)

    run_id = f"{int(time.time())}"
    out_dir = repo_root / "logs" / "ci" / _date_local() / "bmad-bootstrap" / run_id
    _ensure_dir(out_dir)

    # Copy core + utility
    summary_items: List[Tuple[str, CopyResult]] = []
    core_src = src_root / "core"
    util_src = src_root / "utility"
    modules_src = src_root / "modules"

    if core_src.exists():
        summary_items.append(("core", _copy_tree(core_src, dest_root / "core")))
    if util_src.exists():
        summary_items.append(("utility", _copy_tree(util_src, dest_root / "utility")))

    # Copy each module folder to dest_root/<moduleName>
    if modules_src.exists():
        for module_dir in sorted([p for p in modules_src.iterdir() if p.is_dir()]):
            summary_items.append((module_dir.name, _copy_tree(module_dir, dest_root / module_dir.name)))

    copied_files: List[str] = []
    total_copied = 0
    total_skipped = 0
    per_section = []
    for name, r in summary_items:
        total_copied += r.copied
        total_skipped += r.skipped
        copied_files.extend(r.files)
        per_section.append({"section": name, "copied": r.copied, "skipped_existing": r.skipped})

    _write_text(out_dir / "copied_files.txt", "\n".join(copied_files) + ("\n" if copied_files else ""))
    report = {
        "status": "ok",
        "source": src_root.as_posix(),
        "dest": dest_root.as_posix(),
        "sections": per_section,
        "totals": {"copied": total_copied, "skipped_existing": total_skipped},
        "out_dir": out_dir.as_posix(),
    }
    _write_json(out_dir / "summary.json", report)
    _write_text(
        out_dir / "summary.log",
        f"BMAD_BOOTSTRAP status=ok copied={total_copied} skipped_existing={total_skipped} dest={dest_root.as_posix()} out={out_dir.as_posix()}\n",
    )

    print(f"BMAD_BOOTSTRAP status=ok copied={total_copied} dest={dest_root.as_posix()} out={out_dir.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

