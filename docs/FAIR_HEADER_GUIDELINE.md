# FAIR header guideline for data files

**Status**: guidance. This page is not normative: it changes no schema and adds no
requirement to `fhr.json`, `schemas/core.yaml` or [FORMAT.md](FORMAT.md). It describes what a
file header should contain so that the file is easier to find, access, interoperate with and
reuse, whatever its format. It is the guideline of feature 010
([specs/010-fair-header-assessment](../specs/010-fair-header-assessment/spec.md)), and the
command `bioheaders assess` in FAIR-bioHeaders-Tools checks files against it.

Use it when you publish FASTA, GFF3, VCF, GAF, GFA or other text files and want their headers
to carry the metadata that otherwise lives only on a landing page or in a file name. Keep the
convention your file type already has: a GFF3 file keeps its `##` directives, a VCF file its
`##key=value` lines and a GAF file its `!key: value` lines. FAIR-bioHeaders lines
(`;~` in FASTA, `#~` in GFA and GFF3) are one way to write a header where a format has none.

The guideline has 8 items. Each item lists the FAIR principles and the RDA FAIR Data Maturity
Model indicators it serves, the shared-core field names (`schemas/core.yaml`; `FHR:` marks a
field that only the FHR schema has), examples in at least two file types, and the indicators
that `bioheaders assess` reports for it ("checks"). Indicators that cannot apply to a header
inside a file are listed under [Out of scope for headers](#out-of-scope-for-headers), with what
to do at repository level instead. There is no score: the assessment reports a status per
indicator, with the header lines it rests on.

## How to read the examples

- **Kind** `surveyed` means the line was copied from a real public download file during the
  survey of 34 provider files (specs/010-fair-header-assessment/research/survey.md). The
  **Source** column names the survey evidence file in `research/headers/`. `illustrative` lines
  show the form only.
- **Key** `native` means the key is the format's own (from its specification or established
  provider practice). `core` means the format has no key for this concept, so the line uses the
  shared-core field name as the key. Core field names are suggested only where no native key
  exists; where a native key exists, use it.
- Text in `<angle brackets>` is a placeholder. Replace it with your own value; never copy the
  example values. In VCF, `<…>` also delimits structured values such as `##contig=<…>`.
- A suggested `core` key in a GFF3, VCF or GAF header is advice to providers, not part of
  those formats' specifications. Readers that do not know the key ignore it.

## Summary of items

| Item | Title | Principles | Indicators | Core fields | Checks |
|---|---|---|---|---|---|
| G1 | Identify this file | F1, F3 | RDA-F1-01D, RDA-F1-02D, RDA-F3-01M | `identifier`, `accessionID`, `checksum`, `seqcol_id` | RDA-F1-01D, RDA-F1-02D, RDA-F3-01M |
| G2 | Describe it for discovery | F2, R1 | RDA-F2-01M, RDA-R1-01M | `FHR:genome`, `taxon`, `version`, `metadataAuthor`, `dateCreated`, `reuseConditions` | RDA-F2-01M, RDA-R1-01M |
| G3 | Declare the format and the header convention, with versions | I1, R1.3 | RDA-I1-01M, RDA-I1-01D, RDA-I1-02M, RDA-R1.3-01M, RDA-R1.3-01D, RDA-R1.3-02M, RDA-R1.3-02D | `schema`, `schemaVersion` | RDA-I1-01M, RDA-I1-01D, RDA-I1-02M, RDA-R1.3-01M, RDA-R1.3-01D, RDA-R1.3-02M, RDA-R1.3-02D |
| G4 | Use identifiers, not labels, for taxa, people and vocabularies | I1, I2, I3 | RDA-I1-02D, RDA-I2-01M, RDA-I2-01D, RDA-I3-01M, RDA-I3-03M | `taxon`, `metadataAuthor`, `FHR:assemblyAuthor`, `scholarlyArticle`, `funding`, `documentation` | RDA-I1-02D, RDA-I2-01M, RDA-I2-01D, RDA-I3-01M, RDA-I3-03M |
| G5 | Say what this file was derived from, and how | I3, R1.2 | RDA-I3-01D, RDA-I3-02M, RDA-I3-02D, RDA-I3-04M, RDA-R1.2-02M | `derivedFrom`, `headerType`, `relationship`, `checksum`, `seqcol_id`, `accessionID` | RDA-I3-02M, RDA-I3-04M, RDA-R1.2-02M |
| G6 | Record provenance: who, when, from what | R1.2 | RDA-R1.2-01M | `metadataAuthor`, `dateCreated`, `version`, `derivedFrom`, `FHR:assemblySoftware` | RDA-R1.2-01M |
| G7 | State a standard licence | R1.1 | RDA-R1.1-01M, RDA-R1.1-02M, RDA-R1.1-03M | `reuseConditions` | RDA-R1.1-01M, RDA-R1.1-02M, RDA-R1.1-03M |
| G8 | Say where to get the data | A1, A1.1 | RDA-A1-01M, RDA-A1-03D, RDA-A1-04D, RDA-A1-05D, RDA-A1.1-01D | `relatedLink`, `accessionID`, `identifier` | RDA-A1-01M, RDA-A1-03D, RDA-A1-04D, RDA-A1-05D, RDA-A1.1-01D |

