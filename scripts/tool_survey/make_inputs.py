#!/usr/bin/env python3
"""Generate small, deterministic test inputs for the FHR tool-compatibility survey.

Usage: make_inputs.py OUTDIR [--fhr-bin DIR]

Writes control (header-free) and FHR-headed FASTA, GFA and GFF3 files.
FASTA/GFA headers are produced by the released converter (fhr-fasta-combine,
fhr-gfa-combine); GFF3 '#~' headers are hand-written (FHGFF3 is unreleased).
"""
import argparse
import gzip
import random
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent


def wrap(seq, width=60):
    return "\n".join(seq[i:i + width] for i in range(0, len(seq), width))


def rand_seq(rng, n, soft=False):
    s = "".join(rng.choice("ACGT") for _ in range(n))
    if soft:  # soft-masked stretch in the middle
        a, b = n // 3, n // 3 + 200
        s = s[:a] + s[a:b].lower() + s[b:]
    return s


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--fhr-bin", default="", help="directory holding fhr-* CLIs")
    a = ap.parse_args()
    out = Path(a.outdir)
    for sub in ("fasta", "gfa", "gff3", "reads"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    fhr = lambda name: str(Path(a.fhr_bin) / name) if a.fhr_bin else name
    meta = REPO / "examples" / "example.fhr.yaml"
    rng = random.Random(40)

    # ---------------- FASTA ----------------
    recs = [("chr1", rand_seq(rng, 5000, soft=True), "synthetic chromosome 1"),
            ("chr2", rand_seq(rng, 3000), "synthetic chromosome 2"),
            ("chrM", rand_seq(rng, 1200), "synthetic mitochondrion")]
    fa = out / "fasta"
    ctrl = fa / "control.fa"
    ctrl.write_text("".join(f">{n} {d}\n{wrap(s)}\n" for n, s, d in recs))
    run([fhr("fhr-fasta-combine"), "-o", str(fa / "fhr.fa"), str(meta), str(ctrl)])
    # Plain (non-BGZF) gzip of both
    for stem in ("control", "fhr"):
        with open(fa / f"{stem}.fa", "rb") as f, gzip.open(fa / f"{stem}.gzip.fa.gz", "wb") as g:
            shutil.copyfileobj(f, g)
    # BGZF: converter writes BGZF when the output name ends in .gz
    run([fhr("fhr-fasta-combine"), "-o", str(fa / "fhr.bgzf.fa.gz"), str(meta), str(ctrl)])
    run([fhr("fhr-fasta-strip"), str(fa / "fhr.bgzf.fa.gz"), str(fa / "control.bgzf.fa.gz")])
    # CRLF variants
    for stem in ("control", "fhr"):
        data = (fa / f"{stem}.fa").read_bytes().replace(b"\n", b"\r\n")
        (fa / f"{stem}.crlf.fa").write_bytes(data)
    # Unwrapped (two-line) variants for Biopython's fasta-2line parser
    (fa / "control.2line.fa").write_text("".join(f">{n} {d}\n{s}\n" for n, s, d in recs))
    run([fhr("fhr-fasta-combine"), "-o", str(fa / "fhr.2line.fa"), str(meta),
         str(fa / "control.2line.fa")])
    # Edge case: one leading legacy ';' comment line (all comment lines the
    # same width). Not a valid FHR file; probes parsers that treat leading
    # lines as an unnamed record.
    (fa / "edge.comment1.fa").write_text(";~checksum: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n"
                                         + ctrl.read_text())
    # Concatenation (invalid under R10): `cat genome.fhr.fa extra.fhr.fa`
    # puts the second header after the first file's last record.
    extra = fa / "extra.fa"
    extra.write_text(f">chrX extra contig\n{wrap(rand_seq(rng, 800))}\n")
    run([fhr("fhr-fasta-combine"), "-o", str(fa / "extra.fhr.fa"), str(meta), str(extra)])
    (fa / "concat.control.fa").write_text(ctrl.read_text() + extra.read_text())
    (fa / "concat.fhr.fa").write_text((fa / "fhr.fa").read_text() + (fa / "extra.fhr.fa").read_text())
    (fa / "concat.mixed.fa").write_text(ctrl.read_text() + (fa / "extra.fhr.fa").read_text())
    # Single-record variant
    one = fa / "control.single.fa"
    one.write_text(f">chrM\n{wrap(recs[2][1])}\n")
    run([fhr("fhr-fasta-combine"), "-o", str(fa / "fhr.single.fa"), str(meta), str(one)])

    # Protein FASTA (DIAMOND) and a DNA alignment (IQ-TREE). They use their own
    # generator so that every input above stays byte-identical.
    xrng = random.Random(41)
    aa = "ACDEFGHIKLMNPQRSTVWY"
    prots = [(f"prot{i}", "".join(xrng.choice(aa) for _ in range(n)))
             for i, n in ((1, 300), (2, 180), (3, 120))]
    (fa / "control.faa").write_text("".join(f">{n} synthetic protein\n{wrap(s)}\n" for n, s in prots))
    run([fhr("fhr-fasta-combine"), "-o", str(fa / "fhr.faa"), str(meta), str(fa / "control.faa")])
    base = list(rand_seq(xrng, 600).upper())
    taxa = []
    for i in range(1, 6):
        s = list(base)
        for _ in range(30 * i):
            s[xrng.randrange(len(s))] = xrng.choice("ACGT")
        g = xrng.randrange(0, 560)
        s[g:g + 6] = "-" * 6
        taxa.append((f"taxon{i}", "".join(s)))
    (fa / "control.aln.fa").write_text("".join(f">{n}\n{wrap(s)}\n" for n, s in taxa))
    run([fhr("fhr-fasta-combine"), "-o", str(fa / "fhr.aln.fa"), str(meta), str(fa / "control.aln.fa")])

    # reads (exact substrings of chr1/chr2) for mappers
    with open(out / "reads" / "reads.fq", "w") as fq:
        for i in range(20):
            n, s, _ = recs[i % 2]
            p = rng.randrange(0, len(s) - 150)
            r = s[p:p + 150].upper()
            fq.write(f"@r{i}_{n}_{p + 1}\n{r}\n+\n{'I' * 150}\n")

    # ---------------- GFA (GFA1) ----------------
    g = out / "gfa"
    segs = [("s1", rand_seq(rng, 400)), ("s2", rand_seq(rng, 250)),
            ("s3", rand_seq(rng, 300)), ("s4", rand_seq(rng, 500))]
    lines = ["H\tVN:Z:1.0"]
    lines += [f"S\t{n}\t{s}\tLN:i:{len(s)}" for n, s in segs]
    lines += ["L\ts1\t+\ts2\t+\t0M", "L\ts1\t+\ts3\t+\t0M",
              "L\ts2\t+\ts4\t+\t0M", "L\ts3\t+\ts4\t+\t0M",
              "P\tsample1#1#chr1\ts1+,s2+,s4+\t*", "P\tsample2#1#chr1\ts1+,s3+,s4+\t*"]
    (g / "control.gfa").write_text("\n".join(lines) + "\n")
    run([fhr("fhr-gfa-combine"), "-o", str(g / "fhr.gfa"), str(meta), str(g / "control.gfa")])
    # Numeric segment IDs (odgi requires integer names)
    num = "\n".join(lines) + "\n"
    for i in range(4, 0, -1):
        num = num.replace(f"s{i}", str(i))
    (g / "control.numeric.gfa").write_text(num)
    run([fhr("fhr-gfa-combine"), "-o", str(g / "fhr.numeric.gfa"), str(meta),
         str(g / "control.numeric.gfa")])

    # ---------------- GFF3 ----------------
    gd = out / "gff3"
    header = """\
#~schema: https://raw.githubusercontent.com/FAIR-bioHeaders/FHGFF3/main/fhgff3.json
#~schemaVersion: 0.1
#~annotation: Synthetic gene models for the FHR survey genome
#~version: 1.0.0
#~taxon:
#~  name: Homo sapiens
#~  uri: https://identifiers.org/taxonomy:9606
#~metadataAuthor:
#~- name: Adam Wright
#~  uri: https://orcid.org/0000-0002-5719-4024
#~dateCreated: '2026-10-08'
#~derivedFrom:
#~- relationship: annotates
#~  checksum: cnMUAe4I36RZKnFTSOz5hQVtPeu1nvf+0Gt9XE2NSMI=
#~  seqcol_id: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
#~annotationSoftware:
#~- name: BRAKER
#~  version: 3.0.8
#~  commandLineOption: ['--genome=genome.fa', '--species=survey; test']
#~soVersion: '2024-06-05'
#~vitalStats:
#~  geneCount: 3
#~  transcriptCount: 4
#~reuseConditions: public domain
#~checksum: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
"""
    sr = "##sequence-region chr1 1 5000\n##sequence-region chr2 1 3000\n"
    feats = [
        ("chr1", "gene", 101, 1900, "+", ".", "ID=gene1;Name=ABC1"),
        ("chr1", "mRNA", 101, 1900, "+", ".", "ID=tx1;Parent=gene1;Name=ABC1-201"),
        ("chr1", "exon", 101, 400, "+", ".", "ID=exon1;Parent=tx1"),
        ("chr1", "CDS", 151, 400, "+", "0", "ID=cds1;Parent=tx1"),
        ("chr1", "exon", 1001, 1900, "+", ".", "ID=exon2;Parent=tx1"),
        ("chr1", "CDS", 1001, 1800, "+", "2", "ID=cds1;Parent=tx1"),
        ("chr1", "mRNA", 101, 1900, "+", ".", "ID=tx2;Parent=gene1;Name=ABC1-202"),
        ("chr1", "exon", 101, 400, "+", ".", "ID=exon3;Parent=tx2"),
        ("chr1", "exon", 1501, 1900, "+", ".", "ID=exon4;Parent=tx2"),
        ("chr1", "CDS", 151, 400, "+", "0", "ID=cds2;Parent=tx2"),
        ("chr1", "CDS", 1501, 1800, "+", "2", "ID=cds2;Parent=tx2"),
        ("chr1", "gene", 2501, 3400, "-", ".", "ID=gene2;Name=XYZ2"),
        ("chr1", "mRNA", 2501, 3400, "-", ".", "ID=tx3;Parent=gene2"),
        ("chr1", "exon", 2501, 3400, "-", ".", "ID=exon5;Parent=tx3"),
        ("chr1", "CDS", 2601, 3300, "-", "0", "ID=cds3;Parent=tx3"),
        ("chr2", "gene", 201, 1200, "+", ".", "ID=gene3;Name=QRS3"),
        ("chr2", "mRNA", 201, 1200, "+", ".", "ID=tx4;Parent=gene3"),
        ("chr2", "exon", 201, 1200, "+", ".", "ID=exon6;Parent=tx4"),
        ("chr2", "CDS", 301, 1101, "+", "0", "ID=cds4;Parent=tx4"),
    ]
    body = "".join(f"{c}\tsurvey\t{t}\t{s}\t{e}\t.\t{st}\t{ph}\t{at}\n"
                   for c, t, s, e, st, ph, at in feats)
    fasta_sec = "##FASTA\n" + "".join(f">{n}\n{wrap(s)}\n" for n, s, _ in recs[:2])
    v = "##gff-version 3\n"
    files = {
        "control.gff3": v + sr + body,
        "fhr.gff3": v + header + sr + body,              # header, then sequence-region
        "fhr.sr-before.gff3": v + sr + header + body,     # sequence-region, then header
        "control.fasta.gff3": v + sr + body + fasta_sec,
        "fhr.fasta.gff3": v + header + sr + body + fasta_sec,
    }
    for name, text in files.items():
        (gd / name).write_text(text)
    # genome FASTA for gffread -g / AGAT
    shutil.copy(ctrl, gd / "genome.fa")
    print(f"inputs written to {out}")


if __name__ == "__main__":
    main()
