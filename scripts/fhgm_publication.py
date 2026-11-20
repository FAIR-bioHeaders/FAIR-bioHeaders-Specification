#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Verify the unpublished native FHGM 0.1 counterpart; optionally run its full suite."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path('model-contracts/fhgm/0.1')
IDENTITY = 'https://w3id.org/fair-bioheaders/model-contracts/fhgm/0.1'
ANNOTATIONS = {'title': 'FHGM native gene-model record contract 0.1',
 'description': 'Native FHGM model record selected independently of its enclosing FHGFF3 file '
                'header. The native contract defines record structure; the separate model-level '
                'checker establishes model ID uniqueness, eligible feature-target resolution, '
                'record/file reference agreement and bounded immediate-predecessor resolution. '
                'Base-header validity, exact-byte integrity, feature/biology validity and curator '
                'acceptance remain separate outcomes. The reviewed source and development '
                'decisions are preserved at '
                'https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/d9d131a02b042023f4784d842a874232fc891069/development/CONTRACT-REVIEW.md. '
                'Model-contract selection introduces no FHGM header schemaVersion or in-record '
                'schema field.'}
SOURCE_COMMIT = 'd9d131a02b042023f4784d842a874232fc891069'
SOURCE_MANIFEST_SHA256 = '16cd2d029424877305b63b689a415632ab2b1b3443ee435d11e23ef6c1a2efa4'
SOURCE_SCHEMA_SHA256 = 'b7075e5872e0a5ffce5ae61c590ce182f1f219fa269413cad3b1a966753cfeae'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def typed_json(value):
    """Canonical JSON text retains bool/number and integer/float distinctions."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def verify(root=ROOT):
    """Fail on semantic drift, source-set omission or altered accepted source bytes."""
    errors = []
    candidate = root / 'drafts/fhgm'
    source_bytes = (candidate / 'source.json').read_bytes()
    if digest(source_bytes) != SOURCE_MANIFEST_SHA256:
        return ['accepted source manifest differs from immutable publication authority']
    source = json.loads(source_bytes)
    if source['source']['commit'] != SOURCE_COMMIT:
        errors.append('wrong owning source commit')
    expected = {entry['local'] for entry in source['files']}
    actual = {str(file.relative_to(candidate)) for file in (candidate / 'upstream').rglob('*')
              if file.is_file() and '__pycache__' not in file.parts and not file.name.endswith('.pyc')}
    if expected != actual:
        errors.append('accepted source file set differs')
    for entry in source['files']:
        file = candidate / entry['local']
        if file.is_symlink() or not file.is_file():
            errors.append('missing or symlink source: ' + entry['local'])
        elif len(file.read_bytes()) != entry['bytes'] or digest(file.read_bytes()) != entry['sha256']:
            errors.append('changed accepted source: ' + entry['local'])
    source_schema = candidate / 'upstream/development/model/fhgm-model.schema.json'
    if digest(source_schema.read_bytes()) != SOURCE_SCHEMA_SHA256:
        errors.append('wrong source native schema')
    package = root / PACKAGE
    native_file = package / 'fhgm-model.schema.json'
    if native_file.is_symlink():
        errors.append('native schema must not be a symlink')
    native_bytes = native_file.read_bytes()
    native = json.loads(native_bytes)
    if native.pop('$id', None) != IDENTITY:
        errors.append('native schema has wrong model-contract identity')
    original = json.loads(source_schema.read_bytes())
    for key, wanted in ANNOTATIONS.items():
        if typed_json(native.get(key)) != typed_json(wanted):
            errors.append('native counterpart has unexpected root annotation: ' + key)
        native[key] = original[key]
    if typed_json(native) != typed_json(original):
        errors.append('native counterpart changes validation semantics or unapproved annotations')
    metadata = json.loads((package / 'publication.json').read_bytes())
    for field, wanted in [('publicationState', 'candidate-unpublished'),
                          ('kind', 'native-model-contract'), ('modelContractVersion', '0.1'),
                          ('intendedRelease', 'v0.8.0'), ('identity', IDENTITY),
                          ('artifact', 'fhgm-model.schema.json'), ('sha256', digest(native_bytes))]:
        if metadata.get(field) != wanted:
            errors.append('wrong publication metadata: ' + field)
    if metadata.get('source', {}).get('commit') != SOURCE_COMMIT:
        errors.append('publication metadata names wrong owning commit')
    if metadata.get('source', {}).get('sha256') != SOURCE_SCHEMA_SHA256:
        errors.append('publication metadata names wrong owning schema digest')
    if metadata.get('source', {}).get('sourceManifestSha256') != SOURCE_MANIFEST_SHA256:
        errors.append('publication metadata names wrong source manifest digest')
    manifest = json.loads((candidate / 'upstream/development/conformance/manifest.json').read_bytes())
    if metadata.get('suite', {}).get('expectedNotRunVisits') != 10:
        errors.append('expected ten explicitly not-run dual-base visits')
    if len(manifest['vectors']) != 92 or metadata.get('suite', {}).get('vectorCount') != 92:
        errors.append('expected the accepted 92-vector suite')
    return errors


def prepare_snapshot(root, destination):
    """Create an explicit private counterpart, leaving every mirrored byte intact.

    The unchanged owning runner verifies artifact provenance before running.
    Rebind only its native schema's digest/size in the private provenance copy;
    the accepted expectations, IDs, checker, vectors and generators stay exact.
    """
    shutil.copytree(root / 'drafts/fhgm/upstream', destination,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    native = (root / PACKAGE / 'fhgm-model.schema.json').read_bytes()
    relative = 'development/model/fhgm-model.schema.json'
    (destination / relative).write_bytes(native)
    record_file = destination / 'development/conformance/provenance.json'
    provenance = json.loads(record_file.read_bytes())
    matches = [entry for entry in provenance['contractArtifacts'] if entry['local'] == relative]
    if len(matches) != 1 or matches[0]['sha256'] != SOURCE_SCHEMA_SHA256:
        raise ValueError('native schema provenance is not the accepted exact source')
    matches[0].update(sha256=digest(native), size=len(native))
    record_file.write_text(json.dumps(provenance, indent=2) + '\n')


def run_conformance(bases, validator, report, root=ROOT):
    errors = verify(root)
    if errors:
        raise ValueError('\n'.join(errors))
    if len(bases) != 2 or not validator.is_file():
        raise ValueError('supply both released base files and an actual gff3-validate executable')
    report = report.resolve()
    if report.exists():
        raise ValueError('receipt already exists; choose a fresh output path')
    with tempfile.TemporaryDirectory(prefix='fhgm-native-publication-') as directory:
        snapshot = Path(directory) / 'upstream'
        prepare_snapshot(root, snapshot)
        command = [sys.executable, str(snapshot / 'development/conformance/run_conformance.py')]
        for base in bases:
            command.extend(['--base-schema', str(base.resolve())])
        command.extend(['--matrix', '--gff3-validate', str(validator.resolve()), '--report-json', str(report)])
        subprocess.run(command, check=True, cwd=snapshot)
    subprocess.run([sys.executable, str(root / 'drafts/fhgm/check_receipt.py'), str(report),
                    '--exercise-guards'], check=True)
    receipt = json.loads(report.read_bytes())
    receipt['nativeContract'] = {'identity': IDENTITY, 'path': str(PACKAGE / 'fhgm-model.schema.json'),
                                 'sha256': digest((root / PACKAGE / 'fhgm-model.schema.json').read_bytes()),
                                 'sourceCommit': SOURCE_COMMIT, 'status': 'candidate-unpublished'}
    report.write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-conformance', action='store_true')
    parser.add_argument('--base-schema', type=Path, action='append', default=[])
    parser.add_argument('--gff3-validate', type=Path)
    parser.add_argument('--report-json', type=Path)
    args = parser.parse_args()
    try:
        errors = verify()
        if errors:
            parser.exit(1, '\n'.join(errors) + '\n')
        if args.run_conformance:
            if args.gff3_validate is None or args.report_json is None:
                parser.error('--run-conformance requires --gff3-validate and --report-json')
            receipt = run_conformance(args.base_schema, args.gff3_validate, args.report_json)
            print(json.dumps(receipt['counts'], sort_keys=True))
        else:
            print('Native FHGM 0.1 identity/annotation-only counterpart verified; publication remains gated.')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
