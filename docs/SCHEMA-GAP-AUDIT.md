# Schema-contract gap audit

This page records the seven schema-contract questions found in the #150 review, what
the published contract says, what the current schemas and toolkit actually do, and
what remains. It is a status and decision log, not a second specification: the
normative rules stay in [FORMAT.md](FORMAT.md), [SCHEMA-VERSIONS.md](SCHEMA-VERSIONS.md),
[JSONLD.md](JSONLD.md), [FHP.md](FHP.md) and [FHGFF3.md](FHGFF3.md).

- Source review: [#150](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/150)
  (closed; documented in [#152](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/pull/152)).
- Follow-up tracker: [#163](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/163).
- Last audited: 2026-10-22, against released specification **v0.4.1** (schemas from
  v0.4.0), released toolkit **0.8.1**, and toolkit `main` after Tools#91–#94 (not yet
  released). GAP-1 taxon decision recorded 2026-10-28 ([#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189)).

## Status legend

| Status | Meaning |
| --- | --- |
| Done | The decision is recorded and the behaviour needed for the current contract is implemented. |
| Documented | The intended behaviour is stated, but a tooling or test gap remains. |
| Release-gated | Implemented on toolkit `main` but not in a release; dependent spec changes wait for that release. |
| Next major | A schema change would invalidate records valid under the current `schemaVersion`; it belongs to the next major contract. |
| Decision pending | Maintainers must choose before the next major can be drafted. |

## Findings

| ID | Finding | Normative text | Current schema | Current toolkit | Status | Target |
| --- | --- | --- | --- | --- | --- | --- |
| GAP-1 | Required fields accept empty values (`genome: ""`, `taxon: {}`, `metadataAuthor: []`, `assemblyAuthor: [{}]`, `version: ""`) | [Required values are non-empty](SCHEMA-VERSIONS.md#required-values-are-non-empty) | FHR 2.0 / FHP 1.0 / FHGFF3 1.0 accept the empty forms | `main` warns without changing exit status (Tools#93); 0.8.1 does not warn | Release-gated (warnings) + Next major (constraints) | Warnings in 0.8.2; `minLength`/`minItems`/author name in the next major; `taxon.uri` with an NCBI Taxonomy or ITIS identifier required in the next major ([decided, #189](#gap-1-taxon-identifier-decided-189)) |
| GAP-2 | `nameType: Organizational` with an ORCID iD validates | [JSON-LD, author typing and the accepted combination](JSONLD.md#json-ld) (J7) | Accepted under 2.0; no coupling between `nameType` and `uri` | Types from explicit `nameType` first, then ORCID/ROR/Agent (Tools#74/#79) | Documented + Decision pending | Decide in the next major whether to forbid the combination |
| GAP-3 | G1 `##gff-version` grammar is under-specified | [FHGFF3 G1](FHGFF3.md) | Grammar is documentation only; schemas do not parse line 1 | `main` enforces the full grammar (Tools#91); 0.8.1 checks only the prefix | Release-gated | Ship in 0.8.2; then enable the deferred near-miss vectors |
| GAP-4 | J1 and J4 disagree on root export terms (`@id`, `keywords`, `url`, `conformsTo`) | [JSON-LD reading rules](JSONLD.md#json-ld) | No schema effect | Canonical J1 sets them aside with a warning; J3/J4 reject them | Done (intended difference documented) | No change; keep the decision test/docs cross-check |
| GAP-5 | Nothing asserts that schemas on `main` equal the current release tag | [Schema files on main](SCHEMA-VERSIONS.md#schema-files-on-main) | No schema effect | Byte-identity test; a missing tag now fails unless `preRelease` explicitly names it, and an existing tag clears the marker | Done | No further change |
| GAP-6 | `format` (`date`, `uri`) is an annotation unless the validator opts in | [format is asserted](SCHEMA-VERSIONS.md) | `format` declarations; some URI fields also have anchored patterns | Toolkit uses `FormatChecker`; a bare draft 2020-12 validator does not | Done (every declared format tested) | No further change; consider patterns only in a major |
| GAP-7 | NaN and infinities are not ruled out for numeric statistics | [R13](FORMAT.md) | `minimum`/`maximum` do not catch NaN | `main` rejects them explicitly with a field path (Tools#92); 0.8.1 relies on serialisation failure | Release-gated | Ship in 0.8.2; keep the invalid vectors |

## Decisions

- **GAP-1:** required values are normative non-empty values, but the 2.0 schemas cannot
  express that without invalidating records. Warnings are the correct 2.x behaviour;
  constraints wait for a major. The taxon part is superseded by the
  [#189 decision](#gap-1-taxon-identifier-decided-189): `name` or `uri` is no longer
  enough in the next major; `uri` is required.
- **GAP-2:** the combination stays accepted under 2.0 because rejecting it would
  invalidate valid records. `nameType` wins for typing. The next major should decide
  whether ORCID plus `Organizational` is forbidden; the recommended answer is yes,
  because ORCID identifies people.
- **GAP-4:** the difference is intentional: J1 is writer output with a documented
  export-annotation allowance; J3/J4 have no writer contract and must reject unknown
  terms rather than drop them silently.
- **GAP-5:** a missing release tag is skipped only when `preRelease` explicitly
  names it. A tag that exists but lacks a schema file fails, and a stale marker
  fails once the tag exists. A typo in `current` is therefore not indistinguishable
  from a shallow checkout.
- **GAP-6:** conforming validators must assert `format`. The test suite now exercises
  every declared `format` field with a malformed and a valid value; do not claim a
  record valid from a validator that ignores it.
- **GAP-7:** JSON Schema cannot express NaN/infinity, so R13 remains a validator rule
  even after the next major.

### GAP-1: taxon identifier (decided, #189)

**Decided (2026-10-28, [#189](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/189)):
the next major requires `taxon.uri` with an NCBI Taxonomy or ITIS identifier.** The
co-maintainers chose this over GAP-1's earlier "non-empty `name` or non-empty `uri`"
rule, which still allowed a file with no taxonomy identifier. This is a next-major
decision only: `fhr.json` 2.0, `fhp.json` 1.0 and `fhgff3.json` 1.0, their
`schemaVersion`s and today's validation behaviour do not change.

Proposed rule for the next major of FHR, FHP and FHGFF3 (to be made exact when the
contract is drafted):

- `taxon` requires `uri` (`required: [uri]`, `minLength: 1`); `name` stays optional and,
  when present, is non-empty (`minLength: 1`).
- `taxon.uri` must identify an NCBI Taxonomy or an ITIS taxon in one of the recognised
  forms, checked by an anchored `pattern` (an `anyOf` of the two):
  - NCBI Taxonomy: `https://identifiers.org/taxonomy:<taxid>`, the form the 2.0
    pattern already requires (`^https://identifiers\.org/taxonomy:[0-9]+$`).
  - ITIS: `https://www.itis.gov/servlet/SingleRpt/SingleRpt?search_topic=TSN&search_value=<TSN>`.
    identifiers.org has no ITIS namespace, so there is no identifiers.org form to reuse.
    Whether to accept other forms as well (`https://bioregistry.io/itis:<TSN>`, the ITIS
    LSID `urn:lsid:itis.gov:itis_tsn:<TSN>`, or NCBI's OBO PURL
    `http://purl.obolibrary.org/obo/NCBITaxon_<taxid>`) is a drafting choice; accepting
    fewer forms keeps comparison and JSON-LD `@id`s simple.
- Rank is not checked by the schema. Whether the identifier is a real, current taxon
  needs a lookup and stays a toolkit check, not a schema rule.

Why this does not conflict with "unknown values stay absent": NCBI Taxonomy has taxa
for unclassified and environmental material, so a file about such material can still
carry a true identifier instead of a placeholder. Examples, checked against the NCBI
Taxonomy E-utilities on 2026-10-28: `12908` unclassified sequences, `32644`
unidentified, `155900` uncultured organism, `408169` metagenomes (the parent of the
metagenome taxa, such as `256318` metagenome and `410658` soil metagenome). ITIS has no
equivalent entries, so such files use the NCBI form.

Points to keep in mind when drafting:

- NCBI taxids and ITIS TSNs are separate numbering systems and are not
  interchangeable: the same number names different taxa (NCBI `285` is
  *Comamonas testosteroni*, ITIS TSN `285` is *Escherichia coli*). A validator must
  read the system from the URI form, never from the number alone, and tools must not
  convert one to the other by number.
- ITIS covers microbes poorly. Its kingdoms are Bacteria, Archaea, Protozoa, Chromista,
  Fungi, Plantae and Animalia (no viruses), and on 2026-10-28 it had no entry for
  SARS-CoV-2 (NCBI `2697049`) or *Nitrosopumilus maritimus* (NCBI `338192`). Writers
  should prefer NCBI Taxonomy; ITIS is for taxa that a producer already identifies there.
- FHGFF3 compares `taxon.uri` with the native `##species` line by NCBI taxid
  ([FHGFF3.md](FHGFF3.md#native-directives)). An ITIS `taxon.uri` has no NCBI taxid to
  compare, so the next FHGFF3 major must say that the comparison is skipped (or warns)
  for ITIS.
- INSDC requires an NCBI taxid specifically. The base contract accepts ITIS, so the
  draft INSDC profile ([#190](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/190))
  should require the NCBI form; see the
  [INSDC coverage review](insdc-coverage.md) rows A.d and SA.T2.

Migration notes for the next major:

- Every file without `taxon.uri` must add one. Files that already carry a 2.0
  `https://identifiers.org/taxonomy:<taxid>` value need no change to `taxon`.
- Files whose taxon is unclassified or environmental use the matching NCBI taxon above
  rather than leaving `uri` out.
- One idea for the toolkit, not a commitment: suggest candidate NCBI taxids from
  `taxon.name` during migration, for the producer to confirm. It must never fill in an
  identifier silently.

Sources: NCBI Taxonomy records via E-utilities `esummary` (db=taxonomy); identifiers.org
registry, namespace `taxonomy` (MIR:00000006, pattern `^\d+$`; `https://identifiers.org/taxonomy:9606`
resolves to the NCBI Taxonomy browser) and no `itis` namespace; Bioregistry prefixes
`ncbitaxon` (synonym and identifiers.org mapping `taxonomy`) and `itis` (pattern
`^\d+$`, URI format `https://www.itis.gov/servlet/SingleRpt/SingleRpt?search_topic=TSN&search_value=$1`);
ITIS web services (`getLSIDFromTSN`, `getKingdomNames`, `searchByScientificName`).

## Release-gated work (toolkit 0.8.2)

The following are on toolkit `main` but not in 0.8.1:

- full G1 grammar enforcement (Tools#91);
- explicit R13 rejection with a field path (Tools#92);
- empty-required warnings (Tools#93).

After 0.8.2 is published:

- enable the deferred G1 invalid vectors (`fhgff3-version-30`, `-3x`, `-3-1`) in
  [`scripts/make_conformance.py`](../scripts/make_conformance.py) and
  [`tests/test_conformance.py`](../tests/test_conformance.py);
- bump the converter pin in the validation workflow and remove the “deferred” notes;
- re-run the conformance suite with the released converter and confirm agreement.

Do not enable those vectors before the release: Spec CI runs the released toolkit and
would go red.

## Next-major proposal outline

A new major `schemaVersion` is required because these constraints invalidate records
that are valid under 2.0. The proposal should specify, per type:

- `minLength: 1` on required strings (`genome`, `version`, FHP `proteome`, FHGFF3
  `annotation`, author `name`);
- `minItems: 1` on required author arrays;
- author `name` required and non-empty;
- taxon requires a non-empty `uri` that identifies an NCBI Taxonomy or ITIS taxon
  ([decided, #189](#gap-1-taxon-identifier-decided-189)); `name` optional, non-empty if present;
- the GAP-2 decision (forbid ORCID + `Organizational`, or keep it documented);
- R13 as a validator requirement, not a substitutable schema keyword;
- no change to the documented J1/J4 difference unless a concrete interoperability
  need appears.

Generate from LinkML, update `schemas/versions.json`, baselines, examples and vectors,
add valid/invalid vectors for every new constraint, and write a
`SCHEMA-CHANGES-<release>.md` migration note. Reconcile the field set with the
[INSDC coverage review (#157)](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/157)
before freezing the contract. Never rewrite v0.4.x files, examples, vectors or tags.

## Maintenance

When a finding changes state:

1. Update its row and the decision entry.
2. Link the implementing PR and the test/vector that proves it.
3. Link a new release line instead of editing released artifacts.
4. Keep the “Last audited” line and the referenced release/toolkit versions current.
