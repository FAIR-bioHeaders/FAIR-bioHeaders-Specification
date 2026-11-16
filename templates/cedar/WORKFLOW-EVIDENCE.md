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
| Writer | Fresh PyPI `fair-bioheaders==0.11.0`, Python 3.13 | Installed noneditable artifact, invoked outside checkout |
| Writer's FHT contract | Bundled SHA-256 `11c69d6647736695beaa72976a1d9b30c0f44f8cfe55f8eb171c9d0bcb6795f8` | Older draft than the form; not silently substituted |
| FHGM checker | [Owning revision f0b3aee06cc2eafd1bf417bfb1c12105c9b595b3](https://github.com/FAIR-bioHeaders/FHGM-Specification/tree/f0b3aee06cc2eafd1bf417bfb1c12105c9b595b3/development/model) | Existing checker behavior; merged layer proposal is not newly adopted semantics |
| FHGM base candidates | Its existing `base-schemas.json`: v0.5.0 FHGFF3 1.1 SHA-256 `20ce320f5d706f11ed21cdece4dfb56e3568b50be126e25b4016f46f2e8e416c`; v0.6.0 FHGFF3 1.2 SHA-256 `1942be4cefc8b3a2537942c2252b45fbcef87a5532486e4fd0f5d4c540e0fbf9` | Root release bytes checked by digest; declared carrier selects base |

Full original draft provenance remains in [`drafts/provenance.json`](drafts/provenance.json).
The owning FHGM record schema still matches that snapshot byte for byte. New
warnings correct obsolete workflow claims; no pinned schema descriptions are
edited to force that match.

## Checks and limits

| Check | Evidence / expected outcome |
| --- | --- |
| Generate all five templates twice | Existing `test_cedar.py` byte-stability, field coverage, requiredness, identity, digest and draft-marking tests |
| Flatten filled exports for all five types | Complete supplied values survive; optional blanks/root checksum are omitted deliberately; nested parent checksums survive |
| Installed released FHR/FHP/FHGFF3 path | Export → flatten → combine → validate → verify → JSON readback → strip; recursively equal scalar types/values and list order; exact original sequence/feature payload; repeated bound bytes |
| Installed FHT default-off control | Same valid draft input refused without opt-in; no bound output created |
| Installed FHT V7 path | Common `diptera_odb10` fixture binds/validates/verifies with `BIOHEADERS_EXPERIMENTAL_FHT=1`; typed readback and exact payload preserved, draft warning present |
| FHT pin-difference control | `diptera_odb10.1` validates against the unchanged CEDAR snapshot but fails installed 0.11.0 draft validation; unsupported writer coverage is visible, not reported as a pass or “not yet bindable” |
| FHGM standalone record | Flattened model validates against pinned model contract; no file schema/version/checksum is invented |
| FHGM carriers | Same record preserved under `x-fhgm-models` in valid released 1.1 and 1.2 FHGFF3 carriers; checksum recomputed by toolkit |
| Owning FHGM checks | Both registered base candidates supplied; owner resolves declared base, checks target/reference and reports no predecessor claim for the minimal fixture |
| Base-versus-model negative control | A wrong feature target still passes toolkit base/checksum checks but fails the owning model checker; carrier success is not model conformance |
| Missing integration inputs | Missing `CEDAR_TOOLKIT` explicitly skips installed tests; missing `CEDAR_FHGM_ROOT` explicitly skips owning model checks, without claiming model conformance |

Run the commands in the [usage guide](README.md#reproducible-workflow-checks).
The shared CI's existing released-toolkit environment executes the installed
checks. The owning FHGM lane is independently reproducible with the revision
above and local released tags; CI without that owning checkout reports the
model-check test skipped. No new pin or moving-main dependency is introduced.

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
