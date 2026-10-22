# Metadata crosswalks and citation profiles (draft)

Proposal for joint maintainer review under [#56](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/56).
Profile version `0.1.0-draft.1`. This is an incomplete PR foundation, not an
adopted or released mapping suite. “Official” would mean maintained and approved
by FAIR BioHeaders, not endorsement by an external standards body.

## What is available now

The existing [canonical JSON-LD/DCMI table](../../mappings/fhr-jsonld-dcmi.yml),
[MIxS projection](../MAPPINGS.md), and [one-way schema.org export](../SCHEMAORG-EXPORT.md)
remain separate contracts. Their implementations are not re-created here.
The draft adds a scoped resource model, separate supplemental context schema,
a root-field handling inventory, a qualified-DC fixture, and tests of that
fixture's subjects, dates, identifiers and omissions. There is no new exporter.

| Intended use | Profile direction | Current state |
| --- | --- | --- |
| Resource discovery / descriptive metadata | Qualified DCMI Terms (2020-01-20), preserving source/context alongside the graph | Draft assembly fixture and root-field inventory only. |
| Dataset DOI deposit through DataCite | Assess schema 4.7; XML and REST request envelopes separately | Planned; no deposit-ready output or pinned XSD bundle. |
| Dataset/database deposit through Crossref | Assess deposit XSD 5.5.0 | Planned; dataset/container/deposit context still to specify. REST retrieval JSON is not the deposit format. |
| Publish an already assigned ARK | Select a metadata binding, resolver and persistence policy; assess ERC separately | Planned; no minting or assignment inferred. |
| Ordinary assembly citation | Classic BibTeX `@misc` | Planned; tool/style/escaping/rendering matrix remains to implement. |
| Dataset-aware bibliography | Separate BibLaTeX `@dataset` | Planned; backend/style versions remain to select and test. |

The machine-readable delivery matrix is
[`profile-status.yml`](../../mappings/proposals/profile-status.yml). Candidate
versions are references for review, not claims that adapters validate those
formats. The ARK reference is a dated Internet-Draft, explicitly work in progress.

## Resource model and provenance

The first proposed profile describes **one assembly resource**. Keep four
subjects distinct: the assembly, its metadata record, a related publication,
and the specification/software. No author's name, date or identifier moves
between these subjects merely because it appears in the same file.

- `assemblyAuthor` supplies assembly creators; `metadataAuthor` supplies creators
  of the separately identified metadata record. Preserve order, full names,
  identifiers and optional `nameType` in the source; never split names or infer
  a person/organization class. The RDF example uses generic `dcterms:Agent` nodes.
- `dateCreated` is assembly creation. `publicationDate`/`publicationYear` come
  from context and must agree when both are supplied. Neither is defaulted from
  assembly creation, file timestamps or metadata authorship.
- `genome` is not automatically a citation title. Context supplies an explicit
  title. The resource version stays in the source; a literal `version` is not a
  resource-valued `dcterms:hasVersion`/`isVersionOf` assertion.
- `scholarlyArticle` identifies a related article, not the assembly. A generic
  relation does not establish that the article describes this assembly. An
  explicit resource DOI equal to that article DOI is a scope conflict here.
- `accessionID.name` may name a repository. Do not derive an accession from it,
  classify arbitrary strings as DOIs, or turn a supplied SeqCol/file digest into
  a registered identifier. Generic links remain generic relations.

These are proposed adapter decisions. No FHR/FHP/FHGFF3 field, enum, meaning,
requiredness, checksum rule, canonical context, vocabulary or schema version
changes in this PR. Future structured-voucher adoption is separate (#139).

## Separate context, not extra FHR fields

[`assembly-export-context.schema.json`](../../mappings/proposals/assembly-export-context.schema.json)
is a new **proposed export-context contract**, not an extension to `fhr.json`.
It requires the draft profile version, `resourceKind: assembly`, distinct resource
and metadata-record IRIs, and an explicit title. Publisher, publication date/year
and a resource DOI are optional *known* assertions. Absence means unknown;
empty/null assertions and undeclared context keys are rejected. Optional fields
here do not imply optional registration fields in another target profile.

The helper validates structure, this draft's fixed FHR v0.4.0 / schemaVersion
`"2.0"` source identity, and context conflicts. It does not validate the source
record's conformance or determine registration readiness. Raw-main, other
releases and other header types are unsupported by this initial profile; none
silently falls back to v0.4.0. Use the
ordinary source validator separately. It rejects duplicate JSON keys, invalid
JSON constants, equal record/resource IRIs, conflicting publication date/year,
and an article DOI reused as the assembly DOI or resource IRI. DOI comparisons
are case-insensitive; resource IRIs recognize HTTP(S) `doi.org` and `dx.doi.org`
resolver paths, including percent-encoded paths, without network lookups. This
check applies even when optional `resourceDOI` is absent.
No source/context conflict is silently overwritten. Publisher identities and
name classifications are not guessed. No network operation or registration
occurs.

```sh
python scripts/check_mapping_context.py tests/fixtures/mapping-proposal/context.json \
  --source tests/fixtures/mapping-proposal/source.json
python -m unittest discover -s tests -p test_mapping_proposal.py -v
```

## Qualified DC and retained detail

The curated [`assembly-dcmi.yml`](../../mappings/proposals/assembly-dcmi.yml)
records every FHR v0.4.0 **root field**, with source/container cardinality,
subject, condition, transformation and loss/unsupported reason. It is a handling
inventory, not executable mappings or unconditional LinkML `exact_mappings`.
Nested details retain the existing canonical table and the original source;
complete per-target nested rules remain to review. Its conditional rules do not
assert SKOS equivalence. Root cardinality measures field/container presence,
not the number of array items.

The [worked bundle](../../tests/fixtures/mapping-proposal/) contains an unchanged,
schema-valid rich source example; explicit context; a manually curated Turtle
graph; and a report. Checksum/identifiers in this synthetic source are not
file-backed verification results. `example.org` subjects and publisher are
illustrative and no resource DOI is assigned.

The graph separates assembly creators from metadata-record creators, applies
creation/issue dates to the assembly, and applies FHR conformance only to the
metadata record. Rights text is a labelled `dcterms:RightsStatement`, not an
inferred license URI. Dataset/agent/rights nodes retain resource-valued DCMI
relationships instead of treating every target as a text field. The fixture
retains supplied ORCID strings as identifiers of its corresponding agents.

RDF creator/relation triples do not retain array order or the full source
structure. The graph alone is **not** lossless. `source.json` and `context.json`
remain the preservation layer: keep names, order, classifications, typed nested
statistics, software parameters, source versions and identifiers there before
building subsequent adapters. Do not use serialized Simple DC as an intermediate
store. No Simple DC output or reverse mapping is implemented here.

The older canonical table declares legacy version metadata and its format uses
a numeric source-schema version. This proposal explicitly names released FHR
schemaVersion `"2.0"`; it does not silently reinterpret or edit that historical
format. Review version-metadata migration separately when extending that table.

## Header-family coverage and FHT

| Header type | Released contract | Mapping proposal scope |
| --- | --- | --- |
| FHR | v0.4.0 / schemaVersion `"2.0"` | Initial assembly fixture only; not an adopted exporter. |
| FHP | v0.4.0 / `"1.0"` | Not yet profiled; protein-set origin and contributor roles need review. |
| FHGFF3 | v0.4.0 / `"1.0"` | Not yet profiled; annotation creators and genome relationships need review. |
| FHT | No shared release | Blocked on the adopted transcriptome contract and versioned schema. |

Checked 2026-10-20: FHT issues [#6](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/6)
and [#7](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/7) remain open.
Its [PR #12](https://github.com/FAIR-bioHeaders/FHT-Specification/pull/12) updates
AGENTS guidance; it is not a transcriptome-contract adoption. Do not import
legacy FHT fields or claim RNA/cDNA mappings yet. This does not block review of
the initial FHR assembly profile. Do not reuse assembly-author roles for FHP,
FHGFF3 or FHT by assumption.

## Remaining work before adoption

1. Obtain joint review of scope, subject choices, context schema, DCMI layer and
   comparison with direct per-target adapters using the same fixture bundle.
2. Specify all nested-field handling and loss reports for every target; implement
   deterministic adapters with missing/unknown/conflict/special-character cases.
3. Pin complete DataCite/Crossref validation artifacts and request/deposit
   contracts; add XML/REST examples and negative registration-context fixtures.
4. Define ARK binding/resolver/assigned-name policy, safe existing-identifier
   examples, optional ERC serialization, and persistence responsibilities.
5. Implement citation-only BibTeX first and separately test BibLaTeX. Select
   versions/styles, parse/render citations, and cover corporate names, Unicode,
   braces, ORCID loss and escaping. The optional metadata-bearing note envelope
   stays an experiment until extraction/round trips and tool-loss behavior pass.
6. Review family-specific scopes as their contracts allow. Integrate tested
   adapters into Tools, then provide the approved guidance to
   [website #29](https://github.com/FAIR-bioHeaders/fair-bioheaders.github.io/issues/29).
7. Adopt and publish a versioned profile release; do not close #56 or describe
   this draft as official, deposit-ready, endorsed or complete.

## Primary references checked 2026-10-20

- [DCMI Terms, 2020-01-20](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/2020-01-20/).
- [DataCite 4.7](https://schema.datacite.org/meta/kernel-4.7/).
- [Crossref 5.5.0](https://www.crossref.org/documentation/schema-library/metadata-deposit-schema-5-5-0/)
  and [dataset record guide](https://www.crossref.org/documentation/schema-library/markup-guide-record-types/datasets/).
- [ARK Internet-Draft, 2026-05-08](https://arks-org.github.io/arkspec/draft-kunze-ark.html)
  (work in progress; select/pin a binding before claiming support).
- [BibTeX documentation](https://www.bibtex.org/Using/) and
  [BibLaTeX package/manual](https://ctan.org/pkg/biblatex).

No registration service, DOI resolver, ARK minting service or live vocabulary is
called by tests. RDF terms are checked against the repository's existing pinned
DCMI term inventory; fixture schema/context checks are offline.
