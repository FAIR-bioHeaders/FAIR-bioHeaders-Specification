# Contributing

Open issues about a released specification, the shared core, the format rules or the
conformance suite here. Development of one header type belongs in its own repository:
[FHR-Specification](https://github.com/FAIR-bioHeaders/FHR-Specification),
[FHP-Specification](https://github.com/FAIR-bioHeaders/FHP-Specification),
[FHT-Specification](https://github.com/FAIR-bioHeaders/FHT-Specification) or
[FHGFF3](https://github.com/FAIR-bioHeaders/FHGFF3).

Start with an issue describing the use case or failure and a small reproducible
example. Submit a focused branch/PR with behavior, compatibility implications,
and relevant validation. Link related work in [FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools)
and the release tracker when a change spans repositories. Do not include private
genome data, credentials, or unrelated formatting in fixtures.

## Setup and checks

See README for Python requirements and environment setup. From this checkout:

```bash
python -m pip install -r requirements-linkml.txt
python -m unittest discover -s tests -v
python scripts/validate_examples.py
python scripts/check_linkml.py
python scripts/check_schema_drift.py
```

Changes to metadata must coordinate `fhr.json`, the LinkML model, both converter
schema copies, serializers, examples, and documentation. Add regression tests
for changed behavior, including minimal metadata and relevant invalid cases.
Document checksum semantics and migration rather than silently changing identity.
Keep required metadata and runtime dependencies small.

David and Adam are the maintainers and jointly hold schema and release authority
([GOVERNANCE](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/GOVERNANCE.md)). The steering-group option described there is not active.
Follow CODE_OF_CONDUCT and use the SECURITY policy for sensitive findings. Private reporting addresses and independent conflict/appeal routing are documented there.

Release preparation does not authorize publishing packages, merging PRs, or
transferring repository ownership. Keep companion PRs linked for coordinated review.

## Coordinated documentation and citations

Guidance and README changes are tracked in [specification issue #23](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/23). Both private conduct/security contacts and the conflict/appeal routing are documented in the policies.

Use Chicago bibliography entries with DOI resolver links in human-readable citations. Keep the published paper, preprint, specification and converter distinct; preserve concept DOI meaning and existing BibTeX keys. CFF/BibTeX remain machine-readable metadata. The file audit and companion PRs are recorded in [FHR-Citation/AUDIT.md](https://github.com/FAIR-bioHeaders/FHR-Citation/blob/main/AUDIT.md), tracked by [issue #25](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/25).

## License of contributions

New project contributions from March 2025 onward use [MPL-2.0](LICENSE). David Molik left USDA in February 2025. Historical USDA public-domain material remains public domain within the United States; its original notice is preserved in LICENSE. Previously granted permissions and third-party terms remain intact. The project includes both historical material and subsequent MPL-2.0 contributions; file notices and history identify provenance. New contributions must have the rights needed for their declared license; retain source notices.
