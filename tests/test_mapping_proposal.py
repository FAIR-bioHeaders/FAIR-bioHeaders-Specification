# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Offline checks of adopted mapping-v1 artifacts; not target/deposit conformance."""
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
        cls.source_schema = json.loads(subprocess.check_output(
            ["git", "show", "v0.4.0:fhr.json"], cwd=ROOT))
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
        Draft202012Validator(self.source_schema, format_checker=FormatChecker()).validate(self.source)
        self.assertEqual(self.context["profileVersion"], self.table["profile_version"])
        self.assertEqual(self.report["profileVersion"], self.table["profile_version"])

    def test_source_fixture_is_the_pinned_example(self):
        """source.json is examples/example.fhr.json at commit 2da7c96 (README); the
        example itself moves with the release it cites (FHR 2.1 from v0.5.0)."""
        pinned = subprocess.run(["git", "show", "2da7c96:examples/example.fhr.json"],
                                cwd=ROOT, capture_output=True)
        if pinned.returncode:
            self.skipTest("commit 2da7c96 is not available (shallow clone); fetch the history")
        self.assertEqual((BUNDLE / "source.json").read_bytes(), pinned.stdout)

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

    def test_article_resolver_cannot_identify_assembly_without_optional_doi(self):
        for iri in [
            "https://doi.org/10.1093/bib/bbae122",
            "http://doi.org/10.1093/bib/bbae122",
            "https://DX.DOI.ORG/10.1093/BIB/BBAE122",
            "https://doi.org/10.1093%2Fbib%2Fbbae122",
            "https://doi.org/10.1093/bib/bbae122?download=1#article",
        ]:
            with self.subTest(iri=iri):
                context = {**deepcopy(self.context), "resourceIRI": iri}
                before = deepcopy(context)
                source_before = deepcopy(self.source)
                self.assertNotIn("resourceDOI", context)
                self.assertTrue(any("resourceIRI" in error and "distinct article" in error
                                    for error in context_errors(context, self.source)))
                self.assertEqual(context, before)
                self.assertEqual(self.source, source_before)

    def test_distinct_assembly_identifiers_remain_valid(self):
        for iri in [
            self.context["resourceIRI"],
            "https://doi.org/10.1234/assembly",
            "https://example.org/10.1093/bib/bbae122",
            "https://doi.org.example.org/10.1093/bib/bbae122",
        ]:
            with self.subTest(iri=iri):
                self.assertEqual(context_errors({**self.context, "resourceIRI": iri}, self.source), [])

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

    def test_adoption_status_preserves_identity_without_official_or_fht_claims(self):
        registry = json.loads((ROOT / "schemas/versions.json").read_text())
        self.assertNotIn("FHT", registry["files"])
        self.assertEqual(self.table["status"], "adopted")
        self.assertEqual(self.status["status"], "adopted")
        self.assertEqual(self.status["targets"]["dcmi-qualified"]["status"], "adopted-foundation")
        self.assertFalse(self.table["official"])
        self.assertFalse(self.status["official"])
        self.assertEqual(self.schema["properties"]["profileVersion"], {"const": "0.1.0-draft.1"})
        self.assertEqual(self.table["source_schema_version"], "2.0")
        self.assertEqual(self.status["header_types"]["FHR"]["release"], "v0.4.0")
        self.assertEqual(self.table["adoption_decision"], self.status["adoption_decision"])
        for target in ["datacite", "crossref", "ark", "bibtex", "biblatex"]:
            self.assertEqual(self.status["targets"][target]["status"], "deferred")
        for kind in ["FHR", "FHP", "FHGFF3"]:
            record = self.status["header_types"][kind]
            self.assertEqual(record["released_schema_version"], registry["releases"][record["release"]][kind])
        fht = self.status["header_types"]["FHT"]
        self.assertEqual(fht["status"], "blocked")
        self.assertNotIn("released_schema_version", fht)
        self.assertEqual(fht["blocking_issues"], ["https://github.com/FAIR-bioHeaders/FHT-Specification/issues/10"])

    def test_cli_only_checks_context_despite_adoption(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/check_mapping_context.py"),
                                 str(BUNDLE / "context.json"), "--source", str(BUNDLE / "source.json")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no export, deposit validation or registration", result.stdout)


    def test_minimal_companion_omits_unknowns_and_keeps_creator_subjects(self):
        directory = BUNDLE / "minimal"
        source = load_json(directory / "source.json")
        context = load_json(directory / "context.json")
        self.assertEqual(context_errors(context, source), [])
        Draft202012Validator(self.source_schema, format_checker=FormatChecker()).validate(source)
        graph = Graph().parse(directory / "qualified-dc.ttl", format="turtle")
        resource, record = URIRef(context["resourceIRI"]), URIRef(context["metadataRecordIRI"])
        self.assertFalse(list(graph.objects(resource, DC.publisher)))
        self.assertFalse(list(graph.objects(resource, DC.issued)))
        self.assertFalse(list(graph.objects(record, DC.created)))
        self.assertFalse(list(graph.objects(record, DC.issued)))
        for subject, field in [(resource, "assemblyAuthor"), (record, "metadataAuthor")]:
            agents = list(graph.objects(subject, DC.creator))
            self.assertEqual(len(agents), 1)
            self.assertEqual(graph.value(agents[0], RDFS.label), Literal(source[field][0]["name"]))
            self.assertEqual(list(graph.objects(agents[0], RDF.type)), [DC.Agent])
            self.assertFalse(list(graph.objects(agents[0], DC.identifier)))
        self.assertEqual(graph.value(resource, DC.title), Literal(context["title"]))
        self.assertNotEqual(context["title"], source["genome"])
        self.assertFalse(set(graph.objects(resource, DC.creator)) & set(graph.objects(record, DC.creator)))
        self.assertEqual(len(graph), 14)

    def test_optional_context_assertions_are_not_unconditional_graph_aliases(self):
        context = {**self.context, "resourceDOI": "10.1234/assembly"}
        self.assertEqual(context_errors(context, self.source), [])
        # These assertions remain in preserved context; no adopted context row projects them.
        paths = {entry["path"] for entry in self.table["context_entries"]}
        self.assertNotIn("/publicationYear", paths)
        self.assertNotIn("/resourceDOI", paths)
        self.assertFalse(list(self.graph.triples((None, DC.issued, Literal(2026, datatype=XSD.gYear)))))

    def test_reference_snapshot_and_transcription_are_pinned_metadata_only(self):
        import hashlib
        directory = ROOT / "tests/fixtures/mapping-reference"
        reference = load_json(directory / "reference.json")
        raw = (directory / reference["evidence"]["snapshot"]).read_bytes()
        self.assertEqual(len(raw), reference["evidence"]["bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), reference["evidence"]["sha256"])
        snapshot = json.loads(raw)
        self.assertEqual(snapshot["total_count"], 1)
        report = snapshot["reports"][0]
        resource = reference["resource"]
        self.assertEqual(resource["accession"], report["accession"])
        self.assertEqual(resource["title"], report["assembly_info"]["assembly_name"])
        self.assertEqual(resource["organism"], report["organism"]["organism_name"])
        self.assertEqual(reference["sourceAssertions"], {
            "submitter": report["assembly_info"]["submitter"],
            "repositoryReleaseDate": report["assembly_info"]["release_date"]})
        self.assertNotIn("schema", reference)
        self.assertNotIn("checksum", reference)
        self.assertNotIn("creators", resource)
        self.assertTrue(context_errors(self.context, reference))
        for gap in ["assemblyCreatorRoles", "resourceDOI", "sequenceBytes", "exactFileChecksum",
                    "sequenceCollectionDigest", "verifiedParentFileIdentity", "archivePossession",
                    "futurePersistence"]:
            self.assertIn(gap, reference["notEstablished"])


if __name__ == "__main__":
    unittest.main()
