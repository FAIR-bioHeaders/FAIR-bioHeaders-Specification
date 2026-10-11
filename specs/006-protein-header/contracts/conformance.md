# Contract: FHP conformance vectors

**Feature**: 006-protein-header | Research: D-09 | Issue: #50 (FHP part)

`scripts/make_conformance.py` adds vectors with manifest `format: "fhp-fasta"` (FASTA container,
prefix `;~`, suffix `.fhp.fasta`, and `.gz` when compressed). Their metadata is a synthetic FHP
record (`sourceType: predicted`, one `derivedFrom` FHR parent with a placeholder-labelled
checksum).

Their body is amino-acid FASTA containing every special residue:

```
>prot1 synthetic protein with a terminal stop
MKTAYIAKQRQISFVKSHFSRQ*
>prot2 synthetic protein with rare and ambiguous residues
MUOBZJXmkta-yi*AKQR
```

## Valid vectors

| id | Rules | Exercises |
|---|---|---|
| `fhp-fasta-lf` | P1, P2, R1–R4, R7, R10 | baseline protein file |
| `fhp-fasta-crlf` | P1, P2, R1, R3 | CRLF bytes hashed as-is |
| `fhp-fasta-no-final-newline` | P1, R1 | last residue line without a terminator |
| `fhp-fasta-comments-and-blanks` | P1, R3, R10 | ordinary comments and blank lines in the header block |
| `fhp-fasta-gzip` | P1, R1 | gzip: decompressed bytes are hashed |
| `fhp-fasta-bgzf` | P1, R1 | BGZF |
| `fhp-fasta-database-source` | P1, P2 | `sourceType: database` with a `source` entry and no `derivedFrom` |
| `fhp-fasta-mixed-sources` | P1 | `mixed`, with a parent, a database source and a contribution |
| `fhp-fasta-rich` | P1 | every optional FHP field |

## Invalid vectors

| id | Rule | Reason |
|---|---|---|
| `fhp-fasta-sequence-changed` | R3 | a residue changed after the checksum was computed |
| `fhp-fasta-stop-normalized-checksum` | R1 | checksum computed after removing terminal `*` |
| `fhp-fasta-case-normalized-checksum` | R1 | checksum computed after upper-casing residues |
| `fhp-fasta-two-checksum-lines` | R2 | two root checksum lines |
| `fhp-fasta-header-after-record` | R10 | a `;~` line after the first `>` |
| `fhp-fasta-missing-source-type` | P1 | no `sourceType` |
| `fhp-fasta-curated-source-type` | P1 | `sourceType: curated` (not an FHP value) |
| `fhp-fasta-genome-key` | P1 | FHR-only key `genome` |
| `fhp-fasta-derived-from-no-checksum` | P1 | `derivedFrom` entry without `checksum` |
| `fhp-fasta-derived-from-bad-relationship` | P1 | `relationship: encodes` |
| `fhp-fasta-source-without-name` | P1 | `source` entry without `name` |
| `fhp-fasta-unused-genetic-code` | P1 | `geneticCode: 7` |
| `fhp-fasta-busco-no-lineage-version` | P1 | `lineageDataset: primates` (no `_odbNN`) |
| `fhp-fasta-cites-fhr-schema` | P2 | protein metadata citing `fhr.json`, so it is read as FHR and fails |

Invalid P1/P2 vectors carry the parsed `metadata` in the manifest. `check_conformance.py --schema`
confirms that it fails `fhp.json` (P1) or `fhr.json` (P2), and that every valid vector's parsed
metadata passes `fhp.json`. Expected checksums come from the generator's independent oracle,
never from the toolkit.
