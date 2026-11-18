"""Tests for scripts/check_pattern_census.py (#270).

The census has two halves with opposite failure semantics, and these tests hold
both: the released contract inventory must not drift by even one character, and
the draft/proposal reporting must never fail the build — including for the
lookaround patterns that #270 established are legal under the ECMA-262 floor.
"""

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    import yaml  # noqa: F401  (needed to census schemas/core.yaml and shared.yaml)
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_pattern_census.py"
BASELINE = ROOT / ".github" / "pattern-baseline.json"

sys.path.insert(0, str(SCRIPT.parent))
import check_pattern_census as census  # noqa: E402


def scan(pattern):
    return census.scan(pattern)


class AnchorTests(unittest.TestCase):
    """A `$` counts only as an anchor, never as a literal."""

    def test_plain_anchor(self):
        self.assertTrue(scan("^[A-Za-z0-9_-]{32}$")["dollar_anchor"])

    def test_anchor_in_alternation(self):
        self.assertTrue(scan("^[a]$|^[b]$")["dollar_anchor"])

    def test_dollar_inside_character_class_is_not_an_anchor(self):
        for pattern in ("^[a-z$]+", "[$]", "[^$]", r"^[\]$]+"):
            with self.subTest(pattern=pattern):
                self.assertFalse(scan(pattern)["dollar_anchor"],
                                 f"{pattern}: `$` is a literal member of the class")

    def test_escaped_dollar_is_not_an_anchor(self):
        for pattern in (r"^\$$", r"cost: \$[0-9]+$"):
            with self.subTest(pattern=pattern):
                self.assertTrue(scan(pattern)["dollar_anchor"],
                                f"{pattern}: the real `$` at the end still counts")
                self.assertFalse(scan(r"^\$")["dollar_anchor"])

    def test_dollar_after_an_escaped_backslash(self):
        # `\\$` is a literal backslash followed by an anchor.
        self.assertTrue(scan("^x\\\\$")["dollar_anchor"])


class LookaroundTests(unittest.TestCase):
    """`(?:` is a group, `(?=`/`(?!`/`(?<=`/`(?<!` are lookarounds: different things."""

    def test_noncapturing_group_is_not_lookaround(self):
        result = scan("^(?:SRR|ERR)[0-9]+$")
        self.assertTrue(result["noncapturing_group"])
        self.assertEqual(result["lookaround"], [])

    def test_negative_and_positive_lookahead(self):
        self.assertEqual(scan("^(SRR|ERR)[0-9]+(?![\\s\\S])")["lookaround"], ["(?!"])
        self.assertEqual(scan("^x(?=y)")["lookaround"], ["(?="])

    def test_lookbehind(self):
        self.assertEqual(scan("(?<=a)x(?<!b)")["lookaround"], ["(?<=", "(?<!"])

    def test_lookaround_after_a_closed_class(self):
        # The class must not swallow the group syntax: `[a-z](?!x)` has a lookahead.
        result = scan("^[a-z](?![\\s\\S])$")
        self.assertEqual(result["lookaround"], ["(?!"])
        self.assertTrue(result["dollar_anchor"])

    def test_escaped_parenthesis_opens_nothing(self):
        self.assertEqual(scan(r"^\(?\)$")["lookaround"], [])


class EmptyClassTests(unittest.TestCase):
    """The ECMA empty-class idioms `[]` and `[^]`, which PCRE/Python read differently."""

    def test_idioms_detected(self):
        for pattern, expected in (("[]]", "[]"), ("[^]]", "[^]"), ("^a[]b", "[]"),
                                  ("(?!)x[^]y", "[^]")):
            with self.subTest(pattern=pattern):
                self.assertIn(expected, scan(pattern)["empty_class"])

    def test_escaped_bracket_is_not_an_empty_class(self):
        for pattern in (r"[\]]", r"[^\]]", r"(\[\])?", "^[A-Za-z0-9._-]+$"):
            with self.subTest(pattern=pattern):
                self.assertEqual(scan(pattern)["empty_class"], [])

    def test_fhgm_style_host_class_is_not_an_empty_class(self):
        # Shape taken from the FHGM draft's generated IRI pattern.
        self.assertEqual(scan(r"^(?:\[[^\]\t-\r ]+\]|[^/?#@:\[\]]+)$")["empty_class"], [])


