"""Exercise the CI command against valid and invalid documents."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ValidationCommandTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.schema = self.root / "schema.json"
        self.schema.write_text((ROOT / "fhr.json").read_text())
        self.examples = self.root / "examples"
        self.examples.mkdir()
        self.instance = json.loads((ROOT / "examples/example.fhr.json").read_text())

    def write_instance(self, suffix="json"):
        path = self.examples / f"fixture.{suffix}"
        text = json.dumps(self.instance) if suffix == "json" else yaml.safe_dump(self.instance)
        path.write_text(text)

    def run_command(self):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_examples.py"),
             "--schema", str(self.schema), "--examples", str(self.examples)],
            cwd=self.root, capture_output=True, text=True,
        )

    def test_valid_json_and_yaml(self):
        self.write_instance()
        self.write_instance("yaml")
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fixture.json: valid", result.stdout)
        self.assertIn("fixture.yaml: valid", result.stdout)

    def test_invalid_formats_report_both_fields(self):
        self.instance["dateCreated"] = "2026-02-30"
        self.instance["relatedLink"] = ["not a URI"]
        self.write_instance("yaml")
        result = self.run_command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("fixture.yaml: $.dateCreated:", result.stderr)
        self.assertIn("$.relatedLink[0]:", result.stderr)

    def test_missing_required_and_unexpected_fields(self):
        del self.instance["genome"]
        self.instance["unexpected"] = "value"
        self.write_instance()
        result = self.run_command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("'genome' is a required property", result.stderr)
        # With extension fields (R15) jsonschema names the unknown key and the pattern.
        self.assertIn("'unexpected' does not match any of the regexes", result.stderr)

    def test_invalid_schema(self):
        schema = json.loads(self.schema.read_text())
        schema["type"] = "invalid-type"
        self.schema.write_text(json.dumps(schema))
        result = self.run_command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("schema.json: invalid schema:", result.stderr)

    def test_wrong_dialect(self):
        self.schema.write_text('{"$schema": "https://json-schema.org/draft-07/schema#"}')
        result = self.run_command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("expected $schema:", result.stderr)

    def test_parse_errors_do_not_hide_other_failures(self):
        (self.examples / "broken.json").write_text("{")
        (self.examples / "broken.yaml").write_text("genome: [")
        self.instance["checksum"] = "md5:invalid"
        self.write_instance()
        result = self.run_command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("broken.json: parse error:", result.stderr)
        self.assertIn("broken.yaml: parse error:", result.stderr)
        self.assertIn("fixture.json: $.checksum:", result.stderr)

    def test_empty_examples_fail(self):
        result = self.run_command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("no JSON/YAML examples found", result.stderr)


if __name__ == "__main__":
    unittest.main()
