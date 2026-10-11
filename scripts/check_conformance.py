"""Check the FHR conformance vectors against their manifest.

Without options this needs only the Python standard library: it regenerates the
vectors in a temporary directory and compares bytes, and recomputes each valid
vector's SHA-512/256 checksum with its own reading of docs/FORMAT.md.
``--schema`` also validates valid vectors' metadata against fhr.json (needs
PyYAML and jsonschema); JSON-LD vectors are read by rule J1 first.
``--converter`` runs fhr-fasta-validate/fhr-gfa-validate on every FASTA/GFA
vector and ``fhr-convert in.html out.json`` or ``fhr-convert in.jsonld out.json``
on every microdata or JSON-LD vector: valid vectors must exit 0 (microdata and
JSON-LD ones must also produce exactly the manifest metadata) and invalid
vectors nonzero. A converter that rejects every vector of a format as an
unsupported file extension predates that format; those vectors are left out and
reported, unless ``--require-format`` names the format. ``--skip-format`` leaves
out a format explicitly.
"""

import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "make_conformance.py"
PREFIXES = {"fasta": b";~", "gfa": b"#~", "fhp-fasta": b";~"}
# The container whose header-block rules apply to each format (R10).
CONTAINERS = {"fasta": "fasta", "gfa": "gfa", "fhp-fasta": "fasta"}
PLACEHOLDER_CHECKSUMS = {"A" * 43 + "="}
COMMANDS = {"fasta": "fhr-fasta-validate", "gfa": "fhr-gfa-validate", "microdata": "fhr-convert",
            "jsonld": "fhr-convert", "fhp-fasta": "fhr-fasta-validate"}
ENTRY_POINTS = {"fasta": "fasta_validate_main", "gfa": "gfa_validate_main",
                "microdata": "convert_main", "jsonld": "convert_main",
                "fhp-fasta": "fasta_validate_main"}
# Formats whose vectors the converter writes out as JSON metadata.
EXTRACTED = {"microdata", "jsonld"}
RULE_DOCUMENTS = ("docs/FORMAT.md", "docs/MICRODATA.md", "docs/JSONLD.md", "docs/FHP.md")
# The schema each format's metadata must validate against (FHP: docs/FHP.md P1).
SCHEMAS = {"fhp-fasta": "fhp.json"}


def generated_files(directory):
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and (path.name == "manifest.json" or path.parent.name in {"valid", "invalid"})
    }


def check_up_to_date(conformance):
    """Regenerate the vectors and report files whose bytes differ."""
    with tempfile.TemporaryDirectory() as temporary:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--output", temporary],
            capture_output=True, text=True,
        )
        if result.returncode:
            return [f"generator failed: {result.stderr.strip()}"]
        expected = generated_files(Path(temporary))
    actual = generated_files(conformance)
    problems = [f"{name}: missing" for name in sorted(expected.keys() - actual.keys())]
    problems += [f"{name}: not produced by the generator" for name in sorted(actual.keys() - expected.keys())]
    problems += [
        f"{name}: differs from the generator output"
        for name in sorted(expected.keys() & actual.keys()) if expected[name] != actual[name]
    ]
    return problems


def split_lines(data):
    """Yield (start, end) offsets of lines ending in LF, CRLF, CR or end of data."""
    start, size = 0, len(data)
    while start < size:
        end = start
        while end < size and data[end] not in (10, 13):
            end += 1
        if end < size:
            end += 2 if data[end] == 13 and data[end + 1:end + 2] == b"\n" else 1
        yield start, end
        start = end


def fhr_checksum(data, kind):
    """Return (value on the checksum line, computed checksum) for decompressed bytes."""
    prefix = PREFIXES[kind]
    fhr_lines = []
    block = True
    for start, end in split_lines(data):
        line = data[start:end]
        fasta = CONTAINERS[kind] == "fasta"
        if block and (line[:1] == b">" if fasta else line[:1] != b"#" and line.strip()):
            block = False
        if line.startswith(prefix):
            if not block:
                raise ValueError("FHR line after the leading header block")
            fhr_lines.append((start, end, line[len(prefix):].rstrip(b"\r\n")))
    content = [text for _, _, text in fhr_lines if text.strip() and text.lstrip()[:1] != b"#"]
    if not content:
        raise ValueError("no FHR metadata")
    root = min(len(text) - len(text.lstrip(b" \t")) for text in content)
    candidates = []
    for start, end, text in fhr_lines:
        found = re.fullmatch(rb"([ \t]*)checksum[ \t]*:(.*)", text, re.S)
        if found and len(found.group(1)) == root:
            candidates.append((start, end, found.group(2)))
    if len(candidates) != 1:
        raise ValueError(f"{len(candidates)} root-level checksum lines")
    start, end, value = candidates[0]
    value = value.strip().decode("utf-8")
    if len(value) > 1 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1]
    sha = hashlib.new("sha512_256")
    sha.update(data[:start])
    sha.update(data[end:])
    return value, base64.b64encode(sha.digest()).decode("ascii")


