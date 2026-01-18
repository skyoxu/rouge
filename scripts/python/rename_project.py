#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]


SKIP_DIR_NAMES = {
    ".git",
    ".godot",
    "build",
    "logs",
    "tmp",
    "_tmp",
    "TestResults",
}

SKIP_DIR_PREFIXES = (
    "_backup_pre_",
)

SKIP_TOP_DIRS = {
    "backup",  # historical backups; keep intact
}

TEXT_EXTS = {
    ".cs",
    ".csproj",
    ".cfg",
    ".config",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sln",
    ".sql",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}


@dataclass(frozen=True)
class RenameSpec:
    old_pascal: str
    old_lower: str
    new_pascal: str
    new_lower: str


def _is_skipped_dir(path: Path) -> bool:
    name = path.name
    if name in SKIP_DIR_NAMES:
        return True
    if any(name.startswith(prefix) for prefix in SKIP_DIR_PREFIXES):
        return True
    if path.parent == REPO_ROOT and name in SKIP_TOP_DIRS:
        return True
    return False


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(_is_skipped_dir(p) for p in path.parents):
            continue
        yield path


def detect_current_project_name(root: Path) -> str | None:
    project_godot = root / "project.godot"
    if project_godot.exists():
        data = project_godot.read_bytes()
        text = decode_text(data)
        if text:
            for pattern in (
                r'^project/assembly_name="([^"]+)"\r?$',
                r'^config/name="([^"]+)"\r?$',
                r'^project/project_path="res://([^"]+)\.csproj"\r?$',
            ):
                m = re.search(pattern, text, flags=re.M)
                if m:
                    val = m.group(1).strip()
                    if val:
                        return val

    slns = sorted(root.glob("*.sln"))
    if len(slns) == 1:
        return slns[0].stem

    csprojs = sorted(root.glob("*.csproj"))
    if len(csprojs) == 1:
        return csprojs[0].stem

    return None


def decode_text(data: bytes) -> str | None:
    # Prefer UTF-8; fall back to GB18030 for legacy Chinese-encoded files,
    # then rewrite as UTF-8 on write.
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


def write_text_utf8(path: Path, text: str, newline: str) -> None:
    # Always write UTF-8 (no BOM); preserve newline style.
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if newline == "\r\n":
        normalized = normalized.replace("\n", "\r\n")
    path.write_bytes(normalized.encode("utf-8"))


def detect_newline(data: bytes) -> str:
    # Heuristic: if CRLF exists, keep CRLF; else LF.
    return "\r\n" if b"\r\n" in data else "\n"


def replace_all(text: str, spec: RenameSpec) -> str:
    # Replace exact token-like occurrences first (PascalCase), then lowercase.
    # Use word boundaries where it makes sense, but also handle paths/filenames.
    text = re.sub(rf"\b{re.escape(spec.old_pascal)}\b", spec.new_pascal, text)
    text = re.sub(rf"\b{re.escape(spec.old_lower)}\b", spec.new_lower, text)

    # Filenames and explicit paths
    text = text.replace(f"{spec.old_pascal}.csproj", f"{spec.new_pascal}.csproj")
    text = text.replace(f"{spec.old_pascal}.sln", f"{spec.new_pascal}.sln")
    text = text.replace(f"app_userdata\\{spec.old_pascal}\\", f"app_userdata\\{spec.new_pascal}\\")
    text = text.replace(f"app_userdata/{spec.old_pascal}/", f"app_userdata/{spec.new_pascal}/")

    # Default build artifact names used in docs/CI/scripts
    text = text.replace("build/Game.exe", f"build/{spec.new_pascal}.exe")
    text = text.replace("build\\Game.exe", f"build\\{spec.new_pascal}.exe")

    return text


