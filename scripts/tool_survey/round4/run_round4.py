#!/usr/bin/env python3
"""Run the 2026-10-22 survey (docs/TOOL_COMPATIBILITY.md, "More tools (2026-10-22)").

Usage: run_round4.py INPUTS OUTDIR [--only NAME,...]

INPUTS is a directory written by make_round4_inputs.py. Each test runs on the
control and on each variant in a fresh directory, fingerprints the output and
classifies it as run_survey.py does (a, b?, c, c(rc0), n/a). Results go to
OUTDIR/results-round4.tsv and differing fingerprints to OUTDIR/diff/.

The tools live in separate environments (environment-round4.yml); point to
their bin directories with R4R, R4BAKTA, R4KRAKEN, R4BWA, R4VEP and R4HTS
(samtools, bgzip), and to an `npm install` of round4/package.json with R4NODE.
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

PLAIN = [("semicolon", "control.fa", "fhr.fa"), ("semicolon-1line", "control.fa", "comment1.fa"),
         ("hash", "control.fa", "hash.fa"), ("unmarked", "control.fa", "text.fa"),
         ("semicolon-raw-markers", "control.fa", "raw.fa")]
GZ = [("semicolon", "control.fa.gz", "fhr.fa.gz")]
BGZF = [("semicolon", "control.bgzf.fa.gz", "fhr.bgzf.fa.gz")]

R = "$R4R/Rscript $HERE/r_probe.R"
RVER = "$R4R/Rscript -e 'cat(\"{0} \", as.character(packageVersion(\"{0}\")), \" (R \", as.character(getRversion()), \")\\n\", sep = \"\")'"
JB = "$R4NODE/node_modules/.bin/jbrowse"
JBVER = "echo @jbrowse/cli $(grep '\"version\"' $R4NODE/node_modules/@jbrowse/cli/package.json | grep -o '[0-9][0-9.]*')"
IFVER = "echo @gmod/indexedfasta $(grep '\"version\"' $R4NODE/node_modules/@gmod/indexedfasta/package.json | grep -o '[0-9][0-9.]*')"
PROBE = "node $R4NODE/indexedfasta_probe.mjs"
# A .fai that skips the leading block, as pyfaidx 0.9.1 writes it; for BGZF the
# offsets come from the uncompressed copy and bgzip -r adds the .gzi.
HFAI = ("case $IN in *.gz) $R4HTS/bgzip -dc $IN > plain.fa && python3 -I $HERE/header_fai.py plain.fa $IN.fai "
        "&& $R4HTS/bgzip -r $IN;; *) python3 -I $HERE/header_fai.py $IN;; esac")
VEP = ("PATH=$R4VEP:$PATH vep --gff $VEPGFF --fasta $IN -i $VCF -o out.txt --tab --hgvs --no_stats "
       "--fields Uploaded_variation,Location,Allele,Consequence,Protein_position,Amino_acids,Codons,HGVSc,HGVSp "
       "> log.txt 2>&1")
VEPVER = ("echo ensembl-vep $(PATH=$R4VEP:$PATH vep --help 2>&1 | awk '/ensembl-vep /{print $3}'), "
          "Bio::DB::HTS $(PATH=$R4VEP:$PATH perl -MBio::DB::HTS -e 'print $Bio::DB::HTS::VERSION')")
BAKTA = ("PATH=$R4BAKTA:$PATH bakta --db $STUBDB --skip-trna --skip-tmrna --skip-rrna --skip-ncrna "
         "--skip-ncrna-region --skip-crispr --skip-cds --skip-pseudo --skip-sorf --skip-gap --skip-ori "
         "--skip-plot --output o --prefix g $IN > log.txt 2>&1")
KBUILD = ("export PATH=$R4KRAKEN:$PATH; mkdir -p db/taxonomy && cp $KTAX/* db/taxonomy/ "
          "&& kraken2-build --add-to-library $IN --db db > log.txt 2>&1 "
          "&& kraken2-build --build --db db >> log.txt 2>&1 && kraken2 --db db $READS > cls.txt 2>> log.txt")

TESTS = [
    dict(tool="Biostrings readDNAStringSet", ver=RVER.format("Biostrings"),
         cmd=f"{R} biostrings $IN > fp.txt", fp="cat fp.txt", pairs=PLAIN + GZ),
    dict(tool="Biostrings fasta.index + readDNAStringSet", ver=RVER.format("Biostrings"),
         cmd=f"{R} biostrings_index $IN > fp.txt", fp="cat fp.txt", pairs=PLAIN + GZ),
    dict(tool="seqinr read.fasta", ver=RVER.format("seqinr"),
         cmd=f"{R} seqinr $IN > fp.txt", fp="cat fp.txt", pairs=PLAIN + GZ),
    dict(tool="ape read.FASTA", ver=RVER.format("ape"),
         cmd=f"{R} ape_FASTA $IN > fp.txt", fp="cat fp.txt", pairs=PLAIN + GZ),
    dict(tool="ape read.dna(format=fasta)", ver=RVER.format("ape"),
         cmd=f"{R} ape_dna $IN > fp.txt", fp="cat fp.txt", pairs=PLAIN + GZ),
    dict(tool="JBrowse CLI add-assembly (.fai from samtools faidx)", ver=JBVER,
         cmd=f"($R4HTS/samtools faidx $IN 2> faidx.txt || true) && mkdir jb && {JB} add-assembly $IN --load copy --out jb -n g > out.txt 2>&1",
         fp="ls jb", pairs=PLAIN + BGZF),
    dict(tool="JBrowse CLI add-assembly + @gmod/indexedfasta read (header-aware .fai)", ver=IFVER,
         cmd=f"{HFAI} && mkdir jb && {JB} add-assembly $IN --load copy --out jb -n g > out.txt 2>&1 "
             f"&& case $IN in *.gz) {PROBE} bgzip jb/$IN;; *) {PROBE} indexed jb/$IN;; esac > fp.txt",
         fp="cat fp.txt", pairs=PLAIN + BGZF),
    dict(tool="@gmod/indexedfasta FetchableSmallFasta (JBrowse UnindexedFastaAdapter parser)", ver=IFVER,
         cmd=f"{PROBE} small $IN > fp.txt", fp="cat fp.txt", pairs=PLAIN),
    dict(tool="Bakta genome import (stub DB, all annotation steps skipped)",
         ver="PATH=$R4BAKTA:$PATH bakta --version", cmd=BAKTA, fp="$FP fasta o/g.fna", pairs=PLAIN + GZ),
    dict(tool="Kraken2 add-to-library + build + classify reads",
         ver="$R4KRAKEN/kraken2 --version | head -1", cmd=KBUILD,
         fp="md5sum < db/hash.k2d; cat db/seqid2taxid.map cls.txt", pairs=PLAIN + GZ),
    dict(tool="Kraken2 classify (genome FASTA as query)", ver="$R4KRAKEN/kraken2 --version | head -1",
         cmd="$R4KRAKEN/kraken2 --db $KDB $IN > cls.txt 2> log.txt", fp="cut -f1-4 cls.txt", pairs=PLAIN + GZ),
    dict(tool="BWA-MEM2 index + mem", ver="echo bwa-mem2 $(ls $R4BWA/../conda-meta | sed -n 's/^bwa-mem2-\\([0-9.]*\\)-.*/\\1/p')"
             " '(binary reports' $($R4BWA/bwa-mem2 version 2>/dev/null | tail -1)')'",
         cmd="$R4BWA/bwa-mem2 index $IN > log.txt 2>&1 && $R4BWA/bwa-mem2 mem $IN $READS > out.sam 2>> log.txt",
         fp="$FP sam out.sam", pairs=PLAIN + GZ),
    dict(tool="BWA index + mem", ver="echo bwa $($R4BWA/bwa 2>&1 | awk '/^Version/{print $2}')",
         cmd="$R4BWA/bwa index $IN > log.txt 2>&1 && $R4BWA/bwa mem $IN $READS > out.sam 2>> log.txt",
         fp="$FP sam out.sam", pairs=PLAIN + GZ),
    dict(tool="Ensembl VEP --gff --fasta (Bio::DB::HTS::Faidx)", ver=VEPVER,
         cmd=VEP, fp="grep -v '^##' out.txt", pairs=PLAIN + BGZF),
    dict(tool="Ensembl VEP --gff --fasta (header-aware .fai)", ver=VEPVER,
         cmd=f"{HFAI} && {VEP}", fp="grep -v '^##' out.txt", pairs=PLAIN + BGZF),
]


def sh(cmd, cwd, env):
    p = subprocess.run(["bash", "-c", cmd], cwd=cwd, env=env, capture_output=True, text=True, check=False)
    return p.returncode, p.stdout, p.stderr


def first_err(text):
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    for line in text.splitlines():
        s = line.strip()
        if s and any(k in s.lower() for k in ("error", "exception", "fatal", "unexpected", "invalid",
                                              "expecting", "segmentation", "unable", "not ", "failed")):
            return s[:160]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs")
    ap.add_argument("outdir")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    inp = Path(a.inputs).resolve()
    out = Path(a.outdir).resolve()
    (out / "diff").mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="fhrround4."))
    fx = scratch / "fixtures"
    fx.mkdir()
    env = dict(os.environ, HERE=str(HERE), FP=f"python3 -I {HERE.parent / 'fp.py'}",
               READS=str(inp / "reads.fq"), VEPGFF=str(inp / "vep" / "genes.gff.gz"),
               VCF=str(inp / "vep" / "test.vcf"), KTAX=str(inp / "kraken-taxonomy"),
               STUBDB=str(fx / "bakta-stub-db"), KDB=str(fx / "kdb"))
    for k in ("R4R", "R4NODE", "R4BAKTA", "R4KRAKEN", "R4BWA", "R4VEP", "R4HTS"):
        env.setdefault(k, "/nonexistent")
    if env["R4NODE"] != "/nonexistent":
        shutil.copy(HERE / "indexedfasta_probe.mjs", Path(env["R4NODE"]) / "indexedfasta_probe.mjs")
    # Bakta checks for its database files before it reads the genome; with every
    # annotation step skipped, empty files are enough to reach and pass the import.
    sh("set -e; names=$(PATH=$R4BAKTA:$PATH python -I -c 'import bakta.db as d; print(\" \".join(d.FILE_NAMES))'); "
       "major=$(PATH=$R4BAKTA:$PATH python -I -c 'import bakta; print(bakta.__db_schema_version__)'); "
       "mkdir -p $STUBDB; for f in $names pscc.dmnd; do : > $STUBDB/$f; done; "
       "echo \"{\\\"date\\\":\\\"2026-01-01\\\",\\\"major\\\":$major,\\\"minor\\\":0,\\\"type\\\":\\\"light\\\"}\" > $STUBDB/version.json",
       fx, env)
    shutil.copy(inp / "control.fa", fx / "control.fa")
    sh("export PATH=$R4KRAKEN:$PATH; mkdir -p kdb/taxonomy && cp $KTAX/* kdb/taxonomy/ && "
       "kraken2-build --add-to-library control.fa --db kdb && kraken2-build --build --db kdb", fx, env)
    rows, vercache = [], {}
    for t in TESTS:
        if a.only and not any(o and o in t["tool"] for o in a.only.split(",")):
            continue
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
                for lf in ("log.txt", "out.txt", "faidx.txt"):
                    if (d / lf).exists() and rc != 0:
                        logs += (d / lf).read_text(errors="replace")
                logs += se
                res[role] = (rc, sh(t["fp"], d, dict(env, IN=fname))[1], logs)
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
    with open(out / "results-round4.tsv", "w") as f:
        f.write("\t".join(["header_marker", "type", "tool", "version", "inputs", "control_rc", "fhr_rc", "class",
                           "header_lines_in_output", "note"]) + "\n")
        f.writelines("\t".join(x.replace("\t", " ") for x in r) + "\n" for r in rows)
    shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
