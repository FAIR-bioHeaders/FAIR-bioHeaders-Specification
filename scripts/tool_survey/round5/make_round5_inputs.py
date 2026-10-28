#!/usr/bin/env python3
"""Write the inputs of the round-5 survey (docs/TOOL_COMPATIBILITY.md, "More tools (round 5, 2026-10-28)").

Usage: make_round5_inputs.py CONTROL.fa PROTEINS.faa FHR.yaml OUTDIR [--bioheaders BIN]

CONTROL.fa is a plain genome FASTA (the survey used M. genitalium G37,
NC_000908.2) and PROTEINS.faa a plain protein FASTA predicted from it
(`pyrodigal -i CONTROL.fa -a PROTEINS.faa -g 4`). FHR.yaml is the genome
metadata (FAIR-bioHeaders-Tools examples/example.fhr.yaml). OUTDIR gets, for
each STEM in {genome, proteins, small, aln}:

  STEM.control.fa     the plain file
  STEM.fhr.fa         `bioheaders combine` with FHR (genome, aln) or FHP
                      (proteins, small) metadata: an R11-escaped `;~` header
  STEM.comment1.fa    the control with one leading `;comment` line
  STEM.hash.fa,       the FHR/FHP file with the leading lines marked `#~`, or
  STEM.text.fa        unmarked (make_marker_variants.py's conversion)
  STEM.raw.fa         (genome only) a raw `@` and `>` in one value, as a
                      pre-R11 writer would leave it
  STEM.{control,fhr}.fa.gz  gzip copies

small is the first 8 proteins (Clustal Omega, Exonerate queries); aln is a
6-taxon, 600-column DNA alignment derived from the genome with seeded
substitutions and gaps (RAxML-NG). The FHP metadata (fhp.yaml) is written
next to the files.
"""
import argparse
import gzip
import random
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "round4"))
from make_round4_inputs import leading, raw_markers  # noqa: E402

FHP = """schema: https://w3id.org/fair-bioheaders/fhp/v0.4.0
schemaVersion: '1.0'
proteome: Mycoplasmoides genitalium G37 proteins predicted with pyrodigal (survey input)
sourceType: predicted
taxon:
  name: Mycoplasmoides genitalium
  uri: https://identifiers.org/taxonomy:2097
version: '1.0'
metadataAuthor:
- name: FAIR-bioHeaders tool survey
dateCreated: '2026-10-28'
derivedFrom:
- headerType: FHR
  checksum: BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=
  relationship: translatedFrom
geneticCode: 4
predictionSoftware:
- name: pyrodigal
  version: 3.7.1
  uri: https://github.com/althonos/pyrodigal
documentation: Test input for the FAIR-bioHeaders tool-compatibility survey.
reuseConditions: public domain
"""


def records(path):
    recs, name, seq = [], None, []
    for line in Path(path).read_text().splitlines():
        if line.startswith(">"):
            if name is not None:
                recs.append((name, "".join(seq)))
            name, seq = line[1:], []
        elif name is not None:
            seq.append(line.strip())
    if name is not None:
        recs.append((name, "".join(seq)))
    return recs


def write_fasta(path, recs, width=60):
    with open(path, "w") as f:
        for name, seq in recs:
            f.write(f">{name}\n")
            for i in range(0, len(seq), width):
                f.write(seq[i:i + width] + "\n")


def alignment(genome_seq):
    rng = random.Random(5)
    base = list(genome_seq[10000:10600].upper())
    out = []
    for t in range(6):
        s = base[:]
        for _ in range(12 * (t + 1)):
            p = rng.randrange(len(s))
            s[p] = rng.choice("ACGT")
        if t % 2:
            g = rng.randrange(50, 550)
            s[g:g + 3] = "---"
        out.append((f"taxon{t + 1}", "".join(s)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("control")
    ap.add_argument("proteins")
    ap.add_argument("metadata")
    ap.add_argument("outdir")
    ap.add_argument("--bioheaders", default="bioheaders")
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=False)
    (out / "fhp.yaml").write_text(FHP)
    shutil.copy(a.control, out / "genome.control.fa")
    shutil.copy(a.proteins, out / "proteins.control.fa")
    write_fasta(out / "small.control.fa", records(a.proteins)[:8])
    write_fasta(out / "aln.control.fa", alignment(records(a.control)[0][1]))
    meta = {"genome": a.metadata, "aln": a.metadata, "proteins": out / "fhp.yaml", "small": out / "fhp.yaml"}
    for stem, md in meta.items():
        ctrl = out / f"{stem}.control.fa"
        fhr = out / f"{stem}.fhr.fa"
        subprocess.run([a.bioheaders, "combine", "-o", str(fhr), str(md), str(ctrl)], check=True)
        (out / f"{stem}.comment1.fa").write_bytes(b";comment\n" + ctrl.read_bytes())
        (out / f"{stem}.hash.fa").write_bytes(leading(fhr, "hash"))
        (out / f"{stem}.text.fa").write_bytes(leading(fhr, "text"))
        for n in ("control", "fhr"):
            data = (out / f"{stem}.{n}.fa").read_bytes()
            (out / f"{stem}.{n}.fa.gz").write_bytes(gzip.compress(data, mtime=0))
    (out / "genome.raw.fa").write_bytes(raw_markers((out / "genome.fhr.fa").read_bytes()))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
