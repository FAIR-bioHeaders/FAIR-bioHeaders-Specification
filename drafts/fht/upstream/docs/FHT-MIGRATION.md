# FHT 1.0 development contract and legacy migration

Status: **development contract for review under #7**, October 24, 2026. This is
the model implemented from the design approved on #6 / PR #20. It is not a
published release, not adopted community guidance, and not supported by the
family toolkit. Publication, release tags, immutable URLs and version
confirmation remain joint maintainer actions.

The generated JSON Schema is [`fht.json`](../fht.json); its source is
[`fht_linkml.yml`](../fht_linkml.yml). The legacy draft is preserved verbatim at
[`legacy/fht-v0.1.json`](../legacy/fht-v0.1.json) for audit.

## Canonical implementation path

`FHT-Specification` is the development source for the FHT model and its
generated development contract. `fht_linkml.yml` is the source; `fht.json` is
generated and must never be hand-edited. The reviewed schema artifacts are
expected to publish through FAIR-bioHeaders-Specification, consistent with the
shared family layout recorded for this development cycle. Until that
publication review happens, this repository is not claiming a released
contract, and no independently maintained competing schema is introduced. The
legacy draft is kept only at `legacy/fht-v0.1.json` for audit.

Consumers select a contract by the cited `schema` URL and the matching
`schemaVersion`. An unsupported version is rejected; it is not silently replaced
with raw main or the latest release. Immutable aliases and offline bundle
provenance are publication/toolkit concerns (#9 and the shared release
process), not something this development tree can establish.

## Shared imports and provenance

FHT imports the shared core and shared objects from the FAIR-bioHeaders
Specification repository at commit
`0ae18b00ee4bd71ab2dc28bae706b0f9d195076b`, the `v0.6.0` release. The design
decisions recorded in `specs/fht-field-decisions.md` were made against
`980029e5886a1a56a2d2545bfe59c7107539d38d` (v0.4.0/v0.4.1); between the two,
shared #170 widened the `lineageDataset` pattern, released in v0.6.0, and the
core file is unchanged. The copies in `schemas/` are verbatim:

| File | Source path | Role |
| --- | --- | --- |
| `schemas/core-v0.4.yaml` | `schemas/core.yaml` | Required/optional core slots, `Taxon`, `Author`, `DerivedFrom`, `HeaderType`, `DerivationRelationship` |
| `schemas/shared.yaml` | `schemas/shared.yaml` | `Software` and BUSCO `Completeness` objects |

`schemas/core.yaml` is byte-identical at v0.4.0, v0.4.1, v0.5.0, v0.6.0 and
the pinned commit; `schemas/shared.yaml` is the v0.6.0 file. Their
SHA-256 digests are recorded in [`schemas/provenance.json`](../schemas/provenance.json)
and checked by `scripts/check_provenance.py`. Replace them from a reviewed
release; do not edit them here.

## Contract version and URLs

