# INSDC Minimum-Specification Coverage Review

This document records the extent to which the FAIR-bioHeaders specifications cover the requirements of the International Nucleotide Sequence Database Collaboration (INSDC) minimum specifications. It is a coverage assessment with recorded per-requirement dispositions ([FAIR-bioHeaders-Specification#157](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/157)); differences in scope, purpose and representation are documented rather than resolved by reproducing the INSDC specifications wholesale. A ◐/✗ entry records the current state of coverage, not a committed or adopted change.

**Pinned Versions Reviewed:**
- **INSDC side**: [insdc/minimum-specifcations](https://github.com/insdc/minimum-specifcations) at commit `41f0dc4` (2026-07-06). All categories are at v1.0.
- **FAIR-bioHeaders side**:
    - FHR `schemaVersion "2.0"`, FHP `"1.0"`, FHGFF3 `"1.0"`.
    - FHT: Reviewed against the draft [specs/005-rna-transcriptome-header @ `9a87e5c`](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/9a87e5cfe0ce3e024508ff8fdb58e6fe9042dffe/specs/005-rna-transcriptome-header/spec.md). Spec 005 is an evolving draft; the revision above is the one assessed, and it was identical to `main` when the assessment was written.
    - [gff3-validator rule catalogue @ `c753f45`](https://github.com/FAIR-bioHeaders/gff3-validator/blob/c753f451d28b80b5f84c042e0f0486c3b1049adf/gff3_validator/catalogue.yaml) (`catalogue_version 0.1.0-draft`, dated 2026-10-08; DRAFT for Sequence Ontology review).

**Coverage Key:**
✅ covered · ◐ partially covered · ✗ not covered · — not applicable (out of scope by design)

## 1. Context Triage: FAIR-bioHeaders ↔ INSDC Categories

| INSDC spec (all v1.0) | FH context | Relevance | Summary |
| --- | --- | --- | --- |
| [Sequence](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Sequence) | FHR (genome FASTA); FHT (transcriptome FASTA, draft) | Direct | File-level metadata, FASTA syntax standardization and versioning overlap heavily; per-record source modifiers are outside FH's file-bound scope |
| [Assembly](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Assembly) | FHR | Direct | FHR is the file-bound description of an assembled sequence set; INSDC Assembly is the database-level object for the same set |
| [Annotations](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Annotations) | FHGFF3 header + gff3-validator | Direct | Header carries provenance; feature-level rules belong to the validator, not the header |
| [Analysis](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Analysis) | FHR on GFA/FASTA (toolkit formats), `derivedFrom` (FHP/FHGFF3) | Partial | Mandatory checksum/type/title philosophy aligns closely; STUDY_REF has no FH field; BASE_MODIFICATION TSV/CSV and GENOME_MAP formats are unsupported |
| [Sample](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Sample) | `voucherSpecimen`, `taxon`, `relatedLink` (sample record URLs), profiles machinery (draft) | Partial | No released type has a sample object; the draft AgBioData profile demonstrates the community-slot route |
| [Project](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Project) | `relatedLink` (project record URLs), `scholarlyArticle`, `funding` | Partial | No project field in any released type; BioProject links are possible as `relatedLink` URLs only |
| [Package-Checklist](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Package-Checklist) | `schema`+`schemaVersion`, TERMS.md, `profiles/registry.yaml` (draft) | Conceptual analogue | FH community profiles are the direct counterpart: layered requirements with their own versioning, never relaxing the base contract |
| [Experiment](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Experiment) | FHT draft `libraryStrategy`/`strandedness`; FHR `instrument`, `vitalStats.readTechnology` | Marginal | The family has no experiment object |
| [Raw Reads](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Raw%20Reads) | — | N/A | No FASTQ/BAM/CRAM header type exists or is proposed |
| [Compressed Reads](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Compressed%20Reads) | — | N/A | Same |

## 2. Coverage Matrix

### Sequence Minimum Standards v1.0

| # | INSDC requirement | Type(s) | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- | --- | --- |
| S1 | IUPAC nucleotide characters only, no dashes; **T instead of U regardless of molecule type** | FHR/FHT | — | Headers never validate sequence bytes; no FASTA content validator in the family. specs/005 FR-006 deliberately **allows U** in RNA FASTA ("alphabet-independent") | Document the divergence (FH permits what INSDC would rewrite); no schema action |
| S2 | DNA 5'→3' | FHR/FHT | — | sequence-content rule | No action |
| S3/S4 | Minimum sizes (100 nt; 1000 nt for WGS top-level contigs) | FHR/FHT | — | FHT draft `vitalStats` (counts, N50, mean length) reports statistics, enforces no minima | Document boundary |
| S5 | ≤50% Ns | FHR/FHT | — | sequence-content rule | No action |
| S6/S7 | Gap spans all-N; no leading/trailing Ns unless telomere/centromere/circular/contamination gap | FHR | ✗ | no mechanism; needs a sequence+annotation cross-check | Candidate future validator work; no header action |
| S8 | Sequence directly determined or contracted by submitter | FHR/FHP | ◐ | `metadataAuthor` + `assemblyAuthor` required (FHR); FHP `sourceType` (predicted/database/mixed) | No action — an acceptance-policy assertion, not file metadata |
| S9 | Joined sequences in biological order with appropriate gaps | FHR | — | sequence-content rule | No action |
| S10 | No vector/linker unless labelled synthetic; contamination screening to taxonomic order; **proposal for a screening checksum report included in submission** | FHR | ◐ | `assemblySoftware` and `assemblyProtocol` can name screening runs; no structured screening-result evidence field | Document; a structured screening-evidence field would be a schema addition — only propose if curators ask. |
| S11 | Semantic/syntactic FASTA validation; no single standard FASTA with source modifiers exists | FHR | ◐ | FH provides the file-level piece: exact header syntax, versioned JSON Schema contracts, conformance vectors, `bioheaders verify`, `assess sniff/conventions`. | No FH gap; engagement opportunity. |
| S12 | Per-record sequence-specific metadata must travel with the sequence | FHR/FHT | ✗ | FH headers are file-bound; no per-record modifier mechanism. | Document boundary. |
| S13 | Technique keywords (HTGS/STS/GSS/WGS, TSA) validated against molecule type | FHR ✗ / FHT ◐ | ◐ | FHR: no keyword field. FHT draft FR-002: `assemblyType` + `moleculeType` give the file-level analogue | Feed into FHT curator consultation. |
| S14 | Sequence name <51 chars, INSDC-legal characters, must not match another record's accession pattern | FHR | — | per-record naming, not the file header's role. | No action. |
| S15 | Chromosome/linkage-group, plasmid and organelle naming rules | FHR | — | per-record naming | No action |
| S-xref | Cross-references: logical links out (publication) and within categories | all | ◐ | `scholarlyArticle`, `relatedLink`, `identifier`, `derivedFrom`+`relationship` (FHP/FHGFF3 only), `genomeReference` (FHGFF3). | Document conventions. |
| S-ver | Accessioning/versioning: `accession.version` | all | ◐ | Different mechanism: required free-text `version` + required exact-byte SHA-512/256 `checksum`. | Document the divergence. |

### Assembly Minimum Specification v1.0

| # | INSDC requirement | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- |
| A.a | Link to a public BioProject | ◐ | no field; the BioProject record URL belongs in `relatedLink` | Document the convention. |
| A.b | Link to a public BioSample | ◐ | no field; `voucherSpecimen` is free-text; structured vouchers (#139/#140) are separate. | Profile route; document. |
| A.c | Submitter/owner/consortium/center identity | ✅ | `metadataAuthor`, `assemblyAuthor` (required in FHR) | none |
| A.d | BioSample associated with a taxID at species rank or below | ◐ | `taxon` required; rank is not schema-checkable | Document the limitation. |
| A.e | moltypes appropriate for a genome | ◐ | implicit in the type (FHR subject `genome`); FHT draft has one | Document |
| A.f/A.g | All linked sequences live; withdrawn sequences withdraw the assembly | — | repository lifecycle policy | No action |
| A.h | All sequences from the same BioSample and taxID | ◐ | structural: `taxon` is a single required scalar | Document |
| A.i | All sequences from the same INSDC provider | — | — | No action |
| A.j | Metadata: assembly method and version/dates; sequencing technologies | ✅ | `assemblySoftware`, `assemblyProtocol`, `dateCreated`, `vitalStats.readTechnology`, `instrument` | none |
| A.k | Metadata fields ≤1000 characters | ✗ | FH sets no length limits | Document in submission-mapping guidance |
| A.l | Unique sequence names; chromosome/plasmid/organelle names declared; per-sequence type and level | ✗ | per-record assembly structure | Document boundary. |
| A-ver | Versioning: increment on sequence update... not on metadata-only change | ◐ | as S-ver: checksum re-computes on any byte change | Document divergence |

### Annotation Minimum Specification v1.0

*Boundary note: FHGFF3 headers carry provenance only; feature-level rules live in gff3-validator. Catalogue rules cited below are implemented at the pinned catalogue revision unless marked (planned); STR-012 and STR-013 are planned.*

| # | INSDC requirement | Cov. | Location | Disposition |
| --- | --- | --- | --- |
| AN.a | Conform to the INSDC GFF3 specification | ◐ | FHGFF3 header lines are ordinary GFF3; validator checks GFF3 1.26 syntax against a pinned SO release. | Compatibility test + TOOL_COMPATIBILITY.md entry. |
| AN.b.iii | Feature locations: start/end/strand present; within sequence length... | ◐ | SYN-013…015, STR-002, STR-008/011 + BIO-001/002/003. | gff3-validator catalogue cross-check. |
| AN.b.iv | Overlaps: feature intervals must not overlap... | ✗ | no implemented rule; STR-012 (planned, info-level) flags a child extending beyond its parent and STR-013 (planned) checks parent/child seqid agreement — neither checks interval overlap | Validator candidate rule |
| AN.b.v | Lengths: complete CDS ≥30 aa; tRNA 50–150 bp; introns ≥10 bp | ✗ | BIO-009 checks multiple-of-three only | Validator candidate rules |
| AN.b.vi | Coding regions: translation matches /translation... | ◐ | BIO-004, BIO-005, BIO-006/007, BIO-008, BIO-010. | Validator candidates. |
| AN.b.vii | parent:child via `Parent=` (GFF3) / `transcript_id` (FT) | ◐ | STR-003…007, ATT-004/006. | Validator cross-check |
| AN.b.viii | Feature/moltype prohibitions | — | requires record-level molecule-type context | Document N/A |
| AN.b.ix | locus_tag: mandatory in genome submissions | ✗ | no `locus_tag` rule in the catalogue | Validator candidate rule. |
| AN.c.i/c.ii | Prokaryote partiality abutting gaps/ends | ✗ | not in catalogue | Validator cross-check |
| AN.c.iii | Translations conform to the INSDC translation table | ◐ | validator `--translation-table` (explicit); FHP `geneticCode` records the NCBI table ID. | Document; FHGFF3 geneticCode would be a schema addition. |
| AN.d | Sequence-dependent: aa NH3→COOH... | ◐ | BIO-008 (internal stops, with --genome). | Document boundary. |
| AN-xref | Mandatory links within categories... | ◐ | FHGFF3 `genomeReference` = the annotation→genome link; `soVersion` pins SO. | Document. |
| AN-std | Standards: INSDC Feature Table; SO mappings | ◐ | validator pins an SO release. | Covered on FH side. |

### Analysis Minimum Specification v1.0

| INSDC requirement | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- |
| Mandatory TITLE, DESCRIPTION | ◐ | subject slots + optional `documentation` | Document the name correspondence |
| Mandatory ANALYSIS_TYPE | ◐ | type marker + per-type schema URL | Document; new file family = new type proposal |
| Mandatory STUDY_REF | ✗ | same gap as A.a (no project field) | Document convention |
| Mandatory filename, filetype | ◐/— | file-bound by design | No action |
| Mandatory checksum | ✅ | SHA-512/256 over exact file bytes | none |
| Compressed files must be decompressed | ◐ | toolkit streams gzip/BGZF transparently | Document as an exchange-policy divergence |
| Accepted file types per analysis type | ◐ | FASTA, GFA, GFF3 supported | Document |
| Accessioned, not versioned | ✗ | FH requires `version` | Document divergence |

### Sample Minimum Specification v1.0

| INSDC requirement | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- |
| Sample Alias | ◐ | no released field; the BioSample record URL belongs in `relatedLink`; draft AgBioData profile adds `sampleIdentifier` | Profile/documentation route. |
| Organism name (NCBI Taxonomy) | ◐ | `taxon` required, identifiers.org/taxonomy URI pinned | Document limitation. |
| Geographic location | ✗ | absent from every type | Keep external; document. |
| Collection date | ✗ | absent | Keep external; document. |
| Checklist/Package name | ◐ | mechanism analogue: required `schema` + `schemaVersion` | Document the analogy |
| Package-defined mandatory attributes | ◐ | profiles can make optional fields required | Await #51/#56 review. |
| Submitter name and affiliation | ◐ | `metadataAuthor` name/uri/nameType | Document |
| No HTML markup in metadata | ✗ | YAML string values may contain HTML; R11 escapes only the transport characters `>`/`@` (a raw one stays valid with a warning), so a `documentation` value with embedded HTML passes the released contract | Not covered by the contract; a submission-side check (profile constraint or assess convention) is the route |
| Syntactic validation against schema | ✅ | per-type JSON Schema contracts + `bioheaders verify` | none |

### Project Minimum Specification v1.0

| INSDC requirement | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- |
| Title, Description | ◐ | subject-name slot + `documentation` | Document |
| Submitter name | ✅ | `metadataAuthor` | none |
| Project type | — | no analogue | N/A |
| Contributor names/affiliations | ◐ | author lists | Document |
| Publication (PubMed ID or DOI) | ◐ | `scholarlyArticle` accepts a DOI only (`^10\.` pattern); a bare PubMed ID has no released slot — record the PubMed URL in `relatedLink` | Document the limitation |
| Accessioning PRJ…, no versioning | ◐ | the PRJ… record URL belongs in `relatedLink` (`bioproject:` record) | Document convention |

### Package-Checklist Minimum Specification v1.0

| INSDC requirement | Cov. | Location in FH | Disposition |
| --- | --- | --- | --- |
| Field definitions | ✅ | per-type JSON Schema + LinkML models + TERMS.md vocabulary | none |
| Mandatory: NCBI taxID, collection date, geo location | ◐/✗ | `taxon` ✅; collection date and geo location ✗ | Document; keep in the BioSample/MIxS layer |
| Field-name harmonisation | ◐ | mappings machinery; draft `assembly-dcmi.yml`/`profile-status.yml` | Candidate #56 follow-up |
| Controlled vocabularies | ◐ | enums; missing-value convention is absence | Document |

## 3. Summary and Findings

1. **Complementary Layers**: INSDC's Sequence spec proposes a unified FASTA with per-record JSON deflines. FAIR-bioHeaders addresses the file-level half of this gap (exact syntax, versioned schemas, conformance vectors, validators) while leaving per-record modifiers as a separate layer.
2. **Structural Gaps**: Identified a gap regarding the omission of `derivedFrom` in released FHR (unlike FHP/FHGFF3). **Decision:** `derivedFrom` is reserved for provenance between FAIR-bioHeader records (FH to FH, the inner circle of trust). Links to non-FH parents (e.g., raw reads, external databases) are handled via `relatedLink` by design, as FH serves as the primary record for the family.
3. **Profiles as the Solution**: The draft profiles machinery is the designed route for INSDC-style sample/checklist requirements, allowing layered requirements without modifying base contracts.
4. **Versioning Divergence**: INSDC bumps versions on sequence change, not metadata. FH's checksum-based versioning treats any byte change as a new state. These are different layers of identity.
5. **Sequence Content**: Requirements regarding IUPAC characters, N-rules, and gaps are out of scope for FH headers, as they do not validate sequence bytes.