RDA-I3-01D and RDA-I3-02D concern references inside the data records, not the header. They
belong to G5 but are not assessed in the first release (`not assessed`, reason
`deferred-data-body`), so they are not among its checks. RDA-A1-03D, RDA-A1-04D, RDA-A1-05D
and RDA-A1.1-01D are assessed only with `bioheaders assess --online`; otherwise they are
reported as `not assessed` (`online-check-not-requested`).

## G1. Identify this file

State an identifier of this file's own data: a persistent identifier (a DOI, or a versioned
accession of this file's data in a registered scheme) and, where the format defines one, a
digest of the content (the FHR `checksum`, or a SeqCol digest in `seqcol_id`). A name such as
`GRCh38` is a label, not an identifier. In a derived file, the accession of the *parent*
assembly identifies the parent, not this file: record it under G5, not here. None of the 34
surveyed files states an identifier of its own data.

| File type | Convention | Example | Kind | Key | Source |
|---|---|---|---|---|---|
| FASTA | FAIR-bioHeaders | `;~identifier: [<persistent identifier of this file, e.g. a DOI>]` | illustrative | native | illustrative |
| FASTA | FAIR-bioHeaders | `;~checksum: <FHR checksum, written by bioheaders combine>` | illustrative | native | illustrative |
| GFF3 | GFF3 #! | `#!identifier <persistent identifier of this file, e.g. a DOI>` | illustrative | core | illustrative |
| VCF | VCF ## | `##identifier=<persistent identifier of this file, e.g. a DOI>` | illustrative | core | illustrative |
| GAF | GAF ! | `!identifier: <persistent identifier of this file, e.g. a DOI>` | illustrative | core | illustrative |

Checked by RDA-F1-01D (persistent identifier), RDA-F1-02D (globally unique identifier or
digest) and RDA-F3-01M (the header includes the identifier).

## G2. Describe it for discovery

Give the elements a search needs: what the data is about (for a genome, `FHR:genome`), the
taxon, the version or release of the data, who made it, when, and the licence (G7). The
release of a file often appears only in its path or name; put it in the header too, because
the name changes when the file is copied.

| File type | Convention | Example | Kind | Key | Source |
|---|---|---|---|---|---|
| GFF3 | GFF3 ## | `##species https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=6239` | surveyed | native | `ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff` |
| VCF | VCF ## | `##source=ensembl;version=116;url=https://e116.ensembl.org/homo_sapiens` | surveyed | native | `ensembl_vcf_homo_sapiens-chrMT.vcf` |
| VCF | VCF ## | `##contig=<ID=I,assembly=WBcel235,species="Caenorhabditis elegans">` | surveyed | native | `alliance_vcf_VCF-GZ_WBcel235_38.vcf` |
| FASTA | FAIR-bioHeaders | `;~version: <version or release of this file's data, e.g. WS298>` | illustrative | native | illustrative |
| GAF | GAF ! | `!version: <version or release of this file's data, e.g. WS298>` | illustrative | core | illustrative |

Checked by RDA-F2-01M (discovery elements) and RDA-R1-01M (reuse attributes: version,
creator, date, licence, taxon and source data).

## G3. Declare the format and the header convention, with versions

Declare the data format and its version on the first line, as the format specifies. If the
file carries a FAIR-bioHeaders header, name its schema and schema version so that the header
can be validated (`bioheaders validate`). FASTA has no format declaration of its own; a
FAIR-bioHeaders header is the way to declare one.

