# Research: Enriched schema.org export

**Feature**: 013-schemaorg-export | **Date**: 2026-10-14

Every schema.org fact below comes from the release pinned for feature 011:
`schemaorg-current-https.jsonld`, v30.1, SHA-256
`0a4b8c4c910fc831ec8695196510973390906a5ee34dc6b862dfec4d21a12f74`. None of the terms used is
pending.

## R-01 One-way export, separate from the canonical form

- **Decision**: The export is a second JSON-LD profile, written only on request. The canonical
  form of feature 011 stays the default. Readers refuse an export document.
- **Rationale**: David asked to "distinguish enriched export graphs from the canonical
  round-trip JSON-LD format". The canonical form has a round-trip guarantee (011 FR-004). A graph
  that splits one record into several nodes, drops the key order and turns statistics into
  observations cannot keep that guarantee.
- **Alternatives**:
  - *Enrich the canonical form.* This breaks rules J1–J7 and every existing canonical document.
  - *Make the export the default for web embedding.* This changes behaviour that 011 users rely on;
    it can be revisited once #56 defines its export documents.

## R-02 Document shape: one `@graph`, a JSON-LD 1.0 context

- **Decision**: The export is `{"@context": {...}, "@graph": [...]}`. The context is
  `{"@vocab": "http://schema.org/", "fhr": FHR, "dct": DCT}` and nothing else. IRIs are written as
  `{"@id": ...}` value by value; there are no context coercions.
- **Rationale**:
  - validator.schema.org and other JSON-LD 1.0 tools do not process property-scoped contexts
    (011 V8).
  - `@vocab` is how schema.org markup is usually written.
  - Writing IRIs value by value makes every condition part of the exporter's logic, as David asked:
    "conditional prose alone must not imply that an unconditional context alias enforces the
    condition". For example, a licence is an IRI only when it is an absolute URL.
- **Alternatives**:
  - *Reuse the canonical context.* Its keys are FHR keys, not schema.org names, and it would need
    new terms for the export entities.
  - *A published export context file.* It's not needed, because the inline context is short and
    fixed.

## R-03 The metadata record as a separate `CreativeWork`

- **Decision**: A node `_:metadata-record` (`CreativeWork`) has:
  - `about` → the assembly;
  - `creator` → the typed `metadataAuthor` items;
  - `schemaVersion` → the FHR `schema` URL, as an IRI;
  - `fhr:schemaVersion` → the FHR `schemaVersion` value.

  The assembly keeps `creator` → `assemblyAuthor`, `version` and `dateCreated`.
- **Rationale**:
  - `schema:schemaVersion` has domain `CreativeWork` and range `Text` or `URL`. It means the schema
    version used by a creative work, which here is the metadata record.
  - `about` has domain `CreativeWork` and range `Thing`.
  - In FHR, `dateCreated` is "date the genome assembly was created", so it stays on the assembly.
  - This keeps the three versions David named apart: the schema URL, the metadata contract version
    and the assembly version.
- **Alternatives**:
  - *`mainEntity` instead of `about`.* `mainEntity` implies the record is primarily a page about
    one thing; `about` is the weaker, accurate claim.
  - *`sdDatePublished` on the record.* FHR has no record date, so none is written.

## R-04 Statistics as `Observation` nodes

- **Decision**: For each numeric statistic, the export writes an `Observation` with:
  - `observationAbout` → the assembly;
  - `measuredProperty` → the FHR metric term (for example `fhr:N50`, an `rdf:Property` in the
    vocabulary);
  - `value` → the number;
  - `unitCode` → a Units Ontology IRI, and `unitText` → its label;
  - `name` → the FHR key.

  There is no `observationDate`. `readTechnology` is text, so it stays canonical, in a reduced
  `fhr:VitalStats` node.
