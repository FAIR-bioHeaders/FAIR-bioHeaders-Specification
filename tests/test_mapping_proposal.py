# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Offline checks of the draft #56 artifacts; not target/deposit conformance."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_mapping_context import context_errors, load_json  # noqa: E402

BUNDLE = ROOT / "tests/fixtures/mapping-proposal"
DC = Namespace("http://purl.org/dc/terms/")


class MappingProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((BUNDLE / "source.json").read_text())
        cls.context = json.loads((BUNDLE / "context.json").read_text())
        cls.schema = json.loads((ROOT / "mappings/proposals/assembly-export-context.schema.json").read_text())
        cls.table = yaml.safe_load((ROOT / "mappings/proposals/assembly-dcmi.yml").read_text())
        cls.status = yaml.safe_load((ROOT / "mappings/proposals/profile-status.yml").read_text())
        cls.report = json.loads((BUNDLE / "report.json").read_text())
        cls.graph = Graph().parse(BUNDLE / "qualified-dc.ttl", format="turtle")
        cls.resource = URIRef(cls.context["resourceIRI"])
        cls.record = URIRef(cls.context["metadataRecordIRI"])

    def test_context_schema_and_complete_source_fixture_are_valid(self):
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual(context_errors(self.context, self.source), [])
        schema = json.loads((ROOT / "fhr.json").read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(self.source)
        self.assertEqual((BUNDLE / "source.json").read_bytes(), (ROOT / "examples/example.fhr.json").read_bytes())
        self.assertEqual(self.context["profileVersion"], self.table["profile_version"])
        self.assertEqual(self.report["profileVersion"], self.table["profile_version"])

    def test_no_title_fallback_or_unknown_context(self):
        for key in self.schema["required"]:
            context = deepcopy(self.context)
            del context[key]
            self.assertTrue(context_errors(context, self.source), key)
        for patch in ({"title": " "}, {"resourceDOI": None}, {"resourceDOI": ""},
                      {"assemblyAuthor": [{"name": "Unreviewed override"}]},
                      {"publicationDate": "2026-02-30"}, {"publicationYear": "2026"},
                      {"publisher": {}}, {"resourceIRI": "not an IRI"}):
            self.assertTrue(context_errors({**self.context, **patch}, self.source), patch)

    def test_descriptive_context_does_not_invent_registration_values(self):
        minimal = {key: value for key, value in self.context.items() if key in self.schema["required"]}
        before = deepcopy(minimal)
        self.assertEqual(context_errors(minimal, self.source), [])
        self.assertEqual(minimal, before)
        self.assertNotIn("resourceDOI", self.context)
        self.assertEqual(self.report["not_supplied_context"], ["resourceDOI"])
        for result in self.report["registration_readiness"].values():
            self.assertTrue(result.startswith("not-assessed:"))

    def test_context_conflicts_are_reported_without_overwriting(self):
        for patch, message in [
            ({"resourceIRI": self.context["metadataRecordIRI"]}, "distinct resources"),
            ({"publicationYear": 2025}, "conflict"),
            ({"resourceDOI": self.source["scholarlyArticle"].upper()}, "distinct article"),
        ]:
            context = {**deepcopy(self.context), **patch}
            before = deepcopy(context)
            self.assertTrue(any(message in error for error in context_errors(context, self.source)))
            self.assertEqual(context, before)

    def test_other_types_versions_and_moving_main_are_not_silently_reinterpreted(self):
        for schema in [self.source["schema"].replace("fhr/", "fhp/"),
                       self.source["schema"].replace("fhr/", "fht/"),
                       self.source["schema"].replace("v0.4.0", "v999.0.0"),
                       "https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/main/fhr.json"]:
            self.assertTrue(context_errors(self.context, {**self.source, "schema": schema}))
        self.assertTrue(context_errors(self.context, {**self.source, "schema": {}}))
        self.assertTrue(context_errors(self.context, {**self.source, "schemaVersion": 2}))
        self.assertTrue(context_errors({**self.context, "resourceKind": "protein-set"}, self.source))

    def test_duplicate_keys_and_invalid_json_constants_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            for text in ['{"title":"first","title":"second"}', '{"year":NaN}']:
                path.write_text(text)
                with self.assertRaises(ValueError):
                    load_json(path)

    def test_every_root_field_has_an_explicit_handling_and_loss_rule(self):
        source_schema = json.loads((ROOT / "fhr.json").read_text())
        entries = self.table["entries"]
        self.assertEqual(len(entries), len(source_schema["properties"]))
        self.assertEqual({entry["path"] for entry in entries}, {"/" + key for key in source_schema["properties"]})
        terms = {line.strip() for line in (ROOT / "tests/fixtures/dcmi-terms-2020-01-20.txt").read_text().splitlines()
                 if line.strip() and not line.startswith("#")}
        for entry in entries:
            for key in ["subject", "kind", "condition", "transformation", "loss_or_limitation", "target_cardinality"]:
                self.assertTrue(entry[key], (entry["path"], key))
            self.assertEqual(entry["source_cardinality"], "1" if entry["path"][1:] in source_schema["required"] else "0..1")
            self.assertIn(entry["kind"], ["conditional", "unsupported"])
            if entry["kind"] == "unsupported":
                self.assertEqual(entry["terms"], [])
            for term in entry["terms"]:
                self.assertIn(term, terms)
        for entry in self.table["context_entries"]:
            self.assertIn(entry["term"], terms)
        self.assertEqual(set(self.report["source_root_fields_not_projected"]),
                         {entry["path"] for entry in entries if entry["kind"] == "unsupported"})

    def test_fixture_authors_and_dates_have_the_correct_subjects(self):
        for subject, field in [(self.resource, "assemblyAuthor"), (self.record, "metadataAuthor")]:
            agents = list(self.graph.objects(subject, DC.creator))
            self.assertEqual({str(self.graph.value(agent, RDFS.label)) for agent in agents},
                             {author["name"] for author in self.source[field]})
            self.assertEqual({str(identifier) for agent in agents for identifier in self.graph.objects(agent, DC.identifier)},
                             {author["uri"] for author in self.source[field] if "uri" in author})
            for agent in agents:
                self.assertIn((agent, RDF.type, DC.Agent), self.graph)
        self.assertIn((self.resource, DC.created, Literal(self.source["dateCreated"], datatype=XSD.date)), self.graph)
        self.assertIn((self.resource, DC.issued, Literal(self.context["publicationDate"], datatype=XSD.date)), self.graph)
        self.assertFalse(list(self.graph.objects(self.record, DC.created)))
        self.assertFalse(list(self.graph.objects(self.record, DC.issued)))
        self.assertIn((self.record, DC.conformsTo, URIRef(self.source["schema"])), self.graph)
        self.assertFalse(list(self.graph.objects(self.resource, DC.conformsTo)))

    def test_fixture_title_publisher_rights_and_relationships_are_explicit(self):
        self.assertEqual(self.graph.value(self.resource, DC.title), Literal(self.context["title"]))
        self.assertNotEqual(self.context["title"], self.source["genome"])
        publisher = self.graph.value(self.resource, DC.publisher)
        self.assertEqual(self.graph.value(publisher, RDFS.label), Literal(self.context["publisher"]["name"]))
        rights = self.graph.value(self.resource, DC.rights)
        self.assertIn((rights, RDF.type, DC.RightsStatement), self.graph)
        self.assertEqual(self.graph.value(rights, RDFS.label), Literal(self.source["reuseConditions"]))
        expected = {URIRef(uri) for uri in self.source["relatedLink"]}
        expected.add(URIRef(self.source["assemblyProtocol"]))
        expected.add(URIRef("https://doi.org/" + self.source["scholarlyArticle"]))
        self.assertEqual(set(self.graph.objects(self.resource, DC.relation)), expected)
        self.assertEqual(list(self.graph.objects(self.resource, DC.identifier)), [Literal(self.context["resourceIRI"])])
        self.assertIn((self.record, DC.subject, self.resource), self.graph)
        self.assertIn((self.resource, DC.subject, URIRef(self.source["taxon"]["uri"])), self.graph)

    def test_target_and_header_status_never_imply_adoption_or_fht_support(self):
        registry = json.loads((ROOT / "schemas/versions.json").read_text())
        self.assertNotIn("FHT", registry["files"])
        self.assertEqual(self.table["status"], "proposal")
        self.assertEqual(self.status["status"], "proposal")
        self.assertEqual(self.status["targets"]["dcmi-qualified"]["status"], "draft-fixture")
        for target in ["datacite", "crossref", "ark", "bibtex", "biblatex"]:
            self.assertEqual(self.status["targets"][target]["status"], "planned")
        for kind in ["FHR", "FHP", "FHGFF3"]:
            record = self.status["header_types"][kind]
            self.assertEqual(record["released_schema_version"], registry["releases"][record["release"]][kind])
        fht = self.status["header_types"]["FHT"]
        self.assertEqual(fht["status"], "blocked")
        self.assertNotIn("released_schema_version", fht)
        self.assertEqual(len(fht["blocking_issues"]), 2)

    def test_cli_only_checks_draft_context(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/check_mapping_context.py"),
                                 str(BUNDLE / "context.json"), "--source", str(BUNDLE / "source.json")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no export, deposit validation or registration", result.stdout)


if __name__ == "__main__":
    unittest.main()
