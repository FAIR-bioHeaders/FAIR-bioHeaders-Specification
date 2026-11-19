"""Generate the legacy-draft positive/rejection fixtures (issue #14).

Recreates tests/fixtures/legacy/. The fixtures exercise the behavior of the
preserved legacy draft legacy/fht-v0.1.json (measured with jsonschema 4.26.0,
Draft2020-12 dialect, explicit FormatChecker) — never the current contract.
Checksum/ORCID/DOI values are synthetic placeholders reused from the repo's
existing test conventions; no real biological provenance is implied.
"""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "legacy"

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
    "checksum": "A" * 43 + "=",
}

RICH = copy.deepcopy(VALID_BASE)
RICH.update(
    {
        "transcriptomeSynonym": ["Example synonym"],
        "voucherSpecimen": "Example freezer, synthetic placeholder",
        "accessionID": {"name": "Example DB", "url": "https://example.org/x"},
        "instrument": ["Example sequencer"],
        "scholarlyArticle": "10.1234/abc",
        "documentation": "https://example.org/doc",
        "identifier": ["example:TC000001"],
        "relatedLink": ["https://example.org/related"],
        "funding": "Example grant",
        "license": "CC0-1.0",
        "vitalStats": {
            "N50": 1200,
            "totalTranscripts": 34567,
            "averageTranscriptLength": 1873.42,
            "GCContent": 36.1,
        },
    }
)


def rejected(name, mutate):
    value = copy.deepcopy(VALID_BASE)
    mutate(value)
    return name, value


def drop(key):
    return lambda value: value.pop(key)


def set_(key, item):
    return lambda value: value.__setitem__(key, item)


CASES = [
    ("missing-checksum.json", drop("checksum")),
    ("missing-masking.json", drop("masking")),
    ("unknown-top-level-property.json", set_("maskingPolicy", "soft")),
    (
        "schemaversion-string.json",
        set_("schemaVersion", "1.0"),
    ),
    ("transcriptome-number.json", set_("transcriptome", 42)),
    ("masking-hard-masked.json", set_("masking", "hard-masked")),
    (
        "checksum-md5-prefixed.json",
        set_("checksum", "md5:7582b26fcb0a9775b87c38f836e97c42"),
    ),
    ("checksum-bad-charset.json", set_("checksum", "A" * 40 + ":::=")),
    ("datecreated-prose.json", set_("dateCreated", "22 March 2022")),
    ("taxon-uri-no-pattern.json",
     set_("taxon", {"name": "Arabidopsis thaliana",
                    "uri": "https://example.org/taxonomy"})),
    ("relatedlink-not-a-uri.json", set_("relatedLink", ["not a uri"])),
]

EXPECTED = {
    "missing-checksum.json": [{"path": [], "contains": ["'checksum' is a required property"]}],
    "missing-masking.json": [{"path": [], "contains": ["'masking' is a required property"]}],
    "unknown-top-level-property.json": [
        {"path": [], "contains": ["Additional properties are not allowed", "'maskingPolicy'"]}
    ],
    "schemaversion-string.json": [
        {"path": ["schemaVersion"], "contains": ["is not of type 'number'"]}
    ],
    "transcriptome-number.json": [
        {"path": ["transcriptome"], "contains": ["is not of type 'string'"]}
    ],
    "masking-hard-masked.json": [
        {"path": ["masking"], "contains": ["does not match", "not-masked"]}
    ],
    "checksum-md5-prefixed.json": [
        {"path": ["checksum"], "contains": ["is too short"]},
        {"path": ["checksum"], "contains": ["does not match", "[A-Za-z0-9/+=]"]},
    ],
    "checksum-bad-charset.json": [
        {"path": ["checksum"], "contains": ["does not match"]}
    ],
    "datecreated-prose.json": [
        {"path": ["dateCreated"], "contains": ["is not a 'date'"]}
    ],
    "taxon-uri-no-pattern.json": [
        {"path": ["taxon", "uri"], "contains": ["does not match"]}
    ],
    "relatedlink-not-a-uri.json": [
        {"path": ["relatedLink", "0"], "contains": ["is not a 'uri'"]}
    ],
}


def main():
    (FIXTURES / "valid").mkdir(parents=True, exist_ok=True)
    (FIXTURES / "rejected").mkdir(parents=True, exist_ok=True)
    (FIXTURES / "valid" / "full-legacy-record.json").write_text(
        json.dumps(RICH, indent=2) + "\n", encoding="utf-8"
    )
    for name, mutate in CASES:
        value = copy.deepcopy(VALID_BASE)
        mutate(value)
        (FIXTURES / "rejected" / name).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )
    (FIXTURES / "rejected" / "expected.json").write_text(
        json.dumps(EXPECTED, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote", FIXTURES)


if __name__ == "__main__":
    main()
