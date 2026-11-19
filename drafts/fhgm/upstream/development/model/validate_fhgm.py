# SPDX-License-Identifier: MPL-2.0
"""Model-level checker for the draft FHGM contract v0.1 on FHGFF3 1.1/1.2 files.

Runs three passes over an explicit selection: the released FHGFF3 base schema
(transport and file identity only), the draft transport overlay
(fhgm-draft.schema.json) and the native record contract (fhgm-model.schema.json)
per embedded record. Base selection, not base substitution: each loaded file
cites a released FHGFF3 schema URL, and the checker validates it against the
registered bytes of THAT release (base-schemas.json), refusing any file whose
cited release is unregistered or was not supplied. The selected base is printed for every loaded file, so each verdict
carries the release bytes that produced it. Pointer resolution then reports one
verdict per revision claim: resolvable, unresolvable or ambiguous. A resolvable
pointer only identifies a predecessor record; curator acceptance is never
asserted here. FHGM itself is a draft: it has no schemaVersion, no schema URL,
no registry row and no release form (selection rule V7).
"""

import argparse
from collections import defaultdict
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote_to_bytes, urlsplit

from bioheaders import HEADER, header_text, load_yaml, sequence_parts
from bioheaders.cli import checksum
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from yaml import YAMLError

BASE_REGISTRY = Path(__file__).with_name("base-schemas.json")
TRANSPORT = Path(__file__).with_name("fhgm-draft.schema.json")
MODEL_CONTRACT = Path(__file__).with_name("fhgm-model.schema.json")
MODELS = "x-fhgm-models"
RESOLVABLE = "resolvable"
UNRESOLVABLE = "unresolvable"
AMBIGUOUS = "ambiguous"

FORMAT_CHECKER = Draft202012Validator.FORMAT_CHECKER
if "uri" not in FORMAT_CHECKER.checkers:
    FORMAT_CHECKER = FormatChecker()

    @FORMAT_CHECKER.checks("uri")
    def is_uri(value):
        if not isinstance(value, str):
            return True
        if (
            re.search(r"\s", value)
            or re.search(r"%(?![0-9A-Fa-f]{2})", value)
            or any(ord(char) < 0x21 or ord(char) > 0x7E or char in '<>"{}|\\^`' for char in value)
        ):
            return False
        try:
            parts = urlsplit(value)
        except ValueError:
            return False
        return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*", parts.scheme))


class ModelCheckError(ValueError):
    """A draft FHGM model-level rule failed; the reason is the message."""


def _version_key(version):
    return tuple(int(part) for part in version.split("."))


def load_registry():
    """The registered FHGFF3 base releases, keyed by their exact-byte digest."""
    document = json.loads(BASE_REGISTRY.read_bytes())
    return {record["sha256"]: record for record in document["bases"]}


def load_bases(paths):
    """Resolve each supplied --base-schema file against the registry.

    Returns (digest, record, validator) triples oldest release first. Unknown
    bytes are refused: a checker run must say which registered release it
    evaluated.
    """
    registry = load_registry()
    candidates = []
    for path in paths:
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        record = registry.get(digest)
        if record is None:
            raise ValueError(
                f"{path}: sha256 {digest} is not a registered FHGFF3 base release; "
                f"{BASE_REGISTRY.name} registers "
                f"{', '.join(sorted({r['schemaVersion'] for r in registry.values()}))}")
        candidates.append((digest, record, Draft202012Validator(
            json.loads(data), format_checker=Draft202012Validator.FORMAT_CHECKER)))
    candidates.sort(key=lambda triple: _version_key(triple[1]["schemaVersion"]))
    return candidates


def choose_base(header, candidates, registry=None):
    """Pick the supplied base release the carrier's ``schema`` URL cites.

    Returns (digest, record, validator, basis). The cited URL is mapped to
    exactly one registered release through its ``schemaUrls``; schemaVersion
    plays no part in the choice and is judged afterwards by the selected bytes.
    The run is refused - never evaluated against other bytes - when the carrier
    states no schema URL, cites a release the registry does not hold (a
    superseded release, or raw main, which is not a release), or cites a
    registered release whose bytes were not supplied with --base-schema.
    """
    cited = header.get("schema") if isinstance(header, dict) else None
    if not isinstance(cited, str):
        raise ValueError(
            "The carrier states no schema URL, so no FHGFF3 base release can be selected; "
            "a carrier must cite the released fhgff3.json it follows")
    registry = load_registry() if registry is None else registry
    matches = [record for record in registry.values() if cited in record["schemaUrls"]]
    if len(matches) != 1:
        raise ValueError(
            f"The carrier cites schema {cited!r}, which no registered FHGFF3 base release "
            f"answers to; {BASE_REGISTRY.name} registers "
            f"{', '.join(sorted(record['ref'] for record in registry.values()))}")
    wanted = matches[0]
    for digest, record, validator in candidates:
        if digest == wanted["sha256"]:
            return digest, record, validator, f"the cited schema URL names {wanted['ref']}"
    raise ValueError(
        f"The carrier cites the FHGFF3 {wanted['ref']} release, whose bytes were not supplied; "
        f"pass that release's fhgff3.json with --base-schema (see {BASE_REGISTRY.name})")


