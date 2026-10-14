# Implementation Plan: JSON-LD mapping and serialisation for FAIR-bioHeaders metadata

**Branch**: `011-jsonld-mapping` (work branch `specs/jsonld-mapping`) | **Date**: 2026-10-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-jsonld-mapping/spec.md` (clarified 2026-10-10)

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

FHR metadata becomes linked data without changing a single FHR key or the schema. A JSON-LD
document is the FHR record itself plus an `@context` and `@type`. Processors read it as
schema.org (and FHR-vocabulary) triples, and FHR tools read it back to the identical record. The
work has four parts in two repositories:

1. **Semantics in LinkML** (FAIR-bioHeaders-Specification).
   - `schemas/core.yaml` and `fhr_linkml.yml` gain `slot_uri`/`class_uri` annotations, the
     prefixes `sdo:` and `fhr:`, and `default_prefix: fhr`. These are the single source of the
     term IRIs.
   - A small generator, `scripts/make_jsonld.py`, emits the JSON-LD 1.1 context
     (`jsonld/fhr.context.jsonld`) with property-scoped contexts for the nested objects. It also
     emits the FHR vocabulary (`jsonld/terms.ttl`, `docs/TERMS.md`) under
     `https://w3id.org/fair-bioheaders/terms#`.
   - `fhr.json` is untouched, and `check_linkml.py` still passes (research R-06, R-08).
2. **Mapping table** (FAIR-bioHeaders-Specification, `mappings/fhr-jsonld-dcmi.yml` with a JSON Schema).
   - All 45 FHR property paths, each with its JSON-LD term, its DCMI Terms equivalents and a
     mapping kind from #56's vocabulary. 20 paths map to schema.org, 3 become node `@id`s and 22
     use FHR terms. 19 have a DCMI term, and 26 record "none" with a reason. This is the table
     #56 will start from (US2; research R-02, R-03, R-15).
   - `docs/JSONLD.md` states the reading rules J1 to J7, and conformance vectors cover them
     (R-13).
3. **Toolkit** (FAIR-bioHeaders-Tools): `.jsonld` input and output in `bioheaders`.
   - The writer embeds the bundled context and adds typed nodes. It needs no dependency.
   - The canonical reader sets `@context` and `@type` aside and validates as JSON, also with no
     dependency.
   - A general reader for other JSON-LD forms uses an offline PyLD expansion and a deterministic
     mapper, as the opt-in extra `fair-bioheaders[jsonld]` (US1 writer, US3 reader; R-11).
4. **Publication.**
   - The context stays authoritative at raw-main, and the toolkit embeds it rather than
     referencing a URL. Raw GitHub's `text/plain` content type makes URL references unusable for
     conformant JSON-LD processors, and the versioned-URL policy is still open (R-09).
   - The w3id `terms` rule text is prepared for Adam or David to submit (R-10).

All design decisions, with their alternatives, are in [research.md](research.md) (R-01 to R-17).

## Technical Context

**Language/Version**:
- FAIR-bioHeaders-Tools: Python 3.9–3.13; its gates run on 3.9 and 3.13. The general JSON-LD
  reader needs 3.10 or later (PyLD 3), while the writer and the canonical reader work on 3.9.
- FAIR-bioHeaders-Specification scripts and tests: Python 3.13, as in CI.

**Primary Dependencies**:
- FAIR-bioHeaders-Specification:
  - LinkML 1.11.1 (already pinned) for `make_jsonld.py`;
  - `PyLD==3.3.0` as a **dev-only** test dependency (new `requirements-jsonld.txt`);
  - rdflib, which arrives with LinkML, for parsing Turtle in the tests.
- Toolkit:
  - **no new runtime dependency**;
  - an optional extra `jsonld = ["pyld>=3.3,<4"]` (marker `python_version >= "3.10"`), used
    only by the general reader, and PyLD in the dev group. Both arrive with US3: the MVP
    (writer and canonical reader) needs no JSON-LD processor in the toolkit.

