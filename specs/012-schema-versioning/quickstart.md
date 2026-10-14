# Quickstart: Schema versions and schema selection

**Feature**: 012-schema-versioning

From an FHR-Specification checkout of `release-v0.4` with a full git history (tags fetched):

```bash
python -m unittest discover -s tests -v
python scripts/validate_examples.py
python scripts/check_linkml.py
python scripts/check_schema_drift.py
python scripts/check_schema_drift.py --schema fhp.json --baseline .github/schema-baseline-fhp.json
python scripts/check_schema_drift.py --schema fhgff3.json --baseline .github/schema-baseline-fhgff3.json
python scripts/make_jsonld.py --check
python scripts/check_conformance.py --schema
python scripts/check_conformance.py --converter ../FAIR-bioHeaders-Tools --require-format fhgff3   # toolkit v0.4 branch
python scripts/check_release.py --converter ../FAIR-bioHeaders-Tools                              # toolkit v0.4 branch
```

With the toolkit's v0.4 branch installed:

```bash
fhr-fasta-validate conformance/valid/fasta-schema-v0.3.1.fhr.fasta        # valid against v0.3.1
fhr-fasta-validate conformance/invalid/fasta-schema-unknown-release.fhr.fasta
# FHR: unsupported schema version: https://w3id.org/fair-bioheaders/fhr/v0.0.0 (...)
```
