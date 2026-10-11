# Feature Specification: Protein FASTA header (FHP)

**Feature Branch**: `006-protein-header-spec`

**Created**: 2026-10-08 (draft), rewritten 2026-10-10

**Status**: Draft

**Input**: User description: "Define the protein header (FHP) for proteome FASTA files. Cover source
type, genetic code, isoform policy, prediction software, source database and release (for example
UniProt `UP...`), protein count, BUSCO, and `derivedFrom` links to the genome and GFF3. Include
amino-acid conformance vectors with `*` stop symbols." The inputs are issue #47, the FHP part of
#50, umbrella spec 003, core spec 004, the maintainer decisions in #54, and David Molik's
implementation context on #47 and #55.

**Research**: [research-notes.md](research-notes.md) (UniProt, Ensembl, RefSeq, gene predictors,
NCBI genetic codes, BUSCO, vocabularies).

## Purpose and ethos

Protein FASTA files (predicted proteomes, database extracts, curated sets) lose their provenance
when copied, just as genomes do. FHP brings the FHR approach to them: a small YAML header at the
top of the file (`;~` lines), one checksum over the file's exact bytes, a small required set, and
optional fields for the rest.

FHP records **asserted provenance**. It is not a quality-control report. Nothing optional is
compulsory, and nothing is guessed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ship a predicted proteome traceable to its genome and annotation (Priority: P1)

An annotation group runs a gene predictor on a genome that carries an FHR header and produces a GFF3
annotation and `proteins.fa`. They attach an FHP header to `proteins.fa`. It names the genome and
the annotation as parents by their FAIR-bioHeaders checksums, and records the genetic code, the
isoform policy and the prediction software they actually used. A user who later receives only
`proteins.fa`, the genome and the GFF3 can confirm, offline, that the proteins were produced from
exactly those files.

**Why this priority**: This is the family's core value (spec 003, "provenance links between files")
and the case in the grant's genome → annotation → proteome chain. The other stories reuse its
header mechanics.

**Independent Test**:
1. Attach an FHP header to a small amino-acid FASTA with two parent links.
2. Check the file's checksum.
3. Check the parent links with the parents present. This passes.
4. Replace the GFF3 with a different version. The link check reports a mismatch for that parent
   only.

**Acceptance Scenarios**:

1. **Given** a protein FASTA and an FHP record with the required fields, **When** the header is
   attached, **Then** the file starts with `;~` header lines and a checksum computed exactly as for
   FHR (R1–R4), and every sequence byte after the header is unchanged.
2. **Given** an FHP record whose parents are an FHR genome (`translatedFrom`, via the annotation)
   and an FHGFF3 annotation, **When** the parent files are present, **Then** a link check reports
   each recorded parent as matched or not matched by checksum.
3. **Given** the same check, **When** it passes, **Then** the report says that file identity was
   confirmed. It does not say that the translations are correct.
4. **Given** a record without a genetic code, isoform policy or software, **When** it is validated,
   **Then** it is valid. Those fields are optional and are not inferred from the sequences.

---

### User Story 2 - Publish a set taken from a protein database, with no genome chain (Priority: P1)

A resource publishes a protein set taken from a database release. Examples are a UniProt reference
proteome (`UP000005640`, release `2026_03`), a Swiss-Prot subset, or an Ensembl `pep.all` file.
The FHP header records the database, release, set identifier and what was taken, without claiming
a genome or annotation file the producer does not have.

**Why this priority**: Much protein data reaches users this way. David's guidance says that "a
curated protein set need not have a known genome/GFF3 chain". This story must work without the
family's link machinery.

**Independent Test**: Validate a minimal database-derived record that has a source database and
release and no parent files. It is valid, and a link check reports "no parent files recorded", not
an error.

**Acceptance Scenarios**:

1. **Given** a record with one database source (name, release, set identifier), **When** it is
   validated, **Then** it is valid with no `derivedFrom`.
2. **Given** a database source whose release is unknown to the producer, **When** the record is
   written, **Then** the release is omitted, not filled in with a guess or a placeholder.
