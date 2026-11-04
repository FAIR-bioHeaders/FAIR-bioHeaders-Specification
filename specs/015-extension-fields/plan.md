# Implementation Plan: User-defined extension fields with an `x-` prefix

**Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md) |
**Contract**: [contracts/extension-fields.md](contracts/extension-fields.md)

## Summary

Add rule R15 (extension fields) to docs/FORMAT.md, J9 to docs/JSONLD.md and M5 to
docs/MICRODATA.md; release the rule as FHR 2.1, FHP 1.1 and FHGFF3 1.1 in v0.5.0, prepared on
`main` under the `preRelease` exception; add conformance vectors. In FAIR-bioHeaders-Tools,
bundle the new schemas, keep the v0.4.x copies, drop extension fields from JSON-LD, export and
microdata output, and reject them in JSON-LD and microdata input. In FHT-Specification, add the
rule to the draft `"1.0"` contract.

## Technical context

- Specification: LinkML 1.11.1 models (`fhr_linkml.yml`, `fhp_linkml.yml`, `fhgff3_linkml.yml`,
  `schemas/core.yaml`), `json-schema-generator.py` (post-processing for what LinkML cannot say:
  `patternProperties`, `propertyNames`, the version conditional), hand-maintained `fhr.json`
  (validation-equivalent to the generator), generated `fhp.json`/`fhgff3.json`, drift baselines,
  `scripts/make_conformance.py` (stdlib), `scripts/make_jsonld.py` (reference JSON-LD writer and
  reader), `profiles/profile_schema.py` (reuses the generator post-processing).
- Toolkit: Python 3.9+, `jsonschema` with `FormatChecker`, PyYAML; `bioheaders/selection.py`
  (V1–V6), `bioheaders/schemas/bundled.json`, `bioheaders/jsonld.py`, the FHR microdata writer in
  `bioheaders/__init__.py` and `bioheaders/fhp_microdata.py`.
- FHT: its own generator and `fht.json`; unittest suite and CI.

## Constitution check

- I (published schema is the contract): `fhr.json` is edited by hand and checked against the
  generator (`check_linkml.py`); the toolkit's copies equal it (`check_release.py`).
- II (compatibility before tightening): a relaxation. Every record valid under 2.0/1.0 stays
  valid with the same meaning (research R-02); the drift baselines are updated with the reviewed
  diff, and the CHANGELOG and SCHEMA-VERSIONS carry the migration note.
- III (bytes): checksum coverage is unchanged; no existing vector or published file is rewritten.
  Examples move to v0.5.0 only under the documented prepared-release process and get recomputed
  checksums.
- IV (no invented metadata): example extension values are labelled illustrative; no identifier
  or mapping is invented, and extension fields are not mapped to any term.
- V (minimal): no required field, no new dependency, one pattern.

## Project structure

Specification (this repository):
- `docs/FORMAT.md` (R15), `docs/JSONLD.md` (J9), `docs/MICRODATA.md` (M5),
  `docs/SCHEMAORG-EXPORT.md` (X9 and losses), `docs/SCHEMA-VERSIONS.md`, `docs/FHP.md`,
  `docs/FHGFF3.md`, `docs/SCHEMA-GAP-AUDIT.md`, `docs/insdc-coverage.md`, `README.md`,
  `llms.txt`, `CHANGELOG.md`, `conformance/README.md`
- `fhr_linkml.yml`, `fhp_linkml.yml`, `fhgff3_linkml.yml`, `json-schema-generator.py`, `fhr.json`,
  `fhp.json`, `fhgff3.json`, `.github/schema-baseline*.json`, `schemas/versions.json`
- `scripts/make_conformance.py`, `scripts/check_conformance.py`, `scripts/make_jsonld.py`,
  `conformance/`, `examples/`, tests
- `.github/workflows/validate-specification.yml` (toolkit pin, research R-05)

Toolkit (FAIR-bioHeaders-Tools): schema copies and `bioheaders/schemas/{fhr-2.1,fhp-1.1,fhgff3-1.1}.json`,
`bundled.json`, `jsonld.py`, `__init__.py`, `fhp_microdata.py`, `cli.py` (warnings, messages),
examples, tests, README, CHANGELOG, plugin skill.

FHT-Specification: `json-schema-generator.py`, `fht.json`, tests, README, `docs/FHT-MIGRATION.md`,
spec 005.

## Gates

Specification: `python -m unittest discover -s tests -v`; `validate_examples.py` for FHR, FHP and
FHGFF3; `check_linkml.py`; the three `check_schema_drift.py` runs; `make_jsonld.py --check`;
`check_conformance.py`, `--schema`, and `--converter` with the toolkit branch
(`--require-format jsonld --require-format fhp-fasta --require-format fhgff3`);
`check_release.py --converter` with the toolkit branch; `git diff --check`.
Toolkit: pytest, ruff, isort, black, `poetry build`. FHT: unittest, regeneration diff,
`check_provenance.py`.

Reviews before merging: code review and adversarial review covering unknown non-`x-` keys,
old-version records, JSON-LD pollution, YAML injection through keys and values, and the key-pattern
edge cases (spec edge cases).

## Release line

On `main`, as the prepared release v0.5.0 (`preRelease`). Tagging v0.5.0, releasing toolkit 0.9.0,
re-pinning the conformance CI to `fair-bioheaders==0.9.0` and clearing `preRelease` are the
maintainers' release steps, outside this feature.
