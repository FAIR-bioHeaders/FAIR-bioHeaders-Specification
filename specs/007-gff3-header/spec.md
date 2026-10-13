# Feature Specification: GFF3 annotation header (FHGFF3)

**Feature Branch**: `007-gff3-header-spec`

**Created**: 2026-10-08 (draft), rewritten 2026-10-13

**Status**: Draft (clarified 2026-10-13)

**Input**: User description: "Specify `#~` header lines after `##gff-version 3`, ending at the first
feature or `##FASTA`. The checksum covers the whole file, including `##FASTA`. Fields: required
genome link (`derivedFrom`, relationship `annotates`), annotation software, evidence, Sequence
Ontology version, and feature counts." The inputs are:
- issue #48, the FHGFF3 parts of #50, FAIR-bioHeaders-Tools#33 and #34, and gff3-validator rules
  HDR-004 to HDR-009;
- umbrella spec 003, core spec 004 and the multi-format tools spec 008;
- the maintainer decisions in #54 and the FHP decisions of 2026-10-11 (spec 006);
- David Molik's implementation context on #48 and #55.

**Research**: [research-notes.md](research-notes.md) (GFF3 directives, NCBI and Ensembl headers,
annotation tools, Sequence Ontology releases, genome identity, current FAIR-bioHeaders state).

## Clarifications

### Session 2026-10-13

- Q: How is the accession-plus-SeqCol genome link represented? → A: A separate genome-reference
  object (accession and SeqCol digest, both required) beside the checksum-only core `derivedFrom`.
  A schema rule requires at least one of the two genome-link forms. The core is unchanged (FR-006).
- Q: What do tools do with native GFF3 directives that describe the same thing as the header? →
  A: They cross-check them (`##species`, `##genome-build`, `#!genome-build`,
  `#!genome-build-accession`) and report disagreements as warnings, never rewriting either
  (FR-011).
- Q: Is there a required field for how the annotation was made? → A: No. Method and origin go in
  the optional software, protocol and `source` values (FR-013).

## Purpose and ethos

An annotation is only meaningful against the exact assembly it describes, and GFF3 files are the
files most often separated from that assembly. FHGFF3 is **a provenance header around ordinary
GFF3**. It adds a small YAML block of `#~` comment lines after `##gff-version 3` and one checksum
over the file's exact bytes. The block records which genome the annotation belongs to and how it
was made.

FHGFF3 records **asserted provenance**. It is not a feature validator and not a quality report:
- a header never makes the features valid;
- a plain GFF3 file without a header stays valid GFF3;
- feature validation stays in the gff3-validator (spec 009), and its results are reported apart
  from header results.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bind an annotation to its FHR genome by checksum (Priority: P1)

An annotation group annotates a genome that carries an FHR header and attaches an FHGFF3 header to
the resulting `genes.gff3`. The header names the genome as the annotated parent by its FHR checksum.
A user who later receives the GFF3 and a genome file can confirm, offline, that this is exactly the
genome the coordinates refer to.

**Why this priority**: This is the problem FHGFF3 exists to solve. It is also the middle link of
the genome → annotation → proteome chain that FHP (spec 006) already points to.

**Independent Test**:
1. Attach an FHGFF3 header to a small GFF3 whose genome has an FHR header.
2. Check the GFF3's own checksum.
3. Check the genome link with the genome present. It matches.
4. Change one byte of the genome. The link is reported as not matched.

**Acceptance Scenarios**:

1. **Given** a GFF3 file and an FHGFF3 record with the required fields, **When** the header is
   attached, **Then** line 1 is still `##gff-version 3`, the `#~` lines follow, the checksum is
   computed exactly as for FHR (R1–R4), and every other byte is unchanged.
2. **Given** a header whose genome link is an FHR checksum, **When** the genome file is supplied,
   **Then** a link check reports matched or not matched. A match means file identity: it does not
   say the features are correct.
3. **Given** the genome file is not supplied, **When** links are checked, **Then** the genome link
   is reported as "not checked (file not supplied)", distinct from "not matched".

---

### User Story 2 - Bind an annotation to a genome that has no FHR header (Priority: P1)

A curator re-annotates a public assembly that is distributed without an FHR header, for example
an NCBI `GCF_` or Ensembl FASTA. The FHGFF3 header identifies the genome by its accession and
version plus its SeqCol digest, as #54 allows. It does not claim a file checksum the curator never
computed.

