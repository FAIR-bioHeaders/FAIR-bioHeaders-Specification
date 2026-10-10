# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The FAIR-bioHeaders vocabulary (contracts/vocabulary.md, FR-002, FR-008)."""

import copy
import json
from pathlib import Path
import re
import sys
import unittest

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_jsonld_roundtrip import EXPORT, ROR, loader, pyld, records  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
import make_jsonld  # noqa: E402

SUBSET = ROOT / "tests" / "fixtures" / "schemaorg-v30.1-subset.json"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
ALLOWED_RDF = {RDF_NS + name for name in ("type", "first", "rest", "nil")}
# Bioschemas-endorsed term outside schema.org, emitted only with an export context.
BIOSCHEMAS_TERMS = {"http://purl.org/dc/terms/conformsTo"}
FHR = Namespace("https://w3id.org/fair-bioheaders/terms#")
SDO = Namespace("http://schema.org/")
ONTOLOGY = URIRef("https://w3id.org/fair-bioheaders/terms")
CLASSES = {"Agent", "VitalStats"}
PROPERTIES = {
    "schemaVersion", "metadataAuthor", "voucherSpecimen", "accessionID", "instrument",
    "relatedLink", "masking", "vitalStats", "checksum", "assemblySoftware",
    "assemblyProtocol", "seqcol_id",
    "L50", "N50", "L90", "N90", "totalBasePairs", "numberContigs", "numberScaffolds",
    "readTechnology", "gcContent", "scaffoldN50", "scaffoldN90", "scaffoldL50", "scaffoldL90",
    "commandLineOption",
    "nameType",
}


def fhr_iris(node, prefixes=None):
    """Every fhr: IRI used in a context document (CURIEs or full IRIs)."""
    found = set()
    if isinstance(node, dict):
        for key, value in node.items():
            found |= fhr_iris(key) if isinstance(key, str) and key.startswith("fhr:") else set()
            found |= fhr_iris(value)
    elif isinstance(node, list):
        for value in node:
            found |= fhr_iris(value)
    elif isinstance(node, str):
        if node.startswith("fhr:"):
            found.add(str(FHR) + node[4:])
        elif node.startswith(str(FHR)) and node != str(FHR):
            found.add(node)
    return found


class VocabularyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = Graph().parse(ROOT / "jsonld" / "terms.ttl", format="turtle")
        cls.terms_md = (ROOT / "docs" / "TERMS.md").read_text(encoding="utf-8")
        cls.context = json.loads((ROOT / "jsonld" / "fhr.context.jsonld").read_text())

    def defined(self, kind):
        return {str(s)[len(str(FHR)):] for s in self.graph.subjects(RDF.type, kind)
                if str(s).startswith(str(FHR))}

    def test_classes_and_properties(self):
        self.assertEqual(self.defined(RDFS.Class), CLASSES)
        self.assertEqual(self.defined(RDF.Property), PROPERTIES)
        self.assertIn((ONTOLOGY, RDF.type, OWL.Ontology), self.graph)

    def test_every_term_has_label_comment_and_definition(self):
        for name in CLASSES | PROPERTIES:
            term = FHR[name]
            with self.subTest(term=name):
                labels = list(self.graph.objects(term, RDFS.label))
                self.assertEqual(labels, [Literal(name, lang="en")])
                comments = list(self.graph.objects(term, RDFS.comment))
                self.assertEqual(len(comments), 1)
                self.assertTrue(str(comments[0]).strip())
                self.assertEqual(comments[0].language, "en")
                self.assertEqual(list(self.graph.objects(term, RDFS.isDefinedBy)), [ONTOLOGY])

    def test_properties_have_domain_and_range(self):
        for name in PROPERTIES:
            with self.subTest(term=name):
                self.assertTrue(list(self.graph.objects(FHR[name], SDO.domainIncludes)))
                self.assertTrue(list(self.graph.objects(FHR[name], SDO.rangeIncludes)))
        self.assertIn((FHR.accessionID, RDFS.subPropertyOf, SDO.identifier), self.graph)
        self.assertIn((FHR.Agent, RDFS.subClassOf, SDO.Thing), self.graph)
        self.assertIn((FHR.VitalStats, RDFS.subClassOf, SDO.StructuredValue), self.graph)
        self.assertIn((FHR.Agent, URIRef("http://www.w3.org/2004/02/skos/core#closeMatch"),
                       URIRef("http://purl.org/dc/terms/Agent")), self.graph)
        self.assertIn((FHR.N50, SDO.domainIncludes, FHR.VitalStats), self.graph)
        self.assertIn((FHR.commandLineOption, SDO.domainIncludes, SDO.SoftwareApplication),
                      self.graph)
        self.assertIn((FHR.checksum, SDO.domainIncludes, SDO.Dataset), self.graph)

    def test_every_fhr_iri_in_the_context_is_defined(self):
        used = fhr_iris(self.context)
        self.assertTrue(used)
        defined = {str(FHR[name]) for name in CLASSES | PROPERTIES}
        self.assertEqual(used - defined, set())

    def test_no_terms_outside_schema_version_1(self):
        for name in ("derivedFrom", "headerType", "relationship", "DerivedFrom"):
            with self.subTest(term=name):
                self.assertEqual(list(self.graph.predicate_objects(FHR[name])), [])

    def test_jsonld_vocabulary_has_the_same_triples(self):
        from rdflib.compare import isomorphic
        other = Graph().parse(ROOT / "jsonld" / "terms.jsonld", format="json-ld")
        self.assertTrue(isomorphic(self.graph, other))

    def test_turtle_header_comment(self):
        head = (ROOT / "jsonld" / "terms.ttl").read_text(encoding="utf-8").split("@prefix")[0]
        self.assertIn("Generated by scripts/make_jsonld.py", head)
        self.assertIn("do not edit", head)
        self.assertIn("raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/", head)
        self.assertIn("https://w3id.org/fair-bioheaders/fhr/vX.Y.Z/jsonld/", head)
        self.assertIn("never change", head)

    def test_terms_md_has_one_heading_per_term(self):
        headings = re.findall(r"^### (.+)$", self.terms_md, flags=re.M)
        self.assertEqual(sorted(headings), sorted(CLASSES | PROPERTIES))
        self.assertEqual(len(headings), len(set(headings)))
        for name in CLASSES | PROPERTIES:
            self.assertIn(f"`{FHR[name]}`", self.terms_md)


def walk_nodes(value):
    """Yield every node object (a dict with properties) of expanded JSON-LD."""
    if isinstance(value, list):
        for item in value:
            yield from walk_nodes(item)
    elif isinstance(value, dict):
        if "@value" in value:
            return
        if "@list" in value:
            yield from walk_nodes(value["@list"])
            return
        yield value
        for key, item in value.items():
            if not key.startswith("@"):
                yield from walk_nodes(item)


def values(value):
    """Yield value objects of expanded JSON-LD."""
    if isinstance(value, list):
        for item in value:
            yield from values(item)
    elif isinstance(value, dict):
        if "@value" in value:
            yield value
            return
        for key, item in value.items():
            if key != "@context":
                yield from values(item)


class SchemaOrg:
    """The pinned schema.org v30.1 subset plus the FHR vocabulary's class links."""

    def __init__(self, graph):
        data = json.loads(SUBSET.read_text(encoding="utf-8"))
        self.terms = {str(SDO) + name: entry for name, entry in data["terms"].items()}
        self.parents = {iri: {str(SDO) + parent for parent in entry.get("subClassOf", [])}
                        for iri, entry in self.terms.items()}
        for child, parent in graph.subject_objects(RDFS.subClassOf):
            self.parents.setdefault(str(child), set()).add(str(parent))

    def ancestors(self, iri):
        seen, todo = set(), [iri]
        while todo:
            current = todo.pop()
            if current not in seen:
                seen.add(current)
                todo.extend(self.parents.get(current, ()))
        return seen

    def problems(self, expanded):
        found = []
        for node in walk_nodes(expanded):
            types = node.get("@type", [])
            classes = set().union(*(self.ancestors(t) for t in types)) if types else set()
            for key in node:
                if key.startswith("@"):
                    continue
                if key in BIOSCHEMAS_TERMS or key.startswith(str(FHR)):
                    continue
                if not key.startswith(str(SDO)):
                    found.append(f"{key}: not an allowed vocabulary")
                elif key not in self.terms:
                    found.append(f"{key}: not in schema.org v30.1")
                elif not {str(SDO) + d for d in self.terms[key]["domainIncludes"]} & classes:
                    found.append(f"{key}: domain does not include {sorted(types)}")
            for kind in types:
                if kind.startswith(str(SDO)) and kind not in self.terms:
                    found.append(f"{kind}: class not in schema.org v30.1")
                elif not (kind.startswith(str(SDO)) or kind.startswith(str(FHR))):
                    found.append(f"{kind}: type not in an allowed vocabulary")
        for value in values(expanded):
            datatype = value.get("@type")
            if datatype and not datatype.startswith("http://www.w3.org/2001/XMLSchema#"):
                found.append(f"{datatype}: datatype outside xsd:")
        return found


