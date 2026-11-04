# Specification Quality Checklist: Extension fields

**Purpose**: Validate the specification's completeness and quality before planning
**Created**: 2026-11-03
**Feature**: [spec.md](../spec.md)

## Content quality

- [x] No implementation details in requirements beyond the rule, pattern and versions that are the deliverables
- [x] Focused on user value: valid headers that carry project-specific metadata
- [x] All mandatory sections completed

## Requirement completeness

- [x] No [NEEDS CLARIFICATION] markers remain; the maintainers answered every open question (Clarifications)
- [x] Requirements are testable (FR-001 to FR-011 map to vectors and tests)
- [x] Success criteria are measurable (SC-001 to SC-004)
- [x] Edge cases identified (key pattern, YAML typing, values, look-alike names, older versions)
- [x] Scope bounded: top level only; JSON-LD and microdata carry no extension fields

## Compatibility

- [x] Every record valid under FHR 2.0, FHP 1.0 and FHGFF3 1.0 stays valid with the same meaning
- [x] Every existing conformance vector keeps its id, bytes and outcome
- [x] Version selection rules V1 to V6 are unchanged
