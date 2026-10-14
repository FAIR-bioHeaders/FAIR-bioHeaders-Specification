# Feature Specification: FAIR-bioHeaders family of file headers

**Feature Branch**: `003-bioheaders-family`

**Created**: 2026-10-08

**Status**: Draft (umbrella)

**Input**: Extend FHR's approach to other core file types: nucleotide (DNA) and
RNA/transcriptome FASTA, protein FASTA, and GFF3 annotation. This follows the
grant aims (Aim 1: "extend the concepts we applied to create ... FHR to more file
types", schemas in LinkML; Aim 2: tools, generated libraries, profiles, upstream
tool support) and the paper's design goals (unambiguous provenance, metadata
close to data, many implementations, FAIR and TRUST).

## Scope and naming

| Header | File type | Sequence alphabet | Status |
| --- | --- | --- | --- |
| FHR | Reference genome FASTA/GFA | DNA | Released (v0.3.1) |
| FHT | Reference transcriptome FASTA | RNA/cDNA | WIP fork; `fht.json` does not parse |
| FHP | Protein FASTA (proteomes) | amino acid | New |
| FHGFF3 | GFF3 genome annotation | none (features; optional `##FASTA`) | LinkML GFF3 fork with validator prototype |

Child specs: 004 shared core, 005 RNA/transcriptome, 006 protein, 007 GFF3,
008 multi-format tools and libraries, 009 one-stop GFF3 validator. Non-genome nucleotide sets (marker panels, plasmids, contig sets) use FHR with a relaxed community profile (decided in #54). 009 specifies the GFF3 validator.

## Principles carried over from FHR (non-negotiable)

1. YAML header lines with a two-character prefix (`;~` in FASTA, `#~` in GFA/GFF3),
   forming the leading header block (docs/FORMAT.md R10).
2. One checksum definition for every type: SHA-512/256 over the exact
   (decompressed) file bytes except the single root checksum line, padded base64
   (R1–R4). Same parsing rules R5–R8.
3. Small required core; optional fields for everything else.
4. Serialisations JSON, YAML, HTML microdata (and JSON-LD, see 008) are
   interconvertible for every type.
5. Each header type has byte-exact conformance vectors like `conformance/`.

## The new capability: provenance links between files

The family's main value over separate headers is that derived files can name the
exact file they came from by its FHR-family checksum (plus GA4GH SeqCol digest
where applicable):

```
genome (FHR) ──annotated by──> GFF3 (FHGFF3) ──translated to──> proteins (FHP)
      └──────transcripts from──> transcriptome (FHT)
```

A shared `derivedFrom` structure (004) records the parent's header type, checksum,
optional SeqCol ID, accession and relationship. Tools (008) can verify that a
parent file on disk matches the recorded checksum.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Annotate a genome with traceable provenance (Priority: P1)

A curator publishes a genome (FHR), its annotation (FHGFF3) and its proteome
(FHP). A downstream user can check, offline, that the annotation and proteins
belong to exactly that assembly version.

**Independent Test**: Combine headers onto the three files; `verify-links` with
the genome present succeeds, and fails after the genome is swapped for another
version.

### User Story 2 - One toolkit for every header type (Priority: P1)

A pipeline author installs one package (PyPI/Bioconda) and gets convert, validate,
combine, strip and checksum for all four types, with identical behaviour.

### User Story 3 - Community profiles (Priority: P2)

AgBioData (or another community) publishes a profile adding naming and
required-field rules on top of a header type; validation can enforce it.

### User Story 4 - Use from other languages (Priority: P3)

R, Java, JavaScript and Julia users read and validate headers with libraries
generated from the LinkML schemas, checked against the conformance vectors.

## Requirements *(mandatory)*

- **FR-001**: Every header type MUST be defined in LinkML importing the shared
  core (004), with generated JSON Schema as the published validation contract.
- **FR-002**: Checksum and header-parsing rules MUST be shared and specified once
  (docs/FORMAT.md, generalised per container in 008).
- **FR-003**: Each type MUST ship examples, conformance vectors, a CHANGELOG and a
  Zenodo-archived release, following the FHR release process.
- **FR-004**: Existing FHR metadata MUST remain valid (FHR schemaVersion 1 stays
  compatible; the core refactor is not a breaking change for FHR users).
- **FR-005**: Repository layout: a single specification monorepo (FAIR-bioHeaders-Specification) with a directory per header type; the core, parsing rules, conformance tooling and CI are shared; releases are tagged per type (decided in #54).

## Success Criteria *(mandatory)*

- **SC-001**: All four types validate, convert and verify with one toolkit.
- **SC-002**: The genome → annotation → proteome link check works on a real
  public dataset (e.g. an Alliance or AgBioData organism).
- **SC-003**: Each type has a published release, DOI and conformance vectors.
- **SC-004**: At least one community profile and one generated non-Python library
  pass the conformance vectors.

## Assumptions

- David and Adam hold schema authority for all types (GOVERNANCE.md).
- Field choices are consulted with curators via the Alliance, AgBioData and GA4GH
  (grant A.1.1–A.1.2); drafts here are starting points, not final field lists.
