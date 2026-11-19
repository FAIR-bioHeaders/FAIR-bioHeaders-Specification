# FHT immutable draft handoff

**Publication candidate, not a released contract.** The shared
[handoff checklist](../../docs/FHT.md) names the exact final acceptance and
publication steps. No root contract, release selector, registry row, current
published alias or consumer support is established by this directory.

`upstream/` is the complete tracked owning snapshot at
`0f6eb7763aa88d05a42fa69b02cf3f89f5cc3b00`, excluding only `AGENTS.md`:
this is source evidence, not another common-guidance port. Existing local shared
guidance controls this candidate. Original source paths, dependency imports,
fixtures, model, reference binding, legacy/pilot provenance, licenses and notices
are preserved byte-for-byte. Nested `.github/workflows/` files are inert source
evidence; only the top-level candidate workflow is active here.

[source.json](source.json) records 237 files with source/local paths, commit,
byte lengths, modes and SHA-256 digests. `check_source.py` verifies the offline
baseline. With `--upstream`, it independently selects the owning git file set
and compares immutable blobs at the locked commit, detecting a file removed
from both the local payload and its manifest. No network is needed once the
owning commit is checked out.

```sh
python drafts/fht/check_source.py --upstream /path/to/exact-owning-checkout
python -m unittest discover -s drafts/fht -p 'test_candidate.py' -v
python drafts/fht/run_checks.py --upstream /path/to/exact-owning-checkout \
  --receipt /tmp/fht-reference.json
```

Install `upstream/requirements-linkml.txt` with Python 3.13 first. The 93-vector
checker, model regeneration and import/legacy checks execute on the vendored
candidate. All 114 unchanged tests execute in the parity-checked owning checkout:
its HTML reference verifies the actual last schema-changing commit in owning git
history. This avoids inventing a synthetic source revision or weakening that
provenance assertion. The runner repeats parity after execution and writes a
receipt only after every required command and exact count succeeds.

The separate installed lane requires a throwaway environment containing
`fair-bioheaders==0.11.0`:

```sh
python drafts/fht/run_checks.py --upstream /path/to/exact-owning-checkout \
  --toolkit-venv /tmp/fht-toolkit --receipt /tmp/fht-installed.json
```

The explicit overlay mutates that throwaway environment only. Actual installed
execution compares 91 cases, while `fht-fasta-completeness-sum-exceeds-total` and
`fht-fasta-completeness-sum-below-total` are explicitly unsupported arithmetic
checks. They remain normative invalid vectors and reference checks reject them.
The receipt says `consumerArithmeticAccepted: false`; it is never a full
consumer pass. The workflow uploads actual receipts and separately checks all
seven unchanged HTML pairs with Chromium.

David's D1–D3 disposition is recorded in the owning snapshot; final joint
acceptance is still pending. Retained historical decision agendas and pilot
files do not reopen settled questions or establish new release prerequisites.
