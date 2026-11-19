"""Run the FHT #8 suite against an *installed* fair-bioheaders draft lane.

Installed-artifact lane for issue #8 box 7 ("run the shared example/model/drift/conformance
checks with the named toolkit version, documenting limitations") and for the
executable half of box 4. CI installs a named released toolkit in an isolated environment.
fair-bioheaders has no default FHT support — FHT is a
draft read only through the opt-in rule V7 lane
(`BIOHEADERS_EXPERIMENTAL_FHT=1`), which is recognition of a development
contract, not shipped support (issue #9 owns that).

What it checks, and the difference between a failure and a finding:

- A **failure** is a disagreement between the released reader's outcome and an
  expectation derived from the rule text (`conformance/manifest.json`, whose
  expectations come from docs/FORMAT.md, docs/SCHEMA-VERSIONS.md, `fht.json`
  and conformance/README.md). The manifest is never edited here: the reader is
  the thing under test.
- A **finding** is measured behavior the manifest does not decide — the exact
  quoting and line ordering the writer emits, or which schema copy the draft
  lane is pinned to. Findings are reported for issue #9 and change nothing.

The newly valid mixed-molecule case is explicitly unsupported by the installed
four-value schema: a specific rejection probe precedes its reported NOT-RUN
acceptance/writer checks. Other current-contract gaps are measured explicitly. The opt-in
--stage-completeness permits only the two named arithmetic cases as NOT-RUN;
unexplained mismatches remain strict failures.

Lanes:

1. Identity. The installed distribution's version, the draft registry entry it
   ships (commit + SHA-256) and that entry's digest compared with this
   checkout's `fht.json`.
2. `verify` with the draft lane ON, per vector: exit status compared with
   `expected`; `selfChecksum: broken` must be reported as a checksum failure,
   `unreachable` must fail before the checksum question, and a vector whose only
   defect is a `parentLink` `checked-fail` must pass `verify` (the file is
   byte- and schema-valid) and fail `verify-links`.
3. `verify-links` with the lane ON, per `parentLink` vector: `checked-pass` and
   `unchecked` exit 0 and print `matched` / `not checked`; `checked-fail` exits 3
   and prints `not matched`. The three verdicts must stay distinguishable (C3).
4. `verify` with the lane OFF, per vector: reported; 0.11.0 must refuse all. Rule V5
   sends every FHT citation to the current FHR schema when the lane is closed, so
   the default path rejects the whole suite; that is the documented limitation,
   and the class distribution is printed so a later release can be compared with
   it.
5. Strip round trip, per valid vector, against FORMAT.md's own words ("Strip
   removes complete FHR lines and leaves ordinary comments intact"): the output
   must equal the input with exactly the `;~` lines removed — every record
   identifier, every line-wrapping byte, the U or T alphabet, case, and any
   ordinary `;` comment and blank line preserved in place.
6. Combine round trip, per valid vector: metadata parsed from the recombined
   file with this repository's independent reader must equal the metadata parsed
   from the distributed file (values, key order and JSON types), and the
   recombined file must verify under its own recomputed checksum. Whole-file
   byte equality is *not* required and is reported as a finding, because the
   writer emits its own canonical header for the same values.

Local usage (see docs/CI.md; the named version is the one recorded in
conformance/README.md):

    python scripts/run_toolkit_lane.py --venv /path/to/venv-with-fair-bioheaders

Exits 0 when every rule-derived expectation held, 1 otherwise.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import make_fht_fixtures as generator  # noqa: E402  (rule reading, vectors)

DRAFT_ENV = "BIOHEADERS_EXPERIMENTAL_FHT"
PREFIX = b";~"
_MISSING = object()  # distinguishes "absent" from "present and null"

FAILURES = []
FINDINGS = []
STAGED_COMPLETENESS = []
MEASURED = []


def fail(message):
    FAILURES.append(message)
    print(f"FAIL {message}")


def finding(message):
    FINDINGS.append(message)
    print(f"note {message}")


def measured(message):
    MEASURED.append(message)
    print(f"    {message}")


def read_fht_lines(data):
    """Every line of ``data`` with its terminator, split on R1's line ends."""
    return list(generator.split_lines_keepends(data))


def strip_expectation(data):
    """The bytes FORMAT.md requires from strip: drop `;~` lines, keep the rest."""
    return b"".join(text + term for text, term in read_fht_lines(data)
                    if not text.startswith(PREFIX))


