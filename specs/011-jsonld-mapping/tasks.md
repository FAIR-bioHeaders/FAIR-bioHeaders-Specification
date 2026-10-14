---

description: "Task list for feature 011: JSON-LD mapping and serialisation"
---

# Tasks: JSON-LD mapping and serialisation for FAIR-bioHeaders metadata

**Input**: Design documents from `/specs/011-jsonld-mapping/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: These are required.
- The toolkit constitution V says "Every behaviour change ships with regression tests".
- The FAIR-bioHeaders-Specification constitution III says "every parsing rule needs a conformance example".
- Every success criterion (SC-001 to SC-003) has an automated check (research R-14).

In every story the test tasks come first, and they must FAIL before the implementation tasks
start.

**Organization**: Tasks are grouped by user story, so each story can be implemented and tested
on its own. The FR/SC trace is in [checklists/traceability.md](checklists/traceability.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

The work spans two repositories, and every path starts with its repository name:

- **`FAIR-bioHeaders-Specification/`**: this repository. It holds the LinkML annotations, the generator,
  the context, the vocabulary, the mapping table, the docs, the examples and the conformance
  vectors.
- **`FAIR-bioHeaders-Tools/`**: the `fair-bioheaders` package, with the `bioheaders` command. The
  local checkout is `../FHR-File-Converter`. It holds the `.jsonld` format.

Each repository gets its own PRs, cross-linked. No task publishes, releases, tags, submits to
w3id.org or archives a DOI; those are maintainer actions (both constitutions, "Decision
boundaries"). No task edits `fhr.json`, `Diagram.svg`, `.github/schema-baseline.json` or any
`fhr_schema.json` copy (FR-009).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, directories and the test harness.

- [X] T001 [P] Create `FAIR-bioHeaders-Specification/requirements-jsonld.txt` containing exactly `PyLD==3.3.0` (dev and test only). Add a step to `FAIR-bioHeaders-Specification/.github/workflows/validate-specification.yml` that runs `python -m pip install -r requirements-jsonld.txt` after the LinkML install. Add the same install line to the Verification block of `FAIR-bioHeaders-Specification/AGENTS.md`
- [X] T002 [P] Create the directories `FAIR-bioHeaders-Specification/jsonld/` and `FAIR-bioHeaders-Specification/mappings/`. Copy `specs/011-jsonld-mapping/contracts/mapping-table.schema.json` byte-for-byte to `FAIR-bioHeaders-Specification/mappings/mapping-table.schema.json`
- [X] T003 [P] In `FAIR-bioHeaders-Tools/pyproject.toml`:
  - add `bioheaders/fhr.context.jsonld` to `include`;
  - add `pyld = {version = "^3.3", optional = true, python = ">=3.10"}` and `[tool.poetry.extras] jsonld = ["pyld"]`;
  - add `pyld` to the dev group with the same `python = ">=3.10"` marker.

  Leave the runtime dependencies (`jsonschema`, `pyyaml`) unchanged. Change `poetry install` to `poetry install --extras jsonld` in `FAIR-bioHeaders-Tools/.github/workflows/pytest.yaml`, and run `poetry lock` so that `poetry.lock` is updated

  *Done for the MVP (2026-10-10):* only the `include` line. The `jsonld` extra, the dev-group
  `pyld`, the `--extras jsonld` CI change and the lock update move to US3 (T035–T037), because no
  MVP test needs a JSON-LD processor in the toolkit (maintainer instruction for the MVP run)
- [X] T004 [P] Create `FAIR-bioHeaders-Tools/tests/conftest.py` with an autouse fixture that makes `socket.socket.connect` raise for every test in `jsonld_test.py`. The JSON-LD tests must pass offline (FR-005)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The semantics in LinkML, the generator, and the generated context and vocabulary.
Every story needs these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for the foundation (write first, must fail)

- [X] T005 [P] Write `FAIR-bioHeaders-Specification/tests/test_jsonld_context.py` (unittest). It asserts that:
  - `python scripts/make_jsonld.py --check` exits 0;
  - `jsonld/fhr.context.jsonld` has `"@version": 1.1` and `"@protected": true`, the prefixes `sdo` = `http://schema.org/` and `fhr` = `https://w3id.org/fair-bioheaders/terms#`, **no `@vocab`** and **no `schema` prefix**;
  - every key of `fhr.json` at every depth (walking `properties`, `items`, `anyOf` and `$ref`) is a term in the right scope of data-model §2. There are 24 at the root, 2 in `taxon`, 2 in each author list, 2 in `accessionID`, 9 in `vitalStats` and 4 in `assemblySoftware`;
  - every nested scope's `@context` is an array whose first item is `null`;
  - "In each scope the map from key to `@id` is one-to-one" (data-model §2 rule 4);
  - only `schema`, `relatedLink`, `assemblyProtocol`, `accessionID.url` and `assemblySoftware[].uri` have `"@type": "@id"`, `dateCreated` has `"@type": "xsd:date"`, `commandLineOption` has `"@container": "@list"`, and the seven array-valued keys have `"@container": "@set"`;
  - `scripts/check_linkml.py` still exits 0.
- [X] T006 [P] Write `FAIR-bioHeaders-Specification/tests/test_jsonld_vocabulary.py` (unittest, foundation part). It asserts that:
  - `jsonld/terms.ttl` parses with rdflib and has exactly 2 classes (`Agent`, `VitalStats`) and the 22 properties listed in contracts/vocabulary.md;
  - every term has an `rdfs:label` and a non-empty `rdfs:comment` (FR-002) and `rdfs:isDefinedBy <https://w3id.org/fair-bioheaders/terms>`;
  - every `fhr:` IRI in `jsonld/fhr.context.jsonld` is defined in `terms.ttl`;
  - no core slot outside FHR schemaVersion 1 (`derivedFrom`, `headerType`, `relationship`) has a term;
  - `docs/TERMS.md` has exactly one heading per term whose text is exactly the local name.

### Implementation for the foundation

