# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Load and generate community profile schemas layered on a header type.

A *profile* is a small LinkML schema that imports a published type model
(``fhr_linkml.yml`` first, issue #51) and adds community requirements: a slot
made required, a value constraint, or a naming rule. A profile never edits the
published ``fhr.json``/``fhp.json``/``fhgff3.json`` or the type models; it is a
separate schema that a consumer applies *on top of* the unchanged base
contract. See ``docs/PROFILES.md`` and ``profiles/README.md``.

LinkML resolves an ``imports:`` entry to ``<name>.yaml``, while the published
type models are named ``.yml``. Rather than rename or copy a published file,
this loader reads the imported models into memory and supplies them through a
``SchemaView`` importmap. The profile files stay declarative and the published
bytes are untouched.

Only the registry selects a production profile. Imports and base models are
resolved exclusively from the repository root, never from the profile's own
directory, and the resolved base model's identity is checked before generation.
A test may load a model under ``profiles/`` with ``allow_path=True``; absolute
paths and ``..`` are always rejected.

The module is usable without the network: it reads only files in this checkout.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime import SchemaView
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = (ROOT / "profiles").resolve()
REGISTRY_PATH = PROFILES_DIR / "registry.yaml"
# ``json-schema-generator.py`` has a hyphen in its name, so load it by path. A
# profile root reuses that generator's type-specific post-processing; copying
# the rules here would let a profile silently drift from the base contract.
_generator_spec = importlib.util.spec_from_file_location(
    "profile_json_schema_generator", ROOT / "json-schema-generator.py"
)
GENERATOR = importlib.util.module_from_spec(_generator_spec)
_generator_spec.loader.exec_module(GENERATOR)
DIALECT = GENERATOR.DIALECT

PROFILE_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")
PROFILE_STATUSES = {"draft", "reviewed", "adopted"}
REGISTRY_FIELDS = (
    "header_type",
    "model",
    "base_model",
    "profileVersion",
    "applicability",
    "status",
    "community",
    "owner",
    "issue",
)
# The authoritative published type models a profile may layer on. An import is
# accepted only when it resolves to one of these files under ROOT and that file
# still has the expected identity and tree_root class. Most specific first.
PUBLISHED_BASES = {
    "FHGFF3": {
        "model": "fhgff3_linkml.yml",
        "id": "https://w3id.org/fhr/fhgff3",
        "name": "FHGFF3LinkML",
        "root": "FHGFF3",
        "postprocess": GENERATOR.apply_fhgff3_rules,
    },
    "FHP": {
        "model": "fhp_linkml.yml",
        "id": "https://w3id.org/fhr/fhp",
        "name": "FHPLinkML",
        "root": "FHP",
        "postprocess": None,
    },
    "FHR": {
        "model": "fhr_linkml.yml",
        "id": "https://w3id.org/fhr",
        "name": "FHRLinkMLMapping",
        "root": "FHR",
        "postprocess": GENERATOR.apply_fhr_rules,
    },
}


class UnsupportedProfileError(LookupError):
    """The profile is unknown, unsafe, or does not layer on a supported type."""


class ProfileRegistryError(ValueError):
    """The profile registry is malformed or inconsistent."""


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _profile_path(value):
    """Resolve a profile model path that must stay inside ``profiles/``."""
    candidate = Path(str(value))
    if (not str(value).strip() or candidate.is_absolute()
            or ".." in candidate.parts):
        raise UnsupportedProfileError(
            f"profile model {value!r} must be a relative path inside "
            f"{PROFILES_DIR.name}/ (absolute paths and '..' are not allowed)"
        )
    resolved = (PROFILES_DIR / candidate).resolve()
    if not resolved.is_relative_to(PROFILES_DIR):
        raise UnsupportedProfileError(
            f"profile model {value!r} resolves outside {PROFILES_DIR.name}/"
        )
    if not resolved.is_file():
        raise UnsupportedProfileError(
            f"profile model {value!r} is not a file inside {PROFILES_DIR.name}/"
        )
    return resolved


def _validate_registry_entry(profile_id, entry, path=REGISTRY_PATH):
    where = f"{path}: profile {profile_id!r}"
    if not isinstance(profile_id, str) or not profile_id.strip():
        raise ProfileRegistryError(f"{path}: a profile id must be a non-empty string")
    if not isinstance(entry, dict):
        raise ProfileRegistryError(f"{where}: expected a mapping")
    missing = [field for field in REGISTRY_FIELDS if field not in entry]
    if missing:
        raise ProfileRegistryError(f"{where}: missing {', '.join(missing)}")
    header_type = entry["header_type"]
    if header_type not in PUBLISHED_BASES:
        raise ProfileRegistryError(
            f"{where}: header_type {header_type!r} is not one of "
            f"{', '.join(PUBLISHED_BASES)}"
        )
    expected_base = PUBLISHED_BASES[header_type]["model"]
    if entry["base_model"] != expected_base:
        raise ProfileRegistryError(
            f"{where}: base_model {entry['base_model']!r} does not match "
            f"header_type {header_type} (expected {expected_base!r})"
        )
    if entry["status"] not in PROFILE_STATUSES:
        raise ProfileRegistryError(
            f"{where}: status {entry['status']!r} is not one of "
            f"{', '.join(sorted(PROFILE_STATUSES))}"
        )
    if not PROFILE_VERSION_PATTERN.fullmatch(str(entry["profileVersion"])):
        raise ProfileRegistryError(
            f"{where}: profileVersion {entry['profileVersion']!r} must be "
            "MAJOR.MINOR.PATCH"
        )
    for field in ("applicability", "community", "owner", "issue"):
        if not isinstance(entry[field], str) or not entry[field].strip():
            raise ProfileRegistryError(f"{where}: {field} must be a non-empty string")
    try:
        _profile_path(entry["model"])
    except UnsupportedProfileError as error:
        raise ProfileRegistryError(f"{where}: {error}") from error


def validate_registry(entries, path=REGISTRY_PATH):
    """Validate and return a registry mapping of profile id to entry."""
    if not isinstance(entries, dict) or not entries:
        raise ProfileRegistryError(f"{path}: expected a non-empty 'profiles' mapping")
    for profile_id, entry in entries.items():
        _validate_registry_entry(profile_id, entry, path)
    return entries


def load_registry(path=REGISTRY_PATH):
    """Return the validated profile registry, keyed by profile id.

    A profile is a *proposal* until the named community and the maintainers
    review it; the registry records that state, its version and applicability,
    and is not a claim of adoption.
    """
    document = load_yaml(path)
    return validate_registry(document.get("profiles"), path)


def resolve_profile(name, registry=None, *, allow_path=False):
    """Return ``(model path, registry entry or None)`` for a profile id.

    Production selection is registry-only. ``allow_path=True`` is for tests: it
    accepts a ``.yaml``/``.yml`` path confined under ``profiles/`` and returns no
    registry entry. An unknown id raises :class:`UnsupportedProfileError`
    instead of silently passing.
    """
    if allow_path:
        candidate = Path(name)
        if candidate.suffix in {".yaml", ".yml"}:
            return _profile_path(candidate), None
    registry = load_registry() if registry is None else validate_registry(registry)
    entry = registry.get(name)
    if entry is None:
        raise UnsupportedProfileError(
            f"profile {name!r} is not in {REGISTRY_PATH.name}; "
            f"known profiles: {', '.join(sorted(registry))}"
        )
    return _profile_path(entry["model"]), entry


def _resolve_import(name):
    """Locate an imported model under ROOT, never beside the profile."""
    if name.startswith("linkml:"):
        return None
    relative = Path(str(name))
    if (not relative.parts or relative.is_absolute()
            or ".." in relative.parts):
        return None
    stem = ROOT / relative
    for suffix in ("", ".yaml", ".yml"):
        candidate = Path(str(stem) + suffix)
        if candidate.is_file():
            resolved = candidate.resolve()
            if resolved.is_relative_to(ROOT):
                return resolved
    return None


def _import_sources(profile_path):
    """Load every model reachable from a profile as ``name -> (path, schema)``."""
    sources = {}
    todo = list(load_yaml(profile_path).get("imports") or [])
    while todo:
        name = todo.pop()
        if name in sources or name.startswith("linkml:"):
            continue
        resolved = _resolve_import(name)
        if resolved is None:
            raise UnsupportedProfileError(
                f"{profile_path}: import {name!r} is not a published model in "
                "this checkout"
            )
        schema = load_yaml(resolved)
        sources[name] = (resolved, schema)
        todo.extend(schema.get("imports") or [])
    return sources


def _import_map(sources):
    return {name: schema for name, (_, schema) in sources.items()}


def imported_base(model, profile_path):
    """Return ``(header type, import name)`` for the single published base."""
    stems = {
        Path(spec["model"]).stem: name for name, spec in PUBLISHED_BASES.items()
    }
    matches = []
    for name in model.get("imports") or []:
        base = stems.get(Path(str(name)).stem)
        if base is not None:
            matches.append((base, name))
    found = sorted({base for base, _ in matches})
    if not found:
        raise UnsupportedProfileError(
            f"{profile_path}: profile imports no published header type model "
            f"({', '.join(spec['model'] for spec in PUBLISHED_BASES.values())}); "
            "it must layer on one published type"
        )
    if len(found) > 1:
        raise UnsupportedProfileError(
            f"{profile_path}: profile imports more than one published header "
            f"type ({', '.join(found)}); it must layer on exactly one"
        )
    base = found[0]
    return base, next(name for candidate, name in matches if candidate == base)


def _published_base(base, profile_path):
    """Load a published base model and verify its identity, from ROOT only."""
    spec = PUBLISHED_BASES[base]
    path = (ROOT / spec["model"]).resolve()
    if not path.is_file() or not path.is_relative_to(ROOT):
        raise UnsupportedProfileError(
            f"{profile_path}: published base model {spec['model']} is missing"
        )
    schema = load_yaml(path)
    if schema.get("id") != spec["id"] or schema.get("name") != spec["name"]:
        raise UnsupportedProfileError(
            f"{profile_path}: {path.name} does not have the expected {base} "
            f"identity (id {spec['id']!r}, name {spec['name']!r})"
        )
    definition = (schema.get("classes") or {}).get(spec["root"]) or {}
    if not definition.get("tree_root"):
        raise UnsupportedProfileError(
            f"{profile_path}: {path.name} does not define the published "
            f"tree_root class {spec['root']!r}"
        )
    return path, schema


def _check_no_shadowing(profile_path, model, sources):
    """Reject a profile class that redefines a class from an imported model."""
    imported = {}
    for _, (path, schema) in sources.items():
        for name in schema.get("classes") or {}:
            imported.setdefault(name, path.name)
    collisions = sorted(set(model.get("classes") or {}) & set(imported))
    if collisions:
        detail = ", ".join(f"{name} (from {imported[name]})" for name in collisions)
        raise UnsupportedProfileError(
            f"{profile_path}: profile defines class(es) {detail} that are also "
            "defined by an imported published model; rename the profile class "
            "instead of shadowing a published class"
        )


def _check_registry_entry(profile_path, entry, base):
    """Cross-check a registry entry against the profile model's actual base."""
    if entry is None:
        return
    if entry["header_type"] != base:
        raise UnsupportedProfileError(
            f"{profile_path}: registry header_type {entry['header_type']!r} does "
            f"not match the profile's imported base type {base!r}"
        )
    expected_base = PUBLISHED_BASES[base]["model"]
    if entry["base_model"] != expected_base:
        raise UnsupportedProfileError(
            f"{profile_path}: registry base_model {entry['base_model']!r} does "
            f"not match the resolved base model {expected_base!r}"
        )


def root_class(profile_path, model=None):
    """The profile's own ``tree_root`` class (the class the profile constrains)."""
    document = load_yaml(profile_path) if model is None else model
    roots = [
        name
        for name, definition in (document.get("classes") or {}).items()
        if (definition or {}).get("tree_root")
    ]
    if len(roots) != 1:
        raise ValueError(
            f"{profile_path}: a profile must define exactly one tree_root class, "
            f"found {roots or 'none'}"
        )
    return roots[0]


def base_header_type(view, root, profile_path, base):
    """Require the profile root to inherit the published base root class."""
    spec = PUBLISHED_BASES[base]
    ancestors = set(view.class_ancestors(root))
    if spec["root"] not in ancestors:
        raise UnsupportedProfileError(
            f"{profile_path}: profile root class {root!r} does not inherit the "
            f"published {base} class {spec['root']!r} from {spec['model']}"
        )
    return base


def _profile_context(profile, registry=None, *, allow_path=False):
    path, entry = resolve_profile(profile, registry, allow_path=allow_path)
    model = load_yaml(path)
    base, base_import = imported_base(model, path)
    spec = PUBLISHED_BASES[base]
    base_path, _ = _published_base(base, path)
    sources = _import_sources(path)
    resolved = sources.get(base_import)
    if resolved is None or resolved[0] != base_path:
        raise UnsupportedProfileError(
            f"{path}: import {base_import!r} did not resolve to the published "
            f"{base} model {spec['model']}"
        )
    _check_no_shadowing(path, model, sources)
    _check_registry_entry(path, entry, base)
    view = SchemaView(
        str(path), importmap=_import_map(sources), merge_imports=True
    )
    return path, view, model, base


def load_schema_view(profile, registry=None, *, allow_path=False):
    """Merge a profile and its imported published models into one schema view."""
    return _profile_context(profile, registry, allow_path=allow_path)[1]


def generate_profile(profile, registry=None, *, allow_path=False):
    """Generate the JSON Schema for a profile, layered on its type's model.

    ``profile`` is a registry id (``agbiodata-fhr``). Tests may pass a model
    path under ``profiles/`` with ``allow_path=True``. The output is a JSON
    Schema draft 2020-12 document whose root is the profile class; it validates
    the base contract *and* the community additions.
    """
    path, view, model, base = _profile_context(
        profile, registry, allow_path=allow_path
    )
    root = root_class(path, model)
    base_header_type(view, root, path, base)
    generated = json.loads(
        JsonSchemaGenerator(
            view.schema,
            include_null=False,
            not_closed=False,
            top_class=root,
        ).serialize()
    )
    # Match the published schemas: schemaVersion is an enum so later versions
    # can be listed, and LinkML cannot express the exact digest lengths.
    GENERATOR.apply_common_rules(generated)
    # A base type's constraints that LinkML cannot express are added by the same
    # function the published schema uses (for example FHGFF3's genome link).
    postprocess = PUBLISHED_BASES[base]["postprocess"]
    if postprocess is not None:
        postprocess(generated, root, base)
    for key in ("metamodel_version", "version"):
        generated.pop(key, None)
    return generated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("profile", nargs="?", help="registered profile id")
    parser.add_argument("--output", type=Path,
                        help="output file (default: <profile>.schema.json)")
    parser.add_argument("--list", action="store_true",
                        help="list registered profiles and exit")
    args = parser.parse_args(argv)
    if args.list:
        for name, entry in sorted(load_registry().items()):
            print(f"{name}\t{entry['header_type']}\t{entry['profileVersion']}\t"
                  f"{entry['status']}\t{entry['community']}")
        return 0
    if args.profile is None:
        parser.error("a profile id is required (or use --list)")
    try:
        schema = generate_profile(args.profile)
    except (ProfileRegistryError, UnsupportedProfileError) as error:
        print(f"profile_schema: {error}", file=sys.stderr)
        return 2
    output = args.output or Path(f"{Path(args.profile).stem}.schema.json")
    output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
