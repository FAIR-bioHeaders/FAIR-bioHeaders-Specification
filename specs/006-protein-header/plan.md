# Implementation Plan: Protein FASTA header (FHP)

**Branch**: `006-protein-header-spec` (FAIR-bioHeaders-Specification), `fhp-support` (FAIR-bioHeaders-Tools) | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-protein-header/spec.md` (clarified 2026-10-11)

## Summary

FHP brings the FHR header to protein FASTA without changing FHR or the core. The work has two
parts.

**FAIR-bioHeaders-Specification**
- `fhp_linkml.yml` imports `schemas/core.yaml` and adds:
  - required `proteome` and `sourceType`;
  - optional `source`, `geneticCode`, `isoformPolicy`, `predictionSoftware`,
    `predictionProtocol`, `sequenceStats` and `completeness`;
  - the core `derivedFrom`.
- `fhp.json` is generated from it and committed, with its own drift baseline.
- Examples cover predicted, database and mixed sets.
- `docs/FHP.md` states rules P1–P2.
- Conformance vectors (format `fhp-fasta`) cover R1–R10 on amino-acid FASTA and P1–P2 (#50).

**FAIR-bioHeaders-Tools**
- The toolkit bundles the FHP schema and selects it from the `schema` URL, so every command
  handles FHP.
- It adds `.faa` and a `verify-links` command that reports `matched`, `not matched` or
  `not checked` per parent and never writes.

**Deferred**
- JSON-LD and microdata for FHP: the LinkML annotations are in place now (research D-08).
- GFF3 parent checksums: spec 007.

All decisions with alternatives are in [research.md](research.md) (D-01 to D-13).

## Technical Context

**Language/Version**:
- FAIR-bioHeaders-Specification scripts: Python 3.13 (CI).
- Toolkit: Python 3.9–3.13; gates run on 3.9 and 3.13.

**Primary Dependencies**:
- LinkML 1.11.1 (pinned) for schema generation.
- jsonschema and PyYAML, as today.
- No new dependency in either repository.

**Storage**: Files only: schemas, examples and conformance vectors.

**Testing**:
- FAIR-bioHeaders-Specification: `unittest`, including new `tests/test_fhp_schema.py` and extended
  conformance tests.
- Toolkit: pytest, with new `tests/fhp_test.py`.

**Target Platform**: Offline command line and library; the same as FHR.

**Project Type**: A specification plus a library/CLI, in two repositories.

**Performance Goals**: Unchanged streaming behaviour. The link check reads each parent once.

**Constraints**:
- FHR schema, examples, vectors and tool output stay byte-identical (SC-005).
- No network access.
- No invented metadata.

**Scale/Scope**:
- 1 new schema with 16 FHP-specific keys and 5 objects.
- About 7 examples.
- About 23 vectors.
- 1 new CLI command.

## Constitution Check

| Principle | Status |
|---|---|
| I. Published schema is the contract | Pass. `fhp.json` is generated and committed, and `check_linkml.py` checks both types. `fhr.json` is untouched |
| II. Compatibility before tightening | Pass. Additive new type; FHR is unchanged. FHP is new, so its closed objects break nothing |
| III. Preserve bytes | Pass. Same checksum and parsing rules, and byte-preservation tests on amino-acid vectors |
| IV. No invented metadata | Pass. Placeholders are labelled. UniProt values are cited with fetch dates (D-13). All optional fields are omitted when unknown |
| V. Minimal and interoperable | Pass. Two required fields beyond the core, and no new dependency |
| Decision boundaries | Pass. No release, tag, DOI or w3id change. F-05 and F-07 are recorded as maintainer actions |

## Project Structure

### Documentation (this feature)

```text
specs/006-protein-header/
├── spec.md, research-notes.md, research.md, data-model.md, quickstart.md, plan.md, tasks.md
├── contracts/ (fhp-schema.md, cli.md, conformance.md)
└── checklists/requirements.md
```

### Source Code

```text
FAIR-bioHeaders-Specification/
├── fhp_linkml.yml                     # new
├── fhp.json                           # new, generated
├── json-schema-generator.py           # --type fhp
├── .github/schema-baseline-fhp.json   # new
├── .github/workflows/*.yml            # FHP checks; skip fhp-fasta for fhr 0.3.3
├── examples/fhp/                      # new
├── docs/FHP.md                        # new (rules P1–P2)
├── scripts/check_linkml.py, check_schema_drift.py, make_conformance.py, check_conformance.py, check_release.py
├── conformance/                       # regenerated (+ fhp-fasta vectors)
├── tests/test_fhp_schema.py           # new
└── README.md, CHANGELOG.md, AGENTS.md

FAIR-bioHeaders-Tools/
├── bioheaders/fhp_schema.json         # new, a copy of fhp.json
├── bioheaders/__init__.py             # header_type, schema_for, fhr_validate
├── bioheaders/cli.py                  # messages, .faa, combine naming, refusing FHP JSON-LD/microdata, verify-links
├── bioheaders/assess/suggestions.py   # FHP wording
├── tests/fhp_test.py, tests/fixtures/fhp/  # new
└── README.md, CHANGELOG.md
```

**Structure Decision**: Follow the FHR layout (D-01). There is one shared conformance manifest
(D-09), and one schema-selection point in the toolkit (D-10).

## Phases

- **Phase 0, research**: done ([research.md](research.md)).
- **Phase 1, design**: done ([data-model.md](data-model.md), [contracts/](contracts/),
  [quickstart.md](quickstart.md)).
- **Phase 2, tasks**: [tasks.md](tasks.md).

## Branches and release

- FHP is developed on `main` (D-12). The next main → `release-v0.4` sync carries it, and there
  it inherits the v0.4 core patterns. No separate v0.4 PR is needed.
- No FHP tag, DOI or w3id alias is created. Those, and the choice of release line (F-07), are
  maintainer actions.

## Follow-ups (recorded, not in this feature's tasks)

| Id | Follow-up | Why deferred |
|---|---|---|
| F-01 | Generalise `make_jsonld.py` to FHP: an FHP context, FHP terms in the family vocabulary, mapping-table rows | Feature-sized; half-doing it would publish an inconsistent vocabulary (D-08) |
| F-02 | Microdata for FHP (typed reading and writing) | Toolkit microdata typing is FHR-schema-driven (D-08) |
| F-03 | GFF3 parents in `verify-links` | GFF3 header rules are spec 007 (D-10) |
| F-04 | Website Draft entry for FHP (fair-bioheaders.github.io) | Separate repository, maintainer content (D-11) |
| F-05 | w3id alias `/fair-bioheaders/fhp/vX.Y.Z` and its `schema` pattern | Needs a release and tag scheme (D-02) |
| F-06 | Promote `Software` to the core when FHT or FHGFF3 need it | Keeps the core unchanged now (D-04) |
| F-07 | Release FHP v0.1 from a line that has the v0.4 core | Maintainer release decision (D-12) |

## Complexity Tracking

No constitution violations.
