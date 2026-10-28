# Mappings

[Draft citation/deposit profile work for #56](mappings/README.md) now has a
separate export-context proposal, field inventory and worked descriptive bundle.
These are not adopted profiles or shipped DataCite/Crossref/ARK/Bib exporters.

FHR metadata is mapped to other vocabularies in separate profiles:

- [MIxS/MIGS](#mixsmigs-mappings): a partial projection to MIxS v7.0.1 terms
  (`fhr_mappings.yml`, `scripts/project_mixs.py`).
- [JSON-LD and Dublin Core (DCMI Terms)](#json-ld-and-dublin-core-dcmi-terms): every FHR
  field's JSON-LD term and DCMI Metadata Terms equivalents
  (`mappings/fhr-jsonld-dcmi.yml`), the starting point for the DataCite, Crossref, ARK and
  bibliographic exports of [#56](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/56).

## MIxS/MIGS mappings

The crosswalk is pinned to [MIxS v7.0.1](https://github.com/GenomicsStandardsConsortium/mixs/blob/v7.0.1/src/mixs/schema/mixs.yaml).
MIGS is a family of MIxS checklists. These mappings project overlapping sequencing
terms; they do not create a complete MIGS record or establish checklist compliance.

| FHR source | Target | Relationship | Handling and loss |
| --- | --- | --- | --- |
| `vitalStats.numberContigs` | `number_contig` (`MIXS:0000060`) | Exact | Copy the submitted assembly contig count. |
| `assemblyProtocol` | `sop` (`MIXS:0000090`) | Narrow | Copy the assembly protocol URI; FHR does not describe annotation procedures. |
| `assemblySoftware` | `assembly_software` (`MIXS:0000058`) | Lossy | One structured tool becomes `name;version;parameters`; URI is omitted. |

The LinkML model records term mappings on the corresponding slots. The reviewed
crosswalk in `fhr_mappings.yml` is executed by the small FHR-specific projection
script below; it is not a claim that an arbitrary LinkML transformation engine
can execute its expression extensions.

```bash
python scripts/project_mixs.py examples/example.fhr.json
```

The output includes `metadata`, `unmapped` reasons, and `target_version`. Missing
software versions/options are never invented. Legacy software-name strings,
multiple tools, or embedded semicolon/newline delimiters require manual projection.
An explicitly empty option list renders as `none`; argument lists use shell quoting.
No commands are executed. Missing source fields are reported as omissions.

`genome` names an organism/reference, while MIxS `assembly_name` identifies a
submitter's named/versioned assembly: there is no unconditional equivalence.
`dateCreated` is not a sample collection date. `accessionID.name` can name a
repository and must not be treated as an INSDC accession. Taxonomy and accession
crosswalks need additional source context. The earlier speculative NCBI/RefSeq/JGI
mappings have been removed rather than emitting misleading accession values.

**Identifier Conventions:** The shared core reserves `identifier` (a CURIE list) and
`accessionID` (a `{name, url}` object) for the described data itself
(`schemas/core.yaml`); they must not carry related project, sample or publication
identifiers. Links to related INSDC records — BioProject, BioSample, SRA studies —
belong in `relatedLink` as URLs (e.g. `https://www.ebi.ac.uk/bioproject/PRJNA…`,
`https://www.ncbi.nlm.nih.gov/biosample/SAMN…`). Publications are recorded with
`scholarlyArticle` (a bare DOI, no resolver prefix) or a `relatedLink` URL. The
CURIE pattern `^[A-Za-z0-9._-]+:.+$` applies to `identifier` entries of the
described data.

Check the target checklist's required fields, controlled vocabularies, and resource
submission rules before using the projection in a submission. Updating MIxS versions
requires reviewing term definitions and running the mapping fixtures again.

## JSON-LD and Dublin Core (DCMI Terms)

[`mappings/fhr-jsonld-dcmi.yml`](../mappings/fhr-jsonld-dcmi.yml) has one entry for each of the
51 property paths of the current `fhr.json` (`schemaVersion` `"2.0"`), including the v0.4
`nameType` and scaffold statistics. Each entry gives the term that the
[JSON-LD context](../jsonld/fhr.context.jsonld) uses ([JSONLD.md](JSONLD.md)), its DCMI
Metadata Terms equivalents (release 2020-01-20), a mapping kind for each, and the conditions,
losses and sources. Its format is [`mappings/mapping-table.schema.json`](../mappings/mapping-table.schema.json),
and `tests/test_jsonld_mappings.py` checks it against `fhr.json`, the context, the
[FAIR-bioHeaders vocabulary](TERMS.md), the pinned schema.org v30.1 subset and the DCMI term
list. Term IRIs come from LinkML; the table is curated and test-checked against them.

**Known mismatch.** The table records `source_schema_version: 1.0` as a number, because
[`mappings/mapping-table.schema.json`](../mappings/mapping-table.schema.json) types that field
as `number`, matching v0.3's numeric `schemaVersion`. It cannot hold the v0.4 string `"2.0"`,
even though the entry paths are the v2.0 paths checked against the current `fhr.json`.
Changing the field to a string is a mapping-format change and is separate from this
documentation update.

**Kinds** give the target term relative to the FHR field, as SKOS and LinkML do:

| Kind | Meaning | SKOS / LinkML |
| --- | --- | --- |
| `exact` | Same meaning and subject; the value copies unchanged | `skos:exactMatch` / `exact_mappings` |
| `broader` | The target term is broader than the FHR field | `skos:broadMatch` / `broad_mappings` |
| `narrower` | The target term is narrower; only some FHR values qualify | `skos:narrowMatch` / `narrow_mappings` |
| `related` | Associated, but not used to carry the value | `skos:relatedMatch` / `related_mappings` |
| `conditional` | Correct only when the entry's `condition` holds | none (procedural) |
| `lossy` | The value is carried, but the entry's `loss` is lost | none |
| `unsupported` | The target has no term; the entry gives a `reason` | `sssom:NoTermFound` |

`fhr_mappings.yml` words one pair the other way round: its `relationship: narrow` for
`assemblyProtocol` → MIxS `sop` means "FHR is narrower", which is `broader` in this table (the
`broad_mappings` of `fhr_linkml.yml` agree).

**Subject.** Statements are about the assembly unless an entry says `subject: record`. `schema`
and `metadataAuthor` (with its `name` and `uri`) describe the FHR metadata record, so a DCMI
export must attach them to the record, never to the assembly (#56: metadata authors are not
assembly authors).

<!-- Generated by scripts/make_jsonld.py from mappings/fhr-jsonld-dcmi.yml; do not edit. -->

| FHR path | JSON-LD term | JSON-LD kind | DCMI term | DCMI kind |
| --- | --- | --- | --- | --- |
| `schema` | `schema:schemaVersion` | conditional | `dcterms:conformsTo` | conditional |
| `schemaVersion` | `fhr:schemaVersion` | exact | none | unsupported |
| `genome` | `schema:name` | exact | `dcterms:title` | conditional |
| `genomeSynonym[]` | `schema:alternateName` | exact | `dcterms:alternative` | exact |
| `taxon` | `schema:about` | conditional | `dcterms:subject` | conditional |
| `taxon.name` | `schema:name` | exact | none | unsupported |
| `taxon.uri` | `@id` | exact | `dcterms:subject` | conditional |
| `version` | `schema:version` | exact | none | unsupported |
| `metadataAuthor[]` | `fhr:metadataAuthor` | exact | `dcterms:creator` | conditional |
| `metadataAuthor[].name` | `schema:name` | exact | none | unsupported |
| `metadataAuthor[].uri` | `@id` | exact | `dcterms:creator` | conditional |
| `metadataAuthor[].nameType` | `fhr:nameType` | exact | none | unsupported |
| `assemblyAuthor[]` | `schema:creator` | exact | `dcterms:creator` | exact |
| `assemblyAuthor[].name` | `schema:name` | exact | none | unsupported |
| `assemblyAuthor[].uri` | `@id` | exact | `dcterms:creator` | exact |
| `assemblyAuthor[].nameType` | `fhr:nameType` | exact | none | unsupported |
| `dateCreated` | `schema:dateCreated` | exact | `dcterms:created` | exact |
| `voucherSpecimen` | `fhr:voucherSpecimen` | exact | none | unsupported |
| `accessionID` | `fhr:accessionID` | exact | `dcterms:identifier` | conditional |
| `accessionID.name` | `schema:name` | conditional | `dcterms:identifier` | conditional |
| `accessionID.url` | `schema:url` | conditional | `dcterms:identifier` | conditional |
| `instrument[]` | `fhr:instrument` | exact | none | unsupported |
| `scholarlyArticle` | `schema:citation` | exact | `dcterms:isReferencedBy` | conditional |
| `documentation` | `schema:description` | conditional | `dcterms:description` | conditional |
| `identifier[]` | `schema:identifier` | exact | `dcterms:identifier` | exact |
| `relatedLink[]` | `fhr:relatedLink` | exact | `dcterms:relation` | exact |
| `funding` | `schema:funding` | conditional | none | unsupported |
| `reuseConditions` | `schema:license` | conditional | `dcterms:rights`; `dcterms:license` | broader; conditional |
| `masking` | `fhr:masking` | exact | none | unsupported |
| `vitalStats` | `fhr:vitalStats` | exact | none | unsupported |
| `vitalStats.L50` | `fhr:L50` | exact | none | unsupported |
| `vitalStats.N50` | `fhr:N50` | exact | none | unsupported |
| `vitalStats.L90` | `fhr:L90` | exact | none | unsupported |
| `vitalStats.totalBasePairs` | `fhr:totalBasePairs` | exact | none | unsupported |
| `vitalStats.numberContigs` | `fhr:numberContigs` | exact | none | unsupported |
| `vitalStats.numberScaffolds` | `fhr:numberScaffolds` | exact | none | unsupported |
| `vitalStats.readTechnology` | `fhr:readTechnology` | exact | none | unsupported |
| `vitalStats.N90` | `fhr:N90` | exact | none | unsupported |
| `vitalStats.scaffoldN50` | `fhr:scaffoldN50` | exact | none | unsupported |
| `vitalStats.scaffoldN90` | `fhr:scaffoldN90` | exact | none | unsupported |
| `vitalStats.scaffoldL50` | `fhr:scaffoldL50` | exact | none | unsupported |
| `vitalStats.scaffoldL90` | `fhr:scaffoldL90` | exact | none | unsupported |
| `vitalStats.gcContent` | `fhr:gcContent` | exact | none | unsupported |
| `checksum` | `fhr:checksum` | exact | none | unsupported |
| `assemblySoftware` | `fhr:assemblySoftware` | exact | none | unsupported |
| `assemblySoftware[].name` | `schema:name` | exact | none | unsupported |
| `assemblySoftware[].uri` | `schema:url` | conditional | none | unsupported |
| `assemblySoftware[].version` | `schema:softwareVersion` | exact | none | unsupported |
| `assemblySoftware[].commandLineOption[]` | `fhr:commandLineOption` | exact | none | unsupported |
| `assemblyProtocol` | `fhr:assemblyProtocol` | exact | `dcterms:relation` | broader |
| `seqcol_id` | `fhr:seqcol_id` | exact | none | unsupported |

<!-- End of generated table. -->

**Reusing this table (#56).** Further targets, such as DataCite, Crossref, ARK or BibTeX, are
added as new keys under `targets` and new per-entry lists beside `dcmi`, with the same mapping
fields and kinds. Existing rows do not change. A changed term or kind is a minor version of
`table_version` at least, and a removed entry a major one.
