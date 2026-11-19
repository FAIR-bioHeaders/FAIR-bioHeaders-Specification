#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Record actual unittest result fields, independent of test stdout/stderr."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest


def execute(source, receipt):
    receipt = Path(receipt)
    receipt.unlink(missing_ok=True)
    # Never execute bytecode left in the owning worktree's cache. Point Python
    # at an empty cache root, and do not write any new cache during execution.
    with tempfile.TemporaryDirectory(prefix="fht-unit-cache-") as cache:
        old_prefix, old_write = sys.pycache_prefix, sys.dont_write_bytecode
        sys.pycache_prefix, sys.dont_write_bytecode = cache, True
        try:
            suite = unittest.defaultTestLoader.discover(str(Path(source) / "tests"))
            discovered = suite.countTestCases()
            result = unittest.TextTestRunner(verbosity=2).run(suite)
        finally:
            sys.pycache_prefix, sys.dont_write_bytecode = old_prefix, old_write
    data = {"discovered": discovered, "testsRun": result.testsRun,
            "skipped": len(result.skipped), "failures": len(result.failures),
            "errors": len(result.errors), "expectedFailures": len(result.expectedFailures),
            "unexpectedSuccesses": len(result.unexpectedSuccesses),
            "successful": result.wasSuccessful()}
    receipt.write_text(json.dumps(data, indent=2) + "\n")
    return data


def validate(data, expected):
    if data != {"discovered": expected, "testsRun": expected, "skipped": 0,
                "failures": 0, "errors": 0, "expectedFailures": 0,
                "unexpectedSuccesses": 0, "successful": True}:
        raise RuntimeError(f"actual unittest result differs from the reviewed suite: {data}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--expected", type=int, required=True)
    args = parser.parse_args()
    data = execute(args.source, args.receipt)
    validate(data, args.expected)


if __name__ == "__main__":
    main()
