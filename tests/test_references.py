"""Independent byte-mutation and failed-query controls for reference auditing."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('references', Path(__file__).resolve().parents[1] / 'scripts/check_references.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
COMMIT = 'a' * 40
ORIGINAL = b'{"released":true}\n'


class Authority:
    def revision(self, repo, ref, kind):
        return COMMIT

    def read(self, repo, commit, name):
        if name == audit.CONTROL:
            raise audit.Missing(name)
        return ORIGINAL


class ReferenceTests(unittest.TestCase):
    def row(self, cls='released-contract'):
        return {'id': 'test', 'consumer': 'owner/consumer', 'class': cls,
                'repository': 'owner/authority', 'revision': COMMIT if cls == 'draft-contract' else 'v1.0.0',
                'revisionKind': 'commit' if cls == 'draft-contract' else 'tag',
                'materialStatus': 'released', 'commit': COMMIT,
                'files': [{'path': 'schema.json', 'local': 'copy.json',
                           'sha256': hashlib.sha256(ORIGINAL).hexdigest()}]}

    def test_all_five_classes_resolve_actual_bytes(self):
        for cls in audit.CLASSES:
            with self.subTest(cls=cls):
                result = audit.audit(self.row(cls), Authority())
                self.assertEqual(result['verdict'], 'FRESH')
                self.assertEqual(result['negativeControl'], 'confirmed-missing')
                self.assertEqual(result['localComparison'], 'not-run')

    def test_wrong_recorded_digest_is_drift(self):
        changed = ORIGINAL.replace(b'true', b'false')
        self.assertNotEqual(changed, ORIGINAL)
        row = self.row()
        row['files'][0]['sha256'] = hashlib.sha256(changed).hexdigest()
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'DRIFT')

    def test_actual_local_mutation_is_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'copy.json').write_bytes(ORIGINAL)
            self.assertEqual(audit.audit(self.row(), Authority(), root)['verdict'], 'FRESH')
            (root / 'copy.json').write_bytes(ORIGINAL + b' ')
            self.assertEqual(audit.audit(self.row(), Authority(), root)['verdict'], 'DRIFT')

    def test_missing_authority_differs_from_failed_query(self):
        class MissingFile(Authority):
            def read(self, repo, commit, name):
                raise audit.Missing(name)
        class FailedQuery(Authority):
            def read(self, repo, commit, name):
                if name == audit.CONTROL:
                    raise audit.Missing(name)
                raise audit.QueryFailed('HTTP 503')
        self.assertEqual(audit.audit(self.row(), MissingFile())['verdict'], 'ABSENT')
        self.assertEqual(audit.audit(self.row(), FailedQuery())['verdict'], 'QUERY_FAILED')

    def test_failed_control_is_not_an_absence_or_pass(self):
        class Permissive(Authority):
            def read(self, *args):
                return ORIGINAL
        class Offline(Authority):
            def read(self, *args):
                raise audit.QueryFailed('timeout')
        for resolver in (Permissive(), Offline()):
            self.assertEqual(audit.audit(self.row(), resolver)['verdict'], 'QUERY_FAILED')

    def test_empty_measurement_refuses_pass(self):
        class Empty(Authority):
            def read(self, repo, commit, name):
                if name == audit.CONTROL:
                    raise audit.Missing(name)
                return b''
        self.assertEqual(audit.audit(self.row(), Empty())['verdict'], 'QUERY_FAILED')

    def test_tag_commit_mismatch(self):
        row = self.row()
        row['commit'] = 'b' * 40
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'DRIFT')

    def test_released_main_fails_even_when_bytes_match(self):
        row = self.row()
        row.update(revision='main', revisionKind='branch')
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'DRIFT')

    def test_duplicate_paths_and_missing_digest_are_not_passes(self):
        row = self.row('copied-tree')
        row['files'].append(copy.deepcopy(row['files'][0]))
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'DRIFT')
        row = self.row()
        row['files'][0]['sha256'] = None
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'ABSENT')


class IdentityTests(unittest.TestCase):
    def test_frozen_identity_exception_is_exact_bytes_only(self):
        module_spec = importlib.util.spec_from_file_location('identity', Path(__file__).resolve().parents[1] / 'scripts/check_contract_identity.py')
        identity = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(identity)
        legacy = b'{"$id":"https://example.org/main/fhr.json"}'
        ledger = {'artifacts': [{'path': 'fhr.json', 'sha256': hashlib.sha256(legacy).hexdigest()}]}
        self.assertEqual(identity.check(legacy, 'fhr.json', ledger)[0], 'preserved-release')
        self.assertEqual(identity.check(legacy + b' ', 'fhr.json', ledger)[0], 'refused')
        self.assertEqual(identity.check(legacy, 'other.json', ledger)[0], 'refused')
        candidate = b'{"$id":"https://w3id.org/fair-bioheaders/fhr/v0.9.0"}'
        self.assertEqual(identity.check(candidate, 'fhr.json', ledger)[0], 'stable-identity-candidate')


class TreeSetTests(unittest.TestCase):
    row = ReferenceTests.row

    def test_added_authority_path_is_detected_without_digest_change(self):
        class ExtraSource(Authority):
            def paths(self, repo, commit):
                return {'schema.json', 'new-schema.json'}
        row = self.row('copied-tree')
        row['sourcePatterns'] = ['*.json']
        result = audit.audit(row, ExtraSource())
        self.assertEqual(result['verdict'], 'DRIFT')
        self.assertEqual(result['onlyAuthority'], ['new-schema.json'])
        self.assertEqual(result['files'][0]['verdict'], 'FRESH')

    def test_unrecorded_local_path_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'tree').mkdir()
            (root / 'tree/copy.json').write_bytes(ORIGINAL)
            (root / 'tree/unrecorded.json').write_bytes(ORIGINAL)
            row = self.row('copied-tree')
            row['files'][0]['local'] = 'tree/copy.json'
            row['localTree'] = 'tree'
            result = audit.audit(row, Authority(), root)
            self.assertEqual(result['verdict'], 'DRIFT')
            self.assertEqual(result['onlyLocal'], ['tree/unrecorded.json'])

    def test_exact_source_exclusion_does_not_hide_an_omitted_source_file(self):
        class Selected(Authority):
            def paths(self, *args):
                return {'schema.json', 'AGENTS.md', 'omitted.json'}
        row = self.row('copied-tree')
        row['sourcePatterns'] = ['*']
        row['sourceExclusions'] = ['AGENTS.md']
        result = audit.audit(row, Selected())
        self.assertEqual(result['verdict'], 'DRIFT')
        self.assertEqual(result['onlyAuthority'], ['omitted.json'])
        self.assertEqual(result['excludedAuthorityPaths'], ['AGENTS.md'])
        row['files'].append({'path': 'omitted.json', 'sha256': hashlib.sha256(ORIGINAL).hexdigest()})
        self.assertEqual(audit.audit(row, Selected())['verdict'], 'FRESH')

    def test_nonexistent_or_invalid_exclusions_are_not_fresh(self):
        class Selected(Authority):
            def paths(self, *args):
                return {'schema.json'}
        for exclusions in (['typo.md'], ['AGENTS.md', 'AGENTS.md'], 'AGENTS.md'):
            row = self.row('copied-tree')
            row.update(sourcePatterns=['*'], sourceExclusions=exclusions)
            self.assertEqual(audit.audit(row, Selected())['verdict'], 'DRIFT')

    def test_missing_only_authority_or_local_paths_remain_absent(self):
        class MissingAuthority(Authority):
            def read(self, repo, commit, name):
                raise audit.Missing(name)
            def paths(self, *args):
                return set()
        row = self.row('copied-tree')
        row['sourcePatterns'] = ['*.json']
        result = audit.audit(row, MissingAuthority())
        self.assertEqual(result['verdict'], 'ABSENT')
        self.assertEqual(result['onlyRecord'], ['schema.json'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'tree').mkdir()
            row['files'][0]['local'] = 'tree/copy.json'
            row['localTree'] = 'tree'
            # The authority has the recorded file; only its local copy is absent.
            class Complete(Authority):
                def paths(self, *args):
                    return {'schema.json'}
            result = audit.audit(row, Complete(), root)
            self.assertEqual(result['verdict'], 'ABSENT')
            self.assertEqual(result['missingLocal'], ['tree/copy.json'])
            (root / 'tree/unexpected.json').write_bytes(ORIGINAL)
            self.assertEqual(audit.audit(row, Complete(), root)['verdict'], 'DRIFT')

    def test_existing_record_outside_selected_scope_is_drift_not_missing(self):
        class DifferentSelection(Authority):
            def paths(self, *args):
                return {'schema.json'}
        row = self.row('copied-tree')
        row['sourcePatterns'] = ['selected-only/*']
        self.assertEqual(audit.audit(row, DifferentSelection())['verdict'], 'DRIFT')


class RemoteFailureTests(unittest.TestCase):
    row = ReferenceTests.row

    def test_revision_404_requires_independent_access_and_control(self):
        class MissingRevision(Authority):
            def revision(self, *args):
                raise audit.Missing('missing tag')
            def accessible_revision(self, repo):
                return COMMIT
        class Inaccessible(MissingRevision):
            def accessible_revision(self, repo):
                raise audit.QueryFailed('repository access HTTP 404')
        self.assertEqual(audit.audit(self.row(), MissingRevision())['verdict'], 'ABSENT')
        self.assertEqual(audit.audit(self.row(), Inaccessible())['verdict'], 'QUERY_FAILED')

    def test_inaccessible_github_repository_404_is_not_confirmed_absence(self):
        class Hidden(audit.Github):
            def get(self, *args, **kwargs):
                raise audit.Missing('HTTP 404')
        self.assertEqual(audit.audit(self.row(), Hidden())['verdict'], 'QUERY_FAILED')

    def test_malformed_valid_json_commit_shapes_are_query_failures(self):
        for body in ([], {}, None, {'sha': 1}, {'sha': ''}):
            class Malformed(audit.Github):
                def get(self, route, **kwargs):
                    if '/git/ref/tags/' in route:
                        return {'ref': 'refs/tags/v1.0.0'}
                    return body
            with self.subTest(body=body):
                self.assertEqual(audit.audit(self.row(), Malformed())['verdict'], 'QUERY_FAILED')

    def test_malformed_valid_json_tree_shapes_are_query_failures(self):
        for body in ([], {}, {'tree': None}, {'tree': [{}]}, {'tree': [None]}, {'tree': [{'type': [], 'path': 'x'}]}, {'tree': [{'type': 'blob', 'path': None}]}):
            class Malformed(audit.Github, Authority):
                def get(self, *args, **kwargs):
                    return body
                revision = Authority.revision
                read = Authority.read
            row = self.row('copied-tree')
            row['sourcePatterns'] = ['*.json']
            with self.subTest(body=body):
                self.assertEqual(audit.audit(row, Malformed())['verdict'], 'QUERY_FAILED')


class ReleaseIdentityPreflightTests(unittest.TestCase):
    def test_actual_release_preflight_preserves_history_and_refuses_changed_main_identity(self):
        import json
        import shutil
        import subprocess
        import sys
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory)
            (candidate / 'scripts').mkdir()
            (candidate / 'references').mkdir()
            (candidate / 'schemas').mkdir()
            for name in ('check_release.py', 'check_contract_identity.py'):
                shutil.copyfile(root / 'scripts' / name, candidate / 'scripts' / name)
            shutil.copyfile(root / 'references/released-identities.json', candidate / 'references/released-identities.json')
            shutil.copyfile(root / 'schemas/versions.json', candidate / 'schemas/versions.json')
            for name in ('fhr.json', 'fhp.json', 'fhgff3.json'):
                shutil.copyfile(root / name, candidate / name)
            command = [sys.executable, str(candidate / 'scripts/check_release.py'), '--identity-only']
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            target = candidate / 'fhp.json'
            data = json.loads(target.read_text())
            data['description'] = 'New publication candidate bytes with legacy floating identity'
            target.write_text(json.dumps(data))
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn('fhp.json: New or changed published bytes', rejected.stderr)
            data['$id'] = 'https://w3id.org/fair-bioheaders/fhp/v0.9.0'
            target.write_text(json.dumps(data))
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)


class RevisionAndBudgetTests(unittest.TestCase):
    row = ReferenceTests.row

    def test_every_class_refuses_floating_and_unsupported_kinds(self):
        for cls in audit.CLASSES:
            for kind in ('branch', 'unknown', None):
                row = self.row(cls)
                row.update(revision='main', revisionKind=kind)
                self.assertEqual(audit.audit(row, Authority())['verdict'], 'DRIFT')
        row = self.row('draft-contract')
        row.update(revision='v1.0.0', revisionKind='tag')
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'DRIFT')

    def test_released_mirror_needs_tag_and_draft_snapshot_needs_commit(self):
        row = self.row('copied-tree')
        row.update(revision=COMMIT, revisionKind='commit')
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'DRIFT')
        row['materialStatus'] = 'draft'
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'FRESH')
        row.update(revision='v1.0.0', revisionKind='tag')
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'DRIFT')

    def test_missing_tag_commit_is_absent_without_querying_authority(self):
        class NoQuery(Authority):
            def revision(self, *args):
                raise AssertionError('incomplete declarations must not be queried')
        for value in (None, ''):
            row = self.row()
            row['commit'] = value
            self.assertEqual(audit.audit(row, NoQuery())['verdict'], 'ABSENT')
        row = self.row()
        row.pop('commit')
        self.assertEqual(audit.audit(row, NoQuery())['verdict'], 'ABSENT')

    def test_commit_kind_revision_itself_is_a_recorded_commit(self):
        row = self.row('conformance-suite')
        row.update(revision=COMMIT, revisionKind='commit')
        row.pop('commit')
        self.assertEqual(audit.audit(row, Authority())['verdict'], 'FRESH')

    def test_concurrent_identical_requests_share_one_fetch(self):
        import concurrent.futures
        import threading
        class Counted(audit.Github):
            def __init__(self):
                super().__init__()
                self.calls = 0
            def _fetch(self, route, raw=False):
                self.calls += 1
                return ORIGINAL
        resolver = Counted()
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _: resolver.get('same/immutable/object', True), range(100)))
        self.assertEqual(results, [ORIGINAL] * 100)
        self.assertEqual(resolver.calls, 1)

    def test_complete_inventory_request_budget_uses_deduplicated_immutable_reads(self):
        import json
        import urllib.parse
        root = Path(__file__).resolve().parents[1]
        inventory = json.loads((root / 'references/inventory.json').read_text())
        tags = {r['release']: r['commit'] for r in json.loads((root / 'references/released-identities.json').read_text())['artifacts']}
        class Simulation(audit.Github):
            def _fetch(self, route, raw=False):
                if '/git/ref/tags/' in route:
                    return {'ref': 'refs/tags/' + urllib.parse.unquote(route.split('/git/ref/tags/')[1])}
                if '/commits/' in route:
                    ref = urllib.parse.unquote(route.split('/commits/')[1])
                    return {'sha': tags.get(ref, ref)}
                if '/git/trees/' in route:
                    return {'tree': []}
                if audit.CONTROL in route:
                    raise audit.Missing('confirmed negative control')
                return ORIGINAL
        resolver = Simulation()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda row: audit.audit(row, resolver), inventory['references']))
        self.assertFalse(any(r['verdict'] == 'QUERY_FAILED' for r in results))
        self.assertLess(len(resolver._requests), 1000)


class ImmutableCheckoutTests(unittest.TestCase):
    def test_actual_replacement_refs_do_not_change_immutable_bytes_or_sets(self):
        import os
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = dict(os.environ)
            environment.pop('GIT_NO_REPLACE_OBJECTS', None)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args],
                                               env=environment, stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('config', 'user.name', 'Immutable reference control')
            git('config', 'user.email', 'reference@example.invalid')
            (root / 'schema.json').write_bytes(ORIGINAL)
            git('add', '.')
            git('commit', '-qm', 'original immutable source')
            original = git('rev-parse', 'HEAD').decode().strip()
            (root / 'schema.json').write_bytes(b'{"replaced":true}\n')
            (root / 'unexpected.json').write_bytes(ORIGINAL)
            git('add', '.')
            git('commit', '-qm', 'replacement source')
            replacement = git('rev-parse', 'HEAD').decode().strip()
            git('replace', original, replacement)
            self.assertNotEqual(git('show', original + ':schema.json'), ORIGINAL)
            resolver = audit.Checkouts({'owner/authority': root})
            self.assertEqual(resolver.read('owner/authority', original, 'schema.json'), ORIGINAL)
            self.assertEqual(resolver.paths('owner/authority', original), {'schema.json'})
