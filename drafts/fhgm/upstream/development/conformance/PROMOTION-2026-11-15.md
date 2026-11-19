# Promotion packet: real-data gap-proof cases to normative vectors (draft)

Date: 2026-11-15. Maintainer decision (same day): promote the selected
example-lane cases to normative vectors. This packet is the review instrument
for that promotion and implements it in the accompanying draft PR.

Status: **Draft contract; independent expectation review completed 2026-11-19.**
The independent reader `independent_review_275` (gpt-6.1-terra, operated by
David Molik) checked the manifest, fixture
bytes, generator, clauses and [D4–D6 decision record](DECISIONS-2026-11-19.md).
All twelve expectations were accepted: K1 empty array, K2 numeric version,
K3 duplicate identity, K4 transcript/absent target scope, K5 contradictory and
noncomparable references, K6 neighbor/same-immediate-version/missing-history,
and both positive anchors. The reader reproduced all nine generated mutants,
verified all twelve size/SHA-256 records and each seventeen-row payload.
Per-vector clause, disposition and reader are recorded in `expectationReview`.
The author and reader are distinct; this is technical expectation acceptance,
not curator acceptance, biological validation, publication or a replacement for
the independent different-model PR review gate. Historical observations below
retain their original date and are not new full-layer evidence under D4.

## Scope and effect

- Census: 31 sealed vectors → 43 (14 valid, 29 invalid). The 10 gap-proof
  rejections measured by the 2026-11-15 `examples/dmel4/exercise_rules.py`
  run, plus the 2 positive anchors the promoted pointer cases require
  (`manifest_problems` requires every supplied predecessor to itself be a
  recorded vector).
- No earlier vector's bytes, layers, reasons or contexts change (verified by
  a JSON walk of the two manifest revisions). The manifest file's own digest
  moves because entries are added; byte-pinning consumers refresh in their
  own repositories.
