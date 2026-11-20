# SPDX-License-Identifier: MPL-2.0
"""Proposed FHT release integration: exact constraints, selectors, bytes and types."""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import fht_publication as candidate
from check_conformance import select_record, select_schema, schema_validator
from check_linkml import constraints
import fht_microdata as binding


class FHTPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / 'fht.json').read_text())
        cls.owner = json.loads((candidate.OWNER / 'fht.json').read_text())
        cls.reader = candidate.owning_reader()

    def test_every_nonselector_constraint_matches_accepted_owning_contract(self):
        owner, proposed = copy.deepcopy(self.owner), copy.deepcopy(self.schema)
        for document in (owner, proposed):
            for node in (document, document['$defs']['FHT']):
                node['properties']['schema'] = {'type': 'string'}
        self.assertEqual(constraints(owner, owner), constraints(proposed, proposed))
        self.assertEqual(candidate.sha((candidate.OWNER / 'fht.json').read_bytes()),
                         'b62c4e227042e162b43d2c461cfe6c3ece3806636ca88a4cf9b0b2f902fb1fc3')
        self.assertEqual(self.schema['$id'], 'https://w3id.org/fair-bioheaders/fht/v0.7.0')

    def test_v1_through_v7_keep_distinct_selection_outcomes(self):
        common = 'https://raw.githubusercontent.com/FAIR-bioHeaders/'
        for repo in ('FAIR-bioHeaders-Specification',):
            self.assertEqual(select_schema(common + repo + '/main/fht.json'), ('FHT', 'main', 'fht.json'))
            self.assertEqual(select_schema(common + repo + '/v0.7.0/fht.json'), ('FHT', 'v0.7.0', 'fht.json'))
        for suffix in ('', '/'):
            self.assertEqual(select_schema('https://w3id.org/fair-bioheaders/fht/v0.7.0' + suffix), ('FHT', 'v0.7.0', 'fht.json'))
        self.assertEqual(select_schema('https://w3id.org/fair-bioheaders/fht/v0.6.0'), ('FHT', None, None))
        self.assertEqual(select_schema(common + 'FHT-Specification/v0.7.0/fht.json'), ('FHR', 'main', 'fhr.json'))
        draft = common + 'FHT-Specification/main/fht.json'
        self.assertEqual(select_schema(draft), ('FHR', 'main', 'fhr.json'))
        self.assertEqual(candidate.owning_reader().schema_selection({'schema': draft}), 'current')  # Separate historical V7 opt-in.
        self.assertEqual(select_record({'schema': common + 'FHR-Specification/main/fhr.json', 'schemaVersion': 1}), ('FHR', 'v0.3.1', 'fhr.json'))

    def test_93_counterparts_and_changed_v4_dispositions_execute(self):
        receipt = candidate.check()
        self.assertEqual((receipt['cases'], receipt['valid']), (93, 34))
        rows = {row['sourceId']: row for row in receipt['results']}
        for identity in ('fht-fasta-schema-w3id-release-without-fht', 'fht-fasta-schema-shared-raw-tag'):
            self.assertEqual(rows[identity]['rule'], 'V4')
            self.assertEqual(rows[identity]['stage'], 'selection')
        for identity in ('fht-fasta-completeness-sum-exceeds-total', 'fht-fasta-completeness-sum-below-total'):
            self.assertEqual(rows[identity]['stage'], 'semantics')
        self.assertFalse(receipt['publicationVerified'])

    def test_named_checksum_faults_match_their_faulty_digest_relationships(self):
        manifest = json.loads((candidate.TARGET / 'manifest.json').read_text())
        entries = {row['sourceId']: row for row in manifest['vectors']}

        def transformed_sequence(data, transform):
            output, in_fasta = [], False
            for line in data.splitlines(keepends=True):
                content = line.rstrip(b'\r\n')
                ending = line[len(content):]
                if content.startswith(b'>'):
                    in_fasta = True
                elif in_fasta and content and not content.startswith(b';'):
                    content = transform(content)
                output.append(content + ending)
            return b''.join(output)

        for source_id in (
            'fht-fasta-crlf-normalized-checksum',
            'fht-fasta-u-normalized-checksum',
            'fht-fasta-case-normalized-checksum',
            'fht-fasta-checksum-sha256',
            'fht-fasta-checksum-truncated-sha512',
        ):
            with self.subTest(source_id=source_id):
                entry = entries[source_id]
                data = (candidate.TARGET / entry['file']).read_bytes()
                stated, position, length = self.reader.locate_checksum(data)
                if source_id == 'fht-fasta-crlf-normalized-checksum':
                    faulty_bytes = data.replace(b'\r\n', b'\n')
                    faulty_digest = self.reader.recomputed(faulty_bytes)
                elif source_id == 'fht-fasta-u-normalized-checksum':
                    faulty_bytes = transformed_sequence(
                        data, lambda line: line.replace(b'U', b'T').replace(b'u', b't'))
                    faulty_digest = self.reader.recomputed(faulty_bytes)
                elif source_id == 'fht-fasta-case-normalized-checksum':
                    faulty_bytes = transformed_sequence(data, bytes.upper)
                    faulty_digest = self.reader.recomputed(faulty_bytes)
                else:
                    covered = data[:position] + data[position + length:]
                    algorithm = 'sha256' if source_id.endswith('sha256') else 'sha512'
                    digest = hashlib.new(algorithm, covered).digest()
                    if algorithm == 'sha512':
                        digest = digest[:32]
                    faulty_digest = base64.b64encode(digest).decode('ascii')
                self.assertEqual(stated, faulty_digest)
                self.assertNotEqual(stated, self.reader.recomputed(data))
                self.assertFalse(candidate.observe(data, entry, self.reader)['valid'])

    def test_all_historical_v060_fixture_bytes_are_unchanged(self):
        original = subprocess.check_output(['git', '--no-replace-objects', '-C', str(ROOT), 'show', 'v0.6.0:conformance/manifest.json'])
        manifest = json.loads(original)
        self.assertEqual(len(manifest['vectors']), 291)
        for vector in manifest['vectors']:
            name = 'conformance/' + vector['file']
            expected = subprocess.check_output(['git', '--no-replace-objects', '-C', str(ROOT), 'show', 'v0.6.0:' + name])
            self.assertEqual((ROOT / name).read_bytes(), expected, vector['id'])

    def test_candidate_examples_preserve_bytes_metadata_and_typed_values(self):
        self.assertEqual(candidate.check_examples(), 7)
        for location in sorted((ROOT / 'examples/fht').glob('*.fht.json')):
            record = json.loads(location.read_text())
            html = location.with_suffix('.html').read_text()
            actual = binding.read_page(html, allow_candidate=True, warn=lambda message: None)
            self.assertEqual(json.dumps(actual, sort_keys=True), json.dumps(record, sort_keys=True))
            data = location.with_suffix('.fasta').read_bytes()
            stated, _, _ = self.reader.locate_checksum(data)
            self.assertEqual(stated, self.reader.recomputed(data))
            self.assertEqual(actual['checksum'], stated)
            self.assertEqual(list(schema_validator(self.schema).iter_errors(actual)), [])

    def test_binding_refuses_implicit_candidate_unknown_release_and_wrong_types(self):
        record = json.loads((ROOT / 'examples/fht/minimal-de-novo.fht.json').read_text())
        with self.assertRaisesRegex(binding.MicrodataError, 'allow_candidate'):
            binding.write_page(record)
        wrong = copy.deepcopy(record)
        wrong['schema'] = 'https://w3id.org/fair-bioheaders/fht/v9.9.9'
        with self.assertRaisesRegex(binding.MicrodataError, 'selection'):
            binding.write_page(wrong, allow_candidate=True)
        wrong = copy.deepcopy(record); wrong['schemaVersion'] = 1.0
        with self.assertRaises(binding.MicrodataError):
            binding.write_page(wrong, allow_candidate=True)
        record['vitalStats'] = {'totalTranscripts': 9007199254740993}
        text = binding.write_page(record, allow_candidate=True)
        extracted = binding.read_page(text, allow_candidate=True, warn=lambda message: None)
        self.assertEqual(extracted['vitalStats']['totalTranscripts'], 9007199254740993)
        self.assertIs(type(extracted['vitalStats']['totalTranscripts']), int)
        mutated = text.replace('data-fhr-type="integer"', 'data-fhr-type="string"', 1)
        with self.assertRaises(binding.MicrodataError):
            binding.read_page(mutated, allow_candidate=True, warn=lambda message: None)

    def test_observation_detects_actual_covered_byte_mutation(self):
        manifest = json.loads((candidate.TARGET / 'manifest.json').read_text())
        entry = next(row for row in manifest['vectors'] if row['expected'] == 'valid' and not row['compressed'])
        original = (candidate.TARGET / entry['file']).read_bytes()
        self.assertTrue(candidate.observe(original, entry, self.reader)['valid'])
        changed = original + b'\n; controlled covered-byte mutation\n'
        self.assertNotEqual(original, changed)
        result = candidate.observe(changed, entry, self.reader)
        self.assertFalse(result['valid'])
        self.assertEqual(result['stage'], 'checksum')

    def test_primary_rule_cannot_be_masked_by_a_wrong_checksum(self):
        manifest = json.loads((candidate.TARGET / 'manifest.json').read_text())
        entry = next(row for row in manifest['vectors'] if row['sourceId'] == 'fht-fasta-completeness-sum-exceeds-total')
        original = (candidate.TARGET / entry['file']).read_bytes()
        changed = original + b'\n; wrong covered byte\n'
        with self.assertRaisesRegex(ValueError, 'primary rule'):
            candidate.assert_expected(entry, changed, self.reader)

    def test_parent_context_must_bind_the_observed_child(self):
        manifest = json.loads((candidate.TARGET / 'manifest.json').read_text())
        entry = next(row for row in manifest['vectors'] if row['expected'] == 'valid' and any(link['result'] == 'checked-pass' for link in row['parentLink']))
        data = (candidate.TARGET / entry['file']).read_bytes()
        old = entry['parentLink'][0]['statedChecksum'].encode()
        changed = data.replace(old, b'A' * 43 + b'=')
        stated, position, length = self.reader.locate_checksum(changed)
        line = changed[position:position + length]
        changed = changed[:position] + line.replace(stated.encode(), self.reader.recomputed(changed).encode(), 1) + changed[position + length:]
        outcome = candidate.observe(changed, entry, self.reader)
        self.assertFalse(outcome['valid'])
        self.assertEqual(outcome['stage'], 'parent-context')
        with self.assertRaisesRegex(ValueError, 'primary rule'):
            candidate.assert_expected(entry, changed, self.reader)

    def test_binding_recognizes_all_family_aliases_before_conflict_check(self):
        record = json.loads((ROOT / 'examples/fht/minimal-de-novo.fht.json').read_text())
        html = binding.write_page(record, allow_candidate=True)
        for selector in ('https://w3id.org/fair-bioheaders/fhr/v0.6.0',
                         'https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/v0.6.0/fhp.json',
                         'https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json'):
            with self.subTest(selector=selector):
                mixed = html.replace('itemtype="' + binding.FHT_ITEMTYPE + '"', 'itemtype="' + binding.FHT_ITEMTYPE + ' ' + selector + '"')
                with self.assertRaisesRegex(binding.MicrodataError, 'family'):
                    binding.read_page(mixed, allow_candidate=True)

    def test_selected_reader_policy_boundaries_have_positive_and_negative_controls(self):
        import gzip
        import zlib
        manifest = json.loads((candidate.TARGET / 'manifest.json').read_text())
        entry = next(row for row in manifest['vectors'] if row['expected'] == 'valid' and not row['compressed'] and not row['parentLink'])
        plain = (candidate.TARGET / entry['file']).read_bytes()
        compressed = dict(entry, compressed=True)
        wrapped = gzip.compress(plain, mtime=0)
        self.assertTrue(candidate.observe(wrapped + b'\0\0', compressed, self.reader)['valid'])
        self.assertFalse(candidate.observe(wrapped + b'junk', compressed, self.reader)['valid'])
        header = bytearray(wrapped[:10]); header[3] |= 2
        crc = (zlib.crc32(header) & 65535).to_bytes(2, 'little')
        fhcrc = bytes(header) + crc + wrapped[10:]
        self.assertTrue(candidate.observe(fhcrc, compressed, self.reader)['valid'])
        wrong = bytearray(fhcrc); wrong[10] ^= 1
        self.assertFalse(candidate.observe(bytes(wrong), compressed, self.reader)['valid'])
        for statement, valid in ((b';~%YAML 1.2\n;~---\n', False), (b';~documentation: "%YAML quoted text"\n', True)):
            if valid:
                import re
                changed, count = re.subn(rb'^;~documentation:[^\r\n]*(?:\r\n|\n|\r)', statement, plain, count=1, flags=re.M)
                self.assertEqual(count, 1)
            else:
                changed = statement + plain
            stated, position, length = self.reader.locate_checksum(changed)
            line = changed[position:position + length]
            changed = changed[:position] + line.replace(stated.encode(), self.reader.recomputed(changed).encode(), 1) + changed[position + length:]
            self.assertEqual(candidate.observe(changed, entry, self.reader)['valid'], valid)

    def test_tag_reference_state_requires_exact_fixture_tag_and_never_claims_release(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            (fixture / 'schemas').mkdir()
            registry = json.loads((ROOT / 'schemas/versions.json').read_text())
            registry['preRelease'] = None
            (fixture / 'schemas/versions.json').write_text(json.dumps(registry))
            (fixture / 'fht.json').write_bytes((ROOT / 'fht.json').read_bytes())
            record = json.loads((ROOT / 'examples/fht/minimal-de-novo.fht.json').read_text())
            with patch.object(binding, 'ROOT', fixture):
                registry['preRelease'] = 'v0.7.0'
                (fixture / 'schemas/versions.json').write_text(json.dumps(registry))
                before = binding.write_page(record, allow_candidate=True,
                    title='Stable synthetic example', _reference_example=True)
                registry['preRelease'] = None
                (fixture / 'schemas/versions.json').write_text(json.dumps(registry))
            def git(*args):
                return subprocess.check_output(['git', '-C', str(fixture), *args], stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('add', '.')
            git('-c', 'commit.gpgsign=false', '-c', 'user.name=Tag-state fixture',
                '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture only')
            with patch.object(binding, 'ROOT', fixture):
                with self.assertRaisesRegex(binding.MicrodataError, 'actual byte-matching'):
                    binding.write_page(record)
                with self.assertRaisesRegex(binding.MicrodataError, 'actual byte-matching'):
                    binding.write_page(record, _reference_example=True)
                git('tag', 'v0.7.0')  # Only inside the temporary repository, never the shared checkout.
                # A real working-file swap after its bytes are read must not
                # change the schema object that claims exact tag provenance.
                schema_file = fixture / 'fht.json'
                committed = schema_file.read_bytes()
                weaker = dict(self.schema, required=[])
                original_read = Path.read_bytes
                swapped = []
                def swap_after_snapshot(location):
                    raw = original_read(location)
                    if location == schema_file and not swapped:
                        location.write_text(json.dumps(weaker))
                        swapped.append(True)
                    return raw
                with patch.object(Path, 'read_bytes', swap_after_snapshot):
                    selected, mode = binding._candidate_schema(False, None)
                self.assertTrue(swapped)
                self.assertEqual(selected, self.schema)
                self.assertEqual(mode, 'tag-verified-reference')
                schema_file.write_bytes(committed)
                self.assertEqual(binding.write_page(record, title='Stable synthetic example',
                    _reference_example=True), before)
                registry['current'] = 'v0.8.0'
                registry['preRelease'] = 'v0.8.0'
                registry['releases']['v0.8.0'] = dict(registry['releases']['v0.7.0'])
                (fixture / 'schemas/versions.json').write_text(json.dumps(registry))
                self.assertEqual(binding.write_page(record, title='Stable synthetic example',
                    _reference_example=True), before)
                registry['releases']['v0.8.0']['FHT'] = '2.0'
                (fixture / 'schemas/versions.json').write_text(json.dumps(registry))
                with self.assertRaisesRegex(binding.MicrodataError, 'registered FHT 1.0'):
                    binding.write_page(record)
                registry['releases']['v0.8.0']['FHT'] = '1.0'
                (fixture / 'schemas/versions.json').write_text(json.dumps(registry))
                html = binding.write_page(record)
                self.assertIn('FHT tag-verified reference metadata', html)
                self.assertNotIn('publication-candidate metadata', html)
                self.assertNotIn('Unreleased FHT draft binding example', html)
                self.assertIn('<p>FHT reference checked against the exact v0.7.0 tag; GitHub Release and publication have not been verified.', html)
                messages = []
                self.assertEqual(binding.read_page(html, warn=messages.append), record)
                self.assertEqual(len(messages), 1)
                self.assertIn('tag-verified reference', messages[0])
                self.assertIn('GitHub Release and publication not verified', messages[0])
                self.assertNotIn('Unpublished', messages[0])
                changed = dict(self.schema, description='working bytes differ from fixture tag')
                (fixture / 'fht.json').write_text(json.dumps(changed))
                with self.assertRaisesRegex(binding.MicrodataError, 'actual byte-matching'):
                    binding.write_page(record)
                # Candidate diagnostics are checked independently of the actual
                # checkout's publication state, using this private Git fixture.
                schema_file.write_bytes(committed)
                registry['current'] = registry['preRelease'] = 'v0.7.0'
                (fixture / 'schemas/versions.json').write_text(json.dumps(registry))
                messages = []
                self.assertEqual(binding.read_page(before, allow_candidate=True,
                                                  warn=messages.append), record)
                self.assertIn('Unpublished', messages[0])
                self.assertIn('released=false', messages[0])

    def test_shared_binding_executes_every_rule_specific_negative_html_fixture(self):
        fixtures = candidate.OWNER / 'tests/fixtures/microdata'
        manifest = json.loads((fixtures / 'manifest.json').read_text())['invalid']
        self.assertEqual(len(manifest), 20)
        self.assertEqual(set(manifest), {path.name for path in (fixtures / 'invalid').glob('*.html')})
        overrides = {
            'wrong-type.html': 'expected exactly one candidate FHT scope and no conflicting family scope',
            'mixed-family.html': 'expected exactly one candidate FHT scope and no conflicting family scope',
            'unknown-release.html': 'unsupported candidate FHT schema selection',
            'wrong-version-type.html': 'unsupported FHT schemaVersion',
        }
        for name, expected in manifest.items():
            with self.subTest(name=name, reason=expected['reason']):
                text = (fixtures / 'invalid' / name).read_text()
                counterpart = text.replace(candidate.RAW_DRAFT.decode(), binding.FHT_ITEMTYPE)
                error = overrides.get(name, expected['error'])
                self.assertTrue(error.strip())
                with self.assertRaisesRegex(binding.MicrodataError, error):
                    binding.read_page(counterpart, allow_candidate=True)

    def test_shared_binding_document_has_exact_provenance_and_generated_contract_table(self):
        path, expected = candidate.binding_document()
        text = path.read_text()
        self.assertEqual(text, expected)
        self.assertIn(candidate.sha((ROOT / 'fht.json').read_bytes()), text)
        self.assertIn(candidate.sha((candidate.OWNER / 'docs/FHT-MICRODATA.md').read_bytes()), text)
        for label in range(1, 8):
            self.assertIn('## F' + str(label) + ' —', text)
        for name in self.schema['properties']:
            self.assertIn('| `' + name + '` |', text)
        self.assertIn('allow_candidate=False', text)
        self.assertNotIn('4156353aa6d077', text)
        self.assertIn('(FHT-MICRODATA.md)', (ROOT / 'docs/MICRODATA.md').read_text())

    def test_new_fht_has_no_legacy_fhr_repository_publication_authority(self):
        canonical = 'https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/'
        legacy = 'https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/'
        record = json.loads((ROOT / 'examples/fht/minimal-de-novo.fht.json').read_text())
        html = binding.write_page(record, allow_candidate=True)
        for ref in ('main', 'v0.7.0'):
            uri = legacy + ref + '/fht.json'
            with self.subTest(ref=ref):
                self.assertEqual(select_schema(uri), ('FHR', 'main', 'fhr.json'))  # V5.
                changed = dict(record, schema=uri)
                self.assertFalse(schema_validator(self.schema).is_valid(changed))
                with self.assertRaisesRegex(binding.MicrodataError, 'selection'):
                    binding.write_page(changed, allow_candidate=True)
                scope_only = html.replace('itemtype="' + binding.FHT_ITEMTYPE + '"', 'itemtype="' + uri + '"')
                with self.assertRaises(binding.MicrodataError):
                    binding.read_page(scope_only, allow_candidate=True)
                self.assertEqual(select_schema(canonical + ref + '/fht.json'), ('FHT', ref, 'fht.json'))
        for kind in ('fhr', 'fhp', 'fhgff3'):
            header = {'fhr': 'FHR', 'fhp': 'FHP', 'fhgff3': 'FHGFF3'}[kind]
            self.assertEqual(select_schema(legacy + 'main/' + kind + '.json'), (header, 'main', kind + '.json'))
            self.assertEqual(select_schema(legacy + 'v0.6.0/' + kind + '.json'), (header, 'v0.6.0', kind + '.json'))


if __name__ == '__main__':
    unittest.main()
