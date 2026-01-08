from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from _util import repo_root

AUTO_BEGIN = "<!-- BEGIN AUTO:TEST_ORG_NAMING_REFS -->"
AUTO_END = "<!-- END AUTO:TEST_ORG_NAMING_REFS -->"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def truncate(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def extract_testing_framework_excerpt() -> str:
    path = repo_root() / "docs" / "testing-framework.md"
    if not path.exists():
        return ""
    text = read_text(path)
    a = text.find(AUTO_BEGIN)
    b = text.find(AUTO_END)
    if a < 0 or b < 0 or b <= a:
        return ""
    return text[a + len(AUTO_BEGIN) : b].strip()


def extract_json_object(text: str) -> dict[str, Any]:
    text = str(text or "").strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in model output.")
    obj = json.loads(m.group(0))
    if not isinstance(obj, dict):
        raise ValueError("Model output JSON is not an object.")
    return obj


def run_codex_exec(
    *,
    prompt: str,
    output_last_message: Path,
    timeout_sec: int,
    sandbox: str = "read-only",
) -> tuple[int, str, list[str]]:
    exe = shutil.which("codex")
    if not exe:
        return 127, "codex executable not found in PATH\n", ["codex"]
    cmd = [
        exe,
        "exec",
        "-s",
        str(sandbox),
        "-C",
        str(repo_root()),
        "--output-last-message",
        str(output_last_message),
        "-",
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=str(repo_root()),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=int(timeout_sec),
        )
    except subprocess.TimeoutExpired:
        return 124, "codex exec timeout\n", cmd
    except Exception as exc:  # noqa: BLE001
        return 1, f"codex exec failed to start: {exc}\n", cmd
    return int(proc.returncode or 0), str(proc.stdout or ""), cmd

