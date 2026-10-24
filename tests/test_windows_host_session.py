"""Host stdout tee tests with an expendable Python child (no game process)."""
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.host_session import HostSession, HostSessionError  # noqa: E402


class HostSessionTests(unittest.TestCase):
    def test_stdout_is_teed_to_bounded_evidence_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'host_stdout.log'
            session = HostSession(path, max_bytes=1024 * 1024)
            code = 'print("ZDB1|boot|triggers=31"); print("ZDB1|role=server")'
            session.start([sys.executable, '-c', code])
            self.assertEqual(session.wait(timeout=20), 0)
            session.close()
            text = path.read_text(encoding='utf-8')
            self.assertIn('ZDB1|boot|triggers=31', text)
            self.assertIn('ZDB1|role=server', text)
            self.assertFalse(session.truncated)

    def test_oversized_stream_is_truncated_not_unbounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'host_stdout.log'
            session = HostSession(path, max_bytes=16)
            code = 'print("x" * 4096)'
            session.start([sys.executable, '-c', code])
            self.assertEqual(session.wait(timeout=20), 0)
            session.close()
            self.assertLessEqual(path.stat().st_size, 16)
            self.assertTrue(session.truncated)

    def test_stale_stdout_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'host_stdout.log'
            path.write_text('stale', encoding='utf-8')
            session = HostSession(path)
            with self.assertRaises(HostSessionError):
                session.start([sys.executable, '-c', 'print(1)'])

    def test_close_refuses_running_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = HostSession(Path(tmp) / 'host_stdout.log')
            session.start([sys.executable, '-c', 'import time; time.sleep(5)'])
            with self.assertRaises(HostSessionError):
                session.close()
            session.terminate()
            session.wait(timeout=10)
            session.close()


if __name__ == '__main__':
    unittest.main()
