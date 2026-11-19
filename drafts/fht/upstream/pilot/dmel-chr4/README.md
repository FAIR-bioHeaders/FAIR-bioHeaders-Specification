# FHT pilot — *Drosophila melanogaster* GCF_000001215.4 chromosome 4 (FHR parent, FHT transcript subset)

Tracks FAIR-bioHeaders/FHT-Specification#8 (real examples and vectors) and #10
(pilot evidence). This directory carries the first real-data **FHT** header in
the repository: a transcript subset of a published, annotated reference
assembly, whose `derivedFrom` parent is a real **FHR** file that was built here
and whose checksum was computed by the released toolkit and then re-derived
independently.

Status, stated plainly:

- FHT is a **draft**. This record cites the development contract exactly as the
  repository fixtures do — `https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json`
  with `schemaVersion: '1.0'` — and takes no release form: no w3id URL, no tag
  URL, no `schemas/versions.json` row, no "supported" or "official" claim
  (shared selection rule V7). That a real file can be written and verified
  through the toolkit's opt-in draft lane is not a release.
- The FHR half uses the **released** contract: FHR 2.1 at
  `https://w3id.org/fair-bioheaders/fhr/v0.6.0`.
- Every header was written by `fair-bioheaders` **0.11.0 from PyPI** (`bioheaders
  combine`), never by hand and never from the toolkit's working tree. Checksums
  are computed values; the two recorded here were also re-derived with
  [`rederive_checksum.py`](rederive_checksum.py) (stdlib `hashlib`, independent
  of the toolkit).
- No sequence bytes are committed. This directory holds provenance, the header
  records, the selection table and the scripts;
  [`reproduce.sh`](reproduce.sh) rebuilds every byte from NCBI and compares
  every digest in this file.

## Why this donor

The FHR pilot in [`../README.md`](../README.md) used *Prosapia bicincta*
`GCA_036971475.1`, which is genome-only: no `_protein.faa.gz`, no
`_genomic.gff.gz`, and `_feature_count.txt` reporting `Unique Ids 0 / Placements
0`. It cannot support an FHT subset without inventing transcripts, which the
federation rules forbid. That pilot's open question **Q2** ("a companion
annotation/transcriptome source") is answered here: on 2026-11-15 the maintainer
selected *Drosophila melanogaster* `GCF_000001215.4` ("Release 6 plus ISO1 MT")
as the annotated donor, and this directory is that donor's chr4 subset.

## Stage 1 — provenance record

Source of the accession facts, re-probed on 2026-11-15 (not copied from the
brief): NCBI Entrez `esearch.fcgi?db=assembly&term=GCF_000001215.4` → uid
**202931**; `esummary.fcgi?db=assembly&id=202931&retmode=json`.

| Fact | Value |
|---|---|
| RefSeq accession | `GCF_000001215.4` (GenBank `GCA_000001215.4`, "identical") |
| Assembly name / description | `Release 6 plus ISO1 MT` / "Release 6 plus ISO1 mitochondrial genome" |
| Organism / taxid | *Drosophila melanogaster* (fruit fly) / `7227` |
| Assembly level / type | Chromosome / haploid |
| RefSeq category / UCSC name | reference genome / `dm6` |
| BioSample / BioProject | `SAMN02803731` / `PRJNA164` (RefSeq), `PRJNA13812` (GenBank) |
| Submitter organization | The FlyBase Consortium / Berkeley Drosophila Genome Project / Celera Genomics |
| Submission / release / last updated | 2014-08-01 / 2014-08-08 (GenBank and RefSeq) / 2020-12-23 |
| Annotation descriptors last changed | 2023-12-27 (delivery `annotation_hashes.txt`) |
| FTP base | `https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/215/GCF_000001215.4_Release_6_plus_ISO1_MT/` |

The sliced molecule, from the delivery's `_assembly_report.txt` data row
(columns `Sequence-Name … UCSC-style-name`):

| Sequence-Name | Sequence-Role | Assigned-Molecule | Location/Type | GenBank | Rel | RefSeq | Assembly-Unit | Length | UCSC |
|---|---|---|---|---|---|---|---|---|---|
| 4 | assembled-molecule | 4 | Chromosome | AE014135.4 | = | NC_004353.4 | Primary Assembly | 1348131 | chr4 |

