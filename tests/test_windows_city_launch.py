"""One-command Play City tests: plan composition + full launch over injected fakes.

No Warband/WSE2 process, recorder subprocess or real network probe is started:
every process, clock, netstat, summary and recorder is a fixture. These tests
prove ordering, argv, rotation emission, stop-after-client-exit, artifact sealing
and fail-closed cleanup — never engine or gameplay behaviour.
"""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.city_launch import (  # noqa: E402
    CityLauncher, LaunchError, LaunchPaths, build_launch_plan, main,
    server_config_text, session_commands)
from launcher.engines import CLIENT_NAMES, DEDICATED_NAMES  # noqa: E402
from launcher.rotation import (  # noqa: E402
    build_defender_rotation, build_rotation, rotation_sha256,
    validate_rotation)
from launcher.solo import Session  # noqa: E402

SOURCE_SHA = 'ab' * 32
HOST_PID = 2001
CLIENT_PID = 2002
RECORDER_PID = 500


def pe(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(256)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    path.write_bytes(bytes(data))
    return path


def discovery_report(root, client, dedicated):
    def item(path, kind):
        return {'path': str(path), 'executable': str(path / 'mb_warband.exe')
                if kind == 'warband' else str(path), 'kind': kind,
                'status': 'found', 'provenance': ['fixture'],
                'engine_version': None, 'version_status': 'unknown',
                'ownership': 'unknown', 'runtime_verified': False,
                'confidence': 'medium', 'blockers': []}
    return {'schema_version': 1, 'read_only': True,
            'candidates': [item(root, 'warband')],
            'wse2_candidates': [item(client, 'wse2'), item(dedicated, 'wse2')],
            'ambiguity': False, 'selected': str(root),
            'blockers': [], 'warnings': []}


class GameFixture:
    def __init__(self, root):
        self.root = Path(root)
        self.game = self.root / 'Warband'
        pe(self.game / 'mb_warband.exe')
        (self.game / 'Modules').mkdir(parents=True, exist_ok=True)
        self.client = self.game / CLIENT_NAMES[0]
        self.dedicated = self.game / DEDICATED_NAMES[0]
        pe(self.client)
        pe(self.dedicated)
        self.evidence = self.root / 'evidence'
        self.report = discovery_report(self.game, self.client, self.dedicated)


INSTALLED_OK = {'present': True, 'ok': True, 'module_sha256': 'a' * 64,
                'file_count': 12, 'trigger_count': 31,
                'map_scope': 'city-only', 'problems': [],
                'runtime_verified': False}


def valid_audit(archive, **_kwargs):
    return {'status': 'identity_verified', 'identity_ok': True,
            'crc_status': 'verified', 'seven_zip_available': True,
            'actual_sha256': SOURCE_SHA, 'expected_sha256': SOURCE_SHA,
            'problems': []}


class LaunchPlanTests(unittest.TestCase):
    def test_installed_module_is_reused_without_archive_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GameFixture(tmp)

            def must_not_run(*args, **kwargs):
                raise AssertionError('archive audit must not run for reuse')

            plan = build_launch_plan(
                discovery_report=fixture.report, evidence_root=fixture.evidence,
                installed_status=INSTALLED_OK, audit_runner=must_not_run,
                archive_resolver=must_not_run)
            self.assertTrue(plan['ok'], plan['blockers'])
            self.assertFalse(plan['install']['needed'])
            self.assertIn('installed_city_module_reused', plan['warnings'])
            self.assertEqual(plan['endpoint'], '127.0.0.1:7240')
            self.assertTrue(validate_rotation(plan['rotation']))
            self.assertEqual(plan['team0_bots'], 4)
            self.assertEqual(plan['rotation_profile'], 'defender-squad')
            self.assertIn('set_bot_count 1 4', plan['rotation'])
            self.assertIn('set_bot_count 2 32', plan['rotation'])
            self.assertIn('set_defender_spawn_count 0', plan['rotation'])
            self.assertEqual(plan['rotation_sha256'],
                             rotation_sha256(build_defender_rotation()))
            self.assertEqual(plan['rotation'][-1], 'start')
            self.assertIn('set_respawn_period 5', plan['rotation'])
            self.assertIn('--address', plan['client_argv_suffix'])
            self.assertFalse(plan['runtime_verified'])

    def test_install_plan_consumes_pinned_archive_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GameFixture(tmp)
            archive = fixture.root / 'ZOMBIEEEBeta04.rar'
            archive.write_bytes(b'Rar!\x1a\x07\x00fixture')
            plan = build_launch_plan(
                discovery_report=fixture.report, evidence_root=fixture.evidence,
                archive=str(archive), audit_runner=valid_audit,
                installed_status={'present': False, 'ok': False,
                                  'problems': ['module_missing']})
            self.assertTrue(plan['ok'], plan['blockers'])
            self.assertTrue(plan['install']['needed'])
            install = plan['install']['plan']
            self.assertIn('--city-guardposts', install['build_argv'])
            self.assertIn('--tactical-recovery', install['build_argv'])
            for flag in ('--experimental-defenders', '4', '--wave-reinforcements',
                         '--defender-loadouts', 'balanced-ai'):
                self.assertIn(flag, install['build_argv'])
            self.assertNotIn('--all-map-defenses', install['build_argv'])
            self.assertEqual(install['expected_source_sha256'], SOURCE_SHA)

    def test_install_required_but_disabled_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GameFixture(tmp)
            plan = build_launch_plan(
                discovery_report=fixture.report, evidence_root=fixture.evidence,
                installed_status={'present': False, 'ok': False, 'problems': []},
                allow_install=False)
            self.assertFalse(plan['ok'])
            self.assertIn('install_required_but_disabled', plan['blockers'])

    def test_missing_archive_blocks_install_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GameFixture(tmp)
            plan = build_launch_plan(
                discovery_report=fixture.report, evidence_root=fixture.evidence,
                archive_resolver=lambda: [],
                installed_status={'present': False, 'ok': False, 'problems': []})
            self.assertIn('archive_not_found', plan['blockers'])

    def test_ambiguous_explicit_archives_require_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GameFixture(tmp)
            plan = build_launch_plan(
                discovery_report=fixture.report, evidence_root=fixture.evidence,
                archive=[str(fixture.root / 'a.rar'), str(fixture.root / 'b.rar')],
                audit_runner=valid_audit,
                installed_status={'present': False, 'ok': False, 'problems': []})
            self.assertIn('archive_selection_required', plan['blockers'])

    def test_engine_blockers_propagate_to_the_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GameFixture(tmp)
            report = discovery_report(fixture.game, fixture.client,
                                      fixture.dedicated)
            report['wse2_candidates'] = []
            plan = build_launch_plan(discovery_report=report,
                                     evidence_root=fixture.evidence,
                                     installed_status=INSTALLED_OK)
            self.assertIn('client_not_found', plan['blockers'])
            self.assertIn('dedicated_not_found', plan['blockers'])


class LaunchDefenderProfileTests(unittest.TestCase):
    """One-click City must request A's native team-0 allied squad (981..984)."""

    def _plan(self, tmp, **kwargs):
        fixture = GameFixture(tmp)
        return build_launch_plan(discovery_report=fixture.report,
                                 evidence_root=fixture.evidence,
                                 installed_status=INSTALLED_OK, **kwargs)

    def test_city_default_requests_native_defender_squad(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp)
            self.assertEqual(plan['team0_bots'], 4)
            self.assertEqual(plan['rotation_profile'], 'defender-squad')
            self.assertIn('set_bot_count 1 4', plan['rotation'])
            self.assertIn('set_bot_count 2 32', plan['rotation'])
            self.assertIn('set_defender_spawn_count 0', plan['rotation'])
            self.assertEqual(plan['rotation'], build_defender_rotation())
            self.assertTrue(validate_rotation(plan['rotation']))

    def test_stock_rotation_remains_zero_allies(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp, stock_rotation=True)
            self.assertEqual(plan['team0_bots'], 0)
            self.assertEqual(plan['rotation_profile'], 'stock')
            self.assertIn('set_bot_count 1 0', plan['rotation'])
            self.assertEqual(plan['rotation'], build_rotation())

    def test_explicit_team0_bot_override_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp, team0_bots=0)
            self.assertEqual(plan['rotation_profile'], 'stock')
            self.assertIn('set_bot_count 1 0', plan['rotation'])
            plan = self._plan(tmp, team0_bots=2)
            self.assertEqual(plan['team0_bots'], 2)
            self.assertEqual(plan['rotation_profile'], 'custom-team0')
            self.assertIn('set_bot_count 1 2', plan['rotation'])

    def test_conflicting_or_oversized_allies_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(LaunchError):
                self._plan(tmp, stock_rotation=True, team0_bots=2)
            with self.assertRaises(LaunchError):
                self._plan(tmp, team0_bots=-1)
            with self.assertRaises(LaunchError):
                self._plan(tmp, team0_bots=200)
            with self.assertRaises(LaunchError):
                self._plan(tmp, team0_bots='4')


