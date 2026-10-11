---

description: "Task list for feature 006: protein FASTA header (FHP)"
---

# Tasks: Protein FASTA header (FHP)

**Input**: Design documents from `/specs/006-protein-header/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: These are required.
- The FHR-Specification constitution III says "every parsing rule needs a conformance example".
- Every success criterion that can be checked here (SC-001, SC-002, SC-004, SC-005) has an
  automated check.

Within each story the test tasks come first, and they must fail before the implementation starts.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)

## Path Conventions

- `FHR-Specification/`: this repository.
- `FAIR-bioHeaders-Tools/`: the `fair-bioheaders` package; the local checkout is
  `../FHR-File-Converter`.

No task releases, tags, archives a DOI or changes w3id.org (constitution, "Decision boundaries").

---

## Phase 1: Setup

- [X] T001 Add `--type {fhr,fhp}` to `FHR-Specification/json-schema-generator.py`. Keep `generate()` (FHR) byte-identical in output, and add `generate_fhp()`, which applies contracts/fhp-schema.md post-processing 1–4. `--type fhp` defaults its output to `fhp_linkml.json`, like FHR; the published copy is written explicitly with `--output fhp.json`

## Phase 2: Foundational (blocking prerequisites)

- [X] T002 Write `FHR-Specification/tests/test_fhp_schema.py` (must fail first). It checks:
  - `fhp.json` equals `generate_fhp()`;
  - required fields;
  - accepted and rejected values for every FHP field (data-model §1–4, including `geneticCode` 7/8/17–20, `sourceType: curated`, the FHR-only keys, `null`, extra keys in every object, and `lineageDataset` without `_odbNN`);
  - the FHP schema URL pattern;
  - that FHR's `fhr.json` and its generated schema are unchanged.
- [X] T003 Create `FHR-Specification/fhp_linkml.yml` (data-model.md, research D-04 to D-07). Generate `FHR-Specification/fhp.json`. T002 then passes
- [X] T004 [P] Extend `FHR-Specification/scripts/check_linkml.py` to check both types (FHR: `fhr.json` against `generate()`; FHP: `fhp.json` against `generate_fhp()`). Report differences per type
- [X] T005 [P] Create `FHR-Specification/.github/schema-baseline-fhp.json` with `check_schema_drift.py --schema fhp.json --baseline … --update`, after reviewing the schema. Add the FHP drift step to `.github/workflows/check-schema-drift.yml`, and the FHP example and LinkML steps to `validate-specification.yml`

**Checkpoint**: the FHP schema exists, is generated and is drift-guarded.

---

## Phase 3: User Stories 1 and 2 - Predicted and database sets (P1) 🎯 MVP

**Goal**: valid FHP records for predicted sets (with parents) and database sets (with sources,
and no chain).

**Independent Test**: `python scripts/validate_examples.py --schema fhp.json --examples examples/fhp`.

- [X] T006 [P] [US1] Write `FHR-Specification/examples/fhp/minimal-predicted.fhp.json` and `rich-predicted.fhp.yaml`. They are synthetic, with labelled placeholders; the rich one has two `derivedFrom` parents (FHR genome and FHGFF3 annotation, `translatedFrom`), `geneticCode`, `isoformPolicy`, `predictionSoftware`, `sequenceStats` and `completeness`
- [X] T007 [P] [US2] Write `FHR-Specification/examples/fhp/minimal-database.fhp.json` and `rich-database.fhp.json` for the UniProt `UP000005640` download, as research D-13 describes. They have no `derivedFrom`; the source gives name, release, set identifier, URL and asserted assembly accession; the rich one adds UniProt's published counts and BUSCO report, cited in `documentation`
- [X] T008 [US1] Write `FHR-Specification/examples/fhp/example.fhp.fasta`: an amino-acid body with `*` and `B Z J X U O`, combined with the minimal predicted record and a real checksum computed by the conformance oracle, not by the toolkit
- [X] T009 [US1] Write `FHR-Specification/docs/FHP.md`. It covers purpose and ethos; fields (from data-model.md); `sourceType` semantics; assertion versus verification (FR-013, FR-014); rules **[P1]** and **[P2]**; the shared rules R1–R10 by reference; deferred forms (JSON-LD, microdata); and the branch note (D-12)

## Phase 4: User Story 3 - Mixed sets (P2)

- [X] T010 [P] [US3] Write `FHR-Specification/examples/fhp/minimal-mixed.fhp.json` and `rich-mixed.fhp.yaml`: one parent file, one database source and one described manual contribution, with per-source counts that do not add up (US3 AS2)

## Phase 5: User Story 4 - Conformance and toolkit (P2)

**Goal**: byte-exact vectors, and toolkit support for every command.

**Independent Test**: `check_conformance.py --schema` and
`check_conformance.py --converter <toolkit> --require-format fhp-fasta`.

- [X] T011 [US4] Extend `FHR-Specification/scripts/make_conformance.py` with the `fhp-fasta` kind and the vectors of contracts/conformance.md. It adds the P1/P2 rules and covers the protein body's residues. `reference_checksum` treats `fhp-fasta` as a FASTA container. Regenerate `FHR-Specification/conformance/`
- [X] T012 [US4] Extend `FHR-Specification/scripts/check_conformance.py`:
  - `fhp-fasta` in PREFIXES and COMMANDS (`fhr-fasta-validate`);
  - `docs/FHP.md` in RULE_DOCUMENTS;
  - `--schema` validates `fhp-fasta` vectors against `fhp.json`, checks that invalid P1 metadata fails `fhp.json` and that P2 metadata fails `fhr.json`.
  Update `tests/test_conformance.py` for the counts. Add `--skip-format fhp-fasta` to the released-converter CI step
- [X] T013 [US4] Extend `FHR-Specification/scripts/check_release.py` to compare the toolkit's `bioheaders/fhp_schema.json` with `fhp.json` when the toolkit has it, and require it from the toolkit version that ships FHP
- [X] T014 [P] [US4] Write `FAIR-bioHeaders-Tools/tests/fhp_test.py` (must fail first). It covers:
  - schema selection (FHP URL → FHP; anything else → FHR; FHR messages unchanged);
  - `validate`, `verify`, `combine` and `strip` on the FHP fixtures, with byte preservation for every residue class;
  - `.faa` input;
  - `combine` default naming;
  - refusing FHP JSON-LD and microdata output;
  - every FHP conformance vector copied into `tests/fixtures/fhp/`, with its expected outcome.
- [X] T015 [US4] Implement the toolkit changes of contracts/cli.md "Schema selection" in `FAIR-bioHeaders-Tools/bioheaders/__init__.py` and `bioheaders/cli.py`. Bundle `bioheaders/fhp_schema.json` and include it in the package data. T014 then passes, apart from the link tests

## Phase 6: User Story 1 (continued) - Link check (P1)

- [X] T016 [US1] Add link-check tests to `FAIR-bioHeaders-Tools/tests/fhp_test.py` (must fail first). They cover `matched`, `not matched` (a parent of the same type with another checksum), `not checked` (none supplied; a `.gff3` parent), `not a recorded parent`, `--require-all`, the exit codes, that no file is modified (mtime and bytes), and the identity-only notice
- [X] T017 [US1] Implement `bioheaders verify-links` in `FAIR-bioHeaders-Tools/bioheaders/cli.py` per contracts/cli.md. T016 then passes

## Phase 7: User Story 5 - Assessment (P3)

- [X] T018 [P] [US5] Update the FHP wording in `FAIR-bioHeaders-Tools/bioheaders/assess/suggestions.py`, and add an assessment test that an FHP-headed file reports FHP schema conformance

## Phase 8: Polish and cross-cutting

- [X] T019 [P] Update `FHR-Specification/README.md` (family section: FHP draft, link to docs/FHP.md), `AGENTS.md` (repository map: `fhp_linkml.yml`, `fhp.json`, `examples/fhp/`) and `CHANGELOG.md` (Unreleased: FHP draft; no FHR change)
- [X] T020 [P] Update `FAIR-bioHeaders-Tools/README.md` and `CHANGELOG.md` (Unreleased: FHP support, `verify-links`, `.faa`)
- [X] T021 Run every FHR-Specification gate in plan.md and quickstart V1–V5, then V6 with the toolkit branch
  *Status (2026-10-11):* the spec gates all pass: unittest 126, both example sets, `check_linkml` for both types, both drift baselines, `make_jsonld --check`, `check_conformance --schema` (158 vectors) and `check_release`. fhr 0.3.3 passes with `--skip-format fhp-fasta`, and without the skip it fails the FHP vectors as expected. V6 with the toolkit branch: 158/158 vectors (`--require-format fhp-fasta --require-format jsonld`), and `check_release.py --converter` matches the FHP schema and example copies
- [X] T022 Run every toolkit gate on Python 3.9 and 3.13 (pytest, ruff, isort, black, `poetry build`, `python -m build compat/fhr`), plus the installed-wheel check outside the checkout, including `bioheaders validate` on an FHP example
- [X] T023 Open the PRs, specification first. Comment briefly with the PR links on #47, #50, #55 and Tools#33. Record follow-ups F-01 to F-07 (plan.md) on #47

## Status (2026-10-11)

- **FHR-Specification#89** (merged) implements T001–T013, T019 and T021.
- **FAIR-bioHeaders-Tools#48** (merged) implements T014–T018, T020 and T022:
  - Python 3.13: 1096 passed; Python 3.9: 1055 passed (50 skipped);
  - V6: 158/158 vectors through the toolkit;
  - `check_release.py` matches the FHP schema and example copies.
- **Deviations from the plan as written:**
  - `verify-links` exits 3, not 1, when a parent does not match, following `bioheaders assess`
    (contracts/cli.md updated).
  - SC-002 was split into SC-002 and SC-002a. Strip followed by combine restores the body byte
    for byte, not the original file: combine writes its own header and places ordinary comments
    after it.
  - `fhp.json` leaves out LinkML's `metamodel_version`, which varies with the installed runtime.
  - The FHP conformance vectors are written from a record dict, so `make_conformance.py` stays
    standard-library only.
- Follow-ups F-01 to F-07 (plan.md) are recorded on #47.

## Dependencies

- T001 → T003 → T004/T005 → the examples (T006–T010) → T011 → T012.
- T013 needs T015, which depends on T003's `fhp.json`.
- The toolkit tasks (T014–T018) need `fhp.json` and the vectors (T011).
- T021–T023 come last.
