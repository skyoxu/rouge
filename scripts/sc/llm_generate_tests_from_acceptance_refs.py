#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sc-llm-generate-tests-from-acceptance-refs

Generate missing test files referenced by acceptance "Refs:" using Codex CLI (LLM),
then optionally run deterministic tests (scripts/sc/test.py) to verify.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _bootstrap_imports() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))


_bootstrap_imports()

from _codex_cli import extract_json_object, extract_testing_framework_excerpt, run_codex_exec, truncate  # noqa: E402
from _taskmaster import resolve_triplet  # noqa: E402
from _util import ci_dir, repo_root, run_cmd, write_json, write_text  # noqa: E402

REFS_RE = re.compile(r"\bRefs\s*:\s*(.+)$", flags=re.IGNORECASE)
ALLOWED_TEST_PREFIXES = ("Game.Core.Tests/", "Tests.Godot/tests/", "Tests/")


@dataclass(frozen=True)
class GenResult:
    ref: str
    status: str  # ok|skipped|fail
    rc: int | None = None
    prompt_path: str | None = None
    trace_path: str | None = None
    output_path: str | None = None
    error: str | None = None


def _is_allowed_test_path(path: str) -> bool:
    p = str(path or "").strip().replace("\\", "/")
    if not p:
        return False
    if re.match(r"^[A-Za-z]:[\\/]", p) or p.startswith("/") or p.startswith("\\\\"):
        return False
    if p.startswith("../") or "/../" in p:
        return False
    if not (p.lower().endswith(".cs") or p.lower().endswith(".gd")):
        return False
    return any(p.startswith(prefix) for prefix in ALLOWED_TEST_PREFIXES)


def _split_refs_blob(blob: str) -> list[str]:
    s = str(blob or "").replace("`", " ").replace(",", " ").replace(";", " ")
    return [p.strip().replace("\\", "/") for p in s.split() if p.strip()]


def _collect_refs(triplet: Any) -> dict[str, list[int]]:
    refs: dict[str, list[int]] = {}
    for view in [getattr(triplet, "back", None), getattr(triplet, "gameplay", None)]:
        if not isinstance(view, dict):
            continue
        acceptance = view.get("acceptance") or []
        if not isinstance(acceptance, list):
            continue
        for idx, raw in enumerate(acceptance, start=1):
            text = str(raw or "").strip()
            m = REFS_RE.search(text)
            if not m:
                continue
            for r in _split_refs_blob(m.group(1)):
                if _is_allowed_test_path(r):
                    refs.setdefault(r, []).append(idx)
    return refs


def _build_prompt(*, task_id: str, title: str, details: str, ref: str, acceptance_indices: list[int], red: bool) -> str:
    tf_excerpt = extract_testing_framework_excerpt()
    anchors = " ".join([f"ACC:T{task_id}.{i}" for i in sorted(set(acceptance_indices))])
    kind = "C# xUnit" if ref.lower().endswith(".cs") else "GDScript (GdUnit4)"
    red_hint = "The test MUST fail (red) when executed." if red else "The test SHOULD be meaningful and deterministic."
    return "\n".join(
        [
            f"You generate ONE test file: `{ref}` ({kind}).",
            "Output MUST be a single JSON object (no markdown fences):",
            '{ \"path\": \"...\", \"content\": \"...\" }',
            "",
            "Hard constraints:",
            f"- path MUST equal: {ref}",
            "- content MUST be valid UTF-8 text, use \\n newlines.",
            f"- content MUST include these anchors near a test case: {anchors}",
            f"- {red_hint}",
            "- No TODO placeholders; write runnable test skeletons.",
            "",
            f"Task {task_id}: {title}",
            "",
            "Details (may include acceptance/test_strategy context):",
            truncate(details, max_chars=4_000),
            "",
            "Testing framework excerpt (may be empty):",
            tf_excerpt,
            "",
            "Return JSON only.",
        ]
    )


