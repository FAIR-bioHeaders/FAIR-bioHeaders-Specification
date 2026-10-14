# HTML microdata

The example wraps metadata in a `div` with `itemscope` and an `itemtype` pointing
to the FHR schema. Properties use `itemprop`; nested objects introduce an item
scope. Repeated values and empty arrays are preserved through typed containers.

The converter's HTML representation adds `data-fhr-type` annotations (`object`,
`array`, `string`, `integer`, `number`, `boolean`, `null`) to make the original
JSON/YAML mapping recoverable. An array container holds children with
`itemprop="item"`. These are FHR serialization conventions, not a claim that a
generic Schema.org consumer understands FHR properties or these extensions.
HTML values and attribute text must be escaped; command-line strings are data
and are never executed. Unicode and whitespace in typed strings are preserved.

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

The ids M1 to M4 are stable labels used by the
[conformance vectors](../conformance/README.md); they add no requirements beyond
the converter behaviour described here.

The converter also accepts ordinary repeated scalar properties and nested item
scopes, converting schema-defined numeric fields and lists. It rejects missing,
incomplete, or multiple FHR root scopes; legacy examples with flattened nested
properties should be regenerated. Run the converter round-trip and example tests
before changing this representation. The browser microdata download-tool project
is outside this release.
