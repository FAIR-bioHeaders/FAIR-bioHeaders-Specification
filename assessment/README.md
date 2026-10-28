# FAIR header assessment fixtures

These files are the shared fixtures of feature 010
([specs/010-fair-header-assessment](../specs/010-fair-header-assessment/)). They are
used to check any implementation of the FAIR header assessment, such as
`bioheaders assess` in FAIR-bioHeaders-Tools, against implementation-neutral
expected outcomes. They follow the pattern of [`conformance/`](../conformance/).

## Layout

- `headers/`: real header lines captured from public provider download files during
  the Phase 0 survey (research/survey.md §R3). Each file holds only the original
  header lines; the survey's provenance comment lines were removed and the source
  URL and fetch time moved to `manifest.json`. Long runs of `##sequence-region`
  lines that the survey shortened are not reconstructed.
- `pairs/`: small synthetic annotation and genome pairs for User Story 2, made by
  `scripts/make_assessment_fixtures.py`. Sequence names and lengths are
  scaled-down WBcel235 style; the sequences are synthetic.
- `edge/`: synthetic edge cases (no header, compression, archives, binary stubs,
  mixed conventions, malformed and conflicting values), made by the same script.
- `review/`: the SC-001 review packet (`sc001-template.tsv` and the corpus reports) and,
  once a review is done, the reviewer's agreement table `sc001-<date>.tsv`; see
  [review/README.md](review/README.md).
- `manifest.json`: one entry per fixture with its provenance and the expected
  outcomes the fixture exercises. Its format is `manifest.schema.json`.
- `pairs.tsv`: derived → related pairs for batch runs.

Every file is byte-exact: `.gitattributes` turns off line-ending conversion here.
Regenerate the synthetic files with `python scripts/make_assessment_fixtures.py`
instead of editing them.

## Manifest

`manifest.json` (format: `manifest.schema.json`) has a `manifest_version`, the
`rubric_version` the expectations were written for, and one entry per fixture:

- `id`: a stable identifier;
- `file`: the fixture, relative to this directory, and `related`: the related file
  (usually a genome) for a pair;
- `format`: the expected detected format (`fasta`, `gff3`, `gaf`, `vcf`, `gfa`,
  `unknown-text`, `binary` or `archive`), and `type` when the fixture must be read with
  an explicit format;
- provenance: `source_url`, `fetched` and `release` for real captures, or
  `generator` for synthetic files, plus optional `notes`;
- `expected`: only the outcomes the fixture is meant to exercise. A runner compares
  these and ignores everything else:
  - `statuses`: `{indicator: status}`, where a status is `evidenced`,
    `partially_evidenced`, `not_evidenced`, or `not_applicable`/`not_assessed` with an
    optional `/reason`;
  - `evidence_lines`: line numbers that must be among the lines cited for an indicator;
  - `links`: the recorded links in order (`kind`, `value`, and optionally `well_formed`,
    `verdict` and `reason` of the verification);
  - `findings`: finding kinds, optionally at a line;
  - `conformance`: fields of the FAIR-bioHeaders conformance result, or `null`;
  - `circumstantial` and `pair_classification`: the related-file comparison;
  - `scope`: the input scope (`assessed`, `out_of_scope` or `error`), optionally with
    `/reason`, the reason every indicator then carries.

Statuses, reasons, link kinds and verdicts are the implementation-neutral values of
the report format (specs/010-fair-header-assessment/contracts/).

## Running

```bash
python scripts/check_assessment.py --tool ../FAIR-bioHeaders-Tools
python scripts/check_assessment.py --tool ../FAIR-bioHeaders-Tools --batch --guideline
```

`--tool` takes a toolkit checkout, a virtual environment or bin directory, or
`PATH`. The runner runs `bioheaders assess --format json` on every fixture,
validates each report against the tool's own report schema and compares the
expected fields. `--batch` also runs batch mode over `headers/`, `pairs/` and
`edge/` with `pairs.tsv`, twice, compares every per-file report with the manifest and
checks that the second run is byte-identical. `--guideline` compares the tool's
rubric with the item table of
[docs/FAIR_HEADER_GUIDELINE.md](../docs/FAIR_HEADER_GUIDELINE.md). `--review-packet DIR`
writes the SC-001 review packet.

`python scripts/make_assessment_fixtures.py [--output DIR]` regenerates `pairs/` and
`edge/` deterministically (gzip members with `mtime=0` and OS byte 255, on any
Python version); `tests/test_assessment_fixtures.py`
checks that the committed files match its output and that every file is listed once.

## Other implementations

The fixtures are meant for any implementation of the assessment, not only
`bioheaders assess`:

- **The 009 GFF3 validator** (or any other validator that reports FAIR header
  statuses) can read `manifest.json`, run itself on each `file` (with `related` where
  given) and compare its output with `expected` in the same way as `compare()` in
  `scripts/check_assessment.py`. A tool that covers only some formats or indicators
  can skip the entries and indicators it does not support, and should say so.
- **The website** can use the captures and their expected statuses as worked
  examples, and the guideline items as the explanation of each status. Real captures
  carry their source URL and fetch date, which must be shown with them.
- A tool that writes the same JSON report format can be checked directly with
  `check_assessment.py --tool`, if it provides a `bioheaders`-compatible command.

## Provider trial guide (SC-005)

SC-005 asks whether a data provider finds the reports useful on one of its own
releases. Contacting a provider is a maintainer action; this guide is for maintainers
to send, and nothing in this repository contacts anyone.

1. Ask the provider (the Alliance of Genome Resources first) to install the
   `fair-bioheaders` release that includes `assess`, offline, on a machine that can
   read one release.
2. Ask them to run the release walkthrough of
   [quickstart.md](../specs/010-fair-header-assessment/quickstart.md) §4:
   `bioheaders assess --recursive --pairs pairs.tsv --output reports/<release> <release dir>`,
   with a pairs file that maps each annotation and variant file to its genome.
3. Ask for `reports/<release>/summary.tsv` and `summary.md`, the run time and the
   machine, and answers to: Are the statuses right for the files you know? Are the
   suggestions lines you could add to your pipeline? Which indicators are not
   meaningful for you? What would make you add a header line?
4. Record the answers in an issue in FHR-Specification, without private details, and
   link it from the feature's tasks. Rubric or guideline changes that follow go
   through the normal review.

## Licence

New files here are licensed MPL-2.0 (see [LICENSE](../LICENSE) and CONTRIBUTING.md).
The captured provider header lines are short factual metadata from public download
files, used as test fixtures with their source URLs recorded in the manifest.
