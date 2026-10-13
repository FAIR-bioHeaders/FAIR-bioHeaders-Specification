---

description: "Task list for feature 007: GFF3 annotation header (FHGFF3)"
---

# Tasks: GFF3 annotation header (FHGFF3)

**Input**: Design documents from `/specs/007-gff3-header/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: These are required (constitution III: every parsing rule needs a conformance example).
Within each story, the test tasks come first and must fail before the implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: The user story (US1–US6)

## Path Conventions

- `FHR-Specification/`: this repository.
- `FAIR-bioHeaders-Tools/`: the `fair-bioheaders` package (local checkout `../FHR-File-Converter`).
- `gff3-validator/`: the validator.

No task releases, tags, archives a DOI or changes w3id.org.

---

## Phase 1: Setup

- [X] T001 Create `FHR-Specification/schemas/shared.yaml` with `Software`, `Source`, `Completeness` and `BuscoMode` moved from `fhp_linkml.yml`, and make `fhp_linkml.yml` import it. Regenerate `fhp.json` and confirm it is byte-identical (D-04)
- [X] T002 Add `--type fhgff3` to `FHR-Specification/json-schema-generator.py` with contracts/fhgff3-schema.md steps 1–5

## Phase 2: Foundational

- [X] T003 Write `FHR-Specification/tests/test_fhgff3_schema.py` (fails first). It checks:
  - the generator output equals `fhgff3.json`;
  - `fhr.json` and `fhp.json` are unchanged;
  - required fields and closed objects;
  - both genome-link forms, both together, neither, half a reference, two `annotates` items, and
    `annotates` with header type FHP;
  - `featureCounts` and `soVersion` shapes;
  - FHR-only and FHP-only keys rejected;
  - every example valid
- [X] T004 Write `FHR-Specification/fhgff3_linkml.yml` (data-model.md) and generate `fhgff3.json`. Add `.github/schema-baseline-fhgff3.json` and the drift check to CI
- [X] T005 Extend `FHR-Specification/scripts/check_linkml.py` and `scripts/check_release.py` to FHGFF3

## Phase 3: User Stories 1 and 2 (P1): genome links

- [X] T006 [P] [US1] Examples in `FHR-Specification/examples/fhgff3/`:
  - `genome.fhr.fasta` (a synthetic FHR genome);
  - `annotation.fhgff3.gff3` and `.yaml` (checksum link);
  - `minimal-reference.fhgff3.json` (reference link);
  - `rich.fhgff3.yaml` (both links, software, SO version, counts, sources);
  - `embedded-fasta.fhgff3.gff3`;
  - `no-header.gff3`, `header-invalid.fhgff3.gff3` and `stale-parent.fhgff3.gff3`.

  Placeholders are labelled (D-12)
- [X] T007 [US1] `FHR-Specification/docs/FHGFF3.md`: status (draft), files, fields, the genome link (both forms, checksum authoritative), rules G1–G3, the native-directive cross-check, examples and follow-ups. Link it from `README.md` (header family section) and `AGENTS.md`

## Phase 4: User Story 4 (P2): conformance

- [X] T008 [US4] Extend `FHR-Specification/scripts/make_conformance.py` with the `fhgff3` vectors of contracts/conformance.md, using the standard library only. Regenerate `conformance/`, and extend `tests/test_conformance.py`. `check_conformance.py --converter` skips `fhgff3` for converters without GFF3 support unless `--require-format fhgff3` is given
- [X] T009 [US4] Update `FHR-Specification/CHANGELOG.md`. Run every specification gate

## Phase 5: Toolkit (US1–US4, US6)

- [X] T010 [US4] Tests first, in `FAIR-bioHeaders-Tools/tests/fhgff3_test.py`:
  - the `fhgff3` vectors from `FHR-Specification/conformance` (fixtures);
  - combine/strip byte preservation, including `##FASTA`, CRLF, gzip and BGZF;
  - a header before `##gff-version`;
  - late `#~` lines;
  - schema selection;
  - cross-check warnings;
  - `verify-links` for GFF3 files and `genomeReference`;
  - the FHR → FHGFF3 → FHP chain;
  - FHR and FHP outputs unchanged
