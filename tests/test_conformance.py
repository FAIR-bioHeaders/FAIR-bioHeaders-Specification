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
        self.assertIn("ok: valid metadata matches fhr.json (fhp.json for FHP)", result.stdout)

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
        labels = [label for document in ("docs/FORMAT.md", "docs/MICRODATA.md", "docs/JSONLD.md",
                                         "docs/FHP.md", "docs/FHGFF3.md",
                                         "docs/SCHEMA-VERSIONS.md")
                  for label in re.findall(r"\[([RMJPGV]\d+)\]", (ROOT / document).read_text())]
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
            self.assertIn(vector["format"],
                          {"fasta", "gfa", "microdata", "jsonld", "fhp-fasta", "fhgff3"})
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
                subject = {"fhp-fasta": "proteome", "fhgff3": "annotation"}.get(
                    vector["format"], "genome")
                self.assertTrue({subject, "version"} <= vector["metadata"].keys())
            else:
                self.assertIn(vector["rule"], self.manifest["rules"])
                self.assertTrue(vector["reason"])

    def test_numeric_vectors_cite_r13(self):
        vectors = {v["id"]: v for v in self.manifest["vectors"]}
        for name, value in (("fasta-nan-vital-stats", b"gcContent: .nan"),
                            ("fasta-infinity-vital-stats", b"gcContent: .inf")):
            with self.subTest(vector=name):
                vector = vectors[name]
                self.assertEqual((vector["expected"], vector["rule"]), ("invalid", "R13"))
                self.assertIn(value, (CONFORMANCE / vector["file"]).read_bytes())

    def test_fhp_vectors(self):
        """specs/006-protein-header contracts/conformance.md."""
        vectors = {v["id"]: v for v in self.manifest["vectors"] if v["format"] == "fhp-fasta"}
        self.assertEqual(self.manifest["fhpSpecification"], "docs/FHP.md")
        self.assertEqual(len([v for v in vectors.values() if v["expected"] == "valid"]), 12)
        self.assertEqual(len([v for v in vectors.values() if v["expected"] == "invalid"]), 15)
        for vector in vectors.values():
            self.assertTrue(vector["file"].endswith(".fhp.fasta")
                            or vector["file"].endswith(".fhp.fasta.gz"), vector["file"])
        body = (CONFORMANCE / vectors["fhp-fasta-lf"]["file"]).read_bytes().split(b"\n>", 1)[1]
        for residue in (b"*", b"U", b"O", b"B", b"Z", b"J", b"X", b"m", b"-"):
            self.assertIn(residue, body)
        for vector in vectors.values():
            if vector["expected"] == "invalid" and vector["rule"] in {"P1", "P2"}:
                self.assertIn("metadata", vector, vector["id"])
        self.assertEqual(vectors["fhp-fasta-cites-fhr-schema"]["rule"], "P2")

    def test_selection_vectors(self):
        """specs/012-schema-versioning: V1-V5 and the registry they rely on."""
        vectors = [v for v in self.manifest["vectors"]
                   if any(rule.startswith("V") for rule in v.get("rules", [v.get("rule", "")]))]
        self.assertEqual(self.manifest["schemaVersionsSpecification"], "docs/SCHEMA-VERSIONS.md")
        unsupported = {v["id"] for v in vectors if v.get("result") == "unsupported-version"}
        self.assertEqual(unsupported, {"fasta-schema-unknown-release", "fasta-schema-branch-ref",
                                       "fhp-fasta-schema-release-without-type",
                                       "fhgff3-schema-unknown-release"})
        for vector in vectors:
            if vector["id"] in unsupported:
                self.assertEqual((vector["expected"], vector["rule"]), ("invalid", "V4"))
        selected = {v["id"]: v for v in vectors if v["expected"] == "valid"}
        self.assertEqual(selected["fasta-schema-v0.3.1"]["metadata"]["schemaVersion"], 1)
        self.assertEqual(selected["fasta-schema-raw-main"]["metadata"]["schemaVersion"], "2.0")
        sys.path.insert(0, str(ROOT / "scripts"))
        import check_conformance
        cases = {
            "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhp.json":
                ("FHP", "main"),
            "https://w3id.org/fair-bioheaders/fhgff3/v0.4.0/": ("FHGFF3", "v0.4.0"),
            "https://w3id.org/fair-bioheaders/fhr/v0.3.1": ("FHR", "v0.3.1"),
            "https://w3id.org/fair-bioheaders/fhp/v0.3.1": ("FHP", None),
            "https://w3id.org/fair-bioheaders/fhr/v0.4.0/fhr.json": ("FHR", "main"),
            "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/abc123/fhr.json":
                ("FHR", None),
            None: ("FHR", "main"),
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(check_conformance.select_schema(value)[:2], expected)

    def test_fhgff3_vectors(self):
        """specs/007-gff3-header contracts/conformance.md."""
        vectors = {v["id"]: v for v in self.manifest["vectors"] if v["format"] == "fhgff3"}
        self.assertEqual(self.manifest["fhgff3Specification"], "docs/FHGFF3.md")
        self.assertEqual(len([v for v in vectors.values() if v["expected"] == "valid"]), 16)
        self.assertEqual(len([v for v in vectors.values() if v["expected"] == "invalid"]), 13)
        for vector in vectors.values():
            self.assertTrue(vector["file"].endswith((".fhgff3.gff3", ".fhgff3.gff3.gz")),
                            vector["file"])
            data = (CONFORMANCE / vector["file"]).read_bytes()
            if not vector["compressed"] and vector["id"] != "fhgff3-header-before-version":
                self.assertTrue(data.startswith(b"##gff-version 3"), vector["id"])
            if vector["expected"] == "invalid" and vector["rule"] in {"G2", "G3"}:
                self.assertIn("metadata", vector, vector["id"])
        self.assertIn(b"##FASTA", (CONFORMANCE / vectors["fhgff3-embedded-fasta"]["file"]).read_bytes())
        self.assertEqual(vectors["fhgff3-header-before-version"]["rule"], "G1")
        self.assertEqual(vectors["fhgff3-header-after-fasta"]["rule"], "G1")
        self.assertEqual(vectors["fhgff3-cites-fhr-schema"]["rule"], "G3")
        # Invalid near misses for the G1 grammar (##gff-version 30, 3x, 3.1) are
        # added when the released toolkit enforces the grammar; adding them now
        # would fail check_conformance.py --converter against fair-bioheaders
        # 0.8.0, which checks only the "##gff-version 3" prefix.
        self.assertEqual(vectors["fhgff3-version-3-1-26"]["expected"], "valid")
        self.assertEqual(vectors["fhgff3-version-3-trailing-whitespace"]["expected"], "valid")

    def test_g1_version_grammar_rejects_near_misses(self):
        """docs/FHGFF3.md G1: only 3 or 3.x.y is a valid ##gff-version line."""
        text = (ROOT / "docs" / "FHGFF3.md").read_text(encoding="utf-8")
        documented = re.search(r"`\^##gff-version[^`]+`", text)
        self.assertIsNotNone(documented, "G1 does not state the version grammar")
        grammar = re.compile(documented.group(0).strip("`"))
        for line in ("##gff-version 3", "##gff-version 3.1.26", "##gff-version 3 \t"):
            with self.subTest(valid=line):
                self.assertRegex(line, grammar)
        for line in ("##gff-version 30", "##gff-version 3x", "##gff-version 3.1"):
            with self.subTest(invalid=line):
                self.assertNotRegex(line, grammar)

    def test_compressed_vectors_share_the_plain_checksum(self):
        vectors = {vector["id"]: vector for vector in self.manifest["vectors"]}
        compressed = [vector for vector in vectors.values()
                      if vector["compressed"] and vector["expected"] == "valid"]
        self.assertGreaterEqual(len(compressed), 4)
        for vector in compressed:
            kind = vector["format"]
            plain = vectors[{"fhgff3": "fhgff3-minimal-checksum-link"}.get(kind, f"{kind}-lf")]
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
        # These fake converters have no fhr-gff3-validate, so FHGFF3 is also left out.
        self.assertIn("(53 vectors left out: fhgff3 not supported by this converter; "
                      "jsonld skipped)", skipped.stdout)

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
            "if vector.get('result') == 'unsupported-version':\n"
            "    print('FHR: unsupported schema version: ' + sys.argv[1], file=sys.stderr)\n"
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
        self.assertIn("(53 vectors left out: fhgff3 not supported by this converter; "
                      "jsonld not supported by this converter)",
                      lenient.stdout)
        strict = self.check("--skip-regeneration", "--require-format", "jsonld",
                            "--converter", bin_directory)
        self.assertEqual(strict.returncode, 1)
        self.assertIn("jsonld-canonical-embedded: converter rejected (FHR: Unsupported file "
                      "extension", strict.stderr)
        # A converter without fhr-gff3-validate predates FHGFF3: skipped, unless required.
        gff3 = self.check("--skip-regeneration", "--require-format", "fhgff3",
                          "--converter", bin_directory)
        self.assertEqual(gff3.returncode, 1)
        self.assertIn("fhgff3-minimal-checksum-link: converter rejected (Unsupported file "
                      "extension (no fhr-gff3-validate))", gff3.stderr)

    def test_jsonld_vectors(self):
        vectors = {v["id"]: v for v in self.manifest["vectors"] if v["format"] == "jsonld"}
        self.assertEqual(self.manifest["jsonldSpecification"], "docs/JSONLD.md")
        self.assertEqual(len(vectors), 24)
        self.assertIn("notApplicable", self.manifest["rules"]["J7"])
        for vector in vectors.values():
            document = json.loads((CONFORMANCE / vector["file"]).read_text(encoding="utf-8")) \
                if vector["id"] != "jsonld-duplicate-key" else None
            if vector["expected"] == "valid":
                if vector["id"] != "jsonld-expanded":
                    self.assertIn("@context", document)
                self.assertTrue(set(vector["metadata"]) >= {"genome", "checksum"})
        exported = json.loads((CONFORMANCE / vectors["jsonld-export-terms"]["file"]).read_text())
        self.assertEqual(exported["conformsTo"],
                         "https://bioschemas.org/profiles/Dataset/1.0-RELEASE")
        self.assertNotIn("conformsTo", vectors["jsonld-export-terms"]["metadata"])
        self.assertEqual(vectors["jsonld-export-terms"]["expected"], "valid")
        self.assertEqual(vectors["jsonld-root-id"]["rule"], "J4")
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
