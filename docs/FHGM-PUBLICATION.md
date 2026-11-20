# FHGM native 0.1 publication preparation

## Selected package and authority

David accepted the concrete reviewed native model 0.1 package and later stated
“I can speak for Adam on this, he approves” in the coordinating chat, recorded
on [#211, comment 7025645941](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7025645941).
This records joint package acceptance through the operating agent; it is not a
fabricated native human PR review or an assertion that publication occurred.

The candidate artifact is
[`model-contracts/fhgm/0.1/fhgm-model.schema.json`](../model-contracts/fhgm/0.1/fhgm-model.schema.json).
The selected identifier is
`https://w3id.org/fair-bioheaders/model-contracts/fhgm/0.1`; it must resolve to
that artifact at the actual immutable v0.8.0 release. No alias is created by
this preparation. v0.8.0 follows actual FHT v0.7.0, with a distinct release gate.
Native model selection stays outside the record. There is no FHGM header
schemaVersion, record schema field or header `schemas/versions.json` row.

This is a schema resource identity/publication addition. The new schema differs
from the accepted native schema only by the resource-level `$id` and JSON
formatting; no field, requiredness, enum, predicate or existing identifier changes.
Its internal fragment references keep the same targets. The exact crosswalk and
byte digests are in `model-contracts/fhgm/0.1/publication.json`. The owning native
schema, transport overlay, semantic checker, generators, examples and 92 vectors
remain untouched under `drafts/fhgm/upstream/`. No historical fixture is relabeled
as newly published support.

The selected source is owning commit
`d9d131a02b042023f4784d842a874232fc891069`. The 134-file dependency closure is
sealed by `drafts/fhgm/source.json` SHA-256
`16cd2d029424877305b63b689a415632ab2b1b3443ee435d11e23ef6c1a2efa4`.
Its native schema SHA-256 is
`b7075e5872e0a5ffce5ae61c590ce182f1f219fa269413cad3b1a966753cfeae`.
The accepted D4–D6 scope includes gene-level noncoding models and bounded
immediate-predecessor history; transcript-only, split/merge and assembly migration
remain deferred. No extra INSDC field or schemaVersion is added; the existing
coverage/limitations remain, and model metadata is not deposit readiness.

## Reproduce native publication validation

Use an isolated Python environment with the exact owning-suite dependencies:
`fair-bioheaders[jsonld]==0.11.0`, `jsonschema==4.26.0`,
`gff3-validator==0.1.0` without its headers extra. From this shared checkout:

```sh
python scripts/fhgm_publication.py
python -m unittest discover -s tests -p test_fhgm_publication.py -v
git show v0.5.0:fhgff3.json > /tmp/fhgm-native-base050.json
git show v0.6.0:fhgff3.json > /tmp/fhgm-native-base060.json
python scripts/fhgm_publication.py --run-conformance \
  --base-schema /tmp/fhgm-native-base050.json \
  --base-schema /tmp/fhgm-native-base060.json \
  --gff3-validate /absolute/path/to/venv/bin/gff3-validate \
  --report-json /tmp/fhgm-native-new-receipt.json
```

The receipt path must be fresh, never an old success file. The wrapper first
checks every accepted source byte and file-set against the pinned manifest;
then checks schema structural identity after removing only `$id`. It creates a
private execution copy, substitutes the native schema, and updates only that
schema's digest/size in the private conformance provenance. The unchanged owning
runner, checker, examples, vector bytes, IDs and independently recorded
expectations then run all 92 vectors on both registered carrier bases. This
explicit new provenance counterpart does not edit the accepted source tree or
regenerate expectations. The existing eight receipt mutation guards must pass.
The emitted receipt additionally names the exact native identity/schema digest.
CI executes both the old exact draft lane and this native counterpart lane.

A successful suite execution means the actual outcomes matched the recorded
expectations. It does not mean every model passed. Expected not-run visits stay
outside complete-vector/full-model passes; feature validation, checksums,
base header and model predicates remain distinct. Missing or unusable bases,
validator, schema or source refuse execution. Advisory freshness does not gate
or automatically repin these immutable authorities.

## Actual receipts and release boundary

Local native counterpart execution on November 19, 2026 matched all 184 visits
(92 vectors on each carrier lane), with 728 evaluated predicates and 736 layer
comparisons. There were 174 complete vector matches, 48 complete model passes,
and **10 expected not-run visits**, excluded from both complete counts. All GFF3
visits ran; no GFF3 skip was counted as passing. All eight receipt mutation
controls were detected, five publication identity/source/prerequisite controls
passed, ten existing candidate controls passed, and independent owning Git-blob
comparison verified all 134 preserved source files. This is measured technical
candidate evidence, not a release or biological/curator approval. The exact
receipt is attached to the preparation PR / CI artifact;

CI uploads `fhgm-native-unpublished-evidence` separately from the exact draft
receipt. No skipped GFF3 execution is counted as passing.

Before v0.8.0: independently review the current artifact/head, complete all
applicable CI and installed-consumer readiness, verify actual preceding FHT
publication, and finalize release metadata deliberately. Publication requires the
landed main commit, immutable tag, GitHub Release and actual archive/fixed
identifier evidence. Set up and probe the selected alias only against the real
tag; never invent a DOI. Root coordinates those separate actions. A merge of
this candidate alone is neither a release nor default consumer promotion.

After actual publication, refresh the toolkit/model pins, default selection and
installed receipts deliberately, then hand the named released artifact/runtime
to website and Nextflow consumers. Preserve the old draft lane and fixture
history. Downstream microPublication pilots are Project 12 work and add no
Project 9 completion gate; model/biological curator acceptance remains separate.