def decompress(data):
    return generator.decompress(data)


class Toolkit:
    def __init__(self, venv):
        self.venv = Path(venv)
        self.binary = self.venv / "bin" / "bioheaders"
        if not self.binary.exists():
            raise SystemExit(f"{self.binary} not found: pass --venv pointing at a "
                             f"Python environment with fair-bioheaders installed")

    def run_bytes(self, *args, lane=True, data=None):
        env = dict(os.environ)
        env.pop(DRAFT_ENV, None)
        if lane:
            env[DRAFT_ENV] = "1"
        result = subprocess.run([str(self.binary), *[str(a) for a in args]],
                                capture_output=True, input=data, env=env, timeout=60)
        return result

    def run(self, *args, lane=True):
        result = self.run_bytes(*args, lane=lane)
        return result.returncode, (result.stdout + result.stderr).decode("utf-8", "replace")

    def version(self):
        code, out = self.run("--version")
        return out.strip() if code == 0 else f"unknown (exit {code})"

    def site_packages(self):
        candidates = sorted((self.venv / "lib").glob("python*/site-packages"))
        return candidates[0] if candidates else None


def lane_identity(toolkit):
    """Lane 1: what is installed and which draft bytes it reads."""
    version = toolkit.version()
    print(f"toolkit: fair-bioheaders {version} at {toolkit.venv}")
    site = toolkit.site_packages()
    if site is None:
        finding("no site-packages directory found; the draft registry entry "
                "could not be inspected")
        return version, None
    bundled = site / "bioheaders" / "schemas" / "bundled.json"
    if not bundled.is_file():
        finding(f"{bundled} not found: this build registers no drafts")
        return version, None
    registry = json.loads(bundled.read_text(encoding="utf-8"))
    entry = (registry.get("drafts") or {}).get("FHT")
    if entry is None:
        fail("the installed toolkit registers no FHT draft: the V7 lane is "
             "absent, so no draft-lane expectation can be tested here")
        return version, None
    local = hashlib.sha256((ROOT / "fht.json").read_bytes()).hexdigest()
    package = site / "bioheaders"
    schema_path = package / entry["file"]
    installed = (hashlib.sha256(schema_path.read_bytes()).hexdigest()
                 if schema_path.is_file() else None)
    measured(f"draft pin: commit {entry.get('revision')} retrieved "
             f"{entry.get('retrieved')} sha256 {entry.get('sha256')}")
    measured(f"bundled schema bytes sha256 {installed}")
    measured(f"this checkout's fht.json sha256 {local}")
    if entry.get("sha256") != local:
        finding(f"the toolkit's draft pin ({entry.get('sha256')[:12]}…) is not this "
                f"checkout's contract bytes ({local[:12]}…): agreement below is "
                f"agreement with the pinned revision, not with main")
    if installed != entry.get("sha256"):
        fail(f"the installed draft bytes ({installed}) do not match the digest "
             f"the toolkit states for them ({entry.get('sha256')})")
    return version, entry


def load_suite():
    manifest = json.loads((ROOT / "conformance" / "manifest.json").read_text("utf-8"))
    return manifest["vectors"]


def vector_bytes(entry):
    data = (ROOT / "conformance" / entry["file"]).read_bytes()
    return decompress(data) if entry.get("compressed") else data


def place(entry, work, name=None):
    target = Path(work) / (name or Path(entry["file"]).name)
    target.write_bytes((ROOT / "conformance" / entry["file"]).read_bytes())
    return target


MIXED_VECTOR = "fht-fasta-molecule-type-mixed"


def partition_mixed_capability(vectors, installed_schema):
    """Only the explicitly added mixed positive may lack old-reader coverage.

    No expected outcome is changed. A new reader whose enum includes mixed must
    run the ordinary acceptance comparison; no unexpected failure is excused.
    """
    definitions = installed_schema.get("$defs", installed_schema.get("definitions", {}))
    choices = definitions.get("MoleculeType", {}).get("enum")
    if not isinstance(choices, list):
        raise ValueError("installed FHT contract has no inspectable MoleculeType enum")
    compared, unsupported = [], []
    for vector in vectors:
        if vector["id"] == MIXED_VECTOR:
            if vector["expected"] != "valid" or vector.get("metadata", {}).get("moleculeType") != "mixed":
                raise ValueError("mixed capability control must retain its normative valid/mixed expectation")
            if "mixed" not in choices:
                unsupported.append(vector)
                continue
        compared.append(vector)
    return compared, unsupported


