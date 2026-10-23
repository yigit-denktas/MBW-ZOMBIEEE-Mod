"""Pure lifecycle model for fake-process tests; no OS/process/engine adapter.

All receipts are simulations. Actions describe intent, not executed work.
No launcher flags, listener sockets, firewall rules or game config are emitted.
"""
import math


class Session:
    def __init__(self, route='dedicated', endpoint='127.0.0.1', timeout=30):
        if route not in ('dedicated', 'listen'):
            raise ValueError('unverified route; use a dedicated or listen simulation')
        if endpoint != '127.0.0.1':
            raise ValueError('only explicit IPv4 loopback is modeled')
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('timeout must be finite and positive')
        self.route, self.endpoint, self.timeout = route, endpoint, timeout
        self.state, self.error = 'idle', None
        self.active = set()
        self.deadline = None
        self.attempt = 0
        self.last_time = float('-inf')

    def receipt(self):
        return {'schema': 'zombieee.session.v1', 'session_id': 'simulation-' + str(self.attempt),
                'mode': 'private-local-city', 'city': 'tbfc_invasion_4',
                'build_manifest_sha256': None, 'wse2_version': None,
                'start_utc': None, 'end_utc': None, 'host_pid': None, 'client_pid': None,
                'host_exit_code': None, 'outcome': 'unknown', 'evidence_bundle': None,
                'schema_version': 1, 'simulation': True, 'runtime_verified': False,
                'route': self.route, 'endpoint': self.endpoint,
                'mission': 'multiplayer_iv',
                'state': self.state, 'error': self.error,
                'attempt': self.attempt, 'processes': sorted(self.active)}

    def _stop(self):
        self.state = 'stopping'
        self.deadline = None
        # Keep recorder alive until both game processes are confirmed gone.
        games = [p for p in ('client', 'host') if p in self.active]
        return ['stop:' + p for p in games] if games else self._finish_stop()

    def _finish_stop(self):
        if 'recorder' in self.active:
            return ['stop:recorder']
        self.state = 'failed' if self.error else 'stopped'
        return []

    def handle(self, event, now=0, **data):
        """Feed monotonic time; `exited` acknowledges a stopped/crashed fake process.

        A failed spawn must be reported as `exited` for that requested process.
        `ready` and `joined` are fake evidence, never inferred from process creation.
        """
        if not math.isfinite(now):
            raise ValueError('now must be finite')
        if now < self.last_time:
            raise ValueError('time must be monotonic')
        self.last_time = now
        if event in ('ready', 'joined', 'tick') and self.deadline is not None and now >= self.deadline:
            self.error = self.state + '_timeout'
            return self._stop()
        if event == 'start':
            if self.state not in ('idle', 'stopped', 'failed') or self.active:
                raise ValueError('previous attempt must fully stop before retry')
            self.error = None
            self.attempt += 1
            self.deadline = now + self.timeout
            process = 'host' if self.route == 'dedicated' else 'client'
            self.active = {'recorder', process}
            self.state = 'waiting_host'
            return ['start:recorder', 'start:' + process]
        if event == 'stop':
            if self.state in ('idle', 'stopped', 'failed', 'stopping'):
                return []
            return self._stop()
        if event == 'exited':
            process = data.get('process')
            if process not in ('client', 'host', 'recorder'):
                raise ValueError('unknown process')
            if process not in self.active:
                return []
            self.active.remove(process)
            if self.state != 'stopping':
                self.error = process + '_exited'
                return self._stop()
            if not self.active.intersection({'client', 'host'}):
                return self._finish_stop()
            return []
        if event == 'tick':
            return []
        if event == 'ready' and self.state == 'waiting_host':
            if self.route == 'listen':
                self.state, self.deadline = 'playing', None
                return []
            self.active.add('client')
            self.state, self.deadline = 'joining', now + self.timeout
            return ['start:client']
        if event == 'joined' and self.state == 'joining':
            self.state, self.deadline = 'playing', None
            return []
        raise ValueError('event invalid in state ' + self.state)
