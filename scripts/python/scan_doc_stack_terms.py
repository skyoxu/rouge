#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
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
    "backup",
    "tmp",
    "_tmp",
    "TestResults",
    "demo",
}


@dataclass(frozen=True)
class Term:
    key: str
    pattern: re.Pattern[str]
    description: str


def iter_text_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in TEXT_EXTS:
            yield root
        return

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


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def today_dir() -> str:
    return dt.date.today().isoformat()


def build_terms() -> list[Term]:
    # NOTE: Our docs are mostly Chinese. Python's default Unicode definition treats CJK as "\w",
    # which breaks word-boundary (\b) patterns like "\belectron\b" when followed by Chinese text
    # (e.g. "Electron桌面应用"). Use ASCII boundaries for these legacy English tokens.
    flags = re.IGNORECASE | re.ASCII
    return [
        Term(
            key="electron",
            pattern=re.compile(r"\belectron\b", flags),
            description="Legacy desktop shell (Electron) mention",
        ),
        Term(
            key="electron_snake_case",
            pattern=re.compile(r"electron_", flags),
            description="Electron token inside snake_case/file tokens (e.g. electron_main, scan_electron_*)",
        ),
        Term(
            key="electron_private_api",
            pattern=re.compile(r"_electron\b", flags),
            description="Electron private API token (e.g. _electron.launch)",
        ),
        Term(
            key="electron_env_prefix",
            pattern=re.compile(r"\belectron_[a-z0-9_]*\b", flags),
            description="Electron env-like tokens in any case (e.g. ELECTRON_DISABLE_*)",
        ),
        Term(
            key="electron_pascal_identifier",
            pattern=re.compile(r"Electron(?=[A-Z0-9_])", re.ASCII),
            description="Electron PascalCase identifier prefix (e.g. ElectronApplication)",
        ),
        Term(
            key="electron_camel_identifier",
            pattern=re.compile(r"electronAPI", flags),
            description="Electron camelCase identifier (e.g. window.electronAPI)",
        ),
        Term(
            key="electron_path_segment",
            pattern=re.compile(r"electron/", flags),
            description="Electron path segment (e.g. electron/main.ts)",
        ),
        Term(
            key="electronjs_domain",
            pattern=re.compile(r"electronjs\.org", flags),
            description="Electron official docs domain",
        ),
        Term(
            key="electronegativity",
            pattern=re.compile(r"electronegativity", flags),
            description="Legacy security tool name/token",
        ),
        Term(
            key="chromium",
            pattern=re.compile(r"\bchromium\b", flags),
            description="Legacy browser runtime (Chromium) mention",
        ),
        Term(
            key="nodejs",
            pattern=re.compile(r"\bnode\.js\b|\bnodejs\b", flags),
            description="Legacy script runtime (Node.js) mention",
        ),
        Term(
            key="electron_main_process",
            pattern=re.compile(r"\bmain\s+process\b", flags),
            description="Electron main process terminology",
        ),
        Term(
            key="electron_renderer_process",
            pattern=re.compile(r"\brenderer\s+process\b", flags),
            description="Electron renderer process terminology",
        ),
        Term(
            key="electron_preload",
            pattern=re.compile(r"\bpreload\.js\b|\bpreload\s+script\b", flags),
            description="Electron preload script terminology",
        ),
        Term(
            key="electron_ipc",
            pattern=re.compile(r"\bipc\b", flags),
            description="Electron IPC terminology",
        ),
        Term(
            key="electron_browserwindow",
            pattern=re.compile(r"\bbrowserwindow\b", flags),
            description="Electron BrowserWindow terminology",
        ),
        Term(
            key="electron_contextisolation",
            pattern=re.compile(r"\bcontextisolation\b", flags),
            description="Electron contextIsolation terminology",
        ),
        Term(
            key="electron_nodeintegration",
            pattern=re.compile(r"\bnodeintegration\b", flags),
            description="Electron nodeIntegration terminology",
        ),
        Term(
            key="electron_contextbridge",
            pattern=re.compile(r"\bcontextbridge\b", flags),
            description="Electron contextBridge terminology",
        ),
        Term(
            key="web_csp",
            pattern=re.compile(r"\bcontent-security-policy\b|\bcsp\b", flags),
            description="Web Content Security Policy (CSP) terminology",
        ),
        Term(
            key="playwright",
            pattern=re.compile(r"\bplaywright\b", flags),
            description="Legacy E2E tool (Playwright) mention",
        ),
        Term(
            key="vitest",
            pattern=re.compile(r"\bvitest\b", flags),
            description="Legacy unit test tool (Vitest) mention",
        ),
        Term(
            key="jest",
            pattern=re.compile(r"\bjest\b", flags),
            description="Legacy unit test tool (Jest) mention",
        ),
        Term(
            key="pnpm",
            pattern=re.compile(r"\bpnpm\b", flags),
            description="Legacy Node package manager (pnpm) mention",
        ),
        Term(
            key="npm",
            pattern=re.compile(r"\bnpm\b", flags),
            description="Legacy Node package manager (npm) mention",
        ),
        Term(
            key="electron_builder",
            pattern=re.compile(r"\belectron-builder\b", flags),
            description="Legacy packager (electron-builder) mention",
        ),
        Term(
            key="react",
            pattern=re.compile(r"\breact\b", flags),
            description="Legacy frontend framework (React) mention",
        ),
        Term(
            key="tailwind",
            pattern=re.compile(r"\btailwind\b", flags),
            description="Legacy styling framework (Tailwind) mention",
        ),
        Term(
            key="vite",
            pattern=re.compile(r"\bvite\b", flags),
            description="Legacy frontend build tool (Vite) mention",
        ),
        Term(
            key="phaser",
            pattern=re.compile(r"\bphaser\b", flags),
            description="Legacy frontend game engine (Phaser) mention",
        ),
        Term(
            key="i18next",
            pattern=re.compile(r"\bi18next\b", flags),
            description="Legacy i18n framework (i18next) mention",
        ),
        Term(
            key="newguild",
            pattern=re.compile(r"\bnewguild\b", flags),
            description="Legacy repo/project name (newguild) mention",
        ),
        Term(
            key="godotgame",
            pattern=re.compile(r"\bgodotgame\b", flags),
            description="Legacy repo/project name (godotgame) mention",
        ),
        Term(
            key="sanguo",
            pattern=re.compile(r"\bsanguo\b", flags),
            description="Legacy repo/project name (sanguo) mention",
        ),
        Term(
            key="vitegame",
            pattern=re.compile(r"\bvitegame\b", flags),
            description="Legacy project name (vitegame) mention",
        ),
    ]


