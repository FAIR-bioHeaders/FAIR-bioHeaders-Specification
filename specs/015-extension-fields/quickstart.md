# Quickstart: Extension fields

**Feature**: 015-extension-fields

From a FAIR-bioHeaders-Specification checkout with tags fetched (`git fetch --tags`):

```bash
python -m unittest discover -s tests -v
python scripts/validate_examples.py
python scripts/validate_examples.py --schema fhp.json --examples examples/fhp
python scripts/validate_examples.py --schema fhgff3.json --examples examples/fhgff3
python scripts/check_linkml.py
python scripts/check_schema_drift.py
python scripts/make_jsonld.py --check
python scripts/check_conformance.py --schema
python scripts/check_conformance.py --skip-regeneration --require-format jsonld --require-format fhp-fasta --require-format fhgff3 --converter /path/to/toolkit-venv
python scripts/check_release.py --converter ../FAIR-bioHeaders-Tools
```

With the toolkit branch installed:

```bash
bioheaders validate conformance/valid/fasta-extension-fields.fhr.fasta          # valid
bioheaders validate conformance/invalid/fasta-extension-older-version.fhr.fasta  # x- keys need "2.1"
bioheaders convert conformance/valid/fasta-extension-fields.fhr.fasta out.jsonld
# FHR: warning: extension fields are not written to JSON-LD: x-refget-commonName, ...
```