`##sequence-region NC_004353.4 1 1348131` in `_genomic.gff` agrees with that
length, and the `_genomic.fna` defline is
`>NC_004353.4 Drosophila melanogaster chromosome 4`.

### Downloaded files and their digests

Retrieved 2026-11-15 by whole-file `curl` of the URLs above. Every file below
was digested over its complete bytes; the `md5` column is this run's MD5
compared with the delivery's own `md5checksums.txt` entry for that exact path,
which is the positive control that the bytes are the published ones (a
`404`-shaped HTML "Object not found" page or a truncated ranged read would fail
here rather than looking like a missing file).

| File (under the FTP base) | Bytes | SHA-256 | MD5 = NCBI published | Used for |
|---|---|---|---|---|
| `…_genomic.fna.gz` | 44,235,956 | `e69e907b5e87ce756236dcef93e82001cfd08f1a0ed5f22e36cbbd3a87ebc57d` | yes (`869cf40e…`) | reference slice |
| `…_rna.fna.gz` | 23,529,984 | `bc3f402dbdb44b2ed075ddcd10800a1d15a123aeaf99c9cf16bf1085e3ec7855` | yes (`45a0b338…`) | transcript slice |
| `…_genomic.gff.gz` | 8,688,226 | `9a372f10f86f4fe4222d070a101716b7565affdd6cb96efae249e8afa3b2c726` | yes (`1de22f17…`) | transcript/exon coordinates |
| `…_genomic_gaps.txt.gz` | 5,753 | `e993042891ae03def7e2e32c559e23cd34c8692ba677ff12a4026d93ddd18041` | not listed | N accounting |
| `…_assembly_report.txt` | 214,116 | `22bf2cefea3bf4abc56aab340bdfb32f27dcd02b78f57c0762f8f1036e7963e7` | yes (`ecb1db60…`) | molecule identity |
| `…_feature_count.txt` | 3,929 | `1bcc2d12804490dd10452dc9d98ca42c7125ccc2591dad0603ee9783c671d76d` | yes (`390ad296…`) | annotation richness |
| `…_assembly_structure/…/FASTA/chr4.fna.gz` | 378,797 | `c0d89f2a877d3f75896b72340bfbe0be5b9c7edcfb733565021bea147c157f3e` | yes (`1531d6b6…`) | case-only control |
| `md5checksums.txt` | 5,747 | `148f87060005d84a397d74a216cca8454d0f37bd8928be5ac9517169439c9fa1` | — | control list |
| `uncompressed_checksums.txt` | 3,045 | `edbc2647a9f35bca7c2695efde8690d65166249423b9d693ea0aefce635d632c` | — | control list |
| `annotation_hashes.txt` | 410 | `8440fb061a189d21cc26f7d7db70d1daba6b242e17a3292ed480ccf2c1374ccc` | — | annotation dates |

Machine-readable copy with the same numbers plus the derived-artifact digests:
[`provenance.json`](provenance.json).

Decompression was verified the same way — whole-file `gunzip`, then MD5 and size
against `uncompressed_checksums.txt`:

| Uncompressed file | Bytes | MD5 | Matches NCBI |
|---|---|---|---|
| `…_genomic.fna` | 145,657,746 | `a201b53b7eab2eb161671e4b3ae670a0` | yes |
| `…_rna.fna` | 96,785,880 | `76e78617dd3457f256f884ae68933372` | yes |
| `…_genomic.gff` | 164,988,613 | `399b4ac37cc123b724895334be589fdc` | yes |
| `chr4.fna` (component file) | 1,365,033 | `edd1c69d6360fe22ee850c3bca51894b` | yes |

Annotation richness, from `…_feature_count.txt` (assembly-wide, class
`protein_coding` / `with_protein`): 13,962 protein-coding genes and 30,802
CDS-with-protein placements for `all`, 13,949 / 30,789 on the Primary Assembly
unit, plus 1,996 lncRNA, 503 antisense_RNA, 262 miRNA and 54 ncRNA genes. This
donor has gene models, which is what makes an FHT subset possible at all.

## Stage 2 — the chr4 subset

[`extract_chr4.py`](extract_chr4.py) defines and builds it; the exact rules are
in its docstring and are summarised here. Nothing is selected by name guessing,
and nothing absent from the delivery is filled in.