class InlineFlagTests(unittest.TestCase):
    def test_flags_detected(self):
        self.assertEqual(scan("(?s).*")["inline_flags"], ["(?s)"])
        self.assertEqual(scan("(?im)^x")["inline_flags"], ["(?im)"])
        self.assertEqual(scan("(?i-s)x")["inline_flags"], ["(?i-s)"])

    def test_groups_are_not_flags(self):
        for pattern in ("(?:a)", "(?=a)", "(?!a)", "(?#comment)", "(?<name>a)", "(?P<n>a)"):
            with self.subTest(pattern=pattern):
                self.assertEqual(scan(pattern)["inline_flags"], [],
                                 f"{pattern} is not an inline flag")

    def test_named_groups_are_reported_separately(self):
        self.assertEqual(scan("(?P<year>[0-9]{4})")["named_group"], ["(?P<name>"])
        self.assertEqual(scan("(?<year>[0-9]{4})")["named_group"], ["(?<name>"])
        self.assertEqual(scan("(?<year>[0-9]{4})")["lookaround"], [])


class WalkerTests(unittest.TestCase):
    def test_field_named_pattern_is_not_a_pattern_keyword(self):
        # specs/010 synonyms.schema.json describes a data field called `pattern`.
        document = {"properties": {"forms": {"additionalProperties": {"properties": {
            "pattern": {"type": "string"}}}}}}
        self.assertEqual(list(census.iter_patterns(document)), [])

    def test_defs_and_keyword_paths_are_both_walked(self):
        document = {"$defs": {"X": {"properties": {"uri": {"pattern": "^u$"}}}},
                    "propertyNames": {"not": {"pattern": "\n"}}}
        found = dict(census.iter_patterns(document))
        self.assertEqual(found, {"/$defs/X/properties/uri/pattern": "^u$",
                                 "/propertyNames/not/pattern": "\n"})

    def test_pointers_escape_slashes_and_tildes(self):
        found = dict(census.iter_patterns({"a/b": {"c~d": {"pattern": "x"}}},
                                          keyed_by_name=True))
        self.assertEqual(list(found), ["/a~1b/c~0d/pattern"])


class SchemaWalkerTests(unittest.TestCase):
    def test_schema_locations_are_walked_but_instance_data_is_ignored(self):
        doc = {"properties": {"pattern": {"pattern": "^real$"}},
               "patternProperties": {"^key$": {"pattern": "^value$"}},
               "examples": [{"pattern": "not a constraint"}],
               "default": {"pattern": "not a constraint"},
               "enum": [{"pattern": "not a constraint"}],
               "x-data": {"pattern": "not a constraint"},
               "allOf": [{"if": {"pattern": "^if$"},
                           "then": {"items": {"pattern": "^item$"}}}]}
        self.assertEqual(dict(census.iter_schema_patterns(doc)), {
            "/properties/pattern/pattern": "^real$",
            "/patternProperties/^key$/pattern": "^value$",
            "/allOf/0/if/pattern": "^if$",
            "/allOf/0/then/items/pattern": "^item$"})


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.baseline = {"fhr.json": [{"pointer": "/properties/a/pattern",
                                       "pattern": "^a$"}]}

    def test_identical_inventory_has_no_problems(self):
        self.assertEqual(census.compare(self.baseline, copy.deepcopy(self.baseline)), [])

    def test_added_pattern_is_a_problem(self):
        current = copy.deepcopy(self.baseline)
        current["fhr.json"].append({"pointer": "/properties/b/pattern", "pattern": "^b$"})
        problems = census.compare(self.baseline, current)
        self.assertEqual(len(problems), 1)
        self.assertIn("gained", problems[0])

    def test_removed_pattern_is_a_problem(self):
        problems = census.compare(self.baseline, {"fhr.json": []})
        self.assertEqual(len(problems), 1)
        self.assertIn("removed", problems[0])

    def test_one_character_change_is_a_problem(self):
        current = copy.deepcopy(self.baseline)
        current["fhr.json"][0]["pattern"] = "^a$$"
        problems = census.compare(self.baseline, current)
        self.assertEqual(len(problems), 1)
        self.assertIn("changed", problems[0])

    def test_option_1_trailing_lookahead_is_caught(self):
        # The exact edit #264 proposes and #270 says is not a no-op on released patterns.
        current = copy.deepcopy(self.baseline)
        current["fhr.json"][0]["pattern"] = "^a$(?!\\n)"
        self.assertEqual(len(census.compare(self.baseline, current)), 1)

    def test_pointer_order_within_a_file_is_ignored(self):
        baseline = {"fhr.json": [{"pointer": "/a", "pattern": "^a$"},
                                 {"pointer": "/b", "pattern": "^b$"}]}
        current = {"fhr.json": list(reversed(baseline["fhr.json"]))}
        self.assertNotEqual(baseline["fhr.json"], current["fhr.json"])  # real reversal
        self.assertEqual(census.compare(baseline, current), [])

    def test_missing_or_extra_file_is_a_problem(self):
        self.assertTrue(any("whole file" in p for p in
                            census.compare(self.baseline, {})))
        self.assertTrue(any("whole file" in p for p in
                            census.compare({}, self.baseline)))


