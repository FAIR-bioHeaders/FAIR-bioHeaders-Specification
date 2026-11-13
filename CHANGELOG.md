# Changelog

## Unreleased

Work targeting **v0.6.1**, the documentation patch named by the release decision of
2026-11-13: the schema selection rules, the format rules and the published JSON Schemas
stay exactly at v0.6.0 (v0.6.1 repeats the v0.6.0 row in `schemas/versions.json`, as v0.4.1
and v0.4.2 repeated the v0.4.0 row), and a v0.6.1 release changes guidance text only.

## v0.6.0 — 2026-11-13

A minor schema release: dotted BUSCO dataset versions. FHP `"1.2"` and FHGFF3 `"1.2"` accept
the dotted forms the BUSCO user guide documents, such as `enterobacterales_odb12.2`; FHR stays
`"2.1"` and `fhr.json` is byte-identical to v0.5.0, because `Completeness` lives in
`schemas/shared.yaml` and the FHR contract does not import it. Every record valid under FHP
`"1.0"`/`"1.1"` and FHGFF3 `"1.0"`/`"1.1"` stays valid with the same meaning, and a record that
states an older minor may not carry a dotted dataset version, so it keeps exactly its older
outcome. The schemas are published at `https://w3id.org/fair-bioheaders/<type>/v0.6.0`; the
redirects for that tag are a maintainer act like the tag itself. `schemas/versions.json` sets
`current` to v0.6.0 with `preRelease` cleared, and the examples cite the v0.6.0 URLs. The
reference toolkit that bundles these schema bytes is fair-bioheaders 0.11.0, prepared on that
repository's `main` and tagged after this release; the newest published toolkit release, 0.10.0,
bundles the v0.5.0 schemas.

