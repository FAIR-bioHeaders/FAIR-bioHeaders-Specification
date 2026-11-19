"""Validate the scripts/check_fht_fixtures.py runner inside unittest discovery.

The runner is the authoritative implementation (it prints the actionable
per-vector report CI shows); this test imports and runs its ``main()`` so
``python -m unittest discover -s tests`` — used locally and by
.github/workflows/validate-specification.yml — also covers the #8 fixture
lanes: regeneration determinism, the independent R1-R5 checksum reader, the
strict header-text rules, fht.json contract validation, V1/V5 schema
selection (with the V7 draft-lane note), C3 parent-link outcomes and the
examples recomputation.

See conformance/README.md for what these vectors do and do not prove (no
installed-toolkit round trips; that is #9 after a release).

Local usage (pinned environment; see docs/CI.md):

    python -m pip install -r requirements-validation.txt
    python -m unittest tests.test_fixtures -v
"""

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixtureTests(unittest.TestCase):
    def test_conformance_vectors_and_examples(self):
        check_fht_fixtures = load("check_fht_fixtures")
        self.assertEqual(check_fht_fixtures.main([]), 0)


if __name__ == "__main__":
    unittest.main()
