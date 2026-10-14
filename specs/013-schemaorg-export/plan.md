# Implementation Plan: Enriched schema.org export

**Branch**: `013-schemaorg-export` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

## Summary

This plan adds a one-way schema.org export profile beside the canonical JSON-LD of feature 011. It
covers David Molik's #56 proposals: the metadata-record `CreativeWork`, `Grant`, statistics as
`Observation` nodes, the `CreateAction` for assembly provenance, the article as a
`ScholarlyArticle` via `subjectOf`, and the structured SeqCol identifier. The canonical form gains
one vocabulary triple, `fhr:seqcol_id rdfs:subPropertyOf schema:identifier`. Nothing else in it
changes.

## Technical context

- **FAIR-bioHeaders-Specification**:
  - Python 3.13 scripts.
  - The reference exporter is `to_export` in `scripts/make_jsonld.py`. It uses only the standard
    library, like the canonical writer.
  - Tests use `unittest`, PyLD 3.3 (`requirements-jsonld.txt`) and rdflib (from
    `requirements-linkml.txt`).
- **FAIR-bioHeaders-Tools**:
  - `bioheaders/jsonld.py` gains `to_export`, which needs no new dependency.
  - The CLI gains `--jsonld-profile {canonical,export}` on `convert`.
  - Python 3.9+.
- **No schema change**: `fhr.json`, `fhp.json` and `fhgff3.json` are untouched.
  `schemas/core.yaml` gains one `broad_mappings` annotation on `seqcol_id`, which changes no
  validation. `check_linkml.py` and the drift baselines are unchanged.

## Constitution check

| Principle | How this plan meets it |
| --- | --- |
| I. The schema is the contract | No schema change. The vocabulary triple is generated from LinkML. |
| II. Compatibility | The canonical output is byte-identical (SC-002). The export is opt-in. |
| III. Preserve data | The export is one-way. The canonical form remains the exchange format. |
| IV. No invented metadata | X5 says so, and `test_no_fabricated_values` checks it. Unclassified authors stay `fhr:Agent` (R-12). |
| V. Minimal | No new runtime dependency. The context is three entries long. |

## Project structure

```text
FAIR-bioHeaders-Specification/
  docs/SCHEMAORG-EXPORT.md                   rules X1–X9
  mappings/fhr-schemaorg-export.yml          export table (R-09)
  scripts/make_jsonld.py                     to_export, export_outputs, subset terms
  examples/example.fhr.export.jsonld         generated
  tests/fixtures/schemaorg-export/<case>/    record.json, export-context.json?, expected.jsonld
  tests/fixtures/schemaorg-v30.1-subset.json regenerated from the pinned release
  tests/test_schemaorg_export.py
  schemas/core.yaml                          seqcol_id broad_mappings sdo:identifier
  specs/013-schemaorg-export/                this feature
FAIR-bioHeaders-Tools/
  bioheaders/jsonld.py                       to_export, is_export, refusal in the readers
  bioheaders/cli.py                          --jsonld-profile
  examples/example.fhr.export.jsonld, tests/fixtures/schemaorg-export/   byte-identical copies
  tests/jsonld_export_test.py
```

## Gates

FAIR-bioHeaders-Specification:
- `python -m unittest discover -s tests`
- `python scripts/make_jsonld.py --check`
- `python scripts/validate_examples.py`
- `python scripts/check_linkml.py`
- `python scripts/check_schema_drift.py`
- `python scripts/check_conformance.py --schema`
- `python scripts/check_release.py --converter ../FAIR-bioHeaders-Tools`

FAIR-bioHeaders-Tools:
- `pytest` on Python 3.9 and 3.13
- `ruff`, `isort` and `black`
- `poetry build`

## Release line

The feature lands on `main`. It reaches `release-v0.4` at the next sync. There, the exporter's
typing function already honours `nameType`, and the scaffold statistics already have units.

## Complexity tracking

None.
