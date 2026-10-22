# FAIR-bioHeaders Specification

[![Specification checks](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/actions/workflows/validate-specification.yml/badge.svg?branch=main)](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/actions/workflows/validate-specification.yml)
[![Schema drift checks](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/actions/workflows/check-schema-drift.yml/badge.svg?branch=main)](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/actions/workflows/check-schema-drift.yml)
[![Specification DOI](https://img.shields.io/badge/Specification_DOI-10.5281%2Fzenodo.6762549-blue)](https://doi.org/10.5281/zenodo.6762549)
[![File Converter DOI](https://img.shields.io/badge/File_Converter_DOI-10.5281%2Fzenodo.6762547-blue)](https://doi.org/10.5281/zenodo.6762547)

This repository holds the released FAIR-bioHeaders specifications: FHR (reference
genomes), FHP (protein FASTA) and FHGFF3 (GFF3 annotation) headers, the
shared core schema, the format rules, the JSON-LD context and vocabulary, and the
conformance suite. It was called `FHR-Specification` until 2026-10-14 (#108).

A short machine-readable overview for AI assistants is in [`llms.txt`](llms.txt).

Development of each header type happens in its own repository, and finished work
comes here by pull request:

| Header type | Development repository |
| --- | --- |
| FHR | [FHR-Specification](https://github.com/FAIR-bioHeaders/FHR-Specification) |
| FHP | [FHP-Specification](https://github.com/FAIR-bioHeaders/FHP-Specification) |
| FHT | [FHT-Specification](https://github.com/FAIR-bioHeaders/FHT-Specification) |
| FHGFF3 | [FHGFF3](https://github.com/FAIR-bioHeaders/FHGFF3) |

Schema URLs under the old name
(`https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json`
and the like) keep working and are recognised by the tools; new files should cite a
versioned w3id URL (see [SCHEMA-VERSIONS](docs/SCHEMA-VERSIONS.md)).

FHR (FAIR Header Reference genome) keeps machine-readable and human-readable
provenance with reference genome data. This repository defines the JSON Schema,
LinkML model, examples, and partial MIxS/MIGS mappings. The
[FAIR-bioHeaders toolkit](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools)
provides conversion, validation, and FASTA/GFA/GFF3 header tools.

## Draft metadata crosswalks

The [mapping-profile proposal](docs/mappings/README.md) starts issue #56 with
a separate assembly export context, qualified Dublin Core fixture and a delivery
matrix for DataCite, Crossref, ARK and bibliographic profiles. It is incomplete
and not an adopted mapping/export suite; FHT remains blocked on its contract.

## Proposed shared amendments

The [shared voucher descriptions proposal](docs/proposals/shared-voucher-descriptions.md)
preserves free text and specifies an optional structured alternative for family-wide
review. It is not yet supported by the released schemas.

The [community profiles proposal](docs/PROFILES.md) lets a community add
required fields and naming rules on top of a header type without editing the
published schemas, with a draft AgBioData example under
[`profiles/`](profiles/). It is a proposal; no profile is adopted and the
published contracts are unchanged.

## Metadata

The v0.3 release added optional fields and fixed examples; the required metadata
set and numeric `schemaVersion: 1` were unchanged in that release. Package/release version,
schema version, and assembly `version` are distinct. From v0.4 `schemaVersion` is a
`"MAJOR.MINOR"` string (FHR `"2.0"`, FHP and FHGFF3 `"1.0"`), and a file's `schema` URL
selects the schema it is checked against: see [schema versions](docs/SCHEMA-VERSIONS.md). Known gaps between the normative text and what the 2.0/1.0 schemas can express, with their
status and target release, are in [the schema-contract gap audit](docs/SCHEMA-GAP-AUDIT.md).

Required fields: `schema`, `schemaVersion`, `genome`, `taxon`, `version`,
`metadataAuthor`, `assemblyAuthor`, `dateCreated`, `masking`, and `checksum`.
See [the minimal instance](examples/minimal.fhr.json), the field definitions and
descriptions in [`fhr.json`](fhr.json), and [the format and compatibility rules](docs/FORMAT.md).
Top-level unknown fields are
rejected by the schema. From v0.4 nested objects (`taxon`, authors,
`accessionID`, `vitalStats`, software provenance) reject unknown keys too; see
[the v0.4 schema changes](docs/SCHEMA-CHANGES-v0.4.md).

The [rich YAML example](examples/example.fhr.yaml) shows optional
`assemblySoftware`, `assemblyProtocol`, `vitalStats.N90`, `vitalStats.gcContent`,
and `seqcol_id`. A legacy software name string remains valid. GC content uses a
percentage from 0 to 100; N90 uses base pairs. SeqCol digests are supplied by users
and have a different identity/algorithm from the FHR file checksum.

Checksum helpers require SHA-512/256 support in the Python build. Some Apple
system Python builds omit it; use an OpenSSL-enabled Python distribution.
Metadata conversion and validation do not require that hash implementation.

## Serialization and checksums

YAML is embedded in FASTA comments with `;~` and GFA comments with `#~`; the prefix
is removed to recover YAML. JSON/YAML and HTML microdata can store the same
metadata separately. See [the HTML example](examples/example.microdata.fhr.html)
and [microdata guidance](docs/MICRODATA.md). The [JSON-LD form](docs/JSONLD.md)
([example](examples/example.fhr.jsonld)) is the FHR record plus a JSON-LD context
that maps every field to schema.org or a [FAIR-bioHeaders term](docs/TERMS.md), so
the same document is linked data. A separate, one-way [schema.org export](docs/SCHEMAORG-EXPORT.md)
([example](examples/example.fhr.export.jsonld)) splits the record into typed entities (assembly,
metadata record, assembly activity, statistics, grant, article) for search engines and Bioschemas
tools.

The checksum policy, adopted in v0.3 and unchanged in v0.4, is base64 SHA-512/256 over the exact file bytes except
the scalar FHR checksum line (including that line's newline). Metadata, ordinary
comments, and sequence bytes all contribute. [Checksum and migration details](docs/FORMAT.md)
explain the change from the old MD5/payload-only documentation.

[Conformance vectors](conformance/README.md) give valid and invalid FASTA/GFA
files, with expected checksums, for the header parsing and checksum rules. Use
them to test other FHR implementations.

[Tool compatibility](docs/TOOL_COMPATIBILITY.md) records how common FASTA, GFA
and GFF3 tools handle files with FHR headers, and gives workarounds. Most
FASTA indexers, including samtools faidx, need a stripped copy.

The [FAIR header guideline](docs/FAIR_HEADER_GUIDELINE.md) is guidance for the
headers of any data file (FASTA, GFF3, VCF, GAF, GFA and others), organised as 8
items mapped to the RDA FAIR Data Maturity Model indicators, with examples in
each format's own convention. It changes no schema. `bioheaders assess` in
FAIR-bioHeaders-Tools reports a checklist against it, and the
[assessment fixtures](assessment/README.md) let other implementations test the
same expected outcomes.

JSON/YAML/HTML examples contain synthetic checksum and SeqCol placeholders.
The FASTA/GFA examples have verified FHR file checksums but retain a synthetic
SeqCol placeholder; it must not be used as the sequence collection's identity.

## Validation and LinkML

Use Python 3.13 or later for repository checks. The cross-repo `check_release.py`
command requires a companion FAIR-bioHeaders-Tools checkout at the supplied path:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-linkml.txt
python -m unittest discover -s tests -v
python scripts/validate_examples.py
python scripts/check_linkml.py
python scripts/check_schema_drift.py
python scripts/check_release.py --converter ../FAIR-bioHeaders-Tools
python scripts/check_conformance.py --converter ../FAIR-bioHeaders-Tools
python json-schema-generator.py --output /tmp/fhr_linkml.json
python scripts/project_mixs.py examples/example.fhr.json
```

CI checks JSON/YAML examples, the explicit schema review baseline, and LinkML
validation equivalence. Generation uses pinned LinkML 1.11.1, closes every
nested object, writes `schemaVersion` as an enum (`["2.0"]` for FHR), and pins checksum length
constraints. Equivalence checking
resolves local references and compares validation keywords, ignoring descriptive
annotations and ordering of required fields. Generated output does not overwrite
the published `fhr.json`. [MIxS/MIGS mapping limits](docs/MAPPINGS.md) include
partial/lossy terms and omissions; the output is not a complete MIGS submission.
The [JSON-LD and DCMI mapping table](mappings/fhr-jsonld-dcmi.yml) gives every FHR
field's JSON-LD term and its Dublin Core (DCMI Terms) equivalents, with mapping kinds,
conditions and losses ([summary](docs/MAPPINGS.md#json-ld-and-dublin-core-dcmi-terms)).

### Schema files

- `fhr.json`: the published FHR JSON Schema (the contract).
- `schemas/core.yaml`: the LinkML core shared by the FAIR-bioHeaders family
  (`schema`, `schemaVersion`, `taxon`, `version`, `metadataAuthor`,
  `dateCreated`, `checksum` and the optional provenance slots, plus `Taxon`,
  `Author`, `AccessionID`, the `sha2` type and `seqcol_id`). It also defines a
  provisional `DerivedFrom` class and `derivedFrom` slot that link a file to a
  parent by checksum; the FHR contract does not use them.
- `schemas/versions.json`: the schema version of each header type in each release, read by
  tools that select schemas ([schema versions](docs/SCHEMA-VERSIONS.md)).
- `fhr_linkml.yml`: the FHR LinkML model. It imports the core and adds FHR-only
  slots (`genome`, `assemblyAuthor`, `masking`, `vitalStats`, ...).
- `fhp_linkml.yml` and `fhp.json`: the FHP header for protein FASTA
  (proteomes and protein sets). The LinkML model imports the core, and the JSON
  Schema is generated from it. The format is described in [docs/FHP.md](docs/FHP.md),
  with examples in [examples/fhp/](examples/fhp/). FHP is released in v0.4.0 with
  `schemaVersion` `"1.0"`; the spec's "v0.1" label is a document status, not a schema version.
  See [specs/006-protein-header](specs/006-protein-header/spec.md).
- `fhgff3_linkml.yml` and `fhgff3.json`: the FHGFF3 header for GFF3
  annotations, placed after `##gff-version 3`. The record links the annotation to
  its genome, by FHR checksum or by accession plus SeqCol digest. The LinkML model
  imports the core and `schemas/shared.yaml` (software, sources and BUSCO
  completeness, shared with FHP), and the JSON Schema is generated from it. See
  [docs/FHGFF3.md](docs/FHGFF3.md) and [examples/fhgff3/](examples/fhgff3/). FHGFF3 is
  released in v0.4.0 with `schemaVersion` `"1.0"`; the spec's "v0.1" label is a document
  status, not a schema version. See
  [specs/007-gff3-header](specs/007-gff3-header/spec.md).
- `tests/fixtures/fhp_stub.yaml`: a test-only stub showing how a new header type
  imports the core.
- `profiles/`: the draft [community profile](docs/PROFILES.md) mechanism, the
  worked AgBioData FHR example and its conformance cases. A proposal only; it
  does not change any published schema.

For intentional schema edits, explain compatibility and update the review baseline:

```bash
python scripts/check_schema_drift.py --update
```

Commit the baseline with the schema/model changes, synchronize both converter
schema copies, and run every check. Require `schema-drift` and `validate` checks in
branch protection to block failing merges. Whitespace/key order do not count as
drift; other JSON changes require an explicit update and maintainer review.

## Project guidance

See [CONTRIBUTING](CONTRIBUTING.md), [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md),
[SECURITY](SECURITY.md), and [AGENTS](AGENTS.md). David and Adam retain schema
authority; [GOVERNANCE](GOVERNANCE.md) describes the current two-maintainer model and a future steering-group option that is not active.
The [schema diagram](Diagram.svg) is generated with
`python scripts/render_diagram.py` and summarizes required and optional fields.
[Release notes](CHANGELOG.md) document compatibility and deferred work.

## Citing FHR

Chicago bibliography entries are used below. Cite the published paper for a
general description of FHR; cite the specification or converter when using that
resource directly. The software and specification links are concept DOIs; for a
specific release, use the corresponding version DOI from Zenodo. Authors and
years follow the published records resolved by the concept DOIs, and can change as later records are published.

### Published paper

Wright, Adam, Mark D. Wilkinson, Christopher Mungall, Scott Cain, Stephen Richards, Paul Sternberg, Ellen Provin, Jonathan L. Jacobs, Scott Geib, Daniela Raciti, Karen Yook, Lincoln Stein, and David C. Molik. “FAIR Header Reference Genome: A TRUSTworthy Standard.” *Briefings in Bioinformatics* 25, no. 3 (2024): bbae122. https://doi.org/10.1093/bib/bbae122.

### Specification

Molik, David, and Adam Wright. *FHR Specification*. Data set. 2026. https://doi.org/10.5281/zenodo.6762549.

### Converter

Molik, David, and Adam Wright. *FHR File Converter*. Computer software. 2026. https://doi.org/10.5281/zenodo.6762547.

Machine-readable entries are maintained in
[FHR-Citation](https://github.com/FAIR-bioHeaders/FHR-Citation/blob/main/citation.bib).

## Licensing

[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)

New project contributions from March 2025 onward use [MPL-2.0](LICENSE). David Molik left USDA in February 2025. Historical USDA public-domain material remains public domain within the United States; its original notice is preserved in LICENSE. Previously granted permissions and third-party terms remain intact. The project includes both historical material and subsequent MPL-2.0 contributions; file notices and history identify provenance.