- [X] T007 Annotate `FAIR-bioHeaders-Specification/schemas/core.yaml` (research R-08). Make no constraint change:
  - add prefixes `sdo: http://schema.org/`, `fhr: https://w3id.org/fair-bioheaders/terms#`, `xsd: http://www.w3.org/2001/XMLSchema#` and `dcterms: http://purl.org/dc/terms/`, and set `default_prefix: fhr`;
  - add `uri: xsd:string` to type `sha2`;
  - add `slot_uri` on the core slots: `schema` → `sdo:schemaVersion`, `taxon` → `sdo:about`, `version` → `sdo:version`, `dateCreated` → `sdo:dateCreated`, `identifier` → `sdo:identifier`, `scholarlyArticle` → `sdo:citation`, `documentation` → `sdo:description`, `funding` → `sdo:funding`, `reuseConditions` → `sdo:license`;
  - add `broad_mappings: [sdo:identifier]` on `accessionID`;
  - add `class_uri` `sdo:Taxon` on `Taxon`, `fhr:Agent` on `Author` and `sdo:PropertyValue` on `AccessionID`;
  - on `Author`, add `close_mappings: [dcterms:Agent]` and the annotation `jsonld_type_if_uri: sdo:Person`;
  - add `slot_uri: sdo:name` on `Taxon.name`, `Author.name` and `AccessionID.name`, and `slot_uri: sdo:url` on `AccessionID.url`;
  - add the annotation `jsonld_node_id: true` on `Taxon.uri` and `Author.uri`.

  Then run `python scripts/check_linkml.py` and `python -m unittest tests.test_core_schema tests.test_linkml`; both must pass unchanged

  *As implemented:* the maintainer decisions (T046) replace `jsonld_type_if_uri` with
  `jsonld_type_if_orcid: sdo:Person` and `jsonld_type_if_ror: sdo:Organization`, and
  `documentation` gains `jsonld_slot_uri_if_url: sdo:subjectOf`. Three further annotations keep
  LinkML the single source: `jsonld_iri: true` on `schema` (fhr.json types it as a plain string, so
  no range gives the contract's `"@type": "@id"`), and `vocabulary_comment` and
  `vocabulary_subclass_of` on `Author` (and `vocabulary_subclass_of` on `VitalStats`) for the
  vocabulary text and `rdfs:subClassOf` of contracts/vocabulary.md
- [X] T008 Annotate `FAIR-bioHeaders-Specification/fhr_linkml.yml`:
  - add prefixes `sdo:` and `fhr:`, and set `default_prefix: fhr` (keep `MIXS:`; drop `ex:` only if nothing uses it);
  - add `class_uri: sdo:Dataset` on `FHR` and `class_uri: fhr:VitalStats` on `VitalStats`;
  - add `slot_uri: sdo:name` on `genome`, `sdo:alternateName` on `genomeSynonym` and `sdo:creator` on `assemblyAuthor`;
  - on `AssemblySoftware`, add `class_uri: sdo:SoftwareApplication` and the attribute `slot_uri`s `name` → `sdo:name`, `uri` → `sdo:url` and `version` → `sdo:softwareVersion`, and add `list_elements_ordered: true` on `commandLineOption`;
  - add descriptions copied verbatim from `fhr.json` to `N90`, `gcContent` and the `AssemblySoftware` attributes that lack one, and a description to every class that lacks one.

  The existing `exact_mappings`, `broad_mappings` and `related_mappings` to `MIXS:` stay unchanged. Re-run `python scripts/check_linkml.py`, `python scripts/check_schema_drift.py` and `python -m unittest tests.test_linkml`; all must pass
- [X] T009 Implement `FAIR-bioHeaders-Specification/scripts/make_jsonld.py`. It uses `linkml_runtime.SchemaView` on `fhr_linkml.yml` and, for each class reachable from `FHR`, reads `induced_slot(...)`. It writes:
  1. `jsonld/fhr.context.jsonld`, following data-model §1–2:
     - keys in `fhr.json` property order;
     - multivalued → `@set`;
     - `list_elements_ordered` → `@list`;
     - range `uri` → `"@type": "@id"`;
     - range `date` → `xsd:date`;
     - `jsonld_node_id` → the keyword `@id`;
     - a class range → `"@context": [null, {"@protected": true, prefixes, type terms, keys}]`;
     - `assemblySoftware` (any_of) → `@set` plus the AssemblySoftware scope;
     - output `json.dumps(..., indent=2) + "\n"`.

     It fails if two keys in a scope share an IRI.
  2. `jsonld/terms.ttl` and `docs/TERMS.md`, following contracts/vocabulary.md. Only `fhr:` slots and classes reachable from `FHR` are written: `broad_mappings` to `sdo:` give `rdfs:subPropertyOf`, and `close_mappings` give `skos:closeMatch`.

  `--check` regenerates in memory and exits 1 with a unified diff on any difference. The script has a module docstring and no network access

  *As implemented:* the root scope also carries `dct` and four non-FHR terms after the FHR keys:
  `subjectOf` (from the `documentation` annotation, maintainer decision 3) and the export terms
  `keywords`, `url` and `conformsTo` (maintainer decision 2, T048). The author scope gains the type
  term `Organization`. The generated context expands the R-04-typed example to the same N-Quads
  as the contract draft (53 quads, URDNA2015)
- [X] T010 Run `python scripts/make_jsonld.py` and commit `FAIR-bioHeaders-Specification/jsonld/fhr.context.jsonld`, `FAIR-bioHeaders-Specification/jsonld/terms.ttl` and `FAIR-bioHeaders-Specification/docs/TERMS.md`. Confirm that the generated context expands `examples/example.fhr.json` (with the R-04 types added) to the same N-Quads as `specs/011-jsonld-mapping/contracts/fhr.context.jsonld`. If it differs, fix the generator or record the reason in research.md R-06. Makes T005 and T006 pass
- [X] T011 Add a `python scripts/make_jsonld.py --check` step to `FAIR-bioHeaders-Specification/.github/workflows/validate-specification.yml` after the `check_linkml.py` step, and add the same command to the Verification block of `FAIR-bioHeaders-Specification/AGENTS.md`

**Checkpoint**: Foundation ready. The LinkML annotations are in place and `check_linkml.py`
passes. The context and vocabulary are generated and committed, with drift checked in CI.

---

## Phase 3: User Story 1 - Publish FHR metadata as linked data (Priority: P1) 🎯 MVP

**Goal**: An FHR record converts to JSON-LD (FHR keys, an embedded context and typed nodes).
This expands to schema.org and FHR triples and converts back to the identical record, in both
repositories, offline.

**Independent Test**:
- `python -m unittest tests.test_jsonld_roundtrip tests.test_jsonld_vocabulary -v` (quickstart
  V3 and V4) and `poetry run pytest tests/jsonld_test.py` (V5) pass.
- The JSON-LD of every example and conformance metadata record expands with PyLD to predicates
  in `sdo:`, `fhr:` or `rdf:` only, and reads back unchanged.
- The manual schema.org validator check (V8) is recorded.

### Tests for User Story 1 (write first, must fail) ⚠️

- [X] T012 [P] [US1] Write `FAIR-bioHeaders-Specification/tests/test_jsonld_roundtrip.py` (unittest; PyLD tests are skipped with a message when `pyld` is missing). The records are:
  - `examples/example.fhr.json`;
  - `examples/minimal.fhr.json`;
  - `examples/example.fhr.yaml`, with dates as ISO strings;
  - every FHR header of `conformance/valid/*.fhr.fasta` and `*.fhr.gfa`, decoded as `check_conformance.py` does.

  For each record it asserts that:
  - the reference writer `make_jsonld.to_jsonld(record)` follows contracts/cli.md "Writing" steps 1–4: `@type` is the first key of each nested node, there is no `null` and no empty node, and authors are `Person` only when `uri` is present;
  - canonical stripping gives back a record equal to the original under data-model §8 (key order ignored, array order and JSON scalar types kept): SC-001;
  - PyLD 3.3.0 expansion succeeds with a bundled-only document loader, and compaction with the context, plus the `assemblySoftware` restoration, equals the record for every record except `fasta-nested-checksum` and `gfa-nested-checksum`. Those two lose exactly `taxon.checksum`, which is the expected loss (research R-12);
  - `examples/example.fhr.jsonld` and `examples/minimal.fhr.jsonld` are byte-identical to the reference writer's output.

  *As implemented:* 33 records (3 examples and the 30 uncompressed valid FASTA/GFA vector
  headers). The reference canonical reader is `make_jsonld.canonical_record`. The file also
  holds the T046/T048 cases
- [X] T013 [P] [US1] Extend `FAIR-bioHeaders-Specification/tests/test_jsonld_vocabulary.py` for SC-003. For every record of T012, the expanded predicates and `@type` IRIs lie in `http://schema.org/`, `https://w3id.org/fair-bioheaders/terms#` or `rdf:` `type`/`first`/`rest`/`nil`, and datatypes in `xsd:`. Using `tests/fixtures/schemaorg-v30.1-subset.json`, assert that every `sdo:` term exists, and that every `sdo:` property is used only on a node whose `@type` (or a superclass of it) is in the property's `domainIncludes`. This must reject `sdo:relatedLink` on a `sdo:Dataset`; add a negative unit case
- [X] T014 [P] [US1] Write `FAIR-bioHeaders-Tools/tests/jsonld_test.py` (writer and canonical reader; no PyLD needed). It covers:
  - `output_jsonld()` for `examples/example.fhr.json` and `minimal.fhr.json` is byte-identical to `examples/example.fhr.jsonld` and `minimal.fhr.jsonld`;
  - the typing rules of data-model §5, including a legacy string `assemblySoftware` and an author without `uri` → `"Agent"`;
  - "Absent optional fields stay absent" (no `null` and no empty node);
  - `convert` prints `FHR: JSON-LD: taxon.checksum has no JSON-LD term; linked-data consumers will ignore it` for the nested-checksum metadata, and still writes the output;
  - canonical reading:
    - of the embedded context;
    - of each URL in `KNOWN_CONTEXT_URLS`;
    - with `@type` at every depth set aside;
    - with duplicate keys rejected;
    - with a missing `checksum` rejected by schema validation;
  - a non-canonical document without PyLD installed fails with `FHR: reading this JSON-LD form needs the jsonld extra: pip install "fair-bioheaders[jsonld]"` (monkeypatch the import);
  - `bioheaders/fhr.context.jsonld` is byte-identical to `../FAIR-bioHeaders-Specification/jsonld/fhr.context.jsonld`, skipped when that checkout is absent.

  *As implemented:* the MVP has no general reader, so a non-canonical document fails with `this
  JSON-LD is not in the canonical FAIR-bioHeaders form (rule J1 of FAIR-bioHeaders-Specification
  docs/JSONLD.md); reading other JSON-LD forms is not supported yet`, PyLD or not; the "needs
  the jsonld extra" message arrives with the extra in US3. The specification checkout is
  `$FHR_SPECIFICATION` or `../FAIR-bioHeaders-Specification`
- [X] T015 [P] [US1] Extend `FAIR-bioHeaders-Tools/tests/fhr_test.py`:
  - add `"jsonld"` to `test_round_trip`'s `kind` parametrisation;
  - add `.jsonld` and `.jsonld.gz` to `test_cli_all_formats_and_sequence_helpers`, including `--from jsonld`/`--to jsonld` with `-`, and `bioheaders combine` with a `.jsonld` metadata file;
  - in `test_installed_entry_points_outside_checkout`, add `fhr-convert example.fhr.json out.jsonld` and back, from outside the checkout.

  Extend `FAIR-bioHeaders-Tools/tests/bioheaders_test.py::test_convert_and_validate_match_fhr_commands` with a `.jsonld` case

### Implementation for User Story 1

- [X] T016 [US1] Add a reference writer to `FAIR-bioHeaders-Specification/scripts/make_jsonld.py`. `to_jsonld(record)` follows contracts/cli.md "Writing" steps 1–4 exactly, and `--examples` writes `examples/example.fhr.jsonld` and `examples/minimal.fhr.jsonld` from the JSON examples, which `--check` also verifies. Generate and commit both example files
- [X] T017 [US1] Create `FAIR-bioHeaders-Specification/scripts/make_jsonld.py --schemaorg-subset SOURCE`, which reads a local copy of `https://schema.org/version/30.1/schemaorg-current-https.jsonld` (verifying its SHA-256, recorded in the script) and writes `FAIR-bioHeaders-Specification/tests/fixtures/schemaorg-v30.1-subset.json`. The subset contains every `sdo:` term in the context, plus `Thing`, `CreativeWork`, `StructuredValue`, `Intangible`, `Text`, `URL`, `Number`, `Integer`, `Date` and `DateTime`, each with `domainIncludes`, `rangeIncludes`, `subClassOf` and `pending`. It has a `_source` field: "Derived from schema.org v30.1 (https://schema.org/docs/releases.html#v30.1), CC BY-SA 3.0, https://schema.org/docs/terms.html". Commit the fixture. The download is a manual step, and CI never fetches it (makes T013 pass)

  *As implemented:* the source was the copy of
  `https://schema.org/version/latest/schemaorg-current-https.jsonld` retrieved on 2026-10-10
  (then v30.1); its SHA-256 is pinned. The subset also has `relatedLink`, for the negative
  domain test
- [X] T018 [US1] Write `FAIR-bioHeaders-Specification/docs/JSONLD.md`. It covers:
  - what the JSON-LD form is: FR-007, the embedded context and the typing rules of data-model §5;
  - how to embed it in HTML (`<script type="application/ld+json">`, escaping `</`);
  - "follows, does not claim conformance with" the Bioschemas profiles, with the table of missing minimum properties from research R-04;
  - the publication statement:
    - the context's canonical source is raw-main;
    - release copies are at `https://w3id.org/fair-bioheaders/fhr/vX.Y.Z/jsonld/fhr.context.jsonld`;
    - records embed the context because raw GitHub serves `text/plain` (research R-09);
  - the RDF-level losses of research R-12;
  - reading rules **J1, J2, J6 and J7**, worded as in research R-13 and given the stable ids J1 to J7. J3–J5 are added in T033.

  *As implemented:* J1 also covers `subjectOf`, a root `@id` and the export terms (research
  R-18), and the document describes the export context and the conditional Bioschemas claim

  Link it from `FAIR-bioHeaders-Specification/docs/FORMAT.md` and `FAIR-bioHeaders-Specification/README.md`
- [X] T019 [US1] Extend `FAIR-bioHeaders-Specification/scripts/make_conformance.py` with the J1/J2/J6/J7 vectors, written as literal documents with no PyLD:
  - valid `jsonld-canonical-embedded`, `jsonld-canonical-url`, `jsonld-keys-reordered`, `jsonld-legacy-software-string`, `jsonld-open-object-extra-key` (`taxon.checksum`, kept under J1) and `jsonld-schema-versioned-url` (`schema` = `https://w3id.org/fair-bioheaders/fhr/v0.4.0`, research R-16);
  - invalid `jsonld-duplicate-key` and `jsonld-missing-checksum`.

  Add to `conformance/manifest.json`: `"jsonldSpecification": "docs/JSONLD.md"`, rule summaries `J1`–`J7`, and entries with `"format": "jsonld"`, expected `valid`/`invalid`, `rules` and the expected `metadata` for valid vectors. Regenerate and commit `FAIR-bioHeaders-Specification/conformance/`

  *As implemented:* the manifest has J1, J2, J6 and J7 (J3–J5 come with T033, as the labelled
  rules must match docs/JSONLD.md); J7 is `notApplicable` for invalid input. Four further vectors
  cover the maintainer decisions and J1: valid `jsonld-documentation-url` and
  `jsonld-export-terms`, invalid `jsonld-type-object` and `jsonld-documentation-and-subjectof`.
  12 JSON-LD vectors, 124 in all
- [X] T020 [US1] Extend `FAIR-bioHeaders-Specification/scripts/check_conformance.py`:
  - `COMMANDS["jsonld"] = "fhr-convert"`, run as `fhr-convert in.jsonld out.json`, comparing the output metadata like microdata (`same_json`);
  - for `--schema`, strip `@context`/`@type` from J1 vectors before validating;
  - a new `--skip-format FORMAT` option (repeatable).

  In `FAIR-bioHeaders-Specification/.github/workflows/validate-specification.yml`, pass `--skip-format jsonld` to the step that runs the pinned `fhr==0.3.3` converter. Extend `FAIR-bioHeaders-Specification/tests/test_conformance.py` to cover the new format and the option
- [X] T021 [US1] Extend `FAIR-bioHeaders-Specification/scripts/check_release.py` so that it also requires `--converter`'s `bioheaders/fhr.context.jsonld` to be byte-identical to `jsonld/fhr.context.jsonld`. The example loop already covers `examples/*.fhr.jsonld`
- [X] T022 [US1] Copy `FAIR-bioHeaders-Specification/jsonld/fhr.context.jsonld` byte-for-byte to `FAIR-bioHeaders-Tools/bioheaders/fhr.context.jsonld`, and `FAIR-bioHeaders-Specification/examples/example.fhr.jsonld` and `minimal.fhr.jsonld` to `FAIR-bioHeaders-Tools/examples/`
- [X] T023 [US1] Implement `FAIR-bioHeaders-Tools/bioheaders/jsonld.py`. It provides:
  - `CONTEXT`, loaded with `importlib.resources`, and `RELEASED_CONTEXTS`, the list of bundled releases (initially one);
  - `KNOWN_CONTEXT_URLS`, built per contracts/cli.md: raw-main, the raw tag URL and the w3id release alias;
  - `to_jsonld(data)`, steps 1–4;
  - `unmapped_keys(data)`, which returns the paths that have no term in the scopes `taxon`, author, `accessionID` and `vitalStats`, written like `assemblyAuthor[0].affiliation`;
  - `is_canonical(doc)` and the canonical branch of `from_jsonld(doc, *, ignore_unknown_terms=False, warn=...)`. The rule: "the only keys starting with `@` anywhere are the root `@context` and `@type` on objects; every `@type` value is a string or an array of strings".

  A non-canonical document makes `from_jsonld` raise `ValueError` with the exact "needs the jsonld extra" message when `import pyld` fails. Use Python 3.9 syntax and import no third-party module at module import time
- [X] T024 [US1] In `FAIR-bioHeaders-Tools/bioheaders/__init__.py`, add `fhr.input_jsonld(stream, ignore_unknown_terms=False)`, which decodes with `_text` and parses with `object_pairs_hook=_unique_object`, then calls `jsonld.from_jsonld` and `self._input`. Add `fhr.output_jsonld()`, which returns `json.dumps(jsonld.to_jsonld(self.__dict__), ensure_ascii=False, indent=2) + "\n"`
- [X] T025 [US1] In `FAIR-bioHeaders-Tools/bioheaders/cli.py`:
  - add `".jsonld": "jsonld"` to `FORMATS` and `"jsonld": "jsonld"` to `FORMAT_NAMES`;
  - in `_convert`, when the output format is `jsonld`, print one `FHR: JSON-LD: <path> has no JSON-LD term; linked-data consumers will ignore it` line to stderr per `jsonld.unmapped_keys(...)` path before writing;
  - update the `convert` subcommand summary and description to "JSON, YAML, JSON-LD, FASTA, GFA, and HTML".

  T014 and T015 pass after this task
- [X] T026 [US1] Document JSON-LD in `FAIR-bioHeaders-Tools/README.md`:
  - the format and extension;
  - the embedded context;
  - the `jsonld` extra (Python 3.10+, needed only for non-canonical input);
  - the provisional `bioheaders.jsonld` API of contracts/cli.md;
  - a link to FAIR-bioHeaders-Specification `docs/JSONLD.md`.

  Also add an `Unreleased` entry to `FAIR-bioHeaders-Tools/CHANGELOG.md`, and add `bioheaders/jsonld.py` and `bioheaders/fhr.context.jsonld` to the repository map in `FAIR-bioHeaders-Tools/AGENTS.md`
- [X] T027 [US1] Run quickstart V1, V3, V4, V5, V6 (the J1/J2/J6/J7 vectors) and V7 in both repositories. Do V8 by hand: paste `examples/example.fhr.jsonld` into <https://validator.schema.org/> and record the result (the recognised types and any errors) in the FAIR-bioHeaders-Specification PR description

  *Status (2026-10-10):* V1, V3, V4, V5 (Python 3.9 and 3.13), V6 (all 124 vectors through the
  toolkit checkout) and V7 (installed wheel, outside the checkout) pass.
  *V8 (2026-10-10):* `examples/example.fhr.jsonld` posted to <https://validator.schema.org/>.
  The first run recognised `Dataset` and `Grant` but read the nested types as relative IRIs:
  the validator does not implement JSON-LD 1.1 property-scoped contexts. The context now also
  defines every node type at the root (same IRIs), and the rerun recognises `Dataset`, `Taxon`,
  `Person`, `PropertyValue`, `SoftwareApplication`, `Grant` and `fhr:VitalStats`. One error
  remains, and it is the example's data: `license` is the text "public domain", where schema.org
  expects a URL or `CreativeWork` (guideline item 7 already recommends a licence URL)

**Checkpoint**: US1 is complete. The JSON-LD of every example and vector expands to allowed
vocabularies and round-trips, and the toolkit converts `.jsonld` in both directions on Python 3.9
and 3.13 with no new runtime dependency.

---

## Phase 4: User Story 2 - Reuse the mapping for other targets (Priority: P1)

**Goal**: One machine-readable table gives, for every FHR field, its JSON-LD term, its DCMI Terms
equivalents and a mapping kind, with conditions and losses. #56 reuses it.

**Independent Test**: `python -m unittest tests.test_jsonld_mappings -v` (quickstart V2). The table
validates, its paths equal all 45 `fhr.json` property paths, every row has a DCMI value or `none`
with a reason and a kind, and every JSON-LD term equals the IRI derived from LinkML.

### Tests for User Story 2 (write first, must fail) ⚠️

- [X] T028 [P] [US2] Write `FAIR-bioHeaders-Specification/tests/test_jsonld_mappings.py` (unittest). It asserts that:
  - `mappings/fhr-jsonld-dcmi.yml` validates against `mappings/mapping-table.schema.json` with `FormatChecker`;
  - `mappings/mapping-table.schema.json` is byte-identical to `specs/011-jsonld-mapping/contracts/mapping-table.schema.json`;
  - the set of `path`s equals the property paths computed from `fhr.json` (walking `properties`, `items`, `anyOf` and `$ref`; arrays get `[]`), which is "45 in schemaVersion 1", that they are unique and that they are in `fhr.json` order;
  - every `jsonld.term` equals the IRI that `jsonld/fhr.context.jsonld` gives that path, or `@id` for `taxon.uri` and the author `uri`s;
  - `jsonld.status` is `core`/`pending` as in `tests/fixtures/schemaorg-v30.1-subset.json` for `sdo:` terms and `fhr` for `fhr:` terms;
  - every `fhr:` row has `kind: exact` and a non-empty `schemaorg_gap`;
  - every `dcmi[].term` is `none` or a term in `tests/fixtures/dcmi-terms-2020-01-20.txt`;
  - `subject: record` is set on `schema`, `metadataAuthor`, `metadataAuthor[].name` and `metadataAuthor[].uri`;
  - the table's `rdfs:subPropertyOf`/`closeMatch` implications agree with `jsonld/terms.ttl` (`fhr:accessionID` ⊑ `sdo:identifier`).

  It prints the summary counts (schema.org, `@id`, FHR; DCMI term vs none)
- [X] T029 [P] [US2] Create `FAIR-bioHeaders-Specification/tests/fixtures/dcmi-terms-2020-01-20.txt` with one `http://purl.org/dc/terms/` term IRI per line: all properties and classes of DCMI Metadata Terms, 2020-01-20 release. Its header comment lines give the source <https://www.dublincore.org/specifications/dublin-core/dcmi-terms/> and "DCMI Metadata Terms, CC BY 4.0"

### Implementation for User Story 2

- [X] T030 [US2] Write `FAIR-bioHeaders-Specification/mappings/fhr-jsonld-dcmi.yml` (`table_version: 1.0.0`).
  - The header:
    - `id`: the raw-main URL of the file;
    - `source_schema`: the raw-main `fhr.json`;
    - `source_schema_version: 1.0`;
    - `targets.jsonld` (schema.org, `30.1`, <https://schema.org/docs/releases.html#v30.1>, namespaces `http://schema.org/` and `https://w3id.org/fair-bioheaders/terms#`);
    - `targets.dcmi` (DCMI Metadata Terms, `2020-01-20`);
    - `kinds`, with the SKOS equivalents of research R-02.
  - One entry per row of the table in research R-03, in that order, carrying over verbatim the term, the status, the kind and every condition and note.
    - Add `coercion` and `type` per data-model §4.
    - Add `rdf_loss` "order of @set items" on `metadataAuthor`, `assemblyAuthor` and `identifier`.
    - Add `schemaorg_gap` for the 22 `fhr:` rows.
    - Add `reason` on every `none`.
    - Add `sources`, citing #56 (<https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/56>), `docs/MAPPINGS.md` and the schema.org and Bioschemas pages named in R-03.

  Makes T028 pass

  *As implemented:* `rdf_loss` is on all seven `@set` paths (the three named, plus
  `genomeSynonym[]`, `instrument[]`, `relatedLink[]` and `assemblySoftware`), since all of them
  lose order in RDF. The `documentation` row records the `subjectOf` condition (maintainer
  decision 3), and the author rows list the three writer types. Counts as in R-03: 20 schema.org,
  3 `@id`, 22 FHR; 19 DCMI terms (6 exact, 2 broader, 11 conditional) and 26 none
- [X] T031 [US2] Turn `FAIR-bioHeaders-Specification/docs/MAPPINGS.md` into a profile index. Keep the existing MIxS/MIGS section unchanged, and add a "JSON-LD and Dublin Core (DCMI Terms)" section that covers:
  - a summary table generated from the mapping table: path, JSON-LD term, DCMI term and kind;
  - the kind vocabulary and its direction, including the note that `fhr_mappings.yml`'s `relationship: narrow` for `sop` is `broader` in this table;
  - the record-versus-assembly `subject` rule;
  - a "Reusing this table (#56)" paragraph: further targets such as DataCite and Crossref are added as new `targets` keys and new per-entry lists, without changing existing rows.

  Add a `--mappings-summary` mode to `FAIR-bioHeaders-Specification/scripts/make_jsonld.py` that prints the summary table, and have `--check` verify that the table in `docs/MAPPINGS.md` is current. Also add the `DCMI:` line to each term section of the generated `docs/TERMS.md` from the mapping table, and regenerate it
- [X] T032 [US2] Link the table from `FAIR-bioHeaders-Specification/README.md` and `FAIR-bioHeaders-Specification/AGENTS.md`. The AGENTS.md repository map gains `mappings/` and `jsonld/`, and the rule "term IRIs come from LinkML; the mapping table is curated and test-checked against it". Request maintainer confirmation of SC-004 from David on the PR. This is a request, not a task outcome

  *As implemented:* the links and the repository map are in. No PR was opened in this run, so
  the SC-004 request to David is still to be made on the PR

**Checkpoint**: US2 is complete. The MVP (US1 and US2) is done.

---

## Phase 5: User Story 3 - Read JSON-LD back into FHR (Priority: P2)

**Goal**: JSON-LD in other forms, such as expanded or compacted differently, converts back to the
same FHR record, offline. Terms outside the mapping are reported, never silently dropped.

**Independent Test**: `python scripts/check_conformance.py --converter ../FHR-File-Converter`
(with the toolkit installed with `--extras jsonld`, Python 3.10+). Every J3–J5 vector passes, and
`poetry run pytest tests/jsonld_test.py -k general` passes.

### Tests for User Story 3 (write first, must fail) ⚠️

- [X] T033 [P] [US3] Extend `FAIR-bioHeaders-Specification/scripts/make_conformance.py` with the J3–J5 vectors, written as literal documents (no PyLD, so that regeneration stays deterministic):
  - valid `jsonld-expanded`, `jsonld-schemaorg-vocab-compaction` (`{"@vocab": "http://schema.org/", "fhr": "https://w3id.org/fair-bioheaders/terms#"}`, `dateCreated` as a typed value object), `jsonld-graph-single-node` and `jsonld-iri-as-string` (`relatedLink` given as a string under `@vocab` compaction);
  - invalid `jsonld-unknown-term` (`http://schema.org/keywords`), `jsonld-remote-context` (`"@context": "https://schema.org/"`), `jsonld-two-nodes`, `jsonld-two-genome-values`, `jsonld-flattened`, `jsonld-datetime-datecreated` and `jsonld-root-id`.

  Add the manifest entries with rules `J3`–`J5` and the expected `metadata`. Add the rule text for J3–J5 to `FAIR-bioHeaders-Specification/docs/JSONLD.md`, worded as in research R-13. Regenerate `FAIR-bioHeaders-Specification/conformance/`
- [X] T034 [P] [US3] Extend `FAIR-bioHeaders-Tools/tests/jsonld_test.py` with general-path tests (`pytest.importorskip("pyld")`). They cover:
  - every `jsonld` vector copied from FAIR-bioHeaders-Specification `conformance/` (into `tests/fixtures/jsonld/`), with the manifest's expected outcome;
  - for each example, the PyLD-expanded form reads back equal under data-model §8;
  - the reverse map derived from `CONTEXT` covers all 45 paths;
  - the document loader raises "loading document failed" for `https://schema.org/` and for every unknown URL, with sockets blocked;
  - the nested-checksum vectors fail reporting `checksum`, and with `ignore_unknown_terms=True` they succeed and print `FHR: warning: JSON-LD term not in the FHR mapping: ...`;
  - the error messages of contracts/cli.md, verbatim (`exactly one FHR record (found N nodes)`, `gives 2 values for single-valued field genome`, `context is not available offline: <url>`)

### Implementation for User Story 3

- [X] T035 [US3] Implement the general path in `FAIR-bioHeaders-Tools/bioheaders/jsonld.py`. It has:
  - a document loader that returns only the bundled `RELEASED_CONTEXTS` for `KNOWN_CONTEXT_URLS` and raises `JsonLdError(..., code="loading document failed")` otherwise;
  - `pyld.jsonld.expand(doc, {"documentLoader": loader}, on_property_dropped=...)`;
  - a single-node check that allows a single-item `@graph`;
  - a `REVERSE_MAP`, derived once from `CONTEXT`, of scope → IRI → `(key, coercion, child scope)` (data-model §4);
  - the J5 value rules of contracts/cli.md step 5;
  - unknown-term collection (data-model §7) with `reason` `dropped`, `unmapped` or `root-id`, which raises unless `ignore_unknown_terms` and otherwise calls `warn`.

  Output keys follow `fhr.json` property order. PyLD is imported only inside this path
- [X] T036 [US3] Add `--ignore-unknown-terms` to `convert` and `validate` in `FAIR-bioHeaders-Tools/bioheaders/cli.py` (`_convert_arguments`, `_validate_arguments`). Pass it through `read_metadata(path, ..., ignore_unknown_terms=...)` to `input_jsonld`; it is ignored for other formats. Help text: "JSON-LD input only: report terms that do not map to an FHR field as warnings instead of errors". T034 passes after this task
- [X] T037 [US3] Install the toolkit with `--extras jsonld` on Python 3.13, and run `python scripts/check_conformance.py --converter ../FHR-File-Converter` from FAIR-bioHeaders-Specification (quickstart V6, all `jsonld` vectors). Add the general path and the `--ignore-unknown-terms` option to `FAIR-bioHeaders-Tools/README.md` and the `Unreleased` entry of `FAIR-bioHeaders-Tools/CHANGELOG.md`

  *As implemented (US3, 2026-10-10):*
  - The vectors are generated by `expand_canonical` and `vocab_compact` in
    `make_conformance.py`, which rewrite the reference writer's output without a JSON-LD
    processor. `tests/test_jsonld_roundtrip.py` checks with PyLD that each valid vector
    expands to the same RDF (URDNA2015 N-Quads) as the canonical document, except
    `jsonld-iri-as-string`, whose plain strings are literals in RDF.
  - `jsonld-root-id` is in expanded form: under J1 a root `@id` is now export metadata
    (maintainer decision 2), so only the general path reports it (reason `root-id`).
  - `jsonld-flattened` gives the taxon only as `{"@id": ...}`. A flattened document with the
    taxon as a second top-level node already fails J4.
  - The toolkit copies the 23 `jsonld` vectors with their manifest entries into
    `tests/fixtures/jsonld/`. A test compares them with a sibling FAIR-bioHeaders-Specification checkout
    when one exists.
  - A dropped term has no location, so its message ends "(dropped by JSON-LD expansion: it
    has no IRI)". Several unknown terms are listed in one message, separated by commas.
  - A language-tagged value is an error, as a datatype is, because FHR cannot keep it.
  - PyLD is the optional `jsonld` extra and also a dev dependency (Python 3.10+), so the
    toolkit CI runs the general-path tests on 3.13 and skips them on 3.9 without a workflow
    change.

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: The w3id preparation, documentation, the full gates and the cross-repository
consistency.

- [X] T038 [P] Prepare the w3id `terms` rule; do **not** open a PR. In a scratch clone of perma-id/w3id.org, apply the `.htaccess` text of `specs/011-jsonld-mapping/contracts/vocabulary.md` to `ids/fair-bioheaders/.htaccess` and run `node tools/check/bin/w3id-check.js`. It must report no error and no `htaccess/no-406-fallback` or `htaccess/avoid-permanent-redirect` warning. Then run the two `curl` checks against `tools/server`. Record the outputs in the FAIR-bioHeaders-Specification PR description for Adam or David to submit after `jsonld/terms.ttl` and `docs/TERMS.md` are on `main`
- [X] T039 [P] Update `FAIR-bioHeaders-Specification/CHANGELOG.md` (Unreleased: JSON-LD context, vocabulary, mapping table, rules J1–J7, LinkML annotations; no schema change). Also update the `FAIR-bioHeaders-Specification/README.md` formats list and add a "JSON-LD" row to `FAIR-bioHeaders-Specification/docs/TOOL_COMPATIBILITY.md` if it lists formats
- [X] T040 [P] Make `FAIR-bioHeaders-Specification/scripts/make_jsonld.py` write a header comment at the top of `jsonld/terms.ttl`; JSON cannot hold comments, so the context gets none. Add a "Files" section to `FAIR-bioHeaders-Specification/docs/JSONLD.md` saying the same. Both state:
  - "generated by scripts/make_jsonld.py from the LinkML model; do not edit";
  - the raw-main canonical URL;
  - the w3id release alias pattern `https://w3id.org/fair-bioheaders/fhr/vX.Y.Z/jsonld/...`;
  - that the term IRIs never change (FR-008).

  Regenerate, and confirm that `--check` passes
- [X] T041 Run every FAIR-bioHeaders-Specification gate in plan.md (`unittest`, `validate_examples.py`, `check_linkml.py`, `check_schema_drift.py`, `make_jsonld.py --check`, `check_conformance.py --schema`, `check_release.py --converter ../FHR-File-Converter`, `check_conformance.py --converter ../FHR-File-Converter`), and record any environment limitation
- [X] T042 Run every FAIR-bioHeaders-Tools gate in plan.md on Python 3.9 and 3.13 (`poetry install --extras jsonld`, `pytest`, `ruff`, `isort`, `black`, `poetry build`, `python -m build compat/fhr`). Run the installed-wheel check from outside the checkout (quickstart V7). On 3.9, confirm that the general-path tests are reported as skipped, not failed
- [X] T043 Cross-check the spec trace: walk `specs/011-jsonld-mapping/checklists/traceability.md`, confirm each FR/SC has its tasks done, and cross-link the FAIR-bioHeaders-Specification and FAIR-bioHeaders-Tools PRs (and Tools#35, spec#56). Comment on spec#56 with a link to `mappings/fhr-jsonld-dcmi.yml` **only after merge, and only by a maintainer**
  *Done (2026-10-10):* T041 and T042 ran in the US3 PRs (FAIR-bioHeaders-Specification#86,
  FAIR-bioHeaders-Tools#44): every gate passes; toolkit 1053 passed on 3.13, and on 3.9 the
  general-path tests are skipped. The trace walk is recorded at the end of
  `checklists/traceability.md`

### Maintainer decisions (plan.md, 2026-10-10)

- [X] T044 [P] Publish the JSON-LD files on GitHub Pages from FAIR-bioHeaders-Specification. Add `.github/workflows/jsonld-pages.yml` that builds a site with:
  - `vX.Y.Z/context.jsonld` for every release tag that has `jsonld/context.jsonld`, plus the current `main` build for preview;
  - `terms/` with `index.html` (from `docs/TERMS.md`), `terms.ttl` and `terms.jsonld`.

  Pages must serve `application/ld+json` and `text/turtle` with CORS. Verify with `curl -I`. Adam enables Pages (Settings → Pages → Source: GitHub Actions)
  *As implemented:* `scripts/build_pages.py` builds the site under `fhr/vX.Y.Z/jsonld/` (the
  repository paths, so the w3id rule maps one-to-one) and `fhr/main/jsonld/`; the vocabulary
  is also committed as `jsonld/terms.jsonld`, generated by `make_jsonld.py`
- [X] T045 [P] Extend the T038 w3id rule text:
  - `/fair-bioheaders/fhr/vX.Y.Z/context.jsonld` goes to the Pages copy;
  - `/fair-bioheaders/terms` does content negotiation (Accept `text/turtle` → `terms.ttl`, `application/ld+json` → `terms.jsonld`, default → HTML), with a 406-safe fallback.

  Run `w3id-check`. A maintainer submits it (prepared, not opened)
- [X] T046 [US1] In the toolkit JSON-LD writer (and `make_jsonld.py` documentation), type authors from their identifier: ORCID → `sdo:Person`, ROR → `sdo:Organization`, otherwise `fhr:Agent`. Map `documentation` to `sdo:description` for text and `sdo:subjectOf` for an absolute URL. Add tests for each case, and a round trip
  *As implemented:* in both writers (toolkit `bioheaders/jsonld.py` and the reference
  `make_jsonld.py`). An absolute URL is written under the key `subjectOf` and read back as
  `documentation` (research R-18)
- [X] T047 Optional author `type` (`Personal` | `Organizational`, DataCite `nameType`) as an additive schema change on `release-v0.4`, in a separate FAIR-bioHeaders-Specification PR. It touches the LinkML core, `fhr.json`, the schema-change notes, examples and conformance. The writer prefers an explicit `type` over inference (T046)
  *Done on `release-v0.4`* (FAIR-bioHeaders-Specification#85) as `nameType`; see the tasks.md there
- [X] T048 [US1] Bioschemas: an optional export context file (`--export-context PATH`, same format as #56 will use) supplies `keywords` and `url`. The writer emits `dct:conformsTo` <https://bioschemas.org/profiles/Dataset/1.1-RELEASE> only when every Dataset minimum property is present. Test complete and incomplete cases
  *As implemented (deviations, research R-18):* the export context also takes `id` (the root
  `@id`), which the Dataset minimum list requires, and `conformsTo` names
  `Dataset/1.0-RELEASE`, because 1.1 is still a draft. The format (`id`, `url`, `keywords`) is
  provisional until #56 defines its own

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start at once.
- **Foundational (Phase 2)**: Depends on Setup. It blocks every user story.
- **User Stories (Phases 3–5)**: Depend on Foundational.
  - US1 and US2 are independent of each other and can run in parallel.
  - US2's `docs/TERMS.md` DCMI line (T031) regenerates a file from T010, so merge it after T010.
  - US3 depends on US1's toolkit module (T023–T025) and on US1's conformance plumbing (T019,
    T020).
- **Polish (Phase 6)**: Depends on the stories being shipped. T038 needs only T010.

### Within Each User Story

- Tests are written first and must fail.
- FAIR-bioHeaders-Specification artefacts come before the toolkit copies (toolkit constitution I): T016 and
  T010 before T022, and T019 before T034.
- Generator, then generated files, then docs. Toolkit module, then `__init__`, then CLI.

### Parallel Opportunities

- Setup: T001, T002, T003 and T004 together (different files and repositories).
- Foundation tests: T005 and T006 together. T007 and T008 touch different LinkML files, but
  T008 imports T007's prefixes, so run them in sequence.
- US1 tests: T012, T013, T014 and T015 together. Then FAIR-bioHeaders-Specification T016–T021 and toolkit
  T022–T026 in two lanes once T016 is done.
- US2: T028 and T029 together, alongside all of US1.
- US3: T033 and T034 together.
- Polish: T038, T039 and T040 together.

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (they must fail first):
Task: "Round-trip tests in FAIR-bioHeaders-Specification/tests/test_jsonld_roundtrip.py"            # T012
Task: "SC-003 namespace and schema.org domain tests in FAIR-bioHeaders-Specification/tests/test_jsonld_vocabulary.py"  # T013
Task: "Writer and canonical-reader tests in FAIR-bioHeaders-Tools/tests/jsonld_test.py" # T014
Task: "Format-matrix and installed-wheel tests in FAIR-bioHeaders-Tools/tests/fhr_test.py"  # T015

# Then two lanes:
# Spec:    T016 reference writer + examples → T017 schema.org subset → T018 docs/JSONLD.md → T019 vectors → T020 check_conformance → T021 check_release
# Toolkit: T022 copies (after T016) → T023 jsonld.py → T024 __init__ → T025 cli → T026 docs
# Join:    T027 validation (V1, V3–V8)
```

## Parallel Example: User Story 2

```bash
Task: "Mapping-table tests in FAIR-bioHeaders-Specification/tests/test_jsonld_mappings.py"   # T028
Task: "Pinned DCMI term list in FAIR-bioHeaders-Specification/tests/fixtures/dcmi-terms-2020-01-20.txt"  # T029
# then T030 mapping table → T031 MAPPINGS.md + TERMS.md DCMI line → T032 links + SC-004 request
```

---

## Implementation Strategy

### MVP First (User Stories 1 and 2)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational). **Stop and validate**:
   `make_jsonld.py --check` and `check_linkml.py` pass, and the context matches the prototype's
   N-Quads.
2. Complete Phase 3 (US1). **Stop and validate**: quickstart V3–V7 pass, and V8 is recorded.
3. Complete Phase 4 (US2). **Stop and validate**: V2 passes, with 45 rows and the DCMI column
   complete.
4. The MVP is US1 plus US2:
   - portals can publish FHR records as linked data;
   - the toolkit writes and reads canonical JSON-LD with no new dependency;
   - #56 has its table.

   Releasing the toolkit and registering the w3id rule are maintainer actions.

### Incremental Delivery

1. Setup and Foundational: the first FAIR-bioHeaders-Specification PR (LinkML annotations, generator,
   context and vocabulary).
2. US1, specification side: the second FAIR-bioHeaders-Specification PR (examples, docs, J1/J2/J6/J7
   vectors). Toolkit side: the first toolkit PR (`.jsonld` writer and canonical reader).
3. US2: an FAIR-bioHeaders-Specification PR (mapping table and MAPPINGS.md). It can merge in parallel with
   step 2, and this completes the MVP.
4. US3: an FAIR-bioHeaders-Specification PR (J3–J5 vectors) and a toolkit PR (the general reader and the
   extra).
5. Polish: the w3id rule handed to the maintainers, the changelogs and the full gates.

### Parallel Team Strategy

1. One developer per repository after the Foundational phase. The toolkit developer can do
   T003 and T004 early.
2. Then:
   - Developer A (specification): US1 specification lane (T016–T021), then US2 (T028–T032), then
     the US3 vectors (T033).
   - Developer B (toolkit): US1 toolkit lane (T022–T026), then the US3 reader (T034–T037).

---

## Notes

- [P] tasks touch different files and have no dependencies on incomplete tasks.
- The [Story] label maps each task to a user story for traceability; see
  [checklists/traceability.md](checklists/traceability.md).
- Commit after each task or logical group, with cross-linked PRs in the two repositories.
- Never edit `fhr.json`, the converter schema copies or `.github/schema-baseline.json`. This
  feature changes no schema (FR-009). Never edit the generated `jsonld/*` or `docs/TERMS.md` by
  hand.
- Do not invent metadata or mappings (FAIR-bioHeaders-Specification constitution IV). Every non-exact row
  carries its condition or loss. Examples use the existing synthetic records.
- Open maintainer questions (plan.md) have stated defaults. If one is decided differently, these
  tasks are affected:
  - question 1, context URL hosting: T016, T023 (`KNOWN_CONTEXT_URLS`, the writer's embedded
    context) and T038;
  - question 2, Bioschemas fields: T018;
  - question 3, `documentation`: T007, T030;
  - question 4, agent kind: T007, T014 and T023 (typing).
