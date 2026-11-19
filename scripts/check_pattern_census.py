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

Two things are gated, not one:

1. **Which files are governed.** The released surface is *discovered by rule*
   (see :data:`DISCOVERY_RULE`) — not enumerated by hand — and ``.github/
   pattern-baseline.json`` is the authority on the registration: every discovered
   document must appear there either in ``governedFiles`` or in ``excludedFiles``
   **by name, with a reason**. A newly discovered file that is registered nowhere
   fails; a governed file the rule no longer discovers fails; an exclusion whose
   reason is blank fails; and a file named by ``RELEASED_SCOPE`` or by
   ``schemas/versions.json`` can never be excluded at all. This is the fix for the
   hole PR #272 finding 1 reported: the first version decided scope by asking
   "does this file contain a `pattern`?", so **a brand-new contract with no pattern
   in it passed the gate**, and both sides of the comparison were derived from the
   same hand-written tuple, which can never discover a file it does not already
   name. Note the direction of the rule: content is optional, registration is not.
2. **What each governed file asserts.** The ``pattern`` value at every JSON pointer,
   compared against the committed digest. Any gain, loss or edit fails the build.
   An edit *may* be value-preserving (``^[a]$`` and ``^(?:[a])$`` accept the same
   language), but this check cannot tell a provable rewrite from a widening, so every
   edit is gated. #264's ``$(?!\\n)`` is the standing example of an edit that looks
   equivalent and is not: under the toolkit's CPython ``re``, ``$`` also matches
   before a trailing line feed, so the lookahead newly rejects such a value, whereas
   under a strict ECMA-262 reading the two forms coincide. Implementation behaviour
   and the recorded ECMA ruling are different claims and are kept apart here.

The draft scope (the byte-pinned FHT and FHGM draft contract snapshots under
``templates/cedar/drafts/``, the draft profiles and proposals, and the
spec-suite contracts) is reported **informationally as to content**: a lookaround,
an inline flag or an empty-class idiom in a draft can never fail this check, because
#270's conclusion is that they are legitimate under the ECMA-262 floor. What a
scoped file *can* fail on is being unreadable: a draft whose YAML does not parse
fails closed with a named error and a non-zero exit, because a census that skips a
file it cannot open and then prints a clean total is asserting coverage it does not
have. (The Copilot thread proposed leaving that informational too; the maintainer
instruction for this round was to fail closed, and the content/coverage line above
is what reconciles the two.)

Rule V7 is respected throughout: FHT and FHGM are labelled drafts everywhere in
the output; nothing here assigns them a ``schemaVersion``, a registry row, a w3id
or tag URL, or a toolkit support claim. No draft type can enter the governed set:
the registry's ``files`` map names the released types, and that set is asserted by
a test to be exactly what is governed.

