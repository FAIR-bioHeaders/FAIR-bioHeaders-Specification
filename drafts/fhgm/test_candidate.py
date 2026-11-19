# SPDX-License-Identifier: MPL-2.0
"""Effectual source-parity guards for the shared FHGM review candidate."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('candidate_source', HERE / 'check_source.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class SourceParity(unittest.TestCase):
    def test_current_copy_matches_record(self):
        self.assertEqual([], checker.verify())

    def test_changed_missing_and_extra_files_fail_local_parity(self):
        for defect in ('changed', 'missing', 'extra'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / 'candidate'
                shutil.copytree(HERE, root, ignore=shutil.ignore_patterns('__pycache__'))
                data = json.loads((root / 'source.json').read_text())
                file = root / data['files'][0]['local']
                if defect == 'changed':
                    file.write_bytes(file.read_bytes() + b'changed')
                elif defect == 'missing':
                    file.unlink()
                else:
                    (root / 'upstream' / 'unexpected.txt').write_text('extra')
                self.assertTrue(checker.verify(root))
        # A digest list alone cannot detect an entry deleted with its file.
        # The --upstream CI lane checks the selected source set independently.
        self.assertEqual({'development/a', 'LICENSE'}, checker.selected(
            ['development/a', 'LICENSE', 'unrelated'],
            {'prefixes': ['development/'], 'files': ['LICENSE']}))

    def test_upstream_tree_catches_selfconsistent_manifest_and_file_omission(self):
        import hashlib
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'candidate'
            source = Path(directory) / 'source'
            source.mkdir()
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            (source / 'development').mkdir()
            for name in ('a', 'b'):
                (source / 'development' / name).write_text(name)
            subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(source), '-c', 'commit.gpgsign=false',
                '-c', 'user.name=Parity test fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'fixture'], check=True)
            commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD']).decode().strip()
            (root / 'upstream/development').mkdir(parents=True)
            (root / 'upstream/development/a').write_text('a')
            record = {'source': {'commit': commit,
                'selection': {'prefixes': ['development/'], 'files': []}},
                'files': [{'source': 'development/a', 'local': 'upstream/development/a',
                    'bytes': 1, 'sha256': hashlib.sha256(b'a').hexdigest()}]}
            (root / 'source.json').write_text(json.dumps(record))
            self.assertEqual([], checker.verify(root))
            self.assertIn('source selection set differs from pinned tree', checker.verify(root, source))

    def test_candidate_remains_separate_from_header_identity(self):
        record = json.loads((HERE / 'source.json').read_text())
        schema = json.loads((HERE / record['candidate']['nativeArtifact']).read_text())
        self.assertNotIn('schemaVersion', schema.get('properties', {}))
        self.assertNotIn('schema', schema.get('properties', {}))
        self.assertEqual('0.1', record['candidate']['versionProposal'])
        self.assertIn('not published', record['candidate']['publicationStatus'])


class SnapshotBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('candidate_receipt', HERE / 'check_receipt.py')
        cls.receipt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.receipt)

    def test_carrier_and_all_declared_predecessors_are_required(self):
        vector = {'id': 'case', 'context': {'predecessors': ['a/prior.gff3']}}
        good = [{'subject': 'carrier'}, {'subject': 'predecessor prior.gff3'}]
        self.assertEqual([], self.receipt.snapshot_problems(vector, good))
        for bad in (good[:1], [], good[1:], list(reversed(good)),
                    [{'subject': 'carrier'}, {'subject': 'predecessor wrong.gff3'}]):
            self.assertTrue(self.receipt.snapshot_problems(vector, bad))

    def test_duplicate_subject_cannot_replace_a_distinct_declared_input(self):
        vector = {'id': 'case', 'context': {'predecessors': ['a/first.gff3', 'a/second.gff3']}}
        good = [{'subject': 'carrier'}, {'subject': 'predecessor first.gff3'},
                {'subject': 'predecessor second.gff3'}]
        self.assertEqual([], self.receipt.snapshot_problems(vector, good))
        self.assertTrue(self.receipt.snapshot_problems(vector, good[:2] + [good[1]]))

    def test_repeated_same_file_is_counted_and_distinct_same_basename_is_refused(self):
        subjects = [{'subject': 'carrier'}, {'subject': 'predecessor prior.gff3'},
                    {'subject': 'predecessor prior.gff3'}]
        repeated = {'id': 'repeated', 'context': {'predecessors': ['a/prior.gff3', 'a/prior.gff3']}}
        self.assertEqual([], self.receipt.snapshot_problems(repeated, subjects))
        self.assertTrue(self.receipt.snapshot_problems(repeated, subjects[:2]))
        ambiguous = {'id': 'ambiguous', 'context': {'predecessors': ['a/prior.gff3', 'b/prior.gff3']}}
        self.assertTrue(any('ambiguous predecessor identity' in error for error in
                            self.receipt.snapshot_problems(ambiguous, subjects)))

    def test_matrix_context_uses_the_committed_predecessor_subjects(self):
        manifest = json.loads(self.receipt.MANIFEST.read_text())
        vector = next(v for v in manifest['vectors'] if v['id'] == 'contract-rich-revision-chain')
        self.assertEqual([], self.receipt.snapshot_problems(vector,
            [{'subject': 'carrier'}, {'subject': 'predecessor minimal.fhgff3.gff3'}]))
        self.assertTrue(self.receipt.snapshot_problems(vector,
            [{'subject': 'carrier'}, {'subject': 'predecessor minimal-twin.fhgff3.gff3'}]))


if __name__ == '__main__':
    unittest.main()