- Content provenance: every feature row is copied verbatim from the pinned
  RefSeq archive `GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz`
  (chromosome `NC_004353.4`), with digests and retrieval evidence recorded in
  [`../examples/dmel4/SOURCE.md`](../examples/dmel4/SOURCE.md) and
  [`../examples/dmel4/provenance.json`](../examples/dmel4/provenance.json).
  Each emitted vector is one committed fixture header with exactly one
  documented mutation, rendered by the shared canonical `render` helper with
  a fresh computed exact-byte checksum
  ([`make_dmel_vectors.py`](make_dmel_vectors.py), deterministic; byte-reproducibility
  is gated by `run_conformance.py`'s regeneration check). The only invented
  token in the batch is the clearly labelled `gene-Dmel_absentFromThisFile`,
  whose entire claim is that it is absent from the file. The wrong-parent
  digest in `dmel-reference-contradicts-file` is the committed S6k fixture's
  own checksum, read from that file's bytes at generation time — a real
  FHGFF3 file digest that is simply not this file's parent. Nothing else was
  invented.

## Why these ten

A rejection is **gap-proof** when the released FHGFF3 base schema accepts the
header, the file-bound SHA-512/256 checksum verifies over the exact bytes, and
**only** the draft model-level checker rejects. Those cases are invisible to
every released check; a vector for them is the only artifact that can pin the
K-layer behavior. The ten were measured (not argued) on real annotated data
on 2026-11-15. Four neutered-checker controls establish guard attribution for
the duplicate-ID, transcript-target, contradictory-reference and neighbor-pointer
cases, each preserving one selected cross-control rejection. The synthetic
17-of-19 gap-proof set covers the same clauses over
toy bytes; what the promoted batch adds is that the same clauses fire — with
the same verdicts — on a real multi-isoform RefSeq locus, real nested-ID
confusions, a real FHR-subset parent chain and a real-but-wrong parent digest.

## Independent executors used

Two executors are required by the review rule; three ran (the third is a
read-only external check against that repository's server `main`):

1. **This repository's committed checker** — `../model/validate_fhgm.py`
   (single base, base sha256 `20ce320f…`, v0.5.0) via
   `run_conformance.py --base-schema fhgff3-v0.5.0.json --gff3-validate
   gff3-validate`; Python 3.15.0, `fair-bioheaders` 0.11.0, `jsonschema`
   4.26.0, `PyYAML` 6.0.3, `gff3-validator` 0.1.0 (PyPI wheel). Every layer
   and reason substring in the promoted entries is this runner's observation;
   the run at this PR head reports `43 vectors matched their recorded
   outcomes`, gap-proof `27/29`.
2. **The released toolkit 0.11.0** — `bioheaders verify` (the shipped
   released-contract validator: schema plus exact-byte checksum, independent
   YAML reader and checksum implementation) — exits 0 `Checksum verified.`
   for all 12 promoted files, including all 10 rejected ones: the gap premise
   reproduced per file.
3. **FAIR-bioHeaders-Tools-JavaScript `src/fhgm.js`** (independent K-rule
   implementation; server `main` @ `d8552f670976f02c0c81a86c7e759257c886dd06`,
   node v24.22.1) via the driver reproduced in the appendix: rule-level
   agreement 12/12 — each invalid case rejected by the same clause it is
   attributed to (`K1` empty-array, `K2` type, `K3` ambiguity, `K4` both
   target cases, `K5` both halves, `K6` all three pointer cases), both valid
   anchors accepted with the pointer `resolvable`. The pinned record contract
   that library validates against is byte-identical to ours (`bf1553ca…`).

## The ten rejections: clause, tamper, derivation, observation

For each: **Clause** is the normative text the case exercises (citation, not
restatement). **Tamper** is the single documented mutation of the committed
source fixture. **Derivation** reasons from the clause text to the expected
outcome — this is the part the independent reviewer must check. **Observed**
is the executor output (control 1; controls 2 and 3 above cover the released
layers and the cross-implementation check). Vector ids and layer records:
`manifest.json`; generator bytes: `make_dmel_vectors.py`.

### 1. `dmel-empty-model-array` — K1

- Source: `Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3`; mutation:
  `x-fhgm-models` set to the empty array.
- Clause: model README, Transport — "Model records **must** be carried under
  the single top-level extension key `x-fhgm-models` as a sequence of one or
  more records" and manifest rule K1 ("one or more records");
  `fhgm-draft.schema.json` `minItems: 1`.
- Derivation: a zero-record array is not "a sequence of one or more records";
  the file makes the extension claim without carrying any record, so it is
  not an FHGM file and K1 rejects. R15 is not violated (an extension key of
  any value is base-legal), which is exactly why the rejection must come from
  the model layer.
- Observed: reject `$['x-fhgm-models']: [] should be non-empty`; toolkit
  verify 0; JS `K1=reject`.

### 2. `dmel-numeric-model-version` — K2

- Source: v1; mutation: `modelVersion` of `gene-Dmel_CG11076` set to the YAML
  integer `2` (not the string `"2"`).
- Clause: manifest K2 ("opaque values are non-empty strings");
  `fhgm-model.schema.json` `properties.modelVersion` → `$defs/text`
  (`{"type": "string", "minLength": 1, "pattern": "\\S"}`); model README
  K2/modelVersion ("one opaque string").
- Derivation: `2` (number) fails `type: string`; the contract assigns no
  numeric meaning to `modelVersion` (ordering awaits curators), so a number
  is not a spelling of the string but a different value type, and the record
  is malformed under K2.
- Observed: reject `Model record 0 is invalid under draft contract v0.1:
  $.modelVersion: 2 is not of type 'string'`; toolkit verify 0; JS `K2=reject`.

### 3. `dmel-duplicate-model-id` — K3

- Source: v1; mutation: a deep copy of the `gene-Dmel_CG11077` record
  appended (the same real record twice).
- Clause: model README K3 — "`modelId` is unique within one snapshot; a
  collision makes the identity `ambiguous` and rejects the snapshot
  (deviation D4)"; manifest K3.
- Derivation: with two records sharing `gene-Dmel_CG11077`, a predecessor
  pointer naming that id cannot select one record — the identity a pointer
  needs is unselectable — and D4 places the defect on the snapshot, so the
  named outcome is `ambiguous` and the snapshot is rejected rather than a
  per-record verdict being issued.
- Observed: reject `Ambiguous model ID 'gene-Dmel_CG11077': 2 records share
  it in one snapshot`; toolkit verify 0; JS `K3=reject`.

### 4. `dmel-target-transcript-row` — K4

- Source: v1; mutation: `featureId` of `gene-Dmel_CG11077` set to
  `rna-NM_143687.4` — a real mRNA row **of that same gene** in the same file.
- Clause: model README K4 — "`featureId` resolves to exactly one local `gene`
  row (percent-decoded)"; manifest K4; contract featureId description ("The
  v0.1 default resolves one `gene` row; … transcript-only scope awaits curator
  review (open question Q6)").
- Derivation: `rna-NM_143687.4` decodes to no `gene` row — it is the mRNA row
  nested under `gene-Dmel_CG11077` — so K4's "exactly one local gene row"
  fails and the record is rejected. The case pins v0.1 scope against the
  exact producer confusion the real RefSeq graph invites; it rules nothing on
  Q6 (mirrors the synthetic `feature-target-transcript-row`).
- Observed: reject `Model 'gene-Dmel_CG11077' must target one local gene row:
  'rna-NM_143687.4'`; toolkit verify 0; JS `K4=reject`.

### 5. `dmel-target-absent` — K4

- Source: v1; mutation: `featureId` of `gene-Dmel_CG11076` set to
  `gene-Dmel_absentFromThisFile`.
- Clause: same K4 text as case 4; contract featureId ("Exact decoded **local**
  GFF3 feature ID").
- Derivation: no row of any type in the file carries that decoded ID, so the
  target count is zero, "exactly one local gene row" fails, and the record is
  rejected. The name asserts only its own absence from this file.
- Observed: reject `Model 'gene-Dmel_CG11076' must target one local gene row:
  'gene-Dmel_absentFromThisFile'`; toolkit verify 0; JS `K4=reject`.

### 6. `dmel-reference-contradicts-file` — K5

- Source: v1; mutation: the `gene-Dmel_CG11077` record's `reference` replaced
  by `annotates: krWpdzrhfx1SE7SYJlzxMCXiHg64ujNO6L26SF5asZ8=` — the
  committed S6k example fixture's own real file checksum.
- Clause: model README K5 — "a record `reference` shares at least one
  comparable form with the file genome link **and never contradicts it**";
  manifest K5 (deviation D1 strengthened per review 2026-11-14); contract
  `reference.annotates` ("FHR-family checksum of the annotated genome file").
- Derivation: the file's genome link carries `fhr_checksum` (the chr4-subset
  parent) and a `genomeReference`; the mutated record's only form is
  `annotates`, with a different digest than the file's FHR link. The shared
  form holds two different values — a contradiction about which file the
  annotation annotates — so the contradiction half of K5 rejects. The digest
  is a real FHGFF3 file digest, so no released check can flag it: both byte
  streams are internally consistent.
- Observed: reject `Model 'gene-Dmel_CG11077' carries a reference that
  contradicts the file genome link`; toolkit verify 0; JS `K5=reject`.

### 7. `dmel-reference-not-comparable` — K5

- Source: v1; mutation: the file-level `genomeReference` dropped, leaving only
  the FHR-subset `derivedFrom` link; the `gene-Dmel_CG11076` record keeps only
  its accession+SeqCol binding.
- Clause: K5's first half ("shares at least one comparable form"); manifest
  `reference-forms-not-comparable` description (the strictness the adoption
  packet's D1 summary does not mention, confirmed by maintainers on
  2026-11-14); contract `reference` description.
- Derivation: the file states `fhr_checksum` only; the record states
  `accession`+`seqcol_id` only; the key sets are disjoint, so no shared form
  exists and the first half fails even though nothing contradicts. Both
  statements are true about different scopes (subset FHR vs whole assembly)
  — this is the concrete case that makes the open review question "is K5 meant
  to be this strict?" testable; the vector pins current v0.1 behavior, it does
  not settle the question.
- Observed: reject `Model 'gene-Dmel_CG11076' has no reference form comparable
  with the file genome link`; toolkit verify 0; JS `K5=reject`.

### 8. `dmel-pointer-names-neighbor` — K6 (deviation D2)

- Source: `…snapshot-v2…`; mutation: the `gene-Dmel_CG11076` record's
  `predecessor.modelId` set to `gene-Dmel_CG11077` (the unchanged neighbour);
  history supplied: the v1 snapshot.
- Clause: contract `predecessor.modelId` ("it must equal this record's own
  modelId (deviation D2, confirmed 2026-11-14)"); model README K6; manifest K6.
- Derivation: the pointer's `modelId` differs from the carrying record's, so
  the claim is about a different model than the record it rides on; D2 admits
  no renames inside v0.x, so the verdict is `unresolvable` and v0.1 accepts
  only `resolvable`. Everything else about the pointer (snapshot digest,
  version) would match the neighbour, which is precisely the attack the
  released schema and checksum cannot see.
- Observed: reject `Model 'gene-Dmel_CG11076' predecessor is unresolvable: the
  pointer names another model ID 'gene-Dmel_CG11077'`; toolkit verify 0;
  JS `K6=reject`.

### 9. `dmel-pointer-reuses-version` — K6

- Source: v2; mutation: the record's own `modelVersion` set to `"1"` — equal
  to the version recorded in the supplied predecessor; history: v1.
- Clause: contract modelVersion ("An immediate revision must use a value
  different from its predecessor"); model README K6; disposition Q3 (opaque
  equality is the whole of the semantics).
- Derivation: successor version equals the predecessor's recorded version, so
  the revision claim differs from its predecessor in nothing that the contract
  can see; "must differ" fails on equality alone — no ordering is claimed or
  needed.
- Observed: reject `Model 'gene-Dmel_CG11076' predecessor is unresolvable: the
  revision reuses the predecessor model version`; toolkit verify 0;
  JS `K6=reject`.

### 10. `dmel-revision-without-history` — K6 (deviation D3's bound)

- Source: the committed v2 fixture **as-is** (no mutation — the defect is what
  is *not* supplied); history: none.
- Clause: model README K6 ("resolves against **explicitly supplied** prior
  snapshots only (deviation D3)"); checker verdict text; contract `predecessor`
  description.
- Derivation: the pointer names a snapshot digest that is neither the current
  file nor any supplied predecessor, so resolution has no foundation and the
  verdict is `unresolvable`. v0.1 never assumes an unsupplied chain holds;
  the same bytes pass when v1 is supplied (vector 12), which is what makes
  this a bound rather than a bug report.
- Observed: reject `Model 'gene-Dmel_CG11076' predecessor is unresolvable: the
  predecessor snapshot is the current file or was not supplied`; toolkit
  verify 0; JS `K6=reject`.

## The two positive anchors (required, not gap-proof claims)

### 11. `dmel-snapshot-v1` — valid

- The committed v1 fixture as-is. Derivation: two records, distinct real
  `modelId`s, each targeting one local gene row, bound to the two released
  genome-link forms with values copied from the source (accession
  `GCF_000001215.4`, whole-collection SeqCol digest; the subset FHR parent
  checksum) — K1–K5 hold; the pointers are absent, so K6 issues no claim.
  Manifest `rules: [K1, K2, K4, K5]`.
- Observed: pass; toolkit verify 0; JS all rules `pass`.
- Role: supplies v1 as a *vector* so entries 8/9/12 can name it in
  `context.predecessors` (`manifest_problems` requires predecessors to be
  vectors).

### 12. `dmel-snapshot-v2-resolved` — valid

- The committed v2 fixture with v1 supplied. Derivation: the pointer names its
  own `modelId`, a version the supplied snapshot records, a checksum that is
  not the current file, assembly links that share comparable forms without
  contradiction, and no supplied snapshot records a skipped successor — every
  condition of `resolvable` in the model README's verdict list is met.
  `resolvable` identifies a predecessor record; it asserts no curator
  acceptance (O8).
- Observed: pass with `resolvable`; toolkit verify 0; JS `K6=resolvable`.

## Executor agreement table

| vector | attributed clause | repo checker (control 1) | toolkit 0.11.0 verify (control 2) | JS fhgm.js @ main (control 3) |
| --- | --- | --- | --- | --- |
| `dmel-empty-model-array` | K1 | reject, reason sealed | verified (released layers pass) | `K1=reject` |
| `dmel-numeric-model-version` | K2 | reject, reason sealed | verified | `K2=reject` |
| `dmel-duplicate-model-id` | K3 | reject, reason sealed | verified | `K3=reject` |
| `dmel-target-transcript-row` | K4 | reject, reason sealed | verified | `K4=reject` |
| `dmel-target-absent` | K4 | reject, reason sealed | verified | `K4=reject` |
| `dmel-reference-contradicts-file` | K5 | reject, reason sealed | verified | `K5=reject` |
| `dmel-reference-not-comparable` | K5 | reject, reason sealed | verified | `K5=reject` |
| `dmel-pointer-names-neighbor` | K6 | reject, reason sealed | verified | `K6=reject` |
| `dmel-pointer-reuses-version` | K6 | reject, reason sealed | verified | `K6=reject` |
| `dmel-revision-without-history` | K6 | reject, reason sealed | verified | `K6=reject` |
| `dmel-snapshot-v1` | — (valid) | pass | verified | all `pass` |
| `dmel-snapshot-v2-resolved` | — (valid) | pass (`resolvable`) | verified | `K6=resolvable` |

`verified` in column 3 means the released toolkit (schema + exact-byte
checksum) accepts the file: for the ten rejections that is the gap premise,
confirmed per file rather than asserted by the suite.

## FHGFF3 1.2 basis

The reported 10/10 FHGFF3 1.2 agreement comes from
[PR #17's dual-base tree](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/17),
whose dmel4 exercise re-runs the ten cases under `v0.6.0`/`1.2` with fresh
checksums and mixed-identity chains. This branch's exercise does not run that
lane: it still expects its single 1.2 transport mutant to be base-rejected.
The conformance matrix lane's per-vector twins for the promoted 12 will seal
into `base_matrix.json` when this batch lands on a tree that carries PR #17's
matrix lane — recorded as a follow-through of the merge order, not claimed as
done here.

## Neutered-checker evidence (from the 2026-11-15 example-lane run)

`exercise_rules.py` N-K3/N-K4/N-K5/N-K6: each control disables exactly one
guard (the script refuses unless the old text occurs exactly once and the
bytes change), flips its own rejection 1→0 and keeps one selected
cross-control rejection standing; all four pass. This is the non-vacuity
proof for the four cases it covers — duplicate-ID, transcript-target,
contradictory-reference and neighbor-pointer — that the attributed guard, not
an adjacent one, produces those rejections. N-K5's cross-control additionally
shows `mutant-k5-not-comparable` stays rejected with the contradiction guard
disabled — the two K5 halves are independent checks — but its own guard is not
itself neutered. The remaining five promoted cases carry no direct neuter; for
them the evidence is the reason-string identity plus
rule-level agreement between two independent implementations (controls 1 and 3
above), and a reviewer who wants guard-level attribution for those should say
so on this PR rather than assume it exists.

## Review checklist for the independent reader

1. Re-derive each "Derivation" above from the cited clause text alone, before
   reading the observed output; flag any place the observation would differ
   from the text.
2. Re-run the sealed lane: `run_conformance.py --base-schema <v0.5.0 bytes>`
   at the reviewed head; regenerate and `cmp` the nine emitted bytes.
3. Re-run control 2 (`bioheaders verify`, toolkit 0.11.0) and, if the
   JavaScript repository is reachable, the appendix driver against its
   `main`.
4. Confirm no promoted entry rests on an invented identifier, coordinate,
   accession or digest (the two deliberate labelled exceptions are stated
   above: the absent-target token and the S6k digest used as a wrong parent).
5. Confirm the census arithmetic and the unchanged-legacy claim against the
   pre-change manifest.
6. Only then: approve, amend, or reject individual entries. Rejecting an
   entry retires it under `manifest.json`'s `retired` list with its id never
   reused; it does not retire the whole batch.

## Non-goals

No curator acceptance (O8), no support or adoption claim (rule V7), no
`v0.8.0` preparation, no downstream re-pinning, no change to
`selfChecksum`/`parentLink` semantics (FHGM records carry no file identity;
the retired `T1–T3` id shape does not reappear), no edit to `header/`, and no
change to any pre-existing vector byte, expectation or base pin.

## Appendix: cross-implementation driver (as run 2026-11-15)

Clone of `FAIR-bioHeaders-Tools-JavaScript` server `main`
(`d8552f670976f02c0c81a86c7e759257c886dd06`), `npm install`, node v24.22.1;
`exec_fhgm.mjs` (kept outside both repositories — this packet is the record;
the reviewer may re-run it verbatim):

```js
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { load as yamlLoad } from 'js-yaml';
import { checkFhgmModels } from './src/fhgm.js';

const repo = process.argv[2];
const read = (rel) => readFileSync(join(repo, rel));

function headerOf(data) {
  const lines = data.toString('utf8').split('\n');
  const body = lines.filter((l) => l.startsWith('#~')).map((l) => l.slice(2)).join('\n');
  return yamlLoad(body);
}
function geneIdsOf(data) {
  const ids = [];
  for (const line of data.toString('utf8').split('\n')) {
    if (!line || line.startsWith('#')) continue;
    const cols = line.split('\t');
    if (cols.length !== 9 || cols[2] !== 'gene') continue;
    for (const attr of cols[8].split(';')) {
      const [k, ...rest] = attr.split('=');
      if (k === 'ID') ids.push(decodeURIComponent(rest.join('=')));
    }
  }
  return ids;
}

const V1REL = 'development/examples/dmel4/Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3';
const V2REL = 'development/examples/dmel4/Dmel_CG11076-Mpv17.snapshot-v2.fhgff3.gff3';
const v1 = read(V1REL);
const predecessors = [{ header: headerOf(v1), checksum: headerOf(v1).checksum }];

const cases = [
  ['dmel-snapshot-v1', V1REL, false],
  ['dmel-snapshot-v2-resolved', V2REL, true],
  ['dmel-revision-without-history', V2REL, false],
  ['dmel-duplicate-model-id', 'development/conformance/vectors/invalid/dmel-duplicate-model-id.fhgff3.gff3', false],
  ['dmel-empty-model-array', 'development/conformance/vectors/invalid/dmel-empty-model-array.fhgff3.gff3', false],
  ['dmel-numeric-model-version', 'development/conformance/vectors/invalid/dmel-numeric-model-version.fhgff3.gff3', false],
  ['dmel-pointer-names-neighbor', 'development/conformance/vectors/invalid/dmel-pointer-names-neighbor.fhgff3.gff3', true],
  ['dmel-pointer-reuses-version', 'development/conformance/vectors/invalid/dmel-pointer-reuses-version.fhgff3.gff3', true],
  ['dmel-reference-contradicts-file', 'development/conformance/vectors/invalid/dmel-reference-contradicts-file.fhgff3.gff3', false],
  ['dmel-reference-not-comparable', 'development/conformance/vectors/invalid/dmel-reference-not-comparable.fhgff3.gff3', false],
  ['dmel-target-absent', 'development/conformance/vectors/invalid/dmel-target-absent.fhgff3.gff3', false],
  ['dmel-target-transcript-row', 'development/conformance/vectors/invalid/dmel-target-transcript-row.fhgff3.gff3', false],
];

for (const [name, rel, withHistory] of cases) {
  const data = read(rel);
  const options = { geneIds: geneIdsOf(data) };
  if (withHistory) options.predecessors = predecessors;
  const result = checkFhgmModels(headerOf(data), options);
  console.log(JSON.stringify({ case: name, valid: result.valid, rules: result.rules,
                               errors: result.errors.slice(0, 2) }));
}
```

## Per-vector independent disposition (2026-11-19)

Reader for every row: `independent_review_275`, gpt-6.1-terra, operated by
David Molik; distinct from the original derivation author. Clauses and detailed
derivations are the numbered sections above and manifest `expectationReview`.

| Vector | Independent disposition |
| --- | --- |
| `dmel-snapshot-v1` | Accepted pass; D4 earned-evidence boundary retained. |
| `dmel-snapshot-v2-resolved` | Accepted pass; D4 earned-evidence boundary retained. |
| `dmel-duplicate-model-id` | Accepted rejection K3; D4 earned-evidence boundary retained. |
| `dmel-empty-model-array` | Accepted rejection K1; D4 earned-evidence boundary retained. |
| `dmel-numeric-model-version` | Accepted rejection K2; D4 earned-evidence boundary retained. |
| `dmel-pointer-names-neighbor` | Accepted rejection K6; D4 earned-evidence boundary retained. |
| `dmel-pointer-reuses-version` | Accepted rejection K6; D4 earned-evidence boundary retained. |
| `dmel-reference-contradicts-file` | Accepted rejection K5; D4 earned-evidence boundary retained. |
| `dmel-reference-not-comparable` | Accepted rejection K5; D4 earned-evidence boundary retained. |
| `dmel-revision-without-history` | Accepted rejection K6; D4 earned-evidence boundary retained. |
| `dmel-target-absent` | Accepted rejection K4; D4 earned-evidence boundary retained. |
| `dmel-target-transcript-row` | Accepted rejection K4; D4 earned-evidence boundary retained. |
