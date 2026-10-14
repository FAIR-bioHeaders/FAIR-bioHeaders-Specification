# Data model: FAIR header assessment

**Feature**: 010-fair-header-assessment | **Date**: 2026-10-10 | **Plan**: [plan.md](plan.md)

This model covers the five key entities in the spec and the supporting entities that the
report needs. The JSON field names are those of
[contracts/assessment-report.schema.json](contracts/assessment-report.schema.json). The data-file
entities (Indicator, Concept) are specified in
[contracts/data-files.md](contracts/data-files.md).

```text
AssessmentReport 1──1 InputFile
                 1──* HeaderEvidence ──* Concept (via synonyms.json)
                 1──41 IndicatorResult ──1 Indicator (rubric.json) ──1 GuidelineItem
                 │            └──* Finding, 0..1 Suggestion
                 1──0..1 ConformanceResult           (FR-008)
                 1──* RelatedFileLink ──0..1 LinkVerification (FR-005, FR-006)
                 1──0..1 CircumstantialCheck          (FR-005)
                 1──0..1 PairClassification
                 1──0..1 OnlineSection ──* OnlineCheck (FR-011)
ReleaseSummary   1──* AssessmentReport                (US4)
```

---

## 1. InputFile

This entity describes the file being assessed.

| Field | Type | Rules |
|---|---|---|
| `path` | string | The path as given, or the path relative to the batch root. `-` for stdin |
| `size` | integer ≥ 0, or null | Null for stdin |
| `compression` | `none` \| `gzip` \| `bgzf` | Detected from the magic bytes, not from the extension |
| `format` | `fasta` \| `gff3` \| `gaf` \| `vcf` \| `gfa` \| `unknown-text` \| `binary` \| `archive` | Detected from the content first, then the file name; `--type` overrides both |
| `format_source` | `content` \| `extension` \| `option` | How `format` was decided |
| `header_sha256` | hex string (64) | SHA-256 of the header-region bytes actually read (after decompression) |
| `file_sha256` | hex string (64), optional | Only with `--hash-inputs` |
| `header_lines_read` | integer | |
| `records_sampled` | integer | ≤ `--record-limit` |
| `scope` | `assessed` \| `out_of_scope` \| `error` | `out_of_scope` covers binary and archive files. `error` covers unreadable files and corrupt gzip, and then the field `error` is required |

**Validation**: If `scope` ≠ `assessed`, every IndicatorResult is `not_assessed` and carries the
matching reason (`binary-format-out-of-scope`, `archive-not-supported` or `input-unreadable`).

## 2. HeaderEvidence

A spec key entity: one metadata statement found in a file.

| Field | Type | Rules |
|---|---|---|
| `id` | string `e<n>` | Unique within the report; ordered by line |
| `line` | integer ≥ 1 | Line number in the decompressed file |
| `convention` | `fair-bioheaders` \| `gff3-directive` \| `gff3-pragma` \| `gaf` \| `vcf-meta` \| `fasta-defline` \| `unrecognised` | |
| `raw` | string | The original line without its terminator, truncated at 1 MiB (finding `line-too-long`) |
| `key` | string or null | The key as written, for example `annotationSource` or `assembly:` |
| `normalised_key` | string or null | After the synonym-table normalisation rules |
| `value` | string or object or null | A scalar, or the parsed sub-fields (VCF `##contig=<…>`, FHR objects) |
| `concepts` | list of concept ids | Empty for unrecognised lines |
| `scope` | `file` \| `first-record` \| `upstream-provenance` | `first-record` applies to evidence from a FASTA defline. `upstream-provenance` applies to GAF blocks after the first `!Header from`/`!====` separator |
| `value_forms` | list of form ids | The forms the value matches, for example `insdc-assembly-accession` or `spdx-id` |

**Validation and rules**:
- Every line in the header region yields exactly one HeaderEvidence. Unrecognised comment lines
  are kept, with `convention: unrecognised` (edge case).
- `upstream-provenance` evidence is never used for file-level indicators. It is used only as
  provenance context.
- An identifier form found in free text (no key, or a key whose concept does not expect that
  form) yields the finding `identifier-in-free-text` and is not credited.

## 3. Concept

A synonym-table entry, defined in `synonyms.json`.

