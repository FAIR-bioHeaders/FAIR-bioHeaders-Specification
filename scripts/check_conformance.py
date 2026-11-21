"""Check the FHR conformance vectors against their manifest.

Without options this needs only the Python standard library: it regenerates the
vectors in a temporary directory and compares bytes, and recomputes each valid
vector's SHA-512/256 checksum with its own reading of docs/FORMAT.md. It also
reads ``conformance/manifest.json`` at every release tag and fails if a released
vector id is neither a current vector nor ``retired`` (this needs the git tags).
``--schema`` also validates vectors' metadata against the schema their ``schema``
URL selects (docs/SCHEMA-VERSIONS.md; needs PyYAML and jsonschema, and git tags
for older releases); JSON-LD vectors are read by rule J1 first.
``--converter`` runs fhr-fasta-validate/fhr-gfa-validate on every FASTA/GFA
vector and ``fhr-convert in.html out.json`` or ``fhr-convert in.jsonld out.json``
on every microdata or JSON-LD vector: valid vectors must exit 0 (microdata and
JSON-LD ones must also produce exactly the manifest metadata) and invalid
vectors must exit 1 with a diagnostic (tracebacks/process failures do not count). A converter that rejects every vector of a format as an
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
PREFIXES = {"fasta": b";~", "gfa": b"#~", "fhp-fasta": b";~", "fhgff3": b"#~"}
# The container whose header-block rules apply to each format (R10, G1).
CONTAINERS = {"fasta": "fasta", "gfa": "gfa", "fhp-fasta": "fasta", "fhgff3": "gff3"}
PLACEHOLDER_CHECKSUMS = {"A" * 43 + "="}
COMMANDS = {"fasta": "fhr-fasta-validate", "gfa": "fhr-gfa-validate", "microdata": "fhr-convert",
            "jsonld": "fhr-convert", "fhp-fasta": "fhr-fasta-validate",
            "fhgff3": "fhr-gff3-validate"}
ENTRY_POINTS = {"fasta": "fasta_validate_main", "gfa": "gfa_validate_main",
                "microdata": "convert_main", "jsonld": "convert_main",
                "fhp-fasta": "fasta_validate_main", "fhgff3": "gff3_validate_main"}
# Formats whose command a converter may lack because it predates them: their
# vectors are then reported as unsupported, like an unsupported file extension.
OPTIONAL_COMMANDS = {"fhgff3"}
# Formats whose vectors the converter writes out as JSON metadata.
EXTRACTED = {"microdata", "jsonld"}
RULE_DOCUMENTS = ("docs/FORMAT.md", "docs/MICRODATA.md", "docs/JSONLD.md", "docs/FHP.md",
                  "docs/FHGFF3.md", "docs/SCHEMA-VERSIONS.md")
# The schema each format's metadata must validate against (docs/FHP.md P1,
# docs/FHGFF3.md G2).
SCHEMAS = {"fhp-fasta": "fhp.json", "fhgff3": "fhgff3.json"}
# Invalid vectors whose rule names the schema their metadata must fail.
SCHEMA_RULES = {"P1": "fhp.json", "P2": "fhr.json", "G2": "fhgff3.json", "G3": "fhr.json"}
# Schema selection (docs/SCHEMA-VERSIONS.md V1-V6) and the version registry.
REGISTRY_PATH = ROOT / "schemas" / "versions.json"
# Either repository name (#108): FAIR-bioHeaders-Specification, or FHR-Specification
# as it was called before; the old URLs stay supported aliases. The ref may have
# several path segments (refs/heads/main): only main or a release tag is supported (V4).
RAW_SCHEMA = re.compile(r"https://raw\.githubusercontent\.com/FAIR-bioHeaders/"
                        r"(?:FHR|FAIR-bioHeaders)-Specification/(.+)/(fhr|fhp|fhgff3|fht)\.json")
W3ID_SCHEMA = re.compile(r"https://w3id\.org/fair-bioheaders/(fhr|fhp|fhgff3|fht)/"
                         r"(v[0-9]+\.[0-9]+\.[0-9]+)/?")
RELEASE_TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+")
TYPE_NAMES = {"fhr": "FHR", "fhp": "FHP", "fhgff3": "FHGFF3", "fht": "FHT"}
UNSUPPORTED_VERSION = "unsupported schema version"


def select_schema(value, registry=None):
    """Return (header type, release or "main", file name) or (type, None, None) when the
    version is unsupported (V4). Any other value is FHR on main (V5)."""
    registry = registry or json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if isinstance(value, str):
        raw, w3id = RAW_SCHEMA.fullmatch(value), W3ID_SCHEMA.fullmatch(value)
        if raw:
            # The historical FHR repository aliases existing released types,
            # but no FHT artifact/compatibility mirror exists there. A new FHT
            # contract must not manufacture authority by sharing their regex.
            if raw.group(2) == 'fht' and not value.startswith('https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/'):
                return 'FHR', 'main', registry['files']['FHR']  # V5, not FHT.
            ref, header_type = raw.group(1), TYPE_NAMES[raw.group(2)]
        elif w3id:
            ref, header_type = w3id.group(2), TYPE_NAMES[w3id.group(1)]
        else:
            return "FHR", "main", registry["files"]["FHR"]
        if ref == "main":
            return header_type, "main", registry["files"][header_type]
        if RELEASE_TAG.fullmatch(ref) and header_type in registry["releases"].get(ref, {}):
            return header_type, ref, registry["files"][header_type]
        return header_type, None, None
    return "FHR", "main", registry["files"]["FHR"]


# V6: an FHR 1 record citing raw-main is read against the last FHR 1 release.
FHR1_RELEASE = "v0.3.1"


def is_fhr1_version(version):
    """The number 1 (1 or 1.0); not the string "1" and not a boolean (V6)."""
    return isinstance(version, (int, float)) and not isinstance(version, bool) and version == 1


def select_record(metadata, registry=None):
    """Like select_schema for a record's ``schema``, with rule V6: a raw-main fhr.json URL
    and schemaVersion the number 1 select the v0.3.1 FHR schema."""
    registry = registry or json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    value = metadata.get("schema") if isinstance(metadata, dict) else None
    raw = RAW_SCHEMA.fullmatch(value) if isinstance(value, str) else None
    if raw and raw.groups() == ("main", "fhr") and is_fhr1_version(metadata.get("schemaVersion")):
        return "FHR", FHR1_RELEASE, registry["files"]["FHR"]
    return select_schema(value, registry)


def load_schema(release, name, registry=None):
    """The schema text of ``name`` at ``release``: the working tree for main and the
    registry's current release, otherwise ``git show <tag>:<name>``."""
    registry = registry or json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if release in ("main", registry["current"]):
        return json.loads((ROOT / name).read_text(encoding="utf-8"))
    result = subprocess.run(["git", "show", f"{release}:{name}"], cwd=ROOT,
                            capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f"cannot read {name} at {release} (fetch the git tags): "
                         f"{result.stderr.strip()}")
    return json.loads(result.stdout)


