"""Local, bounded crash-surviving recorder for a game/launcher subprocess.

No network, shell, game memory access or automatic evidence upload. Run with
`python -m telemetry.flight_recorder` from the repository root. Python 3.10+.
The child is owned only when launched with --; --observe-pid never kills it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
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


def refuse_links_in_tree(root: Path) -> None:
    """Reject symlinks and Windows reparse points, including ancestor dirs.

    Do not resolve root first: that would hide a substituted 'logs/' junction.
    This is a local safety guard, not a sandbox against concurrent attackers.
    """
    base = Path(root).expanduser().absolute()
    for entry in [base, *base.parents]:
        try:
            meta = entry.lstat()
        except FileNotFoundError:
            continue
        if entry.is_symlink() or getattr(meta, "st_file_attributes", 0) & 0x400:
            raise ValueError("Unsafe recorder path link or reparse point")
    if base.is_dir():
        for entry in base.rglob("*"):
            meta = entry.lstat()
            if entry.is_symlink() or getattr(meta, "st_file_attributes", 0) & 0x400:
                raise ValueError("Unsafe recorder path link or reparse point")


def bounded_window(head: bytes, tail: bytes, total: int, limit: int) -> tuple[bytes, int]:
    """Retain the earliest and latest bytes with an explicit gap if necessary."""
    if total <= limit:
        return head + tail, 0
    # The omission count can change marker length at a power of ten.
    omitted = max(0, total - len(head) - len(tail))
    for _ in range(8):
        marker = (f"\n[ZDB1-OMITTED {omitted} BYTES BETWEEN HEAD AND TAIL]\n").encode()
        room = max(0, limit - len(head) - len(marker))
        kept = tail[-room:] if room else b""
        actual = total - len(head) - len(kept)
        if actual == omitted:
            return head + marker + kept, omitted
        omitted = actual
    marker = (f"\n[ZDB1-OMITTED {omitted} BYTES BETWEEN HEAD AND TAIL]\n").encode()
    room = max(0, limit - len(head) - len(marker))
    return head + marker + (tail[-room:] if room else b""), omitted


def scrub_bounded(data: bytes, limit: int) -> tuple[bytes, int]:
    """Redact before disk write, then re-bound if replacements expand text."""
    clean = scrub(data.decode("utf-8", errors="replace")).encode("utf-8")
    if len(clean) <= limit:
        return clean, 0
    head_size = max(1, limit // 4)
    return bounded_window(clean[:head_size], clean[-(limit - head_size):],
                          len(clean), limit)


class BoundedPipe:
    """Thread-fed bounded head/tail window; never stores unbounded child output."""

    def __init__(self, limit: int):
        self.limit = limit
        self.head_limit = max(1, limit // 4)
        self.tail_limit = limit - self.head_limit
        self.head = bytearray()
        self.tail = bytearray()
        self.seen = 0

    def append(self, chunk: bytes) -> None:
        first = min(len(chunk), self.head_limit - len(self.head))
        self.head.extend(chunk[:first])
        self.tail = bytearray((self.tail + chunk[first:])[-self.tail_limit:])
        self.seen += len(chunk)

    def snapshot(self) -> tuple[bytes, int]:
        return bounded_window(bytes(self.head), bytes(self.tail), self.seen, self.limit)


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
        if value is None:
            clean[key] = None
        elif isinstance(value, str):
            if len(value) > 256:
                raise ValueError("Oversized launcher receipt field")
            clean[key] = scrub(value)
        elif isinstance(value, (int, float, bool)):
            clean[key] = value
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
    """Do not report cumulative system/other-child metrics as game usage.

    A future OS-specific sampler may populate these values only when it has
    measured the owned process itself. A null is deliberately 'unknown'.
    """
    return {"cpu_seconds": None, "peak_memory_kib": None,
            "source": "per-process-sampler-unavailable"}


def record_session(output_root: Path, session_id: str, logs: list[Path],
                   command: list[str] | None = None, observe_pid: int | None = None,
                   timeout: float = 30.0, poll: float = 0.1,
                   max_log_bytes: int = MAX_LOG_BYTES, max_events: int = MAX_EVENTS,
                   launcher_receipt: Path | None = None,
                   attempt_id: str = "1", passive: bool = False,
                   recorder_start_id: str | None = None,
                   control_key: bytes | None = None) -> dict:
    if not SESSION_PATTERN.fullmatch(session_id) or session_id in (".", ".."):
        raise ValueError("Invalid session ID")
    if not SESSION_PATTERN.fullmatch(attempt_id) or attempt_id in (".", ".."):
        raise ValueError("Invalid attempt ID")
    if passive:
        if command is not None or observe_pid is not None:
            raise ValueError("Passive recorder cannot spawn or require a game PID")
        if recorder_start_id is None:
            raise ValueError("Passive recorder requires B's opaque start identity")
        if not isinstance(control_key, bytes) or len(control_key) < 32:
            raise ValueError("Passive recorder requires a 256-bit local control key")
    elif (command is None) == (observe_pid is None):
        raise ValueError("Choose exactly one of a child command or observed PID")
    if recorder_start_id is None:
        recorder_start_id = secrets.token_hex(16)
    if not SESSION_PATTERN.fullmatch(recorder_start_id):
        raise ValueError("Invalid recorder start identity")
    if not 0 < timeout <= 86400 or not 0 < poll <= 60:
        raise ValueError("Invalid timeout or poll interval")
    if not 128 <= max_log_bytes <= MAX_LOG_BYTES or not 2 <= max_events <= MAX_EVENTS:
        raise ValueError("Invalid data bounds")
    if len(logs) > MAX_LOGS:
        raise ValueError("Too many log files")
    receipt = safe_launcher_receipt(launcher_receipt)
    base = output_root.expanduser().resolve()
    root = base / session_id
    root.mkdir(parents=True, exist_ok=False)
    if os.name != "nt":
        os.chmod(root, 0o700)  # private per-user session, best effort on Windows
    (root / "logs").mkdir()
    source_paths = [Path(p).expanduser().resolve() for p in logs]
    offsets = {}
    for index, path in enumerate(source_paths):
        try:
            # Existing logs are not evidence of this run. Record only new bytes.
            offsets[index] = path.stat().st_size
        except OSError:
            offsets[index] = 0
    # Reserve a fixed early portion and a rolling tail. Never grow with log size.
    head_limit = max(1, max_log_bytes // 4)
    tail_limit = max_log_bytes - head_limit
    heads = [bytearray() for _ in source_paths]
    tails = [bytearray() for _ in source_paths]
    seen_bytes = [0] * len(source_paths)
    omitted_bytes = [0] * len(source_paths)
    scrub_omitted_bytes = [0] * len(source_paths)
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

    def append_bytes(i: int, chunk: bytes, count: int) -> None:
        # A huge burst is handled by reading only its earliest and latest bytes,
        # so read amplification and memory stay capped by the configured limit.
        first = min(len(chunk), head_limit - len(heads[i]))
        if first:
            heads[i].extend(chunk[:first])
        remainder = chunk[first:]
        if tail_limit:
            tails[i] = bytearray((tails[i] + remainder)[-tail_limit:])
        seen_bytes[i] += count

    def render_log(i: int) -> bytes:
        saved, omitted = bounded_window(bytes(heads[i]), bytes(tails[i]),
                                        seen_bytes[i], max_log_bytes)
        omitted_bytes[i] = omitted
        return saved

    def sample_logs() -> None:
        for i, path in enumerate(source_paths):
            try:
                size = path.stat().st_size
                if size < offsets[i]:
                    # Replaced/truncated log; previously observed bytes remain
                    # visible, but the provenance discontinuity is explicit.
                    offsets[i] = 0
                    event("log_rotated", log_index=i + 1)
                available = size - offsets[i]
                if available <= 0:
                    continue
                with path.open("rb") as handle:
                    handle.seek(offsets[i])
                    if available <= max_log_bytes:
                        data = handle.read(available)
                    else:
                        early = handle.read(min(available, head_limit - len(heads[i])))
                        handle.seek(size - tail_limit)
                        latest = handle.read(tail_limit)
                        # Account for logical skipped bytes rather than
                        # pretending only the physically read bytes exist.
                        data = early + latest
                append_bytes(i, data, available)
                offsets[i] = size
                saved = render_log(i)
                truncated[i] = omitted_bytes[i] > 0
                clean, extra_omitted = scrub_bounded(saved, max_log_bytes)
                scrub_omitted_bytes[i] = extra_omitted
                atomic_write(root / "logs" / f"log_{i+1:02d}.txt", clean)
                if truncated[i]:
                    event("log_limit", log_index=i + 1, omitted_bytes=omitted_bytes[i])
            except (OSError, RuntimeError) as exc:
                event("log_unavailable", log_index=i + 1,
                      error_type=type(exc).__name__)

    pipe_buffers = {"stdout": BoundedPipe(max_log_bytes),
                    "stderr": BoundedPipe(max_log_bytes)}
    pipe_threads: list[threading.Thread] = []
    output_capture_complete = True

    def drain_stream(pipe, buffer: BoundedPipe) -> None:
        try:
            while True:
                chunk = pipe.read(32 * 1024)
                if not chunk:
                    break
                buffer.append(chunk)
        finally:
            pipe.close()

    attached = False
    last_control_hash = {}

    def control_message(kind: str) -> dict | None:
        # Private, atomic files written by B. The random attempt identity
        # correlates messages; B must also validate its live process handle.
        path = root / ("recorder-" + kind + ".json")
        if not path.exists():
            return None
        if path.is_symlink() or (getattr(path.lstat(), "st_file_attributes", 0) & 0x400):
            event("control_rejected", kind=kind, reason="unsafe_file")
            return None
        try:
            if path.stat().st_size > 4096:
                raise ValueError("oversized")
            data = path.read_bytes()
            fingerprint = digest(data)
            if last_control_hash.get(kind) == fingerprint:
                return None
            last_control_hash[kind] = fingerprint
            value = json.loads(data)
            if (not isinstance(value, dict)
                    or value.get("schema") != "zombieee.recorder-" + kind + ".v1"
                    or value.get("session_id") != session_id
                    or value.get("attempt_id") != attempt_id
                    or value.get("recorder_start_id") != recorder_start_id):
                raise ValueError("mismatched_receipt")
            provided_mac = value.get("mac")
            if not isinstance(provided_mac, str):
                raise ValueError("missing_mac")
            authenticated = {key: part for key, part in value.items() if key != "mac"}
            canonical = json.dumps(authenticated, sort_keys=True,
                                   separators=(",", ":"), ensure_ascii=True).encode()
            expected_mac = hmac.new(control_key, canonical, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(provided_mac, expected_mac):
                raise ValueError("invalid_mac")
            return value
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            event("control_rejected", kind=kind, reason=type(exc).__name__)
            return None

    outcome, exit_code, child = "unknown", None, None
    start = time.monotonic()
    began = utcnow()
    end = None

    def publish_ready() -> None:
        # Agent B must wait for this atomic, per-attempt acknowledgment.
        # Recorder readiness is NOT WSE2, mission or game-host readiness.
        sample_logs()
        event("recorder_ready", session_id=session_id, attempt_id=attempt_id)
        ready = {
            "schema": "zombieee.recorder-ready.v1",
            "session_id": session_id, "attempt_id": attempt_id,
            "recorder_pid": os.getpid(), "recorder_start_id": recorder_start_id,
            "watcher_id": secrets.token_hex(16),
            "ready_utc": utcnow(), "log_offsets_captured": True,
            "watcher_active": True, "log_source_count": len(source_paths),
            "engine_ready": False, "mission_ready": False,
        }
        atomic_write(root / "recorder-ready.json", json_bytes(ready))

    try:
        publish_ready()
        if command is not None:
            if not command:
                raise ValueError("Empty child command")
            try:
                child_env = os.environ.copy()
                child_env.pop("ZOMBIEEE_RECORDER_CONTROL_KEY", None)
                child = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         shell=False, env=child_env)
                for name, pipe in (("stdout", child.stdout), ("stderr", child.stderr)):
                    thread = threading.Thread(target=drain_stream,
                                              args=(pipe, pipe_buffers[name]),
                                              daemon=True, name="zdb1-" + name)
                    thread.start()
                    pipe_threads.append(thread)
            except OSError as exc:
                outcome = "start_failed"
                event("process_start_failed", error_type=type(exc).__name__)
                raise
            event("process_started", owned=True)
        elif passive:
            event("recorder_listening", owned=False, process_identity="unattached")
        else:
            event("process_observed", owned=False,
                  alive_at_start=alive(observe_pid))
        while True:
            sample_logs()
            if passive:
                attachment = control_message("attach") if not attached else None
                if attachment is not None:
                    pids = [attachment.get(key) for key in ("host_pid", "client_pid")]
                    allowed = [pid for pid in pids
                               if type(pid) is int and pid > 0 and pid != os.getpid()]
                    if allowed and all(
                        pid is None or (type(pid) is int and pid > 0 and pid != os.getpid())
                        for pid in pids
                    ):
                        attached = True
                        event("process_attached", claimed_process_count=len(allowed),
                              alive_process_count=sum(alive(pid) is True for pid in allowed))
                        atomic_write(root / "recorder-attachment-ack.json", json_bytes({
                            "schema": "zombieee.recorder-attachment-ack.v1",
                            "session_id": session_id, "attempt_id": attempt_id,
                            "recorder_start_id": recorder_start_id,
                            "attachment_accepted": True,
                            "game_ready": False,
                            "accepted_utc": utcnow(),
                        }))
                    else:
                        event("control_rejected", kind="attach", reason="invalid_pid")
                stop = control_message("stop")
                if stop is not None:
                    outcome = "stopped" if attached else "stopped_without_attachment"
                    break
            if child is not None:
                exit_code = child.poll()
                if exit_code is not None:
                    outcome = "exited"
                    break
            elif not passive:
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
        for thread in pipe_threads:
            thread.join(timeout=2)
            if thread.is_alive():
                output_capture_complete = False
        pipe_omitted = {}
        pipe_scrub_omitted = {}
        for name, stream in pipe_buffers.items():
            # If a descendant keeps an inherited pipe open, this is a
            # partial capture; do not certify it complete.
            if stream.seen:
                saved, omitted = stream.snapshot()
                clean, scrub_extra = scrub_bounded(saved, max_log_bytes)
                atomic_write(root / "logs" / (name + ".txt"), clean)
                pipe_omitted[name] = omitted
                pipe_scrub_omitted[name] = scrub_extra
                if omitted:
                    event("process_output_truncated", stream=name, omitted_bytes=omitted)
            else:
                pipe_omitted[name] = 0
                pipe_scrub_omitted[name] = 0
        end = utcnow()
        event("process_finished", outcome=outcome, exit_code=exit_code)
        safe = {
            "schema": SCHEMA, "session_id": session_id, "attempt_id": attempt_id,
            "watch_mode": "passive" if passive else "owned_child" if child is not None else "external_pid",
            "start_utc": began, "end_utc": end, "outcome": outcome,
            "exit_code": exit_code if child is not None else None,
            "exit_code_observed": child is not None and exit_code is not None,
            "log_count": len(source_paths), "log_bytes_limit_each": max_log_bytes,
            "log_truncated": truncated, "log_omitted_bytes": omitted_bytes,
            "post_redaction_log_omitted_bytes": scrub_omitted_bytes,
            "process_output_omitted_bytes": pipe_omitted,
            "post_redaction_output_omitted_bytes": pipe_scrub_omitted,
            "process_output_capture_complete": output_capture_complete,
            "log_seen_bytes": seen_bytes, "event_count": len(events),
            "duration_seconds": round(time.monotonic() - start, 3),
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
    root = root.expanduser().absolute()
    refuse_links_in_tree(root)
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
        if (root / name).is_symlink():
            raise ValueError("Unsafe recorder manifest symlink")
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
    p.add_argument("--attempt", default="1", help="Opaque launcher retry ID")
    p.add_argument("--passive", action="store_true", help="Arm before B starts game; local attachment/stop control")
    p.add_argument("--recorder-start-id", help="B-supplied opaque process-start correlation")
    # B supplies this only in the spawned recorder's private environment.
    # Never persist or print it, and never pass it to an owned game child.
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
        raw_key = os.environ.get("ZOMBIEEE_RECORDER_CONTROL_KEY", "")
        control_key = bytes.fromhex(raw_key) if raw_key else None
        result = record_session(args.output_root, args.session, args.log,
                                command=cmd if cmd else None,
                                observe_pid=args.observe_pid,
                                timeout=args.timeout, poll=args.poll,
                                launcher_receipt=args.launcher_receipt,
                                attempt_id=args.attempt,
                                passive=args.passive,
                                recorder_start_id=args.recorder_start_id,
                                control_key=control_key)
        print(json.dumps(result, indent=2))
        return 0 if result["outcome"] in ("exited", "disappeared_exit_code_unknown",
                                           "stopped", "stopped_without_attachment") else 2
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Recorder error: {type(error).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
