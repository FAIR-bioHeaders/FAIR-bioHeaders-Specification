# FHT typed HTML microdata — draft binding proposal

Adopted November 19, 2026: [D1–D3](FHT-DECISION-DOCKET.md)
retain optional field behaviour, reject duplicate parent entries and noncanonical
parent checksum encoding, and require complete BUSCO category counts to sum to
total. Arithmetic is a separate C1 semantic check, not expressible by this JSON
Schema contract. Missing counts are not zero. The reference reader/writer checks
arithmetic; older installed consumers remain a publication handoff. Four parent
expectations are accepted for file identity only, without changing fixture bytes.

This is an **unreleased proposal** for [#11](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/11),
against the owning FHT development contract, including the separately reviewed
`moleculeType: mixed` addition. The binding adds no schema fields and changes
no model or canonical JSON/YAML/FASTA bytes of its owning source, and establishes no toolkit or website
support. Shared publication, vocabulary/conformance adoption and runtime delivery
remain separate work. #11 remains open on those handoffs.

## Record identity and schema selection

The proposed draft itemtype is the owning development URL:
`https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json`.
Exactly one FHT scope is required, with no conflicting FHR/FHP/FHGFF3 record scope
or family itemtype token. FHR identity never identifies an FHT record. The
record's `schema` is a distinct ordinary property selecting its contract.

Under the existing V7 draft lane, the reference accepts only that owning raw-main
selector and the current string `schemaVersion: "1.0"`. This is a development
value, not a released version. The exact local schema bytes are recorded in
[`provenance.json`](../tests/fixtures/microdata/provenance.json), SHA-256
`4156353aa6d077fee2d2c69be4e17859b8e4f81bb10824f3c87f6701de196e7a`.
The digest is the pin. The owning-source commit is not stored as a second
constant: the reference resolves it from the checked-out history as the commit
that last changed `fht.json`, and accepts it only when the `fht.json` stored in
that commit hashes to the pinned digest (`owning_commit` in
`tests/fht_microdata.py`; a shallow clone is refused). Each read reports that
commit and digest. An earlier revision of this binding named
`8b178a02b01876953d0360bc9f46bd11a609b3c6`, a pull-request branch commit that
the squash merge left off `main` (the same bytes landed as `f908fec`); resolving
the commit from history means a squash merge cannot strand it again.
Re-anchoring after a schema change updates only the digest.
The current digest covers the Q4 follow-up (#52), which also requires a
nonblank name on supplied assembly authors.
No FHT release or fixed alias currently exists. Every release-tag/w3id selector,
unknown selector, wrong family and unavailable version is rejected; nothing is
substituted or fetched. This is rejection by an explicitly FHT-only draft
reference, not a change to the generic family V5/V7 route (which does not treat
unregistered FHT release forms as published FHT). Shared V4 release-selection
semantics apply only after actual publication. After publication, supported fixed selectors will need an
explicit reviewed registry and matching contract bytes, not guessed URLs.

## Family rules and properties

This proposal reuses shared
[M1–M5](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.6.0/docs/MICRODATA.md)
and [FORMAT R7/R9/R13](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.6.0/docs/FORMAT.md).
It does not redefine JSON-LD or a one-way discovery export. The DOM/tree and typed
container machinery derives from the FHP reference implementation at
[bc7110f](https://github.com/FAIR-bioHeaders/FHP-Specification/blob/bc7110fedb6f05b52b1d2348b5b14a79b91b0637/tests/fhp_microdata.py),
with its MPL-2.0 notice retained. Source digest and adaptations are recorded in the
binding provenance file. This is a **test-only reference**, not an installed parser.

`itemprop` names the actual field. An object has its own `itemscope` and
`data-fhr-type="object"`; an ordered array has `data-fhr-type="array"` and direct
`itemprop="item"` children. Scalars use `data-fhr-type` with the JSON scalar type.
Integer zero, floating zero, exact representable strings/Unicode and nested
key/array order are preserved. Carriage returns are encoded as character
references so browser line-ending normalization does not alter their values.
NUL and unpaired surrogates in emitted standard values or the title cannot
round-trip through HTML tokenization; the
reference reports an HTML serialization error instead of replacing them. This
is a stated binding limit, not a new constraint on JSON/YAML metadata. Omitted
extension values need not be HTML-representable; R13 finite-number validation
still applies to the entire record, including extensions. Missing optional fields remain absent; booleans are not integers.
Untyped fallback uses the selected schema for coercion before full validation.
Repeated ordinary array properties form an ordered array. Repeated scalar or
repeated array-container properties yield invalid shapes, never last-value wins.
Literal CRLF/CR is normalized to LF before HTML tokenization; decoded `&#13;`
references retain carriage returns. A self-closing slash on a non-void HTML
element does not close that element. The first duplicated HTML attribute applies under R9. Family implied end-tag and
inert script/template rules are retained; this is not a general HTML5 browser engine.

The table inventories all 29 root fields at the pinned draft. Requiredness,
constraints and nested properties come from `fht.json` and `fht_linkml.yml`, not
from this table. Each nested object uses the same object/array rules recursively.

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

`metadataAuthor` and `assemblyAuthor` retain their different roles. `dateCreated`
is resource creation, not sample collection. `sample` entries do not establish
uniform pooled identity, and `derivedFrom` retains only the already permitted
FHT/filteredFrom and FHR/transcribedFrom pairs. HTML does not infer construction
history, parents, biological molecule class or scientific validity.

The **current draft schema itself** accepts `x-` extension fields through its
`patternProperties`; that is not a released FHT R15 claim. Following family M5,
the proposed writer omits top-level extensions, reports their keys through its
warning hook and a visible omission notice, and the reader
rejects embedded extension properties. Base-contract round trips are lossless,
while records with extensions must retain their original JSON/YAML preservation
copy. No extension is silently promoted to a standard field.

## Visible values

The binding's promise is that the embedded data is the readable value. The
reference reader applies the direct visibility checks below before extracting
metadata. It does not load arbitrary stylesheets or compute the CSS cascade or
layout; producers remain responsible for keeping the rendered table visible:

- a property element, or the FHT scope, that is concealed: the `hidden`
  attribute, an inline `style` with `display: none`, `visibility: hidden` or
  `visibility: collapse`, or `content-visibility: hidden`, on the element or
  any ancestor; or contents that are never rendered (`head`, `title`, `style`,
  `noscript`, `meta`, `link`). Inline CSS comments separate tokens for these
  checks, so `display:/**/none` and `display:none /*comment*/` are refused;
- an inline style containing a backslash or quote, or an unmatched comment
  terminator, on a property or its ancestor. CSS escapes and quoted values are
  outside this reference reader's supported inline-style subset, so these are
  conservatively refused rather than interpreted as visible;
- a scalar value that includes text from a concealed descendant (for example
  `Visible<span hidden>Hidden</span>`, which a viewer reads as `Visible`). Only
  the scalar's own descendants are checked; concealed markup elsewhere in the
  page, outside any property value, is not refused;
- a property whose value would come from an attribute with no visible text:
  `meta[content]`, `link`, `img`, `audio`, `video`, `source`, `track`, `embed`,
  `iframe` and `object`;
- a `data`, `meter` or `time` value attribute that differs from the text the
  element shows;
- an `href` (on `a` or `area`) outside the FORMAT.md R14 schemes (`http`,
  `https`, `ftp`, `urn`, `doi`, `info`): in a page it is an active link, so a
  `javascript:` or `data:` URL is refused rather than warned about;
- `itemref`, which pulls properties from outside the item, and an `itemprop`
  with more than one token, which would let one visible value fill two fields.

These are restrictions of this draft binding, stricter than the shared
MICRODATA.md M2 value rules; the writer never produces any of them. The
negative fixtures in `tests/fixtures/microdata/invalid/` each change one
readable example page in exactly one of these ways. Every invalid fixture must
name its expected rejection; a missing or empty error assertion fails the tests.
The reader probes the installed `html.parser` for RCDATA behavior: markup inside
`<title>` and `<textarea>` must stay text and character references must decode.
It refuses a parser that fails this capability check, including versions without
the behavior, while accepting backports that provide it. No version-number floor
is used. The writer escapes markup without using `html.parser`, so it does not
need this reader-specific capability check. CI uses the current Python 3.13.

## Supplied protocol, kit and sample context

The [recorded Molik decisions](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8#issuecomment-6928571815)
retain `sample` as an ordered array of typed tissue/stage/condition/strain
assertions. It is not deprecated. BioSample, BioProject and SRA URLs go in
`relatedLink`, separate from the transcriptome's `accessionID`/`identifier`.
All nine root fields remain required, while the existing optional taxon
name/URI members remain optional.

Keep `strandedness` under its existing read/read-1 convention. Record a supplied
library protocol or kit description in `documentation`, with an actual protocol
URL in `relatedLink`; neither is software provenance or an extra controlled
`libraryStrategy` value. For example, an application can add producer-supplied
values to a metadata copy using only existing fields:

```python
if supplied_protocol_and_kit_description:
    record["documentation"] = "\n".join(filter(None, (
        record.get("documentation"), supplied_protocol_and_kit_description
    )))
if supplied_protocol_urls:
    record["relatedLink"] = record.get("relatedLink", []) + supplied_protocol_urls
```

Those variable names stand for actual producer information, not literal header
placeholders. Preserve any existing documentation/links when adding information;
omit unknown optional details rather than guessing a kit or defaulting the strand.
The reference tests exercise these fields as ordinary ordered values and URLs as
text, without introducing a `kit`, `libraryProtocol` or sample-accession slot.

## Reference API, examples and validation

`tests/fht_microdata.py` exposes `write_page(record, schema=None, *,
allow_draft=False, title=..., warn=None)` and `read_page(text, schema=None, *,
allow_draft=False, warn=None)`. Both require explicit `allow_draft=True`. The default schema
is the local development contract; an explicitly supplied schema argument is for
reference tests, not remote schema loading. Extraction selects identity before
coercion and validates with the declared Draft 2020-12 implementation and full
`FormatChecker`. This schema validation is separate from typed structure checks.

The writer renders one visible metadata table, with nested objects and ordered
lists inside it. The embedded data **is the readable value**; there is no hidden
second copy to drift. Field labels, values and title are escaped. URLs remain
text, with no active links, fetching, script or user-controlled attributes.
The seven standalone [HTML examples](../examples/html/) pair with the unchanged
minimal/rich JSON and YAML for all three construction cases, plus the mixed-
molecule example in `examples/`.
They remain synthetic examples. A checksum carried into HTML is the original
FASTA metadata value; neither this HTML document nor any parent is file-verified.

Reproduce from this repository after installing `requirements-linkml.txt`:

```sh
python scripts/make_fht_microdata.py --check
python -m unittest discover -s tests -p 'test_fht_microdata.py' -v
python -m unittest discover -s tests -v
python scripts/check_fht_fixtures.py
python json-schema-generator.py
git diff --exit-code fht.json
python scripts/check_provenance.py
python scripts/check_docs.py
```

`make_fht_microdata.py` without `--check` regenerates the new HTML files and the
marked root-binding table in this document from the actual schema types.
References to enum definitions remain scalar bindings, not object scopes.
It does not alter the model, JSON Schema, existing example records, conformance
vectors or pilot. The test fixture manifest records rule-derived invalid cases:
wrong family/version, repeated scalar, missing object scope, array stray text,
conflicting family scopes, script content used as a required value, and the
visible-values cases above (hidden, `display: none`, a hidden scope, `meta`
content, `noscript`, `itemref`, a multi-token `itemprop`, a `javascript:`
href and a `data` value that differs from its text). Additional
executable cases cover all 29 existing fields, complete format validation,
non-finite numbers, ordered duplicates, zero types, hostile strings, optional end
tags, duplicated attributes, extension loss warnings and explicit draft opt-in.

## Handoffs and decisions

The [small decision docket](FHT-DECISION-DOCKET.md) separates actual curator and
publication decisions from ordinary binding implementation. This proposal does
not enable toolkit or website output. Those consumers need their own reviewed
binding disposition and installed round-trip evidence. No editor/journal
copy-paste path, community endorsement, released vocabulary or conformance format
is claimed here. Shared publication remains the agreed authority; this reference
packet does not reopen the accepted initial design or generation pipeline.

## Optional browser-DOM verification

The reference unit suite runs in normal Python CI without a browser dependency.
The real-browser check runs as its own CI job (`browser` in
`validate-specification.yml`). To run it locally, install Playwright 1.65.0 and
Chromium in a disposable location, then point the script at that installation:

```sh
npm install --prefix /tmp/fht-browser --ignore-scripts playwright@1.65.0
/tmp/fht-browser/node_modules/.bin/playwright install chromium
FHT_PLAYWRIGHT_MODULE=/tmp/fht-browser/node_modules/playwright \
  node scripts/check_fht_html_browser.mjs
```

This independently extracts the visible table with the browser DOM, compares it
with canonical JSON including row/array order, and rejects active or hidden
content and page network requests. Optional `HTML JSON` arguments add a local
stress case. Python tests separately verify integer versus floating-point types,
which JavaScript's single numeric type cannot distinguish. A local Chromium run
also covered hostile Unicode/text and CRLF values; it is not a claim about an
editor, journal system or every browser. No toolkit or website integration is
performed by this check.

## Draft read diagnostics

Every successful reference read emits a V7 diagnostic naming FHT, the owning
source commit and verified schema SHA-256, with `released=false`. A callback
`warn=` may capture each diagnostic; otherwise Python warnings are used. The
helper verifies local raw schema bytes against binding provenance before
validation. A supplied schema object must equal that pinned local contract;
custom overrides cannot inherit its provenance claim. Direct script/template
children of typed arrays are inert, just as in ordinary property traversal.
Scalar string list items use pre-wrap so readable command-line options retain
repeated spaces, tabs and line breaks.
