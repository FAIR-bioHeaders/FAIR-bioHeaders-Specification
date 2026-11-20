#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Build/check immutable-ID FHT release counterparts; never publish or repin."""
import argparse
import base64
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / 'drafts/fht/upstream'
TARGET = ROOT / 'conformance/fht-v0.7.0'
RAW_DRAFT = b'https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json'
SELECTOR = b'https://w3id.org/fair-bioheaders/fht/v0.7.0'
COMMIT = '4ddda69cbcbb3920a06ab657173c0198672cd7bf'


def module(name, source):
    spec = importlib.util.spec_from_file_location(name, source)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def owning_reader():
    # Frozen dependency imports are selected deliberately, rather than from an
    # unrelated local toolkit. Nothing in the immutable snapshot is modified.
    sys.path.insert(0, str(OWNER / 'scripts'))
    return module('accepted_fht_fixture_reader', OWNER / 'scripts/check_fht_fixtures.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def deterministic_gzip(data):
    compressed = bytearray(gzip.compress(data, mtime=0))
    compressed[9] = 255
    return bytes(compressed)


def sequence_transform(data, transform):
    transformed, in_fasta = [], False
    for line in data.splitlines(keepends=True):
        content = line.rstrip(b'\r\n')
        ending = line[len(content):]
        if content.startswith(b'>'):
            in_fasta = True
        elif in_fasta and content and not content.startswith(b';'):
            content = transform(content)
        transformed.append(content + ending)
    return b''.join(transformed)


def named_faulty_checksum(data, source_id, reader):
    if source_id == 'fht-fasta-crlf-normalized-checksum':
        return reader.recomputed(data.replace(b'\r\n', b'\n'))
    if source_id == 'fht-fasta-u-normalized-checksum':
        normalized = sequence_transform(data, lambda line: line.replace(b'U', b'T').replace(b'u', b't'))
        return reader.recomputed(normalized)
    if source_id == 'fht-fasta-case-normalized-checksum':
        return reader.recomputed(sequence_transform(data, bytes.upper))
    if source_id in ('fht-fasta-checksum-sha256', 'fht-fasta-checksum-truncated-sha512'):
        _, position, length = reader.locate_checksum(data)
        covered = data[:position] + data[position + length:]
        algorithm = 'sha256' if source_id == 'fht-fasta-checksum-sha256' else 'sha512'
        digest = hashlib.new(algorithm, covered).digest()
        if algorithm == 'sha512':
            digest = digest[:32]
        return base64.b64encode(digest).decode('ascii')
    return None


def counter_bytes(original, compressed, reader, source_id=None):
    try:
        data = reader.decompress(original) if compressed else original
    except reader.CompressionError:
        # Preserve the primary compression defect and its exact bytes. The
        # rejection occurs before selection; this is not released FHT support.
        return original, 'unreadable compression preserved; selection not run'
    before = data
    data = data.replace(RAW_DRAFT, SELECTOR)
    if data == before:
        return original, 'selector unchanged; explicit selection outcome retained'
    try:
        stated, position, length = reader.locate_checksum(data)
        computed = reader.recomputed(data)
        source_stated = reader.locate_checksum(before)[0]
        matched = source_stated == reader.recomputed(before)
        replacement = named_faulty_checksum(data, source_id, reader)
        if replacement is not None:
            if replacement == computed:
                raise AssertionError(source_id + ': named faulty checksum unexpectedly matches')
            policy = 'shared release selector; named faulty checksum preserved'
        else:
            # Preserve deliberate checksum mismatch, rather than repairing a C2/R3
            # rejection. Only the unique root line changes, never a parent's digest.
            replacement = computed if matched else ('A' if computed[0] != 'A' else 'B') + computed[1:]
            policy = 'shared release selector; root digest recomputed' if matched else 'shared release selector; checksum defect preserved'
        line = data[position:position + length]
        data = data[:position] + line.replace(stated.encode(), replacement.encode(), 1) + data[position + length:]
    except ValueError:
        policy = 'shared release selector; malformed checksum/header defect preserved'
    return (deterministic_gzip(data) if compressed else data), policy


def outputs():
    reader = owning_reader()
    source = json.loads((OWNER / 'conformance/manifest.json').read_text())
    result, vectors = {}, []
    for entry in source['vectors']:
        original = (OWNER / 'conformance' / entry['file']).read_bytes()
        data, policy = counter_bytes(original, entry['compressed'], reader, entry['id'])
        identity = 'fht-v070-' + entry['id'].removeprefix('fht-')
        filename = entry['file'].rsplit('/', 1)[-1].replace(entry['id'], identity)
        relative = entry['expected'] + '/' + filename
        result[TARGET / relative] = data
        row = dict(id=identity, file=relative, format='fht-fasta', compressed=entry['compressed'],
                   expected=entry['expected'], sourceId=entry['id'], sourceFile=entry['file'],
                   sourceSha256=sha(original), sha256=sha(data), transformation=policy,
                   rule=entry.get('rule'), rules=entry.get('rules', []),
                   parentLink=entry.get('parentLink', []))
        if entry.get('parentLink'):
            source_record = reader.parse_metadata(reader.decompress(original) if entry['compressed'] else original)
            row['parentClaims'] = source_record.get('derivedFrom', [])
        if entry['id'] in ('fht-fasta-schema-w3id-release-without-fht', 'fht-fasta-schema-shared-raw-tag'):
            row.update(rule='V4', disposition='Previously V5 before FHT registration; named older shared release lacks FHT. Expected invalid remains, rejection is now unsupported-version; historical source unchanged.')
        vectors.append(row)
    manifest = dict(manifestVersion=1, status='FHT v0.7.0 conformance counterparts; publication and installed support are verified separately',
                    sourceCommit=COMMIT, sourceManifestSha256=sha((OWNER / 'conformance/manifest.json').read_bytes()),
                    historicalShared='291 immutable v0.6.0 cases remain separate; current shared carrier lane is also unchanged',
                    sourceCount=93, vectors=vectors)
    result[TARGET / 'manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    return result


def observe(data, entry, reader):
    from check_conformance import select_record, load_schema
    from check_conformance import schema_validator
    from fht_semantics import completeness_errors
    from jsonschema import FormatChecker
    try:
        from reader_policy import strict_gzip, header_record, canonical, checksum_values
        if entry['compressed']:
            data = strict_gzip(data)
        header_record(data, 'fasta')  # Selected R12 directives/document-marker policy.
        stage, rule, detail, record = reader.first_rejection(data)
        if stage:
            return dict(valid=False, stage=stage, rule=rule, detail=detail)
        kind, release, name = select_record(record)
        if release is None:
            return dict(valid=False, stage='selection', rule='V4')
        schema = load_schema(release, name)
        problems = list(schema_validator(schema).iter_errors(record))
        if problems:
            return dict(valid=False, stage='schema', rule='V5' if kind != 'FHT' else 'contract-schema', violations=[dict(keyword=p.validator, path=list(p.absolute_path), message=p.message) for p in problems])
        if not all(canonical(value) for _, value in checksum_values(record)):
            return dict(valid=False, stage='canonical-checksum', rule='R4')
        problems = completeness_errors(record) if kind == 'FHT' else []
        if problems:
            return dict(valid=False, stage='semantics', rule='C1', errors=problems)
        # Preserve the original supplied-history/file-identity context. Parent
        # files remain immutable historical evidence, not promoted new examples.
        parents = []
        derived = record.get('derivedFrom') or []
        if entry['parentLink'] and derived != entry.get('parentClaims'):
            return dict(valid=False, stage='parent-context', rule='C3', detail='Observed child parent claims (digest/type/role/count) differ from immutable source context')
        for link in entry['parentLink']:
            if not any(isinstance(parent, dict) and parent.get('checksum') == link.get('statedChecksum') for parent in derived):
                return dict(valid=False, stage='parent-context', rule='C3', detail='Declared parent context is not present in the parsed child')
            if link['result'] == 'unchecked':
                parents.append('unchecked')
                continue
            source = (OWNER / 'conformance' / link['file']).read_bytes()
            reader.verify_stated(source)
            supplied = reader.parse_metadata(source)
            parent_kind = 'FHT' if supplied.get('schema') == RAW_DRAFT.decode() else select_record(supplied)[0]
            claim = next(parent for parent in derived if parent.get('checksum') == link['statedChecksum'])
            if claim.get('headerType') != parent_kind:
                return dict(valid=False, stage='parent-context', rule='C3', detail='Supplied parent type differs from child claim')
            computed = reader.recomputed(source)
            parents.append('checked-pass' if computed == link['statedChecksum'] else 'checked-fail')
        if 'checked-fail' in parents:
            return dict(valid=False, stage='parent', rule='C3', parentLink=parents)
        return dict(valid=True, stage='complete', parentLink=parents)
    except (ValueError, reader.CompressionError) as error:
        return dict(valid=False, stage='parse-or-compression', detail=str(error))


def assert_expected(entry, data, reader):
    """Preserve independent primary-defect assertions, not just invalid counts."""
    from check_conformance import schema_validator, select_record
    source = json.loads((OWNER / 'conformance/manifest.json').read_text())
    original = next(row for row in source['vectors'] if row['id'] == entry['sourceId'])
    expected = copy.deepcopy(original)
    compression_error = None
    try:
        payload = reader.decompress(data) if entry['compressed'] else data
    except reader.CompressionError as error:
        payload, compression_error = None, error
    if entry['rule'] == 'V4':
        if compression_error:
            raise ValueError(entry['id'] + ': V4 masked by compression')
        stage, _, detail, record = reader.first_rejection(payload)
        if stage or select_record(record) != ('FHT', None, None):
            raise ValueError(entry['id'] + ': V4 masked or not measured: ' + str(detail))
        return
    reader.FAILURES.clear()
    reader.fail = lambda message: reader.FAILURES.append(message)
    reader.VALIDATOR = schema_validator(json.loads((ROOT / 'fht.json').read_text()))
    def selection(record):
        kind, release, name = select_record(record)
        if kind == 'FHT' and name == 'fht.json' and release in ('main', 'v0.7.0'):
            return 'current'
        value = record.get('schema')
        return 'near-miss-fhr' if isinstance(value, str) and any(form.fullmatch(value) for form in reader.RELEASE_FORMS) else 'other-fhr'
    reader.schema_selection = selection
    # Only selector-constraint errors change from the frozen const to the new
    # released URL pattern. Keep every other keyword/path/reason assertion.
    for identity in ('fht-fasta-cites-fhr-schema', 'fht-fasta-cites-arbitrary-url', 'fht-fasta-schema-trailing-line-feed'):
        reader.EXPECTED_SCHEMA_ERRORS[identity] = {('pattern', '$.schema', 'does not match')}
    if expected['expected'] == 'valid':
        expected['checksum'] = reader.locate_checksum(payload)[0]
        pins = expected.get('metadata', {})
        actual = reader.parse_metadata(payload)
        for name in ('schema', 'checksum'):
            if name in pins:
                pins[name] = actual[name]
        reader.check_expected_valid(expected, payload, entry['id'])
    else:
        reader.check_expected_invalid(expected, payload, entry['id'], compression_error)
    if reader.FAILURES:
        raise ValueError(entry['id'] + ': primary rule/context assertions failed: ' + '; '.join(reader.FAILURES))


def root_bindings(schema):
    """The accepted binding table, derived from actual proposed contract nodes."""
    def resolve(part):
        while '$ref' in part:
            value = schema
            for token in part['$ref'][2:].split('/'):
                value = value[token.replace('~1', '/').replace('~0', '~')]
            part = value
        return part
    rows = ['| Field | Contract shape | Required | Binding |', '| --- | --- | --- | --- |']
    for name, raw in schema['properties'].items():
        part = resolve(raw)
        kind = part['type']
        if kind == 'array':
            item = resolve(part['items'])
            shape, binding = 'array of ' + item.get('title', item['type']), 'ordered typed container'
        elif kind == 'object':
            shape, binding = part.get('title', 'object') + ' object', 'typed object scope'
        else:
            shape, binding = 'enum string' if 'enum' in part else kind, 'typed scalar'
        required = 'yes' if name in schema['required'] else 'no'
        rows.append(f'| `{name}` | {shape} | {required} | {binding} |')
    return '\n'.join(rows)


def binding_document():
    path = ROOT / 'docs/FHT-MICRODATA.md'
    text = path.read_text()
    before, rest = text.split('<!-- BEGIN generated root bindings -->', 1)
    _, after = rest.split('<!-- END generated root bindings -->', 1)
    table = root_bindings(json.loads((ROOT / 'fht.json').read_text()))
    return path, before + '<!-- BEGIN generated root bindings -->\n' + table + '\n<!-- END generated root bindings -->' + after


def example_outputs():
    import fht_microdata as binding
    reader = owning_reader()
    results = {}
    target = ROOT / 'examples/fht'
    for location in sorted((OWNER / 'examples').glob('*.fht.json')):
        record = json.loads(location.read_text())
        record['schema'] = SELECTOR.decode()
        fasta = location.with_suffix('.fasta')
        data, _ = counter_bytes(fasta.read_bytes(), False, reader)
        record['checksum'] = reader.locate_checksum(data)[0]
        results[target / fasta.name] = data
        results[target / location.name] = (json.dumps(record, indent=2, ensure_ascii=False) + '\n').encode()
        text = binding.write_page(record, allow_candidate=True, warn=lambda message: None,
            title=location.stem + ' (FHT v0.7.0 synthetic example)', _reference_example=True)
        results[target / location.with_suffix('.html').name] = text.encode()
    return results


def check_examples():
    path, documented = binding_document()
    if path.read_text() != documented:
        raise ValueError('FHT proposed binding root table differs from actual contract')
    expected = example_outputs()
    actual = {p: p.read_bytes() for p in (ROOT / 'examples/fht').rglob('*') if p.is_file()}
    if actual != expected:
        raise ValueError('Generated FHT candidate examples differ')
    return len(expected) // 3


def check():
    expected = outputs()
    actual = {p: p.read_bytes() for p in TARGET.rglob('*') if p.is_file()}
    if actual != expected:
        raise ValueError('FHT candidate generated file set/bytes differ')
    manifest = json.loads(expected[TARGET / 'manifest.json'])
    reader = owning_reader()
    rows = []
    for entry in manifest['vectors']:
        data = expected[TARGET / entry['file']]
        assert_expected(entry, data, reader)
        outcome = observe(data, entry, reader)
        if outcome['valid'] != (entry['expected'] == 'valid'):
            raise ValueError(entry['id'] + ': unexpected outcome ' + str(outcome))
        if entry['rule'] == 'V4' and outcome.get('rule') != 'V4':
            raise ValueError(entry['id'] + ': V4 masked by earlier failure ' + str(outcome))
        rows.append(dict(id=entry['id'], sourceId=entry['sourceId'], **outcome))
    return dict(status='source-contract-conformance', publicationVerified=False, cases=len(rows), valid=sum(row['valid'] for row in rows), results=rows)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--examples', action='store_true', help='include Python3.13 typed HTML counterpart generation/check')
    args = parser.parse_args()
    if args.write:
        if args.examples:
            location, text = binding_document()
            location.write_text(text)
        for location, data in {**outputs(), **(example_outputs() if args.examples else {})}.items():
            location.parent.mkdir(parents=True, exist_ok=True)
            location.write_bytes(data)
    else:
        report = check()
        if args.examples:
            report['examplePairs'] = check_examples()
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
