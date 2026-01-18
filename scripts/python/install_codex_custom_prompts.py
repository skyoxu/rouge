#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install Codex custom prompts (slash commands) into the user's Codex home.

Codex loads custom prompts from `~/.codex/prompts/*.md`.
Repo files are NOT picked up automatically for `/prompts:<name>`.

This installer supports two sources:
1) Repo-shipped templates: `scripts/codex/prompts/*.md`
2) Optional BMAD agent prompts auto-generated from `_bmad/**/agents/**/*.agent.yaml`

Artifacts (SSoT: logs/**):
  logs/ci/<YYYY-MM-DD>/codex-prompts-install/<run-id>/
    - summary.json
    - summary.log
    - copied_files.txt

Exit code:
  - 0 on success
  - 2 if no prompts were installed (source missing/empty)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple


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


def _read_text_utf8_sig(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig", errors="replace")


def _safe_slug(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9_-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-") or "unknown"


TITLE_RE = re.compile(r"^\s*title\s*:\s*(.+?)\s*$", flags=re.MULTILINE)
NAME_RE = re.compile(r"^\s*name\s*:\s*(.+?)\s*$", flags=re.MULTILINE)


def _extract_agent_title(text: str) -> Optional[str]:
    m = TITLE_RE.search(text)
    if m:
        return m.group(1).strip().strip('"').strip("'")
    return None


def _extract_agent_name(text: str) -> Optional[str]:
    m = NAME_RE.search(text)
    if m:
        return m.group(1).strip().strip('"').strip("'")
    return None


def _agent_prompt_filename(module_name: str, agent_name: str) -> str:
    return f"bmad-{_safe_slug(module_name)}-agents-{_safe_slug(agent_name)}.md"


def _render_agent_prompt_md(
    module_name: str,
    agent_file_rel: str,
    agent_id: str,
    agent_title: str,
) -> str:
    # Keep the prompt content English-only to avoid terminal encoding confusion.
    return "\n".join([
        "---",
        f"description: BMAD agent ({module_name}) {agent_id} - {agent_title}",
        'argument-hint: [TASK_ID=<id>] [FOCUS="<topic>"]',
        "---",
        "",
        "You are working in a Windows-only Godot + C# game repository.",
        "",
        "Project constraints:",
        "- Communication: Chinese. No emoji.",
        "- Work files (code/scripts/tests/log outputs): English only.",
        "- Artifacts: write audit/test outputs under `logs/**`.",
        "- Task truth (SSoT): `.taskmaster/tasks/*.json` (master + view files).",
        "- Overlays: not task SSoT; use overlays only for drift prevention and navigation.",
        "",
        "BMAD agent source:",
        f"- Module: `{module_name}`",
        f"- Agent: `{agent_id}`",
        f"- Definition file: `{agent_file_rel}`",
        "",
        "Instructions:",
        "1) Load and follow the agent definition YAML (persona, principles, critical_actions, menu).",
        "2) If `TASK_ID` is provided, focus only on work mapped to that task and its acceptance criteria.",
        "3) If blocked, stop and report: what failed, where evidence is in `logs/**`, and 2-3 resolution options.",
        "",
        "Inputs:",
        "- TASK_ID: `$TASK_ID` (optional)",
        "- FOCUS: `$FOCUS` (optional)",
        "",
    ]) + "\n"


def _find_bmad_agent_files(repo_root: Path, include_reference: bool) -> List[Tuple[str, Path]]:
    bmad_root = repo_root / "_bmad"
    if not bmad_root.exists():
        return []

    results: List[Tuple[str, Path]] = []
    for agent_file in bmad_root.rglob("*.agent.yaml"):
        rel = agent_file.relative_to(bmad_root).as_posix()

        module_name = rel.split("/", 1)[0]

        if include_reference:
            results.append((module_name, agent_file))
            continue

        # Default: keep only canonical agents: <module>/agents/**.agent.yaml
        # Exclude reference/example agents under workflows/**.
        if "/agents/" not in f"/{rel}":
            continue
        if "/workflows/" in f"/{rel}":
            continue
        results.append((module_name, agent_file))
    return sorted(results, key=lambda x: (x[0], x[1].as_posix()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default="", help="Destination codex prompts directory (default: ~/.codex/prompts)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing prompt files")
    parser.add_argument("--skip-bmad-agents", action="store_true", help="Skip generating BMAD agent prompts from _bmad/**/agents")
    parser.add_argument("--include-bmad-reference", action="store_true", help="Include reference/example agents under _bmad/**/workflows/**")
    args = parser.parse_args()

    repo_root = _repo_root()
    src_dir = repo_root / "scripts" / "codex" / "prompts"

    dest_dir = Path(args.dest) if args.dest else (_codex_home() / "prompts")
    _ensure_dir(dest_dir)

    run_id = f"{int(time.time())}"
    out_dir = repo_root / "logs" / "ci" / _date_local() / "codex-prompts-install" / run_id
    _ensure_dir(out_dir)

    copied_set: set[str] = set()
    skipped_set: set[str] = set()
    overwritten_set: set[str] = set()
    generated_set: set[str] = set()
    errors: List[str] = []

    # 1) Copy repo prompt templates if present.
    if src_dir.exists():
        src_files = sorted([p for p in src_dir.glob("*.md") if p.is_file()])
        for src in src_files:
            dst = dest_dir / src.name
            if dst.exists() and not args.force:
                skipped_set.add(dst.as_posix())
                continue
            if dst.exists() and args.force:
                overwritten_set.add(dst.as_posix())
            shutil.copy2(src, dst)
            copied_set.add(dst.as_posix())

    # 2) Generate BMAD agent prompts (default on).
    if not args.skip_bmad_agents:
        agent_files = _find_bmad_agent_files(repo_root, include_reference=args.include_bmad_reference)
        for module_name, agent_path in agent_files:
            try:
                rel_repo = agent_path.relative_to(repo_root).as_posix()
                agent_id = agent_path.stem.replace(".agent", "")
                raw = _read_text_utf8_sig(agent_path)
                title = _extract_agent_title(raw) or "Agent"
                prompt_name = _agent_prompt_filename(module_name, agent_id)
                dst = dest_dir / prompt_name

                if dst.exists() and not args.force:
                    skipped_set.add(dst.as_posix())
                    continue
                if dst.exists() and args.force:
                    overwritten_set.add(dst.as_posix())

                content = _render_agent_prompt_md(
                    module_name=module_name,
                    agent_file_rel=rel_repo,
                    agent_id=agent_id,
                    agent_title=title,
                )
                dst.write_text(content, encoding="utf-8")
                generated_set.add(dst.as_posix())
            except Exception as e:
                errors.append(f"{agent_path.as_posix()}: {type(e).__name__}: {e}")

    copied = sorted(copied_set)
    generated = sorted(generated_set)
    skipped = sorted(skipped_set)
    overwritten = sorted(overwritten_set)
    all_written = copied + generated
    _write_text(out_dir / "copied_files.txt", "\n".join(all_written) + ("\n" if all_written else ""))
    report = {
        "status": "ok" if (copied or generated) and not errors else ("warn" if (copied or generated) else "fail"),
        "src_dir": src_dir.as_posix(),
        "dest_dir": dest_dir.as_posix(),
        "copied": copied,
        "generated": generated,
        "skipped_existing": skipped,
        "overwritten": overwritten,
        "errors": errors,
        "out_dir": out_dir.as_posix(),
    }
    _write_json(out_dir / "summary.json", report)
    _write_text(
        out_dir / "summary.log",
        f"CODEX_PROMPTS_INSTALL status={report['status']} copied={len(copied)} generated={len(generated)} skipped_existing={len(skipped)} dest={dest_dir.as_posix()} out={out_dir.as_posix()}\n",
    )

    print(f"CODEX_PROMPTS_INSTALL status={report['status']} copied={len(copied)} generated={len(generated)} dest={dest_dir.as_posix()} out={out_dir.as_posix()}")
    return 0 if report["status"] in {"ok", "warn"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
