# Quickstart: assess the headers of a data release

**Feature**: 010-fair-header-assessment | **Contracts**: [cli.md](contracts/cli.md), [assessment-report.schema.json](contracts/assessment-report.schema.json) | **Model**: [data-model.md](data-model.md)

This guide shows how a data provider, for example the Alliance of Genome Resources, runs the
assessment on its own download files. It also gives the end-to-end validation scenarios for this
feature. The example files are real files from the Phase 0 survey
([research/survey.md](research/survey.md)), and their header lines are in
[research/headers/](research/headers/).

> **Status**: `bioheaders assess` is implemented in FAIR-bioHeaders-Tools (feature 010; not
> yet in a release). The outputs below were checked against the implementation on 2026-10-10
> by running each scenario on the shared fixture captures in `assessment/` (the downloads are
> not needed for that), and are abridged. Suggestion texts end with the guideline item, for
> example "(see guideline G7)". The fixture tests (`assessment/manifest.json`) pin the
> statuses.

## Prerequisites

- Python 3.9 or later, and the `fair-bioheaders` release that ships `assess`:

  ```bash
  pip install "fair-bioheaders>=<version with assess>"   # placeholder: the first release that includes assess
  bioheaders assess --help
  ```
- No network is needed to assess files. The downloads below are only to obtain example files.
  To try the tool without downloading anything, use the shared fixtures in a FAIR-bioHeaders-Specification
  checkout (`assessment/headers/`).

## 1. One annotation file (User Story 1)

```bash
curl -sLO https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/985/GCF_000002985.6_WBcel235/GCF_000002985.6_WBcel235_genomic.gff.gz
bioheaders assess GCF_000002985.6_WBcel235_genomic.gff.gz
```

The header lines that are used as evidence ([captured](research/headers/ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff.txt)):

```text
1  ##gff-version 3
2  #!gff-spec-version 1.21
3  #!processor NCBI annotwriter
4  #!genome-build WBcel235
5  #!genome-build-accession NCBI_Assembly:GCF_000002985.6
6  #!annotation-source WormBase WS298
7  ##sequence-region NC_003279.8 1 15072434
8  ##species https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=6239
```

The expected report (abridged, text form):

```text
FAIR header assessment: GCF_000002985.6_WBcel235_genomic.gff.gz (gff3, gzip)
Online checks: not requested

Interoperable
  RDA-I1-01D   evidenced            line 1: ##gff-version 3
  RDA-I2-01M   partially evidenced  line 8: ##species https://www.ncbi.nlm.nih.gov/Taxonomy/...?id=6239
               suggestion: use a persistent taxonomy IRI (value from line 8)
                 ##species https://identifiers.org/taxonomy:6239
  RDA-I3-04M   evidenced            line 4: #!genome-build WBcel235
                                    line 5: #!genome-build-accession NCBI_Assembly:GCF_000002985.6
Reusable
  RDA-R1.1-01M not evidenced        no licence statement in the header
               suggestion: state the licence of this file
                 #!reuseConditions <SPDX licence id, e.g. CC-BY-4.0>
  RDA-R1.2-01M partially evidenced  who: line 3; from what: line 6; when: missing
               suggestion: record when this file was produced
                 #!date-produced <ISO 8601 date, e.g. 2026-10-10>
Findable
  RDA-F1-01D   not evidenced        no identifier of this file itself (line 5 identifies the genome; credited under I3)
  ...
Accessible
  RDA-A1-03D   not assessed         online check not requested (use --online)
  RDA-A2-01M   not applicable       repository-level: embedded metadata cannot outlive the file
  ...
Recorded links
  accession  NCBI_Assembly:GCF_000002985.6  (line 5, annotates)  not verified: no related file given
  name  WBcel235  (line 4, annotates)  not verified: no related file given
```

The output is a checklist with evidence, and there is no score (FR-004). Every status names the
lines it rests on, so a reviewer can check it by reading the file (SC-001).

## 2. A FASTA file with no header (US1 scenario 2)

```bash
curl -sLO https://download.alliancegenome.org/3.1.1/FASTA/WB/FASTA_WB_0.fa
bioheaders assess FASTA_WB_0.fa ; echo "exit $?"
```

The file starts `>I` and has nothing before it ([captured](research/headers/alliance_fasta-genome_FASTA_WB_0.fa.txt)).
Expected result:
- Every indicator that is assessed is `not evidenced`, including the format-declaration
  indicators. A format recognised by sniffing is not header evidence (research R-05).
- Each one has a suggestion written as a FAIR-bioHeaders line, for example
  `;~reuseConditions: <SPDX licence id, e.g. CC-BY-4.0>`.
- The `not applicable` and `not assessed` entries keep their reasons.
- The exit code is `exit 0`. A file with no header is not an error.

