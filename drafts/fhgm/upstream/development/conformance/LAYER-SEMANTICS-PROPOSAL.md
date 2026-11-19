# Proposal: separately earned FHGM layer verdicts

Disposition: D4–D6 were selected by the maintainer on 2026-11-19. The
[decision and implementation record](DECISIONS-2026-11-19.md) is current;
questions below are historical proposal context.

Status: **proposed, not adopted**, 2026-11-16. Refs
[FHGM #22](https://github.com/FAIR-bioHeaders/FHGM-Specification/issues/22).
This document requests a maintainer decision before changing the manifest,
checker, downstream pins or consumer acceptance. FHGM remains a draft; this
proposal creates no field, schema identity, release or support claim.

## Problem and verified baseline

The sealed manifest at `c503ecf` contains 43 vectors. Eight cite K4: three
valid and five invalid. Their actual `layers.model` values are respectively
`pass` and `reject`; the issue body's statement that all eight say `pass`
is incorrect. This correction does not resolve the underlying ambiguity.

The manifest's `layers` description says an unavailable external GFF3 lane is
skipped and no FHGM rule depends on it. That means the external program is
optional, not that the carrier's feature rows are optional for K4.
The model contract's [featureId description](../model/fhgm-model.schema.json)
and [K4 text](../model/README.md#model-level-constraints-the-base-schema-cannot-enforce)
require resolution to a local gene row.

The current [checker](../model/validate_fhgm.py) calls `gene_targets` inside
`validate_snapshot` before checking records. It counts all decoded ID-bearing
rows, then requires exactly one matching row of type `gene` or `SO:0000704`.
It stops at embedded FASTA. Supplied predecessor snapshots also pass through
`validate_snapshot`. These are observations of current code, not additional
normative clauses. In particular, mixed gene/transcript duplicate IDs and the
SO spelling need explicit disposition rather than accidental adoption from code.

## Proposed reporting contract

Keep expected outcomes and measured outcomes separate. `layers` names the
expected result; it does not grant evidence that a consumer ran that check.
Each consumer reports actual status and a reason for each unavailable layer.

| Layer | Evidence needed for a measured verdict | Unavailable evidence |
| --- | --- | --- |
| base | Parsed metadata validated against the selected pinned released FHGFF3 bytes | not-run, with selection or capability reason |
| checksum | SHA-512/256 recomputed over the carrier's exact bytes under FORMAT rules | not-run; a recorded checksum is not verification |
| gff3 | An explicitly named external GFF3 validator actually run over the feature layer | not-run, naming the missing executor; no inferred accept |
| model | The advertised FHGM predicates evaluated with all their inputs | partial per-rule evidence or not-run; no complete model pass |

A complete vector result requires agreement for each layer in the claimed
acceptance scope. A consumer can publish model evidence separately from external
GFF3 evidence, but cannot count an omitted layer as matched. Keep separate
counts for vectors visited, rule predicates evaluated, layer expectations
compared, and complete vectors matched. Historical counts with different scopes
must not be relabelled as directly comparable.

A failed pin or invalid execution prerequisite refuses the run before scoring:
report the refusal and no aggregate pass/fail counts. This differs from a valid
run where a consumer deliberately does not implement a layer and reports its
scope as not-run.

## Per-rule inputs proposed for review

This table describes direct predicate inputs, not permission to skip other
predicates in a complete model verdict. A vector's `rule`/`rules` labels identify
its focus; they are not an exhaustive execution dependency list.

| Rule | Direct inputs | Feature rows needed directly? |
| --- | --- | --- |
| K1 | Carrier identity, parsed header and nonempty model array; selected released base | No |
| K2 | Each record and pinned record schema, including format assertions | No |
| K3 | All model IDs in the snapshot being checked | No |
| K4 | Record featureId and complete local feature-ID/type inventory from carrier bytes | Yes |
| K5 | File genome-link forms and each record reference | No |
| K6 | Current record/header plus explicitly supplied predecessor snapshots, their records, references and recorded successor relations | Not for pointer equality alone; validating supplied snapshots also exercises K4 |
| B1 | Selected released base and independently recomputed exact-byte checksum | Exact carrier bytes, without needing a feature-ID index |

For example, a K6-labelled valid vector cannot earn a full model pass merely by
checking pointer equality if its current or predecessor snapshot was never
validated. A K3-only rejection may establish a duplicate-ID predicate without
establishing a complete snapshot verdict. The reporting must say which claim
was checked. This distinction addresses both broad abstention and unjustified
full passes without requiring every library to call an external executable.

## Decisions requested

1. Adopt or revise the separately earned layer statuses and per-rule input table.
   Decide whether partial rule evidence is an accepted reported subset or every
   model-layer comparison requires the complete checker preconditions.
2. Confirm K4 target semantics for percent decoding, empty/absent inventories,
   multiple ID-bearing rows, transcript targets, mixed-type duplicates and
   `SO:0000704`. The existing text says one gene row; code alone must not settle
   interpretation disputes. Preserve the current fixtures pending that decision.
3. Confirm the K6 requirement for validation of supplied snapshots, including
   transitive K4 inputs; do not treat the vector's focus labels as dependencies.
4. Decide the representation of actual not-run/refused outcomes independently of
   expected `layers` values. Do not add an ad hoc boolean that covers K4 alone.

## Expectation review and subsequent implementation

The [promotion derivations](PROMOTION-2026-11-15.md) require a second reader.
This proposal does not sign off those expectations or remove their disclaimers.
For each promoted vector, the reviewer must record a contract clause, expected
predicate and layer, independent derivation, and disposition. Executor agreement
corroborates the derivation; it cannot supply it. Observed-only candidates must
be removed from normative acceptance or retained only with an explicit decision.

After that review and the decisions above, one owning-suite PR can implement
manifest requirements, runner reporting and a review-status guard. Exercise the
guard with all three known unfinished-review markers (`requires independent
review`, `OBSERVED outputs`, `candidate-unreviewed`) and a reviewed control;
do not merely delete the words to make the guard pass.

The accepted suite must merge before dependent consumer changes. Then update
JavaScript/Java correctness and R/Julia capability scopes against that exact
suite, using one owner per repository. Refresh pins in one dated pass after the
suite settles. A pin refresh is not included here. Joint publication remains a
separate maintainer action, with V7 unchanged.
