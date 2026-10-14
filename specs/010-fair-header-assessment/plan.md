# Implementation Plan: FAIR header assessment for specified and unspecified file types

**Branch**: `010-fair-header-assessment` (work branch `specs/fair-header-assessment`) | **Date**: 2026-10-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-fair-header-assessment/spec.md` (clarified 2026-10-10)

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Data providers get a way to see how FAIR the headers of their existing download files are. It
works for files of any common text type, without first adopting a new header format. The work
has three parts in two repositories:

1. **Guideline** (FAIR-bioHeaders-Specification, `docs/FAIR_HEADER_GUIDELINE.md`). This is guidance, with no
   normative force. It has 8 items, each mapped to RDA FAIR Data Maturity Model indicators and
   FAIR principles. Each item uses the shared-core field names and gives examples in at least two
   conventions (US3).
2. **Assessment** (FAIR-bioHeaders-Tools, `bioheaders assess`). An offline-by-default subcommand
   that reuses the toolkit's streaming gzip/BGZF reader and its FHR header reader. It reads the
   header region of FASTA, GFF3, GAF, VCF, GFA and unknown text files. It maps the keys to
   concepts through a versioned synonym table, and it evaluates all 41 RDA indicators from a
   versioned rubric. The result has five statuses (`evidenced`, `partially evidenced`,
   `not evidenced`, `not applicable`, `not assessed`), each with the cited lines and a
   suggestion. Recorded links to related data are kept separate from circumstantial name and
   length consistency, and the recorded links can be verified against a supplied genome (US1,
   US2). The tool writes human-readable and JSON reports, and in batch mode a release summary
   (US4). There is never a score.
3. **Shared fixtures** (FAIR-bioHeaders-Specification, `assessment/`). Real provider header captures from the
   Phase 0 survey, plus synthetic pairs and edge cases, with implementation-neutral expected
   outcomes and a runner modelled on `check_conformance.py`.

All design decisions, with their alternatives, are in [research.md](research.md) (R-01 to R-21).

## Technical Context

**Language/Version**: Python 3.9–3.13. This matches FAIR-bioHeaders-Tools, whose gates run on 3.9
and 3.13. FAIR-bioHeaders-Specification scripts and tests run on 3.13, as in the existing CI.

**Primary Dependencies**: The standard library, plus the toolkit's existing `jsonschema`
(validating the report, rubric and synonym files) and `PyYAML` (for FHR headers only). **No new
runtime dependency.** Online checks use `urllib` (research R-10).

**Storage**: Files only. Versioned JSON data files are shipped in the wheel
(`bioheaders/assess/data/`), and reports are written to `--output` (research R-12, R-13).

**Testing**:
- Toolkit: `pytest` (files `tests/*_test.py`), with sockets disabled in the assessment tests.
- FAIR-bioHeaders-Specification: `unittest` (`tests/test_*.py`), plus the fixture runner
  `scripts/check_assessment.py`.

**Target Platform**: Laptops and pipeline nodes running Linux, macOS or Windows. Providers run the
tool themselves; there is no hosted service (spec Assumptions).

**Project Type**: A CLI subcommand and library module inside an existing package, plus a
documentation page and a fixture set in the specification repository.

**Performance Goals**: SC-004: 200 files in under 10 minutes on a laptop. The design reads only
the header and a sample of up to 1,000 records per file, reads each related genome once, and uses
a process pool (research R-14). Budget: under 1 s per header-only file, and under 60 s per
100 MB genome scan.

**Constraints**:
- Offline by default; file contents are never sent anywhere (FR-010, FR-011).
- Reproducible, byte-identical reports (FR-009).
- At most 16 MiB of header per file and 1 MiB per line, and a related file is streamed (research
  R-20).
- No score (FR-004).
- RDA text under CC BY 4.0, with attribution (research R-19).
- MPL-2.0 for new work.

**Scale/Scope**:
- Text formats only. Binary formats and archives are reported as out of scope (spec
  Assumptions, research R-15).
- Six header conventions are recognised (research R-02).
- 41 indicators: 25 evaluated offline, 4 online and opt-in, 10 not applicable, 2 deferred
  (research R-03).
- A release has hundreds of files; SC-004 benchmarks 200.

All the unknowns in this context are resolved in [research.md](research.md#technical-context-unknowns-resolution-index).
No NEEDS CLARIFICATION remains.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Both constitutions are **draft** (0.1.0, ratification pending David and Adam). The gates are
applied as written.

### FAIR-bioHeaders-Specification constitution (`.specify/memory/constitution.md`)

| Principle | Gate question | Pre-research | Post-design (re-check) |
|---|---|---|---|
| I. The published JSON schema is the contract | Does the feature change `fhr.json`, the LinkML files or the converter copies? | **Pass**. No schema change. The guideline is guidance and reuses `schemas/core.yaml` slot names without changing them | **Pass**. The design adds `docs/FAIR_HEADER_GUIDELINE.md`, `assessment/`, `scripts/check_assessment.py` and tests. `fhr.json`, `fhr_linkml.yml`, `schemas/core.yaml` and `Diagram.svg` are untouched. FR-008 conformance validates against `fhr.json` through the toolkit's byte-identical bundled copy, recording the canonical raw-main URL (research R-09; spec#44, website#15) |
| II. Compatibility before tightening | Could valid metadata become invalid? | **Pass**. Nothing is tightened. The assessment reports and never validates new constraints | **Pass**. The guideline's suggested keys are optional advice, and FHR validity is unchanged. The cited schema version is honoured, and an unbundled version gives `unsupported-schema-version`, never a silent use of main (spec#44) |
| III. Preserve user data and identity bytes | Are hashed bytes and metadata lines unambiguous? Does every parsing rule have a conformance example? | **Pass**, with an obligation: every native-convention parsing rule needs a fixture | **Pass**. The FHR checksum is computed only by the existing toolkit code (docs/FORMAT.md). SeqCol is compared as a *stated* identifier, never computed or treated as a checksum (research R-07). Every parsing rule in research R-02 and R-15 has a fixture in `assessment/headers` or `assessment/edge` (tasks.md). The assessment never modifies its input |
| IV. No invented metadata | Could the tool or the guideline fabricate values? | **Pass**, with an obligation: the suggestion values must have a stated source | **Pass**. A suggestion takes its values from the file, the related file, or a labelled `<placeholder>`. File-name values are marked "confirm before use". A file-name match is never a recorded link (research R-07, R-11). The rubric schema and a tool test forbid literal identifiers in templates. The guideline's real examples cite their survey source |
| V. Minimal and interoperable | Are new dependencies and frameworks avoided? Is stripping still trivial? | **Pass**. No new dependency and no new package | **Pass**. Data-driven rules with a small named-check escape hatch, not a rule DSL (research R-13). The guideline has 8 items, not 41. The suggestions favour each file's *existing* convention (FR-003), so headers stay easy to strip. The fixture format mirrors `conformance/` |
| Verification gates | Are they named? | Yes, see below | Yes, plus the new `check_assessment.py` |
| Decision boundaries | Does anything here need maintainer authority? | Rubric location, SeqCol computation, guideline key advice and the schema-version bundling policy are raised as open questions. SC-005 provider outreach and any release are maintainer actions | Unchanged. No task publishes, releases or contacts a provider |

**FAIR-bioHeaders-Specification verification gates** (repository root):

```bash
python -m unittest discover -s tests -v          # includes test_assessment_fixtures.py, test_assessment_guideline.py
python scripts/validate_examples.py
python scripts/check_linkml.py
python scripts/check_schema_drift.py
python scripts/check_conformance.py --schema     # unchanged; assessment/ is outside conformance/
python scripts/check_release.py --converter ../FHR-File-Converter
python scripts/check_assessment.py --tool ../FHR-File-Converter   # new
```

### FAIR-bioHeaders-Tools constitution (`origin/main:.specify/memory/constitution.md`)

| Principle | Gate question | Pre-research | Post-design (re-check) |
|---|---|---|---|
| I. The specification is the contract | Is the behaviour defined in FAIR-bioHeaders-Specification first? Are the schema copies byte-identical? | **Pass**. This plan, the spec, the guideline and the shared fixtures define the behaviour in FAIR-bioHeaders-Specification before the toolkit implements it | **Pass**. The report schema design source is `contracts/` here, and the toolkit copy is byte-identical (a test checks this against a checkout). All three `fhr_schema.json` copies are untouched. The rubric is the one artefact that lives only in the toolkit (open question 1). The guideline carries the same interpretations, and a cross-repository check compares their ids |
| II. Exact bytes and one reading | Do all commands identify metadata from the same lines? | **Pass**, with an obligation: reuse the FHR reader | **Pass**. `assess` reads FAIR-bioHeaders lines with `sequence_parts` and `header_lines`, the same functions `validate` and `verify` use. The checksum comes from the existing `checksum()`. Nothing is normalised in the input. The synonym normalisation applies only to *key matching*, and the raw line is kept as evidence |
| III. Fail closed on untrusted input | Is ambiguous input rejected? Is resource use bounded? | **Justified deviation** (Complexity Tracking): native headers are irregular in 4 of the 5 required providers (survey §3.7). They are *reported*, not rejected | **Pass with justification**. Ambiguity is never *credited*: a duplicate-key or alias FHR header is `invalid` under conformance and contributes no evidence, an identifier in free text gets no credit, and conflicting values cap the status. The resource bounds are 16 MiB of header, 1 MiB per line, a record limit, streamed related files and bounded online requests, with private addresses refused and the header schema URL never fetched (research R-10, R-20) |
| IV. Preserve metadata and typed values | Do round trips keep their values? | **N/A**. `assess` is read-only and does no conversion | **Pass**. The report JSON keeps typed values (integers stay integers), absent optional values are omitted or explicitly null as the schema says, and the Markdown output escapes the cited lines |
| V. Compatible, small, tested | Is the public API intact? Are dependencies small? Are tests shipped? | **Pass**. One new subcommand; no new `fhr-*` entry point; no new dependency | **Pass**. The existing commands and entry points are unchanged. The tests come first in every story (tasks.md). The new Python API `bioheaders.assess` is documented as provisional. The data files are included in the wheel, and the installed wheel is tested from outside the checkout |
| Verification gates | Are they named? | Yes, see below | Yes |
| Decision boundaries | | The package release and DOI are maintainer actions | Unchanged |

**FAIR-bioHeaders-Tools verification gates** (Python 3.9 and 3.13):

```bash
poetry install
poetry run pytest                      # includes tests/assess_*_test.py with sockets disabled
poetry run ruff check .
poetry run isort . --check-only
poetry run black . --check
poetry build
python -m build compat/fhr
# installed-wheel check from outside the checkout (sequence-tool rule): bioheaders assess on a fixture
python scripts/bench_assess.py --files 200    # SC-004, run manually or in a scheduled job
```

**Gate result**: PASS. One deviation is justified (toolkit III, tolerant reporting on native
headers), and it is recorded in Complexity Tracking. The re-check after design is also PASS
(the "Post-design" columns above).

## Project Structure

### Documentation (this feature)

```text
specs/010-fair-header-assessment/
├── spec.md                         # Feature spec (clarified)
├── plan.md                         # This file
├── research.md                     # Phase 0: decisions R-01..R-21
├── research/
│   ├── survey.md                   # Appendix A: 34 provider files
│   ├── rda-indicators.md           # Appendix B: 41 RDA indicators for file headers
│   └── headers/                    # Captured header lines (evidence)
├── data-model.md                   # Phase 1: entities, fields, status rules
├── quickstart.md                   # Phase 1: provider walkthrough + validation scenarios
├── contracts/
│   ├── assessment-report.schema.json   # Report format (JSON Schema 2020-12)
│   ├── rubric.schema.json              # rubric.json format
│   ├── synonyms.schema.json            # synonyms.json format
│   ├── data-files.md                   # Data files, reference tables, fixture manifest, pairs TSV
│   └── cli.md                          # bioheaders assess: options, outputs, exit codes
├── checklists/
│   ├── requirements.md             # Spec quality checklist
│   └── traceability.md             # FR/SC → tasks trace (from /speckit-tasks)
└── tasks.md                        # Phase 2 (/speckit-tasks)
```

### Source Code (both repositories)

```text
FAIR-bioHeaders-Specification/                          (this repository)
├── docs/
│   └── FAIR_HEADER_GUIDELINE.md            # US3 guideline (guidance only; 8 items + out-of-scope)
├── assessment/                             # Shared fixtures (conformance-style, implementation-neutral)
│   ├── README.md
│   ├── manifest.json                       # expected statuses/links/verdicts per fixture
│   ├── manifest.schema.json
│   ├── pairs.tsv                           # pairs for the batch fixture run
│   ├── headers/                            # 17 real header captures (survey R3 corpus), provenance in manifest
│   ├── pairs/                              # synthetic genome/annotation pairs (US2, SC-003)
│   ├── edge/                               # header-less, gzip, BGZF, tar.gz, BAM stub, mixed, unknown, malformed...
│   └── review/                             # SC-001 reviewer agreement tables
├── scripts/
│   ├── make_assessment_fixtures.py         # deterministic generator for pairs/ and edge/
│   └── check_assessment.py                 # runs `bioheaders assess` over the fixtures (--tool PATH)
├── tests/
│   ├── test_assessment_fixtures.py         # manifest schema, every file listed, generator deterministic
│   └── test_assessment_guideline.py        # guideline items ↔ rubric ids, ≥2 conventions, core fields exist
├── .gitattributes                          # + assessment/** -text, assessment/**/*.gz binary
└── README.md, CHANGELOG.md                 # links to guideline and fixtures