| Field | Type | Rules |
|---|---|---|
| `id` | kebab-case string | For example `assembly-accession`, `assembly-name`, `licence`, `date-created`, `taxon`, `creator`, `format-version`, `sequence-region`, `sequence-digest`, `source-url`, `software`, `ontology-version`, `file-identifier`, `version` |
| `keys` | map convention → list of keys | The keys are compared after normalisation |
| `forms` | list of form ids | The value forms that give full credit. Other non-empty values give partial credit where the rubric says so |
| `scope` | `file` \| `first-record` | The default scope of evidence for this concept |
| `emit` | map convention → key | The preferred key used in suggestions |
| `core_field` | string or null | The FAIR-bioHeaders shared-core slot (`schemas/core.yaml`), for example `reuseConditions` |

## 4. Indicator (spec "Criterion")

An entry in `rubric.json`. A spec key entity: "a FAIR principle-derived check with its rationale
and suggestion text".

| Field | Type | Rules |
|---|---|---|
| `id` | `RDA-<principle>-<nn><M\|D>` | One of the 41 RDA ids. Unique |
| `title` | string | The RDA short title, verbatim (CC BY 4.0) |
| `principle` | string | For example `I3`, `R1.1` |
| `priority` | `essential` \| `important` \| `useful` | From RDA Table 1 |
| `target` | `metadata` \| `data` | |
| `assessability` | `offline` \| `online` \| `not_applicable` \| `deferred` | 25 / 4 / 10 / 2 (research R-03) |
| `reason` | reason code | Required iff `assessability` ∈ {`not_applicable`, `deferred`} |
| `interpretation` | string | The file-header interpretation, marked as an adaptation |
| `conditions` | list of Condition | Required iff `assessability` ∈ {`offline`, `online`} |
| `evidenced_when` / `partial_when` | rule | `all`, `any`, `never`, `{"min": n}`, or `{"any_of": [ids]}` / `{"all_of": [ids]}` naming conditions (added in implementation: a count cannot say "this condition is required") |
| `check` | named check or null | `derived-link`, `fhr-conformance`, `format-declared`, `record-sample-parse`, `resolve` |
| `online_upgrade` | boolean | True for RDA-F1-01D, RDA-I2-01M and RDA-R1.1-03M (online adds a note only) |
| `guideline_item` | `G1`–`G8` or `out-of-scope` | |
| `suggestions` | map convention → template | Templates may use only `{value}` from evidence, `{related.*}` from the related file, or a labelled `<placeholder>` |

**Condition**: `{id, concept, form?, scope_allowed?: ["file"] | ["file","first-record"]}`.

## 5. IndicatorResult (spec "Assessment result")

| Field | Type | Rules |
|---|---|---|
| `indicator` | Indicator id | Each of the 41 ids appears exactly once, in rubric order |
| `status` | `evidenced` \| `partially_evidenced` \| `not_evidenced` \| `not_applicable` \| `not_assessed` | |
| `reason` | reason code or null | Required iff the status is `not_applicable` or `not_assessed` |
| `method` | `offline` \| `online` \| `none` | `none` iff the status is `not_applicable`, or `not_assessed` with an offline reason |
| `evidence` | list of HeaderEvidence ids | Required (non-empty) iff the status is `evidenced` or `partially_evidenced`. May be non-empty for `not_evidenced`, when the values are malformed |
| `conditions_met` / `conditions_total` | integers | Shown so a reviewer can follow the rule |
| `findings` | list of Finding | |
| `suggestion` | Suggestion or null | Required iff the status is `partially_evidenced` or `not_evidenced` |
| `notes` | list of strings | For example the online resolution note on an online-upgrade indicator |

### Status rules (state derivation)

The status of one indicator is derived in this order. The first step that applies decides it.

```text
1. Indicator.assessability = not_applicable            → not_applicable (reason from rubric)
2. InputFile.scope ≠ assessed                           → not_assessed (binary-format-out-of-scope |
                                                           archive-not-supported | input-unreadable)
3. Indicator.assessability = deferred                   → not_assessed (deferred-data-body)
4. Indicator.assessability = online and no --online     → not_assessed (online-check-not-requested)
5. Indicator.assessability = online, network failure    → not_assessed (online-check-unavailable)
6. Named check fhr-conformance with conformance not_assessed
                                                        → not_assessed (unsupported-header-type |
                                                           unsupported-schema-version)
7. Evaluate the conditions over the credited evidence:
     a. evidence with scope upstream-provenance is ignored;
     b. a malformed value satisfies nothing (it adds a finding);
     c. count the satisfied conditions;
     d. evidenced_when holds → evidenced
        partial_when holds   → partially_evidenced
        otherwise            → not_evidenced
8. Caps (applied after step 7, and only downwards):
     - every satisfying evidence item is first-record   → at most partially_evidenced
     - a conflicting-values finding on a used concept   → at most partially_evidenced
     - a header-truncated finding and the condition unmet → status kept, finding attached
9. Online results never lower a status reached in step 7 or 8.
```

