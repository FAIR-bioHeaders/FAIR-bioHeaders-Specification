# Proposed shared FHT typed HTML microdata binding

**Draft v0.7.0 publication candidate, not a released binding or runtime support.**
This document incorporates the accepted owning binding at
[`4ddda69cbcbb3920a06ab657173c0198672cd7bf`](../drafts/fht/upstream/docs/FHT-MICRODATA.md)
with the explicit shared selector, API and provenance transitions below. The
immutable source document SHA-256 is
`a971f3848a3b845fb22765239ecf735a43c3d6062c876483492645b474176666`.
Its field, typing, ordering, visibility and validation meanings are retained;
F1–F7 are shared review labels, not additional field constraints.

The accepted owning contract SHA-256 is
`b62c4e227042e162b43d2c461cfe6c3ece3806636ca88a4cf9b0b2f902fb1fc3`.
The proposed root contract is [fht.json](../fht.json), SHA-256
`2a20528d609f36c9f936cf9084fe7f2994154b2eb5cf4c10665a6aa848cb86d0`.
Tests compare every non-selector resolved validation constraint; only the
selector forms and annotations change. No URI below is minted or advertised
as live by this branch. Final joint acceptance and the publication gates in
[FHT-PUBLICATION-CANDIDATE.md](FHT-PUBLICATION-CANDIDATE.md) remain separate.

## F1 — scope and itemtype

Exactly one FHT record scope is required. No conflicting FHR/FHP/FHGFF3 scope,
FHT owning-draft scope or family itemtype token is allowed. FHR identity never
identifies an FHT record. The proposed writer uses
`https://w3id.org/fair-bioheaders/fht/v0.7.0` as its `itemtype`.

The reader recognizes shared raw-main, shared raw-tag and versioned w3id family
aliases before detecting conflicts; an unknown version cannot evade that check.
A recognized FHT itemtype must resolve to the same proposed FHT1.0 contract.
The record's ordinary `schema` property is separately selected under F2.

## F2 — selectors and reference states

The proposed v0.7.0 registry permits these FHT selectors:

- shared raw-main `.../FAIR-bioHeaders-Specification/main/fht.json` (and the
  historical `FHR-Specification` namespace alias) selects the reader's current
  FHT contract under V1;
- shared raw-tag `.../v0.7.0/fht.json` selects the registered immutable release
  under V2, and `https://w3id.org/fair-bioheaders/fht/v0.7.0` with optional
  trailing slash selects it under V3;
- a named shared release without FHT, or an unknown shared FHT version, is
  unsupported under V4. Never substitute current FHT or the draft;
- raw tags of the owning `FHT-Specification` repository remain generic V5
  fallback-to-FHR citations, not shared FHT release aliases. This FHT-only HTML
  reference refuses such a record. The separately opted-in historical V7 draft
  uses owning raw-main; it is not another selector for this shared binding.

The schema version remains the string `"1.0"`. No remote schema is fetched.
A supplied schema object must equal the local selected root contract.

While `current = preRelease = v0.7.0`, both APIs require
`allow_candidate=True` and successful reads report unpublished candidate status.
Clearing the marker without an actual byte-matching v0.7.0 tag is refused. With
that exact tag, the reference reports **tag bytes verified**, without claiming
that a GitHub Release, joint acceptance or publication has been verified. The
visible page paragraph, default title and read diagnostic reflect this state.
These are reference states, not a way to bypass the release gates.

## F3 — properties and objects

`itemprop` names the actual field. An object uses its own `itemscope` and
`data-fhr-type="object"`; nested properties follow the selected contract
recursively. Requiredness, cardinality and allowed keys come from the contract,
not from this table. The nine required root fields do not make taxon name/URI
members required. Metadata and assembly authors retain their distinct roles.

