# Changelog

## Unreleased

- docs/FORMAT.md defines the checksum line exactly (R5): after the key and colon it
  holds only the 44-character value, plain or quoted, and spaces. A comment, tag,
  tab or other text on that line now makes the file invalid, because the line is
  excluded from the checksum. R4 requires the canonical base64 form and exact
  string comparison; R1 defines line terminators (LF, CRLF, or a CR not followed by
  LF); R3 states that the checksum line's position within the header block is not
  covered. New rule R12: YAML metadata is read with YAML 1.2 core-schema types and
  must read the same under YAML 1.1, so explicit tags and plain scalars such as
  `010`, `1_000`, `1:30`, `yes`, `on` or `1e3` are invalid (quote them). The JSON
  schemas and `schemaVersion` are unchanged; files written by fair-bioheaders
  already follow these rules. New conformance vectors for R4, R5 and R12. These
  match fair-bioheaders 0.8.1 (security advisory to follow).
- Add `llms.txt`, a short overview of FAIR-bioHeaders for AI assistants (llmstxt.org
  format), checked against `schemas/versions.json` by `tests/test_llms_txt.py`, and an
  AGENTS.md section on using FAIR-bioHeaders in another project.
- Add rule R11 to docs/FORMAT.md (#127, spec 014): in FASTA files (FHR and FHP),
  FHR header lines should not contain a raw `>` or `@`, because kseq-based readers
  (BWA, minimap2, seqtk, `samtools dict`, pysam `FastxFile`) start a record at
  either character anywhere in a line and silently read a bogus record. Writers
  escape them as `\x3E` and `\x40` in double-quoted YAML scalars, which read back
  as the same characters, so the metadata and every other format are unchanged.
  A raw `>` or `@` stays valid (validators warn), so no schema or `schemaVersion`
  change. New conformance vectors `fasta-escaped-record-markers`,
  `fasta-raw-record-markers` and `fhp-fasta-escaped-record-markers`; R11 is a
  writer rule with no invalid vector, like J7.
- Add an "Upstream support" inventory to docs/TOOL_COMPATIBILITY.md (#121): the tools that already
  work with FHR headers, and the changes proposed upstream so that FASTA tools skip `;` lines before
  the first record. Documentation only.

## v0.4.0 — 2026-10-14

The next major public release. FHR's metadata contract moves to `schemaVersion`
`"2.0"`: the v0.4 tightening rejects some files that v0.3 accepted (see
docs/SCHEMA-CHANGES-v0.4.md). The protein header FHP and the GFF3 annotation
header FHGFF3 have their first releases, each at `schemaVersion` `"1.0"`. A file's
`schema` URL selects the schema it is validated against (docs/SCHEMA-VERSIONS.md):
the raw-`main` URL means the current schema, a versioned w3id or tag URL selects
that release, and an unknown version is reported as unsupported. Release-targeted
files cite `https://w3id.org/fair-bioheaders/<type>/v0.4.0`.

- The repository is now `FAIR-bioHeaders-Specification` (#108). Schema
  selection (docs/SCHEMA-VERSIONS.md V1, V2) recognises raw GitHub URLs under
  either name, FAIR-bioHeaders-Specification or FHR-Specification, and the FHP
  and FHGFF3 schemas accept both. New vectors `fasta-schema-canonical-raw-main`,
  `fasta-schema-canonical-raw-tag`, `fhp-fasta-schema-canonical-raw-main` and
  `fhgff3-schema-canonical-raw-main` cover the new name.
- **Schema versions and schema selection** (spec 012, #44). `schemaVersion` is now a
  `"MAJOR.MINOR"` string: FHR `"2.0"` (a major version, because the v0.4
  tightening rejects some files v0.3 accepted), FHP `"1.0"` and FHGFF3 `"1.0"`.
  `docs/SCHEMA-VERSIONS.md` defines major and minor and the rule readers use to
  choose a schema from a file's `schema` URL: raw-main is the current schema with
  no fallback to v0.3.1, a release's raw tag or w3id URL selects that release, and
  a release the reader lacks, a branch or commit ref, or a release without that
  type is unsupported-version (rules V1-V5). `schemas/versions.json` records each
  release's versions. Examples, conformance vectors and assessment fixtures cite
  `https://w3id.org/fair-bioheaders/<type>/v0.4.0`, with recomputed checksums;
  15 vectors test selection. `check_conformance.py --schema` applies the rule and
  reads older releases' schemas from git tags. The FHP and FHGFF3 `schema`
  patterns accept the raw-main, raw tag and w3id forms. Files that cite raw-main
  with `schemaVersion: 1` must be updated or pinned to v0.3.1 (migration in
  `docs/SCHEMA-VERSIONS.md`); no tool rewrites them.
- FHGFF3 v0.1 (draft GFF3 annotation header, spec 007) is released from this
  line too: `fhgff3.json` is generated here from the v0.4 core (tightened
  patterns, optional author `nameType`), with its baseline
  `.github/schema-baseline-fhgff3.json` updated deliberately. `fhp.json` is
  unchanged by the merge.
- FHP v0.1 (draft protein header, spec 006) is released from this line, so
  `fhp.json` is generated here from the v0.4 core: the tightened patterns and the
  optional author `nameType` apply to FHP as well. Its baseline
  `.github/schema-baseline-fhp.json` was updated deliberately. Every core object is
  closed for FHP and FHR alike on this line.
- Tighten loose schema constraints (#35, spec 002). `schemaVersion` stays 1;
  every change rejects values that were already malformed.
  docs/SCHEMA-CHANGES-v0.4.md lists each change with a before/after example and
  a migration hint. Possibly breaking for existing metadata:
  - `schemaVersion` is restricted to 1 (`enum: [1]`); `99` or `2` now fail.
  - Nested objects (`taxon`, `metadataAuthor`/`assemblyAuthor` items,
    `accessionID`, `vitalStats`) reject unknown keys, so a typo such as
    `vitalStats.n50` now fails. Use profiles (#51) for extra fields.
  - `masking` must be exactly one of its five values (anchored pattern).
  - `scholarlyArticle` must be a bare DOI `10.<registrant>/<suffix>` (escaped
    dot, non-empty suffix, no spaces).
  - `identifier` items must be `prefix:accession` with a non-empty prefix of
    letters, digits, `.`, `_` or `-` (uppercase now explicitly allowed) and a
    non-empty accession (anchored).
  - `taxon.uri` and ORCID URIs are anchored at both ends with escaped dots;
    ORCID `X` check digits remain valid and `https://` is still required.
  - `checksum` must be standard padded base64 of a 32-byte digest
    (`^[A-Za-z0-9+/]{43}=$`); 44 `=` characters or unpadded values now fail.
  - `N50`, `L50`, `L90`, `totalBasePairs`, `numberContigs` and
    `numberScaffolds` have `minimum: 0`, like `N90`.
- Add optional `vitalStats.scaffoldN50`, `scaffoldN90`, `scaffoldL50` and
  `scaffoldL90` (nonnegative integers). `N50`, `N90`, `L50` and `L90` are now
  described as contig statistics.
- Add optional `nameType` (`Personal` or `Organizational`, the DataCite
  `nameType` values) to `metadataAuthor` and `assemblyAuthor` items (feature 011,
  maintainer decision 4). It is the vocabulary term `fhr:nameType`, and the
  JSON-LD writer types the author node from it before inferring the type from an
  ORCID or ROR `uri`. The key is `nameType`, not `type`, because JSON-LD contexts
  such as schema.org's alias `type` to `@type`.
- Document that `gcContent` is a percentage from 0 to 100, not a fraction; `0.42`
  remains valid as 0.42 percent.
- LinkML (`schemas/core.yaml`, `fhr_linkml.yml`) carries the same constraints;
  `json-schema-generator.py` no longer reopens nested objects and emits
  `schemaVersion` as `enum: [1]`. The schema review baseline was updated
  deliberately. New tests cover each rejected value against both schemas, real
  edge forms (ORCID `X`, preprint DOIs, uppercase CURIEs, low GC percentages)
  and all examples. The `fasta-nested-checksum`/`gfa-nested-checksum`
  conformance vectors move their nested `checksum:` line from `taxon` into a
  `documentation` block scalar so their metadata stays valid; their expected
  checksums changed. The converter's three bundled schema copies must be
  updated to match.
- Add a one-way schema.org export profile (feature 013, #56, from David Molik's
  2026-10-14 proposals). It is separate from the canonical JSON-LD, which does
  not change, and an export document cannot be read back.
  `docs/SCHEMAORG-EXPORT.md` gives rules X1 to X9:
  - the metadata record is a `CreativeWork` `about` the assembly, with the
    metadata authors and schema;
  - `funding` is a `Grant` whose description is the unchanged text;
  - numeric statistics are `Observation` nodes about the assembly, with the FHR
    metric term and a Units Ontology unit, and no observation date;
  - `assemblySoftware` is the `instrument` of a `CreateAction` whose result is
    the assembly; the protocol is a `HowTo` only when the export context says so;
  - a strict DOI is a `ScholarlyArticle` via `subjectOf`;
  - `seqcol_id` is a `PropertyValue` identifier labelled "GA4GH refget sequence
    collection".

  Nothing is invented: no funders, dates, resolver URLs or identity claims.
  `mappings/fhr-schemaorg-export.yml` places every field. The reference exporter
  `to_export` (`scripts/make_jsonld.py`) writes `examples/example.fhr.export.jsonld`
  and one fixture per proposal (`tests/fixtures/schemaorg-export/`).
  `tests/test_schemaorg_export.py` checks every schema.org term's domain and
  range against the pinned v30.1 subset, which gains the export terms. The
  canonical vocabulary gains `fhr:seqcol_id rdfs:subPropertyOf schema:identifier`
  (LinkML `broad_mappings`; no validation change). `check_release.py` also
  compares the export fixtures with the toolkit.
- Update current maintainer contacts to `molik@fhref.org` and `wright@fhref.org` and project Pages links to `https://fhref.org`. Citation/package metadata and private reporting routes are checked; runtime behavior and historical notices are unchanged.

- Add a **draft** FAIR header for GFF3 annotations, FHGFF3 (spec 007, #48, the
  FHGFF3 part of #50). **FHR and FHP are unchanged**: `fhr.json`, `fhp.json`, the
  core and every existing vector are byte-identical. The new files are:
  - `fhgff3_linkml.yml`, which imports the core, and `fhgff3.json`, generated from it
    (`json-schema-generator.py --type fhgff3`), with its own review baseline;
  - the required `annotation` field and a required genome link. The link is a
    `derivedFrom` item that `annotates` an FHR genome by checksum, or a
    `genomeReference` (assembly accession plus SeqCol digest), or both, with the
    checksum authoritative. The generator adds this rule, and the rule that at most
    one item `annotates` an FHR parent, to the schema;
  - the optional `source`, `annotationSoftware`, `annotationProtocol`, `soVersion`,
    `featureCounts` and BUSCO `completeness` fields.

  `schemas/shared.yaml` takes FHP's software, source and completeness objects, so
  both types share them. `docs/FHGFF3.md` gives the placement rule (after
  `##gff-version 3`, ending at the first feature or `##FASTA`), the fields, the
  native-directive cross-check (warnings only) and rules G1–G3. `examples/fhgff3/`
  has checksum- and reference-linked, embedded-FASTA, plain, invalid and
  stale-parent examples. Twenty-five `fhgff3` conformance vectors cover R1–R10 on
  GFF3 and G1–G3. `check_conformance.py --converter` reports FHGFF3 as unsupported
  for converters without `fhr-gff3-validate` (unless `--require-format fhgff3` is
  given). JSON-LD and microdata for FHGFF3 are follow-ups. FHGFF3 is not released.
- Add a **draft** FAIR header for protein FASTA, FHP (spec 006, #47, the FHP part of
  #50). **FHR is unchanged**: `fhr.json`, `fhr_linkml.yml`, the core and every FHR
  vector are untouched. The new files are:
  - `fhp_linkml.yml`, which imports the shared core, and the JSON Schema `fhp.json`
    generated from it (`json-schema-generator.py --type fhp`), with its own review
    baseline;
  - the required `proteome` and `sourceType` (`predicted | database | mixed`, by
    origin) fields;
  - the optional `derivedFrom`, `source` (non-FAIR-bioHeaders sources such as a
    UniProt release), `geneticCode`, `isoformPolicy`, `predictionSoftware`,
    `predictionProtocol`, `sequenceStats` and BUSCO `completeness` fields.
  `docs/FHP.md` gives the fields and rules P1–P2, and `examples/fhp/` has
  predicted, database and mixed examples. Twenty-three `fhp-fasta` conformance
  vectors cover R1–R10 on amino-acid FASTA (stops, U, O, B, Z, J, X, lower case,
  gaps) and P1–P2. `check_linkml.py` checks both types, and `check_release.py`
  compares the toolkit's FHP schema copy when present. JSON-LD and microdata for
  FHP are follow-ups. FHP is not released.
- Add a JSON-LD form of FHR metadata (feature 011, #56). **No schema change.**
  `jsonld/fhr.context.jsonld` maps every FHR field to schema.org where a term
  fits and otherwise to the FAIR-bioHeaders vocabulary
  `https://w3id.org/fair-bioheaders/terms#` (`jsonld/terms.ttl`,
  `jsonld/terms.jsonld`, `docs/TERMS.md`). All of them are generated by
  `scripts/make_jsonld.py` from LinkML annotations in `schemas/core.yaml` and
  `fhr_linkml.yml`. `docs/JSONLD.md` gives reading rules J1 to J7, the export
  context (Bioschemas `keywords`, `url` and `conformsTo`), author typing from
  ORCID or ROR, and what converting to RDF loses.
  `mappings/fhr-jsonld-dcmi.yml` maps every field to Dublin Core (DCMI Terms),
  with a summary in `docs/MAPPINGS.md`. The conformance suite gains 23 JSON-LD
  vectors, 11 of them for rules J3 to J5 (other forms, read by JSON-LD
  expansion with bundled contexts only: expanded, schema.org `@vocab`, one-node
  `@graph`, IRIs as strings, and the invalid unknown-term, remote-context,
  two-node, two-value, flattened, `xsd:dateTime` and root-`@id` cases). A GitHub Pages site (`scripts/build_pages.py`,
  `.github/workflows/jsonld-pages.yml`) serves the context and vocabulary with
  JSON-LD and Turtle media types. The context also defines every node type at
  the root, so JSON-LD 1.0 tools such as validator.schema.org recognise them;
  w3id redirects for the vocabulary namespace and
  release contexts are prepared for perma-id/w3id.org.

- Add the FAIR header guideline `docs/FAIR_HEADER_GUIDELINE.md` (feature 010,
  US3). **Guidance only; no schema change**: `fhr.json`, `schemas/core.yaml`
  and `fhr_linkml.yml` are untouched. It has 8 items (identify the file;
  describe it; declare format and convention; identifiers not labels; derived
  from; provenance; licence; where to get the data), each mapped to the RDA FAIR
  Data Maturity Model indicators and FAIR principles, with examples in at least
  two file types taken from the 34-file provider survey where they exist. Core
  field names are suggested as keys only where a format has no native key. The
  10 indicators that cannot apply to a header are listed with repository-level
  actions. RDA text is used under CC BY 4.0 with attribution
  (doi:10.15497/rda00050). `tests/test_assessment_guideline.py` checks the item
  table, and `scripts/check_assessment.py --guideline` compares it with the
  toolkit's rubric. The assessment fixture manifest now targets rubric 1.1.0.
- Document the MPL-2.0 transition for new project contributions from March 2025 onward, preserve historical permissions and third-party notices, and align README and citation licensing. No runtime behavior changes.

- Add HTML microdata conformance vectors (rule R9). Thirteen valid and ten invalid
  `.fhr.html` vectors cover repeated attributes (first wins), `itemtype` and
  `itemprop` token lists, implied end tags, nested unrelated item scopes, value
  attributes on their defining elements only, HTML escaping, non-ASCII text, a
  byte order mark, and typed and untyped values. Valid vectors give the complete
  expected metadata object. docs/MICRODATA.md labels the reading rules M1 to M4
  (item scope, values, `data-fhr-type`, schema validity); the manifest lists them
  beside R1 to R10, and R9 is no longer `notApplicable`.
  `check_conformance.py --converter` runs `fhr-convert in.html out.json` on the
  microdata vectors and compares the JSON with the manifest. Converter 0.3.3
  passes every vector; 0.3.0 fails seven microdata vectors.
- Add a tool-compatibility survey for FHR-headed FASTA, GFA and GFF3 files
  (#40, #49) in `docs/TOOL_COMPATIBILITY.md`, with scripts in
  `scripts/tool_survey/`. htslib faidx and most FASTA indexers reject the
  leading `;~` block; kseq-based tools ignore it; all GFA and GFF3 tools tested
  accept `#~` lines. Concatenated FHR files (invalid under R10) are silently
  misread as sequence by many tools. Also adds a draft, unfiled htslib proposal
  in `docs/proposals/htslib-fasta-comments.md`.
- Split the LinkML model into a shared FAIR-bioHeaders core
  (`schemas/core.yaml`) and the FHR module (`fhr_linkml.yml`), which imports it
  (#43, spec 004). The core holds the slots every header type shares, with
  FHR's current names and constraints. It also adds a provisional `DerivedFrom`
  class and `derivedFrom` slot (`headerType`, `checksum`, optional `seqcol_id`
  and `accessionID`, `relationship`). The relationship values await a decision
  on a PROV-O/RO mapping (#54). FHR does not include `derivedFrom`. `fhr.json`
  is unchanged and the generated schema is still validation-equivalent.
  `json-schema-generator.py` gains `generate_from()` for any schema that
  imports the core. A test generates a toy FHP stub from the core.
- Add FASTA/GFA conformance vectors for header parsing and checksum coverage
  (#34). `conformance/manifest.json` lists the expected outcome for each vector.
  `scripts/make_conformance.py` generates the vectors and computes their
  checksums with the standard library only. `scripts/check_conformance.py`
  checks that the vectors are current, recomputes the checksums, and optionally
  runs the converter over the vectors. CI runs these checks with converter 0.3.3
  from PyPI.
- Label the docs/FORMAT.md checksum and header parsing rules R1 to R10. The labels
  are non-normative and the rule text is unchanged.
- Mark the conformance files `-text` in `.gitattributes` so git never converts
  their line endings.

## v0.3.1 — 2026-10-08 (documentation patch)

- docs/FORMAT.md specifies how FHR header lines are parsed: a single-line checksum
  value on an unquoted root-level key, permitted header characters, byte order
  mark handling, no duplicate keys or YAML anchors/aliases, microdata attribute
  rules, and FHR lines forming the leading header block (FASTA and GFA). These
  match converter 0.3.1 (GHSA-pvq5-772j-fq72).
- Archive the private reporting and conflict/appeal contacts added after the
  v0.3.0 tag, and correct stale release, citation and policy wording.
- Add Spec Kit scaffolding with a draft constitution and draft feature specs.

The schema, examples and schemaVersion 1 are unchanged from v0.3.0.

## v0.3 — 2026-10-07 (from v0.2)

- Add optional structured assembly software, assembly protocol URI, N90, GC-content
  percentage, and supplied refget sequence collection ID. Preserve legacy software names.
- Retain required fields and schemaVersion 1; make ORCID's string type explicit.
- Align LinkML generation with the published contract and add equivalence checks.
- Replace speculative resource mappings with verified partial MIxS/MIGS projections.
- Correct JSON/YAML, FASTA/GFA, and escaped/typed microdata examples.
- Adopt exact-byte SHA-512/256 coverage of metadata and sequence, except the checksum
  line; old MD5/payload-only examples must be regenerated, not relabeled.
- Add CI, explicit schema drift protection, a generated diagram, project guidance,
  and a successor governance proposal. Private conduct/security reporting contacts
  and conflict/appeal routing are documented in CODE_OF_CONDUCT and SECURITY.
- Use verified Chicago bibliography citations with concept DOI links.

Published 2026-10-07 as v0.3.0 (version DOI
[10.5281/zenodo.23224136](https://doi.org/10.5281/zenodo.23224136)). Reusable
Nextflow modules are developed in the separate FHR-Nextflow repository (0.1.0-dev,
not yet released). The governance plan remains a proposal. Reporting-contact
updates on main after the tag are not included in the v0.3.0 archive.
