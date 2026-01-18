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
    return bool(re.search(r"^" + re.escape(key) + r"\s*:\s*", fm, flags=re.MULTILINE))


def parse_title_status(fm: str) -> tuple[str, str]:
    title = ""
    status = ""
    for line in fm.splitlines():
        if line.startswith("Title:"):
            title = line.split(":", 1)[1].strip()
        if line.startswith("Status:"):
            status = line.split(":", 1)[1].strip()
    return title, status


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def find_md_links(md_body: str) -> list[str]:
    links: list[str] = []
    for _label, target in LINK_RE.findall(md_body):
        target = target.strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("#"):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        if "*" in target or "?" in target:
            continue
        if target.lower().endswith(".md"):
            links.append(target)
    return links


def extract_scope_hint(body: str) -> str:
    lines = [ln.strip() for ln in body.splitlines()]
    for i, ln in enumerate(lines):
        if ln.lower().startswith("## scope"):
            for j in range(i + 1, min(i + 8, len(lines))):
                if not lines[j]:
                    continue
                if lines[j].startswith("#"):
                    break
                return lines[j][:120]
    return ""


def ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _is_probable_glob_link(target: str) -> bool:
    # Markdown in _index.md sometimes uses "08/*.md" style glob patterns as documentation.
    # Treat these as non-actionable and do not validate as file links.
    return bool(re.search(r"[*?]|\b\*\b", target)) or bool(re.search(r"/\d+\*/", target))


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

    for md in md_files:
        text = read_text_utf8_sig(md)

        if "\ufffd" in text:
            replacement_chars.append({"file": md.as_posix()})

        split = split_front_matter(text)
        if split is None:
            missing_front_matter.append({"file": md.as_posix(), "missing": list(REQUIRED_FM_KEYS)})
            continue

        fm, body = split

        missing_keys = [k for k in REQUIRED_FM_KEYS if not fm_has_key(fm, k)]
        if missing_keys:
            missing_front_matter.append({"file": md.as_posix(), "missing": missing_keys})

        title, status = parse_title_status(fm)
        if status and status not in ALLOWED_STATUS:
            bad_status.append({"file": md.as_posix(), "status": status, "allowed": sorted(ALLOWED_STATUS)})

        scope_hint = extract_scope_hint(body)
        pages.append(MdPage(path=md, title=title or md.name, status=status or "", scope_hint=scope_hint))

        for link in find_md_links(body):
            if _is_probable_glob_link(link):
                continue
            target_path = (md.parent / link).resolve()
            try:
                target_path.relative_to(md.parent.resolve())
            except ValueError:
                broken_links.append({"file": md.as_posix(), "link": link, "reason": "link escapes overlay folder"})
                continue
            if not target_path.exists():
                broken_links.append({"file": md.as_posix(), "link": link, "reason": "target missing"})

    catalog_lines: list[str] = [
        f"# Overlay 08 Catalog ({args.prd_id})",
        "",
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"- Source: {overlay_dir.as_posix()}",
        "",
        "## Pages",
    ]
    for p in pages:
        hint = f" - {p.scope_hint}" if p.scope_hint else ""
        status = f"[{p.status}] " if p.status else ""
        catalog_lines.append(f"- {status}`{p.path.name}`: {p.title}{hint}")
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
