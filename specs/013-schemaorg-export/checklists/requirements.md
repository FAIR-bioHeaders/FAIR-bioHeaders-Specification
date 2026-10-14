# Specification Quality Checklist: Enriched schema.org export

**Purpose**: Validate the specification's completeness and quality before planning
**Created**: 2026-10-14
**Feature**: [spec.md](../spec.md)

## Content quality

- [x] No implementation details in requirements beyond the named profile, files and commands that are the deliverables
- [x] Focused on user value: richer schema.org consumers, and subjects kept apart
- [x] All mandatory sections completed

## Requirement completeness

- [x] No [NEEDS CLARIFICATION] markers remain; the five questions were resolved in the 2026-10-14 session
- [x] Requirements are testable and unambiguous (FR-001 to FR-010 map to tests)
- [x] Success criteria are measurable (SC-001 to SC-006)
- [x] Acceptance scenarios cover every proposal on #56 and `seqcol_id`
- [x] Edge cases identified (absent fields, no export context, URL-like text, unmapped keys)
- [x] Scope bounded: specimens deferred to #101; FHP and FHGFF3 exports deferred
- [x] Dependencies and assumptions identified (schema.org v30.1 pin, UO IRIs, DOI IRI form)

## Feature readiness

- [x] The canonical form is unchanged apart from one generated vocabulary triple (FR-002, SC-002)
- [x] No invented values (FR-004, SC-003)