def lane_unsupported_mixed(toolkit, vectors, work):
    """Probe old-writer rejection without counting it as normative agreement."""
    for vector in vectors:
        code, output = toolkit.run("verify", place(vector, work))
        diagnostic = "schema validation failed at $.moleculeType: 'mixed' is not one of "
        failures = [line for line in output.splitlines() if "validation failed" in line]
        checksum_failed = "checksum verification failed" in output.casefold()
        if (code != 1 or len(failures) != 1 or diagnostic not in failures[0]
                or checksum_failed):
            fail(f"{vector['id']}: old-schema unsupported probe did not specifically reject moleculeType mixed")
        finding(f"{vector['id']}: current-contract acceptance/strip/combine NOT-RUN: "
                "the installed pinned MoleculeType enum lacks mixed; its rejection "
                "is a consumer coverage gap, not a normative invalid outcome")


def _reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "check_fht_fixtures", ROOT / "scripts" / "check_fht_fixtures.py")
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    return reader


def partition_installed_contract(vectors, installed_schema):
    """Split off vectors whose outcome the installed draft bytes decide
    differently from this checkout's fht.json.

    A released toolkit reads the draft revision it was built with. Where that
    older contract and this checkout's contract give different verdicts for
    a record that reaches the contract stage, comparing the toolkit with the
    rule-text expectation would test the pin, not the reader. Such vectors
    are probed against the installed bytes instead (lane_installed_contract)
    and reported NOT-RUN for the current contract. No expectation changes.
    Returns (compared, dependent) where dependent holds (vector, installed_ok).
    """
    import jsonschema
    reader = _reader()
    installed = jsonschema.Draft202012Validator(
        installed_schema, format_checker=jsonschema.FormatChecker())
    compared, dependent = [], []
    for vector in vectors:
        try:
            data = vector_bytes(vector)
        except ValueError:
            compared.append(vector)
            continue
        stage, _, _, record = reader.first_rejection(data)
        if stage is not None or reader.schema_selection(record) != "current":
            compared.append(vector)
            continue
        current_ok = not reader.schema_errors(record)
        installed_ok = not list(installed.iter_errors(record))
        if current_ok == installed_ok:
            compared.append(vector)
        else:
            dependent.append((vector, installed_ok))
    return compared, dependent


def lane_installed_contract(toolkit, dependent, work, *, stage_completeness=False):
    """The toolkit must at least agree with its own installed draft bytes."""
    for vector, installed_ok in dependent:
        code, output = toolkit.run("verify", place(vector, work))
        checksum_failed = "checksum verification failed" in output.casefold()
        want = 0 if installed_ok else 1
        if code != want or checksum_failed:
            fail(f"{vector['id']}: the installed draft bytes "
                 f"{'accept' if installed_ok else 'reject'} this record, but "
                 f"verify exited {code}"
                 + (" with a checksum failure" if checksum_failed else ""))
        reader = _reader()
        record = reader.parse_metadata(vector_bytes(vector))
        semantic_only = (vector["id"] in reader.EXPECTED_SEMANTIC_ERRORS
                         and vector.get("rule") == "C1" and installed_ok
                         and not list(reader.VALIDATOR.iter_errors(record))
                         and reader.completeness_errors(record)
                         == reader.EXPECTED_SEMANTIC_ERRORS[vector["id"]])
        if stage_completeness and semantic_only:
            STAGED_COMPLETENESS.append(vector["id"])
            print(f"note {vector['id']}: C1 arithmetic NOT-RUN by installed toolkit; "
                  "the generated schema accepts it, the fully supplied count set "
                  "fails the owning semantic check. Runtime enforcement remains #9.")
            continue
        finding(f"{vector['id']}: current-contract comparison NOT-RUN: the "
                f"installed draft {'accepts' if installed_ok else 'rejects'} it "
                f"while this checkout's full C1 contract "
                f"{'rejects' if installed_ok else 'accepts'} it (schema pin or "
                "semantic implementation differs; reader agrees with installed bytes)")


