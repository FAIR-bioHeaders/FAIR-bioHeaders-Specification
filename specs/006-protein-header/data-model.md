# Data model: FHP record

**Feature**: 006-protein-header | **Date**: 2026-10-11 | Source of truth: `fhp_linkml.yml` → generated `fhp.json`

All objects are closed: no unknown keys, and `null` is never a value (FR-010). Order below is the
key order of `fhp.json`. "Core" means the slot comes from `schemas/core.yaml` unchanged; "FHP" means
it is defined in `fhp_linkml.yml`.

## 1. FHP (root)

| Key | Origin | Required | Type and constraint |
|---|---|---|---|
| `schema` | core (FHP usage) | yes | string matching `^https://raw\.githubusercontent\.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/[A-Za-z0-9._/-]+/fhp\.json$` (D-02) |
| `schemaVersion` | core (FHP usage) | yes | number, `enum: [1]` (D-03) |
| `proteome` | FHP | yes | string: name of the protein set |
| `sourceType` | FHP | yes | `predicted` \| `database` \| `mixed` (§5) |
| `taxon` | core | yes | Taxon (§6): a single taxon (FR-012) |
| `version` | core | yes | string: version of the protein set |
| `metadataAuthor` | core | yes | array of Author (§6) |
| `dateCreated` | core | yes | string, `format: date` |
| `derivedFrom` | core | no | array of DerivedFrom (§2) |
| `source` | FHP | no | array of Source (§3) |
| `geneticCode` | FHP | no | integer in 1–6, 9–16 or 21–33 |
| `isoformPolicy` | FHP | no | `all` \| `longestPerGene` \| `canonicalPerGene` |
| `predictionSoftware` | FHP | no | array of Software (§4) |
| `predictionProtocol` | FHP | no | string, `format: uri` |
| `sequenceStats` | FHP | no | SequenceStats (§4) |
| `completeness` | FHP | no | Completeness (§4) |
| `voucherSpecimen`, `accessionID`, `scholarlyArticle`, `documentation`, `identifier`, `relatedLink`, `funding`, `reuseConditions` | core | no | as in the core |
| `checksum` | core | yes | 44-character base64 SHA-512/256 (R1–R4) |

FHR-only keys (`genome`, `genomeSynonym`, `assemblyAuthor`, `instrument`, `masking`, `vitalStats`,
`assemblySoftware`, `assemblyProtocol`, `seqcol_id`) are not FHP keys, so they are rejected
(FR-004). A protein set's own SeqCol digest is not modelled, because SeqCol is defined for
nucleotide sequence collections.

## 2. DerivedFrom (core, unchanged)

Required: `headerType` (`FHR` \| `FHT` \| `FHP` \| `FHGFF3`), `checksum` and `relationship`
(`annotates` \| `transcribedFrom` \| `translatedFrom` \| `filteredFrom` \| `assembledFrom`).
Optional: `seqcol_id` and `accessionID`.

Typical FHP use:

| Parent | headerType | relationship |
|---|---|---|
| Genome the proteins were translated from | `FHR` | `translatedFrom` |
| Annotation (gene models) | `FHGFF3` | `translatedFrom` |
| Transcriptome (ORF prediction) | `FHT` | `translatedFrom` |
| Larger protein set this one was filtered from | `FHP` | `filteredFrom` |

## 3. Source (FHP)

| Key | Required | Type | Example |
|---|---|---|---|
| `name` | yes | string | `UniProtKB` |
| `release` | no | string | `2026_03` |
| `setIdentifier` | no | string | `UP000005640` |
| `url` | no | uri | `https://www.uniprot.org/proteomes/UP000005640` |
| `assemblyAccession` | no | string | `GCA_000001405.29`, which the source asserts (not a link) |
| `sequenceCount` | no | integer ≥ 0 | sequences from this source in the file |
| `description` | no | string | what was taken, or how sequences were contributed |

## 4. Software, SequenceStats, Completeness (FHP)

- **Software**: `name` (required), plus `uri`, `version` and `commandLineOption` (an ordered
  array of strings).
- **SequenceStats**: `sequenceCount`, `geneCount` and `totalResidues`, all optional integers
  ≥ 0.
- **Completeness**:
  - required: `lineageDataset` (pattern `^[a-z0-9_]+_odb[0-9]+$`), `completeSingle`,
    `completeDuplicated`, `fragmented`, `missing` (integers ≥ 0) and `total` (integer ≥ 1);
  - optional: `buscoVersion` (string) and `mode` (`proteins` \| `transcriptome` \| `genome`).
  - The schema does not check that the counts add up to `total`. The counts are asserted, and a
    tool may report a discrepancy (US3 AS2).

## 5. sourceType semantics (FR-005)

| Value | Every sequence … | Typically also has |
|---|---|---|
| `predicted` | was produced by a gene-prediction or annotation run | `derivedFrom`, `predictionSoftware`, `geneticCode` |
| `database` | was taken from a published database release, set or annotation run | `source` |
| `mixed` | — the set combines origins or adds contributed sequences | `source` and/or `derivedFrom` |

None of the "typically also has" fields is required by `sourceType`. Missing evidence stays
missing.

## 6. Core objects in FHP

`Taxon` (`name`, `uri`), `Author` (`name`, `uri`) and `AccessionID` (`name`, `url`) keep the core's
attributes and patterns, but are **closed** in `fhp.json` (D-07). On `main` the core patterns are
FHR v0.3's. After the next `release-v0.4` sync they are the tightened v0.4 patterns (D-12).

## 7. Term annotations (for the later JSON-LD increment, D-08)

| Element | IRI |
|---|---|
| FHP root | `sdo:Dataset` |
| `proteome` | `sdo:name` |
| `Software` / its `name`, `uri`, `version` | `sdo:SoftwareApplication` / `sdo:name`, `sdo:url`, `sdo:softwareVersion` |
| `Source.name`, `Source.url`, `Source.description` | `sdo:name`, `sdo:url`, `sdo:description` |
| `Source`, `SequenceStats`, `Completeness` | `fhr:Source`, `fhr:SequenceStats`, `fhr:Completeness` |
| every other FHP slot | `fhr:<slot name>` |