FAIR-bioHeaders-Tools/                      (local checkout ../FHR-File-Converter)
├── bioheaders/
│   ├── cli.py                              # + Subcommand("assess", ...) in SUBCOMMANDS
│   └── assess/
│       ├── __init__.py                     # assess_file(), assess_release() (provisional API)
│       ├── model.py                        # dataclasses: InputFile, HeaderEvidence, IndicatorResult, ...
│       ├── data.py                         # load + validate rubric/synonyms/reference tables, versions
│       ├── sniff.py                        # compression/format/binary/archive detection
│       ├── conventions.py                  # header-region readers: fhr, gff3, gaf, vcf, fasta defline, generic
│       ├── synonyms.py                     # key normalisation, concept + value-form matching
│       ├── rubric.py                       # status derivation (data-model §5), named checks
│       ├── suggestions.py                  # suggestion rendering per convention, value sources
│       ├── links.py                        # recorded links, ranking, verification against related file
│       ├── related.py                      # streaming related-file scan (names, lengths, MD5, FHR checksum), cache
│       ├── circumstantial.py               # name/length comparison, pair classification
│       ├── conformance.py                  # FR-008 via existing validator; schema provenance
│       ├── online.py                       # opt-in resolver (urllib), only imported with --online
│       ├── render.py                       # JSON (sorted, LF), text, Markdown renderers
│       ├── batch.py                        # directory walk, process pool, summary.{json,md,tsv}
│       └── data/
│           ├── rubric.json, rubric.schema.json
│           ├── synonyms.json, synonyms.schema.json
│           ├── assessment-report.schema.json
│           └── reference/{spdx-licenses,id-schemes,formats}.json
├── tests/
│   ├── fixtures/assess/                    # small tool-local fixtures (copied subset + unit cases)
│   ├── conftest.py                         # blocks sockets for assess_*_test.py (except online_local)
│   ├── assess_data_test.py                 # data files valid, 41 indicators, concepts/forms resolve
│   ├── assess_sniff_test.py                # compression/format/binary/archive detection
│   ├── assess_conventions_test.py          # US1 parsing per convention
│   ├── assess_rubric_test.py               # status rules, caps, reasons
│   ├── assess_conformance_test.py          # FR-008 conformance section, schema provenance
│   ├── assess_report_test.py               # schema validity, determinism, no-score wording
│   ├── assess_suggestions_test.py          # SC-002 proxy: applying a suggestion raises the status
│   ├── assess_links_test.py                # US2 links, verification, circumstantial, classification
│   ├── assess_cli_test.py                  # options, exit codes, stdin, output files
│   ├── assess_batch_test.py                # US4 summary, ordering, re-run identity
│   └── assess_online_test.py               # opt-in only; local test server; refused schemes/addresses
├── scripts/bench_assess.py                 # SC-004 synthetic 200-file benchmark
├── pyproject.toml                          # include bioheaders/assess/data/**; no new deps
├── README.md, CHANGELOG.md                 # assess usage, RDA attribution
└── AGENTS.md                               # repository map: bioheaders/assess
```

**Structure Decision**: The work spans two existing repositories and creates no new project
(research R-01).
- The specification side (guideline, fixtures, fixture runner) lives in FAIR-bioHeaders-Specification under
  `docs/`, `assessment/`, `scripts/` and `tests/`.
- The behaviour lives in FAIR-bioHeaders-Tools as the subpackage `bioheaders/assess/`, which is
  registered as a `bioheaders` subcommand.
- The fixtures go in a top-level `assessment/` and not in `conformance/`, because
  `check_conformance.py` would treat a nested `manifest.json` as an unexpected generated file.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Toolkit III (fail closed): irregular native headers are reported, not rejected | US1 must report on files as they are today (spec "Why this priority"). Native header irregularities occur in 4 of the 5 required providers: a comment before `##gff-version`, `#!assembly:`, a hyphenated `fileDate`, three GAF date formats (survey §3.7). Ambiguity is still never *credited*, and FHR headers keep the strict reader | Rejecting irregular files with a nonzero exit would make the tool useless on the Alliance's own files (SC-005), and it would contradict US1 scenario 2 ("the report is not an error") |
