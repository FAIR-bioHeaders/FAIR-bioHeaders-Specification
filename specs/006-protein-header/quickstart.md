# Quickstart: Protein FASTA header (FHP)

**Feature**: 006-protein-header | **Date**: 2026-10-11

## Write an FHP header

`proteins.fhp.json`, a minimal predicted set (placeholders labelled):

```json
{
  "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/main/fhp.json",
  "schemaVersion": 1,
  "proteome": "Example predicted proteome (placeholder)",
  "sourceType": "predicted",
  "taxon": {"name": "Homo sapiens", "uri": "https://identifiers.org/taxonomy:9606"},
  "version": "1.0",
  "metadataAuthor": [{"name": "Example author (placeholder)"}],
  "dateCreated": "2026-10-11",
  "checksum": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
}
```

```bash
bioheaders validate proteins.fhp.json             # FHP metadata is valid.
bioheaders combine proteins.fhp.json proteins.faa # writes proteins.fhp.fasta with the real checksum
bioheaders verify proteins.fhp.fasta              # Checksum verified.
bioheaders strip proteins.fhp.fasta stripped.faa  # stripped.faa is byte-identical to proteins.faa
bioheaders verify-links proteins.fhp.fasta genome.fhr.fasta
```

## Validation scenarios

Run V1–V5 from the FAIR-bioHeaders-Specification root and V6–V8 from the FAIR-bioHeaders-Tools root. Each must
pass before the feature is done.

| # | Scenario | Command | Expected |
|---|---|---|---|
| V1 | `fhp.json` is the LinkML output, and FHR is unchanged | `python scripts/check_linkml.py` | Both types match; exit 0 |
| V2 | FHP schema baseline | `python scripts/check_schema_drift.py --schema fhp.json --baseline .github/schema-baseline-fhp.json` | No drift |
| V3 | FHP examples are valid | `python scripts/validate_examples.py --schema fhp.json --examples examples/fhp` | Every example valid |
| V4 | FHP vectors | `python scripts/check_conformance.py --schema` | All vectors, FHR and FHP, agree with the manifest |
| V5 | FHR untouched | `python scripts/validate_examples.py && python scripts/make_jsonld.py --check && git diff --exit-code main -- fhr.json` | FHR outputs are unchanged |
| V6 | Toolkit on all vectors | `python ../FAIR-bioHeaders-Specification/scripts/check_conformance.py --converter . --require-format fhp-fasta` (from the toolkit checkout, which is installed) | 100% of vectors agree (SC-002) |
| V7 | Byte preservation | `pytest tests/fhp_test.py -k "strip or combine"` | Strip removes exactly the FHP lines of every vector, and combine then strip returns the body byte for byte (SC-002a) |
| V8 | Link check | `pytest tests/fhp_test.py -k links` | matched, not matched and not checked are reported as contracts/cli.md says; nothing is written |
