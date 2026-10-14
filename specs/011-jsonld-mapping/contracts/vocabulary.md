# Contract: the FAIR-bioHeaders vocabulary (`terms#`)

**Feature**: 011-jsonld-mapping | **Repository**: FAIR-bioHeaders-Specification | Research: R-05, R-08, R-10, R-17

The vocabulary defines every FHR-specific term that the JSON-LD context uses (FR-002, FR-008).
It is **generated** by `scripts/make_jsonld.py` from the LinkML model, and it is committed.
Nobody edits it by hand; `make_jsonld.py --check` fails on drift.

## Namespace

- `https://w3id.org/fair-bioheaders/terms#`. It is unversioned: a term IRI never changes and is
  never reused with another meaning.
- The local name is exactly the LinkML slot or class name, which is the FHR key. Examples:
  `seqcol_id`, `commandLineOption`, `VitalStats`.
- The vocabulary is family-wide. Terms that later header types share (FHT, FHP, FHGFF3) reuse
  the same IRI. A new term is added only when a header type needs it, with a changelog entry.
- **Deprecation.** A term is never deleted. It gains `owl:deprecated true` and a
  `dcterms:isReplacedBy` if a replacement exists.

## Files

| File | Purpose | Media type served |
|---|---|---|
| `jsonld/terms.ttl` | RDF vocabulary (Turtle) | `text/turtle` from GitHub Pages (raw GitHub serves `text/plain`, research R-09) |
| `jsonld/terms.jsonld` | The same vocabulary as JSON-LD | `application/ld+json` from GitHub Pages |
| `docs/TERMS.md` | Human documentation page; rendered to `terms/index.html` on Pages, the default redirect target | HTML |

## `jsonld/terms.ttl` layout

The prefixes are fixed, the term blocks are sorted (classes first, then properties, each
alphabetically by local name), and the file ends with a trailing newline. Every term carries:

| Predicate | Required | Source |
|---|---|---|
| `a rdf:Property` or `a rdfs:Class` | yes | LinkML slot or class |
| `rdfs:label` (`@en`) | yes | The FHR key itself, for example `"seqcol_id"@en` |
| `rdfs:comment` (`@en`) | yes | The LinkML description (equal in meaning to the `fhr.json` description) |
| `rdfs:isDefinedBy <https://w3id.org/fair-bioheaders/terms>` | yes | constant |
| `sdo:domainIncludes` | properties | The `class_uri` of every class that uses the slot (FHR → `sdo:Dataset`) |
| `sdo:rangeIncludes` | properties | `sdo:Text`, `sdo:Number`, `sdo:Integer` or `sdo:URL`, or the type IRIs the writer emits for the range class (for authors `sdo:Person`, `sdo:Organization` and `fhr:Agent`) |
| `rdfs:subPropertyOf` | when stated | From a LinkML `broad_mappings` entry that points at an `sdo:` property. In release 1 that is `fhr:accessionID rdfs:subPropertyOf sdo:identifier`. The mapping table must agree (test) |
| `rdfs:subClassOf` | classes | `sdo:Thing` for `fhr:Agent`; `sdo:StructuredValue` for `fhr:VitalStats`. LinkML source: the class annotation `vocabulary_subclass_of` (and `vocabulary_comment` for the `fhr:Agent` comment, since the `Author` class description describes authors) |
| `skos:closeMatch` | when stated | From LinkML `close_mappings`. In release 1 that is `fhr:Agent skos:closeMatch dcterms:Agent` |
| `owl:deprecated`, `dcterms:isReplacedBy` | when deprecated | |

The ontology header node:

```turtle
@prefix fhr:     <https://w3id.org/fair-bioheaders/terms#> .
@prefix sdo:     <http://schema.org/> .
@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:     <http://www.w3.org/2002/07/owl#> .
@prefix skos:    <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

<https://w3id.org/fair-bioheaders/terms> a owl:Ontology ;
    rdfs:label "FAIR-bioHeaders vocabulary"@en ;
    rdfs:comment "Terms for FAIR-bioHeaders metadata that have no schema.org equivalent. Generated from the FAIR-bioHeaders-Specification LinkML model; do not edit."@en ;
    dcterms:license <https://www.mozilla.org/en-US/MPL/2.0/> ;
    rdfs:seeAlso <https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/TERMS.md> .
```

Example term blocks (illustrative; the generated file is authoritative):

