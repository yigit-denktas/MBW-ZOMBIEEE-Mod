"""B passive-recorder adapter tests; process fixtures use C's actual CLI.

Unit cases always run. Interop cases run when Agent C's recorder checkout is
available via `ZOMBIEEE_RECORDER_DIR` or a combined checkout containing
`telemetry/flight_recorder.py`; otherwise they skip with an explicit reason.
No Warband/WSE2 process is started; the fake game is an expendable Python child.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.recorder import (  # noqa: E402
    ATTACH_SCHEMA, READY_SCHEMA, CONTROL_KEY_ENV, MAX_READY_BYTES,
    PassiveRecorder, RecorderError, RecorderRejected, RecorderStartTimeout,
    atomic_write_json, canonical_json, sign_control, validate_ready)


def find_c_recorder():
    configured = os.environ.get('ZOMBIEEE_RECORDER_DIR')
    if configured:
        return Path(configured).expanduser().absolute()
    if (REPO / 'telemetry' / 'flight_recorder.py').is_file():
        return REPO
    return None


C_RECORDER_DIR = find_c_recorder()
C_REASON = ('Agent C recorder checkout unavailable; set ZOMBIEEE_RECORDER_DIR '
            'to the agent/c-flight-recorder checkout')


class FakeRecorderProcess:
    def __init__(self, pid=4242, alive=True):
        self.pid = pid
        self._alive = alive

    def poll(self):
        return None if self._alive else 0


def ready_marker(**overrides):
    marker = {
        'schema': READY_SCHEMA, 'session_id': 'fixture-city-01',
        'attempt_id': 'attempt-01', 'recorder_pid': 4242,
        'recorder_start_id': 'fixture-opaque-start-id',
        'watcher_id': 'fixture-random-watch-token',
        'ready_utc': '2026-10-23T00:00:00+00:00',
        'log_offsets_captured': True, 'watcher_active': True,
        'engine_ready': False, 'mission_ready': False, 'log_source_count': 1,
    }
    marker.update(overrides)
    return marker


def spawn_fake_game(seconds=2.0, exit_code=0):
    program = 'import sys, time; time.sleep({}); sys.exit({})'.format(seconds, exit_code)
    return subprocess.Popen([sys.executable, '-c', program])


class AdapterUnitTests(unittest.TestCase):
    def test_signed_control_matches_c_canonical_encoding(self):
        key = bytes.fromhex('22' * 32)
        body = sign_control('attach', key, 'sess-1', 'attempt-1', 'start-1',
                            host_pid=123, client_pid=None)
        self.assertEqual(body['schema'], ATTACH_SCHEMA)
        unsigned = {k: v for k, v in body.items() if k != 'mac'}
        expected = hmac.new(
            key,
            json.dumps(unsigned, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True).encode('utf-8'),
            hashlib.sha256).hexdigest()
        self.assertEqual(body['mac'], expected)
        self.assertEqual(canonical_json(unsigned),
                         json.dumps(unsigned, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True).encode('utf-8'))

    def test_ready_validation_rejects_noncanonical_markers(self):
        validate_ready(ready_marker(), recorder_pid=4242,
                       session_id='fixture-city-01', attempt_id='attempt-01',
                       recorder_start_id='fixture-opaque-start-id')
        for invalid in (
                {'schema': 'zombieee.recorder_ready.v1'},
                {'session_id': 'foreign'}, {'attempt_id': 'stale'},
                {'recorder_pid': 7}, {'recorder_pid': True},
                {'recorder_start_id': 'other'},
                {'watcher_id': ''}, {'watcher_id': None},
                {'log_offsets_captured': False}, {'watcher_active': False},
                {'watcher_active': 1}, {'engine_ready': True},
                {'mission_ready': True}, {'engine_ready': None}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(RecorderRejected):
                    validate_ready(ready_marker(**invalid), recorder_pid=4242,
                                   session_id='fixture-city-01',
                                   attempt_id='attempt-01',
                                   recorder_start_id='fixture-opaque-start-id')

    def adapter_with_marker(self, tmp, marker=None, *, raw=None):
        adapter = PassiveRecorder(output_root=Path(tmp) / 'private',
                                  log_paths=[Path(tmp) / 'game.log'],
                                  session_id='fixture-city-01',
                                  attempt_id='attempt-01',
                                  recorder_start_id='fixture-opaque-start-id')
        (Path(tmp) / 'game.log').write_text('local fixture\n', encoding='utf-8')
        adapter.session_dir.mkdir(parents=True, exist_ok=True)
        adapter.proc = FakeRecorderProcess()
        if raw is not None:
            (adapter.session_dir / 'recorder-ready.json').write_bytes(raw)
        elif marker is not None:
            atomic_write_json(adapter.session_dir / 'recorder-ready.json', marker)
        return adapter

    def test_await_ready_accepts_canonical_marker_and_rejects_bad_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = self.adapter_with_marker(tmp, ready_marker())
            marker = adapter.await_ready(timeout=1)
            self.assertEqual(marker['watcher_id'], 'fixture-random-watch-token')
            self.assertEqual(adapter.ready['recorder_pid'], 4242)

            adapter = self.adapter_with_marker(
                tmp, raw=b'x' * (MAX_READY_BYTES + 1))
            with self.assertRaises(RecorderError):
                adapter.await_ready(timeout=1)

            adapter = self.adapter_with_marker(tmp, ready_marker(engine_ready=True))
            with self.assertRaises(RecorderRejected):
                adapter.await_ready(timeout=1)

    def test_await_ready_rejects_redirected_marker_when_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = self.adapter_with_marker(tmp)
            target = Path(tmp) / 'outside.json'
            atomic_write_json(target, ready_marker())
            try:
                os.symlink(target, adapter.session_dir / 'recorder-ready.json')
            except (OSError, NotImplementedError):
                self.skipTest('symlink creation is not permitted in this context')
            with self.assertRaises(RecorderError):
                adapter.await_ready(timeout=1)

    def test_control_order_is_enforced_locally(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = PassiveRecorder(output_root=Path(tmp) / 'private',
                                      log_paths=[Path(tmp) / 'game.log'],
                                      session_id='order-1', attempt_id='a1',
                                      recorder_start_id='r1')
            (Path(tmp) / 'game.log').write_text('x', encoding='utf-8')
            adapter.proc = FakeRecorderProcess()
            with self.assertRaises(RecorderRejected):
                adapter.attach(host=FakeRecorderProcess(pid=99))
            adapter.ready = ready_marker()
            with self.assertRaises(RecorderRejected):
                adapter.stop_after_exit()

    def test_no_control_key_is_written_into_control_envelopes(self):
        adapter = PassiveRecorder(output_root=Path(tempfile.gettempdir()),
                                  log_paths=[Path(tempfile.gettempdir()) / 'x.log'],
                                  session_id='k-1', attempt_id='a1', recorder_start_id='r1')
        body = sign_control('attach', adapter.control_key, 'k-1', 'a1', 'r1',
                            host_pid=1, client_pid=None)
        serialized = json.dumps(body)
        self.assertNotIn(adapter.control_key.hex(), serialized)
        self.assertNotIn(CONTROL_KEY_ENV, serialized)


@unittest.skipUnless(C_RECORDER_DIR is not None, C_REASON)
class RecorderInteropTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.log = self.tmp / 'game.log'
        self.log.write_text('UNRELATED PRIOR SESSION\n', encoding='utf-8')

    def make_recorder(self, **overrides):
        options = dict(output_root=self.tmp / 'private', log_paths=[self.log],
                       recorder_dir=C_RECORDER_DIR, timeout=120,
                       startup_timeout=20, poll_interval=0.02, simulation=True)
        options.update(overrides)
        return PassiveRecorder(**options)

    def cleanup_game(self, game):
        if game is not None and game.poll() is None:
            game.terminate()
            game.wait(timeout=3)

    def test_recorder_ready_attach_stop_with_verified_evidence(self):
        adapter = self.make_recorder()
        game = None
        try:
            adapter.start()
            self.assertIsNone(game)  # no game exists before readiness
            marker = adapter.await_ready()
            self.assertEqual(marker['recorder_pid'], adapter.recorder_pid)
            self.assertEqual(marker['schema'], READY_SCHEMA)
            self.assertIsNone(adapter.proc.poll())

            game = spawn_fake_game(3.0)
            ack = adapter.attach(host=game)
            self.assertTrue(ack['attachment_accepted'])
            self.assertFalse(ack['game_ready'])
            self.assertIsNone(game.poll())

            game.wait(timeout=5)
            result = adapter.stop_after_exit(timeout=20)
            self.assertEqual(result['receipt']['watch_mode'], 'passive')
            self.assertEqual(result['receipt']['outcome'], 'stopped')
            self.assertEqual(result['receipt']['session_id'], adapter.session_id)
            self.assertTrue(result['evidence']['verified'])
            self.assertGreater(result['evidence']['file_count'], 3)
            self.assertTrue(result['receipt']['simulation'])
            self.assertEqual(result['receipt']['game_runtime'], 'unknown')
            for item in adapter.session_dir.rglob('*'):
                if item.is_file():
                    self.assertNotIn(adapter.control_key.hex().encode(),
                                     item.read_bytes())
        finally:
            self.cleanup_game(game)
            adapter.close()

    def test_forged_hmac_attach_is_rejected_before_valid_attach(self):
        adapter = self.make_recorder()
        game = None
        try:
            adapter.start()
            adapter.await_ready()
            game = spawn_fake_game(3.0)
            forged = sign_control('attach', secrets.token_bytes(32),
                                  adapter.session_id, adapter.attempt_id,
                                  adapter.recorder_start_id,
                                  host_pid=game.pid, client_pid=None)
            atomic_write_json(adapter.session_dir / 'recorder-attach.json', forged)
            time.sleep(0.3)
            self.assertFalse((adapter.session_dir
                              / 'recorder-attachment-ack.json').exists())
            self.assertIsNone(adapter.proc.poll())

            ack = adapter.attach(host=game)
            self.assertTrue(ack['attachment_accepted'])
            game.wait(timeout=5)
            adapter.stop_after_exit(timeout=20)
        finally:
            self.cleanup_game(game)
            adapter.close()

    def test_signed_stop_before_game_exit_is_rejected(self):
        adapter = self.make_recorder()
        game = None
        try:
            adapter.start()
            adapter.await_ready()
            game = spawn_fake_game(3.0)
            adapter.attach(host=game)
            early = sign_control('stop', adapter.control_key, adapter.session_id,
                                 adapter.attempt_id, adapter.recorder_start_id)
            atomic_write_json(adapter.session_dir / 'recorder-stop.json', early)
            time.sleep(0.3)
            self.assertIsNone(adapter.proc.poll())
            self.assertFalse((adapter.session_dir / 'manifest.json').exists())
            with self.assertRaises(RecorderRejected):
                adapter.stop_after_exit(timeout=5)
            self.assertIsNone(adapter.proc.poll())

            game.wait(timeout=5)
            result = adapter.stop_after_exit(timeout=20)
            self.assertEqual(result['receipt']['outcome'], 'stopped')
            events = (adapter.session_dir / 'events.jsonl').read_text(encoding='utf-8')
            self.assertIn('game_process_not_confirmed_exited', events)
        finally:
            self.cleanup_game(game)
            adapter.close()

    def test_late_fatal_log_over_two_mib_is_preserved(self):
        adapter = self.make_recorder()
        game = None
        try:
            adapter.start()
            adapter.await_ready()
            game = spawn_fake_game(3.5)
            adapter.attach(host=game)
            with open(self.log, 'a', encoding='utf-8') as stream:
                stream.write('ZDB1|boot|triggers=35\n')
                stream.write('filler line for bounded capture\n' * 90000)
                stream.write('FATAL ERROR: late simulated crash\n')
            time.sleep(0.8)
            game.wait(timeout=6)
            result = adapter.stop_after_exit(timeout=20)
            snapshot = (adapter.session_dir / 'logs' / 'log_01.txt').read_text(encoding='utf-8')
            self.assertIn('ZDB1|boot|triggers=35', snapshot)
            self.assertIn('FATAL ERROR: late simulated crash', snapshot)
            self.assertIn('ZDB1-OMITTED', snapshot)
            self.assertNotIn('UNRELATED PRIOR SESSION', snapshot)
            self.assertTrue(result['receipt']['log_truncated'][0])
            self.assertGreater(result['receipt']['log_omitted_bytes'][0], 0)
        finally:
            self.cleanup_game(game)
            adapter.close()

    def test_startup_timeout_and_recorder_crash_fail_closed(self):
        adapter = self.make_recorder(
            recorder_command=[sys.executable, '-c', 'import time; time.sleep(5)'],
            startup_timeout=0.5)
        adapter.start()
        try:
            with self.assertRaises(RecorderStartTimeout):
                adapter.await_ready()
        finally:
            adapter.close()

        adapter = self.make_recorder()
        adapter.start()
        try:
            adapter.proc.terminate()
            adapter.proc.wait(timeout=3)
            with self.assertRaises(RecorderError):
                adapter.await_ready(timeout=2)
        finally:
            adapter.close()

    def test_recorder_death_after_ready_blocks_attachment(self):
        adapter = self.make_recorder()
        game = None
        try:
            adapter.start()
            adapter.await_ready()
            adapter.proc.terminate()
            adapter.proc.wait(timeout=3)
            game = spawn_fake_game(2.0)
            with self.assertRaises(RecorderError):
                adapter.attach(host=game)
        finally:
            self.cleanup_game(game)
            adapter.close()

    def test_recorder_crash_leaves_incomplete_recovery_report(self):
        adapter = self.make_recorder()
        game = None
        try:
            adapter.start()
            adapter.await_ready()
            game = spawn_fake_game(3.0)
            adapter.attach(host=game)
            adapter.proc.terminate()
            adapter.proc.wait(timeout=3)
            completed = subprocess.run(
                [sys.executable, '-m', 'telemetry.recovery', str(adapter.session_dir)],
                cwd=str(C_RECORDER_DIR), capture_output=True, text=True, timeout=20)
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertFalse(report['session_complete'])
            self.assertFalse(report['integrity_verified'])
            self.assertFalse(report['shareable_without_review'])
            self.assertEqual(report['game_runtime'], 'unknown')
            self.assertIn(report['observation'],
                          ('incomplete_recorder_session', 'final_manifest_invalid'))
        finally:
            self.cleanup_game(game)
            adapter.close()

    @unittest.skipUnless(os.name == 'nt', 'Win32 creation-time probe is Windows-only')
    def test_windows_process_creation_time_probe_is_queryable_for_fake_game(self):
        game = spawn_fake_game(3.0)
        try:
            code = ('import json, sys; '
                    'from telemetry.identity import windows_start_filetime; '
                    'print(json.dumps({"value": windows_start_filetime(int(sys.argv[1]))}))')
            completed = subprocess.run(
                [sys.executable, '-c', code, str(game.pid)],
                cwd=str(C_RECORDER_DIR), capture_output=True, text=True, timeout=20)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            value = json.loads(completed.stdout)['value']
            self.assertTrue(value is None or
                            (isinstance(value, str) and value.startswith('windows-filetime:')),
                            value)
        finally:
            self.cleanup_game(game)


if __name__ == '__main__':
    unittest.main()
