# Contract: toolkit behaviour for FHGFF3 (FAIR-bioHeaders-Tools)

**Feature**: 007-gff3-header | Research: D-06 to D-09

## Files and kinds

- `.gff3` and `.gff`, plain or with `.gz`/`.bgz`, are the sequence kind `gff3`. Generic commands
  detect it from the extension, and `--type gff3` sets it explicitly.
- New commands `fhr-gff3-combine`, `fhr-gff3-strip` and `fhr-gff3-validate` mirror the GFA ones.
  `bioheaders combine|strip|verify|verify-links` accept GFF3.
- `bioheaders.FHGFF3_SCHEMA` is the bundled `fhgff3_schema.json` (a byte-identical copy of
  `fhgff3.json`). `header_type()` returns `FHGFF3`, `FHP` or `FHR` (D-02), and `schema_for()`
  returns the matching schema.
- `fhr.input_gff3(stream)` and `fhr.output_gff3()` read and write the `#~` header (G1).

## Behaviour

- **combine**: the body's line 1 must start with `##gff-version 3`. Otherwise the error is
  `GFF3 must begin with ##gff-version 3`, exit 1. The output is line 1, then the header, then the
  rest of the body. The default output name is `X.fhgff3.gff3`.
- **strip**: removes exactly the `#~` lines of the leading block. A late `#~` line is an error,
  as for FASTA/GFA.
- **verify** (`fhr-gff3-validate`): validates the header against the selected schema and verifies
  the checksum. Native-directive disagreements are printed as `FHR: warning: <text>` on standard
  error and do not change the exit status.
- **convert**: an FHGFF3 record converts among JSON, YAML and the GFF3 header. JSON-LD and
  microdata output fail with `JSON-LD and HTML microdata output are not available for FHGFF3
  metadata yet`, exit 1.
- **validate** (metadata file): prints `FHGFF3 metadata is valid.` for FHGFF3 records.
- **Messages**: FHR and FHP messages and outputs are unchanged.

## `verify-links`

- **FILE and PARENT** may be FASTA, GFA or GFF3 (plain or compressed).
- **`derivedFrom` items**: handled as in 006 contracts/cli.md.
- **`genomeReference`** (D-08): one line, `genomeReference <accession>: <status>`, where the status
  is `matched`, `not matched` or `not checked (<reason>)`.
- **Cross-check warnings**: printed after the link lines as `warning: <text>`.
- **Closing line**: `A match confirms file identity only, not that the annotation or translations
  are correct.`
- **Exit status**: unchanged (0, 1, 2, 3).

## `assess`

An FHGFF3-headed GFF3 is reported with header type FHGFF3 and its schema result. The old reason
`GFF3 headers are not specified yet (FHR-Specification spec 007)` is gone.

## Library

- `bioheaders.gff3_directives(lines) -> dict`: the native directives of the leading block.
- `bioheaders.cross_check(metadata, directives) -> list[str]`: warning texts (D-07).
- `bioheaders.gff3_header_report(path, genome=None) -> dict`: the results the gff3-validator maps
  to HDR-004 to HDR-010:
  - `placement`, `checksum`, `yaml` and `schema`, each `{"ok": bool, "message": str}`;
  - `genome_link`, the same shape plus the form used;
  - `genome_match`: `matched`, `not matched`, `not checked` or `None` without a genome;
  - `warnings`: a list of strings.