**Why this priority**: Most annotated genomes today have no FHR header (research G-06). Without
this route, FHGFF3 could only be used after the genome had been re-published, which defeats low
adoption effort.

**Independent Test**: Validate a record whose genome link is an accession plus SeqCol digest and
which has no FHR checksum for the genome. It is valid. A link check reports the link as "asserted,
not verifiable by file checksum", unless a genome is supplied whose own FHR header records the same
accession or SeqCol digest.

**Acceptance Scenarios**:

1. **Given** a record whose genome link has an accession and a SeqCol digest, **When** it is
   validated, **Then** it is valid.
2. **Given** a record whose genome link has an accession but no SeqCol digest, or a SeqCol digest
   but no accession, and no FHR checksum, **When** it is validated, **Then** it is invalid, and the
   message names the missing half of the alternative.
3. **Given** a record with no genome link at all, **When** it is validated, **Then** it is invalid.
4. **Given** an accession-plus-SeqCol link and a supplied genome file with no FHR header,
   **When** links are checked, **Then** the result is "not checked". The tools do not compute
   SeqCol digests in v0.1 and never report an accession as a verified file identity.

---

### User Story 3 - Plain GFF3 workflows keep working (Priority: P1)

A pipeline that knows nothing about FAIR-bioHeaders keeps reading, sorting, indexing and
converting GFF3 files. Files with an FHGFF3 header load in the common GFF3 tools, because `#~`
lines are comments. A GFF3 file without a header is still plain, valid GFF3 to the validator.

**Why this priority**: The GFF3 ecosystem is large and conservative. Any break would block
adoption, and David's guidance requires that the plain-GFF3 workflow is preserved.

**Independent Test**:
1. Validate a GFF3 file without a header. It has no header error by default.
2. Run the surveyed tools (docs/TOOL_COMPATIBILITY.md) on the same file with a header. Their
   outputs match the plain file's.
3. Strip the header. Exactly the header lines are removed.

**Acceptance Scenarios**:

1. **Given** a valid GFF3 file without `#~` lines, **When** it is validated without
   `--require-header`, **Then** there is no header error, and the feature results are unchanged.
2. **Given** a file with a valid header and an invalid feature, **When** it is validated, **Then**
   the feature error is reported, and the header result is reported separately as valid.
3. **Given** a file with an invalid header and valid features, **When** it is validated, **Then**
   the header error is reported, and the feature results are reported separately as valid.
4. **Given** a file with a header, **When** it is stripped, **Then** only the `#~` lines are
   removed, and every native directive, `#!` line, comment, feature and `##FASTA` byte is kept in
   order.

---

### User Story 4 - Header tooling on GFF3, including `##FASTA` and compression (Priority: P2)

A pipeline author uses the FAIR-bioHeaders tools to attach, strip, convert, validate, checksum and
link-check FHGFF3 headers on GFF3 files. The files may be plain, gzip or BGZF compressed, may
carry an embedded `##FASTA` section, and may use CRLF line endings.

**Why this priority**: Tools are what make the header adoptable. The behaviour reuses the FHR and
GFA mechanics, so the design risk is lower than for stories 1–3.

**Independent Test**: Run the FHGFF3 conformance vectors through the toolkit.
- Every valid vector's checksum matches the independently computed value.
- Every invalid vector is rejected for the expected rule.
- Stripping removes exactly the header lines.

**Acceptance Scenarios**:

1. **Given** a GFF3 file with a `##FASTA` section, **When** its checksum is computed, **Then** the
   FASTA bytes are covered, and changing one residue changes the checksum.
2. **Given** the same content as plain text, gzip and BGZF, **When** the checksum is computed,
   **Then** all three give the same value (decompressed bytes, R1).
3. **Given** an FHGFF3 record, **When** it is converted among JSON, YAML and the embedded GFF3
   header, **Then** the record is identical after each round trip.
4. **Given** an FHGFF3 file, **When** it is validated, **Then** it is checked against the FHGFF3
   schema, selected by the record's `schema` URL, and the report names the header type.
5. **Given** a header in which a parent's checksum is recorded, **When** the GFF3's own checksum is
   computed, **Then** the parent checksum is covered, like every other byte except the root
   checksum line.

---

### User Story 5 - The GFF3 validator checks the header (Priority: P2)

