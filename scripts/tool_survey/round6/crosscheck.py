#!/usr/bin/env python3
"""Independent checksum cross-check + FH-aware reader equivalence proof.

Part 1: compute the FH checksum with our own R1-R4 implementation
(make_fixtures.fh_checksum) and with the pinned fair-bioheaders 0.9.0 library
internal (bioheaders.cli.SequenceScan), and compare to the recorded value.
Part 2: read fixture3 and fixture4 metadata with the FH-aware reader
(bioheaders.gff3.header_report) and prove annotation decodes identically and
round-trips.
"""
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from make_fixtures import fh_checksum  # our independent R1-R4 implementation

from bioheaders.cli import SequenceScan, open_input, read_chunks
from bioheaders import fhr
from bioheaders.gff3 import header_report

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"

print("== part 1: independent checksum cross-check ==")
for p in sorted(FIX.glob("fixture*.gff3")):
    sha256 = hashlib.sha256(p.read_bytes()).hexdigest()
    mine = fh_checksum(p) if b"#~checksum:" in p.read_bytes() else None
    tool = None
    if mine:
        with open_input(str(p)) as stream:
            scan = SequenceScan(read_chunks(stream), "gff3")
        tool = scan.checksum()
    recorded = None
    if mine:
        with open_input(str(p)) as stream:
            scan = SequenceScan(read_chunks(stream), "gff3")
        data = fhr()
        data._input_header_lines(scan.header, scan.prefix)
        recorded = data.__dict__.get("checksum")
    print(json.dumps({
        "file": p.name,
        "sha256": sha256,
        "fh_independent": mine,
        "fh_tool_0.9.0": tool,
        "fh_recorded_in_header": recorded,
        "match": (mine == tool == recorded) if mine else "n/a (no header)",
    }))

print("\n== part 2: decoded-value equivalence, fixtures 3 vs 4 ==")
vals = {}
for name in ("fixture3-raw-utf8.gff3", "fixture4-escaped.gff3"):
    rep = header_report(str(FIX / name))
    p = FIX / name
    with open_input(str(p)) as stream:
        scan = SequenceScan(read_chunks(stream), "gff3")
    data = fhr()
    data._input_header_lines(scan.header, scan.prefix)
    ann = data.__dict__["annotation"]
    vals[name] = ann
    print(json.dumps({
        "file": name,
        "header_type": rep["header_type"],
        "yaml_ok": rep["yaml"]["ok"],
        "checksum_ok": rep["checksum"]["ok"],
        "schema_ok": rep["schema"]["ok"],
        "genome_link": rep["genome_link"]["ok"],
        "annotation_value": ann,
        "codepoints": [f"U+{ord(c):04X}" for c in ann],
    }))
print("equal_decoded_values:", vals["fixture3-raw-utf8.gff3"] == vals["fixture4-escaped.gff3"])
target = "Caf\u00e9 annotation"
print("matches_expected_literal:", all(v == target for v in vals.values()))

print("\n== part 2b: round-trip (reader -> YAML bytes -> reader) ==")
import yaml
for name, val in vals.items():
    text = yaml.dump({"annotation": val}, allow_unicode=False, default_style=None)
    back = yaml.safe_load(text)["annotation"]
    print(json.dumps({
        "file": name,
        "yaml_dump_ascii_only": text.rstrip("\n"),
        "dump_bytes_hex": text.encode("ascii", errors="strict").hex(),
        "roundtrip_equal": back == val == target,
    }))