Allowed reason codes:
- `not_applicable`: `embedded-metadata`, `repository-level`, `object-in-hand`.
- `not_assessed`: `online-check-not-requested`, `online-check-unavailable`, `deferred-data-body`,
  `binary-format-out-of-scope`, `archive-not-supported`, `unsupported-header-type`,
  `unsupported-schema-version`, `input-unreadable`.

## 6. Finding

| Field | Type | Rules |
|---|---|---|
| `kind` | enum | `malformed`, `conflicting-values`, `identifier-in-free-text`, `unrecognised-comment`, `header-truncated`, `line-too-long`, `undecodable-line`, `format-irregularity` (for example a comment before `##gff-version`, or a non-standard `fileDate`), `url-names-directory`, `filename-hint` |
| `evidence` | list of HeaderEvidence ids | May be empty for whole-file findings |
| `message` | string | Plain language; names the line and what is wrong |

Findings never change the statuses by themselves, apart from the caps in §5 step 8.

## 7. Suggestion

| Field | Type | Rules |
|---|---|---|
| `text` | string | One sentence: what to add and why |
| `line` | string | The exact line to add, in the file's convention (research R-11) |
| `convention` | convention id | The file's own convention where one exists, otherwise `fair-bioheaders` |
| `value_source` | `file` \| `related-file` \| `placeholder` \| `file-name` | `file-name` values carry "confirm before use" in `text` |
| `guideline_item` | `G1`–`G8` | |

**Rule**: Values never come from outside the file, the related file, or the file name (the last
labelled as such). Placeholders are written `<…>` (FAIR-bioHeaders-Specification constitution IV).

## 8. RelatedFileLink (spec "Related-file link")

A spec key entity: a recorded identity from one file to another.

| Field | Type | Rules |
|---|---|---|
| `kind` | `checksum` \| `seqcol` \| `sequence-digests` \| `accession` \| `url` \| `name` | |
| `rank` | 1–4 | 1: checksum, seqcol, sequence-digests. 2: accession. 3: url. 4: name (research R-06) |
| `value` | string or map (name → digest) | |
| `relationship` | string or null | `derivedFrom.relationship`, or the documented meaning of a native key (for example `annotates` for `#!genome-build-accession`) |
| `evidence` | list of HeaderEvidence ids | Non-empty |
| `well_formed` | boolean | False → finding `malformed`, and the verification verdict is `unverifiable` |
| `verification` | LinkVerification or null | Null when no related file was supplied |

### LinkVerification

| Field | Type | Rules |
|---|---|---|
| `related_path` | string | |
| `verdict` | `match` \| `mismatch` \| `unverifiable` | |
| `reason` | string or null | Required iff `unverifiable`: `malformed`, `related-file-states-no-identity`, `related-file-states-no-seqcol`, `related-file-unreadable`, `sequence-absent` |
| `expected` / `actual` | string or map | What was recorded, and what was found or computed |
| `method` | `computed-fhr-checksum` \| `stated-fhr-checksum` \| `stated-seqcol` \| `computed-md5` \| `stated-identity` | |
| `hints` | list of strings | For example "the related file's name contains GCF_000002985.6". Never part of the verdict |

**State rules**:
- `match` requires that the related file *states* or *computes to* the recorded value.
- A per-sequence digest set is `match` only if every compared sequence matches. It is `mismatch`
  if any sequence differs, and the differing names are listed.

## 9. CircumstantialCheck

| Field | Type | Rules |
|---|---|---|
| `label` | constant `"circumstantial evidence, not a recorded link"` | |
| `source` | `sequence-region` \| `vcf-contig` \| `record-seqids` | |
| `names_compared` | integer | |
| `missing_from_related` | sorted list of names | Complete; never truncated in JSON |
| `length_mismatches` | list `{name, declared, actual}` | |
| `lengths_compared` | integer | How many declared lengths were compared. Lengths that are not declared never lower the verdict |
| `not_declared_count` | integer | Sequences of the related file that the derived file does not mention |
| `verdict` | `consistent` \| `partially_consistent` \| `inconsistent` \| `not_checked` | consistent: every declared name present and no declared length differs. inconsistent: no declared name present. not_checked: nothing declared or sampled. Otherwise partially_consistent |

This entity is never referenced by an IndicatorResult (FR-005).

## 10. PairClassification

`recorded-mismatch` > `recorded-match` > `inconsistent` > `partial` > `consistent-unverified` >
`unknown`. The first one that holds wins:

