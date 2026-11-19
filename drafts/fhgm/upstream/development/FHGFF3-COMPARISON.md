# FHGFF3 reuse and FHGM requirements

This is a design worksheet, not a field adoption table. Start by retaining
FHGFF3 meanings wherever possible. Subtype versus sibling remains undecided.

## Baselines

The inherited [header pin](../header/provenance.json) records shared commit
`bdcaecf759b5b2be5fd61bf8f39368a7e3963315` (FHGFF3 1.0 model). It is reference
material, not a selection of that older contract for FHGM. Current shared sources
must be compared before choosing a base; record the selected commit, schema
version and relevant differences in a design PR. Do not substitute moving main
for a versioned contract.

## Comparison worksheet

| Concept | Existing FHGFF3 starting point | FHGM question / evidence needed |
| --- | --- | --- |
| Contract identity | Required `schema`, `schemaVersion` | How does a subtype or sibling declare identity and get dispatched by tools? |
| Shared required metadata | `taxon`, `version`, `metadataAuthor`, `dateCreated`, `checksum` | Preserve meanings; clarify model version and dates against actual deposits. |
| Annotation identity | Required `annotation` | Can it name the contribution without changing its meaning? |
| Reference genome | FHR `annotates` checksum link and/or complete `genomeReference` | Retain authority/cardinality rules; can deposits supply required identity? |
| Sources and methods | Optional `source`, `annotationSoftware`, `annotationProtocol` | Which evidence and curation requirements fit existing objects? |
| Publication and data identity | Optional `scholarlyArticle`, `identifier`, `accessionID`, links | Keep model deposit, article and assembly separate; check multiplicity. |
| Contributors | Shared author objects; metadata author role | How are model authors and curators credited without conflating roles? |
| Model scope | Native GFF3 `ID`/`Parent` relationships | How does the header identify its locus/models and isoforms? |
| Revision lifecycle | Parent-file provenance and source references | Define replacement, split/merge and supersession; evidence is not necessarily a parent file. |
| Reuse terms | Optional `reuseConditions` | Record actual payload permissions separately from article licensing. |
| GFF3 serialization | Version directive first, leading `#~` block, defined end boundary | Reuse placement, interleaving and embedded FASTA behavior. |
| Integrity | Exact-byte checksum, excluding root checksum line | Reuse rules; transformations require recomputation, not a copied checksum. |
| Feature layer | Ordinary GFF3 types and relationships | Which additional constraints, if any, do worked examples demonstrate? |

## Decision test

Would every valid FHGM record validate against the selected FHGFF3 base with
unchanged meanings? Test both schema shape and type-selection rules: a new schema
URL is not automatically accepted as FHGFF3. If yes, favor a documented subtype;
if requirements conflict, use a sibling contract with compatible shared objects.
Neither an `x-` experiment nor a GitHub fork establishes adoption or runtime support.

## Validation boundaries

Report header/schema validity, GFF3 feature validity, checksum integrity,
reference matching and biological evidence assessment separately. A passing result
in one category does not establish the others. Do not design new feature syntax
merely to represent file-level provenance.

## Pilot comparison against FHGFF3 1.1

Use the published [v0.5.0 FHGFF3 schema](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.5.0/fhgff3.json)
at commit `170e677fbb6726a3f765373dbe1f214820000be7` as the comparison target
for this pass. The inherited mirror has its own pin.

| Concept | Pilot finding |
| --- | --- |
| Assembly identity | The S6k paper supplies an assembly accession. The deposit review did not establish a SeqCol digest or FHR checksum. The FHGFF3 identity requirement needs reference verification before either example can meet it. |
| Article and deposit | FHGFF3 offers `scholarlyArticle` and `identifier`. Keep the publication and model-deposit DOIs separate. Review how to identify individual companion files. |
| Scope and contribution | GFF3 feature relationships can carry locus and isoform structure after conversion. Curator credit, evidence and supersession need a separate semantics review with the journal. |
| Compatibility | The base schema permits `x-` keys and restricts the `schema` URI to FHGFF3. A profile with FHGFF3 identity could validate against this base if the locus-level annotation preserves the base meanings. A dedicated FHGM URI or ordinary new root fields would require separate dispatch or a contract change. |

See the [source review](examples/PILOT.md). Test the profile route with one
converted model and verify its reference linkage before deciding on type identity.

The [revision pilot](examples/revision/README.md) embeds two model records in
one FHGFF3 header. Each record points to its own GFF3 gene feature. Revising one
model preserves the other model's identity. The predecessor pointer combines
the prior annotation checksum with a model ID and version. FHGFF3 1.1 accepts
the extension even when the pointer is stale or names the wrong model.
Model-level resolution and curator acceptance require separate checks.

See the [INSDC coverage supplement](INSDC-COVERAGE.md) for the boundary between
annotation validation and embedded model checks.

See the [contract review and examples](CONTRACT-REVIEW.md) for the proposed decisions and compatibility results.
