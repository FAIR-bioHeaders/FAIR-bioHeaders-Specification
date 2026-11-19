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

Committed files are preserved byte-for-byte: `.gitattributes` turns off
line-ending conversion here. Regenerate synthetic files into a scratch directory
with `python scripts/make_assessment_fixtures.py --output DIR` instead of editing
them. The regeneration oracle is explicit for every generated file in
`generation-oracles.json`; new outputs must be classified before the test passes.

- Plain files, headed files, pairs and `pairs.tsv` retain exact-byte comparison.
- `edge/gzip-refseq.gff.gz` compares the fully decompressed payload, including
  CRC/trailer verification, rather than the deflate representation.
- `edge/bgzf-refseq.gff.gz` and `edge/stub.bam` compare the decompressed payload
  and require valid BGZF block framing and the standard EOF block.
- `edge/gff3-in-tar.gff.gz` is a **gzip-wrapped tar archive**, not a gzip member
  inside a tar. Compare its decompressed tar bytes and require one regular
  `annotation.gff3` member with GFF3 content. The pinned installed toolkit must
  classify independently recompressed variants as `archive`,
  `out_of_scope/archive-not-supported`, matching the manifest.

No committed fixture or conformance digest is updated by these comparisons.
Compressed assessment cases do not establish a stable compressor encoding;
the shared conformance suite's checksum/digest-pinned compressed vectors retain
their separate byte-exact generator checks.

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
`edge/` deterministically within one runtime (gzip members with `mtime=0` and
OS byte 255); `tests/test_assessment_fixtures.py` checks repeatability, the
per-file regeneration oracles and complete fixture registration. Python 3.15's
`gzip.compress` defaults to level 6, versus level 9 through 3.14. With the same
zlib 1.2.12 locally, level 6 produces the 180-byte archive and explicit level 9
reproduces the committed 174 bytes: this observed difference is the Python
default, not a different zlib build. Pinning level 9 would conceal the test's
unnecessary dependence on compressed representation rather than verify behaviour.

CI runs this fixture/installed-assessment subset on Python 3.12, 3.13 and 3.15
with the published toolkit version from `conformance/toolkit-pin.json`. This
does not claim the separate LinkML build supports Python 3.15. Locally, set
`ASSESSMENT_TOOLKIT` to that release's installed `bioheaders` executable to run
the archive-scope checks; an unset executable is reported as not run.

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
