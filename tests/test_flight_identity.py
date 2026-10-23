"""Local start-time identity probes; synthetic data only, no game process."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from telemetry.identity import linux_start_ticks, windows_start_filetime, process_start_identity


class FakeKernel:
    def __init__(self, fail=False):
        self.calls = []
        self.closed = []
        self.fail = fail

    def OpenProcess(self, access, inherited, pid):
        self.calls.append((access, inherited, pid))
        return 417 if not self.fail else 0

    def GetProcessTimes(self, handle, created, exited, kernel, user):
        self.calls.append(("GetProcessTimes", handle))
        if self.fail:
            return 0
        created._obj.low = 12345
        created._obj.high = 7
        return 1

    def CloseHandle(self, handle):
        self.closed.append(handle)


class IdentityTests(unittest.TestCase):
    def test_linux_proc_start_field_22_is_parsed_after_comm(self):
        with tempfile.TemporaryDirectory() as d:
            location = Path(d)
            folder = location / "987"
            folder.mkdir()
            fields = ["S"] + ["0"] * 18 + ["298765"] + ["0"] * 3
            (folder / "stat").write_text(
                "987 (a process ) with parentheses) " + " ".join(fields))
            self.assertEqual(linux_start_ticks(987, location), "linux-proc-start:298765")

    def test_missing_inaccessible_or_invalid_linux_pid_is_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(linux_start_ticks(123456789, Path(d)))
            self.assertIsNone(linux_start_ticks(True, Path(d)))
            self.assertIsNone(linux_start_ticks(0, Path(d)))

    def test_windows_only_queries_creation_time_with_query_limited_rights(self):
        fake = FakeKernel()
        start = windows_start_filetime(842, kernel=fake)
        self.assertEqual(start, f"windows-filetime:{(7 << 32) | 12345}")
        self.assertEqual(fake.calls[0], (0x1000, False, 842))
        self.assertEqual(fake.closed, [417])

    def test_windows_access_failure_is_unknown(self):
        fake = FakeKernel(fail=True)
        self.assertIsNone(windows_start_filetime(842, kernel=fake))
        self.assertEqual(fake.closed, [])

    def test_platform_probe_rejects_wrong_types(self):
        self.assertIsNone(process_start_identity(0))
        self.assertIsNone(process_start_identity(True))
        self.assertIsNone(process_start_identity("17"))


if __name__ == "__main__":
    unittest.main()
