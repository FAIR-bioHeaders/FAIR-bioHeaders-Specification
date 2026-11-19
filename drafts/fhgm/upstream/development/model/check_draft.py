# SPDX-License-Identifier: MPL-2.0
"""Exercise the draft FHGM contract v0.1 checker against its fixtures.

Runs the acceptance and rejection matrix for the contract examples, the
committed model fixtures (regenerated and compared byte-for-byte) and the
S6k-derived record fixture. Also proves the demonstrated gap: files that the
released base schema and checksum accept while the model-level checker
rejects them. Requires fair-bioheaders and jsonschema. The model-conformance
workflow runs this matrix, and the manifest-driven runner in
``development/conformance/``, on every pull request and push to ``main``.

Since the dual-base decision of 2026-11-15 the checker selects, per loaded
file, the registered release that file's ``schema`` URL cites. The matrix runs
once with every supplied base handed to the checker; the fixtures cite v0.5.0,
so those bytes are required. With both bases supplied the selection itself is
additionally exercised - each carrier must be routed to the release it cites,
a citation no registered release answers to and a citation whose bytes were
not supplied must both be refused, and schemaVersion must be judged by the
cited release's own bytes rather than steer the selection.
"""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples" / "revision"))
from check_revision import feature_payload, parse_header, render, validate_file

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "model" / "validate_fhgm.py"
FIXTURES = ROOT / "examples" / "contract"
MODEL_FIXTURES = ROOT / "examples" / "model"
CONFORMANCE_VECTORS = ROOT / "conformance" / "vectors"
S6K = ROOT / "examples" / "s6k"
FHGFF3_12_SCHEMA = "https://w3id.org/fair-bioheaders/fhgff3/v0.6.0"
REGISTRY = ROOT / "model" / "base-schemas.json"


