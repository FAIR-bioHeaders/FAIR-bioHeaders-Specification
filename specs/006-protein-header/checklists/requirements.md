# Specification Quality Checklist: Protein FASTA header (FHP)

**Purpose**: Check that the specification is complete and of good quality before planning
**Created**: 2026-10-10
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [ ] No [NEEDS CLARIFICATION] markers remain (3 remain, all maintainer decisions: FR-005, FR-007, FR-012)
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

**Validation pass 1 (2026-10-10).**

- **Formats named on purpose.** JSON, YAML, HTML microdata, JSON-LD, LinkML, SHA-512/256 and the
  `;~` prefix are domain contracts inherited from FHR (docs/FORMAT.md, spec 004), not
  implementation choices. They appear in the requirements for that reason.
- **No programming language or library is named.** "Toolkit" refers to the existing
  FAIR-bioHeaders tools, as specs 003 and 008 do.
- **Conditional success criteria.** SC-001 assumes `sourceType` stays required, which is FR-005,
  open. If maintainers make it optional, SC-001 becomes "core required fields plus `proteome`".

**Clarify-style coverage scan (no questions asked at this stage).**

| Category | Status | Note |
| --- | --- | --- |
| Functional scope and behaviour | Partial | Multi-species scope open (FR-012) |
| Domain and data model | Partial | `sourceType` meaning (FR-005); external-source representation (FR-007) |
| Interaction and UX flow | Clear | CLI behaviour reuses FHR (spec 008) |
| Non-functional: performance and scale | Clear | Streaming, as for FHR (edge cases) |
| Integration and external dependencies | Clear | Toolkit (008, Tools#33), assessment (010), JSON-LD (011), website |
| Edge cases and failure handling | Clear | Stops, rare residues, absent/different parents, R10 |
| Constraints and trade-offs | Clear | Core unchanged; FHR unaffected (SC-005) |
| Terminology and consistency | Clear | "Assertion" versus "check" defined (FR-013, FR-014) |
| Completion signals | Clear | SC-001–SC-007 |
| Placeholders and TODOs | Partial | Three markers, all maintainer-level |

Answer FR-005, FR-007 and FR-012 through `/speckit-clarify` (maintainers: Adam Wright, David
Molik) before `/speckit-plan`.
