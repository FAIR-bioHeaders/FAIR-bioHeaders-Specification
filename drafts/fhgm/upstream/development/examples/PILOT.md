# FHGM pilot source review

Draft requirements evidence for [#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204) and the [dataset pilot #206](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/206).

## Publication context

| Article | Extended data | Design evidence |
| --- | --- | --- |
| [CG31087 in *D. arawakana*](https://www.micropublication.org/journals/biology/micropub-biology-002315/) | [Dataset](https://doi.org/10.22002/nz145-65h12) | The journal labels this bundle Dataset and lists FASTA, PEP and GFF. |
| [snu in *D. funebris*](https://www.micropublication.org/journals/biology/micropub-biology-002347/) | [Model](https://doi.org/10.22002/tqrd0-6z073) | The journal labels this bundle Model and lists the same file categories. It separately credits model contributors, article reviewers and nomenclature validators. |
| [yellow-f2 in *D. dunni*](https://www.micropublication.org/journals/biology/micropub-biology-002348/) | [Model](https://doi.org/10.22002/y3z7h-z8t72) | The journal provides the deposit DOI with an empty description. Inspect the archive before assigning file roles. |

Use these ortholog-model papers to design separate links for the article, the
deposited model and its reference assembly. Record contributor roles from the
source and keep journal review and nomenclature review distinct from file
validation. Cite the comparative gene and its reference separately from the
assembly on which the contributed model is located. Treat repository resource
labels as source metadata. Archive formats for these three papers remain open.

## Inspected deposits

Retrieved on 2026-11-10. Both are version 1.0 and list CC BY 4.0 in DataCite.
Archive SHA-256 values identify the downloaded ZIP bytes. Retain deposit attribution
and document changes when preparing derived examples.

| Article | Deposit | Archive and primary members | Feature context |
| --- | --- | --- | --- |
| [Glys in *D. busckii*](https://www.micropublication.org/journals/biology/micropub-biology-001095/) | [CaltechDATA](https://data.caltech.edu/doi/10.22002/apf5b-xyg45), [rights metadata](https://api.datacite.org/dois/10.22002/apf5b-xyg45) | `DbusGB1_GlyS.zip`, with `DbusGB1_GlyS.{gff,fasta,pep}` under the matching directory | `CP012526`, reverse strand, four transcript and four peptide records. The paper describes two distinct translations. Assembly accession and sequence version still need confirmation. |
| [S6k in *D. ananassae*](https://www.micropublication.org/journals/biology/micropub-biology-001030/) | [CaltechDATA](https://data.caltech.edu/doi/10.22002/e86gh-a7p16), [rights metadata](https://api.datacite.org/dois/10.22002/e86gh-a7p16) | `DanaCAF1_S6k.zip`, with `DanaCAF1_S6k.{gff,fasta,pep}` under the matching directory | `scaffold_13337`, forward strand, two transcript and two peptide records. The [article text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12464738/) identifies assembly `GCA_000005115.1`. Sequence matching remains open. |

- `DbusGB1_GlyS.zip` SHA-256: `6be9a44aa3a3beb27b01766ad7e75cb9c0b0e3e69189bff14b65683ac3a79454`
- `DanaCAF1_S6k.zip` SHA-256: `2328ee717b9124119f03503694fe8c080778e5d04bede36bbeae11b4a84d974c`

Both ZIPs passed `unzip -t`. The annotation members start with a browser
`track` line and use quoted `gene_id` and `transcript_id` attributes on
`exon`, `CDS` and `stop_codon` rows. A GFF3 fixture needs an explicit conversion
that reconstructs gene and transcript features and `ID`/`Parent` relationships,
documents stop codon handling, and checks coordinates, strand and CDS phase
against the source and companion files. The original archives remain the
provenance records. A model revision and a noncoding example are still needed.

The [S6k fixture](s6k/README.md) reproduces the converted GFF3 feature payload, verifies it against the NCBI
assembly and tests a FHGFF3 1.1 header with an experimental contribution field.
