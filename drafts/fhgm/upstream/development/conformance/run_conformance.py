# SPDX-License-Identifier: MPL-2.0
"""Independent runner for the draft FHGM conformance manifest and base matrix.

An FHGM model record cannot be tested by schema vectors alone: every model-level
rejection in this suite passes the released FHGFF3 base schema and its
exact-byte checksum (that gap is why the separate checker exists, and the
manifest records it per vector). This script therefore reports the layers
**separately**, as FHGM #9 requires:

    base     the released fhgff3.json schema alone, over the parsed header
    checksum the file-bound SHA-512/256 of the exact bytes, recomputed here with
             hashlib over every byte except the root checksum line and its
             terminator - deliberately a second implementation next to the
             toolkit's, so a shared bug cannot hide
    gff3     ``gff3-validate --no-header``, when that separate tool is installed
    model    ``development/model/validate_fhgm.py``: base selection, transport
             overlay, native record contract and the model-level rules with the
             pointer verdicts

Two lanes run over one suite:

    sealed lane  the committed vectors, observed against the FHGFF3 1.1
                 (v0.5.0) bytes. Every expectation lives in manifest.json and
                 keeps its evidence trail; the lane's semantics are unchanged
                 by the dual-base work.
    matrix lane  (``--matrix``) identity-rewritten twins of the same
                 vectors, evaluated against the FHGFF3 1.2 (v0.6.0) bytes with
                 nothing else altered: the ``#~schema`` and ``#~schemaVersion``
                 lines move to the v0.6.0 citation, and the checksum line is
                 recomputed - except where the sealed record says ``stale``,
                 where the old stated digest is preserved so the vector stays a
                 stale-checksum case. Only a v0.5.0 citation moves; a vector
                 citing anything else keeps its schema URL and only its
                 schemaVersion moves.
                 A file declaring FHGFF3 1.0 has no twin to write (its stated
                 identity IS the defect), so it is evaluated as committed.
                 Expectations live in base_matrix.json, sealed by observation
                 under the same discipline as the manifest.

Both lanes hand the checker BOTH registered base files: the checker selects the
release each loaded file cites by its ``schema`` URL and refuses a citation
whose bytes were not supplied, so a 1.1 predecessor in the matrix lane is
judged by the v0.5.0 bytes it cites, never by the 1.2 bytes. The ``base``
layer is the lane's own release (v0.5.0 for the sealed lane, v0.6.0 for the
matrix lane) over the header read by the toolkit's strict reader.

Nothing is imported from ``check_draft.py`` or from the generators. Clause-derived expectations are committed independently of observed evidence;
actual outcomes are read from a run of the committed checker:
``make_vectors.py`` states no expectations, and ``--seal`` records digests and
checksums from bytes that already matched a recorded outcome; ``--seal-matrix``
does the same for the twins.

Exit status: 0 when every vector matched what the manifest (and, with
``--matrix``, the matrix) records, 1 on a mismatch, 2 when the suite itself
cannot run (missing base schema, unreadable manifest). Skipped lanes are
printed, never hidden.

    python3 run_conformance.py --base-schema ...v0.5.0.json --base-schema ...v0.6.0.json
    python3 run_conformance.py --base-schema ...v0.5.0... --base-schema ...v0.6.0.json --matrix
    python3 run_conformance.py --offline              # bytes, digests, checksums
    python3 run_conformance.py --base-schema ... --verbose
    python3 run_conformance.py --base-schema ... --seal          # re-record digests
    python3 run_conformance.py --base-schema ... --base-schema ... --matrix --seal-matrix
"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
DEVELOPMENT = HERE.parent
REPO = DEVELOPMENT.parent
MANIFEST = HERE / "manifest.json"
MATRIX = HERE / "base_matrix.json"
PROVENANCE = HERE / "provenance.json"
CHECKER = DEVELOPMENT / "model" / "validate_fhgm.py"
REPORT_PATH = None
REGISTRY = DEVELOPMENT / "model" / "base-schemas.json"
GENERATORS = {
    "make_fixtures": DEVELOPMENT / "examples" / "model" / "make_fixtures.py",
    "make_vectors": HERE / "make_vectors.py",
    "make_dmel_vectors": HERE / "make_dmel_vectors.py",
}
S6K_PROFILE = DEVELOPMENT / "examples" / "s6k" / "DanaCAF1_S6k.fhgff3.gff3"
S6K_DERIVED = DEVELOPMENT / "examples" / "s6k" / "DanaCAF1_S6k.fhgm-models.fhgff3.gff3"
EMBED = DEVELOPMENT / "examples" / "s6k" / "embed_models.py"
CHECKSUM_PREFIX = b"#~checksum: "
SCHEMA_PREFIX = b"#~schema: "
VERSION_PREFIX = b"#~schemaVersion: "
VECTOR_ID = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
# The 1.2 citation used for identity-rewritten twins: the w3id URL of the
# v0.6.0 release, which is what fair-bioheaders 0.11.0 writes for a 1.2 header.
TWIN_SCHEMA_URL = "https://w3id.org/fair-bioheaders/fhgff3/v0.6.0"
TWIN_SCHEMA_VERSION = "1.2"


class Failure(Exception):
    """The suite could not be run as recorded."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def covered_bytes(data):
    """Every byte except the root checksum line and its terminator (FORMAT.md R3)."""
    return b"".join(
        line for line in data.splitlines(keepends=True)
        if not line.startswith(CHECKSUM_PREFIX)
    )


def recompute_checksum(data):
    """SHA-512/256 of the covered bytes in standard padded base64 (R1, R3, R4)."""
    return base64.b64encode(hashlib.new("sha512_256", covered_bytes(data)).digest()).decode()


def stated_checksum(data):
    for line in data.splitlines():
        if line.startswith(CHECKSUM_PREFIX):
            return line[len(CHECKSUM_PREFIX):].decode()
    return None


def stated_schema_version(data):
    """The version token on the header's schemaVersion line, as a string or None."""
    for line in data.splitlines():
        if line.startswith(VERSION_PREFIX):
            value = line[len(VERSION_PREFIX):].strip().strip(b"\"'")
            return value.decode()
    return None


def path_of(vector):
    return (HERE / vector["file"]).resolve()


def load_registry():
    """The registered FHGFF3 base releases, keyed by their exact-byte digest."""
    try:
        document = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Failure(f"cannot read the base registry {REGISTRY.name}: {error}")
    return {record["sha256"]: record for record in document["bases"]}


