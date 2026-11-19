# SPDX-License-Identifier: MPL-2.0
"""Verify the exact owning draft dependency tree; optionally compare pinned git blobs."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

HERE = Path(__file__).resolve().parent


def selected(paths, selection):
    return {p for p in paths if p in selection['files']
            or any(p.startswith(prefix) for prefix in selection['prefixes'])}


def verify(root=HERE, upstream=None):
    record = json.loads((root / 'source.json').read_text())
    problems = []
    entries = record['files']
    source_paths = [entry['source'] for entry in entries]
    local_paths = [entry['local'] for entry in entries]
    if len(set(source_paths)) != len(entries) or len(set(local_paths)) != len(entries):
        problems.append('duplicate source or local path')
    actual = {p.relative_to(root).as_posix() for p in (root / 'upstream').rglob('*')
              if p.is_file() and '__pycache__' not in p.parts}
    if actual != set(local_paths):
        problems.append('copied file set differs: missing=' + str(sorted(set(local_paths) - actual))
                        + '; extra=' + str(sorted(actual - set(local_paths))))
    for entry in entries:
        if (entry['local'] != 'upstream/' + entry['source']
                or '..' in PurePosixPath(entry['source']).parts
                or PurePosixPath(entry['source']).is_absolute()):
            problems.append('unsafe or remapped source path: ' + entry['source'])
            continue
        file = root / entry['local']
        if not file.is_file() or file.is_symlink():
            problems.append('missing/nonregular copied file: ' + entry['local'])
            continue
        data = file.read_bytes()
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            problems.append('copied bytes differ: ' + entry['local'])
    if upstream is not None:
        commit = record['source']['commit']
        def git(*args):
            return subprocess.check_output(['git', '-C', str(upstream), *args])
        if git('rev-parse', 'HEAD').decode().strip() != commit:
            problems.append('upstream checkout HEAD is not the recorded suite/contract commit')
        listed = git('ls-tree', '-r', '--name-only', commit).decode().splitlines()
        expected = selected(listed, record['source']['selection'])
        if expected != set(source_paths):
            problems.append('source selection set differs from pinned tree')
        for entry in entries:
            if entry['source'] in expected:
                authoritative = git('show', commit + ':' + entry['source'])
                local = root / entry['local']
                if not local.is_file() or local.read_bytes() != authoritative:
                    problems.append('pinned git blob differs: ' + entry['source'])
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path)
    args = parser.parse_args()
    problems = verify(upstream=args.upstream)
    if problems:
        parser.exit(1, '\n'.join(problems) + '\n')
    data = json.loads((HERE / 'source.json').read_text())
    print(f"Verified {len(data['files'])} exact owning draft files at {data['source']['commit']}")
    print('Unpublished review candidate; no contract alias, header identity or release is created.')


if __name__ == '__main__':
    main()
