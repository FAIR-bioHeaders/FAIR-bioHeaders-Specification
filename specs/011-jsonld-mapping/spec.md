# Feature Specification: JSON-LD mapping and serialisation for FAIR-bioHeaders metadata

**Feature Branch**: `011-jsonld-mapping`

**Created**: 2026-10-10

**Status**: Draft

**Input**: FAIR-bioHeaders-Tools#35 ("JSON-LD serialisation") and spec 008 FR-005. David
Molik (2026-10-10): "Go ahead and make the JSON-LD mapping. I haven't started the Dublin
Core, DataCite, Crossref, ARK, and BibTeX/BibLaTeX documentation and mappings yet, and I
can reuse that in that ticket" (FAIR-bioHeaders-Specification#56).

## Clarifications

### Session 2026-10-10

- Q: JSON-LD shape? → A: FHR's own keys plus `@context` (lossless, round-trips) (FR-007).
- Q: Namespace for FHR-specific terms? → A: `https://w3id.org/fair-bioheaders/terms#`, unversioned (FR-008).
- Q: Validating JSON-LD documents? → A: The schema stays unchanged; the toolkit sets `@context`/`@type` aside before validation (FR-009).

## Context

FHR metadata is already available as JSON, YAML, HTML microdata and embedded FASTA/GFA
headers, but not as linked data. Search engines, Bioschemas-aware registries and FAIR
assessment services expect JSON-LD that uses shared vocabularies, chiefly schema.org.
#56 proposes qualified Dublin Core (DCMI) Terms as the shared descriptive layer for
DataCite, Crossref, ARK and bibliographic exports, so this mapping must line up with
DCMI rather than compete with it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish FHR metadata as linked data (Priority: P1)

A data portal converts an FHR record to JSON-LD and embeds it in the genome's landing
page, so that search engines and Bioschemas tools understand the species, authors,
assembly software and identifiers.

**Why this priority**: It is the reason for JSON-LD: machine-actionable discovery.

**Independent Test**: The JSON-LD for every FHR example expands with a standard JSON-LD
processor into triples whose predicates are schema.org (or documented FHR) terms, and
a schema.org validator accepts the page that embeds it.

**Acceptance Scenarios**:

1. **Given** a valid FHR record, **When** it is converted to JSON-LD, **Then** the result
   expands to linked data in which the taxon, people, software and identifiers are typed
   resources with IRIs where the record provides them.
2. **Given** the JSON-LD produced from a record, **When** it is converted back, **Then**
   the original FHR record is recovered exactly (round trip).

---

### User Story 2 - Reuse the mapping for other targets (Priority: P1)

A maintainer building the Dublin Core, DataCite, Crossref, ARK and BibTeX exports (#56)
reads one mapping table that gives, for every FHR field, its JSON-LD term and the
corresponding DCMI term, with notes on loss or conditions.

**Why this priority**: It avoids two diverging semantic mappings of the same fields.

**Independent Test**: Every FHR field (core and FHR-specific) appears in the table with
a schema.org or FHR term, a DCMI term or an explicit "no DCMI equivalent", and a
mapping kind (exact, broader, narrower, related, unsupported).

---

### User Story 3 - Read JSON-LD back into FHR (Priority: P2)

A tool receives FHR metadata as JSON-LD from a portal and converts it to an FHR header
for the genome file.

**Independent Test**: JSON-LD written by FAIR-bioHeaders, and an equivalent document
with keys reordered or compacted differently, both convert to the same FHR record.

### Edge Cases

- Fields with no schema.org equivalent (assembly statistics, masking, checksum).
- Values that are identifiers in some records and free text in others (identifier,
  relatedLink, accessionID).
- Optional fields absent: no empty or null nodes are emitted.
- A record citing a raw-main schema URL vs a versioned one (spec#44).
- Arbitrary JSON-LD from third parties that uses terms outside the mapping (reported,
  not silently dropped, when reading).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The specification MUST publish a JSON-LD context that maps every FHR
  property, including nested objects, to an IRI.
- **FR-002**: Properties with a schema.org equivalent MUST map to it; properties without
  one MUST map to terms in a FAIR-bioHeaders vocabulary, each defined with a label and
  description.
- **FR-003**: The mapping table MUST give, for every property, the JSON-LD term, the DCMI
  Terms equivalent (or "none"), the mapping kind, and notes on loss or conditions, in a
  machine-readable form that #56 can reuse.
- **FR-004**: The JSON-LD form MUST round-trip to the identical FHR record.
- **FR-005**: The toolkit MUST convert FHR records to and from JSON-LD alongside its other
  formats, offline, without fetching the context from the network.
- **FR-006**: Typed resources MUST be used for the record, taxon, people, software and
  identifiers, following Bioschemas profiles where one exists.
- **FR-007**: The JSON-LD form MUST be the FHR record itself with FHR's own keys, plus an `@context` (and optional `@type`), so one document is both FHR metadata and linked data.
- **FR-008**: FHR-specific terms MUST use the persistent, unversioned namespace `https://w3id.org/fair-bioheaders/terms#`, registered with w3id.org; term IRIs do not change between schema versions.
- **FR-009**: The FHR schema stays unchanged; when reading JSON-LD, the toolkit sets `@context` and `@type` aside before validating against the schema.

### Key Entities

- **Context**: the published JSON-LD context document.
- **Vocabulary term**: an FHR-specific property or class with IRI, label and description.
- **Mapping entry**: FHR property path, JSON-LD term, DCMI term, mapping kind, notes.

## Success Criteria *(mandatory)*

- **SC-001**: Every FHR example and conformance metadata record converts to JSON-LD and
  back unchanged.
- **SC-002**: 100% of FHR properties have a mapping entry with a DCMI column.
- **SC-003**: Expanded JSON-LD for the examples uses only schema.org, Bioschemas-endorsed
  or documented FAIR-bioHeaders terms.
- **SC-004**: The #56 work can start from the mapping table without re-deriving any field
  meaning (confirmed by the maintainer of #56).

## Assumptions

- schema.org is the primary JSON-LD vocabulary, because search engines and Bioschemas
  use it; DCMI equivalents are recorded alongside for #56.
- The existing HTML microdata serialisation stays as it is; JSON-LD is an additional
  format.
- Schema-authority decisions (spec#44, website#15) apply to which schema URL a JSON-LD
  record cites.