def verify_provenance(provenance, supplied_bases):
    """Refuse to report a pass when a recorded artifact changed under the manifest.

    ``supplied_bases`` maps the digest of each --base-schema file to its path;
    each required provenance base record must appear in it exactly once.
    """
    problems = []
    registry = load_registry()
    for key in ("baseSchema", "matrixBaseSchema"):
        record = provenance[key]
        matches = [entry for entry in registry.values() if entry["sha256"] == record["sha256"]]
        if len(matches) != 1:
            problems.append(f"provenance {key} sha256 {record['sha256']} matches "
                            f"{len(matches)} registry entries, expected exactly 1")
            continue
        for field in ("size", "ref", "commit", "path", "schemaVersion"):
            if matches[0].get(field) != record.get(field):
                problems.append(f"provenance {key}.{field} {record.get(field)!r} != registry "
                                f"{matches[0].get(field)!r}")
        path = supplied_bases.get(record["sha256"])
        if path is None:
            continue  # a lane needing this base refuses explicitly in main()
        data = path.read_bytes()
        if sha256(data) != record["sha256"]:
            problems.append(f"supplied base {path} digest {sha256(data)} != provenance "
                            f"{record['sha256']}")
        if len(data) != record["size"]:
            problems.append(f"supplied base {path} size {len(data)} != provenance "
                            f"{record['size']}")
    for group in ("contractArtifacts", "vectorGenerators"):
        for artifact in provenance[group]:
            path = REPO / artifact["local"]
            if not path.is_file():
                problems.append(f"{artifact['local']}: recorded artifact is missing")
                continue
            data = path.read_bytes()
            if sha256(data) != artifact["sha256"]:
                problems.append(f"{artifact['local']}: sha256 {sha256(data)} != provenance "
                                f"{artifact['sha256']} (re-record provenance.json after a "
                                "contract or generator change, then re-seal the manifest)")
            elif len(data) != artifact["size"]:
                problems.append(f"{artifact['local']}: size {len(data)} != provenance "
                                f"{artifact['size']}")
    return problems


def check_downstream_pins(provenance):
    """Advisory lane: are the draft pins consumers hold on our bytes still fresh?"""
    from urllib.request import Request, urlopen

    problems = []
    for pin in provenance.get("downstreamPins", []):
        tracked = REPO / pin["tracks"]
        local = sha256(tracked.read_bytes())
        request = Request(pin["url"], headers={"Accept": "application/json",
                                               "User-Agent": "fhgm-conformance-pin-freshness"})
        try:
            with urlopen(request, timeout=60) as response:
                document = json.loads(response.read())
        except Exception as error:  # noqa: BLE001 - network lane, report whatever happened
            problems.append(f"{pin['name']}: could not read {pin['url']}: {error}")
            continue
        node = document
        for part in pin["pointer"].strip("/").split("/"):
            node = node[part]
        remote = node.get(pin["field"])
        state = "fresh" if remote == local else "STALE"
        print(f"{state}: {pin['name']} records {pin['field']} {remote} for {pin['tracks']}; "
              f"this tree holds {local}")
        if remote != local:
            problems.append(
                f"{pin['name']}: pinned digest {remote} != current bytes {local}. Refresh the pin "
                "in the consumer repository against the merged commit, never before it merges.")
    return problems


def predecessors_of(vector):
    context = vector.get("context") or {}
    return [(HERE / path).resolve() for path in context.get("predecessors", [])]


# --- twins for the matrix lane ------------------------------------------------

def twin_bytes(data, checksum_outcome):
    """Derive the FHGFF3 1.2 twin of a committed vector, by bytes alone.

    Exactly three things may change: the ``#~schema`` line moves to the v0.6.0
    citation (only a v0.5.0 citation moves; any other citation is kept), the
    ``#~schemaVersion`` line moves to ``1.2``, and the
    ``#~checksum`` line follows (recomputed when the sealed record says the
    checksum verifies, preserved verbatim when it says ``stale`` so the twin
    stays a stale-checksum case). A file declaring FHGFF3 1.0 gets no rewrite:
    its stated identity is the defect, so it is evaluated as committed and the
    method is reported as ``as-committed-1-0``. Every guard raises rather than
    producing a silently partial rewrite.
    """
    if stated_schema_version(data) == "1.0":
        return data, "as-committed-1-0", None
    lines = data.splitlines(keepends=True)
    schema_at = [i for i, line in enumerate(lines) if line.startswith(SCHEMA_PREFIX)]
    version_at = [i for i, line in enumerate(lines) if line.startswith(VERSION_PREFIX)]
    checksum_at = [i for i, line in enumerate(lines) if line.startswith(CHECKSUM_PREFIX)]
    if len(schema_at) != 1 or len(version_at) != 1 or len(checksum_at) != 1:
        raise Failure(f"twin derivation needs exactly one schema, schemaVersion and checksum "
                      f"line; found {len(schema_at)}/{len(version_at)}/{len(checksum_at)}")
    i, j, k = schema_at[0], version_at[0], checksum_at[0]
    old_version = lines[j]
    if b"1.1" not in old_version:
        raise Failure(f"twin derivation expects a sealed 1.1 carrier, found "
                      f"{old_version.decode().strip()!r}")
    new_lines = list(lines)
    value = lines[i][len(SCHEMA_PREFIX):]
    quote = value[:1] if value[:1] in (b'"', b"'") else b""
    if quote and not value.rstrip(b"\r\n").endswith(quote):
        raise Failure(f"unbalanced quoting on the schema line: {value.decode().strip()!r}")
    if b"/v0.5.0" in value:
        # Only a v0.5.0 citation moves. A vector that cites anything else - the
        # v0.6.0 release already (for example through the FHR-Specification
        # alias), or a citation the checker refuses, such as raw main - keeps
        # it, so the twin tests the same claim; only the stated version moves.
        new_lines[i] = SCHEMA_PREFIX + quote + TWIN_SCHEMA_URL.encode() + quote + b"\n"
    new_lines[j] = re.sub(rb"(?<=['\"])1\.1(?=['\"])", b"1.2", old_version)
    if new_lines[j] == old_version:
        new_lines[j] = VERSION_PREFIX + quote + TWIN_SCHEMA_VERSION.encode() + quote + b"\n"
    if b"".join(new_lines) == data:
        raise Failure("twin rewrite changed no bytes; refusing a vacuous twin")
    body = b"".join(line for t, line in enumerate(new_lines) if t != k)
    if checksum_outcome == "verify":
        digest = base64.b64encode(
            hashlib.new("sha512_256", body).digest()).decode()
        new_lines[k] = CHECKSUM_PREFIX + digest.encode() + b"\n"
    elif checksum_outcome != "stale":
        raise Failure(f"unknown recorded checksum outcome {checksum_outcome!r}")
    # stale: the old stated digest stays byte-for-byte, so the twin remains a
    # stale-checksum case under the new identity.
    return b"".join(new_lines), "identity-rewrite", stated_schema_version(data)