class DigestTests(unittest.TestCase):
    def test_digest_is_stable_and_content_ordered(self):
        files = {"fhr.json": [{"pointer": "/p", "pattern": "^a$"}]}
        self.assertEqual(census.digest(files), census.digest(copy.deepcopy(files)))
        self.assertNotEqual(census.digest(files),
                            census.digest({"fhr.json": [{"pointer": "/p", "pattern": "^b$"}]}))

    def test_only_pointer_and_pattern_are_gated(self):
        """`released_files` drops the analysis keys, so annotations cannot move the digest."""
        rows = [{"pointer": "/p", "pattern": "^a$", "dollar_anchor": True,
                 "lookaround": [], "noncapturing_group": False, "inline_flags": [],
                 "empty_class": [], "named_group": [], "description": "reworded"}]
        stripped = census.released_files({"fhr.json": ("released", "FHR", rows, [])})
        self.assertEqual(stripped, {"fhr.json": [{"pointer": "/p", "pattern": "^a$"}]})
        self.assertEqual(census.digest(stripped),
                         census.digest(self.digest_input))

    def setUp(self):
        self.digest_input = {"fhr.json": [{"pointer": "/p", "pattern": "^a$"}]}


@unittest.skipUnless(yaml is not None, "PyYAML is required to census YAML patterns")
class ReleasedGateEndToEndTests(unittest.TestCase):
    """Run the real script on a scratch copy of the released surface."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        # The scratch repository lives one level down so that its parent is a
        # private directory: the sibling-checkout probe then cannot be confused by
        # anything that already exists in the shared temp dir.
        self.base = Path(directory.name)
        self.root = self.base / "repo"
        for relative, _label in census.RELEASED_SCOPE:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        (self.root / ".github").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BASELINE, self.root / ".github" / "pattern-baseline.json")
        self.contract = self.root / "fhr.json"

    def run_census(self, *extra, env=None):
        environment = dict(os.environ)
        for name in census.ENV_FLAGS:
            environment.pop(name, None)
        environment.update(env or {})
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *extra],
            capture_output=True, text=True, env=environment)

    def patch_pattern(self, mutation):
        document = json.loads(self.contract.read_text())
        mutation(document)
        self.contract.write_text(json.dumps(document, indent=2) + "\n")

    def test_untouched_copy_is_green(self):
        result = self.run_census()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No released pattern added, removed or edited", result.stdout)

    def test_one_character_change_to_a_released_pattern_is_red(self):
        def mutate(document):
            pattern = document["properties"]["seqcol_id"]["pattern"]
            document["properties"]["seqcol_id"]["pattern"] = pattern[:-1]

        self.patch_pattern(mutate)
        result = self.run_census()
        self.assertEqual(result.returncode, 1)
        self.assertIn("released pattern changed", result.stderr)
        self.assertIn("/properties/seqcol_id/pattern", result.stderr)

    def test_option_1_lookahead_on_a_released_pattern_is_red(self):
        self.patch_pattern(lambda document: document["properties"]["seqcol_id"].__setitem__(
            "pattern", document["properties"]["seqcol_id"]["pattern"] + "(?!\\n)"))
        result = self.run_census()
        self.assertEqual(result.returncode, 1)
        self.assertIn("#270/#264", result.stderr)

    def test_gained_pattern_is_red(self):
        self.patch_pattern(lambda document: document["properties"]["dateCreated"].__setitem__(
            "pattern", "^[0-9]{4}$"))
        result = self.run_census()
        self.assertEqual(result.returncode, 1)
        self.assertIn("released pattern set gained", result.stderr)

    def test_removed_pattern_is_red(self):
        def mutate(document):
            del document["properties"]["seqcol_id"]["pattern"]

        self.patch_pattern(mutate)
        result = self.run_census()
        self.assertEqual(result.returncode, 1)
        self.assertIn("released pattern removed", result.stderr)

    def test_missing_released_contract_is_red(self):
        self.contract.unlink()
        result = self.run_census()
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing scoped file", result.stderr)

    def test_unscoped_contract_at_the_root_is_red(self):
        shutil.copyfile(self.contract, self.root / "fhx.json")
        result = self.run_census()
        self.assertEqual(result.returncode, 1)
        self.assertIn("not in the gated scope", result.stderr)
        self.assertIn("fhx.json", result.stderr)

    def test_annotation_only_change_stays_green(self):
        self.patch_pattern(lambda document: document["properties"]["seqcol_id"].__setitem__(
            "description", "reworded by a documentation-only PR"))
        result = self.run_census()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_instance_annotations_are_not_pattern_constraints(self):
        for keyword in ("examples", "default", "const", "enum", "x-extension"):
            with self.subTest(keyword=keyword):
                self.patch_pattern(lambda doc: doc.__setitem__(keyword, [{"pattern": "data"}]))
                result = self.run_census()
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_draft_yaml_is_informational(self):
        target = self.root / "profiles" / "insdc-fhr.yaml"
        target.parent.mkdir()
        target.write_text("pattern: [")
        result = self.run_census()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("invalid YAML", result.stdout)

    def test_malformed_released_yaml_fails_cleanly(self):
        (self.root / "schemas" / "core.yaml").write_text("pattern: [")
        result = self.run_census()
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid YAML", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_unrelated_yaml_does_not_crash(self):
        (self.root / "unrelated").mkdir()
        (self.root / "unrelated" / "note.yaml").write_text("pattern: [")
        result = self.run_census()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_updated_baseline_does_not_claim_unverified_tag_identity(self):
        self.patch_pattern(lambda doc: doc["properties"]["seqcol_id"].__setitem__(
            "pattern", "^changed$"))
        result = self.run_census("--update-baseline")
        self.assertEqual(result.returncode, 0, result.stderr)
        stored = json.loads((self.root / ".github" / "pattern-baseline.json").read_text())
        self.assertNotIn("releasedTag", stored)
        self.assertNotIn("releasedTagNote", stored)
        self.assertEqual(self.run_census().returncode, 0)

    def test_symlinked_sibling_outside_parent_is_informational(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside)
            (target / "fht.json").write_text('{"pattern":"^x$"}')
            (self.root.parent / "FHT-Specification").symlink_to(target, target_is_directory=True)
            result = self.run_census()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(target), result.stdout)

    def test_hand_edited_baseline_is_red(self):
        path = self.root / ".github" / "pattern-baseline.json"
        stored = json.loads(path.read_text())
        stored["files"]["fhr.json"].append({"pointer": "/properties/ghost/pattern",
                                            "pattern": "^x$"})
        path.write_text(json.dumps(stored, indent=2) + "\n")
        result = self.run_census()
        self.assertEqual(result.returncode, 1)
        self.assertIn("internally inconsistent", result.stderr)

    def test_draft_constructs_never_fail_the_build(self):
        profiles = self.root / "profiles"
        profiles.mkdir(parents=True, exist_ok=True)
        (profiles / "insdc-fhr.yaml").write_text(
            "classes:\n  T:\n    slot_usage:\n      uri:\n"
            "        pattern: '^https://example\\.org/[1-9][0-9]*(?![\\s\\S])'\n",
            encoding="utf-8")
        drafts = self.root / "templates" / "cedar" / "drafts"
        drafts.mkdir(parents=True, exist_ok=True)
        (drafts / "fht.schema.json").write_text(json.dumps(
            {"$defs": {"FHT": {"properties": {"sequencingRuns": {"items": {
                "pattern": "^(SRR|ERR|DRR)[0-9]+(?![\\s\\S])"}}}}}}), encoding="utf-8")
        result = self.run_census()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRAFT and proposal scope (informational only)", result.stdout)
        self.assertIn("lookaround", result.stdout)
        self.assertIn("ECMA-262 is the floor", result.stdout)

    def test_update_baseline_refuses_to_run_in_ci(self):
        for flag in ("CI", "GITHUB_ACTIONS"):
            with self.subTest(flag=flag):
                before = (self.root / ".github" / "pattern-baseline.json").read_bytes()
                result = self.run_census("--update-baseline", env={flag: "true"})
                self.assertEqual(result.returncode, 1)
                self.assertIn("refusing to refresh", result.stderr)
                self.assertEqual(before,
                                 (self.root / ".github" / "pattern-baseline.json").read_bytes())

    def test_update_baseline_is_allowed_outside_ci(self):
        result = self.run_census("--update-baseline")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Updated", result.stdout)
        # ...and the file it wrote still passes the plain check.
        self.assertEqual(self.run_census().returncode, 0)

    def test_falsy_ci_markers_are_not_ci(self):
        for flag, value in (("CI", "false"), ("GITHUB_ACTIONS", "0"), ("CI", " ")):
            with self.subTest(**{flag: value}):
                environment = dict(os.environ)
                environment.pop("CI", None)
                environment.pop("GITHUB_ACTIONS", None)
                environment[flag] = value
                result = self.run_census("--update-baseline", env=environment)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_live_probe_is_local_only_and_reports_unverified(self):
        # The scratch root has no sibling FHT/FHGM checkout, and the script must
        # say UNVERIFIED rather than reach for the network.
        result = self.run_census()
        self.assertEqual(result.returncode, 0, result.stderr)
        for type_name in ("FHT", "FHGM"):
            lines = [line for line in result.stdout.splitlines()
                     if line.strip().startswith(type_name + " live DRAFT contract")]
            self.assertEqual(len(lines), 1, result.stdout)
            self.assertIn("UNVERIFIED", lines[0])
            self.assertIn("never fetches", lines[0])

    def test_live_probe_reads_a_sibling_checkout_without_network(self):
        sibling = self.root.parent / "FHT-Specification"
        sibling.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, sibling, True)
        sibling.joinpath("fht.json").write_text(json.dumps(
            {"properties": {"sequencingRuns": {"items": {
                "pattern": "^(SRR|ERR|DRR)[0-9]+(?![\\s\\S])"}}}}), encoding="utf-8")
        result = self.run_census()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FHT live DRAFT contract", result.stdout)
        self.assertIn("1 with lookaround", result.stdout)
        self.assertIn("informational only", result.stdout)

    def test_census_scope_is_offline(self):
        """Importing the script must not pull in an HTTP/network client (#270: no remote reads).

        Only client modules are checked. ``urllib.parse`` is not one: pathlib
        imports it on CPython 3.12, so a bare ``urllib`` prefix test would fail for
        a reason that has nothing to do with the network.
        """
        forbidden = {"urllib.request", "urllib.error", "http", "http.client", "socket",
                     "ssl", "ftplib", "requests", "httpx", "aiohttp"}
        code = ("import sys; before=set(sys.modules);"
                "sys.path.insert(0, {path!r}); import check_pattern_census;"
                "new=set(sys.modules)-before;"
                "print(sorted(m for m in new if m in {forbidden!r}))")
        result = subprocess.run(
            [sys.executable, "-c", code.format(path=str(SCRIPT.parent), forbidden=forbidden)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[]", result.stdout)


class ScopeHygieneTests(unittest.TestCase):
    """Paths must exist, and rule V7 must not leak into the gated scope."""

    def test_every_released_scope_path_exists_in_the_repository(self):
        for relative, label in census.RELEASED_SCOPE:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(),
                                f"{relative} ({label}) is missing from the tree")

    def test_draft_snapshot_paths_exist(self):
        for relative in ("templates/cedar/drafts/fht.schema.json",
                         "templates/cedar/drafts/fhgm-model.schema.json",
                         "profiles/insdc-fhr.yaml", "profiles/agbiodata-fhr.yaml"):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_no_draft_type_is_in_the_gated_released_scope(self):
        for relative, label in census.RELEASED_SCOPE:
            token = relative.lower()
            self.assertNotIn("fht", token)
            self.assertNotIn("fhgm", token)
            self.assertNotIn("FHT", label)
            self.assertNotIn("FHGM", label)

    def test_draft_labels_say_draft(self):
        labels = {relative: label for relative, label in census.DRAFT_SCOPE}
        for relative in ("templates/cedar/drafts/fht.schema.json",
                         "templates/cedar/drafts/fhgm-model.schema.json"):
            self.assertIn("DRAFT", labels[relative])

    def test_live_probes_reference_only_local_paths(self):
        for _type_name, candidates in census.LIVE_DRAFT_PROBES:
            for candidate in candidates:
                self.assertTrue(candidate.startswith("../"), candidate)
                self.assertNotIn("://", candidate)

    @unittest.skipUnless(yaml is not None, "PyYAML is required")
    def test_committed_baseline_matches_the_working_tree(self):
        """The committed baseline is current, so the gate cannot be quietly stale."""
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(ROOT),
                                 "--baseline", str(BASELINE)],
                                capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(yaml is not None, "PyYAML is required (released scope includes YAML)")
    def test_released_surface_carries_no_lookaround(self):
        """Factual snapshot of the released inventory that #270 reported (re-measured)."""
        found = census.expand(ROOT)
        released = [row for entry in found.values() if entry[0] == "released"
                    for row in entry[2]]
        self.assertEqual([row["pointer"] for row in released if row["lookaround"]], [])
        self.assertEqual([row["pointer"] for row in released if row["inline_flags"]], [])
        self.assertEqual([row["pointer"] for row in released if row["empty_class"]], [])


if __name__ == "__main__":
    unittest.main()
