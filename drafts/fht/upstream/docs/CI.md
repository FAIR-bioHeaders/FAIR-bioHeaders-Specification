# Continuous integration and local checks

Status: CI lanes for issue #14 (PR checks for the draft schema, examples and
documentation) plus issue #8 (the byte-backed fixture lane). Every check
below also runs locally with the commands given here. None of these lanes
claims that the legacy draft implements the current family contract, that a
fixture was produced or consumed by an installed toolkit, or that CI setup
amends any schema.

## Lanes

| Workflow | Trigger | Covers |
| --- | --- | --- |
| [`validate-specification.yml`](../.github/workflows/validate-specification.yml) | push/PR | The **current FHT 1.0 development contract**: unit tests over the generated `fht.json` (positive/rejection fixtures in `tests/test_fht_schema.py`, synthetic examples in `examples/`, byte-backed conformance vectors via `tests/test_fixtures.py`), LinkML regeneration drift and the pinned shared-import provenance. Pre-existing; extended by #8. |
| [`fht-fixtures.yml`](../.github/workflows/fht-fixtures.yml) | push/PR | The issue **#8** byte-backed fixtures via `scripts/check_fht_fixtures.py`: regeneration determinism (in-process rerun compared byte-for-byte with `conformance/` and the owned `examples/` files), an independently written R1-R5 reader recomputing every vector checksum, strict R6-R8/R10/R12/R13 header checks (each invalid vector must be rejected by the rule its manifest entry declares; contract vectors must raise exactly their recorded `fht.json` errors), an independent RFC 1952 reader that requires complete gzip members, `fht.json` contract validation with `FormatChecker`, V1/V5 schema selection (with the V7 draft-lane note; the V5 rejection is computed against the pinned released `schemas/fhr-v0.6.0.json`), C3 parent-link outcomes with parent paths confined to the distributed tree, manifest accountability for every lettered FORMAT.md rule (R1-R15 registered, each with both sides or a recorded `notApplicable` reason), and the examples recomputation. The independent job invokes no toolkit. A separate installed-draft job runs the named toolkit under V7; see below. |
| [`docs-checks.yml`](../.github/workflows/docs-checks.yml) | push/PR | Owned documentation signals: Markdownlint with the reviewed local config `.markdownlint-cli2.jsonc` (pinned `markdownlint-cli2@0.24.0`, rule set 0.42.0), plus `scripts/check_docs.py` for local relative links/anchors, whitespace (trailing spaces, CR bytes, final newline) and git conflict markers. Fails the job only on real findings; no network access. |
| [`legacy-draft-checks.yml`](../.github/workflows/legacy-draft-checks.yml) | push/PR | Schema health of the preserved legacy draft `legacy/fht-v0.1.json` (`scripts/check_legacy_schema.py`) and the classified example/fixture suite (`scripts/check_legacy_examples.py`). |
| [`external-links.yml`](../.github/workflows/external-links.yml) | schedule (Mondays) + `workflow_dispatch` | Every http(s) URL cited by repository Markdown, one retry each. Never a PR signal: transient remote failures must not gate unrelated work. |

Every PR lane runs all of its steps (`continue-on-error` steps plus an
`if: always()` summary-and-gate step), so one run reports all findings and
each workflow exposes exactly one required-check-friendly status. All
workflows run with `permissions: contents: read`, `persist-credentials:
false`, pinned action commits (checkout v7, setup-python v7, setup-node v7)
and a job `timeout-minutes`.

## Later stage — adopted-contract conformance

