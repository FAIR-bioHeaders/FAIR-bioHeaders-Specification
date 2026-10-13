# Contract: FHGFF3 conformance vectors

**Feature**: 007-gff3-header | Research: D-10

- Format `fhgff3`. Files are `conformance/{valid,invalid}/fhgff3-*.gff3` (or `.gff3.gz`), with
  entries in the shared `conformance/manifest.json`. Rules: R1–R10 and G1–G3.
- `scripts/make_conformance.py` writes them with the standard library only, and computes the
  expected checksums with `hashlib`.
- `check_conformance.py --converter` runs `fhr-gff3-validate` on each vector. A converter without
  GFF3 support skips the format, as it does for `jsonld` and `fhp-fasta`, unless
  `--require-format fhgff3` is given.
- **Valid vectors** (expected checksum and metadata):

| Id | Covers |
|---|---|
| `fhgff3-minimal-checksum-link` | G2 checksum form |
| `fhgff3-minimal-reference-link` | G2 reference form |
| `fhgff3-both-links` | D-03 both forms |
| `fhgff3-directives-interleaved` | G1: `##sequence-region`, `##species`, `#!` lines between `#~` lines |
| `fhgff3-directives-after-header` | G1 |
| `fhgff3-triple-hash-before-features` | G1 `###` |
| `fhgff3-embedded-fasta` | R1, G1 `##FASTA` covered by the checksum |
| `fhgff3-header-only` | no features |
| `fhgff3-version-3-1-26` | G1 version forms |
| `fhgff3-crlf` | R1 line endings hashed as-is |
| `fhgff3-gzip`, `fhgff3-bgzf` | R1 decompressed bytes, same checksum |
| `fhgff3-nested-parent-checksum` | R3 parent checksum covered |

- **Invalid vectors** (expected rule):

| Id | Rule |
|---|---|
| `fhgff3-header-after-feature` | R10 |
| `fhgff3-header-after-fasta` | G1 |
| `fhgff3-concatenated` | R10 |
| `fhgff3-header-before-version` | G1 |
| `fhgff3-no-genome-link` | G2 |
| `fhgff3-half-reference` | G2 |
| `fhgff3-two-annotates` | G2 |
| `fhgff3-annotates-fhp` | G2 |
| `fhgff3-fhr-only-key` | G2 |
| `fhgff3-two-checksum-lines` | R2 |