def describe(record, digest):
    return (f"{record['repository']}@{record['ref']} {record['path']} "
            f"(sha256 {digest[:16]}...)")


def gene_targets(data):
    """Map each percent-decoded feature ID to (type, has-Parent) per row carrying it.

    Attribute keys are case-sensitive and never trimmed into a valid tag.
    Malformed ID syntax or whitespace-disguised ID/Parent tags prevent a
    trustworthy identity/root inventory. Bare/empty Parent remains present
    and therefore cannot establish an eligible root. Only decoded IDs resolve.
    """
    targets = defaultdict(list)
    for line in data.splitlines():
        if line == b"##FASTA":
            break
        if not line.strip() or line.startswith(b"#"):
            continue
        columns = line.split(b"\t")
        if len(columns) != 9:
            raise ValueError("Expected nine columns in each GFF3 feature row")
        identifiers = []
        has_parent = False
        for attribute in columns[8].split(b";"):
            key, separator, value = attribute.partition(b"=")
            if key != key.strip() and key.strip() in (b"ID", b"Parent"):
                raise ValueError("Untrustworthy feature inventory: whitespace in ID/Parent tag")
            if key == b"ID":
                if not separator or not value or identifiers or b"," in value:
                    raise ValueError("Untrustworthy feature inventory: malformed or duplicate ID attribute")
                identifiers.append(unquote_to_bytes(value))
            elif key == b"Parent":
                has_parent = True
        for identifier in identifiers:
            targets[identifier].append((columns[2], has_parent))
    return targets


def assembly_keys(header):
    keys = {}
    if "genomeReference" in header:
        reference = header["genomeReference"]
        keys["accession"] = reference["accession"]
        keys["seqcol_id"] = reference["seqcol_id"]
    for parent in header.get("derivedFrom", []):
        if parent["headerType"] == "FHR" and parent["relationship"] == "annotates":
            keys["fhr_checksum"] = parent["checksum"]
    return keys


def reference_keys(model):
    keys = {}
    reference = model.get("reference", {})
    if "genomeReference" in reference:
        keys["accession"] = reference["genomeReference"]["accession"]
        keys["seqcol_id"] = reference["genomeReference"]["seqcol_id"]
    if "annotates" in reference:
        keys["fhr_checksum"] = reference["annotates"]
    return keys


def links_conflict(left, right):
    return any(left[key] != right[key] for key in left.keys() & right.keys())


def links_match(left, right):
    return bool(left.keys() & right.keys()) and not links_conflict(left, right)


def parse_snapshot(data):
    """The header document of a snapshot's exact bytes, before any validation."""
    lines = [
        header_text(line, b"#~")
        for kind, line in sequence_parts([data], b"#~", gff3=True)
        if kind is HEADER
    ]
    return load_yaml("\n".join(lines))


def new_snapshot_evidence(label):
    """Actual evidence, separate from expected outcomes and process exit status."""
    return {
        "subject": label,
        "layers": {name: {"status": "not-run", "reason": "not evaluated"}
                   for name in ("base", "checksum", "model", "gff3")},
        "rules": {f"K{number}": {"status": "not-run", "reason": "prerequisite not met"}
                  for number in range(1, 7)},
    }


def earned(evidence, kind, key, action):
    """Record only the phase actually executed; later phases remain not-run."""
    try:
        value = action()
    except (ValueError, ValidationError, YAMLError) as exc:
        if evidence is not None:
            evidence[kind][key] = {"status": "reject", "reason": str(exc)}
        raise
    if evidence is not None:
        evidence[kind][key] = {"status": "pass", "reason": "predicate evaluated"}
    return value


def require_target(targets, model):
    """K4: complete empty inventories reject; unavailable ones cannot be scored."""
    if targets is None:
        raise ValueError("Feature inventory unavailable: K4 is not-run, not a pass")
    feature_id = model["featureId"]
    rows = targets.get(feature_id.encode(), [])
    if len(rows) != 1 or rows[0][0] not in (b"gene", b"SO:0000704"):
        raise ModelCheckError(
            f"Model {model['modelId']!r} must target one local gene row: {feature_id!r}"
        )
    if rows[0][1]:
        raise ModelCheckError(
            f"Model {model['modelId']!r} must target one local gene row: {feature_id!r} "
            "has a Parent attribute, so it is not a root gene row"
        )


