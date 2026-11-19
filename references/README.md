# Cross-repository reference audit

The [D7 decision](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7017854934)
preserves released contracts, including their legacy `$id` bytes. Those identifiers
are namespace identities; they do not instruct a reader to retrieve today's
raw-main content. Retrieval authority is the named release tag, its dereferenced
commit and the exact artifact digest. A raw-main URL used as a draft citation
under V7 likewise does not replace its separate pinned contract/suite commits.

`inventory.json` is a dated normalization of declared references at the eleven
recorded consumer commits. Each consumer lists the exact source record and its
SHA-256 so the normalization can be reviewed against content-addressed source.
It is data for `scripts/check_references.py`, not permission to update any pin.
Coverage gaps are explicit data and remain work under #241. This initial packet
is **not** a claim that every consumer is covered or its scheduled audit deployed.

| Class | Independent authority |
| --- | --- |
| released-contract | Named release tag, resolved commit, exact digest |
| draft-contract | Owning repository's pinned full commit and digest |
| conformance-suite | Its own suite revision and manifest/file digests |
| base-carrier | Named released carrier tag, commit and digest |
| copied-tree | Declared selected path set, source revision and per-path digests; released copies use a release tag |

FHR compatibility mirrors and the released FHGFF3 `header/` mirror remain
release-pinned. A deliberate sync moves tag, dereferenced commit, copied bytes
and their digests together. A development snapshot must be separately and
explicitly classified as draft; it cannot silently replace a released mirror.
Historical non-release fixture overrides remain historical evidence, not a claim
that their commit is a published release. Do not infer adoption from parity.

## Running the advisory audit

```sh
python scripts/check_references.py --consumer FAIR-bioHeaders/FHT-Specification
python scripts/check_references.py --consumer FAIR-bioHeaders/FHT-Specification --consumer-root /path/to/FHT-Specification --checkout FAIR-bioHeaders/FAIR-bioHeaders-Specification=/path/to/shared
```

The default remote resolver uses the GitHub API, resolves tags before fetching
content-addressed bytes, and requires a confirmed missing-path negative control
for each reference group. An offline run with `--checkout` makes no network
request: every authority must be mapped and its objects/tags fetched. Unmapped
or missing git objects are failed queries, not confirmed missing artifacts.
`FRESH`, `DRIFT` and `ABSENT` describe actual comparisons/declaration gaps;
`QUERY_FAILED` separately records permission, rate-limit, transport, malformed
response or control failures. Empty measurements never establish agreement.
The JSON report distinguishes an unperformed local comparison from one performed.
Advisory exit is zero; `--exit-on-findings` is available for controlled tests.
Neither mode writes pins or consumer files.

Tagged references also need their recorded dereferenced full commit; a missing
commit is an incomplete declaration (`ABSENT`), not a fresh tag-only comparison.
A full commit-kind revision already records that immutable commit. Missing-only
authority/local file-set differences stay `ABSENT`; changed bytes, unexpected
files or records outside the selected scope are `DRIFT`. A failed query remains
`QUERY_FAILED`. Offline Git resolution disables replacement objects, so a
`refs/replace` entry cannot substitute bytes or source sets for a recorded
immutable commit. Exact `sourceExclusions` apply only inside an explicitly declared
source scope; nonexistent or duplicate exclusions cannot produce `FRESH`.

## Current staged draft declarations

The dated `inventory.json` remains unchanged. The separate
`scripts/audit_current_references.py` reads **current** `drafts/fht/source.json`
and `drafts/fhgm/source.json` on each run, rather than freezing another copy of
their file lists. Both are explicitly `copied-tree` references to draft material
at full owning commits. Expected repositories, canonical source/local mappings,
digests and selections are checked before querying authorities:

- FHT selects all tracked owning files except exactly `AGENTS.md`.
- FHGM selects `development/` and exactly `.gitattributes`, `LICENSE` and
  `tests/test_fhgm_conformance.py`.

The checker compares complete independent selected source and local sets, so
deleting a file and its manifest entry together still reports `DRIFT`. Only
recognized current-interpreter bytecode caches for declared Python modules,
with valid headers and a complete marshaled code-object payload (decoded but
never executed, with no trailing data), are local exceptions. Unknown Python/data files
and cache-shaped data are not hidden. These reference comparisons do not replace
the candidates' separate provenance, schema, conformance or runtime evidence.

```sh
python -I scripts/audit_current_references.py --plan
python -I scripts/audit_current_references.py \
  --checkout FAIR-bioHeaders/FHT-Specification=/path/to/owning-fht \
  --checkout FAIR-bioHeaders/FHGM-Specification=/path/to/owning-fhgm
```

This audit has no GitHub API fallback: every authority is an explicit checkout,
and unavailable objects/mappings are `QUERY_FAILED`. The scheduled/manual
`current-references.yml` workflow checks out the commits from validated current
declarations and retains the actual JSON, including a setup-failure fallback.
It avoids an extra per-file GitHub API request budget for the staged trees.
Normal PR tests use controlled temporary owning repositories; real declaration
findings remain advisory, with no auto-repin, publication or new PR freshness
gate. Neither this workflow nor the adapter updates `source.json`, payloads or
the dated inventory.

Consumer rollout must pin this checker by source commit/digest, declare the
consumer's own references, schedule it with read-only permissions, retain the
JSON artifact and surface findings without auto-repinning. Central delivery
alone does not satisfy that rollout acceptance. Consumers with derived subsets
must validate the declared transform and payload files, not compare a filtered
manifest's whole-file digest with its parent's digest. For the two header mirrors, explicit source patterns establish the complete
49-path selected upstream set, and declared local-tree exclusions separate authored
documentation from copies. Other selected-path references report set checking as
not-run unless a complete scope is declared; a positive per-file audit alone
does not establish absence of undeclared paths.

## Future publication identity preflight

`released-identities.json` records exact historical release bytes. Run:

```sh
python scripts/check_contract_identity.py fhr.json
```

An exact path/digest match preserves its historical identifier without a schema
edit. New or changed published bytes must instead carry a stable versioned w3id
identity and receive explicit identity/release review. A passing syntactic
preflight is not publication authorization, proof of alias resolution or adoption.
There is no general exemption for `$id` changes in schema drift checks. Released
bytes, drift baselines and archived tags are not rewritten by this policy.

The publication identity check runs **first** in the existing companion release
preflight, `python scripts/check_release.py --converter /path/to/toolkit`.
For identity review without a companion checkout, use
`python scripts/check_release.py --identity-only`. This is a release-preflight
check, not a new always-on schema drift exception. The exact-byte legacy ledger
is applied before assessing new publication candidates; modifying any other
byte of a legacy contract removes that exception and requires a stable identity.
