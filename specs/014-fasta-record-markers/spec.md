# Feature Specification: Escape FASTA record markers in FHR header lines

**Feature Branch**: `014-fasta-record-markers`

**Created**: 2026-10-18

**Status**: Implemented

**Input**: [FAIR-bioHeaders-Specification#127](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/127).
kseq-based FASTA readers start a record at the first `>` or `@` character **anywhere** in a line
(John Marshall, onecodex/needletail#122). So an FHR header line holding a raw `>` or `@`, such as an
email address or `contigs > 1000 bp`, makes BWA, minimap2, seqtk, bioawk, `samtools dict` and pysam
`FastxFile` silently read a bogus record. The proposal: escape the characters in FASTA header lines,
warn on raw ones, and decode when converting to other formats.

## Clarifications

### Session 2026-10-18

Both maintainers approved the strategy on #127. No question needed a new decision.

- Q: Escape, reject, or document only? → A: Escape and warn. David Molik, 2026-10-18 23:40:
  "escape and warn seems like the way to go here. acknowledging the need to decode when converting
  other formats. stratagey approved."
- Q: What do other formats hold? → A: The real characters. Adam Wright: "when we convert between
  the file header in the fasta and the other formats we should decode these things we are encoding
  in the header." YAML escapes decode automatically, so only the FASTA header text carries them.
- Q: Is a raw `>` or `@` invalid? → A: No. R11 is a SHOULD for writers; validators warn, and
  existing files stay valid (research R-02).
- Q: Which containers? → A: FASTA only (FHR and FHP). GFA and GFF3 readers treat `#` lines as
  whole-line comments (research R-05).

## User Scenarios & Testing

### User Story 1 - Write FASTA headers that kseq tools read correctly (Priority: P1)

A data provider combines metadata whose free text contains an email address and a `>` with a
FASTA file, then indexes it with minimap2.

**Independent Test**: combine, then run seqtk or `samtools dict`: only the real records appear.

1. **Given** metadata with `@` or `>` in any string, **When** the toolkit writes a FASTA header,
   **Then** no header line contains a raw `>` or `@`, and reading the header returns the original
   strings.
2. **Given** metadata without `>` or `@`, **When** the toolkit writes a FASTA header, **Then** the
   bytes are identical to before this feature.

### User Story 2 - Get the real characters in every other format (Priority: P1)

**Independent Test**: convert an escaped FASTA header to JSON, YAML, JSON-LD and back.

1. **Given** an escaped FASTA header, **When** it is converted to JSON, YAML, JSON-LD or
   microdata, **Then** the values hold the real `>` and `@`.
2. **Given** that JSON, **When** it is combined into FASTA again, **Then** the header and checksum
   are identical.

### User Story 3 - Be told about raw markers in existing files (Priority: P2)

**Independent Test**: validate a file with a raw `@` and a correct checksum.

1. **Given** a FASTA file whose FHR header line holds a raw `>` or `@`, **When** it is validated,
   **Then** the result is unchanged (valid) and a warning names the line, the reason and the escape.

### Edge cases

- Multi-line strings, long strings that YAML folds, strings that start with `@` or `>` (YAML
  indicators), backslashes and quotes, and strings that also hold YAML-only line breaks (R6).
- Keys holding the characters (not allowed by the schemas, but the writer must still not emit them
  raw).
- YAML comment lines inside the header (`;~# …`) and folded block scalars (`>-`) are header lines
  too: the warning covers them.
- Ordinary `;` comment lines before the first record can trip kseq as well; the rule asks writers to
  avoid the characters there, but only FHR lines are checked (research R-04).

## Requirements

- **FR-001**: docs/FORMAT.md gains rule R11 (FASTA header writers SHOULD NOT write a raw `>` or `@`;
  they escape them as `\x3E` and `\x40` in double-quoted YAML scalars).
- **FR-002**: R11 does not change validity, the schemas or `schemaVersion`.
- **FR-003**: The toolkit's FASTA header writer escapes the characters in every string (keys and
  values) and is byte-identical for metadata without them.
- **FR-004**: Reading a FASTA header returns the real characters; every other output format holds
  them.
- **FR-005**: `fhr-fasta-validate`, `bioheaders verify` and `bioheaders validate` (FASTA input) warn
  on a raw `>` or `@` in an FHR header line, without changing the exit status.
- **FR-006**: Conformance vectors cover escaped values (FHR and FHP) and a raw value that stays
  valid; R11 is a writer rule with no invalid vector, like J7.
- **FR-007**: docs/TOOL_COMPATIBILITY.md points to R11.

## Success Criteria

- **SC-001**: On the new vectors, seqtk, bioawk and `samtools dict` read only the real record for
  the escaped file (`Contig1`) and the bogus record for the raw one (research R-01).
- **SC-002**: All existing examples and conformance vectors are byte-identical.
- **SC-003**: FASTA → JSON → FASTA round trips are byte-identical for metadata with both characters.
- **SC-004**: All spec and toolkit gates pass.

## Assumptions

- Every YAML 1.1/1.2 reader decodes `\x3E` and `\x40` in double-quoted scalars (YAML spec,
  double-quoted escapes); PyYAML does (tested).
- The checksum covers the escaped bytes, like any other header bytes.
