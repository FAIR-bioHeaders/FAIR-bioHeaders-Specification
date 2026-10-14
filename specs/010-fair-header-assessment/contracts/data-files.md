# Contract: data file formats

**Feature**: 010-fair-header-assessment | Research: R-13, R-18, R-19 | Model: [data-model.md](../data-model.md)

Every data file below is UTF-8 JSON (no comments, no duplicate keys) and validated by a JSON
Schema in CI. Each file carries a SemVer version, and every report records that version (FR-009).
The version rules:
- **patch**: wording only.
- **minor**: an added key, form, concept or suggestion; statuses can only rise.
- **major**: a changed rule; any status may change.

| File (FAIR-bioHeaders-Tools) | Schema | Owner of meaning |
|---|---|---|
| `bioheaders/assess/data/rubric.json` | [rubric.schema.json](rubric.schema.json) | This feature. Its interpretations must agree with FAIR-bioHeaders-Specification `docs/FAIR_HEADER_GUIDELINE.md` (cross-check task in tasks.md) |
| `bioheaders/assess/data/synonyms.json` | [synonyms.schema.json](synonyms.schema.json) | This feature. The keys come from [research/survey.md §4](../research/survey.md) |
| `bioheaders/assess/data/reference/spdx-licenses.json` | inline (below) | SPDX licence list, pinned |
| `bioheaders/assess/data/reference/id-schemes.json` | inline (below) | Curated from Bioregistry and identifiers.org, pinned |
| `bioheaders/assess/data/reference/formats.json` | inline (below) | FAIRsharing format records, pinned |
| `bioheaders/assess/data/assessment-report.schema.json` | (is a schema) | Byte-identical to [assessment-report.schema.json](assessment-report.schema.json) |

| File (FAIR-bioHeaders-Specification) | Schema | Purpose |
|---|---|---|
| `assessment/manifest.json` | `assessment/manifest.schema.json` (below) | Expected outcomes of the shared fixtures |
| `assessment/pairs.tsv` | (below) | Pairs file used by the batch fixture run |

---

## 1. `rubric.json`

```json
{
  "rubric_version": "1.0.0",
  "source": {
    "title": "FAIR Data Maturity Model. Specification and Guidelines",
    "version": "1.0",
    "doi": "10.15497/rda00050",
    "licence": "CC-BY-4.0"
  },
  "attribution": "Indicator identifiers and titles from: FAIR Data Maturity Model Working Group (2020). FAIR Data Maturity Model. Specification and Guidelines. Research Data Alliance. doi:10.15497/rda00050. Licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). File-header interpretations are adaptations by FAIR-bioHeaders and are not endorsed by the RDA.",
  "indicators": [
    {
      "id": "RDA-I3-04M",
      "title": "Metadata include qualified references to other data",
      "principle": "I3",
      "priority": "useful",
      "target": "metadata",
      "assessability": "offline",
      "interpretation": "Adapted: the header refers to the data this file was derived from by an identifier (checksum, SeqCol digest, versioned accession, URL) and states the relationship. A name alone is partial. Matching sequence names is circumstantial and not credited.",
      "conditions": [
        {"id": "identifier-reference", "concept": "related-data-identifier", "description": "checksum, seqcol, sequence-digests, accession or url link"},
        {"id": "relationship-stated", "concept": "related-data-relationship"}
      ],
      "evidenced_when": "all",
      "partial_when": "any",
      "check": "derived-link",
      "guideline_item": "G5",
      "suggestions": {
        "gff3-pragma": {
          "text": "Record the accession of the assembly this annotation describes, so that the genome can be identified exactly.",
          "line": "#!genome-build-accession NCBI_Assembly:<versioned assembly accession, e.g. GCF_000002985.6>"
        },
        "vcf-meta": {
          "text": "Give each contig the MD5 of its reference sequence, or name the reference by accession.",
          "line": "##contig=<ID={related.name},length={related.length},md5={related.md5}>"
        },
        "fair-bioheaders": {
          "text": "Add a derivedFrom entry that names the parent by checksum and states the relationship.",
          "line": "#~derivedFrom: [{headerType: FHR, relationship: annotates, checksum: <FHR checksum of the genome file>}]"
        }
      }
    },
    {
      "id": "RDA-A2-01M",
      "title": "Metadata is guaranteed to remain available after data is no longer available",
      "principle": "A2",
      "priority": "essential",
      "target": "metadata",
      "assessability": "not_applicable",
      "reason": "repository-level",
      "interpretation": "Adapted: embedded metadata disappears with the file by construction. Deposit the header in a durable record (landing page or archive) as well.",
      "guideline_item": "out-of-scope"
    }
  ]
}
```