def scan_file(path: Path, rel: str, terms: list[Term]) -> list[dict]:
    text = read_utf8_strict(path)
    hits: list[dict] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        for term in terms:
            if term.pattern.search(line):
                hits.append(
                    {
                        "file": rel,
                        "line": idx,
                        "term": term.key,
                        "snippet": line.strip(),
                    }
                )
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan docs for legacy stack terminology (Electron/frontend stack) and write evidence to logs/ci/."
    )
    parser.add_argument("--root", default="docs", help="Root folder to scan (default: docs)")
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default: logs/ci/<YYYY-MM-DD>/doc-stack-scan)",
    )
    parser.add_argument("--fail-on-hits", action="store_true", help="Exit non-zero if any hits are found")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_absolute():
        root = (REPO_ROOT / root).resolve()

    terms = build_terms()

    if args.out:
        log_dir = Path(args.out)
        if not log_dir.is_absolute():
            log_dir = (REPO_ROOT / log_dir).resolve()
    else:
        log_dir = REPO_ROOT / "logs" / "ci" / today_dir() / "doc-stack-scan"
    scan_path = log_dir / "scan.json"
    summary_path = log_dir / "summary.json"

    files_scanned = 0
    hits: list[dict] = []
    bad_utf8: list[str] = []

    for file_path in iter_text_files(root):
        rel = str(file_path.relative_to(REPO_ROOT))
        files_scanned += 1
        try:
            hits.extend(scan_file(file_path, rel=rel, terms=terms))
        except UnicodeDecodeError:
            bad_utf8.append(rel)

    hits_by_file: dict[str, int] = {}
    hits_by_term: dict[str, int] = {}
    for h in hits:
        hits_by_file[h["file"]] = hits_by_file.get(h["file"], 0) + 1
        hits_by_term[h["term"]] = hits_by_term.get(h["term"], 0) + 1

    top_files = sorted(hits_by_file.items(), key=lambda kv: (-kv[1], kv[0]))[:50]
    top_terms = sorted(hits_by_term.items(), key=lambda kv: (-kv[1], kv[0]))

    summary = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "files_scanned": files_scanned,
        "bad_utf8_files": bad_utf8,
        "terms": [{"key": t.key, "description": t.description, "pattern": t.pattern.pattern} for t in terms],
        "hits": len(hits),
        "top_terms": [{"term": k, "count": v} for k, v in top_terms],
        "top_files": [{"file": k, "count": v} for k, v in top_files],
        "scan_json": str(scan_path),
    }

    write_json(scan_path, hits)
    write_json(summary_path, summary)

    print(f"Doc stack scan complete. hits={len(hits)} scanned={files_scanned} bad_utf8={len(bad_utf8)}")
    print(f"Summary: {summary_path}")

    if bad_utf8:
        print("ERROR: Some files failed UTF-8 strict decoding. Run scripts/python/check_encoding.py first.")
        return 2

    if args.fail_on_hits and hits:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
