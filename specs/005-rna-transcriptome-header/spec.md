# Feature Specification: RNA and transcriptome FASTA header (FHT)

**Feature Branch**: `005-rna-transcriptome-header`

**Created**: 2026-10-08

**Status**: Draft. Requirements synced on 2026-11-02 with the FHT 1.0 development
contract, which is not released.

**Input**: Grant Aim 1 names reference transcriptomes as the next header. FHT is
developed in [FHT-Specification](https://github.com/FAIR-bioHeaders/FHT-Specification),
which owns the model and its revision of this spec (#107). This copy follows
FHT-Specification at
[`9dae29b`](https://github.com/FAIR-bioHeaders/FHT-Specification/tree/9dae29b26d1204307d8defdd7934956900b0ded1):
the revised [spec 005](https://github.com/FAIR-bioHeaders/FHT-Specification/blob/9dae29b26d1204307d8defdd7934956900b0ded1/specs/005-rna-transcriptome-header/spec.md),
the LinkML model `fht_linkml.yml` and the generated `fht.json` (merged in
FHT-Specification PR #21). Where this text and that `fht.json` disagree, `fht.json`
is the contract. The original 2026-10-08 draft (required `moleculeType` of
`mRNA | total RNA | cDNA | ncRNA`) is superseded.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish a de novo transcriptome with provenance (Priority: P1)

A lab assembles a transcriptome from reads without a reference genome (for example
with Trinity) and embeds who built it, from which samples, with which tools, and
its completeness. No genome parent is invented.

**Independent Test**: Combine an FHT header onto a small transcript FASTA;
validate, strip, round-trip all serialisations; checksum verifies.

### User Story 2 - Genome-guided transcript set (Priority: P1)

A lab reconstructs read-supported transcript models using a reference genome. The
genome is documented, but guidance alone is not a sequence-derivation parent link.

### User Story 3 - Annotation-derived transcript set linked to its genome (Priority: P1)

A transcript FASTA extracted from existing annotation coordinates and the matching
genome identifies both sources. An FHR-headed genome can be a `transcribedFrom`
parent; the annotation is linked as context.

## Requirements *(mandatory)*

- **FR-001**: FHT imports the shared core and shared objects pinned at
  `980029e5886a1a56a2d2545bfe59c7107539d38d` (v0.4.0/v0.4.1) and adds the
  required non-blank subject slot `transcriptome`. Exactly nine fields are
  required: `schema`, `schemaVersion` (the string `"1.0"`, proposed, not
  released), `transcriptome`, `assemblyType`, `taxon`, `version`,
  `metadataAuthor`, `dateCreated` and `checksum`.
- **FR-002**: `assemblyType` is required: `de novo`, `genome-guided` or
  `annotation-derived`. There is no `mixed` or `unknown` value; a composite or
  uncertain history leaves the record incomplete. `moleculeType` is optional: one
  biological class for the whole set, `mRNA`, `rRNA`, `tRNA` or
  `transcribed RNA`. `total RNA` and `cDNA` are preparation contexts and are not
  accepted; unknown or heterogeneous sets omit the field.
- **FR-003**: Optional FHT fields: `assemblySoftware` (ordered shared `Software`
  objects), `sample`, `libraryStrategy` (one supplied strategy string, not an ENA
  enum), `strandedness` (`unstranded`, `forward` or `reverse`, where forward means
  the single read or read 1 is sense relative to the transcript), `sequencingRuns`
  (items match `^(SRR|ERR|DRR)[0-9]+$`; an SRS sample accession is not a run),
  `vitalStats`, `completeness` and `derivedFrom`, plus the legacy-compatible
  `transcriptomeSynonym` (non-blank strings), `assemblyAuthor` (shared `Author`
  objects, distinct from `metadataAuthor`) and `instrument` (free-text names).
  The shared optional fields `identifier`, `accessionID`, `scholarlyArticle`,
  `documentation`, `relatedLink`, `funding`, `reuseConditions` and
  `voucherSpecimen` also apply. Optional arrays need at least one item when
  present; unknown values are omitted, not written as empty strings or `null`.
- **FR-004**: `sample` is a non-empty array of `Sample` objects with optional
  `tissue`, `tissueIdentifier` (a CURIE, preferably UBERON, PO or CL; form is
  checked, not resolution), `developmentalStage`, `condition` and `strain`. Each
  entry carries at least one of these, with non-blank text. Pooled material is
  repeated entries, not one fabricated uniform sample.
- **FR-005**: `vitalStats` holds `totalTranscripts` (integer >= 0, FASTA records
  including isoforms), `N50` (integer >= 1) and `averageTranscriptLength`
  (number >= 0). `completeness` reuses the shared BUSCO count object; its
  `lineageDataset` must match `^[a-z0-9_]+_odb[0-9]+$`, so dotted dataset versions
  such as `odb12.2` are rejected and stay in `documentation`, not renamed, until
  #170 decides.
- **FR-006**: `derivedFrom` is a non-empty ordered array accepting only
  `headerType: FHT` with `relationship: filteredFrom`, or `headerType: FHR` with
  `relationship: transcribedFrom` when transcript bases were extracted from that
  genome. Each item requires the parent checksum; `accessionID` is additional,
  never a substitute. Genome guidance alone is not `transcribedFrom`. FHGFF3
  annotations, projects, samples, runs and protocols go in
  `relatedLink`/`documentation`.
- **FR-007**: Drop genome-only fields (`masking`) from FHT; keep the FHT examples
  schema-valid with real checksums.
- **FR-008**: The legacy `fht.json` is preserved verbatim in FHT-Specification
  `legacy/fht-v0.1.json`, and the model is LinkML with a generated JSON Schema.
- **FR-009**: RNA FASTA may use U for uracil; header parsing and checksums are
  alphabet-independent.

## Success Criteria *(mandatory)*

- **SC-001**: FHT released with examples, conformance vectors and DOI
  (FHT-Specification #8 and #10).
- **SC-002**: At least one real public transcriptome carries an FHT header.

## Assumptions

- The forked FHT-File-Converter is retired in favour of the multi-format toolkit (008);
  FHT toolkit support is FHT-Specification #9.
