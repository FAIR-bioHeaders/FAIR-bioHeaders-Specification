# SPDX-License-Identifier: MPL-2.0
"""Native publication must preserve the accepted schema, source and earned evidence."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('fhgm_publication', ROOT / 'scripts/fhgm_publication.py')
publication = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publication)


class NativePublication(unittest.TestCase):
    def copy(self, root):
        shutil.copytree(ROOT / 'drafts/fhgm', root / 'drafts/fhgm',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copytree(ROOT / publication.PACKAGE, root / publication.PACKAGE)

    def test_current_native_counterpart_is_identity_only(self):
        self.assertEqual([], publication.verify())
        schema = json.loads((ROOT / publication.PACKAGE / 'fhgm-model.schema.json').read_bytes())
        self.assertEqual(publication.IDENTITY, schema['$id'])
        self.assertNotIn('schema', schema['properties'])
        self.assertNotIn('schemaVersion', schema['properties'])

    def test_identity_or_constraint_mutation_is_rejected_even_with_matching_metadata_digest(self):
        for defect in ('identity', 'required'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.copy(root)
                package = root / publication.PACKAGE
                file = package / 'fhgm-model.schema.json'
                schema = json.loads(file.read_bytes())
                if defect == 'identity':
                    schema['$id'] += '/wrong'
                else:
                    schema['required'].remove('reference')
                file.write_text(json.dumps(schema))
                metadata = json.loads((package / 'publication.json').read_bytes())
                metadata['sha256'] = publication.digest(file.read_bytes())
                (package / 'publication.json').write_text(json.dumps(metadata))
                self.assertTrue(publication.verify(root))

    def test_changed_or_missing_vector_and_coordinated_source_omission_are_rejected(self):
        for defect in ('changed', 'missing', 'manifest-omission', 'extra'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.copy(root)
                candidate = root / 'drafts/fhgm'
                source = json.loads((candidate / 'source.json').read_bytes())
                entry = next(e for e in source['files'] if '/vectors/' in e['local'])
                file = candidate / entry['local']
                if defect == 'changed':
                    file.write_bytes(file.read_bytes() + b'changed')
                elif defect in ('missing', 'manifest-omission'):
                    file.unlink()
                    if defect == 'manifest-omission':
                        source['files'].remove(entry)
                        (candidate / 'source.json').write_text(json.dumps(source))
                else:
                    (candidate / 'upstream/extra.txt').write_text('extra')
                self.assertTrue(publication.verify(root))

    def test_private_execution_changes_only_native_schema_and_its_exact_provenance_record(self):
        source = ROOT / 'drafts/fhgm/upstream'
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / 'upstream'
            publication.prepare_snapshot(ROOT, snapshot)
            changed = {str(file.relative_to(source)) for file in source.rglob('*')
                       if file.is_file() and '__pycache__' not in file.parts
                       and file.read_bytes() != (snapshot / file.relative_to(source)).read_bytes()}
            self.assertEqual({'development/model/fhgm-model.schema.json',
                              'development/conformance/provenance.json'}, changed)
            before = json.loads((source / 'development/conformance/provenance.json').read_bytes())
            after = json.loads((snapshot / 'development/conformance/provenance.json').read_bytes())
            schema = snapshot / 'development/model/fhgm-model.schema.json'
            target = next(e for e in before['contractArtifacts'] if e['local'] == 'development/model/fhgm-model.schema.json')
            target.update(sha256=publication.digest(schema.read_bytes()), size=schema.stat().st_size)
            self.assertEqual(before, after)

    def test_unusable_prerequisites_do_not_generate_a_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'receipt.json'
            with self.assertRaisesRegex(ValueError, 'both released base files'):
                publication.run_conformance([], Path(directory) / 'missing', report)
            self.assertFalse(report.exists())


if __name__ == '__main__':
    unittest.main()
