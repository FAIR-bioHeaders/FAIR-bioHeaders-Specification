# Draft FHGM contract examples

Status: native draft contract v0.1 (proposal) under shared
[#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204)
review; no publication, no support claims.

These synthetic fixtures use the released FHGFF3 1.1 identity and add one
experimental header key, `x-fhgm-models`. The fictional accession and model
IDs are scoped to this demonstration. The reference digest describes the
one-record synthetic collection in the [revision pilot](../revision/README.md).
Both records were updated to the draft v0.1 shape on 2026-11-12: each now
carries its own `reference` assembly binding, and every checksum, including
the rich fixture's predecessor pointer to the minimal snapshot, was
recomputed from the edited bytes.

- [Minimal](minimal.fhgff3.gff3) describes one noncoding locus with one
  transcript and one exon. The model carries an ID, version, feature pointer
  and record reference binding.
- [Rich](rich.fhgff3.gff3) describes the next snapshot of that locus, now with
  two isoforms. It adds an experimental predecessor pointer, contributor role
  and evidence record. The annotation title and protocol remain ordinary
  FHGFF3 fields. The predecessor checksum is the minimal fixture's checksum,
  and the model-level checker resolves that pointer.

The added header metadata lives entirely under the experimental key. The
feature payload uses ordinary GFF3 coordinates and native `ID` and `Parent`
relationships. A model-layer validator would resolve the selected feature and
check its type and scope, while a GFF3 validator checks the feature graph.
There is no CDS or protein requirement for a noncoding model.

Both headers validate against the released FHGFF3 1.1 JSON Schema at
`v0.5.0`, with format checking, and their exact-byte checksums verify. See
the [review and compatibility matrix](../../CONTRACT-REVIEW.md) for limits
and recommendations.
