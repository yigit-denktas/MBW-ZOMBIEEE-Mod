"""Non-destructive Windows process observation, tested without Windows/game."""
import unittest
from telemetry.flight_recorder import windows_pid_alive, alive


class FakeKernel:
    def __init__(self, result, handle=123, last_error=0):
        self.result = result
        self.handle = handle
        self.last_error = last_error
        self.closed = []
        self.calls = []

    def OpenProcess(self, access, inherit, pid):
        self.calls.append((access, inherit, pid))
        return self.handle

    def WaitForSingleObject(self, handle, delay):
        self.calls.append(("wait", handle, delay))
        return self.result

    def CloseHandle(self, handle):
        self.closed.append(handle)


class WindowsPidSafetyTests(unittest.TestCase):
    def test_running_query_never_requests_terminate_privilege(self):
        kernel = FakeKernel(0x102)
        self.assertTrue(windows_pid_alive(8484, kernel))
        self.assertEqual(kernel.calls[0], (0x00100000, False, 8484))
        self.assertEqual(kernel.closed, [123])

    def test_exited_process_is_detected_without_signal(self):
        kernel = FakeKernel(0)
        self.assertFalse(windows_pid_alive(8484, kernel))
        self.assertEqual(kernel.closed, [123])

    def test_failed_wait_is_unknown_and_handle_closed(self):
        kernel = FakeKernel(0xFFFFFFFF)
        self.assertIsNone(windows_pid_alive(8484, kernel))
        self.assertEqual(kernel.closed, [123])

    def test_access_denied_is_unknown_not_absent(self):
        kernel = FakeKernel(None, handle=0, last_error=5)
        self.assertIsNone(windows_pid_alive(8484, kernel))
        self.assertEqual(kernel.closed, [])

    def test_invalid_pid_is_absent_if_windows_reports_invalid_parameter(self):
        kernel = FakeKernel(None, handle=0, last_error=87)
        self.assertFalse(windows_pid_alive(8484, kernel))
        self.assertEqual(kernel.closed, [])

    def test_posix_id_validation_rejects_bool_and_zero(self):
        self.assertIsNone(alive(True))
        self.assertIsNone(alive(0))


if __name__ == "__main__":
    unittest.main()
