# Contract: gff3-validator header rules (HDR-004 to HDR-010)

**Feature**: 007-gff3-header | Research: D-11

- **When they run**: header mode `auto` or `require`, header lines present, and the installed
  `fair-bioheaders` has `FHGFF3_SCHEMA`.
- **Otherwise**: HDR-002 as today. Mode `skip` gives HDR-003, and no header with `require` gives
  HDR-001.

| Rule | Level | Result from `gff3_header_report` |
|---|---|---|
| HDR-004 | error | `placement` |
| HDR-005 | error | `checksum` |
| HDR-006 | error | `yaml` |
| HDR-007 | error | `schema` |
| HDR-008 | error | `genome_link` |
| HDR-009 | error | `genome_match == "not matched"` with `--genome`. `not checked` is reported as info text, not an error |
| HDR-010 | warning | one finding per cross-check warning (new rule) |

- **Separate layers**: header findings are in the `fhgff3` layer. Feature findings are never
  suppressed or added because of the header (FR-016).
- **Plain GFF3**: a file without a header and without `--require-header` has no header finding.
- **Catalogue**: HDR-004 to HDR-009 change to `status: implemented`. HDR-010 is added. The
  catalogue copy in the package is updated to match.
- **Browser build**: unchanged (HDR-002). Follow-up F-04.