def install_checkout_contract(toolkit, entry):
    """Overlay this checkout's fht.json onto the installed draft (opt-in).

    For a throwaway environment only: the installed package's draft file is
    replaced by this checkout's bytes and its registry entry records their
    digest, so every vector is compared against the contract under review
    rather than against the revision the release was built with."""
    import subprocess as _subprocess
    site = toolkit.site_packages()
    package = site / "bioheaders"
    raw = (ROOT / "fht.json").read_bytes()
    (package / entry["file"]).write_bytes(raw)
    bundled_path = package / "schemas" / "bundled.json"
    registry = json.loads(bundled_path.read_text(encoding="utf-8"))
    head = _subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                           capture_output=True, text=True).stdout.strip() or "unknown"
    registry["drafts"]["FHT"].update(
        sha256=hashlib.sha256(raw).hexdigest(),
        revision=f"checkout {head} (overlaid by run_toolkit_lane.py)",
        retrieved="overlay")
    bundled_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    print(f"overlay: installed FHT draft replaced by this checkout's fht.json "
          f"({hashlib.sha256(raw).hexdigest()[:12]}…) in {package}")


def lane_verify(toolkit, vectors, work):
    """Lane 2: `verify` under the draft lane against the rule-derived expected."""
    checked = {"valid": 0, "invalid": 0}
    for entry in vectors:
        path = place(entry, work)
        code, output = toolkit.run("verify", path)
        links = entry.get("parentLink") or []
        link_failure = any(link["result"] == "checked-fail" for link in links)
        label = entry["id"]
        if entry["expected"] == "valid":
            checked["valid"] += 1
            if code != 0:
                fail(f"{label}: expected valid, verify exited {code}: "
                     f"{output.strip().splitlines()[-1:]!r}")
            elif "Checksum verified." not in output:
                fail(f"{label}: exit 0 without 'Checksum verified.'")
            continue
        checked["invalid"] += 1
        if link_failure:
            if code != 0:
                fail(f"{label}: a C3 link failure must not fail byte/schema "
                     f"verify (the file itself is valid), but verify exited "
                     f"{code}: {output.strip()[:160]!r}")
            continue
        if code != 1:
            fail(f"{label}: expected invalid under {entry['rule']}, verify "
                 f"exited {code}: {output.strip().splitlines()[-1:]!r}")
            continue
        classification = entry["selfChecksum"]
        if classification == "unreachable" and (
                "Checksum verification failed" in output or "Checksum verified." in output):
            fail(f"{label}: declares an unreachable checksum but reported "
                 f"a checksum comparison: {output.strip()[:160]!r}")
        if classification == "broken" and "Checksum verification failed" not in output:
            fail(f"{label}: declares selfChecksum broken but did not report a "
                 f"checksum failure: {output.strip()[:160]!r}")
        if classification == "matches" and "Checksum verification failed" in output:
            fail(f"{label}: declares consistent bytes (the defect is elsewhere) "
                 f"but was rejected by the checksum comparison: the rejection "
                 f"came about by accident")
    print(f"verify (draft lane ON): {checked['valid']} valid accepted, "
          f"{checked['invalid']} invalid rejected")


def lane_links(toolkit, vectors, work):
    """Lane 3: the three parent-link verdicts stay distinguishable."""
    count = 0
    for entry in vectors:
        links = entry.get("parentLink") or []
        if not links:
            continue
        count += 1
        child = place(entry, work, name=f"link-{entry['id']}.fht.fasta")
        parents = [place({"file": link["file"]}, work,
                         name=f"parent-{index}-{Path(link['file']).name}")
                   for index, link in enumerate(links) if link.get("file")]
        code, output = toolkit.run("verify-links", child, *parents)
        results = [link["result"] for link in links]
        label = entry["id"]
        if "checked-fail" in results:
            if code != 3:
                fail(f"{label}: a checked-fail link must exit 3, got {code}: "
                     f"{output.strip()[:160]!r}")
            if "not matched (" not in output:
                fail(f"{label}: a checked-fail link must print 'not matched ('")
        elif code != 0:
            fail(f"{label}: {results} links are not a rejection, but "
                 f"verify-links exited {code}: {output.strip()[:160]!r}")
        if ("checked-pass" in results
                and re.search(r"(?<!not )\bmatched \(", output) is None):
            fail(f"{label}: a checked-pass link must print 'matched ('")
        if "unchecked" in results and "not checked (" not in output:
            fail(f"{label}: an unchecked link must print 'not checked (' — "
                 f"a reader may not call an absent parent verified, and may not "
                 f"silently skip the entry either")
    print(f"verify-links (draft lane ON): {count} vectors with parentLink entries")


