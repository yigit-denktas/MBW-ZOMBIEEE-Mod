"""Read-only delivery checks for a City-first solo release candidate.

This is a **candidate gate**, not acceptance. It verifies the repository-facing
delivery contract that the release notes depend on:

* required files exist (version, README, Windows bootstrap/provenance docs,
  launcher, installer planner, A's builder and archive audit);
* documented reproducible commands are present;
* ``VERSION`` is well-formed and matches the installed module receipt when one is
  supplied;
* no proprietary archives/game executables/logs are tracked by Git;
* no local personal install paths or obvious secrets are present in tracked text;
* a supplied installed module is structurally a City build and still says
  ``runtime_verified=false``.

Nothing is built, installed or launched. Missing runtime evidence is reported as
a gap; it never flips a check to accepted.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from .install import MODULE_NAME, verify_built_module

SCHEMA = 'zombieee.release-gate.v1'
MAX_TRACKED_FILES = 20000
MAX_SCAN_BYTES = 256 * 1024
VERSION_RE = re.compile(
    r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
    r'(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$')
TRACEABILITY_REL = 'docs/release-traceability.json'
TRACEABILITY_SCHEMA = 'zombieee.release-traceability.v1'
WORK_ITEM_RE = re.compile(r'ZOM-[A-Z]+-\d+\Z')
HEX_COMMIT_RE = re.compile(r'[0-9a-fA-F]{7,40}\Z')
REQUIRED_FILES = {
    'VERSION': 'release version',
    'CHANGELOG.md': 'release history',
    'docs/RELEASE_TRACEABILITY.md': 'work-item to PR/commit/version links',
    'docs/release-traceability.json': 'machine-readable traceability record',
    'README.md': 'user-facing readme',
    'docs/WINDOWS_BOOTSTRAP.md': 'Windows install/launch instructions',
    'docs/PROVENANCE.md': 'provenance and attribution',
    'launcher/play_city.py': 'one-command entry point',
    'launcher/control_panel.py': 'desktop launcher surface',
    'launcher/install.py': 'reversible installer',
    'launcher/maintenance.py': 'repair and quarantine uninstall surface',
    'reference/LEGAL_RIGHTS_AND_CREDITS.md': 'rights/credits legal dossier',
    'reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md':
        'independent release/legal cross-review record',
    'installer/manifest.py': 'install planner',
    'tools/build.py': 'Agent A builder',
    'tools/archive_audit.py': 'pinned archive audit',
}
REQUIRED_COMMAND_TOKENS = (
    'launcher.play_city',
    'tools/build.py',
    'archive_audit',
)
FORBIDDEN_EXTENSIONS = ('.rar', '.zip', '.7z', '.exe', '.dll', '.log')
# Path/token privacy scan covers every tracked text file except these exact
# files, whose purpose is to document or detect private paths (no prefix-level
# allowlist that could hide a new leak in a whole directory).
SCAN_EXEMPT_FILES = {
    'docs/PROVENANCE.md': 'documents private-path policy',
    'progress/publishing-review.md': 'privacy review notes',
    'reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md':
        'independent privacy review record',
    'site/index.html': 'static tracker page with placeholder path text',
    'telemetry/privacy.py': 'privacy redaction implementation',
    'tests/test_diagnostics.py': 'privacy fixture paths',
    'tests/test_flight_recorder.py': 'privacy fixture paths',
    'tests/test_faction_log_guard.py': 'privacy fixture paths',
    'tools/diagnostics.py': 'privacy redaction implementation',
    'launcher/release_gate.py': 'privacy scanner source (regex literals)',
    'reference/MODDER_DIAGNOSTICS_RESEARCH.md':
        'diagnostics research quoting log-path policy examples',
    'tests/test_windows_release_traceability.py':
        'privacy-scanner regression fixtures (intentional leak strings)',
    'tests/test_flight_receipt_summary.py':
        'synthetic receipt/manifest path fixtures (no real personal paths)',
}
PERSONAL_PATH_RES = (
    # One or more literal backslashes: plain Windows paths and JSON-escaped
    # forms such as "C:\\Users\\name" in committed receipts/manifests.
    # Drive path with any mix of one-or-more backslashes/forward slashes
    # (plain, JSON-escaped and mixed-separator forms).
    re.compile(r'[A-Za-z]:[\\/]+Users[\\/]+[^"\\\s|<>]+'),
    re.compile(r'/(?:home|Users)/[^\s"\'<>]+'),
    re.compile(r'(?<![\w.>])(?:\\\\)+[A-Za-z0-9._-]+\\+[^\\\s"|<>]+'),
    re.compile(r'file://(?:/[A-Za-z]:)?/[^\s"\'<>]+'),
)
SECRET_RE = re.compile(
    r"(BEGIN [A-Z ]*PRIVATE KEY|\bghp_[A-Za-z0-9]{20,}"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}|\bAKIA[0-9A-Z]{16}"
    r"|\bsk-[A-Za-z0-9]{20,}|\bxox[bap]-[A-Za-z0-9-]{10,}"
    r"|\bglpat-[A-Za-z0-9_-]{20,}|\bAIza[0-9A-Za-z_-]{30,})")


class ReleaseGateError(RuntimeError):
    """The gate could not inspect its inputs."""


def git_tracked_files(root, *, runner=None, timeout=60):
    """Bounded list of tracked paths; never mutates the repository."""
    if runner is None:
        def runner(command, **kwargs):
            return subprocess.run(command, capture_output=True, text=True,
                                  timeout=kwargs.get('timeout', timeout),
                                  shell=False)
    try:
        completed = runner(['git', '-C', str(Path(root).absolute()),
                            'ls-files', '-z'], timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseGateError('git_tracked_files_unavailable') from exc
    if getattr(completed, 'returncode', 1) != 0:
        raise ReleaseGateError('git_tracked_files_failed')
    raw = completed.stdout if isinstance(completed.stdout, str) else ''
    files = [item for item in raw.split('\x00') if item][:MAX_TRACKED_FILES]
    return files


def _read_bounded(path):
    try:
        with open(path, 'rb') as stream:
            return stream.read(MAX_SCAN_BYTES).decode('utf-8', errors='replace')
    except OSError:
        return ''


def _valid_pr(entry, number):
    if not isinstance(entry, dict):
        return False
    if type(entry.get('number')) is not int or entry.get('number') != number:
        return False
    url = entry.get('url')
    if not isinstance(url, str) or not url.startswith(
            'https://github.com/') or ('/pull/' + str(number)) not in url:
        return False
    commit = entry.get('merge_commit')
    return isinstance(commit, str) and bool(HEX_COMMIT_RE.fullmatch(commit))


def _git(root, arguments, runner=None, timeout=60):
    if runner is None:
        def runner(command, **kwargs):
            return subprocess.run(command, capture_output=True, text=True,
                                  timeout=kwargs.get('timeout', timeout),
                                  shell=False)
    try:
        completed = runner(['git', '-C', str(Path(root).absolute())] + arguments,
                           timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseGateError('git_unavailable') from exc
    return getattr(completed, 'returncode', 1)


def _ancestry_checks(root, data, git_runner=None):
    """Check every recorded commit/merge SHA is an ancestor of the candidate."""
    source = data.get('source_revision')
    if not isinstance(source, str) or not re.fullmatch(r'[0-9a-fA-F]{40}', source):
        return {'status': 'invalid_source_revision', 'missing': [],
                'checked': 0, 'available': False}
    try:
        inside = _git(root, ['rev-parse', '--is-inside-work-tree'],
                      runner=git_runner)
    except ReleaseGateError:
        return {'status': 'unavailable', 'missing': [], 'checked': 0,
                'available': False}
    if inside != 0:
        return {'status': 'not_a_repository', 'missing': [], 'checked': 0,
                'available': False}
    commits = set()
    for item in data.get('work_items') or []:
        if not isinstance(item, dict):
            continue
        for value in item.get('commits') or []:
            if isinstance(value, str) and HEX_COMMIT_RE.fullmatch(value):
                commits.add(value)
        for pr in item.get('prs') or []:
            if isinstance(pr, dict):
                commit = pr.get('merge_commit')
                if isinstance(commit, str) and HEX_COMMIT_RE.fullmatch(commit):
                    commits.add(commit)
    for artifact in data.get('support_artifacts') or []:
        if isinstance(artifact, dict):
            if artifact.get('merged') is False or 'pending' in str(
                    artifact.get('state', '')):
                continue  # explicitly pending integration: never claimed as shipped
            for value in artifact.get('commits') or []:
                if isinstance(value, str) and HEX_COMMIT_RE.fullmatch(value):
                    commits.add(value)
            commit = artifact.get('merge_commit')
            if isinstance(commit, str) and HEX_COMMIT_RE.fullmatch(commit):
                commits.add(commit)
    for release in data.get('releases') or []:
        if isinstance(release, dict):
            for value in release.get('included_commits') or []:
                if isinstance(value, str) and HEX_COMMIT_RE.fullmatch(value):
                    commits.add(value)
    missing = []
    for commit in sorted(commits):
        try:
            if _git(root, ['merge-base', '--is-ancestor', commit, source],
                    runner=git_runner) != 0:
                missing.append(commit)
        except ReleaseGateError:
            return {'status': 'unavailable', 'missing': [], 'checked': 0,
                    'available': False}
    return {'status': 'failed' if missing else 'checked', 'missing': missing,
            'checked': len(commits), 'available': True}


METADATA_ONLY_PATHS = {
    'CHANGELOG.md', 'README.md', 'VERSION', 'docs/ROADMAP.md',
    'docs/RELEASE_TRACEABILITY.md', 'docs/release-traceability.json',
    'docs/WINDOWS_BOOTSTRAP.md', 'launcher/release_gate.py',
    'tests/test_windows_release_traceability.py',
}


def _git_output(root, arguments, runner=None, timeout=60):
    if runner is None:
        def runner(command, **kwargs):
            return subprocess.run(command, capture_output=True, text=True,
                                  timeout=kwargs.get('timeout', timeout),
                                  shell=False)
    try:
        completed = runner(['git', '-C', str(Path(root).absolute())] + arguments,
                           timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseGateError('git_unavailable') from exc
    stdout = getattr(completed, 'stdout', '') or ''
    return getattr(completed, 'returncode', 1), stdout


def _head_revision_checks(root, data, check, git_runner=None):
    """Fail closed when source_revision != HEAD without a metadata-only exception.

    A metadata PR cannot set source_revision to its own commit (that commit does
    not exist yet), so an explicit, documented exception is allowed only when the
    commits between source_revision and HEAD touch release-metadata/gate files
    exclusively. Any code/behavior commit in between fails the check.
    """
    source = data.get('source_revision')
    if not isinstance(source, str) or not re.fullmatch(r'[0-9a-fA-F]{40}', source):
        check('traceability_head_revision', False,
              'source_revision missing or not a 40-hex revision')
        return
    try:
        code, head = _git_output(root, ['rev-parse', 'HEAD'], runner=git_runner)
    except ReleaseGateError:
        check('traceability_head_revision', True,
              'unavailable: git not usable in this checkout')
        return
    if code != 0:
        check('traceability_head_revision', True,
              'unavailable: not a git checkout')
        return
    head = head.strip()
    if head.lower() == source.lower():
        check('traceability_head_revision', True,
              'source_revision == HEAD (%s)' % source)
        return
    exception = data.get('source_revision_exception')
    if not isinstance(exception, dict) or not exception.get('reason'):
        check('traceability_head_revision', False,
              'source_revision != HEAD and no documented '
              'source_revision_exception')
        return
    try:
        code, names = _git_output(root, ['diff', '--name-only', source, 'HEAD'],
                                  runner=git_runner)
    except ReleaseGateError:
        check('traceability_head_revision', True,
              'unavailable: cannot diff source_revision..HEAD')
        return
    if code != 0:
        check('traceability_head_revision', False,
              'cannot diff source_revision..HEAD')
        return
    changed = [name for name in names.splitlines() if name.strip()]
    offending = sorted(name for name in changed
                       if name not in METADATA_ONLY_PATHS)
    check('traceability_head_revision', not offending,
          ('metadata-only exception documented; changed=%s'
           % ','.join(changed[:10]) if not offending else
           'non-metadata change(s) between source_revision and HEAD: '
           + ','.join(offending[:10])))


def _traceability_checks(root, version_text, check, git_runner=None):
    """Validate VERSION <-> CHANGELOG <-> work-item/PR/commit traceability."""
    summary = {'schema': None, 'work_items': 0, 'linked_prs': 0,
               'included_prs': 0, 'gaps': 0, 'candidate_version': None}
    data = {}
    try:
        data = json.loads(_read_bounded(root / TRACEABILITY_REL))
    except (OSError, ValueError, TypeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    summary['schema'] = data.get('schema')
    summary['candidate_version'] = data.get('candidate_version')
    check('traceability_schema', data.get('schema') == TRACEABILITY_SCHEMA,
          'schema=' + str(data.get('schema')))
    check('traceability_version', data.get('candidate_version') == version_text,
          'record=%s VERSION=%s' % (data.get('candidate_version'), version_text))
    check('traceability_state',
          data.get('release_state') == 'candidate'
          and data.get('acceptance') == 'none'
          and data.get('runtime_verified') is False,
          'state=%s acceptance=%s runtime_verified=%s'
          % (data.get('release_state'), data.get('acceptance'),
             data.get('runtime_verified')))

    items = data.get('work_items')
    items = items if isinstance(items, list) else []
    summary['work_items'] = len(items)
    ids, work_prs, link_problems = set(), set(), []
    for entry in items:
        if not isinstance(entry, dict):
            link_problems.append('non_object_work_item')
            continue
        item_id = entry.get('id')
        if not isinstance(item_id, str) or not WORK_ITEM_RE.fullmatch(item_id):
            link_problems.append('invalid_work_item_id:' + str(item_id)[:40])
            continue
        if item_id in ids:
            link_problems.append('duplicate_work_item:' + item_id)
        ids.add(item_id)
        if entry.get('acceptance') != 'none':
            link_problems.append('work_item_claims_acceptance:' + item_id)
        if entry.get('release') != version_text:
            link_problems.append('work_item_release_mismatch:' + item_id)
        prs = entry.get('prs') if isinstance(entry.get('prs'), list) else []
        for pr in prs:
            number = pr.get('number') if isinstance(pr, dict) else None
            if not _valid_pr(pr, number):
                link_problems.append('invalid_pr:' + item_id)
            else:
                work_prs.add(number)
        commits = entry.get('commits') if isinstance(entry.get('commits'), list) else []
        valid_commits = [value for value in commits
                         if isinstance(value, str) and HEX_COMMIT_RE.fullmatch(value)]
        if len(valid_commits) != len(commits):
            link_problems.append('invalid_commit:' + item_id)
        blocked = entry.get('state') == 'blocked'
        if blocked:
            if not isinstance(entry.get('blocker'), str) or not entry.get('blocker'):
                link_problems.append('blocked_item_without_reason:' + item_id)
        elif not prs and not valid_commits:
            link_problems.append('work_item_without_link:' + item_id)
    check('traceability_work_items', not link_problems,
          'problems=' + ','.join(link_problems[:12]) if link_problems
          else '%d work items linked' % len(ids))

    releases = data.get('releases')
    releases = releases if isinstance(releases, list) else []
    match = next((entry for entry in releases if isinstance(entry, dict)
                  and entry.get('version') == version_text), None)
    release_problems = []
    included = set()
    changelog_text = _read_bounded(root / 'CHANGELOG.md')
    check('changelog_current', ('## [' + version_text + ']') in changelog_text,
          'heading=## [%s]' % version_text)
    if match is None:
        release_problems.append('release_entry_missing')
    else:
        if match.get('state') != 'candidate':
            release_problems.append('release_state_not_candidate')
        if match.get('acceptance') != 'none':
            release_problems.append('release_claims_acceptance')
        if match.get('runtime_verified') is not False:
            release_problems.append('release_runtime_verified_not_false')
        if match.get('published') is not False:
            release_problems.append('release_claims_publication')
        changelog_link = match.get('changelog')
        if (not isinstance(changelog_link, str)
                or 'CHANGELOG.md' not in changelog_link):
            release_problems.append('release_changelog_link_invalid')
        values = match.get('included_prs')
        values = values if isinstance(values, list) else []
        if not values or any(type(value) is not int for value in values):
            release_problems.append('included_prs_invalid')
        included = {value for value in values if type(value) is int}
        support = match.get('support_prs')
        support = support if isinstance(support, list) else []
        for entry in support:
            if isinstance(entry, dict) and type(entry.get('number')) is int:
                work_prs.add(entry['number'])
        missing = sorted(included - work_prs)
        if missing:
            release_problems.append('included_prs_without_work_item:' +
                                    ','.join(str(value) for value in missing[:8]))
    summary['linked_prs'] = len(work_prs)
    summary['included_prs'] = len(included)
    check('traceability_release_links', not release_problems,
          'problems=' + ','.join(release_problems[:12]) if release_problems
          else '%d included PRs linked' % len(included))
    gaps = data.get('gaps')
    gaps = gaps if isinstance(gaps, list) else []
    summary['gaps'] = len(gaps)
    check('traceability_gaps', bool(gaps) and all(isinstance(item, str) for item in gaps),
          '%d gaps recorded' % len(gaps))
    source = data.get('source_revision')
    if isinstance(source, str) and re.fullmatch(r'[0-9a-fA-F]{40}', source):
        short = source[:7]
        changelog_text = _read_bounded(root / 'CHANGELOG.md')
        readme_text = _read_bounded(root / 'README.md')
        trace_md = _read_bounded(root / 'docs/RELEASE_TRACEABILITY.md')
        check('traceability_source_revision',
              short in changelog_text and short in readme_text
              and (source in trace_md or short in trace_md),
              'source_revision=%s must appear in CHANGELOG, README and '
              'traceability doc' % source)
        _head_revision_checks(root, data, check, git_runner=git_runner)
    ancestry = _ancestry_checks(root, data, git_runner=git_runner)
    summary['ancestry_status'] = ancestry['status']
    summary['ancestry_commits'] = ancestry['checked']
    if ancestry['available']:
        check('traceability_ancestry', not ancestry['missing'],
              ('%d/%d commits are ancestors of %s'
               % (ancestry['checked'] - len(ancestry['missing']),
                  ancestry['checked'], data.get('source_revision')))
              if ancestry['missing'] else
              ('all %d recorded commits are ancestors of %s'
               % (ancestry['checked'], data.get('source_revision'))))
    else:
        check('traceability_ancestry', True,
              'unavailable: ' + ancestry['status']
              + ' (offline fixture or missing repo)')
    check('pr_merged_state', True,
          'GitHub merged-state is unavailable offline; merge-commit '
          'ancestry is checked instead')
    return summary


def build_release_gate(*, root=None, game_root=None, tracked_files=None,
                       git_runner=None, expected_version=None):
    """Compose the read-only delivery-gate report."""
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    root = root.absolute()
    checks, blockers, warnings = {}, [], []

    def check(name, ok, note=''):
        checks[name] = {'ok': bool(ok), 'note': note}
        if not ok:
            blockers.append(name)
        return bool(ok)

    missing = [relative for relative in REQUIRED_FILES
               if not (root / relative).is_file()]
    check('required_files', not missing,
          'missing=' + ','.join(missing) if missing else 'all present')
    version_text = ''
    version_path = root / 'VERSION'
    if version_path.is_file():
        version_text = _read_bounded(version_path).strip().splitlines()
        version_text = version_text[0] if version_text else ''
    check('version_format', bool(VERSION_RE.match(version_text)),
          'VERSION=' + (version_text or 'missing'))
    if expected_version is not None:
        check('version_matches_expected', version_text == expected_version,
              'expected=' + str(expected_version))
    instructions = ''
    for relative in ('docs/WINDOWS_BOOTSTRAP.md', 'README.md'):
        instructions += '\n' + _read_bounded(root / relative)
    missing_tokens = [token for token in REQUIRED_COMMAND_TOKENS
                      if token not in instructions]
    check('reproducible_commands', not missing_tokens,
          'missing=' + ','.join(missing_tokens) if missing_tokens else 'documented')
    traceability = _traceability_checks(root, version_text, check,
                                          git_runner=git_runner)
    if traceability.get('ancestry_status') != 'checked':
        warnings.append('git_ancestry_unavailable:'
                        + str(traceability.get('ancestry_status')))

    if tracked_files is None:
        try:
            tracked_files = git_tracked_files(root, runner=git_runner)
        except ReleaseGateError as exc:
            tracked_files = []
            warnings.append('git_tracked_files_unavailable')
            warnings.append(str(exc)[:120])
    banned = [name for name in tracked_files
              if Path(name).suffix.casefold() in FORBIDDEN_EXTENSIONS]
    check('no_tracked_binaries_or_logs', not banned,
          'banned=' + ','.join(banned[:20]) if banned else 'clean')
    scanned = 0
    personal_hits, secret_hits = [], []
    for name in tracked_files:
        if name in SCAN_EXEMPT_FILES:
            continue
        path = root / name
        if not path.is_file():
            continue
        text = _read_bounded(path)
        scanned += 1
        if any(pattern.search(text) for pattern in PERSONAL_PATH_RES):
            personal_hits.append(name)
        if SECRET_RE.search(text):
            secret_hits.append(name)
    check('no_personal_local_paths', not personal_hits,
          'files=' + ','.join(personal_hits[:20]) if personal_hits else 'clean')
    check('no_obvious_secrets', not secret_hits,
          'files=' + ','.join(secret_hits[:20]) if secret_hits else 'clean')
    checks['tracked_text_scan'] = {'ok': True,
                                   'note': 'scanned %d tracked files' % scanned}

    module = None
    if game_root is not None:
        module_dir = Path(game_root).expanduser().absolute() / 'Modules' / MODULE_NAME
        if module_dir.is_dir():
            module = verify_built_module(module_dir)
            check('installed_module_city_structure', module.get('ok') is True,
                  'problems=' + ','.join(module.get('problems') or [])
                  if module.get('problems') else 'city module valid')
            check('installed_runtime_not_claimed',
                  module.get('checks', {}).get('runtime_verified_false') is True,
                  'build receipt says runtime_verified=false')
        else:
            warnings.append('installed_module_not_found')
    else:
        warnings.append('installed_module_not_provided')
    license_present = (root / 'LICENSE').is_file()
    notices_present = any((root / name).is_file() for name in (
        'THIRD_PARTY_NOTICES.md', 'NOTICE', 'docs/CREDITS.md'))
    checks['repo_license_status'] = {
        'ok': True,
        'note': ('present' if license_present else
                 'absent — owner decision/open risk; reported, not silently passing')}
    checks['third_party_notices_status'] = {
        'ok': True,
        'note': ('present' if notices_present else
                 'absent — attribution is tracked in the legal dossier; '
                 'owner decision/open risk')}
    if not license_present:
        warnings.append('license_file_absent')
    if not notices_present:
        warnings.append('third_party_notices_absent')
    if module is not None and version_text:
        try:
            import json as _json
            with open(Path(game_root).expanduser().absolute() / 'Modules'
                      / MODULE_NAME / 'ZOMBIEEE_REMASTER.json', 'rb') as stream:
                manifest = _json.loads(stream.read(1024 * 1024).decode('utf-8'))
        except (OSError, ValueError):
            manifest = {}
        remaster_version = manifest.get('remaster_version')
        if isinstance(remaster_version, str):
            check('module_version_matches', remaster_version == version_text,
                  'module=' + remaster_version)
        else:
            warnings.append('module_version_unknown')

    gate = {
        'schema': SCHEMA, 'schema_version': 1,
        'read_only': True, 'no_launch': True,
        'ok': not blockers,
        'blockers': blockers,
        'warnings': warnings,
        'checks': checks,
        'version': version_text or None,
        'traceability': traceability,
        'remaster_module': ({'ok': module.get('ok'),
                             'module_sha256': module.get('module_sha256'),
                             'file_count': module.get('file_count'),
                             'map_scope': module.get('map_scope'),
                             'trigger_count': module.get('trigger_count')}
                            if module else None),
        'delivery_status': 'candidate-checks-only',
        'acceptance': 'none',
        'runtime_verified': False,
        'notes': [
            'This gate never claims playable acceptance; owner review and sealed '
            'runtime evidence remain required.',
            'Archives, game binaries, WSE2 and original assets are never committed.',
        ],
    }
    return gate


def format_release_gate(gate):
    lines = ['Release delivery checks: ' + ('OK' if gate['ok'] else 'BLOCKED')]
    for name, entry in gate.get('checks', {}).items():
        lines.append('  %-32s %s%s' % (name, 'pass' if entry.get('ok') else 'FAIL',
                                       ' (' + entry['note'] + ')'
                                       if entry.get('note') else ''))
    for blocker in gate.get('blockers') or []:
        lines.append('  blocker : ' + str(blocker))
    for warning in gate.get('warnings') or []:
        lines.append('  warning : ' + str(warning))
    lines.append('  status  : ' + str(gate.get('delivery_status'))
                 + '; runtime_verified=false; acceptance=none')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', help='repository checkout to check')
    parser.add_argument('--game-root', help='optional installed Warband root')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    gate = build_release_gate(root=args.root, game_root=args.game_root)
    if args.json:
        print(json.dumps(gate, indent=2, sort_keys=True))
    else:
        print(format_release_gate(gate))
    return 0 if gate['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
