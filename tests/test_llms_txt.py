"""llms.txt must stay in step with the released schemas (schemas/versions.json)."""

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILES = {"FHR": "fhr.json", "FHP": "fhp.json", "FHGFF3": "fhgff3.json"}


class LlmsTxtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / "llms.txt").read_text(encoding="utf-8")
        cls.versions = json.loads((ROOT / "schemas/versions.json").read_text(encoding="utf-8"))

    def test_llmstxt_layout(self):
        self.assertTrue(self.text.startswith("# FAIR-bioHeaders\n"))
        self.assertRegex(self.text, r"\n> \S")
        self.assertIn("\n## Optional\n", self.text)

    def test_current_release_and_schema_versions(self):
        current = self.versions["current"]
        for header, version in self.versions["releases"][current].items():
            with self.subTest(header=header):
                url = f"https://w3id.org/fair-bioheaders/{self.versions['w3id'][header]}/{current}"
                self.assertIn(url, self.text)
                self.assertIn(f"{header} `schemaVersion: '{version}'`" if header == "FHR"
                              else f"{header} `'{version}'`", self.text)

    def test_required_fields_named(self):
        named = set(re.findall(r"`([A-Za-z_]+)`", self.text))
        for header, file in FILES.items():
            required = json.loads((ROOT / file).read_text(encoding="utf-8"))["required"]
            with self.subTest(header=header):
                self.assertEqual(set(required) - named, set())


if __name__ == "__main__":
    unittest.main()