def read_vector(conformance, vector):
    data = (conformance / vector["file"]).read_bytes()
    if vector["compressed"]:
        if not data.startswith(b"\x1f\x8b"):
            raise ValueError("compressed vector lacks the gzip magic bytes")
        data = gzip.decompress(data)  # Reads every gzip/BGZF member.
    return data


def check_checksums(conformance, manifest):
    problems = []
    for vector in manifest["vectors"]:
        name = vector["id"]
        if vector["format"] in EXTRACTED:
            continue  # In microdata and JSON-LD the checksum is an ordinary metadata value.
        try:
            data = read_vector(conformance, vector)
        except (OSError, ValueError, EOFError) as error:
            problems.append(f"{name}: {error}")
            continue
        try:
            stated, computed = fhr_checksum(data, vector["format"])
        except (ValueError, UnicodeDecodeError) as error:
            if vector["expected"] == "valid":
                problems.append(f"{name}: {error}")
            continue
        if vector["expected"] == "valid":
            if vector["checksum"] in PLACEHOLDER_CHECKSUMS:
                problems.append(f"{name}: placeholder checksum")
            if not stated == computed == vector["checksum"]:
                problems.append(
                    f"{name}: manifest {vector['checksum']}, line {stated}, computed {computed}"
                )
        elif vector["rule"] in {"R1", "R3", "R4"} and stated == computed:
            problems.append(f"{name}: expected a checksum mismatch")
    return problems


def check_manifest(manifest):
    problems = []
    labelled = [rule for document in RULE_DOCUMENTS
                for rule in re.findall(r"\[([RMJP]\d+)\]", (ROOT / document).read_text())]
    if labelled != list(manifest["rules"]):
        problems.append(f"rule ids {labelled} in {', '.join(RULE_DOCUMENTS)} "
                        "differ from the manifest")
    coverage = {rule: set() for rule in manifest["rules"]}
    for vector in manifest["vectors"]:
        rules = vector["rules"] if vector["expected"] == "valid" else [vector["rule"]]
        for rule in rules:
            if rule not in coverage:
                problems.append(f"{vector['id']}: unknown rule {rule}")
                continue
            coverage[rule].add(vector["expected"])
    for rule, outcomes in coverage.items():
        if "notApplicable" not in manifest["rules"][rule] and outcomes != {"valid", "invalid"}:
            problems.append(f"{rule}: needs at least one valid and one invalid vector")
    return problems