**Rules** (enforced by the schema plus a tool test):
- `evidenced_when` and `partial_when` are `all`, `any`, `never`, `{"min": n}`, or a named list
  `{"any_of": [condition ids]}` / `{"all_of": [condition ids]}`. Placeholders are written
  `<label, e.g. example>`: they contain a space and an example, which tells them apart from VCF
  `<ID=…>` structures.
- There are exactly 41 indicators, with unique ids equal to the RDA Table 1 set. Of them, 25
  are `offline`, 4 `online`, 10 `not_applicable` and 2 `deferred`.
- `offline` and `online` indicators have conditions, rules and a `fair-bioheaders` suggestion.
  `not_applicable` indicators have a reason and `guideline_item: out-of-scope`.
- Every `concept` and `form` referenced must exist in `synonyms.json`.
- Suggestion `line` templates may use `{value}`, `{related.<field>}` (`name`, `length`, `md5`,
  `checksum`, `seqcol_id`, `accession`) or a placeholder written `<…>`. A template must never
  contain a literal identifier, licence, author or date, except as an example inside a
  placeholder (FAIR-bioHeaders-Specification constitution IV).
- Named checks (`derived-link`, `fhr-conformance`, `format-declared`, `record-sample-parse`,
  `resolve`) are implemented in code. Their conditions are still listed, so that a reviewer can
  follow the rule.

## 2. `synonyms.json`

```json
{
  "synonyms_version": "1.0.0",
  "normalisation": {
    "casefold": true,
    "fold_separators": ["-", "_", " "],
    "split_camel_case": true,
    "strip_trailing_colon": true
  },
  "forms": {
    "insdc-assembly-accession": {
      "pattern": "(?:NCBI_Assembly:)?GC[AF]_\\d{9}\\.\\d+",
      "description": "Versioned INSDC/RefSeq assembly accession, optional NCBI prefix",
      "identifier": true
    },
    "spdx-id": {
      "pattern": "[A-Za-z0-9.+-]+",
      "description": "SPDX licence identifier",
      "reference_table": "spdx-licenses",
      "identifier": true
    }
  },
  "concepts": {
    "assembly-accession": {
      "description": "Accession of the assembly a derived file refers to",
      "keys": {
        "gff3-pragma": ["genome-build-accession"],
        "vcf-meta": ["reference"],
        "vcf-contig": ["assembly"],
        "fair-bioheaders": ["derivedFrom.accessionID"]
      },
      "forms": ["insdc-assembly-accession"],
      "scope": "file",
      "core_field": "derivedFrom.accessionID",
      "link_kind": "accession",
      "relationship": "annotates",
      "emit": {
        "gff3-pragma": "genome-build-accession",
        "vcf-meta": "reference",
        "fair-bioheaders": "derivedFrom"
      }
    },
    "assembly-name": {
      "description": "Name of the assembly (not an identifier)",
      "keys": {
        "gff3-pragma": ["genome-build", "genome-version", "assembly"],
        "gff3-directive": ["genome-build"],
        "vcf-meta": ["reference"],
        "vcf-contig": ["assembly"],
        "fasta-defline": ["ensembl-coord-assembly", "release"]
      },
      "scope": "file",
      "core_field": null,
      "link_kind": "name",
      "emit": {"gff3-pragma": "genome-build", "fair-bioheaders": "derivedFrom"}
    }
  }
}
```

