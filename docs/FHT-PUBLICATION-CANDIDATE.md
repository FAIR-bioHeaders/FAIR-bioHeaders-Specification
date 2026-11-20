# FHT v0.7.0 publication preparation

**Accepted, unpublished preparation artifact. Publication remains separately gated.**
This preparation records the shared publication layout for FHT contract
`1.0`, using accepted owning `4ddda69cbcbb3920a06ab657173c0198672cd7bf`.
David accepted this package and recorded Adam’s concurrence on his behalf in [the joint acceptance record](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7025645941). This attributed record is not a native GitHub approval by Adam. No tag,
release object, alias, DOI, website enablement or consumer repin is created.

## Artifacts and compatibility

- Root `fht_linkml.yml` imports the unchanged shared core and shared objects;
  `json-schema-generator.py --type fht --output fht.json` applies the accepted
  FHT-specific generation rules. Only the selector constraint and annotations
  differ from the accepted owning schema; tests compare all other resolved
  constraints. Selected contract identity:
  `https://w3id.org/fair-bioheaders/fht/v0.7.0` (not live).
- `schemas/versions.json` marks **current = preRelease = v0.7.0**, adding FHT
  `1.0` beside byte-identical FHR `2.1`, FHP/FHGFF3 `1.2`. Existing release rows
  remain unchanged. The candidate metadata records joint acceptance and the still-unpublished
  FHT state; no FHT alias has been activated. The preceding guidance release
  [v0.6.1](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/releases/tag/v0.6.1)
  is published at `1812c3bf132fe47f4c30aa8bebd59baeb580988a`, with actual archive DOI
  [10.5281/zenodo.24384147](https://doi.org/10.5281/zenodo.24384147), and its
  source is reconciled here. `authoringRelease` remains v0.6.0, so existing
  CEDAR forms and examples retain citations supported by published readers.
  This does not prevent the separate final FHT publication.
- V1/V2/V3 recognize shared raw-main, shared raw-tag and versioned w3id forms;
  V4 rejects an unregistered FHT release, V5 still routes owning raw tags and
  other unknown citations to FHR, V6 retains numeric FHR-1 handling. The frozen
  owning raw-main V7 opt-in stays a distinct historical draft lane. No fallback
  from an unknown release to the draft or current FHT contract is permitted.
- Vocabulary generation adds reachable FHT term definitions to the common
  namespace, preserving existing term definitions and the FHR JSON-LD context.
  There is **no FHT JSON-LD serializer/context or DCMI projection claim**.
- [FHT-MICRODATA.md](FHT-MICRODATA.md) integrates the complete F1–F7 binding, selector/API overrides and generated 29-field table.
- `scripts/fht_microdata.py` is an attributed adaptation of the accepted typed
  HTML reference. It has a separate registry-selection path, explicit candidate
  opt-in, complete contract/C1 arithmetic checks, integer/type/order preservation,
  visibility and mixed-family checks. It does not verify absent sequence bytes.
  Post-tag execution requires the actual byte-matching v0.7.0 tag; clearing the
  marker without that tag cannot silently enable the binding. Candidate mode
  reports unpublished status; the verified-tag reference mode instead reports
  exact tag-byte verification without claiming a GitHub Release or publication.
  Later family releases retaining registered FHT 1.0 still require those exact
  v0.7.0 bytes; a new `current` value cannot silently disable or replace them.
- Seven synthetic JSON/FASTA/HTML counterparts live in `examples/fht/`.
  Their selectors and root checksums are generated deliberately; original seven
  pairs and source bytes remain unchanged. Parent claims retain their original
  scope and do not become proof of biological derivation. Their visible title
  and paragraph identify synthetic reference material without asserting a
  publication state; the generated HTML is byte-stable across the candidate
  and verified-tag states. API diagnostics retain their actual state.

## Conformance absorption and receipts

`conformance/fht-v0.7.0/manifest.json` maps every one of the 93 immutable owning
cases to a new `fht-v070-*` ID, source payload digest and explicit transformation.
Original IDs, bytes and historical outcomes remain in `drafts/fht/upstream/`.
The 291 v0.6.0 carrier fixtures remain byte-identical; the current 319-case
carrier lane stays independently reproducible. This separate FHT lane is executed
in CI rather than being counted as installed consumer support. Its receipt
reports source conformance and `publicationVerified: false`: the checker does
not query the GitHub Release or archive, so it does not assert whether either
has been published.

Shared selectors and root checksum lines are changed only in the new counterpart
bytes. Deliberate checksum defects remain defects; malformed compressed streams
retain their original bytes and reject before selector evaluation. Parent context
binds the parsed child's digest, type, relationship and count to its immutable
source claims and supplied parent bytes. Historical parent contexts are preserved
as exact file-identity evidence, not advertised as newly released examples.

Primary rejection is tested, not merely invalid counts. The accepted rule-specific
keyword/path/reason assertions are retained; the three old selector `const`
assertions become explicit selector-pattern assertions. The two older shared-tag/
w3id cases remain invalid but move from historical V5 routing to measured V4
unsupported-version. Wrong-checksum masking of a C1 arithmetic rejection and a
changed child parent digest with a recomputed root checksum are detected controls.

```sh
python scripts/fht_publication.py --write --examples
python scripts/fht_publication.py --examples > fht-publication-receipt.json
python -m unittest discover -s tests -p test_fht_publication.py -v
python scripts/check_linkml.py
python scripts/check_release.py --identity-only
```

Use Python 3.13+ for the typed HTML reference's RCDATA requirement and the pinned
`requirements-linkml.txt`/`requirements-jsonld.txt` dependencies. Regeneration
changes only the new counterparts; `drafts/fht/check_source.py --upstream ...`
independently verifies all 239 immutable owning paths.

## Final gates and publication order

1. Joint package acceptance is recorded above. Preserve the settled field decisions.
   Independent model review remains technical review only.
2. The merged toolkit implementation at adb0f5e and owning harness at ac53af9 now
   have an installed development-candidate receipt for all 93 owning cases, with
   zero unsupported/staged cases. These development wheels are not the published
   0.12.0 package. Shared-selector/default support is prepared separately in Tools
   #200 and remains unpublished. Preserve older 91-case receipts with their two
   named arithmetic NOT-RUN gaps as historical evidence.
3. The real preceding v0.6.1 source is reconciled here. Recheck the current base
   and applicable checks. Verify the future FHT release and aliases against actual
   immutable bytes before recommending their URLs as live.
4. Review final release metadata: change CFF preparation version to actual 0.7.0,
   record the real release date, add the v0.7.0 context alias inventory alongside
   the actual tag, and add only identifiers actually minted. Preserve
   stable BibTeX keys, the concept DOI and historical version DOIs/license terms.
5. Obtain separate merge/Pages and release/alias authority. Clear `preRelease` only
   in the commit actually tagged; create and verify the tag **and GitHub Release
   object**, archive/DOI and fixed aliases. The preparation files do not themselves
   establish any of these publication events.
6. Record immutable release evidence, then perform deliberate consumer/default,
   CEDAR, website and Nextflow handoffs through their owners. Keep FHT separate
   from the later FHGM v0.8.0 stage. Public pilot/Project 12/13 work is excluded.

INSDC FHT rows remain explicitly draft; the already completed #157 assessment is
re-pinned to the accepted semantics without changing coverage/dispositions or
claiming deposit readiness. Government dataset bytes and historical permissions
are unchanged. New reference adaptations follow the existing MPL-2.0 notices.

Refs FHT-Specification #10/#8/#11, shared #55/#107/#211. These remain open at
actual release, package acceptance and consumer gates; this candidate closes none.
