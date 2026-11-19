# Round 14 FHGM evidence and scope decisions

The maintainer selected the recommendations in shared #211 on 2026-11-19:
[formal D4–D6 record](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7017854934).
This owning draft implements those choices; it publishes no contract and
changes no consumer pin. The shared publication artifact remains separate.

## D4: earned evidence

The checker accepts `--report-json FILE` and writes actual layers and K1–K6
states for the selected carrier and every supplied snapshot. `pass` means the
predicate ran and passed; `reject` means it ran and failed; `not-run` means a
prerequisite was unavailable or not reached. Snapshot model state may be
`partial` after K1–K5; only the selected carrier earns a full model pass after
K6 and all relevant supplied-snapshot prerequisites pass. The checker does not
run GFF3 validation, so its GFF3 state remains not-run. The suite runs the
independent GFF3 tool and reports that layer separately.

A complete empty inventory rejects K4. Unreadable or malformed inventory is
untrustworthy: K4 stays not-run with a reason. Missing files, unknown base
bytes/citations and missing registered base bytes refuse execution rather than
create model evidence. A failed supplied snapshot leaves selected-file K6 and
fullModel not-run. Snapshot own-pointer claims are not transitively resolved;
there is no external lookup or transitive history service.

The suite's `--report-json FILE` reports vector visits, actual selected-carrier
rule predicates evaluated, layer expectations compared, complete vectors
matched, and complete model passes separately. Invalid pins or execution
prerequisites produce a refusal receipt with a reason and no aggregate counts.
Offline vectors retain actualEvidence null; skipped tools cannot earn complete
vector matches. Legacy manifest `layers.model` retains the historical combined
checker-process result. `evidenceExpectation.model` is a separate clause-derived
fullModel expectation; a process rejection is not automatically a model rejection.

## D5: local root scope

K4 requires exactly one row whose decoded ID equals featureId, whose type is
`gene` or `SO:0000704`, and whose Parent tag is absent. Bare `Parent` and
`Parent=` cannot establish root status. Multiple rows sharing one ID and other
SO gene-like types are outside initial FHGM model scope; that scope rejection
is not a generic GFF3 invalidity claim. Feature-graph and biology checks belong
to `gff3-validator`. Transcript-only, split/merge and assembly migration are
explicitly deferred.

## D6: model identity and publication

Distinct model IDs may target one gene. A revision may change its file-local
featureId. Opaque versions may follow A → B → A: only immediate predecessor
inequality is required. Stable modelId and same-assembly matching still apply.
Strict K5 comparability is retained: no contradictory form and at least one
shared comparable form. Gene-scope noncoding models are included.

Hand-authored JSON Schema remains the v0.x mechanism. Existing normative ECMA
text rules remain, with the independently checked Unicode cases from PR #33;
no new regex-engine support claim is made. The model contract is explicitly
selected separately from FHGFF3 file identity. No new record schema field or
FHGM header registry row is introduced. A concrete publication artifact needs
later shared review.

## New expected outcomes derived from clauses

These expectations were selected before running the checker. Passing controls
are needed alongside negatives so strengthening a rule cannot silently reject
permitted cases.

| Vector | Clause derivation | Expected fullModel |
| --- | --- | --- |
| competing-model-ids-same-target | K3 requires distinct modelId values, not unique featureId values. | pass |
| changed-file-local-feature-id | K6 compares stable modelId, immediate version and assembly/reference; both local targets resolve independently. | pass |
| opaque-version-a-initial | K6 has no predecessor claim to resolve. | pass |
| opaque-version-b-successor | B differs from supplied immediate A and all pointer fields match. | pass |
| opaque-version-a-reused | Reused A differs from supplied immediate B; the older A does not supersede B. | pass |
| noncoding-root-gene | The source gene row is root type gene and has RNA/exon descendants without CDS; protein coding is not required. | pass |
| feature-inventory-complete-empty | A complete zero-row inventory has zero target matches. | reject K4 |
| feature-inventory-no-identifiers | A complete inventory with a row but no ID has zero target matches. | reject K4 |
| feature-target-bare-parent | The exact Parent tag is present, so the target is not an eligible root; independent GFF3 syntax may also reject. | reject K4 |
| feature-target-empty-parent | Empty Parent value does not remove the tag. | reject K4 |
| feature-target-other-so-type | SO:0001263 is not one of the two accepted root types; scope limit only. | reject K4 |

