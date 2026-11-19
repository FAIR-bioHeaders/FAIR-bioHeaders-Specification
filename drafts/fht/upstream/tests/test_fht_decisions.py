# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""D1/D2/D3 dispositions: schema boundaries and cross-field C1 evidence."""

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from fht_semantics import completeness_errors  # noqa: E402
from test_fht_schema import minimal  # noqa: E402


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads((ROOT / "fht.json").read_text())
        self.validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        self.parent = {"headerType": "FHR", "relationship": "transcribedFrom",
                       "checksum": "A" * 43 + "="}
        self.counts = {"lineageDataset": "insecta_odb10", "completeSingle": 2,
                       "completeDuplicated": 1, "fragmented": 0, "missing": 1,
                       "total": 4}

    def test_retained_empty_parent_accession_object(self):
        record = minimal()
        record["derivedFrom"] = [dict(self.parent, accessionID={})]
        self.assertTrue(self.validator.is_valid(record))

    def test_duplicate_equality_ignores_object_key_order(self):
        record = minimal()
        record["derivedFrom"] = [self.parent, dict(reversed(list(self.parent.items())))]
        self.assertEqual({e.validator for e in self.validator.iter_errors(record)}, {"uniqueItems"})
        record["derivedFrom"][1]["accessionID"] = {"name": "supplied extra context"}
        self.assertEqual(list(self.validator.iter_errors(record)), [])

    def test_parent_checksum_final_bits_are_canonical_in_both_root_shapes(self):
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        for candidate in alphabet:
            record = minimal()
            record["derivedFrom"] = [dict(self.parent, checksum="A" * 42 + candidate + "=")]
            want = candidate in "AEIMQUYcgkosw048"
            self.assertEqual(self.validator.is_valid(record), want, candidate)
            nested = copy.deepcopy(self.schema)
            nested["$ref"] = "#/$defs/FHT"
            self.assertEqual(Draft202012Validator(nested).is_valid(record), want, candidate)
        record["derivedFrom"] = [dict(self.parent, checksum="A" * 43 + "=\n")]
        self.assertFalse(self.validator.is_valid(record))

    def test_complete_count_sets_compare_both_directions_and_preserve_zero(self):
        record = minimal()
        record["completeness"] = self.counts
        self.assertEqual(completeness_errors(record), [])
        for total in (3, 5):
            value = copy.deepcopy(record)
            value["completeness"]["total"] = total
            self.assertTrue(self.validator.is_valid(value), "arithmetic is outside JSON Schema")
            self.assertEqual(len(completeness_errors(value)), 1)
        for omitted in ("completeSingle", "completeDuplicated", "fragmented", "missing", "total"):
            value = copy.deepcopy(record)
            del value["completeness"][omitted]
            self.assertEqual(completeness_errors(value), [], "missing is not zero")
            self.assertFalse(self.validator.is_valid(value), "existing requiredness is unchanged")
        record["completeness"]["completeSingle"] = True
        self.assertEqual(completeness_errors(record), [], "bool is not an integer count")
        self.assertFalse(self.validator.is_valid(record))

    def test_mathematical_integer_counts_cannot_bypass_arithmetic(self):
        record = minimal()
        record["completeness"] = {k: float(v) if type(v) is int else v
                                  for k, v in self.counts.items()}
        self.assertTrue(self.validator.is_valid(record))
        self.assertEqual(completeness_errors(record), [])
        record["completeness"]["total"] = 5.0
        self.assertTrue(self.validator.is_valid(record))
        self.assertEqual(len(completeness_errors(record)), 1)
        record["completeness"].update(completeSingle=float(2**53),
                                      completeDuplicated=1, fragmented=0,
                                      missing=0, total=float(2**53))
        self.assertTrue(self.validator.is_valid(record))
        self.assertEqual(len(completeness_errors(record)), 1,
                         "count summation must not round through float")
        for invalid in (True, 2.5, float("inf"), float("nan")):
            record["completeness"]["total"] = invalid
            self.assertEqual(completeness_errors(record), [])

    def test_html_reference_checks_arithmetic_on_write_and_read(self):
        import fht_microdata as html
        record = minimal()
        record["completeness"] = self.counts
        page = html.write_page(record, allow_draft=True, warn=lambda _: None)
        self.assertEqual(html.read_page(page, allow_draft=True, warn=lambda _: None), record)
        record["completeness"]["total"] = 5
        with self.assertRaisesRegex(html.MicrodataError, "C1: completeness"):
            html.write_page(record, allow_draft=True, warn=lambda _: None)
        with patch.object(html, "completeness_errors", return_value=[]):
            invalid = html.write_page(record, allow_draft=True, warn=lambda _: None)
        with self.assertRaisesRegex(html.MicrodataError, "C1: completeness"):
            html.read_page(invalid, allow_draft=True, warn=lambda _: None)

    def test_promoted_cases_have_explicit_file_identity_acceptance(self):
        manifest = json.loads((ROOT / "conformance/manifest.json").read_text())
        self.assertNotIn("promotionCandidates", manifest)
        self.assertFalse(any(v.get("promotion") for v in manifest["vectors"]))
        review = next(r for r in manifest["expectationReviews"] if r["decisionId"] == "D3")
        self.assertEqual(review["status"], "accepted-file-identity-only")
        self.assertEqual(len(review["vectors"]), 4)
        self.assertIn("no biological derivation", review["limitation"])
