# FHT prepublication evidence and decisions

Dated 2026-11-19 (historical measurements retain their dates); refs FHT-Specification #8, #9 and #10, and shared
FAIR-bioHeaders-Specification #211. This packet records the adopted D1–D3 decisions and prepares final joint review.
FHT remains an unreleased draft; default toolkit support is not established.
See the [decision record](FHT-DECISION-DOCKET.md#d1d3-accepted--november-19-2026).

## Acceptance accounting

The seven rows below follow [#8](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8)
and its [per-box evidence](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8#issuecomment-6904199033).
Use [the generated manifest](../conformance/manifest.json) for the current suite
inventory and outcomes. The four reviewed parent-link expectations were accepted by David Molik under
D3 for file identity only; manifest `expectationReviews` records that disposition.

| #8 box | Existing evidence and this packet | Remaining gate |
| --- | --- | --- |
| 1 examples for three construction types | Six minimal/rich stems, JSON/YAML/FASTA; `tests/test_examples.py` and fixture checker validate and recompute checksums | Existing evidence; no new example claim |
| 2 typed serializations | JSON/YAML/embedded FASTA plus seven canonical typed-HTML pairs and a test-only reference reader/writer; the browser job extracts each pair through Chromium | #11 still owns shared binding publication and installed runtime/website handoff; JSON-LD remains unsupported |
| 3 byte-level vectors and streams | Existing U/T, line endings, comments, checksums and compressed vectors; installed lane now exercises actual stdin/stdout | Shared-manifest absorption and any shared vocabulary decision remain publication work; these process checks add no normative vector |
| 4 strip/combine/conversion preservation | Independent payload expectation, metadata values/order/types and recomputed output verification; actual stream payload stdout is compared as bytes | Default-path acceptance belongs to #9 after publication; canonical header regeneration is not whole-file identity |
| 5 parent outcomes | Existing matching, mismatching and unavailable cases, with distinct exit/report checks; independent technical derivations are recorded below | D3 accepts the four expectations for file identity only; final joint review remains |
| 6 version selection and reviewed expectations | Existing V1/V5/V7 cases and documented release-time V4 asymmetry, with recorded independent technical candidate review | D3 disposition recorded; shared absorption/default checks are staged at publication |
| 7 named toolkit and shared checks | `run_toolkit_lane.py` against installed 0.11.0; separate Linux CI job; independent fixture/model/provenance gates retained | Shared FHT format does not exist before publication; installed 0.11.0 bundles an older draft, whose digest is printed, not silently substituted |

The installed lane's case counts and NOT-RUN cases come from the suite and the
installed contract being exercised; they are **implementation comparisons**, not
independently approved acceptance cases. The as-installed 0.11.0 contract is
older than the owning draft. The separate `--checkout-contract --strict --stage-completeness` lane
checks that same installed implementation with this checkout's contract bytes;
this overlay is a test configuration, not a published package refresh. The two
new arithmetic-only invalid vectors are explicitly NOT-RUN by the older installed
runtime, which accepts them under the overlay. All other discrepancies still
fail strict mode. The owning checker and HTML reference enforce arithmetic; #9
must obtain arithmetic-capable consumer evidence before publication. The
printed toolkit identity and draft-byte digests bound each comparison.
Default-path behavior is reported separately with the lane disabled. The
independent job regenerates into a scratch tree and compares committed bytes;
it does not depend on the toolkit job. See [the dated installed evidence](CI.md#installed-reader-against-this-checkouts-contract--2026-11-18).

## Historical independent review request

The derivation author must not approve their own expectations. The following is
a review agenda, not a sign-off. Inspect the bytes, cited clauses and existing
`promotionCandidates` record in `conformance/manifest.json` before deciding.

| Candidate suffix (`fht-fasta-`) | Proposed rule derivation | Question for independent reader |
| --- | --- | --- |
| `parent-subset-citing-whole` | C1/FR-007 permits the parent pair; C3 compares the supplied parent digest, not biological subset coverage | Does checked-pass establish only cited file identity, leaving the derivation claim unverified? |
| `parent-real-digest-wrong-file` | C3 compares the stated digest against the supplied subset file, not any known file with that digest | Confirm verify succeeds for the child while verify-links reports checked-fail, not unchecked |
| `parent-masked-exact` | R1 covers exact case-sensitive bytes; C3 matches the masked parent's own digest | Confirm the stated parent digest independently and checked-pass without case normalization |
| `parent-case-folded-digest` | The original and masked parent have different header and sequence bytes; R1/C3 compare the actual supplied file | Confirm checked-fail; this fixture alone does not isolate sequence-case changes from header changes |

Sources: the draft [FR-007](../specs/005-rna-transcriptome-header/spec.md),
[C1-C3 and absorption notes](../conformance/README.md), and shared
[FORMAT.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FORMAT.md).
No implementation output substitutes for that review. If a candidate remains
unreviewed, keep that state visible rather than relabeling it accepted.

### Independent technical review — 2026-11-16

The coordinating root agent, separate from the derivation author, independently
read FR-007/C3 and FORMAT.md R1-R4 and recomputed the four child and three parent
checksums with Python stdlib SHA-512/256, without importing this repository's
runner, generator or the toolkit. Only the unique root `;~checksum:` line and
its LF terminator were excluded. All four child self-checksums matched, and each
child's nested parent digest equaled the manifest's stated parent digest.

| Parent | Independently recomputed checksum |
| --- | --- |
| Whole | `pdDy56KE7+tzfZfk9eVOAQOPc/Fj78DfNBWOpJC4xac=` |
| Subset | `6j+hYGoiuIO0VoiY4NwaOsnOzhtsEL97A0ss66imAdI=` |
| Masked | `2WBzTRWHA/8A0y8TvwMCVENlk1FetSR9Gt4zz0hrCT8=` |

The reviewer agreed with C3's proposed outcomes: subset-citing-whole and
masked-exact checked-pass; real-digest-wrong-file and case-folded-digest
checked-fail. The latter does not isolate sequence case from header differences.
A pass establishes cited file identity, not the scientific derivation claim.
This is an independent **technical review**, not maintainer/curator acceptance.
D3 subsequently accepted these expectations on November 19, 2026; the manifest
now records acceptance and removes the four promotion markers.

## Remaining review and publication gates

The Molik responses below settle the questionnaire's field choices; do not ask
those questions again. Final joint curator review remains distinct from source implementation; the four
file-identity expectations have received D3 disposition. The [#10 release/pilot split](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/10#issuecomment-6926906659)
keeps producer-pilot metadata and dataset decisions outside foundation publication
acceptance. Do not infer dateCreated, software or reuse terms for that separate
pilot, or require a new dataset program to complete this source packet.

Shared absorption, reader-lane vocabulary/default-path evidence and release acts
remain publication work. Existing draft comparisons do not deliver released
contracts or default consumer support, and this packet changes no issue gate.

## Verification recorded for this packet

On macOS with Python 3.13, on the suite as it then stood (72 vectors), the installed 0.11.0 lane exited 0: 28 valid / 44
invalid compared, 10 parent-link vectors, 0/72 default-path accepts, 28 byte-exact
strips and 28 metadata round trips. Stream checks executed **72 verify, 28 strip,
28 combine**, with byte-exact payload comparisons and verified combined stdout. The stdout
metadata is independently parsed and compared for values, nested key order and
exact scalar types, excluding only the regenerated root checksum. A deliberate
metadata change with unchanged payload and a recomputed checksum is detected.
The package pin printed `b9ad19a62772092e08935cff44ee77a50981bbaf` /
`11c69d6647736695beaa72976a1d9b30c0f44f8cfe55f8eb171c9d0bcb6795f8`;
local draft bytes printed
`59ad9641adcb0e5591045c2d894c066d1adc9984cca84c5ff6502f8dad88487e`.
Those different digests were reported as a finding, not relabeled equal.

The independent fixture checker passed all 72 vectors the suite then had, and
the examples; on 2026-11-18 it passes all 82 current vectors, now asserting each
rejection's rule. Native
repository unittests, provenance/legacy checks, documentation checks and pinned
Markdownlint passed. Harness controls deliberately corrupt payload stdout,
remove all cases and make the named default accept: each is detected. The Linux
installed-artifact lane subsequently passed in merged
[#49](https://github.com/FAIR-bioHeaders/FHT-Specification/pull/49), as recorded
in [the November 16 source verification](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/9#issuecomment-6924425112).
Later contract-aware Linux measurements are recorded in [CI.md](CI.md#installed-reader-against-this-checkouts-contract--2026-11-18).
These dated results do not claim that any future suite addition has run there.

## Existing DOI-pattern coverage — 2026-11-19

The existing imported `scholarlyArticle` pattern ends in `\S+`. Under the
family's settled ECMA-262 interpretation, NBSP (U+00A0) and narrow NBSP
(U+202F) are whitespace and a value ending in either fails C1. An internal
ZWJ (U+200D) is not whitespace and is permitted by that pattern. Four new
vectors pin both negative cases and explicit ASCII/ZWJ positive controls.
The generator computes genuine exact-byte checksums, so the negative cases
must fail the contract rather than file-integrity comparison.

The expectations follow the existing pattern's character-class semantics,
corroborated independently by a second reader using Node's actual regex
engine. They do not establish DOI registration, biological provenance or a
blanket invisible-character prohibition. No schema, field meaning, existing
fixture byte, outcome or parent-candidate promotion marker changes. This is
the owning-suite handoff for [Java #16](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools-Java/issues/16);
it does not repair or repin a consumer.

## Handoff order

Complete reproducible prepublication evidence and independent expectation review;
present the remaining decisions in one curator review. Only after recorded
acceptance prepare shared publication through the established maintainer process.
Verify published contract/registry/vector artifacts before promoting default
runtime support or refreshing consumer release pins. Shared absorption must
preserve the recorded V4/V5 selection asymmetry. FHT HTML drafting (#11) can
proceed independently, but no decision here invents it as a new release gate.

The historical round11 readiness-only packet changed no schema, vector, example,
pilot or published artifact bytes. The subsequent mixed draft addition below
changes the owning model/schema and adds three vectors and one example stem.

## Molik draft responses — 2026-11-16

[The recorded responses and clarifications](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8#issuecomment-6928571815)
supersede D1's initial omission of known heterogeneous sets: `mixed` is the fifth,
case-sensitive `moleculeType` value. It denotes producer-supported biological RNA
heterogeneity, not unknown composition, a library preparation, or the alphabet.
This is an additive enum change in the unreleased draft `1.0`, not publication or
joint curator adoption. Four-value readers, including the pinned 0.11.0 draft
reader, reject this newly valid value and need an explicit future consumer update.
The three construction values, nine required fields and existing taxon members
are retained. The ordered `sample` array remains; BioSample URLs belong in
`relatedLink`, following FHR. Describe protocol/kit information in `documentation`
and put actual protocol URLs in `relatedLink`; no protocol/kit field is added,
and `libraryStrategy` is not overloaded. Current statistics, parent behavior and
field names remain. No new required URI, sample deprecation or mixed construction
value is authorized. Publication and joint review remain separate gates.

The new source-contract tests accept `mixed` and reject `Mixed` and construction
`mixed`. The installed 0.11.0 lane specifically measures rejection of the newly
valid value, reports acceptance/strip/combine NOT-RUN for it, and executes all
other vectors. This consumer gap is not a normative invalid outcome. Native's
independent 2026-11-16 four-candidate review confirmed C1/self-checksums and C3's
two matches/two mismatches. All four children are unrelated synthetic RNA, so no
subset extraction or biological derivation is proven. The case-folded parents
also differ in genome title; all candidates have dateCreated 2026-11-10. Existing
promotion markers remain unchanged; this is technical review, not curator approval.
