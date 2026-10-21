# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Schema versions and the version registry (specs/012-schema-versioning, docs/SCHEMA-VERSIONS.md)."""

import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "schemas" / "versions.json").read_text(encoding="utf-8"))
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def accepted(version):
    """The schemaVersion values the schema of ``version`` accepts (M.0 to M.N)."""
    major, minor = (int(part) for part in version.split("."))
    return [f"{major}.{n}" for n in range(minor + 1)]


class SchemaVersionTests(unittest.TestCase):
    def test_registry_shape(self):
        self.assertIn(REGISTRY["current"], REGISTRY["releases"])
        self.assertEqual(set(REGISTRY["files"]), {"FHR", "FHP", "FHGFF3"})
        self.assertEqual(REGISTRY["w3id"], {"FHR": "fhr", "FHP": "fhp", "FHGFF3": "fhgff3"})
        for tag, types in REGISTRY["releases"].items():
            self.assertRegex(tag, r"^v[0-9]+\.[0-9]+\.[0-9]+$")
            for header_type, version in types.items():
                with self.subTest(tag=tag, header_type=header_type):
                    self.assertIn(header_type, REGISTRY["files"])
                    # v0.3.x published the number 1; later releases use "MAJOR.MINOR".
                    if version != 1:
                        self.assertRegex(version, VERSION)

    def test_published_schemas_match_the_current_release(self):
        """SC-001: every schema accepts exactly its registry version range."""
        for header_type, version in REGISTRY["releases"][REGISTRY["current"]].items():
            schema = json.loads((ROOT / REGISTRY["files"][header_type]).read_text())
            with self.subTest(header_type=header_type):
                self.assertEqual(schema["properties"]["schemaVersion"]["enum"], accepted(version))
                self.assertEqual(schema["properties"]["schemaVersion"]["type"], "string")

    def test_schema_bytes_match_the_current_release_tag(self):
        """docs/SCHEMA-VERSIONS.md: a schema change does not land on main before its release."""
        tag = REGISTRY["current"]
        try:
            tagged = {
                name: subprocess.run(
                    ["git", "show", f"{tag}:{name}"], cwd=ROOT, check=True,
                    capture_output=True,
                ).stdout
                for name in REGISTRY["files"].values()
            }
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(
                f"cannot read the {tag!r} tag ({error}). This is either a shallow checkout "
                "(run `git fetch --tags`) or the documented pre-release exception where "
                "schemas/versions.json `current` names a release before its tag exists "
                "(docs/SCHEMA-VERSIONS.md#schema-files-on-main); check the spelling of "
                "`current` if neither applies"
            )
        for header_type, name in REGISTRY["files"].items():
            with self.subTest(header_type=header_type, tag=tag):
                self.assertEqual(
                    (ROOT / name).read_bytes(), tagged[name],
                    f"{name} differs from {tag}:{name}. A schema change needs its own release; "
                    "see docs/SCHEMA-VERSIONS.md#schema-files-on-main for the exception process.",
                )

    def test_v04_versions(self):
        self.assertEqual(REGISTRY["releases"]["v0.4.0"],
                         {"FHR": "2.0", "FHP": "1.0", "FHGFF3": "1.0"})
        self.assertEqual(REGISTRY["releases"]["v0.3.1"], {"FHR": 1})

    def test_examples_cite_the_current_release(self):
        """FR-010, SC-003: examples cite their type's versioned URL and version."""
        current = REGISTRY["current"]
        releases = REGISTRY["releases"][current]
        urls = {f"https://w3id.org/fair-bioheaders/{segment}/{current}": header_type
                for header_type, segment in REGISTRY["w3id"].items()}
        checked = 0
        for path in sorted((ROOT / "examples").rglob("*")):
            if path.suffix not in {".json", ".yaml", ".fasta", ".gfa", ".gff3"} or \
                    path.name == "no-header.gff3":
                continue
            text = path.read_text(encoding="utf-8")
            with self.subTest(example=path.name):
                self.assertNotIn("FHR-Specification/main/", text)
                cited = [url for url in urls if url in text]
                self.assertEqual(len(cited), 1, path.name)
                version = releases[urls[cited[0]]]
                self.assertTrue(f"'{version}'" in text or f'"{version}"' in text, path.name)
                checked += 1
        self.assertGreaterEqual(checked, 18)

    def test_policy_document_labels(self):
        text = (ROOT / "docs" / "SCHEMA-VERSIONS.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"\[(V\d)\]", text), ["V1", "V2", "V3", "V4", "V5"])
        for tag in REGISTRY["releases"]:
            self.assertIn(tag, text)


if __name__ == "__main__":
    unittest.main()