3. **Given** a database that states which genome assembly its set corresponds to (for example
   UniProt's `GCA_000001405.29` for `UP000005640`), **When** the producer records it, **Then** it
   is recorded as an accession asserted by the source. It is never a checksum link that tools claim
   to verify.

---

### User Story 3 - Describe a set combined from several sources (Priority: P2)

A curator merges predicted proteins from their own annotation with reviewed entries from Swiss-Prot
and a few manually corrected sequences. The header lists each source separately: the parent files
by checksum, the database release by name, and the manual corrections as a described contribution.
It does not imply that any one accession explains every sequence.

**Why this priority**: Mixed sets are common in curated organism databases (Alliance, AgBioData
members). Without this story, producers would have to pick one source and misstate the others. It
builds on stories 1 and 2.

**Independent Test**: Validate a record with one parent file, one database source and one free-text
contribution. It is valid, the link check covers only the parent file, and a JSON round trip
preserves all three.

**Acceptance Scenarios**:

1. **Given** a set from several sources, **When** the record lists them, **Then** each source keeps
   its own identifier, release and optional sequence count. No field claims that a single source
   covers the whole set.
2. **Given** per-source sequence counts that do not add up to the total, **When** the record is
   validated, **Then** it is still valid. Counts are asserted; a tool may report the discrepancy as
   a check, never as a schema error.

---

### User Story 4 - Header tooling works on protein FASTA exactly as on genomes (Priority: P2)

A pipeline author uses the existing FAIR-bioHeaders tools to attach, strip, convert, validate and
checksum FHP headers on protein FASTA, plain or compressed. Amino-acid sequences may use stops,
ambiguity codes, rare residues, lower case and gaps. Tools that cannot read headers still work on the
stripped file.

**Why this priority**: Without tool support the header is not adoptable (paper goal: low
implementation effort). It is mostly a reuse of FHR behaviour, so it carries less design risk than
stories 1–3.

**Independent Test**: Run the FHP conformance vectors through the toolkit. Every valid vector's
checksum matches the independently computed value, every invalid vector is rejected with the
expected rule, and strip followed by combine restores the original bytes.

**Acceptance Scenarios**:

1. **Given** protein FASTA containing `*` (terminal and internal), `B Z J X U O`, lower-case
   residues and `-`, **When** a header is attached, validated and stripped, **Then** the sequence
   bytes are identical before and after, and the checksum covers them exactly.
2. **Given** an FHP record, **When** it is converted among JSON, YAML and the embedded FASTA header,
   **Then** the record is identical after each round trip.
3. **Given** an FHP file, **When** it is validated, **Then** it is checked against the FHP schema,
   not the FHR schema, and the report names the header type.

---

### User Story 5 - The FAIR assessment and the website recognise FHP (Priority: P3)

A data provider runs the FAIR header assessment on an FHP-headed protein file. It recognises the
header type and its schema conformance. The project website lists FHP with Draft status until a
verified release exists.

**Why this priority**: It improves discoverability but depends on stories 1–4.

**Independent Test**: Assess an FHP example and see the header type and schema result in the
report. The website entry shows "Draft" before the release record exists.

**Acceptance Scenarios**:

1. **Given** an FHP-headed file, **When** it is assessed, **Then** the report identifies FHP and its
   schema conformance instead of describing FHP as a future draft.
2. **Given** no published FHP release, **When** the website is updated, **Then** FHP is shown as
   Draft, with no DOI or release claimed.

### Edge Cases

- **Stop symbols**: a terminal `*` on some sequences and not others, internal `*` (read-through,
  pseudogene translations) and `.` used as a stop by some tools. Header handling never inspects or
  changes them.
- **Rare and ambiguous residues**: U, O, B, Z, J and X, in any case. Same as above; the alphabet
  has no effect on header parsing or the checksum.
- **Very large sets** (millions of sequences, compressed): checksum and header handling stream
  without loading the file into memory, as for FHR.
- **Header block placement**: `;~` lines after the first `>` line make the file invalid (R10), as
  in FHR. Concatenating two FHP files therefore produces an invalid file, which tools report.
- **Mixed genetic codes**: nuclear and organellar proteins in one file use different translation
  tables, so one genetic-code value cannot describe the file. The producer omits it or records it
  per source; tools do not guess.
- **Parent present but different**: a genome or annotation of another version is reported as "not
  matched". Translation correctness is not tested.
- **Parent recorded but absent**: reported as "not checked (file not supplied)", distinct from
  "not matched".
- **Parent is a transcriptome**: proteins predicted from transcripts link to an FHT parent with the
  same mechanism.
- **Subset of another FHP file**: a filtered copy links to its FHP parent as `filteredFrom`.
- **Per-sequence review status**: Swiss-Prot and TrEMBL entries in one download. FHP records the
  source, not a whole-file review status; per-sequence status stays in each sequence's own header.
- **Multi-species sets** (UniRef clusters, metaproteomes, pan-proteomes) conflict with the core's
  single required `taxon`. See FR-012.
- **BUSCO from another lineage version**: completeness values carry their lineage dataset and
  version, so values from different versions are never presented as comparable.
- **A FASTA file with an FHR header and protein sequences, or the reverse**: validation against the
  declared header type's schema reports the mismatch. No type is inferred from residues.

## Requirements *(mandatory)*

### Functional Requirements

**Format and identity**

- **FR-001**: An FHP header MUST use FHR's container rules unchanged: `;~` YAML lines forming the
  leading header block, and parsing rules R5–R10 (docs/FORMAT.md).
- **FR-002**: The FHP checksum MUST be defined exactly as FHR's: SHA-512/256 over the exact
  decompressed file bytes except the single root checksum line, as padded base64 (R1–R4). It MUST
  NOT depend on the sequence alphabet, residue case, line wrapping or stop symbols.
- **FR-003**: Header processing (attach, strip, validate, checksum) MUST preserve every sequence
  byte, and MUST NOT normalise, translate, reorder, rename or repair sequences or identifiers.

**Schema**

- **FR-004**: The FHP schema MUST import the shared core (spec 004) without copying core slots. It
  adds the subject slot `proteome`, a human-readable name of the protein set, and only
  protein-specific slots. Genome-only FHR fields (`genome`, `assemblySoftware`, `vitalStats`,
  `masking` and the like) MUST NOT be part of FHP.
- **FR-005**: Beyond the core's required slots and `proteome`, the only other required value MUST
  be the kind of source, `sourceType`
  [NEEDS CLARIFICATION: Is `sourceType` required, and what does each value mean? The draft
  proposes `predicted | curated | mixed`, but "curated" suggests manual review, which a UniProt
  reference proteome (mostly unreviewed TrEMBL) or an Ensembl `pep.all` file lacks (research N-01,
  N-02).]
- **FR-006**: An FHP record MUST be able to link parent FAIR-bioHeaders files (FHR genome, FHGFF3
  annotation, FHT transcriptome, or another FHP file) through the core `derivedFrom` structure, by
  checksum, with an optional SeqCol digest and accession, and a relationship from the shared
  vocabulary (`translatedFrom`, `filteredFrom`, …).
- **FR-007**: An FHP record MUST be able to describe sources that are not FAIR-bioHeaders files,
  such as a database release, set or annotation run. These are kept distinct from checksum-linked
  parents, so that no tool presents them as verified
  [NEEDS CLARIFICATION: How are external and multiple sources expressed? A separate optional
  `source` list (database name, release, set identifier, URL, optional sequence count, description)
  beside `derivedFrom`; or a core change that lets `derivedFrom` hold parents without a checksum?
  See research N-08.]
- **FR-008**: These values MUST be optional, never inferred from the sequences, and omitted when
  unknown:
  - **genetic code**: an NCBI translation table ID (1–6, 9–16, 21–33; research N-05);
  - **isoform policy**: all isoforms, one per gene by longest, one per gene by the source's
    canonical choice, or not stated. "Canonical" is not "longest" (N-01);
  - **prediction software**: the same structured software object as FHR's `assemblySoftware`
    (name, version, URI, command-line options);
  - **annotation or prediction protocol**: a URI;
  - **sequence statistics**: sequence count and, optionally, gene count and total residues;
  - **completeness**: BUSCO counts (complete single, complete duplicated, fragmented, missing,
    total), with the lineage dataset name and version, the BUSCO version and the mode.
- **FR-009**: Completeness values MUST name the lineage dataset and its version and MUST be stored
  as counts, so that values from different lineage versions are not presented as comparable
  (research N-06).
- **FR-010**: Optional nested objects MUST reject unknown keys and MUST NOT accept `null` for
  absent values, consistent with FHR v0.4.
- **FR-011**: The record MUST identify its header type and schema version through the core
  `schema` URL, so that a validator selects the FHP schema without inspecting residues.
- **FR-012**: FHP v0.1 covers protein sets from a single taxon, using the core's required `taxon`
  unchanged. Multi-species sets are out of scope for v0.1
  [NEEDS CLARIFICATION: Is single-taxon scope acceptable for v0.1, or must FHP admit multi-species
  sets (UniRef clusters, metaproteomes, pan-proteomes) now? That would need a list of taxa or a
  higher-rank taxon, which departs from the core's single `taxon`.]

**Assertion versus verification**

- **FR-013**: Every provenance field MUST be documented as an assertion by the producer. Tools that
  check parent links, counts or completeness MUST report what they checked and the result, kept
  apart from the asserted values. They MUST NOT write check results back into the header.
- **FR-014**: A parent-link check MUST distinguish three results for each recorded parent: matched,
  not matched, and not checked (file absent). It MUST state that a match establishes file
  identity, not correct translation.

**Serialisation, conformance and tools**

- **FR-015**: FHP records MUST round-trip losslessly among JSON, YAML, the embedded FASTA header
  and HTML microdata, using the conventions FHR already uses. A JSON-LD form follows the feature
  011 conventions once the FHP slots have LinkML annotations and vocabulary terms (dependency).
- **FR-016**: FHP MUST ship minimal and rich examples for each kind of source (predicted, database,
  mixed). Example values that do not identify real data MUST be marked as placeholders.
- **FR-017**: FHP MUST ship byte-exact conformance vectors covering R1–R10 in amino-acid FASTA,
  including terminal and internal `*`, `B Z J X U O`, lower case, `-`, compressed variants and
  invalid `derivedFrom` cases (#50). Expected checksums MUST be computed independently of the
  toolkit.
- **FR-018**: The FAIR-bioHeaders toolkit MUST validate FHP records against the FHP schema and
  perform attach, strip, convert, checksum and parent-link checks on FHP files with the same
  behaviour as for FHR (spec 008).
- **FR-019**: The FAIR header assessment MUST recognise FHP headers and report their schema
  conformance.
- **FR-020**: FHP schemas, examples and documentation MUST be licensed MPL-2.0, preserving any
  third-party notices.
- **FR-021**: The project website MUST list FHP as Draft until a verified release record (tag and
  archived DOI) exists.

### Key Entities

- **FHP record**: the metadata about one protein FASTA file. It has the core slots (schema, schema
  version, taxon, version, metadata authors, date created, checksum, plus the optional core
  slots), the subject `proteome`, the source type, and the optional protein-specific values.
- **Parent link** (core `derivedFrom`): a FAIR-bioHeaders file this set was produced from,
  identified by its family checksum, with header type, relationship and optional SeqCol digest and
  accession. It can be verified against a file on disk.
- **External source**: a database release, set or annotation run the sequences came from, such as
  UniProt `UP000005640` release `2026_03`, the `pep.all` file of an Ensembl release, or an NCBI annotation
  `GCF_…-RS_2024_08`. It has a name, release, identifier, optional URL, optional count and
  description. It is asserted, not verifiable by checksum.
- **Prediction software**: the tool that produced the gene models or translations, with name,
  version, URI and options. It has the same shape as FHR's software object.
- **Completeness report**: BUSCO counts with lineage dataset and version, tool version and mode.
- **Check report** (tool output, not part of the header): what a tool verified and the result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A minimal valid record for each kind of source (predicted, database, mixed) needs no
  more than the core's required fields plus two (`proteome` and `sourceType`). Each is shown in the
  examples.
- **SC-002**: 100% of FHP conformance vectors pass in the toolkit: valid vectors give the expected
  checksums, and invalid vectors are rejected for the expected rule. Strip followed by combine
  restores the original bytes for every valid vector.
- **SC-003**: A genome → annotation → protein chain built from public data verifies end to end
  offline. Replacing any parent with another version is detected for that parent only.
- **SC-004**: Every FHP example converts among JSON, YAML and the embedded header with no loss in
  any round trip.
- **SC-005**: Every existing FHR example and conformance vector keeps its validity and checksum.
  FHP does not change FHR behaviour.
- **SC-006**: A reviewer from a protein data producer (an Alliance or AgBioData member, or a
  UniProt-based pipeline) can write a valid FHP header for one of their real files from the
  documentation alone, without inventing values, in one sitting.
- **SC-007**: FHP v0.1 is tagged with a CHANGELOG and an archived DOI, and the website moves it from
  Draft to Published only after that record exists.

## Assumptions

- The subject slot is `proteome`, as decided in spec 004 FR-002 and #54. "FHP" is the working name.
- FHP lives in the FHR-Specification monorepo (spec 003 FR-005) with its own schema files,
  examples and per-type release tags. The concrete layout and tag form (for example
  `fhp-vX.Y.Z`, with a w3id alias like `/fair-bioheaders/fhp/vX.Y.Z`) is a plan-level choice.
  Publishing a release is a separate maintainer action (constitution, decision boundaries).
- The relationship vocabulary (`translatedFrom`, `filteredFrom`) and its PROV-O/RO mapping stay as
  in the core (#54). FHP adds no relationship terms unless the plan finds a gap.
- Parent-link verification and per-type schema selection are built in the shared toolkit (spec
  008, Tools#33), not in an FHP-specific tool.
- Bioschemas has no proteome profile, so an FHP record's JSON-LD form is a `Dataset` about proteins
  (research N-07). Single proteins (`Protein` profile) are out of scope.
- The FASTA container rules are unchanged, so tools that only strip `;~` lines work on FHP files
  without changes.
- Field choices are discussed with curators (Alliance, AgBioData; spec 003 assumptions). This
  specification is the starting point, not a final field list.

## Non-goals

- Validating translations against parents (codon-level checks), sequence QC, or computing
  completeness. FHP records results that were produced elsewhere.
- Per-sequence metadata in the header. Per-sequence information stays in each `>` line, in the
  source's own convention.
- Replacing database identifiers (UniProt, RefSeq, Ensembl) or their FASTA header conventions.
- Single-protein records, protein structures and peptide/spectral proteomics files.
- Changing FHR, the core's existing slots, or the checksum and parsing rules.
