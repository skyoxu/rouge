#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_utf8(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def _log(lines: list[str]) -> Path:
    log_dir = REPO_ROOT / "logs" / "setup"
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = log_dir / f"{ts}_install_godot_demo_projects.md"
    _write_utf8(path, "\n".join(lines))
    return path


def _zip_is_valid(zip_path: Path) -> bool:
    try:
        with zipfile.ZipFile(zip_path) as zf:
            # Touch central directory; this will fail for truncated files.
            _ = zf.namelist()[:1]
        return True
    except Exception:
        return False


def download_with_resume(url: str, dest_zip: Path, max_attempts: int, timeout_sec: int) -> None:
    dest_zip.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, max_attempts + 1):
        existing = dest_zip.stat().st_size if dest_zip.exists() else 0
        headers = {"User-Agent": "rouge-installer/1.0"}
        if existing > 0:
            headers["Range"] = f"bytes={existing}-"

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                status = getattr(resp, "status", None)
                # If server ignored Range, restart from scratch.
                if existing > 0 and status == 200:
                    dest_zip.unlink(missing_ok=True)
                    existing = 0

                mode = "ab" if existing > 0 and status == 206 else "wb"
                with dest_zip.open(mode) as f:
                    while True:
                        chunk = resp.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

            if _zip_is_valid(dest_zip):
                return
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            # Keep partial file for resume attempts.
            _ = e
        except Exception:
            # Unknown failure: keep partial file but pause before retry.
            pass

        time.sleep(min(10, attempt))

    raise RuntimeError(f"Download failed or zip remained invalid after {max_attempts} attempts: {url}")


def install(dest_dir: Path, branch: str, max_attempts: int) -> Path:
    url = f"https://codeload.github.com/godotengine/godot-demo-projects/zip/refs/heads/{branch}"

    with tempfile.TemporaryDirectory(prefix="godot-demo-projects_") as td:
        td_path = Path(td)
        zip_path = td_path / f"godot-demo-projects-{branch}.zip"

        download_with_resume(url, zip_path, max_attempts=max_attempts, timeout_sec=120)

        extract_dir = td_path / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)

        roots = [p for p in extract_dir.iterdir() if p.is_dir()]
        if len(roots) != 1:
            raise RuntimeError(f"Unexpected zip layout, expected single root dir, got: {[p.name for p in roots]}")

        root = roots[0]

        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        for child in root.iterdir():
            shutil.move(str(child), str(dest_dir / child.name))

    return dest_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Install godotengine/godot-demo-projects into this repo under demo/ using Python (UTF-8).")
    parser.add_argument("--dest", default=str(REPO_ROOT / "demo" / "godot-demo-projects"), help="Destination directory")
    parser.add_argument("--branch", default="master", help="Branch name to download (default: master)")
    parser.add_argument("--attempts", type=int, default=10, help="Max download attempts (with resume)")
    args = parser.parse_args()

    dest_dir = Path(args.dest)
    if not dest_dir.is_absolute():
        dest_dir = (REPO_ROOT / dest_dir).resolve()
    installed_dir = install(dest_dir=dest_dir, branch=args.branch, max_attempts=args.attempts)

    log_path = _log(
        [
            "# 安装记录：godot-demo-projects",
            "",
            f"- 时间：{dt.datetime.now().isoformat(timespec='seconds')}",
            f"- 来源：`godotengine/godot-demo-projects`（branch: `{args.branch}`）",
            f"- 方式：下载 zip（支持断点续传）+ 解压",
            f"- 目标目录：`{installed_dir.relative_to(REPO_ROOT)}`",
            "",
            "## 备注",
            "",
            "- 这是把上游内容直接落盘到工作区（不是 git submodule）。",
        ]
    )

    print(f"OK: installed into {installed_dir}")
    print(f"Log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
