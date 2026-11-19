#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Run the pinned FHT candidate evidence and write an explicit machine receipt."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from unittest_receipt import validate as validate_unit_result

from check_source import COMMIT, ROOT, verify


def run(cwd, *args):
    with tempfile.TemporaryDirectory(prefix="fht-command-cache-") as cache:
        environment = dict(os.environ, PYTHONPYCACHEPREFIX=cache,
                           PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(list(args), cwd=cwd, text=True, env=environment,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end="", flush=True)
    if result.returncode:
        raise RuntimeError(f"candidate evidence command failed: {args}")
    return result.stdout


STAGED = ["fht-fasta-completeness-sum-exceeds-total",
          "fht-fasta-completeness-sum-below-total"]


def installed_receipt(output):
    required = ["toolkit: fair-bioheaders 0.11.0;",
                "verify (draft lane ON): 34 valid accepted, 57 invalid rejected",
                "verify-links (draft lane ON): 10 vectors with parentLink entries",
                "default path (draft lane OFF): 0 of 93 vectors accepted;",
                "strip: 34 valid vectors compared with the FORMAT.md rule text",
                "combine: 34 valid vectors round-tripped (values, order, verification)",
                "implementation comparisons: 91; current-contract unsupported/not-run: 2",
                "(0 finding(s) reported for #9)"]
    if not all(value in output for value in required):
        raise RuntimeError("installed evidence missing a required comparison layer/count")
    streams = re.search(r"streams \(stdin/stdout, draft lane ON\): (\{.*\})", output)
    if not streams or ast.literal_eval(streams.group(1)) != {"verify": 91, "strip": 34, "combine": 34}:
        raise RuntimeError("installed stream evidence differs")
    staged = re.search(r"staged C1 arithmetic NOT-RUN by installed runtime: 2 (\[.*\])", output)
    if not staged or ast.literal_eval(staged.group(1)) != STAGED:
        raise RuntimeError("installed arithmetic limitations are not the two reviewed cases")
    return {"lane": "installed-overlay", "compared": 91, "notRun": STAGED,
            "consumerArithmeticAccepted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--toolkit-venv", type=Path,
                        help="throwaway fair-bioheaders 0.11.0 environment; overlay changes it")
    args = parser.parse_args()
    # Never leave a stale success receipt when a later run fails.
    args.receipt.unlink(missing_ok=True)
    source = args.upstream.resolve()
    verify(upstream=source)
    candidate = ROOT / "upstream"
    if args.toolkit_venv:
        output = run(source, sys.executable, "scripts/run_toolkit_lane.py",
                     "--venv", str(args.toolkit_venv.resolve()),
                     "--checkout-contract", "--strict", "--stage-completeness")
        receipt = installed_receipt(output)
    else:
        output = run(candidate, sys.executable, "scripts/check_fht_fixtures.py")
        if "checked 34 valid and 59 invalid vectors" not in output:
            raise RuntimeError("fixture evidence lacks the accepted 93-vector accounting")
        run(candidate, sys.executable, "json-schema-generator.py")
        verify(upstream=source)  # Regeneration must preserve exact source bytes.
        run(candidate, sys.executable, "scripts/check_provenance.py")
        run(candidate, sys.executable, "scripts/check_legacy_schema.py")
        run(candidate, sys.executable, "scripts/check_legacy_examples.py")
        # The unchanged owning reference verifies its last schema-changing git
        # commit. Run those exact byte-parity-checked tests with owning history,
        # rather than invent a synthetic commit in this shared repository.
        expected_units = json.loads((ROOT / "source.json").read_text())["expectedEvidence"]["unitTests"]
        with tempfile.TemporaryDirectory(prefix="fht-unit-result-") as work:
            unit_result = Path(work) / "result.json"
            run(source, sys.executable, "-I", str(ROOT / "unittest_receipt.py"),
                "--source", str(source), "--receipt", str(unit_result),
                "--expected", str(expected_units))
            actual_units = json.loads(unit_result.read_text())
            validate_unit_result(actual_units, expected_units)
        receipt = {"lane": "candidate-reference", "vectors": 93,
                   "valid": 34, "invalid": 59, "owningUnitTests": actual_units["testsRun"], "unitResult": actual_units,
                   "unitExecution": "exact owning checkout with required provenance history",
                   "consumerArithmeticAccepted": False}
    verify(upstream=source)
    if subprocess.check_output(["git", "-C", str(source), "diff", "--name-only", "HEAD"]):
        raise RuntimeError("owning checkout changed during evidence execution")
    receipt.update(sourceCommit=COMMIT, status="passed-prepublication-evidence",
                   schemaSha256=hashlib.sha256((candidate / "fht.json").read_bytes()).hexdigest(),
                   released=False, jointAcceptance="pending recorded final review")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
