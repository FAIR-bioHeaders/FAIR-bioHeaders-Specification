# Data model: Schema versions and schema selection

**Feature**: 012-schema-versioning | **Spec**: [spec.md](spec.md)

## SchemaVersion

| Attribute | Value |
|---|---|
| JSON type | string |
| Pattern | `^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$` (core slot) |
| FHR on v0.4 | enum `["2.0"]` |
| FHP | enum `["1.0"]` |
| FHGFF3 | enum `["1.0"]` |
| Legacy | v0.3.0 and v0.3.1 FHR: number, enum `[1]` |

## Registry (`schemas/versions.json`)

| Field | Type | Meaning |
|---|---|---|
| `current` | string, a release tag | The release the working tree's schemas belong to |
| `releases` | object: tag → object: header type → schemaVersion | Versions published by each release |
| `files` | object: header type → file name | `FHR` → `fhr.json`, `FHP` → `fhp.json`, `FHGFF3` → `fhgff3.json` |
| `w3id` | object: header type → path segment | `fhr`, `fhp`, `fhgff3` |

## SchemaURL (parsed)

| Form | Type from | Ref |
|---|---|---|
| raw-main | file name | `main` |
| raw tag | file name | `vX.Y.Z` |
| raw other ref | file name | the ref (unsupported) |
| w3id | path segment | `vX.Y.Z` |
| other | — | — (FHR, current) |

## Selection result

| Field | Values |
|---|---|
| `header_type` | `FHR`, `FHP`, `FHGFF3` |
| `release` | `main` (current), `vX.Y.Z`, or none (V5) |
| `schema` | a JSON Schema, or none when unsupported |
| `status` | `selected` or `unsupported` |
| `message` | for unsupported: the value, type and supported releases |
