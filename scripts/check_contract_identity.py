#!/usr/bin/env python3
"""Preflight future published contract identifiers; never rewrite legacy bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check(data, name, ledger):
    digest = hashlib.sha256(data).hexdigest()
    if any(r['path'] == name and r['sha256'] == digest for r in ledger['artifacts']):
        return 'preserved-release', None
    contract = json.loads(data)
    identity = contract.get('$id')
    if not isinstance(identity, str) or not re.fullmatch(
            r'https://w3id\.org/fair-bioheaders/[a-z0-9-]+/v[0-9]+\.[0-9]+\.[0-9]+/?', identity):
        return 'refused', 'New or changed published bytes require a reviewed stable versioned w3id identity'
    return 'stable-identity-candidate', None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('schema', type=Path)
    parser.add_argument('--ledger', type=Path, default=ROOT / 'references/released-identities.json')
    args = parser.parse_args()
    state, error = check(args.schema.read_bytes(), args.schema.name,
                         json.loads(args.ledger.read_text()))
    print(json.dumps({'path': str(args.schema), 'state': state, 'error': error,
                      'publicationAuthorized': False}))
    return int(error is not None)


if __name__ == '__main__':
    raise SystemExit(main())
