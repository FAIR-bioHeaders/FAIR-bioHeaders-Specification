# SPDX-License-Identifier: MPL-2.0
"""Exercise the draft FHGM K-rules against the real Drosophila locus fixtures.

This is an EXAMPLE-LANE demonstration, not a conformance-vector runner: the
normative census lives in ``development/conformance/`` and this directory
emits no vectors itself (it ran there while the census was 31; the
2026-11-15 draft promotion added the 12 ``dmel-*`` cases derived from the
measurements below, now 43 in total). It answers one question with output:
which model-level rules does a real annotated gene model actually exercise,
and would a neutered checker accept what the real checker rejects?

Each mutation below changes ONLY header content; every mutant file gets a
fresh correct exact-byte checksum from the released toolkit, so a rejection
attributed to K3-K6 cannot be a checksum or transport artifact. For each
mutant the script reports four layers separately:

- ``base``    - the released FHGFF3 schema alone, chosen per file by the
                base-selection rule (v0.5.0 bytes for 1.1 carriers, v0.6.0
                bytes for 1.2 carriers), over the parsed header;
- ``verify``  - ``bioheaders verify`` (schema + exact-byte checksum);
- ``gff3``    - ``gff3-validate --no-header`` when the CLI is available;
- ``model``   - ``validate_fhgm.py``: base selection, transport overlay,
                record contract, rules K3-K6 and pointer verdicts.

Since the maintainer dual-base decision of 2026-11-15 the 1.2 identity is a
carrier the draft admits, not a rejection case: the FHGFF3-1.2 mutant is a
positive transport case, and every gap-proof K-rule rejection is re-run under
1.2 identity (fresh toolkit-recomputed checksum, same records) to show the
model layer's verdicts and reasons do not move between released bases.

The neutered-checker controls copy ``validate_fhgm.py`` to a scratch tree,
replace exactly one guard with a disabled form (the script asserts the old
text occurs exactly once and the bytes changed, so a silent no-op cannot
fake the result), and re-run the mutant that the real checker rejected. A
mutant that the neutered checker accepts proves the rejection came from that
rule and nothing else. Each neuter also runs against a different rejected
mutant as a cross-control: the neutered checker must still reject it.

Usage (from the repository root, with fair-bioheaders, jsonschema and
optionally gff3-validator installed)::

    python3 development/examples/dmel4/exercise_rules.py \
        --base-schema /path/to/fhgff3-v0.5.0.json \
        --base-schema /path/to/fhgff3-v0.6.0.json [--gff3-validate CLI]

FHGM is a draft; nothing here publishes or adopts anything, and no mutant
file is a conformance vector.
"""

import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent.parent / "model"))

from bioheaders import HEADER, header_text, load_yaml, sequence_parts  # noqa: E402
from validate_fhgm import choose_base, load_bases, parse_snapshot  # noqa: E402

V1 = HERE / "Dmel_CG11076-Mpv17.snapshot-v1.fhgff3.gff3"
V2 = HERE / "Dmel_CG11076-Mpv17.snapshot-v2.fhgff3.gff3"
PAYLOAD = HERE / "Dmel_CG11076-Mpv17.payload.gff3"
CHECKER = ROOT / "development" / "model" / "validate_fhgm.py"

# One real wrong-parent digest to drive the K5 contradiction half: the
# exact-byte checksum recorded by the merged S6k example fixture, i.e. a
# genuine FHGFF3 file digest that is simply NOT the parent of this file.
S6K_CHECKSUM = "krWpdzrhfx1SE7SYJlzxMCXiHg64ujNO6L26SF5asZ8="


def parse_header(data):
    lines = [
        header_text(line, b"#~")
        for kind, line in sequence_parts([data], b"#~", gff3=True)
        if kind is HEADER
    ]
    return load_yaml("\n".join(lines))


def combine(toolkit, metadata, output):
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
        json.dump(metadata, handle)
        meta_path = Path(handle.name)
    subprocess.run(
        [str(toolkit), "combine", str(meta_path), str(PAYLOAD), "-o", str(output)],
        check=True,
    )
    meta_path.unlink()


