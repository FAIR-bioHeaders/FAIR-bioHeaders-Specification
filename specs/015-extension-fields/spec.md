# Feature Specification: User-defined extension fields with an `x-` prefix

**Feature Branch**: `015-extension-fields`

**Created**: 2026-11-03

**Status**: Implemented (released in v0.5.0)

**Input**: [FAIR-bioHeaders-Specification#197](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/197).
Every header type rejects unknown top-level keys (`additionalProperties: false`), so a producer has
no valid way to record information the standard does not define. Implementers already work around
this: the refget/seqcol tooling (gtars) keeps a catch-all map of extra fields, and its records carry
keys such as `assemblySource` and `commonName` that FHR does not define. The proposal: allow
top-level keys that start with `x-`, as OpenAPI does for specification extensions, keep rejecting
every other unknown key, and release the change as a minor, backward-compatible schema version.

This is a **schema addition** (a relaxed constraint) to FHR, FHP and FHGFF3, and to the FHT draft
contract.

## Clarifications

### Session 2026-11-03

David Molik approved the proposal on #197 ("I think it sounds good"); Adam Wright approved going
ahead and answered the issue's open questions:

- Q: Which prefix? → A: `x-`, exactly, in lower case. Keys match
  `^x-[A-Za-z0-9][A-Za-z0-9_.-]*$` (research R-01 keeps the pattern unchanged).
- Q: Where are extension fields allowed? → A: At the top level only. Nested objects (`taxon`,
  authors, `accessionID`, `vitalStats`, software, `derivedFrom`, `source`, `genomeReference` and
  the rest) stay closed. Extension fields inside them are a possible future extension.
- Q: Which serialisations? → A: All of them: embedded `;~`/`#~` header lines and standalone YAML
  and JSON, for every header type (FHR, FHP, FHGFF3, FHT).
- Q: Must the part after `x-` be namespaced? → A: A namespace is recommended
  (`x-<project>-<field>`, for example `x-refget-commonName`) but not enforced, and validators do
  not warn about keys without one.
- Q: Which values? → A: Any JSON/YAML value. R11 (`>`/`@` escaping), R12 (YAML 1.1/1.2
  agreement) and R13 (finite numbers) still apply to extension keys and values, and the checksum
  covers the whole header as now.
- Q: What do JSON-LD and HTML microdata do with them? → A: Extension fields are left out of
  JSON-LD, the schema.org export and microdata; they are not mapped to any term. This keeps the
  J3/J8 hardening intact: no extension key or value can reach a JSON-LD processor or an HTML page
  through a writer (research R-04).
- Q: Can an extension change the meaning of a standard field? → A: No. An extension field never
  overrides a standard field. A widely used extension is promoted to a standard field under its own
  (unprefixed) name in a later minor version; the `x-` key is not renamed or reinterpreted.
- Q: Which versions? → A: A minor, backward-compatible change: FHR `"2.0"` → `"2.1"`, FHP and
  FHGFF3 `"1.0"` → `"1.1"`, in specification release v0.5.0 and toolkit 0.9.0. FHT is unreleased,
  so the rule is added to its draft `"1.0"` contract in FAIR-bioHeaders/FHT-Specification.
- Q: What about records that cite the older versions? → A: They are validated against the older
  schemas, where `x-` keys stay invalid. A record citing a v0.4.x schema URL already selects the
  v0.4.x schema (V2, V3); a record that cites a schema accepting several minors but states the
  older `schemaVersion` (`"2.0"`, `"1.0"`) is held to that minor, so `x-` keys are invalid in it
  too (research R-02). Every existing conformance vector keeps its outcome.

## User Scenarios & Testing

### User Story 1 - Record project-specific metadata in a valid header (Priority: P1)

A sequence-collection service wants to keep `commonName` and `assemblySource` with each FHR header.

**Independent Test**: combine metadata with `x-refget-commonName` and `x-refget-assemblySource`
into a FASTA file; verify it; convert it to JSON and YAML and back.

1. **Given** FHR 2.1 metadata with top-level `x-` keys holding strings, numbers, lists and objects,
   **When** it is validated, combined or verified, **Then** it is valid and the keys and values are
   kept, in order, in the header, JSON and YAML.
2. **Given** the same metadata in FHP 1.1 or FHGFF3 1.1 form, **When** it is validated, **Then** it
   is valid.
3. **Given** FHR 2.1 metadata with an `x-` value containing `>` or `@`, **When** the toolkit writes
   a FASTA header, **Then** the characters are escaped (R11) and read back unchanged.

### User Story 2 - Typos and unknown keys are still caught (Priority: P1)

**Independent Test**: validate records with `genom`, `X-foo`, `x-`, `x-_a`, `x- a`, `x-ä`, `x-a\n`
and an `x-` key inside `taxon`.

1. **Given** a record with an unknown key that does not match the pattern, **When** it is validated,
   **Then** it is invalid, as before.
2. **Given** an `x-` key inside a nested object, **When** it is validated, **Then** it is invalid.

### User Story 3 - Older records and older readers are unaffected (Priority: P1)

**Independent Test**: run every existing conformance vector and example; validate an `x-` record
that cites v0.4.0 or states `schemaVersion: '2.0'`.

1. **Given** any record valid under FHR 2.0, FHP 1.0 or FHGFF3 1.0, **When** it is validated with
   the new schemas, **Then** the result is unchanged.
2. **Given** a record with `x-` keys that cites a v0.4.x schema or states the older
   `schemaVersion`, **When** it is validated, **Then** it is invalid.

### User Story 4 - Linked-data and web forms carry only standard fields (Priority: P2)

**Independent Test**: convert an FHR 2.1 record with `x-` keys to JSON-LD, the schema.org export
and HTML microdata; read JSON-LD and microdata documents that hold an `x-` key.

1. **Given** a record with `x-` keys, **When** it is written as JSON-LD, export JSON-LD or
   microdata, **Then** the output holds no extension key or value, and the writer reports which
   keys it left out.
2. **Given** a JSON-LD or microdata document with an `x-` key, **When** it is read, **Then** it is
   invalid.

### Edge cases

- `x-` alone, upper-case `X-`, `x-` followed by `_`, `.` or `-`, by whitespace, by non-ASCII
  letters or digits (including look-alikes such as fullwidth or Kelvin-sign letters), and keys with
  a trailing line feed, which Python's `$` would otherwise accept.
- `x-` keys whose YAML plain form could be another type: none can be, because every key starts
  with the letter `x` (research R-03); their values follow R12 like any other value.
- `x-` values that are `null`, empty, nested deeply (the 64-level limit still applies) or that hold
  JSON-LD keywords such as `@context` or `@id`.
- An extension key named after a standard field (`x-genome`): valid; it means nothing to the
  standard and `genome` still governs.
- The FHGFF3 genome link, FHP `sourceType` rules and FHR V6 compatibility are unchanged.

## Requirements

- **FR-001**: docs/FORMAT.md gains rule R15 (extension fields): top-level keys matching
  `^x-[A-Za-z0-9][A-Za-z0-9_.-]*$` are allowed with any value in the header types and versions that
  accept them; every other unknown key is still invalid; nested objects stay closed.
- **FR-002**: R15 states the meaning rules: validators accept extension fields and attach no
  meaning to them; tools do not rely on them for anything the standard defines; an extension never
  overrides a standard field; widely used extensions are promoted under a new standard name; a
  namespace `x-<project>-<field>` is recommended and not checked.
- **FR-003**: R8, R11, R12 and R13 apply to extension keys and values; the checksum covers them
  like every other header byte.
- **FR-004**: New schema versions FHR `"2.1"`, FHP `"1.1"` and FHGFF3 `"1.1"` express R15. Each
  accepts the older minor `schemaVersion` too, but a record stating the older minor must not have
  `x-` keys. No key containing a line feed is valid.
- **FR-005**: The LinkML models and generator produce the new schemas; `check_linkml.py`, the drift
  baselines and every generated artifact agree.
- **FR-006**: `schemas/versions.json` and docs/SCHEMA-VERSIONS.md record release v0.5.0 with the new
  versions, prepared on `main` under the documented `preRelease` exception; examples and
  `llms.txt` follow it.
- **FR-007**: docs/JSONLD.md J9 and docs/MICRODATA.md M5: writers leave extension fields out and
  report it; a JSON-LD or microdata document with an extension key is invalid. The schema.org
  export leaves them out (X9). The JSON-LD context and vocabulary do not change.
- **FR-008**: Conformance vectors: valid FASTA/GFA/FHP/FHGFF3 records with `x-` keys; invalid
  records with a non-`x-` unknown key, with an `x-` key in a nested object, with `x-` keys under
  the older schema or `schemaVersion`, with malformed keys, and JSON-LD and microdata documents
  with an `x-` key. Every existing vector keeps its id, bytes and outcome.
- **FR-009**: The toolkit (FAIR-bioHeaders-Tools) bundles the new schemas, keeps the v0.4.x copies
  for V2/V3, selects them by rules V1–V6 unchanged, keeps `x-` fields through combine, strip,
  verify and JSON/YAML conversion, and drops them, with a warning, from JSON-LD, the export and
  microdata.
- **FR-010**: The FHT draft contract (FHT-Specification) adds the same rule to `"1.0"`.
- **FR-011**: The INSDC coverage assessment is re-pinned to the new `schemaVersion`s; no row's
  disposition changes.

## Success Criteria

- **SC-001**: Every existing conformance vector, example and test outcome is unchanged except where
  the documented prepared-release process updates examples to v0.5.0.
- **SC-002**: The new vectors pass `check_conformance.py --schema` and `--converter` with the
  toolkit branch.
- **SC-003**: No JSON-LD, export or microdata output of the toolkit or the reference scripts
  contains an `x-` key or value.
- **SC-004**: All specification, toolkit and FHT gates pass.

## Assumptions

- Python's `re` and ECMA-262 agree on `^x-[A-Za-z0-9][A-Za-z0-9_.-]*$` except for a trailing line
  feed (research R-01); the line-feed rule closes that gap.
- JSON Schema `patternProperties` keys are not "additional", so `additionalProperties: false`
  keeps rejecting every other key.
