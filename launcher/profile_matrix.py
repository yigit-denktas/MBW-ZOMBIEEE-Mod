"""Read-only no-launch AI/profile matrix for the City validation builds.

D validates AI/balance fixes with sealed runs. This module gives a repeatable,
deterministic planning step *before* any host process exists:

* it composes the validated rotation (defender squad size, enemy profile, team-2
  count) into the exact command lines and SHA-256 D should find in
  ``rotation.txt`` and the launch receipt;
* it reads the **installed** ``Modules/ZOMBIEEE_Remaster/ZOMBIEEE_REMASTER.json``
  build receipt (Agent A's source of truth) and reports the expected weak
  roster range (894-only vs full 894..911), defender troop ids, rear/forward
  hold entries/stance, zombie block mode and loadout profile;
* it flags mismatches between the requested profile and the installed build
  contract instead of silently claiming a configuration is active;
* it prints the summary fields D must check in the sealed bundle, marking them
  as expected observations, never runtime facts.

No process is started, no build is executed and nothing is written. The planner
only reads files and the in-memory plan; all receipts keep
``runtime_verified=false``.
"""
from __future__ import annotations

from pathlib import Path

from .install import MODULE_NAME, InstallError, read_module_manifest

SCHEMA = 'zombieee.profile-matrix.v1'
REAR_HOLD_ENTRIES = [0, 1, 0]
RECEIPT_FIELDS = (
    'enemy_profile',
    'team2_bots',
    'team0_bots',
    'rotation_profile',
    'rotation_sha256',
    'host_pid',
    'client_pid',
    'host_bound_loopback',
    'join_observed',
    'mission_observed',
    'evidence.verified',
    'evidence_bundle',
    'summary',
    'runtime_verified',
)
EXPECTED_BLOCK_CHOICES = ('stock', 'default')
EXPECTED_WAVE_VISITORS = ('slow', 'original')
EXPECTED_REINFORCE = ('default', 'stock')


def _bounded_int(value):
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _int_list(value, *, limit=32):
    if not isinstance(value, (list, tuple)):
        return None
    result = []
    for item in value[:limit]:
        number = _bounded_int(item)
        if number is None:
            return None
        result.append(number)
    return result


def extract_installed_profile(game_root):
    """Read the installed module receipt as data; never infer missing fields."""
    module_dir = Path(game_root).expanduser().absolute() / 'Modules' / MODULE_NAME
    result = {
        'module_dir': str(module_dir),
        'present': module_dir.is_dir(),
        'manifest_read': False,
        'map_scope': None,
        'trigger_count': None,
        'defender_loadout_profile': None,
        'zombie_bot_roster': None,
        'invader_troops': None,
        'defender_troops': None,
        'hold_entries': None,
        'defensive_line': None,
        'wave_visitors': None,
        'defender_target': None,
        'defender_reinforce': None,
        'zombie_block': {'mode': 'unknown', 'applied': None,
                         'shield_item': None, 'troop_count': None},
        'defender_loadouts': None,
        'runtime_verified': None,
        'problems': [],
    }
    if not result['present']:
        result['problems'].append('installed_module_missing')
        return result
    try:
        manifest = read_module_manifest(module_dir)
    except InstallError as exc:
        result['problems'].append(str(exc))
        return result
    result['manifest_read'] = True
    result['runtime_verified'] = manifest.get('runtime_verified')
    result['map_scope'] = manifest.get('experimental_map_scope')
    result['trigger_count'] = _bounded_int(manifest.get('final_trigger_count'))
    result['defender_loadout_profile'] = manifest.get('defender_loadout_profile')
    roster = manifest.get('native_roster_patch')
    if isinstance(roster, dict):
        result['invader_troops'] = _int_list(roster.get('invader_candidates'))
        result['defender_troops'] = _int_list(roster.get('defender_candidates'))
        if roster.get('applied') is not True:
            result['problems'].append('native_roster_patch_not_applied')
    else:
        result['problems'].append('native_roster_patch_missing')
    result['zombie_bot_roster'] = manifest.get('zombie_bot_roster')
    guardposts = manifest.get('experimental_city_guardposts')
    if isinstance(guardposts, dict):
        result['hold_entries'] = _int_list(guardposts.get('hold_entries'), limit=8)
        defensive = guardposts.get('defensive_line')
        result['defensive_line'] = defensive if type(defensive) is bool else None
        visitors = guardposts.get('wave_visitors')
        if visitors in EXPECTED_WAVE_VISITORS:
            result['wave_visitors'] = visitors
        else:
            result['problems'].append('wave_visitors_receipt_missing')
        target = guardposts.get('defender_target')
        if type(target) is int and not isinstance(target, bool) \
                and 0 <= target <= 64:
            result['defender_target'] = target
        else:
            result['problems'].append('defender_reinforce_receipt_missing')
        reinforce = guardposts.get('defender_reinforce')
        if type(reinforce) is bool:
            result['defender_reinforce'] = reinforce
        elif 'defender_reinforce_receipt_missing' not in result['problems']:
            result['problems'].append('defender_reinforce_receipt_missing')
    else:
        result['problems'].append('city_guardposts_receipt_missing')
    block = manifest.get('zombie_block')
    if block is None:
        result['zombie_block'] = {'mode': 'stock', 'applied': False,
                                  'shield_item': None, 'troop_count': None}
    elif isinstance(block, dict):
        troops = _int_list(block.get('troops'), limit=64)
        result['zombie_block'] = {
            'mode': 'default' if block.get('applied') is True else 'unknown',
            'applied': block.get('applied') is True,
            'shield_item': block.get('shield_item'),
            'troop_count': len(troops) if troops is not None else None,
        }
    else:
        result['problems'].append('zombie_block_receipt_invalid')
    return result


