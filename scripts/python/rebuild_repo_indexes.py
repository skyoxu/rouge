#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rebuild repository "entry indexes" (UTF-8, Windows-friendly).

Why:
- Some docs reference `architecture_base.index` / `docs/index/architecture_base.index`
  and `prd_chunks.index` as stable entry points.
- These indexes should not rely on Node/npm in this repo; use Python only.

Outputs:
1) architecture_base.index (repo root)
   - Plain text, one relative path per line (POSIX slashes).
   - Intended for deterministic tooling / LLM context attachment.

2) docs/index/architecture_base.index (JSONL)
   - One JSON object per line: { path, kind, title, displayTitle }
   - title: YAML front-matter `title` when present, else fallback.
   - displayTitle: first H1 (`# ...`) when present, else fallback.

3) prd_chunks.index (repo root)
   - Plain text, one relative path per line (POSIX slashes).
   - In this repo, PRD is maintained as whole files (not chunks):
     `.taskmaster/docs/prd.txt` (SSoT) + `prd.txt` + `prd_yuan.md` (draft).

Logs:
- logs/ci/<YYYY-MM-DD>/doc-index/rebuild-repo-indexes.json

Usage (Windows):
  py -3 scripts/python/rebuild_repo_indexes.py
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def today_dir() -> str:
    return dt.date.today().isoformat()


def to_posix(relpath: Path) -> str:
    return relpath.as_posix().lstrip("./")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_yaml_front_matter_title(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fm = text[4:end].splitlines()
    for line in fm:
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def first_h1(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def iter_architecture_base_files() -> list[Path]:
    base_dir = REPO_ROOT / "docs" / "architecture" / "base"
    if not base_dir.exists():
        return []
    files = []
    for p in sorted(base_dir.glob("*.md")):
        if p.name.startswith("ZZZ-"):
            continue
        files.append(p)
    return files


def iter_adr_files() -> list[Path]:
    adr_dir = REPO_ROOT / "docs" / "adr"
    if not adr_dir.exists():
        return []
    files = sorted(adr_dir.glob("ADR-*.md"))
    guide = adr_dir / "guide.md"
    if guide.exists():
        files.append(guide)
    return files


def build_architecture_base_index() -> list[str]:
    paths: list[Path] = []
    preferred = [
        REPO_ROOT / "docs" / "PROJECT_DOCUMENTATION_INDEX.md",
        REPO_ROOT / "docs" / "architecture" / "ADR_INDEX_GODOT.md",
    ]
    for p in preferred:
        if p.exists():
            paths.append(p)

    paths.extend(iter_architecture_base_files())
    paths.extend(iter_adr_files())

    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        rel = to_posix(p.relative_to(REPO_ROOT))
        if rel in seen:
            continue
        seen.add(rel)
        out.append(rel)
    return out


def build_architecture_base_jsonl(paths: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for rel in paths:
        p = REPO_ROOT / Path(rel)
        try:
            text = read_text(p)
        except Exception:
            text = ""

        title = parse_yaml_front_matter_title(text) or ""
        display = first_h1(text) or ""
        if not title:
            title = p.stem
        if not display:
            display = title

        kind = "doc"
        if rel.startswith("docs/architecture/base/"):
            kind = "base"
        elif rel.startswith("docs/adr/ADR-"):
            kind = "adr"
        elif rel.startswith("docs/PROJECT_DOCUMENTATION_INDEX.md") or rel.startswith("docs/architecture/ADR_INDEX_GODOT.md"):
            kind = "index"

        out.append({"path": rel, "kind": kind, "title": title, "displayTitle": display})
    return out


def build_prd_index() -> list[str]:
    candidates = [
        ".taskmaster/docs/prd.txt",
        "prd.txt",
        "prd_yuan.md",
    ]
    out: list[str] = []
    for rel in candidates:
        if (REPO_ROOT / rel).exists():
            out.append(rel.replace("\\", "/"))
    return out


def main() -> int:
    arch_paths = build_architecture_base_index()
    prd_paths = build_prd_index()

    arch_txt = "\n".join(arch_paths) + ("\n" if arch_paths else "")
    prd_txt = "\n".join(prd_paths) + ("\n" if prd_paths else "")

    root_arch_index = REPO_ROOT / "architecture_base.index"
    root_prd_index = REPO_ROOT / "prd_chunks.index"
    jsonl_index = REPO_ROOT / "docs" / "index" / "architecture_base.index"

    write_text(root_arch_index, arch_txt)
    write_text(root_prd_index, prd_txt)

    jsonl_items = build_architecture_base_jsonl(arch_paths)
    jsonl_text = "\n".join(json.dumps(x, ensure_ascii=False) for x in jsonl_items) + ("\n" if jsonl_items else "")
    write_text(jsonl_index, jsonl_text)

    report = {
        "date": today_dir(),
        "architecture_base_index": str(root_arch_index.relative_to(REPO_ROOT)).replace("\\", "/"),
        "prd_chunks_index": str(root_prd_index.relative_to(REPO_ROOT)).replace("\\", "/"),
        "architecture_base_jsonl": str(jsonl_index.relative_to(REPO_ROOT)).replace("\\", "/"),
        "counts": {
            "architecture_paths": len(arch_paths),
            "prd_paths": len(prd_paths),
            "architecture_jsonl": len(jsonl_items),
        },
    }

    out_path = REPO_ROOT / "logs" / "ci" / today_dir() / "doc-index" / "rebuild-repo-indexes.json"
    write_json(out_path, report)
    print(f"OK: wrote {report['counts']} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