- [X] T011 [US4] Scanner GFF3 mode, `input_gff3`/`output_gff3`, `FHGFF3_SCHEMA`, `header_type`/`schema_for` in `bioheaders/__init__.py`. Bundle `fhgff3_schema.json`
- [X] T012 [US4] The GFF3 kind, `fhr-gff3-combine|strip|validate`, generic-command support and messages in `bioheaders/cli.py`. Add the scripts in `pyproject.toml`
- [X] T013 [US1] [US2] `verify-links` for GFF3 FILE and PARENT, and `genomeReference` results (D-08)
- [X] T014 [US3] `gff3_directives`, `cross_check` and the warnings in `verify` and `verify-links` (D-07)
- [X] T015 [US6] `assess` recognises FHGFF3. Remove the "not specified yet" reason
- [X] T016 `gff3_header_report` for the validator (contracts/cli.md, Library)
- [X] T017 README and CHANGELOG. Run the toolkit gates on 3.9 and 3.13, and the installed-wheel check

## Phase 6: User Story 5 (P2): gff3-validator

- [X] T018 [US5] Tests first: header conformance cases (no header, valid, invalid placement, bad checksum, schema error, no genome link, stale parent with `--genome`, cross-check warning). Header and feature results stay separate
- [X] T019 [US5] Implement HDR-004 to HDR-010 in `gff3_validator/header.py` and `engine.py` (contracts/validator.md). Update the catalogue (statuses, HDR-010) in both copies, widen the `headers` extra to `>=0.5,<0.7`, and install the toolkit from a pinned commit in CI for the header tests
- [X] T020 [US5] Update the validator README and CHANGELOG, and run its gates

## Phase 7: Polish

- [X] T021 Open the PRs in order (specification, toolkit, validator). Comment with links on #48, #50, #55, Tools#33, Tools#34 and FHR-Specification#62
- [X] T022 Record the task status and follow-ups F-01 to F-07 in this file

## Dependencies

- Setup → Foundational → US1/US2 → US4 (specification).
- The toolkit tasks need the specification's vectors and schema.
- The validator needs the toolkit commit.

## Status (2026-10-13)

All tasks are done:
- FHR-Specification#94 (T001–T009);
- FAIR-bioHeaders-Tools#51 (T010–T017);
- gff3-validator#13 (T018–T020);
- this record (T021–T022).

No release, tag, DOI or w3id change was made.

Deviations recorded during implementation:
- `gff3_header_report` is `bioheaders.gff3.header_report`, in a submodule, because it uses the
  command implementations (contracts/cli.md is updated).
- The toolkit's usage error for a non-sequence file now names GFF3 (`Expected a FASTA, GFA or
  GFF3 file`).
- A GFF3 parent given to `verify-links` is now checksummed instead of reported as "GFF3 headers
  are not specified yet". Both are intended consequences of GFF3 support. FHR and FHP file
  output is unchanged.
- In the gff3-validator, an HDR-009 comparison that cannot be made is listed under skipped
  checks, not reported as a finding. Conformance cases carry `headers: checked | unavailable`,
  and tests run without header support unless marked, so results do not depend on the
  installed toolkit.

Follow-ups, beyond F-01 to F-07 in plan.md:

| Id | Follow-up |
|---|---|
| F-08 | The examples use `##species https://identifiers.org/taxonomy:9606`. GFF3 prefers NCBI's browser URL, and the gff3-validator warns about it (GFF-DIR-007). Their synthetic CDS also draws BIO-006/BIO-007 warnings with `--genome`. Switching to the NCBI form changes the examples' checksums and the toolkit's companion copies |
| F-09 | GFF3 support in the toolkit's Nextflow modules (`fairbioheaders/combine`, `verify`) |
| F-10 | The gff3-validator's `headers` extra pinned to the first fair-bioheaders release with FHGFF3 support, and its CI step replaced by that release |
