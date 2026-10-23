# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Every declared ``format`` is asserted by a conforming validator (#150, #163).

Draft 2020-12 treats ``format`` as an annotation unless the validator opts in.
The schemas use it for dates and URIs, so a validator that ignores it accepts
malformed values. These tests pin both halves: the format is declared, and a
validator with ``FormatChecker`` rejects malformed values while a bare
validator does not.
"""

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ("fhr.json", "fhp.json", "fhgff3.json")
INVALID = {"date": "2022-13-45", "uri": "http://["}
VALID = {"date": "2026-10-22", "uri": "https://example.org/resource"}


def format_nodes(schema, path=""):
    """Yield ``(path, node)`` for every schema object that declares a format."""
    if isinstance(schema, dict):
        if isinstance(schema.get("format"), str):
            yield path or "/", schema
        for key, value in schema.items():
            yield from format_nodes(value, f"{path}/{key}")
    elif isinstance(schema, list):
        for index, value in enumerate(schema):
            yield from format_nodes(value, f"{path}/{index}")


class FormatAssertionTests(unittest.TestCase):
    def test_every_declared_format_has_a_checker(self):
        declared = set()
        for name in SCHEMAS:
            schema = json.loads((ROOT / name).read_text(encoding="utf-8"))
            for path, node in format_nodes(schema):
                declared.add(node["format"])
                with self.subTest(schema=name, path=path):
                    self.assertIn(node["format"], FormatChecker.checkers)
        self.assertEqual(declared, set(INVALID))

    def test_malformed_format_values_are_rejected_when_format_is_asserted(self):
        checked = 0
        for name in SCHEMAS:
            schema = json.loads((ROOT / name).read_text(encoding="utf-8"))
            for path, node in format_nodes(schema):
                fmt = node["format"]
                if fmt not in INVALID or "pattern" in node:
                    continue  # Pattern-bearing fields already constrain the value.
                checked += 1
                with self.subTest(schema=name, path=path, format=fmt):
                    asserting = Draft202012Validator(
                        node, format_checker=FormatChecker()
                    )
                    self.assertFalse(asserting.is_valid(INVALID[fmt]))
                    self.assertTrue(asserting.is_valid(VALID[fmt]))
                    # Without a format checker this is accepted, which is why
                    # the normative text requires validators to assert format.
                    self.assertTrue(Draft202012Validator(node).is_valid(INVALID[fmt]))
        self.assertGreater(checked, 0)

    def test_declared_formats_are_only_date_and_uri(self):
        formats = set()
        for name in SCHEMAS:
            schema = json.loads((ROOT / name).read_text(encoding="utf-8"))
            formats.update(node["format"] for _, node in format_nodes(schema))
        self.assertEqual(formats, {"date", "uri"})
