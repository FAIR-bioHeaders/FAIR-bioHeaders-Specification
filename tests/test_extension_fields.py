# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Extension fields with an x- prefix (docs/FORMAT.md R15, specs/015-extension-fields)."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import make_jsonld  # noqa: E402

try:
    from pyld import jsonld as pyld
except ImportError:  # pragma: no cover - depends on the environment
    pyld = None
REGISTRY = json.loads((ROOT / "schemas" / "versions.json").read_text(encoding="utf-8"))
PATTERN = "^x-[A-Za-z0-9][A-Za-z0-9_.-]*$"
# header type: (schema file, minimal example, first minor, new minor, a nested object path)
TYPES = {
    "FHR": ("fhr.json", "examples/minimal.fhr.json", "2.0", "2.1", "taxon"),
    "FHP": ("fhp.json", "examples/fhp/minimal-predicted.fhp.json", "1.0", "1.2", "taxon"),
    "FHGFF3": ("fhgff3.json", "examples/fhgff3/minimal-reference.fhgff3.json", "1.0", "1.2",
               "genomeReference"),
}
VALID_KEYS = ["x-a", "x-1", "x-refget-commonName", "x-a.b-c_d", "x-A", "x-genome"]
# Each is invalid in every version: not the prefix, an empty or punctuation-led name,
# whitespace, non-ASCII (including look-alikes) and line breaks.
INVALID_KEYS = [
    "genom", "X-a", "x-", "x--a", "x-_a", "x-.a", "x- a", "x-a b", "x-a ", " x-a", "x-ä",
    "x-K", "x-ａ", "ｘ-a", "x-a\n", "x-a\r", "x-a\r\n", "x-a\t", "x-a ",
    "x-a:b", "x-a@b", "x-a>b", "x-a#b", "x-a/b", "xa", "x_a", "ext-a", "x-a\x00",
]
VALUES = ["text", 1, 1.5, True, None, [], {}, [1, "a", {"b": None}],
          {"@context": "https://example.org/", "@id": "_:x", "nested": {"deep": [1]}},
          "<script>&amp;</script>", "contigs > 1000 bp, a@example.org"]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def released(name, tag="v0.4.0"):
    shown = subprocess.run(["git", "show", f"{tag}:{name}"], cwd=ROOT, capture_output=True)
    if shown.returncode:
        return None
    return json.loads(shown.stdout)


def validator(schema):
    return Draft202012Validator(schema, format_checker=FormatChecker())


def generated():
    spec = importlib.util.spec_from_file_location("generator", ROOT / "json-schema-generator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {"FHR": module.generate(), "FHP": module.generate_fhp(),
            "FHGFF3": module.generate_fhgff3()}


class ExtensionFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = generated()

    def schemas(self, header_type):
        """The published schema and the LinkML generator's output."""
        yield "published", load(TYPES[header_type][0])
        yield "LinkML", self.generated[header_type]

    def record(self, header_type, version):
        record = load(TYPES[header_type][1])
        record["schemaVersion"] = version
        return record

    def test_registry_versions(self):
        self.assertEqual(REGISTRY["releases"]["v0.5.0"],
                         {"FHR": "2.1", "FHP": "1.1", "FHGFF3": "1.1"})
        self.assertEqual(REGISTRY["releases"][REGISTRY["current"]],
                         {"FHR": "2.1", "FHP": "1.2", "FHGFF3": "1.2"})
        for header_type, (name, _, first, new, _) in TYPES.items():
            with self.subTest(header_type=header_type):
                schema = load(name)
                # The schema of M.N accepts exactly "M.0" to "M.N"
                # (docs/SCHEMA-VERSIONS.md); "1.2" joined the range in #170.
                major = first.split(".")[0]
                expected = [f"{major}.{n}" for n in range(int(new.split(".")[1]) + 1)]
                self.assertEqual(schema["properties"]["schemaVersion"]["enum"], expected)
                self.assertEqual(list(schema["patternProperties"]), [PATTERN])
                self.assertIs(schema["additionalProperties"], False)

    def test_valid_keys_and_values_in_the_new_minor(self):
        for header_type, (_, _, _, new, _) in TYPES.items():
            for label, schema in self.schemas(header_type):
                check = validator(schema)
                for key in VALID_KEYS:
                    for value in VALUES:
                        record = self.record(header_type, new)
                        record[key] = copy.deepcopy(value)
                        with self.subTest(header_type=header_type, schema=label, key=key,
                                          value=value):
                            self.assertEqual(list(check.iter_errors(record)), [])

    def test_many_extension_fields_in_any_position(self):
        for header_type, (_, _, _, new, _) in TYPES.items():
            record = self.record(header_type, new)
            items = list(record.items())
            record = dict([("x-first", 1)] + items[:3] + [("x-middle", [2])] + items[3:]
                          + [("x-last", {"a": 3})])
            for label, schema in self.schemas(header_type):
                with self.subTest(header_type=header_type, schema=label):
                    self.assertEqual(list(validator(schema).iter_errors(record)), [])

    def test_invalid_keys_in_every_version(self):
        for header_type, (name, _, first, new, _) in TYPES.items():
            schemas = list(self.schemas(header_type))
            old = released(name)
            if old is not None:
                schemas.append(("v0.4.0", old))
            for label, schema in schemas:
                check = validator(schema)
                for version in (first, new):
                    for key in INVALID_KEYS:
                        record = self.record(header_type, version)
                        record[key] = "value"
                        with self.subTest(header_type=header_type, schema=label,
                                          version=version, key=key):
                            self.assertTrue(list(check.iter_errors(record)))

    def test_first_minor_has_no_extension_fields(self):
        """A record that states the older minor is held to it (research R-02)."""
        for header_type, (_, _, first, _, _) in TYPES.items():
            for label, schema in self.schemas(header_type):
                record = self.record(header_type, first)
                self.assertEqual(list(validator(schema).iter_errors(record)), [])
                record["x-a"] = 1
                with self.subTest(header_type=header_type, schema=label):
                    errors = list(validator(schema).iter_errors(record))
                    self.assertEqual(len(errors), 1)
                    self.assertEqual(errors[0].validator, "not")

    def test_nested_objects_stay_closed(self):
        for header_type, (_, _, _, new, nested) in TYPES.items():
            for label, schema in self.schemas(header_type):
                record = self.record(header_type, new)
                record[nested]["x-a"] = 1
                with self.subTest(header_type=header_type, schema=label, path=nested):
                    self.assertTrue(list(validator(schema).iter_errors(record)))
                record = self.record(header_type, new)
                author = record["metadataAuthor"][0]
                author["x-a"] = 1
                with self.subTest(header_type=header_type, schema=label, path="author"):
                    self.assertTrue(list(validator(schema).iter_errors(record)))

    def test_older_release_schemas_reject_extension_fields(self):
        """V2/V3: a record citing v0.4.x is checked against the v0.4.x schema."""
        for header_type, (name, _, first, new, _) in TYPES.items():
            old = released(name)
            if old is None:
                self.skipTest("v0.4.0 is not available; run git fetch --tags")
            check = validator(old)
            for version in (first, new):
                record = self.record(header_type, version)
                record["x-a"] = 1
                with self.subTest(header_type=header_type, version=version):
                    self.assertTrue(list(check.iter_errors(record)))

    def test_older_minor_outcomes_are_unchanged(self):
        """Every record stating the older minor has its v0.4.0 outcome under the new schema.

        The corpus is the header metadata of every FASTA, GFA, FHP and FHGFF3 vector,
        the extracted metadata of the microdata and JSON-LD vectors and every JSON or
        YAML example, plus records with each probe key added."""
        import check_conformance

        class Loader(yaml.SafeLoader):
            """Dates stay strings, as written (FORMAT.md R12)."""

        Loader.yaml_implicit_resolvers = {
            first: [(tag, regexp) for tag, regexp in resolvers
                    if tag != "tag:yaml.org,2002:timestamp"]
            for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
        }
        corpus = []
        manifest = load("conformance/manifest.json")
        for vector in manifest["vectors"]:
            prefix = check_conformance.PREFIXES.get(vector["format"])
            if prefix is None:
                metadata = vector.get("metadata")
            else:
                data = check_conformance.read_vector(ROOT / "conformance", vector)
                try:
                    text = "\n".join(line[len(prefix):].rstrip(b"\r\n").decode("utf-8")
                                     for line in data.splitlines(keepends=True)
                                     if line.startswith(prefix))
                    metadata = yaml.load(text, Loader=Loader)
                except (UnicodeDecodeError, yaml.YAMLError):
                    continue  # Broken on purpose (R6, R8, R12): no record to compare.
            if isinstance(metadata, dict):
                corpus.append(metadata)
        for path in sorted((ROOT / "examples").rglob("*")):
            if path.suffix in {".json", ".yaml"}:
                corpus.append(yaml.load(path.read_text(encoding="utf-8"), Loader=Loader))
        compared = real = 0
        for header_type, (name, minimal, first, _, nested) in TYPES.items():
            old = released(name)
            if old is None:
                self.skipTest("v0.4.0 is not available; run git fetch --tags")
            before, after = validator(old), validator(load(name))
            candidates = [record for record in corpus
                          if check_conformance.select_record(record)[0] == header_type]
            real += len(candidates)
            base = load(minimal)
            for key in INVALID_KEYS + VALID_KEYS + ["unknown", "@context", "x-", "X-A"]:
                for value in VALUES[:4]:
                    candidates.append({**base, key: value})
            candidates.append({**base, nested: {**base[nested], "x-a": 1}})
            for record in candidates:
                record = {**copy.deepcopy(record), "schemaVersion": first}
                with self.subTest(header_type=header_type, record=sorted(record)[:3]):
                    self.assertEqual(not list(before.iter_errors(record)),
                                     not list(after.iter_errors(record)))
                    compared += 1
        self.assertGreater(real, 200)
        self.assertGreater(compared, 500)


