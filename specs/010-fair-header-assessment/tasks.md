---

description: "Task list for feature 010: FAIR header assessment"
---

# Tasks: FAIR header assessment for specified and unspecified file types

**Input**: Design documents from `/specs/010-fair-header-assessment/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: These are required. The toolkit constitution V says "Every behaviour change ships with
regression tests". The FAIR-bioHeaders-Specification constitution III says "every parsing rule needs a
conformance example". In every story the test tasks come first, and they must FAIL before the
implementation tasks start.

**Organization**: Tasks are grouped by user story, so each story can be implemented and tested
on its own. The FR/SC trace is in [checklists/traceability.md](checklists/traceability.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

The work spans two repositories, and every path starts with its repository name:

- **`FAIR-bioHeaders-Specification/`**: this repository. It holds the guideline, the shared fixtures and the
  fixture runner.
- **`FAIR-bioHeaders-Tools/`**: the `fair-bioheaders` package, with the `bioheaders` command.
  The local checkout is `../FHR-File-Converter`. It holds the assessment code, the data files and
  the tool tests.

Each repository gets its own PRs, cross-linked. No task publishes, releases, tags, archives a
DOI or contacts a provider; those are maintainer actions (both constitutions, "Decision
boundaries").

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package skeleton, the fixture directory and the test harness.

- [X] T001 Create the `FAIR-bioHeaders-Tools/bioheaders/assess/` package. Add an empty `__init__.py` (MPL-2.0 header) and the directories `data/` and `data/reference/`. Add `include = ["bioheaders/fhr_schema.json", "bioheaders/assess/data/**/*.json"]` to `FAIR-bioHeaders-Tools/pyproject.toml`. Add **no** new dependency
- [X] T002 [P] Create `FAIR-bioHeaders-Tools/tests/conftest.py` with an autouse fixture that makes `socket.socket.connect` raise for every test module named `assess_*_test.py`, except tests marked `@pytest.mark.online_local`. Create `FAIR-bioHeaders-Tools/tests/fixtures/assess/README.md`, which states the fixture origin (copied from FAIR-bioHeaders-Specification `assessment/`)
- [X] T003 [P] Create `FAIR-bioHeaders-Specification/assessment/` with `README.md` (purpose, layout `headers/`, `pairs/`, `edge/`, `review/`, and the MPL-2.0 notice), `headers/.gitkeep`, `pairs/.gitkeep`, `edge/.gitkeep` and `review/.gitkeep`. Append `assessment/** -text` and `assessment/**/*.gz binary` to `FAIR-bioHeaders-Specification/.gitattributes`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data files, the data model, input sniffing, JSON output, and the fixture manifest
and runner. Every story needs these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for the foundation (write first, must fail)

- [X] T004 [P] Write `FAIR-bioHeaders-Tools/tests/assess_data_test.py`. It asserts that:
  - `rubric.json`, `synonyms.json` and the three reference tables validate against their schemas;
  - the rubric has "exactly 41 indicators, with unique ids equal to the RDA Table 1 set", of which "25 are `offline`, 4 `online`, 10 `not_applicable` and 2 `deferred`";
  - every `concept` and `form` referenced in the rubric exists in `synonyms.json`;
  - no suggestion template contains a literal accession, SPDX id, ORCID or date outside `<…>`;
  - `rubric.attribution` matches `10\.15497/rda00050`;
  - `bioheaders/assess/data/assessment-report.schema.json` is byte-identical to `../FAIR-bioHeaders-Specification/specs/010-fair-header-assessment/contracts/assessment-report.schema.json`. This check is skipped when that checkout is absent
- [X] T005 [P] Write `FAIR-bioHeaders-Specification/tests/test_assessment_fixtures.py` (unittest). It asserts that `assessment/manifest.json` validates against `assessment/manifest.schema.json`, and that "every file under `assessment/headers`, `pairs` and `edge` is listed once". It also asserts that real captures carry `source_url` and `fetched`, that synthetic files carry `generator`, and that `scripts/make_assessment_fixtures.py --output DIR` run twice gives byte-identical trees
- [X] T006 [P] Write `FAIR-bioHeaders-Tools/tests/assess_sniff_test.py`. It covers:
  - gzip and BGZF detected by magic bytes, whatever the extension (dbSNP has no `.vcf`);
  - a tar archive inside gzip gives `format: archive`;
  - the BAM, CRAM, BigWig and BigBed magic numbers give `binary`;
  - NUL bytes in the first 64 KiB give `binary`;
  - `--type` overrides the detection, and `format_source` takes the values `content`, `extension` and `option`

### Implementation for the foundation

- [X] T007 [P] Copy `contracts/assessment-report.schema.json`, `contracts/rubric.schema.json` and `contracts/synonyms.schema.json` byte-for-byte to `FAIR-bioHeaders-Tools/bioheaders/assess/data/`
- [X] T008 [P] Create the pinned reference tables in `FAIR-bioHeaders-Tools/bioheaders/assess/data/reference/`. Each has the shape `{table, version, source, retrieved, entries}` ([contracts/data-files.md §3](contracts/data-files.md)):
  - `spdx-licenses.json`: the full SPDX list at one tagged release, with entries `{id, url, deprecated}`;
  - `id-schemes.json`: the prefixes taxonomy, orcid, ror, doi, so, go, eco, insdc.gca, refseq.gcf, ena.embl, bioproject and biosample, with entries `{prefix, pattern, persistent, resolver}`;
  - `formats.json`: fasta, gff3, gaf, vcf and gfa, with entries `{format, fairsharing, version_directive, versions}`.

  Record the real versions and retrieval dates. Do not copy the illustrative ones in the contract
- [X] T009 Create `FAIR-bioHeaders-Tools/bioheaders/assess/data/synonyms.json` (`synonyms_version` 1.0.0). Include:
  - the normalisation `{casefold, fold_separators ["-","_"," "], split_camel_case, strip_trailing_colon}`;
  - the forms (`insdc-assembly-accession`, `spdx-id`, `taxonomy-iri`, `orcid`, `doi`, `iso-date`, `vcf-date`, `md5`, `fhr-checksum`, `seqcol-digest`, `url`, `directory-url`);
  - concepts covering **every key in [research/survey.md §4](research/survey.md)**.

  Each concept has `keys`, `forms`, `scope`, `core_field` (slot names from `FAIR-bioHeaders-Specification/schemas/core.yaml`), `link_kind`, `relationship` and `emit`. Mark `INFO`, `FORMAT`, `FILTER`, `ALT`, `ID` and `phasing` as structural
- [X] T010 Create `FAIR-bioHeaders-Tools/bioheaders/assess/data/rubric.json` (`rubric_version` 1.0.0) with all 41 indicators, in RDA Table 1 order. For each:
  - the verbatim RDA short `title`;
  - `principle`, `priority` and `target`;
  - `assessability` and `reason`, following research R-03. RDA-I3-01D and RDA-I3-02D are `deferred`/`deferred-data-body`;
  - an `interpretation` paraphrased from [research/rda-indicators.md §2](research/rda-indicators.md) and marked "Adapted";
  - `conditions`, `evidenced_when` and `partial_when`, following B §3 rule 3 and research R-05. RDA-I1-01D, RDA-R1.3-01D and RDA-R1.3-02D need a *declared* format;
  - `check`;
  - `online_upgrade`, which is true for RDA-F1-01D, RDA-I2-01M and RDA-R1.1-03M;
  - `guideline_item` (G1–G8, or `out-of-scope`);
  - suggestion templates for `fair-bioheaders`, `gff3-pragma`, `vcf-meta` and `gaf`, using only `{value}`, `{related.*}` or `<placeholder>`.

  Add the `source` and `attribution` blocks from research R-19
- [X] T011 Implement `FAIR-bioHeaders-Tools/bioheaders/assess/data.py`. It loads the five data files with `importlib.resources`, validates them against the bundled schemas with `jsonschema` (failing loudly), exposes `rubric_version`, `synonyms_version` and `reference_versions`, and caches the result per process (depends on T007–T010)
- [X] T012 [P] Implement the dataclasses in `FAIR-bioHeaders-Tools/bioheaders/assess/model.py` following [data-model.md](data-model.md) §1–§14. Use Python 3.9-compatible syntax (no `slots=`, no `match`). The classes are `InputFile`, `HeaderEvidence`, `IndicatorResult`, `Finding`, `Suggestion`, `RelatedFileLink`, `LinkVerification`, `CircumstantialCheck`, `ConformanceResult`, `OnlineCheck` and `AssessmentReport`, each with `to_json()`. Enforce in `__post_init__`:
  - "`reason` required iff the status is `not_applicable` or `not_assessed`";
  - "`suggestion` required iff the status is `partially_evidenced` or `not_evidenced`";
  - "evidence non-empty iff the status is `evidenced` or `partially_evidenced`"
- [X] T013 [P] Implement `FAIR-bioHeaders-Tools/bioheaders/assess/sniff.py`. It reuses `bioheaders.cli.open_input` for gzip/BGZF streaming, distinguishes gzip from BGZF by the `BC` extra subfield, and returns `(compression, format, format_source, scope)`. It detects tar (`ustar` at offset 257) and binary magic numbers, and never reads past 64 KiB for sniffing (makes T006 pass)
- [X] T014 [P] Implement the JSON serialisation in `FAIR-bioHeaders-Tools/bioheaders/assess/render.py`: `to_json(report)` gives sorted keys, `ensure_ascii=False`, UTF-8, LF line endings, a trailing newline and no floats. It validates against `assessment-report.schema.json` before returning, and raises if the report does not conform
- [X] T015 [P] Write `FAIR-bioHeaders-Specification/assessment/manifest.schema.json` following [contracts/data-files.md §4](contracts/data-files.md). It defines `manifest_version`, `rubric_version`, and `fixtures[]` with `id`, `file`, `related`, `format`, `source_url`/`fetched` or `generator`, and `expected`. `expected` holds `statuses`, `links`, `findings`, `conformance`, `circumstantial`, `pair_classification` and `scope`
- [X] T016 Copy the 17 corpus files of [research/survey.md §R3](research/survey.md) from `specs/010-fair-header-assessment/research/headers/` to `FAIR-bioHeaders-Specification/assessment/headers/`, giving each its original extension (for example `ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff`). Remove the survey's `# SOURCE-URL`, `# FETCHED` and `# ----- captured header lines -----` lines and the `[ELIDED …]` notes, which must not stand in for real lines. Create `FAIR-bioHeaders-Specification/assessment/manifest.json` with one entry per file, giving `source_url`, `fetched` and `format`, and leave `expected` empty for now
- [X] T017 Implement `FAIR-bioHeaders-Specification/scripts/check_assessment.py`, modelled on `scripts/check_conformance.py`. It takes `--tool PATH` (a virtual environment, a checkout or commands on PATH). It runs `bioheaders assess --format json [--related R] FILE` for every manifest entry, validates the output against the tool's bundled report schema, and compares only the listed `expected` fields. It prints `ok: <id>` or a diff, and exits 1 on any difference