def _wave1_expectation(plan, installed):
    profile = plan.get('enemy_profile')
    generic = plan.get('team2_bots')
    candidates = installed.get('invader_troops')
    roster = installed.get('zombie_bot_roster')
    if profile == 'native-only':
        return {
            'generic_bot_count': 0,
            'generic_troop_ids': None,
            'generic_roster': None,
            'native_visitors': ('native wave table; not selected by '
                                'set_bot_count, classes/ids only from the '
                                'sealed summary'),
            'expected': ('team 2 starts with no generic bots; only native '
                         'wave visitors appear when a round starts'),
        }
    return {
        'generic_bot_count': generic,
        'generic_troop_ids': candidates,
        'generic_roster': roster,
        'native_visitors': ('native wave table adds visitors on top of the '
                            'generic count; classes/ids only from the sealed '
                            'summary'),
        'expected': ('original slow Zombie 894 only for the weak roster'
                     if roster == 'weak' else
                     'full native invader roster for a non-weak build'
                     if roster == 'full' else
                     'generic roster unknown from the installed receipt'),
    }


def build_profile_matrix(plan, *, installed=None, expected_zombie_block='stock',
                         expected_hold='rear', expected_wave_visitors='slow',
                         expected_defender_reinforce='default'):
    """Compose the no-launch expectation matrix for one launch plan.

    Returns a JSON-friendly dict. ``ok`` is true only when the plan is runnable,
    the installed module receipt was readable and no requested-profile mismatch
    was found. Mismatches are reported as data; nothing is auto-corrected.
    """
    if expected_zombie_block not in EXPECTED_BLOCK_CHOICES:
        raise ValueError('expected_zombie_block must be one of '
                         + ', '.join(EXPECTED_BLOCK_CHOICES))
    if expected_hold not in ('rear', 'forward'):
        raise ValueError('expected_hold must be rear or forward')
    if expected_wave_visitors not in EXPECTED_WAVE_VISITORS:
        raise ValueError('expected_wave_visitors must be one of '
                         + ', '.join(EXPECTED_WAVE_VISITORS))
    if expected_defender_reinforce not in EXPECTED_REINFORCE:
        raise ValueError('expected_defender_reinforce must be one of '
                         + ', '.join(EXPECTED_REINFORCE))
    engine = plan.get('engine') or {}
    game_root = engine.get('warband_root')
    if installed is None:
        installed = (extract_installed_profile(game_root)
                     if isinstance(game_root, str) else
                     {'present': False, 'manifest_read': False,
                      'problems': ['warband_root_missing']})
    mismatches, gaps = [], []

    def mismatch(field, expected, actual, note):
        mismatches.append({'field': field, 'expected': expected,
                           'actual': actual, 'note': note})

    if not plan.get('ok'):
        gaps.extend(['plan_blocked:' + blocker
                     for blocker in (plan.get('blockers') or [])][:24])
    if not installed.get('present'):
        gaps.append('installed_module_missing')
    elif not installed.get('manifest_read'):
        gaps.extend(installed.get('problems') or ['installed_receipt_unreadable'])
    else:
        if installed.get('runtime_verified') is True:
            mismatch('runtime_verified', False, True,
                     'build receipt must never claim runtime verification')
        if installed.get('map_scope') != 'city-only':
            mismatch('experimental_map_scope', 'city-only',
                     installed.get('map_scope'), 'launcher requires a City-only build')
        trigger_count = installed.get('trigger_count')
        if trigger_count is None or trigger_count < 31:
            mismatch('final_trigger_count', '>=31', trigger_count,
                     'City tactical build expectation')
        if installed.get('defender_loadout_profile') != 'balanced-ai':
            mismatch('defender_loadout_profile', 'balanced-ai',
                     installed.get('defender_loadout_profile'),
                     'launcher City build profile')
        if installed.get('zombie_bot_roster') not in ('weak', 'full'):
            gaps.append('zombie_bot_roster_unknown')
        if plan.get('enemy_profile') == 'weak-wave1' \
                and installed.get('zombie_bot_roster') != 'weak':
            mismatch('zombie_bot_roster', 'weak',
                     installed.get('zombie_bot_roster'),
                     'weak-wave1 requires the weak 894-only generic roster')
        expected_entries = REAR_HOLD_ENTRIES if expected_hold == 'rear' else None
        actual_entries = installed.get('hold_entries')
        if expected_hold == 'rear' and actual_entries != REAR_HOLD_ENTRIES:
            mismatch('hold_entries', REAR_HOLD_ENTRIES, actual_entries,
                     'rear/spawn-line hold expected (entries 0/1)')
        elif expected_hold == 'forward' and actual_entries == REAR_HOLD_ENTRIES:
            mismatch('hold_entries', 'forward', actual_entries,
                     'forward guard sectors requested')
        if expected_entries is not None and installed.get('defensive_line') is False:
            mismatch('defensive_line', True, False,
                     'receipt says the build uses forward guard sectors')
        block = installed.get('zombie_block') or {}
        block_mode = block.get('mode')
        if expected_zombie_block == 'stock' and block_mode == 'default':
            mismatch('zombie_block', 'stock', block_mode,
                     "task-34 target keeps the stock block (no shield in hand); "
                     "rebuild with --zombie-block stock or pass "
                     "--expected-zombie-block default to accept the shield build")
        elif expected_zombie_block == 'default' and block_mode == 'stock':
            mismatch('zombie_block', 'default', block_mode,
                     'expected shield/block patch, installed build is stock')
        elif block_mode == 'unknown':
            gaps.append('zombie_block_mode_unknown')
        installed_visitors = installed.get('wave_visitors')
        if installed_visitors is None:
            gaps.append('wave_visitors_receipt_missing')
        elif installed_visitors != expected_wave_visitors:
            mismatch('wave_visitors', expected_wave_visitors,
                     installed_visitors,
                     'task-34 stages wave slots 200..244 to the slow '
                     'Zombie 894 family; original uses the 0.4 table')
        installed_target = installed.get('defender_target')
        installed_reinforce = installed.get('defender_reinforce')
        if installed_target is None or installed_reinforce is None:
            gaps.append('defender_reinforce_receipt_missing')
        elif expected_defender_reinforce == 'default':
            expected_target = plan.get('team0_bots')
            if installed_reinforce is not True:
                mismatch('defender_reinforce', 'default(enabled)',
                         installed_reinforce,
                         'spawn_agent refill expected (task-34)')
            if installed_target != expected_target:
                mismatch('defender_target', expected_target,
                         installed_target,
                         'spawn_agent refill target must match the '
                         'team-0 squad size')
        else:
            if installed_reinforce is True or installed_target != 0:
                mismatch('defender_reinforce', 'stock',
                         {'enabled': installed_reinforce,
                          'target': installed_target},
                         'stock refill requested; receipt shows spawn_agent')

    rotation = list(plan.get('rotation') or [])
    matrix = {
        'schema': SCHEMA,
        'schema_version': 1,
        'read_only': True,
        'no_launch': True,
        'runtime_verified': False,
        'ok': (bool(plan.get('ok')) and installed.get('manifest_read') is True
               and not mismatches and not gaps),
        'plan_ok': bool(plan.get('ok')),
        'endpoint': plan.get('endpoint'),
        'client_join_address': plan.get('client_join_address'),
        'rotation': {
            'enemy_profile': plan.get('enemy_profile'),
            'team0_bots': plan.get('team0_bots'),
            'team2_bots': plan.get('team2_bots'),
            'rotation_profile': plan.get('rotation_profile'),
            'sha256': plan.get('rotation_sha256'),
            'lines': rotation,
            'expected_rotation_file': 'set_bot_count 1 %s / set_bot_count 2 %s / start'
            % (plan.get('team0_bots'), plan.get('team2_bots')),
        },
        'expected': {
            'team0_bots': plan.get('team0_bots'),
            'team1_generic_bots': plan.get('team2_bots'),
            'defenders_on_line': plan.get('team0_bots'),
            'defender_troop_ids': installed.get('defender_troops'),
            'wave1': _wave1_expectation(plan, installed),
            'hold': {
                'expected': expected_hold,
                'hold_entries': installed.get('hold_entries'),
                'defensive_line': installed.get('defensive_line'),
                'source': 'installed_module_receipt',
            },
            'zombie_block': {
                'expected': expected_zombie_block,
                'installed_mode': (installed.get('zombie_block') or {}).get('mode'),
                'shield_item': (installed.get('zombie_block') or {}).get('shield_item'),
                'troop_count': (installed.get('zombie_block') or {}).get('troop_count'),
                'source': 'installed_module_receipt',
            },
            'wave_visitors': {
                'expected': expected_wave_visitors,
                'installed': installed.get('wave_visitors'),
                'source': 'installed_module_receipt',
            },
            'defender_reinforce': {
                'expected': expected_defender_reinforce,
                'enabled': installed.get('defender_reinforce'),
                'target': installed.get('defender_target'),
                'expected_target': (plan.get('team0_bots')
                                    if expected_defender_reinforce == 'default'
                                    else 0),
                'source': 'installed_module_receipt',
            },
            'map_scope': installed.get('map_scope'),
            'trigger_count': installed.get('trigger_count'),
            'defender_loadout_profile': installed.get('defender_loadout_profile'),
            'rotation_sha256': plan.get('rotation_sha256'),
            'receipt_fields': list(RECEIPT_FIELDS),
            'summary_checks': [
                'composition/teams: team-0 bots == %s (native defenders)'
                % plan.get('team0_bots'),
                'troops.team0: defender troop ids %s'
                % (installed.get('defender_troops') or 'unknown from receipt'),
                'troops.team1 generic candidates: %s'
                % ((installed.get('invader_troops') or 'unknown')
                   if plan.get('team2_bots') else 'none (native-only)'),
                'hold: positions near rear spawn line entries 0/1; sector '
                'rotation is per wave parity',
                'zombie block: %s; runtime block behaviour only from the '
                'sealed summary' % expected_zombie_block,
                'wave-1 visitors: %s gating (slow = wave slots 200..244 '
                'resolve to Zombie 894 only)' % expected_wave_visitors,
                'defender refill: spawn_agent to target %s (%s) when below '
                'the rear line strength'
                % (installed.get('defender_target'),
                   'enabled' if installed.get('defender_reinforce')
                   else 'disabled'),
                'waves/rounds: expected from the sealed summary when a round '
                'starts with a connected player',
            ],
        },
        'installed': installed,
        'mismatches': mismatches,
        'gaps': gaps,
        'notes': [
            'Read-only planner: no host, build or recorder process is started.',
            'Expected values come from the launch plan + installed build receipt; '
            'runtime behaviour and wave completion are never claimed.',
            'rotation SHA-256 is over the exact lines above (UTF-8, LF, trailing LF).',
        ],
    }
    return matrix


