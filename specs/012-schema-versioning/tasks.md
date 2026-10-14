---
description: "Task list for feature 012: schema versions and schema selection"
---

# Tasks: Schema versions and schema selection

**Input**: Design documents from `/specs/012-schema-versioning/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required (constitution III). Within each story the test tasks come first.

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

- `FHR-Specification/`: this repository, branch `release-v0.4`.
- `FAIR-bioHeaders-Tools/`: the toolkit.
- `gff3-validator/`: the validator.

No task releases, tags, archives a DOI, changes w3id.org or edits the website.

---

## Phase 1: Setup

- [X] T001 Merge `main` into `release-v0.4` (merge commit) so the work starts from current docs
  *Done:* FHR-Specification#103

## Phase 2: Foundational

- [X] T002 `FHR-Specification/schemas/versions.json`: the registry (D-04) and a test that every
  schema's `schemaVersion` enum equals `releases[current]`
- [X] T003 Core `schemaVersion`: string, version pattern; per-type `equals_string`: FHR `"2.0"`,
  FHP `"1.0"`, FHGFF3 `"1.0"`; FHP and FHGFF3 `schema` patterns accept V1–V3 forms
- [X] T004 Regenerate `fhp.json`, `fhgff3.json`; update `fhr.json` by hand to match `fhr_linkml.yml`;
  update the three baselines deliberately; `check_linkml.py` passes

## Phase 3: User Story 3 - schemaVersion (P1)

- [X] T005 [US3] Tests: accepted `"2.0"` / `"1.0"`; rejected `1`, `1.0`, `"1"`, `2`, `"2"`,
  `"2.1"`, `"02.0"` against published and generated schemas
- [X] T006 [US3] `docs/SCHEMA-VERSIONS.md`: policy (D-02), registry, rule (contract), migration
  (D-10); SCHEMA-CHANGES-v0.4.md, FORMAT.md, CHANGELOG, README

## Phase 4: User Stories 1, 2, 4 - selection, unsupported, new files (P1/P2)

- [X] T007 [US1] [US2] Vectors V1–V5 in `make_conformance.py` with `result: unsupported-version`
  for V4; manifest rules; `check_conformance.py --schema` selects schemas by the rule, with released
  schemas from tags; `--converter` checks the unsupported message
- [X] T008 [US4] All examples, vectors and assessment fixtures cite `…/<type>/v0.4.0` and the type's
  `schemaVersion`; checksums recomputed; JSON-LD regenerated; microdata `schemaVersion` string
- [X] T009 [US4] FHP rule P2 and FHGFF3 rule G3 recognise the w3id forms (FHP.md, FHGFF3.md);
  MICRODATA.md and JSONLD.md notes; mapping table note
- [X] T010 CI: validate job fetches tags; release-line converter job runs the toolkit v0.4 branch
  at a pinned commit

## Phase 5: User Story 5 - tools (P2)

- [X] T011 [US5] Toolkit step 1 (`main`): `bioheaders/schemas.py`, bundled `fhr-1.json` and
  registry, unsupported-version in commands, GFF3 report and assess; tests; README, CHANGELOG
- [X] T012 [US5] Toolkit step 2 (draft): v0.4 copies, released v0.4.0 entries, examples and
  fixtures from `release-v0.4`; all vectors pass with `--require-format`
  *As implemented (deviation from D-09):* steps 1 and 2 are one draft PR,
  FAIR-bioHeaders-Tools#57. Step 1 alone could not merge to the toolkit's `main`: under the rule,
  spec `main`'s vector `jsonld-schema-versioned-url` (which cites `fhr/v0.4.0` with v0.3
  metadata) is unsupported for a toolkit without v0.4.0, so toolkit and spec `main` would
  disagree. The module is `bioheaders/selection.py` (a package directory `bioheaders/schemas/`
  holds the copies and `bundled.json`). `assess` follows V1–V4 but keeps not assessing records
  whose `schema` is no FAIR-bioHeaders URL (`unsupported-header-type`), as the 38 assessment
  fixtures expect; the command-line tools apply V5
- [X] T013 [US5] gff3-validator: selection tests (skipped without support)
  *As implemented:* draft gff3-validator#16 moves the header cases to the v0.4.0 URLs and adds
  `hdr-007-unsupported-schema-version`; it waits for the toolkit release
- [X] T014 Comments with links on #44, #35, website #15/#16

## Phase 6: Polish

- [X] T015 All gates in quickstart.md; record results and deviations here
  *Results (2026-10-14):* unittest 158 OK; `validate_examples.py`, `check_linkml.py` (three types),
  the three drift baselines, `make_jsonld.py --check`, `check_conformance.py --schema` (199) and
  the standard-library run pass. With toolkit #57 installed from its wheel:
  `check_conformance.py --converter … --require-format jsonld --require-format fhp-fasta
  --require-format fhgff3` 199/199; `check_release.py` (with the new bundled-release check);
  `check_assessment.py` 38/38, `--batch` and `--guideline`. Also fixed on the way: the YAML,
  FASTA, GFA and microdata FHR examples lacked the `nameType` that `example.fhr.json` gained in
  #85.
