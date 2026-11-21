"""A failing process must not certify invalid-vector conformance."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("converter_failure_checker", ROOT / "scripts/check_conformance.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ConverterFailureTests(unittest.TestCase):
    def evaluate(self, invalid, *, known_gaps=None, unsupported=None, only_invalid=False):
        vectors = [{"id": "reject", "file": "invalid.fasta", "format": "fasta", "expected": "invalid"}]
        if not only_invalid:
            vectors.insert(0, {"id": "accept", "file": "valid.fasta", "format": "fasta", "expected": "valid"})
        def run(command, **kwargs):
            if command[-1].endswith("invalid.fasta"):
                return subprocess.CompletedProcess(command, *invalid)
            return subprocess.CompletedProcess(command, 0, "", "")
        with mock.patch.object(checker, "converter_commands", return_value=lambda fmt: ["fake-converter"]), \
                mock.patch.object(checker.subprocess, "run", side_effect=run):
            options = {"unsupported": unsupported}
            if known_gaps is not None:
                options["known_gaps"] = known_gaps
            return checker.check_converter(ROOT, {"vectors": vectors}, "unused", **options)

    def test_clean_rejection_and_acceptance_remain_successful(self):
        self.assertEqual(self.evaluate((1, "", "invalid metadata")), [])

    def test_crashes_abnormal_exits_and_silent_failures_are_not_rejections(self):
        for result in [(1, "", "Traceback (most recent call last):\nRuntimeError: crash"),
                       (2, "", "argument parser failed"), (-9, "", "killed"), (1, "", "")]:
            with self.subTest(result=result):
                problems = self.evaluate(result)
                self.assertEqual(len(problems), 1)
                self.assertIn("reject: converter execution failure", problems[0])

    def test_known_gap_does_not_hide_execution_failure(self):
        problems = self.evaluate((1, "", "Traceback (most recent call last): crash"),
                                 known_gaps={"reject": "known behavior difference"})
        self.assertTrue(any("execution failure" in problem for problem in problems))

    def test_unsupported_text_inside_crash_does_not_skip_the_format(self):
        unsupported = set()
        problems = self.evaluate((1, "", "Traceback (most recent call last): " + checker.UNSUPPORTED),
                                 unsupported=unsupported, only_invalid=True)
        self.assertTrue(any("execution failure" in problem for problem in problems))
        self.assertEqual(unsupported, set())

    def test_legitimate_unsupported_format_remains_explicitly_skipped(self):
        unsupported = set()
        self.assertEqual(self.evaluate((1, "", checker.UNSUPPORTED), unsupported=unsupported,
                                       only_invalid=True), [])
        self.assertEqual(unsupported, {"fasta"})
