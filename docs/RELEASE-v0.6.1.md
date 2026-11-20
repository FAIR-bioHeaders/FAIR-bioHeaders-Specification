# v0.6.1 guidance release candidate

This is preparation, not a published release. The preceding published release
is v0.6.0. Round 15 authorizes the staged publication sequence conditionally;
current-head independent different-model review, applicable CI and final
validation remain required. David and Adam jointly hold release authority.

## Content and compatibility

The v0.6.1 registry row repeats v0.6.0 exactly: FHR 2.1, FHP 1.2, FHGFF3 1.2.
All three root JSON contracts remain byte-identical to v0.6.0. No FHT/FHGM
contract is published by this patch. Staged owning draft packages retain their
explicit draft identities and immutable history.

The patch carries adopted R16 producer-methodology guidance without retroactively
reinterpreting old values; V1–V4 selection and R4 root/nested canonical checksum
clarifications; and the newly selected R1/R12 gzip/directive policies. The latter
close previously unspecified cases and are not claimed as historical-release
outcomes. The reader-policy corpus records actual runtime gaps separately.

`authoringRelease` stays v0.6.0. Generated CEDAR forms, existing file-bound
examples and usage URLs therefore remain usable with the published pinned
reader. A registry entry alone does not give installed readers v0.6.1 support.
Deliberate consumer promotion follows real release bytes and installed receipts;
never rewrite historical fixtures merely to cite a newer documentation patch.

## Final operational gates

1. Review the exact candidate, complete applicable CI, independently validate
   current changes, and record the actual joint release disposition. Read all
   overall and inline findings, respond and resolve handled threads.
2. Finalize citation version/date for the actual release. Keep the concept DOI
   and historical version DOIs labelled correctly; do not invent a version DOI.
3. Clear `preRelease` only in the commit that will be tagged. Land the reviewed
   final commit and tag together so main-push identity checks can see the tag.
   Verify the landed commit by content after any squash merge. Preserve platform
   protections; a reviewed candidate does not authorize a bypass.
4. Verify exact tag contracts, registry and historical fixture bytes; create the
   actual GitHub Release. A tag alone is not publication. Record its URL and
   verify the real archive/version DOI after the archive service creates it.
5. Verify authorized aliases by their initial redirect and final exact bytes,
   with a nonexistent-version control. External alias changes retain upstream
   owners' merge authority. Record unavailable artifacts instead of inventing
   support.
6. Refresh actual installed consumers deliberately, then advance authoring
   citations only with supported-command and fixed-selection evidence. Rebase
   FHT #281 onto the actual preceding release and revalidate its current head
   before its distinct joint acceptance/readiness/publication gates.

No release, archive, alias or installed-reader claim follows from this document.