def registered_ref(path):
    """The registry ref (v0.5.0 or v0.6.0) of one supplied base file, or None."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    for record in json.loads(REGISTRY.read_bytes())["bases"]:
        if record["sha256"] == digest:
            return record["ref"]
    return None


def expect(base, file, error=None, predecessor=None, *extra_bases):
    """Run the checker over one file with one or more base-schema candidates.

    ``base`` may be a single path or a list of paths (each becomes one
    ``--base-schema`` argument); ``predecessor`` a path or list of paths.
    """
    bases = base if isinstance(base, list) else [base, *extra_bases]
    command = [sys.executable, str(VALIDATOR)]
    for one in bases:
        command += ["--base-schema", str(one)]
    if isinstance(predecessor, list):
        for path in predecessor:
            command.extend(["--predecessor", str(path)])
    elif predecessor:
        command.extend(["--predecessor", str(predecessor)])
    command.append(str(file))
    result = subprocess.run(command, capture_output=True, text=True)
    if error is None:
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode == 1 and error in result.stderr, result
    return result


def twin_12(source, output, name):
    """Re-render a fixture under the released FHGFF3 1.2 identity.

    The two identity lines move and the checksum follows; records, pointers and
    feature bytes are the source's, exactly as the conformance matrix lane
    derives its twins.
    """
    metadata = parse_header(source.read_bytes().splitlines(keepends=True))
    del metadata["checksum"]
    metadata["schema"] = FHGFF3_12_SCHEMA
    metadata["schemaVersion"] = "1.2"
    # render() re-emits the ##gff-version directive itself; the payload is the
    # feature lines only (every FHGM fixture is plain, no embedded FASTA).
    payload = b"".join(
        line for line in source.read_bytes().splitlines(keepends=True)
        if not line.startswith(b"#")
    )
    candidate = output / name
    candidate.write_bytes(render(metadata, payload))
    return candidate


def contract_examples(bases, sealed, output):
    minimal = FIXTURES / "minimal.fhgff3.gff3"
    rich = FIXTURES / "rich.fhgff3.gff3"
    base = bases
    expect(base, minimal)
    expect(base, rich, predecessor=minimal)
    expect(base, rich, "predecessor snapshot is the current file or was not supplied")

    pilot = ROOT / "examples" / "revision" / "check_revision.py"
    subprocess.run([sys.executable, str(pilot), str(sealed), str(output)], check=True)
    original = output / "original.gff3"
    expect(base, original)
    expect(base, output / "revised.gff3", predecessor=original)
    expect(base, output / "wrong-model.gff3", "predecessor is unresolvable", original)
    expect(base, output / "stale-predecessor.gff3", "predecessor is unresolvable", original)

    metadata = parse_header(minimal.read_bytes().splitlines(keepends=True))
    del metadata["checksum"]
    models = metadata["x-fhgm-models"]
    payload = feature_payload(30)
    for feature_id, rows, error in (
        ("missing", payload, "must target one local gene"),
        ("toy-a-rna", payload, "must target one local gene"),
        ("toy-a", payload + payload, "must target one local gene"),
        ("toy-a", payload.replace(b"ID=toy-a\n", b"ID=toy%2Da\n"), None),
    ):
        models[0]["featureId"] = feature_id
        candidate = output / "target.gff3"
        candidate.write_bytes(render(metadata, rows))
        expect(base, candidate, error)

    invalid_fields = (
        ("contributors", [{"name": "Example", "role": "curator", "uri": 42}]),
        ("evidence", [{"description": "Synthetic evidence", "uri": 42}]),
        ("methods", {"software": [{"name": "Synthetic software", "uri": 42}]}),
        ("methods", {"protocol": 42}),
        ("publication", {"article": None}),
        ("evidence", [{"description": "Synthetic evidence", "uri": "not a URI"}]),
        ("methods", {"protocol": "not a URI"}),
        # Link fields take only the schemes FORMAT.md R14 accepts.
        ("evidence", [{"description": "Synthetic evidence", "uri": "javascript:void(0)"}]),
        ("methods", {"software": [{"name": "Synthetic software", "uri": "data:,x"}]}),
        ("methods", {"protocol": "file:///synthetic/protocol"}),
        # Opaque text is non-blank, trimmed and free of control characters.
        ("modelId", " model-a"),
        ("modelId", "\u00a0model-a"),
        ("reference", {"genomeReference": dict(
            models[0]["reference"]["genomeReference"], assemblyName="")}),
        ("reference", {"genomeReference": dict(
            models[0]["reference"]["genomeReference"], assemblyName=" ")}),
        ("reuseConditions", " "),
        ("reuseConditions", "CC-BY-4.0\n"),
        ("contributors", [{"name": "Example\u200b", "role": "curator"}]),
        ("publication", {"deposit": ["doi: 10.0000/synthetic"]}),
        # The curie text composition forbids trailing space and invisible text.
        ("publication", {"deposit": ["doi:10.0000/synthetic "]}),
        ("publication", {"deposit": ["doi:10.0000/synthetic\u200b"]}),
    )
    for field, value in invalid_fields:
        invalid_metadata = copy.deepcopy(metadata)
        invalid_metadata["x-fhgm-models"][0][field] = value
        candidate.write_bytes(render(invalid_metadata, payload))
        expect(base, candidate, "invalid under draft contract v0.1")

    models.append(dict(models[0]))
    candidate.write_bytes(render(metadata, payload))
    expect(base, candidate, "Ambiguous model ID")
    models.pop()

    reference = metadata.pop("genomeReference")
    candidate.write_bytes(render(metadata, payload))
    expect(base, candidate, "is not valid under any")
    metadata["genomeReference"] = dict(reference, accession="SYNTHETIC_OTHER.1")

    revised = parse_header(rich.read_bytes().splitlines(keepends=True))
    del revised["checksum"]
    revised["genomeReference"] = metadata["genomeReference"]
    revised["x-fhgm-models"][0]["reference"]["genomeReference"] = metadata["genomeReference"]
    candidate.write_bytes(render(revised, payload))
    expect(base, candidate, "no matching assembly link", minimal)

    candidate.write_bytes(minimal.read_bytes() + b"# changed bytes\n")
    expect(base, candidate, "File checksum mismatch")


def selection_checks(bases, output):
    """Base selection by citation is exercised only when both releases are supplied."""
    refs = {registered_ref(path): path for path in bases}
    if not {"v0.5.0", "v0.6.0"} <= set(refs):
        print("Both registered bases were not supplied: selection cross-checks skipped "
              "(supply v0.5.0 and v0.6.0 bytes to run them).")
        return
    first, second = refs["v0.5.0"], refs["v0.6.0"]
    minimal = FIXTURES / "minimal.fhgff3.gff3"
    rich = FIXTURES / "rich.fhgff3.gff3"

    def run(*arguments):
        return subprocess.run([sys.executable, str(VALIDATOR), *map(str, arguments)],
                              capture_output=True, text=True)

    def refused(result, text):
        assert result.returncode == 1 and text in result.stderr, (result.stdout, result.stderr)

    routed_11 = ("cites schema 'https://w3id.org/fair-bioheaders/fhgff3/v0.5.0' "
                 "(schemaVersion '1.1') -> FAIR-bioHeaders/FAIR-bioHeaders-Specification@v0.5.0")
    # A v0.5.0 carrier routes to the v0.5.0 bytes even when the v0.6.0 bytes
    # are also supplied, and its chain resolves.
    routing = expect(first, rich, None, minimal, second)
    assert routed_11 in routing.stdout, routing.stdout
    # A v0.6.0 carrier with a v0.5.0 predecessor: each file is judged by the
    # release it cites.
    twin_rich = twin_12(rich, output, "twin-rich.fhgff3.gff3")
    result = run("--base-schema", first, "--base-schema", second,
                 "--predecessor", minimal, twin_rich)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert ("(schemaVersion '1.2') -> FAIR-bioHeaders/FAIR-bioHeaders-Specification@v0.6.0"
            in result.stdout), result.stdout
    assert routed_11 in result.stdout, result.stdout
    # No substitution: the same chain with only the v0.6.0 bytes refuses the
    # v0.5.0 predecessor rather than judging it by the newer release, and a
    # v0.6.0 carrier with only the v0.5.0 bytes is refused likewise.
    refused(run("--base-schema", second, "--predecessor", minimal, twin_rich),
            "The carrier cites the FHGFF3 v0.5.0 release, whose bytes were not supplied")
    refused(run("--base-schema", first, twin_rich),
            "The carrier cites the FHGFF3 v0.6.0 release, whose bytes were not supplied")
    # schemaVersion does not steer selection: the cited release's own enum
    # judges it. A v0.5.0 citation stating 1.2 is rejected by the v0.5.0 bytes,
    # and a v0.6.0 citation stating a version no release states is rejected by
    # the v0.6.0 bytes.
    for schema, version, error in (
        ("https://w3id.org/fair-bioheaders/fhgff3/v0.5.0", "1.2", "'1.2' is not one of"),
        (FHGFF3_12_SCHEMA, "9.9", "'9.9' is not one of"),
    ):
        candidate = rerender(minimal, output, "identity.fhgff3.gff3",
                             schema=schema, schemaVersion=version)
        refused(run("--base-schema", first, "--base-schema", second, candidate), error)
    # A citation no registered release answers to - a superseded release or
    # raw main - and a missing citation are refused at selection.
    refused(run("--base-schema", first, "--base-schema", second,
                CONFORMANCE_VECTORS / "invalid" / "transport-1-0-extension.fhgff3.gff3"),
            "which no registered FHGFF3 base release answers to")
    candidate = rerender(minimal, output, "raw-main.fhgff3.gff3", schema=(
        "https://raw.githubusercontent.com/FAIR-bioHeaders/"
        "FAIR-bioHeaders-Specification/main/fhgff3.json"))
    refused(run("--base-schema", first, "--base-schema", second, candidate),
            "which no registered FHGFF3 base release answers to")
    candidate = rerender(minimal, output, "no-schema.fhgff3.gff3", schema=None)
    refused(run("--base-schema", first, "--base-schema", second, candidate),
            "The carrier states no schema URL")
    print("Base selection checks passed: routing by cited URL, no substitution when the "
          "cited bytes are missing, schemaVersion judged by the cited release, and "
          "refusal of unregistered or absent citations.")


def rerender(source, output, name, **changes):
    """Re-render a fixture with header fields changed (None deletes one)."""
    metadata = parse_header(source.read_bytes().splitlines(keepends=True))
    del metadata["checksum"]
    for key, value in changes.items():
        if value is None:
            metadata.pop(key, None)
        else:
            metadata[key] = value
    payload = b"".join(
        line for line in source.read_bytes().splitlines(keepends=True)
        if not line.startswith(b"#")
    )
    candidate = output / name
    candidate.write_bytes(render(metadata, payload))
    return candidate


def s6k_fixture(base):
    derived = S6K / "DanaCAF1_S6k.fhgm-models.fhgff3.gff3"
    plain = S6K / "DanaCAF1_S6k.gff3"
    kept = b"".join(
        line for line in derived.read_bytes().splitlines(keepends=True)
        if not line.startswith(b"#~")
    )
    assert kept == plain.read_bytes(), "S6k feature payload bytes drifted"
    expect(base, derived)


def model_fixtures(bases, sealed, output):
    generated = output / "regenerated"
    generated.mkdir(exist_ok=True)
    subprocess.run(
        [sys.executable, str(MODEL_FIXTURES / "make_fixtures.py"), str(generated)],
        check=True, capture_output=True,
    )
    for fixture in sorted(MODEL_FIXTURES.glob("*.fhgff3.gff3")):
        assert (generated / fixture.name).read_bytes() == fixture.read_bytes(), \
            f"{fixture.name} is not byte-reproducible"

    base = bases
    v1 = MODEL_FIXTURES / "snapshot-v1.fhgff3.gff3"
    v2 = MODEL_FIXTURES / "snapshot-v2.fhgff3.gff3"
    predecessor_name_mismatch = MODEL_FIXTURES / "predecessor-name-mismatch.fhgff3.gff3"
    expect(base, MODEL_FIXTURES / "valid-single.fhgff3.gff3")
    expect(base, v1)
    expect(base, v2, predecessor=v1)
    expect(base, v2, predecessor=[v1, predecessor_name_mismatch])
    expect(base, MODEL_FIXTURES / "pointer-absent-snapshot.fhgff3.gff3",
           "predecessor is unresolvable", v1)
    expect(base, MODEL_FIXTURES / "ambiguous-model-id.fhgff3.gff3", "Ambiguous model ID")
    expect(base, MODEL_FIXTURES / "version-reuse.fhgff3.gff3",
           "reuses the predecessor model version", v1)
    expect(base, MODEL_FIXTURES / "pointer-version-mismatch.fhgff3.gff3",
           "predecessor records version", v1)
    expect(base, MODEL_FIXTURES / "predecessor-name-mismatch.fhgff3.gff3",
           "names another model ID", v1)
    expect(base, MODEL_FIXTURES / "version-gap-skip.fhgff3.gff3",
           "already has a recorded successor", [v1, v2])
    expect(base, MODEL_FIXTURES / "record-without-reference.fhgff3.gff3",
           "invalid under draft contract v0.1")
    expect(base, MODEL_FIXTURES / "record-reference-conflict.fhgff3.gff3",
           "contradicts the file genome link")

    # The demonstrated gap: the released base schema and checksum accept every
    # rejection fixture, and only the model-level checker rejects them.
    validator = None
    for fixture in sorted(MODEL_FIXTURES.glob("*.fhgff3.gff3")):
        if fixture.name.startswith(("valid-", "snapshot-")):
            continue
        data = fixture.read_bytes()
        if validator is None:
            from jsonschema import Draft202012Validator

            validator = Draft202012Validator(
                json.loads(sealed.read_bytes()),
                format_checker=Draft202012Validator.FORMAT_CHECKER,
            )
        validate_file(data, validator)
    print("Base schema and checksum accept every rejection fixture.")


def run(bases, output):
    """Every fixture, with every supplied base handed to the checker.

    The fixtures cite v0.5.0, so those bytes are required; the checker selects
    them by citation, and the gap demonstration uses them directly.
    """
    sealed = next((path for path in bases if registered_ref(path) == "v0.5.0"), None)
    if sealed is None:
        raise SystemExit("check_draft.py needs the registered v0.5.0 base bytes: every "
                         "fixture cites that release")
    contract_examples(bases, sealed, output)
    s6k_fixture(bases)
    model_fixtures(bases, sealed, output)
    print("Draft FHGM contract v0.1 acceptance and rejection cases passed with bases "
          + ", ".join(path.name for path in bases) + ".")


if __name__ == "__main__":
    bases = [Path(argument) for argument in sys.argv[1:]]
    if not bases:
        raise SystemExit("usage: check_draft.py BASE [BASE ...]  "
                         "(released fhgff3.json bytes registered in base-schemas.json)")
    with TemporaryDirectory() as directory:
        output = Path(directory)
        run(bases, output)
        selection_checks(bases, output)
