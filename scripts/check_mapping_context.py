# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Validate the proposed descriptive export context, not a deposit or FHR schema.

Draft issue #56 helper. No transformation, network lookup or identifier minting.
"""
import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "mappings/proposals/assembly-export-context.schema.json"
SOURCE_ALIASES = {
    "https://w3id.org/fair-bioheaders/fhr/v0.4.0",
    "https://w3id.org/fair-bioheaders/fhr/v0.4.0/",
    "https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/v0.4.0/fhr.json",
    "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/v0.4.0/fhr.json",
}


def context_errors(context, source):
    """Return structural/context-conflict errors without rewriting either input."""
    if not isinstance(source, dict):
        return ["source must be a JSON metadata object"]
    source_schema = source.get("schema")
    if not isinstance(source_schema, str) or source_schema not in SOURCE_ALIASES or source.get("schemaVersion") != "2.0":
        return ["this draft context only supports the fixed FHR v0.4.0 / schemaVersion 2.0 source identity"]
    validator = Draft202012Validator(json.loads(SCHEMA.read_text()), format_checker=FormatChecker())
    errors = [f"{error.json_path}: {error.message}" for error in validator.iter_errors(context)]
    if errors:
        return sorted(errors)
    if context["resourceIRI"] == context["metadataRecordIRI"]:
        errors.append("resourceIRI and metadataRecordIRI must identify distinct resources")
    if "publicationDate" in context and "publicationYear" in context:
        if int(context["publicationDate"][:4]) != context["publicationYear"]:
            errors.append("publicationDate and publicationYear conflict; neither takes precedence")
    doi = context.get("resourceDOI")
    article = source.get("scholarlyArticle")
    if doi and isinstance(article, str) and doi.casefold() == article.casefold():
        errors.append("resourceDOI identifies the assembly; scholarlyArticle identifies a distinct article")
    return errors


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON property: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"non-JSON numeric constant: {value}")

    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=reject_constant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", type=Path)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    try:
        errors = context_errors(load_json(args.context), load_json(args.source))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    for error in errors:
        print(error)
    if not errors:
        print("Draft descriptive context checked; no export, deposit validation or registration performed.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