| A process pool (`--jobs`) in batch mode | SC-004 (200 files in under 10 min) when pairing requires full genome scans with MD5 and SHA-512/256. Hashing and decompression are CPU-bound | A sequential run meets the budget for header-only files, but not for releases with several large genomes. Threads are limited by the GIL during decompression. The pool is a few lines of stdlib `concurrent.futures`, and the output order is fixed by sorting |

## Phase outputs

- **Phase 0**: [research.md](research.md). All unknowns are resolved, and appendices A and B are
  linked.
- **Phase 1**: [data-model.md](data-model.md), [contracts/](contracts/) (report schema, rubric
  and synonym schemas, data files, CLI) and [quickstart.md](quickstart.md). The constitution was
  re-checked after design (table columns above): PASS.
- **Phase 2**: [tasks.md](tasks.md) (from `/speckit-tasks`), with
  [checklists/traceability.md](checklists/traceability.md).

## Open questions for maintainers

None of these blocks the MVP (US1 and US2). The tasks follow the stated default until a
maintainer decides otherwise.

1. **Where the rubric lives.** The default is the toolkit (`bioheaders/assess/data/rubric.json`),
   with the guideline in FAIR-bioHeaders-Specification carrying the same interpretations and a
   cross-repository id check. The alternative is to publish the rubric in FAIR-bioHeaders-Specification
   (for example `assessment/rubric.json`) and have the toolkit vendor a byte-identical copy, as
   it does with `fhr.json`.
2. **Bundling several schema versions for FR-008.** Adam's proposal under spec#44 (2026-10-09),
   to bundle v0.3.1 and v0.4.0 and select one by the cited URL, awaits David's answer. The
   default until then is to bundle the current `fhr.json` only. A file that cites another
   version is reported `not_assessed (unsupported-schema-version)`. Nothing falls back silently.
3. **Computing SeqCol digests.** The default is to compare against the related file's *stated*
   `seqcol_id` only, and to report `unverifiable` otherwise. Should release 1 compute GA4GH
   SeqCol digests? That would need pinned GA4GH test vectors in `assessment/`.
4. **Advising core field names as native keys.** For example, should the guideline suggest
   `#!reuseConditions <SPDX id>` in GFF3, `##reuseConditions=` in VCF, and
   `!reuseConditions:` in GAF, where those conventions have no licence key? This is guidance,
   not a specification change, but it amounts to recommending key spellings to other
   communities.
5. **The provisional `derivedFrom` relationship vocabulary (#54).** Suggestions use `annotates`
   (and the other provisional values), and RDA-R1.2-02M stays at most partial until a PROV-O or
   RO mapping is decided.
