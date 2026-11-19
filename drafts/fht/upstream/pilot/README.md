# FHR pilot — *Prosapia bicincta* USDA_Prosapia_bicincta_1.0 (GCA_036971475.1)

Tracks FAIR-bioHeaders/FHT-Specification#40 (pilot split out of the release
ticket #10 by maintainer decision 2026-11-14). This directory carries the
**FHR half** of the pilot: a real published assembly, a released-contract FHR
header written by the **released** `fair-bioheaders` 0.11.0, and the full
command log behind every recorded value. Nothing here is synthetic; nothing
here is FHT — the FHT draft contract takes no part in this pilot and gains no
release form from it (shared rule V7).

## Provenance probes (all re-run by the pilot author on 2026-11-14)

| Value | Source | Probe |
| --- | --- | --- |
| Accession `GCA_036971475.1`, name `USDA_Prosapia_bicincta_1.0`, status **Scaffold**, haploid, coverage 23, taxid **139605**, organism *Prosapia bicincta*, BioSample **SAMN35984262**, BioProject **PRJNA987615**, WGS **JBAIZL01**, isolate DM-2020, submitter **Ag100Pest Initiative Working Group**, GenBank release/submission **2024-03-04** | NCBI Assembly UID 21598811 | `curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=assembly&term=GCA_036971475.1&retmode=json"` → `count: 1`, `idlist: ["21598811"]`; then `esummary.fcgi?db=assembly&id=21598811&retmode=json` (full JSON retained in the PR discussion) |
| Article **10.1093/g3journal/jkae129**, "otb: an automated HiC/HiFi pipeline assembles the *Prosapia bicincta* Genome", *G3: Genes, Genomes, Genetics* **14**(8), published online **2024-06-11**, issue print **2024-08-07**, first author **David C Molik** (ORCID 0000-0003-3192-6538) | Crossref | `curl "https://api.crossref.org/works/10.1093/g3journal/jkae129"` |
| Assembly method `HiFiASM v. 0.16.0-r369`, sequencing technology `PacBio Sequel`, assembly date 16-MAY-2023, GenBank submission authors Molik D.C., Simmonds T., Corpuz R., Kauwe A., Mason C., Sim S., Geib S. | GenBank flatfile header of the first scaffold record | range-GET of the first 3 MB of `..._genomic.gbff.gz`, `gunzip -c \| head` |
| Statistics `total-length 2219595121`, `scaffold-count 428`, `scaffold-N50 270856870`, `scaffold-L50 4`, `scaffold-N90 9050718`, `contig-count 833`, `total-gap-length 41900`, `gc-perc 33` | NCBI | `..._assembly_stats.txt` (whole file) |

> Note on dates: the pilot brief of 2026-11-14 recorded "G3 14(8) 2024-06-11";
> Crossref reports 2024-06-11 as the **online** publication date and 2024-08-07
> as the print issue date; NCBI reports **2024-03-04** as the GenBank
> submission/release date. All three dates are recorded above with their
> sources; none is conflated with another.

## Genome-only constraint (measured, not assumed)

```sh
D=https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/036/971/475/GCA_036971475.1_USDA_Prosapia_bicincta_1.0
f=GCA_036971475.1_USDA_Prosapia_bicincta_1.0
for s in _genomic.fna.gz _protein.faa.gz _genomic.gff.gz _cds_from_genomic.fna.gz; do
  curl -s -o /dev/null -w "$s %{http_code}\n" --range 0-1023 "$D/$f$s"; done
```

Measured 2026-11-14: `_genomic.fna.gz` **206** (serves), `_protein.faa.gz`,
`_genomic.gff.gz`, `_cds_from_genomic.fna.gz` **404** (absent).
`$f_feature_count.txt` (uncompressed in this delivery; the `.gz` name 404s)
reports the single line
`gene  protein_coding  GCA_036971475.1  GCA_036971505.1  Primary Assembly  0  0`
— **Unique Ids 0, Placements 0**. The directory listing contains no annotation
delivery. Consequence: this assembly supports an **FHR pilot only**; deriving
FHP, FHGFF3, FHGM or FHT fixtures from it would require inventing transcript,
protein or feature data, which the federation rules forbid.

## Sequence and masking measurements

`sha256` of the exact downloaded bytes and of the decompressed FASTA,
recomputed record/base statistics (Python 3.13.16, streamed over the file):

| Artifact | Bytes | sha256 |
| --- | --- | --- |
| `..._genomic.fna.gz` (NCBI, Last-Modified 2024-03-05) | 598,121,128 | `73af3dde8beabe4bb7e722aafa31b9c9c9529f40d29582a5b10ae2475b5601e4` |
| `..._genomic.fna` (decompressed) | 2,247,394,312 | `9100ebee1c0169a656660cc679d044f1b210ea13f8296e37ef3ef8c42fea35ba` |

Measurements matched NCBI's `assembly_stats.txt` exactly: 428 records =
scaffold-count; 2,219,595,121 bases = total-length; 41,900 N =
total-gap-length; scaffold N50/L50/N90 = 270,856,870/4/9,050,718 (L90 = 14 is
measured here, not reported by NCBI); case-insensitive GC fraction 33.22%
against NCBI `gc-perc 33`.

Masking: **1,129,108,786 of 2,219,553,221 ACGT characters (50.87%) are
lowercase** in the published `_genomic.fna`, distributed across scaffolds
(measured per record: 45%–100% lowercase on the first six). The only N
characters are the 41,900 gap runs NCBI accounts as spanned gaps, so this is
lowercase masking, not N-substitution. `masking: soft-masked` therefore
describes the observable bytes; `repeat-masked` would additionally assert the
masking agent, which the GenBank structured comment does not document — the
claim is deliberately not made. (A maintainer with pipeline knowledge may
upgrade the value in a reviewed header reissue; the file checksum changes
with it.)

