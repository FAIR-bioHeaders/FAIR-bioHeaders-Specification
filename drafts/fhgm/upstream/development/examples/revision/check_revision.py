"""Generate and check synthetic FHGFF3 revision cases against a supplied schema."""

import argparse
import base64
import hashlib
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA = "https://w3id.org/fair-bioheaders/fhgff3/v0.5.0"
DIRECTIVE = b"##gff-version 3\n"
MODELS = "x-fhgm-models"


def sha512t24u(data):
    return base64.urlsafe_b64encode(hashlib.sha512(data).digest()[:24]).decode()


def canonical(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def synthetic_reference():
    # One synthetic FASTA record, >toy followed by 100 uppercase A bases.
    attributes = {"names": ["toy"], "sequences": ["SQ." + sha512t24u(b"A" * 100)]}
    level_one = {key: sha512t24u(canonical(value)) for key, value in attributes.items()}
    return {"accession": "SYNTHETIC_ASSEMBLY.1", "seqcol_id": sha512t24u(canonical(level_one))}


def checksum(content):
    return base64.b64encode(hashlib.new("sha512_256", content).digest()).decode()


def feature_payload(first_end):
    rows = []
    for gene, start, end in (("toy-a", 10, first_end), ("toy-b", 60, 80)):
        prefix = "toy\tpilot\t"
        bounds = f"{start}\t{end}\t.\t+\t.\t"
        rows.extend((
            f"{prefix}gene\t{bounds}ID={gene}",
            f"{prefix}lncRNA\t{bounds}ID={gene}-rna;Parent={gene}",
            f"{prefix}exon\t{bounds}Parent={gene}-rna",
        ))
    return ("\n".join(rows) + "\n").encode()


def render(metadata, payload):
    header = b"".join(
        f"#~{key}: ".encode() + canonical(value) + b"\n"
        for key, value in metadata.items()
    )
    value = checksum(DIRECTIVE + header + payload)
    return DIRECTIVE + header + f"#~checksum: {value}\n".encode() + payload


def parse_header(lines):
    return yaml.safe_load(b"".join(line[2:] for line in lines if line.startswith(b"#~")))


def validate_file(data, validator):
    lines = data.splitlines(keepends=True)
    header = parse_header(lines)
    validator.validate(header)
    covered = b"".join(line for line in lines if not line.startswith(b"#~checksum:"))
    if checksum(covered) != header["checksum"]:
        raise ValueError("File checksum mismatch")
    return header


def predecessor_matches(successor, model, predecessor):
    """Resolve an in-lineage revision to one model in the supplied annotation."""
    target = model["predecessor"]
    if (
        target["annotationChecksum"] != predecessor["checksum"]
        or successor["genomeReference"] != predecessor["genomeReference"]
        or target["modelId"] != model["modelId"]
    ):
        return False
    candidates = [
        candidate for candidate in predecessor[MODELS]
        if candidate["modelId"] == target["modelId"]
    ]
    return len(candidates) == 1 and candidates[0]["modelVersion"] == target["modelVersion"]


def run(schema_path, output):
    validator = Draft202012Validator(
        json.loads(schema_path.read_bytes()), format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    common = {
        "schema": SCHEMA,
        "schemaVersion": "1.1",
        "annotation": "Synthetic annotation with two noncoding loci",
        "taxon": {"name": "Synthetic example"},
        "metadataAuthor": [{"name": "OpenAI Codex"}],
        "dateCreated": "2026-11-10",
        "genomeReference": synthetic_reference(),
    }
    first = {"modelId": "model-a", "modelVersion": "1", "featureId": "toy-a",
             "reference": {"genomeReference": synthetic_reference()}}
    neighbor = {"modelId": "model-b", "modelVersion": "1", "featureId": "toy-b",
                "reference": {"genomeReference": synthetic_reference()}}
    original_bytes = render(dict(common, version="1", **{MODELS: [first, neighbor]}), feature_payload(30))
    original = validate_file(original_bytes, validator)
    target = {
        "annotationChecksum": original["checksum"],
        "modelId": first["modelId"],
        "modelVersion": first["modelVersion"],
    }
    variants = (
        ("revised.gff3", target, True),
        ("wrong-model.gff3", dict(target, modelId=neighbor["modelId"]), False),
        ("stale-predecessor.gff3", dict(target, annotationChecksum=checksum(b"unrelated bytes")), False),
    )
    for name, pointer, expected in variants:
        model = dict(first, modelVersion="2", predecessor=pointer)
        metadata = dict(common, version="2", **{MODELS: [model, neighbor]})
        data = render(metadata, feature_payload(35))
        header = validate_file(data, validator)
        revised_model, unchanged_model = header[MODELS]
        if unchanged_model != original[MODELS][1]:
            raise ValueError(f"{name}: unchanged model identity or metadata changed")
        if predecessor_matches(header, revised_model, original) != expected:
            raise ValueError(f"{name}: unexpected predecessor resolution")
        (output / name).write_bytes(data)
        print(f"{name}: schema and checksum pass; predecessor resolves: {expected}")

    unsupported = dict(
        common,
        version="2",
        derivedFrom=[
            {"headerType": "FHGFF3", "relationship": "supersedes", "checksum": original["checksum"]}
        ],
    )
    unsupported_header = parse_header(render(unsupported, feature_payload(35)).splitlines(keepends=True))
    errors = list(validator.iter_errors(unsupported_header))
    if len(errors) != 1 or list(errors[0].absolute_path) != ["derivedFrom", 0, "relationship"]:
        raise ValueError("Expected the base schema to reject the supersedes term")

    (output / "original.gff3").write_bytes(original_bytes)
    print("Original passes schema and checksum; model B is unchanged in both snapshots.")
    print("Base schema rejects derivedFrom.relationship=supersedes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema", type=Path)
    parser.add_argument("output", type=Path, help="Existing directory for generated fixtures")
    args = parser.parse_args()
    run(args.schema, args.output)
