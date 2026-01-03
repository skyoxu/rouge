#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import threading
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def today_dir() -> str:
    return dt.date.today().isoformat()


class _NullLog:
    def write(self, _: str) -> None:
        return

    def flush(self) -> None:
        return

    def close(self) -> None:
        return


def open_log_file() -> tuple[Path | None, object]:
    """
    Best-effort logging to logs/**.
    If the workspace is read-only (common in sandboxed Codex runs), fall back to no-op logging.
    """
    try:
        log_dir = REPO_ROOT / "logs" / "ci" / today_dir() / "mcp"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "task-master-stdio-wrapper.log"
        fp = open(log_path, "a", encoding="utf-8", newline="\n")
        fp.write(f"\n=== start {dt.datetime.now().isoformat(timespec='seconds')} pid={os.getpid()} ===\n")
        fp.flush()
        return log_path, fp
    except Exception:
        return None, _NullLog()

def _safe_log_stem(raw: str) -> str:
    keep = []
    for ch in raw:
        if ch.isalnum() or ch in {"-", "_", "."}:
            keep.append(ch)
        else:
            keep.append("_")
    stem = "".join(keep).strip("._")
    return stem or "mcp-stdio-wrapper"


def _infer_server_name(child_argv: list[str]) -> str:
    # Prefer a stable semantic name over the wrapper filename.
    lowered = [a.lower() for a in child_argv]
    if "serena" in lowered:
        return "serena"
    if any("task-master" in a for a in lowered) or any("task_master" in a for a in lowered):
        return "task-master"
    if any("server-github" in a for a in lowered):
        return "github"
    if any("context7" in a for a in lowered):
        return "context7"
    if any("sequential" in a for a in lowered):
        return "sequential-thinking"
    try:
        return Path(child_argv[0]).name
    except Exception:
        return "mcp-stdio-wrapper"


def open_log_file_for(child_argv: list[str]) -> tuple[Path | None, object]:
    """
    Best-effort logging to logs/**.
    If the workspace is read-only (common in sandboxed Codex runs), fall back to no-op logging.
    """
    try:
        log_dir = REPO_ROOT / "logs" / "ci" / today_dir() / "mcp"
        log_dir.mkdir(parents=True, exist_ok=True)
        server_name = _safe_log_stem(_infer_server_name(child_argv))
        log_path = log_dir / f"{server_name}-stdio-wrapper.log"
        fp = open(log_path, "a", encoding="utf-8", newline="\n")
        fp.write(f"\n=== start {dt.datetime.now().isoformat(timespec='seconds')} pid={os.getpid()} ===\n")
        fp.flush()
        return log_path, fp
    except Exception:
        return None, _NullLog()


def write_err(data: bytes) -> None:
    try:
        sys.stderr.buffer.write(data)
        sys.stderr.buffer.flush()
    except Exception:
        pass