def format_profile_matrix(matrix):
    """Human-readable planner output for ``python -m launcher.play_city matrix``."""
    rotation = matrix.get('rotation', {})
    expected = matrix.get('expected', {})
    lines = ['Play City profile matrix: ' + ('OK' if matrix.get('ok') else 'ATTENTION')]
    lines.append('  read-only/no-launch : %s' % matrix.get('no_launch'))
    lines.append('  enemy profile       : %s' % rotation.get('enemy_profile'))
    lines.append('  team-0 bots         : %s' % rotation.get('team0_bots'))
    lines.append('  team-2 generic bots : %s' % rotation.get('team2_bots'))
    lines.append('  rotation sha256     : %s' % rotation.get('sha256'))
    lines.append('  rotation file       : %s'
                 % rotation.get('expected_rotation_file'))
    wave1 = expected.get('wave1') or {}
    lines.append('  wave-1 generic ids  : %s' % wave1.get('generic_troop_ids'))
    lines.append('  wave-1 expectation  : %s' % wave1.get('expected'))
    hold = expected.get('hold') or {}
    lines.append('  hold entries        : %s (expected %s)'
                 % (hold.get('hold_entries'), hold.get('expected')))
    block = expected.get('zombie_block') or {}
    lines.append('  zombie block        : installed=%s expected=%s'
                 % (block.get('installed_mode'), block.get('expected')))
    visitors = expected.get('wave_visitors') or {}
    lines.append('  wave visitors       : installed=%s expected=%s'
                 % (visitors.get('installed'), visitors.get('expected')))
    refill = expected.get('defender_reinforce') or {}
    lines.append('  defender refill     : enabled=%s target=%s '
                 'expected=%s'
                 % (refill.get('enabled'), refill.get('target'),
                    refill.get('expected')))
    lines.append('  defender troop ids  : %s' % expected.get('defender_troop_ids'))
    for entry in matrix.get('mismatches') or []:
        lines.append('  mismatch : %s expected=%s actual=%s (%s)'
                     % (entry.get('field'), entry.get('expected'),
                        entry.get('actual'), entry.get('note')))
    for gap in matrix.get('gaps') or []:
        lines.append('  gap      : ' + str(gap))
    return '\n'.join(lines)
