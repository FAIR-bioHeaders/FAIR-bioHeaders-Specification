"""v0.4 constraint tightening (issue #35, spec 002).

Each value from the spec 002 Background table, and the other forms the v0.4
schema now rejects, must fail both the published fhr.json and the schema
generated from LinkML. Real edge forms and every existing example must still
validate. Syntactic checks do not prove that a DOI or ORCID resolves or that a
checksum matches a file.
"""

import copy
import importlib.util
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "generator", ROOT / "json-schema-generator.py"
)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def setting(path, value):
    """Return a function that sets a nested key (dotted path) on an instance."""
    def apply(instance):
        *parents, last = path.split(".")
        node = instance
        for part in parents:
            node = node[int(part)] if part.isdigit() else node.setdefault(part, {})
        node[int(last) if last.isdigit() else last] = value
    return apply


# (field path, rejected value, reason)
REJECTED = [
    # spec 002 Background table
    ("masking", "xx-unknown-yy", "unanchored masking pattern"),
    ("scholarlyArticle", "10xfoo", "unescaped dot in DOI pattern"),
    ("identifier", ["no colon here"], "identifier without a prefix"),
    ("identifier", ["has a : somewhere"], "unanchored identifier pattern"),
    ("taxon.uri", "xhttps://identifiers.org/taxonomy:9606", "junk before taxon URL"),
    ("metadataAuthor.0.uri", "https://orcid.org/0000-0002-5719-4024junk",
     "trailing junk after ORCID"),
    ("checksum", "=" * 44, "44 '=' characters"),
    ("schemaVersion", 99, "unbounded schemaVersion"),
    ("schemaVersion", 1, "the v0.3 number 1 (schemaVersion is the string 2.0 from v0.4)"),
    ("schemaVersion", 1.0, "the v0.3 number 1.0"),
    ("vitalStats.N50", -1, "negative N50"),
    ("vitalStats.n50", 16, "vitalStats typo key"),
    # further forms rejected by the same tightenings
    ("masking", "unknown-masked", "masking value with a suffix"),
    ("masking", "Soft-masked", "masking values are case-sensitive"),
    ("scholarlyArticle", "10.1093", "DOI without suffix"),
    ("scholarlyArticle", "https://doi.org/10.1093/bib/bbae122", "DOI resolver URL"),
    ("scholarlyArticle", "10.1093/bib/bbae122 trailing", "DOI with whitespace"),
    ("identifier", [":TC010103"], "empty identifier prefix"),
    ("identifier", ["beetlebase:"], "empty identifier accession"),
    ("taxon.uri", "https://identifiers.org/taxonomy:9606/extra", "trailing junk on taxon URL"),
    ("taxon.uri", "https://identifiersXorg/taxonomy:9606", "unescaped dot in taxon URL"),
    ("metadataAuthor.0.uri", "https://orcidXorg/0000-0002-5719-4024",
     "unescaped dot in ORCID URL"),
    ("metadataAuthor.0.uri", "http://orcid.org/0000-0002-5719-4024",
     "ORCID URIs use https (unchanged from v0.3)"),
    ("metadataAuthor.0.uri", "https://orcid.org/0000-0002-5719-402", "short ORCID"),
    ("checksum", "A" * 44, "no base64 padding"),
    ("checksum", "A" * 42 + "==", "padding of a 31-byte value"),
    ("checksum", "A" * 42 + "=A", "padding before the last character"),
    ("checksum", "A" * 42 + "-=", "base64url alphabet"),
    ("checksum", "A" * 43 + "\n", "trailing newline"),
    ("schemaVersion", 2, "a number, not the string 2.0"),
    ("schemaVersion", 2.0, "the number 2.0, as unquoted YAML 2.0 reads"),
    ("schemaVersion", "2", "MAJOR.MINOR has two parts"),
    ("schemaVersion", "2.1", "FHR 2.0 accepts only 2.0"),
    ("schemaVersion", "02.0", "no leading zeros"),
    ("schemaVersion", 1.5, "fractional schemaVersion"),
    ("schemaVersion", "1", "the old version as a string"),
    ("vitalStats.gcContent", 101, "gcContent above 100"),
    ("taxon.url", "https://identifiers.org/taxonomy:9606", "taxon typo key"),
    ("metadataAuthor.0.orcid", "https://orcid.org/0000-0002-5719-4024",
     "metadataAuthor typo key"),
    ("assemblyAuthor.0.email", "someone@example.org", "assemblyAuthor unknown key"),
    ("accessionID.uri", "https://example.org/accession", "accessionID typo key"),
    ("assemblySoftware.0.commandline", ["-t"], "assemblySoftware typo key"),
    ("metadataAuthor.0.nameType", "Person", "nameType uses DataCite values, not schema.org"),
    ("metadataAuthor.0.nameType", "personal", "nameType values are case-sensitive"),
    ("assemblyAuthor.0.nameType", "", "empty nameType"),
]
for name in ("L50", "N50", "L90", "N90", "totalBasePairs", "numberContigs",
             "numberScaffolds", "scaffoldN50", "scaffoldN90", "scaffoldL50",
             "scaffoldL90"):
    REJECTED.append((f"vitalStats.{name}", -1, f"negative {name}"))
    REJECTED.append((f"vitalStats.{name}", 1.5, f"non-integer {name}"))

