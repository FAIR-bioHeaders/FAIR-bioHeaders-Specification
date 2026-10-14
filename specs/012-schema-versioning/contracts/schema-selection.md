# Contract: schema versions and schema selection

**Feature**: 012-schema-versioning | Research: D-01 to D-07

This is the rule every reader applies: the toolkit, the gff3-validator header checks and the
website builder. The published form is [docs/SCHEMA-VERSIONS.md](../../../docs/SCHEMA-VERSIONS.md).

## 1. Version strings

`schemaVersion` is `"MAJOR.MINOR"`: `^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`. The schema of version
M.N accepts `"M.0"` to `"M.N"`. Releases v0.3.0 and v0.3.1 published FHR with the number `1`; they
are not rewritten.

## 2. The registry

`schemas/versions.json` has `current` (a release tag) and `releases` (tag → header type →
schemaVersion). A test checks that each published schema's `schemaVersion` enum equals the values
allowed for `releases[current]`.

## 3. Selection

Let `S` be the record's `schema` value.

| # | `S` matches | Header type | Schema used |
| --- | --- | --- | --- |
| V1 | `https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/F` | type of `F` | the reader's current schema of that type |
| V2 | `https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/vX.Y.Z/F` | type of `F` | release vX.Y.Z's schema of that type |
| V3 | `https://w3id.org/fair-bioheaders/T/vX.Y.Z` or `…/T/vX.Y.Z/` | `T` | release vX.Y.Z's schema of that type |
| V4 | as V1–V3 but the reader lacks that release, the release has no schema of that type, or a raw URL names any other ref | type of `F` or `T` | none: **unsupported-version** |
| V5 | anything else | FHR | the reader's current FHR schema |

`F` is `fhr.json`, `fhp.json` or `fhgff3.json`; `T` is `fhr`, `fhp` or `fhgff3`. Matching is
exact and case-sensitive. A raw URL naming another file is V5.

The "current schema" is the reader's copy of the type's schema on `main`; the reader states the
release its copy corresponds to.

## 4. Results

- V1–V3, V5: validate against the selected schema; the result is valid or invalid with the
  schema's errors.
- V4: the result is **unsupported-version**. The message names `S`, the header type and the
  releases the reader has for that type, for example:
  `FHR: unsupported schema version: https://w3id.org/fair-bioheaders/fhr/v0.0.0 (this tool has FHR
  schemas for main (v0.4.0), v0.3.0, v0.3.1, v0.4.0)`.
  Command-line tools exit as for a validation failure (status 1).

## 5. Writing

Tools keep `schema` as written when they combine, strip or convert. New files and examples cite
the versioned URL of the release they target (V3 form preferred).

## 6. Conformance

Vectors with rule ids `V1`–`V5` (the selection rows) are in `conformance/`. Unsupported-version
vectors are `expected: invalid` with `rule: V4` and `result: unsupported-version`; a reader must
reject them with an unsupported-version message (`check_conformance.py --converter` looks for
`unsupported schema version`).
