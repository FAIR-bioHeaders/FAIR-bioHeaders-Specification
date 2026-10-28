#!/usr/bin/env python3
"""Run the round-5 survey (docs/TOOL_COMPATIBILITY.md, "More tools (round 5, 2026-10-28)").

Usage: run_round5.py INPUTS OUTDIR [--only NAME,...]

INPUTS is a directory written by make_round5_inputs.py. Each test runs on the
control and on each variant in a fresh directory, fingerprints the output and
classifies it as run_round4.py does (a, b?, c, c(rc0), n/a). Rows go to
OUTDIR/results-round5.tsv (rows of tools that are rerun are replaced, so the
environments can be run one at a time) and differing fingerprints to OUTDIR/diff/.

The tools live in separate environments (environment-round5.yml); point to
their bin directories with R5GENE, R5BARRNAP09, R5CLUST, R5ALIGN and R5EMAPPER (eggNOG-mapper is run with a DIAMOND or MMseqs2
database of the plain proteins instead of the eggNOG databases), and
R5CHECKM2SRC to a directory holding CheckM2 1.1.0's checkm2/sequenceClasses.py
and checkm2/version.py (no CheckM2 database is used).
"""
import argparse
import difflib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pairs(stem, gz=True, raw=False):
    p = [("semicolon", f"{stem}.control.fa", f"{stem}.fhr.fa"),
         ("semicolon-1line", f"{stem}.control.fa", f"{stem}.comment1.fa"),
         ("hash", f"{stem}.control.fa", f"{stem}.hash.fa"),
         ("unmarked", f"{stem}.control.fa", f"{stem}.text.fa")]
    if raw:
        p.append(("semicolon-raw-markers", f"{stem}.control.fa", f"{stem}.raw.fa"))
    if gz:
        p.append(("semicolon-gzip", f"{stem}.control.fa.gz", f"{stem}.fhr.fa.gz"))
    return p


G, P, S, A = pairs("genome", raw=True), pairs("proteins"), pairs("small"), pairs("aln", gz=False)
CONDA_VER = "echo {0} $(ls $%s/../conda-meta | sed -n 's/^{0}-\\([0-9][0-9a-z.]*\\)-.*/\\1/p' | head -1)"


def ver(env, pkg):
    return CONDA_VER.replace("%s", env).format(pkg)