# --- lanes ------------------------------------------------------------------

def generator_deps_available():
    """The generators import PyYAML and jsonschema through the pilot helpers."""
    import importlib.util

    return all(importlib.util.find_spec(name) for name in ("yaml", "jsonschema"))


def regenerate(vectors):
    """Rebuild every generated vector in a temporary tree and compare bytes."""
    wanted = {vector["id"]: vector for vector in vectors if vector["generator"] != "committed"}
    produced = {}
    if not wanted:
        return produced
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for kind in {vector["generator"] for vector in wanted.values()}:
            if kind == "embed_models":
                continue
            script = GENERATORS.get(kind)
            if script is None or not script.is_file():
                raise Failure(f"unknown generator {kind!r}")
            target = root / kind
            target.mkdir(parents=True, exist_ok=True)
            result = subprocess.run([sys.executable, str(script), str(target)],
                                    capture_output=True, text=True)
            if result.returncode:
                raise Failure(f"{kind} failed: {result.stderr.strip()[:400]}")
        if any(vector["generator"] == "embed_models" for vector in wanted.values()):
            derived = root / "embed_models" / S6K_DERIVED.name
            derived.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [sys.executable, str(EMBED), str(S6K_PROFILE), str(derived)],
                capture_output=True, text=True)
            if result.returncode:
                raise Failure(f"embed_models failed: {result.stderr.strip()[:400]}")
        for path in root.rglob("*.fhgff3.gff3"):
            produced.setdefault(path.name, path.read_bytes())
    for vector_id, vector in wanted.items():
        name = path_of(vector).name
        if name not in produced:
            raise Failure(f"{vector_id}: {vector['generator']} produced no {name}")
        produced[vector_id] = produced[name] == path_of(vector).read_bytes()
    return produced


class Lanes:
    """The released base schema of one lane and the optional GFF3 tool."""

    def __init__(self, base_schema, offline, gff3_tool):
        self.offline = offline
        self.gff3_tool = gff3_tool
        self.base_validator = None
        if not offline:
            import jsonschema

            self.base_validator = jsonschema.Draft202012Validator(
                json.loads(base_schema.read_bytes()),
                format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)

    def base(self, data):
        if self.offline:
            return "skipped", ""
        # The toolkit's strict reader, the same one the checker uses: it reads
        # only the leading header block (a later #~ line is an error, not more
        # header), refuses YAML-only line breaks and applies the FORMAT.md R12
        # scalar typing, where yaml.safe_load over every #~ line would not.
        from bioheaders import HEADER, header_text, load_yaml, sequence_parts

        try:
            header = load_yaml("\n".join(
                header_text(line, b"#~")
                for kind, line in sequence_parts([data], b"#~", gff3=True)
                if kind is HEADER))
        except Exception as error:  # noqa: BLE001 - any reader refusal is a base reject
            return "reject", f"header unreadable by the strict reader: {error}"
        errors = sorted(self.base_validator.iter_errors(header), key=str)
        if not errors:
            return "accept", ""
        error = errors[0]
        return "reject", f"{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"

    def gff3(self, data):
        if self.offline or not self.gff3_tool:
            return "skipped", ""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vector.fhgff3.gff3"
            path.write_bytes(data)
            result = subprocess.run([self.gff3_tool, "--no-header", str(path)],
                                    capture_output=True, text=True)
        text = (result.stdout + result.stderr).strip()
        return ("accept" if result.returncode == 0 else "reject"), text


def model_lane(vector, data, base_schemas):
    """The committed model-level checker over these exact bytes, every supplied base.

    The checker selects, per loaded file, the release that file's schema URL
    cites, so handing it every registered base is what lets a 1.2 carrier and
    its 1.1 predecessor each be judged by its own release.
    """
    with tempfile.TemporaryDirectory() as directory:
        current = Path(directory) / "current.fhgff3.gff3"
        current.write_bytes(data)
        evidence_file = Path(directory) / "evidence.json"
        command = [sys.executable, str(CHECKER), "--report-json", str(evidence_file)]
        for base_schema in base_schemas:
            command += ["--base-schema", str(base_schema)]
        for predecessor in predecessors_of(vector):
            command += ["--predecessor", str(predecessor)]
        command.append(str(current))
        result = subprocess.run(command, capture_output=True, text=True)
        try:
            evidence = json.loads(evidence_file.read_text())
        except (OSError, ValueError) as exc:
            raise Failure(f"checker produced no usable actual-evidence receipt: {exc}") from exc
        if result.returncode == 2:
            raise Failure(f"model execution prerequisite unusable: {evidence.get('reason')}")
    text = (result.stdout + result.stderr).strip()
    return ("pass" if result.returncode == 0 else "reject"), text, evidence


SELECTION_LINE = re.compile(
    r"Base selection: carrier cites schema .*? -> "
    r"(\S+)@(\S+) (\S+) \(sha256 ([0-9a-f]{16})")


def selected_base(model_text):
    """The checker's printed selection for the carrier (advisory report parse).

    This read-back feeds the verbose summary only; no gate depends on it - the
    recorded layer outcomes and reason substrings are the control.
    """
    match = SELECTION_LINE.search(model_text)
    return f"{match.group(2)} ({match.group(4)}...)" if match else "unknown"


# --- verification -----------------------------------------------------------

