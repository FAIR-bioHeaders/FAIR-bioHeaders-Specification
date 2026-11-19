#!/usr/bin/env python3
"""Independently re-derive the FAIR-bioHeaders checksum of a FASTA header file.

Standard library only, and deliberately not a wrapper around the toolkit: this
reimplements the coverage rule in the shared specification's docs/FORMAT.md
(R1-R5) — SHA-512/256 over every byte of the file except the single root-level
``;~checksum:`` line and its terminator, encoded as canonical padded base64.
It exists so that a recorded checksum can be checked without trusting the
program that wrote it, which is the only way to tell a real parent link from a
value copied out of the header.

Usage:

    python3 rederive_checksum.py FILE [FILE ...]          # compare with stated
    python3 rederive_checksum.py --self-test FILE         # tamper control too

Exit status is 0 when every recomputed value equals the stated one (and, with
``--self-test``, when a single tampered base changes the value).
"""

import argparse
import base64
import hashlib
import re
import sys

PREFIX = b";~"
CHECKSUM_LINE = re.compile(rb"^;~([ \t]*)checksum[ \t]*:")


def checksum_line_index(lines):
    """Index of the single root-indent checksum line, before the first record."""
    hits = []
    root_indent = None
    for position, line in enumerate(lines):
        if not line.startswith(PREFIX):
            if line.startswith(b">"):
                break
            continue
        body = line[len(PREFIX) :]
        indent = len(body) - len(body.lstrip(b" \t"))
        if root_indent is None or indent < root_indent:
            root_indent = indent
        match = CHECKSUM_LINE.match(line)
        if match and len(match.group(1)) == root_indent:
            hits.append(position)
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one root checksum line, found {len(hits)}")
    return hits[0]


def recompute(path):
    """Return (recomputed, stated, covered_bytes, total_bytes)."""
    with open(path, "rb") as handle:
        data = handle.read()
    lines = data.splitlines(keepends=True)
    index = checksum_line_index(lines)
    start = sum(len(line) for line in lines[:index])
    covered = data[:start] + data[start + len(lines[index]) :]
    digest = hashlib.new("sha512_256", covered)
    stated = lines[index].split(b":", 1)[1].strip().strip(b"'\"").decode()
    return base64.b64encode(digest.digest()).decode("ascii"), stated, len(covered), len(data)


def tampered_value(path, index_of_record=0):
    """Recompute over a copy with one sequence base changed; expect a new value."""
    with open(path, "rb") as handle:
        data = handle.read()
    lines = data.splitlines(keepends=True)
    position = next(
        i for i, line in enumerate(lines) if not line.startswith((b";~", b">"))
    )
    line = lines[position]
    original = line[:1]
    replacement = b"C" if original not in (b"C", b"c") else b"G"
    lines[position] = replacement + line[1:]
    mutated = b"".join(lines)
    start = sum(len(entry) for entry in lines[: checksum_line_index(lines)])
    covered = mutated[:start] + mutated[start + len(lines[checksum_line_index(lines)]) :]
    return (
        base64.b64encode(hashlib.new("sha512_256", covered).digest()).decode("ascii"),
        original.decode(),
        replacement.decode(),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="also check that tampering with one base changes the digest",
    )
    args = parser.parse_args(argv)
    failures = 0
    for path in args.files:
        recomputed, stated, covered, total = recompute(path)
        ok = recomputed == stated
        failures += 0 if ok else 1
        print(path)
        print(f"  file bytes        {total}")
        print(f"  covered bytes     {covered}  (file minus the checksum line and its terminator)")
        print(f"  recomputed        {recomputed}")
        print(f"  stated in header  {stated}")
        print(f"  matches           {'yes' if ok else 'NO'}")
        if args.self_test:
            mutated, old, new = tampered_value(path)
            caught = mutated != stated
            failures += 0 if caught else 1
            print(f"  tamper control    first sequence base {old!r} -> {new!r} gives "
                  f"{mutated}; detected={'yes' if caught else 'NO'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