class LaunchEnemyProfileTests(unittest.TestCase):
    """Enemy staging for the live wave/balance regression; loopback/seal intact."""

    def _plan(self, tmp, **kwargs):
        fixture = GameFixture(tmp)
        return build_launch_plan(discovery_report=fixture.report,
                                 evidence_root=fixture.evidence,
                                 installed_status=INSTALLED_OK, **kwargs)

    def test_generic_is_the_unchanged_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp)
            self.assertEqual(plan['enemy_profile'], 'generic')
            self.assertEqual(plan['team2_bots'], 32)
            self.assertIn('set_bot_count 2 32', plan['rotation'])
            self.assertIn('set_bot_count 1 4', plan['rotation'])

    def test_weak_wave1_stages_a_small_enemy_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp, enemy_profile='weak-wave1')
            self.assertEqual(plan['enemy_profile'], 'weak-wave1')
            self.assertEqual(plan['team2_bots'], 8)
            self.assertIn('set_bot_count 2 8', plan['rotation'])
            self.assertIn('set_bot_count 1 4', plan['rotation'])
            self.assertTrue(validate_rotation(plan['rotation'],
                                              enemy_profile='weak-wave1'))

    def test_native_only_emits_zero_generic_team2(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp, enemy_profile='native-only')
            self.assertTrue(plan['ok'], plan['blockers'])
            self.assertEqual(plan['enemy_profile'], 'native-only')
            self.assertEqual(plan['team2_bots'], 0)
            self.assertIn('set_bot_count 2 0', plan['rotation'])
            self.assertIn('set_bot_count 1 4', plan['rotation'])
            self.assertIn('set_defender_spawn_count 0', plan['rotation'])
            self.assertTrue(validate_rotation(plan['rotation'],
                                              enemy_profile='native-only'))
            self.assertEqual(plan['client_join_address'], '127.0.0.1:7240')

    def test_explicit_team2_override_and_invalid_combinations(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp, enemy_profile='weak-wave1', team2_bots=2)
            self.assertEqual(plan['team2_bots'], 2)
            self.assertIn('set_bot_count 2 2', plan['rotation'])
            with self.assertRaises(LaunchError):
                self._plan(tmp, enemy_profile='native-only', team2_bots=2)
            with self.assertRaises(LaunchError):
                self._plan(tmp, enemy_profile='unknown')
            with self.assertRaises(LaunchError):
                self._plan(tmp, team2_bots=-1)
            with self.assertRaises(LaunchError):
                self._plan(tmp, team2_bots=600)