def check_vector(vector, lanes, base_schemas, data=None, recorded=None, expected_layers=None,
                 reason_expected=None):
    """Verify one vector (or one twin) and observe its layers.

    ``data`` is the bytes to evaluate; when omitted, the committed vector file.
    ``recorded`` is the digest record to match against (``vector["bytes"]`` plus
    a checksum line for sealed vectors, the matrix entry's ``twin`` object for
    twins); ``expected_layers``/``reason_expected`` default to the manifest's.
    """
    path = path_of(vector)
    if not path.is_file():
        raise Failure(f"{vector['id']}: missing vector file {vector['file']}")
    if data is None:
        data = path.read_bytes()
    if recorded is None:
        recorded = {**vector["bytes"], "checksum": vector["checksum"]}
    layers = expected_layers if expected_layers is not None else vector["layers"]
    problems = []

    if sha256(data) != recorded["sha256"]:
        problems.append(f"sha256 {sha256(data)} != recorded {recorded['sha256']}")
    if len(data) != recorded["size"]:
        problems.append(f"size {len(data)} != recorded {recorded['size']}")
    stated = stated_checksum(data)
    if stated != recorded["checksum"]:
        problems.append(f"checksum line {stated} != recorded {recorded['checksum']}")
    recomputed = recompute_checksum(data)
    outcome = layers["checksum"]
    if outcome == "verify":
        if recomputed != stated:
            problems.append(f"recorded as verifying, recomputed {recomputed} != stated {stated}")
    elif outcome == "stale":
        if recomputed == stated:
            problems.append("recorded as tampered, but the checksum line covers the bytes again")
    else:
        problems.append(f"unknown recorded checksum outcome {outcome!r}")

    if lanes.offline:
        return problems, None
    base, base_text = lanes.base(data)
    model, model_text, evidence = model_lane(vector, data, base_schemas)
    gff3, gff3_text = lanes.gff3(data)
    if layers["base"] is not None and base != layers["base"]:
        problems.append(f"base layer {base} ({base_text}) != recorded {layers['base']}")
    if layers["model"] is not None and model != layers["model"]:
        problems.append(f"model layer {model} != recorded {layers['model']}")
    expected = vector["expected"]
    reason = reason_expected if reason_expected is not None else vector.get("reason")
    if expected == "valid":
        if model != "pass":
            problems.append(f"expected valid, the checker rejected it: {model_text}")
    else:
        if model != "reject":
            problems.append("expected invalid, the checker accepted it")
        if reason and reason not in model_text:
            problems.append(f"recorded reason {reason!r} not in output: {model_text}")
    if gff3 != "skipped" and layers["gff3"] is not None and gff3 != layers["gff3"]:
        problems.append(f"GFF3 layer {gff3} != recorded {layers['gff3']}: {gff3_text}")
    actual_model = evidence["fullModel"]["status"]
    wanted_model = vector["evidenceExpectation"]["model"]
    if actual_model != wanted_model:
        problems.append(f"actual model evidence {actual_model} != expected {wanted_model}")
    gap = actual_model == "reject" and base == "accept" and recomputed == stated
    return problems, {"base": base, "model": model, "gff3": gff3, "gap": gap,
                      "selected": selected_base(model_text), "evidence": evidence}


# --- sealing -----------------------------------------------------------------

def seal(manifest):
    """Re-record the mechanical fields; expectations are never rewritten."""
    for vector in manifest["vectors"]:
        data = path_of(vector).read_bytes()
        vector["bytes"] = {"size": len(data), "sha256": sha256(data)}
        vector["checksum"] = stated_checksum(data)
    return json.dumps(manifest, indent=2) + "\n"


def seal_matrix(matrix, observations):
    """Re-record twin digests and observed layers; ids, methods and notes stand."""
    by_id = {entry["id"]: entry for entry in matrix["vectors"]}
    for vector_id, observation in observations.items():
        entry = by_id[vector_id]
        entry["twin"] = observation["twin"]
        entry["layers"] = observation["layers"]
        if observation.get("reason"):
            entry["reason"] = observation["reason"]
        entry["selectedBase"] = observation["selected"]
        entry["sameAsSealed"] = observation["sameAsSealed"]
        entry.pop("unobserved", None)
    valid = sum(1 for o in observations.values() if not o.get("invalid"))
    changed = sorted(v for v, o in observations.items() if not o["sameAsSealed"])
    matrix["summary"] = {
        "twins": len(observations),
        "valid": valid,
        "invalid": len(observations) - valid,
        "identityRewritten": sum(1 for o in observations.values()
                                 if o["method"] == "identity-rewrite"),
        "asCommitted10": sum(1 for o in observations.values()
                             if o["method"] == "as-committed-1-0"),
        "verdictChangesAgainstSealed": len(changed),
        "changedVectors": changed,
        "gapProofUnder12": sum(1 for o in observations.values() if o.get("gap")),
    }
    return json.dumps(matrix, indent=2) + "\n"


def skeleton_matrix(manifest):
    """Bootstrap base_matrix.json from the manifest: structure only, no claims.

    Entries carry the vector's identity, polarity, cited rules and derivation
    method. They hold no layers, digests or reasons until ``--seal-matrix``
    records them from an observed run; ``unobserved: true`` marks that state so
    nothing can read a placeholder as an expectation.
    """
    entries = []
    for vector in manifest["vectors"]:
        data = path_of(vector).read_bytes()
        method = twin_bytes(data, vector["layers"]["checksum"])[1]
        entry = {
            "id": vector["id"],
            "file": vector["file"],
            "method": method,
            "expected": vector["expected"],
            "unobserved": True,
            "note": ("its stated FHGFF3 1.0 identity is the defect, so the 1.2 lane "
                     "evaluates the committed bytes against the v0.6.0 base"
                     if method == "as-committed-1-0"
                     else "identity lines rewritten to the v0.6.0 citation, checksum "
                          "recomputed; every other byte and the supplied history are the "
                          "sealed vector's"),
        }
        if "rule" in vector:
            entry["rule"] = vector["rule"]
        else:
            entry["rules"] = vector["rules"]
        if vector.get("sharedRules"):
            entry["sharedRules"] = vector["sharedRules"]
        entries.append(entry)
    return {
        "matrixVersion": 1,
        "status": ("Draft FHGM base matrix: every sealed manifest vector re-observed against "
                   "the released FHGFF3 1.2 (v0.6.0) base bytes. FHGM has no released "
                   "contract, no schemaVersion, no schema URL and no schemas/versions.json "
                   "entry, and selection rule V7 keeps it that way; this file publishes, "
                   "adopts and claims nothing. Every outcome recorded below is an "
                   "observation of development/model/validate_fhgm.py run over a twin "
                   "derived from the committed vector bytes, re-verified by "
                   "run_conformance.py --matrix."),
        "decision": ("maintainer decision 2026-11-15: FHGM supports both released FHGFF3 "
                     "bases; the sealed 1.1 lane in manifest.json keeps its bytes, "
                     "expectations and evidence trail unchanged and this lane adds the 1.2 "
                     "observation alongside it."),
        "specification": "../model/README.md",
        "manifest": "manifest.json",
        "base": "provenance.json matrixBaseSchema records the v0.6.0 bytes; base-schemas.json "
                "registers them for the checker.",
        "method": ("A twin replaces exactly two header lines of its sealed vector - "
                   "a v0.5.0 #~schema citation moves to "
                   "https://w3id.org/fair-bioheaders/fhgff3/v0.6.0 (any other citation, "
                   "such as the v0.6.0 FHR-Specification alias or raw main, is kept) and "
                   "#~schemaVersion to "
                   "1.2, both in the source's quoting style - and the #~checksum line "
                   "follows: recomputed when the sealed record says verify, preserved when "
                   "it says stale so the twin remains a stale-checksum case. Records, "
                   "pointers and every feature byte are unchanged. A vector declaring "
                   "FHGFF3 1.0 is evaluated as committed (method as-committed-1-0): its "
                   "stated identity is the defect and there is no 1.2 form of the claim "
                   "being tested. The checker is handed both registered base files and the "
                   "same committed predecessors as the sealed lane, and selects the "
                   "release each loaded file cites by its schema URL: a 1.2 twin is judged "
                   "by the v0.6.0 bytes and its 1.1 predecessor by the v0.5.0 bytes it "
                   "cites, which makes the lane a mixed-identity chain test. The base "
                   "layer is the v0.6.0 release alone."),
        "summary": {},
        "findings": [],
        "vectors": entries,
    }