def validate_snapshot(data, candidates, transport, record_contract, label="carrier",
                      evidence=None):
    def read_base():
        header = parse_snapshot(data)
        if not isinstance(header, dict):
            raise ValueError("FHGFF3 header metadata must be an object")
        digest, record, base, basis = choose_base(header, candidates)
        print(f"Base selection: {label} cites schema {header.get('schema')!r} "
              f"(schemaVersion {header.get('schemaVersion')!r}) -> "
              f"{describe(record, digest)} ({basis})")
        base.validate(header)
        return header

    header = earned(evidence, "layers", "base", read_base)
    earned(evidence, "rules", "K1", lambda: transport.validate(header))

    def verify_checksum():
        if checksum(BytesIO(data), "gff3") != header["checksum"]:
            raise ValueError("File checksum mismatch")

    earned(evidence, "layers", "checksum", verify_checksum)

    def record_shapes():
        for index, model in enumerate(header[MODELS]):
            try:
                record_contract.validate(model)
            except ValidationError as exc:
                raise ModelCheckError(
                    f"Model record {index} is invalid under draft contract v0.1: "
                    f"{exc.json_path}: {exc.message}"
                ) from exc

    earned(evidence, "rules", "K2", record_shapes)

    def unique_ids():
        groups = defaultdict(list)
        for model in header[MODELS]:
            groups[unicodedata.normalize("NFC", model["modelId"])].append(model)
        for records in groups.values():
            if len(records) > 1:
                spellings = sorted({record["modelId"] for record in records})
                detail = (f" ({len(spellings)} spellings equal under NFC normalisation)"
                          if len(spellings) > 1 else "")
                raise ModelCheckError(
                    f"Ambiguous model ID {spellings[0]!r}: {len(records)} records share it in "
                    f"one snapshot{detail}"
                )

    earned(evidence, "rules", "K3", unique_ids)
    # An unreadable/malformed feature inventory is not a negative K4 verdict.
    # It refuses the snapshot's model run; a trustworthy empty dictionary below
    # is different and is evaluated as zero matching rows (K4 rejection).
    try:
        targets = gene_targets(data)
    except ValueError as exc:
        if evidence is not None:
            evidence["rules"]["K4"] = {"status": "not-run", "reason":
                f"feature inventory untrustworthy: {exc}"}
        raise

    earned(evidence, "rules", "K4",
           lambda: [require_target(targets, model) for model in header[MODELS]])

    def references():
        file_keys = assembly_keys(header)
        for model in header[MODELS]:
            record_keys = reference_keys(model)
            if links_conflict(record_keys, file_keys):
                raise ModelCheckError(
                    f"Model {model['modelId']!r} carries a reference that contradicts "
                    "the file genome link"
                )
            if not links_match(record_keys, file_keys):
                raise ModelCheckError(
                    f"Model {model['modelId']!r} has no reference form comparable "
                    "with the file genome link"
                )

    earned(evidence, "rules", "K5", references)
    if evidence is not None:
        evidence["rules"]["K6"] = {"status": "not-run", "reason":
            "snapshot prerequisites passed; revision claims are evaluated on the selected file only"}
        evidence["layers"]["model"] = {"status": "partial", "reason":
            "K1-K5 evaluated; no full model pass until the selected file's K6 claims are checked"}
    return header, {model["modelId"]: model for model in header[MODELS]}


def resolve_predecessor(model_id, model, header, predecessors):
    """Return (verdict, detail) for one revision pointer. Never raises."""
    pointer = model["predecessor"]
    snapshot = pointer["annotationChecksum"]
    if snapshot == header["checksum"] or snapshot not in predecessors:
        return UNRESOLVABLE, "the predecessor snapshot is the current file or was not supplied"
    if pointer["modelId"] != model_id:
        return UNRESOLVABLE, f"the pointer names another model ID {pointer['modelId']!r}"
    prior_header, prior_models = predecessors[snapshot]
    prior = prior_models.get(model_id)
    if prior is None:
        return UNRESOLVABLE, f"the predecessor snapshot has no model {model_id!r}"
    if prior["modelVersion"] != pointer["modelVersion"]:
        return UNRESOLVABLE, (
            f"the predecessor records version {prior['modelVersion']!r}, "
            f"not {pointer['modelVersion']!r}"
        )
    if prior["modelVersion"] == model["modelVersion"]:
        return UNRESOLVABLE, "the revision reuses the predecessor model version"
    for other_checksum, (other_header, other_models) in predecessors.items():
        if other_checksum == snapshot:
            continue
        other = other_models.get(model_id)
        other_pointer = other.get("predecessor") if other else None
        if (
            other_pointer
            and other_pointer["annotationChecksum"] == snapshot
            and other_pointer["modelId"] == model_id
            and other_pointer["modelVersion"] == pointer["modelVersion"]
            and other["modelVersion"] != prior["modelVersion"]
            and links_match(assembly_keys(other_header), assembly_keys(prior_header))
            and links_match(reference_keys(other), reference_keys(prior))
        ):
            return UNRESOLVABLE, (
                "the pointed record already has a recorded successor "
                f"in supplied snapshot {other_checksum[:8]}..."
            )
    if not links_match(assembly_keys(header), assembly_keys(prior_header)):
        return UNRESOLVABLE, "no matching assembly link with the predecessor snapshot"
    if not links_match(reference_keys(model), reference_keys(prior)):
        return UNRESOLVABLE, "no matching record reference with the predecessor record"
    return RESOLVABLE, f"predecessor {snapshot[:8]}... version {pointer['modelVersion']!r}"


