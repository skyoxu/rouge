#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Overlay 08 catalog/audit generator.

This script audits docs/architecture/overlays/<PRD-ID>/08/*.md for:
  - Required Front-Matter keys (schema consistency)
  - Broken intra-folder links to *.md
  - Replacement character U+FFFD (often indicates encoding/copy issues)

It also generates a lightweight catalog.md for human browsing.

Outputs (default):
  logs/ci/<YYYY-MM-DD>/overlay-08-audit/summary.json
  logs/ci/<YYYY-MM-DD>/overlay-08-audit/summary.log
  logs/ci/<YYYY-MM-DD>/overlay-08-audit/catalog.md
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_FM_KEYS = ("PRD-ID", "Title", "Status", "ADR-Refs", "Arch-Refs", "Test-Refs")
ALLOWED_STATUS = {"Active", "Proposed", "Template"}


@dataclass(frozen=True)
class MdPage:
    path: Path
    title: str
    status: str
    scope_hint: str


def read_text_utf8_sig(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig", errors="replace")


def split_front_matter(text: str) -> tuple[str, str] | None:
    if not text.startswith("---"):
        return None
    lines = text.splitlines(True)
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    fm = "".join(lines[: end + 1])
    body = "".join(lines[end + 1 :])
    return fm, body


def fm_has_key(fm: str, key: str) -> bool:
    return bool(re.search(r"^" + re.escape(key) + r"\s*:", fm, re.M))


def fm_get_scalar(fm: str, key: str) -> str | None:
    m = re.search(r"^" + re.escape(key) + r"\s*:\s*(.+?)\s*$", fm, re.M)
    if not m:
        return None
    return m.group(1).strip()


def extract_scope_hint(body: str) -> str:
    # Heuristic: first bullet under "## Scope".
    lines = body.splitlines()
    in_scope = False
    for ln in lines:
        if ln.strip() == "## Scope":
            in_scope = True
            continue
        if in_scope:
            if ln.startswith("## "):
                return ""
            m = re.match(r"^\s*-\s*(.+?)\s*$", ln)
            if m:
                return m.group(1).strip()
    return ""


def find_md_links(text: str) -> set[str]:
    # Minimal patterns for local md links: (foo.md) and `foo.md`
    out = set(re.findall(r"\(([^)]+\.md)\)", text))
    out |= set(re.findall(r"`([^`]+\.md)`", text))
    # Ignore globs like `08/*.md` used in guidelines.
    return {x for x in out if "*" not in x and "?" not in x}


def ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prd-id", default="PRD-rouge-manager", help="Overlay PRD-ID directory name (default: PRD-rouge-manager)")
    parser.add_argument(
        "--out-dir",
        default="",
        help="Optional output directory (default: logs/ci/<date>/overlay-08-audit)",
    )
    args = parser.parse_args()

    overlay_dir = Path("docs/architecture/overlays") / args.prd_id / "08"
    md_files = sorted(overlay_dir.glob("*.md"))

    if not overlay_dir.exists():
        raise SystemExit(f"overlay dir not found: {overlay_dir}")

    date = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(args.out_dir) if args.out_dir else (Path("logs/ci") / date / "overlay-08-audit")
    ensure_out_dir(out_dir)

    missing_front_matter: list[dict[str, Any]] = []
    broken_links: list[dict[str, Any]] = []
    replacement_chars: list[dict[str, Any]] = []
    bad_status: list[dict[str, Any]] = []
    pages: list[MdPage] = []

    for p in md_files:
        text = read_text_utf8_sig(p)
        if "\ufffd" in text:
            for i, ln in enumerate(text.splitlines(), 1):
                if "\ufffd" in ln:
                    replacement_chars.append({"file": str(p).replace("\\", "/"), "line": i, "text": ln[:200]})

        fm_split = split_front_matter(text)
        if fm_split is None:
            missing_front_matter.append({"file": str(p).replace("\\", "/"), "missing": list(REQUIRED_FM_KEYS)})
            continue

        fm, body = fm_split
        missing_keys = [k for k in REQUIRED_FM_KEYS if not fm_has_key(fm, k)]
        if missing_keys:
            missing_front_matter.append({"file": str(p).replace("\\", "/"), "missing": missing_keys})

        title = fm_get_scalar(fm, "Title") or p.name
        status = fm_get_scalar(fm, "Status") or ""
        if status not in ALLOWED_STATUS:
            bad_status.append({"file": str(p).replace("\\", "/"), "status": status})
            status = status if status else "Proposed"

        scope_hint = extract_scope_hint(body)
        pages.append(MdPage(path=p, title=title, status=status, scope_hint=scope_hint))

        for t in sorted(find_md_links(text)):
            name = Path(t).name
            if name.endswith(".md") and not (overlay_dir / name).exists():
                broken_links.append({"file": str(p).replace("\\", "/"), "link": t})

    catalog_lines: list[str] = []
    catalog_lines.append(f"# Overlay 08 Catalog ({args.prd_id})")
    catalog_lines.append("")
    catalog_lines.append(f"- dir: `{overlay_dir.as_posix()}`")
    catalog_lines.append(f"- generated_at: `{datetime.now().isoformat(timespec='seconds')}`")
    catalog_lines.append("")
    catalog_lines.append("## Pages")
    for page in sorted(pages, key=lambda x: (x.status, x.path.name)):
        hint = f" - {page.scope_hint}" if page.scope_hint else ""
        catalog_lines.append(f"- `{page.path.name}` ({page.status}): {page.title}{hint}")

    write_text(out_dir / "catalog.md", "\n".join(catalog_lines) + "\n")

    report = {
        "status": "ok" if not (missing_front_matter or broken_links or replacement_chars or bad_status) else "warn",
        "overlay_dir": overlay_dir.as_posix(),
        "md_files": len(md_files),
        "required_front_matter_keys": list(REQUIRED_FM_KEYS),
        "missing_front_matter": missing_front_matter,
        "bad_status": bad_status,
        "broken_links": broken_links,
        "replacement_chars": replacement_chars,
        "out_dir": out_dir.as_posix(),
    }

    write_json(out_dir / "summary.json", report)

    summary_lines = [
        f"OVERLAY_08_AUDIT status={report['status']}",
        f"dir={report['overlay_dir']}",
        f"md_files={report['md_files']}",
        f"missing_front_matter={len(missing_front_matter)}",
        f"bad_status={len(bad_status)}",
        f"broken_links={len(broken_links)}",
        f"replacement_chars={len(replacement_chars)}",
        f"out={out_dir.as_posix()}",
    ]
    write_text(out_dir / "summary.log", "\n".join(summary_lines) + "\n")

    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