## 3. An annotation together with its genome (User Story 2)

WormBase WS298 records no genome identity, only `##sequence-region` lines
([captured](research/headers/wormbase_gff3_c_elegans.PRJNA13758.WS298.annotations.gff3.txt)):

```bash
B=https://ftp.ebi.ac.uk/pub/databases/wormbase/releases/WS298/species/c_elegans/PRJNA13758
curl -sLO $B/c_elegans.PRJNA13758.WS298.annotations.gff3.gz
curl -sLO $B/c_elegans.PRJNA13758.WS298.genomic.fa.gz
bioheaders assess --related c_elegans.PRJNA13758.WS298.genomic.fa.gz \
    c_elegans.PRJNA13758.WS298.annotations.gff3.gz
```

Expected (abridged):

```text
Interoperable
  RDA-I3-04M    not evidenced          Metadata include qualified references to other data
      suggestion: Record the accession of the assembly this annotation describes, ...
        #!genome-build-accession NCBI_Assembly:<versioned assembly accession, e.g. GCF_000002985.6>

Recorded links
  none recorded in the header

Circumstantial evidence (not a recorded link)
  source: sequence-region  related file: c_elegans.PRJNA13758.WS298.genomic.fa.gz
  names compared: 7  lengths compared: 7  not declared: 0
  missing from the related file: none
  length differences: none
  verdict: consistent

Pair: consistent-unverified
```

Two more pairs show the other verdicts (the shared fixtures `assessment/pairs/` reproduce them):
- **The same assembly with different sequence names.** The NCBI GenBank GFF3 (`BX284601.5`, …)
  against the RefSeq genome (`NC_003279.8`, …). Every declared name is listed under "missing from
  genome", the verdict is `inconsistent`, and the pair is `inconsistent` (US2 scenario 3).
- **A recorded accession that the genome does not state.** The RefSeq GFF3 against the RefSeq
  genome. The accession link is `unverifiable` (the genome FASTA states no identity), with the
  hint "related file name contains GCF_000002985.6". The names are consistent, so the pair is
  `consistent-unverified`. It is never `recorded-match` on the strength of a file name
  (research R-07).

In CI, add `--fail-on-mismatch` to fail when a *recorded* link disagrees with the supplied file
(exit 3).

## 4. A whole release (User Story 4)

This walkthrough uses a small Alliance release slice: one directory, with one file per
provider-type combination from the survey.

```bash
mkdir -p release-9.1.0 && cd release-9.1.0
for u in \
  https://download.alliancegenome.org/9.1.0/GFF/MGI/GFF_MGI_1.gff.gz \
  https://download.alliancegenome.org/8.3.0/GFF/WB/GFF_WB_4.gff.gz \
  https://download.alliancegenome.org/9.1.0/GAF/WB/GAF_WB_1.gaf.gz \
  https://download.alliancegenome.org/3.2.0/VCF-GZ/WBcel235/VCF-GZ_WBcel235_38.vcf.gz \
  https://download.alliancegenome.org/9.1.0/FASTA/GRCz12tu/FASTA_GRCz12tu_0.fa.gz \
  https://download.alliancegenome.org/3.1.1/FASTA/WB/FASTA_WB_0.fa ; do curl -sLO "$u"; done
printf 'GFF_WB_4.gff.gz\tFASTA_WB_0.fa\nVCF-GZ_WBcel235_38.vcf.gz\tFASTA_WB_0.fa\n' > ../pairs.tsv
cd ..
bioheaders assess --recursive --pairs pairs.tsv --output reports/9.1.0 release-9.1.0/
```

The expected outputs are listed below. The `summary.tsv` excerpt shows the columns for
RDA-I1-01D, RDA-I3-04M and RDA-R1.1-01M only:

```text
reports/9.1.0/
  FASTA_GRCz12tu_0.fa.gz.assessment.json   .md
  FASTA_WB_0.fa.assessment.json            .md
  GAF_WB_1.gaf.gz.assessment.json          .md
  GFF_MGI_1.gff.gz.assessment.json         .md
  GFF_WB_4.gff.gz.assessment.json          .md
  VCF-GZ_WBcel235_38.vcf.gz.assessment.json .md
  summary.json  summary.md  summary.tsv

path                       format  scope     pair                   RDA-I1-01D  RDA-I3-04M  RDA-R1.1-01M
FASTA_GRCz12tu_0.fa.gz     fasta   assessed                         N           N           N
FASTA_WB_0.fa              fasta   assessed                         N           N           N
GAF_WB_1.gaf.gz            gaf     assessed                         E           N           N
GFF_MGI_1.gff.gz           gff3    assessed                         E           E           N
GFF_WB_4.gff.gz            gff3    assessed  consistent-unverified  E           P           N
VCF-GZ_WBcel235_38.vcf.gz  vcf     assessed  consistent-unverified  E           P           N
```

