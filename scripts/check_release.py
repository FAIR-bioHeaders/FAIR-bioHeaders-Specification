"""Check schema and JSON-LD context copies and example identity across local companion checkouts."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--converter", type=Path, required=True)
    args = parser.parse_args()
    schema = json.loads((ROOT / "fhr.json").read_text())
    for relative in ("fhr_schema.json", "fhr/fhr_schema.json"):
        path = args.converter / relative
        if json.loads(path.read_text()) != schema:
            print(f"Schema copy differs: {path}", file=sys.stderr)
            return 1
    context = args.converter / "bioheaders" / "fhr.context.jsonld"
    if not context.is_file() or context.read_bytes() != (
        ROOT / "jsonld" / "fhr.context.jsonld"
    ).read_bytes():
        print(f"JSON-LD context copy differs or is missing: {context}", file=sys.stderr)
        return 1
    for example in (ROOT / "examples").iterdir():
        if (
            example.is_file()
            and example.read_bytes()
            != (args.converter / "examples" / example.name).read_bytes()
        ):
            print(f"Companion example differs: {example.name}", file=sys.stderr)
            return 1
    # FHP (specs/006-protein-header): toolkits from the release that adds FHP
    # bundle fhp_schema.json and copy examples/fhp/; older ones have neither.
    fhp = args.converter / "bioheaders" / "fhp_schema.json"
    if fhp.is_file():
        if fhp.read_bytes() != (ROOT / "fhp.json").read_bytes():
            print(f"FHP schema copy differs: {fhp}", file=sys.stderr)
            return 1
        for example in (ROOT / "examples" / "fhp").iterdir():
            copy = args.converter / "examples" / "fhp" / example.name
            if not copy.is_file() or copy.read_bytes() != example.read_bytes():
                print(f"Companion FHP example differs or is missing: {example.name}",
                      file=sys.stderr)
                return 1
        note = ", the FHP schema and FHP examples"
    else:
        note = " (this converter has no FHP schema)"
    # FHGFF3 (specs/007-gff3-header): the same for fhgff3_schema.json and examples/fhgff3/.
    fhgff3 = args.converter / "bioheaders" / "fhgff3_schema.json"
    if fhgff3.is_file():
        if fhgff3.read_bytes() != (ROOT / "fhgff3.json").read_bytes():
            print(f"FHGFF3 schema copy differs: {fhgff3}", file=sys.stderr)
            return 1
        for example in (ROOT / "examples" / "fhgff3").iterdir():
            copy = args.converter / "examples" / "fhgff3" / example.name
            if not copy.is_file() or copy.read_bytes() != example.read_bytes():
                print(f"Companion FHGFF3 example differs or is missing: {example.name}",
                      file=sys.stderr)
                return 1
        note += ", the FHGFF3 schema and FHGFF3 examples"
    else:
        note += " (this converter has no FHGFF3 schema)"
    # Schema selection (specs/012): the converter's bundled release copies must
    # equal the releases' schemas, and its current copies belong to our current release.
    bundled_path = args.converter / "bioheaders" / "schemas" / "bundled.json"
    if bundled_path.is_file():
        registry = json.loads((ROOT / "schemas" / "versions.json").read_text())
        bundled = json.loads(bundled_path.read_text())
        if bundled["current"]["release"] != registry["current"]:
            print(f"Converter's current schemas are for {bundled['current']['release']}, "
                  f"not {registry['current']}", file=sys.stderr)
            return 1
        for tag, types in bundled["releases"].items():
            if set(types) != set(registry["releases"].get(tag, {})):
                print(f"Converter's {tag} header types differ from schemas/versions.json",
                      file=sys.stderr)
                return 1
            for kind, name in types.items():
                if tag == registry["current"]:
                    theirs = json.loads((ROOT / registry["files"][kind]).read_text())
                else:
                    shown = subprocess.run(["git", "show", f"{tag}:{registry['files'][kind]}"],
                                           cwd=ROOT, capture_output=True, text=True)
                    if shown.returncode:
                        print(f"Cannot read {registry['files'][kind]} at {tag}; fetch the tags",
                              file=sys.stderr)
                        return 1
                    theirs = json.loads(shown.stdout)
                copy = json.loads((args.converter / "bioheaders" / name).read_text())
                if copy != theirs:
                    print(f"Converter's bundled {tag} {kind} schema differs: {name}",
                          file=sys.stderr)
                    return 1
        note += ", and the bundled release schemas"
    print("Both converter schema copies, the JSON-LD context and all example files match "
          f"the specification{note}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