class LaunchPathTests(unittest.TestCase):
    def test_rotation_config_and_argv_are_private_and_loopback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = LaunchPaths(evidence_root=root / 'ev',
                                game_root=root / 'game',
                                session_id='a' * 32)
            paths.prepare(rotation_lines=build_rotation())
            rotation_text = paths.rotation_path.read_text(encoding='utf-8')
            required = '\n'.join(build_rotation()) + '\n'
            self.assertEqual(rotation_text, required)
            config = paths.config_path.read_text(encoding='utf-8')
            self.assertIn('bLoopbackServer=true', config)
            self.assertIn('sServerAddress=127.0.0.1', config)
            self.assertIn('iServerPort=7240', config)
            self.assertIn('sLogPath=' + paths.host_log.name, config)
            self.assertNotIn('0.0.0.0', config)
            host, client = session_commands(
                dedicated_executable=root / 'ded.exe',
                client_executable=root / 'client.exe',
                config_path=paths.config_path,
                rotation_path=paths.rotation_path)
            self.assertEqual(host[:2], [str(root / 'ded.exe'), '--config-path'])
            self.assertIn('--module', host)
            self.assertIn('-r', host)
            self.assertIn(str(paths.rotation_path), host)
            self.assertEqual(client[-5:], ['--module', 'ZOMBIEEE_Remaster',
                                           '--address', '127.0.0.1:7240', '--no-intro'])
            self.assertIn('--no-intro', client)
            with self.assertRaises(LaunchError):
                paths.prepare(rotation_lines=['start'])

    def test_server_config_rejects_non_loopback_port_or_path_names(self):
        self.assertIn('sServerAddress=127.0.0.1',
                      server_config_text(host_log_name='session.log'))
        for kwargs in ({'host_log_name': 'a/b.log'}, {'host_log_name': 'a\\b.log'},
                       {'host_log_name': ''}, {'host_log_name': 'x', 'port': 0},
                       {'host_log_name': 'x', 'port': 7241}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                server_config_text(**kwargs)


# -- fakes -------------------------------------------------------------------

class FakeProc:
    def __init__(self, pid, *, dead_after_polls=None, exit_code=0):
        self.pid = pid
        self._dead_after = dead_after_polls
        self._polls = 0
        self._exit_code = exit_code

    def poll(self):
        self._polls += 1
        if self._dead_after is not None and self._polls > self._dead_after:
            return self._exit_code
        return None


class FakeChild:
    def __init__(self, *, pid, stdout_path, events, capture_stdin,
                 exit_after_checks=None, on_start=None, exit_code=0):
        self.pid = pid
        self.stdout_path = Path(stdout_path)
        self.events = events
        self.capture_stdin = capture_stdin
        self.exit_after_checks = exit_after_checks
        self.on_start = on_start
        self.returncode = None
        self.running = False
        self.closed = False
        self.started = False
        self.started_argv = None
        self.started_cwd = None
        self.control_lines = []
        self.proc = FakeProc(pid, exit_code=exit_code)

    def start(self, argv, cwd=None, env=None):
        self.started = True
        self.started_argv = list(argv)
        self.started_cwd = str(cwd) if cwd is not None else None
        self.stdout_path.touch(exist_ok=True)
        self.running = True
        self.events.append('child.start:' + str(self.pid))
        if self.on_start is not None:
            self.on_start(self)

    def is_running(self):
        if not self.running:
            return False
        if self.exit_after_checks is not None:
            self.exit_after_checks -= 1
            if self.exit_after_checks <= 0:
                self.running = False
                self.returncode = 0
                self.events.append('child.exit:' + str(self.pid))
        return self.running

    def send_line(self, text):
        self.events.append('child.quit:' + str(self.pid))
        self.control_lines.append(text)
        self.running = False
        self.returncode = 0
        return True

    def terminate(self):
        self.events.append('child.terminate:' + str(self.pid))
        self.running = False
        self.returncode = -1

    def kill(self):
        self.events.append('child.kill:' + str(self.pid))
        self.running = False
        self.returncode = -9

    def wait(self, timeout=None):
        self.running = False
        if self.returncode is None:
            self.returncode = 0
        return self.returncode

    def close(self):
        self.closed = True
        self.events.append('child.close:' + str(self.pid))


class FakeRecorder:
    def __init__(self, *, events, output_root, log_paths, session_id,
                 attempt_id, simulation, marker=True, ready_error=None,
                 accept_attachment=True, evidence_ok=True,
                 dead_after_polls=None):
        self.events = events
        self.output_root = Path(output_root)
        self.log_paths = list(log_paths)
        self.session_id = session_id
        self.attempt_id = attempt_id
        self.simulation = simulation
        self.marker = marker
        self.ready_error = ready_error
        self.accept_attachment = accept_attachment
        self.evidence_ok = evidence_ok
        self.recorder_pid = RECORDER_PID
        self.recorder_start_id = 'start-' + session_id[:8]
        self.attached = None
        self.closed = 0
        self.calls = []
        self.proc = FakeProc(RECORDER_PID, dead_after_polls=dead_after_polls,
                             exit_code=9)
        self.session_dir = self.output_root / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def start(self):
        self.calls.append('start')
        self.events.append('recorder.start')

    def await_ready(self):
        self.calls.append('await_ready')
        if self.ready_error is not None:
            raise self.ready_error
        return {'schema': 'zombieee.recorder-ready.v1',
                'session_id': self.session_id,
                'attempt_id': self.attempt_id,
                'recorder_pid': self.recorder_pid,
                'recorder_start_id': self.recorder_start_id,
                'watcher_id': 'watch-token',
                'log_offsets_captured': True,
                'watcher_active': True,
                'engine_ready': False,
                'mission_ready': False}

    def attach(self, *, host, client):
        self.calls.append('attach')
        self.events.append('recorder.attach')
        if not self.accept_attachment:
            return {'attachment_accepted': False, 'game_ready': False}
        self.attached = {'host_pid': host.pid, 'client_pid': client.pid}
        return {'schema': 'zombieee.recorder-attachment-ack.v1',
                'session_id': self.session_id, 'attempt_id': self.attempt_id,
                'attachment_accepted': True, 'game_ready': False}

    def add_artifact(self, source, name='host_stdout.log'):
        self.calls.append('add_artifact')
        self.events.append('recorder.add_artifact')
        source = Path(source)
        if not source.is_file():
            raise RuntimeError('missing host stdout artifact')
        dest = self.session_dir / name
        dest.write_bytes(source.read_bytes())
        return dest

    def stop_after_exit(self, timeout=30.0):
        self.calls.append('stop_after_exit')
        self.events.append('recorder.stop_after_exit')
        self.attached = None
        return {'receipt': {'schema': 'zombieee.flight.v1',
                            'outcome': 'stopped'},
                'evidence': {'verified': self.evidence_ok, 'file_count': 8}}

    def close(self):
        self.closed += 1
        self.calls.append('close')


class FakeWaiter:
    def __init__(self, *, interrupt=False):
        self.now = 0.0
        self.until_calls = []
        self.sleeps = []
        self.interrupt = interrupt

    def clock(self):
        return self.now

    def until(self, predicate, timeout, interval=None):
        self.until_calls.append(float(timeout))
        deadline = self.now + float(timeout)
        step = 1.0 if interval is None else float(interval)
        while True:
            if predicate():
                return True
            if self.now >= deadline:
                return False
            self.now += min(step, deadline - self.now)

    def pause(self, seconds):
        self.sleeps.append(float(seconds))
        if self.interrupt:
            raise KeyboardInterrupt('fixture interrupt')
        self.now += float(seconds)


def netstat_row(pid):
    def runner(argv, **kwargs):
        return SimpleNamespace(
            stdout='  UDP    127.0.0.1:7240      *:*                                    '
                   + str(pid) + '\n')
    return runner


def no_bind_runner(argv, **kwargs):
    return SimpleNamespace(stdout='')


class Harness:
    def __init__(self, tmp, *, recorder_kwargs=None, waiters=None,
                 host_events=None, client_exit_after=3, host_on_start=None,
                 plan_kwargs=None):
        self.fixture = GameFixture(tmp)
        self.events = []
        self.plan = build_launch_plan(
            discovery_report=self.fixture.report,
            evidence_root=self.fixture.evidence,
            installed_status=INSTALLED_OK, **(plan_kwargs or {}))
        assert self.plan['ok'], self.plan['blockers']
        self.session = Session(route='dedicated', endpoint='127.0.0.1',
                               timeout=900, client_exit_ends_session=True)
        self.waiter = waiters or FakeWaiter()
        kwargs = dict(recorder_kwargs or {})
        self.recorder = FakeRecorder(
            events=self.events, output_root=Path(tmp) / 'unused-flight',
            log_paths=[], session_id='0' * 32, attempt_id='1' * 32,
            simulation=False, **kwargs)
        self.host = None
        self.client = None
        self.client_exit_after = client_exit_after
        self.host_on_start = host_on_start

    def host_factory(self, path, capture_stdin):
        self.host = FakeChild(pid=HOST_PID, stdout_path=path,
                              events=self.events, capture_stdin=capture_stdin,
                              on_start=self.host_on_start)
        return self.host

    def client_factory(self, path, capture_stdin):
        self.client = FakeChild(pid=CLIENT_PID, stdout_path=path,
                                events=self.events, capture_stdin=capture_stdin,
                                exit_after_checks=self.client_exit_after)
        return self.client

    def recorder_factory(self, **kwargs):
        for key in ('output_root', 'log_paths', 'session_id', 'attempt_id',
                    'simulation'):
            setattr(self.recorder, key, kwargs[key])
        self.recorder.session_dir = (Path(kwargs['output_root'])
                                     / kwargs['session_id'])
        self.recorder.session_dir.mkdir(parents=True, exist_ok=True)
        return self.recorder

    def launcher(self, **overrides):
        options = dict(
            session=self.session,
            recorder_factory=self.recorder_factory,
            host_session_factory=self.host_factory,
            client_session_factory=self.client_factory,
            waiter=self.waiter,
            summary_runner=lambda flight: {'status': 'ok', 'verified': True,
                                           'evidence_gaps': []},
            netstat_runner=netstat_row(HOST_PID),
            now_utc=lambda: '2026-10-24T04:00:00+00:00',
        )
        options.update(overrides)
        return CityLauncher(self.plan, **options)


def write_join_markers(child):
    child.stdout_path.write_text(
        'ZDB1|player_joined|role=server|count=1\n'
        'ZDB1|heartbeat|count=1|role=server|game_type=7\n'
        'ZDB1|mission_enter|role=server|template=multiplayer_iv\n',
        encoding='utf-8')


class CityLauncherEnemyProfileTests(unittest.TestCase):
    def test_native_only_launch_writes_zero_team2_and_still_seals(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp, host_on_start=write_join_markers,
                              plan_kwargs={'enemy_profile': 'native-only'})
            launcher = harness.launcher()
            receipt = launcher.run()
            self.assertEqual(receipt['status'], 'stopped', receipt.get('error'))
            self.assertEqual(receipt['enemy_profile'], 'native-only')
            self.assertEqual(receipt['team2_bots'], 0)
            self.assertEqual(receipt['team0_bots'], 4)
            self.assertTrue(receipt['host_bound_loopback'])
            self.assertTrue(receipt['evidence']['verified'])
            rotation_text = launcher.paths.rotation_path.read_text(encoding='utf-8')
            self.assertIn('set_bot_count 2 0', rotation_text)
            self.assertIn('set_bot_count 1 4', rotation_text)


class CityLauncherSuccessTests(unittest.TestCase):
    def test_play_installs_nothing_then_records_and_seals_after_client_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp, host_on_start=write_join_markers)
            launcher = harness.launcher()
            receipt = launcher.run()
            self.assertEqual(receipt['status'], 'stopped', receipt.get('error'))
            self.assertEqual(receipt['lifecycle_outcome'], 'clean_stop')
            self.assertTrue(receipt['host_bound_loopback'])
            self.assertTrue(receipt['join_observed'])
            self.assertTrue(receipt['mission_observed'])
            self.assertEqual(receipt['evidence'],
                             {'verified': True, 'file_count': 8,
                              'recorder_outcome': 'stopped'})
            self.assertEqual(receipt['artifacts'], ['host_stdout.log'])
            self.assertEqual(receipt['evidence_bundle'],
                             'flights/' + harness.session.session_id)
            self.assertEqual(receipt['outcome'], 'unknown')
            self.assertFalse(receipt['runtime_verified'])
            self.assertFalse(receipt['simulation'])
            self.assertTrue(receipt['loopback_only'])
            self.assertEqual(receipt['endpoint'], '127.0.0.1:7240')
            self.assertEqual(receipt['team0_bots'], 4)
            self.assertEqual(receipt['rotation_profile'], 'defender-squad')
            self.assertEqual(receipt['rotation_sha256'],
                             rotation_sha256(build_defender_rotation()))
            self.assertTrue(receipt['host_exit_code'] is not None)

            order = harness.events
            self.assertLess(order.index('recorder.start'),
                            order.index('child.start:' + str(HOST_PID)))
            self.assertLess(order.index('child.start:' + str(HOST_PID)),
                            order.index('child.start:' + str(CLIENT_PID)))
            self.assertLess(order.index('recorder.attach'),
                            order.index('recorder.add_artifact'))
            self.assertLess(order.index('recorder.add_artifact'),
                            order.index('recorder.stop_after_exit'))
            self.assertIn('child.quit:' + str(HOST_PID), order)

            host_argv = harness.host.started_argv
            self.assertIn('--config-path', host_argv)
            self.assertIn('-r', host_argv)
            self.assertIn(str(launcher.paths.rotation_path), host_argv)
            client_argv = harness.client.started_argv
            self.assertEqual(client_argv[-3:], ['--address', '127.0.0.1:7240',
                                              '--no-intro'])
            self.assertIn('--no-intro', client_argv)
            self.assertEqual(harness.host.started_cwd,
                             str(harness.fixture.game))

            paths = launcher.paths
            self.assertTrue(paths.rotation_path.is_file())
            rotation_text = paths.rotation_path.read_text(encoding='utf-8')
            self.assertIn('set_bot_count 1 4', rotation_text)
            self.assertIn('set_bot_count 2 32', rotation_text)
            self.assertTrue(paths.config_path.is_file())
            self.assertTrue(paths.launch_receipt.is_file())
            saved = json.loads(paths.launch_receipt.read_text(encoding='utf-8'))
            self.assertEqual(saved['status'], 'stopped')
            self.assertEqual(saved['session_id'], harness.session.session_id)
            self.assertEqual(harness.session.state, 'stopped')
            self.assertIsNone(harness.session.error)

    def test_join_timeout_is_recorded_not_invented(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp, client_exit_after=2)
            receipt = harness.launcher().run()
            self.assertEqual(receipt['status'], 'stopped', receipt.get('error'))
            self.assertFalse(receipt['join_observed'])
            self.assertFalse(receipt['mission_observed'])
            self.assertIn('join_not_observed_within_timeout',
                          harness.plan['warnings'])
            self.assertEqual(harness.session.state, 'stopped')

    def test_max_minutes_stops_an_attended_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp, client_exit_after=10 ** 6,
                              host_on_start=write_join_markers)
            harness.plan['settings']['max_seconds'] = 5.0
            receipt = harness.launcher().run()
            self.assertEqual(receipt['status'], 'stopped', receipt.get('error'))
            self.assertTrue(harness.waiter.sleeps)