# --- census -----------------------------------------------------------------

def census(results, manifest):
    buckets = {rule: {"valid": 0, "invalid": 0, "skipped": 0}
               for rule in manifest["rules"]}
    for result in results:
        for rule in result["cited"]:
            bucket = buckets.setdefault(rule, {"valid": 0, "invalid": 0, "skipped": 0})
            if result["model"] == "skipped":
                bucket["skipped"] += 1
            elif result["expected"] == "valid":
                bucket["valid"] += 1
            else:
                bucket["invalid"] += 1
    return buckets


def report(results, manifest, offline):
    rules = manifest["rules"]
    table = census(results, manifest)
    width = max(len(rule) for rule in rules)
    print("\nFocus-label census (labels, not predicate-evaluation counts)")
    print(f"{'rule':<{width}}  valid  invalid  skipped  covers")
    for rule, summary in rules.items():
        counts = table.get(rule, {"valid": 0, "invalid": 0, "skipped": 0})
        text = summary["summary"]
        if len(text) > 62:
            text = text[:59].rstrip() + "..."
        if summary.get("shared"):
            text = "[shared rule] " + text
        print(f"{rule:<{width}}  {counts['valid']:>5}  {counts['invalid']:>7}  "
              f"{counts['skipped']:>7}  {text}")
    print(f"\n{'open scope':<{width}}  valid  invalid  skipped  states no outcome")
    for rule, summary in manifest["openScope"].items():
        print(f"{rule:<{width}}  {0:>5}  {0:>7}  {0:>7}  {summary['summary'][:62]}")
    valid = sum(1 for result in results if result["expected"] == "valid")
    invalid = len(results) - valid
    rejected = [result for result in results if result["expected"] == "invalid"]
    gaps = [result["id"] for result in rejected if result.get("gap")]
    print(f"\nVectors: {len(results)} recorded ({valid} valid, {invalid} invalid)")
    if offline:
        print("Model lane offline: base, model and gff3 layers were not run.")
        return
    print(f"Gap-proof rejections (the released base schema and the exact-byte checksum "
          f"accept them and an earned model predicate rejects; GFF3 is separate): {len(gaps)}/{len(rejected)}")
    for result in rejected:
        if not result.get("gap"):
            print(f"  not gap-proof: {result['id']} "
                  f"(base={result['base']}, checksum={result['checksum']}, rule={result['rules'][0]})")
    if results and all(result["gff3"] == "skipped" for result in results):
        print("GFF3 feature lane: skipped for every vector (gff3-validate not supplied; it is "
              "a separate tool and no FHGM rule depends on it).")


def report_matrix(results, matrix):
    entries = {entry["id"]: entry for entry in matrix["vectors"]}
    valid = sum(1 for result in results if result["expected"] == "valid")
    invalid = len(results) - valid
    rejected = [result for result in results if result["expected"] == "invalid"]
    changed = sorted(entry["id"] for entry in matrix["vectors"]
                     if entry.get("sameAsSealed") is False)
    rewritten = sum(1 for entry in matrix["vectors"]
                    if entry["method"] == "identity-rewrite")
    gaps = [result["id"] for result in rejected
            if result.get("gap")
            and entries[result["id"]]["layers"]["base"] == "accept"
            and entries[result["id"]]["layers"]["checksum"] == "verify"]
    print(f"\nMatrix lane (FHGFF3 1.2 base, v0.6.0 bytes): {len(results)} twins "
          f"({valid} valid, {invalid} invalid); twin method: {rewritten} identity-rewrite, "
          f"{len(results) - rewritten} as-committed-1-0.")
    print(f"Verdict changes against the sealed 1.1 lane: {len(changed)}"
          + (f" - {', '.join(changed)}" if changed else " (every twin agrees with its "
             "sealed vector's layers and reason)"))
    print(f"Gap-proof rejections under the 1.2 base: {len(gaps)}/{len(rejected)}")
    for result in rejected:
        entry = entries[result["id"]]
        if entry["layers"]["base"] == "reject" or entry["layers"]["checksum"] == "stale":
            print(f"  not gap-proof: {result['id']} "
                  f"(base={entry['layers']['base']}, checksum={entry['layers']['checksum']})")


# --- structural validation ----------------------------------------------------

