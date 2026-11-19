"""Clause-derived policy controls and immutable historical retirement evidence."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
try:
    import reader_policy as policy
finally:
    sys.path.pop(0)
CORPUS = ROOT / 'conformance/reader-policy'


class ReaderPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((CORPUS / 'cases.json').read_text())
        cls.cases = {r['id']: r for r in cls.manifest['cases']}

    def payload(self, identity):
        case = self.cases[identity]
        return (CORPUS / case['file']).read_bytes(), case

    def test_corpus_is_deterministic_and_every_digest_is_measured(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/reader_policy.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.cases), 64)
        for case in self.cases.values():
            data = (CORPUS / case['file']).read_bytes()
            self.assertTrue(data)
            self.assertEqual(hashlib.sha256(data).hexdigest(), case['sha256'])

    def test_pad_bit_alias_decodes_to_identical_bytes_but_is_invalid(self):
        self.assertNotEqual(policy.CANONICAL, policy.NONCANONICAL)
        self.assertEqual(base64.b64decode(policy.CANONICAL), base64.b64decode(policy.NONCANONICAL))
        self.assertTrue(policy.canonical(policy.CANONICAL))
        self.assertFalse(policy.canonical(policy.NONCANONICAL))
        for typ in ('fhr', 'fhp', 'fhgff3'):
            for suffix in ('', '-yaml'):
                good, case = self.payload(typ + '-metadata-canonical-checksum' + suffix)
                bad, negative = self.payload(typ + '-metadata-noncanonical-checksum' + suffix)
                self.assertEqual(policy.observe(good, case), 'valid')
                self.assertEqual(policy.observe(bad, negative), 'invalid')

    def test_nested_failure_has_correct_root_file_checksum(self):
        for kind in ('fhp-fasta', 'fhgff3'):
            data, case = self.payload(kind + '-policy-noncanonical-parent')
            stated, computed = policy.shared.fhr_checksum(data, kind)
            self.assertEqual(stated, computed)
            record = policy.header_record(data, kind)
            schema = policy.shared.load_schema('v0.4.0', 'fhp.json' if kind == 'fhp-fasta' else 'fhgff3.json')
            self.assertTrue(policy.shared.schema_validator(schema).is_valid(record))
            self.assertFalse(policy.canonical(record['derivedFrom'][0]['checksum']))
            self.assertEqual(policy.observe(data, case), 'invalid')

    def test_generic_schema_pass_does_not_substitute_for_selection(self):
        for typ in ('fhp', 'fhgff3'):
            for suffix in ('', '-yaml'):
                data, case = self.payload(typ + '-metadata-selection-v0-4-0' + suffix)
                record = policy.yaml_record(data.decode()) if suffix else json.loads(data)
                current = policy.shared.schema_validator(json.loads((ROOT / (typ + '.json')).read_text()))
                self.assertTrue(current.is_valid(record))
                self.assertEqual(policy.observe(data, case), 'invalid')
                unknown, case = self.payload(typ + '-metadata-selection-v99-0-0' + suffix)
                self.assertEqual(policy.observe(unknown, case), 'unsupported-version')

    def test_directive_text_is_not_broadly_banned(self):
        for kind in ('fasta', 'gfa', 'fhp-fasta', 'fhgff3'):
            quoted, case = self.payload(kind + '-policy-quoted-directive-text')
            self.assertIn(b'%YAML', quoted)
            self.assertEqual(policy.observe(quoted, case), 'valid')
            for suffix in ('yaml-1-1', 'yaml-1-2', 'tag', 'document-marker'):
                directive, case = self.payload(kind + '-policy-' + suffix)
                stated, computed = policy.shared.fhr_checksum(directive, kind)
                self.assertEqual(stated, computed)
                self.assertEqual(policy.observe(directive, case), 'invalid')

    def test_single_fhcrc_bit_is_the_only_changed_transport_byte(self):
        good, _ = self.payload('fasta-policy-gzip-fhcrc-correct')
        bad, _ = self.payload('fasta-policy-gzip-fhcrc-wrong')
        changed = [i for i, pair in enumerate(zip(good, bad)) if pair[0] != pair[1]]
        self.assertEqual(len(good), len(bad))
        self.assertEqual(len(changed), 1)
        self.assertEqual(good[changed[0]] ^ bad[changed[0]], 1)
        plain, _ = self.payload('fasta-policy-plain-control')
        self.assertEqual(policy.strict_gzip(good), plain)
        with self.assertRaises(ValueError):
            policy.strict_gzip(bad)

    def test_gzip_padding_and_multimember_controls(self):
        plain, _ = self.payload('fasta-policy-plain-control')
        for suffix in ('member', 'trailing-nul', 'multimember-trailing-nul'):
            data, _ = self.payload('fasta-policy-gzip-' + suffix)
            self.assertEqual(policy.strict_gzip(data), plain)
        garbage, _ = self.payload('fasta-policy-gzip-trailing-garbage')
        with self.assertRaises(ValueError):
            policy.strict_gzip(garbage)
        with self.assertRaises(ValueError):
            policy.strict_gzip(b'\0' * 16)
        with self.assertRaises(ValueError):
            policy.strict_gzip(good := policy.builder.gzip_member(plain)[:-1])

    def test_new_line_ending_controls_have_one_exact_checksum_predicate(self):
        manifest = json.loads((ROOT / 'conformance/manifest.json').read_text())
        vectors = {v['id']: v for v in manifest['vectors']}
        for kind in ('fhp-fasta', 'fhgff3'):
            for ending in ('cr', 'mixed-endings'):
                for negative in (False, True):
                    identity = kind + '-' + ending + ('-normalized-checksum' if negative else '')
                    vector = vectors[identity]
                    data = (ROOT / 'conformance' / vector['file']).read_bytes()
                    stated, computed = policy.shared.fhr_checksum(data, kind)
                    self.assertEqual(stated == computed, not negative)
                    normalized = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
                    normalized_stated, normalized_computed = policy.shared.fhr_checksum(normalized, kind)
                    self.assertEqual(normalized_stated == normalized_computed, negative)

    def test_retirements_preserve_every_historical_payload_and_predicate(self):
        crosswalk = json.loads((CORPUS / 'retirement-crosswalk.json').read_text())
        source = crosswalk['historicalSource']['commit']
        archive = subprocess.check_output(['git', 'archive', source, 'conformance'], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
            old_bytes = tree.extractfile('conformance/manifest.json').read()
            self.assertEqual(hashlib.sha256(old_bytes).hexdigest(), crosswalk['historicalSource']['manifestSha256'])
            old = json.loads(old_bytes)
            current = json.loads((ROOT / 'conformance/manifest.json').read_text())
            vectors = {v['id']: v for v in current['vectors']}
            retired = {v['id']: v for v in current['retired']}
            self.assertEqual(crosswalk['counts'], {'valid': 30, 'invalid': 48})
            self.assertEqual(len(crosswalk['cases']), 78)
            for historical in old['vectors']:
                actual = (ROOT / 'conformance' / historical['file']).read_bytes()
                self.assertEqual(actual, tree.extractfile('conformance/' + historical['file']).read(), historical['id'])
                identity = historical['id']
                if identity in retired:
                    self.assertNotIn(identity, vectors)
                    self.assertEqual(retired[identity]['expected'], historical['expected'])
                    replacement = vectors[retired[identity]['replacedBy']]
                    self.assertEqual(replacement['expected'], historical['expected'])
                    if historical['expected'] == 'invalid':
                        self.assertEqual(replacement['rule'], historical['rule'])
                    else:
                        self.assertEqual(replacement['rules'], historical['rules'])
                else:
                    self.assertIn(identity, vectors)

    def test_execution_failures_cannot_match_expected_rejection(self):
        from unittest.mock import patch
        case = self.cases['fasta-policy-gzip-fhcrc-wrong']
        failures = [FileNotFoundError('missing executable'), subprocess.TimeoutExpired('tool', 30),
                    subprocess.CompletedProcess([], 2, '', 'usage: invalid command'),
                    subprocess.CompletedProcess([], 1, '', 'Traceback (most recent call last)'),
                    subprocess.CompletedProcess([], 1, '', '')]
        for failure in failures:
            with self.subTest(failure=failure):
                with patch.object(policy.subprocess, 'run', side_effect=failure if isinstance(failure, Exception) else None,
                                  return_value=failure):
                    observed = policy.toolkit_observation(Path('/missing/tool'), Path('case'), case)
                self.assertEqual(observed['actual'], 'execution-error')
                self.assertFalse(observed['matched'])

    def test_published_gap_receipt_detects_wrong_fixed_and_missing_results(self):
        import copy
        expected = json.loads((CORPUS / 'observations/toolkit-0.12.0.json').read_text())
        digest = hashlib.sha256((CORPUS / 'cases.json').read_bytes()).hexdigest()
        self.assertEqual(expected['exit'], 1)
        self.assertEqual((expected['matched'], expected['mismatched']), (35, 29))
        self.assertEqual(policy.receipt_problems(expected, expected, 1, digest), [])
        changed = copy.deepcopy(expected)
        row = next(r for r in changed['runtime'] if not r['matched'])
        row.update(actual=row['expected'], matched=True, exit=1)
        self.assertTrue(policy.receipt_problems(expected, changed, 1, digest))
        missing = copy.deepcopy(expected); missing['runtime'].pop()
        self.assertTrue(policy.receipt_problems(expected, missing, 1, digest))
        self.assertTrue(policy.receipt_problems(expected, expected, 0, digest))
        self.assertTrue(policy.receipt_problems(expected, expected, 1, '0' * 64))
