# Agent instructions

## Repository identity and ownership

Determine the repository from its Git remote before applying this shared file.
These instructions are maintained in FAIR-bioHeaders-Specification and ported as
an AGENTS.md-only commit into the type repositories. A copied family tree does
not make every repository the publication authority, nor justify merging an
entire unrelated repository history for a guidance update.

| Repository | Current role |
| --- | --- |
| FAIR-bioHeaders-Specification | Shared core, format rules, released schemas for all adopted types, version registry, vocabulary, mappings and cross-type conformance. |
| FHR-Specification | FHR development; preserve compatibility files serving established raw URLs and historical tags. |
| FHP-Specification | Protein-header development; inherited FHR/family files are compatibility/history, not evidence of FHP ownership of those types. |
| FHT-Specification | Transcriptome-header development; reconcile the legacy draft with the reviewed family contract before claiming toolkit support. |
| FHGFF3 | Annotation-header development; inherited biodatamodels/gff-schema feature models are distinct from the FAIR header contract. |

David and Adam jointly hold schema and release authority. Read the shared
GOVERNANCE.md; its optional steering group is not active. Read the local README,
relevant issues, current files and applicable contribution/license instructions.
Do not let stale copied README, badges or citation identities override current
repository roles. The retired FHT-File-Converter is an archive; active family
conversion/validation belongs in FAIR-bioHeaders-Tools. Core GFF3 feature
validation belongs in gff3-validator, separate from optional FHGFF3 headers.