def forward_stdin_to_child(
    proc: subprocess.Popen[bytes],
    log_fp,
    log_path: Path | None,
    state: dict,
) -> None:
    """
    Forward wrapper stdin -> child stdin.

    This avoids Windows handle-inheritance edge cases where the stdin handle provided to the wrapper
    by the MCP client is not inheritable by grand-children (the actual Node-based MCP server).
    """
    total = 0
    preview_logged = False
    rewrite_logged = False
    stdout_lock = state.setdefault("stdout_lock", threading.Lock())
    try:
        while True:
            # IMPORTANT: readline() returns as soon as a newline is available.
            # Using read(N) can block until EOF, which causes MCP handshake timeouts.
            line = sys.stdin.buffer.readline()
            if not line:
                try:
                    proc.stdin.close()  # type: ignore[union-attr]
                except Exception:
                    pass
                return
            total += len(line)
            if (not preview_logged) and log_path is not None:
                preview_logged = True
                try:
                    head = line[:256]
                    ascii_head = head.decode("utf-8", errors="replace").replace("\r", "\\r").replace("\n", "\\n")
                    hex_head = head.hex()
                    log_fp.write(f"stdin_first_bytes_len={len(line)} total_so_far={total}\n")
                    log_fp.write(f"stdin_first_bytes_ascii={ascii_head}\n")
                    log_fp.write(f"stdin_first_bytes_hex={hex_head}\n")
                    log_fp.flush()
                except Exception:
                    pass

            out = line
            try:
                text = line.decode("utf-8", errors="strict").strip()
                if text:
                    msg = json.loads(text)
                    if isinstance(msg, dict):
                        method = msg.get("method")
                        msg_id = msg.get("id")
                        if method == "initialize":
                            params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
                            if isinstance(params, dict):
                                client_proto = params.get("protocolVersion") if isinstance(params.get("protocolVersion"), str) else None
                                state["client_protocol"] = client_proto
                                state["init_id"] = msg.get("id")

                                params = dict(params)
                                params["protocolVersion"] = "2024-11-05"
                                params["capabilities"] = {}
                                msg["params"] = params
                                out = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")

                                if (not rewrite_logged) and log_path is not None:
                                    rewrite_logged = True
                                    log_fp.write(
                                        f"rewrite_initialize: id={state['init_id']} client_protocol={client_proto} -> 2024-11-05\n"
                                    )
                                    log_fp.flush()

                                # Proactively send initialized to the child so it can reply promptly.
                                if not state.get("sent_initialized_to_child", False):
                                    state["sent_initialized_to_child"] = True
                                    out += b'{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}\n'
                        elif method in {"resources/list", "resources/templates/list", "prompts/list"} and msg_id is not None:
                            # Codex's MCP client may treat "method not found" for these discovery calls as fatal.
                            # Task Master MCP implements only tools; emulate empty resources/prompts to keep the
                            # connection alive.
                            if method == "resources/list":
                                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": []}}
                            elif method == "resources/templates/list":
                                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"resourceTemplates": []}}
                            else:  # prompts/list
                                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"prompts": []}}

                            out = b""  # do not forward to child
                            with stdout_lock:
                                sys.stdout.buffer.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                                sys.stdout.buffer.flush()
                            try:
                                log_fp.write(f"intercept: {method} id={msg_id} -> empty\n")
                                log_fp.flush()
                            except Exception:
                                pass
                        elif method == "notifications/initialized":
                            state["saw_initialized_from_client"] = True
            except Exception:
                out = line

            try:
                if out:
                    proc.stdin.write(out)  # type: ignore[union-attr]
                    proc.stdin.flush()  # type: ignore[union-attr]
            except BrokenPipeError:
                return
    finally:
        try:
            if log_path is not None:
                log_fp.write(f"stdin_forwarder: done total_bytes={total}\n")
                log_fp.flush()
        except Exception:
            pass


def forward_child_stderr(proc: subprocess.Popen[bytes], log_fp) -> None:
    try:
        while True:
            stderr = proc.stderr  # type: ignore[union-attr]
            chunk = stderr.read1(8192) if hasattr(stderr, "read1") else stderr.read(8192)
            if not chunk:
                return
            try:
                log_fp.write(chunk.decode("utf-8", errors="replace"))
                log_fp.flush()
            except Exception:
                pass
    finally:
        try:
            log_fp.write("stderr_forwarder: done\n")
            log_fp.flush()
        except Exception:
            pass


