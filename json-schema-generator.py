"""Generate the FHR, FHP and FHGFF3 JSON Schemas from their LinkML models.

FHR's output must stay validation-equivalent to the hand-written fhr.json;
FHP's and FHGFF3's outputs are the published fhp.json and fhgff3.json
(specs/006-protein-header D-01, specs/007-gff3-header D-01).
"""

import argparse
import json
from pathlib import Path

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime import SchemaView

ROOT = Path(__file__).resolve().parent
# Core string slots whose exact length LinkML cannot express.
EXACT_LENGTHS = {"checksum": 44, "seqcol_id": 32}


def generate_from(schema_path, legacy_open=True):
    """Generate JSON Schema for any LinkML schema that imports schemas/core.yaml.

    ``legacy_open`` keeps the core objects that FHR schemaVersion 1 leaves open
    open; new header types close them.
    """
    view = SchemaView(str(schema_path))
    generated = json.loads(
        JsonSchemaGenerator(
            view.schema,
            include_null=False,
            not_closed=False,
        ).serialize()
    )
    # Legacy FHR nested objects in the core are open; newer objects stay closed.
    if legacy_open:
        for name in ("Taxon", "Author", "AccessionID"):
            generated["$defs"].get(name, {}).pop("additionalProperties", None)
    # A trailing newline satisfies "$" in Python regexes; pin the exact length.
    for node in (generated, *generated["$defs"].values()):
        for name, length in EXACT_LENGTHS.items():
            if name in node.get("properties", {}):
                node["properties"][name].update(minLength=length, maxLength=length)
    generated["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return generated


def generate():
    generated = generate_from(ROOT / "fhr_linkml.yml")
    generated["$defs"]["VitalStats"].pop("additionalProperties", None)
    # LinkML emits a scalar type beside a heterogeneous union. Retain the union.
    for node in (generated, generated["$defs"]["FHR"]):
        node["properties"]["assemblySoftware"].pop("type", None)
    return generated


def _generate_type(linkml, name, published):
    """A new header type's published schema (specs/006 contracts/fhp-schema.md 1-4)."""
    generated = generate_from(ROOT / linkml, legacy_open=False)
    # Identify the schema like fhr.json: its canonical raw-main URL and type name.
    generated["$id"] = (
        "https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/main/"
        + published
    )
    generated["title"] = name
    # Generator annotations vary with the installed LinkML runtime, not with the
    # model; leave them out so the schema is reproducible.
    for key in ("metamodel_version", "version"):
        generated.pop(key, None)
    # Each header type versions its schema; enum lets later versions be listed.
    for node in (generated, generated["$defs"][name]):
        version = node["properties"]["schemaVersion"]
        version["enum"] = [version.pop("const")]
    return generated


def generate_fhp():
    """The published FHP schema (specs/006-protein-header contracts/fhp-schema.md)."""
    return _generate_type("fhp_linkml.yml", "FHP", "fhp.json")


def generate_fhgff3():
    """The published FHGFF3 schema (specs/007-gff3-header contracts/fhgff3-schema.md).

    LinkML cannot say "derivedFrom contains an item with these values", so the
    genome-link rule (research D-03) is added here: a genomeReference or an
    annotates link to an FHR genome is required, at most one derivedFrom item
    annotates, and an annotates item must name an FHR parent.
    """
    generated = _generate_type("fhgff3_linkml.yml", "FHGFF3", "fhgff3.json")
    generated["$defs"]["AnnotatesGenome"] = {
        "description": "A derivedFrom item that links the annotated FHR genome by checksum",
        "type": "object",
        "required": ["headerType", "relationship"],
        "properties": {"headerType": {"const": "FHR"}, "relationship": {"const": "annotates"}},
    }
    generated["$defs"]["AnnotatesAny"] = {
        "description": "A derivedFrom item with the relationship annotates",
        "type": "object",
        "required": ["relationship"],
        "properties": {"relationship": {"const": "annotates"}},
    }
    rule = {
        "anyOf": [
            {"required": ["genomeReference"]},
            {
                "required": ["derivedFrom"],
                "properties": {
                    "derivedFrom": {"contains": {"$ref": "#/$defs/AnnotatesGenome"}}
                },
            },
        ],
        "allOf": [
            {
                "not": {
                    "required": ["derivedFrom"],
                    "properties": {
                        "derivedFrom": {
                            "contains": {"$ref": "#/$defs/AnnotatesAny"},
                            "minContains": 2,
                        }
                    },
                }
            },
            {
                "properties": {
                    "derivedFrom": {
                        "items": {
                            "if": {"$ref": "#/$defs/AnnotatesAny"},
                            "then": {"properties": {"headerType": {"const": "FHR"}}},
                        }
                    }
                }
            },
        ],
    }
    for node in (generated, generated["$defs"]["FHGFF3"]):
        node.update(rule)
    return generated


GENERATORS = {"fhr": generate, "fhp": generate_fhp, "fhgff3": generate_fhgff3}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--type", choices=sorted(GENERATORS), default="fhr",
                        help="header type to generate (default: fhr)")
    parser.add_argument("--output", type=Path,
                        help="output file (default: TYPE_linkml.json)")
    args = parser.parse_args()
    if args.output is None:
        args.output = ROOT / f"{args.type}_linkml.json"
    schema = GENERATORS[args.type]()
    args.output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