def generated_files(directory):
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and not path.is_relative_to(directory / "fht-v0.7.0") and (path.name == "manifest.json" or path.parent.name in {"valid", "invalid"})
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
        if block and CONTAINERS[kind] == "gff3" and line.startswith(b"##FASTA"):
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
                for rule in re.findall(r"\[([RMJPGV]\d+)\]", (ROOT / document).read_text())]
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
    # Vector ids are never reused: a retired id names no vector.
    ids = {vector["id"] for vector in manifest["vectors"]}
    for retired in manifest.get("retired", []):
        if retired["id"] in ids:
            problems.append(f"{retired['id']}: retired id reused by a vector")
        if retired.get("replacedBy") and retired["replacedBy"] not in ids:
            problems.append(f"{retired['id']}: replacement {retired['replacedBy']} is not a vector")
    return problems


def released_manifests():
    """{tag: manifest} for every release tag whose tree has conformance/manifest.json."""
    tags = subprocess.run(["git", "tag", "--list", "v*"], cwd=ROOT, capture_output=True,
                          text=True)
    if tags.returncode:
        raise ValueError(f"cannot list the release tags: {tags.stderr.strip()}")
    manifests = {}
    for tag in tags.stdout.split():
        shown = subprocess.run(["git", "show", f"{tag}:conformance/manifest.json"], cwd=ROOT,
                               capture_output=True, text=True)
        if not shown.returncode:
            manifests[tag] = json.loads(shown.stdout)
    return manifests


def check_released_ids(manifest, released=None):
    """Every vector id a release published is still a vector or is retired.

    Ids are stable for implementers who pin a release's suite, so dropping or
    renaming a vector without a ``retired`` entry is an error."""
    released = released_manifests() if released is None else released
    if not released:
        return ["no release tag has conformance/manifest.json; fetch the git tags "
                "(git fetch --tags) so released vector ids can be checked"]
    known = ({vector["id"] for vector in manifest["vectors"]}
             | {retired["id"] for retired in manifest.get("retired", [])})
    problems = []
    for tag, old in sorted(released.items()):
        for vector in old["vectors"]:
            if vector["id"] not in known:
                problems.append(f"{vector['id']} (published in {tag}) is neither a vector "
                                "nor retired; add a retired entry in make_conformance.py")
    return problems


