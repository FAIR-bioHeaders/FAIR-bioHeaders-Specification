# FHT to INSDC: conditional mapping strategy

Status: **conditional mapping accompanying the approved initial FHT design**, revised October 24, 2026. This supersedes
the earlier mapping document's submission-ready/completeness conclusions.
Read the [coverage matrix](insdc-fht-coverage.md),
[research and decisions](fht-field-decisions.md),
[proposed spec 005 revision](005-rna-transcriptome-header/spec.md) and
[record designs](fht-record-designs.md) together.

## Baselines and scope

The minimum-specification comparison remains pinned to
`insdc/minimum-specifcations@41f0dc4`, categories v1.0. The October 24 research
uses the sources and shared/FHT revisions recorded in the decision proposal,
including the official ENA experiment XSD revision. These are distinct sources:
minimum-specification mapping does not replace live destination submission rules.

No FHT family schema is released. No exporter, deposit adapter or FHT community
profile is implemented by this document. It describes potential mappings, their
conditions and missing information; it does not establish that a minimal FHT
record satisfies every applicable minimum. #157 therefore remains open.

## Potential mappings and required checks

| FHT assertion | Potential destination | Conditions and losses |
| --- | --- | --- |
| taxon.name / taxon.uri | Organism/taxonomy | Actual identity and required rank must be checked; URI syntax alone does not establish rank or sequence origin |
| metadataAuthor | Header-author attribution | Not automatically deposit submitter, sequence producer, owner or institutional affiliation |
| assemblySoftware | Method, version and options | Shared Software has a real version member. Retain ordered options; do not claim missing version data is present |
| moleculeType | Per-record biological molecule type | Proposed optional file-wide class is not per-record evidence; do not translate total RNA, cDNA or ncRNA mechanically |
| libraryStrategy | Experiment library strategy | Use supplied experiment values, such as RNA-Seq; do not put selection or source values in this field |
| strandedness | Experiment/protocol description | Requires an explicit read/read-1 convention; proposed FHT normalized terms are not an ENA-controlled enum |
| sequencingRuns | Input run links | Actual SRR/ERR/DRR accessions and their associations must be checked. SRS is a sample class, not a run |
| relatedLink | BioProject, study, BioSample, experiment/run or other source URLs | Preserve actual URLs; this is not an exporter that resolves categories automatically |
| identifier / accessionID | Transcriptome's own identifier/accession | Do not replace with study/sample identifiers or assume GCA_/GCF_ genome accessions identify a transcriptome |
| dateCreated | Described resource creation date | Not sample collection date or sequencing date |
| version / checksum | Resource revision / file-byte identity | Neither supplies the destination's accession lifecycle rules. Header edits change the checksum even without sequence changes |
| scholarlyArticle | Publication DOI | Only the supplied article DOI; do not promote it to an assembly identifier |
| sample / voucherSpecimen | Partial source context | Tissue/stage/condition do not constitute a full BioSample, collection date, geography or submission alias |
| completeness / vitalStats | Producer-reported measurements | Neither establishes INSDC eligibility, sequence-content validity or a universal quality threshold |
| derivedFrom | Reviewed family-file provenance | Must match actual source relationships; genome guidance alone does not prove sequence extraction from that genome |

## What still belongs outside the header

NCBI's [TSA documentation](https://www.ncbi.nlm.nih.gov/genbank/tsa/) requires
input read deposition and associated run, BioProject and BioSample accessions,
and imposes sequence and submitter conditions. None can be inferred from a
minimal FHT field set. Annotation extraction and third-party data reuse are not
automatically eligible for TSA solely because the output contains transcripts.
Use the destination's actual submission route and requirements.

Keep per-record molecule/source assertions, submission contacts, affiliations,
sample checklists, geographic location, collection date and repository lifecycle
metadata in their proper layers. Actual exporters must report missing or lossy
values and enforce target constraints at the submission boundary. Linked records
are references, not evidence that all required fields were supplied or verified.

Preserve T/U bytes in the source file. Any destination-specific normalization
creates a derivative and requires recomputed checksum/provenance; it cannot be
performed silently during header parsing or metadata projection.

## Profile and adoption boundary

The AgBioData FHR profile work is a draft precedent, not adopted FHT machinery.
A profile may add constraints only after the underlying fields, selection rules
and actual validator support exist. A JSON Schema metadata profile cannot itself
check FASTA alphabet, base percentages or sequence lengths; a separate content
validator/workflow is needed. No new profile ID or LinkML class is assigned here.

Base design choices are recorded in the decision record; exact model implementation still requires its own contract review.
Future target requirements must identify whether they need a profile, new field,
external metadata, content validation or no header action. Do not label every
missing target field covered merely because a future profile could be written.

## Remaining coordination

- #6: initial field-design and consultation disposition completed by PR #20 on
  merge, following David's recorded approval; further feedback remains welcome.
- #7: implement the approved core imports, exact model/types, migration, schema
  generation and versioning, coordinating final artifacts with shared publication.
- #8/#9: actual fixtures, conformance and installed toolkit support.
- Shared #157: finalize the coverage assessment and dispositions independently.

No curator endorsement, published contract, submission readiness or completed
minimums gate is claimed by this mapping.
