# Contract: the FHGFF3 JSON Schema (`fhgff3.json`)

**Feature**: 007-gff3-header | Research: D-01 to D-05

## Generation

`python json-schema-generator.py --type fhgff3 --output fhgff3.json` generates the schema from
`fhgff3_linkml.yml`, with FHP's post-processing (006 contracts/fhp-schema.md steps 1–4) and one
more step:

1. Every object is closed.
2. `schemaVersion`'s `const: 1` becomes `enum: [1]`.
3. `checksum` and `seqcol_id` get exact `minLength`/`maxLength`.
4. `$schema` is draft 2020-12, `$id` is the raw-main URL of `fhgff3.json`, and `title` is `FHGFF3`.
   Generator version annotations are removed.
5. **The genome-link rule** is added to the root and to `$defs.FHGFF3`:
   ```json
   "anyOf": [
     {"required": ["genomeReference"]},
     {"required": ["derivedFrom"],
      "properties": {"derivedFrom": {"contains": {"$ref": "#/$defs/AnnotatesGenome"}}}}
   ],
   "properties": {"derivedFrom": {"maxContains": 1, "contains": {"$ref": "#/$defs/AnnotatesAny"}}}
   ```
   Here `AnnotatesGenome` requires `headerType: FHR` and `relationship: annotates`, and
   `AnnotatesAny` requires `relationship: annotates`. Because `maxContains` needs a `contains`
   beside it, the second form also requires at least one `annotates` item whenever `derivedFrom`
   is present. To avoid that, `maxContains` is written as
   `"not": {"contains": …, "minContains": 2}`.

The committed `fhgff3.json` must equal the generator output (`scripts/check_linkml.py` checks all
three types). The review baseline is `.github/schema-baseline-fhgff3.json`.

## Rules (docs/FHGFF3.md)

- **[G1] Placement.** Line 1 is `##gff-version 3` (or `3.x.y`). The leading header block runs from
  line 2 to the first line that is neither blank nor begins with `#`, or to the `##FASTA` line,
  whichever comes first. `#~` lines may be mixed with other `#` lines inside it. A `#~` line on
  line 1 or after the block is invalid. R1–R9 apply unchanged, and R10 is read with this block
  end.
- **[G2] Schema.** FHGFF3 metadata must validate against `fhgff3.json`. That makes `annotation`
  and a genome link required, and rejects FHR-only and FHP-only keys, unknown keys and `null`. A
  `genomeReference` needs both `accession` and `seqcol_id`.
- **[G3] Type selection.** A record is read as FHGFF3 only when its `schema` is an FHGFF3 schema
  URL. A GFF3 header citing any other schema is validated as that type (FHR by default), and fails
  if it lacks that type's fields.