def validate_revisions(header, models, predecessors):
    for model_id, model in models.items():
        if "predecessor" not in model:
            print(f"model {model_id} version {model['modelVersion']!r}: no predecessor claim")
            continue
        verdict, detail = resolve_predecessor(model_id, model, header, predecessors)
        if verdict != RESOLVABLE:
            raise ModelCheckError(
                f"Model {model_id!r} predecessor is {verdict}: {detail}"
            )
        print(f"model {model_id} version {model['modelVersion']!r}: {verdict} ({detail})")


def evaluate(file, base_paths, prior_paths):
    """Return a receipt and process outcome without inventing unavailable evidence."""
    receipt = {"evidenceVersion": 1, "status": "refused", "snapshots": [],
               "fullModel": {"status": "not-run", "reason": "execution not completed"}}
    try:
        candidates = load_bases(base_paths)
        transport = Draft202012Validator(json.loads(TRANSPORT.read_bytes()))
        record_contract = Draft202012Validator(
            json.loads(MODEL_CONTRACT.read_bytes()), format_checker=FORMAT_CHECKER)
    except (OSError, ValueError, ValidationError) as exc:
        receipt["reason"] = f"unusable execution prerequisite: {exc}"
        return receipt, 2, str(exc)
    try:
        carrier = new_snapshot_evidence("carrier")
        receipt["snapshots"].append(carrier)
        header, models = validate_snapshot(file.read_bytes(), candidates, transport,
                                          record_contract, evidence=carrier)
        predecessors = {}
        for path in prior_paths:
            prior = new_snapshot_evidence(f"predecessor {path.name}")
            receipt["snapshots"].append(prior)
            snapshot = validate_snapshot(path.read_bytes(), candidates, transport,
                                         record_contract, label=prior["subject"], evidence=prior)
            predecessors[snapshot[0]["checksum"]] = snapshot
        earned(carrier, "rules", "K6",
               lambda: validate_revisions(header, models, predecessors))
    except (OSError, ValueError, ValidationError, YAMLError) as exc:
        receipt["status"] = "evaluated" if any(
            rule["status"] == "reject" for snap in receipt["snapshots"]
            for rule in snap["rules"].values()) else "refused"
        # A rejection earned on a predecessor is a failed K6 prerequisite for
        # the selected file, not evidence that its pointer was resolved.
        failed = next((snap for snap in receipt["snapshots"]
                       if any(r["status"] == "reject" for r in snap["rules"].values())), None)
        if failed is carrier:
            receipt["fullModel"] = {"status": "reject", "reason": str(exc)}
            carrier["layers"]["model"] = dict(receipt["fullModel"])
        else:
            receipt["fullModel"] = {"status": "not-run", "reason": str(exc)}
        receipt["reason"] = str(exc)
        return receipt, 1, str(exc)
    carrier["layers"]["model"] = {"status": "pass", "reason":
        "K1-K6 and relevant supplied-snapshot prerequisites evaluated"}
    receipt["status"] = "evaluated"
    receipt["fullModel"] = dict(carrier["layers"]["model"])
    return receipt, 0, f"Passed FHGFF3 header, checksum and draft FHGM checks for {len(models)} model(s)."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-schema", type=Path, action="append", required=True,
                        help="bytes of a released fhgff3.json named in base-schemas.json")
    parser.add_argument("--predecessor", type=Path, action="append", default=[])
    parser.add_argument("--report-json", type=Path,
                        help="write actual layers/per-rule evidence, including refusals")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    receipt, code, message = evaluate(args.file, args.base_schema, args.predecessor)
    if args.report_json:
        args.report_json.write_text(json.dumps(receipt, indent=2) + "\n")
    if code:
        parser.exit(code, message + "\n")
    print(message)


if __name__ == "__main__":
    main()
