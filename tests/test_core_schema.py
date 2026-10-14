"""The shared LinkML core can be imported by future header types (spec 004)."""

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_linkml import constraints

spec = importlib.util.spec_from_file_location(
    "generator", ROOT / "json-schema-generator.py"
)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

CORE_REQUIRED = [
    "schema", "schemaVersion", "taxon", "version", "metadataAuthor",
    "dateCreated", "checksum",
]
CORE_OPTIONAL = [
    "identifier", "accessionID", "scholarlyArticle", "documentation",
    "relatedLink", "funding", "reuseConditions", "voucherSpecimen",
]
FHR_ONLY = [
    "genome", "genomeSynonym", "assemblyAuthor", "instrument", "masking",
    "vitalStats", "assemblySoftware", "assemblyProtocol", "seqcol_id",
]
CHECKSUM = "A" * 43 + "="


class CoreSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.published = json.loads((ROOT / "fhr.json").read_text())
        cls.fhr = generator.generate()
        cls.stub = generator.generate_from(ROOT / "tests/fixtures/fhp_stub.yaml")
        cls.validator = Draft202012Validator(cls.stub, format_checker=FormatChecker())
        example = json.loads((ROOT / "examples/example.fhr.json").read_text())
        cls.instance = {key: example[key] for key in CORE_REQUIRED}
        cls.instance["proteome"] = "Example proteome"
        cls.instance["derivedFrom"] = [{
            "headerType": "FHR",
            "checksum": CHECKSUM,
            "seqcol_id": "a" * 32,
            "accessionID": {"name": "GCA_000001405.29"},
            "relationship": "translatedFrom",
        }]

    def test_stub_has_core_slots_and_derived_from(self):
        properties = set(self.stub["properties"])
        self.assertEqual(
            properties, set(CORE_REQUIRED + CORE_OPTIONAL + ["proteome", "derivedFrom"])
        )
        self.assertEqual(set(self.stub["required"]), set(CORE_REQUIRED + ["proteome"]))
        self.assertFalse(properties & set(FHR_ONLY))
        self.assertIn("DerivedFrom", self.stub["$defs"])

    def test_core_slots_keep_published_fhr_constraints(self):
        stub = constraints(self.stub, self.stub)["properties"]
        published = constraints(self.published, self.published)["properties"]
        for name in CORE_REQUIRED + CORE_OPTIONAL:
            with self.subTest(slot=name):
                expected = dict(published[name])
                if name == "schemaVersion":
                    # The core gives the "MAJOR.MINOR" form; each header type pins its
                    # accepted values (docs/SCHEMA-VERSIONS.md).
                    self.assertEqual(expected.pop("enum"), ["2.0"])
                self.assertEqual(stub[name], expected)

    def test_fhr_contract_has_no_derived_from(self):
        self.assertNotIn("derivedFrom", self.fhr["properties"])
        self.assertNotIn("derivedFrom", self.published["properties"])

    def test_derived_from_valid_and_invalid(self):
        self.validator.check_schema(self.stub)
        self.validator.validate(self.instance)
        minimal = copy.deepcopy(self.instance)
        minimal["derivedFrom"] = [
            {"headerType": "FHGFF3", "checksum": CHECKSUM, "relationship": "annotates"}
        ]
        self.validator.validate(minimal)
        for key, value in [
            ("headerType", "FHX"),
            ("relationship", "derivedFrom"),
            ("checksum", "A" * 43 + "\n"),
            ("seqcol_id", "a" * 32 + "\n"),
            ("unknownField", "x"),
        ]:
            with self.subTest(key=key):
                instance = copy.deepcopy(self.instance)
                instance["derivedFrom"][0][key] = value
                self.assertFalse(self.validator.is_valid(instance))
        for key in ("headerType", "checksum", "relationship"):
            with self.subTest(missing=key):
                instance = copy.deepcopy(self.instance)
                del instance["derivedFrom"][0][key]
                self.assertFalse(self.validator.is_valid(instance))


if __name__ == "__main__":
    unittest.main()
