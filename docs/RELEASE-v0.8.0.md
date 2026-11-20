# v0.8.0 native FHGM model contract 0.1

## Scope and immutable authorities

This release selects native FHGM model contract 0.1 at
`model-contracts/fhgm/0.1/fhgm-model.schema.json`, identity
`https://w3id.org/fair-bioheaders/model-contracts/fhgm/0.1`, SHA-256
`56c0a5a91e9e56c50c0919a375505c01f52bce5f1792841c40b87b1cd18e9336`.
It adds no FHGM header registry row or in-record `schema`/`schemaVersion`.
The accepted owning source is d9d131a02b042023f4784d842a874232fc891069;
all 134 owning files and 92 vector bytes remain unchanged. Selection is external
to the native record. Native/source parity permits only the specifically reviewed
resource identity and two root annotations; no validation constraint changes.

The four header registry entries repeat v0.7.0 exactly: FHR2.1, FHP1.2,
FHGFF3 1.2, FHT1.0. All four header schema bytes,239 preserved FHT owning files,
93 counterparts,seven example triples and291 historical v0.6.0 payloads remain
unchanged. JSON-LD remains FHR-only; no FHT DCMI/JSON-LD adoption occurs.

Preceding actual publications: v0.6.1 tag1812c3bf132fe47f4c30aa8bebd59baeb580988a,
DOI10.5281/zenodo.24384147; FHT v0.7.0 tag623c79fe58edeb238a20fb6de518c62dd69b92bc,
DOI10.5281/zenodo.24385024. The v0.7.0 Zenodo ZIP measured3,588,008 bytes,
SHA-256 a65d9693361fd4348f6bc0ba69dd7a8ce1c7a8e24e7658625e6b7bc2f55141a7,
with1744 regular files matching the tag. Joint native package acceptance is
recorded in #211 comment7025645941, attributed to David speaking for Adam.

## Final checks and publication

1. Independently review the exact metadata commit, constraints and protected
   source bytes. Read every overall/inline finding and verify current CI. The
   final commit clears preRelease, selects native publicationState released,
   finalizes citation version/date and includes the unchanged FHR context URL.
2. Before any public tag, clone the exact committed source privately and create
   only a private v0.8.0 tag at that same commit. Run native identity controls,
   dual-base92-case suite and eight receipt guards, FHT93-case/seven-example
   regressions, context/CEDAR/generation checks and the broad shared suite.
   The private tag is a preflight, never actual publication evidence.
3. Root creates the new public exact-head tag only after that preflight and
   independent approval. Verify remote tag identity, all exact-head CI and the
   protected PR merge. Never move existing tags or infer success from missing CI.
4. Root creates the actual GitHub Release, reads the actual archive-service
   record, downloads and measures its bytes and compares every regular file to
   the tag. Record only the service-minted DOI and measured archive hashes.
5. External w3id PR7241 is governed by upstream owners. Mark its targets ready
   only after both real releases exist; verify actual redirects, final bytes and
   absent-version controls after upstream merge. No source assertion is a live
   alias claim.
6. Deliberately promote bundles/default selectors only from actual published
   artifacts, then verify installed-toolkit, website and external Nextflow
   handoffs. Authoring remains v0.6.0 until an actual supporting toolkit exists.
   Existing language pins and historical V7 draft remain separate.

The native dual-base receipt measures184 visits,174 complete-vector matches,
48 complete-model passes,728 evaluated predicates,736 layer comparisons and
10 expected NOT_RUN visits excluded from complete/full-pass counts. Source
receipts report publicationVerified:false even after exact-tag validation:
metadata conformance, file integrity, feature/biology checks and curator
acceptance are separate outcomes. Project12 pilots and excluded downstream work
add no Project9 publication gate. No v0.8.0 version DOI is guessed here.
