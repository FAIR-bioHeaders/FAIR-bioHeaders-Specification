# Traceability: spec ↔ plan ↔ tasks

**Feature**: 011-jsonld-mapping | **Created**: 2026-10-10 | **Inputs**: [spec.md](../spec.md), [plan.md](../plan.md), [research.md](../research.md), [data-model.md](../data-model.md), [contracts/](../contracts/), [tasks.md](../tasks.md)

This is the result of an analyze-style consistency pass. Every functional requirement, success
criterion, acceptance scenario and edge case is traced to the design decisions and to the tasks
that implement (I) or test (T) it.

## Functional requirements

| Req | Summary | Design | Tasks (T = test, I = implement) |
|---|---|---|---|
| FR-001 | Publish a context mapping every FHR property, nested ones included, to an IRI | R-03, R-06, R-08, R-09; data-model §1–2; contracts/fhr.context.jsonld | T: T005, T028. I: T007, T008, T009, T010 |
| FR-002 | schema.org where an equivalent exists; otherwise FHR vocabulary terms, each with a label and a description | R-03, R-10; contracts/vocabulary.md | T: T006, T013. I: T007, T008, T009, T010, T017 |
| FR-003 | Machine-readable mapping table: JSON-LD term, DCMI term or none, kind, notes; reusable by #56 | R-02, R-15; data-model §4; contracts/mapping-table.schema.json | T: T028, T029. I: T002, T030, T031, T032 |
| FR-004 | JSON-LD round-trips to the identical record | R-12; data-model §8 | T: T012, T014, T015, T034. I: T016, T023, T024, T035 |
| FR-005 | Toolkit converts to and from JSON-LD alongside other formats, offline | R-11; contracts/cli.md | T: T004 (sockets blocked), T014, T015, T034. I: T003, T022–T025, T035, T036 |
| FR-006 | Typed resources for the record, taxon, people, software and identifiers, following Bioschemas | R-04; data-model §5 | T: T012, T013, T014. I: T007, T008, T016, T023 |
| FR-007 | The JSON-LD is the FHR record with its own keys plus `@context` (and optional `@type`) | R-06 rule 8, R-11; cli.md "Writing" | T: T005 (no `@vocab`, every key a term), T012, T014. I: T009, T016, T023 |
| FR-008 | FHR terms in the unversioned `https://w3id.org/fair-bioheaders/terms#`, registered with w3id | R-05, R-10; contracts/vocabulary.md | T: T005, T006. I: T007, T009, T038 (prepared; submission is a maintainer action) |
| FR-009 | Schema unchanged; `@context`/`@type` set aside before validation | R-11; cli.md "Canonical path"; rule J1 | T: T014, T019 (`jsonld-missing-checksum`), T020 (`--schema` strips). I: T023, T024. No task touches `fhr.json` (tasks.md Notes) |

## Success criteria

| SC | Summary | Design | Tasks |
|---|---|---|---|
| SC-001 | Every example and conformance metadata record converts to JSON-LD and back unchanged | R-12, R-14 | T012 (specification, 34 records), T014, T015 (toolkit), T027 (V3, V5) |
| SC-002 | 100% of FHR properties have a mapping entry with a DCMI column | R-03, R-15 | T028 (path set equals `fhr.json`, 45), T030 |
| SC-003 | Expanded JSON-LD uses only schema.org, Bioschemas-endorsed or documented FHR terms | R-03, R-14 | T013 (namespaces and schema.org domains, pinned v30.1), T006 (every `fhr:` term defined), T017, T027 (V4, V8 manual validator check) |
| SC-004 | #56 can start from the table without re-deriving any field meaning (maintainer confirms) | R-02, R-15 | T030, T031 ("Reusing this table"), T032 (confirmation requested). Confirmed by David Molik on spec#56, 2026-10-10 |

## Acceptance scenarios and edge cases

