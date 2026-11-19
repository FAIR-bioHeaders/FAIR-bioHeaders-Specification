# FHT field design: research and proposed decisions

Status: **initial development design approved by David; recorded for adoption on
merge of PR #20**, October 24, 2026, for
[issue #6](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/6).
This is a schema-contract design decision, not a released schema. Public sources
support the design; they do not constitute curator endorsement.

## Maintainer decision and closure boundary

David explicitly approved the required minimum, construction cases, optional
moleculeType, strand convention, numerical/unknown-value rules and proceeding
with the existing meeting feedback plus research. Further consultation is welcome
but is not a prerequisite for completing this initial design issue. David stated
that he expects Adam to agree; no separate direct approval from Adam is attributed
by this record. The repository's joint schema/release authority remains unchanged.

On merge, PR #20 completes #6's design/consultation disposition. The definitions
below and the revised spec/design tables are the implementation baseline, not
claims of finished schema generation, toolkit support, INSDC completeness or release.
Exact sample serialization and parent-link constraints are explicitly assigned
to #7 for subsequent reviewed contract work. The independent #157 gate remains.

## Baseline and evidence

The comparison uses FHT main `cb28da0c69df4b5c6a59e00e766786a263c55f86`
and shared-specification main `980029e5886a1a56a2d2545bfe59c7107539d38d`:
`schemas/core.yaml`, `schemas/shared.yaml` and draft spec 005. The legacy
`fht.json` remains unchanged. The INSDC minimum-specification assessment retains
its separate `41f0dc4` / category v1.0 baseline; it is not a deposit validator.

| Source | Evidence relevant to this design |
| --- | --- |
| [INSDC Feature Table Definition 11.4, April 2026, `/mol_type`](https://www.insdc.org/submitting-standards/feature-table/) | Biological molecule identity is distinct from a preparation method; the vocabulary distinguishes mRNA, rRNA, tRNA and transcribed RNA. Its qualifiers apply per source feature/record. |
| [ENA RNA-Seq metadata guidance](https://ena-docs.readthedocs.io/en/latest/exp_01.html) | Library strategy, source and selection are separate experiment concepts; strandedness is additional experiment metadata. |
| [ENA experiment XSD, pinned revision](https://github.com/enasequence/webin-xml/blob/21aab62650e2f918b79d610c22d0d2b1b3b1e050/src/main/resources/uk/ac/ebi/ena/sra/schema/SRA.experiment.xsd) | `RNA-Seq` is a strategy, `TRANSCRIPTOMIC` a source, and `PolyA` a selection. Their values cannot substitute for one another. |
| [Trinity genome-guided assembly](https://github.com/trinityrnaseq/trinityrnaseq/wiki/Genome-Guided-Trinity-Transcriptome-Assembly) | A reference can partition aligned reads while reconstructed transcript bases come from those reads. Reference use does not establish sequence extraction from the reference. |
| [Trinity strand conventions](https://github.com/trinityrnaseq/trinityrnaseq/wiki/Running-Trinity) | RF/FR describe paired-read orientation; R/F describe single reads. Any compact strand vocabulary needs an explicit convention. |
| [gffread transcript extraction](https://www.ccb.jhu.edu/software/stringtie/gff.shtml) | Transcript sequences can be extracted using transcript coordinates and a corresponding genome FASTA. This supports a distinct annotation-extraction case. |
| [NCBI TSA requirements](https://www.ncbi.nlm.nih.gov/genbank/tsa/) | TSA requires primary reads and associated run, project and sample accessions, and imposes additional sequence/submission conditions. An FHT header is not a TSA eligibility certificate. |
| [NCBI SRA object model](https://www.ncbi.nlm.nih.gov/sra/docs/submitmeta/) | Runs, experiments, samples and studies have different accession classes. An SRS accession is not an SRR run. |
| [NCBI genetic-code documentation](https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi) | GenBank can display mRNA using the DNA alphabet. T/U representation alone cannot identify biological molecule class. |
| [BUSCO user guide, v6.1.0 when accessed](https://busco.ezlab.org/busco_userguide) | Transcriptome completeness depends on biological context, isoforms, tissue and stage. Report the actual run and lineage rather than a universal pass threshold. |

These online pages were accessed October 24, 2026. Mutable documentation is
identified by access date; no unverified version or archived snapshot is implied.
The ENA XSD pin was checked through GitHub and its three vocabulary lists parsed
as XML. This proposal uses short factual summaries, not copied source text.

## Molik draft responses — 2026-11-16

[The recorded responses and clarifications](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8#issuecomment-6928571815)
supersede D1's initial omission of known heterogeneous sets: `mixed` is the fifth,
case-sensitive `moleculeType` value. It denotes producer-supported biological RNA
heterogeneity, not unknown composition, a library preparation, or the alphabet.
This is an additive enum change in the unreleased draft `1.0`, not publication or
joint curator adoption. Four-value readers, including the pinned 0.11.0 draft
reader, reject this newly valid value and need an explicit future consumer update.
The three construction values, nine required fields and existing taxon members
are retained. The ordered `sample` array remains; BioSample URLs belong in
`relatedLink`, following FHR. Describe protocol/kit information in `documentation`
and put actual protocol URLs in `relatedLink`; no protocol/kit field is added,
and `libraryStrategy` is not overloaded. Current statistics, parent behavior and
field names remain. No new required URI, sample deprecation or mixed construction
value is authorized. Publication and joint review remain separate gates.

## D1: distinguish molecule, library and alphabet

The following is the original recommendation; the dated clarification above
supersedes its heterogeneous-set omission.

**Recommendation:** change draft FR-002's required `moleculeType` to optional,
file-wide biological molecule identity. Do not adopt the current mixed enum
`mRNA | total RNA | cDNA | ncRNA`. This is a requiredness/meaning/vocabulary
change to the proposed contract, not a spelling correction.

For a first implementation, propose `mRNA`, `rRNA`, `tRNA` and `transcribed RNA`
as a deliberately restricted INSDC-aligned vocabulary. Each assertion must apply
to the whole described set and be supported by its producer; matching the string
does not establish INSDC per-record compliance. Omit it for unknown or heterogeneous
sets without one justified classification. Do not automatically map `ncRNA` to
`transcribed RNA`, infer mRNA from RNA-Seq, or infer cDNA from T in a FASTA.
Synthetic/viral/other molecule categories need a separately reviewed extension if
this initial scope cannot describe them accurately.

`total RNA` describes input material; `cDNA` describes a molecular preparation
context; neither identifies a uniform biological transcript class. Preserve such
information in linked experiment metadata or `documentation`, rather than coercing
it into a different class. Do not add new library-source/selection slots incidentally.

Keep `libraryStrategy` optional, a single string carrying the producer's ENA
strategy term when one strategy applies. A suggested value such as `RNA-Seq` is
not an inference rule or a frozen copy of ENA's full evolving enum. Multiple
experiments with different strategies belong in linked run/experiment records;
omit a misleading file-wide scalar. Source and selection cannot be recovered
from strategy alone. These file-wide choices are FHT design recommendations,
not requirements imposed by ENA.

## D2: define the construction cases without inventing parents

Retain required `assemblyType`, using the existing proposed spelling. It describes
how transcript sequences/models were constructed, not their quality or deposit
class. The three definitions below are proposed FHT distinctions informed by the
tools; external tools do not establish an FH relationship vocabulary.

| Value | Proposed meaning and minimal use case | Parent/source treatment |
| --- | --- | --- |
| `de novo` | Reconstruct transcripts from reads without using a reference genome to construct/group the assembly; a reference-free Trinity assembly is the motivating case. Later reference alignment used only for QC does not reclassify it. | No reference genome parent is required. Report known runs when available; do not fabricate a genome relationship. |
| `genome-guided` | Use read evidence plus a reference to construct transcript models or group the reads used for reconstruction. Bases may come from reads or a subsequent reference extraction. | Document reference use and source. Do not equate grouping/alignment guidance with bases extracted from the genome. |
| `annotation-derived` | Extract transcripts from an existing annotation's coordinates and its corresponding genome, without assembling new models from read evidence in this production step; gffread extraction motivates the case. | Identify both actual annotation and genome sources when known. Absence of reads is not evidence of a missing assembly. |

A workflow that assembles new read-supported models and then extracts their
sequences remains genome-guided; the final extraction command alone does not
determine the category. Composite histories that do not fit one class require a
documented decision before claiming conformance: do not guess, choose a tool's
default, or add a `mixed`/`unknown` enum here.

Keep `derivedFrom` optional. It represents actual family-file relationships;
source URLs/accessions can be supplied via `relatedLink` and `documentation`
without claiming byte verification. There is no adopted raw-read family type,
so an SRR run is not a `derivedFrom` family-file checksum link. The shared
relationship vocabulary is provisional: #7 must review allowed FHT parent types,
relationship meanings and checksum/accession requirements. In particular,
`transcribedFrom` must not be asserted solely because a genome guided Trinity.
No new relationship or mandatory genome checksum is adopted by this proposal.

## D3: strand, optional context and numerical reporting

Keep `sample`, tissue, condition, stage, strain, runs, library strategy,
strandedness, software, statistics and BUSCO optional in the base design.
Submission systems can require more; their requirements do not silently become
base-header requirements. Do not infer sample provenance or experimental methods
from an annotation-derived FASTA. Pooled material must retain its actual provenance
externally or in documentation rather than being collapsed to an invented sample.

Propose optional scalar `strandedness` with values `unstranded`, `forward`,
`reverse`. Here forward means the single read or read 1 is sense relative to
the originating transcript; reverse means antisense. In the documented Trinity
convention, F/FR map to forward and R/RF to reverse. This is our proposed FHT
normalization, **not** an ENA enum. It describes the library, not genomic plus/minus
orientation or whether exported transcripts are reverse-complemented. Unknown
is omission, never an automatic `unstranded`. Preserve the source protocol in
documentation; mixed protocols cannot be summarized by one scalar.

Reuse shared `Software` for optional ordered `assemblySoftware` entries:
name required when an entry is present, optional URI, **existing `version`**,
and ordered `commandLineOption` strings. Do not hide a known software version in
its options. Extraction software is applicable too; record the real process.

For optional `vitalStats`, propose retaining the legacy names `totalTranscripts`
(integer >= 0, number of FASTA records), `N50` (integer >= 1, nucleotide symbols)
and `averageTranscriptLength` (finite number >= 0, nucleotide symbols). Count
stored sequences including isoforms; do not call this a gene count. Compute
lengths from all sequence symbols, including ambiguity symbols, excluding deflines
and line endings. Define N50 by descending record lengths and the first length
whose cumulative sum reaches half the total. Omit length statistics for an empty
set. No expression matrix, novel-gene claim or quality cutoff is inferred.

Reuse the shared optional `Completeness` count object, reporting actual lineage,
BUSCO version and transcriptome mode; its four disjoint counts must sum to total
as required by the adopting type's rules. Percentages are not count values.
The current shared lineage pattern accepts `_odb` plus digits, while the current
BUSCO documentation includes dotted dataset versions such as `odb12.2`. Preserve
those source names and open a separate shared-contract review before attempting
to encode them; never rename a measured dataset to make it pass a pattern.
BUSCO and N50 remain separate measures; neither verifies biological correctness.

## D4: unknowns, identities and migration

Absent optional values are omitted; do not substitute null, empty strings,
`unknown` or zero. Zero remains a measured value where allowed. If a required
value is unavailable, the record is incomplete for this proposed contract; report
the missing value rather than inventing authors, taxonomy, method or dates.
Core slot/nested-object constraints are inherited unchanged; this document does
not quietly require an ORCID or strengthen every optional Author/Taxon member.

`identifier` and `accessionID` identify the transcriptome itself. Project, study,
sample and run URLs go in `relatedLink`; known SRR/ERR/DRR run accessions can also
populate optional `sequencingRuns`. Accession existence/association requires
separate checks. Use RNA/cDNA data exactly as supplied; T/U conversion is an
explicit derivative operation with a new checksum, never a header-parser fix.
`dateCreated` is resource creation, not sample collection; version, schemaVersion,
repository release and byte checksum are distinct identities.

Migration from legacy `fht.json` needs explicit retained source metadata:
`license` to `reuseConditions` only after semantic reconciliation; preserve
`assemblyAuthor` attribution separately from header authors; remove required
genome-only `masking` from the new draft without deleting historical records.
Legacy expression/completeness strings must not be guessed into typed numerical
objects. #7 owns the reviewed migration and generated schema, and #8 the actual
byte-backed fixtures. No new FHT version or persistent identifier is assigned here.

## Acceptance disposition and owned follow-up work

The [revised spec 005 proposal](005-rna-transcriptome-header/spec.md) and
[minimal/rich designs](fht-record-designs.md) make these recommendations reviewable.
They do not change the shared publication copy or make the legacy schema conform.

| #6 requirement | Decision/delivery in PR #20 | Follow-up owner |
| --- | --- | --- |
| Consultation record | Existing October 22 meeting summary and dated public-source research accepted by David as sufficient for this design stage; no invented endorsement | Additional community feedback remains welcome, without keeping #6 open indefinitely |
| Required-field rationale/minimal case | Approve the nine-field design and rationale | #7 implements the exact core constraints; #8 creates actual fixtures |
| Three construction cases | Approve D2 definitions; no guessed composite classification or mandatory de novo genome parent | #7 reviews exceptional/composite cases and parent rules |
| Optional context | Approve D3 base optionality | #7 models it; profiles/submission requirements remain separate |
| Names, units, unknowns, vocabulary | Approve D1–D4, including optional moleculeType and the explicit strand convention | #7 reviews exact sample serialization, FHT parent types/relationships/cardinality and migration |
| Spec 005 and minimal/rich designs | Revised development spec and design tables delivered here | #7 coordinates the reviewed shared-publication revision; #8 validates byte-backed fixtures |

### Follow-up acceptance after #6 closes

- **#7 — model and migration:** exact sample shape/controlled identifiers; allowed
  FHT parent types, relationship semantics and identity/cardinality requirements;
  ambiguous/composite history policy; pinned shared imports; generated schema and
  drift/equivalence; explicit retained author/reuse/statistics migration; shared
  publication coordination and version selection. These require their own review,
  not silent interpretation of this record.
- **#8 — fixtures:** actual minimal/rich and rejection records for all three cases,
  measured statistics, omitted/zero values, exact RNA/cDNA bytes and parent outcomes.
- **#9 — runtime/consumers:** toolkit implementation, typed round trips and installed
  package/bundle provenance after the reviewed schema exists.
- **#10 — publication/pilot:** maintainer-controlled release/aliases and a real
  public use case under the existing acceptance criteria.
- **[Shared #170](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/170)
  — BUSCO lineage grammar:** separately review dotted dataset versions across
  importing types; preserve measured names rather than coercing them.
- **[Shared #157](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/157)
  — INSDC coverage:** retain its independent assessment/disposition requirements.

Issue #6 closes on PR #20's merge as completion of this initial design and consultation
disposition. None of these downstream issues is closed by that merge. A merge
records acceptance of the development baseline; it does not publish an FHT schema
or certify community endorsement or INSDC submission readiness.
