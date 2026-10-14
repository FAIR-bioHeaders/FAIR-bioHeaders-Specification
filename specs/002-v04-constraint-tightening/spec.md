# Feature Specification: Tighten loose legacy schema constraints in v0.4

**Feature Branch**: `002-v04-constraint-tightening`

**Created**: 2026-10-08

**Status**: Draft

**Input**: Review finding for FAIR-bioHeaders-Specification#29 (decision 4): "Review retained
legacy constraints and unknown-property behavior rather than silently tightening
them."

## Background

At v0.3.0, `fhr.json` and LinkML agree, but several retained patterns are
unanchored or unescaped, and the statistics are inconsistent:

| Field (fhr.json line) | Current constraint | Accepted by mistake |
| --- | --- | --- |
| `masking` (139) | `(not-masked\|…\|unknown)`, unanchored | `xx-unknown-yy` |
| `scholarlyArticle` (106) | `^10.` | `10xfoo` |
| `identifier` (118) | `[a-z0-9]*:.*`, unanchored | any string containing `:` |
| `taxon.uri` (37) | unanchored, unescaped `.` | junk before the URL |
| `orcidUri` (254) | no `$` anchor | trailing junk |
| `checksum` (261) | `^[A-Za-z0-9/+=]{44}$` | 44 `=` characters |
| `schemaVersion` (12) | `number` | `99` |
| `vitalStats` N50, L50, L90, counts | no `minimum` (only N90 has one) | negative N50 |
| `vitalStats.gcContent` (179) | 0 to 100 | `0.42` meant as a fraction |
| nested objects | unknown properties allowed | `vitalStats.n50` typo |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reject clearly malformed metadata (Priority: P1)

A repository ingesting FHR metadata gets a validation error for a malformed DOI,
masking value, or negative statistic instead of storing it.

**Independent Test**: Each "accepted by mistake" example above fails validation
under the v0.4 schema, and every v0.3 example still passes.

**Acceptance Scenarios**:

1. **Given** each mistaken value in the table, **When** validated against v0.4,
   **Then** validation fails naming that field.
2. **Given** every example in `examples/` and the converter fixtures, **When**
   validated against v0.4, **Then** they pass unchanged.

---

### User Story 2 - Migrate existing metadata knowingly (Priority: P2)

A data producer with v0.3 metadata learns from the changelog and a migration
note exactly which values will now fail, and how to fix them.

**Independent Test**: The schema-baseline diff for v0.4 lists every tightened
constraint, each with a changelog line.

### Edge Cases

- Real ORCIDs with an `X` check digit; ORCIDs written with `http://`.
- `scholarlyArticle` values that are DOIs for preprints or Zenodo records.
- `identifier` CURIEs with uppercase prefixes.
- `gcContent` values legitimately below 1%.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each tightened pattern MUST be anchored and escaped, with the change
  recorded in the schema-baseline diff and CHANGELOG.
- **FR-002**: All `vitalStats` integer statistics MUST have `minimum: 0`.
- **FR-003**: The checksum pattern MUST require valid padded base64 for a 32-byte
  digest (43 base64 characters, then `=`).
- **FR-004**: `schemaVersion` MUST be constrained [NEEDS CLARIFICATION: `const: 1`
  for v0.4, or an `enum` of supported versions, or bump to 2 if any tightening
  counts as breaking?].
- **FR-005**: Nested unknown properties [NEEDS CLARIFICATION: close nested objects
  (`additionalProperties: false`), or keep them open and only warn?].
- **FR-006**: N50/N90 MUST state whether they refer to contigs or scaffolds
  [NEEDS CLARIFICATION: add scaffold variants, or define both as contig?].
- **FR-007**: LinkML, both converter schema copies, docs, and the diagram MUST be
  updated together; `check_linkml.py` and `check_release.py` MUST pass.
- **FR-008**: `gcContent` fractions MUST NOT be silently accepted [NEEDS
  CLARIFICATION: keep 0–100 and document it, or warn when the value is at most 1?].

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every mistaken value in the Background table is rejected.
- **SC-002**: Every existing example and fixture validates unchanged.
- **SC-003**: The release notes list each tightened constraint with a migration
  hint.

## Assumptions

- This is v0.4 work under David and Adam's schema authority; nothing here changes
  v0.3.
- The `release-v0.4` development-branch convention applies.
