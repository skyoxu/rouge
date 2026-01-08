#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sc-llm-fill-acceptance-refs: propose acceptance Refs: paths via Codex CLI.

Updates tasks_back.json/tasks_gameplay.json acceptance items and task-level test_refs; does not create tests.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def _bootstrap_imports() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))


_bootstrap_imports()

from _codex_cli import extract_json_object, extract_testing_framework_excerpt, run_codex_exec, truncate  # noqa: E402
from _taskmaster import default_paths, iter_master_tasks, load_json  # noqa: E402
from _util import ci_dir, repo_root, write_json, write_text  # noqa: E402

REFS_RE = re.compile(r"\bRefs\s*:\s*(.+)$", flags=re.IGNORECASE)
ALLOWED_TEST_PREFIXES = ("Game.Core.Tests/", "Tests.Godot/tests/", "Tests/")


def _is_abs_path(path: str) -> bool:
    p = str(path or "").strip()
    if not p:
        return False
    if re.match(r"^[A-Za-z]:[\\/]", p):
        return True
    return p.startswith("/") or p.startswith("\\\\")


def _is_allowed_test_path(path: str) -> bool:
    p = str(path or "").strip().replace("\\", "/")
    if not p or _is_abs_path(p):
        return False
    if p.startswith("../") or "/../" in p:
        return False
    if not (p.lower().endswith(".cs") or p.lower().endswith(".gd")):
        return False
    return any(p.startswith(prefix) for prefix in ALLOWED_TEST_PREFIXES)


def _strip_refs_suffix(text: str) -> str:
    m = REFS_RE.search(text)
    return text[: m.start()].rstrip() if m else text


def _split_refs_blob(blob: str) -> list[str]:
    s = str(blob or "").replace("`", " ").replace(",", " ").replace(";", " ")
    return [p.strip().replace("\\", "/") for p in s.split() if p.strip()]


def _extract_prd_excerpt() -> str:
    root = repo_root()
    parts: list[str] = []
    for name in ["prd.txt", "prd_yuan.md"]:
        p = root / name
        if p.exists():
            parts.append(p.read_text(encoding="utf-8", errors="ignore"))
    return truncate("\n".join(parts).strip(), max_chars=10_000)


def _list_existing_tests() -> list[str]:
    root = repo_root()
    out: list[str] = []
    for base, ext in [("Game.Core.Tests", ".cs"), ("Tests.Godot/tests", ".gd")]:
        p = root / base
        if not p.exists():
            continue
        for f in p.rglob(f"*{ext}"):
            if not f.is_file():
                continue
            rel = str(f.relative_to(root)).replace("\\", "/")
            if _is_allowed_test_path(rel):
                out.append(rel)
    out.sort()
    return out


def _pick_existing_candidates(*, all_tests: list[str], task_id: int, title: str, limit: int) -> list[str]:
    tid = str(task_id)
    by_tid = [p for p in all_tests if re.search(rf"\bTask{re.escape(tid)}\b", p, flags=re.IGNORECASE)]
    if by_tid:
        return by_tid[:limit]
    tokens = [t for t in re.split(r"[^A-Za-z0-9]+", title) if t][:6]
    if not tokens:
        return []
    picked: list[str] = []
    for p in all_tests:
        pl = p.lower()
        if any(tok.lower() in pl for tok in tokens):
            picked.append(p)
            if len(picked) >= limit:
                break
    return picked


def _infer_preferred_kind(*, acceptance_text: str, prefer_gd_by_layer: bool) -> str:
    t = str(acceptance_text or "").lower()
    if any(k in t for k in ["gdunit", "godot", "scene", ".tscn", "ui", "control", "node", "signal", "headless", "input"]):
        return "gd"
    if any(k in t for k in ["xunit", "game.core", "domain", "service", "contracts", "dto"]):
        return "cs"
    return "gd" if prefer_gd_by_layer else "either"


