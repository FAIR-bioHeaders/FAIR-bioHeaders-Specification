#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Generate/check D9/D10 reader-policy cases and measure an actual toolkit.

This supplementary corpus distinguishes metadata validation from file checksum
verification. Its expectations come from adopted clauses, never toolkit output.
"""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import zlib
import yaml

import make_conformance as builder
import check_conformance as shared

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'conformance/reader-policy'
CANONICAL = 'A' * 43 + '='
NONCANONICAL = 'A' * 42 + 'B='


def strict_gzip(data):
    """All complete members, verified FHCRC/CRC/ISIZE, optional trailing NULs."""
    output = b''
    members = 0
    while data:
        if not data.strip(b'\0'):
            if not members:
                raise ValueError('No gzip member')
            return output
        if not data.startswith(b'\x1f\x8b'):
            raise ValueError('Trailing non-gzip bytes')
        engine = zlib.decompressobj(31)
        try:
            output += engine.decompress(data) + engine.flush()
        except zlib.error as exc:
            raise ValueError('Invalid gzip member/header CRC') from exc
        if not engine.eof:
            raise ValueError('Truncated gzip member')
        data = engine.unused_data
        members += 1
    if not members:
        raise ValueError('No gzip member')
    return output


def canonical(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9+/]{42}[AEIMQUYcgkosw048]=', value):
        return False
    return base64.b64encode(base64.b64decode(value, validate=True)).decode() == value


def checksum_values(record):
    # Only typed checksum fields are normative. An arbitrary extension object
    # named "checksum" does not acquire standard-field semantics.
    yield 'checksum', record.get('checksum')
    for index, parent in enumerate(record.get('derivedFrom', [])):
        yield f'derivedFrom/{index}/checksum', parent.get('checksum')


def yaml_record(text):
    class Loader(yaml.SafeLoader):
        pass
    Loader.yaml_implicit_resolvers = {
        first: [(tag, pattern) for tag, pattern in rules if tag != 'tag:yaml.org,2002:timestamp']
        for first, rules in yaml.SafeLoader.yaml_implicit_resolvers.items()}
    if any(re.match(r'^(?:%YAML(?:\s|$)|%TAG(?:\s|$)|---(?:\s|$))', line)
           for line in text.split('\n')):
        raise ValueError('R12 directives/document marker are refused')
    return yaml.load(text, Loader=Loader)


def header_record(data, kind):
    prefix = shared.PREFIXES[kind]
    text = '\n'.join(data[start:end][len(prefix):].rstrip(b'\r\n').decode()
                     for start, end in shared.split_lines(data)
                     if data[start:end].startswith(prefix))
    return yaml_record(text)


def observe(data, case):
    try:
        if case['operation'] == 'metadata':
            record = yaml_record(data.decode()) if case.get('serialization') == 'yaml' else json.loads(data)
        else:
            if case.get('compression'):
                data = strict_gzip(data)
            record = header_record(data, case['format'])
            stated, computed = shared.fhr_checksum(data, case['format'])
            if stated != computed:
                return 'invalid'
        if not isinstance(record, dict):
            return 'invalid'
        _, release, schema = shared.select_record(record)
        if release is None:
            return 'unsupported-version'
        validator = shared.schema_validator(shared.load_schema(release, schema))
        if not validator.is_valid(record):
            return 'invalid'
        return 'valid' if all(canonical(value) for _, value in checksum_values(record)) else 'invalid'
    except (ValueError, UnicodeError, yaml.YAMLError):
        return 'invalid'


def build():
    cases, payloads = [], {}
    def add(identity, data, expected, rule, kind, operation='file', compression=None, note='', serialization=None):
        suffix = ('.yaml' if serialization == 'yaml' else '.json') if operation == 'metadata' else builder.SUFFIX[kind] + ('.gz' if compression else '')
        name = 'payloads/' + identity + suffix
        payloads[name] = data
        cases.append(dict(id=identity, file=name, sha256=hashlib.sha256(data).hexdigest(),
                          expected=expected, rule=rule, format=kind,
                          operation=operation, compression=compression, description=note))
        if serialization:
            cases[-1]['serialization'] = serialization
    for typ, source in [('fhr', 'examples/minimal.fhr.json'),
                        ('fhp', 'examples/fhp/minimal-predicted.fhp.json'),
                        ('fhgff3', 'examples/fhgff3/minimal-reference.fhgff3.json')]:
        record = json.loads((ROOT / source).read_text())
        record['checksum'] = CANONICAL
        def metadata(suffix, value, expected, rule):
            add(f'{typ}-metadata-{suffix}', (json.dumps(value, indent=2) + '\n').encode(),
                expected, rule, typ, 'metadata', note='Synthetic metadata only; no file identity/parent verification claim.')
            add(f'{typ}-metadata-{suffix}-yaml', ('\n'.join(builder.yaml_lines(value)) + '\n').encode(),
                expected, rule, typ, 'metadata', serialization='yaml',
                note='YAML metadata only; same typed record and clause expectation as its JSON twin.')
        metadata('canonical-checksum', record, 'valid', 'R4')
        changed = copy.deepcopy(record); changed['checksum'] = NONCANONICAL
        metadata('noncanonical-checksum', changed, 'invalid', 'R4')
        if typ != 'fhr':
            for suffix, value, expected in [('canonical-parent', CANONICAL, 'valid'),
                                            ('noncanonical-parent', NONCANONICAL, 'invalid')]:
                changed = copy.deepcopy(record)
                changed['derivedFrom'] = [{'headerType': 'FHR', 'relationship': 'translatedFrom' if typ == 'fhp' else 'annotates', 'checksum': value}]
                metadata(suffix, changed, expected, 'R4')
            for release, expected in [('v0.4.0', 'invalid'), ('v0.3.1', 'unsupported-version'), ('v99.0.0', 'unsupported-version')]:
                changed = copy.deepcopy(record)
                changed['schema'] = f'https://w3id.org/fair-bioheaders/{typ}/{release}'
                metadata('selection-' + release.replace('.', '-'), changed, expected, 'V3' if expected == 'invalid' else 'V4')
    templates = [('fasta', None, lambda _: builder.header('fasta') + builder.body('fasta')),
                 ('gfa', None, lambda _: builder.header('gfa') + builder.body('gfa')),
                 ('fhp-fasta', builder.FHP_RECORD, builder.fhp_lines),
                 ('fhgff3', builder.FHGFF3_RECORD, builder.fhgff3_lines)]
    for kind, template, lines_for in templates:
        record = copy.deepcopy(template)
        if record:
            for parent in record.get('derivedFrom', []):
                parent['checksum'] = CANONICAL
        lines = lines_for(record)
        plain, value = builder.assemble(lines)
        add(kind + '-policy-plain-control', plain, 'valid', 'R12', kind)
        quoted = copy.deepcopy(lines)
        prefix = builder.PREFIX[kind]
        for index, line in enumerate(quoted):
            if line.text.startswith(prefix + b'documentation:'):
                quoted[index] = builder.Line(prefix + b'documentation: "%YAML 1.1; %TAG !e! tag:example.com,2000:; ---"')
        text_control, _ = builder.assemble(quoted)
        add(kind + '-policy-quoted-directive-text', text_control, 'valid', 'R12', kind,
            note='Quoted scalar text is not a directive or document-start token.')
        for suffix, directive in [('yaml-1-1', '%YAML 1.1'), ('yaml-1-2', '%YAML 1.2'),
                                  ('tag', '%TAG !e! tag:example.com,2000:'), ('document-marker', None)]:
            changed = copy.deepcopy(lines)
            position = 1 if kind == 'fhgff3' else 0
            extra = ([builder.Line(builder.PREFIX[kind] + directive.encode())] if directive else []) + [builder.Line(builder.PREFIX[kind] + b'---')]
            changed[position:position] = extra
            data, _ = builder.assemble(changed)
            add(kind + '-policy-' + suffix, data, 'invalid', 'R12', kind,
                note='Selected D10 format policy: directives/document-start markers are refused.')
        if record:
            changed = copy.deepcopy(record)
            changed['derivedFrom'][0]['checksum'] = NONCANONICAL
            data, _ = builder.assemble(lines_for(changed))
            add(kind + '-policy-noncanonical-parent', data, 'invalid', 'R4', kind,
                note='Root file checksum is correct; only the nested parent encoding is noncanonical.')
    plain, _ = builder.standard('fasta')
    member = builder.gzip_member(plain)
    # FNAME + FCOMMENT + FHCRC; RFC1952 stores the low 16 bits of header CRC32.
    header = b'\x1f\x8b\x08\x1a\0\0\0\0\0\xff' + b'synthetic.fa\0header control\0'
    crc = struct.pack('<H', zlib.crc32(header) & 0xffff)
    good_crc = header + crc + member[10:]
    bad_crc = header + bytes([crc[0] ^ 1, crc[1]]) + member[10:]
    for suffix, data, expected in [('member', member, 'valid'),
                                   ('trailing-garbage', member + b'garbage', 'invalid'),
                                   ('trailing-nul', member + b'\0' * 16, 'valid'),
                                   ('fhcrc-correct', good_crc, 'valid'),
                                   ('fhcrc-wrong', bad_crc, 'invalid'),
                                   ('multimember-trailing-nul', builder.multimember_gzip(plain, 80) + b'\0' * 16, 'valid')]:
        add('fasta-policy-gzip-' + suffix, data, expected, 'R1', 'fasta', compression='gzip',
            note='Transport policy; checksum covers the identical decompressed carrier bytes.')
    return {'corpusVersion': 1, 'decision': 'https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7017854934',
            'note': 'Supplementary reader/runtime cases; separate from the main carrier-suite count. Published schema bytes are unchanged.',
            'cases': cases}, payloads


def toolkit_observation(executable, location, case):
    command = [str(executable), 'validate' if case['operation'] == 'metadata' else 'verify', str(location)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        text = (result.stdout + result.stderr).strip()
        if result.returncode == 0:
            actual = 'valid'
        elif result.returncode != 1 or not text or 'Traceback (most recent call last)' in text:
            actual = 'execution-error'
        elif 'unsupported schema version' in text.lower():
            actual = 'unsupported-version'
        else:
            actual = 'invalid'
        code = result.returncode
    except (OSError, subprocess.TimeoutExpired) as error:
        actual, code, text = 'execution-error', None, str(error)
    return {'id': case['id'], 'expected': case['expected'], 'actual': actual,
            'matched': actual == case['expected'], 'exit': code, 'diagnostic': text}


def receipt_problems(expected, actual, strict_exit, corpus_digest):
    """Calibrate the named old release's actual gaps, never certify conformity."""
    problems = []
    if expected.get('corpusSha256') != corpus_digest:
        problems.append('Published receipt belongs to different corpus bytes')
    if strict_exit != expected.get('exit'):
        problems.append('Strict runtime exit changed')
    if actual.get('cases') != expected.get('cases') or actual.get('problems') != expected.get('problems'):
        problems.append('Clause/actual mismatch set changed')
    rows = actual.get('runtime', [])
    known = {r['id']: r for r in expected['runtime']}
    if len(rows) != len(known) or {r['id'] for r in rows} != set(known):
        problems.append('Runtime receipt has missing/extra/duplicate cases')
    for row in rows:
        if row['id'] in known and any(row.get(k) != known[row['id']].get(k)
                for k in ('expected', 'actual', 'matched', 'exit')):
            problems.append(row['id'] + ': named published-release observation changed')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--toolkit', type=Path, help='Actual installed bioheaders executable; mismatches exit 1, never skipped')
    parser.add_argument('--verify-published-receipt', type=Path,
                        help='calibrate exact known published-release observations; not a conformity pass')
    args = parser.parse_args(argv)
    if args.verify_published_receipt and not args.toolkit:
        parser.error('--verify-published-receipt requires --toolkit')
    manifest, payloads = build()
    encoded = (json.dumps(manifest, indent=2) + '\n').encode()
    files = {**payloads, 'cases.json': encoded}
    if args.write:
        for name, data in files.items():
            target = args.output / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    problems, observed = [], []
    for name, data in files.items():
        target = args.output / name
        if not target.is_file() or target.read_bytes() != data:
            problems.append(name + ': differs from deterministic generation')
    for case in manifest['cases']:
        outcome = observe(payloads[case['file']], case)
        if outcome != case['expected']:
            problems.append(case['id'] + ': independent clause oracle returned ' + outcome)
        if args.toolkit:
            observation = toolkit_observation(args.toolkit, args.output / case['file'], case)
            observed.append(observation)
            if not observation['matched']:
                problems.append(case['id'] + ': actual toolkit returned ' + observation['actual'])
    report = {'cases': len(manifest['cases']), 'problems': problems, 'runtime': observed}
    strict_exit = int(bool(problems))
    if args.verify_published_receipt:
        failures = receipt_problems(json.loads(args.verify_published_receipt.read_text()),
                                    report, strict_exit, hashlib.sha256(encoded).hexdigest())
        report.update(strictRuntimeExit=strict_exit, runtimeConformance=not problems,
                      publishedReceiptMatched=not failures, receiptProblems=failures)
        print(json.dumps(report, indent=2))
        return int(bool(failures))
    print(json.dumps(report, indent=2))
    return strict_exit


if __name__ == '__main__':
    raise SystemExit(main())