<!-- BEGIN generated root bindings -->
| Field | Contract shape | Required | Binding |
| --- | --- | --- | --- |
| `accessionID` | AccessionID object | no | typed object scope |
| `assemblyAuthor` | array of AssemblyAuthor | no | ordered typed container |
| `assemblySoftware` | array of Software | no | ordered typed container |
| `assemblyType` | enum string | yes | typed scalar |
| `checksum` | string | yes | typed scalar |
| `completeness` | Completeness object | no | typed object scope |
| `dateCreated` | string | yes | typed scalar |
| `derivedFrom` | array of DerivedFrom | no | ordered typed container |
| `documentation` | string | no | typed scalar |
| `funding` | string | no | typed scalar |
| `identifier` | array of string | no | ordered typed container |
| `instrument` | array of string | no | ordered typed container |
| `libraryStrategy` | string | no | typed scalar |
| `metadataAuthor` | array of MetadataAuthor | yes | ordered typed container |
| `moleculeType` | enum string | no | typed scalar |
| `relatedLink` | array of string | no | ordered typed container |
| `reuseConditions` | string | no | typed scalar |
| `sample` | array of Sample | no | ordered typed container |
| `schema` | string | yes | typed scalar |
| `schemaVersion` | enum string | yes | typed scalar |
| `scholarlyArticle` | string | no | typed scalar |
| `sequencingRuns` | array of string | no | ordered typed container |
| `strandedness` | enum string | no | typed scalar |
| `taxon` | Taxon object | yes | typed object scope |
| `transcriptome` | string | yes | typed scalar |
| `transcriptomeSynonym` | array of string | no | ordered typed container |
| `version` | string | yes | typed scalar |
| `vitalStats` | VitalStats object | no | typed object scope |
| `voucherSpecimen` | string | no | typed scalar |
<!-- END generated root bindings -->

`dateCreated` is resource creation, not sample collection. `sample` stays an
ordered array of supplied tissue/stage/condition/strain assertions, not a
complete BioSample record or proof of uniform pooled identity. BioSample,
BioProject and SRA URLs belong in `relatedLink`, distinct from file identifiers.
Supplied protocol/kit text belongs in existing `documentation`, and actual
protocol URLs in `relatedLink`; no new kit/libraryProtocol field is introduced.
Retain the existing read/read-1 strandedness convention. Unknown optional values
stay absent; HTML must not infer construction, parents or biological class.

## F4 — arrays and repeated properties

An ordered array uses `data-fhr-type="array"` and direct `itemprop="item"`
children. Preserve duplicates and order where the contract allows them. Object
items use their own object scope. Array containers cannot carry stray scalar
text or unlabelled children.

### Repeated properties

Repeated ordinary array properties form an ordered array. Repeated scalars or
repeated array containers produce invalid shapes, never last-value wins.
Property traversal does not turn an object's grandchildren into root properties.
First duplicated HTML attributes win under shared R9. Optional end-tag,
non-void self-closing-slash and inert subtree handling retain the accepted
reference behavior; the Python parser is not a general HTML5 browser engine.

## F5 — scalar types and representability

`data-fhr-type` identifies string, integer, number, boolean or null. Booleans
are not integers. Preserve integer zero, floating zero, Unicode, object key
order and array order. Integers beyond binary64 precision remain exact; the
browser receipt uses lossless integer token parsing and actual adjacent-integer
and object/type-collision controls. Untyped fallback uses the selected schema
for coercion before complete validation.

Literal CRLF/CR normalizes to LF before HTML tokenization; encoded `&#13;`
retains carriage returns. The writer uses character references so supplied CR
values survive. NUL and unpaired surrogates in standard values or the title
raise an HTML serialization error instead of being replaced. This is a binding
limit, not a new JSON/YAML field constraint. Omitted extension values need not
be HTML-representable; finite-number checks still apply to the entire record.

## F6 — validation and preserved metadata

