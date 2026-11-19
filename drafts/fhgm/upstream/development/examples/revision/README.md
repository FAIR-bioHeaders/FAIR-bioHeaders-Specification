# FHGM revision pilot

The [S6k pilot](../s6k/README.md) showed that contribution metadata fits in
an FHGFF3 extension. This follow-up treats FHGFF3 as the annotation file and
FHGM as a repeatable record describing one model within that file.

## Published use case

Flanagan, Hund and Chihade describe corrected gene models and provide an
associated dataset covering multiple published assemblies. The article
motivates capturing which model on which assembly is being revised and the
evidence for the change. The deposit's DataCite record links to the article
with `IsPartOf` and to a dataset version family with `IsVersionOf`. Neither
link establishes that a curator adopted a replacement for a specific model.

- [Article](https://doi.org/10.17912/micropub.biology.002355)
- [Dataset](https://doi.org/10.22002/hv4eg-wg213)
- [DataCite record](https://api.datacite.org/dois/10.22002/hv4eg-wg213)

The synthetic fixture uses no source payload from that study. One FHGFF3
header carries two model records under the experimental `x-fhgm-models` key.
Each record has a stable `modelId`, a `modelVersion`, a file-local
`featureId` pointing to its GFF3 gene feature and, since the draft contract
v0.1 update of 2026-11-12, its own `reference` assembly binding. Native GFF3
`Parent` relationships describe the gene's transcripts and exons.

The second annotation snapshot extends model A's exon and increments its
model version. Model B retains the same record and feature rows. The model A
predecessor pointer names the prior annotation checksum, model ID, and model
version. The annotation checksum covers both embedded records and the feature
payload. The assembly SeqCol digest is computed from the script's synthetic
one-record collection.

## Reproduce the comparison

Use Python with PyYAML and jsonschema installed. From this directory, point
the script at the released [FHGFF3 1.1 schema from v0.5.0](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.5.0/fhgff3.json).
The output directory must already exist.

```sh
out=$(mktemp -d)
python3 check_revision.py /path/to/fhgff3.json "$out"
for file in "$out"/*.gff3; do
  gff3-validate --no-header "$file"
  awk '!/^#~checksum:/' "$file" | openssl dgst -sha512-256 -binary | openssl base64 -A
  printf '\n'
  awk '/^#~checksum:/{print $2}' "$file"
done
```

| Case | FHGFF3 1.1 schema | File checksum | Predecessor check |
| --- | --- | --- | --- |
| Original annotation with A and B | Pass | Pass | No predecessor claim |
| A revised, pointing to prior A | Pass | Pass | Resolves to prior A in the supplied annotation |
| A revised, pointing to B in the correct prior annotation | Pass | Pass | Fails the same-model check even though B exists with the requested version |
| A revised, pointing to A with a stale annotation checksum | Pass | Pass | Fails the annotation checksum check |
| File-level `derivedFrom.relationship: supersedes` | Rejected at the relationship field | Generated in memory | Outside the base vocabulary |

All four emitted files passed feature checks with zero errors and warnings
using gff3-validator 0.1.0 at `c753f45`, with header checks disabled. OpenSSL
independently reproduced each file checksum.

## Design questions for curator review

The pilot assumes stable model IDs across revisions within the same assembly.
The experimental records keep FHGFF3 identity, while a separate check resolves
the predecessor at model scope. A resolved pointer identifies the prior
record. A curator decision is needed to establish accepted supersession.

Before standardizing the extension, decide who assigns stable model IDs, who
can declare supersession, and what source records that decision. Ask whether
isoform-only submissions need transcript-level scope and how to represent a
split, merge, or correction on a different assembly. Keep the publication,
deposit version, exact annotation snapshot, model identity and curator
decision separately identifiable.
