# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The INSDC coverage review (docs/insdc-coverage.md, issue #157) stays complete and pinned.

The requirement IDs of the pinned INSDC minimum specifications are listed in
tests/fixtures/insdc-requirements.json. These tests check that the matrix has
exactly one row for each, that every disposition is final and links its
follow-up issue, that FHT rows are marked draft, and that the assessed
contract versions are still the ones in fhr.json, fhp.json and fhgff3.json.
They run offline; they check link format, not that the issues exist.
"""

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "insdc-coverage.md"
FIXTURE = ROOT / "tests" / "fixtures" / "insdc-requirements.json"
SCHEMAS = {"FHR": "fhr.json", "FHP": "fhp.json", "FHGFF3": "fhgff3.json"}

HEADER = ["ID", "INSDC requirement", "FH type(s)", "Cov.", "Location in FH", "Disposition"]
DISPOSITION = re.compile(r"^\*\*(Covered|Partial|Out of scope|Follow-up)\*\*(.*)$")
# Disposition -> the coverage symbols it may be paired with.
COVERAGE = {"Covered": {"✅"}, "Partial": {"◐"}, "Out of scope": {"—"}, "Follow-up": {"◐", "✗"}}
ISSUE_LINK = re.compile(r"\[([A-Za-z0-9-]*)#(\d+)\]\(https://github\.com/FAIR-bioHeaders/([A-Za-z0-9-]+)/issues/(\d+)\)")
SPEC_REPO = "FAIR-bioHeaders-Specification"


def cells(line):
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def matrix_rows(text):
    """Rows of the section-2 tables, each a list of cells, with the table header checked."""
    section = text.split("\n## 2. Coverage matrix\n", 1)[1].split("\n## 3.", 1)[0]
    rows, headers = [], []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        row = cells(line)
        if row[0] == "ID":
            headers.append(row)
        elif not set(row[0]) <= set("- "):
            rows.append(row)
    return headers, rows


class InsdcCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.headers, cls.rows = matrix_rows(cls.text)

    def test_tables_have_the_six_columns(self):
        self.assertEqual(len(self.headers), 8, "one table per INSDC section in §2")
        for header in self.headers:
            self.assertEqual(header, HEADER)
        for row in self.rows:
            with self.subTest(row=row[0]):
                self.assertEqual(len(row), len(HEADER))

    def test_every_pinned_requirement_has_exactly_one_row(self):
        pinned = [rid for category in self.fixture["categories"].values()
                  for rid in category["requirements"]]
        self.assertEqual(len(pinned), len(set(pinned)), "duplicate IDs in the fixture")
        listed = [rid.strip() for row in self.rows for rid in row[0].split(" / ")]
        duplicates = sorted({rid for rid in listed if listed.count(rid) > 1})
        self.assertEqual(duplicates, [], "IDs with more than one row")
        self.assertEqual(sorted(set(pinned) - set(listed)), [], "pinned IDs missing from the matrix")
        self.assertEqual(sorted(set(listed) - set(pinned)), [], "matrix IDs not in the fixture")

    def test_dispositions_are_final_and_match_coverage(self):
        for row in self.rows:
            rid, coverage, disposition = row[0], row[3], row[5]
            with self.subTest(row=rid):
                match = DISPOSITION.match(disposition)
                self.assertIsNotNone(match, f"{rid}: disposition must start with a bold final status")
                status, rest = match.groups()
                self.assertIn(coverage, COVERAGE[status], f"{rid}: {status} with coverage {coverage}")
                self.assertRegex(rest, r" — \S", f"{rid}: one-line reason after an em dash")
                self.assertNotRegex(disposition.lower(), r"provisional|tbd|todo|to be decided")
                if status == "Follow-up":
                    self.assertRegex(rest.split(" — ", 1)[0], ISSUE_LINK,
                                     f"{rid}: a follow-up names its issue before the reason")

    def test_issue_links_are_well_formed(self):
        links = ISSUE_LINK.findall(self.text)
        self.assertTrue(links)
        for prefix, text_number, repo, url_number in links:
            with self.subTest(link=f"{prefix}#{text_number}"):
                self.assertEqual(text_number, url_number)
                self.assertIn(prefix, ("", SPEC_REPO) if repo == SPEC_REPO else (repo,))
        # A bare or malformed reference to an issue URL would bypass the check above.
        for url in re.findall(r"https://github\.com/FAIR-bioHeaders/[^)\s]*/issues/[^)\s]*", self.text):
            self.assertRegex(url, r"^https://github\.com/FAIR-bioHeaders/[A-Za-z0-9-]+/issues/\d+$")

    def test_follow_ups_are_listed(self):
        related = self.text.split("\n### Related follow-ups\n", 1)[1].split("\n## ", 1)[0]
        listed = {(repo, number) for _, _, repo, number in ISSUE_LINK.findall(related)}
        for row in self.rows:
            if row[5].startswith("**Follow-up**"):
                for _, _, repo, number in ISSUE_LINK.findall(row[5]):
                    self.assertIn((repo, number), listed, f"{row[0]} links an issue not in Related follow-ups")

    def test_fht_rows_are_marked_draft(self):
        for row in self.rows:
            for cell in row[2:5]:
                with self.subTest(row=row[0]):
                    self.assertNotRegex(cell, r"\bFHT\b(?! \(draft\))")

    def test_pinned_insdc_commit(self):
        commit = self.fixture["commit"]
        self.assertRegex(commit, r"^[0-9a-f]{40}$")
        self.assertIn(f"`{commit}`", self.text)
        for linked in re.findall(r"insdc/minimum-specifcations/tree/([^/)]+)/", self.text):
            self.assertEqual(linked, commit)
        for name, category in self.fixture["categories"].items():
            with self.subTest(category=name):
                self.assertEqual(category["version"], "v1.0")
                self.assertTrue(category["document"].startswith(f"{name}/Current version/"))

    def test_assessed_contract_versions_are_current(self):
        line = next(line for line in self.text.splitlines()
                    if line.startswith("- **FAIR-bioHeaders, released**"))
        for header, file in SCHEMAS.items():
            current = json.loads((ROOT / file).read_text(encoding="utf-8"))["properties"]["schemaVersion"]["enum"]
            with self.subTest(header=header):
                assessed = re.search(rf"\b{header}\b[^`]*(?:`schemaVersion` )?`([0-9]+\.[0-9]+)`", line)
                self.assertIsNotNone(assessed)
                self.assertEqual([assessed.group(1)], current,
                                 f"{header} changed: re-assess docs/insdc-coverage.md (#157)")


if __name__ == "__main__":
    unittest.main()
