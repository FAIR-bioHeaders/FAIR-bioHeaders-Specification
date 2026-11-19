"""Validate the synthetic examples in examples/ against the generated fht.json.

Each FASTA example must parse, validate with format checks, carry no raw ``>``
or ``@`` in header lines (shared FORMAT.md R11) and carry the SHA-512/256
checksum of its own bytes under FORMAT.md R3/R4. The JSON and YAML forms must
validate and match the FASTA header they serialize. These are synthetic
examples, not the byte-exact conformance vectors owned by #8.
"""

import base64
import hashlib
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
CHECKSUM_LINE = re.compile(rb"^;~checksum: ?[^\r\n]*(\r\n|\n|\r)?$")


def header(data):
    """Return the parsed ;~ header block of FASTA bytes."""
    lines = data.decode("utf-8").splitlines()
    block = [line[2:] for line in lines if line.startswith(";~")]
    return block, yaml.safe_load("\n".join(block))


def file_checksum(data):
    """SHA-512/256 of every byte except the root checksum line (R3/R4)."""
    kept = [
        line
        for line in data.splitlines(keepends=True)
        if not CHECKSUM_LINE.match(line)
    ]
    digest = hashlib.new("sha512_256", b"".join(kept)).digest()
    return base64.b64encode(digest).decode("ascii")


class ExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = json.loads((ROOT / "fht.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(schema, format_checker=FormatChecker())
        cls.fastas = sorted(EXAMPLES.glob("*.fht.fasta"))

    def assert_valid(self, record, name):
        errors = [error.message for error in self.validator.iter_errors(record)]
        self.assertEqual(errors, [], name)

    def test_examples_exist_for_each_construction_case(self):
        cases = set()
        for path in self.fastas:
            cases.add(header(path.read_bytes())[1]["assemblyType"])
        self.assertEqual(cases, {"de novo", "genome-guided", "annotation-derived"})

    def test_fasta_examples_validate_and_verify(self):
        for path in self.fastas:
            with self.subTest(path.name):
                data = path.read_bytes()
                block, record = header(data)
                self.assert_valid(record, path.name)
                for line in block:
                    self.assertNotIn(">", line)
                    self.assertNotIn("@", line)
                self.assertEqual(
                    sum(1 for line in data.splitlines() if CHECKSUM_LINE.match(line)),
                    1,
                )
                self.assertEqual(record["checksum"], file_checksum(data))

    def test_json_and_yaml_match_their_fasta(self):
        for stem in sorted({p.name.split(".")[0] for p in EXAMPLES.glob("*.fht.json")}):
            with self.subTest(stem):
                fasta = header((EXAMPLES / f"{stem}.fht.fasta").read_bytes())[1]
                as_json = json.loads(
                    (EXAMPLES / f"{stem}.fht.json").read_text(encoding="utf-8")
                )
                as_yaml = yaml.safe_load(
                    (EXAMPLES / f"{stem}.fht.yaml").read_text(encoding="utf-8")
                )
                self.assert_valid(as_json, f"{stem}.fht.json")
                self.assert_valid(as_yaml, f"{stem}.fht.yaml")
                self.assertEqual(as_json, fasta)
                self.assertEqual(as_yaml, fasta)


if __name__ == "__main__":
    unittest.main()
