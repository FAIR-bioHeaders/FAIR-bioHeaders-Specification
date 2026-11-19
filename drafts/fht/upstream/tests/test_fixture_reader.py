"""Negative controls for the independent fixture reader (scripts/check_fht_fixtures.py).

These tests feed the runner bytes and manifest entries that must NOT pass, so a
reader that quietly accepts them (or crashes instead of reporting) fails here:

- gzip/BGZF input: a truncated member, trailing NUL padding, trailing junk and
  a corrupt trailer are rejected with a clean R1 error, never accepted and
  never a zlib traceback;
- R12: a plain date reads as the string written, not a ``datetime.date``;
- per-vector rule assertions: an invalid vector rejected for a different
  defect than the one its manifest entry declares fails the lane (including
  an R10 entry handed valid bytes);
- malformed manifest input (a parentLink naming a directory, a missing
  statedChecksum or rule) is reported as a failure instead of raising.

Every input is derived from the committed suite; no vector byte is modified.

Local usage (pinned environment; see docs/CI.md):

    python -m unittest tests.test_fixture_reader -v
"""

import base64
import datetime
import gzip
import hashlib
import importlib.util
import json
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check = load("check_fht_fixtures")
        cls.manifest = json.loads(
            (ROOT / "conformance" / "manifest.json").read_text("utf-8"))
        cls.entries = {entry["id"]: entry for entry in cls.manifest["vectors"]}
        cls.lf = (ROOT / "conformance/valid/fht-fasta-lf.fht.fasta").read_bytes()

    def setUp(self):
        self.check.FAILURES.clear()

    def reseal(self, data):
        """Recompute the root checksum so only the intended defect remains."""
        _, position, length = self.check.locate_checksum(data)
        body = data[:position] + data[position + length:]
        value = base64.b64encode(hashlib.new("sha512_256", body).digest())
        return data[:position] + b";~checksum: " + value + b"\n" + data[position + length:]

    # ---------------------------------------------------------------- gzip --
    def test_complete_streams_decompress(self):
        for name in ("fht-fasta-gzip", "fht-fasta-bgzf", "fht-fasta-gzip-multimember"):
            with self.subTest(name=name):
                raw = (ROOT / "conformance" / self.entries[name]["file"]).read_bytes()
                self.assertEqual(self.check.decompress(raw), self.lf)
        self.assertEqual(self.check.decompress(gzip.compress(self.lf, mtime=0)), self.lf)

    def test_incomplete_or_padded_streams_are_rejected_cleanly(self):
        whole = gzip.compress(self.lf, mtime=0)
        bad_crc = whole[:-8] + bytes([whole[-8] ^ 0xFF]) + whole[-7:]
        cases = {
            "truncated trailer": whole[:-6],
            "truncated deflate": whole[:40],
            "truncated header": whole[:5],
            "trailing NUL padding": whole + b"\x00" * 16,
            "trailing junk": whole + b"junk",
            "corrupt CRC-32": bad_crc,
            "empty": b"",
        }
        for name, data in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(self.check.CompressionError) as caught:
                    self.check.decompress(data)
                self.assertTrue(str(caught.exception).startswith("R1:"))

    def test_optional_gzip_header_crc_covers_all_header_fields_and_each_member(self):
        whole = gzip.compress(self.lf, mtime=0)
        # FHCRC plus FEXTRA, FNAME and FCOMMENT: CRC covers every header byte.
        header = whole[:3] + bytes([0x1E]) + whole[4:10]
        header += b"\x03\x00abcfile.fasta\x00comment\x00"
        crc = (zlib.crc32(header) & 0xFFFF).to_bytes(2, "little")
        member = header + crc + whole[10:]
        self.assertEqual(zlib.decompress(member, 31), self.lf)
        self.assertEqual(self.check.decompress(member), self.lf)
        self.assertEqual(self.check.decompress(whole + member), self.lf * 2)
        damaged = header + bytes([crc[0] ^ 1, crc[1]]) + whole[10:]
        for raw in (damaged, whole + damaged):
            with self.assertRaises(zlib.error):
                zlib.decompress(raw[len(whole):] if raw.startswith(whole) else raw, 31)
            with self.assertRaisesRegex(self.check.CompressionError, "header CRC-16"):
                self.check.decompress(raw)

    def test_optional_gzip_header_crc_truncation_is_a_clean_r1_failure(self):
        whole = gzip.compress(self.lf, mtime=0)
        header = whole[:3] + bytes([2]) + whole[4:10]
        for suffix in (b"", b"\x00"):
            with self.assertRaisesRegex(self.check.CompressionError, "R1: truncated gzip header CRC-16"):
                self.check.decompress(header + suffix)

    def test_truncated_vector_is_rejected_as_r1(self):
        entry = self.entries["fht-fasta-gzip-truncated"]
        counts = self.check.lane_vectors([entry])
        self.assertEqual(self.check.FAILURES, [])
        self.assertEqual(counts.get("rejected-by-shape"), 1)

    # ----------------------------------------------------------------- R12 --
    def test_plain_date_is_the_string_written(self):
        data = self.reseal(self.lf.replace(b";~dateCreated: '2026-11-10'",
                                           b";~dateCreated: 2026-11-10"))
        record = self.check.parse_metadata(data)
        self.assertEqual(record["dateCreated"], "2026-11-10")
        self.assertNotIsInstance(record["dateCreated"], datetime.date)
        self.assertEqual(self.check.schema_errors(record), [])

    def test_r12_ambiguous_scalars_stay_invalid(self):
        for text in (b"010", b"1_000", b"1:30", b"yes", b"1e3"):
            with self.subTest(value=text):
                data = self.reseal(self.lf.replace(
                    b";~version: '1.0.0'", b";~version: '1.0.0'\n;~x-n: " + text))
                with self.assertRaises(self.check.StrictError) as caught:
                    self.check.parse_metadata(data)
                self.assertTrue(str(caught.exception).startswith("R12:"))

    # -------------------------------------------- per-vector rule assertion --
    def test_wrong_contract_defect_fails_the_vector(self):
        data = self.reseal(self.lf.replace(b";~schemaVersion: '1.0'",
                                           b";~schemaVersion: '9.9'"))
        outcome = self.check.check_expected_invalid(
            self.entries["fht-fasta-bad-assembly-type"], data, "probe")
        self.assertIsNone(outcome)
        self.assertIn("errors differ", self.check.FAILURES[0])

    def test_wrong_shape_rule_fails_the_vector(self):
        data = self.reseal(self.lf.replace(
            b";~version: '1.0.0'", b";~version: '1.0.0'\n;~x-n: 010"))
        outcome = self.check.check_expected_invalid(
            self.entries["fht-fasta-duplicate-key"], data, "probe")
        self.assertIsNone(outcome)
        self.assertIn("rejects it under R12", self.check.FAILURES[0])

    def test_r10_entry_with_valid_bytes_fails(self):
        outcome = self.check.check_expected_invalid(
            self.entries["fht-fasta-header-after-record"], self.lf, "probe")
        self.assertIsNone(outcome)
        self.assertIn("accepts it", self.check.FAILURES[0])

    def test_v5_outcome_is_computed_against_the_fhr_schema(self):
        entry = self.entries["fht-fasta-schema-w3id-release-without-fht"]
        data = self.check.read_vector(entry)
        self.assertEqual(self.check.check_expected_invalid(entry, data, "probe"), "fhr")
        # The same entry over a record whose V5 reading is not the measured
        # FHR rejection (here: a valid FHT record citing raw main) must fail.
        self.assertIsNone(self.check.check_expected_invalid(entry, self.lf, "probe"))

    # ------------------------------------------------- malformed manifests --
    def test_parent_link_naming_a_directory_is_reported(self):
        entry = self.entries["fht-fasta-parent-transcribed-from"]
        data = self.check.read_vector(entry)
        record = self.check.parse_metadata(data)
        link = dict(entry["parentLink"][0], file="parents")
        verdicts = self.check.check_parent_links(data, record, [link], "probe")
        self.assertEqual(verdicts, [None])
        self.assertIn("not a regular file", self.check.FAILURES[0])

    def test_missing_stated_checksum_is_reported(self):
        entry = self.entries["fht-fasta-parent-mismatched"]
        link = {key: value for key, value in entry["parentLink"][0].items()
                if key != "statedChecksum"}
        broken = dict(entry, parentLink=[link])
        data = self.check.read_vector(entry)
        self.assertIsNone(self.check.check_expected_invalid(broken, data, "probe"))
        self.assertTrue(any("statedChecksum" in failure
                            for failure in self.check.FAILURES))
        self.check.FAILURES.clear()
        self.check.lane_manifest({"rules": self.manifest["rules"], "retired": [],
                                  "vectors": [broken]})
        self.assertTrue(any("statedChecksum" in failure
                            for failure in self.check.FAILURES))

    def test_entry_without_rule_is_reported_not_raised(self):
        entry = {key: value for key, value in
                 self.entries["fht-fasta-duplicate-key"].items() if key != "rule"}
        kept = self.check.well_formed({"vectors": [entry]})
        self.assertEqual(kept["vectors"], [])
        self.assertIn("lacks ['rule']", self.check.FAILURES[0])


if __name__ == "__main__":
    unittest.main()
