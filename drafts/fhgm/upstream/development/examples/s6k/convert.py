"""Reproduce the S6k pilot feature payload from the reviewed CaltechDATA ZIP."""

import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

ARCHIVE_SHA256 = "2328ee717b9124119f03503694fe8c080778e5d04bede36bbeae11b4a84d974c"
MEMBER = "DanaCAF1_S6k/DanaCAF1_S6k.gff"


def convert(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("Expected the reviewed DanaCAF1_S6k.zip archive")
    with ZipFile(path) as archive:
        source = archive.read(MEMBER).decode("ascii")

    transcripts = defaultdict(list)
    for line in source.splitlines():
        if not line or line.startswith("track "):
            continue
        *columns, attributes = line.split("\t")
        match = re.fullmatch(r'gene_id "([^"]+)"; transcript_id "([^"]+)";', attributes)
        if not match:
            raise ValueError(f"Unexpected source attributes: {attributes}")
        gene, transcript = match.groups()
        transcripts[gene, transcript].append(columns)

    def parent_row(rows, feature_type, attributes):
        seqid, source, _, _, _, _, strand, _ = rows[0]
        start = min(int(row[3]) for row in rows)
        end = max(int(row[4]) for row in rows)
        return "\t".join(
            [seqid, source, feature_type, str(start), str(end), ".", strand, ".", attributes]
        )

    gene = next(iter(transcripts))[0]
    yield "##gff-version 3"
    yield parent_row(
        [row for rows in transcripts.values() for row in rows], "gene", f"ID={gene}"
    )
    for (_, transcript), rows in sorted(transcripts.items()):
        yield parent_row(rows, "mRNA", f"ID={transcript};Parent={gene}")
        for row in rows:
            yield "\t".join([*row, f"Parent={transcript}"])


if __name__ == "__main__":
    sys.stdout.write("\n".join(convert(Path(sys.argv[1]))) + "\n")
