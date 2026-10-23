"""Local, bounded crash-surviving recorder for a game/launcher subprocess.

No network, shell, game memory access or automatic evidence upload. Run with
`python -m telemetry.flight_recorder` from the repository root. Python 3.10+.
The child is owned only when launched with --; --observe-pid never kills it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from .privacy import scrub

SCHEMA = "zombieee.flight.v1"
MAX_LOG_BYTES = 2 * 1024 * 1024
MAX_EVENTS = 2048
MAX_LOGS = 12
SESSION_PATTERN = re.compile(r"[A-Za-z0-9_.-]{1,64}\Z")
RECEIPT_KEYS = (
    "schema", "session_id", "mode", "city", "mission", "build_manifest_sha256",
    "wse2_version", "start_utc", "end_utc", "host_exit_code",
    "client_exit_code", "outcome",
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    """Replace a complete snapshot; never expose a partially written report."""
    temp = path.with_name(path.name + ".tmp")
    temp.unlink(missing_ok=True)  # a recorder crash may leave an orphan snapshot
    try:
        with temp.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def safe_launcher_receipt(path: Path | None) -> dict | None:
    """Allowlist B's provisional receipt. Exclude PIDs, paths and command lines."""
    if path is None:
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != "zombieee.session.v1":
        raise ValueError("Unknown launcher receipt schema")
    clean = {}
    for key in RECEIPT_KEYS:
        value = raw.get(key)
        if value is None or isinstance(value, (str, int, float, bool)):
            # Redact unexpected identifiers even in allowlisted text fields.
            clean[key] = scrub(value) if isinstance(value, str) else value
    return clean


def alive(pid: int) -> bool | None:
    """Best-effort external PID observation; no exit-code inference."""
    if pid <= 0:
        return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return None


def child_metrics() -> dict:
    """Only publish measured child usage, never estimated Windows CPU/RAM."""
    try:
        import resource  # unavailable on standard Windows Python
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        return {
            "cpu_seconds": round(usage.ru_utime + usage.ru_stime, 3),
            "peak_memory_kib": usage.ru_maxrss if sys.platform.startswith("linux") else None,
            "source": "resource.RUSAGE_CHILDREN",
        }
    except (ImportError, OSError, ValueError):
        return {"cpu_seconds": None, "peak_memory_kib": None, "source": "unavailable"}