Issue **#8** has landed the byte-backed side: `conformance/` carries the
RNA/cDNA positive and rejection vectors, the parent-link fixtures and the
schema-selection fixtures with independently cross-checked checksums, and
`scripts/check_fht_fixtures.py` runs every expectation against the rule
text (see [`../conformance/README.md`](../conformance/README.md) for scope
and honest limits). Still a clearly-labeled later stage, gated on issue
**#9** (installed toolkit support: `fair-bioheaders` gains an FHT reader
and the round trips — strip/combine, conversions and stdout/stdin behavior
— are then re-run against these same vectors with a named toolkit version)
and on the shared publication chain (this repo **#55**,
FAIR-bioHeaders-Specification#107). Shared-core generation/drift against
the publication copy and version-registry coordination are part of that
same gate. Until #9 lands, the synthetic `examples/` remain labeled
synthetic, the vectors' expected outcomes are derived from the rule text
rather than any implementation, and no checksum or SeqCol value here
describes real biological material.

## Installed-artifact lane — the named toolkit version (issue #8 box 7)

`scripts/run_toolkit_lane.py` runs the suite against an **installed**
`fair-bioheaders` and is the box-7 evidence: the checks are the suite's own
rule-derived expectations, executed by a second implementation instead of by
this repository's reader. The independent fixture job does not call it; a separate installed-draft job now does:
it needs a toolkit environment, and FHT is a draft, so the lane reads every
record through the opt-in rule V7 switch
(`BIOHEADERS_EXPERIMENTAL_FHT=1`, set by the script itself). Running under that
switch is recognition of a development contract, not shipped support: default
behavior is unchanged, `fair-bioheaders` still has no FHT feature, and issue
**#9** owns making any of this a released capability. The script never edits
`conformance/`; a disagreement is reported as a failure and becomes a finding
for #9, never a re-expectation.

```sh
python3 -m venv /tmp/fht0110venv
/tmp/fht0110venv/bin/pip install fair-bioheaders==0.11.0
python scripts/run_toolkit_lane.py --venv /tmp/fht0110venv
```

Measured run of 2026-11-15, recorded here rather than restated from the
script's prose. Environment: macOS on a case-insensitive APFS volume,
Python 3.15.0, `bioheaders --version` → `0.11.0`, installed from PyPI into a
throwaway venv (`pip show fair-bioheaders` reports `Version: 0.11.0` in
`site-packages` with no editable location). The suite at this commit is 72
vectors: 28 valid, 44 invalid, 3 parent fixtures.

| Lane | Result |
| --- | --- |
| Draft pin | the bundle registers the FHT draft at commit `b9ad19a62772092e08935cff44ee77a50981bbaf`, retrieved 2026-11-12, sha256 `11c69d6647736695beaa72976a1d9b30c0f44f8cfe55f8eb171c9d0bcb6795f8`; the installed `bioheaders/schemas/fht-draft.json` hashes to exactly that digest; this checkout's `fht.json` is `59ad9641adcb0e5591045c2d894c066d1adc9984cca84c5ff6502f8dad88487e`, so the agreement below is agreement with the **pinned** revision, not with `main` |
| `verify`, lane ON | 28 valid accepted, 44 invalid rejected, **0** disagreements with `expected`. The 7 `selfChecksum: broken` vectors were each reported as a checksum failure, and no `selfChecksum: matches` vector was rejected by the comparison, so no rejection happened by accident |
| `verify-links`, lane ON | the 10 `parentLink` vectors printed `matched (` / `not checked (` / `not matched (` with exit 0 / 0 / 3 exactly as their entries declare: checked-pass, unchecked and checked-fail stay distinguishable (C3), including the mixed-verdict record where one entry passes and the other fails |
| `verify`, lane OFF | all 72 rejected, **0** accepted: 61 fail at `$.schemaVersion: '1.0' is not one of ['2.0', '2.1']` after the V5 warning, 1 at `$.schemaVersion: 1.0 is not of type 'string'`, 1 at `$: 'genome' is a required property`, and 9 earlier in the FHR reading (BOM, U+2028, duplicate key, anchor/alias, the two-checksum-line and concatenation YAML block errors, `011`, `.inf`, header-after-record). This is the default path: with the lane closed the released reader has no FHT schema, so rule V5 routes every FHT citation to the current FHR schema |
| `strip` | for all 28 valid vectors the output equals the input with exactly the `;~` lines removed: record identifiers, line wrapping, the U or T alphabet, letter case (including the lower-case sequence line), ordinary `;` comments and blank lines all stay byte-identical and stay **in place**, including in the CR, CRLF, mixed-ending, no-final-newline and interleaved-comment cases. Compressed vectors are compared on their decompressed bytes, which is what R1 makes the file's content |
| `combine` | metadata values, key order and value types survive `convert` → `strip` → `combine` for all 28 valid vectors, and every recombined file verifies; **0** of 28 recombined files are byte-identical to the distributed bytes, because the writer emits its own canonical header for the same values — allowed by FORMAT.md ("the combine helpers regenerate a canonical YAML header … Strip removes complete FHR lines and leaves ordinary comments intact"), and recorded here because it bounds what "preserve exact bytes" can mean |

Findings for #9 from the same run, none of which changed a vector or an
expectation:

- **The draft pin is older than `main`** (above), so a run against an installed
  0.11.0 is a run against `b9ad19a6…`'s contract bytes.
- **The lane warning does not name the commit or the digest.** Rule V7 asks for
  `… is an unreleased draft (commit <full sha>, sha256 <digest> of those bytes)`,
  and 0.11.0's warning names only the URL and the opt-in variable
  (`grep` for the pinned commit `b9ad19a6…`, the digest `11c69d66…`, the words
  `commit` or `sha256` across the captured stdout and stderr of a lane-on
  `verify` returns no match). The information exists in
  `schemas/bundled.json`; it is not surfaced per record.
- **A checksum failure is printed with the `FHR:` prefix** even for a record
  selected through the FHT draft lane (`fht-fasta-sequence-tampered.fht.fasta` →
  `FHR: Checksum verification failed`), which misattributes the verdict.
- **The writer re-quotes plain scalars** it considers unambiguous
  (`version: '1.0.0'` → `version: 1.0.0`), which is a canonical-header choice
  under FORMAT.md but means a byte-exact whole-file round trip is not what
  combine promises.
- **`bioheaders assess` answers `not assessed: unsupported-header-type`** for an
  FHT record read through the lane (re-measured on `fht-fasta-lf.fht.fasta`,
  matching the pilot's observation in
  [`../pilot/dmel-chr4/README.md`](../pilot/dmel-chr4/README.md)).
- **Only JSON and YAML are serializable today.** With the lane open,
  `bioheaders convert <fht file> out.{json,yaml} --to {json,yaml}` succeed from
  an FHT FASTA input, while `--to jsonld` exits 1 with `JSON-LD output is not
  available for FHT metadata yet` and `--to html` exits 1 with `HTML microdata
  output is not available for FHT metadata: no reviewed FHT binding exists
  (FHT-Specification#9)`. That is the measured basis for box 2 keeping JSON-LD
  and microdata out of `examples/`, and for R9 — a microdata-only rule — having
  no vector here.

This lane is **not** box 4's or #9's acceptance: it is a draft-lane preview on a
case-insensitive filesystem, so it establishes that the released reader's
behavior agrees with the rule text on this suite today — not that FHT is
supported in the default path, and not Linux or macOS case-sensitivity as
separate evidence. Issue **#9** owns the default-path implementation, its own
acceptance run, and released stdin/stdout acceptance. The process-level stream lane below
adds draft evidence without extending the file-based manifest.

## Pinned tools (PR lanes)

| Tool | Pin | Where |
| --- | --- | --- |
| Python | 3.13 (CI image) | all workflows |
| jsonschema | `4.26.0` (`jsonschema[format]`) | legacy-draft and fixture lanes; also inside the `>=4.21,<5` range of `requirements-validation.txt` |
| PyYAML | `6.0.3` | legacy-draft and fixture lanes |
| markdownlint-cli2 | `0.24.0` (markdownlint 0.42.1 rule set) | docs lane via `npx -y`, Node 22 |
| LinkML lane environment | every package exact in `requirements-linkml.txt` (linkml 1.11.1, jsonschema 4.26.0, PyYAML 6.0.3 and their transitive dependencies) | `validate-specification.yml` `validate` job |
| Playwright | `1.65.0` with its Chromium | `validate-specification.yml` `browser` job |
| actions/checkout | `3d3c42e5…` v7 | all workflows |
| actions/setup-python | `5fda3b95…` v7 | all workflows |
| actions/setup-node | `949feb24…` v7 | docs lane |

Local setup used for authoring and reproducible in CI:

```sh
python3 -m venv /tmp/fht14venv
/tmp/fht14venv/bin/pip install "jsonschema[format]==4.26.0" "PyYAML==6.0.3"
```

## Running everything locally

From the repository root:

```sh
# Documentation lane (standard library only)
python scripts/check_docs.py
npx -y markdownlint-cli2@0.24.0

# Legacy draft lane (pinned jsonschema/PyYAML)
python scripts/check_legacy_schema.py
python scripts/check_legacy_examples.py

# Fixture lane (pinned jsonschema/PyYAML; regenerates nothing in the tree)
python scripts/check_fht_fixtures.py

# Regenerate the #8 fixtures and owned examples after editing the generator;
# the fixture lane then proves the committed bytes match a fresh run
python scripts/make_fht_fixtures.py

# Current contract lane (pre-existing; needs requirements-linkml.txt)
python -m unittest discover -s tests -v   # includes tests/test_ci_checks.py

# Manual lane (issue #8 box 7) — needs an installed fair-bioheaders and is
# also runs in the separate installed-draft PR job through the opt-in V7 lane
python scripts/run_toolkit_lane.py --venv /path/to/fair-bioheaders-venv

# Scheduled lane only — never part of a PR signal (network required)
python scripts/check_external_links.py
```

## Schema health of the legacy draft

`scripts/check_legacy_schema.py` parses `legacy/fht-v0.1.json`, detects the
**declared dialect** `https://json-schema.org/draft/2020-12/schema` via
`jsonschema.validators.validator_for` (matching validator
`Draft202012Validator`), meta-validates it and **enables format checking
explicitly** with `FormatChecker()` from `jsonschema[format]`. A paired probe
shows a `date`-format violation is rejected only with the checker attached —
the legacy contract's `format: date`/`format: uri` annotations are inert
otherwise. The file's SHA-256
(`34eec2e5…894aa`, also recorded in `legacy/README.md`) is pinned, so the
historical bytes cannot drift without an explicit, reviewed change.

The check prints a **defect registry** — documented, not silently patched:

| id | Measured current behavior of the legacy draft |
| --- | --- |
| L1 | `taxon.uri` pattern is unanchored with unescaped dots: leading/trailing junk and `identifiersXorg` match |
| L2 | ORCID pattern has no end anchor and unescaped dots: trailing junk after a valid iD passes |
| L3 | `scholarlyArticle` `^10.` accepts e.g. `10X` |
| L4 | `identifier` item pattern is unanchored |
| L5 | Only the top level closes `additionalProperties`; nested objects accept unknown keys (the historical `url`-instead-of-`uri` typo passes) |
| L6 | No nested `required`: empty author objects and a nameless taxon validate |
| L7 | `masking` is required but its alternation is unanchored (`who knows? unknown` passes) |
| L8 | `checksum` (`definitions.sha2`) constrains only 44 base64-charset characters; no algorithm or byte coverage — real coverage is FORMAT.md/#8 territory |
| L9 | `schemaVersion` is typed `number`; the current draft's string `"1.0"` is rejected — recorded incompatibility, preserved as-is |
| L10 | `date`/`uri` formats are enforced only because the validator enables `FormatChecker` explicitly |
| L11 | The legacy `$id` is the raw-main `fht.json` URL, which today serves the FHT 1.0 draft — cite the archived path/tag for audit |

Each registry entry is a live probe: if a probe's measured behavior changes,
CI fails and the change must be reviewed — CI never edits the contract.

## Example validation and classification

Supported example formats are parsed safely (`json.loads`, `yaml.safe_load`;
FASTA via its `;~` block). The current-contract examples in `examples/` are
validated by `tests/test_examples.py` (pre-existing lane). For the legacy
lane:

- **Positive fixtures** — `tests/fixtures/legacy/valid/full-legacy-record.json`
  must validate against `legacy/fht-v0.1.json` with zero errors (its
  checksum/ORCID/DOI strings are synthetic placeholders following
  `tests/test_fht_schema.py`'s `"A"*43+"="` convention — never real digests).
- **Rejection fixtures** — `tests/fixtures/legacy/rejected/*.json` with
  measured expectations in `expected.json`: missing required fields, unknown
  top-level properties, wrong scalar types (`schemaVersion` string,
  `transcriptome` number), `masking`/`checksum` pattern violations, a
  non-date `dateCreated` and a malformed `relatedLink` URI. Matching is
  exact per path: new errors, disappearing errors and repairs all fail.
  Regenerate with `python scripts/make_legacy_fixtures.py`.
- **Historical samples** — `legacy/examples/` are byte-pinned review inputs,
  classified in `tests/fixtures/legacy/classification.json` (tracked reasons,
  linked to this issue and `legacy/README.md`):

| file | classification | measured |
| --- | --- | --- |
| `example.fht.json` | nonconforming-historical | 4 schema errors: top-level `$schema`/`$id`/`assemblySoftware`/`reuseConditions` unknown; `md5:` checksum too short + bad charset; `soft-masked` fails the masking pattern. Notes: taxon URI is *Homo sapiens* (9606) for "Bombas huntii", `schema` URL truncated (`FHT.jso`), author `url` typo silently accepted (L5). |
| `example.fht.yaml` | nonconforming-historical | 4 schema errors: same field-level defects without `$schema`/`$id`; `schemaVersion: 1` is a legacy-valid number. |
| `example.fht.fasta` | unparseable-historical | `;~` block fails YAML parsing (`expected <block end>`): misindented author list items. Would still carry the value defects. |
| `example.microdata.fhr.html` | not-json-or-yaml-historical | HTML presentation artifact (retired converter era); outside the JSON/YAML lane, kept verbatim. |

A repaired, newly-broken or edited historical file fails
`scripts/check_legacy_examples.py` (digest pins + exact error matching); the
correct response is a reviewed re-classification, never a silent in-place fix.

## External links

`scripts/check_external_links.py` collects every http(s) URL cited **as a
Markdown link or angle autolink** (URLs that appear only as inline code, e.g.
dialect identifiers or version templates, are not fetch targets), fetches
each (GET, 30 s timeout, one retry after 5 s, descriptive User-Agent) and
fails on any non-2xx/3xx answer. It runs only on the weekly schedule and on
manual dispatch; the independent PR checks do not fetch these links, so a transient remote
failure cannot be their sole signal. Dependency installation in CI is separate.

### Exclusions

Exclusions live in `scripts/external-links-exclusions.json`. Policy: narrow
(exact URL or explicit prefix), dated, and justified by recorded evidence of
a durable failure or a bot-hostile endpoint; transient failures are retried,
not excluded; adding an entry is a reviewed maintainer change. **Baseline
(2026-11-10): all 32 linked URLs in repository Markdown answered HTTP 200 in
local runs, so the exclusion list is intentionally empty.**

## Reviewer notes

- No schema bytes (`fht.json`, `fht_linkml.yml`, `legacy/*`), examples or
  historical URLs/checksums were changed by this CI work; the only edited
  prose is one re-wrap in `specs/005-rna-transcriptome-header/spec.md` (a
  line beginning `#9` read as an ATX heading), `README.md` (pointer to this
  file) and new files.
- Markdownlint deviations from the default rule set are limited to MD013 and
  MD060, each with a recorded reason in `.markdownlint-cli2.jsonc`.

## Installed draft job and stream evidence (round 11)

The independent `fixtures` job remains independent of the toolkit. The separate
`installed-draft` job installs `fair-bioheaders==0.11.0` into a fresh environment
and runs `scripts/run_toolkit_lane.py` on Linux. The package installation is not
an editable checkout. Package version and bundled draft digests are printed;
a mismatched bundled digest stops the run before any vectors are scored.

The new stream lane sends the committed bytes of every vector to `verify -`
(including gzip/BGZF bytes), and compares `strip - -` stdout byte-for-byte with
the independently derived payload for every valid vector. It sends those payloads
through `combine <metadata> - -o -`, compares the resulting payload bytes, and
compares independently parsed input and stdout metadata (values, recursive key
order and exact scalar types, excluding only the regenerated root checksum), and
verifies the resulting stdout through stdin. Captured stderr is never joined to
payload stdout. A 60-second per-command timeout and nonzero case-count checks
prevent hanging or empty runs from reporting success.

This is additional implementation evidence, not a shared manifest extension,
independent expectation approval, curator acceptance, or default FHT support.
The historical macOS run above remains a dated measurement; Linux evidence is
provided by the new CI job when it actually executes, not by this document.
See [the acceptance and decision packet](FHT-READINESS.md).

## Current source enum versus installed draft — 2026-11-16

The source suite is now 75 vectors (29 valid, 46 invalid). Installed 0.11.0
registers a four-value enum and cannot represent the newly valid `mixed` value.
The runner reads that installed schema, probes the exact positive case for a
specific moleculeType rejection, then reports source acceptance, strip and combine
NOT-RUN for that one ID. An unexpected acceptance or unrelated failure fails the
lane. The other 74 vectors remain ordinary comparisons; all 75 run default-off.
No manifest expectation or approved consumer pin is changed. Earlier 72-vector
results above remain the dated pre-addition measurements.

## Reader assertions and a Linux toolkit run — 2026-11-18

`scripts/check_fht_fixtures.py` now asserts, per invalid vector, the rule that
rejects it (byte rules by the rule id the reader raises; contract rules by the
exact `fht.json` errors recorded per vector; V5 by validating against the pinned
released FHR schema; C3 by recomputing the link as `checked-fail`). The suite is
77 vectors (30 valid, 47 invalid) after adding `fht-fasta-yaml-plain-date` and
`fht-fasta-gzip-truncated`; see
[the conformance README](../conformance/README.md#reader-assertions-plain-dates-and-truncated-streams--2026-11-18).

Measured 2026-11-18 on Linux (Python 3.13.14) with `fair-bioheaders==0.11.0`
from PyPI in a fresh environment, `python scripts/run_toolkit_lane.py`: lane ON,
29 valid accepted and 47 invalid rejected with no disagreement; 10 `parentLink`
vectors with the three verdicts distinguishable; 29 strips and 29 combines
round-tripped; streams `verify` 76, `strip` 29, `combine` 29. The `mixed`
positive stays NOT-RUN against the installed four-value enum, as above. Both new
vectors agree with the installed reader: it accepts the plain date and rejects
the truncated stream ("Compressed file ended before the end-of-stream marker was
reached").

## Installed reader against this checkout's contract — 2026-11-18

The `installed-draft` job now runs the named release twice, each in its own
fresh environment:

1. **As installed.** `fair-bioheaders==0.11.0` reads the draft revision it was
   built with (`b9ad19a6…`). A vector whose verdict that older contract decides
   differently from this checkout's `fht.json` is not compared with the
   rule-text expectation; the reader must instead agree with its own installed
   bytes, and the vector is reported NOT-RUN as a finding for #9 (this
   generalizes the earlier `mixed` handling).
2. **Against this checkout.** `run_toolkit_lane.py --checkout-contract --strict --stage-completeness`
   overlays this checkout's `fht.json` onto the throwaway environment's draft
   file and registry digest. Following adopted D2, two arithmetic-only invalid
   vectors are explicitly NOT-RUN by this old runtime, with actual acceptance
   probes and independent owning rejection checks. Every other vector is
   compared; unexplained findings or any disagreement still fail. Runtime
   arithmetic enforcement remains #9 publication follow-through.

Measured locally on Linux (Python 3.13.14) on 2026-11-18 with the 82-vector
suite: as installed, 78 vectors compared with no disagreement and 4 NOT-RUN
(`mixed` plus the three dialect vectors the older draft accepts); against this
checkout, all 82 compared (30 valid accepted, 52 invalid rejected), with 0
findings.

`validate-specification.yml` checks out full history (`fetch-depth: 0`): the
typed-HTML binding test resolves the commit that last changed `fht.json` and
verifies its stored bytes ([FHT-MICRODATA.md](FHT-MICRODATA.md)).

## Locked contract environment and browser lane — 2026-11-18

`requirements-linkml.txt` is now an exact lock of the whole environment the
`validate` job installs (resolved for CPython 3.13), so `json-schema-generator.py`
regenerates `fht.json` from the same LinkML, jsonschema and transitive versions on
every run; a fresh install from the lock reproduced the committed `fht.json`
byte for byte. The `browser` job of `validate-specification.yml` installs
Playwright 1.65.0 and Chromium outside the checkout and runs
`scripts/check_fht_html_browser.mjs`, which extracts the seven typed-HTML
examples through a real browser DOM and compares them with the canonical JSON
(locally: "7 standalone records match Chromium DOM extraction; no active content
or network requests").
