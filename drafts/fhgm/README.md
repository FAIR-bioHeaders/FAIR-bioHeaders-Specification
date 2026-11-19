# FHGM shared publication candidate — unpublished

This package submits the accepted owning FHGM work for joint shared review.
It is a draft review artifact under V7, not a published contract, release,
header type, consumer repin or curator acceptance. No w3id alias is created;
FHGFF3 file schema identity and released contracts are unchanged. The owning
development repository remains the V7 draft authority; this shared mirror is
not a new reader opt-in URL.

## Concrete proposal for joint review

| Item | Candidate |
| --- | --- |
| Native contract name/version | FHGM native model contract, `0.1` (the existing owning v0.1 draft label; proposed publication label) |
| Current review artifact | `upstream/development/model/fhgm-model.schema.json` |
| Future shared publication path | `model-contracts/fhgm/0.1/fhgm-model.schema.json` — proposed only; not created here |
| Future identifier | `https://w3id.org/fair-bioheaders/model-contracts/fhgm/0.1` — proposed only; not minted or served here |
| Release vehicle | Specification `v0.8.0`, separately gated after FHT `v0.7.0` |
| File identity | Released FHGFF3 1.1/1.2 identity; no FHGM header `schemaVersion`, in-record schema field or header-registry row |
| Native schema mechanism | Existing hand-authored JSON Schema through v0.x; no LinkML migration |
| Conformance | Separate FHGM checker/vector lane, preserving local K/B namespaces and supplied-history contexts |

Joint review must accept or revise this concrete identifier/path/version package
before publication. This proposal adds no contract keyword or validation change.
Adoption of the D4–D6 semantics is already recorded in
[the accepted owning decision record](upstream/development/conformance/DECISIONS-2026-11-19.md).
Do not reopen those selected choices as new policy questions.

## Exact source and absorption boundary

`source.json` records accepted FHGM merge
`d9d131a02b042023f4784d842a874232fc891069` and every copied path, byte size and
SHA-256. `upstream/` preserves the complete owning `development/` dependency
tree, its conformance tests, `.gitattributes` and `LICENSE`: 134 files,
914,784 bytes. Keeping the relative paths preserves generator imports,
source fixtures and predecessor contexts. These are unchanged owning bytes,
including dated historical prose; this README states the shared candidate's
current status.

`check_source.py` checks the local file set and actual bytes. Its `--upstream`
mode independently enumerates the selected pinned git tree, checks the checkout
HEAD and compares each authoritative blob. Thus deleting a file and its manifest
entry together is detected by the source comparison. No moving `main` is used
as the suite or draft-contract authority. Carrier schemas are read separately
from their actual shared release tags, and the exact owning runner verifies
their registered digests.

This is the actual shared mirror and executable candidate lane requested by
FHGM #9. It does not claim full issue acceptance before joint review; shared
#204 and FHGM #8/#9 remain open. Transcript-only, split/merge and assembly
migration remain explicitly deferred. External ID minting and acceptance of
particular revisions remain curatorial matters, not implicit model predicates.
The Project 12 publication-deposit pilots do not become new foundation work.

## Run the candidate

Use the owning suite's explicit installed dependencies (`fair-bioheaders[jsonld]`
0.11.0, jsonschema 4.26.0 and gff3-validator 0.1.0 without the headers extra).
From the shared checkout:

```sh
python drafts/fhgm/check_source.py --upstream /path/to/exact-owning-checkout
python -m unittest discover -s drafts/fhgm -p test_candidate.py -v
git show v0.5.0:fhgff3.json > /tmp/fhgm-base-v050.json
git show v0.6.0:fhgff3.json > /tmp/fhgm-base-v060.json
python drafts/fhgm/upstream/development/conformance/run_conformance.py \
  --base-schema /tmp/fhgm-base-v050.json \
  --base-schema /tmp/fhgm-base-v060.json --matrix \
  --gff3-validate /path/to/gff3-validate --report-json /tmp/fhgm-evidence.json
python drafts/fhgm/check_receipt.py /tmp/fhgm-evidence.json --exercise-guards
python -m unittest discover -s drafts/fhgm/upstream/tests -p test_fhgm_conformance.py -v
```

The workflow checks 92 vectors under both bases and uploads the actual JSON
receipt. The receipt verifier checks all 184 visits against the independently
reviewed expectations, recomputes the separate evidence counts and requires
real GFF3 execution. Expected not-run cases cannot become full passes or complete
vector matches. Its eight controls detect fabricated passes, unsupported rejections, inflated counts, skipped layers,
unavailable supplied-history predicates and omitted, wrong or duplicated
history subjects. Invalid execution prerequisites fail rather than producing an
aggregate success claim.

## Publication and acceptance gates

Before any release, David and Adam review the concrete package above, source
compatibility, serialization, INSDC boundaries and the actual CI evidence.
Publication then needs its own reviewed release artifacts, release object and
identifier/alias actions; none is performed by this PR. Existing consumer pins,
CEDAR templates, website promotion and package support are separate follow-ups,
not silently refreshed here. A technical model pass never establishes feature
graph correctness, biological validity or curator acceptance.

Original source notices are preserved. Government source rows retain their
original status; authored FAIR BioHeaders material follows the family license
split in `upstream/LICENSE`. No inherited feature-model tree is imported.

## Measured candidate validation

The copied suite matched all 184 dual-base vector checks. The actual receipt
contained 184 visits, 728 selected-carrier predicates evaluated, 736 layer
expectations compared, 174 complete vector matches and 48 full model passes;
ten expected not-run visits entered neither complete count. All eight receipt
controls were detected. Independent pinned-blob/file-set comparison verified
all 134 copied files. Ten candidate parity/input-binding tests, 61 exact owning conformance
tests and the dual-base draft self-check passed locally. These are draft
technical results; joint package acceptance and publication remain separate.

The receipt wrapper requires carrier first and every declared predecessor
subject, with multiplicity and order, for a full pass. Matrix twins use the
same committed predecessor inputs. The byte-exact owning receipt labels history
by basename: if different declared files have the same basename, this wrapper
refuses ambiguous identity rather than claiming a complete match. Repeating the
same canonical file is permitted only with the matching number of receipts.
The PR review's whole-snapshot omission, wrong-subject and duplicate-subject
controls leave other evidence and aggregate counts unchanged and must still fail.

A reported model rejection must have at least one actual rejecting carrier
predicate. The additional actual-receipt control changes the last such
predicate to pass while leaving the full rejection and counts unchanged; it
must fail for unsupported evidence, not an incidental count mismatch. This
preserves the user's native correction in commit `4aa3357`.

The candidate-local `.gitattributes` marks the entire copied `upstream/` tree
as byte-preserved, including model schemas and code that the owning nested
attributes did not cover. A fresh `core.autocrlf=true` checkout regression uses
actual representative source bytes. Without the candidate rule its schema/code
controls convert to CRLF; with the rule every representative remains exact.
No byte in the copied source tree is edited to achieve this.
