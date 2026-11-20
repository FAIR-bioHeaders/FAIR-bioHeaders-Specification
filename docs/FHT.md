# Published FHT 1.0

FHT 1.0 was published in specification v0.7.0 at immutable tag
`623c79fe58edeb238a20fb6de518c62dd69b92bc`, GitHub Release 452203176,
DOI [10.5281/zenodo.24385024](https://doi.org/10.5281/zenodo.24385024).
The root `fht.json` and registered FHT 1.0 contract are distinct from the
preserved owning-draft snapshot. Joint package acceptance is recorded in
[#211 comment 7025645941](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7025645941).
Installed-runtime support and the fixed alias pending external w3id PR 7241
must be verified independently; publication does not upgrade existing readers.

## Historical candidate evidence

The following describes the preserved candidate handoff and its measured
runtime limitations at that time. It does not override the published status above.

David Molik's [adopted D1–D3 decisions](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7017854934)
are implemented in the owning snapshot: retain existing optional-value behavior;
reject duplicate parents and noncanonical parent checksums; compare complete
integer BUSCO category sums to total without defaulting absent counts; defer a
new self-parent rule because of its cryptographic fixed-point limitation. Four
parent expectations are accepted for exact file identity only. Neither a match
nor synthetic test acceptance proves biological derivation.

The candidate preserves 93 vectors (34 valid, 59 invalid), seven canonical HTML
pairs, the reference reader/writer and 116 owning tests. Its workflow checks
immutable-source parity and executes those tests with the required owning git
history. Installed toolkit 0.11.0 with an explicit checkout-schema overlay can
compare 91 cases; the two newly invalid arithmetic cases are **NOT-RUN for
consumer enforcement**, following actual old-runtime acceptance probes. This is
not a 93-case consumer pass, a package refresh or default FHT support.

## Concrete staged v0.7.0 handoff

1. David and Adam record final joint acceptance of this exact owning head and
   candidate scope, including the transcriptome contract and typed binding.
   Existing questionnaire answers and D1–D3 are settled; no new dataset program
   or repeated field questionnaire is required.
2. Prepare and verify arithmetic-capable toolkit support against the approved
   contract before publication. Current reference acceptance is executable;
   consumer support needs its own reviewed implementation and installed receipt.
   Default runtime promotion and supported-release pin updates follow actual
   publication and cannot be circular prerequisites requiring that publication
   already to exist.
3. In the eventual publishing PR, generate the approved contract for the selected
   **shared v0.7.0** release, with contract `schemaVersion` **1.0**. Replace the
   owning draft-only selector deliberately with reviewed released forms under
   V1–V7. Update release-form tests without rewriting historical fixture IDs or
   byte-bound examples. Preserve the distinction between owning raw-tag V5 and
   registered shared V2/V3/V4 cases. No future alias is minted by this candidate.
4. Stage the final shared model/contract, registry row, vocabulary/binding and
   cross-type conformance integration in that publication review. Keep INSDC FHT
   rows draft until actual release; assessment #157 is already completed. The
   current 93 owning vectors remain distinct from the released shared suite
   until deliberate absorption. JSON-LD remains unsupported unless separately
   implemented and tested; do not claim serialization parity by analogy.
5. Complete release notes, accurate citation metadata, license/provenance review
   and fixed-artifact alias preparation. Maintainers then perform the agreed
   release process, including a GitHub Release object, and verify actual archive
   identifiers/redirects. A tag alone is insufficient. Do not guess DOI values.
6. After publication, verify actual contract/registry artifacts and coordinate
   toolkit supported/default behavior, consumer pin refreshes and website/Nextflow
   handoffs through their owners. Website export remains disabled until the
   binding and real reader/writer round trips are ready. A future downstream
   rollout is not another Project 9 foundation requirement.

The separate real-data pilot, its creation-date/software attribution and any
full-producer adoption evidence are outside #10's release boundary. Copied pilot
and legacy files are dependency/provenance inputs, not newly accepted public
release examples. No third-party metadata, sequence or historical permission is
rewritten here.

Tracks [FHT #5](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/5),
[#8](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8),
[#9](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/9),
[#10](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/10),
[#11](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/11), shared
[#55](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/55)
and [#107](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/107).
These remain open for their actual final gates. Source-PR merge approval and final
joint adoption/publication authority remain distinct.

The actual released-layout proposal is now prepared in [FHT-PUBLICATION-CANDIDATE.md](FHT-PUBLICATION-CANDIDATE.md), including generated root artifacts, registry selection, vocabulary/binding and a separately executed conformance crosswalk. It remains an unpublished draft review, with the gates above unchanged.