The proposed contract version is `schemaVersion: "1.0"` (a string, MAJOR.MINOR),
separate from the transcriptome `version`, a repository release tag and the
file checksum. The generated schema keeps the development `$id`
`https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json`.
While FHT is a draft the only accepted `schema` value is that raw-main URL
(shared rule V7: a draft is cited by its owning repository's raw-main URL and
never takes a release form). The released forms, the shared repository's raw
tag URL and `https://w3id.org/fair-bioheaders/fht/vX.Y.Z`, are added to the
contract when FHT is published (issue #10). **No w3id alias or release tag is
published by this change.**

`fht.json` is the normative contract. `fht_linkml.yml` is its source, but
`json-schema-generator.py` adds rules LinkML cannot express: the permitted
`derivedFrom` parent pairs, at least one value per `sample` item, top-level
`x-` extension keys, exact checksum and SeqCol lengths, `minItems` on optional
arrays, non-blank required strings and named metadata authors, and the
`schemaVersion` enum. `linkml-validate` against the YAML model therefore
accepts some records that `fht.json` rejects (an FHP parent, an empty `sample`
item) and rejects valid `x-` extension fields. Validate records with
`fht.json` (JSON Schema 2020-12 with format assertion), not with
`linkml-validate`.

## Required fields

Exactly these nine fields are required; each has a real supplied value:

| Field | Contract |
| --- | --- |
| `schema` | FHT schema URL under the pattern above |
| `schemaVersion` | `"1.0"` |
| `transcriptome` | Resource name |
| `assemblyType` | `de novo`, `genome-guided` or `annotation-derived` |
| `taxon` | Shared `Taxon` object |
| `version` | Resource version |
| `metadataAuthor` | Ordered shared `Author` array |
| `dateCreated` | Resource creation date, never the sample collection date |
| `checksum` | Exact-file SHA-512/256, 44-character base64 |

Missing required values cannot be repaired with `null`, `unknown`, a guessed
person or a placeholder checksum. The record is incomplete.

## Optional fields

`moleculeType`, `assemblySoftware`, `sample`, `libraryStrategy`,
`strandedness`, `sequencingRuns`, `vitalStats`, `completeness`, `derivedFrom`,
`identifier`, `accessionID`, `scholarlyArticle`, `documentation`,
`relatedLink`, `funding`, `reuseConditions`, `voucherSpecimen`, plus the
legacy-compatible `transcriptomeSynonym`, `assemblyAuthor` and `instrument`.

Omit an optional value when it is unknown or is not true of the whole set. Do
not write empty strings, empty arrays or null sentinels. A measured zero is
kept.

### Molecule, library and alphabet

`moleculeType` is one biological class for the whole set: `mRNA`, `rRNA`,
`tRNA`, `transcribed RNA` or `mixed`. It is optional. `total RNA` and `cDNA` are
preparation contexts and are not accepted as molecule classes. Do not infer
`mRNA` from RNA-Seq, `cDNA` from T/U bytes, or `transcribed RNA` from `ncRNA`.
Unknown sets omit the field. Use `mixed` only for producer-supported mixtures of biological RNA classes; preparation material or uncertainty does not establish a mixture.

`libraryStrategy` is one supplied strategy string, not a frozen ENA enum.
`strandedness` is the FHT normalization `unstranded`, `forward` or `reverse`:
forward means the single read or read 1 is sense relative to the originating
transcript; reverse means antisense. It is not an ENA enum and does not
describe genomic plus/minus orientation. Unknown or mixed protocols are omitted.

FASTA parsing and checksums are alphabet-independent. T/U conversion is an
explicit derivative with a new checksum, never a header-parser fix.

### Sample and pooled material

`sample` is an optional **array** of `Sample` objects. Each object has optional
`tissue`, `tissueIdentifier`, `developmentalStage`, `condition` and `strain`.
`tissueIdentifier` is a CURIE (for example `UBERON:0000473`); the pattern checks
form, not resolution. Each entry must carry at least one supplied field, and its
text fields must be non-empty. Pooled material is represented by repeated
entries, each with only its own supplied values. Do not collapse a pool into one
fabricated uniform sample or treat a header entry as a complete BioSample record.

### Construction cases and parents

`assemblyType` describes construction, not quality or deposit class.

| Value | Meaning | Parent treatment |
| --- | --- | --- |
| `de novo` | Reads reconstructed without a reference genome constructing or grouping the assembly; later QC alignment does not reclassify it | No genome parent is required |
| `genome-guided` | Read evidence plus a reference constructed models or grouped reads; bases may come from reads or a later extraction | Genome guidance alone never justifies `transcribedFrom` |
| `annotation-derived` | Sequences extracted from existing annotation coordinates and the matching genome, without new read assembly in this step | Identify both sources when known; link the genome by `transcribedFrom` only when bases were extracted from it |

A composite or uncertain history has no `mixed` or `unknown` enum value. Do
not guess. Leave the record incomplete until the case is reviewed.

`derivedFrom` accepts only these reviewed pairs:

| Parent `headerType` | Allowed `relationship` | Condition |
| --- | --- | --- |
| `FHT` | `filteredFrom` | This set is a subset or filtered copy of another FHT file |
| `FHR` | `transcribedFrom` | Transcript bases were extracted from that genome, not merely guided by it |

The shared `DerivedFrom` object requires `headerType`, `relationship` and the
parent's FHR-family `checksum`; `accessionID` is additional, not a substitute
for a verified family link. `FHP` parents and other relationship values are not
accepted. An FHGFF3 annotation, project, study, sample, run or protocol is
context, not a sequence-derivation parent: link it through
`relatedLink`/`documentation` until the shared relationship vocabulary (#54) is
decided. `derivedFrom` items are ordered and at least one item is required when
the array is present.

### Statistics and completeness

`vitalStats` is optional and producer-reported:

- `totalTranscripts`: integer >= 0, number of FASTA records including isoforms;
- `N50`: integer >= 1, computed from all sequence symbols by descending record
  length;
- `averageTranscriptLength`: number >= 0, sequence symbols per record excluding
  deflines and line endings.

`completeness` reuses the shared BUSCO count object (`lineageDataset`,
`buscoVersion`, `mode`, four disjoint counts and `total`). BUSCO counts describe
ortholog groups, not FASTA records or genes; `total` is the number of BUSCO
groups searched. Only `vitalStats.totalTranscripts` counts FASTA records. BUSCO
is not a quality cutoff.

The shared lineage pattern accepts `_odb` plus digits and, since
FAIR-bioHeaders-Specification#170 at v0.6.0, one or more dot-separated numeric
version components such as `odb12.2`. A measured lineage is **not renamed or
coerced** to fit the pattern; malformed forms (`odb12.`, `odb.12`, `odb12..2`,
`odb12.2b`) stay rejected. If a measured value cannot be represented in the
typed object, keep it in `documentation` rather than falsifying the lineage.

## Legacy migration (fht.json v0.1 → FHT 1.0)

Migration is explicit. Preserve the original header bytes and supplied
metadata; do not guess values or silently promote a legacy record.

| Legacy field | FHT 1.0 treatment |
| --- | --- |
| `schema` | Keep a valid FHT contract URL. The old value may be malformed; correct the URL, not the transcriptome identity |
| `schemaVersion` | Number `1`/`1.0` becomes string `"1.0"` |
| `transcriptome`, `transcriptomeSynonym`, `taxon`, `version` | Retained. Do not repair a supplied taxon URI or synonym |
| `metadataAuthor` | Retained as header authors. Legacy `url` is not an `Author` member: map to `uri` only when it is a valid ORCID URL; the pinned shared pattern does not accept ROR or other organization URLs, so preserve those in `documentation`/`relatedLink` |
| `assemblyAuthor` | Retained as optional attribution, distinct from header authors and from a deposit submitter. Never merge the roles |
| `dateCreated` | Retained; it is resource creation, not sample collection |
| `assemblySoftware` | Legacy string becomes an array of shared `Software` objects: `name` from the supplied value. Add `version`/options only when actually supplied; never invent a version |
| `sample`, `libraryStrategy`, `strandedness`, `sequencingRuns` | Not inferred from the legacy record. Add only supplied values; an SRS sample accession is not a run |
| `instrument` | Retained as the legacy-compatible free-text array. Prefer run accessions when available |
| `vitalStats` | Keep `totalTranscripts`, `N50`, `averageTranscriptLength` when measured. `GCContent`, `isoformDiversity`, `expressionLevels`, `novelTranscripts` and the free-text `transcriptomeCompleteness` are not guessed into typed fields; preserve any needed text in `documentation` |
| `completeness` | Only from an actual BUSCO run with counts. A legacy completeness string is not converted into counts |
| `accessionID`, `identifier` | Retained as the transcriptome's own identifiers. Project/sample/run links belong in `relatedLink` |
| `scholarlyArticle` | Retained as a bare DOI; remove a resolver prefix only, do not invent a DOI |
| `documentation`, `relatedLink`, `funding`, `voucherSpecimen` | Retained |
| `license` | Reviewed separately into `reuseConditions`; do not copy blindly when the value is a name, a URL or a third-party notice |
| `masking` | Removed: a genome-assembly field with no FHT meaning. Do not add it back to pass older records |
| `checksum` | Legacy `md5:` values are not valid FHT checksums. Recompute SHA-512/256 from the exact file with the reviewed toolkit; never convert an MD5 string |
| Unknown legacy keys | Not accepted by the schema, which is closed except for top-level extension fields (`x-` keys, FAIR-bioHeaders-Specification `docs/FORMAT.md` R15). Decide explicitly whether to retain a value in documentation, move it to a standard field, or keep it under an extension key such as `x-<project>-<field>`; do not silently drop supplied metadata, and do not put a standard field's value only in an extension key |

The legacy examples are preserved verbatim in `legacy/examples/` as historical
review inputs, not valid FHT 1.0 fixtures. `examples/` holds synthetic examples
that validate against `fht.json`, one per construction type, checked by
`tests/test_examples.py`. Actual byte-backed positive and rejection conformance
fixtures, including RNA and cDNA bytes, are owned by #8.

## Verification and publication boundary

Run:

```sh
python -m unittest discover -s tests -v
python json-schema-generator.py
git diff --exit-code fht.json
python scripts/check_provenance.py
```

This PR supplies the model, generated schema, migration record, drift check and
validation tests. It does **not** publish a schema, assign a release tag or
w3id alias, add toolkit support, validate INSDC submission readiness, or create
the #8 fixtures. Those remain separate review gates (#8, #9, #10 and the
independent #157 assessment).

## Related records

- Issue #7: schema implementation and migration.
- Issue #6 / PR #20: approved initial design.
- `specs/fht-field-decisions.md`, `specs/fht-record-designs.md`,
  `specs/005-rna-transcriptome-header/spec.md`.
- Shared #54 (relationship vocabulary), #157 (INSDC coverage) and #170 (BUSCO
  lineage grammar).

## Narrow Q4/Q8 follow-up after #51 — 2026-11-17

[Adam's coordination proposal](https://github.com/FAIR-bioHeaders/FHT-Specification/pull/50#issuecomment-6929925451)
and [David's explicit approval](https://github.com/FAIR-bioHeaders/FHT-Specification/pull/50#issuecomment-6950266684)
authorize the remaining nonempty-value follow-up, distinct from the nine-root
presence decision. `transcriptome`, `version` and `dateCreated` must be nonblank;
`metadataAuthor` has at least one item and each metadata author has a nonblank
`name`. The local `MetadataAuthor` specialization implements that constraint
without changing the pinned shared `Author` object. Taxon members retain their current optionality,
including the already permitted empty taxon object; the FHT sample array stays.
No new taxonomy decision is opened here.

These are explicit rejection-boundary changes to the unreleased draft, not a
spelling correction: older readers may accept newly invalid empty metadata.
The proposed first-release version, nine required root names and every existing
75 conformance fixture byte/outcome/promotion marker remain unchanged. Direct
schema tests cover the new boundaries; new normative rejection vectors and their
consumer coverage remain part of #8/#9 coordination rather than being claimed
as already exercised by the older installed reader. No toolkit/native consumer
pin or released contract changes. The existing HTML reference must use the
updated owning contract with a verified local provenance anchor; its field
identities, seven canonical records and round-trip assertions stay intact.

The optional `libraryProtocol` proposal is withdrawn. Record an actual kit or
protocol name in `documentation` and an actual protocol URL in `relatedLink`;
this does not infer `strandedness`. A genome-guided workflow that actually
extracts its final transcript bases from a genome can cite that exact FHR parent
with `transcribedFrom` and its family checksum. Genome guidance alone proves no
such extraction; a genome accession or annotation URL is not a parent checksum.
The Q8 clarification changes no relationship pair or verification algorithm and
does not certify the biological truth of a schema-valid claim.

Refs #8 and #11: both remain open for acceptance and publication/runtime handoffs.

### Assembly author names (Q4, proposed after #50)

The Q4 answer ("absolutely required, every time, no exceptions") also covers the
names of supplied assembly authors. `assemblyAuthor` stays optional, but when it
is present every item has a nonblank `name`, through a local `AssemblyAuthor`
specialization with the same rule as `MetadataAuthor`. The shared `Author`
object, taxon members and the sample array are unchanged. An item that gives
only an ORCID `uri`, or an empty or whitespace name, becomes invalid: like the
rules above, this is a rejection-boundary change to the unreleased draft that
needs maintainer approval. The 75 conformance fixtures and the canonical
examples are unchanged, since none has an unnamed assembly author.
