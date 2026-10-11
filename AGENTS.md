# Agent instructions

## Strategy and boundaries

Read README, relevant issue requirements, and current code before editing. The
[2024 FHR paper](https://doi.org/10.1093/bib/bbae122) motivates minimal metadata,
multiple serializations, provenance tied closely to data, compatibility, FAIR,
and TRUST. Practical interpretation: preserve user metadata and sequence bytes,
keep required fields/dependencies small, and prefer interoperable incremental
changes over speculative frameworks. These are implementation guidelines inferred
from the paper, not quotations or governance rules.

David and Adam are the maintainers and jointly hold schema and release authority
(GOVERNANCE.md). The documented steering-group option is not active; do not treat
it as current authority.

## Repository map

`fhr.json` is the published contract; `fhr_linkml.yml` is its LinkML model, which imports the family-wide core in `schemas/core.yaml`. The draft protein header FHP has `fhp_linkml.yml`, from which `fhp.json` is generated (`json-schema-generator.py --type fhp`; never edit `fhp.json` by hand), examples in `examples/fhp/`, `docs/FHP.md`, its own drift baseline `.github/schema-baseline-fhp.json`, and `fhp-fasta` conformance vectors. `json-schema-generator.py` generates a separate schema. `scripts/check_linkml.py` compares validation constraints, and `scripts/check_schema_drift.py` checks the explicit review baseline. `fhr_mappings.yml` and `scripts/project_mixs.py` define a partial MIxS/MIGS projection. `jsonld/` holds the JSON-LD context and the FAIR-bioHeaders vocabulary, generated with `docs/TERMS.md` and `examples/*.fhr.jsonld` by `scripts/make_jsonld.py` from the LinkML annotations (never edit them by hand). `mappings/fhr-jsonld-dcmi.yml` maps every FHR field to its JSON-LD term and DCMI Terms equivalents: term IRIs come from LinkML; the mapping table is curated and test-checked against it. Examples, docs, and `Diagram.svg` must agree.

## Verification

Run relevant checks from the repository root:

```bash
python -m pip install -r requirements-linkml.txt
python -m pip install -r requirements-jsonld.txt
python -m unittest discover -s tests -v
python scripts/validate_examples.py
python scripts/check_linkml.py
python scripts/check_schema_drift.py
python scripts/make_jsonld.py --check
```

For schema changes, inspect compatibility of valid existing instances, required
fields, types, unknown-property policy, patterns, URI/date formats, and optional
values. Synchronize the published schema and both converter copies. Review the
schema diff before intentionally updating `.github/schema-baseline.json`; never
refresh it simply to hide a failed check. For serialization changes, test all
formats and HTML escaping/typed values. For sequence tools, test metadata and
sequence tampering, CRLF, ordinary comments, combine/strip, and installed commands
from outside the checkout. Record environment limitations and failed checks.

Use exact file bytes for SHA-512/256 coverage except the scalar checksum line;
read the format policy before editing checksum behavior. SeqCol is a supplied
collection identifier, not an FHR checksum. Use authoritative pinned MIxS terms
and report partial/lossy mappings explicitly; do not invent accessions or metadata.

Update examples, README, citations, and release notes alongside behavior changes.
Keep cross-repo PR links current. Publishing, adoption of governance, and reporting
contact confirmation are separate maintainer actions. Do not fabricate contacts
or claim a policy has been adopted.

## Licensing policy (2026-10-09)

New FAIR BioHeaders project contributions from March 2025 onward use MPL-2.0.
David Molik left USDA in February 2025. Preserve historical USDA public-domain
material, previously granted permissions, and third-party licenses/notices;
do not label all current contributors as government employees. See LICENSE
for scope. Do not rewrite historical releases or silently relicense upstream
material. Keep README badges, package metadata and citation metadata consistent.