def check_schema(conformance, manifest):
    """Validate the metadata of valid vectors against fhr.json, or fhp.json for FHP."""
    from jsonschema import Draft202012Validator, FormatChecker
    import yaml

    validators = {
        name: Draft202012Validator(json.loads((ROOT / name).read_text()),
                                   format_checker=FormatChecker())
        for name in {"fhr.json", *SCHEMAS.values()}
    }
    problems = []
    for vector in manifest["vectors"]:
        validator = validators[SCHEMAS.get(vector["format"], "fhr.json")]
        if vector["format"] == "fhp-fasta" and vector["expected"] == "invalid" \
                and vector["rule"] in {"P1", "P2"}:
            # The parsed header must match the manifest and fail the schema the
            # rule names: fhp.json for P1, fhr.json for P2 (docs/FHP.md).
            prefix = PREFIXES[vector["format"]]
            text = "\n".join(
                line[len(prefix):].rstrip(b"\r\n").decode("utf-8")
                for line in read_vector(conformance, vector).splitlines(keepends=True)
                if line.startswith(prefix)
            )
            if not same_json(yaml.safe_load(text), vector["metadata"]):
                problems.append(f"{vector['id']}: parsed metadata differs from the manifest")
            schema = "fhp.json" if vector["rule"] == "P1" else "fhr.json"
            if not list(validators[schema].iter_errors(vector["metadata"])):
                problems.append(f"{vector['id']}: metadata unexpectedly matches {schema}")
            continue
        if vector["format"] == "jsonld" and vector["expected"] == "valid":
            from make_jsonld import canonical_record, is_canonical

            document = json.loads((conformance / vector["file"]).read_text(encoding="utf-8"))
            # Other forms (J3 to J5) need a JSON-LD processor; tests/test_jsonld_roundtrip.py
            # checks them with PyLD.
            if is_canonical(document) and not same_json(canonical_record(document),
                                                        vector["metadata"]):
                problems.append(f"{vector['id']}: rule J1 reading differs from the manifest metadata")
        if vector["format"] in EXTRACTED:
            errors = list(validator.iter_errors(vector.get("metadata", {})))
            if vector["expected"] == "valid":
                problems += [f"{vector['id']}: {error.json_path}: {error.message}"
                             for error in errors]
                if vector["metadata"].get("checksum") in PLACEHOLDER_CHECKSUMS:
                    problems.append(f"{vector['id']}: placeholder checksum")
                if "seqcol_id" in vector["metadata"]:
                    problems.append(f"{vector['id']}: valid vectors must not carry a SeqCol placeholder")
            elif "metadata" in vector and not errors:
                problems.append(f"{vector['id']}: extracted metadata unexpectedly matches fhr.json")
            continue
        if vector["expected"] != "valid":
            continue
        prefix = PREFIXES[vector["format"]]
        data = read_vector(conformance, vector)
        text = "\n".join(
            line[len(prefix):].rstrip(b"\r\n").decode("utf-8")
            for line in data.splitlines(keepends=True) if line.startswith(prefix)
        )
        metadata = yaml.safe_load(text)
        for error in validator.iter_errors(metadata):
            problems.append(f"{vector['id']}: {error.json_path}: {error.message}")
        for key, value in vector["metadata"].items():
            if metadata.get(key) != value:
                problems.append(f"{vector['id']}: {key} is {metadata.get(key)!r}, expected {value!r}")
        if metadata.get("checksum") != vector["checksum"]:
            problems.append(f"{vector['id']}: parsed checksum differs from the manifest")
        if "seqcol_id" in metadata:
            problems.append(f"{vector['id']}: valid vectors must not carry a SeqCol placeholder")
    return problems


def converter_commands(location):
    """Return a function mapping a format to the command list that validates it."""
    if location == "PATH":
        found = {kind: shutil.which(name) for kind, name in COMMANDS.items()}
        if not all(found.values()):
            raise ValueError(f"{', '.join(COMMANDS.values())} are not on PATH")
        return lambda kind: [found[kind]]
    path = Path(location)
    if (path / "fhr" / "cli.py").is_file():  # A converter source checkout.
        def from_checkout(kind):
            code = (f"import sys; sys.path.insert(0, {str(path.resolve())!r}); "
                    f"sys.argv[0] = {COMMANDS[kind]!r}; "
                    f"from fhr.cli import {ENTRY_POINTS[kind]} as main; sys.exit(main())")
            return [sys.executable, "-c", code]
        return from_checkout
    for directory in (path, path / "bin", path / "Scripts"):
        found = {kind: shutil.which(name, path=str(directory)) for kind, name in COMMANDS.items()}
        if all(found.values()):
            return lambda kind: [found[kind]]
    raise ValueError(f"{location}: no converter checkout, environment or bin directory")


