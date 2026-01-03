#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def today_dir() -> str:
    return dt.date.today().isoformat()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def which_cmd() -> str | None:
    # Prefer codex.cmd on Windows to avoid PowerShell execution policy issues with codex.ps1.
    for candidate in ("codex.cmd", "codex"):
        found = shutil_which(candidate)
        if found:
            return found
    return None


def shutil_which(name: str) -> str | None:
    # Minimal which() to avoid importing shutil in older environments.
    paths = os.environ.get("PATH", "").split(os.pathsep)
    exts = os.environ.get("PATHEXT", ".EXE;.CMD;.BAT;.COM").split(";")
    for base in paths:
        base = base.strip('"')
        if not base:
            continue
        cand = Path(base) / name
        if cand.is_file():
            return str(cand)
        if Path(name).suffix:
            continue
        for ext in exts:
            ext = ext.strip()
            if not ext:
                continue
            cand2 = Path(base) / f"{name}{ext.lower()}"
            if cand2.is_file():
                return str(cand2)
            cand3 = Path(base) / f"{name}{ext.upper()}"
            if cand3.is_file():
                return str(cand3)
    return None


@dataclass(frozen=True)
class ServerConfig:
    name: str
    enabled: bool
    transport_type: str
    command: str | None
    args: list[str]
    env_vars: list[str]
    cwd: str | None
    startup_timeout_sec: float


def run_capture(cmd: list[str], timeout_sec: float = 10.0) -> tuple[int, str, str]:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    try:
        out, err = p.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
    return p.returncode or 0, out, err


def list_server_names(codex_cmd: str) -> list[str]:
    rc, out, err = run_capture([codex_cmd, "mcp", "list"], timeout_sec=10.0)
    if rc != 0:
        raise RuntimeError(f"codex mcp list failed rc={rc}: {err.strip()}")

    names: list[str] = []
    for line in out.splitlines():
        line = line.rstrip()
        if not line or line.startswith("Name "):
            continue
        # Skip the URL table header.
        if line.startswith("Name") and "Url" in line:
            continue
        # Table rows begin with server name (no leading spaces).
        if line[:1].isspace():
            continue
        name = line.split()[0]
        # Ignore separators (----).
        if set(name) <= {"-"}:
            continue
        names.append(name)
    # Deduplicate preserving order.
    seen: set[str] = set()
    out_names: list[str] = []
    for n in names:
        if n in seen:
            continue
        seen.add(n)
        out_names.append(n)
    return out_names


def get_server_config(codex_cmd: str, name: str) -> ServerConfig:
    rc, out, err = run_capture([codex_cmd, "mcp", "get", name, "--json"], timeout_sec=10.0)
    if rc != 0:
        raise RuntimeError(f"codex mcp get {name} failed rc={rc}: {err.strip()}")
    data = json.loads(out)
    transport = data.get("transport") or {}
    transport_type = (transport.get("type") or "").strip()
    env_vars = transport.get("env_vars") or []
    args = transport.get("args") or []
    return ServerConfig(
        name=str(data.get("name") or name),
        enabled=bool(data.get("enabled")),
        transport_type=transport_type,
        command=transport.get("command"),
        args=[str(a) for a in args],
        env_vars=[str(v) for v in env_vars],
        cwd=transport.get("cwd"),
        startup_timeout_sec=float(data.get("startup_timeout_sec") or 60.0),
    )


