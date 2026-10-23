"""Read-only process-start identity probes for the passive recorder.

These values are private, local safeguards against PID reuse, not stable public
identifiers or proof of process ownership. None is exported in evidence ZIPs.
An unsupported / denied query returns None and MUST remain unknown.
"""
from __future__ import annotations

import os
from pathlib import Path


def linux_start_ticks(pid: int, proc_root: Path = Path("/proc")) -> str | None:
    """Linux proc stat field 22, parsed after the final ')', without shell/ps."""
    if type(pid) is not int or pid <= 0:
        return None
    try:
        data = (proc_root / str(pid) / "stat").read_text(encoding="ascii")
        tail = data.rsplit(")", 1)[1].strip().split()
        # tail[0] is field 3 (state); field 22 becomes tail[19].
        value = int(tail[19])
        return f"linux-proc-start:{value}" if value >= 0 else None
    except (OSError, ValueError, IndexError):
        return None


def windows_start_filetime(pid: int, kernel=None) -> str | None:
    """Read creation FILETIME through PROCESS_QUERY_LIMITED_INFORMATION.

    Opens only a read/query handle, never PROCESS_TERMINATE; caller must not
    equate a bare PID with a verified B-owned process handle.
    """
    if type(pid) is not int or pid <= 0:
        return None
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    if kernel is None:
        try:
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.GetProcessTimes.argtypes = (
                wintypes.HANDLE, ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
                ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME))
            kernel.GetProcessTimes.restype = wintypes.BOOL
            kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
            kernel.CloseHandle.restype = wintypes.BOOL
        except (OSError, AttributeError):
            return None
    try:
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            created, exited, kernel_time, user_time = (FILETIME() for _ in range(4))
            ok = kernel.GetProcessTimes(
                handle, ctypes.byref(created), ctypes.byref(exited),
                ctypes.byref(kernel_time), ctypes.byref(user_time))
            if not ok:
                return None
            value = (int(created.high) << 32) | int(created.low)
            return f"windows-filetime:{value}" if value else None
        finally:
            kernel.CloseHandle(handle)
    except (OSError, ValueError, TypeError):
        return None


def process_start_identity(pid: int) -> str | None:
    """Best effort only. B's owned process handle is still the authority."""
    if type(pid) is not int or pid <= 0:
        return None
    if os.name == "nt":
        return windows_start_filetime(pid)
    if os.path.isdir("/proc"):
        return linux_start_ticks(pid)
    return None
