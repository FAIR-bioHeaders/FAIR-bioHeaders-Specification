# Implementation Plan: Schema versions and schema selection

**Branch**: `012-schema-versioning` (FHR-Specification, from `release-v0.4`),
`schema-selection` and `v04-schemas` (FAIR-bioHeaders-Tools), `schema-selection` (gff3-validator)
| **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-schema-versioning/spec.md` (clarified 2026-10-14)

## Summary

`schemaVersion` becomes a `"MAJOR.MINOR"` string: FHR `"2.0"`, FHP `"1.0"`, FHGFF3 `"1.0"` on the
v0.4 line. A registry (`schemas/versions.json`) records each release's versions. One selection rule
(V1–V5) maps a file's `schema` URL to a header type and a schema: raw-main is current, versioned
URLs select their release, and unknown versions are unsupported. Examples and vectors cite the
v0.4.0 versioned URLs, and new vectors cover selection.

**FHR-Specification (`release-v0.4`)**
- Core `schemaVersion` as a string with the version pattern; per-type enums; FHP and FHGFF3
  `schema` patterns accept the V1–V3 forms.
- Regenerated `fhr.json`, `fhp.json` and `fhgff3.json`, with deliberately updated baselines.
- `schemas/versions.json`; `docs/SCHEMA-VERSIONS.md` (policy and rule); updates to FORMAT.md,
  SCHEMA-CHANGES-v0.4.md, FHP.md (P2), FHGFF3.md (G3), MICRODATA.md, JSONLD.md, README and
  CHANGELOG.
- Examples, vectors (V1–V5 added), assessment fixtures and JSON-LD files regenerated.
- `check_conformance.py --schema` implements the rule, with released schemas from tags (D-07); the
  validate job fetches tags. The release-line converter job runs the toolkit's v0.4 branch at a
  pinned commit (D-09).

**FAIR-bioHeaders-Tools**
- One draft PR (FAIR-bioHeaders-Tools#57), merged with FHR-Specification v0.4.0: the rule in
  `bioheaders/selection.py`; bundled copies in `bioheaders/schemas/` (`bundled.json`, frozen
  v0.3.x and v0.4.0 copies); the v0.4 current copies, examples and fixtures; unsupported-version
  errors in every command, `verify-links`, the GFF3 header report and `assess` (D-09).

**gff3-validator**
- Tests that the header checks report unsupported-version and recognise the w3id FHGFF3 form, run
  when the installed toolkit supports the rule; the `headers` extra moves to the toolkit release
  that has it (follow-up F-02).

## Technical Context

**Language/Version**: Python 3.13 (specification scripts, CI); toolkit and validator Python
3.9–3.13.

**Primary Dependencies**: LinkML 1.11.1, jsonschema, PyYAML. No new dependency.

**Testing**: unittest (specification); pytest (toolkit, validator).

**Constraints**: offline; no rewriting of user files; assembly `version` untouched; releases and
tags are not created.

**Scale/Scope**: 3 schemas, about 20 examples, about 190 regenerated vectors plus 10 new ones,
5 assessment fixtures, 1 new toolkit module.

## Constitution Check

| Principle | Status |
|---|---|
| I. Published schema is the contract | Pass. Schemas regenerated; `check_linkml.py` checks all three; baselines updated deliberately with the diff explained in SCHEMA-CHANGES-v0.4.md |
| II. Compatibility before tightening | Pass by design: this is the explicit, reviewed major change, with a migration note (D-10) and a changelog entry |
| III. Preserve bytes | Pass. Checksums recomputed by the generators; no rewriting of user files |
| IV. No invented metadata | Pass. Version numbers are maintainer decisions |
| V. Minimal and interoperable | Pass. One small registry file; offline selection |
| Decision boundaries | Pass. No release, tag, DOI, w3id or website change |

## Project Structure

```text
specs/012-schema-versioning/
├── spec.md, research.md, data-model.md, quickstart.md, plan.md, tasks.md
├── contracts/schema-selection.md
└── checklists/requirements.md

FHR-Specification/ (release-v0.4)
├── schemas/core.yaml, schemas/versions.json (new)
├── fhr_linkml.yml, fhp_linkml.yml, fhgff3_linkml.yml
├── fhr.json, fhp.json, fhgff3.json, .github/schema-baseline*.json
├── docs/SCHEMA-VERSIONS.md (new), FORMAT.md, SCHEMA-CHANGES-v0.4.md, FHP.md, FHGFF3.md, MICRODATA.md, JSONLD.md
├── scripts/make_conformance.py, check_conformance.py, make_assessment_fixtures.py, make_jsonld.py
├── examples/, conformance/, assessment/, jsonld/, mappings/ (regenerated)
├── tests/
└── .github/workflows/validate-specification.yml

FAIR-bioHeaders-Tools/
├── bioheaders/schemas.py (new), bioheaders/schemas/ (new: registry, released copies)
├── bioheaders/__init__.py, cli.py, gff3.py, assess/conformance.py
└── tests/schema_selection_test.py (new)

gff3-validator/
└── tests/ (selection tests, skipped without support)
```

## Branches and the two `main`s

- The schema work is on `release-v0.4`. `main` gets these docs and changes at the release, when
  `release-v0.4` is merged into `main`; until then `main` keeps the v0.3 schemas, so the
  specification's and the toolkit's `main` stay consistent (`check_release.py` on `main`).
- Toolkit step 1 merges to `main`: it adds behaviour but changes no result for files that cite
  raw-main. Step 2 is a draft PR that release-line CI installs by commit.

## Phases

- Phase 0: [research.md](research.md). Phase 1: [data-model.md](data-model.md),
  [contracts/](contracts/), [quickstart.md](quickstart.md). Phase 2: [tasks.md](tasks.md).

## Follow-ups

| Id | Follow-up | Why deferred |
|---|---|---|
| F-01 | Merge toolkit step 2 and release the toolkit with the v0.4 copies | Waits for FHR-Specification v0.4.0 |
| F-02 | gff3-validator `headers` extra → that toolkit release; drop CI pin | Release action |
| F-03 | Website selection (#15/#16) | David's repository |
| F-04 | Release-line CI: replace the pinned toolkit commit with the toolkit release | After F-01 |

## Complexity Tracking

No constitution violations.
