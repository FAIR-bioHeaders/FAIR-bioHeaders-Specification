# Draft FHGM contract v0.1 fixtures

Status: native draft contract v0.1 (proposal) under shared
[#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204)
review; no publication, no support claims. These fixtures exercise the
[draft model-level checker](../../model/README.md). All content is synthetic:
the fictional accessions, model IDs and evidence strings are placeholders scoped
to this directory, and the assembly link is the
[revision pilot](../revision/README.md) synthetic one-record collection.
[make_fixtures.py](make_fixtures.py) regenerates every `.fhgff3.gff3` file here
byte-for-byte; `python development/model/check_draft.py /path/to/fhgff3-v0.5.0.json`
asserts the expectations below.

Positives:

| Fixture | Expectation |
| --- | --- |
| `valid-single.fhgff3.gff3` | One record, no predecessor claim; passes base, transport and record contract. |
| `snapshot-v1.fhgff3.gff3` | Two records (`model-a` v1, `model-b` v1); the pinned snapshot the rejections below reference. |
| `snapshot-v2.fhgff3.gff3` | Two-record revision chain resolving within the pinned snapshot: `model-a` v2 carries a predecessor pointer to v1 and reports `resolvable`; `model-b` is unchanged with no claim. |

Rejections (each lists the model-level verdict; the released base schema and
exact-byte checksum accept **every** rejection fixture — verified in
`check_draft.py` — the demonstrated gap the separate checker exists to close):

| Fixture | Verdict | Base schema |
| --- | --- | --- |
| `pointer-absent-snapshot.fhgff3.gff3` | `unresolvable`: the predecessor snapshot is the current file or was not supplied (stale-pointer case). | Valid |
| `ambiguous-model-id.fhgff3.gff3` | `ambiguous`: two records share `model-a` in one snapshot, so no pointer can select one. | Valid |
| `version-reuse.fhgff3.gff3` | `unresolvable`: the revision reuses the predecessor `modelVersion`. | Valid |
| `pointer-version-mismatch.fhgff3.gff3` | `unresolvable`: the pointer claims version `9`; the pinned snapshot records `1`. | Valid |
| `predecessor-name-mismatch.fhgff3.gff3` | `unresolvable`: the pointer names the unchanged neighbor `model-b` (the neighbor case from PR #4). | Valid |
| `version-gap-skip.fhgff3.gff3` | `unresolvable`: with both snapshots supplied, the pointer skips `snapshot-v2`, the recorded successor of the pointed record — version-gap misuse. | Valid |
| `record-without-reference.fhgff3.gff3` | Record contract violation: `reference` is required so a record keeps its own assembly binding. | Valid |
| `record-reference-conflict.fhgff3.gff3` | Checker rule 3: the record reference names another accession than the file genome link. | Valid |

To regenerate and compare:

```sh
out=$(mktemp -d)
python3 development/examples/model/make_fixtures.py "$out"
for file in development/examples/model/*.fhgff3.gff3; do
  cmp "$file" "$out/$(basename "$file")"
done
```

The real-provenance counterpart lives in the
[S6k example](../s6k/README.md), where the same draft record shape wraps the
attributed deposit-derived fixture. No fixture here asserts curator
acceptance, biological correctness or INSDC readiness.

These eleven fixtures are also vectors: the
[conformance manifest](../../conformance/manifest.json) cites their committed
bytes in place rather than copying them, and adds generated vectors, three
context-dependent re-runs of the bytes above, and the contract examples. Run
`python3 development/conformance/run_conformance.py --base-schema
/path/to/fhgff3-v0.5.0.json` for the separately reported base, checksum, GFF3 and
model layers across the whole set.