GFFCUT = "grep -v '^#' {0} | cut -f1,3-5,7 | sort"
TESTS = [
    # survey5-gene
    dict(tool="Prodigal", ver=ver("R5GENE", "prodigal"),
         cmd="$R5GENE/prodigal -i $IN -g 4 -a p.faa -f gff -o g.gff > log.txt 2>&1",
         fp=f"$FP fasta p.faa; {GFFCUT.format('g.gff')}", pairs=G),
    dict(tool="pyrodigal CLI", ver=ver("R5GENE", "pyrodigal"),
         cmd="$R5GENE/pyrodigal -i $IN -g 4 -a p.faa -f gff -o g.gff > log.txt 2>&1",
         fp=f"$FP fasta p.faa; {GFFCUT.format('g.gff')}", pairs=G),
    dict(tool="pyrodigal API (GeneFinder; pyrodigal's bundled FASTA reader)", ver=ver("R5GENE", "pyrodigal"),
         cmd="$R5GENE/python -I $HERE/pyrodigal_api.py bundled $IN > genes.txt 2> log.txt",
         fp="cat genes.txt", pairs=G),
    dict(tool="pyrodigal API (GeneFinder; Biopython SeqIO fasta, as in the README)",
         ver="echo pyrodigal $($R5GENE/python -I -c 'import pyrodigal;print(pyrodigal.__version__)'), "
             "Biopython $($R5GENE/python -I -c 'import Bio;print(Bio.__version__)')",
         cmd="$R5GENE/python -I $HERE/pyrodigal_api.py biopython $IN > genes.txt 2> log.txt",
         fp="cat genes.txt", pairs=G),
    dict(tool="Barrnap", ver=ver("R5GENE", "barrnap"),
         cmd="PATH=$R5GENE:$PATH barrnap --kingdom bac --threads 1 $IN > r.gff 2> log.txt",
         fp=GFFCUT.format("r.gff"), pairs=G),
    dict(tool="Barrnap 0.9 (nhmmer; the version Prokka 1.15 uses)", ver=ver("R5BARRNAP09", "barrnap"),
         cmd="PATH=$R5BARRNAP09:$PATH barrnap --kingdom bac --threads 1 $IN > r.gff 2> log.txt",
         fp=GFFCUT.format("r.gff"), pairs=G),
    dict(tool="tRNAscan-SE", ver=ver("R5GENE", "trnascan-se"),
         cmd="PATH=$R5GENE:$PATH tRNAscan-SE -B -q --thread 1 -o t.txt $IN > log.txt 2>&1",
         fp="tail -n +4 t.txt | cut -f1,3-6 | sed 's/ *\\t */\\t/g'", pairs=G),
    # survey5-clust
    dict(tool="MMseqs2 createdb + convert2fasta (genome)", ver=ver("R5CLUST", "mmseqs2"),
         cmd="$R5CLUST/mmseqs createdb $IN db > log.txt 2>&1 && $R5CLUST/mmseqs convert2fasta db out.fa >> log.txt 2>&1",
         fp="$FP fasta out.fa", pairs=G),
    dict(tool="MMseqs2 createdb + convert2fasta (proteins)", ver=ver("R5CLUST", "mmseqs2"),
         cmd="$R5CLUST/mmseqs createdb $IN db > log.txt 2>&1 && $R5CLUST/mmseqs convert2fasta db out.fa >> log.txt 2>&1",
         fp="$FP fasta out.fa", pairs=P),
    dict(tool="MMseqs2 easy-cluster (proteins)", ver=ver("R5CLUST", "mmseqs2"),
         cmd="$R5CLUST/mmseqs easy-cluster $IN clu tmp --threads 1 -v 1 > log.txt 2>&1",
         fp="sort clu_cluster.tsv; $FP fasta clu_rep_seq.fasta", pairs=P),
    dict(tool="MMseqs2 easy-search (8 proteins as query)", ver=ver("R5CLUST", "mmseqs2"),
         cmd="$R5CLUST/mmseqs easy-search $IN $PROT hits.m8 tmp --threads 1 -v 1 > log.txt 2>&1",
         fp="sort hits.m8", pairs=S),
    dict(tool="CD-HIT cd-hit (proteins)", ver=ver("R5CLUST", "cd-hit"),
         cmd="$R5CLUST/cd-hit -i $IN -o out.fa -c 0.9 -T 1 -M 2000 > log.txt 2>&1",
         fp="$FP fasta out.fa; grep -v '^>Cluster' out.fa.clstr | sed 's/^[0-9]*\\t//' | sort", pairs=P),
    dict(tool="CD-HIT cd-hit-est (genome)", ver=ver("R5CLUST", "cd-hit"),
         cmd="$R5CLUST/cd-hit-est -i $IN -o out.fa -c 0.95 -T 1 -M 2000 > log.txt 2>&1",
         fp="$FP fasta out.fa", pairs=G),
    # survey5-align
    dict(tool="MUMmer4 nucmer + show-coords (variant as reference)", ver=ver("R5ALIGN", "mummer4"),
         cmd="$R5ALIGN/nucmer -p o $IN $GENOME > log.txt 2>&1 && $R5ALIGN/show-coords -rclTH o.delta > c.txt 2>> log.txt",
         fp="cut -f1-6,12,13 c.txt", pairs=G),
    dict(tool="MUMmer4 nucmer + show-coords (variant as query)", ver=ver("R5ALIGN", "mummer4"),
         cmd="$R5ALIGN/nucmer -p o $GENOME $IN > log.txt 2>&1 && $R5ALIGN/show-coords -rclTH o.delta > c.txt 2>> log.txt",
         fp="cut -f1-6,12,13 c.txt", pairs=G),
    dict(tool="Exonerate protein2genome (variant as target)", ver=ver("R5ALIGN", "exonerate"),
         cmd="$R5ALIGN/exonerate --model protein2genome -q $Q1 -t $IN --bestn 1 --showalignment no "
             "--showvulgar yes > out.txt 2> log.txt",
         fp="grep '^vulgar' out.txt", pairs=G),
    dict(tool="Exonerate ungapped (8 proteins as query)", ver=ver("R5ALIGN", "exonerate"),
         cmd="$R5ALIGN/exonerate --model ungapped -q $IN -t $SMALL --bestn 1 --showalignment no "
             "--showvulgar yes > out.txt 2> log.txt",
         fp="grep '^vulgar' out.txt | sort", pairs=S),
    dict(tool="Clustal Omega (8 proteins)", ver=ver("R5ALIGN", "clustalo"),
         cmd="$R5ALIGN/clustalo -i $IN -o out.fa --outfmt fa --threads 1 > log.txt 2>&1",
         fp="$FP fasta out.fa", pairs=S),
    dict(tool="RAxML-NG --search1 (6-taxon DNA alignment)", ver=ver("R5ALIGN", "raxml-ng"),
         cmd="$R5ALIGN/raxml-ng --search1 --msa $IN --model GTR+G --seed 1 --threads 1 --prefix r > log.txt 2>&1",
         fp="cat r.raxml.bestTree | sed 's/:[0-9.e-]*//g'; grep -E '^(Alignment sites|Final LogLikelihood)' log.txt",
         pairs=A),
    # CheckM2 genome reader only (no database): sequenceClasses.py from CheckM2 1.1.0
    dict(tool="CheckM2 genome reader (SeqReader.read_nucleotide_sequences, before Prodigal)",
         ver="echo CheckM2 $(sed -n 's/__version__ = \"\\(.*\\)\"/\\1/p' $R5CHECKM2SRC/version.py)",
         cmd="python3 -I -c 'import sys, hashlib, importlib.util as u; s = u.spec_from_file_location(\"sc\", sys.argv[1]); "
             "m = u.module_from_spec(s); s.loader.exec_module(m); "
             "[print(n, len(q), hashlib.md5(q.upper().encode()).hexdigest()) "
             "for n, q in m.SeqReader().read_nucleotide_sequences(sys.argv[2]).items()]' "
             "$R5CHECKM2SRC/sequenceClasses.py $IN > fp.txt 2> log.txt",
         fp="cat fp.txt", pairs=pairs("genome", gz=False, raw=True)),
    # survey5-emapper
    dict(tool="eggNOG-mapper input step (diamond mode, custom DB, --no_annot)",
         ver="echo eggnog-mapper $($R5EMAPPER/emapper.py --version 2>/dev/null | grep -o 'emapper-[0-9.]*' | head -1 | cut -d- -f2), "
             "DIAMOND $($R5EMAPPER/diamond version 2>/dev/null | awk '{print $3}')",
         cmd="mkdir -p data && PATH=$R5EMAPPER:$PATH emapper.py -m diamond --dmnd_db $EMDB --data_dir data --no_annot "
             "-i $IN -o e --cpu 1 --override > log.txt 2>&1",
         fp="grep -v '^#' e.emapper.hits | cut -f1,2 | sort", pairs=S),
    dict(tool="eggNOG-mapper input step (mmseqs mode, custom DB, --no_annot)",
         ver="echo eggnog-mapper $($R5EMAPPER/emapper.py --version 2>/dev/null | grep -o 'emapper-[0-9.]*' | head -1 | cut -d- -f2), "
             "MMseqs2 $($R5EMAPPER/mmseqs version 2>/dev/null)",
         cmd="mkdir -p data && PATH=$R5EMAPPER:$PATH emapper.py -m mmseqs --mmseqs_db $EMMDB --data_dir data --no_annot "
             "-i $IN -o e --cpu 1 --override > log.txt 2>&1",
         fp="grep -v '^#' e.emapper.hits | cut -f1,2 | sort", pairs=S),
    dict(tool="eggNOG-mapper iter_fasta_seqs (its own reader: hmmer mode, --md5, novel_fams)",
         ver="echo eggnog-mapper $($R5EMAPPER/emapper.py --version 2>/dev/null | grep -o 'emapper-[0-9.]*' | head -1 | cut -d- -f2)",
         cmd="$R5EMAPPER/python -I -c 'import sys, hashlib; from eggnogmapper.search.hmmer.hmmer_seqio import iter_fasta_seqs as f; "
             "[print(n, len(s), hashlib.md5(s.encode()).hexdigest()) for n, s in f(sys.argv[1], silent=True)]' $IN > fp.txt 2> log.txt",
         fp="cat fp.txt", pairs=S),
]