Points that a provider should expect from these files:
- **`GFF_MGI_1`** has two recorded links. One is a name: `#!assembly GRCm39`, line 4. The other
  is an accession found inside `#!annotationSource RefSeq GCF_000001635.27-RS_2024_02`, line 5,
  and the accession decides RDA-I3-04M. Line 3, `#!date-produced Mon Sep 21 09:32:10 2026`, gets
  a `format-irregularity` finding (the date is not ISO 8601) and a suggested ISO form. The
  suggested form is built from that same line.
- **`GFF_WB_4`**:
  - Line 1 (`# WormBase release WS298`) comes before `##gff-version`. It gets a
    `format-irregularity` finding and an `unrecognised-comment` finding.
  - `#!assembly WBcel235` is a name only (P).
  - The pair is checked circumstantially against the genome.
- **`VCF-GZ_WBcel235_38`**: the `##contig` lines carry `assembly=WBcel235` (a name) but no
  `length` and no `md5`. The circumstantial check therefore compares names only
  (`lengths_compared: 0`), and the
  suggestion is to add `length=` and `md5=` with values computed from the paired genome
  (`value_source: related-file`).
- **Every file**: RDA-R1.1-01M is `N`. No surveyed file states a licence (survey §3.4). The
  suggestion is a single placeholder line in each file's convention.

The summary also gives per-indicator counts across files, for example "RDA-R1.1-01M: not
evidenced in 6 of 6". It has no per-file total.

To track improvement between releases, assess the next release into `reports/9.2.0` and compare:

```bash
diff reports/9.1.0/summary.tsv reports/9.2.0/summary.tsv
```

Re-running on unchanged files gives byte-identical reports (FR-009), so any difference is a real
change in a header.

## 5. Optional online checks

```bash
bioheaders assess --online GCF_000002985.6_WBcel235_genomic.gff.gz
```

The tool resolves only the identifiers and URLs found in the header: DOIs through `doi.org`,
CURIEs through `identifiers.org`, and http(s) URLs as given. It never sends file contents, never
requests the schema URL of a FAIR-bioHeaders header, and refuses other schemes and hosts that
resolve to private or loopback addresses. The report says `Online checks: ran` and lists each
request with its outcome, HTTP status and time. Only the four access indicators can change
status: they move from `not assessed` to a status (`not assessed` with
`online-check-unavailable` when the check could not be made). Other indicators get a note.
`--online-timeout SECONDS` sets the per-request timeout (default 10). This RefSeq header has no
identifier or URL of the file itself, so the four indicators become `not evidenced`; the
taxonomy URL on line 8 is requested and its outcome is a note under RDA-I2-01M.

## Validation scenarios (end-to-end)

| # | Scenario | Command | Expected | Covers |
|---|---|---|---|---|
| V1 | Shared fixtures | `python scripts/check_assessment.py --tool ../FHR-File-Converter` (FAIR-bioHeaders-Specification) | `ok` for every manifest entry | FR-001–FR-006, FR-008, FR-012, SC-003 |
| V2 | GFF3 with accession | §1 | RDA-I3-04M evidenced, citing line 5 | US1-1 |
| V3 | FASTA with no header | §2 | every assessed indicator `not_evidenced`, a suggestion for each, exit 0 | US1-2, FR-003 |
| V4 | FHR genome | `bioheaders assess conformance/valid/fasta-lf.fhr.fasta` | a conformance section `valid` against `fhr.json` (raw-main URL and bundled SHA-256 recorded), separate from the checklist | US1-3, FR-008 |
| V5 | Pairs | §3 plus `assessment/pairs/*` | the expected pair classification for correct, version-mismatch, partial and name-mismatch pairs | US2, SC-003 |
| V6 | Guideline coverage | `python -m unittest tests.test_assessment_guideline -v` (FAIR-bioHeaders-Specification) | every item has ≥ 2 conventions and check ids; the 41 indicators are covered or out of scope | US3, FR-007 |
| V7 | Release | §4 with a 200-file synthetic release: `python scripts/bench_assess.py --files 200` (toolkit) | done in < 600 s; a second run is byte-identical (2026-10-10: 19.7 s on an i7-1165G7 laptop, Python 3.13) | US4, SC-004, FR-009 |
| V8 | Offline guarantee | toolkit test suite with sockets disabled | passes; `online_checks: not_requested` | FR-010, FR-011 |
| V9 | Reviewer agreement | the reviewer copies `assessment/review/sc001-template.tsv` to `sc001-<date>.tsv` and fills it (see `assessment/review/README.md`) | ≥ 90% agree | SC-001, SC-002 |
| V10 | Provider trial | a maintainer asks the Alliance to run §4 on a release | the provider reports the results useful | SC-005 (maintainer action) |
