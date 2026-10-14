# Research: RDA FAIR Data Maturity Model indicators interpreted for file headers

**Feature**: 010-fair-header-assessment (Phase 0 research, FR-012, FR-002, FR-011, User Story 3)
**Date**: 2026-10-10
**Inputs**: `spec.md` (clarified 2026-10-10); FAIR-bioHeaders `schemas/core.yaml` and `fhr.json`
at FAIR-bioHeaders-Specification `origin/main` 21fef56 (2026-10-09); `specs/004-shared-core-schema/spec.md`;
captured provider headers in `research/headers/`.

## 1. Source

| Item | Value |
|------|-------|
| Title | FAIR Data Maturity Model. Specification and Guidelines |
| Author | RDA FAIR Data Maturity Model Working Group |
| Version | 1.0, "Endorsed; final version" (RDA Recommendation), published 2020-06-25 |
| DOI | [10.15497/rda00050](https://doi.org/10.15497/rda00050) |
| Stable copy used | Zenodo record [3909563](https://zenodo.org/records/3909563): `FAIR Data Maturity Model_ specification and guidelines_v1.00.pdf` (sha256 `a3fa7da4...6c97`) and companion `FAIR_evaluation_levels_v0.02.xlsx` (sha256 `a47fba31...8a`) |
| Licence | Creative Commons Attribution 4.0 International (CC BY 4.0), stated on the document's title page and in the Zenodo metadata |
| Citation (as requested by the document) | FAIR Data Maturity Model Working Group (2020): FAIR Data Maturity Model. Specification and Guidelines. DOI: 10.15497/rda00050 |

The indicator ids, wording and priorities below are taken from Table 1 ("FAIR data maturity
model indicators", section 4.1, pp. 11-12) and the per-indicator descriptions in sections
4.2-4.5. There are **41 indicators**: 20 Essential, 14 Important, 7 Useful; 26 concern
metadata (M) and 15 concern data (D).

The model's own evaluation methods (section 6) are (a) "measuring progress" on five levels
(0 not applicable, 1 not being considered yet, 2 under consideration or in planning, 3 in
implementation, 4 fully implemented) and (b) "pass-or-fail", which counts only level 4 and
aggregates per area by priority. Levels 1-3 describe a provider's *intent and progress*
and cannot be observed in a file; see section 3 for how our statuses relate to them.

### Related assessment tools (how they operationalise the same indicators)

- **F-UJI** (FAIRsFAIR / PANGAEA; Devaraju & Huber, *Patterns* 2022, doi:10.1016/j.patter.2021.100370;
  metrics `fuji_server/yaml/metrics_v0.5.yaml` in github.com/pangaea-data-publisher/fuji). 17
  metrics derived from the RDA indicators (FsF-F1-01D ... FsF-R1.3-02D). Input is a PID or
  landing-page URL; metadata is harvested from the landing page (schema.org JSON-LD, DataCite,
  signposting, OAI-PMH). FsF-A2-01M is commented out of v0.5 because it cannot be tested
  automatically. FsF-R1.3-02D checks the *file format* against a list of community formats.
- **FAIR Evaluator / FAIR Maturity Indicators** (Wilkinson et al., *Sci Data* 6:174, 2019,
  doi:10.1038/s41597-019-0184-5; github.com/FAIRMetrics/Metrics `MaturityIndicators/Gen2`).
  Gen2 tests (Gen2_MI_F1A identifier uniqueness, F1B persistence, F2A/F2B structured/grounded
  metadata, F3, F4 search-engine indexing, A1.1, A1.2, A2, I1A/I1B, I2A/I2B, I3, R1.1) all start
  from a GUID and resolve it over HTTP; "strong" variants require linked data (RDF).
- **FAIR-Checker** (Gaignard et al., *J Biomed Semantics* 14:7, 2023, doi:10.1186/s13326-023-00289-5).
  Extracts RDF/JSON-LD from a web page and evaluates F1A/F1B, F2A/F2B, I1-I3, R1.1-R1.3 with
  SPARQL against the harvested graph and vocabulary registries (LOV, BioPortal, OLS).

None of them reads metadata embedded in a data file: all are online-first and centred on the
landing page / PID record. This is the gap stated in the spec Context. Where they test a
property that is also visible in a file (identifier syntax, licence, vocabulary IRIs,
qualified links, file format), we reuse their test logic (pattern + pinned registry lookup)
but apply it to header lines and run it offline.

## 2. Per-indicator file-header interpretation

**Assessability classes**
- **OFF**: assessable offline from the file alone (plus pinned, versioned reference tables
  shipped with the tool). Some OFF indicators have an optional online confirmation (noted).
- **ON**: needs the opt-in online check (FR-011); offline the indicator is reported as not
  run, never guessed.
- **N/A**: does not apply to an embedded file header; reason given. Reported as `not
  applicable` with a reason code, never silently dropped (FR-012).
- **OFF-body**: assessable offline but only from data records, not the header; deferred from
  the first release (see Decision A).

**Counts**: OFF 25 (header) + OFF-body 2 = 27 offline-assessable; ON 4; N/A 10. Total 41.

Field names in `code` are FAIR-bioHeaders core slots (core.yaml, spec 004 FR-001/FR-003) unless
prefixed `FHR:` (FHR-only, fhr.json). Native convention keys are shown as they appear in
files (GFF3 `##`/`#!`, VCF `##`, GAF `!`).

### Findable

| ID | Indicator (RDA wording) | Pri | M/D | Class | File-header interpretation and evidence | Core field(s) |
|----|------|-----|-----|------|------|------|
| RDA-F1-01M | Metadata is identified by a persistent identifier | E | M | N/A | An embedded header has no identity separate from the file that carries it; FHR `checksum` covers the sequences, not the header. Reason code `embedded-metadata`: identity is inherited from the file (assessed under F1-01D/F1-02D). A separate metadata record (landing page, BioSample, registry entry) is repository-level. | (none) |
| RDA-F1-01D | Data is identified by a persistent identifier | E | D | OFF (online upgrade optional) | Header states an identifier for *this file's own data* in a recognised PID scheme: DOI, INSDC/RefSeq assembly accession (`GCA_`/`GCF_` with version), ENA/SRA, or a CURIE whose prefix is in the pinned registry snapshot flagged as persistent. Persistence policy is judged by the scheme table, not by the evaluator. Labels like `GRCh38` are not PIDs. Note: in GFF3/VCF, `#!genome-build-accession`/`##reference` identify the *related* assembly, not the file, so they are credited under I3, not here. | `accessionID`, `identifier`, `scholarlyArticle` (DOI of the article is not the data's PID: no credit) |
| RDA-F1-02D | Data is identified by a globally unique identifier | E | D | OFF | As F1-01D, but uniqueness only: any registered-namespace CURIE/accession, or a content digest of the file's own data in a defined algorithm (FHR `checksum` sha512/256 base64, `seqcol_id` sha512t24u). Evidence is the value form plus registry entry. Optional (not default): recompute the FHR checksum / SeqCol digest and report mismatch (also feeds R1-01M accuracy). | `checksum`, `seqcol_id`, `identifier`, `accessionID` |
| RDA-F2-01M | Rich metadata is provided to allow discovery | E | M | OFF | Presence of a fixed set of discovery elements, mapped from F-UJI FsF-F2-01M core elements to file terms: subject name, taxon, version, creator, date, identifier. | FHR:`genome` (subject slot per type), `taxon`, `version`, `metadataAuthor`, `dateCreated`, `identifier`/`accessionID` |
| RDA-F3-01M | Metadata includes the identifier for the data | E | M | OFF | The header contains an identifier (any form in F1-02D) under a key whose meaning is "identifier of this data". Distinct from F1: F3 is about inclusion, F1 about the identifier's quality. | `identifier`, `accessionID`, `checksum` |
| RDA-F4-01M | Metadata is offered in such a way that it can be harvested and indexed | E | M | N/A | Reason code `repository-level`: indexing is an act of a searchable resource. Whether the header is machine-harvestable is assessed under I1-01M/I1-02M. Guideline note: register files (or their headers) with an index (e.g. the provider's search, FAIRsharing, Bioregistry-resolvable accession). | (none) |

### Accessible

| ID | Indicator | Pri | M/D | Class | File-header interpretation and evidence | Core field(s) |
|----|------|-----|-----|------|------|------|
| RDA-A1-01M | Metadata contains information to enable the user to get access to the data | I | M | OFF | Header states where/how to obtain the data: a URL with a scheme, an accession with a resolver URL, or access conditions. A bare accession with no URL is partial. Useful for copies that have travelled away from the download site. | `accessionID.url`, `relatedLink`, `documentation`, `reuseConditions`; GAF `!URL`; VCF `##contig=<URL=...>` |
| RDA-A1-02M | Metadata can be accessed manually | E | M | N/A | `embedded-metadata`: anyone holding the file can read a text header; the indicator is about the route to the metadata, which is the file distribution. | (none) |
| RDA-A1-02D | Data can be accessed manually | E | D | N/A | `object-in-hand`: the assessed object is the file itself. How to obtain it again is covered by A1-01M. | (none) |
| RDA-A1-03M | Metadata identifier resolves to a metadata record | E | M | N/A | `embedded-metadata`: no separate metadata identifier (see F1-01M). | (none) |
| RDA-A1-03D | Data identifier resolves to a digital object | E | D | ON | Opt-in: resolve the F1-01D identifier or `accessionID.url` (HTTP HEAD/GET via identifiers.org/doi.org). Evidenced only if it resolves; strongest if a checksum or size published there matches the file (reported as a note, not required). File contents are never sent. | `accessionID`, `identifier` |
| RDA-A1-04M | Metadata is accessed through standardised protocol | E | M | N/A | `embedded-metadata`: delivered with the file. | (none) |
| RDA-A1-04D | Data is accessible through standardised protocol | E | D | ON | Opt-in: the stated data URL uses http/https/ftp and the request succeeds. Offline, the URL scheme is shown as context only. | `accessionID.url`, `relatedLink` |
| RDA-A1-05D | Data can be accessed automatically | I | D | ON | Opt-in: the stated identifier/URL is retrievable without interaction (no login page, HTTP 2xx after redirects). | `accessionID.url`, `relatedLink` |
| RDA-A1.1-01M | Metadata is accessible through a free access protocol | E | M | N/A | `embedded-metadata`. | (none) |
| RDA-A1.1-01D | Data is accessible through a free access protocol | I | D | ON | Opt-in: the successful retrieval in A1-04D used an open protocol (http/https/ftp). | as A1-04D |
| RDA-A1.2-01D | Data is accessible through an access protocol that supports authentication and authorisation | U | D | N/A | `repository-level`: a property of the distribution service, applicable "where necessary"; FAIR-bioHeaders data is typically open. | (none) |
| RDA-A2-01M | Metadata is guaranteed to remain available after data is no longer available | E | M | N/A | `repository-level`. File-level reality differs fundamentally: embedded metadata disappears with the file by construction. Guideline note: deposit the header also in a durable record (archive landing page, registry) and point to it via `relatedLink`. F-UJI also excludes this (FsF-A2-01M commented out in v0.5). | (none) |

### Interoperable

| ID | Indicator | Pri | M/D | Class | File-header interpretation and evidence | Core field(s) |
|----|------|-----|-----|------|------|------|
| RDA-I1-01M | Metadata uses knowledge representation expressed in standardised format | I | M | OFF | Header lines follow a recognised, published header convention: FHR (YAML/JSON lines), GFF3 `##` directives and `#!` pragmas, VCF `##key=value` meta-information, GAF `!key: value`. Free `#` comments are not a standardised representation. | `schema`, `schemaVersion` |
| RDA-I1-01D | Data uses knowledge representation expressed in standardised format | I | D | OFF | The data format is a registered standard and is *declared* in the file with version: `##gff-version 3`, `##fileformat=VCFv4.x`, `!gaf-version: 2.x`. FASTA has no declaration mechanism: format is recognised by sniffing, so partial unless an FHR header names it. | (format directive; FHR `schema` identifies header, not body) |
| RDA-I1-02M | Metadata uses machine-understandable knowledge representation | I | M | OFF | RDA examples are RDF/OWL/JSON-LD/SKOS. File-header reading: header keys are mapped to IRIs through a declared machine-readable schema or context (JSON-LD `@context`, LinkML `slot_uri`). Finding: the core (`core.yaml`) uses `default_prefix: ex` (example.org) with no `slot_uri` mappings, so FHR headers are structured but not yet IRI-mapped (partial). Mapping core slots to schema.org/DCAT terms would raise this. | `schema` (+ future `slot_uri` mappings) |
| RDA-I1-02D | Data uses machine-understandable knowledge representation | I | D | OFF | Header gives typed, machine-readable definitions of the data's own fields: VCF `##INFO/FORMAT=<ID,Number,Type,Description>`, GFF3 `##feature-ontology` naming the type vocabulary. A declared format with no typed self-description (plain GFF3, GAF, FASTA) is partial or not evidenced. | (format-native) |
| RDA-I2-01M | Metadata uses FAIR-compliant vocabularies | I | M | OFF (online upgrade optional) | Ontology-backed header values are IRIs/CURIEs from vocabularies in the pinned registry snapshot (identifiers.org/Bioregistry): taxon `https://identifiers.org/taxonomy:NNNN`, ORCID, SO/GO/ECO terms. Labels only (`Homo sapiens`) or non-PID URLs (NCBI `##species https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/...?id=6239`) are partial. Online opt-in may check the IRI resolves. | `taxon.uri`, `metadataAuthor.uri`; spec 004 FR-006 (pinned ontology versions, term IRI) |
| RDA-I2-01D | Data uses FAIR-compliant vocabularies | U | D | OFF | The header declares the vocabularies (and versions) used in the data body: GFF3 `##feature-ontology <IRI>`, GAF GO/ECO version lines, VCF INFO definitions naming ontologies. Format specs that mandate a vocabulary (GFF3 column 3 = SO, GAF = GO) without a declared version are partial. Body values are not scanned in release 1. | (format-native) |
| RDA-I3-01M | Metadata includes references to other metadata | I | M | OFF | At least one identifier-form reference to a related entity's record: ORCID for people, taxonomy IRI, ROR for organisations, DOI of an article, grant identifier. | `metadataAuthor.uri`, `taxon.uri`, `scholarlyArticle`, `funding`, FHR:`assemblyAuthor.uri` |
| RDA-I3-01D | Data includes references to other data | U | D | OFF-body | Cross-references inside records (GFF3 `Dbxref=`, GAF DB:ID columns, VCF `ID` rsIDs). Data-body indicator: deferred (Decision A). | (none) |
| RDA-I3-02M | Metadata includes references to other data | U | M | OFF | Header refers to another dataset: assembly accession, reference genome, source release. RDA excludes the link to the described data itself (that is F3). Identifier form counts fully; a name-only reference (`##reference=GRCh38`, `#!genome-build WBcel235`) is partial. | `derivedFrom[]`, `relatedLink`; GFF3 `#!genome-build-accession`, `#!annotation-source`; VCF `##reference`, `##contig=<assembly=...>` |
| RDA-I3-02D | Data includes qualified references to other data | U | D | OFF-body | Qualified links inside records (e.g. GFF3 `Parent`/`Derives_from`, `Ontology_term`). Deferred (Decision A). | (none) |
| RDA-I3-03M | Metadata includes qualified references to other metadata | I | M | OFF | As I3-01M, and the relationship role is stated by a key whose meaning is defined in a published convention (e.g. `metadataAuthor` = author of the header instance; FHR:`assemblyAuthor` = assembler). A URL in a free comment line is I3-01M-only. | `metadataAuthor`, FHR:`assemblyAuthor`, `funding`, `scholarlyArticle` |
| RDA-I3-04M | Metadata include qualified references to other data | U | M | OFF | Core FAIR-bioHeaders indicator for derived files (User Story 2). Evidenced when a reference to another dataset uses an identifier form (`checksum`, `seqcol_id`, versioned accession) **and** its relationship is stated: `derivedFrom[]` with `headerType`, `relationship` (`annotates`, `transcribedFrom`, ...) and one of `checksum`/`seqcol_id`/`accessionID`; or a native key whose documented meaning is the relationship, e.g. GFF3 `#!genome-build-accession GCA_000001405.29` (meaning: assembly annotated by this file), satisfying spec Acceptance 1.1. Name-only (`##reference=GRCh38`) is partial. Matching sequence names/lengths is circumstantial and is **not** I3 evidence (FR-005); it is reported separately, as is the match/mismatch check (FR-006). | `derivedFrom.{headerType, relationship, checksum, seqcol_id, accessionID}` |

### Reusable

| ID | Indicator | Pri | M/D | Class | File-header interpretation and evidence | Core field(s) |
|----|------|-----|-----|------|------|------|
| RDA-R1-01M | Plurality of accurate and relevant attributes are provided to allow reuse | E | M | OFF | Presence of a fixed list of reuse attribute groups: identity (version), provenance (author, date, source), licence, taxon, method (FHR:`instrument`, `assemblySoftware`, `assemblyProtocol`), related data. "Accurate" is not judged; where an internal consistency check is defined (recomputed `checksum`/`seqcol_id`, declared lengths vs records) a mismatch is reported as a finding and prevents "evidenced". | `version`, `metadataAuthor`, `dateCreated`, `reuseConditions`, `taxon`, `documentation`, `voucherSpecimen`, `derivedFrom`, FHR:`instrument`/`assemblySoftware`/`assemblyProtocol` |
| RDA-R1.1-01M | Metadata includes information about the licence under which the data can be reused | E | M | OFF | A non-empty licence statement under a licence key. Human-readable text counts here. | `reuseConditions`; GAF/other native licence keys where present |
| RDA-R1.1-02M | Metadata refers to a standard reuse licence | I | M | OFF | The licence value is an SPDX licence identifier, or the canonical URL of a standard licence (Creative Commons, Open Data Commons), from the pinned SPDX licence list. A recognised licence *name* in free text is partial. | `reuseConditions` |
| RDA-R1.1-03M | Metadata refers to a machine-understandable reuse licence | I | M | OFF (online upgrade optional) | The value is an SPDX identifier or SPDX/CC licence IRI (both have published machine-readable expressions). RDA suggests resolving the link: the opt-in online check may confirm resolution. | `reuseConditions` |
| RDA-R1.2-01M | Metadata includes provenance information according to community-specific standards | I | M | OFF | Provenance under keys defined by the convention, in three groups: **who** (`metadataAuthor`, FHR:`assemblyAuthor`, VCF `##source`, GAF `!generated-by`, GFF3 `#!processor`), **when** (`dateCreated`, VCF `##fileDate`, GAF `!date-generated`, GFF3 `#!genebuild-last-updated`), **from what / how** (`derivedFrom`, GFF3 `#!annotation-source`, FHR:`assemblySoftware`). | `metadataAuthor`, `dateCreated`, `version`, `derivedFrom` |
| RDA-R1.2-02M | Metadata includes provenance information according to a cross-community language | U | M | OFF | Provenance is expressed in or mapped to a cross-domain language (PROV-O). In the core, `derivedFrom.relationship` is to be mapped to PROV-O / Relation Ontology (spec 004 FR-003, FAIR-bioHeaders-Specification#54, mapping not yet published): until then at most partial. Native conventions: not evidenced. | `derivedFrom.relationship` |
| RDA-R1.3-01M | Metadata complies with a community standard | E | M | OFF | The header meets the requirements of the convention it uses (required keys present, values well-formed): FHR validates against its schema; GFF3 starts with `##gff-version 3`; VCF `##fileformat` is the first line; GAF `!gaf-version` is the first line. FHR schema conformance is computed and reported separately (FR-008) and only *cited* here. | `schema`, `schemaVersion` + required slots |
| RDA-R1.3-01D | Data complies with a community standard | E | D | OFF | The file's records parse according to the declared format. Release 1: a bounded, deterministic check (header block and the first N records, N fixed and reported). Full validation is left to format validators (e.g. GFF3/VCF validators), whose output may be cited. | (format-native) |
| RDA-R1.3-02M | Metadata is expressed in compliance with a machine-understandable community standard | E | M | OFF | The header's convention has a machine-readable schema and the header declares it: FHR `schema` → JSON Schema / LinkML (evidenced if it validates). GFF3/VCF/GAF header conventions have prose specifications only (partial). | `schema`, `schemaVersion` |
| RDA-R1.3-02D | Data is expressed in compliance with a machine-understandable community standard | I | D | OFF | The data format is listed in the pinned community-format table (FAIRsharing-registered: FASTA, GFF3, GAF, VCF) **and** is declared with version in the file (as F-UJI FsF-R1.3-02D, but from the file rather than the MIME type). Recognised but undeclared (FASTA) is partial. | (format directive) |

### Where file-level reality differs from repository-level intent

1. **Metadata identity and persistence** (F1-01M, F1-02M, A1-03M, A1-04M, A1.1-01M, A2-01M):
   the RDA model assumes a metadata record separate from the data. An embedded header *is*
   part of the data object: it cannot outlive the file or have its own resolver. These are
   marked not applicable with a reason, and the guideline points to the repository-level
   remedy rather than inventing a header field.
2. **Access** (A1-*): repository tools test access by resolving a PID. A file that has
   already been downloaded can only *state* where it came from (A1-01M); retrieval is an
   online, time-dependent fact (ON, opt-in).
3. **Self-reference vs related data**: in derived files the most prominent identifier is
   often the *parent* assembly's (`#!genome-build-accession`), not the file's own. We credit it
   to I3-02M/I3-04M, not to F1/F3, so annotation files without their own accession do not
   look findable by borrowing the genome's.
4. **Content digests** (`checksum`, `seqcol_id`) are a file-level strength the repository tools
   do not use: they are globally unique, verifiable offline, and give a *recorded* link for
   I3-04M that can be checked against the related file (FR-006).
5. **Machine-understandable** (I1-02M, R1.3-02M): RDA examples assume RDF. File headers are
   key-value lines; we give credit for a declared machine-readable schema (R1.3-02M) and for
   IRI mapping of keys (I1-02M) separately, so FHR is not credited with semantics it lacks yet.

## 3. Status vocabulary and evidence rules

### Vocabulary (FR-002)

| Status | Meaning | RDA correspondence |
|--------|---------|--------------------|
| `evidenced` | Every condition of the indicator's rule is met by cited header lines | Level 4 / PASS |
| `partially evidenced` | At least one, but not all, conditions are met (rule-defined per indicator) | No RDA equivalent (levels 2-3 describe intent, not what a file shows); counts as not PASS |
| `not evidenced` | No condition is met, or the relevant values are malformed | FAIL (not mapped to level 1, which describes intent) |
| `not applicable` | The indicator cannot apply to this object; a reason code is mandatory | Level 0 |

Reason codes for `not applicable`: `embedded-metadata`, `repository-level`, `object-in-hand`,
`deferred-data-body`, `online-check-not-run`, `binary-format-out-of-scope`.

Every result also carries `method: offline | online`, the evidence lines (line number,
convention, key, value) and a suggestion (FR-003). No per-area RDA compliance level and no
aggregate score is computed (FR-004), although the per-indicator statuses are compatible
with the RDA pass-or-fail method should a user want to do it themselves.

**Open point for the spec**: FR-002 has four statuses. Reporting skipped online-only
indicators as `not applicable` with `online-check-not-run` keeps that vocabulary, but
"not applicable" then means two different things. Alternative: add a fifth status `not
assessed`. Recommend raising this at `/speckit.clarify` or in plan review.

### Evidence rules (conservative and reproducible)

1. **Only stated evidence**: statuses come from parsed header evidence items (key, value,
   line, convention) and, where the rule says so, from fixed-depth parsing of records. No free
   text is interpreted; no heuristic "looks like" credit. A value matching an identifier
   pattern counts only under a key whose documented meaning is that identifier (edge case
   "values that look like identifiers but are free text"; such values become a suggestion).
2. **Pinned reference tables**: PID schemes, identifier prefixes (Bioregistry / identifiers.org
   snapshot), SPDX licence list, community formats and the convention key map are shipped as
   versioned data files; their versions are printed in every report. Same file + same tool
   and table versions ⇒ identical report (FR-009, US4).
3. **All-of / any-of per indicator**: each indicator's rule lists its conditions; `evidenced`
   = all, `partially evidenced` = the rule's named subset, otherwise `not evidenced`. Example
   rules:
   - F2-01M: six discovery elements; all = evidenced, 3-5 = partial, ≤2 = not evidenced.
   - I3-04M: (identifier-form reference to other data) AND (stated relationship) = evidenced;
     either alone = partial.
   - R1.2-01M: who AND when AND from-what = evidenced; one or two groups = partial.
   - R1.1-01/02/03M are evaluated independently (a standard SPDX id satisfies all three; free
     text satisfies only 01M).
4. **Malformed beats present**: a value under the right key that fails its pattern
   (e.g. `checksum` not 44 base64 characters, `seqcol_id` not 32 characters, taxon URI not
   `identifiers.org/taxonomy:N`) yields `not evidenced` for the conditions it was meant to
   satisfy, plus a finding.
5. **Conventions combine**: if FHR lines and native directives are both present, the
   evidence is their union and every line used is cited; conflicting values (e.g. two
   different assembly accessions) are reported as a finding and block `evidenced` for the
   indicators involved.
6. **Online checks never run silently** (FR-011): the report states whether they ran. Online
   results may raise ON indicators from `not applicable (online-check-not-run)` to a status,
   and may upgrade OFF-with-upgrade indicators (F1-01D, I2-01M, R1.1-03M) only by adding a
   resolution note; they never downgrade an offline status. Each online result records URL,
   HTTP status and timestamp, and is marked non-reproducible over time.
7. **Recorded vs circumstantial** (FR-005): name/length agreement between an annotation and
   a genome is never credited under any RDA indicator; it is a separate section of the report.

## 4. Licence and attribution for reusing indicator text

The RDA document is licensed **CC BY 4.0** (title page: "License: Attribution 4.0
International (CC BY 4.0)"; Zenodo record 3909563 licence `cc-by-4.0`). Quoting the indicator
ids and titles and paraphrasing descriptions in the guideline and tool output is allowed,
including in derivative works, provided that:

- attribution is given: "FAIR Data Maturity Model Working Group (2020): FAIR Data Maturity
  Model. Specification and Guidelines. DOI: 10.15497/rda00050", with a link to the licence
  (https://creativecommons.org/licenses/by/4.0/);
- changes are indicated: the file-header interpretations are adaptations and must be marked
  as such (e.g. "Indicator text © RDA FAIR Data Maturity Model WG, CC BY 4.0; file-header
  interpretation by FAIR-bioHeaders");
- no endorsement by RDA is implied.

Recommendation: quote the short indicator titles verbatim (they are stable identifiers of
meaning) and paraphrase the longer descriptions; put the attribution once in the guideline
and in the tool's criteria data file, which also travels with every machine-readable report.
F-UJI, FAIRMetrics and FAIR-Checker are cited only, not copied.

## 5. Spec Kit research entries

### A. Which indicators the first release assesses

- **Decision**: All 41 indicators appear in every report. The first release *evaluates* the
  25 header-level offline indicators (OFF) by default and the 4 access indicators (A1-03D,
  A1-04D, A1-05D, A1.1-01D) only with the online opt-in. The 10 N/A indicators are listed with
  reason codes; the 2 data-body indicators (I3-01D, I3-02D) are listed as `not applicable
  (deferred-data-body)`.
- **Rationale**: FR-012 requires every indicator to be accounted for; FR-011 requires offline
  by default. The 25 OFF indicators cover all Essential indicators that a file can show
  (F1-01D, F1-02D, F2-01M, F3-01M, R1-01M, R1.1-01M, R1.3-01M/01D/02M) and the key
  FAIR-bioHeaders indicator I3-04M. The deferred pair are "Useful", need record scanning, and
  would make the run time depend on file size (SC-004).
- **Alternatives considered**: (1) Only the 17 F-UJI-aligned metrics: rejected, as it drops
  I3-04M and R1.2-02M which matter most for derived files, and F-UJI's set is landing-page
  oriented. (2) Assessing per FAIR principle (15) instead of per indicator: rejected by FR-012
  and loses the M/D distinction. (3) Treating metadata-identity indicators as satisfied by the
  file identity: rejected as over-crediting; inherited identity is stated in the reason
  instead. (4) Scanning record bodies for I3-01D/I3-02D now: deferred, not rejected.

### B. Status rules

- **Decision**: Four statuses (`evidenced`, `partially evidenced`, `not evidenced`,
  `not applicable` + mandatory reason code) decided by per-indicator all-of/any-of rules over
  parsed header evidence and pinned, versioned reference tables, with the seven rules in
  section 3. RDA maturity levels 1-3 are not used.
- **Rationale**: Reproducibility (FR-009, US4 identical re-runs) and reviewer agreement
  (SC-001 ≥ 90%) need rules without judgement; each status can be checked by reading the cited
  lines. RDA levels 1-3 describe a provider's plans, which a file cannot show. `partially
  evidenced` gives providers credit for progress (the aim of RDA "measuring progress") without
  claiming PASS.
- **Alternatives considered**: (1) RDA 0-4 progress levels: rejected, not observable from a
  file. (2) Binary pass/fail only: rejected, hides the common "name but no accession" case
  that is the cheapest fix. (3) Weighted scores per FAIR area: rejected by FR-004. (4) A
  fifth status `not assessed` for online checks that did not run: open, see section 3.

### C. How the guideline (User Story 3) is structured around the indicators

- **Decision**: The guideline is organised as **items** (what a header should contain), each
  item citing the RDA indicator ids and FAIR principle it serves, so that several indicators
  sharing evidence collapse into one item. Proposed items: (1) identify this file (F1-01D,
  F1-02D, F3-01M: `identifier`/`accessionID`, `checksum`); (2) describe it for discovery
  (F2-01M, R1-01M: subject, `taxon`, `version`, `dateCreated`); (3) declare the format and
  header convention with versions (I1-01M/01D, R1.3-01M/01D/02M/02D: format directive,
  `schema`/`schemaVersion`); (4) use identifiers, not labels, for taxa, people and terms
  (I2-01M/01D, I3-01M, I3-03M: `taxon.uri`, ORCID, ontology IRIs); (5) say which data this
  file was derived from and how (I3-02M, I3-04M, R1.2-02M: `derivedFrom`); (6) record provenance
  (R1.2-01M: who/when/from-what); (7) state a standard licence (R1.1-01/02/03M:
  `reuseConditions` as SPDX id); (8) say where to get the data (A1-01M, enabling the online
  A1 checks: `accessionID.url`, `relatedLink`). A final "Out of scope for headers" section
  lists the 10 N/A indicators with the repository-level action for each. Each item gives the
  core field name, an example in at least two conventions (FHR plus GFF3 `#!`/VCF `##`/GAF
  `!`), and the id of the assessment check that tests it.
- **Rationale**: Satisfies US3 Acceptance 1 (every item cites its principle; every relevant
  principle covered or marked out of scope) and Acceptance 2 (expressed in the file's own
  convention), FR-007 (core field names, two file types), and keeps the guideline short:
  8 items instead of 41 indicators. Mapping guideline item → check id → indicator ids gives
  the US3 independent test a 1:1 trace.
- **Alternatives considered**: (1) One section per indicator (41): rejected as too long and
  repetitive (several M/D pairs share evidence). (2) One section per FAIR principle (15):
  rejected, as principles such as A1 mix file-level and repository-level concerns and
  producers think in header fields. (3) One section per file type: rejected, contradicts
  "independent of file type"; file types appear as example columns instead.

## Sources

- RDA FAIR Data Maturity Model WG (2020), doi:10.15497/rda00050; Zenodo 3909563 (CC BY 4.0).
- F-UJI metrics v0.5: https://github.com/pangaea-data-publisher/fuji/blob/master/fuji_server/yaml/metrics_v0.5.yaml; Devaraju & Huber 2022, doi:10.1016/j.patter.2021.100370.
- FAIR Maturity Indicators Gen2: https://github.com/FAIRMetrics/Metrics/tree/master/MaturityIndicators/Gen2; Wilkinson et al. 2019, doi:10.1038/s41597-019-0184-5.
- FAIR-Checker: Gaignard et al. 2023, doi:10.1186/s13326-023-00289-5.
- FAIR-bioHeaders `schemas/core.yaml`, `fhr.json`, `specs/004-shared-core-schema/spec.md` at FAIR-bioHeaders-Specification 21fef56.
- Provider headers captured in `research/headers/` (Ensembl and NCBI GFF3, FASTA, VCF).