def lane_default_path(toolkit, vectors, work):
    """Lane 4: report V5 behavior and guard the named 0.11.0 default."""
    classes = {}
    for entry in vectors:
        path = place(entry, work, name=f"off-{entry['id']}.fht.fasta")
        code, output = toolkit.run("verify", path, lane=False)
        last = [line for line in output.strip().splitlines() if line.strip()]
        key = (code, re.sub(r"[0-9A-Za-z+/=]{20,}", "<value>",
                            last[-1] if last else "")[:70])
        classes.setdefault(key, []).append(entry["id"])
    accepted = sum(len(ids) for (code, _), ids in classes.items() if code == 0)
    measured(f"default path (draft lane OFF): {accepted} of {len(vectors)} "
             f"vectors accepted; FHT has no default reader, so rule V5 routes "
             f"the rest to the current FHR schema")
    if toolkit.version() == "0.11.0" and accepted:
        fail("0.11.0 accepted FHT vectors with its draft lane disabled")
    for (code, message), ids in sorted(classes.items(), key=lambda kv: str(kv[0])):
        measured(f"  exit={code} n={len(ids):2d} {message!r}"
                 + (f" {ids}" if len(ids) <= 4 else ""))
    return classes


def lane_strip(toolkit, vectors, work):
    """Lane 5: strip preserves every byte except the `;~` header lines."""
    checked = 0
    for entry in vectors:
        if entry["expected"] != "valid":
            continue
        checked += 1
        original = vector_bytes(entry)
        source = Path(work) / f"strip-{entry['id']}.fht.fasta"
        source.write_bytes(original)
        target = Path(work) / f"stripped-{entry['id']}.fasta"
        code, output = toolkit.run("strip", source, target, "--type", "fasta")
        label = entry["id"]
        if code != 0:
            fail(f"{label}: strip exited {code}: {output.strip()[:160]!r}")
            continue
        want = strip_expectation(original)
        got = target.read_bytes()
        if got != want:
            fail(f"{label}: strip did not return the input minus its ';~' lines "
                 f"(sequence identifiers, wrapping, alphabet, ordinary comments "
                 f"and blank lines must stay byte-identical): "
                 f"{len(got)} bytes vs {len(want)} expected")
    print(f"strip: {checked} valid vectors compared with the FORMAT.md rule text")


