"""Wire the issue #14 CI scripts into the existing unittest lane.

The scripts are the authoritative implementations (they print the actionable
per-finding reports CI shows); these tests import and run their ``main()`` so
``python -m unittest discover -s tests`` — used locally and by
.github/workflows/validate-specification.yml — also covers documentation
hygiene, legacy-draft schema health and the classified legacy examples.

The external-link lane (scripts/check_external_links.py) is intentionally NOT
tested here: it needs the network and is scheduled/manual, never a PR signal.

Local usage (pinned environment; see docs/CI.md):

    python -m pip install -r requirements-validation.txt
    python -m unittest tests.test_ci_checks -v
"""

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CiCheckTests(unittest.TestCase):
    def test_fenced_code_closing_honors_delimiter(self):
        check_docs = load("check_docs")
        lines = [
            "````python",
            "```",
            "~~~~",
            "```` trailing info",
            "[example](missing.md)",
            "`````",
            "[outside](missing.md)",
        ]

        self.assertEqual(
            [in_code for _, _, in_code in check_docs.strip_fences(lines)],
            [True, True, True, True, True, True, False],
        )

    def test_url_exclusions_distinguish_exact_matches_from_prefixes(self):
        sys.path.insert(0, str(SCRIPTS))
        try:
            check_external_links = load("check_external_links")
        finally:
            sys.path.remove(str(SCRIPTS))
        exact = {"url": "https://example.test/issues/14"}
        prefix = {"prefix": "https://example.test/issues/"}

        self.assertIs(
            check_external_links.excluded(
                "https://example.test/issues/14", [exact]
            ),
            exact,
        )
        self.assertIsNone(
            check_external_links.excluded(
                "https://example.test/issues/140", [exact]
            )
        )
        self.assertIs(
            check_external_links.excluded(
                "https://example.test/issues/140", [prefix]
            ),
            prefix,
        )

    def test_historical_manifest_must_cover_disk_inventory(self):
        check_legacy_examples = load("check_legacy_examples")
        manifest = {"examples": [{"file": "legacy/examples/kept.json"}]}

        self.assertEqual(
            check_legacy_examples.inventory_findings(
                manifest, ["legacy/examples/kept.json"]
            ),
            {"unclassified": [], "missing": [], "duplicate": []},
        )
        self.assertEqual(
            check_legacy_examples.inventory_findings(
                manifest,
                ["legacy/examples/kept.json", "legacy/examples/new.json"],
            )["unclassified"],
            ["legacy/examples/new.json"],
        )
        self.assertEqual(
            check_legacy_examples.inventory_findings(
                {
                    "examples": [
                        {"file": "legacy/examples/kept.json"},
                        {"file": "legacy/examples/kept.json"},
                    ]
                },
                ["legacy/examples/kept.json"],
            )["duplicate"],
            ["legacy/examples/kept.json"],
        )

    def test_owned_documentation_checks_pass(self):
        with self.subTest("local links, whitespace and conflict markers"):
            self.assertEqual(load("check_docs").main([]), 0)

    def test_legacy_schema_health_passes(self):
        self.assertEqual(load("check_legacy_schema").main(), 0)

    def test_legacy_examples_and_fixtures_match_classification(self):
        self.assertEqual(load("check_legacy_examples").main(), 0)


if __name__ == "__main__":
    unittest.main()