| File type | Convention | Example | Kind | Key | Source |
|---|---|---|---|---|---|
| GFF3 | GFF3 ## | `##gff-version 3` | surveyed | native | `ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff` |
| GFF3 | GFF3 #! | `#!gff-spec-version 1.21` | surveyed | native | `ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff` |
| VCF | VCF ## | `##fileformat=VCFv4.3` | surveyed | native | `alliance_vcf_VCF-GZ_WBcel235_38.vcf` |
| GAF | GAF ! | `!gaf-version: 2.2` | surveyed | native | `go_gaf_wb.gaf` |
| FASTA | FAIR-bioHeaders | `;~schema: <schema URL of the header type, e.g. the raw-main URL of fhr.json>` | illustrative | native | illustrative |
| FASTA | FAIR-bioHeaders | `;~schemaVersion: <schema version the header follows>` | illustrative | native | illustrative |

Checked by RDA-I1-01M (a published header convention), RDA-I1-01D (the data format is
declared with its version), RDA-I1-02M (header keys mapped to IRIs, for example by a JSON-LD
context), RDA-R1.3-01M (the header meets its convention; for FHR, schema validation),
RDA-R1.3-01D (a sample of records parses), RDA-R1.3-02M (the convention has a
machine-readable schema) and RDA-R1.3-02D (a listed community format, declared with its
version).

## G4. Use identifiers, not labels, for taxa, people and vocabularies

Where a value names something that has an identifier, give the identifier: a taxon as an
`https://identifiers.org/taxonomy:<id>` IRI, people with an ORCID iD, articles with a DOI,
funders and grants with their identifiers, and the release of the ontologies the records use
(Sequence Ontology for GFF3 feature types, Gene Ontology for GAF). A taxon page URL with a
query string, or a species name alone, is a label. Formats that type their own fields, such as
VCF `##INFO` lines, already describe the data in a machine-readable way.

| File type | Convention | Example | Kind | Key | Source |
|---|---|---|---|---|---|
| GFF3 | GFF3 ## | `##feature-ontology ftp://ftp.flybase.org/releases/FB2026_03/precomputed_files/ontologies/so.obo.gz` | surveyed | native | `flybase_gff3_dmel-all-r6.69.gff` |
| GAF | GAF ! | `!go-version: http://purl.obolibrary.org/obo/go/releases/2026-08-02/extensions/go-plus.ofn` | surveyed | native | `alliance_gaf_GAF_WB_1.gaf` |
| VCF | VCF ## | `##INFO=<ID=E_Freq,Number=0,Type=Flag,Description="Frequency.https://www.ensembl.org/info/genome/variation/prediction/variant_quality.html#evidence_status">` | surveyed | native | `ensembl_vcf_homo_sapiens-chrMT.vcf` |
| GFF3 | GFF3 ## | `##species https://identifiers.org/taxonomy:<NCBI taxon id>` | illustrative | native | illustrative |
| FASTA | FAIR-bioHeaders | `;~metadataAuthor: [{name: <author name>, uri: <ORCID iD URL of the author>}]` | illustrative | native | illustrative |

Checked by RDA-I1-02D (typed definitions of the data's fields), RDA-I2-01M (values from
FAIR vocabularies), RDA-I2-01D (the vocabularies of the records are declared), RDA-I3-01M
(references to other metadata) and RDA-I3-03M (qualified references, such as an author with
an ORCID iD).

## G5. Say what this file was derived from, and how

A derived file (an annotation, a variant file, transcript or protein sequences) should
record the data it was derived from in a way that can be checked: a versioned assembly
accession, the FHR checksum or SeqCol digest of the parent file, or one MD5 per reference
sequence in VCF `##contig` lines. State the relationship too (for example, this file annotates
the genome). A name alone, such as `##reference=GRCh38`, is partial, and a URL of a directory
does not identify one file. Matching sequence names and lengths are only circumstantial
evidence; `bioheaders assess --related GENOME` reports them separately from the recorded link
and verifies the recorded link against the genome.

| File type | Convention | Example | Kind | Key | Source |
|---|---|---|---|---|---|
| GFF3 | GFF3 #! | `#!genome-build-accession NCBI_Assembly:GCF_000002985.6` | surveyed | native | `ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff` |
| GFF3 | GFF3 #! | `#!genome-build-accession GCA_000001405.29` | surveyed | native | `ensembl_gff3_Homo_sapiens.GRCh38.116.chr.gff3` |
| VCF | VCF ## | `##reference=https://ftp.ensembl.org/pub/release-116/fasta/homo_sapiens/dna/` | surveyed | native | `ensembl_vcf_homo_sapiens-chrMT.vcf` |
| VCF | VCF ## | `##contig=<ID=<sequence name>,length=<sequence length>,md5=<MD5 of the sequence>>` | illustrative | native | illustrative |
| FASTA | FAIR-bioHeaders | `;~derivedFrom: [{headerType: FHR, relationship: <relationship, e.g. transcribedFrom>, checksum: <FHR checksum of the parent genome file>}]` | illustrative | native | illustrative |

