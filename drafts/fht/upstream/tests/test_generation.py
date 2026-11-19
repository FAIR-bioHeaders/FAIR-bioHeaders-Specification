"""Check that the committed FHT schema matches the LinkML model."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "fht_generator", ROOT / "json-schema-generator.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenerationTests(unittest.TestCase):
    def test_committed_schema_matches_the_model(self):
        generated = load_generator().generate()
        committed = json.loads((ROOT / "fht.json").read_text(encoding="utf-8"))
        self.assertEqual(committed, generated)

    def test_pinned_imports_match_provenance(self):
        spec = importlib.util.spec_from_file_location(
            "check_provenance", ROOT / "scripts" / "check_provenance.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.main(), 0)


class CitationProvenanceTests(unittest.TestCase):
    def test_citation_and_provenance_commit_labels_cannot_drift_independently(self):
        spec = importlib.util.spec_from_file_location(
            "check_provenance", ROOT / "scripts" / "check_provenance.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory)
            shutil.copytree(ROOT / "schemas", scratch / "schemas")
            citation = scratch / "CITATION.cff"
            original = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
            citation.write_text(original, encoding="utf-8")
            provenance = scratch / "schemas" / "provenance.json"
            record = json.loads(provenance.read_text(encoding="utf-8"))
            with patch.object(module, "ROOT", scratch), patch.object(
                module, "PROVENANCE", provenance
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(module.main(), 0)
                changed = "f" * 40
                self.assertNotEqual(changed, record["source_commit"])
                for side in ["citation", "provenance", "missing citation marker"]:
                    with self.subTest(side=side):
                        citation.write_text(original, encoding="utf-8")
                        provenance.write_text(json.dumps(record), encoding="utf-8")
                        if side == "citation":
                            citation.write_text(
                                original.replace(record["source_commit"], changed),
                                encoding="utf-8",
                            )
                        elif side == "provenance":
                            provenance.write_text(
                                json.dumps(dict(record, source_commit=changed)),
                                encoding="utf-8",
                            )
                        else:
                            citation.write_text(
                                "\n".join(line for line in original.splitlines()
                                          if not line.startswith("# Pinned shared-source-commit:")),
                                encoding="utf-8",
                            )
                        errors = io.StringIO()
                        with contextlib.redirect_stderr(errors):
                            self.assertEqual(module.main(), 1)
                        self.assertIn("CITATION.cff", errors.getvalue())
                        self.assertIn(
                            "expected exactly one" if side.startswith("missing") else "does not match",
                            errors.getvalue(),
                        )


if __name__ == "__main__":
    unittest.main()
