# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Community profiles layered on a header type (issue #51, spec 008 FR-004).

The profile is a proposal: it adds requirements on top of the unchanged
published FHR contract without editing it. These tests check the mechanism, the
worked AgBioData example, and the conformance cases under
``profiles/examples/agbiodata-fhr/``.
"""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "profiles"))
sys.path.insert(0, str(ROOT / "scripts"))
import profile_schema as profiles  # noqa: E402
from check_linkml import constraints  # noqa: E402

PROFILE = "agbiodata-fhr"
EXAMPLES = ROOT / "profiles" / "examples" / PROFILE
FHGFF3_PROFILE = ROOT / "tests" / "fixtures" / "fhgff3-profile.yaml"
FHP_PROFILE = ROOT / "tests" / "fixtures" / "fhp-profile.yaml"
FHGFF3_EXAMPLE = ROOT / "examples" / "fhgff3" / "minimal-reference.fhgff3.json"
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


class OtherTypeProfileTests(unittest.TestCase):
    """A profile on FHP or FHGFF3 keeps that type's post-generated constraints.

    FHGFF3 adds its genome-link rule after LinkML generation. A profile root that
    subclasses FHGFF3 must receive the same rule, or the profile silently accepts
    records the base contract rejects (issue #51 review).
    """

    @classmethod
    def setUpClass(cls):
        cls.fhgff3 = profiles.generate_profile(FHGFF3_PROFILE)
        cls.fhp = profiles.generate_profile(FHP_PROFILE)
        cls.published_fhgff3 = json.loads(
            (ROOT / "fhgff3.json").read_text(encoding="utf-8")
        )
        cls.published_fhp = json.loads((ROOT / "fhp.json").read_text(encoding="utf-8"))
        cls.fhgff3_validator = Draft202012Validator(
            cls.fhgff3, format_checker=FormatChecker()
        )
        cls.fhgff3_base = Draft202012Validator(
            cls.published_fhgff3, format_checker=FormatChecker()
        )
        cls.instance = json.loads(FHGFF3_EXAMPLE.read_text(encoding="utf-8"))

    def record(self, relationship="annotates", header_type="FHR"):
        instance = copy.deepcopy(self.instance)
        instance.pop("genomeReference", None)
        instance["derivedFrom"] = [
            {
                "headerType": header_type,
                "checksum": "A" * 43 + "=",
                "relationship": relationship,
            }
        ]
        return instance

    def test_fhgff3_profile_keeps_the_post_generated_genome_link_rule(self):
        self.assertEqual(self.fhgff3["anyOf"], self.published_fhgff3["anyOf"])
        self.assertEqual(self.fhgff3["allOf"], self.published_fhgff3["allOf"])
        self.assertIn("AnnotatesGenome", self.fhgff3["$defs"])
        self.assertIn("AnnotatesAny", self.fhgff3["$defs"])
        # The whole published constraint set survives, not only the added rule.
        self.assertEqual(
            constraints(self.fhgff3, self.fhgff3),
            constraints(self.published_fhgff3, self.published_fhgff3),
        )

    def test_fhp_profile_keeps_published_constraints(self):
        # FHP has no type-specific post-generation rules; this audit pins that
        # a profile inherits the entire published FHP contract.
        self.assertEqual(
            constraints(self.fhp, self.fhp),
            constraints(self.published_fhp, self.published_fhp),
        )

    def test_fhgff3_profile_rejects_a_record_without_a_genome_link(self):
        instance = copy.deepcopy(self.instance)
        del instance["genomeReference"]
        self.assertTrue(list(self.fhgff3_base.iter_errors(instance)))
        self.assertTrue(list(self.fhgff3_validator.iter_errors(instance)))

    def test_fhgff3_profile_accepts_one_annotates_parent(self):
        instance = self.record()
        self.assertEqual(list(self.fhgff3_base.iter_errors(instance)), [])
        self.assertEqual(list(self.fhgff3_validator.iter_errors(instance)), [])

    def test_fhgff3_profile_rejects_multiple_annotates_parents(self):
        instance = self.record()
        instance["derivedFrom"] = [self.record()["derivedFrom"][0]] * 2
        self.assertTrue(list(self.fhgff3_base.iter_errors(instance)))
        self.assertTrue(list(self.fhgff3_validator.iter_errors(instance)))

    def test_fhgff3_profile_rejects_an_annotates_parent_that_is_not_fhr(self):
        instance = self.record(header_type="FHP")
        self.assertTrue(list(self.fhgff3_base.iter_errors(instance)))
        self.assertTrue(list(self.fhgff3_validator.iter_errors(instance)))

    def test_profile_without_a_published_header_type_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "orphan-profile.yaml"
            path.write_text(
                "id: https://example.org/orphan\n"
                "name: OrphanProfile\n"
                "prefixes:\n  linkml: https://w3id.org/linkml/\n"
                "default_range: string\n"
                "imports:\n- linkml:types\n"
                "classes:\n  Orphan:\n    tree_root: true\n",
                encoding="utf-8",
            )
            with self.assertRaises(profiles.UnsupportedProfileError) as caught:
                profiles.generate_profile(path)
        self.assertIn("published header type", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
