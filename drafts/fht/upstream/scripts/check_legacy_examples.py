"""Classified validation of the legacy FHT examples and fixtures (issue #14).

Three groups, all measured against the preserved legacy draft
``legacy/fht-v0.1.json`` with the declared Draft 2020-12 dialect and an
explicit ``FormatChecker`` (never against the current contract, and never a
claim that the legacy draft implements the family design):

1. ``tests/fixtures/legacy/valid/`` — positive fixtures: must validate with
   zero errors; any failure is reported with the fixture path and JSON Pointer.
2. ``tests/fixtures/legacy/rejected/`` — rejection fixtures with the measured
   expectations in ``expected.json``: each file must fail with EXACTLY the
   recorded errors (same path, all recorded message fragments, same count), so
   neither new failures nor silent repairs can hide.
3. ``legacy/examples/`` — the preserved historical instances, classified in
   ``tests/fixtures/legacy/classification.json``. The manifest pins each file's
   SHA-256 (the bytes are immutable review inputs) and records the status:
   nonconforming-historical (measured schema errors), unparseable-historical
   (the ;~ YAML block cannot even be parsed) or not-json-or-yaml-historical
   (out of scope for schema validation). The measured outcome must still match
   the classification — a repaired or newly-broken historical file fails this
   check and must be re-reviewed, not quietly reclassified.

Local usage (pinned environment; see docs/CI.md):

    python -m pip install "jsonschema[format]==4.26.0" "PyYAML==6.0.3"
    python scripts/check_legacy_examples.py

Exit status is 0 when every group matches its recorded classification.
"""

import hashlib
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from importlib.metadata import version as package_version

ROOT = Path(__file__).resolve().parents[1]
LEGACY_SCHEMA = ROOT / "legacy" / "fht-v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "legacy"
CLASSIFICATION = FIXTURES / "classification.json"
EXPECTED = FIXTURES / "rejected" / "expected.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measured_errors(validator, instance):
    return [
        ("/".join(str(part) for part in error.absolute_path), error.message)
        for error in validator.iter_errors(instance)
    ]


def match_errors(label, errors, expectations):
    """Assign each measured error to exactly one expected entry. Return findings."""
    findings = []
    remaining = list(errors)
    for expectation in expectations:
        path = "/".join(str(part) for part in expectation["path"])
        fragments = expectation["contains"]
        hit = None
        for candidate in remaining:
            if candidate[0] == path and all(f in candidate[1] for f in fragments):
                hit = candidate
                break
        if hit is None:
            findings.append(
                f"{label}: expected error at /{path} containing {fragments!r} "
                "did not occur"
            )
        else:
            remaining.remove(hit)
    for path, message in remaining:
        findings.append(f"{label}: unexpected error at /{path}: {message}")
    return findings


def inventory_findings(manifest, disk_files):
    """Report unclassified, missing, and duplicate historical example entries."""
    listed = [entry["file"] for entry in manifest["examples"]]
    listed_set = set(listed)
    disk_set = set(disk_files)
    return {
        "unclassified": sorted(disk_set - listed_set),
        "missing": sorted(listed_set - disk_set),
        "duplicate": sorted(
            name for name in listed_set if listed.count(name) > 1
        ),
    }


def parse_header_block(path):
    """Extract and safely parse the ;~ header block of a legacy FASTA file."""
    text = path.read_text(encoding="utf-8")
    block = [line[2:] for line in text.splitlines() if line.startswith(";~")]
    return yaml.safe_load("\n".join(block))


