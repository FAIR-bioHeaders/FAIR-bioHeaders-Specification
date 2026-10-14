# Research: Protein FASTA header (FHP)

**Feature**: 006-protein-header | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md) (clarified 2026-10-11)

Observations about real practice are in [research-notes.md](research-notes.md) (N-01 to N-08).
This file records the design decisions, each with its rationale and the alternatives considered.

## D-01 Files and layout

**Decision**:
- `fhp_linkml.yml` (repository root, next to `fhr_linkml.yml`) imports `schemas/core.yaml`.
- `fhp.json`, the published FHP JSON Schema, is **generated** from it by
  `json-schema-generator.py --type fhp` and committed.
- Examples go in `examples/fhp/`, the format document is `docs/FHP.md`, and the schema review
  baseline is `.github/schema-baseline-fhp.json`.

**Rationale**:
- This mirrors FHR, so readers find the files where they expect them.
- The `examples/fhp/` subdirectory keeps the FHR example run (`validate_examples.py`, which reads
  `examples/*` non-recursively) unchanged.
- FHP has no hand-written legacy schema to preserve. Generating `fhp.json` removes a second
  source of truth, and `check_linkml.py` then guards against hand edits.

**Alternatives**:
- A `fhp/` directory holding schema, examples and docs: it is tidier per type, but splits the
  shared tooling's path conventions, and FHR would stay at the root anyway.
- A hand-written `fhp.json` checked against LinkML like `fhr.json`: that doubles the work with no
  compatibility reason.

## D-02 Header type discrimination

**Decision**: The FHP schema constrains `schema` to a raw GitHub URL of
`FAIR-bioHeaders/FAIR-bioHeaders-Specification/<ref>/fhp.json`. Tools select the FHP schema when `schema`
matches that pattern, and the FHR schema otherwise.

**Rationale**:
- Spec 004 FR-004 and spec FR-011 say the `schema` URL identifies the type.
- FHR's `schema` is an unconstrained string, so the default must stay FHR. That keeps every
  existing FHR file and tool result byte-identical (SC-005).
