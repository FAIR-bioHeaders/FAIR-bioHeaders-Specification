# Research notes: protein FASTA header (FHP)

**Feature**: 006-protein-header | **Date**: 2026-10-10 | **Stage**: specify (input to plan's research.md)

These notes ground the field choices in [spec.md](spec.md) in how protein sets are actually
produced and published. They record observations, not decisions; the plan's Phase 0 turns them into
Decision / Rationale / Alternatives entries.

## N-01 UniProt proteomes and FASTA headers

- UniProtKB FASTA header:
  `>db|UniqueIdentifier|EntryName ProteinName OS=OrganismName OX=OrganismIdentifier[ GN=GeneName] PE=ProteinExistence SV=SequenceVersion`.
  `db` is `sp` (Swiss-Prot, reviewed) or `tr` (TrEMBL, unreviewed). Review status is therefore a
  property of each sequence, not of a whole download.
  Source: <https://rest.uniprot.org/help/fasta-headers>.
- A proteome identifier (UPID) is `UP` followed by 9 digits. It "is stable across releases and can
  therefore be used to cite a UniProt proteome". UPIDs "generally correspond to one genome assembly",
  but sometimes to more than one (nuclear and mitochondrial components assembled separately).
  Source: <https://rest.uniprot.org/help/proteome_id>.
- The human reference proteome record `UP000005640` names its genome assembly
  (`GCA_000001405.29`, source Ensembl). It also gives a BUSCO report (`complete`, `completeSingle`,
  `completeDuplicated`, `fragmented`, `missing`, `total`, `lineageDb: primates_odb10`), a protein
  count and a gene count. Source: <https://rest.uniprot.org/proteomes/UP000005640.json>, fetched
  2026-10-10.
- UniProt releases are named `YYYY_NN`. The REST API reported `X-UniProt-Release: 2026_03`
  (released 2 September 2026) on 2026-10-10.
- The canonical sequence of an entry follows ordered criteria (functional, widely expressed,
  conserved, consensus with CCDS/MANE, otherwise the longest). "Canonical" is therefore not the same
  as "longest". Source: <https://rest.uniprot.org/help/canonical_and_isoforms>.
- A UniProt proteome download can be a subset that one accession does not fully describe. For
  example, Swiss-Prot entries come with TrEMBL entries, and the canonical set with a separate
  additional-isoform set.

**Implication**: a database source needs, as separate optional values, the database name, its
release, a set identifier such as a UPID, and what was taken. The UPID-to-assembly link is a fact
that UniProt asserts, not a checksum FHP can verify.

## N-02 Ensembl peptide FASTA

- File names follow `<species>.<assembly>.pep.<status>.fa.gz`, where status is `all` (translations
  of Ensembl genes) or `abinitio` (GENSCAN/SNAP predictions, "not all ... represent biologically
  real proteins"). Source: Ensembl `pub/current_fasta/homo_sapiens/pep/README`.
- Each header gives the translation, gene and transcript stable IDs and a location that names the
  assembly, for example `chromosome:NCBI35:1:904515:910768:1`. The Ensembl release is part of the
  download path (`release-NNN`), not part of the file.

**Implication**: the predicted-versus-database distinction is not clean. `pep.all` is a database
release of an annotation pipeline's output. FHP should describe where the set was obtained and,
separately and optionally, the annotation it came from.

## N-03 NCBI RefSeq annotation

- NCBI annotation products carry an Annotation Name that combines the RefSeq assembly accession and
  the year and month the run started, for example `GCF_016801865.2-RS_2022_12`. It is "used
  throughout NCBI as a way to uniquely identify annotation products originating from the same
  annotation run". Source: <https://www.ncbi.nlm.nih.gov/refseq/annotation_euk/process>.
- The annotation pipeline has a version (10.2 and 10.3 in 2024 reports).

**Implication**: an annotation release identifier is a good optional "release" value for a
database-derived set, and the assembly accession inside it is a parent accession, not a checksum.

## N-04 Gene predictors

- Prodigal (prokaryotes) writes protein FASTA whose headers give coordinates and
  `ID=…;partial=00;start_type=ATG;…`. `partial` marks genes truncated at contig edges. The
  translation table is a run option. Sources: Prodigal documentation (NMDC copy) and the Galaxy IUC
  prodigal test data.
- BRAKER, AUGUSTUS and funannotate (eukaryotes) emit protein FASTA translated from their GFF3 or GTF
  gene models. The gene models are the natural parent (FHGFF3), and the genome is the grandparent.
- TransDecoder-style ORF prediction translates transcripts, so the parent is a transcriptome (FHT).
- Whether a terminal `*` is written differs between tools and settings. Internal `*` occurs for
  read-through and pseudogene translations.

**Implication**: prediction software reuses FHR's structured software object (name, version, URI,
command-line options). The parent may be a genome, an annotation or a transcriptome. FHP must not
assume a terminal `*` or forbid internal ones.

## N-05 Genetic codes

The NCBI translation tables have integer IDs 1–6, 9–16 and 21–33. IDs 7, 8 and 17–20 are unused.
Source: <https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi>, fetched 2026-10-10. A
mitochondrial or plastid subset uses a different table from the nuclear one, so a single file can
mix tables.

## N-06 BUSCO

- The short summary is `C:x%[S:y%,D:z%],F:a%,M:b%,n:N`, where C = S + D and n is the number of
  BUSCO groups in the lineage dataset.
- Scores from different lineage dataset versions (odb10, odb12) are not comparable. One assembly
  scored 92.6% on ascomycota_odb10 (n = 1706) and 49.4% on ascomycota_odb12 (n = 2826). Source:
  <https://gitlab.com/ezlab/busco/-/issues/796>. A completeness value therefore needs the lineage
  dataset name and version, the BUSCO version and the mode (`proteins`). Raw counts are preferable
  to percentages.

## N-07 Vocabularies

- Bioschemas has a released `Protein` profile (0.11) for a single protein, and `Dataset` (1.0). It
  has no profile for a protein set or proteome (<https://bioschemas.org/profiles/>, fetched
  2026-10-10). An FHP record is therefore a `Dataset` about proteins, like FHR, which is a `Dataset`
  about a genome.
- EDAM has terms for the format (FASTA, `format_1929`) and data (protein sequence, `data_2976`).
- The IUPAC amino-acid alphabet in FASTA practice includes B, Z, J and X (ambiguity), U
  (selenocysteine), O (pyrrolysine), `*` (stop) and `-` (gap), in upper or lower case.

## N-08 Current FAIR-bioHeaders state

- `schemas/core.yaml` already has `HeaderType` FHP and `DerivedFrom`, with header type, checksum,
  SeqCol, accession and relationship. The relationship vocabulary (`translatedFrom`,
  `filteredFrom`, …) is provisional, with its PROV-O/RO mapping open (#54).
- `DerivedFrom` identifies a parent by its FHR-family checksum. A database release (UniProt, an
  Ensembl release) has no such checksum. A provenance record for external sources must therefore
  differ from `derivedFrom`, or `derivedFrom` would have to allow parents without a checksum.
- The core's required `taxon` is a single object. Multi-species protein sets (UniRef clusters,
  metaproteomes, pan-proteomes) do not fit it.
- The toolkit's FASTA header handling is byte-based and alphabet-independent (R1–R10), but metadata
  validation dispatches only to the FHR schema. `bioheaders assess` already says that FHP is a
  draft. Feature 011 generates JSON-LD terms from LinkML annotations, so FHP slots will need
  annotations and vocabulary terms.