**Reference slice (the FHR file).** The single FASTA record whose sequence id is
`NC_004353.4`, copied byte for byte (defline and sequence lines) from
`…_genomic.fna`, which holds 1,870 records. Result: 1 record, 1,365,033 file
bytes, sha256 `9ea85183fc77137381a6e81adf8f088c84c68a888dc323ef8b286b4ef165e184`,
md5 `d6f9e65e3fd14cfcd81bb054746c1806`.

Independent control: NCBI's own per-chromosome file
`…_assembly_structure/Primary_Assembly/assembled_chromosomes/FASTA/chr4.fna`
(1,365,033 bytes, md5 `edd1c69d…`) is **the same length and the same letters**,
and the two differ **only in letter case**: the component file is uppercase, the
`_genomic.fna` record is soft-masked. That is a measured statement
(`differs_only_in_letter_case: true`), and it is what licenses the masking claim
below.

**Transcript set (the FHT file).** Every GFF3 feature on sequence name
`NC_004353.4` whose type is one of `mRNA`, `lnc_RNA`, `antisense_RNA`, `miRNA`,
`snoRNA`, `primary_transcript` and whose `ID` is `rna-<accession>`: **338**
features. Of these, **334** carry a public accession and **exactly those 334**
have records in `…_rna.fna` (34,526 records total); they were copied verbatim,
in source order, to produce 1,382,800 bytes, sha256
`f196bb2cd5cc98d56ae2c3c365d1322e93a42d33d8ba8c0cad66e86fb2cffd3c`.

| Selected feature type | Count |
|---|---|
| mRNA | 298 |
| lnc_RNA | 18 |
| antisense_RNA | 15 |
| primary_transcript | 2 |
| snoRNA | 1 |
| **selected total** | **334** |

**Excluded, not invented.** Four annotated `miRNA` features on `NC_004353.4` have
`ID` values of the form `rna-gnl|FlyBase|…` — `CR46291-RB` (400703-400724),
`CR46291-RA` (400744-400765), `CR43009-RA` (626142-626162), `CR43009-RB`
(626180-626200). They have no public accession and therefore no `_rna.fna`
record, so they are absent from the subset and named here instead of being given
a fabricated identifier. The full per-transcript selection — accession, feature
type, coordinates, strand, parent gene, exon interval count, whether an
`_rna.fna` record exists — is [`chr4_transcripts.tsv`](chr4_transcripts.tsv)
(334 rows plus one comment line, sha256
`bf679f3c1a9127f1c02b4a84f13bd55851ed51fcdc829cd71d3e6885a7631f3f`).

### Measured bytes (masking, N, composition)

Measured over the exact shipped slice bytes, never taken from a summary:

| Quantity | Reference slice (`NC_004353.4`) | Transcript slice (334 records) |
|---|---|---|
| Records | 1 | 334 |
| Sequence symbols | 1,348,131 | 1,334,408 |
| ACGT letters | 1,331,131 | 1,334,408 |
| Lowercase letters | 374,633 | 0 |
| Lowercase fraction | 0.28143962 of letters; 0.27789065 of all symbols | 0 |
| `N` characters | 17,000 | 0 |
| GC | 469,221 letters = 35.2498 % of ACGT | — (not reported in the header) |
| Longest / shortest record | 1,348,131 / 1,348,131 | 27,666 / 63 |
| N50 | 1,348,131 | 4,898 |
| Mean record length | — | 3,995.2335 → 3995.2 |

Character census of the reference slice: `A` 286,843 · `C` 186,129 · `G` 188,866
· `T` 294,660 · `N` 17,000 · `a` 138,398 · `c` 46,437 · `g` 47,789 · `t` 142,009;
no other characters. The 17,000 `N` are one NCBI-reported gap:
`NC_004353.4 1200663 1217662 17000 within_scaffold map` in
`…_genomic_gaps.txt`. The transcript slice census is exactly `A` 443,977 ·
`C` 258,845 · `G` 260,779 · `T` 370,807 — no `N`, no lowercase.

**Masking decision.** `masking: soft-masked` in the FHR header is the measured
state: 27.79 % of the shipped symbols are lowercase and the uppercase variant is
published as the component file, so lowercase encodes masking rather than being
absent. `repeat-masked` is **not** asserted: that would additionally claim which
agent produced the masking, and the delivery records used here do not state it
for this chromosome subset.

### Derivation proof

