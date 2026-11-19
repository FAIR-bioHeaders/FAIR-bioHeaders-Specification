#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Read current staged draft declarations; audit offline without changing pins."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = 'FAIR-bioHeaders/FAIR-bioHeaders-Specification'
SOURCES = {'fht': 'FAIR-bioHeaders/FHT-Specification',
           'fhgm': 'FAIR-bioHeaders/FHGM-Specification'}
FHGM_FILES = ['.gitattributes', 'LICENSE', 'tests/test_fhgm_conformance.py']
SPEC = importlib.util.spec_from_file_location('current_reference_engine', ROOT / 'scripts/check_references.py')
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)


class DeclarationError(ValueError):
    pass


class IncompleteDeclaration(DeclarationError):
    pass


def required(value, name):
    if value is None or value == '' or value == []:
        raise IncompleteDeclaration('Missing declaration: ' + name)
    return value


def path(value):
    required(value, 'path')
    if (not isinstance(value, str) or value in ('.', '')
            or PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts
            or '.git' in PurePosixPath(value).parts or str(PurePosixPath(value)) != value):
        raise DeclarationError('Unsafe or noncanonical declared path')
    return value


def cache_exclusions(root, tree, files):
    """Only current-interpreter bytecode for declared Python modules is exempt."""
    allowed = set()
    for entry in files:
        source = PurePosixPath(entry['local'])
        if source.suffix == '.py':
            for suffix in ('', '.opt-1', '.opt-2'):
                allowed.add(str(source.parent / '__pycache__' /
                    (source.stem + '.' + sys.implementation.cache_tag + suffix + '.pyc')))
    recorded = {entry['local'] for entry in files}
    exclusions = []
    for folder, dirs, names in os.walk(root / tree):
        if any((Path(folder) / name).is_symlink() for name in dirs):
            raise DeclarationError('Local copied tree contains a symlink directory')
        for name in names:
            candidate = Path(folder) / name
            if candidate.is_symlink() or not candidate.is_file():
                raise DeclarationError('Local copied tree contains a nonregular file')
            relative = candidate.relative_to(root).as_posix()
            if relative not in allowed or relative in recorded:
                continue
            with candidate.open('rb') as stream:
                header = stream.read(16)
            if (len(header) == 16 and candidate.stat().st_size > 16
                    and header[:4] == importlib.util.MAGIC_NUMBER
                    and int.from_bytes(header[4:8], 'little') in (0, 1, 3)):
                exclusions.append(relative)
    return sorted(exclusions)


def normalize(kind, record, root):
    source = record if kind == 'fht' else required(record.get('source'), 'source')
    repository = required(source.get('repository'), 'repository')
    if repository != SOURCES[kind]:
        raise DeclarationError('Unexpected owning repository')
    commit = required(source.get('commit'), 'commit')
    if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise DeclarationError('Draft source requires a full immutable commit')
    selection = required(source.get('selection'), 'selection')
    if kind == 'fht':
        if (not isinstance(selection, dict) or selection.get('trackedFiles') != 'all'
                or selection.get('excluded') != ['AGENTS.md']
                or set(selection) - {'trackedFiles', 'excluded', 'reason'}):
            raise DeclarationError('FHT source scope must be all tracked files except AGENTS.md')
        patterns, exclusions = ['*'], ['AGENTS.md']
    else:
        if selection != {'prefixes': ['development/'], 'files': FHGM_FILES}:
            raise DeclarationError('FHGM source scope must retain development/ and the three named files')
        patterns, exclusions = ['development/*'] + FHGM_FILES, []
    entries = required(record.get('files'), 'files')
    if not isinstance(entries, list):
        raise DeclarationError('File declaration must be a list')
    files = []
    seen = set()
    for entry in entries:
        source_path = path(entry.get('source'))
        local = path(entry.get('local'))
        digest = required(entry.get('sha256'), 'sha256')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise DeclarationError('File digest must be full SHA-256')
        if local != 'upstream/' + source_path or source_path in seen:
            raise DeclarationError('Duplicate or remapped source path')
        if kind == 'fht' and source_path == 'AGENTS.md':
            raise DeclarationError('Excluded FHT guidance cannot be part of the copy set')
        if kind == 'fhgm' and not (source_path.startswith('development/') or source_path in FHGM_FILES):
            raise DeclarationError('FHGM file lies outside the approved selection')
        seen.add(source_path)
        files.append({'path': source_path, 'local': 'drafts/' + kind + '/' + local, 'sha256': digest})
    tree = 'drafts/' + kind + '/upstream'
    return {'id': 'shared-staged-' + kind, 'consumer': CONSUMER,
            'record': 'drafts/' + kind + '/source.json', 'class': 'copied-tree',
            'materialStatus': 'draft', 'repository': repository, 'revision': commit,
            'revisionKind': 'commit', 'commit': commit, 'files': files,
            'sourcePatterns': patterns, 'sourceExclusions': exclusions,
            'localTree': tree, 'localExclusions': cache_exclusions(root, tree, files)}


