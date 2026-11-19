"""Generate fht.json from the FHT LinkML model.

The model imports the pinned shared core and shared objects under ``schemas/``.
``fht.json`` is generated, never hand-edited. The generator also applies the
FHT-specific parent rule that LinkML cannot express: a derivedFrom item must be
a reviewed FHT/FHR relationship. The shared DerivedFrom object already requires
the parent checksum; an accessionID is additional, never a substitute.
"""

import argparse
import json
from pathlib import Path

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime import SchemaView

ROOT = Path(__file__).resolve().parent
DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID = (
    "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json"
)
# Core string slots whose exact length LinkML cannot express.
EXACT_LENGTHS = {"checksum": 44, "seqcol_id": 32}
# Optional arrays that are omitted when empty, rather than written as [].
NON_EMPTY_ARRAYS = {
    "transcriptomeSynonym",
    "assemblyAuthor",
    "assemblySoftware",
    "sample",
    "sequencingRuns",
    "instrument",
    "derivedFrom",
}
# Reviewed FHT parent relationships (issue #7). Other relationships are
# deferred to the shared vocabulary decision (#54).
ALLOWED_PARENTS = [
    {
        "properties": {
            "headerType": {"const": "FHT"},
            "relationship": {"const": "filteredFrom"},
        },
        "required": ["headerType", "relationship"],
    },
    {
        "properties": {
            "headerType": {"const": "FHR"},
            "relationship": {"const": "transcribedFrom"},
        },
        "required": ["headerType", "relationship"],
    },
]


def apply_common_rules(generated):
    """Normalize schemaVersion, exact lengths and optional-array cardinality."""
    nodes = (generated, *generated.get("$defs", {}).values())
    for node in nodes:
        version = node.get("properties", {}).get("schemaVersion", {})
        if "const" in version:
            version["enum"] = [version.pop("const")]
        for name, length in EXACT_LENGTHS.items():
            if name in node.get("properties", {}):
                node["properties"][name].update(minLength=length, maxLength=length)
        for name in NON_EMPTY_ARRAYS:
            prop = node.get("properties", {}).get(name)
            if prop and prop.get("type") == "array":
                prop.setdefault("minItems", 1)
    generated["$schema"] = DIALECT
    return generated


REQUIRED_STRINGS = ("transcriptome", "version", "dateCreated")
# "Contains a non-blank character", written so Python's re (jsonschema) and
# ECMA-262 (ajv, browsers) give the same answer. "\\S" does not: Python counts
# U+001C-U+001F and U+0085 as whitespace and U+FEFF as not, ECMA-262 the
# reverse. The excluded set is the union of both dialects' whitespace, so a
# value is blank in one exactly when it is blank in the other. The same class
# is used in fht_linkml.yml.
NON_BLANK_CLASS = (
    "[^\\t-\\r \\x1c-\\x1f\\x85\\xa0\\u1680\\u2000-\\u200a"
    "\\u2028\\u2029\\u202f\\u205f\\u3000\\ufeff]"
)
NON_BLANK = {"minLength": 1, "pattern": NON_BLANK_CLASS}


def apply_required_value_rules(generated):
    """Reject empty required strings and empty/nameless metadata and assembly authors."""
    roots = [generated]
    if isinstance(generated.get("$defs", {}).get("FHT"), dict):
        roots.append(generated["$defs"]["FHT"])
    for node in roots:
        properties = node["properties"]
        for name in REQUIRED_STRINGS:
            properties[name]["minLength"] = 1
            properties[name].setdefault("pattern", NON_BLANK_CLASS)
        properties["metadataAuthor"]["minItems"] = 1
        properties["metadataAuthor"]["items"] = {"$ref": "#/$defs/MetadataAuthor"}
        # assemblyAuthor stays optional; when present every item is named.
        properties["assemblyAuthor"]["items"] = {"$ref": "#/$defs/AssemblyAuthor"}
    defs = generated["$defs"]
    for name in ("MetadataAuthor", "AssemblyAuthor"):
        author = defs[name]
        author["required"] = sorted(set(author.get("required", [])) | {"name"})
        author["properties"]["name"].update(NON_BLANK)
    # Taxon is deliberately left as the pinned core defines it: the maintainers
    # chose to keep the current taxon rules (name and uri both optional) for
    # this draft (FHT-Specification#8, 2026-11-16).
    return generated