**Checkpoint**: Foundation ready. The data files load and validate, input sniffing works, the
JSON output conforms to the schema, and the fixture runner and manifest exist.

---

## Phase 3: User Story 1 - Assess the header of any data file (Priority: P1) 🎯 MVP

**Goal**: `bioheaders assess FILE` reports, for each of the 41 indicators, a status, the cited
header lines and a suggestion. It covers FASTA, GFF3, GAF, VCF, FAIR-bioHeaders and unknown
text, offline, and reports FHR schema conformance separately.

**Independent Test**: Run `python scripts/check_assessment.py --tool ../FHR-File-Converter` over
the 17 real captures from Alliance, WormBase, FlyBase, Ensembl, NCBI and GO (FASTA, GFF3, GAF and
VCF). Every expected status matches, and each cited line can be found in the file (quickstart
V1–V4).

### Tests for User Story 1 (write first, must fail) ⚠️

- [X] T018 [P] [US1] Fill `expected` in `FAIR-bioHeaders-Specification/assessment/manifest.json` for the 17 header fixtures, covering at least RDA-F1-01D, RDA-F2-01M, RDA-I1-01D, RDA-I2-01M, RDA-I3-02M, RDA-I3-04M, RDA-R1.1-01M, RDA-R1.2-01M, RDA-R1.3-01M, RDA-A1-03D (`not_assessed`/`online-check-not-requested`), RDA-A2-01M (`not_applicable`/`repository-level`) and RDA-I3-01D (`not_assessed`/`deferred-data-body`). Also list the expected `links` and `findings`, for example `format-irregularity` for Alliance WB line 1 and MGI `date-produced`, and the FlyBase `.gff.gz` as `scope: out_of_scope`/`archive-not-supported`
- [X] T019 [P] [US1] Extend `FAIR-bioHeaders-Specification/scripts/make_assessment_fixtures.py` to generate `FAIR-bioHeaders-Specification/assessment/edge/` deterministically (gzip `mtime=0`), and add the manifest entries. The fixtures are:
  - a FASTA with no header;
  - gzip and BGZF copies of one GFF3 fixture;
  - a GFF3 inside tar.gz;
  - a BAM magic stub;
  - FHR `#~` lines together with `##` directives in one GFF3;
  - an unknown text convention (`%`-comments);
  - an accession in a free-text `#` comment;
  - a malformed `derivedFrom.checksum` (43 characters);
  - two conflicting `#!genome-build-accession` values;
  - non-UTF-8 header bytes;
  - a valid FHR FASTA (a copy of `conformance/valid/fasta-lf.fhr.fasta`);
  - an FHT stub with no published schema.

  The expected outcomes follow [data-model.md §5](data-model.md). The FASTA with no header expects every `offline` indicator `not_evidenced`. The case of a header longer than 16 MiB is not committed. T020 generates it at test time in a temporary directory
