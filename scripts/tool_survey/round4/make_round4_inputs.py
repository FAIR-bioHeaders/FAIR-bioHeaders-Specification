#!/usr/bin/env python3
"""Write the inputs of the 2026-10-22 survey (docs/TOOL_COMPATIBILITY.md, "More tools (2026-10-22)").

Usage: make_round4_inputs.py CONTROL.fa METADATA.fhr.yaml OUTDIR [--bioheaders BIN]

CONTROL.fa is a plain FASTA file (the survey used M. genitalium G37,
NC_000908.2). OUTDIR gets:

  control.fa        the control, unchanged
  fhr.fa            `bioheaders combine METADATA CONTROL` (R11-escaped `;~` header)
  comment1.fa       the control with one leading `;comment` line
  hash.fa, text.fa  fhr.fa with the leading lines marked `#~`, or unmarked
                    (make_marker_variants.py's conversion)
  raw.fa            fhr.fa with a raw `@` and `>` in one value, as a pre-R11 writer
                    would leave it (checksum not updated)
  *.fa.gz           gzip copies of control.fa and fhr.fa
  *.bgzf.fa.gz      BGZF copies (needs bgzip on PATH)
  reads.fq          50 exact 150 bp reads from the control (seed 1)
  vep/              a one-gene GFF3 (bgzip + tabix) and a 5-variant VCF on the
                    first CDS of the control (NC_000908.2 686..1828, dnaN)
  kraken-taxonomy/  a minimal NCBI taxonomy mapping the first record to taxid 2097
"""
import argparse
import gzip
import random
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from make_marker_variants import convert


def leading(path, variant):
    out, before = [], True
    for line in path.read_bytes().splitlines(keepends=True):
        if line.startswith(b">"):
            before = False
        out.append(convert(line, variant) if before and line.startswith(b";") else line)
    return b"".join(out)


def raw_markers(data):
    out, skip = [], False
    for line in data.splitlines(keepends=True):
        if line.startswith(b";~documentation:"):
            out.append(b";~documentation: contact someone@example.org; contigs > 1000 bp\n")
            skip = True
            continue
        if skip and line.startswith(b";~  "):
            continue
        skip = False
        out.append(line)
    return b"".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("control")
    ap.add_argument("metadata")
    ap.add_argument("outdir")
    ap.add_argument("--bioheaders", default="bioheaders")
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=False)
    ctrl = out / "control.fa"
    shutil.copy(a.control, ctrl)
    subprocess.run([a.bioheaders, "combine", "-o", str(out / "fhr.fa"), a.metadata, str(ctrl)], check=True)
    (out / "comment1.fa").write_bytes(b";comment\n" + ctrl.read_bytes())
    (out / "hash.fa").write_bytes(leading(out / "fhr.fa", "hash"))
    (out / "text.fa").write_bytes(leading(out / "fhr.fa", "text"))
    (out / "raw.fa").write_bytes(raw_markers((out / "fhr.fa").read_bytes()))
    for n in ("control", "fhr"):
        data = (out / f"{n}.fa").read_bytes()
        (out / f"{n}.fa.gz").write_bytes(gzip.compress(data, mtime=0))
        with open(out / f"{n}.bgzf.fa.gz", "wb") as f:
            subprocess.run(["bgzip", "-c", str(out / f"{n}.fa")], stdout=f, check=True)

    lines = ctrl.read_text().splitlines()
    name = lines[0][1:].split()[0]
    seq = "".join(x.strip() for x in lines[1:] if not x.startswith(">"))  # first record only if one record
    rng = random.Random(1)
    with open(out / "reads.fq", "w") as q:
        for i in range(50):
            p = rng.randrange(0, len(seq) - 150)
            q.write(f"@r{i}_{p}\n{seq[p:p + 150]}\n+\n{'I' * 150}\n")

    vep = out / "vep"
    vep.mkdir()
    gff = [
        "##gff-version 3",
        f"{name}\tRefSeq\tgene\t686\t1828\t.\t+\t.\tID=gene-MG_001;Name=dnaN;biotype=protein_coding",
        f"{name}\tRefSeq\tmRNA\t686\t1828\t.\t+\t.\tID=rna-MG_001;Parent=gene-MG_001;biotype=protein_coding",
        f"{name}\tRefSeq\texon\t686\t1828\t.\t+\t.\tID=exon-MG_001;Parent=rna-MG_001",
        f"{name}\tRefSeq\tCDS\t686\t1828\t.\t+\t0\tID=cds-MG_001;Parent=rna-MG_001",
    ]
    (vep / "genes.gff").write_text("\n".join(gff) + "\n")
    subprocess.run(["bgzip", "-f", str(vep / "genes.gff")], check=True)
    subprocess.run(["tabix", "-p", "gff", str(vep / "genes.gff.gz")], check=True)
    swap = {"A": "G", "G": "A", "C": "T", "T": "C"}
    vcf = ["##fileformat=VCFv4.2", f"##contig=<ID={name},length={len(seq)}>",
           "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"]
    for i, p in enumerate((700, 701, 1000, 1500, 1826)):
        r = seq[p - 1].upper()
        vcf.append(f"{name}\t{p}\tv{i}\t{r}\t{swap[r]}\t.\tPASS\t.")
    (vep / "test.vcf").write_text("\n".join(vcf) + "\n")

    tax = out / "kraken-taxonomy"
    tax.mkdir()
    nodes = [(1, 1, "no rank"), (131567, 1, "no rank"), (2, 131567, "superkingdom"), (2097, 2, "species")]
    names = [(1, "root"), (131567, "cellular organisms"), (2, "Bacteria"), (2097, "Mycoplasmoides genitalium")]
    (tax / "nodes.dmp").write_text("".join(f"{t}\t|\t{p}\t|\t{r}\t|\t\t|\n" for t, p, r in nodes))
    (tax / "names.dmp").write_text("".join(f"{t}\t|\t{n}\t|\t\t|\tscientific name\t|\n" for t, n in names))
    acc = name.split(".")[0]
    (tax / "nucl_gb.accession2taxid").write_text(f"accession\taccession.version\ttaxid\tgi\n{acc}\t{name}\t2097\t0\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