- Raw-main is canonical (website#15, spec#44 proposal).

**Alternatives**:
- A top-level `headerType: FHP` field: it duplicates the schema URL and adds a required field.
- Sniffing residues: rejected by FR-011.
- Also allowing a `w3id.org/fair-bioheaders/fhp/vX.Y.Z` form now: no such rule or tag exists
  yet. It can be added additively when a release alias is registered (follow-up F-05).

## D-03 schemaVersion

**Decision**: FHP `schemaVersion` is the number 1, written as `enum: [1]` in `fhp.json`.

**Rationale**: Each header type versions its own schema. `enum` is the form v0.4 chose for FHR
"so later versions can be listed". A `1.0` in YAML still validates, because JSON Schema compares
numbers by value.

**Alternatives**: Keep LinkML's `const: 1`, which is equivalent but inconsistent with v0.4.

## D-04 Prediction software object

**Decision**: A generic `Software` class in `fhp_linkml.yml` (name required; URI, version and
ordered `commandLineOption`), with FHR's `AssemblySoftware` shape and slot URIs.

**Rationale**:
- FR-008 asks for "the same structured software object as FHR's".
- FHR's class is described as assembly software and lives in the FHR module. Moving it would
  change FHR's generated vocabulary text and touch the core, which the clarification keeps
  unchanged.

**Alternatives**:
- Move a generic `Software` class into the core now: better reuse once FHT or FHGFF3 need it.
  This is recorded as follow-up F-06.
- Import `fhr_linkml.yml` into FHP: it would bring in FHR's tree root and genome slots.

## D-05 External sources (clarification Q2)

**Decision**: An optional `source` list of `Source` objects:
- `name` (required);
- optional `release`, `setIdentifier`, `url`, `assemblyAccession`, `sequenceCount` (≥ 0) and
  `description`.

It sits beside the core's checksum-only `derivedFrom`.

**Rationale**:
- Database releases have no FAIR-bioHeaders checksum (N-08).
- A separate list keeps asserted sources apart from verifiable links (FR-013) and leaves the core
  unchanged.
- `assemblyAccession` covers UniProt's stated assembly for a proteome (N-01) without pretending
  to be a link.
- `description` covers manual curation and other contributions in mixed sets (US3).

**Alternatives**:
- Let `derivedFrom` hold accession-only parents: rejected in the clarification.
- One `sourceDatabase` object: it cannot describe mixed sets.

## D-06 sourceType (clarification Q1)

**Decision**: Required enum `predicted | database | mixed`, defined by origin (spec FR-005).

**Rationale**: Review status is per sequence in UniProt (`sp`/`tr`), so a whole-file "curated"
label would mislabel reference proteomes and Ensembl `pep.all` files (N-01, N-02).

**Alternatives**: Recorded in the clarification.

## D-07 Value constraints

**Decision**:
- `geneticCode`: an integer in 1–6, 9–16 or 21–33, generated as three `anyOf` ranges (N-05).
- `isoformPolicy`: `all | longestPerGene | canonicalPerGene`. Absence means not stated.
- `completeness`:
  - `lineageDataset` is required and must match `^[a-z0-9_]+_odb[0-9]+$`, so the version suffix
    (odb10, odb12) is always present (FR-009);
  - the counts `completeSingle`, `completeDuplicated`, `fragmented`, `missing` and `total` are
    required;
  - `buscoVersion` and `mode` (`proteins | transcriptome | genome`) are optional.
- `sequenceStats`: optional non-negative integers `sequenceCount`, `geneCount` and
  `totalResidues`.
- Every FHP object is closed, with no extra keys and no `null` (FR-010). This includes the core
  `Taxon`, `Author` and `AccessionID` objects, which stay open only for legacy FHR on `main`.

**Rationale**:
- Counts are comparable and exact, while percentages are derived (N-06).
- The unused table IDs 7, 8 and 17–20 are rejected.
- Closed objects follow v0.4.

**Alternatives**:
- A BUSCO percentage string (`C:..%[S:..]`): it can't be validated and loses n.
- One `geneticCode` range 1–33: it accepts unused IDs.
- Open core objects for FHP: new types have no legacy to preserve.

## D-08 JSON-LD and microdata

**Decision**:
- The FHP LinkML slots and classes carry `slot_uri`/`class_uri` annotations now:
  - `proteome` → `sdo:name`; the root `sdo:Dataset`; `Software` → `sdo:SoftwareApplication`;
  - other slots default to `fhr:` terms in the family-wide vocabulary.
- Extending `make_jsonld.py` to a second header type, with an FHP context, FHP terms in
  `terms.ttl`/`TERMS.md` and mapping-table rows, is deferred (follow-up F-01).
- Microdata for FHP is deferred too (F-02).
- In the meantime the toolkit refuses to write FHP as JSON-LD or microdata, rather than emitting
  FHR-typed output.

**Rationale**:
- `make_jsonld.py` is built around the single FHR root: its counts, the mapping table's
  `fhr.json` path set and its 116 tests.
- Generalising it is a feature-sized change, and half-doing it would publish an inconsistent
  vocabulary.
- The annotations cost nothing now and make F-01 mechanical.

**Alternatives**: Generalise the generator in this feature. That roughly doubles the work, and
the JSON-LD tests would need a per-type structure first.

## D-09 Conformance vectors

**Decision**:
- **Format**: a new manifest format `fhp-fasta` (container FASTA, prefix `;~`, suffix
  `.fhp.fasta`), produced by `make_conformance.py` beside the FHR vectors.
- **New rules**: two FHP rules in `docs/FHP.md`, which joins `RULE_DOCUMENTS`:
  - **P1**: the metadata must validate against `fhp.json`;
  - **P2**: a record cites an FHP schema URL to be read as FHP. A protein FASTA whose `schema` is
    not an FHP URL is validated as FHR.
- **Shared rules**: the FHP vectors also exercise R1–R10 on amino-acid bodies.
- **Checking**: `check_conformance.py --schema` validates `fhp-fasta` vectors against `fhp.json`.
  The CI step that runs the released converter (fhr 0.3.3) skips `fhp-fasta`, as it skips
  `jsonld`.

**Rationale**:
- One manifest and one generator keep the independent checksum oracle shared (FR-017).
- A separate format id lets older converters be skipped cleanly and keeps FHR vector counts
  unchanged.

**Alternatives**:
- A separate `conformance/fhp/` manifest: it duplicates the oracle and its checks.
- Reusing format `fasta`: old converters would then fail the FHP vectors instead of skipping
  them.

## D-10 Toolkit: schema selection and link checks

**Decision**:
- **Schema selection**: the toolkit bundles `fhp_schema.json` (a byte-identical copy of
  `fhp.json`, checked by `check_release.py`). `fhr.fhr_validate()` selects the schema from
  `schema` (D-02), so every command (validate, verify, combine, convert, assess) gains FHP with
  no new flags. FHR results and messages stay byte-identical.
- **Messages**: FHP messages name FHP, for example "FHP metadata is valid."
- **Extensions**: `.faa` joins the FASTA extensions.
- **Default combine output**: `X.fhp.fasta` for FHP records.
- **`bioheaders verify-links FILE PARENT...`**:
  - computes each supplied parent's family checksum from its bytes (FASTA and GFA containers);
  - reports each recorded `derivedFrom` entry as `matched`, `not matched` or `not checked`, and
    each supplied file that matches no entry;
  - never writes. The rules are in contracts/cli.md.
  - Parents in containers the toolkit cannot checksum yet (GFF3 until spec 007) are reported as
    `not checked`, naming the reason.

**Rationale**:
- A single selection point gives one behaviour everywhere, as spec 008 asks.
- Computing from bytes is what makes a match mean identity (FR-014).
- GFF3 header rules are not specified yet, and guessing them would bake in an unreviewed
  container rule.

**Alternatives**:
- A `--type fhp` flag: easy to forget, and it contradicts FR-011.
- Trusting a parent's stated checksum: it proves nothing about the bytes.
- Treating GFF3 like GFA now: that is a guess about spec 007 (follow-up F-03).

## D-11 Assessment and website

**Decision**:
- **Assessment**: `bioheaders assess` already reports schema conformance through the toolkit's
  validation, so with D-10 it reports FHP conformance. Only the suggestion text that calls FHP a
  future draft changes, to "FHP is a draft specification (not released)".
- **Website**: the Draft entry on fair-bioheaders.github.io is a separate repository. It is
  prepared as a follow-up issue/PR text (F-04), not done here.

**Rationale**: Small and in scope for the assessment. The website is David's repository, and its
content needs his review.

## D-12 Branches and v0.4

**Decision**:
- FHP is developed on `main`; `fhr.json` is untouched.
- The next main → `release-v0.4` sync brings FHP to v0.4, where it inherits the tightened core
  patterns (anchored taxon and ORCID URIs, padded checksum).
- On `main`, FHP inherits the v0.3 core patterns.
- A release of FHP v0.1 should be cut from a line that has the v0.4 core. That is a maintainer
  release decision, recorded as F-07.

**Rationale**: FHP is additive, and the core patterns are a property of the branch, not of FHP.

**Alternatives**: Develop FHP on `release-v0.4` only. That would delay toolkit support, because
the toolkit tracks `main`.

## D-13 Examples

**Decision**: Six examples in `examples/fhp/`: minimal and rich for each of predicted, database
and mixed, plus one embedded FASTA (`example.fhp.fasta`) with an amino-acid body.

- The database examples describe the UniProt human reference proteome download: `UP000005640`,
  release `2026_03`, assembly `GCA_000001405.29`.
- The rich database example also gives the protein count (147520), gene count (20652) and BUSCO
  report (primates_odb10: S 5103, D 8613, F 5, M 59, n 13780). These are UniProt's published
  values for that proteome, fetched 2026-10-10 (N-01), and the example cites them as such.
- The examples carry no sequence data from UniProt, and their checksums are placeholders, as in
  FHR's standalone examples (docs/FORMAT.md, "Migration").
- The predicted and mixed examples are synthetic. Their names, checksums and identifiers are
  labelled as placeholders (FR-016, constitution IV).

**Rationale**: Real, accurately described identifiers make the examples useful, and labels keep
them honest.
