"""B artifact-sealing and transient-read race tests (no game process)."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import launcher.recorder as recorder  # noqa: E402
from launcher.recorder import (  # noqa: E402
    PassiveRecorder, READY_SCHEMA, RecorderRejected)


class FakeProcess:
    pid = 4242

    def poll(self):
        return None


class ArtifactSealingTests(unittest.TestCase):
    def _adapter(self, tmp):
        log = Path(tmp) / 'dedicated.log'
        log.write_text('log', encoding='utf-8')
        adapter = PassiveRecorder(output_root=Path(tmp) / 'private',
                                  log_paths=[log], session_id='sess-art',
                                  attempt_id='attempt-art',
                                  recorder_start_id='start-art')
        adapter.output_root.mkdir(parents=True, exist_ok=True)
        adapter.session_dir.mkdir(parents=True, exist_ok=True)
        adapter.attached = {'schema': 'zombieee.recorder-attachment-ack.v1'}
        return adapter

    def test_host_stdout_artifact_is_copied_into_flight_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = self._adapter(tmp)
            source = Path(tmp) / 'host_stdout.log'
            source.write_text('ZDB1|role=server|game_type=7\n', encoding='utf-8')
            dest = adapter.add_artifact(source)
            self.assertEqual(dest, adapter.session_dir / 'host_stdout.log')
            self.assertIn('game_type=7', dest.read_text(encoding='utf-8'))

    def test_artifact_rejects_bad_names_and_oversize(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = self._adapter(tmp)
            source = Path(tmp) / 'host_stdout.log'
            source.write_text('0123456789', encoding='utf-8')
            with self.assertRaises(RecorderRejected):
                adapter.add_artifact(source, name='../escape.log')
            with self.assertRaises(RecorderRejected):
                adapter.add_artifact(source, limit=4)

    def test_artifact_requires_attachment(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = self._adapter(tmp)
            adapter.attached = None
            source = Path(tmp) / 'host_stdout.log'
            source.write_text('x', encoding='utf-8')
            with self.assertRaises(RecorderRejected):
                adapter.add_artifact(source)


class TransientReadTests(unittest.TestCase):
    def test_await_ready_survives_one_permission_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'dedicated.log'
            log.write_text('log', encoding='utf-8')
            adapter = PassiveRecorder(output_root=Path(tmp) / 'private',
                                      log_paths=[log], session_id='sess-race',
                                      attempt_id='attempt-race',
                                      recorder_start_id='start-race',
                                      poll_interval=0.01)
            adapter.output_root.mkdir(parents=True, exist_ok=True)
            adapter.session_dir.mkdir(parents=True, exist_ok=True)
            adapter.proc = FakeProcess()
            marker = {
                'schema': READY_SCHEMA, 'session_id': adapter.session_id,
                'attempt_id': adapter.attempt_id,
                'recorder_pid': 4242,
                'recorder_start_id': adapter.recorder_start_id,
                'watcher_id': 'watch-token',
                'ready_utc': '2026-10-24T00:00:00+00:00',
                'log_offsets_captured': True, 'watcher_active': True,
                'engine_ready': False, 'mission_ready': False,
            }
            calls = {'n': 0}

            def fake_read(*args, **kwargs):
                calls['n'] += 1
                if calls['n'] == 1:
                    raise PermissionError('simulated atomic replace')
                return marker

            with mock.patch.object(recorder, 'read_bounded_json', side_effect=fake_read):
                self.assertEqual(adapter.await_ready(timeout=2), marker)
            self.assertGreaterEqual(calls['n'], 2)


if __name__ == '__main__':
    unittest.main()
