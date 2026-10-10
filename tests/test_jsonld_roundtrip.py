# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""JSON-LD writing and round trips (feature 011, SC-001, FR-004, FR-006, FR-007).

The reference writer is ``scripts/make_jsonld.py``. The PyLD tests are skipped
with a message when PyLD (requirements-jsonld.txt) is not installed; nothing
is fetched from the network.
"""

import copy
import json
from pathlib import Path
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import make_jsonld  # noqa: E402

try:
    from pyld import jsonld as pyld
except ImportError:  # pragma: no cover - depends on the environment
    pyld = None

PREFIXES = {"fasta": b";~", "gfa": b"#~"}
NESTED_TYPES = {"taxon": "Taxon", "accessionID": "PropertyValue", "vitalStats": "VitalStats"}
LOSSY = {"fasta-nested-checksum", "gfa-nested-checksum"}  # research R-12: taxon.checksum
ORCID = "https://orcid.org/0000-0002-1825-0097"  # ORCID's documented example iD.
ROR = "https://ror.org/05gq02987"  # A ROR iD, used only to test the typing rule.
EXPORT = {
    "id": "https://example.org/datasets/synthetic-human",
    "url": "https://example.org/genomes/synthetic-human",
    "keywords": ["genome assembly", "Homo sapiens"],
}


def header_record(path, kind):
    """Decode a vector's FHR header as scripts/check_conformance.py does."""
    prefix = PREFIXES[kind]
    text = "\n".join(
        line[len(prefix):].rstrip(b"\r\n").decode("utf-8")
        for line in path.read_bytes().splitlines(keepends=True) if line.startswith(prefix)
    )
    return yaml.safe_load(text)


def records():
    found = {
        "example.fhr.json": json.loads((ROOT / "examples/example.fhr.json").read_text()),
        "minimal.fhr.json": json.loads((ROOT / "examples/minimal.fhr.json").read_text()),
        "example.fhr.yaml": yaml.safe_load((ROOT / "examples/example.fhr.yaml").read_text()),
    }
    for kind in ("fasta", "gfa"):
        for path in sorted((ROOT / "conformance/valid").glob(f"*.fhr.{kind}")):
            found[path.name.split(".")[0]] = header_record(path, kind)
    for record in found.values():
        if hasattr(record.get("dateCreated"), "isoformat"):
            record["dateCreated"] = record["dateCreated"].isoformat()
    return found


def equal(left, right):
    """data-model section 8: key order ignored; array order and JSON types kept."""
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(map(equal, left, right))
    return type(left) is type(right) and left == right


def loader(url, options=None):
    """Bundled-only document loader: the raw-main context URL, nothing else."""
    if url == make_jsonld.RAW_MAIN_CONTEXT_URL:
        document = json.loads(make_jsonld.CONTEXT_PATH.read_text())
        return {"contextUrl": None, "documentUrl": url, "document": document}
    raise pyld.JsonLdError(f"not available offline: {url}", "jsonld.LoadDocumentError",
                           code="loading document failed")


