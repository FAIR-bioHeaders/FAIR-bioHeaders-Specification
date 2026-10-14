# Draft: leading `;` comment lines in htslib FASTA indexing

**Status**: draft for discussion. Not filed upstream.
**Target**: samtools/htslib (`faidx.c`), and through it samtools faidx, bcftools,
pysam and every other faidx consumer.
**Context**: FAIR-bioHeaders-Specification #40; [tool survey](../TOOL_COMPATIBILITY.md).

## Problem

`fai_build_core()` accepts only `>`, `@`, blank lines and CR-LF blank lines
before the first record. Any other first byte is a hard error:

```text
$ samtools faidx genome.fhr.fa
[E::fai_build_core] Format error, unexpected ";" at line 1
[faidx] Could not build fai index genome.fhr.fa.fai
```

FAIR Header Reference (FHR) files carry provenance as YAML in a block of `;~`
lines before the first `>` record ([FORMAT.md](../FORMAT.md), rule R10). These
files cannot be indexed by samtools faidx, pysam.FastaFile, bedtools getfasta,
or any htslib-based reference loader. Users must keep a stripped copy, which
separates the metadata from the data it describes.

## Background: `;` comments in FASTA

Lines starting with `;` are the oldest FASTA comment form. They come from the
Pearson and Lipman FASTA package (Pearson & Lipman 1988, *PNAS* 85:2444), where
`;` lines could appear in the sequence file. Later format summaries note that
most programs no longer recognise them. Several parsers still
support the leading form:

- Biopython's `fasta-pearson` format, and the `fasta` parser's error message
  pointing users to it.
- NCBI BLAST `makeblastdb`, which skipped `;` lines in our survey.
- kseq (BWA, minimap2, seqtk), which skips everything before the first `>`.

## Evidence from the survey

samtools 1.24 / htslib 1.24 / pysam 0.24.0, 2026-10-08:

| Input | samtools faidx | Note |
| --- | --- | --- |
| FHR FASTA, plain, BGZF or CRLF | error at line 1 | Same input after `fhr-fasta-strip` indexes and fetches correctly. |
| One leading `;` line | error at line 1 | |
| `;` line *after* a record, same width as the sequence lines | **accepted silently** | `>a\nACGT\n;mid\n>b\nGG\n` indexes `a` with length 8 and sequence `ACGT;mid`. |
| `cat genome.fa extra.fhr.fa` | error | Only because the comment lines differ in width from the previous record's lines (`Different line length in sequence 'chrM'`). |

`samtools dict`, which uses kseq rather than faidx, accepts the leading block.
On the concatenated file it reports chrM as 2613 bp instead of 1200 bp, with a
different M5.

## Proposed behaviour

1. **Before the first record, skip lines that start with `;`.** This applies
   while the format is still unknown (`FAI_NONE`). The skipped lines do not
   affect offsets: `.fai` offsets are absolute file (or BGZF uncompressed)
   positions, so fetching needs no change and `.fai`/`.gzi` formats are
   unchanged.
2. **After the first record, reject `;` lines with a clear error.** Today such a
   line is either reported as an unexpected character, or silently indexed as
   sequence when its width happens to match. Rejecting it closes the silent
   case shown above. Under FHR R10, a `;~` line after a record already makes
   the file invalid.
3. **Keep FASTQ strict.** If leading `;` lines are followed by an `@` record,
   report an error; FASTQ has no comment convention.

The FHR leading-block rule makes this well defined: a header can only occur
before the first `>`, so htslib never has to decide whether a `;` line inside
a record is sequence or comment.

### Prototype patch

Tested against htslib `develop` at 613169c (2026-10-08). All 25 tests in
`test/faidx/faidx.tst` pass.

