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
class Rule:
    key: str
    pattern: re.Pattern[str]
    replacement: str


def today_dir() -> str:
    return dt.date.today().isoformat()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_dir():
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


def build_rules() -> list[Rule]:
    # NOTE: Docs contain mixed Chinese/English. With Unicode "\w", \b won't match tokens like
    # "Electron" when adjacent to CJK (e.g. "Electron桌面应用"). Use ASCII boundaries.
    ascii_i = re.IGNORECASE | re.ASCII
    return [
        Rule(
            "electronegativity_url",
            re.compile(r"https://github\.com/doyensec/electronegativity", re.ASCII),
            "https://example.invalid/legacy-security-scanner",
        ),
        Rule("electronegativity_scan", re.compile(r"electronegativity_scan", ascii_i), "legacy_security_scanner_scan"),
        Rule("electronegativity_word", re.compile(r"electronegativity", ascii_i), "Legacy Security Scanner"),
        Rule("electronjs_domain", re.compile(r"electronjs\.org", ascii_i), "legacy-shell.invalid"),
        Rule("electron_metric", re.compile(r"security\.electron_version", ascii_i), "security.legacy_shell_version"),
        Rule("electron_version_field", re.compile(r"electronVersion", ascii_i), "legacyShellVersion"),
        Rule("electron_env_prefix", re.compile(r"ELECTRON_", ascii_i), "LEGACY_SHELL_"),
        Rule("electron_private_api", re.compile(r"_electron\b", ascii_i), "_legacy_shell"),
        Rule("electron_camel_api", re.compile(r"electronAPI", ascii_i), "legacyShellApi"),
        Rule("electron_pascal_prefix", re.compile(r"Electron(?=[A-Z0-9_])", re.ASCII), "LegacyShell"),
        Rule("electron_snake_prefix", re.compile(r"electron_", ascii_i), "legacy_shell_"),
        Rule("electron_path_segment", re.compile(r"electron/", ascii_i), "legacy-shell/"),
        Rule("electron_word", re.compile(r"\belectron\b", ascii_i), "旧桌面壳"),
        Rule("chromium", re.compile(r"\bchromium\b", ascii_i), "旧浏览器运行时"),
        Rule("nodejs", re.compile(r"\bnode\.js\b|\bnodejs\b", ascii_i), "旧脚本运行时"),
        Rule("electron_main_process", re.compile(r"\bmain\s+process\b", ascii_i), "宿主进程"),
        Rule("electron_renderer_process", re.compile(r"\brenderer\s+process\b", ascii_i), "渲染进程"),
        Rule("electron_preload", re.compile(r"\bpreload\.js\b|\bpreload\s+script\b", ascii_i), "旧预加载脚本"),
        Rule("electron_ipc", re.compile(r"\bipc\b", ascii_i), "进程间通信"),
        Rule("electron_browserwindow", re.compile(r"\bbrowserwindow\b", ascii_i), "旧窗口容器"),
        Rule("electron_contextisolation", re.compile(r"\bcontextisolation\b", ascii_i), "旧隔离开关"),
        Rule("electron_nodeintegration", re.compile(r"\bnodeintegration\b", ascii_i), "旧脚本集成开关"),
        Rule("electron_contextbridge", re.compile(r"\bcontextbridge\b", ascii_i), "旧桥接层"),
        Rule("web_csp", re.compile(r"\bcontent-security-policy\b|\bcsp\b", ascii_i), "Web 内容安全策略"),
        Rule("playwright", re.compile(r"\bplaywright\b", ascii_i), "旧 E2E 工具"),
        Rule("electron_builder", re.compile(r"\belectron-builder\b", ascii_i), "旧打包工具"),
        Rule("react", re.compile(r"\breact\b", ascii_i), "旧前端框架"),
        Rule("vite", re.compile(r"\bvite\b", ascii_i), "旧构建工具"),
        Rule("phaser", re.compile(r"\bphaser\b", ascii_i), "旧前端游戏引擎"),
        Rule("vitegame", re.compile(r"\bvitegame\b", ascii_i), "旧项目"),
    ]


def apply_rules(text: str, rules: list[Rule]) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    out = text
    for rule in rules:
        out, n = rule.pattern.subn(rule.replacement, out)
        if n:
            counts[rule.key] = counts.get(rule.key, 0) + n
    return out, counts


def changed_line_previews(before: str, after: str, max_lines: int) -> list[dict]:
    b_lines = before.splitlines()
    a_lines = after.splitlines()
    previews: list[dict] = []
    for idx in range(min(len(b_lines), len(a_lines))):
        if b_lines[idx] != a_lines[idx]:
            previews.append({"line": idx + 1, "before": b_lines[idx], "after": a_lines[idx]})
            if len(previews) >= max_lines:
                break
    return previews


def main() -> int:
    parser = argparse.ArgumentParser(description="Neutralize legacy stack terms in docs/** (UTF-8 strict).")
    parser.add_argument("--root", default="docs", help="Root folder to sanitize (default: docs)")
    parser.add_argument("--extra", nargs="*", default=[], help="Extra files to include (e.g. README.md)")
    parser.add_argument("--write", action="store_true", help="Write changes back to files")
    parser.add_argument("--max-preview-lines", type=int, default=5, help="Max changed lines recorded per file")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_absolute():
        root = (REPO_ROOT / root).resolve()

    rules = build_rules()

    log_dir = REPO_ROOT / "logs" / "ci" / today_dir() / "legacy-term-sanitize"
    summary_path = log_dir / "summary.json"
    changes_path = log_dir / "changes.json"

    files: list[Path] = list(iter_text_files(root))
    for extra in args.extra:
        p = Path(extra)
        if not p.is_absolute():
            p = (REPO_ROOT / p).resolve()
        if p.is_file() and p.suffix.lower() in TEXT_EXTS and p not in files:
            files.append(p)

    files_scanned = 0
    files_changed = 0
    bad_utf8: list[str] = []
    total_by_rule: dict[str, int] = {}
    change_items: list[dict] = []

    for path in sorted(files):
        rel = str(path.relative_to(REPO_ROOT))
        files_scanned += 1
        try:
            before = read_utf8_strict(path)
        except UnicodeDecodeError:
            bad_utf8.append(rel)
            continue

        after, counts = apply_rules(before, rules)
        if not counts:
            continue

        previews = changed_line_previews(before, after, max_lines=args.max_preview_lines)
        change_items.append(
            {
                "file": rel,
                "changed": before != after,
                "counts": counts,
                "total_replacements": sum(counts.values()),
                "previews": previews,
            }
        )

        for k, v in counts.items():
            total_by_rule[k] = total_by_rule.get(k, 0) + v

        if before != after:
            files_changed += 1
            if args.write:
                write_utf8(path, after)

    summary = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "write": bool(args.write),
        "files_scanned": files_scanned,
        "files_changed": files_changed,
        "bad_utf8_files": bad_utf8,
        "total_replacements_by_rule": dict(sorted(total_by_rule.items())),
        "changes_count": len(change_items),
    }

    write_json(summary_path, summary)
    write_json(changes_path, change_items)

    print(
        "LEGACY_TERM_SANITIZE "
        + f"scanned={files_scanned} changed={files_changed} bad_utf8={len(bad_utf8)} "
        + f"write={int(args.write)} out={log_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