`transcribedFrom` in the FHT contract means "an FHR genome whose bases were
extracted", and the contract warns that genome guidance alone is not such a
link. So the relationship is checked rather than assumed: for each of the 334
records, the spliced join of that record's own GFF `exon` intervals on
`NC_004353.4` (reverse-complemented when the feature is on the minus strand) is
compared with the delivered transcript bytes.

Result: **334 of 334 equal the exon join**. 4 match including the parent's
masking case (they lie entirely in unmasked sequence); the other 330 match after
case folding, which is exactly what a soft-masked parent and an uppercase
transcript delivery imply. Zero mismatches. Negative controls in the same run:
the parent bytes really are case-variable, the reverse-complement table is
checked against a fixed expected mapping, and a single-base mutation of a
transcript is detected as a mismatch — so the comparison is capable of failing
and is not a vacuous pass.

## Stage 3 — the family chain, with the released toolkit

Toolchain: `fair-bioheaders` **0.11.0** installed from PyPI into a throwaway
venv, Python 3.15.0. The FHR step runs on the **default path**; the FHT step
runs with `BIOHEADERS_EXPERIMENTAL_FHT=1`, the opt-in V7 draft lane.

```text
$ bioheaders combine metadata.fhr.yaml out/chr4_genomic.fna -o GCF_000001215.4_chr4.fhr.fasta
$ bioheaders verify GCF_000001215.4_chr4.fhr.fasta
Checksum verified.
$ bioheaders verify-links GCF_000001215.4_chr4.fhr.fasta
no parent files recorded
```

FHR file: 1,368,589 bytes (1,365,033 sequence + 3,556 header, 66 `;~` lines),
sha256 `5e797185f974ccefe01ae7c2dfd5fd6e3c8cf221dab83f6548c29a00f0824f40`,
computed checksum

```text
;~checksum: qQs9oEKygk63F7ppYVl9te6U8lVHeE8Fbzlf7lmB4Yw=
```

That value is what the FHT header's single `derivedFrom` entry carries:
`headerType: FHR`, `relationship: transcribedFrom`, `checksum` as above, plus
`accessionID: NC_004353.4` as additional information.

```text
$ BIOHEADERS_EXPERIMENTAL_FHT=1 bioheaders combine metadata.fht.yaml out/chr4_rna.fna \
    -o GCF_000001215.4_chr4_transcripts.fht.fasta
FHT: warning: schema https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json
selects the bundled FHT draft contract (development only, not a released schema;
experimental opt-in via BIOHEADERS_EXPERIMENTAL_FHT, see docs/FHT-SELECTION-DESIGN.md)
$ BIOHEADERS_EXPERIMENTAL_FHT=1 bioheaders verify GCF_000001215.4_chr4_transcripts.fht.fasta
Checksum verified.
$ BIOHEADERS_EXPERIMENTAL_FHT=1 bioheaders verify-links \
    GCF_000001215.4_chr4_transcripts.fht.fasta GCF_000001215.4_chr4.fhr.fasta
FHT: warning: … (the draft-lane warning above, repeated on every read)
derivedFrom[0] FHR transcribedFrom: matched (GCF_000001215.4_chr4.fhr.fasta)
A match confirms file identity only, not that the translations are correct.
```

FHT file: 1,387,037 bytes (1,382,800 sequence + 4,237 header, 69 `;~` lines),
sha256 `be72f9b29a138d4ab2f52189a750e849f738265f19c3488f97143a1ffb8f11f0`,
computed checksum

```text
;~checksum: BUcrVpAVDG29yRm+DPmX2U5uHwFOSK/trlZpByY2DTk=
```

Controls, so the green result means something:

```text
$ bioheaders verify GCF_000001215.4_chr4_transcripts.fht.fasta          # draft lane OFF
FHR: warning: schema …/FHT-Specification/main/fht.json is not a FAIR-bioHeaders schema URL;
read as FHR, not FHT, against the current schema (rule V5)
FHR: schema validation failed at $.schemaVersion: '1.0' is not one of ['2.0', '2.1']   (exit 1)

$ BIOHEADERS_EXPERIMENTAL_FHT=1 bioheaders verify-links <the FHT file> conformance/parents/parent-genome.fhr.fasta
derivedFrom[0] FHR transcribedFrom: not matched (… has checksum pdDy56KE7+tzfZfk9eVOAQOPc/Fj78DfNBWOpJC4xac=)
… : not a recorded parent                                                 (exit 3)

$ BIOHEADERS_EXPERIMENTAL_FHT=1 bioheaders verify-links <the FHT file> out/chr4_genomic.fna
derivedFrom[0] FHR transcribedFrom: not checked (no supplied file of that header type)
out/chr4_genomic.fna: not checked (No ;~ FHR metadata header found)       (exit 0)
```