class JsonLdExtensionTests(unittest.TestCase):
    """J9: JSON-LD and the export carry no extension fields."""

    def setUp(self):
        self.record = load("examples/example.fhr.json")
        self.extended = {"x-first": {"@context": {"@vocab": "https://example.org/"},
                                     "@id": "https://example.org/evil", "genome": "other"},
                         **self.record,
                         "x-refget-commonName": "</script><script>alert(1)</script>",
                         "x-list": [{"@type": "Person"}, "&"]}

    def test_writer_leaves_extension_fields_out(self):
        warnings = []
        document = make_jsonld.to_jsonld(self.extended, warn=warnings.append)
        self.assertEqual(document, make_jsonld.to_jsonld(self.record))
        self.assertEqual(make_jsonld.jsonld_text(self.extended),
                         (ROOT / "examples/example.fhr.jsonld").read_text(encoding="utf-8"))
        self.assertEqual(warnings, ["extension fields are not written to JSON-LD: "
                                    "x-first, x-refget-commonName, x-list"])
        text = make_jsonld.script_text(make_jsonld.jsonld_text(self.extended))
        self.assertNotIn("x-", text.replace("x-www", ""))

    def test_export_leaves_extension_fields_out(self):
        warnings = []
        self.assertEqual(make_jsonld.to_export(self.extended, warn=warnings.append),
                         make_jsonld.to_export(self.record))
        self.assertEqual(len(warnings), 1)

    def test_canonical_reader_rejects_extension_fields(self):
        document = make_jsonld.to_jsonld(self.record)
        self.assertEqual(make_jsonld.canonical_record(document), self.record)
        for key in ("x-a", "x-", "x-refget-commonName"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "J9"):
                    make_jsonld.canonical_record({**document, key: "value"})

    @unittest.skipIf(pyld is None, "PyLD is not installed (requirements-jsonld.txt)")
    def test_jsonld_processor_drops_an_extension_key(self):
        """Why J9 rejects the key: the FHR context has no term for it, so expansion drops it."""
        document = {**make_jsonld.to_jsonld(self.record), "x-a": "extension-only text"}
        expanded = pyld.expand(document)
        self.assertNotIn("extension-only text", json.dumps(expanded))
        self.assertNotIn("x-a", json.dumps(expanded))


class ProfileExtensionTests(unittest.TestCase):
    """Profiles reuse the post-processing, so they accept the same extension fields."""

    def test_profile_roots_accept_extension_fields(self):
        spec = importlib.util.spec_from_file_location(
            "profile_schema", ROOT / "profiles" / "profile_schema.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        schema = module.generate_profile("agbiodata-fhr")
        self.assertEqual(list(schema["patternProperties"]), [PATTERN])
        record = json.loads((ROOT / "profiles/examples/agbiodata-fhr/valid.json")
                            .read_text(encoding="utf-8"))
        record["schemaVersion"] = "2.1"
        record["x-agbiodata-note"] = "illustrative"
        self.assertEqual(list(validator(schema).iter_errors(record)), [])
        record["schemaVersion"] = "2.0"
        self.assertTrue(list(validator(schema).iter_errors(record)))


if __name__ == "__main__":
    unittest.main()
