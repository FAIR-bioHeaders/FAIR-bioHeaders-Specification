# SC-001 review packet

Success criterion SC-001 of feature 010 asks whether the assessment's statuses are right: a
reviewer who did **not** implement the assessment checks each reported status against the
header lines it cites and the rubric's interpretation, and the criterion is met at **90% or
more agreement** over the statuses of the offline-assessed indicators (research.md R-21). This
directory holds the packet for that review. **No review has been done yet**: the result is
recorded only when a reviewer fills in the table.

## Contents

- `sc001-template.tsv`: one row per corpus file and offline-assessed indicator (17 files ×
  25 indicators = 425 rows), with the columns `fixture`, `indicator`, `status`,
  `cited_lines`, `reviewer_agrees` and `note`. `status` is the reported status
  (`status/reason` for `not_assessed`); `cited_lines` lists the header lines the status rests
  on, as `line N: text`, separated by ` | `. The last two columns are empty.
- `sc001-reports/<fixture>.assessment.md`: the full report for each corpus file, with the
  suggestions and findings, to read alongside the table.

The packet was generated with `bioheaders assess` 0.4.0 (FAIR-bioHeaders-Tools, feature 010
branch) and rubric 1.1.0, from the 17 captures in `../headers/`:

```bash
python scripts/check_assessment.py --tool ../FAIR-bioHeaders-Tools --review-packet assessment/review
```

Regenerate it if the tool or the rubric changes before the review starts; the reports name the
tool and rubric versions.

## How to review

1. Copy `sc001-template.tsv` to `sc001-<YYYY-MM-DD>.tsv` (the date of the review).
2. For each row, read the cited lines (in the report or in `../headers/<file>`) and the
   indicator's interpretation in the toolkit's `bioheaders/assess/data/rubric.json`
   (`interpretation`, `conditions`), or the summary in
   `specs/010-fair-header-assessment/research/rda-indicators.md` §2. The guideline
   `docs/FAIR_HEADER_GUIDELINE.md` says which item each indicator belongs to.
3. Write `yes` in `reviewer_agrees` if the status follows from the file and the rubric, `no`
   if it does not. For `no`, say in `note` which status you expected and why.
4. Agreement is the number of `yes` rows divided by the number of rows answered. SC-001 passes
   at 90% or more.
5. Commit the filled table, with the reviewer's name in the commit message. Do not edit the
   template, the reports or the rubric to remove a disagreement: each `no` becomes a rubric
   issue (in FAIR-bioHeaders-Tools for the rubric, or FHR-Specification for the guideline),
   and the review result stays as recorded.

The reviewer must be someone other than the implementer of the assessment; a self-review does
not count (research.md R-21).
