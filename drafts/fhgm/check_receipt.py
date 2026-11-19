# SPDX-License-Identifier: MPL-2.0
"""Check an actual dual-base receipt, including earned states and count attribution."""
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'upstream/development/conformance/manifest.json'


def snapshot_problems(vector, snapshots):
    """Bind full-pass evidence to every declared input, not only surviving rows.

    The byte-exact owning receipt names history subjects by basename. Distinct
    declared files sharing a basename cannot be distinguished by that interface;
    refuse that ambiguity rather than claiming identity. Repeated references to
    the same canonical file remain countable and must appear equally often.
    Matrix twins use the identical committed predecessors, not rewritten history.
    """
    prior = vector.get('context', {}).get('predecessors', [])
    identities = {}
    expected = ['carrier']
    for relative in prior:
        subject = 'predecessor ' + Path(relative).name
        identities.setdefault(subject, set()).add(str((MANIFEST.parent / relative).resolve()))
        expected.append(subject)
    errors = []
    if any(len(files) > 1 for files in identities.values()):
        errors.append('ambiguous predecessor identity in basename-only receipt: ' + vector['id'])
    subjects = [snapshot.get('subject') for snapshot in snapshots]
    if not subjects or subjects[0] != 'carrier':
        errors.append('full-pass receipt does not begin with carrier: ' + vector['id'])
    if subjects != expected:
        errors.append('full-pass snapshot subjects differ from declared predecessor inputs: ' + vector['id'])
    return errors


def problems(receipt):
    manifest = json.loads(MANIFEST.read_text())
    vectors = {v['id']: v for v in manifest['vectors']}
    expected = {key: v['evidenceExpectation']['model'] for key, v in vectors.items()}
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
        if model == 'reject' and not any(
                rule['status'] == 'reject'
                for rule in actual['snapshots'][0]['rules'].values()):
            errors.append('model rejection without an earned carrier predicate: ' + row['id'])
        if model == 'pass':
            if row['id'] in vectors:
                errors.extend(snapshot_problems(vectors[row['id']], actual.get('snapshots', [])))
            for index, snapshot in enumerate(actual.get('snapshots', [])):
                required = [f'K{n}' for n in range(1, 7 if index == 0 else 6)]
                if any(snapshot['rules'][rule]['status'] != 'pass' for rule in required):
                    errors.append('full pass without required snapshot predicates: ' + row['id'])
                if any(snapshot['layers'][layer]['status'] != 'pass' for layer in ('base', 'checksum')):
                    errors.append('full pass without snapshot base/integrity prerequisites: ' + row['id'])
    measured = [row for row in rows if row.get('actualEvidence')]
    counts = {
        'vectorsVisited': len(rows),
        'rulePredicatesEvaluated': sum(rule['status'] in ('pass', 'reject')
            for row in measured for snapshot in row['actualEvidence'].get('snapshots', [])[:1]
            for rule in snapshot['rules'].values()),
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
        for defect in ('omitted-history', 'wrong-history-subject', 'duplicate-history-subject'):
            bad = deepcopy(receipt)
            target = next(row for row in bad['vectors'] if
                          row['actualEvidence']['fullModel']['status'] == 'pass'
                          and (len(row['actualEvidence']['snapshots']) > 2
                               if defect == 'duplicate-history-subject'
                               else row['id'] == 'contract-rich-revision-chain'))
            snapshots = target['actualEvidence']['snapshots']
            if defect == 'omitted-history':
                del snapshots[1]
            elif defect == 'wrong-history-subject':
                snapshots[1]['subject'] = 'predecessor wrong-file.gff3'
            else:
                snapshots[2]['subject'] = snapshots[1]['subject']
            if not problems(bad):
                parser.exit(1, f'guard missed {defect}\n')
        bad = deepcopy(receipt)
        target = next(row for row in bad['vectors'] if
                      row['actualEvidence']['fullModel']['status'] == 'reject'
                      and sum(rule['status'] == 'reject' for rule in
                              row['actualEvidence']['snapshots'][0]['rules'].values()) == 1)
        rejecting = next(rule for rule in target['actualEvidence']['snapshots'][0]['rules'].values()
                         if rule['status'] == 'reject')
        rejecting['status'] = 'pass'
        errors = problems(bad)
        if not any('model rejection without an earned carrier predicate' in error for error in errors):
            parser.exit(1, 'guard missed unsupported rejection with unchanged counts\n')
        if any('aggregate evidence counts' in error for error in errors):
            parser.exit(1, 'unsupported-rejection control accidentally changed aggregate counts\n')
        print('Detected eight receipt controls, including unsupported rejection with unchanged counts.')
    print(json.dumps(receipt['counts'], sort_keys=True))
    print('Verified actual dual-base draft evidence; no release or curator acceptance implied.')


if __name__ == '__main__':
    main()
