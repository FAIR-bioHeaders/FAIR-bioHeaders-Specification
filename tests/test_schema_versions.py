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


def git_tag_exists(tag):
    """Whether this checkout can read ``tag`` (a shallow clone may not)."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", f"{tag}^{{commit}}"],
            cwd=ROOT, check=True, capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def release_identity_mode(registry, tag_available=None):
    """Return ``"release"`` or ``"pre-release"``, or raise on an invalid state.

    A missing tag is only acceptable when ``preRelease`` names that same tag.
    Otherwise a typo in ``current`` would look exactly like a shallow checkout.
    """
    tag = registry["current"]
    pre_release = registry.get("preRelease")
    available = tag_available or git_tag_exists
    if pre_release is not None:
        if pre_release != tag:
            raise AssertionError("`preRelease` must be null or equal `current`")
        if available(tag):
            raise AssertionError(
                f"`preRelease` names {tag}, but that tag exists; remove the marker"
            )
        return "pre-release"
    if not available(tag):
        raise AssertionError(
            f"{tag} does not exist. For a shallow checkout run `git fetch --tags`; "
            "when preparing a release, set `preRelease` to the same tag as `current`"
        )
    return "release"


class SchemaVersionTests(unittest.TestCase):
    def test_registry_shape(self):
        self.assertIn(REGISTRY["current"], REGISTRY["releases"])
        pre_release = REGISTRY.get("preRelease")
        if pre_release is not None:
            self.assertEqual(pre_release, REGISTRY["current"])
            self.assertRegex(pre_release, r"^v[0-9]+\.[0-9]+\.[0-9]+$")
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
            mode = release_identity_mode(REGISTRY)
        except AssertionError as error:
            self.fail(str(error))
        if mode == "pre-release":
            self.skipTest(
                f"{tag} is the documented pre-release target in schemas/versions.json "
                "and its tag has not been created yet; see "
                "docs/SCHEMA-VERSIONS.md#schema-files-on-main"
            )
        for header_type, name in REGISTRY["files"].items():
            with self.subTest(header_type=header_type, tag=tag):
                result = subprocess.run(
                    ["git", "show", f"{tag}:{name}"], cwd=ROOT, capture_output=True,
                )
                self.assertEqual(
                    result.returncode, 0,
                    f"{tag} exists but {name} cannot be read from it "
                    f"({result.stderr.decode(errors='replace').strip()}). An incomplete "
                    "release must not pass the release-identity check.",
                )
                self.assertEqual(
                    (ROOT / name).read_bytes(), result.stdout,
                    f"{name} differs from {tag}:{name}. A schema change needs its own release; "
                    "see docs/SCHEMA-VERSIONS.md#schema-files-on-main for the exception process.",
                )

    def test_missing_tag_without_a_pre_release_marker_fails(self):
        registry = {"current": "v9.9.9", "preRelease": None}
        with self.assertRaisesRegex(AssertionError, "does not exist"):
            release_identity_mode(registry, lambda tag: False)

    def test_documented_pre_release_may_skip_a_missing_tag(self):
        registry = {"current": "v9.9.9", "preRelease": "v9.9.9"}
        self.assertEqual(
            release_identity_mode(registry, lambda tag: False), "pre-release"
        )

    def test_pre_release_marker_must_match_current(self):
        registry = {"current": "v9.9.9", "preRelease": "v9.9.8"}
        with self.assertRaisesRegex(AssertionError, "must be null or equal"):
            release_identity_mode(registry, lambda tag: False)

    def test_pre_release_marker_must_be_cleared_when_the_tag_exists(self):
        registry = {"current": "v9.9.9", "preRelease": "v9.9.9"}
        with self.assertRaisesRegex(AssertionError, "remove the marker"):
            release_identity_mode(registry, lambda tag: True)

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
        self.assertEqual(re.findall(r"\[(V\d)\]", text), ["V1", "V2", "V3", "V4", "V5", "V6"])
        for tag in REGISTRY["releases"]:
            self.assertIn(tag, text)


if __name__ == "__main__":
    unittest.main()
