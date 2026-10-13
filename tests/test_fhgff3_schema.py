# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The FHGFF3 schema (specs/007-gff3-header data-model.md, contracts/fhgff3-schema.md)."""

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_conformance  # noqa: E402

spec = importlib.util.spec_from_file_location("generator", ROOT / "json-schema-generator.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

URL = "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhgff3.json"
CHECKSUM = "A" * 43 + "="
GENOME = {"headerType": "FHR", "checksum": "B" * 43 + "=", "relationship": "annotates"}
REFERENCE = {"accession": "SYNTHETIC_ASSEMBLY.1", "seqcol_id": "S" * 32}
MINIMAL = {
    "schema": URL,
    "schemaVersion": 1,
    "annotation": "Synthetic annotation (placeholder)",
    "taxon": {"name": "Homo sapiens", "uri": "https://identifiers.org/taxonomy:9606"},
    "version": "1.0",
    "metadataAuthor": [{"name": "Synthetic author (placeholder)"}],
    "dateCreated": "2026-10-13",
    "derivedFrom": [GENOME],
    "checksum": CHECKSUM,
}
RICH = dict(
    MINIMAL,
    genomeReference=dict(REFERENCE, assemblyName="SyntheticAssembly1"),
    derivedFrom=[GENOME, {"headerType": "FHT", "checksum": CHECKSUM,
                          "relationship": "filteredFrom"}],
    source=[{"name": "Synthetic evidence set", "setIdentifier": "SET-1",
             "description": "RNA-seq evidence"}],
    annotationSoftware=[{"name": "ExamplePredictor", "version": "1.0",
                         "uri": "https://example.org/predictor",
                         "commandLineOption": ["--species", "human"]}],
    annotationProtocol="https://example.org/protocol",
    soVersion="2026-08-07",
    featureCounts=[{"featureType": "gene", "count": 2}, {"featureType": "SO:0000234", "count": 3}],
    completeness={"lineageDataset": "primates_odb10", "completeSingle": 1,
                  "completeDuplicated": 0, "fragmented": 0, "missing": 1, "total": 2},
    documentation="Synthetic record for tests",
)
DELETE = object()


def changed(path, value, base=RICH):
    record = copy.deepcopy(base)
    *parents, last = path.split(".")
    node = record
    for part in parents:
        node = node[int(part)] if part.isdigit() else node[part]
    if value is DELETE:
        del node[int(last) if last.isdigit() else last]
    else:
        node[int(last) if last.isdigit() else last] = value
    return record


def without(record, *keys):
    return {key: value for key, value in record.items() if key not in keys}


REJECTED = [
    ("annotation", DELETE, "annotation is required"),
    ("schema", "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhp.json",
     "an FHP schema URL is not an FHGFF3 schema URL"),
    ("genomeReference.seqcol_id", DELETE, "half a genome reference"),
    ("genomeReference.accession", DELETE, "half a genome reference"),
    ("genomeReference.accession", "GCA 1", "accession with whitespace"),
    ("genomeReference.seqcol_id", "short", "SeqCol digest of the wrong length"),
    ("genomeReference.extra", "x", "closed genome reference"),
    ("featureCounts.0.count", -1, "negative count"),
    ("featureCounts.0.featureType", "five prime UTR", "feature type with whitespace"),
    ("featureCounts.0.extra", 1, "closed feature count"),
    ("derivedFrom.0.relationship", "encodes", "relationship outside the vocabulary"),
    ("annotationSoftware.0.name", DELETE, "software without a name"),
    ("sourceType", "predicted", "FHP-only key"),
    ("genome", "x", "FHR-only key"),
    ("soVersion", None, "null is not a value"),
]
ACCEPTED = [
    ("soVersion", "2.5.3", "an older numbered SO release"),
    ("featureCounts.0.featureType", "SO:0000704", "an SO accession as the type"),
    ("genomeReference.assemblyName", DELETE, "assemblyName is optional"),
]
LINKS = {
    "checksum link only": (without(MINIMAL), True),
    "reference only": (dict(without(MINIMAL, "derivedFrom"), genomeReference=REFERENCE), True),
    "both forms": (dict(MINIMAL, genomeReference=REFERENCE), True),
    "reference and another parent": (
        dict(without(MINIMAL, "derivedFrom"), genomeReference=REFERENCE,
             derivedFrom=[{"headerType": "FHGFF3", "checksum": CHECKSUM,
                           "relationship": "filteredFrom"}]), True),
    "neither": (without(MINIMAL, "derivedFrom"), False),
    "a parent that is not the genome": (
        dict(MINIMAL, derivedFrom=[dict(GENOME, relationship="filteredFrom")]), False),
    "two annotates items": (
        dict(MINIMAL, derivedFrom=[GENOME, dict(GENOME, checksum=CHECKSUM)]), False),
    "annotates an FHP file": (
        dict(MINIMAL, derivedFrom=[dict(GENOME, headerType="FHP")]), False),
    "annotates an FHP file beside a reference": (
        dict(MINIMAL, genomeReference=REFERENCE,
             derivedFrom=[dict(GENOME, headerType="FHP")]), False),
    "annotates without a checksum": (
        dict(MINIMAL, derivedFrom=[without(GENOME, "checksum")]), False),
}


class FHGFF3SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.published = json.loads((ROOT / "fhgff3.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.published, format_checker=FormatChecker())

    def errors(self, record):
        return list(self.validator.iter_errors(record))

    def test_published_schema_is_the_generator_output(self):
        self.assertEqual(self.published, generator.generate_fhgff3())
        Draft202012Validator.check_schema(self.published)

    def test_required_fields(self):
        self.assertEqual(self.published["required"], [
            "schema", "schemaVersion", "annotation", "taxon", "version", "metadataAuthor",
            "dateCreated", "checksum"])

    def test_minimal_and_rich_records_are_valid(self):
        self.assertEqual(self.errors(MINIMAL), [])
        self.assertEqual(self.errors(RICH), [])

    def test_genome_link_rule(self):
        for name, (record, valid) in LINKS.items():
            with self.subTest(case=name):
                self.assertEqual(not self.errors(record), valid)

    def test_genome_link_rule_is_on_the_root_and_the_class(self):
        for node in (self.published, self.published["$defs"]["FHGFF3"]):
            self.assertIn("anyOf", node)
            self.assertIn("allOf", node)

    def test_rejected_values(self):
        for path, value, reason in REJECTED:
            with self.subTest(path=path, reason=reason):
                self.assertTrue(self.errors(changed(path, value)), reason)

    def test_accepted_values(self):
        for path, value, reason in ACCEPTED:
            with self.subTest(path=path, reason=reason):
                self.assertEqual(self.errors(changed(path, value)), [], reason)

    def test_every_object_is_closed(self):
        for name, definition in self.published["$defs"].items():
            if definition.get("type") == "object" and "properties" in definition \
                    and not name.startswith("Annotates"):
                with self.subTest(definition=name):
                    self.assertIs(definition.get("additionalProperties"), False)
        self.assertIs(self.published.get("additionalProperties"), False)

    def test_no_fhr_or_fhp_only_keys(self):
        fhr = json.loads((ROOT / "fhr.json").read_text(encoding="utf-8"))
        fhp = json.loads((ROOT / "fhp.json").read_text(encoding="utf-8"))
        own = set(self.published["properties"])
        self.assertEqual((set(fhr["properties"]) - set(fhp["properties"])) & own, set())
        self.assertEqual({"proteome", "sourceType", "geneticCode", "isoformPolicy",
                          "predictionSoftware", "sequenceStats"} & own, set())
        self.assertNotIn("seqcol_id", own)

    def test_other_schemas_do_not_accept_fhgff3_records(self):
        for name in ("fhr.json", "fhp.json"):
            schema = json.loads((ROOT / name).read_text(encoding="utf-8"))
            with self.subTest(schema=name):
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(MINIMAL)))

    def test_fhr_and_fhp_are_unchanged(self):
        # FHGFF3 and the shared module must not change FHR or FHP.
        fhr = generator.generate()
        self.assertNotIn("annotation", fhr["properties"])
        self.assertNotIn("GenomeReference", fhr["$defs"])
        published_fhp = json.loads((ROOT / "fhp.json").read_text(encoding="utf-8"))
        self.assertEqual(generator.generate_fhp(), published_fhp)


class FHGFF3ExampleTests(unittest.TestCase):
    """The FHGFF3 examples (spec FR-018, SC-001, SC-005)."""

    EXAMPLES = ROOT / "examples" / "fhgff3"

    @classmethod
    def setUpClass(cls):
        schema = json.loads((ROOT / "fhgff3.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(schema, format_checker=FormatChecker())

    def metadata(self, name):
        data = (self.EXAMPLES / name).read_bytes()
        stated, computed = check_conformance.fhr_checksum(data, "fhgff3")
        header = "\n".join(line[2:] for line in data.decode("utf-8").splitlines()
                           if line.startswith("#~"))
        return data, stated, computed, yaml.safe_load(header)

    def test_metadata_examples_are_valid(self):
        names = ["annotation.fhgff3.yaml", "minimal-reference.fhgff3.json", "rich.fhgff3.yaml"]
        for name in names:
            text = (self.EXAMPLES / name).read_text(encoding="utf-8")
            record = json.loads(text) if name.endswith(".json") else yaml.safe_load(text)
            with self.subTest(example=name):
                self.assertEqual(list(self.validator.iter_errors(record)), [])

    def test_minimal_reference_adds_only_the_subject_and_the_link(self):
        record = json.loads((self.EXAMPLES / "minimal-reference.fhgff3.json").read_text())
        core = {"schema", "schemaVersion", "taxon", "version", "metadataAuthor",
                "dateCreated", "checksum", "documentation"}
        self.assertEqual(set(record) - core, {"annotation", "genomeReference"})

    def test_headed_examples(self):
        genome = (self.EXAMPLES / "genome.fhr.fasta").read_bytes()
        genome_checksum = check_conformance.fhr_checksum(genome, "fasta")
        self.assertEqual(genome_checksum[0], genome_checksum[1])
        for name in ("annotation.fhgff3.gff3", "embedded-fasta.fhgff3.gff3",
                     "stale-parent.fhgff3.gff3", "header-invalid.fhgff3.gff3"):
            data, stated, computed, record = self.metadata(name)
            with self.subTest(example=name):
                self.assertTrue(data.startswith(b"##gff-version 3\n#~"))
                self.assertEqual(stated, computed)
                errors = list(self.validator.iter_errors(record))
                if name == "header-invalid.fhgff3.gff3":
                    self.assertTrue(errors)
                    continue
                self.assertEqual(errors, [])
                link = record["derivedFrom"][0]["checksum"]
                if name == "stale-parent.fhgff3.gff3":
                    self.assertNotEqual(link, genome_checksum[1])
                else:
                    self.assertEqual(link, genome_checksum[1])
        _, _, _, record = self.metadata("annotation.fhgff3.gff3")
        companion = yaml.safe_load((self.EXAMPLES / "annotation.fhgff3.yaml").read_text())
        self.assertEqual(record, companion)
        self.assertIn(b"##FASTA", (self.EXAMPLES / "embedded-fasta.fhgff3.gff3").read_bytes())

    def test_plain_example_has_no_header(self):
        data = (self.EXAMPLES / "no-header.gff3").read_bytes()
        self.assertTrue(data.startswith(b"##gff-version 3\n"))
        self.assertNotIn(b"#~", data)


if __name__ == "__main__":
    unittest.main()