A curator runs the gff3-validator on an annotation. Besides feature checks, it reports header
placement, checksum, YAML safety, schema validity, the presence of the genome link and, with
`--genome`, whether the link matches. Four example files show distinct outcomes: no header, a
valid header, an invalid header, and a stale parent link.

**Why this priority**: It closes the validator's planned rules HDR-004 to HDR-009 and gives
curators one report. It depends on stories 1–4.

**Independent Test**: Validate the four example files. Each gives its expected, distinct outcome.
In particular, the stale-parent file is valid on its own but reports "not matched" against the
supplied genome.

**Acceptance Scenarios**:

1. **Given** no header, **When** validated, **Then** the result is valid GFF3 with no header error.
   With `--require-header` it is an error (HDR-001).
2. **Given** a valid header, **When** validated, **Then** HDR-004 to HDR-008 pass, and HDR-009 is
   reported only when `--genome` is given.
3. **Given** a header line after the first feature, **When** validated, **Then** HDR-004 fails.
4. **Given** a header whose genome checksum names an older genome, **When** validated with the
   current genome, **Then** HDR-009 reports "not matched". The file's own checksum still verifies.

---

### User Story 6 - Assessment and website recognise FHGFF3 (Priority: P3)

A provider runs the FAIR header assessment on an FHGFF3-headed annotation. It identifies the header
type and its schema result. The project website lists FHGFF3 as Draft until a verified release
exists.

**Why this priority**: It aids discovery but depends on the earlier stories.

**Independent Test**: Assess an FHGFF3 example and see the header type and schema result. The
website shows Draft before a release record exists.

**Acceptance Scenarios**:

1. **Given** an FHGFF3-headed GFF3, **When** assessed, **Then** the report identifies FHGFF3 and its
   schema result instead of "GFF3 headers are not specified yet".
2. **Given** no FHGFF3 release, **When** the website is updated, **Then** FHGFF3 is shown as Draft.

### Edge Cases

