#!/usr/bin/env python3
"""Census every JSON Schema ``pattern`` in the repository and gate the released contracts.

Enforcement point requested by FAIR-bioHeaders-Specification#270.

The policy this script enforces, as stated by the maintainers on 2026-11-18:

    **ECMA-262 is the floor for ``pattern``, the v0.4 lookahead sentence is
    historical not current policy, and no released v0.6.0 contract may be
    widened.**

Read that three ways, because the script deliberately does only two of them:

1. ``docs/SCHEMA-CHANGES-v0.4.md`` still says *"Lookahead workarounds are not
   used because RE2-based validators do not support them."* That line is a
   historical changelog entry, **not** current policy. Current policy is
   ECMA-262, which is also what JSON Schema draft/2020-12 specifies for
   ``pattern``. A negative lookahead such as ``(?![\\s\\S])`` is therefore legal.
2. So this script is an **inventory and drift-detection** tool, not an RE2
   purification tool. **Do not "fix" this by making it fail on lookaheads.**
   That would silently adopt compatibility floor (B) of #270, which the
   maintainers did not choose, and would break the FHT and FHGM drafts and every
   LinkML regeneration that reintroduces ``(?![\\s\\S])``.
3. The released ``pattern`` inventory is gated against its committed digest:
   gain, loss or text edit requires explicit review. This preserves pattern
   bytes, not an engine's accidental acceptance behavior. The recorded #264
   option-3 ruling corrects validators to ECMA-262 semantics without changing
   contracts: ``$`` means the end of the whole string, including when CPython's
   stock ``re`` would accept a position before a final line feed. This census
   neither compiles patterns nor proves ECMA-262 validity or engine conformance.

The draft scope (the byte-pinned FHT and FHGM draft contract snapshots under
``templates/cedar/drafts/``, the draft profiles and proposals, and the
spec-suite contracts) is reported **informationally only** and can never fail
this check: those drafts are drafts, and #270's own conclusion is that their
lookarounds are legitimate under the ECMA-262 floor.

Rule V7 is respected throughout: FHT and FHGM are labelled drafts everywhere in
the output; nothing here assigns them a ``schemaVersion``, a registry row, a w3id
or tag URL, or a toolkit support claim.

No network access. The live owning repositories of the FHT and FHGM drafts are
probed only through local sibling checkouts when one happens to exist; when it
does not, the line is printed as UNVERIFIED rather than fetched, because the
specification's CI must not depend on another repository (a maintainer decision
recorded in #270).

Scope note: this is a census of the ``pattern`` keyword only. ``patternProperties``
keys are regular expressions too and are deliberately out of scope here; adding
them is a follow-up, not an omission to repair silently.

Usage:
    python scripts/check_pattern_census.py                 # census + released gate
    python scripts/check_pattern_census.py --root <tree>    # same, on a scratch tree
    python scripts/check_pattern_census.py --update-baseline
        Refresh .github/pattern-baseline.json after a reviewed, joint-maintainer
        contract change. Refuses to run when a CI environment is detected: only a
        human outside CI may move the released baseline, and the refresh must be
        committed alongside the contract change and explained in the PR.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]

# Gated scope: the released specification surface. The three root JSON contracts
# (they live at the repository root, not under schemas/), the LinkML models they
# are generated from or must agree with, the shared slot models they import, and
# the version registry.
RELEASED_SCOPE = (
    ("fhr.json", "released FHR contract"),
    ("fhp.json", "released FHP contract"),
    ("fhgff3.json", "released FHGFF3 contract"),
    ("fhr_linkml.yml", "FHR LinkML model"),
    ("fhp_linkml.yml", "FHP LinkML model"),
    ("fhgff3_linkml.yml", "FHGFF3 LinkML model"),
    ("schemas/core.yaml", "shared core slot model"),
    ("schemas/shared.yaml", "shared type-independent slot model"),
    ("schemas/versions.json", "contract version registry"),
)

# Informational scope: drafts, proposals and spec-suite contracts. These are
# reported and never gate the build.
DRAFT_SCOPE = (
    ("templates/cedar/drafts/fht.schema.json", "FHT DRAFT contract snapshot"),
    ("templates/cedar/drafts/fhgm-model.schema.json", "FHGM DRAFT model snapshot"),
    ("profiles/insdc-fhr.yaml", "insdc-fhr profile (draft)"),
    ("profiles/agbiodata-fhr.yaml", "agbiodata-fhr profile (draft)"),
    ("mappings/mapping-table.schema.json", "mapping table contract"),
    ("mappings/proposals/assembly-export-context.schema.json",
     "DCMI export-context proposal (draft)"),
    ("assessment/manifest.schema.json", "assessment manifest contract"),
    ("specs/010-fair-header-assessment/contracts/assessment-report.schema.json",
     "spec 010 assessment-report contract"),
    ("specs/010-fair-header-assessment/contracts/rubric.schema.json",
     "spec 010 rubric contract"),
    ("specs/010-fair-header-assessment/contracts/synonyms.schema.json",
     "spec 010 synonyms contract"),
    ("specs/011-jsonld-mapping/contracts/mapping-table.schema.json",
     "spec 011 mapping-table contract"),
    ("specs/013-schemaorg-export/contracts/export-table.schema.json",
     "spec 013 export-table contract"),
)
DRAFT_GLOBS = ("specs/*/contracts/*.json",)

# Deliberately not censused, so that a reader does not mistake the totals for
# "every regex in the tree": .github/schema-baseline*.json (review baselines
# owned by check_schema_drift.py), templates/cedar/*.json (generated authoring
# templates, verified against their source schema by make_cedar.py --check) and
# tests/fixtures/cedar-meta-schemas/*.json (third-party CEDAR meta-schema
# fixtures, not family contracts).
EXCLUDED = (
    ".github/pattern-baseline.json",
    ".github/schema-baseline.json",
    ".github/schema-baseline-fhp.json",
    ".github/schema-baseline-fhgff3.json",
    "templates/cedar/fhr.json",
    "templates/cedar/fhp.json",
    "templates/cedar/fhgff3.json",
    "templates/cedar/fht.json",
    "templates/cedar/fhgm.json",
    "tests/fixtures/cedar-meta-schemas",
)

# The draft contracts are owned by other repositories, so the in-repo
# byte-pinned snapshots under templates/cedar/drafts/ are the verified input
# (their digests are owned by tests/test_cedar.py and scripts/make_cedar.py, not
# re-checked here). These probe entries are an OPTIONAL local-only view of the
# owning repository's own working file: nothing is fetched, and when no sibling
# checkout exists the census prints UNVERIFIED.
LIVE_DRAFT_PROBES = (
    ("FHT", ("../FHT-Specification/fht.json",)),
    ("FHGM", ("../FHGM-Specification/development/model/fhgm-model.schema.json",
              "../FHGM/development/model/fhgm-model.schema.json")),
)

CITATION = "https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/270"
REFRESH_COMMAND = "python scripts/check_pattern_census.py --update-baseline"
ENV_FLAGS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "TF_BUILD", "CIRCLECI")
FLAG_LETTERS = set("aiLmsux")  # PCRE/Python inline flags; ECMA-262 has none


class CensusError(Exception):
    """A released-scope file could not be read or parsed."""


def load_document(path):
    """Read JSON strictly (unique keys, finite values) or parse a YAML model."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject)
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - CI installs PyYAML
        raise CensusError(
            f"{path}: PyYAML is required to census YAML patterns "
            "(pip install -r requirements-linkml.txt)"
        ) from error
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise CensusError(f"{path}: invalid YAML: {error}") from error


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CensusError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject(value):
    raise CensusError(f"invalid JSON constant: {value}")


