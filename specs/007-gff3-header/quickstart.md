# Quickstart: GFF3 annotation header (FHGFF3)

**Feature**: 007-gff3-header

Validation scenarios. Run them from each repository root after the tasks.

## FAIR-bioHeaders-Specification

```bash
python json-schema-generator.py --type fhgff3 --output /tmp/fhgff3.json && cmp /tmp/fhgff3.json fhgff3.json
python scripts/check_linkml.py            # FHR, FHP and FHGFF3
python scripts/check_schema_drift.py --schema fhgff3.json --baseline .github/schema-baseline-fhgff3.json
python scripts/make_conformance.py --check   # or regenerate, then git diff --exit-code conformance/
python scripts/check_conformance.py --schema
python -m unittest discover -s tests
```

Expected: everything passes. `fhp.json` and `fhr.json` are unchanged (`git diff --exit-code`).

## FAIR-bioHeaders-Tools

```bash
fhr-gff3-validate examples/fhgff3/annotation.fhgff3.gff3          # Checksum verified.
bioheaders verify-links examples/fhgff3/annotation.fhgff3.gff3 examples/fhgff3/genome.fhr.fasta  # matched
bioheaders strip examples/fhgff3/annotation.fhgff3.gff3 -o /tmp/plain.gff3
bioheaders combine examples/fhgff3/annotation.fhgff3.yaml /tmp/plain.gff3 -o /tmp/again.gff3
fhr-gff3-validate /tmp/again.gff3
```

Expected:
- The stale-parent example gives `not matched` and exit 3.
- The reference-linked example gives `not checked` for `genomeReference` without an FHR genome.
- The chain FHR genome → FHGFF3 annotation → FHP proteins verifies end to end.

## gff3-validator

```bash
gff3-validate examples/no-header.gff3                     # valid, no header findings
gff3-validate examples/header-valid.gff3 --genome genome.fhr.fasta   # HDR-009 passes
gff3-validate examples/stale-parent.gff3 --genome genome.fhr.fasta   # HDR-009 error
```
