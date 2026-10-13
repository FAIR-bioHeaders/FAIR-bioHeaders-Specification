# Research notes: GFF3 annotation header (FHGFF3)

**Feature**: 007-gff3-header | **Date**: 2026-10-13 | **Stage**: specify (input to plan's research.md)

These notes ground the choices in [spec.md](spec.md) in the GFF3 specification and in how
annotations are actually published. They record observations, not decisions. The plan's Phase 0
turns them into Decision / Rationale / Alternatives entries.

## G-01 GFF3 specification: directives and comments

Source: The-Sequence-Ontology/Specifications `gff3.md` (version 3.1.26), fetched 2026-10-13,
<https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md>.

- `##gff-version 3.#.#` "must be present, must be the topmost line of the file". A header can
  therefore never come before it.
- Lines beginning with `##` are directives. Lines beginning with a single `#` are human-readable
  comments "and can be ignored by parsers". End-of-line comments are not allowed.
  "Application specific directives are allowed, but are not required to be supported by parsers."
  A `#~` line is therefore an ordinary comment to every GFF3 parser.
- `##sequence-region seqid start end`: optional and "strongly encouraged". There is at most one per
  seqid, and features must lie within it unless the landmark is `Is_circular`.
- `##feature-ontology URI`, `##attribute-ontology URI` and `##source-ontology URI` name the
  ontologies used. "If no feature ontology is specified, then the most recent release of the
  Sequence Ontology is assumed." The SO release used is therefore usually **not** recorded in GFF3
  files.
- `##species NCBI_Taxonomy_URI` and `##genome-build source buildName` (for example
  `##genome-build NCBI B36`).
- `###`: "all forward references to feature IDs that have been seen to this point have been
  resolved". It can occur anywhere and has no meaning before the first feature.
- `##FASTA`: "the annotation portion of the file is at an end and that the remainder of the file
  contains one or more sequences … Once a ##FASTA section is encountered no other content beyond
  valid FASTA sequence is allowed". For Artemis compatibility, a line beginning with `>` implies
  `##FASTA`.

## G-02 NCBI RefSeq GFF3 headers

Observed in the first lines of NCBI FTP files, fetched 2026-10-13:

- `GCF_000001405.40_GRCh38.p14_genomic.gff.gz` (human):
  ```
  ##gff-version 3
  #!gff-spec-version 1.21
  #!processor NCBI annotwriter
  #!genome-build GRCh38.p14
  #!genome-build-accession NCBI_Assembly:GCF_000001405.40
  #!annotation-date 08/01/2025
  #!annotation-source NCBI RefSeq GCF_000001405.40-RS_2025_08
  ##sequence-region NC_000001.11 1 248956422
  ##species https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=9606
  ```
- `GCF_000005845.2_ASM584v2_genomic.gff.gz` (*E. coli* K-12) has the same `#!` lines, minus the
  annotation date and source.
- NCBI therefore states, in `#!` comment lines, the assembly accession, the annotation release
  identifier (`GCF_…-RS_YYYY_MM`), the annotation date and the writing software. It states no
  checksum and no SeqCol digest. The species is a taxonomy browser URL, not the
  `identifiers.org` form FHR uses.

## G-03 Ensembl GFF3 headers

Observed in `Saccharomyces_cerevisiae.R64-1-1.63.chromosome.I.gff3.gz` (Ensembl current_gff3),
fetched 2026-10-13:

```
##gff-version 3
##sequence-region   I 1 230218
#!genome-build SGD R64-1-1
#!genome-version R64-1-1
#!genome-date 2011-09
#!genome-build-accession GCA_000146045.2
#!genebuild-last-updated 2018-10
I	R64-1-1	chromosome	1	230218	…
###
```

- Here `##sequence-region` comes **before** the `#!` lines. Native header lines are not in a fixed
  order across producers.
- `###` occurs after the first feature, as the GFF3 specification describes.
- Ensembl records its genebuild date, not a release identifier for the annotation. The Ensembl
  release number (`63` here) is only in the file name.

## G-04 Annotation tools

- **Liftoff** writes `##gff-version 3`, then `# Liftoff v<version>` and `# <command line>` as plain
  comments (`liftoff/write_new_gff.py`, master, fetched 2026-10-13). A lifted-over annotation
  therefore has a source annotation and a target genome. Its provenance includes the source GFF3
  as well as the genome it annotates.
- **funannotate** writes `##gff-version 3` with no provenance lines (`funannotate/library.py`).
- **AUGUSTUS/BRAKER, MAKER, NCBI EGAPx**: not verified for this note. They are known to write tool
  names in the GFF3 source column and sometimes comment lines. The spec does not depend on any
  tool's comment format.
- Conclusion: software names and versions, where present at all, are in free-text comments in
  tool-specific forms. A structured software object (the shape of FHR's `assemblySoftware`) adds
  information rather than duplicating it.

## G-05 Sequence Ontology version

- `so.obo` starts with `format-version: 1.2`, then `data-version: 2026-08-07` (fetched from
  <http://purl.obolibrary.org/obo/so.obo> on 2026-10-13). The `data-version` date is the citable SO
  release.
- The gff3-validator pins SO `2026-08-07` (FAIR-bioHeaders/gff3-validator, rules SO-*). An
  annotation that records the SO release it used lets a validator report "checked against a
  different SO release" instead of guessing.

## G-06 Genome identity without an FHR genome file

- Most annotated genomes are distributed without an FHR header: NCBI `GCF_`/`GCA_` FASTA, Ensembl
  toplevel FASTA. Their identity is the assembly accession and version. Accessions name a record,
  not exact file bytes: two downloads of one accession can differ in sequence names, soft-masking
  or compression.
- A GA4GH refget sequence collection digest (SeqCol, sha512t24u, level 0) identifies the collection
  by names, lengths and sequence digests (docs/FORMAT.md). It is independent of file bytes, line
  wrapping and masking case under the default attribute profile. The same assembly downloaded from
  two mirrors with the same sequence names has the same digest.
- #54 (2026-10-08) therefore allows the genome link to be either the genome's FHR checksum or its
  accession plus SeqCol ID. FHR stores a SeqCol digest supplied by the user and does not compute it.

## G-07 Current FAIR-bioHeaders state (2026-10-13)

- **Core** (`schemas/core.yaml`): `derivedFrom` items require `headerType`, `checksum` and
  `relationship`, and allow `seqcol_id` and `accessionID`. `checksum` is required, so an
  accession-plus-SeqCol genome link cannot be expressed as a `derivedFrom` item without a core
  change. The provisional relationship vocabulary has `annotates` ("This file annotates the parent
  (e.g. GFF3 on a genome)").
- **FHP precedent** (spec 006, clarified 2026-10-11): `derivedFrom` stays checksum-only, and
  sources that are not FAIR-bioHeaders files go in a separate optional `source` list. Single taxon
  in v0.1. FHP is released from the `release-v0.4` line. The w3id pattern is
  `/fair-bioheaders/<type>/vX.Y.Z`.
- **Toolkit** (FAIR-bioHeaders-Tools `main`): reads `#~` headers in GFA. The leading block ends at
  the first nonblank line that is not a `#` comment (`bioheaders/__init__.py` `sequence_parts`).
  For `.gff3`/`.gff` it currently reports "GFF3 headers are not specified yet (FHR-Specification
  spec 007)" (`bioheaders/cli.py` `GFF3_REASON`). `verify-links` covers FHR and FHP parents.
- **gff3-validator**:
  - HDR-001 to HDR-003 (header required, present but not validated, skipped) are implemented.
  - HDR-004 to HDR-009 are planned: leading block ending at the first feature line or `##FASTA`;
    checksum; safe YAML; schema; the genome link; and the genome link against a supplied genome.
  - Header modes: `--require-header`, `--no-header`, `--genome`.
- **Tool survey** (docs/TOOL_COMPATIBILITY.md, #49): all 11 GFF3 tools tested accept `#~` lines,
  whether before or after `##sequence-region` and with `##FASTA`. `gt gff3 -sort -tidy` moves
  `##sequence-region` above the `#~` block. `gt`, AGAT, `bedtools sort -header` and tabix copy
  `#~` lines into changed files, leaving stale checksums.
- **FHGFF3 fork** (FAIR-bioHeaders/FHGFF3, a fork of biodatamodels/gff-schema): the upstream
  licence is unresolved (#75; request biodatamodels/gff-schema#3). Its 2024 validator is an
  unfinished prototype (#48). It models GFF3 features, not a provenance header.