def ecma_pattern(pattern):
    """A bounded Python translation of an ECMA-262 ``pattern`` (JSON Schema).

    In ECMA-262 without the multiline flag, ``$`` matches only at the end of the
    string; Python's ``$`` also matches just before a final line feed. Every
    ``$`` outside a character class becomes ``\\Z``. ECMA empty classes match
    nothing (``[]``) or any character (``[^]``); Python treats a leading ``]``
    as a literal class member instead. Match the toolkit adapter's handling.
    This is not a full ECMA engine: shorthand whitespace sets and other
    documented dialect differences remain outside this correction.
    """
    out, escaped, in_class = [], False, False
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if not escaped and not in_class:
            if pattern.startswith("[]", index):
                out.append("(?!)")
                index += 2
                continue
            if pattern.startswith("[^]", index):
                out.append(r"[\s\S]")
                index += 3
                continue
        if escaped:
            out.append(char)
            escaped = False
        elif char == "\\":
            out.append(char)
            escaped = True
        elif in_class:
            out.append(char)
            in_class = char != "]"
        elif char == "[":
            out.append(char)
            in_class = True
        elif char == "$":
            out.append("\\Z")
        else:
            out.append(char)
        index += 1
    return "".join(out)


def schema_validator(schema):
    """Draft 2020-12 with format assertions and bounded ECMA pattern handling."""
    from jsonschema import Draft202012Validator, FormatChecker, ValidationError, validators

    def pattern(validator, value, instance, _schema):
        if not validator.is_type(instance, "string"):
            return
        try:
            matched = re.search(ecma_pattern(value), instance)
        except re.error as error:
            yield ValidationError(
                f"cannot evaluate contract pattern {value!r} with the bounded "
                f"Python translation: {error}"
            )
            return
        if not matched:
            yield ValidationError(f"{instance!r} does not match {value!r}")

    checker = validators.extend(Draft202012Validator, {"pattern": pattern})
    return checker(schema, format_checker=FormatChecker())


