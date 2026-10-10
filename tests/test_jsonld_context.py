# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The generated JSON-LD context (feature 011, data-model sections 1 and 2)."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_PATH = ROOT / "jsonld" / "fhr.context.jsonld"
SDO = "http://schema.org/"
FHR = "https://w3id.org/fair-bioheaders/terms#"
XSD = "http://www.w3.org/2001/XMLSchema#"
DCT = "http://purl.org/dc/terms/"
# Scope name -> the fhr.json path whose object properties are the scope's keys.
NESTED = {
    "taxon": ("taxon",),
    "metadataAuthor": ("metadataAuthor", "[]"),
    "assemblyAuthor": ("assemblyAuthor", "[]"),
    "accessionID": ("accessionID",),
    "vitalStats": ("vitalStats",),
    "assemblySoftware": ("assemblySoftware", "[]"),
}
COUNTS = {"record": 24, "taxon": 2, "metadataAuthor": 3, "assemblyAuthor": 3,
          "accessionID": 2, "vitalStats": 13, "assemblySoftware": 4}
# Root terms that are not FHR keys: the documentation-as-URL term (maintainer
# decision 3) and the export-context terms (maintainer decision 2).
EXPORT_TERMS = {
    "subjectOf": {"@id": "sdo:subjectOf", "@type": "@id"},
    "keywords": {"@id": "sdo:keywords", "@container": "@set"},
    "url": {"@id": "sdo:url", "@type": "@id"},
    "conformsTo": {"@id": "dct:conformsTo", "@type": "@id"},
}


def resolve(node, document):
    """Follow local $ref pointers."""
    while isinstance(node, dict) and "$ref" in node:
        target = document
        for part in node["$ref"][2:].split("/"):
            target = target[part]
        node = {**target, **{k: v for k, v in node.items() if k != "$ref"}}
    return node


def object_properties(node, document):
    """Property names of an object schema, looking through items and anyOf."""
    node = resolve(node, document)
    if "properties" in node:
        return list(node["properties"])
    if "items" in node:
        return object_properties(node["items"], document)
    for option in node.get("anyOf", []):
        names = object_properties(option, document)
        if names:
            return names
    return []


def expand(value, scope):
    """Expand a CURIE or term definition @id against the prefixes of ``scope``."""
    if isinstance(value, dict):
        value = value["@id"]
    if value.startswith("@") or "://" in value:
        return value
    prefix, _, local = value.partition(":")
    return scope[prefix] + local


class ContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "fhr.json").read_text())
        cls.document = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
        cls.root = cls.document["@context"]
        cls.scopes = {"record": cls.root}
        for name in NESTED:
            cls.scopes[name] = cls.root[name]["@context"][1]
        cls.keys = {"record": list(cls.schema["properties"])}
        for name, path in NESTED.items():
            cls.keys[name] = object_properties(cls.schema["properties"][path[0]], cls.schema)

    def test_generated_files_are_current(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/make_jsonld.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_linkml_still_matches_fhr_json(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/check_linkml.py")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_header_prefixes_and_no_vocab(self):
        self.assertEqual(list(self.document), ["@context"])
        self.assertEqual(self.root["@version"], 1.1)
        self.assertIs(self.root["@protected"], True)
        self.assertEqual(self.root["sdo"], SDO)
        self.assertEqual(self.root["fhr"], FHR)
        self.assertEqual(self.root["xsd"], XSD)
        self.assertEqual(self.root["dct"], DCT)
        for name, scope in self.scopes.items():
            with self.subTest(scope=name):
                self.assertNotIn("@vocab", scope)
                self.assertNotIn("@base", scope)
                if name != "record":
                    self.assertNotIn("schema", scope)
        self.assertIsInstance(self.root["schema"], dict)  # A term, never a prefix.

    def test_every_fhr_key_is_a_term_in_its_scope(self):
        for name, count in COUNTS.items():
            with self.subTest(scope=name):
                self.assertEqual(len(self.keys[name]), count)
                for key in self.keys[name]:
                    self.assertIn(key, self.scopes[name])

    def test_terms_follow_fhr_json_order(self):
        for name, scope in self.scopes.items():
            with self.subTest(scope=name):
                terms = [key for key in scope if key in self.keys[name]]
                self.assertEqual(terms, self.keys[name])

    def test_only_documented_extra_terms(self):
        """Besides FHR keys a scope has only prefixes, type terms and, at the root,
        the export terms."""
        allowed = {"@version", "@protected", "sdo", "fhr", "xsd", "dct"}
        types = {
            "record": {"Dataset"}, "taxon": {"Taxon"},
            "metadataAuthor": {"Person", "Organization", "Agent"},
            "assemblyAuthor": {"Person", "Organization", "Agent"},
            "accessionID": {"PropertyValue"}, "vitalStats": {"VitalStats"},
            "assemblySoftware": {"SoftwareApplication"},
        }
        for name, scope in self.scopes.items():
            with self.subTest(scope=name):
                extra = set(scope) - set(self.keys[name]) - allowed
                expected = types[name] | (set(EXPORT_TERMS) if name == "record" else set())
                self.assertEqual(extra, expected)
                for term in types[name]:
                    self.assertIsInstance(scope[term], str)
        for term, definition in EXPORT_TERMS.items():
            self.assertEqual(self.root[term], definition)
        self.assertEqual(self.root["Dataset"], "sdo:Dataset")
        self.assertEqual(self.scopes["metadataAuthor"]["Person"], "sdo:Person")
        self.assertEqual(self.scopes["metadataAuthor"]["Organization"], "sdo:Organization")
        self.assertEqual(self.scopes["metadataAuthor"]["Agent"], "fhr:Agent")

    def test_nested_scopes_reset_and_protect(self):
        for name in NESTED:
            with self.subTest(scope=name):
                value = self.root[name]["@context"]
                self.assertIsInstance(value, list)
                self.assertEqual(len(value), 2)
                self.assertIsNone(value[0])
                self.assertIs(value[1]["@protected"], True)
                self.assertEqual(value[1]["sdo"], SDO)
                self.assertEqual(value[1]["fhr"], FHR)
        self.assertEqual(self.root["metadataAuthor"]["@context"],
                         self.root["assemblyAuthor"]["@context"])

    def test_injective_per_scope(self):
        for name, scope in self.scopes.items():
            with self.subTest(scope=name):
                seen = {}
                for key, value in scope.items():
                    if key.startswith("@") or key in {"sdo", "fhr", "xsd", "dct"}:
                        continue
                    iri = expand(value, {**self.root, **scope})
                    self.assertNotIn(iri, seen, f"{key} and {seen.get(iri)} share {iri}")
                    seen[iri] = key

    def test_coercions_and_containers(self):
        iri_typed = {("record", "schema"), ("record", "relatedLink"),
                     ("record", "assemblyProtocol"), ("accessionID", "url"),
                     ("assemblySoftware", "uri")}
        sets = {"genomeSynonym", "metadataAuthor", "assemblyAuthor", "instrument",
                "identifier", "relatedLink", "assemblySoftware"}
        for name in self.scopes:
            for key in self.keys[name]:
                definition = self.scopes[name][key]
                with self.subTest(scope=name, key=key):
                    if isinstance(definition, str):
                        self.assertEqual(definition, "@id")
                        self.assertIn((name, key), {("taxon", "uri"), ("metadataAuthor", "uri"),
                                                    ("assemblyAuthor", "uri")})
                        continue
                    kind = definition.get("@type")
                    if (name, key) in iri_typed:
                        self.assertEqual(kind, "@id")
                    elif (name, key) == ("record", "dateCreated"):
                        self.assertEqual(kind, "xsd:date")
                    else:
                        self.assertIsNone(kind)
                    container = definition.get("@container")
                    if (name, key) == ("assemblySoftware", "commandLineOption"):
                        self.assertEqual(container, "@list")
                    elif name == "record" and key in sets:
                        self.assertEqual(container, "@set")
                    else:
                        self.assertIsNone(container)

    def test_term_iris(self):
        sdo = {"schema": "schemaVersion", "genome": "name", "genomeSynonym": "alternateName",
               "taxon": "about", "version": "version", "assemblyAuthor": "creator",
               "dateCreated": "dateCreated", "scholarlyArticle": "citation",
               "documentation": "description", "identifier": "identifier",
               "funding": "funding", "reuseConditions": "license"}
        for key in self.keys["record"]:
            with self.subTest(key=key):
                iri = expand(self.root[key], self.root)
                self.assertEqual(iri, SDO + sdo[key] if key in sdo else FHR + key)
        nested = {("taxon", "name"): SDO + "name", ("accessionID", "name"): SDO + "name",
                  ("accessionID", "url"): SDO + "url", ("metadataAuthor", "name"): SDO + "name",
                  ("assemblySoftware", "name"): SDO + "name",
                  ("assemblySoftware", "uri"): SDO + "url",
                  ("assemblySoftware", "version"): SDO + "softwareVersion",
                  ("assemblySoftware", "commandLineOption"): FHR + "commandLineOption"}
        for (name, key), iri in nested.items():
            with self.subTest(scope=name, key=key):
                self.assertEqual(expand(self.scopes[name][key], self.scopes[name]), iri)
        for key in self.keys["vitalStats"]:
            self.assertEqual(expand(self.scopes["vitalStats"][key], self.scopes["vitalStats"]),
                             FHR + key)

    def test_serialisation(self):
        text = CONTEXT_PATH.read_text(encoding="utf-8")
        self.assertEqual(text, json.dumps(self.document, indent=2) + "\n")


if __name__ == "__main__":
    unittest.main()
