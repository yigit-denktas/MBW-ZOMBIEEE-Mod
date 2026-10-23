"""B-owned adapter for Agent C's passive flight recorder (local, offline).

Implements Agent A's RECORDER_LIFECYCLE_V1 and Agent C's canonical marker and
HMAC controls. B starts the recorder first, verifies its readiness and owned
process handle, then may start game children, attach their PIDs, and stop the
recorder only after those children have been confirmed exited.

No network, no public listener, no automatic game launch and no process kills
beyond B's own recorder child. The local control key lives only in the
recorder child's environment; it is never written to argv, logs or receipts.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import time
from pathlib import Path

READY_SCHEMA = 'zombieee.recorder-ready.v1'
ATTACH_SCHEMA = 'zombieee.recorder-attach.v1'
ATTACHMENT_ACK_SCHEMA = 'zombieee.recorder-attachment-ack.v1'
STOP_SCHEMA = 'zombieee.recorder-stop.v1'
RECEIPT_SCHEMA = 'zombieee.flight.v1'
MODULE = 'telemetry.flight_recorder'
CONTROL_KEY_ENV = 'ZOMBIEEE_RECORDER_CONTROL_KEY'
MAX_READY_BYTES = 16 * 1024
MAX_CONTROL_BYTES = 4 * 1024
MAX_RECEIPT_BYTES = 256 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
SESSION_RE = re.compile(r'[A-Za-z0-9_.-]{1,64}\Z')
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


class RecorderError(RuntimeError):
    """The recorder handshake failed closed."""


class RecorderStartTimeout(RecorderError):
    """No valid readiness marker appeared before the startup deadline."""


class RecorderRejected(RecorderError):
    """A control message or evidence assertion was rejected."""


def canonical_json(value):
    """Canonical bytes used by C for HMAC-SHA256 verification."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True).encode('utf-8')


def sign_control(kind, control_key, session_id, attempt_id, recorder_start_id, **fields):
    """Build one canonical signed control envelope for C."""
    body = {'schema': 'zombieee.recorder-' + kind + '.v1',
            'session_id': session_id, 'attempt_id': attempt_id,
            'recorder_start_id': recorder_start_id, **fields}
    body['mac'] = hmac.new(control_key, canonical_json(body), hashlib.sha256).hexdigest()
    return body


def is_redirected(path):
    """True for a symlink or Windows reparse point; missing paths are not links."""
    try:
        info = Path(path).lstat()
    except FileNotFoundError:
        return False
    return bool(stat.S_ISLNK(info.st_mode)
                or getattr(info, 'st_file_attributes', 0) & FILE_ATTRIBUTE_REPARSE_POINT)


def assert_no_redirect(path, *, stop_at):
    """Reject redirects from `stop_at` down to `path`, inclusive.

    Resolution is deliberately not used: it would hide a substituted directory.
    This is a local safety check, not a defense against a concurrent attacker.
    """
    current = Path(path).absolute()
    stop_at = Path(stop_at).absolute()
    while True:
        if current != stop_at and stop_at not in current.parents:
            raise RecorderError('path_outside_private_root')
        if is_redirected(current):
            raise RecorderError('unsafe_redirected_path: ' + str(current))
        if current == stop_at:
            return
        current = current.parent