def mutate(toolkit, workdir, name, edit, base_file=V1, identity=None):
    """Parse a committed fixture header, apply one edit, recombine with the
    toolkit so the checksum is correct by construction.

    ``identity=(schema URI, schemaVersion)`` additionally moves the released
    file identity - this is how the FHGFF3 1.2 twins are built: same records,
    same feature bytes, a fresh correct checksum over the new identity.
    """
    metadata = parse_header(base_file.read_bytes())
    metadata.pop("checksum")
    edit(metadata)
    if identity is not None:
        metadata["schema"], metadata["schemaVersion"] = identity
    path = workdir / name
    combine(toolkit, metadata, path)
    return path


# --------------------------------------------------------------------------
# mutations: each is one plausible producer error ON REAL DATA
# --------------------------------------------------------------------------

def record(metadata, model_id):
    for item in metadata["x-fhgm-models"]:
        if item["modelId"] == model_id:
            return item
    raise KeyError(model_id)


CG = "gene-Dmel_CG11076"
MP = "gene-Dmel_CG11077"


def edit_numeric_version(metadata):
    record(metadata, CG)["modelVersion"] = 2  # YAML int, not the string "2"


def edit_duplicate_model(metadata):
    metadata["x-fhgm-models"].append(copy.deepcopy(record(metadata, MP)))


def edit_target_transcript(metadata):
    record(metadata, MP)["featureId"] = "rna-NM_143687.4"  # a real mRNA row


def edit_target_absent(metadata):
    record(metadata, CG)["featureId"] = "gene-Dmel_absentFromThisFile"


def edit_reference_contradicts(metadata):
    record(metadata, MP)["reference"] = {"annotates": S6K_CHECKSUM}


def edit_reference_not_comparable(metadata):
    del metadata["genomeReference"]  # file keeps only the derivedFrom link;
    # the CG record keeps only genomeReference -> no shared comparable form


def edit_pointer_names_neighbor(metadata):
    record(metadata, CG)["predecessor"]["modelId"] = MP


def edit_pointer_reuses_version(metadata):
    item = record(metadata, CG)
    item["modelVersion"] = "1"  # successor version identical to predecessor


def edit_empty_models(metadata):
    metadata["x-fhgm-models"] = []


def edit_fhgff3_12(metadata):
    metadata["schema"] = "https://w3id.org/fair-bioheaders/fhgff3/v0.6.0"
    metadata["schemaVersion"] = "1.2"


# --------------------------------------------------------------------------
# layer probes
# --------------------------------------------------------------------------

def layer_base(candidates, path):
    """The released base schema ALONE, chosen by the carrier's cited schema URL."""
    try:
        header = parse_header(path.read_bytes())
        _, _, validator, _ = choose_base(header, candidates)
        validator.validate(header)
        return "accept"
    except Exception as exc:  # jsonschema.ValidationError and parse failures
        return f"reject ({type(exc).__name__})"


def layer_verify(toolkit, path):
    result = subprocess.run(
        [str(toolkit), "verify", str(path)], capture_output=True, text=True, check=False
    )
    return "verify" if result.returncode == 0 else "stale"


def layer_gff3(gff3_validate, path):
    if gff3_validate is None:
        return "skipped"
    result = subprocess.run(
        [str(gff3_validate), "--no-header", str(path)], capture_output=True, text=True, check=False
    )
    return "accept" if result.returncode == 0 else "reject"


def layer_model(base_paths, path, predecessors=()):
    argv = [sys.executable, str(CHECKER)]
    for base_path in base_paths:
        argv += ["--base-schema", str(base_path)]
    for prior in predecessors:
        argv += ["--predecessor", str(prior)]
    argv.append(str(path))
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return "pass", ""
    reason = (result.stderr or result.stdout).strip().splitlines()
    return "reject", reason[-1] if reason else ""


# --------------------------------------------------------------------------
# neutered-checker controls
# --------------------------------------------------------------------------

NEUTERS = {
    # id: (label, exact old text, replacement,
    #      (primary mutant that must now pass, its predecessors),
    #      (cross-control mutant that must still be rejected, its predecessors))
    "N-K4": (
        "K4 root gene-row target check disabled (every featureId resolves to one root gene row)",
        "        rows = targets.get(feature_id.encode(), [])\n",
        '        rows = [(b"gene", False)]\n',
        ("mutant-k4-target-transcript", ()),
        ("mutant-k5-contradicts", ()),
    ),
    "N-K3": (
        "K3 duplicate-modelId rejection disabled",
        "    for key, records in models.items():\n        if len(records) > 1:\n",
        "    for key, records in models.items():\n        if False:\n",
        ("mutant-k3-duplicate-modelid", ()),
        ("mutant-k4-target-transcript", ()),
    ),
    "N-K5": (
        "K5 contradiction test disabled at the function (links_conflict always False)",
        "def links_conflict(left, right):\n"
        "    return any(left[key] != right[key] for key in left.keys() & right.keys())\n",
        "def links_conflict(left, right):\n    return False\n",
        ("mutant-k5-contradicts", ()),
        ("mutant-k5-not-comparable", ()),
    ),
    "N-K6": (
        "K6 own-modelId (deviation D2) check disabled",
        '    if pointer["modelId"] != model_id:\n',
        "    if False:\n",
        ("mutant-k6-neighbor-pointer", (str(V1),)),
        ("mutant-k3-duplicate-modelid", ()),
    ),
}


