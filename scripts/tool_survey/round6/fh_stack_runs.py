#!/usr/bin/env python3
"""FH-stack (fair-bioheaders==0.9.0) behavior evidence + copied-checksum test.

1. `bioheaders strip` on fixtures 2-4: does it keep ordinary comments and all
   other payload bytes? (FORMAT.md: "Strip removes complete FHR lines and
   leaves ordinary comments intact.")
2. `bioheaders combine` regeneration: rewritten header + recomputed checksum
   must verify.
3. Copied-checksum scenario (issue's final checklist item): fixture 3's exact
   header lines (checksum line included) copied onto fixture 4's bytes -> the
   stale checksum claim must be detected and rejected.
"""
import hashlib
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from make_fixtures import fh_checksum, split_lines

ROOT = pathlib.Path(__file__).resolve().parent
FIX = ROOT / "fixtures"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
BH = str(ROOT / ".venv/bin/bioheaders")

results = []

def run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return {"cmd": " ".join(str(c) for c in cmd), "exit": p.returncode,
            "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

# metadata extracted (without checksum) for the combine test, from fixture 4
meta4_lines = [l.decode().rstrip("\n").removeprefix("#~")
               for l in split_lines((FIX / "fixture4-escaped.gff3").read_bytes())
               if l.startswith(b"#~") and not l.startswith(b"#~checksum:")]
meta4 = OUT / "fixture4-metadata.yaml"
meta4.write_text("\n".join(meta4_lines) + "\n", encoding="utf-8")

# 1. strip each headed fixture
for name in ["fixture2-ascii-header.gff3", "fixture3-raw-utf8.gff3", "fixture4-escaped.gff3"]:
    src = FIX / name
    dst = OUT / f"stripped-{name}"
    r = run([BH, "strip", str(src), str(dst)])
    payload_same = dst.exists() and dst.read_bytes() == (FIX / "payload.gff3").read_bytes()
    ordinary = any(l.startswith(b"# ordinary ASCII comment") for l in split_lines(dst.read_bytes())) if dst.exists() else None
    tilde_left = sum(1 for l in split_lines(dst.read_bytes()) if l.startswith(b"#~")) if dst.exists() else None
    results.append({"step": "strip", "fixture": name, **r,
                    "output_equals_plain_payload": payload_same,
                    "ordinary_comment_kept": ordinary,
                    "tilde_lines_remaining": tilde_left})
    # verify on stripped output: should report no header
    results.append({"step": "verify-stripped", "fixture": name,
                    **run([BH, "verify", str(dst)])})

# 2. combine: regenerate fixture 4 from payload + metadata (checksum recomputed)
combo = OUT / "combined-from-payload.gff3"
r = run([BH, "combine", str(meta4), str(FIX / "payload.gff3"), "-o", str(combo), "--type", "gff3"])
r["output_file"] = str(combo.relative_to(ROOT))
if combo.exists():
    b = combo.read_bytes()
    r["byte_identical_to_fixture4"] = b == (FIX / "fixture4-escaped.gff3").read_bytes()
    r["nonascii_bytes"] = sorted({f"{x:02X}" for x in b if x >= 0x80})
    r["recomputed_fh_checksum"] = fh_checksum(combo)
results.append({"step": "combine", "fixture": "fixture4 metadata + plain payload", **r})
results.append({"step": "verify-combined", **run([BH, "verify", str(combo)])})

# 3. copied-checksum scenario: fixture3's header (16 lines incl. its checksum
#    line) placed onto fixture4's byte layout.
f3 = split_lines((FIX / "fixture3-raw-utf8.gff3").read_bytes())
f4 = split_lines((FIX / "fixture4-escaped.gff3").read_bytes())
hdr3 = [l for l in f3 if l.startswith(b"#~")]
body4 = [l for l in f4 if not l.startswith(b"#~")]
mangled = OUT / "fixture4-with-copied-fixture3-header.gff3"
mangled.write_bytes(f4[0] + b"".join(hdr3) + b"".join(body4))
results.append({"step": "copy-header-setup", "fixture": mangled.name,
                "note": "fixture3 header incl. its #~checksum line copied onto fixture4 bytes",
                "sha256": hashlib.sha256(mangled.read_bytes()).hexdigest(),
                "copied_checksum_claim": hdr3[-1].decode().strip(),
                "recomputed_over_new_bytes": fh_checksum(mangled)})
results.append({"step": "verify-copied-header", **run([BH, "verify", str(mangled)])})

print(json.dumps(results, indent=2))
