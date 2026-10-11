# Contract: the FHP JSON Schema (`fhp.json`)

**Feature**: 006-protein-header | Research: D-01 to D-07

## Generation

`python json-schema-generator.py --type fhp --output fhp.json` generates the schema from
`fhp_linkml.yml` with LinkML's JSON Schema generator. FHR's generator settings apply (no nulls,
closed classes), followed by these post-processing steps:

1. Every object is closed, including the core `Taxon`, `Author` and `AccessionID`, which FHR on
   `main` keeps open.
2. `schemaVersion`'s `const: 1` becomes `enum: [1]`.
3. `checksum` and `seqcol_id` get exact `minLength`/`maxLength`, as for FHR.
4. `$schema` is `https://json-schema.org/draft/2020-12/schema`.

The committed `fhp.json` must equal the generator output (`scripts/check_linkml.py`, which now
checks both types). Its review baseline is `.github/schema-baseline-fhp.json`, checked by
`scripts/check_schema_drift.py --schema fhp.json --baseline .github/schema-baseline-fhp.json`.

## Rules (docs/FHP.md)

- **[P1]** FHP metadata must validate against `fhp.json`. That makes `proteome` and
  `sourceType` required; FHR-only keys, unknown keys and `null` are rejected; `derivedFrom`
  entries need `headerType`, `checksum` and `relationship`; `source` entries need `name`;
  `completeness` needs its lineage dataset and all five counts.
- **[P2]** A record is read as FHP only when its `schema` is an FHP schema URL. Tools validate
  any other FASTA/GFA header as FHR, so a protein FASTA citing `fhr.json` is checked against FHR
  and fails if it lacks the FHR fields.

The shared rules R1–R10 (docs/FORMAT.md) apply to FHP files unchanged.