def escape(token):
    return str(token).replace("~", "~0").replace("/", "~1")


# Keywords whose child mapping is keyed by *data-level names*, not by schema
# keywords. Without this, a contract that describes a field called "pattern"
# (specs/010 synonyms.schema.json does) would be misread as carrying a pattern
# keyword.
NAME_KEYED = {"properties", "patternProperties", "$defs", "definitions",
              "dependentSchemas", "dependencies"}


def iter_patterns(node, pointer="", keyed_by_name=False):
    """Yield (pointer, value) for every ``pattern`` keyword, resolving nothing.

    Pointers are reported exactly as they appear in the file: ``$ref`` targets of
    the shared imports are not followed, because #270 asks where a pattern is
    written, not where it applies.
    """
    if isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_patterns(value, f"{pointer}/{index}", keyed_by_name=False)
        return
    if not isinstance(node, dict):
        return
    if keyed_by_name:
        for name, value in node.items():
            yield from iter_patterns(value, pointer + "/" + escape(name))
        return
    for key, value in node.items():
        child = pointer + "/" + escape(key)
        if key == "pattern":
            yield child, value
        elif key in NAME_KEYED:
            yield from iter_patterns(value, child, keyed_by_name=True)
        else:
            yield from iter_patterns(value, child)



# Only schema-valued keywords are traversed in JSON Schema documents. In
# particular examples/default/const/enum and unknown extensions are instances,
# not nested schemas. patternProperties VALUES are schemas; its regex KEYS are
# outside this keyword-only census.
SCHEMA_MAPS = {"properties", "patternProperties", "$defs", "definitions",
               "dependentSchemas", "dependencies"}
