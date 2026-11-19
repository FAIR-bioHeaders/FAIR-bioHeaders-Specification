# Existing K2 text constraints: coverage derivation

This Round 14 packet addresses the unblocked coverage portion of
[FHGM #32](https://github.com/FAIR-bioHeaders/FHGM-Specification/issues/32).
It adds synthetic cases for existing clauses, not a contract change. The native
record contract, transport overlay, checker, base registry, earlier vector bytes
and earlier expected outcomes remain unchanged. FHGM remains an unreleased
draft under V7; no consumer is repinned by this packet.

## Expectations derived before execution

The authority is the unchanged
[`fhgm-model.schema.json`](../model/fhgm-model.schema.json):
`modelId` refers to `$defs/text`; the record's required list contains `modelId`.
K2 validates that record shape before K3 compares identities.

| New case suffix after `record-model-id-` | Clause and expected result |
| --- | --- |
| `trailing-nbsp` (U+00A0), `trailing-narrow-nbsp` (U+202F) | Trailing Unicode whitespace violates `$defs/text/not/pattern`; K2 rejects. |
| `leading-line-separator` (U+2028), `leading-paragraph-separator` (U+2029), `leading-ogham-space` (U+1680) | Leading Unicode whitespace violates `$defs/text/pattern` (`^\S`); K2 rejects. |
| `trailing-en-quad` (U+2000), `trailing-hair-space` (U+200A), `trailing-medium-mathematical-space` (U+205F), `trailing-ideographic-space` (U+3000) | The Unicode whitespace classes named in #32 violate the trailing constraint; K2 rejects. U+2000/U+200A exercise both ends of the named range. |
| `zero-width-space` (U+200B), `right-to-left-mark` (U+200F) | Interior code points at both ends of the explicitly forbidden U+200B–U+200F range; K2 rejects. |
| `left-to-right-embedding` (U+202A), `right-to-left-override` (U+202E) | Interior code points at both ends of the forbidden bidi range; K2 rejects. |
| `word-joiner` (U+2060), `invisible-plus` (U+2064), `byte-order-mark` (U+FEFF) | Explicit forbidden interior characters; K2 rejects. |
| `absent` and `two-records-model-id-absent` | Required `modelId` is missing. K2 rejects with the required-property diagnostic before K3; two missing values must not become an ambiguous empty-string identifier. |
| `interior-nbsp` | Positive control: U+00A0 inside opaque text is not edge whitespace and is not in the forbidden interior ranges. K2 accepts; the ordinary synthetic root-gene target and assembly binding satisfy K4/K5. |

These are 19 new vectors: 18 invalid and one valid. Expected outcomes were
specified from these clauses before the runner was invoked. The runner then
checks the stated expectation and only seals byte sizes, SHA-256 digests and
checksums after the layers agree. Executor agreement corroborates the derivation;
it is not independent expectation review or curator acceptance.

The cases use the same synthetic metadata and feature payload as the earlier
vectors. Each changed header is rendered with a freshly calculated SHA-512/256
checksum. No biological provenance is inferred. The 1.2 matrix derives twins
using the established identity-rewrite procedure; no old vector is rewritten.

## Coverage boundary and pending decisions

The edge-space cases are in the common Python/ECMA-262 whitespace set. They do
not claim that those engines agree on every `\s` member; no blanket Unicode
category or RE2 portability claim follows. A change from `\s` to an explicit
class is still the separate mechanism question in #32.

No outcome is added for `Parent=` or bare `Parent`. Their expected model-layer
result belongs to #22/#27's target/reporting decision, so the present checker is
not used to settle it. Target types, multi-row features, layer prerequisites,
partial/not-run/refused reporting and #28's identity policies likewise remain
unselected. Existing real-data promotion disclaimers are preserved.

Issue #32 remains open for those decisions and its remaining acceptance. The owning
suite's manifest and matrix digests change; contract and checker digests do not.
Consumers should not refresh during this coverage-only packet merely because
draft main moves; use the coordinated refresh after the owning suite settles.

## Validation and independent technical corroboration

- Python 3.15.0, fair-bioheaders 0.11.0, jsonschema 4.26.0: all 162
  sealed/matrix vector checks matched across base, checksum, GFF3 and model
  layers; both lanes have 60/63 gap-proof rejections and no twin verdict change.
- Node 24.22.1 RegExp and Python's schema validator agree on the 16 new text
  rejection values and the interior-NBSP positive. An ASCII-only whitespace
  mutation flips nine new negatives; removal of the invisible-range rejection
  flips seven; removal of required modelId admits the missing-property record.
- The rule-specific coverage test fails on the previous 62-vector manifest;
  an additional test reads the actual sealed JSON values so an ASCII-only
  fixture cannot masquerade as non-ASCII coverage through its name.
- A separate parent reviewer extracted the literal values from the generator
  without importing it or the checker, ran Node RegExp against the unchanged
  text definition and independently confirmed the same 16 rejections and one
  positive, plus the required-modelId clause. This is technical corroboration
  by a separate reader; it is not different-model PR approval or curator
  acceptance, and it does not review the older real-data promotions.

## Ongoing coverage rule

Whenever a contract rule names Unicode whitespace or a non-ASCII character
category, conformance must include a rule-attributed case outside ASCII and
a permitted control. An ASCII-only passing case cannot establish that category.
The tests inspect actual scalar code points as well as manifest attribution.
