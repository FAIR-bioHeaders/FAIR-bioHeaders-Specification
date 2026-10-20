# Draft descriptive bundle for issue #56

- `source.json`: byte-for-byte copy of `examples/example.fhr.json` at shared
  repository commit `2da7c96` (released FHR v0.4.0 contract, schemaVersion 2.0).
  It is a synthetic metadata example, not a verified assembly; the checksum is
  an existing placeholder. No immutable header or sequence bytes were edited.
- `context.json`: synthetic, separate export assertions under draft context
  profile `0.1.0-draft.1`. `example.org` subjects/publisher are illustrative;
  resource DOI is deliberately absent. The issue-date example is 2026, whereas
  source assembly creation is 2022; this tests that these dates are distinct.
- `qualified-dc.ttl`: manually curated expected descriptive graph, not generated
  by a shipped exporter. It is neither a DOI deposit nor a lossless record.
- `report.json`: explicit preservation/omission and readiness boundaries.

Retain source and context with any downstream projection. The graph does not
preserve all nested values, classifications or array ordering. Person names and
ORCID strings come from the existing synthetic source fixture; do not interpret
this example as new claims about real research contributions. MPL-2.0 applies.
