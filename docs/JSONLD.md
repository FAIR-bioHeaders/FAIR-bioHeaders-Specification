# JSON-LD

FHR metadata has a JSON-LD form: the FHR record itself, with FHR's own keys, plus an
`@context` and `@type`. One document is both FHR metadata and linked data. A JSON-LD
processor reads it as schema.org and FAIR-bioHeaders vocabulary statements, and an FHR
tool reads it back to the identical record. `fhr.json` is unchanged: readers set the
JSON-LD keywords aside before schema validation.

- Context: [jsonld/fhr.context.jsonld](../jsonld/fhr.context.jsonld), generated from the
  LinkML model by `scripts/make_jsonld.py`. Do not edit it by hand.
- FAIR-bioHeaders terms (`https://w3id.org/fair-bioheaders/terms#`): [TERMS.md](TERMS.md) and
  [jsonld/terms.ttl](../jsonld/terms.ttl).
- Examples: [example.fhr.jsonld](../examples/example.fhr.jsonld) and
  [minimal.fhr.jsonld](../examples/minimal.fhr.jsonld), written from the JSON examples.
- Design and decisions: [specs/011-jsonld-mapping](../specs/011-jsonld-mapping/plan.md).

```bash
bioheaders convert examples/example.fhr.json example.fhr.jsonld
bioheaders convert example.fhr.jsonld back.json        # the same record again
```

## What the document contains

The writer (rule J7) emits, in this order:

