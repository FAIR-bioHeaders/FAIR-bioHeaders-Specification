# Research: Escape FASTA record markers in FHR header lines

## R-01 Evidence

**Decision**: Treat the problem as real silent corruption.

On 2026-10-18 (seqtk 1.5, bioawk 1.0, samtools 1.24, environment `delim` of the tool survey):

| Vector | seqtk comp | bioawk | samtools dict |
| --- | --- | --- | --- |
| `fasta-raw-record-markers` | `example.org;` 56, `Contig1` 20 | `example.org;` 56, `Contig1` 20 | `example.org;` LN 55, `Contig1` LN 20 |
| `fasta-escaped-record-markers` | `Contig1` 20 | `Contig1` 20 | `Contig1` LN 20 |

The bogus record takes the rest of the header as sequence. fair-bioheaders 0.7.0 `combine` writes
raw characters (#127 follow-up). BWA, minimap2 and pysam `FastxFile` use the same kseq parser.

## R-02 A SHOULD, not a MUST; no schemaVersion change

**Decision**: R11 is a recommendation for writers; files with raw characters stay valid and
validators warn.

**Rationale**: the metadata values are unchanged, so schema validity cannot change.
docs/SCHEMA-VERSIONS.md bumps `schemaVersion` for changes to the metadata contract; R11 changes only
how values are written in one container. Rejecting raw characters would make valid v0.3/v0.4 files
invalid, which needs no justification here because escaping fixes new files.

**Alternatives**: a MUST with an invalid vector (breaks existing files); documentation only (leaves
the toolkit writing files that corrupt in kseq tools).

## R-03 The escape

**Decision**: double-quoted YAML scalars with `\x3E` and `\x40`.

**Rationale**: standard YAML escapes, decoded by every YAML reader, so decoding on conversion is
automatic (Adam's requirement). The toolkit double-quotes any string holding either character and
then replaces every `>` and `@` in the emitted text: no other YAML token the writer emits holds one
(keys and values are strings, dates and numbers cannot), and block scalars are never emitted.

**Alternatives**: `>`/`@` (equivalent, longer); percent-encoding (changes values); a
custom escape (needs a decoder everywhere).

## R-04 What the warning covers

**Decision**: FHR header lines (`;~…`), including YAML comment lines and block-scalar indicators
inside the header. Ordinary `;` comments are not checked.

**Rationale**: FHR lines are the ones FHR writers produce, and the scanner holds them whole.
Ordinary comment bytes pass through the scanner as unsplit data; checking them would need a second
line splitter for little gain. The rule text still asks writers to avoid the characters there.
`bioheaders validate` reads only the leading header block for the warning, so it costs nothing for
large genomes. `assess` is unchanged: it reports FAIR properties, not parser hazards.

## R-05 Containers

**Decision**: FASTA (FHR and FHP) only.

**Rationale**: the tool survey found every GFA and GFF3 reader treats `#` lines as whole-line
comments; `>` and `@` have no record meaning there.

## R-06 Relation to R5 and R6

R6 excludes characters YAML treats as line breaks; R11 excludes characters FASTA readers treat as
record starts. Both keep header lines read the same way by FASTA tools and YAML readers. The
checksum value (R5) is base64 and never holds either character.
