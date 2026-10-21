# Schema versions and schema selection

Every FAIR-bioHeaders header names the schema it follows in `schema` and the version of that
schema's contract in `schemaVersion`. This page says what the version means, which releases carry
which versions, and how a reader chooses the schema to validate a file against. The toolkit, the
gff3-validator header checks and the website follow it. The design is in
[specs/012-schema-versioning](../specs/012-schema-versioning/spec.md) (maintainer decision on
[#44](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/44), 2026-10-14).

## Three different versions

| Value | Example | What it versions |
| --- | --- | --- |
| `schemaVersion` | `"2.0"` | The metadata contract of one header type (this page) |
| Release tag | `v0.4.0` | A release of this repository; it can carry several header types |
| `version` | `1.2.0` | The assembly, protein set or annotation the header describes |

A release tag alone never changes `schemaVersion`, and neither ever changes the described data's
`version`.

## schemaVersion

`schemaVersion` is a string `"MAJOR.MINOR"`: two non-negative integers without leading zeros
(`^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`). Each header type has its own version.

- **Major** (`2.0` → `3.0`): some file that was valid becomes invalid, or a valid value changes
  meaning. Examples: a new required field, a removed field, a tighter pattern, range or enum, a
  closed object, a changed type.
- **Minor** (`2.0` → `2.1`): every valid file stays valid with the same meaning, and something
  new is allowed. Examples: a new optional field, a relaxed constraint.
- **No change**: descriptions, examples, documentation and generated files that change no
  validation outcome.

The schema of version M.N accepts `schemaVersion` values `"M.0"` to `"M.N"`.

In YAML headers write the version quoted: `schemaVersion: '2.0'`. Unquoted, `2.0` is the number
2.0 and fails. The toolkit quotes it when it writes YAML.

## Versions by release

The machine-readable form is [`schemas/versions.json`](../schemas/versions.json).

| Release | FHR | FHP | FHGFF3 |
| --- | --- | --- | --- |
| v0.3.0, v0.3.1 | `1` (a number) | – | – |
| v0.4.0, v0.4.1 | `"2.0"` | `"1.0"` | `"1.0"` |

v0.4.1 changed only format rules (docs/FORMAT.md), not the schemas, so its schemas are the
v0.4.0 ones and `current` in `versions.json` stays `v0.4.0`; examples keep citing v0.4.0.

FHR 2.0 is a major version because the v0.4 tightening
([SCHEMA-CHANGES-v0.4.md](SCHEMA-CHANGES-v0.4.md)) rejects some values v0.3 accepted. The additive
v0.4 changes (author `nameType`, scaffold statistics) are part of 2.0. FHP and FHGFF3 are first
released in v0.4.0.

## Choosing the schema

A reader looks only at the record's `schema` value. `<file>` is `fhr.json`, `fhp.json` or
`fhgff3.json` and gives the header type; `<type>` is `fhr`, `fhp` or `fhgff3`. Matching is exact.

Raw URLs may name the repository by its current name, `FAIR-bioHeaders-Specification`, or by
`FHR-Specification`, its name until #108. Both forms are recognised everywhere and mean the
same; existing files cite the old form, and it keeps serving the same files.

- [V1] `https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/main/<file>` selects
  the reader's **current** schema of that type: the copy of `main` the reader has. There is no
  fallback to an older release.
- [V2] `https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/vX.Y.Z/<file>` selects
  **release vX.Y.Z's** schema of that type.
- [V3] `https://w3id.org/fair-bioheaders/<type>/vX.Y.Z`, with or without a trailing slash, selects
  release vX.Y.Z's schema of that type, the same as V2.
- [V4] If the reader does not have that release, the release has no schema of that type, or a raw
  URL names any ref other than `main` or a release tag, the result is **unsupported-version**. The
  file is not checked against another schema. The message names the value and the releases the
  reader has, for example
  `FHR: unsupported schema version: https://w3id.org/fair-bioheaders/fhr/v0.0.0 (this tool has FHR
  schemas for main (v0.4.0), v0.3.0, v0.3.1, v0.4.0, v0.4.1)`.
- [V5] Any other value, including the w3id path form `…/fhr/v0.4.0/fhr.json`, is **FHR**, checked
  against the current FHR schema. FHR's `schema` field has never been constrained; this keeps that
  behaviour.

Readers use copies of the released schemas (tags are the source) and say which release their
current copy is; they do not fetch schemas at run time. Microdata keeps the raw-main `fhr.json`
URL as its `itemtype` (rule M1 identifies FHR items by it); the `schema` itemprop carries the
versioned URL.

## Writing files

New files and examples cite the versioned URL of the release they target, preferably the w3id form:

```yaml
schema: https://w3id.org/fair-bioheaders/fhr/v0.4.0
schemaVersion: '2.0'
```

The raw-main URL stays the canonical "current schema" link in documentation. Tools keep a file's
`schema` value as written when they combine, strip or convert it.

## Migrating files that cite raw-main with schemaVersion 1

Once the current FHR schema is 2.0, such a file fails with a `schemaVersion` error. No tool rewrites
it, because any change to the header changes the checksum. Choose one:

- **Move to v0.4**: set `schema` to `https://w3id.org/fair-bioheaders/fhr/v0.4.0` and
  `schemaVersion` to `'2.0'`, fix anything the v0.4 tightening rejects
  ([SCHEMA-CHANGES-v0.4.md](SCHEMA-CHANGES-v0.4.md)), and recompute the checksum.
- **Pin v0.3.1**: set `schema` to `https://w3id.org/fair-bioheaders/fhr/v0.3.1`, keep
  `schemaVersion: 1`, and recompute the checksum.

With the toolkit:

```bash
bioheaders convert genome.fa metadata.yaml   # write the header as YAML; edit schema and schemaVersion
bioheaders strip genome.fa -o plain.fa
bioheaders combine metadata.yaml plain.fa -o genome.fhr.fa   # new checksum
```
