# Feature Specification: Schema versions and schema selection

**Feature Branch**: `012-schema-versioning` (on `release-v0.4`)

**Created**: 2026-10-14

**Status**: Draft (clarified 2026-10-14)

**Input**: Maintainer decision on [#44](https://github.com/FAIR-bioHeaders/FHR-Specification/issues/44)
(David Molik, 2026-10-14) and Adam Wright's answers of the same day:
- skip the proposed v0.3.1 legacy fallback; raw-main keeps meaning the current canonical schema;
- new release-targeted files and examples cite the release's versioned URL;
- an explicitly versioned URL selects the matching released schema, and an unknown version gives a
  clear unsupported-version result instead of a silently substituted schema;
- bump `schemaVersion` for major and minor schema changes, with a documented policy, and keep it
  separate from the assembly's `version` and from release tags;
- apply the same selection in the toolkit, the GFF3 validator and the website.

Related: #35 (v0.4 tightening), #54 (header family), website
[#15](https://github.com/FAIR-bioHeaders/fair-bioheaders.github.io/issues/15) and
[#16](https://github.com/FAIR-bioHeaders/fair-bioheaders.github.io/issues/16).

## Clarifications

### Session 2026-10-14

- Q: How is `schemaVersion` written? → A: As a string `"MAJOR.MINOR"`. FHR's v0.4 schema is
  `"2.0"`: a major version, because the v0.4 tightening rejects some files that v0.3 accepted. The
  additive v0.4 changes (author `nameType`, scaffold statistics) are part of 2.0 (FR-001, FR-003).
- Q: What do FHP and FHGFF3 start at? → A: Each header type versions its own contract, so FHP and
  FHGFF3 start at `"1.0"`. Their versioned URLs still use the shared FHR-Specification release
  tag, for example `https://w3id.org/fair-bioheaders/fhp/v0.4.0` (FR-004).
- Q: What does a raw-main URL select? → A: The current canonical schema. There is no fallback to
  v0.3.1 for files that cite raw-main (David, #44) (FR-007).
- Q: What does an unknown version give? → A: An unsupported-version result, never another schema
  (FR-009).

## Purpose

A metadata file names the schema it follows in `schema`. Until now that value was almost always
the raw-main URL, and `schemaVersion` stayed `1` through every change. The v0.4 tightening is
the first change that can make an existing file invalid. Readers, writers and validators need one
rule that says which schema a file is checked against, and a version number that changes when the
contract changes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A file citing a release is checked against that release (Priority: P1)

A data provider writes an FHR header that cites `https://w3id.org/fair-bioheaders/fhr/v0.4.0`.
Years later, after FHR 3.0 has been published, a user validates the file and gets the result the
v0.4.0 schema gives, not the result of whatever schema is current.

**Why this priority**: This is what versioned URLs are for. Without it a later schema change can
silently turn a valid archived file invalid, or the reverse.

**Independent Test**: Validate the same header under two bundled releases, citing each release's
URL in turn; each passes or fails as that release's schema says.

**Acceptance Scenarios**:

1. **Given** a header citing the w3id URL of a release the tool has, **When** it is validated,
   **Then** that release's schema of the header's type is used.
2. **Given** the same header citing the release's raw tag URL
   (`…/FHR-Specification/v0.4.0/fhr.json`), **When** it is validated, **Then** the result is the
   same as with the w3id URL.
3. **Given** a header citing `https://w3id.org/fair-bioheaders/fhr/v0.3.1` with
   `schemaVersion: 1`, **When** a tool that has the v0.3.1 schema validates it, **Then** it is
   checked against v0.3.1, even though the current schema is 2.0.

---

### User Story 2 - Unknown versions are reported, never substituted (Priority: P1)

A file cites a release the tool does not have, for example a newer release than the tool knows,
or a branch or commit URL. The user is told the version is unsupported and which versions the tool
has; the file is not reported valid or invalid against some other schema.

**Why this priority**: Silent substitution is the failure David's decision rules out.

**Independent Test**: The conformance vector citing a release that cannot exist gives an
unsupported-version result in every tool.

**Acceptance Scenarios**:

1. **Given** a header citing `https://w3id.org/fair-bioheaders/fhr/v0.0.0`, **When** it is
   validated, **Then** the result names the unsupported version and lists the supported ones.
2. **Given** a header citing `…/FHR-Specification/some-branch/fhr.json`, **When** it is validated,
   **Then** the same unsupported result is given: only `main` and release tags are recognised refs.
3. **Given** a header citing a release that has no schema of that type (FHP at v0.3.1), **When** it
   is validated, **Then** the result is unsupported-version.

---

### User Story 3 - schemaVersion says which contract a file follows (Priority: P1)

A reader sees `schemaVersion: "2.0"` and knows the file follows FHR contract 2.0, whatever release
tag, package version or assembly `version` it came with. The policy says when the major and minor
numbers change.

**Why this priority**: David asked for it explicitly; a release tag alone does not version the
metadata contract.

**Independent Test**: The policy document defines major and minor; every published schema's
`schemaVersion` matches the version registry; examples and vectors use the right value.

**Acceptance Scenarios**:

1. **Given** the v0.4 FHR schema, **When** a file gives `schemaVersion: "2.0"`, **Then** that
   part is valid; `1`, `"1"`, `2`, `"2"` and `"2.1"` are not.
2. **Given** the FHP and FHGFF3 schemas, **When** a file gives `schemaVersion: "1.0"`, **Then**
   that part is valid.
3. **Given** a future minor version M.N, **When** its schema is published, **Then** it accepts
   `"M.0"` to `"M.N"`.

---

### User Story 4 - New files cite the release they target (Priority: P2)

Examples and newly written files cite the versioned URL of the release they target. Raw-main stays
the canonical "current schema" link in documentation.

**Independent Test**: Every example and every non-selection conformance vector on the release line
cites the v0.4.0 versioned URL of its type and the matching `schemaVersion`.

**Acceptance Scenarios**:

1. **Given** the v0.4 examples, **When** they are read, **Then** each cites
   `https://w3id.org/fair-bioheaders/<type>/v0.4.0` and its type's `schemaVersion`.
2. **Given** an existing file, **When** a tool combines, strips or converts it, **Then** its
   `schema` value is kept as written.

---

### User Story 5 - Every tool applies the same rule (Priority: P2)

The toolkit, the GFF3 validator's header checks and the website builder select schemas the same
way. The rule and the version registry are published in one place for them to follow.

**Independent Test**: The selection vectors give the same outcome through the toolkit and through
the validator's header checks.

**Acceptance Scenarios**:

1. **Given** the selection vectors, **When** the toolkit and gff3-validator run them, **Then** the
   outcomes agree with the manifest.
2. **Given** the website, **When** it is updated by its maintainer, **Then** it can follow the
   published rule and registry without reading toolkit code.

---

### Edge Cases

- A w3id URL with a trailing slash (`…/fhr/v0.4.0/`) is the same as without one; w3id redirects
  both.
- A versioned URL's type and the file name must agree: `…/v0.4.0/fhp.json` is FHP; a raw tag URL
  naming any other file is not a schema URL.
- `https://w3id.org/fair-bioheaders/fhr/v0.4.0/fhr.json` (the w3id PATH form) is not a schema URL
  under this rule; use `…/fhr/v0.4.0`.
- A `schema` value that is not a FAIR-bioHeaders schema URL at all keeps today's behaviour: FHR,
  checked against the current FHR schema (FHR's `schema` field has never been constrained).
- A file citing raw-main with `schemaVersion: 1` fails the current schema once it is 2.0. That is
  the intended result; the migration note says how to update or pin it.
- YAML `schemaVersion: 2.0` unquoted is the float 2.0, not the string `"2.0"`, and fails. Tools
  that write YAML quote it; the docs say so.
- Microdata: the `itemtype` stays the raw-main `fhr.json` URL, which identifies FHR items
  (rule M1); the `schema` itemprop carries the versioned URL. An untyped `schemaVersion` span is
  already a string.
- JSON-LD: `schemaVersion` stays the literal `fhr:schemaVersion`; its range becomes text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `schemaVersion` MUST be a JSON string `"MAJOR.MINOR"` of two non-negative integers
  without leading zeros, in every header type.
- **FR-002**: A documented policy MUST say what is major and minor:
  - **major**: a change that can make a previously valid instance invalid or change what a valid
    value means (new required field, removed field, tighter pattern, range or enum, closed object,
    changed type or meaning);
  - **minor**: a backward-compatible change (new optional field or term, relaxed constraint);
  - **none**: documentation, examples, descriptions and generated artefacts that change no
    validation outcome.
- **FR-003**: The FHR schema on the v0.4 line MUST be `"2.0"`.
- **FR-004**: FHP and FHGFF3 MUST each start at `"1.0"`; each header type's version changes only
  when its own schema changes.
- **FR-005**: The schema of version M.N MUST accept `schemaVersion` values `"M.0"` to `"M.N"` and
  no others.
- **FR-006**: A machine-readable version registry MUST record, for each FHR-Specification release
  tag, the `schemaVersion` of each header type it publishes, and which release the working tree's
  schemas belong to.
- **FR-007**: The selection rule MUST map a `schema` value to a header type and a schema:
  - raw-main URL of a type's file → that type's current schema;
  - w3id `…/fair-bioheaders/<type>/vX.Y.Z` or raw tag URL `…/vX.Y.Z/<type file>` → that
    release's schema of the type;
  - any other value → FHR, current schema.
- **FR-008**: The header type MUST follow from the URL (`fhr`, `fhp`, `fhgff3`), updating FHP rule
  P2 and FHGFF3 rule G3 to recognise the w3id forms.
- **FR-009**: A recognised URL whose release or ref the reader does not have, or whose release has
  no schema of that type, MUST give an unsupported-version result naming the value and the
  supported versions. It MUST NOT be checked against another schema.
- **FR-010**: Examples and conformance vectors on the release line MUST cite the release's
  versioned URL and their type's `schemaVersion`, except vectors that test selection itself.
- **FR-011**: Tools MUST keep a file's `schema` value as written when they combine, strip or
  convert it.
- **FR-012**: Conformance vectors MUST cover: w3id versioned, raw tag, raw-main, an older bundled
  release (v0.3.1), an unknown release, a non-release ref, and a release without that type.
- **FR-013**: The JSON-LD context, vocabulary, mapping notes and microdata rules MUST reflect the
  string `schemaVersion`.
- **FR-014**: A migration note MUST say how files that cite raw-main with `schemaVersion: 1` are
  updated or pinned to v0.3.1. Tools MUST NOT rewrite them silently.
- **FR-015**: The toolkit and gff3-validator MUST implement FR-007 to FR-009 with bundled copies
  whose provenance (release tag, file, SHA-256) is recorded.
- **FR-016**: The rule and registry MUST be documented for the website to follow; this feature does
  not change the website.

### Key Entities

- **Schema version**: the `"MAJOR.MINOR"` contract version of one header type.
- **Release**: an FHR-Specification tag `vX.Y.Z` that publishes one schema version per header
  type it contains.
- **Schema URL**: a `schema` value in one of the recognised forms.
- **Version registry**: `schemas/versions.json`, the release → type → schemaVersion table.
- **Selection result**: a header type plus either a schema (current or released) or
  unsupported-version.

## Success Criteria *(mandatory)*

- **SC-001**: Every published schema's accepted `schemaVersion` values equal the registry's entry
  for the working tree's release (test).
- **SC-002**: All selection vectors pass through the toolkit with the v0.4 copies, and the
  validator's header checks agree on the FHGFF3 cases.
- **SC-003**: No example or ordinary vector on the release line cites raw-main or a numeric
  `schemaVersion`.
- **SC-004**: The policy and rule fit on one documentation page that the website maintainer can
  implement from.
- **SC-005**: The assembly `version` field is untouched by every change here.

## Assumptions

- Released schemas are those at the tags (`v0.3.0`, `v0.3.1`; `v0.4.0` once tagged). The
  specification repository stores no copies; tags are the source, and tools bundle copies.
- v0.3.0 and v0.3.1 publish the same `fhr.json` (SHA-256 `e3d3843e…`), with numeric
  `schemaVersion: 1`. Those releases are not rewritten.
- Until `v0.4.0` is tagged, the release-line working tree stands for it (registry `current`).
- The w3id `/fhr/`, `/fhp/` and `/fhgff3/` rules are live (perma-id/w3id.org#6856, #6868, #6890).
- Online fetching of schemas is out of scope: tools use bundled copies (offline, constitution V).

## Non-goals

- No fallback from raw-main to v0.3.1 (David, #44).
- No constraint on the FHR `schema` field's value beyond what it has.
- No automatic rewriting of existing files.
- No website change (David's repository); a pointer is left on website #15/#16.
- No release, tag, DOI or w3id change.