def check_schema(conformance, manifest):
    """Validate the metadata of valid vectors against their type's schema."""
    import yaml

    class Loader(yaml.SafeLoader):
        """YAML with dates and times read as strings, as written (FORMAT.md R12)."""

    Loader.yaml_implicit_resolvers = {
        first: [(tag, regexp) for tag, regexp in resolvers
                if tag != "tag:yaml.org,2002:timestamp"]
        for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }

    def load_yaml(text):
        return yaml.load(text, Loader=Loader)

    validators = {
        name: schema_validator(json.loads((ROOT / name).read_text()))
        for name in {"fhr.json", *SCHEMAS.values()}
    }
    selected = {}

    def selected_validator(metadata):
        """The validator for the schema ``metadata`` selects, or None (unsupported)."""
        _, release, name = select_record(metadata)
        if release is None:
            return None
        if (release, name) not in selected:
            selected[release, name] = schema_validator(load_schema(release, name))
        return selected[release, name]

    def header_metadata(vector):
        prefix = PREFIXES[vector["format"]]
        text = "\n".join(
            line[len(prefix):].rstrip(b"\r\n").decode("utf-8")
            for line in read_vector(conformance, vector).splitlines(keepends=True)
            if line.startswith(prefix)
        )
        return load_yaml(text)

    problems = []
    for vector in manifest["vectors"]:
        if vector["format"] in PREFIXES and vector.get("rule", "").startswith("V"):
            # Selection vectors (V1-V6): an unsupported version selects no schema;
            # otherwise the metadata must fail the schema its URL selects.
            validator = selected_validator(header_metadata(vector))
            if vector.get("result") == "unsupported-version":
                if validator is not None:
                    problems.append(f"{vector['id']}: schema URL is not unsupported")
            elif validator is None:
                problems.append(f"{vector['id']}: schema URL is unexpectedly unsupported")
            elif not list(validator.iter_errors(header_metadata(vector))):
                problems.append(f"{vector['id']}: metadata unexpectedly matches the selected schema")
            continue
        validator = validators[SCHEMAS.get(vector["format"], "fhr.json")]
        if vector["expected"] == "valid" and vector["format"] in PREFIXES:
            validator = selected_validator(header_metadata(vector))
            if validator is None:
                problems.append(f"{vector['id']}: valid vector cites an unsupported schema")
                continue
        if vector["format"] in SCHEMAS and vector["expected"] == "invalid" \
                and vector["rule"] in SCHEMA_RULES:
            # The parsed header must match the manifest and fail the schema the
            # rule names (docs/FHP.md P1-P2, docs/FHGFF3.md G2-G3).
            prefix = PREFIXES[vector["format"]]
            text = "\n".join(
                line[len(prefix):].rstrip(b"\r\n").decode("utf-8")
                for line in read_vector(conformance, vector).splitlines(keepends=True)
                if line.startswith(prefix)
            )
            if not same_json(load_yaml(text), vector["metadata"]):
                problems.append(f"{vector['id']}: parsed metadata differs from the manifest")
            schema = SCHEMA_RULES[vector["rule"]]
            if not list(validators[schema].iter_errors(vector["metadata"])):
                problems.append(f"{vector['id']}: metadata unexpectedly matches {schema}")
            continue
        if vector["format"] in PREFIXES and vector["expected"] == "invalid" \
                and vector["rule"] == "R15":
            # Extension fields (docs/FORMAT.md R15): the header must fail the schema
            # its record selects, whether that is the current or an older release's.
            metadata = header_metadata(vector)
            validator = selected_validator(metadata)
            if validator is None:
                problems.append(f"{vector['id']}: schema URL is unexpectedly unsupported")
            elif not list(validator.iter_errors(metadata)):
                problems.append(f"{vector['id']}: metadata unexpectedly matches the selected schema")
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
            # The extracted metadata is checked against the schema it selects (V1-V6).
            validator = selected_validator(vector.get("metadata", {})) or validator
            errors = list(validator.iter_errors(vector.get("metadata", {})))
            if vector["expected"] == "valid":
                problems += [f"{vector['id']}: {error.json_path}: {error.message}"
                             for error in errors]
                if vector["metadata"].get("checksum") in PLACEHOLDER_CHECKSUMS:
                    problems.append(f"{vector['id']}: placeholder checksum")
                if "seqcol_id" in vector["metadata"]:
                    problems.append(f"{vector['id']}: valid vectors must not carry a SeqCol placeholder")
            elif "metadata" in vector and not errors:
                problems.append(f"{vector['id']}: extracted metadata unexpectedly matches its schema")
            continue
        if vector["expected"] != "valid":
            continue
        prefix = PREFIXES[vector["format"]]
        data = read_vector(conformance, vector)
        text = "\n".join(
            line[len(prefix):].rstrip(b"\r\n").decode("utf-8")
            for line in data.splitlines(keepends=True) if line.startswith(prefix)
        )
        metadata = load_yaml(text)
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
    def required_found(found):
        return all(command for kind, command in found.items() if kind not in OPTIONAL_COMMANDS)

    def run(found):
        return lambda kind: [found[kind]] if found[kind] else None

    if location == "PATH":
        found = {kind: shutil.which(name) for kind, name in COMMANDS.items()}
        if not required_found(found):
            raise ValueError(f"{', '.join(COMMANDS.values())} are not on PATH")
        return run(found)
    path = Path(location)
    if (path / "fhr" / "cli.py").is_file():  # A converter source checkout.
        def from_checkout(kind):
            code = (f"import sys; sys.path.insert(0, {str(path.resolve())!r}); "
                    f"sys.argv[0] = {COMMANDS[kind]!r}\n"
                    f"try:\n    from fhr.cli import {ENTRY_POINTS[kind]} as main\n"
                    f"except ImportError:\n"
                    f"    sys.exit({UNSUPPORTED + ' (no ' + COMMANDS[kind] + ')'!r})\n"
                    f"sys.exit(main())")
            return [sys.executable, "-c", code]
        return from_checkout
    for directory in (path, path / "bin", path / "Scripts"):
        found = {kind: shutil.which(name, path=str(directory)) for kind, name in COMMANDS.items()}
        if required_found(found):
            return run(found)
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


