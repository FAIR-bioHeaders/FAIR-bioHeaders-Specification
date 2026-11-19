# SPDX-License-Identifier: MPL-2.0
"""Generate the draft FHGM contract v0.1 fixture set deterministically.

All fixtures are synthetic. They reuse the revision pilot's render helpers and
synthetic assembly, and cite no external payload. Every file is a released
FHGFF3 1.1 header carrying x-fhgm-models under the draft transport overlay.
See README.md for the expected checker verdict per fixture.
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "revision"))
from check_revision import (
    MODELS,
    checksum,
    feature_payload,
    render,
    synthetic_reference,
)

DATE = "2026-11-12"
ACCESSION = synthetic_reference()["accession"]


def metadata(models, file_version):
    return {
        "schema": "https://w3id.org/fair-bioheaders/fhgff3/v0.5.0",
        "schemaVersion": "1.1",
        "annotation": "Synthetic annotation for the draft FHGM contract fixtures",
        "taxon": {"name": "Synthetic example"},
        "metadataAuthor": [{"name": "OpenAI Codex"}],
        "dateCreated": DATE,
        "genomeReference": synthetic_reference(),
        "version": file_version,
        MODELS: models,
    }


def record(model_id, model_version, feature="toy-a", **extra):
    model = {
        "modelId": model_id,
        "modelVersion": model_version,
        "featureId": feature,
        "reference": {"genomeReference": synthetic_reference()},
    }
    model.update(extra)
    return model


def pointer(annotation_checksum, model_id, model_version):
    return {
        "annotationChecksum": annotation_checksum,
        "modelId": model_id,
        "modelVersion": model_version,
    }


def header_checksum(data):
    for line in data.splitlines():
        if line.startswith(b"#~checksum: "):
            return line[len(b"#~checksum: "):].decode()
    raise AssertionError("fixture has no checksum line")


def run(output):
    first = record("model-a", "1")
    second = record("model-b", "1", feature="toy-b")
    snapshot_v1 = render(metadata([first, second], "1"), feature_payload(30))
    v1_checksum = header_checksum(snapshot_v1)

    revised = record("model-a", "2", predecessor=pointer(v1_checksum, "model-a", "1"))
    snapshot_v2 = render(metadata([revised, second], "2"), feature_payload(35))

    fixtures = {
        "valid-single.fhgff3.gff3": render(metadata([first], "1"), feature_payload(30)),
        "snapshot-v1.fhgff3.gff3": snapshot_v1,
        "snapshot-v2.fhgff3.gff3": snapshot_v2,
        "pointer-absent-snapshot.fhgff3.gff3": render(
            metadata(
                [record("model-a", "2", predecessor=pointer(checksum(b"unrelated bytes"), "model-a", "1")), second],
                "2",
            ),
            feature_payload(35),
        ),
        "ambiguous-model-id.fhgff3.gff3": render(
            metadata([first, dict(first)], "1"), feature_payload(30)
        ),
        "version-reuse.fhgff3.gff3": render(
            metadata([record("model-a", "1", predecessor=pointer(v1_checksum, "model-a", "1")), second], "2"),
            feature_payload(35),
        ),
        "pointer-version-mismatch.fhgff3.gff3": render(
            metadata([record("model-a", "2", predecessor=pointer(v1_checksum, "model-a", "9")), second], "2"),
            feature_payload(35),
        ),
        "predecessor-name-mismatch.fhgff3.gff3": render(
            metadata([record("model-a", "2", predecessor=pointer(v1_checksum, "model-b", "1")), second], "2"),
            feature_payload(35),
        ),
        "version-gap-skip.fhgff3.gff3": render(
            metadata([record("model-a", "3", predecessor=pointer(v1_checksum, "model-a", "1")), second], "3"),
            feature_payload(35),
        ),
        "record-without-reference.fhgff3.gff3": render(
            metadata([{key: value for key, value in first.items() if key != "reference"}], "1"),
            feature_payload(30),
        ),
        "record-reference-conflict.fhgff3.gff3": render(
            metadata(
                [record("model-a", "1", reference={"genomeReference": {
                    "accession": "SYNTHETIC_OTHER.1",
                    "seqcol_id": synthetic_reference()["seqcol_id"],
                }})],
                "1",
            ),
            feature_payload(30),
        ),
    }
    for name, data in sorted(fixtures.items()):
        (output / name).write_bytes(data)
        print(name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Existing directory for the fixtures")
    args = parser.parse_args()
    run(args.output)
