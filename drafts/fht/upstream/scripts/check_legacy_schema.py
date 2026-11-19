"""Schema-health check for the legacy FHT draft (issue #14).

Validates ``legacy/fht-v0.1.json`` — the preserved pre-contract draft, not the
current FHT 1.0 development contract — and records its defects explicitly
instead of silently amending the contract. The legacy bytes are immutable:
their pinned SHA-256 must match ``legacy/README.md``.

Procedure (documented in docs/CI.md):

1. Parse the file as JSON and detect its declared JSON Schema dialect from
   ``$schema`` with ``jsonschema.validators.validator_for``. The declared
   dialect is ``https://json-schema.org/draft/2020-12/schema``, so the matching
   pinned validator is ``Draft202012Validator`` (jsonschema 4.26.0).
2. Meta-validate the schema with that dialect's ``check_schema``.
3. Enable format checking explicitly (``FormatChecker`` from
   ``jsonschema[format]``) and prove with probes that ``date``/``uri`` formats
   are enforced only with the checker — the legacy contract relies on it.
4. Run the defect registry: each known defect is a live probe asserting the
   measured current behavior (accept/reject). The registry fails if a probe
   changes meaning — either someone edited the preserved bytes (caught also by
   the digest) or the pinned validator changed behavior. Defects are
   documented, never patched here.

Local usage (pinned environment; see docs/CI.md):

    python -m pip install "jsonschema[format]==4.26.0"
    python scripts/check_legacy_schema.py

Exit status is 0 when the legacy draft parses, meta-validates under its
declared dialect and every probe matches its recorded expectation.
"""

import hashlib
import json
import sys
from pathlib import Path

from jsonschema import FormatChecker, validators
from importlib.metadata import version as package_version

ROOT = Path(__file__).resolve().parents[1]
LEGACY_PATH = ROOT / "legacy" / "fht-v0.1.json"
LEGACY_README = ROOT / "legacy" / "README.md"

# The legacy draft is preserved verbatim. This digest is also recorded in
# legacy/README.md; a mismatch means the historical bytes moved.
LEGACY_SHA256 = "34eec2e5c0dd9355ec3ffe3bdff8861d80345336d779b94b5e8a3ccf8ea894aa"
DECLARED_DIALECT = "https://json-schema.org/draft/2020-12/schema"
EXPECTED_VALIDATOR = "Draft202012Validator"

CHECKSUM_PLACEHOLDER = "A" * 43 + "="  # synthetic; NOT a real digest

# A record valid against the legacy draft under explicit format checking. The
# values are synthetic except identifiers reused from this repository's own
# historical material; nothing here claims real biological provenance.
VALID_BASE = {
    "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/"
              "FHT-Specification/main/fht.json",
    "schemaVersion": 0.1,
    "transcriptome": "Example legacy transcriptome",
    "taxon": {
        "name": "Arabidopsis thaliana",
        "uri": "https://identifiers.org/taxonomy:3702",
    },
    "version": "1.0",
    "metadataAuthor": [{"name": "Example author"}],
    "assemblyAuthor": [{"name": "Example assembler"}],
    "dateCreated": "2024-01-01",
    "masking": "not-masked",
    "checksum": CHECKSUM_PLACEHOLDER,
}

