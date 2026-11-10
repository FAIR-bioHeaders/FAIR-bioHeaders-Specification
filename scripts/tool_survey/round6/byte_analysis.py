#!/usr/bin/env python3
"""Precise byte-level analysis of the four fixtures."""
import pathlib
import sys

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"

def lines_with_terminators(data: bytes):
    out, i, n = [], 0, len(data)
    while i < n:
        j = i
        while j < n and data[j] not in (0x0A, 0x0D):
            j += 1
        if j >= n:
            out.append((i, data[i:j])); break
        if data[j] == 0x0A:
            out.append((i, data[i:j+1])); i = j + 1
        elif j + 1 < n and data[j+1] == 0x0A:
            out.append((i, data[i:j+2])); i = j + 2
        else:
            out.append((i, data[i:j+1])); i = j + 1
    return out

names = ["fixture1-plain.gff3", "fixture2-ascii-header.gff3",
         "fixture3-raw-utf8.gff3", "fixture4-escaped.gff3"]
blobs = {n: (FIX / n).read_bytes() for n in names}

print("== sizes ==")
for n in names:
    print(f"{n}: {len(blobs[n])} bytes")

print("\n== non-ASCII byte scan (any byte >= 0x80) ==")
for n in names:
    hits = [(off, b) for off, b in enumerate(blobs[n]) if b >= 0x80]
    if hits:
        for off, b in hits:
            ln = next(i for i, (s, l) in enumerate(lines_with_terminators(blobs[n])) if s <= off < s + len(l))
            print(f"{n}: byte 0x{b:02X} at file offset {off} (line {ln + 1})")
    else:
        print(f"{n}: none (pure ASCII)")

print("\n== line-level comparison: bodies after the header block ==")
# header block = lines 1..17 for fixtures 2-4 ('#~checksum' is line 17);
# fixture 1 has no '#~' lines. Compare everything after the FH header lines.
def body(n):
    ls = lines_with_terminators(blobs[n])
    keep = [l for (s, l) in ls if not l.startswith(b"#~")]
    return b"".join(keep)
b1 = body(names[0])
for n in names[1:]:
    print(f"{n}: body-identical-to-fixture1 = {body(n) == b1}")

print("\n== directive/feature-line identity across all four fixtures ==")
def structural(n):
    return [l for (s, l) in lines_with_terminators(blobs[n])
            if (l.startswith(b"##") or l.startswith(b"#!")) and not l.startswith(b"#~")
            or (l and not l.startswith((b"#",))) and b"\t" in l]
ref = structural(names[0])
for n in names:
    print(f"{n}: {len(structural(n))} directive/feature lines, identical to fixture1 = {structural(n) == ref}")

print("\n== ordinary ASCII comment line present in each ==")
for n in names:
    hit = [l.decode() .rstrip() for (s, l) in lines_with_terminators(blobs[n])
           if l.startswith(b"# ") ]
    print(f"{n}: {hit}")

print("\n== '#~' header lines in fixtures 2-4 (line numbers) ==")
for n in names[1:]:
    for i, (s, l) in enumerate(lines_with_terminators(blobs[n]), 1):
        if l.startswith(b"#~"):
            txt = l.rstrip(b"\n")
            marker = ""
            if any(b >= 0x80 for b in txt):
                marker = "   <-- non-ASCII bytes: " + " ".join(f"{b:02X}" for b in txt if b >= 0x80)
            print(f"{n} L{i:2d}: {txt!r}{marker}")
