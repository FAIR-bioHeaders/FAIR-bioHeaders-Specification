# Data model: GFF3 annotation header (FHGFF3)

**Feature**: 007-gff3-header | **Date**: 2026-10-13 | Research: D-03 to D-05

## FHGFF3 record (class `FHGFF3`, `sdo:Dataset`)

| Slot | Required | Range | Source | Notes |
|---|---|---|---|---|
| `schema` | yes | string | core | Pattern: raw GitHub URL of `FHR-Specification/<ref>/fhgff3.json` (D-02) |
| `schemaVersion` | yes | `1` | core | `enum: [1]` |
| `annotation` | yes | string | FHGFF3 | Name of the annotation (`sdo:name`) |
| `taxon` | yes | `Taxon` | core | One taxon (FR-012) |
| `version` | yes | string | core | Version of the annotation |
| `metadataAuthor` | yes | `Author` list | core | |
| `dateCreated` | yes | date | core | Date the annotation was created |
| `checksum` | yes | `sha2` | core | Root checksum (R1–R4) |
| `genomeReference` | genome link* | `GenomeReference` | FHGFF3 | Accession plus SeqCol (D-03) |
| `derivedFrom` | genome link* | `DerivedFrom` list | core | The `annotates` item is the checksum genome link; other parents allowed |
| `source` | no | `Source` list | shared | Non-FAIR-bioHeaders sources (annotation releases, evidence sets) |
| `annotationSoftware` | no | `Software` list | shared | |
| `annotationProtocol` | no | uri | FHGFF3 | |
| `soVersion` | no | string | FHGFF3 | SO `data-version`, for example `2026-08-07` |
| `featureCounts` | no | `FeatureCount` list | FHGFF3 | |
| `completeness` | no | `Completeness` | shared | BUSCO counts |
| `voucherSpecimen`, `accessionID`, `scholarlyArticle`, `documentation`, `identifier`, `relatedLink`, `funding`, `reuseConditions` | no | | core | As in FHP |

\* At least one genome-link form: `genomeReference`, or a `derivedFrom` item with
`headerType: FHR` and `relationship: annotates`. At most one `annotates` item. Both forms may be
present; the checksum is authoritative (D-03).

Every object is closed, and `null` is never valid (FR-009).

## `GenomeReference` (`fhr:GenomeReference`)

| Attribute | Required | Range | Notes |
|---|---|---|---|
| `accession` | yes | string | Assembly accession with version, as published (for example `GCA_000001405.29`). Non-empty, no whitespace |
| `seqcol_id` | yes | core `seqcol_id` | 32 base64url characters |
| `assemblyName` | no | string | Assembly name, compared with `##genome-build` (D-07) |

## `FeatureCount` (`fhr:FeatureCount`)

| Attribute | Required | Range | Notes |
|---|---|---|---|
| `featureType` | yes | string | Column-3 type as written; pattern `^\S+$` |
| `count` | yes | integer ≥ 0 | |

## Shared module `schemas/shared.yaml` (D-04)

These are moved unchanged from `fhp_linkml.yml`: `Software` (`name` required, `uri`, `version`,
`commandLineOption`), `Source` (`name` required, `release`, `setIdentifier`, `url`,
`assemblyAccession`, `sequenceCount`, `description`), `Completeness` (`lineageDataset`, the five
counts and `total` required; `buscoVersion`, `mode`) and the `BuscoMode` enum. `fhp.json` stays
byte-identical.

## State: link-check results (tool output only)

For each `derivedFrom` item and for `genomeReference`: `matched` | `not matched` | `not checked`
(with a reason). The results are never written to the file.

## Native directives read (tool input only)

`##species`, `##genome-build`, `#!genome-build`, `#!genome-build-accession` in the leading block.
They are compared, never written (D-07).
