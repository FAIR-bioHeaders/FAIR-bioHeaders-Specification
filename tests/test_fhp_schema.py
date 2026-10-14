# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The FHP schema (specs/006-protein-header data-model.md, contracts/fhp-schema.md)."""

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

FHP_URL = "https://w3id.org/fair-bioheaders/fhp/v0.4.0"
CHECKSUM = "A" * 43 + "="
MINIMAL = {
    "schema": FHP_URL,
    "schemaVersion": "1.0",
    "proteome": "Synthetic protein set (placeholder)",
    "sourceType": "predicted",
    "taxon": {"name": "Homo sapiens", "uri": "https://identifiers.org/taxonomy:9606"},
    "version": "1.0",
    "metadataAuthor": [{"name": "Synthetic author (placeholder)"}],
    "dateCreated": "2026-10-11",
    "checksum": CHECKSUM,
}
RICH = dict(
    MINIMAL,
    derivedFrom=[{"headerType": "FHR", "checksum": CHECKSUM, "relationship": "translatedFrom"},
                 {"headerType": "FHGFF3", "checksum": CHECKSUM,
                  "relationship": "translatedFrom", "accessionID": {"name": "x"}}],
    source=[{"name": "UniProtKB", "release": "2026_03", "setIdentifier": "UP000005640",
             "url": "https://www.uniprot.org/proteomes/UP000005640",
             "assemblyAccession": "GCA_000001405.29", "sequenceCount": 3,
             "description": "Reviewed entries"}],
    geneticCode=1,
    isoformPolicy="longestPerGene",
    predictionSoftware=[{"name": "ExamplePredictor", "version": "1.0",
                         "uri": "https://example.org/predictor",
                         "commandLineOption": ["--species", "human"]}],
    predictionProtocol="https://example.org/protocol",
    sequenceStats={"sequenceCount": 3, "geneCount": 2, "totalResidues": 60},
    completeness={"lineageDataset": "primates_odb10", "buscoVersion": "5.8.3",
                  "mode": "proteins", "completeSingle": 1, "completeDuplicated": 0,
                  "fragmented": 0, "missing": 1, "total": 2},
    documentation="Synthetic record for tests",
)


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


DELETE = object()
REJECTED = [
    ("proteome", DELETE, "proteome is required"),
    ("sourceType", DELETE, "sourceType is required"),
    ("sourceType", "curated", "curated is not an FHP source type"),
    ("schema", "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json",
     "an FHR schema URL is not an FHP schema URL"),
    ("schema", "https://example.org/fhp.json", "other hosts are not FHP schema URLs"),
    ("schemaVersion", 1, "schemaVersion is the string 1.0"),
    ("schemaVersion", 1.0, "schemaVersion is the string 1.0, not a number"),
    ("schemaVersion", "1", "MAJOR.MINOR"),
    ("schemaVersion", "1.1", "FHP 1.0 accepts only 1.0"),
    ("schemaVersion", "2.0", "FHR's version is not FHP's"),
    ("schema", "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/"
     "0123abc/fhp.json", "only main and release tags are schema refs"),
    ("schema", "https://w3id.org/fair-bioheaders/fhp/v0.4", "a release tag has three numbers"),
    ("genome", "A genome", "FHR-only key"),
    ("masking", "not-masked", "FHR-only key"),
    ("vitalStats", {"N50": 1}, "FHR-only key"),
    ("unknownKey", 1, "unknown root key"),
    ("documentation", None, "null is not a value"),
    ("taxon.extra", 1, "Taxon is closed in FHP"),
    ("metadataAuthor.0.email", "x@example.org", "Author is closed in FHP"),
    ("derivedFrom.0.checksum", DELETE, "derivedFrom needs a checksum"),
    ("derivedFrom.0.relationship", "encodes", "unknown relationship"),
    ("derivedFrom.0.headerType", "FHX", "unknown header type"),
    ("derivedFrom.1.accessionID.extra", 1, "AccessionID is closed in FHP"),
    ("source.0.name", DELETE, "a source needs a name"),
    ("source.0.extra", 1, "Source is closed"),
    ("source.0.sequenceCount", -1, "negative count"),
    ("geneticCode", 0, "below the table range"),
    ("geneticCode", 7, "unused table ID"),
    ("geneticCode", 8, "unused table ID"),
    ("geneticCode", 17, "unused table ID"),
    ("geneticCode", 20, "unused table ID"),
    ("geneticCode", 34, "above the table range"),
    ("geneticCode", 1.5, "not an integer"),
    ("isoformPolicy", "longest", "not an isoform policy value"),
    ("predictionSoftware.0.name", DELETE, "software needs a name"),
    ("predictionSoftware.0.commandLineOption", "--x", "options are a list"),
    ("predictionProtocol", "not a uri", "protocol is a URI"),
    ("sequenceStats.sequenceCount", -1, "negative count"),
    ("sequenceStats.extra", 1, "SequenceStats is closed"),
    ("completeness.lineageDataset", "primates", "lineage dataset without its version"),
    ("completeness.lineageDataset", DELETE, "lineage dataset required"),
    ("completeness.missing", DELETE, "every count is required"),
    ("completeness.total", 0, "total is at least 1"),
    ("completeness.mode", "protein", "not a BUSCO mode"),
]
ACCEPTED = [
    ("schema", "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhp.json",
     "the raw-main URL"),
    ("schema", "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/v0.4.0/fhp.json",
     "a release's raw tag URL"),
    ("schema", "https://w3id.org/fair-bioheaders/fhp/v0.4.0/", "w3id with a trailing slash"),
    ("sourceType", "database", "each source type"),
    ("sourceType", "mixed", "each source type"),
    ("geneticCode", 6, "range edges"),
    ("geneticCode", 9, "range edges"),
    ("geneticCode", 16, "range edges"),
    ("geneticCode", 21, "range edges"),
    ("geneticCode", 33, "range edges"),
    ("isoformPolicy", "all", "each isoform policy"),
    ("isoformPolicy", "canonicalPerGene", "each isoform policy"),
    ("derivedFrom.0.relationship", "filteredFrom", "filtered from another FHP file"),
    ("derivedFrom.0.headerType", "FHT", "translated from a transcriptome"),
    ("completeness.lineageDataset", "ascomycota_odb12", "another lineage version"),
    ("completeness.total", 13780, "counts that need not add up are not checked"),
]


class FHPSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.published = json.loads((ROOT / "fhp.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.published, format_checker=FormatChecker())

    def errors(self, record):
        return list(self.validator.iter_errors(record))

    def test_published_schema_is_the_generator_output(self):
        self.assertEqual(self.published, generator.generate_fhp())
        Draft202012Validator.check_schema(self.published)

    def test_required_fields(self):
        self.assertEqual(self.published["required"], [
            "schema", "schemaVersion", "proteome", "sourceType", "taxon", "version",
            "metadataAuthor", "dateCreated", "checksum"])

    def test_minimal_and_rich_records_are_valid(self):
        self.assertEqual(self.errors(MINIMAL), [])
        self.assertEqual(self.errors(RICH), [])

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
            if definition.get("type") == "object":
                with self.subTest(definition=name):
                    self.assertIs(definition.get("additionalProperties"), False)
        self.assertIs(self.published.get("additionalProperties"), False)

    def test_no_fhr_only_keys(self):
        fhr = json.loads((ROOT / "fhr.json").read_text(encoding="utf-8"))
        fhr_only = {"genome", "genomeSynonym", "assemblyAuthor", "instrument", "masking",
                    "vitalStats", "assemblySoftware", "assemblyProtocol", "seqcol_id"}
        self.assertLessEqual(fhr_only, set(fhr["properties"]))
        self.assertEqual(fhr_only & set(self.published["properties"]), set())

    def test_fhr_schema_does_not_accept_fhp_records(self):
        fhr = json.loads((ROOT / "fhr.json").read_text(encoding="utf-8"))
        self.assertTrue(list(Draft202012Validator(fhr).iter_errors(MINIMAL)))

    def test_fhr_generation_is_unchanged(self):
        # FHP must not change FHR: the generated FHR schema closes the core
        # objects as v0.4 does and has no FHP keys.
        fhr = generator.generate()
        for name in ("Taxon", "Author", "AccessionID"):
            self.assertIs(fhr["$defs"][name]["additionalProperties"], False)
        self.assertNotIn("proteome", fhr["properties"])
        self.assertNotIn("FHP", fhr["$defs"])


class FHPExampleTests(unittest.TestCase):
    """The FHP examples (spec FR-016, SC-001)."""

    @classmethod
    def setUpClass(cls):
        schema = json.loads((ROOT / "fhp.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(schema, format_checker=FormatChecker())
        cls.examples = {}
        for path in sorted((ROOT / "examples" / "fhp").glob("*.fhp.*")):
            if path.suffix in {".json", ".yaml"}:
                text = path.read_text(encoding="utf-8")
                cls.examples[path.name] = (json.loads(text) if path.suffix == ".json"
                                           else yaml.safe_load(text))

    def test_examples_are_valid(self):
        self.assertEqual(len(self.examples), 6)
        for name, record in self.examples.items():
            with self.subTest(example=name):
                self.assertEqual(list(self.validator.iter_errors(record)), [])

    def test_minimal_examples_add_only_two_fields(self):
        core_required = {"schema", "schemaVersion", "taxon", "version", "metadataAuthor",
                         "dateCreated", "checksum"}
        for kind in ("predicted", "database", "mixed"):
            record = self.examples[f"minimal-{kind}.fhp.json"]
            with self.subTest(kind=kind):
                self.assertEqual(record["sourceType"], kind)
                self.assertLessEqual(set(record) - core_required,
                                     {"proteome", "sourceType", "source"})

    def test_combined_fasta_example(self):
        data = (ROOT / "examples" / "fhp" / "example.fhp.fasta").read_bytes()
        stated, computed = check_conformance.fhr_checksum(data, "fhp-fasta")
        self.assertEqual(stated, computed)
        header = "\n".join(line[2:] for line in data.decode("utf-8").splitlines()
                           if line.startswith(";~"))
        self.assertEqual(list(self.validator.iter_errors(yaml.safe_load(header))), [])
        for residue in ("*", "U", "O", "B", "Z", "J", "X"):
            self.assertIn(residue, data.decode("utf-8").split("\n>", 1)[1])


if __name__ == "__main__":
    unittest.main()