def atomic_write_json(path, value):
    """Write a complete control/report snapshot atomically within its directory."""
    path = Path(path)
    data = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')
    temp = path.with_name(path.name + '.tmp')
    temp.unlink(missing_ok=True)
    try:
        with open(temp, 'xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_bounded_json(path, limit, *, stop_at):
    """Read a small JSON object from a non-redirected private path."""
    path = Path(path)
    assert_no_redirect(path, stop_at=stop_at)
    with open(path, 'rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise RecorderError('oversized_private_file: ' + path.name)
    try:
        value = json.loads(data.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecorderError('invalid_private_json: ' + path.name) from exc
    if not isinstance(value, dict):
        raise RecorderError('private_json_not_object: ' + path.name)
    return value


def validate_ready(marker, *, recorder_pid, session_id, attempt_id, recorder_start_id):
    """Validate the canonical readiness marker; unknown fields are ignored."""
    if not isinstance(marker, dict) or marker.get('schema') != READY_SCHEMA:
        raise RecorderRejected('wrong_ready_schema')
    if marker.get('session_id') != session_id:
        raise RecorderRejected('wrong_session_id')
    if marker.get('attempt_id') != attempt_id:
        raise RecorderRejected('stale_attempt_id')
    if marker.get('recorder_start_id') != recorder_start_id:
        raise RecorderRejected('wrong_recorder_start_id')
    if type(marker.get('recorder_pid')) is not int or marker['recorder_pid'] != recorder_pid:
        raise RecorderRejected('unowned_recorder_pid')
    watcher_id = marker.get('watcher_id')
    if not isinstance(watcher_id, str) or not watcher_id:
        raise RecorderRejected('missing_watcher_id')
    if marker.get('log_offsets_captured') is not True:
        raise RecorderRejected('log_offsets_not_captured')
    if marker.get('watcher_active') is not True:
        raise RecorderRejected('watcher_not_active')
    if marker.get('engine_ready') is not False:
        raise RecorderRejected('recorder_claims_engine_ready')
    if marker.get('mission_ready') is not False:
        raise RecorderRejected('recorder_claims_mission_ready')
    return marker


def verify_manifest(root, *, stop_at=None):
    """Verify C's SHA-256 manifest over redacted evidence (integrity only)."""
    root = Path(root).absolute()
    stop_at = root if stop_at is None else Path(stop_at).absolute()
    manifest = read_bounded_json(root / 'manifest.json', MAX_MANIFEST_BYTES,
                                 stop_at=stop_at)
    entries = manifest.get('sha256')
    if not isinstance(entries, dict) or not entries:
        raise RecorderRejected('manifest_missing_hashes')
    if manifest.get('schema') != RECEIPT_SCHEMA:
        raise RecorderRejected('manifest_schema_mismatch')
    actual = {}
    for item in root.rglob('*'):
        if item.is_file() and item.name != 'manifest.json' and not item.name.endswith('.tmp'):
            actual[str(item.relative_to(root)).replace(os.sep, '/')] = item
    if set(actual) != set(entries):
        raise RecorderRejected('manifest_entry_mismatch')
    for name, expected in entries.items():
        parts = Path(name).parts
        if not name or name.startswith('/') or '\\' in name or '..' in parts:
            raise RecorderRejected('unsafe_manifest_path')
        item = actual[name]
        if is_redirected(item):
            raise RecorderRejected('unsafe_manifest_redirect')
        digest = hashlib.sha256(item.read_bytes()).hexdigest()
        if not hmac.compare_digest(digest, str(expected)):
            raise RecorderRejected('manifest_hash_mismatch: ' + name)
    return {'verified': True, 'file_count': len(entries)}


class PassiveRecorder:
    """Start, verify, attach and stop one C passive-recorder session."""

    def __init__(self, *, output_root, log_paths, recorder_dir=None,
                 session_id=None, attempt_id=None, recorder_start_id=None,
                 control_key=None, timeout=300.0, startup_timeout=20.0,
                 poll_interval=0.05, python_executable=None,
                 recorder_command=None, environ=None, simulation=False):
        self.output_root = Path(output_root).expanduser().absolute()
        self.log_paths = [Path(p).expanduser().absolute() for p in log_paths]
        if not self.log_paths:
            raise ValueError('at least one log path is required')
        self.recorder_dir = (Path(recorder_dir).expanduser().absolute()
                             if recorder_dir is not None else Path(__file__).resolve().parents[1])
        self.session_id = session_id or secrets.token_hex(16)
        self.attempt_id = attempt_id or secrets.token_hex(8)
        self.recorder_start_id = recorder_start_id or secrets.token_hex(16)
        for name, value in (('session_id', self.session_id),
                            ('attempt_id', self.attempt_id),
                            ('recorder_start_id', self.recorder_start_id)):
            if not SESSION_RE.fullmatch(value) or value in ('.', '..'):
                raise ValueError('invalid opaque ' + name)
        self.control_key = bytes(control_key) if control_key is not None else secrets.token_bytes(32)
        if len(self.control_key) < 32:
            raise ValueError('control key must be at least 256 bits')
        if timeout <= 0 or startup_timeout <= 0 or poll_interval <= 0:
            raise ValueError('timeouts and poll interval must be positive')
        self.timeout = float(timeout)
        self.startup_timeout = float(startup_timeout)
        self.poll_interval = float(poll_interval)
        self.python_executable = python_executable or sys.executable
        self.recorder_command = recorder_command
        self.environ = dict(os.environ if environ is None else environ)
        self.simulation = bool(simulation)
        self.session_dir = self.output_root / self.session_id
        self.proc = None
        self.recorder_pid = None
        self.ready = None
        self.attached = None
        self.game_processes = []
        self._recorder_output = ''

    # -- lifecycle ---------------------------------------------------------

    def start(self):
        if self.proc is not None:
            raise RecorderError('recorder adapter already started')
        self.output_root.mkdir(parents=True, exist_ok=True)
        if is_redirected(self.output_root):
            raise RecorderError('output root is a redirected path')
        if self.session_dir.exists() or is_redirected(self.session_dir):
            raise RecorderRejected('stale session directory; use a fresh attempt')
        if self.recorder_command is None:
            recorder = self.recorder_dir / (MODULE.replace('.', os.sep) + '.py')
            if not recorder.is_file():
                raise RecorderError('Agent C recorder not found at ' + str(recorder))
        argv = self._argv()
        env = dict(self.environ)
        env[CONTROL_KEY_ENV] = self.control_key.hex()
        self.proc = subprocess.Popen(
            argv, cwd=str(self.recorder_dir), env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=False)
        self.recorder_pid = self.proc.pid
        return self

    def _argv(self):
        if self.recorder_command is not None:
            return [str(part) for part in self.recorder_command]
        argv = [self.python_executable, '-m', MODULE, '--passive',
                '--output-root', str(self.output_root),
                '--session', self.session_id,
                '--attempt', self.attempt_id,
                '--recorder-start-id', self.recorder_start_id,
                '--poll', str(self.poll_interval),
                '--timeout', str(self.timeout)]
        if self.simulation:
            argv.append('--simulation')
        for log in self.log_paths:
            argv.extend(['--log', str(log)])
        return argv

    def await_ready(self, timeout=None):
        if self.proc is None:
            raise RecorderError('recorder must be started first')
        deadline = time.monotonic() + (self.startup_timeout if timeout is None else timeout)
        marker_path = self.session_dir / 'recorder-ready.json'
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RecorderError('recorder exited before readiness'
                                    + self._failure_detail())
            try:
                marker = read_bounded_json(marker_path, MAX_READY_BYTES,
                                           stop_at=self.output_root)
            except FileNotFoundError:
                marker = None
            if marker is not None:
                validate_ready(marker, recorder_pid=self.proc.pid,
                               session_id=self.session_id,
                               attempt_id=self.attempt_id,
                               recorder_start_id=self.recorder_start_id)
                if self.proc.poll() is not None:
                    raise RecorderError('recorder died while accepting readiness'
                                        + self._failure_detail())
                self.ready = marker
                return marker
            time.sleep(self.poll_interval)
        raise RecorderStartTimeout('recorder readiness timeout')

    def attach(self, *, host=None, client=None, timeout=10.0):
        if self.ready is None:
            raise RecorderRejected('cannot attach before recorder readiness')
        if self.attached is not None:
            raise RecorderRejected('duplicate attachment')
        processes = [item for item in (host, client) if item is not None]
        pids = []
        for process in processes:
            pid = getattr(process, 'pid', None)
            if type(pid) is not int or pid <= 0:
                raise RecorderRejected('invalid game PID')
            if callable(getattr(process, 'poll', None)) and process.poll() is not None:
                raise RecorderRejected('game process already exited before attach')
            pids.append(pid)
        if not pids:
            raise RecorderRejected('no owned game process to attach')
        ack_path = self.session_dir / 'recorder-attachment-ack.json'
        if ack_path.exists() or is_redirected(ack_path):
            raise RecorderRejected('stale attachment acknowledgment')
        body = sign_control('attach', self.control_key, self.session_id,
                            self.attempt_id, self.recorder_start_id,
                            host_pid=getattr(host, 'pid', None),
                            client_pid=getattr(client, 'pid', None))
        assert_no_redirect(self.session_dir, stop_at=self.output_root)
        atomic_write_json(self.session_dir / 'recorder-attach.json', body)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RecorderError('recorder exited before attachment ack'
                                    + self._failure_detail())
            try:
                ack = read_bounded_json(ack_path, MAX_CONTROL_BYTES,
                                        stop_at=self.output_root)
            except FileNotFoundError:
                time.sleep(self.poll_interval)
                continue
            if (ack.get('schema') != ATTACHMENT_ACK_SCHEMA
                    or ack.get('session_id') != self.session_id
                    or ack.get('attempt_id') != self.attempt_id
                    or ack.get('recorder_start_id') != self.recorder_start_id):
                raise RecorderRejected('mismatched attachment acknowledgment')
            if ack.get('attachment_accepted') is not True:
                raise RecorderRejected('recorder rejected attachment')
            if ack.get('game_ready') is not False:
                raise RecorderRejected('attachment ack wrongly claims game readiness')
            self.attached = ack
            self.game_processes = processes
            return ack
        raise RecorderRejected('attachment acknowledgment timeout')

    def stop_after_exit(self, timeout=30.0):
        if self.attached is None:
            raise RecorderRejected('cannot stop before confirmed attachment')
        for process in self.game_processes:
            poll = getattr(process, 'poll', None)
            if callable(poll) and poll() is None:
                raise RecorderRejected('refusing stop: owned game process still running')
        body = sign_control('stop', self.control_key, self.session_id,
                            self.attempt_id, self.recorder_start_id)
        assert_no_redirect(self.session_dir, stop_at=self.output_root)
        atomic_write_json(self.session_dir / 'recorder-stop.json', body)
        try:
            _, stderr = self.proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise RecorderError('recorder did not finish after signed stop') from exc
        self._recorder_output = stderr.decode('utf-8', errors='replace')[-800:]
        if self.proc.returncode != 0:
            raise RecorderError('recorder exited with code '
                                + str(self.proc.returncode)
                                + self._failure_detail())
        receipt = read_bounded_json(self.session_dir / 'recorder.json',
                                    MAX_RECEIPT_BYTES, stop_at=self.output_root)
        if receipt.get('schema') != RECEIPT_SCHEMA:
            raise RecorderRejected('recorder receipt schema mismatch')
        if receipt.get('outcome') != 'stopped':
            raise RecorderRejected('unexpected recorder outcome: '
                                   + str(receipt.get('outcome')))
        if receipt.get('session_id') != self.session_id:
            raise RecorderRejected('recorder receipt session mismatch')
        evidence = verify_manifest(self.session_dir, stop_at=self.output_root)
        return {'receipt': receipt, 'evidence': evidence}

    def close(self):
        """Stop only B's own recorder child after a failure. Never touches games."""
        if self.proc is None:
            return
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=3)
        try:
            self.proc.communicate(timeout=2)
        except (subprocess.TimeoutExpired, ValueError):
            pass

    def _failure_detail(self):
        if self.proc is None or self.proc.poll() is None:
            return ''
        try:
            _, stderr = self.proc.communicate(timeout=2)
        except (subprocess.TimeoutExpired, ValueError):
            return ''
        self._recorder_output = stderr.decode('utf-8', errors='replace')[-800:]
        text = self._recorder_output.strip()
        return (': ' + text) if text else ''

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
