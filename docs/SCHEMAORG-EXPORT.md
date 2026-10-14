# schema.org export of FAIR-bioHeaders metadata

The schema.org export is a **one-way** projection of an FHR record to a schema.org graph, for
search engines, validator.schema.org and Bioschemas tools. It is separate from the
[canonical JSON-LD form](JSONLD.md), which round-trips exactly and stays the default. The export
splits the record into the entities it describes:
- the assembly;
- the metadata record;
- the assembly activity;
- the statistics;
- the grant and the article.

The design is [specs/013-schemaorg-export](../specs/013-schemaorg-export/spec.md), from David
Molik's proposals on [#56](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/56). The
profile is **provisional** until #56 publishes its own export documents.

- Field-by-field table: [`mappings/fhr-schemaorg-export.yml`](../mappings/fhr-schemaorg-export.yml).
- Example: [`examples/example.fhr.export.jsonld`](../examples/example.fhr.export.jsonld).
- Fixtures, one per proposal: [`tests/fixtures/schemaorg-export/`](../tests/fixtures/schemaorg-export/).
- Toolkit: `bioheaders convert x.fhr.json x.jsonld --jsonld-profile export [--export-context FILE]`.

## Rules

The bracketed ids are stable labels used by the tests.

1. **[X1] Separate and one-way.**
   - The export is written only on request.
   - It never replaces the canonical form, and it cannot be read back as FHR metadata. Readers
     refuse it.
   - The canonical context and examples do not change.
2. **[X2] Shape.**
   - The document is `{"@context": {"@vocab": "http://schema.org/", "fhr": ..., "dct": ...},
     "@graph": [...]}`. That is a JSON-LD 1.0 context with no scoped contexts and no coercions, so
     JSON-LD 1.0 tools read it.
   - The graph holds, in order: the assembly (`Dataset`), the metadata record (`CreativeWork`),
     the assembly activity (`CreateAction`, only when it has content), and one `Observation` per
     numeric statistic.
   - The assembly's `@id` is the export context's `id`, or else the blank node `_:assembly`.
3. **[X3] Each statement on its own subject.**
   - The metadata record is `about` the assembly. It carries `metadataAuthor` as `creator`, the
     schema URL as `schemaVersion` and FHR's `schemaVersion` as `fhr:schemaVersion`.
   - The assembly carries `assemblyAuthor` as `creator`, plus `version` and `dateCreated`.
   - Authors are typed as in the canonical form: ORCID gives `Person`, ROR gives `Organization`,
     and an author with neither stays `fhr:Agent`. `fhr:Agent` is outside `creator`'s expected
     range, but classifying the author would invent metadata.
4. **[X4] Statistics are observations of the assembly.**
   - Each numeric `vitalStats` value becomes an `Observation` with:
     - `observationAbout` → the assembly;
     - `measuredProperty` → the FHR term (`fhr:N50`, …);
     - `value`, `unitCode` (Units Ontology) and `unitText`.
   - Units: base pair (`UO_0000244`) for N50, N90 and totalBasePairs; count unit (`UO_0000189`)
     for L50, L90, numberContigs and numberScaffolds; percent (`UO_0000187`) for gcContent.
   - No observation date is written.
   - The statistics are not `variableMeasured` of the dataset, because they describe the
     assembly, not variables measured within its sequence data.
   - `readTechnology` is text, so it stays canonical.
5. **[X5] Values are copied, never extended.**
   - Every value comes from the record or the export context, or is a fixed constant of the
     profile.
   - `funding` becomes a `Grant` whose `description` is the unchanged text. No funder, award
     number or amount is extracted.
   - `reuseConditions` and `documentation` become IRIs only when they are absolute URLs.
     Otherwise they stay text: a non-URL documentation is `description`, and a URL is
     `subjectOf`.
   - A licence that is text is kept as text, and validator.schema.org reports it. Use a licence
     URL.
6. **[X6] Identifiers keep their scope.**
   - The assembly's `identifier` lists `identifier[]`, then `accessionID` as a `PropertyValue`
     (`name`, `url`).
   - Then it lists `seqcol_id` as `{"@type": "PropertyValue", "propertyID": "GA4GH refget sequence
     collection", "value": <digest>}`.
   - No resolver URL is written for the SeqCol digest.
   - The file checksum stays `fhr:checksum`, and the metadata record has no identifier.
7. **[X7] The article.**
   - A `scholarlyArticle` that matches `^10\.[0-9]{4,9}/\S+$` becomes `subjectOf` → a
     `ScholarlyArticle`, whose `@id` is `https://doi.org/<DOI>` and whose `identifier` is a
     `PropertyValue` holding the DOI.
   - Any other value stays `citation` text.
   - The article DOI is never an identifier of the assembly.
8. **[X8] Assembly provenance.**
   - `assemblySoftware` becomes a `CreateAction`, whose `result` is the assembly and whose
     `instrument` is one `SoftwareApplication` per item. A legacy software string becomes one
     `SoftwareApplication` with that `name`.
   - Command-line options keep their order (`@list`).
   - `assemblyProtocol` is `actionProcess` → `HowTo` only when the export context sets
     `"assemblyProtocolHowTo": true`. Otherwise it stays `fhr:assemblyProtocol`.
   - The sequencing `instrument` stays `fhr:instrument`, because it may belong to an upstream
     sequencing activity.
   - No times or agents are written.
9. **[X9] Bioschemas and unmapped keys.**
   - The assembly claims `dct:conformsTo` Bioschemas Dataset 1.0-RELEASE only when every Dataset
     minimum property is present, as in the canonical form.
   - Keys that FHR's nested objects do not define are left out and reported, never projected under
     `@vocab`.

## Export context

The export context is a small JSON or YAML file, the same format as for the canonical form: `id`,
`url` and `keywords`. It may also contain `"assemblyProtocolHowTo": true` (X8). That key is
ignored by the canonical writer.

## What the export loses

The export is not a substitute for the canonical form. It drops:
- the record's key order and shape;
- keys that FHR's nested objects do not define;
- the canonical `vitalStats` object, except `readTechnology`.

It also asserts the article's resource type from the FHR field definition rather than checking it.
Use the canonical form, or FHR's JSON or YAML, to exchange or archive metadata.
