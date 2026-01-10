#!/usr/bin/env python3
"""
Ensure Tests.Godot exposes the runtime project as a single source of truth.

Goal:
  When running GdUnit4 from Tests.Godot, paths like res://Game.Godot/... must always
  resolve to the *real* runtime folder at repo root (Game.Godot).

Approach (Windows):
  Create a directory junction:
    Tests.Godot/Game.Godot  ->  ../Game.Godot

This script is deterministic and writes audit artifacts under logs/ci/<date>/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _iso_ts() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).isoformat()


def _run(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.Popen(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out, _ = p.communicate()
    return p.returncode or 0, out


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _safe_resolve(p: Path) -> Path:
    try:
        return p.resolve(strict=True)
    except Exception:
        return p.absolute()


def _rmdir_tree_windows(path: Path) -> tuple[int, str]:
    return _run(["cmd", "/c", "rmdir", "/s", "/q", str(path)])


def _mklink_junction_windows(link: Path, target: Path) -> tuple[int, str]:
    return _run(["cmd", "/c", "mklink", "/J", str(link), str(target)])


def ensure_runtime_link(
    *,
    tests_project: Path,
    runtime_dir: Path,
    force_recreate: bool,
    out_dir: Path,
) -> int:
    link = tests_project / runtime_dir.name
    target = runtime_dir

    log_txt = out_dir / "ensure-junction.log"
    log_json = out_dir / "ensure-junction.json"

    result: dict[str, object] = {
        "ts": _iso_ts(),
        "tests_project": str(tests_project),
        "link": str(link),
        "target": str(target),
        "force_recreate": force_recreate,
        "actions": [],
        "status": "unknown",
    }

    def add_action(action: str, rc: int | None = None, output: str | None = None) -> None:
        item: dict[str, object] = {"action": action}
        if rc is not None:
            item["rc"] = rc
        if output is not None:
            item["output"] = output
        cast_actions = result["actions"]
        assert isinstance(cast_actions, list)
        cast_actions.append(item)

    tests_project.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        msg = f"Runtime dir not found: {target}"
        add_action("validate-target-missing")
        result["status"] = "fail"
        result["error"] = msg
        _write_text(log_txt, msg + "\n")
        _write_json(log_json, result)
        return 2

    target_resolved = _safe_resolve(target)

    if link.exists():
        link_resolved = _safe_resolve(link)
        if os.path.normcase(str(link_resolved)) == os.path.normcase(str(target_resolved)):
            add_action("link-ok")
            result["status"] = "ok"
            _write_text(log_txt, f"OK: {link} -> {target}\n")
            _write_json(log_json, result)
            return 0

        msg = (
            "Existing path blocks junction creation and does not point to runtime.\n"
            f"  link={link}\n"
            f"  link_resolved={link_resolved}\n"
            f"  target={target}\n"
            f"  target_resolved={target_resolved}\n"
        )
        add_action("link-mismatch")
        if not force_recreate:
            result["status"] = "fail"
            result["error"] = msg
            _write_text(log_txt, msg)
            _write_json(log_json, result)
            return 3

        rc_rm, out_rm = _rmdir_tree_windows(link)
        add_action("remove-existing", rc_rm, out_rm)
        if rc_rm != 0 and link.exists():
            result["status"] = "fail"
            result["error"] = f"Failed to remove existing link path: {link}"
            _write_text(log_txt, msg + "\n" + out_rm)
            _write_json(log_json, result)
            return 4

    rc_mk, out_mk = _mklink_junction_windows(link, target)
    add_action("mklink-junction", rc_mk, out_mk)
    if rc_mk != 0 or not link.exists():
        result["status"] = "fail"
        result["error"] = "mklink /J failed"
        _write_text(log_txt, out_mk)
        _write_json(log_json, result)
        return 5

    # Verify
    link_resolved = _safe_resolve(link)
    if os.path.normcase(str(link_resolved)) != os.path.normcase(str(target_resolved)):
        result["status"] = "fail"
        result["error"] = f"Junction created but resolve mismatch: {link_resolved} != {target_resolved}"
        _write_text(log_txt, out_mk + "\n" + str(result["error"]) + "\n")
        _write_json(log_json, result)
        return 6

    result["status"] = "ok"
    _write_text(log_txt, f"OK: {link} -> {target}\n" + out_mk)
    _write_json(log_json, result)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests-project", default="Tests.Godot", help="Tests project directory (relative to repo root, or absolute).")
    ap.add_argument("--runtime-dir", default="Game.Godot", help="Runtime directory at repo root (default Game.Godot), or absolute.")
    ap.add_argument("--force-recreate", action="store_true", help="If link path exists but is wrong, delete and recreate.")
    args = ap.parse_args()

    root = _repo_root()
    tests_arg = Path(args.tests_project)
    runtime_arg = Path(args.runtime_dir)
    tests_project = (tests_arg if tests_arg.is_absolute() else (root / tests_arg)).resolve()
    runtime_dir = (runtime_arg if runtime_arg.is_absolute() else (root / runtime_arg)).resolve()

    date = dt.date.today().strftime("%Y-%m-%d")
    out_dir = root / "logs" / "ci" / date / "gd-tests-junction"

    rc = ensure_runtime_link(
        tests_project=tests_project,
        runtime_dir=runtime_dir,
        force_recreate=args.force_recreate,
        out_dir=out_dir,
    )
    if rc == 0:
        print(f"GD_TESTS_JUNCTION_OK link={tests_project / runtime_dir.name} target={runtime_dir}")
    else:
        print(f"GD_TESTS_JUNCTION_FAIL rc={rc} out={out_dir}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
