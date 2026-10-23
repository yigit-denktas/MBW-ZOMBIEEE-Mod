import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from launcher.solo import Session


class FakeHarness:
    """No OS processes: actions maintain a fake process inventory."""
    def __init__(self, route='dedicated'):
        self.session = Session(route=route, timeout=10)
        self.running = set()
        self.events = []
        self.now = 0

    def send(self, event, now=None, **data):
        now = self.now if now is None else now
        actions = self.session.handle(event, now, **data)
        self.now = now
        self.events.extend(actions)
        for action in actions:
            verb, name = action.split(':')
            if verb == 'start':
                self.running.add(name)
            elif verb == 'stop':
                # Exit must be acknowledged separately, as with real processes.
                pass
        if event == 'exited':
            self.running.discard(data['process'])
        return actions


class SoloTests(unittest.TestCase):
    def test_dedicated_readiness_precedes_client_and_shutdown_is_ordered(self):
        h = FakeHarness()
        self.assertEqual(h.send('start'), ['start:recorder', 'start:host'])
        self.assertEqual(h.session.state, 'waiting_host')
        self.assertNotIn('client', h.running)
        self.assertEqual(h.send('ready'), ['start:client'])
        h.send('joined')
        self.assertEqual(h.session.state, 'playing')
        self.assertEqual(h.send('stop'), ['stop:client', 'stop:host'])
        self.assertEqual(h.send('exited', process='client'), [])
        self.assertEqual(h.send('exited', process='host'), ['stop:recorder'])
        h.send('exited', process='recorder')
        self.assertEqual(h.session.state, 'stopped')
        self.assertFalse(h.running)

    def test_listen_route_remains_distinct_simulation(self):
        h = FakeHarness('listen')
        self.assertEqual(h.send('start'), ['start:recorder', 'start:client'])
        h.send('ready')
        self.assertEqual(h.session.state, 'playing')
        self.assertTrue(h.session.receipt()['simulation'])
        self.assertFalse(h.session.receipt()['runtime_verified'])

    def test_timeout_cleanup_and_retry_waits_for_all_exits(self):
        h = FakeHarness()
        h.send('start')
        self.assertEqual(h.send('tick', now=10), ['stop:host'])
        self.assertEqual(h.session.state, 'stopping')
        with self.assertRaises(ValueError):
            h.send('start')
        h.send('exited', process='host')
        h.send('exited', process='recorder')
        self.assertEqual(h.session.state, 'failed')
        h.send('start', now=20)
        self.assertEqual(h.session.state, 'waiting_host')

    def test_client_crash_stops_host_before_recorder(self):
        h = FakeHarness()
        h.send('start')
        h.send('ready')
        h.send('joined')
        self.assertEqual(h.send('exited', process='client'), ['stop:host'])
        self.assertEqual(h.send('exited', process='host'), ['stop:recorder'])
        h.send('exited', process='recorder')
        self.assertEqual(h.session.state, 'failed')

    def test_join_timeout_and_recorder_crash(self):
        for process in ('host', 'recorder'):
            with self.subTest(process=process):
                h = FakeHarness()
                h.send('start')
                actions = h.send('exited', process=process)
                self.assertTrue(actions)
                self.assertEqual(h.session.state, 'stopping')
        h = FakeHarness()
        h.send('start')
        h.send('ready', now=5)
        self.assertEqual(h.send('tick', now=15), ['stop:client', 'stop:host'])

    def test_endpoint_and_city_scope_are_fixed(self):
        for endpoint in ('0.0.0.0', '192.168.1.2', 'example.com', '::'):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                Session(endpoint=endpoint)
        receipt = Session().receipt()
        self.assertEqual(receipt['map'], 'tbfc_invasion_4')
        self.assertEqual(receipt['mission'], 'multiplayer_iv')
        self.assertEqual(receipt['endpoint'], '127.0.0.1')
        with self.assertRaises(ValueError):
            Session(route='public')

    def test_stop_is_idempotent_and_early_join_rejected(self):
        h = FakeHarness()
        h.send('start')
        with self.assertRaises(ValueError):
            h.send('joined')
        h.send('stop')
        self.assertEqual(h.send('stop'), [])

    def test_late_ready_cannot_bypass_timeout(self):
        h = FakeHarness()
        h.send('start')
        self.assertEqual(h.send('ready', now=11), ['stop:host'])
        self.assertNotIn('client', h.running)
        self.assertEqual(h.session.error, 'waiting_host_timeout')

    def test_time_cannot_move_backwards(self):
        h = FakeHarness()
        h.send('start', now=5)
        with self.assertRaises(ValueError):
            h.send('ready', now=4)