- [X] T020 [P] [US1] Write `FAIR-bioHeaders-Tools/tests/assess_conventions_test.py`, with one test per parsing rule in research R-02/R-15:
  - GFF3 `##`, and `#!` with `key value` and `key: value` (`#!assembly:`);
  - a comment before `##gff-version`, kept as `unrecognised` with a `format-irregularity` finding;
  - the header ends at the first feature line or `##FASTA`;
  - all 1,870 `##sequence-region` lines read;
  - GAF first-block evidence `scope: file`, and later blocks `upstream-provenance`;
  - VCF `##contig=<…>` sub-fields parsed, and `##source=ensembl;version=116;url=…` split;
  - the FASTA first defline (Ensembl `chromosome:GRCh38:MT:…`, FlyBase `MD5=…;release=r6.69;`, WormBase `gene=`), all `scope: first-record`;
  - every header line yields exactly one `HeaderEvidence`;
  - `line-too-long` (over 1 MiB), `header-truncated` (over 16 MiB, generated in `tmp_path` and never committed) and `undecodable-line`.

  Use fixtures copied into `FAIR-bioHeaders-Tools/tests/fixtures/assess/`
- [X] T021 [P] [US1] Write `FAIR-bioHeaders-Tools/tests/assess_rubric_test.py`. It covers:
  - the status derivation order 1–9 of data-model §5;
  - the first-record cap and the conflicting-values cap;
  - "a malformed value satisfies nothing";
  - "upstream-provenance evidence is never used for file-level indicators";
  - identifier-in-free-text gets no credit;
  - the NCBI RefSeq GFF3 gives RDA-I3-04M `evidenced`, citing line 5 `#!genome-build-accession NCBI_Assembly:GCF_000002985.6` (US1 scenario 1);
  - a FASTA with no header gives every offline indicator `not_evidenced`, each with a suggestion, and no exception (US1 scenario 2);
  - "each of the 41 ids appears exactly once, in rubric order";
  - the `not_applicable` reasons are only `embedded-metadata`, `repository-level` or `object-in-hand`
- [X] T022 [P] [US1] Write `FAIR-bioHeaders-Tools/tests/assess_conformance_test.py`. It covers:
  - a valid FHR FASTA gives `conformance.result: valid`, `schema_used.canonical_url` equal to `https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/main/fhr.json`, and `bundled_sha256` equal to the SHA-256 of `bioheaders/fhr_schema.json`, kept separate from `results` (US1 scenario 3, FR-008);
  - a duplicate-key FHR header gives `invalid`, and its values are not used as FAIR evidence;
  - an FHT stub gives `not_assessed`/`unsupported-header-type`;
  - a cited schema version that is not bundled gives `not_assessed`/`unsupported-schema-version`, with no network access
- [X] T023 [P] [US1] Write `FAIR-bioHeaders-Tools/tests/assess_report_test.py`. It covers:
  - every report validates against the bundled schema;
  - two runs give byte-identical JSON and Markdown (FR-009);
  - the text and Markdown output never contains "score", "is FAIR" or "certified" (FR-004);
  - the attribution is present in the JSON and Markdown;
  - `online_checks == "not_requested"`, and no socket was opened (FR-010, FR-011);
  - the Markdown escapes the cited lines that contain `|`, `<` and backticks
