"""Owned child process whose stdout is teed into a bounded evidence file.

The passive recorder can only attach to PIDs; it cannot read another process's
stdout. The launcher therefore owns the host child and tees its combined
stdout/stderr to a file that can be handed to ``PassiveRecorder.add_artifact``
before the signed stop, so C seals the ZDB1 probe stream inside the flight
bundle (issue #16).

The same owner wrapper is used for the auto-joined client, so both engine
processes are bounded, private children of the launcher. An optional stdin pipe
exists **only** for a graceful host ``quit``; no password, serial or token is
ever written to it.

This module starts no game by itself; tests use an expendable Python child.
"""
from __future__ import annotations

import subprocess
import threading
from pathlib import Path

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
MAX_STDIN_BYTES = 512


class HostSessionError(RuntimeError):
    """The host session could not be started or was used out of order."""


class HostSession:
    def __init__(self, stdout_path, *, max_bytes=DEFAULT_MAX_BYTES,
                 capture_stdin=False):
        self.stdout_path = Path(stdout_path).expanduser().absolute()
        if type(max_bytes) is not int or max_bytes <= 0:
            raise ValueError('max_bytes must be a positive integer')
        if type(capture_stdin) is not bool:
            raise ValueError('capture_stdin must be a boolean')
        self.max_bytes = max_bytes
        self.capture_stdin = capture_stdin
        self.proc = None
        self.returncode = None
        self.truncated = False
        self.captured_bytes = 0
        self._thread = None
        self._stream = None
        self._file = None
        self._stdin = None
        self._lock = threading.Lock()

    def start(self, argv, *, cwd=None, env=None):
        if self.proc is not None:
            raise HostSessionError('host session already started')
        if not isinstance(argv, (list, tuple)) or not argv:
            raise ValueError('argv must be a non-empty list')
        self.stdout_path.parent.mkdir(parents=True, exist_ok=True)
        if self.stdout_path.exists():
            raise HostSessionError('stdout evidence path already exists')
        self._file = open(self.stdout_path, 'xb')
        self.proc = subprocess.Popen(
            [str(part) for part in argv], cwd=None if cwd is None else str(cwd),
            env=env, stdin=subprocess.PIPE if self.capture_stdin else subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        self._stdin = self.proc.stdin if self.capture_stdin else None
        self._stream = self.proc.stdout
        self._thread = threading.Thread(target=self._pump, name='host-stdout-tee',
                                        daemon=True)
        self._thread.start()
        return self

    def _pump(self):
        try:
            while True:
                chunk = self._stream.read(4096)
                if not chunk:
                    return
                with self._lock:
                    remaining = self.max_bytes - self.captured_bytes
                    if remaining <= 0:
                        self.truncated = True
                        continue
                    payload = chunk[:remaining]
                    self._file.write(payload)
                    self._file.flush()
                    self.captured_bytes += len(payload)
                    if len(payload) < len(chunk):
                        self.truncated = True
        finally:
            with self._lock:
                if self._file is not None:
                    self._file.close()
                    self._file = None

    @property
    def pid(self):
        return None if self.proc is None else self.proc.pid

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def send_line(self, text):
        """Write one bounded control line to a capture-stdin child.

        Returns False when stdin was not captured, is already closed or the
        child has exited. Never raises for a dead child: shutdown is best effort
        and the owned handle remains the authority.
        """
        if not self.capture_stdin or self._stdin is None:
            return False
        if not isinstance(text, str) or not text or '\n' in text or '\r' in text:
            raise ValueError('control line must be one non-empty text line')
        if len(text.encode('utf-8')) > MAX_STDIN_BYTES:
            raise ValueError('control line too long')
        if not self.is_running():
            return False
        try:
            self._stdin.write((text + '\n').encode('utf-8'))
            self._stdin.flush()
        except (OSError, ValueError):
            return False
        return True

    def close_stdin(self):
        if self._stdin is not None:
            try:
                self._stdin.close()
            except (OSError, ValueError):
                pass
            self._stdin = None

    def wait(self, timeout=None):
        if self.proc is None:
            raise HostSessionError('host session not started')
        self.returncode = self.proc.wait(timeout=timeout)
        if self._thread is not None:
            self._thread.join(timeout=5)
        self.close_stdin()
        return self.returncode

    def terminate(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()

    def kill(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.kill()

    def close(self):
        if self.proc is not None and self.proc.poll() is None:
            raise HostSessionError('refusing to close a running host')
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5)
        self.close_stdin()
        with self._lock:
            if self._file is not None:
                self._file.close()
                self._file = None
