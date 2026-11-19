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


    def test_linkml_instances_are_not_constraints(self):
        """The other traversal: a LinkML slot's `examples` is prose, not a pattern.

        inventory() picks iter_patterns for .yaml/.yml and iter_schema_patterns for
        .json, so the instance-data exclusion has two implementations and each needs
        its own test. Naming this one in a review reply before it existed is what
        forced it: the claim was checked, found false, and then made true.
        """
        document = {"slots": {"uri": {"pattern": "^https://x$",
                                      "examples": [{"pattern": "illustrative"}],
                                      "description": "text"}},
                    "classes": {"T": {"attributes": {"n": {"pattern": "^[0-9]+$"}}}},
                    "name": "model"}
        self.assertEqual(dict(census.iter_patterns(document)), {
            "/slots/uri/pattern": "^https://x$",
            "/classes/T/attributes/n/pattern": "^[0-9]+$"})
        # a field legitimately *named* pattern is still just a name in LinkML too
        nested = {"classes": {"T": {"attributes": {"pattern": {"type": "string"}}}}}
        self.assertEqual(list(census.iter_patterns(nested)), [])


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
        self.assertIn("no released pattern added, removed or edited", result.stdout)
        self.assertIn("11 governed", result.stdout)

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
        self.assertIn("not registered in the baseline", result.stderr)
        self.assertIn("fhx.json", result.stderr)

    def test_unscoped_contract_without_patterns_is_RED_not_out_of_scope(self):
        """Replaced: this test used to assert exit 0, i.e. it pinned finding 1 as design.

        A pattern-free contract on the released surface is exactly the case the governed
        FILE set exists to catch, so the expectation is inverted rather than relaxed.
        """
        (self.root / "fhx.json").write_text('{"type":"string"}')
        result = self.run_census()
        self.assertEqual(result.returncode, 1,
                         "a pattern-free root contract must not pass the gate")
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

    def test_malformed_draft_yaml_fails_closed(self):
        """Changed from `is_informational`: unreadable is not the same as harmless.

        Copilot asked for a quiet informational note here; the maintainer instruction for
        this round was to fail closed, and that is what this asserts. A draft's *content*
        (lookarounds and friends) is still purely informational — see
        test_draft_constructs_never_fail_the_build. The line is content vs. coverage, not
        released vs. draft.
        """
        target = self.root / "profiles" / "insdc-fhr.yaml"
        target.parent.mkdir()
        target.write_text("pattern: [")
        result = self.run_census()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("invalid YAML", result.stderr)
        self.assertIn("could not be censused", result.stderr)
        self.assertNotIn("Traceback", result.stderr + result.stdout)

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
            if token in {"fht.json", "fht_linkml.yml"}:
                registry = json.loads((ROOT / 'schemas/versions.json').read_text())
                self.assertEqual(registry['preRelease'], 'v0.7.0')
                self.assertNotIn('FHT', registry['releases']['v0.6.0'])
                continue  # Explicit new publication candidate, not an accidental draft promotion.
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
        released = [row for name, entry in found.items() if entry[0] == "released"
                    and name not in {'fht.json', 'fht_linkml.yml'} for row in entry[2]]
        self.assertEqual([row["pointer"] for row in released if row["lookaround"]], [])
        self.assertEqual([row["pointer"] for row in released if row["inline_flags"]], [])
        self.assertEqual([row["pointer"] for row in released if row["empty_class"]], [])


if __name__ == "__main__":
    unittest.main()


