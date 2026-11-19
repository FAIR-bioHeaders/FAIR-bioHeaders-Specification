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
                'repository': 'owner/authority', 'revision': 'v1.0.0',
                'revisionKind': 'tag', 'commit': COMMIT,
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
