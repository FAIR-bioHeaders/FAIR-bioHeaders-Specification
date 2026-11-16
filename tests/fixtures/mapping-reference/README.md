# Metadata-only reference to an externally held assembly

This is a reusable source-reference example for #56, **not** a complete FHR
header, source file, export profile, deposit or downstream pilot. No sequence or
annotation file was downloaded. The example does not claim that the author of
this metadata owns, archives or has verified the assembly's bytes.

`ncbi-response.json` is the unmodified NCBI Datasets API response downloaded on
2026-11-16 from the URL in `reference.json`. Its actual downloaded byte length
and SHA-256 are recorded there. `reference.json` transcribes the accession,
assembly name, organism, supplied submitter and repository release date from that
snapshot. Tests verify the transcription and provenance offline. NCBI metadata
is attributed to its source; the raw response is not relicensed as an authored
FAIR-bioHeaders fixture. This example's documentation and authored representation
follow the repository contribution terms.

A human-readable reference can identify the resource as:

> *Drosophila melanogaster*, “Release 6 plus ISO1 MT”; NCBI RefSeq assembly
> `GCF_000001215.4` (repository release date: 2014-08-01).
> https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000001215.4/

The accession includes its accession version. Do not invent a separate assembly
version, creator list or resource DOI. The source's submitter string is preserved
as **submitter**, not automatically converted into an assembly creator. The
repository release date is not silently relabelled assembly creation, article
publication, specimen collection or deposition date. A separately verified
article would have its own identifier and attribution; none is supplied here.

## Relation to the adopted foundation and deferred targets

| Layer | What this reference supplies / does not establish |
| --- | --- |
| Qualified DCMI foundation | Explicit resource identity/title/source information illustrates the resource boundary. It lacks a complete FHR source and therefore is not an input to the adopted assembly exporter. Do not fabricate required metadata or checksum to pass it. |
| Supplemental context | An explicit title and distinct record/resource identities can describe scope, but context never manufactures the missing complete source or author roles. |
| DataCite/bibliography | Preserve supplied accession/title/repository/date roles for future reviewed adapters. Missing creators, resource DOI and other target-required assertions remain gaps; no DataCite validity or formatted citation profile is claimed. |
| Exact file / parent identity | Metadata alone establishes neither downloaded sequence bytes, exact file checksum, SeqCol digest nor verified parent-file identity. Repository-reported statistics are not byte evidence. |
| Archiving / persistence | A source URL records where the metadata was found; it does not transfer possession, archive a sequence, register an identifier or guarantee future resolution. |

The stable accession is the reference's identity. The live API response is only a
dated observation, not a promise that all future responses are byte-identical.
Tests use the pinned snapshot and make no live requests.