## Header authoring and validation (released toolchain only)

Tool: `fair-bioheaders` **0.11.0 from PyPI** (site-packages install, not a
working tree) under Python 3.15.0:

```text
$ bioheaders --version        # 0.11.0
$ pip show fair-bioheaders    # Version: 0.11.0

$ bioheaders combine pilot/metadata.fhr.yaml GCA_036971475.1_USDA_Prosapia_bicincta_1.0_genomic.fna \
    -o GCA_036971475.1_USDA_Prosapia_bicincta_1.0.fhr.fasta      # 8.3 s

$ bioheaders verify GCA_036971475.1_USDA_Prosapia_bicincta_1.0.fhr.fasta
Checksum verified.                                                # exit 0

$ bioheaders verify-links GCA_036971475.1_USDA_Prosapia_bicincta_1.0.fhr.fasta
no parent files recorded                                          # exit 0
                                                                  # (a primary
                                                                  # assembly
                                                                  # header;
                                                                  # derivedFrom
                                                                  # is absent
                                                                  # by design)

$ bioheaders assess --online --format json --output ... \
    GCA_036971475.1_USDA_Prosapia_bicincta_1.0.fhr.fasta
                                                                  # 12/12
                                                                  # header URLs
                                                                  # resolved,
                                                                  # HTTP 200,
                                                                  # 0 findings
```

Resulting file identity (2026-11-14):

| Artifact | Bytes | Digest |
| --- | --- | --- |
| `..._1.0.fhr.fasta` (header + exact FASTA bytes) | 2,247,396,983 | sha256 `c3e01149d1dc194a73664974c42a6307f207955b3a7951399b7f54a5bfafd560` |
| FHR header block | 2,671 | = 2,247,396,983 − 2,247,394,312 |
| **FHR checksum (SHA-512/256, base64)** | — | `GzNUcBwcd/kAnGzI2dNGsJQbp2mrhJxzLNPvZVzw/Lw=` |

The FHR checksum was independently re-derived outside the toolkit
(Python 3.13.16 `hashlib.new("sha512_256")` over the exact file bytes minus
the `;~checksum:` line and its terminator): identical. The `assess --online`
run recorded above is the released tool's own report (tool version
`bioheaders assess 0.11.0`): 12/12 declared URLs `resolved` HTTP 200, zero
findings.

## What this pilot demonstrates

1. A real, publicly released assembly (not synthetic, not a fixture) carries a
   released-contract FHR 2.1 header written by the released toolkit.
2. The file-bound checksum survives the full pipeline: `combine` →
   `verify` → independent SHA-512/256 recomputation → `assess --online`
   (zero findings), with every declared identifier resolving (12/12 HTTP 200;
   the publisher's landing page behind `doi.org/10.1093/g3journal/jkae129`
   answers 403 to plain `curl` bot traffic on 2026-11-14, while the Crossref
   API resolves the DOI natively — recorded, not hidden).
3. Metadata claims are enforceable: the masking value was **derived from the
   bytes**, and two brief-supplied date framings were corrected against
   primary sources above.

## Not demonstrated / not verified here

- No FHT/FHP/FHGFF3 header exists for this material — see the genome-only
  constraint; no transcriptome, proteome or annotation was fabricated.
- Biosample **attributes** were not fetched (only the accession was needed
  and verified); the G3 full text was not machine-readable through Europe
  PMC (`isOpenAccess=N`), so the masking agent is undocumented here.
- The 2.25 GB FASTA and combined file are **not committed** (repo-size
  policy); [`reproduce.sh`](reproduce.sh) re-creates the combined file from
  NCBI and compares every digest in this table.
- This pilot does not constitute FHT adoption, publication or toolkit
  support (#9/#10 remain open; rule V7).

## Q2 — companion annotation source (dated note, 2026-11-14)

The pilot stops at FHR. Completing the FHT acceptance item of #10
("at least one real public transcriptome carrying an FHT header with
verifiable provenance") requires **Q2: a companion annotation/transcriptome
source**, and specifically:

- a public transcript set (RNA or cDNA FASTA) with a nameable origin — e.g.
  a TSA (transcriptome shotgun assembly) or a published annotated
  transcriptome — whose record the FHT `derivedFrom` can cite with a real
  parent-file checksum and/or accession; and
- a decision whether the pilot transcriptome must belong to the *same
  organism* as this FHR parent (for *Prosapia bicincta* this assembly's
  record carries no annotation and no linked transcripts were found in the
  probes above), or whether a different species with both a published genome
  and public transcripts is acceptable.

Until Q2 is answered with a concrete source, the FHT half of the pilot cannot
proceed without inventing data, and this PR does not proceed.

### Q2 — answered by a different donor (dated note, 2026-11-15)

Both halves of the question are resolved by maintainer decision on 2026-11-15:
the pilot donor for the annotation-bearing half is *Drosophila melanogaster*
`GCF_000001215.4` ("Release 6 plus ISO1 MT"), a Chromosome-level RefSeq
annotation with 13,962 protein-coding genes and 30,802 CDS-with-protein
placements — so the pilot transcriptome is **not** the same organism as this
*Prosapia bicincta* FHR parent, and it does not use this directory's FHR file as
its parent either. See [`dmel-chr4/README.md`](dmel-chr4/README.md) for the
chr4 (`NC_004353.4`) FHR subset, the 334-transcript FHT subset built on it, the
`transcribedFrom` link with a computed-and-independently-re-derived parent
checksum, and the limits that still apply (FHT is a draft; rule V7). This
*Prosapia bicincta* FHR pilot is unchanged and stays genome-only.
