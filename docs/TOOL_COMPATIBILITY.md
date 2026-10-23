# Tool compatibility of FHR-headed files

This survey tests how common bioinformatics tools handle FASTA, GFA and GFF3
files that carry FHR header lines (`;~` in FASTA, `#~` in GFA and GFF3). It
answers [#40](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/40)
(FASTA and GFA tools) and
[#49](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/49) (GFF3
tools; spec 007 FR-006). Run date: 2026-10-08.

## Method

Every test runs twice in fresh directories. One run uses a header-free control
file and the other uses the same file with an FHR header. Each output is reduced
to a fingerprint: record names, lengths and an MD5 of the upper-cased sequence
for FASTA/SAM output, sorted `S`/`L`/`P` lines for GFA, and an MD5 of the text
with `;~`/`#~` lines removed for other outputs. For FASTA, only the leading `;`
block is excluded; `;` text inside a record counts as sequence, so absorbed
header text shows up as a change. The two fingerprints are then compared.
Separately, the survey counts how many FHR lines the tool copied into its
output. The runner marks differences as `b?`. Each one was checked by hand
against its diff in
[results/diff](../scripts/tool_survey/results/diff), and all are reported
below as **b**.

| Class | Meaning |
| --- | --- |
| **a** | Works. Exit 0 and output identical to the control run. The header is ignored, or copied through (see "header kept"). |
| **b** | Works but misreads the header as sequence or names. Exit 0 and output differs from the control: silent corruption. |
| **c** | Fails. Non-zero exit, or **c (exit 0)**: prints an error and writes no data but exits 0. |
| n/a | The control file fails too, so the header is not the cause. |

Inputs come from [scripts/tool_survey/make_inputs.py](../scripts/tool_survey/make_inputs.py),
and the runner is [run_survey.py](../scripts/tool_survey/run_survey.py). The
raw results are in [results.tsv](../scripts/tool_survey/results/results.tsv).

- **FASTA**: three records (5000, 3000 and 1200 bp; 60-column lines; one
  soft-masked stretch). The FHR copy is made with `fhr-fasta-combine` 0.3.3 and
  [example.fhr.yaml](../examples/example.fhr.yaml), giving 52 `;~` lines.
  Variants: plain; gzip (made with Python `gzip`, not BGZF); BGZF (written by
  `fhr-fasta-combine -o x.fa.gz`; the BGZF control was made with
  `fhr-fasta-strip`); CRLF line endings; unwrapped (for `fasta-2line`); and
  `edge.comment1.fa`, which has one leading `;` line. That edge file is not
  valid FHR. It probes parsers that read leading lines as an unnamed record.
  Two concatenations, both invalid under R10, test what happens when header
  lines follow a record. `concat.fhr.fa` is `cat genome.fhr.fa extra.fhr.fa`.
  `concat.mixed.fa` is `cat genome.fa extra.fhr.fa`. Both are compared with
  `cat genome.fa extra.fa`.
- **GFA**: GFA1 with four segments, four links and two paths. The FHR copy is
  made with `fhr-gfa-combine`. A copy with numeric segment IDs is used for odgi.
- **GFF3**: three genes (one with two mRNAs), multi-line CDS features, and two
  `##sequence-region` lines. The survey predates the FHGFF3 release, so the 25 `#~` lines are
  hand-written, schema-like YAML rather than toolkit output. The lines follow `##gff-version 3` and come
  either before (`fhr.gff3`) or after (`fhr.sr-before.gff3`) the
  `##sequence-region` lines. A third variant has a `##FASTA` section.
- **Mapping**: 20 exact 150 bp reads. A small BAM for the counting tools is made
  by mapping them to the control genome.

## Environment

Linux x86-64; conda-forge and bioconda through micromamba. The pins are in
[environment.yml](../scripts/tool_survey/environment.yml) and
[environment-graph.yml](../scripts/tool_survey/environment-graph.yml). Other
software: Node 20.19.4 with `@jbrowse/cli` 4.3.0 and `@gmod/gff` 2.1.0
([package.json](../scripts/tool_survey/package.json)), and the FHR converter
(`fhr`) 0.3.3.

## FASTA

| Tool | Version | Command | Inputs | Class | Notes |
| --- | --- | --- | --- | --- | --- |
| samtools faidx | 1.24 (htslib 1.24) | `samtools faidx x.fa`; region fetch | plain, BGZF, CRLF, edge | **c** | `[E::fai_build_core] Format error, unexpected ";" at line 1`; no `.fai` written. Plain gzip is n/a (the control fails too: gzip, not BGZF). |
| samtools dict | 1.24 | `samtools dict x.fa` | plain, BGZF | a | Sequence `@SQ` lines (name, length, M5) match the control. |
| bgzip -t | htslib 1.24 | `bgzip -t x.fa.gz` | BGZF | a | Checks the compression only; the converter's BGZF output is valid. |
| pysam.FastaFile | 0.24.0 | `FastaFile(x).fetch()` | plain, BGZF | **c** | Calls htslib faidx: `OSError` with the same `;` error. |
| pysam.FastxFile | 0.24.0 | iterate records | plain, gzip, BGZF, CRLF, edge | a | kseq parser skips lines before the first `>`. |
| seqkit stats | 2.14.0 | `seqkit stats -T -a` | plain, gzip | **c (exit 0)** | `[ERRO] fastx: invalid FASTA/Q format`; prints only the column header but exits 0. |
| seqkit seq / grep | 2.14.0 | `seqkit seq`, `seqkit grep -p chr2` | plain, gzip, edge | **c** | Exit 255, `invalid FASTA/Q format`. |
| seqkit faidx | 2.14.0 | `seqkit faidx x.fa chr2:1-60` | plain | **c** | `invalid fasta file`. BGZF is n/a (seqkit faidx does not support gzip). |
| seqtk seq / comp | 1.5-r133 | `seqtk seq -l 60`, `seqtk comp` | plain, gzip, CRLF, edge | a | kseq. |
| bioawk | 1.0 | `bioawk -c fastx` | plain, gzip, edge | a | kseq. |
| pyfaidx | 0.9.0.4 | `Fasta(x)` | plain | **c** | `FastaIndexingError: Line length of fasta file is not consistent! ... >None at line 2`. |
| pyfaidx | 0.9.0.4 | `Fasta(x)` | edge (one `;` line) | **b** | Builds a record named `None` whose sequence is the comment text, plus the three real records. See [Silent corruption](#silent-corruption). |
| Biopython `SeqIO` `fasta` | 1.88 | `SeqIO.parse(x, "fasta")` | plain, CRLF, edge | **c** | `ValueError: This FASTA file contains comments at the beginning of the file...`; the message suggests `fasta-pearson`. |
| Biopython `fasta-pearson` | 1.88 | `SeqIO.parse(x, "fasta-pearson")` | plain | a | Skips leading lines. |
| Biopython `fasta-2line` | 1.88 | `SeqIO.parse(x, "fasta-2line")` | unwrapped | **c** | `Expected FASTA record starting with '>'`. |
| BWA | 0.7.19-r1273 | `bwa index`; `bwa mem` | plain, gzip, edge | a | `@SQ` lines and every alignment (name, contig, position, CIGAR) match the control. |
| minimap2 | 2.31-r1302 | `minimap2 -d`; `minimap2 -a` | plain, gzip, edge | a | Same comparison as BWA. |
| bowtie2-build | 2.5.5 | `bowtie2-build x.fa idx` | plain, edge | **c** | `Reference file does not seem to be a FASTA file`. On edge: `Encountered empty reference sequence`, then exit 1. |
| hisat2-build | 2.2.3 | `hisat2-build x.fa idx` | plain | **c** | Same message as bowtie2. |
| STAR | 2.7.11b | `--runMode genomeGenerate` | plain | **c** | `the first character is ';' (59), not '>'`. |
| salmon | 2.8.0 | `salmon index -t x.fa` | plain | **c** | `index build failed`. |
| kallisto | 0.52.0 | `kallisto index`; `inspect` | plain, edge | a | Target, k-mer and unitig counts match. |
| makeblastdb | BLAST 2.17.0+ | `makeblastdb -parse_seqids`; `blastdbcmd -entry all` | plain, edge | a | Records extracted from the database match the control. |
| bedtools getfasta | 2.31.1 | `bedtools getfasta -fi x.fa -bed r.bed` | plain, BGZF, edge | **c** | htslib faidx error; exit 1. |
| Picard CreateSequenceDictionary | 3.5.0 (htsjdk) | `-R x.fa -O x.dict` | plain, edge | **c** | `SAMException: ... Expected > but saw chr(59)`. Leaves a partial `x.dict` containing only `@HD VN:1.6`. |
| UCSC faToTwoBit / faSize | 482 | `faToTwoBit`, `faSize -detailed` | plain | **c** | `Expecting '>' line 1`. |
| pyfastx | 2.3.1 | `pyfastx.Fasta(x)` | plain, gzip | **c** | `not plain or gzip compressed fasta formatted file`. |
| MAFFT | 7.526 | `mafft --auto` | plain, edge | a | Same alignment as the control. |
| gffread `-g` | 0.12.9 | `gffread genes.gff3 -g x.fa -x cds.fa` | plain | **c** | `sequence lines in a FASTA record must have the same length!` |
| AGAT (BioPerl `Bio::DB::Fasta`) | 1.7.0 | `agat_sp_extract_sequences.pl -f x.fa` | plain | **c** | `Each line of the fasta entry must be the same length ... ';~taxon:'`. |
| JBrowse CLI `add-assembly` | 4.3.0 | `jbrowse add-assembly x.fa` | plain | **c** | Needs a `.fai`, which samtools cannot build for this file. |
| Bioconductor Biostrings | 2.80.2 | `readDNAStringSet(x)` | plain | a | Added 2026-10-18. Same names and sequences as the control. Biostrings skips leading `;` lines but rejects `#` or unmarked lines (`">" expected at beginning of line 1`). |
| scikit-bio | 0.7.4 | `skbio.io.read(x, format="fasta")` | plain | **c** | Added 2026-10-18. `FASTAFormatError: Found non-header line when attempting to read the 1st record`. |
| noodles-fasta (Rust) | 0.68.0 | `noodles_fasta::io::Reader::records()` | plain | **c** | Added 2026-10-18. `invalid prefix`. |
| rust-bio (Rust) | 4.2.2 | `bio::io::fasta::Reader::records()` | plain | **c** | Added 2026-10-18. `Expected > at record start.` |
| BioJulia FASTX.jl | 2.2.0 (Julia 1.11.7) | `FASTAReader` | plain | **c** | Added 2026-10-18. `Error when parsing FASTX file. Saw unexpected byte ';' on line 1`. |
| HMMER/Easel `esl-reformat` | HMMER 3.4 | `esl-reformat fasta x.fa` | plain | **c** | Added 2026-10-18. `Parse failed (sequence file x.fa)`. |
| EMBOSS `seqret` | 6.6.0 | `seqret -sequence x.fa -auto` | plain | **c** | Added 2026-10-18. `Unable to read sequence`. With `#` lines instead it is **b**: EMBOSS detects GDE format and writes one sequence made of header text and all records. |
| MMseqs2 `createdb` | 18.8cc5c | `createdb`, then `convert2fasta` | plain | a | Added 2026-10-18. Same sequences as the control. |
| DIAMOND `makedb` | 2.2.8 | `makedb`, then `getseq` (protein) | plain | **c** | Added 2026-10-18. `First line must begin with '>' (FASTA) or '@' (FASTQ)`. |
| CD-HIT `cd-hit-est` | 4.8.1 | `cd-hit-est -c 1.0` | plain | a | Added 2026-10-18. Same representative sequences as the control. |
| Clustal Omega | 1.2.4 | `clustalo -i x.fa` | plain | **c** | Added 2026-10-18. `Can't determine format of sequence file`. |
| MUSCLE `-align` | 5.3 | `muscle -align x.fa` | plain | **c** | Added 2026-10-18. `Expected '>' in FASTA, got ';~schema: ...'`. |
| IQ-TREE | 3.1.4 | `iqtree3 -s x.aln.fa` (DNA alignment) | plain | **c** | Added 2026-10-18. `Unknown sequence format`. With `#` lines it tries NEXUS: `Expecting #NEXUS to be the first token`. |

bcftools (for example `bcftools norm -f`), GATK and other htslib/htsjdk
reference consumers were not run separately. They load references through the
same faidx/htsjdk code, so they inherit the **c** result above.

## GFA

| Tool | Version | Command | Class | Header kept | Notes |
| --- | --- | --- | --- | --- | --- |
| gfatools stat | 0.4-r214 (bioconda gfatools 0.5.5) | `gfatools stat` | a | n/a | |
| gfatools gfa2fa | same | `gfatools gfa2fa` | a | no | |
| gfatools view | same | `gfatools view` | a | no | `#` lines dropped. |
| vg | 1.76.1 | `vg convert -g x.gfa -f`; `vg stats -lz` | a | no | Warns `[GFAParser] Ignoring unrecognized # line type`. |
| odgi | 0.9.4 | `odgi build -g`; `stats -S`; `view -g` | a | no | Numeric-ID copy. odgi rejects non-numeric segment names whether or not there is a header. |
| gfapy | 1.2.3 | `Gfa.from_file`; `to_file` | a | yes (52) | Comments are kept and written back. |

No GFA tool tested misreads `#~` lines: `#` comments are part of GFA1.

## GFF3

Each row covers three inputs: header before `##sequence-region`, header after
`##sequence-region`, and a file with a `##FASTA` section. Results did not
differ between the first two.

| Tool | Version | Command | Class | Header kept | Notes |
| --- | --- | --- | --- | --- | --- |
| GenomeTools `gt gff3validator` | 1.6.5 | `gt gff3validator` | a | n/a | `input is valid GFF3` for all three. |
| GenomeTools `gt gff3` | 1.6.5 | `gt gff3 -sort -tidy -retainids` | a | yes (25) | Moves `##sequence-region` lines above the `#~` block. |
| gffread | 0.12.9 | `-T`; `-E -o`; `-g genome.fa -x` | a | no | Writes its own `# gffread` comment lines instead. |
| AGAT | 1.7.0 | `agat_convert_sp_gxf2gxf.pl`; `agat_sp_statistics.pl` | a | yes (25) | Header kept in place (after `##gff-version 3`); statistics identical. |
| gffutils | 0.14 | `create_db(..., merge_strategy="create_unique")` | a | n/a | Features and `directives` identical; `#~` lines are not stored. |
| bedtools | 2.31.1 | `sort -header`; `intersect` | a | `sort -header`: yes | The `##FASTA` variant is n/a (bedtools reads the FASTA lines as features). |
| bgzip + tabix | htslib 1.24 | sort, `bgzip`, `tabix -p gff`, region query | a | `tabix -H`: yes | Header lines must stay at the top when sorting (`grep '^#'` first). `##FASTA` is n/a (tabix cannot parse it). |
| htseq-count | HTSeq 2.1.2 | `-f bam -t exon -i Parent` | a | n/a | `##FASTA` is n/a (HTSeq rejects it in the control too). |
| featureCounts | subread 2.1.1 | `-F GTF -t exon -g Parent` | a | n/a | |
| JBrowse CLI | 4.3.0 | `add-track`; `text-index` | a | n/a | Trix index byte-identical to the control. |
| `@gmod/gff` (JBrowse 2 parser) | 2.1.0 | `parseStringSync` | a | as comments | `#~` lines come back as comment items; features, directives and sequences match. |

## Concatenated files (invalid under R10)

`cat a.fhr.fa b.fhr.fa` and `cat a.fa b.fhr.fa` leave `;~` lines after the last
record of the first file. R10 makes such a file invalid, and
`fhr-fasta-validate` rejects it. Concatenating FASTA files is routine, though,
so the survey also ran the FASTA tools on these files.

| Tool | `cat fhr + fhr` | `cat plain + fhr` | Effect when it "works" |
| --- | --- | --- | --- |
| samtools dict | **b** | **b** | chrM length 1200 → 2613 and a different M5: the header text is counted as chrM sequence. |
| pysam.FastxFile, seqtk seq/comp, bioawk | **b** | **b** | chrM 1200 → 2719. |
| minimap2 (`-d`, `-a`) | **b** | **b** | `@SQ SN:chrM LN:2719` in the index and the SAM header. |
| kallisto index | **b** | **b** | k-mers 9,880 → 11,367 (the header is indexed as target sequence). |
| seqkit stats/seq/grep | c | **b** | Rejects a leading `;` but absorbs later `;` lines into chrM. |
| Biopython `fasta` | c | **b** | chrM 1200 → 2613. |
| bowtie2-build, hisat2-build | c | **b** | chrM 1886 in the index. |
| STAR, salmon | c | **b** | STAR `chrNameLength` chrM 2719; salmon offsets show chrM 2687. |
| Picard CreateSequenceDictionary | c | **b** | chrM 2719 with a different M5. |
| UCSC faToTwoBit, faSize | c | **b** | chrM 2279 (non-letters dropped). |
| pyfastx | c | **b** | chrM 2714. |
| BWA | c | c | `bwa index` exits 0, but `bwa mem` then fails: `[bns_restore_core] Parse error reading .amb`. |
| samtools faidx, bedtools getfasta, pysam.FastaFile | c | c | Fails here only because the header lines differ in width from chrM's lines (`Different line length in sequence 'chrM'`). With equal widths faidx indexes the text: `printf '>a\nACGT\n;mid\n>b\nGG\n'` gives `a` length 8, sequence `ACGT;mid`. |
| pyfaidx, MAFFT, gffread, AGAT/BioPerl, seqkit faidx, JBrowse | c | c | |
| makeblastdb, Biopython `fasta-pearson` | a | a | Skip `;` lines anywhere. |

## Silent corruption

**Valid FHR files.** In the FASTA, GFA and GFF3 surveys above, no tool silently
changed sequence data, names or features. Every class **a** result had a
fingerprint identical to its control. This covers BWA, minimap2, kallisto,
makeblastdb, MAFFT, seqtk, bioawk, pysam.FastxFile, Biopython `fasta-pearson`,
and all GFA and GFF3 tools.

The later [annotation and assembly survey](#annotation-and-assembly-tools) found
two silent misreads of valid files, both in the tools' own FASTA parsers: QUAST
counts the header as an extra contig in its threshold rows (ablab/quast#300), and
TransDecoder 6.0.0 predicts ORFs on the header text (fixed on master,
TransDecoder/TransDecoder#213). See [Upstream support](#upstream-support).
The [2026-10-22 survey](#more-tools-2026-10-22) found a third: JBrowse 2's unindexed FASTA
adapter (`UnindexedFastaAdapter`, the `parseSmallFasta()` code of `@gmod/indexedfasta`) shows
the header as an extra reference sequence named `;~schema:`.

**Concatenated files (above).** These are the main corruption risk. Most
tools that accept a leading header silently append a later header to the
previous record's sequence. That changes its length, its MD5 and SeqCol
digests, any `.dict`, and the aligner indexes. The tools that reject a leading
header (STAR, Picard, UCSC, seqkit, bowtie2, salmon) do the same with a header
that follows a record. The FHR rules already forbid this. Strip each FHR file
before concatenating it with others, and run `fhr-fasta-validate` on inputs.

**One leading comment line (pyfaidx).** With exactly one leading `;` line, or
several of equal width, pyfaidx indexes the comment as an unnamed sequence:

```text
$ printf ';~ab: 1\n;~cd: 2\n>chr1\nACGTACGT\nACGT\n' > eq.fa
$ python -c 'import pyfaidx; f=pyfaidx.Fasta("eq.fa"); print({k: str(f[k][:]) for k in f.keys()})'
{'None': ';~ab: 1;~cd: 2', 'chr1': 'ACGTACGTACGT'}
$ cat eq.fa.fai
None	14	0	7	8
chr1	12	22	8	9
```

Real FHR headers have lines of different widths, so pyfaidx fails with an
error instead. The edge case still affects files with legacy `;` comments.

Related, smaller risks:

- **Errors with exit 0.** `seqkit stats` reports `invalid FASTA/Q format` but
  exits 0 and prints an empty table, so a pipeline does not stop. Likewise,
  `bwa index` succeeds on a concatenated file and the failure appears only at
  `bwa mem`.
- **Partial output.** Picard leaves a `.dict` file holding only `@HD`, which a
  make-style workflow may treat as up to date.
- **Stale headers in derived files.** `gt gff3`, AGAT, `bedtools sort -header`,
  tabix and gfapy copy `#~` lines into files whose bytes have changed. The
  copied `checksum` then no longer matches the file. FHR validation catches
  this; anything that reads the header without validating it does not. `gt`
  also reorders `##sequence-region` lines above the header block (relevant to
  the open placement question in spec 007 FR-001).

## Summary of risks

1. **FASTA indexing is the main gap for valid files.** htslib faidx rejects the
   file, and so does everything built on it: samtools faidx, pysam.FastaFile,
   bedtools getfasta, JBrowse assemblies, Ensembl VEP (which then crashes in
   `Bio::DB::HTS`), and bcftools/GATK-style reference loading. A `.fai` that
   skips the header, as pyfaidx 0.9.1 writes it, lets the region readers work.
   htsjdk (Picard), pyfaidx, seqkit, pyfastx, UCSC tools, gffread, BioPerl
   `Bio::DB::Fasta`, the Burrows-Wheeler builders (bowtie2, HISAT2), STAR,
   salmon and Bakta (Biopython `fasta`) all reject it too. All of these fail
   loudly.
2. **kseq-based tools work.** BWA, BWA-MEM2, minimap2, seqtk, bioawk,
   pysam.FastxFile and kallisto, plus makeblastdb, MAFFT, Kraken2, R's seqinr and
   ape, Biostrings and Biopython `fasta-pearson`, ignore the leading `;` block.
3. **Concatenation corrupts data silently.** A header after the first record
   is read as sequence by most tools, including samtools dict, minimap2,
   STAR, salmon, kallisto and Picard. R10 forbids this layout; validation
   and stripping before `cat` avoid it.
4. **GFA and GFF3 headers are compatible** with every tool tested. GFF3 tools
   either drop `#~` comments or keep them (some reordered). Failures seen with
   `##FASTA` sections come from the `##FASTA` section, not from the header.
5. **Some annotation tools misread valid files silently.** QUAST and
   TransDecoder 6.0.0 read the header as sequence (see
   [Annotation and assembly tools](#annotation-and-assembly-tools)), and so does
   JBrowse 2's unindexed FASTA adapter ([More tools](#more-tools-2026-10-22)).

## Recommended workarounds

Strip the header for FASTA tools in class **c**. With the converter (0.3.3),
the output keeps every other byte; a `.gz` output name gives BGZF, which faidx
can index:

```bash
fhr-fasta-strip genome.fhr.fa.gz genome.fa.gz   # BGZF output
samtools faidx genome.fa.gz                      # verified: index and fetch work
fhr-fasta-strip genome.fhr.fa genome.fa          # uncompressed
fhr-fasta-strip genome.fhr.fa - | seqkit stats - # streaming
```

Without the converter, drop every line that starts with `;`. R10 allows FHR
lines only before the first record, and samtools rejects any `;` line anyway:

```bash
sed '/^;/d' genome.fhr.fa > genome.fa
zcat genome.fhr.fa.gz | sed '/^;/d' | bgzip > genome.fa.gz
```

Keep the FHR file as the archival copy; the stripped copy is derived. The FHR
metadata can be kept beside it as JSON/YAML with `fhr-convert`.

- **Biopython**: use `SeqIO.parse(path, "fasta-pearson")`. Avoid `fasta-blast` in
  Biopython 1.85 to 1.88: it gives every record the first record's ID
  (biopython/biopython#5377).
- **GFA**: no action needed. `fhr-gfa-strip` or `grep -v '^#~'` gives the
  original bytes back.
- **GFF3**: no action needed. To remove the header use `grep -v '^#~' x.gff3`
  (verified byte-identical to the control). Re-run FHR combine on derived files
  instead of keeping the copied header.
- **tabix**: when sorting, keep all `#` lines on top:
  `(grep '^#' x.gff3; grep -v '^#' x.gff3 | sort -k1,1 -k4,4n) | bgzip > x.gff3.gz`.

To combine FASTA files, strip each FHR file first:

```bash
for f in *.fhr.fa; do fhr-fasta-strip "$f" -; done > combined.fa
```

Then add a new header to the result with `fhr-fasta-combine` if needed.

Native support in htslib would remove most FASTA stripping. The proposal
([proposals/htslib-fasta-comments.md](proposals/htslib-fasta-comments.md),
samtools/htslib#2103 and #2106) was declined on 2026-10-15, so stripping
remains the route for faidx-based tools. See [Upstream support](#upstream-support).

For region reads there is a second route (checked 2026-10-22): htslib uses an existing `.fai`
rather than rebuilding it, and pyfaidx 0.9.1 writes a `.fai` that skips the header. With that
index, `samtools faidx x.fa chr:start-end`, Ensembl VEP `--fasta` and JBrowse `add-assembly`
read the FHR file unchanged ([More tools](#more-tools-2026-10-22)). Commands that build the
index themselves, such as `samtools faidx x.fa` without a region, still fail.

```bash
python -c 'import pyfaidx; pyfaidx.Fasta("genome.fhr.fa")'   # writes genome.fhr.fa.fai
samtools faidx genome.fhr.fa chr1:1000-2000                  # uses that .fai
```

Stripping a header removes its metadata from the working copy. For files that
cannot carry an FHR header, or tools that need a stripped copy, the
[FAIR header guideline](FAIR_HEADER_GUIDELINE.md) shows how to keep the same
metadata in each format's native header lines (GFF3 `##`/`#!`, VCF `##`,
GAF `!`). `bioheaders assess` reports what a header already provides; its shared
fixtures are in [assessment/](../assessment/README.md).

## Annotation and assembly tools

On 2026-10-19 the survey was extended to tools that consume a genome FASTA in assembly
QC and annotation work. Each was run on the same three-chromosome control genome and on the
FHR file written by fair-bioheaders 0.8.0, whose header follows rule R11 (no raw `>` or `@`).
As in [Comment markers](#comment-markers---or-none), each was also run with the header lines
marked `#` and unmarked, and once more with a header value containing a raw `@` and `>`
(`contact someone@example.org; contigs > 1000 bp`, as a pre-R11 writer would leave it).
Versions are pinned in `scripts/tool_survey/environment-annotation.yml`; results are in
`scripts/tool_survey/results/results-annotation.tsv`.

| Tool | Version | Operation | `;` (R11) | `#` | unmarked | raw `@`/`>` | Cause and notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QUAST | 5.3.0 | `quast.py` report | **b** | **b** | **b** | **b** | Silent misread: 4 contigs and 10705 bp instead of 3 and 9200; the header becomes an unnamed contig. QUAST's own `quast_libs/fastaparser.py` (`get_chr_lengths_from_fastafile`, `create_fai_file`) counts lines before the first `>` |
| AUGUSTUS | 3.5.0 | `augustus --species=human` | **c** | **c** | **c** | **c** | `GBProcessor::determineFileType(): Couldn't determine input file type. Found bad character ':'`. AUGUSTUS's own format detection A comment line without punctuation (e.g. `;comment`) is instead read silently as an extra `unnamed-1` sequence (found 2026-10-22). |
| Liftoff (FHR genome as target or reference) | 1.6.3 | `liftoff -g genes.gff3` | **c** | **c** | **c** | **c** | `pyfaidx.FastaIndexingError: … Inconsistent line found in >None` (pyfaidx 0.9.0.4) With pyfaidx 0.9.1 (released 2026-10-19) both directions work (class **a**, checked 2026-10-20). |
| gffcompare | 0.12.10 | `gffcompare -r … -s genome.fa` | **c** | **c** | **c** | **c** | `sequence lines in a FASTA record must have the same length!` (gclib `GFastaIndex`, as gffread) |
| Mash | 2.3 | `mash sketch -i`, `mash info` | a | a | a | **b** | With a raw `@` it reads a 572 bp record named `example.org;` (kseq-style scan) |
| sourmash | 4.9.4 | `sourmash sketch dna --singleton` | **c** | **c** | **c** | **c** | `unknown file format` from screed 1.2.0, which decides the format from the first byte |
| seqfu | 1.30.3 | `seqfu cat` | a | a | a | **c (exit 0)** | With a raw `@` it writes nothing and exits 0 |
| TransDecoder | 6.0.0 | `TransDecoder.LongOrfs` | **b** | **b** | **b** | **b** | Silent misread: five ORFs predicted on a sequence named `;~schema:` made of header text. `PerlLib/Fasta_reader.pm` (also shipped with Trinity) treats the header block as a record |
| Prokka | 1.15.6 | `prokka --noanno --fast` | **c** | **c** | **c** | **c** | BioPerl 1.7.8 `Bio::SeqIO::fasta::next_seq` exception |
| BUSCO | 6.1.0 | genome mode, `bacteria_odb12` | **c** | **c** | **c** | **c** | Biopython `SeqIO` `fasta`: `This FASTA file contains comments at the beginning of the file` |
| compleasm | 0.2.10 | `compleasm run -l bacteria` | a | a | a | a | The genome goes to miniprot. The random test genome has no marker hits, so this shows only that the file is read without error |
| RepeatModeler | 2.0.9 | `BuildDatabase` | a | a | **c** | a | Accepts `;` and `#` lines; rejects unmarked text |
| RepeatMasker | 4.1.2.p1 | `RepeatMasker -lib` (custom library) | a | a | a | a | Same masking as the control, with one `FastaDB` warning per header line ("unrecognized format … is being ignored"). 4.2.4 was not run: it needs a Dfam FamDB download even with `-lib` |
| meryl (Merqury's assembly k-mers) | 1.4.2 | `meryl count k=21` | **c** | **c** | **c** | **c** | Segmentation fault |
| Merqury | 1.4.1 | `merqury.sh` | **c (exit 0)** | **c (exit 0)** | **c (exit 0)** | **c (exit 0)** | Exits 0 but writes no QV or completeness: the meryl crash inside `spectra-cn.sh` is not reported |

Not tested: BRAKER (needs GeneMark and a licence key) and Trinity's genome-guided mode (heavy);
Trinity's Perl utilities share TransDecoder's `Fasta_reader.pm`. Bakta and Kraken2 (large
databases) were tested later with a stub or tiny database; see
[More tools (2026-10-22)](#more-tools-2026-10-22).

Failures fixed by upstream changes: Liftoff (pyfaidx v0.9.1, mdshw5/pyfaidx#244, released
2026-10-19 and verified 2026-10-20) and, once released, Prokka (the next BioPerl release, bioperl/bioperl-live#410). gffcompare
would be fixed by gpertea/gclib#15, which is open. The raw-`@`/`>` failures of Mash and seqfu do
not occur with R11 headers (fair-bioheaders 0.8.0 and later). The remaining failures (QUAST,
TransDecoder, AUGUSTUS, sourmash/screed, BUSCO, meryl/Merqury) are in the tools' own parsers and
are tracked in FAIR-bioHeaders-Specification#121 (BUSCO, QUAST, TransDecoder, meryl/Merqury,
screed/sourmash and AUGUSTUS have been contacted; see [Upstream support](#upstream-support)).

## More tools (2026-10-22)

On 2026-10-22 ten more tools were run on a real genome, *Mycoplasmoides genitalium* G37
(NC_000908.2, one 580,076 bp record): the R and Bioconductor FASTA readers, JBrowse 2's FASTA
code, Bakta, Kraken2, BWA-MEM2 and Ensembl VEP. The FHR file was written by
fair-bioheaders 0.8.1 (`bioheaders combine` with FAIR-bioHeaders-Tools
`examples/example.fhr.yaml`; 53 `;~` lines, R11-escaped). Each tool also read the control with a
single `;comment` line, the header marked `#` or unmarked, the header with a raw `@`/`>` value
(as in [Annotation and assembly tools](#annotation-and-assembly-tools)), and gzip or BGZF copies
where the tool reads them. Outputs were fingerprinted as above (record names, lengths and MD5s;
SAM alignments; Kraken2 classifications and `hash.k2d`; VEP consequences and HGVS). Versions are
in `scripts/tool_survey/environment-round4.yml`, inputs and runner in `scripts/tool_survey/round4/`,
and results in `scripts/tool_survey/results/results-round4.tsv`.

| Tool | Version | Operation | `;` (R11) | one `;` line | `#` | unmarked | raw `@`/`>` | gzip / BGZF | Cause and notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Biostrings | 2.80.2 (R 4.5.3) | `readDNAStringSet()`; `fasta.index()` then `readDNAStringSet()` | a | a | **c** | **c** | a | a (gzip) | Skips leading `;` lines only; `#` and unmarked lines give `">" expected at beginning of line 1`. The index offset points at the `>` line |
| seqinr | 4.2.44 | `read.fasta()` | a | a | a | a | a | a (gzip) | Skips everything before the first line that starts with `>` |
| ape | 5.8.1 | `read.FASTA()`, `read.dna(format = "fasta")` | a | a | a | a | **b** | a (gzip) | Starts a record at any `>` byte: a raw `>` gives an extra 253 bp record named `1000`. Not seen with R11 headers |
| JBrowse CLI `add-assembly` | 4.3.0 | `jbrowse add-assembly x.fa --load copy` | **c** | **c** | **c** | **c** | **c** | **c** (BGZF) | `Error: Could not resolve to a file or a URL: "x.fa.fai"`. The CLI builds no index; it needs a `.fai` (and `.gzi`) made beforehand, normally by `samtools faidx`, which rejects the file (htslib, samtools/htslib#2106, declined) |
| JBrowse CLI + `@gmod/indexedfasta` `IndexedFasta`, `BgzipIndexedFasta` | 4.3.0; 5.0.13 | `add-assembly` and region reads, with a `.fai` that skips the header | a | a | a | a | a | a (BGZF) | JBrowse's own indexed reader only follows the `.fai` offsets. With a header-aware `.fai` (pyfaidx 0.9.1 writes one) every variant matches the control |
| `@gmod/indexedfasta` `FetchableSmallFasta` (the parser copied into JBrowse 2's `UnindexedFastaAdapter`) | 5.0.13; `@jbrowse/plugin-sequence` 4.3.0 | `getSequenceNames()`, `fetch()` | **b** | **b** | **b** | **b** | **b** | n/a | Silent misread: an extra reference sequence `;~schema:` of 1,344 bp made of header text. `parseSmallFasta()` splits the whole file on `>`, so text before the first `>` becomes a record (and a raw `>` inside a header line splits it again) |
| Bakta | 1.12.2 | `bakta` genome import | **c** | **c** | **c** | **c** | **c** | **c** (gzip) | `ERROR: wrong genome file format!` `bakta/io/fasta.py` `import_sequences()` uses Biopython `SeqIO.parse(fh, 'fasta')`, which raises `This FASTA file contains comments at the beginning of the file`; `fasta-pearson` would accept it |
| Kraken2 | 2.17.2 | `kraken2-build --add-to-library`, `--build`; `kraken2` on 50 reads | a | a | a | a | a | n/a | `scan_fasta_file.pl` reads taxids only from `>` lines, and the build counts 1 sequence of 580,076 bp; `hash.k2d` and every read classification match the control. `--add-to-library` does not read gzip (control too) |
| Kraken2 | 2.17.2 | `kraken2` with the genome FASTA as the query | a | a | a | a | **b** | a (gzip) | With a raw `@` it classifies an extra 600 bp sequence named `example.org;` (kseq-style scan). Not seen with R11 headers |
| BWA-MEM2 | 2.3 (binary reports 2.2.1) | `bwa-mem2 index`; `bwa-mem2 mem` on 50 reads | a | a | a | a | **c** | a (gzip) | Same as BWA 0.7.19, rerun alongside: `@SQ` and every alignment match. With a raw `@` the index gains a record `example.org;` and `mem` stops with `[bns_restore_core] Parse error reading x.fa.amb` |
| Ensembl VEP | 116.3 (Bio::DB::HTS 3.01, htslib 1.21) | `vep --gff genes.gff.gz --fasta x.fa` (no cache) | **c** | **c** | **c** | **c** | **c** | **c** (BGZF) | `[E::fai_build_core] Format error, unexpected ";" at line 1`, then a segmentation fault (exit 139). VEP loads FASTA through `Bio::DB::HTS::Faidx` (htslib faidx; BioPerl `Bio::DB::Fasta` only when that is missing). `Faidx.xs` does not check `fai_load()` for NULL, so any FASTA that htslib cannot index crashes Perl instead of raising an error. With a header-aware `.fai` VEP gives the control's consequences and HGVS |

**Where the JBrowse failure comes from.** The earlier JBrowse result (`add-assembly`, above) is
htslib's: the CLI only copies an existing `.fai`, and `samtools faidx` cannot make one. That is the
behaviour samtools/htslib#2106 proposed to change. JBrowse's indexed readers work once a `.fai`
exists. JBrowse's own bug is the unindexed path, which silently shows the header as an extra
sequence.

**A header-aware `.fai` unblocks htslib readers.** htslib uses an existing `.fai` instead of
rebuilding it. The `.fai` that pyfaidx 0.9.1 writes for an FHR file
(`python -c 'import pyfaidx; pyfaidx.Fasta("x.fa")'`) skips the header, and with it
`samtools faidx x.fa chr:1000-1010` (1.24), VEP and JBrowse give the same results as for the
control. `samtools faidx x.fa` without a region still tries to rebuild the index and fails.

Not tested: a full Bakta annotation. Its smallest database (db-light 6.0) is 1.34 GB compressed
but 3.8 GB unpacked, so Bakta was run with a stub database and every annotation step skipped.
That runs the genome import, which is where the file is rejected. VEP was run without a cache.
Kraken2 used a minimal custom taxonomy with one genome.

The failures in Bakta, the JBrowse unindexed adapter and `Bio::DB::HTS::Faidx` are in the
projects' own code and are listed as candidates in FAIR-bioHeaders-Specification#121 (none has been
contacted). The JBrowse `add-assembly` failure is htslib's.

## Comment markers: `;`, `#` or none

Is `;` the right marker, or would another convention be better supported? On
2026-10-15 the FASTA tests above were rerun three times on the same file, changing
only the lines before the first `>`: the FHR `;~` lines, the same lines starting
with `#~`, and the same lines with no marker. The tools were the versions listed
under [Environment](#environment). There were 29 tests across 22 tools;
UCSC faToTwoBit and the JBrowse CLI gave no result for any variant and are left
out. `scripts/tool_survey/make_marker_variants.py` writes the variants.

| Result | `;` | `#` | no marker |
| --- | --- | --- | --- |
| Works | 11 | 11 | 10 |
| Fails | 18 | 18 | 19 |

- `;` and `#` gave the same result in every test, with the same errors
  (htslib names the character: `unexpected ";"` or `unexpected "#"`).
- The tools that work ignore everything before the first `>`: `samtools dict`,
  pysam `FastxFile`, seqtk, BWA, minimap2, kallisto, bioawk, MAFFT and Biopython
  `fasta-pearson`. None of them copies the header lines into its output, and all
  of them also accept the unmarked lines.
- BLAST's `makeblastdb` is the one tool that recognises comment markers. It
  accepts `;` and `#` lines, but for the unmarked file it warns that the input
  "does NOT appear to be FASTA" and creates no database.
- The tools that fail, fail on all three variants. Some reject any first line
  that is not `>` (samtools faidx, UCSC faSize, Bowtie2); others read the leading
  lines as sequence and then fail on inconsistent line lengths (gffread,
  pyfaidx, AGAT/BioPerl).

On 2026-10-18 the same comparison was run for the 13 parsers added to the FASTA table
(versions in `scripts/tool_survey/environment-extra.yml`; 13 tests across 13 tools,
results in `scripts/tool_survey/results/results-extra.tsv`):

| Result (2026-10-18 additions) | `;` | `#` | no marker |
| --- | --- | --- | --- |
| Works | 3 | 2 | 2 |
| Misreads (silent) | 0 | 1 | 0 |
| Fails | 10 | 10 | 11 |

- Bioconductor Biostrings accepts the `;` lines and rejects `#` and unmarked lines, so
  it implements the Pearson comment form.
- `#` is already meaningful to some formats: EMBOSS detects GDE and silently merges the
  header and every record into one sequence, and IQ-TREE expects NEXUS.
- MMseqs2 and CD-HIT skip anything before the first `>`.

The [2026-10-22 tools](#more-tools-2026-10-22) give the same picture (13 tests across 10 tools,
counting the plain-file runs and leaving out the two header-aware `.fai` runs):

| Result (2026-10-22 additions) | `;` | `#` | no marker |
| --- | --- | --- | --- |
| Works | 9 | 7 | 7 |
| Misreads (silent) | 1 | 1 | 1 |
| Fails | 3 | 5 | 5 |

- Biostrings again accepts `;` and rejects `#` and unmarked lines, in both
  `readDNAStringSet()` and `fasta.index()`.
- seqinr, ape, Kraken2 and BWA-MEM2 skip anything before the first `>`.
- The JBrowse unindexed parser misreads all three variants; JBrowse `add-assembly`
  (htslib), Bakta (Biopython) and VEP (htslib) reject all three.

So no competing marker would gain support: most tools are either lenient about text
before the first record or strict, and the two that tell marked lines apart
(makeblastdb and Biostrings) accept `;`. `;` keeps the advantage of being the
documented FASTA comment form (Pearson and Lipman), it is the form Biostrings
recognises, and unlike `#` it does not collide with GDE or NEXUS.

## Upstream support

This is the inventory of tool support for FAIR-bioHeaders headers. It records which tools work
with FHR headers as released and the changes proposed upstream so that the others do. Live status
is tracked in [#121](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/121).

### Tools that work today

These read FHR-headed files with results identical to the control file in the survey above. Biopython's
`fasta-blast` also skips the header, but in 1.85 to 1.88 it gives every record the first record's ID
(biopython/biopython#5377), so it is not listed.

**Caveat for kseq-based readers.** kseq starts a record at the first `>` or `@` character
anywhere, not only at the start of a line. If an FHR header line contains a raw `>` or `@`
(an email address, `length > 1000`), seqtk, bioawk and `samtools dict` read a bogus extra
record (checked 2026-10-18: `;~metadataAuthor: someone@example.org` gives a 0-length record
named `example.org`). BWA, minimap2 and pysam `FastxFile` use the same parser, and
BWA-MEM2, Kraken2 classification and R's ape (which starts a record at any `>`) behave the
same way (checked 2026-10-22). Rule R11 of
[FORMAT.md](FORMAT.md) therefore asks FASTA header writers to escape these characters in
double-quoted YAML (`\x40`, `\x3E`), which reads back as the same metadata; the toolkit's
`combine` does this from the release after 0.7.0, and `verify` warns on a raw `>` or `@`
(FAIR-bioHeaders-Specification#127).

| Format | Tools (surveyed version) |
| --- | --- |
| FASTA | BWA 0.7.19 (`index`, `mem`); minimap2 2.31; seqtk 1.5 (`seq`, `comp`); bioawk 1.0; kallisto 0.52.0; MAFFT 7.526; makeblastdb 2.17.0+; samtools 1.24 `dict`; pysam 0.24.0 `FastxFile`; Biopython 1.88 `SeqIO` format `fasta-pearson`; Bioconductor Biostrings 2.80.2 `readDNAStringSet`; MMseqs2 18.8cc5c `createdb`; CD-HIT 4.8.1 `cd-hit-est`; Mash 2.3 `sketch`; seqfu 1.30.3 `cat`; compleasm 0.2.10; RepeatModeler 2.0.9 `BuildDatabase`; RepeatMasker 4.1.2.p1 (with warnings); pyfaidx 0.9.1; Liftoff 1.6.3 (with pyfaidx 0.9.1 or later); Biostrings 2.80.2 `fasta.index`; seqinr 4.2.44 `read.fasta`; ape 5.8.1 `read.FASTA`, `read.dna`; BWA-MEM2 2.3 (`index`, `mem`); Kraken2 2.17.2 (`kraken2-build --add-to-library`, `--build`, `kraken2`); JBrowse CLI 4.3.0 `add-assembly`, `@gmod/indexedfasta` 5.0.13 `IndexedFasta` and Ensembl VEP 116.3 `--fasta` (each with a `.fai` written by pyfaidx 0.9.1) |
| GFA | gfatools 0.4 (`view`, `stat`, `gfa2fa`); gfapy 1.2.3; odgi 0.9.4 (`build`, `stats`, `view`); vg 1.76.1 (`stats`, `convert`) |
| GFF3 | GenomeTools 1.6.5 (`gt gff3 -sort -tidy`, `gt gff3validator`); AGAT 1.7.0 GFF3 tools; gffread 0.12.9 (`-E`, `-T`, `-g -x`); gffutils 0.14; featureCounts 2.1.1; HTSeq 2.1.2 `htseq-count`; bedtools 2.31.1 (`intersect`, `sort`); bgzip and tabix 1.24; `@gmod/gff` 2.1.0; JBrowse CLI 4.3.0 (`add-track`, `text-index`) |

### FASTA tools: changes proposed upstream

Status as of 2026-10-21; FAIR-bioHeaders-Specification#121 is the live tracker.

Each proposal asks for the same narrow rule: skip lines starting with `;` **before the first `>`**,
the original Pearson FASTA comment form and FHR rule R10. A `;` line anywhere else keeps its
current meaning, so no file that a tool reads today is read differently.

| Project | Affected tools | Proposal (2026-10-14 unless dated) | Status |
| --- | --- | --- | --- |
| samtools/htslib | samtools faidx, pysam `FastaFile`, bedtools getfasta, JBrowse `add-assembly` (needs a `.fai`) | Issue samtools/htslib#2103; PR samtools/htslib#2106 | Declined 2026-10-15: "the de facto standard is not to use semicolons for comments", unless there is general consensus |
| mdshw5/pyfaidx | pyfaidx (silently created a `None` record) | mdshw5/pyfaidx#244 | **Released in pyfaidx v0.9.1 (2026-10-19)**; also fixes the silent `None` record. Verified 2026-10-20 |
| samtools/htsjdk | Picard CreateSequenceDictionary, GATK | samtools/htsjdk#1922 | **Merged 2026-10-19** (samtools/htsjdk#1922); reaches Picard and GATK with the next htsjdk release |
| shenwei356/bio | seqkit `stats`, `seq`, `grep`, `faidx` | shenwei356/bio#12 | **Merged 2026-10-18**; reaches seqkit users in the next SeqKit release, documented as discarding leading comments |
| biopython/biopython | `SeqIO` `fasta` (`fasta-pearson` already works) | Discussion issue biopython/biopython#5375 | **Supported without changes** through `SeqIO.parse(handle, "fasta-pearson")`. The default `fasta` reader is unchanged (2026-10-16), so tools built on it, such as BUSCO, are approached individually. Avoid `fasta-blast` in 1.85 to 1.88 (biopython/biopython#5377) |
| lmdu/pyfastx | pyfastx | lmdu/pyfastx#99 | Open |
| ucscGenomeBrowser/kent | faToTwoBit, faSize | ucscGenomeBrowser/kent#105 | Declined 2026-10-19: UCSC's FASTA parsing serves its own pipelines and NCBI input |
| gpertea/gclib | gffread `-g` | gpertea/gclib#15 | Open |
| bioperl/bioperl-live | `Bio::DB::Fasta`, AGAT genome input | bioperl/bioperl-live#410 | **Merged 2026-10-19** (`Bio::DB::Fasta` and `Bio::SeqIO::fasta`); reaches AGAT users with the next BioPerl release (the last CPAN release is 1.7.8, 2021) |
| BenLangmead/bowtie2 | bowtie2-build | BenLangmead/bowtie2#534 | Open |
| DaehwanKimLab/hisat2 | hisat2-build | DaehwanKimLab/hisat2#476 | Open |
| alexdobin/STAR | STAR `genomeGenerate` | Feature request alexdobin/STAR#2709, with a suggested patch | Open |
| onecodex/needletail | salmon `index` (through piscem-rs), other needletail users | onecodex/needletail#122; salmon then needs a dependency update | Open. The maintainer prefers skipping all text before the first record (the kseq behaviour) to partial Pearson comment support; we offered to rework the PR |
| scikit-bio/scikit-bio | `skbio.io.read(format="fasta")` | Issue scikit-bio/scikit-bio#2644 (2026-10-18; their guide asks for an issue first) | Maybe (2026-10-20): the maintainer will leave the parser as is while watching consensus; an explicit opt-in would avoid changing the format sniffer |
| zaeleus/noodles | noodles-fasta reader, async reader and indexer | zaeleus/noodles#439 (2026-10-18) | Declined 2026-10-19 |
| rust-bio/rust-bio | `bio::io::fasta::Reader` | rust-bio/rust-bio#722 (2026-10-18) | Open |
| BioJulia/FASTX.jl | `FASTA.Reader`, `validate_fasta`, `faidx` | BioJulia/FASTX.jl#132 (2026-10-18) | Open |
| EddyRivasLab/easel | HMMER and the Easel miniapps | EddyRivasLab/easel#84 (2026-10-18) | Open |
| bbuchfink/diamond | `diamond makedb` and other FASTA input | Issue bbuchfink/diamond#992 (2026-10-18; asked before a PR, since its readers seek by byte offset) | **Accepted 2026-10-19**: to be included in the next DIAMOND release |
| iqtree/iqtree3 | IQ-TREE FASTA alignment input | iqtree/iqtree3#235 (2026-10-18) | Open |
| rcedgar/muscle | MUSCLE FASTA input | Issue rcedgar/muscle#112 (2026-10-18; the author asks to be consulted before changes) | Open |
| ezlab/busco (GitLab) | BUSCO genome mode (Biopython `fasta`) | Issue gitlab.com/ezlab/busco/-/work_items/864 (2026-10-20; tested `fasta-pearson` fix, identical completeness) | Open |
| ablab/quast | QUAST threshold rows (`# contigs (>= 0 bp)`, `Total length (>= 0 bp)`) | Issue ablab/quast#300 (2026-10-20; tested patch, PR offered) | Open |
| TransDecoder/TransDecoder | `TransDecoder.LongOrfs` (same reader in Trinity's `PerlLib`) | Issue TransDecoder/TransDecoder#213 (2026-10-20; tested patch, PR offered) | **Accepted 2026-10-20**: the maintainer will fix it in the next TransDecoder release |
| marbl/meryl (marbl/meryl-utility) | `meryl count` (segfault on any input it can't open, e.g. a leading `;` block) | Issue marbl/meryl#58 (2026-10-21; tested null check and `;`-skipping in `bufSeqFile`, PRs offered) | Open |
| marbl/merqury | `merqury.sh` exits 0 with no QV or completeness when `meryl count` fails | Issue marbl/merqury#182 (2026-10-21; tested exit-status checks, PR offered) | Open |
| dib-lab/screed (used by sourmash) | `screed.open()` / `sourmash sketch dna`: "unknown file format" for a leading `;` block | Issue dib-lab/screed#123 (2026-10-22; tested patch, identical sketches; PR offered) | Open |
| Gaius-Augustus/Augustus | `augustus`: leading `;` lines fail type detection ("Found bad character") or, without punctuation, become an extra `unnamed-1` sequence | Issue Gaius-Augustus/Augustus#452 (2026-10-22; tested patch, identical predictions; PR offered) | Open |

Until these are released, the workarounds above apply: strip the header for the tool (`fhr-fasta-strip`)
and keep the FHR file as the record of provenance.

## Not tested

- **Bandage**: GUI only.
- **GATK**: large install; it uses htsjdk, as Picard does.
- **pybedtools**: wraps bedtools.
- **GFA2 and rGFA tags**: only GFA1 was tested.
- **Protein FASTA beyond DIAMOND**: MAFFT/MUSCLE protein modes were not tested (not needed for #40).
- **GFF3 and GFA concatenation**: `#~` lines after features are ordinary
  comments to these tools, so data cannot be corrupted. The result is still
  invalid FHR.
