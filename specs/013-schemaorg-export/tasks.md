# Tasks: Enriched schema.org export

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

`[P]` means the task can run in parallel. Story labels refer to the spec's user stories.

## Phase 1: Setup

- [X] T001 Extend the pinned schema.org v30.1 subset with the export terms: `EXPORT_SCHEMAORG_TERMS` in `scripts/make_jsonld.py`, regenerated with `--schemaorg-subset` from the pinned file (SHA-256 `0a4b8c4c…`)
- [X] T002 [P] Write the source-record fixtures in `tests/fixtures/schemaorg-export/<case>/record.json`, with `export-context.json` where a case needs one. Every record must validate against `fhr.json`

## Phase 2: Tests first

- [X] T003 [P] `tests/test_schemaorg_export.py`:
  - fixtures and example current;
  - shape;
  - author subjects;
  - conditions (DOI, HowTo, legacy software, IRI values, funding, SeqCol);
  - statistics;
  - Bioschemas claim;
  - no fabricated values;
  - reader refusal;
  - unmapped keys;
  - canonical form unchanged;
  - export table (schema, paths, targets, alternatives, units);
  - domains, ranges and relationship direction with PyLD
- [X] T004 [P] Update `tests/test_jsonld_mappings.py` for the second `rdfs:subPropertyOf schema:identifier` link

## Phase 3: User Stories 1 and 2 (P1): the export graph and its subjects

- [X] T005 [US1] `to_export`, `export_text`, `is_export`, `export_unmapped_keys` and `export_outputs` in `scripts/make_jsonld.py`. `generate()` and `--check` cover `examples/example.fhr.export.jsonld` and every `expected.jsonld`
- [X] T006 [US1] Refuse export documents in `canonical_record` (R-11)
- [X] T007 [US2] Metadata-record `CreativeWork`: `about`, `creator`, `schemaVersion` and `fhr:schemaVersion` (R-03)

## Phase 4: User Story 3 (P2): funding, article and identifiers

- [X] T008 [US3] `Grant` (R-05), `ScholarlyArticle` via `subjectOf` with the strict DOI and the citation fallback (R-07), and the SeqCol `PropertyValue` (R-08)
- [X] T009 [US3] `fhr:seqcol_id rdfs:subPropertyOf schema:identifier`: `broad_mappings` in `schemas/core.yaml`, the vocabulary regenerated and the mapping-table note added

## Phase 5: User Story 4 (P2): statistics and provenance

- [X] T010 [US4] `Observation` per numeric statistic with UO units; `readTechnology` stays canonical (R-04)
- [X] T011 [US4] `CreateAction` with software instruments, the legacy string, the ordered command line and the opt-in `HowTo`; the sequencing instrument stays canonical (R-06)

## Phase 6: Table, docs and toolkit

- [X] T012 [P] `mappings/fhr-schemaorg-export.yml` and `contracts/export-table.schema.json` (R-09)
- [X] T013 [P] `docs/SCHEMAORG-EXPORT.md` (X1–X9). Link it from README, `docs/JSONLD.md` and AGENTS.md. Add a CHANGELOG entry
- [X] T014 `scripts/check_release.py` compares the export example and fixtures when the toolkit has them
- [X] T015 FAIR-bioHeaders-Tools:
  - `to_export` in `bioheaders/jsonld.py`, with the refusal in `from_jsonld`;
  - `convert --jsonld-profile export`, with export unmapped-key warnings;
  - byte-identical copies of the example and fixtures;
  - `tests/jsonld_export_test.py`;
  - README and CHANGELOG
- [X] T016 Gates in both repositories (plan.md)
- [X] T017 Quickstart V5: validator.schema.org with `examples/example.fhr.export.jsonld` and the full fixture
  *Result (2026-10-14):*
  - **Full fixture:** 0 errors, 0 warnings. Recognised: Dataset, CreativeWork, CreateAction, HowTo, Observation, Grant, ScholarlyArticle, PropertyValue, Taxon, Person, SoftwareApplication and Property (for `measuredProperty`).
  - **Example:** one finding, the text licence "public domain", reported once for each node that refers to the assembly (10 in total). This is the example's data (X5).

## Follow-ups (not in this feature)

- F-01: structured voucher specimens (#101).
- F-02: at the next `release-v0.4` sync, check that `nameType` typing and the scaffold statistics flow into the export. The shared typing function and the unit table already cover them. The export table gains the v0.4 paths.
- F-03: decide whether web embedding should prefer the export once #56 defines its documents. Until then, the canonical form stays the default (R-01).
- F-04: an export for FHP and FHGFF3. The toolkit refuses JSON-LD for those types today.
