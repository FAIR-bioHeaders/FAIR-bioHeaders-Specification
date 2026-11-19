# SPDX-License-Identifier: MPL-2.0
"""Derive an FHGM record fixture from the vetted S6k profile fixture.

Reads DanaCAF1_S6k.fhgff3.gff3 (merged in PR #3, attributed to the CaltechDATA
deposit), replaces the experimental x-fhgm-contribution-scope key with one
x-fhgm-models record under the draft contract v0.1, and recomputes the
exact-byte checksum. The GFF3 feature payload bytes are untouched; the header
is re-rendered in the revision pilot's canonical one-value-per-line form.
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "revision"))
from check_revision import parse_header, render  # noqa: E402 (sibling pilot)

RECORDS = "x-fhgm-models"
FEATURE_ID = "DanaCAF1_S6k"
# Attribution recorded in README.md: the deposited model is by Laura K. Reed.
CONTRIBUTORS = [{"name": "Laura K. Reed", "role": "model author (deposit attribution)"}]
# The pilot's recorded reference-verification result (README.md table).
EVIDENCE = [{
    "description": (
        "Transcripts PA and PB match the deposited 1,467-nt transcript and "
        "489-aa peptide against GCA_000005115.1 (CH902618.1); the separately "
        "annotated stop intervals read TAA, as recorded by the S6k pilot."
    )
}]
SOFTWARE = "development/examples/s6k/convert.py"


def derive(data, source=SOFTWARE):
    lines = data.splitlines(keepends=True)
    header = parse_header([line for line in lines if line.startswith(b"#~")])
    payload = b"".join(
        line for line in lines
        if not line.startswith(b"#~") and not line.startswith(b"##gff-version")
    )
    metadata = {key: value for key, value in header.items()
                if key not in ("checksum", "x-fhgm-contribution-scope")}
    record = {
        # The file-local model ID reuses the gene feature ID of the converted
        # deposit. File-local identity is the reviewed default (#204 Q2, 2026-11-14);
        # who may mint an external model ID stays a curator question.
        "modelId": FEATURE_ID,
        "modelVersion": header["version"],
        "featureId": FEATURE_ID,
        "reference": {"genomeReference": dict(header["genomeReference"])},
        "contributors": CONTRIBUTORS,
        "evidence": EVIDENCE,
        "methods": {"software": [{"name": source}]},
        "publication": {
            "article": header["scholarlyArticle"],
            "deposit": list(header["identifier"]),
        },
        "reuseConditions": header["reuseConditions"],
    }
    metadata[RECORDS] = [record]
    return render(metadata, payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="DanaCAF1_S6k.fhgff3.gff3 path")
    parser.add_argument("output", type=Path, help="derived fixture path")
    args = parser.parse_args()
    data = derive(args.fixture.read_bytes())
    args.output.write_bytes(data)
    print(f"Wrote {args.output.name}")


if __name__ == "__main__":
    main()
