# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Generate/check standalone examples of the test-only FHT draft binding (#11)."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from fht_microdata import write_page  # noqa: E402

START = "<!-- BEGIN generated root bindings -->"
END = "<!-- END generated root bindings -->"


def root_bindings(schema):
    """Document types from actual schema refs; enum refs are scalar, not objects."""

    def resolve(part):
        while "$ref" in part:
            value = schema
            for token in part["$ref"][2:].split("/"):
                value = value[token.replace("~1", "/").replace("~0", "~")]
            part = value
        return part

    rows = [
        "| Field | Contract shape | Required | Binding |",
        "| --- | --- | --- | --- |",
    ]
    for name, raw in schema["properties"].items():
        part = resolve(raw)
        kind = part["type"]
        if kind == "array":
            item = resolve(part["items"])
            shape = "array of " + item.get("title", item["type"])
            binding = "ordered typed container"
        elif kind == "object":
            shape, binding = (
                part.get("title", "object") + " object",
                "typed object scope",
            )
        else:
            shape = "enum string" if "enum" in part else kind
            binding = "typed scalar"
        required = "yes" if name in schema["required"] else "no"
        rows.append(f"| `{name}` | {shape} | {required} | {binding} |")
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = ROOT / "examples" / "html"
    problems = []
    doc = ROOT / "docs" / "FHT-MICRODATA.md"
    original = doc.read_text(encoding="utf-8")
    before, remainder = original.split(START, 1)
    _, after = remainder.split(END, 1)
    schema = json.loads((ROOT / "fht.json").read_text(encoding="utf-8"))
    regenerated = before + START + "\n" + root_bindings(schema) + "\n" + END + after
    if args.check:
        if original != regenerated:
            problems.append(str(doc.relative_to(ROOT)) + " root field table")
    else:
        doc.write_text(regenerated, encoding="utf-8")
    for source in sorted((ROOT / "examples").glob("*.fht.json")):
        record = json.loads(source.read_text(encoding="utf-8"))
        text = write_page(
            record, allow_draft=True, title=source.stem + " (unreleased draft)"
        )
        target = output / (source.stem + ".html")
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != text:
                problems.append(str(target.relative_to(ROOT)))
        else:
            output.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
    if problems:
        print("Draft HTML fixture drift: " + ", ".join(problems), file=sys.stderr)
        return 1
    print(
        "FHT draft HTML examples "
        + ("match their canonical inputs." if args.check else "generated.")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
