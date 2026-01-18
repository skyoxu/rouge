#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]

TEXT_EXTS = {".md", ".txt", ".yml", ".yaml", ".json", ".toml", ".feature"}

SKIP_DIR_NAMES = {
    ".git",
    ".godot",
    "build",
    "logs",
    "tmp",
    "_tmp",
    "TestResults",
    "demo",
}


@dataclass(frozen=True)
class Change:
    file: str
    removed: int


def today_dir() -> str:
    return dt.date.today().isoformat()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_dir():
            if path.name in SKIP_DIR_NAMES:
                continue
            continue
        if any(parent.name in SKIP_DIR_NAMES for parent in path.parents):
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        yield path


def read_utf8_strict(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def write_utf8(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def build_emoji_pattern() -> re.Pattern[str]:
    # Conservative "emoji/dingbat" ranges:
    # - Misc symbols + Dingbats: U+2600..U+27BF
    # - Emoji blocks: U+1F000..U+1FAFF, U+1FC00..U+1FFFF (future/proposed)
    # - Variation Selector-16: U+FE0F
    # - Zero-width joiner: U+200D
    # - Fitzpatrick modifiers: U+1F3FB..U+1F3FF
    # - Regional indicators: U+1F1E6..U+1F1FF
    return re.compile(
        r"[\u2600-\u27BF"
        r"\u200D\uFE0F"
        r"\U0001F000-\U0001FAFF"
        r"\U0001FC00-\U0001FFFF"
        r"\U0001F1E6-\U0001F1FF"
        r"\U0001F3FB-\U0001F3FF"
        r"]"
    )


def remove_emoji(text: str, pat: re.Pattern[str]) -> tuple[str, int]:
    removed = 0

    def _repl(_: re.Match[str]) -> str:
        nonlocal removed
        removed += 1
        return ""

    out = pat.sub(_repl, text)
    return out, removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove emoji/dingbat symbols from docs (UTF-8 strict).")
    parser.add_argument("--root", default="docs", help="Root folder to scan (default: docs)")
    parser.add_argument(
        "--extra",
        nargs="*",
        default=[],
        help="Extra files (repo-relative) to include, e.g. README.md AGENTS.md",
    )
    parser.add_argument("--write", action="store_true", help="Write changes back to files")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_absolute():
        root = (REPO_ROOT / root).resolve()

    emoji_pat = build_emoji_pattern()
    changes: list[Change] = []
    scanned = 0
    bad_utf8: list[str] = []

    targets: list[Path] = list(iter_text_files(root))
    for extra in args.extra:
        p = Path(extra)
        if not p.is_absolute():
            p = (REPO_ROOT / p).resolve()
        if p.exists() and p.is_file():
            targets.append(p)

    for path in sorted(set(targets)):
        rel = str(path.relative_to(REPO_ROOT))
        scanned += 1
        try:
            text = read_utf8_strict(path)
        except UnicodeDecodeError:
            bad_utf8.append(rel)
            continue

        sanitized, removed = remove_emoji(text, emoji_pat)
        if removed <= 0:
            continue

        changes.append(Change(file=rel, removed=removed))
        if args.write:
            write_utf8(path, sanitized)

    out_path = REPO_ROOT / "logs" / "ci" / today_dir() / "emoji-sanitize.json"
    payload = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "files_scanned": scanned,
        "changes": [c.__dict__ for c in changes],
        "total_removed": sum(c.removed for c in changes),
        "bad_utf8_files": bad_utf8,
        "wrote": bool(args.write),
    }
    write_json(out_path, payload)
    print(f"EMOJI_SANITIZE scanned={scanned} changed={len(changes)} removed={payload['total_removed']} out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