def update_project_godot(text: str, spec: RenameSpec) -> str:
    text = replace_all(text, spec)
    text = re.sub(r'^config/name=".*"\r?$', f'config/name="{spec.new_pascal}"', text, flags=re.M)
    text = re.sub(
        r'^project/assembly_name=".*"\r?$',
        f'project/assembly_name="{spec.new_pascal}"',
        text,
        flags=re.M,
    )
    text = re.sub(
        r'^project/project_path="res://.*"\r?$',
        f'project/project_path="res://{spec.new_pascal}.csproj"',
        text,
        flags=re.M,
    )
    # Remove obvious mojibake duplicate key if present.
    text = re.sub(r'^\s*".*config_version"\s*=\s*\d+\s*\r?$', "", text, flags=re.M)
    # Compact accidental extra blank lines introduced by removal.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def update_export_presets(text: str, spec: RenameSpec) -> str:
    text = replace_all(text, spec)
    text = re.sub(
        r'^export_path="build[\\/][^"]+"\r?$',
        f'export_path="build/{spec.new_pascal}.exe"',
        text,
        flags=re.M,
    )
    text = re.sub(
        r'^application/product_name=".*"\r?$',
        f'application/product_name="{spec.new_pascal}"',
        text,
        flags=re.M,
    )
    text = re.sub(
        r'^application/file_description=".*"\r?$',
        f'application/file_description="{spec.new_pascal}"',
        text,
        flags=re.M,
    )
    return text


def is_text_file(path: Path) -> bool:
    if path.name in {"project.godot", "export_presets.cfg"}:
        return True
    return path.suffix.lower() in TEXT_EXTS


def scan_semantics(root: Path, spec: RenameSpec) -> dict:
    top_dirs = sorted([p.name for p in root.iterdir() if p.is_dir() and not _is_skipped_dir(p)])
    top_files = sorted([p.name for p in root.iterdir() if p.is_file()])
    solutions = sorted([p.name for p in root.glob("*.sln")])
    csprojs = sorted([p.name for p in root.glob("*.csproj")])
    workflows = sorted([str(p.relative_to(root)) for p in (root / ".github" / "workflows").glob("*.yml")])

    occurrences = 0
    files_with_hits: set[str] = set()
    pattern = re.compile(rf"\b({re.escape(spec.old_pascal)}|{re.escape(spec.old_lower)})\b")
    for f in iter_files(root):
        if not is_text_file(f):
            continue
        data = f.read_bytes()
        decoded = decode_text(data)
        if decoded is None:
            continue
        hits = len(pattern.findall(decoded))
        if hits:
            occurrences += hits
            files_with_hits.add(str(f.relative_to(root)))

    return {
        "root": str(root),
        "top_dirs": top_dirs,
        "top_files": top_files,
        "solutions": solutions,
        "csprojs": csprojs,
        "workflows": workflows,
        "rename_from": {"pascal": spec.old_pascal, "lower": spec.old_lower},
        "rename_to": {"pascal": spec.new_pascal, "lower": spec.new_lower},
        "hit_count_estimate": occurrences,
        "files_with_hits_count": len(files_with_hits),
    }


def write_log(root: Path, title: str, body_lines: list[str]) -> Path:
    log_dir = root / "logs" / "rename"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = log_dir / f"{ts}_{title}.md"
    content = "\n".join(body_lines).rstrip() + "\n"
    path.write_bytes(content.encode("utf-8"))
    return path


def rename_files(root: Path, spec: RenameSpec, dry_run: bool) -> list[tuple[Path, Path]]:
    renames: list[tuple[Path, Path]] = []
    candidates = {
        root / f"{spec.old_pascal}.csproj": root / f"{spec.new_pascal}.csproj",
        root / f"{spec.old_pascal}.sln": root / f"{spec.new_pascal}.sln",
    }
    for src, dst in candidates.items():
        if src.exists() and src != dst:
            renames.append((src, dst))

    for src, dst in renames:
        if dry_run:
            continue
        if dst.exists():
            raise FileExistsError(f"Refusing to overwrite existing file: {dst}")
        src.rename(dst)

    return renames


