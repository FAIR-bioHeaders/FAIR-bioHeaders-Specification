#!/usr/bin/env python3
"""Pinned fallback GFF3 parser runs for issue #210 evidence.

NOTE: The task brief suggested the BioPython GFF parser; Bio.GFF no longer
exists in any modern Biopython (verified: absent from 1.79, 1.83, 1.84, 1.85
sdists and the 1.88 wheel/arm64). Pinned pip alternatives used instead:
  - gff3==1.0.1 ("simple-gff3", https://github.com/hotdogee/gff3-py)
  - gffutils==0.14
Both run in parse/validation and (gffutils) export/conversion-equivalent
modes only. No uploads.
"""
import io
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from make_fixtures import split_lines

import gff3 as gff3_pkg
import gffutils
from gffutils.gffwriter import GFFWriter

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"
OUT = pathlib.Path(__file__).resolve().parent / "outputs"
OUT.mkdir(exist_ok=True)


def recomputed_checksum(data: bytes) -> str:
    import base64, hashlib
    lines = split_lines(data)
    hits = [l for l in lines if l.startswith(b"#~checksum:")]
    target = hits[0] if hits else None
    rest = b"".join(l for l in lines if l is not target)
    return base64.b64encode(hashlib.new("sha512_256", rest).digest()).decode()


def expected_features(path: pathlib.Path):
    return [l.decode() for l in split_lines(path.read_bytes())
            if l and not l.startswith(b"#") and b"\t" in l]


results = {"versions": {"gff3": gff3_pkg.__version__, "gffutils": gffutils.__version__},
           "per_fixture": []}

NAMES = ["fixture1-plain.gff3", "fixture2-ascii-header.gff3",
         "fixture3-raw-utf8.gff3", "fixture4-escaped.gff3"]

for name in NAMES:
    path = FIX / name
    exp = expected_features(path)
    entry = {"fixture": name, "expected_feature_lines": len(exp)}

    # ---------- gff3==1.0.1 (simple-gff3) ----------
    g = {"parser": "gff3==1.0.1"}
    try:
        gf = gff3_pkg.Gff3()
        gf.parse(str(path))
        lines = gf.lines
        g["accepts"] = True
        types = {}
        for ld in lines:
            types[ld["line_type"]] = types.get(ld["line_type"], 0) + 1
        g["line_types"] = types
        comment_lines = [ld for ld in lines if ld["line_type"] == "comment"]
        g["comment_lines_total"] = len(comment_lines)
        g["ordinary_comment_preserved_in_parse"] = any(
            ld["line_raw"].startswith("# ordinary ASCII comment") for ld in comment_lines)
        tilde = [ld["line_raw"] for ld in comment_lines if ld["line_raw"].startswith("#~")]
        g["tilde_lines_classified_as_comment"] = len(tilde)
        g["tilde_annotation_line_raw"] = [t for t in tilde if t.startswith("#~annotation")]
        g["tilde_annotation_codepoints_nonascii"] = [
            [f"U+{ord(c):04X}" for c in t if ord(c) > 0x7F]
            for t in tilde if t.startswith("#~annotation") and any(ord(c) > 0x7F for c in t)]
        feats = [ld for ld in lines if ld["line_type"] == "feature"]
        g["features_parsed"] = len(feats)
        g["features_expected"] = len(exp)
        g["errors_any"] = sum(1 for ld in lines if ld.get("line_errors"))
        err_detail = []
        for ld in lines:
            for e in ld.get("line_errors", []):
                err_detail.append({"line_index": ld["line_index"],
                                   "raw_prefix": ld["line_raw"][:40],
                                   "message": e.get("message"),
                                   "error_type": e.get("error_type")})
        g["errors_detail"] = err_detail[:10]
    except Exception as e:
        g["accepts"] = False
        g["exception"] = f"{type(e).__name__}: {e}"
    entry["simple_gff3"] = g

    # ---------- gffutils==0.14: iterate (validation-equivalent) ----------
    g2 = {"parser": "gffutils==0.14"}
    try:
        feats = list(gffutils.DataIterator(str(path)))
        g2["accepts"] = True
        g2["features_parsed"] = len(feats)
        g2["features_expected"] = len(exp)
        g2["feature_key_tuples_match"] = sorted(
            f["ID"][0] for f in feats) == sorted(
            __import__("re").findall(r"ID=([^;]+)", "\n".join(exp)))
    except Exception as e:
        g2["accepts"] = False
        g2["exception"] = f"{type(e).__name__}: {e}"
    entry["gffutils_iter"] = g2

    # ---------- gffutils create_db + GFFWriter export (conversion-equivalent) ----------
    g3 = {"parser": "gffutils==0.14", "mode": "create_db() sqlite + GFFWriter export"}
    try:
        db = gffutils.create_db(str(path), ":memory:", force=True, keep_order=True)
        g3["db_stored_directives"] = list(db.directives)
        sio = io.StringIO()
        w = GFFWriter(sio)
        n = 0
        for f in db.all_features():
            w.write_rec(f)
            n += 1
        text = sio.getvalue()
        w.close()
        ob = text.encode("utf-8")
        op = OUT / f"gffutils-{name}"
        op.write_bytes(ob)
        g3["accepts"] = True
        g3["features_written"] = n
        ol = split_lines(ob)
        g3["output_file"] = f"outputs/{op.name}"
        g3["output_feature_lines"] = sum(1 for l in ol if l and not l.startswith(b"#") and b"\t" in l)
        g3["output_expected_features"] = len(exp)
        g3["feature_lines_byte_identical_to_input"] = [
            l.decode().rstrip("\n") for l in ol if l and not l.startswith(b"#") and b"\t" in l
        ] == [e.rstrip("\n") for e in exp]
        g3["ordinary_comment_in_output"] = any(l.startswith(b"# ordinary ASCII comment") for l in ol)
        g3["tilde_lines_in_output"] = sum(1 for l in ol if l.startswith(b"#~"))
        g3["directives_in_output"] = [l.decode().rstrip() for l in ol
                                      if l.startswith(b"##") or l.startswith(b"#!")]
        g3["nonascii_bytes_in_output"] = sorted({f"{b:02X}" for b in ob if b >= 0x80})
        g3["output_checksum_recorded"] = None
        g3["output_checksum_note"] = "no #~ line survives export; FH header dropped entirely"
    except Exception as e:
        g3["accepts"] = False
        g3["exception"] = f"{type(e).__name__}: {e}"
    entry["gffutils_export"] = g3

    results["per_fixture"].append(entry)

print(json.dumps(results, indent=2, sort_keys=False))
