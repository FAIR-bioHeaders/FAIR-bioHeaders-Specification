# Contract: toolkit behaviour for FHP (FAIR-bioHeaders-Tools)

**Feature**: 006-protein-header | Research: D-08, D-10, D-11

## Schema selection (every command)

- `bioheaders.FHP_SCHEMA` is loaded from the bundled `fhp_schema.json`, a byte-identical copy of
  FAIR-bioHeaders-Specification `fhp.json`.
- `bioheaders.header_type(metadata)` returns `"FHP"` when `metadata["schema"]` is a string that
  fully matches the FHP schema URL pattern (D-02), and `"FHR"` otherwise.
- `bioheaders.schema_for(metadata)` returns the matching schema.
- `fhr.fhr_validate()` validates against `schema_for(self.__dict__)`. Nothing else in validation
  changes.
- **Messages**: `validate` prints `FHP metadata is valid.` for FHP records. FHR output is
  unchanged (`FHR metadata is valid.`), and so are `verify` (`Checksum verified.`) and error
  texts.
- **Extensions**: `.faa` is a FASTA extension.
- **Default combine output**: `combine` names its output `X.fhp.fasta` (or `.fhp.gfa`) when the
  metadata is FHP, and `X.fhr.*` as before otherwise.
- **Formats**: converting an FHP record to JSON-LD or HTML microdata fails with
  `JSON-LD and HTML microdata output are not available for FHP metadata yet`, exit status 1.
  JSON, YAML and the FASTA/GFA header work.

## `bioheaders verify-links FILE PARENT...`

**FILE** is a FASTA or GFA file with a FAIR-bioHeaders header (plain or gzip/BGZF). Its header is
validated, and its checksum verified, exactly as `verify` does. Then:

1. For each **PARENT**:
   - A FASTA or GFA file by extension: compute its family checksum from its bytes (R1–R4) and read
     its header type from its `schema` (FHP, FHR when the URL ends in `/fhr.json`, otherwise
     unknown).
   - Any other container, such as `.gff3`: the parent is unsupported, with the reason
     `GFF3 headers are not specified yet (FAIR-bioHeaders-Specification spec 007)` or
     `unsupported file type`.
2. For each `derivedFrom` entry, in order:
   - `matched` if a supplied parent's computed checksum equals the entry's `checksum`;
   - otherwise `not matched` if at least one supplied, checksummed parent has a known header type
     equal to the entry's `headerType`. Each such file is listed with its computed checksum;
   - otherwise `not checked`, with the reason: no supplied file of that header type, or the
     supplied file's container is unsupported.
3. Supplied parents that match no entry are listed as `not a recorded parent`.

**Output**: one line per entry, then one per unmatched file. Example:

```
derivedFrom[0] FHR translatedFrom: not matched (genome-v2.fa has checksum Q1x…=)
derivedFrom[1] FHGFF3 translatedFrom: not checked (annotation.gff3: GFF3 headers are not specified yet (FAIR-bioHeaders-Specification spec 007))
```

Free text after the status is informative and is not a stable interface. The status words are
stable. The last line always says:
`A match confirms file identity only, not that the translations are correct.`

**Exit status**:
- 0: no entry is `not matched` and, with `--require-all`, none is `not checked`;
- 1: FILE or a parent cannot be read, or FILE's header or checksum is invalid;
- 2: usage error;
- 3: an entry is `not matched` or, with `--require-all`, `not checked`.

These follow `bioheaders assess`, where 3 means a recorded link did not match.

The command never writes to FILE or to any parent. It applies to any header type with
`derivedFrom`; FHR schemaVersion 1 has none, so for FHR files it reports `no parent files
recorded` and exits 0.

## Assessment

`bioheaders assess` reports FHP schema conformance through `fhr_validate()`. The suggestion that
described FHP as a future draft says FHP is a draft specification (not released).