def same_json(left, right):
    """JSON equality that keeps booleans, numbers, strings and containers apart."""
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(same_json(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(map(same_json, left, right))
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    numbers = (int, float)
    if isinstance(left, numbers) and isinstance(right, numbers):
        return left == right
    return type(left) is type(right) and left == right


UNSUPPORTED = "Unsupported file extension"


def check_converter(conformance, manifest, location, skip=(), require=(), unsupported=None):
    """Run the converter on every vector and return the disagreements.

    A converter that rejects every vector of a format with "Unsupported file
    extension" predates that format: its vectors are left out and the format is
    added to ``unsupported``, unless the format is in ``require``.
    """
    command = converter_commands(location)
    problems = []
    by_format = {}
    for vector in manifest["vectors"]:
        if vector["format"] in skip:
            continue
        with tempfile.TemporaryDirectory() as temporary:
            arguments = [str(conformance / vector["file"])]
            output = Path(temporary) / "metadata.json"
            if vector["format"] in EXTRACTED:
                arguments.append(str(output))
            result = subprocess.run(
                command(vector["format"]) + arguments,
                capture_output=True, text=True, timeout=120, cwd=temporary,
                env={**os.environ, "PYTHONSAFEPATH": "1"},
            )
            accepted = result.returncode == 0
            by_format.setdefault(vector["format"], []).append(
                not accepted and UNSUPPORTED in (result.stderr + result.stdout))
            extracted = None
            if accepted and vector["format"] in EXTRACTED:
                try:
                    extracted = json.loads(output.read_text(encoding="utf-8"))
                except (OSError, ValueError) as error:
                    problems.append(f"{vector['id']}: converter wrote no JSON metadata ({error})")
                    continue
        if not accepted and UNSUPPORTED in (result.stderr + result.stdout) \
                and vector["format"] not in require:
            problems.append((vector["format"], f"{vector['id']}: converter does not support "
                             f"the {vector['format']} format"))
            continue
        if accepted != (vector["expected"] == "valid"):
            detail = (result.stderr or result.stdout).strip().splitlines()
            detail = detail[-1] if detail else f"exit {result.returncode}"
            outcome = "accepted" if accepted else f"rejected ({detail})"
            expected = vector["expected"] + (f", {vector['rule']}" if "rule" in vector else "")
            problems.append(f"{vector['id']}: converter {outcome}; expected {expected}")
        elif extracted is not None and not same_json(extracted, vector["metadata"]):
            differences = sorted(
                key for key in extracted.keys() | vector["metadata"].keys()
                if not same_json(extracted.get(key), vector["metadata"].get(key))
            )
            problems.append(f"{vector['id']}: converter extracted different metadata for "
                            f"{', '.join(differences)}: "
                            + json.dumps({key: extracted.get(key) for key in differences},
                                         ensure_ascii=False))
    # A format is skipped only if the converter rejected all of its vectors as
    # unsupported; otherwise those rejections are real disagreements.
    skipped = {fmt for fmt, flags in by_format.items() if flags and all(flags)
               and fmt not in require}
    if unsupported is not None:
        unsupported.update(skipped)
    return [problem[1] if isinstance(problem, tuple) else problem for problem in problems
            if not (isinstance(problem, tuple) and problem[0] in skipped)]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--conformance", type=Path, default=ROOT / "conformance",
                        help="vector directory (default: conformance/)")
    parser.add_argument("--schema", action="store_true",
                        help="validate valid vectors' metadata against fhr.json (needs PyYAML, jsonschema)")
    parser.add_argument("--converter", nargs="?", const="PATH", metavar="LOCATION",
                        help="run the converter CLI: a converter checkout, a virtual environment "
                             "or bin directory, or PATH (the default when no value is given)")
    parser.add_argument("--skip-regeneration", action="store_true",
                        help="do not compare the vectors with freshly generated ones")
    parser.add_argument("--skip-format", action="append", default=[], metavar="FORMAT",
                        choices=sorted(COMMANDS),
                        help="with --converter, leave out the vectors of FORMAT (repeatable), "
                             "for converters that predate it")
    parser.add_argument("--require-format", action="append", default=[], metavar="FORMAT",
                        choices=sorted(COMMANDS),
                        help="with --converter, fail instead of skipping when the converter "
                             "does not support FORMAT (repeatable). Without it, a format whose "
                             "every vector is rejected as an unsupported file extension is "
                             "skipped and reported")
    args = parser.parse_args()
    unsupported = set()
    conformance = args.conformance.resolve()
    manifest = json.loads((conformance / "manifest.json").read_text())

    steps = []
    if not args.skip_regeneration:
        steps.append(("vectors match the generator", lambda: check_up_to_date(conformance)))
    steps.append(("manifest covers the labelled rules", lambda: check_manifest(manifest)))
    steps.append(("checksums recomputed independently", lambda: check_checksums(conformance, manifest)))
    if args.schema:
        steps.append(("valid metadata matches fhr.json (fhp.json for FHP)", lambda: check_schema(conformance, manifest)))
    if args.converter:
        steps.append((f"converter ({args.converter}) agrees with the manifest",
                      lambda: check_converter(conformance, manifest, args.converter,
                                              args.skip_format, args.require_format,
                                              unsupported)))

    failed = False
    for label, step in steps:
        try:
            problems = step()
        except ValueError as error:
            problems = [str(error)]
        for problem in problems:
            print(f"{label}: {problem}", file=sys.stderr)
        failed |= bool(problems)
        print(f"{'FAIL' if problems else 'ok'}: {label}", flush=True)
    count = len(manifest["vectors"])
    left_out = set(args.skip_format) | unsupported
    skipped = sum(vector["format"] in left_out for vector in manifest["vectors"])
    note = ""
    if args.converter and skipped:
        reasons = [f"{fmt} not supported by this converter" for fmt in sorted(unsupported)]
        reasons += [f"{fmt} skipped" for fmt in sorted(set(args.skip_format) - unsupported)]
        note = f" ({skipped} vectors left out: {'; '.join(reasons)})"
    print(f"{count} vectors {'failed' if failed else 'passed'}{note}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
