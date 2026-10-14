# Research: FAIR header assessment (Phase 0)

**Feature**: 010-fair-header-assessment | **Date**: 2026-10-10 | **Plan**: [plan.md](plan.md) | **Spec**: [spec.md](spec.md)

This document resolves every unknown in the plan's Technical Context. Its decisions rest on two
appendices, which hold the evidence:

- **Appendix A**: [research/survey.md](research/survey.md). It surveys the headers of 34 real
  download files from 9 provider groups, covering FASTA, GFF3, GAF and VCF. The captured header
  lines are in [research/headers/](research/headers/).
- **Appendix B**: [research/rda-indicators.md](research/rda-indicators.md). It interprets all 41
  RDA FAIR Data Maturity Model indicators for file headers. It also covers the status vocabulary,
  the evidence rules and the licence of the RDA text.

Entries cite the appendices by section ("A §R2" is survey entry R2, "B §3" is
rda-indicators section 3). When this document and an appendix disagree, this document wins: it
adds the fifth status that the spec clarification of 2026-10-10 introduced (R-04), and it
requires a declared format before RDA-I1-01D, RDA-R1.3-01D or RDA-R1.3-02D can be credited
(R-05).

Two repositories are involved:
- **FAIR-bioHeaders-Specification** is this repository.
- **FAIR-bioHeaders-Tools** is the `fair-bioheaders` distribution. Its import name and command are
  `bioheaders`, and the local checkout is `../FHR-File-Converter`.

---

## R-01. Where each part lives

**Decision**:

| Part | Repository | Path | Status |
|---|---|---|---|
| Guideline (US3, FR-007) | FAIR-bioHeaders-Specification | `docs/FAIR_HEADER_GUIDELINE.md` | Guidance only. Changes no schema; uses no MUST/SHOULD |
| Assessment (US1, US2, US4) | FAIR-bioHeaders-Tools | `bioheaders assess` subcommand, code in `bioheaders/assess/` | New subcommand; no new `fhr-*` entry point |
| Indicator rubric | FAIR-bioHeaders-Tools | `bioheaders/assess/data/rubric.json` | Versioned data file shipped in the wheel |
| Synonym table | FAIR-bioHeaders-Tools | `bioheaders/assess/data/synonyms.json` | Versioned data file shipped in the wheel |
| Reference tables (SPDX, identifier schemes, formats) | FAIR-bioHeaders-Tools | `bioheaders/assess/data/reference/*.json` | Pinned snapshots, version recorded |
| Report JSON Schema | FAIR-bioHeaders-Tools (design source: `contracts/` here) | `bioheaders/assess/data/assessment-report.schema.json` | Byte-identical to `contracts/assessment-report.schema.json` at release |
| Shared fixtures (implementation-neutral expected outcomes) | FAIR-bioHeaders-Specification | `assessment/` (`manifest.json`, `headers/`, `pairs/`, `edge/`) | Same style as `conformance/` |
| Fixture runner | FAIR-bioHeaders-Specification | `scripts/check_assessment.py --tool ../FHR-File-Converter` | Same style as `check_conformance.py --converter` |

The tool reuses the toolkit's `open_input`, which detects gzip/BGZF by magic bytes and streams,
and `read_chunks`. For files that carry a FAIR-bioHeaders header it also reuses
`sequence_parts`/`header_lines`, so `assess` reads an FHR header from the same lines as
`validate`, `verify` and `strip`.

**Rationale**:
- The guideline describes what a header *should* contain for types that have no specification.
  It belongs with the specifications, but it is guidance, so it does not touch `fhr.json` and
  leaves FAIR-bioHeaders-Specification constitution I and II untouched.
- The assessment is behaviour, and behaviour lives in the toolkit (toolkit constitution I). A
  subcommand of the existing `bioheaders` CLI adds no new public entry point and inherits the
  streaming, gzip/BGZF and stdin support.
- The rubric and the synonym table change faster than code: new providers and new spellings.
  As versioned data files they can be reviewed as data, and their versions go into every report,
  which FR-009 requires.
- The fixtures follow the `conformance/` pattern. The expected outcomes are language-neutral, so
  another implementation, such as the 009 GFF3 validator or the website, can be checked against
  the same files.
- The fixtures go in a top-level `assessment/` and not in `conformance/assessment/`. The reason is
  that `scripts/check_conformance.py` `generated_files()` picks up every `manifest.json` under
  `conformance/` with `rglob`, and would report a second manifest as "not produced by the
  generator".

**Alternatives considered**:
- *A standalone tool or repository (`fair-header-check`).* Rejected: it would duplicate the
  streaming/gzip reader and the FHR reader, so FHR lines could be read two ways (toolkit
  constitution II), and it adds a package to maintain.
- *Putting the rubric in FAIR-bioHeaders-Specification.* Rejected for release 1. The rubric's rule ids are
  coupled to the code that evaluates them. The guideline, which *is* in FAIR-bioHeaders-Specification, carries
  the human-readable interpretation and cites the same check ids, and a cross-repository check
  keeps the two in step (cross-check task in tasks.md). This is an open question for the maintainers (plan, Open
  questions).
