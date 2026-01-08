#!/usr/bin/env python3
"""
Deterministic stop-loss check for scripts/sc internal module imports.

Intent:
  Scan Python files under scripts/sc/ for imports like:
    - import _util
    - from _taskmaster import resolve_triplet
  and ensure the corresponding scripts/sc/_*.py modules exist.

Why:
  These sc tools are often copied between repos; missing internal modules cause
  runtime ImportError and waste time. This check fails fast.

Usage (Windows):
  py -3 scripts/python/check_sc_internal_imports.py --out logs/ci/<YYYY-MM-DD>/sc-internal-imports.json
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def iter_sc_py_files(sc_dir: Path) -> list[Path]:
    if not sc_dir.exists():
        return []
    files: list[Path] = []
    for p in sc_dir.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        files.append(p)
    return sorted(files)


def collect_internal_imports(py_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Returns (imports, parse_errors).
    """
    try:
        text = py_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        return [], [f"read_error: {exc}"]

    try:
        tree = ast.parse(text, filename=str(py_path))
    except SyntaxError as exc:
        return [], [f"syntax_error: {exc.msg} at line {exc.lineno} col {exc.offset}"]
    except Exception as exc:  # noqa: BLE001
        return [], [f"parse_error: {exc}"]

    out: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = str(alias.name or "")
                if name.startswith("_") and not name.startswith("__") and "." not in name:
                    out.append({"kind": "import", "module": name, "lineno": getattr(node, "lineno", None)})
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            mod = str(node.module or "")
            if mod.startswith("_") and not mod.startswith("__") and "." not in mod:
                out.append({"kind": "from", "module": mod, "lineno": getattr(node, "lineno", None)})
    return out, []


def main() -> int:
    ap = argparse.ArgumentParser(description="Check scripts/sc internal module imports for missing _*.py files.")
    ap.add_argument("--out", required=True, help="Output JSON path (under logs/ci/... recommended).")
    args = ap.parse_args()

    root = repo_root()
    sc_dir = root / "scripts" / "sc"
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (root / out_path).resolve()

    report: dict[str, Any] = {
        "status": "fail",
        "sc_dir": str(sc_dir.relative_to(root)).replace("\\", "/") if sc_dir.exists() else str(sc_dir).replace("\\", "/"),
        "files_scanned": 0,
        "imports": [],
        "missing_modules": [],
        "errors": [],
    }

    files = iter_sc_py_files(sc_dir)
    report["files_scanned"] = len(files)

    module_refs: dict[str, list[dict[str, Any]]] = {}
    for f in files:
        imports, parse_errors = collect_internal_imports(f)
        rel = str(f.relative_to(root)).replace("\\", "/")
        if parse_errors:
            for e in parse_errors:
                report["errors"].append({"file": rel, "error": e})
            continue
        for imp in imports:
            imp_rec = {"file": rel, **imp}
            report["imports"].append(imp_rec)
            module_refs.setdefault(str(imp.get("module") or ""), []).append(imp_rec)

    missing: list[dict[str, Any]] = []
    for mod, refs in sorted(module_refs.items()):
        if not mod:
            continue
        expected = sc_dir / f"{mod}.py"
        if not expected.exists():
            missing.append(
                {
                    "module": mod,
                    "expected_path": str(expected.relative_to(root)).replace("\\", "/"),
                    "referenced_by": refs,
                }
            )

    report["missing_modules"] = missing
    ok = not missing and not report["errors"]
    report["status"] = "ok" if ok else "fail"
    write_json(out_path, report)

    if ok:
        print(f"SC_INTERNAL_IMPORTS status=ok files={report['files_scanned']} imports={len(report['imports'])}")
        return 0
    print(
        "SC_INTERNAL_IMPORTS status=fail "
        f"files={report['files_scanned']} missing_modules={len(missing)} parse_errors={len(report['errors'])}"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
