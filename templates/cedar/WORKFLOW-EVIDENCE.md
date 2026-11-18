# Five-template workflow evidence and publication handoff

This is reproducible **offline workflow evidence**, not a live CEDAR publication
or curator acceptance. It completes the existing authoring workflow under #162;
it does not create templates for missing types, change fields, re-pin snapshots
or publish FHT/FHGM contracts. All five templates already existed.

## Inputs and authority

| Surface | Existing source | Status |
| --- | --- | --- |
| FHR / FHP / FHGFF3 | Root released contracts, registry v0.6.0; versions 2.1 / 1.2 / 1.2 | Published contracts, unchanged |
| FHT form | `drafts/fht.schema.json`, owner commit `226f923c28b680edb3c546e99a751482d06aef1a`, SHA-256 `59ad9641adcb0e5591045c2d894c066d1adc9984cca84c5ff6502f8dad88487e` | Existing pinned draft, unchanged |
| FHGM form | `drafts/fhgm-model.schema.json`, owner commit `ac3d37b3033312844fc3151217731928ae33aa54`, SHA-256 `bf1553cac04dc88d8afaff1d39bc50360342e1ebedac4b73dfe3dff570ff410f` | Existing pinned model draft, unchanged |
| Writer | Fresh PyPI `fair-bioheaders` at the release pinned in [`conformance/toolkit-pin.json`](../../conformance/toolkit-pin.json) (0.12.0 since 2026-11-18; first recorded with 0.11.0), Python 3.13 | Installed noneditable artifact, invoked outside checkout |
| Writer's FHT contract | 0.12.0 bundles owner revision `226f923c28b680edb3c546e99a751482d06aef1a`, SHA-256 `59ad9641adcb0e5591045c2d894c066d1adc9984cca84c5ff6502f8dad88487e`, byte-identical to the form's snapshot. 0.11.0 bundled revision `b9ad19a62772092e08935cff44ee77a50981bbaf` (bytes unchanged since `2d582f1`), SHA-256 `11c69d6647736695beaa72976a1d9b30c0f44f8cfe55f8eb171c9d0bcb6795f8` | Pinned digest checked against the installed artifact; never silently substituted |
| FHGM checker | [Owning revision f0b3aee06cc2eafd1bf417bfb1c12105c9b595b3](https://github.com/FAIR-bioHeaders/FHGM-Specification/tree/f0b3aee06cc2eafd1bf417bfb1c12105c9b595b3/development/model), recorded for CI in [`drafts/provenance.json`](drafts/provenance.json) (`snapshots.fhgm.ownerChecker`); its `fhgm-model.schema.json` is byte-identical to the snapshot (verified 2026-11-18) | Existing checker behavior; merged layer proposal is not newly adopted semantics |
| FHGM base candidates | Its existing `base-schemas.json`: v0.5.0 FHGFF3 1.1 SHA-256 `20ce320f5d706f11ed21cdece4dfb56e3568b50be126e25b4016f46f2e8e416c`; v0.6.0 FHGFF3 1.2 SHA-256 `1942be4cefc8b3a2537942c2252b45fbcef87a5532486e4fd0f5d4c540e0fbf9` | Root release bytes checked by digest; declared carrier selects base |

Full original draft provenance remains in [`drafts/provenance.json`](drafts/provenance.json).
The owning FHGM record schema still matches that snapshot byte for byte. New
warnings correct obsolete workflow claims; no pinned schema descriptions are
edited to force that match.

## Checks and limits

| Check | Evidence / expected outcome |
| --- | --- |
| Generate all five templates twice | Existing `test_cedar.py` byte-stability, field coverage, requiredness, identity, digest and draft-marking tests; `make_cedar.py --check` also fails on a top-level `*.json` the generator does not produce |
| Value constraints | Every leaf field of all five templates: enum → literals, closed pattern → literals, pattern → regex, minimum/maximum → minValue/maxValue, integer → `xsd:long`, number → `xsd:double`, date → `xsd:date`, single literal → defaultValue, requiredness; unpatterned `format: uri` → CEDAR link field (`CedarValueConstraintTests`) |
| Snapshot tamper control | A one-byte change to a temporary copy of the FHGM snapshot refuses to generate; the tracked snapshot is never written |
| Flatten filled exports for all five types | Complete supplied values survive; optional blanks/root checksum are omitted deliberately; nested parent checksums survive |
| Flatten exports with blank elements and lists | Every optional element or multiple-value field left blank, at any depth, is omitted (`CedarBlankExportTests`); required ones stay for the validator |
| Malformed exports | An object or list `@value`, an unparsable or non-finite numeric value and a non-string link `@id` raise `ValueError` naming the field path; `--flatten` prints it and exits 1 without a traceback (`CedarFlattenInputErrorTests`) |
| CEDAR meta-schemas | All five templates pass the template, element and field meta-schemas vendored from cedar-model-validation-library `34e65d2` (`tests/test_cedar_meta_schema.py`) |
| Installed released FHR/FHP/FHGFF3 path | Export → flatten → combine → validate → verify → JSON readback → strip; recursively equal scalar types/values and list order; exact original sequence/feature payload; repeated bound bytes |
| Installed FHT default-off control | Same valid draft input refused without opt-in; no bound output created |
| Installed FHT V7 path | Common `diptera_odb10` fixture binds/validates/verifies with `BIOHEADERS_EXPERIMENTAL_FHT=1`; typed readback and exact payload preserved, draft warning present |
| FHT pin control | The installed bundle's FHT digest must equal the pinned one. `diptera_odb10.1` validates against the CEDAR snapshot; the installed toolkit must accept it when its bundled draft is that snapshot (0.12.0) and reject it otherwise (0.11.0), so a writer-coverage gap stays visible rather than being reported as a pass |
| FHGM standalone record | Flattened model validates against pinned model contract; no file schema/version/checksum is invented |
| FHGM carriers | Same record preserved under `x-fhgm-models` in valid released 1.1 and 1.2 FHGFF3 carriers; checksum recomputed by toolkit |
| Owning FHGM checks | Both registered base candidates supplied; owner resolves declared base, checks target/reference and reports no predecessor claim for the minimal fixture |
| Base-versus-model negative control | A wrong feature target still passes toolkit base/checksum checks but fails the owning model checker; carrier success is not model conformance |
| Missing integration inputs | Missing `CEDAR_TOOLKIT` explicitly skips installed tests; missing `CEDAR_FHGM_ROOT` explicitly skips owning model checks, without claiming model conformance. The shared CI sets both, so neither is skipped there |

Run the commands in the [usage guide](README.md#reproducible-workflow-checks).
The shared CI's existing released-toolkit environment executes the installed
checks, and the conformance job checks out FHGM-Specification at the checker
revision recorded in `drafts/provenance.json` and sets `CEDAR_FHGM_ROOT`, so the
owning model check runs there instead of being skipped. Locally the lane is
reproducible with the same revision and fetched release tags. The checker
revision is a fixed commit, not moving `main`.

The records and tiny payloads are synthetic test data, not a dataset/pilot
program. These tests perform no full GFF3 feature/biology validation, reference
sequence comparison, evidence assessment, curator acceptance, live CEDAR import,
terminology-server validation or real workbench-export exercise. A generated
CEDAR artifact wrapper is not evidence that a template has been uploaded.

## Remaining publication gate — #162 remains open

Implementation and offline evidence do not answer the live-publication task.
Maintainers must:

1. Select the CEDAR instance/account and responsible owner with upload access.
2. Review form wording and visible draft/unsupported-value notices for that
   instance; keep released and draft templates distinguishable.
3. Import the five artifacts, let the workbench assign actual artifact/property
   URIs, and record the authoritative links, owner, import date and source
   versions/digests. Generated null IDs and synthetic field URIs are not
   published CEDAR identifiers.
4. Export real filled workbench instances and run the documented flatten/bind
   checks, retaining the FHT pin limitation and separate FHGM model-check path.
   Publish the real template links in usage guidance and reconcile acceptance.

No upload, account change, URI assignment or external publication was performed
by this packet. No new schema, release, profile version or maintainer decision
is requested to finish the offline workflow.