- [X] T024 [P] [US1] Write `FAIR-bioHeaders-Tools/tests/assess_suggestions_test.py` as the SC-002 proxy. For each fixture and each `partially_evidenced`/`not_evidenced` result, it inserts `suggestion.line` (with placeholders filled from a test table) into a copy of the header and re-assesses. The indicator's status must not fall, and must rise for single-condition indicators. Every `value_source` is `file`, `related-file`, `placeholder` or `file-name`, and `file-name` suggestions contain "confirm before use"
- [X] T025 [P] [US1] Write the single-file tests in `FAIR-bioHeaders-Tools/tests/assess_cli_test.py`:
  - `--format text|markdown|json`;
  - `--output DIR` writes `<name>.assessment.json` and `.md` atomically;
  - `-` with `--type vcf` works, and `-` without `--type` exits 2;
  - a missing path exits 1;
  - corrupt gzip exits 1 with a `FHR: ` stderr message;
  - a binary or archive input exits 0 with `scope: out_of_scope`;
  - `--record-limit 0` reads the header only;
  - `--hash-inputs` adds `input.file_sha256`;
  - `--help` shows the RDA attribution;
  - the existing subcommands' help output is unchanged

### Implementation for User Story 1

- [X] T026 [US1] Implement the header-region readers in `FAIR-bioHeaders-Tools/bioheaders/assess/conventions.py`: FAIR-bioHeaders (through `bioheaders.sequence_parts`/`header_lines`, the same functions as `validate`/`verify`), GFF3 `##`/`#!`, GAF (first block and `upstream-provenance`), VCF meta and `##contig`, FASTA first defline, and generic comments. Each yields `HeaderEvidence`. Enforce "16 MiB header" and "1 MiB per line", and sample up to `--record-limit` records for seqids and RDA-R1.3-01D (depends on T012, T013; makes T020 pass)
- [X] T027 [US1] Implement `FAIR-bioHeaders-Tools/bioheaders/assess/synonyms.py`. It does the key normalisation (casefold, fold `-`, `_` and space, split camelCase, strip a trailing `:`), maps keys to concepts per convention, and matches value forms with `re.fullmatch` and reference-table lookups. It resolves one key to several concepts by form (VCF `reference` gives an accession, a URL or a name), and emits `identifier-in-free-text` findings (depends on T011)
- [X] T028 [US1] Implement the recorded-link extraction and ranking in `FAIR-bioHeaders-Tools/bioheaders/assess/links.py`, following research R-06. Kinds: `checksum`, `seqcol` and `sequence-digests` are rank 1, `accession` rank 2, `url` rank 3 and `name` rank 4. Set `relationship` from `derivedFrom.relationship` or the concept's documented `relationship`. Flag `well_formed: false` with a `malformed` finding, `conflicting-values` for same-kind conflicts, and `url-names-directory` for directory URLs. There is no verification yet (depends on T027)
- [X] T029 [US1] Implement `FAIR-bioHeaders-Tools/bioheaders/assess/conformance.py`. It detects the header type from `schema` against an allow-list (not a URL substring guess, per spec#44) and validates FHR with the existing `bioheaders.fhr` validator. It records `{canonical_url, bundled_sha256, version}`, and returns `not_assessed` with `unsupported-header-type` or `unsupported-schema-version`. It never fetches the URL (depends on T012; makes T022 pass)
- [X] T030 [US1] Implement the status derivation in `FAIR-bioHeaders-Tools/bioheaders/assess/rubric.py`, exactly following data-model §5 steps 1–9 ("Online results never lower a status reached in step 7 or 8"), with the named checks `format-declared`, `record-sample-parse`, `fhr-conformance` and `derived-link` (presence and rank only). Fill in `conditions_met` and `conditions_total` (depends on T026–T029; makes T021 pass)
- [X] T031 [US1] Implement `FAIR-bioHeaders-Tools/bioheaders/assess/suggestions.py`. It renders the rubric templates in the file's own convention: GFF3 uses `#!` with the native `emit` key, otherwise the core field name. VCF uses `##`, and GAF uses `!`. FASTA and other files without a header convention get a FAIR-bioHeaders `;~`/`#~` line, with a note that FHT and FHP are drafts. Every suggestion sets `value_source`, `file-name` values carry "from the file name; confirm before use", and values are never invented (depends on T030; makes T024 pass)
- [X] T032 [US1] Implement the text and Markdown renderers in `FAIR-bioHeaders-Tools/bioheaders/assess/render.py`. The sections, in order, are: input, online-checks line, conformance, checklist grouped F/A/I/R, recorded links, findings and attribution (contracts/cli.md "Outputs"). Escape Markdown, and never use the words in FR-004 (makes T023 pass)
- [X] T033 [US1] Implement `assess_file(path, related=None, online=False, record_limit=1000, hash_inputs=False)` in `FAIR-bioHeaders-Tools/bioheaders/assess/__init__.py`. It returns a plain dict that conforms to the report schema; out-of-scope and error inputs give every indicator `not_assessed` with the matching reason. Document the API as provisional
- [X] T034 [US1] Register `Subcommand("assess", …)` in `SUBCOMMANDS` in `FAIR-bioHeaders-Tools/bioheaders/cli.py`, with the options `--type`, `--format`, `--output`, `--record-limit` and `--hash-inputs`. Use the exit codes 0, 1 and 2 of [contracts/cli.md](contracts/cli.md) and atomic output (temporary file, then `os.replace`, like `write_output`), and put the RDA attribution in the help epilogue. Add no `fhr-*` entry point (makes T025 pass)
- [X] T035 [US1] Run `python scripts/check_assessment.py --tool ../FHR-File-Converter` from `FAIR-bioHeaders-Specification/`. Fix the tool, not the manifest, unless a reviewer agrees that the expectation was wrong, and record any expectation change with its reason in the commit message

**Checkpoint**: User Story 1 is fully functional. Any text file can be assessed offline into a
41-indicator checklist with evidence and suggestions. This is MVP part 1.

---

## Phase 4: User Story 2 - Check that an annotation matches its sequence file (Priority: P1) 🎯 MVP

**Goal**: `bioheaders assess --related GENOME ANNOTATION` verifies each recorded link (`match`,
`mismatch` or `unverifiable`, with a reason). It reports name and length consistency separately,
as circumstantial evidence, and lists the missing names.

**Independent Test**: The `assessment/pairs/` fixtures give the expected pair classification and
link verdicts for the correct, version-mismatch, partially matching, name-mismatch,
accession-only, no-link and VCF-MD5 pairs (SC-003, quickstart V5).

### Tests for User Story 2 (write first, must fail) ⚠️

- [X] T036 [P] [US2] Extend `FAIR-bioHeaders-Specification/scripts/make_assessment_fixtures.py` to generate `FAIR-bioHeaders-Specification/assessment/pairs/`. The sequences are synthetic, and the names and lengths are scaled-down WBcel235-style. Write `FAIR-bioHeaders-Specification/assessment/pairs.tsv`, and add the manifest entries with `related` and the expected `links[].verification.verdict`, `circumstantial` and `pair_classification`:
  - an FHR genome with an annotation whose `derivedFrom.checksum` is correct, expecting `recorded-match`;
  - the same annotation against a genome with one base changed (a different version), expecting `recorded-mismatch`;
  - an accession-only annotation against a FASTA with no header, expecting `unverifiable`/`related-file-states-no-identity` and `consistent-unverified`;
  - a WormBase-style annotation with no link, expecting `consistent-unverified`;
  - GenBank `BX284601.5`-style names against RefSeq `NC_003279.8`-style names, expecting `inconsistent` with the full sorted `missing_from_related`;
  - an annotation with one name missing and one length differing, expecting `partial`;
  - a VCF `##contig md5=` set with one wrong MD5, expecting `recorded-mismatch` with the differing names listed;
  - a malformed checksum, expecting `unverifiable`/`malformed`
- [X] T037 [P] [US2] Write `FAIR-bioHeaders-Tools/tests/assess_links_test.py`. It covers:
  - every verification method in research R-07: `computed-fhr-checksum`, `stated-fhr-checksum`, `stated-seqcol`, `computed-md5` (upper-cased, no whitespace) and `stated-identity`;
  - "`match` requires that the related file *states* or *computes to* the recorded value";
  - a file-name match gives only a `hints[]` entry and never `match`;
  - "a per-sequence digest set is `match` only if every compared sequence matches";
  - the circumstantial verdicts and `lengths_compared` ("Lengths that are not declared never lower the verdict");
  - the circumstantial section is never referenced by an `IndicatorResult` (FR-005);
  - the pair classification precedence in data-model §10;
  - a related file shared by two annotations is scanned once

### Implementation for User Story 2

- [X] T038 [US2] Implement `FAIR-bioHeaders-Tools/bioheaders/assess/related.py`. It streams the related FASTA, FHR FASTA or GFA once through `open_input` and `read_chunks`, and collects the sequence names, lengths and per-sequence MD5. It computes the FHR checksum with the existing `bioheaders.cli.checksum`, and collects the stated FHR `checksum`, `seqcol_id` and `accessionID`. It uses constant memory apart from the name table, and caches by `(path, size)` per process
- [X] T039 [US2] Add verification to `FAIR-bioHeaders-Tools/bioheaders/assess/links.py`. It gives `LinkVerification` objects with `verdict`, `reason` (required iff `unverifiable`: `malformed`, `related-file-states-no-identity`, `related-file-states-no-seqcol`, `related-file-unreadable` or `sequence-absent`), `expected`, `actual`, `method` and `hints` (depends on T038)
- [X] T040 [US2] Implement `FAIR-bioHeaders-Tools/bioheaders/assess/circumstantial.py`. It compares `##sequence-region`, VCF `##contig`, or else the sampled seqids, with the related names and lengths. It fills `missing_from_related` (complete and sorted), `length_mismatches`, `lengths_compared`, `not_declared_count` and `verdict`, and sets the label "circumstantial evidence, not a recorded link". It also computes `pair_classification` with the precedence `recorded-mismatch` > `recorded-match` > `inconsistent` > `partial` > `consistent-unverified` > `unknown` (makes T037 pass)
- [X] T041 [US2] Add the `--related FILE` and `--fail-on-mismatch` options (exit 3, which takes precedence over 0 but not over 1) to the `assess` subcommand in `FAIR-bioHeaders-Tools/bioheaders/cli.py`. Add the "Recorded links" verdicts and the "Circumstantial evidence (not a recorded link)" section to `FAIR-bioHeaders-Tools/bioheaders/assess/render.py`. Extend `FAIR-bioHeaders-Tools/tests/assess_cli_test.py` with exit-code-3 cases
- [X] T042 [US2] Extend `FAIR-bioHeaders-Specification/scripts/check_assessment.py` to pass `--related` for manifest entries that have `related` and to compare the `links`, `circumstantial` and `pair_classification` expectations. Run it over `assessment/pairs/` and fix the tool until every pair passes (SC-003)

**Checkpoint**: User Stories 1 and 2 both work on their own. **This is the MVP.** Providers can
assess files and check annotation-genome pairs.

---

## Phase 5: User Story 3 - Guidelines for file types not yet specified (Priority: P2)

**Goal**: One short guideline, `FAIR-bioHeaders-Specification/docs/FAIR_HEADER_GUIDELINE.md`. Each item cites
its FAIR principles and RDA indicators, uses the shared-core field names, gives examples in at
least two conventions, and names the assessment checks that test it.

**Independent Test**: `python -m unittest tests.test_assessment_guideline -v` passes. Every item
has examples in ≥ 2 conventions and ≥ 1 check id. Every indicator is either covered by an item or
listed as out of scope (quickstart V6).

### Tests for User Story 3 (write first, must fail) ⚠️

- [X] T043 [P] [US3] Write `FAIR-bioHeaders-Specification/tests/test_assessment_guideline.py` (unittest). It parses the item table and the per-item example tables of `docs/FAIR_HEADER_GUIDELINE.md` and asserts:
  - there are exactly the 8 items G1–G8;
  - "every offline, online and deferred indicator appears in exactly one item";
  - the 10 not-applicable indicators appear under "Out of scope for headers", each with a repository-level action;
  - each item has examples in ≥ 2 conventions (FR-007) and non-empty `principles` and `checks`;
  - every `core_fields` entry exists as a slot in `schemas/core.yaml`, or is marked `FHR:` and exists in `fhr.json`;
  - every real example cites a survey `source`;
  - the RDA attribution text is present.

  The list of 41 RDA ids is embedded in the test, so it does not depend on the toolkit

### Implementation for User Story 3

- [X] T044 [US3] Write `FAIR-bioHeaders-Specification/docs/FAIR_HEADER_GUIDELINE.md`, following research R-17. It needs:
  - a status line saying it is guidance and changes no schema;
  - a summary table of items, principles, RDA ids, core fields and checks;
  - the 8 items, each with its rationale and examples. Take examples from real surveyed lines where they exist (for example `#!genome-build-accession NCBI_Assembly:GCF_000002985.6`, `##species …?id=6239`, `!go-version: …`), as FHR `;~`/`#~`, GFF3 `#!`, VCF `##` and GAF `!` lines;
  - "how to express each item in your existing convention" (US3 scenario 2);
  - the "Out of scope for headers" section, covering the 10 indicators and the action for each;
  - the RDA CC BY 4.0 attribution (research R-19).

  Licensed MPL-2.0 (makes T043 pass)
- [X] T045 [US3] Add a cross-check to `FAIR-bioHeaders-Specification/scripts/check_assessment.py`, the `--guideline` step. It reads the tool's bundled `bioheaders/assess/data/rubric.json` from `--tool` and fails if any rubric `guideline_item` or check id disagrees with the guideline's item table, in either direction
- [X] T046 [US3] Align `FAIR-bioHeaders-Tools/bioheaders/assess/data/rubric.json` with the guideline. Every suggestion `text` names its guideline item (for example "see guideline G7"), and `suggestion.guideline_item` is filled. Bump `rubric_version` to the next minor version if any text changes, and update `FAIR-bioHeaders-Specification/assessment/manifest.json` `rubric_version` to match
- [X] T047 [P] [US3] Link the guideline and `assessment/` from `FAIR-bioHeaders-Specification/README.md` and `FAIR-bioHeaders-Specification/docs/TOOL_COMPATIBILITY.md`, and add a `CHANGELOG.md` entry in FAIR-bioHeaders-Specification marked guidance-only, with no schema change

**Checkpoint**: The guideline is published in the specification repository, and it agrees with
the rubric in the tool.

---

## Phase 6: User Story 4 - Assess many files at once (Priority: P3)

**Goal**: `bioheaders assess --recursive --output DIR [--pairs TSV] RELEASE/` writes per-file
reports, plus `summary.json`, `summary.md` and `summary.tsv`, with per-indicator counts and no
per-file total. A re-run on unchanged files gives identical output.

**Independent Test**: A 200-file directory gives a summary table and per-file reports in under 10
minutes, and a second run is byte-identical (quickstart V7).

### Tests for User Story 4 (write first, must fail) ⚠️

- [X] T048 [P] [US4] Write `FAIR-bioHeaders-Tools/tests/assess_batch_test.py`. It covers:
  - `--recursive`, and `--include`/`--exclude` globs against relative paths, with hidden files skipped;
  - the per-file reports mirror the input tree;
  - the `summary.tsv` columns are `path`, `format`, `scope`, `pair_classification`, then one per indicator in rubric order, with the cells `E`, `P`, `N`, `NA` and `NAS` and **no total column**;
  - `summary.json` has `indicator_counts` and `errors[]`;
  - the output is identical for `--jobs 1` and `--jobs 4`;
  - a re-run gives byte-identical files;
  - one unreadable file gives exit 1, and every other report is still written;
  - `--pairs` with a duplicate derived path, `--pairs` together with `--related`, and batch mode without `--output` each exit 2
- [X] T049 [P] [US4] Add a `--batch` mode to `FAIR-bioHeaders-Specification/scripts/check_assessment.py`. It runs `bioheaders assess --recursive --pairs assessment/pairs.tsv --output TMP assessment/`, checks every per-file report against the manifest, and checks that a second run is byte-identical

### Implementation for User Story 4

- [X] T050 [US4] Implement `FAIR-bioHeaders-Tools/bioheaders/assess/batch.py`. It walks the directory (sorted, with include/exclude), parses the pairs TSV ([contracts/data-files.md §5](contracts/data-files.md)), and runs a `concurrent.futures.ProcessPoolExecutor` with `--jobs` (default `min(CPU count, 8)`), scanning each related file once. It writes the per-file JSON and Markdown atomically, and builds the summaries in sorted path order: `summary.json`, a `summary.md` table with per-indicator counts, and `summary.tsv`
- [X] T051 [US4] Add `assess_release(paths, output_dir, pairs=None, jobs=None, online=False)` to `FAIR-bioHeaders-Tools/bioheaders/assess/__init__.py`. Add the options `--recursive`, `--include`, `--exclude`, `--jobs` and `--pairs` to the `assess` subcommand in `FAIR-bioHeaders-Tools/bioheaders/cli.py`, with the batch-mode exit codes (makes T048 pass)
- [X] T052 [US4] Write `FAIR-bioHeaders-Tools/scripts/bench_assess.py`. It generates a synthetic 200-file release in a temporary directory: 120 annotation and variant files of 50–500 MB, gzip and BGZF, 10 genomes of 100 MB, and a pairs TSV. It runs the batch assessment, prints the wall time and the machine (CPU and Python version), and exits 1 if the run takes 600 s or more (SC-004)

**Checkpoint**: All four user stories work on their own.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: The opt-in online checks (FR-011), documentation, packaging, the full gates and the
success-criteria checks.

### Opt-in online checks (cross-cutting; FR-010, FR-011)

- [X] T053 [P] Write `FAIR-bioHeaders-Tools/tests/assess_online_test.py`, marked `online_local`, against a `http.server` on 127.0.0.1 with the private-address refusal disabled for the test. It covers:
  - without `--online` no request is made, and the four access indicators are `not_assessed`/`online-check-not-requested`;
  - with `--online` only header-derived identifiers and URLs are requested, using HEAD then GET with `Range: bytes=0-0` and never a request body;
  - redirects are capped at 5;
  - schemes other than http(s) and private addresses give `refused`;
  - a timeout gives `not_assessed`/`online-check-unavailable`;
  - an online result never lowers an offline status;
  - `online_checks: "ran"` and the `online.checks[]` fields `checked_at` and `time_dependent: true` are present;
  - the schema URL in an FHR header is never requested
- [X] T054 Implement `FAIR-bioHeaders-Tools/bioheaders/assess/online.py` with `urllib`, following research R-10. It resolves DOIs through `https://doi.org/` and CURIEs and accessions through `https://identifiers.org/`. It applies the per-request timeout, refuses loopback, private and link-local addresses, sends no cookies or credentials, uses the User-Agent `bioheaders-assess/<version>`, de-duplicates requests, and allows 1 request per host at a time. Import it lazily, only when `--online` is given. Add `--online` and `--online-timeout` (default 10; `--online-timeout` without `--online` exits 2) to `FAIR-bioHeaders-Tools/bioheaders/cli.py` (makes T053 pass)

### Documentation and packaging

- [X] T055 [P] Document `bioheaders assess` in `FAIR-bioHeaders-Tools/README.md`: usage taken from [quickstart.md](quickstart.md), the "checklist, not a score" note, offline by default, and the RDA attribution. Add an entry to `FAIR-bioHeaders-Tools/CHANGELOG.md`, and add `bioheaders/assess/` and the data files to the repository map in `FAIR-bioHeaders-Tools/AGENTS.md`
- [X] T056 [P] Complete `FAIR-bioHeaders-Specification/assessment/README.md`. Describe the manifest fields, how other implementations (the 009 GFF3 validator and the website) use the fixtures, `make_assessment_fixtures.py`, `check_assessment.py --tool`, and the provider-trial guide for SC-005. The guide is for maintainers to send; this task does not contact anyone
- [X] T057 Build the wheel with `poetry build` in `FAIR-bioHeaders-Tools/`, install it into a fresh virtual environment outside the checkout, and run `bioheaders assess` on one fixture of each format to confirm that the `bioheaders/assess/data/**` files are packaged. Also run `python -m build compat/fhr`

### Gates and success criteria

- [X] T058 Run the FAIR-bioHeaders-Tools gates on Python 3.9 and 3.13: `poetry run pytest`, `ruff check .`, `isort . --check-only` and `black . --check`. Record any environment limitation in the PR description
- [X] T059 Run the FAIR-bioHeaders-Specification gates: `python -m unittest discover -s tests -v`, `scripts/validate_examples.py`, `scripts/check_linkml.py`, `scripts/check_schema_drift.py`, `scripts/check_conformance.py --schema` (it must stay unaffected by `assessment/`), `scripts/check_release.py --converter ../FHR-File-Converter`, and `scripts/check_assessment.py --tool ../FHR-File-Converter --batch --guideline`
- [X] T060 Run `python scripts/bench_assess.py --files 200` in `FAIR-bioHeaders-Tools/` on a laptop-class machine. Record the wall time and the machine in the PR (SC-004 requires under 600 s)
- [X] T061 Prepare the SC-001 review. Generate `FAIR-bioHeaders-Specification/assessment/review/sc001-template.tsv`, with columns `fixture`, `indicator`, `status`, `cited_lines`, `reviewer_agrees` and `note`, from the reports for the 17 corpus files. A reviewer other than the implementer fills it in as `sc001-<date>.tsv`, and the result passes at ≥ 90% agreement. Disagreements become rubric issues and are not edited away
- [X] T062 Run every scenario in [quickstart.md](quickstart.md) (V1–V9) against the implementation, and correct the quickstart's expected outputs wherever the reviewed implementation legitimately differs, with the reason in the commit message

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start immediately.
- **Foundational (Phase 2)**: Depends on Setup, and blocks all user stories. Within it, T011
  depends on T007–T010, and T016 and T017 depend on T015.
- **US1 (Phase 3)**: Depends on Foundational.
- **US2 (Phase 4)**: Depends on Foundational and on US1's T026–T028 and T033 (header readers,
  synonyms, link extraction and `assess_file`). Its fixture and test tasks (T036, T037) can start
  together with US1.
