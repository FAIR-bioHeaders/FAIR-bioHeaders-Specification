"""Exercise the conformance vectors, their generator and their checker."""

import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "conformance"


def run(*arguments):
    return subprocess.run([sys.executable, *map(str, arguments)], capture_output=True, text=True)


class ConformanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.manifest = json.loads((CONFORMANCE / "manifest.json").read_text())

    def check(self, *extra, conformance=CONFORMANCE):
        return run(ROOT / "scripts/check_conformance.py", "--conformance", conformance, *extra)

    def copy_vectors(self):
        copy = self.root / "conformance"
        shutil.copytree(CONFORMANCE, copy)
        return copy

    def test_committed_vectors_pass_stdlib_and_schema_checks(self):
        result = self.check("--schema")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok: vectors match the generator", result.stdout)
        self.assertIn("ok: valid metadata matches fhr.json", result.stdout)

    def test_generator_is_deterministic(self):
        outputs = [self.root / "first", self.root / "second"]
        for output in outputs:
            result = run(ROOT / "scripts/make_conformance.py", "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
        first, second = ({path.relative_to(output): path.read_bytes()
                          for path in output.rglob("*") if path.is_file()} for output in outputs)
        self.assertEqual(first, second)

    def test_modified_vector_is_reported(self):
        copy = self.copy_vectors()
        vector = copy / "valid/fasta-lf.fhr.fasta"
        vector.write_bytes(vector.read_bytes().replace(b"ACGT", b"ACGA", 1))
        result = self.check(conformance=copy)
        self.assertEqual(result.returncode, 1)
        self.assertIn("valid/fasta-lf.fhr.fasta: differs from the generator output", result.stderr)
        self.assertIn("fasta-lf: manifest", result.stderr)

    def test_line_ending_normalization_is_reported(self):
        copy = self.copy_vectors()
        vector = copy / "valid/gfa-crlf.fhr.gfa"
        vector.write_bytes(vector.read_bytes().replace(b"\r\n", b"\n"))
        result = self.check("--skip-regeneration", conformance=copy)
        self.assertEqual(result.returncode, 1)
        self.assertIn("gfa-crlf: manifest", result.stderr)

    def test_extra_file_is_reported(self):
        copy = self.copy_vectors()
        (copy / "invalid/stray.fhr.fasta").write_bytes(b">x\nA\n")
        result = self.check(conformance=copy)
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid/stray.fhr.fasta: not produced by the generator", result.stderr)

    def test_every_rule_is_labelled_and_covered(self):
        labels = [label for document in ("docs/FORMAT.md", "docs/MICRODATA.md", "docs/JSONLD.md")
                  for label in re.findall(r"\[([RMJ]\d+)\]", (ROOT / document).read_text())]
        self.assertEqual(labels, list(self.manifest["rules"]))
        for rule, details in self.manifest["rules"].items():
            outcomes = {
                vector["expected"] for vector in self.manifest["vectors"]
                if rule in vector.get("rules", [vector.get("rule")])
            }
            if "notApplicable" in details:
                # No invalid input exists (J7 constrains writers); valid vectors may cite it.
                self.assertNotIn("invalid", outcomes, rule)
            else:
                self.assertEqual(outcomes, {"valid", "invalid"}, rule)

    def test_manifest_fields(self):
        required = json.loads((ROOT / "fhr.json").read_text())["required"]
        for vector in self.manifest["vectors"]:
            self.assertIn(vector["format"], {"fasta", "gfa", "microdata", "jsonld"})
            self.assertTrue((CONFORMANCE / vector["file"]).is_file(), vector["file"])
            self.assertEqual(vector["file"].split("/")[0], vector["expected"])
            if vector["format"] in {"microdata", "jsonld"}:
                suffix = ".html" if vector["format"] == "microdata" else ".jsonld"
                self.assertTrue(vector["file"].endswith(suffix), vector["file"])
                self.assertNotIn("checksum", vector)
                if vector["expected"] == "valid":
                    self.assertTrue(set(required) <= vector["metadata"].keys(), vector["id"])
                else:
                    self.assertTrue(vector["reason"])
                continue
            if vector["expected"] == "valid":
                self.assertRegex(vector["checksum"], r"^[A-Za-z0-9+/]{43}=$")
                self.assertTrue({"genome", "version"} <= vector["metadata"].keys())
            else:
                self.assertIn(vector["rule"], self.manifest["rules"])
                self.assertTrue(vector["reason"])

    def test_compressed_vectors_share_the_plain_checksum(self):
        vectors = {vector["id"]: vector for vector in self.manifest["vectors"]}
        compressed = [vector for vector in vectors.values()
                      if vector["compressed"] and vector["expected"] == "valid"]
        self.assertGreaterEqual(len(compressed), 4)
        for vector in compressed:
            kind = vector["format"]
            plain = vectors[f"{kind}-lf"]
            data = (CONFORMANCE / vector["file"]).read_bytes()
            self.assertEqual(data[3] & 0x08, 0, "no stored file name")
            self.assertEqual(data[4:8], b"\0\0\0\0", "mtime 0")
            self.assertEqual(gzip.decompress(data), (CONFORMANCE / plain["file"]).read_bytes())
            self.assertEqual(vector["checksum"], plain["checksum"])

    def test_converter_that_accepts_everything_fails(self):
        bin_directory = self.root / "bin"
        bin_directory.mkdir()
        for name in ("fhr-fasta-validate", "fhr-gfa-validate"):
            script = bin_directory / name
            script.write_text(f"#!{sys.executable}\nraise SystemExit(0)\n")
            script.chmod(0o755)
        # A converter that extracts only the genome from every HTML file.
        script = bin_directory / "fhr-convert"
        script.write_text(f"#!{sys.executable}\nimport sys\n"
                          "open(sys.argv[2], 'w').write('{\"genome\": \"Synthetic FHR "
                          "conformance genome\"}')\n")
        script.chmod(0o755)
        result = self.check("--skip-regeneration", "--converter", bin_directory)
        self.assertEqual(result.returncode, 1)
        self.assertIn("fasta-u2028-in-header: converter accepted; expected invalid, R6",
                      result.stderr)
        self.assertIn("microdata-type-mismatch: converter accepted; expected invalid, M3",
                      result.stderr)
        self.assertIn("microdata-canonical: converter extracted different metadata for "
                      "assemblyAuthor,", result.stderr)
        self.assertIn("jsonld-type-object: converter accepted; expected invalid, J1",
                      result.stderr)
        self.assertIn("jsonld-canonical-embedded: converter extracted different metadata",
                      result.stderr)
        self.assertNotIn("fasta-lf:", result.stderr)
        skipped = self.check("--skip-regeneration", "--skip-format", "jsonld",
                             "--converter", bin_directory)
        self.assertEqual(skipped.returncode, 1)
        self.assertNotIn("jsonld-", skipped.stderr)
        self.assertIn("microdata-type-mismatch", skipped.stderr)
        self.assertIn("(13 vectors left out: jsonld skipped)", skipped.stdout)

    def test_converter_without_a_format_is_skipped_unless_required(self):
        # An older converter: correct on every format except JSON-LD, which it
        # rejects as an unsupported file extension (as fhr 0.3.3 does).
        bin_directory = self.root / "bin"
        bin_directory.mkdir()
        manifest = json.dumps({v["file"]: v for v in self.manifest["vectors"]})
        body = (
            f"#!{sys.executable}\nimport json, sys\n"
            f"vectors = {{v.rsplit('/', 1)[-1]: m for v, m in json.loads({manifest!r}).items()}}\n"
            "vector = vectors[sys.argv[1].rsplit('/', 1)[-1]]\n"
            "if vector['format'] == 'jsonld':\n"
            "    print('FHR: Unsupported file extension: ' + sys.argv[1], file=sys.stderr)\n"
            "    raise SystemExit(1)\n"
            "if vector['expected'] != 'valid':\n"
            "    raise SystemExit(1)\n"
            "if len(sys.argv) > 2:\n"
            "    json.dump(vector['metadata'], open(sys.argv[2], 'w'))\n"
        )
        for name in ("fhr-fasta-validate", "fhr-gfa-validate", "fhr-convert"):
            script = bin_directory / name
            script.write_text(body)
            script.chmod(0o755)
        lenient = self.check("--skip-regeneration", "--converter", bin_directory)
        self.assertEqual(lenient.returncode, 0, lenient.stderr)
        self.assertIn("(13 vectors left out: jsonld not supported by this converter)",
                      lenient.stdout)
        strict = self.check("--skip-regeneration", "--require-format", "jsonld",
                            "--converter", bin_directory)
        self.assertEqual(strict.returncode, 1)
        self.assertIn("jsonld-canonical-embedded: converter rejected (FHR: Unsupported file "
                      "extension", strict.stderr)

    def test_jsonld_vectors(self):
        vectors = {v["id"]: v for v in self.manifest["vectors"] if v["format"] == "jsonld"}
        self.assertEqual(self.manifest["jsonldSpecification"], "docs/JSONLD.md")
        self.assertEqual(len(vectors), 13)
        self.assertIn("notApplicable", self.manifest["rules"]["J7"])
        for vector in vectors.values():
            document = json.loads((CONFORMANCE / vector["file"]).read_text(encoding="utf-8")) \
                if vector["id"] != "jsonld-duplicate-key" else None
            if vector["expected"] == "valid":
                self.assertIn("@context", document)
                self.assertTrue(set(vector["metadata"]) >= {"genome", "checksum"})
        exported = json.loads((CONFORMANCE / vectors["jsonld-export-terms"]["file"]).read_text())
        self.assertEqual(exported["conformsTo"],
                         "https://bioschemas.org/profiles/Dataset/1.0-RELEASE")
        self.assertNotIn("conformsTo", vectors["jsonld-export-terms"]["metadata"])
        linked = json.loads((CONFORMANCE / vectors["jsonld-documentation-url"]["file"]).read_text())
        self.assertNotIn("documentation", linked)
        self.assertEqual(linked["subjectOf"],
                         vectors["jsonld-documentation-url"]["metadata"]["documentation"])

    @unittest.skipUnless(os.environ.get("FHR_CONVERTER"), "set FHR_CONVERTER to test a converter")
    def test_converter_agrees_with_manifest(self):
        result = self.check("--skip-regeneration", "--converter", os.environ["FHR_CONVERTER"])
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