def update_text_files(root: Path, spec: RenameSpec, dry_run: bool) -> dict:
    changed = 0
    scanned = 0
    skipped_decode = 0
    per_file = []

    self_path = Path(__file__).resolve()
    for path in iter_files(root):
        # Avoid self-modification during runs.
        if path.resolve() == self_path:
            continue
        if not is_text_file(path):
            continue
        scanned += 1
        data = path.read_bytes()
        decoded = decode_text(data)
        if decoded is None:
            skipped_decode += 1
            continue

        newline = detect_newline(data)
        updated = decoded

        if path.name == "project.godot":
            updated = update_project_godot(updated, spec)
        elif path.name == "export_presets.cfg":
            updated = update_export_presets(updated, spec)
        else:
            updated = replace_all(updated, spec)

        if updated != decoded:
            changed += 1
            per_file.append(str(path.relative_to(root)))
            if not dry_run:
                write_text_utf8(path, updated, newline=newline)

    return {
        "scanned_text_files": scanned,
        "changed_files": changed,
        "skipped_decode": skipped_decode,
        "changed_paths": per_file,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename project name and normalize text files to UTF-8.")
    parser.add_argument(
        "--old",
        default=None,
        help="Existing project name (PascalCase). If omitted, tries to detect from project.godot / *.sln / *.csproj.",
    )
    parser.add_argument("--old-lower", default=None, help="Existing lowercase name (defaults to lowercased --old)")
    parser.add_argument("--new", required=True, help="New project name (PascalCase), e.g. Rouge")
    parser.add_argument("--new-lower", default=None, help="New lowercase name, e.g. rouge (defaults to lowercased --new)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    args = parser.parse_args()

    old_pascal = args.old or detect_current_project_name(REPO_ROOT)
    if not old_pascal:
        print("Error: unable to detect current project name; pass --old explicitly.")
        return 2

    spec = RenameSpec(
        old_pascal=old_pascal,
        old_lower=(args.old_lower or old_pascal.lower()),
        new_pascal=args.new,
        new_lower=(args.new_lower or args.new.lower()),
    )

    semantic = scan_semantics(REPO_ROOT, spec)
    scan_log = write_log(
        REPO_ROOT,
        "scan",
        [
            f"# MCP/Repo Semantic Scan",
            "",
            f"- Root: `{semantic['root']}`",
            f"- Rename: `{spec.old_pascal}`/`{spec.old_lower}` -> `{spec.new_pascal}`/`{spec.new_lower}`",
            f"- Hit estimate: {semantic['hit_count_estimate']} occurrences across {semantic['files_with_hits_count']} files (excluding .git, backup, logs).",
            "",
            "## Top-level",
            "",
            f"- Dirs: {', '.join(semantic['top_dirs'])}",
            f"- Files: {', '.join(semantic['top_files'])}",
            "",
            "## .NET",
            "",
            f"- Solutions: {', '.join(semantic['solutions'])}",
            f"- Projects: {', '.join(semantic['csprojs'])}",
            "",
            "## CI",
            "",
            f"- Workflows: {', '.join(semantic['workflows'])}",
            "",
        ],
    )

    file_renames = rename_files(REPO_ROOT, spec, dry_run=args.dry_run)
    text_updates = update_text_files(REPO_ROOT, spec, dry_run=args.dry_run)

    rename_lines = [
        "# Rename Report",
        "",
        f"- Time: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"- Dry run: {args.dry_run}",
        f"- Scan log: `{scan_log}`",
        "",
        "## File renames",
        "",
    ]
    if file_renames:
        for src, dst in file_renames:
            rename_lines.append(f"- `{src.relative_to(REPO_ROOT)}` -> `{dst.relative_to(REPO_ROOT)}`")
    else:
        rename_lines.append("- (none)")

    rename_lines += [
        "",
        "## Text updates",
        "",
        f"- Scanned text files: {text_updates['scanned_text_files']}",
        f"- Changed files: {text_updates['changed_files']}",
        f"- Skipped (decode failed): {text_updates['skipped_decode']}",
    ]

    report_log = write_log(REPO_ROOT, "rename_report", rename_lines)

    print(f"OK. Report: {report_log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
