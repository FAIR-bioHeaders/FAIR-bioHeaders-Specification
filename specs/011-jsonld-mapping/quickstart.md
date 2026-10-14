# Quickstart: FHR metadata as JSON-LD

**Feature**: 011-jsonld-mapping | **Contracts**: [cli.md](contracts/cli.md), [fhr.context.jsonld](contracts/fhr.context.jsonld), [vocabulary.md](contracts/vocabulary.md), [mapping-table.schema.json](contracts/mapping-table.schema.json) | **Model**: [data-model.md](data-model.md)

This guide shows a data portal how to publish an FHR record as linked data (US1), shows a
maintainer how to reuse the mapping table (US2), and shows a tool how to read JSON-LD back
(US3). It also gives the end-to-end validation scenarios V1 to V8 for this feature.

> **Status**: This is a design-phase guide. The `.jsonld` format, `jsonld/`, `mappings/` and the
> examples do not exist until the tasks in [tasks.md](tasks.md) are implemented. The expected
> outputs below come from the Phase 0 prototype ([research.md](research.md)), and the tests pin
> them.

## Prerequisites

- Python 3.9 or later and the `fair-bioheaders` release that ships JSON-LD:

  ```bash
  pip install "fair-bioheaders>=<version with jsonld>"            # placeholder: the first release with JSON-LD
  pip install "fair-bioheaders[jsonld]>=<version with jsonld>"    # only to read arbitrary JSON-LD (US3); Python 3.10+
  ```
- No network is needed. The context is bundled and never fetched.
- For the specification checks: a FAIR-bioHeaders-Specification checkout with
  `pip install -r requirements-linkml.txt -r requirements-jsonld.txt`.

## 1. Publish a record as linked data (User Story 1)

```bash
bioheaders convert examples/example.fhr.json example.fhr.jsonld
```

The output is the FHR record itself, with FHR's keys unchanged, plus an embedded `@context` and
`@type`. Abridged:

```json
{
  "@context": { "@version": 1.1, "@protected": true, "sdo": "http://schema.org/", "...": "..." },
  "@type": "Dataset",
  "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/main/fhr.json",
  "schemaVersion": 1.0,
  "taxon": { "@type": "Taxon", "name": "Homo sapiens", "uri": "https://identifiers.org/taxonomy:9606" },
  "genome": "Synthetic human reference example",
  "metadataAuthor": [ { "@type": "Person", "name": "Adam Wright", "uri": "https://orcid.org/0000-0002-5719-4024" } ],
  "assemblySoftware": [ { "@type": "SoftwareApplication", "name": "hifiasm", "version": "0.19.8", "...": "..." } ],
  "...": "..."
}
```

To embed it in a landing page, put it inside a script element:

```html
<script type="application/ld+json">
  … contents of example.fhr.jsonld …
</script>
```

Escape `</` as `<\/` if any value could contain it. The landing page's own microdata, if any,
stays separate.