# (field path, accepted value, reason): real edge forms that must stay valid
ACCEPTED = [
    ("schemaVersion", "2.0", "the v0.4 contract version"),
    ("metadataAuthor.0.uri", "https://orcid.org/0000-0002-1694-233X", "ORCID X check digit"),
    ("scholarlyArticle", "10.5281/zenodo.6762550", "Zenodo DOI"),
    ("scholarlyArticle", "10.1101/2020.03.22.002386", "bioRxiv preprint DOI"),
    ("scholarlyArticle", "10.1000.10/123456", "DOI prefix with a subdivision"),
    ("scholarlyArticle", "10.1002/(SICI)1097-4636(199709)36:3<408::AID-JBM16>3.0.CO;2-I",
     "SICI DOI with punctuation"),
    ("identifier", ["GO:0008150", "NCBITaxon:9606", "ENA.embl:GCA_000001405.29"],
     "uppercase and dotted CURIE prefixes"),
    ("identifier", ["https://example.org/genome"], "URL (scheme as prefix)"),
    ("checksum", "LDnzswnZNe5GgEl5Xa1Sb8V4HAQZitxCy6Ao2jmb4o0=", "real digest"),
    ("checksum", "+/" * 21 + "A=", "base64 '+' and '/'"),
    ("vitalStats.gcContent", 0.42, "0.42 percent is a legitimate low percentage"),
    ("vitalStats.gcContent", 0, "lower bound"),
    ("vitalStats.gcContent", 100, "upper bound"),
    ("vitalStats.N50", 0, "zero statistic"),
    ("vitalStats.scaffoldN50", 50000000, "scaffold N50"),
    ("vitalStats.scaffoldN90", 1000000, "scaffold N90"),
    ("vitalStats.scaffoldL50", 12, "scaffold L50"),
    ("vitalStats.scaffoldL90", 40, "scaffold L90"),
    ("masking", "unknown", "each masking value"),
    ("masking", "not-masked", "each masking value"),
    ("masking", "hard-masked", "each masking value"),
    ("masking", "repeat-masked", "each masking value"),
    ("metadataAuthor.0.nameType", "Personal", "optional author nameType"),
    ("assemblyAuthor.0.nameType", "Organizational",
     "nameType with an ORCID iD; accepted, and nameType wins for typing (docs/JSONLD.md)"),
]


def load(path):
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)


class V04TighteningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.published = json.loads((ROOT / "fhr.json").read_text())
        cls.generated = generator.generate()
        cls.validators = {
            name: Draft202012Validator(schema, format_checker=FormatChecker())
            for name, schema in (("fhr.json", cls.published), ("LinkML", cls.generated))
        }
        cls.example = load(ROOT / "examples/example.fhr.json")

    def instance(self, path, value):
        instance = copy.deepcopy(self.example)
        setting(path, value)(instance)
        return instance

    def test_rejected_values_fail_both_schemas_naming_the_field(self):
        for path, value, reason in REJECTED:
            instance = self.instance(path, value)
            top = path.split(".")[0]
            for name, validator in self.validators.items():
                with self.subTest(path=path, value=value, reason=reason, schema=name):
                    errors = list(validator.iter_errors(instance))
                    self.assertTrue(errors, "accepted")
                    self.assertTrue(
                        any(error.absolute_path and error.absolute_path[0] == top
                            for error in errors),
                        [error.message for error in errors],
                    )

    def test_edge_forms_stay_valid_in_both_schemas(self):
        for path, value, reason in ACCEPTED:
            instance = self.instance(path, value)
            for name, validator in self.validators.items():
                with self.subTest(path=path, value=value, reason=reason, schema=name):
                    self.assertEqual(
                        [error.message for error in validator.iter_errors(instance)], []
                    )

    def test_legacy_software_string_stays_valid(self):
        for validator in self.validators.values():
            validator.validate(self.instance("assemblySoftware", "hifiasm"))

    def test_every_example_still_validates(self):
        examples = sorted(
            path for path in (ROOT / "examples").iterdir()
            if path.suffix in {".json", ".yaml", ".yml"}
        )
        self.assertTrue(examples)
        for path in examples:
            for name, validator in self.validators.items():
                with self.subTest(example=path.name, schema=name):
                    validator.validate(load(path))

    def test_conformance_metadata_still_validates(self):
        manifest = json.loads((ROOT / "conformance/manifest.json").read_text())
        validator = self.validators["fhr.json"]
        for vector in manifest["vectors"]:
            if vector["format"] == "microdata" and vector["expected"] == "valid":
                with self.subTest(vector=vector["id"]):
                    validator.validate(vector["metadata"])

    def test_every_nested_object_is_closed(self):
        def objects(node, path):
            if isinstance(node, dict):
                if node.get("type") == "object" or "properties" in node:
                    yield path, node
                for key, child in node.items():
                    yield from objects(child, f"{path}/{key}")
            elif isinstance(node, list):
                for index, child in enumerate(node):
                    yield from objects(child, f"{path}/{index}")

        found = list(objects(self.published, ""))
        self.assertGreaterEqual(len(found), 7)
        for path, node in found:
            with self.subTest(path=path or "/"):
                self.assertIs(node.get("additionalProperties"), False)


if __name__ == "__main__":
    unittest.main()
