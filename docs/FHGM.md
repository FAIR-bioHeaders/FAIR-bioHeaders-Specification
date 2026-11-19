# FHGM: FAIR header gene model — draft overview

**Status: a draft under rule V7. There is no released FHGM contract.** The
maintainers have adopted FHGM's form and most of its draft design (see
[Adopted decisions and open items](#adopted-decisions-and-open-items)), and
the draft contract is developed in
[FHGM-Specification](https://github.com/FAIR-bioHeaders/FHGM-Specification).
Adoption of those decisions is not publication: FHGM has no released JSON
Schema or LinkML model, no `schemaVersion`, no w3id schema URL, and no entry in
the version registry [`schemas/versions.json`](../schemas/versions.json) — that
registry lists released contracts only. The design record is
[#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204);
pilot datasets are tracked in
[#206](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/206)
and family delivery in
[#55](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/55).
No toolkit, validator or builder support is claimed; nothing on this page is a
release statement. Unreleased draft contracts do have a defined reader lane,
rule V7 of [SCHEMA-VERSIONS.md](SCHEMA-VERSIONS.md): explicit opt-in, pinned to
a development-repository commit and schema digest, and warned on for every
record read through it. Because an FHGM record carries no `schema` field, that
lane selects the contract and validator applied to the records, not the file's
routing. That is a statement about reader behavior, not about any tool, and not
an adoption, support or release claim. Finished, adopted contracts publish
through this repository through the normal review and release cycle.

## What FHGM is meant to be

FHGM (FAIR Header Gene Model) is the working name for file-bound metadata that
describes a gene-model contribution — a new or revised model — with enough
information to identify its reference assembly, contributors, evidence,
methods and publication context, so that the model stays interpretable when
its file is downloaded apart from the article or repository that announced it.
The motivating use case is the
[microPublication Biology Gene Models collection](https://www.micropublication.org/journals/biology/collections/genemodels/).
The proposal and its requirements are recorded in
[#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204);
its scope items are model identity and scope, reference coordinates,
new-versus-revision semantics, evidence and methods, credit and publication,
packaging and integrity. The draft record names them `modelId`,
`modelVersion`, `featureId`, `reference`, `predecessor`, `annotates`,
`publication.article`/`deposit` and `reuseConditions`; the 2026-11-14 review
adopted those names as drafted for the draft v0.x line, but they are draft
field names, not a published contract.

## The FHGFF3 file header versus FHGM model records

FHGFF3 and FHGM describe different things and are not alternatives to each
other:

- **FHGFF3 describes the annotation file.** The FHGFF3 header is the file-level
  `#~` block defined by [docs/FHGFF3.md](FHGFF3.md): a released contract
  (`fhgff3.json`; currently `schemaVersion` `"1.2"`, release v0.6.0) covering
  the whole GFF3 file — its identity, taxon, genome link and exact-byte
  checksum.
- **FHGM would describe individual gene-model records.** A model record
  characterizes one contributed model *inside* an annotation. A file can carry
  several such records. Record-level fields and rules exist only as a draft
  contract, not a released one.

FHGM is one model record that can be repeated inside an FHGFF3 annotation:
each record points to a GFF3 feature `ID`, and native GFF3 `ID`/`Parent`
relationships supply transcript and exon structure. The same boundary is
summarized in the [INSDC coverage review's draft FHGM note](insdc-coverage.md)
for annotation categories.

## Adopted decisions and open items

Adopted by the maintainers (decisions, not a published contract):

- **Form (2026-11-12,
  [Option C ruling on #204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204#issuecomment-6829197859)).**
  FHGM is a native gene-model contract with its own record schema,
  requiredness and model-level validation, carried inside FHGFF3 files by
  `x-` extension transport. It is a separately versioned, explicitly selected
  validator over the released FHGFF3 file identity, not a separate file type
  or sibling header contract. This settles the earlier subtype, overlay or
  sibling question. It builds on the five proposed decisions in the
  development repository's contract review, which were
  [agreed on 2026-11-11](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204#issuecomment-6784767088):
  development stays in FHGM-Specification and a reviewed contract publishes
  through this repository, and a resolved predecessor pointer stays separate
  from curator acceptance of a revision.
- **Draft contract.**
  [FHGM-Specification PR #11](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/11)
  (merged 2026-11-12) added the native draft contract v0.1 and its
  model-level checker.
- **Review dispositions (2026-11-14).** The maintainers adopted the
  [FHGM adoption decision packet](proposals/fhgm-adoption-packet.md)
  ([#211 decision record](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-6880245660)).
  The resulting dispositions, recorded in the development repository's
  [`development/CONTRACT-REVIEW.md`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/CONTRACT-REVIEW.md),
  adopt the draft field names; a file-local `modelId` by default; an opaque
  `modelVersion` (equality only, no ordering) through v0.x; selection-only
  contract identity until publication (no in-record contract marker or URI);
  a required record `reference`; predecessor pointers that name their own
  `modelId`; version-gap checks bounded to the supplied snapshots; and a
  duplicate `modelId` as a snapshot-level `ambiguous` rejection. The schema
  stays hand-authored JSON Schema through v0.x
  ([FHGM-Specification#8](https://github.com/FAIR-bioHeaders/FHGM-Specification/issues/8#issuecomment-6882779157)).
- **Both FHGFF3 bases (2026-11-15,
  [#211 decision record](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-6903153378)).**
  The draft accepts FHGFF3 1.1 and 1.2 carriers; see the next section.
- **Real-data vectors (2026-11-15, same record).** Selected real-data cases
  are promoted to the draft's conformance vectors.

The 2026-11-19 [D4–D6 decision record](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7017854934)
and accepted [FHGM PR #34](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/34)
settle the previously listed technical questions: earned per-rule evidence;
complete-empty inventory rejection versus unavailable-input not-run; bounded
supplied-history prerequisites; exactly one root `gene`/`SO:0000704` row with
Parent absent; graph/biology owned by gff3-validator; strict K5 comparability;
and permitted competing model IDs, renamed file-local targets and opaque
A→B→A versions. The promoted expectations received independent review, and
real noncoding gene-scope coverage is included.

The [shared publication candidate](../drafts/fhgm/README.md) carries the exact
accepted owning dependency tree and executable 92-case dual-base suite. It
proposes native contract label `0.1` and a separate model-contract publication
path for joint review; no alias, released contract or FHGM header-registry row
is created. The hand-authored schema mechanism, file-local IDs and dual bases
are settled; they are not new approval questions.

Remaining gates are joint review of that concrete publication package and
actual publication as specification v0.8.0. Curator acceptance of particular
models and external identifier minting authority remain distinct. Transcript-only,
split/merge and assembly-migration scopes are explicitly deferred, not hidden
requirements for this initial gene-scope contract. Project 12 deposit/pilot
work remains separate from the shared foundation.

## How the current pilot is built

The pilot lives in the FHGM development repository,
[FHGM-Specification](https://github.com/FAIR-bioHeaders/FHGM-Specification),
and uses the FHGFF3 extension-field rule ([FORMAT.md R15](FORMAT.md), from
FHGFF3 1.1) to carry the draft records: the embedded model records sit under an
`x-`-prefixed key (`x-fhgm-models` in the reviewed drafts) so the file remains a
schema-valid FHGFF3 header. Two released FHGFF3 bases are carriers: FHGFF3 1.1
(release v0.5.0) and FHGFF3 1.2 (release v0.6.0). By the maintainer decision of
2026-11-15 the draft accepts both, by selection rather than substitution:
[FHGM-Specification PR #17](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/17)
(merged 2026-11-16) registers each base's released bytes by tag and SHA-256
digest in `development/model/base-schemas.json`, and the checker validates a
carrier against the base selected by its cited `schema` URL and reports the
base it used. The file keeps its FHGFF3 `schema` URL and `schemaVersion`; the
records add no coverage to any released contract.

Verified pilot artifacts (see the linked PRs and records for method detail):

- [FHGM-Specification PR #3](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/3)
  (merged 2026-11-10) built the *S6k* fixture: the GFF3 is reproduced from the
  attributed CaltechDATA archive, its transcripts and peptides are verified
  against the named reference assembly, and the headed file is tested against
  the released FHGFF3 schema with an independent checksum recomputation.
- [FHGM-Specification PR #4](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/4)
  (merged 2026-11-10) tested two embedded model records and a revision pointer:
  a synthetic successor annotation carries two records, and the predecessor
  pointer combines the prior annotation checksum with a model ID and version.
- [FHGM-Specification PR #15](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/15)
  (merged 2026-11-14) added the draft conformance vectors, model-level checks
  and a draft model-conformance CI lane.
- [FHGM-Specification PR #18](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/18)
  (merged 2026-11-16) promoted ten real-data rejection cases from
  *Drosophila melanogaster* chromosome 4, with two positive anchors, to draft
  conformance vectors; their
  recorded expectations were independently accepted in FHGM PR #34. Read
  that repository's `development/conformance/manifest.json` for the current set.
- The draft requirements review — the comparison worksheet
  [`development/FHGFF3-COMPARISON.md`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/FHGFF3-COMPARISON.md),
  the decision record
  [`development/CONTRACT-REVIEW.md`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/CONTRACT-REVIEW.md),
  the source review of inspected deposits in
  [`development/examples/PILOT.md`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/examples/PILOT.md),
  and the draft contract and checker under
  [`development/model/`](https://github.com/FAIR-bioHeaders/FHGM-Specification/tree/main/development/model) —
  is draft material for #204, not a published contract.

### What the pilot checks, and what it does not

The pilot deliberately separates two kinds of outcome:

- **File integrity.** The FHGFF3 schema check validates the header structure and
  genome link; the checksum covers the full file's exact bytes, including every
  embedded model record. A stale or edited file fails integrity regardless of
  what its records say.
- **Model-level revision resolution.** The pilot showed that the released base
  schema accepts the extension records *even when a revision pointer names an
  unchanged neighbor model or a stale predecessor file* — those files still
  pass schema and integrity checks. Resolving a pointer (prior annotation
  checksum plus model ID plus version, same assembly) therefore requires a
  separate model-level check, which the draft validator in the development
  repository performs on top of the base schema. And a resolved pointer only
  identifies a predecessor record: whether a revision is *accepted* is a
  curator decision with its own evidence, which no header check establishes.

This matches the boundary drawn in
[#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204):
evidence assertions, feature validity (gff3-validator), reference matching,
file integrity and biological or curatorial acceptance are distinct checks.
A valid header never establishes a correct model.

## The FHGM development repository

[FHGM-Specification](https://github.com/FAIR-bioHeaders/FHGM-Specification) was
created on 2026-11-05 as a fork of `FAIR-bioHeaders/FHGFF3` (itself derived from
the biodatamodels/gff-schema lineage). Its GitHub description, "LinkML schema
for GFF3, the Genome Feature Format for Gene Models", reflects that inherited
baseline, not an implemented FHGM schema. What the repository actually contains
today:

- `development/` — the active FHGM work: the requirements plan, the FHGFF3
  comparison worksheet, the draft contract review record for #204, the source
  review of microPublication deposits, the pilot fixtures (the *S6k* case,
  a synthetic revision case, minimal/rich contract fixtures and the
  *Drosophila* chromosome 4 real-data cases), the native draft contract and
  model-level checker under `development/model/`, and the draft conformance
  suite under `development/conformance/`.
- `header/` — an unmodified pinned copy of the shared FHGFF3 header model kept
  as a reference baseline
  ([`header/provenance.json`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/header/provenance.json),
  pinned to the shared specification's v0.6.0 release tag since 2026-11-18);
  the copy is not an editable FHGM model.
- `src/`, `jsonschema/`, `python/`, `rdf/`, `owl/`, `shex/`, `graphql/`, `csv/` —
  inherited biodatamodels/gff-schema feature-model material, retained with its
  original identity. That inherited material is outside this native-contract
  candidate; its notices and provenance must be preserved separately.
- CI in that repository verifies documentation and the inherited FHGFF3
  baseline, and a draft model-conformance workflow runs the draft FHGM vectors
  and checker against both FHGFF3 bases. That lane checks the draft, not a
  released contract, and the repository states plainly that it makes no FHGM
  contract, schema version, release or toolkit support claim.

Do not read files in `FHGM-Specification` as published contracts. Baseline
fixtures there are reference material, and the repository's own guidance is that
they must never be relabeled as adopted FHGM examples.

## Deferred — explicitly not stated here

- Normative (published) field names, requiredness, types or cardinalities for
  FHGM records. The `x-fhgm-models` shape and the field names adopted in the
  2026-11-14 review are draft, held under rule V7 until a shared publication.
- Any released schema version, `schemaVersion` value or w3id URL for FHGM, and
  any entry in `schemas/versions.json`.
- Any claim that the `fair-bioheaders` toolkit, `gff3-validator`, the metadata
  builders or the website support FHGM. Family support, serialization choices
  and version dispatch are decided only after #204 resolves.