def build_neutered(checker_text, neuter_id, outdir):
    _label, old, new, *_ = NEUTERS[neuter_id]
    occurrences = checker_text.count(old)
    if occurrences != 1:
        raise SystemExit(
            f"{neuter_id}: expected the old guard text exactly once in "
            f"validate_fhgm.py, found {occurrences}; refusing a vacuous control"
        )
    patched = checker_text.replace(old, new)
    if patched == checker_text:
        raise SystemExit(f"{neuter_id}: patch did not change the bytes")
    script = outdir / f"{neuter_id}-validate_fhgm.py"
    script.write_text(patched)
    for schema in ("fhgm-draft.schema.json", "fhgm-model.schema.json",
                   "base-schemas.json"):
        shutil.copyfile(CHECKER.with_name(schema), outdir / schema)
    return script


def run_script(script, base_paths, path, predecessors=()):
    argv = [sys.executable, str(script)]
    for base_path in base_paths:
        argv += ["--base-schema", str(base_path)]
    for prior in predecessors:
        argv += ["--predecessor", str(prior)]
    argv.append(str(path))
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-schema", type=Path, action="append", required=True,
                        help="released fhgff3.json bytes registered in base-schemas.json; "
                             "supply both v0.5.0 and v0.6.0 for the dual-base lane")
    parser.add_argument("--toolkit", default=None, help="bioheaders CLI path")
    parser.add_argument("--gff3-validate", default=None, help="gff3-validate CLI path")
    args = parser.parse_args()

    toolkit = args.toolkit or shutil.which("bioheaders")
    if toolkit is None:
        raise SystemExit("bioheaders CLI not found; pass --toolkit")
    gff3_validate = args.gff3_validate or shutil.which("gff3-validate")
    candidates = load_bases(args.base_schema)
    registered = {record["schemaVersion"] for _, record, _ in candidates}
    if not {"1.1", "1.2"} <= registered:
        raise SystemExit("the dual-base lane needs both registered releases supplied: "
                         "--base-schema v0.5.0 --base-schema v0.6.0 "
                         f"(got {sorted(registered)})")
    base_paths = list(args.base_schema)

    workdir = Path(tempfile.mkdtemp(prefix="fhgm-dmel4-exercise-"))
    try:
        mutants = {}

        def add(name, path, rule, predecessors=(), note=""):
            base = layer_base(candidates, path)
            verify = layer_verify(toolkit, path)
            gff3 = layer_gff3(gff3_validate, path)
            model, reason = layer_model(base_paths, path, predecessors)
            gap = (
                base == "accept"
                and verify == "verify"
                and gff3 == "accept"
                and model == "reject"
            )
            mutants[name] = {
                "path": path,
                "predecessors": tuple(str(prior) for prior in predecessors),
                "rule": rule,
                "base": base,
                "verify": verify,
                "gff3": gff3,
                "model": model,
                "reason": reason,
                "gap": gap,
                "note": note,
            }

        # Positive controls: the committed real fixtures pass every layer.
        add(
            "fixture-v1",
            V1,
            "K1-K6",
            note="two real gene models, both genome-link forms",
        )
        add(
            "fixture-v2-with-history",
            V2,
            "K6",
            predecessors=(V1,),
            note="real revision pointer resolved against snapshot v1",
        )
        add(
            "fixture-v2-without-history",
            V2,
            "K6",
            note="the same bytes are rejected when history is not supplied",
        )

        # Mutants: one producer error each, correct checksum by construction.
        add("mutant-k2-numeric-version",
            mutate(toolkit, workdir, "k2-numeric.fhgff3.gff3", edit_numeric_version), "K2")
        add("mutant-k3-duplicate-modelid",
            mutate(toolkit, workdir, "k3-dup.fhgff3.gff3", edit_duplicate_model), "K3")
        add("mutant-k4-target-transcript",
            mutate(toolkit, workdir, "k4-transcript.fhgff3.gff3", edit_target_transcript), "K4",
            note="featureId names the real transcript row rna-NM_143687.4")
        add("mutant-k4-target-absent",
            mutate(toolkit, workdir, "k4-absent.fhgff3.gff3", edit_target_absent), "K4")
        add("mutant-k5-contradicts",
            mutate(toolkit, workdir, "k5-contradict.fhgff3.gff3", edit_reference_contradicts), "K5",
            note="record binds the S6k example's real checksum: wrong parent, valid bytes")
        add("mutant-k5-not-comparable",
            mutate(toolkit, workdir, "k5-notcomparable.fhgff3.gff3", edit_reference_not_comparable),
            "K5", note="file derivedFrom-only; record genomeReference-only")
        add("mutant-k6-neighbor-pointer",
            mutate(toolkit, workdir, "k6-neighbor.fhgff3.gff3", edit_pointer_names_neighbor, V2),
            "K6", predecessors=(V1,), note="deviation D2 attack on real records")
        add("mutant-k6-version-reused",
            mutate(toolkit, workdir, "k6-reuse.fhgff3.gff3", edit_pointer_reuses_version, V2),
            "K6", predecessors=(V1,))
        add("mutant-k1-empty-models",
            mutate(toolkit, workdir, "k1-empty.fhgff3.gff3", edit_empty_models), "K1")
        add("mutant-transport-fhgff3-12",
            mutate(toolkit, workdir, "k12-version.fhgff3.gff3", edit_fhgff3_12), "K1",
            note="released v0.6.0 FHGFF3 1.2 identity carrying x-fhgm-models: a positive "
                 "transport case since the 2026-11-15 dual-base decision (the 1.1-only "
                 "harness rejected this at the base layer)")

        # B1: payload byte tamper, header (and its checksum) untouched.
        tampered = workdir / "b1-tamper.fhgff3.gff3"
        data = V1.read_bytes()
        needle = b"\tgene\t1029711\t1031757\t.\t-\t."
        if data.count(needle) != 1:
            raise SystemExit("B1 control: tamper target coordinate not unique in v1 bytes")
        tampered.write_bytes(data.replace(needle, b"\tgene\t1029711\t1031758\t.\t-\t."))
        add("tamper-payload-byte", tampered, "B1",
            note="one CDS end coordinate changed after the checksum was written")

        header = (
            "| case | rule | base | verify | gff3 | model | layer gap | note |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
        )
        rows = []
        for name, m in mutants.items():
            rows.append(
                f"| `{name}` | {m['rule']} | {m['base']} | {m['verify']} | {m['gff3']} | "
                f"{m['model']} | {'yes' if m['gap'] else 'no'} | {m['note']} |"
            )
        print(header + "\n".join(rows))
        print()
        for name, m in mutants.items():
            if m["reason"]:
                print(f"reason[{name}]: {m['reason']}")
        print()
        gaps = [n for n, m in mutants.items() if m["gap"]]
        print(f"gap-proof rejections (base accepts, checksum verifies, only the "
              f"model checker rejects): {len(gaps)}")
        for n in gaps:
            print(f"  - {n}")
        print()

        # Expectation gate: the table above is only evidence if the recorded
        # outcomes are the required ones. base/verify/gff3/model/gap per case;
        # "" model means pass.
        EXPECT = {
            "fixture-v1": ("accept", "verify", "accept", "pass", False),
            "fixture-v2-with-history": ("accept", "verify", "accept", "pass", False),
            "fixture-v2-without-history": ("accept", "verify", "accept", "reject", True),
            "mutant-k2-numeric-version": ("accept", "verify", "accept", "reject", True),
            "mutant-k3-duplicate-modelid": ("accept", "verify", "accept", "reject", True),
            "mutant-k4-target-transcript": ("accept", "verify", "accept", "reject", True),
            "mutant-k4-target-absent": ("accept", "verify", "accept", "reject", True),
            "mutant-k5-contradicts": ("accept", "verify", "accept", "reject", True),
            "mutant-k5-not-comparable": ("accept", "verify", "accept", "reject", True),
            "mutant-k6-neighbor-pointer": ("accept", "verify", "accept", "reject", True),
            "mutant-k6-version-reused": ("accept", "verify", "accept", "reject", True),
            "mutant-k1-empty-models": ("accept", "verify", "accept", "reject", True),
            "mutant-transport-fhgff3-12": ("accept", "verify", "accept", "pass", False),
            "tamper-payload-byte": ("accept", "stale", "accept", "reject", False),
        }
        problems = []
        if gff3_validate is not None:
            for name, (eb, ev, eg, em, egap) in EXPECT.items():
                m = mutants[name]
                if (m["base"], m["verify"], m["gff3"], m["model"], m["gap"]) != (
                        eb, ev, eg, em, egap):
                    problems.append(
                        f"{name}: got "
                        f"{(m['base'], m['verify'], m['gff3'], m['model'], m['gap'])}, "
                        f"expected {(eb, ev, eg, em, egap)}"
                    )
        else:
            print("gff3 lane unavailable: expectation gate skipped "
                  "(install gff3-validator to run it)")
        if problems:
            for p in problems:
                print(f"EXPECTATION MISMATCH: {p}")
            raise SystemExit("recorded layer outcomes did not match expectations")

        # Dual-base re-run: every gap-proof rejection, recombined under the
        # released FHGFF3 1.2 identity with a fresh toolkit checksum. Same
        # records, same feature bytes; only the two identity lines move.
        print("dual-base re-run of the gap-proof set (FHGFF3 1.2 identity):")
        identity_12 = ("https://w3id.org/fair-bioheaders/fhgff3/v0.6.0", "1.2")
        twin_moves = 0
        for name in gaps:
            source = mutants[name]["path"]
            twin_name = f"twin12-{name}"
            twin = mutate(toolkit, workdir, f"{twin_name}.fhgff3.gff3", lambda m: None,
                          base_file=source, identity=identity_12)
            # Predecessors stay the committed snapshots: a 1.2 carrier naming a
            # 1.1 predecessor is the mixed-identity chain real revision history
            # will contain after a base-line release bump.
            preds = tuple(Path(prior) for prior in mutants[name]["predecessors"])
            base = layer_base(candidates, twin)
            verify = layer_verify(toolkit, twin)
            model, reason = layer_model(base_paths, twin, predecessors=preds)
            real_reason = mutants[name]["reason"]
            agrees = (base == "accept" and verify == "verify" and model == "reject"
                      and (not real_reason or real_reason in reason))
            if not agrees:
                raise SystemExit(
                    f"{twin_name}: layer outcome ({base}, {verify}, {model}, {reason!r}) "
                    f"does not reproduce the sealed rejection "
                    f"({mutants[name]['base']}, {mutants[name]['verify']}, "
                    f"{mutants[name]['model']}, {mutants[name]['reason']!r})")
            twin_moves += 1
            print(f"  {twin_name}: base=accept verify=verify model=reject "
                  f"reason reproduced")
        print(f"  {twin_moves}/{len(gaps)} gap-proof rejections reproduce unchanged under "
              "the 1.2 base; the 1.2 mutant itself is admitted as a positive carrier "
              "(see mutant-transport-fhgff3-12 above).")
        print()

        # Neutered-checker controls.
        checker_text = CHECKER.read_text()
        print("neutered-checker controls:")
        failures = []
        for neuter_id, (label, _old, _new, (primary, primary_preds),
                        (control, control_preds)) in NEUTERS.items():
            script = build_neutered(checker_text, neuter_id, workdir)
            rc_real = run_script(
                CHECKER, base_paths, mutants[primary]["path"], primary_preds
            )
            rc_pass = run_script(
                script, base_paths, mutants[primary]["path"], primary_preds
            )
            rc_still = run_script(
                script, base_paths, mutants[control]["path"], control_preds
            )
            ok = rc_real != 0 and rc_pass == 0 and rc_still != 0
            if not ok:
                failures.append(neuter_id)
            print(
                f"  {neuter_id}: {label}\n"
                f"    {primary}: real checker rc={rc_real} (expected non-zero), "
                f"neutered rc={rc_pass} (expected 0)\n"
                f"    cross-control {control}: neutered rc={rc_still} "
                f"(expected non-zero) -> {'OK' if ok else 'FAILED'}"
            )
        if failures:
            raise SystemExit(f"neuter control did not behave as expected: {failures}")
        print()
        print("All model-rule mutants rejected by the real checker; every neuter "
              "flips exactly its own rejection and keeps the others.")
        return 0
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