### The subset is the point

`derivedFrom` here names the **chr4-only** FHR file: 1,348,131 bp of one
chromosome, not the 143 Mbp assembly. The whole-assembly file
`…_genomic.fna` has its own different FHR checksum, and this header deliberately
does **not** carry it. Citing the whole-assembly checksum while shipping a chr4
subset would let `verify-links` report `matched` against a file that is not the
one the transcripts were taken from — a verified link to a false provenance
claim. Both headers say in `documentation` that the parent is this subset and
that a real deployment would point at the full assembly; the FHR `genome` name
says `chromosome 4 (NC_004353.4 subset)` and the FHT `transcriptome` name says
`chromosome 4 transcripts (NC_004353.4 subset)`.

### Independent re-derivation

`rederive_checksum.py` implements the FORMAT.md coverage rule from the rule text
(SHA-512/256 over every byte except the root `;~checksum:` line and its
terminator, canonical padded base64) with stdlib `hashlib` only, and is not a
wrapper around the toolkit:

```text
GCF_000001215.4_chr4.fhr.fasta
  file bytes        1368589
  covered bytes     1368532  (file minus the checksum line and its terminator)
  recomputed        qQs9oEKygk63F7ppYVl9te6U8lVHeE8Fbzlf7lmB4Yw=
  stated in header  qQs9oEKygk63F7ppYVl9te6U8lVHeE8Fbzlf7lmB4Yw=
  matches           yes
  tamper control    first sequence base 't' -> 'C' gives RiP+WQ9TMwAv5LKulQS8MIEMlfnYrQHjKUJTL/fMrMo=; detected=yes
GCF_000001215.4_chr4_transcripts.fht.fasta
  file bytes        1387037
  covered bytes     1386980  (file minus the checksum line and its terminator)
  recomputed        BUcrVpAVDG29yRm+DPmX2U5uHwFOSK/trlZpByY2DTk=
  stated in header  BUcrVpAVDG29yRm+DPmX2U5uHwFOSK/trlZpByY2DTk=
  matches           yes
  tamper control    first sequence base 'G' -> 'C' gives q2n9HPycJvk/29GAzcR4EJ3r8IqOGwMp7UDXjzPl3IA=; detected=yes
```

The parent value in the FHT header is the FHR file's computed checksum, and it
is the value the independent re-derivation produces from the parent file's own
bytes — it was not copied from an assertion in the header under test.

### Schema validation, strip round trip, assess

Validation with `jsonschema` 4.26.0 `Draft202012Validator` + `FormatChecker`
(the pins in [`../../docs/CI.md`](../../docs/CI.md)):

| Record | Schema | Result |
|---|---|---|
| FHT header | this repository's `fht.json` at `origin/main` (sha256 `59ad9641adcb0e55…`) | VALID |
| FHT header | toolkit-bundled `fht-draft.json` (sha256 `11c69d6647736695…`) | VALID |
| FHR header | released `fhr_schema.json` (sha256 `694ab5afaf8c3743…`, FHR 2.1 = the v0.5.0/v0.6.0 copy) | VALID |

Draft-pin observation for #9: the 0.11.0 bundle pins the draft at commit
`b9ad19a62772092e08935cff44ee77a50981bbaf` (retrieved 2026-11-12, sha256
`11c69d66…`), while `origin/main` `fht.json` is `59ad9641…`. The only
differences are the `completeness.lineageDataset` pattern and its descriptions
(BUSCO names with dotted version suffixes), which this record does not use, so
the record validates against both. The pin is nonetheless older than main.

Strip round trips (byte equality with the extracted inputs, checked with
`cmp`-equivalent assertions in `reproduce.sh`):

```text
ok:   strip(FHR) == out/chr4_genomic.fna
ok:   strip(FHT, draft lane) == out/chr4_rna.fna
```

`bioheaders assess --online` (0.11.0):

