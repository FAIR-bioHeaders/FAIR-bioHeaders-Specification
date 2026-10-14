# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The JSON-LD and DCMI mapping table (feature 011, FR-003, SC-002)."""

from collections import Counter
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDFS
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import make_jsonld  # noqa: E402

TABLE = ROOT / "mappings" / "fhr-jsonld-dcmi.yml"
SCHEMA = ROOT / "mappings" / "mapping-table.schema.json"
SDO = "http://schema.org/"
FHR = "https://w3id.org/fair-bioheaders/terms#"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
RECORD_PATHS = {"schema", "metadataAuthor[]", "metadataAuthor[].name", "metadataAuthor[].uri"}


def resolve(node, document):
    while "$ref" in node:
        target = document
        for part in node["$ref"][2:].split("/"):
            target = target[part]
        node = {**target, **{k: v for k, v in node.items() if k != "$ref"}}
    return node


def property_paths(node, document, prefix=""):
    """Every property path of fhr.json in order; array-valued keys get []."""
    paths = []
    for name, child in resolve(node, document).get("properties", {}).items():
        child = resolve(child, document)
        if child.get("type") == "array":
            path = f"{prefix}{name}[]"
            paths.append(path)
            paths += property_paths(resolve(child["items"], document), document, path + ".")
            continue
        path = prefix + name
        paths.append(path)
        paths += property_paths(child, document, path + ".")
        for option in child.get("anyOf", []):
            option = resolve(option, document)
            if option.get("type") == "array":
                paths += property_paths(resolve(option["items"], document), document,
                                        f"{path}[].")
    return paths


def context_term(context, path):
    """The expanded IRI (or @id) that the context gives a property path."""
    scope = context["@context"]
    prefixes = dict(scope)
    parts = path.replace("[]", "").split(".")
    for index, key in enumerate(parts):
        definition = scope[key]
        if index < len(parts) - 1:
            scope = definition["@context"][1]
            prefixes.update(scope)
    value = definition if isinstance(definition, str) else definition["@id"]
    if value == "@id":
        return value
    prefix, _, local = value.partition(":")
    return prefixes[prefix] + local


class MappingTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = yaml.safe_load(TABLE.read_text(encoding="utf-8"))
        cls.entries = cls.table["entries"]
        cls.schema = json.loads((ROOT / "fhr.json").read_text())
        cls.context = json.loads(make_jsonld.CONTEXT_PATH.read_text())
        cls.subset = json.loads((ROOT / "tests/fixtures/schemaorg-v30.1-subset.json").read_text())
        cls.dcmi = {line.strip() for line in
                    (ROOT / "tests/fixtures/dcmi-terms-2020-01-20.txt").read_text().splitlines()
                    if line.strip() and not line.startswith("#")}

    def test_table_validates(self):
        schema = json.loads(SCHEMA.read_text())
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker())
                        .iter_errors(self.table), key=lambda e: list(e.path))
        self.assertEqual([f"{list(e.path)}: {e.message}" for e in errors], [])
        self.assertEqual(self.table["table_version"], "1.0.0")
        self.assertEqual(set(self.table["kinds"]), set(schema["$defs"]["kind"]["enum"]))

    def test_schema_copy_is_byte_identical(self):
        contract = ROOT / "specs/011-jsonld-mapping/contracts/mapping-table.schema.json"
        self.assertEqual(SCHEMA.read_bytes(), contract.read_bytes())

    def test_paths_equal_fhr_json(self):
        expected = property_paths(self.schema, self.schema)
        self.assertEqual(len(expected), 45)
        paths = [entry["path"] for entry in self.entries]
        self.assertEqual(paths, expected)

    def test_jsonld_terms_come_from_the_context(self):
        for entry in self.entries:
            with self.subTest(path=entry["path"]):
                self.assertEqual(entry["jsonld"]["term"], context_term(self.context, entry["path"]))

    def test_status_kind_and_gap(self):
        for entry in self.entries:
            term, mapping = entry["jsonld"]["term"], entry["jsonld"]
            with self.subTest(path=entry["path"]):
                if term.startswith(SDO):
                    pending = self.subset["terms"][term[len(SDO):]]["pending"]
                    self.assertEqual(mapping["status"], "pending" if pending else "core")
                    self.assertNotIn("schemaorg_gap", entry)
                elif term.startswith(FHR):
                    self.assertEqual(mapping["status"], "fhr")
                    self.assertEqual(mapping["kind"], "exact")
                    self.assertTrue(entry.get("schemaorg_gap", "").strip())
                else:
                    self.assertEqual(term, "@id")
                    self.assertEqual(mapping["status"], "keyword")
                    self.assertEqual(mapping["coercion"], "node-id")

    def test_dcmi_terms_are_pinned(self):
        for entry in self.entries:
            with self.subTest(path=entry["path"]):
                for mapping in entry["dcmi"]:
                    if mapping["term"] == "none":
                        self.assertTrue(mapping["reason"].strip())
                    else:
                        self.assertIn(mapping["term"], self.dcmi)

    def test_record_subject(self):
        for entry in self.entries:
            with self.subTest(path=entry["path"]):
                if entry["path"] in RECORD_PATHS:
                    self.assertEqual(entry["jsonld"].get("subject"), "record")
                    for mapping in entry["dcmi"]:
                        if mapping["term"] != "none":
                            self.assertEqual(mapping.get("subject"), "record")
                else:
                    self.assertNotEqual(entry["jsonld"].get("subject"), "record")

    def test_coercions_agree_with_the_context(self):
        root = self.context["@context"]
        for entry in self.entries:
            path, coercion = entry["path"], entry["jsonld"]["coercion"]
            with self.subTest(path=path):
                parts = path.replace("[]", "").split(".")
                scope = root
                for key in parts[:-1]:
                    scope = scope[key]["@context"][1]
                definition = scope[parts[-1]]
                if definition == "@id":
                    self.assertEqual(coercion, "node-id")
                    continue
                container = definition.get("@container")
                kind = definition.get("@type")
                if "@context" in definition:
                    self.assertEqual(coercion, "set-of-nodes" if container == "@set" else "node")
                    self.assertTrue(entry["jsonld"]["type"])
                elif container == "@list":
                    self.assertEqual(coercion, "list")
                elif container == "@set":
                    self.assertEqual(coercion, "set-of-iri" if kind == "@id" else "set")
                elif kind == "@id":
                    self.assertEqual(coercion, "iri")
                elif kind == "xsd:date":
                    self.assertEqual(coercion, "xsd:date")
                else:
                    self.assertEqual(coercion, "literal")
                if container == "@set":
                    self.assertEqual(entry["jsonld"].get("rdf_loss"), "order of @set items")

    def test_vocabulary_links_agree(self):
        graph = Graph().parse(ROOT / "jsonld/terms.ttl", format="turtle")
        implied = {(str(s), str(o)) for s, o in graph.subject_objects(RDFS.subPropertyOf)}
        self.assertEqual(implied, {(FHR + "accessionID", SDO + "identifier"),
                                   (FHR + "seqcol_id", SDO + "identifier")})
        for path in ("accessionID", "seqcol_id"):
            entry = next(e for e in self.entries if e["path"] == path)
            self.assertIn("rdfs:subPropertyOf schema:identifier", entry["notes"])
        self.assertIn((URIRef(FHR + "Agent"), SKOS.closeMatch,
                       URIRef("http://purl.org/dc/terms/Agent")), graph)

    def test_summary_counts(self):
        terms = Counter("schema.org" if e["jsonld"]["term"].startswith(SDO) else
                        "FHR" if e["jsonld"]["term"].startswith(FHR) else "@id"
                        for e in self.entries)
        dcmi = Counter("term" if e["dcmi"][0]["term"] != "none" else "none"
                       for e in self.entries)
        kinds = Counter(e["dcmi"][0]["kind"] for e in self.entries
                        if e["dcmi"][0]["term"] != "none")
        print(f"\nJSON-LD: {dict(terms)}; DCMI: {dict(dcmi)}; DCMI kinds: {dict(kinds)}")
        self.assertEqual(terms, {"schema.org": 20, "@id": 3, "FHR": 22})
        self.assertEqual(dcmi, {"term": 19, "none": 26})
        self.assertEqual(kinds, {"exact": 6, "broader": 2, "conditional": 11})

    def test_mappings_md_summary_is_current(self):
        text = (ROOT / "docs/MAPPINGS.md").read_text(encoding="utf-8")
        self.assertIn(make_jsonld.mappings_summary(self.table), text)

    def test_terms_md_has_dcmi_lines(self):
        text = (ROOT / "docs/TERMS.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("\n- DCMI: "), 22)


if __name__ == "__main__":
    unittest.main()
