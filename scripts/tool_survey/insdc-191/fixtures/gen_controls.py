#!/usr/bin/env python3
"""Write the two negative-control fixtures for the issue #191 survey.

Each control is a byte-for-byte copy of the corresponding valid FH* fixture
with ONE character changed inside the root checksum value. The replacement
character keeps the canonical padded-base64 form required by FORMAT.md R4/R5
(position 21 of a 32-byte SHA-512/256 digest in base64 is unconstrained), so
these are *stale-checksum* files, not syntactically broken ones. The schema is
untouched. `bioheaders verify` must reject both; the INSDC tools are expected
not to notice, which is the point of the control.

Run from fixtures/:  python3 gen_controls.py
"""

import base64
import hashlib
from pathlib import Path

here = Path(__file__).resolve().parent


def stale(value: str) -> str:
    i = 20
    replacement = "B" if value[i] != "B" else "C"
    out = value[:i] + replacement + value[i + 1 :]
    assert out != value, "control must differ from the valid fixture"
    assert len(out) == len(value) == 44 and out.endswith("=")
    return out


def write_control(src_name: str, dst_name: str, prefix: str, at_data_start) -> None:
    src, dst = here / src_name, here / dst_name
    lines = src.read_text().splitlines(keepends=True)
    mark = f"{prefix}checksum:"
    recorded = next(l for l in lines if l.startswith(mark)).split(":", 1)[1].strip()
    body = "".join(l for l in lines if not l.startswith(mark))
    recomputed = base64.b64encode(hashlib.new("sha512_256", body.encode()).digest()).decode()
    assert recorded == recomputed, f"{src_name} is not a valid fixture: {recorded} != {recomputed}"
    without = [l for l in lines if not l.startswith(mark)]
    first_data = next(i for i, l in enumerate(without) if at_data_start(l))
    dst.write_text(
        "".join(without[:first_data]) + f"{mark} {stale(recorded)}\n" + "".join(without[first_data:])
    )
    print(f"wrote {dst_name}: one character of the checksum value changed")


# FASTA: the header block ends at the first record line.
write_control("fhr_header.fsa", "fhr_corrupt.fsa", ";~", lambda l: l.startswith(">"))
# GFF3: the header block ends at the first line that is not a comment line, so
# the checksum stays inside the block and after ##gff-version 3.
write_control("fhgff3_header.gff", "fhgff3_corrupt.gff", "#~", lambda l: not l.startswith("#"))