def record_session(output_root: Path, session_id: str, logs: list[Path],
                   command: list[str] | None = None, observe_pid: int | None = None,
                   timeout: float = 30.0, poll: float = 0.1,
                   max_log_bytes: int = MAX_LOG_BYTES, max_events: int = MAX_EVENTS,
                   launcher_receipt: Path | None = None) -> dict:
    if not SESSION_PATTERN.fullmatch(session_id) or session_id in (".", ".."):
        raise ValueError("Invalid session ID")
    if (command is None) == (observe_pid is None):
        raise ValueError("Choose exactly one of a child command or observed PID")
    if not 0 < timeout <= 86400 or not 0 < poll <= 60:
        raise ValueError("Invalid timeout or poll interval")
    if not 1 <= max_log_bytes <= MAX_LOG_BYTES or not 2 <= max_events <= MAX_EVENTS:
        raise ValueError("Invalid data bounds")
    if len(logs) > MAX_LOGS:
        raise ValueError("Too many log files")
    receipt = safe_launcher_receipt(launcher_receipt)
    base = output_root.expanduser().resolve()
    root = base / session_id
    root.mkdir(parents=True, exist_ok=False)
    (root / "logs").mkdir()
    source_paths = [Path(p).expanduser().resolve() for p in logs]
    offsets = {}
    for index, path in enumerate(source_paths):
        try:
            # Existing logs are not evidence of this run. Record only new bytes.
            offsets[index] = path.stat().st_size
        except OSError:
            offsets[index] = 0
    raw_logs = [bytearray() for _ in source_paths]
    truncated = [False] * len(source_paths)
    events = []
    event_drops = 0

    def event(name: str, **fields) -> None:
        nonlocal event_drops
        if len(events) >= max_events:
            event_drops += 1
            return
        events.append({"schema": SCHEMA, "event": name, "utc": utcnow(), **fields})
        atomic_write(root / "events.jsonl",
                     b"".join(json.dumps(e, sort_keys=True, separators=(",", ":")).encode() + b"\n"
                              for e in events))

    def sample_logs() -> None:
        for i, path in enumerate(source_paths):
            try:
                size = path.stat().st_size
                if size < offsets[i]:
                    offsets[i] = 0
                    event("log_rotated", log_index=i + 1)
                available = size - offsets[i]
                if available <= 0:
                    continue
                room = max_log_bytes - len(raw_logs[i])
                # Advance to EOF if budget exhausted: no hidden accumulation.
                if room <= 0:
                    offsets[i] = size
                    if not truncated[i]:
                        truncated[i] = True
                        event("log_limit", log_index=i + 1)
                    continue
                with path.open("rb") as handle:
                    handle.seek(offsets[i])
                    data = handle.read(min(available, room))
                offsets[i] += len(data)
                raw_logs[i].extend(data)
                if available > len(data):
                    offsets[i] = size
                    truncated[i] = True
                    event("log_limit", log_index=i + 1)
                # Scrub the *whole* accumulated text, so secrets split across
                # poll boundaries never reach the on-disk snapshot.
                clean = scrub(raw_logs[i].decode("utf-8", errors="replace"))
                atomic_write(root / "logs" / f"log_{i+1:02d}.txt", clean.encode())
            except (OSError, RuntimeError) as exc:
                event("log_unavailable", log_index=i + 1,
                      error_type=type(exc).__name__)

    outcome, exit_code, child = "unknown", None, None
    start = time.monotonic()
    began = utcnow()
    end = None
    try:
        if command is not None:
            if not command:
                raise ValueError("Empty child command")
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     shell=False)
            event("process_started", owned=True)
        else:
            event("process_observed", owned=False,
                  alive_at_start=alive(observe_pid))
        while True:
            sample_logs()
            if child is not None:
                exit_code = child.poll()
                if exit_code is not None:
                    outcome = "exited"
                    break
            else:
                state = alive(observe_pid)
                if state is False:
                    outcome = "disappeared_exit_code_unknown"
                    break
            if time.monotonic() - start >= timeout:
                outcome = "timeout"
                break
            time.sleep(poll)
    except KeyboardInterrupt:
        outcome = "interrupted"
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                exit_code = child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                exit_code = child.wait(timeout=3)
        if child is not None and exit_code is None:
            exit_code = child.poll()
        sample_logs()
        end = utcnow()
        event("process_finished", outcome=outcome, exit_code=exit_code)
        safe = {
            "schema": SCHEMA, "session_id": session_id,
            "start_utc": began, "end_utc": end, "outcome": outcome,
            "exit_code": exit_code if child is not None else None,
            "exit_code_observed": child is not None and exit_code is not None,
            "log_count": len(source_paths), "log_bytes_limit_each": max_log_bytes,
            "log_truncated": truncated, "event_count": len(events),
            "event_drops": event_drops,
            "metrics": child_metrics() if child is not None else {
                "cpu_seconds": None, "peak_memory_kib": None, "source": "unavailable"},
            "launcher": receipt,
            "caveat": "Process exit is not proof of game startup, a playable wave or valid AI.",
        }
        atomic_write(root / "recorder.json", json_bytes(safe))
        # Explicit per-file digests over redacted outputs, not original game logs.
        files = [p for p in root.rglob("*") if p.is_file()
                 and p.name != "manifest.json" and not p.name.endswith(".tmp")]
        manifest = {"schema": SCHEMA, "sha256": {
            str(p.relative_to(root)).replace(os.sep, "/"): digest(p.read_bytes())
            for p in sorted(files)}}
        atomic_write(root / "manifest.json", json_bytes(manifest))
    return safe


def verify_recording(root: Path) -> dict:
    """Verify the recorded snapshots after completion (integrity, not authenticity)."""
    root = root.expanduser().resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    expected = manifest.get("sha256")
    if manifest.get("schema") != SCHEMA or not isinstance(expected, dict):
        raise ValueError("Recorder manifest schema mismatch")
    actual = {str(p.relative_to(root)).replace(os.sep, "/") for p in root.rglob("*")
              if p.is_file() and not p.name.endswith(".tmp") and p.name != "manifest.json"}
    if set(expected) != actual or "recorder.json" not in expected:
        raise ValueError("Recorder manifest entry mismatch")
    for name, h in expected.items():
        if name.startswith("/") or "\\" in name or ".." in Path(name).parts:
            raise ValueError("Unsafe recorder manifest path")
        if digest((root / name).read_bytes()) != h:
            raise ValueError("Recorder SHA-256 integrity failure: " + name)
    receipt = json.loads((root / "recorder.json").read_text(encoding="utf-8"))
    if receipt.get("schema") != SCHEMA:
        raise ValueError("Recorder receipt schema mismatch")
    return {"verified": True, "file_count": len(expected), "session_id": receipt.get("session_id")}



def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--session", required=True)
    p.add_argument("--log", action="append", type=Path, default=[])
    p.add_argument("--launcher-receipt", type=Path)
    p.add_argument("--observe-pid", type=int)
    p.add_argument("--timeout", type=float, default=30)
    p.add_argument("--poll", type=float, default=0.1)
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args()
    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    try:
        result = record_session(args.output_root, args.session, args.log,
                                command=cmd if cmd else None,
                                observe_pid=args.observe_pid,
                                timeout=args.timeout, poll=args.poll,
                                launcher_receipt=args.launcher_receipt)
        print(json.dumps(result, indent=2))
        return 0 if result["outcome"] in ("exited", "disappeared_exit_code_unknown") else 2
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Recorder error: {type(error).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
