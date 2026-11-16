# Qualified DCMI foundation: consumer handoff

This implements the adopted scope in [mapping v1](README.md), not a new profile
identifier. No new header fields, target equivalences or registration behavior.
The serialized context token remains `0.1.0-draft.1`.

## Inputs and refusal boundary

Accept a complete FHR v0.4.0 / schemaVersion `"2.0"` metadata object and the
separate context conforming to `mappings/proposals/assembly-export-context.schema.json`.
Use the fixed released source schema, with format checks. The shared
`check_mapping_context.py` checks context/identity/conflicts, not full source
validity. Refuse unknown versions, other types and raw-main citations explicitly;
never fall back to a newer schema or infer a type from the output filename.

Keep title/resource/record identity explicit. Reject duplicate keys and non-JSON
numeric constants when reading JSON. Reject invalid context and all documented
identity/date conflicts before emitting Turtle. For readable inputs, a refused
operation may still preserve the original input bytes and a diagnostic report in
a fresh output bundle; it must not emit Turtle or label the refusal a successful
projection. A metadata-only external reference is not a complete FHR record. No
sequence or live authority is fetched.

## Exact semantic projection

Use `http://purl.org/dc/terms/` predicates and the pinned DCMI vocabulary.

| Input | Subject and output |
| --- | --- |
| context.resourceIRI | Resource subject, `a dctype:Dataset`, and literal `dcterms:identifier`. |
| context.metadataRecordIRI | Separate metadata subject, `a dctype:Text`, `dcterms:subject` → resource. |
| context.title | Resource `dcterms:title`; no genome fallback. |
| source.schema | Metadata record `dcterms:conformsTo` → cited schema IRI. |
| source.assemblyAuthor / metadataAuthor | Resource / record `dcterms:creator` → distinct generic Agents with labels and optional literal identifiers. |
| source.dateCreated | Resource `dcterms:created` as `xsd:date`. |
| source.taxon.uri | Resource `dcterms:subject` → supplied taxonomy IRI, when present. |
| context.publisher | Resource publisher → generic Agent with name label and optional literal identifier. |
| context.publicationDate | Resource `dcterms:issued` as `xsd:date`, only when supplied. |
| source.relatedLink / assemblyProtocol | Resource generic relations → supplied IRIs. |
| source.scholarlyArticle | Resource generic relation → DOI resolver IRI for a syntactically valid supplied article DOI; never resource identity. |
| source.reuseConditions | Resource rights → labelled RightsStatement, when supplied. |

The source schema's DOI shape is not evidence of a live DOI or registered entity.
If an otherwise source-valid article value cannot safely form the documented DOI
relation, preserve it and report that omission; do not invent a relation or reject
the entire source as though a new core constraint had been adopted.

`resourceDOI` and `publicationYear` are preserved context assertions/conflict checks;
the existing v1 fixture does not define an additional graph projection for them.
Do not silently add one. All 15 unsupported root fields and their reasons remain
in the inventory. Taxon names, nameType, source array order, resource version,
metrics and software/protocol detail remain in the preservation layer.

## Outputs and evidence

Produce qualified Turtle plus a machine-readable report and preservation copies
of **all** source/context data. Report at least the existing rich fixture's
profile identity, present-but-unprojected root paths, missing optional context,
ordering/classification/nested-structure losses, conflicts/refusals, and
registration readiness marked not assessed. A separate JSON report must not be
advertised as a DataCite/Crossref submission. File checksum verification is not
performed from metadata alone; the synthetic rich fixture's checksum is not proof.

The shared rich and minimal graph fixtures are hand-curated independent semantic
expectations. Compare parsed RDF graphs (blank-node labels and Turtle ordering
are serialization details), then require the consumer's **own** output bytes to
repeat for identical inputs. Inputs and preserved arrays must not be reordered or
mutated to make graph canonicalization easier. Escape literal/IRI special
characters safely; no opaque value may become Turtle syntax.

Required consumer checks: rich and minimal graphs; missing publisher/date/DOI;
separate creator subjects; quotes, Unicode, newlines and braces; preserved author
and link order despite graph order loss; nameType retained without inferred
Person/Organization; conflicts; unsupported source versions/types; invalid source;
no source/context mutation; repeated byte equality; packaged-data parity and
installed-wheel execution outside the checkout. At least one deliberately wrong
subject/date/creator expectation must fail comparison. Existing canonical
JSON-LD/schema.org and MIxS tests must remain unchanged and pass.

The implementation PR records its command/API, output filenames and report shape.
A subsequent package release records shipment; only then can the withheld official
label be reconsidered under the existing adoption decision. No Tools commit or
release is named as delivered by this handoff document.