class CityLauncherFailureTests(unittest.TestCase):
    def test_host_never_binding_loopback_fails_before_the_client(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp)
            receipt = harness.launcher(netstat_runner=no_bind_runner).run()
            self.assertEqual(receipt['status'], 'failed')
            self.assertEqual(receipt['lifecycle_outcome'], 'failed')
            self.assertIn('host did not bind loopback', receipt['error'])
            self.assertIsNone(harness.client)
            self.assertGreaterEqual(harness.recorder.closed, 1)
            self.assertNotIn('recorder.add_artifact', harness.events)
            self.assertNotIn('recorder.stop_after_exit', harness.events)
            self.assertTrue(harness.host.closed)

    def test_recorder_readiness_failure_aborts_before_any_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp, recorder_kwargs={
                'ready_error': RuntimeError('recorder crashed')})
            receipt = harness.launcher().run()
            self.assertEqual(receipt['status'], 'failed')
            self.assertIn('recorder crashed', receipt['error'])
            self.assertIsNone(harness.host)
            self.assertGreaterEqual(harness.recorder.closed, 1)

    def test_attachment_rejection_stops_owned_children_without_sealing(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp, recorder_kwargs={'accept_attachment': False})
            receipt = harness.launcher().run()
            self.assertEqual(receipt['status'], 'failed')
            self.assertIn('recorder did not accept', receipt['error'])
            self.assertNotIn('recorder.add_artifact', harness.events)
            self.assertNotIn('recorder.stop_after_exit', harness.events)
            self.assertTrue(harness.host.closed)
            self.assertTrue(harness.client.closed)

    def test_recorder_death_during_play_fails_and_stops_games(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp, recorder_kwargs={'dead_after_polls': 2}, client_exit_after=10 ** 6,
                              host_on_start=write_join_markers)
            receipt = harness.launcher().run()
            self.assertEqual(receipt['status'], 'failed')
            self.assertIsNone(receipt['evidence'])
            self.assertIn('recorder_exited', str(receipt['error']))
            self.assertIn('child.quit:' + str(HOST_PID), harness.events)
            self.assertNotIn('recorder.stop_after_exit', harness.events)
            self.assertGreaterEqual(harness.recorder.closed, 1)

    def test_keyboard_interrupt_is_a_clean_owned_shutdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp, waiters=FakeWaiter(interrupt=True),
                              host_on_start=write_join_markers)
            receipt = harness.launcher().run()
            self.assertEqual(receipt['status'], 'interrupted')
            self.assertIsNone(receipt['evidence'])
            self.assertTrue(harness.recorder.closed >= 1)
            self.assertTrue(harness.host.closed)
            self.assertIn('close', harness.recorder.calls)

    def test_plan_blocked_launcher_refuses_to_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = Harness(tmp)
            harness.plan['ok'] = False
            harness.plan['blockers'] = ['warband_not_found']
            with self.assertRaises(LaunchError):
                harness.launcher()
            self.assertEqual(harness.events, [])