def apply_sample_rules(generated):
    """Require each Sample entry to carry at least one supplied value."""
    sample = generated.get("$defs", {}).get("Sample")
    if sample is None:
        raise ValueError("generated schema has no Sample definition")
    sample["anyOf"] = [
        {"required": [name]}
        for name in (
            "tissue",
            "tissueIdentifier",
            "developmentalStage",
            "condition",
            "strain",
        )
    ]
    return generated


# Extension fields (FAIR-bioHeaders-Specification docs/FORMAT.md R15, issue
# FAIR-bioHeaders-Specification#197): a top-level key matching this pattern may
# hold any value the standard does not define. LinkML cannot express
# patternProperties or propertyNames, so they are added after generation. Nested
# objects stay closed. FHT has no released minor before the draft 1.0, so there
# is no older-minor conditional as in FHR 2.1 and FHP/FHGFF3 1.1.
EXTENSION_PATTERN = "^x-[A-Za-z0-9][A-Za-z0-9_.-]*$"
EXTENSION_FIELD = {
    "description": (
        "Extension field (FAIR-bioHeaders-Specification docs/FORMAT.md R15): any "
        "value; it means nothing to the standard"
    )
}
# Python's "$" also matches before a final line feed, ECMA-262's does not; no key
# may contain one, so both dialects accept the same keys.
NO_LINE_FEED = {"not": {"pattern": "\n"}}


def apply_extension_rules(generated):
    """Allow top-level extension fields on the FHT root (and its $defs copy)."""
    roots = [generated]
    if isinstance(generated.get("$defs", {}).get("FHT"), dict):
        roots.append(generated["$defs"]["FHT"])
    for node in roots:
        node["patternProperties"] = {EXTENSION_PATTERN: dict(EXTENSION_FIELD)}
        node["propertyNames"] = dict(NO_LINE_FEED)
    return generated


def apply_fht_parent_rules(generated):
    """Restrict derivedFrom to reviewed FHT/FHR parent relationships."""
    parent = generated.get("$defs", {}).get("DerivedFrom")
    if parent is None:
        raise ValueError("generated schema has no DerivedFrom definition")
    # Approved draft-local D2 constraints; pinned shared imports stay intact.
    parent["properties"]["checksum"]["pattern"] = (
        "^[A-Za-z0-9+/]{42}[AEIMQUYcgkosw048]=(?![\\s\\S])"
    )
    roots = [generated, generated["$defs"]["FHT"]]
    for node in roots:
        node["properties"]["derivedFrom"]["uniqueItems"] = True
    parent["allOf"] = [
        {
            "description": (
                "Permitted FHT parent relationship: another FHT file filtered "
                "into this set, or an FHR genome whose bases were extracted "
                "(annotation-derived, or genome-guided models written out from the genome). Genome guidance alone is not a "
                "transcribedFrom link. The shared object already requires the "
                "parent checksum; accessionID is additional, not a substitute."
            ),
            "anyOf": ALLOWED_PARENTS,
        }
    ]
    return generated


def generate():
    view = SchemaView(str(ROOT / "fht_linkml.yml"))
    generated = json.loads(
        JsonSchemaGenerator(
            view.schema,
            include_null=False,
            not_closed=False,
        ).serialize()
    )
    generated = apply_common_rules(generated)
    generated["$id"] = SCHEMA_ID
    generated["title"] = "FHT"
    for key in ("metamodel_version", "version"):
        generated.pop(key, None)
    generated = apply_required_value_rules(generated)
    generated = apply_sample_rules(generated)
    generated = apply_fht_parent_rules(generated)
    return apply_extension_rules(generated)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "fht.json",
        help="output file (default: fht.json in the repository root)",
    )
    args = parser.parse_args()
    schema = generate()
    args.output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
