#!/usr/bin/env python3
"""Fixture generator for spec issue #210 validation evidence.

Builds four otherwise-identical GFF3 files (synthetic data only):
  1 fixture1-plain.gff3          plain GFF3, no FH header
  2 fixture2-ascii-header.gff3   FHGFF3 header, ASCII-only metadata
  3 fixture3-raw-utf8.gff3       FHGFF3 header, raw UTF-8 (U+00E9) in annotation
  4 fixture4-escaped.gff3        FHGFF3 header, same value as YAML \\u00E9 escape

and a shared companion FASTA. Checksum semantics follow FORMAT.md R1-R5
(origin/main @9db6606): the file is read as bytes; a line ends at LF, CRLF, or
a lone CR not followed by LF, terminator included; the single root-level
`#~checksum:` line and its terminator are excluded; every other byte is hashed
with SHA-512/256 and encoded as padded standard base64.
"""
import base64
import hashlib
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "fixtures"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- payload ---
# Shared plain-GFF3 payload (byte-identical body for all four fixtures;
# fixture 1 is exactly this file).
PAYLOAD = (
    "##gff-version 3\n"
    "#!genome-build Synthetic SyntheticAssembly1\n"
    "##sequence-region ctg1 1 48\n"
    "# ordinary ASCII comment: this line must survive downstream tools\n"
    "ctg1\tsynthetic\tgene\t1\t48\t.\t+\t.\tID=gene1;Name=synthetic_gene_1\n"
    "ctg1\tsynthetic\tmRNA\t1\t48\t.\t+\t.\tID=rna1;Parent=gene1\n"
    "ctg1\tsynthetic\texon\t1\t24\t.\t+\t.\tID=exon1;Parent=rna1\n"
    "ctg1\tsynthetic\texon\t25\t48\t.\t+\t.\tID=exon2;Parent=rna1\n"
    "ctg1\tsynthetic\tCDS\t1\t48\t.\t+\t0\tID=cds1;Parent=rna1\n"
    "##FASTA\n"
    ">ctg1 synthetic companion sequence\n"
    "ACGTACGTACGTACGTACGTACGT\n"
    "TGCATGCATGCATGCATGCATGCATG\n"
)

COMPANION_FASTA = (
    ">ctg1 synthetic companion sequence\n"
    "ACGTACGTACGTACGTACGTACGT\n"
    "TGCATGCATGCATGCATGCATGCATG\n"
)

# ------------------------------------------------------------- metadata ----
# Base FHGFF3 metadata (schemaVersion 1.1 / contract v0.5.0). Genome link is
# the asserted accession+SeqCol form; every identifier is synthetic
# (GCA_900000015.1 is the reserved INSDC test accession; the SeqCol digest is
# the all-'S' placeholder used by the spec's own examples).
def metadata_yaml(annotation_value_line: str) -> str:
    return (
        "schema: https://w3id.org/fair-bioheaders/fhgff3/v0.5.0\n"
        "schemaVersion: '1.1'\n"
        f"{annotation_value_line}\n"
        "taxon:\n"
        "  name: Syntheticus testis\n"
        "  uri: https://identifiers.org/taxonomy:991300001\n"
        "version: '1.0'\n"
        "metadataAuthor:\n"
        "  - name: Synthetic Test Curator\n"
        "    nameType: Personal\n"
        "dateCreated: '2026-11-10'\n"
        "genomeReference:\n"
        "  accession: GCA_900000015.1\n"
        "  seqcol_id: SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS\n"
        "  assemblyName: SyntheticAssembly1\n"
    )

ASCII_ANNOT = "annotation: Synthetic annotation"
RAW_ANNOT = 'annotation: "Caf\u00e9 annotation"'          # raw U+00E9
ESC_ANNOT = 'annotation: "Caf\\u00E9 annotation"'         # literal backslash-u


# --------------------------------------------------------- checksum logic ---
def split_lines(data: bytes) -> list:
    """R1: a line ends at LF, CRLF, or lone CR; terminator belongs to line."""
    lines, i, n = [], 0, len(data)
    while i < n:
        j = i
        while j < n and data[j] not in (0x0A, 0x0D):
            j += 1
        if j >= n:
            lines.append(data[i:j])
            break
        if data[j] == 0x0A:
            lines.append(data[i:j + 1])
            i = j + 1
        else:  # CR
            if j + 1 < n and data[j + 1] == 0x0A:
                lines.append(data[i:j + 2])
                i = j + 2
            else:
                lines.append(data[i:j + 1])
                i = j + 1
    return lines


CHECKSUM_LINE = re.compile(rb"^[ \t]*#~checksum:")


def fh_checksum(path: pathlib.Path) -> str:
    """R2-R4: exclude the single root-level checksum line, SHA-512/256 the rest."""
    data = path.read_bytes()
    lines = split_lines(data)
    hits = [ln for ln in lines if CHECKSUM_LINE.match(ln) and not ln.startswith(b"#~#")]
    # root-level only: '#~checksum:' at column 0 (our headers have no indent);
    # '#~# more fields' style lines never match the regex anyway.
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one checksum line, found {len(hits)}")
    rest = b"".join(ln for ln in lines if ln is not hits[0])
    return base64.b64encode(hashlib.new("sha512_256", rest).digest()).decode()


def header_block(metadata: str, checksum: str) -> bytes:
    lines = ["#~" + ln for ln in metadata.splitlines()]
    lines.append("#~checksum: " + checksum)
    return ("\n".join(lines) + "\n").encode("utf-8")


def build(name: str, annotation_line) -> pathlib.Path:
    payload = PAYLOAD.encode("utf-8")
    if annotation_line is None:
        path = OUT / name
        path.write_bytes(payload)
        return path
    meta = metadata_yaml(annotation_line)
    # insert header after line 1 (##gff-version 3), checksum computed over
    # payload + header-minus-checksum-line, then appended (writers put it last)
    first, _, rest = payload.partition(b"\n")
    candidate = first + b"\n" + ("\n".join("#~" + l for l in meta.splitlines())).encode() + b"\n" + rest
    csum = fh_checksum_bytes(candidate)
    full = (
        first + b"\n"
        + ("\n".join("#~" + l for l in meta.splitlines())).encode()
        + b"\n#~checksum: " + csum.encode() + b"\n"
        + rest
    )
    path = OUT / name
    path.write_bytes(full)
    return path


def fh_checksum_bytes(data: bytes) -> str:
    lines = split_lines(data)
    return base64.b64encode(hashlib.new("sha512_256", b"".join(lines)).digest()).decode()


if __name__ == "__main__":
    (OUT / "companion.fasta").write_text(COMPANION_FASTA)
    (OUT / "payload.gff3").write_text(PAYLOAD)
    build("fixture1-plain.gff3", None)
    build("fixture2-ascii-header.gff3", ASCII_ANNOT)
    build("fixture3-raw-utf8.gff3", RAW_ANNOT)
    build("fixture4-escaped.gff3", ESC_ANNOT)
    for p in sorted(OUT.glob("fixture*.gff3")):
        print(p.name, "sha256=", hashlib.sha256(p.read_bytes()).hexdigest(),
              "fh=", fh_checksum(p) if b"#~checksum:" in p.read_bytes() else "-")