def manifest_problems(manifest):
    """Every structural claim the manifest makes, checked against this tree.

    Returns a list of human-readable problems; empty means the manifest is
    internally consistent and every byte it cites is present. Kept separate from
    ``main`` so ``tests/test_fhgm_conformance.py`` can feed it broken manifests
    and assert that each defect is caught.
    """
    problems = []
    for rule in (f"K{number}" for number in range(1, 7)):
        if not manifest.get('ruleRequirements', {}).get(rule):
            problems.append(f"{rule}: missing rule input requirements")
    if not manifest.get('fullModelRequirements'):
        problems.append("missing full model prerequisite declaration")
    vectors = manifest["vectors"]
    ids = [vector["id"] for vector in vectors]
    if len(set(ids)) != len(ids):
        problems.append("duplicate vector id in manifest")
    for vector in vectors:
        rendered = json.dumps(vector).lower()
        for marker in ("requires independent review", "observed outputs", "candidate-unreviewed"):
            if marker in rendered:
                problems.append(f"{vector['id']}: active vector carries pending review marker {marker!r}")
        if vector['id'].startswith('dmel-') or vector.get('reviewRequired'):
            review = vector.get('expectationReview', {})
            if (review.get('status') != 'accepted'
                    or not all(review.get(key) for key in
                               ('reader', 'author', 'derivation', 'clause', 'disposition', 'date'))
                    or review.get('reader') == review.get('author')):
                problems.append(f"{vector['id']}: missing independent accepted expectation record")
        if vector.get('evidenceExpectation', {}).get('model') not in ('pass', 'reject', 'not-run'):
            problems.append(f"{vector['id']}: invalid or missing fullModel evidence expectation")
        if not VECTOR_ID.match(vector["id"]):
            problems.append(f"vector id {vector['id']!r} is not kebab-case")
        if not path_of(vector).is_file():
            problems.append(f"{vector['id']}: missing vector file {vector['file']}")
        elif vector["file"].startswith("vectors/") \
                and path_of(vector).name != f"{vector['id']}.fhgff3.gff3":
            # Vectors this suite generates are named by their id. Vectors citing bytes
            # already published under ../examples/ keep those file names and map them to
            # a stable manifest id instead: renaming committed fixture bytes would break
            # the documentation that already cites them, and one snapshot may appear as
            # several vectors under different supplied histories.
            problems.append(f"{vector['id']}: file {vector['file']!r} is not named for the id")
        for rule in ([vector["rule"]] if "rule" in vector else vector.get("rules", [])):
            if rule not in manifest["rules"]:
                problems.append(f"{vector['id']}: cites unknown rule {rule}")
            elif rule in manifest.get("openScope", {}):
                problems.append(f"{vector['id']}: cites open scope {rule} as a rule")
        if (vector["expected"] == "valid") != ("rules" in vector):
            problems.append(f"{vector['id']}: valid vectors cite rules, invalid vectors one rule")
        if (vector["expected"] == "invalid") != ("reason" in vector):
            problems.append(f"{vector['id']}: only invalid vectors record a reason")
        for rule in vector.get("sharedRules", []):
            if rule not in manifest["rules"] or not manifest["rules"][rule].get("shared"):
                problems.append(f"{vector['id']}: cites {rule} as a shared rule but the manifest "
                                "does not record it as one")
        files = {other["file"] for other in vectors}
        for predecessor in predecessors_of(vector):
            relative = vector_relative_file(manifest, predecessor)
            if not predecessor.is_file():
                problems.append(f"{vector['id']}: missing predecessor {predecessor.name}")
            elif relative not in files:
                problems.append(f"{vector['id']}: predecessor {predecessor.name} is not a vector")
            elif relative == vector["file"]:
                problems.append(f"{vector['id']}: a vector cannot be its own predecessor")
    return problems


def vector_relative_file(manifest, absolute):
    for vector in manifest["vectors"]:
        if path_of(vector) == absolute:
            return vector["file"]
    return None


def matrix_problems(matrix, manifest, sealing=False):
    """Structural checks on the matrix record, mirroring manifest_problems.

    The matrix must cover every manifest vector exactly once, record a legal
    twin method and layer set, keep the sealed vector's expected polarity, and
    be honest about agreement: sameAsSealed may only be true when the recorded
    layers and reason equal the sealed vector's. While ``--seal-matrix`` is
    recording the first observation, unobserved entries are tolerated.
    """
    problems = []
    sealed = {vector["id"]: vector for vector in manifest["vectors"]}
    entries = matrix["vectors"]
    ids = [entry["id"] for entry in entries]
    if len(set(ids)) != len(ids):
        problems.append("duplicate vector id in matrix")
    if set(ids) != set(sealed):
        missing = sorted(set(sealed) - set(ids))
        extra = sorted(set(ids) - set(sealed))
        if missing:
            problems.append(f"matrix is missing twins for: {', '.join(missing)}")
        if extra:
            problems.append(f"matrix holds twins for no sealed vector: {', '.join(extra)}")
    for entry in entries:
        vector = sealed.get(entry["id"])
        if vector is None:
            continue
        if entry["method"] not in ("identity-rewrite", "as-committed-1-0"):
            problems.append(f"{entry['id']}: unknown twin method {entry['method']!r}")
        elif entry["method"] == "as-committed-1-0" and vector["layers"]["base"] != "reject":
            problems.append(f"{entry['id']}: a 1.0 twin must be the vector the base rejects")
        if (entry["expected"] == "valid") == ("rule" in entry):
            problems.append(f"{entry['id']}: invalid twins cite one rule, valid twins a list")
        if (entry["expected"] == "invalid") != ("reason" in entry) and not entry.get("unobserved"):
            problems.append(f"{entry['id']}: only invalid twins record a reason")
        if entry["expected"] != vector["expected"]:
            problems.append(f"{entry['id']}: expected polarity {entry['expected']!r} != sealed "
                            f"{vector['expected']!r}; the twin lane re-observes verdicts, it "
                            "does not re-litigate validity")
        if entry.get("unobserved"):
            if not sealing:
                problems.append(f"{entry['id']}: matrix entry is unobserved; run "
                                "--seal-matrix against a clean run to record it")
            continue
        for layer in ("base", "checksum", "gff3", "model"):
            if layer not in entry["layers"]:
                problems.append(f"{entry['id']}: layers missing {layer}")
        for field in ("size", "sha256", "checksum"):
            if not entry.get("twin", {}).get(field):
                problems.append(f"{entry['id']}: twin record missing {field}")
        agrees = (entry["layers"] == vector["layers"]
                  and entry.get("reason") == vector.get("reason"))
        if bool(entry.get("sameAsSealed")) != agrees:
            problems.append(f"{entry['id']}: sameAsSealed={entry.get('sameAsSealed')!r} "
                            "contradicts the recorded layers/reason against the sealed vector")
    return problems


def verify_twins(matrix, manifest):
    """Re-derive every sealed twin from the committed bytes and compare digests."""
    problems = []
    sealed = {vector["id"]: vector for vector in manifest["vectors"]}
    for entry in matrix["vectors"]:
        if entry.get("unobserved"):
            continue
        vector = sealed[entry["id"]]
        data = path_of(vector).read_bytes()
        derived, method, _ = twin_bytes(data, vector["layers"]["checksum"])
        if method != entry["method"]:
            problems.append(f"{entry['id']}: re-derived method {method!r} != recorded "
                            f"{entry['method']!r}")
        if sha256(derived) != entry["twin"]["sha256"]:
            problems.append(f"{entry['id']}: re-derived twin sha256 {sha256(derived)} != "
                            f"recorded {entry['twin']['sha256']}")
        if len(derived) != entry["twin"]["size"]:
            problems.append(f"{entry['id']}: re-derived twin size {len(derived)} != "
                            f"recorded {entry['twin']['size']}")
        if stated_checksum(derived) != entry["twin"]["checksum"]:
            problems.append(f"{entry['id']}: re-derived twin checksum line "
                            f"{stated_checksum(derived)} != recorded {entry['twin']['checksum']}")
    return problems


# --- per-lane driver -----------------------------------------------------------