def check_converter(conformance, manifest, location, skip=(), require=(), unsupported=None,
                    known_gaps=None):
    """Run the converter on every vector and return the disagreements.

    Process crashes, abnormal exit codes and silent failures never establish a
    valid rejection or satisfy a known gap.

    ``known_gaps`` maps vector ids the converter is known to get wrong to the
    reason: for those the wrong accept/reject outcome is expected instead, and
    the right one is a problem, so a fixed gap must be removed from the list.

    A converter that rejects every vector of a format with "Unsupported file
    extension" predates that format: its vectors are left out and the format is
    added to ``unsupported``, unless the format is in ``require``.
    """
    command = converter_commands(location)
    known_gaps = known_gaps or {}
    ids = {vector["id"] for vector in manifest["vectors"]}
    problems = [f"{gap}: listed as a known gap but is not a vector" for gap in known_gaps
                if gap not in ids]
    by_format = {}
    for vector in manifest["vectors"]:
        if vector["format"] in skip:
            continue
        with tempfile.TemporaryDirectory() as temporary:
            arguments = [str(conformance / vector["file"])]
            output = Path(temporary) / "metadata.json"
            if vector["format"] in EXTRACTED:
                arguments.append(str(output))
            program = command(vector["format"])
            if program is None:  # The converter has no command for this format.
                result = subprocess.CompletedProcess(
                    [], 1, "", f"{UNSUPPORTED} (no {COMMANDS[vector['format']]})")
            else:
                result = subprocess.run(
                    program + arguments,
                    capture_output=True, text=True, timeout=120, cwd=temporary,
                    env={**os.environ, "PYTHONSAFEPATH": "1"},
                )
            diagnostic = (result.stderr + result.stdout).strip()
            if result.returncode != 0 and (result.returncode != 1 or not diagnostic
                    or "Traceback (most recent call last)" in diagnostic):
                # A process failure is not evidence that the converter judged
                # this vector invalid. Never hide it as a known gap or an
                # unsupported format, even when its output includes that text.
                by_format.setdefault(vector["format"], []).append(False)
                detail = diagnostic.splitlines()[-1] if diagnostic else "no diagnostic"
                problems.append(f"{vector['id']}: converter execution failure "
                                f"(exit {result.returncode}: {detail})")
                continue
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
        if vector.get("result") == "unsupported-version" and not accepted \
                and UNSUPPORTED_VERSION not in (result.stderr + result.stdout).lower():
            detail = (result.stderr or result.stdout).strip().splitlines()
            problems.append(f"{vector['id']}: converter rejected it without an unsupported "
                            f"schema version message ({detail[-1] if detail else 'no output'})")
        if vector["id"] in known_gaps:
            if accepted == (vector["expected"] == "valid"):
                problems.append(f"{vector['id']}: converter now gets this known gap right; "
                                "remove it from the known gaps")
            continue
        if accepted != (vector["expected"] == "valid"):
            detail = (result.stderr or result.stdout).strip().splitlines()
            detail = detail[-1] if detail else f"exit {result.returncode}"
            outcome = "accepted" if accepted else f"rejected ({detail})"
            expected = vector["expected"] + (f", {vector['rule']}" if "rule" in vector else "")
            problems.append(f"{vector['id']}: converter {outcome}; expected {expected}")
        elif accepted and missing_warnings(vector.get("warnings", []), result.stderr):
            problems.append(f"{vector['id']}: converter printed no warning; expected one "
                            f"under {', '.join(missing_warnings(vector['warnings'], result.stderr))}")
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


def missing_warnings(rules, stderr):
    """The rules in ``rules`` that no warning line on ``stderr`` names.

    A vector's ``warnings`` lists the rules (R14) under which a validator should
    warn. Any line containing "warning" is not enough: an unrelated warning, such
    as one about the schema version, would satisfy it. Each listed rule needs its
    own line that contains "warning" and names the rule as a complete token: no
    letter, digit or underscore may touch it on either side, so R140, R14A and
    XR14 do not count as R14.
    """
    lines = [line for line in stderr.splitlines() if "warning" in line.lower()]
    return [rule for rule in rules
            if not any(re.search(rf"(?<![A-Za-z0-9_]){re.escape(rule)}(?![A-Za-z0-9_])", line)
                       for line in lines)]


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
    parser.add_argument("--known-gaps", type=Path, metavar="FILE",
                        help="with --converter, a JSON file whose knownGaps object maps vector "
                             "ids to the reason the converter gets them wrong (for example "
                             "conformance/toolkit-pin.json); those vectors must still be wrong")
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
    steps.append(("released vector ids are vectors or retired",
                  lambda: check_released_ids(manifest)))
    steps.append(("checksums recomputed independently", lambda: check_checksums(conformance, manifest)))
    if args.schema:
        steps.append(("valid metadata matches fhr.json (fhp.json for FHP)", lambda: check_schema(conformance, manifest)))
    known_gaps = {}
    if args.known_gaps:
        known_gaps = json.loads(args.known_gaps.read_text(encoding="utf-8")).get("knownGaps", {})
    if args.converter:
        steps.append((f"converter ({args.converter}) agrees with the manifest",
                      lambda: check_converter(conformance, manifest, args.converter,
                                              args.skip_format, args.require_format,
                                              unsupported, known_gaps)))

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
    if args.converter and known_gaps:
        note += (f" ({len(known_gaps)} known converter gaps: "
                 f"{', '.join(sorted(known_gaps))})")
    print(f"{count} vectors {'failed' if failed else 'passed'}{note}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
