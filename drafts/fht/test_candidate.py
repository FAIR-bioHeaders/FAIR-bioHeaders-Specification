# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Controls for omitted source files and fabricated/partial evidence receipts."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import check_source
from run_checks import installed_receipt, STAGED, unit_receipt


class SourceControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "owning"
        self.source.mkdir()
        self.root = self.base / "candidate"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.source)], check=True)
        self.git("remote", "add", "origin", "https://github.com/FAIR-bioHeaders/FHT-Specification.git")
        self.git("config", "user.name", "Candidate control")
        self.git("config", "user.email", "candidate@example.invalid")
        schema = {"properties": {"schema": {"const": "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json"}}}
        schema["$defs"] = {"FHT": {"properties": schema["properties"]}}
        files = {"fht.json": json.dumps(schema).encode(),
                 "conformance/manifest.json": json.dumps({"vectors": [
                     {"expected": "valid" if i < 34 else "invalid"} for i in range(93)]}).encode(),
                 "required.txt": b"independently selected dependency\n"}
        entries = []
        for name, raw in files.items():
            for root in (self.source, self.root / "upstream"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            entries.append({"source": name, "local": "upstream/" + name,
                            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                            "mode": "100644"})
        self.git("add", ".")
        self.git("commit", "-qm", "owning control")
        commit = self.git("rev-parse", "HEAD").decode().strip()
        self.addCleanup(patch.stopall)
        patch.object(check_source, "COMMIT", commit).start()
        self.manifest = {"repository": check_source.REPOSITORY, "commit": commit,
                         "selection": {"trackedFiles": "all", "excluded": ["AGENTS.md"]},
                         "files": entries}
        self.write_manifest()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args])

    def write_manifest(self):
        (self.root / "source.json").write_text(json.dumps(self.manifest))

    def verify(self, source=True):
        with contextlib.redirect_stdout(io.StringIO()):
            check_source.verify(self.root, self.source if source else None)

    def test_independent_selection_detects_file_and_manifest_omitted_together(self):
        self.verify()
        (self.root / "upstream/required.txt").unlink()
        self.manifest["files"] = [e for e in self.manifest["files"] if e["source"] != "required.txt"]
        self.write_manifest()
        self.verify(source=False)  # Local digest lists alone cannot prove closure.
        with self.assertRaisesRegex(ValueError, "owning file set differs"):
            self.verify()

    def test_corrupted_and_unlisted_files_fail_offline(self):
        target = self.root / "upstream/required.txt"
        raw = target.read_bytes()
        target.write_bytes(raw + b"changed")
        with self.assertRaisesRegex(ValueError, "byte parity failed"):
            self.verify(source=False)
        target.write_bytes(raw)
        (self.root / "upstream/unlisted.txt").write_text("extra")
        with self.assertRaisesRegex(ValueError, "file inventory differs"):
            self.verify(source=False)

    def test_false_source_pin_or_remote_fails(self):
        self.manifest["commit"] = "0" * 40
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "reviewed source"):
            self.verify()
        self.manifest["commit"] = check_source.COMMIT
        self.write_manifest()
        self.git("remote", "set-url", "origin", "git@other.example:FAIR-bioHeaders/FHT-Specification.git")
        with self.assertRaisesRegex(ValueError, "remote"):
            self.verify()


class ReceiptControls(unittest.TestCase):
    def installed_output(self):
        return "\n".join([
            "toolkit: fair-bioheaders 0.11.0; draft pin checkout source",
            "verify (draft lane ON): 34 valid accepted, 57 invalid rejected",
            "verify-links (draft lane ON): 10 vectors with parentLink entries",
            "default path (draft lane OFF): 0 of 93 vectors accepted;",
            "strip: 34 valid vectors compared with the FORMAT.md rule text",
            "combine: 34 valid vectors round-tripped (values, order, verification)",
            "streams (stdin/stdout, draft lane ON): {'verify': 91, 'strip': 34, 'combine': 34}",
            "implementation comparisons: 91; current-contract unsupported/not-run: 2",
            f"staged C1 arithmetic NOT-RUN by installed runtime: 2 {STAGED!r}",
            "OK: (0 finding(s) reported for #9)"])

    def test_unsupported_arithmetic_cannot_become_fabricated_consumer_pass(self):
        output = self.installed_output()
        receipt = installed_receipt(output)
        self.assertFalse(receipt["consumerArithmeticAccepted"])
        self.assertEqual(receipt["notRun"], STAGED)
        for bad in (output.replace("91; current-contract unsupported/not-run: 2", "93; current-contract unsupported/not-run: 0"),
                    output.replace(STAGED[0], "different-case"),
                    output.replace("verify-links (draft lane ON): 10", "verify-links (draft lane ON): 0"),
                    output.replace("'strip': 34", "'strip': 0")):
            with self.assertRaises(RuntimeError):
                installed_receipt(bad)

    def test_unit_count_and_no_skips_are_required(self):
        unit_receipt("Ran 114 tests in 1.2s\n\nOK\n")
        for output in ("Ran 113 tests in 1.2s\n\nOK\n",
                       "Ran 114 tests in 1.2s\n\nOK (skipped=1)\n",
                       "Ran 114 tests in 1.2s\n\nFAILED\n"):
            with self.assertRaises(RuntimeError):
                unit_receipt(output)


if __name__ == "__main__":
    unittest.main()