**Storage**: Files only.
- FAIR-bioHeaders-Specification: the generated context and vocabulary, the curated mapping table, examples
  and conformance vectors.
- Toolkit: the bundled `bioheaders/fhr.context.jsonld`, byte-identical to the specification's
  `jsonld/fhr.context.jsonld`.

**Testing**:
- FAIR-bioHeaders-Specification: `unittest` (`tests/test_jsonld_*.py`), `scripts/make_jsonld.py --check`, and
  the extended `scripts/check_conformance.py`.
- Toolkit: `pytest` (`tests/jsonld_test.py`) with sockets disabled, run on 3.9 and 3.13. The
  general-path tests skip on 3.9.

**Target Platform**: Wherever the toolkit runs: Linux, macOS, Windows and pipeline nodes. Data
portals embed the output in HTML landing pages.

**Project Type**: A specification artefact set (LinkML annotations, generator, context, vocabulary,
mapping table, docs, vectors) plus a serialisation format in an existing library and CLI.

**Performance Goals**: Not performance-sensitive. Metadata records are kilobytes, and the writer
and canonical reader are single-pass dict operations. Budget: under 50 ms per record for the
canonical path, under 1 s for the general path, including PyLD import.

**Constraints**:
- `fhr.json` and the three toolkit schema copies are unchanged (FR-009, constitution I).
- FHR keys are unchanged (FR-007).
- The term IRIs are unversioned and permanent (FR-008).
- Offline: the context is never fetched (FR-005).
- Deterministic, byte-identical writer output.
- The context is injective per scope (R-06).
- MPL-2.0 for new work, with schema.org (CC BY-SA 3.0) and DCMI (CC BY 4.0) attribution on the
  derived fixtures (R-17).

**Scale/Scope**:
- 45 FHR property paths: 24 top-level and 21 nested.
- 6 node scopes and 7 type terms.
- 24 FHR vocabulary terms: 22 properties and 2 classes.
- About 17 JSON-LD conformance vectors.
- FHR only: FHT, FHP and FHGFF3 reuse the core terms later.

