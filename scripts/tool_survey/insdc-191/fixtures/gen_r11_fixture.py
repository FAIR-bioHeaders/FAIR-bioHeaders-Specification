#!/usr/bin/env python3
"""Build the R11 negative-control fixture: a VALID FHR file whose header block
contains a raw '>' character in a value.

docs/FORMAT.md R11 warns that many FASTA readers start a record at the first
'>' or '@' anywhere in a line, so writers must escape those characters inside
quoted YAML scalars (\\x3E / \\x40). A file with a raw '>' stays valid but
validators warn.

This fixture isolates that single hazard: it is fixtures/fhr_header.fsa with
the `documentation` value replaced by one containing a raw '>', and the
`;~checksum:` line recomputed over the new bytes per FORMAT.md R3/R4 (SHA-
512/256 over every byte except the checksum line and its terminator, standard
padded base64). `bioheaders verify` therefore reports only the R11 warning, not
a checksum or schema failure.

Deterministic. Run from fixtures/:  python3 gen_r11_fixture.py
"""
import base64
import hashlib
from pathlib import Path

here = Path(__file__).resolve().parent
lines = (here / "fhr_header.fsa").read_text().splitlines(keepends=True)

out = []
skipping_continuation = False
for line in lines:
    if line.startswith(";~documentation:"):
        out.append(";~documentation: Synthetic R11 control value with a raw > character unquoted.\n")
        skipping_continuation = True
        continue
    if skipping_continuation:
        # drop the folded continuation lines of the old documentation value
        if line.startswith(";~ ") or line.startswith(";~\t"):
            continue
        skipping_continuation = False
    if line.startswith(";~checksum:"):
        continue
    out.append(line)

# FORMAT.md R3: every byte except the checksum line and its terminator is
# hashed, and the position of the checksum line within the header block does
# not matter. `out` is the file with the checksum line removed, so hashing it
# gives the checksum of the finished file.
value = base64.b64encode(
    hashlib.new("sha512_256", "".join(out).encode("utf-8")).digest()
).decode("ascii")

first_record = next(i for i, line in enumerate(out) if line.startswith(">"))
final = "".join(out[:first_record]) + f";~checksum: {value}\n" + "".join(out[first_record:])
(here / "fhr_r11_rawgt.fsa").write_bytes(final.encode("utf-8"))
print("wrote fixtures/fhr_r11_rawgt.fsa checksum", value)
