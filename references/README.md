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
