#!/usr/bin/env python3
"""Write FILE.fai for an uncompressed FASTA, skipping lines before the first `>`.

Usage: header_fai.py FILE [OUT]

The index has the samtools layout (name, length, offset, line bases, line
bytes) with offsets into FILE, so it is what a header-aware indexer writes;
for the survey file it is byte-identical to pyfaidx 0.9.1's .fai. For a BGZF
file, run it on the uncompressed copy and pass OUT=FILE.gz.fai (offsets in a
.fai are uncompressed offsets).
"""
import sys

path = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else path + ".fai"
recs, rec, off = [], None, 0
with open(path, "rb") as f:
    for line in f:
        body = line.rstrip(b"\r\n")
        if body.startswith(b">"):
            if rec:
                recs.append(rec)
            rec = [body[1:].split()[0].decode(), 0, off + len(line), 0, 0]
        elif rec is not None and body:
            if rec[3] == 0:
                rec[3], rec[4] = len(body), len(line)
            rec[1] += len(body)
        off += len(line)
if rec:
    recs.append(rec)
with open(out, "w") as f:
    f.writelines("\t".join(map(str, r)) + "\n" for r in recs)
