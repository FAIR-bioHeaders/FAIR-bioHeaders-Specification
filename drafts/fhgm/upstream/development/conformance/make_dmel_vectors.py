# SPDX-License-Identifier: MPL-2.0
"""Generate the promoted real-data FHGM vectors deterministically.

Companion generator to ``make_vectors.py`` for the cases promoted (as a draft,
under independent-review conditions) from the real *Drosophila melanogaster*
chromosome-4 example lane ``development/examples/dmel4/``. Each emitted file is
one committed fixture's header with exactly one documented producer-error
mutation, re-rendered canonical-line by the shared ``check_revision.render``
helper with a freshly computed exact-byte checksum; the feature rows are the
fixture's own bytes, copied verbatim from the pinned RefSeq archive
(see examples/dmel4/SOURCE.md and provenance.json). Nothing here invents
identifiers, coordinates, accessions or digests:

- accessions, SeqCol digests, gene IDs and the revision pointer come from the
  committed dmel4 fixtures;
- the wrong-parent digest in dmel-reference-contradicts-file is the real
  exact-byte checksum of the committed S6k example fixture, read from that
  file's own checksum line at generation time - a genuine FHGFF3 file digest
  that is simply not this file's parent.

Two rules from ``make_vectors.py`` carry over unchanged. A vector's expected
outcome must be OBSERVED by running ``development/model/validate_fhgm.py`` on
the emitted bytes before it is recorded (``run_conformance.py --seal`` records
digests from bytes that already matched a recorded outcome; nothing here states
an expectation). And no emitted vector gives semantics to split, merge,
assembly migration, transcript-only contribution or companion-file identity
(#204 Q6, curator scope): the transcript-target case is a statement about
v0.1's gene-row scope only, exactly like its synthetic sibling.

Usage: ``python3 make_dmel_vectors.py <existing-directory>`` writes the
promoted invalid vectors into that directory, named by their manifest ids.
The valid anchors (the two committed snapshots) are cited in place and are not
emitted here.
"""

import argparse
from copy import deepcopy
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
DEVELOPMENT = HERE.parent
sys.path.insert(0, str(DEVELOPMENT / "examples" / "revision"))
from check_revision import MODELS, parse_header, render  # noqa: E402

DMEL4 = DEVELOPMENT / "examples" / "dmel4"
V1 = DMEL4 / "Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3"
V2 = DMEL4 / "Dmel_CG11076-Mpv17.snapshot-v2.fhgff3.gff3"
S6K = DEVELOPMENT / "examples" / "s6k" / "DanaCAF1_S6k.fhgm-models.fhgff3.gff3"

CG = "gene-Dmel_CG11076"   # the multi-isoform locus; revised by V2
MP = "gene-Dmel_CG11077"   # the single-exon neighbour (Mpv17), unchanged


def load(path):
    """(metadata without checksum, feature payload bytes) of a committed fixture."""
    data = path.read_bytes()
    metadata = parse_header(data.splitlines(keepends=True))
    del metadata["checksum"]
    payload = b"".join(
        line for line in data.splitlines(keepends=True) if not line.startswith(b"#")
    )
    return metadata, payload


def record(metadata, model_id):
    for item in metadata[MODELS]:
        if item["modelId"] == model_id:
            return item
    raise KeyError(model_id)


def s6k_checksum():
    """The committed S6k fixture's own file-bound checksum line, read from its bytes."""
    for line in S6K.read_bytes().splitlines():
        if line.startswith(b"#~checksum: "):
            return line[len(b"#~checksum: "):].decode()
    raise AssertionError("S6k fixture carries no checksum line")


# --- the promoted producer errors, one mutation per case -----------------------
# Mirrors development/examples/dmel4/exercise_rules.py exactly; the exercise is
# the demonstration, these are the digest-pinned normative cases.

def make():
    v1, v1_payload = load(V1)
    v2, v2_payload = load(V2)
    out = {}

    def render_case(name, metadata, payload):
        return name, render(metadata, payload)

    m = deepcopy(v1)
    record(m, CG)["modelVersion"] = 2  # YAML int, not the string "2"
    out["dmel-numeric-model-version"] = m, v1_payload

    m = deepcopy(v1)
    m[MODELS].append(deepcopy(record(m, MP)))
    out["dmel-duplicate-model-id"] = m, v1_payload

    m = deepcopy(v1)
    record(m, MP)["featureId"] = "rna-NM_143687.4"  # a real mRNA row of the file
    out["dmel-target-transcript-row"] = m, v1_payload

    m = deepcopy(v1)
    record(m, CG)["featureId"] = "gene-Dmel_absentFromThisFile"
    out["dmel-target-absent"] = m, v1_payload

    m = deepcopy(v1)
    record(m, MP)["reference"] = {"annotates": s6k_checksum()}
    out["dmel-reference-contradicts-file"] = m, v1_payload

    m = deepcopy(v1)
    del m["genomeReference"]  # file keeps only the FHR derivedFrom link;
    # the CG record keeps only its genomeReference: no shared comparable form
    out["dmel-reference-not-comparable"] = m, v1_payload

    m = deepcopy(v2)
    record(m, CG)["predecessor"]["modelId"] = MP  # deviation D2 on real records
    out["dmel-pointer-names-neighbor"] = m, v2_payload

    m = deepcopy(v2)
    record(m, CG)["modelVersion"] = "1"  # successor version equals the recorded one
    out["dmel-pointer-reuses-version"] = m, v2_payload

    m = deepcopy(v1)
    m[MODELS] = []
    out["dmel-empty-model-array"] = m, v1_payload

    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="existing directory for emitted vectors")
    args = parser.parse_args()
    for name, (metadata, payload) in make().items():
        path = args.output / f"{name}.fhgff3.gff3"
        path.write_bytes(render(metadata, payload))
    print(f"emitted {len(make())} promoted real-data vectors")


if __name__ == "__main__":
    main()
