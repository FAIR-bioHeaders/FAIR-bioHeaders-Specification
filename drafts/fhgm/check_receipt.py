# SPDX-License-Identifier: MPL-2.0
"""Check an actual dual-base receipt, including earned states and count attribution."""
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'upstream/development/conformance/manifest.json'


def problems(receipt):
    manifest = json.loads(MANIFEST.read_text())
    expected = {v['id']: v['evidenceExpectation']['model'] for v in manifest['vectors']}
    rows = receipt.get('vectors', [])
    errors = []
    if receipt.get('status') != 'completed':
        errors.append('receipt did not complete')
    lanes = Counter((row['id'], 'matrix' if 'method' in row else 'sealed') for row in rows)
    wanted_lanes = Counter({(key, lane): 1 for key in expected for lane in ('sealed', 'matrix')})
    if lanes != wanted_lanes:
        errors.append('receipt does not contain each vector once per base lane')
    for row in rows:
        actual = row.get('actualEvidence')
        if not actual or row.get('gff3') == 'skipped' or not row.get('matched'):
            errors.append('missing, skipped or mismatched actual evidence: ' + row['id'])
            continue
        model = actual['fullModel']['status']
        if model != expected.get(row['id']):
            errors.append('earned model state differs: ' + row['id'])
        if model == 'pass':
            for index, snapshot in enumerate(actual['snapshots']):
                required = [f'K{n}' for n in range(1, 7 if index == 0 else 6)]
                if any(snapshot['rules'][rule]['status'] != 'pass' for rule in required):
                    errors.append('full pass without required snapshot predicates: ' + row['id'])
                if any(snapshot['layers'][layer]['status'] != 'pass' for layer in ('base', 'checksum')):
                    errors.append('full pass without snapshot base/integrity prerequisites: ' + row['id'])
    measured = [row for row in rows if row.get('actualEvidence')]
    counts = {
        'vectorsVisited': len(rows),
        'rulePredicatesEvaluated': sum(rule['status'] in ('pass', 'reject')
            for row in measured for rule in row['actualEvidence']['snapshots'][0]['rules'].values()),
        'layerExpectationsCompared': sum(3 + (row['gff3'] != 'skipped') for row in measured),
        'completeVectorsMatched': sum(bool(row['matched'] and row['gff3'] != 'skipped'
            and row['actualEvidence']['fullModel']['status'] in ('pass', 'reject')) for row in measured),
        'completeModelPasses': sum(row['actualEvidence']['fullModel']['status'] == 'pass' for row in measured),
    }
    if counts != receipt.get('counts'):
        errors.append('aggregate evidence counts do not match actual predicates/states')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt', type=Path)
    parser.add_argument('--exercise-guards', action='store_true')
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    errors = problems(receipt)
    if errors:
        parser.exit(1, '\n'.join(errors) + '\n')
    if args.exercise_guards:
        bad = deepcopy(receipt)
        target = next(row for row in bad['vectors']
                      if row['actualEvidence']['fullModel']['status'] == 'not-run')
        target['actualEvidence']['fullModel']['status'] = 'pass'
        if not problems(bad):
            parser.exit(1, 'guard missed fabricated pass on unavailable evidence\n')
        bad = deepcopy(receipt)
        bad['counts']['completeVectorsMatched'] += 1
        if not problems(bad):
            parser.exit(1, 'guard missed an inflated complete-vector count\n')
        bad = deepcopy(receipt)
        bad['vectors'][0]['gff3'] = 'skipped'
        if not problems(bad):
            parser.exit(1, 'guard missed a skipped GFF3 layer\n')
        bad = deepcopy(receipt)
        target = next(row for row in bad['vectors'] if
                      row['actualEvidence']['fullModel']['status'] == 'pass'
                      and len(row['actualEvidence']['snapshots']) > 1)
        target['actualEvidence']['snapshots'][1]['rules']['K4']['status'] = 'not-run'
        if not problems(bad):
            parser.exit(1, 'guard missed unavailable supplied-history K4 evidence\n')
        print('Detected fabricated-pass, inflated-count, skipped-layer and missing-history-predicate controls.')
    print(json.dumps(receipt['counts'], sort_keys=True))
    print('Verified actual dual-base draft evidence; no release or curator acceptance implied.')


if __name__ == '__main__':
    main()