def declarations(root=ROOT):
    rows, failures, inputs = [], [], []
    for kind in SOURCES:
        record_path = 'drafts/' + kind + '/source.json'
        failure = {'id': 'shared-staged-' + kind, 'consumer': CONSUMER,
                   'class': 'copied-tree', 'record': record_path,
                   'localComparison': 'not-run', 'files': []}
        try:
            raw = (root / record_path).read_bytes()
            inputs.append({'path': record_path, 'sha256': hashlib.sha256(raw).hexdigest()})
            rows.append(normalize(kind, json.loads(raw), root))
        except (FileNotFoundError, IncompleteDeclaration) as exc:
            failures.append(dict(failure, verdict='ABSENT', reason=str(exc)))
        except DeclarationError as exc:
            failures.append(dict(failure, verdict='DRIFT', reason=str(exc)))
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
            failures.append(dict(failure, verdict='QUERY_FAILED', reason=str(exc)))
    return {'inventoryVersion': 1, 'advisory': True, 'references': rows}, failures, inputs


def audit_current(mapping, root=ROOT):
    table, failures, inputs = declarations(root)
    resolver = ENGINE.Checkouts(mapping)  # No GitHub API fallback, including missing mappings.
    results = [ENGINE.audit(row, resolver, root) for row in table['references']] + failures
    return {'inventoryVersion': 1, 'advisory': True, 'wrote': [],
            'inventorySource': 'current staged source.json declarations',
            'declarationRecords': inputs, 'references': results,
            'declaredFiles': sum(len(row['files']) for row in table['references']),
            'scope': 'Staged copied draft trees only; candidate parity/conformance and dated inventory remain separate.'}


def plan(root=ROOT):
    table, failures, inputs = declarations(root)
    pending = [{'id': r['id'], 'consumer': CONSUMER, 'class': r['class'],
                'record': r['record'], 'verdict': 'QUERY_FAILED', 'localComparison': 'not-run',
                'reason': 'Authority audit was not completed; retained from validated setup plan.'}
               for r in table['references']]
    return {'advisory': True, 'wrote': [], 'planOnly': True,
            'declarationRecords': inputs, 'failures': failures,
            'sources': [{'id': r['id'], 'repository': r['repository'], 'commit': r['revision']}
                        for r in table['references']], 'references': failures + pending}


def emit(report, output=None):
    text = json.dumps(report, indent=2) + '\n'
    if output:
        output = output.resolve()
        if output.is_relative_to(ROOT.resolve()):
            raise ValueError('Audit output must remain outside the source checkout')
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', dir=output.parent, delete=False) as stream:
            stream.write(text)
            temporary = Path(stream.name)
        temporary.replace(output)
    print(text, end='')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', action='append', default=[], metavar='OWNER/REPO=PATH')
    parser.add_argument('--plan', action='store_true', help='validate current declarations before authority checkout')
    parser.add_argument('--github-output', type=Path, help='explicit workflow output file for validated source commits')
    parser.add_argument('--plan-output', type=Path, help='atomic setup/fallback report outside the source checkout')
    parser.add_argument('--report-output', type=Path, help='atomic audit report outside the source checkout')
    parser.add_argument('--exit-on-findings', action='store_true', help='controlled fixtures only; real audits remain advisory')
    args = parser.parse_args()
    for output in (args.plan_output, args.report_output):
        if output:
            if output.resolve().is_relative_to(ROOT.resolve()):
                parser.error('Audit output must remain outside the source checkout')
            output.unlink(missing_ok=True)
    if args.plan:
        report = plan()
        emit(report, args.plan_output)
        if report['failures']:
            return 1
        if args.github_output:
            with args.github_output.open('a') as stream:
                for source in report['sources']:
                    stream.write(source['id'].removeprefix('shared-staged-') + '_commit=' + source['commit'] + '\n')
        return 0
    if not args.checkout:
        parser.error('Offline audit requires explicit --checkout mappings; no network fallback')
    mapping = dict(value.split('=', 1) for value in args.checkout)
    report = audit_current(mapping)
    emit(report, args.report_output)
    return int(args.exit_on_findings and any(row['verdict'] != 'FRESH' for row in report['references']))


if __name__ == '__main__':
    raise SystemExit(main())
