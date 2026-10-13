"""Check every validation constraint after resolving internal schema references."""

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS = {"description", "title", "$id", "$schema", "metamodel_version", "version"}


def constraints(node, document):
    if isinstance(node, bool):
        return node
    node = dict(node)
    if "$ref" in node:
        pointer = node.pop("$ref")
        if not pointer.startswith("#/"):
            raise ValueError(f"External reference not supported: {pointer}")
        target = document
        for part in pointer[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        collision = set(node) & set(target) - ANNOTATIONS
        if collision:
            raise ValueError(f"Overlapping reference constraints: {collision}")
        node = {**target, **node}
    result = {}
    for key, value in node.items():
        if key in ANNOTATIONS or key in {"$defs", "definitions"}:
            continue
        if key in {"properties", "patternProperties", "dependentSchemas"}:
            result[key] = {
                name: constraints(child, document) for name, child in value.items()
            }
        elif key in {
            "items",
            "additionalProperties",
            "contains",
            "not",
            "if",
            "then",
            "else",
            "propertyNames",
        }:
            result[key] = constraints(value, document)
        elif key in {"anyOf", "allOf", "oneOf", "prefixItems"}:
            children = [constraints(child, document) for child in value]
            result[key] = (
                sorted(children, key=lambda child: json.dumps(child, sort_keys=True))
                if key != "prefixItems"
                else children
            )
        elif key in {"required", "enum"}:
            result[key] = sorted(
                value, key=lambda child: json.dumps(child, sort_keys=True)
            )
        else:
            result[key] = value
    return result


# (header type, published schema, generator function name). fhr.json is
# hand-written and must stay validation-equivalent; fhp.json and fhgff3.json are
# generated and must equal the generator's constraints (specs/006-protein-header
# D-01, specs/007-gff3-header D-01).
TYPES = (("FHR", "fhr.json", "generate"), ("FHP", "fhp.json", "generate_fhp"),
         ("FHGFF3", "fhgff3.json", "generate_fhgff3"))


def main():
    module_spec = importlib.util.spec_from_file_location(
        "generator", ROOT / "json-schema-generator.py"
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    failed = False
    for name, path, function in TYPES:
        generated = getattr(module, function)()
        published = json.loads((ROOT / path).read_text())
        left = constraints(published, published)
        right = constraints(generated, generated)
        if left != right:
            from check_schema_drift import differences

            print(f"{name}: LinkML validation constraints differ from {path}:",
                  file=sys.stderr)
            for change in differences(left, right):
                print(change, file=sys.stderr)
            failed = True
        else:
            print(f"{name}: LinkML generation matches all published validation "
                  f"constraints in {path}.")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