def lane_combine(toolkit, vectors, work):
    """Lane 6: combine preserves metadata values/order/types, and the output
    verifies under its own recomputed checksum."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "check_fht_fixtures", ROOT / "scripts" / "check_fht_fixtures.py")
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)

    identical = 0
    checked = 0
    for entry in vectors:
        if entry["expected"] != "valid":
            continue
        checked += 1
        label = entry["id"]
        original = vector_bytes(entry)
        source = Path(work) / f"meta-{label}.fht.fasta"
        source.write_bytes(original)
        metadata = Path(work) / f"combine-meta-{label}.yaml"
        code, output = toolkit.run("convert", source, metadata, "--to", "yaml")
        if code != 0:
            fail(f"{label}: convert to YAML exited {code}: "
                 f"{output.strip()[:160]!r}")
            continue
        stripped = Path(work) / f"combine-seq-{label}.fasta"
        stripped.write_bytes(strip_expectation(original))
        out = Path(work) / f"combined-{label}.fht.fasta"
        code, output = toolkit.run("combine", metadata, stripped, "-o", out)
        if code != 0:
            fail(f"{label}: combine exited {code}: {output.strip()[:160]!r}")
            continue
        data = out.read_bytes()
        if strip_expectation(data) != strip_expectation(original):
            fail(f"{label}: combine changed payload bytes "
                 f"(identifiers, wrapping, alphabet, comments or line endings)")
        try:
            before = reader.parse_metadata(original)
            after = reader.parse_metadata(data)
        except ValueError as error:
            fail(f"{label}: the recombined file does not read cleanly: {error}")
            continue
        before.pop("checksum", None)
        after.pop("checksum", None)
        changed = [key for key in set(before) | set(after)
                   if before.get(key, _MISSING) != after.get(key, _MISSING)]
        if changed:
            fail(f"{label}: combine changed the metadata at "
                 f"{sorted(changed)[:3]}")
        if list(before) != list(after):
            fail(f"{label}: combine reordered the metadata keys: "
                 f"{list(before)} -> {list(after)}")
        def metadata_shape(value):
            if isinstance(value, dict):
                return (type(value), [(type(key), key, metadata_shape(item))
                                     for key, item in value.items()])
            if isinstance(value, list):
                return (type(value), [metadata_shape(item) for item in value])
            return type(value)

        mistyped = [key for key in before
                    if key in after and
                    metadata_shape(before[key]) != metadata_shape(after[key])]
        if mistyped:
            fail(f"{label}: combine changed a nested key order or value type at "
                 f"{sorted(mistyped)[:3]}")
        code, output = toolkit.run("verify", out)
        if code != 0:
            fail(f"{label}: the recombined file does not verify: "
                 f"{output.strip()[:160]!r}")
        if data == original:
            identical += 1
    measured(f"combine: {identical} of {checked} recombined files are byte-identical "
            f"to the distributed bytes; the writer emits its own canonical header "
            f"for the same values, which the rule text allows (FORMAT.md: combine "
            f"regenerates the header and recomputes the checksum)")
    print(f"combine: {checked} valid vectors round-tripped (values, order, "
          f"verification)")


def metadata_signature(data):
    """Independent parsed values and recursive ordering/types, except root checksum."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "check_fht_fixtures", ROOT / "scripts" / "check_fht_fixtures.py")
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    metadata = reader.parse_metadata(data)
    metadata.pop("checksum", None)

    def ordered_typed(value):
        if isinstance(value, dict):
            return (type(value), tuple((ordered_typed(key), ordered_typed(item))
                                      for key, item in value.items()))
        if isinstance(value, list):
            return (type(value), tuple(ordered_typed(item) for item in value))
        return (type(value), value)

    return ordered_typed(metadata)


