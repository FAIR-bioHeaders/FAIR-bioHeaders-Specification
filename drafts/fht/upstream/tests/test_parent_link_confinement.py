"""Regression tests for checked parentLink path confinement (#39 follow-up).

A checked-pass or checked-fail parentLink must name a file inside the
distributed conformance/ tree. Before this fix the runner only required the
"file" value to be truthy and then read it with ``CONFORMANCE / file``,
which Python resolves verbatim for absolute paths and follows ``../``
segments through — so a manifest could make the byte-exact suite depend on
a file outside the tree that ships with it (raised on PR #39 by the Copilot
review; conformance/README.md's "Finalized field semantics" already required
"a named parent file inside this directory"). The enforcement lives in
scripts/check_fht_fixtures.py: checked_parent_path(), lane_manifest() and
check_parent_links().

Every input here is synthetic or read from the committed suite; no vector
byte is modified.

Local usage (pinned environment; see docs/CI.md):

    python -m pip install -r requirements-validation.txt
    python -m unittest tests.test_parent_link_confinement -v
"""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParentLinkConfinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check = load("check_fht_fixtures")
        cls.manifest = json.loads(
            (ROOT / "conformance" / "manifest.json").read_text("utf-8"))
        # A real checked-pass link pair from the committed suite, used both
        # as the positive control and as the base for the escape variants.
        passes = [e for e in cls.manifest["vectors"]
                  if any(link.get("result") == "checked-pass"
                         for link in e.get("parentLink") or [])]
        cls.entry = passes[0]
        cls.data = (ROOT / "conformance" / cls.entry["file"]).read_bytes()
        cls.record = cls.check.parse_metadata(cls.data)

    def setUp(self):
        self.check.FAILURES.clear()

    def link(self, result, file_value, cited=None):
        if cited is None:
            cited = next(link["statedChecksum"]
                         for link in self.entry["parentLink"]
                         if link["result"] == "checked-pass")
        return {"result": result, "statedChecksum": cited, "file": file_value}

    # ------------------------------------------------------------- helper --

    def test_helper_resolves_in_suite_path_inside_conformance(self):
        resolved = self.check.checked_parent_path("parents/parent-genome.fhr.fasta")
        self.assertIsNotNone(resolved)
        self.assertTrue(resolved.is_relative_to(self.check.CONFORMANCE))
        self.assertTrue(resolved.is_file())

    def test_helper_rejects_traversal_absolute_and_bare_directory(self):
        for value in ("../README.md", "../escape.fht.fasta",
                      "parents/../../escape.fht.fasta", "/etc/passwd",
                      "/tmp/outside.fht.fasta", "."):
            with self.subTest(value=value):
                self.assertIsNone(self.check.checked_parent_path(value))

    def test_helper_admits_an_absolute_path_that_stays_in_the_tree(self):
        # The rule is confinement, not path style: a resolved location
        # inside conformance/ is a legitimate parent wherever it was
        # spelled from (lane_manifest still requires it to exist there).
        inside = self.check.CONFORMANCE / "parents" / "parent-genome.fhr.fasta"
        resolved = self.check.checked_parent_path(str(inside))
        self.assertIsNotNone(resolved)
        self.assertTrue(resolved.is_relative_to(self.check.CONFORMANCE))

    # ------------------------------------------------ verification reads --

    def test_check_parent_links_accepts_the_committed_in_suite_parent(self):
        self.check.check_parent_links(
            self.data, self.record, self.entry["parentLink"], self.entry["id"])
        self.assertEqual(self.check.FAILURES, [])

    def test_check_parent_links_rejects_traversal_parent(self):
        for result in ("checked-pass", "checked-fail"):
            with self.subTest(result=result):
                self.check.FAILURES.clear()
                self.check.check_parent_links(
                    self.data, self.record,
                    [self.link(result, "../parents/outside.fht.fasta")],
                    f"synthetic/{result}-traversal")
                self.assertEqual(len(self.check.FAILURES), 1)
                self.assertIn("must resolve inside conformance/",
                              self.check.FAILURES[0])

    def test_check_parent_links_rejects_absolute_parent(self):
        self.check.check_parent_links(
            self.data, self.record,
            [self.link("checked-pass", "/tmp/outside.fht.fasta")],
            "synthetic/absolute")
        self.assertEqual(len(self.check.FAILURES), 1)
        self.assertIn("must resolve inside conformance/", self.check.FAILURES[0])

    # ------------------------------------------------------ manifest lane --

    def synthetic_manifest(self, link):
        entry = dict(self.entry)
        entry["id"] = "synthetic/parentlink-confinement"
        entry["parentLink"] = [link]
        return {"rules": self.manifest["rules"], "retired": [],
                "vectors": [entry]}

    def lane_manifest_failures_containing(self, needle):
        return [f for f in self.check.FAILURES if needle in f]

    def test_lane_manifest_rejects_traversal_parent(self):
        self.check.lane_manifest(
            self.synthetic_manifest(
                self.link("checked-pass", "../parents/outside.fht.fasta")))
        found = self.lane_manifest_failures_containing(
            "must resolve inside conformance/")
        self.assertEqual(len(found), 1, self.check.FAILURES)

    def test_lane_manifest_rejects_absolute_parent(self):
        self.check.lane_manifest(
            self.synthetic_manifest(
                self.link("checked-fail", "/tmp/outside.fht.fasta")))
        found = self.lane_manifest_failures_containing(
            "must resolve inside conformance/")
        self.assertEqual(len(found), 1, self.check.FAILURES)

    def test_lane_manifest_requires_in_suite_parent_to_exist(self):
        self.check.lane_manifest(
            self.synthetic_manifest(
                self.link("checked-pass",
                          "parents/no-such-parent.fht.fasta")))
        found = self.lane_manifest_failures_containing(
            "does not exist inside conformance/")
        self.assertEqual(len(found), 1, self.check.FAILURES)

    def test_lane_manifest_keeps_the_naming_rules(self):
        # Existing rules retained: an unchecked link must name no file and
        # a checked verdict must name one.
        self.check.lane_manifest(
            self.synthetic_manifest(
                self.link("unchecked", "parents/parent-genome.fhr.fasta")))
        self.assertEqual(
            len(self.lane_manifest_failures_containing(
                "unchecked parentLink must name no file")), 1,
            self.check.FAILURES)
        self.check.FAILURES.clear()
        no_file = self.link("checked-pass",
                            "parents/parent-genome.fht.fasta")
        del no_file["file"]
        self.check.lane_manifest(self.synthetic_manifest(no_file))
        self.assertEqual(
            len(self.lane_manifest_failures_containing(
                "checked-pass parentLink must name a file")), 1,
            self.check.FAILURES)


if __name__ == "__main__":
    unittest.main()