def sh(cmd, cwd, env):
    p = subprocess.run(["bash", "-c", cmd], cwd=cwd, env=env, capture_output=True, text=True, check=False)
    return p.returncode, p.stdout, p.stderr


def first_err(text):
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if "Traceback (most recent call last)" in text:
        exc = [x for x in lines if re.match(r"^[\w.]*(Error|Exception)\b", x)]
        return (exc or lines)[-1][:200]
    what = [x for x in lines if x.startswith("what():")]
    if what:
        return what[0][:200]
    for keys in (("error", "fatal", "exception", "segmentation", "abort"),
                 ("unexpected", "invalid", "expecting", "unable", "not ", "failed", "can't", "cannot")):
        for s in lines:
            if not s.startswith("#") and any(k in s.lower() for k in keys):
                return s[:200]
    return ""


HEAD = ["header_marker", "type", "tool", "version", "inputs", "control_rc", "fhr_rc", "class",
        "header_lines_in_output", "note"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs")
    ap.add_argument("outdir")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    inp = Path(a.inputs).resolve()
    out = Path(a.outdir).resolve()
    (out / "diff").mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="fhrround5."))
    env = dict(os.environ, HERE=str(HERE), FP=f"python3 -I {HERE.parent / 'fp.py'}",
               GENOME=str(inp / "genome.control.fa"), PROT=str(inp / "proteins.control.fa"),
               SMALL=str(inp / "small.control.fa"), Q1=str(scratch / "q1.faa"), EMDB=str(scratch / "em.dmnd"), EMMDB=str(scratch / "emmdb"))
    for k in ("R5GENE", "R5BARRNAP09", "R5CLUST", "R5ALIGN", "R5EMAPPER", "R5CHECKM2SRC"):
        env.setdefault(k, "/nonexistent")
    # Exonerate query: the first protein of the small set.
    small = (inp / "small.control.fa").read_text().split(">")[1]
    (scratch / "q1.faa").write_text(">" + small)
    # eggNOG-mapper: a DIAMOND database of the plain proteins stands in for the eggNOG one.
    sh("$R5EMAPPER/diamond makedb --in $PROT -d em --quiet && $R5EMAPPER/mmseqs createdb $PROT emmdb -v 1", scratch, env)
    rows, vercache = [], {}
    run_tools = set()
    for t in TESTS:
        if a.only and not any(o and o in t["tool"] for o in a.only.split(",")):
            continue
        run_tools.add(t["tool"])
        if t["ver"] not in vercache:
            lines = sh(t["ver"], scratch, env)[1].strip().splitlines()
            vercache[t["ver"]] = lines[0] if lines else "?"
        version = vercache[t["ver"]]
        for pi, (marker, ctrl, fhr) in enumerate(t["pairs"]):
            res = {}
            for role, fname in (("control", ctrl), ("fhr", fhr)):
                d = scratch / f"{re.sub(r'[^A-Za-z0-9.]+', '_', t['tool'])}.{pi}.{role}"
                d.mkdir()
                shutil.copy(inp / fname, d / fname)
                rc, _, se = sh(t["cmd"], d, dict(env, IN=fname))
                logs = ""
                for lf in ("log.txt", "out.txt"):
                    if (d / lf).exists() and rc != 0:
                        logs += (d / lf).read_text(errors="replace")
                logs += se
                res[role] = (rc, sh(t["fp"], d, dict(env, IN=fname))[1], logs)
                if role == "fhr" and rc != 0:
                    (out / "diff" / f"{d.name}.log").write_text(logs)
            (crc, cfp, clog), (hrc, hfp, hlog) = res["control"], res["fhr"]

            def data(fp):
                return "\n".join(x for x in fp.splitlines() if not x.startswith("fhr-header-lines-in-output"))
            hl = next((x.split(":")[1].strip() for x in hfp.splitlines()
                       if x.startswith("fhr-header-lines-in-output")), "")
            empty = lambda fp: (not data(fp).strip()) or "missing-output" in fp  # noqa: E731
            if crc != 0 or empty(cfp):
                cls, note = "n/a", "control also fails: " + first_err(clog)
            elif hrc != 0:
                cls, note = "c", first_err(hlog)
            elif empty(hfp):
                cls, note = "c(rc0)", first_err(hlog)
            elif data(cfp) == data(hfp):
                cls, note = "a", ""
            else:
                cls, note = "b?", ""
                name = re.sub(r"[^A-Za-z0-9.]+", "_", f"{t['tool']}.{fhr}")
                (out / "diff" / f"{name}.diff").write_text("".join(difflib.unified_diff(
                    data(cfp).splitlines(True), data(hfp).splitlines(True), ctrl, fhr)))
            note = note.replace(str(scratch) + "/", "")
            rows.append([marker, "fasta", t["tool"], version, f"{ctrl} vs {fhr}", str(crc), str(hrc), cls, hl, note])
            print("\t".join(rows[-1]), flush=True)
    tsv = out / "results-round5.tsv"
    old = []
    if tsv.exists():
        old = [r.rstrip("\n").split("\t") for r in tsv.read_text().splitlines()[1:]]
        old = [r for r in old if r[2] not in run_tools]
    order = {t["tool"]: i for i, t in enumerate(TESTS)}
    allrows = sorted(old + rows, key=lambda r: order.get(r[2], 999))
    with open(tsv, "w") as f:
        f.write("\t".join(HEAD) + "\n")
        f.writelines("\t".join(x.replace("\t", " ") for x in r) + "\n" for r in allrows)
    shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
