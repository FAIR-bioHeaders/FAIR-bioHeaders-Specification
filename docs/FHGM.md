# FHGM: FAIR header gene model — draft overview

**Status: draft documentation of a proposal under review. There is no FHGM
contract.** FHGM has no released JSON Schema or LinkML model, no
`schemaVersion`, no w3id schema URL, and no entry in the version registry
[`schemas/versions.json`](../schemas/versions.json) — that registry lists
released contracts only. Contract ownership, required fields, serialization
and model-level validation are under review in
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
its candidate scope items (model identity and scope, reference coordinates,
new-versus-revision semantics, evidence and methods, credit and publication,
packaging and integrity) are *concepts under review, not adopted field names*.

## The FHGFF3 file header versus FHGM model records

FHGFF3 and FHGM describe different things and are not alternatives to each
other:

- **FHGFF3 describes the annotation file.** The FHGFF3 header is the file-level
  `#~` block defined by [docs/FHGFF3.md](FHGFF3.md): one released contract
  (`schemaVersion` `"1.1"`, `fhgff3.json`) covering the whole GFF3 file — its
  identity, taxon, genome link and exact-byte checksum.
- **FHGM would describe individual gene-model records.** A model record
  characterizes one contributed model *inside* an annotation. A file can carry
  several such records. Record-level fields and rules do not exist yet as a
  contract.

The working design in #204 treats FHGM as one model record that can be repeated
inside an FHGFF3 annotation: the current pilot embeds repeatable model-level
records in an FHGFF3 file, and each experimental record points to a GFF3 feature
`ID`; native GFF3 `ID`/`Parent` relationships supply transcript and exon
structure. The record shape, requiredness, serialization and validation rules
remain subject to joint maintainer review. Whether FHGM ends up as a subtype, a
separately versioned overlay selected at validation time, or a sibling contract
is one of the open decisions in #204. The same boundary is summarized in the
[INSDC coverage review's draft FHGM note](insdc-coverage.md) for annotation
categories.

## How the current pilot is built

The pilot lives in the FHGM development repository,
[FHGM-Specification](https://github.com/FAIR-bioHeaders/FHGM-Specification),
and uses the FHGFF3 1.1 extension-field rule
([FORMAT.md R15](FORMAT.md)) to carry the experimental records: the embedded
model records sit under an `x-`-prefixed key (`x-fhgm-models` in the reviewed
drafts) so the file remains a schema-valid FHGFF3 1.1 header. The file keeps its
FHGFF3 `schema` URL and `schemaVersion`; the records add no coverage to any
released contract.

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
- The draft requirements review — the comparison worksheet
  [`development/FHGFF3-COMPARISON.md`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/FHGFF3-COMPARISON.md),
  the decision record
  [`development/CONTRACT-REVIEW.md`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/CONTRACT-REVIEW.md),
  the source review of inspected deposits in
  [`development/examples/PILOT.md`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/examples/PILOT.md),
  and the draft overlay validator under
  [`development/model/`](https://github.com/FAIR-bioHeaders/FHGM-Specification/tree/main/development/model) —
  is review input for #204, not a proposed published contract.

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
  review of microPublication deposits, and the pilot fixtures (the *S6k* case,
  a synthetic revision case, and minimal/rich contract fixtures) with a draft
  overlay validator added 2026-11-10.
- `header/` — an unmodified pinned copy of the shared FHGFF3 header model kept
  as a reference baseline
  ([`header/provenance.json`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/header/provenance.json));
  the pin predates current shared main and the copy is not an editable FHGM
  model.
- `src/`, `jsonschema/`, `python/`, `rdf/`, `owl/`, `shex/`, `graphql/`, `csv/` —
  inherited biodatamodels/gff-schema feature-model material, retained with its
  original identity. The inherited upstream licensing question is unresolved, as
  it is in the FHGFF3 repository (see the repository README and
  [FHGFF3#3](https://github.com/FAIR-bioHeaders/FHGFF3/issues/3)); MPL-2.0 on
  FAIR BioHeaders contributions does not settle it.
- CI in that repository verifies documentation and the inherited FHGFF3 baseline;
  it does not validate FHGM, and the repository states plainly that it makes no
  FHGM contract, schema version, release or toolkit support claim.

Do not read files in `FHGM-Specification` as published contracts. Baseline
fixtures there are reference material, and the repository's own guidance is that
they must never be relabeled as adopted FHGM examples.

## Deferred — explicitly not stated here

- Normative field names, requiredness, types or cardinalities for FHGM records
  (the `x-fhgm-models` shape is a draft validation proposal under #204 review).
- Any released schema version, `schemaVersion` value or w3id URL for FHGM, and
  any entry in `schemas/versions.json`.
- Any claim that the `fair-bioheaders` toolkit, `gff3-validator`, the metadata
  builders or the website support FHGM. Family support, serialization choices
  and version dispatch are decided only after #204 resolves.
