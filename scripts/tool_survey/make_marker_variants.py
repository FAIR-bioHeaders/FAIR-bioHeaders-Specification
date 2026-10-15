#!/usr/bin/env python3
"""Make comment-marker variants of the survey inputs.

Usage: make_marker_variants.py INPUTS

INPUTS is a directory written by make_inputs.py. This writes INPUTS-hash and
INPUTS-text next to it: copies in which the leading `;` lines of
fasta/fhr.fa (the lines before the first `>`) start with `#` instead, or
have no marker (`;~key: value` becomes `key: value`). Every other byte is
unchanged. Run run_survey.py on each directory and compare the FASTA rows
for `control.fa vs fhr.fa` (docs/TOOL_COMPATIBILITY.md, "Comment markers").
"""
import shutil
import sys
from pathlib import Path


def convert(line, variant):
    if variant == "hash":
        return b"#" + line[1:]
    return line[2:] if line.startswith(b";~") else line[1:]


def main():
    inputs = Path(sys.argv[1]).resolve()
    for variant in ("hash", "text"):
        target = inputs.with_name(f"{inputs.name}-{variant}")
        if target.exists():
            sys.exit(f"{target} exists; remove it first")
        shutil.copytree(inputs, target)
        path = target / "fasta" / "fhr.fa"
        out, before = [], True
        for line in path.read_bytes().splitlines(keepends=True):
            if line.startswith(b">"):
                before = False
            out.append(convert(line, variant) if before and line.startswith(b";") else line)
        path.write_bytes(b"".join(out))
        print(f"wrote {target}")


if __name__ == "__main__":
    main()