- **US3 (Phase 5)**: T043 and T044 (FAIR-bioHeaders-Specification) depend only on Foundational T010 for the
  indicator-to-item mapping, so they can run in parallel with US1 and US2. T045 and T046 need
  the rubric (T010) and the runner (T017).
- **US4 (Phase 6)**: Depends on US1 (T033 and T034). It uses US2's `related.py` cache (T038) for
  pairs, but without `--pairs` it is testable on US1 alone.
- **Polish (Phase 7)**: T053 and T054 depend on US1. T057–T062 depend on all the stories
  wanted in the release.

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational.
- **US2 (P1)**: Builds on the US1 header model (it needs recorded links). It is testable on its
  own with `assessment/pairs/`.
- **US3 (P2)**: A document plus tests in FAIR-bioHeaders-Specification. It is independent of the tool code,
  apart from the T045 cross-check.
- **US4 (P3)**: Wraps US1 (and US2 for pairs) in batch mode.

### Within Each User Story

- The tests (and their fixtures and manifest expectations) are written first and FAIL before the
  implementation.
- Models come before services, services before the CLI, and the core before integration.
- The FAIR-bioHeaders-Specification fixture tasks and the FAIR-bioHeaders-Tools test tasks are in different
  repositories, so they always parallelise.

### Repository split

