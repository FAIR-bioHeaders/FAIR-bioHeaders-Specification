# HTML microdata

The example wraps metadata in a `div` with `itemscope` and an `itemtype` pointing
to the FHR schema. Properties use `itemprop`; nested objects introduce an item
scope. Repeated values and empty arrays are preserved through typed containers.

The converter's HTML representation adds `data-fhr-type` annotations (`object`,
`array`, `string`, `integer`, `number`, `boolean`, `null`) to make the original
JSON/YAML mapping recoverable. An array container holds children with
`itemprop="item"`. These are FHR serialization conventions, not a claim that a
generic Schema.org consumer understands FHR properties or these extensions.
HTML values and attribute text must be escaped (`&`, `<` and `>` in text, and the
quote character as well in attributes); command-line strings are data and are never
executed. Unicode and whitespace in typed strings are preserved. The converter writes
every value as element text, never as an `href` or `src`, so a value is not a link in
the page. A reader that takes a value from an `href` applies the link-scheme rule R14
of [FORMAT.md](FORMAT.md) like any other.

To embed metadata, copy the generated item-scope element into a page:

```bash
fhr-convert examples/example.fhr.json /tmp/example.html
fhr-convert /tmp/example.html /tmp/example.yaml
fhr-validate /tmp/example.yaml
```

## Reading rules

Readers extract FHR metadata from HTML as follows. The first of repeated
attributes applies, and `itemtype` and `itemprop` are space-separated token lists
(rule R9 in [FORMAT.md](FORMAT.md#checksum-decision-for-v03)). Converter 0.3.1 and later implement
these rules.

- [M1] A document holds exactly one FHR item scope: an element with `itemscope`
  whose `itemtype` tokens include the raw-main `fhr.json` URL. That URL identifies
  FHR items; the record's `schema` property, usually a versioned URL, selects the
  schema it is checked against ([SCHEMA-VERSIONS.md](SCHEMA-VERSIONS.md)). A document with none, or
  with more than one, is invalid. An element with `itemscope` but no `itemprop`
  inside the FHR scope is a separate item: neither it nor its properties belong
  to the FHR metadata.
- [M2] The document is parsed as HTML, so end tags implied by HTML (`p`, `li`,
  `dt`, `dd`, `td`, `th`, `tr` and others) end their elements. A property's value
  is the defining attribute of its element if present (`meta[content]`,
  `a`/`area`/`link[href]`, `audio`/`embed`/`iframe`/`img`/`source`/`track`/`video[src]`,
  `object[data]`, `data`/`meter[value]`, `time[datetime]`), and otherwise its text
  content with character references decoded. Those attributes on any other element
  are ignored.
- [M3] With `data-fhr-type`, a `string` value is kept exactly, including
  whitespace, and an `integer`, `number`, `boolean` or `null` value must be JSON of
  that type, or the document is invalid. Without it, values of schema-defined
  numeric fields are read as numbers, and values of schema-defined list fields
  become lists.
- [M4] The extracted metadata must validate against `fhr.json`. A property that
  appears more than once becomes a list, so a repeated property whose field
  takes a single value is invalid.
- [M5] Microdata carries no extension fields ([FORMAT.md](FORMAT.md) R15). A
  writer leaves every top-level `x-` key out, with its value, and reports the keys
  it left out. A document whose FHR item has an `itemprop` that starts with `x-` is
  invalid, even where the selected schema would accept the key in JSON or YAML, so
  that HTML pages never hold values that the standard does not define. A microdata
  round trip therefore drops extension fields; use JSON or YAML to keep them.

The ids M1 to M5 are stable labels used by the
[conformance vectors](../conformance/README.md); they add no requirements beyond
the converter behaviour described here.

The converter also accepts ordinary repeated scalar properties and nested item
scopes, converting schema-defined numeric fields and lists. It rejects missing,
incomplete, or multiple FHR root scopes; legacy examples with flattened nested
properties should be regenerated. Run the converter round-trip and example tests
before changing this representation. The browser microdata download-tool project
is outside this release.

## Type-specific bindings

The escaping, typed-container and HTML parsing conventions above are shared.
FHP and FHGFF3 reuse those conventions, but not the FHR-specific identity and
validation requirements: their F1/H1 rules replace M1 with the type-specific
itemtype, and their F2/H2 rules select the type-specific schema instead of
validating against `fhr.json` as M4 does. The type-specific binding documents
are authoritative for the complete rules and required fields. **Naming a binding
here is documentation, not a claim of toolkit, validator or website support**:
runtime status is summarized in the rows below, and toolkit implementation is
tracked in the linked FAIR-bioHeaders-Tools records. The shared conformance
vectors cover FHR microdata only; they do not record per-tool HTML support.

| Type | Binding document | Itemtype (record scope) | Status |
| --- | --- | --- | --- |
| FHR | this page (M1 to M5) | raw-main `fhr.json` | Released representation; shipped in the toolkit |
| FHP | [FHP-Specification `docs/FHP-MICRODATA.md`](https://github.com/FAIR-bioHeaders/FHP-Specification/blob/main/docs/FHP-MICRODATA.md) | raw-main `fhp.json` | Binding reviewed in FHP-Specification; the toolkit reader/writer shipped in fair-bioheaders 0.8.2 ([Tools#58](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/issues/58)). No shared conformance vector exists for the FHP form; see #216 for the publication-vs-implementation ruling this row depends on |
| FHGFF3 | [FHGFF3 `docs/FHGFF3-MICRODATA.md`](https://github.com/FAIR-bioHeaders/FHGFF3/blob/main/docs/FHGFF3-MICRODATA.md) | raw-main `fhgff3.json` | Draft binding reviewed in FHGFF3#5 (rules H1 to H8). The toolkit reader/writer merged in [Tools#139](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/pull/139), but is **not released**. Hardening and explicit experimental status are tracked by [Tools#140](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/issues/140) / [Tools#141](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/pull/141); binding status remains under [FHGFF3#16](https://github.com/FAIR-bioHeaders/FHGFF3/pull/16). No shared conformance vector exists yet. Website enablement still requires a suitable toolkit release; merge alone does not establish adoption or website support |

A shared publication of the FHP/FHGFF3 HTML forms as first-class conformance
vectors, and any change to the "must be published through FAIR-bioHeaders-
Specification before adoption" precondition in the two type-repo binding
documents, is governed by the ruling requested in
[#216](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/216).
This section records that the bindings exist and where they live; it adds no
requirement and adopts no contract.
