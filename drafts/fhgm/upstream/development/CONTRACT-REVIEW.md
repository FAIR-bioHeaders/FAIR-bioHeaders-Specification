# FHGM contract review for David and Adam

Current disposition: [Round 14 D4–D6](conformance/DECISIONS-2026-11-19.md)
supersedes the historical open wording below. Hand-authored JSON Schema is
settled through v0.x; model-contract publication is separate from FHGFF3 file
identity. Historical review questions below are retained as a dated record.

Draft decision record for [shared issue #204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204).
The comparison target is [released FHGFF3 1.1](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.5.0/fhgff3.json).

Status: native draft contract v0.1 (proposal); the 2026-11-12 Option C ruling
(native model contract plus FHGFF3-embedded `x-` transport, release held) is
implemented as a draft under the proposed decisions below, and the
[2026-11-12 draft contract section](#draft-contract-v01-2026-11-12) records how,
plus reasoned deviations that remain proposals. The
[review dispositions (2026-11-14)](#review-dispositions-2026-11-14) record the
joint review's positions on the six open questions and four flagged deviations,
taken against the shared specification's adoption decision packet. They close
Q1–Q4 and D1–D4 at the packet's recommended positions. Later maintainer
direction settles Q5 as hand-authored JSON Schema through v0.x; Q6 scopes are
explicitly deferred by the Round 14 decision. Publication-ready is not published: FHGM
still has no released contract, no `schemaVersion`, no schema URL and no
`schemas/versions.json` entry, and selection rule V7 keeps it that way until the
shared publication PR lands.

## Deposit evidence and field mapping

| Deposit evidence | FHGFF3 reuse | Model requirement or open work |
| --- | --- | --- |
| [S6k](https://doi.org/10.22002/e86gh-a7p16) bundles annotation, transcript and peptide files. The converted pilot verifies two isoforms against the named assembly. | Required `annotation` and `taxon` describe the file and organism. The conditional assembly link is satisfied by the verified `genomeReference`. Optional `scholarlyArticle` and `identifier` distinguish the article and deposit. | Use the gene as the default target and native GFF3 relationships for isoforms. Keep sequence comparisons and CDS stop warnings as separate outcomes. |
| [Glys](https://doi.org/10.22002/apf5b-xyg45) bundles annotation, four transcripts and four peptides, including repeated translations. The inspected archive names a reverse-strand sequence; assembly version is still unverified. | Optional `source` can record the archive and `relatedLink` can identify companion resources. The required genome link cannot be supplied from the scaffold name alone. | Track transcripts by native feature ID rather than by peptide count. Keep this case in source review until the assembly link can be verified. |
| [ABCB7](https://api.datacite.org/dois/10.22002/pr8ks-0fg53) is a version 1.0 Model deposit linked to an article and dataset version family. | Optional `scholarlyArticle`, `identifier` and `reuseConditions` can represent article DOI, deposit DOI and deposit rights. | A repository resource type or version-family link provides no model identity authority. This was a metadata review only. |
| [Corrected synthetase models](https://api.datacite.org/dois/10.22002/hv4eg-wg213) are a version 1.0 Dataset linked to the article and version family. The study compares models across assemblies. | Each FHGFF3 file still needs its own assembly link. Optional `source`, `annotationSoftware` and `annotationProtocol` describe inputs or methods for the file where applicable. | A prior annotation checksum plus model ID and version identifies the predecessor record. Dataset version relations do not establish model supersession. This was a metadata and published-use-case review; the pilot is synthetic. |

Keep `schema`, `schemaVersion`, `version`, `metadataAuthor`, `dateCreated`
and `checksum` at file scope with their FHGFF3 meanings. A model version and
contributor role belong on the model. Article authorship, journal review and
curator acceptance are separate assertions. Record evidence at the narrowest
scope it supports. Use supplied identifiers and roles, and leave unknown
optional values absent. The [source review](examples/PILOT.md) records inspected
archive members, licenses and checksums.

## Proposed decisions

1. **Subtype at the validation layer.** Use the FHGFF3 file contract and a
   separately versioned, explicitly selected FHGM extension validator. Keep the
   released FHGFF3 URI and schema version in the file. After approval, give the
   model contract its own identifier and version separate from those file fields.
   A sibling file type would be warranted if real cases need a different
   subject, incompatible assembly rules or incompatible file semantics.
2. **Ownership.** Develop the model contract and fixtures in FHGM-Specification.
   Coordinate GFF3 checks with gff3-validator and publish a reviewed model
   contract through FAIR-bioHeaders-Specification with David and Adam's approval.
3. **Scope and identity.** Start with one uniquely resolved local feature at
   gene scope. Support explicit transcript scope when curators confirm a
   transcript-only submission use case. Allow a file-local model ID, preserve
   supplied external identifiers with their authorities, and use the snapshot
   checksum with model ID and version for cross-file references. Use the native
   [GFF3 feature graph](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md)
   for isoforms and shared features. Allow noncoding models without CDS or
   protein files.
4. **Revision.** Start with single-predecessor, same-assembly revisions. Treat
   split, merge, and assembly migration as distinct cases requiring examples
   and review. A resolved pointer only identifies the prior record. Record
   acceptance separately with the responsible curator or authority and evidence
   for the decision. The [DataCite relationship vocabulary](https://datacite-metadata-schema.readthedocs.io/en/4.6/appendices/appendix-1/relationType/)
   distinguishes dataset membership and version relations; it does not express
   approval of a model in a particular annotation.
5. **Assembly.** Keep the existing FHGFF3 assembly rule. Use a verified
   accession and SeqCol digest or an FHR link. [GA4GH refget](https://ga4gh.github.io/refget/)
   identifies reference collections from their content. A scaffold name or
   dataset DOI alone cannot establish collection identity.

Ask curators to confirm transcript-only use, identifier minting and authority
for acceptance, using the above defaults as the review proposal. Treat any
change to released FHGFF3 constraints or field meanings as a separate contract
proposal.

## Draft contract v0.1 (2026-11-12)

Native draft contract v0.1 (proposal) under shared #204 review; no
publication, no support claims. Per the recorded Option C hybrid decision, the
[draft model](model/README.md) now states a native FHGM record contract —
[`model/fhgm-model.schema.json`](model/fhgm-model.schema.json), authored as
JSON Schema and enforced per record — carried by FHGFF3 1.1
[`x-` transport](model/README.md#transport-fhgff3-embedded-records-normative-draft-wording)
under `x-fhgm-models` (FORMAT.md R15). [`model/fhgm-draft.schema.json`](model/fhgm-draft.schema.json)
was reduced to a transport-only overlay; [`model/validate_fhgm.py`](model/validate_fhgm.py)
is the separate model-level checker with the `resolvable` / `unresolvable` /
`ambiguous` verdicts.

Mapping to the proposed decisions above:

| Decision | Draft contract v0.1 |
| --- | --- |
| 1. Subtype at the validation layer | Implemented: the file keeps its released FHGFF3 URI and `schemaVersion` 1.1; FHGM is selected only by explicitly running the checker. The model contract's own in-file identity is not yet expressed — see open questions. |
| 2. Ownership | Implemented: model, checker and fixtures live in this repository's `development/` tree; nothing was published to the shared repository. |
| 3. Scope and identity | Implemented: required `modelId`, `modelVersion` and gene-scope `featureId`; snapshot-checksum identity for cross-file references (`predecessor.annotationChecksum` + model ID + version). |
| 4. Revision | Implemented: single-predecessor, same-assembly pointers, resolved against explicitly supplied snapshots; resolution and curator acceptance stay separate, and the checker never asserts acceptance. |
| 5. Assembly | Implemented at file scope unchanged. At record scope v0.1 requires a `reference` binding mirroring the genome-link alternative — a deviation, below. |

Proposed deviations and extensions, each a draft choice for the maintainers,
not an adoption. Reviewed 2026-11-14: all four were kept at their recommended
positions — see [review dispositions](#review-dispositions-2026-11-14), which
also corrects how D4 is realized in the checker.

- **Record-level `reference` is required.** #204's premise is that a
  contribution stays interpretable apart from its context; an extracted record
  with no assembly binding loses it. The checker additionally rejects a record
  reference that contradicts, or shares no comparable form with, the file
  genome link (rule 3 in the [model README](model/README.md#model-level-constraints-the-base-schema-cannot-enforce)).
  A reviewer may prefer inheritance from the file header instead; the fixtures
  demonstrate the embedded-binding shape either way.
- **The pointer must name its own `modelId`.** This formalizes the revision
  pilot's assumption that `modelId` is stable across revisions of the same
  model; renames would need split/merge semantics still under review.
- **Version-gap rejection is bounded to supplied snapshots.** A pointer that
  skips a recorded successor present in the supplied predecessor set is
  `unresolvable`. No transitive or external history is claimed — decision 4
  kept transitive history open, and v0.1 only refuses to silently contradict
  the chain the reviewer handed it.
- **Duplicate `modelId` within a snapshot is `ambiguous`, not merely invalid.**
  The identity the pointer needs cannot be selected, so the verdict name is
  part of the interface.

### Historical questions for the #204 joint review

v0.1 deliberately does not close. Dispositions were recorded on 2026-11-14 in
the [review dispositions](#review-dispositions-2026-11-14): Q1–Q4 adopted, Q5
held as a publication gate, Q6 left to curators.

1. **Final field names.** `modelId`, `modelVersion`, `featureId`, `reference`,
   `predecessor`, `annotates`, `publication.article`/`deposit` and
   `reuseConditions` are proposals; naming consistency with shared objects is
   the shared repository's call.
2. **Is `modelId` curator-assigned or derived?** The S6k-derived fixture uses
   the gene feature ID as a placeholder; who mints stable IDs, and under what
   authority, is unassigned.
3. **`modelVersion` semantics.** v0.1 treats it as opaque (equality/difference
   only). Ordering, comparison or scheme requirements await curator input.
4. **Model-contract identity.** Decision 1 asks for the model contract's own
   identifier and version. v0.1 expresses it only by explicit validator
   selection; whether a contract URI or embedded version marker is added, and
   where it lives given R15, is undecided.
5. **Schema pipeline.** The record contract is hand-authored JSON Schema
   because the PR #10 overlay was; adoption should decide whether it moves to
   the family LinkML chain at shared publication.
6. **Transcript-only scope, split/merge, assembly migration and companion-file
   identity** remain exactly as decision 3/4 left them.

## Review dispositions (2026-11-14)

The joint review of the six open questions and four flagged deviations ran
against the [FHGM adoption decision
packet](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/proposals/fhgm-adoption-packet.md)
merged in the shared specification, which the maintainer accepted on
2026-11-14 ("we can publish"). The positions below are what the reviewed
contract now states. They are review decisions inside a
still-unreleased draft: nothing here publishes, versions or registers FHGM, and
per selection rule V7 the draft takes no release form until the shared
publication PR lands. The release vehicle (`v0.7.0` with FHT or its own
`v0.8.0`) is a maintainer decision; this record assumes neither.

| Item | Disposition taken | Evidence and dissent |
| --- | --- | --- |
| Q1 — field names | Adopted as drafted: `modelId`, `modelVersion`, `featureId`, `reference`, `predecessor`, `annotates`, `publication.article`/`deposit`, `reuseConditions`. | The packet's recommendation (a). The nested objects already mirror the shared FHGFF3 shapes and every fixture and the checker use these bytes; a rename is a major-version candidate, so it is cheap only before publication. No dissent. |
| Q2 — `modelId` authority | Adopted: **file-local by default**. `modelId` is unique within one annotation snapshot and needs no minting authority; a producer-supplied external identifier may occupy the same opaque field, with its authority recorded alongside it. | The packet's recommendation (b)-as-default, plus decision 3's existing allowance. **Partial dissent:** the packet also proposes keeping "an optional external-identifier field pending curator input". No pilot needs a second field — `modelId` is opaque, and `publication.deposit` already carries deposit CURIEs with their authorities — and a new optional field is a schema addition with its own cycle. So no field is added by this review; if the curator round asks for one, it comes as a labeled draft addition. *Who may mint external model IDs remains curator-gated.* |
| Q3 — `modelVersion` semantics | Adopted: **opaque**, equality/difference only, through v0.x. An immediate revision must differ from its predecessor; `9` may name a revision earlier than `2`. | The packet's recommendation (a), and the pilots support it: the whole gap rule set is bounded to supplied snapshots precisely because no ordering is claimed. Ordering needs curator use cases the pilots did not supply. Pinned by the `version-gap-*` and `version-reuse` vectors. |
| Q4 — model-contract identity | Adopted: **selection-only until publication**. No in-record contract version marker and no contract URI in the draft. | The packet's recommendation (a); the record keeps carrying no `schema` field, and the transport keeps the released FHGFF3 file identity. Consequence carried forward, not decided here: because FHGM records name no schema, the publication PR must state whether the contract is `schemas/versions.json`-eligible at all (rule V1 selects a *file's* schema) or registry-ineligible by design, with a contract URI minted beside it. |
| Q5 — schema pipeline (historical; superseded) | **Now settled through v0.x: hand-authored JSON Schema.** Historical disposition: The draft stays hand-authored JSON Schema; the LinkML-chain question is recorded as a publication gate. | **Ambiguity flagged in the packet, not resolved by us.** Its recommendation reads "decide (b) **at publication, not now**", which can be read as endorsing the family LinkML chain or as deferring the choice; its evidence section establishes only that the shared chain (`schemas/core.yaml`, per-type LinkML, `scripts/check_linkml.py`, `scripts/make_jsonld.py`, drift checks) enumerates the released types today. Both branches and their cost are named below so the publication PR cannot be started without the choice on the record: LinkML means registering a generator lane for a contract that is not a file-header schema; JSON Schema means the published file *is* the artifact and drift checking reduces to a pinned-bytes rule. |
| Q6 — scope edges | **Left open, exactly as decision 3/4 and the packet leave it.** No transcript-only scope, no split/merge, no assembly migration, no companion-file identity in v0.x. | The packet makes no recommendation (curator decision, per the 2026-11-11 instruction). The conformance suite lists these as *open scope* with no vectors and no implied verdicts rather than silently testing them as invalid-by-design. |
| D1 — record `reference` required | **Adopted (keep required)** — a record carries its own assembly binding, mirroring the FHGFF3 genome-link alternative. | The packet's recommendation (a); `record-without-reference` shows the extracted-record loss the requirement closes. |
| D2 — pointer names its own `modelId` | **Adopted (keep)**. A predecessor pointer that names another `modelId` is `unresolvable`. | The packet's recommendation (a). This is the load-bearing stability assumption from the PR #4 revision pilot; `predecessor-name-mismatch` is the attack the released base schema waves through. Renames stay a Q6 split/merge case, not a v0.x loosening. |
| D3 — version-gap rejection bounded to supplied snapshots | **Adopted (keep bounded)**. The checker only refuses to contradict the chain it was handed. | The packet's recommendation (a); decision 4 kept transitive history open and (b) would need an external history service outside every recorded boundary. Pinned as a *pair*: the same bytes are `unresolvable` with the recorded successor supplied and `resolvable` without it. |
| D4 — duplicate `modelId` is `ambiguous` | **Adopted (keep the named outcome)**, with one correction to the draft's claim about where it appears. | The packet's recommendation (a) calls it a three-verdict *pointer* interface. As implemented, and as the pilots ran it, ambiguity is detected while loading a snapshot, so `ambiguous` is a **snapshot-level rejection** and `resolve_predecessor` returns only `resolvable`/`unresolvable`. The [model README](model/README.md) now says so; a true per-pointer `ambiguous` verdict would be a checker-interface change for a later draft, not a wording fix. Consumers (Tools #135) should branch on the rejection reason, which is why the reason text is part of the vector manifest. |

### Raised by the review

1. **Are supplied snapshots' own pointers resolved?** No. Rule K6 resolves the
   selected file's pointers against the supplied set; each supplied snapshot
   must pass the *snapshot-level* checks (base schema, transport, record
   contract, K3–K5), but its own `predecessor` claim is not resolved. The
   draft README's parenthetical "each of which must itself pass all checks"
   overstated this and has been corrected. Whether a reviewer may hand the
   checker a chain whose intermediate link is itself unverified is a new
   question for the curator round, numbered **Q7** and carried as open scope
   `O6` in the conformance manifest; v0.x keeps the weaker, bounded behavior and
   the suite pins it with a positive vector
   (`history-with-unresolved-own-pointer`) so the choice is visible instead of
   accidental.
2. **How strong is K5 (the draft's rule 3)?** The packet summarizes D1's checker
   rule as "rejects a record reference that contradicts the file genome link".
   The implemented rule is stronger: it also rejects a record reference that
   *shares no comparable form* with the file link, so a record bound by an FHR
   parent checksum inside a file whose genome link is an accession plus SeqCol
   digest is rejected even though nothing contradicts. That is defensible (the
   file would then carry two unrelated authority claims about the same
   assembly) but it is not what the packet's sentence says. The
   `reference-forms-not-comparable` vector pins the behavior; confirm it is the
   intended strength, or narrow the rule to contradiction only in a later draft.

## Compatibility and verification

| Example | Released FHGFF3 1.1 compatibility |
| --- | --- |
| [Minimal](examples/contract/minimal.fhgff3.gff3) and [rich](examples/contract/rich.fhgff3.gff3) | Both pass the base schema with format checking and exact-byte checksum verification. Available GFF3 core checks report zero errors and warnings. |
| [S6k](examples/s6k/README.md) | The headed conversion passes the base contract. The recorded sequence match and separate stop warnings remain visible. |
| [Revision pilot](examples/revision/README.md) | Original, revision and two intentionally bad pointers pass the base contract. The model-level resolution check rejects the wrong-model and stale pointers. An unsupported `derivedFrom.relationship` is rejected by the base. |
| [Contract v0.1 fixtures](examples/model/README.md) | All eleven fixtures — three positives and eight rejections — pass the released base schema and exact-byte checksum; only the model-level checker distinguishes them, per the fixture table. They are cited in place by the [conformance manifest](conformance/manifest.json), which adds 14 generated vectors, re-runs three of these committed files under different supplied histories, and includes the contract examples and the S6k record fixture: 31 vectors over 28 files, 12 valid and 19 invalid, 17 of the 19 rejections gap-proof. |
| Glys source archive and unconverted deposits | Source material only. They have not been verified as headed FHGFF3 examples. |

The base schema accepts experimental extension content without checking FHGM
semantics. Schema and checksum checks were run separately from the available
GFF3 core checks, which did not run Sequence Ontology or genome-aware checks.
See the [INSDC supplement](INSDC-COVERAGE.md) for the submission boundary.

The [draft model-level checker](model/README.md) implements contract v0.1:
it runs the released base schema, the transport overlay and the native record
contract, then applies the model-level rules and revision-pointer verdicts
against the [contract examples](examples/contract/README.md), the
[committed fixture set](examples/model/README.md) and the
[S6k-derived record fixture](examples/s6k/README.md). `model/check_draft.py`
re-proves each run, including that the released base schema and checksum accept
every model-level rejection fixture. The contract fixtures were updated to the
v0.1 record shape on 2026-11-12 and their checksums recomputed.

CI integration landed with #9 rather than waiting for publication: the
[model-conformance workflow](../.github/workflows/model-conformance.yml) runs the
[conformance runner](conformance/README.md), this self-test and the offline
byte/digest lane on every pull request and push to `main`. Every outcome recorded
in the manifest was observed by running the committed checker on 2026-11-14 with
the toolkit, `jsonschema`, Python and `gff3-validate` versions named in
[`conformance/provenance.json`](conformance/provenance.json); the workflow's own
first execution is the run of this pull request, reported back here once it
finishes. Two review findings came out of writing the vectors, recorded above:
supplied snapshots' own pointers are not resolved (Q7), and rule K5 requires a
comparable reference form rather than only the absence of a contradiction.

## Maintainer decisions recorded 2026-11-15

1. **Dual FHGFF3 base support (closes the F1 framing from the real-data
   examples, [examples/dmel4/README.md](examples/dmel4/README.md)).**
   Asked as "rebase the single pin to 1.2 (A), stay pinned to 1.1 (B), support
   both (C)", the maintainer decided **C**. Implemented as base *selection*: the
   checker routes each carrier by its declared `schemaVersion` against the
   registry in `model/base-schemas.json`, the overlay admits the two released
   identity branches, and the conformance suite is matrixed — the sealed 1.1
   lane and its evidence trail stay intact, the new `base_matrix.json` records
   the 1.2 observation. Nothing about this changes rule V7: FHGM stays a draft
   with no release form. Measured outcome: 31 twins, 0 verdict changes; the
   17/19 gap-proof split holds on both bases; the v0.5.0→v0.6.0 release delta
   (dotted BUSCO dataset versions, gated to 1.2 carriers) touches no FHGM
   content because no vector or fixture carries a `completeness` object.
2. **Promotion of selected example-lane cases to normative vectors.** The 10
   gap-proof rejections measured over the real *Drosophila* chr4 fixtures are
   the candidate set. Promotion runs as a separate draft PR whose recorded
   expectations require independent review by a second reader — the derivation
   author cannot approve them — and nothing merges on this repository's agent
   lanes. The retired `T1–T3` id shape stays retired: promoted vectors keep
   kebab-case ids in this suite's existing style (`K`/`B` rule labels stay local
   to this repository, as the manifest's rule vocabulary records), and
   `selfChecksum`/`parentLink` semantics are unaffected (FHGM records keep no
   file identity of their own).
