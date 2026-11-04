# Contract: Extension fields (R15, J9, M5)

**Feature**: 015-extension-fields

## Schema fragment

The root of `fhr.json` (2.1), `fhp.json` (1.1) and `fhgff3.json` (1.1) keeps
`"additionalProperties": false` and adds:

```json
"patternProperties": {
  "^x-[A-Za-z0-9][A-Za-z0-9_.-]*$": {
    "description": "Extension field (docs/FORMAT.md R15): any value; it means nothing to the standard"
  }
},
"propertyNames": {"not": {"pattern": "\n"}}
```

and one item in the root `allOf` (FHGFF3 already has an `allOf`; FHR gains one):

```json
{
  "if": {"required": ["schemaVersion"], "properties": {"schemaVersion": {"const": "2.0"}}},
  "then": {"propertyNames": {"not": {"pattern": "^x-"}}}
}
```

with `"1.0"` for FHP and FHGFF3. `schemaVersion` is `{"enum": ["2.0", "2.1"]}` (FHR) or
`{"enum": ["1.0", "1.1"]}` (FHP, FHGFF3). Nested object definitions do not change.

The FHT draft (`fht.json` `"1.0"`) gets the same `patternProperties` and `propertyNames`, and no
conditional.

## Outcomes

| Record | FHR 2.0 schema | FHR 2.1 schema |
| --- | --- | --- |
| standard fields only, `schemaVersion: '2.0'` | valid | valid |
| standard fields only, `schemaVersion: '2.1'` | invalid (enum) | valid |
| `x-a: 1`, `schemaVersion: '2.1'` | invalid | valid |
| `x-a: 1`, `schemaVersion: '2.0'` | invalid | invalid (conditional) |
| `genom: …` (typo), any version | invalid | invalid |
| `X-a`, `x-`, `x-_a`, `x- a`, `x-ä`, `"x-a\n"` | invalid | invalid |
| `taxon: {name: …, x-a: 1}` | invalid | invalid |

FHP and FHGFF3 follow the same table with `"1.0"`/`"1.1"`.

## Serialisations

| Form | Extension fields |
| --- | --- |
| `;~`/`#~` header lines, YAML, JSON | kept as written, in order; R8, R11, R12, R13 apply; inside the checksum |
| canonical or other JSON-LD (read) | invalid (J9; in non-canonical forms also an unknown term, J4) |
| JSON-LD, schema.org export (write) | left out; the writer reports the keys it left out |
| HTML microdata (read) | invalid (M5) |
| HTML microdata (write) | left out; the writer reports the keys it left out |

## Toolkit messages

- An `x-` key under the older minor: `x-refget-commonName: extension fields (x-...) need
  schemaVersion "2.1"` (or `"1.1"`), instead of jsonschema's default `not` message.
- Writers: `FHR: warning: extension fields are not written to JSON-LD: x-a, x-b` (and the same
  for microdata and the export).