| Repository | Tasks |
|---|---|
| FAIR-bioHeaders-Specification | T003, T005, T015, T016, T017, T018, T019, T035 (run), T036, T042, T043, T044, T045, T047, T049, T056, T059, T061 |
| FAIR-bioHeaders-Tools | T001, T002, T004, T006–T014, T020–T034, T037–T041, T046, T048, T050–T055, T057, T058, T060 |
| Both (verification) | T062 |

### Parallel Opportunities

- Setup: T002 and T003 alongside T001.
- Foundational tests T004, T005 and T006 together. Then T007, T008, T012, T013, T014 and T015
  together, and after them T009 → T010 → T011.
- US1 tests T018–T025 all together (8 tasks, in different files and repositories).
- US2's T036 and T037 together, and alongside US1 implementation.
- US3's T043, T044 and T047 alongside US1 and US2 (a different repository).
- US4's T048 and T049 together.
- Polish: T053, T055 and T056 together.

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (they must fail first):
Task: "Fill expected outcomes for 17 header fixtures in FAIR-bioHeaders-Specification/assessment/manifest.json"            # T018
Task: "Generate edge fixtures in FAIR-bioHeaders-Specification/assessment/edge/ via scripts/make_assessment_fixtures.py"  # T019
Task: "Convention parsing tests in FAIR-bioHeaders-Tools/tests/assess_conventions_test.py"                     # T020
Task: "Status rule tests in FAIR-bioHeaders-Tools/tests/assess_rubric_test.py"                                 # T021
Task: "FHR conformance tests in FAIR-bioHeaders-Tools/tests/assess_conformance_test.py"                        # T022
Task: "Report schema/determinism/no-score tests in FAIR-bioHeaders-Tools/tests/assess_report_test.py"          # T023
Task: "Suggestion applicability tests in FAIR-bioHeaders-Tools/tests/assess_suggestions_test.py"               # T024
Task: "Single-file CLI tests in FAIR-bioHeaders-Tools/tests/assess_cli_test.py"                                # T025