- **Rationale**:
  - `Observation` is a subclass of `QuantitativeValue`, so `value`, `unitCode` and `unitText` are in
    its domain. `observationAbout` (range `Thing`) points from the statistic to the assembly, and
    `measuredProperty` (range `Property`) keeps the precise FHR metric IRI.
  - David warned that statistics "characterize the assembly and must not automatically be treated as
    variables measured within its sequence dataset". `Dataset.variableMeasured` would say exactly
    that, and `additionalProperty` does not have `Dataset` in its domain.
  - The rule "do not infer an observation date from `dateCreated`" is followed by writing no date.
- **Units**:
  - base pair, `http://purl.obolibrary.org/obo/UO_0000244`: N50, N90, totalBasePairs and the v0.4
    scaffold N50 and N90;
  - count unit, `UO_0000189`: L50, L90, numberContigs, numberScaffolds and the v0.4 scaffold L50 and
    L90;
  - percent, `UO_0000187`: gcContent.

  The labels were checked in OLS on 2026-10-14 and none is obsolete.
- **Alternatives**:
  - *`PropertyValue` under `variableMeasured`.* This is what Bioschemas recommends for measured
    variables, but here it would put the statistics in the wrong place. It is recorded as a known
    difference from the Bioschemas recommendation.
  - *`PropertyValue` with no link from the assembly.* That leaves the statistics disconnected from
    what they describe.

## R-05 `funding` as a `Grant`

- **Decision**: The assembly has `funding` → `{"@type": "Grant", "description": <the funding
  text>}`, with no other property.
- **Rationale**:
  - The range of `schema:funding` is `Grant` alone, so the canonical text value already strains
    the range.
  - FHR defines `funding` as the funding source of the assembly, which is a grant of resources in
    schema.org's broad sense.
  - The text stays word for word. Funder, award number, amount and identifier are never extracted.
- **Alternatives**:
  - *Parse the text for a funder or award number.* That is fabrication, which constitution IV
    forbids.
  - *Keep the text literal.* That violates the range.

## R-06 Assembly provenance as a `CreateAction`

- **Decision**: When `assemblySoftware` is present, or the export context declares the protocol
  procedural, the export writes a node `_:assembly-activity` (`CreateAction`) with:
  - `result` → the assembly;
  - `instrument` → one `SoftwareApplication` per software item: `name`, `softwareVersion` from
    `version`, `url` from `uri` and `fhr:commandLineOption`. A legacy string item becomes
    `{"@type": "SoftwareApplication", "name": ...}`.
  - `actionProcess` → `{"@id": <protocol>, "@type": "HowTo"}`, only if the export context has
    `"assemblyProtocolHowTo": true`.

  The record's `instrument` (sequencing instrument) and, without that flag, `assemblyProtocol` stay
  as canonical FHR terms on the assembly.
- **Rationale**:
  - `result`, `instrument` and `actionProcess` all have domain `Action`; `actionProcess` has range
    `HowTo`.
  - David: "sequencing instruments may belong to an upstream sequencing activity", and "use `HowTo`
    only when the resource describes procedural instructions". The exporter cannot open the
    protocol offline, so the provider has to say so.
  - No `startTime`, `endTime` or `agent` is written, because the record has none.
- **Alternatives**:
  - *Put the sequencer in the same action.* That conflates two activities.
  - *Always write a `HowTo`.* That asserts a resource type nobody checked.

## R-07 `scholarlyArticle` as a `ScholarlyArticle` via `subjectOf`

- **Decision**: If the value matches the strict DOI syntax `^10\.[0-9]{4,9}/\S+$`, the assembly
  has `subjectOf` → a `ScholarlyArticle` with:
  - `@id` → `https://doi.org/<DOI>`;
  - `identifier` → `{"@type": "PropertyValue", "propertyID": "https://registry.identifiers.org/registry/doi",
    "value": <DOI>}`.

  Otherwise it stays `citation` text.
- **Rationale**:
  - FHR defines `scholarlyArticle` as the "article where the data was published", which describes
    the assembly. David: use `subjectOf` when the article describes it.
  - `subjectOf` has domain `Thing` and range `CreativeWork` or `Event`.
  - The strict syntax replaces the permissive v0.3 pattern `^10.` for this projection.
  - The `https://doi.org/` IRI is the DOI's standard form (DOI Handbook §3), not an invented
    resolver.
  - The DOI never becomes an identifier of the assembly.
