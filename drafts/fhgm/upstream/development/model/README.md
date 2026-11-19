# Draft FHGM native model contract v0.1 (proposal)

Status: reviewed native draft contract v0.1 (proposal) under shared
[#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204)
review. The 2026-11-14 joint review took its positions in the
[review dispositions](../CONTRACT-REVIEW.md#review-dispositions-2026-11-14).
The maintainer accepted the packet on 2026-11-14 ("we can publish"); publication
itself is **not performed here** - no `schemaVersion`, no w3id schema URL and no
`schemas/versions.json` entry exists or is claimed for FHGM, and selection rule
V7 keeps the draft out of every release form until the shared publication PR
lands. Publication stays with the shared specification.

The record contract remains hand-authored JSON Schema through v0.x (maintainer
choice, reaffirmed 2026-11-19). LinkML migration is deferred. The model contract
is explicitly selected and versioned separately from the released FHGFF3 file
identity: no in-record schema field or FHGM header-registry row is added.
Concrete publication artifacts still require the shared publication review.

The [Round 14 decision record](../conformance/DECISIONS-2026-11-19.md) records
the selected D4–D6 semantics and the evidence interface implemented here.

## Record fields

One FHGM record describes one contributed gene model inside an annotation
file. File-scope fields (`schema`, `schemaVersion`, `annotation`, `taxon`,
`version`, `metadataAuthor`, `dateCreated`, `checksum` and the FHGFF3 genome
link) keep their released FHGFF3 1.1 meanings at file scope. Concept citations
name the [#204 requirement rows](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204);
they are draft rationales, not adopted semantics.

| Field | Requiredness | #204 concept | Draft rationale |
| --- | --- | --- | --- |
| `modelId` | Required, one opaque string | Model identity and scope | Unique within one annotation snapshot; stable across a revision of the same model on the same assembly. **File-local by default** (review disposition Q2, 2026-11-14): no minting authority is needed, and a producer-supplied external identifier may occupy this same opaque field. Who may mint external model IDs stays with curators. |
| `modelVersion` | Required, one opaque string | Model identity and scope | **Opaque by review disposition (Q3)**: equality/difference only. An immediate revision must use a value different from its predecessor; no ordering is implied or checked, so `9` may name a revision earlier than `2`. Ordering needs curator use cases the pilots did not supply. |
| `featureId` | Required, one opaque string | Model identity and scope | Exact decoded local GFF3 feature ID. v0.1 resolves one `gene` row; isoforms stay in the native `ID`/`Parent` graph; transcript-only scope awaits curator review (open question Q6). Resolution is a checker rule, not a schema constraint. |
| `reference` | Required; `genomeReference` (accession + supplied SeqCol digest) and/or `annotates` (FHR parent checksum) | Reference coordinates | Mirrors the FHGFF3 genome-link alternative so the record survives extraction from its file; requiredness is adopted as deviation D1. Checker rule 3 is stronger than "does not contradict": the record reference must **share at least one comparable form** with the file genome link **and** never contradict it. Never inferred; values are producer-supplied assertions. |
| `predecessor` | Optional; then `annotationChecksum` + `modelId` + `modelVersion` all required | New and revised models | The revision pointer proven necessary in the pilots: prior annotation snapshot checksum, model ID and version. Absent means no revision claim. Its `modelId` **must equal the record's own** `modelId` (deviation D2, adopted), which is what makes a rename impossible inside v0.x. Single-predecessor, same-assembly revision only; split, merge and assembly migration stay open. |
| `contributors` | Optional nonempty list of `{name, role, nameType?, uri?}` | Credit and publication | Supplied model contributors and roles; author objects mirror the shared FHGFF3 `Author`. File metadata authors stay in `metadataAuthor`; article authorship, journal review and curator acceptance stay outside the record. |
| `evidence` | Optional nonempty list of `{description, uri?}` | Evidence and methods | Supplied evidence assertions; `uri` takes an R14-accepted scheme (K2). An assertion is not a validation result; feature and biology checks belong to gff3-validator and reference matching to its own inputs. |
| `methods` | Optional object: `software[] {name, version?, uri?}`, `protocol` URI, `limitations[]` | Evidence and methods | URIs take an R14-accepted scheme (K2). Tools with versions, a curation protocol reference and supplied limitations or uncertainty. Software objects mirror the FHGFF3 `Software` role. |
| `publication` | Optional object: `article` DOI, `deposit` curie list | Credit and publication | Article and deposited model data keep separate, independently resolvable identities; assembly identity stays in `reference`. Patterns mirror the FHGFF3 `scholarlyArticle` and `identifier` fields. |
| `reuseConditions` | Optional string | Packaging and integrity | Reuse terms supplied for the record; never inferred from the article or file license. |

Nested objects are closed (`additionalProperties: false`), matching the base
header's rule that unknown keys are invalid everywhere except top-level `x-`
keys. Unknown optional values stay absent.

## Model-level constraints the base schema cannot enforce

The pilots (FHGM-Specification PRs #3/#4, summarized in the shared
`docs/FHGM.md`) showed the released FHGFF3 1.1 schema accepts a revision
pointer that names an unchanged neighbor model or a stale predecessor file:
those files pass schema and integrity checks unchanged. These rules therefore
live in the separate model-level checker below, not in any JSON Schema. Each
carries the stable id the [conformance manifest](../conformance/manifest.json)
cites; the two ids before them are the transport floor and the record shape the
checker enforces through the JSON Schema files.

- **K1 — transport.** A file the checker accepts keeps a released FHGFF3
  identity — the `v0.5.0` citation with `schemaVersion` `"1.1"` or the `v0.6.0`
  citation with `schemaVersion` `"1.2"` or `"1.1"` (maintainer dual-base
  decision of 2026-11-15; FORMAT.md R15 admits extension fields from `"1.1"`,
  the v0.6.0 release accepts `"1.1"` records, and a citation and stated version
  that contradict each other are rejected; either citation may use the w3id
  URL or the raw tag URL under either repository name) — and carries one or more records under the single top-level
  `x-fhgm-models` key. A file stating FHGFF3 `1.0` cannot carry the extension
  at all: the base schema rejects it on either release, from byte-identical
  clause text.
- **K2 — record shape.** Each record validates against
  `fhgm-model.schema.json`, whose required set is `modelId`, `modelVersion`,
  `featureId` and `reference` (deviation D1: `reference` stays required, so an
  extracted record keeps its own assembly binding). Opaque text values
  (identifiers, versions, names, roles, descriptions, `reuseConditions`,
  `assemblyName`) are non-empty, have no leading or trailing whitespace and no
  control, zero-width or bidirectional formatting character anywhere; `deposit`
  identifiers are `prefix:local` with a non-blank local part. The link fields
  (`evidence[].uri`, `methods.software[].uri`, `methods.protocol`) must be URIs
  with a scheme the shared FORMAT.md R14 accepts — `http`, `https` or `ftp` with
  a host, or a `urn:`, `doi:` or `info:` identifier — so `javascript:`, `data:`,
  `file:` and the like are rejected rather than only warned about as in the
  released header types.
- **K3** (rule 1 in the draft) — `modelId` is unique within one snapshot,
  compared after Unicode NFC normalisation so canonically equivalent spellings
  collide; a collision makes the identity `ambiguous` and rejects the snapshot
  (deviation D4). K3 runs after K2 and before every per-record rule, so a
  duplicate is reported as `ambiguous` even when a colliding record is also
  wrong in some other way.
- **K4** (rule 2) — `featureId` resolves to exactly one local **root** gene
  row: a row of type `gene` or `SO:0000704` with no `Parent` attribute.
  Matching rules, all pinned by vectors:
  - only the percent-decoded ID is compared: `ID=toy%2Da` is `toy-a`, and a
    record naming the raw spelling `toy%2Da` does not resolve;
  - attribute tags are case-sensitive, without trimming: `id` is not `ID`.
    Whitespace-disguised `ID`/`Parent` tags and malformed or duplicate ID
    attributes make the local inventory untrustworthy; K4 stays not-run with
    a reason. They cannot establish a root by being silently ignored;
  - exactly one row may carry the ID. Multiple rows sharing one ID and other
    gene-like types (`ncRNA_gene`, `pseudogene`, …) are outside the initial
    FHGM model scope. This is not a claim of generic GFF3 invalidity;
  - `Parent` must be absent: bare `Parent` and `Parent=` cannot establish a
    root. GFF3 syntax and feature-graph/biological correctness remain owned by
    `gff3-validator`;
  - a trustworthy complete inventory with zero matching rows rejects K4,
    including a known empty inventory. Missing or untrustworthy inventory
    leaves K4 not-run with a reason and cannot earn a full model pass.
- **K5** (rule 3) — a record `reference` shares at least one comparable form with
  the file genome link and never contradicts it. Both halves are enforced: an
  accession-plus-digest file and an FHR-checksum record reject each other even
  though neither contradicts the other.
- **K6** (rule 4) — a predecessor pointer resolves against **explicitly supplied**
  prior snapshots only (deviation D3): the successor's assembly link and record
  reference must match the predecessor's, the versions must differ, the pointer
  must name its own `modelId` (deviation D2), and when the supplied set contains
  a recorded successor of the pointed record the pointer must name that successor
  rather than skip it (version-gap misuse). Relevant prerequisites of every
  supplied snapshot are evaluated, including its complete feature inventory.
  A failed or unavailable prerequisite prevents a full selected-file model
  pass. Its own predecessor claim is not transitively resolved.

### Permitted identity cases (maintainer decision 2026-11-19)

The initial model contract permits the following. Each has a conformance case;
none establishes curator acceptance or a globally unique model identity.

- Two records with different `modelId`s targeting the same gene row in one
  snapshot.
- A revision whose `featureId` differs from its resolved predecessor's: K6
  compares model ID, version, assembly link and record reference, not the
  target.
- A version that returns to an earlier value (`"1"` → `"2"` → `"1"`): versions
  are opaque and only the immediate predecessor is compared (disposition Q3),
  so `(modelId, modelVersion)` need not identify one record across a chain.

Base selection is part of the checker: `base-schemas.json` registers the released
FHGFF3 bytes the checker accepts (v0.5.0 and v0.6.0, each resolved from its tag to
its commit) together with the `schema` URLs that cite each release (w3id with and
without the trailing slash, and the raw tag URL under both repository names). The
carrier's cited `schema` URL chooses which registered bytes validate it;
`schemaVersion` plays no part in the choice and is judged by the cited release's
own enum. A citation no registered release answers to (a superseded release such
as v0.4.0, or raw main), a missing citation, and a citation whose release bytes
were not supplied with `--base-schema` are refused with a selection error, never
evaluated against other bytes. The selected release is printed for every loaded
file, so no verdict is silent about the bytes that produced it. This is selection, not
substitution: the sealed conformance vectors keep their 1.1 bytes and their
evidence trail, and the matrix lane re-observes 1.2 twins separately.

The manifest adds one more id, **B1**, for the boundary these rules sit on: a file
must already satisfy the released FHGFF3 base schema and its exact-byte checksum
before any FHGM verdict exists. Model checks add to those guarantees and never
replace them, so a rejection reported under B1 (the 1.0-transport vector and a
checksum-tampered file) is not evidence of a model-level gap. Everything the
checker reports under K3–K6 is.

## Transport: FHGFF3-embedded records (normative draft wording)

This section is draft normative text for the adopted Option C transport; it
grants nothing and changes no released contract.

- An FHGM-carrying file **must** be a valid FHGFF3 file of an admitted identity
  — the released `v0.5.0` citation with `schemaVersion` `"1.1"` or the released
  `v0.6.0` citation with `schemaVersion` `"1.2"` or `"1.1"`, per the
  maintainer dual-base decision of 2026-11-15 — and **must** keep that released FHGFF3 `schema` URI
  and `schemaVersion` together, unaltered. FHGM adds no
  file-type identity at v0.1; selection happens by explicitly running the
  model-level checker, per the recorded decision. Review disposition Q4 keeps
  that as the only expression of model-contract identity until publication: the
  draft adds no in-record version marker and no contract URI, and both stay
  additive later. The record carries no `schema` field, so the selection rules
  do not reach it; draft-stage recognition runs through the V7 lane at the
  contract/validator level, and publication mints the contract's own identifier.
- Model records **must** be carried under the single top-level extension key
  `x-fhgm-models` as a sequence of one or more objects, per
  [FORMAT.md R15](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FORMAT.md)
  (extension fields exist from FHGFF3 `schemaVersion` `"1.1"`). Repeatable
  records ride the array; each record **must** satisfy the native contract
  above.
- The extension **never** overrides a standard field (R15). The file checksum
  **covers** the record bytes like every other header byte (R3): editing any
  record changes the file checksum, and the checksum covers the records — not
  any external model registry.
- The base schema validates the **transport only**: header structure, the
  genome link and the presence of the array. Model meaning — targets,
  identity, pointers — is validated exclusively by the separate draft checker
  (`validate_fhgm.py`). A file that passes base schema, checksum and transport
  has **not** passed FHGM validation.
- Pointer resolution is reported per the verdicts below and resolution **never**
  asserts curator acceptance of a revision; acceptance is a separate decision
  with its own evidence, recorded outside the header check.
- The draft states **no** semantics for split, merge, assembly migration,
  transcript-only scope or companion-file identity (open question Q6, left to
  curators). A file that needs one of those is outside v0.1 rather than invalid
  under it: the checker reports only what it checks, and the [conformance
  manifest](../conformance/manifest.json) records the list as open scope with no
  vectors.

### Checker verdicts

Two levels, three names. Deviation D4 keeps all three names in the interface;
the review of 2026-11-14 records which level each appears at, because the draft
README previously implied that `ambiguous` was reachable per pointer.

Snapshot level, while loading the selected file or any supplied prior snapshot
(rules K2–K5):

- `ambiguous` — multiple records share one `modelId`, so the identity a pointer
  needs cannot select a record. Ambiguity is a defect of that snapshot, so
  loading it rejects the run; this includes a *supplied prior* that is itself
  ambiguous. No pointer verdict is reported for such a run.
- any other snapshot defect — a record contract violation, an unresolved feature
  target, a reference that conflicts with the file link, a transport or base
  schema failure, a checksum mismatch — aborts the run with that reason.

Pointer level, after every loaded snapshot passed the checks above:

- `resolvable` — exactly one prior record matches the pointer identity, on a
  matching assembly, with a changed version and no skipped recorded successor.
- `unresolvable` — zero matches: the snapshot is absent or is the current
  file, the pointer names another model ID, the prior record or its recorded
  version differs, the version is reused, the assembly links conflict or share
  no comparable form, or a recorded successor of the pointed record was skipped.

For each record with a `predecessor`, the checker resolves against the
explicitly supplied prior snapshots. **Each supplied snapshot must itself pass
the snapshot-level checks above; its own `predecessor` claim is not resolved** —
that is the bound deviation D3 describes, and it is why a snapshot with an
unverifiable or skipped intermediate link can still serve as history here. The 2026-11-19 decision preserves this bounded behavior: no external history
lookup or transitive history service is inferred.

v0.1 accepts only `resolvable`; `unresolvable` and `ambiguous` exit non-zero
with the reason, and the reason text is a stable part of the interface — the
manifest cites the exact substring each vector must produce. Even a `resolvable`
verdict states only that the pointer identifies its predecessor record.

## Running the draft checker

Use Python with `fair-bioheaders` (the checker reuses its GFF3 header reader
and checksum implementation) and `jsonschema`. From the FHGM repository root,
with the released base schemas registered in `base-schemas.json` — the sealed
fixtures cite the v0.5.0 release and need its bytes; passing both releases lets
the checker select per loaded file, by the release that file cites:

```sh
git -C /path/to/FAIR-bioHeaders-Specification show v0.5.0:fhgff3.json > /tmp/fhgff3-v0.5.0.json
git -C /path/to/FAIR-bioHeaders-Specification show v0.6.0:fhgff3.json > /tmp/fhgff3-v0.6.0.json
python development/model/validate_fhgm.py --base-schema /tmp/fhgff3-v0.5.0.json \
  --base-schema /tmp/fhgff3-v0.6.0.json \
  --predecessor development/examples/contract/minimal.fhgff3.gff3 \
  development/examples/contract/rich.fhgff3.gff3
python development/model/check_draft.py /tmp/fhgff3-v0.5.0.json /tmp/fhgff3-v0.6.0.json
```

`check_draft.py` is the draft self-test: it regenerates
[`../examples/model/`](../examples/model/README.md) byte-for-byte, runs every
acceptance and rejection fixture against the checker, and re-proves that the
base schema alone accepts the model-invalid files. The manifest-driven
[conformance suite](../conformance/README.md) is the vector census and the CI
lane; `--matrix` additionally evaluates the FHGFF3 1.2 twins recorded in
`base_matrix.json`:

```sh
python3 development/conformance/run_conformance.py --base-schema /tmp/fhgff3-v0.5.0.json
python3 development/conformance/run_conformance.py \
  --base-schema /tmp/fhgff3-v0.5.0.json --base-schema /tmp/fhgff3-v0.6.0.json --matrix
python3 development/conformance/run_conformance.py --offline   # bytes and digests only
```

Run `gff3-validate --no-header` separately for GFF3 syntax and feature-graph
checks — the conformance runner does that when the tool is supplied and reports
the lane as skipped otherwise — and remember that reference sequence matching and
biological evidence assessment require their own inputs. See the
[INSDC supplement](../INSDC-COVERAGE.md) for the coverage boundary:
the experimental records add no coverage to any released contract.
