#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install .NET 8 SDK to a user-scoped directory on Windows (no admin expected).

Why:
  - This repo relies on `dotnet test` (xUnit) and other .NET tooling.
  - Some environments do not have `winget` or `dotnet` preinstalled/in PATH.

Approach:
  - Download Microsoft's official dotnet-install.ps1.
  - Run it via PowerShell to install the latest .NET 8 SDK into:
      %LOCALAPPDATA%\\Microsoft\\dotnet
  - Write installation logs to logs/ci/<YYYY-MM-DD>/install-dotnet8/

Notes:
  - This modifies the current machine's user profile (installs binaries under LocalAppData).
  - It does NOT permanently modify PATH. It prints instructions to do so.
"""

from __future__ import annotations

import datetime as _dt
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


DOTNET_INSTALL_PS1_URL = "https://dotnet.microsoft.com/download/dotnet/scripts/v1/dotnet-install.ps1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ci_out_dir(root: Path) -> Path:
    date = _dt.date.today().isoformat()
    out = root / "logs" / "ci" / date / "install-dotnet8"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 (trusted URL)
        data = r.read()
    dst.write_bytes(data)


def main() -> int:
    root = _repo_root()
    out_dir = _ci_out_dir(root)

    existing = shutil.which("dotnet")
    if existing:
        (out_dir / "already-present.txt").write_text(f"dotnet already in PATH: {existing}\n", encoding="utf-8")
        print(f"DOTNET status=ok already_in_path={existing}")
        return 0

    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        (out_dir / "error.txt").write_text("PowerShell not found (powershell/pwsh).\n", encoding="utf-8")
        print("DOTNET status=fail reason=powershell_not_found")
        return 2

    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        (out_dir / "error.txt").write_text("LOCALAPPDATA is not set.\n", encoding="utf-8")
        print("DOTNET status=fail reason=localappdata_not_set")
        return 2

    install_dir = Path(local_appdata) / "Microsoft" / "dotnet"
    tmp_dir = root / "_tmp" / "dotnet-install"
    script_path = tmp_dir / "dotnet-install.ps1"

    try:
        _download(DOTNET_INSTALL_PS1_URL, script_path)
    except Exception as exc:  # noqa: BLE001
        (out_dir / "download-error.txt").write_text(f"Failed to download: {exc}\n", encoding="utf-8")
        print("DOTNET status=fail reason=download_failed")
        return 2

    cmd = [
        powershell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-Channel",
        "8.0",
        "-Quality",
        "ga",
        "-InstallDir",
        str(install_dir),
    ]

    proc = subprocess.run(
        cmd,
        cwd=str(root),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30 * 60,
    )
    (out_dir / "install.log").write_text(proc.stdout or "", encoding="utf-8")
    (out_dir / "install.cmd.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")

    dotnet_exe = install_dir / "dotnet.exe"
    if proc.returncode != 0 or not dotnet_exe.exists():
        print(f"DOTNET status=fail rc={proc.returncode} out={out_dir}")
        return 2

    # Verify dotnet --info using the installed binary directly.
    info = subprocess.run(
        [str(dotnet_exe), "--info"],
        cwd=str(root),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )
    (out_dir / "dotnet-info.log").write_text(info.stdout or "", encoding="utf-8")

    instructions = "\n".join(
        [
            "Installed .NET SDK to:",
            str(install_dir),
            "",
            "To make `dotnet` available in new terminals, add this directory to your user PATH:",
            str(install_dir),
            "",
            "Or run dotnet with an absolute path:",
            str(dotnet_exe),
            "",
        ]
    )
    (out_dir / "next-steps.txt").write_text(instructions, encoding="utf-8")
    print(f"DOTNET status=ok dotnet={dotnet_exe} out={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