def run_lane(vectors, matrix_entries, lanes, base_paths, offline, verbose, lane):
    """Check every vector (sealed bytes) or twin (matrix lane); return results."""
    results = []
    failed = []
    for vector in vectors:
        entry = matrix_entries.get(vector["id"]) if lane == "matrix" else None
        if lane == "matrix":
            data = twin_bytes(path_of(vector).read_bytes(),
                              vector["layers"]["checksum"])[0]
            if entry.get("unobserved"):
                # Bootstrap: the seal run records digests and observes layers;
                # there is nothing recorded to compare against yet. The layer
                # checks below are skipped by passing None; the checksum layer
                # is policy-stated (preserve the sealed record's) and verified.
                recorded = {"size": len(data), "sha256": sha256(data),
                            "checksum": stated_checksum(data)}
                layers_expected = {"base": None,
                                   "checksum": vector["layers"]["checksum"],
                                   "gff3": None, "model": None}
                reason_expected = vector.get("reason")
            else:
                recorded = dict(entry["twin"])
                layers_expected = entry["layers"]
                reason_expected = entry.get("reason")
        else:
            data = None
            recorded = None
            layers_expected = None
            reason_expected = None
        problems, outcome = check_vector(vector, lanes, base_paths, data=data,
                                         recorded=recorded,
                                         expected_layers=layers_expected,
                                         reason_expected=reason_expected)
        result = {
            "id": vector["id"],
            "expected": vector["expected"],
            "rules": [vector["rule"]] if "rule" in vector else vector["rules"],
            "cited": ([vector["rule"]] if "rule" in vector else vector["rules"])
            + vector.get("sharedRules", []),
            "checksum": (layers_expected or vector["layers"])["checksum"],
            "model": "skipped" if offline else outcome["model"],
            "base": "skipped" if offline else outcome["base"],
            "gff3": "skipped" if offline else outcome["gff3"],
            "gap": None if offline else outcome["gap"],
            "selected": None if offline else outcome["selected"],
            "actualEvidence": None if offline else outcome["evidence"],
            "matched": not problems,
        }
        if lane == "matrix":
            result["method"] = entry["method"]
            result["sameAsSealed"] = entry.get("sameAsSealed")
        results.append(result)
        if problems:
            failed.append(vector["id"])
            print(f"FAIL[{lane}] {vector['id']}")
            for problem in problems:
                print(f"     {problem}")
        elif verbose:
            shown = data if data is not None else path_of(vector).read_bytes()
            print(f"ok[{lane:>6}] {vector['id']:<40} base={result['base']} "
                  f"checksum={result['checksum']} gff3={result['gff3']} "
                  f"model={result['model']} selected={result['selected']} "
                  f"bytes={sha256(shown)[:12]}")
    return results, failed


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-schema", type=Path, action="append", default=[],
                        help="bytes of a released fhgff3.json named in base-schemas.json; "
                             "repeat per base (every non-offline run needs both v0.5.0 and "
                             "v0.6.0)")
    parser.add_argument("--matrix", action="store_true",
                        help="also evaluate the FHGFF3 1.2 twins of every vector against "
                             "base_matrix.json expectations")
    parser.add_argument("--offline", action="store_true",
                        help="verify bytes, digests and checksums only (standard library)")
    parser.add_argument("--skip-regeneration", action="store_true",
                        help="do not re-run the generators and compare bytes")
    parser.add_argument("--gff3-validate", default=os.environ.get("GFF3_VALIDATE"),
                        help="optional gff3-validate executable for the feature lane")
    parser.add_argument("--seal", action="store_true",
                        help="re-record vector digests and checksums after a clean run")
    parser.add_argument("--seal-matrix", action="store_true",
                        help="bootstrap or re-record base_matrix.json from a clean matrix "
                             "run (implies --matrix)")
    parser.add_argument("--check-downstream-pins", action="store_true",
                        help="fetch the draft pins other repositories hold on our contract bytes "
                             "and report whether they are still fresh (network)")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--report-json", type=Path,
                        help="write separately counted actual layer/rule evidence")
    args = parser.parse_args()
    global REPORT_PATH
    REPORT_PATH = args.report_json
    if args.seal_matrix:
        args.matrix = True

    supplied = {}
    for path in args.base_schema:
        if not path.is_file():
            raise Failure(f"no base schema at {path}")
        supplied[sha256(path.read_bytes())] = path
    registry = load_registry()
    for digest, path in supplied.items():
        if digest not in registry:
            registered = ", ".join(sorted(r["ref"] for r in registry.values()))
            raise Failure(f"--base-schema {path} (sha256 {digest[:16]}...) is not a "
                          f"registered FHGFF3 base release; {REGISTRY.name} registers "
                          f"{registered}")

    manifest = json.loads(MANIFEST.read_text())
    provenance = json.loads(PROVENANCE.read_text())
    vectors = manifest["vectors"]
    matrix = json.loads(MATRIX.read_text()) if MATRIX.is_file() else None

    problems = verify_provenance(provenance, supplied)
    problems += manifest_problems(manifest)
    if matrix is not None:
        problems += matrix_problems(matrix, manifest, sealing=args.seal_matrix)
    if args.matrix and matrix is None and not args.seal_matrix and not args.offline:
        raise Failure(f"--matrix needs {MATRIX.name} (bootstrap it with --seal-matrix)")
    if problems:
        for problem in problems:
            print(f"record: {problem}")
        raise Failure("the recorded suite does not match this tree")

    sealed_base = provenance["baseSchema"]
    matrix_base = provenance["matrixBaseSchema"]
    if args.offline:
        print(f"Offline lane: provenance verified against this tree "
              f"({sealed_base['repository']}@{sealed_base['ref']} and "
              f"{matrix_base['repository']}@{matrix_base['ref']} base records cross-checked "
              "against base-schemas.json; base/model/GFF3 layers not run).")
    else:
        # Both lanes need both releases: vectors and their predecessors cite
        # either one, and the checker refuses a citation whose bytes it lacks.
        if sealed_base["sha256"] not in supplied or matrix_base["sha256"] not in supplied:
            raise Failure("a non-offline run requires both registered base releases - the "
                          "v0.5.0 bytes named by provenance.json baseSchema and the v0.6.0 "
                          "bytes named by matrixBaseSchema - because the checker selects the "
                          "release each loaded file cites")
        artifacts = len(provenance["contractArtifacts"]) + len(provenance["vectorGenerators"])
        print("Base schemas supplied: " + "; ".join(
            f"{registry[digest]['schemaVersion']} {registry[digest]['ref']} "
            f"(sha256 {digest[:16]}..., commit {registry[digest]['commit'][:8]})"
            for digest in sorted(supplied, key=lambda d: registry[d]["schemaVersion"])))
        print(f"Provenance verified for the base schemas, the registry and "
              f"{artifacts} recorded artifacts.")

    if args.check_downstream_pins:
        stale = check_downstream_pins(provenance)
        if stale:
            raise Failure("downstream pin prerequisites failed: " + "; ".join(stale))

    generated = sum(1 for vector in vectors if vector["generator"] != "committed")
    if args.skip_regeneration:
        print(f"Regeneration check skipped by request: {generated} generated vectors were "
              "compared against their recorded digests only.")
    elif not generator_deps_available():
        print(f"Regeneration check skipped: the generators import PyYAML and jsonschema, which "
              f"this interpreter does not have. {generated} generated vectors were compared "
              "against their recorded digests only.")
    else:
        reproduced = regenerate(vectors)
        bad = sorted(key for key, value in reproduced.items() if value is False)
        if bad:
            raise Failure(f"vectors are not byte-reproducible: {', '.join(bad)}")
        print(f"Regenerated {generated} generated vectors byte-for-byte "
              f"({len(vectors) - generated} committed by hand).")

    if matrix is not None and args.offline:
        twin_problems = verify_twins(matrix, manifest)
        if twin_problems:
            for problem in twin_problems:
                print(f"record: {problem}")
            raise Failure("the recorded matrix twins do not re-derive from the sealed bytes")
        print(f"Matrix integrity: {len(matrix['vectors'])} twins re-derived byte-for-byte "
              "from the sealed vectors; 1.2 base/model layers not run offline.")

    gff3_tool = args.gff3_validate or shutil.which("gff3-validate")
    if not args.offline and not gff3_tool:
        print("gff3-validate not found: the GFF3 feature lane reports skipped for every vector. "
              "It is a separate tool, and no FHGM rule depends on it.")

    if args.seal:
        if args.offline:
            raise Failure("--seal requires a non-offline run to verify layer outcomes")
        seal(manifest)

    sealed_lanes = Lanes(supplied.get(sealed_base["sha256"]), args.offline, gff3_tool)
    all_bases = [supplied[digest] for digest in sorted(supplied)]
    lane_results, lane_failed = run_lane(
        vectors, None, sealed_lanes, all_bases,
        args.offline, args.verbose, "sealed")
    results = list(lane_results)
    failed = list(lane_failed)

    matrix_results = []
    if args.matrix:
        matrix_lanes = Lanes(supplied.get(matrix_base["sha256"]), args.offline, gff3_tool)
        if matrix is None:
            matrix = skeleton_matrix(manifest)
        entries = {entry["id"]: entry for entry in matrix["vectors"]}
        matrix_results, matrix_failed = run_lane(
            vectors, entries, matrix_lanes, all_bases,
            args.offline, args.verbose, "matrix")
        results.extend(matrix_results)
        failed.extend(matrix_failed)

    if args.seal:
        if failed:
            raise Failure("refusing to seal while vectors mismatch")
        MANIFEST.write_text(seal(manifest))
        print(f"Sealed {MANIFEST.name}: vector sizes, sha256 digests and checksum lines "
              "re-recorded from the bytes on disk.")
    if args.seal_matrix:
        if args.offline:
            raise Failure("--seal-matrix requires a non-offline run to observe the layers")
        if failed:
            raise Failure("refusing to seal the matrix while vectors mismatch")
        sealed_by_id = {result["id"]: result for result in lane_results}
        observations = {}
        for vector, twin_result in zip(vectors, matrix_results):
            sealed_result = sealed_by_id[vector["id"]]
            derived = twin_bytes(path_of(vector).read_bytes(),
                                 vector["layers"]["checksum"])[0]
            if twin_result["gff3"] == "skipped":
                raise Failure("--seal-matrix requires gff3-validate to observe the feature layer")
            gff3_observed = twin_result["gff3"]
            observations[vector["id"]] = {
                "method": twin_result["method"],
                "invalid": vector["expected"] == "invalid",
                "gap": bool(twin_result["gap"]),
                "twin": {"size": len(derived), "sha256": sha256(derived),
                         "checksum": stated_checksum(derived)},
                "layers": {"base": twin_result["base"],
                           "checksum": vector["layers"]["checksum"],
                           "gff3": gff3_observed,
                           "model": twin_result["model"]},
                "reason": vector.get("reason"),
                "selected": twin_result["selected"],
                "sameAsSealed": (twin_result["base"] == sealed_result["base"]
                                 and twin_result["model"] == sealed_result["model"]),
            }
        MATRIX.write_text(seal_matrix(matrix, observations))
        print(f"Sealed {MATRIX.name}: twin digests, observed layers and agreement flags "
              "re-recorded from this run.")

    measured = [result for result in results if result["actualEvidence"] is not None]
    counts = {
        "vectorsVisited": len(results),
        "rulePredicatesEvaluated": sum(
            rule["status"] in ("pass", "reject")
            for result in measured
            for rule in result["actualEvidence"]["snapshots"][0]["rules"].values()),
        "layerExpectationsCompared": sum(
            3 + (result["gff3"] != "skipped") for result in measured),
        "completeVectorsMatched": sum(
            result["matched"] and result["gff3"] != "skipped"
            and result["actualEvidence"]["fullModel"]["status"] in ("pass", "reject")
            for result in measured),
        "completeModelPasses": sum(
            result["actualEvidence"]["fullModel"]["status"] == "pass"
            for result in measured),
    }
    if not args.offline:
        print("Actual evidence counts: " + "; ".join(f"{key}={value}" for key, value in counts.items()))
    if args.report_json:
        args.report_json.write_text(json.dumps({
            "evidenceVersion": 1, "status": "mismatch" if failed else "completed",
            "countScope": "vector visits across requested lanes; predicates are selected-carrier K1-K6 only, not repeated history validation",
            "counts": counts, "vectors": results,
        }, indent=2) + "\n")

    report(lane_results, manifest, args.offline)
    if args.matrix and matrix_results:
        report_matrix(matrix_results, matrix)
    if failed:
        print(f"\nFAILED {len(failed)} of {len(results)} checks: {', '.join(failed)}")
        return 1
    mode = "offline (bytes, digests and checksums only)" if args.offline \
        else "base, checksum, model and GFF3 layers as available"
    lanes_run = "sealed 1.1 and matrix 1.2" if args.matrix else "sealed 1.1"
    print(f"\nOK: {len(results)} vector checks matched their recorded outcomes "
          f"({lanes_run} lanes, {mode}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Failure, OSError, ImportError, json.JSONDecodeError) as failure:
        if REPORT_PATH is not None:
            REPORT_PATH.write_text(json.dumps({"evidenceVersion": 1,
                "status": "refused", "reason": str(failure)}, indent=2) + "\n")
        print(f"run_conformance: {failure}", file=sys.stderr)
        raise SystemExit(2)
