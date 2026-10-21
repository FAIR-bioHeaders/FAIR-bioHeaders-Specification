# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Community profiles layered on a header type (issue #51, spec 008 FR-004).

The profile is a proposal: it adds requirements on top of the unchanged
published FHR contract without editing it. These tests check the mechanism, the
worked AgBioData example, and the conformance cases under
``profiles/examples/agbiodata-fhr/``.
"""

import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "profiles"))
sys.path.insert(0, str(ROOT / "scripts"))
import profile_schema as profiles  # noqa: E402
from check_linkml import constraints  # noqa: E402

PROFILE = "agbiodata-fhr"
EXAMPLES = ROOT / "profiles" / "examples" / PROFILE
# The properties the worked profile intentionally changes; every other FHR
# property must keep the published constraints exactly.
CHANGED = {"accessionID", "identifier"}


def load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


class ProfileMechanismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = profiles.load_registry()
        cls.published = json.loads((ROOT / "fhr.json").read_text(encoding="utf-8"))
        cls.generated = profiles.generate_profile(PROFILE)
        cls.validator = Draft202012Validator(cls.generated, format_checker=FormatChecker())
        cls.base = Draft202012Validator(cls.published, format_checker=FormatChecker())

    def test_registry_entry_is_a_draft_that_names_the_issue(self):
        entry = self.registry[PROFILE]
        self.assertEqual(entry["header_type"], "FHR")
        self.assertEqual(entry["status"], "draft")
        self.assertIn("issues/51", entry["issue"])
        self.assertIn("not consulted", entry["community"])
        self.assertNotIn(entry["status"], {"reviewed", "adopted"})

    def test_profile_model_imports_the_published_type_model(self):
        model = profiles.load_yaml(ROOT / "profiles" / "agbiodata-fhr.yaml")
        self.assertIn("fhr_linkml", model["imports"])
        self.assertEqual(model["classes"]["AgBioDataFHR"]["is_a"], "FHR")

    def test_unknown_profile_is_reported_not_silently_passed(self):
        with self.assertRaises(profiles.UnsupportedProfileError) as caught:
            profiles.resolve_profile("other-community-fhr")
        self.assertIn(PROFILE, str(caught.exception))

    def test_profile_schema_is_a_valid_draft_2020_12_schema(self):
        self.assertEqual(self.generated["$schema"], profiles.DIALECT)
        self.validator.check_schema(self.generated)
        self.assertIs(self.generated["additionalProperties"], False)

    def test_profile_layers_on_fhr_without_changing_base_constraints(self):
        profile = constraints(self.generated, self.generated)["properties"]
        published = constraints(self.published, self.published)["properties"]
        self.assertTrue(set(published) <= set(profile))
        for name in published:
            if name in CHANGED:
                continue
            with self.subTest(slot=name):
                self.assertEqual(profile[name], published[name])
        self.assertEqual(set(profile) - set(published), {"sampleIdentifier"})

    def test_profile_adds_required_accession_and_naming_rules(self):
        self.assertIn("accessionID", self.generated["required"])
        self.assertNotIn("accessionID", self.published["required"])
        # The profile does not relax any inherited required slot.
        self.assertTrue(set(self.published["required"]) <= set(self.generated["required"]))

        accession = self.generated["$defs"]["AgBioDataAssemblyAccession"]
        self.assertEqual(accession["required"], ["name"])
        patterns = [branch["pattern"] for branch in accession["properties"]["name"]["anyOf"]]
        self.assertEqual(
            patterns, [r"^GC[AF]_[0-9]{9}\.[0-9]+$", r"^[a-z][a-z0-9]*:[A-Za-z0-9._-]+$"]
        )
        self.assertEqual(
            self.generated["properties"]["identifier"]["items"]["pattern"],
            r"^[a-z][a-z0-9]*:[A-Za-z0-9._-]+$",
        )
        self.assertEqual(
            self.generated["properties"]["sampleIdentifier"]["items"]["pattern"],
            r"^[a-z][a-z0-9]*:[A-Za-z0-9._-]+$",
        )

    def test_profile_generation_is_deterministic(self):
        self.assertEqual(profiles.generate_profile(PROFILE), self.generated)


class ProfileConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = profiles.generate_profile(PROFILE)
        cls.validator = Draft202012Validator(cls.generated, format_checker=FormatChecker())
        cls.published = json.loads((ROOT / "fhr.json").read_text(encoding="utf-8"))
        cls.base = Draft202012Validator(cls.published, format_checker=FormatChecker())

    def test_profile_accepts_valid_instances(self):
        for name in ("valid.json", "valid-with-sample-identifiers.json"):
            with self.subTest(example=name):
                self.assertEqual(list(self.validator.iter_errors(load(name))), [])

    def test_profile_rejects_invalid_instances_naming_the_field(self):
        cases = {
            "invalid-missing-accession.json": "$",
            "invalid-accession-name.json": "$.accessionID.name",
            "invalid-identifier-name.json": "$.identifier[0]",
            "invalid-sample-identifier.json": "$.sampleIdentifier[0]",
        }
        for name, path in cases.items():
            with self.subTest(example=name):
                errors = list(self.validator.iter_errors(load(name)))
                self.assertTrue(errors, "profile accepted an invalid instance")
                self.assertIn(path, [error.json_path for error in errors])

    def test_base_valid_records_can_be_profile_invalid(self):
        """A record can satisfy the published contract but not the community one."""
        for name in (
            "invalid-missing-accession.json",
            "invalid-accession-name.json",
            "invalid-identifier-name.json",
            "unsupported-profile.json",
        ):
            with self.subTest(example=name):
                self.assertEqual(list(self.base.iter_errors(load(name))), [])
                self.assertNotEqual(list(self.validator.iter_errors(load(name))), [])

    def test_profile_only_field_is_outside_the_published_contract(self):
        """The extension boundary: a community field is not in the base contract."""
        instance = load("valid-with-sample-identifiers.json")
        self.assertEqual(list(self.validator.iter_errors(instance)), [])
        errors = list(self.base.iter_errors(instance))
        self.assertTrue(errors)
        self.assertTrue(any("Additional properties" in error.message for error in errors))
        self.assertNotIn("sampleIdentifier", self.published["properties"])
        self.assertNotIn("AgBioDataFHR", self.published.get("$defs", {}))

    def test_relaxed_case_needs_a_derived_schema_not_this_profile(self):
        """A relaxed profile cannot remove a base requirement (see docs/PROFILES.md)."""
        instance = load("relaxed-nucleotide-set.json")
        self.assertNotEqual(list(self.base.iter_errors(instance)), [])
        self.assertNotEqual(list(self.validator.iter_errors(instance)), [])
        for slot in ("genome", "assemblyAuthor", "masking"):
            with self.subTest(slot=slot):
                self.assertIn(slot, self.generated["required"])


if __name__ == "__main__":
    unittest.main()
