#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import argparse
import subprocess
import sys
import threading
import time
from pathlib import Path
from queue import Queue, Empty


REPO_ROOT = Path(__file__).resolve().parents[2]


def today_dir() -> str:
    return dt.date.today().isoformat()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Task Master MCP (stdio) initialize handshake.")
    parser.add_argument("--child", default="task-master-mcp.cmd", help="Child command to launch (default: task-master-mcp.cmd)")
    args = parser.parse_args()

    wrapper = REPO_ROOT / "scripts" / "mcp" / "task_master_stdio_wrapper.py"
    if not wrapper.exists():
        print("probe error: wrapper not found", file=sys.stderr)
        return 2

    out_dir = REPO_ROOT / "logs" / "ci" / today_dir() / "mcp"
    out_path = out_dir / "task-master-stdio-probe.json"

    cmd = ["py", "-3", str(wrapper), "--", args.child]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    started = dt.datetime.now().isoformat(timespec="seconds")
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    stdout_q: Queue[str | None] = Queue()
    stderr_buf = bytearray()

    def _read_stdout() -> None:
        try:
            while True:
                line = proc.stdout.readline()  # type: ignore[union-attr]
                if not line:
                    stdout_q.put(None)
                    return
                stdout_q.put(line.decode("utf-8", errors="replace").strip())
        except Exception:
            stdout_q.put(None)

    def _read_stderr() -> None:
        try:
            while True:
                chunk = proc.stderr.read(8192)  # type: ignore[union-attr]
                if not chunk:
                    return
                if len(stderr_buf) < 200_000:
                    stderr_buf.extend(chunk[: 200_000 - len(stderr_buf)])
        except Exception:
            return

    t_out = threading.Thread(target=_read_stdout, daemon=True)
    t_err = threading.Thread(target=_read_stderr, daemon=True)
    t_out.start()
    t_err.start()

    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "probe_task_master", "version": "0.1"},
            "capabilities": {},
        },
    }

    proc.stdin.write((json.dumps(init_req, ensure_ascii=False) + "\n").encode("utf-8"))  # type: ignore[union-attr]
    proc.stdin.flush()  # type: ignore[union-attr]
    proc.stdin.write((json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n").encode("utf-8"))  # type: ignore[union-attr]
    proc.stdin.flush()  # type: ignore[union-attr]
    try:
        proc.stdin.close()  # type: ignore[union-attr]
    except Exception:
        pass

    deadline = time.time() + 20
    response = None
    notifications: list[object] = []
    raw_lines: list[str] = []

    while time.time() < deadline:
        try:
            s = stdout_q.get(timeout=0.5)
        except Empty:
            continue
        if s is None:
            break
        if not s:
            continue
        raw_lines.append(s)
        try:
            msg = json.loads(s)
        except Exception:
            continue
        if isinstance(msg, dict) and msg.get("id") == 1 and "result" in msg:
            response = msg
            break
        notifications.append(msg)

    try:
        proc.wait(timeout=10)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

    payload = {
        "ts": started,
        "cmd": cmd,
        "initialize": init_req,
        "response": response,
        "notifications_count": len(notifications),
        "raw_stdout_lines": raw_lines[:200],
        "stderr_preview": bytes(stderr_buf).decode("utf-8", errors="replace")[:20000],
    }
    write_json(out_path, payload)

    ok = response is not None
    print(f"probe ok={ok} out={out_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
