# FHT conformance vectors (development contract — issue #8)

Adopted November 19, 2026: [D1–D3](../docs/FHT-DECISION-DOCKET.md)
retain optional field behaviour, reject duplicate parent entries and noncanonical
parent checksum encoding, and require complete BUSCO category counts to sum to
total. Arithmetic is a separate C1 semantic check, not expressible by this JSON
Schema contract. Missing counts are not zero. The reference reader/writer checks
arithmetic; older installed consumers remain a publication handoff. Four parent
expectations are accepted for file identity only, without changing fixture bytes.

Byte-exact positive and rejection fixtures for the FHT 1.0 **development**
contract, the generated [`fht.json`](../fht.json) of this repository
([revised spec 005](../specs/005-rna-transcriptome-header/spec.md), PR #21).
They apply the shared specification's header and checksum rules
([docs/FORMAT.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FORMAT.md)
R1-R15 on FASTA `;~` headers) and the family schema-selection rules
([docs/SCHEMA-VERSIONS.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/SCHEMA-VERSIONS.md)
V1/V5, as limited by the V7 draft-lane note) to transcriptome files, in RNA
(U) and cDNA (T) form. The layout and
the manifest fields mirror the shared suite's `fhp-fasta` vectors so the
shared `conformance/manifest.json` can absorb these vectors unchanged when
FHT is published.

**Status: development, not publication.** Draft D1–D3 decisions are adopted; no FHT contract is released
or published; FHT has no released contract (issue #10), no toolkit support
(issue #9) and no shared-manifest entry yet (issue #55 /
FAIR-bioHeaders-Specification#107, the #55 chain's "lane F").

## Layout

- `valid/`: files a conforming implementation must accept.
- `invalid/`: files it must reject.
- `parents/`: three synthetic FHR-headed genome files, each a byte target for the
  C3 link vectors (none is itself an FHR conformance vector):
  `parent-genome.fhr.fasta` holds both scaffolds, `parent-genome-subset.fhr.fasta`
  holds a proper subset of them, and `parent-genome-masked.fhr.fasta` holds both
  with one sequence line written in lower case and `masking: soft-masked`. The
  three exist so the subset and case hazards can be *compared against real bytes*
  rather than described: each has its own computed digest, and the digests are
  asserted pairwise different by the generator.
- `manifest.json`: the expected outcome for every file. Field names and
  semantics follow the shared manifest (`id`, `file`, `format`, `compressed`,
  `expected`, `rules`, `description`, `checksum`, `metadata`, `rule`,
  `reason`, `result`, `retired`), the proposed format id is `fht-fasta`, and
  three manifest fields here have no shared-manifest precedent:
  `selfChecksum` and `parentLink` are **finalized** for release (maintainer
  decision 2026-11-14, issue #37; semantics below), while the top-level
  `status` label remains provisional pending shared absorption. `promotion`
  (per vector) and `promotionCandidates` (top level) are **review
  bookkeeping**, not release vocabulary: they mark pilot-derived vectors whose
  expectations no second reader has confirmed yet, and both disappear when the
  review lands.
- `*.gz`: gzip or BGZF copies; validate their decompressed bytes.

Every file is byte-exact. The repository `.gitattributes` turns off
line-ending conversion for `conformance/**` and `examples/**`, so CR, CRLF
and checksummed bytes survive every checkout. Do not open and re-save these
files in an editor; run the generator instead.

## Rule registry

R1-R15 and V1/V5 carry the summaries of the shared documents (see
`rules` in `manifest.json`; the documents are authoritative). FHT's own
rules are **C1-C3** — the letter scheme of the shared suite (one uppercase
letter plus number), with `C` for the development **contract** rules; `C` is
unassigned in every federation conformance namespace (the shared manifest
registers R, V, M, G, J and P). They replaced the provisional `T1-T3`
before external citation (issue #36; the old labels were additionally
ambiguous with the RNA-U/cDNA-T notation this suite uses throughout). Their
rule text, derived from the merged contract, is:

- **[C1] Contract validation.** The metadata parsed from a `;~` header must
  validate against `fht.json` (draft 2020-12, asserted `format`s): the nine
  required fields (`schema`, `schemaVersion` `"1.0"`, `transcriptome`,
  `assemblyType`, `taxon`, `version`, `metadataAuthor`, `dateCreated`,
  `checksum`) present, with non-blank `transcriptome`, `version` and
  `dateCreated`, at least one named metadata author and a name on every
  supplied assembly author; enums (`de novo`,
  `genome-guided`, `annotation-derived`; `mRNA`, `rRNA`, `tRNA`,
  `transcribed RNA`, `mixed`; `unstranded`, `forward`, `reverse`); patterns
  (checksums, run accessions, taxon URI, DOI); nested cardinality (`sample`
  items need one value; the FHT arrays `transcriptomeSynonym`,
  `assemblyAuthor`, `assemblySoftware`, `sample`, `sequencingRuns`,
  `instrument` and `derivedFrom` need one item when present); the closed top
  level plus the `x-` extension pattern; and only the two permitted parent
  pairs (FR-007). The schema does not reject every empty value: `taxon: {}`,
  an unnamed software item, `relatedLink: []` and empty
  optional strings still validate (see
  [`../specs/fht-record-designs.md`](../specs/fht-record-designs.md) and
  [#56](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/56)).
- **[C2] Schema-URL closure.** A record's `schema` value must be this
  repository's raw `main` URL,
  `https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json`,
  exactly (a JSON Schema `const`). That is the one citation shared rule V7
  admits for a draft, and a draft never takes a release form, so release-tag
  and w3id URLs are rejected as well; a reader routes them to FHR under V5.
  The released forms (the shared V2 raw-tag URL and the V3 w3id URL) are added
  when FHT is published. Unlike released FHR (selection rule V5 leaves its
  `schema` open), an arbitrary URL or another type's schema URL fails the
  contract; it never silently selects the FHT schema.
- **[C3] Parent-link verification.** A `derivedFrom` item's `checksum` is
  the parent file's FHR-family checksum under R1-R5. A reader that has the
  parent file must recompute it and compare as exact strings: equal is
  **checked-pass**, different is **checked-fail** and must be reported as
  an invalid link (not skipped). Without the parent file the link is
  **unchecked**: the record stays valid, and no implementation may call
  such a link verified. An `accessionID` on the link is additional, never
  a substitute for the checksum (FR-007).

Checked / unchecked / invalid, concretely:
`fht-fasta-parent-transcribed-from` and `fht-fasta-parent-filtered-from`
cite checksums that recompute from files in this directory (checked-pass);
`fht-fasta-parent-unavailable` cites the canonical placeholder
`AAAA…AAA=` with no parent file (unchecked, still valid);
`fht-fasta-parent-mismatched` is byte-valid, schema-valid and
checksum-consistent but cites a perturbed parent checksum (invalid link,
checked-fail); `fht-fasta-parent-mixed-verdicts` pairs a checked-pass and a
checked-fail link in one record, proving the verdict is per entry.
`fht-fasta-parent-real-digest-wrong-file` and
`fht-fasta-parent-case-folded-digest` are checked-fail with a **genuine** digest
— the value is the true checksum of a different real file in `parents/`, so
nothing is malformed and only the exact-string comparison can catch it;
`fht-fasta-parent-subset-citing-whole` and `fht-fasta-parent-masked-exact` are
their checked-pass siblings. Those four are promotion candidates from the
real-data pilot: see "Promotion candidates from the pilot" below.

### Finalized field semantics (issue #37)

`selfChecksum` names, per vector, the state of the file's own root checksum
line under the R1-R5 recomputation, and is recorded on **every** vector
in [`manifest.json`](manifest.json):

- `matches` — the stated value equals the recomputed value over the covered
  bytes. The positive class: all valid vectors carry it, and so do the
  invalid vectors whose single defect lies elsewhere (the anti-accident rule:
  an implementation must not pass a vector by failing the comparison by
  accident).
- `broken` — the root checksum line parses but recomputes differently
  (negative fixture, 7 vectors).
- `unreachable` — the root checksum line cannot be located or compared at all
  (negative fixture, 10 vectors; the R2/R5 line-shape families, the
  non-canonical R4 value and the truncated gzip stream, which has no
  decompressed bytes to hash).

`parentLink` is an array of per-link entries
`{file, statedChecksum, result}` recorded exactly on the vectors that
exercise C3 (10):

- `result` is one of `checked-pass` / `checked-fail` / `unchecked`.
- `unchecked` ⇔ `file: null`: the parent bytes were not supplied; the link is
  neither verified nor a rejection reason.
- `checked-pass` / `checked-fail` require a named parent file inside this
  directory; `statedChecksum` is compared to its recomputed checksum as an
  exact string. The runner enforces this containment by resolution: a
  parentLink path that escapes `conformance/` (via `../` segments or an
  absolute location) is rejected without being read.
- The verdict is **per entry**: one record may carry both outcomes and the
  checked-fail entry drives rejection
  (`fht-fasta-parent-mixed-verdicts`).

These two fields are finalized for release with the positive and negative
fixtures above; shared absorption may rename them onto whatever the shared
manifest schema uses but must not change this verdict model (issue #9
adopts these failure classes as its toolkit acceptance list). The top-level
`status` label is the only field still provisional pending absorption.

## Provenance — every byte is generated

[`../scripts/make_fht_fixtures.py`](../scripts/make_fht_fixtures.py) (stdlib
only) writes `valid/`, `invalid/`, `parents/`, `manifest.json` and the
generated files in [`../examples/`](../examples/). It is deterministic with
no seed: no clock, locale, random source or filesystem order; gzip/BGZF
vectors use stored deflate blocks with mtime 0 and no name, so reruns
reproduce identical bytes on any zlib build.

Checksums are **cross-checked by a second, independent implementation**: the
generator embeds values computed at build time, and
[`../scripts/check_fht_fixtures.py`](../scripts/check_fht_fixtures.py)
re-derives every expectation from the rule text with its own R1 line
splitting (LF/CRLF/lone CR), its own R2 root-indent detection, its own R5
value grammar and its own SHA-512/256 recomputation (adapted from the
stdlib reference in FAIR-bioHeaders-Specification
`scripts/tool_survey/round6/make_fixtures.py`, not copied from the
generator's same-file helper). CI (`.github/workflows/fht-fixtures.yml`,
also wired into `tests/test_fixtures.py`) runs three proofs:

1. regeneration inside the process, twice, compared with the committed
   bytes (`diff`-level identity, per file);
2. the same regeneration into a scratch directory outside the tree;
3. every vector re-read and re-classified by the independent runner
   (valid: recomputed checksum equals the manifest and the record passes
   `fht.json` with `FormatChecker`; invalid: rejected **for the rule its
   entry declares**, with the `selfChecksum` anti-accident rule —
   non-checksum defects carry consistent checksums so an implementation
   cannot pass by failing the comparison by accident). The runner reads the
   bytes in rule order (R7, R10, R2/R5/R4, R6/R8/R12/R13, then the R3
   comparison) and every error it raises names its rule, so a byte-rule
   vector passes only when the declared rule is the one that rejects it. A
   contract vector (C1, C2, V1, R15) passes only when its `fht.json` errors
   equal the per-vector expectation recorded in the runner
   (`EXPECTED_SCHEMA_ERRORS`: keyword, JSON path and offending value, with
   no missing and no extra error). The two V5 vectors are routed to the
   reader's current FHR schema and validated there: the pinned copy of
   released `fhr.json` in [`../schemas/fhr-v0.6.0.json`](../schemas/fhr-v0.6.0.json)
   must raise exactly the five errors listed under "What these vectors do
   **not** yet prove" below.
   A C3 vector passes only when its parent link is actually recomputed as
   `checked-fail`. Compressed vectors are read by the runner's own RFC 1952
   reader, which requires every member to be complete (deflate end of
   stream plus a matching CRC-32/ISIZE trailer) and rejects bytes after the
   last member, including NUL padding.

### Synthetic content policy

No metadata, parent checksum or identifier is invented to look real. Every
name carries a `Synthetic`/`(placeholder)` label; URLs live in example.org
or on this repository's own schema paths; the DOI uses the reserved
`10.5555` prefix; run accessions use `SRR/ERR/DRR 999xxxx`; the parent
placeholder checksum is the canonical-set `"A"*43 + "="`. The taxon is the
real *Homo sapiens* NCBI Taxonomy 9606, reused from the shared suite's
vectors, and the sequences are short synthetic nucleotide strings — no real
transcript is reproduced. All `vitalStats` of `fht-fasta-rich` are genuinely
computed from that vector's own sequence bytes. The parent fixture in
`parents/` is a fabricated FHR file with its own **real computed** checksum,
cited at its recomputed value by the checked-pass vectors.

## Vector census

`manifest.json` is authoritative; this is the map, not the list.

| Group | Vectors |
| --- | --- |
| Byte coverage (R1-R4) | RNA `lf`/`crlf`/`cr`/`mixed-endings`/`no-final-newline`, cDNA `T` variant, `gzip` (one member), `bgzf` (multi-block), `gzip-multimember` (two members split inside the checksum line); rejections: a gzip stream truncated inside its trailer (`gzip-truncated`, R1: no decompressed bytes exist), CRLF-normalized, U→T-normalized and case-normalized checksums (R1), sequence tamper and its compressed copy `gzip-sequence-tampered` (R3), SHA-256, truncated SHA-512 and non-canonical base64 (R4) |
| Checksum line shape (R2/R5) | root-indented, space-before-colon, quoted value, checksum-first, trailing spaces, nested (derivedFrom) parent checksum; rejections: missing, doubled, nested-only (R2), block literal, continuation, trailing comment (R5) |
| Header text (R6-R8, R10, R12/R13) | ordinary comments/blank lines incl. `;~#` and a post-record `;` comment, raw UTF-8 value, plain (unquoted) `dateCreated` read as the string written (`yaml-plain-date`, R12); rejections: U+2028 (R6), BOM (R7), duplicate key and anchor/alias (R8), `;~` after record and concatenation (R10), `011` (R12), `.inf` (R13) |
| Writer recommendations | escaped `\x3E`/`\x40` (R11), `javascript:` relatedLink kept valid with `warnings: ["R14"]` |
| Extensions (R15) | valid `x-` values of every JSON type and in the rich record; rejections: nested `x-` key, `X-Wrongcase` key |
| Contract (C1) | minimal (nine required fields only), rich (every optional field), all three `assemblyType` values in `examples/`; rejections: missing/unknown `assemblyType`, `cDNA` molecule type, empty `sample`, FHR `genome` key, legacy `masking` key, `SRS` run accession, the three parent-shape defects, and three values that only one regex dialect used to reject (a run accession ending in a line feed, a lone U+FEFF `transcriptome`, a lone U+001C `version`) |
| Selection (C2, V1, V5) | valid raw-main citation (`fht-fasta-schema-raw-main`, the only resolvable FHT URL today); rejections: FHR schema URL, arbitrary URL and the raw-main URL followed by a line feed (C2), future major `2.0` and unquoted number via raw-main (V1), `w3id .../fht/v0.5.0`, this repository's raw tag `v9.9.9` and the shared repository's V2 raw tag `…/FAIR-bioHeaders-Specification/v0.6.0/fht.json` (V5, `result: invalid-as-fhr` — read as FHR, rejected by the current FHR schema; after FHT registration the w3id vector becomes V4, but the development-repository raw-tag URL remains V5 because it matches no V2 form) |
| Parent links (C3) | checked-pass ×5 (the two-link rich record, `-parent-transcribed-from`, `-parent-filtered-from`, and the two pilot candidates `-parent-subset-citing-whole` and `-parent-masked-exact`), unchecked ×1, checked-fail ×3 (`-parent-mismatched`, and the pilot candidates `-parent-real-digest-wrong-file` and `-parent-case-folded-digest`, whose stated value is a genuine digest of a *different* shipped file), mixed verdicts ×1 (checked-pass + checked-fail in one record; #37) |

Counts: 30 valid, 52 invalid, 3 parent fixtures; every vector carries a
finalized `selfChecksum` (35 matches-invalid + 30 matches-valid = 65, 7
broken, 10 unreachable) and the ten C3 link vectors carry `parentLink`
entries. Rule coverage self-check:
every registered rule except the recommendation/warning/outcome-only/lane
rules (R9, R11, R14, V5, V7 — each with a recorded `notApplicable` note in the
manifest) has both a valid and an invalid vector.

### Accountability for FORMAT.md R1-R15

Issue #8's third box asks for stable cases "for R1–R10"; the table is the
answer for the whole shared range, so a reviewer can check each rule instead of
counting vectors. 21 rules are registered: every lettered rule of FORMAT.md
(R1-R15), the three selection rules this suite names (V1, V5, V7) and this
contract's own C1-C3. `scripts/check_fht_fixtures.py` fails the lane if a
rule R1-R15 is absent from the registry, or if a registered rule has neither
both sides nor a recorded reason.

| Rule | Valid vector | Invalid vector | Where |
| --- | --- | --- | --- |
| R1 exact bytes, decompressed | `fht-fasta-lf` (+ `crlf`, `cr`, `mixed-endings`, `no-final-newline`, `cdna`, `gzip`, `bgzf`, `gzip-multimember`) | `fht-fasta-crlf-normalized-checksum`, `-u-normalized-checksum`, `-case-normalized-checksum`, `-gzip-truncated` | FORMAT.md |
| R2 one root checksum line | `-root-indented`, `-space-before-colon`, `-quoted-value`, `-nested-checksum` | `-missing-checksum`, `-two-checksum-lines`, `-only-nested-checksum` | FORMAT.md |
| R3 exclude that line, hash the rest | `-checksum-first`, `-checksum-trailing-spaces`, `-comments-and-blank-lines` (the excluded line is located, not guessed) | `-sequence-tampered`, `-gzip-sequence-tampered` | FORMAT.md |
| R4 SHA-512/256 canonical base64 | `-lf` (44-char canonical value) | `-checksum-sha256`, `-checksum-truncated-sha512`, `-checksum-non-canonical` | FORMAT.md |
| R5 checksum line grammar | `-quoted-value`, `-checksum-trailing-spaces` | `-block-literal-checksum`, `-continued-checksum`, `-checksum-with-comment` | FORMAT.md |
| R6 UTF-8, no U+0085/2028/2029 | `-utf8-metadata` | `-u2028-in-header` | FORMAT.md |
| R7 no BOM | `-lf` | `-utf8-bom` | FORMAT.md |
| R8 no duplicate keys/anchors/aliases/merge | `-lf` | `-duplicate-key`, `-yaml-anchor-alias` | FORMAT.md |
| R9 microdata token lists | — | — | **not applicable to `fht-fasta`**: a microdata-only rule, and no FHT microdata reader or writer exists (box 2 keeps unimplemented serializations out of the suite; the typed-HTML lane is issue #11). Registered with this `notApplicable` note so the R1-R15 audit accounts for it. |
| R10 leading header block | `-comments-and-blank-lines` | `-header-after-record`, `-concatenated` | FORMAT.md |
| R11 escaped `>`/`@` (writer advice) | `-escaped-record-markers` | — (recommendation; `notApplicable`) | FORMAT.md |
| R12 YAML 1.1/1.2 agreement | `-lf` (all plain scalars agree), `-yaml-plain-date` (a plain date is the string written) | `-yaml-leading-zero` | FORMAT.md |
| R13 finite numbers | `-rich` | `-inf-vital-stats` | FORMAT.md |
| R14 link schemes (warn only) | `-link-scheme-warning` (`warnings: ["R14"]`) | — (never a rejection; `notApplicable`) | FORMAT.md |
| R15 `x-` extensions | `-extension-fields`, `-rich` | `-extension-nested-key`, `-extension-uppercase-key` | FORMAT.md (via FR-010) |
| V1 raw-main selects current | `-schema-raw-main` | `-version-2-0-via-raw-main`, `-schemaversion-number` | SCHEMA-VERSIONS.md |
| V5 unrecognized value is FHR | — (no FHT-valid record can be FHR-valid; `notApplicable`) | `-schema-w3id-release-without-fht`, `-schema-raw-tag-unknown`, `-schema-shared-raw-tag` (`result: invalid-as-fhr`) | SCHEMA-VERSIONS.md, as limited by V7 |
| V7 opt-in draft lane | — (governs whether any record here is read as the draft; no byte outcome of its own, `notApplicable`) | — (same reason) | SCHEMA-VERSIONS.md |
| C1 contract validation | `-minimal`, `-rich`, `-lf`, `-cdna`, `-extension-fields`, the three parent-link positives | the missing/unknown `assemblyType`, `cDNA` molecule type, empty `sample`, FHR `genome` key, legacy `masking` key and `SRS` run rejections | `fht.json`, this README |
| C2 schema-URL closure | `-schema-raw-main` | `-cites-fhr-schema`, `-cites-arbitrary-url`, `-schema-trailing-line-feed` | `fht.json` |
| C3 parent links | `-parent-transcribed-from`, `-parent-filtered-from`, `-parent-unavailable`, `-rich` | `-parent-mismatched`, `-parent-mixed-verdicts` | this README |

The "where" column distinguishes the shared-document rules from this
development contract's own C-rules; the manifest's `rules` entries carry the
same rule summaries, and `docs/FORMAT.md` and `docs/SCHEMA-VERSIONS.md` stay
authoritative for their text.

### The rule this suite cannot carry yet: V7 with the lane closed

Every vector here is read **through** the opt-in draft lane: the `expected`
values describe a reader that chose to read this repository's `fht.json`. Rule
V7 also decides what a reader does when it did *not* choose the lane — then the
owning-repository raw-main URL is "any other value" under V5, so each of these
records is read as FHR and rejected there. Measured with `fair-bioheaders`
0.11.0 in both configurations (see [`../docs/CI.md`](../docs/CI.md)): on the
then 82-vector suite (2026-11-18, Linux; a dated measurement, not the current
suite census), 0 of 82 vectors are accepted with
the lane off, and with it on all 30 valid vectors are accepted once the reader
holds this checkout's contract (29 with its own older bundled draft, which
lacks `mixed`). The first measurement, 2026-11-15 on the then 72-vector suite,
was 0 of 72 off and 28 on.

That is a second, configuration-dependent outcome for the *same bytes*, and this
manifest vocabulary cannot hold it: a vector has one `file`, one `expected` and
no field for the reader's lane. Two ids for the same bytes with different
`expected` values would be worse — the shared suite's rule is that ids are never
reused or rewritten, and a consumer that reads the whole manifest (the toolkit's
gated `tests/fht_conformance_test.py`, for instance) has no way to know which of
the two it is being asked to reproduce. So the lane-closed behavior is recorded
as a measurement, not as a vector, until either

1. the shared manifest grows a reader-configuration field (a vocabulary change
   for FAIR-bioHeaders-Specification, coordinated at absorption: this repo #55 /
   FAIR-bioHeaders-Specification#107), or
2. issue #9 gives the toolkit a default FHT reader, after which V5-with-the-lane-
   off stops being the FHT story at all.

Until one of those lands, `fht-fasta-schema-raw-main` asserts the lane-on result
only, and `notApplicable` on V7 says so in the manifest itself.

## Promotion candidates from the real-data pilot (#45)

The maintainer decision recorded on #8 is to promote selected pilot cases to
normative vectors. Four vectors here do that, and they are marked as
**candidates**, not as accepted vectors:

- per vector: `"promotion": "candidate-unreviewed"`;
- top level: `promotionCandidates`, carrying the source, the candidate ids and
  the review rule that governs them.

**What was promoted and what was not.** #45 built a real chr4 (`NC_004353.4`)
FHR parent and a 334-transcript FHT subset on top of it. Its *bytes* stay in
`pilot/`: they are third-party sequence, they are 1.4 MB each, and the synthetic
content policy exists so a published vector never depends on a download. What
transfers is the *shape* of what the pilot had to reason about, restated over
synthetic fixtures: a subset whose link cites the whole parent; a parent whose
letters exist in two case encodings with two digests; and a link whose stated
digest is genuine but belongs to a file the reader was not handed.

**The constraint that governs this section.** A vector's `expected` outcome must
not be produced by the implementation under test. Each candidate's expectation
below was written from rule text first — FR-007 in
[`../specs/005-rna-transcriptome-header/spec.md`](../specs/005-rna-transcriptome-header/spec.md)
and rules C3/R1 in this file and in
[`docs/FORMAT.md`](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FORMAT.md)
— and three executors then read the fixtures independently.

| Candidate | Expected, from the clause quoted | A — released `fair-bioheaders` 0.11.0 (PyPI, V7 lane ON) | B — `scripts/check_fht_fixtures.py` (this repository's independent reader) | C — `FAIR-bioHeaders-Tools-JavaScript` at `d8552f6` (`src/reader.js`, `src/parent-links.js`) |
| --- | --- | --- | --- | --- |
| `fht-fasta-parent-subset-citing-whole` | valid + `checked-pass`. C3: "equal is **checked-pass**"; FR-007 fixes the permitted pair and requires the parent's FHR-family checksum, and says nothing about coverage | `verify` exit 0 (`Checksum verified.`); `verify-links` exit 0 printing `matched (` | accepted; link recomputes equal | `valid: true`, verdict `checked-pass`, selection `V7/FHT` |
| `fht-fasta-parent-real-digest-wrong-file` | invalid + `checked-fail`. C3: "different is **checked-fail** and must be reported as an invalid link (not skipped)" | `verify` exit 0 (the file itself is valid), `verify-links` exit 3 printing `not matched (` | rejected in the parent-link class | `valid: false`, verdict `checked-fail`, the error names both digests |
| `fht-fasta-parent-masked-exact` | valid + `checked-pass`. R1: "Read the FASTA/GFA as bytes; do not normalize…", so the masked file's own digest is the only correct citation for it | `verify` exit 0; `verify-links` exit 0, `matched (` | accepted; link recomputes equal | `valid: true`, verdict `checked-pass` |
| `fht-fasta-parent-case-folded-digest` | invalid + `checked-fail`. R1 plus C3's exact-string comparison: the uppercase and masked copies of one set of letters are two files, so citing one against the other fails | `verify` exit 0, `verify-links` exit 3, `not matched (` | rejected in the parent-link class | `valid: false`, verdict `checked-fail` |

Reproducing the cross-check (nothing outside the repository is written; both
reads are read-only):

```sh
# A — the released reader, PyPI 0.11.0, in a throwaway venv
python3 -m venv /tmp/fht0110 && /tmp/fht0110/bin/pip install fair-bioheaders==0.11.0
BIOHEADERS_EXPERIMENTAL_FHT=1 /tmp/fht0110/bin/bioheaders verify \
  conformance/valid/fht-fasta-parent-subset-citing-whole.fht.fasta   # exit 0
BIOHEADERS_EXPERIMENTAL_FHT=1 /tmp/fht0110/bin/bioheaders verify-links \
  conformance/invalid/fht-fasta-parent-real-digest-wrong-file.fht.fasta \
  conformance/parents/parent-genome-subset.fhr.fasta                 # exit 3

# B — this repository's own reader
python scripts/check_fht_fixtures.py

# C — the JavaScript library, read-only export of its origin/main
git -C ../FAIR-bioHeaders-Tools-JavaScript archive origin/main | tar -x -C /tmp/fhtjs
ln -s "$PWD/../FAIR-bioHeaders-Tools-JavaScript/node_modules" /tmp/fhtjs/node_modules
# then call inspectBytes(bytes, {container: 'fasta', drafts: ['FHT'], parents})
# from /tmp/fhtjs/src/reader.js over the manifest's vectors
```

A and C were run against these bytes on 2026-11-15 and reported **no
disagreement with any of the 72 vectors the suite then had**, not only with the
four candidates. A was re-run on 2026-11-18 against the then 82 vectors, with
no disagreement ([`../docs/CI.md`](../docs/CI.md)); C was not re-run. A
through `bioheaders verify` / `verify-links`, C through `inspectBytes(bytes,
{container: 'fasta', drafts: ['FHT'], parents})` on a read-only `git archive`
export of that repository's `origin/main`. C's own `capability:draft` runner
refuses this suite by design, because its recorded `suiteManifestSha256` still
names the 66-vector revision — a stale pin, reported and not repaired here. C
reads the contract at `59ad9641…`, this checkout's `fht.json`; A reads its
bundled `11c69d66…` at `b9ad19a6…`, so A's agreement is with that pinned older
revision.

### Expectations require independent review — the reviewer must not be the author of the derivation

Agreement between implementations corroborates an expectation; it does not
substitute for review, and it cannot detect the case where every executor shares
one misreading of the rule text. **The four vectors above were derived by this
PR's author and need a second reader — all four, specifically:**

1. `fht-fasta-parent-subset-citing-whole` — is `valid` the only rule-compatible
   outcome, or does FR-007's "only for real reviewed family-file relationships"
   make a subset-citing-whole link a record defect rather than a scope statement
   the contract cannot see? A reviewer should also decide whether the vector
   should carry a warning field, which would make "file identity only"
   machine-checkable instead of descriptive.
2. `fht-fasta-parent-real-digest-wrong-file` — the outcome is C3's, but whether a
   reader must *name both digests* in its report is not settled by any rule text
   here; #45's `verify-links` output does, and no clause compels it.
3. `fht-fasta-parent-masked-exact` and `fht-fasta-parent-case-folded-digest` —
   both rest on reading R1's "do not normalize" as covering letter case. The rule
   text supports it by omission (case is not in the normalization list, and the
   bytes are the bytes), but that inference is the author's, and a curator should
   confirm it, because the pilot's real parent is exactly this shape (27.8 %
   lowercase, with NCBI's uppercase component file beside it).

All candidates include `dateCreated: 2026-11-10`; no checksum derivation interprets
that date. `assemblySoftware` and `reuseConditions` are absent. Their children are
synthetic RNA bodies, not demonstrated extractions from the synthetic ctgA parent.
The checks prove file identity and schema/checksum behavior only. The uppercase
and masked parent also differ in their genome title and masking metadata; this is
not an isolated sequence-case experiment. Independent technical review on
2026-11-16 confirmed all four exact-byte outcomes, without promoting their
`candidate-unreviewed` markers or granting curator acceptance.

**Accepting a candidate** is a one-line change: drop its id from
`PROMOTION_CANDIDATES` in `scripts/make_fht_fixtures.py` and regenerate. The
vector, its id and its bytes do not move — only the `promotion` marking and the
top-level list do, so review leaves a trace in history. **Rejecting** one follows
the shared retirement rule: retire the id, never rewrite its expectation.

### Measured, deliberately not promoted

- **The lane-off / V5 outcome.** #45 ran the same real FHT file twice: with the
  draft lane closed, the released reader routed it to the current FHR schema and
  rejected `schemaVersion '1.0'`; with the lane open, it verified. Rule V7's text
  gives that reading directly ("Without that choice, V5 governs such a value and
  the outcome is exactly what it was before V7 existed"), and both paths were
  re-measured on this suite on 2026-11-15: `bioheaders verify` with the lane
  closed accepts **0 of 72** vectors; with it open it accepts 32 — the 28 valid
  vectors plus the 4 whose only defect is a `checked-fail` link, which `verify`
  passes by design and `verify-links` rejects with exit 3. It is **not** a
  vector, because a vector carries one
  `file` and one `expected`, and this is one byte string with two outcomes,
  decided by the reader's configuration. Encoding it needs a manifest field for
  the reader's lane — shared vocabulary, so that belongs to #55 /
  FAIR-bioHeaders-Specification#107 and to #9, not to a draft PR inventing it
  here.
- **`assess`'s FHT findings** (`not assessed: unsupported-header-type`, and the
  `derivedFrom[].accessionID` sequence accession `NC_004353.4` flagged against an
  assembly-accession pattern) are toolkit behavior over released vocabulary and
  belong to #9; making them FHT vectors would let an FHT expectation depend on a
  tool's rubric.
- **Any real-data vector** (the chr4 bytes, the 334-record subset, the GFF exon
  proof). They stay pilot evidence in `pilot/dmel-chr4/`.

## What these vectors do **not** yet prove

- **No installed-toolkit behavior in the default path.** A default
  `fair-bioheaders` install still has no FHT feature: the released reader
  routes these records as FHR (rule V5), so there are no default-on
  `bioheaders`/`fhr-*` round trips, strip/combine or conversion claims.
  The opt-in V7 draft lane (fair-bioheaders 0.11.0,
  `BIOHEADERS_EXPERIMENTAL_FHT=1`) consumes this suite through the gated
  `tests/fht_conformance_test.py` in FAIR-bioHeaders-Tools, but a gated
  preview consumer is not shipped support: full support, including the
  default path, belongs to issue #9 after FHT ships in a toolkit release.
  "Strip/combine preserve sequence IDs,
  wrapping, U/T, metadata ordering/types and exact bytes under the
  established checksum coverage policy" is *represented here only* as
  byte-preservation fixtures (the alphabet variants and the
  normalization-rejection vectors); the executable round-trip half waits
  for #9. What has been measured since is recorded in
  [`../docs/CI.md`](../docs/CI.md) ("Manual lane — the named toolkit
  version"): `scripts/run_toolkit_lane.py` runs `verify`, `verify-links`,
  `strip` and a `convert`/`strip`/`combine` round trip against the suite
  with `fair-bioheaders` 0.11.0 under the opt-in lane, and reports
  agreement plus the writer's canonical-header findings. That is a draft-lane
  preview, not the default path, and it changes no expectation here.
- **No shared publication.** These vectors are not in the shared
  `conformance/manifest.json` and cite no resolvable FHT release URL,
  because none exists (the registry has no FHT entry; the w3id URL answers
  404, re-verified 2026-11-13). Expected outcomes for the V5 vectors are
  derived from the SCHEMA-VERSIONS.md rule text, including the V7 note
  (FAIR-bioHeaders-Specification#221 ruling, Option A, 2026-11-13, merged
  in `a4278c4622e8a90258fab8fa6c32532613f9bf26`): a release-shaped URL for
  a type no release registers is "any other value" under V5, read as FHR
  with the near-miss warning (FAIR-bioHeaders-Tools#125); V4 applies only
  once FHT enters `schemas/versions.json`. The FHR-invalid outcome was
  measured, not assumed: the current FHR schema — `fhr.json` at that shared
  commit, byte-identical to release tag `v0.5.0` (sha256
  `694ab5afaf8c3743eacf9e2aacb5551f7cbe37073b6f4afc3ae4a65b47f9d4df`) —
  rejects both records with the same five errors (`'1.0' is not one of
  ['2.0', '2.1']`; required `genome`, `assemblyAuthor` and `masking`
  absent; `transcriptome`, `assemblyType`, `moleculeType` match no FHR
  property or the `x-` pattern), reproduced on 2026-11-13 with jsonschema
  4.26.0 and confirmed by the released reader `bioheaders verify` from
  fair-bioheaders 0.10.0, which reports the V5 warning and the schemaVersion
  rejection for each file. Since 2026-11-18 CI computes this outcome on every
  run: the runner validates both records against the pinned copy of release
  v0.6.0's `fhr.json` (same bytes and digest as v0.5.0, recorded in
  `schemas/provenance.json`) and requires exactly those five errors. **No implementation under test produced any
  expectation in this
  directory** — there is no FHT implementation. The generator's own
  reference reader and the runner's independently written reader agreeing
  on every byte is the cross-check this stage can honestly offer.
- **No stdin/stdout vectors.** Stream *framing* is covered: `gzip` (one
  member), `bgzf` (multi-block with the EOF block) and `gzip-multimember`
  (two members with the member boundary inside the root checksum line) are all
  distributed as files whose decompressed bytes are `fht-fasta-lf`, which is
  what R1 makes decidable. What the shared manifest's file-based vocabulary
  cannot express is a reader fed a pipe instead of a path, so the CLI's
  stdin/stdout behavior stays #9 territory.

## How the shared suite absorbs these vectors

When FHT is published through the #55 chain
(FAIR-bioHeaders-Specification#107):

1. Copy the `valid/fht-fasta-*` and `invalid/fht-fasta-*` files and their
   manifest entries into the shared `conformance/` tree; the format id
   `fht-fasta` slots beside `fhp-fasta`.
2. Adopt the finalized fields: `selfChecksum` and `parentLink` were
   finalized at the draft stage with positive and negative fixtures (#37,
   maintainer decision 2026-11-14; semantics in "Finalized field semantics"
   above); shared absorption may rename them onto the shared manifest
   vocabulary but must not change the verdict model. C1-C3 already follow
   the shared rule-label scheme (#36) and carry over as the rule ids of the
   shared FHT format document.
3. Re-point the `schema` URL: vectors currently cite this repository's
   raw-main URL (the only contract that exists). At release, the same
   bytes move to a new `fht-fasta-schema-*` vector set citing the w3id
   URL, exactly as FHP moved to `…/fhp/v0.4.0`; the raw-main vectors stay
   valid under V1 and keep their ids (ids are never reused or rewritten).
   The `schema` constraint of `fht.json` also changes then: today it is
   the raw-main URL only (C2), and publication adds the V2 shared raw-tag
   and V3 w3id forms for the released version (issue #10). The V5-shaped
   rejection vectors then **diverge, and that asymmetry
   is the expected outcome** (recorded on closed #30; the V7 ruling,
   FAIR-bioHeaders-Specification#221 Option A): once FHT enters
   `schemas/versions.json`, a `https://w3id.org/fair-bioheaders/fht/vX.Y.Z`
   citation for an unregistered version becomes a genuine **V4**
   unsupported-version case, while a raw tag URL of *this development
   repository* (`…/FHT-Specification/v9.9.9/fht.json`) stays **V5**,
   because V2 anchors versioned release URLs to the shared publication
   repository and a dev-repo tag URL matches no V2 form at any point.
   Any outcome change retires the old id per the shared retirement rule.
4. Add the toolkit invocation to `scripts/check_conformance.py`
   (`--require-format fht-fasta`) once the released reader supports FHT.

Until then, `python scripts/check_fht_fixtures.py` (pinned jsonschema
4.26.0 + PyYAML 6.0.3, see [`../docs/CI.md`](../docs/CI.md)) is the
verification, and its failure classes are the acceptance list for #9's
toolkit implementation.

## Current mixed-molecule source coverage — 2026-11-16

The owning suite now has **75 vectors: 29 valid and 46 invalid**. The new valid
`fht-fasta-molecule-type-mixed` has an independently generated matching checksum;
`fht-fasta-molecule-type-mixed-case` rejects `Mixed` and
`fht-fasta-assembly-type-mixed` rejects a mixed construction type. All previous
72 vector bytes and outcomes remain unchanged. The installed 0.11.0 four-value
draft reader cannot accept the new positive vector: acceptance, strip and combine
for that vector are explicitly NOT-RUN, following a specific rejection probe.
All other comparisons and default-off checks still execute. The older counts
above describe their original measurement, not new reader coverage.

## Reader assertions, plain dates and truncated streams — 2026-11-18

The suite now has **77 vectors: 30 valid and 47 invalid**. Two vectors were
added and no existing vector's bytes or expected outcome changed:

- `fht-fasta-yaml-plain-date` (valid, R12): `dateCreated: 2026-11-10` written
  plain. FORMAT.md R12 says a plain scalar that looks like a date or time is a
  string, exactly as written; the shared suite's valid
  `fasta-yaml-portable-types` vector relies on the same reading. The runner
  previously rejected it as "must be quoted", which contradicted the rule.
  Writers still quote such values.
- `fht-fasta-gzip-truncated` (invalid, R1, `selfChecksum: unreachable`):
  `fht-fasta-lf` as one gzip member cut six bytes before its end, inside the
  CRC-32/ISIZE trailer. Every deflate byte is present, so a lenient
  decompressor returns the whole file, but the stream is incomplete and R1 has
  no decompressed bytes to hash.

A gzip stream followed by NUL padding or other trailing bytes is also rejected
by the runner's reader (unit tests in `tests/test_fixture_reader.py`), but no
vector asserts it: FORMAT.md does not decide padding, and the released
`fair-bioheaders` 0.11.0 reader accepts trailing NUL bytes (measured
2026-11-18), so that is reader policy here, not a rule-text outcome.

## Raw-main-only schema URL and portable patterns — 2026-11-18

At this dated revision the suite had **82 vectors: 30 valid and 52 invalid**.
The current vector list and outcomes are in [`manifest.json`](manifest.json),
which is authoritative for the census. Five invalid vectors were added; no
existing vector's bytes or expected outcome changed.

- `fht.json` accepts only the raw-main `schema` URL (C2 above). The V5 vector
  `fht-fasta-schema-shared-raw-tag` cites the V2 form
  `…/FAIR-bioHeaders-Specification/v0.6.0/fht.json`: no release carries an
  `fht.json`, so it is read as FHR and rejected there like the other two V5
  vectors. `fht-fasta-schema-trailing-line-feed` (C2) is the raw-main URL plus
  a line feed.
- FHT's own patterns are written so Python's `re` (jsonschema) and ECMA-262
  (ajv, browsers) agree. Anchored patterns end with `(?![\s\S])` instead of
  `$`, which Python also matches before a final line feed. Non-blank checks use
  an explicit character class, the union of both dialects' whitespace, instead
  of `\S`, because Python counts U+001C-U+001F and U+0085 as whitespace and
  U+FEFF as not, and ECMA-262 the reverse. The C1 vectors
  `fht-fasta-run-accession-trailing-line-feed`,
  `fht-fasta-blank-transcriptome-bom` and `fht-fasta-blank-version-separator`
  each used to be accepted by one dialect. Patterns imported unchanged from the
  pinned shared core (for example `scholarlyArticle` and `identifier`) keep
  their shared form.