| Item | Tasks |
|---|---|
| US1-1: Conversion expands to linked data with typed taxon, people, software and identifiers, with IRIs where provided | T012, T013, T014, T016, T023 |
| US1-2: Converting back recovers the record exactly | T012, T014, T015, T024 |
| US1 independent test: a schema.org validator accepts an embedding page | T027 (V8, manual and recorded), T013 (offline domain proxy) |
| US2: Every field has a term, DCMI or "no DCMI equivalent", and a kind | T028, T030 |
| US3: FAIR-bioHeaders output and a reordered or differently compacted equivalent both convert to the same record | T019 (`jsonld-keys-reordered`), T033 (`jsonld-expanded`, `jsonld-schemaorg-vocab-compaction`, `jsonld-graph-single-node`), T034, T035 |
| Edge: fields with no schema.org equivalent (statistics, masking, checksum) | R-03 rows 27–38; T006 (FHR terms defined), T028 (`schemaorg_gap`) |
| Edge: values that are identifiers in some records and free text in others | R-06 rule 4 (they stay literals); T005 (only the five URI fields are coerced), T030 (conditions) |
| Edge: optional fields absent, so no empty or null nodes | cli.md step 4; T012, T014 |
| Edge: raw-main vs versioned schema URL (spec#44) | R-16; T019 (`jsonld-schema-versioned-url`) |
| Edge: third-party terms outside the mapping are reported, not silently dropped | R-07, rule J4; T033 (`jsonld-unknown-term`), T034, T035, T036 |

## Constitution obligations

| Obligation (plan.md) | Tasks |
|---|---|
| Specification I: annotations-only LinkML; `check_linkml.py` passes; generated artefacts drift-checked | T005, T007, T008, T009, T011, T041 |
| Specification III: every reading rule has a vector | T019 (J1, J2, J6, J7), T033 (J3–J5), T020 |
| Specification IV: conditions and losses stated; nothing fabricated | T028 (schema enforces `condition`/`loss`/`reason`), T030 |
| Toolkit I: byte-identical context and examples | T014, T021, T022 |
| Toolkit III: no fetch; ambiguity rejected | T004, T034, T035 |
| Toolkit IV: typed values preserved; no null/empty nodes | T012, T014 |
| Toolkit V: no new runtime dependency; tests first; installed wheel | T003, T015, T042 |

## Consistency findings

The pass found these points. Each one is resolved in the artefacts as noted.

1. **Two mapping-kind lists.**
   - The spec (US2) lists `exact, broader, narrower, related, unsupported`.
   - #56 lists `exact, conditional, narrower/broader, lossy, unsupported`.
   - *Resolved*: the union of seven kinds, with a defined direction (research R-02,
     mapping-table schema `$defs/kind`).
2. **The direction in `fhr_mappings.yml`.** Its `assemblyProtocol` → `sop` `relationship: narrow`
   means "FHR is narrower", which is `broader` in the new table and `broad_mappings` in LinkML.
   *Resolved*: documented, not changed, because `project_mixs.py` reads it (R-02, T031).
3. **FR-006 "identifiers" as typed resources.** `identifier[]` values are strings and cannot
   become nodes without changing FHR values (FR-007). *Resolved*: `accessionID` is a typed
   `PropertyValue`, and `identifier[]` stays CURIE text as Bioschemas recommends (R-04).
4. **US1's independent test names "a schema.org validator".** That validator is online only.
   *Resolved*: the offline domain and namespace test is the CI gate (T013), and the manual
   validator run is recorded on the PR (T027, V8).
5. **FR-005 "offline" and US3's arbitrary third-party JSON-LD.** A JSON-LD processor is needed.
   *Resolved*:
   - the general reader is an opt-in extra on Python 3.10+, with a bundled-only loader;
   - the MVP paths need nothing;
   - the limitation is justified in plan Complexity Tracking.
6. **Spec 004 FR-004** ("schemas are published at versioned, persistent URLs via w3id.org")
   against the 2026-10-09 raw-main decision (spec#44, website#15). *Resolved for this feature*:
   - the context is embedded, so no URL policy is needed;
   - raw-main stays canonical;
   - the existing w3id release alias addresses released copies (R-09).

   The underlying conflict is left to spec#44.
7. **The LinkML ids `https://w3id.org/fhr`, `https://w3id.org/fhr/core` and
   `https://w3id.org/fhr/mappings`** (`fhr_linkml.yml`, `schemas/core.yaml`, `fhr_mappings.yml`).
   These w3id paths are not registered: `https://w3id.org/fhr` returned 404 on 2026-10-10, and
   only `/fair-bioheaders/` exists. *Not changed*: `core.yaml` already calls its id
   "provisional pending the persistent schema URL decision". The new term namespace is under the
   registered `/fair-bioheaders/` space. This is flagged for spec#44.
8. **`default_prefix: ex` (`https://example.org/`)** in both LinkML files. Every slot URI was
   therefore an example.org IRI. *Resolved*: `default_prefix: fhr` (T007, T008). This has no
   validation effect (verified in the prototype).
9. **Open nested objects.** `taxon`, the authors, `accessionID` and `vitalStats` accept extra keys,
   and two conformance vectors use one. *Resolved*:
   - they are kept under J1;
   - the writer warns about them;
   - the general path reports them (R-07, T014, T034).

## Implementation status (T043, 2026-10-10)

Every FR, SC and acceptance item above has its tasks done:

- MVP (US1, US2): FAIR-bioHeaders-Specification#80 and #81, FAIR-bioHeaders-Tools#42 (issue Tools#35).
- US3 (the general reader): FAIR-bioHeaders-Specification#86, FAIR-bioHeaders-Tools#44.
- Maintainer decisions:
  - Pages publishing: FAIR-bioHeaders-Specification#83. The w3id rules were merged in perma-id/w3id.org#6860 (live 2026-10-12).
  - Decisions recorded in FAIR-bioHeaders-Specification#78; author typing and the Bioschemas export are in
    FAIR-bioHeaders-Specification#80 and FAIR-bioHeaders-Tools#42.
  - `nameType` on `release-v0.4`: FAIR-bioHeaders-Specification#85.
- V8 on validator.schema.org is recorded under T027. Root type terms were added for JSON-LD 1.0
  tools.

FR-008 is complete: perma-id/w3id.org#6860 is merged and the namespace resolves by content
negotiation.

SC-004 is confirmed: David Molik replied on spec#56 on 2026-10-10 that the mapping table is
correct for starting the export work ("This looks correct, yes"). No open items remain. His
2026-10-14 proposals for an enriched schema.org export are a new feature (013), not a gap in 011.