def no_nulls_or_empty_nodes(test, value, path="$"):
    if isinstance(value, dict):
        test.assertTrue(set(value) - {"@type"}, f"{path}: empty node")
        for key, item in value.items():
            no_nulls_or_empty_nodes(test, item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            no_nulls_or_empty_nodes(test, item, f"{path}[{index}]")
    else:
        test.assertIsNotNone(value, path)


class WriterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = records()
        cls.context = json.loads(make_jsonld.CONTEXT_PATH.read_text())["@context"]

    def test_record_set(self):
        self.assertEqual(len(self.records), 33)  # 3 examples and 30 vector headers.

    def test_writer_steps(self):
        for name, record in self.records.items():
            with self.subTest(record=name):
                document = make_jsonld.to_jsonld(record)
                self.assertEqual(list(document)[:2], ["@context", "@type"])
                self.assertEqual(document["@context"], self.context)
                self.assertEqual(document["@type"], "Dataset")
                self.assertEqual(list(document)[2:], list(record))
                for key, kind in NESTED_TYPES.items():
                    if isinstance(record.get(key), dict):
                        self.assertEqual(list(document[key])[0], "@type")
                        self.assertEqual(document[key]["@type"], kind)
                for key in ("metadataAuthor", "assemblyAuthor"):
                    for item, written in zip(record.get(key, []), document.get(key, [])):
                        self.assertEqual(list(written)[0], "@type")
                        orcid = str(item.get("uri", "")).startswith("https://orcid.org/")
                        self.assertEqual(written["@type"], "Person" if orcid else "Agent")
                software = document.get("assemblySoftware")
                if isinstance(software, list):
                    for item in software:
                        self.assertEqual(item["@type"], "SoftwareApplication")
                no_nulls_or_empty_nodes(self, {k: v for k, v in document.items()
                                               if k != "@context"})

    def test_canonical_round_trip(self):
        for name, record in self.records.items():
            with self.subTest(record=name):
                document = json.loads(json.dumps(make_jsonld.to_jsonld(record)))
                self.assertTrue(equal(make_jsonld.canonical_record(document), record))

    def test_examples_are_writer_output(self):
        for stem in ("example", "minimal"):
            with self.subTest(example=stem):
                record = json.loads((ROOT / f"examples/{stem}.fhr.json").read_text())
                text = (ROOT / f"examples/{stem}.fhr.jsonld").read_text(encoding="utf-8")
                self.assertEqual(text, make_jsonld.jsonld_text(record))

    def test_absent_optional_fields_stay_absent(self):
        minimal = self.records["minimal.fhr.json"]
        document = make_jsonld.to_jsonld(minimal)
        self.assertEqual(set(document) - {"@context", "@type"}, set(minimal))

    def test_unmapped_nested_keys(self):
        self.assertEqual(make_jsonld.unmapped_keys(self.records["fasta-nested-checksum"]),
                         ["taxon.checksum"])
        record = copy.deepcopy(self.records["example.fhr.json"])
        record["assemblyAuthor"][0]["affiliation"] = "Example institute"
        record["vitalStats"]["contigN50"] = 3
        self.assertEqual(make_jsonld.unmapped_keys(record),
                         ["assemblyAuthor[0].affiliation", "vitalStats.contigN50"])
        self.assertEqual(make_jsonld.unmapped_keys(self.records["example.fhr.json"]), [])

    def test_keyword_like_keys_are_refused(self):
        record = copy.deepcopy(self.records["example.fhr.json"])
        record["taxon"]["@id"] = "https://example.org/taxon"
        with self.assertRaisesRegex(ValueError, r"taxon\.@id"):
            make_jsonld.to_jsonld(record)


class MaintainerDecisionTests(unittest.TestCase):
    """T046 (author typing, documentation) and T048 (export context)."""

    def setUp(self):
        self.record = json.loads((ROOT / "examples/example.fhr.json").read_text())

    def test_author_typing_from_identifier(self):
        self.record["metadataAuthor"] = [{"name": "Josiah Carberry", "uri": ORCID},
                                         {"name": "Example organization", "uri": ROR},
                                         {"name": "Name only"},
                                         {"name": "Other identifier",
                                          "uri": "https://example.org/people/1"}]
        written = make_jsonld.to_jsonld(self.record)["metadataAuthor"]
        self.assertEqual([item["@type"] for item in written],
                         ["Person", "Organization", "Agent", "Agent"])
        document = json.loads(json.dumps(make_jsonld.to_jsonld(self.record)))
        self.assertTrue(equal(make_jsonld.canonical_record(document), self.record))

    def test_documentation_text_and_url(self):
        document = make_jsonld.to_jsonld(self.record)
        self.assertIn("documentation", document)
        self.assertNotIn("subjectOf", document)
        for value in ("https://example.org/genome/README", "ftp://example.org/docs/readme.txt"):
            with self.subTest(value=value):
                record = dict(self.record, documentation=value)
                document = make_jsonld.to_jsonld(record)
                self.assertNotIn("documentation", document)
                self.assertEqual(document["subjectOf"], value)
                self.assertEqual(list(document).index("subjectOf"),
                                 list(record).index("documentation") + 2)
                back = make_jsonld.canonical_record(json.loads(json.dumps(document)))
                self.assertTrue(equal(back, record))
                self.assertEqual(list(back), list(record))
        for value in ("See https://example.org/readme", "https://example.org/a b",
                      "example.org/readme", "urn:example:readme"):
            with self.subTest(text=value):
                document = make_jsonld.to_jsonld(dict(self.record, documentation=value))
                self.assertEqual(document["documentation"], value)

    def test_documentation_and_subject_of_together_are_invalid(self):
        document = make_jsonld.to_jsonld(self.record)
        document["subjectOf"] = "https://example.org/readme"
        with self.assertRaisesRegex(ValueError, "documentation"):
            make_jsonld.canonical_record(document)

    def test_without_export_context_no_bioschemas_claim(self):
        document = make_jsonld.to_jsonld(self.record)
        for key in ("@id", "keywords", "url", "conformsTo"):
            self.assertNotIn(key, document)
        self.assertEqual(make_jsonld.bioschemas_missing(document), ["@id", "keywords", "url"])

    def test_complete_export_context_claims_conformance(self):
        document = make_jsonld.to_jsonld(self.record, export=EXPORT)
        self.assertEqual(list(document)[:3], ["@context", "@type", "@id"])
        self.assertEqual(document["@id"], EXPORT["id"])
        self.assertEqual(list(document)[-3:], ["keywords", "url", "conformsTo"])
        self.assertEqual(document["keywords"], EXPORT["keywords"])
        self.assertEqual(document["url"], EXPORT["url"])
        self.assertEqual(document["conformsTo"], make_jsonld.BIOSCHEMAS_DATASET_PROFILE)
        self.assertEqual(make_jsonld.bioschemas_missing(document), [])
        warnings = []
        back = make_jsonld.canonical_record(json.loads(json.dumps(document)),
                                            warn=warnings.append)
        self.assertTrue(equal(back, self.record))
        self.assertEqual(len(warnings), 4)

    def test_incomplete_export_context_makes_no_claim(self):
        cases = {
            "keywords": dict(EXPORT, keywords=None),
            "@id": {k: v for k, v in EXPORT.items() if k != "id"},
        }
        for missing, export in cases.items():
            with self.subTest(missing=missing):
                export = {k: v for k, v in export.items() if v is not None}
                document = make_jsonld.to_jsonld(self.record, export=export)
                self.assertNotIn("conformsTo", document)
                self.assertEqual(make_jsonld.bioschemas_missing(document), [missing])
        for key, missing in (("documentation", "description"), ("identifier", "identifier"),
                             ("reuseConditions", "license")):
            with self.subTest(record_field=key):
                record = {k: v for k, v in self.record.items() if k != key}
                document = make_jsonld.to_jsonld(record, export=EXPORT)
                self.assertNotIn("conformsTo", document)
                self.assertEqual(make_jsonld.bioschemas_missing(document), [missing])
        record = dict(self.record, documentation="https://example.org/readme")
        document = make_jsonld.to_jsonld(record, export=EXPORT)
        self.assertEqual(make_jsonld.bioschemas_missing(document), ["description"])

    def test_export_context_is_validated(self):
        for export in ({"keyword": ["x"]}, {"keywords": "genome"}, {"keywords": []},
                       {"keywords": [""]}, {"url": "example.org"}, {"id": 5}, []):
            with self.subTest(export=export):
                with self.assertRaises(ValueError):
                    make_jsonld.to_jsonld(self.record, export=export)


@unittest.skipIf(pyld is None, "PyLD is not installed: pip install -r requirements-jsonld.txt")
class ProcessorTests(unittest.TestCase):
    """PyLD 3.3.0 expansion and compaction with a bundled-only loader."""

    @classmethod
    def setUpClass(cls):
        cls.records = records()
        cls.context = json.loads(make_jsonld.CONTEXT_PATH.read_text())

    def compact_back(self, record, document):
        expanded = pyld.expand(document, {"documentLoader": loader})
        compacted = pyld.compact(expanded, self.context, {"documentLoader": loader})
        back = make_jsonld.canonical_record(compacted, warn=lambda message: None)
        if isinstance(record.get("assemblySoftware"), str):  # The legacy string form.
            self.assertEqual(back["assemblySoftware"], [record["assemblySoftware"]])
            back["assemblySoftware"] = record["assemblySoftware"]
        return back

    def test_expand_and_compact_back(self):
        for name, record in self.records.items():
            with self.subTest(record=name):
                back = self.compact_back(record, make_jsonld.to_jsonld(record))
                expected = copy.deepcopy(record)
                if name in LOSSY:
                    del expected["taxon"]["checksum"]
                self.assertTrue(equal(back, expected), json.dumps(back, indent=1))

    def test_maintainer_decision_outputs_expand_and_compact_back(self):
        record = copy.deepcopy(self.records["example.fhr.json"])
        record["documentation"] = "https://example.org/genome/README"
        record["metadataAuthor"].append({"name": "Example organization", "uri": ROR})
        record["metadataAuthor"].append({"name": "Name only"})
        document = make_jsonld.to_jsonld(record, export=EXPORT)
        self.assertTrue(equal(self.compact_back(record, document), record))
        expanded = pyld.expand(document, {"documentLoader": loader})[0]
        sdo = "http://schema.org/"
        self.assertEqual(expanded["@id"], EXPORT["id"])
        self.assertEqual(expanded[sdo + "subjectOf"], [{"@id": record["documentation"]}])
        self.assertNotIn(sdo + "description", expanded)
        # documentation is a URL, so the Bioschemas description is missing: no claim.
        self.assertNotIn("http://purl.org/dc/terms/conformsTo", expanded)
        self.assertEqual(expanded[sdo + "url"], [{"@id": EXPORT["url"]}])
        self.assertEqual(expanded[sdo + "keywords"],
                         [{"@value": word} for word in EXPORT["keywords"]])
        authors = expanded["https://w3id.org/fair-bioheaders/terms#metadataAuthor"]
        self.assertEqual([a["@type"] for a in authors],
                         [[sdo + "Person"], [sdo + "Organization"],
                          ["https://w3id.org/fair-bioheaders/terms#Agent"]])
        complete = make_jsonld.to_jsonld(self.records["example.fhr.json"], export=EXPORT)
        complete_expanded = pyld.expand(complete, {"documentLoader": loader})[0]
        self.assertEqual(complete_expanded["http://purl.org/dc/terms/conformsTo"],
                         [{"@id": make_jsonld.BIOSCHEMAS_DATASET_PROFILE}])
        self.assertEqual(complete_expanded[sdo + "description"],
                         [{"@value": self.records["example.fhr.json"]["documentation"]}])

    def test_canonical_url_reference_expands_like_the_embedded_context(self):
        record = self.records["example.fhr.json"]
        embedded = make_jsonld.to_jsonld(record)
        by_url = dict(embedded, **{"@context": make_jsonld.RAW_MAIN_CONTEXT_URL})
        self.assertEqual(pyld.expand(embedded, {"documentLoader": loader}),
                         pyld.expand(by_url, {"documentLoader": loader}))

    def test_loader_refuses_other_urls(self):
        document = dict(make_jsonld.to_jsonld(self.records["minimal.fhr.json"]),
                        **{"@context": "https://schema.org/"})
        with self.assertRaises(pyld.JsonLdError):
            pyld.expand(document, {"documentLoader": loader})


    def nquads(self, document):
        return pyld.normalize(document, {"algorithm": "URDNA2015", "format": "application/n-quads",
                                         "documentLoader": loader})

    def test_general_form_vectors_mean_the_canonical_document(self):
        """Rules J3 to J5: each valid vector in another form expands to the same RDF as the
        canonical document of its expected metadata, except where J5 accepts a string for
        an IRI (a literal in RDF)."""
        manifest = json.loads((ROOT / "conformance/manifest.json").read_text())
        general = [v for v in manifest["vectors"] if v["format"] == "jsonld"
                   and v["expected"] == "valid" and {"J3", "J4", "J5"} & set(v["rules"])]
        self.assertEqual(len(general), 4)
        for vector in general:
            document = json.loads((ROOT / "conformance" / vector["file"]).read_text())
            canonical = make_jsonld.to_jsonld(vector["metadata"])
            with self.subTest(vector=vector["id"]):
                self.assertFalse(make_jsonld.is_canonical(document))
                same = self.nquads(document) == self.nquads(canonical)
                self.assertEqual(same, vector["id"] != "jsonld-iri-as-string")

    def test_general_form_invalid_vectors(self):
        def read(name):
            return json.loads((ROOT / f"conformance/invalid/{name}.fhr.jsonld").read_text())

        def expand(name):
            return pyld.expand(read(name), {"documentLoader": loader})

        with self.assertRaises(pyld.JsonLdError):
            expand("jsonld-remote-context")
        self.assertEqual(len(expand("jsonld-two-nodes")), 2)
        self.assertIn("http://schema.org/keywords", expand("jsonld-unknown-term")[0])
        self.assertEqual(len(expand("jsonld-two-genome-values")[0]["http://schema.org/name"]), 2)
        self.assertEqual(expand("jsonld-flattened")[0]["http://schema.org/about"],
                         [{"@id": "https://identifiers.org/taxonomy:9606"}])
        self.assertIn("@id", expand("jsonld-root-id")[0])


if __name__ == "__main__":
    unittest.main()
