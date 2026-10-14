# Implementation Plan: GFF3 annotation header (FHGFF3)

**Branch**: `007-gff3-header-spec` (FAIR-bioHeaders-Specification), `fhgff3-support` (FAIR-bioHeaders-Tools), `fhgff3-header-rules` (gff3-validator) | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-gff3-header/spec.md` (clarified 2026-10-13)

## Summary

FHGFF3 brings the FHR header to GFF3 annotations without changing FHR, FHP or the core. The work
spans three repositories.

**FAIR-bioHeaders-Specification**
- `schemas/shared.yaml` takes FHP's `Software`, `Source` and `Completeness` (D-04), with
  `fhp.json` unchanged.
- `fhgff3_linkml.yml` imports the core and the shared module, and adds:
  - required `annotation`;
  - the genome link: `genomeReference`, or a core `derivedFrom` item that `annotates` an FHR
    genome;
  - optional `source`, `annotationSoftware`, `annotationProtocol`, `soVersion`, `featureCounts`
    and `completeness`.
- `fhgff3.json` is generated, with the genome-link rule added in post-processing (contracts
  step 5) and its own baseline.
- `docs/FHGFF3.md` states rules G1–G3 and the cross-check. There are examples and `fhgff3`
  conformance vectors (#50).

**FAIR-bioHeaders-Tools**
- A GFF3 kind: the leading-block scan with the `##FASTA` end (D-06), combine after
  `##gff-version`, and the `fhr-gff3-*` commands.
- FHGFF3 schema selection, native-directive cross-check warnings (D-07), `verify-links` for GFF3
  files and `genomeReference` (D-08), and assess support.

**gff3-validator**
- HDR-004 to HDR-009 and the new HDR-010 through the optional toolkit (D-11).

**Deferred**: JSON-LD and microdata (F-01), the browser build's header checks (F-04), w3id and the
release (F-02, F-03).

## Technical Context

**Language/Version**:
- FAIR-bioHeaders-Specification scripts: Python 3.13 (CI).
- Toolkit and validator: Python 3.9–3.13.

**Primary Dependencies**: LinkML 1.11.1 (pinned), jsonschema and PyYAML. No new dependency. The
validator's optional extra gets a wider version range.

**Storage**: Files only.

**Testing**: unittest (specification); pytest (toolkit, validator).

**Target Platform**: Offline command line and library. The validator also has a Pyodide browser
build, which is unchanged.

**Project Type**: A specification, a library/CLI and a validator, in three repositories.

**Performance Goals**: Streaming as today. Header checks read the file once more, at most.

**Constraints**:
- FHR and FHP schemas, examples, vectors and tool output stay byte-identical.
- No network access.
- No invented metadata.
- Plain GFF3 results are unchanged.

**Scale/Scope**:
- 1 new schema and 1 shared module.
- About 9 examples and about 24 vectors.
- 3 new CLI entry points.
- 7 validator rules (6 planned, 1 new).

## Constitution Check

| Principle | Status |
|---|---|
| I. Published schema is the contract | Pass. `fhgff3.json` is generated and committed, and `check_linkml.py` checks three types. `fhr.json` and `fhp.json` are unchanged (test) |
| II. Compatibility before tightening | Pass. A new additive type. The shared module moves classes without changing `fhp.json` |
| III. Preserve bytes | Pass. Same checksum rules, byte-preservation tests and GFF3 vectors |
| IV. No invented metadata | Pass. Synthetic data and labelled placeholders (D-12) |
| V. Minimal and interoperable | Pass. Two required items beyond the core, no new dependency, and native directives are reused, not duplicated |
| Decision boundaries | Pass. No release, tag, DOI, w3id or website change |

## Project Structure

### Documentation (this feature)

```text
specs/007-gff3-header/
├── spec.md, research-notes.md, research.md, data-model.md, quickstart.md, plan.md, tasks.md
├── contracts/ (fhgff3-schema.md, cli.md, conformance.md, validator.md)
└── checklists/requirements.md
```

### Source Code

```text
FAIR-bioHeaders-Specification/
├── schemas/shared.yaml                  # new (classes moved from fhp_linkml.yml)
├── fhp_linkml.yml                       # imports schemas/shared
├── fhgff3_linkml.yml, fhgff3.json       # new (generated)
├── .github/schema-baseline-fhgff3.json  # new
├── json-schema-generator.py             # --type fhgff3
├── scripts/check_linkml.py, check_schema_drift.py (CI), make_conformance.py, check_conformance.py, check_release.py
├── examples/fhgff3/                     # new
├── docs/FHGFF3.md                       # new
├── conformance/                         # regenerated (+ fhgff3 vectors)
├── tests/test_fhgff3_schema.py          # new
└── README.md, CHANGELOG.md, AGENTS.md, .github/workflows/*

FAIR-bioHeaders-Tools/
├── bioheaders/fhgff3_schema.json        # new copy
├── bioheaders/__init__.py               # scanner GFF3 mode, header_type, gff3 I/O, directives, cross-check, report
├── bioheaders/cli.py                    # gff3 kind and commands, verify-links, messages
├── bioheaders/assess/…                  # FHGFF3 recognition
├── pyproject.toml                       # fhr-gff3-* scripts
└── tests/fhgff3_test.py, tests/fixtures/fhgff3/

gff3-validator/
├── gff3_validator/header.py, engine.py  # HDR-004..010
├── rules/catalogue.yaml (+ package copy) # statuses, HDR-010
├── pyproject.toml                       # headers extra range
├── conformance/ (header cases)
└── .github/workflows (install toolkit from a pinned commit for header tests)
```

**Structure Decision**: Follow FHP's layout (D-01). There is one scanner (D-06) and one header
implementation, the toolkit's, used by the validator (D-11).

## Phases

- **Phase 0, research**: done ([research.md](research.md)).
- **Phase 1, design**: done ([data-model.md](data-model.md), [contracts/](contracts/),
  [quickstart.md](quickstart.md)).
- **Phase 2, tasks**: [tasks.md](tasks.md).

## Branches and release

- FHGFF3 is developed on `main`. It joins `release-v0.4` at the next main → `release-v0.4` sync,
  which the coordinator does. FHGFF3 v0.1 is released with FAIR-bioHeaders-Specification v0.4.0 (D-13).
- The toolkit's GFF3 support ships in a future 0.6.0 release. The validator's header rules need
  that release before the validator's own next PyPI release (D-11, D-14).

## Follow-ups (recorded, not in this feature's tasks)

| Id | Follow-up | Why deferred |
|---|---|---|
| F-01 | JSON-LD and microdata for FHP and FHGFF3 (`make_jsonld.py` per type) | Feature-sized (D-09) |
| F-02 | w3id alias `/fair-bioheaders/fhgff3/vX.Y.Z` | Maintainer action, with the release |
| F-03 | Website Draft entry for FHGFF3 | Separate repository (David) |
| F-04 | Header checks in the validator's browser build (bundle the toolkit in Pyodide) | Build change with its own size and CSP review |
| F-05 | Optional SeqCol computation, so reference links can be verified against plain FASTA | Needs a refget implementation and a decision on attribute profiles |
| F-06 | Promote `schemas/shared.yaml` classes to the core if FHT also needs them | Core change; FHR equivalence must be shown |
| F-07 | Toolkit 0.6.0 release, then the validator extra pinned to `>=0.6` | Release actions |

## Complexity Tracking

No constitution violations.