The [2024 FHR paper](https://doi.org/10.1093/bib/bbae122) motivates small required
metadata, provenance close to data and interoperability. Preserve supplied
metadata and sequence bytes; do not invent identifiers, authors, source material,
software, SeqCol digests or scientific relationships.

## Schema additions and their own development cycle

A new optional field, structured alternative, enum value, constraint, required
field or changed meaning is a schema-contract change, even when motivated by a
UI, exporter, parser fix or documentation task. Identify it explicitly as a
**schema addition** or other contract change in its issue and PR. Supporting an
already adopted field in a consumer is implementation work, not a new field.

Schema additions have their own proposal, review, compatibility, versioning and
release cycle. Keep them separately reviewable from routine fixes, website work,
packaging and dependency updates; link dependent implementation PRs rather than
silently adopting a field downstream. Shared fields/objects and cross-type rules
belong in FAIR-bioHeaders-Specification; type-specific design starts in the owning
development repository and is coordinated into shared publication. Name affected
types, requiredness, semantics, mappings, serializers and conformance fixtures.

During active construction of FHP, FHT and FHGFF3, maintainers may iterate on draft
fields with lighter process and include coordinated schema/implementation work in
one clearly scoped PR. Record the proposal and compatibility impact in that PR;
this flexibility does not make every field adopted or supported. Preserve already
published contracts and cited versions, label draft behavior, and obtain joint
maintainer review before publication. FHR additions retain the separate cycle.
Do not apply draft flexibility to released FHP/FHGFF3 schemas retroactively.

Use the shared specification's `docs/SCHEMA-VERSIONS.md` and
`schemas/versions.json`: contract versions are per type, distinct from repository
release tags and biological resource versions. Additive changes that preserve all
valid values and meanings qualify for a minor increment; invalidating records or
changing meanings requires a major increment. Do not assign a new version merely
for implementing an existing contract. Never rewrite immutable releases, fixed
schema aliases or existing file-bound headers as incidental cleanup. Header edits
require checksum recomputation and may affect downstream parent links.

Proposals are not adopted contracts: FAIR-bioHeaders-Specification#139 / draft
PR #140 (structured vouchers) and profiles still under review in that repository
(#56) remain proposals until adopted. Implemented subsets do not establish full
profile or header-family support. The mapping page in fair-bioheaders.github.io#29
depends on approved profiles.

## Models, generated artifacts and compatibility

In the shared publication tree, `schemas/core.yaml` defines common slots and
objects; `schemas/shared.yaml` holds additional objects used by FHP/FHGFF3.
Root classes opt into slots: changing a shared definition requires checking every
importing type, not just the motivating FHR example. Keep voucher evidence
separate from `derivedFrom` parent-file relationships.

`fhr.json` is the published FHR validation contract; `fhr_linkml.yml` must agree.
Generate `fhp.json` and `fhgff3.json` from their LinkML models using
`json-schema-generator.py --type fhp` / `--type fhgff3`; do not hand-edit those
outputs. Review schema diffs before updating drift baselines. Preserve canonical
JSON-LD round trips separately from one-way schema.org/DCMI/MIxS projections;
report conditions, unsupported fields and losses rather than invent equivalence.
Generate contexts/vocabulary via `scripts/make_jsonld.py`, where present.

Only use paths and commands present in the checkout. FHT currently has a legacy
`fht.json` and examples; FHGFF3 has inherited feature-model sources and generated
formats. Do not pretend these trees already contain the shared publication
build/test machinery. Review their README/Makefile and coordinate adoption with
the shared repository rather than copying incompatible generated artifacts.

Honor cited supported schema releases and shared schema-selection rules; never
silently substitute current main for an unknown release. Raw-main is a current
contract link, not an immutable version. Keep supported old-name URL aliases and
published example/vector bytes intact. Exact file checksum coverage follows
`docs/FORMAT.md`; SeqCol identifies sequence collections and is not a file checksum.

## Using FAIR-bioHeaders in another project

For assistants and people adding FAIR-bioHeaders headers to data elsewhere (summary in
[the shared `llms.txt`](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/llms.txt)):

- Use the `fair-bioheaders` tools (`pip install fair-bioheaders`): `bioheaders combine
  metadata.yaml genome.fa -o genome.fhr.fa` adds a header and computes the checksum;
  `bioheaders verify` checks it; `bioheaders strip` removes it. Never write or edit a
  checksum by hand. The Claude Code plugin in FAIR-bioHeaders-Tools
  (`plugins/fair-bioheaders`) packages these steps as a skill.
- Cite a versioned schema in `schema` (`https://w3id.org/fair-bioheaders/fhr/v0.4.0`,
  `.../fhp/v0.4.0`, `.../fhgff3/v0.4.0`) with its `schemaVersion` from
  `schemas/versions.json`. Required fields are in `fhr.json`, `fhp.json` and
  `fhgff3.json`; never invent values for them.
- Strict FASTA readers (samtools faidx and the rest of htslib, Picard, Biopython's default
  `fasta` format and others in `docs/TOOL_COMPATIBILITY.md`) reject a leading `;~`
  block: strip it first, or use Biopython's `fasta-pearson`.
- FASTA header values with `>` or `@` are escaped as `\x3E` and `\x40` (FORMAT.md R11).
- Keep `llms.txt` current when a release changes schema versions, URLs or commands;
  `tests/test_llms_txt.py` checks the versions and required fields.

## Verification

For AGENTS.md-only changes, inspect the diff, links and repository identity and
run `git diff --check`; executable/schema suites are unnecessary unless behavior
changes. For model/schema changes, run relevant commands where available:

```sh
python -m unittest discover -s tests -v
python scripts/validate_examples.py
python scripts/check_linkml.py
python scripts/check_schema_drift.py
python scripts/make_jsonld.py --check
```

Use the checkout's requirements files to prepare the environment when needed.
Check legacy and new valid/rejected instances, all affected header types, typed
serialization round trips and escaping. Coordinate toolkit schema bundles and
version-aware consumers in linked PRs; do not assume sibling checkout tests use
installed release bytes. Record checks actually run and environment limitations.
Update guidance, fixtures, release notes and version records with behavior changes.
Publishing releases, tags, DOIs or deployments remains a separate maintainer action.

## Licensing and historical material

New FAIR BioHeaders contributions from March 2025 onward use MPL-2.0, subject to
the local LICENSE. Preserve historical USDA public-domain material and third-party
permissions/notices. David Molik left USDA in February 2025; do not classify all
contributors as government employees or rewrite historical releases. In FHGFF3,
MPL-2.0 on FAIR BioHeaders contributions does not resolve the inherited
biodatamodels/gff-schema licensing question. Preserve upstream notices and do not
assert permission that has not been established.
