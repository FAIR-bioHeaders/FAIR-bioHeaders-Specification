# Draft FHGM alignment with the INSDC annotation review

This supplement uses the [shared INSDC assessment](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/insdc-coverage.md)
and its [Annotation Minimum Specification v1.0 pin](https://github.com/insdc/minimum-specifcations/tree/41f0dc424748c9f7e50a8b6bda9b888218c4b65e/Annotations).
Assessment v2 and the FHGM pilots use
[FHGFF3 1.1 from v0.5.0](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.5.0/fhgff3.json).
The matrix applies the same ratings to FHGFF3 1.0 and 1.1 and counts only
standard fields. The experimental FHGM records add no coverage. Follow-up
checks are tracked in [FHGM #5](https://github.com/FAIR-bioHeaders/FHGM-Specification/issues/5).

| Assessment rows | Where the requirement belongs | FHGM finding |
| --- | --- | --- |
| AN.a, AN.b.iii, AN.b.vii | GFF3 syntax, coordinates and feature hierarchy | A model record points to a feature ID in its enclosing file. Resolve that pointer and its model scope separately. Use native GFF3 IDs and Parent relationships for gene, transcript and exon structure. |
| AN.b.iv–vi, AN.b.viii–ix, AN.c.i–ii | Feature, record-context or submission profile checks | Preserve the existing dispositions. Route placement decisions and missing rules through [validator #27](https://github.com/FAIR-bioHeaders/gff3-validator/issues/27). A model ID does not establish an INSDC locus tag. |
| AN.c.iii, AN.d | Translation and sequence-dependent validation | The S6k pilot verifies the deposited transcript and peptide against the reference. The validator still reports the two source stop codons kept outside the CDS. Record both outcomes without inferring submission acceptance. |
| AN-xref | Enclosing annotation and its reference assembly | The FHGFF3 genome link supplies assembly identity for embedded models. Scope each feature pointer to that annotation. Keep model ID, model version, publication, deposit, and predecessor annotation checksum distinct. |

The [S6k fixture](examples/s6k/README.md) provides evidence for reference
matching and documents the source conversion. The [revision fixture](examples/revision/README.md)
shows that a correct file checksum cannot distinguish a valid predecessor
from a pointer to the wrong model. Neither pilot establishes INSDC submission
readiness. Live submission-validator work is tracked in [shared #191](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/191).

Before drafting a contract, review unresolved and ambiguous feature targets,
transcript-only scope, same-assembly assumptions and predecessor resolution.
Record the curator authority for supersession separately from whether a
pointer resolves. Any proposed standard field, requiredness or constraint
needs its own schema review and an explicit disposition for affected INSDC rows.

The [draft contract v0.1 checker](model/README.md) implements local
gene-target checks for AN.a, AN.b.iii and AN.b.vii, record-versus-file
reference agreement and same-assembly pointer checks relevant to AN-xref.
These checks leave the existing coverage ratings in place. The
feature validator still owns coordinate and hierarchy checks, and the
reference check compares supplied identifiers across snapshots.