@unittest.skipIf(pyld is None, "PyLD is not installed: pip install -r requirements-jsonld.txt")
class ExpansionVocabularyTests(unittest.TestCase):
    """SC-003: expanded records use schema.org (in its domains), FHR or rdf: terms."""

    @classmethod
    def setUpClass(cls):
        cls.graph = Graph().parse(ROOT / "jsonld" / "terms.ttl", format="turtle")
        cls.schemaorg = SchemaOrg(cls.graph)
        cls.records = records()

    def expand(self, document):
        return pyld.expand(document, {"documentLoader": loader})

    def test_subset_fixture(self):
        data = json.loads(SUBSET.read_text(encoding="utf-8"))
        self.assertIn("CC BY-SA 3.0", data["_source"])
        self.assertIn("v30.1", data["_source"])
        context = json.loads(make_jsonld.CONTEXT_PATH.read_text())
        used = {name[4:] for name in re.findall(r'"(sdo:[A-Za-z]+)"', json.dumps(context))}
        self.assertEqual(used - set(data["terms"]), set())
        for name in ("Thing", "CreativeWork", "StructuredValue", "Intangible", "Text", "URL",
                     "Number", "Integer", "Date", "DateTime"):
            self.assertIn(name, data["terms"])
        self.assertTrue(data["terms"]["Taxon"]["pending"])
        self.assertFalse(data["terms"]["Dataset"]["pending"])

    def test_every_record_uses_allowed_terms_in_their_domains(self):
        for name, record in self.records.items():
            with self.subTest(record=name):
                expanded = self.expand(make_jsonld.to_jsonld(record))
                self.assertEqual(self.schemaorg.problems(expanded), [])
                predicates = {key for node in walk_nodes(expanded) for key in node
                              if not key.startswith("@")}
                for predicate in predicates:
                    self.assertTrue(predicate.startswith((str(SDO), str(FHR))), predicate)

    def test_maintainer_decision_output_uses_allowed_terms(self):
        record = copy.deepcopy(self.records["example.fhr.json"])
        record["documentation"] = "https://example.org/genome/README"
        record["assemblyAuthor"].append({"name": "Example organization", "uri": ROR})
        expanded = self.expand(make_jsonld.to_jsonld(record, export=EXPORT))
        self.assertEqual(self.schemaorg.problems(expanded), [])

    def test_rdf_terms_after_conversion(self):
        quads = pyld.to_rdf(make_jsonld.to_jsonld(self.records["example.fhr.json"]),
                            {"documentLoader": loader, "format": "application/n-quads"})
        for line in quads.splitlines():
            predicate = line.split(" ")[1][1:-1]
            self.assertTrue(predicate.startswith((str(SDO), str(FHR))) or predicate in ALLOWED_RDF,
                            predicate)

    def test_domain_violation_is_rejected(self):
        node = [{"@type": [str(SDO) + "Dataset"],
                 str(SDO) + "relatedLink": [{"@id": "https://example.org/"}]}]
        self.assertEqual(self.schemaorg.problems(node),
                         [f"{SDO}relatedLink: domain does not include ['{SDO}Dataset']"])
        self.assertTrue(self.schemaorg.problems([{"@type": [str(SDO) + "Dataset"],
                                                  "http://purl.org/dc/terms/title": "x"}]))


if __name__ == "__main__":
    unittest.main()