SCHEMA_ARRAYS = {"allOf", "anyOf", "oneOf", "prefixItems"}
SCHEMA_SINGLES = {"additionalProperties", "unevaluatedProperties", "propertyNames",
                  "items", "additionalItems", "unevaluatedItems", "contains",
                  "not", "if", "then", "else", "contentSchema"}


def iter_schema_patterns(node, pointer=""):
    """Yield written pattern keywords in schema locations, without following refs."""
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        child = pointer + "/" + escape(key)
        if key == "pattern":
            yield child, value
        elif key in SCHEMA_MAPS and isinstance(value, dict):
            for name, schema in value.items():
                yield from iter_schema_patterns(schema, child + "/" + escape(name))
        elif key in SCHEMA_ARRAYS or (key == "items" and isinstance(value, list)):
            if isinstance(value, list):
                for index, schema in enumerate(value):
                    yield from iter_schema_patterns(schema, f"{child}/{index}")
        elif key in SCHEMA_SINGLES:
            yield from iter_schema_patterns(value, child)


def scan(pattern):
    """Lexically classify the dialect-relevant constructs in one regex string.

    Returns a dict of booleans and lists. This is a scanner, not a regex parser:
    it tracks backslash escapes and character-class state so that ``$`` inside a
    class and an escaped ``\\$`` are not counted as anchors, and ``(?:`` is not
    counted as a lookahead. It is deliberately conservative and never raises.
    """
    result = {
        "dollar_anchor": False,
        "lookaround": [],
        "noncapturing_group": False,
        "inline_flags": [],
        "empty_class": [],
        "named_group": [],
    }
    index = 0
    length = len(pattern)
    in_class = False
    while index < length:
        char = pattern[index]
        if char == "\\":
            index += 2  # an escaped character is never a construct or a class
            continue
        if in_class:
            if char == "]":
                in_class = False
            index += 1
            continue
        if char == "$":
            result["dollar_anchor"] = True
            index += 1
            continue
        if char == "[":
            negated = index + 1 < length and pattern[index + 1] == "^"
            close = index + 2 if negated else index + 1
            if close < length and pattern[close] == "]":
                # ECMA-262 reads [] / [^] as an (empty or everything-matching)
                # closed class; PCRE and Python read the next ] as its first
                # member. That reading difference is the point of the census.
                result["empty_class"].append("[^]" if negated else "[]")
                index = close + 1
                continue
            in_class = True
            index += 1
            continue
        if char == "(" and index + 1 < length and pattern[index + 1] == "?":
            body = pattern[index + 2:index + 6]
            if body.startswith(":"):
                result["noncapturing_group"] = True
                index += 3
                continue
            if body.startswith("!") or body.startswith("="):
                result["lookaround"].append("(?!" if body[0] == "!" else "(?=")
                index += 3
                continue
            if body.startswith("<=") or body.startswith("<!"):
                result["lookaround"].append("(?<=" if body[0:2] == "<=" else "(?<!")
                index += 4
                continue
            if body.startswith("<"):
                end = pattern.find(">", index + 3)
                result["named_group"].append("(?<name>")
                index = end + 1 if end != -1 else index + 3
                continue
            if body.startswith("P<"):
                end = pattern.find(">", index + 3)
                result["named_group"].append("(?P<name>")
                index = end + 1 if end != -1 else index + 3
                continue
            letters = []
            cursor = index + 2
            while cursor < length and (pattern[cursor] in FLAG_LETTERS or pattern[cursor] == "-"):
                letters.append(pattern[cursor])
                cursor += 1
            if letters and cursor < length and pattern[cursor] in (")", ":", "-"):
                result["inline_flags"].append("(?" + "".join(letters) + ")")
                index = cursor + 1
                continue
        index += 1
    return result


