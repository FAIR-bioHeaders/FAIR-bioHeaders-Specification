#!/usr/bin/env python3
"""Run the FHR tool-compatibility survey.

Usage: run_survey.py INPUTS OUTDIR [--node-dir DIR] [--only SUBSTRING[,SUBSTRING...]]

INPUTS is the directory written by make_inputs.py. Every test is run twice,
on a header-free control file and on the matching FHR-headed file, each in a
fresh scratch directory. Outputs are reduced to a fingerprint (fp.py) and
compared. Automatic classes:

  a   exit 0 and fingerprint identical to control (header ignored or passed
      through; see header_lines_out)
  b?  exit 0 but fingerprint differs from control: candidate silent
      corruption, inspect diff/<tool>.<input>.diff
  c   non-zero exit, or exit 0 with an empty/missing output (marked "c(rc0)")
  n/a control run failed too: failure unrelated to the header

Tools needed on PATH: see environment.yml. vg/odgi may live in a second
environment (environment-graph.yml); JBrowse CLI and @gmod/gff are looked up
in --node-dir/node_modules.
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

FA_PLAIN = [("control.fa", "fhr.fa")]
FA_EDGE = [("control.fa", "edge.comment1.fa")]
FA_CONCAT = [("concat.control.fa", "concat.fhr.fa"), ("concat.control.fa", "concat.mixed.fa")]
FA_GZIP = [("control.gzip.fa.gz", "fhr.gzip.fa.gz")]
FA_BGZF = [("control.bgzf.fa.gz", "fhr.bgzf.fa.gz")]
FA_CRLF = [("control.crlf.fa", "fhr.crlf.fa")]
FA_2LINE = [("control.2line.fa", "fhr.2line.fa")]
GFA = [("control.gfa", "fhr.gfa")]
GFA_NUM = [("control.numeric.gfa", "fhr.numeric.gfa")]
GFF = [("control.gff3", "fhr.gff3"), ("control.gff3", "fhr.sr-before.gff3")]
GFF_FA = [("control.fasta.gff3", "fhr.fasta.gff3")]
FAA = [("control.faa", "fhr.faa")]
ALN = [("control.aln.fa", "fhr.aln.fa")]

FAFP = '$FP fasta out.fa'
SAMFP = '$FP sam out.sam'
PYFA = ('$PY -I -c "import sys,{mod}\n{body}" $IN > out.fa')

TESTS = [
    # ------------------------------------------------------------ FASTA
    dict(t="fasta", tool="samtools faidx", ver="samtools --version | head -1",
         cmd="samtools faidx $IN && samtools faidx $IN chr2:1-60 chr1:101-160 chrM > out.fa",
         fp=FAFP + " && cut -f1-2 $IN.fai", pairs=FA_PLAIN + FA_BGZF + FA_CRLF + FA_GZIP + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="samtools dict", ver="samtools --version | head -1",
         cmd="samtools dict $IN > out.sam", fp=SAMFP, pairs=FA_PLAIN + FA_BGZF + FA_CONCAT),
    dict(t="fasta", tool="bgzip -t", ver="bgzip --version | head -1",
         cmd="bgzip -t $IN && bgzip -dc $IN > out.fa", fp=FAFP, pairs=FA_BGZF),
    dict(t="fasta", tool="pysam.FastaFile", ver="$PY -c 'import pysam;print(\"pysam\",pysam.__version__)'",
         cmd="$PY -I -c 'import pysam,sys\nf=pysam.FastaFile(sys.argv[1])\nfor r in f.references: print(\">\"+r); print(f.fetch(r))' $IN > out.fa",
         fp=FAFP, pairs=FA_PLAIN + FA_BGZF + FA_CONCAT),
    dict(t="fasta", tool="pysam.FastxFile", ver="$PY -c 'import pysam;print(\"pysam\",pysam.__version__)'",
         cmd="$PY -I -c 'import pysam,sys\nfor r in pysam.FastxFile(sys.argv[1]): print(\">\"+r.name); print(r.sequence)' $IN > out.fa",
         fp=FAFP, pairs=FA_PLAIN + FA_GZIP + FA_BGZF + FA_CRLF + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="seqkit stats", ver="seqkit version",
         cmd="seqkit stats -T -a $IN > out.txt",
         fp="tail -n +2 out.txt | cut -f2-", pairs=FA_PLAIN + FA_GZIP + FA_CONCAT),
    dict(t="fasta", tool="seqkit seq", ver="seqkit version",
         cmd="seqkit seq $IN > out.fa", fp=FAFP, pairs=FA_PLAIN + FA_GZIP + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="seqkit grep", ver="seqkit version",
         cmd="seqkit grep -p chr2 -p chrM $IN > out.fa", fp=FAFP, pairs=FA_PLAIN + FA_CONCAT),
    dict(t="fasta", tool="seqkit faidx", ver="seqkit version",
         cmd="seqkit faidx $IN chr2:1-60 chrM > out.fa", fp=FAFP, pairs=FA_PLAIN + FA_BGZF + FA_CONCAT),
    dict(t="fasta", tool="seqtk seq", ver="seqtk 2>&1 | grep Version",
         cmd="seqtk seq -l 60 $IN > out.fa", fp=FAFP, pairs=FA_PLAIN + FA_GZIP + FA_CRLF + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="seqtk comp", ver="seqtk 2>&1 | grep Version",
         cmd="seqtk comp $IN > out.txt", fp="cat out.txt", pairs=FA_PLAIN + FA_GZIP + FA_CONCAT),
    dict(t="fasta", tool="pyfaidx", ver="$PY -c 'import pyfaidx;print(\"pyfaidx\",pyfaidx.__version__)'",
         cmd="$PY -I -c 'import pyfaidx,sys\nf=pyfaidx.Fasta(sys.argv[1])\nfor k in f.keys(): print(\">\"+k); print(f[k][:])' $IN > out.fa",
         fp=FAFP, pairs=FA_PLAIN + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="Biopython SeqIO fasta", ver="$PY -c 'import Bio;print(\"biopython\",Bio.__version__)'",
         cmd="$PY -I -c 'import sys\nfrom Bio import SeqIO\nSeqIO.write(SeqIO.parse(sys.argv[1],\"fasta\"),\"out.fa\",\"fasta\")' $IN",
         fp=FAFP, pairs=FA_PLAIN + FA_CRLF + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="Biopython SeqIO fasta-pearson", ver="$PY -c 'import Bio;print(\"biopython\",Bio.__version__)'",
         cmd="$PY -I -c 'import sys\nfrom Bio import SeqIO\nSeqIO.write(SeqIO.parse(sys.argv[1],\"fasta-pearson\"),\"out.fa\",\"fasta\")' $IN",
         fp=FAFP, pairs=FA_PLAIN + FA_CONCAT),
    dict(t="fasta", tool="Biopython SeqIO fasta-2line", ver="$PY -c 'import Bio;print(\"biopython\",Bio.__version__)'",
         cmd="$PY -I -c 'import sys\nfrom Bio import SeqIO\nSeqIO.write(SeqIO.parse(sys.argv[1],\"fasta-2line\"),\"out.fa\",\"fasta\")' $IN",
         fp=FAFP, pairs=FA_2LINE),
    dict(t="fasta", tool="BWA index + mem", ver="bwa 2>&1 | grep Version",
         cmd="bwa index -p idx $IN 2>/dev/null && bwa mem idx $READS > out.sam 2>/dev/null",
         fp=SAMFP, pairs=FA_PLAIN + FA_GZIP + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="minimap2 -d + map", ver="echo minimap2 $(minimap2 --version)",
         cmd="minimap2 -d idx.mmi $IN 2>/dev/null && minimap2 -a idx.mmi $READS > out.sam 2>/dev/null",
         fp=SAMFP, pairs=FA_PLAIN + FA_GZIP + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="bowtie2-build", ver="bowtie2-build --version | head -1 | sed 's,.*/,,'",
         cmd="bowtie2-build $IN idx > log.txt 2>&1 && bowtie2-inspect idx > out.fa",
         fp=FAFP, pairs=FA_PLAIN + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="hisat2-build", ver="hisat2-build --version | head -1 | sed 's,.*/,,'",
         cmd="hisat2-build $IN idx > log.txt 2>&1 && hisat2-inspect idx > out.fa",
         fp=FAFP, pairs=FA_PLAIN + FA_CONCAT),
    dict(t="fasta", tool="STAR genomeGenerate", ver="echo STAR $(STAR --version)",
         cmd="mkdir -p g && STAR --runMode genomeGenerate --genomeDir g --genomeFastaFiles $IN --genomeSAindexNbases 4 --outFileNamePrefix g/ > log.txt 2>&1",
         fp="cat g/chrNameLength.txt", pairs=FA_PLAIN + FA_CONCAT),
    dict(t="fasta", tool="salmon index", ver="salmon --version",
         cmd="salmon index -t $IN -i idx -k 21 > log.txt 2>&1",
         fp="cat idx/refseq_offsets.json && md5sum < idx/refseq.bin", pairs=FA_PLAIN + FA_CONCAT),
    dict(t="fasta", tool="kallisto index", ver="kallisto version",
         cmd="kallisto index -i idx $IN > log.txt 2>&1 && kallisto inspect idx > out.txt 2>&1",
         fp="grep -E 'targets|k-mers|unitigs' out.txt", pairs=FA_PLAIN + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="makeblastdb", ver="makeblastdb -version | head -1",
         cmd="makeblastdb -in $IN -dbtype nucl -parse_seqids -out db > log.txt && blastdbcmd -db db -entry all > out.fa",
         fp=FAFP, pairs=FA_PLAIN + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="bedtools getfasta", ver="bedtools --version",
         cmd="printf 'chr2\\t0\\t60\\nchr1\\t100\\t160\\n' > r.bed && bedtools getfasta -fi $IN -bed r.bed > out.fa",
         fp=FAFP, pairs=FA_PLAIN + FA_BGZF + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="Picard CreateSequenceDictionary", ver="echo picard $(picard CreateSequenceDictionary --version 2>&1 | tail -1)",
         cmd="picard CreateSequenceDictionary -R $IN -O out.sam > log.txt 2>&1",
         fp=SAMFP, pairs=FA_PLAIN + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="UCSC faToTwoBit", ver="ls $(dirname $(command -v faToTwoBit))/../conda-meta | grep -o '^ucsc-fatotwobit-[0-9][0-9.]*' | head -1",
         cmd="faToTwoBit $IN out.2bit && twoBitToFa out.2bit out.fa", fp=FAFP, pairs=FA_PLAIN + FA_CONCAT),
    dict(t="fasta", tool="UCSC faSize", ver="ls $(dirname $(command -v faSize))/../conda-meta | grep -o '^ucsc-fasize-[0-9][0-9.]*' | head -1",
         cmd="faSize -detailed $IN > out.txt", fp="cat out.txt", pairs=FA_PLAIN + FA_CONCAT),
    dict(t="fasta", tool="bioawk", ver="ls $(dirname $(command -v bioawk))/../conda-meta | grep -o '^bioawk-[0-9][0-9.]*' | head -1",
         cmd="bioawk -c fastx '{print \">\"$name; print $seq}' $IN > out.fa", fp=FAFP, pairs=FA_PLAIN + FA_GZIP + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="pyfastx", ver="$PY -c 'import pyfastx;print(\"pyfastx\",pyfastx.__version__)'",
         cmd="$PY -I -c 'import pyfastx,sys\nfor s in pyfastx.Fasta(sys.argv[1]): print(\">\"+s.name); print(s.seq)' $IN > out.fa",
         fp=FAFP, pairs=FA_PLAIN + FA_GZIP + FA_CONCAT),
    dict(t="fasta", tool="MAFFT", ver="echo mafft $(mafft --version 2>&1)",
         cmd="mafft --quiet --auto $IN > out.fa", fp=FAFP, pairs=FA_PLAIN + FA_EDGE + FA_CONCAT),
    dict(t="fasta", tool="gffread -g (genome FASTA)", ver="echo gffread $(gffread --version 2>&1)",
         cmd="gffread $GFF -g $IN -x out.fa", fp=FAFP, pairs=FA_PLAIN + FA_CONCAT),
    dict(t="fasta", tool="AGAT/BioPerl Bio::DB::Fasta", ver="echo AGAT $(agat --version 2>&1 | tail -1)",
         cmd="agat_sp_extract_sequences.pl --gff $GFF -f $IN -t cds -o out.fa > log.txt 2>&1",
         fp=FAFP, pairs=FA_PLAIN + FA_CONCAT),
    dict(t="fasta", tool="JBrowse CLI add-assembly", ver="echo @jbrowse/cli $($NODE/node_modules/.bin/jbrowse --version | awk '{print $NF}')",
         cmd="(samtools faidx $IN 2>faidx.txt || true) && mkdir jb && $NODE/node_modules/.bin/jbrowse add-assembly $IN --load copy --out jb -n g > out.txt 2>&1",
         fp="ls jb", pairs=FA_PLAIN + FA_CONCAT),
    # ------------------------------------------------------------ FASTA, 2026-10-18 additions
    # environment-extra.yml; Rust probes in rust/ ($RUSTBIN); FASTX.jl ($JULIA)
    dict(t="fasta", tool="Bioconductor Biostrings readDNAStringSet",
         ver="Rscript -e 'cat(\"Biostrings\", as.character(packageVersion(\"Biostrings\")), \"\\n\")' 2>/dev/null",
         cmd="Rscript -e 'suppressMessages(library(Biostrings)); writeXStringSet(readDNAStringSet(commandArgs(TRUE)[1]), \"out.fa\")' $IN",
         fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="scikit-bio skbio.io.read", ver="$PY -c 'import skbio;print(\"scikit-bio\",skbio.__version__)'",
         cmd="$PY -I -c 'import skbio,sys\nfor q in skbio.io.read(sys.argv[1], format=\"fasta\"): print(\">\"+q.metadata[\"id\"]); print(str(q))' $IN > out.fa",
         fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="noodles-fasta (Rust)", ver="echo noodles-fasta $(grep -A1 'name = \"noodles-fasta\"' $RUSTDIR/Cargo.lock | sed -n 2p | cut -d'\"' -f2)",
         cmd="$RUSTBIN/noodles_fasta $IN > out.fa", fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="rust-bio bio::io::fasta", ver="echo bio $(grep -A1 'name = \"bio\"' $RUSTDIR/Cargo.lock | sed -n 2p | cut -d'\"' -f2)",
         cmd="$RUSTBIN/rust_bio $IN > out.fa", fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="BioJulia FASTX.jl", ver="$JULIA --startup-file=no -e 'using FASTX; println(\"FASTX \", pkgversion(FASTX))'",
         cmd="$JULIA --startup-file=no -e 'using FASTX; FASTAReader(open(ARGS[1])) do r; for x in r; println(\">\", identifier(x)); println(sequence(x)); end; end' $IN > out.fa",
         fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="HMMER/Easel esl-reformat", ver="echo hmmer $(hmmsearch -h | grep -o 'HMMER [0-9.]*' | head -1 | cut -d' ' -f2)",
         cmd="esl-reformat fasta $IN > out.fa", fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="EMBOSS seqret", ver="echo EMBOSS $(embossversion -auto 2>/dev/null)",
         cmd="seqret -sequence $IN -outseq out.fa -auto", fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="MMseqs2 createdb", ver="echo mmseqs $(mmseqs version)",
         cmd="mmseqs createdb $IN db > log.txt 2>&1 && mmseqs convert2fasta db out.fa > log.txt 2>&1",
         fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="DIAMOND makedb (protein)", ver="diamond version",
         cmd="diamond makedb --in $IN -d db > log.txt 2>&1 && diamond getseq -d db --out out.fa >> log.txt 2>&1",
         fp=FAFP, pairs=FAA),
    dict(t="fasta", tool="CD-HIT cd-hit-est", ver="echo cd-hit $(cd-hit-est -h 2>&1 | grep -o 'version [0-9.]*' | head -1)",
         cmd="cd-hit-est -i $IN -o out.fa -c 1.0 -n 10 > log.txt 2>&1", fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="Clustal Omega", ver="echo clustalo $(clustalo --version)",
         cmd="clustalo -i $IN -o out.fa --force > log.txt 2>&1", fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="MUSCLE -align", ver="muscle -version 2>&1 | head -1",
         cmd="muscle -align $IN -output out.fa > log.txt 2>&1", fp=FAFP, pairs=FA_PLAIN),
    dict(t="fasta", tool="IQ-TREE (alignment)", ver="iqtree3 --version 2>&1 | grep -o 'version [0-9.]*' | head -1",
         cmd="iqtree3 -s $IN -m JC -nt 1 -seed 1 --prefix t -redo > log.txt 2>&1",
         fp="cat t.treefile 2>/dev/null || echo missing-output", pairs=ALN),
    # ------------------------------------------------------------ GFA
    dict(t="gfa", tool="gfatools stat", ver="echo gfatools $(gfatools version 2>&1 | grep gfatools | awk '{print $2}')",
         cmd="gfatools stat $IN > out.txt 2>/dev/null", fp="cat out.txt", pairs=GFA),
    dict(t="gfa", tool="gfatools gfa2fa", ver="true",
         cmd="gfatools gfa2fa $IN > out.fa 2>/dev/null", fp=FAFP, pairs=GFA),
    dict(t="gfa", tool="gfatools view", ver="true",
         cmd="gfatools view $IN > out.gfa 2>/dev/null", fp="$FP gfa out.gfa", pairs=GFA),
    dict(t="gfa", tool="vg convert -g -f", ver="vg version | head -1",
         cmd="vg convert -g $IN -f > out.gfa 2>log.txt", fp="$FP gfa out.gfa", pairs=GFA),
    dict(t="gfa", tool="vg stats", ver="true",
         cmd="vg convert -g $IN -p > g.vg 2>log.txt && vg stats -lz g.vg > out.txt", fp="cat out.txt", pairs=GFA),
    dict(t="gfa", tool="odgi build + stats", ver="echo odgi $(odgi version)",
         cmd="odgi build -g $IN -o g.og > log.txt 2>&1 && odgi stats -i g.og -S > out.txt 2>>log.txt",
         fp="cat out.txt", pairs=GFA_NUM),
    dict(t="gfa", tool="odgi view", ver="true",
         cmd="odgi build -g $IN -o g.og > log.txt 2>&1 && odgi view -i g.og -g > out.gfa 2>>log.txt",
         fp="$FP gfa out.gfa", pairs=GFA_NUM),
    dict(t="gfa", tool="gfapy (parse + write)", ver="$PY -c 'import importlib.metadata as m;print(\"gfapy\",m.version(\"gfapy\"))'",
         cmd="$PY -I -c 'import gfapy,sys\ng=gfapy.Gfa.from_file(sys.argv[1])\ng.to_file(\"out.gfa\")' $IN",
         fp="$FP gfa out.gfa", pairs=GFA),
    # ------------------------------------------------------------ GFF3
    dict(t="gff3", tool="gt gff3validator", ver="gt --version | head -1",
         cmd="gt gff3validator $IN > out.txt 2>&1", fp="cat out.txt", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="gt gff3 -sort -tidy", ver="true",
         cmd="gt gff3 -sort -tidy -retainids $IN > out.gff3 2>log.txt", fp="$FP text out.gff3", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="gffread -T (GTF)", ver="echo gffread $(gffread --version 2>&1)",
         cmd="gffread $IN -T -o out.gtf 2>log.txt", fp="$FP text out.gtf", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="gffread -E (GFF3 out)", ver="true",
         cmd="gffread $IN -E -o out.gff3 2>log.txt",
         fp="grep -v '^# ' out.gff3 > o2.gff3; $FP text o2.gff3", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="gffread -g -x (CDS extract)", ver="true",
         cmd="gffread $IN -g $GENOME -x out.fa 2>log.txt", fp=FAFP, pairs=GFF + GFF_FA),
    dict(t="gff3", tool="AGAT agat_convert_sp_gxf2gxf.pl", ver="echo AGAT $(agat --version 2>&1 | tail -1)",
         cmd="agat_convert_sp_gxf2gxf.pl --gff $IN -o out.gff3 > log.txt 2>&1", fp="$FP text out.gff3", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="AGAT agat_sp_statistics.pl", ver="true",
         cmd="agat_sp_statistics.pl --gff $IN -o out.txt > log.txt 2>&1", fp="$FP text out.txt", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="gffutils create_db", ver="$PY -c 'import gffutils;print(\"gffutils\",gffutils.__version__)'",
         cmd="$PY -I -c 'import gffutils,sys\ndb=gffutils.create_db(sys.argv[1],\"db.sqlite\",merge_strategy=\"create_unique\")\nprint(sorted((f.featuretype,f.seqid,f.start,f.end,f.id) for f in db.all_features()))\nprint(db.directives)' $IN > out.txt",
         fp="cat out.txt", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="bedtools sort", ver="bedtools --version",
         cmd="bedtools sort -header -i $IN > out.gff3", fp="$FP text out.gff3", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="bedtools intersect", ver="true",
         cmd="printf 'chr1\\t150\\t1200\\n' > q.bed && bedtools intersect -a $IN -b q.bed > out.gff3",
         fp="$FP text out.gff3", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="bgzip + tabix -p gff", ver="tabix --version | head -1",
         cmd="(grep '^#' $IN; grep -v '^#' $IN | sort -k1,1 -k4,4n) | bgzip > s.gff3.gz && tabix -p gff s.gff3.gz && tabix s.gff3.gz chr1:150-1200 > out.gff3",
         fp="$FP text out.gff3", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="htseq-count", ver="$PY -c 'import HTSeq;print(\"HTSeq\",HTSeq.__version__)'",
         cmd="htseq-count -f bam -t exon -i Parent $BAM $IN > out.txt 2>log.txt", fp="cat out.txt", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="featureCounts", ver="featureCounts -v 2>&1 | grep -o 'v[0-9.]*'",
         cmd="featureCounts -F GTF -t exon -g Parent -a $IN -o out.txt $BAM > log.txt 2>&1",
         fp="grep -v '^#' out.txt", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="JBrowse CLI add-track + text-index", ver="echo @jbrowse/cli $($NODE/node_modules/.bin/jbrowse --version | awk '{print $NF}')",
         cmd="J=$NODE/node_modules/.bin/jbrowse; mkdir jb && $J add-assembly $GENOME --load copy --out jb -n g >log.txt 2>&1 && $J add-track $IN --load copy --out jb -a g --trackId t >>log.txt 2>&1 && $J text-index --out jb -q >>log.txt 2>&1",
         fp="cat jb/trix/g.ix", pairs=GFF + GFF_FA),
    dict(t="gff3", tool="@gmod/gff parser (JBrowse 2)", ver="echo @gmod/gff $(grep '\"version\"' $NODE/node_modules/@gmod/gff/package.json | grep -o '[0-9][0-9.]*')",
         cmd="node $NODE/gff_probe.mjs $IN > out.txt", fp="sed 's/\"C\":[0-9]*,//' out.txt", pairs=GFF + GFF_FA),
]


def sh(cmd, cwd, env):
    p = subprocess.run(["bash", "-c", cmd], cwd=cwd, env=env, capture_output=True, text=True, check=False)
    return p.returncode, p.stdout, p.stderr


def first_err(text):
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    for line in text.splitlines():
        s = line.strip()
        if s and any(k in s.lower() for k in ("error", "exception", "fatal", "unexpected", "invalid",
                                              "expecting", "warning", "not ", "failed")):
            return s[:160]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs")
    ap.add_argument("outdir")
    ap.add_argument("--node-dir", default=os.environ.get("SURVEY_NODE_DIR", ""))
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    inp = Path(a.inputs).resolve()
    out = Path(a.outdir).resolve()
    (out / "diff").mkdir(parents=True, exist_ok=True)
    node = Path(a.node_dir).resolve() if a.node_dir else None
    if node:
        shutil.copy(HERE / "gff_probe.mjs", node / "gff_probe.mjs")
    scratch = Path(tempfile.mkdtemp(prefix="fhrsurvey."))
    # Shared fixtures: control genome, its .fai, reads, a small BAM
    fx = scratch / "fixtures"
    fx.mkdir()
    shutil.copy(inp / "fasta" / "control.fa", fx / "genome.fa")
    shutil.copy(inp / "gff3" / "control.gff3", fx / "genes.gff3")
    env = dict(os.environ, FP=f"python3 -I {HERE / 'fp.py'}", PY="python3",
               READS=str(inp / "reads" / "reads.fq"), GENOME=str(fx / "genome.fa"),
               GFF=str(fx / "genes.gff3"), BAM=str(fx / "reads.bam"),
               NODE=str(node) if node else "/nonexistent",
               RUSTDIR=str(HERE / "rust"),
               RUSTBIN=os.environ.get("RUSTBIN", str(HERE / "rust" / "target" / "release")),
               JULIA=os.environ.get("JULIA", "julia"))
    sh("samtools faidx genome.fa && minimap2 -a genome.fa $READS 2>/dev/null | samtools sort -o reads.bam - && samtools index reads.bam",
       fx, env)
    rows = []
    vercache = {}
    last_ver = ""
    for t in TESTS:
        if a.only and not any(o and o in t["tool"] for o in a.only.split(",")):
            continue
        v = t["ver"]
        if v != "true":
            if v not in vercache:
                vercache[v] = sh(v, scratch, env)[1].strip().splitlines()[0:1]
                vercache[v] = vercache[v][0] if vercache[v] else "?"
            last_ver = vercache[v]
        version = last_ver
        sub = {"fasta": "fasta", "gfa": "gfa", "gff3": "gff3"}[t["t"]]
        for pi, (ctrl, fhr) in enumerate(t["pairs"]):
            res = {}
            for role, fname in (("control", ctrl), ("fhr", fhr)):
                d = scratch / f"{t['tool'].replace(' ', '_').replace('/', '_')}.{pi}.{fname}.{role}"
                d.mkdir()
                shutil.copy(inp / sub / fname, d / fname)
                e = dict(env, IN=fname)
                rc, _, se = sh(t["cmd"], d, e)
                logs = se
                for lf in ("log.txt", "out.txt"):
                    if (d / lf).exists() and rc != 0:
                        logs += (d / lf).read_text(errors="replace")
                _, fp, _ = sh(t["fp"], d, e)
                res[role] = (rc, fp, logs)
            (crc, cfp, _), (hrc, hfp, hlog) = res["control"], res["fhr"]
            def data(fp):
                return "\n".join(l for l in fp.splitlines() if not l.startswith("fhr-header-lines-in-output"))
            hl = ""
            for l in hfp.splitlines():
                if l.startswith("fhr-header-lines-in-output"):
                    hl = l.split(":")[1].strip()
            empty = lambda fp: (not data(fp).strip()) or "missing-output" in fp
            if crc != 0 or empty(cfp):
                cls = "n/a"
            elif hrc != 0:
                cls = "c"
            elif empty(hfp):
                cls = "c(rc0)"
            elif data(cfp) == data(hfp):
                cls = "a"
            else:
                cls = "b?"
            note = first_err(hlog) if cls.startswith("c") or cls == "n/a" else ""
            if cls == "n/a":
                note = "control also fails: " + first_err(res["control"][2])
            note = note.replace(str(scratch) + "/", "")
            if cls == "b?":
                name = f"{t['tool']}.{fhr}".replace(" ", "_").replace("/", "_")
                (out / "diff" / f"{name}.diff").write_text("".join(difflib.unified_diff(
                    data(cfp).splitlines(True), data(hfp).splitlines(True), ctrl, fhr)))
            rows.append([t["t"], t["tool"], version, f"{ctrl} vs {fhr}", str(crc), str(hrc), cls, hl, note])
            print("\t".join(rows[-1]), flush=True)
    with open(out / "results.tsv", "w") as f:
        f.write("\t".join(["type", "tool", "version", "inputs", "control_rc", "fhr_rc", "class",
                           "header_lines_in_output", "note"]) + "\n")
        f.writelines("\t".join(x.replace("\t", " ") for x in r) + "\n" for r in rows)
    shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
