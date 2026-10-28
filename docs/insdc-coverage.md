# INSDC Minimum-Specification Coverage Review

This document records how far the FAIR-bioHeaders specifications cover the requirements of the International Nucleotide Sequence Database Collaboration (INSDC) minimum specifications, with a final disposition for every requirement ([FAIR-bioHeaders-Specification#157](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/157)). It is a coverage assessment, not a plan to reproduce the INSDC specifications: differences in scope, purpose and representation are recorded, not resolved by copying INSDC fields into the headers.

A FAIR-bioHeaders header, a community profile or an optional field is never evidence that a file is ready to deposit. INSDC submissions are validated by the INSDC nodes' own tools and records; see [Using FAIR-bioHeaders alongside an INSDC submission](#4-using-fair-bioheaders-alongside-an-insdc-submission).

## Assessment version

**Assessment v1, 2026-10-28.** Every row below has a final disposition. Re-assess (and bump this version) when the pinned INSDC commit or any FAIR-bioHeaders `schemaVersion` changes; `tests/test_insdc_coverage.py` fails until the pins below are updated.

**Pinned inputs:**

- **INSDC**: [insdc/minimum-specifcations](https://github.com/insdc/minimum-specifcations) (the repository name is spelled this way upstream) at commit `41f0dc424748c9f7e50a8b6bda9b888218c4b65e` (2026-07-06). All ten categories are at v1.0. Text was read from the per-category PDFs in each `Current version/` folder.
- **FAIR-bioHeaders, released**: FHR `schemaVersion` `2.0`, FHP `1.0` and FHGFF3 `1.0` (`fhr.json`, `fhp.json`, `fhgff3.json`; release line v0.4.x, unchanged in v0.4.2).
- **FHT, draft (not released)**: the FHT 1.0 development contract, [`fht.json` at FHT-Specification `0ceb6f4`](https://github.com/FAIR-bioHeaders/FHT-Specification/blob/0ceb6f460e1f749f9eb2afb0a8b2f83cddb0e07a/fht.json), and the shared draft [specs/005-rna-transcriptome-header at `9a87e5c`](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/9a87e5cfe0ce3e024508ff8fdb58e6fe9042dffe/specs/005-rna-transcriptome-header/spec.md). FHT rows are marked **FHT (draft)** and describe a contract that can still change.
- **gff3-validator**: [rule catalogue at `c753f45`](https://github.com/FAIR-bioHeaders/gff3-validator/blob/c753f451d28b80b5f84c042e0f0486c3b1049adf/gff3_validator/catalogue.yaml) (`catalogue_version 0.1.0-draft`, 2026-10-08, a draft for Sequence Ontology review). Rules cited as implemented are implemented at that revision; planned rules are marked (planned).

**History:**

| Version | Date | Change |
| --- | --- | --- |
| v0 | 2026-10-22 | First-pass matrix posted on #157 with provisional dispositions. |
| v0 | 2026-10-28 | Landed in [#183](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/pull/183); review fixes in [#184](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/pull/184). |
| v1 | 2026-10-28 | Every requirement given an ID and a final disposition; coverage claims rechecked against the pinned sources; follow-ups opened; submission guidance and `tests/test_insdc_coverage.py` added. |

## Keys

**Requirement IDs.** INSDC does not number every requirement, so this review assigns IDs that follow each document's own numbering where it exists: `S` Sequence (rules 1–15), `A` Assembly (rules a–l), `AN` Annotation (rules a–d), `AY` Analysis, `SA` Sample, `P` Project, `PC` Package-Checklist (bullets numbered in document order; `T` rows are table 1 fields), and `EX`/`RR`/`CR` for Experiment, Raw Reads and Compressed Reads. `-xref`, `-ver`, `-fmt`, `-std` and `-fed` rows cover a document's cross-reference, versioning, data-format, standards and federation sections. Rows that share a disposition list several IDs. The full ID list is pinned in [`tests/fixtures/insdc-requirements.json`](../tests/fixtures/insdc-requirements.json).

**Coverage:** ✅ covered · ◐ partially covered · ✗ not covered · — out of scope by design.

**Disposition** (the first word of the last column):

- **Covered**: the released contract carries what the requirement asks of a file header.
- **Partial**: part is carried; the rest is recorded here and no change is planned.
- **Out of scope**: the requirement concerns sequence content, a single record, an archive record or a repository process, which a file-level header does not carry by design.
- **Follow-up**: a gap tracked in a linked issue.

## 1. Context triage: FAIR-bioHeaders and INSDC categories

| INSDC spec (all v1.0) | FH context | Relevance | Summary |
| --- | --- | --- | --- |
| [Sequence](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Sequence) | FHR (genome FASTA); FHT (draft, transcriptome FASTA) | Direct | File-level metadata and versioning overlap; sequence-content rules and per-sequence source modifiers are outside a file-level header |
| [Assembly](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Assembly) | FHR | Direct | FHR describes an assembled sequence set in the file; INSDC Assembly is the archive record for the same set |
| [Annotations](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Annotations) | FHGFF3 header + gff3-validator | Direct | The header carries provenance; feature rules belong to the validator |
| [Analysis](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Analysis) | FHR on FASTA and GFA, FHGFF3 on GFF | Partial | Checksum, type and title have analogues; filename and SRA-schema rules apply to the archive record |
| [Sample](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Sample) | `taxon`, `relatedLink` (sample record URLs), `voucherSpecimen`; FHT (draft) `sample` | Partial | No released type has a sample object; FH links to the BioSample record |
| [Project](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Project) | `relatedLink` (project record URLs), `scholarlyArticle` | Link only | FH links to the BioProject record and does not describe projects |
| [Package-Checklist](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Package-Checklist) | `schema` + `schemaVersion`, draft profiles, mapping tables | Analogue | Checklists govern sample records; FH profiles are the analogous mechanism for header fields |
| [Experiment](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Experiment) | FHR `instrument`, `vitalStats.readTechnology`; FHT (draft) `libraryStrategy`, `sequencingRuns` | Marginal | No experiment object in the family |
| [Raw Reads](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Raw%20Reads) | — | None | No FASTQ/BAM/CRAM header type exists or is proposed |
| [Compressed Reads](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Compressed%20Reads) | — | None | Same |

## 2. Coverage matrix

### Sequence Minimum Standards v1.0

| ID | INSDC requirement | FH type(s) | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- | --- | --- |
| S1 | IUPAC nucleotide characters only, no dashes; T instead of U regardless of molecule type | FHR, FHT (draft) | — | Headers never validate or rewrite sequence bytes. FHT (draft) FR-006 allows U in RNA FASTA; T/U conversion is an explicit derivative with a new checksum | **Out of scope** — sequence content; convert U to T for submission, then recompute the header |
| S2 | DNA 5′ to 3′ | FHR, FHT (draft) | — | no sequence-content rule | **Out of scope** — sequence content |
| S3 / S4 | Minimum length 100 nt; 1000 nt for WGS top-level contigs | FHR, FHT (draft) | — | `vitalStats` reports statistics and sets no minimum | **Out of scope** — sequence content, checked by INSDC tools |
| S5 | At most 50% N unless a complete chromosome | FHR | — | `vitalStats.gcContent` is a statistic, not a rule | **Out of scope** — sequence content |
| S6 / S7 | Gap spans all N; no leading/trailing N except telomere, centromere, circular or contamination gap | FHR | — | would need a sequence plus annotation cross-check; no FH rule | **Out of scope** — sequence content; the family has no FASTA content validator and none is proposed |
| S8 | Sequence determined or contracted by the submitter, or third-party | FHR, FHP | — | FHR `metadataAuthor`/`assemblyAuthor` name who made the file; FHP `sourceType` says where sequences came from | **Out of scope** — an attestation made at submission, not file metadata |
| S9 | Joined sequences in biological order with gaps | FHR | — | no sequence-content rule | **Out of scope** — sequence content |
| S10 | No vector/linker unless synthetic; contamination screening to order; proposed screening checksum report | FHR | ◐ | `assemblySoftware` and `assemblyProtocol` can name the screening tools and run; no screening-result field | **Partial** — tools can be named; a screening-report field would be a schema addition and is not proposed while INSDC's report format (10.b) is undefined |
| S11 | Semantic and syntactic FASTA validation; full specification still to be developed | FHR, FHT (draft) | ◐ | FH specifies its own header block (FORMAT.md), versioned schemas, conformance vectors and `bioheaders verify`; FASTA body rules (blank lines, IUPAC) are not checked | **Partial** — FH validates the header block only; sequence-body validation stays with INSDC tools |
| S12 | Sequence-specific metadata (molecule type, topology, chromosome type, localization) included with each sequence | FHR, FHT (draft) | — | headers describe the whole file; no per-sequence fields. FHT (draft) `moleculeType` is one value for the file | **Out of scope** — per-sequence metadata belongs in the deflines or the submission |
| S13 | Technique keywords (HTGS/STS/GSS/WGS, TSA) validated against molecule type | FHR, FHT (draft) | ◐ | FHR: no keyword field. FHT (draft): `assemblyType` and `moleculeType` (`mRNA`, `rRNA`, `tRNA`, `transcribed RNA`, all RNA, consistent with "TSA should not be DNA") | **Partial** — FHT (draft) has the file-level analogue; INSDC's keyword list is still to be determined, so no FHR keyword field is proposed |
| S14 | Submitter sequence name under 51 characters, INSDC-legal characters, not an accession pattern | FHR | — | per-sequence naming; `assess related` compares names across GFF3/FASTA pairs as a consistency check | **Out of scope** — per-sequence naming |
| S15 | Chromosome, linkage-group, plasmid and organelle naming rules | FHR | — | per-sequence naming | **Out of scope** — per-sequence naming |
| S-fmt | Data formats: a unified FASTA with per-sequence source modifiers and technique keywords, possibly JSON in the defline | FHR, FHT (draft) | — | FH headers are a file-level block before the first record and define no per-record defline | **Out of scope** — a per-record defline format is a separate layer; a file-level FH header can sit alongside it |
| S-xref | Cross-references: publication; reads, assembly, annotations, study, sample, validation reports | FHR, FHP, FHGFF3 | ◐ | `scholarlyArticle` (DOI); `relatedLink` for record URLs (MAPPINGS.md identifier conventions); FHP/FHGFF3 `derivedFrom` (FH parents by checksum); FHGFF3 `genomeReference`; no validation-report link | **Partial** — links to INSDC records travel as `relatedLink` URLs; FHR `derivedFrom` is not offered, by design, because it is reserved for FH parents (see §3) |
| S-ver | Accession.version; version increments with sequence change; reassembly is a new set version | FHR, FHP, FHGFF3 | ◐ | required free-text `version`, required exact-byte `checksum`, optional `seqcol_id` | **Partial** — FH assigns no accessions; its checksum changes on any byte change, including header edits, while `version` is producer-assigned and can stay unchanged for metadata-only edits |

### Assembly Minimum Specification v1.0

| ID | INSDC requirement | FH type(s) | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- | --- | --- |
| A.a | Link to a public BioProject | FHR | ◐ | no field; the BioProject record URL belongs in `relatedLink` | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — nothing checks that the link is present; a draft INSDC profile can require it |
| A.b | Link to a public BioSample | FHR | ◐ | no field; the BioSample record URL belongs in `relatedLink`; `voucherSpecimen` is free text about the physical sample (structured vouchers: #139) | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — as A.a |
| A.c | Identity of the submitter, owner, consortium or center | FHR | ◐ | `metadataAuthor` and `assemblyAuthor` are required, but an empty list or an author without `name` is valid (SCHEMA-GAP-AUDIT GAP-1) | **Follow-up** [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189) — non-empty authors are a next-major constraint |
| A.d | BioSample taxID at species rank or below; binomial for clone/isolate assemblies | FHR | ◐ | `taxon` is required, but `taxon.uri` (identifiers.org NCBI taxonomy) is optional; rank cannot be checked by schema | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190), [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189) — a profile can require `taxon.uri`; requiring it in the base contract is a next-major decision; rank needs a taxonomy lookup |
| A.e | Molecule types appropriate for a genome (genomic DNA/RNA, viral cRNA, other DNA/RNA) | FHR | — | FHR's subject is a genome; molecule type is per sequence in INSDC | **Out of scope** — per-sequence metadata (as S12) |
| A.f / A.g | All linked sequences live; withdrawn sequences withdraw the assembly | FHR | — | archive lifecycle; offline, `bioheaders verify` detects a stale FH parent by checksum | **Out of scope** — repository lifecycle policy |
| A.h | All sequences from one BioSample and one taxID | FHR | ◐ | `taxon` is a single object, so a file asserts one taxon; no sample field | **Partial** — one taxon per file by structure; the sample is identified only by its `relatedLink` URL |
| A.i | All sequences from the same INSDC provider | FHR | — | archive-side rule | **Out of scope** — archive policy |
| A.j | Assembly method and version/dates; sequencing technologies | FHR | ◐ | `assemblySoftware` (`name` required, `version`), `assemblyProtocol`, `dateCreated` (required), `vitalStats.readTechnology`, `instrument`; all but `dateCreated` optional | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — the fields exist but are optional; a profile can require them |
| A.k | Metadata values at most 1000 characters | FHR | ✗ | FH sets no length limits | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — check lengths before copying values into a submission |
| A.l | Unique sequence names; chromosome/plasmid/organelle names; per-sequence type and level | FHR | — | per-sequence assembly structure; `vitalStats` holds aggregates only | **Out of scope** — per-sequence structure is submitted separately (for example as chromosome assignment or AGP files) |
| A-ver | Version increments on sequence, membership, name or level change; not on metadata-only change | FHR | ◐ | as S-ver | **Partial** — the checksum changes on metadata-only header edits, unlike an INSDC version; `version` need not |

### Annotation Minimum Specification v1.0

*FHGFF3 headers carry provenance only; feature rules are gff3-validator's. Catalogue rule IDs below drop the `GFF-` prefix (`SYN-013` is `GFF-SYN-013`).*

| ID | INSDC requirement | FH type(s) | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- | --- | --- |
| AN.a | Conform to the INSDC GFF3 specification or feature table | FHGFF3 | ◐ | header lines are GFF3 comments after `##gff-version 3`; gff3-validator checks GFF3 1.26 syntax and structure; INSDC submission tools are untested with `#~` blocks | **Follow-up** [#191](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/191) — test table2asn and Webin-CLI; until then strip the header before submission |
| AN.b.i | Features and qualifiers limited to the INSDC Feature Table | FHGFF3 | ◐ | types checked against a pinned SO release (SO-001…009), not against the INSDC feature and qualifier lists | **Partial** — SO's mapping to INSDC features is incomplete upstream (AN-std), so an INSDC feature-table check cannot be derived from SO alone |
| AN.b.iii | Feature locations: start/end/strand present; within the sequence; one sequence; intervals ordered per strand; partial only at ends; CDS/mRNA locations compatible | FHGFF3 | ◐ | b.iii.1: SYN-013…015, SYN-017; b.iii.2: STR-008, STR-011, BIO-002; b.iii.3: STR-002; b.iii.6: BIO-005 (CDS within exons) only; b.iii.4 and b.iii.5: no rule | **Follow-up** [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27) — rules for b.iii.4–6 |
| AN.b.iv | Intervals do not overlap; rRNA does not overlap CDS or rRNA; tRNA not inside a CDS exon | FHGFF3 | ✗ | no implemented rule; STR-012/013 (planned) are parent/child checks | **Follow-up** [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27) — overlap rules, with the slippage exception |
| AN.b.v | Complete CDS at least 30 aa; complete tRNA 50–150 bp; introns at least 10 bp | FHGFF3 | ✗ | BIO-009 checks multiple-of-three only | **Follow-up** [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27) — length rules, with the evidence and low-quality exceptions |
| AN.b.vi | Coding regions: translation matches `/translation`; start/stop codons or partial; phase ≠ 0 partial; translation exceptions; product nomenclature; no product on pseudo parents; mRNA-record rules | FHGFF3 | ◐ | BIO-004 (phases), BIO-006/007 (start/stop), BIO-008 (internal stops), BIO-010 with `--genome` and an explicit `--translation-table`; vi.1 is feature-table only; vi.4 and vi.7 have no rule; vi.6 is not machine-checkable; vi.8/vi.9 need a record molecule type | **Follow-up** [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27) — rules for vi.4 and vi.7 |
| AN.b.vii | CDS parent via `Parent=` (GFF3) or `transcript_id` (feature table), unique genome-wide | FHGFF3 | ◐ | STR-004 (Parent resolves), STR-006 (no cycles), STR-001 (unique IDs); no check that every CDS has a Parent | **Follow-up** [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27) — check that every CDS has a Parent; transcript_id is feature-table only |
| AN.b.viii | Feature types prohibited on some molecule types | FHGFF3 | — | GFF3 carries no record molecule type | **Out of scope** — needs record-level context GFF3 does not carry |
| AN.b.ix | locus_tag present in genome submissions; consistent prefix; unique per gene | FHGFF3 | ✗ | no rule | **Follow-up** [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27) — locus_tag rules; placement (core or profile) to decide |
| AN.c.i | Prokaryote partiality only where abutting a gap or sequence end | FHGFF3 | ✗ | no rule | **Follow-up** [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27) — prokaryote partiality rule |
| AN.c.ii | `artificial_location` only in genome-scale annotation | FHGFF3 | ✗ | no rule | **Follow-up** [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27) — `artificial_location` scope rule |
| AN.c.iii | Translations use the INSDC translation table of the declared organism | FHGFF3, FHP | ◐ | validator `--translation-table` is explicit, never inferred; FHP `geneticCode` records the NCBI table; FHGFF3 has no `geneticCode` | **Partial** — the table is supplied to the validator; an FHGFF3 slot would be a schema addition and is not proposed without demand |
| AN.d | Amino acids NH3 to COOH; no internal stops; IUPAC amino acids; provided translation matches; complete CDS start and stop | FHGFF3, FHP | ◐ | BIO-006/007/008 with `--genome` (d.ii, d.v); d.i and d.iii concern protein sequences, which no FH tool validates; d.iv is feature-table only | **Partial** — codon checks exist; protein-sequence content is outside FH |
| AN-xref | Mandatory links to sequence, sample, assembly, study, validation reports; optional publication and db_xrefs | FHGFF3 | ◐ | `genomeReference` (assembly accession and `seqcol_id`) or `derivedFrom` an FHR file; `relatedLink` for study and sample; ATT-014 checks `Dbxref` form; no validation-report link | **Partial** — the genome link is first-class; other links are `relatedLink` URLs |
| AN-std | Standards: INSDC Feature Table; Sequence Ontology with incomplete INSDC mappings | FHGFF3 | ◐ | validator pins an SO release and SO rules; the Feature Table is not modelled | **Partial** — the incomplete INSDC to SO mapping is upstream at the Sequence Ontology |

### Analysis Minimum Specification v1.0

| ID | INSDC requirement | FH type(s) | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- | --- | --- |
| AY1 | Link to one BioProject and one or more BioSamples, public when the analysis is public | FHR, FHGFF3 | ◐ | `relatedLink` record URLs | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — as A.a and A.b |
| AY2 | Valid against the INSDC SRA analysis schema | FHR, FHGFF3 | — | applies to the SRA XML record | **Out of scope** — archive record format |
| AY3 | Mandatory TITLE and DESCRIPTION | FHR, FHGFF3 | ◐ | `genome` / `annotation` names are required; `documentation` is optional | **Partial** — names exist; a description is optional |
| AY4 | Mandatory ANALYSIS_TYPE | FHR, FHGFF3 | ◐ | the header type and `schema` URL identify FHR or FHGFF3; no analysis-type field | **Partial** — the submitter picks ANALYSIS_TYPE; FH types do not map one-to-one |
| AY5 | Mandatory STUDY_REF | FHR, FHGFF3 | ◐ | `relatedLink` (BioProject record URL) | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — as A.a |
| AY6 | Mandatory filename and filetype | FHR, FHGFF3 | — | FH binds metadata into the file and records no filename | **Out of scope** — the archive record describes the file from outside |
| AY7 | Mandatory checksum | FHR, FHGFF3 | ◐ | SHA-512/256 over the file bytes except the checksum line, required in every type | **Partial** — not the whole-file digest INSDC records; compute the submission checksum on the uploaded file |
| AY8 | Compressed files must be decompressed | FHR, FHGFF3 | — | FH tools read gzip and BGZF | **Out of scope** — exchange policy |
| AY9 | Data files supported by the analysis type (TSV/CSV/GFF; BNX/CMAP/XMAP; GFA; FASTA) | FHR, FHGFF3 | ◐ | FASTA and GFA (FHR), GFF3 (FHGFF3); no type for TSV, CSV, BNX, CMAP or XMAP | **Partial** — a new file family would need a new header type; none is proposed |
| AY-xref | Links out (protocol DOI, publication) and within categories | FHR, FHGFF3 | ◐ | `assemblyProtocol` / `annotationProtocol` (URI), `scholarlyArticle`, `relatedLink` | **Partial** — carried as URIs and DOIs, not typed links |
| AY-ver | Accessioned, not versioned | FHR, FHGFF3 | — | FH requires a resource `version`; accessions come from the archive | **Out of scope** — archive accessioning |

### Sample Minimum Specification v1.0

| ID | INSDC requirement | FH type(s) | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- | --- | --- |
| SA.1 | Metadata limited to ASCII | FHR, FHP, FHGFF3 | ✗ | YAML values are UTF-8 | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — check before copying values into a sample record |
| SA.2 | Unique for a submitter | FHR, FHP, FHGFF3 | — | archive-side uniqueness | **Out of scope** — archive policy |
| SA.T1 | Sample alias, unique across a submission | FHR, FHP, FHGFF3, FHT (draft) | ◐ | no released field; BioSample URL in `relatedLink`; the draft AgBioData profile adds `sampleIdentifier`; FHT (draft) `sample` holds tissue and condition, "not a complete BioSample record" | **Partial** — FH links to the sample record instead of containing it |
| SA.T2 | Organism name in NCBI Taxonomy at species rank or below | FHR, FHP, FHGFF3 | ◐ | `taxon` required; `taxon.uri` optional; rank not checkable | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190), [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189) — as A.d |
| SA.T3 | Geographic location | FHR, FHP, FHGFF3 | — | absent from every type | **Out of scope** — belongs in the BioSample record (MIxS layer), which FH links to |
| SA.T4 | Collection date | FHR, FHP, FHGFF3 | — | absent; `dateCreated` is not a collection date (MAPPINGS.md) | **Out of scope** — as SA.T3 |
| SA.T5 | Checklist/package name, validated against a version | FHR, FHP, FHGFF3 | — | analogue: required `schema` URL and `schemaVersion`; draft profiles registry | **Out of scope** — governs sample records; FH's analogue is `schema` + `schemaVersion` |
| SA.T6 | Package-defined mandatory attributes | FHR, FHP, FHGFF3 | — | analogue: draft profiles make optional slots required | **Out of scope** — sample-checklist content |
| SA.T7 | Submitter name and affiliation | FHR, FHP, FHGFF3 | ◐ | `metadataAuthor` name, ORCID `uri`, `nameType`; no affiliation field; may be empty (GAP-1) | **Follow-up** [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189) — non-empty authors; an affiliation is recorded as its own `Organizational` entry |
| SA.3 | No HTML markup | FHR, FHP, FHGFF3 | ✗ | string values may contain HTML; R11 escapes only `>` and `@` | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — not checked by the released contract |
| SA.4 | Syntactic validation against the BioSample XSD | FHR, FHP, FHGFF3 | — | applies to BioSample XML; FH validates its own header against per-type JSON Schemas | **Out of scope** — archive record format |
| SA.5 | Attribute naming aligned across INSDC nodes | FHR, FHP, FHGFF3 | — | INSDC-internal; FH's MIxS mapping (MAPPINGS.md) is the related work | **Out of scope** — INSDC coordination |
| SA-ver | Sample versioning | FHR, FHP, FHGFF3 | — | archive-side | **Out of scope** — archive versioning |

### Project Minimum Specification v1.0

| ID | INSDC requirement | FH type(s) | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- | --- | --- |
| P.1 | Metadata limited to ASCII | FHR, FHP, FHGFF3 | ✗ | YAML values are UTF-8 | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — as SA.1 |
| P.2 | Unique for a submitter | FHR, FHP, FHGFF3 | — | archive-side | **Out of scope** — archive policy |
| P.T1 / P.T2 | Description (20–4000 characters) and title (20–250 characters) of the research effort | FHR, FHP, FHGFF3 | — | FH names and documents a file, not a research effort | **Out of scope** — project description lives in the BioProject record |
| P.T3 | Submitter name | FHR, FHP, FHGFF3 | — | set by the submission portal; FH `metadataAuthor` names the header's authors | **Out of scope** — project record field |
| P.T4 | Project type (umbrella or primary) | FHR, FHP, FHGFF3 | — | no analogue | **Out of scope** — project record field |
| P.T5 / P.T6 | Contributor names and affiliations (optional) | FHR, FHP, FHGFF3 | — | FH author lists name the file's authors, not project contributors | **Out of scope** — project record field |
| P.T7 | Publication: PubMed ID or DOI (optional) | FHR, FHP, FHGFF3 | ◐ | `scholarlyArticle` takes a DOI only (`^10\.` pattern); a PubMed ID goes in `relatedLink` as a URL | **Partial** — DOI first-class, PubMed by URL |
| P.H | Project hierarchy rules | FHR, FHP, FHGFF3 | — | no analogue | **Out of scope** — project record structure |
| P-xref | Links to the project from experiment, sequence, assembly, validation reports and analysis | FHR, FHP, FHGFF3 | ◐ | `relatedLink` (BioProject record URL) | **Follow-up** [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) — as A.a |
| P-ver | Accession PRJ…; no versioning | FHR, FHP, FHGFF3 | — | accession assigned by INSDC; its record URL goes in `relatedLink` | **Out of scope** — archive accessioning |

### Package-Checklist Minimum Specification v1.0

| ID | INSDC requirement | FH type(s) | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- | --- | --- |
| PC.a | Checklist name and description refer to the partner or sample type | FHR, FHP, FHGFF3 | — | analogue: profile names and versions in `profiles/registry.yaml` (draft) | **Out of scope** — governs INSDC checklists |
| PC.b | Field definitions: name, description with value standard, type, validation rules, mandatory/optional, cardinality | FHR, FHP, FHGFF3 | — | analogue: per-type JSON Schema, LinkML models and TERMS.md define the same properties for header fields | **Out of scope** — governs INSDC checklists |
| PC.c | Mandatory in every checklist: NCBI taxID and name, collection date, geographic location | FHR, FHP, FHGFF3 | — | `taxon` only; date and location absent (SA.T3, SA.T4) | **Out of scope** — sample-checklist fields |
| PC.d | Checklist-specific mandatory fields | FHR, FHP, FHGFF3 | — | analogue: draft profiles | **Out of scope** — sample-checklist fields |
| PC-fed | Federation: checklist and field names aligned and synonymised across partners | FHR, FHP, FHGFF3 | ◐ | mapping tables: MIxS v7.0.1 projection (pinned, partial), JSON-LD/DCMI for every FHR 2.0 path | **Partial** — no formal FH to INSDC crosswalk; §4 lists the main correspondences |
| PC-std | Standards: spatiotemporal metadata, INSDC controlled vocabularies, feature-table mappable, INSDC missing-value reporting, ontologies, GSC alignment | FHR, FHP, FHGFF3 | ◐ | enums, NCBI taxonomy URIs, SO; missing values are absent, not tokens | **Partial** — FH has no missing-value tokens; supply INSDC tokens when filling a checklist |

### Experiment, Raw Reads and Compressed Reads v1.0

| ID | INSDC requirement | FH type(s) | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- | --- | --- |
| EX | Experiment object: links to one study, one sample and runs; STUDY_REF, SAMPLE_DESCRIPTOR, LIBRARY_STRATEGY/SOURCE/SELECTION/LAYOUT, PLATFORM, INSTRUMENT_MODEL | FHR, FHT (draft) | — | no experiment object; FHR `instrument`, `vitalStats.readTechnology`; FHT (draft) `libraryStrategy`, `strandedness`, `sequencingRuns` (SRR/ERR/DRR run accessions) | **Out of scope** — experiments are archive records; FHT (draft) run accessions point to them |
| RR | Raw read files: FASTQ/BAM/CRAM rules, quality scores, Run/Experiment/Study/Sample links, consent | — | — | no read-file header type exists or is proposed | **Out of scope** — no read-file header type |
| CR | Compressed read files: as RR without base qualities; QC flags; unique checksums | — | — | as RR | **Out of scope** — no read-file header type |

## 3. Summary

1. **Complementary layers.** INSDC Sequence v1.0 proposes a unified FASTA with per-sequence modifiers in the defline. FAIR-bioHeaders covers the file level (exact header syntax, versioned schemas, conformance vectors, validators) and leaves per-sequence modifiers to that separate layer.
2. **Links to INSDC records, not copies.** FH headers do not contain project, sample or experiment objects. Links to those records travel in `relatedLink`; `identifier` and `accessionID` identify the described data itself (MAPPINGS.md). `derivedFrom` is reserved for provenance between FAIR-bioHeaders files (FH to FH, by checksum), so FHR does not offer it for non-FH parents such as reads or archive records.
3. **Required is not always non-empty.** Required author lists may be empty and `taxon.uri` is optional in the released contracts. Non-empty authors are planned for the next major (GAP-1); whether `taxon.uri` should be required is a next-major decision ([#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189)).
4. **Profiles are the route for submission checks.** The draft profile machinery can require the optional fields an INSDC submission needs without changing the base contract ([#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190)). A profile pass still does not mean an INSDC node will accept a submission.
5. **Versioning differs by layer.** INSDC versions change with sequence content, not metadata. The FH checksum changes with any byte, including a header edit; the FH `version` is producer-assigned.
6. **Sequence content and archive policy are out of scope.** IUPAC, length, N and gap rules, per-sequence naming, and record lifecycle rules stay with INSDC tools and records.
7. **Annotation rules belong to the validator.** The INSDC Annotation rules gff3-validator lacks are tracked in [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27); none changes the FHGFF3 header.

### Federation summary

| Repository / type | Contract assessed | Rows | Open follow-ups |
| --- | --- | --- | --- |
| FAIR-bioHeaders-Specification: FHR | `2.0` (released) | Sequence, Assembly, Analysis, Sample, Project, Package-Checklist | [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190) profile; [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189) next major |
| FAIR-bioHeaders-Specification: FHP | `1.0` (released) | Sequence S8 and S-xref/S-ver, Annotation AN.c.iii/AN.d, Sample, Project, Package-Checklist | [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189) next major |
| FAIR-bioHeaders-Specification: FHGFF3 | `1.0` (released) | Annotation, Analysis, Sample, Project, Package-Checklist | [#191](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/191) tool tests; [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189) next major |
| FHT-Specification: FHT (draft) | `1.0` development contract at `0ceb6f4` (unreleased) | Sequence S1–S4, S11–S13, S-fmt; Sample SA.T1; Experiment | none; rows are re-checked when FHT is released |
| gff3-validator | catalogue `0.1.0-draft` at `c753f45` | Annotation | [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27) |

### Related follow-ups

- [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189): next major, whether `taxon` requires a taxonomy identifier (with GAP-1 non-empty authors).
- [#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190): draft INSDC submission-readiness profile for FHR.
- [#191](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/191): test FH headers with INSDC submission validators.
- [gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27): INSDC Annotation rules missing from the catalogue.
- [#170](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/170): BUSCO `lineageDataset` dotted versions. Raised by the same FHT design review; no INSDC requirement depends on it.
- [#139](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/139): structured voucher specimens, relevant to A.b and SA.T1 but reviewed on its own track.

## 4. Using FAIR-bioHeaders alongside an INSDC submission

A FAIR-bioHeaders header keeps metadata with a file you share or archive yourself. It does not replace an INSDC submission and does not make a file ready to deposit. To submit to GenBank, ENA or DDBJ, follow that node's instructions and validators, and use the header as a source of values.

1. **Register the records INSDC needs.** BioProject, BioSample, collection date, geographic location and the per-sequence details in S12 and A.l (molecule type, topology, chromosome names and levels) are not in FH headers. Supply them through the node's submission route.
2. **Submit files without the header unless the node accepts it.** INSDC submission tools have not been tested with `;~` or `#~` header blocks ([#191](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/191)), and strict FASTA readers reject them (TOOL_COMPATIBILITY.md). Use `bioheaders strip` to write a header-free copy, and compute the checksum the node asks for on the file you upload. The FH `checksum` is not that checksum.
3. **Copy values with care.** Common correspondences:

   | INSDC asks for | Take it from | Check |
   | --- | --- | --- |
   | Organism / taxID | `taxon.name`, `taxon.uri` | `taxon.uri` is optional; INSDC needs a species-rank or lower taxID |
   | Submitter, assembly authors | `metadataAuthor`, `assemblyAuthor` | INSDC may want the submitting centre, not the header's authors |
   | Assembly method and version | `assemblySoftware` `name` and `version` | optional in FHR; INSDC requires it |
   | Sequencing technology | `vitalStats.readTechnology`, `instrument` | optional in FHR |
   | Publication | `scholarlyArticle` (DOI) | PubMed IDs are in `relatedLink` URLs, if at all |
   | Analysis checksum | compute on the uploaded file | not the FH `checksum` |

   INSDC limits assembly metadata to 1000 characters and sample and project metadata to ASCII without HTML. FH does not enforce these limits, so check values before you copy them.
4. **Validate annotations with both tools.** An FHGFF3 header never makes features valid. Run gff3-validator for GFF3 rules and the node's own validator (for NCBI, `table2asn`) for INSDC rules, several of which gff3-validator does not yet check ([gff3-validator#27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27)).
5. **Record the result in the header afterwards.** When INSDC assigns accessions, add the BioProject and BioSample record URLs to `relatedLink` and the accession of the described assembly to `accessionID` or `identifier`. Then regenerate the header with `bioheaders combine`, which recomputes the checksum. This is a metadata-only change: the checksum changes, but you may keep `version`, as INSDC does for metadata-only edits. Files that cite the old checksum in `derivedFrom` need updating too.

Keep the sequence bytes the same in your FH-headed copy and in the submitted copy, apart from changes INSDC requires (for example U to T, S1). If you change the sequence, record the new file as a derivative with its own checksum.