def inventory(root, relative):
    """Census one file: (rows, anomalies). rows carry the scan properties."""
    path = root / relative
    if not path.is_file():
        raise CensusError(f"missing scoped file: {relative}")
    try:
        document = load_document(path)
    except (CensusError, ValueError, OSError) as error:
        raise CensusError(f"{relative}: unreadable: {error}") from error
    rows = []
    anomalies = []
    walker = iter_patterns if path.suffix in {".yaml", ".yml"} else iter_schema_patterns
    for pointer, value in walker(document):
        if not isinstance(value, str):
            anomalies.append(f"{pointer}: pattern is not a string ({type(value).__name__})")
            continue
        rows.append({"pointer": pointer, "pattern": value, **scan(value)})
    rows.sort(key=lambda row: row["pointer"])
    return rows, anomalies


def draft_paths(root):
    """Draft/proposal scope: the named files plus any spec-suite contract found."""
    paths = list(DRAFT_SCOPE)
    seen = {relative for relative, _label in paths}
    for glob in DRAFT_GLOBS:
        for path in sorted(root.glob(glob)):
            relative = path.relative_to(root).as_posix()
            if relative in seen or any(relative.startswith(ex) for ex in EXCLUDED):
                continue
            if not path.is_file():
                continue
            paths.append((relative, "spec-suite contract"))
            seen.add(relative)
    return paths


def expand(root):
    """Every scoped path that exists: {relative path: (scope, label, rows, anomalies)}.

    A released-scope file that is missing or unparsable raises :class:`CensusError`
    (silently losing a gated contract is the failure mode this script exists to
    prevent). A draft-scope file that cannot be read is recorded as an anomaly
    instead: drafts never gate the build.
    """
    found = {}
    for relative, label in RELEASED_SCOPE:
        rows, anomalies = inventory(root, relative)
        found[relative] = ("released", label, rows, anomalies)
    for relative, label in draft_paths(root):
        path = root / relative
        if relative in found or not path.is_file():
            continue
        try:
            rows, anomalies = inventory(root, relative)
        except CensusError as error:
            rows, anomalies = [], [f"unreadable: {error}"]
        found[relative] = ("draft", label, rows, anomalies)
    return found


def released_files(found):
    return {
        relative: [{"pointer": row["pointer"], "pattern": row["pattern"]}
                   for row in rows]
        for relative, (_scope, _label, rows, _anomalies) in sorted(found.items())
        if _scope == "released"
    }


