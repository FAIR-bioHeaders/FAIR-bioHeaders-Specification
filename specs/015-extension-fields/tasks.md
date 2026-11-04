# Tasks: User-defined extension fields with an `x-` prefix

## Phase 1: Schemas (specification)

- [X] T001 `json-schema-generator.py`: `apply_extension_rules` adds the `patternProperties`,
  `propertyNames` and version conditional (contract) to the FHR, FHP and FHGFF3 roots and to
  profile roots that reuse them
- [X] T002 `schemaVersion` `equals_string_in` `["2.0", "2.1"]` (FHR) and `["1.0", "1.1"]` (FHP,
  FHGFF3) in the LinkML models; regenerate `fhp.json` and `fhgff3.json`; edit `fhr.json` to match
  (`check_linkml.py`)
- [X] T003 Review the schema diffs and update the three drift baselines
- [X] T004 `schemas/versions.json`: `current` and `preRelease` `v0.5.0`, release entry
  `{"FHR": "2.1", "FHP": "1.1", "FHGFF3": "1.1"}`; `tests/test_schema_versions.py`

## Phase 2: Rules and documentation

- [X] T005 docs/FORMAT.md R15 (extension fields); intro sentence on the closed top level
- [X] T006 docs/JSONLD.md J9; docs/MICRODATA.md M5; docs/SCHEMAORG-EXPORT.md X9 and losses
- [X] T007 docs/SCHEMA-VERSIONS.md: versions table, minor gating sentence, V4 example; docs/FHP.md,
  docs/FHGFF3.md, docs/SCHEMA-GAP-AUDIT.md, README.md, `llms.txt`
- [X] T008 docs/insdc-coverage.md re-pinned to the new `schemaVersion`s (no disposition change)

## Phase 3: Examples and reference implementation

- [X] T009 Examples cite v0.5.0 and the new versions (prepared-release process); recompute
  checksums of file examples; regenerate JSON-LD, microdata and export examples and fixtures
- [X] T010 `scripts/make_jsonld.py`: the reference writers leave extension fields out; the
  reference readers reject them (J9, M5)

## Phase 4: Conformance

- [X] T011 `scripts/make_conformance.py`: rules R15, J9, M5; valid vectors (FASTA, GFA, FHP, FHGFF3)
  with `x-` keys; invalid vectors for a non-`x-` unknown key, a nested `x-` key, the older
  `schemaVersion`, an older release URL, malformed keys, JSON-LD and microdata with an `x-` key;
  regenerate; every existing vector unchanged
- [X] T012 `scripts/check_conformance.py` and `tests/test_conformance.py`, vector counts
- [X] T013 Conformance CI: pin the toolkit commit with the v0.5.0 schemas (research R-05)

## Phase 5: Toolkit (FAIR-bioHeaders-Tools)

- [ ] T014 Bundle `fhr-2.1.json`, `fhp-1.1.json`, `fhgff3-1.1.json` and the current copies;
  `bundled.json` `current.release` `v0.5.0` and the v0.5.0 entry; examples copied from the
  specification
- [ ] T015 JSON-LD, export and microdata writers leave extension fields out with a warning;
  JSON-LD (canonical and general) and microdata readers reject them; FHP likewise
- [ ] T016 Readable message for `x-` keys under the older minor
- [ ] T017 Tests: validation by version and URL, key edge cases, R11/R12/R13 in keys and values,
  combine/strip/verify/convert round trips, JSON-LD/microdata/export output, readers
- [ ] T018 README, CHANGELOG, plugin skill, version 0.9.0 prepared (not released)

## Phase 6: FHT (FHT-Specification)

- [ ] T019 Generator post-processing and regenerated `fht.json`; tests; README and migration notes

## Phase 7: Gates and review

- [ ] T020 All gates in plan.md; code review and adversarial review; fixes in new commits
- [ ] T021 CHANGELOGs; status comments on #197 and the PRs