```diff
--- a/faidx.c
+++ b/faidx.c
@@ -161,7 +161,7 @@ static inline int fai_insert_index(faidx_t *idx, const char *name, uint64_t len,
 
 static faidx_t *fai_build_core(BGZF *bgzf) {
     kstring_t name = { 0, 0, NULL };
-    int c, read_done, line_num;
+    int c, read_done, line_num, leading_comments = 0;
     faidx_t *idx;
     uint64_t seq_offset, qual_offset;
     uint64_t seq_len, qual_len;
@@ -194,6 +194,10 @@ static faidx_t *fai_build_core(BGZF *bgzf) {
                             hts_log_error("Found '@' in a FASTA file, error at line %d", line_num);
                             goto fail;
                         }
+                        if (leading_comments) {
+                            hts_log_error("Found '@' after ';' comment lines, error at line %d", line_num);
+                            goto fail;
+                        }
 
                         idx->format = FAI_FASTQ;
                         state = IN_NAME;
@@ -214,6 +218,17 @@ static faidx_t *fai_build_core(BGZF *bgzf) {
                         line_num++;
                     break;
 
+                    case ';':
+                        // Legacy (Pearson) FASTA comment.  Accepted only
+                        // before the first record, e.g. an FHR header block.
+                        if (idx->format == FAI_NONE) {
+                            while ((c = bgzf_getc(bgzf)) >= 0 && c != '\n');
+                            leading_comments = 1;
+                            line_num++;
+                            break;
+                        }
+                    // fall through
+
                     default: {
                         char s[4] = { '"', c, '"', '\0' };
                         hts_log_error("Format error, unexpected %s at line %d", isprint(c) ? s : "character", line_num);
@@ -266,6 +281,9 @@ static faidx_t *fai_build_core(BGZF *bgzf) {
                     } else if (c == '>') {
                         state = IN_NAME;
                         continue;
+                    } else if (c == ';') {
+                        hts_log_error("Comment line in sequence '%s' at line %d; ';' lines are only accepted before the first record", name.s, line_num);
+                        goto fail;
                     }
                 } else if (idx->format == FAI_FASTQ) {
                     if (c == '+') {
```

## Compatibility impact

- **Files indexable today**: unaffected, with one exception. Files with a `;`
  line inside a record, which today may be indexed silently with the `;` text
  as sequence, would now be rejected. That outcome is arguably always a bug.
- **Files rejected today with a leading `;`**: now indexable.
- **`.fai` and `.gzi`**: formats unchanged.
- **Other loaders**: CRAM reference loading, `bcftools norm -f`, mpileup `-f`,
  and pysam.FastaFile use `fai_load`/`fai_build`, so they gain support with no
  further change.
- **Format detection**: `hts_detect_format` classifies a file starting with `;`
  as text rather than FASTA. That affects only code that sniffs the format;
  faidx does not. Teaching the sniffer about leading `;` lines could be a
  follow-up.
- **Other tools**: htsjdk (Picard, GATK) and pyfaidx have their own parsers.
  They reject the leading block today and would need separate changes.

## Test cases

To add to `test/faidx/` alongside `faidx.tst`:

| Input | Expected |
| --- | --- |
| `;~a: 1\n;~bb: 22\n>chr1\nACGTACGT\nACGT\n>chr2\nGG\n` | Index identical to the file without the first two lines, except for offsets shifted by the header length. `chr1:1-12` gives `ACGTACGTACGT`. |
| Same as above, BGZF | Same, with a `.gzi`. |
| CRLF: `;c\r\n>a\r\nACGT\r\n` | `a` length 4. |
| `;c\n\n;d\n>a\nACGT\nAC\n` (comments mixed with blank lines) | `a` length 6. |
| `>a\nACGT\n;mid\n>b\nGG\n` | Error: comment line in sequence `a` at line 3. |
| `;c\n@r1\nACGT\n+\nIIII\n` | Error: `@` after `;` comment lines. |
| `;only a comment\n` | Error, as for an empty file (no records). |
| `;c` (no newline, end of file) | Error, as above. |
| Real FHR file from FHR-File-Converter (`fhr-fasta-combine`), plain and BGZF | Same names, lengths and sequences as the stripped file. |

## Related upstream issues

GitHub searches on 2026-10-08 ("fasta comment", "comment lines", "faidx
semicolon", "unexpected ;", "fai_build_core" in samtools/htslib,
samtools/samtools and samtools/hts-specs) found **no issue or PR asking for `;`
comment support**. Related reports on the same error path:

- [samtools/samtools#929](https://github.com/samtools/samtools/issues/929)
  (open): `Format error, unexpected ...` messages are too terse. A
  comment-specific message would help here too.
- [samtools/samtools#1783](https://github.com/samtools/samtools/issues/1783):
  a UTF-8 BOM produced the same "unexpected ... at line 1" failure. FHR R7
  forbids a BOM for the same reason.
- [samtools/samtools#131](https://github.com/samtools/samtools/issues/131):
  misleading error when the first line is not `>name`.

## Before filing

- Confirm with htslib maintainers that point 2 is welcome as a behaviour
  change, or offer it as a warning first.
- Point to the FHR specification and to the converter's `fhr-fasta-strip`
  BGZF output as the current workaround.
