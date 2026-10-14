# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The schema.org export profile (specs/013-schemaorg-export, docs/SCHEMAORG-EXPORT.md)."""

import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import make_jsonld  # noqa: E402
from test_jsonld_mappings import property_paths  # noqa: E402

try:
    from pyld import jsonld as pyld
except ImportError:  # pragma: no cover - the CI step installs requirements-jsonld.txt
    pyld = None

SDO = "http://schema.org/"
FHR = "https://w3id.org/fair-bioheaders/terms#"
FIXTURES = ROOT / "tests" / "fixtures" / "schemaorg-export"
TABLE = ROOT / "mappings" / "fhr-schemaorg-export.yml"
TABLE_SCHEMA = ROOT / "specs" / "013-schemaorg-export" / "contracts" / "export-table.schema.json"
SUBSET = ROOT / "tests" / "fixtures" / "schemaorg-v30.1-subset.json"
LITERAL_TYPES = {str: {"Text", "URL", "Date", "DateTime"}, int: {"Number", "Integer"},
                 float: {"Number", "Float"}, bool: {"Boolean"}}


def cases():
    found = {}
    for case in sorted(path for path in FIXTURES.iterdir() if path.is_dir()):
        record = json.loads((case / "record.json").read_text(encoding="utf-8"))
        context = case / "export-context.json"
        export = json.loads(context.read_text(encoding="utf-8")) if context.exists() else None
        found[case.name] = (record, export, case / "expected.jsonld")
    return found


def nodes(document):
    """Every node object in an export document, with the key path to it."""
    found = []

    def walk(value):
        if isinstance(value, dict):
            if "@type" in value:
                found.append(value)
            for key, item in value.items():
                if key != "@context":
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(document["@graph"])
    return found


def subject_kind(node):
    """The export-table subject of a node (contracts/export.md)."""
    kind = node["@type"]
    if kind == "PropertyValue":
        if node.get("propertyID") == make_jsonld.SEQCOL_SCHEME:
            return "seqcol"
        if node.get("propertyID") == make_jsonld.DOI_REGISTRY:
            return "doi"
        return "accession"
    return {"Dataset": "assembly", "CreativeWork": "metadata-record", "CreateAction": "activity",
            "Observation": "observation", "Grant": "grant", "ScholarlyArticle": "article",
            "Taxon": "taxon", "Person": "author", "Organization": "author",
            "fhr:Agent": "author", "SoftwareApplication": "software",
            "fhr:VitalStats": "vital-stats", "HowTo": "how-to"}[kind]


def compact_keys(node):
    keys = set()
    for key in node:
        if key == "@id":
            keys.add("@id")
        elif key.startswith("fhr:") or key.startswith("dct:"):
            keys.add(key)
        elif not key.startswith("@"):
            keys.add("sdo:" + key)
    return keys


class ExportFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = cases()

    def test_fixtures_and_example_are_current(self):
        for path, text in make_jsonld.export_outputs().items():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_every_source_record_is_valid_fhr(self):
        schema = json.loads((ROOT / "fhr.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for name, (record, _, _) in self.cases.items():
            with self.subTest(case=name):
                self.assertEqual([e.message for e in validator.iter_errors(record)], [])

    def test_shape(self):
        for name, (record, export, _) in self.cases.items():
            document = make_jsonld.to_export(record, export)
            with self.subTest(case=name):
                self.assertEqual(document["@context"], make_jsonld.EXPORT_CONTEXT)
                graph = document["@graph"]
                assembly, metadata = graph[0], graph[1]
                self.assertEqual(assembly["@type"], "Dataset")
                self.assertEqual(metadata["@type"], "CreativeWork")
                self.assertEqual(metadata["about"], {"@id": assembly["@id"]})
                for node in graph[2:]:
                    self.assertIn(node["@type"], ("CreateAction", "Observation"))
                    target = node.get("result") or node.get("observationAbout")
                    self.assertEqual(target, {"@id": assembly["@id"]})
                self.assertTrue(make_jsonld.is_export(document))

    def test_authors_keep_their_subject(self):
        for name, (record, export, _) in self.cases.items():
            graph = make_jsonld.to_export(record, export)["@graph"]
            with self.subTest(case=name):
                self.assertEqual([a.get("name") for a in graph[0]["creator"]],
                                 [a.get("name") for a in record["assemblyAuthor"]])
                self.assertEqual([a.get("name") for a in graph[1]["creator"]],
                                 [a.get("name") for a in record["metadataAuthor"]])
                self.assertNotIn("schemaVersion", graph[0])
                self.assertEqual(graph[1]["schemaVersion"], {"@id": record["schema"]})
                self.assertEqual(graph[1]["fhr:schemaVersion"], record["schemaVersion"])
                self.assertEqual(graph[0]["version"], record["version"])

    def test_conditions(self):
        graph = {name: make_jsonld.to_export(record, export)["@graph"]
                 for name, (record, export, _) in self.cases.items()}
        article = graph["article-doi"][0]["subjectOf"][0]
        self.assertEqual(article["@type"], "ScholarlyArticle")
        self.assertEqual(article["@id"], "https://doi.org/10.1093/bib/bbae122")
        self.assertNotIn("10.1093/bib/bbae122", json.dumps(graph["article-doi"][0]["identifier"]
                                                           if "identifier" in graph["article-doi"][0]
                                                           else []))
        self.assertNotIn("subjectOf", graph["article-not-doi"][0])
        self.assertEqual(graph["article-not-doi"][0]["citation"],
                         "10.1093/bib/bbae122 (accepted manuscript)")
        software = graph["provenance-software"]
        self.assertEqual(software[0]["fhr:assemblyProtocol"],
                         {"@id": "https://example.org/assembly-protocol"})
        self.assertEqual(software[0]["fhr:instrument"], ["Example sequencer"])
        self.assertNotIn("actionProcess", software[2])
        self.assertEqual(software[2]["instrument"][0]["fhr:commandLineOption"],
                         {"@list": ["-t", "32"]})
        how_to = graph["provenance-howto"]
        self.assertNotIn("fhr:assemblyProtocol", how_to[0])
        self.assertEqual(how_to[2]["actionProcess"],
                         {"@id": "https://example.org/assembly-protocol", "@type": "HowTo"})
        self.assertEqual(graph["provenance-legacy"][2]["instrument"],
                         [{"@type": "SoftwareApplication", "name": "legacy assembler 1.0"}])
        self.assertEqual(len(graph["metadata-record"]), 2)  # no empty CreateAction
        iri = graph["iri-values"][0]
        self.assertEqual(iri["subjectOf"], [{"@id": "https://example.org/genome/README"}])
        self.assertNotIn("description", iri)
        self.assertEqual(iri["license"],
                         {"@id": "https://creativecommons.org/publicdomain/zero/1.0/"})
        self.assertEqual(graph["funding-grant"][0]["funding"],
                         {"@type": "Grant", "description":
                          "Synthetic Research Council, award SRC-0001 (placeholder text)"})
        seqcol = graph["seqcol"][0]["identifier"]
        self.assertEqual(seqcol[0], "beetlebase:TC010103")
        self.assertEqual(seqcol[-1], {"@type": "PropertyValue",
                                      "propertyID": "GA4GH refget sequence collection",
                                      "value": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"})

    def test_statistics(self):
        record, export, _ = self.cases["statistics"]
        graph = make_jsonld.to_export(record, export)["@graph"]
        observations = [n for n in graph if n["@type"] == "Observation"]
        numeric = [k for k in record["vitalStats"] if k != "readTechnology"]
        self.assertEqual([o["name"] for o in observations], numeric)
        for observation in observations:
            key = observation["name"]
            unit, label = make_jsonld.UNITS[make_jsonld.STATISTIC_UNITS[key]]
            self.assertEqual(observation["measuredProperty"], {"@id": f"fhr:{key}"})
            self.assertEqual(observation["value"], record["vitalStats"][key])
            self.assertEqual(observation["unitCode"], {"@id": unit})
            self.assertEqual(observation["unitText"], label)
        self.assertEqual(graph[0]["fhr:vitalStats"],
                         {"@type": "fhr:VitalStats", "fhr:readTechnology": "HiFi"})
        for name, (record, export, _) in self.cases.items():
            text = make_jsonld.export_text(record, export)
            with self.subTest(case=name):
                self.assertNotIn("observationDate", text)
                self.assertNotIn("variableMeasured", text)
                self.assertNotIn("startTime", text)
                self.assertNotIn("endTime", text)

    def test_bioschemas_claim_only_when_complete(self):
        for name, (record, export, _) in self.cases.items():
            assembly = make_jsonld.to_export(record, export)["@graph"][0]
            with self.subTest(case=name):
                self.assertEqual("dct:conformsTo" in assembly, name == "full")

    def test_no_fabricated_values(self):
        """Every literal and IRI comes from the source, the export context or the profile."""
        constants = {make_jsonld.SEQCOL_SCHEME, make_jsonld.DOI_REGISTRY,
                     make_jsonld.BIOSCHEMAS_DATASET_PROFILE, make_jsonld.ASSEMBLY_ID,
                     make_jsonld.METADATA_RECORD_ID, make_jsonld.ACTIVITY_ID}
        constants |= {value for pair in make_jsonld.UNITS.values() for value in pair}

        def scalars(value):
            if isinstance(value, dict):  # type names are the profile's, not values
                for key, item in value.items():
                    if key != "@type":
                        yield from scalars(item)
            elif isinstance(value, list):
                for item in value:
                    yield from scalars(item)
            else:
                yield value

        for name, (record, export, _) in self.cases.items():
            allowed = set(scalars(record)) | set(scalars(export or {})) | constants
            stats = record.get("vitalStats", {})
            allowed |= {f"fhr:{key}" for key in stats} | {f"_:observation-{key}" for key in stats}
            allowed |= set(stats)
            if "scholarlyArticle" in record:
                allowed.add(f"https://doi.org/{record['scholarlyArticle']}")
            document = make_jsonld.to_export(record, export)
            for node in nodes(document):
                for key, value in node.items():
                    if key == "@type":
                        continue
                    for scalar in scalars(value):
                        with self.subTest(case=name, key=key, value=scalar):
                            self.assertIn(scalar, allowed)

    def test_reader_refuses_an_export(self):
        record, export, _ = self.cases["full"]
        document = json.loads(make_jsonld.export_text(record, export))
        with self.assertRaisesRegex(ValueError, "one-way schema.org export"):
            make_jsonld.canonical_record(document)

    def test_unmapped_nested_keys_are_reported_and_left_out(self):
        record, export, _ = self.cases["metadata-record"]
        record = json.loads(json.dumps(record))
        record["taxon"]["checksum"] = "nested property, not the file checksum"
        self.assertEqual(make_jsonld.export_unmapped_keys(record), ["taxon.checksum"])
        self.assertNotIn("nested property", make_jsonld.export_text(record, export))

    def test_canonical_form_is_unchanged(self):
        """SC-002: the canonical writer has no export terms, and its examples are current."""
        context = make_jsonld.load_context()
        for path, text in make_jsonld.example_outputs(context).items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_text(encoding="utf-8"), text)
                for term in ("Observation", "CreateAction", "Grant", "ScholarlyArticle"):
                    self.assertNotIn(f'"{term}"', text)


class ExportTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = yaml.safe_load(TABLE.read_text(encoding="utf-8"))
        cls.entries = cls.table["entries"]
        cls.schema = json.loads((ROOT / "fhr.json").read_text(encoding="utf-8"))
        all_cases = cases()
        cls.produced = set()
        cls.produced_any = set()
        for name, (record, export, _) in all_cases.items():
            pairs = {(subject_kind(node), key)
                     for node in nodes(make_jsonld.to_export(record, export))
                     for key in compact_keys(node)}
            cls.produced_any |= pairs
            if name == "full":
                cls.produced = pairs

    def test_schema_valid(self):
        schema = json.loads(TABLE_SCHEMA.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker())
                      .iter_errors(self.table))
        self.assertEqual([e.message for e in errors], [])

    def test_paths_equal_fhr_json(self):
        self.assertEqual([entry["path"] for entry in self.entries],
                         property_paths(self.schema, self.schema))

    def test_every_target_is_produced(self):
        """SC-004: the full fixture produces each declared target; alternatives occur too."""
        for entry in self.entries:
            with self.subTest(path=entry["path"]):
                self.assertIn((entry["subject"], entry["property"]), self.produced)
                if "alternative" in entry:
                    alternative = entry["alternative"]
                    self.assertIn((alternative["subject"], alternative["property"]),
                                  self.produced_any)

    def test_statistic_units_cover_the_numeric_fields(self):
        stats = self.schema["properties"]["vitalStats"]["properties"]
        numeric = {name for name, spec in stats.items()
                   if spec.get("type") in ("integer", "number")}
        self.assertEqual(numeric - set(make_jsonld.STATISTIC_UNITS), set())


@unittest.skipIf(pyld is None, "PyLD is not installed")
class ExportVocabularyTests(unittest.TestCase):
    """SC-001: schema.org terms within their domains and ranges (pinned v30.1 subset)."""

    @classmethod
    def setUpClass(cls):
        cls.terms = json.loads(SUBSET.read_text(encoding="utf-8"))["terms"]
        vocabulary = Graph().parse(ROOT / "jsonld" / "terms.ttl", format="turtle")
        cls.fhr_classes = {}
        for cls_iri in vocabulary.subjects(RDF.type, RDFS.Class):
            parents = {str(o)[len(SDO):] for o in vocabulary.objects(cls_iri, RDFS.subClassOf)
                       if str(o).startswith(SDO)}
            cls.fhr_classes[str(cls_iri)] = parents
        cls.fhr_properties = {str(s) for s in vocabulary.subjects(RDF.type, RDF.Property)}
        cls.documents = {name: make_jsonld.to_export(record, export)
                         for name, (record, export, _) in cases().items()}
        record = json.loads((ROOT / "examples" / "example.fhr.json").read_text(encoding="utf-8"))
        cls.documents["example"] = make_jsonld.to_export(record)

    def closure(self, names):
        seen, todo = set(), list(names)
        while todo:
            name = todo.pop()
            if name in seen:
                continue
            seen.add(name)
            todo += self.terms.get(name, {}).get("subClassOf", [])
        return seen

    def types_of(self, node):
        names = set()
        for kind in node.get("@type", []):
            if kind.startswith(SDO):
                names.add(kind[len(SDO):])
            elif kind in self.fhr_classes:
                names |= self.fhr_classes[kind]
            else:
                self.fail(f"type {kind} is neither schema.org nor FAIR-bioHeaders")
        return self.closure(names)

    def test_domains_ranges_and_namespaces(self):
        for name, document in self.documents.items():
            flat = pyld.flatten(document)
            graph = {node["@id"]: node for node in flat}
            for node in flat:
                subject_types = self.types_of(node)
                for predicate, values in node.items():
                    if predicate.startswith("@"):
                        continue
                    if predicate.startswith(FHR):
                        self.assertIn(predicate, self.fhr_properties, predicate)
                        continue
                    if predicate == "http://purl.org/dc/terms/conformsTo":
                        continue
                    self.assertTrue(predicate.startswith(SDO), predicate)
                    term = self.terms[predicate[len(SDO):]]
                    self.assertFalse(term["pending"], predicate)
                    with self.subTest(case=name, predicate=predicate):
                        self.assertTrue(subject_types & set(term["domainIncludes"]),
                                        f"{predicate} on {sorted(subject_types)}")
                        ranges = set(term["rangeIncludes"])
                        for value in values:
                            self.check_range(predicate, ranges, value, graph)

    def check_range(self, predicate, ranges, value, graph):
        if "@list" in value:
            for item in value["@list"]:
                self.check_range(predicate, ranges, item, graph)
            return
        if "@value" in value:
            literal = value["@value"]
            kinds = set(LITERAL_TYPES[type(literal)])
            if isinstance(literal, str) and not make_jsonld.is_absolute_url(literal):
                kinds.discard("URL")
            if predicate == SDO + "license" and not kinds & ranges:
                # Rule X5: a licence that is not a URL stays the provider's text; schema.org
                # expects a URL or CreativeWork and validator.schema.org reports it (011 V8).
                return
            self.assertTrue(kinds & ranges, f"{predicate} literal {literal!r}")
            return
        target = value["@id"]
        if target in self.fhr_properties:  # measuredProperty: an rdf:Property term
            self.assertIn("Property", ranges)
            return
        node = graph.get(target, {})
        if node.get("@type") == [FHR + "Agent"] and predicate == SDO + "creator":
            # Research R-12: an author with neither an ORCID, a ROR ID nor a nameType is not
            # classified; inventing Person or Organization would fabricate metadata.
            return
        if node.get("@type"):
            self.assertTrue(self.types_of(node) & ranges,
                            f"{predicate} -> {node['@type']} not in {sorted(ranges)}")
        # An untyped IRI may denote any resource; nothing more can be checked offline.

    def test_relationship_direction(self):
        for name, document in self.documents.items():
            flat = {node["@id"]: node for node in pyld.flatten(document)}
            dataset = [i for i, n in flat.items() if SDO + "Dataset" in n.get("@type", [])]
            self.assertEqual(len(dataset), 1)
            for node in flat.values():
                for predicate in ("about", "observationAbout", "result"):
                    for value in node.get(SDO + predicate, []):
                        if SDO + "CreativeWork" in node.get("@type", []) or predicate != "about":
                            with self.subTest(case=name, predicate=predicate):
                                self.assertEqual(value["@id"], dataset[0])


if __name__ == "__main__":
    unittest.main()
