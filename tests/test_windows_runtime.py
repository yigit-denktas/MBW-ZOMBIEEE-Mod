"""Bounded portable probe tests: loopback observation, tails, deterministic waits."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.runtime import (  # noqa: E402
    ENDPOINT, MAX_TAIL_BYTES, ProbeError, Waiter, contains_marker,
    host_bound_loopback, is_loopback_endpoint, loopback_addresses, read_text_tail)


def netstat(*rows):
    return SimpleNamespace(stdout='\n'.join(rows) + '\n', returncode=0)


class EndpointTests(unittest.TestCase):
    def test_only_literal_ipv4_loopback_is_accepted(self):
        self.assertTrue(is_loopback_endpoint('127.0.0.1:7240'))
        for value in ('0.0.0.0:7240', '[::1]:7240', '::1:7240', 'localhost:7240',
                      '127.0.0.1', '127.0.0.1:0', '127.0.0.1:70000', '192.168.1.2:7240',
                      '', None, 7240):
            with self.subTest(value=value):
                self.assertFalse(is_loopback_endpoint(value))
        self.assertEqual(ENDPOINT, '127.0.0.1:7240')


class LoopbackObservationTests(unittest.TestCase):
    def test_exact_address_and_owned_pid_are_required(self):
        rows = ['  UDP    127.0.0.1:7240      *:*                                    501',
                '  TCP    127.0.0.1:7241      0.0.0.0:0    LISTENING               502']
        runner = lambda argv, **kwargs: netstat(*rows)  # noqa: E731
        self.assertTrue(host_bound_loopback(501, runner=runner))
        self.assertFalse(host_bound_loopback(502, runner=runner))
        self.assertFalse(host_bound_loopback(501, runner=lambda a, **k: netstat(
            '  UDP    0.0.0.0:7240        *:*                                    501')))
        self.assertFalse(host_bound_loopback(501, runner=lambda a, **k: netstat(
            '  UDP    127.0.0.1:7241      *:*                                    501')))
        self.assertEqual([address for address, _pid in loopback_addresses(runner=runner)],
                         ['127.0.0.1:7240', '127.0.0.1:7241'])

    def test_missing_netstat_is_unknown_not_ready(self):
        def broken(argv, **kwargs):
            raise FileNotFoundError('netstat unavailable')
        self.assertEqual(loopback_addresses(runner=broken), [])
        self.assertFalse(host_bound_loopback(501, runner=broken))
        self.assertFalse(host_bound_loopback(0, runner=broken))
        self.assertFalse(host_bound_loopback('501', runner=broken))


class BoundedTailTests(unittest.TestCase):
    def test_tail_is_bounded_and_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'host_stdout.log'
            path.write_text('a' * (MAX_TAIL_BYTES + 100) + 'ZDB1|player_joined\n',
                            encoding='utf-8')
            text = read_text_tail(path, limit=4096)
            self.assertLessEqual(len(text), 4096)
            self.assertIn('ZDB1|player_joined', text)
            self.assertTrue(contains_marker(path, ('ZDB1|player_joined',), limit=4096))
            self.assertFalse(contains_marker(path, ('ZDB1|mission_enter',), limit=4096))
            self.assertEqual(read_text_tail(Path(tmp) / 'missing.log'), '')


class WaiterTests(unittest.TestCase):
    def test_deadline_and_immediate_success_with_injected_clock(self):
        state = {'now': 0.0, 'sleeps': []}

        def sleep(seconds):
            state['sleeps'].append(seconds)
            state['now'] += seconds

        waiter = Waiter(clock=lambda: state['now'], sleep=sleep, interval=1.0)
        self.assertTrue(waiter.until(lambda: True, 5.0))
        self.assertEqual(state['sleeps'], [])
        self.assertFalse(waiter.until(lambda: False, 3.0))
        self.assertAlmostEqual(state['now'], 3.0)
        self.assertTrue(waiter.until(lambda: state['now'] >= 5.0, 30.0))
        self.assertAlmostEqual(state['now'], 5.0)

    def test_invalid_wait_configuration_is_rejected(self):
        with self.assertRaises(ProbeError):
            Waiter(interval=0)
        waiter = Waiter(clock=lambda: 0.0, sleep=lambda seconds: None)
        with self.assertRaises(ProbeError):
            waiter.until(lambda: False, -1)
        with self.assertRaises(ProbeError):
            waiter.until(lambda: False, float('nan'))
        with self.assertRaises(ProbeError):
            waiter.until('not callable', 1)
        with self.assertRaises(ProbeError):
            waiter.pause(-1)


if __name__ == '__main__':
    unittest.main()
