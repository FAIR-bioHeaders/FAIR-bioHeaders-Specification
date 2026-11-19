# FHT v0.7.0 publication preparation

**Draft review artifact. Do not merge or publish under ordinary code approval.**
This branch proposes the actual shared publication layout for FHT contract
`1.0`, using accepted owning `4ddda69cbcbb3920a06ab657173c0198672cd7bf`.
Final joint David/Adam acceptance of this exact package remains pending. No tag,
release object, alias, DOI, website enablement or consumer repin is created.

## Proposed artifacts and compatibility

- Root `fht_linkml.yml` imports the unchanged shared core and shared objects;
  `json-schema-generator.py --type fht --output fht.json` applies the accepted
  FHT-specific generation rules. Only the selector constraint and annotations
  differ from the accepted owning schema; tests compare all other resolved
  constraints. Proposed stable identity:
  `https://w3id.org/fair-bioheaders/fht/v0.7.0` (not live).
- `schemas/versions.json` marks **current = preRelease = v0.7.0**, adding FHT
  `1.0` beside byte-identical FHR `2.1`, FHP/FHGFF3 `1.2`. Existing release rows
  remain unchanged. The candidate metadata explicitly records no joint acceptance
  or aliases. The planned guidance-only v0.6.1 stage remains separate: rebase
  this candidate on its actual accepted release before the final release review;
  do not fabricate that release or pre-register nonexistent historical aliases.
- V1/V2/V3 recognize shared raw-main, shared raw-tag and versioned w3id forms;
  V4 rejects an unregistered FHT release, V5 still routes owning raw tags and
  other unknown citations to FHR, V6 retains numeric FHR-1 handling. The frozen
  owning raw-main V7 opt-in stays a distinct historical draft lane. No fallback
  from an unknown release to the draft or current FHT contract is permitted.
- Vocabulary generation adds reachable FHT term definitions to the common
  namespace, preserving existing term definitions and the FHR JSON-LD context.
  There is **no FHT JSON-LD serializer/context or DCMI projection claim**.
- `scripts/fht_microdata.py` is an attributed adaptation of the accepted typed
  HTML reference. It has a separate registry-selection path, explicit candidate
  opt-in, complete contract/C1 arithmetic checks, integer/type/order preservation,
  visibility and mixed-family checks. It does not verify absent sequence bytes.
  Post-tag execution requires the actual byte-matching v0.7.0 tag; clearing the
  marker without that tag cannot silently enable the binding. Candidate mode
  reports unpublished status; the verified-tag reference mode instead reports
  exact tag-byte verification without claiming a GitHub Release or publication.
- Seven synthetic JSON/FASTA/HTML counterparts live in `examples/fht/`.
  Their selectors and root checksums are generated deliberately; original seven
  pairs and source bytes remain unchanged. Parent claims retain their original
  scope and do not become proof of biological derivation.

## Conformance absorption and receipts

`conformance/fht-v0.7.0/manifest.json` maps every one of the 93 immutable owning
cases to a new `fht-v070-*` ID, source payload digest and explicit transformation.
Original IDs, bytes and historical outcomes remain in `drafts/fht/upstream/`.
The 291 v0.6.0 carrier fixtures remain byte-identical; the current 319-case
carrier lane stays independently reproducible. This separate FHT lane is executed
in CI rather than being counted as installed consumer support.

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

1. Joint David/Adam acceptance of this exact contract, binding, examples and
   selection package; preserve the settled field decisions rather than repeating
   the questionnaire. Independent model review remains technical review only.
2. B supplies reviewed arithmetic-capable current-contract implementation and
   actual installed receipts. Existing old-runtime receipts prove only 91 cases
   with **two named arithmetic NOT-RUN** gaps, never full 93-case support.
3. Reconcile the real preceding v0.6.1 guidance stage, current base and all current
   checks. Verify releases/aliases against actual immutable bytes; do not turn the
   proposed URLs in this branch into live usage recommendations prematurely.
4. Review final release metadata: change CFF preparation version to actual 0.7.0,
   record the real release date, and add only identifiers actually minted. Preserve
   stable BibTeX keys, the concept DOI and historical version DOIs/license terms.
5. Obtain separate merge/Pages and release/alias authority. Clear `preRelease` only
   in the commit actually tagged; create and verify the tag **and GitHub Release
   object**, archive/DOI and fixed aliases. No step is authorized by this draft.
6. Record immutable release evidence, then perform deliberate consumer/default,
   CEDAR, website and Nextflow handoffs through their owners. Keep FHT separate
   from the later FHGM v0.8.0 stage. Public pilot/Project 12/13 work is excluded.

INSDC FHT rows remain explicitly draft; the already completed #157 assessment is
re-pinned to the accepted semantics without changing coverage/dispositions or
claiming deposit readiness. Government dataset bytes and historical permissions
are unchanged. New reference adaptations follow the existing MPL-2.0 notices.

Refs FHT-Specification #10/#8/#11, shared #55/#107/#211. These remain open at
actual release, package acceptance and consumer gates; this candidate closes none.
