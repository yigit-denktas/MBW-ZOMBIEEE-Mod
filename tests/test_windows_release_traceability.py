"""Release traceability + SemVer candidate tests (no game launch).

The real repository metadata is checked read-only; mutated temporary fixtures
prove the release gate fails closed on missing/mismatched links.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.release_gate import SCAN_EXEMPT_FILES, build_release_gate  # noqa: E402

VERSION = '0.3.0-beta.1'
WORK_ITEM = {
    'id': 'ZOM-WIN-02', 'title': 'fixture', 'lane': 'B', 'state': 'active',
    'acceptance': 'none', 'release': VERSION, 'summary': 'fixture',
    'prs': [{'number': 28,
             'url': 'https://github.com/example/repo/pull/28',
             'merge_commit': '8e7849b2e32cf95cafacd24ba3535c1679a5edc9'}],
    'commits': ['579b446292b335656595e776049d6f36bb4b581c'],
}
BASE_TRACE = {
    'schema': 'zombieee.release-traceability.v1', 'schema_version': 1,
    'candidate_version': VERSION, 'release_state': 'candidate',
    'acceptance': 'none', 'runtime_verified': False,
    'work_items': [WORK_ITEM],
    'releases': [{
        'version': VERSION, 'state': 'candidate',
        'changelog': 'CHANGELOG.md#030-beta1-2026-10-24',
        'acceptance': 'none', 'runtime_verified': False, 'published': False,
        'included_prs': [28],
    }],
    'gaps': ['fixture runtime gap'],
}


def build_fixture_repo(root, *, version=VERSION, trace=None, changelog=None):
    if trace is None:
        trace = copy.deepcopy(BASE_TRACE)
        trace['candidate_version'] = version
        for item in trace.get('work_items', []):
            item['release'] = version
        for release in trace.get('releases', []):
            release['version'] = version
    else:
        trace = copy.deepcopy(trace)
    files = {
        'VERSION': version + '\n',
        'README.md': 'python -m launcher.play_city; tools/build.py; '
                     'archive_audit\n',
        'CHANGELOG.md': ('# Changelog\n\n## [' + version + '] - 2026-10-24\n'
                         if changelog is None else changelog),
        'docs/WINDOWS_BOOTSTRAP.md': 'python -m launcher.play_city; '
                                     'tools/build.py; archive_audit\n',
        'docs/PROVENANCE.md': 'provenance\n',
        'docs/RELEASE_TRACEABILITY.md': 'traceability table ' + version + '\n',
        'docs/release-traceability.json': json.dumps(trace, indent=2) + '\n',
        'launcher/play_city.py': 'pass\n',
        'launcher/control_panel.py': 'pass\n',
        'launcher/install.py': 'pass\n',
        'launcher/maintenance.py': 'pass\n',
        'reference/LEGAL_RIGHTS_AND_CREDITS.md': 'legal dossier\n',
        'reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md':
            'independent review record\n',
        'installer/manifest.py': 'pass\n',
        'tools/build.py': 'pass\n',
        'tools/archive_audit.py': 'pass\n',
    }
    for relative, content in files.items():
        path = Path(root) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    return list(files)


class RepositoryTraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.version = (REPO / 'VERSION').read_text(encoding='utf-8').strip()
        self.trace = json.loads(
            (REPO / 'docs/release-traceability.json').read_text(encoding='utf-8'))

    def test_candidate_metadata_is_internally_consistent(self):
        self.assertEqual(self.trace['schema'], 'zombieee.release-traceability.v1')
        self.assertEqual(self.trace['candidate_version'], self.version)
        self.assertEqual(self.trace['release_state'], 'candidate')
        self.assertEqual(self.trace['acceptance'], 'none')
        self.assertIs(self.trace['runtime_verified'], False)
        changelog = (REPO / 'CHANGELOG.md').read_text(encoding='utf-8')
        self.assertIn('## [' + self.version + ']', changelog)
        readme = (REPO / 'README.md').read_text(encoding='utf-8')
        self.assertIn(self.version, readme)
        self.assertIn('RELEASE_TRACEABILITY', readme)
        roadmap = (REPO / 'docs/ROADMAP.md').read_text(encoding='utf-8')
        self.assertIn('0.3.0-beta.1', roadmap)
        self.assertIn('does not award', roadmap)
        # Every non-blocked work item links a PR and/or commit; blocked explains.
        ids = set()
        for item in self.trace['work_items']:
            self.assertRegex(item['id'], r'^ZOM-[A-Z]+-\d+$')
            self.assertNotIn(item['id'], ids)
            ids.add(item['id'])
            self.assertEqual(item['acceptance'], 'none')
            self.assertEqual(item['release'], self.version)
            if item['state'] == 'blocked':
                self.assertTrue(item.get('blocker'))
            else:
                self.assertTrue(item.get('prs') or item.get('commits'), item['id'])
            for pr in item.get('prs', []):
                self.assertEqual(pr['url'],
                                 'https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/'
                                 + str(pr['number']))
                self.assertRegex(pr['merge_commit'], r'^[0-9a-f]{40}$')
        # Ledger IDs exist for every linked work item.
        ledger = json.loads((REPO / 'progress/ledger.json').read_text(
            encoding='utf-8'))
        ledger_ids = {entry['id'] for entry in ledger['items']}
        self.assertTrue(ids.issubset(ledger_ids), ids - ledger_ids)
        # Release links are covered and no acceptance/publication is claimed.
        release = self.trace['releases'][0]
        self.assertEqual(release['version'], self.version)
        self.assertEqual(release['acceptance'], 'none')
        self.assertIs(release['runtime_verified'], False)
        self.assertIs(release['published'], False)
        support = {entry['number'] for entry in release.get('support_prs', [])}
        work_prs = {pr['number'] for item in self.trace['work_items']
                    for pr in item.get('prs', [])}
        self.assertEqual(set(release['included_prs']) - work_prs - support, set())
        self.assertRegex(self.trace['source_revision'], r'^[0-9a-f]{40}$')
        support = {entry['id']: entry for entry in self.trace['support_artifacts']}
        self.assertEqual(set(support),
                         {'C-TASK-35', 'C-TASK-48', 'G-TASK-49',
                          'H-TASK-58'})
        self.assertIs(support['G-TASK-49']['merged'], True)
        self.assertIn('merged', support['G-TASK-49']['state'])
        self.assertEqual(support['G-TASK-49']['merge_commit'],
                         '8b38f7deed9711e36d11ab005eb8e8b269dc525d')
        self.assertEqual(support['G-TASK-49']['pr']['number'], 31)
        self.assertIn('no binaries', support['G-TASK-49']['summary'])
        self.assertIn('NOT a runtime/telemetry artifact',
                      support['C-TASK-48']['summary'])
        self.assertIs(support['C-TASK-48']['merged'], True)
        self.assertEqual(support['C-TASK-48']['merge_commit'],
                         '7bf941cd2dbcdca95e68a3c31652ce5c7870147d')
        self.assertIn('50fa25b', support['C-TASK-48']['commits'])
        self.assertEqual(self.trace['version_decision']['candidate'], self.version)
        self.assertIn('0.3.0 milestone', self.trace['version_decision']['milestone_awarded'])
        self.assertEqual(self.trace['version_decision']['owner_approval'], 'pending')
        self.assertEqual(self.trace['reviews'][0]['reviewer'], 'Agent E')
        self.assertEqual(self.trace['reviews'][0]['acceptance'], 'none')
        self.assertTrue((REPO / self.trace['reviews'][0]['record']).is_file())
        self.assertTrue(self.trace['gaps'])
        # The real checkout passes the release gate: strict, no tolerance.
        gate = build_release_gate(root=REPO)
        self.assertTrue(gate['ok'], gate['blockers'])
        self.assertEqual(gate['acceptance'], 'none')
        self.assertIs(gate['runtime_verified'], False)
        self.assertEqual(gate['traceability']['candidate_version'], self.version)
        self.assertGreaterEqual(gate['traceability']['work_items'], 10)
        self.assertGreaterEqual(gate['traceability']['included_prs'], 10)
        self.assertIn('absent', gate['checks']['repo_license_status']['note'])
        self.assertIn('absent', gate['checks']['third_party_notices_status']['note'])
        self.assertIn('license_file_absent', gate['warnings'])
        self.assertEqual(gate['traceability']['ancestry_status'], 'checked')
        self.assertTrue(gate['checks']['traceability_ancestry']['ok'])
        self.assertGreaterEqual(gate['traceability']['ancestry_commits'], 20)


class GateFailClosedTests(unittest.TestCase):
    def _gate(self, root):
        tracked = build_fixture_repo(root)
        return build_release_gate(root=root, tracked_files=tracked)

    def test_version_mismatch_between_record_and_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = copy.deepcopy(BASE_TRACE)
            trace['candidate_version'] = '0.3.0-rc.2'
            tracked = build_fixture_repo(tmp, trace=trace)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('traceability_version', gate['blockers'])

    def test_work_item_without_link_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = copy.deepcopy(BASE_TRACE)
            trace['work_items'][0]['prs'] = []
            trace['work_items'][0]['commits'] = []
            tracked = build_fixture_repo(tmp, trace=trace)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('traceability_work_items', gate['blockers'])

    def test_acceptance_or_publication_claim_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = copy.deepcopy(BASE_TRACE)
            trace['acceptance'] = 'owner-accepted'
            trace['releases'][0]['acceptance'] = 'owner-accepted'
            trace['releases'][0]['published'] = True
            tracked = build_fixture_repo(tmp, trace=trace)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('traceability_state', gate['blockers'])
            self.assertIn('traceability_release_links', gate['blockers'])

    def test_stale_changelog_or_missing_gaps_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked = build_fixture_repo(tmp, changelog='# Changelog\n')
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('changelog_current', gate['blockers'])
        with tempfile.TemporaryDirectory() as tmp:
            trace = copy.deepcopy(BASE_TRACE)
            trace['gaps'] = []
            tracked = build_fixture_repo(tmp, trace=trace)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('traceability_gaps', gate['blockers'])

    def test_unlinked_included_pr_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = copy.deepcopy(BASE_TRACE)
            trace['releases'][0]['included_prs'] = [28, 999]
            tracked = build_fixture_repo(tmp, trace=trace)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('traceability_release_links', gate['blockers'])

    def test_privacy_scan_catches_leaks_outside_exact_exemptions(self):
        cases = {
            'tests/new_leak_fixture.py': 'C:/Users/Alice/private.txt',
            'docs/path_note.md': '/home/alice/private',
            'docs/escaped_path_note.md':
                r'C:\\Users\\Alice\\ZOMBIEEE',
            'docs/mixed_path_note.md': 'C:\\Users/Alice/ZOMBIEEE',
            'docs/mixed_path_note2.md': 'C:/Users\\Alice\\ZOMBIEEE',
            'docs/manifest.json': json.dumps({
                'game_root': 'C:\\Users\\Alice\\ZOMBIEEE'}),
            'reference/unc_note.md': r'\\fileserver\private\share',
            'docs/url_note.md': 'file:///C:/private/log.txt',
            'docs/token_note.md': 'ghp_' + 'a' * 30,
        }
        for relative, content in cases.items():
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as tmp:
                    tracked = build_fixture_repo(tmp)
                    path = Path(tmp) / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content + '\n', encoding='utf-8')
                    tracked.append(relative)
                    gate = build_release_gate(root=tmp, tracked_files=tracked)
                    expected = ('no_obvious_secrets' if 'ghp_' in content
                                else 'no_personal_local_paths')
                    self.assertIn(expected, gate['blockers'])
        # Exact documented exemptions remain explicit (fixture path privacy files).
        with tempfile.TemporaryDirectory() as tmp:
            tracked = build_fixture_repo(tmp)
            path = Path(tmp) / 'tests/test_diagnostics.py'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(r'FIXTURE = "C:\Users\Alice\x.rar"' + '\n',
                            encoding='utf-8')
            tracked.append('tests/test_diagnostics.py')
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertNotIn('no_personal_local_paths', gate['blockers'])

    def test_privacy_scan_ignores_non_personal_path_fragments(self):
        # Regression: a genuine UNC share is flagged, but the same shape must
        # not be invented inside an escaped drive path ("C:\\x\\record") or a
        # placeholder-relative suffix ("<warband-root>\\Logs\\..."). The JSON
        # fixture below is the real one from test_flight_receipt_summary, which
        # must stay inside the scanned set - no exemption may hide it.
        fragments = {
            'docs/escaped_drive_note.json':
                json.dumps({'sha256': {'C:\\x\\recorder.json': '0' * 64}}),
            'docs/drive_relative_note.md': r'D:\\games\\logs\\rgl_log.txt',
            'docs/escaped_placeholder_note.md':
                '<warband-root>\\\\Logs\\\\rgl_log.txt',
            'docs/placeholder_note.md':
                '<warband-root>\\Logs\\rgl_log.txt',
        }
        for relative, content in fragments.items():
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as tmp:
                    tracked = build_fixture_repo(tmp)
                    path = Path(tmp) / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content + '\n', encoding='utf-8')
                    tracked.append(relative)
                    gate = build_release_gate(root=tmp, tracked_files=tracked)
                    self.assertNotIn('no_personal_local_paths',
                                     gate['blockers'], content)
        self.assertNotIn('tests/test_flight_receipt_summary.py',
                         SCAN_EXEMPT_FILES)

    def test_git_ancestry_fails_closed_on_stale_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked = build_fixture_repo(tmp)
            subprocess.run(['git', '-C', tmp, 'init'], check=True,
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', tmp, 'config', 'user.email',
                            'fixture@example.invalid'], check=True,
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', tmp, 'config', 'user.name',
                            'fixture'], check=True, capture_output=True,
                           text=True)
            subprocess.run(['git', '-C', tmp, 'add', '-A'], check=True,
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', tmp, 'commit', '-m', 'fixture'],
                           check=True, capture_output=True, text=True)
            head = subprocess.run(
                ['git', '-C', tmp, 'rev-parse', 'HEAD'], check=True,
                capture_output=True, text=True).stdout.strip()
            trace_path = Path(tmp) / 'docs/release-traceability.json'
            trace = json.loads(trace_path.read_text(encoding='utf-8'))
            trace['source_revision'] = head
            trace['work_items'][0]['commits'] = ['f' * 40]
            trace_path.write_text(json.dumps(trace), encoding='utf-8')
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('traceability_ancestry', gate['blockers'])
            self.assertTrue(gate['traceability']['ancestry_status'], 'failed')

    def test_pending_asset_artifact_is_not_claimed_as_shipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked = build_fixture_repo(tmp)
            trace_path = Path(tmp) / 'docs/release-traceability.json'
            trace = json.loads(trace_path.read_text(encoding='utf-8'))
            trace['support_artifacts'] = [{
                'id': 'G-TASK-49', 'kind': 'docs-definitions-only',
                'state': 'pending-merge', 'merged': False,
                'summary': 'docs-only fixture, no binaries',
                'commits': ['85b9c0b'], 'merge_commit': None}]
            trace_path.write_text(json.dumps(trace), encoding='utf-8')
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertNotIn('traceability_ancestry', gate['blockers'])
            self.assertIn('unavailable', gate['checks']['traceability_ancestry']['note'])

    def test_docs_credits_is_accepted_as_notice_alternative(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked = build_fixture_repo(tmp)
            credits = Path(tmp) / 'docs/CREDITS.md'
            credits.write_text('third-party credits register\n', encoding='utf-8')
            tracked.append('docs/CREDITS.md')
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('present',
                          gate['checks']['third_party_notices_status']['note'])

    def test_ancestry_unavailable_is_a_warning_not_a_false_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked = build_fixture_repo(tmp)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertTrue(gate['checks']['traceability_ancestry']['ok'])
            self.assertIn('unavailable', gate['checks']['traceability_ancestry']['note'])
            self.assertTrue(any(item.startswith('git_ancestry_unavailable')
                                for item in gate['warnings']))

    def test_source_revision_head_exception_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked = build_fixture_repo(tmp)
            subprocess.run(['git', '-C', tmp, 'init'], check=True,
                           capture_output=True, text=True)
            for key, value in (('user.email', 'fixture@example.invalid'),
                               ('user.name', 'fixture')):
                subprocess.run(['git', '-C', tmp, 'config', key, value],
                               check=True, capture_output=True, text=True)
            subprocess.run(['git', '-C', tmp, 'add', '-A'], check=True,
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', tmp, 'commit', '-m', 'base'], check=True,
                           capture_output=True, text=True)
            base = subprocess.run(['git', '-C', tmp, 'rev-parse', 'HEAD'],
                                  check=True, capture_output=True,
                                  text=True).stdout.strip()
            trace_path = Path(tmp) / 'docs/release-traceability.json'
            trace = json.loads(trace_path.read_text(encoding='utf-8'))
            trace['source_revision'] = base
            trace_path.write_text(json.dumps(trace), encoding='utf-8')
            subprocess.run(['git', '-C', tmp, 'add', '-A'], check=True,
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', tmp, 'commit', '-m', 'metadata'],
                           check=True, capture_output=True, text=True)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('traceability_head_revision', gate['blockers'])
            trace['source_revision_exception'] = {
                'kind': 'metadata', 'reason': 'metadata-only test branch'}
            trace_path.write_text(json.dumps(trace), encoding='utf-8')
            subprocess.run(['git', '-C', tmp, 'add', '-A'], check=True,
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', tmp, 'commit', '-m', 'exception'],
                           check=True, capture_output=True, text=True)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertNotIn('traceability_head_revision', gate['blockers'])
            code_path = Path(tmp) / 'launcher/play_city.py'
            code_path.write_text('def main():\n    return 0\n', encoding='utf-8')
            subprocess.run(['git', '-C', tmp, 'add', '-A'], check=True,
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', tmp, 'commit', '-m', 'code'], check=True,
                           capture_output=True, text=True)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('traceability_head_revision', gate['blockers'])

    def test_semver_candidate_and_malformed_versions(self):
        for version in ('0.3.0-beta.1', '0.3.0', '0.3.0-rc.2+build.5'):
            with tempfile.TemporaryDirectory() as tmp:
                tracked = build_fixture_repo(tmp, version=version)
                gate = build_release_gate(root=tmp, tracked_files=tracked)
                self.assertTrue(gate['checks']['version_format']['ok'], version)
                self.assertNotIn('traceability_version', gate['blockers'])
        for version in ('0.3', 'v0.3.0', '0.3.0.1', ''):
            with tempfile.TemporaryDirectory() as tmp:
                tracked = build_fixture_repo(tmp, version=version)
                gate = build_release_gate(root=tmp, tracked_files=tracked)
                self.assertFalse(gate['checks']['version_format']['ok'], version)
                self.assertIn('version_format', gate['blockers'])


if __name__ == '__main__':
    unittest.main()
