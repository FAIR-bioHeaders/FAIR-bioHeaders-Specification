# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The shared FAIR header assessment fixtures and their manifest (feature 010)."""

import gzip
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "assessment"
GENERATOR = ROOT / "scripts" / "make_assessment_fixtures.py"
FIXTURE_DIRECTORIES = ("headers", "pairs", "edge")
GENERATED_DIRECTORIES = ("pairs", "edge")
ORACLES = json.loads((ASSESSMENT / "generation-oracles.json").read_text())


def fixture_value(name, content):
    """The bytes that carry this assessment case's declared meaning.

    Compressed representation is not a cross-runtime interface. The payload,
    archive members and BGZF framing are, and must still match exactly.
    """
    oracle = ORACLES[name]
    if oracle == "bytes":
        return content
    payload = gzip.decompress(content)  # CRC/truncation errors remain failures.
    if oracle == "bgzf-payload":
        offset = 0
        while offset < len(content):
            block = content[offset:]
            if block[:16] != bytes.fromhex("1f8b08040000000000ff060042430200"):
                raise AssertionError(f"{name}: invalid BGZF block header")
            size = int.from_bytes(block[16:18], "little") + 1
            if size < 28 or size > 65536 or offset + size > len(content):
                raise AssertionError(f"{name}: invalid BGZF block size")
            gzip.decompress(block[:size])
            offset += size
        if content[-28:] != bytes.fromhex("1f8b08040000000000ff0600424302001b0003000000000000000000"):
            raise AssertionError(f"{name}: missing standard BGZF EOF block")
    elif oracle == "gzip-tar":
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
            members = archive.getmembers()
            if len(members) != 1 or members[0].name != "annotation.gff3" or not members[0].isfile():
                raise AssertionError(f"{name}: expected one regular annotation.gff3 member")
            if not archive.extractfile(members[0]).read().startswith(b"##gff-version 3\n"):
                raise AssertionError(f"{name}: missing GFF3 member content")
    elif oracle != "gzip-payload":
        raise AssertionError(f"{name}: unknown generation oracle {oracle!r}")
    return payload


def tree(directory, subdirectories):
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for name in subdirectories
        for path in sorted((directory / name).rglob("*"))
        if path.is_file() and path.name != ".gitkeep"
    }


class AssessmentFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ASSESSMENT / "manifest.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((ASSESSMENT / "manifest.schema.json").read_text(encoding="utf-8"))

    def test_manifest_validates_against_its_schema(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:  # pragma: no cover - requirements-validation.txt has it
            self.skipTest("jsonschema is not installed")
        Draft202012Validator.check_schema(self.schema)
        errors = sorted(Draft202012Validator(self.schema).iter_errors(self.manifest), key=str)
        self.assertEqual([], [f"{list(e.absolute_path)}: {e.message}" for e in errors])

    def test_every_fixture_file_is_listed_once(self):
        listed = [entry["file"] for entry in self.manifest["fixtures"]]
        self.assertEqual(len(listed), len(set(listed)), "a file is listed twice")
        on_disk = set(tree(ASSESSMENT, FIXTURE_DIRECTORIES))
        related = {entry["related"] for entry in self.manifest["fixtures"] if "related" in entry}
        self.assertEqual(sorted(on_disk - set(listed) - related), [], "files not in the manifest")
        self.assertEqual(sorted(set(listed) - on_disk), [], "manifest entries without a file")
        self.assertEqual(sorted(related - on_disk), [], "related files that do not exist")

    def test_ids_are_unique(self):
        ids = [entry["id"] for entry in self.manifest["fixtures"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_provenance(self):
        for entry in self.manifest["fixtures"]:
            with self.subTest(entry["id"]):
                if entry["file"].startswith("headers/"):
                    self.assertTrue(entry["source_url"].startswith("https://"))
                    self.assertRegex(entry["fetched"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z$")
                    self.assertNotIn("generator", entry)
                else:
                    self.assertEqual(entry["generator"], "scripts/make_assessment_fixtures.py")
                    self.assertNotIn("source_url", entry)

    def test_real_captures_keep_no_survey_annotations(self):
        for path in sorted((ASSESSMENT / "headers").iterdir()):
            if path.suffix == ".gz" or path.name == ".gitkeep":
                continue
            with self.subTest(path.name):
                text = path.read_bytes().decode("utf-8")
                for marker in ("# SOURCE-URL", "# FETCHED", "----- captured header lines", "[ELIDED"):
                    self.assertNotIn(marker, text)

    def test_generator_is_deterministic_and_matches_the_committed_files(self):
        outputs = []
        for _ in range(2):
            directory = tempfile.TemporaryDirectory()
            self.addCleanup(directory.cleanup)
            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--output", directory.name],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = tree(Path(directory.name), GENERATED_DIRECTORIES)
            generated["pairs.tsv"] = (Path(directory.name) / "pairs.tsv").read_bytes()
            outputs.append(generated)
        self.assertEqual(outputs[0], outputs[1])
        committed = tree(ASSESSMENT, GENERATED_DIRECTORIES)
        committed["pairs.tsv"] = (ASSESSMENT / "pairs.tsv").read_bytes()
        self.assertEqual(sorted(outputs[0]), sorted(committed))
        self.assertEqual(set(outputs[0]), set(ORACLES), "classify every generated artifact")
        for name, content in outputs[0].items():
            self.assertEqual(fixture_value(name, content), fixture_value(name, committed[name]),
                             f"{name} differs from the generator's declared oracle")

    def test_compression_changes_preserve_the_oracle_but_payload_changes_do_not(self):
        for name in ("edge/gzip-refseq.gff.gz", "edge/gff3-in-tar.gff.gz"):
            with self.subTest(name=name):
                committed = (ASSESSMENT / name).read_bytes()
                payload = gzip.decompress(committed)
                variant = gzip.compress(payload, compresslevel=0, mtime=0)
                self.assertNotEqual(variant, committed)
                self.assertEqual(fixture_value(name, variant), fixture_value(name, committed))
                if name.endswith("gff3-in-tar.gff.gz"):
                    mutated = payload.replace(b"ID=gene1", b"ID=gene2", 1)
                else:
                    mutated = payload.replace(b"RefSeq", b"RefSeX", 1)
                self.assertNotEqual(mutated, payload)
                self.assertNotEqual(fixture_value(name, gzip.compress(mutated, mtime=0)),
                                    fixture_value(name, committed))

    def test_compressed_oracles_reject_corruption_and_lost_bgzf_framing(self):
        for name, oracle in ORACLES.items():
            if oracle == "bytes":
                continue
            with self.subTest(name=name):
                content = (ASSESSMENT / name).read_bytes()
                with self.assertRaises((EOFError, OSError, AssertionError)):
                    fixture_value(name, content[:-1])
                if oracle == "bgzf-payload":
                    with self.assertRaisesRegex(AssertionError, "BGZF"):
                        fixture_value(name, gzip.compress(gzip.decompress(content), mtime=0))


class AssessmentInstalledToolkitTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("ASSESSMENT_TOOLKIT"),
                         "set ASSESSMENT_TOOLKIT to the pinned installed bioheaders executable")
    def test_archive_scope_survives_compressor_changes(self):
        cli = Path(os.environ["ASSESSMENT_TOOLKIT"]).resolve()
        pin = json.loads((ROOT / "conformance/toolkit-pin.json").read_text())["version"]
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        with tempfile.TemporaryDirectory() as directory:
            installed = subprocess.run([str(cli.with_name("python")), "-c",
                                       "import bioheaders,importlib.metadata,json;print(json.dumps("
                                       "[importlib.metadata.version('fair-bioheaders'),bioheaders.__file__]))"],
                                      cwd=directory, env=env, capture_output=True, text=True, check=True)
            version, module = json.loads(installed.stdout)
            self.assertEqual(version, pin)
            self.assertIn("site-packages", Path(module).parts)
            source = ASSESSMENT / "edge/gff3-in-tar.gff.gz"
            payload = gzip.decompress(source.read_bytes())
            spec = importlib.util.spec_from_file_location("assessment_checker", ROOT / "scripts/check_assessment.py")
            checker = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(checker)
            expected = next(e["expected"] for e in json.loads((ASSESSMENT / "manifest.json").read_text())["fixtures"]
                            if e["id"] == "edge-gff3-in-tar")
            for level in (0, 6, 9):
                path = Path(directory) / f"archive-level-{level}.gff.gz"
                path.write_bytes(gzip.compress(payload, compresslevel=level, mtime=0))
                result = subprocess.run([str(cli), "assess", "--format", "json", str(path)],
                                        cwd=directory, env=env, capture_output=True, text=True, check=True)
                report = json.loads(result.stdout)
                self.assertEqual(report["input"]["format"], "archive")
                self.assertEqual(report["input"]["compression"], "gzip")
                self.assertEqual(checker.compare(expected, report), [], result.stdout)
                self.assertTrue(any(r["reason"] == "archive-not-supported" for r in report["results"]))


if __name__ == "__main__":
    unittest.main()
