# Feature Specification: Conformance test vectors for header parsing and checksum coverage

**Feature Branch**: `001-checksum-conformance-vectors`

**Created**: 2026-10-08

**Status**: Draft

**Input**: Review finding for FAIR-bioHeaders-Specification#29 (decision 3): the checksum
rules in docs/FORMAT.md left cases undefined. Independent implementations need
shared vectors so they agree on which bytes are hashed and which lines are
metadata.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check an implementation against the specification (Priority: P1)

A developer writing an FHR reader in another language (R, Rust, Nextflow/Groovy)
runs it over a published set of files with expected outcomes.

**Why this priority**: Without shared vectors, every implementation reinterprets
docs/FORMAT.md, and parsers can disagree about where the checksum line ends.

**Independent Test**: Run the reference converter over every vector and compare
with the manifest.

**Acceptance Scenarios**:

1. **Given** a valid vector, **When** an implementation validates it, **Then** it
   reports the manifest's checksum and parsed metadata.
2. **Given** an invalid vector, **When** validated, **Then** it is rejected, and the
   manifest names the rule it breaks.

---

### User Story 2 - Guard against regressions in CI (Priority: P2)

`scripts/check_release.py` (or a new script) runs the vectors against the
converter so a parsing change cannot silently alter checksum coverage.

**Independent Test**: Break one rule in a converter checkout and see CI fail.

### Edge Cases

Each needs at least one vector:

- LF, CRLF, lone CR, mixed endings, no final newline.
- Ordinary `;`/`#` comments; FASTA and GFA prefixes.
- Checksum key indented to the root indentation; spaces before the colon.
- Quoted checksum key; nested `checksum` property; two checksum lines.
- Block or folded scalar and continuation-line checksum values.
- Characters that YAML and byte-line splitting may treat differently inside a
  header line.
- Leading UTF-8 BOM in FASTA/GFA.
- Duplicate keys, YAML anchors, aliases, merge keys.
- Non-UTF-8 bytes in sequence description lines (valid: not decoded).
- FHR lines after sequence data, and two concatenated FHR files (invalid: FHR
  lines must form the leading header block).
- Ordinary comments and blank lines before or between FHR lines (valid).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Vectors MUST live under `conformance/` with a machine-readable
  manifest giving file, format, expected outcome (valid or rule violated), and,
  for valid files, the expected checksum.
- **FR-002**: Every rule in the docs/FORMAT.md checksum section MUST be covered by
  at least one valid and one invalid vector.
- **FR-003**: Expected checksums MUST be computed independently of the converter
  (plain `hashlib.sha512_256` over the specified bytes) by the generator script.
- **FR-004**: Vectors MUST be byte-exact in git (mark them binary in
  `.gitattributes` so line endings are never normalized).
- **FR-005**: CI MUST run the converter against every vector.
- **FR-006**: Placeholder checksum or SeqCol values MUST NOT appear in valid
  vectors.

### Key Entities

- **Vector**: one FASTA or GFA file with exact bytes.
- **Manifest**: expected outcome per vector, and the docs/FORMAT.md rule it tests.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of docs/FORMAT.md checksum rules map to vectors.
- **SC-002**: The reference converter passes all vectors.
- **SC-003**: A second, independent checker script agrees with the manifest.

## Assumptions

- The vectors document the checksum and header parsing rules in docs/FORMAT.md.
- The vectors are additive and do not change schemaVersion.