def _write_file(root: Path, rel: str, content: str) -> None:
    path = (root / rel).resolve()
    if root not in path.parents and path != root:
        raise ValueError(f"ref path escapes repo: {rel}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(content), encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate missing tests from acceptance Refs: using Codex CLI.")
    ap.add_argument("--task-id", required=True, help="Master task id (e.g. 11).")
    ap.add_argument("--tdd-stage", choices=["red-first", "scaffold-only"], default="red-first")
    ap.add_argument("--verify", choices=["none", "unit", "all", "auto"], default="auto")
    ap.add_argument("--godot-bin", default=None, help="Godot mono console path (required for verify=all/auto when .gd refs exist)")
    ap.add_argument("--timeout-sec", type=int, default=600, help="Per-file codex exec timeout (seconds).")
    args = ap.parse_args()

    task_id = str(args.task_id).split(".", 1)[0]
    triplet = resolve_triplet(task_id=task_id)
    out_dir = ci_dir("sc-llm-acceptance-tests")

    refs_map = _collect_refs(triplet)
    refs = sorted(refs_map.keys())
    if not refs:
        print(f"SC_LLM_ACCEPTANCE_TESTS status=skipped reason=no_refs task_id={task_id} out={out_dir}")
        write_json(out_dir / f"summary-{task_id}.json", {"status": "skipped", "reason": "no_refs", "task_id": task_id})
        return 0

    primary = next((r for r in refs if r.lower().endswith(".cs")), refs[0])
    order = [primary] + [r for r in refs if r != primary] if args.tdd_stage == "red-first" else refs

    title = str(triplet.master.get("title") or "").strip()
    details_blob = "\n".join(
        [
            str(triplet.master.get("details") or ""),
            str((triplet.back or {}).get("details") or ""),
            str((triplet.gameplay or {}).get("details") or ""),
        ]
    )

    results: list[dict[str, Any]] = []
    hard_fail = False
    wrote_any = False

    root = repo_root()
    for ref in order:
        ref_norm = ref.replace("\\", "/")
        target = root / ref_norm
        if target.exists():
            results.append(GenResult(ref=ref_norm, status="skipped").__dict__)
            continue

        # Strict red-first: any newly generated test file must be red in current repo state.
        red = bool(args.tdd_stage == "red-first")
        prompt = _build_prompt(
            task_id=task_id,
            title=title,
            details=details_blob,
            ref=ref_norm,
            acceptance_indices=refs_map.get(ref_norm, []),
            red=red,
        )

        prompt_path = out_dir / f"prompt-{task_id}-{Path(ref_norm).name}.txt"
        last_msg_path = out_dir / f"codex-last-{task_id}-{Path(ref_norm).name}.txt"
        trace_path = out_dir / f"codex-trace-{task_id}-{Path(ref_norm).name}.log"
        write_text(prompt_path, prompt)

        rc, trace_out, cmd = run_codex_exec(prompt=prompt, output_last_message=last_msg_path, timeout_sec=int(args.timeout_sec))
        write_text(trace_path, trace_out)
        if rc != 0 and last_msg_path.exists():
            # Codex exec may time out but still have produced a usable last message file.
            # In that case, prefer making forward progress by attempting to parse and write the test file.
            pass
        elif rc != 0 or not last_msg_path.exists():
            hard_fail = True
            results.append(
                GenResult(
                    ref=ref_norm,
                    status="fail",
                    rc=rc,
                    prompt_path=str(prompt_path),
                    trace_path=str(trace_path),
                    output_path=str(last_msg_path),
                    error=f"codex_exec_failed rc={rc} cmd={' '.join(cmd)}",
                ).__dict__
            )
            continue

        raw = last_msg_path.read_text(encoding="utf-8", errors="ignore")
        try:
            obj = extract_json_object(raw)
        except Exception as exc:  # noqa: BLE001
            hard_fail = True
            results.append(
                GenResult(
                    ref=ref_norm,
                    status="fail",
                    prompt_path=str(prompt_path),
                    trace_path=str(trace_path),
                    output_path=str(last_msg_path),
                    error=f"invalid_model_json:{exc}",
                ).__dict__
            )
            continue

        out_path = str(obj.get("path") or "").strip().replace("\\", "/")
        content = obj.get("content")
        if out_path != ref_norm or not isinstance(content, str):
            hard_fail = True
            results.append(
                GenResult(
                    ref=ref_norm,
                    status="fail",
                    prompt_path=str(prompt_path),
                    trace_path=str(trace_path),
                    output_path=str(last_msg_path),
                    error="model_output_missing_path_or_content",
                ).__dict__
            )
            continue

        try:
            _write_file(root, ref_norm, content)
            wrote_any = True
            status_rc = 0 if rc == 0 else int(rc)
            status = "ok" if rc == 0 else "ok_with_codex_rc"
            results.append(
                GenResult(
                    ref=ref_norm,
                    status=status,
                    rc=status_rc,
                    prompt_path=str(prompt_path),
                    trace_path=str(trace_path),
                    output_path=str(last_msg_path),
                    error=None if rc == 0 else f"codex_exec_nonzero_rc_but_output_used rc={rc}",
                ).__dict__
            )
        except Exception as exc:  # noqa: BLE001
            hard_fail = True
            results.append(GenResult(ref=ref_norm, status="fail", prompt_path=str(prompt_path), trace_path=str(trace_path), output_path=str(last_msg_path), error=f"write_failed:{exc}").__dict__)

    verify = str(args.verify)
    has_gd = any(r.lower().endswith(".gd") for r in refs)
    if verify == "auto":
        verify = "all" if has_gd else "unit"

    verify_rc = None
    verify_log = None
    if verify != "none" and wrote_any and not hard_fail:
        cmd = ["py", "-3", "scripts/sc/test.py", "--type", "all" if verify == "all" else "unit"]
        godot_bin = args.godot_bin
        if verify == "all":
            if not godot_bin:
                print("SC_LLM_ACCEPTANCE_TESTS ERROR: --godot-bin required for verify=all")
                hard_fail = True
            else:
                cmd += ["--godot-bin", godot_bin]
        if not hard_fail:
            verify_rc, out = run_cmd(cmd, cwd=repo_root(), timeout_sec=3_600)
            verify_log_path = out_dir / f"verify-{task_id}.log"
            write_text(verify_log_path, out)
            verify_log = str(verify_log_path)
            if args.tdd_stage == "red-first":
                if verify_rc == 0:
                    hard_fail = True
            else:
                if verify_rc != 0:
                    hard_fail = True

    payload: dict[str, Any] = {
        "cmd": "sc-llm-generate-tests-from-acceptance-refs",
        "task_id": task_id,
        "tdd_stage": args.tdd_stage,
        "verify": args.verify,
        "status": "fail" if hard_fail else "ok",
        "results": results,
    }
    if verify_rc is not None:
        payload["verify_rc"] = verify_rc
    if verify_log:
        payload["verify_log"] = verify_log
    write_json(out_dir / f"summary-{task_id}.json", payload)

    print(f"SC_LLM_ACCEPTANCE_TESTS status={payload['status']} task_id={task_id} out={out_dir}")
    return 0 if not hard_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
