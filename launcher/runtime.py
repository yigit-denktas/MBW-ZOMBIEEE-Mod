"""Small portable probes for the one-click launcher (no engine semantics).

The launcher may not treat process creation, a log line or a bound socket as
gameplay evidence. These helpers only answer bounded, observable questions:

* did the **owned dedicated child** bind exactly IPv4 loopback ``127.0.0.1:7240``
  (observed read-only via ``netstat``; no firewall or listener is touched)?
* does a bounded tail of the host stdout tee contain a probe marker?
* wait for a predicate with a monotonic deadline, without busy-looping.

Everything is injectable so offline tests never start a game. No network call,
no firewall change, no public bind and no process memory access happen here.
"""
from __future__ import annotations

import math
import os
import subprocess
import time
from pathlib import Path

LOOPBACK_HOST = '127.0.0.1'
LOOPBACK_PORT = 7240
ENDPOINT = LOOPBACK_HOST + ':' + str(LOOPBACK_PORT)
MAX_TAIL_BYTES = 256 * 1024

# C's passive recorder writes these markers into the dedicated host's stdout
# (which the launcher tees). They are observations, not acceptance verdicts.
JOIN_MARKERS = ('ZDB1|player_joined', 'ZDB1|mission_enter', 'ZDB1|heartbeat')
MISSION_MARKERS = ('ZDB1|mission_enter', 'ZDB1|round_started', 'ZDB1|heartbeat')


class ProbeError(ValueError):
    """A probe was configured outside its documented bounds."""


def is_loopback_endpoint(value):
    """True only for the literal IPv4 loopback endpoint the launcher supports."""
    if not isinstance(value, str) or value.count(':') != 1:
        return False
    host, _, port = value.partition(':')
    if host != LOOPBACK_HOST or not port.isdigit():
        return False
    return 1 <= int(port) <= 65535


def loopback_addresses(*, runner=None, timeout=15):
    """Parse ``netstat -ano`` for exact loopback addresses (read-only)."""
    if runner is None:
        def runner(argv, **kwargs):
            return subprocess.run(argv, capture_output=True, text=True,
                                  timeout=kwargs.get('timeout', timeout),
                                  shell=False)
    try:
        completed = runner(['netstat', '-ano'], timeout=timeout)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return []
    text = completed.stdout if isinstance(completed.stdout, str) else ''
    rows = []
    for line in text.splitlines():
        tokens = line.split()
        if len(tokens) < 4 or tokens[0].upper() not in ('TCP', 'UDP'):
            continue
        local, pid = tokens[1], tokens[-1]
        if not pid.isdigit():
            continue
        if local.startswith(LOOPBACK_HOST + ':'):
            rows.append((local, int(pid)))
    return rows


def host_bound_loopback(pid, *, endpoint=None, runner=None, timeout=15):
    """True when the supplied owned PID has an exact loopback listener row."""
    if type(pid) is not int or pid <= 0:
        return False
    target = endpoint or (LOOPBACK_HOST + ':' + str(LOOPBACK_PORT))
    if not is_loopback_endpoint(target):
        return False
    return any(address == target and owner == pid
               for address, owner in loopback_addresses(runner=runner, timeout=timeout))


def read_text_tail(path, *, limit=MAX_TAIL_BYTES):
    """Bounded tail of a private text file; missing/unreadable stays empty."""
    path = Path(path)
    try:
        with open(path, 'rb') as stream:
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(max(0, size - limit))
            data = stream.read(limit)
    except (OSError, ValueError):
        return ''
    return data.decode('utf-8', errors='replace')


def contains_marker(path, markers, *, limit=MAX_TAIL_BYTES):
    text = read_text_tail(path, limit=limit)
    return any(marker in text for marker in markers)


def _finite_positive(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ProbeError(name + ' must be a number')
    if not math.isfinite(float(value)) or value <= 0:
        raise ProbeError(name + ' must be finite and positive')
    return float(value)


class Waiter:
    """Deterministic bounded waiting with injectable clock/sleep.

    ``until`` returns ``True`` as soon as the predicate holds and ``False`` at
    the deadline; it always evaluates the predicate at least once. Timeouts are
    observations, never permission to claim readiness.
    """

    def __init__(self, *, clock=time.monotonic, sleep=time.sleep, interval=1.0):
        self.clock = clock
        self.sleep = sleep
        self.interval = _finite_positive(interval, 'interval')

    def until(self, predicate, timeout, *, interval=None):
        if not callable(predicate):
            raise ProbeError('predicate must be callable')
        timeout = float(timeout)
        if not math.isfinite(timeout) or timeout < 0:
            raise ProbeError('timeout must be finite and non-negative')
        step = _finite_positive(self.interval if interval is None else interval,
                                'interval')
        deadline = self.clock() + timeout
        while True:
            if predicate():
                return True
            remaining = deadline - self.clock()
            if remaining <= 0:
                return False
            self.sleep(min(step, remaining))

    def pause(self, seconds):
        seconds = float(seconds)
        if not math.isfinite(seconds) or seconds < 0:
            raise ProbeError('pause must be finite and non-negative')
        self.sleep(seconds)
