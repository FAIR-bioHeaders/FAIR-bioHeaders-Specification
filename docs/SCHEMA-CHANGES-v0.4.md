# FHR v0.4 schema changes (unreleased)

This is the explained diff between the v0.3 `fhr.json` and the v0.4 schema. It
resolves [FHR-Specification#35](https://github.com/FAIR-bioHeaders/FHR-Specification/issues/35)
and [spec 002](../specs/002-v04-constraint-tightening/spec.md), following the
maintainer decisions recorded in that issue on 2026-10-09.

`schemaVersion` becomes the string `"2.0"` (maintainer decision on
[#44](https://github.com/FAIR-bioHeaders/FHR-Specification/issues/44), 2026-10-14;
[SCHEMA-VERSIONS.md](SCHEMA-VERSIONS.md)). Each tightening rejects values that were
already malformed under the documented meaning of the field, but because some files
valid under v0.3 become invalid, the contract version is a major one. No field becomes
required and no field is removed; `schemaVersion`'s type changes from number to string. Every
example in `examples/`, every conformance vector's metadata and the converter's
test fixtures that carry metadata still validate. One converter test that added
a `checksum` key under `accessionID` has to change (see Converter copies below).

The checks are syntactic. A matching DOI, ORCID or checksum does not prove that
the identifier resolves, that the person is the author, or that the file is
intact; only checksum verification against the file does that.

## Tightened constraints

Each row lists the JSON Schema location, the v0.3 and v0.4 constraint, an
example that v0.3 accepted and v0.4 rejects, and how to fix it.

| Location | v0.3 | v0.4 | Now rejected (example) | Migration |
| --- | --- | --- | --- | --- |
| `/properties/schemaVersion` | `type: number` | `type: string`, `enum: ["2.0"]`, pattern `^(0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*)$` | `1`, `1.0`, `99`, `2`, `"2"` | Write `'2.0'` (quoted in YAML) and cite `https://w3id.org/fair-bioheaders/fhr/v0.4.0`; or pin v0.3.1 by citing `https://w3id.org/fair-bioheaders/fhr/v0.3.1`. Either way recompute the checksum ([SCHEMA-VERSIONS.md](SCHEMA-VERSIONS.md#migrating-files-that-cite-raw-main-with-schemaversion-1)). |
| `/properties/masking/pattern` | `(not-masked\|hard-masked\|soft-masked\|repeat-masked\|unknown)` (unanchored) | `^(not-masked\|hard-masked\|soft-masked\|repeat-masked\|unknown)$` | `xx-unknown-yy`, `unknown-masked` | Use exactly one of the five values. |
| `/properties/scholarlyArticle/pattern` | `^10.` (unescaped dot) | `^10\.[0-9]+(\.[0-9]+)*/\S+$` | `10xfoo`, `10.1093`, `10.1093/x y` | Give the bare DOI, `10.<registrant>/<suffix>`, with no spaces. A resolver URL (`https://doi.org/…`) was already rejected. |
| `/properties/identifier/items/pattern` | `[a-z0-9]*:.*` (unanchored) | `^[A-Za-z0-9._-]+:.+$` | `has a : somewhere`, `:TC010103`, `beetlebase:` | Write `prefix:accession` with a non-empty prefix of letters, digits, `.`, `_` or `-`, and a non-empty accession. Uppercase prefixes (`GO:0008150`, `NCBITaxon:9606`) are now explicitly allowed. |
| `/properties/taxon/properties/uri/pattern` | `https://identifiers.org/taxonomy:[0-9]+` (unanchored, unescaped dots) | `^https://identifiers\.org/taxonomy:[0-9]+$` | `xhttps://identifiers.org/taxonomy:9606`, `…:9606/extra` | Use exactly `https://identifiers.org/taxonomy:<NCBI taxon id>`. |
| `/definitions/orcidUri/pattern` (both author lists) | `^https://orcid.org/[0-9]{4}-…-[0-9]{3}[0-9X]` (no `$`, unescaped dot) | `^https://orcid\.org/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]$` | `https://orcid.org/0000-0002-5719-4024junk` | Remove trailing text. `X` check digits remain valid. `http://orcid.org/` was already rejected and still is; write `https://`. |
| `/definitions/sha2/pattern` (`checksum`) | `^[A-Za-z0-9/+=]{44}$` | `^[A-Za-z0-9+/]{43}=$` (length 44 kept) | 44 `=`, 44 letters without padding, `…==` | Write the standard padded base64 of the 32-byte SHA-512/256 digest; recompute it with the converter if unsure. Any real FHR checksum already has this form. |
| `/properties/vitalStats/properties/{N50,L50,L90,totalBasePairs,numberContigs,numberScaffolds}` | `type: integer` | `type: integer`, `minimum: 0` | `N50: -1` | Statistics are counts or lengths; remove or correct negative values. (`N90` already had `minimum: 0`.) |
| `/properties/taxon/additionalProperties` | open | `false` | `taxon.url` | Keep only `name` and `uri`. |
| `/properties/metadataAuthor/items/additionalProperties`, `/properties/assemblyAuthor/items/additionalProperties` | open | `false` | `orcid`, `email` | Keep only `name` and `uri`. |
| `/properties/accessionID/additionalProperties` | open | `false` | `accessionID.uri` | Keep only `name` and `url` (note: `url`, not `uri`). |
| `/properties/vitalStats/additionalProperties` | open | `false` | `vitalStats.n50` | Use the exact, case-sensitive statistic names. |

`assemblySoftware` objects were already closed, and the top level already
rejected unknown keys. After this change every object in `fhr.json` rejects
unknown keys. Communities that need more fields should use profiles
([#51](https://github.com/FAIR-bioHeaders/FHR-Specification/issues/51)) rather
than extra keys.

## Additions (no existing instance is affected)

| Location | v0.4 | Meaning |
| --- | --- | --- |
| `/properties/vitalStats/properties/scaffoldN50` | optional `integer`, `minimum: 0` | Scaffold length in base pairs at 50 percent of the assembly length. |
| `/properties/vitalStats/properties/scaffoldN90` | optional `integer`, `minimum: 0` | Scaffold length in base pairs at 90 percent of the assembly length. |
| `/properties/vitalStats/properties/scaffoldL50` | optional `integer`, `minimum: 0` | Smallest number of scaffolds covering 50 percent of the assembly length. |
| `/properties/vitalStats/properties/scaffoldL90` | optional `integer`, `minimum: 0` | Smallest number of scaffolds covering 90 percent of the assembly length. |
| `/properties/metadataAuthor/items/properties/nameType`, `/properties/assemblyAuthor/items/properties/nameType` | optional `string`, `enum: [Personal, Organizational]` | Whether the author is a person or an organization, with the values of DataCite `nameType`. JSON-LD writers type the author node from it (`Person` or `Organization`) before falling back to the ORCID or ROR identifier. |

## Clarified descriptions (no validation change)

- `N50`, `N90`, `L50` and `L90` are contig statistics, as `N90`'s description
  already said. If you recorded scaffold values in them, move those values to
  the new `scaffold*` fields. The schema cannot detect this.
- `gcContent` remains a percentage from 0 to 100. A fraction such as `0.42`
  meant as 42 percent is still accepted, because `0.42` is also a legitimate
  0.42 percent value. Write `42.0` for 42 percent. Validators must not rescale
  or reject low values based on magnitude alone.
- `scholarlyArticle` is a bare DOI; `identifier` items are `prefix:accession`.

## Known limitation

JSON Schema patterns use ECMA-262 semantics, where `$` matches only at the end
of the string. Python's `re` (used by the `jsonschema` package) also lets `$`
match before one trailing newline, so under Python a value such as
`"soft-masked\n"` still passes the anchored patterns. The checksum and SeqCol
fields close this gap with exact lengths. Lookahead workarounds are not used
because RE2-based validators do not support them.

## Implementation and checks

- LinkML: `schemas/core.yaml` (checksum type, `schemaVersion`, `identifier`,
  `scholarlyArticle`, `Taxon.uri`, `Author.uri`) and `fhr_linkml.yml`
  (`masking`, `VitalStats`). `json-schema-generator.py` no longer reopens the
  `Taxon`, `Author`, `AccessionID` and `VitalStats` objects, and rewrites
  LinkML's `const` for `schemaVersion` as the published enum (`["2.0"]` for FHR,
  `["1.0"]` for FHP and FHGFF3; spec 012).
  `scripts/check_linkml.py` passes.
- `.github/schema-baseline.json` was updated deliberately with
  `scripts/check_schema_drift.py --update` after reviewing the diff above.
- `tests/test_v04_tightening.py` checks that every rejected example fails both
  `fhr.json` and the LinkML-generated schema at the named field, that real edge
  forms (ORCID `X` check digits, preprint and Zenodo DOIs, uppercase CURIE
  prefixes, 0.42 percent GC) and every example still validate, and that every
  object in `fhr.json` is closed.
- Conformance: the `fasta-nested-checksum` and `gfa-nested-checksum` vectors put
  their nested `checksum:` line under `taxon`, which v0.4 rejects. They now put
  it in a `documentation` block scalar. That still tests the same rule (an
  indented `checksum:` line is covered metadata, not the root checksum line),
  and the metadata validates. Their expected checksums changed; no other vector
  changed. The R2 rule about nested checksum properties still applies to
  header types that have them, such as `derivedFrom[].checksum`.

## Schema version and examples (spec 012)

- `schemaVersion` is a `"MAJOR.MINOR"` string in every header type; `schemas/versions.json`
  records the versions of each release, and `tests/test_schema_versions.py` keeps the schemas
  equal to it.
- Every example, conformance vector and assessment fixture cites the v0.4.0 versioned URL of its
  type (`https://w3id.org/fair-bioheaders/<type>/v0.4.0`) and its type's version; checksums were
  recomputed. Vectors V1–V5 test which schema a `schema` URL selects.
- The FHP and FHGFF3 `schema` patterns accept the raw-main, raw tag and w3id forms only; commit
  and branch refs are no longer schema URLs.
- All three baselines were updated deliberately after reviewing these diffs.

## Converter copies

The FHR File Converter (`bioheaders` package) bundles three identical copies of
the schema: `fhr_schema.json`, `fhr/fhr_schema.json` and
`bioheaders/fhr_schema.json`. All three must be replaced with the v0.4
`fhr.json` in the same release, as `scripts/check_release.py --converter`
requires (it checks the first two; the converter's own test checks all three
match). The converter test `test_nested_checksum_names_stay_covered` puts a
`checksum` key under `accessionID` and fails under v0.4. It needs to move that
key to a still-valid place, such as a `documentation` block scalar.