def lane_streams(toolkit, vectors, work):
    """Exercise actual stdin/stdout, outside the file-only manifest vocabulary.

    Compare raw stdout bytes; diagnostic text on stderr must never become payload.
    Compressed inputs are tested exactly as distributed, not pre-decompressed.
    """
    counts = {"verify": 0, "strip": 0, "combine": 0}
    for entry in vectors:
        raw = (ROOT / "conformance" / entry["file"]).read_bytes()
        expected_code = 0 if (entry["expected"] == "valid" or any(
            link["result"] == "checked-fail" for link in entry.get("parentLink", [])
        )) else 1
        result = toolkit.run_bytes("verify", "-", "--type", "fasta", data=raw)
        counts["verify"] += 1
        if result.returncode != expected_code:
            fail(f"{entry['id']}: stdin verify exit {result.returncode}, expected {expected_code}")
        if entry["expected"] != "valid":
            continue
        result = toolkit.run_bytes("strip", "-", "-", "--type", "fasta", data=raw)
        counts["strip"] += 1
        payload = strip_expectation(vector_bytes(entry))
        if result.returncode != 0 or result.stdout != payload:
            fail(f"{entry['id']}: stdin/stdout strip changed payload bytes or failed")
        source = place(entry, work, name=f"stream-{entry['id']}.fht.fasta")
        metadata = Path(work) / f"stream-{entry['id']}.yaml"
        code, output = toolkit.run("convert", source, metadata, "--to", "yaml")
        if code != 0:
            fail(f"{entry['id']}: stream setup convert failed: {output[:160]}")
            continue
        result = toolkit.run_bytes("combine", metadata, "-", "-o", "-",
                                   "--type", "fasta", data=payload)
        counts["combine"] += 1
        if result.returncode != 0 or strip_expectation(result.stdout) != payload:
            fail(f"{entry['id']}: stdin/stdout combine changed payload bytes or failed")
            continue
        try:
            if metadata_signature(vector_bytes(entry)) != metadata_signature(result.stdout):
                fail(f"{entry['id']}: stdin/stdout combine changed metadata values, order or types")
        except ValueError as error:
            fail(f"{entry['id']}: combined stdout metadata does not read cleanly: {error}")
        verified = toolkit.run_bytes("verify", "-", "--type", "fasta", data=result.stdout)
        if verified.returncode != 0 or b"Checksum verified." not in verified.stdout + verified.stderr:
            fail(f"{entry['id']}: combined stdout does not verify")
    if not counts["verify"] or not counts["strip"] or not counts["combine"]:
        fail("stream lane executed zero cases for an operation")
    print(f"streams (stdin/stdout, draft lane ON): {counts}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--venv", required=True, type=Path,
                        help="Python environment with fair-bioheaders installed")
    parser.add_argument("--keep", action="store_true",
                        help="keep the scratch directory and print its path")
    parser.add_argument("--checkout-contract", action="store_true",
                        help="overlay this checkout's fht.json onto the installed "
                             "draft before scoring (modifies the environment: use a "
                             "throwaway venv)")
    parser.add_argument("--strict", action="store_true",
                        help="fail when any finding is reported, not only on "
                             "disagreements")
    parser.add_argument("--stage-completeness", action="store_true",
                        help="explicit prepublication accounting for the two "
                             "schema-valid C1 BUSCO arithmetic cases old toolkit "
                             "code cannot check; requires --checkout-contract")
    args = parser.parse_args(argv)
    if args.stage_completeness and not args.checkout_contract:
        parser.error("--stage-completeness requires --checkout-contract")

    if not environment_ok():
        return 1
    toolkit = Toolkit(args.venv)
    if args.checkout_contract:
        _, entry = lane_identity(toolkit)
        if FAILURES or entry is None:
            print("Identity check failed before the overlay: NOTHING SCORED")
            return 1
        install_checkout_contract(toolkit, entry)
        FINDINGS.clear()
    version, entry = lane_identity(toolkit)
    if FAILURES:
        print("Identity check failed: NOTHING SCORED")
        return 1
    vectors = load_suite()
    work = Path(tempfile.mkdtemp(prefix="fht-toolkit-lane-"))
    try:
        installed_schema = json.loads((toolkit.site_packages() / "bioheaders" / entry["file"]).read_bytes())
        compared, unsupported = partition_mixed_capability(vectors, installed_schema)
        lane_unsupported_mixed(toolkit, unsupported, work)
        compared, dependent = partition_installed_contract(compared, installed_schema)
        lane_installed_contract(toolkit, dependent, work,
                                stage_completeness=args.stage_completeness)
        unsupported = unsupported + [vector for vector, _ in dependent]
        if FAILURES:
            print("Unsupported-value preflight failed: NOTHING SCORED")
            return 1
        lane_verify(toolkit, compared, work)
        lane_links(toolkit, compared, work)
        lane_default_path(toolkit, vectors, work)
        lane_strip(toolkit, compared, work)
        lane_combine(toolkit, compared, work)
        lane_streams(toolkit, compared, work)
    finally:
        if args.keep:
            print(f"scratch: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)

    print(f"\ntoolkit: fair-bioheaders {version}; "
          f"draft pin {entry.get('revision') if entry else 'n/a'}")
    print(f"vectors: {len([v for v in vectors if v['expected'] == 'valid'])} valid, "
          f"{len([v for v in vectors if v['expected'] == 'invalid'])} invalid")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s): the installed reader disagrees with "
              f"the rule text. Expectations are NOT adjusted here; conformance/"
              f"README.md records them and issue #9 owns the implementation.")
        return 1
    print(f"implementation comparisons: {len(compared)}; current-contract unsupported/not-run: {len(unsupported)}")
    print(f"staged C1 arithmetic NOT-RUN by installed runtime: {len(STAGED_COMPLETENESS)} "
          f"{STAGED_COMPLETENESS}")
    if args.strict and FINDINGS:
        print(f"\n{len(FINDINGS)} finding(s) and --strict: failing. With "
              f"--checkout-contract only explicitly staged arithmetic may be NOT-RUN.")
        return 1
    print(f"\nOK: the installed reader agrees with the compared subset; unsupported "
          f"current-contract values are not acceptance passes "
          f"({len(FINDINGS)} finding(s) reported for #9)")
    return 0


def environment_ok():
    if sys.version_info < (3, 9):
        print("this lane needs Python 3.9+ (subprocess and hashlib features)",
              file=sys.stderr)
        return False
    if "sha512_256" not in hashlib.algorithms_available:
        print("SHA-512/256 is unavailable in this Python build", file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