The `derivedFrom` slot and its relationship vocabulary are provisional (FAIR-bioHeaders-Specification#54),
and FHR does not include `derivedFrom` in v0.3 (`schemaVersion` 1) or v0.4 (`"2.0"`); the
released FHP and FHGFF3 headers use it, and the transcript (FHT) header remains a legacy
draft. Until a PROV-O or Relation Ontology mapping is
published, RDA-R1.2-02M can be at most partially evidenced.

Checked by RDA-I3-02M (a reference to other data), RDA-I3-04M (a qualified reference: an
identifier and the relationship) and RDA-R1.2-02M (provenance in a cross-community
language).

## G6. Record provenance: who, when, from what

Record who produced the file (a person, organisation or pipeline, and the software), when it
was produced, and from what source data. Use the date form the convention specifies (VCF
`##fileDate` is `YYYYMMDD`); elsewhere use ISO 8601. In a GAF file, the first header block is
the file's own; blocks copied from upstream files are upstream provenance.

| File type | Convention | Example | Kind | Key | Source |
|---|---|---|---|---|---|
| GFF3 | GFF3 #! | `#!processor NCBI annotwriter` | surveyed | native | `ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff` |
| GFF3 | GFF3 #! | `#!annotation-source WormBase WS298` | surveyed | native | `ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff` |
| GFF3 | GFF3 #! | `#!date-produced 2026-09-26T20:54:41+00:00` | surveyed | native | `alliance_gff3_GFF_HUMAN_0.gff` |
| VCF | VCF ## | `##fileDate=20260404` | surveyed | native | `ensembl_vcf_homo_sapiens-chrMT.vcf` |
| VCF | VCF ## | `##source=AGR VCF File generator` | surveyed | native | `alliance_vcf_VCF-GZ_WBcel235_38.vcf` |
| GAF | GAF ! | `!generated-by: UniProt` | surveyed | native | `alliance_gaf_GAF_WB_1.gaf` |
| GAF | GAF ! | `!date-generated: 2026-08-04 15:14` | surveyed | native | `alliance_gaf_GAF_WB_1.gaf` |
| FASTA | FAIR-bioHeaders | `;~dateCreated: <ISO 8601 date the file was produced>` | illustrative | native | illustrative |

Checked by RDA-R1.2-01M (provenance under keys the convention defines: who, when, from what).

## G7. State a standard licence

State the licence under which the data can be reused, as an SPDX licence identifier (or the
canonical URL of a standard licence). An SPDX identifier is both standard and
machine-understandable. None of the 34 surveyed files states a licence, and none of GFF3, VCF
or GAF has a licence key, so the examples use the core field name `reuseConditions`.

| File type | Convention | Example | Kind | Key | Source |
|---|---|---|---|---|---|
| FASTA | FAIR-bioHeaders | `;~reuseConditions: <SPDX licence identifier, e.g. CC-BY-4.0>` | illustrative | native | illustrative |
| GFF3 | GFF3 #! | `#!reuseConditions <SPDX licence identifier, e.g. CC-BY-4.0>` | illustrative | core | illustrative |
| VCF | VCF ## | `##reuseConditions=<SPDX licence identifier, e.g. CC-BY-4.0>` | illustrative | core | illustrative |
| GAF | GAF ! | `!reuseConditions: <SPDX licence identifier, e.g. CC-BY-4.0>` | illustrative | core | illustrative |

Checked by RDA-R1.1-01M (a licence statement), RDA-R1.1-02M (a standard licence) and
RDA-R1.1-03M (a machine-understandable licence).

## G8. Say where to get the data

Say where this file can be obtained again: a download URL, or an accession together with its
resolver URL. A copy that has travelled away from its download site can then be traced back.
No surveyed file states where the file itself can be downloaded.

| File type | Convention | Example | Kind | Key | Source |
|---|---|---|---|---|---|
| FASTA | FAIR-bioHeaders | `;~relatedLink: [<URL where this file can be downloaded>]` | illustrative | native | illustrative |
| FASTA | FAIR-bioHeaders | `;~accessionID: {name: <accession of this file's data>, url: <resolver URL of the accession>}` | illustrative | native | illustrative |
| GFF3 | GFF3 #! | `#!relatedLink <URL where this file can be downloaded>` | illustrative | core | illustrative |
| VCF | VCF ## | `##relatedLink=<URL where this file can be downloaded>` | illustrative | core | illustrative |

Checked by RDA-A1-01M (the header says how to get the data, offline) and, only with
`bioheaders assess --online`, RDA-A1-03D (the identifier resolves), RDA-A1-04D (the URL works
over a standard protocol), RDA-A1-05D (it can be retrieved without interaction) and
RDA-A1.1-01D (over a free, open protocol). The online checks send only the identifier or URL
from the header, never file contents.

## How to express each item in your existing convention

| Convention | Header lines | Where an item has a native key | Where it has none |
|---|---|---|---|
| GFF3 | `##` directives from the GFF3 specification, then `#!` pragmas (NCBI, Ensembl and Alliance practice), before the first feature | Use the directive or the established pragma, for example `##species`, `##feature-ontology`, `#!genome-build-accession`, `#!processor`, `#!date-produced` | `#!<core field name> <value>`, for example `#!reuseConditions` |
| VCF | `##key=value` meta-information lines after `##fileformat` | Use the VCF key, for example `##fileDate`, `##source`, `##reference`, and `##contig=<ID=…,length=…,md5=…>` | `##<core field name>=<value>` |
| GAF | `!key: value` lines after `!gaf-version`; the first block is the file's own | Use the GAF key, for example `!generated-by`, `!date-generated`, `!go-version` | `!<core field name>: <value>` |
| FASTA | No native header; deflines describe single records | Not applicable | FAIR-bioHeaders `;~` lines before the first `>`: FHR for genomes (`bioheaders combine` writes a complete header); FHP for proteins is released in v0.4.0; FHT for transcripts is a legacy draft |
| GFA | No native header metadata | Not applicable | FAIR-bioHeaders `#~` lines (FHR) |
| Other text formats | The format's own comment lines | Use the format's own key | A FAIR-bioHeaders-style `key: value` line in the format's comment syntax |

Put metadata in the header, not only in file names, directory names or landing pages: names
change when files are copied, and landing pages do not travel with the file. Keep one value
per concept; two different values for the same concept (for example two assembly accessions)
are reported as conflicting.

## Out of scope for headers

These 10 indicators are about a metadata record separate from the data, or about the service
that distributes it. A header inside a file cannot meet them, so `bioheaders assess` reports
them as `not applicable` with the reason below. Meet them at repository level instead.

| Indicator | Reason | Repository-level action |
|---|---|---|
| RDA-F1-01M | `embedded-metadata` | Give the metadata record (landing page or registry entry) its own persistent identifier, for example a DOI for the release |
| RDA-F1-02M | `embedded-metadata` | Make the metadata record's identifier globally unique, as above; the header shares the identity of its file (G1) |
| RDA-F4-01M | `repository-level` | Register the files or their landing pages with a searchable index, such as the provider's search, a data repository or a Bioregistry-resolvable accession |
| RDA-A1-02M | `embedded-metadata` | Keep the landing page readable without special software; anyone holding the file can already read its text header |
| RDA-A1-02D | `object-in-hand` | Keep the download location documented on the landing page; inside the file, state it under G8 |
| RDA-A1-03M | `embedded-metadata` | Make the metadata record's identifier resolve to the record, for example a DOI resolving to the landing page |
| RDA-A1-04M | `embedded-metadata` | Serve the metadata record over a standard protocol such as HTTPS |
| RDA-A1.1-01M | `embedded-metadata` | Serve the metadata record over a free, open protocol such as HTTPS |
| RDA-A1.2-01D | `repository-level` | Where access must be controlled, use a distribution service that supports authentication and authorisation |
| RDA-A2-01M | `repository-level` | Deposit the header metadata in a durable record (an archive landing page or registry entry) that outlives the file, and point to it with `relatedLink` |

## Licence and attribution

This guideline is licensed MPL-2.0, like the rest of this repository (see
[LICENSE](../LICENSE) and CONTRIBUTING.md). Surveyed example lines are short factual metadata
from public download files; their sources are listed in
specs/010-fair-header-assessment/research/survey.md.

Indicator identifiers and titles from: FAIR Data Maturity Model Working Group (2020). FAIR
Data Maturity Model. Specification and Guidelines. Research Data Alliance.
doi:10.15497/rda00050. Licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
File-header interpretations are adaptations by FAIR-bioHeaders and are not endorsed by the RDA.