1. `"@context"`: the context object, embedded rather than referenced by URL (see
   [Publication](#publication)).
2. `"@type": "Dataset"` (`schema:Dataset`).
3. Every FHR key of the record, in record order, with its value unchanged except that nested
   objects gain a first key `@type`:

   | FHR value | `@type` |
   | --- | --- |
   | `taxon` | `Taxon` (`schema:Taxon`) |
   | an item of `metadataAuthor` or `assemblyAuthor` | `Person` when its `nameType` is `Personal` and `Organization` when it is `Organizational` (v0.4); otherwise `Person` (`schema:Person`) when its `uri` is an ORCID iD; `Organization` (`schema:Organization`) when its `uri` is a ROR ID; otherwise `Agent` (`fhr:Agent`, "not classified") |
   | `accessionID` | `PropertyValue` (`schema:PropertyValue`) |
   | an object item of `assemblySoftware` | `SoftwareApplication` (`schema:SoftwareApplication`); a legacy string stays a string |
   | `vitalStats` | `VitalStats` (`fhr:VitalStats`) |

   A `documentation` value that is an absolute URL (a scheme, `://`, and no whitespace) is
   written under the key `subjectOf` (`schema:subjectOf`) in the same position. Text stays
   under `documentation` (`schema:description`).
4. Nothing else. Absent optional fields stay absent; no `null` and no empty node is emitted.

From v0.4 an author may state its kind in `nameType`, with the DataCite values `Personal` and
`Organizational`; the writer uses it first and keeps it as the literal `fhr:nameType`. Without
it the type follows the identifier: an ORCID identifies a person and a ROR ID an organization.
A name alone implies neither, so it is typed `fhr:Agent`. `fhr.json` currently allows only
ORCID URIs for authors.

Nested objects that FHR leaves open (`taxon`, author items, `accessionID`, `vitalStats`) may
carry keys that the context does not define, such as `taxon.checksum`. They stay in the
document, so the FHR round trip is exact, but JSON-LD processors ignore them. The toolkit
prints one warning per key, for example
`FHR: JSON-LD: taxon.checksum has no JSON-LD term; linked-data consumers will ignore it`.

### Export context and Bioschemas

The record follows the property choices of the Bioschemas
[Dataset](https://bioschemas.org/profiles/Dataset/1.0-RELEASE),
[Taxon](https://bioschemas.org/profiles/Taxon/1.0-RELEASE),
[ComputationalTool](https://bioschemas.org/profiles/ComputationalTool/1.0-RELEASE) and
[Person](https://bioschemas.org/profiles/Person/0.3-DRAFT) profiles. It claims conformance only
when the Dataset minimum properties are all present. There is no Bioschemas profile for genome
assemblies.

Some minimum properties are not FHR fields. A writer may take them from an **export context**
(`bioheaders convert --export-context FILE`), a small YAML or JSON mapping that is kept outside
the FHR record. Its format is provisional until FHR-Specification#56 defines the shared export
context:

```yaml
id: https://example.org/datasets/hs-synthetic        # the dataset's IRI, written as @id
url: https://example.org/genomes/hs-synthetic        # its landing page, written as url
keywords: [genome assembly, Homo sapiens]            # written as keywords
```

All three keys are optional, and other keys are an error. `@id` follows `@type`; `keywords`
and `url` follow the FHR keys. When every Dataset minimum property is present, the writer then
adds `"conformsTo": "https://bioschemas.org/profiles/Dataset/1.0-RELEASE"`
(`dct:conformsTo`). Dataset 1.1 was still a draft on 2026-10-10, so 1.0-RELEASE is the profile
that is checked:

| Bioschemas Dataset minimum | Written from |
| --- | --- |
| `@id` | export context `id` |
| `description` | `documentation`, when it is text (a URL becomes `subjectOf`) |
| `identifier` | `identifier` (non-empty) |
| `keywords` | export context `keywords` |
| `license` | `reuseConditions` |
| `name` | `genome` |
| `url` | export context `url` |

Without an export context, or with an incomplete one, there is no `conformsTo`, and the toolkit
says which properties are missing. The Taxon, ComputationalTool and Person profiles also need
properties that FHR lacks (`taxonRank`, a tool `description`, a person `description` and
`mainEntityOfPage`, and their own `dct:conformsTo`), so they are followed but not claimed.

## Embedding in a web page

Put the document in a script element of the landing page:

```html
<script type="application/ld+json">
  … contents of example.fhr.jsonld …
</script>
```

If any value could contain `</`, write it as `<\/` inside the element. The page's microdata,
if any, stays separate ([MICRODATA.md](MICRODATA.md)).

## Publication

- The canonical source of the context is `jsonld/fhr.context.jsonld` on `main`:
  `https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/jsonld/fhr.context.jsonld`.
- Release copies are addressed as
  `https://w3id.org/fair-bioheaders/fhr/vX.Y.Z/jsonld/fhr.context.jsonld`, once a release
  contains the file. That URL redirects to the copy on the
  [GitHub Pages site](https://fair-bioheaders.github.io/FHR-Specification/), which serves it as
  `application/ld+json` with CORS, so JSON-LD processors can load it.
- The vocabulary namespace `https://w3id.org/fair-bioheaders/terms` redirects by content
  negotiation: `Accept: text/turtle` gets `terms.ttl`, `Accept: application/ld+json` gets
  `terms.jsonld`, and anything else gets the HTML documentation page, where each term has an
  anchor (`#checksum`).
- Records still embed the context. Raw GitHub serves files as `text/plain`, which conforming
  JSON-LD processors must refuse to load as a context, and an embedded context also keeps old
  documents' meaning when the context changes and works offline.
- Term IRIs never change. The context changes only additively within one FHR `schemaVersion`.

### Files

| File | Contents |
| --- | --- |
| `jsonld/fhr.context.jsonld` | The JSON-LD 1.1 context |
| `jsonld/terms.ttl` | The vocabulary, as Turtle |
| `jsonld/terms.jsonld` | The vocabulary, as JSON-LD (the same triples) |
| `docs/TERMS.md` | The vocabulary's documentation page |

All four are generated by `scripts/make_jsonld.py` from the LinkML model; do not edit them.
`python scripts/make_jsonld.py --check` fails when one is out of date. `terms.ttl` starts with a
comment saying so, with its canonical URL and the release alias pattern; JSON cannot hold
comments, so the context and `terms.jsonld` have none. `scripts/build_pages.py` builds the Pages
site from them and from every release tag (`.github/workflows/jsonld-pages.yml`).

## What converting to RDF loses

The JSON-LD document round-trips exactly as FHR metadata. Converting it to RDF triples does not:

- `@set` arrays (the author lists, `identifier`, `genomeSynonym`, `instrument`, `relatedLink`,
  `assemblySoftware`) lose their order; `commandLineOption` is an RDF list and keeps it;
- empty arrays produce no triples;
- a JSON number such as `1.0` becomes `"1"^^xsd:integer`;
- nested keys without a term (above) are dropped.

## Reading rules

Readers turn a JSON-LD document into FHR metadata as follows. The rule ids are stable; the
conformance vectors in [conformance/](../conformance/README.md) cite them. Rules J3 to J5, for
JSON-LD in other forms (expanded, compacted with another context or in a `@graph`), are still
to be specified (specs/011-jsonld-mapping, user story 3); until then a document that is not
canonical is rejected.

- [J1] **Canonical form.** A document is canonical when its root is an object whose `@context`
  is a published FHR context, embedded (equal as parsed JSON to the `@context` value of
  `jsonld/fhr.context.jsonld`) or referenced by a known FHR context URL (the raw-main URL above,
  or a release URL once releases contain the file); when the only keys starting with `@`
  anywhere are that root `@context`, an optional root `@id` and `@type` on any object; and when
  every `@type` value is a string or an array of strings. A reader sets the root `@context` and
  every `@type` aside. A root `subjectOf` string is the FHR `documentation` value; a document
  with both `documentation` and `subjectOf` is invalid. The export terms `@id`, `keywords`, `url`
  and `conformsTo` at the root are not FHR fields: they are set aside, with a warning. What
  remains is FHR JSON, including nested keys without a term.
- [J2] Duplicate object keys are invalid, as in JSON.
- [J6] The resulting metadata must validate against `fhr.json`.
- [J7] **Writing.** A writer emits the document described in
  [What the document contains](#what-the-document-contains), serialised as JSON with two-space
  indentation, non-ASCII characters unescaped and a final newline. For the JSON examples the
  result is byte-identical to `examples/*.fhr.jsonld`.
