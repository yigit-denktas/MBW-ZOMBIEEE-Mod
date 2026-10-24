"""One-command private City flow for Windows: discover, install, record, play.

The owner's target is a single action:

    python -m launcher.play_city

which performs, in order and fail-closed:

1. read-only discovery of an owned Warband install and its WSE2 client +
   dedicated programs (``launcher.discovery`` / ``launcher.engines``);
2. when the City module is missing or stale, a pinned Beta 0.4 archive audit
   through Agent A's read-only tool (SHA-256 + 7-Zip member CRC) and a
   ``tools/build.py`` City build through Agent A's builder, activated with a
   retained backup and digest verification (``launcher.install``);
3. emission of the validated dedicated rotation (``launcher.rotation``) into a
   fresh private launch directory;
4. arming Agent C's passive recorder, starting the dedicated host as an owned
   child whose stdout is teed, and auto-joining the owner's client to
   ``127.0.0.1:7240``;
5. waiting for the owner to leave the game, then stopping the owned children,
   sealing the host stdout artifact into C's signed flight bundle, verifying the
   manifest and rendering C's receipt summary.

Boundaries: only literal IPv4 loopback is used; no firewall rule, public bind,
server-browser publication, serial key, remote host or automatic upload is
created. Nothing is claimed as verified gameplay: receipts keep
``runtime_verified=false`` and ``outcome=unknown``; observations are recorded
with their evidence gaps. Offline tests inject every process/recorder/waiter.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .discovery import discover, known_locations
from .engines import plan_engines
from .install import (MODULE_NAME, CITY_BUILD_FLAGS, execute_install,
                      plan_install, restore_backup, verify_built_module)
from .recorder import PassiveRecorder, atomic_write_json, is_redirected
from .rotation import (DEFAULT_TEAM1_BOTS, DEFENDER_SQUAD_BOTS, build_rotation,
                      rotation_sha256, validate_rotation)
from .runtime import (ENDPOINT, JOIN_MARKERS, MISSION_MARKERS, Waiter,
                      contains_marker, host_bound_loopback, is_loopback_endpoint)
from .solo import Session

SCHEMA = 'zombieee.city-launch-receipt.v1'
PLAN_SCHEMA = 'zombieee.city-launch-plan.v1'
DEFAULT_EVIDENCE_DIR = Path(__file__).resolve().parents[1] / 'local' / 'session' / 'play-city'
MAX_ARCHIVE_CANDIDATES = 16
MAX_ARCHIVE_SCAN = 4096
MAX_RECEIPT_BYTES = 1024 * 1024
MAX_SUMMARY_OUTPUT = 1024 * 1024
SERVER_CONFIG_TEMPLATE = """\
# Generated per launch by launcher.play_city. Private loopback only.
[Log]
bAutoFlushLog=true
bBackupOnExit=true
sLogPath={log_name}
sStoredLogDirectory=Logs
[Network]
bLoopbackServer=true
bHTTPServerQueries=false
bOGPServer=false
bRCONServer=false
bAutoSelectClientPort=true
iServerPort={port}
iOGPServerPort=0
iRCONServerPort=0
sServerAddress={host}
sClientAddress=
"""
SESSION_TIMEOUT_FLOOR = 120
DEFAULT_SETTINGS = {
    'host_ready_timeout': 45.0,
    'join_timeout': 120.0,
    'mission_timeout': 60.0,
    'shutdown_timeout': 20.0,
    'recorder_stop_timeout': 90.0,
    'poll_interval': 2.0,
    'terminate_timeout': 15.0,
    'max_seconds': 0.0,
    'session_timeout': 900.0,
}


class LaunchError(RuntimeError):
    """The one-click flow was invoked outside a safe, validated state."""


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _read_bounded_json(path, limit=MAX_RECEIPT_BYTES):
    path = Path(path)
    with open(path, 'rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise LaunchError('oversized_json: ' + path.name)
    value = json.loads(data.decode('utf-8'))
    if not isinstance(value, dict):
        raise LaunchError('json_not_object: ' + path.name)
    return value


def _redirected_components(paths):
    """True for any existing symlink/reparse component from each path root."""
    components = []
    seen = set()
    for value in paths:
        current = Path(value).expanduser().absolute()
        for component in (*reversed(current.parents), current):
            key = os.path.normcase(str(component))
            if key in seen:
                continue
            seen.add(key)
            if is_redirected(component):
                components.append(str(component))
    return components


# -- archive discovery and audit ---------------------------------------------

def archive_candidates(explicit=None, *, environ=None, extra_dirs=()):
    """Return bounded candidate RAR paths; explicit input is never a default."""
    if explicit:
        return [str(Path(item).expanduser()) for item in explicit][:MAX_ARCHIVE_CANDIDATES]
    env = os.environ if environ is None else environ
    dirs = []
    for key in ('USERPROFILE', 'HOME'):
        if env.get(key):
            dirs.append(Path(env[key]) / 'Downloads')
    for item in extra_dirs:
        dirs.append(Path(item).expanduser())
    found, seen, examined = [], set(), 0
    for directory in dirs:
        try:
            entries = sorted(directory.iterdir(), key=lambda item: item.name.casefold())
        except (FileNotFoundError, NotADirectoryError, PermissionError, OSError):
            continue
        for entry in entries:
            examined += 1
            if examined > MAX_ARCHIVE_SCAN:
                return found
            name = entry.name.casefold()
            if not name.endswith('.rar') or 'zombieee' not in name:
                continue
            try:
                if not entry.is_file():
                    continue
            except OSError:
                continue
            key = os.path.normcase(str(entry.absolute()))
            if key not in seen:
                seen.add(key)
                found.append(str(entry.absolute()))
            if len(found) >= MAX_ARCHIVE_CANDIDATES:
                return found
    return found


def run_archive_audit(archive, *, repo_root=None, python_executable=None,
                      timeout=1800, runner=None):
    """Consume Agent A's read-only audit CLI; never duplicate its hash policy."""
    repo_root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    argv = [python_executable or sys.executable,
            str(repo_root / 'tools' / 'archive_audit.py'),
            '--archive', str(Path(archive).expanduser().absolute()),
            '--verify-crc', '--json']
    if runner is None:
        def runner(command, **kwargs):
            return subprocess.run(command, capture_output=True, text=True,
                                  timeout=kwargs.get('timeout', timeout), shell=False)
    try:
        completed = runner(argv, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return {'status': 'audit_failed', 'identity_ok': False,
                'crc_status': 'not_checked', 'seven_zip_available': False,
                'actual_sha256': None, 'expected_sha256': None,
                'problems': ['audit_runner_' + type(exc).__name__]}
    stdout = completed.stdout if isinstance(completed.stdout, str) else ''
    try:
        report = json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {'status': 'invalid_report', 'identity_ok': False,
                'crc_status': 'not_checked', 'seven_zip_available': False,
                'actual_sha256': None, 'expected_sha256': None,
                'problems': ['archive_audit_invalid_json']}
    if not isinstance(report, dict) or type(report.get('identity_ok')) is not bool:
        return {'status': 'invalid_report', 'identity_ok': False,
                'crc_status': 'not_checked', 'seven_zip_available': False,
                'actual_sha256': None, 'expected_sha256': None,
                'problems': ['archive_audit_invalid_shape']}
    report['status'] = ('identity_verified' if report['identity_ok']
                        else 'identity_rejected')
    return report


# -- launch plan --------------------------------------------------------------

def installed_module_status(game_root, *, expected_source_sha256=None):
    """Structural status of the installed City module (no writes, no launch)."""
    module_dir = Path(game_root).expanduser().absolute() / 'Modules' / MODULE_NAME
    if not module_dir.is_dir():
        return {'present': False, 'ok': False, 'problems': ['module_missing']}
    status = verify_built_module(module_dir,
                                 expected_source_sha256=expected_source_sha256)
    status['present'] = True
    return status


def _normalize_archive(archive):
    """One explicit archive or a selection blocker; never a silent guess."""
    if archive is None:
        return None, None
    values = [archive] if isinstance(archive, (str, Path)) else list(archive)
    values = [str(Path(item).expanduser()) for item in values if item]
    if len(values) == 1:
        return values[0], None
    if not values:
        return None, None
    return None, 'archive_selection_required'


def build_launch_plan(*, discovery_report, evidence_root, archive=None,
                      archive_identity=None, audit_runner=None,
                      game_root=None, client_exe=None, dedicated_exe=None,
                      rebuild=False, allow_install=True, repo_root=None,
                      process_checker=None, installed_status=None,
                      archive_resolver=None, settings=None,
                      team0_bots=None, stock_rotation=False):
    """Compose the full read-only launch plan; no writes or process starts."""
    repo_root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    evidence_root = Path(evidence_root).expanduser().absolute()
    settings = dict(DEFAULT_SETTINGS, **(settings or {}))
    blockers, warnings = [], []
    engines = plan_engines(discovery_report, game_root=game_root,
                           client_exe=client_exe, dedicated_exe=dedicated_exe)
    blockers.extend(engines['blockers'])
    install_plan = None
    install_needed = False
    installed = None
    if engines['warband_root'] is not None:
        installed = (installed_status if installed_status is not None
                     else installed_module_status(engines['warband_root']))
        install_needed = rebuild or not installed.get('ok', False)
        if install_needed and not allow_install:
            blockers.append('install_required_but_disabled')
        if install_needed and allow_install:
            chosen_archive, archive_blocker = _normalize_archive(archive)
            if archive_blocker:
                blockers.append(archive_blocker)
            identity = archive_identity
            if chosen_archive is None and archive_blocker is None:
                resolver = archive_resolver or archive_candidates
                candidates = list(resolver() or [])[:MAX_ARCHIVE_CANDIDATES]
                if len(candidates) == 1:
                    chosen_archive = candidates[0]
                elif not candidates:
                    blockers.append('archive_not_found')
                else:
                    blockers.append('archive_selection_required')
            if chosen_archive is not None:
                chosen_archive = str(Path(chosen_archive).expanduser().absolute())
                if identity is None:
                    runner = audit_runner or run_archive_audit
                    try:
                        identity = runner(chosen_archive, repo_root=repo_root)
                    except TypeError:
                        identity = runner(chosen_archive)
                install_plan = plan_install(
                    game_root=engines['warband_root'],
                    transaction_id=('play-' + time.strftime('%Y%m%d-%H%M%S')
                                    + '-' + secrets.token_hex(3)),
                    archive=chosen_archive, archive_identity=identity,
                    evidence_dir=evidence_root, repo_root=repo_root,
                    running_processes=(process_checker() if process_checker else None),
                    build_timeout=1800)
                blockers.extend('install:' + item for item in install_plan['blockers'])
        elif not install_needed:
            warnings.append('installed_city_module_reused')
    evidence_issues = []
    if evidence_root.exists() and not evidence_root.is_dir():
        evidence_issues.append('evidence_root_not_directory')
    if _redirected_components([evidence_root]):
        evidence_issues.append('evidence_root_redirected')
    blockers.extend(evidence_issues)

    if type(stock_rotation) is not bool:
        raise LaunchError('stock_rotation must be a boolean')
    if stock_rotation and team0_bots is not None and team0_bots != 0:
        raise LaunchError('stock_rotation conflicts with explicit team0_bots')
    if team0_bots is None:
        # One-click City always builds/uses A's City defender profile, so the
        # native team-0 ally squad must be requested explicitly: rotation team 1
        # (1-based) == telemetry team 0, `set_bot_count 1 4`.
        team0_bots = 0 if stock_rotation else DEFENDER_SQUAD_BOTS
    if (type(team0_bots) is not int or isinstance(team0_bots, bool)
            or not 0 <= team0_bots <= 200):
        raise LaunchError('team0_bots must be an integer in [0, 200]')
    try:
        rotation = build_rotation(team1_bots=team0_bots)
    except ValueError as exc:
        raise LaunchError('rotation refused: ' + str(exc)) from exc
    rotation_profile = ('stock' if team0_bots == DEFAULT_TEAM1_BOTS
                        else 'defender-squad'
                        if team0_bots == DEFENDER_SQUAD_BOTS
                        else 'custom-team0')
    if not validate_rotation(rotation):
        raise LaunchError('rotation contract self-check failed')
    if not is_loopback_endpoint(ENDPOINT):
        raise LaunchError('non-loopback endpoint refused')
    plan = {
        'schema': PLAN_SCHEMA,
        'schema_version': 1,
        'dry_run': True,
        'execution_enabled': not blockers,
        'ok': not blockers,
        'blockers': list(dict.fromkeys(blockers)),
        'warnings': warnings,
        'route': 'dedicated',
        'endpoint': ENDPOINT,
        'loopback_only': True,
        'city': 'tbfc_invasion_4',
        'mission': 'multiplayer_iv',
        'module_name': MODULE_NAME,
        'engine': {
            'warband_root': engines['warband_root'],
            'client_executable': (engines['client'] or {}).get('executable'),
            'dedicated_executable': (engines['dedicated'] or {}).get('executable'),
            'client_provenance': (engines['client'] or {}).get('provenance'),
            'dedicated_provenance': (engines['dedicated'] or {}).get('provenance'),
            'runtime_verified': False,
        },
        'discovery': {
            'warband_candidates': len(discovery_report.get('candidates') or []),
            'wse2_candidates': len(discovery_report.get('wse2_candidates') or []),
            'ambiguity': bool(discovery_report.get('ambiguity')),
            'warning_count': len(discovery_report.get('warnings') or []),
            'blockers': list(discovery_report.get('blockers') or [])[:16],
        },
        'evidence_root': str(evidence_root),
        'install': {
            'needed': bool(install_needed),
            'installed_ok': bool(installed and installed.get('ok')),
            'installed': installed,
            'plan': install_plan,
            'receipt': None,
        },
        'rotation': rotation,
        'team0_bots': team0_bots,
        'rotation_profile': rotation_profile,
        'rotation_sha256': rotation_sha256(rotation),
        'client_join_address': ENDPOINT,
        'client_argv_suffix': ['--module', MODULE_NAME, '--address', ENDPOINT,
                               '--no-intro'],
        'host_argv_suffix': ['--config-path', '<server-config.ini>',
                             '-r', '<rotation.txt>', '--module', MODULE_NAME],
        'server_config_loopback': True,
        'custom_city_flags': list(CITY_BUILD_FLAGS),
        'settings': settings,
        'runtime_verified': False,
        'notes': [
            'host readiness is a read-only loopback UDP 7240 observation',
            'join/mission markers are C probe observations, not acceptance',
            'stopping after client exit is the normal end of a Play City session',
        ],
    }
    return plan


# -- argv and private session files ------------------------------------------

def server_config_text(*, host_log_name, port=7240):
    """Generate the private WSE2 dedicated config; loopback + port are forced."""
    if not isinstance(host_log_name, str) or not host_log_name:
        raise ValueError('host_log_name must be a non-empty string')
    if '/' in host_log_name or '\\' in host_log_name or host_log_name in ('.', '..'):
        raise ValueError('host_log_name must be a plain file name')
    if type(port) is not int or port != 7240:
        raise ValueError('only the validated loopback port 7240 is supported')
    return SERVER_CONFIG_TEMPLATE.format(log_name=host_log_name,
                                         port=port, host='127.0.0.1')


def session_commands(*, dedicated_executable, client_executable, config_path,
                     rotation_path):
    """Exact owned argv for the dedicated host and the auto-joined client."""
    if not is_loopback_endpoint(ENDPOINT):
        raise LaunchError('non-loopback endpoint refused')
    host = [str(dedicated_executable), '--config-path', str(config_path),
            '-r', str(rotation_path), '--module', MODULE_NAME]
    client = [str(client_executable), '--module', MODULE_NAME,
              '--address', ENDPOINT, '--no-intro']
    return host, client


class LaunchPaths:
    """Fresh private paths for one launch attempt (created by ``prepare``)."""

    def __init__(self, *, evidence_root, game_root, session_id):
        if not isinstance(session_id, str) or not session_id or len(session_id) > 64:
            raise ValueError('invalid session id')
        if any(character not in '0123456789abcdef' for character in session_id):
            raise ValueError('session id must be lowercase hex')
        self.evidence_root = Path(evidence_root).expanduser().absolute()
        self.game_root = Path(game_root).expanduser().absolute()
        self.session_id = session_id
        self.launch_root = self.evidence_root / 'launches'
        self.launch_dir = self.launch_root / session_id
        self.flight_root = self.evidence_root / 'flights'
        self.config_path = self.launch_dir / 'server-config.ini'
        self.rotation_path = self.launch_dir / 'rotation.txt'
        self.host_stdout = self.launch_dir / 'host_stdout.log'
        self.client_stdout = self.launch_dir / 'client_stdout.log'
        self.host_log = self.game_root / ('zombieee_play_' + session_id + '.log')
        self.launch_receipt = self.launch_dir / 'launch-receipt.json'
        self.summary_path = self.launch_dir / 'summary.json'

    def prepare(self, *, rotation_lines):
        try:
            valid = validate_rotation(rotation_lines)
        except (TypeError, ValueError) as exc:
            raise LaunchError('rotation failed validation before write: '
                              + str(exc)) from exc
        if not valid:
            raise LaunchError('rotation failed validation before write')
        for directory in (self.launch_root, self.flight_root):
            directory.mkdir(parents=True, exist_ok=True)
        if self.launch_dir.exists() or is_redirected(self.launch_dir):
            raise LaunchError('stale launch directory; retry with a fresh session')
        self.launch_dir.mkdir(parents=True, exist_ok=False)
        payload = ('\n'.join(rotation_lines) + '\n').encode('utf-8')
        self.rotation_path.write_bytes(payload)
        self.config_path.write_text(
            server_config_text(host_log_name=self.host_log.name), encoding='utf-8')
        return self


# -- orchestrator -------------------------------------------------------------

class CityLauncher:
    """Drive one Play City attempt over injectable processes and recorder.

    Every side effect is an injected collaborator (recorder factory, host/client
    session factories, waiter, summary runner), so offline tests can assert the
    exact ordering and that no game is launched.
    """

    def __init__(self, plan, *, session, recorder_factory, host_session_factory,
                 client_session_factory, waiter=None, summary_runner=None,
                 netstat_runner=None, logger=None, now_utc=None,
                 repo_root=None):
        if not isinstance(plan, dict) or plan.get('schema') != PLAN_SCHEMA:
            raise LaunchError('not a launch plan')
        if plan.get('ok') is not True:
            raise LaunchError('plan is blocked: ' + ', '.join(plan.get('blockers') or []))
        if session is None:
            raise LaunchError('a lifecycle Session is required')
        self.plan = plan
        self.settings = dict(DEFAULT_SETTINGS, **(plan.get('settings') or {}))
        self.session = session
        self.recorder_factory = recorder_factory
        self.host_session_factory = host_session_factory
        self.client_session_factory = client_session_factory
        self.waiter = waiter or Waiter(interval=self.settings['poll_interval'])
        self.summary_runner = summary_runner or self._default_summary_runner
        self.netstat_runner = netstat_runner
        self.logger = logger or (lambda message: None)
        self.now_utc = now_utc or utc_now
        self.repo_root = (Path(repo_root) if repo_root is not None
                          else Path(__file__).resolve().parents[1])
        self.paths = LaunchPaths(evidence_root=plan['evidence_root'],
                                 game_root=plan['engine']['warband_root'],
                                 session_id=session.session_id)
        self.recorder = None
        self.host = None
        self.client = None
        self.host_argv = None
        self.client_argv = None
        self.host_stdout = None
        self.client_stdout = None
        self.host_log = self.paths.host_log
        self.identities = {}
        self.host_bound_seen = False
        self.join_observed = False
        self.mission_observed = False
        self.receipt = self._base_receipt()

    # -- receipt helpers ---------------------------------------------------

    def _base_receipt(self):
        plan = self.plan
        install = plan.get('install') or {}
        installed = install.get('installed') or {}
        return {
            'schema': SCHEMA,
            'schema_version': 1,
            'session_id': self.session.session_id,
            'attempt_id': None,
            'mode': 'private-local-city',
            'city': plan.get('city'),
            'mission': plan.get('mission'),
            'route': 'dedicated',
            'endpoint': plan.get('endpoint'),
            'loopback_only': True,
            'build_manifest_sha256': installed.get('module_sha256'),
            'module': {'sha256': installed.get('module_sha256'),
                       'file_count': installed.get('file_count'),
                       'trigger_count': installed.get('trigger_count'),
                       'map_scope': installed.get('map_scope')},
            'install': {
                'performed': bool(install.get('receipt')),
                'status': (install.get('receipt') or {}).get('status'),
                'backup_retained': bool((install.get('receipt') or {}).get('backup')),
                'transaction_id': (install.get('receipt') or {}).get('transaction_id'),
            },
            'wse2_version': None,
            'start_utc': None,
            'end_utc': None,
            'host_pid': None,
            'client_pid': None,
            'host_exit_code': None,
            'client_exit_code': None,
            'outcome': 'unknown',
            'lifecycle_outcome': None,
            'status': 'planned',
            'error': None,
            'evidence_bundle': None,
            'evidence': None,
            'artifacts': [],
            'rotation_sha256': plan.get('rotation_sha256'),
            'team0_bots': plan.get('team0_bots'),
            'rotation_profile': plan.get('rotation_profile'),
            'host_bound_loopback': None,
            'join_observed': None,
            'mission_observed': None,
            'summary': {'status': 'not_collected'},
            'simulation': False,
            'runtime_verified': False,
            'notes': list(plan.get('notes') or []),
        }

    def _set(self, **fields):
        self.receipt.update(fields)
        return self.receipt

    def _session_event(self, event, process=None, pid=None, start_id=None,
                       **extra):
        data = {'session_id': self.session.session_id,
                'attempt_id': self.session.attempt_id}
        if process is not None:
            data['process'] = process
        if pid is not None:
            data['pid'] = pid
        if start_id is not None:
            data['start_id'] = start_id
        data.update(extra)
        try:
            return self.session.handle(event, self.waiter.clock(), **data)
        except (ValueError, KeyError) as exc:
            self.logger('lifecycle event ' + event + ' rejected: ' + str(exc))
            return []

    def _session_exit(self, process):
        pid, start_id = self.identities.get(process, (None, None))
        return self._session_event('exited', process=process, pid=pid,
                                   start_id=start_id)

    def _record_identity(self, process, pid, start_id):
        self.identities[process] = (pid, start_id)
        return self._session_event('process_started', process=process,
                                   pid=pid, start_id=start_id)

    # -- launch steps ------------------------------------------------------

    def _prepare_files(self):
        engine = self.plan['engine']
        for role, executable in (('client', engine['client_executable']),
                                 ('dedicated', engine['dedicated_executable'])):
            if not isinstance(executable, str) or not Path(executable).is_file():
                raise LaunchError('WSE2 ' + role + ' executable disappeared')
        self.paths.prepare(rotation_lines=self.plan['rotation'])
        host, client = session_commands(
            dedicated_executable=engine['dedicated_executable'],
            client_executable=engine['client_executable'],
            config_path=self.paths.config_path,
            rotation_path=self.paths.rotation_path)
        self.host_argv, self.client_argv = host, client
        self.host_stdout = self.paths.host_stdout
        self.client_stdout = self.paths.client_stdout
        self._set(status='files_prepared',
                  rotation_sha256=rotation_sha256(self.plan['rotation']))

    def _start_recorder(self):
        actions = self._session_event('start')
        if actions != ['start:recorder']:
            raise LaunchError('lifecycle refused the recorder start')
        self._set(attempt_id=self.session.attempt_id)
        self.recorder = self.recorder_factory(
            output_root=self.paths.flight_root,
            log_paths=[self.host_log],
            session_id=self.session.session_id,
            attempt_id=self.session.attempt_id,
            simulation=False)
        self.recorder.start()
        self._record_identity('recorder', self.recorder.recorder_pid,
                              self.recorder.recorder_start_id)
        marker = self.recorder.await_ready()
        actions = self._session_event(
            'recorder_ready',
            schema=marker.get('schema'),
            recorder_pid=marker.get('recorder_pid'),
            recorder_start_id=marker.get('recorder_start_id'),
            watcher_id=marker.get('watcher_id'),
            log_offsets_captured=marker.get('log_offsets_captured'),
            watcher_active=marker.get('watcher_active'),
            engine_ready=marker.get('engine_ready'),
            mission_ready=marker.get('mission_ready'),
            recorder_alive=True)
        if actions != ['start:host']:
            raise LaunchError('recorder readiness did not authorize the host')
        self._set(status='recorder_ready')

    def _start_host(self):
        self.host = self.host_session_factory(self.host_stdout, capture_stdin=True)
        self.host.start(self.host_argv, cwd=self.plan['engine']['warband_root'],
                        env=None)
        self._record_identity('host', self.host.pid,
                              'pid-%d-%s' % (self.host.pid, secrets.token_hex(8)))
        self.receipt['host_pid'] = self.host.pid
        self._set(status='host_started')
        if not self.waiter.until(self.host.is_running, 10.0):
            raise LaunchError('host exited during startup')
        if not self.waiter.until(
                lambda: host_bound_loopback(self.host.pid,
                                            runner=self.netstat_runner),
                self.settings['host_ready_timeout']):
            raise LaunchError('host did not bind loopback ' + ENDPOINT)
        self.host_bound_seen = True
        actions = self._session_event('host_ready', recorder_alive=True)
        if actions != ['start:client']:
            raise LaunchError('host readiness did not authorize the client')
        self._set(status='host_bound_loopback', host_bound_loopback=True)

    def _start_client(self):
        self.client = self.client_session_factory(self.client_stdout,
                                                  capture_stdin=False)
        self.client.start(self.client_argv, cwd=self.plan['engine']['warband_root'],
                          env=None)
        self._record_identity('client', self.client.pid,
                              'pid-%d-%s' % (self.client.pid, secrets.token_hex(8)))
        self.receipt['client_pid'] = self.client.pid
        self._set(status='client_started')
        if not self.waiter.until(self.client.is_running, 10.0):
            raise LaunchError('client exited during startup')

    def _attach(self):
        ack = self.recorder.attach(host=self.host.proc, client=self.client.proc)
        if not isinstance(ack, dict) or ack.get('attachment_accepted') is not True:
            raise LaunchError('recorder did not accept the owned game children')
        self._set(status='attached')

    def _await_join_and_mission(self):
        join = self.waiter.until(
            lambda: contains_marker(self.host_stdout, JOIN_MARKERS),
            self.settings['join_timeout'])
        self.join_observed = bool(join)
        self.receipt['join_observed'] = self.join_observed
        if not join:
            self.plan.setdefault('warnings', []).append(
                'join_not_observed_within_timeout')
            return
        if self._session_event('joined') == []:
            self._set(status='joined')
        mission = self.waiter.until(
            lambda: contains_marker(self.host_stdout, MISSION_MARKERS),
            self.settings['mission_timeout'])
        self.mission_observed = bool(mission)
        self.receipt['mission_observed'] = self.mission_observed
        if mission and self._session_event('mission_entered') == []:
            self._set(status='playing')

    def _play(self):
        max_seconds = self.settings['max_seconds']
        deadline = None if not max_seconds else self.waiter.clock() + max_seconds
        interval = self.settings['poll_interval']
        self._set(status='playing')
        while True:
            if not self.client.is_running():
                return 'client_exit'
            if not self.host.is_running():
                return 'host_exit'
            proc = getattr(self.recorder, 'proc', None)
            if proc is not None and proc.poll() is not None:
                return 'recorder_exit'
            if deadline is not None and self.waiter.clock() >= deadline:
                return 'max_seconds'
            self.waiter.pause(interval)

    # -- shutdown and sealing ---------------------------------------------

    def _stop_child(self, name):
        child = getattr(self, name, None)
        if child is None:
            return
        try:
            running = child.is_running()
        except OSError:
            running = False
        if running:
            if name == 'host':
                child.send_line('quit')
            if not self.waiter.until(lambda: not child.is_running(),
                                     self.settings['shutdown_timeout']):
                child.terminate()
                if not self.waiter.until(lambda: not child.is_running(),
                                         self.settings['terminate_timeout']):
                    child.kill()
                    self.waiter.until(lambda: not child.is_running(), 5.0)
        try:
            child.wait(timeout=self.settings['terminate_timeout'])
        except (subprocess.TimeoutExpired, OSError):
            pass
        self.receipt[name + '_exit_code'] = getattr(child, 'returncode', None)
        try:
            child.close()
        except (OSError, RuntimeError):
            pass

    def _seal_and_stop_recorder(self):
        if self.recorder is None:
            return
        if getattr(self.recorder, 'attached', None) is None:
            self.recorder.close()
            return
        try:
            self.recorder.add_artifact(self.host_stdout, name='host_stdout.log')
            self.receipt['artifacts'] = ['host_stdout.log']
            stopped = self.recorder.stop_after_exit(
                timeout=self.settings['recorder_stop_timeout'])
        except Exception as exc:  # noqa: BLE001 - evidence failure must be recorded
            self.receipt['evidence'] = {'verified': False,
                                        'error': type(exc).__name__ + ': ' + str(exc)}
            try:
                self.recorder.close()
            except Exception:
                pass
            raise LaunchError('evidence sealing failed: ' + type(exc).__name__)
        evidence = stopped.get('evidence') or {}
        self.receipt['evidence'] = {
            'verified': evidence.get('verified') is True,
            'file_count': evidence.get('file_count'),
            'recorder_outcome': (stopped.get('receipt') or {}).get('outcome'),
        }
        flight_dir = Path(self.recorder.session_dir)
        try:
            self.receipt['evidence_bundle'] = str(
                flight_dir.relative_to(self.paths.evidence_root)).replace(os.sep, '/')
        except ValueError:
            self.receipt['evidence_bundle'] = flight_dir.name
        try:
            summary = self.summary_runner(flight_dir)
        except Exception as exc:  # noqa: BLE001 - summary is additive evidence
            summary = {'status': 'failed',
                       'error': type(exc).__name__ + ': ' + str(exc)}
        if isinstance(summary, dict):
            self.receipt['summary'] = summary
            try:
                atomic_write_json(self.paths.summary_path, summary)
            except OSError:
                pass

    def _drive_stop(self, actions):
        pending = list(actions)
        seen = set()
        while pending:
            action = pending.pop(0)
            if action in seen:
                continue
            seen.add(action)
            if action == 'stop:client':
                self._stop_child('client')
                pending.extend(self._session_exit('client'))
            elif action == 'stop:host':
                self._stop_child('host')
                pending.extend(self._session_exit('host'))
            elif action == 'stop:recorder':
                self._seal_and_stop_recorder()
                pending.extend(self._session_exit('recorder'))
            else:
                raise LaunchError('unknown lifecycle action: ' + str(action))

    def _shutdown(self, reason):
        self._set(status='stopping')
        if reason == 'client_exit':
            actions = self._session_exit('client')
        elif reason == 'host_exit':
            actions = self._session_exit('host')
        elif reason == 'recorder_exit':
            actions = self._session_exit('recorder')
        else:
            actions = self._session_event('stop')
        self._drive_stop(actions)

    # -- entry point -------------------------------------------------------

    def run(self):
        self.receipt['start_utc'] = self.now_utc()
        try:
            self._prepare_files()
            self._start_recorder()
            self._start_host()
            self._start_client()
            self._attach()
            self._await_join_and_mission()
            reason = self._play()
        except KeyboardInterrupt:
            self.receipt['error'] = 'interrupted'
            self._set(status='interrupted', lifecycle_outcome='interrupted')
            self._abort_owned()
            return self._finalize()
        except Exception as exc:  # noqa: BLE001 - record every startup failure
            self.receipt['error'] = type(exc).__name__ + ': ' + str(exc)
            self._set(status='failed', lifecycle_outcome='failed')
            self._abort_owned()
            return self._finalize()
        try:
            self._shutdown(reason)
        except Exception as exc:  # noqa: BLE001 - shutdown failure is not success
            self.receipt['error'] = type(exc).__name__ + ': ' + str(exc)
            self._abort_owned()
            self._set(status='failed', lifecycle_outcome='failed')
            return self._finalize()
        clean = (self.session.state == 'stopped' and not self.session.error
                 and (self.receipt.get('evidence') or {}).get('verified') is True)
        self._set(status='stopped' if clean else 'failed',
                  lifecycle_outcome='clean_stop' if clean else 'failed')
        if not clean and self.session.error:
            self.receipt['error'] = self.session.error
        return self._finalize()

    def _abort_owned(self):
        """Best-effort cleanup of only the launcher's own children."""
        for name in ('client', 'host'):
            try:
                self._stop_child(name)
            except (OSError, RuntimeError, LaunchError):
                pass
        if self.recorder is not None:
            try:
                self.recorder.close()
            except Exception:  # noqa: BLE001 - cleanup must not mask the error
                pass
        for session in (self.client, self.host):
            try:
                if session is not None:
                    session.close()
            except (OSError, RuntimeError):
                pass

    def _finalize(self):
        if self.recorder is not None:
            try:
                self.recorder.close()
            except Exception:  # noqa: BLE001 - reaping must not mask the outcome
                pass
        self.receipt['end_utc'] = self.now_utc()
        self.receipt['attempt_id'] = self.session.attempt_id
        self.receipt['rotation_sha256'] = rotation_sha256(self.plan['rotation'])
        try:
            atomic_write_json(self.paths.launch_receipt, self.receipt)
        except OSError:
            pass
        return self.receipt

    def _default_summary_runner(self, flight_dir):
        argv = [sys.executable, str(self.repo_root / 'tools' / 'diagnostics.py'),
                'summary', str(flight_dir), '--json']
        try:
            completed = subprocess.run(argv, cwd=str(self.repo_root),
                                       capture_output=True, text=True, timeout=120,
                                       shell=False)
        except (OSError, subprocess.TimeoutExpired):
            return {'status': 'unavailable'}
        if completed.returncode != 0:
            return {'status': 'failed',
                    'error': 'diagnostics_exit_' + str(completed.returncode)}
        try:
            summary = json.loads((completed.stdout or '')[:MAX_SUMMARY_OUTPUT])
        except json.JSONDecodeError:
            return {'status': 'invalid_json'}
        return summary if isinstance(summary, dict) else {'status': 'invalid_shape'}


# -- CLI ----------------------------------------------------------------------

def _print_plan(plan):
    lines = ['Play City plan: ' + ('OK' if plan.get('ok') else 'BLOCKED')]
    engine = plan.get('engine') or {}
    lines.append('  warband : ' + str(engine.get('warband_root') or 'not selected'))
    lines.append('  client  : ' + str(engine.get('client_executable') or 'not found'))
    lines.append('  host    : ' + str(engine.get('dedicated_executable') or 'not found'))
    lines.append('  join    : ' + str(plan.get('client_join_address')) + ' (loopback only)')
    install = plan.get('install') or {}
    lines.append('  module  : ' + ('rebuild/install required' if install.get('needed')
                                   else 'installed City module reused'))
    if install.get('plan') and install['plan'].get('archive'):
        audit = install['plan'].get('archive_identity') or {}
        lines.append('  archive : identity=%s crc=%s'
                     % (audit.get('identity_ok'), audit.get('crc_status')))
    rotation = plan.get('rotation_sha256')
    lines.append('  rotation: ' + (str(rotation)[:16] + '...' if rotation else 'none'))
    lines.append('  allies  : team-0 bots=%s (%s)'
                 % (plan.get('team0_bots'), plan.get('rotation_profile')))
    for blocker in plan.get('blockers') or []:
        lines.append('  blocker : ' + blocker)
    for warning in plan.get('warnings') or []:
        lines.append('  warning : ' + warning)
    return '\n'.join(lines)


def _print_receipt(receipt):
    lines = ['Play City: ' + str(receipt.get('status')),
             '  session   : ' + str(receipt.get('session_id')),
             '  lifecycle : ' + str(receipt.get('lifecycle_outcome')),
             '  host bound loopback : ' + str(receipt.get('host_bound_loopback')),
             '  join observed       : ' + str(receipt.get('join_observed')),
             '  mission observed    : ' + str(receipt.get('mission_observed')),
             '  evidence  : ' + str(receipt.get('evidence')),
             '  bundle    : ' + str(receipt.get('evidence_bundle')),
             '  runtime_verified : ' + str(receipt.get('runtime_verified'))]
    if receipt.get('error'):
        lines.append('  error     : ' + str(receipt.get('error')))
    summary = receipt.get('summary') or {}
    if summary.get('status') not in (None, 'not_collected'):
        lines.append('  summary   : ' + ('ok' if summary.get('verified')
                                         else 'unverified'))
    return '\n'.join(lines)


def _parse_settings(args):
    return {
        'host_ready_timeout': float(args.host_ready_timeout),
        'join_timeout': float(args.join_timeout),
        'mission_timeout': float(args.mission_timeout),
        'shutdown_timeout': float(args.shutdown_timeout),
        'recorder_stop_timeout': float(args.recorder_stop_timeout),
        'max_seconds': float(args.max_minutes) * 60.0,
        'session_timeout': float(args.session_timeout),
    }


def _discovery_for(args):
    steam, games = ([], []) if args.no_known_folders else known_locations()
    custom = list(args.custom_path or [])
    if args.game_root:
        custom.append(args.game_root)
    return discover([*steam, *(args.steam_root or [])], custom, games)


def _build_plan_from_args(args, *, allow_install):
    report = _discovery_for(args)
    evidence_root = (Path(args.evidence_root).expanduser()
                     if args.evidence_root else DEFAULT_EVIDENCE_DIR)
    return build_launch_plan(
        discovery_report=report, evidence_root=evidence_root,
        archive=args.archive, game_root=args.game_root,
        client_exe=args.client_exe, dedicated_exe=args.dedicated_exe,
        rebuild=getattr(args, 'rebuild', False), allow_install=allow_install,
        settings=_parse_settings(args),
        team0_bots=getattr(args, 'team0_bots', None),
        stock_rotation=getattr(args, 'stock_rotation', False))


def _run_install_if_needed(plan):
    install = plan.get('install') or {}
    if not install.get('needed'):
        return None
    install_plan = install.get('plan')
    if not install_plan:
        raise LaunchError('install plan missing')
    receipt = execute_install(install_plan)
    status = receipt.get('status')
    if status != 'installed':
        raise LaunchError('City install failed: ' + str(status)
                          + (' (' + ', '.join(receipt.get('blockers') or []) + ')'
                             if receipt.get('blockers') else ''))
    try:
        atomic_write_json(Path(install_plan['evidence_root'])
                          / ('install-receipt-' + str(install_plan['transaction_id'])
                             + '.json'), receipt)
    except OSError:
        pass
    installed = installed_module_status(
        plan['engine']['warband_root'],
        expected_source_sha256=install_plan.get('expected_source_sha256'))
    if not installed.get('ok'):
        raise LaunchError('installed module failed post-install verification')
    plan['install']['installed'] = installed
    plan['install']['installed_ok'] = True
    plan['install']['receipt'] = receipt
    return receipt


def _host_session(path, capture_stdin):
    from .host_session import HostSession
    return HostSession(path, capture_stdin=capture_stdin)


def command_play(args):
    plan = _build_plan_from_args(args, allow_install=not args.no_install)
    if not plan.get('ok'):
        if args.json:
            print(json.dumps(plan, indent=2, sort_keys=True))
        else:
            print(_print_plan(plan))
        return 2
    try:
        _run_install_if_needed(plan)
    except (LaunchError, OSError, ValueError) as exc:
        print('Play City refused: ' + str(exc), file=sys.stderr)
        return 2
    settings = plan['settings']
    session = Session(route='dedicated', endpoint='127.0.0.1',
                      timeout=max(settings['session_timeout'], SESSION_TIMEOUT_FLOOR),
                      client_exit_ends_session=True)
    launcher = CityLauncher(
        plan, session=session,
        recorder_factory=lambda **kwargs: PassiveRecorder(
            **kwargs, timeout=max(settings['session_timeout'], SESSION_TIMEOUT_FLOOR)),
        host_session_factory=_host_session,
        client_session_factory=_host_session,
        waiter=Waiter(interval=settings['poll_interval']),
        logger=lambda message: None,
    )
    receipt = launcher.run()
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        print(_print_receipt(receipt))
    return 0 if receipt.get('status') == 'stopped' else 3


def command_plan(args):
    plan = _build_plan_from_args(args, allow_install=True)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(_print_plan(plan))
    return 0 if plan.get('ok') else 2


def command_install(args):
    plan = _build_plan_from_args(args, allow_install=True)
    if not plan.get('ok'):
        if args.json:
            print(json.dumps(plan, indent=2, sort_keys=True))
        else:
            print(_print_plan(plan))
        return 2
    try:
        receipt = _run_install_if_needed(plan)
    except (LaunchError, OSError, ValueError) as exc:
        print('City install refused: ' + str(exc), file=sys.stderr)
        return 2
    if receipt is None:
        print('City module already installed and valid; nothing to do.')
        return 0
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        print('City install: ' + str(receipt.get('status')))
        print('  module sha256 : ' + str(receipt.get('module_sha256')))
        print('  files         : ' + str(receipt.get('file_count')))
        print('  backup        : ' + str(receipt.get('backup')))
    return 0 if receipt.get('status') == 'installed' else 2


def command_doctor(args):
    plan = _build_plan_from_args(args, allow_install=True)
    report = {
        'schema': 'zombieee.city-doctor.v1',
        'ok': plan.get('ok'),
        'plan': plan,
        'blockers': plan.get('blockers'),
        'runtime_verified': False,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_print_plan(plan))
    return 0 if plan.get('ok') else 2


def command_rollback(args):
    try:
        receipt = _read_bounded_json(args.receipt)
    except (OSError, ValueError, LaunchError) as exc:
        print('Rollback refused: ' + str(exc), file=sys.stderr)
        return 2
    result = restore_backup(receipt)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print('Rollback: ' + str(result.get('status'))
              + (' (' + str(result.get('error')) + ')' if result.get('error') else ''))
    return 0 if result.get('status') == 'restored' else 2


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--game-root', help='explicit Warband root (must be discoverable)')
    common.add_argument('--client-exe', help='explicit WSE2 client executable')
    common.add_argument('--dedicated-exe', help='explicit WSE2 dedicated executable')
    common.add_argument('--archive', action='append',
                        help='pinned ZOMBIEEEBeta04.rar (repeat for selection)')
    common.add_argument('--evidence-root', help='private local evidence directory')
    common.add_argument('--no-known-folders', action='store_true',
                        help='do not use environment/registry install hints')
    common.add_argument('--steam-root', action='append',
                        help='extra Steam root (contains steamapps)')
    common.add_argument('--custom-path', action='append',
                        help='extra discovery path (never executed)')
    common.add_argument('--json', action='store_true', help='emit JSON')
    common.add_argument('--team0-bots', '--team1-bots', dest='team0_bots',
                        type=int, default=None, metavar='N',
                        help='allied team-0 bots (1-based rotation team 1; '
                             'City default 4, stock 0)')
    common.add_argument('--stock-rotation', action='store_true',
                        help='emit the stock rotation with zero allied defenders')
    common.add_argument('--rebuild', action='store_true',
                        help='force a reversible City rebuild/install')
    timeouts = argparse.ArgumentParser(add_help=False)
    timeouts.add_argument('--host-ready-timeout', type=float, default=45.0)
    timeouts.add_argument('--join-timeout', type=float, default=120.0)
    timeouts.add_argument('--mission-timeout', type=float, default=60.0)
    timeouts.add_argument('--shutdown-timeout', type=float, default=20.0)
    timeouts.add_argument('--recorder-stop-timeout', type=float, default=90.0)
    timeouts.add_argument('--session-timeout', type=float, default=900.0)
    timeouts.add_argument('--max-minutes', type=float, default=0.0,
                          help='automatic stop after N minutes; 0 waits for client exit')
    parser = argparse.ArgumentParser(
        description='Private one-command City playthrough for an owned Warband + WSE2 install.')
    sub = parser.add_subparsers(dest='command')
    play = sub.add_parser('play', parents=[common, timeouts],
                          help='install if needed, then launch and record City')
    play.add_argument('--no-install', action='store_true',
                      help='never modify the game tree; fail if the module is missing')
    play.set_defaults(func=command_play)
    plan_cmd = sub.add_parser('plan', parents=[common, timeouts],
                              help='show the launch plan; never writes or launches')
    plan_cmd.set_defaults(func=command_plan)
    install = sub.add_parser('install', parents=[common, timeouts],
                             help='build/install the City module only (reversible)')
    install.set_defaults(func=command_install)
    doctor = sub.add_parser('doctor', parents=[common, timeouts],
                            help='read-only readiness report')
    doctor.set_defaults(func=command_doctor)
    rollback = sub.add_parser('rollback', help='restore a retained install backup')
    rollback.add_argument('--receipt', required=True,
                          help='install receipt JSON recorded by a previous run')
    rollback.add_argument('--json', action='store_true')
    rollback.set_defaults(func=command_rollback)
    return parser


COMMANDS = ('play', 'plan', 'install', 'doctor', 'rollback')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in COMMANDS:
        # Bare invocation is the owner-facing one-command play flow.
        argv = ['play', *argv]
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except LaunchError as exc:
        print('Play City refused: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
