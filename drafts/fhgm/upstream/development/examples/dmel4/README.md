# Real-data example fixtures: two *Drosophila melanogaster* chromosome-4 gene models

Status: **example lane** — real-data-derived fixtures with provenance. The
fixture files themselves remain **not** vectors, but the maintainer promotion
decision of 2026-11-15 lifts ten measured gap-proof rejections from this
directory's `exercise_rules.py` run, plus two required positive anchors, into
`development/conformance/` as digest-pinned `dmel-*` vectors (census 31 → 43)
— as a DRAFT pending independent review of every expectation
([../../conformance/PROMOTION-2026-11-15.md](../../conformance/PROMOTION-2026-11-15.md)). FHGM is a draft under selection rule V7: no
`schemaVersion`, no registry row, no w3id URL, no toolkit-support claim and no
release form attach to anything here, and no pointer resolved below asserts
curator acceptance. Refs FHGM [#8](https://github.com/FAIR-bioHeaders/FHGM-Specification/issues/8),
[#9](https://github.com/FAIR-bioHeaders/FHGM-Specification/issues/9) and shared
[#206](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/206).

This directory builds the first FHGM model records over a real annotated
genome: an FHR single-chromosome subset, an FHGFF3 1.1 annotation carrying two
`x-fhgm-models` records taken from the RefSeq annotation of *D. melanogaster*
`GCF_000001215.4` ("Release 6 plus ISO1 MT"), and a second snapshot that
revises one record through a `predecessor` pointer. Every header checksum was
written by the released toolkit (`fair-bioheaders` 0.11.0, `bioheaders
combine`); none was edited by hand. Provenance and reuse review:
[SOURCE.md](SOURCE.md); machine-readable record:
[provenance.json](provenance.json).

## Provenance re-verified in this session (2026-11-15)

- NCBI `esummary` db=assembly uid=202931: `GCF_000001215.4`, assembly name
  "Release 6 plus ISO1 MT", status Chromosome, BioSample `SAMN02803731`,
  taxid 7227, RefSeq FTP path as used below. Raw response:
  [ncbi-esummary-202931.json](ncbi-esummary-202931.json). Every field above
  was re-read from the fetched JSON on 2026-11-15 rather than copied from
  prior notes.
- Whole-file downloads only (a ranged read of a `.gz` truncates mid-stream);
  `gzip -t` passed on both archives before any read; both MD5s equal NCBI's
  published `md5checksums.txt` values. SHA-256:
  `…_genomic.fna.gz` `e69e907b…ebc57d` (44,235,956 B),
  `…_genomic.gff.gz` `9a372f10…b2c726` (8,688,226 B).
- Chromosome 4 is `NC_004353.4` (GenBank `AE014135.4`), 1,348,131 bp — from
  the assembly report row and from a direct base count, **not** from the older
  `NT_033777.4` identifier some notes carry; this release labels `NT_033777.3`
  as chromosome 3R.
- The extracted chromosome-4 record equals NCBI's independently published
  `…/assembled_chromosomes/FASTA/chr4.fna` (MD5 `edd1c69d…`, 1,365,033 B per
  `uncompressed_checksums.txt`) after case normalization: the per-chromosome
  file is unmasked, `genomic.fna.gz` is soft-masked with 374,633 lowercase
  bases. The FHR subset therefore declares `masking: soft-masked`.
- SeqCol digests were computed with the S6k pilot recipe; the implementation
  was validated by reproducing the S6k fixture's recorded digest
  `JpZUOWCdrUxBuclH0rbvPszL9b8HpHZj` for `GCA_000005115.1` (13,749 records)
  before any Drosophila value was trusted. Values used here: full assembly
  collection `hFwVeJXKpWP3X-g4wmJGT-eZTa1r3Y1l`; the 1-record FHR subset
  collection `2TLKYAYTWuvi_dekG8QRQBX2fYa4LHhw`. Uppercasing inside the
  recipe makes soft-masking irrelevant to the digest.

## Locus definition

Selected from the source by structure (smallest multi-isoform protein-coding
gene on chr4, plus its single-exon neighbor). All rows are copied **verbatim**
from `…_genomic.gff.gz`, in source order; nothing was constructed. The
payload file is the `##gff-version 3` directive plus these 17 rows.

| type | start | end | strand | phase | ID | Parent |
| --- | --- | --- | --- | --- | --- | --- |
| region | 1 | 1348131 | + | . | `NC_004353.4:1..1348131` | — |
| gene | 1028675 | 1029361 | - | . | `gene-Dmel_CG11077` (`Name=Mpv17`) | — |
| mRNA | 1028675 | 1029361 | - | . | `rna-NM_143687.4` | `gene-Dmel_CG11077` |
| exon | 1028675 | 1029361 | - | . | `exon-NM_143687.4-1` | `rna-NM_143687.4` |
| CDS | 1028743 | 1029249 | - | 0 | `cds-NP_651944.1` | `rna-NM_143687.4` |
| gene | 1029711 | 1031757 | - | . | `gene-Dmel_CG11076` | — |
| mRNA | 1029711 | 1031757 | - | . | `rna-NM_001258500.1` | `gene-Dmel_CG11076` |
| exon | 1031595 | 1031757 | - | . | `exon-NM_001258500.1-1` | `rna-NM_001258500.1` |
| exon | 1029711 | 1030777 | - | . | `exon-NM_001258500.1-2` | `rna-NM_001258500.1` |
| CDS | 1029971 | 1030753 | - | 0 | `cds-NP_001245429.2` | `rna-NM_001258500.1` |
| mRNA | 1029711 | 1031676 | - | . | `rna-NM_143686.4` | `gene-Dmel_CG11076` |
| exon | 1031552 | 1031676 | - | . | `exon-NM_143686.4-1` | `rna-NM_143686.4` |
| exon | 1029711 | 1030777 | - | . | `exon-NM_143686.4-2` | `rna-NM_143686.4` |
| CDS | 1029971 | 1030753 | - | 0 | `cds-NP_651943.2` | `rna-NM_143686.4` |
| mRNA | 1029711 | 1030975 | - | . | `rna-NM_166807.3` | `gene-Dmel_CG11076` |
| exon | 1029711 | 1030975 | - | . | `exon-NM_166807.3-1` | `rna-NM_166807.3` |
| CDS | 1029971 | 1030810 | - | 0 | `cds-NP_726630.2` | `rna-NM_166807.3` |

Gene-level cross-references as the source writes them: `gene-Dmel_CG11076` →
`FLYBASE:FBgn0039929`, `GeneID:43830`; `gene-Dmel_CG11077` →
`FLYBASE:FBgn0039930`, `GeneID:43831`. The source rows state no personal
model authors and no article; `contributors` and `publication.article` are
therefore **absent** from the records — what the source does not supply, the
fixture does not claim.

Sequence-level truth check (not promoted into any header claim): translating
the four CDS intervals from the extracted chromosome (genetic code table 1,
minus strand) and comparing with `…_protein.faa.gz` gives exact matches for
`NP_651944.1` (168 aa) and `NP_726630.2` (279 aa), and a 259/260 match for
`NP_651943.2` and `NP_001245429.2`: those two CDS begin with genome codon
**CTG** while the published peptide begins with the annotated initiator **M**
(a Drosophila CTG-initiation convention). All four end in an in-frame TAG.

## Carrier chain

`build_fixture.py` (toolkit-only, deterministic, byte-reproducible across
runs) writes:

| file | role | identity |
| --- | --- | --- |
| `Dmel-NC_004353.4-chr4.fhr.fa` (not committed; rebuilt from the pinned archive) | FHR parent | FHGFF3-style `;~` header, FHR `2.1` / v0.6.0 URI; exact-byte checksum `zSTzyw4aOnZWd2XXKL9GBWtVWM1S6e0i1vt1XX0mVOY=` |
| `Dmel_CG11076-Mpv17.payload.gff3` | verbatim locus rows | 6,753 B, SHA-256 `b0757bd8…0afa9763` |
| `Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3` | FHGFF3 1.1 + two `x-fhgm-models` records | checksum `4o7S2qFElvCqHkK59ZLarK9LGPO4Jwrsn1Ea6LwQZMY=` |
| `Dmel_CG11076-Mpv17.snapshot-v2.fhgff3.gff3` | revision snapshot; the `Dmel_CG11076` record revises to `"2"` and names v1 in `predecessor` | checksum `8TaIBDS3IJv+OAyV0fr6jOC7bmjlF1JxAtJOQkAnVME=` |

**The FHR is a declared subset.** It contains exactly one sequence record
(`NC_004353.4`, soft-masked) out of the 1,876-record assembly collection.
The `derivedFrom` checksum in both snapshots describes **this subset file as
it exists on disk**, not the assembly; the whole-assembly identity is carried
separately in the file-level `genomeReference` (accession `GCF_000001215.4`
plus the computed full-collection SeqCol digest). The two records use both
released genome-link forms with real values: `gene-Dmel_CG11076` binds the
`genomeReference`, `gene-Dmel_CG11077` binds `annotates` (the FHR subset
checksum) — the real-data shape of the `both-reference-forms` vector.

The v2 `predecessor` is honest about what it is, and the record says so in
its own second `evidence` entry: the revision is of this example's own record
between two snapshots of one unchanged biological model; it is not a claim
that FlyBase or RefSeq revised `CG11076`.

## Verification transcripts

Environment: Python 3.15.0, `fair-bioheaders` 0.11.0, `jsonschema` 4.26.0,
`gff3-validator` 0.1.0; base schema = FHGFF3 `fhgff3.json` at tag `v0.5.0`
(SHA-256 `20ce320f…e8e416c`, registered in `development/model/base-schemas.json`
and selected by `validate_fhgm.py` for these 1.1-declaring fixtures; the same
record is in `development/conformance/provenance.json`; a nonsense-tag control
URL returned 404, confirming the raw path is real). The exercise lane is
re-run below under both registered releases (v0.5.0 and v0.6.0) following the
maintainer dual-base decision of 2026-11-15.

Toolkit integrity of the chain:

```text
bioheaders verify Dmel-NC_004353.4-chr4.fhr.fa              → Checksum verified. (exit 0)
bioheaders verify Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3 → Checksum verified. (exit 0)
bioheaders verify Dmel_CG11076-Mpv17.snapshot-v2.fhgff3.gff3 → Checksum verified. (exit 0)
```

`verify-links` — three cases, all recorded:

```text
$ bioheaders verify-links snapshot-v1 Dmel-NC_004353.4-chr4.fhr.fa
derivedFrom[0] FHR annotates: matched (…/Dmel-NC_004353.4-chr4.fhr.fa)
genomeReference GCF_000001215.4: not matched (… records seqcol_id 2TLKYAYTWuvi_dekG8QRQBX2fYa4LHhw)
→ exit 3
$ bioheaders verify-links --require-all snapshot-v1 <subset FHR> <whole-assembly FHR>
derivedFrom[0] FHR annotates: matched (…subset…)
genomeReference GCF_000001215.4: matched (…whole…)
→ exit 0   (genuine match on both released link forms)
$ bioheaders verify-links snapshot-v1 <wrong FHR (mitochondrion record)>
derivedFrom[0] FHR annotates: not matched (… has checksum jeSFnYsvIrUwgvS+2c4uiCi/UExjascdYsdzry+Cdro=)
→ exit 3   (negative control: the match above discriminates)
```

Draft model checker (K1–K6) on the committed bytes:

```text
$ python3 development/model/validate_fhgm.py --base-schema fhgff3-v0.5.0.json snapshot-v1
model gene-Dmel_CG11076 version '1': no predecessor claim
model gene-Dmel_CG11077 version '1': no predecessor claim
Passed FHGFF3 header, checksum and draft FHGM checks for 2 model(s).   (exit 0)

$ python3 development/model/validate_fhgm.py --base-schema … --predecessor snapshot-v1 snapshot-v2
model gene-Dmel_CG11076 version '2': resolvable (predecessor 4o7S2qFE... version '1')   (exit 0)

$ python3 development/model/validate_fhgm.py --base-schema … snapshot-v2     # no history
Model 'gene-Dmel_CG11076' predecessor is unresolvable: … not supplied       (exit 1)
```

Feature layer on the exact payload bytes: `gff3-validate --no-header` reports
0 errors / 0 warnings (1 note: HDR-003 header checks skipped); the same run
with `--genome Dmel-NC_004353.4-chr4.fhr.fa` executes the genome-aware lane:
0 errors / 0 warnings.

## Which model rules a real locus actually exercises

`exercise_rules.py` applies one realistic producer error per case to the
real fixture headers and re-runs all four layers; each mutant gets a fresh
correct checksum from the toolkit, so any rejection cannot be a checksum or
transport artifact. The script exits 0 only if every expectation above holds;
its exit-0 run output is transcribed below (2026-11-15):

| case | rule | base | verify | gff3 | model | layer gap |
| --- | --- | --- | --- | --- | --- | --- |
| `fixture-v1` | K1-K6 | accept | verify | accept | pass | — |
| `fixture-v2-with-history` | K6 | accept | verify | accept | pass | — |
| `fixture-v2-without-history` | K6 | accept | verify | accept | reject | yes |
| `mutant-k2-numeric-version` | K2 | accept | verify | accept | reject | yes |
| `mutant-k3-duplicate-modelid` | K3 | accept | verify | accept | reject | yes |
| `mutant-k4-target-transcript` | K4 | accept | verify | accept | reject | yes |
| `mutant-k4-target-absent` | K4 | accept | verify | accept | reject | yes |
| `mutant-k5-contradicts` | K5 | accept | verify | accept | reject | yes |
| `mutant-k5-not-comparable` | K5 | accept | verify | accept | reject | yes |
| `mutant-k6-neighbor-pointer` | K6 | accept | verify | accept | reject | yes |
| `mutant-k6-version-reused` | K6 | accept | verify | accept | reject | yes |
| `mutant-k1-empty-models` | K1 | accept | verify | accept | reject | yes |
| `mutant-transport-fhgff3-12` | K1 | accept | verify | accept | pass | — |
| `tamper-payload-byte` | B1 | accept | stale | accept | reject | no |

Table transcribed 2026-11-15 after the dual-base decision: the FHGFF3 1.2
identity mutant is now a **positive** transport case (it was the base-layer
rejection finding F1 recorded below), so the run holds 11 model-layer
rejections, of which **10 are gap-proof** — the released base schema accepts
them and the exact-byte checksum verifies, and **only** the model checker
distinguishes them, on real annotated data. The 11th (`tamper-payload-byte`)
is caught by the released checksum too. The reasons quoted by the script:

```text
fixture-v2-without-history: Model 'gene-Dmel_CG11076' predecessor is unresolvable: the predecessor snapshot is the current file or was not supplied
mutant-k2-numeric-version: $.modelVersion: 2 is not of type 'string'
mutant-k3-duplicate-modelid: Ambiguous model ID 'gene-Dmel_CG11077': 2 records share it in one snapshot
mutant-k4-target-transcript: Model 'gene-Dmel_CG11077' must target one local gene row: 'rna-NM_143687.4'
mutant-k4-target-absent: Model 'gene-Dmel_CG11076' must target one local gene row: 'gene-Dmel_absentFromThisFile'
mutant-k5-contradicts: Model 'gene-Dmel_CG11077' carries a reference that contradicts the file genome link
mutant-k5-not-comparable: Model 'gene-Dmel_CG11076' has no reference form comparable with the file genome link
mutant-k6-neighbor-pointer: … the pointer names another model ID 'gene-Dmel_CG11077'
mutant-k6-version-reused: … the revision reuses the predecessor model version
mutant-k1-empty-models: $['x-fhgm-models']: [] should be non-empty
```

### Dual-base re-run: the gap-proof set under the FHGFF3 1.2 base

The same script rebuilds each of the 10 gap-proof cases under the released
1.2 identity (`schema` and `schemaVersion` moved, a fresh correct
toolkit-recomputed checksum, records and feature bytes untouched, predecessors
kept as the committed 1.1 snapshots — the mixed-identity chain a base-line
release bump produces in the field) and requires every verdict and reason to
reproduce. Exit-0 run output (2026-11-15):

```text
dual-base re-run of the gap-proof set (FHGFF3 1.2 identity):
  twin12-fixture-v2-without-history: base=accept verify=verify model=reject reason reproduced
  twin12-mutant-k2-numeric-version: base=accept verify=verify model=reject reason reproduced
  twin12-mutant-k3-duplicate-modelid: base=accept verify=verify model=reject reason reproduced
  twin12-mutant-k4-target-transcript: base=accept verify=verify model=reject reason reproduced
  twin12-mutant-k4-target-absent: base=accept verify=verify model=reject reason reproduced
  twin12-mutant-k5-contradicts: base=accept verify=verify model=reject reason reproduced
  twin12-mutant-k5-not-comparable: base=accept verify=verify model=reject reason reproduced
  twin12-mutant-k6-neighbor-pointer: base=accept verify=verify model=reject reason reproduced
  twin12-mutant-k6-version-reused: base=accept verify=verify model=reject reason reproduced
  twin12-mutant-k1-empty-models: base=accept verify=verify model=reject reason reproduced
  10/10 gap-proof rejections reproduce unchanged under the 1.2 base; the 1.2
  mutant itself is admitted as a positive carrier.
```

### Neutered-checker controls (non-vacuity proof)

A rule is only shown to bite if a checker without it accepts the very file
the real checker rejects. Each control copies `validate_fhgm.py`, replaces
one guard (the script refuses to proceed unless the old text occurs exactly
once and the bytes change — a substitution that matches nothing cannot fake a
green result), and re-runs. All four controls pass with cross-controls:

```text
N-K4: K4 gene-row target check disabled
  mutant-k4-target-transcript: real rc=1, neutered rc=0
  cross-control mutant-k5-contradicts: neutered rc=1 -> OK
N-K3: K3 duplicate-modelId rejection disabled
  mutant-k3-duplicate-modelid: real rc=1, neutered rc=0
  cross-control mutant-k4-target-transcript: neutered rc=1 -> OK
N-K5: K5 contradiction test disabled (links_conflict -> False)
  mutant-k5-contradicts: real rc=1, neutered rc=0
  cross-control mutant-k5-not-comparable: neutered rc=1 -> OK
N-K6: K6 own-modelId (D2) check disabled
  mutant-k6-neighbor-pointer: real rc=1, neutered rc=0
  cross-control mutant-k3-duplicate-modelid: neutered rc=1 -> OK
```

What the real locus adds over the synthetic set, honestly stated: K2, K3, K4
(absent target), K6 (neighbor, version-reuse, no-history) and K1 fire here
the same way they fire on the synthetic vectors — the real data confirms the
rules are not artifacts of synthetic simplification, but adds no new
detection power for those. What only this real annotated genome produced:

- K4 rejection against a **real transcript row of the same gene**
  (`rna-NM_143687.4`), the exact confusion a producer editing a nested
  RefSeq graph faces; the synthetic transcript-row vector modeled it, this
  shows it occurs in the data shape itself.
- K5 strictness in a form the synthetic case only asserts: file linked to an
  **FHR subset** by `derivedFrom` while a record legitimately cites the
  **whole-assembly accession + SeqCol** — nothing contradicts, and v0.1
  rejects for sharing no comparable form (`mutant-k5-not-comparable`). The
  N-K5 control shows the two K5 halves are separable, which makes the
  open review question "is K5 meant to be this strict?" testable rather than
  rhetorical.
- The K1/B1 transport boundary against the **current** released FHGFF3
  identity (1.2 / v0.6.0) — not representable in synthetic bytes alone
  without deciding which released version the draft rides on (finding F1,
  since resolved: the decision of 2026-11-15 admits both released identities,
  and the re-run above shows the K-layer verdicts are base-invariant).
- The `verify-links` subset-vs-assembly behavior above, which no K rule
  covers and which only real parent files exercise.

## Findings for #8/#9 (draft, no decisions taken here)

1. **F1 — the draft's base identity lags the released FHGFF3.**
   **Resolved by maintainer decision 2026-11-15: support both released bases
   (option C of the A/B/C framing).** The harness now selects the base from
   the carrier's declared identity (`development/model/base-schemas.json` plus
   the checker's selection lane and the conformance suite's 1.2 matrix); the
   sealed 1.1 vectors keep their bytes and expectations. The text below is the
   finding as filed on 2026-11-15, kept unrewritten as the review record.
   K1 requires
   the FHGFF3 `1.1` identity and the checker pins the v0.5.0 bytes, but the
   released contract is FHGFF3 `1.2` (v0.6.0) — which the same toolkit
   verifies fine (`mutant-transport-fhgff3-12`: `verify` passes; the base
   schema at v0.5.0 rejects `'1.2' is not one of ['1.0', '1.1']`). A producer
   following current `llms.txt` guidance writes 1.2 headers and the draft
   checker will reject them. The publication PR should decide whether the
   overlay/base pin rebases to the newest FHGFF3 minor (1.2 adds no property
   changes over 1.1 in the bundled schemas), or whether the draft stays bound
   to 1.1 until publication.
2. **F2 — K5 strictness now has a real use case on both sides.** Review-raised
   item 2 asked whether rejecting no-comparable-form is intended. This fixture
   pair shows the realistic scenario: the annotation file annotates a subset
   FHR (checksum link) while a record cites the assembly accession and the
   whole-collection SeqCol (both true statements about different scopes).
   v0.1 rejects that file; N-K5 shows the contradiction half and the
   comparability half are independent checks, so the open review question
   "is K5 meant to be this strict?" can now be decided against a concrete
   real-data case.
3. **F3 — `verify-links` on a subset-parent chain.** With only the subset FHR
   supplied, `verify-links` reports the matched `derivedFrom` **and** exits 3
   because the `genomeReference` row cannot match a candidate whose recorded
   `seqcol_id` describes a different collection. That is correct
   discrimination, but chain consumers and pilot instructions need to know a
   subset FHR cannot satisfy an assembly-level `genomeReference`; either both
   parents are supplied or exit 3 is expected.
4. **F4 — reuse terms are not citable from RefSeq.** No reuse-terms statement
   exists in the downloaded assembly tree, so `reuseConditions` (record and
   file scope) stays absent, per "unknown optional values stay absent". Any
   FHGM guidance that expects producers to fill it from a database deposit
   needs a citable source; for NCBI-derived models there is none in-tree.
5. **F5 — model authorship is not present in RefSeq rows.** `contributors`
   cannot be honestly filled for database-derived models (only the assembly
   submitter organization is stated, which the fixture records at FHR file
   scope). The curator round (Q2) should expect database-sourced records to
   carry `evidence`/`publication.deposit` and no personal contributors.
6. **F6 — one record per gene works on real isoform graphs.** The
   three-transcript `CG11076` locus needs exactly one record under v0.1
   (`featureId` → gene row, isoforms stay in the ID/Parent graph). This is
   first real evidence bearing on Q6's transcript-only question: the data
   shape supports gene-level records without loss, and transcript-level
   records would need the open O1 scope.
7. **F7 — biology truth note.** Two CDS start with a genome CTG that RefSeq
   annotates as initiator M; a naive table-1 translation check reports a
   mismatch that is not an error in the model. Nothing in the fixtures claims
   translation identity; the record evidence entries cite only what was
   copied from the source.

## Reproducing

```sh
# fetch (whole files; verify digests and gzip -t before trusting anything —
# expected values are recorded in provenance.json; build_fixture.py re-checks
# them and aborts on mismatch)
BASE=https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/215/GCF_000001215.4_Release_6_plus_ISO1_MT
curl -s -O $BASE/GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.fna.gz
curl -s -O $BASE/GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz
python3 development/examples/dmel4/build_fixture.py \
  --fna-gz GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.fna.gz \
  --gff-gz GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz \
  --outdir /tmp/dmel4-build --payload-out /tmp/payload.check.gff3
cmp /tmp/dmel4-build/Dmel_CG11076-Mpv17.payload.gff3 \
   development/examples/dmel4/Dmel_CG11076-Mpv17.payload.gff3
cmp /tmp/dmel4-build/Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3 \
   development/examples/dmel4/Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3
cmp /tmp/dmel4-build/Dmel_CG11076-Mpv17.snapshot-v2.fhgff3.gff3 \
   development/examples/dmel4/Dmel_CG11076-Mpv17.snapshot-v2.fhgff3.gff3
python3 development/examples/dmel4/exercise_rules.py --base-schema /tmp/fhgff3-v0.5.0.json
```

`build_fixture.py` aborts on digest or `gzip -t` mismatch; `exercise_rules.py`
needs only the committed fixtures, the toolkit, `jsonschema` and the pinned
base schema (no downloads).

## Not verified here

- The full `verify-links`/assess behavior for gzip'd parent candidates and
  every CLI flag combination beyond the cases transcribed above.
- Independent publication of the Drosophila SeqCol digests (computed by the
  validated recipe; NCBI publishes no SeqCol id to compare against).
- The noncoding / lncRNA and transcript-only scope cases (chr4 has 18 lnc_RNA
  and 15 antisense_RNA genes; none modeled — Q6/O1 territory).
- Split/merge/assembly-migration semantics (open scope; nothing here needs
  them, nothing here tests them).
- Curator acceptance of any revision (O8): no file in this directory carries
  an acceptance assertion, and the v1→v2 pointer is explicitly a fixture-level
  record revision.
- Any support claim: the toolkit never parses `x-fhgm-models` content; the
  passes above are base-schema/checksum passes plus the draft checker.
