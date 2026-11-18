# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The generated CEDAR templates against CEDAR's own artifact meta-schemas.

tests/fixtures/cedar-meta-schemas/ holds byte-exact copies of the merged
Draft-04 meta-schemas from metadatacenter/cedar-model-validation-library (see
provenance.json there, and its licence notice). The walk mirrors that
library's CedarValidator: the template meta-schema for the template, then the
element, literal-field, IRI-field or static-field meta-schema for every
user-defined child at any depth (multi-instance children are checked through
their item). Runs offline.
"""
import hashlib
import json
import unittest

from jsonschema import Draft4Validator, FormatChecker

from test_cedar import ALL_STEMS, ROOT, load_template, make_cedar

META_DIR = ROOT / "tests" / "fixtures" / "cedar-meta-schemas"
PROVENANCE = json.loads((META_DIR / "provenance.json").read_text(encoding="utf-8"))
STATIC_FIELD = make_cedar.CEDAR + "StaticTemplateField"
# CedarValidator.IRI_INPUT_TYPES at the vendored commit.
IRI_INPUT_TYPES = {"controlled-term", "link", "ext-ror", "ext-orcid", "ext-pfas",
                   "ext-rrid", "ext-pubmed", "ext-nih-grant-id", "ext-doi"}


def meta_validator(kind):
    schema = json.loads((META_DIR / f"{kind}-meta-schema.json").read_text(encoding="utf-8"))
    Draft4Validator.check_schema(schema)
    return Draft4Validator(schema, format_checker=FormatChecker())


class CedarMetaSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validators = {kind: meta_validator(kind) for kind in (
            "template", "element", "literal-field", "iri-field", "static-field")}

    def errors(self, kind, node, where):
        return [f"{kind} meta-schema at {where}/{'/'.join(map(str, error.absolute_path))}: "
                f"{error.message}"
                for error in self.validators[kind].iter_errors(node)]

    def children(self, node, where):
        found = []
        for name, child in node.get("properties", {}).items():
            if not isinstance(child, dict):
                continue
            target = child["items"] if child.get("type") == "array" else child
            kind = target.get("@type") if isinstance(target, dict) else None
            path = f"{where}/{name}"
            if kind == make_cedar.CEDAR_ELEMENT:
                found += self.errors("element", target, path)
                found += self.children(target, path)
            elif kind == STATIC_FIELD:
                found += self.errors("static-field", target, path)
            elif kind == make_cedar.CEDAR_FIELD:
                iri = target.get("_ui", {}).get("inputType") in IRI_INPUT_TYPES
                found += self.errors("iri-field" if iri else "literal-field", target, path)
        return found

    def test_vendored_meta_schemas_match_their_provenance(self):
        self.assertEqual(PROVENANCE["commit"], "34e65d2571a37966e59d158695b6062d3ec47a55")
        on_disk = {path.name for path in META_DIR.iterdir()} - {"provenance.json"}
        self.assertEqual(on_disk, set(PROVENANCE["files"]))
        for name, entry in PROVENANCE["files"].items():
            digest = hashlib.sha256((META_DIR / name).read_bytes()).hexdigest()
            self.assertEqual(digest, entry["sha256"], f"{name}: vendored bytes changed")

    def test_every_generated_template_passes_the_cedar_meta_schemas(self):
        for stem in ALL_STEMS:
            with self.subTest(stem=stem):
                template = load_template(stem)
                found = self.errors("template", template, "") + self.children(template, "")
                self.assertEqual([], found)

    def test_the_meta_schemas_reject_an_unaliased_schema_prefixed_name(self):
        # The defect this guards: a contract key starting with "schema" fails
        # CEDAR's child-name pattern unless the form aliases it.
        template = load_template("fhr")
        alias = make_cedar.form_field_name("schemaVersion")
        self.assertNotEqual(alias, "schemaVersion")
        template["properties"]["schemaVersion"] = template["properties"].pop(alias)
        context = template["properties"]["@context"]["properties"]
        context["schemaVersion"] = context.pop(alias)
        self.assertTrue(self.errors("template", template, ""))

    def test_generator_refuses_reserved_form_names(self):
        for name in ("schemaFoo", "xsdThing", "pav", "a.b", "$ref"):
            with self.assertRaises(SystemExit):
                make_cedar.form_field_name(name)
        for contract in make_cedar.FORM_FIELD_ALIASES:
            self.assertEqual(make_cedar.contract_field_name(make_cedar.form_field_name(contract)),
                             contract)


if __name__ == "__main__":
    unittest.main()
