# FHT 1.0 publication in v0.7.0

This is the final tag package and operational record. Source, a private preview
or a tag alone does not establish publication: verify the actual GitHub Release,
archive and redirects. Joint package acceptance is attributed in
[#211](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7025645941).
The preceding release is v0.6.1, archive
[10.5281/zenodo.24384147](https://doi.org/10.5281/zenodo.24384147).

## Exact artifacts

- FHT contract `1.0`: root `fht.json`, SHA-256
  `082b0790b7878940c4496c97d7485e32c65de8ba75ecc080e53f04fb44251a43`.
  Logical identity: `https://w3id.org/fair-bioheaders/fht/v0.7.0`.
  Immutable retrieval after the actual tag exists is
  `https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/v0.7.0/fht.json`.
  The external redirect remains a separate verification step; do not claim it is
  live merely because the identifier appears in the schema.
- FHR `2.1`, FHP `1.2` and FHGFF3 `1.2` retain their exact v0.6.0 bytes.
  The existing 291 payloads and historical ledgers are unchanged. FHT has 93
  separately named counterparts, preserving every immutable owning input, plus
  seven synthetic JSON/FASTA/typed-HTML example triples.
- FHT has the accepted construction and molecule vocabularies, nine required
  roots, named metadata authors and completeness arithmetic. Typed HTML has a
  separate metadata binding and exact-tag guard; no FHT JSON-LD serializer or
  context is introduced. Model validation is not file/parent/biological proof.
- Assessment v6 records FHT publication and its exact digest. All INSDC
  requirement IDs, coverage outcomes and dispositions are preserved; no deposit
  readiness or external endorsement is inferred.
- This release does not publish native FHGM 0.1. Its staged artifact remains
  labelled unpublished for the separate v0.8.0 release; no FHGM header row exists.

## Final checks and publication

1. Independently review the exact final metadata commit; verify changed source,
   prerequisites and all overall/inline findings. The final commit clears
   `preRelease`, finalizes citation version/date and registers the unchanged FHR
   context for this actual tag. Never invent a version DOI.
2. Before creating the public tag, test the exact commit in a private Git clone
   with a private tag at that same commit. Record this only as a preflight, not
   a published tag or installed-release receipt. Run identity, context, CEDAR,
   generation, 93-case and seven-example checks and the full suite there.
3. Push the reviewed branch and new tag, verify the remote tag/commit and await
   all applicable exact-head CI. Merge through the protected PR path; preserve
   the exact tag bytes. A failing check is not a publication pass.
4. Create and verify the actual GitHub Release. Read the archive service's
   actual version record, download its bytes and compare them with the tag;
   record the minted DOI rather than guessing it.
5. The external alias PR remains under upstream owners' merge authority. After
   its real targets exist, request readiness and verify the initial redirect,
   final bytes and nonexistent-version controls. Record an unresolved redirect
   as an external gate, not a live identifier claim.
6. Deliberately refresh actual package bundles, installed receipts, authoring,
   website and Nextflow handoffs after the relevant releases. Existing toolkit
   0.12.0 and language draft pins do not acquire FHT default support from a
   specification release. Keep the historical V7 lane distinct.

Authoring remains pinned to v0.6.0 pending an actually published supporting
reader. Source/candidate runtime receipts and website previews remain labelled
as such. The public pilot and excluded downstream projects are not release gates.
