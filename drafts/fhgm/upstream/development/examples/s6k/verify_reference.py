"""Check the S6k model against the exact NCBI assembly used by this fixture."""

import base64
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from gff3_validator.codons import CODONS, TABLES

from convert import convert

ASSEMBLY_SHA256 = "04ef43ac3ec64d444a052aaae4de51955bb928a9f1e731846a781bdaeadf3090"


def fasta(lines):
    name = None
    chunks = []
    for line in lines:
        if line.startswith(">"):
            if name is not None:
                yield name, "".join(chunks).upper()
            name = line[1:].split()[0]
            chunks = []
        else:
            chunks.append(line.strip())
    if name is not None:
        yield name, "".join(chunks).upper()


def digest(data):
    return base64.urlsafe_b64encode(hashlib.sha512(data).digest()[:24]).decode("ascii")


def canonical(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("ascii")


def verify(archive_path, assembly_path):
    with assembly_path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != ASSEMBLY_SHA256:
            raise ValueError("Expected the pinned NCBI assembly archive")

    collection = {"names": [], "sequences": []}
    scaffold = None
    with gzip.open(assembly_path, "rt", encoding="ascii") as stream:
        for name, sequence in fasta(stream):
            collection["names"].append(name)
            collection["sequences"].append("SQ." + digest(sequence.encode("ascii")))
            if name == "CH902618.1":
                scaffold = sequence
    if scaffold is None:
        raise ValueError("CH902618.1 missing from the assembly")

    features = defaultdict(lambda: defaultdict(list))
    for row in list(convert(archive_path))[1:]:
        seqid, _, kind, start, end, _, strand, _, attributes = row.split("\t")
        if kind in {"exon", "CDS", "stop_codon"}:
            if seqid != "scaffold_13337" or strand != "+":
                raise ValueError("Unexpected scaffold or strand")
            features[attributes.removeprefix("Parent=")][kind].append((int(start), int(end)))

    with ZipFile(archive_path) as archive:
        stem = "DanaCAF1_S6k/DanaCAF1_S6k"
        transcripts = dict(fasta(archive.read(stem + ".fasta").decode("ascii").splitlines()))
        peptides = dict(fasta(archive.read(stem + ".pep").decode("ascii").splitlines()))

    code = dict(zip(CODONS, TABLES[1][1], strict=True))
    for name, rows in features.items():
        exon, cds, stop = (
            "".join(scaffold[start - 1:end] for start, end in sorted(rows[kind]))
            for kind in ("exon", "CDS", "stop_codon")
        )
        peptide = "".join(code[cds[index:index + 3]] for index in range(0, len(cds), 3))
        if exon != transcripts[name + "_transcript"]:
            raise ValueError(f"{name}: transcript mismatch")
        if peptide != peptides[name + "_peptide"].removesuffix("*") or code.get(stop) != "*":
            raise ValueError(f"{name}: peptide or stop codon mismatch")
        print(f"{name}: {len(exon)} nt, {len(peptide)} aa, terminal {stop}")

    level_one = {name: digest(canonical(values)) for name, values in collection.items()}
    print(f"SeqCol ({len(collection['names'])} sequences): {digest(canonical(level_one))}")


if __name__ == "__main__":
    verify(Path(sys.argv[1]), Path(sys.argv[2]))