```turtle
fhr:Agent a rdfs:Class ;
    rdfs:label "Agent"@en ;
    rdfs:comment "A person or organization that the FHR record does not classify; FHR records the kind of agent only through an ORCID or ROR identifier."@en ;
    rdfs:subClassOf sdo:Thing ;
    skos:closeMatch dcterms:Agent ;
    rdfs:isDefinedBy <https://w3id.org/fair-bioheaders/terms> .

fhr:seqcol_id a rdf:Property ;
    rdfs:label "seqcol_id"@en ;
    rdfs:comment "Unprefixed GA4GH refget sequence collection top-level digest (sha512t24u); supplied by the user, not calculated by FHR."@en ;
    sdo:domainIncludes sdo:Dataset ;
    sdo:rangeIncludes sdo:Text ;
    rdfs:isDefinedBy <https://w3id.org/fair-bioheaders/terms> .
```

### Terms in release 1

These are derived from research R-03.

- **Classes (2)**: `Agent` and `VitalStats`.
- **Properties (22)**:
  - top-level: `schemaVersion`, `metadataAuthor`, `voucherSpecimen`, `accessionID`,
    `instrument`, `relatedLink`, `masking`, `vitalStats`, `checksum`, `assemblySoftware`,
    `assemblyProtocol` and `seqcol_id`;
  - in `vitalStats`: `L50`, `N50`, `L90`, `N90`, `totalBasePairs`, `numberContigs`,
    `numberScaffolds`, `readTechnology` and `gcContent`;
  - in `assemblySoftware`: `commandLineOption`.

The core slots that FHR schemaVersion 1 does not use (`derivedFrom`, `headerType`,
`relationship`) get **no** term until a header type uses them and #54 decides their vocabulary.

## `docs/TERMS.md` layout

The page is generated. It has a short introduction (namespace, licence, how to cite, link to
`docs/JSONLD.md` and the mapping table), then one section per term, sorted like the Turtle file:

```markdown
### seqcol_id

`https://w3id.org/fair-bioheaders/terms#seqcol_id`. Property.

Unprefixed GA4GH refget sequence collection top-level digest (sha512t24u); supplied by the user, not calculated by FHR.

- Used on: Dataset (the FHR record)
- Value: Text
- DCMI: none (see the [mapping table](../mappings/fhr-jsonld-dcmi.yml))
```

The heading text is exactly the local name, so GitHub's anchor is `#seqcol_id`. A test asserts
that every term has exactly one heading.

## w3id registration (maintainer action)

The rules below go into `ids/fair-bioheaders/.htaccess` in perma-id/w3id.org, before the
existing `fhr/` rules (maintainer decision 1 replaced the raw-GitHub targets of the first draft
with the GitHub Pages site built by `scripts/build_pages.py`). The header comment gains matching
bullets. A PR may be opened only by Adam Wright or David Molik, the administrators of
`/fair-bioheaders/`.

```apache
RewriteCond %{HTTP_ACCEPT} text/turtle
RewriteRule ^terms/?$ https://fhref.org/FAIR-bioHeaders-Specification/terms/terms.ttl [R=302,L]
RewriteCond %{HTTP_ACCEPT} application/ld\+json
RewriteRule ^terms/?$ https://fhref.org/FAIR-bioHeaders-Specification/terms/terms.jsonld [R=302,L]
RewriteRule ^terms/?$ https://fhref.org/FAIR-bioHeaders-Specification/terms/ [R=302,L]
RewriteRule ^fhr/(v[0-9]+\.[0-9]+\.[0-9]+)/jsonld/([^/]+)$ https://fhref.org/FAIR-bioHeaders-Specification/fhr/$1/jsonld/$2 [R=302,L]
```

The third rule is the 406-safe fallback: a client that accepts neither RDF form gets the HTML
page.

Checks before submitting (done 2026-10-10 against perma-id/w3id.org master):
1. `node tools/check/bin/w3id-check.js ids/fair-bioheaders`: "No problems found" (41 rules).
2. The Apache of `tools/server` (Docker), requesting `/fair-bioheaders/terms`:
   - `Accept: text/turtle` → 302 to `terms/terms.ttl`;
   - `Accept: application/ld+json` → 302 to `terms/terms.jsonld`;
   - `Accept: text/html` and `*/*` → 302 to `terms/`;
   - `fhr/v0.4.0/jsonld/fhr.context.jsonld` → 302 to the Pages copy;
   - `fhr/v0.3.1`, `fhr/v0.3.1/schemas/core.yaml`, `gff3-validator` and the root are unchanged.
3. The targets are live on Pages (the `jsonld-pages` workflow has run on `main`).

## Verification (FAIR-bioHeaders-Specification)

- `python scripts/make_jsonld.py --check`: the context, `terms.ttl` and `TERMS.md` are up to date.
- `tests/test_jsonld_vocabulary.py`:
  - `terms.ttl` parses with rdflib, which `requirements-linkml.txt` already installs as a
    LinkML dependency;
  - every `fhr:` IRI in the context and the mapping table is defined, with a label and a
    comment;
  - no term is defined twice;
  - every term has a heading in `TERMS.md`.
