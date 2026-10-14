# Contract: the schema.org export profile

**Feature**: 013-schemaorg-export | Research: R-01 to R-11

The normative text is in [`docs/SCHEMAORG-EXPORT.md`](../../../docs/SCHEMAORG-EXPORT.md) (rules
X1–X9). This contract fixes the output shape that the reference exporter
(`scripts/make_jsonld.py`, `to_export`) and the toolkit must both produce byte for byte.

## Output

```text
{"@context": EXPORT_CONTEXT, "@graph": [ASSEMBLY, METADATA_RECORD, ACTIVITY?, OBSERVATION*]}
```

- `EXPORT_CONTEXT` = `{"@vocab": "http://schema.org/", "fhr": "https://w3id.org/fair-bioheaders/terms#", "dct": "http://purl.org/dc/terms/"}`.
- The JSON text is written with `json.dumps(document, indent=2, ensure_ascii=False)` plus a final
  newline, like the canonical writer.
- **Node identifiers**: the assembly is the export context's `id` or else `_:assembly`. The
  others are always blank nodes: `_:metadata-record`, `_:assembly-activity` and
  `_:observation-<KEY>`.

### ASSEMBLY (`Dataset`)

The keys appear in this order, and an absent field is left out:

| Key | From | Rule |
| --- | --- | --- |
| `@id`, `@type` = `Dataset` | export `id` | X2 |
| `name` | `genome` | |
| `alternateName` | `genomeSynonym` | list kept |
| `version` | `version` | |
| `dateCreated` | `dateCreated` | string kept |
| `about` | `taxon` | `{"@id": uri, "@type": "Taxon", "name": name}`, keys present only |
| `creator` | `assemblyAuthor` | typed items (X3) |
| `identifier` | `identifier[]`, `accessionID`, `seqcol_id` | strings, then `{"@type": "PropertyValue", "name", "url": {"@id"}}`, then the SeqCol `PropertyValue` (X6) |
| `description` / `subjectOf` | `documentation`, `scholarlyArticle` | X5, X7 |
| `citation` | `scholarlyArticle` (not a strict DOI) | X7 |
| `license` | `reuseConditions` | `{"@id"}` if an absolute URL, else text |
| `funding` | `funding` | `{"@type": "Grant", "description": text}` (X5) |
| `keywords`, `url` | export context | `url` as `{"@id"}` |
| `fhr:voucherSpecimen`, `fhr:instrument`, `fhr:relatedLink`, `fhr:masking`, `fhr:assemblyProtocol`, `fhr:vitalStats`, `fhr:checksum` | canonical terms | `relatedLink` and `assemblyProtocol` as `{"@id"}`; `fhr:vitalStats` only for non-numeric statistics (`{"@type": "fhr:VitalStats", "fhr:readTechnology": ...}`); `assemblyProtocol` is left out when written as a `HowTo` |
| `dct:conformsTo` | — | `{"@id": "https://bioschemas.org/profiles/Dataset/1.0-RELEASE"}` when complete (X8) |

### METADATA_RECORD (`CreativeWork`)

`@id` is `_:metadata-record` and `@type` is `CreativeWork`. It also has:
- `about`: `{"@id": <assembly @id>}`;
- `creator`: the typed `metadataAuthor` items;
- `schemaVersion`: `{"@id": schema}`;
- `fhr:schemaVersion`: the value.

### ACTIVITY (`CreateAction`), only when it has content

`@id` is `_:assembly-activity` and `@type` is `CreateAction`. It also has:
- `result`: `{"@id": <assembly>}`;
- `instrument`: a list of `SoftwareApplication`, each with `name`, `softwareVersion`,
  `url: {"@id"}` and `fhr:commandLineOption` (as `{"@list": [...]}`, because argument order
  matters) in that order, only the keys present;
- `actionProcess`: `{"@id": protocol, "@type": "HowTo"}`.

### OBSERVATION (`Observation`), one per numeric statistic in `vitalStats` key order

| Key | Value |
| --- | --- |
| `@id` | `_:observation-<KEY>` |
| `@type` | `Observation` |
| `name` | the FHR key |
| `observationAbout` | `{"@id": <assembly>}` |
| `measuredProperty` | `{"@id": "fhr:<KEY>"}` |
| `value` | the number, unchanged |
| `unitCode` | `{"@id": <UO IRI>}` |
| `unitText` | the UO label |

## Export context (provisional, extends 011)

The keys `id`, `url` and `keywords` are as in 011. There is one new optional key,
`assemblyProtocolHowTo`, a boolean. It is accepted, and ignored, by the canonical writer. In the
export, `true` turns `assemblyProtocol` into `actionProcess` → `HowTo`.

## Errors and warnings

- **Reserved keys:** same rules as the canonical writer (no `@` keys in the record).
- **Keys with no export target:** a key inside FHR's open nested objects that has no export
  target is reported (`unmapped_keys`) and left out.
- **Reading an export:** refused with the R-11 message.
