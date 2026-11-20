# Maintenance and review record — November 20, 2026

Audited default baseline: `5e7029d7c253c2030cc33a09374d838b3992f95a`. The Round 16 maintenance PR adds
policy/docs and the explicitly described fixes below; the PR records its current
head, CI and independent model review separately. This is a bounded source review,
not a certification of security or biological correctness.

## Executed security scans

| Surface | Tool and command | Observation |
| --- | --- | --- |
| Python source | Bandit 1.8.6 on Python 3.13.16: `bandit -r . -x ./drafts,./tests,./conformance,./header,./python,./docs -f json` | 11,697 lines; 102 findings, zero scanner errors; dispositions below |
| Workflow source | zizmor 1.16.3: `zizmor --offline --format json .github/workflows` | No findings |
| Available Git history | gitleaks 8.30.1: `gitleaks git --redact --no-banner --report-format json .` | 185 findings; reviewed historical synthetic accession/SeqCol/checksum metadata, not authentication credentials |
| Declared Python dependency closure | pip-audit 2.9.0: requirements resolution with PyPI advisory service, November 20, 2026 | 85 resolved packages; no known advisories returned |

Dependency inputs were `requirements-linkml.txt` and `requirements-jsonld.txt`.
Resolution is platform/time dependent, not a lockfile or audit of every future
version admitted by a range. Workflow-installed toolkit/browser tools, operating
system packages and external services are separate environments; their mere
presence in a workflow is not a dependency audit result.

The first Bandit attempt on Python 3.15 raised per-file scanner exceptions despite
exit zero. It was invalidated and repeated on supported Python 3.13; no zero-result
claim uses that failed scan. The local detailed evidence retains commands, JSON,
locations and original failures, with secret findings redacted.

## Static findings and general source review

Bandit rule counts: B101: 23, B302: 1, B310: 1, B311: 8, B324: 6, B404: 16, B506: 2, B603: 28, B607: 17.
Subprocess findings use explicit argument arrays without a shell in trusted source
maintenance commands; tools must come from the chosen environment. SafeLoader
subclasses deliberately retain date strings and strict field rules; they do not
construct Python objects. Assertions and seeded random values are fixture/checker
oracles, not authorization or secret generation. MD5/SHA-1 uses record upstream
checksums, provenance or legacy fixture behavior, not file-bound SHA-512/256
substitution. Network checks read declared repository links with timeouts and
report failure; this local maintenance tooling is not an unrestricted hosted
fetch/validation service.

Review covered CLI inputs/outputs and failure paths in owned generators/checkers,
file replacement and scratch paths, schema/checksum/selection boundaries, pinned
code-loading adapters, YAML/HTML handling, workflow permissions and PR trust.
Publication, curator acceptance and package installation remain separate acts.
Whole-file reads and decompression assume bounded, supplied research/test inputs;
no hostile-input resource-isolation guarantee is made. Reusing these scripts as a
network service requires a separate limits and trust-boundary review.

The reference inventory decodes (never executes) local `.pyc` objects with
`marshal` to classify runtime cache files. Bandit B302 is retained as a trusted
local-checkout limitation: do not use untrusted copied cache files as server input.
Frozen `drafts/` source was excluded from automated editing/scanning; its pinned
239/134-file source sets and historical 291-payload ledger remain unchanged.

### Confirmed fix: destructive output selection

`scripts/build_pages.py` replaced an existing output with recursive deletion before
checking whether it was the checkout or its ancestor. A mistaken `.`/`..` could
delete source. The fix rejects repository/ancestor, Git metadata, tracked-source and symlink
outputs before removal. Regression tests prove no deletion of checkout, parent, another Git
worktree, Git metadata, tracked docs or a symlink target, while ordinary scratch
builds still work.
This is a local data-loss/correctness finding, not a remote exploit claim.

## Guidance, workplans and retained branches

The current [working guide](WORKING-GUIDE.md) indexes setup and source tools.
Live AGENTS/llms/contribution guidance uses human-only merges and actual independent
model review. Existing local skills and historical plans remain subordinate to
that live rule. There are no nested tracked AGENTS copies in this repository.
Older plans and dated receipts are historical design/evidence; their checkboxes
are not new work authorization. Immutable published/vendored bytes retain their
provenance, and any older embedded instructions are non-operative.

The repository/common-directory inventory records exact local and tracking refs,
worktree paths, dirty status and default ancestry. Old branch ownership and active
use are not proven merely by names, age or merged ancestry. Those candidates are
retained for exact human ownership decisions; no forced removal, reset, remote
branch deletion or historical tag change was performed. The Round 16 worktree and
PR branch stay active through human review.

The PR handoff records actual test skips and CI. Browser, installed-package,
network and external-owner checks are not silently credited by local Python
checks. A human must merge; no release or website publication occurs here.