class SessionExitTests(unittest.TestCase):
    def _play_through(self, session):
        session.handle('start', 0)
        identity = {'session_id': session.session_id,
                    'attempt_id': session.attempt_id}
        session.handle('process_started', 0, process='recorder', pid=500,
                       start_id='rec', **identity)
        session.handle('recorder_ready', 0, schema='zombieee.recorder-ready.v1',
                       recorder_pid=500, recorder_start_id='rec',
                       watcher_id='watch', log_offsets_captured=True,
                       watcher_active=True, engine_ready=False,
                       mission_ready=False, recorder_alive=True, **identity)
        session.handle('process_started', 0, process='host', pid=2001,
                       start_id='host', **identity)
        session.handle('host_ready', 0, recorder_alive=True, **identity)
        session.handle('process_started', 0, process='client', pid=2002,
                       start_id='client', **identity)
        session.handle('joined', 0, **identity)
        session.handle('mission_entered', 0, **identity)
        return identity

    def test_client_exit_is_a_normal_end_of_session(self):
        session = Session(route='dedicated', endpoint='127.0.0.1', timeout=900,
                          client_exit_ends_session=True)
        identity = self._play_through(session)
        self.assertEqual(session.state, 'playing')
        self.assertEqual(session.handle('exited', 1, process='client', pid=2002,
                                        start_id='client', **identity),
                         ['stop:host'])
        self.assertTrue(session.client_exit_requested_stop)
        self.assertIsNone(session.error)
        self.assertEqual(session.handle('exited', 1, process='host', pid=2001,
                                        start_id='host', **identity),
                         ['stop:recorder'])
        session.handle('exited', 1, process='recorder', pid=500, start_id='rec',
                       **identity)
        self.assertEqual(session.state, 'stopped')
        self.assertTrue(session.receipt()['client_exit_requested_stop'])

    def test_default_session_still_treats_client_exit_as_a_crash(self):
        session = Session(route='dedicated', endpoint='127.0.0.1', timeout=900)
        identity = self._play_through(session)
        actions = session.handle('exited', 1, process='client', pid=2002,
                                 start_id='client', **identity)
        self.assertIn('stop:host', actions)
        self.assertEqual(session.error, 'client_exited')
        self.assertFalse(session.client_exit_requested_stop)


class CliTests(unittest.TestCase):
    def test_plan_subcommand_is_read_only_and_reports_blockers_as_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GameFixture(tmp)
            archive = fixture.root / 'not-the-pinned-archive.rar'
            archive.write_bytes(b'not a rar')
            code = main(['plan', '--no-known-folders', '--custom-path',
                         str(fixture.game), '--custom-path', str(fixture.client),
                         '--custom-path', str(fixture.dedicated),
                         '--archive', str(archive),
                         '--evidence-root', str(fixture.evidence),
                         '--json'])
            self.assertEqual(code, 2)
            # The plan is blocked before any build/write; the module dir is absent.
            self.assertFalse((fixture.game / 'Modules' / 'ZOMBIEEE_Remaster').exists())

    def test_help_and_unknown_command_handling(self):
        with self.assertRaises(SystemExit):
            main(['rollback'])


if __name__ == '__main__':
    unittest.main()