# Defect registry: measured current behavior of the preserved legacy draft.
# ``want`` is what the draft actually does today (this check asserts it),
# never what a future contract should do. Future/adopted constraints live in
# the current draft (fht.json, tests/test_fht_schema.py) and docs/FHT-MIGRATION.md.
DEFECTS = [
    {
        "id": "L1-unanchored-taxon-uri",
        "want": "accept",
        "patch": {"taxon": {"name": "X",
                            "uri": "junk-https://identifiers.org/taxonomy:123-trailing"}},
        "note": "taxon.uri pattern 'https://identifiers.org/taxonomy:[0-9]+' is "
                "unanchored and its dots are unescaped: leading/trailing junk and "
                "'identifiersXorg' all match (re.search semantics). The current "
                "draft anchors this with ^...$.",
    },
    {
        "id": "L2-unanchored-orcid-pattern",
        "want": "accept",
        "patch": {"metadataAuthor": [{"name": "A",
                                      "uri": "https://orcid.org/0000-0002-5719-4024-evil"}]},
        "note": "definitions.orcidUri pattern has no end anchor and unescaped "
                "dots, so trailing junk after a valid ORCID iD passes.",
    },
    {
        "id": "L3-scholarly-article-loose-pattern",
        "want": "accept",
        "patch": {"scholarlyArticle": "10X"},
        "note": "scholarlyArticle pattern '^10.' uses an unescaped dot and no "
                "suffix requirement: '10X' passes as a DOI.",
    },
    {
        "id": "L4-unanchored-identifier-pattern",
        "want": "accept",
        "patch": {"identifier": ["PREFIX beetlebase:TC1"]},
        "note": "identifier items pattern '[a-z0-9]*:.*' is unanchored; any "
                "string containing 'x:' somewhere matches.",
    },
    {
        "id": "L5-nested-objects-allow-unknown-keys",
        "want": "accept",
        "patch": {"assemblyAuthor": [{"name": "A",
                                      "url": "https://orcid.org/0000-0002-5719-4024"}]},
        "note": "Only the top level sets additionalProperties: false; nested "
                "objects (taxon, authors, accessionID, vitalStats) accept unknown "
                "keys, so a 'url'-instead-of-'uri' typo — present in the "
                "historical example — is silently accepted. The current draft "
                "closes every object and allows only top-level x- extensions.",
    },
    {
        "id": "L6-no-nested-required-fields",
        "want": "accept",
        "patch": {"metadataAuthor": [{}], "taxon": {"uri": "https://identifiers.org/taxonomy:3702"}},
        "note": "Author entries and taxon require nothing: an empty author "
                "object and a nameless taxon validate.",
    },
    {
        "id": "L7-masking-unanchored-and-required",
        "want": "accept",
        "patch": {"masking": "who knows? unknown"},
        "note": "masking is required but its alternation is unanchored, so any "
                "string containing one of the words passes ('soft-masked' from "
                "the historical example is rejected, 'who knows? unknown' is "
                "accepted). Masking was dropped from the current draft.",
    },
    {
        "id": "L8-checksum-is-shape-only",
        "want": "accept",
        "patch": {"checksum": "A" * 43 + "="},
        "note": "definitions.sha2 constrains only length 44 and the base64 "
                "character set; any 44-character filler validates and no "
                "algorithm or byte coverage is defined. Real SHA-512/256 "
                "byte-coverage rules belong to the shared FORMAT.md and #8.",
    },
    {
        "id": "L9-schema-version-is-a-number",
        "want": "reject",
        "patch": {"schemaVersion": "1.0"},
        "fragment": "is not of type 'number'",
        "note": "schemaVersion is typed 'number' (historical examples use 1 or "
                "1.0); the string MAJOR.MINOR convention of the current draft "
                "is rejected here. This probe records the direction of the "
                "incompatibility, not a preference for the legacy typing.",
    },
    {
        "id": "L10-formats-only-enforced-with-explicit-checker",
        "want": "reject",
        "patch": {"dateCreated": "22 March 2022"},
        "fragment": "is not a 'date'",
        "note": "dateCreated declares format: date and author/accessionID/"
                "relatedLink declare format: uri. JSON Schema treats formats "
                "as annotations unless the validator enables them; this check "
                "passes a FormatChecker explicitly, and the paired "
                "no-checker probe above shows the difference.",
    },
    {
        "id": "L11-schema-id-identity-clash",
        "want": "accept",
        "patch": {},
        "note": "the legacy $id is "
                "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-"
                "Specification/main/fht.json — today that URL serves the "
                "current FHT 1.0 draft. Instances that cite the raw-main URL "
                "in 'schema' therefore do not pin the legacy contract; cite "
                "this file's archived path or tag for audit use.",
    },
]