- `recorded-mismatch`: any LinkVerification is `mismatch`.
- `recorded-match`: at least one verification is `match`.
- `inconsistent`: the CircumstantialCheck verdict is `inconsistent`.
- `partial`: the verdict is `partially_consistent`.
- `consistent-unverified`: the verdict is `consistent`.
- `unknown`: otherwise.

A `recorded-match` with a circumstantial verdict other than `consistent` adds the finding
`format-irregularity`, with a message that the recorded link matches but the declared names
disagree.

## 11. ConformanceResult (FR-008)

| Field | Type | Rules |
|---|---|---|
| `header_type` | `FHR` \| `FHT` \| `FHP` \| `FHGFF3` \| null | Determined from the `schema` value against an allow-list, not by matching substrings of the URL (spec#44). Null when the `schema` value is missing or not on the list; the result is then `not_assessed` (`unsupported-header-type`) and the core fields are still read as evidence. The allow-list holds the raw-main URLs of `fhr.json` (FHR) and `fht.json` (FHT, unpublished fork); FHP and FHGFF3 have no schema URL yet |
| `cited_schema` | string or null | The `schema` value in the file |
| `cited_schema_version` | string or null | |
| `schema_used` | `{canonical_url, bundled_sha256, version}` or null | The canonical URL is the raw-main URL (website#15) |
| `result` | `valid` \| `invalid` \| `not_assessed` | |
| `reason` | string or null | Required unless `valid`. For `invalid`: the JSON path and message, or the reader error (duplicate key and similar). For `not_assessed`: `unsupported-header-type` or `unsupported-schema-version` |

**Rule**: An `invalid` FAIR-bioHeaders header contributes no FAIR evidence. Its lines are listed
as evidence with the concept `fair-bioheaders-invalid`.

## 12. OnlineSection and OnlineCheck (FR-011)

The report's top level always has `online_checks: "ran" | "not_requested"`. When `ran`, the
OnlineSection lists one OnlineCheck per checked target:

| Field | Type | Rules |
|---|---|---|
| `target` | string | An identifier or URL taken from the HeaderEvidence |
| `request_url` | string | For example `https://doi.org/…` or `https://identifiers.org/…` |
| `final_url` | string or null | |
| `http_status` | integer or null | |
| `outcome` | `resolved` \| `not_found` \| `refused` \| `unavailable` | `refused` means the scheme or address is not allowed (research R-10) |
| `checked_at` | RFC 3339 UTC | |
| `time_dependent` | constant `true` | |

## 13. GuidelineItem (spec key entity; FAIR-bioHeaders-Specification `docs/FAIR_HEADER_GUIDELINE.md`)

| Field | Type | Rules |
|---|---|---|
| `id` | `G1`–`G8` | |
| `title` | string | For example "Say what this file was derived from, and how" |
| `principles` | list of FAIR principles | Non-empty |
| `indicators` | list of RDA ids | Every offline, online and deferred indicator appears in exactly one item. The not-applicable indicators appear under "Out of scope for headers" |
| `core_fields` | list of `schemas/core.yaml` slot names | Must exist in the core, or be FHR-only and marked `FHR:` |
| `examples` | list `{convention, line, source}` | At least 2 conventions (FR-007, US3 independent test). `source` is a survey file id, or `illustrative` |
| `checks` | list of Indicator ids | The assessment checks that test this item |

**Validation**: A test in FAIR-bioHeaders-Specification (`tests/test_assessment_guideline.py`) parses the
guideline's item table and checks it against the rubric indicator list. It checks for missing
items, unknown ids, fewer than 2 example conventions, and unknown core fields.

## 14. AssessmentReport and ReleaseSummary

**AssessmentReport** has the following top-level fields:
- `report_version`;
- `tool {name, version}`;
- `rubric_version`, `synonyms_version`, `reference_versions`;
- `attribution`;
- `online_checks`;
- `input` (InputFile);
- `evidence[]`;
- `results[]` (41 entries);
- `conformance`;
- `links[]`;
- `circumstantial`;
- `pair_classification`;
- `findings[]` (file-level);
- `online`.

It has no score field, and `additionalProperties: false` at the top level enforces that (FR-004).

**ReleaseSummary** (US4) has these fields:
- `report_version`, `tool`, the data-file versions;
- `root`;
- `files[] {path, format, scope, statuses: {indicator: status}, pair_classification}`;
- `indicator_counts {indicator: {status: n}}`;
- `errors[] {path, message}`.
- `attribution` and `online_checks`, as in a report (added in implementation, contracts/cli.md).

It has no per-file totals. Its order is sorted by `path`.

**Reproducibility rule**: Every field except `online.*` is a function of the input bytes, the
options, the tool version and the data-file versions alone.