- *Inside the planned 009 GFF3 validator.* Rejected: 009 is GFF3-only and has no plan yet. 009 can
  call `bioheaders assess` or use the fixtures later.
- *A hosted web service.* Rejected by the spec Assumptions ("Providers run the assessment
  themselves").

## R-02. Header conventions recognised (FR-001)

**Decision**: Adopt A §R1 as written. Recognise six conventions:
- FAIR-bioHeaders lines (`;~` in FASTA, `#~` in GFA/GFF3);
- GFF3 `##` directives;
- GFF3 `#!` pragmas, as `key value` or `key: value`;
- GAF `!key: value`, using only the first block as the file's own metadata;
- VCF `##key=value` and `##KEY=<…>`, with the `##contig` sub-fields parsed;
- the first FASTA defline, as record-level evidence.

The header region is defined per format:
- GFF3: lines before the first feature line or `##FASTA`.
- GAF: leading `!` lines.
- VCF: lines up to and including `#CHROM`.
- FASTA: lines before the first `>`, plus the first defline.
- Unknown text: leading lines that begin with `#`, `!`, `;`, `%` or `//`.

Any other comment line in the header region is reported as an *unrecognised comment line*
(edge case), and is never dropped. The format comes from content sniffing first and the file name
second, because dbSNP has no `.vcf` extension. `--type` overrides both.

**Rationale**: Covers every metadata line in the 34 surveyed files, including the format
irregularities in A §3.7.

**Alternatives considered**: See A §R1. They were FAIR-bioHeaders-only, strict spec parsers, and a
flat GAF header.

## R-03. Which indicators are assessed (FR-012)

**Decision**: Adopt B §5.A. Every report lists all 41 RDA indicators:
- **25 header-level offline indicators** are evaluated by default.
- **4 access indicators** are evaluated only with `--online`: RDA-A1-03D, RDA-A1-04D, RDA-A1-05D
  and RDA-A1.1-01D.
- **10 indicators cannot apply to a file header.** They are reported `not applicable`, with the
  reason codes `embedded-metadata`, `repository-level` or `object-in-hand`.
- **2 data-body indicators**, RDA-I3-01D and RDA-I3-02D, are reported `not assessed` with reason
  `deferred-data-body`. They could apply, but release 1 does not scan record bodies.

The indicator id is the RDA id, for example `RDA-I3-04M`.

**Rationale**: FR-012 requires that every indicator be accounted for, and FR-011 requires offline
operation by default. The 2 data-body indicators are moved from B's `not applicable` to
`not assessed`, because under the clarified FR-002 "not applicable" may only mean "cannot apply
to a file header".

**Alternatives considered**: See B §5.A. They were the F-UJI subset, per-principle assessment,
crediting inherited identity, and scanning bodies now.

## R-04. Report statuses (FR-002, FR-004)

**Decision**: There are five statuses. The JSON values are the snake_case forms in brackets.
1. **evidenced** (`evidenced`): every condition of the rule is met by the cited lines.
2. **partially evidenced** (`partially_evidenced`): the rule's named subset is met.
3. **not evidenced** (`not_evidenced`): no condition is met, or the values are malformed.
4. **not applicable** (`not_applicable`): the indicator cannot apply to a file header. A reason
   code is mandatory: `embedded-metadata`, `repository-level` or `object-in-hand`.
5. **not assessed** (`not_assessed`): the check was not run. A reason code is mandatory:
   - `online-check-not-requested`;
   - `online-check-unavailable` (network error or timeout; never treated as a failure);
   - `deferred-data-body`;
   - `binary-format-out-of-scope`;
   - `archive-not-supported` (for example the FlyBase `.gff.gz` that is a tar archive);
   - `unsupported-header-type` (a FAIR-bioHeaders type with no published schema yet: FHT, FHP,
     FHGFF3);
   - `input-unreadable`.

Each result carries:
- the evidence lines (line number, convention, raw key, value);
- `method` (`offline` or `online`);
- a suggestion whenever the status is `partially_evidenced` or `not_evidenced` (FR-003);
- findings, such as malformed or conflicting values.

There is no aggregate score, no per-area RDA level and no "is FAIR" wording anywhere, including
in the batch summary (R-16). Each status can be checked by reading the cited lines.

**Rationale**: Implements the clarification of 2026-10-10 and closes the open point in B §3. RDA
maturity levels 1–3 describe a provider's intent, which a file cannot show (B §5.B).

**Alternatives considered**:
- Four statuses with `online-check-not-run` as a not-applicable reason. Superseded by the
  clarification.
- RDA levels 0–4. Not observable from a file.
- Pass/fail only. Hides the common "name but no accession" case.
- Weighted scores. Forbidden by FR-004.

## R-05. Evidence rules

**Decision**: Adopt B §3, rules 1–7, unchanged in substance, plus two additions:
- **Record-level cap**: evidence that comes only from the first FASTA defline (A §3.1) can give a
  file-level indicator at most `partially_evidenced`. The report marks it with
  `scope: "first-record"`.
- **File name and path are never evidence**: they are not in the header. They may only *inform a
  suggestion*, and then they are marked "from the file name; confirm before use" (R-11).
- **A format recognised only by sniffing is not evidence**. RDA-I1-01D, RDA-R1.3-01D and
  RDA-R1.3-02D need a *declared* format: `##gff-version`, `##fileformat`, `!gaf-version`, or a
  FAIR-bioHeaders `schema`. A FASTA with no header is therefore `not_evidenced` on these three
  too, and its suggestion is to add a FAIR-bioHeaders header. This departs from B §2 (which made
  undeclared FASTA "partial"). It is needed so that US1 scenario 2 holds: for a FASTA with no
  header, *every indicator that is assessed* is `not_evidenced`. The `not_applicable` and
  `not_assessed` entries keep their reasons.

Identifier-shaped values count only under a key whose documented meaning is that identifier.
That covers the edge case of free text that looks like an identifier. When an identifier is
found in free text, the result is a suggestion and a finding of kind `identifier-in-free-text`.
It is never credited.

**Rationale**: These rules need no judgement, which SC-001 (≥ 90% reviewer agreement) and FR-009
(reproducibility) both require.

**Alternatives considered**:
- Heuristic "looks like" credit. Rejected: it lowers reviewer agreement and conflicts with
  FAIR-bioHeaders-Specification constitution IV.
- Treating the defline as a header. Rejected: it would over-credit record-level metadata.

## R-06. Recorded-link ranking (FR-005, US2)

**Decision**: Adopt A §R2. Recorded links to related data rank by strength, and each link is
classified as exactly one kind:

| Rank | Kind | Sources | Indicator credit (RDA-I3-02M / RDA-I3-04M) |
|---|---|---|---|
| 1 | `checksum` / `seqcol` / `sequence-digests` | FAIR-bioHeaders `derivedFrom.checksum` / `derivedFrom.seqcol_id`; VCF `##contig md5=` on every contig. (Implementation note: a FASTA defline `MD5=`, as in FlyBase, is the digest of that record's *own* sequence, so it is credited as record-level identity under RDA-F1-02D, not as a link to related data) | Identifier form: evidenced if a relationship is stated |
| 2 | `accession` | `derivedFrom.accessionID`; GFF3 `#!genome-build-accession` (optional `NCBI_Assembly:` prefix, pattern `GC[AF]_\d{9}\.\d+`); accession inside `#!annotation-source`/`annotationSource`; VCF `##reference`/`##contig assembly=` matching that pattern | Identifier form: evidenced if a relationship is stated |
| 3 | `url` | VCF `##reference=<URL>`, `##contig URL=` | Identifier form. A directory URL is credited as partial, with a finding `url-names-directory` |
| 4 | `name` | GFF3 `#!genome-build`, `##genome-build`, `#!genome-version`, `#!assembly`; VCF `##reference=GRCh38`; Ensembl defline assembly field; FlyBase `release=` | **partially_evidenced** ("named, not identified") |

When several links are present, every one is reported. The strongest one decides the indicator
status. If two links of the same kind conflict, for example two different accessions, the result
is a `conflicting-values` finding, and the indicator cannot reach `evidenced`.

GAF gets the reason "the header links to a gene set or ontology release, not a genome": no
genome link is expected. GAF is checked for the ontology and gene-set version instead
(RDA-I3-02M, via `!go-version`).

**Rationale**: Today only NCBI and Ensembl GFF3 record an accession, and no derived file records
a digest. The ranking separates identifiers that can be checked from names that only claim a
genome (A §R2).

**Alternatives considered**: See A §R2. They were any assembly-like string, the file name as a
recorded link, and requiring a checksum.

## R-07. Verifying a recorded link against the related file (FR-006)

**Decision**: `--related FILE` (or `--pairs`) supplies the related file. Each recorded link gets
one verdict: `match`, `mismatch` or `unverifiable` (with a reason).

| Link kind | How it is verified offline | `unverifiable` reasons |
|---|---|---|
| `checksum` (FHR-family) | The related file's FHR checksum is computed with the toolkit's existing checksum code. That is SHA-512/256 over the exact bytes except the root checksum line (docs/FORMAT.md). If the related file has an FHR header, its stated checksum is verified first. Then the computed value is compared with the recorded one | related file unreadable |
| `seqcol` | Compared with the related file's *stated* `seqcol_id` (FHR field) | `related-file-states-no-seqcol`. Computing a SeqCol digest is deferred: SeqCol is a supplied identifier (FAIR-bioHeaders-Specification constitution III), and no GA4GH vectors are in the repository yet |
| `sequence-digests` (VCF contig `md5`, defline `MD5=`) | The MD5 of each named sequence in the related FASTA is computed as the VCF specification defines it (sequence letters upper-cased, no whitespace) and compared | sequence name absent from the related file (reported in the name lists) |
| `accession` | Compared with an accession the related file *states* about itself: FHR `accessionID`, or a native self-identifying key | `related-file-states-no-identity`. That is the case for every surveyed FASTA (A §R2). A file name that contains the accession is reported as a *hint*, never as a match |
| `url` / `name` | Compared with an equal URL or name the related file states | `related-file-states-no-identity` |

A malformed recorded identity, such as a wrong-length checksum or an accession that fails the
pattern, gets a `malformed` finding. Its verdict is `unverifiable` with reason `malformed`. This
covers that edge case. `--fail-on-mismatch` makes any `mismatch` return exit code 3 (contract
in [contracts/cli.md](contracts/cli.md)).

**Rationale**: "unverifiable" is the honest verdict for an accession or name when the genome does
not state its own identity (A §3.2). Computing the FHR checksum reuses code that is already
correct. The per-sequence MD5 is defined by VCF, and FlyBase already publishes it.

**Alternatives considered**:
- *Treating a file-name match as `match`.* Rejected: it is not recorded (FR-005), and
  FAIR-bioHeaders-Specification constitution IV forbids it.
- *Computing SeqCol digests now.* Deferred. Implementing the GA4GH algorithm without published
  vectors here risks a wrong digest. This is an open question.
- *Resolving the accession online to get the expected sequence names.* Rejected for release 1:
  it is network-dependent and not reproducible.

## R-08. Circumstantial evidence (FR-005, US2 scenarios 2 and 3)

**Decision**: When a related file is supplied, compare these declared sequence names and lengths
in the derived file with the related file's sequence names and lengths:
- GFF3 `##sequence-region` names and ends;
- VCF `##contig ID`/`length`;
- seqids of the bounded record sample (R-14), when no names are declared.

The related file is a FASTA, scanned in one streaming pass, or an FHR FASTA/GFA.

The result has these parts:
- `names_compared`;
- `missing_from_related` (the full list, sorted; US2 scenario 3);
- `length_mismatches` (name, declared, actual);
- `not_declared` (sequences of the related file that the derived file does not mention; counted
  only, never a failure);
- `lengths_compared` (how many declared lengths could be compared; VCF `##contig` lines often
  carry none);
- a verdict: `consistent` (every declared name present and no declared length differs),
  `partially_consistent` (some names missing, or some declared length differs), `inconsistent`
  (no declared name present), or `not_checked` (no names declared and no records sampled).
  Lengths that are not declared are counted in `lengths_compared` and never lower the
  verdict.

This section is labelled *circumstantial evidence, not a recorded link*. It is reported
separately and never credited under any RDA indicator (B §3 rule 7).

The pair has one overall classification:
- `recorded-match`: at least one link is `match` and none is `mismatch`.
- `recorded-mismatch`: any link is `mismatch`.
- `consistent-unverified`: no `match`, the circumstantial verdict is `consistent`, and no link is
  `mismatch`.
- `partial`: the circumstantial verdict is `partially_consistent`.
- `inconsistent`: the circumstantial verdict is `inconsistent`.
- `unknown`: nothing could be compared.

SC-003 is tested against this classification.

**Rationale**: Matching names and lengths is the only check possible for WormBase-style files
(A §R2). A precedence rule fixed in advance gives one classification per pair, which SC-003 can
test.

**Alternatives considered**:
- *Merging circumstantial evidence into the link verdict.* Rejected: FR-005 forbids it.
- *Comparing sequence content.* Out of scope, since annotations carry no sequence.
- *Name aliasing (`I` vs `NC_003279.8`).* Rejected: aliasing needs external tables (the SeqCol
  or assembly report). The GenBank and RefSeq pair is reported `inconsistent`, and the missing
  names are listed. That outcome is correct: the names differ.

## R-09. FAIR-bioHeaders schema conformance (FR-008) and schema authority

**Decision**: When a file carries a FAIR-bioHeaders header, the report has a separate
`conformance` section, apart from the FAIR assessment.
- For FHR, the header is validated with the toolkit's existing validator against the bundled
  schema, which is byte-identical to `fhr.json`.
- The report records:
  - the schema actually used: the canonical raw-main URL
    `https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/main/fhr.json`, the
    bundled copy's SHA-256, and the `schemaVersion` the file cites;
  - the result: `valid`, `invalid` (with the JSON path and message) or `not_assessed`.

The validator honours the version the file cites (spec#44 decision of 2026-10-09). If the file
cites a version the toolkit does not bundle, the result is `not_assessed` with reason
`unsupported-schema-version`. There is no silent fallback, and the schema URL in the header is
never fetched, not even with `--online`.

FHT, FHP and FHGFF3 have no published JSON schema yet. For them conformance is `not_assessed`
with reason `unsupported-header-type`, but their core fields are still read as evidence.

The FAIR assessment *cites* the conformance result under RDA-R1.3-01M and RDA-R1.3-02M; it does
not recompute it. An FHR header that fails to parse is reported under conformance. Its values are
not used as FAIR evidence, so nothing is reinterpreted (toolkit constitution III).

**Rationale**:
- spec#44 (molikd, 2026-10-09) and website#15 make raw-main the canonical schema and the bundled
  copy a cache with recorded provenance.
- Validation follows the cited version, and an unknown version gives an actionable unsupported
  result.
- "An untrusted header URL must not trigger arbitrary automatic fetches."

**Alternatives considered**:
- *Fetching the cited schema online.* Rejected by spec#44.
- *Validating every file against main.* Rejected: spec#44 says that is an explicit migration
  check, not the default.
- *Folding conformance into R1.3 statuses.* Rejected by FR-008.

## R-10. Online opt-in (FR-010, FR-011)

**Decision**: Offline is the default, and no network module is imported unless `--online` is
given. With `--online` the tool resolves only values taken from the header:
- identifiers (DOI through `https://doi.org/`, CURIEs and accessions through
  `https://identifiers.org/`);
- URLs.

The rules for these requests:
- Python's `urllib`, so there is no new dependency.
- `HEAD`, falling back to `GET` with `Range: bytes=0-0`.
- Schemes `http` and `https` only.
- At most 5 redirects, and each one is checked against the same rules.
- A per-request timeout (default 10 s, `--online-timeout`).
- Hosts that resolve to loopback, private or link-local addresses are refused.
- No cookies and no credentials.
- A fixed User-Agent `bioheaders-assess/<version>`.
- At most 1 request per host at a time.
- Results are de-duplicated per run.

No file content is ever sent; the only thing sent is the identifier or URL itself.

Each online result records:
- the URL;
- the final URL;
- the HTTP status;
- the UTC time;
- `time_dependent: true`.

Online results go in a separate `online` section of the report.

What the online results can change:
- The 4 access indicators can move from `not_assessed` (`online-check-not-requested`) to a
  status.
- Network errors give `not_assessed` (`online-check-unavailable`).
- RDA-F1-01D, RDA-I2-01M and RDA-R1.1-03M get only a resolution note.
- An online result never downgrades an offline status (B §3 rule 6).

The report's top-level `online_checks` field says `ran` or `not_requested`, which FR-011 requires.

**Rationale**: FR-010 and FR-011, and the spec#44 guidance on untrusted URLs. The refused
private addresses and the scheme rule keep requests to public resolvers, so a hostile header
cannot direct requests at internal services (toolkit constitution III).

**Alternatives considered**:
- *Online by default.* Rejected by FR-011.
- *A third-party HTTP client.* Rejected: it adds a runtime dependency (both constitutions, V).
- *FTP resolution.* Deferred: no surveyed identifier needs it, and it makes timeouts harder to
  control.

## R-11. Suggestions (FR-003, SC-002) and no invented metadata

**Decision**: Each gap has a suggestion with these parts:
- the concept;
- the line to add, in the file's own convention where one exists:
  - GFF3: a `#!` pragma, using the established native key where there is one (for example
    `#!genome-build-accession`) and otherwise the core field name (for example
    `#!reuseConditions`);
  - VCF: `##key=value`, or `##contig=<…,md5=…>`;
  - GAF: `!key: value`;
- otherwise, a FAIR-bioHeaders line, for example `;~reuseConditions: …` for FASTA, with a note
  that FHT and FHP are drafts;
- the guideline item it comes from (R-17).

Values in suggested lines come from one of three sources, which the suggestion names:
- the file's own statements, for example promoting `#!genome-build WBcel235` to an accession
  suggestion that *names* the build;
- the supplied related file;
- a labelled placeholder (`<SPDX licence id, e.g. CC-BY-4.0>`).

Values from the file name are offered only as "from the file name; confirm before use". No
suggestion contains an invented accession, licence, author or date.

The suggestion templates live in `rubric.json`, per indicator and per convention. The preferred
native and core keys per concept live in `synonyms.json` (`emit`).

**Rationale**: SC-002 requires that a suggestion can be applied without consulting other
documentation. FAIR-bioHeaders-Specification constitution IV forbids invented metadata and requires labelled
placeholders.

**Alternatives considered**:
- *Always suggesting FAIR-bioHeaders lines.* Rejected: it contradicts US3 scenario 2 and FR-003
  ("in the file's own convention").
- *Filling licence and author from provider defaults.* Rejected as invented metadata.

## R-12. Report formats and reproducibility (FR-009)

**Decision**: The JSON report follows
[contracts/assessment-report.schema.json](contracts/assessment-report.schema.json). It is
serialised with sorted keys, UTF-8, LF line endings and a trailing newline, and contains no
floats.

The human-readable forms:
- `text` (terminal, the default for a single file);
- `markdown` (renders on GitHub and in issue trackers; used for the per-file and summary
  reports in `--output`).

Both are rendered from the same in-memory report, so they cannot disagree.

The reproducible part of the report contains:
- the tool name and version;
- the rubric, synonym and reference-table versions;
- the input as given, its size, the SHA-256 of the header bytes read, the detected format and
  the compression;
- the results.

Wall-clock times appear only in the `online` section. `--hash-inputs` adds a full-file SHA-256
on request; it is optional because it costs a full read (R-14).

With the same input bytes and the same tool and table versions, the report is byte-identical
(US4 independent test). The attribution block (R-19) is always included.

**Rationale**: FR-009 asks for a human-readable and a machine-readable report, with reproducible
results. Keeping times and online results out of the reproducible part lets two runs be compared
by diff.

**Alternatives considered**:
- *HTML reports.* Deferred: Markdown is enough for issue trackers and needs no escaping
  machinery.
- *SARIF.* Rejected: it is designed for code-analysis tools, and it would push a score-like
  severity model.
- *YAML reports.* Rejected: JSON is the machine format already validated with `jsonschema`.

## R-13. Rubric, synonym and reference data files

**Decision**: All data files are JSON, validated by JSON Schemas shipped next to them (formats in
[contracts/data-files.md](contracts/data-files.md)). Each file carries `version` (SemVer). The
rubric's version changes whenever a rule or a suggestion changes.

- **`rubric.json`**: one entry per RDA indicator (41). Each entry gives:
  - the id;
  - the verbatim short title (CC BY 4.0);
  - the FAIR principle, priority and M/D;
  - `assessability` (`offline`, `online`, `not_applicable` or `deferred`);
  - the file-header interpretation (paraphrased, marked as an adaptation);
  - the reason code if not applicable;
  - `conditions` (concepts and required value forms);
  - `evidenced_when` / `partial_when` (all, any, never, minimum counts, or named `any_of`/`all_of` condition lists);
  - an optional named `check` for the rules that cannot be expressed as data (`derived-link`,
    `fhr-conformance`, `format-declared`, `record-sample-parse`);
  - the guideline item id;
  - suggestion templates per convention;
  - the attribution block.
- **`synonyms.json`**: the key normalisation rules (case fold; `-`, `_`, space and camelCase
  folded; trailing `:` removed). Then concepts (for example `assembly-accession`, `licence`,
  `date-created`, `taxon`), each with:
  - its matching keys per convention;
  - its value forms (named regular expressions, such as `insdc-assembly-accession`,
    `spdx-id`, `taxonomy-iri`, `iso-date`, `orcid`);
  - its scope (`file` or `first-record`);
  - its `emit` key per convention.

  The table starts with every key in A §4.
- **`reference/spdx-licenses.json`**: SPDX licence list ids and URLs, pinned to a release.
- **`reference/id-schemes.json`**: a curated subset of Bioregistry and identifiers.org prefixes
  (taxonomy, orcid, ror, doi, so, go, eco, insdc.gca, refseq.gcf, ena.embl, bioproject,
  biosample), with patterns and persistence flags, pinned.
- **`reference/formats.json`**: community formats (FASTA, GFF3, GAF, VCF) with FAIRsharing ids
  and version directives.

**Rationale**:
- `jsonschema` is already a dependency.
- JSON has no anchors or aliases, which suits the fail-closed rule (toolkit constitution III),
  and it is deterministic.
- A curated subset of prefixes keeps the wheel small (both constitutions, V).
- The named-check escape hatch keeps the data format simple: it does not become a rule language.

**Alternatives considered**:
- *YAML.* Rejected: anchors would have to be rejected anyway, and comments are not needed
  because the files hold `description` fields.
- *A full Bioregistry dump.* Rejected: about 1,500 prefixes, mostly irrelevant, and it would need
  frequent refreshes.
- *Rules as Python code only.* Rejected: they could not be reviewed as data, and their version
  would be hidden.
- *A general rule DSL.* Rejected as a speculative framework (FAIR-bioHeaders-Specification constitution V).

## R-14. Performance approach (SC-004: 200 files in under 10 minutes on a laptop)

**Decision**:
1. **Header-only streaming.** Each file is opened with `open_input`. Decompression stops when the
   header region ends, plus a bounded record sample: the first 1,000 records by default
   (`--record-limit`), used for RDA-R1.3-01D and for seqids. A multi-GB GFF3 therefore costs
   about the same as a small one. The FlyBase header (1,870 `##sequence-region` lines) is read
   whole, because the bound is in bytes: 16 MiB, the toolkit's `MAX_HEADER_BYTES`. A longer
   header is truncated, and the finding `header-truncated` lists the indicators that may be
   affected.
2. **Full reads only for related files** (US2: names, lengths, MD5, FHR checksum). Each related
   file is scanned once per run and cached by path and size, so one genome paired with many
   annotations is read once.
3. **Parallel files.** `--jobs N` (default: CPU count, at most 8) runs files in a process pool.
   Results are ordered by sorted relative path, so the output does not depend on scheduling.
4. **Benchmark.** `scripts/bench_assess.py` in the tool builds a synthetic 200-file release: 120
   annotations and variant files of 50–500 MB each, gzip and BGZF, plus 10 genomes of 100 MB for
   pairing. The scale was chosen to resemble an Alliance release. The benchmark asserts a wall
   time under 600 s and records the machine in its output. Budget: under 1 s per header-only
   file, and under 60 s per 100 MB genome scan with MD5 and SHA-512/256.

**Rationale**: Header-only reading makes the run time independent of body size. Only pairing
needs full reads, and those are cached.

**Alternatives considered**:
- *Reading whole files.* Rejected: multi-GB GFF3 and dbSNP files would exceed the budget.
- *Indexed random access (BGZF `.gzi`).* Unnecessary: the header is at the start of the file.
- *Threads.* Rejected: gzip decompression and hashing are CPU-bound, and the GIL would limit
  them; processes avoid that.

## R-15. Compression, archives, binary and unknown formats (edge cases)

**Decision**:
- gzip and BGZF are detected by magic bytes and streamed (toolkit `open_input`).
- A tar archive inside gzip (`ustar` at offset 257 of the decompressed stream) gives a file-level
  `not_assessed` (`archive-not-supported`), with a suggestion to publish a plain `.gff.gz`. This
  is the FlyBase case.
- These binary formats are detected by magic bytes and get a file-level `not_assessed`
  (`binary-format-out-of-scope`):
  - BAM: the decompressed stream starts `BAM\1`;
  - CRAM: `CRAM`;
  - BigWig: `0x888FFC26`;
  - BigBed: `0x8789F2EB`;
  - other files with NUL bytes in the first 64 KiB.
- An unknown text format uses the generic comment detection from R-02. Its header lines are
  reported as unrecognised comment lines, and the indicators are evaluated on what was
  recognised.
- Header bytes that are not valid UTF-8 give a finding `undecodable-line`, and those lines are
  not interpreted.

None of these cases is an error exit. Only unreadable paths, corrupt gzip and I/O failures are
errors.

**Rationale**: These are the spec's edge cases and the survey irregularities. Reporting something
we cannot handle is better than guessing at it (toolkit constitution III).

**Alternatives considered**:
- *Reading inside tar archives.* Deferred: archives can hold several members, which raises the
  question of what "the file" is.
- *An error exit for a binary file.* Rejected: a release scan would stop on the first BAM.

## R-16. Batch mode and summary (US4)

**Decision**: `bioheaders assess DIR` (with `--recursive`, `--include` and `--exclude` globs)
writes the following into `--output OUT`:
- for every file, `<relative path>.assessment.json` and `<relative path>.assessment.md`;
- `summary.json` and `summary.md`;
- `summary.tsv`: one row per file, with the format and the status of each assessed indicator,
  written as symbols (`E`, `P`, `N`, `NA`, `NAS`);
- per-indicator counts across files, for example "RDA-R1.1-01M: evidenced in 0 of 200 files";
- a list of the inputs that could not be assessed.

There is **no per-file total or score** (FR-004). Pairs come from `--pairs pairs.tsv`, a two-column
TSV of derived and related paths, relative to the input directory.

To track improvement between releases, run the tool on both releases and compare the two
`summary.tsv` files by row. The format is stable, so `diff` works.

**Rationale**:
- US4 asks for a summary across files plus per-file reports.
- Per-indicator counts show progress without becoming a score.
- An explicit pairs file avoids guessing which genome goes with which file, which FAIR-bioHeaders-Specification
  constitution IV forbids.

**Alternatives considered**:
- *Automatic pairing by file name.* Rejected as a guess; it may be offered later as a
  *suggested* pairs file.
- *A per-file "percentage evidenced".* Rejected: it is a score (FR-004).

## R-17. Guideline structure (US3, FR-007)

**Decision**: Adopt B §5.C. The guideline `docs/FAIR_HEADER_GUIDELINE.md` has 8 items:
1. identify this file;
2. describe it for discovery;
3. declare the format and header convention, with versions;
4. use identifiers, not labels;
5. say what this file was derived from, and how;
6. record provenance;
7. state a standard licence;
8. say where to get the data.

Each item gives:
- the RDA indicator ids and the FAIR principle it serves;
- the shared-core field name (`schemas/core.yaml`, for example `derivedFrom`, `reuseConditions`,
  `taxon`, `dateCreated`);
- examples in at least two conventions, drawn from real surveyed files where one exists (for
  example `#!genome-build-accession NCBI_Assembly:GCF_000002985.6`) and from FHR, GFF3 `#!`,
  VCF `##` and GAF `!`;
- the assessment check id(s) that test it.

A final section, "Out of scope for headers", lists the 10 not-applicable indicators with the
repository-level action for each. The RDA attribution (R-19) appears once.

**Rationale**: This meets US3 scenarios 1 and 2 and FR-007, and keeps the guideline to one short
document.

**Alternatives considered**: See B §5.C: one section per indicator, per principle, or per file
type.

## R-18. Fixtures and the SC-001 corpus

**Decision**: The shared fixtures live in FAIR-bioHeaders-Specification `assessment/`:
- `headers/`: the raw captured header lines of the A §R3 corpus. These are 17 files, a superset
  of the five required providers and four types. The survey's `# SOURCE-URL`/`# FETCHED` lines
  are removed, and the provenance moves to the manifest (`source_url`, `fetched`).
- `pairs/`: small synthetic genome and annotation pairs. The sequences are synthetic, but the
  names and lengths follow WBcel235. The pairs cover:
  - a correct pair with an FHR checksum link;
  - a version-mismatch pair (checksum of a different genome version);
  - an accession-only pair (unverifiable plus consistent);
  - a WormBase-style pair with no link (circumstantial only);
  - a GenBank-vs-RefSeq names pair (`inconsistent`, with missing names listed);
  - a partial pair (some names missing, one length differs);
  - a VCF `##contig md5=` pair with one wrong MD5.
- `edge/`:
  - a header-less FASTA;
  - gzip and BGZF copies;
  - a tar.gz;
  - a BAM magic stub;
  - FHR plus `##` directives in one file;
  - an unknown convention;
  - an identifier in free text;
  - a malformed checksum;
  - a too-long header;
  - non-UTF-8 bytes.
- `manifest.json`: per fixture, the expected statuses for the indicators it exercises, the pair
  classification, link verdicts and findings, using implementation-neutral ids (schema
  `assessment/manifest.schema.json`).

`scripts/make_assessment_fixtures.py` generates the synthetic fixtures deterministically (gzip
`mtime=0`). The real captures are copied, not generated. `.gitattributes` gains
`assessment/** -text`.

**Rationale**: A §R3. No network in CI. The expected outcomes are language-neutral, as in
`conformance/`.

**Alternatives considered**:
- *Whole real files in CI.* Rejected: too large, and the network is not reproducible.
- *Fixtures only in the tool repository.* Rejected: other implementations (009, the website)
  could not use them.

## R-19. RDA attribution and licensing

**Decision**: New code, data files, documents and fixtures are under **MPL-2.0** (CONTRIBUTING.md,
"License of contributions"; the toolkit AGENTS.md licensing policy of 2026-10-09). Quoted RDA
indicator titles and paraphrased descriptions are under **CC BY 4.0**. They carry this
attribution in `rubric.json` (`attribution`), in every JSON report (`attribution`), in the
guideline and in the `--help` epilogue of `assess`:

> Indicator identifiers and titles from: FAIR Data Maturity Model Working Group (2020). FAIR
> Data Maturity Model. Specification and Guidelines. Research Data Alliance.
> doi:10.15497/rda00050. Licensed CC BY 4.0
> (https://creativecommons.org/licenses/by/4.0/). File-header interpretations are adaptations by
> FAIR-bioHeaders and are not endorsed by the RDA.

Only the short titles are quoted verbatim; the descriptions are paraphrased. F-UJI, FAIRMetrics
and FAIR-Checker are cited, never copied.

Survey header excerpts are short factual metadata lines from public download files, used as test
fixtures with source URLs.

**Rationale**: B §4. CC BY 4.0 allows adaptation with attribution and an indication of changes,
and MPL-2.0 files can carry CC BY material with its notice.

**Alternatives considered**:
- *Copying the full RDA descriptions.* Allowed, but rejected: the reports would get long.
- *Leaving the attribution only in the guideline.* Rejected: machine-readable reports travel
  without it.

## R-20. Bounded resources on untrusted input

**Decision**: Every input is untrusted (toolkit constitution III). The tool enforces these limits:
- Header bytes are capped at 16 MiB per file.
- One line is capped at 1 MiB. A longer line is truncated in evidence, with the finding
  `line-too-long`.
- The record sample is capped by `--record-limit`.
- Related-file scans use constant memory apart from the name and length table.
- Duplicate-key and ambiguous FAIR-bioHeaders headers are reported as invalid under conformance,
  never reinterpreted.

Native conventions are tolerant by design, because the survey shows real irregularities. Each
irregularity is a reported *finding*, not a silent repair. An assessment never modifies its
input.

**Rationale**: The assessment must report on imperfect files (US1 scenario 2: a file with no
header is not an error). Fail-closed applies to *interpretation*: nothing ambiguous is credited.
It does not mean refusing to report.

**Alternatives considered**: *Rejecting irregular native headers with an error.* Rejected: it would
fail 4 of the 5 required providers (A §3.7).

## R-21. Validating SC-001 and SC-005

**Decision**:
- **SC-001**: For the 17 corpus files, a reviewer who is not the implementer checks each reported
  status against the cited lines and the rubric text. The reviewer records agree or disagree in
  `assessment/review/sc001-<date>.tsv` in FAIR-bioHeaders-Specification. The criterion is met at ≥ 90%
  agreement over the statuses of the offline-assessed indicators.
- **SC-005**: A maintainer asks a provider, the Alliance first, to run the quickstart on one
  release and report back. Contacting the provider is a maintainer action; a task list does not
  authorise it.

**Rationale**: These criteria involve people, not tests. Writing the agreement table to the
repository makes the result auditable.

**Alternatives considered**: *A self-review by the implementer.* Rejected: it is not independent.

---

## Technical Context unknowns: resolution index

| Technical Context item | Resolved by |
|---|---|
| Where code, guideline, data and fixtures live | R-01 |
| Recognised conventions / format detection | R-02, R-15 |
| Indicator set and statuses | R-03, R-04, R-05 |
| Related-file link model and verification | R-06, R-07, R-08 |
| FHR conformance and schema authority | R-09 |
| Network behaviour | R-10 |
| Suggestion generation | R-11 |
| Output formats, reproducibility | R-12, R-16 |
| Data file formats | R-13 |
| Performance goal | R-14 |
| Resource bounds / untrusted input | R-20 |
| Licensing and attribution | R-19 |
| Testing / fixtures / success-criteria validation | R-18, R-21 |

No NEEDS CLARIFICATION remains. Four open questions for the maintainers are listed in
[plan.md](plan.md#open-questions-for-maintainers). None of them blocks the MVP.