def build_initialize_params(root_uri: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {
        "protocolVersion": "2024-11-05",
        "clientInfo": {"name": "rouge-mcp-selftest", "version": "0"},
        "capabilities": {
            "experimental": {},
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
            "prompts": {"listChanged": False},
        },
    }
    if root_uri:
        params["rootUri"] = root_uri
    return params


def stdio_handshake_tools_list(
    cfg: ServerConfig,
    root_uri: str | None,
    timeout_sec: float,
    out_dir: Path,
) -> dict[str, Any]:
    missing_env = [k for k in cfg.env_vars if not os.environ.get(k)]
    if missing_env:
        return {"status": "skipped", "reason": "missing_env_vars", "missing_env_vars": missing_env}
    if not cfg.command:
        return {"status": "skipped", "reason": "missing_command"}

    cmd = [cfg.command, *cfg.args]
    env = os.environ.copy()
    cwd = cfg.cwd or str(REPO_ROOT)

    p = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=env,
    )

    stdout_lines: list[bytes] = []
    stderr_bytes: list[bytes] = []

    def drain_stdout() -> None:
        assert p.stdout is not None
        while True:
            line = p.stdout.readline()
            if not line:
                return
            stdout_lines.append(line)

    def drain_stderr() -> None:
        assert p.stderr is not None
        while True:
            chunk = p.stderr.read(4096)
            if not chunk:
                return
            stderr_bytes.append(chunk)

    t_out = threading.Thread(target=drain_stdout, daemon=True)
    t_err = threading.Thread(target=drain_stderr, daemon=True)
    t_out.start()
    t_err.start()

    def send(obj: dict[str, Any]) -> None:
        assert p.stdin is not None
        p.stdin.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
        p.stdin.flush()

    init_params = build_initialize_params(root_uri)
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": init_params})
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})

    init_ok = False
    tools_ok = False
    tools_count: int | None = None
    errors: list[str] = []
    seen = 0

    start = time.time()
    while time.time() - start < timeout_sec:
        # Parse any new stdout lines.
        while seen < len(stdout_lines):
            raw = stdout_lines[seen]
            seen += 1
            try:
                msg = json.loads(raw.decode("utf-8"))
            except Exception:
                continue
            if isinstance(msg, dict) and msg.get("id") == 1 and "result" in msg:
                init_ok = True
            if isinstance(msg, dict) and msg.get("id") == 2:
                if "result" in msg and isinstance(msg["result"], dict) and isinstance(msg["result"].get("tools"), list):
                    tools_ok = True
                    tools_count = len(msg["result"]["tools"])
                elif "error" in msg:
                    errors.append(str(msg.get("error")))
        if init_ok and tools_ok:
            break
        time.sleep(0.1)

    # Save limited evidence (avoid secrets).
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_text = b"".join(stdout_lines).decode("utf-8", errors="replace")
    stderr_text = b"".join(stderr_bytes).decode("utf-8", errors="replace")
    (out_dir / f"{cfg.name}-stdout.preview.txt").write_text(stdout_text[:8000], encoding="utf-8", newline="\n")
    (out_dir / f"{cfg.name}-stderr.preview.txt").write_text(stderr_text[:8000], encoding="utf-8", newline="\n")

    try:
        if p.stdin:
            p.stdin.close()
    except Exception:
        pass
    try:
        p.terminate()
    except Exception:
        pass
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()

    status = "ok" if init_ok and tools_ok else "failed"
    return {
        "status": status,
        "init_ok": init_ok,
        "tools_ok": tools_ok,
        "tools_count": tools_count,
        "errors": errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="MCP self-test for Codex CLI configured servers (stdio only).")
    ap.add_argument(
        "--root-uri",
        default=None,
        help='MCP initialize rootUri (default: file:/// + repo root absolute path)',
    )
    ap.add_argument(
        "--timeout-sec",
        type=float,
        default=30.0,
        help="Per-server timeout seconds for initialize + tools/list (default: 30).",
    )
    args = ap.parse_args()

    codex_cmd = which_cmd()
    if not codex_cmd:
        sys.stderr.write("mcp-selftest: codex.cmd not found in PATH\n")
        return 2

    names = list_server_names(codex_cmd)
    root_uri = args.root_uri
    if root_uri is None:
        # Windows path -> file URI. Keep it simple: replace backslashes with slashes and prefix file:///.
        root_uri = "file:///" + str(REPO_ROOT.resolve()).replace("\\", "/")
    log_dir = REPO_ROOT / "logs" / "ci" / today_dir() / "mcp" / "selftest"
    report_path = REPO_ROOT / "logs" / "ci" / today_dir() / "mcp" / "mcp-selftest.json"

    results: dict[str, Any] = {
        "ts": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "root_uri": root_uri,
        "timeout_sec": args.timeout_sec,
        "servers": {},
    }

    for name in names:
        cfg = get_server_config(codex_cmd, name)
        if not cfg.enabled:
            results["servers"][name] = {"status": "skipped", "reason": "disabled"}
            continue
        if cfg.transport_type != "stdio":
            results["servers"][name] = {"status": "skipped", "reason": f"transport_{cfg.transport_type}"}
            continue
        results["servers"][name] = stdio_handshake_tools_list(
            cfg=cfg,
            root_uri=root_uri,
            timeout_sec=float(args.timeout_sec),
            out_dir=log_dir,
        )

    write_json(report_path, results)
    print(str(report_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