def _is_placeholder_ref(*, task_id: int, path: str) -> bool:
    p = str(path or "").strip().replace("\\", "/")
    if not p:
        return False
    if p.lower().endswith(".cs"):
        return p == f"Game.Core.Tests/Tasks/Task{task_id}RequirementsTests.cs"
    if p.lower().endswith(".gd"):
        return re.search(rf"(?i)(?<!\\d)task{task_id}(?!\\d)", Path(p).name) is not None
    return False


def _default_ref_for(*, task_id: int, prefer_gd: bool) -> str:
    return f"Tests.Godot/tests/UI/test_task{task_id}_acceptance.gd" if prefer_gd else f"Game.Core.Tests/Tasks/Task{task_id}AcceptanceTests.cs"


def _build_prompt(
    *,
    prd_excerpt: str,
    task_id: int,
    title: str,
    master_details: str,
    missing_items: list[dict[str, Any]],
    existing_candidates: list[str],
    max_refs_per_item: int,
) -> str:
    tf_excerpt = extract_testing_framework_excerpt()
    return "\n".join(
        [
            "You propose repo-relative test file paths for acceptance items.",
            "",
            "Output MUST be a single JSON object (no markdown fences):",
            '{ "back": { "0": ["..."] }, "gameplay": { "1": ["...","..."] } }',
            "",
            f"Constraints: paths must be under one of {ALLOWED_TEST_PREFIXES}, end with .cs or .gd, not absolute, no ..",
            f"Max refs per item: {max_refs_per_item}",
            "Prefer .cs for core/domain; prefer .gd for Godot/UI/scene/signal.",
            "",
            f"Task {task_id}: {title}",
            "",
            "Master details:",
            truncate(master_details, max_chars=2_000),
            "",
            "PRD excerpt (may be empty):",
            prd_excerpt,
            "",
            "Testing framework excerpt (may be empty):",
            tf_excerpt,
            "",
            "Existing candidate tests (may be empty):",
            "\n".join(f"- {p}" for p in existing_candidates[:30]),
            "",
            "Input items (0-based index within each view's acceptance list):",
            json.dumps(missing_items, ensure_ascii=False, indent=2),
            "",
            "Return JSON only.",
        ]
    )


def _apply_paths(
    *,
    root: Path,
    entry: dict[str, Any],
    task_id: int,
    paths_by_index: dict[int, list[str]],
    overwrite_existing: bool,
    rewrite_placeholders: bool,
    max_refs_per_item: int,
    prefer_gd: bool,
) -> int:
    acceptance = entry.get("acceptance")
    if not isinstance(acceptance, list):
        return 0

    test_refs = entry.get("test_refs")
    if not isinstance(test_refs, list):
        test_refs = []
    norm_test_refs = [str(x).strip().replace("\\", "/") for x in test_refs if str(x).strip()]

    updated = 0
    new_acceptance: list[str] = []
    for idx, raw in enumerate(acceptance):
        text = str(raw or "").strip()
        m = REFS_RE.search(text)
        had_refs = bool(m)
        existing_refs = _split_refs_blob(m.group(1)) if m else []

        if had_refs and rewrite_placeholders and not any(_is_placeholder_ref(task_id=task_id, path=r) for r in existing_refs):
            new_acceptance.append(text)
            continue
        if had_refs and (not overwrite_existing) and (not rewrite_placeholders):
            new_acceptance.append(text)
            continue

        proposed = paths_by_index.get(idx, [])
        valid = [p.replace("\\", "/") for p in proposed if _is_allowed_test_path(p)]
        if not valid:
            valid = [_default_ref_for(task_id=task_id, prefer_gd=prefer_gd)]

        preferred = _infer_preferred_kind(acceptance_text=text, prefer_gd_by_layer=prefer_gd)
        if preferred == "cs":
            valid = [p for p in valid if p.lower().endswith(".cs")] or valid
        if preferred == "gd":
            valid = [p for p in valid if p.lower().endswith(".gd")] or valid

        chosen = valid[: max(1, min(int(max_refs_per_item), 5))]
        existing = [p for p in chosen if (root / p).exists()]
        chosen = existing if existing else chosen

        base = _strip_refs_suffix(text) if had_refs else text
        new_acceptance.append(f"{base} Refs: {' '.join(chosen)}")
        updated += 1

        for p in chosen:
            if p not in norm_test_refs:
                norm_test_refs.append(p)

    entry["acceptance"] = new_acceptance
    entry["test_refs"] = norm_test_refs
    return updated


