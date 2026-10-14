# Feature Specification: Enriched schema.org export of FAIR-bioHeaders metadata

**Feature Branch**: `013-schemaorg-export`

**Created**: 2026-10-14

**Status**: Draft

**Input**: David Molik's comment of 2026-10-14 on
[FAIR-bioHeaders-Specification#56](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/56),
"Likely required schema.org mapping additions". It asks for:
- a separate metadata-record `CreativeWork`;
- `funding` as a `Grant`;
- the numeric statistics as measurements;
- the assembly activity as a `CreateAction`;
- the article as a `ScholarlyArticle`;
- a structured SeqCol identifier.

It also asks to keep the enriched export separate from the canonical round-trip JSON-LD of
feature 011. Structured voucher specimens are deferred to #101.

## Clarifications

### Session 2026-10-14

These were resolved from David's comment, the 011 design and the pinned schema.org v30.1 release.
None needed a new maintainer decision.

- Q: Is the export a new default for JSON-LD output or web embedding? → A: No. The canonical
  JSON-LD of feature 011 stays the default and stays unchanged. The export is an opt-in profile,
  following David's instruction to "distinguish enriched export graphs from the canonical round-trip
  JSON-LD format".
- Q: Can an export document be read back as FHR metadata? → A: No. It is a one-way projection, and
  readers refuse it with a message that names the canonical form.
- Q: How are the numeric statistics attached to the assembly without treating them as variables
  measured within the sequence data? → A: As schema.org `Observation` nodes whose
  `observationAbout` is the assembly and whose `measuredProperty` is the FHR metric term. No
  observation date is written. `Dataset.variableMeasured` is not used (research R-04).
- Q: When is `assemblyProtocol` written as a `HowTo`? → A: Only when the export context says the
  protocol is procedural instructions. The exporter cannot check a remote resource offline.
  Otherwise the protocol stays the canonical `fhr:assemblyProtocol` (research R-06).
- Q: Does the canonical vocabulary gain `fhr:seqcol_id rdfs:subPropertyOf schema:identifier`?
  → A: Yes. The digest identifies the sequence content of the assembly that the record describes,
  in the same way that `accessionID` identifies the assembly, which already has this relation. The
  canonical document's keys, values and round trip do not change (research R-08).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish a richer schema.org description of an assembly (Priority: P1)

A data provider who already publishes FHR metadata as canonical JSON-LD wants a schema.org graph
that general-purpose consumers can use. Search engines, the schema.org validator and Bioschemas
tools understand typed entities such as `Grant`, `ScholarlyArticle` and `CreateAction` better than
FAIR-bioHeaders-specific terms.

**Why this priority**: This is the outcome #56 asks for. Each of the other stories adds one
entity to this graph.

**Independent Test**: Convert `examples/example.fhr.json` with the export profile. Paste the output
into validator.schema.org; it reports the expected types. Check it offline against the pinned
schema.org subset: every schema.org property is used within its domain and range.

**Acceptance Scenarios**:

1. **Given** a valid FHR record, **When** it is exported, **Then** the output is a JSON-LD graph
   whose assembly node is a `Dataset` and whose metadata-record node is a `CreativeWork` that is
   `about` the assembly.
2. **Given** the same record, **When** it is converted to canonical JSON-LD, **Then** the output is
   byte-identical to the output before this feature.
3. **Given** an export document, **When** it is read as FHR metadata, **Then** the reader refuses
   it and names the canonical form.

### User Story 2 - Give metadata authorship and schema their own subject (Priority: P1)

A consumer must not mistake the authors of the header (`metadataAuthor`) for authors of the
assembly, or the FHR schema URL for a property of the assembly.

**Independent Test**: Export a record with metadata authors and assembly authors. The metadata
authors are `creator` of the metadata-record `CreativeWork` only. The assembly authors are
`creator` of the `Dataset` only. `schema` and `schemaVersion` appear only on the metadata record.

**Acceptance Scenarios**:

1. **Given** `metadataAuthor` and `assemblyAuthor`, **When** exported, **Then** each list is
   attached to its own subject, with the same typing rule as feature 011 (ORCID → `Person`, ROR →
   `Organization`, otherwise `fhr:Agent`).
2. **Given** a record, **When** exported, **Then** the schema URL, the metadata `schemaVersion` and
   the assembly `version` keep their own values and are not merged.

### User Story 3 - Funding, article and identifiers as typed entities (Priority: P2)

**Independent Test**: The funding, article and SeqCol fixtures each give exactly the expected
nodes, with no value that is not in the source.

**Acceptance Scenarios**:

1. **Given** `funding` text, **When** exported, **Then** the assembly has `funding` → `Grant`,
   whose `description` is the unchanged text. No funder, award number, amount or identifier is
   added.
2. **Given** a `scholarlyArticle` DOI that matches the strict DOI syntax, **When** exported,
   **Then** the assembly has `subjectOf` → `ScholarlyArticle`. Its `@id` is the DOI's
   `https://doi.org/` IRI, and its `identifier` is a `PropertyValue` holding the unchanged DOI.
   The DOI is never written as an identifier of the assembly.
3. **Given** a `scholarlyArticle` value that does not match the strict DOI syntax, **When**
   exported, **Then** it is written as `citation` text and no article node is made.
4. **Given** `seqcol_id`, **When** exported, **Then** the assembly's `identifier` includes a
   `PropertyValue` with `propertyID` "GA4GH refget sequence collection" and the unchanged digest
   as `value`. No resolver URL is written.

### User Story 4 - Statistics and assembly provenance (Priority: P2)

**Independent Test**: The statistics fixture gives one `Observation` per numeric statistic, with
the FHR metric term, value and unit. The provenance fixtures give a `CreateAction` whose `result`
is the assembly and whose `instrument` is the assembly software.

**Acceptance Scenarios**:

1. **Given** numeric `vitalStats`, **When** exported, **Then** each becomes an `Observation` with
   `observationAbout` → assembly, `measuredProperty` → the FHR term (for example `fhr:N50`),
   `value`, and a unit (`unitCode` from the Units Ontology and `unitText`). There is no
   `observationDate`.
2. **Given** `readTechnology` (text), **When** exported, **Then** it stays as the canonical FHR
   term.
3. **Given** `assemblySoftware`, **When** exported, **Then** a `CreateAction` has `result` → the
   assembly and `instrument` → one `SoftwareApplication` per item. A legacy string item becomes a
   `SoftwareApplication` with that `name`. No start or end time is written.
4. **Given** `instrument` (the sequencing instrument), **When** exported, **Then** it is not made
   an `instrument` of the assembly action. It stays the canonical `fhr:instrument`, because the
   record does not say which activity used it.
5. **Given** `assemblyProtocol`, **When** exported, **Then** it is `actionProcess` → `HowTo` only
   if the export context declares it procedural. Otherwise it stays the canonical
   `fhr:assemblyProtocol`.

### Edge Cases

- **Optional fields absent:** no empty node and no node without content is written. For example,
  there is no `CreateAction` without software or a declared protocol.
- **No export context:** the assembly and metadata-record nodes get blank-node identifiers, and
  Bioschemas conformance is not claimed.
- **Statistic units:** each statistic has a fixed unit in the export table. A statistic the table
  does not know stays canonical.
- **URL-like text:** `reuseConditions`, `documentation` and similar values become IRIs only when
  they are absolute URLs; otherwise they stay text. The exporter decides per value, not through a
  context alias.
- **Unmapped keys:** keys that FHR's nested objects do not define are left out of the export and
  reported. They are not silently projected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The specification defines an export profile: a one-way projection of an FHR record
  to a schema.org JSON-LD graph. It has documented subjects, conditions, transformations and losses
  (`docs/SCHEMAORG-EXPORT.md`, rules X1–X9).
- **FR-002**: The canonical JSON-LD of feature 011 (rules J1–J7, the context and the examples)
  does not change, except for the vocabulary relation in FR-009.
- **FR-003**: The export uses only schema.org v30.1 terms (non-pending), FAIR-bioHeaders terms and
  `dct:conformsTo`. Every schema.org property is used on a subject within its domain, with values
  within its range. This is checked offline against the pinned schema.org subset.
- **FR-004**: Every literal value in an export comes from the source record or the export context,
  or is a fixed constant of the profile (unit labels, the SeqCol scheme label, type names). Nothing
  else is generated: no dates, funders, award numbers, resolver URLs or identity claims.
- **FR-005**: Each of David's proposals, and `seqcol_id`, has a complete fixture: a source record,
  an optional export context and the expected output. Both the reference exporter and the toolkit
  reproduce it byte for byte.
- **FR-006**: A companion table (`mappings/fhr-schemaorg-export.yml`) gives, for every FHR field,
  its export subject, its schema.org or FHR property, and any condition, transformation and loss.
  Tests check that its paths equal the `fhr.json` property paths and that the exporter emits each
  declared target.
- **FR-007**: The toolkit writes the export with `bioheaders convert ... --jsonld-profile export`,
  offline. It refuses to read an export document back.
- **FR-008**: Bioschemas Dataset conformance is claimed on the assembly node only when the Dataset
  minimum properties are present, as in feature 011.
- **FR-009**: The vocabulary states `fhr:seqcol_id rdfs:subPropertyOf schema:identifier`,
  generated from LinkML. The mapping table records it.
- **FR-010**: Structured voucher specimens are out of scope (#101). `voucherSpecimen` stays free
  text, in the canonical FHR term.

### Key Entities

- **Assembly** (`Dataset`): the genome assembly that the FHR record describes.
- **Metadata record** (`CreativeWork`): the FHR header itself, with its authors and schema.
- **Assembly activity** (`CreateAction`): the activity that produced the assembly, with the
  software as its instruments.
- **Statistic** (`Observation`): one measured characteristic of the assembly.
- **Grant**, **ScholarlyArticle**, **SeqCol identifier** (`PropertyValue`).

## Success Criteria *(mandatory)*

- **SC-001**: For every example and fixture, the export expands with a JSON-LD processor, and
  100% of its schema.org properties pass the domain and range check.
- **SC-002**: The canonical JSON-LD examples and conformance vectors are byte-identical before
  and after this feature.
- **SC-003**: Every literal value in every export fixture is traceable to the source, the export
  context or the profile's constants (tested).
- **SC-004**: All `fhr.json` property paths appear in the export table, and every declared target
  is produced by the exporter for the full fixture.
- **SC-005**: The toolkit's export output equals the specification fixtures byte for byte.
- **SC-006**: validator.schema.org recognises the types of the exported example (manual check,
  recorded).

## Assumptions

- The export profile is provisional until #56 publishes its own export documents, like the
  export-context format of feature 011.
- The Units Ontology (UO) IRIs for base pair (UO_0000244), percent (UO_0000187) and count unit
  (UO_0000189) are stable OBO identifiers, checked on 2026-10-14.
- schema.org v30.1, the release pinned for feature 011, is still the reference. New terms come from
  the same pinned file.
- The `https://doi.org/` form of a DOI is its standard persistent IRI, as the DOI Handbook says. It
  is a transformation of the supplied DOI, not an invented resolver.
