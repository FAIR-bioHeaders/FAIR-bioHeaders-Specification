"""Check pinned shared files (LinkML imports, released FHR schema) against schemas/provenance.json.

The pinned core and shared files are copied verbatim from the shared
specification repository. This check fails if either copy changes without an
updated provenance record, so a local edit cannot masquerade as a shared change.
"""

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "schemas" / "provenance.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    try:
        record = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"Provenance check failed: {error}", file=sys.stderr)
        return 1
    failures = []
    try:
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        commits = re.findall(
            r"^# Pinned shared-source-commit: ([0-9a-f]{40})$", citation, re.MULTILINE
        )
        if len(commits) != 1:
            failures.append("CITATION.cff: expected exactly one pinned shared-source-commit")
        elif commits[0] != record.get("source_commit"):
            failures.append(
                "CITATION.cff shared source commit does not match "
                "schemas/provenance.json source_commit"
            )
    except OSError as error:
        failures.append(f"CITATION.cff: {error}")
    for relative, expected in record.get("files", {}).items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"{relative}: missing")
            continue
        actual = sha256(path)
        if actual != expected.get("sha256"):
            failures.append(
                f"{relative}: sha256 {actual} does not match "
                f"{expected.get('sha256')}"
            )
    if failures:
        print("Pinned shared imports do not match provenance:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print(
            "Replace the copy from the pinned shared release; do not edit it by "
            "hand. Update schemas/provenance.json only as part of a reviewed "
            "import change.",
            file=sys.stderr,
        )
        return 1
    print(
        "Pinned shared imports match schemas/provenance.json "
        f"({record.get('source_commit')})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
