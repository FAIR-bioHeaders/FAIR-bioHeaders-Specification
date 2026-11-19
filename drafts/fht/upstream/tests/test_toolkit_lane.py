"""Controls for the installed-artifact harness, independent of a toolkit install."""
import base64
import hashlib
import contextlib
import io
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "toolkit_lane", Path(__file__).resolve().parents[1] / "scripts/run_toolkit_lane.py"
)
lane = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lane)


class StreamControls(unittest.TestCase):
    def setUp(self):
        lane.FAILURES.clear()

    def test_empty_stream_lane_is_a_failure(self):
        with contextlib.redirect_stdout(io.StringIO()):
            lane.lane_streams(None, [], None)
        self.assertIn("zero cases", lane.FAILURES[0])

    def test_corrupt_stdout_is_not_hidden_by_success_exit(self):
        vector = {"id": "control", "file": "valid/control.fasta", "expected": "valid"}

        class BrokenToolkit:
            def run_bytes(self, *args, **kwargs):
                return subprocess.CompletedProcess(args, 0, b"corrupted", b"diagnostic")

            def run(self, *args, **kwargs):
                return 1, "setup deliberately unavailable"

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(Path, "read_bytes", return_value=b">id\nAC\n"), \
                    patch.object(lane, "place", return_value=Path(tmp) / "input"):
                with contextlib.redirect_stdout(io.StringIO()):
                    lane.lane_streams(BrokenToolkit(), [vector], tmp)
        self.assertTrue(any("strip changed payload" in x for x in lane.FAILURES))

    def test_stream_combine_metadata_corruption_is_detected(self):
        vector = next(v for v in lane.load_suite() if v["id"] == "fht-fasta-lf")
        original = lane.vector_bytes(vector)
        payload = lane.strip_expectation(original)
        lines = original.splitlines(keepends=True)
        changed = b"".join(
            b";~transcriptome: corrupted by the writer\n"
            if line.startswith(b";~transcriptome:") else line
            for line in lines)
        covered = b"".join(line for line in changed.splitlines(keepends=True)
                            if not line.startswith(b";~checksum:"))
        checksum = base64.b64encode(hashlib.new("sha512_256", covered).digest())
        changed = b"".join(b";~checksum: " + checksum + b"\n"
                            if line.startswith(b";~checksum:") else line
                            for line in changed.splitlines(keepends=True))
        self.assertEqual(lane.strip_expectation(changed), payload)
        self.assertNotEqual(changed, original)

        class MetadataLosingToolkit:
            def run_bytes(self, *args, **kwargs):
                output = changed if args[0] == "combine" else (
                    payload if args[0] == "strip" else b"Checksum verified.")
                return subprocess.CompletedProcess(args, 0, output, b"")

            def run(self, *args, **kwargs):
                return 0, ""

        with tempfile.TemporaryDirectory() as tmp, \
                contextlib.redirect_stdout(io.StringIO()):
            lane.lane_streams(MetadataLosingToolkit(), [vector], tmp)
        self.assertTrue(any("combine changed metadata" in x for x in lane.FAILURES))
        self.assertEqual(len(lane.FAILURES), 1)

    def test_signature_preserves_nested_order_and_scalar_types(self):
        def header(nested):
            return (";~checksum: ignored\n;~metadataAuthor:\n" + nested).encode()

        before = header(";~- name: Example\n;~  uri: '1'\n")
        reordered = header(";~- uri: '1'\n;~  name: Example\n")
        mistyped = header(";~- name: Example\n;~  uri: 1\n")
        self.assertNotEqual(lane.metadata_signature(before), lane.metadata_signature(reordered))
        self.assertNotEqual(lane.metadata_signature(before), lane.metadata_signature(mistyped))
        self.assertEqual(lane.metadata_signature(before), lane.metadata_signature(
            before.replace(b"checksum: ignored", b"checksum: regenerated")))
        nested = b";~checksum: root\n;~derivedFrom:\n;~- checksum: parent-one\n"
        self.assertNotEqual(lane.metadata_signature(nested), lane.metadata_signature(
            nested.replace(b"parent-one", b"parent-two")))

    def test_mixed_capability_is_narrow_and_does_not_rewrite_expectations(self):
        vector = next(v for v in lane.load_suite() if v["id"] == lane.MIXED_VECTOR)
        other = next(v for v in lane.load_suite() if v["id"] == "fht-fasta-lf")
        old = {"$defs": {"MoleculeType": {"enum": ["mRNA", "rRNA", "tRNA", "transcribed RNA"]}}}
        compared, unsupported = lane.partition_mixed_capability([other, vector], old)
        self.assertEqual(compared, [other])
        self.assertEqual(unsupported, [vector])
        self.assertEqual(vector["expected"], "valid")
        old["$defs"]["MoleculeType"]["enum"].append("mixed")
        self.assertEqual(lane.partition_mixed_capability([other, vector], old),
                         ([other, vector], []))
        malformed = dict(vector, expected="invalid")
        with self.assertRaisesRegex(ValueError, "normative valid/mixed"):
            lane.partition_mixed_capability([malformed], old)
        with self.assertRaisesRegex(ValueError, "no inspectable"):
            lane.partition_mixed_capability([vector], {})

    def test_unsupported_mixed_probe_cannot_hide_an_unexpected_result(self):
        vector = next(v for v in lane.load_suite() if v["id"] == lane.MIXED_VECTOR)

        class UnexpectedAccept:
            def run(self, *args, **kwargs):
                return 0, "Checksum verified."

        class WrongRejection:
            def run(self, *args, **kwargs):
                return 1, "checksum failure for moleculeType mixed"

        for toolkit in (UnexpectedAccept(), WrongRejection()):
            lane.FAILURES.clear()
            with patch.object(lane, "place", return_value=Path("unused")), \
                    contextlib.redirect_stdout(io.StringIO()):
                lane.lane_unsupported_mixed(toolkit, [vector], None)
            self.assertIn("did not specifically reject", lane.FAILURES[0])

    def test_unsupported_mixed_requires_one_enum_diagnostic(self):
        vector = next(v for v in lane.load_suite() if v["id"] == lane.MIXED_VECTOR)
        message = "schema validation failed at $.moleculeType: 'mixed' is not one of ['mRNA']"

        class EnumRejection:
            def run(self, *args, **kwargs):
                return 1, message

        with patch.object(lane, "place", return_value=Path("unused")), \
                contextlib.redirect_stdout(io.StringIO()):
            lane.lane_unsupported_mixed(EnumRejection(), [vector], None)
        self.assertEqual(lane.FAILURES, [])
        message += "\nschema validation failed at $.checksum: unrelated error"
        with patch.object(lane, "place", return_value=Path("unused")), \
                contextlib.redirect_stdout(io.StringIO()):
            lane.lane_unsupported_mixed(EnumRejection(), [vector], None)
        self.assertIn("did not specifically reject", lane.FAILURES[0])

    def test_unsupported_mixed_rejects_enum_plus_checksum_failure(self):
        vector = next(v for v in lane.load_suite() if v["id"] == lane.MIXED_VECTOR)
        enum = ("FHT: schema validation failed at $.moleculeType: "
                "'mixed' is not one of ['mRNA', 'rRNA', 'tRNA', 'transcribed RNA']")

        class CombinedRejection:
            def run(self, *args, **kwargs):
                return 1, enum + "\n" + checksum

        for checksum in ("Checksum verification failed.",
                         "FHT: Checksum verification failed.",
                         "FHR: Checksum verification failed."):
            with self.subTest(diagnostic=checksum):
                lane.FAILURES.clear()
                with patch.object(lane, "place", return_value=Path("unused")), \
                        contextlib.redirect_stdout(io.StringIO()):
                    lane.lane_unsupported_mixed(CombinedRejection(), [vector], None)
                self.assertIn("did not specifically reject", lane.FAILURES[0])

    def test_installed_contract_partition_only_splits_contract_differences(self):
        import json
        suite = {v["id"]: v for v in lane.load_suite()}
        current = json.loads((Path(lane.ROOT) / "fht.json").read_text())
        picked = [suite["fht-fasta-lf"], suite["fht-fasta-blank-version-separator"],
                  suite["fht-fasta-utf8-bom"]]
        self.assertEqual(lane.partition_installed_contract(picked, current), (picked, []))
        older = json.loads(json.dumps(current))
        for root in (older, older["$defs"]["FHT"]):
            root["properties"]["version"].pop("pattern")
        compared, dependent = lane.partition_installed_contract(picked, older)
        self.assertEqual([v["id"] for v in compared], ["fht-fasta-lf", "fht-fasta-utf8-bom"])
        self.assertEqual(dependent, [(suite["fht-fasta-blank-version-separator"], True)])

    def test_installed_contract_probe_requires_agreement_with_installed_bytes(self):
        vector = next(v for v in lane.load_suite()
                      if v["id"] == "fht-fasta-blank-version-separator")

        class Rejects:
            def run(self, *args, **kwargs):
                return 1, "schema validation failed"

        with patch.object(lane, "place", return_value=Path("unused")), \
                contextlib.redirect_stdout(io.StringIO()):
            lane.lane_installed_contract(Rejects(), [(vector, True)], None)
        self.assertIn("installed draft bytes accept", lane.FAILURES[0])

    def test_staged_arithmetic_is_named_semantic_only_and_actual_runtime_probed(self):
        suite = {v["id"]: v for v in lane.load_suite()}
        arithmetic = suite["fht-fasta-completeness-sum-below-total"]
        other = suite["fht-fasta-blank-version-separator"]

        class Accepts:
            def run(self, *args, **kwargs):
                return 0, "Checksum verified."

        class Rejects:
            def run(self, *args, **kwargs):
                return 1, "schema validation failed"

        for toolkit, vector, staged, findings, failure in (
                (Accepts(), arithmetic, 1, 0, False),
                (Accepts(), other, 0, 1, False),
                (Rejects(), arithmetic, 1, 0, True)):
            lane.FAILURES.clear()
            lane.FINDINGS.clear()
            lane.STAGED_COMPLETENESS.clear()
            with patch.object(lane, "place", return_value=Path("unused")), \
                    contextlib.redirect_stdout(io.StringIO()):
                lane.lane_installed_contract(toolkit, [(vector, True)], None,
                                             stage_completeness=True)
            self.assertEqual(len(lane.STAGED_COMPLETENESS), staged)
            self.assertEqual(len(lane.FINDINGS), findings)
            self.assertEqual(bool(lane.FAILURES), failure)

    def test_named_toolkit_default_cannot_accept_fht(self):
        class IncorrectDefault:
            def version(self):
                return "0.11.0"

            def run(self, *args, **kwargs):
                return 0, "Checksum verified."

        with patch.object(lane, "place", return_value=Path("unused")), \
                contextlib.redirect_stdout(io.StringIO()):
            lane.lane_default_path(IncorrectDefault(), [{"id": "control"}], None)
        self.assertIn("draft lane disabled", lane.FAILURES[0])

    def test_binary_transport_keeps_diagnostic_stderr_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "bin/bioheaders"
            binary.parent.mkdir()
            binary.touch()
            toolkit = lane.Toolkit(tmp)
            result = subprocess.CompletedProcess([], 0, b"payload\r\n", b"warning\n")
            with patch.object(lane.subprocess, "run", return_value=result) as run:
                actual = toolkit.run_bytes("strip", "-", "-", data=b"input\r\n")
            self.assertEqual(actual.stdout, b"payload\r\n")
            self.assertEqual(run.call_args.kwargs["input"], b"input\r\n")
            self.assertEqual(run.call_args.kwargs["timeout"], 60)
            self.assertNotIn("text", run.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