def main() -> int:
    ap = argparse.ArgumentParser(description="Fill acceptance Refs: using Codex CLI (LLM).")
    ap.add_argument("--all", action="store_true", help="Process all tasks in tasks_back/tasks_gameplay.")
    ap.add_argument("--task-id", default=None, help="Process a single task id (master id).")
    ap.add_argument("--write", action="store_true", help="Write JSON files in-place. Without this flag, dry-run.")
    ap.add_argument("--overwrite-existing", action="store_true", help="Overwrite existing Refs: in acceptance items.")
    ap.add_argument("--rewrite-placeholders", action="store_true", help="Rewrite existing Refs: when they look like placeholders.")
    ap.add_argument("--timeout-sec", type=int, default=300, help="codex exec timeout per task (default: 300).")
    ap.add_argument("--max-refs-per-item", type=int, default=2, help="Max refs per acceptance item (default: 2).")
    ap.add_argument("--candidate-limit", type=int, default=30, help="Max existing candidate tests to provide to the model.")
    ap.add_argument("--max-tasks", type=int, default=0, help="Optional safety cap; 0 means no limit.")
    args = ap.parse_args()

    root = repo_root()
    out_dir = ci_dir("sc-llm-acceptance-refs")

    tasks_json_p, back_p, gameplay_p = default_paths()
    tasks_json = load_json(tasks_json_p)
    master_by_id = {str(t.get("id")): t for t in iter_master_tasks(tasks_json)}
    back = load_json(back_p)
    gameplay = load_json(gameplay_p)
    if not isinstance(back, list) or not isinstance(gameplay, list):
        print("SC_LLM_ACCEPTANCE_REFS ERROR: tasks_back/tasks_gameplay must be JSON arrays.")
        return 2

    all_tests = _list_existing_tests()
    prd_excerpt = _extract_prd_excerpt()
    back_by_id = {int(t.get("taskmaster_id")): t for t in back if isinstance(t, dict) and isinstance(t.get("taskmaster_id"), int)}
    gameplay_by_id = {
        int(t.get("taskmaster_id")): t for t in gameplay if isinstance(t, dict) and isinstance(t.get("taskmaster_id"), int)
    }

    if args.task_id:
        task_ids = [int(str(args.task_id).split(".", 1)[0])]
    elif args.all:
        task_ids = sorted(set(back_by_id.keys()) | set(gameplay_by_id.keys()))
    else:
        print("SC_LLM_ACCEPTANCE_REFS ERROR: specify --task-id <n> or --all")
        return 2

    if args.max_tasks and int(args.max_tasks) > 0:
        task_ids = task_ids[: int(args.max_tasks)]

    results: list[dict[str, Any]] = []
    updated_total = 0

    for tid in task_ids:
        master = master_by_id.get(str(tid)) or {}
        title = str(master.get("title") or "").strip()
        master_details = str(master.get("details") or "")

        missing: list[dict[str, Any]] = []
        for view_name, entry in [("back", back_by_id.get(tid)), ("gameplay", gameplay_by_id.get(tid))]:
            if not isinstance(entry, dict):
                continue
            acceptance = entry.get("acceptance")
            if not isinstance(acceptance, list):
                continue
            for idx, raw in enumerate(acceptance):
                text = str(raw or "").strip()
                if not text:
                    continue
                m = REFS_RE.search(text)
                if not m:
                    missing.append({"view": view_name, "index": idx, "text": text})
                elif args.rewrite_placeholders:
                    refs = _split_refs_blob(m.group(1))
                    if any(_is_placeholder_ref(task_id=tid, path=r) for r in refs):
                        missing.append({"view": view_name, "index": idx, "text": _strip_refs_suffix(text)})

        if not missing:
            results.append({"task_id": tid, "status": "skipped", "reason": "no_missing_items"})
            continue

        candidates = _pick_existing_candidates(all_tests=all_tests, task_id=tid, title=title, limit=int(args.candidate_limit))
        prompt = _build_prompt(
            prd_excerpt=prd_excerpt,
            task_id=tid,
            title=title,
            master_details=master_details,
            missing_items=missing,
            existing_candidates=candidates,
            max_refs_per_item=int(args.max_refs_per_item),
        )

        prompt_path = out_dir / f"prompt-{tid}.txt"
        last_msg_path = out_dir / f"codex-last-{tid}.txt"
        trace_path = out_dir / f"codex-trace-{tid}.log"
        write_text(prompt_path, prompt)

        rc, trace_out, cmd = run_codex_exec(prompt=prompt, output_last_message=last_msg_path, timeout_sec=int(args.timeout_sec))
        write_text(trace_path, trace_out)
        if rc != 0 or not last_msg_path.exists():
            results.append({"task_id": tid, "status": "fail", "error": "codex_exec_failed", "rc": rc, "cmd": cmd})
            continue

        raw = last_msg_path.read_text(encoding="utf-8", errors="ignore")
        try:
            obj = extract_json_object(raw)
        except Exception as exc:  # noqa: BLE001
            results.append({"task_id": tid, "status": "fail", "error": f"invalid_model_json:{exc}"})
            continue

        def _index_map(v: Any) -> dict[int, list[str]]:
            out: dict[int, list[str]] = {}
            if not isinstance(v, dict):
                return out
            for k, paths in v.items():
                try:
                    idx = int(str(k))
                except ValueError:
                    continue
                if isinstance(paths, list):
                    out[idx] = [str(x) for x in paths]
            return out

        back_map = _index_map(obj.get("back"))
        gameplay_map = _index_map(obj.get("gameplay"))

        updated = 0
        if tid in back_by_id:
            prefer_gd = str((back_by_id[tid] or {}).get("layer") or "").strip().lower() == "ui"
            updated += _apply_paths(
                root=root,
                entry=back_by_id[tid],
                task_id=tid,
                paths_by_index=back_map,
                overwrite_existing=bool(args.overwrite_existing),
                rewrite_placeholders=bool(args.rewrite_placeholders),
                max_refs_per_item=int(args.max_refs_per_item),
                prefer_gd=prefer_gd,
            )
        if tid in gameplay_by_id:
            prefer_gd = str((gameplay_by_id[tid] or {}).get("layer") or "").strip().lower() == "ui"
            updated += _apply_paths(
                root=root,
                entry=gameplay_by_id[tid],
                task_id=tid,
                paths_by_index=gameplay_map,
                overwrite_existing=bool(args.overwrite_existing),
                rewrite_placeholders=bool(args.rewrite_placeholders),
                max_refs_per_item=int(args.max_refs_per_item),
                prefer_gd=prefer_gd,
            )

        updated_total += updated
        results.append({"task_id": tid, "status": "ok", "updated": updated})

    write_json(out_dir / "summary.json", {"cmd": "sc-llm-fill-acceptance-refs", "updated_total": updated_total, "results": results})

    if args.write and updated_total:
        back_p.write_text(json.dumps(back, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        gameplay_p.write_text(json.dumps(gameplay, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"SC_LLM_ACCEPTANCE_REFS status=ok updated={updated_total} out={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