# Then implement in dependency order:
T026 conventions.py → T027 synonyms.py → T028 links.py (extraction) ; T029 conformance.py [parallel with T026–T028]
→ T030 rubric.py → T031 suggestions.py → T032 render.py → T033 assess_file → T034 cli.py → T035 run fixtures
```

## Parallel Example: User Story 2

```bash
Task: "Generate pair fixtures + pairs.tsv in FAIR-bioHeaders-Specification/assessment/pairs/"     # T036
Task: "Link/circumstantial tests in FAIR-bioHeaders-Tools/tests/assess_links_test.py" # T037
# then T038 related.py → T039 links.py verification → T040 circumstantial.py → T041 cli/render → T042 run pairs
```

---

## Implementation Strategy

### MVP First (User Stories 1 and 2)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (US1). **Stop and validate**: run `check_assessment.py` on the 17 captures.
3. Complete Phase 4 (US2). **Stop and validate**: all the pair fixtures classify correctly
   (SC-003).
4. The MVP is US1 plus US2: providers can assess any text file and check annotation-genome
   pairs, offline. Deployment (a PyPI or Bioconda release) is a maintainer action.

### Incremental Delivery

1. Setup and Foundational give the foundation.
2. US1, then test: the first toolkit PR (assessment of single files).
3. US2, then test: the second toolkit PR (related-file verification). This completes the MVP.
4. US3: an FAIR-bioHeaders-Specification PR (guideline). It can be merged in parallel with steps 2 and 3,
   and the cross-check is enabled once the rubric is merged.
5. US4, then test: the toolkit batch-mode PR, with the benchmark.
6. Polish: the online opt-in, documentation and gates. SC-001 review, then the SC-005 provider
   trial, which is a maintainer action.

### Parallel Team Strategy

1. One developer per repository during Setup and Foundational. FAIR-bioHeaders-Specification: T003, T005,
   T015–T017. FAIR-bioHeaders-Tools: T001, T002, T004, T006–T014.
2. Then:
   - Developer A (toolkit): US1 implementation, then US2, then US4.
   - Developer B (specification): the US1 and US2 fixtures (T018, T019, T036), then the US3
     guideline (T043–T047), then the batch runner (T049).

---

## Notes

- [P] tasks touch different files and have no dependencies on incomplete tasks.
- The [Story] label maps each task to a user story for traceability; see
  [checklists/traceability.md](checklists/traceability.md).
- Commit after each task or logical group, with cross-linked PRs in the two repositories.
- Never refresh `.github/schema-baseline.json`. Never edit `fhr.json` or the converter schema
  copies. This feature changes no schema.
- Suggestions and fixtures never contain invented accessions, licences, authors or dates
  (FAIR-bioHeaders-Specification constitution IV). Use labelled placeholders.
- Open maintainer questions (plan.md) have stated defaults. If one is decided differently, the
  affected tasks are T010 and T046 (rubric location), T029 (bundling several schema versions),
  T039 (SeqCol computation), T044 (advice on native keys) and T031 (relationship vocabulary).