# Requirement loop: every entry of the legacy 'required' list must be enforced.
def required_probes():
    for name in VALID_BASE:
        yield name


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def errors_for(validator, instance):
    return sorted(
        ("/".join(str(p) for p in error.absolute_path), error.message)
        for error in validator.iter_errors(instance)
    )


def main():
    failures = []

    def report(ok, label, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'} {label}" + (f": {detail}" if detail else ""))
        if not ok:
            failures.append(label)

    print("Legacy draft schema health (not the current FHT 1.0 contract)")
    print(f"  file: legacy/fht-v0.1.json  validator: jsonschema {package_version('jsonschema')}")

    try:
        raw = LEGACY_PATH.read_text(encoding="utf-8")
    except OSError as error:
        print(f"FAIL: cannot read {LEGACY_PATH}: {error}", file=sys.stderr)
        return 1
    digest = sha256(LEGACY_PATH)
    report(digest == LEGACY_SHA256, "preserved-bytes digest",
           f"{digest}")
    readme_digest = LEGACY_SHA256 in LEGACY_README.read_text(encoding="utf-8")
    report(readme_digest, "legacy/README.md records the same digest")

    try:
        schema = json.loads(raw)
    except ValueError as error:
        print(f"FAIL: legacy fht-v0.1.json is not valid JSON: {error}", file=sys.stderr)
        return 1
    report(True, "JSON parse")

    dialect = schema.get("$schema")
    report(dialect == DECLARED_DIALECT, "declared dialect", str(dialect))
    validator_cls = validators.validator_for(schema)
    report(validator_cls.__name__ == EXPECTED_VALIDATOR,
           "matching validator selected from declared dialect",
           validator_cls.__name__)
    try:
        validator_cls.check_schema(schema)
        meta_ok, meta_detail = True, "meta-validates under declared dialect"
    except Exception as error:
        meta_ok, meta_detail = False, str(error)[:200]
    report(meta_ok, "schema meta-validation", meta_detail)

    with_formats = validator_cls(schema, format_checker=FormatChecker())
    without_formats = validator_cls(schema)
    report(not errors_for(with_formats, VALID_BASE),
           "baseline valid record (explicit format checking on)")
    prose_date = dict(VALID_BASE, dateCreated="22 March 2022")
    report(bool(errors_for(with_formats, prose_date))
           and not errors_for(without_formats, prose_date),
           "format checking demonstrably explicit",
           "'date' violations surface only with the FormatChecker this check "
           "enables, as required by the issue")

    print("Defect registry (documented behavior of the preserved draft; the "
          "contract itself is not amended):")
    for defect in DEFECTS:
        instance = dict(VALID_BASE)
        instance.update(defect["patch"])
        errors = errors_for(with_formats, instance)
        if defect["want"] == "accept":
            ok = not errors
            detail = defect["note"]
        else:
            ok = any(defect["fragment"] in message for _, message in errors)
            detail = f"{defect['note']} (expected message fragment: " \
                     f"{defect['fragment']!r})"
        report(ok, f"{defect['id']} -> {defect['want']}s as recorded", detail)

    print("Required-field enforcement (the legacy draft's own 'required' list):")
    for name in required_probes():
        instance = dict(VALID_BASE)
        del instance[name]
        errors = errors_for(with_formats, instance)
        ok = any(f"'{name}' is a required property" == message for _, message in errors)
        report(ok, f"missing {name!r} is rejected")

    unknown = dict(VALID_BASE)
    unknown["totallyUnknown"] = True
    report(any(path == ""
               and message.startswith("Additional properties are not allowed")
               and "totallyUnknown" in message
               for path, message in errors_for(with_formats, unknown)),
           "unknown top-level property is rejected")

    if failures:
        print(f"\nLegacy schema health failed: {len(failures)} finding(s)", file=sys.stderr)
        return 1
    print("\nLegacy schema health passed: dialect detected, schema meta-valid, "
          "formats explicit, defect registry matches measured behavior.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
