# INSDC minimum-specification coverage review — FHT draft fields (matrix v1)

**Pinned versions reviewed:**

- **INSDC side:** insdc/minimum-specifcations at commit `41f0dc4` (2026-07-06), all categories v1.0. Retrieved 2026-10-23.
- **FHT side:** FHT-Specification main @ `92f652d` (AGENTS.md commit); draft spec 005-rna-transcriptome-header/spec.md; legacy fht.json schema.

**Status:** provisional mapping, not curator approval or deposit validation.
The [October 24 research/design proposal](fht-field-decisions.md) proposes a
revision of spec 005; older FR-002/FR-003 references below identify the original
draft, not adopted requirements.

**Coverage key:** ✅ covered · ◐ partially covered · ✗ not covered · — not applicable to a file-bound header

## Table 1 — INSDC categories relevant to FHT transcriptome FASTA

| INSDC spec (all v1.0) | FH context | Relevance | Summary |
|---|---|---|---|
| [Sequence](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Sequence) | FHT (draft transcriptome FASTA header) | **Direct** | Per-record sequence metadata, molecule type, topology; file-level metadata aligns with the `;~` block |
| [Assembly](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Assembly) | FHT draft construction/provenance fields | **Direct** | Partial file-level overlap; method/version, submitter and deposit identity requirements are not automatically inherited or satisfied |
| [Annotations](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Annotations) | FHT ✗ (transcriptome FASTA has no features; annotation belongs to the GFF3 side) | — | Not applicable to a transcriptome header file. FHGFF3 records annotation-header provenance separately; this does not adopt an FHT parent-link rule |
| [Analysis](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Analysis) | FHT (`assemblyType`, `libraryStrategy`, platform → `instrument`) | **Partial** | Title/description/map to `transcriptome`+`documentation`; technology keywords align with `moleculeType`+`libraryStrategy`; STUDY_REF has no FH field |
| [Sample](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Sample) | FHT draft FR-003 `sample` (tissue/UBERON, stage, condition, strain) | **Partial** | No released type has a sample object yet; the draft AgBioData profile adds a community-only `sampleIdentifier` slot. FHT's optional `sample` struct fills part of this gap |
| [Project](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Project) | External project metadata | **Partial** | Actual BioProject URLs can be referenced in relatedLink; transcriptome self-identifiers must not be repurposed |
| [Package-Checklist](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Package-Checklist) | FHT (`schema`+`schemaVersion`) + draft FR-003 base fields (`libraryStrategy`, `strandedness`; not profile-only extensions) | **Conceptual analogue** | Community profiles (#51/#156) add constraints on top of base schema; never edit the contract directly. The AgBioData FHR profile model shows this boundary pattern |
| [Experiment](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Experiment) | FHT draft FR-003 (`libraryStrategy`, `strandedness`, `sequencingRuns`) | **Partial** | No experiment object exists in the family. The FHT optional fields serve as a *file-level proxy* for Experiment metadata, not an Experiment replacement |
| [Raw Reads](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Raw%20Reads) | FHT ✗ (FASTQ/BAM/CRAM header type not proposed) | N/A | No action |
| [Compressed Reads](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Compressed%20Reads) | FHT ✗ | N/A | Not applicable |

## Table 2 — Sequence Minimum Standards v1.0 mapped to FHT draft fields

| # | INSDC requirement | Cov. | Location in FHT | Disposition |
|---|---|---|---|---|
| **S1** | IUPAC sequence representation, including T rather than U | ✗ | Original spec 005 permits U and preserves exact bytes; the research proposal separates alphabet from biological molecule class | Keep deposit normalization explicit. Alphabet checking needs a content validator, not a metadata-schema enum |
| **S2** | DNA 5'→3' directionality | — | sequence-content rule; headers carry no directional metadata | N/A for a file-bound header; per-record defline metadata is future work (see S12) |
| **S3/S4** | Minimum sizes (100 nt; 1000 nt WGS top-level contigs) | — | FHT draft `vitalStats` reports transcript count, N50, mean length but enforces no minimums | Document boundary: INSDC sets deposit-level thresholds; FH headers report statistics without gatekeeping. A profile could add `minTranscriptLength` if curators require it |
| **S5** | ≤50% Ns in contigs/scaffolds | — | sequence-content rule | N/A for a file-bound header |
| **S6/S7** | Gap spans all-N; no leading/trailing Ns unless telomere/centromere/circular/contamination gap | — | sequence-content rule | N/A for a file-bound header |
| **S8** | Sequence directly determined or contracted by submitter | ◐ | `metadataAuthor` records header authors; `assemblyAuthor` belongs to the legacy FHT schema, not the shared core. Neither establishes submitter ownership or that reads were sequenced by the submitter. A `sourceType`-style assertion is not in the FHT draft. FHP uses `sourceType` (predicted/database/mixed) — FHT could benefit from the same | **Proposal:** borrow FHP's `sourceType` as an optional field for FHT to indicate whether transcripts are experimentally determined vs. in silico predicted |
| **S9** | Joined sequences in biological order with appropriate gaps | — | sequence-content rule; the file header cannot express per-record ordering | N/A for a file-bound header |
| **S10** | Ambiguity/contamination screening and proposed screening-report linkage | ◐ | Optional software and documentation can describe an actual screen; they do not establish results. FHR-specific assemblyProtocol is not imported automatically into FHT | Keep measured results/report references distinct from asserted methods; content validation remains external |
| **S11** | Semantic/syntactic FASTA validation; "full spec will need to be developed" | ◐ | Header-schema and checksum validation establish header validity but **not** sequence-content validity (IUPAC alphabet, gap rules, ≤50% Ns). FHT toolkit support is pending per README.md and FHT #9. FH provides file-bound structure (exact syntax R1–R11, versioned schemas, conformance vectors); INSDC Sequence v1.0 **already cites the 2024 FHR paper** (engagement opportunity) | Document boundary between header validation and sequence-content validation. This is an **engagement opportunity**: unified-FASTA per-record defline needs companion FH type or extension, not part of #6 scope |
| **S12** | Per-record sequence-specific metadata: molecule type, topology, chromosome number/location, viral segment, plasmid name; topology+completeness in deflines | ✗ | **No per-record mechanism exists in any FH header type.** Headers are file-bound (`;~`/`#~`), not per-sequence. The INSDC unified-FASTA proposal carries per-record JSON deflines — a different layer from FH's design | Document boundary. Per-record FASTA modifiers are future work only if INSDC's unified format materializes and curators request FH support. Not in #6 scope |
| **S13** | Technique keywords validated against biological molecule type | ◐ | Original FR-002 mixes material and molecule class. Assembly construction mode, library strategy and molecule type describe different axes | D1 proposes separation; no automatic TSA/keyword or per-record moltype equivalence |
| **S14** | Sequence name <51 chars, INSDC-legal characters, must not match another record's accession pattern | — | per-record naming; the file header carries no per-record name constraints. Adjacent: `assess related` compares names across files | N/A for a file-bound header |
| **S15** | Chromosome/linkage-group, plasmid and organelle naming rules | — | per-record naming | N/A for a file-bound header |
| **S-xref** | Cross-references: logical links out (publication) and within categories (reads, assembly, annotations, study, sample, validation reports) | ◐ | `scholarlyArticle` (DOI), `relatedLink`, `accessionID`, `derivedFrom` (FHT opts in per FR-003). **Correction:** the shared core reserves `identifier` for the transcriptome itself — project/study/sample accessions belong in `relatedLink`, not `identifier`. Study links use `bioproject:PRJ…`; sample links use `biosample:SAMN…` (SRS denotes an SRA Sample, not a study). Not yet implemented | Document convention separately for each category; no schema action now. Use `relatedLink` for project/study/sample URLs, keep `identifier` for the transcriptome's own accession |
| **S-ver** | Accessioning/versioning: `accession.version`; version increments on sequence change; **not** on metadata-only change | ◐ | FH uses free-text required `version` + required exact-byte SHA-512/256 `checksum`. An FH metadata edit bumps the checksum (and arguably warrants a version bump) — INSDC's "metadata-only = no version bump" is a different layer convention. Document divergence | **Document** in spec 005; not a gap to close (different layers, different identity model). A submission-mapping note should clarify this for curators |

## Table 3 — Assembly Minimum Specification v1.0 mapped to FHT draft fields

| # | INSDC requirement | Cov. | Location in FHT | Disposition |
|---|---|---|---|---|
| **A.a** | Link to a public BioProject | ◐ | No dedicated `project` field. Use `relatedLink` for the project URL; `identifier` describes the transcriptome itself | Document the convention; a dedicated `project` slot would be a schema addition — only if curators ask for it explicitly |
| **A.b** | Link to a public BioSample | ◐ | FHT draft FR-003 optional `sample` struct (tissue/UBERON, stage, condition, strain). The draft AgBioData FHR profile is not an adopted FHT mechanism. Retain the actual BioSample URL in `relatedLink`; no released FHT sample contract exists | Document; the profile route is the correct mechanism — never edit the base contract for community-specific requirements |
| **A.c** | Submitter/owner/consortium/center identity | ◐ | Spec 005 FR-002/FR-003 do not add `assemblyAuthor`; only the legacy fht.json had it. The shared core imports `metadataAuthor` (with optional `name`, `uri`, `nameType`), and **does not include** `assemblyAuthor`. These are distinct contracts and must not be combined to imply required submitter identity. FR-002/FR-003 leave submitter/assembler identity requirements open for #6 | Document which fields are draft-proposed vs legacy; leave requiredness decisions to #6 curator consultation |
| **A.d** | BioSample associated with a taxID at species rank or below; binomial, not environmental, for clone/isolate assemblies | ◐ | `taxon` required: URI pattern-pinned to `https://identifiers.org/taxonomy:<NCBI taxid>`. **Rank is not schema-checkable** — same limitation as FHR/FHP. Taxonomy resolution is online (assess `--online` territory) | Document the limitation. No schema action — rank checking requires external resolution. Not a blocker for transcriptome use |
| **A.e** | Moltypes appropriate for a genome (genomic DNA/RNA, viral cRNA, …) | ◐ | The original FR-002 molecule enum remains unadopted and mixes biological classes with library material; file-wide assertions cannot establish per-record moltype validity | Review D1; mapping is provisional and conditional |
| **A.f/A.g** | All linked sequences live; withdrawn sequences withdraw the assembly | — | repository lifecycle policy, outside file-bound header scope. Adjacent family tools distinguish file checksum checks from parent-link verification; neither implements repository withdrawal policy | N/A for a file-bound header |
| **A.h** | Common BioSample and taxonomic source across an assembly | ◐ | A shared taxon object and draft sample context are assertions, not evidence that every sequence has the same biological origin | Keep actual sample associations externally and review pooled-source cases; do not infer uniform origin |
| **A.i** | All sequences from the same INSDC provider | — | N/A for a file-bound header | Not applicable |
| **A.j** | Metadata: assembly method and version/dates (e.g., "Canu v. 1.2.3"); sequencing technologies | ◐ | Mixes optional draft fields (`assemblySoftware`, `sequencingRuns` from FR-003) with legacy-only `instrument` and FHR's `assemblyProtocol`. The shared core does not include these — they are inherited from the FHT legacy fht.json only. `assemblyProtocol` is not a shared-core field; a type-specific field is not inherited automatically. Shared `Software` already has a distinct `version` member | Document which values will be required at submission time; distinguish draft-proposed optional fields from established required ones |
| **A.k** | Metadata fields ≤1000 characters | ✗ | FH sets no length limits (R11 escaping only). Relevant only when exporting FH values into INSDC submissions | Document in submission-mapping guidance; not a schema change. If curators need enforcement, a profile can add it |
| **A.l** | Unique sequence names; chromosome/plasmid/organelle names declared; per-sequence type and level | ✗ | per-record assembly structure; the NCBI assembly-report/AGP layer. FHT `vitalStats` carries aggregates only (transcriptCount, N50, meanLength) | Document boundary; no header action. The transcriptome header is not an assembly report |
| **A-ver** | Versioning: increment on sequence update/addition/removal/level change; **not** on metadata-only change | ◐ | Same S-ver point above (see Table 2). Different identity model — FH metadata edit recomputes checksum and may warrant a version bump | Document divergence; not a gap to close |

## Table 4 — Experiment Minimum Specification v1.0 mapped to FHT draft fields

| # | INSDC requirement | Cov. | Location in FHT | Disposition |
|---|---|---|---|---|
| **E-lay** | Experiment library strategy | ◐ | Draft libraryStrategy is optional. ENA uses distinct strategy/source/selection fields; RNA-Seq is a strategy, while PolyA is a selection | Use supplied source terms and D1; no frozen whole-archive enum or inferred strategy |
| **E-sou** | Library source (transcriptomic, genomic, cDNA, …) | ◐ | Overlaps with `moleculeType` (FR-002). The 2026-11-16 Molik response adds file-wide biological class `mixed` for known heterogeneity; this does not encode library preparation material or per-record INSDC evidence | Keep this mapping partial. Preserve source evidence; neither mixed nor a uniform file-wide enum supplies per-record library-source provenance. |
| **E-sel** | Library selection (poly-A, random, oligo-dT, …) | ✗ | Not in FHT draft FR-003. Could be added as part of a libraryProfile struct or a community profile | Document as a potential future addition; only if curators request it explicitly |
| **E-str** | Experiment strandedness/protocol | ◐ | ENA guidance describes stranded status, and Trinity defines explicit read orientation conventions. The previous firststrand/secondstrand claim is not an ENA enum | D3 proposes an explicit FHT read/read-1 normalization for review; unknown is omission |
| **E-pla** | Platform (ILLUMINA, ION Torrent, …) | ◐ | FHT optional `instrument` carries platform identifiers (legacy fht.json example: "Sequel IIe", "Nanopore"). `sequencingRuns` carries SRA accessions for run-level detail | Accept as-is; a controlled vocabulary would be a schema addition — only if curators request it |
| **E-stu** | STUDY_REF (link to study) | ✗ | No shared study field. Use `relatedLink` for a study/project URL; do not repurpose a transcriptome self-identifier | Document convention; no schema action now |

## Table 5 — Sample Minimum Specification v1.0 mapped to FHT draft fields

| # | INSDC requirement | Cov. | Location in FHT | Disposition |
|---|---|---|---|---|
| **SM-alias** | Sample Alias (unique across submission) | ◐ | FHT FR-003 `sample` struct includes tissue/UBERON, stage, condition, strain fields. No dedicated sampleAlias field | Document; a community profile can add this if curators need it |
| **SM-org** | Organism name (NCBI Taxonomy) | ◐ | FHT inherits `taxon` from the core — required in every type (see A.d). Same rank limitation as all types | Document assertion/verification boundary |
| **SM-geo** | Geographic location | ✗ | Absent from every FH type. Per this ticket's guidance: keep external (BioSample/MIxS layer) | Document as N/A; geographic metadata belongs in the BioSample layer, not a file-bound header |
| **SM-date** | Collection date | ✗ | FHT has `dateCreated` (assembly creation date). The spec already warns this is **not** a sample collection date (see MAPPINGS.md) | Document the distinction explicitly; add a note in the draft decision record that `dateCreated` ≠ collectionDate |
| **SM-cls** | Checklist/Package name validated against a version | ✗ | `schema` + `schemaVersion` identify the header contract, not an INSDC sample checklist and its version. The shared profile proposal selects profiles out of band, versions them separately, and currently does not support FHT | Mark as missing; retain checklist identity and validation in the external sample-submission metadata |
| **SM-sub** | Submitter name and affiliation | ◐ | `metadataAuthor` has the same limitations as A.c: `nameType: Organizational` classifies an author, not affiliation; `Author.uri` accepts ORCID rather than organization identifiers. A header author is not necessarily the submitter. The shared core does not include a dedicated submitter-identity field | Mark partial; retain explicit submitter identity and affiliation in external submission metadata |

## Key findings and recommendations

1. This is a provisional draft-field mapping. Optional metadata and proposed
   profiles do not prove INSDC submission completeness or resolve #157.
2. The [research/decision proposal](fht-field-decisions.md) separates biological
   molecule identity, library strategy/source/selection and T/U representation.
   It proposes optional moleculeType with explicitly reviewed meanings.
3. Sequence preservation and deposit normalization are separate operations. The
   original draft permits U; actual INSDC/TSA submission checks remain external.
   Do not infer biological class or change file bytes from an alphabet label.
4. Project/sample/study URLs belong in relatedLink; identifier and accessionID
   identify the transcriptome itself. Run accessions identify runs, not samples.
5. Shared Software already has version. Keep software versions out of ad hoc
   option strings when structured provenance is supplied. Do not conflate legacy
   assemblyAuthor, header author, submitter and affiliation.
6. Per-record sequence, source, checklist and repository-lifecycle requirements
   are not satisfied by a file header. External metadata and content validation
   remain necessary. A profile cannot make unsupported fields or validators exist.

The [mapping strategy](insdc-fht-mapping-strategy.md) records these boundaries.
The initial development design is approved by David for adoption on PR #20 merge. No schema
bytes, field values, curator approval, toolkit support or new profile is established
by this coverage review. PR #20 closes #6's initial design decision on merge; #7 owns implementation.