## Noncoding source provenance

The four rows in `noncoding-source.gff3` are copied verbatim from the complete
RefSeq archive already pinned by the dmel4 examples, downloaded in full on
2026-11-19: 8,688,226 bytes, SHA-256
`9a372f10f86f4fe4222d070a101716b7565affdd6cb96efae249e8afa3b2c726`.
[Exact archive](https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/215/GCF_000001215.4_Release_6_plus_ISO1_MT/GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz).
Selection is chromosome NC_004353.4, root `gene-Dmel_CR45124` and its transitive
local Parent descendants: one gene, one antisense_RNA and two exon rows,
coordinates 42774–43374; zero CDS rows. The exact assembly reference comes from
the existing dmel4 fixture. New model identifiers and versions are synthetic
review metadata. The source rows retain their original US Government work
status; authored metadata and generator are MPL-2.0. This scope fixture claims
neither biological validation nor curator acceptance.

## Independent expectation review and mutation controls

On 2026-11-19 independent reader `independent_review_275`, gpt-6.1-terra,
operated by David Molik, accepted all eleven new outcomes after checking the
actual manifest, bytes, generator, contexts and source subset. This authoring
agent inherited parent gpt-6.1-sol; the parent verified runtime session metadata.
Expectation acceptance is separate from PR approval. The reader did not
independently download the source archive or claim biological derivation.
The twelve historical dmel expectations also have individual accepted records
from that reader in the manifest and promotion packet.

Four locally run checker mutants were detected by the state-machine tests:
Parent truthiness instead of presence, silently skipping empty inventory,
skipping supplied-history validation, and forbidding opaque A reuse. Each
produced a failing relevant regression test; the unchanged checker passed the
same controls. The review guard also rejects each actual unfinished marker
(`requires independent review`, `OBSERVED outputs`, `candidate-unreviewed`)
and rejects a missing accepted reader record. Deleting marker prose alone does
not satisfy the guard.

## Validation measured for this change

The full installed-tool run matched 184/184 vector checks across both released
bases: 92 vectors (24 valid, 68 invalid), zero twin outcome changes, 63 earned
gap-proof rejections per base. Its JSON receipt records 184 visits, 728 actual
selected-carrier rule predicates evaluated, 736 layer expectations compared,
174 complete vector matches and 48 complete model passes. The remaining ten
visits have expected fullModel not-run, and do not enter either complete count.
All earlier 81 byte pins, checksums, legacy layer outcomes, reasons and supplied
contexts were independently compared with the merged parent and are unchanged.
The installed dependency environment passed 116 unit tests; the standard-library
run passed 116 with ten dependency-related skips. Dual-base draft self-check,
Markdown lint and owned local-link checks passed. The PR still requires its
own current-head independent review and CI before merge.

## PR review correction: trustworthy attribute inventory

The independent gpt-6.1-terra PR review reproduced false root passes for
`ID=toy-a;Parent =other` and `ID=toy-a;ID`. These malformed identity/root
attributes now refuse inventory construction instead of silently establishing
a root. Whitespace-disguised ID/Parent tags, missing/empty ID values, duplicate
ID attributes and raw comma-separated IDs are untrustworthy. K4 and fullModel
remain not-run with a reason, including when such a snapshot is supplied as
history. Exact lowercase custom tags and percent-decoded ID values keep their
semantics. This limited identity/root parse guard adds no graph/biology checks;
bare Parent and Parent= remain the explicitly selected K4 rejections.

After the PR correction, all 117 installed-dependency unit tests passed;
the standard-library run passed with eleven dependency skips. A fifth mutant
removing both new malformed-attribute guards was caught by the seven-case
parser regression, and the original four mutants were rerun and caught.
