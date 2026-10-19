# Implementation Plan: Escape FASTA record markers in FHR header lines

**Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Add rule R11 to docs/FORMAT.md, conformance vectors for it, and a pointer in
docs/TOOL_COMPATIBILITY.md (this repository); make the toolkit's FASTA header writer escape `>` and
`@` and its validators warn on raw ones (FAIR-bioHeaders-Tools).

## Technical context

- Specification: Markdown docs, `scripts/make_conformance.py` (stdlib only), the manifest and its
  checks. No schema, LinkML or JSON-LD change.
- Toolkit: Python 3.9+, PyYAML. `fhr.output_fasta()` is the single FASTA header writer (combine for
  FHR and FHP goes through it); GFA and GFF3 writers are unchanged.

## Constitution check

- Byte preservation: unchanged; the escapes are written only into new FHR header lines.
- Minimal required metadata: unchanged; no field is added.
- Compatibility: existing files stay valid; output for metadata without the characters is
  byte-identical (SC-002).

## Project structure

- `docs/FORMAT.md` (R11), `docs/FHP.md`, `docs/TOOL_COMPATIBILITY.md`, `conformance/README.md`,
  `CHANGELOG.md`
- `scripts/make_conformance.py`, `conformance/manifest.json`, three new vectors
- `tests/test_conformance.py`, `tests/test_jsonld_roundtrip.py` (vector counts)
- Toolkit: `bioheaders/__init__.py` (`_FastaDumper`, `RECORD_MARKERS`, `record_marker_warnings`,
  `output_fasta`), `bioheaders/cli.py` (warnings), `tests/record_markers_test.py`, CHANGELOG

## Gates

Specification: unittest, `validate_examples.py`, `check_linkml.py`, `check_schema_drift.py`,
`make_jsonld.py --check`, `check_conformance.py` (stdlib only), `--schema`, and `--converter` with
the toolkit branch. Toolkit: pytest on 3.9 and 3.13, ruff, isort, black, `poetry build`, the
installed wheel outside the checkout.

## Release line

On `main`. The toolkit change ships in the next toolkit release (not part of this feature).