def jsonrpc_stream_filter(proc: subprocess.Popen[bytes], log_fp, state: dict) -> int:
    """
    Read stdout as (mostly) newline-delimited JSON-RPC messages and forward ONLY JSON-RPC 2.0 messages to stdout.
    Everything else is treated as noise and redirected to logs.

    Why:
    - Some MCP servers print logs or even JSON fragments to stdout.
    - Some MCP implementations pretty-print across multiple lines.
    - Codex's MCP client expects stdout to be JSON-RPC messages only.
    """
    buf = bytearray()
    decoder = json.JSONDecoder()
    max_accumulated_bytes = 5_000_000

    def flush_noise(noise: bytes) -> None:
        if not noise:
            return
        try:
            log_fp.write(noise.decode("utf-8", errors="replace"))
            log_fp.flush()
        except Exception:
            pass

    stdout = proc.stdout  # type: ignore[union-attr]
    while True:
        line = stdout.readline()
        if not line:
            break

        # Fast path: non-JSON line -> noise.
        stripped = line.lstrip()
        if not stripped or stripped[:1] not in (b"{", b"["):
            flush_noise(line)
            continue

        buf.clear()
        buf.extend(stripped)

        # Slow path: support multi-line / pretty-printed JSON by accumulating until it parses.
        while True:
            if len(buf) > max_accumulated_bytes:
                flush_noise(bytes(buf))
                buf.clear()
                break
            try:
                text = buf.decode("utf-8")
                value, end = decoder.raw_decode(text.lstrip())
                # If there's extra junk after a valid JSON value, treat the whole thing as noise.
                if text[end:].strip():
                    flush_noise(bytes(buf))
                    buf.clear()
                    break
            except json.JSONDecodeError:
                nxt = stdout.readline()
                if not nxt:
                    flush_noise(bytes(buf))
                    buf.clear()
                    break
                buf.extend(nxt)
                continue
            except UnicodeDecodeError:
                flush_noise(bytes(buf))
                buf.clear()
                break

            if isinstance(value, dict) and value.get("jsonrpc") == "2.0":
                init_id = state.get("init_id")
                client_proto = state.get("client_protocol")
                if (
                    init_id is not None
                    and value.get("id") == init_id
                    and isinstance(value.get("result"), dict)
                    and isinstance(client_proto, str)
                ):
                    res = dict(value["result"])
                    if "protocolVersion" in res:
                        res["protocolVersion"] = client_proto
                        value["result"] = res

                out_line = (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")
                sys.stdout.buffer.write(out_line)
                sys.stdout.buffer.flush()
                try:
                    log_fp.write(
                        f"forward_jsonrpc: id={value.get('id')} method={value.get('method')} has_result={'result' in value} has_error={'error' in value}\n"
                    )
                    log_fp.flush()
                except Exception:
                    pass
            else:
                flush_noise(bytes(buf))
            buf.clear()
            break

    if buf:
        flush_noise(bytes(buf))

    return_code = proc.wait()
    try:
        log_fp.write(f"child_exit: {return_code}\n")
        log_fp.flush()
    except Exception:
        pass
    return return_code


def normalize_child_cmd(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    suffix = Path(argv[0]).suffix.lower()
    if suffix in {".cmd", ".bat"}:
        # Windows cannot CreateProcess() a .cmd/.bat directly; run through cmd.exe.
        return ["cmd.exe", "/d", "/s", "/c", argv[0], *argv[1:]]
    return argv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MCP stdio wrapper: keep stdout clean (JSON-RPC only) and redirect noise to stderr/logs."
    )
    parser.add_argument("child", nargs=argparse.REMAINDER, help="Child command and args (use: wrapper.py -- <cmd> [args...])")
    args = parser.parse_args()

    child = args.child
    if child and child[0] == "--":
        child = child[1:]
    if not child:
        write_err(b"wrapper error: missing child command\n")
        return 2

    state: dict = {}
    try:
        child = normalize_child_cmd(child)
        log_path, log_fp = open_log_file_for(child)
        if log_path is not None:
            log_fp.write(f"child_cmd: {child}\n")
        log_fp.flush()

        proc = subprocess.Popen(
            child,
            # IMPORTANT: use an explicit stdin pipe and forward wrapper stdin to it.
            # In some Windows setups, the stdin handle given to this wrapper by Codex is not inheritable
            # by grand-children, which makes "stdin=None" unreliable.
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(REPO_ROOT),
        )

        t_in = threading.Thread(target=forward_stdin_to_child, args=(proc, log_fp, log_path, state), daemon=True)
        t_err = threading.Thread(target=forward_child_stderr, args=(proc, log_fp), daemon=True)
        t_in.start()
        t_err.start()

        rc = jsonrpc_stream_filter(proc, log_fp, state)
        return rc if isinstance(rc, int) else 0
    except Exception as e:
        write_err(f"wrapper error: {e}\n".encode("utf-8", errors="replace"))
        try:
            log_fp.write(f"wrapper exception: {e}\n")
            log_fp.flush()
        except Exception:
            pass
        return 1
    finally:
        try:
            if log_path is not None:
                log_fp.write(f"wrapper_end: {dt.datetime.now().isoformat(timespec='seconds')}\n")
                log_fp.flush()
                log_fp.close()
        except Exception:
            pass
        if log_path is None:
            write_err(b"wrapper log: disabled (workspace read-only)\n")
        else:
            write_err(f"wrapper log: {log_path}\n".encode("utf-8", errors="replace"))


if __name__ == "__main__":
    raise SystemExit(main())
