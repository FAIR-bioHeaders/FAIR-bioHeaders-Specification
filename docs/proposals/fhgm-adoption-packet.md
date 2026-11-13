# FHGM adoption decision packet (#204)

**What this packet is:** a consolidated decision aid for the **joint-maintainer
review of FHGM** under the recorded [2026-11-12 Option C ruling](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204#issuecomment-6829197859)
(native gene-model contract + FHGFF3-embedded `x-` transport, release held).
It maps the current state as of 2026-11-13 with every claim linked to merged
content, turns the v0.1 draft's six open questions and four flagged deviations
into a review agenda with evidence positions, lays out the adoption mechanics
checklist the review's output feeds, and restates the boundaries. Its point is
that the review can be a reading-and-deciding session: the pilot evidence,
fixture census and shared-side artifact enumeration are all assembled here
rather than re-derived.

**What this packet is not:** it is not an adoption, a publication, a version
assignment, or a support claim. FHGM still has no released contract, no
`schemaVersion`, no w3id schema URL, and no `schemas/versions.json` entry, and
this document changes none of that. Nothing here merges, publishes or
promotes anything; adoption requires the joint maintainer decision recorded on
[#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204),
and curator acceptance remains a separate gate (see §4). Every
"recommendation" below is a recommendation only, and positions the pilots
**cannot** support — chiefly the curator-gated ones — are said so instead of
being guessed at.

Prepared 2026-11-13 against shared `main` at `e15e1d0` and
FHGM-Specification `main` at `8b0ca00` (the merged v0.1 draft).

---

## 1. Current-state map (dated, every claim linked to merged content)

| When | What | Where it is merged |
| --- | --- | --- |
| 2026-11-04 | #204 opened as a new-type proposal; maintainer record that FHGM ≠ FHGFF3 (annotation vs model contribution). | [#204 body + 11-04 comments](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204) |
| 2026-11-05 | Revised recommendation: start FHGM-derived from FHGFF3, decide subtype-vs-sibling by field comparison; development repo chosen as a fork of FHGFF3 (inherited biodatamodels/gff-schema baseline, licensing question unresolved). | [#204 11-05 comments](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204#issuecomment-6666453057); FHGM PR #1 (setup, merged); repo state described in [`docs/FHGM.md`](../FHGM.md) |
| 2026-11-10 | Pilots merged: **S6k** real-provenance fixture (deposit-derived, transcripts/peptides verified against the named assembly) and the **revision pilot** (two embedded records + predecessor pointer `annotationChecksum + modelId + modelVersion`) — the pilot that first showed the base schema accepts stale/neighbor pointers. | [FHGM PR #3](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/3), [PR #4](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/4) (both merged 2026-11-10); [`development/examples/`](https://github.com/FAIR-bioHeaders/FHGM-Specification/tree/main/development/examples) |
| 2026-11-10 | Decision record merged: deposit evidence table, five proposed decisions (validation-layer subtype; ownership; gene-scope identity; single-predecessor revision with acceptance kept separate; existing assembly rule), compatibility table. Minimal/rich fixtures pass released FHGFF3 1.1 + checksum. | [FHGM PR #7](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/7) (`51ff023`) → [`development/CONTRACT-REVIEW.md`](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/CONTRACT-REVIEW.md) |
| 2026-11-10 | Maintainer pre-commitment on #204 to the subtype-validator proposal ("explicitly selected FHGM subtype validator over the released FHGFF3 file identity, with a separate model contract identifier/version"); draft overlay + snapshot validation implemented. | [#204 11-10 comments](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204#issuecomment-6774377632); [FHGM PR #10](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/10) (`0590e31`) |
| 2026-11-10 | Shared draft overview page added (still frames subtype/overlay/sibling as open; describes repo contents and boundaries). | shared PR #213 → [`docs/FHGM.md`](../FHGM.md) |
| 2026-11-12 | **Option C ruling: hybrid, staged.** Native model contract (own schema/requiredness/model-level validation) carried by FHGFF3-embedded `x-` transport; release held; a reviewed draft-contract PR in FHGM-Specification authorized. Same comment records the #56 scope-down. | [#204 ruling](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204#issuecomment-6829197859) |
| 2026-11-12/13 | **First Option C artifact merged: native draft contract v0.1 (proposal).** 10-field record schema (required `modelId`, `modelVersion`, `featureId`, `reference`), transport-only overlay, three-verdict model-level checker, 11 byte-reproducible fixtures; the base-schema gap re-proven live against current shared `fhgff3.json` with fair-bioheaders 0.10.0 (all 8 rejections pass base schema + checksum). | [FHGM PR #11](https://github.com/FAIR-bioHeaders/FHGM-Specification/pull/11) (merged 2026-11-12T23:09Z, `8b0ca00`) → [`development/model/`](https://github.com/FAIR-bioHeaders/FHGM-Specification/tree/main/development/model) ([schema](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/model/fhgm-model.schema.json), [checker README](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/model/README.md), [fixtures](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/examples/model/README.md)) |
| 2026-11-13 | **V7 draft lane ruled type-neutral**: unreleased draft contracts from the owning development repo's raw URL may be recognized only behind explicit opt-in, revision-pinned, loud warnings, never release-shaped; the ruling explicitly names FHGM model records, and notes that for FHGM "the practical consumer is model-level validation tooling (the record itself carries no schema URL — selection applies at the contract/validator level)." | [#221 ruling comment](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/221) |
| now | Open dependencies: [Tools #135](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/issues/135) (opt-in validation for the *reviewed* model contract) is open and gated; [#206](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/206) (pilot dataset provenance) was unblocked by the Option C ruling; website FHGM promotion is post-adoption. | as linked |

Status in one line: **under review — the draft artifact exists and its
central claim is reproducibly demonstrated; nothing about FHGM is adopted,
versioned or published.**

## 2. Review agenda — the v0.1 draft's own open items

Six open questions from
[`CONTRACT-REVIEW.md` § "Open questions for the #204 joint review"](https://github.com/FAIR-bioHeaders/FHGM-Specification/blob/main/development/CONTRACT-REVIEW.md)
plus four flagged deviations, each as question / options / evidence on the
table / position. Where the pilots support a recommendation it is stated and
**marked as recommendation only**; where the question is curator-gated (per
the 2026-11-11 maintainer instruction to get curator input before fixing those
defaults) no recommendation is manufactured.

### Open questions

**Q1 — Final field names.** `modelId`, `modelVersion`, `featureId`,
`reference`, `predecessor`, `annotates`, `publication.article/deposit`,
`reuseConditions`.
*Options:* (a) adopt v0.1 names; (b) rename for consistency with shared
objects before publication.
*Evidence:* the record's nested objects already mirror shared FHGFF3 shapes
(`contributors` mirrors `Author`, `methods.software` mirrors `Software`,
`publication` patterns mirror `scholarlyArticle`/`identifier`), and all three
fixtures plus the checker use the v0.1 names byte-reproducibly.
***Recommendation only:*** adopt (a) for the review of v0.x; a later rename is
a major-version candidate (it breaks record compatibility), so cheap change is
now, not after publication.

**Q2 — Is `modelId` curator-assigned or derived?**
*Options:* (a) curator-minted external IDs; (b) file-local derivation from the
gene `featureId`; (c) snapshot-scoped composite (checksum + feature ID).
*Evidence:* the S6k-derived fixture uses the gene feature ID as a *flagged
placeholder*; the pilots' cross-file pointer works with
`annotationChecksum + modelId + modelVersion` without any external minting
authority; CONTRACT-REVIEW decision 3 already defaults to "file-local model ID
allowed."
*Curator-gated for minting authority*, but the mechanics answer is on the
table. ***Recommendation only:*** fix (b)-as-default semantics in v0.2 (the
pointer machinery works with zero minting authority), keep (a) open as an
optional external-identifier field pending curator input — mirrors how
`identifier` works at file scope.

**Q3 — `modelVersion` semantics** (opaque vs ordered vs scheme).
*Options:* (a) keep opaque (equality/difference only, as v0.1); (b) require
ordering; (c) pin a scheme.
*Evidence:* the whole version-gap rule set was deliberately *bounded* to
supplied snapshots precisely because no ordering is claimed; `version-gap-skip`
and `version-reuse` fixtures pass with opaque comparison alone.
***Recommendation only:*** keep (a) through v0.x; ordering needs curator use
cases the pilots did not supply.

**Q4 — Model-contract identity.** v0.1 expresses identity only by explicit
validator selection.
*Options:* (a) selection-only until publication; (b) an in-record version
marker; (c) a contract URI in the file.
*Evidence:* the transport draft wording is explicit that an FHGM-carrying file
keeps its released FHGFF3 `schema`/`schemaVersion` and "FHGM adds no
file-type identity at v0.1"; the #221 V7 ruling already gives the draft stage
a rule-conformant recognition path that is selection-at-contract-level ("the
record itself carries no schema URL"); adding (b) or (c) later is additive.
***Recommendation only:*** adopt (a) now, mint the contract URI as part of the
shared publication artifact (it needs a w3id/versions.json decision, not a
draft-stage hack).

**Q5 — Schema pipeline: hand-authored JSON Schema vs the family LinkML chain.**
*Options:* (a) stay JSON Schema at publication; (b) migrate the record contract
to LinkML generation at publication.
*Evidence:* authored as JSON Schema because the PR #10 overlay was (stated
premise correction in PR #11); no LinkML artifacts exist for FHGM; the chain
that (b) would enter is `schemas/core.yaml` + per-type LinkML +
`scripts/check_linkml.py` + `make_jsonld.py` + drift checks — and the shared
repo's LinkML machinery is currently enumerated over the released types only.
***Recommendation only:*** decide (b) **at publication, not now** — but record
the choice in the review minutes because it determines the generator-
registration row of §3; a late surprise is worse than an early label.

**Q6 — Scope edges: transcript-only submissions, split/merge, assembly
migration, companion-file identity.**
*Options:* as left by decisions 3/4 (gene-scope start; distinct reviewed cases).
*Evidence:* Glys shows a real four-transcript bundle whose assembly link
cannot be verified from the scaffold name — direct support for keeping
transcript-only scope and assembly migration open rather than extrapolating
gene-scope rules; the DataCite relationship vocabulary review shows dataset
version relations do not express model supersession.
**Curator decision — no recommendation here** (per the 2026-11-11 instruction
and the #204 checklist item "consult gene-model authors/curators").

### Flagged deviations (each a draft choice needing maintainer sign-off)

**D1 — Record-level `reference` is required.**
*Options:* (a) keep required; (b) inherit from the file header, record omits it.
*Evidence:* #204's premise is a contribution interpretable apart from its
context; `record-without-reference` and `record-reference-conflict` fixtures
show both failure modes the requirement closes; checker rule 3 rejects a
record reference that contradicts the file genome link.
***Recommendation only:*** keep (a); reviewers who prefer (b) inherit a
silent-extraction hazard the packet's fixtures already demonstrate.

**D2 — The pointer must name its own `modelId`.**
*Options:* (a) keep; (b) allow model renames.
*Evidence:* this formalizes the stability assumption the PR #4 revision pilot
showed is load-bearing — `predecessor-name-mismatch` (naming the unchanged
neighbor `model-b`) is exactly the attack the base schema waves through;
renames belong to split/merge semantics that Q6 leaves open.
***Recommendation only:*** keep (a); renames are a Q6 case, not a v0.x
loosening.

**D3 — Version-gap rejection bounded to supplied snapshots.**
*Options:* (a) keep bounded; (b) claim transitive/external history checking.
*Evidence:* decision 4 explicitly kept transitive history open; the bounded
rule "only refuses to silently contradict the chain the reviewer handed it"
(`version-gap-skip` fixture). (b) would require an external history service —
outside every recorded boundary.
***Recommendation only:*** keep (a).

**D4 — Duplicate `modelId` within a snapshot is `ambiguous` (a named verdict),
not merely invalid.**
*Options:* (a) keep the three-verdict interface; (b) fold ambiguity into
unresolvable.
*Evidence:* the identity a pointer needs cannot be selected under a duplicate,
which is a defect of the *snapshot*, not of the pointer; `ambiguous-model-id`
fixture; downstream tooling (Tools #135) can branch on the distinction.
***Recommendation only:*** keep (a); verdict names are API surface and hardest
to change after a toolkit ships against them.

## 3. Adoption mechanics checklist (what happens *after* the review decides)

PR #11's report enumerates the shared-side artifacts a later adoption PR needs;
this checklist mirrors that enumeration with the dependencies this packet has
mapped. **None of it is authorized by reading this page; each row needs the
review decision first.**

- [ ] **Shared native artifact.** Publish the reviewed model contract through
  the shared specification (per CONTRACT-REVIEW decision 2). Location and form
  decision: `development/model/fhgm-model.schema.json` becomes a shared,
  published artifact (a new published path is needed — FHGM is not a header
  *file* contract, so it does not sit beside `fhr.json`/`fhgff3.json` without a
  stated reason). **Q5 feeds directly here:** LinkML (b) means registering a
  generator lane (`check_linkml.py`, `make_jsonld.py`, drift checks all
  currently enumerate the released types); JSON Schema (a) means the published
  file is itself the artifact and drift-checking reduces to a pinned-bytes
  rule. The review minutes should name which, or the adoption PR cannot start.
- [ ] **`versions.json` timing.** Register nothing until publication; the
  registry lists released contracts only, and Q4's recommendation (no in-file
  FHGM identity) means FHGM may *never* get a `schemaVersion` value in
  `versions.json` in the header sense — the publication decision is what
  identifier the *contract* gets (URI + version label) and whether that is
  registry-eligible or registry-ineligible by design. Decide in the publication
  PR, not before.
- [ ] **Conformance absorption.** The v0.1 result "all 8 model-level rejections
  pass the released base schema and exact-byte checksum" means **schema-vector
  conformance cannot express FHGM acceptance**: any conformance lane for FHGM
  must run the model-level checker (verdicts `resolvable/unresolvable/
  ambiguous`), against explicitly supplied predecessor snapshots. Decide:
  extend `conformance/manifest.json` with a checker-vector lane vs a separate
  FHGM conformance suite in the shared repo. The 11 byte-reproducible fixtures
  (`make_fixtures.py` regenerates `cmp`-identically) are the ready-made seed
  vectors either way.
- [ ] **V7 draft lane (interim, before any publication).** Already ruled and
  type-neutral on [#221](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/221)
  (2026-11-13): consumers may recognize the FHGM v0.1 draft from FHGM-Specification's
  raw URL only behind explicit opt-in, revision-pinned (commit + digest), with
  loud warnings, never at release-shaped URLs. This governs *draft-stage*
  tooling behavior; it grants no adoption and expires on FHGM's own publication,
  which registers the contract under V1 + the registry decision above.
- [ ] **Toolkit model-checker issue.** [Tools #135](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/issues/135)
  ("Add opt-in validation for the reviewed FHGM model contract") stays open
  and gated: it consumes the *reviewed* contract, the published checker
  interface (verdict names are API — see D4), and the pinned base-schema bytes
  pattern the draft checker already uses. Not before.
- [ ] **Website FHGM promotion path.** Draft → joint review (this agenda) →
  shared publication PR (the rows above) → **then** website promotion. The
  first website-adjacent edit is replacing the still-open "subtype/overlay/
  sibling" framing in [`docs/FHGM.md`](../FHGM.md) — a snapshot from 2026-11-10
  that predates Option C — as part of the publication PR, not as a standalone
  website claim. Site pages come after, mirroring how FHGFF3 was promoted from
  contract to site.
- [ ] **Five-repo AGENTS port.** The shared-side enumeration includes the
  AGENTS guidance port across the spec repositories; the workspace convention
  (shared sections byte-identical, two recorded local deltas) applies.
- [ ] **Labeling discipline throughout.** CHANGELOG, `docs/SCHEMA-VERSIONS.md`,
  `llms.txt` and conformance README effects belong to the publication PR;
  until then every FHGM artifact keeps its "proposal / no support claim"
  wording, and `check_draft.py`'s recorded caveat stands: the v0.1 checker run
  is not executed by FHGM-Specification's CI — commands and environment are
  documented, and CI integration is itself an adoption-mechanics task.

## 4. Boundaries (restated, consistent with #204)

These are quoted or paraphrased directly from the ruling and the merged draft;
adoption changes none of them:

- **No GFF3 replacement.** FHGM "does not define a replacement for GFF3
  feature semantics" and does not mandate a universal gene-prediction pipeline;
  transcript and exon structure stay in the native GFF3 `ID`/`Parent` graph.
- **No correctness certification.** The contract does not "certify orthology,
  biological correctness, or journal acceptance." A valid header never
  establishes a correct model; evidence assertions in a record are supplied
  assertions, not validation results — feature checks belong to gff3-validator,
  reference matching to its own inputs.
- **Resolution ≠ acceptance.** A `resolvable` pointer verdict only identifies
  the predecessor record; curator acceptance of a revision is "a separate
  decision with its own evidence, recorded outside the header check," and the
  checker never asserts it.
- **Transport grants nothing.** An FHGM-carrying file remains a valid FHGFF3
  1.1 file with its released `schema` URI and `schemaVersion`; `x-` extension
  fields never override standard fields (FORMAT.md R15); the file checksum
  covers record bytes, not any external registry; passing base schema +
  checksum + transport "has **not** passed FHGM validation."
- **No presumption of released FHT** for transcript/protein companion files;
  no FHGM `schemaVersion`, w3id URL or `versions.json` entry exists, and no
  toolkit/validator/builder support is claimed anywhere pre-adoption.
- **Standing rule:** a proposal's existence ≠ adoption; publication, aliases
  and DOIs remain separate maintainer actions.

*End of packet. Prepared for review on #204; grants nothing.*
