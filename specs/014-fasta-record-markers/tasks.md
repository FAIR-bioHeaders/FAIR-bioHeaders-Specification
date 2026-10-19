# Tasks: Escape FASTA record markers in FHR header lines

## Phase 1: Specification

- [X] T001 Rule R11 in `docs/FORMAT.md`; R1 to R11 in `docs/FHP.md` and `conformance/README.md`
- [X] T002 R11 in `scripts/make_conformance.py` `RULES` and `NOT_APPLICABLE`; vectors
  `fasta-escaped-record-markers`, `fasta-raw-record-markers`, `fhp-fasta-escaped-record-markers`
  with the decoded value in their expected metadata; regenerate `conformance/`
- [X] T003 Update the vector counts in `tests/test_conformance.py` and `tests/test_jsonld_roundtrip.py`
- [X] T004 Point the kseq caveat in `docs/TOOL_COMPATIBILITY.md` to R11; CHANGELOG
- [X] T005 Record the seqtk, bioawk and `samtools dict` evidence (research R-01)

## Phase 2: Toolkit (FAIR-bioHeaders-Tools)

- [X] T006 `_FastaDumper` and `RECORD_MARKERS`; `output_fasta` escapes after dumping
- [X] T007 `record_marker_warnings`; warnings in `_verify` and `_validate` (leading block only)
- [X] T008 `tests/record_markers_test.py`: escaping, round trip, other formats, byte-identical
  output without markers, edge strings, warnings for the three commands, FHP
- [X] T009 README and CHANGELOG

## Phase 3: Gates

- [X] T010 All specification and toolkit gates (plan.md), including `check_conformance.py
  --converter` with the toolkit branch