- **Alternatives**: *Keep `citation` → article node.* That is right only for a cited work, and the
  FHR field means more than that.

## R-08 `seqcol_id`: a structured identifier in the export, and a subproperty in the canonical form

- **Decision**:
  - The export adds to the assembly's `identifier` list
    `{"@type": "PropertyValue", "propertyID": "GA4GH refget sequence collection", "value": <digest>}`.
  - The canonical vocabulary gains `fhr:seqcol_id rdfs:subPropertyOf schema:identifier`, through
    a LinkML `broad_mappings` entry like the one on `accessionID`.
  - No resolver URL is written.
- **Rationale**:
  - David: schema.org identifiers "are not limited to bibliographic/citation identifiers"; SeqCol
    identifies a sequence collection.
  - The FHR record's subject is the assembly, and the digest is the assembly's collection identity
    under the supplied attribute profile. That is the same kind of statement as `accessionID`, which
    already has this relation.
  - The scope stays separate from the file checksum (`fhr:checksum`) and from the metadata record,
    which has no identifier.
  - The structured form also states the scheme, which the plain literal cannot.
- **Alternatives**:
  - *Leave the canonical form unchanged.* That loses an inference that standard RDF consumers can
    use, and the subproperty statement is all David asked to assess.
  - *Use a refget URL.* A resolver would be invented.

## R-09 Companion export table instead of new mapping-table columns

- **Decision**: A new file, `mappings/fhr-schemaorg-export.yml`, with JSON Schema
  `specs/013-schemaorg-export/contracts/export-table.schema.json`. It has one entry per `fhr.json`
  path, giving `subject`, `property` and, as needed, `condition`, `transformation` and `loss`.
- **Rationale**:
  - The 011 table's schema is closed and describes canonical terms and DCMI equivalents.
  - The export answers a different question: which node, and under what condition.
  - A separate file keeps both tables simple, and each is test-checked against its own generator.
- **Alternatives**: *Add export columns to the 011 table.* That would change a schema #56 already
  builds on.

## R-10 Bioschemas implications

- **Decision**: As in 011, the assembly claims `dct:conformsTo`
  `https://bioschemas.org/profiles/Dataset/1.0-RELEASE` only when every Dataset minimum property is
  present.
- **Differences from Bioschemas recommendations**: statistics are not under `variableMeasured`
  (R-04), and the metadata record is a separate node. Neither is a minimum property.
- **Rationale**: Claiming conformance only when the minimum properties are present keeps the claim
  true.

## R-11 Reader behaviour

- **Decision**:
  - The toolkit's canonical reader sees the export context and refuses with: "this is a one-way
    schema.org export (FAIR-bioHeaders-Specification docs/SCHEMAORG-EXPORT.md); it cannot be read back as FHR
    metadata; use the canonical JSON-LD form".
  - The general reader (PyLD) does the same before expanding.
- **Rationale**: Silently mapping an export back would lose the record's subjects and order, and
  every term outside the canonical mapping would be reported anyway.

## R-12 Unclassified authors stay `fhr:Agent` (a known range exception)

- **Decision**: An author with neither an ORCID nor a ROR ID (nor, from v0.4, a `nameType`) is
  written as `{"@type": "fhr:Agent", "name": ...}` under `creator`, as in the canonical form.
- **Consequence**: `schema:creator` expects `Person` or `Organization`. `fhr:Agent` is a subclass
  of `schema:Thing`, so this is outside the expected range. It is the only such exception, and the
  domain/range test allows it only for `creator`.
- **Rationale**: FHR does not say whether a name-only author is a person or an organization.
  Choosing one would invent metadata (constitution IV). From v0.4, a provider can state the kind in
  `nameType`, and the shared typing function then gives `Person` or `Organization`.
- **Alternatives**:
  - *Leave unclassified authors out of `creator`.* That loses authorship.
  - *Write the name as text.* `creator` has no text range either.
