# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Controlled owning git trees; current production findings are not PR gates."""
import copy
import contextlib
import hashlib
import importlib.util
import json
import io
import os
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('staged_reference_adapter', ROOT / 'scripts/audit_current_references.py')
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)
REPOSITORIES = {'fht': 'FAIR-bioHeaders/FHT-Specification',
                'fhgm': 'FAIR-bioHeaders/FHGM-Specification'}


class CurrentReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'shared'
        self.mapping = {}
        self.owners = {}
        self.records = {}
        for kind in ('fht', 'fhgm'):
            owner = self.base / ('owning-' + kind)
            owner.mkdir()
            self.owners[kind] = owner
            self.mapping[REPOSITORIES[kind]] = owner
            files = ({'.gitattributes': b'* -text\n', 'AGENTS.md': b'guidance\n',
                      'module.py': b'answer = 7\n', 'data.json': b'{"fixture":true}\n'}
                     if kind == 'fht' else {
                         '.gitattributes': b'* -text\n', 'LICENSE': b'fixture notice\n',
                         'tests/test_fhgm_conformance.py': b'# fixture only\n',
                         'development/model.py': b'answer = 7\n',
                         'development/data.json': b'{"fixture":true}\n',
                         'README.md': b'outside selected scope\n'})
            for name, raw in files.items():
                target = owner / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            self.git(kind, 'init', '-q')
            self.git(kind, 'config', 'user.name', 'Current reference control')
            self.git(kind, 'config', 'user.email', 'reference@example.invalid')
            self.git(kind, 'add', '.')
            self.git(kind, 'commit', '-qm', 'controlled owning source')
            commit = self.git(kind, 'rev-parse', 'HEAD').decode().strip()
            source = {'repository': REPOSITORIES[kind], 'commit': commit}
            entries = []
            for name, raw in files.items():
                if name == 'AGENTS.md' or (kind == 'fhgm' and name == 'README.md'):
                    continue
                target = self.root / 'drafts' / kind / 'upstream' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                entries.append({'source': name, 'local': 'upstream/' + name,
                                'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
            if kind == 'fht':
                source['selection'] = {'trackedFiles': 'all', 'excluded': ['AGENTS.md']}
                record = {**source, 'files': entries}
            else:
                source['selection'] = {'prefixes': ['development/'],
                                       'files': ['.gitattributes', 'LICENSE', 'tests/test_fhgm_conformance.py']}
                record = {'source': source, 'files': entries}
            self.records[kind] = record
            self.write(kind)

    def git(self, kind, *args):
        return subprocess.check_output(['git', '-C', str(self.owners[kind]), *args], stderr=subprocess.DEVNULL)

    def write(self, kind):
        (self.root / 'drafts' / kind / 'source.json').write_text(json.dumps(self.records[kind]))

    def result(self, kind='fht', mapping=None):
        report = adapter.audit_current(self.mapping if mapping is None else mapping, self.root)
        return next(row for row in report['references'] if row['id'] == 'shared-staged-' + kind)

    def test_both_independent_selected_source_and_local_sets_are_fresh(self):
        report = adapter.audit_current(self.mapping, self.root)
        self.assertEqual(report['declaredFiles'], 8)
        self.assertEqual({r['verdict'] for r in report['references']}, {'FRESH'})
        for row in report['references']:
            self.assertEqual(row['sourceSetComparison'], 'performed')
            self.assertEqual(row['localComparison'], 'performed')
            self.assertEqual(row['onlyAuthority'], [])
            self.assertEqual(row['onlyLocal'], [])
        self.assertEqual(self.result()['excludedAuthorityPaths'], ['AGENTS.md'])
        self.assertEqual(report['wrote'], [])

    def test_repository_reference_and_path_mutations_cannot_be_fresh(self):
        original = copy.deepcopy(self.records['fht'])
        for mutation in ('repository', 'commit', 'source', 'local'):
            self.records['fht'] = copy.deepcopy(original)
            if mutation == 'repository':
                self.records['fht']['repository'] = 'other/owner'
            elif mutation == 'commit':
                self.records['fht']['commit'] = 'main'
            else:
                self.records['fht']['files'][0][mutation] = '../outside'
            self.write('fht')
            self.assertEqual(self.result()['verdict'], 'DRIFT', mutation)

    def test_source_selection_cannot_be_narrowed_or_silently_expanded(self):
        original = copy.deepcopy(self.records['fht'])
        self.records['fht']['selection']['excluded'].append('data.json')
        self.write('fht')
        self.assertEqual(self.result()['verdict'], 'DRIFT')
        self.records['fht'] = original
        self.write('fht')
        self.records['fhgm']['source']['selection']['prefixes'] = ['']
        self.write('fhgm')
        self.assertEqual(self.result('fhgm')['verdict'], 'DRIFT')

    def test_omitting_a_file_and_its_manifest_entry_still_drifts(self):
        for kind, name in (('fht', 'data.json'), ('fhgm', 'development/data.json')):
            self.records[kind]['files'] = [f for f in self.records[kind]['files'] if f['source'] != name]
            self.write(kind)
            (self.root / 'drafts' / kind / 'upstream' / name).unlink()
            row = self.result(kind)
            self.assertEqual(row['verdict'], 'DRIFT')
            self.assertEqual(row['onlyAuthority'], [name])

    def test_unknown_python_or_data_files_are_never_cache_exclusions(self):
        tree = self.root / 'drafts/fht/upstream'
        for name in ('unknown.py', '__pycache__/test_rogue.py', 'notes.dat',
                     '__pycache__/module.' + sys.implementation.cache_tag + '.pyc'):
            target = tree / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'not generated bytecode')
            self.assertEqual(self.result()['verdict'], 'DRIFT', name)
            target.unlink()

    def test_only_recognized_generated_bytecode_of_a_declared_module_is_exempt(self):
        tree = self.root / 'drafts/fht/upstream'
        cache = tree / '__pycache__' / ('module.' + sys.implementation.cache_tag + '.pyc')
        cache.parent.mkdir()
        py_compile.compile(str(tree / 'module.py'), cfile=str(cache), doraise=True)
        row = self.result()
        self.assertEqual(row['verdict'], 'FRESH')
        self.assertEqual(row['onlyLocal'], [])
        cache.write_bytes(b'data at a cache-shaped path')
        self.assertEqual(self.result()['verdict'], 'DRIFT')

    def test_unperformed_queries_and_missing_declarations_are_distinct(self):
        self.assertEqual(self.result(mapping={})['verdict'], 'QUERY_FAILED')
        self.records['fht'].pop('commit')
        self.write('fht')
        self.assertEqual(self.result()['verdict'], 'ABSENT')

    def test_current_record_change_is_used_instead_of_dated_inventory(self):
        raw = b'{"fixture":"new reviewed source"}\n'
        (self.owners['fht'] / 'data.json').write_bytes(raw)
        self.git('fht', 'add', 'data.json')
        self.git('fht', 'commit', '-qm', 'new controlled source')
        commit = self.git('fht', 'rev-parse', 'HEAD').decode().strip()
        self.records['fht']['commit'] = commit
        item = next(f for f in self.records['fht']['files'] if f['source'] == 'data.json')
        item.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        (self.root / 'drafts/fht/upstream/data.json').write_bytes(raw)
        self.write('fht')
        row = self.result()
        self.assertEqual(row['verdict'], 'FRESH')
        self.assertEqual(row['resolvedCommit'], commit)

    def test_atomic_plan_fallback_preserves_known_absent_and_drift(self):
        import yaml
        self.records['fht'].pop('commit')
        self.write('fht')
        self.records['fhgm']['source']['repository'] = 'wrong/repository'
        self.write('fhgm')
        report = adapter.plan(self.root)
        self.assertEqual({r['verdict'] for r in report['references']}, {'ABSENT', 'DRIFT'})
        steps = yaml.safe_load((ROOT / '.github/workflows/current-references.yml').read_text())['jobs']['current-staged-trees']['steps']
        script = next(s['run'] for s in steps if s.get('name', '').startswith('Preserve a failure record'))
        with tempfile.TemporaryDirectory() as work:
            plan_file = Path(work) / 'current-reference-plan.json'
            with contextlib.redirect_stdout(io.StringIO()):
                adapter.emit(report, plan_file)
            subprocess.run(['bash', '-e', '-c', script], check=True,
                           env={**os.environ, 'RUNNER_TEMP': work})
            retained = json.loads((Path(work) / 'current-reference-audit.json').read_text())
            self.assertEqual({r['verdict'] for r in retained['references']}, {'ABSENT', 'DRIFT'})

    def test_setup_failure_without_a_plan_retains_query_failed_json(self):
        import yaml
        steps = yaml.safe_load((ROOT / '.github/workflows/current-references.yml').read_text())['jobs']['current-staged-trees']['steps']
        script = next(s['run'] for s in steps if s.get('name', '').startswith('Preserve a failure record'))
        with tempfile.TemporaryDirectory() as work:
            subprocess.run(['bash', '-e', '-c', script], check=True,
                           env={**os.environ, 'RUNNER_TEMP': work})
            retained = json.loads((Path(work) / 'current-reference-audit.json').read_text())
            self.assertEqual(retained['references'][0]['verdict'], 'QUERY_FAILED')
            self.assertEqual(retained['references'][0]['localComparison'], 'not-run')


if __name__ == '__main__':
    unittest.main()
