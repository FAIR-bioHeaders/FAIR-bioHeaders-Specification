# Candidate source record — Drosophila melanogaster chromosome 4 (example lane)

Status: reviewed and validated **source record for real-data examples**
(`development/examples/dmel4/`). The derived headed files are examples with
provenance, not `development/conformance/` vectors, and they cite no curator
acceptance. FHGM remains a draft (selection rule V7): no `schemaVersion`, no
registry row, no w3id URL, no support claim and no release form attach to
anything in this directory.

## Selection and identities

- Use case and selection rationale: the first real annotated-genome gene-model
  fixtures for FHGM. The maintainer's *Prosapia bicincta* assembly is
  genome-only (zero gene/CDS/mRNA features) and cannot supply gene models;
  *Drosophila melanogaster* `GCF_000001215.4` was chosen as the annotated
  donor (maintainer decision 2026-11-15) and re-verified in this session from
  NCBI `esummary` (see below). Chromosome 4 (1,348,131 bp) bounds a small real
  subset. Two adjacent protein-coding loci were selected by structure from the
  RefSeq GFF3 (not by name from memory): one multi-isoform gene
  (`Dmel_CG11076`: 3 mRNA transcripts, 5 exons, 3 CDS) and one minimal
  single-exon gene (`Dmel_Mpv17`: 1 transcript, 1 exon, 1 CDS). No noncoding
  case is modeled here; that remains open (#204 Q6 territory).
- Article citation, identifier and URL: none used. The source GFF3 rows carry
  no article reference for these two models; nothing was invented and no
  literature was contacted.
- Model-data deposit identifier, version and URL: the RefSeq annotation
  release itself (below). Record-level `publication.deposit` repeats the
  Dbxref tokens exactly as the source writes them (`FLYBASE:FBgn0039929`,
  `GeneID:43830`, `FLYBASE:FBgn0039930`, `GeneID:43831`).
- Retrieval date and actual source filenames/formats: 2026-11-15, HTTPS from
  the NCBI FTP mirror; whole-file downloads only (no ranged reads).
  `GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.fna.gz` (44,235,956 B,
  SHA-256 `e69e907b5e87ce756236dcef93e82001cfd08f1a0ed5f22e36cbbd3a87ebc57d`,
  MD5 `869cf40e4f5c7ca27d04ca9ae7baee4f`) and
  `…_genomic.gff.gz` (8,688,226 B, SHA-256
  `9a372f10f86f4fe4222d070a101716b7565affdd6cb96efae249e8afa3b2c726`, MD5
  `1de22f17786c44ae98d7922116967b4e`). Both MD5s match NCBI's published
  `md5checksums.txt`; both passed `gzip -t` before any read.
- Reference assembly/version and sequence identifiers: `GCF_000001215.4`
  ("Release 6 plus ISO1 MT", status Chromosome, RefSeq category
  reference genome, BioSample `SAMN02803731`, taxid 7227, GenBank synonym
  `GCA_000001215.4`, UCSC synonym `dm6`), verified from NCBI `esummary`
  db=assembly uid=202931 (raw response kept as
  [ncbi-esummary-202931.json](ncbi-esummary-202931.json)). Chromosome 4 is
  RefSeq `NC_004353.4` / GenBank `AE014135.4`, 1,348,131 bp (assembly report
  row; independently counted from the FASTA).
- Model/locus and transcript identifiers: see the table in
  [README.md](README.md#locus-definition); every ID and Parent value is
  copied verbatim from the source GFF3.

## Permissions and bytes

- Payload-specific reuse terms and evidence URL: NCBI's distribution terms
  were not found stated in the downloaded assembly tree (`README.txt` in the
  dataset directory carries no reuse-terms statement), so no terms string is
  quoted into any header: `reuseConditions` is **absent** at both file and
  record scope. The workspace maintainer ruling on record is that the
  sequence is a US Government work and must not be relicensed; this
  repository does not restate a license for it.
- Attribution/notices to retain: the source is named in the FHGFF3 `source`
  field (name, release filename, assembly accession, FTP URL) and in the
  per-record `evidence` entries. The submitter organization "The FlyBase
  Consortium/Berkeley Drosophila Genome Project/Celera Genomics" is recorded
  verbatim as `assemblyAuthor` of the derived FHR subset.
- Permission decision before vendoring: only the 17 extracted locus rows
  (~6.7 KB) and the derived headers are committed. The 44 MB and 8.7 MB
  archives stay out of the repository; the builder pins them by digest.
- Source byte hashes with algorithm: SHA-256 and MD5 above; per-chromosome
  cross-check `chr4.fna` MD5 `edd1c69d6360fe22ee850c3bca51894b`
  (1,365,033 B) from NCBI `uncompressed_checksums.txt`.
- Original versus transformed paths and transformation procedure: originals
  are the two `.gz` archives. Transformations (all implemented
  deterministically in [build_fixture.py](build_fixture.py), every header
  checksum written by `fair-bioheaders` 0.11.0 `bioheaders combine`):
  `Dmel_CG11076-Mpv17.payload.gff3` is the byte-exact region + gene-closure
  rows for the two loci with the `##gff-version 3` directive prepended;
  `Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3` and `…-v2.fhgff3.gff3` add the
  `#~` FHGFF3 1.1 header (with `x-fhgm-models`) around that exact payload;
  the FHR subset file `Dmel-NC_004353.4-chr4.fhr.fa` is the byte-exact
  `NC_004353.4` record from `genomic.fna.gz` plus a `;~` FHR 2.1 header. The
  rebuilt files are byte-reproducible across independent runs.

## Metadata evidence

| Proposed concept | Supplied value | Exact source/location | Missing information or ambiguity |
| --- | --- | --- | --- |
| gene feature ID | `gene-Dmel_CG11076`, `gene-Dmel_CG11077` | `ID=` attribute, gene rows, source GFF3 | — |
| `featureId` = gene row; `modelId` = same opaque string | as left | file-local default per review disposition Q2 | external-ID minting authority still curator-gated (O5) |
| `modelVersion` | `"1"`; revision record `"2"` | this example's own snapshot sequence | RefSeq rows state no model version; opaque equality only (Q3) |
| genome link (file) | `genomeReference` `GCF_000001215.4` + SeqCol `hFwVeJXKpWP3X-g4wmJGT-eZTa1r3Y1l`; `derivedFrom` FHR checksum `zSTzyw4aOnZWd2XXKL9GBWtVWM1S6e0i1vt1XX0mVOY=` | accession: esummary `assemblyaccession`; seqcol: computed from pinned `genomic.fna.gz` (recipe validated on the S6k assembly); FHR checksum: written by toolkit | SeqCol value for this assembly is computed, not published by NCBI |
| `taxon` | name + `https://identifiers.org/taxonomy:7227` | esummary `speciestaxid` | — |
| `evidence` (per record) | row-level provenance strings + FTP URL | payload rows + `provenance.json` | evidence is a producer assertion, not a validation result |
| `publication.deposit` | `FLYBASE:FBgn…`, `GeneID:…` | `Dbxref=` attributes of the gene rows | `publication.article` absent — no article in the source |
| `contributors` | absent | source rows carry no model authorship | RefSeq-derived records have no personal-attribution source (finding) |
| `reuseConditions` | absent | no terms statement in the downloaded tree | finding: a real RefSeq-derived producer has nothing citable |
| `predecessor` (v2) | `annotationChecksum` = v1 checksum, own `modelId`, prior version `"1"` | derived from the committed v1 bytes | the revision is of **this example's own record**, stated in the record's evidence text; it is not a claim about FlyBase/RefSeq model history |

## Validation record

Commands, tools and results are recorded with their outputs in
[README.md](README.md#verification-transcripts): header validation and exact-byte
checksum (`bioheaders verify`, fair-bioheaders 0.11.0), parent matching
(`bioheaders verify-links`, including the negative and partial cases), feature
syntax and genome-aware checks (`gff3-validate 0.1.0 --no-header`, plus a
`--genome` run against the chr4 subset), schema-layer comparison against the
pinned released FHGFF3 1.1 bytes, and the draft model checker
(`development/model/validate_fhgm.py`) including the four neutered-checker
controls. Sequence-level biology: the four CDS intervals were translated from
the extracted chromosome and compared with `…_protein.faa.gz`; two match
exactly, and two differ only at the initiator (genome CTG vs published M) — a
Drosophila CTG-initiation convention, recorded in the README and deliberately
**not** promoted into any header claim.