# The scratch tree copies the real governed surface, which includes YAML models,
# so this class needs PyYAML like ReleasedGateEndToEndTests does. Without the
# guard these tests report the missing dependency as a census defect, which is
# exactly the fail-closed behaviour they are supposed to be testing past.
@unittest.skipUnless(yaml is not None, "PyYAML is required (released scope includes YAML)")
class GovernedFileDiscoveryTests(unittest.TestCase):
    """The baseline must be the authority on WHICH FILES are governed, not on which
    files happen to contain a `pattern` (PR #272 review, finding 1).

    Both files under test here are pattern-free, so a gate keyed on pattern content
    cannot see them at all.
    """

    PATTERN_FREE_SCHEMA = (
        '{"$schema":"https://json-schema.org/draft/2020-12/schema",'
        '"$id":"https://example.org/fhx.json","title":"FHX","type":"object",'
        '"properties":{"nothing":{"type":"string"}}}')

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.root = self.base / "repo"
        for relative, _label in census.RELEASED_SCOPE:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        # The real repository also carries a root-level YAML that is data, not a
        # contract (fhr_mappings.yml): the discovery rule sees it, so a faithful
        # scratch tree has to carry it too.
        for extra in ("fhr_mappings.yml",):
            if (ROOT / extra).is_file():
                shutil.copyfile(ROOT / extra, self.root / extra)
        (self.root / ".github").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BASELINE, self.root / ".github" / "pattern-baseline.json")

    def run_census(self, *extra, env=None):
        environment = dict(os.environ)
        for name in census.ENV_FLAGS:
            environment.pop(name, None)
        environment.update(env or {})
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *extra],
                              capture_output=True, text=True, env=environment)

    def test_a_pattern_free_root_contract_fails_the_gate(self):
        """Case (a): the reviewer's exact probe file."""
        (self.root / "fhx.json").write_text(self.PATTERN_FREE_SCHEMA, encoding="utf-8")
        result = self.run_census()
        self.assertEqual(result.returncode, 1,
                         f"expected RED, got exit {result.returncode}:\n{result.stdout}")
        self.assertIn("fhx.json", result.stderr)
        self.assertIn("not registered", result.stderr.lower() + result.stdout.lower())

    def test_a_registered_governed_file_that_disappears_fails_the_gate(self):
        """Case (b): the other direction — deleted or unscoped, not just added."""
        (self.root / "fhx.json").write_text(self.PATTERN_FREE_SCHEMA, encoding="utf-8")
        refresh = self.run_census("--update-baseline")
        self.assertEqual(refresh.returncode, 0, refresh.stdout + refresh.stderr)
        stored = json.loads((self.root / ".github" / "pattern-baseline.json").read_text())
        self.assertIn("fhx.json", {entry["path"] for entry in stored["governedFiles"]})
        (self.root / "fhx.json").unlink()
        result = self.run_census()
        self.assertEqual(result.returncode, 1,
                         f"expected RED, got exit {result.returncode}:\n{result.stdout}")
        self.assertIn("fhx.json", result.stderr)

    def test_a_pattern_free_file_can_be_excluded_only_by_name_with_a_reason(self):
        """Case (c): this is a registration requirement, not a blanket ban."""
        (self.root / "notes.json").write_text(
            json.dumps({"description": "release notes data", "count": 2}), encoding="utf-8")
        excluded = self.run_census("--update-baseline", "--exclude",
                                   "notes.json::root-level data file, not a contract")
        self.assertEqual(excluded.returncode, 0, excluded.stdout + excluded.stderr)
        stored = json.loads((self.root / ".github" / "pattern-baseline.json").read_text())
        entries = {entry["path"]: entry for entry in stored["excludedFiles"]}
        self.assertIn("notes.json", entries)
        self.assertTrue(entries["notes.json"]["reason"].strip())
        self.assertNotIn("notes.json", {e["path"] for e in stored["governedFiles"]})
        self.assertEqual(self.run_census().returncode, 0, "registered exclusion must pass")
        # and an exclusion without a reason is refused rather than accepted silently
        bare = self.run_census("--update-baseline", "--exclude", "notes.json")
        self.assertEqual(bare.returncode, 2 if bare.returncode == 2 else 1)
        self.assertIn("reason", (bare.stderr + bare.stdout).lower())

    def test_a_governed_file_can_never_be_excluded_away(self):
        """A scope that shrinks to dodge a false positive has stopped being a gate."""
        for path in ("fhr.json", "schemas/core.yaml"):
            with self.subTest(path=path):
                result = self.run_census("--update-baseline",
                                         "--exclude", f"{path}::not interesting")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(path, result.stderr + result.stdout)

    def test_baseline_records_and_digests_the_governed_set(self):
        refresh = self.run_census("--update-baseline")
        self.assertEqual(refresh.returncode, 0, refresh.stdout + refresh.stderr)
        stored = json.loads((self.root / ".github" / "pattern-baseline.json").read_text())
        missing = [key for key in ("governedFiles", "governedFileDigest", "excludedFiles",
                                   "discoveryRule") if key not in stored]
        self.assertEqual(missing, [], f"baseline omits {missing}")  # do not dump the file
        self.assertEqual(stored["governedFileDigest"], census.digest(stored["governedFiles"]))
        paths = {entry["path"] for entry in stored["governedFiles"]}
        self.assertEqual(paths, {relative for relative, _label in census.RELEASED_SCOPE},
                         "the explicit list is a seed: every seed file stays governed")
        # tamper: drop a governed entry without re-digesting
        stored["governedFiles"] = stored["governedFiles"][1:]
        (self.root / ".github" / "pattern-baseline.json").write_text(
            json.dumps(stored, indent=2) + "\n", encoding="utf-8")
        result = self.run_census()
        self.assertEqual(result.returncode, 1)
        self.assertIn("governed", result.stderr)

    def test_discovery_rule_finds_the_real_repository_surface(self):
        discovered = census.discover_governed_surface(ROOT)
        for relative, _label in census.RELEASED_SCOPE:
            self.assertIn(relative, discovered, relative)
        self.assertIn("fhr_mappings.yml", discovered,
                      "a root-level YAML is on the surface; it is excluded by name, "
                      "not discovered-away")
        self.assertNotIn("examples/minimal.fhr.yaml", discovered)
        self.assertNotIn("templates/cedar/fhr.json", discovered)
        self.assertNotIn("conformance/manifest.json", discovered)

    def test_output_labels_its_denominators(self):
        """#271 counts a broader regex scope; every number here must name its own."""
        result = self.run_census()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Counting scope", result.stdout)
        self.assertIn("keyword `pattern` only", result.stdout)
        self.assertIn("entries = one per file+JSON pointer", result.stdout)
        self.assertIn("distinct strings", result.stdout)
        self.assertIn("Subtotal, the three released contracts only", result.stdout)
        self.assertIn("59 entries", result.stdout)   # fhr 10 + fhp 23 + fhgff3 26
        self.assertIn("Discovery rule:", result.stdout)

    def test_committed_baseline_registers_the_whole_surface(self):
        """The shipped baseline must be internally complete against its own rule."""
        stored = json.loads(BASELINE.read_text())
        registered = ({entry["path"] for entry in stored["governedFiles"]}
                      | {entry["path"] for entry in stored["excludedFiles"]})
        self.assertEqual(registered, set(census.discover_governed_surface(ROOT)),
                         "every discovered surface document is governed or excluded by name")

    def test_governed_set_is_exactly_the_released_types_and_holds_no_draft(self):
        """Rule V7, enforced structurally: the registry decides what is governed.

        The governed set must equal the seed plus every contract `schemas/versions.json`
        names as released, and it must never contain a draft type — so a future FHT or
        FHGM contract cannot be pulled into the released gate by editing one tuple.
        """
        stored = json.loads(BASELINE.read_text())
        governed = {entry["path"] for entry in stored["governedFiles"]}
        self.assertEqual(governed, census.mandatory_governed(ROOT))
        _current, _pre, files = census.registry(ROOT)
        self.assertTrue(files, "the registry must name the released types")
        self.assertTrue(set(files.values()) <= governed)
        for path in sorted(governed):
            token = path.lower()
            if token in {'fht.json', 'fht_linkml.yml'}:
                self.assertEqual(_pre, 'v0.7.0')
                self.assertEqual(files['FHT'], 'fht.json')
                continue
            self.assertNotIn("fht", token)
            self.assertNotIn("fhgm", token)
            self.assertNotIn("draft", token)
        for entry in stored["excludedFiles"]:
            self.assertNotIn(entry["path"], governed,
                             "a file is governed or excluded, never both")
            self.assertTrue(str(entry["reason"]).strip(), "an exclusion needs a reason")