| File | Online checks | Findings | Conformance field |
|---|---|---|---|
| FHR | 11, all `resolved` | none | `valid` against FHR 2.1 |
| FHT | 6, all `resolved` | 1 (see below) | `not_assessed`, reason `unsupported-header-type` |

The single FHT finding is real and is left in place rather than worked around:

```text
line 15: the value 'NC_004353.4' of derivedFrom is not a well-formed insdc-assembly-accession
```

`assess` classifies `derivedFrom[].accessionID` against
`(?:NCBI_Assembly:)?GC[AF]_\d{9}\.\d+`. A subset parent's accession is a
sequence accession, not an assembly accession, so the honest value is flagged.
Substituting `GCF_000001215.4` would silence the finding and describe a parent
file that does not exist here, so it was not done. Both behaviours are pilot
evidence for #9 (what the draft lane does and does not cover) and a question for
the curator list below.

## Stage 4 — classification of every artifact

| Artifact | Bucket | Reason |
|---|---|---|
| `provenance.json` | pilot evidence for #10 | accession/URL/digest record; no normative claim |
| `metadata.fhr.yaml`, `metadata.fht.yaml` | pilot evidence for #10; candidate `examples/` content for #8 | real-data-derived, provenance-labelled header inputs |
| `header.fhr.txt`, `header.fht.txt` | pilot evidence for #10 | the verified `;~` blocks, byte-exact, with computed checksums |
| `chr4_transcripts.tsv` | pilot evidence for #10 | the selection table the subset is defined by |
| `extract_chr4.py`, `rederive_checksum.py`, `reproduce.sh`, this file | pilot evidence for #10 | documentation plus reproduction script |
| `GCF_000001215.4_chr4.fhr.fasta`, `GCF_000001215.4_chr4_transcripts.fht.fasta` | **not committed** | 1.4 M each of third-party sequence; rebuilt and digest-checked by `reproduce.sh`, following the `../README.md` precedent |

