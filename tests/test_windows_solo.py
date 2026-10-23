"""Fake events prove ordering and correlation, never engine semantics."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from launcher.solo import Session


class FakeHarness:
    def __init__(self, route='dedicated'):
        self.session = Session(route=route, timeout=10)
        self.running = set()
        self.identities = {}
        self.actions = []
        self.now = 0

    def send(self, event, now=None, **data):
        now = self.now if now is None else now
        if event not in ('start', 'stop', 'tick'):
            data.setdefault('session_id', self.session.session_id)
            data.setdefault('attempt_id', self.session.attempt_id)
        if event == 'host_ready':
            data.setdefault('recorder_alive', 'recorder' in self.running)
        actions = self.session.handle(event, now, **data)
        self.now = now
        self.actions.extend(actions)
        return actions

    def started(self, process):
        identity = {'pid': 100 + len(self.identities), 'start_id': 'fake-' + process}
        self.identities[process] = identity
        self.running.add(process)
        return self.send('process_started', process=process, **identity)

    def recorder_ready(self, **overrides):
        identity = self.identities['recorder']
        data = {'schema': 'zombieee.recorder-ready.v1',
                'recorder_pid': identity['pid'], 'recorder_start_id': identity['start_id'],
                'watcher_id': 'fixture-random-watch-token',
                'log_offsets_captured': True, 'watcher_active': True,
                'engine_ready': False, 'mission_ready': False,
                'recorder_alive': 'recorder' in self.running}
        data.update(overrides)
        return self.send('recorder_ready', **data)

    def exited(self, process):
        self.running.discard(process)
        return self.send('exited', process=process, **self.identities[process])

    def boot_host(self):
        self.send('start')
        self.started('recorder')
        self.recorder_ready()
        self.started('host' if self.session.route == 'dedicated' else 'client')

    def play(self):
        self.boot_host()
        self.send('host_ready')
        if self.session.route == 'dedicated':
            self.started('client')
        self.send('joined')
        self.send('mission_entered')


class SoloTests(unittest.TestCase):
    def test_no_game_requested_before_live_correlated_recorder_ready(self):
        for route, process in (('dedicated', 'host'), ('listen', 'client')):
            with self.subTest(route=route):
                h = FakeHarness(route)
                self.assertEqual(h.send('start'), ['start:recorder'])
                self.assertEqual(h.session.state, 'waiting_recorder')
                self.assertEqual(h.session.active, {'recorder'})
                h.started('recorder')
                self.assertEqual(h.actions, ['start:recorder'])
                self.assertEqual(h.recorder_ready(), ['start:' + process])
                self.assertEqual(h.session.state, 'waiting_game_start')
                h.started(process)
                self.assertEqual(h.session.state, 'waiting_host')

    def test_recorder_ready_needs_canonical_marker_and_live_identity(self):
        h = FakeHarness()
        h.send('start')
        self.assertEqual(h.send('recorder_ready', schema='zombieee.recorder-ready.v1',
                                recorder_pid=100, recorder_start_id='fake-recorder',
                                recorder_alive=True), [])
        h.started('recorder')
        for invalid in ({'recorder_pid': 999}, {'recorder_start_id': 'reused-pid'},
                        {'recorder_alive': False}, {'recorder_alive': 1}, {'schema': 'old'},
                        {'log_offsets_captured': False}, {'watcher_active': False},
                        {'watcher_active': 1}, {'engine_ready': True},
                        {'mission_ready': True}, {'engine_ready': None},
                        {'watcher_id': ''}, {'watcher_id': None}):
            with self.subTest(invalid=invalid):
                self.assertEqual(h.recorder_ready(**invalid), [])
                self.assertEqual(h.session.state, 'waiting_recorder')
        self.assertEqual(h.recorder_ready(), ['start:host'])
        self.assertEqual(h.recorder_ready(), [])
        self.assertEqual(h.session.state, 'waiting_game_start')

    def test_canonical_recorder_ready_v1_fixture_is_parsed(self):
        """Mirror (and override correlation for) C's canonical marker fixture."""
        import json
        fixture = json.loads((Path(__file__).resolve().parent / 'fixtures'
                              / 'recorder_ready_v1.json').read_text(encoding='utf-8'))
        h = FakeHarness()
        h.send('start')
        identity = {'pid': 424242, 'start_id': 'fixture-opaque-start-id'}
        h.identities['recorder'] = identity
        h.running.add('recorder')
        h.send('process_started', process='recorder', **identity)
        marker = dict(fixture, session_id=h.session.session_id,
                      attempt_id=h.session.attempt_id, recorder_pid=identity['pid'],
                      recorder_start_id=identity['start_id'], recorder_alive=True)
        self.assertEqual(h.send('recorder_ready', **marker), ['start:host'])
        self.assertEqual(h.session.state, 'waiting_game_start')
        self.assertTrue(h.session.recorder_acknowledged)

    def test_dedicated_launch_host_join_and_mission_are_separate_milestones(self):
        h = FakeHarness()
        h.boot_host()
        self.assertEqual(h.send('host_ready'), ['start:client'])
        self.assertEqual(h.session.state, 'waiting_client_start')
        self.assertEqual(h.send('joined'), [])
        h.started('client')
        self.assertEqual(h.session.state, 'awaiting_join')
        h.send('joined')
        self.assertEqual(h.session.state, 'awaiting_mission')
        self.assertEqual(h.session.receipt()['outcome'], 'unknown')
        h.send('mission_entered')
        self.assertEqual(h.session.state, 'playing')
        self.assertEqual(h.send('stop'), ['stop:client', 'stop:host'])
        self.assertEqual(h.exited('client'), [])
        self.assertEqual(h.exited('host'), ['stop:recorder'])
        h.exited('recorder')
        self.assertEqual(h.session.state, 'stopped')
        self.assertFalse(h.running)

    def test_listen_host_ready_does_not_mean_player_joined(self):
        h = FakeHarness('listen')
        h.boot_host()
        self.assertEqual(h.send('host_ready'), [])
        self.assertEqual(h.session.state, 'awaiting_join')
        self.assertEqual(h.session.receipt()['outcome'], 'unknown')
        h.send('joined')
        self.assertEqual(h.session.state, 'awaiting_mission')
        self.assertNotEqual(h.session.state, 'playing')
        h.send('mission_entered')
        self.assertEqual(h.session.state, 'playing')
        self.assertTrue(h.session.receipt()['simulation'])
        self.assertFalse(h.session.receipt()['runtime_verified'])

    def test_mission_entry_requires_join_and_never_skips_milestones(self):
        h = FakeHarness('listen')
        h.boot_host()
        self.assertEqual(h.send('mission_entered'), [])
        self.assertEqual(h.session.state, 'waiting_host')
        h.send('host_ready')
        self.assertEqual(h.send('mission_entered'), [])
        self.assertEqual(h.session.state, 'awaiting_join')
        h.send('joined')
        self.assertEqual(h.session.state, 'awaiting_mission')
        h.send('mission_entered')
        self.assertEqual(h.session.state, 'playing')

    def test_early_host_ready_or_join_cannot_skip_recorder(self):
        h = FakeHarness()
        h.send('start')
        for event in ('host_ready', 'joined', 'mission_entered'):
            self.assertEqual(h.send(event), [])
        self.assertEqual(h.session.state, 'waiting_recorder')
        self.assertEqual(h.actions, ['start:recorder'])

    def test_recorder_start_failure_never_requests_game(self):
        h = FakeHarness()
        h.send('start')
        self.assertEqual(h.send('start_failed', process='recorder'), [])
        self.assertEqual(h.session.state, 'failed')
        self.assertEqual(h.session.error, 'recorder_start_failed')
        self.assertEqual(h.actions, ['start:recorder'])
        self.assertFalse(h.session.active)

    def test_recorder_timeout_and_retry_reject_stale_events(self):
        h = FakeHarness()
        h.send('start')
        h.started('recorder')
        old_attempt = h.session.attempt_id
        self.assertEqual(h.send('tick', now=10), ['stop:recorder'])
        with self.assertRaises(ValueError):
            h.send('start')
        h.exited('recorder')
        self.assertEqual(h.session.state, 'failed')
        h.send('start', now=20)
        h.started('recorder')
        self.assertNotEqual(old_attempt, h.session.attempt_id)
        for event, data in (
            ('recorder_ready', {'schema': 'zombieee.recorder-ready.v1', 'recorder_pid': 100,
                                'recorder_start_id': 'fake-recorder', 'recorder_alive': True}),
            ('exited', {'process': 'recorder', **h.identities['recorder']}),
            ('start_failed', {'process': 'recorder'})):
            self.assertEqual(h.send(event, attempt_id=old_attempt, **data), [])
        self.assertEqual(h.session.state, 'waiting_recorder')
        self.assertEqual(h.recorder_ready(), ['start:host'])

    def test_foreign_session_or_missing_correlation_cannot_ready_recorder(self):
        h = FakeHarness()
        h.send('start')
        h.started('recorder')
        self.assertEqual(h.recorder_ready(session_id='foreign'), [])
        self.assertEqual(h.session.handle('recorder_ready', 100), [])
        self.assertEqual(h.session.state, 'waiting_recorder')
        self.assertEqual(h.recorder_ready(), ['start:host'])

    def test_late_recorder_ready_cannot_bypass_timeout(self):
        h = FakeHarness()
        h.send('start')
        h.started('recorder')
        h.now = 11
        self.assertEqual(h.recorder_ready(), ['stop:recorder'])
        self.assertEqual(h.session.error, 'waiting_recorder_timeout')
        self.assertNotIn('start:host', h.actions)

    def test_recorder_crash_before_handshake_or_immediately_after(self):
        h = FakeHarness()
        h.send('start')
        h.started('recorder')
        h.exited('recorder')
        self.assertEqual(h.session.state, 'failed')
        self.assertEqual(h.recorder_ready(), [])
        self.assertNotIn('start:host', h.actions)
        h = FakeHarness()
        h.boot_host()
        self.assertEqual(h.exited('recorder'), ['stop:host'])
        h.exited('host')
        self.assertEqual(h.session.state, 'failed')

    def test_game_start_failure_preserves_recorder_until_cleanup(self):
        h = FakeHarness()
        h.send('start')
        h.started('recorder')
        h.recorder_ready()
        self.assertEqual(h.send('start_failed', process='host'), ['stop:recorder'])
        h.exited('recorder')
        self.assertEqual(h.session.state, 'failed')

    def test_late_process_start_is_tracked_until_confirmed_exit(self):
        h = FakeHarness()
        h.send('start')
        h.started('recorder')
        h.recorder_ready()
        h.now = 11
        self.assertEqual(h.started('host'), ['stop:host'])
        self.assertEqual(h.exited('host'), ['stop:recorder'])
        h.exited('recorder')
        self.assertEqual(h.session.state, 'failed')

    def test_dead_recorder_prevents_dedicated_client_spawn(self):
        h = FakeHarness()
        h.boot_host()
        self.assertEqual(h.send('host_ready', recorder_alive=False), ['stop:host'])
        self.assertNotIn('start:client', h.actions)
        self.assertEqual(h.session.error, 'recorder_not_live')

    def test_stop_before_recorder_spawn_ack_tracks_late_child(self):
        h = FakeHarness()
        h.send('start')
        self.assertEqual(h.send('stop'), ['stop:recorder'])
        self.assertEqual(h.started('recorder'), ['stop:recorder'])
        self.assertEqual(h.recorder_ready(), [])
        h.exited('recorder')
        self.assertEqual(h.session.state, 'stopped')
        self.assertNotIn('start:host', h.actions)

    def test_client_start_failure_stops_host_then_recorder(self):
        h = FakeHarness()
        h.boot_host()
        h.send('host_ready')
        self.assertEqual(h.send('start_failed', process='client'), ['stop:host'])
        self.assertEqual(h.exited('host'), ['stop:recorder'])
        h.exited('recorder')
        self.assertEqual(h.session.state, 'failed')

    def test_recorder_exit_during_shutdown_is_not_a_clean_stop(self):
        h = FakeHarness()
        h.play()
        self.assertEqual(h.send('stop'), ['stop:client', 'stop:host'])
        self.assertEqual(h.exited('recorder'), [])
        self.assertEqual(h.exited('client'), [])
        self.assertEqual(h.exited('host'), [])
        self.assertEqual(h.session.state, 'failed')
        self.assertEqual(h.session.error, 'recorder_exited_during_shutdown')

    def test_host_or_client_crash_stops_other_games_before_recorder(self):
        for process, other in (('client', 'host'), ('host', 'client')):
            with self.subTest(process=process):
                h = FakeHarness()
                h.play()
                self.assertEqual(h.exited(process), ['stop:' + other])
                self.assertEqual(h.exited(other), ['stop:recorder'])
                h.exited('recorder')
                self.assertEqual(h.session.state, 'failed')

    def test_join_and_mission_timeouts_for_both_routes(self):
        for route in ('dedicated', 'listen'):
            with self.subTest(route=route):
                h = FakeHarness(route)
                h.boot_host()
                h.send('host_ready', now=5)
                if route == 'dedicated':
                    h.started('client')
                self.assertEqual(h.session.state, 'awaiting_join')
                actions = h.send('tick', now=15)
                self.assertIn('stop:client', actions)
                self.assertNotIn('stop:recorder', actions)
                self.assertEqual(h.session.error, 'awaiting_join_timeout')
        for route in ('dedicated', 'listen'):
            with self.subTest(route=route, phase='mission'):
                h = FakeHarness(route)
                h.boot_host()
                h.send('host_ready', now=5)
                if route == 'dedicated':
                    h.started('client')
                h.send('joined', now=5)
                self.assertEqual(h.session.state, 'awaiting_mission')
                actions = h.send('tick', now=15)
                self.assertIn('stop:client', actions)
                self.assertEqual(h.session.error, 'awaiting_mission_timeout')

    def test_wrong_process_identity_and_duplicate_events_are_ignored(self):
        h = FakeHarness()
        h.play()
        self.assertEqual(h.send('exited', process='client', pid=999, start_id='fake-client'), [])
        self.assertEqual(h.session.state, 'playing')
        h.send('stop')
        self.assertEqual(h.send('stop'), [])
        h.exited('client')
        self.assertEqual(h.exited('client'), [])

    def test_endpoint_and_city_scope_are_fixed(self):
        for endpoint in ('0.0.0.0', '192.168.1.2', 'example.com', '::'):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                Session(endpoint=endpoint)
        receipt = Session().receipt()
        self.assertEqual(receipt['city'], 'tbfc_invasion_4')
        self.assertEqual(receipt['mission'], 'multiplayer_iv')
        self.assertEqual(receipt['endpoint'], '127.0.0.1')
        with self.assertRaises(ValueError):
            Session(route='public')

    def test_shared_receipt_keeps_unobserved_runtime_fields_unknown(self):
        receipt = Session().receipt()
        self.assertEqual(receipt['schema'], 'zombieee.session.v1')
        self.assertEqual(receipt['mode'], 'private-local-city')
        self.assertEqual(receipt['outcome'], 'unknown')
        for key in ('build_manifest_sha256', 'wse2_version', 'start_utc', 'end_utc',
                    'host_pid', 'client_pid', 'host_exit_code', 'evidence_bundle'):
            self.assertIsNone(receipt[key])

    def test_time_cannot_move_backwards(self):
        h = FakeHarness()
        h.send('start', now=5)
        with self.assertRaises(ValueError):
            h.send('tick', now=4)
