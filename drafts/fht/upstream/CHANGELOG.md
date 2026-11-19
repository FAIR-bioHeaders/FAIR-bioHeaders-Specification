# Development changelog

## Unreleased — reference integrity fixes, 2026-11-19

- Verify optional RFC 1952 member header CRCs, with valid/corrupt/truncated
  controls and independent zlib agreement.
- Compare browser integer values without Number rounding, including exact
  values beyond 2**53 and both adjacent mismatch controls in Chromium.
- Preserve all 93 vector bytes/outcomes and the current draft contract.

## Unreleased — adopted FHT draft decisions, 2026-11-19

- Retain optional software/array/string/object behaviour (D1, #56).
- Tighten the owning draft rejection boundary: duplicate parent entries,
  noncanonical parent checksums and complete BUSCO count sums (D2, #57).
  Preserve existing requiredness; missing counts are not zero. Defer self-parent
  policy because a byte-valid self-reference requires a checksum fixed point.
- Accept four reviewed parent expectations for file identity only (D3), recording
  human disposition and independent technical review. Preserve all old vector
  bytes, IDs and outcomes. Add seven boundary regression vectors.
- Keep consumer repins, publication and release identifiers separate. The older
  installed runtime explicitly cannot enforce the two new arithmetic vectors.

## Unreleased

- Existing-constraint coverage (#8; Java #16 handoff): add ASCII and internal-ZWJ
  DOI positive controls and trailing-NBSP/narrow-NBSP C1 rejections under the
  unchanged scholarlyArticle pattern. All previous fixture bytes, outcomes and
  candidate markers remain unchanged; no schema or consumer pin moves. Refresh
  the readiness table to distinguish the merged typed-HTML reference/browser
  lane from unshipped runtime support, and record #56/#57's actual remaining
  decisions without reopening settled taxon/sample/author choices.

- Documentation and CI: state exactly which empty values `fht.json` rejects and
  which it still accepts, and label each statement as a current FHT draft
  requirement, shared family guidance (FORMAT.md / SCHEMA-VERSIONS.md v0.6.0,
  written for released FHR, FHP and FHGFF3) or a #56 proposal; parent-link and
  completeness checks are in #57; C1 now lists `mixed`. Fix the stale shared pin in
  `CITATION.cff` (v0.6.0, `0ae18b00`) and dated 72-vector counts. Lock
  `requirements-linkml.txt` exactly and run the Chromium browser check in CI.
  AGENTS.md: port the shared real-data-cases wording (specification `e11a9bf`)
  and the FHP absolute-links sentence (`659115c`), and move the FHT-only update
  into a local section.

- Typed-HTML reference (#11): read only values a viewer can see. Reject hidden
  or `display: none` properties and scopes, concealed descendants that add text
  to a scalar value, unrendered elements, `meta[content]` and other
  attribute-only values, `data`/`meter`/`time` values that differ from
  their text, `href` schemes outside R14, `itemref` and multi-token `itemprop`.
  Concealed attribute-valued array items and containers are checked too. CSS
  comments are token separators for inline visibility checks; escaped or quoted
  inline style syntax is conservatively refused. This reference does not compute
  arbitrary stylesheet cascades or layout.
  Eleven visible-value negative fixtures; all 20 invalid fixtures declare their
  expected rejection. The reader probes `<title>`/`<textarea>` RCDATA behavior,
  accepting capable backports without a version-number floor. The writer and
  the seven example pages are unchanged.

- Draft contract (rejection boundary of the unreleased draft): `schema` accepts
  only this repository's raw-main URL, because rule V7 gives a draft no release
  form; release forms are added at publication (#10). FHT-local patterns now
  give the same answer in Python and ECMA-262 regex dialects (no trailing-LF
  `$`, an explicit non-blank class instead of `\S`). New vectors: one C2, three
  C1 and one V5 rejection; existing vector bytes and outcomes are unchanged.
  `fht.json` is documented as normative over `linkml-validate`. The typed-HTML
  binding resolves its owning commit from git history and verifies the stored
  bytes, instead of comparing a hard-coded commit. The installed-draft CI job
  also runs the toolkit against this checkout's `fht.json` and fails on
  findings. Rebased over #52: the `AssemblyAuthor` name uses the
  same portable non-blank class, and the binding digest is re-pinned to the
  regenerated `fht.json`.

- Fixture runner: assert per invalid vector the rule that rejects it (rule ids
  raised by the byte/text reader, exact `fht.json` errors per contract vector,
  `checked-fail` recomputed for C3, and the V5 outcome computed against a pinned
  copy of released `fhr.json` v0.6.0). Read plain date scalars as strings
  (FORMAT.md R12) instead of rejecting them; replace the copied gzip helper with
  an independent RFC 1952 reader that requires complete members and rejects
  trailing padding; report malformed manifest entries (a directory as parent, a
  missing `statedChecksum`) instead of crashing. New vectors
  `fht-fasta-yaml-plain-date` (valid) and `fht-fasta-gzip-truncated` (invalid);
  existing vector bytes and outcomes are unchanged. Refs #8.

- Proposed Q4 follow-up after #50: supplied `assemblyAuthor` items need a
  nonblank `name` (local `AssemblyAuthor`, same rule as `MetadataAuthor`); the
  list stays optional and the shared `Author`, taxon and sample rules are
  unchanged. Rejection-boundary change to the unreleased draft; the 75
  conformance vectors and canonical examples are unchanged. The test-only HTML
  binding is re-anchored to the new schema bytes.

- Narrow #50 to the approved Q4 nonempty metadata values and Q8 extraction
  documentation after #51. Require nonblank transcriptome/version/date and
  nonempty, named metadata authors, without tightening optional assembly authors,
  taxon members or the retained sample array. Withdraw libraryProtocol in favor
  of documentation/relatedLink. This changes unreleased draft rejection boundaries;
  existing 75 conformance vector bytes/outcomes and all external consumer pins
  remain unchanged. Shared publication and first-release adoption remain separate.

- Record Molik's Q1–Q9 draft decisions; add `mixed` as the fifth molecule type,
  keeping the three construction types, sample array and current taxon rules.
  Owning source commit: `fcce5f6173322b337d24c7eea51ff8745d7b32aa`.
- Propose typed FHT HTML with seven readable canonical pairs and a test-only
  writer/extractor validated against the owning draft. Record protocol/kit
  context through existing documentation and relatedLink fields.
- Keep shared publication, runtime support and the separate real-data pilot
  handoffs explicit. These changes publish no contract or package.