**No conformance vectors were added.** `conformance/` stayed exactly as it was
at this PR's date (66 vectors, 1 parent fixture; see
[`../../conformance/README.md`](../../conformance/README.md)). A real example is
not promoted to a normative vector here, for the reason that file already
states: vector `expected` outcomes must be independently reviewed against the
rule text, not generated by the thing under review. These artifacts were
produced by an implementation (the released toolkit's draft lane), so they
cannot bootstrap themselves into vectors. If a reviewer wants any of them as
vectors, the absorption procedure in that README applies: keep `selfChecksum`
and `parentLink` semantics on the C1-C3 model, and record the suite commit
separately from the contract commit.

**Classification question written rather than decided.** Whether a real-data,
provenance-labelled FHT record should also land in `examples/` is left to the
maintainers: `examples/` is currently generated and re-verified as a
deterministic, synthetic set ([`../../conformance/README.md`](../../conformance/README.md)
"Synthetic content policy"; `tests/test_examples.py` validates every
`examples/*.fht.fasta`), and a real-data example would need that lane to carry
both synthetic and real records. This PR therefore adds nothing to `examples/`
and asks, on #8, whether the intended home for the pilot headers is `examples/`,
`pilot/`, or a new `examples/real/` with its own lane.

## Stage 5 — gates and counts

Verified, not copied. Baseline measured in this worktree at `origin/main`
(`156bda6`), then again with these files added. Neither run touches
`conformance/`, `examples/`, `fht.json` or `fht_linkml.yml`, so the counts are
unchanged by design:

| Gate | Baseline on `main` | With this change |
|---|---|---|
| `python scripts/check_fht_fixtures.py` | `OK: all fixture lanes pass`; manifest 25 valid + 41 invalid = **66 vectors**, 19 rules, 1 parent fixture, `retired: 0`; 68 conformance files + 13 owned example files regenerate byte-identically; 6 example FASTA headers recomputed | `OK: all fixture lanes pass`; identical census: 66 vectors (25 + 41), 19 rules, 68 + 13 regenerated, 6 example headers, rejections 21 shape / 16 schema / 2 fhr-routed (V5) / 2 parent-link |
| `python -m unittest discover -s tests` | `Ran 45 tests … OK` (needs `linkml==1.11.1`; without it, 44 pass and `test_generation` errors on the missing module) | `Ran 45 tests … OK` |
| `python scripts/check_docs.py` | passed, 12 Markdown files, 34 external URLs noted | passed, **13** Markdown files (this one added), 34 external URLs noted |
| `npx -y markdownlint-cli2@0.24.0` | clean | clean: `Linting: 13 files`, `Summary: 0 issues in 0 files` |

The counts above are the record for this directory's review date (2026-11-15,
PR #45). The suite grew later the same day: the issue #8 box-3 work registered
R9 and added the two stream vectors, and the pilot promotion candidates (#47)
added four more vectors and two more parent fixtures, so `conformance/` is now
**72 vectors
(28 valid + 44 invalid), 21 rules, 3 parent fixtures**. Read
[`../../conformance/README.md`](../../conformance/README.md) for the current
census; nothing in the pilot changed.

`scripts/check_examples.py` does not exist in this repository; the equivalent
lanes are `scripts/check_fht_fixtures.py` (examples recomputation) and
`tests/test_examples.py`. The "291 = 228 pass / 0 fail / 63 declared-not-run"
ledger is the **shared** suite in FAIR-bioHeaders-Specification (its
`conformance/manifest.json` holds 291 vectors: 119 valid / 172 invalid across
`fasta`, `gfa`, `fhp-fasta`, `fhgff3`, `jsonld`, `microdata`) and no `fht-fasta`
format; it is not a count in this repository and was not re-run here. The brief's
"66 vectors in 2 files, `fht-1.0-draft.json` 45 + `fhgm-1.0-draft.json` 21"
matches nothing in this checkout: this repo's 66 vectors live in one manifest
(25 + 41), and no file with either of those names exists in FHT-Specification or
in FAIR-bioHeaders-Tools `origin/main` (checked with `git ls-tree`).

## What is not verified / open questions

- **Not a released FHT capability.** Nothing here makes FHT supported, released
  or registered. The default reader still refuses these records (rule V5), which
  is the behavior the vectors already assert.
- **`assess` does not assess FHT conformance** (`not_assessed` /
  `unsupported-header-type`), and it flags a subset parent's sequence accession
  as not a well-formed assembly accession. Both are #9 items, not FHT contract
  items.
- **The toolkit's draft pin is older than `main`** (`11c69d66…` at `b9ad19a6…`,
  2026-11-12, vs `59ad9641…`); the difference is the `completeness.lineageDataset`
  BUSCO pattern. Worth re-pinning on the next toolkit release.
- **`reuseConditions` is omitted from both headers.** The delivery carries no
  license statement (`README.txt` has none), and "NCBI RefSeq is a US Government
  work" is not a claim this subset can source for FlyBase/BDGP/Celera-derived
  sequence, so nothing is asserted. Should the pilot carry an explicit reuse
  string, and who supplies it with authority?
- **`dateCreated` semantics.** The FHT header uses 2026-11-15, the date this
  subset was extracted; the annotation itself is FlyBase's on an assembly
  submitted 2014-08-01 with annotation descriptors last changed 2023-12-27. The
  FHR header keeps 2014-08-01, the assembly's own creation date. If `dateCreated`
  should always mean the upstream resource rather than the file, the FHT value
  changes and the checksum changes with it.
- **`assemblySoftware` is omitted** although the contract invites recording an
  extraction ("Extraction is a process too"). Recording the pilot's own
  not-yet-published script as the software of record looked self-referential;
  the extraction is described in `documentation` and scripted here instead. A
  curator decision on that field would settle it.
- **`moleculeType` is omitted deliberately**: the set is heterogeneous (298 mRNA
  with 36 non-coding records), and the contract says to omit it for
  heterogeneous sets rather than pick one label.
- **Not checked:** per-chromosome GC or N50 against an NCBI summary (this
  delivery's `_assembly_stats.txt` is assembly-level, not per molecule), the
  identity of the masking tool, and whether the four excluded miRNA features
  should be represented by their FlyBase transcript ids.

## Reproducing

```sh
python3 -m venv .venv-pilot
.venv-pilot/bin/pip install fair-bioheaders==0.11.0
PYTHON_VENV="$PWD/.venv-pilot" bash pilot/dmel-chr4/reproduce.sh
```

The script exits non-zero on the first mismatch between a recorded value and a
recomputed one. It needs about 76 MB of downloads and writes only inside
`PILOT_WORK_DIR` (default `/tmp/fht-pilot-dmel`).