All the unknowns in this context are resolved in [research.md](research.md#technical-context-unknowns-resolution-index).
No NEEDS CLARIFICATION remains.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Both constitutions are **draft** (0.1.0, ratification pending David and Adam). The gates are
applied as written.

### FAIR-bioHeaders-Specification constitution (`.specify/memory/constitution.md`)

| Principle | Gate question | Pre-research | Post-design (re-check) |
|---|---|---|---|
| I. The published JSON schema is the contract | Does the feature change `fhr.json`, the LinkML files or the converter copies? Do LinkML and generated artefacts agree? | **Pass, with an obligation**: annotations-only LinkML edits; FR-009 forbids a schema change | **Pass**. `fhr.json`, `Diagram.svg`, `.github/schema-baseline.json` and the converter schema copies are untouched. The LinkML edits are prefixes, `default_prefix`, `slot_uri`/`class_uri`, two annotations, `list_elements_ordered`, `uri:` on `sha2`, and descriptions copied from `fhr.json`. The prototype confirmed that `check_linkml.py` still reports "LinkML generation matches all published validation constraints" (R-08). The context and vocabulary are generated from LinkML and drift-checked, so they cannot disagree with it. The examples gain `.jsonld` siblings that `check_release.py` keeps identical in the toolkit |
| II. Compatibility before tightening | Could valid metadata become invalid? | **Pass**. Nothing is tightened | **Pass**. Every valid FHR record converts to JSON-LD and back exactly through the canonical path (R-12). JSON-LD is an additional format; JSON, YAML, microdata, FASTA and GFA are unchanged. Package, release, `schemaVersion` and context versions stay distinct (R-09) |
| III. Preserve user data and identity bytes | Are metadata lines and hashed bytes unambiguous? Does every parsing rule have a conformance example? | **Pass, with an obligation**: JSON-LD reading rules need vectors | **Pass**. JSON-LD never touches FASTA/GFA bytes or the checksum rule. `checksum` and `seqcol_id` are separate FHR terms with no equivalence to `sdo:sha256` or to identifiers (R-03 rows 38 and 45). The reading rules J1 to J7 each have valid or invalid vectors in `conformance/` (R-13). Open-object extra keys are preserved in the document and reported for linked data (R-07) |
| IV. No invented metadata | Could the mapping assert equivalences or values that are not justified? | **Pass, with an obligation**: every non-exact mapping states its condition or loss | **Pass**. Authors are typed Person only with an ORCID, otherwise `fhr:Agent` (R-04). No `keywords`, `url` or `dct:conformsTo` is fabricated for Bioschemas. Literals stay literals where a value may be free text (R-06). The mapping table schema requires `condition` for `conditional`, `loss` for `lossy` and `reason` for `none`. DCMI conditions follow #56's crosswalk, and `subject: record` keeps record statements off the assembly. Vocabulary versions are pinned (schema.org 30.1, DCMI 2020-01-20) |
| V. Minimal and interoperable | Are new dependencies and frameworks avoided? Does stripping stay trivial? | **Pass**. Dev-only PyLD; a small generator, not a framework | **Pass**. The generator is FHR-specific and in the style of `json-schema-generator.py`. There is no runtime dependency in the specification, and PyLD is test-only. It reuses schema.org and DCMI rather than inventing terms; FHR terms exist only where no schema.org term fits. Headers and stripping are unaffected. It serves the paper's "variety of serialisations" goal |
| Verification gates | Are they named? | Yes, see below | Yes, plus `make_jsonld.py --check` and the JSON-LD tests |
| Decision boundaries | Does anything here need maintainer authority? | The w3id registration, the context URL policy, Bioschemas fields and SC-004 confirmation are maintainer matters | Unchanged. No task submits to w3id.org, publishes, releases or tags. The `.htaccess` text is prepared as an artefact (R-10). Open questions are below |

**FAIR-bioHeaders-Specification verification gates** (repository root):

```bash
python -m pip install -r requirements-linkml.txt -r requirements-jsonld.txt
python -m unittest discover -s tests -v          # includes test_jsonld_mappings, test_jsonld_roundtrip, test_jsonld_vocabulary, test_jsonld_context
python scripts/validate_examples.py              # unchanged: globs .json/.yaml only
python scripts/check_linkml.py                   # must still pass after the annotations
python scripts/check_schema_drift.py             # no schema change
python scripts/make_jsonld.py --check            # new: context, terms.ttl and TERMS.md up to date
python scripts/check_conformance.py --schema     # extended with jsonld vectors (J6 schema check)
python scripts/check_release.py --converter ../FHR-File-Converter   # extended: context copy identical
python scripts/check_conformance.py --converter ../FHR-File-Converter   # jsonld vectors through the toolkit
```

### FAIR-bioHeaders-Tools constitution (`origin/main:.specify/memory/constitution.md`)

| Principle | Gate question | Pre-research | Post-design (re-check) |
|---|---|---|---|
| I. The specification is the contract | Is the behaviour defined in FAIR-bioHeaders-Specification first? Are the copies byte-identical? | **Pass**. The context, the reading rules, the examples and the vectors are specified here before the toolkit implements them | **Pass**. `bioheaders/fhr.context.jsonld` is byte-identical to `jsonld/fhr.context.jsonld`, checked by a toolkit test and by `check_release.py`. The writer's byte layout and the reading rules are defined in [contracts/cli.md](contracts/cli.md) and `docs/JSONLD.md`. The `fhr_schema.json` copies are untouched |
| II. Exact bytes and one reading | Do all commands identify metadata the same way? | **Pass**: no sequence byte handling changes | **Pass**. `combine` with a `.jsonld` metadata file uses the same `read_metadata`, and the header it writes is the YAML of the same record. Strip and verify are unchanged |
| III. Fail closed on untrusted input | Is ambiguous input rejected? Is resource use bounded? | **Pass, with obligations**: no remote fetch; ambiguity rejected | **Pass**. Duplicate keys are rejected. Contexts that are not bundled are refused, and nothing is fetched. More than one node, flattened form, multiple values for a single field, a wrong datatype and unknown terms are all errors. `--ignore-unknown-terms` is an explicit opt-in that still reports every term. Input size is bounded by the existing metadata reading. The PyLD loader cannot reach the network |
| IV. Preserve metadata and typed values | Do round trips keep values and types? Are absent optional fields omitted? | **Pass, with an obligation**: an exact round trip | **Pass**. The canonical path is exact for every valid record, compared by value and JSON type (R-12). No nulls or empty nodes are emitted. `commandLineOption` order is kept as `@list`. The RDF-level losses are documented and not hidden (R-12) |
| V. Compatible, small, tested | Is the public API intact? Are dependencies small? Are tests shipped? | **Pass**. One format; no new command; no runtime dependency | **Pass, with one justified limitation** (Complexity Tracking): the general reader needs the optional extra and Python 3.10 or later. The existing commands, the nine entry points and the `fhr` alias are unchanged. The new API (`bioheaders.jsonld`, `--ignore-unknown-terms`) is additive and documented as provisional. Tests come first in every story (tasks.md), and the installed wheel is tested from outside the checkout |
| Verification gates | Are they named? | Yes, see below | Yes |
| Decision boundaries | | Package release and DOI are maintainer actions | Unchanged |

**FAIR-bioHeaders-Tools verification gates** (Python 3.9 and 3.13):

```bash
poetry install --extras jsonld            # on 3.9 the extra's marker skips PyLD
poetry run pytest                         # includes tests/jsonld_test.py with sockets disabled
poetry run ruff check .
poetry run isort . --check-only
poetry run black . --check
poetry build
python -m build compat/fhr
# installed-wheel check from outside the checkout: convert json → jsonld → json (quickstart V7)
```

**Gate result**: PASS. One limitation is justified in Complexity Tracking: the general reader is
unavailable on Python 3.9 and without the extra. The post-design re-check is also PASS (the
"Post-design" columns above).

## Project Structure

### Documentation (this feature)

```text
specs/011-jsonld-mapping/
├── spec.md                         # Feature spec (clarified)
├── plan.md                         # This file
├── research.md                     # Phase 0: decisions R-01..R-17 (per-property table in R-03)
├── data-model.md                   # Phase 1: context, scopes, terms, mapping entries, reader states
├── quickstart.md                   # Phase 1: portal/maintainer/tool walkthrough + V1..V8
├── contracts/
│   ├── fhr.context.jsonld          # Draft JSON-LD 1.1 context (prototype-tested)
│   ├── vocabulary.md               # terms.ttl / TERMS.md format; w3id .htaccess text
│   ├── mapping-table.schema.json   # mappings/fhr-jsonld-dcmi.yml format (JSON Schema 2020-12)
│   └── cli.md                      # .jsonld in bioheaders: dispatch, writer bytes, readers, errors, API
├── checklists/
│   ├── requirements.md             # Spec quality checklist
│   └── traceability.md             # FR/SC → tasks trace (from /speckit-tasks)
└── tasks.md                        # Phase 2 (/speckit-tasks)
```

### Source Code (both repositories)

```text
FAIR-bioHeaders-Specification/                          (this repository)
├── schemas/core.yaml                       # + prefixes sdo/fhr/xsd, default_prefix fhr, slot_uri/class_uri, annotations, sha2 uri
├── fhr_linkml.yml                          # + the same for FHR-only slots and classes; descriptions from fhr.json
├── jsonld/
│   ├── fhr.context.jsonld                  # generated (make_jsonld.py), committed
│   └── terms.ttl                           # generated FHR vocabulary
├── mappings/
│   ├── fhr-jsonld-dcmi.yml                 # curated table: 45 paths × JSON-LD term + DCMI + kind (US2)
│   └── mapping-table.schema.json           # copy of contracts/mapping-table.schema.json
├── docs/
│   ├── JSONLD.md                           # usage, rules J1..J7, losses, publication
│   ├── TERMS.md                            # generated vocabulary page (w3id default target)
│   ├── MAPPINGS.md                         # becomes a profile index: MIxS + JSON-LD/DCMI
│   └── FORMAT.md, README.md                # links
├── examples/
│   ├── example.fhr.jsonld                  # generated from example.fhr.json (writer contract)
│   └── minimal.fhr.jsonld
├── conformance/
│   ├── valid/*.jsonld, invalid/*.jsonld    # J1..J7 vectors
│   └── manifest.json                       # + jsonldSpecification, rules J1..J7, format "jsonld"
├── scripts/
│   ├── make_jsonld.py                      # generate context/vocabulary/TERMS.md/examples; --check; --schemaorg-subset
│   ├── make_conformance.py                 # + JSON-LD vectors
│   ├── check_conformance.py                # + jsonld format via fhr-convert; --skip-format
│   └── check_release.py                    # + context copy identical
├── tests/
│   ├── fixtures/schemaorg-v30.1-subset.json  # pinned term/domain subset (CC BY-SA 3.0 attribution)
│   ├── fixtures/dcmi-terms-2020-01-20.txt     # pinned DCMI term list (CC BY 4.0 attribution)
│   ├── test_jsonld_context.py              # generation, injectivity, every fhr.json key a term
│   ├── test_jsonld_mappings.py             # SC-002
│   ├── test_jsonld_roundtrip.py            # SC-001
│   └── test_jsonld_vocabulary.py           # SC-003, FR-002
├── requirements-jsonld.txt                 # PyLD==3.3.0 (dev/test only)
├── .github/workflows/validate-specification.yml  # install requirements-jsonld.txt; run make_jsonld --check; --skip-format jsonld for fhr==0.3.3
└── CHANGELOG.md, AGENTS.md                 # repository map: jsonld/, mappings/

FAIR-bioHeaders-Tools/                      (local checkout ../FHR-File-Converter)
├── bioheaders/
│   ├── __init__.py                         # fhr.input_jsonld / output_jsonld
│   ├── jsonld.py                           # CONTEXT, KNOWN_CONTEXT_URLS, to_jsonld, from_jsonld, unmapped_keys, reverse map, offline loader
│   ├── fhr.context.jsonld                  # byte-identical copy of FAIR-bioHeaders-Specification jsonld/fhr.context.jsonld
│   └── cli.py                              # FORMATS/FORMAT_NAMES + jsonld; --ignore-unknown-terms; help text
├── examples/example.fhr.jsonld, minimal.fhr.jsonld   # byte-identical with FAIR-bioHeaders-Specification
├── tests/jsonld_test.py                    # writer bytes, canonical/general readers, CLI, offline, round trips
├── pyproject.toml                          # include context; extras jsonld = pyld (py>=3.10); dev pyld
├── README.md, CHANGELOG.md, AGENTS.md      # JSON-LD format, extra, API
└── .github/workflows/pytest.yaml           # install with --extras jsonld
```

**Structure Decision**: The work spans two existing repositories and creates no new project
(research R-01).
- The semantic source (LinkML), the generated context and vocabulary, the curated mapping table,
  the rules and the vectors live in FAIR-bioHeaders-Specification.
- The behaviour lives in FAIR-bioHeaders-Tools as one module, `bioheaders/jsonld.py`, behind the
  existing format dispatch.
- The w3id `terms` registration is a text artefact here (contracts/vocabulary.md). Adam or David
  submits it.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Toolkit V (feature parity on the gated Python versions): the general JSON-LD reader needs the optional `jsonld` extra and Python 3.10 or later | US3 must read JSON-LD that FAIR-bioHeaders did not write, for example compacted differently or expanded. That needs a conformant JSON-LD 1.1 expansion, and PyLD 3 is the maintained Python implementation; it requires 3.10. On 3.9 the writer and the canonical reader, which are the whole MVP, work with no dependency | Making PyLD a hard dependency adds `lxml` and two other packages to every install and drops 3.9. PyLD 2.0.4 runs on 3.9, but its compaction mis-handles property-scoped contexts and it has no dropped-term callback (prototype, R-11). A home-made expander would be a second implementation of a W3C algorithm |
| The context is embedded in every written document instead of referenced by URL | Conformant JSON-LD processors must reject raw GitHub's `text/plain` (JSON-LD 1.1 API, LoadDocumentCallback), and the versioned-URL policy is open (spec#44). Embedding keeps documents valid offline and immutable | A raw-main URL reference changes old documents' meaning when main changes, and strict processors cannot load it. A w3id alias reference depends on an unagreed policy and on a release containing the file (R-09) |

## Phase outputs

- **Phase 0**: [research.md](research.md). All unknowns are resolved. The per-property mapping is
  R-03, and the draft context was validated in a prototype with PyLD 3.3.0 and 2.0.4.
- **Phase 1**: [data-model.md](data-model.md), [contracts/](contracts/) (context, vocabulary,
  mapping-table schema, CLI) and [quickstart.md](quickstart.md). The constitution was re-checked
  after design (table columns above): PASS.
- **Phase 2**: [tasks.md](tasks.md) (from `/speckit-tasks`), with
  [checklists/traceability.md](checklists/traceability.md).

## Maintainer decisions (Adam, 2026-10-10)

The four open questions are settled by following established practice. Tasks T044 to T048
implement them.

1. **Dereferenceable context and vocabulary** (W3C JSON-LD 1.1; W3C *Best Practice Recipes
   for Publishing RDF Vocabularies*):
   - Serve each release's context at a **versioned** URL
     (`https://w3id.org/fair-bioheaders/fhr/vX.Y.Z/context.jsonld`) with
     `Content-Type: application/ld+json` and CORS.
   - Serve the **unversioned** term namespace `https://w3id.org/fair-bioheaders/terms#` with
     content negotiation: HTML for people, Turtle and JSON-LD for software.
   - Host both on GitHub Pages, which sends these types and CORS headers, behind w3id.org
     redirects.
   - Keep the embedded context as the offline fallback. Raw-main remains the canonical
     source of the files; Pages only serves them with correct media types.
2. **Bioschemas Dataset profile.** The FHR core stays small, so no required fields are added.
   - The JSON-LD writer maps what FHR has: `genome`→`name`, `documentation`→`description`,
     `reuseConditions`→`license`, identifiers and accessions→`identifier`.
   - `keywords` and the landing-page `url` come from an optional export context, shared with
     #56.
   - `dct:conformsTo` the Bioschemas Dataset profile is emitted only when every minimum
     property is present.
3. **`documentation`** maps to `sdo:description` (and `dcterms:description`) when the value is
   text. When it is an absolute URL it maps to `sdo:subjectOf`.
4. **Author type.**
   - Infer from the identifier: an ORCID gives `sdo:Person`, a ROR ID gives
     `sdo:Organization`, and anything else gives `fhr:Agent` ("not classified").
   - Add an optional author `type` field with DataCite's `nameType` values (`Personal`,
     `Organizational`) as an additive v0.4 schema change on `release-v0.4` (T047), so #56's
     DataCite export gets `nameType` too.

**As implemented in the MVP** (research R-18): decisions 2, 3 and 4 are in (T046, T048), with
two corrections found while implementing. The Bioschemas Dataset minimum list includes `@id`,
so the export context also takes the dataset `id`; and Dataset 1.1 is still a draft, so
`conformsTo` names `Dataset/1.0-RELEASE`. The author `type` field (T047) and the Pages and w3id
publication of decision 1 (T044, T045) are not done.

Maintainer actions, which are not tasks:
- submit the w3id `terms` rule (text in [contracts/vocabulary.md](contracts/vocabulary.md));
- confirm SC-004 (David, as the #56 owner);
- release both packages.