Alongside the schema change, this tag carries the guidance that landed on `main` since v0.5.0:
the selection rule **V7** (the opt-in draft lane, #221) documented in docs/SCHEMA-VERSIONS.md,
generated CEDAR authoring templates for the released types and draft-labeled templates for FHT
and FHGM (#162 and the decision of 2026-11-13), the INSDC submission-validator evidence rounds
(#191, #210) and the `docs/FHGM.md` draft overview. Carrying them in the tag states where the
text lives, nothing more: a draft type is still not published by this release, FHT and FHGM take
no `schemaVersion`, no registry row and no w3id URL, and the follow-through corrections to that
guidance are scheduled for v0.6.1.

- **Selection rules (documentation, #221 ruling of 2026-11-13): rule V7, the draft lane.**
  docs/SCHEMA-VERSIONS.md adds `[V7]`: a reader MAY recognise an unreleased **draft** contract at
  the raw-main URL of the development repository that owns its type, only behind an explicit user
  decision, reading it against bytes pinned by commit and SHA-256 digest (the
  `header/provenance.json` / `scripts/make_cedar.py` discipline) and warning loudly on every
  record so read. The rule is type-neutral: FHT (FHT-Specification's `fht.json` and its merged
  vector suite) and FHGM (model records in FHGM-Specification) are named only as current
  instances, and for a type whose records carry no `schema` field the lane selects the contract
  and validator, not the file's routing. Default behavior is unchanged value for value: without
  the opt-in decision such a URL is still "any other value" under V5, and a draft never takes a
  release form — an unregistered type's w3id or raw-tag URL stays V5 territory, with the near-miss
  warning of FAIR-bioHeaders-Tools#125. Published rules V1 to V6 are not rewritten; V7 is
  additive, and publication promotes a type into V1 and `schemas/versions.json`, leaving the lane
  open for the next draft. No schema, model, example or vector byte changes and no `schemaVersion`
  or registry effect: `scripts/make_conformance.py` registers the V7 summary in the manifest's
  `rules` map as `notApplicable` (the lane has no default-behavior vector, and no shared vector
  cites a draft URL), so `conformance/manifest.json` gains that line only and all 291 vectors stay
  byte-identical; `tests/test_schema_versions.py` extends its label enumeration; conformance/
  README.md and docs/FHGM.md point at the rule. Refs #221.

- Generated **draft** CEDAR authoring templates for FHT and FHGM
  (`templates/cedar/{fht,fhgm}.json`), per the maintainer decision of
  2026-11-13 ("CEDAR will expand to include FHGM and FHT") extending
  #162 Option A. Both are generated from byte-pinned development snapshots
  under `templates/cedar/drafts/` (repository, branch, commit, SHA-256, git
  blob and retrieval date recorded in `drafts/provenance.json`; generation
  refuses when snapshot bytes and digests diverge). Draft templates embed
  `status: "draft"`, a DRAFT title and an embedded warning string; the FHT
  template pins the FHT-Specification raw-main contract URL and contains no
  w3id URL (none exists), and covers all 66 named contract paths with the
  draft's open `x-` patternProperty slot omitted like the released R15 slots;
  the FHGM template authors ONE model record (32 named paths, reference
  choose-one handled as the FHGFF3 genome link is) and documents the
  FHGFF3-embedded `x-fhgm-models` transport in its provenance. No schema,
  version or registry change; publication/upgrade is gated on the FHT release
  (#107 lane F) and FHGM adoption (#204). `scripts/make_cedar.py` gains a
  released|draft config table, `--check` now covers all five templates and
  verifies the snapshot digests; `tests/test_cedar.py` grows from 11 to 21
  tests (filled draft exports round-trip and validate against the stored
  draft schemas, Draft 2020-12 + FormatChecker). Extension slots remain
  omitted; publication to a CEDAR instance remains a maintainer action.
  Refs #162.

- Generated CEDAR workbench authoring templates for the released types
  (`templates/cedar/{fhp,fhgff3,fhr}.json`, FHR 2.1 / FHP 1.1 / FHGFF3 1.1) and
  their generator `scripts/make_cedar.py` (stdlib-only, deterministic,
  `--check` wired into the Validate specification workflow;
  `tests/test_cedar.py`). Authoring aids only: no schema, version or registry
  change; extension slots (docs/FORMAT.md R15) are omitted from the forms;
  publication to a CEDAR instance remains a maintainer action. Refs #162.

- **Schema change (minor, staged for v0.6.0, #170): dotted BUSCO dataset versions.**
  The shared `Completeness.lineageDataset` pattern widens from
  `^[a-z0-9_]+_odb[0-9]+$` to `^[a-z0-9_]+_odb[0-9]+(\.[0-9]+)*$`, so dataset
  ids documented by the BUSCO user guide, such as `enterobacterales_odb12.2`,
  are valid. The change is additive: every previously valid value stays
  valid with the same meaning. It affects the shared `Completeness` object
  in `schemas/shared.yaml`, imported by FHP and FHGFF3; FHR has no
  completeness slot, so `fhr.json` is unchanged and stays `"2.1"`. Staged as
  FHP `"1.2"` and FHGFF3 `"1.2"` for release v0.6.0, prepared on `main` under
  the pre-release exception (docs/SCHEMA-VERSIONS.md, "Schema files on main"):
  `schemas/versions.json` sets `current` and `preRelease` to `v0.6.0` with the
  new `releases` entry (`FHR "2.1"`, `FHP "1.2"`, `FHGFF3 "1.2"`), exactly as
  #198 pre-staged v0.5.0. The `schemaVersion` enums in `fhp_linkml.yml` and
  `fhgff3_linkml.yml` gain `"1.2"`, and `json-schema-generator.py` adds a
  conditional per type (mirroring the R15 `extension_gate`): a record that
  states `'1.0'` or `'1.1'` keeps the single-integer suffix, so it holds its
  exact older-minor outcome (`tests/test_extension_fields.py` compares every
  vector against v0.4.0). Regenerated `fhp.json` and `fhgff3.json` and both
  review baselines; the release-identity byte check skips while `preRelease`
  names the untagged `current`. 7 new conformance vectors (291: 119 valid,
  172 invalid): `fhp-fasta-busco-lineage-dotted` and
  `fhgff3-busco-lineage-dotted` state `'1.2'` and cite the prepared v0.6.0;
  the five malformed-dot rejections (trailing dot, leading dot, letter
  component, uppercase, and the FHGFF3 trailing-dot twin) fail the old and
  the new pattern alike and keep a v0.4.0 citation, so they are stable at
  every toolkit version. Like the R15 vectors before fair-bioheaders 0.9.0,
  the two positive dotted vectors need a toolkit that bundles the v0.6.0
  schemas: the conformance CI's released-`0.9.0` job reports them as an
  unsupported version until the workflow is repinned to the FAIR-bioHeaders-Tools
  commit that does, as #198 did with its `5b05b65` pin (the pin stays here
  because no such toolkit commit exists yet). Examples and `llms.txt` follow
  v0.6.0 with recomputed checksums and FHGFF3 parent links (FHR examples
  re-cite the v0.6.0 URL, still stating `'2.1'`). docs/FHP.md, docs/FHGFF3.md,
  docs/SCHEMA-VERSIONS.md, README.md, specs/005 FR-005 and conformance/README.md
  follow the widening; the INSDC coverage assessment is re-pinned (v3), no row
  changes (#170 carries no INSDC requirement).

- The conformance CI runs the released `fair-bioheaders[jsonld]==0.9.0`, the first release
  that bundles the v0.5.0 schemas (R15, J9, M5), instead of the pinned FAIR-bioHeaders-Tools
  commit `5b05b65`.
- `examples/fhp/rich-predicted.fhp.yaml`: the author gains `nameType: Personal`, as in the
  FHP-Specification copy (its #12) that FAIR-bioHeaders-Tools bundles, so the two companion
  copies match again and `check_release.py` passes. The example stays valid FHP 1.1 (author
  `nameType` is part of FHP since 1.0). `check_release.py` now reports a missing top-level
  companion example instead of stopping with a traceback.

## v0.5.0 — 2026-11-04

A minor schema release: extension fields. FHR `"2.1"`, FHP `"1.1"` and FHGFF3 `"1.1"` accept
top-level keys that start with `x-` (docs/FORMAT.md R15); every record valid under FHR `"2.0"`,
FHP `"1.0"` and FHGFF3 `"1.0"` stays valid with the same meaning. The schemas are published at
`https://w3id.org/fair-bioheaders/<type>/v0.5.0`, and `schemas/versions.json` sets `current` to
v0.5.0 with `preRelease` cleared. These rules match fair-bioheaders 0.9.0.

- **Schema addition (minor): extension fields** (#197,
  [specs/015-extension-fields](specs/015-extension-fields/spec.md)). A top-level key that
  matches `^x-[A-Za-z0-9][A-Za-z0-9_.-]*$` may hold any JSON/YAML value that the standard
  does not define, for example `x-refget-commonName`. New rule R15 in docs/FORMAT.md:
  every other unknown key is still invalid, nested objects stay closed, R8, R11, R12 and
  R13 apply to extension keys and values, the checksum covers them, validators attach no
  meaning to them, an extension never overrides a standard field, a namespace
  `x-<project>-<field>` is recommended but not checked, and a widely used extension is
  promoted under its own standard name. New schema versions FHR `"2.1"`, FHP `"1.1"` and
  FHGFF3 `"1.1"`: `patternProperties` for the pattern, no key with a line feed (Python's `$`
  matches before one), and a record that states `"2.0"`/`"1.0"` may not use extension
  fields, so it keeps exactly its 2.0/1.0 outcome. Every record valid under FHR 2.0, FHP 1.0
  and FHGFF3 1.0 stays valid with the same meaning. Records that cite a v0.4.x schema URL
  are still checked against the v0.4.x schemas (V2, V3), where `x-` keys are unknown keys;
  the selection rules V1 to V6 are unchanged.
- docs/JSONLD.md J9 and docs/MICRODATA.md M5 (new): JSON-LD, the schema.org export (X9)
  and microdata carry no extension fields. Writers leave them out and report the keys, and
  a JSON-LD document (canonical or not) or microdata item with an `x-` key is invalid, so
  JSON readers and JSON-LD processors still read the same record (J3) and no extension
  value reaches a JSON-LD processor or a web page through a writer. The JSON-LD context is
  unchanged; the vocabulary's `schemaVersion` comment names 2.1. The reference writers in
  `scripts/make_jsonld.py` leave extension fields out and its canonical reader rejects
  them.
- `schemas/versions.json`: v0.5.0 (`FHR` `"2.1"`, `FHP` and `FHGFF3` `"1.1"`) was prepared
  on `main` under the `preRelease` exception (docs/SCHEMA-VERSIONS.md, "Schema files on
  main") and the marker is cleared for the release, so the examples and `llms.txt` cite
  v0.5.0 and the new versions, with recomputed checksums for the headed examples and the
  FHGFF3 parent links. New
  example `examples/extension-fields.fhr.yaml`. docs/SCHEMA-VERSIONS.md: a record that
  states an earlier minor is held to it. The INSDC coverage assessment is re-pinned (v2);
  no row changes. The mapping-proposal fixture stays pinned to its source commit.
- 34 new conformance vectors (284: 117 valid, 167 invalid), the only ones that cite
  v0.5.0; every existing vector keeps its id, bytes and outcome. `check_conformance.py
  --schema` checks that each invalid R15 vector fails the schema it selects. The
  conformance CI runs the FAIR-bioHeaders-Tools commit that bundles the v0.5.0 schemas,
  pinned by hash, until fair-bioheaders 0.9.0 is released.
- `json-schema-generator.py` adds the extension rules (LinkML cannot express them) for
  every header type and for profile roots; drift baselines updated.

- specs/005-rna-transcriptome-header (#107): synced the shared copy with the FHT 1.0
  development contract in FHT-Specification (`9dae29b`, model merged in its PR #21),
  replacing the original draft's required `moleculeType` (`mRNA | total RNA | cDNA |
  ncRNA`). It now records the nine required fields, optional `moleculeType`
  (`mRNA | rRNA | tRNA | transcribed RNA`), the `sample` array and its rules, the two
  allowed `derivedFrom` pairs with a required parent checksum, the legacy-compatible
  `transcriptomeSynonym`, `assemblyAuthor` and `instrument`, and the dotted BUSCO lineage
  limitation (#170). Documentation only: no shared schema, `schemaVersion`, example,
  vector or validation change. FHT stays draft and unreleased.
- docs/SCHEMA-GAP-AUDIT.md (#189): recorded the maintainer decision that the next major
  of FHR, FHP and FHGFF3 requires `taxon.uri` with an NCBI Taxonomy or ITIS identifier,
  replacing GAP-1's "`name` or `uri`" plan. Adds the proposed rule (recognised URI forms),
  NCBI taxa for unclassified and environmental material, the ITIS caveats (separate
  numbering, limited microbial coverage, no FHGFF3 `##species` comparison) and migration
  notes. docs/insdc-coverage.md rows A.c, A.d, SA.T2, SA.T7 and the follow-ups, and the
  planned constraints in docs/SCHEMA-VERSIONS.md, now say this is decided for the next
  major; the INSDC profile (#190) requires the NCBI form. No schema, `schemaVersion`,
  example, vector or validation change.
- Docs: shortened J3/J8 rationale.
- docs/insdc-coverage.md (#157): assessment v1 of the INSDC minimum-specification
  review. Every requirement of the ten categories at insdc/minimum-specifcations
  `41f0dc4` has an ID and a final disposition (covered, partial, out of scope or a linked
  follow-up). Corrected claims: A.c submitter identity and A.j assembly metadata are
  partial (required author lists may be empty; method and technology fields are optional),
  A.d and SA.T2 note that `taxon.uri` is optional, the Analysis checksum (AY7) is not the
  whole-file digest INSDC records, and BioSample XSD validation (SA.4) is out of scope.
  FHT rows cite the FHT 1.0 development contract and stay marked draft. Follow-ups:
  #189 (next major: taxonomy identifier), #190 (draft INSDC profile), #191 (INSDC
  submission tools), gff3-validator#27 (Annotation rules). New section on using FH headers
  alongside an INSDC submission, linked from README, MAPPINGS.md and llms.txt.
- tests/test_insdc_coverage.py: checks that the matrix has one row for each requirement ID
  pinned in tests/fixtures/insdc-requirements.json, that dispositions are final and match
  the coverage symbol, that follow-up links are well formed and listed, that FHT rows are
  marked draft, and that the assessed `schemaVersion`s match the schemas.
- AGENTS.md: review proposed schema revisions against the INSDC coverage review.
- scripts/make_assessment_fixtures.py: pin the gzip header OS byte to 255, so the
  generated assessment fixtures match the committed files on Python 3.12 as well as 3.13.

## v0.4.2 — 2026-10-28

A patch release of the format rules: hardening that accepts only the FHR JSON-LD context,
restricts link schemes, and escapes JSON-LD in HTML script elements, plus FHR 1
compatibility (V6). The JSON schemas and every `schemaVersion` are unchanged (FHR `"2.0"`,
FHP and FHGFF3 `"1.0"`); `https://w3id.org/fair-bioheaders/<type>/v0.4.2` selects the same
schemas as v0.4.0, and `schemas/versions.json` keeps `current` at v0.4.0 so the examples
are unchanged. These rules match fair-bioheaders 0.8.5.

- docs/JSONLD.md J3: a document read by JSON-LD expansion may use only the FHR context
  (a known URL or an embedded copy equal as parsed JSON, alone or as the only item of an
  array, on a top-level object). Any other context, embedded, extended, `@import`ed,
  nested or with a schema.org `@vocab`, is invalid, and so is `@nest`: such a context could map an FHR key such as
  `genome` to another field's IRI, so JSON readers and JSON-LD readers would read
  different values from one document. J1's "equal as parsed JSON" now compares JSON types
  exactly. Conformance: the valid vector `jsonld-schemaorg-vocab-compaction` is now the
  invalid `jsonld-context-schemaorg-vocab`; `jsonld-iri-as-string` keeps its id but now
  uses the FHR context with value objects; new invalid J3 vectors `jsonld-context-remapped`,
  `jsonld-context-extended`, `jsonld-context-import`, `jsonld-context-nested` and
  `jsonld-nest`, and a new
  valid `jsonld-context-url-array`. `jsonld-unknown-term`, `jsonld-flattened` and
  `jsonld-datetime-datecreated` are now built on the expanded form, so they still break
  only their own rule.
- docs/FORMAT.md R14 (new): a `format: uri` value should use `http` or `https`; `ftp`,
  `urn:`, `doi:` and `info:` are also accepted. Other schemes (`javascript:`, `data:`,
  `file:`, ...) stay schema-valid, but validators warn, and JSON-LD and schema.org export
  writers refuse to write them as links (J7, X5). Text becomes an IRI (documentation as
  `subjectOf`; documentation and the licence in the export) only when it is an `http`,
  `https` or `ftp` URL, instead of any `scheme://` text. New valid vectors
  `fasta-link-scheme-warning`, `jsonld-link-scheme-warning` (both with the new optional
  manifest field `warnings`) and `jsonld-documentation-other-scheme`;
  `check_conformance.py --converter` checks that the converter warns.
- docs/JSONLD.md J8 (new): JSON-LD embedded in `<script type="application/ld+json">` must
  have every `<`, `>` and `&` written as `\u003c`, `\u003e` and `\u0026` (and should
  have U+2028/U+2029 escaped). Escaping only `</`, as advised before, does not cover every
  value. New valid vector
  `jsonld-script-escaped`; `scripts/make_jsonld.py` gains the reference `script_text`.
- 250 vectors (109 valid, 141 invalid), from 240. The conformance CI now runs fair-bioheaders 0.8.5, the first release
  with these rules.
- **Normative (schema selection):** add rule V6 to docs/SCHEMA-VERSIONS.md, FHR 1
  compatibility. FHR 1 (releases up to v0.3.1) told writers to cite the raw-main
  `fhr.json` URL with `schemaVersion: 1`, and existing FHR 1 files in the wild do; since
  v0.4.0 raw-main selects FHR 2.0, so V1 alone made those files fail on `schemaVersion`
  even when they were valid FHR 1. A record whose `schema` is the raw-main `fhr.json`
  URL (either repository name) and whose `schemaVersion` is the number 1 (`1` or `1.0`;
  not the string `"1"` or a boolean) is now an FHR 1 record, checked against the v0.3.1
  schema: deprecated (readers should warn), not invalid. Every other record selects as
  before, and FHP and FHGFF3 are unaffected. The migration section now describes such
  files as deprecated. No schema bytes, `schemaVersion` or `versions.json` change.
- Conformance vectors for V6 (233 -> 240 vectors): the invalid vector
  `fasta-schema-raw-main-version-1` (raw-main with `schemaVersion: 1.0`) is retired,
  because V6 changes its outcome, and the same bytes are the new valid vector
  `fasta-schema-raw-main-version-1-0`. Vector ids are never reused: the manifest gains a
  `retired` list (id, former outcome, replacement, reason), and `check_conformance.py`
  rejects a vector that reuses a retired id. New valid
  `fasta-schema-raw-main-version-1-integer`,
  `fasta-schema-canonical-raw-main-version-1`, `microdata-schema-raw-main-version-1`
  (untyped `schemaVersion`) and `jsonld-schema-raw-main-version-1`; new invalid
  `fasta-schema-raw-main-version-1-invalid` (an FHR 1 record that v0.3.1 rejects),
  `fasta-schema-raw-main-version-string-1` and `fasta-schema-raw-main-version-true`
  (V6 needs the number 1, so V1 applies). `check_conformance.py --schema` applies V6, and
  validates microdata and JSON-LD metadata against the schema it selects. fair-bioheaders
  0.8.4 is the first release that implements V6 (FAIR-bioHeaders-Tools#114).

- Enable the deferred FHGFF3 G1 near-miss vectors `fhgff3-version-30`,
  `fhgff3-version-3x` and `fhgff3-version-3-1` (invalid, G1), now that fair-bioheaders
  0.8.2 enforces the full `##gff-version` grammar (FAIR-bioHeaders-Tools#91), and pin
  the conformance CI to fair-bioheaders 0.8.2 (#171). Vectors and tests only; no schema
  or `schemaVersion` change.

- Start the draft #56 mapping-profile foundation: separate proposed assembly
  export context, root-field DCMI handling inventory, worked descriptive RDF
  bundle, target/family status matrix and offline semantic tests. No core schema,
  canonical serialization or release/version changes; target adapters and FHT
  mapping remain unfinished.

- Document the open schema-contract questions from #150 and add conformance coverage:
  required values must be non-empty (the matching schema constraints are deferred to the
  next major `schemaVersion`), `format` must be asserted by a conforming validator, NaN and
  infinities are invalid (new rule R13, invalid vectors `fasta-nan-vital-stats` and
  `fasta-infinity-vital-stats`), `nameType` wins over an ORCID for JSON-LD typing while the
  combination stays accepted, the J1/J4 export-term difference is intended, and FHGFF3 G1
  now gives the full `##gff-version` grammar with a valid trailing-whitespace vector. The
  near-miss `##gff-version` vectors (`fhgff3-version-30`, `-3x`, `-3-1`) are deferred until
  the toolkit implements the grammar (FAIR-bioHeaders-Tools#75).
  `tests/test_schema_versions.py` now checks that the schema bytes on main equal the current
  release tag. Documentation, vectors and tests only; no schema or `schemaVersion` change.

## v0.4.1 — 2026-10-21

A patch release of the format rules. The JSON schemas and every `schemaVersion` are
unchanged (FHR `"2.0"`, FHP and FHGFF3 `"1.0"`); `https://w3id.org/fair-bioheaders/<type>/v0.4.1`
selects the same schemas as v0.4.0, and `schemas/versions.json` keeps `current`
at v0.4.0 so the examples are unchanged. The checksum-line and YAML rules below close a gap in
what the checksum covers; see GHSA-4hc8-hc87-xvc8 (FAIR-bioHeaders-Tools), fixed in
fair-bioheaders 0.8.1.


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
- docs/FORMAT.md states which containers each header type goes in (FHR: FASTA and
  GFA; FHP: FASTA; FHGFF3: GFF3), as fair-bioheaders enforces since #73, and the
  input limits that readers may apply (1 MiB and 10,000 lines of header, 20,000
  YAML nodes nested at most 64 deep, 64 MiB metadata files).
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

The major public release. FHR's metadata contract moves to `schemaVersion`
`"2.0"`: the v0.4 tightening rejects some files that v0.3 accepted (see
docs/SCHEMA-CHANGES-v0.4.md). The protein header FHP and the GFF3 annotation
header FHGFF3 have their first releases, each at `schemaVersion` `"1.0"`. A file's
`schema` URL selects the schema it is validated against (docs/SCHEMA-VERSIONS.md):
the raw-`main` URL means the current schema, a versioned w3id or tag URL selects
that release, and an unknown version is reported as unsupported. Release-targeted
files cite `https://w3id.org/fair-bioheaders/<type>/v0.4.0`.

Several entries below record intermediate states on the release line. Where the
final state supersedes an earlier entry, that entry is marked **Superseded in
v0.4.0** rather than rewritten; the release records stay in place.

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
- FHGFF3 v0.1 (document status; released as `schemaVersion` `"1.0"`, spec 007;
  called a draft when this entry was written) is released from this
  line too: `fhgff3.json` is generated here from the v0.4 core (tightened
  patterns, optional author `nameType`), with its baseline
  `.github/schema-baseline-fhgff3.json` updated deliberately. `fhp.json` is
  unchanged by the merge.
- FHP v0.1 (document status; released as `schemaVersion` `"1.0"`, spec 006;
  called a draft when this entry was written) is released from this line, so
  `fhp.json` is generated here from the v0.4 core: the tightened patterns and the
  optional author `nameType` apply to FHP as well. Its baseline
  `.github/schema-baseline-fhp.json` was updated deliberately. Every core object is
  closed for FHP and FHR alike on this line.
- Tighten loose schema constraints (#35, spec 002). **Superseded in v0.4.0:**
  the released `schemaVersion` is the string `"2.0"`, not 1 (see the
  schema-version entry above); the rest of the tightening stands. Every other
  change rejects values that were already malformed.
  docs/SCHEMA-CHANGES-v0.4.md lists each change with a before/after example and
  a migration hint. Possibly breaking for existing metadata:
  - `schemaVersion` is restricted to 1 (`enum: [1]`); `99` or `2` now fail.
    **Superseded in v0.4.0** by `type: string`, `enum: ["2.0"]`; non-string and
    unknown values still fail.
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
  `schemaVersion` as `enum: [1]` (**superseded in v0.4.0** by the string
  `enum: ["2.0"]`). The schema review baseline was updated
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

- Add a FAIR header for GFF3 annotations, FHGFF3 (spec 007, #48, the FHGFF3
  part of #50; draft at the time, released in v0.4.0). **Superseded in v0.4.0:**
  FHR and FHP were regenerated from the v0.4 core later on this line, so they
  are not byte-identical to their pre-v0.4 files. At the time of this entry
  **FHR and FHP were unchanged**: `fhr.json`, `fhp.json`, the core and every
  existing vector were byte-identical. The new files are:
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
  given). JSON-LD and microdata for FHGFF3 are follow-ups. FHGFF3 was not
  released at this point; **superseded in v0.4.0** by the release entry above.
- Add a FAIR header for protein FASTA, FHP (spec 006, #47, the FHP part of
  #50; draft at the time, released in v0.4.0). **Superseded in v0.4.0:** FHR was
  regenerated from the v0.4 core later on this line. At the time of this entry
  **FHR was unchanged**: `fhr.json`, `fhr_linkml.yml`, the core and every FHR
  vector were untouched. The new files are:
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
  FHP are follow-ups. FHP was not released at this point; **superseded in
  v0.4.0** by the release entry above.
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