**Rules**:
- After normalisation, a key may map to several concepts. For example VCF `reference` maps to
  `assembly-accession` when the value matches the accession form, to `source-url` for a URL,
  and otherwise to `assembly-name`. The order of resolution is the form match first, then the
  concept order in the file.
- The FASTA defline pseudo-keys (`ensembl-coord-assembly` and others) are produced by the
  defline parser (research R-02), not by the file.
- The table must contain every key in research/survey.md §4. A tool test checks this against
  the shared fixtures, so every surveyed key line maps to a concept or is deliberately
  structural (`INFO`, `FORMAT`, `FILTER`, `ALT`, `ID`, `phasing`).

## 3. Reference tables

All three files share this shape:

```json
{
  "table": "spdx-licenses",
  "version": "3.27",
  "source": "https://github.com/spdx/license-list-data/blob/v3.27/json/licenses.json",
  "retrieved": "2026-10-10",
  "entries": [ {"id": "CC-BY-4.0", "url": "https://creativecommons.org/licenses/by/4.0/"} ]
}
```

- `spdx-licenses` entries: `{id, url, deprecated}`.
- `id-schemes` entries: `{prefix, pattern, persistent, resolver}`. For example
  `{"prefix": "taxonomy", "pattern": "^\\d+$", "persistent": true, "resolver": "https://identifiers.org/taxonomy:"}`.
- `formats` entries: `{format, fairsharing, version_directive, versions}`. For example
  `{"format": "gff3", "fairsharing": "FAIRsharing.dnk0f6", "version_directive": "##gff-version", "versions": ["3"]}`.
  `fairsharing` is null when no FAIRsharing record id could be confirmed (the earlier illustrative
  VCF id `FAIRsharing.pxr7x2` is in fact the SwissLipids record).

The `version` and `retrieved` values above are illustrative. The implementation task pins the
real values when it creates each file. Refreshing a table changes its `version`, which every
report records.

## 4. `assessment/manifest.json` (FAIR-bioHeaders-Specification shared fixtures)

```json
{
  "manifest_version": "1.0.0",
  "rubric_version": "1.0.0",
  "fixtures": [
    {
      "id": "ncbi-refseq-gff3-wbcel235",
      "file": "headers/ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff",
      "source_url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/985/GCF_000002985.6_WBcel235/GCF_000002985.6_WBcel235_genomic.gff.gz",
      "fetched": "2026-10-10T12:31Z",
      "format": "gff3",
      "expected": {
        "statuses": {"RDA-I3-04M": "evidenced", "RDA-R1.1-01M": "not_evidenced", "RDA-I1-01D": "evidenced"},
        "links": [{"kind": "accession", "value": "NCBI_Assembly:GCF_000002985.6"}],
        "findings": []
      }
    },
    {
      "id": "pair-genbank-vs-refseq-names",
      "file": "pairs/genbank-names.gff3",
      "related": "pairs/refseq-names.fa",
      "format": "gff3",
      "expected": {
        "pair_classification": "inconsistent",
        "circumstantial": {"verdict": "inconsistent", "missing_from_related": ["BX284601.5"]}
      }
    }
  ]
}
```

**Rules**:
- `expected.statuses` lists only the indicators the fixture is meant to exercise. A runner
  compares those and ignores the rest.
- Ids are stable.
- Every file under `assessment/headers`, `pairs` and `edge` is listed once.
- Real captures carry `source_url` and `fetched`. Synthetic files carry
  `"generator": "scripts/make_assessment_fixtures.py"`.

## 5. Pairs file (`--pairs`, and `assessment/pairs.tsv`)

The pairs file is UTF-8 and tab-separated, with no header row. Each line has two columns: the
derived path and the related path, both relative to the directory being assessed. Lines that
start with `#` are ignored. A derived path may appear at most once; a second occurrence is a
usage error (exit 2). A related path may appear any number of times, and it is read once per
run.