def main():
    failures = []
    checked = 0

    def report(ok, label, detail=""):
        nonlocal checked
        checked += 1
        print(f"  {'PASS' if ok else 'FAIL'} {label}" + (f": {detail}" if detail else ""))
        if not ok:
            failures.append(label)

    print("Legacy example and fixture validation "
          f"(jsonschema {package_version('jsonschema')}, PyYAML "
          f"{package_version('pyyaml')}, Draft 2020-12 + explicit FormatChecker)")

    schema = json.loads(LEGACY_SCHEMA.read_text(encoding="utf-8"))
    manifest = json.loads(CLASSIFICATION.read_text(encoding="utf-8"))
    expectations = json.loads(EXPECTED.read_text(encoding="utf-8"))
    report(sha256(LEGACY_SCHEMA) == manifest["schemaSha256"],
           "legacy schema matches the classification manifest digest",
           manifest["schemaSha256"])
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    print("Positive fixtures (tests/fixtures/legacy/valid/):")
    for path in sorted((FIXTURES / "valid").glob("*.json")):
        relative = path.relative_to(ROOT)
        instance = json.loads(path.read_text(encoding="utf-8"))
        errors = measured_errors(validator, instance)
        report(not errors, str(relative),
               "; ".join(f"/{p}: {m}" for p, m in errors[:5]) if errors
               else "valid against the legacy draft")

    print("Rejection fixtures (tests/fixtures/legacy/rejected/):")
    listed = sorted(p.name for p in (FIXTURES / "rejected").glob("*.json")
                    if p.name != "expected.json")
    report(set(listed) == set(expectations),
           "rejection fixtures and expected.json cover the same files",
           f"fixtures={listed} expected={sorted(expectations)}")
    for name in listed:
        path = FIXTURES / "rejected" / name
        relative = path.relative_to(ROOT)
        instance = json.loads(path.read_text(encoding="utf-8"))
        errors = measured_errors(validator, instance)
        findings = match_errors(str(relative), errors, expectations.get(name, []))
        report(not findings, str(relative),
               findings[0] if findings else f"{len(errors)} measured error(s) match")

    print("Historical examples (legacy/examples/, classified with tracked reasons):")
    disk_files = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "legacy" / "examples").rglob("*")
        if path.is_file()
    ]
    inventory = inventory_findings(manifest, disk_files)
    report(
        not any(inventory.values()),
        "historical examples and classification manifest cover the same files",
        f"unclassified={inventory['unclassified']} missing={inventory['missing']} "
        f"duplicate={inventory['duplicate']}",
    )
    for entry in manifest["examples"]:
        relative = entry["file"]
        path = ROOT / relative
        if not path.is_file():
            report(False, relative, "file listed in the classification manifest is missing")
            continue
        if sha256(path) != entry["sha256"]:
            report(False, relative,
                   f"preserved bytes moved: sha256 {sha256(path)} != "
                   f"{entry['sha256']} (historical examples must not be repaired in place)")
            continue
        status = entry["classification"]
        if status == "not-json-or-yaml-historical":
            report(entry["format"] not in ("json", "yaml", "fasta"),
                   f"{relative} [{status}]",
                   "outside the supported JSON/YAML/FASTA example formats; "
                   "preserved as a presentation artifact")
            continue
        if entry["format"] == "fasta":
            try:
                parse_header_block(path)
            except yaml.YAMLError as error:
                text = str(error)
                ok = all(fragment in text
                         for fragment in entry["expectedParseErrorContains"])
                report(ok, f"{relative} [{status}]",
                       "header block fails to parse as recorded"
                       if ok else f"parse error {text[:120]!r} does not contain "
                       f"{entry['expectedParseErrorContains']}")
            else:
                report(False, f"{relative} [{status}]",
                       "header block now parses; the classification is stale — "
                       "re-review, do not repair silently")
            continue
        if entry["format"] == "json":
            instance = json.loads(path.read_text(encoding="utf-8"))
        else:
            instance = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = measured_errors(validator, instance)
        findings = match_errors(relative, errors, entry["expectedErrors"])
        report(not findings, f"{relative} [{status}]",
               findings[0] if findings
               else f"{len(errors)} measured field error(s) match the recorded "
                    "classification")

    if failures:
        print(f"\nLegacy example checks failed: {len(failures)}/{checked}",
              file=sys.stderr)
        return 1
    print(f"\nLegacy example checks passed: {checked} grouped result(s); "
          "no historical failure is hidden and none was repaired in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