def digest(files):
    payload = json.dumps(files, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_baseline(found):
    files = released_files(found)
    return {
        "baselineVersion": 1,
        "note": (
            "Committed inventory of every JSON Schema `pattern` in the released "
            "specification surface. Refresh only through a reviewed contract "
            "change: python scripts/check_pattern_census.py --update-baseline "
            "(refuses to run in CI). See " + CITATION + "."
        ),
        "policy": (
            "ECMA-262 is the floor for `pattern`; the v0.4 lookahead sentence is "
            "historical, not current policy; no released contract may be widened."
        ),
        "policySource": CITATION,
        "scope": sorted(relative for relative, entry in found.items()
                        if entry[0] == "released"),
        "files": files,
        "patternCount": sum(len(rows) for rows in files.values()),
        "digest": digest(files),
    }


def compare(baseline_files, current_files):
    """Released-scope drift messages: gained, lost or edited patterns."""
    problems = []
    for relative in sorted(set(baseline_files) | set(current_files)):
        before = {row["pointer"]: row["pattern"] for row in baseline_files.get(relative, [])}
        after = {row["pointer"]: row["pattern"] for row in current_files.get(relative, [])}
        if relative not in baseline_files:
            problems.append(f"{relative}: released scope gained a whole file")
        elif relative not in current_files:
            problems.append(f"{relative}: released scope lost a whole file")
        for pointer in sorted(set(after) - set(before)):
            problems.append(
                f"{relative}: {pointer}: released pattern set gained "
                f"{after[pointer]!r} (a new constraint on a published contract)"
            )
        for pointer in sorted(set(before) - set(after)):
            problems.append(
                f"{relative}: {pointer}: released pattern removed {before[pointer]!r} "
                "(removing a constraint widens the accepted value set)"
            )
        for pointer in sorted(set(before) & set(after)):
            if before[pointer] != after[pointer]:
                problems.append(
                    f"{relative}: {pointer}: released pattern changed "
                    f"{before[pointer]!r} -> {after[pointer]!r}; review this pattern-text "
                    "change under the contract change process (#270/#264)"
                )
    return problems


def on_released_surface(relative):
    """True for paths where a *released* contract lives: the repository root and
    ``schemas/``. A pattern-bearing document there that no scope table lists must
    not be skipped quietly: that is how a newly published contract would escape
    the gate."""
    path = PurePosixPath(relative)
    return (path.parent == PurePosixPath(".") and path.suffix in {".json", ".yaml", ".yml"}
            or path.parent == PurePosixPath("schemas"))


def unscoped(root, found):
    """Pattern-bearing documents outside every scope table, split by surface.

    Returns (on the released surface, elsewhere, unreadable on the released
    surface). The first and third gate the build: they are how a newly published
    contract at the repository root or under ``schemas/`` could otherwise slip
    past the drift check unnoticed.
    """
    listed, elsewhere, unreadable = [], [], []
    for path in sorted(root.rglob("*")):
        if path.suffix not in {".json", ".yaml", ".yml"} or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith(".git/") or relative in found:
            continue
        if any(relative == ex or relative.startswith(ex + "/") for ex in EXCLUDED):
            continue
        try:
            rows, _anomalies = inventory(root, relative)
        except CensusError as error:
            if on_released_surface(relative):
                unreadable.append(f"{relative}: unparsable ({error})")
            continue
        if not rows:
            continue
        (listed if on_released_surface(relative) else elsewhere).append(relative)
    return listed, elsewhere, unreadable


def describe(relative, rows):
    """One summary line per file, with the construct counts #270 asked for."""
    unit = "pattern " if len(rows) == 1 else "patterns"
    return (
        f"{relative:62s} {len(rows):3d} {unit}  "
        f"$-anchor {sum(1 for r in rows if r['dollar_anchor']):3d}   "
        f"lookaround {sum(1 for r in rows if r['lookaround']):3d}   "
        f"(?:) group {sum(1 for r in rows if r['noncapturing_group']):3d}   "
        f"inline flag {sum(1 for r in rows if r['inline_flags']):3d}   "
        f"empty class {sum(1 for r in rows if r['empty_class']):3d}"
    )


def ci_environment():
    """Names of CI markers set in this environment, so a refresh can be refused."""
    return sorted(name for name in ENV_FLAGS
                  if os.environ.get(name, "").strip().lower() not in ("", "0", "false"))


def live_draft_lines(root):
    """Local-only probe of the owning repositories' live draft contracts."""
    lines = []
    for type_name, candidates in LIVE_DRAFT_PROBES:
        hit = None
        for candidate in candidates:
            path = (root / candidate).resolve()
            if path.is_file():
                hit = path
                break
        if hit is None:
            lines.append(
                f"  {type_name} live DRAFT contract in its owning repository: UNVERIFIED "
                "(no local sibling checkout; this check never fetches another repository)"
            )
            continue
        try:
            rows, _anomalies = inventory(hit.parent, hit.name)
        except CensusError as error:
            lines.append(f"  {type_name} live DRAFT contract {hit}: UNVERIFIED ({error})")
            continue
        lookaround = [(r["pointer"], r["pattern"]) for r in rows if r["lookaround"]]
        try:
            display = hit.relative_to(root.parent)
        except ValueError:
            display = hit
        lines.append(
            f"  {type_name} live DRAFT contract {display}: "
            f"{len(rows)} patterns, {len(lookaround)} with lookaround "
            "(local sibling checkout; NOT verified against the owning repository's "
            "main, so informational only)"
        )
        for pointer, value in lookaround:
            lines.append(f"      {pointer} = {value}")
    return lines


def main():
    parser = argparse.ArgumentParser(
        description="Census schema `pattern` values and gate the released contracts (#270).")
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="repository tree to census (default: this repository)")
    parser.add_argument("--baseline", type=Path, default=None,
                        help="committed released-pattern baseline "
                             "(default: <root>/.github/pattern-baseline.json)")
    parser.add_argument("--update-baseline", action="store_true",
                        help="rewrite the baseline from the census (refuses to run in CI)")
    args = parser.parse_args()
    root = args.root.resolve()
    baseline_path = args.baseline.resolve() if args.baseline else (
        root / ".github" / "pattern-baseline.json")

    try:
        found = expand(root)
    except CensusError as error:
        print(f"pattern census failed: {error}", file=sys.stderr)
        return 1

    listed, elsewhere, unreadable = unscoped(root, found)
    if listed or unreadable:
        print("pattern census failed: a pattern-bearing document on the released surface "
              "(repository root or schemas/) is not in the gated scope:", file=sys.stderr)
        for text in listed + unreadable:
            print(f"  {text}", file=sys.stderr)
        print("Add it to RELEASED_SCOPE in scripts/check_pattern_census.py so a published "
              "contract cannot escape the drift gate (or move it off the released surface), "
              "then refresh the baseline outside CI.", file=sys.stderr)
        return 1

    released_anomalies = sorted(
        f"{relative}: {text}" for relative, (scope, _label, _rows, texts) in found.items()
        if scope == "released" for text in texts)
    if released_anomalies:
        print("pattern census failed: malformed pattern keywords in the released scope:",
              file=sys.stderr)
        for text in released_anomalies:
            print(f"  {text}", file=sys.stderr)
        return 1
    draft_anomalies = sorted(
        f"{relative}: {text}" for relative, (scope, _label, _rows, texts) in found.items()
        if scope == "draft" for text in texts)

    baseline_payload = build_baseline(found)
    current = baseline_payload["files"]

    if args.update_baseline:
        blocked = ci_environment()
        if blocked:
            print(
                "refusing to refresh the released-pattern baseline inside CI "
                f"(detected {', '.join(blocked)}): {REFRESH_COMMAND} is a human action "
                "taken outside CI after a reviewed contract change, and the refreshed "
                "baseline must be committed with that change.",
                file=sys.stderr,
            )
            return 1
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(baseline_payload, indent=2, ensure_ascii=False,
                                            allow_nan=False) + "\n", encoding="utf-8")
        print(f"Updated {baseline_path} ({baseline_payload['patternCount']} released patterns, "
              f"{baseline_payload['digest']}); review and commit it with the contract change.")
        return 0

    print("Pattern census (FAIR-bioHeaders-Specification#270)")
    print("=" * 78)
    print("Policy: ECMA-262 is the floor for `pattern`. The v0.4 changelog sentence")
    print("about lookahead workarounds is historical, not current policy, so lookaround")
    print("patterns are counted and reported, never rejected. The released contracts")
    print("are gated against a committed digest: no released pattern may be added,")
    print("removed or edited without review. Engine conformance is checked separately.")
    print("=" * 78)

    for scope, heading in (("released", "RELEASED scope (gated by the baseline digest)"),
                           ("draft", "DRAFT and proposal scope (informational only)")):
        paths = sorted(p for p, (s, *_rest) in found.items() if s == scope)
        print(f"\n{heading}")
        if not paths:
            print("  (no files found)")
            continue
        total = {}
        for relative in paths:
            _scope, label, rows, _anomalies = found[relative]
            print(f"  {describe(relative, rows)}  [{label}]")
            for key in ("dollar_anchor", "lookaround", "noncapturing_group",
                        "inline_flags", "empty_class", "named_group"):
                total[key] = total.get(key, 0) + sum(1 for row in rows if row[key])
        print(f"  {'SUBTOTAL ' + scope:62s} "
              f"{sum(len(found[p][2]) for p in paths):3d} patterns   "
              + "   ".join(
                  f"{key.replace('_', ' ')} {total.get(key, 0):3d}"
                  for key in ("dollar_anchor", "lookaround", "noncapturing_group",
                              "inline_flags", "empty_class", "named_group")))

    print("\nConstruct detail (informational; never fails the build)")
    detail = [(relative, row) for relative in sorted(found)
              for row in found[relative][2]
              if row["lookaround"] or row["inline_flags"] or row["empty_class"]
              or row["named_group"]]
    if not detail:
        print("  no lookaround, inline-flag, empty-class or named-group constructs")
    for relative, row in detail:
        scope = found[relative][0]
        marks = []
        if row["lookaround"]:
            marks.append("lookaround " + ",".join(sorted(set(row["lookaround"]))))
        if row["inline_flags"]:
            marks.append("inline flag " + ",".join(sorted(set(row["inline_flags"]))))
        if row["empty_class"]:
            marks.append("empty class " + ",".join(sorted(set(row["empty_class"]))))
        if row["named_group"]:
            marks.append("named group " + ",".join(sorted(set(row["named_group"]))))
        print(f"  [{scope:8s}] {relative} {row['pointer']}")
        print(f"             {'; '.join(marks)}")
        print(f"             {row['pattern']!r}")

    if draft_anomalies:
        print("\nDraft-scope notes (informational)")
        for text in draft_anomalies:
            print(f"  {text}")

    print("\nPattern-bearing documents outside both scope tables (informational; not family "
          "contracts, see EXCLUDED)")
    if not elsewhere:
        print("  none")
    else:
        for relative in elsewhere:
            print(f"  {relative}")

    print("\nDraft contracts owned by other repositories")
    print("  FHT and FHGM are drafts under rule V7: no schemaVersion, registry row,")
    print("  w3id or tag URL, and no support claim is made or implied here.")
    for line in live_draft_lines(root):
        print(line)

    if not baseline_path.is_file():
        print(f"\npattern census failed: no baseline at {baseline_path}. Create one outside CI "
              f"with: {REFRESH_COMMAND}", file=sys.stderr)
        return 1
    try:
        stored = load_document(baseline_path)
    except (CensusError, ValueError, OSError) as error:
        print(f"pattern census failed: {baseline_path}: unreadable: {error}", file=sys.stderr)
        return 1
    stored_files = stored.get("files")
    if not isinstance(stored_files, dict):
        print(f"pattern census failed: {baseline_path} has no `files` inventory", file=sys.stderr)
        return 1
    stored_digest = stored.get("digest")
    recomputed = digest(stored_files)
    if stored_digest != recomputed:
        print(f"pattern census failed: {baseline_path} is internally inconsistent: recorded "
              f"digest {stored_digest} != recomputed {recomputed}. The baseline itself was "
              "edited by hand; regenerate it outside CI.", file=sys.stderr)
        return 1

    problems = compare(stored_files, current)
    released_count = sum(len(rows) for rows in current.values())
    if problems:
        print(f"\nRELEASED PATTERN DRIFT: {baseline_path} vs {root} "
              f"({len(problems)} problems)", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print("No released contract may be widened or narrowed by a pattern edit; that is a "
              "contract change with its own versioning and release cycle. If the change really "
              f"is reviewed and approved, refresh the baseline as a human outside CI with "
              f"`{REFRESH_COMMAND}` and commit both files together.", file=sys.stderr)
        return 1
    print(f"\nReleased gate: {released_count} patterns across {len(current)} files match the "
          f"baseline {baseline_path.name} ({stored_digest}). No released pattern added, "
          "removed or edited.")
    print("Draft constructs above are informational: ECMA-262 is the floor (#270).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