No network access. The live owning repositories of the FHT and FHGM drafts are
probed only through local sibling checkouts when one happens to exist; when it
does not — or when reading one raises at all, including a sibling that is a symlink
resolving outside the workspace — the line is printed as UNVERIFIED rather than
fetched, and rather than crashing, because the specification's CI must not depend on
another repository (a maintainer decision recorded in #270).

Scope note: this is a census of the ``pattern`` keyword only. ``patternProperties``
keys are regular expressions too and are deliberately out of scope here; adding
them is a follow-up, not an omission to repair silently. Counts are labelled
entries (one per file + JSON pointer), distinct strings, and entries ending in
``$``, so they are never compared against the broader regex-entry census in the
#271 docs page (the #241 reference-class point).

Usage:
    python scripts/check_pattern_census.py                 # census + released gate
    python scripts/check_pattern_census.py --root <tree>    # same, on a scratch tree
    python scripts/check_pattern_census.py --update-baseline
        Refresh .github/pattern-baseline.json after a reviewed, joint-maintainer
        contract change. Refuses to run when a CI environment is detected: only an
        authorized actor outside CI should refresh it after review. Environment
        markers do not authenticate the actor or prove approval — they make an
        automated refresh inconvenient, and branch protection plus a one-file diff
        in review is what actually authorises it.
    python scripts/check_pattern_census.py --update-baseline --exclude PATH::REASON
        Register a discovered surface document as not-a-contract. Both halves are
        mandatory, and a governed file cannot be excluded.

Verified behaviours — each is a test, and each was re-run against the pre-fix script
before the fix was believed (a test that never saw the broken code is not a regression
test):

    released pattern changed by one character ................ RED
    released pattern deleted / added ........................ RED
    unscoped root contract WITH a pattern .................... RED
    unscoped root contract with NO pattern ................... RED   (governed-file set)
    governed file that disappears ............................ RED
    exclusion registered without a reason .................... RED
    exclusion attempted for a governed file .................. REFUSED
    baseline hand-edited without re-digesting ................ RED
    baseline version 1 in check mode ......................... RED (and refresh still works)
    --update-baseline under a CI marker ...................... REFUSED, bytes unchanged
    lookaround in a draft ................................ GREEN (informational)
    malformed YAML in a scoped draft ................. RED (named error, no traceback)
    malformed YAML in an unscoped document ............. does not abort the sweep
    sibling checkout symlinked outside the tree ........ UNVERIFIED line, never a crash
    ``examples``/``const``/unknown-keyword data ...... GREEN (instance data, not a
        constraint, and still listed informationally)
    description-only edit beside a released pattern .... GREEN
    untouched tree ..................................... GREEN
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
    ("fht.json", "proposed FHT v0.7.0 contract (unpublished)"),
    ("fht_linkml.yml", "FHT publication candidate model"),
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

# The governed surface is DISCOVERED by rule, not enumerated by hand. RELEASED_SCOPE
# above is a seed: it labels files and it names the minimum set that must always stay
# governed. It is not the boundary of the check, and that distinction is the whole
# point — see PR #272 review, finding 1: a gate whose two comparison sides both derive
# from one hand-written tuple can never see a file the tuple does not already name, so
# a brand-new contract with no `pattern` in it passed. The rule below is what finds
# such a file. `docs/TERMS.md` places the released contracts at the repository root,
# and the shared models and registry under schemas/, so exactly those two places are
# the surface. Root-level discovery is deliberately NOT recursive: examples/,
# templates/ and conformance/ hold instances and generated artifacts, and the
# informational sweep still reports any `pattern` they carry.
DISCOVERY_RULE = ("*.json / *.yaml / *.yml at the repository root, plus every "
                  "*.json / *.yaml / *.yml under schemas/ (recursive)")
SURFACE_SUFFIXES = {".json", ".yaml", ".yml"}


def expand(root, governed=None):
    """Every scoped path: {relative: (scope, label, rows, anomalies)}.

    `governed` is the DISCOVERED set minus registered exclusions; the hand-written
    RELEASED_SCOPE is always included as the seed. A released-scope file that is
    missing or unparsable raises :class:`CensusError` (silently losing a gated
    contract is the failure mode this script exists to prevent). A draft-scope file
    that cannot be read is recorded as an anomaly instead: what a draft *contains*
    never gates the build.
    """
    labels = dict(RELEASED_SCOPE)
    paths = sorted(set(governed or ()) | set(labels))
    found = {}
    for relative in paths:
        rows, anomalies = inventory(root, relative)
        found[relative] = ("released", labels.get(relative, "discovered on the released "
                                                       "surface"), rows, anomalies)
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
# Baseline format. 2 registers the governed FILE set (discovered by rule)
# plus per-file pattern counts; version 1 stored only a hand-written `scope`
# list, so an unregistered contract was invisible to it.
BASELINE_VERSION = 2
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

# LinkML keywords whose value is prose or annotation data, never a constraint. The
# instance-data exclusion (PR #272 review, finding 3) was first applied only to the
# JSON Schema traversal, which left the .yaml models — schemas/core.yaml,
# schemas/shared.yaml, the *_linkml.yml files and the draft profiles, i.e. exactly the
# files where `examples:` is common — still walking into their own instance data. A
# LinkML-side test is what showed it.
LINKML_DATA_KEYS = {"examples", "description", "title", "annotations", "extensions",
                    "comments", "notes"}
# LinkML containers whose child keys are model-level NAMES (a class name, a slot name),
# not keywords. `attributes` and `slot_usage` in particular: a class may legitimately
# declare a slot called `pattern`, and without this the walker reads that slot's
# definition as the pattern keyword — a non-string, which now fails closed.
LINKML_NAMED_KEYS = {"classes", "slots", "types", "enums", "attributes", "slot_usage",
                     "subsets", "prefixes", "settings", "enum_entries", "permissible_values"}


def iter_patterns(node, pointer="", keyed_by_name=False):
    """Yield (pointer, value) for every ``pattern`` keyword, resolving nothing.

    Pointers are reported exactly as they appear in the file: ``$ref`` targets of
    the shared imports are not followed, because #270 asks where a pattern is
    written, not where it applies. This is the LinkML traversal; the JSON Schema one is
    `iter_schema_patterns`, and both exclude instance data, for the same reason.
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
        if key in LINKML_DATA_KEYS:
            continue
        if key == "pattern":
            yield child, value
        elif key in NAME_KEYED or key in LINKML_NAMED_KEYS:
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


def discover_governed_surface(root):
    """Every document the rule places on the released surface, whether or not it has patterns."""
    found = set()
    for path in root.iterdir():
        if path.is_file() and path.suffix in SURFACE_SUFFIXES:
            found.add(path.relative_to(root).as_posix())
    schemas = root / "schemas"
    if schemas.is_dir():
        for path in schemas.rglob("*"):
            if path.is_file() and path.suffix in SURFACE_SUFFIXES:
                found.add(path.relative_to(root).as_posix())
    return sorted(found)


def registry(root):
    """The release identity and the released type->file map this repository asserts.

    schemas/versions.json is the authority on which types are released, so it also
    decides which contracts must be governed: a file named there can never be
    discovered-away or excluded-away.
    """
    try:
        document = load_document(root / "schemas" / "versions.json")
    except CensusError:
        return None, None, {}
    if not isinstance(document, dict):
        return None, None, {}
    files = document.get("files")
    return (document.get("current"), document.get("preRelease"),
            {str(key): str(value) for key, value in files.items()}
            if isinstance(files, dict) else {})


def mandatory_governed(root):
    """Seed paths plus every contract the registry names as released."""
    _current, _pre, files = registry(root)
    return {relative for relative, _label in RELEASED_SCOPE} | set(files.values())


def parse_exclusion(value):
    """`path::reason` -> (path, reason). A reason is mandatory: an anonymous exclusion
    is just a silent skip with extra typing."""
    path, separator, reason = value.partition("::")
    path = path.strip()
    reason = reason.strip()
    if not separator or not path or not reason:
        raise ValueError(f"--exclude expects PATH::REASON, got {value!r}")
    return path, reason


def compare_governed(baseline, discovered, root):
    """Registration drift, in both directions, keyed on the discovered surface.

    Returns (problems, stale). A discovered document that is neither governed nor
    excluded by name with a reason is the unregistered-contract case; a governed file
    that is no longer discovered is the deleted-or-moved case.
    """
    problems = []
    governed = {entry["path"] for entry in baseline.get("governedFiles", [])}
    excluded = {entry["path"]: entry for entry in baseline.get("excludedFiles", [])}
    for path in sorted(set(discovered) - governed - set(excluded)):
        try:
            entries = len(inventory(root, path)[0])
        except CensusError as error:
            entries = f"uncensusable: {error}"
        problems.append(
            f"{path}: discovered on the released surface ({DISCOVERY_RULE}) but not "
            f"registered in the baseline as governed or as excluded with a reason "
            f"(it holds {entries} pattern entries; 0 entries still fails — a "
            "pattern-free contract is still a contract joining the governed surface)")
    for path in sorted(governed - set(discovered)):
        problems.append(
            f"{path}: the baseline governs it but the discovery rule no longer finds it "
            "(deleted, renamed, or moved off the released surface). Removing a governed "
            "contract is a contract change: review it, then refresh the baseline "
            "outside CI.")
    for path, entry in sorted(excluded.items()):
        if not str(entry.get("reason", "")).strip():
            problems.append(f"{path}: registered as excluded with no reason")
        if path in mandatory_governed(root):
            problems.append(
                f"{path}: is named by RELEASED_SCOPE or by schemas/versions.json and "
                "cannot be excluded; a governed file that stops looking interesting is "
                "still a governed file")
    stale = sorted(set(excluded) - set(discovered))
    return problems, stale

# Deliberately not censused, so that a reader does not mistake the totals for
# "every regex in the tree": .github/schema-baseline*.json (review baselines
# owned by check_schema_drift.py), templates/cedar/*.json (generated authoring
# templates, verified against their source schema by make_cedar.py --check) and
# tests/fixtures/cedar-meta-schemas/*.json (third-party CEDAR meta-schema
# fixtures, not family contracts).


def governed_entries(root, found, discovered, excluded):
    """The governed file set: discovered surface minus the registered exclusions."""
    labels = dict(RELEASED_SCOPE)
    entries = []
    for relative in discovered:
        if relative in excluded:
            continue
        rows = found[relative][2] if relative in found else []
        entries.append({"path": relative,
                        "label": labels.get(relative, "discovered on the released surface"),
                        "patternEntries": len(rows)})
    return entries


def build_baseline(root, found, discovered, excluded):
    files = released_files(found)
    governed = governed_entries(root, found, discovered, excluded)
    rows = [row for entry in found.values() if entry[0] == "released" for row in entry[2]]
    return {
        "baselineVersion": 2,
        "note": (
            "Two gates, one file. (1) WHICH FILES are governed: the released surface is "
            "discovered by rule and every discovered document must appear here either in "
            "governedFiles or in excludedFiles with a reason, so a new contract fails even "
            "when it contains no `pattern` at all. (2) WHAT EACH GOVERNED FILE ASSERTS: "
            "every JSON Schema `pattern` entry below, by file and JSON pointer. Refresh "
            "only through a reviewed contract change: "
            "python scripts/check_pattern_census.py --update-baseline (refuses to run in "
            "CI). See " + CITATION + "."
        ),
        "policy": (
            "ECMA-262 is the floor for `pattern`; the v0.4 lookahead sentence is "
            "historical, not current policy; no released contract may be widened."
        ),
        "policySource": CITATION,
        "countingScope": {
            "keyword": "the `pattern` keyword only; `patternProperties` keys are regular "
                       "expressions too and are out of this scope by design (#270 "
                       "follow-up), so this is narrower than the regex-entry census in "
                       "the #271 docs page",
            "unit": "entry = one (file, JSON pointer) pair; the same string under two "
                    "pointers counts twice; entriesEndingInDollar counts entries whose "
                    "text ends in `$`; distinctPatternStrings counts unique strings",
            "governedFiles": "discovered by rule, not enumerated; see discoveryRule",
        },
        "discoveryRule": DISCOVERY_RULE,
        "governedFiles": governed,
        "governedFileDigest": digest(governed),
        "excludedFiles": [{"path": path, "reason": excluded[path]}
                          for path in sorted(excluded)],
        "files": files,
        "patternEntries": len(rows),
        "distinctPatternStrings": len({row["pattern"] for row in rows}),
        "entriesEndingInDollar": sum(1 for row in rows if row["pattern"].endswith("$")),
        "patternCount": len(rows),
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
                f"{after[pointer]!r} (a new written constraint requiring review)"
            )
        for pointer in sorted(set(before) - set(after)):
            problems.append(
                f"{relative}: {pointer}: released pattern removed {before[pointer]!r} "
                "(removing a constraint can widen the accepted value set)"
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
    not be skipped quietly. Documents without a pattern keyword are outside
    this inventory guard; this is not a complete contract-file inventory."""
    path = PurePosixPath(relative)
    return (path.parent == PurePosixPath(".") and path.suffix in {".json", ".yaml", ".yml"}
            or path.parent == PurePosixPath("schemas"))


def unscoped(root, found, excluded=()):
    """Pattern-bearing documents outside every scope table, split by surface.

    Returns (on the released surface, elsewhere, unreadable on the released
    surface). The first and third gate the build: they are how a newly published
    contract at the repository root or under ``schemas/`` could otherwise slip
    past this pattern-keyword drift check unnoticed. Documents without pattern
    keywords are outside this guard.
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
        if relative in excluded:
            # registered as not-a-contract, by name and with a reason, in the baseline:
            # the registration check already vets that decision, so this sweep stays quiet
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


def load_stored(baseline_path):
    """Read the committed baseline, or return None when there is not one yet."""
    if not baseline_path.is_file():
        return None
    try:
        stored = load_document(baseline_path)
    except (CensusError, ValueError, OSError) as error:
        raise CensusError(f"{baseline_path}: unreadable: {error}") from error
    if not isinstance(stored, dict):
        raise CensusError(f"{baseline_path}: not an object")
    return stored


def exclusions_for(root, stored, requested, refresh):
    """Registered exclusions carry forward; a refresh may add to them, never subtract
    a governed file. Returns {path: reason}."""
    excluded = {}
    if isinstance(stored, dict):
        for entry in stored.get("excludedFiles", []) or []:
            if isinstance(entry, dict) and entry.get("path") and entry.get("reason"):
                excluded[str(entry["path"])] = str(entry["reason"])
    if not refresh:
        return excluded
    mandatory = mandatory_governed(root)
    for value in requested:
        try:
            path, reason = parse_exclusion(value)
        except ValueError as error:
            raise CensusError(str(error)) from error
        if path in mandatory:
            raise CensusError(
                f"{path} is named by RELEASED_SCOPE or by schemas/versions.json and cannot "
                "be excluded: a governed contract that stops looking interesting is still a "
                "governed contract. If it really is no longer released, that is a registry "
                "and release decision, not a census flag.")
        excluded[path] = reason
    return excluded


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
    parser.add_argument("--exclude", action="append", default=[], metavar="PATH::REASON",
                        help="with --update-baseline, register a discovered surface file as "
                             "not-a-contract, naming it and justifying it; a governed file "
                             "cannot be excluded")
    args = parser.parse_args()
    root = args.root.resolve()
    baseline_path = args.baseline.resolve() if args.baseline else (
        root / ".github" / "pattern-baseline.json")

    # 1. Discover the surface by rule. Everything else in this check is downstream of
    #    this list, including the baseline's own claim about what it governs.
    discovered = discover_governed_surface(root)
    try:
        stored = load_stored(baseline_path)
    except CensusError as error:
        print(f"pattern census failed: {error}", file=sys.stderr)
        return 1
    try:
        excluded = exclusions_for(root, stored, args.exclude, args.update_baseline)
    except CensusError as error:
        print(f"pattern census failed: {error}", file=sys.stderr)
        return 1

    try:
        governed = [entry for entry in discovered if entry not in excluded]
        found = expand(root, governed)
    except CensusError as error:
        print(f"pattern census failed: {error}", file=sys.stderr)
        return 1

    # 2. Registration: the baseline is the authority on which files are governed.
    #    Checked before pattern contents, because a file this check has never heard of
    #    cannot contribute a trustworthy pattern inventory. A refresh is exempt from the
    #    "no baseline yet" and "old baseline format" guards — refusing those in refresh
    #    mode would make the very command that upgrades a baseline impossible to run.
    if not args.update_baseline:
        if stored is None:
            print(f"pattern census failed: no baseline at {baseline_path}. Create one "
                  f"outside CI with: {REFRESH_COMMAND}", file=sys.stderr)
            return 1
        if stored.get("baselineVersion") != BASELINE_VERSION:
            print(f"pattern census failed: {baseline_path.name} is baseline version "
                  f"{stored.get('baselineVersion')!r}; this script writes version "
                  f"{BASELINE_VERSION}. A version-1 baseline names a hand-written file list "
                  "and no governed set, so it cannot detect an unregistered contract. "
                  f"Upgrade it outside CI with `{REFRESH_COMMAND}`.", file=sys.stderr)
            return 1
    registration, stale = ([], []) if args.update_baseline else \
        compare_governed(stored, discovered, root)
    if registration:
        print(f"\nGOVERNED FILE SET: {baseline_path} vs the discovered released surface "
              f"({len(registration)} problems)", file=sys.stderr)
        for problem in registration:
            print(f"  {problem}", file=sys.stderr)
        print(f"Register the file by refreshing outside CI (`{REFRESH_COMMAND}`), which puts "
              "it in governedFiles, or exclude it by name with a reason "
              f"(`{REFRESH_COMMAND} --exclude PATH::REASON`). A file named by "
              "schemas/versions.json can never be excluded.", file=sys.stderr)
        return 1
    listed, elsewhere, unreadable = unscoped(root, found, set(excluded))
    if listed or unreadable:
        print("pattern census failed: a pattern-bearing document on the released surface "
              "(repository root or schemas/) is not in the gated scope:", file=sys.stderr)
        for text in listed + unreadable:
            print(f"  {text}", file=sys.stderr)
        print("Add it to RELEASED_SCOPE in scripts/check_pattern_census.py so a published "
              "pattern-bearing contract cannot escape this drift gate (or move it off the "
              "released surface), then refresh the baseline outside CI.", file=sys.stderr)
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
        f"[draft] {relative}: {text}" for relative, (scope, _label, _rows, texts)
        in found.items() if scope == "draft" for text in texts)
    # Deliberately NOT informational. The Copilot thread proposed letting draft parse
    # failures pass quietly; the maintainer instruction for this round was to fail closed.
    # The distinction that keeps both honest: what a draft CONTAINS (a lookaround, an
    # inline flag) is reported and never gates, because ECMA-262 is the floor. Whether a
    # scoped file can be READ at all is coverage, and a census that skips an unreadable
    # file while printing a clean total is making a claim it did not verify.
    scope_anomalies = released_anomalies + draft_anomalies
    if scope_anomalies:
        print("pattern census failed: a file listed in a scope table could not be censused "
              "(contents are informational for drafts; unreadable is not, because a skipped "
              "file is an unverified coverage claim):", file=sys.stderr)
        for text in scope_anomalies:
            print(f"  {text}", file=sys.stderr)
        return 1

    baseline_payload = build_baseline(root, found, discovered, excluded)
    current = baseline_payload["files"]

    if args.update_baseline:
        blocked = ci_environment()
        if blocked:
            print(
                "refusing to refresh the released-pattern baseline inside CI "
                f"(detected {', '.join(blocked)}): {REFRESH_COMMAND} is an authorized action "
                "taken outside CI after a reviewed contract change, and the refreshed "
                "baseline must be committed with that change.",
                file=sys.stderr,
            )
            return 1
        after = compare_governed(baseline_payload, discovered, root)[0]
        if after:
            print("refusing to write an inconsistent baseline:", file=sys.stderr)
            for problem in after:
                print(f"  {problem}", file=sys.stderr)
            return 1
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(baseline_payload, indent=2, ensure_ascii=False,
                                            allow_nan=False) + "\n", encoding="utf-8")
        print(f"Updated {baseline_path}: {len(baseline_payload['governedFiles'])} governed "
              f"files, {baseline_payload['patternEntries']} pattern entries "
              f"({baseline_payload['distinctPatternStrings']} distinct strings, "
              f"{baseline_payload['entriesEndingInDollar']} ending in `$`), "
              f"{baseline_payload['digest']}; "
              f"{len(baseline_payload['excludedFiles'])} surface files excluded by name")
        if stale:
            print("  note: these registered exclusions no longer describe a discovered file "
                  f"and were dropped: {', '.join(stale)}")
        print("Review and commit it with the contract change.")
        return 0

    print("Pattern census (FAIR-bioHeaders-Specification#270)")
    print("=" * 92)
    print("Policy: ECMA-262 is the floor for `pattern`. The v0.4 changelog sentence")
    print("about lookahead workarounds is historical, not current policy, so lookaround")
    print("patterns are counted and reported, never rejected. Two things are gated:")
    print("the governed FILE set (discovered by rule, registered in the baseline), and")
    print("the `pattern` entry at every pointer inside those files.")
    print("=" * 92)
    print(f"Discovery rule: {DISCOVERY_RULE}")
    print("Counting scope (do not compare these totals with a differently scoped census,")
    print("such as the regex-entry census in the #271 docs page):")
    for key, value in baseline_payload["countingScope"].items():
        print(f"  {key}: {value}")

    for scope, heading in (("released", "RELEASED scope (gated: file set + pattern entries)"),
                           ("draft", "DRAFT and proposal scope (informational only)")):
        paths = sorted(p for p, (s, *_rest) in found.items() if s == scope)
        print(f"\n{heading}")
        if not paths:
            print("  (no files found)")
            continue
        rows = [row for p in paths for row in found[p][2]]
        total = {}
        for relative in paths:
            _scope, label, entry_rows, _anomalies = found[relative]
            print(f"  {describe(relative, entry_rows)}  [{label}]")
            for key in ("dollar_anchor", "lookaround", "noncapturing_group",
                        "inline_flags", "empty_class", "named_group"):
                total[key] = total.get(key, 0) + sum(1 for row in entry_rows if row[key])
        print(f"  {'SUBTOTAL ' + scope:62s} {len(rows):3d} entries   "
              + "   ".join(f"{key.replace('_', ' ')} {total[key]:3d}"
                           for key in ("dollar_anchor", "lookaround", "noncapturing_group",
                                       "inline_flags", "empty_class", "named_group"))
              + f"   distinct strings {len({row['pattern'] for row in rows}):3d}"
              + f"   ending in $ {sum(1 for row in rows if row['pattern'].endswith('$')):3d}")
        print(f"    (entries = one per file+JSON pointer; keyword `pattern` only)")

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

    if stale:
        print("\nRegistered exclusions that no longer describe a discovered file "
              "(informational; a refresh drops them)")
        for path in stale:
            print(f"  {path}")

    print("\nSurface files excluded by name (each must state a reason; a governed file")
    print("  named by RELEASED_SCOPE or schemas/versions.json can never appear here)")
    if not baseline_payload["excludedFiles"]:
        print("  none")
    for entry in baseline_payload["excludedFiles"]:
        print(f"  {entry['path']}: {entry['reason']}")

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

    stored_files = stored.get("files")
    if not isinstance(stored_files, dict):
        print(f"pattern census failed: {baseline_path} has no `files` inventory", file=sys.stderr)
        return 1
    if stored.get("digest") != digest(stored_files):
        print(f"pattern census failed: {baseline_path} is internally inconsistent: recorded "
              "pattern digest does not match its own `files` inventory. The baseline itself "
              "was edited by hand; regenerate it outside CI.", file=sys.stderr)
        return 1
    if stored.get("governedFileDigest") != digest(stored.get("governedFiles", [])):
        print(f"pattern census failed: {baseline_path} is internally inconsistent: recorded "
              "governed-file digest does not match its own `governedFiles` list. The baseline "
              "was edited by hand; regenerate it outside CI.", file=sys.stderr)
        return 1

    problems = compare(stored_files, current)
    if problems:
        print(f"\nRELEASED PATTERN DRIFT: {baseline_path} vs {root} "
              f"({len(problems)} problems)", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print("No released contract may be widened or narrowed by a pattern edit; that is a "
              "contract change with its own versioning and release cycle. If the change really "
              f"is reviewed and approved, refresh the baseline outside CI with "
              f"`{REFRESH_COMMAND}` and commit both files together.", file=sys.stderr)
        return 1
    released_rows = [row for entry in found.values() if entry[0] == "released"
                     for row in entry[2]]
    print(f"\nReleased gate: {len(discovered)} surface documents discovered "
          f"({len(stored.get('governedFiles', []))} governed, "
          f"{len(stored.get('excludedFiles', []))} excluded by name), "
          f"{len(released_rows)} `pattern` entries "
          f"({len({row['pattern'] for row in released_rows})} distinct strings, "
          f"{sum(1 for row in released_rows if row['pattern'].endswith('$'))} ending in `$`, "
          f"{sum(1 for row in released_rows if row['lookaround'])} with lookaround) match the "
          f"baseline {baseline_path.name} (patterns {stored.get('digest')}; files "
          f"{stored.get('governedFileDigest')}). No governed file added, removed or "
          "unregistered; no released pattern added, removed or edited.")
    # A second denominator, labelled: #271's docs census counts regex entries under a
    # broader scope, so the three-contract subset is printed here to keep the two
    # documents reconcilable instead of contradictory (#241 reference classes).
    three_paths = sorted(path for path, entry in found.items()
                         if entry[0] == "released" and path in {"fhr.json", "fhp.json", "fhgff3.json"})
    three = [row for path in three_paths for row in found[path][2]]
    three_distinct = len({row["pattern"] for row in three})
    three_dollar = sum(1 for row in three if row["pattern"].endswith("$"))
    print(f"  Subtotal, the three released contracts only ({', '.join(three_paths)}): "
          f"{len(three)} entries ({three_distinct} distinct strings, {three_dollar} ending "
          "in `$`). The rest of the released scope is the LinkML models, the shared slot "
          "models and the registry.")
    print("Draft constructs above are informational: ECMA-262 is the floor (#270).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