What a JSON-LD processor sees (the prototype's N-Quads, abridged):

```text
_:b0 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schema.org/Dataset> .
_:b0 <http://schema.org/name> "Synthetic human reference example" .
_:b0 <http://schema.org/about> <https://identifiers.org/taxonomy:9606> .
<https://identifiers.org/taxonomy:9606> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schema.org/Taxon> .
_:b0 <http://schema.org/creator> <https://orcid.org/0000-0003-3192-6538> .
<https://orcid.org/0000-0003-3192-6538> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schema.org/Person> .
_:b0 <http://schema.org/dateCreated> "2022-03-21"^^<http://www.w3.org/2001/XMLSchema#date> .
_:b0 <https://w3id.org/fair-bioheaders/terms#checksum> "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" .
_:b2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schema.org/SoftwareApplication> .
_:b2 <http://schema.org/softwareVersion> "0.19.8" .
```

**What it is not, by default.** The record follows the Bioschemas Dataset, Taxon, Person and
ComputationalTool profiles' property choices, but it does not claim conformance: it has no
`@id`, `keywords` or `url` (research R-04). An export context supplies them (research R-18):

```bash
cat > export.yaml <<'EOF'
id: https://example.org/datasets/hs-synthetic
url: https://example.org/genomes/hs-synthetic
keywords: [genome assembly, Homo sapiens]
EOF
bioheaders convert --export-context export.yaml examples/example.fhr.json page.jsonld
```

The output then ends with `"conformsTo": "https://bioschemas.org/profiles/Dataset/1.0-RELEASE"`,
because every Dataset minimum property is present. With an incomplete export context the toolkit
names the missing properties and makes no claim.

## 2. Reuse the mapping table (User Story 2)

```bash
python - <<'EOF'
import yaml
table = yaml.safe_load(open("mappings/fhr-jsonld-dcmi.yml"))
for e in table["entries"]:
    d = e["dcmi"][0]
    print(f'{e["path"]:42} {e["jsonld"]["term"]:55} {d["term"]:38} {d["kind"]}')
EOF
```

Expected (abridged):

```text
schema                                     http://schema.org/schemaVersion                      http://purl.org/dc/terms/conformsTo    conditional
genome                                     http://schema.org/name                               http://purl.org/dc/terms/title         conditional
dateCreated                                http://schema.org/dateCreated                        http://purl.org/dc/terms/created       exact
checksum                                   https://w3id.org/fair-bioheaders/terms#checksum      none                                   unsupported
…
```

There are 45 rows. 19 rows have a DCMI term; the other 26 are `none`, each with a `reason`.
`conditional` rows carry a `condition`. `subject: record` marks statements about the metadata
record rather than the assembly, as #56's resource model requires.

## 3. Read JSON-LD back (User Story 3)

```bash
bioheaders convert example.fhr.jsonld back.json            # canonical path, no extra needed
bioheaders validate example.fhr.jsonld                      # "FHR metadata is valid."
bioheaders convert portal-record.jsonld back.json          # any other JSON-LD form: needs the jsonld extra
```

A record from a portal that added Bioschemas terms:

```text
$ bioheaders convert portal-record.jsonld back.json
FHR: JSON-LD term not in the FHR mapping: http://schema.org/keywords (at the record)
$ echo $?
1
$ bioheaders convert --ignore-unknown-terms portal-record.jsonld back.json
FHR: warning: JSON-LD term not in the FHR mapping: http://schema.org/keywords (at the record)
```

## Validation scenarios

Run these from the repository root of FAIR-bioHeaders-Specification (V1 to V4, V8) and of
FAIR-bioHeaders-Tools (V5 to V7). Each must pass before the feature is done.

| # | Scenario | Command | Expected |
|---|---|---|---|
| V1 | The context and vocabulary are generated from LinkML and up to date (R-08) | `python scripts/make_jsonld.py --check && python scripts/check_linkml.py` | Both exit 0. LinkML generation still matches `fhr.json` |
| V2 | Every FHR property has a mapping entry with a DCMI column (SC-002) | `python -m unittest tests.test_jsonld_mappings -v` | 45 paths equal the `fhr.json` property paths; schema-valid; terms equal the LinkML IRIs |
| V3 | Round trip over all examples and conformance metadata (SC-001) | `python -m unittest tests.test_jsonld_roundtrip -v` | Every record is equal after canonical stripping; also after PyLD expansion plus mapping, except the two documented `*-nested-checksum` vectors, which report `checksum` |
| V4 | Expanded terms only from allowed vocabularies; schema.org domains respected (SC-003) | `python -m unittest tests.test_jsonld_vocabulary -v` | Every predicate is in `sdo:`, `fhr:` or `rdf:`; every `sdo:` property is used on a type in its domain (pinned v30.1 subset); every `fhr:` term is defined |
| V5 | Toolkit conversions, offline | `poetry run pytest tests/jsonld_test.py` (sockets disabled) | Byte-identical to `examples/*.fhr.jsonld`; all format pairs round-trip; unknown remote context refused |
| V6 | Conformance vectors through the toolkit | `python scripts/check_conformance.py --converter ../FHR-File-Converter` (from FAIR-bioHeaders-Specification) | Every `jsonld` vector `ok` |
| V7 | Installed wheel, outside the checkout | `bioheaders convert examples/example.fhr.json /tmp/x.jsonld && bioheaders convert /tmp/x.jsonld /tmp/x.json && cmp <(python -m json.tool --sort-keys /tmp/x.json) <(python -m json.tool --sort-keys examples/example.fhr.json)` | exits 0 |
| V8 | Manual check with the schema.org validator, recorded in the PR (not a CI gate) | Paste `examples/example.fhr.jsonld` into <https://validator.schema.org/> | Dataset, Taxon, Person, PropertyValue and SoftwareApplication are recognised, with no errors for `sdo:` properties. FHR terms are listed as unrecognised extensions, which is expected |

SC-004 is confirmed by the maintainer of #56, David Molik, on the PR. It is not a script.