Extract identity before coercion. Validate the full FHT Draft2020-12 contract
with format assertions and the shared bounded ECMA pattern adapter; reject
noncanonical standard checksum encodings and non-finite numbers. Apply the
accepted C1 arithmetic rule to complete exclusive integer BUSCO categories:
components must sum to total; absent counts are not zero. Parent roles remain
FHT/`filteredFrom` and FHR/`transcribedFrom` only; genome guidance alone does
not establish actual base extraction or a `transcribedFrom` link. No new self-parent
fixed-point rule or biological derivation inference is introduced.

A checksum in HTML is the original metadata value. Schema/arithmetic checks do
not verify sequence bytes, the HTML file's checksum or an unavailable parent.
The separate FASTA conformance lane verifies exact self/parent file identity.

Following M5, the writer omits top-level extensions, reports their keys through
its warning hook and a visible omission notice, and the reader rejects embedded
extension properties. Base-record round trips are lossless. Records containing
extensions retain their original JSON/YAML preservation copy; extension values
are not promoted to standard fields. There is no FHT JSON-LD serializer/context,
adopted DCMI projection or installed toolkit/website capability claim.

## F7 — visible values and inert content

The embedded data must be the readable value, without a second hidden copy.
The writer escapes labels, title and values; URLs remain text without scripts,
active links, fetching or user-controlled attributes. Preserve readable scalar
whitespace with `pre-wrap`, including scalar string list items.

The reader refuses the accepted binding's unsupported or concealed cases:

- `hidden`, inline `display:none`, `visibility:hidden/collapse` or
  `content-visibility:hidden` on a property, scope or ancestor; CSS comments
  separate tokens, so comments cannot conceal those declarations;
- unsupported inline escapes/quotes or unmatched comment terminators;
- scalar text from concealed descendants, or values in never-rendered
  `head`, `title`, `style`, `noscript`, `meta` or `link` content;
- attribute-only values from `meta[content]`, `link`, media/embed/iframe/object
  elements; a `data`, `meter` or `time` value differing from its shown text;
- active `href` schemes outside R14's http/https/ftp/urn/doi/info subset;
- `itemref` or multi-token `itemprop` that borrows or duplicates a visible value.

Direct `script` and `template` subtrees are inert: they create no record scopes,
properties or scalar text, including within typed arrays. Concealed markup
outside a property's scalar descendants does not supply metadata and is not
itself treated as a property. The reference does not fetch stylesheets, compute
the full CSS cascade or establish visibility in every browser. Its reader probes
RCDATA behavior (title/textarea markup stays text with character references
decoded) and refuses an incapable parser; it does not guess from a version number.
These accepted binding limits are stricter than generic M2 value extraction.

## Executable API and evidence

[`scripts/fht_microdata.py`](../scripts/fht_microdata.py) exposes:

```python
write_page(record, schema=None, *, allow_candidate=False, title=None, warn=None)
read_page(text, schema=None, *, allow_candidate=False, warn=None)
```

The seven [proposed counterpart triples](../examples/fht/) are synthetic. Frozen
owning examples and invalid fixture expectations remain byte-identical under
`drafts/fht/upstream/`; selector-adjusted in-memory negative tests verify the
shared reader's actual primary rejection reasons. The shared counterpart
manifest has new IDs and explicit source transformations, not rewritten old IDs.

```sh
python scripts/fht_publication.py --examples
python -m unittest discover -s tests -p test_fht_publication.py -v
FHT_PLAYWRIGHT_MODULE=/path/to/playwright node scripts/check_fht_publication_browser.mjs
```

Python3.13+ with the pinned requirements provides the tested RCDATA behavior;
Playwright1.65.0/Chromium independently extracts all seven visible tables and
checks exact integers/types without network requests. Reference evidence is
separate from B's installed arithmetic-capable/runtime/browser promotion and
joint package acceptance. The immutable owning DOM/typed implementation derives
from FHP `bc7110fedb6f05b52b1d2348b5b14a79b91b0637`; MPL-2.0 notices and the
family's historical/third-party provenance split remain unchanged.