- **Native directives among header lines**: `##sequence-region`, `##species`, `##genome-build`,
  `#!` lines and ordinary comments may appear before, between or after `#~` lines inside the
  leading block (#54). NCBI puts `##sequence-region` after its `#!` lines, and Ensembl before them
  (research G-02, G-03).
- **Reordering tools**: `gt gff3 -sort -tidy` moves `##sequence-region` above the `#~` block. The
  result still has a well-placed header, but its checksum no longer matches. The tools report a
  stale checksum and never repair it.
- **Sorting and indexing**: `sort | bgzip` pipelines that do not keep `#` lines first move header
  lines below features, which makes the file invalid (R10). The documented pattern keeps
  `grep '^#'` lines first. A tabix index is a derived file and is not covered.
- **`###` before any feature** is a `#` line inside the leading block and does not end it. `###`
  after features is ordinary GFF3.
- **Implied `##FASTA`**: a line beginning with `>` (Artemis compatibility) ends the header block,
  like any non-`#` line.
- **Header lines after `##FASTA`** or inside the FASTA section are invalid (R10), even before the
  first `>` line.
- **Concatenated GFF3 files**: a second `##gff-version` and `#~` block later in the file are
  invalid (R10). Feature tools read them as comments, so the data is not corrupted (research G-07).
- **`##gff-version 3.1.26`** and other `3.x.y` forms are accepted on line 1. A header before line 1
  is invalid, because GFF3 requires the version directive first.
- **Header-only file** (no features): valid if the header is valid. It describes an empty
  annotation.
- **Embedded FASTA versus genome link**: a `##FASTA` section is part of the GFF3's own bytes and
  checksum. It does not replace the genome link, and the tools do not compare it with the genome.
- **Lifted-over annotation**: it annotates the target genome (`annotates`). The source annotation
  can be recorded as a further parent or source, but the genome link always names the genome the
  coordinates refer to.
- **Several genome links**: v0.1 allows exactly one annotated genome per file. An annotation on two
  assemblies is two files.
- **Disagreement with native directives**: the header's taxon or genome accession may disagree
  with `##species` or `#!genome-build-accession`. Tools warn and change nothing (FR-011). NCBI's
  `##species` is a taxonomy browser URL, so the comparison is by numeric taxonomy ID.
- **Header present, toolkit without FHGFF3 support**: the validator reports HDR-002 ("present but
  not validated"), as it does today.
- **CRLF files**: line endings are hashed as they are. A CRLF and an LF copy have different
  checksums, as in FHR.

## Requirements *(mandatory)*

### Functional Requirements

**Format and identity**

- **FR-001 (placement)**: An FHGFF3 file MUST begin with the GFF3 version directive
  (`##gff-version 3` or `3.x.y`) on line 1. The leading header block starts at line 2 and ends at
  the first line that is neither blank nor begins with `#`, or at the `##FASTA` directive,
  whichever comes first. Inside the block, `#~` lines MAY be mixed with other `##` directives
  (including `##sequence-region` and `###`), `#!` lines, ordinary `#` comments and blank lines. A
  `#~` line anywhere after the block is invalid (R10). This makes the toolkit's GFA rule, plus
  `##FASTA` as an explicit end, the GFF3 rule. It agrees with gff3-validator HDR-004 and with the
  tool survey.
- **FR-002 (checksum)**: The checksum MUST be FHR's: SHA-512/256 over the exact decompressed file
  bytes, including any `##FASTA` section and any parent checksums recorded in the header, excluding
  only the single root `#~checksum:` line and its terminator, as padded base64 (R1–R4).
- **FR-003 (parsing)**: Header lines MUST follow FHR rules R5–R8 (single-line checksum scalar,
  UTF-8 without YAML line-break characters, no byte order mark, no duplicate keys, anchors, aliases
  or merge keys), with `#~` as the prefix.
- **FR-004 (byte preservation)**: Attaching, stripping, validating and checksumming MUST preserve
  every byte outside the `#~` lines. Tools MUST NOT reorder, rename, normalise or repair
  directives, features, IDs or embedded sequences.

**Schema**

- **FR-005**: The FHGFF3 schema MUST import the shared core (spec 004) without copying core slots.
  It adds the subject slot `annotation`, a human-readable name of the annotation, and only
  annotation-specific slots. Genome-only FHR fields (`genome`, `assemblySoftware`, FHR
  `vitalStats`, `masking` and the like) MUST NOT be part of FHGFF3. FHR schemaVersion 1 MUST NOT
  gain `derivedFrom`.
- **FR-006 (genome link, required)**: Every FHGFF3 record MUST identify the one genome its
  coordinates refer to, either by the genome's FHR checksum or by its accession plus SeqCol digest
  (#54). The two forms are:
  - a core `derivedFrom` item with header type `FHR` and relationship `annotates` (FR-007);
  - a separate `genomeReference` object with the genome's accession and SeqCol digest, both
    required, and an optional assembly name. It is never a checksum link and never reported as
    verified.

  The schema MUST enforce that at least one form is present. A record with neither, or a
  `genomeReference` with only half of the pair, is invalid. At most one `derivedFrom` item may
  have the relationship `annotates`. The core `derivedFrom` is unchanged. Both forms MAY be
  present for the same genome; whether that is allowed, and which is authoritative, is recorded in
  the plan (research D-03).
- **FR-007**: A checksum genome link MUST use the core `derivedFrom` item with header type `FHR` and
  the relationship `annotates` from the shared vocabulary (#54). FHGFF3 MAY record further
  FAIR-bioHeaders parents through `derivedFrom`, for example the source annotation of a liftover or
  a transcriptome used as evidence. A new relationship term needed for these is a plan-level
  addition to the provisional vocabulary.
- **FR-008**: These values MUST be optional, never inferred from the features, and omitted when
  unknown:
  - **sources that are not FAIR-bioHeaders files** (annotation releases such as
    `GCF_000001405.40-RS_2025_08`, evidence sets, a liftover source given by accession): an
    optional `source` list with the same shape and meaning as FHP's (spec 006 FR-007), never
    presented as verified;
  - **annotation software**: the same structured software object as FHR's `assemblySoftware`
    (name, version, URI, command-line options), one or more;
  - **annotation protocol**: a URI;
  - **Sequence Ontology release**: the SO `data-version` used for feature types (for example
    `2026-08-07`);
  - **feature counts**: counts per feature type, keyed by the SO term name used in the file (for
    example `gene`, `mRNA`, `CDS`);
  - **completeness**: BUSCO counts with lineage dataset and version, BUSCO version and mode, in the
    same shape as FHP's.
- **FR-009**: Optional nested objects MUST reject unknown keys and MUST NOT accept `null`,
  consistent with FHR v0.4.
- **FR-010**: The record MUST identify its header type and schema version through the core `schema`
  URL, so that tools select the FHGFF3 schema without inspecting features.
- **FR-011**: The header MUST NOT duplicate native GFF3 directives as required fields. Where header
  values and native directives describe the same thing, tools MUST cross-check them and report a
  disagreement as a warning that names both values. They MUST NOT rewrite either, and a
  disagreement MUST NOT make the file invalid. The pairs are:
  - the taxon's NCBI Taxonomy ID against `##species`;
  - the genome accession (from `genomeReference`, or the `annotates` item's accession) against
    `#!genome-build-accession`;
  - the assembly name (from `genomeReference`) against `##genome-build` and `#!genome-build`.

  A directive or value that is absent on either side is not compared. A comparison that cannot be
  made is reported as not checked, never as a match.
- **FR-012**: FHGFF3 v0.1 covers annotations of a single taxon and a single genome, using the core's
  required `taxon` unchanged.
- **FR-013**: Beyond the core's required slots, `annotation` and the genome link, no value is
  required. How the annotation was made is described only by the optional annotation software,
  protocol and `source` values. Public annotations mix prediction, evidence and curation, so a
  required method label would mostly say "mixed" (research G-02, G-03).

**Assertion versus verification**

- **FR-014**: Every provenance field MUST be documented as an assertion by the producer. Tools that
  check links, counts or completeness MUST report what they checked and the result, apart from the
  asserted values, and MUST NOT write results back into the header.
- **FR-015**: A link check MUST report, for each recorded parent:
  - matched, not matched, or not checked (file absent);
  - for an accession-plus-SeqCol genome link, matched only when a supplied genome's own FHR header
    records the same SeqCol digest, and otherwise "not checked" or "asserted".

  It MUST state that a match establishes identity, not correct annotation.

**Header results versus feature results**

- **FR-016**: The absence of a header MUST NOT make an otherwise valid GFF3 invalid, unless the user
  asks for a header (`--require-header`, HDR-001). A valid header MUST NOT make features valid.
  Validators MUST report header results and feature results separately.

**Serialisation, conformance and tools**

- **FR-017**: FHGFF3 records MUST round-trip losslessly among JSON, YAML and the embedded GFF3
  header. HTML microdata and JSON-LD follow in a later increment, as for FHP. The LinkML slots
  carry the term annotations those forms need from the start.
- **FR-018**: FHGFF3 MUST ship minimal and rich examples, including:
  - a checksum genome link and an accession-plus-SeqCol genome link;
  - an embedded `##FASTA` example;
  - the four validator outcome examples: no header, valid header, invalid header, stale parent.

  Values that do not identify real data MUST be marked as placeholders.
- **FR-019**: FHGFF3 MUST ship byte-exact conformance vectors covering R1–R10 in GFF3, with
  expected checksums computed independently of the toolkit (#50). They MUST include:
  - native directives before, among and after `#~` lines;
  - `###` before features;
  - `##FASTA` with residues covered by the checksum;
  - `#~` lines after a feature, after `##FASTA` and in a second concatenated file;
  - a header before `##gff-version`;
  - gzip and BGZF variants and CRLF;
  - invalid genome links (none, half a pair, wrong relationship).
- **FR-020**: The FAIR-bioHeaders toolkit MUST validate FHGFF3 records against the FHGFF3 schema.
  It MUST perform attach, strip, convert, checksum and link checks on `.gff3`/`.gff` files (plain,
  gzip, BGZF) with the same behaviour as for FHR and GFA (spec 008, Tools#33, Tools#34). It MUST
  replace today's "GFF3 headers are not specified yet" result.
- **FR-021**: The gff3-validator MUST implement HDR-004 to HDR-009 using the toolkit's header
  support rather than a second parser. It keeps the existing header modes (`--require-header`,
  `--no-header`, `--genome`).
- **FR-022**: The FAIR header assessment MUST recognise FHGFF3 headers and report their schema
  result.
- **FR-023**: FHGFF3 schemas, examples and documentation MUST be licensed MPL-2.0. No file from the
  FHGFF3 fork is copied while its upstream licence is unresolved (#75).
- **FR-024**: The project website MUST list FHGFF3 as Draft until a verified release record (tag
  and archived DOI) exists.

### Key Entities

- **FHGFF3 record**: the metadata about one GFF3 file. It has the core slots (schema, schema
  version, taxon, version, metadata authors, date created, checksum, plus the optional core
  slots), the subject `annotation`, the genome link, and the optional annotation-specific values.
- **Genome link**: the one genome the coordinates refer to. It is either an FHR file checksum
  (verifiable against a file) or an accession plus SeqCol digest (an identity asserted by the
  producer).
- **Parent link** (core `derivedFrom`): any FAIR-bioHeaders file the annotation was produced from,
  identified by its family checksum, with header type and relationship.
- **External source**: an annotation release, evidence set or other input that is not a
  FAIR-bioHeaders file, given by name, release, identifier and URL. It is asserted, never verified.
- **Annotation software**: tool name, version, URI and options, in the shape of FHR's software
  object.
- **Check report** (tool output, not part of the header): what was checked and the result, for the
  header and for the features separately.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A minimal valid record needs only the core's required fields, `annotation` and the
  genome link. Both genome-link forms are shown in the examples.
- **SC-002**: 100% of FHGFF3 conformance vectors pass in the toolkit and in the gff3-validator:
  valid vectors give the expected checksums, and invalid vectors are rejected for the expected rule.
- **SC-003**: For every valid vector, strip removes exactly the `#~` lines and keeps every other
  byte. Combining the stripped body with the metadata gives a valid file whose body, stripped
  again, is byte-identical.
- **SC-004**: Every plain GFF3 conformance case of the gff3-validator keeps its result when
  validated without `--require-header`. Adding FHGFF3 changes no feature result.
- **SC-005**: The four validator outcome examples give four distinct, documented results.
- **SC-006**: A genome → annotation → proteome chain (FHR → FHGFF3 → FHP) built from public data
  verifies end to end offline. Replacing any parent with another version is detected for that link
  only.
- **SC-007**: Every existing FHR and FHP example and conformance vector keeps its validity and
  checksum.
- **SC-008**: The surveyed GFF3 tools (docs/TOOL_COMPATIBILITY.md, 11 tools) still give outputs
  identical to the plain file for an FHGFF3 example that follows FR-001.
- **SC-009**: A curator from an annotation producer (an Alliance or AgBioData member) can write a
  valid FHGFF3 header for one of their real annotations from the documentation alone, without
  inventing values, in one sitting.
- **SC-010**: FHGFF3 v0.1 is tagged with a CHANGELOG and an archived DOI. The website moves it from
  Draft to Published only after that record exists.

## Assumptions

- The subject slot is `annotation` (spec 004 FR-002). "FHGFF3" is the working name (#54).
- FHGFF3 is a fresh LinkML module in the FHR-Specification monorepo that imports
  `schemas/core.yaml`, built the same way as FHP. The FHGFF3 fork (biodatamodels/gff-schema) models
  GFF3 features, not a provenance header. Its upstream licence is unresolved (#75), so it may be
  read for ideas only, and no file is copied.
- As for FHP (2026-10-11), FHGFF3 is released from the `release-v0.4` line. Its persistent schema
  URL follows the pattern `https://w3id.org/fair-bioheaders/fhgff3/vX.Y.Z`. The w3id rule and the
  release are separate maintainer actions.
- The relationship `annotates` stays as in the provisional core vocabulary (#54). Any PROV-O or RO
  mapping is decided there, not here.
- SeqCol digests are supplied by the producer. The tools do not compute them in v0.1
  (docs/FORMAT.md). Computing them could be a later, explicitly optional capability.
- The shared toolkit's GFA mechanics (`#~` prefix, streaming checksum, leading-block scan) apply to
  GFF3, plus the `##FASTA` end of FR-001.
- The `source` list and the software object are shared with FHP. Whether they move into the core
  is a plan-level choice (FHP follow-up).
- Field choices are discussed with curators (Alliance, AgBioData; spec 003). This specification is
  the starting point.

## Non-goals

- Feature validation: syntax, structure, ontology and biology stay in spec 009.
- GTF, GVF and other GFF dialects.
- Rewriting, normalising or generating native GFF3 directives, or moving header values into them.
- Per-feature provenance (that stays in feature attributes such as `source` and `Dbxref`).
- Computing SeqCol digests or completeness, or checking annotation correctness.
- Annotations spanning several genomes or taxa in v0.1 (FR-012).
- Changing FHR, the core's existing slots, or the checksum and parsing rules R1–R10.
