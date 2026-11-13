# Mapping v1 adoption decision packet (#56)

**What this packet is:** a consolidated decision aid for the joint-maintainer
review of the **#56 mapping v1 surface** — the artifact set merged as PR #143
that the recorded [2026-11-12 scope-down decision](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204#issuecomment-6829197859)
designated as the deliverable of this issue ("root-field inventory +
supplemental export-context schema/checker + curated DCMI fixture become
mapping v1"). It states the v1 surface file-by-file as merged, gives one
adoption row per artifact with the consequences of each choice, lists the open
semantic questions with marked-reversible recommended positions, enumerates
what the scope-down defers to the per-target follow-up issue (with a ready-to-
file skeleton), and attaches a link-verification appendix re-checked on
2026-11-13 so adoption does not ratify rot.

**What this packet is not:** it is not an adoption, a release, a publication,
or a status change. Nothing here adopts anything — adoption is a joint
maintainer decision recorded on
[#56](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/56).
It grants no "official" label, opens no w3id alias, ships no exporter, and
does not unblock [website #29](https://github.com/FAIR-bioHeaders/fair-bioheaders.github.io/issues/29)
by itself. Every "recommendation" in this packet is a recommendation only.
A proposal's existence ≠ adoption; that standing rule is unchanged.

Prepared 2026-11-13 against shared `main` at `e15e1d0`. The v1 surface itself
was merged on 2026-10-22 (PR #143, head `392cb4c`; audit record names merge
commit `1327573`).

---

## 1. The v1 surface as merged (file-by-file)

PR #143 ("Start draft metadata mapping profiles and assembly export context",
merged 2026-10-22T12:12Z) touched 15 files: 11 added, 4 modified (pointer-only
edits to `AGENTS.md`, `CHANGELOG.md`, `README.md`, `docs/MAPPINGS.md`). The
core artifacts and what each one asserts:

| Artifact | What it is | What it asserts (and does not) |
| --- | --- | --- |
| [`docs/mappings/README.md`](README.md) | Profile prose, resource-model statement, delivery narrative, FHT/FHP/FHGFF3 scope table, remaining-work list. | Asserts: a four-subject resource model (assembly / metadata record / describing publication / specification-software), profile version `0.1.0-draft.1`, qualified DCMI Terms 2020-01-20 as the descriptive target, "no new exporter". Explicitly *not* adopted; states that "official" would mean maintainer-approved only. |
| [`mappings/proposals/assembly-dcmi.yml`](../../mappings/proposals/assembly-dcmi.yml) | Machine-readable handling inventory, 28 entries. | Asserts: **all 24 released FHR v0.4.0 (schemaVersion "2.0") root fields are covered** — verified by set comparison against `fhr.json` on 2026-11-13 — as 9 `conditional` and 15 `unsupported`, each with subject (`25 resource` / `3 metadata-record`), container cardinality, condition, transformation, and loss/limitation. Plus **4 context-supplied entries** (`/title`, `/publisher`, `/publicationDate`, `/resourceIRI`) that use a *different shape* — singular `term:`, no `kind:` — because they are export-context keys, not FHR root fields. Asserts handling rules only; not executable mappings, not SKOS equivalences. |
| [`mappings/proposals/assembly-export-context.schema.json`](../../mappings/proposals/assembly-export-context.schema.json) | Proposed supplemental export-context JSON Schema (draft 2020-12), separate from `fhr.json`. | Asserts: required `profileVersion` (`const "0.1.0-draft.1"`), `resourceKind: assembly`, distinct `resourceIRI`/`metadataRecordIRI`, explicit `title`; optional `publisher`, `publicationDate`, `publicationYear`, `resourceDOI`; closed object. Its `$id` is a **raw-main URL**. Does not add any field to FHR and claims no registration readiness. |
| [`scripts/check_mapping_context.py`](../../scripts/check_mapping_context.py) | Offline checker for the context schema plus semantic conflict rules. | Asserts: duplicate-key rejection, fixed source identity (FHR v0.4.0 / "2.0"), equal record/resource IRI rejection, publication date/year conflict rejection, and article-DOI-reuse rejection — including DOI resolver forms (`doi.org`, `dx.doi.org`, case-insensitive, percent-encoded) inside `resourceIRI` even when `resourceDOI` is absent (the fix from the Copilot review, commit `8dfb09a`). No network, no source-record validation, no registration check. |
| [`mappings/proposals/profile-status.yml`](../../mappings/proposals/profile-status.yml) | Machine-readable delivery matrix. | Asserts per-target status: `dcmi-qualified` = `draft-fixture`; DataCite 4.7, Crossref 5.5.0, ARK (draft-kunze-ark 2026-05-08), BibTeX, BibLaTeX = `planned`; per-header-type: FHR = `draft-fixture`, FHP/FHGFF3 = `not-yet-profiled`, FHT = `blocked` on FHT-Spec #6/#7. Candidate versions are review references, not adapter claims. |
| [`tests/fixtures/mapping-proposal/`](../../tests/fixtures/mapping-proposal/) (5 files) | The worked bundle: `source.json` (byte-for-byte copy of `examples/example.fhr.json` at `2da7c96`), `context.json`, `qualified-dc.ttl`, `report.json`, `README.md`. | Asserts: one manually curated qualified-DC Turtle graph — two subjects (assembly gets title/creator/publisher/created/issued/subject/relation/rights; the metadata record gets `dcterms:subject` → assembly, `dcterms:conformsTo` → the cited schema IRI, and the metadata creators), and a report declaring 15 unprojected root fields, five limitations, and `registration_readiness: not-assessed`. The TTL is *not generated by a shipped exporter*; checksums are placeholders; `example.org` URIs are illustrative. |
| [`tests/test_mapping_proposal.py`](../../tests/test_mapping_proposal.py) | 14 test methods binding the above together. | Asserts: source validity against the released schema, context checker behavior (including the resolver-form regressions), and the graph's subject separation, dates, identifiers, relation direction, rights typing and declared omissions. |

Not re-created here, and separate contracts that v1 explicitly does **not**
absorb: the canonical JSON-LD/DCMI table
([`mappings/fhr-jsonld-dcmi.yml`](../../mappings/fhr-jsonld-dcmi.yml), feature
011, all 45 property paths), the one-way schema.org export
([`docs/SCHEMAORG-EXPORT.md`](../SCHEMAORG-EXPORT.md), feature 013), and the
MIxS projection ([`docs/MAPPINGS.md`](../MAPPINGS.md)). `docs/mappings/README.md`
records one known inconsistency against them: the older canonical table uses a
numeric source-schema version format ("legacy version metadata") while v1 names
released FHR schemaVersion `"2.0"`; the proposal does not reinterpret the old
format and defers that migration to its own review.

## 2. Adoption decision sheet

One row per artifact. "Adopt as normative" means the joint review approves the
artifact as maintained FAIR-bioHeaders guidance under a version label; "keep
proposal-grade" means it stays review input with its current disclaimers;
"drop" means removal or supersession. Consequences are spelled out for the
three questions the review must answer alongside each row: **W** = what website
#29 may then publish, **U** = what the TERMS/context URIs must become,
**R** = release-cycle effect.

| # | Artifact | Options | Consequences of adopting as normative | Recommended disposition (recommendation only) |
| --- | --- | --- | --- | --- |
| 1 | Resource model (four distinct subjects) in `docs/mappings/README.md` | adopt / keep / adopt-with-edit | **W:** #29 may publish the resource model as official guidance ("which identity goes where"). **U:** unchanged — the model uses DCMI IRIs and the released schema IRI, both already stable. **R:** documentation-only; no schema bytes. | **Adopt as normative.** It is the load-bearing semantics for every other row; nothing in it constrains released contracts. Reversible: a later structured-voucher (#139) or per-target decision can narrow it. |
| 2 | `assembly-dcmi.yml` — the 9 `conditional` root-field rules | adopt / keep / drop rule-by-rule | **W:** #29 publishes them as the official FHR→qualified-DC handling table with the recorded conditions and losses. **U:** requires the inventory to name the *fixed* DCMI version (it already pins 2020-01-20) and the cited contract IRI `https://w3id.org/fair-bioheaders/fhr/v0.4.0` (verified live 2026-11-13). **R:** enters a **documentation/mapping release cycle** (see row 3 note); does not touch header schemas. | **Adopt as normative.** The 4 context entries (`/title`, `/publisher`, `/publicationDate`, `/resourceIRI`) already occupy a separate `context_entries:` block with their own shape, checked separately by the existing tests. |
| 3 | `assembly-dcmi.yml` — the 15 `unsupported` root-field rulings | adopt as "final" / adopt as "v1-surface only" / keep open | **W:** #29 can list them as "not projected by the official descriptive profile" but *not* as "unmappable". **U:** none. **R:** none. | **Adopt as "`unsupported` in the v1 descriptive surface", not permanently.** The report.json field name (`source_root_fields_not_projected`) already says this; a blanket final ruling would contradict the nested/per-target work the scope-down defers. Reversible per target by the follow-up issue. |
| 4 | `assembly-export-context.schema.json` + `check_mapping_context.py` | adopt as normative (versioned doc contract) / keep proposal-grade / drop | **W:** #29 publishes the context schema and checker semantics as the official way to supply title/publisher/publication facts. **U:** the `$id` **must change** — a normative artifact cannot be identified by a mutable raw-main URL; options are a raw **tag** URL (`…/vX.Y.Z/mappings/proposals/assembly-export-context.schema.json`) or, later, a w3id path (a w3id edit is a maintainer action through perma-id, not part of review). `profileVersion` is `const "0.1.0-draft.1"`, so adoption requires a version bump (e.g. `1.0.0`) in schema + checker + fixtures together. **R:** decision needed whether mapping-profile contracts get their own versioning line (suggested: `profile_version`, changelog entry, tagged URLs) **without** entering `schemas/versions.json` — it is not a header contract and registering it there would misuse the released-contract registry. | **Adopt with the `$id`/version remediations.** Keeping it proposal-grade leaves #29 with nothing deposit-free to publish beyond prose. |
| 5 | `qualified-dc.ttl` + `source.json` + `context.json` + `report.json` bundle | adopt as the normative worked example / keep illustrative / promote to conformance vector | **W:** #29 embeds the bundle as *the* official worked example (source → context → graph → loss report). **U:** the graph's term IRIs are names, not documents; adoption does not depend on purl dereferenceability (see §5 rot note). **R:** if promoted into `conformance/`, the bundle becomes release-gated: every future FHR schema change must regenerate or re-justify it. There is currently **no conformance lane for mapping fixtures** (`conformance/manifest.json` covers header vectors), so promotion is a small new-lane decision, not a copy step. | **Adopt as the normative worked example now; conformance promotion as a separate follow-up** once an exporter exists (a vector must be checkable against something deterministic). |
| 6 | `profile-status.yml` delivery matrix | adopt as living tracker / keep / fold into the follow-up issue | **W:** #29 must **not** publish `planned` rows as available; adoption of v1 makes only `dcmi-qualified` + FHR rows publishable. **U:** none. **R:** none. | **Keep as living tracker, re-point `planned` rows to the follow-up issue** (skeleton in §4) so the matrix and the issue set cannot diverge. |
| 7 | `tests/test_mapping_proposal.py` | keep as-is | Tests are the executable definition of rows 2–5; whatever wording is adopted must keep them green (they pin `0.1.0-draft.1`, the checker behaviors, and the graph). | **Keep; update in lockstep with any adopted version bump.** Note for the record: the PR body said "11 new tests", the 2026-10-22 audit comment said "13 mapping tests"; the file on `main` has **14** test methods today. Harmless drift from the post-review fix commits, but adoption minutes should cite the file, not a remembered count. |
| 8 | The "official" label itself | grant on v1 adoption / withhold until an exporter ships | **W:** #29's gating check — website #29 is blocked "until v1 adoption", so the label decides whether the page says "maintainer-approved mapping guidance (no shipped exporter yet)" or stays unpublished. **R:** grant means a CHANGELOG entry and a named profile version; it is not a repository release tag unless maintainers choose to cut one. | **Grant the label to exactly rows 1–5 + 7 as adopted, with an explicit "no deterministic exporter shipped yet" rider.** The issue body already separates descriptive export from deposit readiness; the label should say so. |

## 3. Open semantics — recommended positions (each reversible)

The specific ambiguities the review must land, with a recommended position.
Every position is marked **reversible**: each can be reopened by the follow-up
issue or a later profile cycle without invalidating released contracts, because
none of them changes header bytes.

1. **Resource-vs-context subjects.** Which DCMI triples may the context supply?
   Context currently supplies `title`, `publisher`, `issued` (publication date)
   and `identifier` (resource IRI); source supplies `created` (assembly
   creation) and both creator sets. *Recommendation:* adopt the fixture's
   split as the rule — context never supplies `created`, source never supplies
   `issued`; equality of resource and metadata-record IRIs stays a hard error.
   Reversible by adding context keys (an additive profile version).
2. **Date conflicts.** The checker rejects `publicationDate`/`publicationYear`
   disagreement; the fixture deliberately uses 2022 creation vs 2026 issuance to
   prove no defaulting. *Recommendation:* adopt "no date is ever derived from
   another date" as normative wording, matching the issue-body table row for
   `dateCreated`.
3. **Unmapped-field reporting.** Four distinct states — absent, empty,
   unsupported, conflict — must not collapse (issue body: "For every field,
   distinguish…"). *Recommendation:* adopt the four-state vocabulary now, at
   the descriptive-profile level, with `report.json`'s shape
   (`source_root_fields_not_projected`, `not_supplied_context`,
   `conflict_policy`) as the draft report format; require future adapters to
   emit the same categories. Do not require per-item cardinality reporting yet
   (root cardinality measures container presence — say so explicitly in the
   adopted text).
4. **`genome` is not a title.** Already an `unsupported` ruling with a context
   remedy. *Recommendation:* adopt as normative; it is the strongest single
   anti-fabrication rule in the set.
5. **`scholarlyArticle` relation typing.** The curated graph emits generic
   `dcterms:relation`, while the issue body allows "is described by" only when
   established. *Recommendation:* keep generic `relation` in v1; a typed
   relation needs a context assertion (e.g. `articleDescribesResource: true`),
   which is exactly the kind of additive key a later minor profile version
   carries. Reversible and cheap.
6. **Rights handling.** Free-text `reuseConditions` → `dcterms:RightsStatement`
   label, never an inferred license URI. *Recommendation:* adopt as normative;
   conservative license detection can only ever be a narrowing change.
7. **Taxon subjects.** Supplied taxonomy IRI as `dcterms:subject` without
   resolution; no invented subject schemes. *Recommendation:* adopt as
   normative. (The fixture's `https://identifiers.org/taxonomy:9606` redirect
   was verified live 2026-11-13; adoption still treats IRIs as names.)
8. **Identifier scope.** `accessionID.name` may name a repository — never
   yields an accession; `checksum` and `seqcol_id` are not bibliographic
   identifiers; every `identifier` string is not a DOI. *Recommendation:*
   adopt the inventory's three `unsupported` rulings plus the checker's
   DOI-resolver-form rejection as the normative anti-confusion set.
9. **Metadata-record conformance assertion.** `dcterms:conformsTo` applies only
   to the metadata-record subject, with the cited fixed schema IRI;
   `schemaVersion` itself stays unpromoted (`unsupported` entry).
   *Recommendation:* adopt as normative — it is the only sanctioned place where
   the FHR contract appears in DC, and it scopes the claim to the record.
10. **Canonical-table divergence.** The v1 profile names `"2.0"` while
    `mappings/fhr-jsonld-dcmi.yml` uses a numeric legacy source-schema format
    and declares its own DCMI equivalences (6 exact / 2 broader / 11
    conditional across 19 of 45 paths). *Recommendation:* v1 adoption should
    record that the two tables are **separate contracts with separate version
    metadata** and schedule reconciliation — not merge them; silently merging
    would relabel conditional prose as unconditional equivalence, which the
    issue body forbids.

## 4. Explicitly deferred to the per-target follow-up (scope-down of 2026-11-12)

Per the recorded decision, everything below left this issue's deliverable set
and moves to a community-contributable follow-up worked one target at a time:

- Deep per-target crosswalks and deterministic adapters for **DataCite 4.7**
  (XSD pin, XML vs REST envelopes, deposit-ready validation), **Crossref
  5.5.0** (database/dataset record structure, container/registration context),
  **ARK** (binding/resolver/persistence policy, optional ERC), **EZID** (ANVL
  `erc`/`datacite`/`dc`/`crossref` profiles, `_target`/`_profile`/`_status`
  handling, test-shoulder fixtures — added to scope 2026-10-22 by request),
  classic **BibTeX** `@misc` and **BibLaTeX** `@dataset` (style/tool matrix),
  and the optional metadata-bearing `note` envelope (an experiment until
  round-trip evidence exists).
- **Nested-field handling for all targets** (v1 covers root fields only; nested
  detail stays in the preserved source and the canonical table).
- Deposit-ready profiles that *fail clearly* on missing registration context;
  export-vs-import separation and any reverse mappings; Simple DC
  compatibility views; FHP/FHGFF3 type-specific profiles; **FHT** (blocked on
  FHT-Spec #7's adopted contract, not the closed #6).
- The full issue-body acceptance-criteria checklist items that reference those
  targets (BibTeX rendering matrices, EZID ANVL escaping tests, XSD-validated
  deposit XML, etc.).

What stays in #56 is exactly §1–§3 of this packet: review and adopt the v1
surface, record the label, then close the issue with the follow-up filed.

### Draft skeleton for the follow-up issue (ready to file)

```text
Title: Per-target metadata mapping crosswalks and adapters (follow-up to #56 mapping v1)

Labels/links: Relates #56 (v1 adopted surface), #55 (family), website #29.
MPL-2.0; one target at a time; community-contributable.

## Basis
Adopted mapping v1 (per #56 adoption record <LINK>): four-subject resource
model, root-field handling inventory, assembly export context + checker,
qualified-DC worked bundle. This issue extends that surface per target.
Nothing here changes released FH* contracts; existence of a slice ≠ adoption;
no minting, registration or network calls in fixtures.

## Ground rules per target slice
- Pin the exact target version (XSD/schema/spec URL + retrieval date).
- Root AND nested field handling; four-state reporting (absent/empty/
  unsupported/conflict) in the report.json category shape.
- Descriptive export ≠ deposit-ready; deposit slices must fail with a named
  missing-context list; registration readiness is never asserted by export.
- Fixtures: source/context/output triplets from valid FHR examples, negative
  cases, special characters; offline validation only; test shoulders where
  the target defines them.
- Delivery: a PR adding mappings/proposals/<target>.* + fixtures + tests;
  update mappings/proposals/profile-status.yml status in the same PR.

## Target checklist (one contributor, one slice, one review each)
- [ ] DataCite 4.7 — XSD pin; XML vs REST envelopes; deposit-ready failures;
      missing-DOI refusal example.
- [ ] Crossref 5.5.0 — database/dataset deposit XML vs REST retrieval;
      container metadata inheritance; paper-reference example.
- [ ] ARK — assigned-identifier handling, resolver policy, metadata binding,
      optional ERC serialization; persistence language; no minting.
- [ ] EZID — ANVL erc/datacite/dc/crossref profiles; internal elements;
      escaping; ark:/99999/fk4… + doi:10.5072/FK2… shoulders only.
- [ ] BibTeX (classic @misc) — citation-only first; escaping/Unicode/
      corporate names; rendering matrix with pinned tool versions.
- [ ] BibLaTeX (@dataset) — separate profile; backend/style selection.
- [ ] Metadata-bearing note envelope — experiment gate: extraction and
      round-trip evidence in a named tool matrix before any support claim.
- [ ] FHP / FHGFF3 root-field profiles after v1 wording proves portable;
      FHT only after its contract is adopted (FHT-Spec #7).
```

## 5. Verification appendix — link targets re-checked 2026-11-13

Method: `curl -sL` (follow redirects), full results in the session record.
Checked: every external target used by the v1 surface (the two DCMI namespace
prefixes and the property/type IRIs that appear in `qualified-dc.ttl` and
`assembly-dcmi.yml`, the pinned DCMI 2020-01-20 version page, the schema
references in `profile-status.yml`, the fixture's identifiers.org taxon IRI,
and `https://w3id.org/fair-bioheaders/fhr/v0.4.0`).

| Target | Result 2026-11-13 |
| --- | --- |
| `https://w3id.org/fair-bioheaders/fhr/v0.4.0` (cited in the inventory and graph) | **200** → raw tag `…/v0.4.0/fhr.json`. Healthy. |
| DCMI 2020-01-20 versioned page (pinned in inventory/matrix) | **200**. Healthy. |
| `http://purl.org/dc/terms/` and `/title`, `http://purl.org/dc/dcmitype/Text` | **200** → dublincore.org spec page. |
| `http://purl.org/dc/terms/conformsTo`, `/subject`, `http://purl.org/dc/dcmitype/Dataset` | **503** (redirect chain lands on `purl.archive.org`, which is erroring at check time). **Rot found — see below.** |
| `https://identifiers.org/taxonomy:9606` (fixture subject) | **200** → NCBI Taxonomy redirect. |
| DataCite 4.7 / Crossref 5.5.0 pages / dataset guide / references guide | **200** each. |
| ARK `draft-kunze-ark` (matrix candidate) | **200**; the I-D itself carries "Expires 26 April 2027" — the matrix's "work in progress" caveat is correct and must survive into any ARK slice. |
| EZID apidoc + home, BibTeX docs, BibLaTeX (ctan + mirrors.ctan PDF), micropub collection, `https://doi.org/10.22002/*` fixtures' DOIs | **200** each. |

**Findings that bear on adoption:**

1. **purl.org DCMI term dereferencing is intermittently failing (503 at
   purl.archive.org).** This is why the packet recommends (row 2, semantics #7)
   that adoption language treat the term IRIs as **names pinned to the
   2020-01-20 versioned specification page**, never as living documents, and
   that website #29 not advertise dereference demos. The v1 fixture checks are
   offline against the repository's pinned DCMI term inventory and remain
   green; adoption does not inherit this outage, but publishing "these URLs
   resolve" would have rotted within a day.
2. **The persistent vocabulary alias is now live.** `https://w3id.org/fair-bioheaders/terms`
   resolves (→ the generated terms page on fhref.org); perma-id PR #6860 merged
   2026-10-11. This postdates parts of the issue discussion (2026-10-10 said
   "pending") and changes consequence **U** in rows 4: if any v1 artifact needs
   a persistent self-identifier beyond the schema IRI, the terms namespace now
   exists; the export-context `$id` raw-main URL remains the one identifier in
   the v1 surface that violates stability expectations and should be retagged
   on adoption.
3. No rot found in any reference that v1 *asserts conformance against*; the
   failing dereferences are namespace-alias lookups only.

*End of packet. Prepared for review on #56; grants nothing.*
