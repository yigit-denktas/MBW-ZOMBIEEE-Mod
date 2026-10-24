"""Pure lifecycle model for fake-process tests; no OS/process/engine adapter.

All receipts are simulations. Actions describe intent, not executed work.
No launcher flags, listener sockets, firewall rules or game config are emitted.
"""
import math
import uuid

from .rotation import build_rotation, rotation_sha256


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
        self.session_id = uuid.uuid4().hex
        self.attempt_id = None
        self.started = {}
        self.recorder_acknowledged = False
        self.last_time = float('-inf')

    def receipt(self):
        rotation = build_rotation()
        return {'schema': 'zombieee.session.v1', 'session_id': self.session_id,
                'mode': 'private-local-city', 'city': 'tbfc_invasion_4',
                'build_manifest_sha256': None, 'wse2_version': None,
                'start_utc': None, 'end_utc': None, 'host_pid': None, 'client_pid': None,
                'host_exit_code': None, 'outcome': 'unknown', 'evidence_bundle': None,
                'schema_version': 1, 'simulation': True, 'runtime_verified': False,
                'route': self.route, 'endpoint': self.endpoint,
                'mission': 'multiplayer_iv',
                'rotation_sha256': rotation_sha256(rotation),
                'state': self.state, 'error': self.error,
                'attempt': self.attempt, 'attempt_id': self.attempt_id,
                'recorder_acknowledged': self.recorder_acknowledged,
                'processes': sorted(self.active)}

    def rotation_commands(self):
        """Validated dedicated rotation the launcher must emit before start."""
        if self.route != 'dedicated':
            raise ValueError('validated rotation is for the dedicated route')
        return build_rotation()

    def _stop(self):
        self.state = 'stopping'
        self.deadline = None
        self.recorder_acknowledged = False
        # Keep recorder alive until both game processes are confirmed gone.
        games = [p for p in ('client', 'host') if p in self.active]
        return ['stop:' + p for p in games] if games else self._finish_stop()

    def _finish_stop(self):
        if 'recorder' in self.active:
            return ['stop:recorder']
        self.state = 'failed' if self.error else 'stopped'
        return []

    def handle(self, event, now=0, **data):
        """Model correlated adapter observations; never infer engine evidence.

        Async events need session_id/attempt_id. process_started/exited also
        require an owned pid/start_id. recorder_ready requires the canonical
        `zombieee.recorder-ready.v1` marker, matching recorder identity, the
        recorded readiness booleans and an adapter's fresh recorder_alive=True.
        joined and mission_entered are separate fake engine observations; neither
        is inferred from host readiness or process creation.
        A pending spawn failure is start_failed, not a fabricated process exit.
        """
        asynchronous = {'process_started', 'recorder_ready', 'host_ready', 'joined',
                        'mission_entered', 'exited', 'start_failed'}
        if event in asynchronous and (
                self.attempt_id is None or data.get('session_id') != self.session_id
                or data.get('attempt_id') != self.attempt_id):
            return []
        if not math.isfinite(now):
            raise ValueError('now must be finite')
        if now < self.last_time:
            raise ValueError('time must be monotonic')
        self.last_time = now
        if event in ('recorder_ready', 'host_ready', 'joined', 'mission_entered',
                     'tick') and self.deadline is not None and now >= self.deadline:
            self.error = self.state + '_timeout'
            return self._stop()
        if event == 'start':
            if self.state not in ('idle', 'stopped', 'failed') or self.active:
                raise ValueError('previous attempt must fully stop before retry')
            self.error = None
            self.attempt += 1
            self.attempt_id = uuid.uuid4().hex
            self.started = {}
            self.recorder_acknowledged = False
            self.deadline = now + self.timeout
            self.active = {'recorder'}
            self.state = 'waiting_recorder'
            return ['start:recorder']
        if event == 'stop':
            if self.state in ('idle', 'stopped', 'failed', 'stopping'):
                return []
            return self._stop()
        if event in ('process_started', 'exited', 'start_failed'):
            process = data.get('process')
            if process not in ('client', 'host', 'recorder'):
                raise ValueError('unknown process')
            if process not in self.active:
                return []
            identity = (data.get('pid'), data.get('start_id'))
            if event == 'process_started':
                if (type(identity[0]) is not int or identity[0] <= 0
                        or not isinstance(identity[1], str) or not identity[1]):
                    return []
                if process in self.started:
                    return []
                self.started[process] = identity
                if self.deadline is not None and now >= self.deadline:
                    self.error = self.state + '_timeout'
                    return self._stop()
                if self.state == 'stopping':
                    return ['stop:' + process]
                if self.state == 'waiting_game_start' and process in ('host', 'client'):
                    self.state, self.deadline = 'waiting_host', now + self.timeout
                elif self.state == 'waiting_client_start' and process == 'client':
                    self.state, self.deadline = 'awaiting_join', now + self.timeout
                return []
            if event == 'exited' and self.started.get(process) != identity:
                return []
            if event == 'start_failed' and process in self.started:
                return []
            self.active.remove(process)
            self.started.pop(process, None)
            if self.state != 'stopping':
                self.error = process + ('_exited' if event == 'exited' else '_start_failed')
                return self._stop()
            if process == 'recorder' and self.active.intersection({'client', 'host'}):
                # Losing the recorder before the game children are confirmed gone
                # must never collapse into a clean 'stopped' result.
                self.error = 'recorder_' + (
                    'exited' if event == 'exited' else 'start_failed') + '_during_shutdown'
            if not self.active.intersection({'client', 'host'}):
                return self._finish_stop()
            return []
        if event == 'tick':
            return []
        if event == 'recorder_ready':
            if (self.state != 'waiting_recorder' or 'recorder' not in self.active
                    or data.get('schema') != 'zombieee.recorder-ready.v1'
                    or data.get('recorder_alive') is not True
                    or data.get('log_offsets_captured') is not True
                    or data.get('watcher_active') is not True
                    or data.get('engine_ready') is not False
                    or data.get('mission_ready') is not False
                    or not isinstance(data.get('watcher_id'), str)
                    or not data.get('watcher_id')
                    or self.started.get('recorder') != (
                        data.get('recorder_pid'), data.get('recorder_start_id'))):
                return []
            self.recorder_acknowledged = True
            process = 'host' if self.route == 'dedicated' else 'client'
            self.active.add(process)
            self.state, self.deadline = 'waiting_game_start', now + self.timeout
            return ['start:' + process]
        if event == 'host_ready' and self.state == 'waiting_host':
            if not self.recorder_acknowledged or data.get('recorder_alive') is not True:
                self.error = 'recorder_not_live'
                return self._stop()
            if self.route == 'listen':
                self.state, self.deadline = 'awaiting_join', now + self.timeout
                return []
            self.active.add('client')
            self.state, self.deadline = 'waiting_client_start', now + self.timeout
            return ['start:client']
        if event == 'joined' and self.state == 'awaiting_join':
            self.state, self.deadline = 'awaiting_mission', now + self.timeout
            return []
        if event == 'mission_entered' and self.state == 'awaiting_mission':
            self.state, self.deadline = 'playing', None
            return []
        if event in asynchronous:
            return []
        raise ValueError('event invalid in state ' + self.state)
