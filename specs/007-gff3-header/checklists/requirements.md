# Specification Quality Checklist: GFF3 annotation header (FHGFF3)

**Purpose**: Check that the specification is complete and of good quality before planning
**Created**: 2026-10-13
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [ ] No [NEEDS CLARIFICATION] markers remain (FR-006, FR-011 and FR-013 are open)
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

**Validation pass 1 (2026-10-13).**

- **Formats named on purpose.** GFF3 directives, the `#~` prefix, SHA-512/256, SeqCol, JSON, YAML
  and LinkML are domain contracts inherited from FHR, the GFF3 specification and spec 004, not
  implementation choices. The gff3-validator options (`--require-header`, `--no-header`,
  `--genome`) and rule IDs HDR-001 to HDR-009 are named because the spec must stay consistent with
  that published catalogue.
- **No programming language or library is named.** "Toolkit" means the existing FAIR-bioHeaders
  tools, as in specs 003 and 008.
- **Header-end rule settled here, not left open.** #54 decided that `##sequence-region` may be
  interleaved. FR-001 resolves the contradictory wording in the 2026-10-08 draft: the block ends at
  the first non-`#` nonblank line or at `##FASTA`. This matches the toolkit's existing GFA scan,
  gff3-validator HDR-004 and the tool survey, so it is not a maintainer question.
- **Conditional success criteria.** SC-001 depends on FR-013. FR-006's representation does not
  change any success criterion, only the schema shape.

**Clarify-style coverage scan (no questions asked at this stage).**

| Category | Status | Note |
| --- | --- | --- |
| Functional scope and behaviour | Clear | One genome, one taxon in v0.1 (FR-012) |
| Domain and data model | Partial | Genome-link representation (FR-006); required origin field (FR-013) |
| Interaction and UX flow | Clear | CLI behaviour reuses FHR/GFA (spec 008); validator modes unchanged |
| Non-functional quality | Clear | Streaming, byte preservation and offline operation inherited (FR-002, FR-004) |
| Integration and external dependencies | Partial | Use of native directives (FR-011) |
| Edge cases and failure handling | Clear | Edge Cases section; R10 cases in FR-019 |
| Constraints and trade-offs | Clear | No fork files (FR-023); FHR unchanged (FR-005) |
| Terminology and consistency | Clear | `annotation`, `annotates`, `source` as in specs 004 and 006 |
| Completion signals | Clear | SC-001 to SC-010 |
| Misc and placeholders | Clear | Placeholders marked (FR-018) |

The three open items are the only ones whose answer changes the schema or the tools' contract. All
other ambiguities have a defensible default recorded in Assumptions.
