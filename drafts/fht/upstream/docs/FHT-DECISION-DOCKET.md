# FHT decision docket

## D1–D3 accepted — November 19, 2026

David Molik answered “Use the recommendations”; the
[adopted decision record](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7017854934)
supersedes the pending choices below.

- **D1 / #56:** retain existing software name/version and optional array,
  string and object behaviour. Supplied assemblyAuthor names, taxon and sample
  decisions remain settled. Empty optional values are regression-tested.
- **D2 / #57:** reject identical duplicate derivedFrom entries and noncanonical
  padded-base64 parent checksums. When all four integer BUSCO category counts
  and total are supplied, their sum must equal total. Missing counts are never
  zero; existing schema requiredness is unchanged. Cross-field arithmetic is a
  C1 semantic check outside JSON Schema, enforced by the owning checker and HTML
  reference reader/writer. The new self-parent C3 rule is deferred for the
  cryptographic fixed-point limitation described below.
- **D3:** accept the four reviewed parent expectations for exact file identity
  only: subset-citing-whole and masked-exact pass; wrong-file and case-folded
  fail. The manifest records human acceptance and prior independent technical
  review. Promotion markers are removed without changing old fixture bytes,
  IDs or outcomes. No biological extraction claim follows.

The final prepublication matrix is [FHT-READINESS.md](FHT-READINESS.md).
Joint final review (#8), publication/docs (#10), binding handoff (#11), and
runtime coordination (#9) remain distinct gates under #5. Shared/default-path
checks and arithmetic-capable consumer verification are publication work;
prepublication reference acceptance does not require an already published FHT.

## Historical decision agenda (now dispositioned above)

This is a small publication/review agenda, not a request to repeat settled
field decisions. [David Molik's Q1–Q9 answers](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8#issuecomment-6928571815)
supersede the earlier unanswered-questionnaire status. Keep all three
construction values, add the separately owned fifth molecule value `mixed`,
retain the strand convention and nine required roots/current taxon rules, keep
the sample array, align accession links with FHR, and retain existing names.
Protocol/kit information uses existing `documentation`/`relatedLink` fields.
No further external answers are a new prerequisite to this authorized draft
implementation. Joint review and publication keep their existing gates; the
model generation pipeline and agreed review path are not reopened.

| Existing owner | Decision still requiring a record | Evidence already available |
| --- | --- | --- |
| #8, candidate disposition | Record acceptance or retained candidate state for the four independently reviewed parent expectations; do not equate execution with curator acceptance | [Readiness technical review](FHT-READINESS.md#independent-technical-review--2026-11-16), existing manifest candidate markers and rule derivations |
| #8 / shared publication | Disposition shared/default-path acceptance as publication-time follow-through, with honest prepublication evidence; no default runtime claim before actual publication | [Readiness accounting](FHT-READINESS.md#acceptance-accounting), merged [#49](https://github.com/FAIR-bioHeaders/FHT-Specification/pull/49), [#10 merge verification](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/10#issuecomment-6924427026) |
| #8, concrete real-example review if promoted | Approve the annotation-derived pilot's resource creation date and actual extraction-software attribution before treating those assertions as release examples | Existing [#45](https://github.com/FAIR-bioHeaders/FHT-Specification/pull/45), [pilot handoff](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/10#issuecomment-6897167617); the model already defines resource creation and permits extraction software |
| #11 / shared publication | Review this explicit draft binding and coordinate its eventual shared publication and runtime/website handoffs | [Binding proposal](FHT-MICRODATA.md), paired HTML examples and reference tests; no new schema fields |

## Constraint decisions raised after the questionnaire

These are specific proposals against the unreleased draft, not unanswered
questionnaire items or automatic requirements for the first publication.

| Owner | Exact remaining choice | Settled boundary |
| --- | --- | --- |
| [#56](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/56) | Keep or tighten the supplied software name/version, optional relatedLink/identifier/commandLineOption arrays, optional strings and optional objects | Supplied assemblyAuthor entries already require a nonblank name through merged #52; the field remains optional. Keep the recorded taxon/sample choices unless David explicitly revises them. Empty CLI argument strings may be real tokens; array cardinality and item content are separate choices. |
| [#57](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/57) | Disposition duplicate parent entries, a parent checksum equal to the record's own checksum, canonical parent-checksum encoding and BUSCO count arithmetic | Existing schema/reader behaviour is not adoption. A count rule must state which optional counts are required to compare and whether it means equality or only an upper bound; missing counts must not silently become zero. A shared-family amendment is separate from an FHT-local draft change. |

After the decisions, one owning PR can implement the selected constraints and
their clause-derived C1/C3 rejection vectors. An explicit decision to retain or
defer a proposal is a valid disposition; absence of an answer is not. Changes
to shared released contracts, curator acceptance and publication are separate.

The self-parent proposal needs special treatment: a nested parent checksum is
itself covered by the child's checksum. Making a byte-valid file name its own
recomputed checksum would require a cryptographic fixed point; copying the
stated root checksum into a parent entry instead breaks the child's checksum.
That mutation can demonstrate bad file integrity, but cannot independently
prove a C3 self-parent rule. Any metadata-level equality rule must identify
that narrower claim rather than promise a byte-valid same-file fixture.

## Keep the split pilot separate

[November 14 decision 1D](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-6880245660)
split #10 release/docs/citations from the real-data pilot. Whether a bounded chr4
subset or complete producer set satisfies a future public pilot, where real
examples live and which supplied reuse wording applies remain pilot work. They
must not become a new complete-producer-set gate on #10 release preparation.
Existing contract/example semantics and curator acceptance under #8 still matter;
no pilot header or checksum is changed by this binding packet.

The release vehicle is already chosen: shared `v0.7.0`, through the established
maintainer publication process. INSDC assessment #157 is complete; #6/#7's initial
design/model decisions and the review path are not repeated. Additional parent
relationships under shared #54 are a separate proposal, not a binding blocker or
authority to add a field. Release tags, registry rows, aliases, DOI records,
package publication and deployments require their existing maintainer actions.

## Keep examples and measurements distinct

The supplied questionnaire's three compact LF snippets have valid checksums,
but their large illustrative statistics are not measurements of the displayed
one-record bodies. None is imported unchanged into this binding's acceptance
fixtures. The HTML pairs reuse only the repository's existing, explicitly
synthetic canonical JSON/YAML records, with their input bytes unchanged. HTML
round trips preserve assertions; they do not verify file statistics, BUSCO runs
or biological derivation. The current owning draft accepts dotted BUSCO lineage
versions; an older installed writer pin is a separate consumer limitation and
is not changed here.
